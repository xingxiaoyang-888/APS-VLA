"""Read-only G1-F evidence analysis; no model loading, gate changes or test access.

Inputs may be absent while jobs run: missing evidence is pending, never zero.
Outputs are a JSON summary and short Chinese Markdown report. Cost scopes are
kept separate; allocation bills are not added to nested instrumented durations.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
METRICS = ("teacher_l1", "demonstration_l1")
FUTURE = ("future_mse", "future_zero_visual_mse", "future_reversed_action_mse")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                   separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class Evidence:
    def __init__(self):
        self.files = {}

    def read(self, path):
        path = Path(path).resolve()
        self.files[str(path)] = digest(path)
        return json.loads(path.read_text(encoding="utf-8"))

    def lines(self, path, *, allow_partial=False):
        path = Path(path).resolve()
        self.files[str(path)] = digest(path)
        raw = path.read_bytes().splitlines(keepends=True)
        rows, partial = [], False
        for i, line in enumerate(raw):
            try:
                rows.append(json.loads(line))
            except (ValueError, UnicodeError):
                if allow_partial and i == len(raw) - 1 and not line.endswith(b"\n"):
                    partial = True
                else:
                    raise ValueError(f"corrupt evidence line: {path}:{i+1}")
        return rows, partial

    def unchanged(self):
        if any(digest(path) != expected for path, expected in self.files.items()):
            raise ValueError("input evidence changed while being analyzed; retry after synchronization")


def finite(value, *, nonnegative=True):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or (nonnegative and value < 0):
        raise ValueError("metric must be a finite number in its declared range")
    return float(value)


def stats(values):
    a = np.asarray([finite(v, nonnegative=False) for v in values], dtype=np.float64)
    if not len(a):
        return {"count": 0, "mean": None, "p95": None}
    return {"count": len(a), "mean": float(a.mean()), "p95": float(np.quantile(a, .95))}


def clustered_interval(rows, *, value="delta", cluster="episode_id", strata="task_name", repeats=2000, seed=1517):
    """Resample whole paired clusters within tasks, preserving repeated windows.

    The estimand is the observation mean; numerator AND denominator change
    together when unequal-sized episode clusters are drawn more than once.
    """
    if type(repeats) is not int or repeats < 100:
        raise ValueError("bootstrap requires at least100 draws")
    groups, membership = defaultdict(dict), {}
    for row in rows:
        c, s = row[cluster], row[strata]
        if c in membership and membership[c] != s:
            raise ValueError("one bootstrap cluster cannot belong to different tasks")
        membership[c] = s
        groups[s].setdefault(c, []).append(finite(row[value], nonnegative=False))
    estimate = stats([r[value] for r in rows])["mean"]
    interval = None
    # With a single episode within any task, task-stratified uncertainty is not identifiable.
    if groups and all(len(g) >= 2 for g in groups.values()):
        rng = np.random.default_rng(seed)
        totals, counts = np.zeros(repeats), np.zeros(repeats)
        for task in sorted(groups):
            g = groups[task]
            aggregates = np.asarray([(sum(g[c]), len(g[c])) for c in sorted(g)])
            drawn = aggregates[rng.integers(0, len(g), size=(repeats, len(g)))].sum(axis=1)
            totals += drawn[:, 0]
            counts += drawn[:, 1]
        interval = np.quantile(totals / counts, [.025, .975]).tolist()
    return {"mean": estimate, "ci95_percentile": interval, "observations": len(rows), "clusters": len(membership),
            "strata": {str(k): len(v) for k, v in sorted(groups.items())}, "repeats": repeats, "seed": seed,
            "resampling_unit": cluster, "stratified_by": strata,
            "interpretation": "Exploratory fixed-development-panel interval; small n, post-selection, no significance or population claim."}


def metric_groups(rows, metrics):
    def summarize(group):
        return {key: stats([r[key] for r in group]) for key in metrics}
    return {"overall": summarize(rows),
            "by_task": {task: summarize([r for r in rows if r["window"]["task_name"] == task])
                        for task in sorted({r["window"]["task_name"] for r in rows})},
            "by_phase": {phase: summarize([r for r in rows if r["window"]["phase"] == phase])
                         for phase in ("early", "middle", "late")},
            "by_task_phase": [{"task_name": task, "phase": phase, **summarize(group)}
                for task in sorted({r["window"]["task_name"] for r in rows}) for phase in ("early", "middle", "late")
                if (group := [r for r in rows if (r["window"]["task_name"], r["window"]["phase"]) == (task, phase)])]}


def validate_validation(payload, expected, arm, update):
    if payload.get("arm") != arm or payload.get("update") != update or payload.get("windows") != len(expected):
        raise ValueError("validation arm/update/coverage mismatch")
    rows = payload["observations"]
    keyed = {r["window"]["window_id"]: r for r in rows}
    if len(keyed) != len(rows) or set(keyed) != set(expected):
        raise ValueError("validation contains duplicate, absent or unregistered window IDs")
    for wid, row in keyed.items():
        if row["window"] != expected[wid] or row["window"]["split"] != "validation":
            raise ValueError("validation window differs from its actual registered split/time/episode")
        for key in METRICS + (FUTURE if arm == "B" else ()):
            finite(row[key])
        indices = row["retained_indices"]
        if (len(indices) != 128 or any(type(i) is not int or not 0 <= i < 512 for i in indices)
                or indices != sorted(set(indices)) or sum(i < 256 for i in indices) != 64):
            raise ValueError("validation is not the registered ordered hard64-per-camera policy")
        actions = np.asarray(row["normalized_actions"])
        if actions.shape != (8, 7) or not np.isfinite(actions).all():
            raise ValueError("invalid validation action chunk")
    checks = {"validation_metric": stats([r["teacher_l1"] for r in rows])["mean"],
              "teacher_l1_p95": stats([r["teacher_l1"] for r in rows])["p95"],
              "demonstration_l1": stats([r["demonstration_l1"] for r in rows])["mean"]}
    checks.update({k: stats([r[k] for r in rows])["mean"] for k in FUTURE if arm == "B"})
    if any(not math.isclose(finite(payload[k]), v, rel_tol=1e-6, abs_tol=1e-8) for k, v in checks.items()):
        raise ValueError("validation aggregate differs from its window records")
    return keyed


def paired_windows(a, b, *, repeats, seed):
    if set(a) != set(b) or any(a[k]["window"] != b[k]["window"] for k in a):
        raise ValueError("A/B validation windows must match exactly by ID")
    output = {}
    for metric in METRICS:
        rows = [{"window_id": k, "episode_id": a[k]["window"]["episode_id"],
                 "task_name": a[k]["window"]["task_name"], "phase": a[k]["window"]["phase"],
                 "A": a[k][metric], "B": b[k][metric], "delta": b[k][metric] - a[k][metric]} for k in sorted(a)]
        output[metric] = {"direction": "B_minus_A; negative favors B", "rows": rows,
            "overall": clustered_interval(rows, repeats=repeats, seed=seed),
            "by_task": {task: clustered_interval([r for r in rows if r["task_name"] == task], repeats=repeats, seed=seed)
                        for task in sorted({r["task_name"] for r in rows})},
            "by_phase": {phase: clustered_interval([r for r in rows if r["phase"] == phase], repeats=repeats, seed=seed)
                         for phase in ("early", "middle", "late")}}
    return output


def hard_selection_comparison(a, b):
    """Compare saved hard sets and outputs; this is not teacher/GT recomputation."""
    if set(a) != set(b) or any(a[k]["window"] != b[k]["window"] for k in a):
        raise ValueError("hard-set comparison requires identical registered window IDs")
    rows = []
    for wid in sorted(a):
        left, right = set(a[wid]["retained_indices"]), set(b[wid]["retained_indices"])
        if len(left) != 128 or len(right) != 128:
            raise ValueError("hard-set overlap denominator is the fixed128-token budget")
        intersection, union = len(left & right), len(left | right)
        delta = np.abs(np.asarray(a[wid]["normalized_actions"], dtype=np.float64) -
                       np.asarray(b[wid]["normalized_actions"], dtype=np.float64))
        rows.append({"window": a[wid]["window"], "intersection_count": intersection,
                     "intersection_over_128": intersection / 128, "jaccard": intersection / union,
                     "sets_identical": left == right, "AB_output_l1": float(delta.mean())})
    metrics = ("intersection_over_128", "jaccard", "AB_output_l1")
    def group(values):
        return {"windows": len(values), "identical_sets": sum(r["sets_identical"] for r in values),
                **{key: stats([r[key] for r in values]) for key in metrics}}
    return {"overall": group(rows), "by_task": {task: group([r for r in rows if r["window"]["task_name"] == task])
            for task in sorted({r["window"]["task_name"] for r in rows})},
        "by_phase": {phase: group([r for r in rows if r["window"]["phase"] == phase]) for phase in ("early", "middle", "late")},
        "rows": rows, "limits": "Saved A/B hard sets and saved normalized output differences only. Overlap does not establish causal utility; AB output L1 is not teacher/GT error."}


def analyze_training(directory, windows, window_sha, config, evidence, *, repeats=2000, seed=1517):
    if directory is None:
        return {"status": "pending", "reason": "training directory not supplied"}, {}
    directory = Path(directory)
    needed = [directory / arm / "training_report.json" for arm in ("A", "B")]
    needed += [directory / arm / f"validation_{u:04d}.json" for arm in ("A", "B") for u in config["selection"]["updates"]]
    if missing := [str(p) for p in needed if not p.is_file()]:
        return {"status": "pending", "missing": missing}, {}
    expected = {r["window_id"]: r for r in windows["windows"] if r["split"] == "validation"}
    reports, histories, analysis = {}, {}, {}
    for arm in ("A", "B"):
        report = evidence.read(directory / arm / "training_report.json")
        if (report.get("status") != "completed" or report.get("arm") != arm or report.get("vla_parameters_unchanged") is not True
                or report.get("window_manifest_sha256") != window_sha or report.get("config_sha256") != signature({**config, "arm": arm})
                or report.get("training_updates_completed") != config["training"]["updates"] or not report.get("source_files")):
            raise ValueError("training report is incomplete or belongs to another config/window/model implementation")
        reports[arm], histories[arm], curves = report, {}, []
        for update in config["selection"]["updates"]:
            payload = evidence.read(directory / arm / f"validation_{update:04d}.json")
            histories[arm][update] = validate_validation(payload, expected, arm, update)
            curves.append({"update": update, "seconds_recorded": finite(payload["seconds"]),
                           **metric_groups(list(histories[arm][update].values()), METRICS + (FUTURE if arm == "B" else ()))})
        evaluated = [{"update": c["update"], "validation_metric": c["overall"]["teacher_l1"]["mean"]} for c in curves]
        if len(report["evaluations"]) != len(evaluated) or any(x["update"] != y["update"] or not math.isclose(x["validation_metric"], y["validation_metric"], rel_tol=1e-6, abs_tol=1e-8) for x, y in zip(report["evaluations"], evaluated)):
            raise ValueError("reported validation history differs from saved observations")
        best = min(evaluated, key=lambda r: (r["validation_metric"], r["update"]))
        if report["best_update"] != best["update"] or not math.isclose(report["best_validation_metric"], best["validation_metric"], rel_tol=1e-6, abs_tol=1e-8):
            raise ValueError("selected checkpoint is not minimum hard-teacher L1 with earliest tie")
        analysis[arm] = {"best_update": best["update"], "initial_scorer_sha256": report["initial_scorer_sha256"],
            "best_checkpoint_sha256": report["best_checkpoint_sha256"], "curves": curves,
            "initial": curves[0], "final": curves[-1], "best": next(c for c in curves if c["update"] == best["update"]),
            "trainable_parameters": report["trainable_parameters"], "future_head_parameters": report["future_head_parameters"],
            "peak_memory_allocated_bytes": report["peak_memory_allocated_bytes"],
            "validation_completed_seconds_lower_bound": sum(c["seconds_recorded"] for c in curves)}
    for key in ("initial_scorer_sha256", "sample_order_sha256", "vla_parameter_sha256", "source_files"):
        if reports["A"][key] != reports["B"][key]:
            raise ValueError("A/B training differs in shared initialization/order/frozen model/source")
    pairs = {label: paired_windows(histories["A"][ua], histories["B"][ub], repeats=repeats, seed=seed)
             for label, ua, ub in (("initial", 0, 0), ("final", config["training"]["updates"], config["training"]["updates"]),
                                  ("selected_best", reports["A"]["best_update"], reports["B"]["best_update"]))}
    bbest = histories["B"][reports["B"]["best_update"]]
    interventions = {}
    for key in FUTURE[1:]:
        rows = [{"episode_id": r["window"]["episode_id"], "task_name": r["window"]["task_name"],
                 "delta": r[key] - r["future_mse"]} for r in bbest.values()]
        interventions[key + "_minus_original"] = clustered_interval(rows, repeats=repeats, seed=seed)
    finalized = False
    # run_g1_future.py uses args.mode='train', hence train_finalization.json.
    final_path, summary_path = directory / "train_finalization.json", directory / "training_summary.json"
    if final_path.is_file() and summary_path.is_file():
        final, summary = evidence.read(final_path), evidence.read(summary_path)
        if (summary.get("arms") != reports or summary.get("status") != "completed" or final.get("status") != "verified"
                or final.get("checkpoint_unchanged") is not True or final.get("result_sha256") != digest(summary_path)):
            raise ValueError("training finalization does not bind these completed A/B reports")
        finalized = True
    return {"status": "analyzed" if finalized else "awaiting_finalization", "finalization_verified": finalized,
        "arms": analysis, "paired_windows": pairs, "B_readout_interventions": interventions,
        "best_hard_selection_comparison": hard_selection_comparison(histories["A"][reports["A"]["best_update"]], bbest),
        "limitations": ["Best checkpoint selected on these same validation windows; intervals are descriptive, not independent test evidence.",
                         "Future/zero-visual/reversed-action losses are interventions on the trained readout, not separately trained controls.",
                         "L1 rows are audited reported errors; raw teacher/GT arrays are absent here, so those L1 values cannot be independently recomputed."]}, reports


def analyze_closed_loop(directory, reports, evidence, *, repeats=2000, seed=1517,
                        suite="libero_spatial", panel_path=None):
    if directory is None:
        return {"status": "pending", "reason": "closed-loop directory not supplied"}
    directory = Path(directory)
    names = ("panel.json", "config.json", "trials.jsonl", "closed_loop_report.json")
    if missing := [str(directory / n) for n in names if not (directory / n).is_file()]:
        return {"status": "pending", "missing": missing}
    panel, config, summary = [evidence.read(directory / n) for n in ("panel.json", "config.json", "closed_loop_report.json")]
    events, partial = evidence.lines(directory / "trials.jsonl", allow_partial=True)
    if partial or summary.get("status") != "completed":
        return {"status": "pending", "reason": "closed-loop run incomplete or journal tail partial"}
    if (summary.get("checkpoint_unchanged") is not True or summary.get("test_opened") is not False
            or summary.get("trials_jsonl_sha256") != digest(directory / "trials.jsonl")
            or config.get("panel_signature") != panel.get("panel_signature")):
        raise ValueError("closed-loop summary/journal/panel verification mismatch")
    provenance = summary["provenance"]
    if any(provenance.get(k) != v for k, v in config.items() if k != "runtime"):
        raise ValueError("closed-loop summary provenance differs from frozen run config")
    if "runtime" in config and {k: v for k, v in provenance["runtime"].items() if k != "slurm_job_id"} != config["runtime"]:
        raise ValueError("closed-loop runtime provenance differs from frozen run")
    run_signature = signature(config)
    if any(e.get("run_signature") != run_signature for e in events):
        raise ValueError("closed-loop events belong to another frozen run")
    from cti_vla.evaluation.future_trials import validate_future_trial_identities, summarize_future_trials, load_future_development_panel
    dense_reference = None
    if suite == "libero_10":
        from cti_vla.data.long_initial_states import load_long_development_panel
        if panel_path is None:
            raise ValueError("Long analysis requires its explicit frozen development panel")
        evidence.read(panel_path)
        frozen_panel = load_long_development_panel(panel_path)
        dense_reference = config.get("dense_reference")
        expected_methods = ["future_A", "future_B"] if dense_reference is not None else ["dense", "future_A", "future_B"]
        if config.get("suite") != suite or config.get("max_steps") != 520 or config.get("methods") != expected_methods:
            raise ValueError("Long closed-loop config differs from its suite/horizon/three-method protocol")
        if dense_reference is not None:
            from cti_vla.evaluation.future_dense_reuse import require_dense_compatibility
            require_dense_compatibility(dense_reference, frozen_panel, config)
            if config.get("training_seed") not in (23, 41) or any(
                    config["selectors"][arm]["seed"] != config["training_seed"] for arm in ("A", "B")):
                raise ValueError("reused dense requires the new registered training seed, distinct from evaluation seed17")
    elif suite == "libero_spatial":
        state_root = ROOT / "configs/manifests/spatial_initial_states_v1"
        frozen_panel = load_future_development_panel(state_root / "init_states_development.json", state_root / "g0_development_15.json")
    else:
        raise ValueError("unsupported explicit analysis suite")
    if panel != frozen_panel:
        raise ValueError("closed-loop panel differs from the existing frozen development initial states")
    completed = {}
    for event in events:
        if event.get("event") == "result" and event.get("status") in ("completed", "policy_error"):
            if event["trial_id"] in completed or type(event.get("success")) is not bool or (event["status"] == "policy_error" and event["success"]):
                raise ValueError("duplicate/invalid completed trial")
            completed[event["trial_id"]] = event
    ledger = SimpleNamespace(events=events, completed=lambda: completed, path=directory / "trials.jsonl")
    validate_future_trial_identities(panel, config["methods"], ledger, dense_reference=dense_reference)
    rebuilt = summarize_future_trials(panel, config["methods"], ledger, provenance=summary["provenance"], checkpoint_unchanged=True,
        dense_reference=dense_reference)
    for key in ("status", "expected_trials", "completed_trials", "methods", "paired_AB", "cost"):
        if summary.get(key) != rebuilt[key]:
            raise ValueError("closed-loop summary differs from actual paired trials")
    if dense_reference is not None and any(summary.get(k) != rebuilt[k] for k in ("dense_reference_signature", "reused_dense_trials")):
        raise ValueError("closed-loop reused dense evidence differs from config")
    if reports:
        for arm in ("A", "B"):
            if config["selectors"][arm]["selector_checkpoint_sha256"] != reports[arm]["best_checkpoint_sha256"]:
                raise ValueError("closed-loop selector differs from analyzed training checkpoint")
    table = Counter({"A_only": 0, "B_only": 0, "both": 0, "neither": 0})
    pairs = []
    for row in rebuilt["paired_AB"]["results"]:
        a, b = row["A_success"], row["B_success"]
        table["both" if a and b else "A_only" if a else "B_only" if b else "neither"] += 1
        pairs.append({**row, "delta": int(b) - int(a)})
    if len(pairs) != 30:
        raise ValueError("completed G1-F requires all30 exact same-initial-state pairs")
    result = {"status": "analyzed", "training_checkpoint_link_verified": bool(reports), "paired_counts": dict(table),
        "methods": rebuilt["methods"], "pairs": pairs,
        "paired_B_minus_A": clustered_interval(pairs, cluster="state_trial_id", strata="task_id", repeats=repeats, seed=seed),
        "cost": rebuilt["cost"], "limits": "Only30 reused development states across3 tasks; no formal significance, seed replication or final-test conclusion."}
    if suite == "libero_10":
        result["limits"] = "Only30 preregistered Long development states across3 tasks; intervals are conditional on one trained seed and these tasks, not across-seed generalization or final-test evidence."
        result["paired_vs_dense"] = {}
        if dense_reference is not None:
            dense_rows = {r["state_trial_id"]: r for r in dense_reference["dense_results"]}
            result["dense_reference"] = {"signature": dense_reference["signature"], "trials": 30,
                "successes": sum(r["success"] for r in dense_rows.values()), "new_inferences": 0, "new_gpu_seconds": 0}
        for arm in ("A", "B"):
            rows = []
            for state in panel["states"]:
                dense = dense_rows[state["trial_id"]] if dense_reference is not None else completed[state["trial_id"] + ":dense"]
                selected = completed[state["trial_id"] + ":future_" + arm]
                rows.append({"state_trial_id": state["trial_id"], "task_id": state["task_id"],
                    "dense_success": dense["success"], "selector_success": selected["success"],
                    "delta": int(selected["success"]) - int(dense["success"])})
            result["paired_vs_dense"][arm] = {"pairs": rows,
                "selector_minus_dense": clustered_interval(rows, cluster="state_trial_id", strata="task_id", repeats=repeats, seed=seed)}
    return result


def analyze_cost_events(path, evidence):
    rows, partial = evidence.lines(path, allow_partial=True)
    active, attempts = {}, []
    for event in rows:
        name = event.get("event", "")
        if name not in ("cache_start", "cache_end", "cache_failed", "update_start", "update_end", "update_failed"):
            raise ValueError("unrecognized cost event; update the analyzer explicitly")
        kind, status = name.split("_")
        key = (kind, event["window_id"] if kind == "cache" else event["update"])
        if status == "start":
            if key in active:
                attempts.append({**active.pop(key), "completion": "interrupted_unknown"})
            active[key] = {"kind": kind, "key": key[1], "job_id": event.get("job_id")}
        else:
            if key not in active:
                raise ValueError("orphan cost completion without durable start")
            attempt = active.pop(key)
            if event.get("job_id", attempt["job_id"]) != attempt["job_id"]:
                raise ValueError("cost completion belongs to another job")
            attempts.append({**attempt, **event, "completion": "completed" if status == "end" else "failed"})
    attempts.extend({**r, "completion": "interrupted_unknown"} for r in active.values())
    unknown = sum(r["completion"] == "interrupted_unknown" or "seconds" not in r for r in attempts)
    known = sum(finite(r["seconds"]) for r in attempts if "seconds" in r)
    duplicates = len(attempts) - len({(r["kind"], r["key"]) for r in attempts})
    return {"path": str(Path(path).resolve()), "attempts": len(attempts), "completed": sum(r["completion"] == "completed" for r in attempts),
        "failed_explicit": sum(r["completion"] == "failed" for r in attempts),
        "interrupted_unknown": sum(r["completion"] == "interrupted_unknown" for r in attempts), "repeated_attempts": duplicates,
        "partial_tail": partial, "known_seconds": known, "seconds_total": None if unknown or partial else known,
        "known_teacher_forwards": sum(r.get("teacher_forwards", 0) for r in attempts),
        "known_vision_forwards": sum(r.get("vision_forwards", 0) for r in attempts),
        "known_forward_backward_samples": sum(r.get("forward_backward_samples", 0) for r in attempts),
        "job_ids": sorted({str(r["job_id"]) for r in attempts if r["job_id"]}),
        "limits": "Completed cache/update work including repeats. Missing validation-start events and hard-killed unlogged work cannot be reconstructed; counters are lower bounds."}


def analyze_slurm(paths, evidence, *, job_ids=()):
    """Accept project accounting JSON or sacct --parsable2 with named columns."""
    if not paths:
        return {"status": "pending", "reason": "no Slurm accounting supplied"}
    jobs, skipped, missing = {}, [], []
    for path in paths:
        path = Path(path)
        if path.suffix.lower() == ".json":
            payload = evidence.read(path)
            rows = payload["jobs"]
        else:
            evidence.files[str(path.resolve())] = digest(path)
            rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8")), delimiter="|"))
        for row in rows:
            jid = str(row.get("job_id", row.get("JobIDRaw", row.get("JobID", ""))))
            if "." in jid or (job_ids and jid not in job_ids):
                skipped.append(jid)
                continue
            if not jid:
                raise ValueError("Slurm row lacks job ID")
            elapsed = row.get("elapsed_seconds", row.get("ElapsedRaw"))
            gpu = row.get("allocated_gpus")
            if gpu is None:
                tres = dict(item.split("=", 1) for item in row.get("AllocTRES", "").split(",") if "=" in item)
                gpu = tres.get("gres/gpu")  # Never infer GPU count from CPU count or a job name.
            normalized = {"job_id": jid, "state": row.get("state", row.get("State")),
                "exit_code": row.get("exit_code", row.get("ExitCode")),
                "elapsed_seconds": None if elapsed in (None, "", "Unknown") else finite(float(elapsed)),
                "allocated_gpus": None if gpu in (None, "", "Unknown") else finite(float(gpu))}
            if jid in jobs and jobs[jid] != normalized:
                raise ValueError("conflicting accounting snapshots for the same allocation; supply final billing")
            jobs[jid] = normalized
    for jid in job_ids:
        if jid not in jobs:
            missing.append(jid)
    rows = list(jobs.values())
    known = [r for r in rows if r["elapsed_seconds"] is not None and r["allocated_gpus"] is not None]
    terminal = {"COMPLETED", "FAILED", "TIMEOUT", "CANCELLED", "OUT_OF_MEMORY", "NODE_FAIL", "PREEMPTED", "BOOT_FAIL", "DEADLINE"}
    unfinished = [r["job_id"] for r in rows if str(r["state"]).split()[0].rstrip("+") not in terminal]
    hours = sum(r["elapsed_seconds"] * r["allocated_gpus"] / 3600 for r in known)
    return {"status": "recorded" if rows else "pending", "jobs": rows, "missing_requested_jobs": missing,
        "excluded_steps_or_unrequested_jobs": sorted(set(skipped)), "states": dict(Counter(r["state"] for r in rows)),
        "known_allocated_gpu_hours": hours, "allocated_gpu_hours_total": hours if len(known) == len(rows) and rows and not missing and not unfinished else None,
        "unfinished_jobs": unfinished, "scope": "Allocation wall time × allocated GPUs; includes failed/retried jobs. Never add this to overlapping instrumented durations."}


def analyze_latency(directory, reports, evidence):
    if directory is None:
        return {"status": "pending", "reason": "no matched observation-to-action profiling provided"}
    directory = Path(directory)
    if any(not (directory / n).is_file() for n in ("measurements.json", "calls.jsonl", "summary.json")):
        return {"status": "pending", "reason": "profiler measurements/journal/summary incomplete"}
    measured, summary = [evidence.read(directory / n) for n in ("measurements.json", "summary.json")]
    journal, _ = evidence.lines(directory / "calls.jsonl")
    if measured.get("synthetic") is not False or measured.get("checkpoint_unchanged") is not True:
        return {"status": "pending", "reason": "profiling lacks real unchanged-checkpoint evidence"}
    provenance = measured.get("provenance", {})
    if not journal or journal[0].get("identity") != provenance:
        raise ValueError("profiling journal identity differs from measurement provenance")
    if (provenance.get("stage") != "G1-F_development_latency" or provenance.get("test_opened") is not False
            or provenance.get("panel", {}).get("split") != "development"
            or provenance.get("panel", {}).get("version") != "g1f-development-dense-control-0-80-160-v1"):
        raise ValueError("profiling evidence is not the registered G1-F development panel")
    if not {"future_A", "future_B", "dense"}.issubset(measured["methods"]):
        return {"status": "pending", "reason": "profiling does not cover both actual G1-F deployment arms"}
    if not reports:
        return {"status": "pending", "reason": "cannot bind profiling checkpoints before completed A/B reports"}
    for arm in ("A", "B"):
        method_provenance = measured["methods"]["future_" + arm].get("provenance", {})
        if method_provenance.get("selector_checkpoint_sha256") != reports[arm]["best_checkpoint_sha256"]:
            raise ValueError("profiling checkpoint differs from analyzed A/B model")
    from cti_vla.evaluation.profiling import ProfileConfig, summarize_latencies, verify_measurement_journal
    if ProfileConfig(**measured["config"]).synthetic or measured["config"] != provenance["config"]:
        raise ValueError("profiling protocol differs from its real fixed measurement identity")
    verify_measurement_journal(measured, directory / "calls.jsonl")
    if (summary.get("measurements_sha256") != digest(directory / "measurements.json")
            or summary.get("journal_sha256") != digest(directory / "calls.jsonl") or summary.get("checkpoint_unchanged") is not True):
        raise ValueError("profiling summary hash chain mismatch")
    rebuilt = summarize_latencies(measured, bootstrap_repeats=summary["bootstrap"]["repeats"], seed=summary["bootstrap"]["seed"])
    if any(summary.get(k) != v for k, v in rebuilt.items()):
        raise ValueError("profiler summary differs from full observation-to-action measurements")
    return {"status": "analyzed", **rebuilt, "cost": measured["cost"]}


def markdown(summary):
    offline, loop, latency = summary["offline"], summary["closed_loop"], summary["latency"]
    lines = ["# G1-F 独立结果分析", "", "仅汇总已提供证据；本报告不自动放行扩大 seed、预算或 test。", "",
             f"离线验证：{offline['status']}；闭环：{loop['status']}；完整延迟：{latency['status']}。", ""]
    if "arms" in offline:
        lines += ["| 组 | best update | teacher L1 mean / p95 | GT L1 mean / p95 |", "|---|---:|---|---|"]
        for arm, data in offline["arms"].items():
            s = data["best"]["overall"]
            lines.append(f"| {arm} | {data['best_update']} | {s['teacher_l1']['mean']:.6g} / {s['teacher_l1']['p95']:.6g} | {s['demonstration_l1']['mean']:.6g} / {s['demonstration_l1']['p95']:.6g} |")
        paired = offline["paired_windows"]["selected_best"]["teacher_l1"]["overall"]
        lines += ["", f"相同窗口 B−A teacher L1：{paired['mean']:.6g}，episode 聚类区间 {paired['ci95_percentile']}。负值偏向 B。",
                  "选模与分析使用相同验证集，属于选择后的描述性比较。逐任务/阶段、init/final 曲线及未来头干预结果见 JSON。", ""]
        future = offline["arms"]["B"]["best"]["overall"]
        lines += ["B 未来 MSE：原读出 / zero-visual / reversed-actions = " +
                  " / ".join(f"{future[k]['mean']:.6g}" for k in FUTURE) + "。", ""]
        sets = offline["best_hard_selection_comparison"]["overall"]
        lines += [f"硬集合完全相同 {sets['identical_sets']}/{sets['windows']} 窗；交集/128 均值 {sets['intersection_over_128']['mean']:.4f}，"
                  f"Jaccard 均值 {sets['jaccard']['mean']:.4f}；保存的 A/B 输出 L1 为 {sets['AB_output_l1']['mean']:.6g}。",
                  "集合变化或未来误差下降均不直接证明 B 改善控制。", ""]
    if loop["status"] == "analyzed":
        p = loop["paired_counts"]
        lines += [f"30 个同初态配对：仅 A 成功 {p['A_only']}，仅 B 成功 {p['B_only']}，共同成功 {p['both']}，共同失败 {p['neither']}。",
                  "这是 3 个任务的既有开发初态；小样本区间不作为正式显著性或最终测试结论。", ""]
    costs = summary["costs"]
    known = sum(r["known_seconds"] for r in costs["event_files"])
    cost_text = (f"已记录 cache/update 完成与显式失败耗时合计 {known:.3f} 秒，仅是已提供日志的下界；缺失账单及中断验证不补零。"
                 if costs["event_files"] else "cache/update 计时：pending，尚未提供事件日志。")
    lines += [cost_text,
              f"Slurm 账单：{costs['slurm']['status']}。GPU 分配时长与程序内计时分别报告，不相加。",
              "未来预测误差及 zero-visual / reversed-actions 仅诊断训练读出的依赖，不是额外训练的消融。", ""]
    return "\n".join(lines)


def run(args):
    evidence = Evidence()
    from cti_vla.data.experiment_protocol import load_experiment_protocol
    from cti_vla.data.future_windows import load_future_windows
    suite = getattr(args, "suite", "libero_spatial")
    if suite == "libero_10":
        from cti_vla.data.long_future_windows import load_long_future_protocol, load_future_windows as load_long_windows
        if getattr(args, "config", None) is None or getattr(args, "panel", None) is None:
            raise ValueError("Long analysis requires explicit --suite libero_10 --panel and --config")
        if args.latency_directory is not None:
            raise ValueError("Long latency has no registered panel in this90-trial protocol")
        args.protocol = args.protocol or ROOT / "configs/manifests/long_future_v1/protocol.json"
        args.windows = args.windows or ROOT / "configs/manifests/long_future_v1/windows.json"
        protocol = load_long_future_protocol(args.protocol)
        windows = load_long_windows(args.windows, protocol)
    elif suite == "libero_spatial":
        args.config = args.config or ROOT / "configs/experiments/g1_future_v1.json"
        args.protocol = args.protocol or ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json"
        args.windows = args.windows or ROOT / "configs/manifests/spatial_future_v1/windows.json"
        protocol = load_experiment_protocol(args.protocol)
        windows = load_future_windows(args.windows, protocol)
    else:
        raise ValueError("unsupported explicit analysis suite")
    evidence.read(args.windows)
    evidence.read(args.protocol)
    config = evidence.read(args.config)
    if config.get("schema") != "g1_future_v1":
        raise ValueError("this analyzer consumes only the registered G1-F v1 producer")
    if suite == "libero_10" and config.get("suite") != suite:
        raise ValueError("Long analysis must use the Long training config")
    offline, reports = analyze_training(args.training_directory, windows, digest(args.windows), config, evidence,
                                       repeats=args.bootstrap_repeats, seed=args.bootstrap_seed)
    loop = analyze_closed_loop(args.closed_loop_directory, reports, evidence, repeats=args.bootstrap_repeats,
        seed=args.bootstrap_seed, suite=suite, panel_path=getattr(args, "panel", None))
    latency = analyze_latency(args.latency_directory, reports, evidence)
    paths = list(args.cost_events)
    if args.training_directory:
        paths.extend(p for p in (args.training_directory / "cost_events.jsonl", args.training_directory / "A/cost_events.jsonl",
                                args.training_directory / "B/cost_events.jsonl") if p.is_file())
    paths = sorted({Path(p).resolve() for p in paths})
    cost_files = [analyze_cost_events(p, evidence) for p in paths]
    slurm = analyze_slurm(args.slurm_accounting, evidence, job_ids=tuple(args.job_id))
    summary = {"schema_version": 1, "stage": "G1-F_independent_analysis", "scientific_decision": "manual_review_required",
        "expanded_seed_authorized": False, "test_authorized": False, "offline": offline, "closed_loop": loop, "latency": latency,
        "costs": {"event_files": cost_files, "slurm": slurm,
                  "missing_cost_categories": ["Unprovided job/event files", "Killed validation work has no per-attempt journal in frozen v1", "Cached entries reused across jobs require original producer cost files"],
                  "validation_seconds": {a: d["validation_completed_seconds_lower_bound"] for a, d in offline.get("arms", {}).items()},
                  "warning": "No complete total is claimed from incomplete nested timers. Reported arm wall_seconds_this_attempt excludes earlier attempts."},
        "evidence_sha256": evidence.files, "analyzer_sha256": digest(__file__)}
    if suite == "libero_10":
        summary.update(stage="G1-F_Long_independent_analysis", suite=suite)
    evidence.unchanged()
    output = args.output_directory.resolve()
    if args.project_root.resolve() not in output.parents:
        raise ValueError("analysis artifacts must stay inside the project")
    output.mkdir(parents=True, exist_ok=True)
    if any(str((output / name).resolve()) in evidence.files for name in ("summary.json", "报告.md")):
        raise ValueError("analysis output would overwrite consumed source evidence")
    # Results may be refreshed as missing inputs arrive; source evidence is never modified.
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (output / "报告.md").write_text(markdown(summary), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("libero_spatial", "libero_10"), default="libero_spatial")
    parser.add_argument("--panel", type=Path, help="Long only: explicit frozen development_panel_30.json")
    parser.add_argument("--training-directory", type=Path)
    parser.add_argument("--closed-loop-directory", type=Path)
    parser.add_argument("--latency-directory", type=Path)
    parser.add_argument("--cost-events", type=Path, action="append", default=[])
    parser.add_argument("--slurm-accounting", type=Path, action="append", default=[])
    parser.add_argument("--job-id", action="append", default=[], help="Optional allocation filter; otherwise all supplied accounting jobs are reported")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--windows", type=Path)
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--bootstrap-repeats", type=int, default=2000)
    parser.add_argument("--bootstrap-seed", type=int, default=1517)
    result = run(parser.parse_args())
    print(json.dumps({"offline": result["offline"]["status"], "closed_loop": result["closed_loop"]["status"],
                      "latency": result["latency"]["status"], "scientific_decision": result["scientific_decision"]}))


if __name__ == "__main__":
    main()

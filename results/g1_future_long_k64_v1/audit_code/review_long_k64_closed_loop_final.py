"""Independent read-only audit of actual Long64/128 development evidence.

No production analysis/rollout modules are imported. Default invocation reads
evidence and prints a result. --write exclusively creates three new seed reviews
and one aggregate review only after all required inputs exist and checks pass.
The previous seed17 review is never overwritten. No simulator/model/test access.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SEEDS = (17, 23, 41)
TASKS = (0, 3, 5)
ROUND = "g1_future_long_k64_v1"
PARENT_FILES = {
    "config.json": "1d9fb2c974105656f3a9909b13ac4dff1aed347f680b108df5793582195f17ea",
    "panel.json": "64ce305a9530dca00879fdc00a4d08552d95c1ebf3db981533873d3b0d14886e",
    "closed_loop_report.json": "b54ea4fa2755317e9a71b1d566694e2ddcc0bb2267087ab16d5e34eb6ba85611",
    "trials.jsonl": "ff68b045e16c7e96ee2205471112e68c8596526b32ebef753db653a46e0bcad0",
}
DENSE_SIGNATURE = "9af54766a03d820ee2d2969a4f346e7032b40545123678fd3b46ec7f39cb94ef"
PARENT_JOBS = {"2993273", "2993299", "2993307", "2993338", "2993590", "2993591", "2993645", "2993646"}


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class Audit:
    def __init__(self, project):
        self.root = Path(project).resolve()
        self.evidence = {}
        self.checks = 0

    def check(self, condition, message):
        self.checks += 1
        if not condition:
            raise ValueError(message)

    def path(self, path):
        path = Path(path)
        path = (self.root / path).resolve() if not path.is_absolute() else path.resolve()
        self.check(self.root in path.parents, "evidence escaped project")
        self.check("init_states_test" not in path.name, "sealed initial states must never be opened")
        return path

    def digest(self, path):
        path = self.path(path)
        value = hashlib.sha256(path.read_bytes()).hexdigest()
        self.evidence[path.relative_to(self.root).as_posix()] = value
        return value

    def read(self, path):
        path = self.path(path)
        self.digest(path)
        return json.loads(path.read_text(encoding="utf-8"))

    def lines(self, path):
        path = self.path(path)
        self.digest(path)
        raw = path.read_bytes()
        self.check(raw.endswith(b"\n"), "journal has an incomplete/unterminated tail; preserve and wait")
        return [json.loads(line) for line in raw.splitlines()]

    def unchanged(self):
        for path, expected in self.evidence.items():
            self.check(hashlib.sha256((self.root / path).read_bytes()).hexdigest() == expected,
                "evidence changed during audit: " + path)


def dense_identity(config):
    fields = ("suite", "panel_signature", "base_model_revision", "input_version", "action_version",
        "packing_version", "stats_key", "environment_seed", "runtime_seed", "max_steps", "wait_steps",
        "action_chunk", "policy_watchdog_seconds", "source_verification")
    value = {key: config[key] for key in fields}
    asset = [sha for path, sha in config["watched_artifacts"].items()
             if path.replace("\\", "/").endswith("/configs/assets/openvla_oft_libero_long.json")]
    if len(asset) != 1:
        raise ValueError("need exactly one Long base manifest identity")
    value["asset_manifest_sha256"] = asset[0]
    value["policy_source_hashes"] = {key: sha for key, sha in config["source_hashes"].items()
        if key.startswith("src/cti_vla/models/") or key in ("src/cti_vla/evaluation/libero_runtime.py", "scripts/eval_libero.py")}
    value["runtime_semantics"] = {key: config["runtime"][key]
        for key in ("attention", "dtype", "mujoco_gl", "python", "packages", "cuda", "gpu")}
    return value


def resample(matrix, states):
    """Sample each state once per draw with all its seed values kept together."""
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != 30 or not np.isfinite(matrix).all():
        raise ValueError("invalid30-state paired matrix")
    rng = np.random.default_rng(1517)
    drawn = np.zeros((2000, matrix.shape[1]))
    for task in TASKS:
        indexes = sorted((i for i, s in enumerate(states) if s["task_id"] == task), key=lambda i: states[i]["trial_id"])
        if len(indexes) != 10:
            raise ValueError("not10 states per fixed task")
        drawn += matrix[indexes][rng.integers(0, 10, size=(2000, 10))].sum(axis=1)
    means = matrix.mean(axis=0)
    return {"mean": float(matrix.mean()), "ci95_percentile": np.quantile(drawn.mean(axis=1) / 30, [.025, .975]).tolist(),
        "per_seed_mean": means.tolist(), "sample_sd": float(means.std(ddof=1)) if len(means) > 1 else None,
        "range": [float(means.min()), float(means.max())], "unique_states": 30,
        "state_seed_cells": int(matrix.size), "bootstrap_repeats": 2000, "bootstrap_seed": 1517}


def audit_seed(audit, seed, run_root, panel, parent_config, parent_dense, target_config, *, budget=128, inventory=None):
    folder = run_root / "closed_loop"
    config, summary, saved_panel = [audit.read(folder / name) for name in ("config.json", "closed_loop_report.json", "panel.json")]
    events = audit.lines(folder / "trials.jsonl")
    methods = ["dense", "future_A", "future_B"] if seed == 17 and budget == 128 else ["future_A", "future_B"]
    audit.check(saved_panel == panel and config["panel_signature"] == panel["panel_signature"], "panel changed")
    audit.check(config["methods"] == methods and config["suite"] == "libero_10" and config["test_opened"] is False, "wrong methods/suite/test")
    audit.check((config["environment_seed"], config["runtime_seed"], config["wait_steps"], config["max_steps"], config["action_chunk"]) == (0, 17, 10, 520, 8), "evaluation seeds/limits changed")
    audit.check(dense_identity(config) == dense_identity(parent_config), "dense reuse identity changed")
    audit.check(summary["trials_jsonl_sha256"] == audit.digest(folder / "trials.jsonl"), "summary journal hash changed")
    audit.check(all(summary["provenance"].get(k) == v for k, v in config.items() if k != "runtime"), "summary provenance differs from config")
    audit.check({k: v for k, v in summary["provenance"]["runtime"].items() if k != "slurm_job_id"} == config["runtime"], "runtime provenance changed")
    if seed != 17 or budget == 64:
        reference = config["dense_reference"]
        audit.check(reference["signature"] == DENSE_SIGNATURE == signature({k: v for k, v in reference.items() if k != "signature"}), "dense reference receipt changed")
        audit.check(reference["source_files"] == PARENT_FILES and config["training_seed"] == seed, "wrong dense/seed identity")
        audit.check(summary["reused_dense_trials"] == 30 and summary["dense_reference_signature"] == DENSE_SIGNATURE, "reused dense counted incorrectly")
        if budget == 64:
            audit.check(config["visual_tokens"] == 64 and config["per_camera_budgets"] == [32, 32], "wrong64 evaluation budget")
            audit.check(config["budget_reuse_registration_sha256"] == audit.digest(run_root / "budget_reuse_registration.json"), "new-budget input/cache reuse receipt changed")
            audit.check(inventory is not None and all(inventory["files"].get(k) == v for k, v in config["source_hashes"].items()), "closed-loop source differs from registered frozen snapshot")
            submission = audit.read(run_root / "submission_closed_loop.json")
            audit.check(submission["source_sha256"] == inventory["source_sha256"] and submission["training_seed"] == seed
                and submission["mode"] == "closed_loop" and submission["experiment"] == ROUND, "new closed-loop submission identity changed")
        else:
            audit.check(config["engineering_reuse_registration_sha256"] == audit.digest(run_root / "reuse_registration.json"), "engineering reuse receipt changed")
    expected = {}
    for state in panel["states"]:
        for method in methods:
            expected[state["trial_id"] + ":" + method] = {"state_trial_id": state["trial_id"], "method": method,
                **{key: state[key] for key in ("task_id", "task_name", "initial_state_sha256", "source_state_index")},
                "split": "development", "environment_seed": 0}
    active, completed, attempts, unknown = {}, {}, [], 0
    event_counts = Counter(e["event"] for e in events)
    invocation_jobs = sorted({str(e["slurm_job_id"]) for e in events if e["event"] == "invocation"})
    audit.check(bool(invocation_jobs) and all(j.isdecimal() for j in invocation_jobs), "Slurm invocation identity missing")
    audit.check(not set(event_counts) - {"invocation", "start", "result", "cleanup_error"}, "unknown journal event")
    for e in events:
        audit.check(e["run_signature"] == signature(config), "event belongs to other run")
        if "trial_id" not in e:
            continue
        tid = e["trial_id"]
        audit.check(tid in expected and all(e.get(k) == v for k, v in expected[tid].items()), "trial/state/method identity mismatch")
        if e["event"] == "start":
            audit.check(tid not in completed, "a completed trial was rerun")
            if tid in active:
                unknown += 1
            active[tid] = e
        elif e["event"] == "result":
            audit.check(tid in active and e["status"] in ("completed", "policy_error", "infrastructure_error"), "orphan/unknown result")
            active.pop(tid)
            attempts.append(e)
            audit.check(type(e["success"]) is bool and (e["status"] == "completed" or not e["success"]), "invalid success flag")
            if e["status"] in ("completed", "policy_error"):
                audit.check(tid not in completed, "duplicate completed outcome")
                completed[tid] = e
    unknown += len(active)
    audit.check(set(completed) == set(expected), "closed-loop is incomplete; missing completed trials")
    audit.check(summary["status"] == "completed" and summary["checkpoint_unchanged"] is True and summary["test_opened"] is False, "closed-loop not finalized")
    audit.check(summary["stage"] == "G1-F_Long_development", "wrong closed-loop stage")
    audit.check(summary["expected_trials"] == summary["completed_trials"] == len(expected), "wrong final trial count")
    errors = Counter(r["status"] for r in attempts)
    first_hash_missing, first_hash_compared = 0, 0
    for row in attempts:
        chunks, steps = row["chunks"], row["control_steps"]
        audit.check(0 <= steps <= 520 and row["wait_steps"] == 10, "step/wait limits changed")
        if row["status"] == "completed":
            audit.check(row["policy_calls"] == len(chunks) == math.ceil(steps / 8), "chunk8/call count mismatch")
            audit.check(row["termination"] == ("environment_success" if row["success"] else "task_horizon"), "invalid normal termination")
            audit.check(row["success"] or steps == 520, "normal failure stopped before horizon")
        else:
            audit.check(row["policy_calls"] >= len(chunks), "failed policy attempt was not charged")
        audit.check([c["control_step"] for c in chunks] == list(range(0, len(chunks) * 8, 8)), "action chunk positions differ")
        actual_actions = np.asarray(row["executed_actions"], dtype=float)
        if steps:
            planned = np.concatenate([np.asarray(c["environment_actions"]) for c in chunks])[:steps]
            audit.check(actual_actions.shape == (steps, 7) and np.array_equal(actual_actions, planned) and np.isfinite(actual_actions).all(), "executed action queue mismatch")
        if chunks:
            expected_hash = parent_dense[row["state_trial_id"]]["chunks"][0]["observation_sha256"]
            audit.check(chunks[0]["observation_sha256"] == expected_hash, "initial observation differs from paired seed17 dense")
            first_hash_compared += 1
        else:
            first_hash_missing += 1
        for chunk in chunks:
            meta = chunk["metadata"]
            audit.check(meta["policy_calls"] == 1 and meta["inputs_version"] == config["input_version"] and meta["action_version"] == config["action_version"], "per-chunk policy/input/action changed")
            audit.check(np.asarray(chunk["normalized_actions"]).shape == (8, 7) and np.isfinite(chunk["normalized_actions"]).all(), "invalid action output")
            if row["method"] != "dense":
                indexes = meta["retained_indices"]
                arm = row["method"][-1]
                audit.check(indexes == sorted(set(indexes)) and len(indexes) == budget and all(type(i) is int and 0 <= i < 512 for i in indexes)
                    and sum(i < 256 for i in indexes) == budget // 2, "trained-budget original-index packing changed")
                audit.check(meta["scorer_calls"] == meta["vision_calls"] == 1 and meta["future_head_calls"] == 0 and meta["packing_version"] == config["packing_version"] and meta["selector_checkpoint_sha256"] == config["selectors"][arm]["selector_checkpoint_sha256"], "deployed selector differs from receipt")
                audit.check(meta["visual_tokens"] == budget and meta["per_camera_budgets"] == [budget // 2] * 2
                    and meta["language_cache"] == "disabled" and meta["pair_id"] == config["pair_id"], "deployed token budget/cache/pair differs")
    method_stats = {}
    for method in methods:
        rows = [r for r in completed.values() if r["method"] == method]
        stats = {"trials": len(rows), "successes": sum(r["success"] for r in rows), "policy_failures": sum(r["status"] == "policy_error" for r in rows),
            "per_task": {str(t): {"trials": 10, "successes": sum(r["success"] for r in rows if r["task_id"] == t)} for t in TASKS}}
        audit.check(all(summary["methods"][method][k] == stats[k] for k in ("trials", "successes", "policy_failures")), "method summary differs from raw trials")
        for task, group in stats["per_task"].items():
            audit.check(all(summary["methods"][method]["per_task"][task][k] == v for k, v in group.items()), "task summary differs")
        method_stats[method] = stats
    pairs, table = [], Counter({"A_only": 0, "B_only": 0, "both": 0, "neither": 0})
    for state in panel["states"]:
        left, right = [completed[state["trial_id"] + ":future_" + arm]["success"] for arm in ("A", "B")]
        table["both" if left and right else "A_only" if left else "B_only" if right else "neither"] += 1
        pairs.append({"state_trial_id": state["trial_id"], "task_id": state["task_id"], "A_success": left,
            "B_success": right, "B_minus_A": int(right) - int(left)})
    audit.check(summary["paired_AB"]["results"] == pairs and summary["paired_AB"]["completed_pairs"] == 30, "reported pair rows changed")
    delta = resample([[r["B_minus_A"]] for r in pairs], panel["states"])
    audit.check(summary["paired_AB"]["B_minus_A_success_rate"] == delta["mean"], "paired mean mismatch")
    cost = {"recorded_result_attempts": len(attempts), "unfinished_attempts_unknown_cost": unknown,
        "known_policy_calls": sum(r.get("policy_calls", 0) for r in attempts),
        "known_wall_seconds": sum(r.get("wall_seconds", 0) for r in attempts)}
    cost["policy_calls_total"] = None if unknown else cost["known_policy_calls"]
    for key, value in cost.items():
        audit.check(summary["cost"][key] == value or (isinstance(value, float) and math.isclose(summary["cost"][key], value, abs_tol=1e-8)), "failed/interrupted cost differs: " + key)
    initial_hashes, training_jobs = [], set()
    for arm in ("A", "B"):
        trained = audit.read(run_root / f"training/{arm}/training_report.json")
        receipt = audit.read(run_root / f"training/{arm}/deployment_receipt.json")
        metadata, selector = receipt["metadata"], config["selectors"][arm]
        audit.check(receipt["pair_config"] == target_config and receipt["training_config"] == dict(target_config, arm=arm), "seed config differs from training")
        audit.check(metadata["seed"] == selector["seed"] == target_config["seed"] == seed and metadata["pair_id"] == config["pair_id"] == signature(target_config), "training seed and runtime seed confused")
        audit.check(receipt["metadata_sha256"] == signature(metadata) and all(selector.get(k) == v for k, v in metadata.items()), "checkpoint metadata differs")
        audit.check(metadata["config_sha256"] == trained["config_sha256"] == signature(dict(target_config, arm=arm)), "per-arm config signature differs")
        audit.check(metadata["training_source_files"] == trained["source_files"] and metadata["training_source_sha256"] == signature(trained["source_files"]), "training source inventory differs")
        audit.check(metadata["window_manifest_sha256"] == trained["window_manifest_sha256"] == audit.digest("configs/manifests/long_future_v1/windows.json"), "training window identity differs")
        gate_path = (f"results/{ROUND}/acceptance/f01_acceptance.json" if budget == 64
            else "results/g1_future_long_v1/acceptance/f01_acceptance.json")
        audit.check(receipt["f01_report_sha256"] == trained["f01_report_sha256"] == audit.digest(gate_path), "budget-specific engineering acceptance identity differs")
        audit.check(metadata["input_acceptance_sha256"] == trained["input_acceptance_sha256"] == audit.digest("results/g1_future_long_v1/inputs/input_acceptance.json"), "official input acceptance identity differs")
        audit.check(receipt["base_frozen"] is True and metadata["base_frozen"] is True and trained["vla_parameters_unchanged"] is True, "base frozen evidence is missing")
        audit.check(selector["future_head_deployed"] is False and selector["selection_mode"] == f"full512_score_once_camera{budget // 2}", "deployment is not one-shot trained-budget selection")
        if budget == 64:
            audit.check(metadata["visual_tokens"] == selector["visual_tokens"] == 64 and
                metadata["per_camera_budgets"] == selector["per_camera_budgets"] == [32, 32], "checkpoint was not trained at64 budget")
            review = audit.read(run_root / "training/independent_review.json")
            audit.check(review["status"] == "passed" and review["training_seed"] == seed and review["job_id"] == trained["job_id"], "new64 training independent review missing")
            audit.check(all(inventory["files"].get(k) == v for k, v in trained["source_files"].items()), "trained source differs from frozen64 inventory")
        audit.check(receipt["checkpoint_sha256"] == selector["selector_checkpoint_sha256"] == trained["best_checkpoint_sha256"] and signature(receipt) == selector["deployment_receipt_sha256"], "checkpoint hash differs")
        audit.check(receipt["training_complete"] is True and receipt["checkpoint_unchanged"] is True and receipt["planned_updates"] == receipt["completed_updates"] == trained["training_updates_completed"] == 100, "bounded training incomplete")
        audit.check([r["update"] for r in receipt["evaluations"]] == [0, 25, 50, 75, 100], "checkpoint validation schedule changed")
        best = min(receipt["evaluations"], key=lambda r: (r["validation_metric"], r["update"]))
        audit.check(best["update"] == trained["best_update"] == metadata["update"] and best["validation_metric"] == trained["best_validation_metric"] == metadata["validation_metric"], "best-checkpoint selection differs")
        initial_hashes.append(trained["initial_scorer_sha256"])
        training_jobs.add(str(trained["job_id"]))
    audit.check(len(set(initial_hashes)) == 1, "within-seed A/B initial DIE differs")
    final = audit.read(run_root / "training/train_finalization.json")
    training_jobs.add(str(final["job_id"]))
    audit.check(final["status"] == "verified" and final["checkpoint_unchanged"] is True and final["result_sha256"] == audit.digest(run_root / "training/training_summary.json"), "training finalization missing")
    return {"status": "passed", "training_seed": seed, "trained_visual_tokens": budget, "evaluation_runtime_seed": 17, "environment_seed": 0,
        "expected_new_trials": len(expected), "completed_trials": len(completed), "unique_states": 30,
        "method_statistics": method_stats, "AB_pairs": pairs, "AB_paired_counts": dict(table), "B_minus_A": delta,
        "per_task_B_minus_A": {str(t): sum(r["B_minus_A"] for r in pairs if r["task_id"] == t) / 10 for t in TASKS},
        "attempt_event_counts": dict(event_counts), "result_status_counts": dict(errors), "cost": cost,
        "closed_loop_slurm_job_ids": invocation_jobs, "training_completion_slurm_job_ids": sorted(training_jobs),
        "initial_observation_hash_matches": first_hash_compared, "initial_hash_unavailable_policy_failures": first_hash_missing,
        "initial_scorer_sha256": initial_hashes[0], "dense_reference_new_trials": 30 if seed == 17 and budget == 128 else 0,
        "test_opened": False, "notes": ["Interface/policy failures and interrupted attempts, when present, are retained rather than dropped.",
            "Server checkpoint bytes are not downloaded or freshly rehashed here; local receipts and finalized run identities are verified."]}


def audit_cost(audit, aggregate_root):
    account = audit.read(aggregate_root / "slurm_accounting.json")["jobs"]
    text_path = aggregate_root / "slurm_accounting.txt"
    audit.digest(text_path)
    raw = list(csv.DictReader(text_path.read_text(encoding="utf-8").splitlines(), delimiter="|"))
    audit.check(len(account) == len({str(r["job_id"]) for r in account}) and len(raw) == len({r["JobIDRaw"] for r in raw}), "allocation row duplicated")
    raw_by_id = {r["JobIDRaw"]: r for r in raw}
    audit.check(set(raw_by_id) == {str(r["job_id"]) for r in account}, "raw sacct and JSON coverage differ")
    audit.check(not PARENT_JOBS & set(raw_by_id), "parent job charged again")
    registered = {}
    for path in sorted(aggregate_root.rglob("submission_*.json")):
        value = audit.read(path)
        jid = str(value["job_id"])
        audit.check(value["experiment"] == ROUND and jid not in registered, "duplicate or unrelated submitted allocation")
        registered[jid] = value
    # Root freezes the live registry immediately before this final audit.
    # Later supervisor status updates must not invalidate scientific evidence.
    supervisor = audit.read(aggregate_root / "supervisor_state_at_review.json")
    supervised = {str(j["job_id"]): j for j in supervisor["registered_jobs"] if j.get("experiment") == ROUND}
    audit.check(set(registered) == set(supervised) == set(raw_by_id), "all submitted/supervised allocations including failures must be billed")
    for seed in SEEDS:
        for stage in ("train", "closed_loop"):
            submission = audit.read(aggregate_root / f"seed{seed}/submission_{stage}.json")
            job_id = str(submission["job_id"])
            audit.check(submission["training_seed"] == seed and submission["mode"] == stage and job_id in raw_by_id, "registered allocation missing")
            matches = [r for r in account if str(r["job_id"]) == job_id]
            audit.check(len(matches) == 1 and matches[0]["training_seed"] == seed and matches[0]["scope"] == stage, "registered allocation scope/seed changed")
    for mode in ("acceptance", "collect", "profile"):
        audit.check(any(r["mode"] == mode for r in registered.values()), "missing authorized allocation stage: " + mode)
    total, rows = 0, []
    terminal = {"COMPLETED", "FAILED", "TIMEOUT", "CANCELLED", "OUT_OF_MEMORY", "NODE_FAIL", "PREEMPTED", "BOOT_FAIL", "DEADLINE"}
    for row in account:
        jid = str(row["job_id"])
        source = raw_by_id[jid]
        submitted = registered[jid]
        audit.check(row["scope"] == submitted["mode"] and row["training_seed"] == submitted.get("training_seed")
            and row["scope"] in ("acceptance", "train", "closed_loop", "collect", "collection", "profile", "profiling", "latency"), "unexpected seed/stage allocation")
        audit.check(row["training_seed"] in (*SEEDS, None), "unexpected training seed allocation")
        audit.check(source["State"].split()[0].rstrip("+") in terminal, "unfinished allocation cost")
        seconds = int(source["ElapsedRaw"])
        tres = dict(item.split("=", 1) for item in source["AllocTRES"].split(",") if "=" in item)
        gpus = int(tres.get("gres/gpu", 0))
        audit.check(row["elapsed_seconds"] == seconds and row["allocated_gpus"] == gpus and gpus in (0, 1)
            and row["state"] == source["State"] and row["exit_code"] == source["ExitCode"], "accounting scalar mismatch")
        if gpus:
            audit.check((datetime.fromisoformat(source["End"]) - datetime.fromisoformat(source["Start"])).total_seconds() == seconds, "allocation timestamps disagree")
        total += seconds * gpus
        rows.append({"job_id": jid, "seed": row["training_seed"], "scope": row["scope"], "state": row["state"], "gpu_seconds": seconds * gpus})
    return {"allocations": rows, "new_gpu_seconds": total, "new_gpu_hours": total / 3600,
        "parent128_allocations_excluded": True, "failed_and_retried_allocations_included": True,
        "scope": "Unique new parent allocation wall seconds times GPUs. No addition of overlapping episode, validation or training timers."}


def compare_estimate(audit, actual, expected, label):
    audit.check(math.isclose(actual["mean"], expected["mean"], abs_tol=1e-12)
        and np.allclose(actual["ci95_percentile"], expected["ci95_percentile"], atol=1e-12, rtol=0),
        "independent state-cluster mean/interval differs: " + label)
    audit.check(math.isclose(actual["sample_sd"], expected["training_seed_mean_sample_sd"], abs_tol=1e-12)
        and np.allclose(actual["range"], expected["training_seed_mean_range"], atol=1e-12, rtol=0),
        "independent seed variation differs: " + label)


def paired_cells(left, right):
    values = Counter({"left_only": 0, "right_only": 0, "both": 0, "neither": 0})
    for a, b in zip(left, right):
        values["both" if a and b else "left_only" if a else "right_only" if b else "neither"] += 1
    return dict(values)


def verify_offline(audit, run, budget, analyzed):
    best, arms = {}, {}
    for arm in ("A", "B"):
        trained = audit.read(run / f"training/{arm}/training_report.json")
        saved = audit.read(run / f"training/{arm}/validation_{trained['best_update']:04d}.json")
        rows = saved["observations"]
        audit.check(len(rows) == 60 and all(len(r["retained_indices"]) == budget for r in rows), "offline budget/window count differs")
        best[arm] = rows
        arms[arm] = {metric: float(np.mean([r[metric] for r in rows])) for metric in ("teacher_l1", "demonstration_l1")}
        primary = analyzed["arms"][arm]["best"]["overall"]
        for metric, value in arms[arm].items():
            audit.check(math.isclose(value, primary[metric]["mean"], abs_tol=1e-12), "offline action error aggregation differs")
    audit.check([r["window"] for r in best["A"]] == [r["window"] for r in best["B"]], "offline A/B window alignment differs")
    overlap, jaccard, identical = [], [], 0
    for a, b in zip(best["A"], best["B"]):
        left, right = set(a["retained_indices"]), set(b["retained_indices"])
        overlap.append(len(left & right) / budget)
        jaccard.append(len(left & right) / len(left | right))
        identical += left == right
    primary = analyzed["best_hard_selection_comparison"]["overall"]
    audit.check(math.isclose(float(np.mean(overlap)), primary[f"intersection_over_{budget}"]["mean"], abs_tol=1e-12)
        and math.isclose(float(np.mean(jaccard)), primary["jaccard"]["mean"], abs_tol=1e-12)
        and primary["identical_sets"] == identical, "offline token overlap aggregation differs")
    return {"arms": arms, "intersection_over_budget": float(np.mean(overlap)), "jaccard": float(np.mean(jaccard)),
        "identical_sets": identical, "windows": 60,
        "scope": "Reaggregated saved per-window errors and exact token IDs; local teacher/GT arrays are unavailable."}


def run(project):
    audit = Audit(project)
    root, aggregate_root = audit.root, audit.root / f"results/{ROUND}"
    registration = audit.read(f"configs/experiments/{ROUND}.json")
    audit.check(registration["schema"] == ROUND and registration["training_seeds"] == list(SEEDS)
        and registration["evaluation"]["total_new_AB_trials"] == 180, "registration changed seeds/schema/count")
    audit.check(registration["analysis"]["bootstrap_repeats"] == 2000 and registration["analysis"]["bootstrap_seed"] == 1517,
        "registered bootstrap differs")
    inventory = audit.read(aggregate_root / f"source_{ROUND}.json")
    audit.check(inventory["source_sha256"] == hashlib.sha256(json.dumps(inventory["files"], sort_keys=True).encode()).hexdigest(),
        "source inventory signature differs")
    audit.check(inventory["files"][f"configs/experiments/{ROUND}.json"] == audit.digest(f"configs/experiments/{ROUND}.json"),
        "experiment was not frozen in production source")
    for relative, expected_sha in registration["frozen_evidence_sha256"].items():
        audit.check(audit.digest(relative) == expected_sha, "frozen parent evidence changed: " + relative)
    panel_path = root / registration["evaluation"]["panel"]
    audit.check(audit.digest(panel_path) == PARENT_FILES["panel.json"], "fixed panel bytes changed")
    panel = audit.read(panel_path)
    audit.check(Counter(s["task_id"] for s in panel["states"]) == {0: 10, 3: 10, 5: 10}
        and len({s["trial_id"] for s in panel["states"]}) == 30, "panel is not30 unique fixed states")
    audit.check(panel["split"] == "development" and panel["test_opened"] is False, "not sealed-test-safe development panel")
    for state in panel["states"]:
        values = np.asarray(state["initial_state"], dtype="<f8")
        h = hashlib.sha256(b"cti-vla:libero-init-state:v1\0" + np.asarray(values.shape, dtype="<i8").tobytes() + values.tobytes()).hexdigest()
        audit.check(values.ndim == 1 and np.isfinite(values).all() and h == state["initial_state_sha256"], "initial-state byte hash mismatch")
    parent_root = root / "results/g1_future_long_v1"
    for name, expected in PARENT_FILES.items():
        audit.check(audit.digest(parent_root / "closed_loop" / name) == expected, "original dense evidence changed")
    parent_config = audit.read(parent_root / "closed_loop/config.json")
    parent_events = audit.lines(parent_root / "closed_loop/trials.jsonl")
    parent_dense = {r["state_trial_id"]: r for r in parent_events if r["event"] == "result" and r["method"] == "dense"}
    audit.check(len(parent_dense) == 30, "dense must remain30 unique historical trials")
    f01 = audit.read(aggregate_root / "acceptance/f01_acceptance.json")
    final = audit.read(aggregate_root / "acceptance/acceptance_finalization.json")
    root_review = audit.read(aggregate_root / "acceptance/root_review.json")
    audit.check(f01["status"] == "passed" and f01["visual_tokens"] == 64 and f01["per_camera_budgets"] == [32, 32]
        and f01["checks"]["hard64_packing"] is True and "hard128_packing" not in f01["checks"]
        and root_review["status"] == "passed" and root_review["source_sha256"] == inventory["source_sha256"], "new64 actual engineering gate missing")
    audit.check(final["status"] == "verified" and final["checkpoint_unchanged"] is True
        and final["result_sha256"] == audit.digest(aggregate_root / "acceptance/f01_acceptance.json"), "new64 gate finalization differs")
    parent_training_config = audit.read(registration["parent_config"])
    per_budget, roots = {128: {}, 64: {}}, {}
    for budget in (128, 64):
        for seed in SEEDS:
            if budget == 128:
                run_root = root / registration["evaluation"]["reuse128_roots"][str(seed)]
                training_config = audit.read(run_root / "training/A/deployment_receipt.json")["pair_config"]
            else:
                entry = registration["new_configs"][str(seed)]
                audit.check(audit.digest(entry["path"]) == entry["sha256"], "new config file changed")
                training_config, run_root = audit.read(entry["path"]), root / entry["result_root"]
            excluded = ("seed", "run_id", "tokens_per_camera")
            audit.check(training_config["seed"] == seed and training_config["tokens_per_camera"] * 2 == budget
                and {k: v for k, v in training_config.items() if k not in excluded} ==
                    {k: v for k, v in parent_training_config.items() if k not in excluded}, "matched training configuration differs")
            roots[budget, seed] = run_root
            per_budget[budget][seed] = audit_seed(audit, seed, run_root, panel, parent_config, parent_dense,
                training_config, budget=budget, inventory=inventory if budget == 64 else None)
        audit.check(len({r["initial_scorer_sha256"] for r in per_budget[budget].values()}) == 3, "training seeds are not distinct fresh initializations")
    for seed in SEEDS:
        audit.check(per_budget[64][seed]["initial_scorer_sha256"] == per_budget[128][seed]["initial_scorer_sha256"], "cross-budget seeded initialization changed")
    states = panel["states"]
    dense = np.asarray([int(parent_dense[s["trial_id"]]["success"]) for s in states])[:, None]
    matrices = {f"{arm}{budget}": np.asarray([[int(per_budget[budget][seed]["AB_pairs"][i][arm + "_success"])
        for seed in SEEDS] for i in range(30)]) for budget in (128, 64) for arm in ("A", "B")}
    vectors = [{"state_trial_id": state["trial_id"], "task_id": state["task_id"], "dense_success": bool(dense[i, 0]),
        "method_seed_vectors": {name: value[i].tolist() for name, value in matrices.items()}} for i, state in enumerate(states)]
    comparisons = [("B128", "A128"), ("B64", "A64"), ("B64", "A128"), ("A64", "A128"), ("B64", "B128")]
    comparisons += [(method, "dense") for method in matrices]
    contrasts = {left + "_minus_" + right: resample(matrices[left] - (dense if right == "dense" else matrices[right]), states)
        for left, right in comparisons}
    methods = {name: resample(value, states) for name, value in matrices.items()}
    cost = audit_cost(audit, aggregate_root)
    for seed in SEEDS:
        for scope, key in (("train", "training_completion_slurm_job_ids"), ("closed_loop", "closed_loop_slurm_job_ids")):
            billed = {row["job_id"] for row in cost["allocations"] if row["seed"] == seed and row["scope"] == scope}
            audit.check(set(per_budget[64][seed][key]).issubset(billed), "actual training/evaluation invocation is missing from cost")
    analyzed = audit.read(aggregate_root / "analysis/summary.json")
    audit.check(analyzed["status"] in ("analyzed", "closed_loop_analyzed") and analyzed["test_opened"] is False
        and not analyzed["pending_runs"], "primary analysis is incomplete")
    closed = analyzed["closed_loop"]
    audit.check(closed["unique_initial_states"] == 30 and closed["new64_AB_trials"] == 180
        and closed["historical128_AB_trials"] == 180 and closed["dense"]["unique_trials"] == 30
        and closed["dense"]["successes"] == int(dense.sum()) and closed["dense"]["new_inferences"] == 0,
        "dense or repeated initial states were incorrectly multiplied")
    audit.check(closed["state_vectors"] == vectors, "primary analysis dropped or changed complete state/seed vectors")
    for name, value in methods.items():
        primary = closed["methods"][name]
        compare_estimate(audit, value, primary["equal_seed_mean"], name)
        for j, seed in enumerate(SEEDS):
            row = primary["per_seed"][str(seed)]
            audit.check(row["trials"] == 30 and row["successes"] == int(matrices[name][:, j].sum()), "per-seed method success count differs")
            for task in TASKS:
                indexes = [i for i, state in enumerate(states) if state["task_id"] == task]
                audit.check(row["by_task"][str(task)]["trials"] == 10 and row["by_task"][str(task)]["successes"] ==
                    int(matrices[name][indexes, j].sum()), "per-task success count differs")
    for left, right in comparisons:
        name, primary = left + "_minus_" + right, closed["contrasts"][left + "_minus_" + right]
        compare_estimate(audit, contrasts[name], primary, name)
        right_matrix = np.repeat(dense, 3, axis=1) if right == "dense" else matrices[right]
        for j, seed in enumerate(SEEDS):
            a, b = matrices[left][:, j], right_matrix[:, j]
            row = primary["per_seed"][str(seed)]
            audit.check(row["paired_counts"] == paired_cells(a, b) and math.isclose(row["left_minus_right"], float((a-b).mean()), abs_tol=1e-12), "paired seed difference/cells differ")
            for task in TASKS:
                ids = [i for i, state in enumerate(states) if state["task_id"] == task]
                audit.check(row["by_task"][str(task)]["paired_counts"] == paired_cells(a[ids], b[ids])
                    and math.isclose(row["by_task"][str(task)]["left_minus_right"], float((a[ids]-b[ids]).mean()), abs_tol=1e-12), "paired task difference/cells differ")
    offline = {str(budget): {str(seed): verify_offline(audit, roots[budget, seed], budget,
        analyzed["offline_all_budgets"][str(budget)][str(seed)]) for seed in SEEDS} for budget in (128, 64)}
    audit.check(math.isclose(analyzed["new_costs"]["allocated_gpu"]["allocated_gpu_hours_total"] * 3600,
        cost["new_gpu_seconds"], abs_tol=1e-8), "new complete GPU allocation total differs")
    audit.unchanged()
    aggregate = {"stage": "Long64_vs128_independent_closed_loop_audit", "status": "passed", "reviewer": "train64",
        "reviewed_utc": datetime.now(timezone.utc).isoformat(), "checks": audit.checks, "blockers": [],
        "training_seeds": list(SEEDS), "unique_initial_states": 30, "new64_AB_trials": 180,
        "historical128_AB_trials": 180, "dense_reference_unique_trials": 30,
        "per_budget_seed": {str(b): {str(s): v for s, v in rows.items()} for b, rows in per_budget.items()},
        "independently_recomputed_method_estimates": methods, "independently_recomputed_contrasts": contrasts,
        "offline_diagnostics": offline, "state_vectors": vectors, "new_cost": cost, "test_opened": False,
        "evidence_sha256": audit.evidence, "audit_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "limits": "All3 seed vectors stay together within30 unique states. Local nonweight evidence audit only; no independent rehash of server checkpoint tensors. Paired success and full allocation cost verified; latency statistics need separate profiling audit. No C or further experiment authorized."}
    return aggregate, per_budget[64], aggregate_root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--write", action="store_true", help="Exclusively create final review JSONs after a successful complete audit")
    args = parser.parse_args()
    try:
        result, seeds, output = run(args.project_root)
    except FileNotFoundError as exc:
        print(json.dumps({"status": "pending", "missing": str(exc), "reports_written": False}))
        return 2
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": f"{type(exc).__name__}: {exc}", "reports_written": False}))
        return 1
    if args.write:
        targets = {output / "analysis/independent_closed_loop_review.json": result,
            **{output / f"seed{seed}/closed_loop/independent_review.json": {**seeds[seed],
                "reviewer": "train64", "reviewed_utc": result["reviewed_utc"], "evidence_sha256": result["evidence_sha256"],
                "audit_script_sha256": result["audit_script_sha256"]} for seed in SEEDS}}
        if any(path.exists() for path in targets):
            raise FileExistsError("refusing to overwrite an existing review")
        for path, value in targets.items():
            with path.open("xb") as stream:
                stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode())
    print(json.dumps({"status": result["status"], "checks": result["checks"], "reports_written": args.write,
        "new_gpu_seconds": result["new_cost"]["new_gpu_seconds"], "B64_minus_A64": result["independently_recomputed_contrasts"]["B64_minus_A64"],
        "B64_minus_A128": result["independently_recomputed_contrasts"]["B64_minus_A128"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

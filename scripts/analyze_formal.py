"""Read-only formal-main-v2 analysis; incomplete evidence yields pending, no table.

No weight loader, simulator, final-state value loader, or mutating TrialLedger
is used. All22 outcomes travel together when a task's initial state is sampled.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation.formal_runtime import (FORMAL_SCHEMA, FORMAL_SUITES, FORMAL_BUDGETS, FORMAL_SEEDS,
    validate_formal_receipt, uniform_formal_indices)
from cti_vla.evaluation.formal_trials import (expected_method_ids, validate_freeze_matrix, validate_final_release,
    validate_execution_manifest, selector_instance_identity, ENVIRONMENT)
from cti_vla.evaluation.teacher_diagnostics import json_signature

ROOT = Path(__file__).resolve().parents[1]
VERSION = "formal-main-v2-analysis-1"
BOOTSTRAP_SEED, BOOTSTRAP_REPEATS = 20261016, 10000
SUITES = ("libero_10", "libero_spatial", "libero_object", "libero_goal")
TERMINAL_JOBS = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL", "PREEMPTED", "BOOT_FAIL",
    "DEADLINE", "REVOKED", "SPECIAL_EXIT"}
STATISTICAL_PROTOCOL = dict(bootstrap_repeats=10000, bootstrap_seed=20261016,
    stratify=["suite", "task"], cluster="initial state carrying all3 training seeds",
    interval="95% percentile", seed_sd_ddof=1, suite_weight="equal", task_weight="equal",
    primary_budget=128, practical_dense_loss_margin=.02,
    practical_acceptance="difference interval lower bound strictly greater than -0.02")


class PendingEvidence(Exception):
    def __init__(self, *missing):
        self.missing = list(missing)
        super().__init__("; ".join(missing))


class Evidence:
    """Immutable JSON/JSONL references only; never repairs malformed bytes."""
    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.seen = {}

    def path(self, ref, label):
        if not isinstance(ref, dict) or not ref.get("path") or not ref.get("sha256"):
            raise PendingEvidence(label + ": missing path/SHA256 reference")
        raw = Path(ref["path"])
        path = (self.root / raw).resolve() if not raw.is_absolute() else raw.resolve()
        if (self.root not in path.parents or path.suffix.lower() not in (".json", ".jsonl")
                or path.name.lower() in ("sealed_final.json", "init_states_test.json")
                or "sealed_final" in path.name.lower()):
            raise ValueError("analysis accepts project nonweight receipts/results only; never sealed state values: " + label)
        if not path.is_file():
            raise PendingEvidence(label + ": " + str(path))
        digest = file_sha256(path)
        if digest != ref["sha256"]:
            raise ValueError("immutable evidence SHA256 mismatch: " + label)
        self.seen[str(path)] = digest
        return path

    def read(self, ref, label):
        return json.loads(self.path(ref, label).read_text(encoding="utf-8"))

    def lines(self, ref, label):
        return list(self.iter_lines(ref, label))

    def iter_lines(self, ref, label):
        path = self.path(ref, label)
        with path.open("rb") as stream:
            stream.seek(0, 2)
            if stream.tell():
                stream.seek(-1, 2)
                if stream.read(1) != b"\n":
                    raise PendingEvidence(label + ": incomplete/uncommitted JSONL tail retained without repair")
            stream.seek(0)
            for line in stream:
                try:
                    yield json.loads(line)
                except (ValueError, UnicodeDecodeError) as exc:
                    raise ValueError("invalid JSONL evidence retained without repair: " + label) from exc

    def unchanged(self):
        if any(file_sha256(path) != sha for path, sha in self.seen.items()):
            raise ValueError("analysis evidence changed while it was being read")


def require_registration(registration):
    if (registration.get("schema") != FORMAL_SCHEMA or tuple(registration.get("suite_order", [])) != SUITES
            or registration.get("budgets") != [256, 128, 64] or registration.get("seeds") != [17, 23, 41]
            or registration.get("training_arms") != 72 or registration.get("final_trials") != 35200):
        raise ValueError("analysis is only defined for the complete registered formal-main-v2 matrix")
    if registration.get("statistics") != STATISTICAL_PROTOCOL:
        raise ValueError("statistical weighting/bootstrap/primary comparison differs from registration")


def pending_cache_cost():
    return {"status": "pending_real_training_logs", "not_assumed_zero": True,
        "missing": ["per-arm actual requested-window sequence and128GiB capacity replay",
                    "same-window measured current/teacher/future/diagnostic component times"],
        "scope": "Independent-cache cost estimate will be separate from actual Slurm GPU seconds; no extra training or GPU jobs for accounting."}


def interval(values, estimate):
    # Equal-weight binary rates have a finest denominator4800. Twelve decimal
    # places keep far more precision than this bootstrap can resolve, while
    # preventing summation roundoff at exactly-0.02 from crossing the strict
    # registered practical threshold.
    bounds = np.quantile(values, [.025, .975], method="linear")
    return {"estimate": float(estimate), "ci95_percentile": [round(float(v), 12) for v in bounds]}


def family_indices(methods):
    return {**{"dense": [methods.index("dense")]},
        **{f"uniform{k}": [methods.index(f"uniform{k}")] for k in FORMAL_BUDGETS},
        **{f"{arm}{k}": [methods.index(f"{arm}{k}_seed{s}") for s in FORMAL_SEEDS]
            for k in FORMAL_BUDGETS for arm in ("A", "B")}}


def cluster_bootstrap(outcomes):
    """One seeded index matrix per suite/task, reused across all22 columns."""
    if not isinstance(outcomes, np.ndarray) or outcomes.dtype != np.bool_ or outcomes.shape != (4, 10, 40, 22):
        raise ValueError("complete outcomes must be a bool[4 suites,10 tasks,40 states,22 instances] tensor")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    suite_samples = np.zeros((BOOTSTRAP_REPEATS, 4, 22), dtype=np.float64)
    digest = hashlib.sha256()
    for suite in range(4):
        for task in range(10):
            indices = rng.integers(0, 40, size=(BOOTSTRAP_REPEATS, 40), dtype=np.int64)
            digest.update(np.ascontiguousarray(indices, dtype="<i8").tobytes())
            suite_samples[:, suite, :] += outcomes[suite, task][indices].mean(axis=1) / 10.
    return suite_samples, digest.hexdigest()


def paired_counts(left, right):
    return dict(left_only=int(np.count_nonzero(left & ~right)), right_only=int(np.count_nonzero(~left & right)),
        both=int(np.count_nonzero(left & right)), neither=int(np.count_nonzero(~left & ~right)))


def summarize_success(outcomes, *, state_ids):
    methods = expected_method_ids()
    if len(state_ids) != 4 or any(len(tasks) != 10 or any(len(ids) != 40 or len(set(ids)) != 40 for ids in tasks) for tasks in state_ids):
        raise ValueError("statistics require explicit ordered40-state identities on every task")
    draws, draw_sha = cluster_bootstrap(outcomes)
    per_task = outcomes.mean(axis=2)
    per_suite = per_task.mean(axis=1)
    overall = per_suite.mean(axis=0)
    global_draws = draws.mean(axis=1)
    families = family_indices(methods)
    instance_rows = []
    for index, mid in enumerate(methods):
        instance_rows.append(dict(method_id=mid, **interval(global_draws[:, index], overall[index]),
            suites={suite: dict(**interval(draws[:, s, index], per_suite[s, index]),
                by_task={str(t): dict(trials=40, successes=int(outcomes[s, t, :, index].sum()), success_rate=float(per_task[s, t, index]))
                         for t in range(10)}) for s, suite in enumerate(SUITES)}))
    family_rows = {}
    for name, indices in families.items():
        seeded = len(indices) == 3
        family_rows[name] = dict(**interval(global_draws[:, indices].mean(axis=1), overall[indices].mean()),
            per_seed={str(seed): float(overall[i]) for seed, i in zip(FORMAL_SEEDS, indices)} if seeded else None,
            seed_sample_std=float(np.std(overall[indices], ddof=1)) if seeded else None,
            suites={suite: dict(**interval(draws[:, s, indices].mean(axis=1), per_suite[s, indices].mean()),
                per_seed={str(seed): float(per_suite[s, i]) for seed, i in zip(FORMAL_SEEDS, indices)} if seeded else None,
                seed_sample_std=float(np.std(per_suite[s, indices], ddof=1)) if seeded else None,
                by_task={str(t): float(per_task[s, t, indices].mean()) for t in range(10)}) for s, suite in enumerate(SUITES)})
    contrasts = [(f"B{k}", f"A{k}") for k in FORMAL_BUDGETS]
    contrasts += [(name, "dense") for name in families if name != "dense"]
    contrasts += [("B64", "A128")]
    comparisons = {}
    for left, right in contrasts:
        li, ri = families[left], families[right]
        effect = overall[li].mean() - overall[ri].mean()
        values = global_draws[:, li].mean(axis=1) - global_draws[:, ri].mean(axis=1)
        row = dict(left=left, right=right, positive_favors=left, **interval(values, effect),
            suites={suite: interval(draws[:, s, li].mean(axis=1) - draws[:, s, ri].mean(axis=1),
                per_suite[s, li].mean() - per_suite[s, ri].mean()) for s, suite in enumerate(SUITES)})
        if right == "dense":
            row["practical_2pp_target_supported"] = row["ci95_percentile"][0] > -.02
            row["practical_target_rule"] = "95% CI lower bound strictly greater than -0.02"
        # Dense/uniform remain a single shared reference, never extra seeds.
        right_indices = ri * len(li) if len(ri) == 1 else ri
        row["per_seed"] = {str(seed): interval(global_draws[:, a] - global_draws[:, b], overall[a] - overall[b])
            for seed, a, b in zip(FORMAL_SEEDS, li, right_indices)} if len(li) == 3 else None
        row["seed_sample_std"] = float(np.std(overall[li] - overall[right_indices], ddof=1)) if len(li) == 3 else None
        for s, suite in enumerate(SUITES):
            row["suites"][suite]["per_seed"] = {str(seed): interval(draws[:, s, a] - draws[:, s, b], per_suite[s, a] - per_suite[s, b])
                for seed, a, b in zip(FORMAL_SEEDS, li, right_indices)} if len(li) == 3 else None
            row["suites"][suite]["seed_sample_std"] = float(np.std(per_suite[s, li] - per_suite[s, right_indices], ddof=1)) if len(li) == 3 else None
        row["seed_task_pairs"] = [dict(suite=suite, task_id=t,
            training_seed=FORMAL_SEEDS[j] if len(li) == 3 else None,
            left_minus_right=float(per_task[s, t, a] - per_task[s, t, b]),
            **paired_counts(outcomes[s, t, :, a], outcomes[s, t, :, b]))
            for s, suite in enumerate(SUITES) for t in range(10) for j, (a, b) in enumerate(zip(li, right_indices))]
        comparisons[left + "_minus_" + right] = row
    return dict(unique_initial_states=1600, final_trials=35200, states_per_suite=400, training_seeds=list(FORMAL_SEEDS),
        primary_comparison="B128_minus_A128", method_ids=methods, suite_order=list(SUITES), state_ids=state_ids,
        instances=instance_rows, families=family_rows, comparisons=comparisons,
        bootstrap=dict(seed=BOOTSTRAP_SEED, repeats=BOOTSTRAP_REPEATS, percentile_method="linear",
            interval_decimal_places=12,
            draws_sha256=draw_sha, unit="task-stratified initial-state clusters carrying all22 instance outcomes",
            weighting="4 suites equally,10 tasks equally within suite,3 training seeds equally within learned family",
            rng="numpy.default_rng PCG64; suite_order then task0..9; each draw matrix int64[10000,40]",
            seed_resampling=False, p_values_reported=False),
        limits="Intervals condition on these40 tasks and three training seeds. Repeated seed-state outcomes are not independent initial states; an interval spanning zero does not establish equivalence. All comparisons retained; no exploratory significant-subset selection.")


def read_registry(reader, ref, suite, frozen):
    from cti_vla.data.formal_initial_states import validate_formal_final_registry
    if ref.get("sha256") != frozen["final_registry_sha256"]:
        raise ValueError("final identity registry differs from the global freeze")
    registry = reader.read(ref, suite + ":final_registry")
    validate_formal_final_registry(registry)
    if registry["suite"] != suite or json_signature(registry["source"]) != frozen["panel_source_sha256"]:
        raise ValueError("final registry suite/source differs from release")
    return registry


def validate_chunk(chunk, identity):
    from cti_vla.evaluation.libero_runtime import INPUTS_VERSION, ACTION_VERSION
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    meta = chunk.get("metadata", {})
    required = dict(schema=FORMAL_SCHEMA, suite=identity["suite"], method=identity["method"],
        visual_tokens=identity["visual_tokens"], per_camera_budgets=[identity["visual_tokens"] // 2] * 2,
        policy_calls=1, vision_calls=1, packing_calls=1, scorer_calls=int(identity["method"] in ("A", "B")),
        future_head_calls=0, language_cache="disabled", inputs_version=INPUTS_VERSION,
        action_version=ACTION_VERSION, packing_version=PACKING_VERSION)
    if any(meta.get(k) != v for k, v in required.items()):
        raise ValueError("final rollout chunk violated frozen deployment contract")
    kept = meta.get("retained_indices", [])
    if (len(kept) != identity["visual_tokens"] or kept != sorted(set(kept))
            or any(type(i) is not int or not 0 <= i < 512 for i in kept)
            or sum(i < 256 for i in kept) != identity["visual_tokens"] // 2):
        raise ValueError("final rollout has incorrect hard token identities")
    if identity["method"] == "uniform" and kept != uniform_formal_indices(identity["visual_tokens"]).tolist():
        raise ValueError("formal uniform rollout changed the frozen nested grid")
    for key in ("normalized_actions", "environment_actions"):
        actions = np.asarray(chunk.get(key), dtype=np.float64)
        if actions.shape != (8, 7) or not np.isfinite(actions).all():
            raise ValueError("final rollout chunk actions are invalid")
        if key == "environment_actions" and np.any(np.abs(actions) > 1.00001):
            raise ValueError("final executable action outside normalized controller bounds")
    if identity["method"] in ("A", "B") and (meta.get("selector_checkpoint_sha256") != identity["checkpoint_sha256"]
            or meta.get("training_seed") != identity["training_seed"] or meta.get("pair_id") != identity["pair_id"]):
        raise ValueError("final rollout uses a different selected checkpoint")


def read_final_run(reader, refs, *, registry, matrix, release, registration_sha):
    suite = registry["suite"]
    config = reader.read(refs.get("config"), suite + ":run.config")
    report = reader.read(refs.get("report"), suite + ":run.report")
    events = reader.iter_lines(refs.get("trials"), suite + ":run.trials")
    manifest = config.get("manifest", {})
    mids = validate_execution_manifest(manifest, registration_sha256=registration_sha)
    if (config.get("schema") != FORMAL_SCHEMA or config.get("kind") != "evaluation_run"
            or config.get("registration_sha256") != registration_sha or manifest.get("suite") != suite
            or manifest.get("split") != "final" or manifest.get("global_freeze") != matrix or manifest.get("release") != release):
        raise ValueError("formal analysis requires the exact released final execution")
    signature = json_signature(config)
    if (report.get("schema") != FORMAL_SCHEMA or report.get("kind") != "evaluation_summary"
            or report.get("suite") != suite or report.get("split") != "final"
            or report.get("trials_jsonl_sha256") != refs["trials"]["sha256"]
            or report.get("provenance", {}).get("run_signature") != signature):
        raise ValueError("final run report and raw ledger identity mismatch")
    for key, value in config.items():
        if key != "runtime" and report["provenance"].get(key) != value:
            raise ValueError("final report changed its frozen execution provenance")
    if not config.get("runtime") or any(report["provenance"].get("runtime", {}).get(k) != v for k, v in config["runtime"].items()):
        raise ValueError("final report runtime differs from the frozen execution; only job ID may be added")
    identities = {r["identity"]["method_id"]: r["identity"] for r in manifest["methods"]}
    states = {r["trial_id"]: r for r in registry["states"]}
    expected = {state_id + ":" + mid: (state, mid) for state_id, state in states.items() for mid in mids}
    completed, active, unknown, failed_infra, jobs = {}, {}, 0, 0, set()
    for event in events:
        if event.get("run_signature") != signature:
            raise ValueError("final ledger mixes run signatures")
        if event.get("event") == "invocation":
            if event.get("slurm_job_id"):
                jobs.add(str(event["slurm_job_id"]))
            continue
        tid = event.get("trial_id")
        if tid not in expected:
            raise ValueError("final ledger references an unregistered state/method")
        state, mid = expected[tid]
        required = dict(state_trial_id=state["trial_id"], method=mid, suite=suite, split="final",
            task_id=state["task_id"], task_name=state["task_name"], initial_state_sha256=state["initial_state_sha256"],
            source_state_index=state["source_state_index"], environment_seed=0, runtime_seed=17, configured_wait_steps=10, action_chunk=8)
        if any(event.get(k) != v for k, v in required.items()):
            raise ValueError("final paired state/environment identity differs from registry")
        if event["event"] == "start":
            if tid in completed:
                raise ValueError("completed final trial was rerun")
            unknown += int(tid in active)
            active[tid] = event
        elif event["event"] == "result":
            if tid not in active:
                raise ValueError("final result lacks its start event")
            active.pop(tid)
            status = event.get("status")
            if status == "infrastructure_error":
                if event.get("success") is not False:
                    raise ValueError("infrastructure failure cannot be counted as a success")
                failed_infra += 1
                continue
            if status not in ("completed", "policy_error") or type(event.get("success")) is not bool:
                raise ValueError("final result status/success invalid")
            if status == "policy_error" and event["success"]:
                raise ValueError("policy error cannot be counted as a success")
            if tid in completed:
                raise ValueError("duplicate completed final trial")
            if event.get("wait_steps") != 10 or not 0 <= event.get("control_steps", -1) <= FORMAL_SUITES[suite]["max_steps"]:
                raise ValueError("final rollout wait/horizon differs from registration")
            for chunk in event.get("chunks", []):
                validate_chunk(chunk, identities[mid])
            controls, chunks = event["control_steps"], event.get("chunks", [])
            executed = np.asarray(event.get("executed_actions", []), dtype=np.float64).reshape(-1, 7)
            if (len(executed) != controls or not np.isfinite(executed).all() or np.any(np.abs(executed) > 1.00001)
                    or [c["control_step"] for c in chunks] != list(range(0, controls, 8))
                    or event.get("policy_calls") != len(chunks) + int(status == "policy_error")):
                raise ValueError("final action queue/query/control-step evidence is incomplete")
            if controls and not np.array_equal(executed, np.concatenate([c["environment_actions"] for c in chunks])[:controls]):
                raise ValueError("executed final actions differ from returned chunk actions")
            if status == "completed" and ((event["success"] and event.get("termination") != "environment_success")
                    or (not event["success"] and (event.get("termination") != "task_horizon" or controls != FORMAL_SUITES[suite]["max_steps"]))
                    or controls == 0):
                raise ValueError("completed final success/horizon evidence is inconsistent")
            # Audit full raw actions above, then retain only a compact outcome
            # cell. A complete35200-trial run must not accumulate gigabytes of
            # redundant action chunks in analysis memory.
            completed[tid] = {**required, "status": status, "success": event["success"],
                "first_observation_sha256": chunks[0]["observation_sha256"] if chunks else None}
        elif event["event"] != "cleanup_error":
            raise ValueError("unknown final ledger event")
    unknown += len(active)
    if set(completed) != set(expected) or report.get("status") != "completed" or report.get("checkpoint_unchanged") is not True:
        raise PendingEvidence(suite + ": incomplete final run; " + str(len(expected) - len(completed)) + " trial cells missing")
    if (report.get("completed_trials") != len(completed) or report.get("unique_initial_states") != 400
            or report.get("expected_trials") != len(expected) or not jobs):
        raise ValueError("final report counts differ from raw calls")
    for mid in mids:
        subset = [r for r in completed.values() if r["method"] == mid]
        saved = report["methods"][mid]
        if saved.get("trials") != 400 or saved.get("successes") != sum(r["success"] for r in subset):
            raise ValueError("final reported success differs from raw trials")
        for task in range(10):
            rows = [r for r in subset if r["task_id"] == task]
            if saved["per_task"][str(task)].get("trials") != 40 or saved["per_task"][str(task)].get("successes") != sum(r["success"] for r in rows):
                raise ValueError("final per-task reported counts differ")
    return list(completed.values()), dict(unknown_attempts=unknown, infrastructure_failures=failed_infra,
        policy_errors=sum(r["status"] == "policy_error" for r in completed.values()), job_ids=sorted(jobs))


def assemble_outcomes(registries, rows):
    methods = expected_method_ids()
    state_ids, index = [], {}
    for s, suite in enumerate(SUITES):
        tasks = []
        for task in range(10):
            states = sorted((r for r in registries[suite]["states"] if r["task_id"] == task), key=lambda r: r["source_state_index"])
            if len(states) != 40:
                raise ValueError("formal final task requires40 unique initial states")
            tasks.append([r["trial_id"] for r in states])
            for i, state in enumerate(states):
                index[(suite, state["trial_id"])] = (s, task, i, state["initial_state_sha256"])
        state_ids.append(tasks)
    values = np.zeros((4, 10, 40, 22), dtype=np.bool_)
    covered, first_hashes = set(), {}
    for row in rows:
        key = (row["suite"], row["state_trial_id"])
        if key not in index or row["method"] not in methods:
            raise ValueError("unregistered final outcome identity")
        s, t, i, sha = index[key]
        if row["task_id"] != t or row["initial_state_sha256"] != sha or type(row["success"]) is not bool:
            raise ValueError("final outcome task/state/success mismatch")
        cell = (s, t, i, methods.index(row["method"]))
        if cell in covered:
            raise ValueError("duplicate final cell across runs; do not select a preferred attempt")
        covered.add(cell)
        values[cell] = row["success"]
        chunks = row.get("chunks", [])
        obs_sha = row.get("first_observation_sha256")
        if chunks:
            if chunks[0].get("control_step") != 0:
                raise ValueError("final first model input is not control step0")
            obs_sha = chunks[0]["observation_sha256"]
        if obs_sha is not None:
            if key in first_hashes and first_hashes[key] != obs_sha:
                raise ValueError("paired methods began from different raw observations")
            first_hashes[key] = obs_sha
    if len(covered) != 35200:
        raise PendingEvidence(f"final outcomes: {35200 - len(covered)} missing state/method cells")
    return values, state_ids


def read_training_diagnostics(reader, entries, matrix, registrations, window_manifests):
    frozen = {(r["suite"], r["method_id"]): r for r in matrix["instances"] if r["method"] in ("A", "B")}
    if len(entries) != 72:
        raise PendingEvidence(f"training diagnostics: need72 entries, found{len(entries)}")
    registered = {(r["suite"], r["visual_tokens"], r["seed"]): r for r in registrations["pairs"]}
    selected, summaries, jobs, reports = {}, [], set(), {}
    for item in entries:
        key = item.get("suite"), item.get("method_id")
        if key not in frozen or key in selected:
            raise ValueError("training diagnostic matrix contains unregistered/duplicate arm")
        identity = frozen[key]
        receipt = reader.read(item.get("receipt"), str(key) + ":receipt")
        validate_formal_receipt(receipt, receipt["metadata"])
        pair_ref = registered[(key[0], identity["visual_tokens"], identity["training_seed"])]
        pair = reader.read({"path": pair_ref["path"], "sha256": pair_ref["sha256"]}, str(key) + ":registered pair config")
        if receipt["pair_config"] != pair:
            raise ValueError("formal training diagnostics differ from preregistered hyperparameters")
        actual = selector_instance_identity({**receipt["metadata"], "selector_checkpoint_sha256": receipt["checkpoint_sha256"],
            "deployment_receipt_sha256": json_signature(receipt), "f01_report_sha256": receipt["f01_report_sha256"]})
        if actual != identity:
            raise ValueError("training diagnostics do not belong to frozen final checkpoint")
        report = reader.read(item.get("report"), str(key) + ":training_report")
        if (report.get("status") != "completed" or report.get("training_updates_completed") != 5000
                or report.get("best_checkpoint_sha256") != identity["checkpoint_sha256"]
                or report.get("best_update") != receipt["metadata"]["update"]
                or report.get("evaluations") != receipt["evaluations"] or report.get("vla_parameters_unchanged") is not True
                or report.get("committed_samples") != 40000 or report.get("next_sample_cursor") != 40000):
            raise ValueError("training report differs from complete selected checkpoint")
        best = min(receipt["evaluations"], key=lambda r: (r["validation_metric"], r["update"]))
        if item.get("selected_validation", {}).get("sha256") != best["artifact_sha256"]:
            raise ValueError("diagnostic artifact is not the selected checkpoint validation")
        validation = reader.read(item.get("selected_validation"), str(key) + ":selected_validation")
        windows = window_manifests[key[0]]
        valid_ids = set(windows["validation_window_ids"])
        expected = {r["window_id"]: r for r in windows["windows"] if r["window_id"] in valid_ids}
        observations = validation["observations"]
        if (len(observations) != len(expected) or {r["window_id"] for r in observations} != set(expected)
                or validation.get("update") != best["update"] or validation.get("arm") != identity["method"]
                or validation.get("validation_metric") != best["validation_metric"]):
            raise ValueError("selected diagnostics lack the complete unchanged validation panel")
        per_task = {}
        for task in range(10):
            group = [r for r in observations if r["task_id"] == task]
            if not group:
                raise ValueError("selected validation misses a task")
            for row in group:
                source = expected[row["window_id"]]
                kept = row["retained_indices"]
                if (source["task_id"] != task or source["episode_id"] != row["episode_id"] or source["split"] != "validation"
                        or len(kept) != identity["visual_tokens"] or kept != sorted(set(kept))
                        or any(type(i) is not int or not 0 <= i < 512 for i in kept)
                        or sum(i < 256 for i in kept) != identity["visual_tokens"] // 2
                        or any(not math.isfinite(row[k]) or row[k] < 0 for k in ("teacher_l1", "demonstration_l1"))):
                    raise ValueError("selected validation window/action/token diagnostic is invalid")
            per_task[str(task)] = {k: float(np.mean([r[k] for r in group])) for k in ("teacher_l1", "demonstration_l1")}
        macro = {k: float(np.mean([v[k] for v in per_task.values()])) for k in ("teacher_l1", "demonstration_l1")}
        if not math.isclose(macro["teacher_l1"], best["validation_metric"], rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("task-equal selected action error disagrees with selection metric")
        selected[key] = {r["window_id"]: r for r in observations}
        reports[key] = report
        reported_jobs = list(map(str, report.get("job_ids", [])))
        if not reported_jobs:
            raise PendingEvidence(str(key) + ": training report lacks allocation job IDs")
        if len(set(reported_jobs)) != len(reported_jobs) or any(not j.isascii() or not j.isdigit() for j in reported_jobs):
            raise ValueError("training report has invalid or duplicate allocation job IDs")
        jobs.update(reported_jobs)
        summaries.append(dict(suite=key[0], method_id=key[1], checkpoint_sha256=identity["checkpoint_sha256"],
            selected_update=best["update"], action_error_task_macro=macro, per_task=per_task,
            peak_cuda_memory_allocated_bytes=report.get("peak_cuda_memory_allocated_bytes"),
            unique_committed_windows=report.get("unique_committed_windows"), committed_samples=report.get("committed_samples")))
    if set(selected) != set(frozen):
        raise PendingEvidence("training diagnostics: missing selected formal arms")
    overlaps = []
    for suite in SUITES:
        for budget in FORMAL_BUDGETS:
            for seed in FORMAL_SEEDS:
                a, b = selected[(suite, f"A{budget}_seed{seed}")], selected[(suite, f"B{budget}_seed{seed}")]
                ra, rb = reports[(suite, f"A{budget}_seed{seed}")], reports[(suite, f"B{budget}_seed{seed}")]
                if any(ra.get(k) != rb.get(k) or not ra.get(k) for k in ("initial_scorer_sha256", "sample_order_sha256")):
                    raise ValueError("formal A/B training did not share initialization and data order")
                task_rows = {}
                for task in range(10):
                    pairs = [(set(a[w]["retained_indices"]), set(b[w]["retained_indices"])) for w in a if a[w]["task_id"] == task]
                    task_rows[str(task)] = dict(windows=len(pairs), overlap_fraction=float(np.mean([len(x & y) / budget for x, y in pairs])),
                        jaccard=float(np.mean([len(x & y) / len(x | y) for x, y in pairs])))
                overlaps.append(dict(suite=suite, visual_tokens=budget, seed=seed, per_task=task_rows,
                    overlap_fraction_task_macro=float(np.mean([v["overlap_fraction"] for v in task_rows.values()])),
                    jaccard_task_macro=float(np.mean([v["jaccard"] for v in task_rows.values()]))))
    return {"selected_action_errors": summaries, "AB_token_overlap": overlaps}, jobs


def summarize_cost(accounting, *, expected_job_ids, observed_job_ids):
    rows = accounting.get("jobs", [])
    index = {}
    for row in rows:
        job = str(row.get("job_id", ""))
        if not job.isascii() or not job.isdigit() or job in index:
            raise ValueError("GPU accounting has a missing/duplicate job ID")
        if row.get("experiment") != FORMAL_SCHEMA:
            raise ValueError("formal cost ledger contains another project/experiment")
        index[job] = row
    expected = set(map(str, expected_job_ids))
    if len(expected) != len(expected_job_ids) or set(index) != expected or not set(observed_job_ids) <= expected:
        raise PendingEvidence("GPU accounting must cover exactly the root complete job inventory and all evidence job IDs")
    by_mode, total = {}, 0.
    for job, row in index.items():
        seconds, gpus = row.get("elapsed_seconds"), row.get("gpus")
        status = str(row.get("status", "")).split()
        if not status or status[0].rstrip("+") not in TERMINAL_JOBS:
            raise PendingEvidence("GPU accounting nonterminal job: " + job)
        if (isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0
                or type(gpus) is not int or gpus < 0):
            raise ValueError("GPU accounting requires actual finite allocation seconds and GPU count")
        if job in observed_job_ids and gpus < 1:
            raise ValueError("an observed training/rollout/profiling job cannot be charged as a CPU-only allocation")
        gpu_seconds = seconds * gpus
        total += gpu_seconds
        mode = row.get("mode", "unspecified")
        by_mode[mode] = by_mode.get(mode, 0.) + gpu_seconds
    return dict(actual_allocated_gpu_seconds=total, actual_allocated_gpu_hours=total / 3600., unique_jobs=len(index),
        gpu_seconds_by_mode=by_mode, jobs=rows,
        scope="Each actual allocation counted once, including failed/retried engineering, loading, shared caches, training/validation/checkpointing, collection, final/development rollouts and both timing passes. Nested internal phase times are not added to this total.")


def analyze(evidence, registration, *, project_root):
    reader = Evidence(project_root)
    require_registration(registration)
    if (evidence.get("schema") != FORMAL_SCHEMA or evidence.get("kind") != "analysis_evidence"
            or evidence.get("registration_sha256") != json_signature(registration)):
        raise ValueError("formal analysis evidence manifest differs from registration")
    base = dict(version=VERSION, schema=FORMAL_SCHEMA, registration_sha256=json_signature(registration),
        analysis_script_sha256=file_sha256(__file__), analysis_runtime=dict(python=sys.version, numpy=np.__version__),
        evidence_manifest_sha256=json_signature(evidence), weights_loaded=False, sealed_state_values_read=False,
        main_experiment_delivery_complete=False,
        standalone_cache_cost=pending_cache_cost())
    try:
        # Nothing referencing a final result is followed until both gates pass.
        missing = [k for k in ("global_freeze", "release") if not evidence.get(k)]
        if missing:
            raise PendingEvidence(*missing)
        matrix = reader.read(evidence["global_freeze"], "global_freeze")
        validate_freeze_matrix(matrix, registration_sha256=json_signature(registration))
        release = reader.read(evidence["release"], "root release")
        validate_final_release(release, matrix, registration_sha256=json_signature(registration))
        for suite in SUITES:
            spec = evidence.get("suites", {}).get(suite, {})
            missing.extend(f"{suite}:{k}" for k in ("final_registry", "runs", "windows", "full_profile", "component_profile") if not spec.get(k))
        missing.extend(k for k in ("training", "accounting", "root_cost_inventory") if not evidence.get(k))
        if missing:
            raise PendingEvidence(*missing)
        registries, all_rows, attempts, latency, window_manifests, observed_jobs = {}, [], [], {}, {}, set()
        for suite in SUITES:
            spec = evidence["suites"][suite]
            registries[suite] = read_registry(reader, spec["final_registry"], suite, matrix["suites"][suite])
            windows = reader.read(spec["windows"], suite + ":window manifest")
            if windows.get("suite") != suite or windows.get("test_pixels_opened") is not False:
                raise ValueError("diagnostic windows must be the matching sealed-test formal manifest")
            val_ids = set(windows["validation_window_ids"])
            window_manifests[suite] = {"validation_window_ids": windows["validation_window_ids"],
                "windows": [r for r in windows["windows"] if r["window_id"] in val_ids]}
            del windows
            if any(row["window_manifest_sha256"] != spec["windows"]["sha256"] for row in matrix["instances"]
                    if row["suite"] == suite and row["method"] in ("A", "B")):
                raise ValueError("validation manifest differs from selected models")
            for run in spec["runs"]:
                rows, cost = read_final_run(reader, run, registry=registries[suite], matrix=matrix,
                    release=release, registration_sha=json_signature(registration))
                all_rows.extend(rows)
                attempts.append(dict(suite=suite, **cost))
                observed_jobs.update(cost["job_ids"])
            from cti_vla.evaluation.formal_profiling import analyze_formal_profile
            latency[suite] = {}
            for name, expected_pass in (("full_profile", "full"), ("component_profile", "components")):
                refs = spec[name]
                paths = {key: reader.path(refs.get(key), suite + ":" + name + ":" + key)
                    for key in ("config", "measurements", "summary", "calls")}
                if len({p.parent for p in paths.values()}) != 1 or {p.name for p in paths.values()} != {"config.json", "measurements.json", "summary.json", "calls.jsonl"}:
                    raise ValueError("profile references must identify one immutable complete output directory")
                config = json.loads(paths["config"].read_text(encoding="utf-8"))
                if config.get("global_freeze_sha256") != evidence["global_freeze"]["sha256"]:
                    raise ValueError("latency did not use the same global success freeze")
                actual = {r["identity"]["method_id"]: r["identity"] for r in config["manifest"]["methods"]}
                frozen = {r["method_id"]: r for r in matrix["instances"] if r["suite"] == suite}
                if actual != frozen:
                    raise ValueError("latency and final success use different deployment instances")
                summary = analyze_formal_profile(paths["config"].parent, registration)
                if summary["pass_name"] != expected_pass:
                    raise ValueError("full latency and component pass cannot be substituted")
                latency[suite][expected_pass] = summary
                observed_jobs.add(str(config["slurm_job_id"]))
            full_config = reader.read(spec["full_profile"]["config"], suite + ":full identity")
            component_config = reader.read(spec["component_profile"]["config"], suite + ":component identity")
            if (full_config["panel"] != component_config["panel"] or full_config["runtime"] != component_config["runtime"]):
                raise ValueError("full/components did not use the same raw panel/software runtime")
        outcomes, state_ids = assemble_outcomes(registries, all_rows)
        diagnostics, training_jobs = read_training_diagnostics(reader, evidence["training"], matrix, registration, window_manifests)
        observed_jobs.update(training_jobs)
        inventory = reader.read(evidence["root_cost_inventory"], "root complete cost inventory")
        if (inventory.get("schema") != FORMAL_SCHEMA or inventory.get("kind") != "final_cost_inventory"
                or inventory.get("issued_by") != "root" or inventory.get("complete") is not True
                or inventory.get("registration_sha256") != json_signature(registration)):
            raise PendingEvidence("root final cost inventory is not complete")
        cost = summarize_cost(reader.read(evidence["accounting"], "Slurm accounting"),
            expected_job_ids=inventory["job_ids"], observed_job_ids=observed_jobs)
        statistics = summarize_success(outcomes, state_ids=state_ids)
        reader.unchanged()
        return {**base, "status": "completed_core_analysis", "success": statistics, "latency": latency,
            "diagnostics": diagnostics, "cost": cost, "retained_failed_attempts": attempts,
            "read_evidence_sha256": reader.seen, "new_experiments_authorized": False}
    except PendingEvidence as exc:
        reader.unchanged()
        return {**base, "status": "pending", "missing": exc.missing, "main_table_generated": False,
            "read_evidence_sha256": reader.seen, "note": "No outcome estimates or performance claims until all registered evidence is complete."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registration", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    registration = json.loads(args.registration.read_text(encoding="utf-8"))
    if args.evidence.is_file():
        evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
        result = analyze(evidence, registration, project_root=args.project_root)
    else:
        require_registration(registration)
        result = dict(version=VERSION, status="pending", missing=["analysis evidence manifest: " + str(args.evidence)],
            main_table_generated=False, weights_loaded=False, sealed_state_values_read=False,
            analysis_script_sha256=file_sha256(__file__), main_experiment_delivery_complete=False,
            standalone_cache_cost=pending_cache_cost())
    if args.output:
        output = args.output.resolve()
        if args.project_root.resolve() not in output.parents or output.exists() or output.suffix.lower() != ".json":
            raise ValueError("analysis output must be a new project JSON artifact; preserve earlier results")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "missing", "main_table_generated") if k in result}, ensure_ascii=False))


if __name__ == "__main__":
    main()

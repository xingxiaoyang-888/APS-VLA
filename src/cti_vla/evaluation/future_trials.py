"""G1-F paired A/B development trials. No final-test manifest is opened."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

from cti_vla.data.identity import file_sha256
from cti_vla.data.initial_states import validate_initial_state_manifest
from cti_vla.evaluation.libero_runtime import run_episode
from cti_vla.evaluation.teacher_diagnostics import json_signature

DEVELOPMENT_SHA256 = "d06a3d76fdf577f023ff29cf1088f73fc514cb20c549c97d000a8bb4ff724f9e"
G0_PANEL_SHA256 = "632ccaad8a2d44892d7f4aa1cd6cf6880fd16da8eb99e0792acb8eed142cff5b"
METHOD_ORDER = ("dense", "uniform128", "future_A", "future_B")


def load_future_development_panel(development_path, g0_panel_path):
    if file_sha256(development_path) != DEVELOPMENT_SHA256 or file_sha256(g0_panel_path) != G0_PANEL_SHA256:
        raise ValueError("G1-F accepts only the existing frozen development initial states")
    development, anchor = [json.loads(Path(p).read_text(encoding="utf-8")) for p in (development_path, g0_panel_path)]
    for value in (development, anchor):
        validate_initial_state_manifest(value)
        if value["split"] != "development":
            raise ValueError("G1-F prohibits final-test initial states")
    if development["source"] != anchor["source"] or development["environment_seed"] != anchor["environment_seed"]:
        raise ValueError("development source/seed mismatch")
    originals = {row["trial_id"]: row for row in development["states"]}
    if Counter(row["task_id"] for row in anchor["states"]) != {0: 5, 3: 5, 5: 5} or any(originals.get(row["trial_id"]) != row for row in anchor["states"]):
        raise ValueError("development task mapping differs from G0")
    panel = {"schema_version": 1, "suite": development["suite"], "split": "development",
        "environment_seed": development["environment_seed"], "source": development["source"],
        "states": sorted((row for row in development["states"] if row["task_id"] in (0, 3, 5)),
                         key=lambda row: (row["task_id"], row["source_state_index"])),
        "development_manifest_sha256": DEVELOPMENT_SHA256, "g0_panel_sha256": G0_PANEL_SHA256,
        "test_opened": False, "rule": "all10 existing development states for each task0,3,5; same states for A/B and controls"}
    panel["panel_signature"] = json_signature(panel)
    _validate_panel(panel)
    return panel


def _validate_panel(panel):
    if panel.get("suite") == "libero_10":
        from cti_vla.data.long_initial_states import validate_long_development_panel
        validate_long_development_panel(panel)
        return
    if panel.get("suite") != "libero_spatial":
        raise ValueError("only explicitly registered Spatial or Long development suites are supported")
    unsigned = {k: v for k, v in panel.items() if k != "panel_signature"}
    if panel.get("panel_signature") != json_signature(unsigned) or panel.get("split") != "development" or panel.get("test_opened") is not False:
        raise ValueError("G1-F requires the signed development panel, never test")
    if Counter(row["task_id"] for row in panel["states"]) != {0: 10, 3: 10, 5: 10} or len({row["trial_id"] for row in panel["states"]}) != 30:
        raise ValueError("G1-F requires exactly task0,3,5 with10 development states each")
    if panel.get("development_manifest_sha256") != DEVELOPMENT_SHA256 or panel.get("g0_panel_sha256") != G0_PANEL_SHA256:
        raise ValueError("G1-F development source identities changed")


def _methods(methods, *, suite="libero_spatial", dense_reference=None, panel=None):
    methods = tuple(methods)
    if suite == "libero_10":
        if dense_reference is not None:
            from cti_vla.evaluation.future_dense_reuse import validate_dense_reference
            validate_dense_reference(dense_reference, panel)
            if len(methods) != 2 or set(methods) != {"future_A", "future_B"}:
                raise ValueError("dense reuse requires exactly A/B new trials")
            return ("future_A", "future_B")
        expected = ("dense", "future_A", "future_B")
        if len(methods) != 3 or set(methods) != set(expected):
            raise ValueError("Long preregistration requires exactly dense/A/B, without uniform")
        return expected
    if len(set(methods)) != len(methods) or not {"future_A", "future_B"}.issubset(methods) or set(methods) - set(METHOD_ORDER):
        raise ValueError("G1-F requires A/B with optional dense/uniform128 controls")
    return tuple(m for m in METHOD_ORDER if m in methods)


def future_trial_horizon(panel):
    _validate_panel(panel)
    return 520 if panel["suite"] == "libero_10" else 220


def _identity(panel, state, method):
    return {"trial_id": f"{state['trial_id']}:{method}", "state_trial_id": state["trial_id"],
        "method": method, "task_id": state["task_id"], "task_name": state["task_name"], "split": "development",
        "initial_state_sha256": state["initial_state_sha256"], "source_state_index": state["source_state_index"],
        "environment_seed": panel["environment_seed"]}


def validate_future_trial_identities(panel, methods, ledger, *, dense_reference=None):
    _validate_panel(panel)
    expected = {row["trial_id"]: row for state in panel["states"] for m in _methods(methods, suite=panel["suite"], dense_reference=dense_reference, panel=panel)
                for row in [_identity(panel, state, m)]}
    for event in ledger.events:
        if "trial_id" not in event:
            continue
        correct = expected.get(event["trial_id"])
        if correct is None or any(event.get(k) != v for k, v in correct.items()):
            raise ValueError("G1-F ledger trial differs from its paired state/method identity")


def evaluate_future_trials(panel, policies, ledger, environment_factory, *, reseed,
        policy_watchdog_seconds=60., stop_after=None, on_result=None, dense_reference=None):
    methods = _methods(policies, suite=panel["suite"], dense_reference=dense_reference, panel=panel)
    validate_future_trial_identities(panel, methods, ledger, dense_reference=dense_reference)
    if stop_after is not None and (type(stop_after) is not int or stop_after <= 0):
        raise ValueError("stop_after must be a positive trial count")
    ran = 0
    for state in panel["states"]:
        for method in methods:
            identity = _identity(panel, state, method)
            if identity["trial_id"] in ledger.completed():
                continue
            if stop_after is not None and ran >= stop_after:
                return ran
            ledger.append({**identity, "event": "start", "created_utc": datetime.now(timezone.utc).isoformat()})
            env = None
            try:
                reseed()
                env, instruction = environment_factory(state)
                result = run_episode(env, policies[method], instruction, state["initial_state"],
                                     policy_watchdog_seconds=policy_watchdog_seconds,
                                     max_steps=future_trial_horizon(panel))
            except Exception as exc:
                result = {"status": "infrastructure_error", "success": False, "termination": type(exc).__name__,
                    "error": str(exc), "error_phase": "environment_creation", "chunks": [], "executed_actions": [],
                    "policy_calls": 0, "control_steps": 0, "wait_steps": 0}
            finally:
                if env is not None:
                    try:
                        env.close()
                    except Exception as exc:
                        ledger.append({**identity, "event": "cleanup_error", "error": str(exc)})
            row = {**identity, **result, "event": "result", "created_utc": datetime.now(timezone.utc).isoformat()}
            ledger.append(row)
            ran += 1
            if on_result:
                on_result(row)
            if result["status"] == "infrastructure_error":
                raise RuntimeError("G1-F infrastructure failure retained; repair and resume the same trial")
    return ran


def summarize_future_trials(panel, methods, ledger, *, provenance, checkpoint_unchanged=None, dense_reference=None):
    methods = _methods(methods, suite=panel["suite"], dense_reference=dense_reference, panel=panel)
    validate_future_trial_identities(panel, methods, ledger, dense_reference=dense_reference)
    completed = ledger.completed()
    summaries = {}
    for method in methods:
        rows = [r for r in completed.values() if r["method"] == method]
        per_task = {}
        for task in (0, 3, 5):
            group = [r for r in rows if r["task_id"] == task]
            per_task[str(task)] = {"trials": len(group), "successes": sum(r["success"] for r in group),
                "success_rate": sum(r["success"] for r in group) / len(group) if group else None}
        summaries[method] = {"trials": len(rows), "successes": sum(r["success"] for r in rows),
            "policy_failures": sum(r["status"] == "policy_error" for r in rows), "per_task": per_task,
            "task_macro_success_rate": sum(r["success_rate"] for r in per_task.values()) / 3
                if all(r["trials"] == 10 for r in per_task.values()) else None}
    paired = []
    for state in panel["states"]:
        a = completed.get(f"{state['trial_id']}:future_A")
        b = completed.get(f"{state['trial_id']}:future_B")
        if a is not None and b is not None:
            paired.append({"state_trial_id": state["trial_id"], "task_id": state["task_id"],
                "A_success": bool(a["success"]), "B_success": bool(b["success"]),
                "B_minus_A": int(b["success"]) - int(a["success"])})
    # Starts surviving a hard kill must not silently become free successful trials.
    active, unknown_starts = {}, 0
    for event in ledger.events:
        tid = event.get("trial_id")
        if event.get("event") == "start":
            if tid in active:
                unknown_starts += 1
            active[tid] = event
        elif event.get("event") == "result":
            active.pop(tid, None)
    unknown_starts += len(active)
    attempts = [r for r in ledger.events if r.get("event") == "result"]
    done = len(completed) == 30 * len(methods)
    result = {"stage": "G1-F_Long_development" if panel["suite"] == "libero_10" else "G1-F_development",
        "status": "completed" if done and checkpoint_unchanged is True else "incomplete",
        "expected_trials": 30 * len(methods), "completed_trials": len(completed), "methods": summaries,
        "paired_AB": {"completed_pairs": len(paired), "results": paired,
            "B_minus_A_success_rate": sum(r["B_minus_A"] for r in paired) / 30 if len(paired) == 30 else None},
        "checkpoint_unchanged": checkpoint_unchanged, "test_opened": False,
        "cost": {"recorded_result_attempts": len(attempts), "unfinished_attempts_unknown_cost": unknown_starts,
            "known_policy_calls": sum(r.get("policy_calls", 0) for r in attempts),
            "policy_calls_total": None if unknown_starts else sum(r.get("policy_calls", 0) for r in attempts),
            "known_wall_seconds": sum(r.get("wall_seconds", 0.) for r in attempts),
            "scope": "Episode attempts include simulator work; interrupted attempts require scheduler reconciliation. Not deployment latency."},
        "trials_jsonl_sha256": file_sha256(ledger.path) if ledger.path.exists() else None,
        "provenance": provenance,
        "limitations": ("Fixed Long task0,3,5 development panel, official520-step horizon and dense/A/B only; no sealed-final evaluation or population claim."
            if panel["suite"] == "libero_10" else "Fixed three-task development panel, including prior G0 states; no test evaluation, population inference or benchmark claim.")}
    if dense_reference is not None:
        result.update(dense_reference_signature=dense_reference["signature"], reused_dense_trials=30,
            limitations="60 new A/B trials on the fixed30 Long development states; seed17 dense reference reused without new inference or cost. No final-test or population claim.")
    return result

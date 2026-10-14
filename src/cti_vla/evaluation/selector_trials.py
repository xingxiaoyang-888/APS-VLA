"""Development-only paired selector trials using the unchanged G0 runner."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

from cti_vla.data.identity import file_sha256
from cti_vla.data.initial_states import validate_initial_state_manifest
from cti_vla.evaluation.libero_runtime import run_episode
from cti_vla.evaluation.teacher_diagnostics import json_signature


def load_selector_development_panel(development_path, g0_panel_path, test_path) -> dict:
    """Use all ten dev states for each of the same three frozen G0 tasks.

    Held-out state content is read only for split integrity, never evaluated.
    This is an expanded development panel, including the previous G0 states.
    """
    payloads = [json.loads(Path(path).read_text(encoding="utf-8")) for path in
                (development_path, g0_panel_path, test_path)]
    development, anchor, heldout = payloads
    for value in payloads:
        validate_initial_state_manifest(value)
    if [value["split"] for value in payloads] != ["development", "development", "test"]:
        raise ValueError("selector pilot requires development states and a separate held-out integrity manifest")
    if any(value["source"] != development["source"] or value["environment_seed"] != development["environment_seed"] for value in payloads):
        raise ValueError("initial-state source/split protocol mismatch")
    anchor_counts = Counter(row["task_id"] for row in anchor["states"])
    if len(anchor_counts) != 3 or set(anchor_counts.values()) != {5}:
        raise ValueError("development task IDs must come from the frozen G0 three-by-five panel")
    if len(development["states"]) != 100 or set(Counter(row["task_id"] for row in development["states"]).values()) != {10} or len(heldout["states"]) != 400 or set(Counter(row["task_id"] for row in heldout["states"]).values()) != {40}:
        raise ValueError("expected the fixed ten-development/forty-test split for ten tasks")
    originals = {row["trial_id"]: row for row in development["states"]}
    if any(originals.get(row["trial_id"]) != row for row in anchor["states"]):
        raise ValueError("G0 anchor states differ from the registered development split")
    dev_hashes = {row["initial_state_sha256"] for row in development["states"]}
    if dev_hashes & {row["initial_state_sha256"] for row in heldout["states"]}:
        raise ValueError("development and final-test states overlap")
    states = sorted((row for row in development["states"] if row["task_id"] in anchor_counts),
                    key=lambda row: (row["task_id"], row["source_state_index"]))
    panel = {"schema_version": 1, "suite": "libero_spatial", "split": "development",
        "environment_seed": development["environment_seed"], "source": development["source"], "states": states,
        "rule": "all ten registered dev states of each of the three frozen G0 tasks; no outcome-based selection",
        "split_check": {"passed": True, "overlap": 0, "test_used_only_for_split_disjointness": True,
                        "development_manifest_sha256": file_sha256(development_path),
                        "g0_panel_sha256": file_sha256(g0_panel_path), "test_manifest_sha256": file_sha256(test_path)}}
    panel["panel_signature"] = json_signature(panel)
    return panel


def _trial_identity(panel, state, method):
    return {"trial_id": f"{state['trial_id']}:{method}", "state_trial_id": state["trial_id"], "method": method,
            "task_id": state["task_id"], "task_name": state["task_name"], "split": "development",
            "initial_state_sha256": state["initial_state_sha256"],
            "source_state_index": state["source_state_index"], "environment_seed": panel["environment_seed"]}


def validate_selector_trial_identities(panel, ledger) -> None:
    if panel["split"] != "development":
        raise ValueError("selector pilot is development-only")
    expected = {row["trial_id"]: row for state in panel["states"] for method in ("dense", "uniform128", "cti128")
                for row in [_trial_identity(panel, state, method)]}
    for event in ledger.events:
        if "trial_id" not in event:
            continue
        identity = expected.get(event["trial_id"])
        if identity is None or any(event.get(key) != value for key, value in identity.items()):
            raise ValueError("ledger trial identity differs from the frozen selector development panel")


def evaluate_development_trials(panel, policies, ledger, environment_factory, *, reseed,
                                 policy_watchdog_seconds=60., stop_after=None, on_result=None) -> int:
    """Resume identical trials; policy failures count, infrastructure errors halt.

    environment_factory(state) returns (env, instruction), and must set the
    registered environment seed. reseed() resets other shared RNGs per method.
    The parent CLI records source/checkpoint/panel identity in ledger signature.
    """
    if panel["split"] != "development" or set(policies) != {"dense", "uniform128", "cti128"}:
        raise ValueError("first selector pilot is development-only dense/uniform128/cti128")
    if stop_after is not None and (type(stop_after) is not int or stop_after <= 0):
        raise ValueError("stop_after must be positive")
    validate_selector_trial_identities(panel, ledger)
    ran = 0
    for state in panel["states"]:
        for method, policy in policies.items():
            trial_id = f"{state['trial_id']}:{method}"
            if trial_id in ledger.completed():
                continue
            if stop_after is not None and ran >= stop_after:
                return ran
            identity = _trial_identity(panel, state, method)
            ledger.append({**identity, "event": "start", "created_utc": datetime.now(timezone.utc).isoformat()})
            env = None
            try:
                reseed()
                env, instruction = environment_factory(state)
                result = run_episode(env, policy, instruction, state["initial_state"],
                                     policy_watchdog_seconds=policy_watchdog_seconds)
            except Exception as exc:
                result = {"status": "infrastructure_error", "success": False, "termination": type(exc).__name__,
                          "error": str(exc), "error_phase": "environment_creation", "chunks": [],
                          "executed_actions": [], "policy_calls": 0, "control_steps": 0, "wait_steps": 0}
            finally:
                if env is not None:
                    try:
                        env.close()
                    except Exception as exc:
                        ledger.append({**identity, "event": "cleanup_error", "error": str(exc)})
            row = {**identity, **result, "event": "result", "created_utc": datetime.now(timezone.utc).isoformat()}
            ledger.append(row)
            ran += 1
            if on_result is not None:
                on_result(row)
            if result["status"] == "infrastructure_error":
                raise RuntimeError("infrastructure failure retained; repair and resume this same trial ID")
    return ran


def summarize_selector_trials(panel, ledger, *, provenance, checkpoint_unchanged=None) -> dict:
    validate_selector_trial_identities(panel, ledger)
    completed = ledger.completed()
    methods = {}
    for method in ("dense", "uniform128", "cti128"):
        rows = [row for row in completed.values() if row["method"] == method]
        grouped = {task: [row for row in rows if row["task_id"] == task]
                   for task in sorted({state["task_id"] for state in panel["states"]})}
        per_task = {str(task): {"trials": len(group), "successes": sum(row["success"] for row in group),
                               "success_rate": sum(row["success"] for row in group) / len(group) if group else None}
                    for task, group in grouped.items()}
        methods[method] = {"trials": len(rows), "successes": sum(row["success"] for row in rows),
            "policy_failures": sum(row["status"] == "policy_error" for row in rows), "per_task": per_task,
            "task_macro_success_rate": sum(row["success_rate"] for row in per_task.values()) / len(per_task)
                if all(row["trials"] == 10 for row in per_task.values()) else None}
    done = len(completed) == 3 * len(panel["states"])
    return {"stage": "G4_development", "status": "completed" if done and checkpoint_unchanged is True else "incomplete",
        "expected_trials": 3 * len(panel["states"]), "completed_trials": len(completed), "methods": methods,
        "checkpoint_unchanged": checkpoint_unchanged, "initial_state_split": panel["split_check"],
        "trials_jsonl_sha256": file_sha256(ledger.path) if ledger.path.exists() else None,
        "provenance": provenance,
        "limitations": "Three-task development pilot only; timings are rollout diagnostics, not benchmarks; B3/ACL, final-state testing and multi-seed statistics are separate required experiments."}

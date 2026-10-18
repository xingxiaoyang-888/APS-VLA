"""Formal development trials and a fail-closed global sealed-final release.

Only this loader may open the formal final registry or state values. A root
release binds all72 selected models,16 baselines and four completed development
panels first. Repeated training seeds never create new independent initial states.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from types import SimpleNamespace

from cti_vla.data.identity import file_sha256
from cti_vla.data.initial_states import initial_state_sha256
from cti_vla.evaluation.formal_runtime import (
    FORMAL_SCHEMA, FORMAL_SUITES, FORMAL_BUDGETS, FORMAL_SEEDS, require_sha)
from cti_vla.evaluation.libero_runtime import run_episode
from cti_vla.evaluation.teacher_diagnostics import json_signature

ENVIRONMENT = {"environment_seed": 0, "runtime_seed": 17, "wait_steps": 10, "action_chunk": 8}


def method_id(method, visual_tokens, seed=None):
    if method == "dense" and visual_tokens == 512 and seed is None:
        return "dense"
    if method == "uniform" and visual_tokens in FORMAL_BUDGETS and seed is None:
        return f"uniform{visual_tokens}"
    if method in ("A", "B") and visual_tokens in FORMAL_BUDGETS and seed in FORMAL_SEEDS:
        return f"{method}{visual_tokens}_seed{seed}"
    raise ValueError("unregistered formal method/budget/seed")


def expected_method_ids():
    return ["dense", *[method_id("uniform", k) for k in FORMAL_BUDGETS],
        *[method_id(a, k, s) for k in FORMAL_BUDGETS for s in FORMAL_SEEDS for a in ("A", "B")]]


def selector_instance_identity(provenance):
    from cti_vla.evaluation.formal_runtime import formal_metadata
    p = formal_metadata(provenance)
    identity = {"schema": FORMAL_SCHEMA, "suite": p["suite"], "method": p["arm"],
        "visual_tokens": p["visual_tokens"], "training_seed": p["seed"],
        "method_id": method_id(p["arm"], p["visual_tokens"], p["seed"]),
        **{k: p[k] for k in ("config_sha256", "frozen_model_sha256", "input_acceptance_sha256", "model_revision",
            "stats_key", "pair_id", "selection_protocol_sha256", "window_manifest_sha256", "data_protocol_sha256")},
        "source_sha256": p["training_source_sha256"], "checkpoint_sha256": provenance["selector_checkpoint_sha256"],
        "deployment_receipt_sha256": provenance["deployment_receipt_sha256"], "f01_report_sha256": provenance["f01_report_sha256"],
        "training_complete": p["training_complete"], "future_head_deployed": False}
    validate_instance_identity(identity)
    return identity


def baseline_instance_identity(*, suite, method, visual_tokens, model_revision, frozen_model_sha256,
        source_files, input_acceptance_sha256):
    identifier = method_id(method, visual_tokens)
    if method not in ("dense", "uniform"):
        raise ValueError("baseline identity is only dense or deterministic uniform")
    from cti_vla.evaluation.formal_runtime import uniform_formal_indices
    config = {"schema": FORMAL_SCHEMA, "suite": suite, "method": method, "visual_tokens": visual_tokens,
        "retained_indices": list(range(512)) if method == "dense" else uniform_formal_indices(visual_tokens).tolist(),
        "environment": {**ENVIRONMENT, "max_steps": FORMAL_SUITES[suite]["max_steps"]}}
    identity = dict(schema=FORMAL_SCHEMA, suite=suite, method=method, visual_tokens=visual_tokens,
        training_seed=None, method_id=identifier, config_sha256=json_signature(config),
        model_revision=model_revision, stats_key=FORMAL_SUITES[suite]["stats_key"],
        frozen_model_sha256=frozen_model_sha256, source_sha256=json_signature(source_files),
        input_acceptance_sha256=input_acceptance_sha256, future_head_deployed=False)
    validate_instance_identity(identity)
    return identity


def validate_instance_identity(identity):
    """Minimal complete deployment identity, independent of server file paths."""
    if identity.get("schema") != FORMAL_SCHEMA or identity.get("suite") not in FORMAL_SUITES:
        raise ValueError("formal instance schema/suite mismatch")
    identifier = method_id(identity.get("method"), identity.get("visual_tokens"), identity.get("training_seed"))
    if identity.get("method_id") != identifier:
        raise ValueError("formal instance method ID differs from its identity")
    for key in ("config_sha256", "frozen_model_sha256", "source_sha256", "input_acceptance_sha256"):
        require_sha(identity.get(key), key)
    if identity.get("stats_key") != FORMAL_SUITES[identity["suite"]]["stats_key"]:
        raise ValueError("formal instance suite normalization differs")
    if not isinstance(identity.get("model_revision"), str) or not identity["model_revision"]:
        raise ValueError("formal instance base revision is missing")
    if identity["method"] in ("A", "B"):
        for key in ("checkpoint_sha256", "deployment_receipt_sha256", "pair_id", "f01_report_sha256",
                "selection_protocol_sha256", "window_manifest_sha256", "data_protocol_sha256"):
            require_sha(identity.get(key), key)
        if identity.get("training_complete") is not True:
            raise ValueError("formal final freeze cannot include unfinished training")
    if identity.get("future_head_deployed") is not False:
        raise ValueError("formal deployment must remove all auxiliary heads")
    return identifier


def validate_freeze_matrix(matrix, *, registration_sha256):
    """Validate global coverage before any final registry/state file access."""
    require_sha(registration_sha256, "registration_sha256")
    if (matrix.get("schema") != FORMAL_SCHEMA or matrix.get("kind") != "global_final_freeze"
            or matrix.get("registration_sha256") != registration_sha256):
        raise ValueError("formal global freeze registration mismatch")
    entries = matrix.get("instances", [])
    seen = {}
    for identity in entries:
        key = (identity.get("suite"), validate_instance_identity(identity))
        if key in seen:
            raise ValueError("duplicate formal global instance")
        seen[key] = identity
    expected = {(suite, mid) for suite in FORMAL_SUITES for mid in expected_method_ids()}
    if set(seen) != expected or len(entries) != 88:
        raise ValueError("final release requires all72 selected checkpoints and16 baselines")
    suites = matrix.get("suites", {})
    if set(suites) != set(FORMAL_SUITES):
        raise ValueError("final freeze must include all four suite panels")
    for suite, row in suites.items():
        for key in ("development_panel_sha256", "development_completion_sha256", "final_registry_sha256",
                "panel_source_sha256"):
            require_sha(row.get(key), suite + ":" + key)
        if (row.get("development_completed") is not True or row.get("development_unique_initial_states") != 100
                or set(row.get("development_method_ids", [])) != set(expected_method_ids())
                or len(row.get("development_method_ids", [])) != 22):
            raise ValueError("final release requires completed100-state development for every method and suite")
        # All methods of a suite use precisely the same base and input contract.
        base = seen[(suite, "dense")]
        for mid in expected_method_ids():
            identity = seen[(suite, mid)]
            if any(identity[k] != base[k] for k in ("frozen_model_sha256", "model_revision", "stats_key", "input_acceptance_sha256")):
                raise ValueError("formal global freeze mixes base/input identities within a suite")
    return seen


def make_final_release(matrix, *, registration_sha256, created_utc):
    """Root calls only after auditing the entire immutable matrix and dev evidence."""
    validate_freeze_matrix(matrix, registration_sha256=registration_sha256)
    if not isinstance(created_utc, str) or not created_utc:
        raise ValueError("root release requires a timestamp")
    payload = {"schema": FORMAL_SCHEMA, "kind": "sealed_final_release", "issued_by": "root",
        "registration_sha256": registration_sha256, "global_freeze_sha256": json_signature(matrix),
        "created_utc": created_utc, "all72_selected_models_frozen": True, "all16_baselines_frozen": True,
        "all4_development_panels_complete": True, "final_content_previously_opened": False,
        "release_scope": "exact frozen400 initial states per suite; no tuning or reselection after release"}
    return {**payload, "root_signed_payload_sha256": json_signature(payload)}


def validate_final_release(release, matrix, *, registration_sha256):
    validate_freeze_matrix(matrix, registration_sha256=registration_sha256)
    expected = make_final_release(matrix, registration_sha256=registration_sha256, created_utc=release.get("created_utc"))
    if release != expected:
        raise ValueError("formal final release is missing, changed or not root-finalized")


def load_formal_panel(*, suite, split, development_path=None, final_registry_path=None,
        sealed_final_path=None, release_path=None, release_file_sha256=None, matrix=None,
        registration_sha256=None):
    if suite not in FORMAL_SUITES or split not in ("development", "final"):
        raise ValueError("formal panel requires an explicit registered suite/split")
    if split == "development":
        from cti_vla.data.formal_initial_states import load_formal_development_panel
        panel = load_formal_development_panel(development_path)
        if panel["suite"] != suite:
            raise ValueError("formal development panel suite mismatch")
        return panel
    # Do not stat, read or hash either final path before all release checks pass.
    require_sha(release_file_sha256, "root release file SHA256")
    if release_path is None or file_sha256(release_path) != release_file_sha256:
        raise ValueError("formal final requires the exact root-issued release file")
    release = json.loads(Path(release_path).read_text(encoding="utf-8"))
    validate_final_release(release, matrix, registration_sha256=registration_sha256)
    frozen_suite = matrix["suites"][suite]
    if file_sha256(final_registry_path) != frozen_suite["final_registry_sha256"]:
        raise ValueError("formal final registry changed after root freeze")
    registry = json.loads(Path(final_registry_path).read_text(encoding="utf-8"))
    panel = json.loads(Path(sealed_final_path).read_text(encoding="utf-8"))
    validate_formal_final_panel(panel, registry, suite=suite,
        panel_source_sha256=frozen_suite["panel_source_sha256"])
    panel = dict(panel)
    panel["release_file_sha256"] = release_file_sha256
    panel["final_registry_sha256"] = frozen_suite["final_registry_sha256"]
    return panel


def validate_formal_final_panel(panel, registry, *, suite, panel_source_sha256):
    from cti_vla.data.formal_initial_states import validate_formal_final_registry, STATE_NAMESPACE
    from cti_vla.data.experiment_protocol import verify_payload
    validate_formal_final_registry(registry)
    verify_payload(panel, STATE_NAMESPACE)
    if (panel.get("registry_signature") != registry["content_signature"]
            or panel.get("release_required") != "root-complete-frozen-experiment-matrix"
            or panel.get("task_catalog") != registry.get("task_catalog")):
        raise ValueError("formal sealed panel does not bind its registered final identity set")
    keys = ("trial_id", "task_id", "task_name", "source_state_index", "source_file", "initial_state_sha256")
    for value in (registry, panel):
        if (value.get("suite") != suite or value.get("split") != "final"
                or value.get("environment_seed") != 0 or json_signature(value.get("source")) != panel_source_sha256):
            raise ValueError("formal final suite/source/environment identity differs from release")
        states = value.get("states", [])
        if (Counter(r.get("task_id") for r in states) != {i: 40 for i in range(10)}
                or len({r.get("trial_id") for r in states}) != 400
                or len({(r.get("task_id"), r.get("source_state_index")) for r in states}) != 400):
            raise ValueError("formal final requires40 unique registered states on every one of10 tasks")
    if any("initial_state" in r for r in registry["states"]):
        raise ValueError("final registry must contain indices/hashes only")
    index = {r["trial_id"]: r for r in registry["states"]}
    for row in panel["states"]:
        if (any(row.get(k) != index.get(row["trial_id"], {}).get(k) for k in keys)
                or initial_state_sha256(row["initial_state"]) != row["initial_state_sha256"]):
            raise ValueError("formal final state bytes differ from frozen index/hash registry")


def validate_execution_manifest(manifest, *, registration_sha256):
    if (manifest.get("schema") != FORMAL_SCHEMA or manifest.get("kind") != "evaluation_execution"
            or manifest.get("registration_sha256") != registration_sha256
            or manifest.get("suite") not in FORMAL_SUITES or manifest.get("split") not in ("development", "final")
            or manifest.get("environment") != {**ENVIRONMENT, "max_steps": FORMAL_SUITES[manifest["suite"]]["max_steps"]}):
        raise ValueError("formal evaluation execution identity/environment mismatch")
    methods = manifest.get("methods", [])
    identifiers = [validate_instance_identity(row["identity"]) for row in methods]
    if not methods or len(set(identifiers)) != len(identifiers) or any(row["identity"]["suite"] != manifest["suite"] for row in methods):
        raise ValueError("formal execution requires unique registered methods for one suite")
    if manifest["split"] == "final":
        matrix, release = manifest.get("global_freeze", {}), manifest.get("release", {})
        validate_final_release(release, matrix, registration_sha256=registration_sha256)
        frozen = {(row["suite"], row["method_id"]): row for row in matrix["instances"]}
        if any(frozen[(manifest["suite"], row["identity"]["method_id"])] != row["identity"] for row in methods):
            raise ValueError("formal final execution changes a frozen deployment identity")
    return identifiers


def audit_development_outputs(output_directories, *, panel, registration_sha256, expected_identities):
    """Build the root freeze's dev receipt from complete durable raw results.

    Read one output at a time. A report alone cannot assert completion; every
    method/state is reconstructed, and duplicate successful attempts fail.
    This function never accepts or reads a final-state path.
    """
    from cti_vla.data.formal_initial_states import validate_formal_development_panel
    validate_formal_development_panel(panel)
    suite = panel["suite"]
    expected = {row["method_id"]: row for row in expected_identities if row.get("suite") == suite}
    if set(expected) != set(expected_method_ids()) or len(expected) != 22:
        raise ValueError("development audit requires all22 frozen suite identities")
    for identity in expected.values():
        validate_instance_identity(identity)
    coverage, outputs = {}, []
    for directory in output_directories:
        directory = Path(directory)
        paths = {name: directory / name for name in ("config.json", "panel.json", "closed_loop_report.json", "trials.jsonl")}
        config, recorded_panel, report = [json.loads(paths[name].read_text(encoding="utf-8"))
            for name in ("config.json", "panel.json", "closed_loop_report.json")]
        manifest = config["manifest"]
        methods = validate_execution_manifest(manifest, registration_sha256=registration_sha256)
        if (manifest["suite"] != suite or manifest["split"] != "development" or recorded_panel != panel
                or config.get("panel_signature") != json_signature(panel)
                or report.get("status") != "completed" or report.get("checkpoint_unchanged") is not True):
            raise ValueError("formal development audit found incomplete or different panel evidence")
        if any(row["identity"] != expected[row["identity"]["method_id"]] for row in manifest["methods"]):
            raise ValueError("development methods differ from the globally frozen identities")
        signature = json_signature(config)
        events, completed, active = [], {}, {}
        with paths["trials.jsonl"].open(encoding="utf-8") as stream:
            for line in stream:
                event = json.loads(line)
                if event.get("run_signature") != signature:
                    raise ValueError("development raw event belongs to another run")
                events.append(event)
                if event.get("event") == "start":
                    if event["trial_id"] in completed:
                        raise ValueError("a completed development trial was restarted")
                    active[event["trial_id"]] = event
                elif event.get("event") == "result":
                    if event["trial_id"] not in active or type(event.get("success")) is not bool:
                        raise ValueError("development result lacks its durable start or boolean outcome")
                    active.pop(event["trial_id"])
                    if event.get("status") not in ("completed", "policy_error", "infrastructure_error"):
                        raise ValueError("development result has an unregistered status")
                    if event["status"] != "completed" and event["success"]:
                        raise ValueError("development error cannot count as a success")
                if event.get("event") == "result" and event.get("status") in ("completed", "policy_error"):
                    if event["trial_id"] in completed:
                        raise ValueError("duplicate completed development trial")
                    completed[event["trial_id"]] = event
        ledger = SimpleNamespace(path=paths["trials.jsonl"], events=events, completed=lambda: completed)
        reconstructed = summarize_formal_trials(panel, methods, ledger, provenance=report["provenance"], checkpoint_unchanged=True)
        if report != reconstructed or report["provenance"].get("run_signature") != signature:
            raise ValueError("development summary differs from durable raw results")
        for mid in methods:
            if mid in coverage:
                raise ValueError("a development method was counted from more than one output")
            coverage[mid] = report["methods"][mid]
        outputs.append({"path": str(directory), "sha256": {name: file_sha256(path) for name, path in paths.items()},
            "methods": methods, "completed_trials": report["completed_trials"]})
    if set(coverage) != set(expected_method_ids()) or any(v["trials"] != 100 for v in coverage.values()):
        raise ValueError("development global freeze lacks one or more complete100-state methods")
    return dict(schema=FORMAL_SCHEMA, kind="development_completion", suite=suite, status="completed",
        registration_sha256=registration_sha256, panel_signature=json_signature(panel), unique_initial_states=100,
        method_ids=expected_method_ids(), completed_trials=2200, instances_sha256=json_signature(expected),
        outputs=outputs, methods=coverage, test_opened=False,
        audit_scope="All22 methods rebuilt from durable raw100-state evidence; no seed replica is a new initial state.")


def _identity(panel, state, identifier):
    return {"trial_id": f"{state['trial_id']}:{identifier}", "state_trial_id": state["trial_id"],
        "method": identifier, "suite": panel["suite"], "split": panel["split"], "task_id": state["task_id"],
        "task_name": state["task_name"], "initial_state_sha256": state["initial_state_sha256"],
        "source_state_index": state["source_state_index"], "environment_seed": 0,
        "runtime_seed": 17, "configured_wait_steps": 10, "action_chunk": 8}


def validate_trial_identities(panel, methods, ledger):
    expected_count = 100 if panel["split"] == "development" else 400
    if (panel["suite"] not in FORMAL_SUITES or len(panel["states"]) != expected_count
            or Counter(r["task_id"] for r in panel["states"]) != {i: expected_count // 10 for i in range(10)}
            or panel.get("environment_seed") != 0 or not methods or set(methods) - set(expected_method_ids())):
        raise ValueError("formal trials require the exact balanced panel and registered methods")
    if panel["split"] == "final":
        require_sha(panel.get("release_file_sha256"), "formal final release")
    expected = {row["trial_id"]: row for state in panel["states"] for mid in methods for row in [_identity(panel, state, mid)]}
    for row in ledger.events:
        if "trial_id" in row and (row["trial_id"] not in expected or any(row.get(k) != v for k, v in expected[row["trial_id"]].items())):
            raise ValueError("formal ledger contains another panel/method/environment identity")


def evaluate_formal_trials(panel, policies, ledger, environment_factory, *, reseed,
        policy_watchdog_seconds=60., stop_after=None, on_result=None):
    methods = tuple(policies)
    validate_trial_identities(panel, methods, ledger)
    if stop_after is not None and (type(stop_after) is not int or stop_after <= 0):
        raise ValueError("stop_after must be a positive count")
    ran = 0
    for state in panel["states"]:
        for identifier in methods:
            identity = _identity(panel, state, identifier)
            if identity["trial_id"] in ledger.completed():
                continue
            if stop_after is not None and ran >= stop_after:
                return ran
            ledger.append({**identity, "event": "start", "created_utc": datetime.now(timezone.utc).isoformat()})
            started = time.perf_counter()
            env = None
            try:
                reseed()
                env, instruction = environment_factory(state)
                result = run_episode(env, policies[identifier], instruction, state["initial_state"], wait_steps=10,
                    max_steps=FORMAL_SUITES[panel["suite"]]["max_steps"], policy_watchdog_seconds=policy_watchdog_seconds)
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
            row["attempt_wall_seconds"] = time.perf_counter() - started
            ledger.append(row)
            ran += 1
            if on_result:
                on_result(row)
            if result["status"] == "infrastructure_error":
                raise RuntimeError("formal infrastructure attempt retained; repair and resume same trial")
    return ran


def summarize_formal_trials(panel, methods, ledger, *, provenance, checkpoint_unchanged=None):
    validate_trial_identities(panel, methods, ledger)
    completed = ledger.completed()
    summaries = {}
    for identifier in methods:
        rows = [r for r in completed.values() if r["method"] == identifier]
        tasks = {}
        for task in range(10):
            group = [r for r in rows if r["task_id"] == task]
            tasks[str(task)] = {"trials": len(group), "successes": sum(r["success"] for r in group),
                "success_rate": sum(r["success"] for r in group) / len(group) if group else None}
        summaries[identifier] = {"trials": len(rows), "successes": sum(r["success"] for r in rows),
            "success_rate": sum(r["success"] for r in rows) / len(rows) if rows else None, "per_task": tasks}
    active, orphaned = {}, 0
    for row in ledger.events:
        if row.get("event") == "start":
            orphaned += int(row["trial_id"] in active)
            active[row["trial_id"]] = row
        elif row.get("event") == "result":
            active.pop(row["trial_id"], None)
    attempts = [r for r in ledger.events if r.get("event") == "result"]
    unknown = orphaned + len(active)
    count = len(panel["states"])
    paired = {}
    for budget in FORMAL_BUDGETS:
        for seed in FORMAL_SEEDS:
            a, b = method_id("A", budget, seed), method_id("B", budget, seed)
            if a not in methods or b not in methods:
                continue
            rows = []
            for state in panel["states"]:
                left, right = completed.get(f"{state['trial_id']}:{a}"), completed.get(f"{state['trial_id']}:{b}")
                if left is not None and right is not None:
                    rows.append({"state_trial_id": state["trial_id"], "task_id": state["task_id"],
                        "A_success": bool(left["success"]), "B_success": bool(right["success"]),
                        "B_minus_A": int(right["success"]) - int(left["success"])})
            paired[f"k{budget}_seed{seed}"] = {"completed_pairs": len(rows), "expected_pairs": count,
                "B_minus_A_success_rate": sum(r["B_minus_A"] for r in rows) / count if len(rows) == count else None,
                "per_task": {str(t): {"pairs": sum(r["task_id"] == t for r in rows),
                    "B_minus_A": sum(r["B_minus_A"] for r in rows if r["task_id"] == t) / (count // 10)
                        if sum(r["task_id"] == t for r in rows) == count // 10 else None} for t in range(10)},
                "results": rows}
    return {"schema": FORMAL_SCHEMA, "kind": "evaluation_summary", "suite": panel["suite"], "split": panel["split"],
        "status": "completed" if len(completed) == count * len(methods) and checkpoint_unchanged is True else "incomplete",
        "expected_trials": count * len(methods), "completed_trials": len(completed), "unique_initial_states": count,
        "methods": summaries, "paired_AB": paired, "checkpoint_unchanged": checkpoint_unchanged,
        "test_opened": panel["split"] == "final", "provenance": provenance,
        "trials_jsonl_sha256": file_sha256(ledger.path) if ledger.path.exists() else None,
        "cost": {"recorded_result_attempts": len(attempts), "unfinished_attempts_unknown_cost": unknown,
            "known_policy_calls": sum(r.get("policy_calls", 0) for r in attempts),
            "policy_calls_total": None if unknown else sum(r.get("policy_calls", 0) for r in attempts),
            "known_wall_seconds": sum(r.get("wall_seconds", 0.) for r in attempts),
            "known_attempt_wall_seconds": sum(r.get("attempt_wall_seconds", 0.) for r in attempts),
            "scope": "Includes every episode attempt; all allocations require Slurm reconciliation. Not inference latency."},
        "inference_unit": "Initial states are paired across methods and seeds; repeated training seeds are not independent initial states."}

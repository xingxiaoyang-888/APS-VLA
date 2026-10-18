"""CPU-only acceptance of complete G0 evidence, recomputed from raw records."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
METHODS = ("official_dense", "dense", "uniform128")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    def invalid_constant(value):
        raise ValueError(f"non-finite JSON constant: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=invalid_constant)


def read_jsonl(path):
    content = Path(path).read_text(encoding="utf-8")
    require(content.endswith("\n"), f"unfinished JSONL record: {path}")
    rows = []
    for line in content.splitlines():
        require(bool(line.strip()), f"empty JSONL record: {path}")
        value = json.loads(line)
        require(isinstance(value, dict), "JSONL records must be objects")
        rows.append(value)
    return rows


def finite_number(value, *, low=0.0, high=None):
    return type(value) in (int, float) and math.isfinite(value) and value >= low and (high is None or value <= high)


def validate_cpu_junit(path):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    require(bool(suites), "CPU JUnit has no test suite")
    cases = list(root.iter("testcase"))
    require(bool(cases), "CPU JUnit contains no tests")
    require(sum(int(suite.attrib.get("tests", -1)) for suite in suites) == len(cases), "JUnit test counts do not match its test cases")
    for suite in suites:
        for kind in ("failures", "errors", "skipped"):
            require(kind in suite.attrib and int(suite.attrib[kind]) == 0, f"CPU JUnit has {kind} or lacks its count")
    for case in cases:
        require(not any(case.find(kind) is not None for kind in ("failure", "error", "skipped")), "CPU JUnit includes a failed/error/skipped test")
        require("test_libero_runtime" in case.attrib.get("classname", ""), "CPU JUnit must exclusively contain tests/test_libero_runtime.py")
    names = [case.attrib["name"] for case in cases]
    require(len(set(names)) == len(names), "CPU JUnit contains duplicate test cases")
    source = ROOT / "tests/test_libero_runtime.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    required_counts = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
            continue
        count = 1
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "parametrize":
                count *= len(ast.literal_eval(decorator.args[1]))
        required_counts[node.name] = count
    require(Counter(name.split("[", 1)[0] for name in names) == required_counts, "CPU JUnit omits or duplicates current runtime test cases")
    require("test_official_cpu_image_reference_when_tensorflow_available" in names, "official TensorFlow image reference test was not executed")
    return {"passed": True, "tests": len(cases), "failures": 0, "errors": 0, "skipped": 0,
            "junit_sha256": sha256(path), "test_source_sha256": sha256(source)}


def validate_observations(report, report_path):
    from cti_vla.data.experiment_protocol import load_experiment_protocol
    from cti_vla.data.libero import load_manifest
    require(report["stage"] == "g0_observation_parity" and report["status"] == "passed", "observation report is not passed G0 parity")
    require(report["checkpoint_unchanged"] is True, "observation run lacks end-of-run immutable-checkpoint verification")
    parity = report["dense_parity"]
    require(parity["passed"] is True and parity["observations"] == 90 and finite_number(parity["atol"], high=.002) and parity["atol"] > 0, "observation parity counts/tolerance invalid")
    require(finite_number(parity["max_abs_error"], high=parity["atol"]), "observation dense error exceeds tolerance")
    protocol_path = ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json"
    protocol = load_experiment_protocol(protocol_path)
    panel_path = protocol_path.parent / protocol.payload["panels"]["diagnostic_90"]["path"]
    panel = load_manifest(panel_path)
    require(report["provenance"]["panel_sha256"] == sha256(panel_path), "observation report uses a different frozen panel")
    require(report["provenance"]["protocol_signature"] == protocol.payload["content_signature"], "observation data protocol differs")
    record_path = report_path.parent / "observations.jsonl"
    require(report["observations_jsonl_sha256"] == sha256(record_path), "observation report/JSONL checksum mismatch")
    rows = read_jsonl(record_path)
    expected = {sample.sample_id: sample for sample in panel.samples}
    tasks = {episode.episode_id: episode.task_name for episode in panel.episodes}
    require(len(rows) == 90 and len({row["sample_id"] for row in rows}) == 90, "observations must contain 90 unique samples")
    require({row["sample_id"] for row in rows} == set(expected), "observed sample IDs differ from the frozen panel")
    for row in rows:
        sample = expected[row["sample_id"]]
        require((row["episode_id"], row["step_index"], row["stage"], row["task"]) == (sample.episode_id, sample.step_index, sample.stage, tasks[sample.episode_id]), "observation sample metadata mismatch")
        for key in ("passed", "pixels_equal", "prompt_equal", "gripper_equal", "action_postprocess_equal"):
            require(row[key] is True, f"observation did not pass {key}")
        require(finite_number(row["proprio_max_abs_error"], high=1e-6), "observation proprio error invalid")
        require(finite_number(row["dense_max_abs_error"], high=parity["atol"]), "observation action error invalid")
        if row["dense_max_abs_error"] != 0:
            # Producer subtracts torch.float32 actions; reconstruct the same
            # arithmetic rather than changing the rounding with float64.
            left, right = (np.asarray(row[key], dtype=np.float32) for key in ("official_normalized_actions", "migrated_normalized_actions"))
            require(left.shape == right.shape == (8, 7) and np.isfinite(left).all() and np.isfinite(right).all(), "nonzero parity error needs finite original [8,7] action arrays")
            require(float(np.max(np.abs(left - right))) == row["dense_max_abs_error"], "saved action arrays do not match reported error")
    phases = Counter(row["stage"] for row in rows)
    task_counts = Counter(row["task"] for row in rows)
    require(dict(phases) == {"early": 30, "middle": 30, "late": 30}, "G0 must cover three phases with 30 observations each")
    require(len(task_counts) == 10 and set(task_counts.values()) == {9}, "G0 must cover ten tasks with nine observations each")
    require(report["coverage"]["tasks"] == 10 and report["coverage"]["phases"] == dict(phases), "observation coverage summary mismatch")
    maximum = max(row["dense_max_abs_error"] for row in rows)
    require(maximum == parity["max_abs_error"], "observation maximum-error summary mismatch")
    require(report["policy_sample_forwards"] == 180 and report["vision_forwards"] == 90, "observation forward accounting mismatch")
    return {"passed": True, "observations": 90, "tasks": 10, "phases": dict(phases), "max_abs_error": maximum,
            "atol": parity["atol"], "observations_jsonl_sha256": sha256(record_path)}


def validate_closed_loop(report, report_path):
    from cti_vla.data.initial_states import validate_initial_state_manifest
    from cti_vla.evaluation.libero_runtime import compare_dense_trials
    require(report["stage"] == "g0_closed_loop" and report["status"] == "passed", "closed-loop report is not complete")
    require(report["checkpoint_unchanged"] is True, "closed-loop run lacks end-of-run immutable-checkpoint verification")
    folder = ROOT / "configs/manifests/spatial_initial_states_v1"
    panel_path, test_path = folder / "g0_development_15.json", folder / "init_states_test.json"
    panel, heldout = read_json(panel_path), read_json(test_path)
    validate_initial_state_manifest(panel)
    validate_initial_state_manifest(heldout)
    require(panel["split"] == "development" and heldout["split"] == "test" and panel["source"] == heldout["source"], "initial-state split/source definition mismatch")
    overlap = {row["initial_state_sha256"] for row in panel["states"]} & {row["initial_state_sha256"] for row in heldout["states"]}
    split = report["initial_state_split"]
    require(not overlap and split["passed"] is True and split["overlap"] == 0, "development/final initial-state overlap")
    require(split["development_manifest_sha256"] == sha256(panel_path) and split["test_manifest_sha256"] == sha256(test_path), "initial-state manifest checksum mismatch")
    config_path, records_path = report_path.parent / "config.json", report_path.parent / "trials.jsonl"
    config = read_json(config_path)
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    signature = hashlib.sha256(encoded).hexdigest()
    require(signature == report["provenance"]["run_signature"], "closed-loop configuration signature mismatch")
    for key, value in config.items():
        if key != "runtime":
            require(report["provenance"][key] == value, f"closed-loop report/config disagree on {key}")
    require(config["methods"] == list(METHODS) and config["wait_steps"] == 10 and config["max_steps"] == 220 and config["policy_watchdog_seconds"] == 60, "closed-loop execution protocol mismatch")
    require(config["panel_signature"] == panel["content_signature"], "closed-loop panel signature mismatch")
    require(report["trials_jsonl_sha256"] == sha256(records_path), "closed-loop report/JSONL checksum mismatch")
    events = read_jsonl(records_path)
    require(all(row["run_signature"] == signature for row in events), "mixed run configurations in ledger")
    states = {row["trial_id"]: row for row in panel["states"]}
    expected = {f"{state}:{method}" for state in states for method in METHODS}
    completed = {}
    infrastructure_retries = 0
    for row in events:
        if row["event"] != "result":
            continue
        require(row["trial_id"] in expected, "unexpected trial ID in ledger")
        if row["status"] == "infrastructure_error":
            infrastructure_retries += 1
            continue
        require(row["status"] == "completed", "policy/interface failure prevents G0 acceptance")
        require(row["trial_id"] not in completed, "duplicate completed trial")
        completed[row["trial_id"]] = row
    require(set(completed) == expected and len(completed) == 45, "G0 requires all 45 paired method trials")
    for trial_id, row in completed.items():
        state = states[row["state_trial_id"]]
        require(trial_id == f"{row['state_trial_id']}:{row['method']}" and row["method"] in METHODS, "method/trial identity mismatch")
        for key in ("task_id", "task_name", "initial_state_sha256", "source_state_index"):
            require(row[key] == state[key], f"trial initial-state metadata mismatch: {key}")
        require(row["split"] == "development" and row["environment_seed"] == panel["environment_seed"], "trial split/environment seed mismatch")
        require(type(row["success"]) is bool and row["wait_steps"] == 10, "invalid success/wait accounting")
        require(type(row["control_steps"]) is int and 1 <= row["control_steps"] <= 220, "invalid control horizon")
        require(row["termination"] == ("environment_success" if row["success"] else "task_horizon"), "termination does not match success signal")
        require(row["success"] or row["control_steps"] == 220, "unsuccessful trial stopped before the frozen horizon")
        chunks = row["chunks"]
        require(len(chunks) == row["policy_calls"] == math.ceil(row["control_steps"] / 8), "chunk8 policy-call accounting mismatch")
        for index, chunk in enumerate(chunks):
            require(chunk["control_step"] == index * 8 and len(chunk["observation_sha256"]) == 64, "invalid chunk control step/observation hash")
            for key in ("normalized_actions", "environment_actions"):
                actions = np.asarray(chunk[key], dtype=np.float64)
                require(actions.shape == (8, 7) and np.isfinite(actions).all(), "chunk must contain finite [8,7] actions")
            require(np.abs(np.asarray(chunk["environment_actions"])).max() <= 1.00001, "out-of-range environment control")
            meta = chunk["metadata"]
            require(meta["method"] == row["method"] and meta["visual_tokens"] == (128 if row["method"] == "uniform128" else 512), "chunk method/token budget mismatch")
            require(meta["inputs_version"] == config["input_version"] and meta["action_version"] == config["action_version"] and meta["policy_calls"] == 1, "chunk input/action/call metadata mismatch")
            require(finite_number(chunk["engineering_seconds"], high=60), "chunk exceeded watchdog or lacks finite timing")
        verify = chunks[0]["metadata"]["preprocessing_verification"]
        require(verify["images_equal"] is True and verify["raw_proprio_equal"] is True and verify["normalized_proprio_max_abs_error"] == 0, "first policy query lacks official preprocessing verification")
        expected_actions = np.concatenate([np.asarray(chunk["environment_actions"]) for chunk in chunks])[:row["control_steps"]]
        require(np.array_equal(np.asarray(row["executed_actions"]), expected_actions), "executed controls do not match the chunk8 queue")
    pairs = [{"state_trial_id": state, **compare_dense_trials(completed[f"{state}:official_dense"], completed[f"{state}:dense"])} for state in states]
    require(all(row["passed"] for row in pairs), "recomputed paired dense rollout comparison failed")
    require(report["dense_parity"]["passed"] is True and report["dense_parity"]["atol"] == .002, "closed-loop parity summary failed")
    require({row["state_trial_id"] for row in report["dense_parity"]["pairs"]} == set(states) and len(report["dense_parity"]["pairs"]) == 15, "closed-loop parity summary lacks 15 unique pairs")
    reported_pairs = {row["state_trial_id"]: row for row in report["dense_parity"]["pairs"]}
    require(all(row == reported_pairs[row["state_trial_id"]] for row in pairs), "recomputed paired metrics differ from report")
    task_counts = Counter(row["task_id"] for row in states.values())
    require(len(task_counts) == 3 and set(task_counts.values()) == {5}, "closed-loop panel is not 3 tasks x 5 states")
    loop = report["closed_loop"]
    require(loop["passed"] is True and loop["num_tasks"] == 3 and loop["episodes_per_task"] == 5 and loop["expected_trials"] == loop["completed_trials"] == 45, "closed-loop count summary mismatch")
    by_method = {}
    for method in METHODS:
        rows = [row for row in completed.values() if row["method"] == method]
        value = {"trials": len(rows), "successes": sum(row["success"] for row in rows), "policy_failures": 0, "policy_calls": sum(row["policy_calls"] for row in rows)}
        require(value == loop["methods"][method], "method count summary mismatch")
        by_method[method] = value
    return {"passed": True, "num_tasks": 3, "episodes_per_task": 5, "completed_trials": 45,
            "methods": by_method, "paired_dense_comparisons": 15, "resolved_infrastructure_failures": infrastructure_retries,
            "trials_jsonl_sha256": sha256(records_path)}, {**split, "passed": True}


def accept(observations_path, closed_loop_path, cpu_tests_path):
    observations, closed = read_json(observations_path), read_json(closed_loop_path)
    provenance = {}
    for key in ("model_revision", "input_version", "packing_version", "action_version", "runtime_sha256"):
        value = observations["provenance"][key]
        require(isinstance(value, str) and bool(value) and value == closed["provenance"][key], f"G0 subreports use different {key}")
        provenance[key] = value
    require(observations["provenance"]["checkpoint_manifest_sha256"] == closed["provenance"]["manifest_sha256"], "G0 checkpoint manifests differ")
    cpu = validate_cpu_junit(cpu_tests_path)
    dense = validate_observations(observations, observations_path)
    loop, split = validate_closed_loop(closed, closed_loop_path)
    return {"stage": "G0", "status": "passed", "dense_parity": dense, "closed_loop": loop,
            "initial_state_split": split, "cpu_tests": cpu, "checkpoint_unchanged": True,
            "provenance": {**provenance, "checkpoint_manifest_sha256": observations["provenance"]["checkpoint_manifest_sha256"],
                           "observation_report_sha256": sha256(observations_path), "closed_loop_report_sha256": sha256(closed_loop_path),
                           "acceptance_script_sha256": sha256(__file__), "created_utc": datetime.now(timezone.utc).isoformat()},
            "limitations": "G0 engineering acceptance only. Development success counts and engineering timings are not final research results."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--closed-loop", type=Path, required=True)
    parser.add_argument("--cpu-tests", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        report = accept(args.observations, args.closed_loop, args.cpu_tests)
    except Exception as exc:
        report = {"stage": "G0", "status": "failed", "error": str(exc), "created_utc": datetime.now(timezone.utc).isoformat()}
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(json.dumps({"status": report["status"], "output": str(args.output), "error": report.get("error")}), flush=True)
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

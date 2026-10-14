"""Acceptance rejects partial or internally inconsistent G0 evidence."""
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import numpy as np
import pytest

from cti_vla.data.experiment_protocol import load_experiment_protocol
from cti_vla.data.libero import load_manifest
from cti_vla.evaluation.libero_runtime import ACTION_VERSION, INPUTS_VERSION, compare_dense_trials
from cti_vla.models.abstraction.packing import PACKING_VERSION


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("accept_g0_test", ROOT / "scripts/accept_g0.py")
acceptance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(acceptance)


def write(path, value):
    path.write_text(json.dumps(value, allow_nan=False), encoding="utf-8")


def write_rows(path, rows):
    path.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in rows), encoding="utf-8")


@pytest.fixture
def evidence(tmp_path):
    observations_dir, closed_dir = tmp_path / "obs", tmp_path / "closed"
    observations_dir.mkdir()
    closed_dir.mkdir()
    protocol = load_experiment_protocol(ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")
    panel_path = ROOT / "configs/manifests/spatial_g0g1_v1/diagnostic_90.json"
    panel = load_manifest(panel_path)
    task_by_episode = {episode.episode_id: episode.task_name for episode in panel.episodes}
    rows = [{"sample_id": sample.sample_id, "episode_id": sample.episode_id, "step_index": sample.step_index,
             "stage": sample.stage, "task": task_by_episode[sample.episode_id], "pixels_equal": True,
             "prompt_equal": True, "proprio_max_abs_error": 0., "dense_max_abs_error": 0.,
             "gripper_equal": True, "action_postprocess_equal": True, "passed": True} for sample in panel.samples]
    write_rows(observations_dir / "observations.jsonl", rows)
    provenance = {"model_revision": "a" * 40, "input_version": INPUTS_VERSION,
                  "packing_version": PACKING_VERSION, "action_version": ACTION_VERSION, "runtime_sha256": "b" * 64}
    observed = {"stage": "g0_observation_parity", "status": "passed", "checkpoint_unchanged": True,
                "dense_parity": {"passed": True, "observations": 90, "max_abs_error": 0., "atol": .002},
                "coverage": {"tasks": 10, "phases": {"early": 30, "middle": 30, "late": 30}},
                "observations_jsonl_sha256": acceptance.sha256(observations_dir / "observations.jsonl"),
                "provenance": {**provenance, "checkpoint_manifest_sha256": "c" * 64,
                               "panel_sha256": acceptance.sha256(panel_path), "protocol_signature": protocol.payload["content_signature"]},
                "policy_sample_forwards": 180, "vision_forwards": 90}
    state_folder = ROOT / "configs/manifests/spatial_initial_states_v1"
    state_panel = acceptance.read_json(state_folder / "g0_development_15.json")
    split = {"passed": True, "overlap": 0, "development_manifest_sha256": acceptance.sha256(state_folder / "g0_development_15.json"),
             "test_manifest_sha256": acceptance.sha256(state_folder / "init_states_test.json")}
    config = {**provenance, "manifest_sha256": "c" * 64, "methods": list(acceptance.METHODS),
              "wait_steps": 10, "max_steps": 220, "policy_watchdog_seconds": 60., "panel_signature": state_panel["content_signature"]}
    run_signature = hashlib.sha256(json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    actions = np.zeros((8, 7)).tolist()
    trials = []
    for state in state_panel["states"]:
        for method in acceptance.METHODS:
            metadata = {"method": method, "visual_tokens": 128 if method == "uniform128" else 512,
                        "inputs_version": INPUTS_VERSION, "action_version": ACTION_VERSION, "policy_calls": 1,
                        "preprocessing_verification": {"images_equal": True, "raw_proprio_equal": True, "normalized_proprio_max_abs_error": 0.}}
            chunk = {"control_step": 0, "observation_sha256": "d" * 64, "normalized_actions": deepcopy(actions),
                     "environment_actions": deepcopy(actions), "engineering_seconds": .1, "metadata": metadata}
            trials.append({"event": "result", "run_signature": run_signature, "trial_id": f"{state['trial_id']}:{method}",
                           "state_trial_id": state["trial_id"], "task_id": state["task_id"], "task_name": state["task_name"],
                           "initial_state_sha256": state["initial_state_sha256"], "source_state_index": state["source_state_index"],
                           "method": method, "split": "development", "environment_seed": 0, "status": "completed",
                           "success": True, "termination": "environment_success", "wait_steps": 10, "control_steps": 1,
                           "policy_calls": 1, "chunks": [chunk], "executed_actions": [deepcopy(actions[0])]})
    write_rows(closed_dir / "trials.jsonl", trials)
    write(closed_dir / "config.json", config)
    pairs = [{"state_trial_id": state["trial_id"], **compare_dense_trials(trials[index * 3], trials[index * 3 + 1])}
             for index, state in enumerate(state_panel["states"])]
    closed = {"stage": "g0_closed_loop", "status": "passed", "checkpoint_unchanged": True,
              "provenance": {**config, "run_signature": run_signature}, "initial_state_split": split,
              "trials_jsonl_sha256": acceptance.sha256(closed_dir / "trials.jsonl"),
              "dense_parity": {"passed": True, "atol": .002, "pairs": pairs},
              "closed_loop": {"passed": True, "num_tasks": 3, "episodes_per_task": 5, "expected_trials": 45, "completed_trials": 45,
                              "methods": {method: {"trials": 15, "successes": 15, "policy_failures": 0, "policy_calls": 15} for method in acceptance.METHODS}}}
    observed_path, closed_path = observations_dir / "observation_report.json", closed_dir / "closed_loop_report.json"
    write(observed_path, observed)
    write(closed_path, closed)
    source = ast.parse((ROOT / "tests/test_libero_runtime.py").read_text(encoding="utf-8"))
    test_names = []
    for node in source.body:
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
            continue
        parameters = [ast.literal_eval(dec.args[1]) for dec in node.decorator_list
                      if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == "parametrize"]
        test_names.extend([f"{node.name}[{value}]" for value in parameters[0]] if parameters else [node.name])
    tree = ET.Element("testsuites")
    suite = ET.SubElement(tree, "testsuite", tests=str(len(test_names)), errors="0", failures="0", skipped="0")
    for name in test_names:
        ET.SubElement(suite, "testcase", name=name, classname="tests.test_libero_runtime")
    cpu_path = tmp_path / "runtime_cpu.xml"
    ET.ElementTree(tree).write(cpu_path)
    return observed_path, closed_path, cpu_path


def test_complete_evidence_is_accepted_and_exposes_g1_contract(evidence):
    report = acceptance.accept(*evidence)
    assert report["stage"] == "G0" and report["status"] == "passed"
    assert report["dense_parity"]["observations"] == 90
    assert report["closed_loop"]["completed_trials"] == 45
    from cti_vla.evaluation.teacher_diagnostics import require_g0
    require_g0(report, model_revision="a" * 40, input_version=INPUTS_VERSION, packing_version=PACKING_VERSION)


@pytest.mark.parametrize("field", ["checkpoint_unchanged", "coverage", "version", "split", "count"])
def test_positive_summary_booleans_cannot_hide_invalid_report_fields(evidence, field):
    observation_path, closed_path, _ = evidence
    target = closed_path if field in ("split", "count") else observation_path
    report = acceptance.read_json(target)
    if field == "checkpoint_unchanged":
        report.pop(field)
    elif field == "coverage":
        report["coverage"]["phases"] = {"early": 90}
    elif field == "version":
        report["provenance"]["input_version"] = "legacy-processor-only"
    elif field == "split":
        report["initial_state_split"]["overlap"] = 1
    else:
        report["closed_loop"]["completed_trials"] = 44
    write(target, report)
    with pytest.raises((ValueError, KeyError)):
        acceptance.accept(*evidence)


@pytest.mark.parametrize("mutation", ["missing_observation", "duplicate_trial", "policy_error", "unpaired_drift", "wrong_queue", "nan_action"])
def test_actual_records_are_recomputed_instead_of_trusting_passed_flags(evidence, mutation):
    observation_path, closed_path, _ = evidence
    report_path = observation_path if mutation == "missing_observation" else closed_path
    ledger_path = report_path.parent / ("observations.jsonl" if mutation == "missing_observation" else "trials.jsonl")
    rows = acceptance.read_jsonl(ledger_path)
    if mutation == "missing_observation":
        rows.pop()
    elif mutation == "duplicate_trial":
        rows.append(deepcopy(rows[0]))
    elif mutation == "policy_error":
        rows[2]["status"] = "policy_error"
    elif mutation == "unpaired_drift":
        rows[1]["chunks"][0]["observation_sha256"] = "e" * 64
    elif mutation == "wrong_queue":
        rows[2]["executed_actions"][0][0] = .5
    else:
        rows[2]["chunks"][0]["normalized_actions"][0][0] = "NaN"
    write_rows(ledger_path, rows)
    report = acceptance.read_json(report_path)
    report["observations_jsonl_sha256" if mutation == "missing_observation" else "trials_jsonl_sha256"] = acceptance.sha256(ledger_path)
    write(report_path, report)
    with pytest.raises((ValueError, KeyError)):
        acceptance.accept(*evidence)


def test_cpu_skip_prevents_gate_even_if_all_other_reports_pass(evidence):
    cpu_path = evidence[2]
    tree = ET.parse(cpu_path)
    suite = next(tree.getroot().iter("testsuite"))
    suite.attrib["skipped"] = "1"
    case = next(row for row in suite if row.attrib["name"] == "test_official_cpu_image_reference_when_tensorflow_available")
    ET.SubElement(case, "skipped")
    tree.write(cpu_path)
    with pytest.raises(ValueError, match="skipped"):
        acceptance.accept(*evidence)


def test_report_record_checksum_mismatch_is_rejected(evidence):
    record_path = evidence[0].parent / "observations.jsonl"
    with record_path.open("a", encoding="utf-8") as stream:
        stream.write("{}\n")
    with pytest.raises(ValueError, match="checksum mismatch"):
        acceptance.accept(*evidence)


def test_nonzero_small_action_error_uses_producers_float32_arithmetic(evidence):
    report_path = evidence[0]
    record_path = report_path.parent / "observations.jsonl"
    rows = acceptance.read_jsonl(record_path)
    left, right = np.zeros((8, 7), dtype=np.float32), np.zeros((8, 7), dtype=np.float32)
    # Both values are exactly representable in bf16 as well. Their difference
    # rounds differently in float32 and float64 despite the same stored arrays.
    left[0, 0], right[0, 0] = 2 ** -10, 2 ** -40
    error = float(np.max(np.abs(left - right)))
    assert error != float(np.max(np.abs(left.astype(np.float64) - right.astype(np.float64))))
    rows[0].update(official_normalized_actions=left.tolist(), migrated_normalized_actions=right.tolist(), dense_max_abs_error=error)
    write_rows(record_path, rows)
    report = acceptance.read_json(report_path)
    report["dense_parity"]["max_abs_error"] = error
    report["observations_jsonl_sha256"] = acceptance.sha256(record_path)
    write(report_path, report)
    assert acceptance.accept(*evidence)["status"] == "passed"


def test_failed_cli_writes_failed_gate_and_exits_nonzero(tmp_path):
    output = tmp_path / "gate.json"
    result = subprocess.run([sys.executable, str(ROOT / "scripts/accept_g0.py"), "--observations", str(tmp_path / "missing.json"),
                             "--closed-loop", str(tmp_path / "missing.json"), "--cpu-tests", str(tmp_path / "missing.xml"),
                             "--output", str(output)], capture_output=True, text=True)
    assert result.returncode != 0
    report = acceptance.read_json(output)
    assert report["stage"] == "G0" and report["status"] == "failed" and report["error"]

from contextlib import nullcontext
from copy import deepcopy
import json
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from cti_vla.data.experiment_protocol import signed_payload
from cti_vla.data.identity import file_sha256
from cti_vla.data.initial_states import STATE_NAMESPACE, initial_state_sha256
from cti_vla.evaluation.libero_runtime import _observation_hash
from cti_vla.evaluation.profiling import (PANEL_NAMESPACE, PHASES, ProfileConfig, ProfileJournal, ProfileMethod,
    RawObservation, StageRecorder, load_raw_panel, profile_methods, read_profile_cost, summarize_latencies,
    verify_measurement_journal)

ROOT = Path(__file__).resolve().parents[1]


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def sample(index=0):
    return RawObservation(f"obs{index}", f"episode{index}", "task", "pick up bowl", "first", {
        "agentview_image": np.full((4, 4, 3), index, dtype=np.uint8),
        "robot0_eye_in_hand_image": np.full((4, 4, 3), index + 1, dtype=np.uint8),
        "robot0_eef_pos": np.zeros(3), "robot0_eef_quat": np.asarray([0., 0., 0., 1.]),
        "robot0_gripper_qpos": np.zeros(2)})


class Clock:
    device = torch.device("cpu")
    def __init__(self):
        self.log, self.tick = [], 0
    def synchronize(self):
        self.log.append("sync")
    def reset_peak(self):
        self.log.append("reset_peak")
    def memory(self):
        return {k: None for k in ("allocated", "reserved", "peak_allocated", "peak_reserved")}
    def event(self):
        return None
    def timer(self):
        self.log.append("timer")
        self.tick += 1_000_000
        return self.tick


def factory(log, *, cached=True, fail=False, mutate=False):
    def create():
        context = None
        language = set()
        def set_context(value):
            nonlocal context
            context = value
        def clear():
            log.append("clear_language")
            language.clear()
        def prime(instruction):
            log.append("prime_language")
            language.add(instruction)
        def policy(observation, instruction):
            log.append(("full_raw_policy", observation["agentview_image"].shape, context is not None))
            for phase in PHASES:
                with context(phase) if context else nullcontext():
                    log.append(phase)
                    if phase == "vision" and fail:
                        raise RuntimeError("synthetic policy failure")
                    if phase == "vision" and mutate:
                        observation["agentview_image"][0, 0, 0] += 1
            return SimpleNamespace(environment_actions=np.zeros((8, 7)))
        return ProfileMethod(policy, {"cache_scope": "language_only" if cached else "none",
            "instruction_cache_enabled": cached, "synthetic": True}, set_context, clear, prime)
    return create


def test_primary_calls_recompute_every_phase_and_components_never_pollute_primary(tmp_path):
    log, clock = [], Clock()
    journal = ProfileJournal(tmp_path / "calls.jsonl", {"synthetic": True})
    config = ProfileConfig(warmup_calls=2, repeats=2, component_repeats=1, synthetic=True)
    result = profile_methods([sample(0), sample(1)], {"dense": factory(log), "cti": factory(log)},
                             config=config, clock=clock, emit=journal, timer=clock.timer)
    # Per method: 2 warmups + 2 observations * 2 instruction modes * 3 rounds.
    assert result["sample_policy_forwards"] == 28
    assert log.count("vision") == log.count("condition_selection") == log.count("policy") == 28
    assert len([item for item in log if isinstance(item, tuple) and item[0] == "full_raw_policy"]) == 28
    assert log.count("clear_language") == 16 and log.count("prime_language") == 12
    assert all("components" not in row for row in result["rows"] if row["kind"] == "main")
    assert all(set(row["components"]) == set(PHASES) for row in result["rows"] if row["kind"] == "components")
    # One sync before each block, exactly two around each complete measured call.
    assert clock.log.count("sync") == 6 + 2 * 28
    cost = read_profile_cost(tmp_path / "calls.jsonl")
    assert cost["completed"] == 28 and cost["failed"] == cost["unknown_completion"] == 0
    assert cost["attempts_by_pass"] == {"warmup": 4, "main": 16, "components": 8}
    summary = summarize_latencies(result, bootstrap_repeats=100)
    assert all(row["count"] == 4 for row in summary["primary"])
    assert all(row["speedup_ratio_of_paired_means"] == 1 for row in summary["paired_dense_comparisons"])
    assert summary["paired_dense_comparisons"][0]["episode_clusters"] == 2
    result["cost"] = cost
    assert verify_measurement_journal(result, tmp_path / "calls.jsonl") == cost
    changed = deepcopy(result)
    changed["rows"][0]["elapsed_ms"] *= 2
    with pytest.raises(ValueError, match="durable measured"):
        verify_measurement_journal(changed, tmp_path / "calls.jsonl")


def test_component_regions_do_not_synchronize_or_allow_nested_timing():
    clock = Clock()
    recorder = StageRecorder(clock, clock.timer)
    for name in PHASES:
        with recorder.phase(name):
            pass
    assert clock.log.count("sync") == 0
    assert set(recorder.report()) == set(PHASES)
    with recorder.phase("vision"):
        with pytest.raises(ValueError, match="nonnested"):
            with recorder.phase("policy"):
                pass


def test_methods_reject_vision_cache_and_shared_observation_mutation():
    clock = Clock()
    config = ProfileConfig(warmup_calls=0, repeats=1, component_repeats=0, synthetic=True)
    bad = factory([])()
    bad.metadata = {"cache_scope": "vision"}
    with pytest.raises(ValueError, match="forbids"):
        profile_methods([sample()], {"dense": lambda: bad}, config=config, clock=clock, emit=lambda e: None)
    with pytest.raises(ValueError, match="mutated"):
        profile_methods([sample()], {"dense": factory([], mutate=True)}, config=config, clock=clock, emit=lambda e: None)


def test_failed_call_is_charged_and_failure_is_not_a_timing_sample(tmp_path):
    path = tmp_path / "calls.jsonl"
    journal = ProfileJournal(path, {"synthetic": True})
    with pytest.raises(RuntimeError, match="synthetic policy failure"):
        profile_methods([sample()], {"dense": factory([], fail=True)},
                         config=ProfileConfig(warmup_calls=0, repeats=1, component_repeats=0, synthetic=True),
                         clock=Clock(), emit=journal)
    assert read_profile_cost(path)["failed"] == 1
    assert read_profile_cost(path)["completed"] == 0
    with pytest.raises(FileExistsError):
        ProfileJournal(path, {"synthetic": True})


def test_durable_start_without_completion_keeps_unknown_charge(tmp_path):
    path = tmp_path / "calls.jsonl"
    journal = ProfileJournal(path, {"synthetic": True})
    journal({"event": "start", "call_id": 0, "method": "dense", "instruction_mode": "cold",
             "kind": "main", "round": 0, "observation_id": "o", "episode_id": "e"})
    cost = read_profile_cost(path)
    assert cost["sample_policy_forwards_attempted"] == cost["unknown_completion"] == 1
    assert cost["completed"] == 0


def test_paired_bootstrap_averages_repeats_and_keeps_episode_clusters():
    # Two episodes, three observations each, five repeats: never 30 independent
    # episodes. Dense/selector ratios are exactly two in every paired state.
    rows = []
    episodes = {f"o{i}": f"e{i // 3}" for i in range(6)}
    for method, factor in (("dense", 2.), ("cti", 1.)):
        for repeat in range(5):
            for index, (oid, eid) in enumerate(episodes.items()):
                rows.append({"kind": "main", "method": method, "instruction_mode": "cold", "round": repeat,
                             "observation_id": oid, "episode_id": eid, "elapsed_ms": factor * (index + 1 + repeat),
                             "memory_bytes": {"peak_allocated": 100, "peak_reserved": 200}})
    result = {"rows": rows, "methods": {"dense": {}, "cti": {}}, "synthetic": True,
              "observations": 6, "observation_episodes": episodes, "config": {"instruction_modes": ["cold"], "repeats": 5}}
    summary = summarize_latencies(result, bootstrap_repeats=100)
    comparison = summary["paired_dense_comparisons"][0]
    assert comparison["observations"] == 6 and comparison["episode_clusters"] == 2
    assert comparison["speedup_ratio_of_paired_means"] == 2
    assert comparison["speedup_ci95_episode_cluster"] == [2, 2]
    shortened = deepcopy(result)
    shortened["rows"] = [row for row in shortened["rows"] if row["round"] != 4]
    with pytest.raises(ValueError, match="omit/add"):
        summarize_latencies(shortened, bootstrap_repeats=100)


def panel_fixture(root, *, split="development", queries=3):
    def write(name, value):
        path = root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return {"path": name, "sha256": file_sha256(path)}
    sid = "state-trial"
    state_hash = initial_state_sha256([1., 2., 3.])
    states = signed_payload({"schema_version": 1, "suite": "libero_spatial", "split": split,
        "environment_seed": 0, "states": [{"trial_id": sid, "task_id": 0, "task_name": "task",
            "source_state_index": 0, "initial_state": [1., 2., 3.], "initial_state_sha256": state_hash}]}, STATE_NAMESPACE)
    state_ref = write("states.json", states)
    chunks, rows = [], []
    phase_indices = {0: "first"} if queries == 1 else ({0: "first", 1: "last"} if queries == 2 else {0: "first", (queries - 1) // 2: "middle", queries - 1: "last"})
    for index in range(queries):
        raw = sample(index).observation
        chunks.append({"observation_sha256": _observation_hash(raw)})
        if index in phase_indices:
            archive = root / f"{index}.npz"
            np.savez(archive, **raw)
            rows.append({"observation_id": f"o{index}", "episode_id": sid, "query_index": index,
                "phase": phase_indices[index], "arrays": {"path": archive.name, "sha256": file_sha256(archive)}})
    receipt = write("dense.json", {"method": "dense", "status": "completed", "state_trial_id": sid,
        "initial_state_sha256": state_hash, "instruction": "pick up bowl", "model_revision": "synthetic",
        "policy_calls": queries, "chunks": chunks})
    panel = signed_payload({"schema_version": 1, "source_kind": "simulator_raw", "arrays_preprocessed": False,
        "split": split, "model_revision": "synthetic", "initial_states_manifest": state_ref,
        "episodes": [{"episode_id": sid, "task_name": "task", "instruction": "pick up bowl",
                      "policy_calls": queries, "dense_receipt": receipt}], "observations": rows}, PANEL_NAMESPACE)
    path = root / "panel.json"
    path.write_text(json.dumps(panel), encoding="utf-8")
    return path, panel


@pytest.mark.parametrize("queries", [1, 2, 3, 6])
def test_raw_panel_uses_actual_dense_first_middle_last_queries_and_shortfalls(tmp_path, queries):
    path, _ = panel_fixture(tmp_path, queries=queries)
    samples, provenance = load_raw_panel(path)
    assert len(samples) == min(queries, 3)
    assert provenance["short_trajectory_observations_missing"] == max(0, 3 - queries)


def test_test_split_guard_runs_before_opening_any_array_or_state_reference(tmp_path):
    panel = signed_payload({"schema_version": 1, "source_kind": "simulator_raw", "arrays_preprocessed": False,
                            "split": "test"}, PANEL_NAMESPACE)
    path = tmp_path / "panel.json"
    path.write_text(json.dumps(panel), encoding="utf-8")
    with pytest.raises(ValueError, match="configuration freeze"):
        load_raw_panel(path)


def test_matching_archive_hash_cannot_disguise_wrong_observation_bytes(tmp_path):
    path, panel = panel_fixture(tmp_path)
    first = panel["observations"][0]
    archive = tmp_path / first["arrays"]["path"]
    np.savez(archive, **sample(42).observation)
    first["arrays"]["sha256"] = file_sha256(archive)
    panel.pop("content_signature")
    path.write_text(json.dumps(signed_payload(panel, PANEL_NAMESPACE)), encoding="utf-8")
    with pytest.raises(ValueError, match="actual dense"):
        load_raw_panel(path)


def test_formal_measurement_counts_cannot_be_shortened_or_run_on_cpu():
    with pytest.raises(ValueError, match="50 warmups"):
        ProfileConfig(warmup_calls=1)
    with pytest.raises(ValueError, match="allocated CUDA"):
        profile_methods([sample()], {"dense": factory([])}, config=ProfileConfig(), clock=Clock(), emit=lambda e: None)


def test_same_path_new_checkpoint_cannot_bypass_frozen_methods_manifest(tmp_path):
    runner = script("profile_observation_to_action")
    checkpoint, report, methods = tmp_path / "synthetic.bin", tmp_path / "g3.json", tmp_path / "methods.json"
    checkpoint.write_bytes(b"tiny synthetic checkpoint for hash tests only")
    report.write_text(json.dumps({"best_checkpoint_sha256": file_sha256(checkpoint)}), encoding="utf-8")
    payload = {"schema_version": 1, "methods": [{"name": "dense", "kind": "dense"}, {
        "name": "cti128", "kind": "selector", "target_tokens": 128, "checkpoint": str(checkpoint),
        "checkpoint_sha256": file_sha256(checkpoint), "training_report": str(report),
        "training_report_sha256": file_sha256(report)}]}
    methods.write_text(json.dumps(payload), encoding="utf-8")
    assert len(runner.method_specs(methods)) == 2
    checkpoint.write_bytes(b"different tiny synthetic checkpoint")
    report.write_text(json.dumps({"best_checkpoint_sha256": file_sha256(checkpoint)}), encoding="utf-8")
    with pytest.raises(ValueError, match="pin actual"):
        runner.method_specs(methods)


def test_final_runtime_freeze_is_checked_before_any_referenced_final_data(tmp_path):
    freeze = tmp_path / "freeze.json"
    frozen = {"status": "configuration_frozen", "stage": "final_evaluation",
              "model_revision": "synthetic", "methods_sha256": "synthetic-methods"}
    freeze.write_text(json.dumps(frozen), encoding="utf-8")
    panel = signed_payload({"schema_version": 1, "source_kind": "simulator_raw", "arrays_preprocessed": False,
        "split": "test", "model_revision": "synthetic", "configuration_freeze_sha256": file_sha256(freeze)}, PANEL_NAMESPACE)
    path = tmp_path / "panel.json"
    path.write_text(json.dumps(panel), encoding="utf-8")
    # No final-state or array reference even exists. Incorrect ordering would
    # raise KeyError/FileNotFoundError, instead of this frozen-protocol guard.
    with pytest.raises(ValueError, match="runtime/G0/statistics"):
        load_raw_panel(path, formal=True, freeze_receipt=freeze, methods_sha256="synthetic-methods", expected_freeze={})


def test_snapshot_analysis_writes_to_explicit_project_not_source_snapshot(tmp_path, monkeypatch):
    analyzer = script("analyze_observation_latency")
    project = tmp_path / "project"
    run = project / "results" / "run"
    run.mkdir(parents=True)
    source = project / "snapshots" / "g5_source"
    source.mkdir(parents=True)
    monkeypatch.setattr(analyzer, "ROOT", source)
    journal = ProfileJournal(run / "calls.jsonl", {"synthetic": True})
    clock = Clock()
    value = profile_methods([sample()], {"dense": factory([], cached=False)},
        config=ProfileConfig(warmup_calls=0, repeats=1, component_repeats=0, synthetic=True),
        clock=clock, emit=journal, timer=clock.timer)
    value.update(cost=read_profile_cost(run / "calls.jsonl"), checkpoint_unchanged=True)
    measured = run / "measurements.json"
    measured.write_text(json.dumps(value), encoding="utf-8")
    (run / "summary.json").write_text(json.dumps({"checkpoint_unchanged": True,
        "measurements_sha256": file_sha256(measured), "journal_sha256": file_sha256(run / "calls.jsonl")}), encoding="utf-8")
    output = project / "results" / "independent_analysis.json"
    args = SimpleNamespace(measurements=measured, output=output, project_root=project,
                           bootstrap_repeats=100, bootstrap_seed=1117)
    assert analyzer.run(args)["synthetic"] is True
    assert output.exists() and not list(source.iterdir())
    for forbidden in (run / "overwritten.json", source / "new.json"):
        args.output = forbidden
        with pytest.raises(ValueError, match="outside"):
            analyzer.run(args)

"""Independent arithmetic, pairing, provenance and interrupted-cost regressions."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("future_result_analysis", ROOT / "scripts/analyze_g1_future.py")
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def write_lines(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def test_cluster_resampling_uses_episode_totals_and_counts_not_individual_windows():
    rows = [{"episode_id": "long", "task_name": "task", "delta": 0}] * 9
    rows += [{"episode_id": "short", "task_name": "task", "delta": 10}]
    result = a.clustered_interval(rows, repeats=1000, seed=3)
    assert result["mean"] == 1
    assert result["ci95_percentile"] == [0, 10]  # All-long / all-short cluster draws.
    assert result["clusters"] == 2 and result["observations"] == 10
    assert a.clustered_interval(rows[:9], repeats=100)["ci95_percentile"] is None


@pytest.fixture
def validation_rows():
    payload = json.loads((ROOT / "configs/manifests/spatial_future_v1/windows.json").read_text(encoding="utf-8"))
    expected = {r["window_id"]: r for r in payload["windows"] if r["split"] == "validation"}
    rows = [{"window": deepcopy(r), "teacher_l1": 1., "demonstration_l1": 2.,
             "retained_indices": list(range(64)) + list(range(256, 320)),
             "normalized_actions": np.zeros((8, 7)).tolist()} for r in expected.values()]
    return payload, expected, rows


def test_validation_checks_actual_window_metadata_even_if_id_unchanged(validation_rows):
    _, expected, rows = validation_rows
    payload = {"arm": "A", "update": 0, "windows": 60, "observations": rows,
               "validation_metric": 1., "teacher_l1_p95": 1., "demonstration_l1": 2.}
    assert len(a.validate_validation(payload, expected, "A", 0)) == 60
    rows[0]["window"]["future_step"] += 1
    with pytest.raises(ValueError, match="actual registered"):
        a.validate_validation(payload, expected, "A", 0)


def test_pairs_join_on_window_id_and_report_signed_B_minus_A(validation_rows):
    _, _, rows = validation_rows
    left = {r["window"]["window_id"]: r for r in rows}
    right = {r["window"]["window_id"]: {**r, "teacher_l1": .5} for r in reversed(rows)}
    result = a.paired_windows(left, right, repeats=100, seed=1)
    assert result["teacher_l1"]["overall"]["mean"] == -.5
    assert result["teacher_l1"]["overall"]["clusters"] == 20
    assert result["teacher_l1"]["overall"]["ci95_percentile"] == [-.5, -.5]
    assert result["demonstration_l1"]["overall"]["mean"] == 0


def test_cost_replayed_completed_updates_and_hard_kill_are_all_charged(tmp_path):
    events = [{"event": "update_start", "update": 1, "job_id": "j1"},
              {"event": "update_end", "update": 1, "job_id": "j1", "seconds": 2., "forward_backward_samples": 8},
              {"event": "update_start", "update": 2, "job_id": "j1"},  # killed before a completion
              {"event": "update_start", "update": 1, "job_id": "j2"},  # replay from earlier checkpoint
              {"event": "update_end", "update": 1, "job_id": "j2", "seconds": 3., "forward_backward_samples": 8},
              {"event": "update_start", "update": 2, "job_id": "j2"},
              {"event": "update_failed", "update": 2, "job_id": "j2", "seconds": 1.}]
    result = a.analyze_cost_events(write_lines(tmp_path / "events.jsonl", events), a.Evidence())
    assert (result["attempts"], result["completed"], result["failed_explicit"], result["interrupted_unknown"]) == (4, 2, 1, 1)
    assert result["known_seconds"] == 6 and result["seconds_total"] is None
    assert result["repeated_attempts"] == 2 and result["known_forward_backward_samples"] == 16


def test_cache_completion_without_job_field_inherits_its_start(tmp_path):
    events = [{"event": "cache_start", "window_id": "w", "job_id": "1"},
              {"event": "cache_end", "window_id": "w", "seconds": 3, "teacher_forwards": 1, "vision_forwards": 3}]
    result = a.analyze_cost_events(write_lines(tmp_path / "cache.jsonl", events), a.Evidence())
    assert result["job_ids"] == ["1"] and result["seconds_total"] == 3


def test_truncated_last_event_is_preserved_and_prevents_complete_cost(tmp_path):
    path = tmp_path / "cost.jsonl"
    path.write_bytes(b'{"event":"update_start","update":1,"job_id":"1"}\n{"event":')
    before = path.read_bytes()
    result = a.analyze_cost_events(path, a.Evidence())
    assert result["partial_tail"] and result["seconds_total"] is None
    assert path.read_bytes() == before


def test_orphan_cost_completion_is_not_self_accepted(tmp_path):
    path = write_lines(tmp_path / "cost.jsonl", [{"event": "update_end", "update": 1, "seconds": 1}])
    with pytest.raises(ValueError, match="orphan"):
        a.analyze_cost_events(path, a.Evidence())


def test_slurm_failed_allocation_counts_and_steps_do_not_double_count(tmp_path):
    path = tmp_path / "sacct.txt"
    path.write_text("JobIDRaw|State|ElapsedRaw|AllocTRES|ExitCode|\n"
                    "1|COMPLETED|3600|cpu=7,gres/gpu=1|0:0|\n"
                    "1.batch|COMPLETED|3600|cpu=7,gres/gpu=1|0:0|\n"
                    "2|FAILED|1800|cpu=7,gres/gpu=1|1:0|\n", encoding="utf-8")
    result = a.analyze_slurm([path, path], a.Evidence())
    assert len(result["jobs"]) == 2 and result["allocated_gpu_hours_total"] == 1.5
    assert result["states"] == {"COMPLETED": 1, "FAILED": 1}


def test_missing_gpu_count_or_requested_job_is_not_imputed(tmp_path):
    path = write(tmp_path / "billing.json", {"jobs": [{"job_id": "1", "state": "FAILED", "elapsed_seconds": 100}]})
    result = a.analyze_slurm([path], a.Evidence(), job_ids=("1", "2"))
    assert result["allocated_gpu_hours_total"] is None and result["missing_requested_jobs"] == ["2"]


@pytest.fixture
def training_fixture(tmp_path, validation_rows):
    windows, _, rows = validation_rows
    config = json.loads((ROOT / "configs/experiments/g1_future_v1.json").read_text())
    reports = {}
    for arm in ("A", "B"):
        curves = []
        for update, metric in zip(config["selection"]["updates"], [1., .4, .4, .8, .9]):
            observations = deepcopy(rows)
            for row in observations:
                row["teacher_l1"] = metric
                if arm == "B":
                    row.update(future_mse=.5, future_zero_visual_mse=.8, future_reversed_action_mse=.6)
            payload = {"arm": arm, "update": update, "windows": 60, "observations": observations,
                       "validation_metric": metric, "teacher_l1_p95": metric, "demonstration_l1": 2., "seconds": 3.}
            if arm == "B":
                payload.update(future_mse=.5, future_zero_visual_mse=.8, future_reversed_action_mse=.6)
            write(tmp_path / arm / f"validation_{update:04d}.json", payload)
            curves.append({"update": update, "validation_metric": metric})
        reports[arm] = {"status": "completed", "arm": arm, "vla_parameters_unchanged": True,
            "window_manifest_sha256": "window-hash", "config_sha256": a.signature({**config, "arm": arm}),
            "training_updates_completed": 100, "source_files": {"synthetic_fixture": "x"}, "evaluations": curves,
            "initial_scorer_sha256": "init", "sample_order_sha256": "order", "vla_parameter_sha256": "vla",
            "best_update": 25, "best_validation_metric": .4, "best_checkpoint_sha256": arm,
            "trainable_parameters": 100, "future_head_parameters": 0 if arm == "A" else 20, "peak_memory_allocated_bytes": 300}
        write(tmp_path / arm / "training_report.json", reports[arm])
    s = write(tmp_path / "training_summary.json", {"status": "completed", "arms": reports})
    write(tmp_path / "train_finalization.json", {"status": "verified", "checkpoint_unchanged": True, "result_sha256": a.digest(s)})
    return tmp_path, windows, config, reports


def test_training_recomputes_earliest_best_curve_and_B_readout_diagnostics(training_fixture):
    directory, windows, config, _ = training_fixture
    result, _ = a.analyze_training(directory, windows, "window-hash", config, a.Evidence(), repeats=100)
    assert result["status"] == "analyzed" and result["arms"]["A"]["best_update"] == 25
    assert result["arms"]["B"]["final"]["overall"]["teacher_l1"]["mean"] == pytest.approx(.9)
    assert result["B_readout_interventions"]["future_zero_visual_mse_minus_original"]["mean"] == pytest.approx(.3)
    assert result["arms"]["B"]["validation_completed_seconds_lower_bound"] == 15


@pytest.mark.parametrize("tamper", ["different_init", "late_tie", "fake_summary", "same_id_wrong_split"])
def test_training_rejects_unmatched_or_self_inconsistent_evidence(training_fixture, tamper):
    directory, windows, config, reports = training_fixture
    if tamper in ("different_init", "late_tie"):
        reports["B"]["initial_scorer_sha256" if tamper == "different_init" else "best_update"] = "changed" if tamper == "different_init" else 50
        write(directory / "B/training_report.json", reports["B"])
    else:
        path = directory / "B/validation_0025.json"
        payload = json.loads(path.read_text())
        if tamper == "fake_summary":
            payload["validation_metric"] = 0
        else:
            payload["observations"][0]["window"]["split"] = "train"
        write(path, payload)
    with pytest.raises(ValueError):
        a.analyze_training(directory, windows, "window-hash", config, a.Evidence(), repeats=100)


def test_absent_finalization_keeps_analysis_unverified(training_fixture):
    directory, windows, config, _ = training_fixture
    (directory / "train_finalization.json").unlink()
    result, _ = a.analyze_training(directory, windows, "window-hash", config, a.Evidence(), repeats=100)
    assert result["status"] == "awaiting_finalization" and not result["finalization_verified"]


def test_producer_train_mode_receipt_name_required_and_hash_checked(training_fixture):
    directory, windows, config, _ = training_fixture
    real = directory / "train_finalization.json"
    receipt = json.loads(real.read_text())
    real.unlink()
    write(directory / "training_finalization.json", receipt)
    result, _ = a.analyze_training(directory, windows, "window-hash", config, a.Evidence(), repeats=100)
    assert not result["finalization_verified"]  # A similarly named file is not the producer's receipt.
    receipt["result_sha256"] = "wrong"
    write(real, receipt)
    with pytest.raises(ValueError, match="finalization"):
        a.analyze_training(directory, windows, "window-hash", config, a.Evidence(), repeats=100)


def test_hard_set_overlap_and_saved_action_difference_have_separate_meaning(validation_rows):
    _, _, rows = validation_rows
    left = {r["window"]["window_id"]: r for r in rows}
    right = deepcopy(left)
    first = next(iter(right.values()))
    first["retained_indices"] = [1, *range(2, 65), *range(256, 320)]
    first["normalized_actions"][0][0] = 56.
    result = a.hard_selection_comparison(left, right)
    assert result["overall"]["identical_sets"] == 59
    changed = next(r for r in result["rows"] if not r["sets_identical"])
    assert changed["intersection_over_128"] == 127 / 128
    assert changed["jaccard"] == 127 / 129
    assert changed["AB_output_l1"] == 1
    assert result["overall"]["AB_output_l1"]["mean"] == pytest.approx(1 / 60)


@pytest.fixture
def loop_fixture(tmp_path):
    from cti_vla.evaluation.future_trials import load_future_development_panel, summarize_future_trials
    state_root = ROOT / "configs/manifests/spatial_initial_states_v1"
    panel = load_future_development_panel(state_root / "init_states_development.json", state_root / "g0_development_15.json")
    config = {"panel_signature": panel["panel_signature"], "methods": ["future_A", "future_B"],
              "selectors": {arm: {"selector_checkpoint_sha256": arm} for arm in ("A", "B")}}
    events = []
    for i, state in enumerate(panel["states"]):
        for arm in ("A", "B"):
            identity = {"trial_id": state["trial_id"] + ":future_" + arm, "state_trial_id": state["trial_id"],
                "method": "future_" + arm, "task_id": state["task_id"], "task_name": state["task_name"], "split": "development",
                "initial_state_sha256": state["initial_state_sha256"], "source_state_index": state["source_state_index"],
                "environment_seed": panel["environment_seed"], "run_signature": a.signature(config)}
            success = i % 4 in ((0, 2) if arm == "A" else (1, 2))
            events.extend([{**identity, "event": "start"}, {**identity, "event": "result", "status": "completed", "success": success}])
    p = write_lines(tmp_path / "trials.jsonl", events)
    complete = {r["trial_id"]: r for r in events if r["event"] == "result"}
    ledger = SimpleNamespace(events=events, completed=lambda: complete, path=p)
    summary = summarize_future_trials(panel, config["methods"], ledger, provenance=config, checkpoint_unchanged=True)
    for name, value in (("panel.json", panel), ("config.json", config), ("closed_loop_report.json", summary)):
        write(tmp_path / name, value)
    return tmp_path, events, summary


def test_closed_loop_recomputes_all_four_sameinit_cells(loop_fixture):
    path, _, _ = loop_fixture
    result = a.analyze_closed_loop(path, {arm: {"best_checkpoint_sha256": arm} for arm in ("A", "B")}, a.Evidence(), repeats=100)
    assert result["paired_counts"] == {"A_only": 8, "B_only": 8, "both": 7, "neither": 7}
    assert result["paired_B_minus_A"]["mean"] == 0
    assert result["paired_B_minus_A"]["clusters"] == 30


def test_resigned_loop_summary_does_not_hide_wrong_initial_state(loop_fixture):
    path, events, summary = loop_fixture
    events[1]["initial_state_sha256"] = "bad"
    write_lines(path / "trials.jsonl", events)
    summary["trials_jsonl_sha256"] = a.digest(path / "trials.jsonl")
    write(path / "closed_loop_report.json", summary)
    with pytest.raises(ValueError, match="paired state/method identity"):
        a.analyze_closed_loop(path, {}, a.Evidence(), repeats=100)


def test_missing_outputs_are_pending_and_analysis_never_writes_gate(tmp_path):
    args = SimpleNamespace(protocol=ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json",
        windows=ROOT / "configs/manifests/spatial_future_v1/windows.json", config=ROOT / "configs/experiments/g1_future_v1.json",
        training_directory=None, closed_loop_directory=None, latency_directory=None, cost_events=[], slurm_accounting=[], job_id=[],
        bootstrap_repeats=100, bootstrap_seed=1, project_root=tmp_path, output_directory=tmp_path / "analysis")
    result = a.run(args)
    assert all(result[k]["status"] == "pending" for k in ("offline", "closed_loop", "latency"))
    assert result["scientific_decision"] == "manual_review_required"
    assert not result["test_authorized"] and not result["expanded_seed_authorized"]
    assert {p.name for p in args.output_directory.iterdir()} == {"summary.json", "报告.md"}


def test_input_modification_during_analysis_is_rejected(tmp_path):
    path = write(tmp_path / "evidence.json", {"x": 1})
    reader = a.Evidence()
    reader.read(path)
    write(path, {"x": 2})
    with pytest.raises(ValueError, match="changed"):
        reader.unchanged()


@pytest.fixture
def latency_fixture(tmp_path):
    """Complete fixed-schema fake timing, only in pytest scratch; never a GPU result."""
    from dataclasses import asdict
    from cti_vla.evaluation.profiling import (ProfileConfig, PROFILING_VERSION, PHASES, read_profile_cost,
                                            summarize_latencies)
    config = asdict(ProfileConfig())
    config["instruction_modes"] = list(config["instruction_modes"])
    provenance = {"unit_test_fixture_only": True, "stage": "G1-F_development_latency", "test_opened": False,
                  "config": config, "panel": {"split": "development", "version": "g1f-development-dense-control-0-80-160-v1"}}
    methods = {"dense": {}, "future_A": {"provenance": {"selector_checkpoint_sha256": "A"}},
               "future_B": {"provenance": {"selector_checkpoint_sha256": "B"}}}
    events = [{"event": "identity", "identity": provenance, "identity_sha256": a.signature(provenance)}]
    rows, call_id = [], 0
    for method in methods:
        for kind, repeats, modes, observations in (("warmup", 50, ["cold"], [0]),
                ("main", 5, ["cold", "hot"], [0, 1]), ("components", 1, ["cold", "hot"], [0, 1])):
            for repeat in range(repeats):
                for mode in modes:
                    for obs in observations:
                        meta = {"call_id": call_id, "method": method, "instruction_mode": mode, "kind": kind,
                                "round": repeat, "observation_id": str(obs), "episode_id": "ep" + str(obs)}
                        events.append({"event": "start", **meta})
                        row = {**meta, "elapsed_ms": 10 if method == "dense" else 5,
                               "memory_bytes": {"peak_allocated": 10, "peak_reserved": 20}}
                        if kind == "components":
                            row["components"] = {p: {"host_ms": 1., "cuda_stream_elapsed_ms": 1.} for p in PHASES}
                        events.append({"event": "complete", **row})
                        if kind != "warmup":
                            rows.append(row)
                        call_id += 1
    journal = write_lines(tmp_path / "calls.jsonl", events)
    measured = {"profiling_version": PROFILING_VERSION, "status": "completed_measurement", "synthetic": False,
        "checkpoint_unchanged": True, "config": config, "methods": methods, "observations": 2,
        "observation_episodes": {"0": "ep0", "1": "ep1"}, "provenance": provenance,
        "cost": read_profile_cost(journal), "rows": rows}
    mp = write(tmp_path / "measurements.json", measured)
    summary = summarize_latencies(measured, bootstrap_repeats=100)
    summary.update(measurements_sha256=a.digest(mp), journal_sha256=a.digest(journal), checkpoint_unchanged=True)
    write(tmp_path / "summary.json", summary)
    return tmp_path, measured, summary


def test_profiler_schema_is_recomputed_from_all_complete_calls(latency_fixture):
    path, _, _ = latency_fixture
    result = a.analyze_latency(path, {arm: {"best_checkpoint_sha256": arm} for arm in ("A", "B")}, a.Evidence())
    assert result["unit"] == "ms/action_chunk8"
    assert {r["speedup_ratio_of_paired_means"] for r in result["paired_dense_comparisons"]} == {2.}
    assert result["cost"]["completed"] == 222


def test_profile_metadata_cannot_be_replaced_after_journal_measurement(latency_fixture):
    path, measured, summary = latency_fixture
    measured["provenance"]["stage"] = "another-run"
    write(path / "measurements.json", measured)
    summary["measurements_sha256"] = a.digest(path / "measurements.json")
    write(path / "summary.json", summary)
    with pytest.raises(ValueError, match="journal identity"):
        a.analyze_latency(path, {}, a.Evidence())

"""CPU evidence-reuse and complete-state-vector resampling regressions."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from cti_vla.data.long_initial_states import load_long_development_panel
from cti_vla.evaluation.future_dense_reuse import load_dense_reference, require_dense_compatibility, validate_dense_reference
from cti_vla.evaluation.future_multiseed import state_vector_interval, summarize_seed_vectors
from cti_vla.evaluation import future_trials, libero_runtime
from cti_vla.evaluation.teacher_diagnostics import json_signature
from test_future_runtime import good_policy
from test_selector_runtime import Env

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "configs/manifests/long_initial_states_v1/development_panel_30.json"
PARENT = ROOT / "results/g1_future_long_v1/closed_loop"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def script(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.fixture(scope="module")
def reference():
    panel = load_long_development_panel(PANEL)
    return panel, load_dense_reference(PARENT, panel)


def test_actual_parent_reference_is_30_trials_not_90_dense(reference):
    panel, receipt = reference
    require_dense_compatibility(receipt, panel, read(PARENT / "config.json"))
    assert len(receipt["dense_results"]) == 30
    assert sum(r["success"] for r in receipt["dense_results"]) == 29
    assert receipt["new_inferences"] == receipt["new_gpu_seconds"] == 0


@pytest.mark.parametrize("field", ["base_model_revision", "stats_key", "input_version", "action_version",
    "packing_version", "environment_seed", "runtime_seed", "max_steps", "wait_steps", "action_chunk", "panel_signature"])
def test_reuse_refuses_changed_policy_environment_protocol(reference, field):
    panel, receipt = reference
    config = read(PARENT / "config.json")
    config[field] = 99 if isinstance(config[field], int) else "changed"
    with pytest.raises(ValueError):
        require_dense_compatibility(receipt, panel, config)


def test_reuse_refuses_source_runtime_or_resigned_outcome(reference):
    panel, receipt = reference
    config = read(PARENT / "config.json")
    config["runtime"]["packages"]["mujoco"] = "different"
    with pytest.raises(ValueError):
        require_dense_compatibility(receipt, panel, config)
    config = read(PARENT / "config.json")
    config["source_hashes"]["src/cti_vla/evaluation/libero_runtime.py"] = "0" * 64
    with pytest.raises(ValueError):
        require_dense_compatibility(receipt, panel, config)
    altered = deepcopy(receipt)
    altered["dense_results"][0]["success"] = not altered["dense_results"][0]["success"]
    altered["signature"] = json_signature({k: v for k, v in altered.items() if k != "signature"})
    with pytest.raises(ValueError):
        validate_dense_reference(altered, panel)


@pytest.mark.parametrize("field", ["cuda", "gpu"])
def test_dense_reuse_requires_same_cuda_and_gpu_type(reference, field):
    panel, receipt = reference
    config = read(PARENT / "config.json")
    config["runtime"][field] = "changed"
    with pytest.raises(ValueError):
        require_dense_compatibility(receipt, panel, config)


def test_new_AB_only_60_trials_resume_without_dense_policy_or_cost(reference, tmp_path):
    panel, receipt = reference
    policies = {"future_A": good_policy, "future_B": good_policy}
    ledger = libero_runtime.TrialLedger(tmp_path / "trials.jsonl", run_signature="synthetic-seed23")
    made = []
    def create(state):
        made.append(state["trial_id"])
        return Env(), "same"
    future_trials.evaluate_future_trials(panel, policies, ledger, create, reseed=lambda: None,
        stop_after=2, dense_reference=receipt)
    assert made[0] == made[1]
    assert future_trials.evaluate_future_trials(panel, policies, ledger, create, reseed=lambda: None, dense_reference=receipt) == 58
    result = future_trials.summarize_future_trials(panel, policies, ledger, provenance={}, checkpoint_unchanged=True, dense_reference=receipt)
    assert result["status"] == "completed" and result["expected_trials"] == result["completed_trials"] == 60
    assert result["reused_dense_trials"] == 30 and set(result["methods"]) == set(policies)
    assert result["cost"]["recorded_result_attempts"] == 60 and result["cost"]["known_policy_calls"] == 120
    with pytest.raises(ValueError):
        future_trials.evaluate_future_trials(panel, policies, ledger, create, reseed=lambda: None)


def test_prepare_new_seed_requires_dense_reference_and_eval_seed17(reference):
    cli = script("multiseed_eval_test", "scripts/eval_future_selector_libero.py")
    args = SimpleNamespace(suite="libero_10", panel=PANEL, config=ROOT / "configs/experiments/g1_future_long_seed23_v1.json",
        prepare_only=True, controls=None, dense_reference=PARENT, seed=17)
    result = cli.run(args)
    assert result["expected_trials"] == 60 and result["training_seed"] == 23 and result["evaluation_runtime_seed"] == 17
    assert result["gpu_calls"] == 0 and not result["f01_accepted"]
    args.seed = 23
    with pytest.raises(ValueError, match="evaluation seed17"):
        cli.run(args)


def test_AB_only_analyzer_replays_60_new_trials_and_keeps_dense_reference_separate(reference, tmp_path):
    panel, receipt = reference
    config = read(PARENT / "config.json")
    config.update(methods=["future_A", "future_B"], training_seed=23, dense_reference=receipt)
    for selector in config["selectors"].values():
        selector["seed"] = 23
    ledger = libero_runtime.TrialLedger(tmp_path / "trials.jsonl", run_signature=json_signature(config))
    for state in panel["states"]:
        for method in config["methods"]:
            identity = future_trials._identity(panel, state, method)
            ledger.append({**identity, "event": "start"})
            ledger.append({**identity, "event": "result", "status": "completed", "success": method == "future_B"})
    summary = future_trials.summarize_future_trials(panel, config["methods"], ledger,
        provenance=config, checkpoint_unchanged=True, dense_reference=receipt)
    for name, value in (("config.json", config), ("panel.json", panel), ("closed_loop_report.json", summary)):
        (tmp_path / name).write_text(json.dumps(value), encoding="utf-8")
    analyzer = script("multiseed_single_analysis_test", "scripts/analyze_g1_future.py")
    result = analyzer.analyze_closed_loop(tmp_path, {}, analyzer.Evidence(), suite="libero_10", panel_path=PANEL)
    assert result["status"] == "analyzed" and result["paired_counts"]["B_only"] == 30
    assert set(result["methods"]) == {"future_A", "future_B"}
    assert result["dense_reference"]["trials"] == 30 and result["dense_reference"]["new_inferences"] == 0
    assert result["paired_vs_dense"]["A"]["selector_minus_dense"]["mean"] == -29 / 30
    assert result["cost"]["recorded_result_attempts"] == 60


def test_bootstrap_preserves_opposite_seed_values_within_every_state():
    rows = [{"state_trial_id": f"{t}:{i}", "task_id": t, "seed_vector": [i % 2, -(i % 2), 0]}
            for t in (0, 3, 5) for i in range(10)]
    result = state_vector_interval(rows)
    # Resampling seed/state cells independently would create spurious uncertainty.
    assert result["mean"] == 0 and result["ci95_percentile"] == [0, 0]
    assert result["unique_initial_states"] == 30 and result["paired_seed_state_cells"] == 90
    assert result["training_seed_mean_sample_sd"] == .5
    assert result["training_seed_mean_range"] == [-.5, .5]


def test_identical_seed_vectors_have_single_state_interval_not_tripled_n():
    rows = [{"state_trial_id": f"{t}:{i}", "task_id": t, "seed_vector": [i % 2] * 3}
            for t in (0, 3, 5) for i in range(10)]
    result = state_vector_interval(rows)
    rng = np.random.default_rng(1517)
    draws = sum(np.asarray([i % 2 for i in range(10)])[rng.integers(0, 10, (2000, 10))].sum(axis=1) for _ in range(3)) / 30
    assert result["ci95_percentile"] == np.quantile(draws, [.025, .975]).tolist()


def test_three_seed_summary_keeps_all_seeds_and_dense_unique(reference):
    panel, receipt = reference
    base = {"pairs": [{"state_trial_id": s["trial_id"], "task_id": s["task_id"], "A_success": True, "B_success": True}
        for s in panel["states"]], "methods": {}, "paired_counts": {}, "paired_B_minus_A": {}, "paired_vs_dense": {}}
    reports = {seed: deepcopy(base) for seed in (17, 23, 41)}
    reports[41]["pairs"][0]["B_success"] = False
    result = summarize_seed_vectors(panel, reports, receipt)
    assert len(result["all_paired_results"]) == 90 and len(result["state_vectors"]) == 30
    assert result["dense_reference"]["unique_trials"] == 30 and result["dense_reference"]["successes"] == 29
    assert result["contrasts"]["B_minus_A"]["mean"] == pytest.approx(-1 / 90)
    assert result["contrasts"]["B_minus_A"]["training_seed_mean_range"] == [-1 / 30, 0]
    del reports[41]
    with pytest.raises(ValueError, match="all17/23/41"):
        summarize_seed_vectors(panel, reports, receipt)

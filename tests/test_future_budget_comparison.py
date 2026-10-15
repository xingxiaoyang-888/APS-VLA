"""CPU matched-budget, paired-state and no-retrofitted-checkpoint regressions."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from cti_vla.data.long_initial_states import load_long_development_panel
from cti_vla.evaluation.future_budget_comparison import summarize_budget_comparison
from cti_vla.evaluation.future_dense_reuse import load_dense_reference

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "configs/manifests/long_initial_states_v1/development_panel_30.json"
DENSE = ROOT / "results/g1_future_long_v1/closed_loop"


def script(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def fixture():
    panel = load_long_development_panel(PANEL)
    reference = load_dense_reference(DENSE, panel)
    reports = {budget: {seed: {"pairs": [{"state_trial_id": state["trial_id"], "task_id": state["task_id"],
        "A_success": True, "B_success": True} for state in panel["states"]]} for seed in (17, 23, 41)} for budget in (64, 128)}
    return panel, reference, reports


def test_cross_budget_state_vectors_preserve_matched_seed_dependence():
    panel, reference, reports = fixture()
    for index, state in enumerate(panel["states"]):
        reports[64][17]["pairs"][index]["B_success"] = index % 2 == 0
        reports[128][17]["pairs"][index]["A_success"] = index % 2 != 0
        reports[64][23]["pairs"][index]["B_success"] = index % 2 != 0
        reports[128][23]["pairs"][index]["A_success"] = index % 2 == 0
    result = summarize_budget_comparison(panel, reports, reference)
    cross = result["contrasts"]["B64_minus_A128"]
    assert cross["mean"] == 0 and cross["ci95_percentile"] == [0, 0]
    assert result["unique_initial_states"] == 30 and result["new64_AB_trials"] == 180
    assert result["dense"]["unique_trials"] == 30 and result["dense"]["successes"] == 29
    assert cross["per_seed"]["17"]["paired_counts"]["left_only"] == 15
    assert result["methods"]["B64"]["per_seed"]["41"]["successes"] == 30


@pytest.mark.parametrize("change", ["seed", "budget", "state", "task", "bool"])
def test_budget_comparison_refuses_dropped_or_mispaired_results(change):
    panel, reference, reports = fixture()
    if change == "seed":
        del reports[64][23]
    elif change == "budget":
        del reports[128]
    elif change == "state":
        reports[64][17]["pairs"].pop()
    elif change == "task":
        reports[64][17]["pairs"][0]["task_id"] = 9
    else:
        reports[64][17]["pairs"][0]["A_success"] = 1
    with pytest.raises(ValueError):
        summarize_budget_comparison(panel, reports, reference)


@pytest.mark.parametrize("seed", [17, 23, 41])
def test_new64_preparation_requires_budget_contract_and_reuses_only_dense(seed):
    cli = script("budget64_eval_prepare", "scripts/eval_future_selector_libero.py")
    args = SimpleNamespace(suite="libero_10", panel=PANEL,
        config=ROOT / f"configs/experiments/g1_future_long_k64_seed{seed}_v1.json",
        prepare_only=True, controls=None, dense_reference=DENSE, seed=17,
        budget_reuse_registration=ROOT / "nonexecuted_registration_placeholder.json")
    result = cli.run(args)
    assert result["expected_trials"] == 60 and result["training_seed"] == seed
    assert result["visual_tokens"] == 64 and result["per_camera_budgets"] == [32, 32]
    assert result["gpu_calls"] == 0 and not result["f01_accepted"]
    args.budget_reuse_registration = None
    with pytest.raises(ValueError, match="explicit budget"):
        cli.run(args)


def test_overlap_uses_trained64_denominator_and_rejects128_saved_sets():
    cli = script("budget64_offline_analysis", "scripts/analyze_g1_future.py")
    a = {"w": {"window": {"window_id": "w", "task_name": "t", "phase": "early"},
        "retained_indices": [*range(32), *range(256, 288)], "normalized_actions": [[0.] * 7] * 8}}
    b = deepcopy(a)
    b["w"]["retained_indices"] = [*range(1, 33), *range(256, 288)]
    result = cli.hard_selection_comparison(a, b, tokens_per_camera=32)
    assert result["overall"]["intersection_over_64"]["mean"] == 63 / 64
    assert "intersection_over_128" not in result["overall"]
    with pytest.raises(ValueError, match="trained token budget"):
        cli.hard_selection_comparison(a, b)


@pytest.mark.parametrize("lower,bmedian,bp95,expected", [(.01, 6, 8, True), (0, 6, 8, False),
    (-.01, 6, 8, False), (.01, 11, 8, False), (.01, 6, 13, False)])
def test_tradeoff_rule_requires_paired_success_and_both_measured_latencies(lower, bmedian, bp95, expected):
    cli = script("budget_tradeoff_tests", "scripts/analyze_g1_future_budgets.py")
    closed = {"contrasts": {name: {"mean": .03, "ci95_percentile": [lower, .07]}
        for name in ("B64_minus_A64", "B128_minus_A128", "B64_minus_A128")}}
    latency = {"seed_equal_weight_summaries": [{"method_family": method,
        "mean_of_seed_medians_ms": bmedian if method == "B64" else 10,
        "mean_of_seed_p95_ms": bp95 if method == "B64" else 12}
        for method in ("A128", "B128", "A64", "B64")]}
    result = cli.tradeoff_diagnostics(closed, latency)
    assert result["strict_B64_over_A128"] is expected
    assert result["C_execution_authorized"] is False
    assert cli.tradeoff_diagnostics(closed, {})["strict_B64_over_A128"] is None

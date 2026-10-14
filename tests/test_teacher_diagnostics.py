"""Independent, CPU-only G1 intervention, accounting and restart oracles."""

import json
import importlib.util
from pathlib import Path
from argparse import Namespace
from dataclasses import dataclass

import pytest
import torch

from cti_vla.evaluation.teacher_diagnostics import (
    ActionQueryCache, compare_labels, require_g0, run_exact_selection,
    run_intervention_panel, run_repeatability,
)
from cti_vla.labeling.sampling import DiagnosticSet, camera_balanced_set, fixed_anchor_panel


def _forward(visual, indices):
    selected = visual[:, indices[0]]
    value = selected.sum() + selected.square().sum() * .07
    return value.expand(1, 8, 7)


def test_fixed_anchors_balanced_original_order_and_rng_independence():
    panel = fixed_anchor_panel("sample", seed=117)
    assert [len(p.retained_indices) for p in panel] == [512, 256, 256, 128, 128]
    for row in panel:
        assert row.candidate_indices == panel[0].candidate_indices
        assert len(row.candidate_indices) == 16
        assert set(row.candidate_indices) <= set(row.retained_indices)
        assert row.retained_indices == tuple(sorted(set(row.retained_indices)))
        assert sum(i < 256 for i in row.retained_indices) == len(row.retained_indices) // 2
    torch.manual_seed(987)
    assert fixed_anchor_panel("sample", seed=117) == panel
    assert fixed_anchor_panel("other", seed=117)[0].candidate_indices != panel[0].candidate_indices


def test_uniform_is_two_dimensional_centered_grid():
    result = camera_balanced_set(per_camera=64, mode="uniform")
    expected = tuple(r * 16 + c for r in range(1, 16, 2) for c in range(1, 16, 2))
    assert result == expected + tuple(i + 256 for i in expected)


def test_signed_deletion_and_replacement_match_hand_computation():
    visual = torch.tensor([[[1.], [-2.], [4.], [-1.]]])
    seen = []
    def linear(source, indices):
        seen.append((source.clone(), indices.clone()))
        return source[:, indices[0]].sum().expand(1, 8, 7)
    oracle = ActionQueryCache(visual, linear, identity={"sample": "hand"})
    record = DiagnosticSet("partial", (0, 1, 2), (0, 1))
    report = run_intervention_panel(oracle, (record,))
    row = report["sets"][0]
    # Full sum=2, partial=3, base E=1. Delete token0 =>2/E0/y-1;
    # delete token1 =>5/E3/y+2. Full camera0 mean=-0.5.
    assert row["deletion_labels"] == pytest.approx([-1., 2.])
    assert row["replacement_labels"] == pytest.approx([-.5, 1.5])
    replacements = [pair for pair in seen if pair[1].shape[1] == 3 and not torch.equal(pair[0], visual)]
    assert len(replacements) == 2
    for index, (source, indices) in zip((0, 1), replacements):
        assert indices.tolist() == [[0, 1, 2]]
        assert source[0, index, 0] == -.5
        other = [i for i in range(4) if i != index]
        assert torch.equal(source[:, other], visual[:, other])
    assert torch.equal(oracle.visual, visual)


def test_panel_exact_plan_query_count_and_lengths():
    visual = torch.linspace(-1, 1, 512).reshape(1, 512, 1)
    oracle = ActionQueryCache(visual, _forward, identity={"sample": 1})
    run_intervention_panel(oracle, fixed_anchor_panel(1))
    ledger = oracle.ledger()
    assert ledger["sample_forwards_completed"] == 165
    assert ledger["api_calls_attempted"] == 165
    assert ledger["attempts_by_category"] == {"full_reference": 1, "panel_deletion": 80, "panel_replacement": 80, "panel_base": 4}
    assert set(ledger["by_visual_length"]) == {"512", "511", "256", "255", "128", "127"}


def test_exact_teacher_path_has_900_calls_and_complete_comparators():
    visual = torch.linspace(-1, 1, 512).reshape(1, 512, 1)
    oracle = ActionQueryCache(visual, _forward, identity={"sample": 2}, max_sample_forwards=914)
    report = run_exact_selection(oracle, sample_id=2)
    counts = oracle.ledger()["attempts_by_category"]
    assert counts["full_reference"] + counts["teacher_all_candidates"] + counts["teacher_stage_evaluation"] == 900
    assert oracle.ledger()["sample_forwards_completed"] <= 914
    assert len(report["methods"]) == 6
    for name, rows in report["methods"].items():
        assert [r["keep_count"] for r in rows] == [256, 128, 64]
        for row in rows:
            assert sum(i < 256 for i in row["retained_indices"]) == row["keep_count"] // 2
    assert report["methods"]["teacher_staged"][0] == report["methods"]["full_loo_static"][0]
    assert sum(len(s["candidate_indices"]) for s in report["stage_labels"]) == 512 + 256 + 128


def test_durable_resume_reuses_completed_actions_and_rejects_identity(tmp_path):
    journal = tmp_path / "queries.jsonl"
    visual = torch.arange(8.).reshape(1, 8, 1)
    oracle = ActionQueryCache(visual, _forward, identity={"input_sha": "a"}, journal_path=journal)
    expected = oracle.query((0, 2, 4, 6), category="first")
    resumed = ActionQueryCache(visual, lambda *_: pytest.fail("cache recomputed"), identity={"input_sha": "a"}, journal_path=journal)
    assert torch.equal(resumed.query((0, 2, 4, 6), category="reuse"), expected)
    assert resumed.ledger()["sample_forwards_completed"] == 1
    assert resumed.ledger()["cache_hits"] == 1
    with pytest.raises(ValueError, match="identity"):
        ActionQueryCache(visual, _forward, identity={"input_sha": "b"}, journal_path=journal)
    events = [json.loads(line) for line in journal.read_text().splitlines()]
    events[2]["action"][0][0][0] += 1
    journal.write_text("\n".join(json.dumps(event) for event in events) + "\n")
    with pytest.raises(ValueError, match="checksum"):
        ActionQueryCache(visual, _forward, identity={"input_sha": "a"}, journal_path=journal)


def test_failed_calls_are_charged_and_budget_is_not_reset_on_resume(tmp_path):
    visual = torch.arange(8.).reshape(1, 8, 1)
    journal = tmp_path / "queries.jsonl"
    def fail(*_):
        raise RuntimeError("fake policy failure")
    oracle = ActionQueryCache(visual, fail, identity={}, journal_path=journal, max_sample_forwards=2)
    with pytest.raises(RuntimeError, match="fake policy"):
        oracle.query((0, 4), category="failure")
    resumed = ActionQueryCache(visual, _forward, identity={}, journal_path=journal, max_sample_forwards=2)
    resumed.query((0, 4), category="retry")
    assert resumed.ledger()["sample_forwards_attempted"] == 2
    assert resumed.ledger()["failed_calls"] == 1
    with pytest.raises(RuntimeError, match="budget"):
        resumed.query((1, 5), category="over_budget")


def test_repeatability_adds_exactly_two_actual_calls_once(tmp_path):
    visual = torch.arange(8.).reshape(1, 8, 1)
    journal = tmp_path / "queries.jsonl"
    oracle = ActionQueryCache(visual, _forward, identity={}, journal_path=journal)
    oracle.query(tuple(range(8)), category="ref")
    oracle.query(tuple(range(1, 8)), category="initial")
    assert run_repeatability(oracle, 0)["label_absolute_difference"] == 0
    assert oracle.ledger()["sample_forwards_completed"] == 4
    resumed = ActionQueryCache(visual, _forward, identity={}, journal_path=journal)
    run_repeatability(resumed, 0)
    assert resumed.ledger()["sample_forwards_completed"] == 4


def test_g0_gate_rejects_smoke_and_insufficient_trials():
    passed = {"stage": "G0", "status": "passed", "dense_parity": {"passed": True},
              "closed_loop": {"passed": True, "num_tasks": 3, "episodes_per_task": 5},
              "initial_state_split": {"passed": True},
              "provenance": {"model_revision": "r", "input_version": "i", "packing_version": "p"}}
    require_g0(passed, model_revision="r", input_version="i", packing_version="p")
    with pytest.raises(ValueError):
        require_g0(dict(passed, stage="smoke"), model_revision="r", input_version="i", packing_version="p")
    with pytest.raises(ValueError):
        require_g0(passed, model_revision="r", input_version="processor-only", packing_version="p")
    passed["closed_loop"]["episodes_per_task"] = 4
    with pytest.raises(ValueError):
        require_g0(passed, model_revision="r", input_version="i", packing_version="p")


def test_rank_ties_and_near_zero_do_not_fabricate_sign_flips():
    result = compare_labels([0., 0., 2., 3.], [-1e-7, 1e-7, 4., 6.], noise_tolerance=1e-6)
    assert result["sign_comparison_count"] == 2
    assert result["sign_flips_outside_noise"] == 0
    assert compare_labels([1., 1.], [2., 3.], noise_tolerance=0)["spearman"] is None


def test_cli_consumes_frozen_protocol_panels_and_selects_ten_repeats():
    from cti_vla.data.experiment_protocol import load_experiment_protocol
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("run_teacher_diagnostics", root / "scripts/run_teacher_diagnostics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    protocol = load_experiment_protocol(root / "configs/manifests/spatial_g0g1_v1/protocol.json")
    panel = module.build_observation_panel(protocol, repeat_seed=617)
    assert panel["diagnostic_selection_seed"] == 117
    assert panel["teacher_selection_seed"] == 217
    assert len(panel["observations"]) == 90
    exact = [row for row in panel["observations"] if row["exact_selection"]]
    repeat = [row for row in panel["observations"] if row["repeatability"]]
    assert len(exact) == 12 and len({r["task_name"] for r in exact}) == 4
    assert len(repeat) == len({r["task_name"] for r in repeat}) == 10
    for row in panel["observations"]:
        protocol.require_sample(row["episode_id"], row["step_index"], split="train")


def test_real_callback_never_receives_gradients_or_modifies_features():
    visual = torch.arange(8., requires_grad=True).reshape(1, 8, 1)
    seen = []
    def callback(source, indices):
        seen.append(torch.is_grad_enabled())
        return _forward(source, indices)
    oracle = ActionQueryCache(visual, callback, identity={})
    action = oracle.query((0, 4), category="replace", replace_index=0)
    assert seen == [False]
    assert not action.requires_grad
    assert torch.equal(visual.detach(), torch.arange(8.).reshape(1, 8, 1))


def test_cli_rejects_missing_g0_before_loading_or_querying_cuda(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("teacher_cli_gate", root / "scripts/run_teacher_diagnostics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = tmp_path / "g0.json"
    report.write_text(json.dumps({"status": "passed", "stage": "engineering_smoke"}))
    monkeypatch.setattr(torch.cuda, "device_count", lambda: pytest.fail("G0 guard reached CUDA"))
    args = Namespace(protocol=root / "configs/manifests/spatial_g0g1_v1/protocol.json",
                     asset_manifest=root / "configs/assets/openvla_oft_libero_spatial.json",
                     repeat_seed=617, output=tmp_path / "out", prepare_only=False,
                     checkpoint=tmp_path / "nonexistent-model", cache_directory=tmp_path / "hf",
                     data_directory=tmp_path / "rlds", g0_report=report)
    with pytest.raises(ValueError, match="passed G0"):
        module.run(args)
    assert not (args.output / "queries").exists()


def _cli_module():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("teacher_cli_recovery", root / "scripts/run_teacher_diagnostics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hard_kill_journal_cost_is_counted_without_observation_result(tmp_path):
    module = _cli_module()
    row = {"sample_id": 7}
    calls = 0
    def interrupted(source, indices):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise KeyboardInterrupt("simulate process interruption outside Exception handler")
        return _forward(source, indices)
    oracle = ActionQueryCache(torch.arange(8.).reshape(1, 8, 1), interrupted,
                              identity={"config_sha256": "config", "sample": row},
                              journal_path=tmp_path / "queries/7.jsonl")
    oracle.query(tuple(range(8)), category="complete")
    with pytest.raises(KeyboardInterrupt):
        oracle.query(tuple(range(7)), category="interrupted")
    summary = module._summary(tmp_path, "config", [row])
    assert summary["completed_observations"] == 0
    assert summary["cost"]["sample_forwards_attempted"] == 2
    assert summary["cost"]["sample_forwards_completed"] == 1
    assert summary["cost"]["interrupted_calls_unknown_completion"] == 1
    assert summary["cost"]["policy_seconds_total"] is None


def test_observation_completion_waits_for_checkpoint_finalization_receipt(tmp_path):
    from cti_vla.evaluation.teacher_diagnostics import atomic_json
    module = _cli_module()
    row = {"sample_id": 7}
    path = tmp_path / "observations/7.json"
    atomic_json(path, {"status": "completed", "config_sha256": "config", "observation": row})
    with pytest.raises(ValueError, match="missing.*journal"):
        module._summary(tmp_path, "config", [row])
    oracle = ActionQueryCache(torch.arange(8.).reshape(1, 8, 1), _forward,
                              identity={"config_sha256": "config", "sample": row},
                              journal_path=tmp_path / "queries/7.jsonl")
    oracle.query(tuple(range(8)), category="full")
    assert module._summary(tmp_path, "config", [row])["status"] == "awaiting_final_verification"
    @dataclass
    class VerifiedCheckpoint:
        passed: bool = True
    module._finalize(tmp_path, "config", [row], VerifiedCheckpoint())
    assert module._summary(tmp_path, "config", [row])["status"] == "completed"
    atomic_json(path, {"status": "failed", "config_sha256": "config", "observation": row})
    with pytest.raises(ValueError, match="finalization"):
        module._summary(tmp_path, "config", [row])

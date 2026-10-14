"""CPU synthetic contract tests only. No research weights or GPU results."""
from contextlib import contextmanager
from copy import deepcopy
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation import libero_runtime
from cti_vla.evaluation.future_runtime import (
    FutureRolloutPolicy, make_future_checkpoint_metadata, make_future_deployment_receipt,
    load_future_selector_checkpoint, require_future_f01, validate_future_pair,
)
from cti_vla.evaluation.future_trials import (
    evaluate_future_trials, load_future_development_panel, summarize_future_trials,
)
from cti_vla.evaluation.teacher_diagnostics import json_signature
from cti_vla.models.abstraction.packing import PACKING_VERSION
from cti_vla.selection import ConditionalInfluenceEstimator

# Reuse existing frozen-policy synthetic fixtures; no test copies a real model.
from test_selector_runtime import VLA, Head, Env, STATS_KEY

ROOT = Path(__file__).resolve().parents[1]


def checkpoint_fixture(tmp_path, arm="A", best_update=25):
    dimensions = dict(token_dim=4, language_dim=4, proprio_dim=8, hidden_dim=8,
                      num_cameras=2, patches_per_camera=256, max_instruction_tokens=128)
    common = {"seed": 17, "training": {"updates": 100}, "scorer_dimensions": dimensions,
        "model_revision": "synthetic-base", "stats_key": STATS_KEY,
        "selection": {"metric": "hard_validation_teacher_l1", "updates": [0, 25, 50, 75, 100]}}
    config = {**common, "arm": arm}
    sources = {"src/cti_vla/training/future_auxiliary.py": "a" * 64}
    metadata = make_future_checkpoint_metadata(arm=arm, seed=17, scorer_dimensions=dimensions,
        training_config=config, pair_config=common, window_manifest_sha256="b" * 64,
        model_revision="synthetic-base", stats_key=STATS_KEY, training_source_files=sources,
        update=best_update, validation_metric=.1, training_complete=False)
    estimator = ConditionalInfluenceEstimator(4, 4, 8, hidden_dim=8)
    saved = {**metadata, "estimator_state_dict": estimator.state_dict()}
    if arm == "B":
        saved["future_head_state_dict"] = {"unused": torch.ones(2)}
    path = tmp_path / f"synthetic_{arm}.pt"
    torch.save(saved, path)
    evaluations = [{"update": i, "validation_metric": .1 if i >= best_update else .2}
                   for i in common["selection"]["updates"]]
    receipt = make_future_deployment_receipt(path, metadata, training_config=config, pair_config=common,
        f01_report_sha256="c" * 64, planned_updates=100, completed_updates=100, evaluations=evaluations)
    expected = {"model_revision": "synthetic-base", "input_version": libero_runtime.INPUTS_VERSION,
        "packing_version": PACKING_VERSION, "stats_key": STATS_KEY,
        "window_manifest_sha256": "b" * 64, "f01_report_sha256": "c" * 64}
    return path, saved, receipt, expected, sources


def load_fixture(tmp_path, arm="A", best_update=25):
    path, saved, receipt, expected, sources = checkpoint_fixture(tmp_path, arm, best_update)
    loaded = load_future_selector_checkpoint(path, receipt, expected_versions=expected, expected_source_hashes=sources)
    return loaded, (path, saved, receipt, expected, sources)


@pytest.mark.parametrize("arm,best", [("A", 0), ("A", 25), ("B", 25)])
def test_completed_receipt_accepts_earlier_best_and_never_deploys_future_head(tmp_path, arm, best):
    loaded, _ = load_fixture(tmp_path, arm, best)
    assert loaded.provenance["update"] == best
    assert loaded.provenance["training_complete"] is False
    assert loaded.provenance["future_head_deployed"] is False
    assert not hasattr(loaded, "future_head")
    assert not loaded.estimator.training
    assert all(p.dtype == torch.float32 and not p.requires_grad for p in loaded.estimator.parameters())


@pytest.mark.parametrize("change", ["bytes", "window", "source", "f01", "incomplete", "tie_later", "schedule", "budget", "nonfinite", "arm_config"])
def test_receipt_identity_and_selection_fail_closed(tmp_path, change):
    path, saved, receipt, expected, sources = checkpoint_fixture(tmp_path)
    if change == "bytes":
        path.write_bytes(path.read_bytes() + b"changed")
    elif change == "window":
        expected["window_manifest_sha256"] = "d" * 64
    elif change == "source":
        sources[next(iter(sources))] = "d" * 64
    elif change == "f01":
        expected["f01_report_sha256"] = "d" * 64
    elif change == "incomplete":
        receipt["completed_updates"] = 25
    elif change == "tie_later":
        receipt["evaluations"][0]["validation_metric"] = .1
    elif change == "schedule":
        receipt["evaluations"].pop(2)
    elif change == "budget":
        receipt["planned_updates"] = receipt["completed_updates"] = 50
    elif change == "arm_config":
        receipt["training_config"]["arm"] = "B"
    elif change == "nonfinite":
        saved["estimator_state_dict"]["camera_embedding.weight"][0, 0] = float("nan")
        torch.save(saved, path)
        receipt["checkpoint_sha256"] = file_sha256(path)
    with pytest.raises(ValueError):
        load_future_selector_checkpoint(path, receipt, expected_versions=expected, expected_source_hashes=sources)


def test_pair_rejects_mismatched_training_windows_and_duplicate_arm(tmp_path):
    a, _ = load_fixture(tmp_path, "A")
    b, _ = load_fixture(tmp_path, "B")
    validate_future_pair(a, b)
    with pytest.raises(ValueError, match="distinct"):
        validate_future_pair(a, a)
    b.provenance["window_manifest_sha256"] = "d" * 64
    with pytest.raises(ValueError, match="window"):
        validate_future_pair(a, b)


def test_f01_requires_real_model_and_every_required_check(tmp_path):
    loaded, fixture = load_fixture(tmp_path)
    expected = fixture[3]
    report = {"stage": "G1-F01", "status": "passed", "execution": "real_frozen_openvla_l40",
        "config_sha256": loaded.provenance["pair_id"], "window_manifest_sha256": expected["window_manifest_sha256"],
        "model_revision": expected["model_revision"], "input_version": expected["input_version"], "packing_version": PACKING_VERSION,
        "checks": {key: True for key in ("time_alignment", "no_future_leakage", "action_gradient_to_die",
            "future_gradient_to_die", "vla_parameters_unchanged", "hard128_packing", "dense_differentiable_parity")}}
    kwargs = dict(pair_id=loaded.provenance["pair_id"], window_manifest_sha256=expected["window_manifest_sha256"], model_revision=expected["model_revision"])
    require_future_f01(report, **kwargs)
    for key, value in (("execution", "synthetic_cpu"), ("status", "prepared"), ("config_sha256", "d" * 64)):
        with pytest.raises(ValueError, match="real-model"):
            require_future_f01({**report, key: value}, **kwargs)
    report["checks"].pop("future_gradient_to_die")
    with pytest.raises(ValueError, match="real-model"):
        require_future_f01(report, **kwargs)


def synthetic_policy(tmp_path, monkeypatch, *, arm="A", context=None, record_selection=True):
    loaded, _ = load_fixture(tmp_path, arm)
    components = SimpleNamespace(vla=VLA(), action_head=Head(), proprio_projector=torch.nn.Linear(8, 4))
    prepared = []
    def prepare(observation, instruction, processor, stats, *, device, dtype):
        ids = torch.tensor([[1, 17 if instruction == "first" else 23, 2]])
        proprio = torch.arange(8, dtype=torch.float32)[None] / 10
        result = {"pixel_values": torch.tensor([float(observation.get("pixel", 0))]),
            "input_ids": ids, "attention_mask": torch.ones_like(ids), "normalized_proprio": proprio,
            "normalized_proprio_numpy": proprio.numpy()[0], "inputs_version": libero_runtime.INPUTS_VERSION}
        prepared.append(result)
        return result
    monkeypatch.setattr(libero_runtime, "prepare_observation_inputs", prepare)
    policy = FutureRolloutPolicy(components, object(), loaded, stats_key=STATS_KEY,
        stage_context=context, record_selection=record_selection)
    return policy, components, prepared


@pytest.mark.parametrize("arm", ["A", "B"])
def test_one_full_score_one_real_packed_policy_with_original_positions(tmp_path, monkeypatch, arm):
    policy, components, _ = synthetic_policy(tmp_path, monkeypatch, arm=arm)
    seen = []
    def score(batch, retained):
        seen.append(retained.clone())
        return torch.zeros_like(batch.valid, dtype=torch.float32)
    monkeypatch.setattr(policy.selector.estimator, "forward", score)
    chunk = policy({}, "first")
    assert len(seen) == 1 and bool(seen[0].all())
    indices = list(range(64)) + list(range(256, 320))
    assert chunk.metadata["retained_indices"] == indices
    calls = components.vla.language_model.model.calls
    assert len(calls) == components.vla.vision_calls == 1
    assert calls[0]["inputs_embeds"].shape == (1, 190, 4)
    assert calls[0]["position_ids"][0, 1:129].tolist() == [i + 1 for i in indices]
    assert calls[0]["position_ids"][0, 129].item() == 513
    assert not calls[0]["output_hidden_states"] and not calls[0]["use_cache"]
    assert components.action_head.hidden_shapes == [(1, 56, 4)]
    assert chunk.metadata["policy_calls"] == chunk.metadata["scorer_calls"] == 1
    assert chunk.metadata["future_head_calls"] == 0
    assert chunk.normalized_actions.shape == chunk.environment_actions.shape == (8, 7)


def test_profile_hooks_no_hidden_observation_or_language_cache(tmp_path, monkeypatch):
    stages = []
    @contextmanager
    def context(name):
        stages.append(name)
        yield
    policy, components, prepared = synthetic_policy(tmp_path, monkeypatch, context=context, record_selection=False)
    first = policy({"pixel": 0}, "first")
    policy.reset()
    policy.clear_instruction_cache()
    policy.prepare_instruction("second")
    second = policy({"pixel": 1}, "second")
    assert len(prepared) == components.vla.vision_calls == len(components.vla.language_model.model.calls) == 2
    assert stages == ["preprocess", "vision", "condition_selection", "policy", "postprocess"] * 2
    assert not np.array_equal(first.normalized_actions, second.normalized_actions)
    assert "retained_indices" not in first.metadata
    assert first.metadata["language_cache"] == "disabled"


def test_nonfinite_scorer_stops_before_policy(tmp_path, monkeypatch):
    policy, components, _ = synthetic_policy(tmp_path, monkeypatch)
    monkeypatch.setattr(policy.selector.estimator, "forward", lambda batch, retained: torch.full_like(batch.valid, float("nan"), dtype=torch.float32))
    with pytest.raises(ValueError, match="finite"):
        policy({}, "first")
    assert not components.vla.language_model.model.calls


def panel():
    base = ROOT / "configs/manifests/spatial_initial_states_v1"
    return load_future_development_panel(base / "init_states_development.json", base / "g0_development_15.json")


def good_policy(observation, instruction):
    actions = np.zeros((8, 7))
    actions[:, -1] = -1
    return libero_runtime.PolicyChunk(actions, actions, {})


def test_only_pinned_dev_panel_and_no_test_open(monkeypatch):
    original = Path.read_text
    def guarded(path, *args, **kwargs):
        assert "test" not in path.name
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", guarded)
    value = panel()
    assert len(value["states"]) == 30 and value["test_opened"] is False
    base = ROOT / "configs/manifests/spatial_initial_states_v1"
    with pytest.raises(ValueError, match="frozen development"):
        load_future_development_panel(base / "init_states_test.json", base / "g0_development_15.json")


def test_paired_resume_policy_failure_and_same_initial_state(tmp_path):
    value = panel()
    ledger = libero_runtime.TrialLedger(tmp_path / "trials.jsonl", run_signature="synthetic")
    def fail(observation, instruction):
        raise RuntimeError("synthetic policy failure")
    policies = {"future_A": good_policy, "future_B": fail}
    states, seeds = [], []
    def create(state):
        states.append((state["trial_id"], state["initial_state_sha256"]))
        return Env(), "first"
    evaluate_future_trials(value, policies, ledger, create, reseed=lambda: seeds.append(17), stop_after=2)
    assert states[0] == states[1] and seeds == [17, 17]
    assert list(ledger.completed().values())[1]["status"] == "policy_error"
    evaluate_future_trials(value, policies, ledger, create, reseed=lambda: None, stop_after=2)
    assert len(ledger.completed()) == 4 and states[2][0] != states[0][0]
    result = summarize_future_trials(value, policies, ledger, provenance={}, checkpoint_unchanged=True)
    assert result["status"] == "incomplete" and result["paired_AB"]["completed_pairs"] == 2
    assert result["methods"]["future_B"]["policy_failures"] == 2


@pytest.mark.parametrize("field,bad", [("initial_state_sha256", "wrong"), ("source_state_index", 999), ("method", "future_C"), ("split", "test"), ("environment_seed", 99)])
def test_resume_and_summary_reject_mispaired_metadata(tmp_path, field, bad):
    value = panel()
    ledger = libero_runtime.TrialLedger(tmp_path / "trials.jsonl", run_signature="synthetic")
    policies = {"future_A": good_policy, "future_B": good_policy}
    evaluate_future_trials(value, policies, ledger, lambda state: (Env(), "same"), reseed=lambda: None, stop_after=1)
    ledger.events[-1][field] = bad
    with pytest.raises(ValueError, match="identity"):
        summarize_future_trials(value, policies, ledger, provenance={})
    with pytest.raises(ValueError, match="identity"):
        evaluate_future_trials(value, policies, ledger, lambda _: pytest.fail("must reject before environment"), reseed=lambda: None)


def test_interrupted_trial_is_charged_unknown_after_resume(tmp_path):
    value = panel()
    ledger = libero_runtime.TrialLedger(tmp_path / "trials.jsonl", run_signature="synthetic")
    policies = {"future_A": good_policy, "future_B": good_policy}
    def interrupted(state):
        raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        evaluate_future_trials(value, policies, ledger, interrupted, reseed=lambda: None)
    result = summarize_future_trials(value, policies, ledger, provenance={})
    assert result["cost"]["unfinished_attempts_unknown_cost"] == 1 and result["cost"]["policy_calls_total"] is None
    evaluate_future_trials(value, policies, ledger, lambda state: (Env(), "same"), reseed=lambda: None, stop_after=1)
    result = summarize_future_trials(value, policies, ledger, provenance={})
    assert result["cost"]["unfinished_attempts_unknown_cost"] == 1 and result["completed_trials"] == 1

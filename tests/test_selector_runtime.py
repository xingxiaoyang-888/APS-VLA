"""CPU synthetic contracts only; no trained research checkpoint or simulator."""
from contextlib import contextmanager
from dataclasses import asdict
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from torch import nn

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation import libero_runtime as runtime
from cti_vla.evaluation.selector_runtime import (
    LoadedSelector, SelectorRolloutPolicy, camera_budget_schedule, load_selector_checkpoint,
    validate_selector_training_coverage,
)
from cti_vla.evaluation.selector_trials import (
    evaluate_development_trials, load_selector_development_panel, summarize_selector_trials,
)
from cti_vla.evaluation.teacher_diagnostics import json_signature
from cti_vla.labeling.deletion import LABEL_VERSION
from cti_vla.models.abstraction.packing import PACKING_VERSION
from cti_vla.selection import ConditionalInfluenceEstimator
from cti_vla.training.conditional import TrainingLabelScale
from cti_vla.training.offline import OFFLINE_TRAIN_VERSION, OfflineTrainConfig

ROOT = Path(__file__).resolve().parents[1]
STATS_KEY = "libero_spatial_no_noops"
CONDITION = f"{runtime.INPUTS_VERSION}:{STATS_KEY}:frozen-prompt-embeddings"


def checkpoint_fixture(tmp_path):
    model = ConditionalInfluenceEstimator(4, 4, 8, hidden_dim=8)
    config = asdict(OfflineTrainConfig(hidden_dim=8))
    expected = {"model_revision": "fake-model", "dataset_version": "fake-data",
        "input_version": runtime.INPUTS_VERSION, "packing_version": PACKING_VERSION,
        "condition_version": CONDITION, "protocol_signature": "fake-protocol"}
    source_hashes = {"src/cti_vla/selection/conditional.py": "fake-hash"}
    identity = {"training_version": OFFLINE_TRAIN_VERSION, "config": config,
        "train_cache_sha256": "train", "validation_cache_sha256": "validation",
        "run_identity": {**expected, "source_files": source_hashes,
                         "scorer_dimensions": {"visual": 4, "language": 4, "proprio": 8, "hidden": 8}}}
    scale = TrainingLabelScale(.01, 16, ("fake-train-episode",),
        ("fake-model", "fake-data", runtime.INPUTS_VERSION, PACKING_VERSION, CONDITION, "normalized-l1-8x7-v1", LABEL_VERSION))
    payload = {"schema_version": 1, "identity": identity, "identity_sha256": json_signature(identity),
        "estimator": model.state_dict(), "scale": asdict(scale), "best_epoch": 2, "next_epoch": 2,
        "best_score": .1, "history": [{"epoch": 2, "validation": {"mean_l1_task_stage_macro": .1}}]}
    path = tmp_path / "synthetic_best.pt"
    torch.save(payload, path)
    report = {"stage": "G3", "status": "completed", "frozen_base_unchanged": True, "seed": 17,
        "best_checkpoint_sha256": file_sha256(path), "identity_sha256": payload["identity_sha256"],
        "best_epoch": 2, "best_validation_mean_l1": .1, "scale": asdict(scale)}
    return path, payload, report, expected, source_hashes


def test_safe_checkpoint_load_is_frozen_fp32_and_validation_selected(tmp_path):
    path, _, report, expected, sources = checkpoint_fixture(tmp_path)
    loaded = load_selector_checkpoint(path, report, expected_versions=expected, expected_source_hashes=sources)
    assert not loaded.estimator.training
    assert all(not p.requires_grad and p.dtype == torch.float32 for p in loaded.estimator.parameters())
    assert loaded.provenance["training_seed"] == 17
    assert loaded.provenance["best_epoch"] == 2
    assert loaded.scale.value == .01


def test_formal_training_coverage_requires_all_train_and_effective_validation():
    from cti_vla.data.experiment_protocol import load_experiment_protocol
    protocol = load_experiment_protocol(ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")
    episodes = tuple(sorted(protocol.manifests["train"].episode_ids))
    scale = TrainingLabelScale(.1, 906 * 16, episodes, ("v",) * 7)
    selector = LoadedSelector(None, scale, {})
    report = {"train_observations": 906, "validation_observations": 189}
    validate_selector_training_coverage(selector, report, protocol)
    with pytest.raises(ValueError, match="train episodes"):
        validate_selector_training_coverage(LoadedSelector(None, TrainingLabelScale(.1, 906 * 16, episodes[:-1], ("v",) * 7), {}), report, protocol)
    with pytest.raises(ValueError, match="effective-validation"):
        validate_selector_training_coverage(selector, {**report, "validation_observations": 192}, protocol)
    with pytest.raises(ValueError, match="sixteen-label"):
        validate_selector_training_coverage(LoadedSelector(None, TrainingLabelScale(.1, 16, episodes, ("v",) * 7), {}), report, protocol)


@pytest.mark.parametrize("change", ["bytes", "report_status", "version", "source", "latest_epoch", "scale", "nonfinite", "schedule"])
def test_checkpoint_incompatibilities_fail_closed(tmp_path, change):
    path, saved, report, expected, sources = checkpoint_fixture(tmp_path)
    if change == "bytes":
        path.write_bytes(path.read_bytes() + b"changed")
    elif change == "report_status":
        report["status"] = "paused_at_epoch_boundary"
    elif change == "version":
        expected["input_version"] = "processor-only-old"
    elif change == "source":
        sources = {next(iter(sources)): "different-code"}
    else:
        if change == "latest_epoch":
            saved["next_epoch"] = 4
        elif change == "scale":
            saved["scale"]["versions"] = (*saved["scale"]["versions"][:4], "wrong-condition", *saved["scale"]["versions"][5:])
        elif change == "nonfinite":
            saved["estimator"]["camera_embedding.weight"][0, 0] = float("nan")
        elif change == "schedule":
            saved["identity"]["config"]["validation_camera_budgets"] = ((64, 64),)
            saved["identity_sha256"] = report["identity_sha256"] = json_signature(saved["identity"])
        torch.save(saved, path)
        report["best_checkpoint_sha256"] = file_sha256(path)
    with pytest.raises(ValueError):
        load_selector_checkpoint(path, report, expected_versions=expected, expected_source_hashes=sources)


class Backbone(nn.Module):
    def __init__(self):
        super().__init__()
        self.embed_tokens = nn.Embedding(30000, 4)
        self.calls = []
    def forward(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(last_hidden_state=kwargs["inputs_embeds"].cumsum(1) / 1000)


class VLA(nn.Module):
    def __init__(self):
        super().__init__()
        self.language_model = nn.Module()
        self.language_model.model = Backbone()
        self.norm_stats = {STATS_KEY: {"proprio": {"test_stats": True}}}
        self.visual = torch.arange(512 * 4, dtype=torch.float32).reshape(1, 512, 4) / 10000
        self.vision_calls = 0
    def get_input_embeddings(self):
        return self.language_model.model.embed_tokens
    def _process_vision_features(self, pixels, language, film):
        assert language is None and film is False and not torch.is_grad_enabled()
        self.vision_calls += 1
        return self.visual + float(pixels.flatten()[0])
    def _unnormalize_actions(self, actions, stats_key):
        assert stats_key == STATS_KEY
        physical = actions.copy()
        physical[:, -1] = (physical[:, -1] + 1) / 2
        return physical


class Head(nn.Module):
    def __init__(self):
        super().__init__()
        self.hidden_shapes = []
    def predict_action(self, hidden):
        self.hidden_shapes.append(tuple(hidden.shape))
        return hidden.reshape(1, 8, 7, 4).mean(-1).tanh()


def synthetic_policy(tmp_path, monkeypatch, target=128, context=None, record_selection=True):
    path, _, report, expected, sources = checkpoint_fixture(tmp_path)
    loaded = load_selector_checkpoint(path, report, expected_versions=expected, expected_source_hashes=sources)
    components = SimpleNamespace(vla=VLA(), action_head=Head(), proprio_projector=nn.Linear(8, 4))
    prepared = []
    def prepare(observation, instruction, processor, stats, *, device, dtype):
        assert stats == {"test_stats": True}
        ids = torch.tensor([[1, 17 if instruction == "first" else 23, 2]])
        proprio = torch.arange(8, dtype=torch.float32)[None] / 10
        value = {"pixel_values": torch.tensor([float(observation.get("pixel", 0))]),
                 "input_ids": ids, "attention_mask": torch.ones_like(ids), "normalized_proprio": proprio,
                 "normalized_proprio_numpy": proprio.numpy()[0], "inputs_version": runtime.INPUTS_VERSION}
        prepared.append(value)
        return value
    monkeypatch.setattr(runtime, "prepare_observation_inputs", prepare)
    policy = SelectorRolloutPolicy(components, object(), loaded, stats_key=STATS_KEY, target_tokens=target,
                                   stage_context=context, record_selection=record_selection)
    return policy, components, prepared


@pytest.mark.parametrize("budget", [256, 128, 64])
def test_staged_selection_uses_one_actual_packed_forward_original_positions(tmp_path, monkeypatch, budget):
    policy, components, prepared = synthetic_policy(tmp_path, monkeypatch, target=budget)
    observed = []
    hook = policy.selector.estimator.register_forward_pre_hook(lambda module, args: observed.append((args[0], args[1].clone())))
    result = policy({}, "first")
    hook.remove()
    backbone = components.vla.language_model.model
    assert components.vla.vision_calls == len(backbone.calls) == 1
    assert [int(mask.sum()) for _, mask in observed] == [512, 256, 128][:len(camera_budget_schedule(budget))]
    first_batch = observed[0][0]
    assert torch.equal(first_batch.normalized_proprio, prepared[0]["normalized_proprio"])
    assert torch.equal(first_batch.instruction_embeddings, components.vla.get_input_embeddings()(prepared[0]["input_ids"]))
    assert not first_batch.visual.requires_grad
    kept = result.metadata["retained_indices"]
    assert len(kept) == budget and kept == sorted(set(kept))
    assert sum(index < 256 for index in kept) == budget // 2
    call = backbone.calls[0]
    assert call["inputs_embeds"].shape[1] == budget + 62  # BOS+proprio+3 prompt+56 action+stop
    assert call["position_ids"][0, 1:1 + budget].tolist() == [index + 1 for index in kept]
    assert call["position_ids"][0, budget + 1].item() == 513
    assert bool((call["attention_mask"] == 1).all())
    assert call["output_hidden_states"] is False and call["use_cache"] is False
    assert components.action_head.hidden_shapes == [(1, 56, 4)]
    assert result.metadata["policy_calls"] == 1 and result.metadata["scorer_calls"] == len(observed)
    np.testing.assert_array_equal(result.environment_actions[:, -1], -np.sign(result.normalized_actions[:, -1]))


def test_hook_stages_and_fresh_inputs_no_hidden_observation_cache(tmp_path, monkeypatch):
    stages = []
    @contextmanager
    def context(name):
        stages.append((name, "start"))
        yield
        stages.append((name, "end"))
    policy, components, prepared = synthetic_policy(tmp_path, monkeypatch, context=context, record_selection=False)
    first = policy({"pixel": 0}, "first")
    policy.reset()
    second = policy({"pixel": 1}, "second")
    assert len(prepared) == components.vla.vision_calls == len(components.vla.language_model.model.calls) == 2
    assert not np.array_equal(first.normalized_actions, second.normalized_actions)
    assert stages[:10] == [(name, boundary) for name in ("preprocess", "vision", "condition_selection", "policy", "postprocess") for boundary in ("start", "end")]
    assert "retained_indices" not in first.metadata
    assert first.metadata["language_cache"] == "disabled"


def test_selector_error_stops_before_policy_and_never_returns_invalid_actions(tmp_path, monkeypatch):
    policy, components, _ = synthetic_policy(tmp_path, monkeypatch)
    monkeypatch.setattr(policy.selector.estimator, "forward", lambda batch, retained: torch.full_like(batch.valid, float("nan"), dtype=torch.float32))
    with pytest.raises(ValueError, match="finite"):
        policy({}, "first")
    assert not components.vla.language_model.model.calls


def real_panel():
    root = ROOT / "configs/manifests/spatial_initial_states_v1"
    return load_selector_development_panel(root / "init_states_development.json", root / "g0_development_15.json", root / "init_states_test.json")


def test_selector_development_panel_is_same_three_tasks_ten_states_and_no_test():
    panel = real_panel()
    assert len(panel["states"]) == 30
    assert len({row["task_id"] for row in panel["states"]}) == 3
    assert panel["split"] == "development" and panel["split_check"]["overlap"] == 0
    root = ROOT / "configs/manifests/spatial_initial_states_v1"
    with pytest.raises(ValueError, match="development states"):
        load_selector_development_panel(root / "init_states_test.json", root / "g0_development_15.json", root / "init_states_development.json")


def env_observation():
    return {"agentview_image": np.zeros((2, 2, 3), dtype=np.uint8), "robot0_eye_in_hand_image": np.zeros((2, 2, 3), dtype=np.uint8),
            "robot0_eef_pos": np.zeros(3), "robot0_eef_quat": np.array([0., 0., 0., 1.]), "robot0_gripper_qpos": np.zeros(2)}


class Env:
    def reset(self):
        self.steps = 0
    def set_init_state(self, values):
        self.values = values
        return env_observation()
    def step(self, action):
        self.steps += 1
        return env_observation(), 0, self.steps == 19, {}
    def close(self):
        pass


def test_selector_adapter_runs_unchanged_chunk8_queue(tmp_path, monkeypatch):
    policy, components, _ = synthetic_policy(tmp_path, monkeypatch)
    result = runtime.run_episode(Env(), policy, "first", [1.])
    assert result["success"] and result["control_steps"] == 9
    assert result["wait_steps"] == 10 and result["policy_calls"] == 2
    assert components.vla.vision_calls == len(components.vla.language_model.model.calls) == 2
    assert [row["control_step"] for row in result["chunks"]] == [0, 8]


def test_paired_trial_resume_keeps_policy_failures_and_same_initial_state(tmp_path):
    panel = real_panel()
    ledger = runtime.TrialLedger(tmp_path / "trials.jsonl", run_signature="synthetic-frozen")
    calls = []
    def good(observation, instruction):
        value = np.zeros((8, 7))
        value[:, -1] = -1
        return runtime.PolicyChunk(value, value, {})
    def broken(observation, instruction):
        raise RuntimeError("synthetic OOM")
    policies = {"dense": good, "uniform128": good, "cti128": broken}
    def create(state):
        calls.append((state["trial_id"], state["initial_state_sha256"]))
        return Env(), "same task"
    evaluate_development_trials(panel, policies, ledger, create, reseed=lambda: None, stop_after=3)
    assert calls[0] == calls[1] == calls[2]
    assert len(ledger.completed()) == 3
    assert list(ledger.completed().values())[-1]["status"] == "policy_error"
    evaluate_development_trials(panel, policies, ledger, create, reseed=lambda: None, stop_after=3)
    assert len(ledger.completed()) == 6 and calls[3][0] != calls[0][0]
    summary = summarize_selector_trials(panel, ledger, provenance={}, checkpoint_unchanged=True)
    assert summary["status"] == "incomplete"
    assert summary["methods"]["cti128"]["policy_failures"] == 2
    assert summary["methods"]["cti128"]["task_macro_success_rate"] is None


def test_infrastructure_failure_retains_trial_and_retries_same_id(tmp_path):
    panel = real_panel()
    ledger = runtime.TrialLedger(tmp_path / "trials.jsonl", run_signature="synthetic-frozen")
    def fail(state):
        raise RuntimeError("renderer unavailable")
    policies = {name: None for name in ("dense", "uniform128", "cti128")}
    for _ in range(2):
        with pytest.raises(RuntimeError, match="infrastructure failure"):
            evaluate_development_trials(panel, policies, ledger, fail, reseed=lambda: None)
    assert not ledger.completed()
    assert len({row["trial_id"] for row in ledger.events}) == 1
    assert len([row for row in ledger.events if row["event"] == "result"]) == 2


@pytest.mark.parametrize("field,value", [("initial_state_sha256", "wrong-state"), ("method", "cti64"),
    ("environment_seed", 99), ("source_state_index", 999), ("split", "test"), ("task_id", 999)])
def test_resume_and_standalone_summary_reject_mispaired_identity(tmp_path, field, value):
    panel = real_panel()
    ledger = runtime.TrialLedger(tmp_path / "trials.jsonl", run_signature="synthetic-frozen")
    def fail(state):
        raise RuntimeError("synthetic unavailable renderer")
    policies = {name: None for name in ("dense", "uniform128", "cti128")}
    with pytest.raises(RuntimeError):
        evaluate_development_trials(panel, policies, ledger, fail, reseed=lambda: None)
    ledger.events[-1][field] = value
    with pytest.raises(ValueError, match="identity"):
        evaluate_development_trials(panel, policies, ledger, fail, reseed=lambda: None)
    with pytest.raises(ValueError, match="identity"):
        summarize_selector_trials(panel, ledger, provenance={})

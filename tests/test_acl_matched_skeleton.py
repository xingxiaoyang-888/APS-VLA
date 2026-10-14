"""Synthetic CPU baseline adaptation checks; no native/GPU reproduction."""

import ast
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch
from torch import nn

from cti_vla.data.experiment_protocol import ExperimentProtocol, load_experiment_protocol
from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
from cti_vla.labeling import DeletionTeacher, LabelProvenance
from cti_vla.labeling.deletion import LABEL_VERSION
from cti_vla.models.abstraction.packing import PACKING_VERSION
from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
from cti_vla.selection import ConditionalInfluenceEstimator, ConditionalTokenBatch, staged_topk
from cti_vla.training.offline import (
    OFFLINE_CACHE_VERSION, OfflineDataset, OfflineObservation, initial_training_assignments,
    sample_initial_sets, save_offline_observation,
)
from cti_vla_baselines.acl_matched import (
    METHOD_ID, UPSTREAM_UTILS_SHA256, FrozenDifferentiableOFTPolicy, MatchedCost, cosine_alpha, gate_raw_tokens,
    join_cached_observation, matched_epoch_batches, matched_loss, select_matched,
    soft_top_k, supplement_receipt, train_matched_step,
)

ROOT = Path(__file__).resolve().parents[1]


class ToyBackbone(nn.Module):
    def __init__(self):
        super().__init__()
        self.embed_tokens = nn.Embedding(20, 4)
        self.transform = nn.Linear(4, 4)
        self.last_call = None

    def forward(self, **kwargs):
        self.last_call = kwargs
        values = self.transform(kwargs["inputs_embeds"])
        denominator = torch.arange(1, values.shape[1] + 1, device=values.device)[None, :, None]
        # Causal mixing makes action tokens depend on every earlier raw token.
        hidden = values.cumsum(1) / denominator + kwargs["position_ids"][..., None] * .0001
        return SimpleNamespace(last_hidden_state=hidden)


class ToyVLA(nn.Module):
    def __init__(self):
        super().__init__()
        self.language_model = nn.Module()
        self.language_model.model = ToyBackbone()

    def get_input_embeddings(self):
        return self.language_model.model.embed_tokens


class ToyHead(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(7 * 4, 7)

    def predict_action(self, hidden):
        return self.linear(hidden.reshape(hidden.shape[0], 8, 28))


@pytest.fixture
def matched(tmp_path):
    torch.manual_seed(71)
    real = load_experiment_protocol(ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")
    source = real.manifests["train"]
    episode = source.episodes[0]
    train = replace(source, episodes=(episode,), samples=tuple(s for s in source.samples if s.episode_id == episode.episode_id))
    protocol = ExperimentProtocol(real.path, dict(real.payload, content_signature="synthetic-acl-protocol"),
                                  dict(real.manifests, train=train), real.excluded_episode_ids)
    vla = ToyVLA()
    teacher = OpenVLAOFTTokenPolicy(vla, ToyHead(), nn.Linear(8, 4), num_patches_full=512,
                                   assistant_empty_token_id=9)
    projector = nn.Linear(3, 4)
    student = FrozenDifferentiableOFTPolicy(teacher, projector, model_revision="toy-model", input_version="toy-input")
    config = {"split": "train", "protocol_signature": protocol.payload["content_signature"],
              "model_revision": "toy-model", "dataset_version": protocol.payload["source_signature"],
              "input_version": "toy-input", "packing_version": PACKING_VERSION,
              "condition_version": "toy-condition", "action_version": "normalized-l1-8x7-v1", "label_version": LABEL_VERSION}
    entries, raw_inputs, black_inputs = [], [], []
    assignments = initial_training_assignments(train)
    for sample in train.samples:
        raw = torch.randn(1, 512, 3)
        black = torch.randn(1, 512, 3) * .2  # Explicit synthetic fixture, not real black-image features.
        ids = torch.tensor([[1, 7, 9]])
        mask = torch.ones_like(ids)
        with torch.no_grad():
            batch = ConditionalTokenBatch(projector(raw), vla.get_input_embeddings()(ids), mask.bool(), torch.randn(1, 8),
                                           torch.tensor([[0] * 256 + [1] * 256]), torch.arange(256).repeat(2)[None],
                                           torch.ones(1, 512, dtype=torch.bool))
        provenance = LabelProvenance((str(sample.sample_id),), (sample.episode_id,), "train", "toy-model",
                                     protocol.payload["source_signature"], "toy-input", PACKING_VERSION,
                                     "toy-condition", "normalized-l1-8x7-v1")
        def callback(data, indices):
            return teacher.forward_from_full_tokens(data.visual, data.normalized_proprio,
                input_ids=ids, attention_mask=mask, retained_indices=indices)
        labeler = DeletionTeacher(teacher, callback)
        reference = labeler.reference(batch, provenance)
        records = []
        for retained, candidates in sample_initial_sets(assignments[sample.sample_id]):
            keep = torch.zeros_like(batch.valid)
            keep[:, list(retained)] = True
            records.append(labeler.label(batch, keep, torch.tensor([candidates]), provenance, full_reference=reference))
        metadata = {**asdict(sample), "task_name": episode.task_name, "assignment": assignments[sample.sample_id],
                    "build_config_sha256": json_signature(config)}
        item = OfflineObservation(batch, tuple(records), ids, mask, metadata)
        path = tmp_path / f"{sample.sample_id}.pt"
        digest = save_offline_observation(path, item)
        entries.append({**metadata, "path": path.name, "sha256": digest})
        raw_inputs.append(raw)
        black_inputs.append(black)
    index = {"cache_version": OFFLINE_CACHE_VERSION, "status": "completed", "split": "train",
             "protocol_signature": protocol.payload["content_signature"], "build_config": config,
             "build_config_sha256": json_signature(config), "observations": entries, "expected_observations": len(entries)}
    atomic_json(tmp_path / "index.json", index)
    dataset = OfflineDataset(tmp_path / "index.json", protocol, split="train")
    receipt = supplement_receipt(dataset, 0, raw_inputs[0], black_inputs[0], black_preprocessing_signature="synthetic-toy-black-not-real-asset")
    full = join_cached_observation(dataset, 0, 0, raw_inputs[0], black_inputs[0], receipt)
    partial = join_cached_observation(dataset, 0, 1, raw_inputs[0], black_inputs[0], receipt)
    scorer = ConditionalInfluenceEstimator(4, 4, 8, hidden_dim=8)
    return SimpleNamespace(protocol=protocol, dataset=dataset, teacher=teacher, student=student, vla=vla,
                           full=full, partial=partial, scorer=scorer)


def test_lapsum_budget_shift_invariance_and_finite_difference_gradient():
    scores = torch.tensor([[-.4, .2, .7, 1.1]], requires_grad=True)
    weights = torch.tensor([[.2, -.3, .8, .4]])
    selected = soft_top_k(scores, 2, .6)
    assert selected.sum().item() == pytest.approx(2, abs=2e-6)
    assert torch.allclose(selected, soft_top_k(scores + 3, 2, .6), atol=2e-6)
    (selected * weights).sum().backward()
    assert scores.grad.sum().abs() < 1e-6
    numeric = []
    for column in range(4):
        positive, negative = scores.detach().clone(), scores.detach().clone()
        positive[0, column] += .002
        negative[0, column] -= .002
        numeric.append(float(((soft_top_k(positive, 2, .6) - soft_top_k(negative, 2, .6)) * weights).sum() / .004))
    assert torch.allclose(scores.grad[0], torch.tensor(numeric), atol=4e-5, rtol=5e-4)
    with pytest.raises(ValueError, match="budget"):
        soft_top_k(scores, 4, .6)


def test_math_matches_pinned_author_forward_and_vjp_when_source_available():
    path = ROOT / "external/VLA-ACL/src/openvla-oft/prismatic/training/scorer_train_utils.py"
    if not path.exists():
        pytest.skip("optional author source fixture is not included in the project checkout")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == UPSTREAM_UTILS_SHA256
    names = {"_laplace_cdf", "_solve_lapsum_threshold", "SoftTopK", "soft_top_k", "gate_vision_tokens"}
    source = ast.parse(path.read_text(encoding="utf-8"))
    selected = ast.Module(body=[node for node in source.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names], type_ignores=[])
    namespace = {"torch": torch}
    exec(compile(selected, str(path), "exec"), namespace)
    left = torch.tensor([[-2., .1, .3, 1.3]], requires_grad=True)
    right = left.detach().clone().requires_grad_(True)
    ours, theirs = soft_top_k(left, 2, .2), namespace["soft_top_k"](right, 2, .2)
    assert torch.allclose(ours, theirs, atol=1e-7)
    weights = torch.tensor([[.2, 1., -.3, .6]])
    (ours * weights).sum().backward()
    (theirs * weights).sum().backward()
    assert torch.allclose(left.grad, right.grad, atol=1e-7)
    raw, black = torch.randn(1, 4, 3), torch.randn(1, 4, 3)
    assert torch.equal(gate_raw_tokens(raw, ours, black), namespace["gate_vision_tokens"](raw, theirs, black))


def test_black_gate_uses_author_detached_stabilizer_not_its_full_derivative():
    raw = torch.tensor([[[2., 3.], [4., 6.]]])
    black = torch.tensor([[[7., 9.], [8., 10.]]])
    scores = torch.tensor([[.5, 1.]], requires_grad=True)
    out = gate_raw_tokens(raw, scores, black)
    assert torch.allclose(out[:, 0], .5 * raw[:, 0] + math_sqrt(.75) * black[:, 0])
    assert torch.equal(out[:, 1], raw[:, 1])
    out.sum().backward()
    assert torch.equal(scores.grad, raw.sum(-1)) and torch.isfinite(scores.grad).all()


def math_sqrt(value):
    return value ** .5


def test_student_parity_original_positions_and_input_gradient_teacher_stays_detached(matched):
    r = matched.partial
    indices = r.retained_mask.nonzero()[:, 1][None]
    projected = r.observation.batch.visual[:, indices[0]].clone().requires_grad_(True)
    kwargs = {"input_ids": r.observation.input_ids, "attention_mask": r.observation.attention_mask}
    actual = matched.student(projected, indices, normalized_proprio=r.observation.batch.normalized_proprio, **kwargs)
    positions = matched.vla.language_model.model.last_call["position_ids"].clone()
    expected = matched.teacher.forward_from_tokens(projected, r.observation.batch.normalized_proprio,
                                                   patch_keep_mask=r.retained_mask, **kwargs)
    assert torch.equal(actual, expected) and not expected.requires_grad
    assert torch.equal(positions, matched.vla.language_model.model.last_call["position_ids"])
    assert torch.equal(positions[:, 1:1 + indices.shape[1]], indices + 1)
    assert positions[0, 1 + indices.shape[1]].item() == 513
    actual.square().mean().backward()
    assert projected.grad.abs().sum() > 0
    assert all(p.grad is None and not p.requires_grad for p in matched.student.parameters())


def test_train_step_reaches_conditional_scorer_only_and_soft_S_is_not_hard_K(matched):
    before = {name: value.clone() for name, value in matched.student.state_dict().items()}
    optimizer = torch.optim.AdamW(matched.scorer.parameters(), lr=3e-4, weight_decay=1e-4)
    cost = MatchedCost()
    result = train_matched_step(matched.scorer, matched.student, optimizer, (matched.full, matched.partial),
                                matched.protocol, alpha=.6, cost=cost)
    assert result["method_id"] == METHOD_ID and "adaptation" in METHOD_ID
    assert cost.student_forwards_completed == cost.backward_completed == 2 and cost.optimizer_steps == 1
    assert len(cost.cached_teacher_observations) == 1
    for trace in result["traces"]:
        assert trace["physical_student_visual_tokens"] == 2 * trace["soft_target_total"]
        assert sum(trace["gate_sum_by_camera"]) == pytest.approx(trace["soft_target_total"], abs=1e-3)
    for prefix in ("language_projection", "proprio_encoder", "set_projection", "visual_projection"):
        assert any(p.grad is not None and p.grad.abs().sum() > 0 for name, p in matched.scorer.named_parameters() if name.startswith(prefix))
    assert all(torch.equal(before[name], value) for name, value in matched.student.state_dict().items())
    assert all(p.grad is None for p in matched.student.parameters())


def test_receipt_rejects_changed_raw_or_black_or_prompt(matched):
    matched.full.black.add_(1)
    with pytest.raises(ValueError, match="not bound"):
        matched.full.validate(matched.protocol)
    matched.partial.observation.input_ids[0, 1] += 1
    with pytest.raises(ValueError, match="not bound"):
        matched.partial.validate(matched.protocol)


def test_wrong_split_and_extra_optimizer_parameters_fail_before_student(matched):
    dataset = matched.dataset
    dataset.split = "validation"
    with pytest.raises(ValueError, match="train"):
        join_cached_observation(dataset, 0, 0, matched.full.raw, matched.full.black, matched.full.receipt)
    dataset.split = "train"
    optimizer = torch.optim.AdamW([*matched.scorer.parameters(), *matched.student.parameters()], lr=3e-4)
    cost = MatchedCost()
    with pytest.raises(ValueError, match="exactly"):
        train_matched_step(matched.scorer, matched.student, optimizer, [matched.full], matched.protocol, alpha=.5, cost=cost)
    assert cost.student_forwards_started == 0


def test_projector_mismatch_is_rejected_before_student_backbone(matched):
    with torch.no_grad():
        matched.student.visual_projector.weight.add_(.1)
    cost = MatchedCost()
    with pytest.raises(ValueError, match="does not project"):
        matched_loss(matched.scorer, matched.student, matched.full, matched.protocol, alpha=.5, cost=cost)
    assert cost.student_forwards_started == 0 and cost.projector_parity_forwards == 1


def test_common_hard_selection_and_epoch_record_budget(matched):
    matched.scorer.eval()
    for parameter in matched.scorer.parameters():
        nn.init.zeros_(parameter)
    batch = matched.full.observation.batch
    actual = select_matched(matched.scorer, batch, budget=64)
    common = staged_topk(matched.scorer, batch, ((128, 128), (64, 64), (32, 32)))
    assert torch.equal(actual.source_indices, common.source_indices)
    assert actual.source_indices.tolist() == [list(range(32)) + list(range(256, 288))]
    batches = matched_epoch_batches(matched.dataset, seed=17, epoch=2)
    assert sorted(i for b in batches for i in b) == list(range(len(matched.dataset)))
    assert all(len(b) == 16 for b in batches[:-1]) and 1 <= len(batches[-1]) <= 16
    assert cosine_alpha(0, 100) == 2 and cosine_alpha(100, 100) == .1

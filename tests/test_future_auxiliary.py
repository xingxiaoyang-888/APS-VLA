"""Synthetic CPU G1-F behavior checks; not a real VLA training result."""

import copy
from dataclasses import replace
from types import SimpleNamespace

import pytest
import torch
from torch import nn
from torch.nn import functional as F

from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
from cti_vla.selection import ConditionalInfluenceEstimator, ConditionalTokenBatch
from cti_vla.training.future_auxiliary import (
    FUTURE_SELECTION_VERSION, FrozenFutureRepresentation, FutureAuxiliaryHead,
    FutureTrainingBatch, frozen_future_target, future_auxiliary_loss, hard_select_future,
)
from cti_vla_baselines.acl_matched import FrozenDifferentiableOFTPolicy, gate_raw_tokens


class ToyBackbone(nn.Module):
    def __init__(self):
        super().__init__()
        self.embed_tokens = nn.Embedding(20, 8)
        self.transform = nn.Linear(8, 8)
        self.calls = 0

    def forward(self, **kwargs):
        self.calls += 1
        values = torch.tanh(self.transform(kwargs["inputs_embeds"]))
        positions = kwargs["position_ids"]
        count = torch.arange(1, values.shape[1] + 1, device=values.device)[None, :, None]
        hidden = values.cumsum(1) / count + positions[..., None] * .0001
        return SimpleNamespace(last_hidden_state=hidden)


class ToyVLA(nn.Module):
    def __init__(self):
        super().__init__()
        self.language_model = nn.Module()
        self.language_model.model = ToyBackbone()

    def get_input_embeddings(self):
        return self.language_model.model.embed_tokens


class ToyActionHead(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(7 * 8, 7)

    def predict_action(self, hidden):
        return self.linear(hidden.reshape(hidden.shape[0], 8, 7 * 8))


@pytest.fixture(autouse=True)
def cpu_threads():
    # Tiny tensor tests otherwise spend most time starting CPU thread pools.
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


@pytest.fixture
def example():
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(171)
        vla = ToyVLA()
        teacher = OpenVLAOFTTokenPolicy(vla, ToyActionHead(), nn.Linear(8, 8),
                                       num_patches_full=512, assistant_empty_token_id=9)
        projector = nn.Sequential(nn.Linear(5, 8), nn.SiLU(), nn.Linear(8, 8))
        student = FrozenDifferentiableOFTPolicy(teacher, projector, model_revision="synthetic-model", input_version="synthetic-input")
        raw = torch.randn(2, 512, 5)
        # Synthetic fixture only: not asserted to be genuine black-image features.
        black = torch.randn_like(raw) * .3
        ids = torch.tensor([[1, 3, 9], [1, 4, 9]])
        attention = torch.ones_like(ids)
        with torch.no_grad():
            conditions = ConditionalTokenBatch(projector(raw), vla.get_input_embeddings()(ids), attention.bool(),
                torch.randn(2, 8), torch.arange(2).repeat_interleave(256)[None].expand(2, -1),
                torch.arange(256).repeat(2)[None].expand(2, -1), torch.ones(2, 512, dtype=torch.bool))
            full = teacher.forward_from_full_tokens(conditions.visual, conditions.normalized_proprio,
                                                     input_ids=ids, attention_mask=attention)
            target = frozen_future_target(projector(torch.randn_like(raw)))
        batch = FutureTrainingBatch(conditions, raw, black, ids, attention, full,
                                   torch.tanh(torch.randn(2, 8, 7)), target)
        scorer = ConditionalInfluenceEstimator(8, 8, 8, hidden_dim=16)
        auxiliary = FutureAuxiliaryHead(8)
    return SimpleNamespace(vla=vla, teacher=teacher, student=student, batch=batch,
                           scorer=scorer, auxiliary=auxiliary)


def trainable_gradient(module):
    return sum(float(p.grad.abs().sum()) for p in module.parameters() if p.grad is not None)


def test_spatial_cells_projection_normalization_and_private_rng():
    rng_before = torch.get_rng_state().clone()
    reducer = FrozenFutureRepresentation(3)
    assert torch.equal(rng_before, torch.get_rng_state())
    assert not list(reducer.parameters())
    assert torch.equal(reducer.projection, FrozenFutureRepresentation(3).projection)
    assert not torch.equal(reducer.projection, FrozenFutureRepresentation(3, projection_seed=918).projection)
    grid = torch.arange(2 * 16 * 16 * 3, dtype=torch.float32).reshape(2, 16, 16, 3) / 100
    pooled = torch.stack([grid[c, r:r + 8, s:s + 8].mean((0, 1))
                          for c in range(2) for r in [0, 8] for s in [0, 8]])
    expected = F.layer_norm(pooled @ reducer.projection, (64,), eps=1e-5).reshape(1, 512)
    assert torch.allclose(reducer(grid.reshape(1, 512, 3)), expected, atol=2e-6, rtol=1e-6)
    assert reducer.specification()["normalization_eps"] == 1e-5


def test_current_representation_keeps_gradients_future_target_does_not(example):
    current = example.batch.conditions.visual.clone().requires_grad_(True)
    reducer = example.auxiliary.representation
    output = reducer(current)
    weights = torch.linspace(-1, 1, 512)[None]
    (output * weights).mean().backward()
    assert current.grad is not None and current.grad.abs().sum() > 0
    with torch.inference_mode():
        frozen = example.batch.conditions.visual.clone()
        target = frozen_future_target(frozen)
    assert not target.requires_grad and not target.is_inference()
    assert torch.equal(target, reducer.target(example.batch.conditions.visual))
    with pytest.raises(ValueError, match="detached"):
        reducer.target(current)


@pytest.mark.parametrize("budget", [32, 64])
def test_action_A_is_exact_half_teacher_half_GT_and_soft_mass_is_per_sample(example, budget):
    x = future_auxiliary_loss(example.scorer, example.student, example.batch, alpha=.6, tokens_per_camera=budget)
    teacher = F.l1_loss(x.predicted_actions.float(), example.batch.teacher_actions)
    gt = F.l1_loss(x.predicted_actions.float(), example.batch.demonstration_actions)
    assert torch.equal(x.action_loss, .5 * teacher + .5 * gt)
    assert torch.equal(x.loss, x.action_loss) and x.future_mse is None
    assert x.gates.shape == (2, 512)
    assert torch.allclose(x.gates.reshape(2, 2, 256).sum(-1), torch.full((2, 2), float(budget)), atol=2e-4, rtol=0)
    assert x.source_indices.tolist() == [list(range(512))] * 2
    assert x.metrics()["physical_student_visual_tokens"] == 512
    assert x.metrics()["hard_deployment_visual_tokens"] == 2 * budget
    x.action_loss.backward()
    assert trainable_gradient(example.scorer) > 0
    example.student.require_frozen()


@pytest.mark.parametrize("budget", [32, 64])
def test_AB_identical_initial_scorer_and_action_path_only_B_adds_future_loss(example, budget):
    # This is the required runner construction order: clone before creating B's head.
    a, b = copy.deepcopy(example.scorer), copy.deepcopy(example.scorer)
    head = FutureAuxiliaryHead(8)
    assert all(torch.equal(a.state_dict()[k], v) for k, v in b.state_dict().items())
    result_a = future_auxiliary_loss(a, example.student, example.batch, alpha=1.2, tokens_per_camera=budget)
    result_b = future_auxiliary_loss(b, example.student, example.batch, alpha=1.2, auxiliary_head=head, tokens_per_camera=budget)
    assert torch.equal(result_a.scores, result_b.scores)
    assert torch.equal(result_a.gates, result_b.gates)
    assert torch.equal(result_a.predicted_actions, result_b.predicted_actions)
    assert torch.equal(result_a.action_loss, result_b.action_loss)
    assert torch.equal(result_b.loss, result_b.action_loss + .1 * result_b.future_mse)


@pytest.mark.parametrize("budget", [32, 64])
def test_future_loss_alone_reaches_DIE_and_has_no_ungated_head_input(example, budget):
    captured = []
    hook = example.auxiliary.register_forward_pre_hook(lambda module, args: captured.append(args))
    result = future_auxiliary_loss(example.scorer, example.student, example.batch, alpha=.5,
                                   auxiliary_head=example.auxiliary, tokens_per_camera=budget)
    hook.remove()
    assert len(captured) == 1 and len(captured[0]) == 2
    expected = example.student.visual_projector(gate_raw_tokens(example.batch.raw_tokens, result.gates, example.batch.black_tokens))
    assert torch.equal(captured[0][0], expected)
    assert not torch.equal(captured[0][0], example.batch.conditions.visual)
    assert captured[0][1] is example.batch.demonstration_actions
    result.future_mse.backward()
    assert trainable_gradient(example.scorer) > 0
    assert trainable_gradient(example.auxiliary) > 0
    assert all(p.grad is None and not p.requires_grad for p in example.student.parameters())
    assert all(getattr(example.batch, name).grad is None for name in
               ["raw_tokens", "black_tokens", "teacher_actions", "demonstration_actions", "future_target"])


def test_one_optimizer_update_changes_DIE_and_head_but_not_any_VLA_parameter(example):
    frozen = {name: v.clone() for name, v in example.student.state_dict().items()}
    scorer_before = {name: p.clone() for name, p in example.scorer.named_parameters()}
    head_before = {name: p.clone() for name, p in example.auxiliary.named_parameters()}
    optimizer = torch.optim.AdamW([*example.scorer.parameters(), *example.auxiliary.parameters()], lr=1e-4, weight_decay=.01)
    result = future_auxiliary_loss(example.scorer, example.student, example.batch, alpha=2., auxiliary_head=example.auxiliary)
    result.loss.backward()
    torch.nn.utils.clip_grad_norm_([*example.scorer.parameters(), *example.auxiliary.parameters()], 1., error_if_nonfinite=True)
    optimizer.step()
    assert any(not torch.equal(scorer_before[k], p) for k, p in example.scorer.named_parameters())
    assert any(not torch.equal(head_before[k], p) for k, p in example.auxiliary.named_parameters())
    assert all(torch.equal(frozen[k], p) for k, p in example.student.state_dict().items())
    example.student.require_frozen()


def test_future_target_and_demonstration_cannot_leak_into_scores_or_policy(example):
    changed = replace(example.batch, demonstration_actions=-example.batch.demonstration_actions,
                      future_target=example.batch.future_target + .7)
    first = future_auxiliary_loss(example.scorer, example.student, example.batch, alpha=.8, auxiliary_head=example.auxiliary)
    second = future_auxiliary_loss(example.scorer, example.student, changed, alpha=.8, auxiliary_head=example.auxiliary)
    assert torch.equal(first.scores, second.scores)
    assert torch.equal(first.gates, second.gates)
    assert torch.equal(first.predicted_actions, second.predicted_actions)
    assert first.demonstration_l1 != second.demonstration_l1
    assert first.future_mse != second.future_mse


@pytest.mark.parametrize("budget", [32, 64])
def test_shared_hard_path_calls_scorer_once_keeps_registered_original_positions_without_head(example, budget):
    scorer = example.scorer.eval()
    for p in scorer.parameters():
        nn.init.zeros_(p)
    calls = []
    hook = scorer.register_forward_pre_hook(lambda module, args: calls.append(args[1].clone()))
    selected = hard_select_future(scorer, example.batch.conditions, tokens_per_camera=budget)
    hook.remove()
    assert len(calls) == 1 and calls[0].all()
    assert selected.source_indices.tolist() == [list(range(budget)) + list(range(256, 256 + budget))] * 2
    assert len(selected.stage_masks) == 1
    assert "single" in FUTURE_SELECTION_VERSION
    with pytest.raises(ValueError, match="eval"):
        hard_select_future(scorer.train(), example.batch.conditions)


@pytest.mark.parametrize("budget", [True, 32.0, 16, 128, None])
def test_unregistered_budgets_fail_before_policy_forward(example, budget):
    calls = example.vla.language_model.model.calls
    with pytest.raises(ValueError, match="tokens_per_camera"):
        future_auxiliary_loss(example.scorer, example.student, example.batch, alpha=.5, tokens_per_camera=budget)
    with pytest.raises(ValueError, match="tokens_per_camera"):
        hard_select_future(example.scorer.eval(), example.batch.conditions, tokens_per_camera=budget)
    assert example.vla.language_model.model.calls == calls


def test_inference_cache_tensors_materialize_as_ordinary_inputs_for_backward(example):
    with torch.inference_mode():
        batch = FutureTrainingBatch(example.batch.conditions, example.batch.raw_tokens.clone(),
            example.batch.black_tokens.clone(), example.batch.input_ids.clone(), example.batch.attention_mask.clone(),
            example.batch.teacher_actions.clone(), example.batch.demonstration_actions.clone(), example.batch.future_target.clone())
    assert all(not getattr(batch, name).is_inference() for name in batch.__dataclass_fields__ if name != "conditions")
    result = future_auxiliary_loss(example.scorer, example.student, batch, alpha=.3, auxiliary_head=example.auxiliary)
    result.loss.backward()
    assert trainable_gradient(example.scorer) > 0


@pytest.mark.parametrize("name", ["raw_tokens", "teacher_actions", "demonstration_actions", "future_target"])
def test_attached_targets_or_features_are_rejected(example, name):
    with pytest.raises(ValueError, match="detached"):
        replace(example.batch, **{name: getattr(example.batch, name).clone().requires_grad_(True)})


def test_layout_target_and_raw_projector_mismatches_fail_before_VLA(example):
    calls_before = example.vla.language_model.model.calls
    with pytest.raises(ValueError, match="all512"):
        valid = example.batch.conditions.valid.clone()
        valid[:, 0] = False
        replace(example.batch, conditions=replace(example.batch.conditions, valid=valid))
    with pytest.raises(ValueError, match="original camera"):
        replace(example.batch, conditions=replace(example.batch.conditions, patch_ids=example.batch.conditions.patch_ids.flip(1)))
    with pytest.raises(ValueError, match="FP32"):
        replace(example.batch, future_target=example.batch.future_target.double())
    with pytest.raises(ValueError, match="future_target"):
        future_auxiliary_loss(example.scorer, example.student, replace(example.batch, future_target=None),
                               alpha=.5, auxiliary_head=example.auxiliary)
    with pytest.raises(ValueError, match="do not project"):
        future_auxiliary_loss(example.scorer, example.student, replace(example.batch, raw_tokens=example.batch.raw_tokens + .1), alpha=.5)
    assert example.vla.language_model.model.calls == calls_before


def test_no_grad_context_or_unfrozen_student_is_rejected(example):
    with torch.no_grad(), pytest.raises(RuntimeError, match="requires autograd"):
        future_auxiliary_loss(example.scorer, example.student, example.batch, alpha=.5)
    next(example.student.parameters()).requires_grad_(True)
    with pytest.raises(RuntimeError, match="frozen"):
        future_auxiliary_loss(example.scorer, example.student, example.batch, alpha=.5)


def test_target_representation_remains_FP32_under_autocast(example):
    expected = frozen_future_target(example.batch.conditions.visual)
    with torch.autocast("cpu", dtype=torch.bfloat16):
        actual = frozen_future_target(example.batch.conditions.visual)
    assert actual.dtype == torch.float32 and torch.equal(actual, expected)

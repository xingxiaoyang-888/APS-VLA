"""Behavior tests for the new method boundary; no pretrained VLA required."""

from dataclasses import replace

import pytest
import torch
from torch import nn

from cti_vla.labeling import DeletionTeacher, LabelProvenance, load_deletion_labels, save_deletion_labels
from cti_vla.selection import ConditionalInfluenceEstimator, ConditionalTokenBatch, staged_topk
from cti_vla.training import ConditionalTrainConfig, ConditionalTrainer, TrainingLabelScale, signed_influence_loss


def batch(n=4):
    torch.manual_seed(17)
    return ConditionalTokenBatch(
        visual=torch.randn(1, n, 4), instruction_embeddings=torch.randn(1, 3, 5),
        instruction_mask=torch.ones(1, 3, dtype=torch.bool), normalized_proprio=torch.tensor([[0.2, -0.3]]),
        camera_ids=torch.tensor([[0] * (n // 2) + [1] * (n // 2)]),
        patch_ids=torch.tensor([list(range(n // 2)) * 2]), valid=torch.ones(1, n, dtype=torch.bool),
    )


def model():
    torch.manual_seed(5)
    return ConditionalInfluenceEstimator(4, 5, 2, hidden_dim=12, num_cameras=2, patches_per_camera=3, max_instruction_tokens=4)


def provenance(**kwargs):
    values = dict(sample_ids=("sample-0",), episode_ids=("episode-0",), split="train", model_revision="weights-sha256",
                  dataset_version="libero-v1", preprocessing_version="crop-v1", packing_version="original-positions-v1",
                  condition_version="checkpoint-proprio-v1", action_version="normalized-l1-chunk-v1")
    values.update(kwargs)
    return LabelProvenance(**values)


def labeled():
    data = batch()
    data.visual[0, :, 0] = torch.tensor([1., -2., 3., -1.])
    policy = nn.Linear(1, 1).eval().requires_grad_(False)
    seen = []

    def forward(data, indices):
        assert not torch.is_grad_enabled()
        assert torch.equal(indices, indices.sort(1).values)
        seen.append(indices.clone())
        return data.visual[:, :, 0].gather(1, indices).sum(1)[:, None, None]

    teacher = DeletionTeacher(policy, forward, action_shape=(1, 1))
    retained = torch.tensor([[True, True, True, False]])
    labels = teacher.label(data, retained, torch.tensor([[0, 1]]), provenance())
    return data, policy, teacher, labels, seen


def test_teacher_uses_full_reference_and_signed_actual_deletions():
    _, _, _, labels, seen = labeled()
    torch.testing.assert_close(labels.base_error, torch.tensor([1.]))
    torch.testing.assert_close(labels.deleted_error, torch.tensor([[0., 3.]]))
    torch.testing.assert_close(labels.influence, torch.tensor([[-1., 2.]]))
    assert [x.tolist() for x in seen] == [[[0, 1, 2, 3]], [[0, 1, 2]], [[1, 2]], [[0, 2]]]
    assert labels.teacher_calls == 4
    assert not labels.influence.requires_grad


def test_full_set_reuses_reference_and_teacher_rejects_train_mode():
    data, policy, teacher, _, seen = labeled()
    seen.clear()
    labels = teacher.label(data, data.valid, torch.tensor([[0, 1]]), provenance())
    assert labels.teacher_calls == 3 and len(seen) == 3
    torch.testing.assert_close(labels.base_error, torch.zeros(1))
    policy.train()
    with pytest.raises(ValueError, match="frozen"):
        teacher.label(data, data.valid, torch.tensor([[0]]), provenance())


def test_teacher_rejects_unfrozen_policy_and_duplicate_candidates():
    data, policy, teacher, _, _ = labeled()
    policy.requires_grad_(True)
    with pytest.raises(ValueError, match="frozen"):
        teacher.label(data, data.valid, torch.tensor([[0]]), provenance())
    policy.requires_grad_(False)
    with pytest.raises(ValueError, match="duplicate"):
        teacher.label(data, data.valid, torch.tensor([[0, 0]]), provenance())


def test_cached_full_reference_reuses_one_forward_across_sets_and_detects_staleness():
    data, _, teacher, labels, seen = labeled()
    seen.clear()
    reference = teacher.reference(data, provenance())
    first = teacher.label(data, labels.retained_mask, torch.tensor([[0, 1]]), provenance(), full_reference=reference)
    second = teacher.label(data, data.valid, torch.tensor([[0, 1]]), provenance(), full_reference=reference)
    assert len(seen) == 1 + first.teacher_calls + second.teacher_calls == 6
    torch.testing.assert_close(first.influence, labels.influence)
    with pytest.raises(ValueError, match="stale"):
        teacher.label(replace(data, normalized_proprio=data.normalized_proprio + 1), data.valid, torch.tensor([[0]]), provenance(), full_reference=reference)


def test_cache_roundtrip_is_detached_and_rejects_incompatible_contents(tmp_path):
    data, _, _, labels, _ = labeled()
    path = save_deletion_labels(tmp_path / "labels.pt", labels)
    restored = load_deletion_labels(path, batch=data, retained=labels.retained_mask, provenance=provenance())
    torch.testing.assert_close(restored.influence, labels.influence)
    assert not restored.influence.requires_grad
    with pytest.raises(FileExistsError):
        save_deletion_labels(path, labels)
    with pytest.raises(ValueError, match="provenance"):
        load_deletion_labels(path, batch=data, retained=labels.retained_mask, provenance=provenance(model_revision="other"))


def test_cache_binds_exact_condition_set_and_versions():
    data, _, _, labels, _ = labeled()
    labels.validate_for(data, labels.retained_mask, provenance())
    with pytest.raises(ValueError, match="provenance"):
        labels.validate_for(data, labels.retained_mask, provenance(packing_version="different"))
    with pytest.raises(ValueError, match="retained"):
        labels.validate_for(data, data.valid, provenance())
    changed = replace(data, normalized_proprio=data.normalized_proprio + 0.01)
    with pytest.raises(ValueError, match="fingerprint"):
        labels.validate_for(changed, labels.retained_mask, provenance())
    with pytest.raises(ValueError, match="incompatible"):
        provenance(label_version="legacy-replacement")


def test_cache_detects_mutated_labels():
    _, _, _, labels, _ = labeled()
    labels.influence.add_(1.)
    with pytest.raises(ValueError, match="E\\(S-i\\)"):
        labels.__post_init__()


def test_estimator_has_signed_head_and_conditions_affect_scores():
    data, estimator = batch(), model()
    original = estimator(data, data.valid)
    for changed in (
        replace(data, instruction_embeddings=data.instruction_embeddings.flip(1)),
        replace(data, normalized_proprio=data.normalized_proprio + 1.),
        replace(data, patch_ids=data.patch_ids.flip(1)),
    ):
        assert not torch.allclose(original, estimator(changed, data.valid), atol=1e-7)
    retained = torch.tensor([[True, False, True, True]])
    assert not torch.allclose(original[retained], estimator(data, retained)[retained])
    estimator.output[-1].weight.data.zero_()
    estimator.output[-1].bias.data.fill_(-2.)
    assert (estimator(data, data.valid) == -2).all()


def test_detached_boundary_and_trainable_condition_encoders():
    data, estimator = batch(), model()
    source = data.visual.clone().requires_grad_()
    with pytest.raises(ValueError, match="detached"):
        replace(data, visual=source)
    data = replace(data, visual=source.detach())
    estimator(data, data.valid).square().mean().backward()
    assert source.grad is None
    assert estimator.language_encoder[1].weight.grad.abs().sum() > 0
    assert estimator.language_position.weight.grad.abs().sum() > 0
    assert estimator.proprio_encoder[0].weight.grad.abs().sum() > 0


def test_features_and_labels_from_inference_mode_support_scorer_backward():
    with torch.inference_mode():
        data, _, _, labels, _ = labeled()
    assert all(not getattr(data, field).is_inference() for field in data.__dataclass_fields__)
    assert not labels.candidate_indices.is_inference() and not labels.retained_mask.is_inference()
    estimator = model()
    trainer = ConditionalTrainer(estimator, torch.optim.Adam(estimator.parameters()), TrainingLabelScale.fit([labels]))
    assert trainer.train_step(data, labels, provenance=provenance())["labels"] == 2


def test_bfloat16_frozen_features_and_empty_camera_summary_are_finite():
    data = batch()
    data = replace(data, visual=data.visual.bfloat16(), instruction_embeddings=data.instruction_embeddings.bfloat16())
    retained = torch.tensor([[True, True, False, False]])
    scores = model()(data, retained)
    assert scores.dtype == torch.float32 and torch.isfinite(scores).all()


def test_staged_selection_rescores_enforces_camera_budget_and_original_order():
    class Scorer(nn.Module):
        def __init__(self):
            super().__init__()
            self.counts = []

        def forward(self, data, retained):
            self.counts.append(int(retained.sum()))
            if len(self.counts) == 1:
                return torch.tensor([[-1., -9., -2., -4., -8., -3.]])
            return torch.tensor([[-5., 0., -2., -1., 0., -3.]])

    scorer = Scorer().eval()
    data = batch(6)
    selection = staged_topk(scorer, data, ((2, 2), (1, 1)))
    assert scorer.counts == [6, 4]
    assert selection.source_indices.tolist() == [[2, 3]]
    assert [int(x.sum()) for x in selection.stage_masks] == [4, 2]
    assert not (selection.stage_masks[1] & ~selection.stage_masks[0]).any()


def test_staged_ties_are_deterministic_and_invalid_budgets_fail():
    class Ties(nn.Module):
        def forward(self, data, retained):
            return torch.zeros_like(data.valid, dtype=torch.float32)

    scorer, data = Ties().eval(), batch(6)
    assert staged_topk(scorer, data, ((1, 1),)).source_indices.tolist() == [[0, 3]]
    with pytest.raises(ValueError, match="exceeds"):
        staged_topk(scorer, data, ((1, 1), (2, 1)))


def test_training_scale_is_global_signed_and_excludes_evaluation():
    _, _, _, labels, _ = labeled()
    scale = TrainingLabelScale.fit([labels])
    assert scale.value == pytest.approx((5 / 2) ** 0.5)
    assert scale.label_count == 2
    validation = replace(labels, provenance=provenance(split="validation", episode_ids=("validation-episode",)))
    with pytest.raises(ValueError, match="training episodes only"):
        TrainingLabelScale.fit([validation])
    scale.validate(validation.provenance)
    with pytest.raises(ValueError, match="overlaps"):
        scale.validate(provenance(split="test"))


def test_huber_accepts_signed_values_and_ranking_never_crosses_sets():
    predicted = torch.tensor([[-1.], [2.]], requires_grad=True)
    target = predicted.detach().clone()
    loss, regression, ranking = signed_influence_loss(predicted, target, ConditionalTrainConfig(ranking_weight=1))
    assert loss.item() == regression.item() == ranking.item() == 0
    loss.backward()


def test_train_step_updates_only_scorer_without_teacher_calls():
    data, policy, _, labels, seen = labeled()
    estimator = model()
    before = estimator.output[-1].weight.detach().clone()
    optimizer = torch.optim.Adam(estimator.parameters(), lr=1e-3)
    trainer = ConditionalTrainer(estimator, optimizer, TrainingLabelScale.fit([labels]))
    calls_before = len(seen)
    metrics = trainer.train_step(data, labels, provenance=provenance())
    assert metrics["labels"] == 2 and torch.isfinite(torch.tensor(metrics["loss"]))
    assert not torch.equal(before, estimator.output[-1].weight)
    assert len(seen) == calls_before and all(p.grad is None for p in policy.parameters())
    with pytest.raises(ValueError, match="validation/test"):
        trainer.train_step(data, labels, provenance=provenance(split="test"))


def test_optimizer_rejects_extra_policy_parameters():
    _, policy, _, labels, _ = labeled()
    estimator = model()
    optimizer = torch.optim.Adam([*estimator.parameters(), *policy.parameters()], lr=1e-3)
    with pytest.raises(ValueError, match="exactly"):
        ConditionalTrainer(estimator, optimizer, TrainingLabelScale.fit([labels]))

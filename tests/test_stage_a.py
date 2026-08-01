import pytest
import torch

from diwa.data.contracts import TokenBatch
from diwa.losses.influence_loss import conditional_influence_loss
from diwa.models.influence.die import DecisionInfluenceEstimator
from diwa.training.stage_a import StageABatch, StageATrainer, freeze_teacher_modules


def make_stage_batch():
    torch.manual_seed(3)
    token_batch = TokenBatch(
        z=torch.randn(2, 6, 8),
        token_type=torch.tensor([[0, 0, 1, 1, 2, 2]] * 2),
        frame_id=torch.tensor([[0, 0, 1, 1, 2, 2]] * 2),
        camera_id=torch.tensor([[0, 1, 0, 1, 0, 1]] * 2),
        valid=torch.ones(2, 6, dtype=torch.bool),
        query=torch.randn(2, 4),
        proprio=torch.randn(2, 3),
    )
    return StageABatch(
        token_batch=token_batch,
        intervened_mask=torch.zeros(2, 6, dtype=torch.bool),
        source_indices=torch.tensor([[0, 2, 4], [1, 3, 5]], dtype=torch.long),
        target_influence=torch.tensor([[0.1, 0.5, 0.2], [0.3, 0.05, 0.8]]),
        valid_candidates=torch.ones(2, 3, dtype=torch.bool),
    )


def make_estimator():
    return DecisionInfluenceEstimator(
        token_dim=8,
        query_dim=4,
        hidden_dim=16,
        num_token_types=3,
        num_frames=3,
        num_cameras=2,
        metadata_dim=4,
    )


def test_stage_a_cpu_dry_run_updates_only_die_parameters():
    estimator = make_estimator()
    before = [parameter.detach().clone() for parameter in estimator.parameters()]
    trainer = StageATrainer(estimator, torch.optim.AdamW(estimator.parameters(), lr=1e-3))
    output = trainer.train_step(make_stage_batch())
    assert output.loss > 0
    assert output.valid_candidates == 6
    assert output.valid_pairs > 0
    assert any(not torch.equal(old, new) for old, new in zip(before, estimator.parameters()))


def test_stage_a_optimizer_rejects_non_die_parameters():
    estimator = make_estimator()
    foreign = torch.nn.Linear(2, 2)
    optimizer = torch.optim.AdamW(list(estimator.parameters()) + list(foreign.parameters()))
    with pytest.raises(ValueError, match="exactly"):
        StageATrainer(estimator, optimizer)


def test_freeze_teacher_modules_forces_eval_and_no_grad():
    teacher = torch.nn.Sequential(torch.nn.Linear(4, 4), torch.nn.Dropout(0.5)).train()
    freeze_teacher_modules([teacher])
    assert not teacher.training
    assert not any(parameter.requires_grad for parameter in teacher.parameters())


def test_influence_loss_ignores_ties_for_ranking():
    predicted = torch.tensor([[0.2, 0.3]], requires_grad=True)
    target = torch.tensor([[0.5, 0.5]])
    output = conditional_influence_loss(predicted, target, torch.ones(1, 2, dtype=torch.bool))
    assert output.valid_pairs.item() == 0
    output.loss.backward()
    assert predicted.grad is not None


def test_stage_a_rejects_upstream_activation_graph():
    batch = make_stage_batch()
    batch.token_batch.z.requires_grad_(True)
    with pytest.raises(ValueError, match="detached"):
        StageABatch(
            token_batch=batch.token_batch,
            intervened_mask=batch.intervened_mask,
            source_indices=batch.source_indices,
            target_influence=batch.target_influence,
            valid_candidates=batch.valid_candidates,
        )

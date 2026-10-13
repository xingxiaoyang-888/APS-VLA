"""Independent multi-row, condition, and gradient checks for CTI supervision."""

from dataclasses import replace

import pytest
import torch
from torch import nn

from cti_vla.labeling import DeletionTeacher, LabelProvenance
from cti_vla.selection import ConditionalInfluenceEstimator, ConditionalTokenBatch


def inputs():
    generator = torch.Generator().manual_seed(198)
    return ConditionalTokenBatch(
        torch.randn((2, 6, 4), generator=generator),
        torch.randn((2, 4, 5), generator=generator),
        torch.tensor([[True, True, False, False], [True, True, True, False]]),
        torch.tensor([[0.3, -0.2], [0.1, 0.4]]),
        torch.tensor([[0, 0, 0, 1, 1, 1]] * 2),
        torch.tensor([[0, 1, 2, 0, 1, 2]] * 2),
        torch.ones((2, 6), dtype=torch.bool),
    )


def provenance():
    return LabelProvenance(("sample-a", "sample-b"), ("episode-a", "episode-b"),
                           "train", "model-v1", "data-v1", "preprocess-v1",
                           "packing-v1", "condition-v1", "action-v1")


def estimator():
    torch.manual_seed(103)
    return ConditionalInfluenceEstimator(4, 5, 2, hidden_dim=16, num_cameras=2,
                                         patches_per_camera=3, max_instruction_tokens=4)


def test_two_row_teacher_uses_each_rows_own_set_and_full_reference():
    batch = inputs()
    policy = nn.Linear(1, 1).eval().requires_grad_(False)

    def action(batch, indices):
        selected = batch.visual.gather(1, indices[..., None].expand(-1, -1, 4))
        # Nonlinear set interaction gives a separate oracle, not LOO constants.
        pooled = selected.sum(1)
        return (pooled[:, :2].square() + batch.normalized_proprio).unsqueeze(1)

    teacher = DeletionTeacher(policy, action, action_shape=(1, 2))
    retained = torch.tensor([[True, False, True, True, False, True],
                             [False, True, True, True, True, False]])
    candidates = torch.tensor([[0, 5], [1, 4]])
    labels = teacher.label(batch, retained, candidates, provenance())
    full = action(batch, torch.arange(6).repeat(2, 1))
    expected = []
    for row in range(2):
        values = batch.visual[row]
        baseline = (values[retained[row]].sum(0)[:2].square() + batch.normalized_proprio[row])
        base_error = (baseline - full[row, 0]).abs().mean()
        marginal = []
        for candidate in candidates[row]:
            reduced = retained[row].clone()
            reduced[candidate] = False
            changed = values[reduced].sum(0)[:2].square() + batch.normalized_proprio[row]
            marginal.append((changed - full[row, 0]).abs().mean() - base_error)
        expected.append(torch.stack(marginal))
    torch.testing.assert_close(labels.influence, torch.stack(expected))
    swapped = replace(batch, normalized_proprio=batch.normalized_proprio.flip(0))
    with pytest.raises(ValueError, match="fingerprint"):
        labels.validate_for(swapped, retained, provenance())


def test_empty_camera_backward_has_no_nonfinite_gradients():
    batch, model = inputs(), estimator()
    retained = torch.tensor([[True, True, True, False, False, False],
                             [False, False, False, True, True, True]])
    model(batch, retained).square().mean().backward()
    gradients = [parameter.grad for parameter in model.parameters() if parameter.grad is not None]
    assert gradients and all(torch.isfinite(gradient).all() for gradient in gradients)


def test_condition_changes_affect_relative_scores_not_just_shared_offset():
    batch, model = inputs(), estimator()
    baseline = model(batch, batch.valid)
    alternatives = (
        replace(batch, instruction_embeddings=batch.instruction_embeddings.flip(1)),
        replace(batch, normalized_proprio=-batch.normalized_proprio * 3),
    )
    for alternative in alternatives:
        change = model(alternative, alternative.valid) - baseline
        centered_change = change - change.mean(1, keepdim=True)
        assert centered_change.abs().max() > 1e-5


def test_padding_and_discarded_content_do_not_enter_retained_set_summary():
    batch, model = inputs(), estimator()
    retained = torch.tensor([[True, False, True, True, False, True],
                             [False, True, True, True, True, False]])
    baseline = model(batch, retained)
    visual = batch.visual.clone()
    visual[~retained] += 20
    words = batch.instruction_embeddings.clone()
    words[~batch.instruction_mask] += 20
    changed = replace(batch, visual=visual, instruction_embeddings=words)
    torch.testing.assert_close(model(changed, retained)[retained], baseline[retained])

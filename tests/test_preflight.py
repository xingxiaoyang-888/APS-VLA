import pytest
import torch

from diwa.data.contracts import TokenBatch
from diwa.evaluation.preflight import compare_action_outputs, content_permutation_audit, measure_forward_latency
from diwa.models.influence.die import DecisionInfluenceEstimator


def make_batch():
    return TokenBatch(
        z=torch.arange(2 * 4 * 6, dtype=torch.float32).reshape(2, 4, 6) + 1,
        token_type=torch.tensor([[0, 0, 1, 1]] * 2),
        frame_id=torch.tensor([[0, 1, 0, 1]] * 2),
        camera_id=torch.tensor([[0, 0, 1, 1]] * 2),
        valid=torch.ones(2, 4, dtype=torch.bool),
        query=torch.ones(2, 3),
        proprio=torch.ones(2, 2),
    )


def test_equivalence_report_uses_fp32_absolute_error():
    reference = torch.zeros(2, 8, 7, dtype=torch.bfloat16)
    candidate = reference.clone()
    candidate[0, 0, 0] = 0.001
    report = compare_action_outputs(reference, candidate, atol=0.002)
    assert report.passed
    assert report.max_abs_error > 0


def test_content_permutation_audit_requires_true_permutation():
    batch = make_batch()
    estimator = DecisionInfluenceEstimator(6, 3, hidden_dim=8, num_token_types=2, num_frames=2, num_cameras=2)
    permutation = torch.tensor([[3, 2, 1, 0], [1, 0, 3, 2]])
    metrics = content_permutation_audit(estimator, batch, torch.zeros_like(batch.valid), permutation)
    assert metrics["content_permutation_mean_abs_change"] >= 0
    with pytest.raises(ValueError, match="exactly once"):
        content_permutation_audit(estimator, batch, torch.zeros_like(batch.valid), torch.zeros(2, 4, dtype=torch.long))
    with pytest.raises(ValueError, match="preserve"):
        padded = make_batch()
        padded.valid[:, -1] = False
        content_permutation_audit(
            estimator,
            padded,
            torch.zeros_like(padded.valid),
            torch.tensor([[3, 0, 1, 2], [3, 0, 1, 2]]),
        )


def test_latency_helper_restores_module_mode():
    module = torch.nn.Linear(4, 4).train()
    inputs = torch.ones(2, 4)
    report = measure_forward_latency(lambda: module(inputs), [module], warmup=1, repetitions=3)
    assert report.repetitions == 3
    assert report.median_ms >= 0
    assert module.training


def test_latency_helper_releases_warmup_output_before_measurement():
    module = torch.nn.Linear(4, 4).eval()
    report = measure_forward_latency(lambda: module(torch.ones(1, 4)), [module], warmup=2, repetitions=2)
    assert report.repetitions == 2

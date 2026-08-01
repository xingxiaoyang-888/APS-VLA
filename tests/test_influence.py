import pytest
import torch
from torch import nn

from diwa.data.contracts import TokenBatch
from diwa.data.interventions import MatchedMeanBaseline
from diwa.losses.action_distance import normalized_action_chunk_distance
from diwa.models.influence.die import DecisionInfluenceEstimator
from diwa.models.influence.teacher import CounterfactualTeacher


def make_batch(batch=2, tokens=5, hidden=6, query_dim=4):
    z = torch.arange(batch * tokens * hidden, dtype=torch.float32).reshape(batch, tokens, hidden) / 10 + 1
    return TokenBatch(
        z=z,
        token_type=torch.tensor([[0, 1, 1, 2, 2]] * batch),
        frame_id=torch.tensor([[0, 0, 1, 1, 2]] * batch),
        camera_id=torch.tensor([[0, 0, 0, 1, 1]] * batch),
        valid=torch.ones(batch, tokens, dtype=torch.bool),
        query=torch.ones(batch, query_dim),
        proprio=torch.ones(batch, 3),
    )


class TinyTokenPolicy(nn.Module):
    def __init__(self):
        super().__init__()
        self.forward_calls = 0
        self.grad_modes = []
        self.live_output_sizes = []

    def forward_from_tokens(self, tokens, proprio):
        self.forward_calls += 1
        self.grad_modes.append(torch.is_grad_enabled())
        # [B, 2, 2], deterministically dependent on token content.
        pooled = tokens.float().sum(dim=(1, 2)) + proprio.float().sum(dim=1)
        output = pooled[:, None, None].expand(-1, 2, 2).clone()
        self.live_output_sizes.append(output.numel())
        return output


class KwargTokenPolicy(TinyTokenPolicy):
    def __init__(self):
        super().__init__()
        self.received_input_ids = []

    def forward_from_tokens(self, tokens, proprio, **kwargs):
        self.received_input_ids.append(kwargs["input_ids"])
        return super().forward_from_tokens(tokens, proprio)


def test_action_chunk_distance_uses_fp32_and_per_sample_reduction():
    first = torch.zeros(2, 2, 2, dtype=torch.bfloat16)
    second = torch.tensor([[[1.0, 0.0], [0.0, 0.0]], [[2.0, 2.0], [2.0, 2.0]]], dtype=torch.bfloat16)
    distance = normalized_action_chunk_distance(first, second, huber_delta=1.0)
    assert distance.dtype == torch.float32
    assert torch.allclose(distance, torch.tensor([0.125, 1.5]))


def test_action_chunk_distance_rejects_nan_and_shape_mismatch():
    with pytest.raises(ValueError, match="identical"):
        normalized_action_chunk_distance(torch.ones(1, 2, 2), torch.ones(1, 2, 3))
    invalid = torch.ones(1, 2, 2)
    invalid[0, 0, 0] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        normalized_action_chunk_distance(invalid, torch.ones_like(invalid))


def test_die_outputs_positive_scores_and_masks_removed_tokens():
    torch.manual_seed(0)
    batch = make_batch()
    estimator = DecisionInfluenceEstimator(
        token_dim=6,
        query_dim=4,
        hidden_dim=16,
        num_token_types=3,
        num_frames=3,
        num_cameras=2,
        metadata_dim=4,
    )
    intervened = torch.zeros_like(batch.valid)
    intervened[:, 1] = True
    scores = estimator(batch, intervened)
    assert scores.shape == batch.valid.shape
    assert torch.all(scores[:, 1] == 0)
    assert torch.all(scores[:, [0, 2, 3, 4]] > 0)
    scores.sum().backward()
    assert any(parameter.grad is not None for parameter in estimator.parameters())


def test_die_rejects_all_tokens_intervened_and_bad_metadata():
    batch = make_batch()
    estimator = DecisionInfluenceEstimator(6, 4, hidden_dim=8, num_token_types=3, num_frames=3, num_cameras=2)
    with pytest.raises(ValueError, match="surviving"):
        estimator(batch, torch.ones_like(batch.valid))
    batch.camera_id[0, 0] = 2
    with pytest.raises(ValueError, match="camera_id"):
        estimator(batch, torch.zeros_like(batch.valid))


def test_die_allows_negative_metadata_only_on_padding():
    batch = make_batch()
    batch.valid[:, -1] = False
    batch.token_type[:, -1] = -1
    batch.frame_id[:, -1] = -1
    batch.camera_id[:, -1] = -1
    estimator = DecisionInfluenceEstimator(6, 4, hidden_dim=8, num_token_types=3, num_frames=3, num_cameras=2)
    scores = estimator(batch, torch.zeros_like(batch.valid))
    assert torch.all(scores[:, -1] == 0)


def test_teacher_runs_two_sequential_graph_free_forwards():
    batch = make_batch()
    baseline = MatchedMeanBaseline()(batch.z, batch.token_type, batch.frame_id, batch.camera_id)
    policy = TinyTokenPolicy().eval()
    teacher = CounterfactualTeacher(policy, action_chunk_shape=(2, 2))
    base_mask = torch.zeros_like(batch.valid)
    candidate_mask = torch.zeros_like(batch.valid)
    candidate_mask[:, 0] = True
    targets = teacher.estimate(batch, baseline, base_mask, candidate_mask)
    assert policy.forward_calls == 2
    assert policy.grad_modes == [False, False]
    assert targets.influence.shape == (batch.batch_size,)
    assert not targets.influence.requires_grad
    assert torch.all(targets.influence > 0)
    assert torch.equal(targets.candidate_count, torch.ones(batch.batch_size, dtype=torch.long))
    assert torch.equal(targets.base_intervened_count, torch.zeros(batch.batch_size, dtype=torch.long))


def test_teacher_requires_eval_disjoint_masks_and_survivor():
    batch = make_batch()
    baseline = MatchedMeanBaseline()(batch.z, batch.token_type, batch.frame_id, batch.camera_id)
    policy = TinyTokenPolicy()
    teacher = CounterfactualTeacher(policy)
    empty = torch.zeros_like(batch.valid)
    candidate = torch.zeros_like(batch.valid)
    candidate[:, 0] = True
    with pytest.raises(RuntimeError, match="eval"):
        teacher.estimate(batch, baseline, empty, candidate)

    policy.eval()
    with pytest.raises(ValueError, match="disjoint"):
        teacher.estimate(batch, baseline, candidate, candidate)
    all_but_one = torch.ones_like(batch.valid)
    all_but_one[:, 0] = False
    with pytest.raises(ValueError, match="untouched"):
        teacher.estimate(batch, baseline, all_but_one, candidate)


def test_teacher_rejects_non_finite_policy_output():
    class BadPolicy(TinyTokenPolicy):
        def forward_from_tokens(self, tokens, proprio):
            output = super().forward_from_tokens(tokens, proprio)
            output[0, 0, 0] = float("inf")
            return output

    batch = make_batch()
    baseline = MatchedMeanBaseline()(batch.z, batch.token_type, batch.frame_id, batch.camera_id)
    candidate = torch.zeros_like(batch.valid)
    candidate[:, 0] = True
    with pytest.raises(ValueError, match="NaN/Inf"):
        CounterfactualTeacher(BadPolicy().eval(), action_chunk_shape=(2, 2)).estimate(
            batch, baseline, torch.zeros_like(batch.valid), candidate
        )


def test_teacher_passes_shared_prompt_inputs_to_both_sequential_branches():
    batch = make_batch()
    baseline = MatchedMeanBaseline()(batch.z, batch.token_type, batch.frame_id, batch.camera_id)
    candidate = torch.zeros_like(batch.valid)
    candidate[:, 0] = True
    input_ids = torch.ones(batch.batch_size, 3, dtype=torch.long)
    policy = KwargTokenPolicy().eval()
    CounterfactualTeacher(policy, action_chunk_shape=(2, 2)).estimate(
        batch,
        baseline,
        torch.zeros_like(batch.valid),
        candidate,
        policy_inputs={"input_ids": input_ids},
    )
    assert policy.received_input_ids == [input_ids, input_ids]


def test_teacher_rejects_wrong_action_chunk_shape():
    batch = make_batch()
    baseline = MatchedMeanBaseline()(batch.z, batch.token_type, batch.frame_id, batch.camera_id)
    candidate = torch.zeros_like(batch.valid)
    candidate[:, 0] = True
    with pytest.raises(ValueError, match="invalid batch or dtype"):
        CounterfactualTeacher(TinyTokenPolicy().eval()).estimate(
            batch, baseline, torch.zeros_like(batch.valid), candidate
        )

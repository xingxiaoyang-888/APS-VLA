import pytest
import torch

from diwa.data.contracts import TokenBatch
from diwa.data.interventions import MatchedMeanBaseline
from diwa.models.influence.sampling import TeacherCandidateSampler, compute_coverage_audit
from diwa.models.influence.teacher import CounterfactualTeacher


class CountingPolicy(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.calls = 0

    def forward_from_tokens(self, tokens, proprio, **kwargs):
        self.calls += 1
        pooled = tokens.sum(dim=(1, 2)) + proprio.sum(dim=1)
        return pooled[:, None, None].expand(-1, 2, 2).clone()


def make_batch():
    return TokenBatch(
        z=torch.ones(2, 10, 4),
        token_type=torch.tensor([[0, 0, 0, 1, 1, 1, 2, 2, 2, 2]] * 2),
        frame_id=torch.tensor([[0, 0, 1, 0, 1, 1, 0, 1, 2, 2]] * 2),
        camera_id=torch.tensor([[0, 1, 0, 0, 0, 1, 1, 0, 0, 1]] * 2),
        valid=torch.ones(2, 10, dtype=torch.bool),
        query=torch.ones(2, 3),
        proprio=torch.ones(2, 2),
    )


def test_sampler_emits_unique_single_token_candidates_by_role():
    batch = make_batch()
    scores = torch.arange(20, dtype=torch.float32).reshape(2, 10)
    result = TeacherCandidateSampler().sample(
        batch, scores, torch.zeros_like(batch.valid), generator=torch.Generator().manual_seed(7)
    )
    assert result.masks.shape == (2, 8, 10)
    assert torch.all(result.masks.sum(dim=-1) == 1)
    assert torch.equal(result.source_indices[:, :4], torch.tensor([[9, 8, 7, 6], [9, 8, 7, 6]]))
    assert torch.all(result.source_kind[:, :4] == TeacherCandidateSampler.TOP)
    for row in result.source_indices:
        assert len(row.unique()) == 8


def test_sampler_never_selects_intervened_or_invalid_tokens():
    batch = make_batch()
    batch.valid[:, -1] = False
    intervened = torch.zeros_like(batch.valid)
    intervened[:, 8] = True
    scores = torch.arange(20, dtype=torch.float32).reshape(2, 10)
    scores[:, 8:] = 0
    result = TeacherCandidateSampler(num_top=3, num_stratified=2, num_hard_negative=2).sample(
        batch, scores, intervened
    )
    assert not bool((result.masks & intervened[:, None]).any())
    assert not bool((result.masks & ~batch.valid[:, None]).any())


def test_sampler_rejects_nonzero_score_on_ineligible_token():
    batch = make_batch()
    intervened = torch.zeros_like(batch.valid)
    intervened[:, 0] = True
    with pytest.raises(ValueError, match="zero DIE"):
        TeacherCandidateSampler().sample(batch, torch.ones(2, 10), intervened)


def test_candidate_set_rejects_mask_index_mismatch():
    batch = make_batch()
    scores = torch.arange(20, dtype=torch.float32).reshape(2, 10)
    result = TeacherCandidateSampler().sample(batch, scores, torch.zeros_like(batch.valid))
    result.source_indices[0, 0] = 0
    with pytest.raises(ValueError, match="mask and source_indices|candidate slots"):
        type(result)(
            result.masks,
            result.source_indices,
            result.source_kind,
            result.valid_candidates,
            result.eligible_count,
        )


def test_audit_uses_score_quantiles_and_computes_coverage():
    batch = make_batch()
    scores = torch.arange(20, dtype=torch.float32).reshape(2, 10)
    intervened = torch.zeros_like(batch.valid)
    sampler = TeacherCandidateSampler(num_top=2, num_stratified=1, num_hard_negative=1, audit_size=6)
    regular = sampler.sample(batch, scores, intervened)
    audit = sampler.audit_candidates(batch, scores, intervened, regular)
    metrics = compute_coverage_audit(regular, audit, audit.source_indices.clamp_min(0).float())
    assert torch.all(metrics.top1_covered)
    assert torch.all(metrics.oracle_regret == 0)
    assert torch.equal(metrics.evaluated_count, torch.full((2,), 6, dtype=torch.long))
    assert metrics.mean_metrics()["candidate_top1_coverage"] == 1.0


def test_candidate_teacher_reuses_one_base_forward_and_stays_graph_free():
    batch = make_batch()
    scores = torch.arange(20, dtype=torch.float32).reshape(2, 10)
    sampler = TeacherCandidateSampler(num_top=2, num_stratified=1, num_hard_negative=1)
    candidates = sampler.sample(batch, scores, torch.zeros_like(batch.valid))
    policy = CountingPolicy().eval()
    targets = CounterfactualTeacher(policy, action_chunk_shape=(2, 2)).estimate_candidates(
        batch,
        MatchedMeanBaseline()(batch.z, batch.token_type, batch.frame_id, batch.camera_id),
        torch.zeros_like(batch.valid),
        candidates,
    )
    assert policy.calls == 1 + sampler.num_candidates
    assert targets.influence.shape == (2, sampler.num_candidates)
    assert not targets.influence.requires_grad

import pytest
import torch

from diwa.data.contracts import TokenBatch
from diwa.data.teacher_cache import TeacherCacheShard
from diwa.evaluation.gates import check_expansion_gates
from diwa.training.pipeline import stage_a_batch_from_cache


def make_token_batch():
    return TokenBatch(
        z=torch.ones(2, 5, 4),
        token_type=torch.zeros(2, 5, dtype=torch.long),
        frame_id=torch.zeros(2, 5, dtype=torch.long),
        camera_id=torch.zeros(2, 5, dtype=torch.long),
        valid=torch.ones(2, 5, dtype=torch.bool),
        query=torch.ones(2, 3),
        proprio=torch.ones(2, 2),
    )


def make_cache():
    return TeacherCacheShard(
        sample_id=torch.tensor([20, 10]),
        source_indices=torch.tensor([[1, 2], [3, 4]]),
        source_kind=torch.zeros(2, 2, dtype=torch.long),
        influence=torch.tensor([[0.1, 0.2], [0.3, 0.4]]),
        valid_candidates=torch.ones(2, 2, dtype=torch.bool),
        base_intervened_count=torch.zeros(2, dtype=torch.long),
        eligible_count=torch.full((2,), 5, dtype=torch.long),
    )


def test_cache_rows_align_by_sample_id_not_file_order():
    result = stage_a_batch_from_cache(
        make_token_batch(), torch.zeros(2, 5, dtype=torch.bool), make_cache(), torch.tensor([10, 20])
    )
    assert torch.equal(result.source_indices, torch.tensor([[3, 4], [1, 2]]))


def test_expansion_gate_blocks_missing_or_failed_audits():
    passing = {
        "candidate_top1_coverage": 0.9,
        "candidate_oracle_regret": 0.01,
        "full_retention_max_abs_error": 0.001,
        "packed_speedup": 1.2,
        "content_permutation_mean_abs_change": 0.01,
    }
    check_expansion_gates(passing)
    failing = dict(passing, packed_speedup=1.0)
    with pytest.raises(RuntimeError, match="packed_speedup"):
        check_expansion_gates(failing)
    with pytest.raises(ValueError, match="missing"):
        check_expansion_gates({})

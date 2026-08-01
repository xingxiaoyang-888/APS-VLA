import json

import pytest
import torch

from diwa.data.teacher_cache import (
    MAX_SAMPLES_PER_SHARD,
    TeacherCacheManifest,
    TeacherCacheShard,
    load_teacher_cache_shard,
    save_teacher_cache_shard,
)


def make_manifest(policy="policy-sha"):
    return TeacherCacheManifest(
        data_signature="libero-spatial-v1+processor-sha",
        policy_signature=policy,
        baseline_signature="matched-mean-v1",
        action_chunk_size=8,
        action_dim=7,
    )


def make_shard():
    return TeacherCacheShard(
        sample_id=torch.tensor([11, 12], dtype=torch.long),
        source_indices=torch.tensor([[1, 3], [2, 4]], dtype=torch.long),
        source_kind=torch.tensor([[0, 2], [0, 1]], dtype=torch.long),
        influence=torch.tensor([[0.1, 0.2], [0.3, 0.4]], dtype=torch.float32),
        valid_candidates=torch.ones(2, 2, dtype=torch.bool),
        base_intervened_count=torch.tensor([0, 1], dtype=torch.long),
        eligible_count=torch.tensor([10, 9], dtype=torch.long),
    )


def test_cache_roundtrip_requires_exact_manifest(tmp_path):
    path = tmp_path / "teacher-00000.pt"
    shard = make_shard()
    save_teacher_cache_shard(path, shard, make_manifest())
    loaded = load_teacher_cache_shard(path, make_manifest())
    assert torch.equal(loaded.influence, shard.influence)
    assert loaded.estimated_bytes == shard.estimated_bytes
    assert json.loads(path.with_suffix(".json").read_text())["schema_version"] == 1
    with pytest.raises(ValueError, match="manifest mismatch"):
        load_teacher_cache_shard(path, make_manifest(policy="different-policy"))


def test_cache_rejects_activation_like_or_invalid_tensors():
    with pytest.raises(ValueError, match="fp32"):
        TeacherCacheShard(
            sample_id=torch.tensor([1]),
            source_indices=torch.tensor([[0]]),
            source_kind=torch.tensor([[0]]),
            influence=torch.ones(1, 1, dtype=torch.bfloat16),
            valid_candidates=torch.ones(1, 1, dtype=torch.bool),
            base_intervened_count=torch.zeros(1, dtype=torch.long),
            eligible_count=torch.ones(1, dtype=torch.long),
        )
    with pytest.raises(ValueError, match="shard samples"):
        TeacherCacheShard(
            sample_id=torch.arange(MAX_SAMPLES_PER_SHARD + 1),
            source_indices=torch.zeros(MAX_SAMPLES_PER_SHARD + 1, 1, dtype=torch.long),
            source_kind=torch.zeros(MAX_SAMPLES_PER_SHARD + 1, 1, dtype=torch.long),
            influence=torch.zeros(MAX_SAMPLES_PER_SHARD + 1, 1),
            valid_candidates=torch.ones(MAX_SAMPLES_PER_SHARD + 1, 1, dtype=torch.bool),
            base_intervened_count=torch.zeros(MAX_SAMPLES_PER_SHARD + 1, dtype=torch.long),
            eligible_count=torch.ones(MAX_SAMPLES_PER_SHARD + 1, dtype=torch.long),
        )


def test_cache_refuses_stale_temp_file(tmp_path):
    path = tmp_path / "teacher.pt"
    path.with_suffix(".pt.tmp").write_bytes(b"incomplete")
    with pytest.raises(FileExistsError, match="temporary"):
        save_teacher_cache_shard(path, make_shard(), make_manifest())

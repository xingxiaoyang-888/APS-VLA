"""Offline teacher labeling and Stage-A cache consumption boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

import torch

from diwa.data.contracts import TokenBatch
from diwa.data.interventions import MatchedMeanBaseline
from diwa.data.teacher_cache import TeacherCacheShard
from diwa.models.influence.die import DecisionInfluenceEstimator
from diwa.models.influence.sampling import CandidateSet, TeacherCandidateSampler
from diwa.models.influence.teacher import CounterfactualTeacher
from diwa.training.stage_a import StageABatch


@dataclass(frozen=True)
class LabelBatchOutput:
    shard: TeacherCacheShard
    die_scores: torch.Tensor
    candidates: CandidateSet


@torch.no_grad()
def label_teacher_batch(
    sample_id: torch.Tensor,
    batch: TokenBatch,
    estimator: DecisionInfluenceEstimator,
    teacher: CounterfactualTeacher,
    sampler: TeacherCandidateSampler,
    intervened_mask: torch.Tensor,
    *,
    baseline: Optional[torch.Tensor] = None,
    policy_inputs: Optional[Mapping[str, torch.Tensor]] = None,
    generator: Optional[torch.Generator] = None,
) -> LabelBatchOutput:
    """Generate one activation-free target batch using sequential 7B forwards."""

    if estimator.training:
        raise RuntimeError("teacher labeling requires estimator.eval() for deterministic candidate selection")
    if sample_id.shape != (batch.batch_size,) or sample_id.dtype != torch.long:
        raise ValueError("sample_id must be long [B]")
    if sample_id.device != batch.z.device:
        raise ValueError("sample_id and TokenBatch must share device during labeling")
    if baseline is None:
        baseline = MatchedMeanBaseline()(
            batch.z, batch.token_type, batch.frame_id, batch.camera_id, batch.valid
        )
    scores = estimator(batch, intervened_mask).detach()
    candidates = sampler.sample(
        batch, scores, intervened_mask, generator=generator
    )
    targets = teacher.estimate_candidates(
        batch,
        baseline,
        intervened_mask,
        candidates,
        policy_inputs=policy_inputs,
    )
    shard = TeacherCacheShard.from_targets(sample_id, candidates, targets)
    return LabelBatchOutput(shard=shard, die_scores=scores, candidates=candidates)


def stage_a_batch_from_cache(
    token_batch: TokenBatch,
    intervened_mask: torch.Tensor,
    cache: TeacherCacheShard,
    sample_id: torch.Tensor,
) -> StageABatch:
    """Align cache rows to the current batch without putting a whole shard on GPU."""

    if sample_id.shape != (token_batch.batch_size,) or sample_id.dtype != torch.long:
        raise ValueError("sample_id must be long [B]")
    if sample_id.unique().numel() != sample_id.numel():
        raise ValueError("sample_id values must be unique within the training batch")
    cache_lookup = {int(value): index for index, value in enumerate(cache.sample_id.tolist())}
    try:
        rows = torch.tensor(
            [cache_lookup[int(value)] for value in sample_id.detach().cpu().tolist()],
            dtype=torch.long,
        )
    except KeyError as error:
        raise KeyError(f"sample id {error.args[0]} is missing from teacher cache") from error
    device = token_batch.z.device
    selected_indices = cache.source_indices.index_select(0, rows)
    if bool((selected_indices[cache.valid_candidates.index_select(0, rows)] >= token_batch.num_tokens).any()):
        raise ValueError("cache source index exceeds current TokenBatch token count")
    return StageABatch(
        token_batch=token_batch,
        intervened_mask=intervened_mask,
        source_indices=cache.source_indices.index_select(0, rows).to(device=device, non_blocking=True),
        target_influence=cache.influence.index_select(0, rows).to(device=device, non_blocking=True),
        valid_candidates=cache.valid_candidates.index_select(0, rows).to(device=device, non_blocking=True),
    )


__all__ = ["LabelBatchOutput", "label_teacher_batch", "stage_a_batch_from_cache"]

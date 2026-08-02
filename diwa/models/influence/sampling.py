"""Auditable teacher-candidate sampling for conditional token influence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch

from diwa.data.contracts import TokenBatch


@dataclass(frozen=True)
class CandidateSet:
    masks: torch.Tensor
    source_indices: torch.Tensor
    source_kind: torch.Tensor
    valid_candidates: torch.Tensor
    eligible_count: torch.Tensor

    def __post_init__(self) -> None:
        tensor_values = (
            self.masks,
            self.source_indices,
            self.source_kind,
            self.valid_candidates,
            self.eligible_count,
        )
        if any(not isinstance(value, torch.Tensor) for value in tensor_values):
            raise TypeError("all CandidateSet fields must be tensors")
        if self.masks.ndim != 3 or self.masks.dtype != torch.bool:
            raise ValueError("masks must be bool [B, C, N]")
        batch, candidates, _ = self.masks.shape
        if self.source_indices.shape != (batch, candidates) or self.source_indices.dtype != torch.long:
            raise ValueError("source_indices must be long [B, C]")
        if self.source_kind.shape != (batch, candidates) or self.source_kind.dtype != torch.long:
            raise ValueError("source_kind must be long [B, C]")
        if self.valid_candidates.shape != (batch, candidates) or self.valid_candidates.dtype != torch.bool:
            raise ValueError("valid_candidates must be bool [B, C]")
        if self.eligible_count.shape != (batch,) or self.eligible_count.dtype != torch.long:
            raise ValueError("eligible_count must be long [B]")
        if bool((self.masks.sum(dim=-1)[self.valid_candidates] != 1).any()):
            raise ValueError("each valid candidate must select exactly one token")
        if bool(self.masks[~self.valid_candidates].any()):
            raise ValueError("invalid candidate slots must have empty masks")
        if bool((self.source_indices[self.valid_candidates] < 0).any()):
            raise ValueError("valid candidates need non-negative source indices")
        if bool((self.source_indices[~self.valid_candidates] != -1).any()):
            raise ValueError("invalid candidate slots need source index -1")
        if bool((self.source_kind[~self.valid_candidates] != -1).any()):
            raise ValueError("invalid candidate slots need source kind -1")
        for sample in range(batch):
            valid_indices = self.source_indices[sample, self.valid_candidates[sample]]
            if valid_indices.unique().numel() != valid_indices.numel():
                raise ValueError("candidate slots must not duplicate a source token")
            for slot in torch.nonzero(self.valid_candidates[sample], as_tuple=False).flatten().tolist():
                selected = torch.nonzero(self.masks[sample, slot], as_tuple=False).flatten()
                if selected.numel() != 1 or int(selected.item()) != int(self.source_indices[sample, slot].item()):
                    raise ValueError("candidate mask and source_indices disagree")
        if bool((self.source_kind[self.valid_candidates] < 0).any()) or bool(
            (self.source_kind[self.valid_candidates] > 3).any()
        ):
            raise ValueError("candidate source kind is out of range")
        if self.masks.device != self.source_indices.device or self.masks.device != self.source_kind.device:
            raise ValueError("candidate tensors must share device")
        if self.eligible_count.device != self.masks.device:
            raise ValueError("eligible_count must share candidate device")
        if bool((self.eligible_count < self.valid_candidates.sum(dim=1)).any()):
            raise ValueError("eligible_count is smaller than the number of valid candidates")


@dataclass(frozen=True)
class CoverageAudit:
    top1_covered: torch.Tensor
    oracle_regret: torch.Tensor
    sampled_best: torch.Tensor
    oracle_best: torch.Tensor
    evaluated_count: torch.Tensor

    def __post_init__(self) -> None:
        batch = self.top1_covered.shape[0]
        if self.top1_covered.shape != (batch,) or self.top1_covered.dtype != torch.bool:
            raise ValueError("top1_covered must be bool [B]")
        for name, value in (
            ("oracle_regret", self.oracle_regret),
            ("sampled_best", self.sampled_best),
            ("oracle_best", self.oracle_best),
        ):
            if value.shape != (batch,) or not value.is_floating_point():
                raise ValueError(f"{name} must be floating [B]")
            if not torch.isfinite(value).all():
                raise ValueError(f"{name} contains NaN/Inf")
        if self.evaluated_count.shape != (batch,) or self.evaluated_count.dtype != torch.long:
            raise ValueError("evaluated_count must be long [B]")

    def mean_metrics(self) -> dict[str, float]:
        return {
            "candidate_top1_coverage": float(self.top1_covered.float().mean().item()),
            "candidate_oracle_regret": float(self.oracle_regret.mean().item()),
            "candidate_audit_count": float(self.evaluated_count.float().mean().item()),
        }


class TeacherCandidateSampler:
    """Samples 4 DIE-top, 2 stratified-uniform, and 2 hard negatives."""

    TOP = 0
    STRATIFIED = 1
    HARD_NEGATIVE = 2
    AUDIT = 3

    def __init__(self, num_top: int = 4, num_stratified: int = 2, num_hard_negative: int = 2, audit_size: int = 16) -> None:
        for name, value in (("num_top", num_top), ("num_stratified", num_stratified), ("num_hard_negative", num_hard_negative), ("audit_size", audit_size)):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if num_top + num_stratified + num_hard_negative <= 0:
            raise ValueError("at least one regular candidate is required")
        if audit_size <= 0:
            raise ValueError("audit_size must be positive")
        self.num_top = num_top
        self.num_stratified = num_stratified
        self.num_hard_negative = num_hard_negative
        self.audit_size = audit_size

    @property
    def num_candidates(self) -> int:
        return self.num_top + self.num_stratified + self.num_hard_negative

    @staticmethod
    def _validate(batch: TokenBatch, scores: torch.Tensor, intervened_mask: torch.Tensor) -> torch.Tensor:
        if scores.shape != batch.valid.shape or not scores.is_floating_point():
            raise ValueError("scores must be floating [B, N]")
        if scores.device != batch.z.device or not torch.isfinite(scores).all():
            raise ValueError("scores must be finite and share the token device")
        if intervened_mask.shape != batch.valid.shape or intervened_mask.dtype != torch.bool:
            raise ValueError("intervened_mask must be bool [B, N]")
        if intervened_mask.device != batch.z.device or bool((intervened_mask & ~batch.valid).any()):
            raise ValueError("intervened_mask selects invalid tokens or uses the wrong device")
        eligible = batch.valid & ~intervened_mask
        if not bool((eligible.sum(dim=1) >= 2).all()):
            raise ValueError("candidate sampling requires at least two surviving valid tokens per sample")
        if bool((scores[~eligible] != 0).any()):
            raise ValueError("invalid/intervened tokens must have zero DIE scores")
        return eligible

    @staticmethod
    def _metadata_key(batch: TokenBatch, sample: int, index: int) -> tuple[int, int, int]:
        return (int(batch.token_type[sample, index]), int(batch.frame_id[sample, index]), int(batch.camera_id[sample, index]))

    @torch.no_grad()
    def sample(self, batch: TokenBatch, scores: torch.Tensor, intervened_mask: torch.Tensor, *, generator: Optional[torch.Generator] = None) -> CandidateSet:
        eligible = self._validate(batch, scores, intervened_mask)
        if not bool((eligible.sum(dim=1) >= self.num_candidates + 1).all()):
            raise ValueError("regular sampling needs num_candidates plus one untouched token")
        batch_size, tokens = scores.shape
        masks = torch.zeros((batch_size, self.num_candidates, tokens), dtype=torch.bool, device=scores.device)
        source_indices = torch.full((batch_size, self.num_candidates), -1, dtype=torch.long, device=scores.device)
        source_kind = torch.full_like(source_indices, -1)
        valid_candidates = torch.zeros_like(source_indices, dtype=torch.bool)

        for sample in range(batch_size):
            eligible_idx = torch.nonzero(eligible[sample], as_tuple=False).flatten()
            order = eligible_idx[torch.argsort(scores[sample, eligible_idx], descending=True, stable=True)]
            selected: list[int] = []
            kinds: list[int] = []
            for index in order[: self.num_top].tolist():
                selected.append(index)
                kinds.append(self.TOP)

            remaining = [index for index in eligible_idx.tolist() if index not in selected]
            if remaining and self.num_stratified:
                strata: dict[tuple[int, int, int], list[int]] = {}
                for index in remaining:
                    strata.setdefault(self._metadata_key(batch, sample, index), []).append(index)
                keys = sorted(strata)
                if len(keys) > 1:
                    keys = [keys[i] for i in torch.randperm(len(keys), generator=generator).tolist()]
                for offset_index in range(self.num_stratified):
                    key = keys[offset_index % len(keys)]
                    options = strata[key]
                    options = [index for index in options if index not in selected]
                    if not options:
                        options = [index for index in remaining if index not in selected]
                    if not options:
                        break
                    offset = int(torch.randint(len(options), (1,), generator=generator).item()) if len(options) > 1 else 0
                    selected.append(options[offset])
                    kinds.append(self.STRATIFIED)

            remaining = [index for index in order.tolist() if index not in selected]
            for index in remaining[: self.num_hard_negative]:
                selected.append(index)
                kinds.append(self.HARD_NEGATIVE)

            for slot, (index, kind) in enumerate(zip(selected, kinds)):
                masks[sample, slot, index] = True
                source_indices[sample, slot] = index
                source_kind[sample, slot] = kind
                valid_candidates[sample, slot] = True

        return CandidateSet(masks, source_indices, source_kind, valid_candidates, eligible.sum(dim=1).long())

    @torch.no_grad()
    def audit_candidates(
        self,
        batch: TokenBatch,
        scores: torch.Tensor,
        intervened_mask: torch.Tensor,
        regular: CandidateSet,
    ) -> CandidateSet:
        eligible = self._validate(batch, scores, intervened_mask)
        batch_size, tokens = scores.shape
        if regular.masks.shape[0] != batch_size or regular.masks.shape[2] != tokens:
            raise ValueError("regular candidates must match batch/token dimensions")
        if self.audit_size < regular.masks.shape[1]:
            raise ValueError("audit_size must cover every regular candidate")
        slots = min(self.audit_size, int(eligible.sum(dim=1).min().item()))
        masks = torch.zeros((batch_size, slots, tokens), dtype=torch.bool, device=scores.device)
        indices = torch.full((batch_size, slots), -1, dtype=torch.long, device=scores.device)
        kinds = torch.full_like(indices, self.AUDIT)
        valid = torch.zeros_like(indices, dtype=torch.bool)
        for sample in range(batch_size):
            eligible_idx = torch.nonzero(eligible[sample], as_tuple=False).flatten()
            order = eligible_idx[torch.argsort(scores[sample, eligible_idx], descending=True, stable=True)]
            regular_indices = regular.source_indices[sample, regular.valid_candidates[sample]].tolist()
            chosen_list = list(dict.fromkeys(regular_indices))
            remaining_slots = slots - len(chosen_list)
            remaining_order = torch.tensor(
                [index for index in order.tolist() if index not in chosen_list],
                dtype=torch.long,
                device=order.device,
            )
            if remaining_slots > 0 and remaining_order.numel() > 0:
                positions = torch.linspace(
                    0, remaining_order.numel() - 1, min(remaining_slots, remaining_order.numel()), device=order.device
                ).round().long()
                chosen_list.extend(remaining_order[positions].tolist())
            chosen = torch.tensor(chosen_list, dtype=torch.long, device=order.device)
            for slot, index in enumerate(chosen.tolist()):
                masks[sample, slot, index] = True
                indices[sample, slot] = index
                valid[sample, slot] = True
        return CandidateSet(masks, indices, kinds, valid, eligible.sum(dim=1).long())


def compute_coverage_audit(regular: CandidateSet, audit: CandidateSet, audit_influence: torch.Tensor) -> CoverageAudit:
    if regular.masks.shape[0] != audit.masks.shape[0]:
        raise ValueError("regular and audit candidate batches must match")
    if regular.masks.shape[2] != audit.masks.shape[2] or regular.masks.device != audit.masks.device:
        raise ValueError("regular and audit candidate token dimensions/devices must match")
    if audit_influence.shape != audit.valid_candidates.shape or not audit_influence.is_floating_point():
        raise ValueError("audit_influence must be floating [B, C_audit]")
    if audit_influence.device != audit.masks.device or not torch.isfinite(audit_influence).all():
        raise ValueError("audit_influence must be finite and share candidate device")
    masked = audit_influence.masked_fill(~audit.valid_candidates, -torch.inf)
    oracle_slot = masked.argmax(dim=1)
    oracle_best = masked.gather(1, oracle_slot[:, None]).squeeze(1)
    oracle_index = audit.source_indices.gather(1, oracle_slot[:, None]).squeeze(1)
    covered = ((regular.source_indices == oracle_index[:, None]) & regular.valid_candidates).any(dim=1)
    overlap = (regular.source_indices[:, :, None] == audit.source_indices[:, None, :]) & regular.valid_candidates[:, :, None] & audit.valid_candidates[:, None, :]
    if not bool((overlap.any(dim=2) == regular.valid_candidates).all()):
        raise ValueError("audit set must include every valid regular candidate")
    sampled_best = audit_influence[:, None, :].masked_fill(~overlap, -torch.inf).amax(dim=(1, 2))
    if not torch.isfinite(sampled_best).all():
        raise ValueError("regular candidates have no overlap with audit candidates")
    return CoverageAudit(covered, (oracle_best - sampled_best).clamp_min(0), sampled_best, oracle_best, audit.valid_candidates.sum(dim=1).long())


__all__ = ["CandidateSet", "CoverageAudit", "TeacherCandidateSampler", "compute_coverage_audit"]

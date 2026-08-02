"""Deterministic token selection and true equal-length tensor packing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch


@dataclass(frozen=True)
class PackedPatches:
    """Physically shortened patch tensor and its source indices."""

    patches: torch.Tensor
    keep_mask: torch.Tensor
    source_indices: torch.Tensor
    num_patches_full: int

    def __post_init__(self) -> None:
        if self.patches.ndim != 3:
            raise ValueError("patches must have shape [B, K, D]")
        batch, keep, _ = self.patches.shape
        if self.keep_mask.shape != (batch, self.num_patches_full) or self.keep_mask.dtype != torch.bool:
            raise ValueError("keep_mask must be bool [B, N_full]")
        if self.source_indices.shape != (batch, keep) or self.source_indices.dtype != torch.long:
            raise ValueError("source_indices must be long [B, K]")
        if not torch.equal(self.keep_mask.sum(dim=1), torch.full((batch,), keep, device=self.keep_mask.device)):
            raise ValueError("PackedPatches requires equal K for every sample")
        if keep >= self.num_patches_full:
            raise ValueError("packing must physically shorten the sequence; K must be < N_full")
        if keep <= 0:
            raise ValueError("at least one patch must be retained")


def deterministic_topk_mask(
    scores: torch.Tensor,
    keep_count: int,
    valid_mask: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    """Select a fixed number of valid tokens with stable index tie-breaking."""

    if scores.ndim != 2 or not scores.is_floating_point():
        raise ValueError("scores must be floating [B, N]")
    if not torch.isfinite(scores).all():
        raise ValueError("scores must be finite")
    batch, tokens = scores.shape
    if not 0 < keep_count < tokens:
        raise ValueError("keep_count must satisfy 0 < keep_count < N_full")
    if valid_mask is None:
        valid_mask = torch.ones_like(scores, dtype=torch.bool)
    if valid_mask.shape != scores.shape or valid_mask.dtype != torch.bool:
        raise ValueError("valid_mask must be bool with the same [B, N] shape as scores")
    if valid_mask.device != scores.device:
        raise ValueError("valid_mask and scores must share device")
    if not bool((valid_mask.sum(dim=1) >= keep_count).all()):
        raise ValueError("each sample must have at least keep_count valid tokens")

    # Stable sorting makes lower source index win exact score ties.
    masked_scores = scores.masked_fill(~valid_mask, -torch.inf)
    order = torch.argsort(masked_scores, dim=1, descending=True, stable=True)
    selected = order[:, :keep_count]
    keep_mask = torch.zeros((batch, tokens), dtype=torch.bool, device=scores.device)
    keep_mask.scatter_(1, selected, True)
    if bool((keep_mask & ~valid_mask).any()):
        raise RuntimeError("top-k selected an invalid token")
    return keep_mask


def pack_equal_length(patches: torch.Tensor, keep_mask: torch.Tensor) -> PackedPatches:
    """Gather equal-count selections into a physically shorter contiguous tensor.

    Ragged selections are rejected. Padding them back to a dense max length would not
    demonstrate true packed-token acceleration and is handled by a future bucket layer.
    """

    if patches.ndim != 3 or not patches.is_floating_point():
        raise ValueError("patches must be floating [B, N, D]")
    if not torch.isfinite(patches).all():
        raise ValueError("patches must contain only finite values")
    batch, tokens, hidden = patches.shape
    if keep_mask.shape != (batch, tokens) or keep_mask.dtype != torch.bool:
        raise ValueError("keep_mask must be bool [B, N]")
    if keep_mask.device != patches.device:
        raise ValueError("keep_mask and patches must share device")
    counts = keep_mask.sum(dim=1)
    if not bool((counts > 0).all()):
        raise ValueError("each sample must retain at least one patch")
    if counts.unique().numel() != 1:
        raise ValueError("ragged keep counts are forbidden; bucket samples by keep_count before packing")
    keep = int(counts[0].item())
    if keep >= tokens:
        raise ValueError("packing must reduce sequence length; refusing dense/full keep mask")

    indices = torch.arange(tokens, device=patches.device, dtype=torch.long).expand(batch, -1)
    source_indices = indices.masked_select(keep_mask).reshape(batch, keep)
    gather_idx = source_indices.unsqueeze(-1).expand(batch, keep, hidden)
    packed = patches.gather(dim=1, index=gather_idx).contiguous()
    return PackedPatches(
        patches=packed,
        keep_mask=keep_mask,
        source_indices=source_indices,
        num_patches_full=tokens,
    )


__all__ = ["PackedPatches", "deterministic_topk_mask", "pack_equal_length"]

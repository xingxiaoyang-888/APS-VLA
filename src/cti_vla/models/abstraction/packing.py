"""Shared physical token deletion and OFT original-position metadata.

Every index refers to the original camera-major visual sequence. Dense teacher,
deletion labels, deployment and timing must use this same versioned contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch


PACKING_VERSION = "oft-original-positions-v1"


def retained_indices(keep_mask: torch.Tensor) -> torch.Tensor:
    """Return ascending original indices; reject empty or ragged buckets."""
    if keep_mask.ndim != 2 or keep_mask.dtype != torch.bool:
        raise ValueError("keep_mask must be bool [B, N_full]")
    batch, tokens = keep_mask.shape
    if batch == 0 or tokens == 0:
        raise ValueError("keep_mask must have nonempty batch and token dimensions")
    counts = keep_mask.sum(dim=1)
    if not bool((counts > 0).all()):
        raise ValueError("each sample must retain at least one patch")
    if counts.unique().numel() != 1:
        raise ValueError("ragged keep counts are forbidden; bucket by keep_count")
    indices = torch.arange(tokens, device=keep_mask.device).expand(batch, -1)
    return indices.masked_select(keep_mask).reshape(batch, int(counts[0].item()))


def mask_from_indices(indices: torch.Tensor, num_patches_full: int) -> torch.Tensor:
    """Validate an ordered retained set and convert it to a full-length mask."""
    if indices.ndim != 2 or indices.dtype != torch.long or min(indices.shape) <= 0:
        raise ValueError("indices must be nonempty long [B, K]")
    if num_patches_full <= 0 or bool(((indices < 0) | (indices >= num_patches_full)).any()):
        raise ValueError("retained indices are outside the full visual sequence")
    if indices.shape[1] > 1 and not bool((indices[:, 1:] > indices[:, :-1]).all()):
        raise ValueError("retained indices must be unique and in ascending original order")
    mask = torch.zeros((indices.shape[0], num_patches_full), dtype=torch.bool, device=indices.device)
    return mask.scatter_(1, indices, True)


@dataclass(frozen=True)
class PackedPatches:
    patches: torch.Tensor
    keep_mask: torch.Tensor
    source_indices: torch.Tensor
    num_patches_full: int

    def __post_init__(self) -> None:
        if self.patches.ndim != 3 or not self.patches.is_floating_point():
            raise ValueError("patches must be floating [B, K, D]")
        if not bool(torch.isfinite(self.patches).all()):
            raise ValueError("patches must be finite")
        if self.keep_mask.shape != (self.patches.shape[0], self.num_patches_full):
            raise ValueError("keep_mask shape does not match batch/full count")
        if self.keep_mask.device != self.patches.device or self.source_indices.device != self.patches.device:
            raise ValueError("patches and selection metadata must share device")
        expected = retained_indices(self.keep_mask)
        if self.source_indices.dtype != torch.long or not torch.equal(self.source_indices, expected):
            raise ValueError("source_indices must match the original-order keep_mask")
        if self.patches.shape[1] != expected.shape[1]:
            raise ValueError("physical patch count disagrees with selection metadata")


def deterministic_topk_mask(
    scores: torch.Tensor,
    keep_count: int,
    valid_mask: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    """Select largest scores; lower original index wins an exact tie."""
    if scores.ndim != 2 or not scores.is_floating_point() or min(scores.shape) <= 0:
        raise ValueError("scores must be nonempty floating [B, N]")
    if not bool(torch.isfinite(scores).all()):
        raise ValueError("scores must be finite")
    if isinstance(keep_count, bool) or not isinstance(keep_count, int) or not 0 < keep_count <= scores.shape[1]:
        raise ValueError("keep_count must satisfy 0 < keep_count <= N_full")
    if valid_mask is None:
        valid_mask = torch.ones_like(scores, dtype=torch.bool)
    if valid_mask.shape != scores.shape or valid_mask.dtype != torch.bool:
        raise ValueError("valid_mask must be bool with the same [B, N] shape as scores")
    if valid_mask.device != scores.device:
        raise ValueError("valid_mask and scores must share device")
    if not bool((valid_mask.sum(dim=1) >= keep_count).all()):
        raise ValueError("each sample must have at least keep_count valid tokens")
    order = torch.argsort(scores.masked_fill(~valid_mask, -torch.inf), dim=1, descending=True, stable=True)
    return torch.zeros_like(valid_mask).scatter_(1, order[:, :keep_count], True)


def pack_equal_length(
    patches: torch.Tensor, keep_mask: torch.Tensor, *, allow_dense: bool = False,
) -> PackedPatches:
    """Gather original-order tokens; no padding or full-length replacement."""
    if patches.ndim != 3 or not patches.is_floating_point():
        raise ValueError("patches must be floating [B, N, D]")
    if keep_mask.shape != patches.shape[:2] or keep_mask.device != patches.device:
        raise ValueError("keep_mask must match patch [B, N] shape and device")
    indices = retained_indices(keep_mask)
    if not allow_dense and indices.shape[1] == patches.shape[1]:
        raise ValueError("packing must reduce sequence length; set allow_dense for the full teacher")
    packed = patches.gather(1, indices.unsqueeze(-1).expand(-1, -1, patches.shape[2])).contiguous()
    return PackedPatches(packed, keep_mask, indices, patches.shape[1])


@dataclass(frozen=True)
class OFTPackedBatch:
    """Unpadded OFT prefix; prompt count excludes BOS and includes empty token."""

    projected_patches: torch.Tensor
    proprio_token: torch.Tensor
    patch_keep_mask: torch.Tensor
    num_patches_full: int
    num_patches_keep: torch.Tensor
    num_prompt_tokens: torch.Tensor
    action_chunk_shape: tuple[int, int] = (8, 7)

    def __post_init__(self) -> None:
        if self.projected_patches.ndim != 3 or not self.projected_patches.is_floating_point():
            raise ValueError("projected_patches must be floating [B, K, D]")
        batch, keep, hidden = self.projected_patches.shape
        if not isinstance(self.num_patches_full, int) or isinstance(self.num_patches_full, bool):
            raise ValueError("num_patches_full must be a Python int")
        if self.patch_keep_mask.shape != (batch, self.num_patches_full):
            raise ValueError("patch_keep_mask must be [B, N_full]")
        indices = retained_indices(self.patch_keep_mask)
        if indices.shape[1] != keep:
            raise ValueError("projected_patches must have physical K matching keep_mask, without padding")
        if self.proprio_token.shape != (batch, 1, hidden):
            raise ValueError("proprio_token must have shape [B, 1, D]")
        for name in ("num_patches_keep", "num_prompt_tokens"):
            value = getattr(self, name)
            if value.shape != (batch,) or value.dtype != torch.long:
                raise ValueError(f"{name} must be long [B]")
        if not bool((self.num_patches_keep == keep).all()):
            raise ValueError("num_patches_keep disagrees with physical sequence length")
        if not bool((self.num_prompt_tokens >= 1).all()):
            raise ValueError("num_prompt_tokens must include at least one non-BOS prompt token")
        if len(self.action_chunk_shape) != 2 or any(type(v) is not int or v <= 0 for v in self.action_chunk_shape):
            raise ValueError("action_chunk_shape must be positive (chunk, action_dim)")
        for name in ("proprio_token", "patch_keep_mask", "num_patches_keep", "num_prompt_tokens"):
            if getattr(self, name).device != self.projected_patches.device:
                raise ValueError(f"{name} must share device with projected_patches")
        if self.proprio_token.dtype != self.projected_patches.dtype:
            raise ValueError("proprio_token and projected_patches must share dtype")
        if not bool(torch.isfinite(self.projected_patches).all()) or not bool(torch.isfinite(self.proprio_token).all()):
            raise ValueError("prefix features must be finite")

    @property
    def batch_size(self) -> int:
        return self.projected_patches.shape[0]

    @property
    def packed_num_patches(self) -> int:
        return self.projected_patches.shape[1]

    def action_hidden_start(self, sample_index: int) -> int:
        if not 0 <= sample_index < self.batch_size:
            raise IndexError("sample_index out of range")
        return self.packed_num_patches + 1 + int(self.num_prompt_tokens[sample_index].item())

    def original_position_ids(self, text_sequence_length: int) -> torch.Tensor:
        """RoPE IDs: BOS=0, visual=i+1, proprio=N+1, then original text IDs.

        These semantic positions are separate from packed tensor/action offsets.
        Cache positions are deliberately left to the backbone's physical layout.
        """
        if text_sequence_length < 2:
            raise ValueError("text sequence must contain BOS and at least one following token")
        visual = retained_indices(self.patch_keep_mask) + 1
        bos = torch.zeros((self.batch_size, 1), dtype=torch.long, device=visual.device)
        suffix = torch.arange(
            self.num_patches_full + 1,
            self.num_patches_full + 1 + text_sequence_length,
            device=visual.device,
        ).expand(self.batch_size, -1)
        return torch.cat((bos, visual, suffix), dim=1).contiguous()


__all__ = [
    "PACKING_VERSION", "OFTPackedBatch", "PackedPatches", "deterministic_topk_mask",
    "mask_from_indices", "pack_equal_length", "retained_indices",
]

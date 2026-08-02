"""Validated tensor contracts used at the OpenVLA-OFT/DIWA boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import torch


def _check_batch_shape(name: str, tensor: torch.Tensor, batch: int) -> None:
    if tensor.ndim == 0 or tensor.shape[0] != batch:
        raise ValueError(f"{name} must have batch dimension {batch}, got {tuple(tensor.shape)}")


def _check_same_device_dtype(name: str, tensor: torch.Tensor, reference: torch.Tensor) -> None:
    if tensor.device != reference.device:
        raise ValueError(f"{name} device {tensor.device} != z device {reference.device}")
    integer_dtypes = (torch.bool, torch.uint8, torch.int8, torch.int16, torch.int32, torch.int64)
    if tensor.dtype != reference.dtype and tensor.dtype not in integer_dtypes:
        raise ValueError(f"{name} dtype {tensor.dtype} incompatible with z dtype {reference.dtype}")


@dataclass
class TokenBatch:
    """Typed token batch before DIE scoring.

    `z` contains projected visual/latent tokens. Proprio is already normalized
    according to the OpenVLA-OFT checkpoint statistics.
    """

    z: torch.Tensor
    token_type: torch.Tensor
    frame_id: torch.Tensor
    camera_id: torch.Tensor
    valid: torch.Tensor
    query: torch.Tensor
    proprio: torch.Tensor
    diffusion_noise: Optional[torch.Tensor] = None

    def __post_init__(self) -> None:
        if not isinstance(self.z, torch.Tensor) or self.z.ndim != 3:
            raise ValueError("z must be a rank-3 tensor [B, N, D]")
        if not self.z.is_floating_point():
            raise TypeError("z must be floating point")
        batch, tokens, _ = self.z.shape
        if tokens <= 0:
            raise ValueError("z must contain at least one token")

        for name, value in (
            ("token_type", self.token_type),
            ("frame_id", self.frame_id),
            ("camera_id", self.camera_id),
            ("valid", self.valid),
        ):
            if not isinstance(value, torch.Tensor) or value.shape != (batch, tokens):
                raise ValueError(f"{name} must have shape [B, N]={batch, tokens}")
        if self.token_type.dtype not in (torch.int32, torch.int64, torch.long):
            raise TypeError("token_type must be an integer tensor")
        if self.frame_id.dtype not in (torch.int32, torch.int64, torch.long):
            raise TypeError("frame_id must be an integer tensor")
        if self.camera_id.dtype not in (torch.int32, torch.int64, torch.long):
            raise TypeError("camera_id must be an integer tensor")
        if self.valid.dtype != torch.bool:
            raise TypeError("valid must be bool")
        if not self.z.isfinite().all():
            raise ValueError("z must contain only finite values")

        _check_batch_shape("query", self.query, batch)
        _check_batch_shape("proprio", self.proprio, batch)
        if self.query.ndim != 2 or self.proprio.ndim != 2:
            raise ValueError("query and proprio must be rank-2 tensors [B, D]")
        if not self.query.is_floating_point() or not self.proprio.is_floating_point():
            raise TypeError("query and proprio must be floating point")
        if self.query.dtype != self.z.dtype or self.proprio.dtype != self.z.dtype:
            raise TypeError("query and proprio must use the same dtype as z")
        if not self.query.isfinite().all() or not self.proprio.isfinite().all():
            raise ValueError("query and proprio must contain only finite values")
        _check_same_device_dtype("query", self.query, self.z)
        _check_same_device_dtype("proprio", self.proprio, self.z)
        for name, value in (
            ("token_type", self.token_type),
            ("frame_id", self.frame_id),
            ("camera_id", self.camera_id),
            ("valid", self.valid),
        ):
            _check_same_device_dtype(name, value, self.z)

        if not bool(self.valid.any(dim=1).all()):
            raise ValueError("each sample must have at least one valid token")
        if self.diffusion_noise is not None:
            if not isinstance(self.diffusion_noise, torch.Tensor) or self.diffusion_noise.ndim < 2:
                raise ValueError("diffusion_noise must be a tensor with batch dimension")
            _check_batch_shape("diffusion_noise", self.diffusion_noise, batch)
            if not self.diffusion_noise.is_floating_point() or self.diffusion_noise.dtype != self.z.dtype:
                raise TypeError("diffusion_noise must use the same floating dtype as z")
            if not self.diffusion_noise.isfinite().all():
                raise ValueError("diffusion_noise must contain only finite values")
            _check_same_device_dtype("diffusion_noise", self.diffusion_noise, self.z)

    @property
    def batch_size(self) -> int:
        return self.z.shape[0]

    @property
    def num_tokens(self) -> int:
        return self.z.shape[1]

    @property
    def hidden_dim(self) -> int:
        return self.z.shape[2]


@dataclass
class OFTPackedBatch:
    """Packed prefix contract preserving OFT action-token indexing metadata."""

    projected_patches: torch.Tensor
    proprio_token: torch.Tensor
    patch_keep_mask: torch.Tensor
    num_patches_full: int
    num_patches_keep: torch.Tensor
    num_prompt_tokens: torch.Tensor
    action_chunk_shape: Tuple[int, int] = (8, 7)

    def __post_init__(self) -> None:
        if self.projected_patches.ndim != 3:
            raise ValueError("projected_patches must have shape [B, N_keep, D]")
        if not self.projected_patches.is_floating_point() or not self.projected_patches.isfinite().all():
            raise TypeError("projected_patches must be finite floating point")
        batch, keep_tokens, hidden = self.projected_patches.shape
        if self.proprio_token.ndim != 3 or self.proprio_token.shape != (batch, 1, hidden):
            raise ValueError("proprio_token must have shape [B, 1, D] matching projected_patches")
        if self.patch_keep_mask.ndim != 2 or self.patch_keep_mask.shape[0] != batch:
            raise ValueError("patch_keep_mask must have shape [B, N_full]")
        if not isinstance(self.num_patches_full, int) or isinstance(self.num_patches_full, bool):
            raise TypeError("num_patches_full must be a Python int")
        if self.num_patches_full != self.patch_keep_mask.shape[1]:
            raise ValueError("num_patches_full must equal patch_keep_mask.shape[1]")
        if self.num_patches_full <= 0 or keep_tokens <= 0:
            raise ValueError("full and packed patch counts must be positive")
        if self.patch_keep_mask.dtype != torch.bool:
            raise TypeError("patch_keep_mask must be bool")
        if self.num_patches_keep.shape != (batch,) or self.num_patches_keep.dtype not in (
            torch.int32,
            torch.int64,
            torch.long,
        ):
            raise ValueError("num_patches_keep must be integer tensor [B]")
        actual = self.patch_keep_mask.sum(dim=1)
        if not torch.equal(actual.to(self.num_patches_keep.device), self.num_patches_keep):
            raise ValueError("num_patches_keep disagrees with patch_keep_mask")
        if not bool((self.num_patches_keep > 0).all()):
            raise ValueError("each sample must retain at least one patch")
        if self.num_prompt_tokens.shape != (batch,) or self.num_prompt_tokens.dtype not in (
            torch.int32,
            torch.int64,
            torch.long,
        ):
            raise ValueError("num_prompt_tokens must be integer tensor [B]")
        if bool((self.num_prompt_tokens < 0).any()):
            raise ValueError("num_prompt_tokens cannot be negative")
        if len(self.action_chunk_shape) != 2 or any(
            not isinstance(v, int) or isinstance(v, bool) or v <= 0 for v in self.action_chunk_shape
        ):
            raise ValueError("action_chunk_shape must be a positive (chunk, action_dim) tuple")
        if self.projected_patches.device != self.proprio_token.device:
            raise ValueError("projected_patches and proprio_token must share device")
        if self.projected_patches.dtype != self.proprio_token.dtype:
            raise ValueError("projected_patches and proprio_token must share dtype")
        if not self.proprio_token.isfinite().all():
            raise ValueError("proprio_token must contain only finite values")
        if self.patch_keep_mask.device != self.projected_patches.device:
            raise ValueError("patch_keep_mask must share device with projected_patches")
        if self.num_patches_keep.device != self.projected_patches.device:
            raise ValueError("num_patches_keep must share device with projected_patches")
        if self.num_prompt_tokens.device != self.projected_patches.device:
            raise ValueError("num_prompt_tokens must share device with projected_patches")

    @property
    def batch_size(self) -> int:
        return self.projected_patches.shape[0]

    @property
    def packed_num_patches(self) -> int:
        """Only valid for equal-length buckets; ragged batches use per-sample counts."""
        values = self.num_patches_keep.unique()
        if values.numel() != 1:
            raise RuntimeError("packed batch is ragged; use num_patches_keep per sample")
        return int(values.item())

    def action_hidden_start(self, sample_index: int) -> int:
        if not 0 <= sample_index < self.batch_size:
            raise IndexError("sample_index out of range")
        # OpenVLA-OFT appends one proprio token after the retained visual patches.
        return int(
            self.num_patches_keep[sample_index].item()
            + 1
            + self.num_prompt_tokens[sample_index].item()
        )


__all__ = ["OFTPackedBatch", "TokenBatch"]

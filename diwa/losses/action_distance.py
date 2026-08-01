"""Numerically stable distance for normalized OpenVLA-OFT action chunks."""

from __future__ import annotations

from typing import Literal

import torch


def normalized_action_chunk_distance(
    first: torch.Tensor,
    second: torch.Tensor,
    *,
    huber_delta: float = 1.0,
    reduction: Literal["none", "mean", "sum"] = "none",
) -> torch.Tensor:
    """Huber distance over `[B, K, action_dim]` normalized action chunks.

    The calculation is accumulated in fp32 even when model outputs are bf16.
    """

    if first.ndim != 3 or second.ndim != 3 or first.shape != second.shape:
        raise ValueError("action chunks must have identical [B, K, action_dim] shape")
    if not first.is_floating_point() or not second.is_floating_point():
        raise TypeError("action chunks must be floating point")
    if first.device != second.device:
        raise ValueError("action chunks must share device")
    if huber_delta <= 0:
        raise ValueError("huber_delta must be positive")
    if reduction not in ("none", "mean", "sum"):
        raise ValueError("reduction must be one of: none, mean, sum")
    if not torch.isfinite(first).all() or not torch.isfinite(second).all():
        raise ValueError("action chunks must contain only finite values")

    diff = (first.float() - second.float()).abs()
    delta = torch.as_tensor(huber_delta, device=diff.device, dtype=diff.dtype)
    loss = torch.where(diff <= delta, 0.5 * diff.square(), delta * (diff - 0.5 * delta))
    per_sample = loss.mean(dim=(1, 2))
    if reduction == "mean":
        return per_sample.mean()
    if reduction == "sum":
        return per_sample.sum()
    return per_sample


__all__ = ["normalized_action_chunk_distance"]

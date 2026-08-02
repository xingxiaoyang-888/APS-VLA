"""Non-zero matched baselines and token interventions."""

from __future__ import annotations

from typing import Optional

import torch


def _reject_zero_baseline(baseline: torch.Tensor, reference: torch.Tensor) -> None:
    if baseline.shape != reference.shape:
        raise ValueError(f"baseline shape {baseline.shape} != token shape {reference.shape}")
    if not baseline.is_floating_point():
        raise TypeError("baseline must be floating point")
    if not baseline.isfinite().all():
        raise ValueError("baseline must contain only finite values")
    # Exact zero is forbidden: it is an OOD intervention for this project.
    if bool(torch.all(baseline == 0)):
        raise ValueError("all-zero intervention baseline is forbidden; use matched mean or EMA prototype")
    if baseline.device != reference.device or baseline.dtype != reference.dtype:
        raise ValueError("baseline must share device and dtype with tokens")


class MatchedMeanBaseline:
    """Computes per-token-type/camera/frame means without gradients."""

    def __init__(self, eps: float = 1e-6) -> None:
        self.eps = eps

    @torch.no_grad()
    def __call__(
        self,
        z: torch.Tensor,
        token_type: torch.Tensor,
        frame_id: torch.Tensor,
        camera_id: torch.Tensor,
        valid: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        if z.ndim != 3:
            raise ValueError("z must be [B, N, D]")
        if not z.is_floating_point() or not z.isfinite().all():
            raise ValueError("z must be finite floating point")
        if not (token_type.shape == frame_id.shape == camera_id.shape == z.shape[:2]):
            raise ValueError("metadata must all have shape [B, N]")
        if valid is None:
            valid = torch.ones(z.shape[:2], dtype=torch.bool, device=z.device)
        if valid.shape != z.shape[:2] or valid.dtype != torch.bool or valid.device != z.device:
            raise ValueError("valid must be bool [B, N] on the z device")
        if not bool(valid.any(dim=1).all()):
            raise ValueError("each sample must have at least one valid token")
        # Batch-global matched statistics are detached and broadcast back to tokens.
        keys = torch.stack((token_type, frame_id, camera_id), dim=-1).reshape(-1, 3)
        flat = z.reshape(-1, z.shape[-1])
        flat_valid = valid.reshape(-1)
        out = torch.empty_like(flat)
        for key in torch.unique(keys, dim=0):
            mask = torch.all(keys == key, dim=1)
            values = flat[mask & flat_valid]
            if values.numel() == 0:
                continue
            mean = values.mean(dim=0)
            if torch.all(mean == 0):
                mean = values.abs().mean(dim=0)
            out[mask] = mean
        # Invalid/padded positions never participate in an intervention target.
        out[~flat_valid] = 0
        if bool(torch.all(out == 0)):
            raise ValueError("matched mean baseline collapsed to zero")
        return out.reshape_as(z).detach()


class EMABaseline:
    """EMA prototype baseline keyed by token type/camera/frame tuple."""

    def __init__(self, momentum: float = 0.99) -> None:
        if not 0.0 < momentum < 1.0:
            raise ValueError("momentum must be in (0, 1)")
        self.momentum = momentum
        self._prototype: Optional[torch.Tensor] = None

    @torch.no_grad()
    def update(self, z: torch.Tensor) -> None:
        if z.ndim != 2 or not z.is_floating_point():
            raise ValueError("EMA update expects detached [M, D] floating tensor")
        if not z.isfinite().all():
            raise ValueError("EMA update rejects NaN/Inf")
        mean = z.detach().mean(dim=0)
        if self._prototype is None:
            self._prototype = mean.clone()
        else:
            if self._prototype.shape != mean.shape or self._prototype.device != mean.device:
                raise ValueError("EMA prototype shape/device changed")
            self._prototype.mul_(self.momentum).add_(mean, alpha=1.0 - self.momentum)

    @torch.no_grad()
    def __call__(self, z: torch.Tensor) -> torch.Tensor:
        if self._prototype is None:
            raise RuntimeError("EMA baseline is uninitialized; call update() first")
        baseline = self._prototype.to(device=z.device, dtype=z.dtype).expand_as(z).clone()
        _reject_zero_baseline(baseline, z)
        return baseline.detach()


@torch.no_grad()
def apply_intervention(
    z: torch.Tensor,
    intervene_mask: torch.Tensor,
    baseline: torch.Tensor,
    *,
    allow_empty: bool = False,
) -> torch.Tensor:
    """Replace selected tokens with a validated non-zero matched baseline."""

    if z.ndim != 3:
        raise ValueError("z must have shape [B, N, D]")
    if not z.isfinite().all():
        raise ValueError("z must contain only finite values")
    if intervene_mask.shape != z.shape[:2] or intervene_mask.dtype != torch.bool:
        raise ValueError("intervene_mask must be bool [B, N]")
    _reject_zero_baseline(baseline, z)
    if not allow_empty and not bool(intervene_mask.any(dim=1).all()):
        raise ValueError("each sample must intervene on at least one token")
    return torch.where(intervene_mask.unsqueeze(-1), baseline, z).detach()


__all__ = ["EMABaseline", "MatchedMeanBaseline", "apply_intervention"]

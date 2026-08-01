"""Stable regression and ranking losses for conditional influence targets."""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn.functional as F


@dataclass(frozen=True)
class InfluenceLossOutput:
    loss: torch.Tensor
    regression: torch.Tensor
    ranking: torch.Tensor
    valid_candidates: torch.Tensor
    valid_pairs: torch.Tensor


def conditional_influence_loss(
    predicted: torch.Tensor,
    target: torch.Tensor,
    valid: torch.Tensor,
    *,
    regression_beta: float = 0.25,
    ranking_weight: float = 0.1,
    ranking_temperature: float = 0.25,
    ranking_tie_margin: float = 1e-4,
) -> InfluenceLossOutput:
    if predicted.ndim != 2 or target.shape != predicted.shape or valid.shape != predicted.shape:
        raise ValueError("predicted, target, and valid must share [B, C] shape")
    if not predicted.is_floating_point() or not target.is_floating_point() or valid.dtype != torch.bool:
        raise TypeError("predicted/target must be floating and valid must be bool")
    if predicted.device != target.device or predicted.device != valid.device:
        raise ValueError("loss inputs must share device")
    if not torch.isfinite(predicted).all() or not torch.isfinite(target).all():
        raise ValueError("loss inputs contain NaN/Inf")
    if bool((predicted < 0).any()) or bool((target < 0).any()):
        raise ValueError("influence predictions and targets must be non-negative")
    if not bool(valid.any(dim=1).all()):
        raise ValueError("each sample must contain at least one valid candidate")
    if regression_beta <= 0 or ranking_weight < 0 or ranking_temperature <= 0 or ranking_tie_margin < 0:
        raise ValueError("loss hyperparameters are out of range")

    predicted_log = torch.log1p(predicted.float())
    target_log = torch.log1p(target.float())
    regression_values = F.smooth_l1_loss(
        predicted_log, target_log, beta=regression_beta, reduction="none"
    )
    regression = regression_values[valid].mean()

    target_diff = target_log[:, :, None] - target_log[:, None, :]
    predicted_diff = predicted_log[:, :, None] - predicted_log[:, None, :]
    pair_valid = valid[:, :, None] & valid[:, None, :]
    upper_triangle = torch.triu(
        torch.ones(predicted.shape[1], predicted.shape[1], dtype=torch.bool, device=predicted.device),
        diagonal=1,
    )
    pair_valid = pair_valid & upper_triangle & (target_diff.abs() > ranking_tie_margin)
    if bool(pair_valid.any()):
        direction = target_diff.sign()
        ranking_values = F.softplus(-direction * predicted_diff / ranking_temperature)
        ranking = ranking_values[pair_valid].mean()
        valid_pairs = pair_valid.sum()
    else:
        ranking = predicted_log.sum() * 0.0
        valid_pairs = torch.zeros((), dtype=torch.long, device=predicted.device)
    loss = regression + ranking_weight * ranking
    return InfluenceLossOutput(
        loss=loss,
        regression=regression.detach(),
        ranking=ranking.detach(),
        valid_candidates=valid.sum().detach(),
        valid_pairs=valid_pairs.detach(),
    )


__all__ = ["InfluenceLossOutput", "conditional_influence_loss"]

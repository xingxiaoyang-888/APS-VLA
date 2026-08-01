"""OOM-conscious Stage-A optimization of the Decision Influence Estimator."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import torch
from torch import nn

from diwa.data.contracts import TokenBatch
from diwa.losses.influence_loss import conditional_influence_loss
from diwa.models.influence.die import DecisionInfluenceEstimator


@dataclass(frozen=True)
class StageAConfig:
    regression_beta: float = 0.25
    ranking_weight: float = 0.1
    ranking_temperature: float = 0.25
    ranking_tie_margin: float = 1e-4
    max_grad_norm: float = 1.0

    def __post_init__(self) -> None:
        numeric = (self.regression_beta, self.ranking_weight, self.ranking_temperature, self.ranking_tie_margin, self.max_grad_norm)
        if any(not isinstance(value, (int, float)) or not math.isfinite(float(value)) for value in numeric):
            raise ValueError("Stage-A hyperparameters must be finite numbers")
        if self.regression_beta <= 0 or self.ranking_weight < 0:
            raise ValueError("regression_beta/ranking_weight are out of range")
        if self.ranking_temperature <= 0 or self.ranking_tie_margin < 0 or self.max_grad_norm <= 0:
            raise ValueError("ranking/gradient hyperparameters are out of range")


@dataclass(frozen=True)
class StageABatch:
    token_batch: TokenBatch
    intervened_mask: torch.Tensor
    source_indices: torch.Tensor
    target_influence: torch.Tensor
    valid_candidates: torch.Tensor

    def __post_init__(self) -> None:
        batch = self.token_batch.batch_size
        if self.intervened_mask.shape != self.token_batch.valid.shape or self.intervened_mask.dtype != torch.bool:
            raise ValueError("intervened_mask must be bool [B, N]")
        if self.source_indices.ndim != 2 or self.source_indices.shape[0] != batch or self.source_indices.dtype != torch.long:
            raise ValueError("source_indices must be long [B, C]")
        expected = self.source_indices.shape
        if self.target_influence.shape != expected or not self.target_influence.is_floating_point():
            raise ValueError("target_influence must be floating [B, C]")
        if self.valid_candidates.shape != expected or self.valid_candidates.dtype != torch.bool:
            raise ValueError("valid_candidates must be bool [B, C]")
        for value in (self.intervened_mask, self.source_indices, self.target_influence, self.valid_candidates):
            if value.device != self.token_batch.z.device:
                raise ValueError("Stage-A tensors and TokenBatch must share device")
        for name, value in (
            ("z", self.token_batch.z),
            ("query", self.token_batch.query),
            ("proprio", self.token_batch.proprio),
            ("target_influence", self.target_influence),
        ):
            if value.requires_grad:
                raise ValueError(f"Stage-A {name} must be detached from teacher/VLA graphs")
        if bool((self.intervened_mask & ~self.token_batch.valid).any()):
            raise ValueError("intervened_mask selects invalid tokens")
        valid_indices = self.source_indices[self.valid_candidates]
        if bool((valid_indices < 0).any()) or bool((valid_indices >= self.token_batch.num_tokens).any()):
            raise ValueError("valid source_indices are out of token range")
        if bool((self.source_indices[~self.valid_candidates] != -1).any()):
            raise ValueError("invalid candidate source index must be -1")
        safe_indices = self.source_indices.clamp_min(0)
        selected_valid = self.token_batch.valid.gather(1, safe_indices)
        selected_intervened = self.intervened_mask.gather(1, safe_indices)
        if bool((~selected_valid[self.valid_candidates]).any()) or bool(selected_intervened[self.valid_candidates].any()):
            raise ValueError("candidate source indices select invalid/intervened tokens")
        if not torch.isfinite(self.target_influence).all() or bool((self.target_influence < 0).any()):
            raise ValueError("target influence must be finite and non-negative")
        if bool((self.target_influence[~self.valid_candidates] != 0).any()):
            raise ValueError("invalid candidates must have zero target influence")


@dataclass(frozen=True)
class StageAStepOutput:
    loss: float
    regression_loss: float
    ranking_loss: float
    grad_norm: float
    valid_candidates: int
    valid_pairs: int


def freeze_teacher_modules(modules: Iterable[nn.Module]) -> None:
    """Freeze and eval all 7B teacher-side modules before DIE-only training."""

    seen: set[int] = set()
    for module in modules:
        if not isinstance(module, nn.Module):
            raise TypeError("freeze_teacher_modules expects nn.Module objects")
        if id(module) in seen:
            continue
        seen.add(id(module))
        module.eval()
        module.requires_grad_(False)
        if module.training or any(parameter.requires_grad for parameter in module.parameters()):
            raise RuntimeError("failed to freeze a teacher-side module")


class StageATrainer:
    def __init__(
        self,
        estimator: DecisionInfluenceEstimator,
        optimizer: torch.optim.Optimizer,
        config: StageAConfig | None = None,
    ) -> None:
        self.estimator = estimator
        self.optimizer = optimizer
        self.config = config or StageAConfig()
        estimator_params = {id(parameter) for parameter in estimator.parameters() if parameter.requires_grad}
        optimizer_params = {
            id(parameter)
            for group in optimizer.param_groups
            for parameter in group["params"]
        }
        if not estimator_params:
            raise ValueError("estimator has no trainable parameters")
        if optimizer_params != estimator_params:
            raise ValueError("Stage-A optimizer must contain exactly the trainable DIE parameters")

    def train_step(self, batch: StageABatch) -> StageAStepOutput:
        self.estimator.train()
        self.optimizer.zero_grad(set_to_none=True)
        token_scores = self.estimator(batch.token_batch, batch.intervened_mask)
        safe_indices = batch.source_indices.clamp_min(0)
        predicted = token_scores.gather(1, safe_indices).masked_fill(~batch.valid_candidates, 0.0)
        loss_output = conditional_influence_loss(
            predicted,
            batch.target_influence,
            batch.valid_candidates,
            regression_beta=self.config.regression_beta,
            ranking_weight=self.config.ranking_weight,
            ranking_temperature=self.config.ranking_temperature,
            ranking_tie_margin=self.config.ranking_tie_margin,
        )
        if not torch.isfinite(loss_output.loss):
            raise FloatingPointError("Stage-A loss is NaN/Inf; refusing optimizer step")
        loss_output.loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(
            self.estimator.parameters(), self.config.max_grad_norm, error_if_nonfinite=True
        )
        self.optimizer.step()
        return StageAStepOutput(
            loss=float(loss_output.loss.detach()),
            regression_loss=float(loss_output.regression),
            ranking_loss=float(loss_output.ranking),
            grad_norm=float(grad_norm.detach()),
            valid_candidates=int(loss_output.valid_candidates),
            valid_pairs=int(loss_output.valid_pairs),
        )


__all__ = ["StageABatch", "StageAConfig", "StageAStepOutput", "StageATrainer", "freeze_teacher_modules"]

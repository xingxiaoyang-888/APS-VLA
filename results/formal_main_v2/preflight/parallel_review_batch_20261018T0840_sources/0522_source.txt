"""Offline scorer-only optimization with a single training-set target scale."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import torch
import torch.nn.functional as F

from cti_vla.labeling import DeletionLabels, LabelProvenance
from cti_vla.selection import ConditionalInfluenceEstimator, ConditionalTokenBatch


def _versions(provenance: LabelProvenance) -> tuple[str, ...]:
    return tuple(getattr(provenance, name) for name in (
        "model_revision", "dataset_version", "preprocessing_version", "packing_version",
        "condition_version", "action_version", "label_version",
    ))


@dataclass(frozen=True)
class TrainingLabelScale:
    """RMS of signed training labels; no centering or per-observation scaling.

    Save this object with each scorer checkpoint. Predictions are in normalized
    units after training; multiply by ``value`` for raw action-error increments.
    Ranking/top-k is invariant to this single positive scaling factor.
    """

    value: float
    label_count: int
    training_episodes: tuple[str, ...]
    versions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not math.isfinite(self.value) or self.value <= 0 or type(self.label_count) is not int or self.label_count <= 0:
            raise ValueError("label scale/count must be positive and finite")
        if not self.training_episodes or len(self.versions) != 7:
            raise ValueError("scale requires training episodes and all version identities")

    @classmethod
    def fit(cls, records: Iterable[DeletionLabels], *, minimum: float = 1e-6) -> "TrainingLabelScale":
        if not math.isfinite(minimum) or minimum <= 0:
            raise ValueError("minimum scale must be finite and positive")
        total, count, episodes, versions = 0.0, 0, set(), None
        for record in records:
            record.__post_init__()
            if record.provenance.split != "train":
                raise ValueError("target scale must be fit on training episodes only")
            current = _versions(record.provenance)
            if versions is not None and versions != current:
                raise ValueError("cannot fit a scale across incompatible label versions")
            versions = current
            total += record.influence.detach().double().square().sum().item()
            count += record.influence.numel()
            episodes.update(record.provenance.episode_ids)
        if count == 0:
            raise ValueError("cannot fit scale without training labels")
        return cls(max(math.sqrt(total / count), minimum), count, tuple(sorted(episodes)), versions)

    def validate(self, provenance: LabelProvenance) -> None:
        if self.versions != _versions(provenance):
            raise ValueError("label scale was fit on incompatible model/data/packing/condition versions")
        if provenance.split != "train" and set(self.training_episodes).intersection(provenance.episode_ids):
            raise ValueError("evaluation episode overlaps scale-fitting training episodes")


@dataclass(frozen=True)
class ConditionalTrainConfig:
    huber_delta: float = 1.0
    ranking_weight: float = 0.0
    ranking_temperature: float = 1.0
    ranking_tie_margin: float = 1e-4
    max_grad_norm: float = 1.0

    def __post_init__(self) -> None:
        values = (self.huber_delta, self.ranking_weight, self.ranking_temperature, self.ranking_tie_margin, self.max_grad_norm)
        if any(not math.isfinite(x) for x in values):
            raise ValueError("training hyperparameters must be finite")
        if min(self.huber_delta, self.ranking_temperature, self.max_grad_norm) <= 0 or min(self.ranking_weight, self.ranking_tie_margin) < 0:
            raise ValueError("training hyperparameters out of range")


def signed_influence_loss(predicted: torch.Tensor, target: torch.Tensor, config: ConditionalTrainConfig) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Huber regression and optional comparisons ONLY inside the same row/S."""
    if predicted.ndim != 2 or min(predicted.shape) <= 0 or target.shape != predicted.shape:
        raise ValueError("predicted and target must share nonempty [B, C] shape")
    if not predicted.is_floating_point() or not target.is_floating_point() or target.requires_grad:
        raise ValueError("scores must be floating point; targets must be detached")
    if predicted.device != target.device or not torch.isfinite(predicted).all() or not torch.isfinite(target).all():
        raise ValueError("scores must be finite and share device")
    regression = F.huber_loss(predicted.float(), target.float(), delta=config.huber_delta)
    ranking = predicted.sum() * 0.0
    if config.ranking_weight > 0:
        difference = target[:, :, None] - target[:, None, :]
        upper = torch.triu(torch.ones(predicted.shape[1], predicted.shape[1], dtype=torch.bool, device=predicted.device), diagonal=1)
        valid = upper & (difference.abs() > config.ranking_tie_margin)
        if valid.any():
            predicted_difference = predicted[:, :, None] - predicted[:, None, :]
            ranking = F.softplus(-difference.sign() * predicted_difference / config.ranking_temperature)[valid].mean()
    return regression + config.ranking_weight * ranking, regression.detach(), ranking.detach()


class ConditionalTrainer:
    """Consumes verified detached cache records, never calls the large policy."""

    def __init__(self, estimator: ConditionalInfluenceEstimator, optimizer: torch.optim.Optimizer,
                 scale: TrainingLabelScale, config: ConditionalTrainConfig | None = None) -> None:
        expected = {id(p) for p in estimator.parameters() if p.requires_grad}
        provided_list = [p for group in optimizer.param_groups for p in group["params"]]
        provided = {id(p) for p in provided_list}
        if not expected or provided != expected or len(provided_list) != len(provided):
            raise ValueError("optimizer must contain exactly the trainable scorer/condition parameters")
        self.estimator, self.optimizer, self.scale = estimator, optimizer, scale
        self.config = config or ConditionalTrainConfig()

    def train_step(self, batch: ConditionalTokenBatch, labels: DeletionLabels, *, provenance: LabelProvenance) -> dict[str, float | int]:
        if provenance.split != "train":
            raise ValueError("training cannot consume validation/test episodes")
        labels.validate_for(batch, labels.retained_mask, provenance)
        self.scale.validate(provenance)
        # Recheck graph boundary even if a caller mutated a frozen dataclass tensor.
        batch.__post_init__()
        self.estimator.train()
        self.optimizer.zero_grad(set_to_none=True)
        predicted = self.estimator(batch, labels.retained_mask).gather(1, labels.candidate_indices)
        target = labels.influence.detach().float() / self.scale.value
        loss, regression, ranking = signed_influence_loss(predicted, target, self.config)
        if not torch.isfinite(loss):
            raise FloatingPointError("non-finite loss; refusing optimizer update")
        loss.backward()
        norm = torch.nn.utils.clip_grad_norm_(self.estimator.parameters(), self.config.max_grad_norm, error_if_nonfinite=True)
        self.optimizer.step()
        return {"loss": loss.detach().item(), "regression": regression.item(), "ranking": ranking.item(),
                "grad_norm": norm.detach().item(), "labels": target.numel()}

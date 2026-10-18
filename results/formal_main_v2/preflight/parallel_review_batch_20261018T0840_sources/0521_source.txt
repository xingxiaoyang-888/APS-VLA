"""Scorer-only training, detached from the frozen VLA."""

from .conditional import ConditionalTrainConfig, ConditionalTrainer, TrainingLabelScale, signed_influence_loss

__all__ = ["ConditionalTrainConfig", "ConditionalTrainer", "TrainingLabelScale", "signed_influence_loss"]

"""Read-only checks required before scaling DIWA to the 7B server job."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable, Iterable, Mapping, Optional

import torch
from torch import nn

from diwa.data.contracts import TokenBatch
from diwa.models.influence.die import DecisionInfluenceEstimator


@dataclass(frozen=True)
class EquivalenceReport:
    max_abs_error: float
    mean_abs_error: float
    passed: bool


@dataclass(frozen=True)
class LatencyReport:
    median_ms: float
    p90_ms: float
    peak_memory_bytes: Optional[int]
    repetitions: int


def validate_openvla_oft_structure(
    vla: nn.Module,
    action_head: nn.Module,
    proprio_projector: nn.Module,
    *,
    action_chunk_size: int = 8,
    action_dim: int = 7,
) -> dict[str, str]:
    """Fail fast on checkpoint/component mismatches without running a forward."""

    language_model = getattr(vla, "language_model", None)
    backbone = getattr(language_model, "model", None)
    if not isinstance(backbone, nn.Module):
        raise ValueError("expected checkpoint path vla.language_model.model")
    embedding = vla.get_input_embeddings() if hasattr(vla, "get_input_embeddings") else None
    if not isinstance(embedding, nn.Module) or not any(module is embedding for module in backbone.modules()):
        raise ValueError("input embedding must belong to vla.language_model.model")
    if not callable(getattr(action_head, "predict_action", None)):
        raise ValueError("deterministic L1 action head must implement predict_action")
    if hasattr(action_head, "noise_scheduler"):
        raise ValueError("diffusion action head is forbidden in the primary DIWA configuration")
    if not isinstance(proprio_projector, nn.Module):
        raise TypeError("proprio_projector must be an nn.Module")
    if action_chunk_size != 8 or action_dim != 7:
        raise ValueError("primary LIBERO checkpoint requires action shape [8, 7]")
    return {
        "language_backbone": "vla.language_model.model",
        "action_head": action_head.__class__.__name__,
        "proprio_projector": proprio_projector.__class__.__name__,
        "action_shape": "8x7",
    }


def compare_action_outputs(
    reference: torch.Tensor,
    candidate: torch.Tensor,
    *,
    atol: float = 2e-3,
) -> EquivalenceReport:
    if reference.shape != candidate.shape or reference.ndim != 3:
        raise ValueError("equivalence inputs must share [B, K, action_dim] shape")
    if not reference.is_floating_point() or not candidate.is_floating_point():
        raise TypeError("equivalence inputs must be floating point")
    if reference.device != candidate.device or atol < 0:
        raise ValueError("equivalence inputs must share device and atol must be non-negative")
    if not torch.isfinite(reference).all() or not torch.isfinite(candidate).all():
        raise ValueError("equivalence inputs contain NaN/Inf")
    error = (reference.float() - candidate.float()).abs()
    max_error = float(error.max())
    return EquivalenceReport(
        max_abs_error=max_error,
        mean_abs_error=float(error.mean()),
        passed=max_error <= atol,
    )


@torch.inference_mode()
def content_permutation_audit(
    estimator: DecisionInfluenceEstimator,
    batch: TokenBatch,
    intervened_mask: torch.Tensor,
    permutation: torch.Tensor,
) -> dict[str, float]:
    """Detect metadata shortcuts by permuting token content within each sample."""

    if permutation.shape != batch.valid.shape or permutation.dtype != torch.long:
        raise ValueError("permutation must be long [B, N]")
    if permutation.device != batch.z.device:
        raise ValueError("permutation and TokenBatch must share device")
    expected = torch.arange(batch.num_tokens, device=permutation.device).expand_as(permutation)
    if not torch.equal(torch.sort(permutation, dim=1).values, expected):
        raise ValueError("each permutation row must contain every token index exactly once")
    gathered_valid = batch.valid.gather(1, permutation)
    gathered_intervened = intervened_mask.gather(1, permutation)
    if not torch.equal(gathered_valid, batch.valid) or not torch.equal(gathered_intervened, intervened_mask):
        raise ValueError("permutation must preserve valid/padding and intervened positions")
    original = estimator(batch, intervened_mask).float()
    gather = permutation.unsqueeze(-1).expand_as(batch.z)
    permuted_batch = TokenBatch(
        z=batch.z.gather(1, gather),
        token_type=batch.token_type,
        frame_id=batch.frame_id,
        camera_id=batch.camera_id,
        valid=batch.valid,
        query=batch.query,
        proprio=batch.proprio,
        diffusion_noise=batch.diffusion_noise,
    )
    permuted = estimator(permuted_batch, intervened_mask).float()
    valid_scores = batch.valid & ~intervened_mask
    mean_change = (original - permuted).abs()[valid_scores].mean()
    centered_original = original[valid_scores] - original[valid_scores].mean()
    centered_permuted = permuted[valid_scores] - permuted[valid_scores].mean()
    denominator = centered_original.norm() * centered_permuted.norm()
    correlation = torch.tensor(0.0, device=batch.z.device)
    if float(denominator) > 0:
        correlation = (centered_original * centered_permuted).sum() / denominator
    return {
        "content_permutation_mean_abs_change": float(mean_change),
        "content_permutation_score_correlation": float(correlation),
    }


@torch.inference_mode()
def measure_forward_latency(
    forward: Callable[[], torch.Tensor],
    modules: Iterable[nn.Module],
    *,
    warmup: int = 3,
    repetitions: int = 10,
) -> LatencyReport:
    if warmup < 0 or repetitions <= 0:
        raise ValueError("warmup must be non-negative and repetitions positive")
    modules = tuple(modules)
    prior_modes = [module.training for module in modules]
    for module in modules:
        module.eval()
    try:
        for _ in range(warmup):
            output = forward()
            if not isinstance(output, torch.Tensor):
                raise TypeError("latency forward must return a tensor")
        del output
        if torch.cuda.is_available():
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()
        timings = []
        for _ in range(repetitions):
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            start = time.perf_counter()
            output = forward()
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            timings.append((time.perf_counter() - start) * 1000.0)
            del output
        values = torch.tensor(timings, dtype=torch.float64)
        return LatencyReport(
            median_ms=float(values.median()),
            p90_ms=float(torch.quantile(values, 0.9)),
            peak_memory_bytes=torch.cuda.max_memory_allocated() if torch.cuda.is_available() else None,
            repetitions=repetitions,
        )
    finally:
        for module, training in zip(modules, prior_modes):
            module.train(training)


__all__ = [
    "EquivalenceReport",
    "LatencyReport",
    "compare_action_outputs",
    "content_permutation_audit",
    "measure_forward_latency",
    "validate_openvla_oft_structure",
]

"""G1-F CTI-DIE adaptation of ACL-style training, not native ACL reproduction.

A uses full-teacher and demonstrated normalized actions equally. B adds a
training-only future representation head. The VLA is frozen, but its student
forward remains differentiable with respect to gated visual inputs. This is a
separate experiment from signed-deletion-label CTI and the historical matched
baseline; it does not change either implementation or authorize a GPU run.

The existing conditional estimator is reused as an architecture, not as a
calibrated deletion-marginal predictor. Both variants score the current full512
observation once. Neither future features nor demonstrated actions enter DIE.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import torch
from torch import nn
from torch.nn import functional as F

from cti_vla.selection.conditional import (
    ConditionalInfluenceEstimator, ConditionalTokenBatch, StagedSelection, staged_topk,
)
from cti_vla_baselines.acl_matched import (
    FrozenDifferentiableOFTPolicy, gate_raw_tokens, soft_top_k,
)


FUTURE_TRAINING_VERSION = "g1f-cti-die-acl-soft128-half-teacher-half-gt-v1"
FUTURE_SELECTION_VERSION = "g1f-full512-single-top64-per-camera-v1"
FUTURE_TARGET_VERSION = "g1f-camera2-grid2x2-gaussian64-cell-layernorm-v1"
FUTURE_PROJECTION_SEED = 917
FUTURE_TARGET_DIM = 512


def validate_tokens_per_camera(tokens_per_camera: int = 64) -> int:
    """Only the two registered budgets; never silently reinterpret a checkpoint."""
    if type(tokens_per_camera) is not int or tokens_per_camera not in (32, 64):
        raise ValueError("G1-F tokens_per_camera must be exactly32 or64")
    return tokens_per_camera


def future_training_version(tokens_per_camera: int = 64) -> str:
    budget = validate_tokens_per_camera(tokens_per_camera)
    return FUTURE_TRAINING_VERSION if budget == 64 else "g1f-cti-die-acl-soft64-half-teacher-half-gt-v1"


def future_selection_version(tokens_per_camera: int = 64) -> str:
    budget = validate_tokens_per_camera(tokens_per_camera)
    return FUTURE_SELECTION_VERSION if budget == 64 else "g1f-full512-single-top32-per-camera-v1"


def _finite_float(value: torch.Tensor, name: str, *, detached: bool = False) -> None:
    if not isinstance(value, torch.Tensor) or not value.is_floating_point() or not torch.isfinite(value).all():
        raise ValueError(f"{name} must be a finite floating tensor")
    if detached and value.requires_grad:
        raise ValueError(f"{name} must be detached")


def _ordinary(value: torch.Tensor, name: str) -> torch.Tensor:
    if not isinstance(value, torch.Tensor):
        raise TypeError(f"{name} must be a tensor")
    if value.requires_grad:
        raise ValueError(f"{name} must be detached")
    if value.is_inference():
        with torch.inference_mode(False), torch.no_grad():
            return value.clone()
    return value


def validate_full_conditions(conditions: ConditionalTokenBatch) -> None:
    """Common soft/hard contract: two complete, camera-major 16x16 grids."""
    if not isinstance(conditions, ConditionalTokenBatch):
        raise TypeError("conditions must be ConditionalTokenBatch")
    b, n, _ = conditions.visual.shape
    if n != 512 or not bool(conditions.valid.all()):
        raise ValueError("G1-F requires all512 current tokens, not a partial set")
    if conditions.normalized_proprio.shape != (b, 8):
        raise ValueError("G1-F requires normalized proprio [B,8]")
    for name in ("visual", "instruction_embeddings", "normalized_proprio"):
        _finite_float(getattr(conditions, name), name, detached=True)
    cameras = torch.arange(2, device=conditions.visual.device).repeat_interleave(256)[None].expand(b, -1)
    patches = torch.arange(256, device=conditions.visual.device).repeat(2)[None].expand(b, -1)
    if not torch.equal(conditions.camera_ids, cameras) or not torch.equal(conditions.patch_ids, patches):
        raise ValueError("current tokens must retain original camera-major patch order")


@torch.no_grad()
def hard_select_future(scorer: ConditionalInfluenceEstimator,
                       conditions: ConditionalTokenBatch, *, tokens_per_camera: int = 64) -> StagedSelection:
    """Deployment path shared by A/B: one full-set score and registered top-k/view.

    Requires scorer.eval(). Ties use smaller original indices. The future head
    is absent from this API and no teacher, GT or future tensor is available.
    """
    validate_full_conditions(conditions)
    budget = validate_tokens_per_camera(tokens_per_camera)
    if not isinstance(scorer, ConditionalInfluenceEstimator):
        raise TypeError("G1-F requires the shared conditional estimator")
    return staged_topk(scorer, conditions, ((budget, budget),))


class FrozenFutureRepresentation(nn.Module):
    """Differentiable reducer with a fixed random projection and no parameters.

    Each view is pooled from16x16 to2x2 nonoverlapping8x8 cells. A shared
    Gaussian D->64 matrix is generated on CPU using a private seeded generator
    and divided by sqrt(D). Each cell uses non-affine LayerNorm(eps=1e-5),
    giving roughly unit variance per output component, not unit vector norm.
    Flatten order: camera, cell row, cell column, projected component.

    forward preserves current gated-input gradients; target explicitly blocks
    future gradients. The projection is a persistent buffer for checkpointing.
    """

    def __init__(self, projected_dim: int, *, projection_seed: int = FUTURE_PROJECTION_SEED):
        super().__init__()
        if type(projected_dim) is not int or projected_dim <= 0:
            raise ValueError("projected_dim must be positive")
        if type(projection_seed) is not int or not 0 <= projection_seed < 2**63:
            raise ValueError("projection_seed must be a nonnegative int64")
        self.projected_dim, self.projection_seed = projected_dim, projection_seed
        # Do not consume the scorer/optimizer's global RNG stream.
        with torch.inference_mode(False), torch.no_grad():
            generator = torch.Generator(device="cpu").manual_seed(projection_seed)
            projection = torch.randn(projected_dim, 64, generator=generator, dtype=torch.float32) / math.sqrt(projected_dim)
        self.register_buffer("projection", projection)

    def specification(self) -> dict:
        return {"version": FUTURE_TARGET_VERSION, "projected_dim": self.projected_dim,
                "projection_seed": self.projection_seed, "projection_dim_per_cell": 64,
                "num_cameras": 2, "patch_grid": [16, 16], "pooled_grid": [2, 2],
                "normalization": "per-cell non-affine LayerNorm", "normalization_eps": 1e-5,
                "target_dim": FUTURE_TARGET_DIM, "projection_scale": "1/sqrt(projected_dim)"}

    def forward(self, projected: torch.Tensor) -> torch.Tensor:
        _finite_float(projected, "projected visual features")
        if projected.ndim != 3 or projected.shape[1:] != (512, self.projected_dim) or projected.shape[0] <= 0:
            raise ValueError("future representation needs [B,512,projected_dim]")
        if projected.device != self.projection.device or self.projection.dtype != torch.float32:
            raise ValueError("fixed projection must be FP32 on the feature device")
        with torch.autocast(device_type=projected.device.type, enabled=False):
            b = projected.shape[0]
            # [B,camera,cell_row,within_row,cell_col,within_col,D]
            pooled = projected.float().reshape(b, 2, 2, 8, 2, 8, self.projected_dim).mean(dim=(3, 5))
            reduced = pooled @ self.projection
            normalized = F.layer_norm(reduced, (64,), eps=1e-5)
            return normalized.reshape(b, FUTURE_TARGET_DIM)

    def target(self, future_projected: torch.Tensor) -> torch.Tensor:
        _finite_float(future_projected, "future projected features", detached=True)
        with torch.inference_mode(False), torch.no_grad():
            return self(future_projected).clone()


def frozen_future_target(projected: torch.Tensor, *, projection_seed: int = FUTURE_PROJECTION_SEED) -> torch.Tensor:
    """Cache-producer helper: ordinary detached FP32 [B,512] future target.

    Reuse FrozenFutureRepresentation.target for many records to avoid repeatedly
    creating/transferring its deterministic matrix. It produces identical data.
    """
    if not isinstance(projected, torch.Tensor) or projected.ndim != 3:
        raise ValueError("future features must have shape [B,512,D]")
    with torch.inference_mode(False), torch.no_grad():
        reducer = FrozenFutureRepresentation(projected.shape[-1], projection_seed=projection_seed).to(projected.device)
        return reducer.target(projected)


class FutureAuxiliaryHead(nn.Module):
    """Training-only568->256->512 head; no language, proprio or ungated bypass."""

    def __init__(self, projected_dim: int, *, hidden_dim: int = 256,
                 projection_seed: int = FUTURE_PROJECTION_SEED):
        super().__init__()
        if type(hidden_dim) is not int or hidden_dim <= 0:
            raise ValueError("future head hidden_dim must be positive")
        self.representation = FrozenFutureRepresentation(projected_dim, projection_seed=projection_seed)
        self.predictor = nn.Sequential(nn.Linear(512 + 8 * 7, hidden_dim), nn.SiLU(), nn.Linear(hidden_dim, 512))

    def forward(self, gated_projected: torch.Tensor, executed_actions: torch.Tensor) -> torch.Tensor:
        _finite_float(executed_actions, "executed demonstration actions", detached=True)
        if executed_actions.shape != (gated_projected.shape[0], 8, 7) or executed_actions.device != gated_projected.device:
            raise ValueError("executed normalized actions must be [B,8,7] on the visual device")
        if self.predictor[0].weight.dtype != torch.float32:
            raise ValueError("future head trainable parameters must remain FP32")
        with torch.autocast(device_type=gated_projected.device.type, enabled=False):
            current = self.representation(gated_projected)
            return self.predictor(torch.cat((current, executed_actions.float().flatten(1)), dim=1))


@dataclass(frozen=True)
class FutureTrainingBatch:
    """One matched A/B batch. Temporal/split/provenance checks are runner-owned.

    The producer must supply real black-image features, not zeros/camera means;
    GT must use the same action normalization as the policy. The future target
    must be from this same-episode observation after the eight supplied actions.
    These semantic facts cannot be inferred from tensor shapes here.
    """
    conditions: ConditionalTokenBatch
    raw_tokens: torch.Tensor
    black_tokens: torch.Tensor
    input_ids: torch.Tensor
    attention_mask: torch.Tensor
    teacher_actions: torch.Tensor
    demonstration_actions: torch.Tensor
    future_target: torch.Tensor | None = None

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if name != "conditions" and value is not None:
                object.__setattr__(self, name, _ordinary(value, name))
        self.validate()

    def validate(self) -> None:
        validate_full_conditions(self.conditions)
        b = self.conditions.visual.shape[0]
        device = self.conditions.visual.device
        if self.raw_tokens.ndim != 3 or self.raw_tokens.shape[:2] != (b, 512) or self.raw_tokens.shape[-1] <= 0:
            raise ValueError("raw tokens must be complete [B,512,D_raw]")
        if self.black_tokens.shape != self.raw_tokens.shape or self.black_tokens.dtype != self.raw_tokens.dtype:
            raise ValueError("black-image raw features must match raw shape/dtype")
        for name in ("raw_tokens", "black_tokens", "teacher_actions", "demonstration_actions"):
            _finite_float(getattr(self, name), name, detached=True)
        for name in ("teacher_actions", "demonstration_actions"):
            if getattr(self, name).shape != (b, 8, 7):
                raise ValueError("teacher and demonstration actions must both be [B,8,7]")
        if self.future_target is not None:
            _finite_float(self.future_target, "future_target", detached=True)
            if self.future_target.shape != (b, FUTURE_TARGET_DIM) or self.future_target.dtype != torch.float32:
                raise ValueError("future_target must be FP32 [B,512]")
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if name != "conditions" and value is not None and value.device != device:
                raise ValueError("training tensors must share the condition device")
        # Validate prompt shape/padding before an expensive policy forward.
        from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
        OpenVLAOFTTokenPolicy._validate_prompt(self.input_ids, self.attention_mask, b)


@dataclass
class FutureLossOutput:
    loss: torch.Tensor
    action_loss: torch.Tensor
    teacher_l1: torch.Tensor
    demonstration_l1: torch.Tensor
    future_mse: torch.Tensor | None
    predicted_actions: torch.Tensor
    scores: torch.Tensor
    gates: torch.Tensor
    source_indices: torch.Tensor
    tokens_per_camera: int = 64

    def metrics(self) -> dict:
        return {"loss": float(self.loss.detach()), "action_loss": float(self.action_loss.detach()),
                "teacher_l1": float(self.teacher_l1.detach()),
                "demonstration_l1": float(self.demonstration_l1.detach()),
                "future_mse": None if self.future_mse is None else float(self.future_mse.detach()),
                "gate_mass_by_camera": self.gates.detach().reshape(-1, 2, 256).sum(-1).cpu().tolist(),
                "physical_student_visual_tokens": 512, "hard_deployment_visual_tokens": 2 * self.tokens_per_camera}


def future_auxiliary_loss(scorer: ConditionalInfluenceEstimator, student: FrozenDifferentiableOFTPolicy,
                          batch: FutureTrainingBatch, *, alpha: float,
                          auxiliary_head: FutureAuxiliaryHead | None = None,
                          auxiliary_weight: float = .1, projection_atol: float = 1e-5,
                          tokens_per_camera: int = 64) -> FutureLossOutput:
    """One differentiable loss; optimizer, accumulation, costs and resume are caller-owned.

    A and B have exactly the same scorer/action path and0.5/0.5 action objective.
    B adds auxiliary_weight*MSE over all512 target components. No action/future
    target is passed to the scorer. B's head receives only the already-gated
    current projected tensor and the actual normalized demonstration actions.
    """
    batch.validate()
    budget = validate_tokens_per_camera(tokens_per_camera)
    if not isinstance(scorer, ConditionalInfluenceEstimator) or not isinstance(student, FrozenDifferentiableOFTPolicy):
        raise TypeError("shared conditional estimator and differentiable frozen OFT student are required")
    if not math.isfinite(auxiliary_weight) or auxiliary_weight < 0 or not math.isfinite(projection_atol) or projection_atol < 0:
        raise ValueError("loss weight and projection tolerance must be finite and nonnegative")
    if auxiliary_head is not None and batch.future_target is None:
        raise ValueError("B requires a matched detached future_target")
    if auxiliary_head is not None and not isinstance(auxiliary_head, FutureAuxiliaryHead):
        raise TypeError("auxiliary_head must be FutureAuxiliaryHead")
    student.require_frozen()
    if not torch.is_grad_enabled():
        raise RuntimeError("G1-F training requires autograd through the frozen VLA inputs")
    conditions = batch.conditions
    with torch.no_grad():
        check = student.visual_projector(batch.raw_tokens)
        if check.shape != conditions.visual.shape or check.dtype != conditions.visual.dtype or not torch.allclose(check, conditions.visual, atol=projection_atol, rtol=0):
            raise ValueError("raw features do not project to the current cached conditions")
    scores = scorer(conditions, conditions.valid)
    if scores.shape != (conditions.visual.shape[0], 512) or not torch.isfinite(scores).all():
        raise ValueError("full-set scorer must return finite [B,512] scores")
    gates = torch.cat([soft_top_k(scores[:, c * 256:(c + 1) * 256], budget, alpha) for c in range(2)], dim=1)
    gated_raw = gate_raw_tokens(batch.raw_tokens, gates, batch.black_tokens)
    gated_projected = student.visual_projector(gated_raw)
    source = torch.arange(512, device=scores.device)[None].expand(scores.shape[0], -1)
    prediction = student(gated_projected, source, input_ids=batch.input_ids, attention_mask=batch.attention_mask,
                         normalized_proprio=conditions.normalized_proprio.to(gated_projected.dtype))
    teacher_l1 = (prediction.float() - batch.teacher_actions.float()).abs().mean()
    demonstration_l1 = (prediction.float() - batch.demonstration_actions.float()).abs().mean()
    action_loss = .5 * teacher_l1 + .5 * demonstration_l1
    future_mse = None
    loss = action_loss
    if auxiliary_head is not None:
        future_prediction = auxiliary_head(gated_projected, batch.demonstration_actions)
        future_mse = F.mse_loss(future_prediction, batch.future_target)
        loss = action_loss + auxiliary_weight * future_mse
    if not loss.requires_grad or not torch.isfinite(loss):
        raise RuntimeError("training loss must be finite and retain a scorer gradient path")
    student.require_frozen()
    return FutureLossOutput(loss, action_loss, teacher_l1, demonstration_l1, future_mse,
                            prediction, scores, gates, source, budget)

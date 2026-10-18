"""New CTI-VLA conditional scorer; no world-model or VLA dependency."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn

from cti_vla.models.abstraction.packing import retained_indices


@dataclass(frozen=True)
class ConditionalTokenBatch:
    """Frozen features in original visual order, before any deletion.

    ``instruction_embeddings`` come from the frozen token embedding table, not
    a pooled language-model output. ``patch_ids`` retain original camera-local
    patch positions. Proprio must already use the checkpoint's normalization.
    """

    visual: torch.Tensor
    instruction_embeddings: torch.Tensor
    instruction_mask: torch.Tensor
    normalized_proprio: torch.Tensor
    camera_ids: torch.Tensor
    patch_ids: torch.Tensor
    valid: torch.Tensor

    def __post_init__(self) -> None:
        # inference_mode outputs are detached but cannot be saved by autograd,
        # including boolean masks and embedding indices. Materialize ordinary
        # frozen inputs once so scorer training can safely save them backward.
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if not isinstance(value, torch.Tensor):
                raise TypeError(f"{name} must be a tensor")
            if value.is_inference():
                with torch.inference_mode(False), torch.no_grad():
                    object.__setattr__(self, name, value.clone())
        if self.visual.ndim != 3 or min(self.visual.shape) <= 0:
            raise ValueError("visual must be nonempty floating [B, N, D]")
        b, n, _ = self.visual.shape
        if self.instruction_embeddings.ndim != 3 or self.instruction_embeddings.shape[0] != b:
            raise ValueError("instruction_embeddings must be [B, L, D_language]")
        if min(self.instruction_embeddings.shape) <= 0:
            raise ValueError("instruction_embeddings cannot be empty")
        if self.instruction_mask.shape != self.instruction_embeddings.shape[:2] or self.instruction_mask.dtype != torch.bool:
            raise ValueError("instruction_mask must be bool [B, L]")
        if self.normalized_proprio.ndim != 2 or self.normalized_proprio.shape[0] != b or self.normalized_proprio.shape[1] <= 0:
            raise ValueError("normalized_proprio must be [B, P]")
        for name in ("visual", "instruction_embeddings", "normalized_proprio"):
            value = getattr(self, name)
            if not value.is_floating_point() or not torch.isfinite(value).all():
                raise ValueError(f"{name} must be finite floating point")
            if value.requires_grad:
                raise ValueError(f"{name} must be detached from VLA/teacher graphs")
        for name, dtype in (("camera_ids", torch.long), ("patch_ids", torch.long), ("valid", torch.bool)):
            value = getattr(self, name)
            if value.shape != (b, n) or value.dtype != dtype:
                raise ValueError(f"{name} has invalid shape or dtype")
        if any(getattr(self, name).device != self.visual.device for name in self.__dataclass_fields__):
            raise ValueError("all condition tensors must share a device")
        if not self.valid.any(1).all() or not self.instruction_mask.any(1).all():
            raise ValueError("each sample needs visual tokens and instruction tokens")
        for name in ("camera_ids", "patch_ids"):
            if (getattr(self, name)[self.valid] < 0).any():
                raise ValueError(f"valid {name} must be nonnegative")
        for row in range(b):
            ids = torch.stack((self.camera_ids[row, self.valid[row]], self.patch_ids[row, self.valid[row]]), 1)
            if ids.unique(dim=0).shape[0] != ids.shape[0]:
                raise ValueError("camera/patch coordinates must be unique per sample")

    def validate_retained(self, retained: torch.Tensor) -> None:
        if retained.shape != self.valid.shape or retained.dtype != torch.bool or retained.device != self.visual.device:
            raise ValueError("retained must be bool [B, N] on the feature device")
        if (retained & ~self.valid).any() or not retained.any(1).all():
            raise ValueError("retained must be a nonempty subset of valid visual tokens")


class ConditionalInfluenceEstimator(nn.Module):
    """Signed deletion increment, conditioned on language, proprio and S.

    The small positional language encoder is trainable. Its source embeddings
    are detached by the batch contract. All scores use original token slots;
    inactive scores are zero and must be masked before ranking.
    """

    def __init__(self, token_dim: int, language_dim: int, proprio_dim: int, *, hidden_dim: int = 256,
                 num_cameras: int = 2, patches_per_camera: int = 256, max_instruction_tokens: int = 128) -> None:
        super().__init__()
        dims = (token_dim, language_dim, proprio_dim, hidden_dim, num_cameras, patches_per_camera, max_instruction_tokens)
        if any(type(x) is not int or x <= 0 for x in dims):
            raise ValueError("all dimensions must be positive integers")
        self.token_dim, self.language_dim, self.proprio_dim = token_dim, language_dim, proprio_dim
        self.num_cameras, self.patches_per_camera = num_cameras, patches_per_camera
        self.max_instruction_tokens = max_instruction_tokens
        self.visual_projection = nn.Sequential(nn.LayerNorm(token_dim), nn.Linear(token_dim, hidden_dim))
        self.camera_embedding = nn.Embedding(num_cameras, hidden_dim)
        self.patch_embedding = nn.Embedding(patches_per_camera, hidden_dim)
        self.language_projection = nn.Linear(language_dim, hidden_dim)
        self.language_position = nn.Embedding(max_instruction_tokens, hidden_dim)
        # Nonlinearity BEFORE pooling ensures that instruction order can matter.
        self.language_encoder = nn.Sequential(nn.SiLU(), nn.Linear(hidden_dim, hidden_dim), nn.SiLU())
        self.proprio_encoder = nn.Sequential(nn.Linear(proprio_dim, hidden_dim), nn.SiLU(), nn.Linear(hidden_dim, hidden_dim))
        self.set_projection = nn.Linear(2 * num_cameras * hidden_dim, hidden_dim)
        self.ratio_projection = nn.Linear(1, hidden_dim)
        self.output = nn.Sequential(nn.LayerNorm(hidden_dim), nn.Linear(hidden_dim, hidden_dim), nn.SiLU(), nn.Linear(hidden_dim, 1))

    def encode_instruction(self, embeddings: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        length = embeddings.shape[1]
        if length > self.max_instruction_tokens:
            raise ValueError("instruction exceeds configured positional capacity")
        parameter = self.language_projection.weight
        positions = torch.arange(length, device=embeddings.device)
        encoded = self.language_encoder(self.language_projection(embeddings.detach().to(parameter.dtype)) + self.language_position(positions))
        return (encoded * mask[..., None]).sum(1) / mask.sum(1, keepdim=True)

    def forward(self, batch: ConditionalTokenBatch, retained: torch.Tensor) -> torch.Tensor:
        batch.validate_retained(retained)
        if (batch.visual.shape[-1], batch.instruction_embeddings.shape[-1], batch.normalized_proprio.shape[-1]) != (self.token_dim, self.language_dim, self.proprio_dim):
            raise ValueError("feature dimensions do not match the estimator")
        if (batch.camera_ids[batch.valid] >= self.num_cameras).any() or (batch.patch_ids[batch.valid] >= self.patches_per_camera).any():
            raise ValueError("camera/patch coordinate exceeds configured capacity")
        dtype = self.visual_projection[1].weight.dtype
        # Explicit detach also protects callers that mutate tensors after construction.
        u = self.visual_projection(batch.visual.detach().to(dtype))
        u = u + self.camera_embedding(batch.camera_ids.masked_fill(~batch.valid, 0))
        u = u + self.patch_embedding(batch.patch_ids.masked_fill(~batch.valid, 0))
        summaries = []
        for camera in range(self.num_cameras):
            active = retained & (batch.camera_ids == camera)
            count = active.sum(1, keepdim=True)
            mean = (u * active[..., None]).sum(1) / count.clamp_min(1)
            maximum = u.masked_fill(~active[..., None], -torch.inf).amax(1)
            maximum = torch.where(count > 0, maximum, torch.zeros_like(maximum))
            summaries.extend((mean, maximum))
        context = self.set_projection(torch.cat(summaries, -1))
        context = context + self.encode_instruction(batch.instruction_embeddings, batch.instruction_mask)
        context = context + self.proprio_encoder(batch.normalized_proprio.detach().to(dtype))
        ratio = retained.sum(1, keepdim=True).to(dtype) / batch.valid.sum(1, keepdim=True)
        context = context + self.ratio_projection(ratio)
        scores = self.output(u + context[:, None]).squeeze(-1)
        return scores.masked_fill(~retained, 0.0)


@dataclass(frozen=True)
class StagedSelection:
    source_indices: torch.Tensor
    retained_mask: torch.Tensor
    stage_masks: tuple[torch.Tensor, ...]


@torch.no_grad()
def staged_topk(estimator: nn.Module, batch: ConditionalTokenBatch, camera_budgets: tuple[tuple[int, ...], ...]) -> StagedSelection:
    """Re-score S at each fixed per-camera budget, then return original order.

    E.g. for two 256-patch cameras: ((128,128), (64,64), (32,32)).
    Scores are signed removal costs; high scores survive. Equal scores use
    smaller original sequence indices deterministically.
    """
    if estimator.training:
        raise ValueError("selection requires estimator.eval()")
    if not camera_budgets:
        raise ValueError("at least one stage is required")
    cameras = len(camera_budgets[0])
    if cameras == 0 or (batch.camera_ids[batch.valid] >= cameras).any():
        raise ValueError("budgets must cover every camera")
    retained = batch.valid.clone()
    stages = []
    for budgets in camera_budgets:
        if len(budgets) != cameras or any(type(k) is not int or k <= 0 for k in budgets):
            raise ValueError("each stage needs positive integer budgets for every camera")
        scores = estimator(batch, retained)
        if scores.shape != retained.shape or not torch.isfinite(scores[retained]).all():
            raise ValueError("scorer must return finite scores for retained visual tokens")
        next_retained = torch.zeros_like(retained)
        for camera, k in enumerate(budgets):
            eligible = retained & (batch.camera_ids == camera)
            if (eligible.sum(1) < k).any():
                raise ValueError("stage budget exceeds current per-camera retained count")
            order = torch.argsort(scores.masked_fill(~eligible, -torch.inf), dim=1, descending=True, stable=True)[:, :k]
            next_retained.scatter_(1, order, True)
        retained = next_retained
        stages.append(retained.clone())
    source = retained_indices(retained)
    return StagedSelection(source, retained, tuple(stages))

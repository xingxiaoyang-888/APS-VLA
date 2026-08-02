"""Memory-conscious conditional decision influence estimator."""

from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn

from diwa.data.contracts import TokenBatch


class DecisionInfluenceEstimator(nn.Module):
    """Predicts marginal removal influence conditioned on prior interventions.

    `intervened_mask=True` means that a token has already been replaced by its
    matched baseline. Pooling therefore summarizes the valid surviving tokens.
    """

    def __init__(
        self,
        token_dim: int,
        query_dim: int,
        hidden_dim: int = 256,
        num_token_types: int = 8,
        num_frames: int = 16,
        num_cameras: int = 8,
        metadata_dim: int = 32,
        dropout: float = 0.0,
    ) -> None:
        super().__init__()
        for name, value in (
            ("token_dim", token_dim),
            ("query_dim", query_dim),
            ("hidden_dim", hidden_dim),
            ("num_token_types", num_token_types),
            ("num_frames", num_frames),
            ("num_cameras", num_cameras),
            ("metadata_dim", metadata_dim),
        ):
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if not 0.0 <= dropout < 1.0:
            raise ValueError("dropout must be in [0, 1)")

        self.token_dim = token_dim
        self.query_dim = query_dim
        self.num_token_types = num_token_types
        self.num_frames = num_frames
        self.num_cameras = num_cameras

        self.token_norm = nn.LayerNorm(token_dim)
        self.token_proj = nn.Linear(token_dim, hidden_dim)
        self.context_proj = nn.Linear(token_dim, hidden_dim)
        self.query_proj = nn.Linear(query_dim, hidden_dim)
        self.ratio_proj = nn.Sequential(nn.Linear(1, hidden_dim), nn.SiLU())
        self.type_embedding = nn.Embedding(num_token_types, metadata_dim)
        self.frame_embedding = nn.Embedding(num_frames, metadata_dim)
        self.camera_embedding = nn.Embedding(num_cameras, metadata_dim)
        self.metadata_proj = nn.Linear(3 * metadata_dim, hidden_dim)
        self.output = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, 1),
        )

    @staticmethod
    def _check_index_range(name: str, values: torch.Tensor, valid: torch.Tensor, upper: int) -> None:
        checked = values[valid]
        if checked.numel() == 0:
            raise ValueError(f"{name} cannot be empty")
        if bool((checked < 0).any()) or bool((checked >= upper).any()):
            raise ValueError(f"{name} values must be in [0, {upper})")

    def forward(self, batch: TokenBatch, intervened_mask: torch.Tensor) -> torch.Tensor:
        if batch.hidden_dim != self.token_dim:
            raise ValueError(f"TokenBatch hidden dim {batch.hidden_dim} != estimator token_dim {self.token_dim}")
        if batch.query.shape[1] != self.query_dim:
            raise ValueError(f"query dim {batch.query.shape[1]} != estimator query_dim {self.query_dim}")
        if intervened_mask.shape != batch.valid.shape or intervened_mask.dtype != torch.bool:
            raise ValueError("intervened_mask must be bool [B, N]")
        if intervened_mask.device != batch.z.device:
            raise ValueError("intervened_mask and tokens must share device")
        if bool((intervened_mask & ~batch.valid).any()):
            raise ValueError("invalid/padded tokens cannot be marked as intervened")
        self._check_index_range("token_type", batch.token_type, batch.valid, self.num_token_types)
        self._check_index_range("frame_id", batch.frame_id, batch.valid, self.num_frames)
        self._check_index_range("camera_id", batch.camera_id, batch.valid, self.num_cameras)

        surviving = batch.valid & ~intervened_mask
        if not bool(surviving.any(dim=1).all()):
            raise ValueError("each sample must retain at least one surviving token")
        weights = surviving.unsqueeze(-1).to(dtype=batch.z.dtype)
        context = (batch.z * weights).sum(dim=1) / weights.sum(dim=1).clamp_min(1.0)
        removed_ratio = intervened_mask.sum(dim=1, keepdim=True).to(batch.z.dtype)
        removed_ratio = removed_ratio / batch.valid.sum(dim=1, keepdim=True).clamp_min(1).to(batch.z.dtype)

        # Padding metadata is often -1. It is never scored, but must be remapped
        # before embedding lookup to avoid negative/out-of-range indexing.
        safe_type = batch.token_type.masked_fill(~batch.valid, 0)
        safe_frame = batch.frame_id.masked_fill(~batch.valid, 0)
        safe_camera = batch.camera_id.masked_fill(~batch.valid, 0)
        metadata = torch.cat(
            (
                self.type_embedding(safe_type),
                self.frame_embedding(safe_frame),
                self.camera_embedding(safe_camera),
            ),
            dim=-1,
        )
        # Additive conditioning avoids materializing repeated context/query tensors
        # inside one large concatenated [B, N, feature_dim] activation.
        hidden = self.token_proj(self.token_norm(batch.z))
        hidden = hidden + self.context_proj(context).unsqueeze(1)
        hidden = hidden + self.query_proj(batch.query).unsqueeze(1)
        hidden = hidden + self.ratio_proj(removed_ratio).unsqueeze(1)
        hidden = hidden + self.metadata_proj(metadata)
        raw = self.output(hidden).squeeze(-1)
        scores = F.softplus(raw.float()).to(dtype=raw.dtype)
        return scores.masked_fill(~batch.valid | intervened_mask, 0.0)


__all__ = ["DecisionInfluenceEstimator"]

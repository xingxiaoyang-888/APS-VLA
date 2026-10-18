"""Actual-deletion supervision relative to the same full teacher action."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Callable

import torch
from torch import nn

from cti_vla.models.abstraction.packing import retained_indices
from cti_vla.selection import ConditionalTokenBatch


LABEL_VERSION = "cti-signed-deletion-l1-v1"


@dataclass(frozen=True)
class LabelProvenance:
    sample_ids: tuple[str, ...]
    episode_ids: tuple[str, ...]
    split: str
    model_revision: str
    dataset_version: str
    preprocessing_version: str
    packing_version: str
    condition_version: str
    action_version: str
    label_version: str = LABEL_VERSION

    def __post_init__(self) -> None:
        if self.split not in {"train", "validation", "test"}:
            raise ValueError("split must be train, validation or test")
        if not self.sample_ids or len(self.episode_ids) != len(self.sample_ids):
            raise ValueError("sample and episode identities must be nonempty and aligned")
        values = (*self.sample_ids, *self.episode_ids, self.model_revision, self.dataset_version,
                  self.preprocessing_version, self.packing_version, self.condition_version, self.action_version)
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("all provenance identities and versions must be nonempty strings")
        if self.label_version != LABEL_VERSION:
            raise ValueError("historical replacement labels are incompatible with deletion supervision")


def feature_fingerprint(batch: ConditionalTokenBatch) -> str:
    """Digest exact frozen contents and token coordinates, including conditions.

    This is an offline cache integrity check, not part of timed deployment.
    Dtype and shape are included; bfloat16 is hashed without float conversion.
    """
    digest = hashlib.sha256()
    for name in batch.__dataclass_fields__:
        tensor = getattr(batch, name).detach().cpu().contiguous()
        digest.update(f"{name}:{tensor.dtype}:{tuple(tensor.shape)};".encode())
        digest.update(tensor.view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


@dataclass(frozen=True)
class FullTeacherReference:
    """Reuse one full forward across multiple retained sets of the same batch."""

    action: torch.Tensor
    provenance: LabelProvenance
    feature_sha256: str

    def validate_for(self, batch: ConditionalTokenBatch, provenance: LabelProvenance, action_shape: tuple[int, int]) -> None:
        if self.provenance != provenance or self.feature_sha256 != feature_fingerprint(batch):
            raise ValueError("full teacher reference has stale provenance/features/conditions")
        if self.action.shape != (batch.visual.shape[0], *action_shape) or self.action.device != batch.visual.device:
            raise ValueError("full teacher reference has wrong shape/device")
        if not self.action.is_floating_point() or not torch.isfinite(self.action).all() or self.action.requires_grad:
            raise ValueError("full teacher reference must be finite floating point and detached")


@dataclass(frozen=True)
class DeletionLabels:
    """One S per row, all candidate indices refer to the original full sequence."""

    retained_mask: torch.Tensor
    candidate_indices: torch.Tensor
    influence: torch.Tensor
    base_error: torch.Tensor
    deleted_error: torch.Tensor
    full_action: torch.Tensor
    provenance: LabelProvenance
    feature_sha256: str
    teacher_calls: int

    def __post_init__(self) -> None:
        for name in ("retained_mask", "candidate_indices", "influence", "base_error", "deleted_error", "full_action"):
            value = getattr(self, name)
            if not isinstance(value, torch.Tensor):
                raise TypeError(f"{name} must be a tensor")
            if value.is_inference():
                with torch.inference_mode(False), torch.no_grad():
                    object.__setattr__(self, name, value.clone())
        if self.retained_mask.ndim != 2 or self.retained_mask.dtype != torch.bool:
            raise ValueError("retained_mask must be bool [B, N]")
        b, n = self.retained_mask.shape
        if min(b, n) <= 0 or not self.retained_mask.any(1).all():
            raise ValueError("label sets must be nonempty")
        if self.candidate_indices.ndim != 2 or self.candidate_indices.shape[0] != b or self.candidate_indices.dtype != torch.long:
            raise ValueError("candidate_indices must be long [B, C]")
        if self.candidate_indices.shape[1] <= 0:
            raise ValueError("each row needs at least one candidate")
        if len(self.provenance.sample_ids) != b:
            raise ValueError("provenance sample count differs from labels")
        if len(self.feature_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.feature_sha256):
            raise ValueError("feature_sha256 must be a SHA256 hex digest")
        expected = self.candidate_indices.shape
        for name, shape in (("influence", expected), ("deleted_error", expected), ("base_error", (b,))):
            value = getattr(self, name)
            if value.shape != shape or not value.is_floating_point() or not torch.isfinite(value).all() or value.requires_grad:
                raise ValueError(f"{name} must have expected shape, be finite floating point and detached")
        if self.full_action.ndim != 3 or self.full_action.shape[0] != b or min(self.full_action.shape) <= 0:
            raise ValueError("full_action must be nonempty [B, chunk, action]")
        if not self.full_action.is_floating_point() or not torch.isfinite(self.full_action).all() or self.full_action.requires_grad:
            raise ValueError("full_action must be finite floating point and detached")
        tensors = (self.candidate_indices, self.influence, self.base_error, self.deleted_error, self.full_action)
        if any(value.device != self.retained_mask.device for value in tensors):
            raise ValueError("all cached label tensors must share a device")
        if (self.candidate_indices < 0).any() or (self.candidate_indices >= n).any():
            raise ValueError("candidate index outside original sequence")
        if not self.retained_mask.gather(1, self.candidate_indices).all():
            raise ValueError("label candidate must belong to its retained set")
        if (self.retained_mask.sum(1) <= 1).any():
            raise ValueError("deleting one candidate must retain at least one visual token")
        for row in self.candidate_indices:
            if row.unique().numel() != row.numel():
                raise ValueError("candidate indices must be unique within a set")
        if (self.base_error < 0).any() or (self.deleted_error < 0).any():
            raise ValueError("action errors must be nonnegative")
        if not torch.allclose(self.influence, self.deleted_error - self.base_error[:, None], rtol=1e-5, atol=1e-7):
            raise ValueError("labels must equal E(S-i)-E(S), including negative increments")
        if type(self.teacher_calls) is not int or self.teacher_calls not in {expected[1], expected[1] + 1, expected[1] + 2}:
            raise ValueError("teacher_calls must count executed full/base/deletion calls; a cached reference costs no new call")

    @property
    def teacher_calls_per_observation(self) -> int:
        """Each observation participates once in every batched teacher call."""
        return self.teacher_calls

    @property
    def teacher_sample_forwards(self) -> int:
        """Executed per-observation forward count, including all B observations."""
        return self.teacher_calls * self.retained_mask.shape[0]

    def validate_for(self, batch: ConditionalTokenBatch, retained: torch.Tensor, provenance: LabelProvenance) -> None:
        self.__post_init__()
        batch.validate_retained(retained)
        if provenance != self.provenance:
            raise ValueError("cache provenance mismatch: model/data/condition/packing/episode/split changed")
        if not torch.equal(retained, self.retained_mask):
            raise ValueError("cache retained set mismatch")
        if feature_fingerprint(batch) != self.feature_sha256:
            raise ValueError("cache visual/condition/token-coordinate fingerprint mismatch")


class DeletionTeacher:
    """No-gradient sequential teacher with a shared retained-index adapter.

    ``forward_retained(batch, indices)`` MUST call the same real packing and
    policy path used by deployment. Indices are sorted original coordinates;
    neither masking nor feature replacement implements this contract. The
    policy module is supplied separately to enforce frozen eval mode.
    """

    def __init__(self, policy: nn.Module,
                 forward_retained: Callable[[ConditionalTokenBatch, torch.Tensor], torch.Tensor], *,
                 action_shape: tuple[int, int] = (8, 7)) -> None:
        if not isinstance(policy, nn.Module) or not callable(forward_retained):
            raise TypeError("teacher requires a policy module and retained-index callback")
        if len(action_shape) != 2 or any(type(x) is not int or x <= 0 for x in action_shape):
            raise ValueError("action_shape must be positive (chunk, action_dim)")
        self.policy, self.forward_retained, self.action_shape = policy, forward_retained, action_shape

    def _validate_policy(self) -> None:
        if any(module.training for module in self.policy.modules()) or any(p.requires_grad for p in self.policy.parameters()):
            raise ValueError("teacher requires every policy module frozen and in eval mode")

    def _action(self, batch: ConditionalTokenBatch, mask: torch.Tensor) -> torch.Tensor:
        output = self.forward_retained(batch, retained_indices(mask))
        shape = (batch.visual.shape[0], *self.action_shape)
        if not isinstance(output, torch.Tensor) or output.shape != shape or not output.is_floating_point():
            raise ValueError(f"teacher action must be floating {shape}")
        if output.device != batch.visual.device or not torch.isfinite(output).all():
            raise ValueError("teacher action must be finite and on the feature device")
        return output.detach().float().clone()

    @torch.no_grad()
    def reference(self, batch: ConditionalTokenBatch, provenance: LabelProvenance) -> FullTeacherReference:
        """Costs one teacher call; account for it once per observation batch."""
        self._validate_policy()
        if len(provenance.sample_ids) != batch.visual.shape[0]:
            raise ValueError("provenance sample count differs from feature batch")
        return FullTeacherReference(self._action(batch, batch.valid), provenance, feature_fingerprint(batch))

    @torch.no_grad()
    def label(self, batch: ConditionalTokenBatch, retained: torch.Tensor,
              candidate_indices: torch.Tensor, provenance: LabelProvenance, *,
              full_reference: FullTeacherReference | None = None) -> DeletionLabels:
        self._validate_policy()
        batch.validate_retained(retained)
        b, n = retained.shape
        if len(provenance.sample_ids) != b:
            raise ValueError("provenance sample count differs from feature batch")
        if candidate_indices.ndim != 2 or candidate_indices.shape[0] != b or candidate_indices.shape[1] <= 0 or candidate_indices.dtype != torch.long:
            raise ValueError("candidate_indices must be nonempty long [B, C]")
        if candidate_indices.device != retained.device or (candidate_indices < 0).any() or (candidate_indices >= n).any():
            raise ValueError("invalid candidate indices/device")
        if not retained.gather(1, candidate_indices).all() or (retained.sum(1) < 2).any():
            raise ValueError("candidates must belong to S and leave a nonempty visual set")
        for row in candidate_indices:
            if row.unique().numel() != row.numel():
                raise ValueError("duplicate deletion candidates")
        # Validate all bucket sizes before incurring any teacher cost.
        retained_indices(batch.valid)
        retained_indices(retained)
        if full_reference is None:
            full = self._action(batch, batch.valid)
        else:
            full_reference.validate_for(batch, provenance, self.action_shape)
            full = full_reference.action.detach().float().clone()
        same_as_full = torch.equal(retained, batch.valid)
        base = full if same_as_full else self._action(batch, retained)
        base_error = (base - full).abs().mean((1, 2))
        deleted_errors = []
        for slot in range(candidate_indices.shape[1]):
            reduced = retained.clone()
            reduced.scatter_(1, candidate_indices[:, slot:slot + 1], False)
            deleted = self._action(batch, reduced)
            deleted_errors.append((deleted - full).abs().mean((1, 2)))
        deleted_error = torch.stack(deleted_errors, 1)
        return DeletionLabels(
            retained.clone(), candidate_indices.clone(), deleted_error - base_error[:, None], base_error,
            deleted_error, full, provenance, feature_fingerprint(batch),
            candidate_indices.shape[1] + int(full_reference is None) + int(not same_as_full),
        )

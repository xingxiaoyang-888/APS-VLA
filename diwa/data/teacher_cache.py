"""Bounded, activation-free cache shards for counterfactual teacher targets."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

import torch

if TYPE_CHECKING:
    from diwa.models.influence.sampling import CandidateSet
    from diwa.models.influence.teacher import CandidateTeacherTargets


CACHE_SCHEMA_VERSION = 1
MAX_SAMPLES_PER_SHARD = 4096
MAX_CANDIDATES_PER_SAMPLE = 16


@dataclass(frozen=True)
class TeacherCacheManifest:
    data_signature: str
    policy_signature: str
    baseline_signature: str
    estimand: str = "normalized_action_chunk_huber"
    action_chunk_size: int = 8
    action_dim: int = 7
    huber_delta: float = 1.0
    schema_version: int = CACHE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("data_signature", "policy_signature", "baseline_signature", "estimand"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.action_chunk_size <= 0 or self.action_dim <= 0 or self.huber_delta <= 0:
            raise ValueError("action shape and huber_delta must be positive")
        if self.schema_version != CACHE_SCHEMA_VERSION:
            raise ValueError(f"unsupported cache schema version {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "data_signature": self.data_signature,
            "policy_signature": self.policy_signature,
            "baseline_signature": self.baseline_signature,
            "estimand": self.estimand,
            "action_chunk_size": self.action_chunk_size,
            "action_dim": self.action_dim,
            "huber_delta": self.huber_delta,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TeacherCacheManifest":
        required = set(cls.__dataclass_fields__)
        if set(value) != required:
            raise ValueError(f"cache manifest keys must be exactly {sorted(required)}")
        return cls(**dict(value))


@dataclass(frozen=True)
class TeacherCacheShard:
    sample_id: torch.Tensor
    source_indices: torch.Tensor
    source_kind: torch.Tensor
    influence: torch.Tensor
    valid_candidates: torch.Tensor
    base_intervened_count: torch.Tensor
    eligible_count: torch.Tensor

    def __post_init__(self) -> None:
        tensor_values = (
            self.sample_id,
            self.source_indices,
            self.source_kind,
            self.influence,
            self.valid_candidates,
            self.base_intervened_count,
            self.eligible_count,
        )
        if any(not isinstance(value, torch.Tensor) for value in tensor_values):
            raise TypeError("all TeacherCacheShard fields must be tensors")
        if self.sample_id.ndim != 1 or self.sample_id.dtype != torch.long:
            raise ValueError("sample_id must be long [S]")
        samples = self.sample_id.shape[0]
        if not 0 < samples <= MAX_SAMPLES_PER_SHARD:
            raise ValueError(f"shard samples must be in [1, {MAX_SAMPLES_PER_SHARD}]")
        if self.sample_id.unique().numel() != samples:
            raise ValueError("sample_id values must be unique within a shard")
        if self.source_indices.ndim != 2 or self.source_indices.shape[0] != samples:
            raise ValueError("source_indices must be [S, C]")
        candidates = self.source_indices.shape[1]
        if not 0 < candidates <= MAX_CANDIDATES_PER_SAMPLE:
            raise ValueError(f"candidate count must be in [1, {MAX_CANDIDATES_PER_SAMPLE}]")
        expected = (samples, candidates)
        if self.source_indices.dtype != torch.long or self.source_kind.shape != expected or self.source_kind.dtype != torch.long:
            raise ValueError("source_indices/source_kind must be long [S, C]")
        if self.influence.shape != expected or self.influence.dtype != torch.float32:
            raise ValueError("influence must be fp32 [S, C]")
        if self.valid_candidates.shape != expected or self.valid_candidates.dtype != torch.bool:
            raise ValueError("valid_candidates must be bool [S, C]")
        for name, value in (
            ("base_intervened_count", self.base_intervened_count),
            ("eligible_count", self.eligible_count),
        ):
            if value.shape != (samples,) or value.dtype != torch.long:
                raise ValueError(f"{name} must be long [S]")
        tensors = self.tensor_dict().values()
        if any(value.device.type != "cpu" for value in tensors):
            raise ValueError("cache shards must own detached CPU tensors only")
        if any(value.requires_grad for value in tensors):
            raise ValueError("cache shards cannot retain autograd tensors")
        if not torch.isfinite(self.influence).all() or bool((self.influence < 0).any()):
            raise ValueError("influence must be finite and non-negative")
        if bool((self.influence[~self.valid_candidates] != 0).any()):
            raise ValueError("invalid candidate slots must have zero influence")
        if bool((self.source_indices[self.valid_candidates] < 0).any()):
            raise ValueError("valid candidate source indices must be non-negative")
        if bool((self.source_indices[~self.valid_candidates] != -1).any()):
            raise ValueError("invalid candidate source index must be -1")
        if bool((self.source_kind[~self.valid_candidates] != -1).any()):
            raise ValueError("invalid candidate source kind must be -1")
        if bool((self.source_kind[self.valid_candidates] < 0).any()) or bool(
            (self.source_kind[self.valid_candidates] > 3).any()
        ):
            raise ValueError("candidate source kind is out of range")
        if bool((self.base_intervened_count < 0).any()) or bool((self.eligible_count <= 0).any()):
            raise ValueError("intervened/eligible counts are out of range")
        if bool((self.base_intervened_count >= self.eligible_count).any()):
            raise ValueError("base_intervened_count must leave at least one eligible token")

    @classmethod
    def from_targets(
        cls,
        sample_id: torch.Tensor,
        candidates: CandidateSet,
        targets: CandidateTeacherTargets,
    ) -> "TeacherCacheShard":
        if sample_id.shape != (candidates.masks.shape[0],) or sample_id.dtype != torch.long:
            raise ValueError("sample_id must be long [B]")
        if not torch.equal(candidates.source_indices, targets.source_indices):
            raise ValueError("candidate and teacher source indices disagree")
        if not torch.equal(candidates.valid_candidates, targets.valid_candidates):
            raise ValueError("candidate and teacher validity masks disagree")

        def cpu(value: torch.Tensor, dtype: torch.dtype | None = None) -> torch.Tensor:
            result = value.detach()
            if dtype is not None:
                result = result.to(dtype=dtype)
            return result.to(device="cpu", copy=True).contiguous()

        return cls(
            sample_id=cpu(sample_id, torch.long),
            source_indices=cpu(targets.source_indices, torch.long),
            source_kind=cpu(candidates.source_kind, torch.long),
            influence=cpu(targets.influence, torch.float32),
            valid_candidates=cpu(targets.valid_candidates, torch.bool),
            base_intervened_count=cpu(targets.base_intervened_count, torch.long),
            eligible_count=cpu(candidates.eligible_count, torch.long),
        )

    @property
    def estimated_bytes(self) -> int:
        return sum(value.numel() * value.element_size() for value in self.tensor_dict().values())

    def tensor_dict(self) -> dict[str, torch.Tensor]:
        return {
            "sample_id": self.sample_id,
            "source_indices": self.source_indices,
            "source_kind": self.source_kind,
            "influence": self.influence,
            "valid_candidates": self.valid_candidates,
            "base_intervened_count": self.base_intervened_count,
            "eligible_count": self.eligible_count,
        }


def save_teacher_cache_shard(
    path: str | Path,
    shard: TeacherCacheShard,
    manifest: TeacherCacheManifest,
) -> tuple[Path, Path]:
    tensor_path = Path(path)
    if tensor_path.suffix != ".pt":
        raise ValueError("teacher cache tensor path must end in .pt")
    manifest_path = tensor_path.with_suffix(".json")
    tensor_path.parent.mkdir(parents=True, exist_ok=True)
    tensor_tmp = tensor_path.with_suffix(".pt.tmp")
    manifest_tmp = manifest_path.with_suffix(".json.tmp")
    if tensor_tmp.exists() or manifest_tmp.exists():
        raise FileExistsError("stale cache temporary file exists; inspect before retrying")
    try:
        torch.save(
            {"manifest": manifest.to_dict(), "tensors": shard.tensor_dict()},
            tensor_tmp,
        )
        manifest_tmp.write_text(
            json.dumps(manifest.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(tensor_tmp, tensor_path)
        os.replace(manifest_tmp, manifest_path)
    finally:
        # Only remove temporary files owned by this exact write attempt.
        tensor_tmp.unlink(missing_ok=True)
        manifest_tmp.unlink(missing_ok=True)
    return tensor_path, manifest_path


def load_teacher_cache_shard(
    path: str | Path,
    expected_manifest: TeacherCacheManifest,
) -> TeacherCacheShard:
    tensor_path = Path(path)
    manifest_path = tensor_path.with_suffix(".json")
    if not tensor_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("teacher cache requires matching .pt and .json files")
    stored_manifest = TeacherCacheManifest.from_dict(
        json.loads(manifest_path.read_text(encoding="utf-8"))
    )
    if stored_manifest != expected_manifest:
        raise ValueError("teacher cache manifest mismatch; refusing stale/incompatible targets")
    payload = torch.load(tensor_path, map_location="cpu", weights_only=True)
    if not isinstance(payload, dict) or set(payload) != {"manifest", "tensors"}:
        raise ValueError("teacher cache payload does not match schema")
    embedded_manifest = TeacherCacheManifest.from_dict(payload["manifest"])
    if embedded_manifest != stored_manifest:
        raise ValueError("embedded and sidecar cache manifests disagree; shard may be partially replaced")
    tensors = payload["tensors"]
    if not isinstance(tensors, dict) or set(tensors) != set(TeacherCacheShard.__dataclass_fields__):
        raise ValueError("teacher cache tensor keys do not match schema")
    return TeacherCacheShard(**tensors)


__all__ = [
    "CACHE_SCHEMA_VERSION",
    "MAX_CANDIDATES_PER_SAMPLE",
    "MAX_SAMPLES_PER_SHARD",
    "TeacherCacheManifest",
    "TeacherCacheShard",
    "load_teacher_cache_shard",
    "save_teacher_cache_shard",
]

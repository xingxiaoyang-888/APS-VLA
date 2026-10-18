"""Versioned CPU tensor cache for actual-deletion labels (no legacy import)."""

from __future__ import annotations

from dataclasses import asdict
import os
from pathlib import Path
import tempfile

import torch

from cti_vla.selection import ConditionalTokenBatch
from .deletion import DeletionLabels, LabelProvenance


CACHE_SCHEMA_VERSION = 1
_TENSOR_FIELDS = ("retained_mask", "candidate_indices", "influence", "base_error", "deleted_error", "full_action")


def save_deletion_labels(path: str | Path, labels: DeletionLabels, *, overwrite: bool = False) -> Path:
    """Atomically write one verified batch; cached tensors never retain a graph."""
    labels.__post_init__()
    target = Path(path)
    if target.suffix != ".pt":
        raise ValueError("deletion cache path must end in .pt")
    if target.exists() and not overwrite:
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "provenance": asdict(labels.provenance),
        "feature_sha256": labels.feature_sha256,
        "teacher_calls": labels.teacher_calls,
        "tensors": {name: getattr(labels, name).detach().to("cpu", copy=True).contiguous() for name in _TENSOR_FIELDS},
    }
    descriptor, temporary = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            torch.save(payload, stream)
            stream.flush()
            os.fsync(stream.fileno())
        if target.exists() and not overwrite:
            raise FileExistsError(target)
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return target


def load_deletion_labels(path: str | Path, *, batch: ConditionalTokenBatch,
                         retained: torch.Tensor, provenance: LabelProvenance) -> DeletionLabels:
    """Reject stale identities, conditions, S, and old replacement cache schemas."""
    payload = torch.load(Path(path), map_location="cpu", weights_only=True)
    keys = {"schema_version", "provenance", "feature_sha256", "teacher_calls", "tensors"}
    if not isinstance(payload, dict) or set(payload) != keys or payload["schema_version"] != CACHE_SCHEMA_VERSION:
        raise ValueError("unsupported deletion-cache schema")
    metadata = payload["provenance"]
    if not isinstance(metadata, dict) or set(metadata) != set(LabelProvenance.__dataclass_fields__):
        raise ValueError("unsupported deletion-cache provenance schema")
    tensors = payload["tensors"]
    if not isinstance(tensors, dict) or set(tensors) != set(_TENSOR_FIELDS) or any(not isinstance(v, torch.Tensor) for v in tensors.values()):
        raise ValueError("unsupported deletion-cache tensor schema")
    labels = DeletionLabels(
        **{name: value.to(batch.visual.device) for name, value in tensors.items()},
        provenance=LabelProvenance(**metadata), feature_sha256=payload["feature_sha256"], teacher_calls=payload["teacher_calls"],
    )
    labels.validate_for(batch, retained, provenance)
    return labels

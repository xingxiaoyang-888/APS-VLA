"""Bounded, framework-agnostic manifests for LIBERO Spatial samples.

The OpenVLA-OFT upstream input pipeline is RLDS/TensorFlow based, while the
DIWA teacher/cache code is PyTorch based.  This module deliberately sits
between them: it records deterministic episode/step identities and validates
the frozen LIBERO action contract without importing TensorFlow, decoding
images, or loading a model.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .identity import stable_sample_id

LIBERO_SPATIAL_DATASET = "libero_spatial_no_noops"
LIBERO_ACTION_CHUNK_SIZE = 8
LIBERO_ACTION_DIM = 7
LIBERO_PROPRIO_DIM = 8
LIBERO_NUM_IMAGES = 2
MANIFEST_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class LiberoSampleRef:
    """A stable reference to one observation/action training row."""

    episode_id: str
    step_index: int
    sample_id: int
    task_name: str = ""

    def __post_init__(self) -> None:
        if not self.episode_id.strip():
            raise ValueError("episode_id must be non-empty")
        if not isinstance(self.step_index, int) or isinstance(self.step_index, bool) or self.step_index < 0:
            raise ValueError("step_index must be a non-negative integer")
        if not isinstance(self.sample_id, int) or isinstance(self.sample_id, bool) or not 0 <= self.sample_id < 2**63:
            raise ValueError("sample_id must fit signed non-negative int64")
        if self.task_name and not self.task_name.strip():
            raise ValueError("task_name cannot contain only whitespace")

    @classmethod
    def create(cls, episode_id: str | int, step_index: int, *, task_name: str = "") -> "LiberoSampleRef":
        episode = str(episode_id)
        return cls(
            episode_id=episode,
            step_index=step_index,
            sample_id=stable_sample_id(LIBERO_SPATIAL_DATASET, episode, step_index),
            task_name=task_name,
        )


@dataclass(frozen=True)
class LiberoManifest:
    """Deterministic sample manifest consumed by cache/loader orchestration."""

    split: str
    samples: tuple[LiberoSampleRef, ...]
    dataset_name: str = LIBERO_SPATIAL_DATASET
    action_chunk_size: int = LIBERO_ACTION_CHUNK_SIZE
    action_dim: int = LIBERO_ACTION_DIM
    proprio_dim: int = LIBERO_PROPRIO_DIM
    num_images: int = LIBERO_NUM_IMAGES
    source_signature: str = ""

    def __post_init__(self) -> None:
        if self.dataset_name != LIBERO_SPATIAL_DATASET:
            raise ValueError(f"unsupported primary dataset: {self.dataset_name}")
        if not self.split.strip():
            raise ValueError("manifest split must be non-empty")
        if (self.action_chunk_size, self.action_dim, self.proprio_dim, self.num_images) != (
            LIBERO_ACTION_CHUNK_SIZE,
            LIBERO_ACTION_DIM,
            LIBERO_PROPRIO_DIM,
            LIBERO_NUM_IMAGES,
        ):
            raise ValueError("LIBERO manifest action/image contract mismatch")
        if not self.samples:
            raise ValueError("LIBERO manifest must contain at least one sample")
        if tuple(self.samples) != tuple(sorted(self.samples, key=lambda item: (item.episode_id, item.step_index))):
            raise ValueError("samples must be sorted by episode_id and step_index")
        sample_ids = [sample.sample_id for sample in self.samples]
        if len(set(sample_ids)) != len(sample_ids):
            raise ValueError("duplicate sample_id in LIBERO manifest")
        pairs = [(sample.episode_id, sample.step_index) for sample in self.samples]
        if len(set(pairs)) != len(pairs):
            raise ValueError("duplicate episode/step in LIBERO manifest")

    @property
    def episode_ids(self) -> tuple[str, ...]:
        return tuple(sorted({sample.episode_id for sample in self.samples}))

    @property
    def sample_count(self) -> int:
        return len(self.samples)

    @property
    def episode_count(self) -> int:
        return len(self.episode_ids)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "dataset_name": self.dataset_name,
            "split": self.split,
            "action_chunk_size": self.action_chunk_size,
            "action_dim": self.action_dim,
            "proprio_dim": self.proprio_dim,
            "num_images": self.num_images,
            "source_signature": self.source_signature,
            "samples": [
                {
                    "episode_id": sample.episode_id,
                    "step_index": sample.step_index,
                    "sample_id": sample.sample_id,
                    "task_name": sample.task_name,
                }
                for sample in self.samples
            ],
        }


def build_pilot_manifest(
    episode_ids: Iterable[str | int],
    *,
    steps_per_episode: int,
    split: str = "pilot",
    task_names: Mapping[str, str] | None = None,
) -> LiberoManifest:
    """Build a deterministic bounded manifest from already-discovered rows."""

    if not isinstance(steps_per_episode, int) or isinstance(steps_per_episode, bool) or steps_per_episode <= 0:
        raise ValueError("steps_per_episode must be a positive integer")
    task_names = task_names or {}
    normalized = sorted({str(episode_id) for episode_id in episode_ids})
    if not normalized or any(not episode.strip() for episode in normalized):
        raise ValueError("episode_ids must contain at least one non-empty id")
    samples = tuple(
        sample
        for episode in normalized
        for sample in (
            LiberoSampleRef.create(episode, step, task_name=task_names.get(episode, ""))
            for step in range(steps_per_episode)
        )
    )
    return LiberoManifest(split=split, samples=samples)


def assert_episode_disjoint(*manifests: LiberoManifest) -> None:
    """Reject train/validation/test leakage at episode granularity."""

    for index, left in enumerate(manifests):
        for right in manifests[index + 1 :]:
            overlap = set(left.episode_ids) & set(right.episode_ids)
            if overlap:
                raise ValueError(
                    f"LIBERO manifests are episode-overlapping: {left.split} vs {right.split}: "
                    f"{sorted(overlap)[:5]}"
                )


def save_manifest(path: str | Path, manifest: LiberoManifest) -> Path:
    """Atomically save a small JSON manifest; refuse stale temp files."""

    output = Path(path)
    if output.suffix != ".json":
        raise ValueError("LIBERO manifest path must end with .json")
    temporary = output.with_suffix(output.suffix + ".tmp")
    if temporary.exists():
        raise FileExistsError(f"temporary manifest exists; inspect before replacing: {temporary}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(json.dumps(manifest.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, output)
    return output


def load_manifest(path: str | Path) -> LiberoManifest:
    input_path = Path(path)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ValueError("unsupported LIBERO manifest schema")
    raw_samples = payload.get("samples")
    if not isinstance(raw_samples, list):
        raise ValueError("LIBERO manifest samples must be a list")
    samples = tuple(
        LiberoSampleRef(
            episode_id=str(item["episode_id"]),
            step_index=item["step_index"],
            sample_id=item["sample_id"],
            task_name=str(item.get("task_name", "")),
        )
        for item in raw_samples
        if isinstance(item, dict)
    )
    if len(samples) != len(raw_samples):
        raise ValueError("LIBERO manifest contains malformed sample entries")
    return LiberoManifest(
        split=str(payload.get("split", "")),
        samples=samples,
        dataset_name=str(payload.get("dataset_name", "")),
        action_chunk_size=payload.get("action_chunk_size"),
        action_dim=payload.get("action_dim"),
        proprio_dim=payload.get("proprio_dim"),
        num_images=payload.get("num_images"),
        source_signature=str(payload.get("source_signature", "")),
    )


__all__ = [
    "LIBERO_ACTION_CHUNK_SIZE",
    "LIBERO_ACTION_DIM",
    "LIBERO_NUM_IMAGES",
    "LIBERO_PROPRIO_DIM",
    "LIBERO_SPATIAL_DATASET",
    "LiberoManifest",
    "LiberoSampleRef",
    "assert_episode_disjoint",
    "build_pilot_manifest",
    "load_manifest",
    "save_manifest",
]

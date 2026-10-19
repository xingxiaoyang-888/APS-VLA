"""Versioned manifests with episode splits and full temporal-stage coverage.

The three stages are thirds of the recorded trajectory, not semantic phases.
Every observation is eligible: teacher-generated action chunks do not require
eight future recorded actions, so the final observations are not discarded.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import random
import re
from typing import Iterable, Mapping, Sequence

from .identity import canonical_mapping_signature, stable_sample_id

LIBERO_SPATIAL_DATASET = "libero_spatial_no_noops"
LIBERO_ACTION_CHUNK_SIZE = 8
LIBERO_ACTION_DIM = 7
LIBERO_PROPRIO_DIM = 8
LIBERO_NUM_IMAGES = 2
MANIFEST_SCHEMA_VERSION = 2
STAGES = ("early", "middle", "late")


def _nonempty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def temporal_stage(step_index: int, num_steps: int) -> str:
    if type(num_steps) is not int or num_steps < 3:
        raise ValueError("num_steps must be at least 3 for stage coverage")
    if type(step_index) is not int or not 0 <= step_index < num_steps:
        raise ValueError("step_index outside episode")
    return STAGES[min(2, 3 * step_index // num_steps)]


@dataclass(frozen=True)
class LiberoEpisodeRef:
    """Content-stable trajectory identity plus physical storage provenance."""

    episode_id: str
    num_steps: int
    task_name: str
    source_shard: str
    record_index: int
    episode_file_path: str = ""

    def __post_init__(self) -> None:
        for name in ("episode_id", "task_name", "source_shard"):
            _nonempty(getattr(self, name), name)
        if not isinstance(self.episode_file_path, str):
            raise ValueError("episode_file_path must be a string")
        temporal_stage(0, self.num_steps)
        if type(self.record_index) is not int or self.record_index < 0:
            raise ValueError("record_index must be non-negative integer")


@dataclass(frozen=True)
class LiberoSampleRef:
    episode_id: str
    step_index: int
    sample_id: int
    stage: str

    def __post_init__(self) -> None:
        _nonempty(self.episode_id, "episode_id")
        if type(self.step_index) is not int or self.step_index < 0:
            raise ValueError("step_index must be non-negative integer")
        expected = stable_sample_id(LIBERO_SPATIAL_DATASET, self.episode_id, self.step_index)
        if type(self.sample_id) is not int or self.sample_id != expected:
            raise ValueError("sample_id does not match versioned episode/step identity")
        if self.stage not in STAGES:
            raise ValueError("unknown temporal stage")

    @classmethod
    def create(cls, episode: LiberoEpisodeRef, step_index: int) -> "LiberoSampleRef":
        return cls(episode.episode_id, step_index,
                   stable_sample_id(LIBERO_SPATIAL_DATASET, episode.episode_id, step_index),
                   temporal_stage(step_index, episode.num_steps))


@dataclass(frozen=True)
class LiberoManifest:
    split: str
    episodes: tuple[LiberoEpisodeRef, ...]
    samples: tuple[LiberoSampleRef, ...]
    source_signature: str
    seed: int
    dataset_name: str = LIBERO_SPATIAL_DATASET
    schema_version: int = MANIFEST_SCHEMA_VERSION
    action_chunk_size: int = LIBERO_ACTION_CHUNK_SIZE
    action_dim: int = LIBERO_ACTION_DIM
    proprio_dim: int = LIBERO_PROPRIO_DIM
    num_images: int = LIBERO_NUM_IMAGES
    sampling_rule: str = "temporal-thirds-with-endpoints-v1"

    def __post_init__(self) -> None:
        _nonempty(self.split, "split")
        if type(self.schema_version) is not int or self.schema_version != MANIFEST_SCHEMA_VERSION:
            raise ValueError("unsupported manifest schema; historical pilots require a separate audit")
        if self.dataset_name != LIBERO_SPATIAL_DATASET:
            raise ValueError("unsupported dataset")
        if not isinstance(self.source_signature, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", self.source_signature):
            raise ValueError("source_signature must be a SHA256 content signature")
        if type(self.seed) is not int:
            raise ValueError("seed must be an integer")
        values = (self.action_chunk_size, self.action_dim, self.proprio_dim, self.num_images)
        if any(type(value) is not int for value in values) or values != (8, 7, 8, 2):
            raise ValueError("LIBERO action/image contract mismatch")
        if self.sampling_rule != "temporal-thirds-with-endpoints-v1":
            raise ValueError("unsupported sampling rule")
        if not self.episodes or not self.samples:
            raise ValueError("manifest must contain episodes and samples")
        if tuple(sorted(self.episodes, key=lambda item: item.episode_id)) != self.episodes:
            raise ValueError("episodes must be sorted by original episode_id")
        episodes = {item.episode_id: item for item in self.episodes}
        if len(episodes) != len(self.episodes):
            raise ValueError("duplicate original episode_id, including across shards")
        if len({(item.source_shard, item.record_index) for item in self.episodes}) != len(self.episodes):
            raise ValueError("duplicate physical episode locator")
        if tuple(sorted(self.samples, key=lambda item: (item.episode_id, item.step_index))) != self.samples:
            raise ValueError("samples must be sorted by episode_id and step_index")
        if len({item.sample_id for item in self.samples}) != len(self.samples):
            raise ValueError("duplicate sample_id")
        covered = {key: set() for key in episodes}
        selected = {key: set() for key in episodes}
        for item in self.samples:
            if item.episode_id not in episodes:
                raise ValueError("sample refers to an unregistered episode")
            if item.stage != temporal_stage(item.step_index, episodes[item.episode_id].num_steps):
                raise ValueError("sample stage disagrees with original episode length")
            covered[item.episode_id].add(item.stage)
            selected[item.episode_id].add(item.step_index)
        for key, episode in episodes.items():
            if covered[key] != set(STAGES):
                raise ValueError(f"episode {key!r} lacks early/middle/late coverage")
            if not {0, episode.num_steps - 1}.issubset(selected[key]):
                raise ValueError(f"episode {key!r} lacks trajectory endpoints")

    @property
    def episode_ids(self) -> tuple[str, ...]:
        return tuple(item.episode_id for item in self.episodes)

    @property
    def sample_count(self) -> int:
        return len(self.samples)

    @property
    def episode_count(self) -> int:
        return len(self.episodes)

    def to_dict(self) -> dict:
        return asdict(self)


def build_stage_covered_manifest(
    episodes: Iterable[LiberoEpisodeRef], *, split: str, source_signature: str,
    samples_per_episode: int = 3, seed: int = 0,
) -> LiberoManifest:
    """Choose balanced temporal stages, preserving the first/final observation."""
    if type(samples_per_episode) is not int or samples_per_episode < 3:
        raise ValueError("samples_per_episode must be at least 3")
    if type(seed) is not int:
        raise ValueError("seed must be integer")
    episodes = tuple(sorted(episodes, key=lambda item: item.episode_id))
    samples = []
    for episode in episodes:
        count = min(samples_per_episode, episode.num_steps)
        selected = {0, episode.num_steps // 2, episode.num_steps - 1}
        rng = random.Random(canonical_mapping_signature(
            {"episode": episode.episode_id, "seed": seed}, namespace="cti-vla:stage-sampling:v1"))
        candidates = [[step for step in range(episode.num_steps)
                       if temporal_stage(step, episode.num_steps) == stage and step not in selected]
                      for stage in STAGES]
        for values in candidates:
            rng.shuffle(values)
        while len(selected) < count:
            for values in candidates:
                if values and len(selected) < count:
                    selected.add(values.pop())
        samples.extend(LiberoSampleRef.create(episode, step) for step in sorted(selected))
    return LiberoManifest(split, episodes, tuple(samples), source_signature, seed)


def split_episodes(
    episodes: Iterable[LiberoEpisodeRef], *, seed: int,
    fractions: Mapping[str, float] | None = None,
) -> dict[str, tuple[LiberoEpisodeRef, ...]]:
    """Stratify by task, assign whole episodes, require each task in each split.

    Splits are reproducible for the same source inventory and seed. Save the
    manifests: adding source episodes can change assignment.
    """
    fractions = dict(fractions or {"train": 0.7, "validation": 0.15, "test": 0.15})
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if len(fractions) < 2 or any(not isinstance(key, str) or not key.strip() for key in fractions):
        raise ValueError("at least two named splits required")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0
           for value in fractions.values()) or not math.isclose(sum(fractions.values()), 1.0):
        raise ValueError("split fractions must be positive and sum to one")
    episodes = list(episodes)
    if not episodes or len({item.episode_id for item in episodes}) != len(episodes):
        raise ValueError("episode inventory must be non-empty with unique original episode IDs")
    tasks: dict[str, list[LiberoEpisodeRef]] = {}
    for episode in episodes:
        tasks.setdefault(episode.task_name, []).append(episode)
    output: dict[str, list[LiberoEpisodeRef]] = {key: [] for key in fractions}
    keys = sorted(fractions)
    for task, values in sorted(tasks.items()):
        if len(values) < len(keys):
            raise ValueError(f"task {task!r} has too few episodes for task-covered splits")
        values.sort(key=lambda item: canonical_mapping_signature(
            {"seed": seed, "episode": item.episode_id}, namespace="cti-vla:episode-split:v1"))
        counts = {key: 1 for key in keys}
        for _ in range(len(values) - len(keys)):
            key = max(keys, key=lambda key: len(values) * fractions[key] - counts[key])
            counts[key] += 1
        offset = 0
        for key in keys:
            output[key].extend(values[offset:offset + counts[key]])
            offset += counts[key]
    return {key: tuple(sorted(values, key=lambda item: item.episode_id)) for key, values in output.items()}


def assert_episode_disjoint(*manifests: LiberoManifest) -> None:
    for index, left in enumerate(manifests):
        for right in manifests[index + 1:]:
            if left.dataset_name != right.dataset_name or left.source_signature != right.source_signature:
                raise ValueError("split manifests must share dataset/source signature")
            overlap = set(left.episode_ids) & set(right.episode_ids)
            if overlap:
                raise ValueError(f"episode-overlapping splits {left.split}/{right.split}: {sorted(overlap)[:5]}")


def save_manifest(path: str | Path, manifest: LiberoManifest) -> Path:
    output = Path(path)
    if output.suffix != ".json":
        raise ValueError("manifest path must end with .json")
    temporary = output.with_suffix(".json.tmp")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(f"manifest exists: {output}")
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest.to_dict(), stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")
    os.replace(temporary, output)
    return output


def load_manifest(path: str | Path) -> LiberoManifest:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != set(LiberoManifest.__dataclass_fields__):
        raise ValueError("manifest schema mismatch; historical pilots are not CTI-VLA manifests")
    if payload["schema_version"] != MANIFEST_SCHEMA_VERSION:
        raise ValueError("unsupported manifest schema")
    if not isinstance(payload["episodes"], list) or not isinstance(payload["samples"], list):
        raise ValueError("episodes and samples must be lists")
    try:
        payload["episodes"] = tuple(LiberoEpisodeRef(**item) for item in payload["episodes"])
        payload["samples"] = tuple(LiberoSampleRef(**item) for item in payload["samples"])
        return LiberoManifest(**payload)
    except TypeError as error:
        raise ValueError(f"malformed manifest entry: {error}") from error

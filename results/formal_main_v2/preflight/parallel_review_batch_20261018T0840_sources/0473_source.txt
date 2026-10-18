"""Frozen observation panels and authoritative episode/split membership."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
import os
from pathlib import Path, PurePosixPath
import random
import tempfile
from typing import Any

from .identity import canonical_mapping_signature, file_sha256
from .libero import LiberoEpisodeRef, LiberoManifest, LiberoSampleRef, assert_episode_disjoint, load_manifest

EXPOSED_EPISODE = "libero-episode-sha256:58121c87d2d470ed04f09a954d0f5ecaf0fd3b50752c21641f6020b9fa7df6f5"
PROTOCOL_VERSION = "spatial-g0g1-v1"
DIAGNOSTIC_SEED = 117
TEACHER_SEED = 217
DEVELOPMENT_TASK_SEED = 317
INITIAL_STATE_SEED = 417


def signed_payload(payload: dict[str, Any], namespace: str) -> dict[str, Any]:
    if "content_signature" in payload:
        raise ValueError("content_signature is reserved")
    return {**payload, "content_signature": canonical_mapping_signature(payload, namespace=namespace)}


def verify_payload(payload: dict[str, Any], namespace: str) -> None:
    value = dict(payload)
    signature = value.pop("content_signature", None)
    if signature != canonical_mapping_signature(value, namespace=namespace):
        raise ValueError("manifest content signature mismatch")


def write_frozen_json(path: str | Path, payload: dict[str, Any]) -> Path:
    """Idempotent exact-content write; never replace a different frozen file."""
    path = Path(path)
    data = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise FileExistsError(f"frozen file differs: {path}")
        return path
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            raise FileExistsError(f"frozen file appeared while writing: {path}")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return path


def task_key(episode: LiberoEpisodeRef) -> str:
    """Read upstream task key from the recorded HDF5 basename, not task order."""
    filename = PurePosixPath(episode.episode_file_path.replace("\\", "/")).name
    if not filename.endswith("_demo.hdf5"):
        raise ValueError(f"unexpected original task HDF5 path: {filename}")
    return filename[:-len("_demo.hdf5")]


def _subset(manifest: LiberoManifest, episode_ids: set[str]) -> LiberoManifest:
    if not episode_ids <= set(manifest.episode_ids):
        raise ValueError("panel includes an episode outside its source split")
    return replace(manifest,
                   episodes=tuple(e for e in manifest.episodes if e.episode_id in episode_ids),
                   samples=tuple(s for s in manifest.samples if s.episode_id in episode_ids))


def _reference(path: Path, base: Path) -> dict[str, str]:
    return {"path": Path(os.path.relpath(path.resolve(), base.resolve())).as_posix(), "sha256": file_sha256(path)}


def prepare_observation_protocol(source_directory: str | Path, output_directory: str | Path,
                                 exposure_evidence: str | Path) -> dict[str, Any]:
    source, output = Path(source_directory), Path(output_directory)
    manifests = {split: load_manifest(source / f"{split}.json") for split in ("train", "validation", "test")}
    if any(manifest.split != name for name, manifest in manifests.items()):
        raise ValueError("source manifest names disagree with authoritative split fields")
    assert_episode_disjoint(*manifests.values())
    train, validation = manifests["train"], manifests["validation"]
    if EXPOSED_EPISODE not in validation.episode_ids:
        raise ValueError("registered engineering exposure is absent from source validation")
    evidence = json.loads(Path(exposure_evidence).read_text(encoding="utf-8"))
    if evidence.get("status") != "passed" or evidence.get("dataset", {}).get("episode_id") != EXPOSED_EPISODE:
        raise ValueError("engineering exposure evidence does not identify the registered episode")
    integration = evidence.get("conditional_integration", {})
    if integration.get("scale_fit_labels") != 4 or integration.get("optimizer_steps") != 1:
        raise ValueError("unexpected exposure evidence; review before freezing protocol")
    output.mkdir(parents=True, exist_ok=True)
    exclusion_path = write_frozen_json(output / "exposure_exclusions.json", {
        "schema_version": 1, "reason": "engineering-only; never include in formal validation metrics or model training",
        "episodes": [{"episode_id": EXPOSED_EPISODE, "original_split": "validation",
                      "exposed_steps": [evidence["dataset"]["step_index"]],
                      "scale_fit_labels": 4, "optimizer_steps": 1,
                      "saved_trained_model": False}],
        "evidence": _reference(Path(exposure_evidence), output),
    })
    effective = _subset(validation, set(validation.episode_ids) - {EXPOSED_EPISODE})
    task_episodes: dict[str, list[LiberoEpisodeRef]] = {}
    for episode in train.episodes:
        task_episodes.setdefault(episode.task_name, []).append(episode)
    tasks = sorted(task_episodes)
    if len(tasks) != 10:
        raise ValueError("G0/G1 protocol requires all ten Spatial tasks")
    selected_ids = set()
    for task in tasks:
        candidates = sorted(task_episodes[task], key=lambda e: e.episode_id)
        if len(candidates) < 3:
            raise ValueError("each task needs at least three training episodes")
        rng = random.Random(canonical_mapping_signature({"seed": DIAGNOSTIC_SEED, "task": task}, namespace="cti-vla:diagnostic-panel:v1"))
        selected_ids.update(e.episode_id for e in rng.sample(candidates, 3))
    diagnostic = _subset(train, selected_ids)
    teacher_rng = random.Random(TEACHER_SEED)
    teacher_tasks = sorted(teacher_rng.sample(tasks, 4))
    teacher_ids = set()
    for task in teacher_tasks:
        candidates = [e for e in diagnostic.episodes if e.task_name == task]
        teacher_ids.add(teacher_rng.choice(candidates).episode_id)
    teacher = _subset(train, teacher_ids)
    if (diagnostic.sample_count, teacher.sample_count) != (90, 12):
        raise ValueError("source sampling must have exactly three stage-covered observations per episode")
    dev_tasks = sorted(random.Random(DEVELOPMENT_TASK_SEED).sample(tasks, 3))
    catalog = []
    for task in tasks:
        keys = {task_key(episode) for episode in task_episodes[task]}
        if len(keys) != 1:
            raise ValueError("one instruction maps to multiple official task filenames")
        catalog.append({"task_name": keys.pop(), "instruction": task})
    catalog.sort(key=lambda row: row["task_name"])
    development_path = write_frozen_json(output / "development_tasks.json", {
        "schema_version": 1, "seed": DEVELOPMENT_TASK_SEED,
        "rule": "sort ten task instructions; random.Random(seed).sample(3); sort selected instructions",
        "tasks": [row for row in catalog if row["instruction"] in dev_tasks],
    })
    panels = {}
    for name, manifest, seed in (("diagnostic_90", diagnostic, DIAGNOSTIC_SEED),
                                 ("teacher_12", teacher, TEACHER_SEED),
                                 ("validation_effective", effective, 17)):
        path = write_frozen_json(output / f"{name}.json", manifest.to_dict())
        panels[name] = {**_reference(path, output), "selection_seed": seed,
                        "episodes": manifest.episode_count, "observations": manifest.sample_count}
    payload = signed_payload({
        "schema_version": 1, "protocol_version": PROTOCOL_VERSION, "suite": "libero_spatial",
        "source_signature": train.source_signature,
        "source_manifests": {split: _reference(source / f"{split}.json", output) for split in manifests},
        "exclusions": _reference(exclusion_path, output), "panels": panels,
        "development_tasks": _reference(development_path, output), "task_catalog": catalog,
        "initial_state_seed": INITIAL_STATE_SEED,
        "rules": {"diagnostic": "sort content IDs within each task; independently seeded sample of three episodes; retain all three stages",
                  "teacher": "sort task instructions; seeded sample of four tasks then one diagnostic-panel episode per task; retain all three stages",
                  "formal_validation": "exclude entire registered engineering episode; preserve original manifests",
                  "test": "never use for engineering training, mechanism selection or tuning",
                  "initial_states": "inventory official states only; if all tasks have >=60 use 10 development + 50 final; otherwise require exactly 50 per task for 10+40"},
    }, "cti-vla:experiment-protocol:v1")
    write_frozen_json(output / "protocol.json", payload)
    return payload


@dataclass(frozen=True)
class ExperimentProtocol:
    path: Path
    payload: dict[str, Any]
    manifests: dict[str, LiberoManifest]
    excluded_episode_ids: frozenset[str]

    def require_sample(self, episode_id: str, step_index: int, *, split: str) -> tuple[LiberoEpisodeRef, LiberoSampleRef]:
        """Resolve split from pinned source manifests; never trust caller labels."""
        if split not in self.manifests or type(step_index) is not int:
            raise ValueError("invalid required split or step_index")
        if episode_id in self.excluded_episode_ids:
            raise ValueError("episode is engineering-only and excluded from formal data use")
        actual = [name for name, manifest in self.manifests.items() if episode_id in manifest.episode_ids]
        if actual != [split]:
            raise ValueError(f"authoritative episode split is {actual}; required {split}")
        manifest = self.manifests[split]
        episode = next(e for e in manifest.episodes if e.episode_id == episode_id)
        sample = next((s for s in manifest.samples if s.episode_id == episode_id and s.step_index == step_index), None)
        if sample is None:
            raise ValueError("observation is not in the frozen source manifest")
        return episode, sample


def load_experiment_protocol(path: str | Path) -> ExperimentProtocol:
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    verify_payload(payload, "cti-vla:experiment-protocol:v1")
    if payload.get("schema_version") != 1 or payload.get("protocol_version") != PROTOCOL_VERSION:
        raise ValueError("unsupported experiment protocol")

    def verify_file(ref):
        target = path.parent / ref["path"]
        if file_sha256(target) != ref["sha256"]:
            raise ValueError(f"pinned manifest hash mismatch: {target}")
        return target

    manifests = {name: load_manifest(verify_file(ref)) for name, ref in payload["source_manifests"].items()}
    if set(manifests) != {"train", "validation", "test"} or any(m.split != name for name, m in manifests.items()):
        raise ValueError("source manifests must identify real train/validation/test splits")
    assert_episode_disjoint(*manifests.values())
    if any(m.source_signature != payload["source_signature"] for m in manifests.values()):
        raise ValueError("source data signature mismatch")
    exclusion = json.loads(verify_file(payload["exclusions"]).read_text(encoding="utf-8"))
    excluded = frozenset(row["episode_id"] for row in exclusion["episodes"])
    if excluded != frozenset({EXPOSED_EPISODE}) or not excluded <= set(manifests["validation"].episode_ids):
        raise ValueError("invalid engineering exposure exclusion")
    for ref in payload["panels"].values():
        verify_file(ref)
    verify_file(payload["development_tasks"])
    return ExperimentProtocol(path, payload, manifests, excluded)


def select_train_observation(protocol: ExperimentProtocol, shard: str | Path, *,
                             record_index: int | None = None, step_index: int | None = None):
    """Select the first train sample in a shard, or validate explicit coordinates."""
    if (record_index is None) != (step_index is None):
        raise ValueError("record_index and step_index must both be supplied or both omitted")
    if record_index is None:
        episode_map = {e.episode_id: e for e in protocol.manifests["train"].episodes if e.source_shard == Path(shard).name}
        candidates = [s for s in protocol.manifests["train"].samples if s.episode_id in episode_map]
        if not candidates:
            raise ValueError("shard contains no frozen train observations")
        selected = min(candidates, key=lambda s: (episode_map[s.episode_id].record_index, s.step_index))
        return protocol.require_sample(selected.episode_id, selected.step_index, split="train")
    if type(record_index) is not int or record_index < 0 or type(step_index) is not int or step_index < 0:
        raise ValueError("record/step index must be nonnegative integers")
    matches = [e for m in protocol.manifests.values() for e in m.episodes
               if e.source_shard == Path(shard).name and e.record_index == record_index]
    if len(matches) != 1:
        raise ValueError("shard/record does not uniquely identify a registered episode")
    return protocol.require_sample(matches[0].episode_id, step_index, split="train")

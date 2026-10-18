"""Independent, sealed-test LIBERO-Long G1-F protocol and h8 windows.

Inventory parses protobuf structure and hashes compressed step fields. It never
decodes RGB or materializes action/state arrays. Only registered train/validation
records enter the full episode decoder and conservative endpoint diagnostics.
Spatial manifests, selection rules and implementation are not changed.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import random
import re

import numpy as np

from .experiment_protocol import signed_payload, verify_payload, task_key
from .future_windows import ACTION_TARGET_VERSION, HORIZON, PHASES, WINDOW_FIELDS, legal_future_starts, normalize_demo_actions
from .identity import canonical_mapping_signature, file_sha256
from .libero import LiberoEpisodeRef, split_episodes
from .sequence_example import LiberoEpisode, _example_class, _episode_content_id, decode_libero_example
from .tfrecord import iter_tfrecord_records

SUITE = "libero_10"
DATASET = "libero_10_no_noops"
DATASET_REVISION = "6ce6aaaaabdbe590b1eef5cd29c0d33f14a08551"
PROTOCOL_VERSION = "g1-future-long-protocol-v1"
FUTURE_VERSION = "g1-future-long-windows-h8-v1"
REG_NAMESPACE = "cti-vla:long-future-registration:v1"
PROTOCOL_NAMESPACE = "cti-vla:long-future-protocol:v1"
WINDOW_NAMESPACE = "cti-vla:long-future-windows:v1"
SPLIT_SEED, TRAIN_SEED, VALIDATION_SEED = 17, 117, 517
DEVELOPMENT_TASK_IDS = [0, 3, 5]
SHARD_NAMES = tuple(f"liber_o10-train.tfrecord-{i:05d}-of-00032" for i in range(32))
SHARD_EPISODE_COUNTS = {name: (11 if i in (3, 9, 16, 22, 28) else 12) for i, name in enumerate(SHARD_NAMES)}
# Official LIBERO task_order_index=0 at commit 8f1084e..., independent of data.
OFFICIAL_TASK_NAMES = (
    "LIVING_ROOM_SCENE2_put_both_the_alphabet_soup_and_the_tomato_sauce_in_the_basket",
    "LIVING_ROOM_SCENE2_put_both_the_cream_cheese_box_and_the_butter_in_the_basket",
    "KITCHEN_SCENE3_turn_on_the_stove_and_put_the_moka_pot_on_it",
    "KITCHEN_SCENE4_put_the_black_bowl_in_the_bottom_drawer_of_the_cabinet_and_close_it",
    "LIVING_ROOM_SCENE5_put_the_white_mug_on_the_left_plate_and_put_the_yellow_and_white_mug_on_the_right_plate",
    "STUDY_SCENE1_pick_up_the_book_and_place_it_in_the_back_compartment_of_the_caddy",
    "LIVING_ROOM_SCENE6_put_the_white_mug_on_the_plate_and_put_the_chocolate_pudding_to_the_right_of_the_plate",
    "LIVING_ROOM_SCENE1_put_both_the_alphabet_soup_and_the_cream_cheese_box_in_the_basket",
    "KITCHEN_SCENE8_put_both_moka_pots_on_the_stove",
    "KITCHEN_SCENE6_put_the_yellow_and_white_mug_in_the_microwave_and_close_it",
)
OFFICIAL_MAPPING = {"task_order_index": 0,
                    "task_map_sha256": "dc644c34987f6e0e4dc5320e5168cd2ee170cb8520f6a9344d2cd6d50f2c55fc",
                    "benchmark_source_sha256": "b1c7bcbe75150e123c2d250cf455c7ed7333b76d21c78ec122a5c02544d19b83"}


def official_long_catalog():
    return [{"task_id": i, "task_name": name,
             "instruction": re.sub(r"^.*?SCENE\d+_", "", name).replace("_", " ")}
            for i, name in enumerate(OFFICIAL_TASK_NAMES)]


def registration_payload():
    return signed_payload({"schema_version": 1, "version": PROTOCOL_VERSION, "suite": SUITE,
        "dataset_name": DATASET, "dataset_revision": DATASET_REVISION, "episode_count": 379,
        "shard_episode_counts": SHARD_EPISODE_COUNTS,
        "split_seed": SPLIT_SEED, "split_fractions": {"train": .7, "validation": .15, "test": .15},
        "split_rule": "cti-vla:episode-split:v1; per-task stable content hash; existing largest-deficit integer allocation",
        "train_selection_seed": TRAIN_SEED, "validation_selection_seed": VALIDATION_SEED,
        "selection_rule": "sorted episode IDs; per-task random.Random(namespace signature).sample without replacement",
        "episodes_per_task": {"train": 3, "validation": 2}, "horizon": HORIZON,
        "phase_rule": "first/middle/last legal h8 start; require three distinct starts; never resample short selected episodes",
        "task_catalog": official_long_catalog(), "official_mapping": OFFICIAL_MAPPING,
        "libero_revision": "8f1084e3132a39270c3a13ebe37270a43ece2a01",
        "development_task_ids": DEVELOPMENT_TASK_IDS, "test_pixels_opened": False,
        "quarantined_episode_ids": [], "diagnostics_version": "h8-raw-endpoint-change-v1",
        "diagnostics_used_for_selection": False}, REG_NAMESPACE)


def _load_registration(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload != registration_payload():
        raise ValueError("Long registration differs from fixed rules/official task mapping")
    return payload


def load_long_asset(path):
    path = Path(path)
    asset = json.loads(path.read_text(encoding="utf-8"))
    if (asset.get("repository"), asset.get("revision"), asset.get("dataset_path"), asset.get("suite"),
        asset.get("episode_count"), asset.get("shard_count")) != (
            "openvla/modified_libero_rlds", DATASET_REVISION, DATASET + "/1.0.0", SUITE, 379, 32):
        raise ValueError("Long dataset asset metadata differs from preregistration")
    files = asset["files"]
    if len(files) != 34 or len({f["path"] for f in files}) != len(files):
        raise ValueError("Long asset requires all32 shards and two unique metadata files")
    sources = {}
    for spec in files:
        name = PurePosixPath(spec["path"]).name
        if spec["path"] != DATASET + "/1.0.0/" + name:
            raise ValueError("Long asset path escaped dataset")
        if type(spec["size"]) is not int or spec["size"] <= 0:
            raise ValueError("Long asset size invalid")
        if name in SHARD_NAMES:
            if not re.fullmatch(r"[0-9a-f]{64}", spec.get("sha256", "")):
                raise ValueError("Long shard requires preexisting source SHA256")
            sources[name] = {"bytes": spec["size"], "sha256": spec["sha256"]}
        elif name not in ("dataset_info.json", "features.json") or not re.fullmatch(r"[0-9a-f]{40}", spec.get("git_blob_sha1", "")):
            raise ValueError("Long metadata source identity invalid")
    if set(sources) != set(SHARD_NAMES) or sum(f["size"] for f in files) != asset["total_bytes"]:
        raise ValueError("Long asset shard inventory/total bytes mismatch")
    return asset, sources


def _verify_dataset_info(path, asset):
    data = Path(path).read_bytes()
    spec = next(f for f in asset["files"] if f["path"].endswith("/dataset_info.json"))
    git_hash = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
    if len(data) != spec["size"] or git_hash != spec["git_blob_sha1"]:
        raise ValueError("dataset_info differs from immutable asset")
    info = json.loads(data)
    if info["name"] != "liber_o10" or info["version"] != "1.0.0" or len(info["splits"]) != 1 or info["splits"][0]["name"] != "train":
        raise ValueError("unexpected Long dataset_info")
    lengths = tuple(int(n) for n in info["splits"][0]["shardLengths"])
    if dict(zip(SHARD_NAMES, lengths)) != SHARD_EPISODE_COUNTS or len(lengths) != 32:
        raise ValueError("dataset_info episode/shard counts differ")
    return dict(zip(SHARD_NAMES, lengths))


def probe_episode_metadata(payload: bytes, source_shard: str, record_index: int) -> LiberoEpisodeRef:
    """Read lengths, text, boundary flags and canonical compressed-payload ID.

    Protobuf parses wire values, but this function does not inspect numeric action/
    state values, create their NumPy arrays, or invoke any JPEG decoder.
    """
    if not isinstance(payload, bytes) or not payload or len(payload) > 512 * 1024 * 1024:
        raise ValueError("invalid or oversized inventory payload")
    msg = _example_class()()
    msg.ParseFromString(payload)
    features = msg.features.feature
    kinds = {"steps/action": ("float_list", 7), "steps/observation/state": ("float_list", 8),
             "steps/observation/joint_state": ("float_list", 7), "steps/reward": ("float_list", 1),
             "steps/discount": ("float_list", 1), "steps/is_first": ("int64_list", 1),
             "steps/is_last": ("int64_list", 1), "steps/is_terminal": ("int64_list", 1),
             "steps/language_instruction": ("bytes_list", 1), "steps/observation/image": ("bytes_list", 1),
             "steps/observation/wrist_image": ("bytes_list", 1)}
    if not set(kinds).union({"episode_metadata/file_path"}) <= set(features):
        raise ValueError("Long inventory missing required fields")
    n = len(features["steps/is_first"].int64_list.value)
    if not 3 <= n <= 10000:
        raise ValueError("invalid inventory episode length")
    for key, (kind, width) in kinds.items():
        feature = features[key]
        if feature.WhichOneof("kind") != kind or len(getattr(feature, kind).value) != n * width:
            raise ValueError("inventory feature kind/length mismatch: " + key)
    flags = {name: tuple(features["steps/" + name].int64_list.value) for name in ("is_first", "is_last", "is_terminal")}
    if (flags["is_first"] != (1,) + (0,) * (n - 1) or flags["is_last"] != (0,) * (n - 1) + (1,)
        or flags["is_terminal"][:-1] != (0,) * (n - 1) or flags["is_terminal"][-1] not in (0, 1)):
        raise ValueError("inventory episode boundary flags invalid")
    instructions = features["steps/language_instruction"].bytes_list.value
    instruction = instructions[0].decode("utf-8", errors="strict")
    if not instruction.strip() or any(text != instructions[0] for text in instructions):
        raise ValueError("inventory instruction changed within episode")
    feature = features["episode_metadata/file_path"]
    if feature.WhichOneof("kind") != "bytes_list" or len(feature.bytes_list.value) != 1:
        raise ValueError("inventory file path invalid")
    ref = LiberoEpisodeRef(_episode_content_id(msg), n, instruction, source_shard, record_index,
                           feature.bytes_list.value[0].decode("utf-8", errors="strict"))
    expected = {row["task_name"]: row["instruction"] for row in official_long_catalog()}
    if expected.get(task_key(ref)) != instruction:
        raise ValueError("Long record task basename/instruction differs from official catalog")
    return ref


@dataclass(frozen=True)
class LongEpisodeManifest:
    split: str
    episodes: tuple[LiberoEpisodeRef, ...]
    dataset_name: str = DATASET

    @property
    def episode_ids(self):
        return tuple(e.episode_id for e in self.episodes)


@dataclass(frozen=True)
class LongFutureProtocol:
    path: Path
    payload: dict
    manifests: dict[str, LongEpisodeManifest]
    excluded_episode_ids: frozenset[str]
    asset_path: Path
    registration_path: Path


def _source_signature(sources):
    return canonical_mapping_signature(sources, namespace="cti-vla:long-future-rlds-source:v1")


def _episode_summary(manifests):
    return {split: {"episodes": len(m.episodes), "by_task": dict(sorted(Counter(e.task_name for e in m.episodes).items()))}
            for split, m in sorted(manifests.items())}


def _check_refs(episodes, sources):
    if len(episodes) != 379 or len({e.episode_id for e in episodes}) != len(episodes):
        raise ValueError("Long inventory requires379 unique content IDs")
    if len({(e.source_shard, e.record_index) for e in episodes}) != len(episodes):
        raise ValueError("Long inventory repeats a physical locator")
    instructions = {r["task_name"]: r["instruction"] for r in official_long_catalog()}
    if {e.task_name for e in episodes} != set(instructions.values()):
        raise ValueError("Long inventory must cover all10 official tasks")
    for e in episodes:
        if e.source_shard not in sources or instructions.get(task_key(e)) != e.task_name or not re.fullmatch(r"libero-episode-sha256:[0-9a-f]{64}", e.episode_id):
            raise ValueError("Long inventory source/task/content identity mismatch")
    for name in sources:
        indices = sorted(e.record_index for e in episodes if e.source_shard == name)
        if indices != list(range(SHARD_EPISODE_COUNTS[name])):
            raise ValueError("Long inventory shard record coverage is not contiguous")


def build_long_future_protocol(data_directory, asset_manifest, registration_path, *, progress=None):
    data_directory, asset_manifest, registration_path = map(Path, (data_directory, asset_manifest, registration_path))
    registration = _load_registration(registration_path)
    asset, sources = load_long_asset(asset_manifest)
    counts = _verify_dataset_info(data_directory / "dataset_info.json", asset)
    episodes = []
    for name in SHARD_NAMES:
        path = data_directory / name
        if {"bytes": path.stat().st_size, "sha256": file_sha256(path)} != sources[name]:
            raise ValueError("Long shard differs from immutable asset: " + name)
        refs = [probe_episode_metadata(payload, name, i) for i, payload in iter_tfrecord_records(path)]
        if len(refs) != counts[name]:
            raise ValueError("Long shard episode count differs from dataset_info: " + name)
        episodes.extend(refs)
        if progress:
            progress({"stage": "metadata_only_inventory", "shard": name, "episodes_total": len(episodes)})
    _check_refs(episodes, sources)
    split_refs = split_episodes(episodes, seed=SPLIT_SEED)
    manifests = {split: LongEpisodeManifest(split, tuple(refs)) for split, refs in split_refs.items()}
    payload = {"schema_version": 1, "version": PROTOCOL_VERSION, "suite": SUITE, "dataset_name": DATASET,
               "dataset_revision": DATASET_REVISION, "dataset_asset_sha256": file_sha256(asset_manifest),
               "registration_sha256": file_sha256(registration_path), "registration_signature": registration["content_signature"],
               "source_files": sources, "source_signature": _source_signature(sources), "shard_episode_counts": counts,
               "episodes_by_split": {s: [asdict(e) for e in m.episodes] for s, m in sorted(manifests.items())},
               "summary": _episode_summary(manifests), "task_catalog": registration["task_catalog"],
               "official_mapping": registration["official_mapping"], "development_task_ids": DEVELOPMENT_TASK_IDS,
               "split_seed": SPLIT_SEED, "train_selection_seed": TRAIN_SEED, "validation_selection_seed": VALIDATION_SEED,
               "excluded_episode_ids": [], "test_pixels_opened": False,
               "inventory_scope": "protobuf field lengths/text/boundary flags and canonical compressed-payload identity; no RGB decoding or numeric action/state array materialization"}
    return signed_payload(payload, PROTOCOL_NAMESPACE)


def load_long_future_protocol(path, asset_manifest=None, registration_path=None) -> LongFutureProtocol:
    path = Path(path).resolve()
    project = path.parents[3]
    asset_path = Path(asset_manifest or project / "configs/assets/libero_long_rlds.json")
    reg_path = Path(registration_path or project / "configs/experiments/g1_future_long_data_v1.json")
    registration = _load_registration(reg_path)
    _, sources = load_long_asset(asset_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    verify_payload(payload, PROTOCOL_NAMESPACE)
    for key, expected in {"schema_version": 1, "version": PROTOCOL_VERSION, "suite": SUITE, "dataset_name": DATASET,
        "dataset_revision": DATASET_REVISION, "dataset_asset_sha256": file_sha256(asset_path),
        "registration_sha256": file_sha256(reg_path), "registration_signature": registration["content_signature"],
        "source_files": sources, "source_signature": _source_signature(sources), "task_catalog": registration["task_catalog"],
        "official_mapping": registration["official_mapping"], "development_task_ids": DEVELOPMENT_TASK_IDS,
        "split_seed": SPLIT_SEED, "train_selection_seed": TRAIN_SEED, "validation_selection_seed": VALIDATION_SEED,
        "excluded_episode_ids": [], "test_pixels_opened": False}.items():
        if payload.get(key) != expected:
            raise ValueError("Long protocol differs from frozen registration/source: " + key)
    if set(payload["episodes_by_split"]) != {"train", "validation", "test"}:
        raise ValueError("Long protocol requires three episode splits")
    manifests = {s: LongEpisodeManifest(s, tuple(LiberoEpisodeRef(**e) for e in refs)) for s, refs in payload["episodes_by_split"].items()}
    episodes = [e for m in manifests.values() for e in m.episodes]
    _check_refs(episodes, sources)
    expected = split_episodes(episodes, seed=SPLIT_SEED)
    if any(tuple(expected[s]) != m.episodes for s, m in manifests.items()):
        raise ValueError("Long protocol membership differs from deterministic episode split")
    if payload["shard_episode_counts"] != dict(sorted(Counter(e.source_shard for e in episodes).items())) or payload["summary"] != _episode_summary(manifests):
        raise ValueError("Long protocol inventory counts differ")
    protocol = LongFutureProtocol(path, payload, manifests, frozenset(), asset_path, reg_path)
    planned_future_episodes(protocol)  # Fail if a task cannot supply the fixed panel.
    return protocol


def require_future_episode(protocol, episode_id, split):
    if split not in ("train", "validation"):
        raise ValueError("Long G1-F test is sealed")
    if episode_id in protocol.excluded_episode_ids:
        raise ValueError("Long episode is quarantined")
    matches = [(s, e) for s, m in protocol.manifests.items() for e in m.episodes if e.episode_id == episode_id]
    if len(matches) != 1 or matches[0][0] != split:
        raise ValueError("Long window differs from authoritative episode split")
    return matches[0][1]


def planned_future_episodes(protocol):
    selected = {}
    for split, count, seed in (("train", 3, TRAIN_SEED), ("validation", 2, VALIDATION_SEED)):
        refs = []
        for task in official_long_catalog():
            pool = sorted((e for e in protocol.manifests[split].episodes if e.task_name == task["instruction"]
                           and e.episode_id not in protocol.excluded_episode_ids), key=lambda e: e.episode_id)
            if len(pool) < count:
                raise ValueError("Long task lacks required split episodes")
            rng_seed = canonical_mapping_signature({"seed": seed, "split": split, "task": task["task_name"]},
                                                   namespace="cti-vla:long-future-panel-selection:v1")
            refs.extend(random.Random(rng_seed).sample(pool, count))
        if any(not legal_future_starts(e.num_steps) for e in refs):
            raise ValueError("selected Long episode lacks three distinct h8 starts; no replacement/resampling allowed")
        selected[split] = tuple(sorted(refs, key=lambda e: e.episode_id))
    return selected


def _window_id(episode_id, start):
    return canonical_mapping_signature({"dataset_name": DATASET, "episode_id": episode_id, "start_step": start,
                                        "horizon": HORIZON}, namespace="cti-vla:future-window:v1")


def _row(ref, split, phase, start, terminal):
    future = start + HORIZON
    return {"window_id": _window_id(ref.episode_id, start), "episode_id": ref.episode_id,
            "source_shard": ref.source_shard, "record_index": ref.record_index, "num_steps": ref.num_steps,
            "task_name": ref.task_name, "split": split, "phase": phase, "start_step": start, "future_step": future,
            "action_start": start, "action_stop_exclusive": future, "horizon": HORIZON,
            "future_is_last": future == ref.num_steps - 1, "future_is_terminal": bool(terminal)}


def _validate_registered_row(row, protocol):
    if not isinstance(row, dict) or set(row) != WINDOW_FIELDS:
        raise ValueError("Long future window fields mismatch")
    ref = require_future_episode(protocol, row["episode_id"], row["split"])
    selected = planned_future_episodes(protocol)
    if ref not in selected[row["split"]]:
        raise ValueError("Long episode not in frozen future panel")
    if row["phase"] not in PHASES or type(row["future_is_last"]) is not bool or type(row["future_is_terminal"]) is not bool:
        raise ValueError("Long phase/boundary flags invalid")
    start = legal_future_starts(ref.num_steps)[PHASES.index(row["phase"])]
    if row["future_is_terminal"] and not row["future_is_last"]:
        raise ValueError("Long terminal marker precedes episode end")
    if row != _row(ref, row["split"], row["phase"], start, row["future_is_terminal"]) or any(type(row[k]) is not int for k in
        ("record_index", "num_steps", "start_step", "future_step", "action_start", "action_stop_exclusive", "horizon")):
        raise ValueError("Long future interval/identity differs from registration")
    return ref


def validate_future_window(row, episode: LiberoEpisode, protocol):
    ref = _validate_registered_row(row, protocol)
    if (episode.episode_id, episode.source_shard, episode.record_index, episode.num_steps, episode.episode_file_path) != (
        ref.episode_id, ref.source_shard, ref.record_index, ref.num_steps, ref.episode_file_path):
        raise ValueError("Long runtime content ID/length/locator/path mismatch")
    n = ref.num_steps
    for name in ("is_first", "is_last", "is_terminal"):
        flags = getattr(episode, name)
        if flags.shape != (n,) or flags.dtype != np.bool_:
            raise ValueError("Long runtime boundary flag shape/type invalid")
    if not episode.is_first[0] or episode.is_first[1:].any() or not episode.is_last[-1] or episode.is_last[:-1].any() or episode.is_terminal[:-1].any():
        raise ValueError("Long runtime episode boundary violation")
    t, u = row["start_step"], row["future_step"]
    if bool(episode.is_last[u]) != row["future_is_last"] or bool(episode.is_terminal[u]) != row["future_is_terminal"]:
        raise ValueError("Long runtime future flag mismatch")
    if len(episode.instructions) != n or any(s != ref.task_name for s in episode.instructions):
        raise ValueError("Long runtime instruction mismatch")
    if episode.actions.shape != (n, 7) or episode.proprio.shape != (n, 8) or not np.isfinite(episode.actions).all() or not np.isfinite(episode.proprio).all():
        raise ValueError("Long runtime action/state shape or finite check failed")
    if len(episode.images) != n or len(episode.wrist_images) != n or episode.actions[t:u].shape != (HORIZON, 7):
        raise ValueError("Long runtime future interval incomplete")


def _rotation_matrix(vector):
    vector = np.asarray(vector, dtype=np.float64)
    theta = float(np.linalg.norm(vector))
    if theta < 1e-12:
        return np.eye(3)
    x, y, z = vector / theta
    cross = np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])
    return np.eye(3) + np.sin(theta) * cross + (1 - np.cos(theta)) * (cross @ cross)


def rotation_distance(first, second):
    """SO(3) endpoint angle in radians; robust to axis-angle wraparound."""
    relative = _rotation_matrix(first).T @ _rotation_matrix(second)
    return float(np.arccos(np.clip((np.trace(relative) - 1) / 2, -1, 1)))


def endpoint_change_diagnostics(row, episode):
    """Raw RGB/proprio changes only; no semantic or learned-state inference."""
    from PIL import Image
    t, u = row["start_step"], row["future_step"]
    states = np.asarray(episode.proprio[t:u + 1], dtype=np.float64)
    if states.shape != (9, 8) or not np.isfinite(states).all():
        raise ValueError("Long diagnostic requires nine finite aligned states")
    metrics = {"position_endpoint_l2_m": float(np.linalg.norm(states[-1, :3] - states[0, :3])),
               "position_path_length_m": float(np.linalg.norm(np.diff(states[:, :3], axis=0), axis=1).sum()),
               "rotation_endpoint_angle_rad": rotation_distance(states[0, 3:6], states[-1, 3:6]),
               "rotation_path_angle_rad": sum(rotation_distance(a[3:6], b[3:6]) for a, b in zip(states[:-1], states[1:])),
               "gripper_endpoint_qpos_l2": float(np.linalg.norm(states[-1, 6:] - states[0, 6:])),
               "gripper_path_qpos_l2": float(np.linalg.norm(np.diff(states[:, 6:], axis=0), axis=1).sum())}
    for camera, images in (("front", episode.images), ("wrist", episode.wrist_images)):
        arrays = []
        for i in (t, u):
            with Image.open(io.BytesIO(images[i])) as image:
                if image.mode != "RGB" or image.size != (256, 256):
                    raise ValueError("Long diagnostic expects raw released256x256 RGB")
                arrays.append(np.asarray(image, dtype=np.float64))
        delta = (arrays[1] - arrays[0]) / 255.
        metrics[camera + "_rgb_mae_0_1"] = float(np.abs(delta).mean())
        metrics[camera + "_rgb_rmse_0_1"] = float(np.sqrt(np.square(delta).mean()))
        metrics[camera + "_pixel_fraction_abs_gt8"] = float((np.max(np.abs(delta), axis=2) > 8 / 255.).mean())
    return {**{k: row[k] for k in ("window_id", "episode_id", "split", "task_name", "phase", "start_step", "future_step")}, "metrics": metrics}


def _window_summary(planned, rows):
    return {split: {"episodes": len(refs), "windows": sum(r["split"] == split for r in rows),
            "by_task": {task: {"episodes": sum(e.task_name == task for e in refs),
                "windows": sum(r["split"] == split and r["task_name"] == task for r in rows),
                "phase_counts": dict(Counter(r["phase"] for r in rows if r["split"] == split and r["task_name"] == task))}
                for task in sorted({e.task_name for e in refs})}} for split, refs in planned.items()}


def summarize_endpoint_changes(rows):
    output = {}
    groups = {"all": rows}
    for field in ("split", "task_name", "phase"):
        groups.update({field + ":" + value: [r for r in rows if r[field] == value] for value in sorted({r[field] for r in rows})})
    for group, subset in groups.items():
        output[group] = {"windows": len(subset), "episodes": len({r["episode_id"] for r in subset}), "metrics": {
            name: {"mean": float(np.mean(values)), "median": float(np.median(values)), "p95": float(np.percentile(values, 95))}
            for name in sorted(subset[0]["metrics"]) for values in [[r["metrics"][name] for r in subset]]}}
    return output


def build_future_windows(protocol, data_directory, asset_manifest=None, *, progress=None):
    """Return (manifest, diagnostics). Decode ONLY the selected50 records."""
    asset_path = Path(asset_manifest or protocol.asset_path)
    if file_sha256(asset_path) != protocol.payload["dataset_asset_sha256"]:
        raise ValueError("Long future asset differs from protocol")
    _, all_sources = load_long_asset(asset_path)
    planned = planned_future_episodes(protocol)
    wanted = defaultdict(dict)
    for split, refs in planned.items():
        for ref in refs:
            wanted[ref.source_shard][ref.record_index] = (split, ref)
    rows, changes, sources = [], [], {}
    for name, records in sorted(wanted.items()):
        path = Path(data_directory) / name
        actual = {"bytes": path.stat().st_size, "sha256": file_sha256(path)}
        if actual != all_sources[name]:
            raise ValueError("Long future shard differs from pinned source: " + name)
        sources[name] = actual
        found = set()
        for index, payload in iter_tfrecord_records(path):
            if index not in records:
                continue
            split, ref = records[index]
            episode = replace(decode_libero_example(payload), source_shard=name, record_index=index)
            for phase, t in zip(PHASES, legal_future_starts(ref.num_steps)):
                row = _row(ref, split, phase, t, episode.is_terminal[t + HORIZON])
                validate_future_window(row, episode, protocol)
                rows.append(row)
                changes.append(endpoint_change_diagnostics(row, episode))
            found.add(index)
            if found == set(records):
                break
        if found != set(records):
            raise ValueError("missing selected Long episode in " + name)
        if progress:
            progress({"stage": "selected_train_validation_only", "shard": name, "windows_total": len(rows)})
    rows.sort(key=lambda r: (r["split"] != "train", r["task_name"], r["episode_id"], r["start_step"]))
    changes.sort(key=lambda r: r["window_id"])
    payload = {"schema_version": 1, "version": FUTURE_VERSION, "suite": SUITE, "dataset_name": DATASET,
               "protocol_signature": protocol.payload["content_signature"], "source_signature": protocol.payload["source_signature"],
               "dataset_asset_sha256": file_sha256(asset_path), "registration_sha256": protocol.payload["registration_sha256"],
               "source_files": sources, "horizon": HORIZON, "train_selection_seed": TRAIN_SEED, "validation_seed": VALIDATION_SEED,
               "task_catalog": protocol.payload["task_catalog"], "development_task_ids": DEVELOPMENT_TASK_IDS,
               "selected_episodes": {s: [e.episode_id for e in refs] for s, refs in planned.items()}, "windows": rows,
               "summary": _window_summary(planned, rows), "exclusions": [], "test_pixels_opened": False,
               "action_target_version": ACTION_TARGET_VERSION,
               "time_alignment": {"current": "obs[t] before action[t]", "action_interval": "[t,t+8)", "future": "obs[t+8]",
                   "index_unit": "regenerated no-op-filtered simulator control transitions", "raw_demo_timestamps_available": False,
                   "padding": "forbidden", "phase_rule": "first/middle/last legal start; not semantic task stages"}}
    manifest = signed_payload(payload, WINDOW_NAMESPACE)
    diagnostics = {"schema_version": 1, "version": "h8-raw-endpoint-change-v1", "suite": SUITE,
                   "window_manifest_signature": manifest["content_signature"], "source_signature": payload["source_signature"],
                   "diagnostics_used_for_selection": False, "test_pixels_opened": False,
                   "limitations": "Descriptive endpoint/path changes only. RGB changes include camera motion and appearance; proprio does not measure object progress. None identifies semantic subtask transitions. Repeated windows within episode are dependent.",
                   "rows": changes, "summary": summarize_endpoint_changes(changes)}
    return manifest, signed_payload(diagnostics, "cti-vla:long-future-endpoint-diagnostics:v1")


def load_future_windows(path, protocol):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    verify_payload(payload, WINDOW_NAMESPACE)
    for key, expected in {"schema_version": 1, "version": FUTURE_VERSION, "suite": SUITE, "dataset_name": DATASET,
        "protocol_signature": protocol.payload["content_signature"], "source_signature": protocol.payload["source_signature"],
        "dataset_asset_sha256": protocol.payload["dataset_asset_sha256"], "registration_sha256": protocol.payload["registration_sha256"],
        "horizon": HORIZON, "train_selection_seed": TRAIN_SEED, "validation_seed": VALIDATION_SEED,
        "task_catalog": protocol.payload["task_catalog"], "development_task_ids": DEVELOPMENT_TASK_IDS,
        "action_target_version": ACTION_TARGET_VERSION, "exclusions": [], "test_pixels_opened": False}.items():
        if payload.get(key) != expected:
            raise ValueError("Long future manifest differs from registration/source: " + key)
    planned = planned_future_episodes(protocol)
    if payload["selected_episodes"] != {s: [e.episode_id for e in refs] for s, refs in planned.items()}:
        raise ValueError("Long future panel differs from deterministic selection")
    rows = payload["windows"]
    expected = {(s, e.episode_id, p) for s, refs in planned.items() for e in refs for p in PHASES}
    actual = {(r["split"], r["episode_id"], r["phase"]) for r in rows}
    if len(rows) != 150 or actual != expected or len(actual) != len(rows) or len({r["window_id"] for r in rows}) != len(rows):
        raise ValueError("Long future manifest must have exact90train/60validation windows")
    for row in rows:
        _validate_registered_row(row, protocol)
    if payload["summary"] != _window_summary(planned, rows):
        raise ValueError("Long future coverage summary mismatch")
    required = {r["source_shard"] for r in rows}
    if payload["source_files"] != {name: source for name, source in protocol.payload["source_files"].items() if name in required}:
        raise ValueError("Long future source receipts differ from protocol")
    return payload


# Explicit aliases support callers that route both suites in the same module.
load_long_protocol = load_long_future_protocol
load_long_future_windows = load_future_windows

__all__ = ["LongFutureProtocol", "load_long_future_protocol", "load_long_protocol", "load_future_windows",
           "load_long_future_windows", "validate_future_window", "normalize_demo_actions", "require_future_episode",
           "planned_future_episodes", "build_long_future_protocol", "build_future_windows", "probe_episode_metadata",
           "registration_payload", "endpoint_change_diagnostics", "rotation_distance"]

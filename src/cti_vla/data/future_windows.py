"""G1-F same-episode future windows and native OFT demonstration actions.

Indices refer to the regenerated no-noop control trajectory, not raw-demo
timestamps. obs[t] precedes actions[t]; actions[t:t+h] lead to obs[t+h].
There is no saved post-final-action observation and no tail padding here.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import replace
import json
from pathlib import Path, PurePosixPath
import random
from typing import Mapping

import numpy as np

from .experiment_protocol import ExperimentProtocol
from .identity import canonical_mapping_signature, file_sha256
from .libero import LIBERO_SPATIAL_DATASET, load_manifest
from .sequence_example import LiberoEpisode, decode_libero_example
from .tfrecord import iter_tfrecord_records

FUTURE_VERSION = "g1-future-windows-h8-v1"
ACTION_TARGET_VERSION = "libero-native-oft-gripper-invert-clip-boundsq99-constant-zero-v1"
HORIZON = 8
VALIDATION_SEED = 517
PHASES = ("early", "middle", "late")
WINDOW_FIELDS = {
    "window_id", "episode_id", "source_shard", "record_index", "num_steps", "task_name", "split", "phase",
    "start_step", "future_step", "action_start", "action_stop_exclusive", "horizon", "future_is_last", "future_is_terminal",
}


def _signature(payload):
    return canonical_mapping_signature(payload, namespace="cti-vla:future-windows:v1")


def _window_id(episode_id, start, horizon):
    return canonical_mapping_signature({"dataset_name": LIBERO_SPATIAL_DATASET, "episode_id": episode_id,
                                        "start_step": start, "horizon": horizon}, namespace="cti-vla:future-window:v1")


def require_future_episode(protocol: ExperimentProtocol, episode_id: str, split: str):
    """Episode membership only: new starts need not be in the old step whitelist."""
    if split not in ("train", "validation"):
        raise ValueError("G1-F permits only train/effective validation; test is sealed")
    if episode_id in protocol.excluded_episode_ids:
        raise ValueError("engineering-only episode is quarantined")
    matches = [(name, ref) for name, manifest in protocol.manifests.items()
               for ref in manifest.episodes if ref.episode_id == episode_id]
    if len(matches) != 1 or matches[0][0] != split:
        raise ValueError("future window does not match the authoritative episode split")
    return matches[0][1]


def legal_future_starts(num_steps: int, horizon: int = HORIZON):
    if type(num_steps) is not int or num_steps <= 0 or type(horizon) is not int or horizon != HORIZON:
        raise ValueError("G1-F v1 requires positive episode length and fixed horizon8")
    last = num_steps - horizon - 1
    if last < 2:
        return ()  # Require three distinct current observations; do not duplicate.
    return (0, last // 2, last)


def planned_future_episodes(protocol: ExperimentProtocol, validation_seed: int = VALIDATION_SEED):
    if type(validation_seed) is not int or validation_seed != VALIDATION_SEED:
        raise ValueError("G1-F v1 validation selection seed is frozen at517")
    panel_ref = protocol.payload["panels"]["diagnostic_90"]
    path = protocol.path.parent / panel_ref["path"]
    if file_sha256(path) != panel_ref["sha256"]:
        raise ValueError("future train parent panel changed")
    panel = load_manifest(path)
    train = tuple(sorted((require_future_episode(protocol, e.episode_id, "train") for e in panel.episodes), key=lambda e: e.episode_id))
    if len(train) != 30 or len({e.task_name for e in train}) != 10:
        raise ValueError("G1-F requires the frozen diagnostic30 training episodes")
    validation = []
    for task in sorted({e.task_name for e in train}):
        pool = sorted((e for e in protocol.manifests["validation"].episodes
                       if e.task_name == task and e.episode_id not in protocol.excluded_episode_ids), key=lambda e: e.episode_id)
        if len(pool) < 2:
            raise ValueError("each task requires two effective-validation episodes")
        seed = canonical_mapping_signature({"seed": validation_seed, "task": task}, namespace="cti-vla:future-validation-selection:v1")
        validation.extend(random.Random(seed).sample(pool, 2))
    return {"train": train, "validation": tuple(sorted(validation, key=lambda e: e.episode_id))}


def _row(ref, split, phase, start, terminal):
    future = start + HORIZON
    return {"window_id": _window_id(ref.episode_id, start, HORIZON), "episode_id": ref.episode_id,
            "source_shard": ref.source_shard, "record_index": ref.record_index, "num_steps": ref.num_steps,
            "task_name": ref.task_name, "split": split, "phase": phase, "start_step": start, "future_step": future,
            "action_start": start, "action_stop_exclusive": future, "horizon": HORIZON,
            "future_is_last": future == ref.num_steps - 1, "future_is_terminal": bool(terminal)}


def _validate_registered_row(window, protocol):
    if not isinstance(window, dict) or set(window) != WINDOW_FIELDS:
        raise ValueError("future window fields mismatch")
    ref = require_future_episode(protocol, window["episode_id"], window["split"])
    starts = legal_future_starts(ref.num_steps)
    if not starts or window["phase"] not in PHASES:
        raise ValueError("future episode lacks three valid distinct starts or phase")
    start = starts[PHASES.index(window["phase"])]
    if type(window["future_is_terminal"]) is not bool or type(window["future_is_last"]) is not bool:
        raise ValueError("future flags must be booleans")
    if window["future_is_terminal"] and not window["future_is_last"]:
        raise ValueError("future terminal marker precedes episode end")
    expected = _row(ref, window["split"], window["phase"], start, window["future_is_terminal"])
    if window != expected or any(type(window[k]) is not int for k in
                                 ("record_index", "num_steps", "start_step", "future_step", "action_start", "action_stop_exclusive", "horizon")):
        raise ValueError("future window interval/identity differs from its registered episode")
    return ref


def validate_future_window(window: dict, episode: LiberoEpisode, protocol: ExperimentProtocol) -> None:
    """Required before caching: validate decoded content, timing, conditions and flags."""
    ref = _validate_registered_row(window, protocol)
    if episode.episode_id != ref.episode_id or episode.source_shard != ref.source_shard or episode.record_index != ref.record_index or episode.num_steps != ref.num_steps:
        raise ValueError("runtime episode content ID/length/storage locator differs from future window")
    n = ref.num_steps
    for name in ("is_first", "is_last", "is_terminal"):
        flags = getattr(episode, name)
        if flags.shape != (n,) or flags.dtype != np.bool_:
            raise ValueError("invalid runtime episode flags")
    if not episode.is_first[0] or episode.is_first[1:].any() or not episode.is_last[-1] or episode.is_last[:-1].any() or episode.is_terminal[:-1].any():
        raise ValueError("runtime first/last/terminal flags break episode boundaries")
    start, future = window["start_step"], window["future_step"]
    if episode.is_last[start:future].any() or episode.is_terminal[start:future].any() or episode.is_first[start + 1:future + 1].any():
        raise ValueError("future window crosses a terminal or restart boundary")
    if bool(episode.is_last[future]) != window["future_is_last"] or bool(episode.is_terminal[future]) != window["future_is_terminal"]:
        raise ValueError("registered future flags differ from runtime episode")
    if len(episode.instructions) != n or any(text != ref.task_name for text in episode.instructions):
        raise ValueError("runtime future episode instruction changed")
    if episode.actions.shape != (n, 7) or episode.proprio.shape != (n, 8) or not np.isfinite(episode.actions).all() or not np.isfinite(episode.proprio).all():
        raise ValueError("invalid runtime action/proprio arrays")
    if len(episode.images) != n or len(episode.wrist_images) != n or episode.actions[start:future].shape != (HORIZON, 7):
        raise ValueError("future actions or paired camera observations are incomplete")


def normalize_demo_actions(raw_actions, action_stats: Mapping) -> np.ndarray:
    """Native OFT LIBERO transform + BOUNDS_Q99, with checkpoint statistics.

    Return float32[h,7]. The gripper becomes 1=open,0=closed and is unscaled.
    This does not fit statistics; callers must bind the immutable checkpoint
    dataset_statistics.json hash and selected stats key in cache provenance.
    """
    raw = np.asarray(raw_actions, dtype=np.float32)
    if raw.shape != (HORIZON, 7) or not np.isfinite(raw).all():
        raise ValueError("demonstration actions must be finite [8,7]")
    arrays = {name: np.asarray(action_stats[name], dtype=np.float32) for name in ("q01", "q99", "min", "max")}
    if any(value.shape != (7,) or not np.isfinite(value).all() for value in arrays.values()):
        raise ValueError("checkpoint action statistics must have seven finite dimensions")
    if "mask" not in action_stats:
        raise ValueError("checkpoint action normalization mask must be explicit")
    mask = np.asarray(action_stats["mask"])
    if mask.dtype != np.bool_ or mask.shape != (7,) or mask.tolist() != [True] * 6 + [False]:
        raise ValueError("native LIBERO action mask must normalize six pose dimensions, excluding gripper")
    if np.any(arrays["q01"] > arrays["q99"]) or np.any(arrays["min"] > arrays["max"]):
        raise ValueError("invalid checkpoint action bounds")
    actions = raw.copy()
    actions[:, -1] = 1.0 - np.clip(actions[:, -1], 0.0, 1.0)
    normalized = np.clip(2.0 * (actions - arrays["q01"]) / (arrays["q99"] - arrays["q01"] + np.float32(1e-8)) - 1.0, -1.0, 1.0)
    output = np.where(mask, normalized, actions)
    output = np.where(arrays["min"] == arrays["max"], np.float32(0), output).astype(np.float32)
    if not np.isfinite(output).all():
        raise ValueError("nonfinite normalized demonstration actions")
    return np.ascontiguousarray(output)


def _summary(planned, rows):
    by_split = {}
    for split, episodes in planned.items():
        by_task = {}
        for task in sorted({e.task_name for e in episodes}):
            refs = [e for e in episodes if e.task_name == task]
            windows = [r for r in rows if r["split"] == split and r["task_name"] == task]
            by_task[task] = {"selected_episodes": len(refs), "windows": len(windows),
                             "phase_counts": dict(Counter(w["phase"] for w in windows)),
                             "possible_future_start_count": sum(max(e.num_steps - HORIZON, 0) for e in refs),
                             "tail_starts_without_future": sum(min(e.num_steps, HORIZON) for e in refs),
                             "episodes_without_three_starts": sum(not legal_future_starts(e.num_steps) for e in refs)}
        by_split[split] = {"episodes": len(episodes), "windows": sum(v["windows"] for v in by_task.values()), "by_task": by_task}
    return by_split


def build_future_windows(protocol: ExperimentProtocol, data_directory, asset_manifest, *, progress=None) -> dict:
    """Hash source shards, decode selected train/validation records, freeze timing.

    Other records' TFRecord envelopes are checked but their observations/actions
    are never decoded. No test episode becomes a window or model input.
    """
    data_directory, asset_manifest = Path(data_directory), Path(asset_manifest)
    asset = json.loads(asset_manifest.read_text(encoding="utf-8"))
    if asset["repository"] != "openvla/modified_libero_rlds" or asset["revision"] != "6ce6aaaaabdbe590b1eef5cd29c0d33f14a08551":
        raise ValueError("future windows require the pinned Spatial dataset")
    specs = {PurePosixPath(r["path"]).name: r for r in asset["files"]}
    planned = planned_future_episodes(protocol)
    wanted = defaultdict(dict)
    exclusions = []
    for split, episodes in planned.items():
        for ref in episodes:
            if not legal_future_starts(ref.num_steps):
                exclusions.append({"split": split, "episode_id": ref.episode_id, "reason": "fewer_than_three_distinct_h8_starts", "num_steps": ref.num_steps})
            else:
                wanted[ref.source_shard][ref.record_index] = (split, ref)
    sources, rows = {}, []
    for name, records in sorted(wanted.items()):
        path, spec = data_directory / name, specs[name]
        actual = {"bytes": path.stat().st_size, "sha256": file_sha256(path)}
        if actual != {"bytes": spec["size"], "sha256": spec["lfs_oid"]}:
            raise ValueError(f"future data source hash differs: {name}")
        sources[name] = actual
        found = set()
        for index, payload in iter_tfrecord_records(path):
            if index not in records:
                continue
            split, ref = records[index]
            episode = replace(decode_libero_example(payload), source_shard=name, record_index=index)
            for phase, start in zip(PHASES, legal_future_starts(ref.num_steps)):
                if start + HORIZON >= episode.num_steps:
                    raise ValueError("runtime episode too short for registered future")
                row = _row(ref, split, phase, start, episode.is_terminal[start + HORIZON])
                validate_future_window(row, episode, protocol)
                rows.append(row)
            found.add(index)
            if found == set(records):
                break
        if found != set(records):
            raise ValueError(f"missing selected future episode in {name}")
        if progress:
            progress({"shard": name, "selected_episodes_verified": len(found), "windows_total": len(rows)})
    rows.sort(key=lambda r: (0 if r["split"] == "train" else 1, r["task_name"], r["episode_id"], r["start_step"]))
    payload = {"schema_version": 1, "version": FUTURE_VERSION, "dataset_name": LIBERO_SPATIAL_DATASET,
               "protocol_signature": protocol.payload["content_signature"], "source_signature": protocol.payload["source_signature"],
               "horizon": HORIZON, "validation_seed": VALIDATION_SEED,
               "train_parent_panel_sha256": protocol.payload["panels"]["diagnostic_90"]["sha256"],
               "dataset_asset_sha256": file_sha256(asset_manifest), "source_files": sources,
               "selected_episodes": {split: [e.episode_id for e in refs] for split, refs in planned.items()},
               "windows": rows, "exclusions": exclusions, "summary": _summary(planned, rows),
               "time_alignment": {"version": "regenerated-noop-skipped-before-step-same-index-rlds-v1",
                                  "current": "obs[t] before action[t]", "action_interval": "[t,t+8)", "future": "obs[t+8]",
                                  "index_unit": "regenerated simulator control transition", "raw_demo_timestamps_available": False,
                                  "padding": "forbidden", "phase_rule": "first/middle/last legal start; phases refer to legal-start range",
                                  "terminal_marker": "RLDS terminal flag labels its outgoing action/step; it is not a saved post-final-action frame"},
               "action_target_version": ACTION_TARGET_VERSION}
    return {**payload, "content_signature": _signature(payload)}


def load_future_windows(path, protocol: ExperimentProtocol) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    unsigned = dict(payload)
    signature = unsigned.pop("content_signature", None)
    if signature != _signature(unsigned):
        raise ValueError("future manifest content signature mismatch")
    if payload["schema_version"] != 1 or payload["version"] != FUTURE_VERSION or payload["horizon"] != HORIZON or payload["validation_seed"] != VALIDATION_SEED:
        raise ValueError("future manifest version/horizon/seed changed")
    if payload["protocol_signature"] != protocol.payload["content_signature"] or payload["source_signature"] != protocol.payload["source_signature"] or payload["train_parent_panel_sha256"] != protocol.payload["panels"]["diagnostic_90"]["sha256"]:
        raise ValueError("future manifest differs from pinned protocol/source/parent")
    if payload["action_target_version"] != ACTION_TARGET_VERSION or payload["dataset_name"] != LIBERO_SPATIAL_DATASET:
        raise ValueError("future dataset/action semantics differ")
    planned = planned_future_episodes(protocol, payload["validation_seed"])
    expected_members = {split: [e.episode_id for e in refs] for split, refs in planned.items()}
    if payload["selected_episodes"] != expected_members:
        raise ValueError("future episode selection differs from frozen rule")
    expected = {(split, e.episode_id, phase) for split, refs in planned.items() for e in refs if legal_future_starts(e.num_steps) for phase in PHASES}
    rows = payload["windows"]
    actual = {(r["split"], r["episode_id"], r["phase"]) for r in rows}
    if actual != expected or len(actual) != len(rows) or len({r["window_id"] for r in rows}) != len(rows):
        raise ValueError("future manifest has missing, repeated or unregistered windows")
    for row in rows:
        _validate_registered_row(row, protocol)
    expected_exclusions = [{"split": split, "episode_id": e.episode_id, "reason": "fewer_than_three_distinct_h8_starts", "num_steps": e.num_steps}
                           for split, refs in planned.items() for e in refs if not legal_future_starts(e.num_steps)]
    if payload["exclusions"] != expected_exclusions or payload["summary"] != _summary(planned, rows):
        raise ValueError("future exclusions/coverage summary differs")
    # The selected shard receipts are checked against the preexisting asset list,
    # not self-pinned by a recomputed manifest signature.
    asset_path = protocol.path.resolve().parents[3] / "configs/assets/libero_spatial_rlds.json"
    asset = json.loads(asset_path.read_text(encoding="utf-8"))
    required = {r["source_shard"] for r in rows}
    registered = {PurePosixPath(r["path"]).name: {"bytes": r["size"], "sha256": r["lfs_oid"]}
                  for r in asset["files"] if "lfs_oid" in r and PurePosixPath(r["path"]).name in required}
    if payload["dataset_asset_sha256"] != file_sha256(asset_path) or payload["source_files"] != registered:
        raise ValueError("future source receipts differ from immutable dataset asset")
    return payload


__all__ = ["FUTURE_VERSION", "ACTION_TARGET_VERSION", "HORIZON", "VALIDATION_SEED", "legal_future_starts",
           "require_future_episode", "planned_future_episodes", "normalize_demo_actions", "validate_future_window",
           "build_future_windows", "load_future_windows"]

"""Formal four-suite, full-pool h8 windows. No model or image decoding.

Inventory reads protobuf structure, text and flags, and hashes compressed step
payloads. Test records receive identities only; no test window is constructed.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

import numpy as np

from .experiment_protocol import signed_payload, verify_payload, task_key, load_experiment_protocol
from .future_windows import normalize_demo_actions, ACTION_TARGET_VERSION
from .identity import canonical_mapping_signature, file_sha256
from .initial_states import official_task_catalog
from .libero import LiberoEpisodeRef, split_episodes
from .sequence_example import _example_class, _episode_content_id
from .tfrecord import iter_tfrecord_records

SUITES = {"libero_spatial": "libero_spatial_no_noops", "libero_10": "libero_10_no_noops",
          "libero_object": "libero_object_no_noops", "libero_goal": "libero_goal_no_noops"}
VERSION = "formal-main-v2-full-pool-h8"
PROTOCOL_NAMESPACE = "cti-vla:formal-main-protocol:v2"
WINDOW_NAMESPACE = "cti-vla:formal-main-windows:v2"
HORIZON, NEW_SPLIT_SEED = 8, 20261016
PHASES = ("early", "middle", "late")
DATASET_REVISION = "6ce6aaaaabdbe590b1eef5cd29c0d33f14a08551"
LIBERO_REVISION = "8f1084e3132a39270c3a13ebe37270a43ece2a01"
OFFICIAL_MAPPING = {"task_order_index": 0,
    "task_map_sha256": "dc644c34987f6e0e4dc5320e5168cd2ee170cb8520f6a9344d2cd6d50f2c55fc",
    "benchmark_source_sha256": "b1c7bcbe75150e123c2d250cf455c7ed7333b76d21c78ec122a5c02544d19b83"}
PARENTS = {"libero_spatial": "configs/manifests/spatial_g0g1_v1/protocol.json",
           "libero_10": "configs/manifests/long_future_v1/protocol.json"}
SERVER_PROJECT_ROOTS = ("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA",
                        "/share/home/u15016/XXY_CVPR/CTI-VLA")


def _within(root, path):
    path = Path(path).resolve()
    if Path(root).resolve() not in path.parents:
        raise ValueError("formal asset must remain inside project")
    return path


def data_location_allowed(project, path):
    """Resolved paths only: the two explicitly authorized CTI-VLA disks."""
    project, path = PurePosixPath(project), PurePosixPath(path)
    if ".." in path.parts or ".." in project.parts:
        return False
    if project.as_posix() in SERVER_PROJECT_ROOTS:
        return any(PurePosixPath(root) / "data" in path.parents for root in SERVER_PROJECT_ROOTS)
    return project in path.parents


def _data_directory(project, path):
    path = Path(path).resolve()
    if not data_location_allowed(Path(project).resolve().as_posix(), path.as_posix()):
        raise ValueError("data must belong to this project or its two registered server data roots")
    return path


def catalog_for_suite(project, suite):
    if suite not in SUITES:
        raise ValueError("unsupported formal suite")
    catalog, mapping = official_task_catalog(Path(project) / "external/LIBERO", suite)
    if mapping != OFFICIAL_MAPPING:
        raise ValueError("official task mapping changed")
    return [{**row, "instruction": re.sub(r"^.*?SCENE\d+_", "", row["task_name"]).replace("_", " ")}
            for row in catalog]


def _spec_sha(spec):
    return spec.get("sha256", spec.get("lfs_oid"))


def load_formal_asset(path, suite):
    asset = json.loads(Path(path).read_text(encoding="utf-8"))
    if (asset.get("repository"), asset.get("revision"), asset.get("dataset_path")) != (
        "openvla/modified_libero_rlds", DATASET_REVISION, SUITES[suite] + "/1.0.0"):
        raise ValueError("formal dataset asset repository/revision/path differs")
    if asset.get("suite", suite) != suite or type(asset.get("episode_count")) is not int or asset["episode_count"] < 30:
        raise ValueError("formal dataset suite/episode count invalid")
    sources = {}
    names = set()
    for spec in asset["files"]:
        name = PurePosixPath(spec["path"]).name
        if name in names or spec["path"] != asset["dataset_path"] + "/" + name or type(spec["size"]) is not int or spec["size"] <= 0:
            raise ValueError("formal dataset file identity invalid")
        names.add(name)
        if ".tfrecord-" in name:
            if not re.fullmatch(r"[0-9a-f]{64}", _spec_sha(spec) or ""):
                raise ValueError("immutable shard SHA256 required")
            sources[name] = {"bytes": spec["size"], "sha256": _spec_sha(spec)}
        elif name not in {"dataset_info.json", "features.json"} or not (
            re.fullmatch(r"[0-9a-f]{40}", spec.get("git_blob_sha1", "")) or
            re.fullmatch(r"[0-9a-f]{64}", _spec_sha(spec) or "")):
            raise ValueError("formal metadata identity invalid")
    if not sources or names - set(sources) != {"dataset_info.json", "features.json"} or sum(f["size"] for f in asset["files"]) != asset["total_bytes"]:
        raise ValueError("formal asset inventory incomplete")
    return asset, dict(sorted(sources.items()))


def verify_source_file(path, spec):
    path = Path(path)
    if path.stat().st_size != spec["bytes"] or file_sha256(path) != spec["sha256"]:
        raise ValueError("formal source bytes/SHA mismatch: " + path.name)


def _metadata_counts(data, asset, sources):
    parsed = {}
    for name in ("dataset_info.json", "features.json"):
        spec = next(s for s in asset["files"] if s["path"].endswith("/" + name))
        value = (Path(data) / name).read_bytes()
        digest = hashlib.sha256(value).hexdigest() if _spec_sha(spec) else hashlib.sha1(f"blob {len(value)}\0".encode() + value).hexdigest()
        if len(value) != spec["size"] or digest != (_spec_sha(spec) or spec["git_blob_sha1"]):
            raise ValueError("immutable dataset metadata mismatch")
        parsed[name] = json.loads(value)
    info = parsed["dataset_info.json"]
    if info.get("version") != "1.0.0" or len(info["splits"]) != 1 or info["splits"][0]["name"] != "train":
        raise ValueError("unexpected official RLDS split")
    lengths = [int(n) for n in info["splits"][0]["shardLengths"]]
    expected_names = [f"{info['name']}-train.tfrecord-{i:05d}-of-{len(lengths):05d}" for i in range(len(lengths))]
    if sorted(sources) != expected_names or sum(lengths) != asset["episode_count"]:
        raise ValueError("official record count/shard list mismatch")
    return dict(zip(expected_names, lengths))


def probe_formal_episode(payload, source_shard, record_index, catalog):
    """No JPEG decoder or numeric action/state NumPy materialization is called."""
    if not isinstance(payload, bytes) or not payload or len(payload) > 512 * 1024 * 1024:
        raise ValueError("invalid inventory payload")
    msg = _example_class()()
    msg.ParseFromString(payload)
    f = msg.features.feature
    kinds = {"steps/action": ("float_list", 7), "steps/observation/state": ("float_list", 8),
        "steps/observation/joint_state": ("float_list", 7), "steps/reward": ("float_list", 1),
        "steps/discount": ("float_list", 1), "steps/is_first": ("int64_list", 1),
        "steps/is_last": ("int64_list", 1), "steps/is_terminal": ("int64_list", 1),
        "steps/language_instruction": ("bytes_list", 1), "steps/observation/image": ("bytes_list", 1),
        "steps/observation/wrist_image": ("bytes_list", 1)}
    if not set(kinds).union({"episode_metadata/file_path"}) <= set(f):
        raise ValueError("inventory missing required features")
    n = len(f["steps/is_first"].int64_list.value)
    if not 3 <= n <= 10000:
        raise ValueError("invalid inventory length")
    for key, (kind, width) in kinds.items():
        if f[key].WhichOneof("kind") != kind or len(getattr(f[key], kind).value) != n * width:
            raise ValueError("inventory feature length/type mismatch")
    flags = {name: tuple(f["steps/" + name].int64_list.value) for name in ("is_first", "is_last", "is_terminal")}
    if (flags["is_first"] != (1,) + (0,) * (n - 1) or flags["is_last"] != (0,) * (n - 1) + (1,)
        or flags["is_terminal"][:-1] != (0,) * (n - 1) or flags["is_terminal"][-1] not in (0, 1)):
        raise ValueError("episode first/last/terminal boundary violation")
    instructions = f["steps/language_instruction"].bytes_list.value
    text = instructions[0].decode("utf-8", errors="strict")
    if any(value != instructions[0] for value in instructions):
        raise ValueError("instruction changed inside episode")
    path_field = f["episode_metadata/file_path"]
    if path_field.WhichOneof("kind") != "bytes_list" or len(path_field.bytes_list.value) != 1:
        raise ValueError("episode original path invalid")
    ref = LiberoEpisodeRef(_episode_content_id(msg), n, text, source_shard, record_index,
                           path_field.bytes_list.value[0].decode("utf-8", errors="strict"))
    tasks = {task["task_name"]: task["instruction"] for task in catalog}
    if tasks.get(task_key(ref)) != text:
        raise ValueError("episode task name/instruction differs from official catalog")
    return ref, bool(flags["is_terminal"][-1])


def deduplicate_inventory(items):
    """One canonical locator per content ID; aliases never get another split."""
    grouped = defaultdict(list)
    for ref, terminal in items:
        grouped[ref.episode_id].append((ref, terminal))
    chosen, terminal_by_id, aliases = [], {}, {}
    for episode_id, rows in sorted(grouped.items()):
        rows.sort(key=lambda item: (item[0].source_shard, item[0].record_index))
        first, terminal = rows[0]
        if any((r.num_steps, r.task_name, task_key(r), t) != (first.num_steps, first.task_name, task_key(first), terminal) for r, t in rows):
            raise ValueError("duplicate content ID has conflicting episode metadata")
        chosen.append(first)
        terminal_by_id[episode_id] = terminal
        if len(rows) > 1:
            aliases[episode_id] = [asdict(r) for r, _ in rows]
    return chosen, terminal_by_id, aliases


def _parent(project, suite):
    if suite not in PARENTS:
        return None
    path = Path(project) / PARENTS[suite]
    if suite == "libero_spatial":
        return load_experiment_protocol(path)
    from .long_future_windows import load_long_future_protocol
    return load_long_future_protocol(path, Path(project) / "configs/assets/libero_long_rlds.json",
                                     Path(project) / "configs/experiments/g1_future_long_data_v1.json")


@dataclass(frozen=True)
class FormalEpisodeManifest:
    split: str
    episodes: tuple
    @property
    def episode_ids(self):
        return tuple(e.episode_id for e in self.episodes)


@dataclass(frozen=True)
class FormalProtocol:
    path: Path
    payload: dict
    manifests: dict
    excluded_episode_ids: frozenset
    episode_index: dict


def build_formal_protocol(data_directory, asset_manifest, *, project_root, suite, progress=None):
    project = Path(project_root).resolve()
    data, asset_path = _data_directory(project, data_directory), _within(project, asset_manifest)
    asset, sources = load_formal_asset(asset_path, suite)
    counts = _metadata_counts(data, asset, sources)
    catalog = catalog_for_suite(project, suite)
    items = []
    for name, spec in sources.items():
        verify_source_file(data / name, spec)
        records = 0
        for index, payload in iter_tfrecord_records(data / name):
            items.append(probe_formal_episode(payload, name, index, catalog))
            records += 1
        if records != counts[name]:
            raise ValueError("actual shard record count differs from immutable metadata")
        if progress:
            progress({"shard": name, "records": records, "rgb_decodes": 0})
    refs, terminals, aliases = deduplicate_inventory(items)
    parent = _parent(project, suite)
    if parent:
        inherited = [e for m in parent.manifests.values() for e in m.episodes]
        if sorted(refs, key=lambda e: e.episode_id) != sorted(inherited, key=lambda e: e.episode_id) or aliases:
            raise ValueError("formal inventory differs from inherited split; do not redraw or silently deduplicate")
        splits = {s: m.episodes for s, m in parent.manifests.items()}
        excluded = sorted(parent.excluded_episode_ids)
        inherited_source = {"path": PARENTS[suite], "sha256": file_sha256(parent.path)}
        seed = 17
    else:
        splits = split_episodes(refs, seed=NEW_SPLIT_SEED)
        excluded, inherited_source, seed = [], None, NEW_SPLIT_SEED
    payload = {"schema_version": 2, "version": VERSION, "suite": suite, "dataset_name": SUITES[suite],
        "dataset_revision": DATASET_REVISION, "dataset_asset": asset_path.relative_to(project).as_posix(),
        "dataset_asset_sha256": file_sha256(asset_path), "source_files": sources,
        "source_signature": canonical_mapping_signature(sources, namespace="cti-vla:formal-rlds-source:v2"),
        "task_catalog": catalog, "official_mapping": OFFICIAL_MAPPING, "split_seed": seed,
        "split_fractions": {"train": .7, "validation": .15, "test": .15}, "inherited_protocol": inherited_source,
        "episodes_by_split": {s: [asdict(e) for e in sorted(es, key=lambda e: e.episode_id)] for s, es in splits.items()},
        "excluded_episode_ids": excluded, "terminal_by_episode": terminals, "duplicate_aliases": aliases,
        "raw_episode_count": len(items), "unique_episode_count": len(refs), "shard_episode_counts": counts,
        "horizon": HORIZON, "train_rule": "all legal starts 0..N-9, no padding or subset",
        "validation_rule": "per effective episode first/middle/last legal start, deduplicated; no short-episode replacement",
        "phase_rule": "thirds of legal-start index range; semantic stage not inferred",
        "test_pixels_opened": False, "inventory_scope": "protobuf text/lengths/boundaries and compressed-content hashes; zero RGB decodes or numeric action/state array materialization"}
    return signed_payload(payload, PROTOCOL_NAMESPACE)


def load_formal_protocol(path, project_root=None):
    path = Path(path).resolve()
    project = Path(project_root).resolve() if project_root else path.parents[4]
    payload = json.loads(path.read_text(encoding="utf-8"))
    verify_payload(payload, PROTOCOL_NAMESPACE)
    suite = payload["suite"]
    if payload.get("schema_version") != 2 or payload.get("version") != VERSION or suite not in SUITES or payload.get("horizon") != 8 or payload.get("test_pixels_opened") is not False:
        raise ValueError("unsupported formal protocol")
    asset_path = _within(project, project / payload["dataset_asset"])
    asset, sources = load_formal_asset(asset_path, suite)
    if (payload["dataset_asset_sha256"] != file_sha256(asset_path) or payload["source_files"] != sources
        or payload["source_signature"] != canonical_mapping_signature(sources, namespace="cti-vla:formal-rlds-source:v2")
        or payload["task_catalog"] != catalog_for_suite(project, suite) or payload["official_mapping"] != OFFICIAL_MAPPING
        or payload["dataset_name"] != SUITES[suite] or payload["dataset_revision"] != DATASET_REVISION):
        raise ValueError("formal source/catalog binding mismatch")
    if set(payload["episodes_by_split"]) != {"train", "validation", "test"}:
        raise ValueError("three episode splits required")
    manifests = {s: FormalEpisodeManifest(s, tuple(LiberoEpisodeRef(**r) for r in rows)) for s, rows in payload["episodes_by_split"].items()}
    index = {}
    catalog = {t["task_name"]: t for t in payload["task_catalog"]}
    for split, manifest in manifests.items():
        for ref in manifest.episodes:
            if ref.episode_id in index or ref.source_shard not in sources or not 0 <= ref.record_index < payload["shard_episode_counts"][ref.source_shard]:
                raise ValueError("episode identity/split/source collision")
            if catalog[task_key(ref)]["instruction"] != ref.task_name:
                raise ValueError("formal episode official task mismatch")
            index[ref.episode_id] = (split, ref)
    if (len(index) != payload["unique_episode_count"] or set(payload["terminal_by_episode"]) != set(index)
        or any(type(t) is not bool for t in payload["terminal_by_episode"].values())
        or payload["raw_episode_count"] != asset["episode_count"]
        or sum(payload["shard_episode_counts"].values()) != asset["episode_count"]):
        raise ValueError("formal inventory counts/flags inconsistent")
    parent = _parent(project, suite)
    if parent:
        if payload["inherited_protocol"] != {"path": PARENTS[suite], "sha256": file_sha256(parent.path)} or payload["split_seed"] != 17:
            raise ValueError("inherited formal protocol changed")
        if any(m.episodes != parent.manifests[s].episodes for s, m in manifests.items()) or payload["excluded_episode_ids"] != sorted(parent.excluded_episode_ids) or payload["duplicate_aliases"]:
            raise ValueError("inherited episode split/quarantine changed")
    else:
        expected = split_episodes([ref for _, ref in index.values()], seed=NEW_SPLIT_SEED)
        if payload["inherited_protocol"] is not None or payload["split_seed"] != NEW_SPLIT_SEED or payload["excluded_episode_ids"] or any(m.episodes != expected[s] for s, m in manifests.items()):
            raise ValueError("new suite split differs from preregistered stable hash rule")
    return FormalProtocol(path, payload, manifests, frozenset(payload["excluded_episode_ids"]), index)


def legal_starts(num_steps):
    if type(num_steps) is not int or num_steps < 1:
        raise ValueError("episode length must be a positive integer")
    return range(max(0, num_steps - HORIZON))


def validation_starts(num_steps):
    starts = legal_starts(num_steps)
    if not starts:
        return {}
    chosen = defaultdict(list)
    for label, start in zip(("first", "middle", "last"), (0, (len(starts) - 1) // 2, len(starts) - 1)):
        chosen[start].append(label)
    return dict(chosen)


def _window_row(protocol, ref, split, start):
    nvalid = len(legal_starts(ref.num_steps))
    task = next(t for t in protocol.payload["task_catalog"] if t["task_name"] == task_key(ref))
    future = start + HORIZON
    return {"window_id": canonical_mapping_signature({"dataset": protocol.payload["dataset_name"], "episode_id": ref.episode_id,
        "start": start, "horizon": HORIZON}, namespace="cti-vla:formal-window:v2"),
        "episode_id": ref.episode_id, "source_shard": ref.source_shard, "record_index": ref.record_index,
        "num_steps": ref.num_steps, "task_id": task["task_id"], "task_name": ref.task_name, "split": split,
        "phase": PHASES[min(2, 3 * start // nvalid)], "start_step": start, "future_step": future,
        "action_start": start, "action_stop_exclusive": future, "horizon": HORIZON,
        "future_is_last": future == ref.num_steps - 1,
        "future_is_terminal": future == ref.num_steps - 1 and protocol.payload["terminal_by_episode"][ref.episode_id],
        "selection_positions": validation_starts(ref.num_steps)[start] if split == "validation" else []}


def iter_formal_window_rows(protocol):
    catalog = {t["task_name"]: t["task_id"] for t in protocol.payload["task_catalog"]}
    for split in ("train", "validation"):
        refs = sorted(protocol.manifests[split].episodes, key=lambda e: (catalog[task_key(e)], e.episode_id))
        for ref in refs:
            if ref.episode_id in protocol.excluded_episode_ids:
                continue
            starts = legal_starts(ref.num_steps) if split == "train" else validation_starts(ref.num_steps)
            for start in starts:
                yield _window_row(protocol, ref, split, start)


def build_formal_windows(protocol):
    rows = list(iter_formal_window_rows(protocol))
    summary = {}
    for split in ("train", "validation"):
        selected = [r for r in rows if r["split"] == split]
        summary[split] = {"windows": len(selected), "episodes_with_windows": len({r["episode_id"] for r in selected}),
            "by_task": {str(task): {"windows": sum(r["task_id"] == task for r in selected),
                "episodes": len({r["episode_id"] for r in selected if r["task_id"] == task}),
                "by_phase": dict(Counter(r["phase"] for r in selected if r["task_id"] == task))} for task in range(10)},
            "short_episode_ids": sorted(e.episode_id for e in protocol.manifests[split].episodes if not legal_starts(e.num_steps)),
            "quarantined_episode_ids": sorted(set(protocol.manifests[split].episode_ids) & protocol.excluded_episode_ids)}
    return signed_payload({"schema_version": 2, "version": VERSION, "suite": protocol.payload["suite"],
        "protocol_signature": protocol.payload["content_signature"], "protocol_sha256": file_sha256(protocol.path),
        "source_signature": protocol.payload["source_signature"], "source_files": protocol.payload["source_files"],
        "dataset_asset_sha256": protocol.payload["dataset_asset_sha256"], "horizon": HORIZON,
        "action_target_version": ACTION_TARGET_VERSION, "test_pixels_opened": False,
        "windows": rows, "train_window_ids": [r["window_id"] for r in rows if r["split"] == "train"],
        "validation_window_ids": [r["window_id"] for r in rows if r["split"] == "validation"], "summary": summary}, WINDOW_NAMESPACE)


def load_formal_windows(path, protocol):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    verify_payload(payload, WINDOW_NAMESPACE)
    # Exact regeneration prevents signed truncation into a convenient subset.
    if payload != build_formal_windows(protocol):
        raise ValueError("formal window manifest differs from the complete registered pool")
    return payload


def validate_formal_window(row, episode, protocol):
    split, ref = protocol.episode_index.get(row.get("episode_id"), (None, None))
    if split not in ("train", "validation") or row.get("split") != split or ref.episode_id in protocol.excluded_episode_ids:
        raise ValueError("formal window split/quarantine violation; test is sealed")
    start = row.get("start_step")
    if type(start) is not int or start not in legal_starts(ref.num_steps) or (split == "validation" and start not in validation_starts(ref.num_steps)):
        raise ValueError("unregistered formal start")
    if row != _window_row(protocol, ref, split, start):
        raise ValueError("formal window metadata/time interval mismatch")
    if (episode.episode_id, episode.source_shard, episode.record_index, episode.num_steps, episode.episode_file_path) != (
        ref.episode_id, ref.source_shard, ref.record_index, ref.num_steps, ref.episode_file_path):
        raise ValueError("formal runtime content ID/length/source mismatch")
    n = ref.num_steps
    for name in ("is_first", "is_last", "is_terminal"):
        flags = getattr(episode, name)
        if flags.shape != (n,) or flags.dtype != np.bool_:
            raise ValueError("formal runtime flag shape/type invalid")
    if not episode.is_first[0] or episode.is_first[1:].any() or not episode.is_last[-1] or episode.is_last[:-1].any() or episode.is_terminal[:-1].any():
        raise ValueError("formal runtime terminal/restart boundary violation")
    future = start + HORIZON
    if bool(episode.is_terminal[-1]) != protocol.payload["terminal_by_episode"][ref.episode_id] or bool(episode.is_last[future]) != row["future_is_last"]:
        raise ValueError("formal runtime terminal metadata changed")
    if len(episode.instructions) != n or any(s != ref.task_name for s in episode.instructions):
        raise ValueError("formal runtime instruction mismatch")
    if episode.actions.shape != (n, 7) or episode.proprio.shape != (n, 8) or not np.isfinite(episode.actions).all() or not np.isfinite(episode.proprio).all():
        raise ValueError("formal runtime action/proprio invalid")
    if len(episode.images) != n or len(episode.wrist_images) != n or episode.actions[start:future].shape != (8, 7):
        raise ValueError("formal runtime h8 observations/actions incomplete")

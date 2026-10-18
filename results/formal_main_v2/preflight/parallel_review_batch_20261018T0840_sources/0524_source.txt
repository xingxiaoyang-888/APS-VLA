"""On-demand, bounded, shared formal features; the eligible pool is never cut.

Only registered train/validation episodes are decoded. CPU metadata indexes
the complete legal pool; tensors are generated on demand and stored in a
bounded shared cache. Cache eviction changes computation cost, never sampling.
"""
from __future__ import annotations

from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import struct
import time

import numpy as np
import torch

from cti_vla.evaluation.teacher_diagnostics import json_signature
from cti_vla.training.formal_future import (
    append_event, atomic_torch_save, capture_rng, file_sha256, load_torch,
    restore_rng, validate_provider_partition,
)

FORMAL_CACHE_VERSION = "formal-main-v2-shared-bounded-ordinary-cpu-records-v1"


@contextmanager
def exclusive_file_lock(path: Path):
    """OS releases this lock after process death; no stale-lock guessing."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            while True:
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(.05)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class BoundedRecordCache:
    """Atomic tensor files with a transaction-locked LRU and content hashes.

    The SQLite write transaction covers cache reads too, so another process
    cannot evict a file while it is being loaded. Per-key locks prevent two
    jobs from generating the same missing feature. Failed/orphan temporary
    writes are retained until an explicit cleanup; they are never cache hits.
    """
    def __init__(self, root: Path, *, identity: dict, max_bytes: int, event):
        if type(max_bytes) is not int or max_bytes <= 0:
            raise ValueError("cache capacity must be a positive byte count")
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.identity, self.identity_sha = identity, json_signature(identity)
        self.max_bytes, self.event = max_bytes, event
        with self._transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS entries (key TEXT PRIMARY KEY, relative_path TEXT NOT NULL, bytes INTEGER NOT NULL, sha256 TEXT NOT NULL, last_used INTEGER NOT NULL, pinned INTEGER NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            existing = db.execute("SELECT value FROM settings WHERE key='max_bytes'").fetchone()
            if existing and int(existing[0]) != max_bytes:
                raise ValueError("shared cache capacity differs between registered workers")
            db.execute("INSERT OR IGNORE INTO settings VALUES ('max_bytes', ?)", (str(max_bytes),))
            namespace = "identity:" + self.identity_sha
            serialized = json.dumps(identity, sort_keys=True, ensure_ascii=False, allow_nan=False)
            previous = db.execute("SELECT value FROM settings WHERE key=?", (namespace,)).fetchone()
            if previous and previous[0] != serialized:
                raise ValueError("cache identity collision")
            db.execute("INSERT OR IGNORE INTO settings VALUES (?,?)", (namespace, serialized))
        self._cleanup_orphans()

    @contextmanager
    def _transaction(self):
        connection = sqlite3.connect(self.root / "index.sqlite3", timeout=600., isolation_level=None)
        try:
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.execute("COMMIT")
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def key(self, logical_key):
        return hashlib.sha256((self.identity_sha + ":" + logical_key).encode()).hexdigest()

    def _safe_path(self, relative):
        path = (self.root / relative).resolve()
        if self.root not in path.parents or path.parent != self.root / "records" or path.suffix != ".pt" or len(path.stem) != 64:
            raise ValueError("cache entry path is not within this generated-record directory")
        int(path.stem, 16)
        return path

    def _load(self, key):
        with self._transaction() as db:
            row = db.execute("SELECT relative_path,bytes,sha256 FROM entries WHERE key=?", (key,)).fetchone()
            if row is None:
                return None
            path = self._safe_path(row[0])
            if not path.is_file() or path.stat().st_size != row[1] or file_sha256(path) != row[2]:
                raise ValueError("shared feature cache file is missing or corrupt; do not silently recompute")
            payload = load_torch(path)
            if payload.get("cache_identity_sha256") != self.identity_sha or payload.get("key") != key:
                raise ValueError("feature cache payload identity mismatch")
            db.execute("UPDATE entries SET last_used=? WHERE key=?", (time.time_ns(), key))
            return payload["record"]

    def _cleanup_orphans(self):
        """Remove only generated files absent from the committed cache index.

        Eviction deletes index rows before deleting their files. A process
        killed between these operations leaves harmless orphans, never an
        index pointing to a deleted file. The same transaction lock protects
        recovery from concurrent republication of an evicted key.
        """
        removed = []
        with self._transaction() as db:
            indexed = {row[0] for row in db.execute("SELECT relative_path FROM entries")}
            for path in (self.root / "records").glob("*.pt"):
                relative = path.relative_to(self.root).as_posix()
                if relative not in indexed:
                    safe = self._safe_path(relative)
                    size = safe.stat().st_size
                    safe.unlink()
                    removed.append({"key": safe.stem, "bytes": size})
            # A producer can die inside torch.save before publishing. The
            # transaction excludes live writers; only our exact temporary
            # filename format is eligible for recovery cleanup.
            for path in (self.root / "records").glob("*.partial"):
                if re.fullmatch(r"[0-9a-f]{64}\.pt\.[0-9a-f]{32}\.partial", path.name):
                    if path.resolve().parent != self.root / "records":
                        raise ValueError("cache temporary file escapes generated-record directory")
                    size = path.stat().st_size
                    path.unlink()
                    removed.append({"key": path.name, "bytes": size})
        for row in removed:
            self.event("cache_orphan_cleanup", **row)

    def _delete_evicted_files(self, evicted):
        with self._transaction() as db:
            for old in evicted:
                # A concurrent miss may already have republished this key.
                if db.execute("SELECT 1 FROM entries WHERE key=?", (old["key"],)).fetchone() is None:
                    path = self._safe_path("records/" + old["key"] + ".pt")
                    if path.exists():
                        path.unlink()

    def get_or_create(self, logical_key, build, *, pinned=False):
        key = self.key(logical_key)
        # 256 lock stripes bound the number of lock files. Hash collisions only
        # serialize unrelated cache misses and cannot change their contents.
        lock = self.root / "locks" / (key[:2] + ".lock")
        started = time.perf_counter()
        with exclusive_file_lock(lock):
            cached = self._load(key)
            if cached is not None:
                self.event("cache_hit", logical_key=logical_key, key=key, seconds=time.perf_counter() - started)
                return cached
            self.event("cache_miss", logical_key=logical_key, key=key)
            record = build()
            if not isinstance(record, dict):
                raise TypeError("feature cache producer must return a dictionary")
            path = self._safe_path("records/" + key + ".pt")
            payload = {"cache_identity_sha256": self.identity_sha, "key": key, "record": record}
            evicted = []
            with self._transaction() as db:
                # All eviction and publication is under the same cross-process
                # lock as loading. Files are generated by this class only.
                atomic_torch_save(path, payload)
                size, sha = path.stat().st_size, file_sha256(path)
                if size > self.max_bytes:
                    raise ValueError("one feature record exceeds the registered cache capacity")
                total = db.execute("SELECT COALESCE(SUM(bytes),0) FROM entries").fetchone()[0]
                while total + size > self.max_bytes:
                    old = db.execute("SELECT key,relative_path,bytes FROM entries WHERE pinned=0 ORDER BY last_used,key LIMIT 1").fetchone()
                    if old is None:
                        raise ValueError("pinned shared tensors exceed cache capacity")
                    old_path = self._safe_path(old[1])
                    if not old_path.is_file() or old_path.stat().st_size != old[2]:
                        raise ValueError("registered cache eviction target changed")
                    db.execute("DELETE FROM entries WHERE key=?", (old[0],))
                    total -= old[2]
                    evicted.append({"key": old[0], "bytes": old[2]})
                db.execute("INSERT INTO entries VALUES (?,?,?,?,?,?)",
                           (key, path.relative_to(self.root).as_posix(), size, sha, time.time_ns(), int(pinned)))
            self._delete_evicted_files(evicted)
            for value in evicted:
                self.event("cache_eviction", **value)
            self.event("cache_publish", logical_key=logical_key, key=key, bytes=size, sha256=sha,
                       seconds=time.perf_counter() - started)
            return record


class FormalRecordProvider:
    def __init__(self, *, protocol: dict, manifest: dict, data_directory: Path, components,
                 processor, policy, stats_key: str, cache_root: Path, cache_identity: dict,
                 events_path: Path, max_cache_bytes: int = 128 * 1024**3, ram_records: int = 2,
                 job_id: str):
        if type(ram_records) is not int or ram_records < 0:
            raise ValueError("RAM record capacity must be a nonnegative integer")
        self.protocol, self.manifest = protocol, manifest
        self.rows = {row["window_id"]: row for row in manifest["windows"]}
        if len(self.rows) != len(manifest["windows"]):
            raise ValueError("duplicate formal window IDs")
        self.train_window_ids, self.validation_window_ids = manifest["train_window_ids"], manifest["validation_window_ids"]
        validate_provider_partition(self)
        self.data_directory = Path(data_directory).resolve()
        self.components, self.processor, self.policy = components, processor, policy
        self.vla = components.vla
        self.stats_key, self.device = stats_key, next(self.vla.parameters()).device
        self.dtype = next(self.vla.parameters()).dtype
        self.events_path, self.job_id = Path(events_path), str(job_id)
        self.context = {}
        self.ram_records, self.memory = ram_records, OrderedDict()
        self.episode_memory, self.shard_indexes, self._black = OrderedDict(), {}, None
        self._representation = None
        self.cache_identity = {"cache_version": FORMAL_CACHE_VERSION, **cache_identity}
        self.cache = BoundedRecordCache(cache_root, identity=self.cache_identity,
                                        max_bytes=max_cache_bytes, event=self._event)

    def _event(self, name, **kwargs):
        append_event(self.events_path, {"event": name, "job_id": self.job_id,
            "time_unix_ns": time.time_ns(), "cache_identity_sha256": json_signature(self.cache_identity),
            **self.context, **kwargs})

    def set_context(self, **context):
        self.context = context

    def _index_shard(self, shard):
        from cti_vla.data.tfrecord import _masked_crc32c
        path = (self.data_directory / shard).resolve()
        if self.data_directory not in path.parents:
            raise ValueError("registered shard escapes the dataset directory")
        if shard not in self.manifest["source_files"]:
            raise ValueError("window references an unregistered shard")
        stat = path.stat()
        registered = self.manifest["source_files"][shard]
        if {"bytes": stat.st_size, "sha256": file_sha256(path)} != {k: registered[k] for k in ("bytes", "sha256")}:
            raise ValueError("RLDS source differs from the registered source SHA")
        offsets = []
        with path.open("rb") as handle:
            while True:
                header = handle.read(12)
                if not header:
                    break
                if len(header) != 12 or _masked_crc32c(header[:8]) != struct.unpack("<I", header[8:])[0]:
                    raise ValueError("invalid TFRecord index header")
                length = struct.unpack("<Q", header[:8])[0]
                if not 0 < length <= 512 * 1024**2 or handle.tell() + length + 4 > stat.st_size:
                    raise ValueError("invalid TFRecord indexed record length")
                offsets.append((handle.tell(), length))
                handle.seek(length + 4, os.SEEK_CUR)
            if handle.tell() != stat.st_size or not offsets:
                raise ValueError("invalid TFRecord framing")
        # Whole-file SHA has verified payload/trailer bytes against the frozen
        # registration. Indexing does not decode any held-out episode.
        self.shard_indexes[shard] = (path, stat.st_size, stat.st_mtime_ns, offsets)
        self._event("shard_index_verified", shard=shard, sha256=registered["sha256"], records=len(offsets))

    def get_episode(self, row):
        from cti_vla.data.sequence_example import decode_libero_example
        if row.get("window_id") not in self.rows or self.rows[row["window_id"]] != row or row["split"] not in ("train", "validation"):
            raise ValueError("only registered train/validation episodes may be decoded")
        key = (row["source_shard"], row["record_index"])
        if key in self.episode_memory:
            self.episode_memory.move_to_end(key)
            return self.episode_memory[key]
        shard, index = key
        if shard not in self.shard_indexes:
            self._index_shard(shard)
        path, size, mtime, offsets = self.shard_indexes[shard]
        stat = path.stat()
        if (stat.st_size, stat.st_mtime_ns) != (size, mtime):
            raise ValueError("RLDS source changed after SHA verification")
        if type(index) is not int or not 0 <= index < len(offsets):
            raise ValueError("registered record index out of range")
        offset, length = offsets[index]
        with path.open("rb") as handle:
            handle.seek(offset)
            payload = handle.read(length)
        if len(payload) != length:
            raise ValueError("truncated registered episode")
        episode = replace(decode_libero_example(payload), source_shard=shard, record_index=index)
        self.episode_memory[key] = episode
        while len(self.episode_memory) > 1:
            self.episode_memory.popitem(last=False)
        return episode

    def _black_record(self, episode, row):
        from cti_vla.evaluation.libero_runtime import _prepare_processed_inputs, process_camera
        if self._black is None:
            def build():
                started = time.perf_counter()
                self._event("shared_black_generate_start")
                rng = capture_rng()
                try:
                    with torch.inference_mode(False), torch.no_grad():
                        black_image = process_camera(np.zeros((256, 256, 3), dtype=np.uint8), already_rotated=True)
                        inputs = _prepare_processed_inputs([black_image, black_image], episode.proprio[row["start_step"]],
                            episode.instructions[row["start_step"]], self.processor,
                            self.vla.norm_stats[self.stats_key]["proprio"], device=self.device, dtype=self.dtype)
                        black = self.vla.vision_backbone(inputs["pixel_values"]).detach().cpu()
                    if self.device.type == "cuda":
                        torch.cuda.synchronize(self.device)
                    self._event("shared_black_generate_end", seconds=time.perf_counter() - started, vision_forwards=1)
                    return {"black_tokens": black}
                finally:
                    restore_rng(rng)
            self._black = self.cache.get_or_create("shared:black-image", build, pinned=True)["black_tokens"]
        return self._black

    def _build(self, row):
        from cti_vla.data.formal_windows import normalize_demo_actions, validate_formal_window
        from cti_vla.evaluation.libero_runtime import prepare_rlds_eval_inputs
        from cti_vla.training.future_auxiliary import FrozenFutureRepresentation
        episode = self.get_episode(row)
        validate_formal_window(row, episode, self.protocol)
        started = time.perf_counter()
        self._event("feature_generate_start", window_id=row["window_id"], split=row["split"])
        rng = capture_rng()
        def sync():
            if self.device.type == "cuda":
                torch.cuda.synchronize(self.device)
        try:
            with torch.inference_mode(False), torch.no_grad():
                sync()
                current_started = time.perf_counter()
                inputs = prepare_rlds_eval_inputs(episode, row["start_step"], self.processor,
                    self.vla.norm_stats[self.stats_key]["proprio"], device=self.device, dtype=self.dtype)
                raw = self.vla.vision_backbone(inputs["pixel_values"]).detach()
                visual = self.vla.projector(raw).detach()
                language = self.vla.get_input_embeddings()(inputs["input_ids"]).detach()
                sync()
                current_seconds = time.perf_counter() - current_started
                teacher_started = time.perf_counter()
                teacher = self.policy.forward_from_full_tokens(visual, inputs["normalized_proprio"],
                    input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"])
                sync()
                teacher_seconds = time.perf_counter() - teacher_started
                future_started = time.perf_counter()
                future = prepare_rlds_eval_inputs(episode, row["future_step"], self.processor,
                    self.vla.norm_stats[self.stats_key]["proprio"], device=self.device, dtype=self.dtype)
                future_visual = self.vla._process_vision_features(future["pixel_values"], None, False)
                if self._representation is None:
                    self._representation = FrozenFutureRepresentation(visual.shape[-1]).to(self.device)
                target = self._representation.target(future_visual)
                sync()
                future_seconds = time.perf_counter() - future_started
                diagnostic_started = time.perf_counter()
                current_summary = self._representation.target(visual)
                difference = (np.asarray(episode.proprio[row["future_step"]], dtype=np.float64)
                              - np.asarray(episode.proprio[row["start_step"]], dtype=np.float64))
                diagnostics = {"horizon_control_actions": 8,
                    "raw_proprio_l2_change": float(np.linalg.norm(difference)),
                    "translation_l2_change": float(np.linalg.norm(difference[:3])),
                    "axis_angle_vector_l2_change": float(np.linalg.norm(difference[3:6])),
                    "gripper_l2_change": float(np.linalg.norm(difference[6:])),
                    "normalized_proprio_l2_change": float((future["normalized_proprio"].float() - inputs["normalized_proprio"].float()).norm()),
                    "visual_summary_mse_change": float((target - current_summary).square().mean()),
                    "future_is_last": bool(row["future_is_last"]), "future_is_terminal": bool(row["future_is_terminal"])}
                sync()
                diagnostic_seconds = time.perf_counter() - diagnostic_started
                demonstration = normalize_demo_actions(episode.actions[row["action_start"]:row["action_stop_exclusive"]],
                    self.vla.norm_stats[self.stats_key]["action"])
                record = {"raw_tokens": raw, "visual": visual, "language": language,
                    "teacher_actions": teacher.float(), "demonstration_actions": torch.as_tensor(demonstration)[None],
                    "future_target": target, **{k: inputs[k] for k in ("input_ids", "attention_mask", "normalized_proprio")}}
                record = {k: v.detach().cpu().clone() for k, v in record.items()}
                record["future_window_diagnostics"] = diagnostics
            sync()
            self._event("feature_generate_end", window_id=row["window_id"], seconds=time.perf_counter() - started,
                        teacher_forwards=1, vision_forwards=2, current_vision_forwards=1, future_vision_forwards=1,
                        current_preprocess_vision_projection_seconds=current_seconds, teacher_forward_seconds=teacher_seconds,
                        future_preprocess_vision_target_seconds=future_seconds, window_diagnostic_seconds=diagnostic_seconds,
                        future_target_required_by_current_arm=(self.context.get("arm") == "B" if "arm" in self.context else None),
                        producer_scope="shared A/B record; A does not require future-target generation",
                        future_target_detached=True, checkpoint_normalization=True, window_alignment_validated=True)
            return record
        finally:
            restore_rng(rng)

    def get(self, window_id: str) -> dict:
        if window_id not in self.rows:
            raise ValueError("window is not in the registered train/validation pool")
        row = self.rows[window_id]
        if row["split"] not in ("train", "validation"):
            raise ValueError("test is sealed")
        if window_id in self.memory:
            self.memory.move_to_end(window_id)
            self._event("ram_cache_hit", window_id=window_id)
            return self.memory[window_id]
        # Generate shared black outside the window-key lock, avoiding lock
        # stripe recursion if the two different keys share a stripe.
        if self._black is None:
            episode = self.get_episode(row)
            self._black_record(episode, row)
        record = self.cache.get_or_create("window:" + window_id, lambda: self._build(row))
        record = {**record, "black_tokens": self._black}
        if self.ram_records:
            self.memory[window_id] = record
            while len(self.memory) > self.ram_records:
                self.memory.popitem(last=False)
        return record

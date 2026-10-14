"""Bounded Long input acceptance contracts; never substitutes for a G0 gate."""
from __future__ import annotations

import math
import json
from pathlib import Path

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation import libero_runtime
from cti_vla.evaluation.teacher_diagnostics import json_signature
from cti_vla.models.abstraction.packing import PACKING_VERSION

LONG_SUITE = "libero_10"
LONG_STATS_KEY = "libero_10_no_noops"
INPUT_ACCEPTANCE_VERSION = "g1f-long-three-registered-train-inputs-v1"
INPUT_TASK_IDS = (0, 3, 5)


def select_input_windows(manifest, protocol):
    """Choose metadata only: one earliest registered window per fixed task."""
    if manifest.get("suite") != LONG_SUITE or protocol.payload.get("suite") != LONG_SUITE:
        raise ValueError("Long acceptance requires its own manifest and protocol")
    catalog = {r["task_id"]: r for r in protocol.payload["task_catalog"]}
    rows = []
    for task in INPUT_TASK_IDS:
        candidates = [r for r in manifest["windows"] if r["split"] == "train"
                      and r["task_name"] == catalog[task]["instruction"]]
        if not candidates:
            raise ValueError(f"registered Long train windows lack task{task}")
        rows.append(min(candidates, key=lambda r: (r["episode_id"], r["start_step"], r["window_id"])))
    if len({r["window_id"] for r in rows}) != 3:
        raise ValueError("input acceptance windows must be distinct")
    return rows


def require_long_input_acceptance(report, *, config, window_manifest_sha256,
        protocol_sha256, asset_manifest_sha256, source_files, verification_script_sha256,
        selected_windows):
    """Require finalized, exact implementation/config/data evidence before F01."""
    expected = {"stage": "G1-F00-input-parity", "status": "passed",
        "execution": "real_frozen_openvla_l40", "version": INPUT_ACCEPTANCE_VERSION,
        "suite": LONG_SUITE, "stats_key": LONG_STATS_KEY,
        "model_revision": config["model_revision"], "config_sha256": json_signature(config),
        "window_manifest_sha256": window_manifest_sha256, "protocol_sha256": protocol_sha256,
        "asset_manifest_sha256": asset_manifest_sha256, "source_files": source_files,
        "verification_script_sha256": verification_script_sha256,
        "input_version": libero_runtime.INPUTS_VERSION, "action_version": libero_runtime.ACTION_VERSION,
        "packing_version": PACKING_VERSION, "checkpoint_unchanged": True,
        "test_opened": False, "policy_sample_forwards": 6, "vision_forwards": 6, "policy_attempts": 6}
    if any(report.get(key) != value for key, value in expected.items()):
        raise ValueError("Long official input acceptance identity/finalization mismatch")
    rows = report.get("observations", [])
    if len(rows) != 3 or [r.get("window") for r in rows] != selected_windows:
        raise ValueError("Long input acceptance changed its fixed train observations")
    flags = ("pixels_equal", "prompt_equal", "raw_camera_bridge_equal", "native_physical_equal",
             "action_postprocess_equal", "gripper_equal", "demonstration_normalization_valid", "passed")
    for row in rows:
        if any(row.get(k) is not True for k in flags):
            raise ValueError("Long input/action parity did not pass")
        for key, limit in (("proprio_max_abs_error", 1e-6), ("dense_max_abs_error", .002)):
            value = row.get(key)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= limit:
                raise ValueError("Long official parity error is missing/nonfinite/above tolerance")


def verify_input_acceptance_journal(path, report):
    """Bind successful receipt to the complete durable six-call evidence."""
    path = Path(path)
    if file_sha256(path) != report.get("calls_jsonl_sha256"):
        raise ValueError("Long input acceptance journal SHA mismatch")
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    active, done = {}, []
    keys = ("call_id", "window_id", "kind", "job_id")
    for event in events:
        call_id = event["call_id"]
        if event.get("event") == "start" and call_id == len(done) and not active:
            active[call_id] = event
        elif event.get("event") == "complete" and call_id in active and all(event.get(k) == active[call_id].get(k) for k in keys):
            done.append(active.pop(call_id))
        else:
            raise ValueError("Long input acceptance requires six clean completed call pairs")
    expected = {(r["window"]["window_id"], kind) for r in report["observations"]
                for kind in ("official_dense", "shared_dense")}
    if active or len(done) != 6 or {(r["window_id"], r["kind"]) for r in done} != expected or any(r["job_id"] != report["job_id"] for r in done):
        raise ValueError("Long input acceptance query coverage mismatch")


__all__ = ["LONG_SUITE", "LONG_STATS_KEY", "INPUT_ACCEPTANCE_VERSION", "INPUT_TASK_IDS",
           "select_input_windows", "require_long_input_acceptance", "verify_input_acceptance_journal"]

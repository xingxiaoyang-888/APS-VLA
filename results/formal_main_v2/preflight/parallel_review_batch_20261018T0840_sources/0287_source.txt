"""Reuse only the byte-pinned seed17 Long dense development reference.

This is evidence reuse, never a new trial or a new cost-bearing inference.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from types import SimpleNamespace

from cti_vla.data.identity import file_sha256
from cti_vla.data.long_initial_states import validate_long_development_panel
from cti_vla.evaluation.teacher_diagnostics import json_signature

VERSION = "g1f-long-seed17-dense-reference-v1"
SOURCE_FILES = {
    "config.json": "1d9fb2c974105656f3a9909b13ac4dff1aed347f680b108df5793582195f17ea",
    "panel.json": "64ce305a9530dca00879fdc00a4d08552d95c1ebf3db981533873d3b0d14886e",
    "closed_loop_report.json": "b54ea4fa2755317e9a71b1d566694e2ddcc0bb2267087ab16d5e34eb6ba85611",
    "trials.jsonl": "ff68b045e16c7e96ee2205471112e68c8596526b32ebef753db653a46e0bcad0",
}
REFERENCE_SIGNATURE = "9af54766a03d820ee2d2969a4f346e7032b40545123678fd3b46ec7f39cb94ef"


def dense_identity(config):
    """Compare policy/environment semantics, excluding selector and GPU allocation."""
    fields = ("suite", "panel_signature", "base_model_revision", "input_version", "action_version",
        "packing_version", "stats_key", "environment_seed", "runtime_seed", "max_steps", "wait_steps",
        "action_chunk", "policy_watchdog_seconds", "source_verification")
    value = {k: config[k] for k in fields}
    if value["suite"] != "libero_10" or (value["environment_seed"], value["runtime_seed"], value["max_steps"],
            value["wait_steps"], value["action_chunk"]) != (0, 17, 520, 10, 8):
        raise ValueError("dense reuse requires registered Long evaluation seeds/horizon/chunk")
    manifests = [digest for path, digest in config["watched_artifacts"].items()
                 if path.replace("\\", "/").endswith("/configs/assets/openvla_oft_libero_long.json")]
    if len(manifests) != 1:
        raise ValueError("dense reuse requires one immutable Long model asset manifest")
    value["asset_manifest_sha256"] = manifests[0]
    value["policy_source_hashes"] = {k: v for k, v in config["source_hashes"].items()
        if k.startswith("src/cti_vla/models/") or k in
        ("src/cti_vla/evaluation/libero_runtime.py", "scripts/eval_libero.py")}
    if not value["policy_source_hashes"] or "src/cti_vla/evaluation/libero_runtime.py" not in value["policy_source_hashes"]:
        raise ValueError("dense reuse lacks preprocessing/policy source identities")
    runtime = config["runtime"]
    value["runtime_semantics"] = {k: runtime[k] for k in ("attention", "dtype", "mujoco_gl", "python", "packages", "cuda", "gpu")}
    return value


def validate_dense_reference(receipt, panel):
    validate_long_development_panel(panel)
    unsigned = {k: v for k, v in receipt.items() if k != "signature"}
    if (receipt.get("version") != VERSION or receipt.get("source_files") != SOURCE_FILES
            or receipt.get("signature") != json_signature(unsigned)
            or (REFERENCE_SIGNATURE is not None and receipt["signature"] != REFERENCE_SIGNATURE)
            or receipt.get("panel_signature") != panel["panel_signature"]):
        raise ValueError("dense reference differs from immutable seed17 evidence")
    expected = {s["trial_id"]: s for s in panel["states"]}
    rows = receipt.get("dense_results", [])
    if len(rows) != 30 or {r["state_trial_id"] for r in rows} != set(expected):
        raise ValueError("dense reference lacks the30 exact paired states")
    for r in rows:
        s = expected[r["state_trial_id"]]
        if (any(r[k] != s[k] for k in ("task_id", "task_name", "initial_state_sha256", "source_state_index"))
                or type(r["success"]) is not bool or r["status"] != "completed"):
            raise ValueError("dense reference state/outcome identity mismatch")


def require_dense_compatibility(receipt, panel, config):
    validate_dense_reference(receipt, panel)
    if receipt["identity"] != dense_identity(config):
        raise ValueError("dense reference model/environment/input/packing/panel/horizon identity differs")


def load_dense_reference(directory, panel):
    directory = Path(directory)
    for name, expected in SOURCE_FILES.items():
        if file_sha256(directory / name) != expected:
            raise ValueError("dense reference requires exact original seed17 files: " + name)
    config, saved_panel, report = [json.loads((directory / name).read_text(encoding="utf-8"))
        for name in ("config.json", "panel.json", "closed_loop_report.json")]
    if saved_panel != panel or config["methods"] != ["dense", "future_A", "future_B"] or any(
            config["selectors"][arm]["seed"] != 17 for arm in ("A", "B")):
        raise ValueError("dense reference must be the original seed17 three-arm run")
    events = [json.loads(line) for line in (directory / "trials.jsonl").read_text(encoding="utf-8").splitlines()]
    if Counter(e["event"] for e in events) != {"invocation": 1, "start": 90, "result": 90} or any(
            e["run_signature"] != json_signature(config) for e in events):
        raise ValueError("dense reference journal coverage/identity mismatch")
    completed = {}
    active = set()
    for e in events:
        if e["event"] == "start":
            if e["trial_id"] in active or e["trial_id"] in completed:
                raise ValueError("duplicate reference attempt")
            active.add(e["trial_id"])
        elif e["event"] == "result":
            if e["trial_id"] not in active or e["status"] != "completed":
                raise ValueError("reference trial is orphaned or has interface errors")
            active.remove(e["trial_id"])
            completed[e["trial_id"]] = e
    if active or report["checkpoint_unchanged"] is not True or report["test_opened"] is not False:
        raise ValueError("dense reference is not finalized")
    from cti_vla.evaluation.future_trials import summarize_future_trials
    rebuilt = summarize_future_trials(panel, config["methods"],
        SimpleNamespace(events=events, completed=lambda: completed, path=directory / "trials.jsonl"),
        provenance=report["provenance"], checkpoint_unchanged=True)
    if any(report[k] != rebuilt[k] for k in ("status", "methods", "cost", "completed_trials", "paired_AB")):
        raise ValueError("reference summary differs from raw trials")
    rows = []
    for s in panel["states"]:
        r = completed[s["trial_id"] + ":dense"]
        rows.append({**{k: r[k] for k in ("state_trial_id", "task_id", "task_name", "initial_state_sha256",
            "source_state_index", "status", "success", "termination", "control_steps", "policy_calls")},
            "initial_observation_sha256": r["chunks"][0]["observation_sha256"]})
    receipt = {"version": VERSION, "source_files": SOURCE_FILES, "panel_signature": panel["panel_signature"],
        "identity": dense_identity(config), "dense_results": rows, "new_inferences": 0, "new_gpu_seconds": 0}
    receipt["signature"] = json_signature(receipt)
    validate_dense_reference(receipt, panel)
    return receipt

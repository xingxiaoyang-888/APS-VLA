"""G0 development-only paired LIBERO rollouts; engineering timings, no benchmark.

Run on one allocated GPU. The output directory is a single-writer append-only
trial ledger. Repeating exactly the same command resumes incomplete trials;
completed successes and policy failures are never rerun to select a better run.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import random
import subprocess


ROOT = Path(__file__).resolve().parents[1]
LIBERO_COMMIT = "8f1084e3132a39270c3a13ebe37270a43ece2a01"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def signature(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def write_json(path, payload):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def git_revision(path):
    try:
        result = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], check=False, capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    except OSError:
        return None


def verify_source_checkout(path, expected):
    """Accept pinned Git checkout or root-verified git-archive inventory."""
    actual = git_revision(path)
    if actual == expected:
        dirty = subprocess.run(["git", "-C", str(path), "diff", "--quiet", "HEAD", "--"], check=False)
        if dirty.returncode != 0:
            raise ValueError(f"pinned source checkout has modified tracked files: {path}")
        return {"revision": expected, "verification": "git_head"}
    marker_path, inventory_path = path / "SOURCE_REVISION.json", path / "SOURCE_FILES.json"
    if not marker_path.is_file() or not inventory_path.is_file():
        raise ValueError(f"source checkout revision mismatch: {path}: {actual} != {expected}")
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    if marker["revision"] != expected or inventory["revision"] != expected or marker["archive_sha256"] != inventory["archive_sha256"]:
        raise ValueError("source archive revision/inventory mismatch")
    if not inventory["files"]:
        raise ValueError("empty source archive inventory")
    for relative, checksum in inventory["files"].items():
        source = (path / relative).resolve()
        if path.resolve() not in source.parents or not source.is_file() or sha256(source) != checksum:
            raise ValueError(f"source archive file verification failed: {relative}")
    return {"revision": expected, "verification": "archive_all_files_sha256", "archive_sha256": marker["archive_sha256"],
            "inventory_sha256": sha256(inventory_path), "file_count": len(inventory["files"])}


def configure_cache(path, checkpoint):
    path, checkpoint = path.resolve(), checkpoint.resolve()
    if path == checkpoint or checkpoint in path.parents:
        raise ValueError("cache must be outside immutable checkpoint")
    for directory in (path, path / "hub", path / "modules"):
        directory.mkdir(parents=True, exist_ok=True)
    os.environ.update(HF_HOME=str(path), HF_HUB_CACHE=str(path / "hub"), HF_MODULES_CACHE=str(path / "modules"),
                      HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")


def load_development_panel(path, test_path):
    from cti_vla.data.initial_states import validate_initial_state_manifest
    payload = json.loads(path.read_text(encoding="utf-8"))
    heldout = json.loads(test_path.read_text(encoding="utf-8"))
    for item in (payload, heldout):
        validate_initial_state_manifest(item)
    if payload["split"] != "development" or heldout["split"] != "test":
        raise ValueError("G0 must use a development panel and a separate final-test manifest")
    if payload["suite"] != heldout["suite"] or payload["suite"] != "libero_spatial":
        raise ValueError("G0 is scoped to the paired LIBERO Spatial protocol")
    if payload["source"] != heldout["source"]:
        raise ValueError("initial state manifests use different source/protocol definitions")
    development_hashes = {row["initial_state_sha256"] for row in payload["states"]}
    test_hashes = {row["initial_state_sha256"] for row in heldout["states"]}
    if development_hashes & test_hashes:
        raise ValueError("development/final initial state overlap")
    counts = Counter(row["task_id"] for row in payload["states"])
    if len(counts) != 3 or set(counts.values()) != {5}:
        raise ValueError("G0 requires the frozen 3 tasks x 5 states development panel")
    return payload, {"passed": True, "development_manifest_sha256": sha256(path),
                     "test_manifest_sha256": sha256(test_path), "overlap": 0,
                     "test_used_only_for_split_disjointness": True}


def environment_provenance(torch, device):
    versions = {}
    for name in ("numpy", "torch", "transformers", "tensorflow-cpu", "mujoco", "robosuite", "gym", "timm"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    properties = torch.cuda.get_device_properties(device)
    return {"python": platform.python_version(), "packages": versions, "cuda": torch.version.cuda,
            "gpu": properties.name, "gpu_memory_bytes": properties.total_memory,
            "cpu": platform.processor(), "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
            "mujoco_gl": os.environ.get("MUJOCO_GL"), "dtype": "bfloat16", "attention": "sdpa"}


def summarize(ledger, panel, provenance, split_check, checkpoint_unchanged):
    from cti_vla.evaluation.libero_runtime import METHODS, compare_dense_trials
    results = ledger.completed()
    pairs = []
    for state in panel["states"]:
        keys = [f"{state['trial_id']}:{method}" for method in ("official_dense", "dense")]
        if all(key in results for key in keys):
            pairs.append({"state_trial_id": state["trial_id"], **compare_dense_trials(*(results[key] for key in keys))})
    counts = Counter(row["task_id"] for row in panel["states"])
    expected = len(panel["states"]) * len(METHODS)
    all_completed = len(results) == expected and all(row["status"] == "completed" for row in results.values())
    parity = len(pairs) == len(panel["states"]) and all(row["passed"] for row in pairs)
    by_method = {}
    for method in METHODS:
        rows = [row for row in results.values() if row["method"] == method]
        by_method[method] = {"trials": len(rows), "successes": sum(row["success"] for row in rows),
                             "policy_failures": sum(row["status"] == "policy_error" for row in rows),
                             "policy_calls": sum(row["policy_calls"] for row in rows)}
    completed = all_completed and parity and checkpoint_unchanged
    return {"status": "passed" if completed else "incomplete_or_failed", "stage": "g0_closed_loop",
            "closed_loop": {"passed": completed, "num_tasks": len(counts), "episodes_per_task": min(counts.values()),
                            "expected_trials": expected, "completed_trials": len(results), "methods": by_method},
            "dense_parity": {"passed": parity, "atol": 0.002, "pairs": pairs},
            "initial_state_split": split_check, "checkpoint_unchanged": checkpoint_unchanged,
            "trials_jsonl_sha256": sha256(ledger.path) if ledger.path.exists() else None,
            "provenance": provenance, "num_tasks": len(counts), "episodes_per_task": min(counts.values()),
            "limitations": "Development engineering gate only. Success counts are not final test results; per-call timings include correctness checks and are not latency benchmarks. The separate 90-observation G0 parity report is still required."}


def run(args):
    from cti_vla.data.initial_states import official_task_catalog
    from cti_vla.evaluation.libero_runtime import (ACTION_VERSION, INPUTS_VERSION, METHODS, OFT_COMMIT,
        OpenVLARolloutPolicy, TrialLedger, load_official_reference_functions, run_episode)
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    panel, split_check = load_development_panel(args.initial_states, args.test_initial_states)
    config_file = args.libero_config / "config.yaml"
    if not config_file.is_file():
        raise ValueError(f"pre-create project LIBERO config to avoid upstream interactive home writes: {config_file}")
    os.environ["LIBERO_CONFIG_PATH"] = str(args.libero_config.resolve())
    # Source hashes are also checked by the isolated reference-function loader.
    source_verification = {}
    for name, directory, expected in (("openvla_oft", args.official_source, OFT_COMMIT), ("libero", args.libero_source, LIBERO_COMMIT)):
        source_verification[name] = verify_source_checkout(directory, expected)
    catalog, mapping = official_task_catalog(args.libero_source)
    if panel["source"]["revision"] != LIBERO_COMMIT:
        raise ValueError("state manifest LIBERO revision mismatch")
    for key, value in mapping.items():
        if panel["source"][key] != value:
            raise ValueError(f"state manifest/source mapping mismatch: {key}")
    configure_cache(args.cache_directory, args.checkpoint)
    reference = load_official_reference_functions(args.official_source)
    import numpy as np
    import torch
    from transformers import AutoProcessor
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.models.openvla_oft_runtime_compat import TRANSFORMERS_OFT_COMMIT, OFT_SDPA_FORWARD_SHA256
    if torch.cuda.device_count() != 1:
        raise RuntimeError("expose exactly one allocated GPU via the scheduler")
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    manifest = load_checkpoint_manifest(args.manifest)
    print("Verifying immutable checkpoint before model load", flush=True)
    before = verify_checkpoint_directory(args.checkpoint, manifest)
    components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
    processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
    keys = [key for key in components.vla.norm_stats if "libero_spatial" in key]
    stats_key = args.stats_key or (keys[0] if len(keys) == 1 else None)
    if stats_key not in components.vla.norm_stats:
        raise ValueError("supply valid LIBERO Spatial --stats-key")
    # Import the installed pinned checkout only after the project config exists.
    from libero.libero import benchmark, get_libero_path
    from libero.libero.envs import OffScreenRenderEnv
    import libero.libero as installed_libero
    installed_path = Path(installed_libero.__file__).resolve()
    if args.libero_source.resolve() not in installed_path.parents:
        raise ValueError("LIBERO import must resolve inside the pinned --libero-source checkout")
    suite = benchmark.get_benchmark_dict()[panel["suite"]](task_order_index=0)
    for state in panel["states"]:
        if suite.get_task(state["task_id"]).name != state["task_name"] or catalog[state["task_id"]]["task_name"] != state["task_name"]:
            raise ValueError("runtime task ID/name differs from the frozen initial-state manifest")
    runtime = environment_provenance(torch, device)
    # Hardware/software are part of the resume signature; Slurm job ID is not.
    frozen_runtime = {key: value for key, value in runtime.items() if key != "slurm_job_id"}
    from cti_vla.evaluation import libero_runtime
    config = {"schema_version": 1, "stage": "g0_closed_loop", "model_revision": manifest.revision,
              "manifest_sha256": sha256(args.manifest), "panel_signature": panel["content_signature"],
              "split_check": split_check, "methods": list(METHODS), "seed": args.seed,
              "environment_seed": panel["environment_seed"], "wait_steps": 10, "max_steps": 220,
              "policy_watchdog_seconds": args.policy_watchdog_seconds, "stats_key": stats_key,
              "input_version": INPUTS_VERSION, "action_version": ACTION_VERSION, "packing_version": PACKING_VERSION,
              "official_commit": OFT_COMMIT, "libero_commit": LIBERO_COMMIT,
              "source_verification": source_verification,
              "transformers_commit": TRANSFORMERS_OFT_COMMIT, "sdpa_forward_sha256": OFT_SDPA_FORWARD_SHA256,
              "script_sha256": sha256(__file__), "runtime_sha256": sha256(libero_runtime.__file__),
              "runtime": frozen_runtime}
    run_signature = signature(config)
    args.output_directory.mkdir(parents=True, exist_ok=True)
    ledger = TrialLedger(args.output_directory / "trials.jsonl", run_signature=run_signature)
    provenance = {**config, "run_signature": run_signature, "code_commit": git_revision(ROOT),
                  "checkpoint": asdict(before), "runtime": runtime, "created_utc": datetime.now(timezone.utc).isoformat()}
    old_config = args.output_directory / "config.json"
    if old_config.exists() and json.loads(old_config.read_text(encoding="utf-8")) != config:
        raise ValueError("output directory configuration changed; use a new directory")
    if not old_config.exists():
        write_json(old_config, config)
        write_json(args.output_directory / "provenance.json", provenance)
    ledger.append({"event": "invocation", "slurm_job_id": runtime["slurm_job_id"],
                   "created_utc": provenance["created_utc"], "recovered_tail": ledger.recovered_tail})
    policies = {method: OpenVLARolloutPolicy(components, processor, stats_key=stats_key, method=method, reference=reference) for method in METHODS}
    ran = 0
    for state in panel["states"]:
        for method in METHODS:
            trial_id = f"{state['trial_id']}:{method}"
            if trial_id in ledger.completed():
                continue
            if args.stop_after is not None and ran >= args.stop_after:
                break
            identity = {"trial_id": trial_id, "state_trial_id": state["trial_id"], "task_id": state["task_id"],
                        "task_name": state["task_name"], "initial_state_sha256": state["initial_state_sha256"],
                        "source_state_index": state["source_state_index"], "method": method, "split": "development",
                        "environment_seed": panel["environment_seed"], "slurm_job_id": runtime["slurm_job_id"]}
            ledger.append({**identity, "event": "start", "created_utc": datetime.now(timezone.utc).isoformat()})
            print(f"Starting {trial_id}", flush=True)
            env = None
            try:
                # Reset all RNGs as well as env.seed for independent paired runs.
                random.seed(args.seed)
                np.random.seed(args.seed)
                torch.manual_seed(args.seed)
                task = suite.get_task(state["task_id"])
                env = OffScreenRenderEnv(bddl_file_name=str(Path(get_libero_path("bddl_files")) / task.problem_folder / task.bddl_file),
                                         camera_heights=256, camera_widths=256)
                env.seed(panel["environment_seed"])
                result = run_episode(env, policies[method], task.language, state["initial_state"],
                                     policy_watchdog_seconds=args.policy_watchdog_seconds)
            except Exception as exc:
                result = {"status": "infrastructure_error", "success": False, "termination": type(exc).__name__,
                          "error": str(exc), "error_phase": "environment_creation", "chunks": [],
                          "executed_actions": [], "policy_calls": 0, "control_steps": 0, "wait_steps": 0}
            finally:
                if env is not None:
                    try:
                        env.close()
                    except Exception as exc:
                        ledger.append({**identity, "event": "cleanup_error", "error": str(exc)})
            ledger.append({**identity, **result, "event": "result", "created_utc": datetime.now(timezone.utc).isoformat()})
            ran += 1
            print(json.dumps({"trial_id": trial_id, "status": result["status"], "success": result["success"], "control_steps": result["control_steps"]}), flush=True)
            write_json(args.output_directory / "closed_loop_report.json", summarize(ledger, panel, provenance, split_check, False))
            if result["status"] == "infrastructure_error":
                raise RuntimeError("infrastructure failure recorded; fix then resume the same trial ID")
        if args.stop_after is not None and ran >= args.stop_after:
            break
    print("Verifying immutable checkpoint after evaluation", flush=True)
    after = verify_checkpoint_directory(args.checkpoint, manifest)
    if before != after:
        raise RuntimeError("checkpoint changed during evaluation")
    report = summarize(ledger, panel, provenance, split_check, True)
    write_json(args.output_directory / "closed_loop_report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--initial-states", type=Path, default=ROOT / "configs/manifests/spatial_initial_states_v1/g0_development_15.json")
    parser.add_argument("--test-initial-states", type=Path, default=ROOT / "configs/manifests/spatial_initial_states_v1/init_states_test.json")
    parser.add_argument("--official-source", type=Path, default=ROOT / "external/openvla-oft")
    parser.add_argument("--libero-source", type=Path, default=ROOT / "external/LIBERO")
    parser.add_argument("--libero-config", type=Path, default=ROOT / "configs/libero_runtime")
    parser.add_argument("--cache-directory", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--stats-key")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--policy-watchdog-seconds", type=float, default=60.0)
    parser.add_argument("--stop-after", type=int, help="Stop after this many new trials for staged engineering runs; does not pass the full gate")
    args = parser.parse_args()
    if args.policy_watchdog_seconds != 60.0 or (args.stop_after is not None and args.stop_after <= 0):
        parser.error("G0 watchdog is fixed to 60 seconds and stop-after must be positive")
    checkpoint, output = args.checkpoint.resolve(), args.output_directory.resolve()
    if output == checkpoint or checkpoint in output.parents:
        parser.error("output must be outside the immutable checkpoint")
    args.output_directory.mkdir(parents=True, exist_ok=True)
    try:
        report = run(args)
    except Exception as exc:
        write_json(args.output_directory / "invocation_failure.json", {"status": "failed", "error": str(exc), "created_utc": datetime.now(timezone.utc).isoformat()})
        raise
    print(json.dumps({"status": report["status"], "report": str(args.output_directory / "closed_loop_report.json")}), flush=True)
    if report["status"] != "passed" and args.stop_after is None:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

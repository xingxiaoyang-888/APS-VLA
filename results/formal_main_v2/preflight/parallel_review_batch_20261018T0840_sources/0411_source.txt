"""Collect three predeclared dense development trajectories, never test data.

The raw server-only NPZ panel uses actual control steps0/80/160. Early success
leaves explicit missing entries. This is collection cost, not latency timing.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import random
import time

ROOT = Path(__file__).resolve().parents[1]


def run(args):
    from cti_vla.data.identity import file_sha256
    from cti_vla.evaluation import libero_runtime
    from cti_vla.evaluation.future_trials import load_future_development_panel
    from cti_vla.evaluation.future_profiling import (CaptureDense, FUTURE_PANEL_VERSION, profile_states,
        save_dense_episode, write_future_panel, load_future_raw_panel, validate_new_output_paths, load_script)
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature, require_g0
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    panel = load_future_development_panel(args.development_states, args.g0_panel)
    states = profile_states(panel)
    if args.prepare_only:
        return {"status": "prepared_only", "version": FUTURE_PANEL_VERSION, "gpu_calls": 0,
            "state_trial_ids": [s["trial_id"] for s in states], "control_steps": [0, 80, 160],
            "target_observations": 9, "test_opened": False, "missing_rule": "no final-frame substitution"}
    if os.name == "nt" or not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("real collection requires a server Slurm allocation")
    if any(v is None for v in (args.output, args.checkpoint, args.cache_directory, args.g0_report)):
        raise ValueError("collection requires new output, base checkpoint, external cache and passed G0")
    validate_new_output_paths(project_root=args.project_root, source_root=ROOT, output=args.output,
        cache=args.cache_directory, weight_roots=[args.checkpoint])
    execution_start = time.perf_counter()
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.data.initial_states import official_task_catalog
    asset = load_checkpoint_manifest(args.asset_manifest)
    g0 = json.loads(args.g0_report.read_text(encoding="utf-8"))
    require_g0(g0, model_revision=asset.revision, input_version=libero_runtime.INPUTS_VERSION, packing_version=PACKING_VERSION)
    runtime_sha = file_sha256(libero_runtime.__file__)
    if g0["provenance"].get("runtime_sha256") != runtime_sha or g0["provenance"].get("checkpoint_manifest_sha256") != file_sha256(args.asset_manifest):
        raise ValueError("collection must use the accepted G0 runtime and immutable base")
    common = load_script(ROOT, "eval_libero")
    sources = {"oft": common.verify_source_checkout(args.official_source, libero_runtime.OFT_COMMIT),
        "libero": common.verify_source_checkout(args.libero_source, common.LIBERO_COMMIT)}
    catalog, mapping = official_task_catalog(args.libero_source)
    if any(panel["source"].get(k) != v for k, v in mapping.items()):
        raise ValueError("development task mapping differs from pinned LIBERO")
    if not (args.libero_config / "config.yaml").is_file():
        raise ValueError("project LIBERO configuration must already exist")
    os.environ["LIBERO_CONFIG_PATH"] = str(args.libero_config.resolve())
    common.configure_cache(args.cache_directory, args.checkpoint)
    import numpy as np
    import torch
    from transformers import AutoProcessor
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.evaluation.profiling import hardware_telemetry
    if torch.cuda.device_count() != 1:
        raise RuntimeError("collection needs exactly one allocated visible GPU")
    torch.cuda.set_device(0)
    device = torch.device("cuda:0")
    before = verify_checkpoint_directory(args.checkpoint, asset)
    load_start = time.perf_counter()
    components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
    processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
    torch.cuda.synchronize(device)
    loading_seconds = time.perf_counter() - load_start
    policy = libero_runtime.OpenVLARolloutPolicy(components, processor, stats_key=args.stats_key, method="dense")
    from libero.libero import benchmark, get_libero_path
    from libero.libero.envs import OffScreenRenderEnv
    import libero.libero as installed_libero
    if args.libero_source.resolve() not in Path(installed_libero.__file__).resolve().parents:
        raise ValueError("installed LIBERO is outside the verified source")
    suite = benchmark.get_benchmark_dict()[panel["suite"]](task_order_index=0)
    for state in states:
        if suite.get_task(state["task_id"]).name != state["task_name"] or catalog[state["task_id"]]["task_name"] != state["task_name"]:
            raise ValueError("runtime task ID differs from the frozen development panel")
    watched = {str(p.resolve()): file_sha256(p) for p in (args.asset_manifest, args.g0_report, args.development_states, args.g0_panel)}
    identity = {"version": FUTURE_PANEL_VERSION, "panel_signature": panel["panel_signature"],
        "state_trial_ids": [s["trial_id"] for s in states], "model_revision": asset.revision,
        "input_version": libero_runtime.INPUTS_VERSION, "packing_version": PACKING_VERSION,
        "action_version": libero_runtime.ACTION_VERSION, "stats_key": args.stats_key,
        "runtime_sha256": runtime_sha, "seed": args.seed, "environment_seed": panel["environment_seed"],
        "source_verification": sources, "watched": watched, "source_files": {
            p.relative_to(ROOT).as_posix(): file_sha256(p) for p in [*sorted((ROOT / "src/cti_vla").rglob("*.py")),
                Path(__file__), ROOT / "scripts/eval_libero.py"]},
        "model_loading_seconds_excluded": loading_seconds,
        "checkpoint": asdict(before), "hardware": hardware_telemetry(), "test_opened": False}
    args.output.mkdir(parents=True, exist_ok=False)
    atomic_json(args.output / "config.json", identity)
    ledger = libero_runtime.TrialLedger(args.output / "collection_trials.jsonl", run_signature=json_signature(identity))
    began, cpu_began = time.perf_counter(), time.process_time()
    torch.cuda.reset_peak_memory_stats(device)
    completed = []
    try:
        for state in states:
            tid = state["trial_id"]
            ledger.append({"event": "start", "trial_id": tid, "method": "dense"})
            env = None
            try:
                random.seed(args.seed)
                np.random.seed(args.seed)
                torch.manual_seed(args.seed)
                task = suite.get_task(state["task_id"])
                env = OffScreenRenderEnv(bddl_file_name=str(Path(get_libero_path("bddl_files")) / task.problem_folder / task.bddl_file),
                    camera_heights=256, camera_widths=256)
                env.seed(panel["environment_seed"])
                capture = CaptureDense(policy)
                result = libero_runtime.run_episode(env, capture, task.language, state["initial_state"])
            finally:
                if env is not None:
                    env.close()
            ledger.append({"event": "result", "trial_id": tid, **result})
            if result["status"] != "completed":
                raise RuntimeError("dense collection failed; retain this attempt and rerun to a new output")
            completed.append((state, task.language, result, capture.captured))
            print(json.dumps({"state_trial_id": tid, "control_steps": result["control_steps"], "captured_steps": sorted(capture.captured)}), flush=True)
        after = verify_checkpoint_directory(args.checkpoint, asset)
        if before != after or any(file_sha256(p) != sha for p, sha in watched.items()):
            raise RuntimeError("collection source/checkpoint changed")
        provenance = {**identity, "checkpoint_unchanged": True}
        episodes = [save_dense_episode(args.output / f"task_{s['task_id']}", s, instruction, result, frames,
            provenance=provenance) for s, instruction, result, frames in completed]
        write_future_panel(args.output, panel, episodes, provenance=provenance)
        samples, loaded = load_future_raw_panel(args.output / "panel.json", development_path=args.development_states,
            g0_panel_path=args.g0_panel)
        report = {"status": "completed", "observations": len(samples), "panel": loaded,
            "wall_seconds": time.perf_counter() - began, "cpu_seconds": time.process_time() - cpu_began,
            "execution_wall_seconds_including_model_loading": time.perf_counter() - execution_start,
            "policy_calls": sum(r[2]["policy_calls"] for r in completed),
            "peak_memory_allocated_bytes": torch.cuda.max_memory_allocated(device),
            "peak_memory_reserved_bytes": torch.cuda.max_memory_reserved(device), "hardware_after": hardware_telemetry(),
            "cost_scope": "Three dense simulator trajectories including captured-array copies; not deployment latency"}
        atomic_json(args.output / "collection_report.json", report)
        return report
    except BaseException as exc:
        starts = sum(e["event"] == "start" for e in ledger.events)
        results = [e for e in ledger.events if e["event"] == "result"]
        unknown = starts - len(results)
        atomic_json(args.output / "collection_report.json", {"status": "failed", "error": f"{type(exc).__name__}: {exc}",
            "attempted_episodes": starts, "unknown_completion": unknown,
            "known_policy_calls": sum(e.get("policy_calls", 0) for e in results),
            "policy_calls_total": None if unknown else sum(e.get("policy_calls", 0) for e in results),
            "wall_seconds": time.perf_counter() - began, "cpu_seconds": time.process_time() - cpu_began,
            "execution_wall_seconds_including_model_loading": time.perf_counter() - execution_start,
            "checkpoint_unchanged": None, "test_opened": False})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    states = ROOT / "configs/manifests/spatial_initial_states_v1"
    parser.add_argument("--development-states", type=Path, default=states / "init_states_development.json")
    parser.add_argument("--g0-panel", type=Path, default=states / "g0_development_15.json")
    for key in ("checkpoint", "cache-directory", "g0-report", "output"):
        parser.add_argument("--" + key, type=Path)
    parser.add_argument("--asset-manifest", type=Path, default=ROOT / "configs/assets/openvla_oft_libero_spatial.json")
    parser.add_argument("--official-source", type=Path, default=ROOT / "external/openvla-oft")
    parser.add_argument("--libero-source", type=Path, default=ROOT / "external/LIBERO")
    parser.add_argument("--libero-config", type=Path, default=ROOT / "configs/libero_runtime")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--stats-key", default="libero_spatial_no_noops")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--prepare-only", action="store_true")
    print(json.dumps(run(parser.parse_args()), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

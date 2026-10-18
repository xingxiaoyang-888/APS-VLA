"""Collect three registered Long dense trajectories for shared raw O2A timing."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
import json
import os
from pathlib import Path
import random
import time

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run(args):
    from cti_vla.data.identity import file_sha256
    from cti_vla.data.long_initial_states import load_long_development_panel
    from cti_vla.evaluation import libero_runtime
    from cti_vla.evaluation.future_dense_reuse import load_dense_reference, require_dense_compatibility, SOURCE_FILES
    from cti_vla.evaluation.future_long_profiling import (LONG_PANEL_VERSION, CaptureLongDense,
        fixed_long_profile_states, save_long_dense_episode, write_long_raw_panel, load_long_raw_panel)
    from cti_vla.evaluation.future_profiling import load_script, validate_new_output_paths
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    registration = read(args.registration)
    panel = load_long_development_panel(args.development_panel)
    reference = load_dense_reference(args.dense_reference, panel)
    selected = fixed_long_profile_states(panel, reference, registration)
    if args.prepare_only:
        return {"status": "prepared_only", "gpu_calls": 0, "version": LONG_PANEL_VERSION,
            "states": [{k: s[k] for k in ("trial_id", "task_id", "source_state_index", "requested_control_steps",
                "reference_control_steps", "reference_initial_observation_sha256")} for s in selected],
            "target_observations": 9, "test_opened": False, "new_success_trials": False}
    if os.name == "nt" or not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Long observation collection requires a server Slurm allocation")
    if any(getattr(args, k) is None for k in ("checkpoint", "cache_directory", "output", "input_acceptance")):
        raise ValueError("collection needs immutable base/input acceptance, cache and new output")
    validate_new_output_paths(project_root=args.project_root, source_root=ROOT, output=args.output,
        cache=args.cache_directory, weight_roots=[args.checkpoint])
    execution_start = time.perf_counter()
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.data.initial_states import official_task_catalog
    asset = load_checkpoint_manifest(args.asset_manifest)
    input_report = read(args.input_acceptance)
    old_config = read(args.dense_reference / "config.json")
    if (file_sha256(args.input_acceptance) != old_config["input_acceptance_sha256"]
            or input_report.get("status") != "passed" or input_report.get("checkpoint_unchanged") is not True
            or input_report.get("model_revision") != asset.revision
            or input_report.get("asset_manifest_sha256") != file_sha256(args.asset_manifest)):
        raise ValueError("Long collection must use original accepted input/base identity")
    common = load_script(ROOT, "eval_libero")
    sources = {"openvla_oft": common.verify_source_checkout(args.official_source, libero_runtime.OFT_COMMIT),
        "libero": common.verify_source_checkout(args.libero_source, common.LIBERO_COMMIT)}
    catalog, mapping = official_task_catalog(args.libero_source, suite="libero_10")
    if any(panel["source"].get(k) != v for k, v in mapping.items()):
        raise ValueError("Long collection task mapping differs from original panel")
    if not (args.libero_config / "config.yaml").is_file():
        raise ValueError("project LIBERO config must be pre-created")
    os.environ["LIBERO_CONFIG_PATH"] = str(args.libero_config.resolve())
    common.configure_cache(args.cache_directory, args.checkpoint)
    import numpy as np
    import torch
    from transformers import AutoProcessor
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.evaluation.profiling import hardware_telemetry
    if torch.cuda.device_count() != 1 or torch.cuda.get_device_name(0) != "NVIDIA L40":
        raise RuntimeError("Long observation collection requires exactly one NVIDIA L40")
    torch.cuda.set_device(0)
    device = torch.device("cuda:0")
    actual = deepcopy(old_config)
    actual.update(base_model_revision=asset.revision, source_verification=sources,
        runtime=common.environment_provenance(torch, device), input_version=libero_runtime.INPUTS_VERSION,
        action_version=libero_runtime.ACTION_VERSION, packing_version=PACKING_VERSION,
        source_hashes={key: file_sha256(ROOT / key) for key in old_config["source_hashes"]
            if key.startswith("src/cti_vla/models/") or key in ("src/cti_vla/evaluation/libero_runtime.py", "scripts/eval_libero.py")})
    require_dense_compatibility(reference, panel, actual)
    before = verify_checkpoint_directory(args.checkpoint, asset)
    load_start = time.perf_counter()
    components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
    processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
    torch.cuda.synchronize(device)
    loading_seconds = time.perf_counter() - load_start
    policy = libero_runtime.OpenVLARolloutPolicy(components, processor,
        stats_key="libero_10_no_noops", method="dense")
    from libero.libero import benchmark, get_libero_path
    from libero.libero.envs import OffScreenRenderEnv
    import libero.libero as installed_libero
    if args.libero_source.resolve() not in Path(installed_libero.__file__).resolve().parents:
        raise ValueError("installed LIBERO is outside frozen source")
    suite = benchmark.get_benchmark_dict()["libero_10"](task_order_index=0)
    for state in selected:
        if suite.get_task(state["task_id"]).name != state["task_name"] or catalog[state["task_id"]]["task_name"] != state["task_name"]:
            raise ValueError("Long collection runtime task identity mismatch")
    watched_paths = [args.registration, args.development_panel, args.input_acceptance, args.asset_manifest,
        *[args.dense_reference / name for name in SOURCE_FILES]]
    watched = {str(p.resolve()): file_sha256(p) for p in watched_paths}
    identity = {"version": LONG_PANEL_VERSION, "panel_signature": panel["panel_signature"],
        "registration_sha256": file_sha256(args.registration), "registration_signature": json_signature(registration),
        "model_revision": asset.revision, "input_version": libero_runtime.INPUTS_VERSION,
        "action_version": libero_runtime.ACTION_VERSION, "packing_version": PACKING_VERSION,
        "stats_key": "libero_10_no_noops", "runtime_sha256": file_sha256(libero_runtime.__file__),
        "seed": 17, "environment_seed": 0, "max_steps": 520, "wait_steps": 10, "action_chunk": 8,
        "source_verification": sources, "runtime": actual["runtime"], "watched": watched,
        "checkpoint": asdict(before), "source_files": actual["source_hashes"],
        "collector_sha256": file_sha256(__file__), "dense_reference_signature": reference["signature"],
        "model_loading_seconds_excluded_from_collection": loading_seconds, "hardware": hardware_telemetry(),
        "test_opened": False, "new_success_trials": False}
    args.output.mkdir(parents=True, exist_ok=False)
    atomic_json(args.output / "config.json", identity)
    ledger = libero_runtime.TrialLedger(args.output / "collection_trials.jsonl", run_signature=json_signature(identity))
    completed = []
    began, cpu_began = time.perf_counter(), time.process_time()
    try:
        for state in selected:
            tid = state["trial_id"]
            ledger.append({"event": "start", "trial_id": tid, "method": "dense"})
            env = None
            try:
                random.seed(17)
                np.random.seed(17)
                torch.manual_seed(17)
                task = suite.get_task(state["task_id"])
                env = OffScreenRenderEnv(bddl_file_name=str(Path(get_libero_path("bddl_files")) / task.problem_folder / task.bddl_file),
                    camera_heights=256, camera_widths=256)
                env.seed(0)
                capture = CaptureLongDense(policy, state["requested_control_steps"])
                result = libero_runtime.run_episode(env, capture, task.language, state["initial_state"],
                    wait_steps=10, max_steps=520, policy_watchdog_seconds=60.0)
            finally:
                if env is not None:
                    env.close()
            ledger.append({"event": "result", "trial_id": tid, **result})
            if result["status"] != "completed":
                raise RuntimeError("Long collection failed; preserve failed attempt")
            if result["chunks"][0]["observation_sha256"] != state["reference_initial_observation_sha256"]:
                raise ValueError("Long first observation differs from original dense replay")
            completed.append((state, task.language, result, capture.captured))
            print(json.dumps({"task_id": state["task_id"], "control_steps": result["control_steps"],
                "captured_steps": sorted(capture.captured)}), flush=True)
        after = verify_checkpoint_directory(args.checkpoint, asset)
        if before != after or any(file_sha256(p) != sha for p, sha in watched.items()):
            raise RuntimeError("Long collection source/checkpoint changed")
        provenance = {**identity, "checkpoint_unchanged": True}
        episodes = [save_long_dense_episode(args.output / f"task_{s['task_id']}", s, instruction, result, arrays,
            provenance=provenance) for s, instruction, result, arrays in completed]
        write_long_raw_panel(args.output, panel, episodes, provenance=provenance, registration=registration)
        samples, loaded = load_long_raw_panel(args.output / "panel.json", development_panel=panel,
            dense_reference=reference, registration=registration)
        report = {"status": "completed", "observations": len(samples), "panel": loaded,
            "wall_seconds": time.perf_counter() - began, "cpu_seconds": time.process_time() - cpu_began,
            "execution_wall_seconds_including_model_loading": time.perf_counter() - execution_start,
            "policy_calls": sum(r[2]["policy_calls"] for r in completed), "hardware_after": hardware_telemetry(),
            "checkpoint_unchanged": True, "test_opened": False,
            "cost_scope": "Three dense trajectory replays for raw observations; excluded from success counts and per-call timing, charged in GPU cost"}
        atomic_json(args.output / "collection_report.json", report)
        return {"status": "completed", "observations": len(samples), "missing": loaded["missing"], "policy_calls": report["policy_calls"]}
    except BaseException as exc:
        starts = sum(e["event"] == "start" for e in ledger.events)
        results = [e for e in ledger.events if e["event"] == "result"]
        atomic_json(args.output / "collection_report.json", {"status": "failed", "error": f"{type(exc).__name__}: {exc}",
            "attempted_episodes": starts, "unknown_completion": starts - len(results),
            "known_policy_calls": sum(r.get("policy_calls", 0) for r in results),
            "execution_wall_seconds_including_model_loading": time.perf_counter() - execution_start,
            "checkpoint_unchanged": None, "test_opened": False})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registration", type=Path, required=True)
    parser.add_argument("--development-panel", type=Path, required=True)
    parser.add_argument("--dense-reference", type=Path, required=True)
    parser.add_argument("--asset-manifest", type=Path, default=ROOT / "configs/assets/openvla_oft_libero_long.json")
    for key in ("checkpoint", "cache-directory", "input-acceptance", "output"):
        parser.add_argument("--" + key, type=Path)
    parser.add_argument("--official-source", type=Path, default=ROOT / "external/openvla-oft")
    parser.add_argument("--libero-source", type=Path, default=ROOT / "external/LIBERO")
    parser.add_argument("--libero-config", type=Path, default=ROOT / "configs/libero_runtime")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--prepare-only", action="store_true")
    print(json.dumps(run(parser.parse_args()), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

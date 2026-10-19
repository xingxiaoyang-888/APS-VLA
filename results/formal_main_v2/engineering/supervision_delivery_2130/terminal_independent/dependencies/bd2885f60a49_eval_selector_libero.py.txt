"""Evaluate a G3 best selector on the frozen three-task, ten-dev-state pilot.

Server GPU execution only; --prepare-only checks the CPU initial-state plan.
Uses dense/uniform128/cti128 on the same30 states. No final-test execution and
no latency benchmark are implemented by this development command.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]


def _g0_helpers():
    spec = importlib.util.spec_from_file_location("cti_frozen_g0_cli_helpers", ROOT / "scripts/eval_libero.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(args):
    from cti_vla.evaluation.selector_trials import load_selector_development_panel
    panel = load_selector_development_panel(args.development_states, args.g0_panel, args.test_states)
    if args.prepare_only:
        return {"stage": "G4_development", "status": "panel_prepared_only", "gpu_calls": 0,
                "tasks": sorted({row["task_id"] for row in panel["states"]}), "states": len(panel["states"]),
                "expected_trials": 90, "methods": ["dense", "uniform128", "cti128"],
                "panel_signature": panel["panel_signature"], "checkpoint_validated": False}
    if any(getattr(args, name) is None for name in
           ("g0_report", "g3_report", "selector_checkpoint", "checkpoint", "cache_directory", "output_directory")):
        raise ValueError("formal pilot requires G0/G3 reports, selector/base checkpoints, cache and output directories")
    from cti_vla.data.experiment_protocol import load_experiment_protocol, write_frozen_json
    from cti_vla.data.identity import file_sha256
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation import libero_runtime, selector_runtime
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature, require_g0
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    protocol = load_experiment_protocol(args.protocol)
    manifest = load_checkpoint_manifest(args.asset_manifest)
    g0 = json.loads(args.g0_report.read_text(encoding="utf-8"))
    require_g0(g0, model_revision=manifest.revision, input_version=libero_runtime.INPUTS_VERSION,
               packing_version=PACKING_VERSION)
    if g0["provenance"]["runtime_sha256"] != file_sha256(libero_runtime.__file__) or g0["provenance"]["checkpoint_manifest_sha256"] != file_sha256(args.asset_manifest):
        raise ValueError("selector pilot input/base source differs from accepted G0")
    g3 = json.loads(args.g3_report.read_text(encoding="utf-8"))
    selector = selector_runtime.load_selector_checkpoint(args.selector_checkpoint, g3,
        expected_versions=selector_runtime.selector_expected_versions(manifest.revision, protocol, args.stats_key),
        expected_source_hashes=selector_runtime.deployment_source_hashes(ROOT))
    selector_runtime.validate_selector_training_coverage(selector, g3, protocol)
    if os.name == "nt":
        raise RuntimeError("formal GPU evaluation and trained checkpoints remain on the server")
    common = _g0_helpers()
    source_verification = {"openvla_oft": common.verify_source_checkout(args.official_source, libero_runtime.OFT_COMMIT),
                           "libero": common.verify_source_checkout(args.libero_source, common.LIBERO_COMMIT)}
    from cti_vla.data.initial_states import official_task_catalog
    catalog, mapping = official_task_catalog(args.libero_source)
    if panel["source"]["revision"] != common.LIBERO_COMMIT or any(panel["source"].get(key) != value for key, value in mapping.items()):
        raise ValueError("development task mapping differs from pinned LIBERO source")
    if not (args.libero_config / "config.yaml").is_file():
        raise ValueError("pre-create project LIBERO config; implicit interactive home configuration is forbidden")
    os.environ["LIBERO_CONFIG_PATH"] = str(args.libero_config.resolve())
    for target in (args.output_directory.resolve(), args.cache_directory.resolve()):
        if target == args.checkpoint.resolve() or args.checkpoint.resolve() in target.parents or target == args.selector_checkpoint.resolve().parent or args.selector_checkpoint.resolve().parent in target.parents:
            raise ValueError("evaluation artifacts/caches must stay outside immutable base and trained checkpoint directories")
    common.configure_cache(args.cache_directory, args.checkpoint)
    import numpy as np
    import torch
    from transformers import AutoProcessor
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.evaluation.selector_trials import evaluate_development_trials, summarize_selector_trials
    if torch.cuda.device_count() != 1:
        raise RuntimeError("selector pilot requires one scheduler-allocated GPU")
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    before = verify_checkpoint_directory(args.checkpoint, manifest)
    components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
    processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
    selector.estimator.to(device=device)
    policies = {method: libero_runtime.OpenVLARolloutPolicy(components, processor, stats_key=args.stats_key, method=method)
                for method in ("dense", "uniform128")}
    policies["cti128"] = selector_runtime.SelectorRolloutPolicy(components, processor, selector, stats_key=args.stats_key)
    from libero.libero import benchmark, get_libero_path
    from libero.libero.envs import OffScreenRenderEnv
    import libero.libero as installed_libero
    if args.libero_source.resolve() not in Path(installed_libero.__file__).resolve().parents:
        raise ValueError("installed LIBERO does not resolve inside the verified source checkout")
    suite = benchmark.get_benchmark_dict()[panel["suite"]](task_order_index=0)
    for state in panel["states"]:
        if suite.get_task(state["task_id"]).name != state["task_name"] or catalog[state["task_id"]]["task_name"] != state["task_name"]:
            raise ValueError("runtime task ID/name differs from the frozen development manifest")
    runtime = common.environment_provenance(torch, device)
    config = {"schema_version": 1, "stage": "G4_development", "panel_signature": panel["panel_signature"],
        "selector": dict(selector.provenance), "base_model_revision": manifest.revision,
        "g0_report_sha256": file_sha256(args.g0_report), "g3_report_sha256": file_sha256(args.g3_report),
        "base_manifest_sha256": file_sha256(args.asset_manifest), "source_verification": source_verification,
        "source_hashes": {**selector_runtime.deployment_source_hashes(ROOT),
                          **{path.relative_to(ROOT).as_posix(): file_sha256(path) for path in
                            (Path(__file__), ROOT / "scripts/eval_libero.py", Path(selector_runtime.__file__),
                             ROOT / "src/cti_vla/evaluation/selector_trials.py")}},
        "input_version": libero_runtime.INPUTS_VERSION, "action_version": libero_runtime.ACTION_VERSION,
        "packing_version": PACKING_VERSION, "environment_seed": panel["environment_seed"], "seed": args.seed,
        "methods": list(policies), "wait_steps": 10, "max_steps": 220, "action_chunk": 8,
        "policy_watchdog_seconds": args.policy_watchdog_seconds, "stats_key": args.stats_key,
        "runtime": {key: value for key, value in runtime.items() if key != "slurm_job_id"}}
    signature = json_signature(config)
    args.output_directory.mkdir(parents=True, exist_ok=True)
    write_frozen_json(args.output_directory / "config.json", config)
    write_frozen_json(args.output_directory / "panel.json", panel)
    ledger = libero_runtime.TrialLedger(args.output_directory / "trials.jsonl", run_signature=signature)
    provenance = {**config, "run_signature": signature, "checkpoint": asdict(before), "runtime": runtime}
    ledger.append({"event": "invocation", "slurm_job_id": runtime["slurm_job_id"],
                   "created_utc": datetime.now(timezone.utc).isoformat(), "recovered_tail": ledger.recovered_tail})
    def reseed():
        random.seed(args.seed)
        np.random.seed(args.seed)
        torch.manual_seed(args.seed)
    def create_environment(state):
        task = suite.get_task(state["task_id"])
        env = OffScreenRenderEnv(bddl_file_name=str(Path(get_libero_path("bddl_files")) / task.problem_folder / task.bddl_file),
                                  camera_heights=256, camera_widths=256)
        env.seed(panel["environment_seed"])
        return env, task.language
    def report_result(row):
        atomic_json(args.output_directory / "closed_loop_report.json",
                    summarize_selector_trials(panel, ledger, provenance=provenance))
        print(json.dumps({"trial_id": row["trial_id"], "status": row["status"], "success": row["success"]}), flush=True)
    evaluate_development_trials(panel, policies, ledger, create_environment, reseed=reseed,
        policy_watchdog_seconds=args.policy_watchdog_seconds, stop_after=args.stop_after, on_result=report_result)
    after = verify_checkpoint_directory(args.checkpoint, manifest)
    if before != after or file_sha256(args.selector_checkpoint) != selector.provenance["selector_checkpoint_sha256"]:
        raise RuntimeError("base or trained selector checkpoint changed during evaluation")
    result = summarize_selector_trials(panel, ledger, provenance=provenance, checkpoint_unchanged=True)
    atomic_json(args.output_directory / "closed_loop_report.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    states = ROOT / "configs/manifests/spatial_initial_states_v1"
    parser.add_argument("--development-states", type=Path, default=states / "init_states_development.json")
    parser.add_argument("--g0-panel", type=Path, default=states / "g0_development_15.json")
    parser.add_argument("--test-states", type=Path, default=states / "init_states_test.json")
    parser.add_argument("--protocol", type=Path, default=ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")
    parser.add_argument("--asset-manifest", type=Path, default=ROOT / "configs/assets/openvla_oft_libero_spatial.json")
    parser.add_argument("--official-source", type=Path, default=ROOT / "external/openvla-oft")
    parser.add_argument("--libero-source", type=Path, default=ROOT / "external/LIBERO")
    parser.add_argument("--libero-config", type=Path, default=ROOT / "configs/libero_runtime")
    for name in ("g0-report", "g3-report", "selector-checkpoint", "checkpoint", "cache-directory", "output-directory"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--stats-key", default="libero_spatial_no_noops")
    parser.add_argument("--seed", type=int, default=17, help="Shared environment/runtime RNG seed, independent of checkpoint training seed")
    parser.add_argument("--policy-watchdog-seconds", type=float, default=60.)
    parser.add_argument("--stop-after", type=int)
    parser.add_argument("--prepare-only", action="store_true")
    print(json.dumps(run(parser.parse_args()), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

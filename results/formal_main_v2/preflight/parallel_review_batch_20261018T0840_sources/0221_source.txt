"""G1-F A/B full observation-to-action timing on a fixed development raw panel.

No language/visual/selection/action cache. Cold/hot are the shared runner's
schedule labels; both execute the complete identical uncached path.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from dataclasses import asdict
import gc
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]


def run(args):
    from cti_vla.data.experiment_protocol import load_experiment_protocol, write_frozen_json
    from cti_vla.data.future_windows import load_future_windows
    from cti_vla.data.identity import file_sha256
    from cti_vla.evaluation import future_runtime, libero_runtime
    from cti_vla.evaluation.future_profiling import load_future_raw_panel, load_script, validate_new_output_paths
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation.profiling import (ProfileConfig, ProfileJournal, ProfileMethod, TorchClock,
        hardware_telemetry, profile_methods, read_profile_cost, summarize_latencies, verify_measurement_journal)
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    asset = load_checkpoint_manifest(args.asset_manifest)
    expected_panel = {"model_revision": asset.revision, "input_version": libero_runtime.INPUTS_VERSION,
        "packing_version": PACKING_VERSION, "action_version": libero_runtime.ACTION_VERSION,
        "stats_key": args.stats_key, "runtime_sha256": file_sha256(libero_runtime.__file__)}
    samples, panel = load_future_raw_panel(args.panel, development_path=args.development_states,
        g0_panel_path=args.g0_panel, expected_versions=expected_panel)
    config = ProfileConfig(order_seed=args.order_seed)
    methods = ("dense", "uniform128", "future_A", "future_B")
    if args.prepare_only:
        return {"status": "panel_prepared_only", "gpu_calls": 0, "panel": panel, "methods": methods,
            "config": asdict(config), "planned_full_pipeline_calls": 4 * (50 + len(samples) * 2 * 6),
            "f01_accepted": False, "checkpoint_validated": False, "cache_enabled": False, "test_opened": False}
    if os.name == "nt" or not os.environ.get("SLURM_JOB_ID") or not args.uncontended_gpu:
        raise RuntimeError("real timing requires Slurm and explicit uncontended-GPU attestation")
    required = ("f01_report", "checkpoint_a", "checkpoint_b", "receipt_a", "receipt_b", "checkpoint", "cache_directory", "output")
    if any(getattr(args, key) is None for key in required):
        raise ValueError("timing requires F01, completed A/B checkpoint/receipts, frozen base, cache and new output")
    validate_new_output_paths(project_root=args.project_root, source_root=ROOT, output=args.output,
        cache=args.cache_directory, weight_roots=[args.checkpoint, args.checkpoint_a.parent, args.checkpoint_b.parent])
    execution_start = time.perf_counter()
    watched_paths = [args.config, args.window_manifest, args.protocol, args.f01_report, args.checkpoint_a, args.checkpoint_b,
        args.receipt_a, args.receipt_b, args.asset_manifest, args.panel]
    watched = {str(p.resolve()): file_sha256(p) for p in watched_paths}
    def unchanged():
        if any(file_sha256(p) != digest for p, digest in watched.items()):
            raise ValueError("frozen G1-F timing configuration/evidence/checkpoint bytes changed")
    common_config = json.loads(args.config.read_text(encoding="utf-8"))
    protocol = load_experiment_protocol(args.protocol)
    windows = load_future_windows(args.window_manifest, protocol)
    f01 = json.loads(args.f01_report.read_text(encoding="utf-8"))
    future_runtime.require_future_f01(f01, pair_id=json_signature(common_config),
        window_manifest_sha256=watched[str(args.window_manifest.resolve())], model_revision=asset.revision)
    expected = {"model_revision": asset.revision, "input_version": libero_runtime.INPUTS_VERSION,
        "packing_version": PACKING_VERSION, "stats_key": args.stats_key,
        "window_manifest_sha256": watched[str(args.window_manifest.resolve())],
        "f01_report_sha256": watched[str(args.f01_report.resolve())]}
    sources = future_runtime.future_deployment_source_hashes(ROOT)
    receipts, preliminary = {}, {}
    for arm in ("A", "B"):
        receipts[arm] = json.loads(getattr(args, "receipt_" + arm.lower()).read_text(encoding="utf-8"))
        if receipts[arm].get("pair_config") != common_config:
            raise ValueError("A/B timing pair differs from the accepted common configuration")
        preliminary[arm] = future_runtime.load_future_selector_checkpoint(getattr(args, "checkpoint_" + arm.lower()),
            receipts[arm], expected_versions=expected, expected_source_hashes=sources)
    future_runtime.validate_future_pair(preliminary["A"], preliminary["B"])
    selector_provenance = {arm: dict(value.provenance) for arm, value in preliminary.items()}
    del preliminary
    common = load_script(ROOT, "eval_libero")
    common.configure_cache(args.cache_directory, args.checkpoint)
    import torch
    from transformers import AutoProcessor
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    if torch.cuda.device_count() != 1:
        raise RuntimeError("timing requires exactly one allocated visible GPU")
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    torch.manual_seed(args.order_seed)
    before = verify_checkpoint_directory(args.checkpoint, asset)
    load_start = time.perf_counter()
    components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
    processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
    torch.cuda.synchronize(device)
    loading_seconds = time.perf_counter() - load_start
    unchanged()
    # Reuse the tested shared lightweight baseline without invoking its old G5 CLI.
    baseline_module = load_script(ROOT, "profile_observation_to_action")
    factories = {}
    for name in methods:
        def factory(name=name):
            gc.collect()
            unchanged()
            if name.startswith("future_"):
                arm = name[-1]
                loaded = future_runtime.load_future_selector_checkpoint(getattr(args, "checkpoint_" + arm.lower()),
                    receipts[arm], expected_versions=expected, expected_source_hashes=sources, device=device)
                policy = future_runtime.FutureRolloutPolicy(components, processor, loaded,
                    stats_key=args.stats_key, record_selection=False)
                provenance = dict(loaded.provenance)
                if provenance != selector_provenance[arm]:
                    raise ValueError("deployed A/B selector identity changed between timing rounds")
            else:
                policy = baseline_module.MatchedBaseline(components, processor, stats_key=args.stats_key, method=name)
                provenance = dict(expected_panel)
            return ProfileMethod(policy, {"provenance": provenance, "instruction_cache_enabled": False,
                "cache_scope": "none", "instruction_modes_note": "Both labels recompute all language; no cache or cache speedup.",
                "future_head_deployed": False, "policy_calls_per_chunk": 1, "precision": "base_bfloat16_DIE_float32",
                "attention": "sdpa", "batch_size": 1},
                lambda context: setattr(policy, "stage_context", context or (lambda _: nullcontext())))
        factories[name] = factory
    args.output.mkdir(parents=True, exist_ok=False)
    source_paths = [*sorted((ROOT / "src/cti_vla").rglob("*.py")),
        ROOT / "src/cti_vla_baselines/acl_matched.py", ROOT / "scripts/profile_observation_to_action.py", Path(__file__)]
    identity = {"stage": "G1-F_development_latency", "test_opened": False, "panel": panel, "config": asdict(config),
        "methods": list(methods), "selector_provenance": selector_provenance, "checkpoint_hashes": watched,
        "window_content_signature": windows["content_signature"], **expected_panel,
        "pair_id": json_signature(common_config), "source_files": {p.relative_to(ROOT).as_posix(): file_sha256(p) for p in source_paths},
        "hardware": hardware_telemetry(), "uncontended_gpu_attested": True, "language_cache_enabled": False,
        "model_loading_seconds_excluded": loading_seconds, "compile": "disabled; native eager SDPA",
        "limitations": "Three development trajectories, up to nine fixed-step observations; no final-test or population claims. Cold/hot are identical uncached paths."}
    write_frozen_json(args.output / "config.json", identity)
    journal_path = args.output / "calls.jsonl"
    journal = ProfileJournal(journal_path, identity)
    began, cpu_began = time.perf_counter(), time.process_time()
    try:
        result = profile_methods(samples, factories, config=config, clock=TorchClock(device), emit=journal, telemetry=hardware_telemetry)
        after = verify_checkpoint_directory(args.checkpoint, asset)
        unchanged()
        if before != after:
            raise RuntimeError("immutable base checkpoint changed during timing")
        result.update(provenance=identity, checkpoint_unchanged=True, cost=read_profile_cost(journal_path),
            wall_seconds_including_measurement_overhead=time.perf_counter() - began,
            execution_wall_seconds_including_model_loading=time.perf_counter() - execution_start,
            cpu_seconds=time.process_time() - cpu_began, hardware_after=hardware_telemetry())
        verify_measurement_journal(result, journal_path)
        atomic_json(args.output / "measurements.json", result)
        summary = summarize_latencies(result)
        summary.update(stage="G1-F_development_latency", panel=panel, test_opened=False,
            checkpoint_unchanged=True, cost=result["cost"], measurements_sha256=file_sha256(args.output / "measurements.json"),
            journal_sha256=file_sha256(journal_path), provenance=identity,
            wall_seconds_including_measurement_overhead=result["wall_seconds_including_measurement_overhead"],
            execution_wall_seconds_including_model_loading=result["execution_wall_seconds_including_model_loading"],
            limitations=identity["limitations"])
        atomic_json(args.output / "summary.json", summary)
        return {"status": summary["status"], "observations": len(samples), "methods": list(methods), "cost": result["cost"]}
    except BaseException as exc:
        try:
            cost = read_profile_cost(journal_path)
        except Exception as cost_error:
            cost = {"unavailable": str(cost_error), "charged_work_must_not_be_assumed_zero": True}
        atomic_json(args.output / "summary.json", {"status": "failed", "stage": "G1-F_development_latency",
            "error": f"{type(exc).__name__}: {exc}", "cost": cost, "checkpoint_unchanged": None,
            "wall_seconds_including_measurement_overhead": time.perf_counter() - began,
            "execution_wall_seconds_including_model_loading": time.perf_counter() - execution_start,
            "cpu_seconds": time.process_time() - cpu_began, "test_opened": False})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, required=True)
    states = ROOT / "configs/manifests/spatial_initial_states_v1"
    parser.add_argument("--development-states", type=Path, default=states / "init_states_development.json")
    parser.add_argument("--g0-panel", type=Path, default=states / "g0_development_15.json")
    parser.add_argument("--config", type=Path, default=ROOT / "configs/experiments/g1_future_v1.json")
    parser.add_argument("--window-manifest", type=Path, default=ROOT / "configs/manifests/spatial_future_v1/windows.json")
    parser.add_argument("--protocol", type=Path, default=ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")
    parser.add_argument("--asset-manifest", type=Path, default=ROOT / "configs/assets/openvla_oft_libero_spatial.json")
    for name in ("f01-report", "checkpoint-a", "checkpoint-b", "receipt-a", "receipt-b", "checkpoint", "cache-directory", "output"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--stats-key", default="libero_spatial_no_noops")
    parser.add_argument("--order-seed", type=int, default=1017)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--uncontended-gpu", action="store_true")
    print(json.dumps(run(parser.parse_args()), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

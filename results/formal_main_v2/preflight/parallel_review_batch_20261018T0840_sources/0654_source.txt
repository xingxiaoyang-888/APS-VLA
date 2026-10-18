"""Time dense and all twelve Long A/B deployments on one raw observation panel."""
from __future__ import annotations

import argparse
from contextlib import contextmanager, nullcontext
from dataclasses import asdict
import gc
import inspect
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def method_specs(path, registration_path):
    from cti_vla.data.identity import file_sha256
    from cti_vla.evaluation.future_long_profiling import LONG_METHODS, LONG_PROFILE_VERSION
    payload, registration = read(path), read(registration_path)
    if payload.get("version") != LONG_PROFILE_VERSION or payload.get("registration_sha256") != file_sha256(registration_path):
        raise ValueError("method identities must be frozen against the timing preregistration")
    rows = payload["methods"]
    if tuple(r["name"] for r in rows) != LONG_METHODS or rows[0] != {"name": "dense"}:
        raise ValueError("Long timing requires exactly the13 registered deployment instances")
    for row in rows[1:]:
        name = row["name"]
        if row.get("seed") != int(name.split("seed")[1]) or row.get("total_tokens") != int(name.split("_")[0][1:]):
            raise ValueError("method seed/budget differs from its registered identity")
        for key in ("checkpoint", "receipt", "f01_report", "input_acceptance", "source_inventory"):
            ref = row[key]
            if file_sha256(ref["path"]) != ref["sha256"]:
                raise ValueError("immutable timing method reference changed: " + name + ":" + key)
        receipt = read(row["receipt"]["path"])
        if row["checkpoint"]["sha256"] != receipt.get("checkpoint_sha256"):
            raise ValueError("profile checkpoint is not the trained receipt's selected best")
        frozen = registration["frozen_evidence_sha256"]
        input_key = "results/g1_future_long_v1/inputs/input_acceptance.json"
        if row["input_acceptance"]["sha256"] != frozen[input_key]:
            raise ValueError("profile input acceptance differs from preregistered original Long evidence")
        if row["total_tokens"] == 128:
            seed, arm = row["seed"], name[0]
            root = "results/g1_future_long_v1" if seed == 17 else f"results/g1_future_long_multiseed_v1/seed{seed}"
            inventory_key = ("results/g1_future_long/source_g1_future_long_v1.json" if seed == 17 else
                "results/g1_future_long_multiseed_v1/source_g1_future_long_multiseed_v1.json")
            anchors = {"receipt": f"{root}/training/{arm}/deployment_receipt.json",
                "source_inventory": inventory_key,
                "f01_report": "results/g1_future_long_v1/acceptance/f01_acceptance.json"}
            if any(row[field]["sha256"] != frozen[key] for field, key in anchors.items()):
                raise ValueError("old128 profile identity differs from preregistered immutable result")
        else:
            anchor = registration["new_configs"][str(row["seed"]) ]
            config_path = ROOT / anchor["path"]
            if file_sha256(config_path) != anchor["sha256"] or receipt.get("pair_config") != read(config_path):
                raise ValueError("new64 profile receipt differs from registered training seed/config")
            expected = Path(anchor["checkpoint_root_server"]) / name[0] / "best.pt"
            if Path(row["checkpoint"]["path"]).resolve() != expected.resolve():
                raise ValueError("new64 profiling requires its own registered selected checkpoint")
            if Path(row["source_root"]).resolve() != ROOT.resolve():
                raise ValueError("new64 profiling requires the current frozen production snapshot")
    return rows


def uncontended_device():
    """Read-only process inventory for this process's one CUDA device."""
    output = subprocess.run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=10, check=True).stdout
    rows = [(parts[0].strip(), int(parts[1].strip())) for line in output.splitlines()
        if len(parts := line.split(",")) == 2 and parts[1].strip().isdigit()]
    own = {uuid for uuid, pid in rows if pid == os.getpid()}
    if len(own) != 1:
        raise RuntimeError("cannot attest this process's unique allocated GPU UUID")
    uuid = next(iter(own))
    competitors = sorted({pid for gpu, pid in rows if gpu == uuid and pid != os.getpid()})
    if competitors:
        raise RuntimeError("other compute process shares the allocated timing GPU; retain this bounded attempt")
    return {"gpu_uuid": uuid, "own_pid": os.getpid(), "other_compute_processes": 0}


def run(args):
    from cti_vla.data.identity import file_sha256
    from cti_vla.data.long_initial_states import load_long_development_panel
    from cti_vla.evaluation import libero_runtime
    from cti_vla.evaluation.future_dense_reuse import load_dense_reference
    from cti_vla.evaluation.future_long_profiling import (LONG_PROFILE_VERSION, profile_registration,
        load_long_raw_panel, load_snapshot_deployment_modules, original_auxiliary_module,
        profile_long_methods, verify_long_profile_journal, summarize_long_profile)
    from cti_vla.evaluation.future_profiling import load_script, validate_new_output_paths
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation.profiling import ProfileJournal, ProfileMethod, TorchClock, hardware_telemetry, read_profile_cost
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    registration = read(args.registration)
    config = dict(profile_registration(registration))
    development = load_long_development_panel(args.development_panel)
    dense = load_dense_reference(args.dense_reference, development)
    asset = load_checkpoint_manifest(args.asset_manifest)
    expected_panel = {"model_revision": asset.revision, "input_version": libero_runtime.INPUTS_VERSION,
        "packing_version": PACKING_VERSION, "action_version": libero_runtime.ACTION_VERSION,
        "stats_key": "libero_10_no_noops", "runtime_sha256": file_sha256(libero_runtime.__file__)}
    samples, panel = load_long_raw_panel(args.panel, development_panel=development,
        dense_reference=dense, registration=registration, expected_versions=expected_panel)
    if len({s.episode_id for s in samples}) != 3:
        raise ValueError("Long timing stops when all three registered development tasks are not represented")
    if args.prepare_only:
        return {"status": "prepared_only", "gpu_calls": 0, "panel": panel,
            "planned_full_pipeline_calls": 13 * (20 + 20 * len(samples)), "test_opened": False,
            "methods_validated": False, "checkpoint_validated": False}
    if os.name == "nt" or not os.environ.get("SLURM_JOB_ID") or not args.uncontended_gpu:
        raise RuntimeError("real Long timing requires Slurm and an uncontended GPU attestation")
    if any(getattr(args, k) is None for k in ("methods", "checkpoint", "cache_directory", "output")):
        raise ValueError("timing requires completed immutable method identities, base, cache and new output")
    specs = method_specs(args.methods, args.registration)
    validate_new_output_paths(project_root=args.project_root, source_root=ROOT, output=args.output,
        cache=args.cache_directory, weight_roots=[args.checkpoint, *[Path(r["checkpoint"]["path"]).parent for r in specs[1:]]])
    execution_start = time.perf_counter()
    watched_paths = [args.registration, args.methods, args.panel, args.development_panel, args.asset_manifest]
    watched_paths += [Path(row[key]["path"]) for row in specs[1:]
        for key in ("checkpoint", "receipt", "f01_report", "input_acceptance", "source_inventory")]
    watched = {str(path.resolve()): file_sha256(path) for path in watched_paths}

    def unchanged():
        if any(file_sha256(path) != digest for path, digest in watched.items()):
            raise ValueError("Long timing frozen configuration/evidence/selector bytes changed")

    loaded, snapshots, modules, identities = {}, {}, {}, {}
    for row in specs[1:]:
        name = row["name"]
        source_root = Path(row["source_root"])
        inventory = Path(row["source_inventory"]["path"])
        key = (str(source_root.resolve()), str(inventory.resolve()))
        if key not in snapshots:
            snapshots[key] = load_snapshot_deployment_modules(source_root, inventory, current_root=ROOT)
        runtime, aux, source = snapshots[key]
        modules[name] = (runtime, aux)
        f01 = read(row["f01_report"]["path"])
        input_report = read(row["input_acceptance"]["path"])
        receipt = read(row["receipt"]["path"])
        common_config = receipt["pair_config"]
        if (common_config.get("seed") != row["seed"] or receipt["metadata"]["arm"] != name[0]
                or common_config.get("tokens_per_camera", 64) * 2 != row["total_tokens"]
                or input_report.get("status") != "passed" or input_report.get("checkpoint_unchanged") is not True
                or f01.get("input_acceptance_sha256") != row["input_acceptance"]["sha256"]):
            raise ValueError("Long profile method differs from accepted trained seed/arm/budget/input")
        acceptance_kwargs = {"suite": "libero_10", "input_acceptance_sha256": row["input_acceptance"]["sha256"]}
        if "visual_tokens" in inspect.signature(runtime.require_future_f01).parameters:
            acceptance_kwargs.update(visual_tokens=row["total_tokens"], per_camera_budgets=[row["total_tokens"] // 2] * 2)
        runtime.require_future_f01(f01, pair_id=f01["config_sha256"],
            window_manifest_sha256=receipt["metadata"]["window_manifest_sha256"],
            model_revision=asset.revision, **acceptance_kwargs)
        if row["total_tokens"] == 64:
            from cti_vla.evaluation.future_budget_reuse import require_budget_f01
            accepted = require_budget_f01(Path(row["f01_report"]["path"]), config=common_config,
                source_root=source_root, window_manifest_sha256=receipt["metadata"]["window_manifest_sha256"],
                input_acceptance_sha256=row["input_acceptance"]["sha256"])
            watched.update(accepted["watched_files"])
        expected = {"suite": "libero_10", "model_revision": asset.revision,
            "input_version": libero_runtime.INPUTS_VERSION, "packing_version": PACKING_VERSION,
            "stats_key": "libero_10_no_noops", "input_acceptance_sha256": row["input_acceptance"]["sha256"],
            "window_manifest_sha256": receipt["metadata"]["window_manifest_sha256"],
            "f01_report_sha256": row["f01_report"]["sha256"]}
        if row["total_tokens"] == 64:
            expected.update(visual_tokens=64, per_camera_budgets=[32, 32])
        loaded[name] = runtime.load_future_selector_checkpoint(row["checkpoint"]["path"], receipt,
            expected_versions=expected, expected_source_hashes=source["deployment_source_files"])
        identities[name] = {"selector": dict(loaded[name].provenance), "snapshot": source,
            "total_tokens": row["total_tokens"], "training_seed": row["seed"], "arm": name[0],
            "checkpoint_ref": row["checkpoint"], "receipt_ref": row["receipt"]}
    for budget in (128, 64):
        for seed in (17, 23, 41):
            name_a, name_b = f"A{budget}_seed{seed}", f"B{budget}_seed{seed}"
            modules[name_a][0].validate_future_pair(loaded[name_a], loaded[name_b])
    common = load_script(ROOT, "eval_libero")
    common.configure_cache(args.cache_directory, args.checkpoint)
    import torch
    from transformers import AutoProcessor
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    if torch.cuda.device_count() != 1 or torch.cuda.get_device_name(0) != "NVIDIA L40":
        raise RuntimeError("Long timing requires one allocated NVIDIA L40")
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    torch.manual_seed(1017)
    # Initialize only the CUDA context so competing processes are checked
    # before loading the large base. This is not a policy inference.
    torch.empty(0, device=device)
    allocation = uncontended_device()
    runtime = common.environment_provenance(torch, device)
    expected_runtime = dense["identity"]["runtime_semantics"]
    if any(runtime.get(key) != value for key, value in expected_runtime.items()):
        raise ValueError("Long timing environment differs from the development success reference")
    before = verify_checkpoint_directory(args.checkpoint, asset)
    load_start = time.perf_counter()
    components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
    processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
    torch.cuda.synchronize(device)
    loading_seconds = time.perf_counter() - load_start
    baseline = load_script(ROOT, "profile_observation_to_action")
    factories = {}
    for row in specs:
        name = row["name"]

        @contextmanager
        def factory(name=name):
            gc.collect()
            if name == "dense":
                policy = baseline.MatchedBaseline(components, processor, stats_key="libero_10_no_noops", method="dense")
                active = nullcontext()
                provenance = {**expected_panel, "total_tokens": 512}
            else:
                runtime_module, aux = modules[name]
                loaded[name].estimator.to(device)
                policy = runtime_module.FutureRolloutPolicy(components, processor, loaded[name],
                    stats_key="libero_10_no_noops", record_selection=False)
                active = original_auxiliary_module(aux)
                provenance = identities[name]
            method = ProfileMethod(policy, {"provenance": provenance, "cache_scope": "none",
                "instruction_cache_enabled": False, "future_head_deployed": False,
                "precision": "base_bfloat16_DIE_float32", "attention": "sdpa", "batch_size": 1},
                lambda context: setattr(policy, "stage_context", context or (lambda _: nullcontext())))
            try:
                with active:
                    yield method
            finally:
                if name != "dense":
                    loaded[name].estimator.to("cpu")
                del method, policy
        factories[name] = factory
    unchanged()
    args.output.mkdir(parents=True, exist_ok=False)
    identity = {"version": LONG_PROFILE_VERSION, "stage": "G1-F_Long_budget_latency", "test_opened": False,
        "registration_sha256": file_sha256(args.registration), "registration_signature": json_signature(registration),
        "methods_manifest_sha256": file_sha256(args.methods), "config": config,
        "method_identities": identities, "panel": panel, "watched": watched,
        "source_files": {str(p.relative_to(ROOT)).replace("\\", "/"): file_sha256(p) for p in (
            Path(__file__), ROOT / "scripts/profile_observation_to_action.py",
            ROOT / "src/cti_vla/evaluation/future_long_profiling.py", ROOT / "src/cti_vla/evaluation/profiling.py")},
        "base": asdict(before), "runtime": runtime, "allocation": allocation, "hardware": hardware_telemetry(),
        "model_loading_seconds_excluded_from_calls": loading_seconds,
        "all_instances_share_one_loaded_base": True, "uncontended_gpu_attested_and_checked": True,
        "compile": "disabled; native eager SDPA", "cache_scope": "none", "future_head_deployed": False,
        **expected_panel}
    atomic_json(args.output / "config.json", identity)
    journal_path = args.output / "calls.jsonl"
    journal = ProfileJournal(journal_path, identity)
    began, cpu_began = time.perf_counter(), time.process_time()

    def telemetry():
        return {**hardware_telemetry(), "uncontended_device": uncontended_device()}

    try:
        result = profile_long_methods(samples, factories, config=config,
            clock=TorchClock(device), emit=journal, telemetry=telemetry)
        after = verify_checkpoint_directory(args.checkpoint, asset)
        unchanged()
        if before != after:
            raise RuntimeError("Long timing immutable base changed")
        result.update(provenance=identity, checkpoint_unchanged=True, cost=read_profile_cost(journal_path),
            wall_seconds_including_measurement_overhead=time.perf_counter() - began,
            execution_wall_seconds_including_model_loading=time.perf_counter() - execution_start,
            cpu_seconds=time.process_time() - cpu_began, hardware_after=telemetry())
        verify_long_profile_journal(result, journal_path)
        atomic_json(args.output / "measurements.json", result)
        summary = summarize_long_profile(result)
        summary.update(checkpoint_unchanged=True, cost=result["cost"], panel=panel,
            measurements_sha256=file_sha256(args.output / "measurements.json"), journal_sha256=file_sha256(journal_path),
            config_sha256=file_sha256(args.output / "config.json"),
            execution_wall_seconds_including_model_loading=result["execution_wall_seconds_including_model_loading"])
        atomic_json(args.output / "summary.json", summary)
        return {"status": summary["status"], "observations": len(samples), "deployment_instances": 13, "cost": result["cost"]}
    except BaseException as exc:
        atomic_json(args.output / "summary.json", {"status": "failed", "stage": "G1-F_Long_budget_latency",
            "error": f"{type(exc).__name__}: {exc}", "cost": read_profile_cost(journal_path),
            "execution_wall_seconds_including_model_loading": time.perf_counter() - execution_start,
            "checkpoint_unchanged": None, "test_opened": False})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("registration", "panel", "development-panel", "dense-reference"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--asset-manifest", type=Path, default=ROOT / "configs/assets/openvla_oft_libero_long.json")
    for key in ("methods", "checkpoint", "cache-directory", "output"):
        parser.add_argument("--" + key, type=Path)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--uncontended-gpu", action="store_true")
    print(json.dumps(run(parser.parse_args()), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

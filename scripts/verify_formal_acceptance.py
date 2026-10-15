"""Formal four-suite F00/F01: fixed three train windows, all three budgets.

Only root submits this CLI to Slurm. No development/final-state file is opened.
Failed attempts retain the complete durable journal and allocation cost.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import importlib.util
import json
import os
from pathlib import Path
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
CAPACITY_ROOT = Path("/share/home/u15016/XXY_CVPR/CTI-VLA")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_feature_cache_path(project_root, cache_path, suite, *, capacity_root=CAPACITY_ROOT):
    project, path = Path(project_root).resolve(), Path(cache_path).resolve()
    capacity = (Path(capacity_root) / "data/formal_main_v2" / suite).resolve()
    if path == capacity or capacity in path.parents:
        return path
    if project not in path.parents:
        raise ValueError("formal feature cache must stay in the project or its exact registered capacity suite cache")
    relative = path.relative_to(project)
    if not relative.parts or relative.parts[0] in ("models", "checkpoints", "src", "scripts", "external", "configs"):
        raise ValueError("formal feature cache cannot overlap source/configuration/weight directories")
    return path


def validate_engineering_checkpoint_path(path, suite, *, capacity_root=CAPACITY_ROOT):
    allowed = (Path(capacity_root) / "checkpoints/formal_main_v2/engineering" / suite).resolve()
    path = allowed if path is None else Path(path).resolve()
    if path != allowed and allowed not in path.parents:
        raise ValueError("formal engineering weights must stay in the exact registered capacity suite directory")
    return path


def _official_parity_function():
    spec = importlib.util.spec_from_file_location("formal_official_dense_parity_core", ROOT / "scripts/verify_long_inputs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.verify_one


def run(args):
    from cti_vla.data.formal_windows import load_formal_protocol, load_formal_windows, validate_formal_window
    from cti_vla.data.identity import file_sha256
    from cti_vla.evaluation.formal_acceptance import (select_formal_acceptance_windows,
        require_formal_input_acceptance, require_formal_acceptance, acceptance_source_hashes,
        module_parameter_sha256, run_formal_operator_window, verify_formal_operator_journal)
    from cti_vla.evaluation.formal_runtime import FORMAL_SCHEMA, FORMAL_SUITES
    from cti_vla.evaluation import libero_runtime
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation.future_profiling import validate_new_output_paths
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    from cti_vla.training.formal_future import validate_formal_training_config, append_event
    configs = [read_json(path) for path in args.configs]
    for config in configs:
        validate_formal_training_config(config)
    if (len(configs) != 3 or {c["tokens_per_camera"] for c in configs} != {32, 64, 128}
            or any(c["seed"] != 17 or c["suite"] != args.suite for c in configs)):
        raise ValueError("formal acceptance requires all three seed17 budget configurations for exactly one suite")
    strip = lambda c: {k: v for k, v in c.items() if k not in ("tokens_per_camera", "run_id")}
    if any(strip(c) != strip(configs[0]) for c in configs):
        raise ValueError("formal engineering budgets differ outside their token budget/run ID")
    protocol = load_formal_protocol(args.protocol, project_root=args.project_root)
    manifest = load_formal_windows(args.windows, protocol)
    selected = select_formal_acceptance_windows(manifest, protocol)
    config = configs[0]
    asset = load_checkpoint_manifest(args.asset_manifest)
    if (asset.revision != config["model_revision"] or config["stats_key"] != FORMAL_SUITES[args.suite]["stats_key"]
            or manifest["suite"] != args.suite):
        raise ValueError("formal base/data/suite identity differs")
    if args.prepare_only:
        return dict(schema=FORMAL_SCHEMA, status="prepared_only", suite=args.suite, selected_windows=selected,
            budgets=[256, 128, 64], gpu_calls=0, test_opened=False, f00_accepted=False, f01_accepted=False)
    if os.name == "nt" or not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("formal real engineering acceptance requires server Slurm allocation")
    validate_new_output_paths(project_root=args.project_root, source_root=ROOT, output=args.output,
        cache=args.cache_directory, weight_roots=[args.checkpoint])
    validate_feature_cache_path(args.project_root, args.feature_cache, args.suite)
    engineering_checkpoints = validate_engineering_checkpoint_path(args.engineering_checkpoints, args.suite)
    if args.feature_cache.resolve() == args.checkpoint.resolve() or args.checkpoint.resolve() in args.feature_cache.resolve().parents:
        raise ValueError("formal feature cache must stay outside immutable base weights")
    sources = acceptance_source_hashes(ROOT)
    watched = {str(p.resolve()): file_sha256(p) for p in [*args.configs, args.protocol, args.windows, args.asset_manifest]}
    before = verify_checkpoint_directory(args.checkpoint, asset)
    for directory in (args.cache_directory, args.cache_directory / "hub", args.cache_directory / "modules"):
        directory.mkdir(parents=True, exist_ok=True)
    os.environ.update(HF_HOME=str(args.cache_directory), HF_HUB_CACHE=str(args.cache_directory / "hub"),
        HF_MODULES_CACHE=str(args.cache_directory / "modules"), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    import torch
    from transformers import AutoProcessor
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
    from cti_vla.training.formal_records import FormalRecordProvider
    from cti_vla_baselines.acl_matched import FrozenDifferentiableOFTPolicy
    from cti_vla.evaluation.future_input_acceptance import verify_input_acceptance_journal
    if torch.cuda.device_count() != 1:
        raise RuntimeError("formal engineering acceptance requires exactly one visible GPU")
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    torch.manual_seed(17)
    reference = libero_runtime.load_official_reference_functions(args.oft_source)
    watched.update({str((args.oft_source / p).resolve()): file_sha256(args.oft_source / p) for p in libero_runtime._REFERENCE_FILES})
    args.output.mkdir(parents=True, exist_ok=False)
    journal, operators = args.output / "input_calls.jsonl", args.output / "operator_calls.jsonl"
    started, input_calls, operator_calls = time.perf_counter(), 0, 0
    job_id = os.environ["SLURM_JOB_ID"]
    def query_for(path, row, budget=None):
        def query(kind, fn):
            nonlocal input_calls, operator_calls
            index = input_calls if budget is None else operator_calls
            if budget is None:
                input_calls += 1
            else:
                operator_calls += 1
            identity = dict(call_id=index, window_id=row["window_id"], kind=kind, job_id=job_id)
            if budget is not None:
                identity["visual_tokens"] = budget
            append_event(path, {"event": "start", **identity})
            t0 = time.perf_counter()
            try:
                value = fn()
                torch.cuda.synchronize(device)
            except BaseException as exc:
                append_event(path, {"event": "failed", **identity, "error": str(exc), "seconds": time.perf_counter() - t0})
                raise
            append_event(path, {"event": "complete", **identity, "seconds": time.perf_counter() - t0})
            return value
        return query
    def unchanged():
        if sources != acceptance_source_hashes(ROOT) or any(file_sha256(p) != v for p, v in watched.items()):
            raise ValueError("formal acceptance source/config/input bytes changed")
        if module_parameter_sha256(components) != frozen:
            raise ValueError("formal frozen VLA parameter/buffer bytes changed")
        student.require_frozen()
    try:
        components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
        processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
        policy = OpenVLAOFTTokenPolicy(components.vla, components.action_head, components.proprio_projector, num_patches_full=512)
        student = FrozenDifferentiableOFTPolicy(policy, components.vla.projector,
            model_revision=asset.revision, input_version=libero_runtime.INPUTS_VERSION)
        frozen = module_parameter_sha256(components)
        provider = FormalRecordProvider(protocol=protocol, manifest=manifest, data_directory=args.data_directory,
            components=components, processor=processor, policy=policy, stats_key=config["stats_key"],
            cache_root=args.feature_cache, events_path=args.output / "cache_cost_events.jsonl", job_id=job_id,
            cache_identity=dict(suite=args.suite, model_revision=asset.revision, asset_manifest_sha256=file_sha256(args.asset_manifest),
                data_protocol_sha256=file_sha256(args.protocol), window_manifest_sha256=file_sha256(args.windows),
                dataset_statistics_sha256=file_sha256(args.checkpoint / "dataset_statistics.json"), producer_source_files=sources))
        torch.cuda.reset_peak_memory_stats(device)
        observations = []
        verify_one = _official_parity_function()
        for row in selected:
            episode = provider.get_episode(row)
            validate_formal_window(row, episode, protocol)
            observations.append(verify_one(episode, row, components, processor, policy, reference,
                stats_key=config["stats_key"], query=query_for(journal, row)))
        unchanged()
        if before != verify_checkpoint_directory(args.checkpoint, asset):
            raise ValueError("formal base files changed during official parity")
        f00 = dict(schema=FORMAL_SCHEMA, kind="input_acceptance", status="passed", execution="real_frozen_openvla_slurm",
            suite=args.suite, stats_key=config["stats_key"], model_revision=asset.revision,
            window_manifest_sha256=file_sha256(args.windows), data_protocol_sha256=file_sha256(args.protocol),
            asset_manifest_sha256=file_sha256(args.asset_manifest), source_files=sources,
            input_version=libero_runtime.INPUTS_VERSION, action_version=libero_runtime.ACTION_VERSION,
            packing_version=PACKING_VERSION, checkpoint_unchanged=True, checkpoint=asdict(before),
            frozen_model_sha256=frozen, observations=observations, test_opened=False,
            policy_sample_forwards=6, policy_attempts=input_calls, vision_forwards=6,
            calls_jsonl_sha256=file_sha256(journal), official_source_revision=libero_runtime.OFT_COMMIT,
            hardware=torch.cuda.get_device_name(), job_id=job_id, wall_seconds=time.perf_counter() - started)
        require_formal_input_acceptance(f00, config=config, window_manifest_sha256=file_sha256(args.windows),
            data_protocol_sha256=file_sha256(args.protocol), asset_manifest_sha256=file_sha256(args.asset_manifest),
            source_files=sources, selected_windows=selected)
        verify_input_acceptance_journal(journal, f00)
        f00_path = args.output / "input_acceptance.json"
        atomic_json(f00_path, f00)
        reports = []
        # The registered first engineering run is the primary128-token budget.
        for current in sorted(configs, key=lambda c: (64, 128, 32).index(c["tokens_per_camera"])):
            total = current["tokens_per_camera"] * 2
            t0 = time.perf_counter()
            rows = []
            for row in selected:
                record = provider.get(row["window_id"])
                episode = provider.get_episode(row)
                rows.append(run_formal_operator_window(config=current, window=row, record=record,
                    components=components, processor=processor, policy=policy, student=student, episode=episode,
                    query=query_for(operators, row, total)))
                unchanged()
            report = dict(schema=FORMAL_SCHEMA, kind="operator_acceptance", status="passed", execution="real_frozen_openvla_slurm",
                suite=args.suite, stats_key=current["stats_key"], model_revision=asset.revision,
                accepted_pair_config=current, accepted_pair_id=json_signature(current), visual_tokens=total,
                per_camera_budgets=[total // 2] * 2, window_manifest_sha256=file_sha256(args.windows),
                input_acceptance_sha256=file_sha256(f00_path), frozen_model_sha256=frozen,
                source_files=sources, input_version=libero_runtime.INPUTS_VERSION, packing_version=PACKING_VERSION,
                checkpoint_unchanged=True, test_opened=False, observations=rows, job_id=job_id,
                hardware=torch.cuda.get_device_name(), wall_seconds=time.perf_counter() - t0,
                peak_memory_allocated_bytes=torch.cuda.max_memory_allocated(device),
                operator_journal_prefix_sha256=file_sha256(operators), operator_journal_prefix_bytes=operators.stat().st_size,
                operator_probes_completed=operator_calls)
            require_formal_acceptance(report, config=current, window_manifest_sha256=file_sha256(args.windows),
                input_acceptance_sha256=file_sha256(f00_path), source_files=sources, selected_windows=selected)
            verify_formal_operator_journal(operators, report)
            path = args.output / f"f01_k{total}.json"
            atomic_json(path, report)
            reports.append({"visual_tokens": total, "path": str(path), "sha256": file_sha256(path)})
        from cti_vla.training.formal_resume_acceptance import (run_formal_resume_acceptance,
            require_formal_resume_acceptance, verify_resume_journal)
        primary = next(c for c in configs if c["tokens_per_camera"] == 64)
        resume_windows = selected[:2]
        resume_events = args.output / "f03_calls.jsonl"
        engineering_attempt = engineering_checkpoints / (job_id + "_" + uuid.uuid4().hex[:12])
        resume_report = run_formal_resume_acceptance(config=primary,
            records=[provider.get(row["window_id"]) for row in resume_windows], windows=resume_windows,
            student=student, components=components, checkpoint_root=engineering_attempt,
            events_path=resume_events, job_id=job_id, source_files=sources,
            window_manifest_sha256=file_sha256(args.windows), input_acceptance_sha256=file_sha256(f00_path))
        resume_path = args.output / "resume_acceptance.json"
        atomic_json(resume_path, resume_report)
        require_formal_resume_acceptance(resume_report, config=primary, window_manifest_sha256=file_sha256(args.windows),
            input_acceptance_sha256=file_sha256(f00_path), source_files=sources, selected_windows=resume_windows,
            frozen_model_sha256=frozen)
        verify_resume_journal(resume_events, resume_report)
        unchanged()
        if before != verify_checkpoint_directory(args.checkpoint, asset):
            raise ValueError("formal base files changed during engineering gates")
        result = dict(schema=FORMAL_SCHEMA, status="passed", suite=args.suite, test_opened=False,
            input_acceptance_sha256=file_sha256(f00_path), operator_acceptances=reports,
            source_files=sources, frozen_model_sha256=frozen, checkpoint_unchanged=True,
            input_calls=input_calls, operator_probes=operator_calls, job_id=job_id,
            operator_calls_sha256=file_sha256(operators), wall_seconds=time.perf_counter() - started)
        result.update(resume_acceptance_sha256=file_sha256(resume_path), f03_calls_sha256=file_sha256(resume_events),
            resume_acceptance_passed=True)
        atomic_json(args.output / "acceptance_complete.json", result)
        return result
    except BaseException as exc:
        atomic_json(args.output / "failure.json", dict(schema=FORMAL_SCHEMA, status="failed",
            error=f"{type(exc).__name__}: {exc}", input_call_attempts=input_calls, operator_probe_attempts=operator_calls,
            job_id=job_id, wall_seconds=time.perf_counter() - started, test_opened=False,
            cost_scope="All attempts retained; reconcile entire Slurm allocation including load/backward/cache and failures."))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configs", type=Path, nargs=3, required=True)
    for name in ("protocol", "windows", "checkpoint", "asset-manifest", "data-directory", "oft-source", "cache-directory", "feature-cache", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--engineering-checkpoints", type=Path,
        help="Only the registered H/checkpoints/formal_main_v2/engineering/{suite} tree; defaults there")
    parser.add_argument("--suite", choices=("libero_spatial", "libero_object", "libero_goal", "libero_10"), required=True)
    parser.add_argument("--prepare-only", action="store_true")
    print(json.dumps(run(parser.parse_args()), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

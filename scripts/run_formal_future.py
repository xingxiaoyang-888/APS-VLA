"""Run one registered formal-main-v2 A/B pair on server Slurm, with resume.

The scientific plan remains5000 updates. Engineering segments may stop after
a registered500-step boundary or after a complete update at a wall limit.
Such segments emit a resumable progress report, never a deployment receipt.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _within(path, root):
    path, root = Path(path).resolve(), Path(root).resolve()
    if root not in path.parents:
        raise ValueError(f"runtime path must be strictly below {root}")
    return path


def run(args):
    invocation_started = time.perf_counter()
    if os.name == "nt" or not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("real formal VLA execution is server Slurm only")
    from cti_vla.training.formal_future import (
        atomic_json_save, file_sha256, formal_source_hashes, json_signature,
        parameter_fingerprint, train_formal_arm, validate_formal_training_config,
        configure_formal_training_numerics,
    )
    from cti_vla.training.formal_records import FormalRecordProvider, exclusive_file_lock
    from cti_vla.training.formal_resume_acceptance import require_formal_resume_acceptance, verify_resume_journal
    from cti_vla.data.formal_windows import load_formal_protocol, load_formal_windows
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation.formal_acceptance import (
        require_formal_acceptance, require_formal_input_acceptance, select_formal_acceptance_windows,
        verify_formal_operator_journal,
    )
    from cti_vla.evaluation.future_input_acceptance import verify_input_acceptance_journal
    from cti_vla.evaluation.formal_runtime import (
        make_formal_checkpoint_metadata, make_formal_deployment_receipt,
    )
    config = read_json(args.config)
    spec = validate_formal_training_config(config)
    if args.max_wall_seconds is not None and (not math.isfinite(args.max_wall_seconds) or args.max_wall_seconds <= 0):
        raise ValueError("--max-wall-seconds must be finite and positive")
    if args.stop_after_updates is not None and args.stop_after_updates not in spec.validation_updates[1:]:
        raise ValueError("--stop-after-updates must be500,1000,...,5000")
    project_root = Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
    capacity_root = Path("/share/home/u15016/XXY_CVPR/CTI-VLA")
    output = _within(args.output, project_root)
    feature_cache = _within(args.feature_cache, capacity_root / "data/formal_main_v2")
    checkpoints = _within(args.training_checkpoints, capacity_root / "checkpoints/formal_main_v2")
    cache_directory = _within(args.cache_directory, project_root)
    if ROOT == output or ROOT in output.parents or ROOT in feature_cache.parents or ROOT in checkpoints.parents:
        raise ValueError("formal outputs cannot be placed inside the immutable source snapshot")
    # Protocol assets and inherited splits live in the project, while ROOT is
    # the immutable executable snapshot (which does not vendor external/LIBERO).
    protocol = load_formal_protocol(args.protocol, project_root)
    manifest = load_formal_windows(args.windows, protocol)
    if manifest["suite"] != config["suite"] or protocol.payload["suite"] != config["suite"]:
        raise ValueError("formal suite and full data protocol differ")
    asset = load_checkpoint_manifest(args.asset_manifest)
    if asset.revision != config["model_revision"]:
        raise ValueError("formal base revision differs from registered pair")
    source = formal_source_hashes(ROOT)
    watched = {str(path.resolve()): file_sha256(path) for path in
               (args.config, args.protocol, args.windows, args.asset_manifest,
                args.input_acceptance_report, args.acceptance_report)}
    protocol_dependencies = [project_root / protocol.payload["dataset_asset"]]
    inherited = protocol.payload.get("inherited_protocol")
    if inherited:
        protocol_dependencies.append(project_root / inherited["path"])
    watched.update({str(path.resolve()): file_sha256(path) for path in protocol_dependencies})
    fixed_windows = select_formal_acceptance_windows(manifest, protocol)
    f00, f01 = read_json(args.input_acceptance_report), read_json(args.acceptance_report)
    require_formal_input_acceptance(f00, config=config, window_manifest_sha256=file_sha256(args.windows),
        data_protocol_sha256=file_sha256(args.protocol), asset_manifest_sha256=file_sha256(args.asset_manifest),
        source_files=source, selected_windows=fixed_windows)
    require_formal_acceptance(f01, config=config, window_manifest_sha256=file_sha256(args.windows),
        input_acceptance_sha256=file_sha256(args.input_acceptance_report), source_files=source,
        selected_windows=fixed_windows)
    input_journal = args.input_acceptance_report.parent / "input_calls.jsonl"
    operator_journal = args.acceptance_report.parent / "operator_calls.jsonl"
    verify_input_acceptance_journal(input_journal, f00)
    verify_formal_operator_journal(operator_journal, f01)
    watched.update({str(path.resolve()): file_sha256(path) for path in (input_journal, operator_journal)})
    if f00["frozen_model_sha256"] != f01["frozen_model_sha256"]:
        raise ValueError("formal input/operator gates used different frozen model bytes")
    resume_gate_path = args.acceptance_report.parent / "resume_acceptance.json"
    resume_journal_path = args.acceptance_report.parent / "f03_calls.jsonl"
    resume_gate = read_json(resume_gate_path)
    require_formal_resume_acceptance(resume_gate, config=config,
        window_manifest_sha256=file_sha256(args.windows),
        input_acceptance_sha256=file_sha256(args.input_acceptance_report), source_files=source,
        selected_windows=fixed_windows[:2], frozen_model_sha256=f01["frozen_model_sha256"])
    verify_resume_journal(resume_journal_path, resume_gate)
    watched.update({str(path.resolve()): file_sha256(path) for path in (resume_gate_path, resume_journal_path)})
    for folder in (cache_directory, cache_directory / "hub", cache_directory / "modules"):
        folder.mkdir(parents=True, exist_ok=True)
    os.environ.update(HF_HOME=str(cache_directory), HF_HUB_CACHE=str(cache_directory / "hub"),
        HF_MODULES_CACHE=str(cache_directory / "modules"), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    import torch
    configure_formal_training_numerics()
    from transformers import AutoProcessor
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
    from cti_vla_baselines.acl_matched import FrozenDifferentiableOFTPolicy
    from cti_vla.evaluation.libero_runtime import INPUTS_VERSION
    if torch.cuda.device_count() != 1:
        raise RuntimeError("formal training requires exactly one scheduler-assigned GPU")
    output.mkdir(parents=True, exist_ok=True)
    job_id = os.environ["SLURM_JOB_ID"]
    attempt = str(job_id) + "_" + uuid.uuid4().hex[:12]
    # One lock per pair blocks duplicate trainers, while other pairs may share
    # the bounded suite cache through its independent cross-process locks.
    with exclusive_file_lock(output / ".training.lock"):
        before = verify_checkpoint_directory(args.checkpoint, asset)
        components = load_openvla_oft_components(args.checkpoint, device="cuda:0", use_minimal_prismatic_compat=True)
        processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
        policy = OpenVLAOFTTokenPolicy(components.vla, components.action_head, components.proprio_projector, num_patches_full=512)
        student = FrozenDifferentiableOFTPolicy(policy, components.vla.projector, model_revision=asset.revision, input_version=INPUTS_VERSION)
        modules = {name: getattr(components, name) for name in ("vla", "action_head", "proprio_projector")}
        frozen_hash = parameter_fingerprint(modules)
        if frozen_hash != f01["frozen_model_sha256"]:
            raise ValueError("loaded formal model differs from the accepted parameter/buffer fingerprint")
        cache_identity = {"suite": config["suite"], "model_revision": asset.revision,
            "asset_manifest_sha256": file_sha256(args.asset_manifest), "data_protocol_sha256": file_sha256(args.protocol),
            "window_manifest_sha256": file_sha256(args.windows),
            "dataset_statistics_sha256": file_sha256(args.checkpoint / "dataset_statistics.json"),
            "producer_source_files": source}
        provider = FormalRecordProvider(protocol=protocol, manifest=manifest, data_directory=args.data_directory,
            components=components, processor=processor, policy=policy, stats_key=config["stats_key"],
            cache_root=feature_cache, cache_identity=cache_identity, events_path=output / "cache_events" / (attempt + ".jsonl"),
            max_cache_bytes=128 * 1024**3, ram_records=2, job_id=job_id)
        identity = {"window_manifest_sha256": file_sha256(args.windows),
            "data_protocol_sha256": file_sha256(args.protocol),
            "selection_protocol_sha256": json_signature(config["selection"]),
            "input_acceptance_sha256": file_sha256(args.input_acceptance_report),
            "f01_report_sha256": file_sha256(args.acceptance_report),
            "resume_acceptance_sha256": file_sha256(resume_gate_path), "resume_journal_sha256": file_sha256(resume_journal_path),
            "frozen_model_sha256": frozen_hash, "asset_manifest_sha256": file_sha256(args.asset_manifest),
            "training_source_files": source, "cache_identity": cache_identity,
            "training_order_version": "python-random-private-seeded-full-pool-shuffle-cycle-v1"}
        registered_path = output / "registered_config.json"
        if registered_path.exists() and read_json(registered_path) != config:
            raise ValueError("existing formal output belongs to another registered config")
        if not registered_path.exists():
            atomic_json_save(registered_path, config)
        results = {}
        for arm in (["A", "B"] if args.arm == "both" else [args.arm]):
            remaining_wall = (None if args.max_wall_seconds is None else
                              args.max_wall_seconds - (time.perf_counter() - invocation_started))
            if remaining_wall is not None and remaining_wall <= 0:
                break
            results[arm] = train_formal_arm(config=config, arm=arm, spec=spec, provider=provider, policy=policy,
                student=student, frozen_modules=modules, identity=identity, output=output / arm,
                checkpoints=checkpoints / arm, metadata_factory=make_formal_checkpoint_metadata,
                receipt_factory=make_formal_deployment_receipt, resume=args.resume, job_id=job_id,
                stop_after_updates=args.stop_after_updates, max_wall_seconds=remaining_wall,
                progress=lambda row: print(json.dumps(row, ensure_ascii=False), flush=True))
        for arm in ("A", "B"):
            if arm in results:
                continue
            complete_path, partial_path = output / arm / "training_report.json", output / arm / "progress_report.json"
            if complete_path.exists() or partial_path.exists():
                other = read_json(complete_path if complete_path.exists() else partial_path)
                if other.get("identity", {}).get("pair_config_sha256") != json_signature(config):
                    raise ValueError("other arm report belongs to another pair")
                results[arm] = other
            else:
                results[arm] = {"status": "not_started", "planned_updates": 5000}
        after = verify_checkpoint_directory(args.checkpoint, asset)
        if (before != after or source != formal_source_hashes(ROOT)
                or any(file_sha256(Path(path)) != digest for path, digest in watched.items())):
            raise RuntimeError("formal base/data/config/gates/source changed during execution")
        complete = all(results[arm]["status"] == "completed" for arm in ("A", "B"))
        report = {"schema": "formal_main_v2", "status": "completed" if complete else "checkpointed",
            "planned_updates_per_arm": 5000, "arms": results, "job_id": job_id,
            "requested_arms": ["A", "B"] if args.arm == "both" else [args.arm], "pair_complete": complete,
            "test_opened": False, "checkpoint_unchanged": True, "source_files": source}
        report_name = "training_summary.json" if complete else "training_progress.json"
        atomic_json_save(output / report_name, report)
        atomic_json_save(output / "finalizations" / (attempt + ".json"), {"status": "verified",
            "kind": "training" if complete else "engineering_segment", "checkpoint_unchanged": True,
            "checkpoint": asdict(after), "job_id": job_id, "result_status": report["status"],
            "result_sha256": file_sha256(output / report_name), "source_files": source})
        return report


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    for name in ("config", "windows", "protocol", "checkpoint", "asset-manifest", "data-directory",
                 "cache-directory", "feature-cache", "training-checkpoints", "output",
                 "input-acceptance-report", "acceptance-report"):
        result.add_argument("--" + name, type=Path, required=True)
    result.add_argument("--arm", choices=("A", "B", "both"), default="both")
    result.add_argument("--resume", action="store_true")
    result.add_argument("--stop-after-updates", type=int)
    result.add_argument("--max-wall-seconds", type=float)
    return result


def main():
    args = parser().parse_args()
    started = time.perf_counter()
    try:
        report = run(args)
        print(json.dumps({"status": report["status"], "arms": list(report["arms"])}), flush=True)
    except BaseException as error:
        from cti_vla.training.formal_future import atomic_json_save
        atomic_json_save(args.output / "failures" / (os.environ.get("SLURM_JOB_ID", "local") + "_" + uuid.uuid4().hex + ".json"),
            {"status": "failed", "error_type": type(error).__name__, "error": str(error),
             "seconds": time.perf_counter() - started, "utc": datetime.now(timezone.utc).isoformat()})
        raise


if __name__ == "__main__":
    main()

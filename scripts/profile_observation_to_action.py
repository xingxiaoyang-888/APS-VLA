"""G5 full raw-observation profiling; never creates or chooses final inputs."""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from dataclasses import asdict
import gc
import json
import os
from pathlib import Path
import time

import torch

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation import libero_runtime
from cti_vla.evaluation.profiling import (PROFILING_VERSION, ProfileConfig, ProfileJournal, ProfileMethod,
    TorchClock, hardware_telemetry, load_raw_panel, profile_methods, read_profile_cost, summarize_latencies, verify_measurement_journal)
from cti_vla.evaluation.teacher_diagnostics import atomic_json, require_g0
from cti_vla.models.abstraction.packing import PACKING_VERSION

ROOT = Path(__file__).resolve().parents[1]


class MatchedBaseline:
    """Dense/uniform use the same lightweight frozen policy as the selector."""
    def __init__(self, components, processor, *, stats_key, method):
        from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
        if method not in ("dense", "uniform128"):
            raise ValueError("profiling baseline must be dense or uniform128")
        self.components, self.processor, self.stats_key, self.method = components, processor, stats_key, method
        self.device = next(components.vla.parameters()).device
        self.dtype = next(components.vla.parameters()).dtype
        self.stage_context = lambda _: nullcontext()
        self.token_policy = OpenVLAOFTTokenPolicy(components.vla, components.action_head, components.proprio_projector, num_patches_full=512)

    @torch.no_grad()
    def __call__(self, observation, instruction):
        vla = self.components.vla
        with self.stage_context("preprocess"):
            inputs = libero_runtime.prepare_observation_inputs(observation, instruction, self.processor,
                vla.norm_stats[self.stats_key]["proprio"], device=self.device, dtype=self.dtype)
        with self.stage_context("vision"):
            visual = vla._process_vision_features(inputs["pixel_values"], None, False)
        with self.stage_context("condition_selection"):
            # Regenerate even the fixed baseline's indices inside the pipeline.
            indices = torch.as_tensor(libero_runtime.uniform128_indices(), device=self.device)[None] if self.method == "uniform128" else None
        with self.stage_context("policy"):
            normalized = self.token_policy.forward_from_full_tokens(visual, inputs["normalized_proprio"],
                input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"], retained_indices=indices)
        with self.stage_context("postprocess"):
            normalized = normalized.float().cpu().numpy()[0]
            physical = vla._unnormalize_actions(normalized, self.stats_key)
            actions = libero_runtime.postprocess_actions(physical)
            return libero_runtime.PolicyChunk(normalized, actions, {
                "method": self.method, "policy_calls": 1, "vision_calls": 1,
                "visual_tokens": 512 if self.method == "dense" else 128, "language_cache": "disabled",
                "inputs_version": libero_runtime.INPUTS_VERSION, "action_version": libero_runtime.ACTION_VERSION,
                "packing_version": PACKING_VERSION})


def method_specs(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    values = payload["methods"]
    if payload["schema_version"] != 1 or not values or len({row["name"] for row in values}) != len(values):
        raise ValueError("method names must be distinct in a schema1 methods manifest")
    if [row["kind"] for row in values if row["name"] == "dense"] != ["dense"] or sum(row["kind"] == "dense" for row in values) != 1:
        raise ValueError("exactly one matched baseline named dense is required")
    for row in values:
        if row["kind"] not in ("dense", "uniform128", "selector"):
            raise ValueError("supported profiling adapters are dense, uniform128 and trained selector")
        if row["kind"] == "selector" and row["target_tokens"] not in (256, 128, 64):
            raise ValueError("selector profiling uses fixed 256/128/64 budgets")
        if row["kind"] == "selector":
            for path_key, digest_key in (("checkpoint", "checkpoint_sha256"), ("training_report", "training_report_sha256")):
                expected = row.get(digest_key)
                if not isinstance(expected, str) or len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected) or file_sha256(Path(row[path_key])) != expected:
                    raise ValueError("selector profiling spec must pin actual checkpoint/report bytes")
            report = json.loads(Path(row["training_report"]).read_text(encoding="utf-8"))
            if report.get("best_checkpoint_sha256") != row["checkpoint_sha256"]:
                raise ValueError("frozen method checkpoint differs from its pinned G3 best")
    return values


def run(args):
    from cti_vla.data.experiment_protocol import load_experiment_protocol, write_frozen_json
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation.selector_runtime import (SelectorRolloutPolicy, deployment_source_hashes,
                                                   load_selector_checkpoint, selector_expected_versions,
                                                   validate_selector_training_coverage)
    specs = method_specs(args.methods)
    expected_freeze = None
    if args.formal:
        if args.g0_report is None:
            raise ValueError("formal panel access requires the approved G0 report")
        asset = load_checkpoint_manifest(args.asset_manifest)
        g0 = json.loads(args.g0_report.read_text(encoding="utf-8"))
        require_g0(g0, model_revision=asset.revision, input_version=libero_runtime.INPUTS_VERSION, packing_version=PACKING_VERSION)
        expected_freeze = {"model_revision": asset.revision, "input_version": libero_runtime.INPUTS_VERSION,
            "packing_version": PACKING_VERSION, "action_version": libero_runtime.ACTION_VERSION, "stats_key": args.stats_key,
            "g0_report_sha256": file_sha256(args.g0_report), "runtime_sha256": file_sha256(libero_runtime.__file__),
            "asset_manifest_sha256": file_sha256(args.asset_manifest), "protocol_manifest_sha256": file_sha256(args.protocol)}
        if g0["provenance"].get("runtime_sha256") != expected_freeze["runtime_sha256"] or g0["provenance"].get("checkpoint_manifest_sha256") != expected_freeze["asset_manifest_sha256"]:
            raise ValueError("formal panel access requires G0 matching current runtime/checkpoint evidence")
    samples, panel = load_raw_panel(args.panel, formal=args.formal, freeze_receipt=args.freeze_receipt,
                                   methods_sha256=file_sha256(args.methods), expected_freeze=expected_freeze)
    config = ProfileConfig(order_seed=args.order_seed)
    if args.prepare_only:
        return {"status": "prepared_only", "gpu_queries": 0, "panel": panel, "methods": specs,
                "unique_raw_observations": len(samples), "config": asdict(config),
                "planned_full_pipeline_calls": len(specs) * (50 + len(samples) * 2 * (5 + 1))}
    if os.name == "nt" or not os.environ.get("SLURM_JOB_ID") or not args.uncontended_gpu:
        raise RuntimeError("real profiling requires a server Slurm allocation and explicit uncontended-GPU attestation")
    if any(value is None for value in (args.checkpoint, args.cache_directory, args.output, args.g0_report)):
        raise ValueError("execution requires checkpoint, external HF cache, output and passed G0 report")
    if args.output.exists():
        raise FileExistsError("timing runs use a new output directory; preserve failed/earlier runs")
    project_root = args.project_root.resolve()
    if project_root not in args.output.resolve().parents or (project_root != ROOT.resolve() and ROOT.resolve() in args.output.resolve().parents):
        raise ValueError("profiling results must stay inside the project and outside the immutable source snapshot")
    checkpoint = args.checkpoint.resolve()
    for target in (args.output.resolve(), args.cache_directory.resolve()):
        if target == checkpoint or checkpoint in target.parents:
            raise ValueError("profiling/cache output must stay outside immutable base checkpoint")
    asset = load_checkpoint_manifest(args.asset_manifest)
    if panel["model_revision"] != asset.revision:
        raise ValueError("dense panel was collected with another model revision")
    g0 = json.loads(args.g0_report.read_text(encoding="utf-8"))
    require_g0(g0, model_revision=asset.revision, input_version=libero_runtime.INPUTS_VERSION, packing_version=PACKING_VERSION)
    if g0["provenance"]["runtime_sha256"] != file_sha256(libero_runtime.__file__) or g0["provenance"]["checkpoint_manifest_sha256"] != file_sha256(args.asset_manifest):
        raise ValueError("profiling input/checkpoint code differs from G0")
    protocol = load_experiment_protocol(args.protocol)
    if torch.cuda.device_count() != 1:
        raise RuntimeError("profiling requires exactly one allocated visible GPU")
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    torch.manual_seed(args.order_seed)
    for directory in (args.cache_directory, args.cache_directory / "hub", args.cache_directory / "modules"):
        directory.mkdir(parents=True, exist_ok=True)
    os.environ.update(HF_HOME=str(args.cache_directory), HF_HUB_CACHE=str(args.cache_directory / "hub"),
                      HF_MODULES_CACHE=str(args.cache_directory / "modules"), HF_HUB_OFFLINE="1",
                      TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    from transformers import AutoProcessor
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    before = verify_checkpoint_directory(checkpoint, asset)
    loading_started = time.perf_counter()
    components = load_openvla_oft_components(checkpoint, device=device, use_minimal_prismatic_compat=True)
    processor = AutoProcessor.from_pretrained(checkpoint, trust_remote_code=True, local_files_only=True)
    if args.stats_key not in components.vla.norm_stats:
        raise ValueError("unknown model normalization stats key")
    torch.cuda.synchronize(device)
    model_loading_seconds = time.perf_counter() - loading_started
    checkpoint_hashes = {}
    factories = {}
    expected_versions = selector_expected_versions(asset.revision, protocol, args.stats_key)
    source_hashes = deployment_source_hashes(ROOT)
    for spec in specs:
        if spec["kind"] == "selector":
            path = Path(spec["checkpoint"])
            report_path = Path(spec["training_report"])
            if file_sha256(path) != spec["checkpoint_sha256"] or file_sha256(report_path) != spec["training_report_sha256"]:
                raise ValueError("selector/report changed after frozen method preflight")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            checkpoint_hashes[str(path)] = spec["checkpoint_sha256"]
            checkpoint_hashes[str(report_path)] = spec["training_report_sha256"]
        else:
            path, report = None, None

        def factory(spec=spec, path=path, report=report):
            # One scorer resident at a time; no prior method's live tensors are
            # included in allocated memory. Reserved allocator memory is shown.
            gc.collect()
            if spec["kind"] == "selector":
                if file_sha256(path) != spec["checkpoint_sha256"] or file_sha256(Path(spec["training_report"])) != spec["training_report_sha256"]:
                    raise ValueError("selector/report changed before a frozen method block")
                loaded = load_selector_checkpoint(path, report, expected_versions=expected_versions,
                                                   expected_source_hashes=source_hashes, device=device)
                if args.formal:
                    validate_selector_training_coverage(loaded, report, protocol)
                policy = SelectorRolloutPolicy(components, processor, loaded, stats_key=args.stats_key,
                                                target_tokens=spec["target_tokens"], record_selection=False)
                provenance = dict(loaded.provenance)
            else:
                policy = MatchedBaseline(components, processor, stats_key=args.stats_key, method=spec["kind"])
                provenance = {}
            return ProfileMethod(policy, {"spec": spec, "provenance": provenance, "instruction_cache_enabled": False,
                "cache_scope": "none", "instruction_modes_note": "Both cold/hot recompute language; no language cache is implemented.",
                "precision": "base_bfloat16_selector_float32", "attention": "sdpa", "batch_size": 1},
                lambda context: setattr(policy, "stage_context", context or (lambda _: nullcontext())))
        factories[spec["name"]] = factory
    args.output.mkdir(parents=True)
    identity = {"profiling_version": PROFILING_VERSION, "panel": panel, "methods": specs, "config": asdict(config),
                "methods_sha256": file_sha256(args.methods), "asset_manifest_sha256": file_sha256(args.asset_manifest),
                "g0_report_sha256": file_sha256(args.g0_report), "protocol_manifest_sha256": file_sha256(args.protocol),
                "model_revision": asset.revision, "input_version": libero_runtime.INPUTS_VERSION,
                "action_version": libero_runtime.ACTION_VERSION, "packing_version": PACKING_VERSION,
                "stats_key": args.stats_key, "checkpoint_hashes": checkpoint_hashes,
                "source_files": {p.relative_to(ROOT).as_posix(): file_sha256(p) for p in [*sorted((ROOT / "src/cti_vla").rglob("*.py")), Path(__file__)]},
                "hardware": hardware_telemetry(), "uncontended_gpu_attested": args.uncontended_gpu,
                "project_root": str(project_root), "source_root": str(ROOT.resolve()),
                "model_loading_seconds_excluded": model_loading_seconds, "compile": "disabled; native eager SDPA"}
    write_frozen_json(args.output / "config.json", identity)
    journal_path = args.output / "calls.jsonl"
    journal = ProfileJournal(journal_path, identity)
    began, cpu_began = time.perf_counter(), time.process_time()
    try:
        measured = profile_methods(samples, factories, config=config, clock=TorchClock(device), emit=journal, telemetry=hardware_telemetry)
        after = verify_checkpoint_directory(checkpoint, asset)
        if after != before or any(file_sha256(Path(path)) != sha for path, sha in checkpoint_hashes.items()):
            raise RuntimeError("base/selector checkpoint or training report changed during profiling")
        measured.update(provenance=identity, checkpoint_unchanged=True, cost=read_profile_cost(journal_path),
                        wall_seconds_including_measurement_overhead=time.perf_counter() - began,
                        cpu_seconds=time.process_time() - cpu_began)
        verify_measurement_journal(measured, journal_path)
        atomic_json(args.output / "measurements.json", measured)
        summary = summarize_latencies(measured)
        summary.update(measurements_sha256=file_sha256(args.output / "measurements.json"),
                       journal_sha256=file_sha256(journal_path), checkpoint_unchanged=True, cost=measured["cost"], panel=panel)
        atomic_json(args.output / "summary.json", summary)
        return {"status": summary["status"], "observations": len(samples), "methods": len(specs), "cost": measured["cost"]}
    except BaseException as exc:
        try:
            cost = read_profile_cost(journal_path)
        except Exception as cost_error:
            cost = {"unavailable": str(cost_error), "charged_work_must_not_be_assumed_zero": True}
        atomic_json(args.output / "summary.json", {"status": "failed", "checkpoint_unchanged": None, "cost": cost,
            "error": f"{type(exc).__name__}: {exc}", "wall_seconds_including_measurement_overhead": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu_began})
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--methods", type=Path, required=True)
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--freeze-receipt", type=Path)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--uncontended-gpu", action="store_true")
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--cache-directory", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--project-root", type=Path, default=ROOT, help="Writable project root when running from an immutable source snapshot")
    parser.add_argument("--g0-report", type=Path)
    parser.add_argument("--asset-manifest", type=Path, default=ROOT / "configs/assets/openvla_oft_libero_spatial.json")
    parser.add_argument("--protocol", type=Path, default=ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")
    parser.add_argument("--stats-key", default="libero_spatial_no_noops")
    parser.add_argument("--order-seed", type=int, default=1017)
    print(json.dumps(run(parser.parse_args()), ensure_ascii=False), flush=True)

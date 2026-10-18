"""Optional preregistered three-observation smaller-step teacher diagnostic.

This creates an independent run. Formal execution requires a reviewed no-go
activation receipt bound to complete G1, its D4 analysis and this registration.
It never decides scientific go, submits jobs, or changes the main G1 result.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
from functools import lru_cache
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import random
import time

ROOT = Path(__file__).resolve().parents[1]
VERSION = "g1-optional-preregistered-small-step-v1"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_paths(project_root, output, *, source_root=ROOT, cache=None, checkpoint=None, main=None):
    """Source may be an immutable snapshot within the writable project root."""
    project_root, source_root, output = (Path(p).resolve() for p in (project_root, source_root, output))
    within = lambda candidate, parent: candidate == parent or parent in candidate.parents
    if not within(source_root, project_root):
        raise ValueError("source snapshot must belong to the declared project root")
    for target in (output, *([Path(cache).resolve()] if cache is not None else [])):
        if not within(target, project_root) or target == project_root:
            raise ValueError("outputs/runtime cache must be a child directory of this project")
        if source_root != project_root and within(target, source_root):
            raise ValueError("outputs/runtime cache must not modify the source snapshot")
        if checkpoint is not None and within(target, Path(checkpoint).resolve()):
            raise ValueError("optional artifacts/runtime cache must be outside immutable weights")
        if main is not None and (within(target, Path(main).resolve()) or within(Path(main).resolve(), target)):
            raise ValueError("optional output/cache must be separate from the immutable original G1 directory")


@lru_cache(maxsize=1)
def d4_helpers():
    spec = importlib.util.spec_from_file_location("cti_readonly_d4_helpers", ROOT / "scripts/analyze_g1_d4.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_registration(path, protocol):
    from cti_vla.data.identity import file_sha256
    from cti_vla.data.libero import load_manifest
    from cti_vla.evaluation.teacher_diagnostics import json_signature
    registration = read_json(path)
    unsigned = dict(registration)
    signature = unsigned.pop("content_signature", None)
    if signature != "sha256:" + json_signature(unsigned):
        raise ValueError("optional diagnostic registration signature mismatch")
    parent = ROOT / registration["parent_panel"]
    if file_sha256(parent) != registration["parent_sha256"] or registration["parent_sha256"] != protocol.payload["panels"]["teacher_12"]["sha256"]:
        raise ValueError("optional diagnostic parent is not the frozen teacher12 panel")
    teacher = load_manifest(parent)
    episodes = {e.episode_id: e for e in teacher.episodes}
    chosen = random.Random(717).sample(sorted(episodes), 3)
    expected = []
    for episode_id, stage in zip(chosen, ("early", "middle", "late")):
        sample = next(s for s in teacher.samples if s.episode_id == episode_id and s.stage == stage)
        episode, registered = protocol.require_sample(episode_id, sample.step_index, split="train")
        if sample != registered:
            raise ValueError("optional sample differs from authoritative train observation")
        expected.append({**asdict(sample), "task_name": episode.task_name,
                         "source_shard": episode.source_shard, "record_index": episode.record_index})
    if registration["samples"] != expected or registration["seed"] != 717 or registration["comparison_seed"] != 517:
        raise ValueError("optional samples/seeds differ from the preregistered membership-only rule")
    if registration["main_total_token_schedule"] != [512, 256, 128, 64] or registration["followup_total_token_schedule"] != [512, 384, 256, 192, 128, 96, 64] or registration["followup_per_camera_budgets"] != [192, 128, 96, 64, 48, 32]:
        raise ValueError("optional schedules cannot change after registration")
    if registration["methods"] != ["teacher_staged", "full_loo_static", "uniform", "random_seed_17", "random_seed_23", "random_seed_41"]:
        raise ValueError("optional controls differ from the registered methods")
    bound = 1 + sum(registration["followup_total_token_schedule"][:-1]) + 6 + 30 - 1
    if bound != 1604 or registration["cost_bound"]["fresh_unique_query_upper_bound_per_observation"] != bound or registration["cost_bound"]["attempt_cap_per_observation"] != 2000:
        raise ValueError("optional query budget differs from frozen1604/2000 bounds")
    return registration


def require_activation(path, *, registration_sha, evidence, analysis_sha):
    receipt = read_json(path)
    required = {"schema_version": 1, "decision": "activate_optional_step_diagnostic",
                "main_g1_scientific_decision": "no_go", "registration_sha256": registration_sha,
                "g1_config_sha256": evidence["config_sha256"],
                "g1_finalization_sha256": evidence["finalization_sha256"], "d4_summary_sha256": analysis_sha}
    if any(receipt.get(key) != value for key, value in required.items()) or not receipt.get("reviewed_by") or not receipt.get("reviewed_utc") or not str(receipt.get("review_notes", "")).strip():
        raise ValueError("formal optional diagnostic requires a reviewed no-go activation bound to G1/D4/registration")
    return receipt


def verify_main_implementation(main_config):
    from cti_vla.data.identity import file_sha256
    critical_sources = [*sorted((ROOT / "src/cti_vla/models").rglob("*.py")),
                        ROOT / "src/cti_vla/data/sequence_example.py", ROOT / "src/cti_vla/evaluation/libero_runtime.py",
                        ROOT / "src/cti_vla/evaluation/teacher_diagnostics.py", ROOT / "src/cti_vla/labeling/sampling.py"]
    if any(main_config.get("source_snapshot", {}).get(path.relative_to(ROOT).as_posix()) != file_sha256(path) for path in critical_sources):
        raise ValueError("policy, packing, input or data implementation differs from original G1")


def validate_main_inputs(args, protocol, registration):
    from cti_vla.data.identity import file_sha256
    from cti_vla.evaluation.teacher_diagnostics import run_exact_selection
    helper = d4_helpers()
    main_config, all_rows, evidence = helper.verify_panel(args.g1_directory, protocol)
    if main_config.get("set_seed") != 517 or main_config.get("random_seeds") != [17, 23, 41] or not math.isfinite(main_config["noise_tolerance"]) or main_config["noise_tolerance"] < 0:
        raise ValueError("main G1 seed/controls/noise tolerance differs from the registered comparison")
    verify_main_implementation(main_config)
    analysis = read_json(args.analysis_summary)
    if analysis.get("status") != "completed_offline_analysis" or analysis.get("source_evidence") != evidence or analysis.get("coverage", {}).get("diagnostic_observations") != 90 or analysis.get("coverage", {}).get("teacher_observations") != 12:
        raise ValueError("optional diagnosis requires complete D4 analysis of this exact finalized G1")
    activation = require_activation(args.activation_receipt, registration_sha=file_sha256(args.registration),
                                    evidence=evidence, analysis_sha=file_sha256(args.analysis_summary))
    by_id = {r["sample_id"]: r for r in all_rows}
    observations, originals, main_identities, full_actions = [], {}, {}, {}
    for selected in registration["samples"]:
        row = by_id[selected["sample_id"]]
        if not row["exact_selection"] or any(row.get(key) != value for key, value in selected.items()):
            raise ValueError("registered optional observation is absent from main teacher12")
        original = read_json(args.g1_directory / "observations" / f"{row['sample_id']}.json")
        if original.get("status") != "completed" or original.get("observation") != row or original.get("config_sha256") != evidence["config_sha256"]:
            raise ValueError("main exact observation is incomplete or misidentified")
        replay = helper.JournalActions(args.g1_directory / "queries" / f"{row['sample_id']}.jsonl",
                                      config_sha=evidence["config_sha256"], observation=row)
        recomputed = run_exact_selection(replay, sample_id=row["sample_id"], seed=registration["comparison_seed"])
        helper.assert_same(original["exact_selection"], recomputed, path="main_exact_recomputation")
        observations.append(row)
        originals[str(row["sample_id"])] = recomputed
        main_identities[str(row["sample_id"])] = replay.identity
        full_actions[str(row["sample_id"])] = replay.query(replay.full_indices, category="full_reference").tolist()
    return main_config, observations, originals, main_identities, full_actions, evidence, activation


def reference_difference(full, config, sample_id):
    """The frozen reference is copied from the verified original action journal."""
    import torch
    original = torch.tensor(config["main_full_actions"][str(sample_id)], dtype=torch.float32)
    if original.shape != (1, 8, 7) or not torch.isfinite(original).all() or full.shape != original.shape or not torch.isfinite(full).all():
        raise ValueError("invalid original/optional full teacher action")
    difference = float((full.cpu().float() - original).abs().max())
    if difference > config["reference_atol"]:
        raise ValueError("optional full teacher action differs beyond original G1 noise tolerance")
    return difference


def result_comparison(main, followup):
    rows = []
    for method, original_rows in main["methods"].items():
        subsequent = {r["keep_count"]: r for r in followup["methods"][method]}
        for original in original_rows:
            smaller = subsequent[original["keep_count"]]
            rows.append({"method": method, "keep_count": original["keep_count"],
                         "main_error": original["error"], "followup_error": smaller["error"],
                         "followup_minus_main_mean_l1": smaller["error"]["mean_l1"] - original["error"]["mean_l1"],
                         "main_retained_indices": original["retained_indices"],
                         "followup_retained_indices": smaller["retained_indices"]})
    return rows


def output_hashes(output, observations, folder, suffix):
    from cti_vla.data.identity import file_sha256
    return {str(row["sample_id"]): file_sha256(output / folder / f"{row['sample_id']}{suffix}")
            for row in observations if (output / folder / f"{row['sample_id']}{suffix}").exists()}


def summarize(output, config, observations, originals):
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature, read_query_journal_ledger, run_exact_selection
    output = Path(output)
    config_sha = json_signature(config)
    expected_ids = {str(row["sample_id"]) for row in observations}
    for directory, suffix in (("observations", "*.json"), ("queries", "*.jsonl")):
        if {path.stem for path in (output / directory).glob(suffix)} - expected_ids:
            raise ValueError("optional run contains an unregistered observation or query journal")
    complete, failed, costs = [], [], []
    for row in observations:
        path = output / "observations" / f"{row['sample_id']}.json"
        journal = output / "queries" / f"{row['sample_id']}.jsonl"
        if journal.exists():
            ledger = read_query_journal_ledger(journal, expected_fields={"config_sha256": config_sha, "sample": row})
            if ledger["sample_forwards_attempted"] > 2000 or ledger["unique_cached_actions"] > 1604:
                raise ValueError("optional journal exceeds its registered unique/attempt budget")
            costs.append(ledger)
        if not path.exists():
            continue
        result = read_json(path)
        if result.get("config_sha256") != config_sha or result.get("observation") != row:
            raise ValueError("optional observation identity/config mismatch")
        if result["status"] != "completed":
            failed.append(result)
            continue
        if not journal.exists():
            raise ValueError("completed optional result lacks its authoritative queries")
        replay = d4_helpers().JournalActions(journal, config_sha=config_sha, observation=row)
        expected_identity = config["main_input_identities"][str(row["sample_id"])]
        for key in ("input_sha256", "visual_sha256", "sequence_overhead_tokens", "num_cameras", "action_shape", "diagnostics_version"):
            if replay.identity.get(key) != expected_identity.get(key):
                raise ValueError("optional journal input features differ from main G1")
        difference = reference_difference(replay.query(replay.full_indices, category="full_reference"), config, row["sample_id"])
        d4_helpers().assert_same(result["full_reference_max_abs_difference"], difference, path="full_reference_comparison")
        recomputed = run_exact_selection(replay, sample_id=row["sample_id"], seed=517,
                                         per_camera_budgets=tuple(config["followup_per_camera_budgets"]))
        d4_helpers().assert_same(result["exact_selection"], recomputed, path="optional_recomputed")
        d4_helpers().assert_same(result["main_schedule_exact"], originals[str(row["sample_id"])], path="frozen_main_comparison")
        d4_helpers().assert_same(result["comparison"], result_comparison(originals[str(row["sample_id"])], recomputed), path="paired_comparison")
        complete.append(result)
    keys = ("api_calls_attempted", "sample_forwards_attempted", "sample_forwards_completed", "unique_cached_actions", "cache_hits", "failed_calls", "interrupted_calls_unknown_completion", "known_policy_seconds", "journal_bytes")
    cost = {key: sum(item[key] for item in costs) for key in keys}
    cost["policy_seconds_total"] = None if cost["interrupted_calls_unknown_completion"] else cost["known_policy_seconds"]
    cost["by_visual_length"] = {}
    for item in costs:
        for length, values in item["by_visual_length"].items():
            merged = cost["by_visual_length"].setdefault(length, {key: 0 for key in values})
            for key, value in values.items():
                merged[key] += value
    for folder in ("attempts", "observation_attempts"):
        attempts = [read_json(path) for path in sorted((output / folder).glob("*.json"))]
        if any(a.get("config_sha256") != config_sha for a in attempts):
            raise ValueError("optional cost receipt belongs to another config")
        cost[folder] = {"count": len(attempts), "unfinalized": sum(a.get("status") == "running" for a in attempts)}
        for name in ("wall_seconds", "cpu_seconds", "preflight_seconds", "preprocessing_seconds", "vision_seconds", "checkpoint_verification_seconds", "model_loading_seconds"):
            cost[folder][f"recorded_{name}_lower_bound"] = sum(a.get(name, 0.) for a in attempts)
        for name in ("wall_seconds", "cpu_seconds"):
            cost[folder][name + "_total"] = None if cost[folder]["unfinalized"] else cost[folder]["recorded_" + name + "_lower_bound"]
    cost["scope"] = "Run attempts include Python run-entry preflight, model load, checkpoint verification, decoding and all observation work until the final cost receipt; final summary serialization is excluded. Observation/policy fields are nested breakdowns and must not be added again. Unfinalized attempts require scheduler reconciliation; unknown cost remains null. Not deployment latency."
    finalized = False
    if (output / "finalization.json").exists():
        receipt = read_json(output / "finalization.json")
        finalized = (receipt.get("status") == "verified" and receipt.get("config_sha256") == config_sha and receipt.get("checkpoint_unchanged") is True
                     and receipt.get("checkpoint_verification") == config["expected_checkpoint_verification"]
                     and receipt.get("observation_files") == output_hashes(output, observations, "observations", ".json")
                     and receipt.get("query_journals") == output_hashes(output, observations, "queries", ".jsonl"))
        if not finalized:
            raise ValueError("optional finalization no longer matches checkpoint or query/result hashes")
    all_complete = len(complete) == len(observations)
    result = {"stage": "G1_optional_step_diagnostic", "version": VERSION,
              "status": "completed" if all_complete and finalized else "awaiting_final_verification" if all_complete else "partial",
              "config_sha256": config_sha, "expected_observations": 3, "completed_observations": len(complete),
              "failed_observations": len(failed), "cost": cost,
              "paired_results": [{"observation": row["observation"], "comparison": row["comparison"]} for row in complete],
              "go_no_go": "not_decided_no_automatic_G2_activation",
              "limitations": "Three preregistered observations across three episodes/tasks/phases. Original main G1 remains primary; no general improvement, closed-loop or speed claim. All failures and additional attempted work retained."}
    atomic_json(output / "summary.json", result)
    return result


def finalize(output, config, observations, verification):
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
    if asdict(verification) != config["expected_checkpoint_verification"]:
        raise ValueError("final optional checkpoint verification differs from frozen asset")
    for row in observations:
        result = read_json(output / "observations" / f"{row['sample_id']}.json")
        if result.get("status") != "completed" or result.get("config_sha256") != json_signature(config) or not (output / "queries" / f"{row['sample_id']}.jsonl").exists():
            raise ValueError("cannot finalize incomplete optional observations or missing journals")
    atomic_json(output / "finalization.json", {"status": "verified", "config_sha256": json_signature(config),
                "checkpoint_unchanged": True, "checkpoint_verification": asdict(verification),
                "observation_files": output_hashes(output, observations, "observations", ".json"),
                "query_journals": output_hashes(output, observations, "queries", ".jsonl"),
                "created_utc": datetime.now(timezone.utc).isoformat()})


def run(args):
    started, cpu_started = time.perf_counter(), time.process_time()
    import cti_vla
    if Path(cti_vla.__file__).resolve().parent != ROOT / "src/cti_vla":
        raise ValueError("cti_vla imports must come from this source snapshot; set PYTHONPATH to its src directory")
    from cti_vla.data.experiment_protocol import load_experiment_protocol, write_frozen_json
    from cti_vla.data.identity import file_sha256
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
    protocol = load_experiment_protocol(args.protocol)
    registration = load_registration(args.registration, protocol)
    output = args.output_directory.resolve()
    validate_paths(args.project_root, output)
    if args.prepare_only:
        output.mkdir(parents=True, exist_ok=True)
        result = {"status": "prepared_only_not_activated", "gpu_calls": 0,
                  "registration_sha256": file_sha256(args.registration), "samples": registration["samples"],
                  "cost_bound": registration["cost_bound"], "followup_per_camera_budgets": registration["followup_per_camera_budgets"]}
        atomic_json(output / "preflight_summary.json", result)
        return result
    if any(getattr(args, key) is None for key in ("g1_directory", "analysis_summary", "activation_receipt", "checkpoint", "data_directory", "cache_directory")):
        raise ValueError("formal optional diagnostic requires complete G1, D4, activation receipt, checkpoint, data and runtime cache")
    if os.name == "nt":
        raise RuntimeError("formal optional teacher calls and weights are server-only")
    validate_paths(args.project_root, output, cache=args.cache_directory, checkpoint=args.checkpoint, main=args.g1_directory)
    main_config, observations, originals, identities, full_actions, evidence, activation = validate_main_inputs(args, protocol, registration)
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation.libero_runtime import INPUTS_VERSION
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    asset = load_checkpoint_manifest(args.asset_manifest)
    if main_config["model_revision"] != asset.revision or main_config["asset_manifest_sha256"] != file_sha256(args.asset_manifest) or main_config["input_version"] != INPUTS_VERSION or main_config["packing_version"] != PACKING_VERSION:
        raise ValueError("optional policy model/input/packing differs from original G1")
    stats = read_json(args.checkpoint / "dataset_statistics.json")
    requested_stats = main_config.get("stats_key")
    matching = [key for key in stats if "libero_spatial" in key]
    stats_key = requested_stats or (matching[0] if len(matching) == 1 else None)
    if stats_key not in stats:
        raise ValueError("cannot resolve the same original Spatial normalization key")
    sources = [*sorted((ROOT / "src/cti_vla").rglob("*.py")), Path(__file__), ROOT / "scripts/analyze_g1_d4.py"]
    config = {"schema_version": 1, "version": VERSION, "registration_sha256": file_sha256(args.registration),
              "activation_receipt_sha256": file_sha256(args.activation_receipt), "activation": activation,
              "analysis_summary_sha256": file_sha256(args.analysis_summary), "main_evidence": evidence,
              "model_revision": asset.revision, "input_version": INPUTS_VERSION, "packing_version": PACKING_VERSION,
              "stats_key": stats_key, "protocol_signature": protocol.payload["content_signature"],
              "followup_per_camera_budgets": registration["followup_per_camera_budgets"], "comparison_seed": 517,
              "unique_query_upper_bound": 1604, "attempt_cap_per_observation": 2000,
              "reference_atol": main_config["noise_tolerance"], "main_input_identities": identities, "main_full_actions": full_actions,
              "expected_checkpoint_verification": {"repository": asset.repository, "revision": asset.revision,
                                                    "file_count": len(asset.files), "total_bytes": asset.total_bytes},
              "source_files": {path.relative_to(ROOT).as_posix(): file_sha256(path) for path in sources}}
    output.mkdir(parents=True, exist_ok=True)
    write_frozen_json(output / "config.json", config)
    write_frozen_json(output / "observation_panel.json", {"observations": observations, "registration_sha256": config["registration_sha256"]})
    config_sha = json_signature(config)
    summarize(output, config, observations, originals)
    pending = [row for row in observations if not (output / "observations" / f"{row['sample_id']}.json").exists()
               or read_json(output / "observations" / f"{row['sample_id']}.json").get("status") != "completed"]
    if args.observation_limit is not None:
        pending = pending[:args.observation_limit]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    attempt_path = output / "attempts" / f"{timestamp}.json"
    attempt = {"status": "running", "config_sha256": config_sha, "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
               "created_utc": datetime.now(timezone.utc).isoformat(), "requested_observations": len(pending),
               "preflight_seconds": time.perf_counter() - started,
               "runtime": {"python": platform.python_version()}, "cpu_count": os.cpu_count()}
    atomic_json(attempt_path, attempt)
    try:
        check_started = time.perf_counter()
        before = verify_checkpoint_directory(args.checkpoint, asset)
        attempt["checkpoint_verification_seconds"] = time.perf_counter() - check_started
        atomic_json(attempt_path, attempt)
        if pending:
            _run_pending(args, config, pending, originals, output, attempt, attempt_path)
        check_started = time.perf_counter()
        after = verify_checkpoint_directory(args.checkpoint, asset)
        attempt["checkpoint_verification_seconds"] += time.perf_counter() - check_started
        if before != after:
            raise RuntimeError("immutable checkpoint changed during optional diagnostic")
        interim = summarize(output, config, observations, originals)
        if interim["completed_observations"] == 3:
            finalize(output, config, observations, after)
        attempt["status"] = "completed"
    except Exception as exc:
        attempt.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        attempt.update(wall_seconds=time.perf_counter() - started, cpu_seconds=time.process_time() - cpu_started)
        atomic_json(attempt_path, attempt)
        summarize(output, config, observations, originals)
    return summarize(output, config, observations, originals)


def _run_pending(args, config, pending, originals, output, attempt, attempt_path):
    cache = args.cache_directory.resolve()
    for path in (cache, cache / "hub", cache / "modules"):
        path.mkdir(parents=True, exist_ok=True)
    os.environ.update(HF_HOME=str(cache), HF_HUB_CACHE=str(cache / "hub"), HF_MODULES_CACHE=str(cache / "modules"),
                      HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    from cti_vla.evaluation.teacher_diagnostics import atomic_json
    from cti_vla.data.sequence_example import iter_libero_examples
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
    import torch
    import transformers
    from transformers import AutoProcessor
    if torch.cuda.device_count() != 1:
        raise RuntimeError("optional diagnostic requires exactly one scheduler-assigned GPU")
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    load_started = time.perf_counter()
    components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
    processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
    vla = components.vla
    policy = OpenVLAOFTTokenPolicy(vla, components.action_head, components.proprio_projector, num_patches_full=512)
    torch.cuda.synchronize(device)
    attempt.update(model_loading_seconds=time.perf_counter() - load_started, gpu=torch.cuda.get_device_name(device),
                   runtime={**attempt["runtime"], "torch": torch.__version__, "transformers": transformers.__version__, "cuda": torch.version.cuda})
    atomic_json(attempt_path, attempt)
    wanted = {}
    for row in pending:
        wanted.setdefault(row["source_shard"], {}).setdefault(row["record_index"], []).append(row)
    for shard, records in sorted(wanted.items()):
        found = set()
        for episode in iter_libero_examples(args.data_directory / shard):
            if episode.record_index not in records:
                continue
            found.add(episode.record_index)
            for row in records[episode.record_index]:
                if episode.episode_id != row["episode_id"]:
                    raise ValueError("optional RLDS content ID differs from registered episode")
                _run_observation(row, episode, config, originals, output, vla, policy, processor, device)
            if found == set(records):
                break
        if found != set(records):
            raise ValueError("registered optional observation is missing from RLDS data")


def _run_observation(row, episode, config, originals, output, vla, policy, processor, device):
    import torch
    from cti_vla.evaluation.libero_runtime import prepare_rlds_eval_inputs
    from cti_vla.evaluation.teacher_diagnostics import ActionQueryCache, atomic_json, json_signature, run_exact_selection, tensor_signature
    config_sha = json_signature(config)
    started, cpu_started = time.perf_counter(), time.process_time()
    attempt = {"status": "running", "config_sha256": config_sha, "sample_id": row["sample_id"],
               "slurm_job_id": os.environ.get("SLURM_JOB_ID")}
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    attempt_path = output / "observation_attempts" / f"{row['sample_id']}_{timestamp}.json"
    atomic_json(attempt_path, attempt)
    result = {"status": "failed", "config_sha256": config_sha, "observation": row}
    oracle = None
    try:
        torch.cuda.reset_peak_memory_stats(device)
        inputs = prepare_rlds_eval_inputs(episode, row["step_index"], processor,
                                         vla.norm_stats[config["stats_key"]]["proprio"], device=device, dtype=torch.bfloat16)
        torch.cuda.synchronize(device)
        attempt["preprocessing_seconds"] = time.perf_counter() - started
        atomic_json(attempt_path, attempt)
        vision_started = time.perf_counter()
        with torch.no_grad():
            visual = vla._process_vision_features(inputs["pixel_values"], None, False).detach()
        torch.cuda.synchronize(device)
        attempt["vision_seconds"] = time.perf_counter() - vision_started
        atomic_json(attempt_path, attempt)
        if visual.shape != (1, 512, int(vla.llm_dim)):
            raise ValueError("expected two camera-major 256-patch projected sequences")
        original_identity = config["main_input_identities"][str(row["sample_id"])]
        input_sha = tensor_signature({key: inputs[key] for key in ("pixel_values", "input_ids", "attention_mask", "normalized_proprio")})
        if inputs["inputs_version"] != config["input_version"] or input_sha != original_identity["input_sha256"] or tensor_signature({"visual": visual}) != original_identity["visual_sha256"]:
            raise ValueError("optional real input/projected features differ from original G1")
        def forward(features, indices):
            return policy.forward_from_full_tokens(features, inputs["normalized_proprio"], input_ids=inputs["input_ids"],
                                                   attention_mask=inputs["attention_mask"], retained_indices=indices)
        prompt_length = inputs["input_ids"].shape[1] + int(inputs["input_ids"][0, -1] != 29871)
        oracle = ActionQueryCache(visual, forward, identity={"config_sha256": config_sha, "sample": row, "input_sha256": input_sha},
                                  journal_path=output / "queries" / f"{row['sample_id']}.jsonl",
                                  max_sample_forwards=2000, sequence_overhead_tokens=prompt_length + 58)
        full = oracle.query(oracle.full_indices, category="full_reference")
        difference = reference_difference(full, config, row["sample_id"])
        exact = run_exact_selection(oracle, sample_id=row["sample_id"], seed=517,
                                    per_camera_budgets=tuple(config["followup_per_camera_budgets"]))
        if oracle.ledger()["unique_cached_actions"] > 1604:
            raise RuntimeError("optional fresh unique queries exceed preregistered1604 bound")
        result.update(status="completed", exact_selection=exact, main_schedule_exact=originals[str(row["sample_id"])],
                      comparison=result_comparison(originals[str(row["sample_id"])], exact), full_reference_max_abs_difference=difference)
        attempt["status"] = "completed"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        attempt.update(status="failed", error=result["error"])
        raise
    finally:
        attempt.update(wall_seconds=time.perf_counter() - started, cpu_seconds=time.process_time() - cpu_started,
                       peak_allocated_bytes=torch.cuda.max_memory_allocated(device))
        if oracle is not None:
            result["cost_at_observation_end"] = oracle.ledger()
        atomic_json(attempt_path, attempt)
        atomic_json(output / "observations" / f"{row['sample_id']}.json", result)
    print(json.dumps({"sample_id": row["sample_id"], "status": "completed", "cost": oracle.ledger()}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT,
                        help="Writable project root containing this source snapshot and results")
    parser.add_argument("--registration", type=Path, default=ROOT / "configs/manifests/spatial_g1_step_diagnostic_v1.json")
    parser.add_argument("--protocol", type=Path, default=ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")
    parser.add_argument("--asset-manifest", type=Path, default=ROOT / "configs/assets/openvla_oft_libero_spatial.json")
    parser.add_argument("--output-directory", type=Path, required=True)
    for name in ("g1-directory", "analysis-summary", "activation-receipt", "checkpoint", "data-directory", "cache-directory"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--observation-limit", type=int)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if args.observation_limit is not None and not 1 <= args.observation_limit <= 3:
        parser.error("observation limit must be1..3")
    print(json.dumps(run(args), ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()

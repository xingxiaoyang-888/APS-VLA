"""Build G2 detached feature/actual-deletion caches after a reviewed G1 go.

No scorer is trained here. Test observations are unavailable to this command.
Completed observation files are reused; interrupted observations may incur
additional teacher calls, which remain charged in durable query journals.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]


def _setup_cache(path: Path, checkpoint: Path) -> None:
    path, checkpoint = path.resolve(), checkpoint.resolve()
    if path == checkpoint or checkpoint in path.parents:
        raise ValueError("HF runtime cache must be outside immutable model weights")
    for folder in (path, path / "hub", path / "modules"):
        folder.mkdir(parents=True, exist_ok=True)
    os.environ.update(HF_HOME=str(path), HF_HUB_CACHE=str(path / "hub"), HF_MODULES_CACHE=str(path / "modules"),
                      HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")


def _write_index(output, config, entries, metadata, *, verified_checkpoint=None):
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature, read_query_journal_ledger
    from cti_vla.training.offline import OFFLINE_CACHE_VERSION
    config_sha = json_signature(config)
    costs = []
    for row in metadata:
        path = output / "queries" / f"{row['sample_id']}.jsonl"
        if path.exists():
            costs.append(read_query_journal_ledger(path, expected_fields={"build_config_sha256": config_sha, "sample": row}))
        elif any(entry["sample_id"] == row["sample_id"] for entry in entries):
            raise ValueError("cached training observation is missing its authoritative teacher query journal")
    cost_keys = ("api_calls_attempted", "sample_forwards_attempted", "sample_forwards_completed", "cache_hits", "failed_calls", "interrupted_calls_unknown_completion", "known_policy_seconds", "journal_bytes")
    cost = {key: sum(item[key] for item in costs) for key in cost_keys}
    cost["policy_seconds_total"] = None if cost["interrupted_calls_unknown_completion"] else cost["known_policy_seconds"]
    lengths = sorted({length for item in costs for length in item["by_visual_length"]}, key=int)
    cost["by_visual_length"] = {length: {key: sum(item["by_visual_length"].get(length, {}).get(key, 0) for item in costs)
                                                for key in ("api_calls_attempted", "sample_forwards_attempted", "sample_forwards_completed", "known_policy_seconds")}
                                for length in lengths}
    attempts = []
    for path in sorted((output / "attempts").glob("*.json")):
        attempt = json.loads(path.read_text(encoding="utf-8"))
        if attempt.get("build_config_sha256") != config_sha:
            raise ValueError("cache attempt log belongs to another build config")
        attempts.append(attempt)
    cost["unfinalized_observation_attempts"] = sum(a["status"] == "running" for a in attempts)
    for key in ("wall_seconds", "cpu_seconds", "preprocessing_seconds", "feature_encoding_seconds"):
        cost[f"recorded_{key}_lower_bound"] = sum(a.get(key, 0.0) for a in attempts)
    cost["observation_wall_seconds_total"] = None if cost["unfinalized_observation_attempts"] else cost["recorded_wall_seconds_lower_bound"]
    cost["scope"] = "Teacher policy from cached projected features plus separately recorded observation preprocessing/feature/CPU/wall cost. Loading, full shard decoding and unfinalized hard-kill overhead require job/Slurm usage reconciliation."
    index = {"schema_version": 1, "cache_version": OFFLINE_CACHE_VERSION,
             "status": "completed" if len(entries) == len(metadata) and verified_checkpoint is not None else "partial",
             "build_config_sha256": config_sha, "build_config": config,
             "protocol_signature": config["protocol_signature"], "split": config["split"],
             "expected_observations": len(metadata), "observations": sorted(entries, key=lambda e: e["sample_id"]),
             "labels": len(entries) * 16, "teacher_cost": cost,
             "checkpoint_verification": asdict(verified_checkpoint) if verified_checkpoint is not None else None}
    atomic_json(output / "index.json", index)
    return index


def run(args):
    from cti_vla.data.experiment_protocol import load_experiment_protocol, write_frozen_json
    from cti_vla.data.identity import file_sha256
    from cti_vla.data.libero import load_manifest
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation.libero_runtime import LIBERO_EVAL_INPUT_VERSION
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    from cti_vla.training.offline import initial_training_assignments, load_offline_observation, require_g1
    from cti_vla.labeling.sampling import named_seed
    from cti_vla.labeling.deletion import LABEL_VERSION

    protocol = load_experiment_protocol(args.protocol)
    if args.split == "validation":
        ref = protocol.payload["panels"]["validation_effective"]
        manifest = load_manifest(protocol.path.parent / ref["path"])
    else:
        manifest = protocol.manifests["train"]
    assignments = initial_training_assignments(manifest, seed=args.sampling_seed)
    metadata = []
    for sample in manifest.samples:
        episode, authoritative = protocol.require_sample(sample.episode_id, sample.step_index, split=args.split)
        if sample != authoritative:
            raise ValueError("cache observation differs from registered split sample")
        metadata.append({**asdict(sample), "task_name": episode.task_name, "source_shard": episode.source_shard,
                         "record_index": episode.record_index, "is_last_step": sample.step_index == episode.num_steps - 1,
                         "assignment": assignments[sample.sample_id]})
    audited_ids = {row["sample_id"] for row in sorted(metadata, key=lambda row: named_seed(args.audit_seed, "cache-audit", row["sample_id"]))[:math.ceil(len(metadata) * .01)]}
    for row in metadata:
        row["audit_recompute"] = row["sample_id"] in audited_ids
    args.output.mkdir(parents=True, exist_ok=True)
    write_frozen_json(args.output / "sampling_plan.json", {"split": args.split, "seed": args.sampling_seed,
                      "audit_seed": args.audit_seed, "audit_fraction": .01,
                      "protocol_signature": protocol.payload["content_signature"], "observations": metadata})
    if args.prepare_only:
        summary = {"status": "prepared_only", "split": args.split, "observations": len(metadata),
                "labels": len(metadata) * 16, "teacher_sample_forward_upper_bound": len(metadata) * 18,
                "audit_observations": len(audited_ids), "audit_additional_teacher_upper_bound": len(audited_ids) * 18, "gpu_calls": 0}
        atomic_json(args.output / "preflight_summary.json", summary)
        return summary
    if any(value is None for value in (args.g1_report, args.checkpoint, args.data_directory, args.cache_directory)):
        raise ValueError("formal G2 requires --g1-report, --checkpoint, --data-directory and --cache-directory")
    checkpoint_manifest = load_checkpoint_manifest(args.asset_manifest)
    report = json.loads(args.g1_report.read_text(encoding="utf-8"))
    require_g1(report, model_revision=checkpoint_manifest.revision, input_version=LIBERO_EVAL_INPUT_VERSION,
               packing_version=PACKING_VERSION, protocol_signature=protocol.payload["content_signature"])
    if args.checkpoint.resolve() == args.output.resolve() or args.checkpoint.resolve() in args.output.resolve().parents:
        raise ValueError("detached caches must be outside immutable model weights")
    stats = json.loads((args.checkpoint / "dataset_statistics.json").read_text(encoding="utf-8"))
    matching_keys = [key for key in stats if "libero_spatial" in key]
    resolved_stats_key = args.stats_key or (matching_keys[0] if len(matching_keys) == 1 else None)
    if resolved_stats_key not in stats:
        raise ValueError("supply the unique Spatial --stats-key")
    config = {"split": args.split, "protocol_signature": protocol.payload["content_signature"],
              "g1_report_sha256": file_sha256(args.g1_report), "model_revision": checkpoint_manifest.revision,
              "asset_manifest_sha256": file_sha256(args.asset_manifest), "input_version": LIBERO_EVAL_INPUT_VERSION,
              "packing_version": PACKING_VERSION, "sampling_seed": args.sampling_seed, "stats_key": resolved_stats_key,
              "dataset_version": protocol.payload["source_signature"],
              "condition_version": f"{LIBERO_EVAL_INPUT_VERSION}:{resolved_stats_key}:frozen-prompt-embeddings",
              "action_version": "normalized-l1-8x7-v1", "label_version": LABEL_VERSION,
              "normalization_stats_sha256": file_sha256(args.checkpoint / "dataset_statistics.json"),
              "query_cap": args.query_cap, "audit_atol": args.audit_atol,
              "sampling_plan_sha256": file_sha256(args.output / "sampling_plan.json"),
              "source_files": {path.relative_to(ROOT).as_posix(): file_sha256(path)
                               for path in [*sorted((ROOT / "src/cti_vla").rglob("*.py")), Path(__file__)]}}
    config_sha = json_signature(config)
    write_frozen_json(args.output / "build_config.json", config)
    # Verify weights before accepting even an entirely cached invocation.
    before = verify_checkpoint_directory(args.checkpoint, checkpoint_manifest)
    registered = {}
    if (args.output / "index.json").exists():
        old_index = json.loads((args.output / "index.json").read_text(encoding="utf-8"))
        if old_index.get("build_config_sha256") != config_sha:
            raise ValueError("existing cache index belongs to a different build config")
        registered = {entry["sample_id"]: entry for entry in old_index["observations"]}
    entries, pending = [], []
    for row in metadata:
        path = args.output / "observations" / f"{row['sample_id']}.pt"
        if path.exists():
            receipt = json.loads(path.with_suffix(".receipt.json").read_text(encoding="utf-8"))
            digest = registered[row["sample_id"]]["sha256"] if row["sample_id"] in registered else receipt["cache_sha256"]
            cached = load_offline_observation(path, expected_sha256=digest, protocol=protocol, required_split=args.split)
            if cached.metadata.get("build_config_sha256") != config_sha or any(cached.metadata.get(k) != v for k, v in row.items()):
                raise ValueError("existing feature cache belongs to a different sampling/input/version config")
            entries.append({**row, "path": path.relative_to(args.output).as_posix(), "sha256": digest})
        else:
            pending.append(row)
    if not pending:
        return _write_index(args.output, config, entries, metadata, verified_checkpoint=before)
    _write_index(args.output, config, entries, metadata)
    if args.observation_limit is not None:
        pending = pending[:args.observation_limit]
    _setup_cache(args.cache_directory, args.checkpoint)
    import torch
    from transformers import AutoProcessor
    from cti_vla.data.sequence_example import iter_libero_examples
    from cti_vla.evaluation.libero_runtime import prepare_rlds_eval_inputs
    from cti_vla.evaluation.teacher_diagnostics import ActionQueryCache, tensor_signature
    from cti_vla.labeling import DeletionTeacher, LabelProvenance
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
    from cti_vla.selection import ConditionalTokenBatch
    from cti_vla.training.offline import OfflineObservation, sample_initial_sets, save_offline_observation

    if torch.cuda.device_count() != 1:
        raise RuntimeError("G2 requires one scheduler-assigned visible GPU")
    device = torch.device("cuda:0")
    components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
    vla = components.vla
    processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
    stats_key = resolved_stats_key
    if stats_key not in vla.norm_stats:
        raise ValueError("supply Spatial --stats-key")
    policy = OpenVLAOFTTokenPolicy(vla, components.action_head, components.proprio_projector,
                                  num_patches_full=components.num_patches_full)
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
                    raise ValueError("decoded RLDS episode content ID mismatch")
                oracle, started = None, time.perf_counter()
                cpu_started = time.process_time()
                attempt_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
                attempt = {"sample_id": row["sample_id"], "build_config_sha256": config_sha,
                           "status": "running", "slurm_job_id": os.environ.get("SLURM_JOB_ID")}
                attempt_path = args.output / "attempts" / f"{row['sample_id']}_{attempt_id}.json"
                atomic_json(attempt_path, attempt)
                try:
                    torch.cuda.reset_peak_memory_stats(device)
                    inputs = prepare_rlds_eval_inputs(episode, row["step_index"], processor,
                                                     vla.norm_stats[stats_key]["proprio"], device=device, dtype=torch.bfloat16)
                    torch.cuda.synchronize(device)
                    attempt["preprocessing_seconds"] = time.perf_counter() - started
                    encoding_started = time.perf_counter()
                    with torch.no_grad():
                        visual = vla._process_vision_features(inputs["pixel_values"], None, False).detach()
                        language = vla.get_input_embeddings()(inputs["input_ids"]).detach()
                    torch.cuda.synchronize(device)
                    attempt["feature_encoding_seconds"] = time.perf_counter() - encoding_started
                    batch = ConditionalTokenBatch(visual, language, inputs["attention_mask"].bool(),
                        inputs["normalized_proprio"].detach(), torch.arange(2, device=device).repeat_interleave(256)[None],
                        torch.arange(256, device=device).repeat(2)[None], torch.ones(1, 512, device=device, dtype=torch.bool))
                    provenance = LabelProvenance((str(row["sample_id"]),), (row["episode_id"],), args.split,
                        checkpoint_manifest.revision, protocol.payload["source_signature"], inputs["inputs_version"], PACKING_VERSION,
                        f"{inputs['inputs_version']}:{stats_key}:frozen-prompt-embeddings", "normalized-l1-8x7-v1")
                    def forward(source, indices):
                        return policy.forward_from_full_tokens(source, inputs["normalized_proprio"],
                            input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"], retained_indices=indices)
                    identity = {"build_config_sha256": config_sha, "sample": row,
                                "input_sha256": tensor_signature({k: inputs[k] for k in
                                    ("pixel_values", "input_ids", "attention_mask", "normalized_proprio")})}
                    prompt_length = inputs["input_ids"].shape[1] + int(inputs["input_ids"][0, -1] != 29871)
                    oracle = ActionQueryCache(visual, forward, identity=identity,
                        journal_path=args.output / "queries" / f"{row['sample_id']}.jsonl",
                        max_sample_forwards=args.query_cap, sequence_overhead_tokens=prompt_length + 58)
                    query_repeat_id = attempt_id
                    def retained_callback(data, indices):
                        count = indices.shape[1]
                        category = "full_reference" if count == 512 else "set_base" if count in (256, 128) else "deletion"
                        # Fresh retry identity preserves actual teacher_calls in
                        # existing DeletionLabels; earlier failed work is charged.
                        return oracle.query(tuple(indices[0].cpu().tolist()), category=category,
                                            repeat_id=query_repeat_id).to(data.visual.device)
                    teacher = DeletionTeacher(policy, retained_callback)
                    prior_calls = oracle.ledger()["sample_forwards_attempted"]
                    reference = teacher.reference(batch, provenance)
                    labels = []
                    for retained, candidates in sample_initial_sets(row["assignment"]):
                        mask = torch.zeros_like(batch.valid)
                        mask[:, list(retained)] = True
                        labels.append(teacher.label(batch, mask, torch.tensor([candidates], device=device),
                                                    provenance, full_reference=reference))
                    if oracle.ledger()["sample_forwards_attempted"] - prior_calls != 18:
                        raise RuntimeError("fresh G2 observation must execute exactly 18 teacher sample forwards")
                    audit = None
                    if row["audit_recompute"]:
                        query_repeat_id = attempt_id + ":audit"
                        repeated_reference = teacher.reference(batch, provenance)
                        repeated = [teacher.label(batch, label.retained_mask, label.candidate_indices,
                                                  provenance, full_reference=repeated_reference) for label in labels]
                        differences = {name: max(float((getattr(left, name) - getattr(right, name)).abs().max())
                                                 for left, right in zip(labels, repeated))
                                       for name in ("influence", "base_error", "deleted_error", "full_action")}
                        audit = {"atol": args.audit_atol, "max_absolute_differences": differences,
                                 "teacher_sample_forwards": 18, "set_records_recomputed": 2}
                        if max(differences.values()) > args.audit_atol:
                            raise RuntimeError(f"fixed cache numerical recomputation audit failed: {differences}")
                        if oracle.ledger()["sample_forwards_attempted"] - prior_calls != 36:
                            raise RuntimeError("audited G2 observation must execute exactly 36 sample forwards")
                    item = OfflineObservation(batch, tuple(labels), inputs["input_ids"], inputs["attention_mask"],
                                              dict(row, build_config_sha256=config_sha, recomputation_audit=audit))
                    item.validate(protocol, required_split=args.split)
                    path = args.output / "observations" / f"{row['sample_id']}.pt"
                    digest = save_offline_observation(path, item)
                    entries.append({**row, "path": path.relative_to(args.output).as_posix(), "sha256": digest})
                    attempt["status"] = "completed"
                except Exception as error:
                    attempt["status"] = "failed"
                    attempt["error"] = f"{type(error).__name__}: {error}"
                    raise
                finally:
                    attempt["wall_seconds"] = time.perf_counter() - started
                    attempt["cpu_seconds"] = time.process_time() - cpu_started
                    attempt["peak_allocated_bytes"] = torch.cuda.max_memory_allocated(device)
                    if oracle is not None:
                        attempt["cost_after_attempt"] = oracle.ledger()
                    atomic_json(attempt_path, attempt)
                    _write_index(args.output, config, entries, metadata)
                print(json.dumps({"sample_id": row["sample_id"], "status": "completed", "new_teacher_sample_forwards": 36 if row["audit_recompute"] else 18}), flush=True)
            if found == set(records):
                break
        if found != set(records):
            raise ValueError("registered cache episodes missing from the RLDS shard")
    after = verify_checkpoint_directory(args.checkpoint, checkpoint_manifest)
    if before != after:
        raise RuntimeError("immutable VLA checkpoint changed while producing labels")
    return _write_index(args.output, config, entries, metadata, verified_checkpoint=after)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")
    parser.add_argument("--asset-manifest", type=Path, default=ROOT / "configs/assets/openvla_oft_libero_spatial.json")
    parser.add_argument("--split", choices=("train", "validation"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--g1-report", type=Path)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--cache-directory", type=Path)
    parser.add_argument("--data-directory", type=Path)
    parser.add_argument("--stats-key")
    parser.add_argument("--sampling-seed", type=int, default=717)
    parser.add_argument("--audit-seed", type=int, default=817)
    parser.add_argument("--audit-atol", type=float, default=1e-6)
    parser.add_argument("--query-cap", type=int, default=72, help="Per-observation total attempted calls, including recomputation and failed retries")
    parser.add_argument("--observation-limit", type=int)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if args.query_cap < 36 or not math.isfinite(args.audit_atol) or not 0 <= args.audit_atol <= .002 or (args.observation_limit is not None and args.observation_limit <= 0):
        parser.error("query cap must be >=36, audit atol in[0,0.002], and observation limit positive")
    result = run(args)
    print(json.dumps({k: result[k] for k in ("status", "split", "observations", "expected_observations", "labels", "teacher_sample_forward_upper_bound", "audit_observations", "audit_additional_teacher_upper_bound", "teacher_cost", "gpu_calls") if k in result}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

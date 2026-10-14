"""D1 supplement: 18 unique successful policy queries per approved pair.

No simulator success or selector-training claim is made. Pair membership,
instructions, formal-image evidence and eight shared candidates must have been
frozen before any label query. --prepare-only allocates no GPU.
Failed/interrupted attempts are charged separately within a frozen retry cap.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import platform
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def configure_cache(path, checkpoint):
    path, checkpoint = path.resolve(), checkpoint.resolve()
    if path == checkpoint or checkpoint in path.parents:
        raise ValueError("cache must be outside immutable checkpoint")
    for directory in (path, path / "hub", path / "modules"):
        directory.mkdir(parents=True, exist_ok=True)
    os.environ.update(HF_HOME=str(path), HF_HUB_CACHE=str(path / "hub"), HF_MODULES_CACHE=str(path / "modules"),
                      HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")


def verify_episode_evidence(episode, pair):
    """Check the actual train bytes and final policy pixels against review."""
    import numpy as np
    from PIL import Image
    from cti_vla.evaluation.libero_runtime import process_camera
    if episode.episode_id != pair["episode_id"] or episode.instructions[pair["step_index"]] != pair["instructions"][0]:
        raise ValueError("actual D1 episode/instruction differs from the preregistered pair")
    step = pair["step_index"]
    for name, encoded in (("main", episode.images[step]), ("wrist", episode.wrist_images[step])):
        if hashlib.sha256(encoded).hexdigest() != pair["views"][name]["raw_jpeg_sha256"]:
            raise ValueError("D1 raw image hash mismatch")
        with Image.open(BytesIO(encoded)) as image:
            formal = process_camera(np.asarray(image.convert("RGB")), already_rotated=True)
        if hashlib.sha256(np.ascontiguousarray(formal).tobytes()).hexdigest() != pair["views"][name]["rgb_sha256"]:
            raise ValueError("D1 formal pixels differ from the visually reviewed image")
    if hashlib.sha256(np.asarray(episode.proprio[step], dtype="<f4").tobytes()).hexdigest() != pair["raw_proprio_sha256"]:
        raise ValueError("D1 physical proprio differs from the reviewed observation")


def condition_episode(episode, step, instruction):
    """Override only language in an ephemeral input view; source ID is unchanged."""
    instructions = list(episode.instructions)
    instructions[step] = instruction
    return SimpleNamespace(num_steps=episode.num_steps, images=episode.images, wrist_images=episode.wrist_images,
                           proprio=episode.proprio, instructions=instructions)


def verify_pair_evidence(payload, evidence_root):
    """CPU-only, byte-level linkage from the preregistration to reviewed images."""
    import numpy as np
    from PIL import Image
    from cti_vla.data.identity import file_sha256
    root = Path(evidence_root).resolve()
    files = {}
    def resolve(relative):
        path = (root / relative).resolve()
        if root not in path.parents:
            raise ValueError("D1 evidence path must remain inside evidence root")
        return path
    def checked(relative, expected):
        path = resolve(relative)
        if file_sha256(path) != expected:
            raise ValueError(f"D1 evidence hash mismatch: {relative}")
        files[path.relative_to(root).as_posix()] = expected
        return path
    directory = Path(payload["review_image_directory"])
    receipt = json.loads(checked(directory / "prepared_images.json", payload["prepared_images_sha256"]).read_text(encoding="utf-8"))
    registry = json.loads(checked("results/g1_preflight/d1_visual_candidates/candidates.json", payload["candidate_registry_sha256"]).read_text(encoding="utf-8"))
    if receipt["formal_d1_queries"] != 0 or receipt["schema_version"] != 1:
        raise ValueError("D1 review receipt must precede all label queries")
    for key in ("input_version", "runtime_sha256", "protocol_signature", "candidate_registry_sha256"):
        if receipt[key] != payload[key]:
            raise ValueError(f"D1 review receipt identity mismatch: {key}")
    prepared = {row["sample_id"]: row for row in receipt["observations"]}
    candidates = {row["sample_id"]: row for row in registry}
    if len(prepared) != len(receipt["observations"]) or len(candidates) != len(registry) or set(prepared) != set(candidates):
        raise ValueError("D1 candidate/receipt coverage mismatch")
    included = {row["sample_id"] for row in payload["pairs"]}
    excluded = {row["sample_id"] for row in payload["exclusions"]}
    if included & excluded or included | excluded != set(prepared):
        raise ValueError("D1 approved/excluded coverage differs from reviewed candidates")
    identity_keys = ("sample_id", "episode_id", "step_index", "split", "instruction", "source_shard", "record_index")
    for sample, row in prepared.items():
        candidate = candidates[sample]
        if any(row[key] != candidate[key] for key in identity_keys):
            raise ValueError("D1 review/candidate observation identity mismatch")
        for name in ("main", "wrist"):
            view, raw = row["views"][name], candidate["views"][name]
            if view["raw_jpeg_sha256"] != raw["sha256"] or view["official_reference_equal"] is not True:
                raise ValueError("D1 original/formal image reference mismatch")
            checked(raw["path"], raw["sha256"])
            path = checked(directory / view["file"], view["png_sha256"])
            with Image.open(path) as image:
                pixels = np.asarray(image)
                if image.mode != "RGB" or list(pixels.shape) != [224, 224, 3] or list(pixels.shape) != view["shape"]:
                    raise ValueError("D1 reviewed PNG has invalid mode/shape")
            if hashlib.sha256(np.ascontiguousarray(pixels).tobytes()).hexdigest() != view["rgb_sha256"]:
                raise ValueError("D1 reviewed RGB pixel hash mismatch")
    for pair in payload["pairs"]:
        row = prepared[pair["sample_id"]]
        if any(row[key] != pair[key] for key in (*identity_keys, "raw_proprio_sha256", "views")):
            raise ValueError("D1 frozen pair differs from the reviewed observation receipt")
    return {"status": "verified", "observations_reviewed": len(prepared), "pairs_approved": len(included), "files": files}


def _condition_cost(output, pair, condition, config_sha, max_attempts_per_condition):
    from cti_vla.evaluation.condition_diagnostics import D1_VERSION, validate_attempt_cap
    from cti_vla.evaluation.teacher_diagnostics import read_query_journal_ledger
    validate_attempt_cap(max_attempts_per_condition)
    path = Path(output) / "queries" / pair["pair_id"] / f"condition_{condition}.jsonl"
    cost = read_query_journal_ledger(path, expected_fields={"config_sha256": config_sha, "pair": pair,
        "condition_index": condition, "instruction": pair["instructions"][condition], "d1_version": D1_VERSION,
        "max_attempts_per_condition": max_attempts_per_condition, "unique_successful_queries_required": 9})
    if cost["sample_forwards_attempted"] > max_attempts_per_condition or cost["sample_forwards_completed"] > 9 or cost["unique_cached_actions"] != cost["sample_forwards_completed"]:
        raise ValueError("D1 condition exceeds its frozen attempts or unique-query panel")
    return cost


def summarize_partial_queries(output, pairs, config_sha, *, max_attempts_per_condition=12):
    """Recover charged starts without a model or even a completed pair file.

    Missing journals mean no durable query start. Corrupt existing journals
    raise instead of being silently counted as free. Unknown completions make
    total policy seconds null; their known elapsed-time lower bound is retained.
    """
    from cti_vla.evaluation.condition_diagnostics import sum_query_costs, validate_attempt_cap
    validate_attempt_cap(max_attempts_per_condition)
    output = Path(output)
    expected = {output / "queries" / pair["pair_id"] / f"condition_{condition}.jsonl"
                for pair in pairs for condition in (0, 1)}
    if set((output / "queries").rglob("*.jsonl")) - expected:
        raise ValueError("D1 output contains journals outside the frozen pair panel")
    costs, present, missing = [], [], []
    for pair in pairs:
        pair_path = output / "pairs" / f"{pair['pair_id']}.json"
        saved = json.loads(pair_path.read_text(encoding="utf-8")) if pair_path.exists() else None
        if saved is not None and (saved.get("config_sha256") != config_sha or saved.get("pair") != pair):
            raise ValueError("D1 saved pair belongs to another frozen configuration")
        for condition in (0, 1):
            path = output / "queries" / pair["pair_id"] / f"condition_{condition}.jsonl"
            relative = path.relative_to(output).as_posix()
            if not path.exists():
                if saved is not None and saved.get("status") == "completed":
                    raise ValueError("D1 completed pair has a missing charged query journal")
                missing.append(relative)
                continue
            costs.append(_condition_cost(output, pair, condition, config_sha, max_attempts_per_condition))
            present.append(relative)
    return {"stage": "D1", "status": "partial", "config_sha256": config_sha,
            "pairs_registered": len(pairs), "unique_successful_queries_required": 18 * len(pairs),
            "max_policy_sample_forwards_attempted": 2 * max_attempts_per_condition * len(pairs),
            "cost": sum_query_costs(costs), "journals_present": present, "journals_missing": missing}


def write_partial_summary(output, pairs, config_sha, *, max_attempts_per_condition=12, status="partial", error=None):
    from cti_vla.evaluation.teacher_diagnostics import atomic_json
    from cti_vla.data.identity import file_sha256
    try:
        result = summarize_partial_queries(output, pairs, config_sha, max_attempts_per_condition=max_attempts_per_condition)
    except Exception as exc:
        # Preserve evidence and uncertainty, never replace an unreadable charge
        # with a zero. No model execution is allowed after a failed reconcile.
        result = {"stage": "D1", "config_sha256": config_sha, "cost": None,
                  "cost_reconciliation_error": f"{type(exc).__name__}: {exc}"}
        if error is None:
            atomic_json(Path(output) / "summary.json", dict(result, status="failed"))
            raise
    result.update(status=status, checkpoint_unchanged=None,
                  query_journal_sha256={path.relative_to(output).as_posix(): file_sha256(path)
                      for path in sorted((Path(output) / "queries").rglob("*.jsonl"))})
    if error is not None:
        result["error"] = error
    result["cost_scope"] = "Durable policy-query attempts including failures and unknown completion; unknown timing is not zero. Nonquery preprocessing/vision/CPU cost from killed attempts requires invocation and scheduler accounting. Not deployment latency."
    atomic_json(Path(output) / "summary.json", result)
    return result


def reconcile_pair_queries(output, row, config_sha, max_attempts_per_condition=12):
    """Re-read durable query evidence even when a completed pair was resumed."""
    import torch
    from cti_vla.evaluation.teacher_diagnostics import tensor_signature, action_error
    from cti_vla.evaluation.condition_diagnostics import D1_VERSION, FIXED_CANDIDATES, sum_query_costs
    output = Path(output)
    pair = row["pair"]
    if row["status"] != "completed" or row["d1_version"] != D1_VERSION or row["max_attempts_per_condition"] != max_attempts_per_condition or len(row["conditions"]) != 2 or pair["candidate_indices"] != list(FIXED_CANDIDATES):
        raise ValueError("D1 result differs from the frozen diagnostic contract")
    costs = []
    for condition in (0, 1):
        path = output / "queries" / pair["pair_id"] / f"condition_{condition}.jsonl"
        cost = _condition_cost(output, pair, condition, config_sha, max_attempts_per_condition)
        if cost["sample_forwards_completed"] != 9 or cost["unique_cached_actions"] != 9:
            raise ValueError("completed D1 condition needs nine unique successfully journaled queries")
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        starts = {event["call_id"]: event for event in events if event["event"] == "start"}
        full = tuple(range(512))
        expected = {full, *(tuple(index for index in full if index != token) for token in pair["candidate_indices"])}
        for event in starts.values():
            retained = tuple(event["retained_indices"])
            category = "D1_condition_full" if retained == full else "D1_actual_deletion"
            if retained not in expected or event["replace_index"] is not None or event["repeat_id"] is not None or event["physical_visual_tokens"] != len(retained) or event["category"] != category:
                raise ValueError("D1 charged query differs from its actual-deletion contract")
        actions = {}
        for event in events:
            if event["event"] != "complete":
                continue
            action = torch.tensor(event["action"], dtype=torch.float32)
            if action.shape != (1, 8, 7) or not bool(torch.isfinite(action).all()) or tensor_signature({"action": action}) != event["action_sha256"]:
                raise ValueError("D1 journal action content/hash mismatch")
            retained = tuple(starts[event["call_id"]]["retained_indices"])
            if retained in actions:
                raise ValueError("D1 contains a repeated charged query")
            actions[retained] = action
        if set(actions) != expected:
            raise ValueError("D1 journal retained sets differ from frozen actual-deletion panel")
        recorded = row["conditions"][condition]
        if recorded["condition_index"] != condition or recorded["instruction"] != pair["instructions"][condition]:
            raise ValueError("D1 result condition identity mismatch")
        if not torch.equal(actions[full], torch.tensor(recorded["full_reference_action"], dtype=torch.float32)):
            raise ValueError("D1 result reference differs from durable condition-specific reference")
        if recorded["baseline_error"] != action_error(actions[full], actions[full]):
            raise ValueError("D1 full-set baseline error must use its own full reference")
        for token, deletion in zip(pair["candidate_indices"], recorded["deletions"]):
            retained = tuple(index for index in full if index != token)
            error = action_error(actions[retained], actions[full])
            if deletion["source_index"] != token or deletion["error"] != error or deletion["signed_label"] != error["mean_l1"] or not torch.equal(actions[retained], torch.tensor(deletion["action"], dtype=torch.float32)):
                raise ValueError("D1 result label differs from its durable own-condition reference")
        if len(recorded["deletions"]) != 8:
            raise ValueError("D1 condition result is missing candidate labels")
        costs.append(cost)
    differences = [right["signed_label"] - left["signed_label"]
                   for left, right in zip(row["conditions"][0]["deletions"], row["conditions"][1]["deletions"])]
    if row["label_difference_condition1_minus_condition0"] != differences or row["mean_absolute_label_difference"] != sum(abs(value) for value in differences) / len(differences):
        raise ValueError("D1 condition difference summary differs from durable labels")
    result = sum_query_costs(costs)
    # sum_query_costs accepts raw ledgers; expose this alias for later aggregation.
    result["unique_cached_actions"] = result["unique_successful_queries"]
    return result


def _run(args):
    from cti_vla.data.experiment_protocol import load_experiment_protocol, write_frozen_json
    from cti_vla.data.identity import file_sha256
    from cti_vla.evaluation.condition_diagnostics import D1_VERSION, validate_pair_manifest, run_condition_pair, validate_attempt_cap, sum_query_costs
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature, require_g0, tensor_signature
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    from cti_vla.evaluation import condition_diagnostics, libero_runtime
    protocol = load_experiment_protocol(args.protocol)
    pairs = json.loads(args.pairs.read_text(encoding="utf-8"))
    validate_pair_manifest(pairs, protocol, input_version=libero_runtime.INPUTS_VERSION)
    max_attempts = args.max_attempts_per_condition
    validate_attempt_cap(max_attempts)
    evidence = verify_pair_evidence(pairs, args.evidence_root)
    if args.prepare_only:
        return {"status": "prepared_only", "pairs": len(pairs["pairs"]), "exclusions": len(pairs["exclusions"]),
                "pair_manifest_signature": pairs["content_signature"], "unique_successful_queries_required": 18 * len(pairs["pairs"]),
                "max_policy_sample_forwards": 2 * max_attempts * len(pairs["pairs"]), "evidence": evidence, "gpu_queries": 0}
    if any(value is None for value in (args.g0_report, args.checkpoint, args.cache_directory, args.data_directory, args.output)):
        raise ValueError("formal D1 needs --g0-report, --checkpoint, --cache-directory, --data-directory, --output")
    if args.output.resolve() == args.checkpoint.resolve() or args.checkpoint.resolve() in args.output.resolve().parents:
        raise ValueError("D1 output must be outside the immutable checkpoint")
    manifest = load_checkpoint_manifest(args.checkpoint_manifest)
    g0 = json.loads(args.g0_report.read_text(encoding="utf-8"))
    require_g0(g0, model_revision=manifest.revision, input_version=libero_runtime.INPUTS_VERSION, packing_version=PACKING_VERSION)
    runtime_hash = file_sha256(libero_runtime.__file__)
    if runtime_hash != pairs["runtime_sha256"] or runtime_hash != g0["provenance"]["runtime_sha256"]:
        raise ValueError("D1 visual review, G0 and current formal-input code hashes must match")
    if g0["provenance"]["checkpoint_manifest_sha256"] != file_sha256(args.checkpoint_manifest):
        raise ValueError("D1 checkpoint manifest differs from accepted G0")
    for pair in pairs["pairs"]:
        relative = Path(pair["bddl"]).relative_to("external/LIBERO")
        if file_sha256(args.libero_source / relative) != pair["bddl_sha256"]:
            raise ValueError("physical scene definition differs from the approved pair")
    config = {"schema_version": 1, "stage": "D1", "version": D1_VERSION,
              "model_revision": manifest.revision, "input_version": libero_runtime.INPUTS_VERSION,
              "packing_version": PACKING_VERSION, "runtime_sha256": runtime_hash,
              "module_sha256": file_sha256(condition_diagnostics.__file__), "script_sha256": file_sha256(__file__),
              "pair_manifest_signature": pairs["content_signature"], "pair_manifest_sha256": file_sha256(args.pairs),
              "g0_report_sha256": file_sha256(args.g0_report), "protocol_signature": protocol.payload["content_signature"],
              "checkpoint_manifest_sha256": file_sha256(args.checkpoint_manifest), "stats_key": args.stats_key,
              "seed": 17, "per_condition_sample_forward_cap": max_attempts, "per_condition_unique_successful_queries": 9,
              "total_unique_policy_query_cap": len(pairs["pairs"]) * 18, "total_attempt_cap": len(pairs["pairs"]) * 2 * max_attempts,
              "retry_policy": "Exceptions stop invocation; restart reuses completed actions and retries incomplete query within unchanged attempt cap. Failed/unknown attempts remain charged.",
              "evidence": evidence,
              "source_files": {str(path.relative_to(ROOT).as_posix()): file_sha256(path) for path in sorted((ROOT / "src/cti_vla").rglob("*.py"))}}
    config_sha = json_signature(config)
    args.output.mkdir(parents=True, exist_ok=True)
    write_frozen_json(args.output / "config.json", config)
    # Set only after accepting this invocation's complete frozen config. An
    # incompatible restart must not overwrite the previous run's summary.
    args._active_d1_config = config
    args._active_d1_pairs = pairs
    if not pairs["pairs"]:
        result = {"stage": "D1", "status": "not_applicable", "config_sha256": config_sha, "exclusions": pairs["exclusions"], "policy_sample_forwards": 0}
        atomic_json(args.output / "summary.json", result)
        return result
    write_partial_summary(args.output, pairs["pairs"], config_sha, max_attempts_per_condition=max_attempts, status="running")
    configure_cache(args.cache_directory, args.checkpoint)
    import numpy as np
    import torch
    from transformers import AutoProcessor
    from cti_vla.data.sequence_example import iter_libero_examples
    from cti_vla.evaluation.checkpoint_manifest import verify_checkpoint_directory
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
    if torch.cuda.device_count() != 1:
        raise RuntimeError("D1 must run within one scheduler-allocated GPU")
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    torch.manual_seed(17)
    np.random.seed(17)
    before = verify_checkpoint_directory(args.checkpoint, manifest)
    components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
    processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
    if args.stats_key not in components.vla.norm_stats:
        raise ValueError("D1 stats key is absent from checkpoint")
    policy = OpenVLAOFTTokenPolicy(components.vla, components.action_head, components.proprio_projector, num_patches_full=512)
    invocation = {"created_utc": datetime.now(timezone.utc).isoformat(), "config_sha256": config_sha,
                  "checkpoint": asdict(before), "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
                  "python": platform.python_version(), "torch": torch.__version__, "cuda": torch.version.cuda,
                  "gpu": torch.cuda.get_device_name(device), "dtype": "bfloat16", "attention": "sdpa"}
    atomic_json(args.output / "attempts" / f"{time.time_ns()}.json", invocation)
    outputs = []
    for pair in pairs["pairs"]:
        path = args.output / "pairs" / f"{pair['pair_id']}.json"
        if path.exists():
            old = json.loads(path.read_text(encoding="utf-8"))
            if old.get("config_sha256") != config_sha or old.get("pair") != pair:
                raise ValueError("saved D1 pair belongs to another frozen configuration")
            if old["status"] == "completed":
                outputs.append(old)
                continue
        began, cpu_began = time.perf_counter(), time.process_time()
        episode = next(row for row in iter_libero_examples(args.data_directory / pair["source_shard"]) if row.record_index == pair["record_index"])
        verify_episode_evidence(episode, pair)
        inputs = [libero_runtime.prepare_rlds_eval_inputs(condition_episode(episode, pair["step_index"], instruction),
                  pair["step_index"], processor, components.vla.norm_stats[args.stats_key]["proprio"], device=device, dtype=torch.bfloat16)
                  for instruction in pair["instructions"]]
        if not torch.equal(inputs[0]["pixel_values"], inputs[1]["pixel_values"]) or not torch.equal(inputs[0]["normalized_proprio"], inputs[1]["normalized_proprio"]):
            raise ValueError("D1 changed a visual/proprio condition alongside language")
        preprocessing_seconds = time.perf_counter() - began
        torch.cuda.synchronize(device)
        vision_started = time.perf_counter()
        with torch.inference_mode():
            visual = components.vla._process_vision_features(inputs[0]["pixel_values"], None, False)
        torch.cuda.synchronize(device)
        vision_seconds = time.perf_counter() - vision_started
        signatures = [tensor_signature({key: item[key] for key in ("input_ids", "attention_mask", "normalized_proprio")}) for item in inputs]
        def bind(item):
            return lambda full, indices: policy.forward_from_full_tokens(full, item["normalized_proprio"], input_ids=item["input_ids"], attention_mask=item["attention_mask"], retained_indices=indices)
        identity = {"config_sha256": config_sha, "pair": pair, "instructions": pair["instructions"],
                    "condition_tensor_signatures": signatures, "normalized_proprio": inputs[0]["normalized_proprio_numpy"].tolist()}
        overheads = [item["input_ids"].shape[1] + int(item["input_ids"][0, -1].item() != 29871) + 58 for item in inputs]
        # Overhead = prompt including BOS + optional empty token + proprio1 +
        # action56 + stop1; visual tokens alone are 512/511.
        journal_directory = args.output / "queries" / pair["pair_id"]
        try:
            result = run_condition_pair(visual, [bind(item) for item in inputs], identity=identity,
                                        candidate_indices=pair["candidate_indices"], journal_directory=journal_directory,
                                        sequence_overheads=overheads, max_attempts_per_condition=max_attempts)
        except Exception as exc:
            atomic_json(path, {"status": "failed", "config_sha256": config_sha, "pair": pair, "error": str(exc),
                              "note": "Durable per-condition query journals retain attempted/failed/interrupted costs; retries consume the same cap."})
            raise
        result.update(config_sha256=config_sha, pair=pair, normalized_proprio=identity["normalized_proprio"],
                      condition_tensor_signatures=signatures, preprocessing_seconds=preprocessing_seconds,
                      vision_seconds=vision_seconds, vision_sample_forwards=1,
                      wall_seconds_this_attempt=time.perf_counter() - began, cpu_seconds_this_attempt=time.process_time() - cpu_began)
        atomic_json(path, result)
        outputs.append(result)
        print(json.dumps({"pair_id": pair["pair_id"], "status": result["status"], "queries": result["cost"]["sample_forwards_completed"]}), flush=True)
    after = verify_checkpoint_directory(args.checkpoint, manifest)
    if before != after:
        raise RuntimeError("immutable checkpoint changed during D1")
    reconciled_costs = [reconcile_pair_queries(args.output, row, config_sha, max_attempts) for row in outputs]
    summary = {"stage": "D1", "status": "completed", "config_sha256": config_sha, "pairs": len(outputs),
               "checkpoint_unchanged": True, "pair_manifest_signature": pairs["content_signature"],
               "cost": sum_query_costs(reconciled_costs),
               "pair_result_sha256": {row["pair"]["pair_id"]: file_sha256(args.output / "pairs" / f"{row['pair']['pair_id']}.json") for row in outputs},
               "query_journal_sha256": {str(path.relative_to(args.output).as_posix()): file_sha256(path) for path in sorted((args.output / "queries").rglob("*.jsonl"))},
               "cost_scope": "Teacher sample/API counts and synchronized cached-feature policy seconds are reconciled from every condition journal. Per-pair files record preprocessing/vision/wall/CPU time for their successful attempt; invocation receipts and failed query journals retain failures. Hard-killed nonquery wall/CPU time remains unknown and needs Slurm accounting. Not deployment latency.",
               "provenance": config, "interpretation": "Only legal-language frozen-teacher label sensitivity; no closed-loop success, causality or trained-selector benefit claim."}
    if summary["cost"]["sample_forwards_completed"] != 18 * len(outputs):
        raise RuntimeError("D1 completed query count differs from preregistered 18/pair")
    atomic_json(args.output / "summary.json", summary)
    return summary


def run(args):
    """Persist partial query costs on normal exceptions and Python interrupts."""
    args._active_d1_config = None
    try:
        return _run(args)
    except BaseException as exc:
        output = getattr(args, "output", None)
        config = getattr(args, "_active_d1_config", None)
        if output is not None and config is not None:
            from cti_vla.evaluation.teacher_diagnostics import json_signature
            write_partial_summary(Path(output), args._active_d1_pairs["pairs"], json_signature(config),
                max_attempts_per_condition=config["per_condition_sample_forward_cap"],
                status="failed", error=f"{type(exc).__name__}: {exc}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=Path, default=ROOT / "configs/manifests/spatial_d1_v1/pairs.json")
    parser.add_argument("--protocol", type=Path, default=ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")
    parser.add_argument("--checkpoint-manifest", type=Path, default=ROOT / "configs/assets/openvla_oft_libero_spatial.json")
    parser.add_argument("--libero-source", type=Path, default=ROOT / "external/LIBERO")
    parser.add_argument("--g0-report", type=Path)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--cache-directory", type=Path)
    parser.add_argument("--data-directory", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--evidence-root", type=Path, default=ROOT,
                        help="Project root containing the immutable reviewed receipt, PNG and original JPEG evidence")
    parser.add_argument("--max-attempts-per-condition", type=int, default=12,
                        help="Frozen total attempt cap (9..32), including nine required successes plus failed/unknown retries")
    parser.add_argument("--stats-key", default="libero_spatial_no_noops")
    parser.add_argument("--prepare-only", action="store_true")
    print(json.dumps(run(parser.parse_args()), ensure_ascii=False), flush=True)

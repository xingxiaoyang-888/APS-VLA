"""G1: fixed 90-observation D2/D3 panel and nested 12-observation exact teacher.

Formal execution requires a passed, version-matched G0 report. --prepare-only
only freezes the already registered observation IDs and prints query bounds.
No training, checkpoint writes, simulator runs or research claims occur here.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_observation_panel(protocol, *, repeat_seed: int) -> dict:
    from cti_vla.data.libero import load_manifest
    from cti_vla.labeling.sampling import named_seed
    panels = protocol.payload["panels"]
    diagnostic = load_manifest(protocol.path.parent / panels["diagnostic_90"]["path"])
    teacher = load_manifest(protocol.path.parent / panels["teacher_12"]["path"])
    if diagnostic.sample_count != 90 or teacher.sample_count != 12 or not set(teacher.episode_ids) <= set(diagnostic.episode_ids):
        raise ValueError("G1 requires the frozen 90-observation panel and nested 12-observation panel")
    if diagnostic.split != "train" or teacher.split != "train" or not set(teacher.samples) <= set(diagnostic.samples):
        raise ValueError("G1 panels must be nested registered train samples")
    records = []
    for sample in diagnostic.samples:
        episode, registered = protocol.require_sample(sample.episode_id, sample.step_index, split="train")
        if registered != sample:
            raise ValueError("diagnostic panel sample disagrees with authoritative train manifest")
        records.append({**asdict(sample), "task_name": episode.task_name,
                        "source_shard": episode.source_shard, "record_index": episode.record_index,
                        "is_last_step": sample.step_index == episode.num_steps - 1,
                        "exact_selection": sample.sample_id in {s.sample_id for s in teacher.samples}})
    tasks = sorted({r["task_name"] for r in records})
    if len(tasks) != 10:
        raise ValueError("diagnostic panel must cover all ten tasks")
    repeat_ids = set()
    for index, task in enumerate(tasks):
        stage = ("early", "middle", "late")[index % 3]
        candidates = [r for r in records if r["task_name"] == task and r["stage"] == stage]
        repeat_ids.add(min(candidates, key=lambda r: named_seed(repeat_seed, "repeat", r["sample_id"]))["sample_id"])
    for row in records:
        row["repeatability"] = row["sample_id"] in repeat_ids
    return {"diagnostic_manifest_sha256": panels["diagnostic_90"]["sha256"],
            "teacher_manifest_sha256": panels["teacher_12"]["sha256"],
            "diagnostic_selection_seed": panels["diagnostic_90"]["selection_seed"],
            "teacher_selection_seed": panels["teacher_12"]["selection_seed"],
            "repeat_selection_seed": repeat_seed,
            "repeat_rule": "one per sorted task; early/middle/late cyclic; minimum named hash within task/stage",
            "observations": records}


def _source_snapshot() -> dict:
    paths = sorted((ROOT / "src/cti_vla").rglob("*.py")) + [Path(__file__)]
    return {str(path.relative_to(ROOT).as_posix()): sha256(path) for path in paths}


def _configure_cache(path: Path, checkpoint: Path) -> None:
    path, checkpoint = path.resolve(), checkpoint.resolve()
    if path == checkpoint or checkpoint in path.parents:
        raise ValueError("HF runtime cache must be outside the immutable checkpoint")
    for child in (path, path / "hub", path / "modules"):
        child.mkdir(parents=True, exist_ok=True)
    os.environ.update({"HF_HOME": str(path), "HF_HUB_CACHE": str(path / "hub"),
                       "HF_MODULES_CACHE": str(path / "modules"), "HF_HUB_OFFLINE": "1",
                       "TRANSFORMERS_OFFLINE": "1", "TOKENIZERS_PARALLELISM": "false"})


def _summary(output: Path, config_sha: str, expected: list[dict]) -> dict:
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, read_query_journal_ledger
    completed, failed = [], []
    for observation in expected:
        path = output / "observations" / f"{observation['sample_id']}.json"
        if not path.exists():
            continue
        row = json.loads(path.read_text(encoding="utf-8"))
        if row.get("config_sha256") != config_sha or row.get("observation") != observation:
            raise ValueError("saved observation has incompatible config or panel identity")
        (completed if row["status"] == "completed" else failed).append(row)
    # Journals are authoritative for teacher cost, including hard-killed
    # observations whose finally/result file never ran.
    costs = []
    completed_ids = {row["observation"]["sample_id"] for row in completed}
    for observation in expected:
        path = output / "queries" / f"{observation['sample_id']}.jsonl"
        if path.exists():
            costs.append(read_query_journal_ledger(path, expected_fields={"config_sha256": config_sha, "sample": observation}))
        elif observation["sample_id"] in completed_ids:
            raise ValueError("completed observation is missing its authoritative query journal")
    total_keys = ("api_calls_attempted", "sample_forwards_attempted", "sample_forwards_completed",
                  "failed_calls", "interrupted_calls_unknown_completion", "cache_hits", "known_policy_seconds", "journal_bytes")
    method_groups = defaultdict(list)
    for row in completed:
        for name, results in row.get("exact_selection", {}).get("methods", {}).items():
            for result in results:
                for group_kind, group in (("task", row["observation"]["task_name"]),
                                          ("stage", row["observation"]["stage"]),
                                          ("last_step", str(row["observation"]["is_last_step"]))):
                    method_groups[(name, result["keep_count"], group_kind, group)].append(result["error"]["mean_l1"])
    attempt_costs = []
    for path in sorted((output / "observation_attempts").glob("*.json")):
        attempt = json.loads(path.read_text(encoding="utf-8"))
        if attempt.get("config_sha256") != config_sha:
            raise ValueError("observation attempt belongs to an incompatible config")
        attempt_costs.append(attempt)
    cost = {key: sum(item[key] for item in costs) for key in total_keys}
    cost["policy_seconds_total"] = (None if cost["interrupted_calls_unknown_completion"]
                                      else cost["known_policy_seconds"])
    cost["reconciled_query_journals"] = len(costs)
    for key in ("vision_seconds", "preprocessing_seconds", "wall_seconds_this_attempt", "cpu_seconds_this_attempt"):
        cost[key] = sum(item.get(key, 0.0) for item in attempt_costs)
    cost["recorded_observation_attempts"] = len(attempt_costs)
    cost["interrupted_nonquery_costs"] = "A hard process kill before attempt finalization leaves wall/vision/CPU cost unknown; durable teacher start events still record attempted calls. Cluster job usage must reconcile such attempts."
    finalization_path = output / "finalization.json"
    finalized = False
    if finalization_path.exists():
        receipt = json.loads(finalization_path.read_text(encoding="utf-8"))
        finalized = (receipt.get("config_sha256") == config_sha and receipt.get("status") == "verified"
                     and receipt.get("checkpoint_unchanged") is True
                     and receipt.get("observation_files") == _observation_hashes(output, expected)
                     and receipt.get("query_journals") == _journal_hashes(output, expected))
        if not finalized:
            raise ValueError("G1 finalization receipt no longer matches observation results/config")
    all_complete = len(completed) == len(expected)
    status = "completed" if all_complete and finalized else "awaiting_final_verification" if all_complete else "partial"
    summary = {"stage": "G1", "status": status,
               "config_sha256": config_sha, "completed_observations": len(completed),
               "expected_observations": len(expected), "failed_observations": len(failed),
               "cost": cost,
               "exact_error_groups": [{"method": k[0], "keep_count": k[1], "group_kind": k[2],
                                       "group": k[3], "n": len(v), "mean_l1": sum(v) / len(v)}
                                      for k, v in sorted(method_groups.items())],
               "g1_go_no_go": "requires scientific review; no automatic success or improvement claim",
               "limitations": "Offline frozen-teacher normalized-action diagnostics. No closed-loop success or deployment latency result. D1 legal alternative instructions and optional smaller-step search are separate preregistered experiments."}
    atomic_json(output / "summary.json", summary)
    return summary


def _observation_hashes(output: Path, expected: list[dict]) -> dict:
    return {str(row["sample_id"]): sha256(output / "observations" / f"{row['sample_id']}.json")
            for row in expected if (output / "observations" / f"{row['sample_id']}.json").exists()}


def _journal_hashes(output: Path, expected: list[dict]) -> dict:
    return {str(row["sample_id"]): sha256(output / "queries" / f"{row['sample_id']}.jsonl")
            for row in expected if (output / "queries" / f"{row['sample_id']}.jsonl").exists()}


def _finalize(output: Path, config_sha: str, expected: list[dict], verified_checkpoint) -> None:
    from cti_vla.evaluation.teacher_diagnostics import atomic_json
    for row in expected:
        path = output / "observations" / f"{row['sample_id']}.json"
        result = json.loads(path.read_text(encoding="utf-8"))
        if result.get("status") != "completed" or result.get("config_sha256") != config_sha:
            raise ValueError("cannot finalize incomplete observations")
        if not (output / "queries" / f"{row['sample_id']}.jsonl").exists():
            raise ValueError("cannot finalize without all authoritative query journals")
    atomic_json(output / "finalization.json", {"status": "verified", "config_sha256": config_sha,
                "checkpoint_unchanged": True, "checkpoint_verification": asdict(verified_checkpoint),
                "observation_files": _observation_hashes(output, expected),
                "query_journals": _journal_hashes(output, expected),
                "created_utc": datetime.now(timezone.utc).isoformat()})


def run(args) -> dict:
    from cti_vla.data.experiment_protocol import load_experiment_protocol, write_frozen_json
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest
    from cti_vla.evaluation.teacher_diagnostics import DIAGNOSTICS_VERSION, json_signature, require_g0
    from cti_vla.labeling.sampling import SAMPLING_VERSION
    from cti_vla.models.abstraction.packing import PACKING_VERSION

    protocol = load_experiment_protocol(args.protocol)
    panel = build_observation_panel(protocol, repeat_seed=args.repeat_seed)
    args.output.mkdir(parents=True, exist_ok=True)
    write_frozen_json(args.output / "observation_panel.json", panel)
    if args.prepare_only:
        return {"status": "prepared_only", "gpu_calls": 0, "observations": 90, "exact_observations": 12,
                "repeat_observations": 10, "independent_query_upper_bounds":
                {"D2": 7650, "D3": 7200, "exact_and_controls": 10968, "repeatability_extra": 20,
                 "total_before_cross_panel_cache_reuse": 25838}, "output": str(args.output)}
    if any(value is None for value in (args.checkpoint, args.cache_directory, args.data_directory, args.g0_report)):
        raise ValueError("formal execution requires --checkpoint, --cache-directory, --data-directory and --g0-report")
    from cti_vla.evaluation.libero_runtime import LIBERO_EVAL_INPUT_VERSION
    checkpoint_manifest = load_checkpoint_manifest(args.asset_manifest)
    g0 = json.loads(args.g0_report.read_text(encoding="utf-8"))
    require_g0(g0, model_revision=checkpoint_manifest.revision,
               input_version=LIBERO_EVAL_INPUT_VERSION, packing_version=PACKING_VERSION)
    if args.checkpoint.resolve() == args.output.resolve() or args.checkpoint.resolve() in args.output.resolve().parents:
        raise ValueError("results must not be written inside the checkpoint")
    config = {"schema_version": 1, "stage": "G1", "diagnostics_version": DIAGNOSTICS_VERSION,
              "sampling_version": SAMPLING_VERSION, "input_version": LIBERO_EVAL_INPUT_VERSION,
              "packing_version": PACKING_VERSION, "model_revision": checkpoint_manifest.revision,
              "asset_manifest_sha256": sha256(args.asset_manifest), "g0_report_sha256": sha256(args.g0_report),
              "protocol_signature": protocol.payload["content_signature"], "panel_sha256": json_signature(panel),
              "set_seed": args.set_seed, "random_seeds": [17, 23, 41], "noise_tolerance": args.noise_tolerance,
              "repeat_seed": args.repeat_seed, "per_observation_query_cap": args.query_cap,
              "stats_key": args.stats_key, "source_snapshot": _source_snapshot(),
              "action_error": "FP32 mean normalized absolute error over 8x7", "batch_size": 1,
              "D2": "full plus anchored random/uniform256/128,16shared candidates",
              "D3": "candidate-only fixed-full-camera-mean replacement within actual packed S"}
    config_sha = json_signature(config)
    write_frozen_json(args.output / "config.json", config)
    observations = panel["observations"]
    prior = _summary(args.output, config_sha, observations)
    pending = []
    for row in observations:
        path = args.output / "observations" / f"{row['sample_id']}.json"
        if not path.exists() or json.loads(path.read_text(encoding="utf-8"))["status"] != "completed":
            pending.append(row)
    if args.observation_limit is not None:
        pending = pending[:args.observation_limit]
    if not pending:
        if prior["status"] != "completed":
            # Completed observation JSONs alone do not finish a run. A previous
            # process may have died or failed the final immutable-weight check.
            from cti_vla.evaluation.checkpoint_manifest import verify_checkpoint_directory
            verified = verify_checkpoint_directory(args.checkpoint, checkpoint_manifest)
            _finalize(args.output, config_sha, observations, verified)
        return _summary(args.output, config_sha, observations)

    _configure_cache(args.cache_directory, args.checkpoint)
    import torch
    import transformers
    from transformers import AutoProcessor
    from cti_vla.data.sequence_example import iter_libero_examples
    from cti_vla.evaluation.checkpoint_manifest import verify_checkpoint_directory
    from cti_vla.evaluation.libero_runtime import prepare_rlds_eval_inputs
    from cti_vla.evaluation.teacher_diagnostics import ActionQueryCache, atomic_json, run_exact_selection, run_intervention_panel, run_repeatability, tensor_signature
    from cti_vla.labeling.sampling import fixed_anchor_panel
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy

    if torch.cuda.device_count() != 1:
        raise RuntimeError("formal G1 requires exactly one scheduler-assigned visible GPU")
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    before = verify_checkpoint_directory(args.checkpoint, checkpoint_manifest)
    components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
    vla = components.vla
    processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
    keys = [key for key in vla.norm_stats if "libero_spatial" in key]
    stats_key = args.stats_key or (keys[0] if len(keys) == 1 else None)
    if stats_key not in vla.norm_stats:
        raise ValueError("supply --stats-key identifying the Spatial checkpoint statistics")
    policy = OpenVLAOFTTokenPolicy(vla, components.action_head, components.proprio_projector,
                                  num_patches_full=components.num_patches_full)
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, text=True, capture_output=True, check=False)
    attempt = {"created_utc": datetime.now(timezone.utc).isoformat(), "config_sha256": config_sha,
               "git_commit": git.stdout.strip() if git.returncode == 0 else None, "git_status": dirty.stdout,
               "checkpoint_verified": asdict(before), "stats_key": stats_key,
               "hardware": {"gpu": torch.cuda.get_device_name(device), "cpu_count": os.cpu_count()},
               "runtime": {"python": platform.python_version(), "torch": torch.__version__,
                           "transformers": transformers.__version__, "cuda": torch.version.cuda},
               "slurm_job_id": os.environ.get("SLURM_JOB_ID"), "requested_observations": len(pending)}
    attempt_path = args.output / "attempts" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".json")
    atomic_json(attempt_path, attempt)
    by_shard = defaultdict(lambda: defaultdict(list))
    for row in pending:
        by_shard[row["source_shard"]][row["record_index"]].append(row)
    for shard, wanted in sorted(by_shard.items()):
        found = set()
        for episode in iter_libero_examples(args.data_directory / shard):
            if episode.record_index not in wanted:
                continue
            found.add(episode.record_index)
            for row in wanted[episode.record_index]:
                if episode.episode_id != row["episode_id"]:
                    raise ValueError("decoded episode hash disagrees with registered content ID")
                protocol.require_sample(episode.episode_id, row["step_index"], split="train")
                output_path = args.output / "observations" / f"{row['sample_id']}.json"
                result = {"status": "failed", "config_sha256": config_sha, "observation": row}
                oracle = None
                started = time.perf_counter()
                cpu_started = time.process_time()
                observation_attempt_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
                try:
                    torch.cuda.reset_peak_memory_stats(device)
                    inputs = prepare_rlds_eval_inputs(episode, row["step_index"], processor,
                                                     vla.norm_stats[stats_key]["proprio"], device=device, dtype=torch.bfloat16)
                    if inputs["inputs_version"] != LIBERO_EVAL_INPUT_VERSION:
                        raise ValueError("formal preprocessing version mismatch")
                    torch.cuda.synchronize(device)
                    result["preprocessing_seconds"] = time.perf_counter() - started
                    vision_started = time.perf_counter()
                    with torch.no_grad():
                        projected = vla._process_vision_features(inputs["pixel_values"], None, False)
                    torch.cuda.synchronize(device)
                    result["vision_seconds"] = time.perf_counter() - vision_started
                    if projected.shape != (1, 512, int(vla.llm_dim)):
                        raise ValueError("expected two camera-major 256-patch projected sequences")
                    identity = {"config_sha256": config_sha, "sample": row,
                                "input_sha256": tensor_signature({k: inputs[k] for k in
                                    ("pixel_values", "input_ids", "attention_mask", "normalized_proprio")})}
                    def forward(visual, indices):
                        return policy.forward_from_full_tokens(visual, inputs["normalized_proprio"],
                            input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"], retained_indices=indices)
                    prompt_length = inputs["input_ids"].shape[1] + int(inputs["input_ids"][0, -1] != 29871)
                    oracle = ActionQueryCache(projected, forward, identity=identity,
                                              journal_path=args.output / "queries" / f"{row['sample_id']}.jsonl",
                                              max_sample_forwards=args.query_cap, sequence_overhead_tokens=prompt_length + 58)
                    fixed = fixed_anchor_panel(row["sample_id"], seed=args.set_seed)
                    result["interventions"] = run_intervention_panel(oracle, fixed, noise_tolerance=args.noise_tolerance)
                    if row["exact_selection"]:
                        result["exact_selection"] = run_exact_selection(oracle, sample_id=row["sample_id"], seed=args.set_seed)
                    if row["repeatability"]:
                        result["repeatability"] = run_repeatability(oracle, fixed[0].candidate_indices[0])
                    result["status"] = "completed"
                except Exception as error:
                    result["error"] = f"{type(error).__name__}: {error}"
                    raise
                finally:
                    result["wall_seconds_this_attempt"] = time.perf_counter() - started
                    result["cpu_seconds_this_attempt"] = time.process_time() - cpu_started
                    result["peak_allocated_bytes"] = torch.cuda.max_memory_allocated(device)
                    if oracle is not None:
                        result["cost"] = oracle.ledger()
                    elif output_path.exists():
                        # A failed preprocessing/cache-identity retry issued no
                        # new teacher calls; retain already charged query cost.
                        previous = json.loads(output_path.read_text(encoding="utf-8"))
                        if previous.get("config_sha256") == config_sha and "cost" in previous:
                            result["cost"] = previous["cost"]
                    # Preserve failed/retried input/vision cost instead of
                    # overwriting it when this observation eventually succeeds.
                    atomic_json(args.output / "observation_attempts" / f"{row['sample_id']}_{observation_attempt_id}.json",
                                {key: value for key, value in result.items()
                                 if key not in ("interventions", "exact_selection", "repeatability")})
                    atomic_json(output_path, result)
                    _summary(args.output, config_sha, observations)
                print(json.dumps({"sample_id": row["sample_id"], "status": result["status"],
                                  "teacher_sample_forwards": result["cost"]["sample_forwards_completed"]}), flush=True)
            if found == set(wanted):
                break
        if found != set(wanted):
            raise ValueError(f"registered episodes missing from shard {shard}")
    after = verify_checkpoint_directory(args.checkpoint, checkpoint_manifest)
    if before != after:
        raise RuntimeError("immutable checkpoint changed during G1")
    attempt.update(status="completed", checkpoint_unchanged=True)
    atomic_json(attempt_path, attempt)
    # Bounded invocations remain partial until every registered observation is
    # complete and a successful final checkpoint verification has been saved.
    current = _summary(args.output, config_sha, observations)
    if current["completed_observations"] == len(observations):
        _finalize(args.output, config_sha, observations, after)
    return _summary(args.output, config_sha, observations)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")
    parser.add_argument("--asset-manifest", type=Path, default=ROOT / "configs/assets/openvla_oft_libero_spatial.json")
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--cache-directory", type=Path)
    parser.add_argument("--data-directory", type=Path)
    parser.add_argument("--g0-report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--stats-key")
    parser.add_argument("--set-seed", type=int, default=517)
    parser.add_argument("--repeat-seed", type=int, default=617)
    parser.add_argument("--noise-tolerance", type=float, default=1e-6)
    parser.add_argument("--query-cap", type=int, default=1100, help="Attempted B=1 calls per observation, including failed retries")
    parser.add_argument("--observation-limit", type=int, help="Bound new observations this invocation; restart resumes full registered panel")
    args = parser.parse_args()
    if args.noise_tolerance < 0 or args.query_cap < 1081 or (args.observation_limit is not None and args.observation_limit <= 0):
        parser.error("noise tolerance must be nonnegative; query cap >=1081; observation limit positive")
    print(json.dumps(run(args), ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()

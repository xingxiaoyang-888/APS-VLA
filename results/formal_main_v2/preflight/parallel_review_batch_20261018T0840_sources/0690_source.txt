"""G3 server-only lightweight selector training with frozen packed validation.

Requires complete detached train/effective-validation caches and a reviewed G1
go report. Only scorer/condition parameters enter AdamW. Checkpoints are saved
to the explicitly supplied server directory, never copied to the local project.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import time

ROOT = Path(__file__).resolve().parents[1]


def run(args):
    if os.name == "nt":
        raise RuntimeError("formal training/checkpoint writes must run on the server; local CPU tests use temporary synthetic models only")
    from cti_vla.data.experiment_protocol import load_experiment_protocol
    from cti_vla.data.identity import file_sha256
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation.libero_runtime import LIBERO_EVAL_INPUT_VERSION
    from cti_vla.evaluation.teacher_diagnostics import atomic_json
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    from cti_vla.training.offline import OfflineDataset, OfflineTrainConfig, require_g1, seed_training, train_offline

    protocol = load_experiment_protocol(args.protocol)
    asset = load_checkpoint_manifest(args.asset_manifest)
    g1 = json.loads(args.g1_report.read_text(encoding="utf-8"))
    require_g1(g1, model_revision=asset.revision, input_version=LIBERO_EVAL_INPUT_VERSION,
               packing_version=PACKING_VERSION, protocol_signature=protocol.payload["content_signature"])
    train = OfflineDataset(args.train_index, protocol, split="train")
    validation = OfflineDataset(args.validation_index, protocol, split="validation")
    for dataset in (train, validation):
        build = dataset.index.get("build_config", {})
        if build.get("g1_report_sha256") != file_sha256(args.g1_report):
            raise ValueError("cache was not generated under this reviewed G1 go report")
        if build.get("model_revision") != asset.revision or build.get("input_version") != LIBERO_EVAL_INPUT_VERSION or build.get("packing_version") != PACKING_VERSION:
            raise ValueError("training cache model/input/packing versions differ from validation policy")
        if build.get("normalization_stats_sha256") != file_sha256(args.checkpoint / "dataset_statistics.json"):
            raise ValueError("cached proprio normalization differs from the validation policy checkpoint")
        runtime_sources = [*sorted((ROOT / "src/cti_vla/models").rglob("*.py")), ROOT / "src/cti_vla/evaluation/libero_runtime.py"]
        if any(build.get("source_files", {}).get(path.relative_to(ROOT).as_posix()) != file_sha256(path) for path in runtime_sources):
            raise ValueError("model/input runtime code differs from the feature-label cache producer")
    if train.index["build_config"]["source_files"] != validation.index["build_config"]["source_files"]:
        raise ValueError("train and validation caches must share the frozen producer source snapshot")
    first = train.observation(0)
    if first.batch.visual.shape[1] != 512 or first.batch.normalized_proprio.shape[1] != 8:
        raise ValueError("formal Spatial training requires512 visual tokens and8 normalized proprio values")
    checkpoint = args.checkpoint.resolve()
    checkpoint_directory, hf = args.checkpoint_directory.resolve(), args.cache_directory.resolve()
    for target in (checkpoint_directory, hf, args.output.resolve()):
        if target == checkpoint or checkpoint in target.parents:
            raise ValueError("training outputs/runtime caches must be outside immutable VLA weights")
    for path in (hf, hf / "hub", hf / "modules"):
        path.mkdir(parents=True, exist_ok=True)
    os.environ.update(HF_HOME=str(hf), HF_HUB_CACHE=str(hf / "hub"), HF_MODULES_CACHE=str(hf / "modules"),
                      HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    import torch
    import transformers
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
    from cti_vla.selection import ConditionalInfluenceEstimator

    if torch.cuda.device_count() != 1:
        raise RuntimeError("G3 requires exactly one scheduler-assigned visible GPU")
    before = verify_checkpoint_directory(checkpoint, asset)
    device = torch.device("cuda:0")
    components = load_openvla_oft_components(checkpoint, device=device, use_minimal_prismatic_compat=True)
    vla = components.vla
    policy = OpenVLAOFTTokenPolicy(vla, components.action_head, components.proprio_projector,
                                  num_patches_full=components.num_patches_full)
    config = OfflineTrainConfig(seed=args.seed, max_epochs=args.max_epochs,
                                effective_batch_records=16, learning_rate=args.learning_rate,
                                weight_decay=1e-4, hidden_dim=256)
    seed_training(config.seed)
    scorer = ConditionalInfluenceEstimator(first.batch.visual.shape[-1], first.batch.instruction_embeddings.shape[-1],
                                           first.batch.normalized_proprio.shape[-1], hidden_dim=config.hidden_dim,
                                           num_cameras=2, patches_per_camera=256, max_instruction_tokens=128)
    identity = {"model_revision": asset.revision, "input_version": LIBERO_EVAL_INPUT_VERSION,
                "packing_version": PACKING_VERSION, "protocol_signature": protocol.payload["content_signature"],
                "g1_report_sha256": file_sha256(args.g1_report),
                "source_files": {path.relative_to(ROOT).as_posix(): file_sha256(path)
                                 for path in [*sorted((ROOT / "src/cti_vla").rglob("*.py")), Path(__file__)]},
                "scorer_dimensions": {"visual": scorer.token_dim, "language": scorer.language_dim,
                                      "proprio": scorer.proprio_dim, "hidden": 256},
                "runtime": {"python": platform.python_version(), "torch": torch.__version__,
                            "transformers": transformers.__version__, "cuda": torch.version.cuda}}
    validation_calls = 0
    def forward_validation(observation, indices):
        nonlocal validation_calls
        if policy.training or any(p.requires_grad for p in policy.parameters()):
            raise RuntimeError("validation policy must remain frozen and eval-only")
        validation_calls += 1
        attempt["validation_sample_forwards_started"] = validation_calls
        atomic_json(attempt_path, attempt)
        action = policy.forward_from_full_tokens(observation.batch.visual,
                    observation.batch.normalized_proprio.to(observation.batch.visual.dtype),
                    input_ids=observation.input_ids, attention_mask=observation.attention_mask, retained_indices=indices)
        torch.cuda.synchronize(device)
        attempt["validation_sample_forwards_completed"] += 1
        atomic_json(attempt_path, attempt)
        return action
    started = time.perf_counter()
    cpu_started = time.process_time()
    attempt = {"status": "running", "seed": args.seed, "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
               "hardware": {"gpu": torch.cuda.get_device_name(device), "cpu_count": os.cpu_count()},
               "created_utc": datetime.now(timezone.utc).isoformat(), "identity": identity,
               "validation_sample_forwards_started": 0, "validation_sample_forwards_completed": 0,
               "unfinished_attempt_cost": "If the job is hard-killed, the final outstanding started query and elapsed GPU/CPU/wall time remain unknown and must be reconciled from scheduler usage.",
               "resumed": args.resume, "checkpoint_directory": str(checkpoint_directory)}
    attempt_path = args.output.parent / "training_attempts" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".json")
    atomic_json(attempt_path, attempt)
    try:
        torch.cuda.reset_peak_memory_stats(device)
        result = train_offline(scorer, train, validation, forward_validation, config=config,
                               checkpoint_directory=checkpoint_directory, run_identity=identity,
                               device=device, resume=args.resume, stop_after_epochs=args.stop_after_epochs)
        after = verify_checkpoint_directory(checkpoint, asset)
        if before != after:
            raise RuntimeError("immutable base checkpoint changed during scorer training")
        result.update(stage="G3", seed=args.seed, frozen_base_unchanged=True,
                      train_observations=len(train.entries), validation_observations=len(validation.entries),
                      parameters_trained=sum(p.numel() for p in scorer.parameters() if p.requires_grad),
                      validation_rule="task-macro normalized packed E at128; each task early/middle/late equally weighted; earlier epoch wins ties",
                      checkpoint_storage="server only", scientific_status="training output; no test, closed-loop or speedup claims")
        for kind in ("latest", "best"):
            path = result.get(f"{kind}_checkpoint")
            if path is not None:
                result[f"{kind}_checkpoint_sha256"] = file_sha256(path)
        atomic_json(args.output, result)
        attempt["status"] = result["status"]
        return result
    except Exception as error:
        attempt.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        torch.cuda.synchronize(device)
        attempt.update(wall_seconds=time.perf_counter() - started,
                       cpu_seconds=time.process_time() - cpu_started,
                       validation_sample_forwards_this_attempt=validation_calls,
                       peak_allocated_bytes=torch.cuda.max_memory_allocated(device),
                       partial_epoch_note="Failed work after the last completed epoch is charged in this attempt and recomputed on resume.")
        atomic_json(attempt_path, attempt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")
    parser.add_argument("--asset-manifest", type=Path, default=ROOT / "configs/assets/openvla_oft_libero_spatial.json")
    parser.add_argument("--train-index", type=Path, required=True)
    parser.add_argument("--validation-index", type=Path, required=True)
    parser.add_argument("--g1-report", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--cache-directory", type=Path, required=True)
    parser.add_argument("--checkpoint-directory", type=Path, required=True, help="Server destination for latest/best scorer, optimizer and RNG checkpoints")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, choices=(17, 23, 41), default=17)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--max-epochs", type=int, default=30)
    parser.add_argument("--stop-after-epochs", type=int)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.stop_after_epochs is not None and args.stop_after_epochs <= 0:
        parser.error("stop-after-epochs must be positive")
    result = run(args)
    print(json.dumps({k: result[k] for k in ("status", "best_epoch", "best_validation_mean_l1", "completed_epochs", "optimizer_steps")}), flush=True)


if __name__ == "__main__":
    main()

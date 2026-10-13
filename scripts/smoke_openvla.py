"""One real RLDS observation: official dense parity and physical packing smoke.

Single unsmoothed timings diagnose execution only; they are not benchmarks or
observation-to-action latency claims. No model/checkpoint file is modified.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time


def configure_cache(path: Path, checkpoint: Path) -> None:
    path = path.resolve()
    checkpoint = checkpoint.resolve()
    if path == checkpoint or checkpoint in path.parents:
        raise ValueError("Hugging Face cache must be outside the immutable checkpoint")
    for child in (path, path / "hub", path / "modules"):
        child.mkdir(parents=True, exist_ok=True)
    os.environ.update({
        "HF_HOME": str(path), "HF_HUB_CACHE": str(path / "hub"),
        "HF_MODULES_CACHE": str(path / "modules"), "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1", "TOKENIZERS_PARALLELISM": "false",
    })


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_revision() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1],
            text=True, capture_output=True, check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _timed_cuda(function, device):
    import torch
    torch.cuda.synchronize(device)
    torch.cuda.reset_peak_memory_stats(device)
    started = time.perf_counter()
    output = function()
    torch.cuda.synchronize(device)
    return output, {
        "seconds": time.perf_counter() - started,
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
    }


def _official_normalized(components, projected, inputs):
    """Use the checkpoint's original text/prefix/regression methods as reference."""
    import numpy as np
    import torch
    vla = components.vla
    ids = inputs["input_ids"]
    attention = inputs["attention_mask"]
    if not bool((ids[:, -1] == 29871).all()):
        ids = torch.cat((ids, torch.full((1, 1), 29871, device=ids.device, dtype=ids.dtype)), dim=1)
        attention = torch.cat((attention, torch.ones((1, 1), device=ids.device, dtype=attention.dtype)), dim=1)
    labels = torch.full_like(ids, -100)
    full_ids, full_attention = vla._prepare_input_for_action_prediction(ids, attention)
    labels = vla._prepare_labels_for_action_prediction(labels, full_ids)
    embeddings = vla.get_input_embeddings()(full_ids)
    action_mask = vla._process_action_masks(labels)
    prefix = vla._process_proprio_features(projected, inputs["normalized_proprio"], components.proprio_projector)
    normalized, hidden = vla._regression_or_discrete_prediction(
        embeddings, action_mask, prefix, full_attention, labels,
        components.num_patches_full + 1, ids.shape[1] - 1, components.action_head,
    )
    if hidden.shape != (1, 56, int(vla.llm_dim)):
        raise RuntimeError("official action hidden states have the wrong shape")
    actions = torch.from_numpy(np.asarray(normalized, dtype=np.float32)).to(projected.device).unsqueeze(0)
    if actions.shape != (1, 8, 7) or not bool(torch.isfinite(actions).all()):
        raise RuntimeError("official reference produced invalid normalized actions")
    return actions


def run(args: argparse.Namespace) -> dict:
    configure_cache(args.cache_directory, args.checkpoint)
    import numpy as np
    import torch
    import transformers
    from transformers import AutoProcessor

    from cti_vla.data.sequence_example import iter_libero_examples
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation.conditional_smoke import run_conditional_smoke
    from cti_vla.labeling import LabelProvenance
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    from cti_vla.models.openvla_oft_inputs import prepare_rlds_inputs
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
    from cti_vla.models.openvla_oft_runtime_compat import TRANSFORMERS_OFT_COMMIT, OFT_SDPA_FORWARD_SHA256

    if args.record_index < 0 or args.step_index < 0:
        raise ValueError("record/step index must be non-negative")
    if torch.cuda.device_count() != 1:
        raise RuntimeError("expose exactly one GPU via CUDA_VISIBLE_DEVICES")
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    manifest = load_checkpoint_manifest(args.manifest)
    print("Verifying checkpoint hashes before model load...", flush=True)
    before = verify_checkpoint_directory(args.checkpoint, manifest)
    episode = next((item for item in iter_libero_examples(args.shard) if item.record_index == args.record_index), None)
    if episode is None or args.step_index >= episode.num_steps:
        raise ValueError("requested RLDS episode/observation was not found")
    components = load_openvla_oft_components(
        args.checkpoint, device=device, use_minimal_prismatic_compat=True,
    )
    vla = components.vla
    processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
    keys = [key for key in vla.norm_stats if "libero_spatial" in key]
    stats_key = args.stats_key or (keys[0] if len(keys) == 1 else None)
    if stats_key not in vla.norm_stats:
        raise ValueError("supply --stats-key identifying the checkpoint's LIBERO Spatial statistics")
    inputs = prepare_rlds_inputs(
        episode, args.step_index, processor, vla.norm_stats[stats_key]["proprio"],
        device=device, dtype=torch.bfloat16,
    )
    policy = OpenVLAOFTTokenPolicy(
        vla, components.action_head, components.proprio_projector,
        num_patches_full=components.num_patches_full,
    )
    with torch.inference_mode():
        projected, vision_timing = _timed_cuda(
            lambda: vla._process_vision_features(inputs["pixel_values"], None, False), device,
        )
        if projected.shape != (1, 512, 4096):
            raise RuntimeError(f"unexpected projected feature shape: {tuple(projected.shape)}")
        official, official_timing = _timed_cuda(lambda: _official_normalized(components, projected, inputs), device)
        rows = []
        dense = None
        for keep_count in (512, 256, 128, 64):
            # Fixed uniform camera-balanced control, not a trained selector.
            local_indices = torch.arange(keep_count // 2, device=device) * (256 // (keep_count // 2))
            indices = torch.cat((local_indices, local_indices + 256)).unsqueeze(0)
            actions, timing = _timed_cuda(
                lambda: policy.forward_from_full_tokens(
                    projected, inputs["normalized_proprio"], input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"], retained_indices=indices,
                ), device,
            )
            if actions.shape != (1, 8, 7) or not bool(torch.isfinite(actions).all()):
                raise RuntimeError(f"invalid actions at keep_count={keep_count}")
            if keep_count == 512:
                dense = actions
                max_error = float((dense.float() - official).abs().max().item())
                if max_error > args.atol:
                    raise RuntimeError(f"official/dense max absolute error {max_error} exceeds {args.atol}")
            rows.append({
                "keep_count": keep_count, "per_camera": [keep_count // 2] * 2,
                "indices": indices[0].tolist(), "action_shape": list(actions.shape),
                "normalized_actions": actions.float().cpu().tolist(),
                "mean_l1_from_dense": float((actions.float() - dense.float()).abs().mean().item()),
                **timing,
            })
    # This call deliberately leaves inference_mode: only its ephemeral scorer
    # optimization uses autograd. It does not save a trained model.
    shard_sha256 = _sha256(args.shard)
    condition_provenance = LabelProvenance(
        sample_ids=(f"{episode.episode_id}:step-{args.step_index}",), episode_ids=(episode.episode_id,),
        split="train", model_revision=manifest.revision,
        dataset_version=f"engineering-smoke-shard-sha256:{shard_sha256}",
        preprocessing_version=inputs["inputs_version"], packing_version=PACKING_VERSION,
        condition_version=f"{inputs['inputs_version']}:{stats_key}:frozen-prompt-embeddings",
        action_version="normalized-l1-8x7-v1",
    )
    print("Running conditional teacher/cache/scorer integration smoke...", flush=True)
    conditional = run_conditional_smoke(
        policy, projected, inputs, condition_provenance,
        cache_directory=args.output.parent, hidden_dim=args.scorer_hidden_dim, seed=args.seed,
    )
    print("Verifying checkpoint hashes after smoke...", flush=True)
    after = verify_checkpoint_directory(args.checkpoint, manifest)
    if before != after:
        raise RuntimeError("checkpoint changed during smoke")
    props = torch.cuda.get_device_properties(device)
    return {
        "status": "passed", "kind": "single_observation_tensor_boundary_smoke",
        "created_utc": datetime.now(timezone.utc).isoformat(), "seed": args.seed,
        "checkpoint": asdict(before), "checkpoint_path": str(args.checkpoint.resolve()),
        "checkpoint_unchanged": True, "manifest_sha256": _sha256(args.manifest),
        "code_commit": _git_revision(), "script_sha256": _sha256(Path(__file__)),
        "source_snapshot_sha256": _sha256(Path(__file__).resolve().parents[1] / "results/migration/source_snapshot.json")
            if (Path(__file__).resolve().parents[1] / "results/migration/source_snapshot.json").is_file() else None,
        "packing_version": PACKING_VERSION, "inputs_version": inputs["inputs_version"],
        "dataset": {
            "shard": str(args.shard.resolve()), "shard_sha256": shard_sha256,
            "record_index": args.record_index, "step_index": args.step_index,
            "episode_id": episode.episode_id, "num_steps": episode.num_steps,
            "episode_file_path": getattr(episode, "episode_file_path", None),
            "prompt": inputs["prompt"], "image_sizes": inputs["image_sizes"], "stats_key": stats_key,
        },
        "hardware": {"gpu": props.name, "memory_bytes": props.total_memory, "capability": list(torch.cuda.get_device_capability(device))},
        "runtime": {"python": platform.python_version(), "torch": torch.__version__, "cuda": torch.version.cuda,
                    "transformers": transformers.__version__, "transformers_oft_commit": TRANSFORMERS_OFT_COMMIT,
                    "sdpa_forward_sha256": OFT_SDPA_FORWARD_SHA256, "dtype": "bfloat16"},
        "dense_parity": {"max_abs_error": max_error, "atol": args.atol, "passed": True},
        "vision": vision_timing, "official_reference": official_timing, "budgets": rows,
        "conditional_integration": conditional,
        "timing_scope": "One call per budget from cached projected visual tokens, including packing and policy validation; CUDA synchronized. Vision measured separately. Excludes image decode, preprocessing, transfers, selector, loading and hash checks.",
        "limitations": "Not a benchmark, closed-loop success test, or validated rollout preprocessing. Processor-only RLDS images have no evaluation center crop. No speedup or policy-quality conclusion is supported.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--cache-directory", type=Path, required=True)
    parser.add_argument("--shard", type=Path, required=True)
    parser.add_argument("--record-index", type=int, default=0)
    parser.add_argument("--step-index", type=int, default=0)
    parser.add_argument("--stats-key")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--scorer-hidden-dim", type=int, default=64, help="Temporary scorer width for engineering integration only")
    parser.add_argument("--atol", type=float, default=0.002)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 0 < args.atol <= 0.002:
        parser.error("--atol must be positive and no larger than 0.002")
    checkpoint = args.checkpoint.resolve()
    output = args.output.resolve()
    if output == checkpoint or checkpoint in output.parents:
        parser.error("--output must be outside the immutable checkpoint")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = run(args)
    except Exception as exc:
        args.output.write_text(json.dumps({"status": "failed", "error": str(exc), "created_utc": datetime.now(timezone.utc).isoformat()}, indent=2), encoding="utf-8")
        raise
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": "passed", "output": str(args.output), "dense_parity": result["dense_parity"]}), flush=True)


if __name__ == "__main__":
    main()

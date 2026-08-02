"""Real single-sample OpenVLA-OFT forward and dense-reference equivalence smoke."""

from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import time


def _normalize_proprio(raw, stats):
    import numpy as np

    low = np.asarray(stats["q01"], dtype=np.float32)
    high = np.asarray(stats["q99"], dtype=np.float32)
    mask = np.asarray(stats.get("mask", np.ones_like(low, dtype=bool)), dtype=bool)
    if raw.shape != low.shape or low.shape != (8,) or not np.isfinite(low).all() or not np.isfinite(high).all():
        raise RuntimeError("checkpoint proprio statistics do not match the frozen 8D contract")
    normalized = np.where(mask, 2.0 * (raw - low) / (high - low + 1e-8) - 1.0, raw)
    return np.clip(normalized, -1.0, 1.0).astype(np.float32)


def _make_images():
    import numpy as np
    from PIL import Image

    # Deterministic non-constant images exercise both fused vision branches.
    y, x = np.mgrid[0:224, 0:224]
    first = np.stack(((x + y) % 256, (2 * x + y) % 256, (x + 3 * y) % 256), axis=-1).astype(np.uint8)
    second = np.stack(((3 * x + y) % 256, (x + 2 * y) % 256, (2 * x + 3 * y) % 256), axis=-1).astype(np.uint8)
    return Image.fromarray(first, mode="RGB"), Image.fromarray(second, mode="RGB")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--cache-directory", type=Path, required=True)
    args = parser.parse_args()

    from diwa.evaluation.smoke_openvla_oft import _configure_huggingface_cache

    _configure_huggingface_cache(args.cache_directory)

    import numpy as np
    import torch
    from transformers import AutoProcessor

    from diwa.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from diwa.evaluation.preflight import compare_action_outputs
    from diwa.models.openvla_oft_loader import load_openvla_oft_components
    from diwa.models.openvla_oft_policy import OpenVLAOFTTokenPolicy

    if torch.cuda.device_count() != 1:
        raise RuntimeError("forward smoke requires exactly one visible GPU")
    torch.cuda.set_device(0)
    torch.cuda.init()
    device = torch.device("cuda:0")
    dtype = torch.bfloat16
    baseline_allocated = torch.cuda.memory_allocated(device)
    baseline_reserved = torch.cuda.memory_reserved(device)

    manifest = load_checkpoint_manifest(args.manifest)
    before = verify_checkpoint_directory(args.checkpoint, manifest)
    components = load_openvla_oft_components(
        args.checkpoint,
        device=device,
        use_minimal_prismatic_compat=True,
    )
    vla = components.vla
    processor = AutoProcessor.from_pretrained(
        args.checkpoint,
        trust_remote_code=True,
        local_files_only=True,
    )
    prompt = "In: What action should the robot take to move the object to the target?\nOut:"
    image_a, image_b = _make_images()
    primary = processor(prompt, image_a, return_tensors="pt")
    wrist = processor(prompt, image_b, return_tensors="pt")
    pixel_values = torch.cat((primary["pixel_values"], wrist["pixel_values"]), dim=1).to(
        device=device, dtype=dtype
    )
    input_ids = primary["input_ids"].to(device=device)
    attention_mask = primary["attention_mask"].to(device=device)
    if input_ids.shape[0] != 1 or not bool((attention_mask != 0).all()):
        raise RuntimeError("processor produced an unsupported padded or batched prompt")

    norm_stats = getattr(vla, "norm_stats", None)
    valid_stats_keys = [
        key for key, value in (norm_stats or {}).items()
        if isinstance(key, str) and "libero_spatial" in key and isinstance(value, dict)
    ]
    if len(valid_stats_keys) != 1:
        raise RuntimeError(f"expected exactly one LIBERO Spatial statistics key, got {valid_stats_keys}")
    stats_key = valid_stats_keys[0]
    proprio_stats = norm_stats[stats_key]["proprio"]
    low = np.asarray(proprio_stats["q01"], dtype=np.float32)
    high = np.asarray(proprio_stats["q99"], dtype=np.float32)
    raw_proprio = low + 0.37 * (high - low)
    normalized_proprio = torch.from_numpy(_normalize_proprio(raw_proprio, proprio_stats)).to(
        device=device, dtype=dtype
    ).unsqueeze(0)

    # Reproduce the official OFT input construction exactly, including the assistant-empty token.
    if not bool(torch.all(input_ids[:, -1] == 29871)):
        input_ids = torch.cat((input_ids, torch.full((1, 1), 29871, device=device, dtype=input_ids.dtype)), dim=1)
        attention_mask = torch.cat((attention_mask, torch.ones((1, 1), device=device, dtype=attention_mask.dtype)), dim=1)
    labels = torch.full_like(input_ids, -100)
    num_prompt_tokens = input_ids.shape[-1] - 1
    full_ids, full_attention = vla._prepare_input_for_action_prediction(input_ids, attention_mask)
    labels = vla._prepare_labels_for_action_prediction(labels, full_ids)
    input_embeddings = vla.get_input_embeddings()(full_ids)
    action_mask = vla._process_action_masks(labels)
    language_embeddings = input_embeddings[~action_mask].reshape(1, -1, input_embeddings.shape[-1])
    projected_patches = vla._process_vision_features(pixel_values, language_embeddings, False)
    projected_patches_with_proprio = vla._process_proprio_features(
        projected_patches, normalized_proprio, components.proprio_projector
    )
    if projected_patches.shape != (1, components.num_patches_full, int(vla.llm_dim)):
        raise RuntimeError(f"unexpected projected patch shape: {tuple(projected_patches.shape)}")

    # One official full-retention reference call. It is intentionally isolated and measured.
    torch.cuda.synchronize(device)
    torch.cuda.reset_peak_memory_stats(device)
    reference_start = time.perf_counter()
    with torch.inference_mode():
        official_normalized, official_hidden = vla._regression_or_discrete_prediction(
            input_embeddings,
            action_mask,
            projected_patches_with_proprio,
            full_attention,
            labels,
            components.num_patches_full + 1,
            num_prompt_tokens,
            components.action_head,
        )
    torch.cuda.synchronize(device)
    reference_seconds = time.perf_counter() - reference_start
    reference_peak = torch.cuda.max_memory_allocated(device)
    official_normalized = torch.from_numpy(np.asarray(official_normalized, dtype=np.float32)).to(device=device)
    if tuple(official_normalized.shape) != (8, 7) or official_hidden.shape != (1, 56, int(vla.llm_dim)):
        raise RuntimeError("official reference returned an invalid action/hidden shape")

    del official_hidden, language_embeddings, input_embeddings, labels, action_mask
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(device)

    policy = OpenVLAOFTTokenPolicy(
        vla,
        components.action_head,
        components.proprio_projector,
        num_patches_full=components.num_patches_full,
    ).eval()
    forward_start = time.perf_counter()
    with torch.inference_mode():
        diwa_normalized = policy.forward_from_tokens(
            projected_patches,
            normalized_proprio,
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
    torch.cuda.synchronize(device)
    forward_seconds = time.perf_counter() - forward_start
    forward_peak = torch.cuda.max_memory_allocated(device)
    comparison = compare_action_outputs(
        official_normalized.unsqueeze(0), diwa_normalized, atol=5e-3
    )
    if not comparison.passed:
        raise RuntimeError(f"dense official/DIWA action mismatch: {comparison}")

    result = {
        "checkpoint_revision": before.revision,
        "prompt_tokens_before_action": int(num_prompt_tokens),
        "pixel_values_shape": list(pixel_values.shape),
        "projected_patches_shape": list(projected_patches.shape),
        "num_patches_full": components.num_patches_full,
        "normalized_proprio_shape": list(normalized_proprio.shape),
        "official_action_shape": list(official_normalized.unsqueeze(0).shape),
        "diwa_action_shape": list(diwa_normalized.shape),
        "comparison": comparison.__dict__,
        "official_reference_seconds": reference_seconds,
        "official_reference_peak_allocated_bytes": reference_peak,
        "diwa_forward_seconds": forward_seconds,
        "diwa_forward_peak_allocated_bytes": forward_peak,
    }
    print("FORWARD_SMOKE_RESULT=" + json.dumps(result, sort_keys=True), flush=True)

    del policy, components, vla, processor, projected_patches_with_proprio, projected_patches
    del normalized_proprio, official_normalized, diwa_normalized, pixel_values, full_ids, full_attention
    del input_ids, attention_mask, primary, wrist
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.synchronize(device)
    released = {
        "allocated_bytes": torch.cuda.memory_allocated(device),
        "reserved_bytes": torch.cuda.memory_reserved(device),
        "baseline_allocated_bytes": baseline_allocated,
        "baseline_reserved_bytes": baseline_reserved,
    }
    if released["allocated_bytes"] > baseline_allocated + 16 * 1024 * 1024:
        residuals = []
        for obj in gc.get_objects():
            try:
                if isinstance(obj, torch.Tensor) and obj.is_cuda:
                    residuals.append({"shape": list(obj.shape), "dtype": str(obj.dtype), "bytes": obj.numel() * obj.element_size()})
            except (ReferenceError, RuntimeError):
                continue
        raise RuntimeError(f"CUDA allocation grew beyond baseline after forward smoke: {released}; residuals={residuals}")
    after = verify_checkpoint_directory(args.checkpoint, manifest)
    if after != before:
        raise RuntimeError("checkpoint changed during forward smoke")
    print("FORWARD_POST_RELEASE=" + json.dumps(released, sort_keys=True), flush=True)
    print("FORWARD_POST_CHECKPOINT=" + json.dumps(after.__dict__, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

"""Single-card real OpenVLA-OFT counterfactual teacher pilot.

This is an audit-only path.  It uses a deterministic token-L2 selector as a
placeholder for an untrained DIE; its values must not be reported as trained
estimator scores.  The teacher labels themselves are real paired normalized
action distances from the frozen OpenVLA-OFT policy.
"""

from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import time


def _cleanup_cuda(device, baseline_allocated: int, baseline_reserved: int) -> dict[str, int]:
    import torch

    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.synchronize(device)
    residuals = []
    for obj in gc.get_objects():
        try:
            if isinstance(obj, torch.Tensor) and obj.is_cuda:
                residuals.append({"shape": list(obj.shape), "dtype": str(obj.dtype)})
        except (ReferenceError, RuntimeError):
            continue
    result = {
        "allocated_bytes": torch.cuda.memory_allocated(device),
        "reserved_bytes": torch.cuda.memory_reserved(device),
        "baseline_allocated_bytes": baseline_allocated,
        "baseline_reserved_bytes": baseline_reserved,
    }
    if residuals or result["allocated_bytes"] > baseline_allocated + 16 * 1024 * 1024:
        raise RuntimeError(f"teacher pilot left CUDA state: {result}; residuals={residuals}")
    return result


def _build_token_batch(projected_patches, normalized_proprio):
    import torch

    from diwa.data.contracts import TokenBatch

    batch, tokens, _ = projected_patches.shape
    if batch != 1 or tokens != 512:
        raise RuntimeError(f"teacher pilot requires one full 512-patch sample, got {tuple(projected_patches.shape)}")
    # Two fused images: 256 patch tokens per image.  Keep metadata explicit so
    # matched means are computed within camera groups, never over a fake zero baseline.
    token_type = torch.zeros((batch, tokens), dtype=torch.long, device=projected_patches.device)
    # Both images belong to the same observation frame; camera identity is the
    # only grouping distinction.  Keeping this explicit is important because
    # MatchedMeanBaseline groups by (token_type, frame_id, camera_id).
    frame_id = torch.zeros((batch, tokens), dtype=torch.long, device=projected_patches.device)
    camera_id = torch.cat(
        (
            torch.zeros((batch, tokens // 2), dtype=torch.long, device=projected_patches.device),
            torch.ones((batch, tokens // 2), dtype=torch.long, device=projected_patches.device),
        ),
        dim=1,
    )
    valid = torch.ones((batch, tokens), dtype=torch.bool, device=projected_patches.device)
    query = projected_patches.mean(dim=1)
    return TokenBatch(
        z=projected_patches.detach(),
        token_type=token_type,
        frame_id=frame_id,
        camera_id=camera_id,
        valid=valid,
        query=query.detach(),
        proprio=normalized_proprio.detach(),
    )


def _make_selector_scores(token_batch):
    """Deterministic untrained pilot selector; explicitly not a DIE output."""

    scores = token_batch.z.float().norm(dim=-1)
    scores = scores.masked_fill(~token_batch.valid, 0.0)
    if not torch_is_finite(scores):
        raise RuntimeError("pilot selector produced NaN/Inf")
    return scores


def torch_is_finite(value) -> bool:
    return bool(value.isfinite().all())


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

    from diwa.data.interventions import MatchedMeanBaseline
    from diwa.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from diwa.models.influence.sampling import TeacherCandidateSampler, compute_coverage_audit
    from diwa.models.influence.teacher import CounterfactualTeacher
    from diwa.models.openvla_oft_loader import load_openvla_oft_components

    if torch.cuda.device_count() != 1:
        raise RuntimeError("teacher pilot requires exactly one visible GPU")
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
    from diwa.evaluation.forward_smoke_openvla_oft import _make_images, _normalize_proprio

    prompt = "In: What action should the robot take to move the object to the target?\nOut:"
    image_a, image_b = _make_images()
    primary = processor(prompt, image_a, return_tensors="pt")
    wrist = processor(prompt, image_b, return_tensors="pt")
    pixel_values = torch.cat((primary["pixel_values"], wrist["pixel_values"]), dim=1).to(
        device=device, dtype=dtype
    )
    input_ids = primary["input_ids"].to(device=device)
    attention_mask = primary["attention_mask"].to(device=device)
    if not bool((attention_mask != 0).all()):
        raise RuntimeError("teacher pilot refuses padded prompt tensors")

    stats_keys = [
        key for key, value in (getattr(vla, "norm_stats", {}) or {}).items()
        if isinstance(key, str) and "libero_spatial" in key and isinstance(value, dict)
    ]
    if len(stats_keys) != 1:
        raise RuntimeError(f"expected exactly one LIBERO Spatial norm_stats key, got {stats_keys}")
    proprio_stats = vla.norm_stats[stats_keys[0]]["proprio"]
    low = np.asarray(proprio_stats["q01"], dtype=np.float32)
    high = np.asarray(proprio_stats["q99"], dtype=np.float32)
    raw_proprio = low + 0.37 * (high - low)
    normalized_proprio = torch.from_numpy(_normalize_proprio(raw_proprio, proprio_stats)).to(
        device=device, dtype=dtype
    ).unsqueeze(0)

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
    token_batch = _build_token_batch(
        projected_patches,
        normalized_proprio,
    )
    if projected_patches.dtype is not dtype or token_batch.z.dtype is not dtype:
        raise RuntimeError("teacher pilot requires bf16 projected patches")
    baseline = MatchedMeanBaseline()(
        token_batch.z,
        token_batch.token_type,
        token_batch.frame_id,
        token_batch.camera_id,
        token_batch.valid,
    )
    if bool(torch.all(baseline == 0)):
        raise RuntimeError("matched baseline unexpectedly collapsed to all zeros")
    scores = _make_selector_scores(token_batch)
    intervened_mask = torch.zeros_like(token_batch.valid)

    sampler4 = TeacherCandidateSampler(num_top=4, num_stratified=0, num_hard_negative=0, audit_size=512)
    regular4 = sampler4.sample(token_batch, scores, intervened_mask)
    regular2 = TeacherCandidateSampler(num_top=2, num_stratified=0, num_hard_negative=0, audit_size=512).sample(
        token_batch, scores, intervened_mask
    )
    audit = sampler4.audit_candidates(token_batch, scores, intervened_mask, regular4)
    if audit.masks.shape[1] != 512:
        raise RuntimeError(f"exact audit must evaluate all 512 eligible tokens, got {audit.masks.shape[1]}")

    from diwa.models.openvla_oft_policy import OpenVLAOFTTokenPolicy

    policy = OpenVLAOFTTokenPolicy(
        vla,
        components.action_head,
        components.proprio_projector,
        num_patches_full=components.num_patches_full,
    ).eval()
    teacher = CounterfactualTeacher(policy, action_chunk_shape=(8, 7))
    policy_inputs = {"input_ids": input_ids, "attention_mask": attention_mask}

    torch.cuda.reset_peak_memory_stats(device)
    started = time.perf_counter()
    audit_targets = teacher.estimate_candidates(
        token_batch,
        baseline,
        intervened_mask,
        audit,
        policy_inputs=policy_inputs,
    )
    torch.cuda.synchronize(device)
    teacher_seconds = time.perf_counter() - started
    peak_bytes = torch.cuda.max_memory_allocated(device)

    metrics = {}
    for name, regular in (("m2", regular2), ("m4", regular4)):
        coverage = compute_coverage_audit(regular, audit, audit_targets.influence)
        selected = audit_targets.influence.gather(1, regular.source_indices).squeeze(0)
        metrics[name] = {
            **coverage.mean_metrics(),
            "selected_source_indices": regular.source_indices.squeeze(0).tolist(),
            "selected_influence": selected.float().cpu().tolist(),
            "regular_candidate_count": int(regular.valid_candidates.sum()),
            "exact_audit_count": int(audit.valid_candidates.sum()),
        }

    result = {
        "checkpoint_revision": before.revision,
        "selector": "deterministic_token_l2_pilot_not_trained_DIE",
        "norm_stats_key": stats_keys[0],
        "token_batch_shape": list(token_batch.z.shape),
        "prompt_tokens_before_action": int(num_prompt_tokens),
        "baseline_abs_mean": float(baseline.float().abs().mean().cpu()),
        "base_intervened_count": int(intervened_mask.sum()),
        "teacher_seconds": teacher_seconds,
        "teacher_peak_allocated_bytes": peak_bytes,
        "metrics": metrics,
    }
    print("TEACHER_PILOT_RESULT=" + json.dumps(result, sort_keys=True), flush=True)

    del teacher, policy, components, vla, processor, projected_patches, token_batch
    del baseline, scores, audit_targets, audit, regular2, regular4
    del policy_inputs, regular, coverage, selected, name
    del input_ids, attention_mask, pixel_values, full_ids, full_attention, labels, action_mask
    del language_embeddings, input_embeddings, normalized_proprio, intervened_mask, primary, wrist
    released = _cleanup_cuda(device, baseline_allocated, baseline_reserved)
    after = verify_checkpoint_directory(args.checkpoint, manifest)
    if after != before:
        raise RuntimeError("checkpoint changed during teacher pilot")
    print("TEACHER_PILOT_POST_RELEASE=" + json.dumps(released, sort_keys=True), flush=True)
    print("TEACHER_PILOT_POST_CHECKPOINT=" + json.dumps(after.__dict__, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

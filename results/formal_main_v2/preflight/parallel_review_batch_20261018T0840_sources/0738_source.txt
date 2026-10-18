"""Deterministic RLDS inputs for OFT tensor-boundary smoke tests.

This processor-only image path is NOT a validated LIBERO rollout preprocessing
pipeline: no evaluation center crop, environment rotation or action postprocess
is implied. Both smoke branches consume the identical prepared observations.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any, Mapping

import numpy as np


INPUTS_VERSION = "rlds-processor-only-oft-prompt-bounds-q99-v1"


def format_prompt(instruction: str) -> str:
    """Match the pinned OpenVLA-OFT evaluation instruction template."""
    if not isinstance(instruction, str) or not instruction.strip():
        raise ValueError("instruction must be nonempty text")
    return f"In: What action should the robot take to {instruction.lower()}?\nOut:"


def normalize_proprio(raw: np.ndarray, stats: Mapping[str, Any]) -> np.ndarray:
    """Checkpoint bounds_q99 transform, including its mask and clipping rule."""
    raw = np.asarray(raw, dtype=np.float32)
    low = np.asarray(stats["q01"], dtype=np.float32)
    high = np.asarray(stats["q99"], dtype=np.float32)
    mask = np.asarray(stats.get("mask", np.ones_like(low, dtype=bool)), dtype=bool)
    if any(value.shape != (8,) for value in (raw, low, high, mask)):
        raise ValueError("raw proprio, bounds and mask must all have shape [8]")
    if not all(np.isfinite(value).all() for value in (raw, low, high)):
        raise ValueError("proprio and normalization statistics must be finite")
    if np.any(high < low):
        raise ValueError("normalization upper bounds must not be below lower bounds")
    normalized = np.where(mask, 2.0 * (raw - low) / (high - low + 1e-8) - 1.0, raw)
    return np.clip(normalized, -1.0, 1.0).astype(np.float32)


def prepare_rlds_inputs(
    episode: Any,
    step_index: int,
    processor: Any,
    norm_stats: Mapping[str, Any],
    *,
    device: Any,
    dtype: Any,
) -> dict[str, Any]:
    """Prepare one real observation; norm_stats is its proprio-statistics dict.

    All episode steps are allowed, including the final observation. A policy
    prediction does not require eight future recorded demonstration actions.
    """
    import torch
    from PIL import Image

    if type(step_index) is not int or not 0 <= step_index < episode.num_steps:
        raise ValueError("step_index is outside the episode")
    prompt = format_prompt(episode.instructions[step_index])
    processed = []
    sizes = []
    for encoded in (episode.images[step_index], episode.wrist_images[step_index]):
        with Image.open(BytesIO(encoded)) as image:
            rgb = image.convert("RGB")
            sizes.append(list(rgb.size))
            processed.append(processor(prompt, rgb, return_tensors="pt"))
    primary, wrist = processed
    if not torch.equal(primary["input_ids"], wrist["input_ids"]):
        raise RuntimeError("camera preprocessing changed the shared language instruction")
    ids = primary["input_ids"].to(device=device)
    attention = primary["attention_mask"].to(device=device)
    if ids.ndim != 2 or ids.shape[0] != 1 or not bool((attention == 1).all()):
        raise RuntimeError("RLDS smoke requires one unpadded prompt")
    pixels = torch.cat((primary["pixel_values"], wrist["pixel_values"]), dim=1).to(device=device, dtype=dtype)
    if pixels.ndim != 4 or pixels.shape[0] != 1 or pixels.shape[1] != 12:
        raise RuntimeError("two fused RGB views must yield pixel_values [1, 12, H, W]")
    proprio = torch.from_numpy(normalize_proprio(episode.proprio[step_index], norm_stats)).to(
        device=device, dtype=dtype,
    ).unsqueeze(0)
    return {
        "pixel_values": pixels, "input_ids": ids, "attention_mask": attention,
        "normalized_proprio": proprio, "prompt": prompt, "image_sizes": sizes,
        "inputs_version": INPUTS_VERSION,
    }


__all__ = ["INPUTS_VERSION", "format_prompt", "normalize_proprio", "prepare_rlds_inputs"]

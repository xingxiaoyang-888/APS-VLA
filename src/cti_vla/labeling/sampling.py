"""Deterministic, camera-balanced G1 panels, selected without teacher outputs."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import random
from typing import Sequence

SAMPLING_VERSION = "g1-fixed-anchor-grid-prune-v1"


def named_seed(seed: int, *parts: object) -> int:
    """Separate RNG streams by observation and purpose; do not use Python hash()."""
    raw = json.dumps([seed, *parts], ensure_ascii=False, separators=(",", ":")).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def camera_balanced_set(
    *, per_camera: int, grid_shape: tuple[int, int] = (16, 16),
    num_cameras: int = 2, mode: str, seed: int = 0,
    anchors: Sequence[int] = (),
) -> tuple[int, ...]:
    """Original camera-major indices with equal, exact per-camera budgets.

    Uniform means a centered rectangular grid. With forced anchors, merge the
    grid and anchors, then remove non-anchor points with the nearest neighbor
    until the budget is met. This anchor-conditioned distribution is deliberately
    different from the unconstrained uniform deployment control.
    """
    rows, cols = grid_shape
    if any(type(v) is not int or v <= 0 for v in (rows, cols, num_cameras, per_camera)):
        raise ValueError("grid, cameras and budget must be positive integers")
    size = rows * cols
    if per_camera > size or mode not in ("uniform", "random"):
        raise ValueError("invalid per-camera budget or sampling mode")
    anchor_list = tuple(anchors)
    if len(set(anchor_list)) != len(anchor_list) or any(type(i) is not int or not 0 <= i < size * num_cameras for i in anchor_list):
        raise ValueError("anchors must be unique original indices")
    output = []
    for camera in range(num_cameras):
        mandatory = {i - camera * size for i in anchor_list if i // size == camera}
        if len(mandatory) > per_camera:
            raise ValueError("anchors exceed a camera budget")
        if mode == "random":
            pool = sorted(set(range(size)) - mandatory)
            rng = random.Random(named_seed(seed, "camera", camera))
            selected = mandatory | set(rng.sample(pool, per_camera - len(mandatory)))
        else:
            factors = [(r, per_camera // r) for r in range(1, rows + 1)
                       if per_camera % r == 0 and per_camera // r <= cols]
            if not factors:
                raise ValueError("uniform budget must admit a rectangular grid")
            nr, nc = min(factors, key=lambda shape: (abs(math.log((shape[0] / shape[1]) / (rows / cols))), shape))
            selected = {int((r + .5) * rows / nr) * cols + int((c + .5) * cols / nc)
                        for r in range(nr) for c in range(nc)} | mandatory
            def distance(a: int, b: int) -> int:
                return (a // cols - b // cols) ** 2 + (a % cols - b % cols) ** 2
            while len(selected) > per_camera:
                # Resolve ties by original index, keeping lower indices.
                remove = min(selected - mandatory,
                             key=lambda i: (min(distance(i, j) for j in selected if j != i), -i))
                selected.remove(remove)
        output.extend(camera * size + i for i in sorted(selected))
    return tuple(output)


@dataclass(frozen=True)
class DiagnosticSet:
    name: str
    retained_indices: tuple[int, ...]
    candidate_indices: tuple[int, ...]


def fixed_anchor_panel(
    sample_id: object, *, seed: int = 17, grid_shape: tuple[int, int] = (16, 16),
    num_cameras: int = 2, anchors_per_camera: int = 8,
    per_camera_budgets: tuple[int, ...] = (128, 64),
) -> tuple[DiagnosticSet, ...]:
    """Full + random/uniform partial sets, sharing the exact same candidates."""
    size = math.prod(grid_shape)
    anchors = camera_balanced_set(per_camera=anchors_per_camera, grid_shape=grid_shape,
                                  num_cameras=num_cameras, mode="random",
                                  seed=named_seed(seed, sample_id, "anchors"))
    records = [DiagnosticSet("full", tuple(range(size * num_cameras)), anchors)]
    for budget in per_camera_budgets:
        if budget >= size:
            raise ValueError("partial budget must be smaller than full camera size")
        for mode in ("random", "uniform"):
            kept = camera_balanced_set(per_camera=budget, grid_shape=grid_shape,
                                       num_cameras=num_cameras, mode=mode, anchors=anchors,
                                       seed=named_seed(seed, sample_id, mode, budget))
            records.append(DiagnosticSet(f"{mode}_{budget * num_cameras}", kept, anchors))
    return tuple(records)

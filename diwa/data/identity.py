"""Stable identities for dataset rows and cache compatibility signatures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


def stable_sample_id(dataset: str, episode_id: str | int, step_index: int) -> int:
    if not dataset.strip() or str(episode_id) == "" or step_index < 0:
        raise ValueError("dataset/episode_id must be non-empty and step_index non-negative")
    payload = f"{dataset}\x1f{episode_id}\x1f{step_index}".encode("utf-8")
    # Keep the sign bit clear so ids fit signed torch.long and external databases.
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "big") & ((1 << 63) - 1)


def canonical_mapping_signature(value: Mapping[str, Any], *, namespace: str) -> str:
    if not namespace.strip():
        raise ValueError("signature namespace must be non-empty")
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    digest = hashlib.sha256(namespace.encode("utf-8") + b"\x00" + encoded).hexdigest()
    return f"sha256:{digest}"


def file_set_signature(paths: Iterable[str | Path], *, namespace: str) -> str:
    if not namespace.strip():
        raise ValueError("signature namespace must be non-empty")
    resolved = sorted(Path(path).resolve() for path in paths)
    if not resolved:
        raise ValueError("at least one signature file is required")
    hasher = hashlib.sha256(namespace.encode("utf-8") + b"\x00")
    for path in resolved:
        if not path.is_file():
            raise FileNotFoundError(path)
        hasher.update(path.name.encode("utf-8") + b"\x00")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"


__all__ = ["canonical_mapping_signature", "file_set_signature", "stable_sample_id"]

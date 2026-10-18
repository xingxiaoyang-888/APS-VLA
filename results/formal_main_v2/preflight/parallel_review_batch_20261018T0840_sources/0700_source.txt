"""Portable, versioned identities for observations and data provenance."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


def canonical_mapping_signature(value: Mapping[str, Any], *, namespace: str) -> str:
    if not isinstance(namespace, str) or not namespace.strip():
        raise ValueError("signature namespace must be non-empty")
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    return "sha256:" + hashlib.sha256(namespace.encode() + b"\x00" + encoded).hexdigest()


def stable_sample_id(dataset: str, episode_id: str, step_index: int) -> int:
    if not isinstance(dataset, str) or not dataset.strip():
        raise ValueError("dataset must be non-empty")
    if not isinstance(episode_id, str) or not episode_id.strip():
        raise ValueError("episode_id must be non-empty")
    if type(step_index) is not int or step_index < 0:
        raise ValueError("step_index must be a non-negative integer")
    digest = canonical_mapping_signature(
        {"dataset": dataset, "episode_id": episode_id, "step_index": step_index},
        namespace="cti-vla:observation:v2",
    )
    return int(digest.split(":")[1][:16], 16) & ((1 << 63) - 1)


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_set_signature(paths: Iterable[str | Path], *, namespace: str) -> str:
    """Hash names, sizes and content hashes; portable between local and server.

    Duplicate basenames are rejected because names are the portable file keys.
    """
    paths = [Path(path) for path in paths]
    if not paths or len({path.name for path in paths}) != len(paths):
        raise ValueError("file set must be non-empty with unique basenames")
    records = {
        path.name: {"bytes": path.stat().st_size, "sha256": file_sha256(path)}
        for path in paths
    }
    return canonical_mapping_signature(records, namespace=namespace)

"""Strict, streaming verification for immutable checkpoint snapshots."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


_HASH_CHUNK_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class CheckpointFileSpec:
    path: str
    size: int
    sha256: str | None = None
    git_blob_sha1: str | None = None

    def __post_init__(self) -> None:
        relative = PurePosixPath(self.path)
        if relative.is_absolute() or not relative.parts or any(part in ("", ".", "..") for part in relative.parts):
            raise ValueError(f"checkpoint path must be safe and relative: {self.path!r}")
        if not isinstance(self.size, int) or isinstance(self.size, bool) or self.size < 0:
            raise ValueError("checkpoint file size must be a non-negative integer")
        if (self.sha256 is None) == (self.git_blob_sha1 is None):
            raise ValueError("each checkpoint file needs exactly one hash kind")
        if self.sha256 is not None and not _valid_hex_digest(self.sha256, 64):
            raise ValueError(f"invalid SHA-256 for {self.path}")
        if self.git_blob_sha1 is not None and not _valid_hex_digest(self.git_blob_sha1, 40):
            raise ValueError(f"invalid Git blob SHA-1 for {self.path}")


@dataclass(frozen=True)
class CheckpointManifest:
    schema_version: int
    repository: str
    revision: str
    total_bytes: int
    files: tuple[CheckpointFileSpec, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported checkpoint manifest schema")
        if not self.repository.strip() or not _valid_hex_digest(self.revision, 40):
            raise ValueError("checkpoint repository/revision is invalid")
        if not self.files:
            raise ValueError("checkpoint manifest must contain files")
        paths = [item.path for item in self.files]
        if len(paths) != len(set(paths)):
            raise ValueError("checkpoint manifest contains duplicate paths")
        if sum(item.size for item in self.files) != self.total_bytes:
            raise ValueError("checkpoint manifest total_bytes mismatch")


@dataclass(frozen=True)
class CheckpointVerification:
    repository: str
    revision: str
    file_count: int
    total_bytes: int


def _valid_hex_digest(value: str, length: int) -> bool:
    return len(value) == length and all(character in "0123456789abcdef" for character in value)


def load_checkpoint_manifest(path: str | Path) -> CheckpointManifest:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "repository",
        "revision",
        "total_bytes",
        "files",
    }:
        raise ValueError("checkpoint manifest keys mismatch")
    raw_files = payload["files"]
    if not isinstance(raw_files, list):
        raise ValueError("checkpoint manifest files must be a list")
    files = []
    for item in raw_files:
        if not isinstance(item, dict) or not set(item).issubset({"path", "size", "sha256", "git_blob_sha1"}):
            raise ValueError("invalid checkpoint file entry")
        if "path" not in item or "size" not in item:
            raise ValueError("checkpoint file entry is missing path/size")
        files.append(CheckpointFileSpec(**item))
    return CheckpointManifest(
        schema_version=payload["schema_version"],
        repository=payload["repository"],
        revision=payload["revision"],
        total_bytes=payload["total_bytes"],
        files=tuple(files),
    )


def verify_checkpoint_file(root: str | Path, spec: CheckpointFileSpec) -> None:
    root_path = Path(root).resolve()
    candidate = root_path.joinpath(*PurePosixPath(spec.path).parts)
    if candidate.is_symlink() or not candidate.is_file():
        raise FileNotFoundError(f"checkpoint file missing or unsafe: {spec.path}")
    if candidate.stat().st_size != spec.size:
        raise ValueError(f"checkpoint size mismatch: {spec.path}")
    if spec.sha256 is not None:
        actual = _stream_hash(candidate, "sha256")
        expected = spec.sha256
    else:
        actual = _git_blob_sha1(candidate, spec.size)
        expected = spec.git_blob_sha1
    if actual != expected:
        raise ValueError(f"checkpoint hash mismatch: {spec.path}")


def verify_checkpoint_directory(
    root: str | Path,
    manifest: CheckpointManifest,
) -> CheckpointVerification:
    root_path = Path(root)
    if root_path.is_symlink() or not root_path.is_dir():
        raise FileNotFoundError(root_path)
    expected_paths = {item.path for item in manifest.files}
    actual_paths = {
        path.relative_to(root_path).as_posix()
        for path in root_path.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    missing = sorted(expected_paths - actual_paths)
    extra = sorted(actual_paths - expected_paths)
    if missing or extra:
        raise ValueError(f"checkpoint file set mismatch; missing={missing}, extra={extra}")
    for spec in manifest.files:
        verify_checkpoint_file(root_path, spec)
    return CheckpointVerification(
        repository=manifest.repository,
        revision=manifest.revision,
        file_count=len(manifest.files),
        total_bytes=manifest.total_bytes,
    )


def _stream_hash(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_HASH_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_blob_sha1(path: Path, size: int) -> str:
    digest = hashlib.sha1()
    digest.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_HASH_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = [
    "CheckpointFileSpec",
    "CheckpointManifest",
    "CheckpointVerification",
    "load_checkpoint_manifest",
    "verify_checkpoint_directory",
    "verify_checkpoint_file",
]

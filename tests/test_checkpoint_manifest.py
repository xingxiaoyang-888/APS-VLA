import hashlib
import json

import pytest

from diwa.evaluation.checkpoint_manifest import (
    load_checkpoint_manifest,
    verify_checkpoint_directory,
)


def git_blob_sha1(content):
    return hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()


def write_manifest(tmp_path, files):
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "repository": "owner/model",
                "revision": "a" * 40,
                "total_bytes": sum(item["size"] for item in files),
                "files": files,
            }
        ),
        encoding="utf-8",
    )
    return path


def test_checkpoint_verification_supports_lfs_and_git_blob_hashes(tmp_path):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    lfs_content = b"large-model-content"
    regular_content = b"config-content"
    checkpoint.joinpath("weights.bin").write_bytes(lfs_content)
    checkpoint.joinpath("config.json").write_bytes(regular_content)
    manifest = load_checkpoint_manifest(
        write_manifest(
            tmp_path,
            [
                {
                    "path": "weights.bin",
                    "size": len(lfs_content),
                    "sha256": hashlib.sha256(lfs_content).hexdigest(),
                },
                {
                    "path": "config.json",
                    "size": len(regular_content),
                    "git_blob_sha1": git_blob_sha1(regular_content),
                },
            ],
        )
    )
    result = verify_checkpoint_directory(checkpoint, manifest)
    assert result.file_count == 2
    assert result.total_bytes == len(lfs_content) + len(regular_content)


def test_checkpoint_verification_rejects_extra_and_corrupt_files(tmp_path):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    content = b"expected"
    checkpoint.joinpath("weights.bin").write_bytes(content)
    manifest = load_checkpoint_manifest(
        write_manifest(
            tmp_path,
            [{"path": "weights.bin", "size": len(content), "sha256": hashlib.sha256(content).hexdigest()}],
        )
    )
    checkpoint.joinpath("unexpected.tmp").write_bytes(b"partial")
    with pytest.raises(ValueError, match="file set mismatch"):
        verify_checkpoint_directory(checkpoint, manifest)
    checkpoint.joinpath("unexpected.tmp").unlink()
    checkpoint.joinpath("weights.bin").write_bytes(b"corrupt!")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_checkpoint_directory(checkpoint, manifest)


def test_checkpoint_manifest_rejects_path_traversal(tmp_path):
    with pytest.raises(ValueError, match="safe and relative"):
        load_checkpoint_manifest(
            write_manifest(
                tmp_path,
                [{"path": "../weights.bin", "size": 1, "sha256": "0" * 64}],
            )
        )

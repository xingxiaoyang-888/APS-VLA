#!/usr/bin/env python3
"""Download immutable HF files with resume, hashes, and an explicit receipt.

Standard-library only: usable before installing the GPU runtime. Model weights
must be downloaded on the server, never into the local project workspace.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import re
import time
import urllib.error
import urllib.request


def safe_path(root: Path, name: str) -> Path:
    rel = PurePosixPath(name)
    if rel.is_absolute() or not rel.parts or ".." in rel.parts or "\\" in name or ":" in name:
        raise ValueError(f"Unsafe asset path: {name}")
    target = root.joinpath(*rel.parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Asset escapes root: {name}")
    return target


def verify(path: Path, item: dict) -> str:
    if path.is_symlink() or not path.is_file() or path.stat().st_size != item["size"]:
        raise ValueError(f"Missing file or size mismatch: {path.name}")
    sha256 = item.get("sha256") or item.get("lfs_oid")
    expected = sha256 or item.get("git_blob_sha1")
    if not expected:
        raise ValueError(f"Missing pinned digest: {path.name}")
    digest = hashlib.sha256() if sha256 else hashlib.sha1()
    if not sha256:
        digest.update(f"blob {item['size']}\0".encode())
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected:
        raise ValueError(f"Hash mismatch: {path.name}; expected {expected}; got {actual}")
    return actual


def download_file(url: str, target: Path, item: dict) -> dict:
    if target.exists():
        digest = verify(target, item)
        print(f"verified_existing {item['path']}", flush=True)
        return {"path": item["path"], "size": item["size"], "digest": digest}
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".partial")
    if partial.is_symlink():
        raise ValueError("Partial file must not be a symlink")
    for attempt in range(4):
        offset = partial.stat().st_size if partial.exists() else 0
        if offset > item["size"]:
            raise ValueError(f"Oversized partial: {partial}")
        if offset == item["size"]:
            break
        request = urllib.request.Request(url, headers={"Range": f"bytes={offset}-", "User-Agent": "cti-vla-assets/1"})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                if response.status == 206:
                    content_range = response.headers.get("Content-Range", "")
                    match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", content_range)
                    if not match or int(match[1]) != offset or int(match[3]) != item["size"] or int(match[2]) >= item["size"]:
                        raise ValueError(f"Invalid Content-Range: {content_range}")
                elif response.status != 200 or offset:
                    raise ValueError(f"Server did not honor resume at {offset}")
                with partial.open("ab") as handle:
                    while chunk := response.read(4 * 1024 * 1024):
                        if handle.tell() + len(chunk) > item["size"]:
                            raise ValueError("Response exceeds expected file size")
                        handle.write(chunk)
            if partial.stat().st_size != item["size"]:
                raise OSError("Incomplete transfer")
            break
        except (OSError, urllib.error.URLError) as error:
            if attempt == 3:
                raise
            print(f"retry {item['path']} attempt={attempt + 1} error={type(error).__name__}", flush=True)
            time.sleep(2 * (attempt + 1))
    digest = verify(partial, item)
    partial.replace(target)
    print(f"verified_download {item['path']} bytes={item['size']}", flush=True)
    return {"path": item["path"], "size": item["size"], "digest": digest}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--kind", choices=("model", "dataset"), required=True)
    parser.add_argument("--endpoint", default="https://huggingface.co")
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if args.kind == "model" and platform.system() == "Windows":
        parser.error("Project policy: download model weights on the server only")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if not re.fullmatch(r"[a-f0-9]{40}", manifest["revision"]):
        raise ValueError("Asset revision must be an immutable commit")
    if len({item["path"] for item in manifest["files"]}) != len(manifest["files"]):
        raise ValueError("Duplicate asset paths")
    if sum(item["size"] for item in manifest["files"]) != manifest["total_bytes"]:
        raise ValueError("Manifest total size mismatch")
    prefix = "datasets/" if args.kind == "dataset" else ""
    base = f"{args.endpoint.rstrip('/')}/{prefix}{manifest['repository']}/resolve/{manifest['revision']}"
    started = time.monotonic()
    def transfer(item: dict) -> dict:
        return download_file(f"{base}/{item['path']}", safe_path(args.root, item["path"]), item)
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as pool:
        verified = list(pool.map(transfer, manifest["files"]))
    receipt = {"status": "verified", "repository": manifest["repository"], "revision": manifest["revision"],
               "root": str(args.root.resolve()), "endpoint": args.endpoint, "files": verified,
               "total_bytes": sum(x["size"] for x in verified), "elapsed_seconds": time.monotonic() - started}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    temp = args.receipt.with_suffix(".partial")
    temp.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    temp.replace(args.receipt)
    print(f"complete files={len(verified)} receipt={args.receipt}", flush=True)


if __name__ == "__main__":
    main()

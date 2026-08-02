#!/usr/bin/env python3
"""Resume one Hugging Face LFS object using bounded HTTP Range requests."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import urllib.request


def download(url: str, output: Path, expected_size: int, expected_sha256: str, chunk_size: int) -> None:
    if expected_size <= 0 or chunk_size <= 0:
        raise ValueError("expected_size and chunk_size must be positive")
    if len(expected_sha256) != 64 or any(char not in "0123456789abcdefABCDEF" for char in expected_sha256):
        raise ValueError("expected_sha256 must be a 64-character hex digest")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(output.name + ".partial")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite verified output: {output}")
    current = partial.stat().st_size if partial.exists() else 0
    if current > expected_size:
        raise ValueError(f"partial file is larger than expected object: {current}>{expected_size}")

    while current < expected_size:
        end = min(expected_size - 1, current + chunk_size - 1)
        request = urllib.request.Request(url, headers={"Range": f"bytes={current}-{end}"})
        with urllib.request.urlopen(request, timeout=120) as response:
            content_range = response.headers.get("Content-Range", "")
            expected_range = f"bytes {current}-{end}/{expected_size}"
            if content_range != expected_range:
                raise RuntimeError(f"unexpected Content-Range {content_range!r}, expected {expected_range!r}")
            with partial.open("ab") as handle:
                before = handle.tell()
                shutil.copyfileobj(response, handle, length=1024 * 1024)
                after = handle.tell()
        if after <= before or after != end + 1:
            raise RuntimeError(f"range made invalid progress: before={before}, after={after}, end={end}")
        current = after
        print(f"range_complete={current}/{expected_size}", flush=True)

    digest = hashlib.sha256()
    with partial.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    actual = digest.hexdigest()
    if actual.lower() != expected_sha256.lower():
        raise RuntimeError(f"SHA-256 mismatch: {actual} != {expected_sha256}")
    partial.replace(output)
    print(f"verified_output={output} size={output.stat().st_size} sha256={actual}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("output", type=Path)
    parser.add_argument("expected_size", type=int)
    parser.add_argument("expected_sha256")
    parser.add_argument("--chunk-size", type=int, default=8 * 1024 * 1024)
    args = parser.parse_args()
    download(args.url, args.output, args.expected_size, args.expected_sha256, args.chunk_size)


if __name__ == "__main__":
    main()

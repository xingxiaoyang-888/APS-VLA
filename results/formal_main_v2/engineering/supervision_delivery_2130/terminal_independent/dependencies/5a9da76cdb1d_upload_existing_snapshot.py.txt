#!/usr/bin/env python3
"""Resume an existing local immutable snapshot onto the authorized SSH server.

No local weight copy is made. A remote hash verification is required before use.
Only files enumerated in the pinned manifest are transferred.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path, PurePosixPath
import shlex
import subprocess
import time


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if not args.destination.startswith("/") or ".." in PurePosixPath(args.destination).parts:
        raise ValueError("Require an explicit absolute server destination")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    for item in manifest["files"]:
        rel = PurePosixPath(item["path"])
        if rel.is_absolute() or ".." in rel.parts or "\\" in item["path"]:
            raise ValueError("Unsafe manifest path")
        source = args.source / item["path"]
        if not source.is_file() or source.stat().st_size != item["size"]:
            raise ValueError(f"Incomplete source: {item['path']}")
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=15", args.host]
    remote_probe = "import json,pathlib; p=pathlib.Path(" + repr(args.destination) + "); print(json.dumps({str(x.relative_to(p)):x.stat().st_size for x in p.rglob('*') if x.is_file()}))"
    sizes = json.loads(subprocess.check_output(ssh + ["python3 -c " + shlex.quote(remote_probe)], text=True))
    def transfer(item: dict) -> None:
        offset = sizes.get(item["path"], 0)
        if offset > item["size"]:
            raise ValueError("Remote file larger than pinned asset")
        if offset == item["size"]:
            print(f"present_unverified {item['path']}", flush=True)
            return
        target = args.destination.rstrip("/") + "/" + item["path"]
        parent = str(PurePosixPath(target).parent)
        command = "mkdir -p " + shlex.quote(parent) + " && cat >> " + shlex.quote(target)
        started = time.monotonic()
        with (args.source / item["path"]).open("rb") as stream:
            stream.seek(offset)
            subprocess.run(ssh + [command], stdin=stream, check=True)
        print(f"uploaded_unverified {item['path']} bytes={item['size']-offset} seconds={time.monotonic()-started:.1f}", flush=True)
    with ThreadPoolExecutor(max_workers=max(1, min(4, args.workers))) as pool:
        list(pool.map(transfer, manifest["files"]))
    print("All files transferred; run remote pinned-manifest verification before loading.", flush=True)


if __name__ == "__main__":
    main()

"""Verify every source file against the frozen package inventory."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def verify(root: Path, inventory: Path) -> dict:
    root = root.resolve()
    payload = json.loads(inventory.read_text(encoding="utf-8"))
    expected = hashlib.sha256(json.dumps(payload["files"], sort_keys=True).encode()).hexdigest()
    if expected != payload["source_sha256"]:
        raise ValueError("source inventory signature mismatch")
    for relative, checksum in payload["files"].items():
        path = (root / relative).resolve()
        if root not in path.parents or hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
            raise ValueError(f"source file mismatch: {relative}")
    return {"status": "passed", "source_sha256": expected, "files": len(payload["files"])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    print(json.dumps(verify(args.root, args.inventory)))

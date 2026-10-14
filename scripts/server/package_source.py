#!/usr/bin/env python3
"""Package source/config/tests only, with a portable SHA256 inventory."""
from __future__ import annotations

import hashlib
import json
import argparse
from pathlib import Path
import subprocess
import tarfile


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path(".local/source-sync.tar"))
    parser.add_argument("--inventory", type=Path, default=Path("results/migration/source_snapshot.json"))
    args = parser.parse_args()
    output = (root / args.archive).resolve()
    record = (root / args.inventory).resolve()
    if root not in output.parents or root not in record.parents:
        raise ValueError("source package and inventory must stay inside CTI-VLA")
    output.parent.mkdir(parents=True, exist_ok=True)
    included = [root / name for name in ("pyproject.toml", "README.md", "AGENTS.md")]
    for directory in ("src", "scripts", "configs", "tests", "docs"):
        included.extend(p for p in (root / directory).rglob("*")
                        if p.is_file() and "__pycache__" not in p.parts and p.suffix in {".py", ".md", ".json", ".txt", ".yaml", ".yml", ".slurm", ".sh"})
    hashes = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(included)}
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True)
    status = subprocess.run(["git", "status", "--porcelain"], cwd=root, text=True, capture_output=True, check=True)
    snapshot = {"base_or_current_commit": result.stdout.strip(), "dirty": bool(status.stdout.strip()), "files": hashes,
                "source_sha256": hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()}
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8", newline="\n")
    with tarfile.open(output, "w") as archive:
        for p in included + [record]:
            archive.add(p, arcname=p.relative_to(root).as_posix())
    print(json.dumps({"archive": str(output), "files": len(hashes), "source_sha256": snapshot["source_sha256"]}))


if __name__ == "__main__":
    main()

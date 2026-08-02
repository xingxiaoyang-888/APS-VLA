"""CLI for exact checkpoint snapshot verification."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint_directory", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    manifest = load_checkpoint_manifest(args.manifest)
    result = verify_checkpoint_directory(args.checkpoint_directory, manifest)
    print(json.dumps(asdict(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

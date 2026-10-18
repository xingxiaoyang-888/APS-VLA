"""Verify official source archives and configure LIBERO inside this project."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tarfile


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def prepare(root: Path, registry: Path) -> dict:
    root = root.resolve()
    sources = json.loads(registry.read_text(encoding="utf-8"))["sources"]
    receipts = []
    for item in sources:
        name = "LIBERO" if item["repository"].endswith("/LIBERO.git") else "openvla-oft"
        archive = root / "external" / item["archive_name"]
        if archive.stat().st_size != item["bytes"] or digest(archive) != item["archive_sha256"]:
            raise ValueError(f"official source archive failed verification: {archive.name}")
        destination = (root / "external" / name).resolve()
        if root not in destination.parents:
            raise ValueError("runtime sources must stay inside project")
        marker = destination / "SOURCE_REVISION.json"
        if destination.exists():
            if not marker.exists() or json.loads(marker.read_text()) != item:
                raise ValueError(f"refusing to replace an unregistered source directory: {destination}")
        else:
            destination.mkdir(parents=True)
            with tarfile.open(archive) as handle:
                for member in handle.getmembers():
                    target = (destination / member.name).resolve()
                    if target != destination and destination not in target.parents:
                        raise ValueError("archive path escapes destination")
                    if not (member.isdir() or member.isfile()):
                        raise ValueError("only ordinary source files and directories are supported")
                handle.extractall(destination)
            marker.write_text(json.dumps(item, indent=2) + "\n", encoding="utf-8")
        files = {}
        with tarfile.open(archive) as handle:
            for member in handle.getmembers():
                if not member.isfile():
                    continue
                target = (destination / member.name).resolve()
                if destination not in target.parents:
                    raise ValueError("archive inventory path escapes source directory")
                stream = handle.extractfile(member)
                value = hashlib.sha256()
                for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                    value.update(block)
                if digest(target) != value.hexdigest():
                    raise ValueError(f"extracted source file differs from archive: {member.name}")
                files[member.name] = value.hexdigest()
        (destination / "SOURCE_FILES.json").write_text(json.dumps({
            "revision": item["revision"], "archive_sha256": item["archive_sha256"], "files": files,
        }, indent=2) + "\n", encoding="utf-8")
        receipts.append({**item, "directory": str(destination)})
    libero = root / "external/LIBERO/libero/libero"
    config_directory = root / "configs/libero_runtime"
    config_directory.mkdir(parents=True, exist_ok=True)
    paths = {"benchmark_root": libero, "bddl_files": libero / "bddl_files",
             "init_states": libero / "init_files", "assets": libero / "assets", "datasets": root / "data"}
    if any(not value.is_dir() for value in paths.values()):
        raise ValueError("LIBERO source or project data directories are incomplete")
    # JSON is also valid YAML; no additional dependency or interactive import.
    (config_directory / "config.yaml").write_text(
        json.dumps({k: str(v) for k, v in paths.items()}, indent=2) + "\n", encoding="utf-8")
    result = {"sources": receipts, "libero_config_path": str(config_directory)}
    output = root / "results/setup/runtime_sources.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.root, args.registry), indent=2))

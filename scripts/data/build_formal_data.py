"""CPU metadata-only inventory and complete formal training window index."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time

from cti_vla.data.experiment_protocol import write_frozen_json
from cti_vla.data.formal_windows import SUITES, build_formal_protocol, load_formal_protocol, build_formal_windows, load_formal_windows
from cti_vla.data.identity import file_sha256

ROOT = Path(__file__).resolve().parents[2]
ASSETS = {"libero_spatial": "libero_spatial_rlds.json", "libero_10": "libero_long_rlds.json",
          "libero_object": "libero_object_rlds.json", "libero_goal": "libero_goal_rlds.json"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=SUITES, required=True)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--asset-manifest", type=Path)
    parser.add_argument("--data-directory", type=Path)
    args = parser.parse_args()
    project = args.project_root.resolve()
    if ROOT != project and project not in ROOT.parents:
        raise ValueError("source snapshot must belong to project")
    output = project / "configs/manifests/formal_main_v2" / args.suite
    audit = project / "results/formal_main_v2/data" / args.suite / "build_audit.json"
    if ROOT != project and any(ROOT in p.resolve().parents for p in (output, audit)):
        raise ValueError("immutable source snapshot must not receive outputs")
    asset = args.asset_manifest or project / "configs/assets" / ASSETS[args.suite]
    data = args.data_directory or project / "data/modified_libero_rlds" / SUITES[args.suite] / "1.0.0"
    started = time.perf_counter()
    payload = build_formal_protocol(data, asset, project_root=project, suite=args.suite,
        progress=lambda row: print(json.dumps(row), flush=True))
    write_frozen_json(output / "protocol.json", payload)
    protocol = load_formal_protocol(output / "protocol.json", project)
    windows = build_formal_windows(protocol)
    write_frozen_json(output / "windows.json", windows)
    load_formal_windows(output / "windows.json", protocol)
    # A rerun verifies frozen outputs and keeps its original wall-cost receipt.
    result = {"schema_version": 2, "status": "passed_cpu_metadata_and_complete_window_inventory", "suite": args.suite,
        "protocol_sha256": file_sha256(output / "protocol.json"), "windows_sha256": file_sha256(output / "windows.json"),
        "protocol_signature": payload["content_signature"], "windows_signature": windows["content_signature"],
        "source_signature": payload["source_signature"], "source_files": payload["source_files"],
        "raw_episode_count": payload["raw_episode_count"], "unique_episode_count": payload["unique_episode_count"],
        "episode_counts": {s: len(m.episodes) for s, m in protocol.manifests.items()},
        "duplicate_content_groups": len(payload["duplicate_aliases"]), "summary": windows["summary"],
        "test_pixels_opened": False, "rgb_decode_calls": 0, "model_calls": 0,
        "wall_seconds": time.perf_counter() - started}
    if not audit.exists():
        write_frozen_json(audit, result)
    print(json.dumps({k: result[k] for k in ("status", "suite", "episode_counts", "summary", "protocol_sha256", "windows_sha256")}, indent=2), flush=True)


if __name__ == "__main__":
    main()

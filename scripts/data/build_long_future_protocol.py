"""CPU-only immutable Long episode inventory; no image decoding or model use."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from cti_vla.data.experiment_protocol import write_frozen_json
from cti_vla.data.identity import file_sha256
from cti_vla.data.long_future_windows import build_long_future_protocol, load_long_future_protocol, planned_future_episodes

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--asset-manifest", type=Path)
    parser.add_argument("--registration", type=Path)
    parser.add_argument("--data-directory", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--audit-output", type=Path)
    args = parser.parse_args()
    project = args.project_root.resolve()
    if ROOT != project and project not in ROOT.parents:
        raise ValueError("source snapshot must belong to project root")
    asset = args.asset_manifest or project / "configs/assets/libero_long_rlds.json"
    registration = args.registration or project / "configs/experiments/g1_future_long_data_v1.json"
    data = args.data_directory or project / "data/modified_libero_rlds/libero_10_no_noops/1.0.0"
    output = args.output or project / "configs/manifests/long_future_v1/protocol.json"
    audit_path = args.audit_output or project / "results/g1_future_long/data/protocol_audit.json"
    for path in (asset, registration, data, output, audit_path):
        if project not in path.resolve().parents:
            raise ValueError("Long data inputs/outputs must remain inside project")
    for path in (output, audit_path):
        if ROOT != project and ROOT in path.resolve().parents:
            raise ValueError("immutable source snapshot cannot receive data outputs")
    start = time.perf_counter()
    payload = build_long_future_protocol(data, asset, registration, progress=lambda e: print(json.dumps(e), flush=True))
    write_frozen_json(output, payload)
    protocol = load_long_future_protocol(output, asset, registration)
    audit = {"schema_version": 1, "status": "verified_real_long_metadata_inventory", "suite": "libero_10",
             "protocol_sha256": file_sha256(output), "protocol_signature": payload["content_signature"],
             "source_signature": payload["source_signature"], "source_files": payload["source_files"],
             "summary": payload["summary"], "selected_episode_counts": {s: len(refs) for s, refs in planned_future_episodes(protocol).items()},
             "inventory_scope": payload["inventory_scope"], "test_pixels_opened": False,
             "rgb_decode_calls": 0, "model_calls": 0, "wall_seconds": time.perf_counter() - start}
    write_frozen_json(audit_path, audit)
    print(json.dumps({"status": audit["status"], "summary": audit["summary"], "protocol_sha256": audit["protocol_sha256"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()

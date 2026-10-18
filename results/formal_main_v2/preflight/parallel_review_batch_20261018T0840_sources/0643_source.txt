"""CPU-only fixed150 Long h8 windows and conservative observed-change audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from cti_vla.data.experiment_protocol import signed_payload, write_frozen_json
from cti_vla.data.identity import file_sha256
from cti_vla.data.long_future_windows import build_future_windows, load_future_windows, load_long_future_protocol

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--asset-manifest", type=Path)
    parser.add_argument("--registration", type=Path)
    parser.add_argument("--data-directory", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--diagnostics-output", type=Path)
    parser.add_argument("--audit-output", type=Path)
    args = parser.parse_args()
    project = args.project_root.resolve()
    if ROOT != project and project not in ROOT.parents:
        raise ValueError("source snapshot must belong to project root")
    protocol_path = args.protocol or project / "configs/manifests/long_future_v1/protocol.json"
    asset = args.asset_manifest or project / "configs/assets/libero_long_rlds.json"
    registration = args.registration or project / "configs/experiments/g1_future_long_data_v1.json"
    data = args.data_directory or project / "data/modified_libero_rlds/libero_10_no_noops/1.0.0"
    output = args.output or project / "configs/manifests/long_future_v1/windows.json"
    diagnostics_path = args.diagnostics_output or project / "results/g1_future_long/data/h8_endpoint_changes.json"
    audit_path = args.audit_output or project / "results/g1_future_long/data/window_audit.json"
    for path in (protocol_path, asset, registration, data, output, diagnostics_path, audit_path):
        if project not in path.resolve().parents:
            raise ValueError("Long data inputs/outputs must remain inside project")
    for path in (output, diagnostics_path, audit_path):
        if ROOT != project and ROOT in path.resolve().parents:
            raise ValueError("immutable source snapshot cannot receive data outputs")
    start = time.perf_counter()
    protocol = load_long_future_protocol(protocol_path, asset, registration)
    manifest, changes = build_future_windows(protocol, data, asset, progress=lambda e: print(json.dumps(e), flush=True))
    write_frozen_json(output, manifest)
    load_future_windows(output, protocol)
    changes.pop("content_signature")
    write_frozen_json(diagnostics_path, signed_payload({**changes, "window_manifest_sha256": file_sha256(output)},
                                                      "cti-vla:long-future-endpoint-diagnostics:v1"))
    audit = {"schema_version": 1, "status": "verified_real_long150_windows_no_training", "suite": "libero_10",
             "manifest_sha256": file_sha256(output), "manifest_signature": manifest["content_signature"],
             "protocol_sha256": file_sha256(protocol_path), "diagnostics_sha256": file_sha256(diagnostics_path),
             "source_files": manifest["source_files"], "summary": manifest["summary"],
             "test_pixels_opened": False, "decoded_episodes": {"train": 30, "validation": 20, "test": 0},
             "model_calls": 0, "wall_seconds": time.perf_counter() - start,
             "limitations": "Source-audited timing, no independent simulator regeneration. Descriptive changes do not establish semantic subtask changes. No selection by endpoint diagnostics."}
    write_frozen_json(audit_path, audit)
    print(json.dumps({"status": audit["status"], "windows": len(manifest["windows"]), "manifest_sha256": audit["manifest_sha256"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()

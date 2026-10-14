"""CPU-only G1-F window audit; preserves original splits and writes no weights."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from cti_vla.data.experiment_protocol import load_experiment_protocol, write_frozen_json
from cti_vla.data.future_windows import build_future_windows, load_future_windows
from cti_vla.data.identity import file_sha256

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--protocol", type=Path, default=ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")
    parser.add_argument("--asset-manifest", type=Path, default=ROOT / "configs/assets/libero_spatial_rlds.json")
    parser.add_argument("--data-directory", type=Path, default=ROOT / "data/modified_libero_rlds/libero_spatial_no_noops/1.0.0")
    parser.add_argument("--output", type=Path, default=ROOT / "configs/manifests/spatial_future_v1/windows.json")
    parser.add_argument("--audit-output", type=Path, default=ROOT / "results/g1_future/data_window_audit.json")
    args = parser.parse_args()
    project = args.project_root.resolve()
    for path in (args.output, args.audit_output):
        if project not in path.resolve().parents:
            raise ValueError("future outputs must stay within the declared project")
    start = time.perf_counter()
    protocol = load_experiment_protocol(args.protocol)
    manifest = build_future_windows(protocol, args.data_directory, args.asset_manifest,
                                    progress=lambda event: print(json.dumps(event), flush=True))
    write_frozen_json(args.output, manifest)
    validated = load_future_windows(args.output, protocol)
    audit = {"schema_version": 1, "status": "verified_real_rlds_windows_no_training", "gpu_calls": 0,
             "manifest_sha256": file_sha256(args.output), "manifest_signature": validated["content_signature"],
             "summary": validated["summary"], "source_files": validated["source_files"], "exclusions": validated["exclusions"],
             "wall_seconds": time.perf_counter() - start,
             "raw_data_scope": "Only the 30 train and 20 effective-validation episodes decoded; no test observations/model inputs",
             "limitations": "Released RLDS has no raw-demo timestamps or original demo index; alignment audited from pinned upstream source, not independently regenerated simulation"}
    # Timing changes across repeated audits; keep each verification receipt separately.
    write_frozen_json(args.audit_output, audit)
    print(json.dumps({"status": audit["status"], "windows": len(validated["windows"]), "manifest_signature": validated["content_signature"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()

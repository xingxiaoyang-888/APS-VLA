"""CPU-only 10-development/40-sealed-final initial states for each of10 tasks."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from cti_vla.data.formal_initial_states import prepare_formal_initial_states
from cti_vla.data.formal_windows import SUITES

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=SUITES, required=True)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    args = parser.parse_args()
    project = args.project_root.resolve()
    if ROOT != project and project not in ROOT.parents:
        raise ValueError("source snapshot must belong to project")
    output = project / "configs/manifests/formal_main_v2" / args.suite / "initial_states"
    if ROOT != project and ROOT in output.resolve().parents:
        raise ValueError("immutable source snapshot must not receive outputs")
    receipt = prepare_formal_initial_states(project, args.suite)
    print(json.dumps({k: receipt[k] for k in ("status", "suite", "development_count", "sealed_final_count",
        "inherited_development_rows", "cross_split_content_hash_intersection", "development_sha256", "final_registry_sha256")}, indent=2), flush=True)


if __name__ == "__main__":
    main()

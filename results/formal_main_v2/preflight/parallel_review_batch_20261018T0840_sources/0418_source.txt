"""Freeze Long task0/3/5 and official state split, without any simulator/GPU."""
import argparse
import json
from pathlib import Path
from cti_vla.data.long_initial_states import build_long_initial_states, register_long_tasks

ROOT = Path(__file__).resolve().parents[2]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--libero-source", type=Path, default=ROOT / "external/LIBERO")
    parser.add_argument("--official-source", type=Path, default=ROOT / "external/openvla-oft")
    parser.add_argument("--output", type=Path, default=ROOT / "configs/manifests/long_initial_states_v1")
    parser.add_argument("--register-only", action="store_true")
    args = parser.parse_args()
    function = register_long_tasks if args.register_only else build_long_initial_states
    print(json.dumps(function(args.libero_source, args.official_source, args.output), ensure_ascii=False), flush=True)

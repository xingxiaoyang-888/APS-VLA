"""Freeze G0/G1 observations, exclusions, and official LIBERO initial states."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cti_vla.data.experiment_protocol import INITIAL_STATE_SEED, prepare_observation_protocol
from cti_vla.data.initial_states import prepare_initial_state_manifests


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    observations = commands.add_parser("observations")
    observations.add_argument("--source-directory", type=Path, required=True)
    observations.add_argument("--output-directory", type=Path, required=True)
    observations.add_argument("--exposure-evidence", type=Path, required=True)
    states = commands.add_parser("initial-states")
    states.add_argument("--libero-root", type=Path, required=True)
    states.add_argument("--source-revision", required=True)
    states.add_argument("--development-tasks", type=Path, required=True)
    states.add_argument("--output-directory", type=Path, required=True)
    states.add_argument("--seed", type=int, default=INITIAL_STATE_SEED)
    states.add_argument("--environment-seed", type=int, default=0)
    args = parser.parse_args()
    if args.command == "observations":
        result = prepare_observation_protocol(args.source_directory, args.output_directory, args.exposure_evidence)
        summary = {"status": "frozen_observation_protocol", "content_signature": result["content_signature"],
                   "panels": result["panels"], "output_directory": str(args.output_directory)}
    else:
        result = prepare_initial_state_manifests(args.libero_root, args.output_directory,
                    source_revision=args.source_revision, development_tasks_path=args.development_tasks,
                    seed=args.seed, environment_seed=args.environment_seed)
        summary = {"status": result["status"], "development_count": result["development_count"],
                   "test_count": result["test_count"], "split_rule": result["source"]["split_rule"],
                   "output_directory": str(args.output_directory)}
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

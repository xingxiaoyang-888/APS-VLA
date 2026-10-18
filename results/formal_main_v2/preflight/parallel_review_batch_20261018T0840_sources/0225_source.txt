"""Freeze a CPU-only seed23/41 engineering-inheritance contract; no GPU calls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation.future_seed_reuse import (
    SCHEMA, function_hashes, module_structure_hash, load_long_seed_reuse, source_hashes)
from cti_vla.evaluation.teacher_diagnostics import json_signature


def register(args):
    root = args.project_root.resolve()
    parent = args.parent_run.resolve()
    paths = {
        "config":args.parent_config, "source_inventory":args.parent_source_inventory,
        "runner":args.parent_runner, "input_acceptance":parent / "inputs/input_acceptance.json",
        "input_journal":parent / "inputs/calls.jsonl", "f01_acceptance":parent / "acceptance/f01_acceptance.json",
        "f01_finalization":parent / "acceptance/acceptance_finalization.json",
        "cache_index":parent / "training/cache_index.json", "windows":args.windows,
        "protocol":args.protocol, "asset_manifest":args.asset_manifest}
    entries = {}
    for key, path in paths.items():
        path = path.resolve()
        if root not in path.parents:
            raise ValueError("all reuse evidence must reside within the main project")
        entries[key] = {"path":path.relative_to(root).as_posix(), "sha256":file_sha256(path)}
    config = json.loads(args.target_config.read_text(encoding="utf-8"))
    value = {"schema":SCHEMA, "allowed_config_changes":["seed", "run_id"],
        "experiment_registration_sha256":file_sha256(args.source_root / "configs/experiments/g1_future_long_multiseed_v1.json"),
        "target_seed":config["seed"], "target_run_id":config["run_id"],
        "target_config_identity_sha256":json_signature(config),
        "target_source_files":source_hashes(args.source_root), "parent_files":entries,
        "parent_runner_module_structure_sha256":module_structure_hash(args.parent_runner),
        "protected_runner_functions":function_hashes(args.parent_runner)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise ValueError("reuse registration must be new and cannot overwrite a prior contract")
    # The unapproved candidate is never a passed receipt. Validate all original
    # evidence before atomically installing the requested registration.
    candidate = args.output.with_suffix(args.output.suffix + ".candidate")
    if candidate.exists():
        raise ValueError("unfinished candidate exists")
    candidate.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        load_long_seed_reuse(candidate, config=config, project_root=root, source_root=args.source_root)
        candidate.replace(args.output)
    except BaseException:
        candidate.unlink()
        raise
    return {"status":"registered_inheritance_not_new_F01", "seed":config["seed"],
            "registration_sha256":file_sha256(args.output), "GPU_calls":0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("project-root", "source-root", "parent-run", "parent-config", "parent-source-inventory",
                 "parent-runner", "target-config", "windows", "protocol", "asset-manifest", "output"):
        parser.add_argument("--"+name, type=Path, required=True)
    print(json.dumps(register(parser.parse_args())))


if __name__ == "__main__":
    main()

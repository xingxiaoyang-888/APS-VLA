"""Read-only Long input/cache inheritance for a new64-token engineering gate.

The original128 F01 is deliberately not accepted here. The new seed17 F01
must measure the32-per-camera operator; other seeds may inherit only that
same-budget gate under an identical frozen implementation.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation.teacher_diagnostics import json_signature
from cti_vla.evaluation.future_seed_reuse import (
    read, source_hashes, _resolve, verify_reused_cache, require_fresh_seed_destinations,
)

SCHEMA = "long-g1f64-input-cache-reuse-new-f01-required-v1"
REGISTRATION = "configs/experiments/g1_future_long_k64_v1.json"
RUNNER = "scripts/run_g1_future.py"
INPUT_FUNCTIONS = ("cache_records", "make_batch", "module_hash", "training_order")
TARGET_NODES = ("FrozenFutureRepresentation", "frozen_future_target", "FUTURE_TARGET_VERSION",
                "FUTURE_PROJECTION_SEED", "FUTURE_TARGET_DIM")
PARENT_LOGICAL_PATHS = {
    "config": "configs/experiments/g1_future_long_v1.json",
    "windows": "configs/manifests/long_future_v1/windows.json",
    "protocol": "configs/manifests/long_future_v1/protocol.json",
    "source_inventory": "results/g1_future_long/source_g1_future_long_v1.json",
    "cache_index": "results/g1_future_long_v1/training/cache_index.json",
    "input_acceptance": "results/g1_future_long_v1/inputs/input_acceptance.json",
    "input_journal": "results/g1_future_long_v1/inputs/calls.jsonl",
}


def named_ast_hashes(path, names):
    wanted = set(names)
    found = {}
    for node in ast.parse(Path(path).read_text(encoding="utf-8")).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            keys = [node.name]
        elif isinstance(node, ast.Assign):
            keys = [n.id for n in node.targets if isinstance(n, ast.Name)]
        else:
            keys = []
        for name in wanted.intersection(keys):
            found[name] = hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
    if set(found) != wanted:
        raise ValueError("incomplete protected input/cache implementation")
    return found


@dataclass(frozen=True)
class LongBudgetReuse:
    registration_sha256: str
    input_acceptance_sha256: str
    parent_config: dict
    cache_index: list
    watched_files: dict
    receipt: dict


def load_long_budget_reuse(registration_path, *, config, project_root, source_root, expected_paths=None):
    """Validate original F00 and all cache identities; this never passes F01."""
    from cti_vla.data.long_future_windows import load_long_future_protocol, load_future_windows
    from cti_vla.evaluation.future_input_acceptance import (
        require_long_input_acceptance, select_input_windows, verify_input_acceptance_journal,
    )
    project_root, source_root = Path(project_root).resolve(), Path(source_root).resolve()
    registration_path = Path(registration_path).resolve()
    reg = read(registration_path)
    if reg.get("schema") != SCHEMA or reg.get("allowed_config_changes") != ["seed", "run_id", "tokens_per_camera"]:
        raise ValueError("invalid64-token input/cache reuse registration")
    if type(config.get("seed")) is not int or config["seed"] not in (17, 23, 41):
        raise ValueError("64-token round is restricted to seeds17/23/41")
    if config.get("run_id") != f"g1_future_long_k64_seed{config['seed']}_v1" or config.get("tokens_per_camera") != 32:
        raise ValueError("64-token target needs its independent run and32-per-camera budget")
    if (reg.get("target_config_identity_sha256") != json_signature(config)
            or reg.get("target_seed") != config["seed"] or reg.get("target_run_id") != config["run_id"]):
        raise ValueError("64-token target configuration changed")
    current_sources = source_hashes(source_root)
    if reg.get("target_source_files") != current_sources:
        raise ValueError("registered64-token implementation changed")
    experiment_path = source_root / REGISTRATION
    experiment = read(experiment_path)
    if reg.get("experiment_registration_sha256") != file_sha256(experiment_path):
        raise ValueError("64-token experiment preregistration changed")
    target = experiment["new_configs"][str(config["seed"])]
    target_path = _resolve(source_root, target["path"])
    if file_sha256(target_path) != target["sha256"] or read(target_path) != config:
        raise ValueError("target differs from preregistered64-token config")
    required = set(PARENT_LOGICAL_PATHS) | {"runner", "asset_manifest"}
    if set(reg.get("parent_files", {})) != required:
        raise ValueError("64-token cache inheritance requires complete parent input evidence")
    paths, watched = {}, {str(registration_path): file_sha256(registration_path),
                         str(experiment_path): file_sha256(experiment_path), str(target_path): file_sha256(target_path)}
    for key, item in reg["parent_files"].items():
        path = _resolve(project_root, item["path"])
        if file_sha256(path) != item["sha256"]:
            raise ValueError("parent input/cache evidence changed: " + key)
        paths[key] = path
        watched[str(path)] = item["sha256"]
    for key, path in (expected_paths or {}).items():
        if key not in paths or paths[key] != Path(path).resolve():
            raise ValueError("explicit CLI and64-token input reuse differ: " + key)
    if any(experiment.get("frozen_evidence_sha256", {}).get(logical) != file_sha256(paths[key])
           for key, logical in PARENT_LOGICAL_PATHS.items()):
        raise ValueError("parent input/cache differs from independent preregistered hashes")
    parent = read(paths["config"])
    if (parent.get("suite") != "libero_10" or parent.get("seed") != 17
            or parent.get("run_id") != "g1_future_long_v1" or parent.get("tokens_per_camera") != 64):
        raise ValueError("input/cache parent must be original Long128 seed17")
    allowed = {"seed", "run_id", "tokens_per_camera"}
    if {k: v for k, v in parent.items() if k not in allowed} != {k: v for k, v in config.items() if k not in allowed}:
        raise ValueError("only seed/run_id/budget may differ from the original Long config")
    f00, inventory = read(paths["input_acceptance"]), read(paths["source_inventory"])
    original = f00["source_files"]
    inv_hash = hashlib.sha256(json.dumps(inventory["files"], sort_keys=True).encode()).hexdigest()
    if inventory.get("source_sha256") != inv_hash or any(inventory["files"].get(k) != v for k, v in original.items()):
        raise ValueError("original input/cache source inventory is inconsistent")
    if original.get(RUNNER) != file_sha256(paths["runner"]):
        raise ValueError("parent runner differs from the accepted cache producer")
    # These are the actual dependencies of F00 and feature-cache production.
    # Only selector training/deployment budget changes receive a fresh F01.
    prefixes = ("src/cti_vla/data/", "src/cti_vla/models/", "src/cti_vla/selection/", "src/cti_vla_baselines/")
    exact = {"src/cti_vla/evaluation/libero_runtime.py", "src/cti_vla/evaluation/teacher_diagnostics.py",
             "src/cti_vla/evaluation/future_input_acceptance.py"}
    for relative, sha in original.items():
        if relative.startswith(prefixes) or relative in exact:
            if current_sources.get(relative) != sha:
                raise ValueError("accepted input/cache/model dependency changed: " + relative)
    if named_ast_hashes(paths["runner"], INPUT_FUNCTIONS) != named_ast_hashes(source_root / RUNNER, INPUT_FUNCTIONS):
        raise ValueError("input/cache producer functions changed")
    target_relative = "src/cti_vla/training/future_auxiliary.py"
    parent_target = paths["runner"].parents[1] / target_relative
    if file_sha256(parent_target) != original.get(target_relative):
        raise ValueError("parent target representation source changed")
    if named_ast_hashes(parent_target, TARGET_NODES) != named_ast_hashes(source_root / target_relative, TARGET_NODES):
        raise ValueError("future cache target definition changed")
    watched[str(parent_target)] = file_sha256(parent_target)
    for key, relative in (("config", PARENT_LOGICAL_PATHS["config"]), ("windows", PARENT_LOGICAL_PATHS["windows"]),
                          ("protocol", PARENT_LOGICAL_PATHS["protocol"]), ("asset_manifest", "configs/assets/openvla_oft_libero_long.json")):
        if inventory["files"].get(relative) != file_sha256(paths[key]):
            raise ValueError("parent frozen asset/config/data identity changed")
    verifier = source_root / "scripts/verify_long_inputs.py"
    if file_sha256(verifier) != inventory["files"].get("scripts/verify_long_inputs.py"):
        raise ValueError("official input acceptance implementation changed")
    for relative in ("configs/assets/libero_long_rlds.json", "configs/experiments/g1_future_long_data_v1.json"):
        path = source_root / relative
        if file_sha256(path) != inventory["files"].get(relative):
            raise ValueError("RLDS asset/data registration changed")
        watched[str(path)] = file_sha256(path)
    protocol = load_long_future_protocol(paths["protocol"], asset_manifest=source_root / "configs/assets/libero_long_rlds.json",
        registration_path=source_root / "configs/experiments/g1_future_long_data_v1.json")
    manifest = load_future_windows(paths["windows"], protocol)
    require_long_input_acceptance(f00, config=parent, window_manifest_sha256=file_sha256(paths["windows"]),
        protocol_sha256=file_sha256(paths["protocol"]), asset_manifest_sha256=file_sha256(paths["asset_manifest"]),
        source_files=original, verification_script_sha256=file_sha256(verifier), selected_windows=select_input_windows(manifest, protocol))
    verify_input_acceptance_journal(paths["input_journal"], f00)
    index = read(paths["cache_index"])
    registered = {r["window_id"]: r for r in manifest["windows"]}
    if len(index) != 150 or {e["identity"]["window"]["window_id"] for e in index} != set(registered):
        raise ValueError("input reuse needs the original complete150-window cache")
    producer = {"source_files": original, "asset_manifest_sha256": file_sha256(paths["asset_manifest"]),
                "model_revision": config["model_revision"], "dataset_statistics_sha256": f00["dataset_statistics_sha256"]}
    for entry in index:
        identity = entry["identity"]
        expected = {"window": registered[identity["window"]["window_id"]], "config_sha256": file_sha256(paths["config"]),
                    "window_manifest_sha256": file_sha256(paths["windows"]), "producer": producer}
        if identity != expected or any(entry.get(k) is not True for k in
                ("window_alignment_validated", "future_target_detached", "checkpoint_normalization")):
            raise ValueError("original cache producer/config/window identity differs")
    receipt = {"schema": SCHEMA, "status": "verified_input_cache_reuse_new64_F01_required",
        "target_seed": config["seed"], "target_run_id": config["run_id"], "tokens_per_camera": 32,
        "target_config_identity_sha256": json_signature(config), "registration_sha256": file_sha256(registration_path),
        "parent_input_acceptance_sha256": file_sha256(paths["input_acceptance"]), "target_source_files": current_sources,
        "parent_files": reg["parent_files"], "new_GPU_calls": 0, "inherited_old128_F01": False,
        "scope": "Original detached inputs/cache only; new64-budget F01 required before any training."}
    return LongBudgetReuse(file_sha256(registration_path), file_sha256(paths["input_acceptance"]), parent, index, watched, receipt)


def require_budget_f01(acceptance_path, *, config, source_root, window_manifest_sha256, input_acceptance_sha256):
    """Accept only the new64 seed17 gate; seed23/41 inherit its operator checks."""
    from cti_vla.evaluation.future_runtime import require_future_f01
    root, path = Path(source_root).resolve(), Path(acceptance_path).resolve()
    experiment_path = root / REGISTRATION
    experiment = read(experiment_path)
    anchor = experiment["new_configs"]["17"]
    anchor_path = _resolve(root, anchor["path"])
    reference = read(anchor_path)
    if file_sha256(anchor_path) != anchor["sha256"]:
        raise ValueError("64-token F01 configuration changed from preregistration")
    if reference.get("seed") != 17 or reference.get("run_id") != "g1_future_long_k64_seed17_v1" or reference.get("tokens_per_camera") != 32:
        raise ValueError("64-token engineering anchor must be new seed17")
    if (config.get("seed") not in (17, 23, 41) or config.get("run_id") != f"g1_future_long_k64_seed{config['seed']}_v1"
            or {k: v for k, v in reference.items() if k not in ("seed", "run_id")} !=
               {k: v for k, v in config.items() if k not in ("seed", "run_id")}):
        raise ValueError("same-budget F01 inheritance allows only seed/run_id changes")
    report = read(path)
    require_future_f01(report, pair_id=json_signature(reference), window_manifest_sha256=window_manifest_sha256,
        model_revision=config["model_revision"], suite="libero_10", input_acceptance_sha256=input_acceptance_sha256,
        visual_tokens=64, per_camera_budgets=(32, 32))
    if report.get("config_file_sha256") != file_sha256(anchor_path) or report.get("source_files") != source_hashes(root):
        raise ValueError("64-token F01 source/config differs from current frozen implementation")
    finalized_path = path.parent / "acceptance_finalization.json"
    finalized = read(finalized_path)
    if (finalized.get("status") != "verified" or finalized.get("checkpoint_unchanged") is not True
            or finalized.get("result_status") != "passed" or finalized.get("result_sha256") != file_sha256(path)
            or finalized.get("job_id") != report.get("job_id")):
        raise ValueError("64-token F01 must have complete matching finalization")
    watched = {str(p): file_sha256(p) for p in (path, finalized_path, anchor_path, experiment_path)}
    return {"accepted_pair_id": json_signature(reference), "report_sha256": file_sha256(path), "watched_files": watched,
        "receipt": {"status": "verified_same64_budget_F01", "target_seed": config["seed"], "accepted_seed": 17,
            "accepted_pair_id": json_signature(reference), "report_sha256": file_sha256(path),
            "visual_tokens": 64, "per_camera_budgets": [32, 32], "same_frozen_source": True,
            "measured_for_target_seed": config["seed"] == 17}}

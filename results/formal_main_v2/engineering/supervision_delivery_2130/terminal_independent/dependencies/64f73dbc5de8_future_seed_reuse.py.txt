"""Explicit inheritance of seed17 engineering evidence; never a new F01 run.

Only training seed/run_id may change. Parent evidence and cached tensors retain
their original identity, while each new arm starts from a fresh initialization.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation.teacher_diagnostics import json_signature

SCHEMA = "long-g1f-seed-only-engineering-reuse-v1"
PROTECTED_FUNCTIONS = ("train_pair", "training_order", "validate_hard", "acceptance", "module_hash", "make_batch", "cache_records")
ORCHESTRATION_FUNCTIONS = {"resolve_suite", "require_input_gate", "run", "main"}
RUNNER = "scripts/run_g1_future.py"
REUSE_SOURCE = "src/cti_vla/evaluation/future_seed_reuse.py"
ADDED_SOURCES = {REUSE_SOURCE, "src/cti_vla/evaluation/future_dense_reuse.py",
                 "src/cti_vla/evaluation/future_multiseed.py"}
# Evaluation-only registration logic; no training/cache/policy caller imports it.
EVALUATION_ONLY_CHANGES = {"src/cti_vla/evaluation/future_trials.py"}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def source_hashes(root):
    root = Path(root).resolve()
    return {p.relative_to(root).as_posix(): file_sha256(p)
            for p in sorted((root / "src").rglob("*.py")) + [root / RUNNER]}


def function_hashes(path):
    nodes = {n.name: n for n in ast.parse(Path(path).read_text(encoding="utf-8")).body
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if not set(PROTECTED_FUNCTIONS) <= nodes.keys():
        raise ValueError("parent/current runner lacks a protected implementation")
    return {name: hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
            for name, node in nodes.items() if name not in ORCHESTRATION_FUNCTIONS}


def module_structure_hash(path):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    tree.body = [n for n in tree.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return hashlib.sha256(ast.dump(tree, include_attributes=False).encode()).hexdigest()


def _resolve(root, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("reuse evidence paths must be project relative")
    path = (root / relative).resolve()
    if root not in path.parents or not path.is_file():
        raise ValueError("reuse evidence missing or outside the project")
    return path


@dataclass(frozen=True)
class LongSeedReuse:
    registration_sha256: str
    parent_pair_id: str
    input_acceptance_sha256: str
    f01_report_sha256: str
    parent_config: dict
    cache_index: list
    watched_files: dict
    receipt: dict


def load_long_seed_reuse(registration_path, *, config, project_root, source_root,
                         expected_paths=None):
    """CPU-only evidence verification; does not read cache tensors or a model.

    ``expected_paths`` maps parent_files keys to the caller's explicitly supplied
    paths, preventing a CLI argument from silently selecting different evidence.
    """
    from cti_vla.data.long_future_windows import load_long_future_protocol, load_future_windows
    from cti_vla.evaluation.future_input_acceptance import (
        require_long_input_acceptance, select_input_windows, verify_input_acceptance_journal)
    from cti_vla.evaluation.future_runtime import require_future_f01
    project_root, source_root = Path(project_root).resolve(), Path(source_root).resolve()
    registration_path = Path(registration_path).resolve()
    reg = read(registration_path)
    if reg.get("schema") != SCHEMA or reg.get("allowed_config_changes") != ["seed", "run_id"]:
        raise ValueError("invalid seed-only engineering reuse registration")
    if config.get("seed") not in (23, 41) or type(config.get("seed")) is not int:
        raise ValueError("engineering reuse is limited to authorized seeds23/41")
    if config.get("run_id") != f"g1_future_long_seed{config['seed']}_v1":
        raise ValueError("new seed requires its independently named run")
    if reg.get("target_config_identity_sha256") != json_signature(config):
        raise ValueError("reuse target configuration changed")
    if reg.get("target_seed") != config["seed"] or reg.get("target_run_id") != config["run_id"]:
        raise ValueError("reuse target seed/run identity changed")
    current_sources = source_hashes(source_root)
    if reg.get("target_source_files") != current_sources:
        raise ValueError("registered current implementation changed")
    experiment_path = source_root / "configs/experiments/g1_future_long_multiseed_v1.json"
    experiment = read(experiment_path)
    if reg.get("experiment_registration_sha256") != file_sha256(experiment_path):
        raise ValueError("frozen multiseed experiment registration changed")
    target = experiment["new_configs"][str(config["seed"])]
    target_path = _resolve(source_root, target["path"])
    if file_sha256(target_path) != target["sha256"] or read(target_path) != config:
        raise ValueError("target configuration differs from the preregistered file")
    required = {"config", "source_inventory", "runner", "input_acceptance", "input_journal",
                "f01_acceptance", "f01_finalization", "cache_index", "windows", "protocol", "asset_manifest"}
    if set(reg.get("parent_files", {})) != required:
        raise ValueError("reuse registration must bind the complete parent evidence")
    paths, watched = {}, {str(registration_path): file_sha256(registration_path),
                         str(experiment_path):file_sha256(experiment_path), str(target_path):file_sha256(target_path)}
    for key, item in reg["parent_files"].items():
        path = _resolve(project_root, item["path"])
        if file_sha256(path) != item["sha256"]:
            raise ValueError("parent evidence changed: " + key)
        paths[key] = path
        watched[str(path)] = item["sha256"]
    for key, path in (expected_paths or {}).items():
        if key not in paths or paths[key] != Path(path).resolve():
            raise ValueError("explicit CLI and reuse evidence differ: " + key)
    preregistered = {
        "config":"configs/experiments/g1_future_long_v1.json",
        "protocol":"configs/manifests/long_future_v1/protocol.json",
        "windows":"configs/manifests/long_future_v1/windows.json",
        "source_inventory":"results/g1_future_long/source_g1_future_long_v1.json",
        "cache_index":"results/g1_future_long_v1/training/cache_index.json",
        "input_acceptance":"results/g1_future_long_v1/inputs/input_acceptance.json",
        "input_journal":"results/g1_future_long_v1/inputs/calls.jsonl",
        "f01_acceptance":"results/g1_future_long_v1/acceptance/f01_acceptance.json",
        "f01_finalization":"results/g1_future_long_v1/acceptance/acceptance_finalization.json"}
    if any(experiment.get("frozen_evidence_sha256", {}).get(logical) != file_sha256(paths[key])
           for key, logical in preregistered.items()):
        raise ValueError("parent evidence differs from independently preregistered hashes")
    parent = read(paths["config"])
    if parent.get("suite") != "libero_10" or parent.get("seed") != 17 or parent.get("run_id") != "g1_future_long_v1":
        raise ValueError("engineering parent must be the original Long seed17")
    if {k:v for k,v in parent.items() if k not in ("seed", "run_id")} != {
            k:v for k,v in config.items() if k not in ("seed", "run_id")}:
        raise ValueError("only training seed and run_id may differ from the parent")
    f00, f01 = read(paths["input_acceptance"]), read(paths["f01_acceptance"])
    original = f00["source_files"]
    inventory = read(paths["source_inventory"])
    inv_hash = hashlib.sha256(json.dumps(inventory["files"], sort_keys=True).encode()).hexdigest()
    if inventory.get("source_sha256") != inv_hash or any(inventory["files"].get(k) != v for k,v in original.items()):
        raise ValueError("parent source inventory is inconsistent")
    if original.get(RUNNER) != file_sha256(paths["runner"]):
        raise ValueError("parent runner does not match actual accepted source")
    additions = set(current_sources) - set(original)
    if REUSE_SOURCE not in additions or not additions <= ADDED_SOURCES or set(original) - set(current_sources):
        raise ValueError("unreviewed source added/removed for engineering reuse")
    if any(current_sources[k] != v for k,v in original.items() if k not in {RUNNER, *EVALUATION_ONLY_CHANGES}):
        raise ValueError("model/loss/data/selector/packing source changed since acceptance")
    protected = function_hashes(paths["runner"])
    if reg.get("protected_runner_functions") != protected or function_hashes(source_root / RUNNER) != protected:
        raise ValueError("training/cache/acceptance function semantics changed")
    structure = module_structure_hash(paths["runner"])
    if reg.get("parent_runner_module_structure_sha256") != structure or module_structure_hash(source_root / RUNNER) != structure:
        raise ValueError("runner imports/globals/module structure changed")
    for key, relative in (("config", "configs/experiments/g1_future_long_v1.json"),
                          ("windows", "configs/manifests/long_future_v1/windows.json"),
                          ("protocol", "configs/manifests/long_future_v1/protocol.json"),
                          ("asset_manifest", "configs/assets/openvla_oft_libero_long.json")):
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
    protocol = load_long_future_protocol(paths["protocol"],
        asset_manifest=source_root / "configs/assets/libero_long_rlds.json",
        registration_path=source_root / "configs/experiments/g1_future_long_data_v1.json")
    manifest = load_future_windows(paths["windows"], protocol)
    require_long_input_acceptance(f00, config=parent, window_manifest_sha256=file_sha256(paths["windows"]),
        protocol_sha256=file_sha256(paths["protocol"]), asset_manifest_sha256=file_sha256(paths["asset_manifest"]),
        source_files=original, verification_script_sha256=file_sha256(verifier),
        selected_windows=select_input_windows(manifest, protocol))
    verify_input_acceptance_journal(paths["input_journal"], f00)
    require_future_f01(f01, pair_id=json_signature(parent), window_manifest_sha256=file_sha256(paths["windows"]),
        model_revision=config["model_revision"], suite="libero_10",
        input_acceptance_sha256=file_sha256(paths["input_acceptance"]))
    finalized = read(paths["f01_finalization"])
    if (f01["source_files"] != original or finalized.get("status") != "verified"
            or finalized.get("checkpoint_unchanged") is not True
            or finalized.get("result_sha256") != file_sha256(paths["f01_acceptance"])
            or finalized.get("result_status") != "passed" or finalized.get("job_id") != f01.get("job_id")):
        raise ValueError("parent F01 finalization changed")
    index = read(paths["cache_index"])
    registered = {r["window_id"]: r for r in manifest["windows"]}
    if len(index) != 150 or {e["identity"]["window"]["window_id"] for e in index} != set(registered):
        raise ValueError("reuse requires the complete registered150-window cache")
    producer = {"source_files":original, "asset_manifest_sha256":file_sha256(paths["asset_manifest"]),
        "model_revision":config["model_revision"], "dataset_statistics_sha256":f00["dataset_statistics_sha256"]}
    for entry in index:
        identity = entry["identity"]
        expected = {"window":registered[identity["window"]["window_id"]],
            "config_sha256":file_sha256(paths["config"]), "window_manifest_sha256":file_sha256(paths["windows"]), "producer":producer}
        if identity != expected or any(entry.get(k) is not True for k in
                ("window_alignment_validated", "future_target_detached", "checkpoint_normalization")):
            raise ValueError("cached feature producer/config/window identity differs")
    receipt = {"schema":SCHEMA, "status":"verified_inheritance_not_new_F01", "target_seed":config["seed"],
        "target_run_id":config["run_id"], "target_config_identity_sha256":json_signature(config),
        "registration_sha256":file_sha256(registration_path), "parent_pair_id":json_signature(parent),
        "parent_f01_report_sha256":file_sha256(paths["f01_acceptance"]),
        "parent_input_acceptance_sha256":file_sha256(paths["input_acceptance"]),
        "target_source_files":current_sources, "parent_files":reg["parent_files"],
        "new_engineering_GPU_calls":0, "scope":"Inherited seed17 engineering evidence; fresh target-seed training, not newly measured target-seed F01 gradients."}
    return LongSeedReuse(file_sha256(registration_path), json_signature(parent),
        file_sha256(paths["input_acceptance"]), file_sha256(paths["f01_acceptance"]), parent, index, watched, receipt)


def verify_reused_cache(contract, feature_root):
    """Read-only verification against the original receipts, never self-sign."""
    feature_root = Path(feature_root).resolve()
    for entry in contract.cache_index:
        path = Path(entry["path"]).resolve()
        if feature_root not in path.parents or not path.is_file():
            raise ValueError("parent cache absent or outside explicit feature root")
        expected = {k:v for k,v in entry.items() if k != "path"}
        if read(path.with_suffix(".json")) != expected or file_sha256(path) != entry["cache_sha256"] or path.stat().st_size != entry["cache_bytes"]:
            raise ValueError("parent cached tensor/receipt changed")
    return contract.cache_index


def require_fresh_seed_destinations(output, checkpoints):
    for name, path in (("output", Path(output)), ("checkpoints", Path(checkpoints))):
        if path.exists() and (not path.is_dir() or any(path.iterdir())):
            raise ValueError("seed extension requires empty new " + name + "; resume is forbidden")

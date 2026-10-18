"""Inventory official LIBERO states and freeze disjoint development/test sets."""

from __future__ import annotations

import ast
import collections
import codecs
import hashlib
import json
from pathlib import Path
import pickle
import random
import types
from typing import Any

import numpy as np

from .experiment_protocol import INITIAL_STATE_SEED, signed_payload, verify_payload, write_frozen_json
from .identity import canonical_mapping_signature, file_sha256

STATE_NAMESPACE = "cti-vla:libero-initial-state-manifest:v1"


def initial_state_sha256(values) -> str:
    """SHA256 of version prefix, int64-LE shape, and finite float64-LE bytes."""
    array = np.asarray(values)
    if array.dtype.kind not in "fiu" or array.ndim != 1 or array.size == 0 or not np.isfinite(array).all():
        raise ValueError("initial state must be a finite nonempty numeric vector")
    array = np.asarray(array, dtype="<f8")
    digest = hashlib.sha256(b"cti-vla:libero-init-state:v1\x00")
    digest.update(np.asarray(array.shape, dtype="<i8").tobytes())
    digest.update(np.ascontiguousarray(array).tobytes())
    return digest.hexdigest()


class _StateUnpickler(pickle.Unpickler):
    """Only the numeric constructors used by official torch.save state files."""

    def find_class(self, module, name):
        import torch
        allowed = {
            ("_codecs", "encode"): codecs.encode,
            ("numpy", "ndarray"): np.ndarray, ("numpy", "dtype"): np.dtype,
            ("numpy.core.multiarray", "_reconstruct"): np.core.multiarray._reconstruct,
            ("numpy._core.multiarray", "_reconstruct"): np.core.multiarray._reconstruct,
            ("numpy.core.multiarray", "scalar"): np.core.multiarray.scalar,
            ("numpy._core.multiarray", "scalar"): np.core.multiarray.scalar,
            ("collections", "OrderedDict"): collections.OrderedDict,
            ("torch._utils", "_rebuild_tensor_v2"): torch._utils._rebuild_tensor_v2,
            ("torch._utils", "_rebuild_tensor"): torch._utils._rebuild_tensor,
        }
        if (module, name) not in allowed:
            raise pickle.UnpicklingError(f"unsupported constructor in initial-state file: {module}.{name}")
        return allowed[(module, name)]


def load_official_states(path: str | Path) -> np.ndarray:
    """Read numeric .pruned_init/.pt/.pth files without arbitrary pickle globals."""
    import torch
    path = Path(path)
    if path.suffix not in {".pruned_init", ".pt", ".pth"}:
        raise ValueError("use the official .pruned_init file, not unpruned .init states")
    module = types.SimpleNamespace(__name__="cti_vla_state_pickle", Unpickler=_StateUnpickler,
                                   load=lambda stream, **kwargs: _StateUnpickler(stream, **kwargs).load())
    value = torch.load(path, map_location="cpu", pickle_module=module, weights_only=False)
    if isinstance(value, torch.Tensor):
        value = value.detach().cpu().numpy()
    if isinstance(value, (list, tuple)):
        value = [v.detach().cpu().numpy() if isinstance(v, torch.Tensor) else v for v in value]
    array = np.asarray(value)
    if array.dtype.kind not in "fiu" or array.ndim != 2 or min(array.shape) <= 0 or not np.isfinite(array).all():
        raise ValueError("official state file must contain finite numeric [states, dimensions]")
    return np.ascontiguousarray(array, dtype="<f8")


def _literal_assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"official source has no literal {name} assignment: {path}")


def official_task_catalog(libero_root: str | Path, suite: str = "libero_spatial") -> tuple[list[dict], dict]:
    root = Path(libero_root)
    benchmark = root / "libero/libero/benchmark"
    mapping_path, order_path = benchmark / "libero_suite_task_map.py", benchmark / "__init__.py"
    mapping = _literal_assignment(mapping_path, "libero_task_map")
    order = _literal_assignment(order_path, "task_orders")[0]
    names = mapping[suite]
    if len(names) != 10 or sorted(order) != list(range(10)):
        raise ValueError("expected official ten-task Spatial order")
    catalog = [{"task_id": index, "task_name": names[original]} for index, original in enumerate(order)]
    return catalog, {"task_order_index": 0, "task_map_sha256": file_sha256(mapping_path),
                     "benchmark_source_sha256": file_sha256(order_path)}


def validate_initial_state_manifest(payload: dict[str, Any]) -> None:
    verify_payload(payload, STATE_NAMESPACE)
    if payload.get("schema_version") != 1 or payload.get("suite") != "libero_spatial":
        raise ValueError("unsupported initial-state manifest")
    if payload.get("split") not in {"development", "test"} or type(payload.get("environment_seed")) is not int:
        raise ValueError("invalid initial-state split or environment seed")
    rows = payload.get("states")
    if not isinstance(rows, list) or not rows:
        raise ValueError("initial-state manifest needs a nonempty state list")
    if len({row["trial_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate trial ID")
    if len({(row["task_name"], row["source_state_index"]) for row in rows}) != len(rows):
        raise ValueError("duplicate task/state index")
    mapping = {}
    for row in rows:
        if type(row["task_id"]) is not int or not 0 <= row["task_id"] < 10:
            raise ValueError("invalid official task ID")
        if type(row["source_state_index"]) is not int or row["source_state_index"] < 0:
            raise ValueError("invalid source state index")
        if row["task_id"] in mapping and mapping[row["task_id"]] != row["task_name"]:
            raise ValueError("task ID maps to inconsistent names")
        mapping[row["task_id"]] = row["task_name"]
        if initial_state_sha256(row["initial_state"]) != row["initial_state_sha256"]:
            raise ValueError("initial state content hash mismatch")


def prepare_initial_state_manifests(libero_root: str | Path, output_directory: str | Path, *,
                                    source_revision: str, development_tasks_path: str | Path,
                                    seed: int = INITIAL_STATE_SEED, environment_seed: int = 0) -> dict:
    root, output = Path(libero_root), Path(output_directory)
    if len(source_revision) != 40 or any(c not in "0123456789abcdef" for c in source_revision):
        raise ValueError("official source revision must be a full commit SHA")
    if type(seed) is not int or type(environment_seed) is not int:
        raise ValueError("state and environment seeds must be integers")
    catalog, mapping_provenance = official_task_catalog(root)
    development_tasks_path = Path(development_tasks_path)
    development = json.loads(development_tasks_path.read_text(encoding="utf-8"))
    development_names = {row["task_name"] for row in development["tasks"]}
    if len(development_names) != 3 or not development_names <= {row["task_name"] for row in catalog}:
        raise ValueError("three frozen development tasks must match official task names")
    inventory, matrices = [], {}
    for task in catalog:
        path = root / "libero/libero/init_files/libero_spatial" / f"{task['task_name']}.pruned_init"
        states = load_official_states(path)
        hashes = [initial_state_sha256(row) for row in states]
        if len(set(hashes)) != len(hashes):
            raise ValueError(f"duplicate initial-state contents within task: {task['task_name']}")
        matrices[task["task_name"]] = states
        inventory.append({**task, "source_file": path.name, "file_sha256": file_sha256(path),
                          "count": len(states), "state_dimensions": states.shape[1], "state_sha256": hashes})
    counts = [row["count"] for row in inventory]
    if all(count >= 60 for count in counts):
        final_count, rule = 50, "official-library-disjoint-10-development-50-test"
    elif set(counts) == {50}:
        final_count, rule = 40, "official-library-fallback-10-development-40-test"
    else:
        write_frozen_json(output / "initial_state_inventory.json", {
            "schema_version": 1, "status": "blocked_inventory_requires_protocol_review",
            "suite": "libero_spatial", "source_revision": source_revision, "tasks": inventory,
            "reason": "Need >=60 states for every task, or exactly 50 for every task. Never invent states.",
        })
        raise ValueError("official state counts do not permit the preregistered disjoint protocol")
    source = {"repository": "Lifelong-Robot-Learning/LIBERO", "revision": source_revision,
              "state_file_variant": ".pruned_init", "split_seed": seed, "split_rule": rule,
              "selection_rule": "sort official task names; within each task shuffle source indices with a task-specific SHA256-seeded Random; first 10 development, next N test; sort selected source indices",
              "development_tasks_sha256": file_sha256(development_tasks_path),
              **mapping_provenance,
              "files": [{k: v for k, v in row.items() if k != "state_sha256"} for row in inventory]}
    selected = {"development": [], "test": []}
    for task in sorted(inventory, key=lambda row: row["task_name"]):
        indices = list(range(task["count"]))
        random.Random(canonical_mapping_signature({"seed": seed, "task": task["task_name"]}, namespace="cti-vla:init-state-split:v1")).shuffle(indices)
        groups = {"development": sorted(indices[:10]), "test": sorted(indices[10:10 + final_count])}
        for split, group in groups.items():
            for index in group:
                selected[split].append({
                    "trial_id": f"libero_spatial:{task['task_name']}:state-{index:04d}:env-{environment_seed}",
                    "task_id": task["task_id"], "task_name": task["task_name"],
                    "source_state_index": index, "source_file": task["source_file"],
                    "initial_state": matrices[task["task_name"]][index].tolist(),
                    "initial_state_sha256": task["state_sha256"][index],
                })
    overlap = {row["initial_state_sha256"] for row in selected["development"]} & {row["initial_state_sha256"] for row in selected["test"]}
    if overlap:
        raise ValueError("initial-state content hashes overlap development/test, including across tasks; review instead of redrawing")
    inventory_payload = {"schema_version": 1, "status": "verified_numeric_inventory_not_environment_validation",
                         "suite": "libero_spatial", "source": source, "tasks": inventory,
                         "development_count": len(selected["development"]), "test_count": len(selected["test"]),
                         "cross_split_content_hash_intersection": 0,
                         "limitations": "Only official serialized numeric states inventoried; simulator restoration and legality are checked by G0."}
    write_frozen_json(output / "initial_state_inventory.json", inventory_payload)
    for split, rows in selected.items():
        payload = signed_payload({"schema_version": 1, "suite": "libero_spatial", "split": split,
                                  "environment_seed": environment_seed, "source": source, "states": rows}, STATE_NAMESPACE)
        validate_initial_state_manifest(payload)
        write_frozen_json(output / f"init_states_{split}.json", payload)
    g0_rows = []
    for task in sorted(development_names):
        g0_rows.extend([row for row in selected["development"] if row["task_name"] == task][:5])
    g0 = signed_payload({"schema_version": 1, "suite": "libero_spatial", "split": "development",
                         "environment_seed": environment_seed, "source": source,
                         "panel_rule": "three frozen development tasks, first five sorted development source indices each",
                         "states": g0_rows}, STATE_NAMESPACE)
    validate_initial_state_manifest(g0)
    write_frozen_json(output / "g0_development_15.json", g0)
    return inventory_payload

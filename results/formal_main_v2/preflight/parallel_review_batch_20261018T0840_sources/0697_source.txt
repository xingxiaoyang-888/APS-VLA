"""Formal initial-state preparation: development values, sealed final registry.

The constructor may load official CPU matrices solely to preallocate and seal
states. Development loaders have no path that loads final state values. Actual
final evaluation and its full-matrix release gate belong to evaluation code.
"""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
import random

from .experiment_protocol import signed_payload, verify_payload, write_frozen_json
from .formal_windows import SUITES, LIBERO_REVISION, OFFICIAL_MAPPING
from .identity import canonical_mapping_signature, file_sha256
from .initial_states import official_task_catalog, initial_state_sha256, load_official_states

STATE_NAMESPACE = "cti-vla:formal-initial-state-panel:v2"
REGISTRY_NAMESPACE = "cti-vla:formal-final-state-registry:v2"
SEED = 417
INHERIT = {"libero_spatial": "spatial_initial_states_v1", "libero_10": "long_initial_states_v1"}
IDENTITY_FIELDS = ("trial_id", "task_id", "task_name", "source_state_index", "source_file", "initial_state_sha256")


def split_state_indices(task_name, count=50):
    if count != 50:
        raise ValueError("formal preregistration requires exactly50 official states per task")
    indices = list(range(count))
    random.Random(canonical_mapping_signature({"seed": SEED, "task": task_name},
                  namespace="cti-vla:init-state-split:v1")).shuffle(indices)
    return sorted(indices[:10]), sorted(indices[10:])


def _catalog_source(root, suite):
    catalog, source = official_task_catalog(root, suite)
    if source != OFFICIAL_MAPPING:
        raise ValueError("official source task mapping changed")
    return catalog


def _validate_rows(payload, *, values, count_per_task):
    if payload.get("schema_version") != 2 or payload.get("suite") not in SUITES or payload.get("environment_seed") != 0:
        raise ValueError("invalid formal state schema/suite/environment seed")
    catalog = payload["task_catalog"]
    if [r["task_id"] for r in catalog] != list(range(10)) or len({r["task_name"] for r in catalog}) != 10:
        raise ValueError("formal states require all10 official tasks")
    rows = payload["states"]
    if len(rows) != 10 * count_per_task or Counter(r["task_id"] for r in rows) != Counter({i: count_per_task for i in range(10)}):
        raise ValueError("formal state task allocation incomplete")
    if len({r["trial_id"] for r in rows}) != len(rows) or len({(r["task_id"], r["source_state_index"]) for r in rows}) != len(rows):
        raise ValueError("formal initial state duplicate identity")
    for row in rows:
        task = catalog[row["task_id"]]
        index = row["source_state_index"]
        if type(index) is not int or not 0 <= index < 50 or row["task_name"] != task["task_name"]:
            raise ValueError("formal state task/index mismatch")
        if row["trial_id"] != f"{payload['suite']}:{task['task_name']}:state-{index:04d}:env-0" or row["source_file"] != task["task_name"] + ".pruned_init":
            raise ValueError("formal state trial/source identity mismatch")
        dev, final = split_state_indices(task["task_name"])
        if index not in (dev if payload["split"] == "development" else final):
            raise ValueError("formal state differs from fixed split")
        if values:
            if initial_state_sha256(row["initial_state"]) != row["initial_state_sha256"]:
                raise ValueError("formal state numeric hash mismatch")
        elif set(row) != set(IDENTITY_FIELDS):
            raise ValueError("final registry must contain identities only, never state values")
        source = next(s for s in payload["source"]["files"] if s["task_id"] == row["task_id"])
        if source["source_file"] != row["source_file"] or source["count"] != 50:
            raise ValueError("formal state source file mismatch")


def validate_formal_development_panel(payload):
    verify_payload(payload, STATE_NAMESPACE)
    if payload.get("split") != "development":
        raise ValueError("development API refuses sealed final states")
    _validate_rows(payload, values=True, count_per_task=10)


def load_formal_development_panel(path):
    # No neighbouring final file is opened, even for overlap validation.
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_formal_development_panel(payload)
    return payload


def validate_formal_final_registry(payload):
    verify_payload(payload, REGISTRY_NAMESPACE)
    if payload.get("split") != "final" or payload.get("state_values_included") is not False:
        raise ValueError("invalid sealed final identity registry")
    _validate_rows(payload, values=False, count_per_task=40)


def prepare_formal_initial_states(project_root, suite, *, output_directory=None):
    project = Path(project_root).resolve()
    if suite not in SUITES:
        raise ValueError("unsupported formal initial-state suite")
    output = Path(output_directory or project / "configs/manifests/formal_main_v2" / suite / "initial_states").resolve()
    if project not in output.parents:
        raise ValueError("initial-state outputs must remain inside project")
    libero = project / "external/LIBERO"
    catalog = _catalog_source(libero, suite)
    inherited_rows, inherited_inventory, inherited_files = {}, {}, {}
    if suite in INHERIT:
        old = project / "configs/manifests" / INHERIT[suite]
        # Intentionally never reference/read the old init_states_test.json.
        dev_path, inventory_path = old / "init_states_development.json", old / "initial_state_inventory.json"
        dev = json.loads(dev_path.read_text(encoding="utf-8"))
        inv = json.loads(inventory_path.read_text(encoding="utf-8"))
        if dev["suite"] != suite or dev["split"] != "development" or dev["environment_seed"] != 0:
            raise ValueError("legacy development identity invalid")
        inherited_rows = {(r["task_id"], r["source_state_index"]): r for r in dev["states"]}
        inherited_inventory = {r["task_id"]: r for r in inv["tasks"]}
        expected_ids = set(range(10)) if suite == "libero_spatial" else {0, 3, 5}
        if set(inherited_inventory) != expected_ids or Counter(r["task_id"] for r in dev["states"]) != Counter({i: 10 for i in expected_ids}):
            raise ValueError("legacy development task allocation changed")
        inherited_files = {dev_path.relative_to(project).as_posix(): file_sha256(dev_path),
                           inventory_path.relative_to(project).as_posix(): file_sha256(inventory_path)}
    inventory, development, final = [], [], []
    for task in catalog:
        source_path = libero / "libero/libero/init_files" / suite / (task["task_name"] + ".pruned_init")
        matrix = load_official_states(source_path)
        dev_indices, final_indices = split_state_indices(task["task_name"], len(matrix))
        hashes = [initial_state_sha256(state) for state in matrix]
        if len(set(hashes)) != 50:
            raise ValueError("duplicate official state contents; do not redraw")
        source = {**task, "source_file": source_path.name, "file_sha256": file_sha256(source_path),
                  "count": len(matrix), "state_dimensions": matrix.shape[1], "state_sha256": hashes}
        if task["task_id"] in inherited_inventory:
            if source != inherited_inventory[task["task_id"]]:
                raise ValueError("official state source differs from inherited inventory")
        inventory.append(source)
        for split, indices in ((development, dev_indices), (final, final_indices)):
            for index in indices:
                row = {"trial_id": f"{suite}:{task['task_name']}:state-{index:04d}:env-0", **task,
                    "source_state_index": index, "source_file": source_path.name,
                    "initial_state": matrix[index].tolist(), "initial_state_sha256": hashes[index]}
                old = inherited_rows.get((task["task_id"], index))
                if split is development and task["task_id"] in inherited_inventory:
                    if old != row:
                        raise ValueError("inherited development state values/index/trial changed")
                    row = old  # Preserve every original row field and numeric value.
                split.append(row)
    if {r["initial_state_sha256"] for r in development} & {r["initial_state_sha256"] for r in final}:
        raise ValueError("cross-task development/final content collision; do not redraw")
    source = {"repository": "Lifelong-Robot-Learning/LIBERO", "revision": LIBERO_REVISION,
        "state_file_variant": ".pruned_init", "split_seed": SEED, "split_rule": "10-development-40-final-fixed-old-task-name-hash-shuffle",
        **OFFICIAL_MAPPING, "inherited_metadata_sha256": inherited_files,
        "files": [{k: v for k, v in t.items() if k != "state_sha256"} for t in inventory]}
    common = {"schema_version": 2, "suite": suite, "environment_seed": 0, "task_catalog": catalog, "source": source}
    dev_payload = signed_payload({**common, "split": "development", "states": development}, STATE_NAMESPACE)
    registry = signed_payload({**common, "split": "final", "state_values_included": False,
        "states": [{k: row[k] for k in IDENTITY_FIELDS} for row in final]}, REGISTRY_NAMESPACE)
    sealed = signed_payload({**common, "split": "final", "release_required": "root-complete-frozen-experiment-matrix",
        "registry_signature": registry["content_signature"], "states": final}, STATE_NAMESPACE)
    validate_formal_development_panel(dev_payload)
    validate_formal_final_registry(registry)
    write_frozen_json(output / "development.json", dev_payload)
    write_frozen_json(output / "final_registry.json", registry)
    # Constructor writes the sealed asset; no final evaluation or developer loader reads it.
    write_frozen_json(output / "sealed_final.json", sealed)
    receipt = {"schema_version": 2, "status": "prepared_cpu_partition_not_final_evaluation", "suite": suite,
        "source": source, "tasks": inventory, "development_count": 100, "sealed_final_count": 400,
        "development_sha256": file_sha256(output / "development.json"),
        "final_registry_sha256": file_sha256(output / "final_registry.json"),
        "sealed_final_path": "sealed_final.json", "sealed_final_signature": sealed["content_signature"],
        "cross_split_content_hash_intersection": 0, "old_sealed_test_files_read": False,
        "final_environment_runs": 0, "inherited_development_rows": len(inherited_rows)}
    write_frozen_json(output / "inventory.json", receipt)
    return receipt

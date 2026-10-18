"""Predeclared Long task0/3/5 initial states; no task/rollout-driven selection."""
from __future__ import annotations

import ast
from collections import Counter
import json
from pathlib import Path
import random
import subprocess

from .experiment_protocol import INITIAL_STATE_SEED, signed_payload, verify_payload, write_frozen_json
from .identity import canonical_mapping_signature, file_sha256
from .initial_states import STATE_NAMESPACE, initial_state_sha256, load_official_states, official_task_catalog

LIBERO_REVISION = "8f1084e3132a39270c3a13ebe37270a43ece2a01"
OFT_REVISION = "e4287e94541f459edc4feabc4e181f537cd569a8"
LONG_SUITE = "libero_10"
LONG_TASK_IDS = (0, 3, 5)
LONG_MAX_STEPS = 520
LONG_TASK_NAMES = (
    "LIVING_ROOM_SCENE2_put_both_the_alphabet_soup_and_the_tomato_sauce_in_the_basket",
    "KITCHEN_SCENE4_put_the_black_bowl_in_the_bottom_drawer_of_the_cabinet_and_close_it",
    "STUDY_SCENE1_pick_up_the_book_and_place_it_in_the_back_compartment_of_the_caddy",
)
# Filled once after the preregistered official state build, before any rollout.
LONG_PANEL_SHA256 = "64ce305a9530dca00879fdc00a4d08552d95c1ebf3db981533873d3b0d14886e"
LONG_PANEL_SIGNATURE = "d6135205703e081bbc2bc99461670458101cd5bb4d5fd10d3f3865c5d5f8909f"


def _signature(value):
    import hashlib
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _fixed_checkout(root, revision, paths):
    root = Path(root)
    actual = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    if actual != revision:
        raise ValueError("Long initial-state construction requires the fixed official source commit")
    subprocess.run(["git", "-C", str(root), "diff", "--exit-code", revision, "--", *paths],
        check=True, capture_output=True, text=True)


def register_long_tasks(libero_root, oft_root, output_directory):
    """Write the index-only choice before opening any Long state/data file."""
    _fixed_checkout(libero_root, LIBERO_REVISION, ["libero/libero/benchmark"])
    relative = "experiments/robot/libero/run_libero_eval.py"
    _fixed_checkout(oft_root, OFT_REVISION, [relative])
    source = Path(oft_root) / relative
    tree = ast.parse(source.read_text(encoding="utf-8"))
    values = next(node.value for node in tree.body if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "TASK_MAX_STEPS" for t in node.targets))
    match = [(key.lineno, ast.literal_eval(value)) for key, value in zip(values.keys, values.values)
             if isinstance(key, ast.Attribute) and key.attr == "LIBERO_10"]
    if len(match) != 1 or match[0][1] != LONG_MAX_STEPS:
        raise ValueError("fixed official Long horizon changed; do not silently choose another")
    catalog, mapping = official_task_catalog(libero_root, suite=LONG_SUITE)
    tasks = [catalog[i] for i in LONG_TASK_IDS]
    if tuple(t["task_name"] for t in tasks) != LONG_TASK_NAMES:
        raise ValueError("predeclared Long indices differ from the fixed official task mapping")
    payload = {"schema_version": 1, "suite": LONG_SUITE, "display_name": "LIBERO-Long",
        "selection_rule": "task_order_index0 IDs0,3,5 fixed before Long state inventory, data or results; same index rule as Spatial",
        "tasks": tasks, "methods": ["dense", "future_A", "future_B"], "development_states_per_task": 10,
        "sealed_final_states_per_task": 40, "expected_development_trials": 90, "environment_seed": 0,
        "initial_state_split_seed": INITIAL_STATE_SEED, "split_namespace": "cti-vla:init-state-split:v1",
        "source": {"repository": "Lifelong-Robot-Learning/LIBERO", "revision": LIBERO_REVISION, **mapping},
        "horizon": {"max_steps": LONG_MAX_STEPS, "wait_steps": 10, "action_chunk": 8,
            "repository": "moojink/openvla-oft", "revision": OFT_REVISION, "file": relative,
            "source_line": match[0][0], "file_sha256": file_sha256(source),
            "note": "Pinned official LIBERO_10 horizon is520, not700; wait steps are separate."},
        "status": "preregistered_indices_only_before_state_inventory"}
    payload["content_signature"] = _signature(payload)
    path = Path(output_directory) / "development_tasks.json"
    write_frozen_json(path, payload)
    return payload


def validate_long_initial_state_manifest(payload):
    verify_payload(payload, STATE_NAMESPACE)
    if payload.get("schema_version") != 1 or payload.get("suite") != LONG_SUITE or payload.get("split") not in ("development", "test") or payload.get("environment_seed") != 0:
        raise ValueError("unsupported Long initial-state identity")
    source = payload["source"]
    if source.get("revision") != LIBERO_REVISION or source.get("split_seed") != INITIAL_STATE_SEED or source.get("task_order_index") != 0:
        raise ValueError("Long source/split seed differs from its preregistration")
    rows = payload["states"]
    count = 10 if payload["split"] == "development" else 40
    if Counter(row["task_id"] for row in rows) != {task: count for task in LONG_TASK_IDS} or len({r["trial_id"] for r in rows}) != len(rows):
        raise ValueError("Long manifest requires exactly the preregistered three tasks and state counts")
    if len({(r["task_id"], r["source_state_index"]) for r in rows}) != len(rows):
        raise ValueError("duplicate Long initial state")
    for row in rows:
        name = LONG_TASK_NAMES[LONG_TASK_IDS.index(row["task_id"])]
        index = row["source_state_index"]
        if row["task_name"] != name or type(index) is not int or not 0 <= index < 50:
            raise ValueError("Long task/source index differs from the official source")
        if row["trial_id"] != f"{LONG_SUITE}:{name}:state-{index:04d}:env-0" or initial_state_sha256(row["initial_state"]) != row["initial_state_sha256"]:
            raise ValueError("Long initial-state bytes/identity mismatch")


def build_long_initial_states(libero_root, oft_root, output_directory):
    root, output = Path(libero_root), Path(output_directory)
    registration = register_long_tasks(root, oft_root, output)
    inventory, matrices = [], {}
    for task in registration["tasks"]:
        relative = f"libero/libero/init_files/{LONG_SUITE}/{task['task_name']}.pruned_init"
        _fixed_checkout(root, LIBERO_REVISION, [relative])
        path = root / relative
        matrix = load_official_states(path)
        hashes = [initial_state_sha256(row) for row in matrix]
        if len(matrix) != 50 or len(set(hashes)) != 50:
            raise ValueError("Long preregistration requires exactly50 distinct official states per selected task")
        matrices[task["task_id"]] = matrix
        inventory.append({**task, "source_file": path.name, "file_sha256": file_sha256(path),
            "count": 50, "state_dimensions": int(matrix.shape[1]), "state_sha256": hashes})
    source = {**registration["source"], "state_file_variant": ".pruned_init", "split_seed": INITIAL_STATE_SEED,
        "split_rule": "official-library-fallback-10-development-40-test",
        "selection_rule": "Per-task SHA256-seeded Random using the unchanged Spatial namespace/seed417; first10 development, remaining40 sealed final; sort source indices",
        "development_tasks_sha256": file_sha256(output / "development_tasks.json"),
        "files": [{k: v for k, v in item.items() if k != "state_sha256"} for item in inventory]}
    groups = {"development": [], "test": []}
    for task in inventory:
        indices = list(range(50))
        random.Random(canonical_mapping_signature({"seed": INITIAL_STATE_SEED, "task": task["task_name"]}, namespace="cti-vla:init-state-split:v1")).shuffle(indices)
        for split, chosen in (("development", indices[:10]), ("test", indices[10:])):
            for index in sorted(chosen):
                groups[split].append({"trial_id": f"{LONG_SUITE}:{task['task_name']}:state-{index:04d}:env-0",
                    "task_id": task["task_id"], "task_name": task["task_name"], "source_state_index": index,
                    "source_file": task["source_file"], "initial_state": matrices[task["task_id"]][index].tolist(),
                    "initial_state_sha256": task["state_sha256"][index]})
    overlap = {r["initial_state_sha256"] for r in groups["development"]} & {r["initial_state_sha256"] for r in groups["test"]}
    if overlap:
        raise ValueError("Long development/final state content overlaps; never redraw")
    for split, rows in groups.items():
        payload = signed_payload({"schema_version": 1, "suite": LONG_SUITE, "split": split,
            "environment_seed": 0, "source": source, "states": rows}, STATE_NAMESPACE)
        validate_long_initial_state_manifest(payload)
        write_frozen_json(output / f"init_states_{split}.json", payload)
    panel = {"schema_version": 1, "suite": LONG_SUITE, "split": "development", "environment_seed": 0,
        "source": source, "states": groups["development"], "max_steps": LONG_MAX_STEPS, "wait_steps": 10,
        "action_chunk": 8, "methods": ["dense", "future_A", "future_B"], "test_opened": False,
        "development_manifest_sha256": file_sha256(output / "init_states_development.json"),
        "registration_sha256": file_sha256(output / "development_tasks.json"),
        "rule": "all10 preregistered development states for Long task0,3,5; same states for dense/A/B; sealed final never evaluated"}
    panel["panel_signature"] = _signature(panel)
    write_frozen_json(output / "development_panel_30.json", panel)
    report = {"suite": LONG_SUITE, "status": "numeric_inventory_only_not_simulator_acceptance",
        "tasks": inventory, "development_count": 30, "sealed_final_count": 120,
        "cross_split_content_hash_intersection": 0, "source": source,
        "panel_sha256": file_sha256(output / "development_panel_30.json"), "panel_signature": panel["panel_signature"],
        "limits": "No simulator, model inference, Long episode data or sealed-final rollout was run."}
    write_frozen_json(output / "initial_state_inventory.json", report)
    return report


def validate_long_development_panel(panel):
    if panel.get("panel_signature") != LONG_PANEL_SIGNATURE or panel["panel_signature"] != _signature({k: v for k, v in panel.items() if k != "panel_signature"}):
        raise ValueError("Long panel differs from the frozen preregistration")
    if panel.get("test_opened") is not False or panel.get("split") != "development" or panel.get("max_steps") != LONG_MAX_STEPS or panel.get("methods") != ["dense", "future_A", "future_B"]:
        raise ValueError("Long evaluation only accepts its three-method development panel")
    state_payload = signed_payload({key: panel[key] for key in ("schema_version", "suite", "split", "environment_seed", "source", "states")}, STATE_NAMESPACE)
    validate_long_initial_state_manifest(state_payload)


def load_long_development_panel(path):
    if LONG_PANEL_SHA256 is None or file_sha256(path) != LONG_PANEL_SHA256:
        raise ValueError("Long evaluation requires the frozen development panel; sealed final is prohibited")
    panel = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_long_development_panel(panel)
    return panel

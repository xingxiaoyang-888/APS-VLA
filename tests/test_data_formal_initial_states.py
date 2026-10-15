"""Formal state preparation must preserve legacy identities and seal values."""
import json
from pathlib import Path
import shutil

import numpy as np
import pytest

from cti_vla.data import formal_initial_states as states
from cti_vla.data.experiment_protocol import signed_payload

ROOT = Path(__file__).resolve().parents[1]


def synthetic_project(tmp_path, monkeypatch, suite="libero_object"):
    source = tmp_path / "external/LIBERO/libero/libero"
    (source / "benchmark").mkdir(parents=True)
    for name in ("__init__.py", "libero_suite_task_map.py"):
        shutil.copyfile(ROOT / "external/LIBERO/libero/libero/benchmark" / name, source / "benchmark" / name)
    catalog = states._catalog_source(tmp_path / "external/LIBERO", suite)
    matrices = {}
    for task in catalog:
        path = source / "init_files" / suite / (task["task_name"] + ".pruned_init")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(task["task_id"]))
        matrices[path.name] = np.arange(150, dtype=float).reshape(50, 3) + 1000 * task["task_id"]
    monkeypatch.setattr(states, "load_official_states", lambda path: matrices[path.name])
    return tmp_path


def test_state_registry_has_no_numeric_values_and_dev_loader_never_reads_final(tmp_path, monkeypatch):
    project = synthetic_project(tmp_path, monkeypatch)
    receipt = states.prepare_formal_initial_states(project, "libero_object")
    out = project / "configs/manifests/formal_main_v2/libero_object/initial_states"
    registry = json.loads((out / "final_registry.json").read_text())
    states.validate_formal_final_registry(registry)
    assert len(registry["states"]) == 400
    assert all("initial_state" not in r for r in registry["states"])
    assert receipt["cross_split_content_hash_intersection"] == 0
    (out / "sealed_final.json").write_text("not available without release")
    (out / "final_registry.json").write_text("also inaccessible to development")
    dev = states.load_formal_development_panel(out / "development.json")
    assert len(dev["states"]) == 100


def test_development_loader_refuses_validly_signed_final(tmp_path, monkeypatch):
    project = synthetic_project(tmp_path, monkeypatch)
    states.prepare_formal_initial_states(project, "libero_object")
    path = project / "configs/manifests/formal_main_v2/libero_object/initial_states/sealed_final.json"
    with pytest.raises(ValueError, match="refuses sealed"):
        states.load_formal_development_panel(path)


def test_state_allocation_requires_exact50_and_rejects_cross_split_duplicates(tmp_path, monkeypatch):
    for count in (49, 51, 60):
        with pytest.raises(ValueError, match="exactly50"):
            states.split_state_indices("task", count)
    project = synthetic_project(tmp_path, monkeypatch)
    monkeypatch.setattr(states, "load_official_states", lambda path: np.zeros((50, 3)))
    with pytest.raises(ValueError, match="duplicate official"):
        states.prepare_formal_initial_states(project, "libero_object")


def test_hash_correct_wrong_split_state_is_rejected(tmp_path, monkeypatch):
    project = synthetic_project(tmp_path, monkeypatch)
    states.prepare_formal_initial_states(project, "libero_object")
    out = project / "configs/manifests/formal_main_v2/libero_object/initial_states"
    dev = json.loads((out / "development.json").read_text())
    sealed = json.loads((out / "sealed_final.json").read_text())
    dev["states"][0] = sealed["states"][0]
    dev.pop("content_signature")
    with pytest.raises(ValueError, match="fixed split"):
        states.validate_formal_development_panel(signed_payload(dev, states.STATE_NAMESPACE))

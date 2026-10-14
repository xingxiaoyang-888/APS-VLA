"""Protocol checks use frozen real metadata and small synthetic state files."""

from collections import Counter
import copy
import argparse
import importlib.util
import json
from pathlib import Path
import pickle
import shutil

import numpy as np
import pytest
import torch

from cti_vla.data.experiment_protocol import (
    EXPOSED_EPISODE, load_experiment_protocol, prepare_observation_protocol,
    select_train_observation, signed_payload,
)
from cti_vla.data.identity import file_sha256
from cti_vla.data.initial_states import (
    STATE_NAMESPACE, initial_state_sha256, load_official_states,
    prepare_initial_state_manifests, validate_initial_state_manifest,
)
from cti_vla.data.libero import load_manifest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def protocol_tree(tmp_path):
    source = tmp_path / "source"
    shutil.copytree(ROOT / "configs/manifests/spatial_v1", source)
    evidence = tmp_path / "smoke.json"
    shutil.copyfile(ROOT / "results/smoke/openvla_2987244.json", evidence)
    output = tmp_path / "protocol"
    before = {p.name: file_sha256(p) for p in source.glob("*.json")}
    result = prepare_observation_protocol(source, output, evidence)
    assert before == {p.name: file_sha256(p) for p in source.glob("*.json")}
    return source, output, evidence, result


def test_panels_are_frozen_train_subsets_with_full_stage_coverage(protocol_tree):
    source, output, evidence, result = protocol_tree
    assert prepare_observation_protocol(source, output, evidence) == result
    diagnostic = load_manifest(output / "diagnostic_90.json")
    teacher = load_manifest(output / "teacher_12.json")
    effective = load_manifest(output / "validation_effective.json")
    assert (diagnostic.episode_count, diagnostic.sample_count) == (30, 90)
    assert set(Counter(e.task_name for e in diagnostic.episodes).values()) == {3}
    assert Counter(s.stage for s in diagnostic.samples) == {"early": 30, "middle": 30, "late": 30}
    assert (teacher.episode_count, teacher.sample_count) == (4, 12)
    assert set(teacher.episode_ids) <= set(diagnostic.episode_ids)
    assert len({e.task_name for e in teacher.episodes}) == 4
    assert (effective.episode_count, effective.sample_count) == (63, 189)
    assert EXPOSED_EPISODE not in effective.episode_ids
    assert len({e.task_name for e in effective.episodes}) == 10


def test_guard_rejects_validation_test_exposure_and_nonmanifest_frames(protocol_tree):
    _, output, _, _ = protocol_tree
    protocol = load_experiment_protocol(output / "protocol.json")
    for split in ("validation", "test"):
        sample = next(s for s in protocol.manifests[split].samples if s.episode_id != EXPOSED_EPISODE)
        with pytest.raises(ValueError, match="authoritative episode split"):
            protocol.require_sample(sample.episode_id, sample.step_index, split="train")
    with pytest.raises(ValueError, match="engineering-only"):
        protocol.require_sample(EXPOSED_EPISODE, 0, split="validation")
    sample = protocol.manifests["train"].samples[0]
    episode, returned = protocol.require_sample(sample.episode_id, sample.step_index, split="train")
    assert returned == sample
    with pytest.raises(ValueError, match="frozen source manifest"):
        protocol.require_sample(episode.episode_id, 1, split="train")


def test_smoke_defaults_to_real_train_and_explicit_old_record_is_rejected(protocol_tree):
    _, output, _, _ = protocol_tree
    protocol = load_experiment_protocol(output / "protocol.json")
    shard = "libero_spatial-train.tfrecord-00000-of-00016"
    episode, sample = select_train_observation(protocol, shard)
    assert episode.record_index != 0
    protocol.require_sample(episode.episode_id, sample.step_index, split="train")
    with pytest.raises(ValueError, match="engineering-only"):
        select_train_observation(protocol, shard, record_index=0, step_index=0)
    with pytest.raises(ValueError, match="both"):
        select_train_observation(protocol, shard, record_index=episode.record_index)


def test_source_manifest_tampering_is_detected_before_membership(protocol_tree):
    source, output, _, _ = protocol_tree
    path = source / "train.json"
    data = json.loads(path.read_text())
    data["split"] = "validation"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        load_experiment_protocol(output / "protocol.json")


def test_smoke_rejects_exposed_observation_before_cuda_or_model_setup(protocol_tree):
    _, output, _, _ = protocol_tree
    spec = importlib.util.spec_from_file_location("cti_test_smoke", ROOT / "scripts/smoke_openvla.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # No GPU/cache/checkpoint fields are provided: rejection must happen before
    # accessing any of them, based on pinned dataset membership alone.
    args = argparse.Namespace(experiment_protocol=output / "protocol.json",
                              shard=Path("libero_spatial-train.tfrecord-00000-of-00016"),
                              record_index=0, step_index=0)
    with pytest.raises(ValueError, match="engineering-only"):
        module.run(args)


def test_numeric_initial_states_loader_and_canonical_hash(tmp_path):
    values = np.arange(30, dtype=np.float64).reshape(5, 6)
    path = tmp_path / "states.pruned_init"
    torch.save([row for row in values], path)
    np.testing.assert_array_equal(load_official_states(path), values)
    assert initial_state_sha256(values[0]) == initial_state_sha256(values[0].tolist())
    assert initial_state_sha256(values[0]) == initial_state_sha256(values[0].astype(">f8"))
    assert initial_state_sha256(values[0]) != initial_state_sha256(values[1])
    for bad in ([], [[1, 2]], [float("nan")], ["1.0"], [True]):
        with pytest.raises(ValueError):
            initial_state_sha256(bad)
    with pytest.raises(ValueError, match="unpruned"):
        load_official_states(tmp_path / "states.init")


class UnsupportedConstructor:
    def __reduce__(self):
        return sorted, ([2, 1],)


def test_state_loader_rejects_unsupported_pickle_globals(tmp_path):
    path = tmp_path / "unsupported.pruned_init"
    torch.save(UnsupportedConstructor(), path)
    with pytest.raises(pickle.UnpicklingError, match="unsupported constructor"):
        load_official_states(path)


def fake_library(tmp_path, *, count=50):
    root = tmp_path / "libero"
    benchmark = root / "libero/libero/benchmark"
    benchmark.mkdir(parents=True)
    names = [f"task_{i}" for i in range(10)]
    (benchmark / "libero_suite_task_map.py").write_text("libero_task_map = " + repr({"libero_spatial": names}))
    (benchmark / "__init__.py").write_text("task_orders = " + repr([list(range(10))]))
    states = root / "libero/libero/init_files/libero_spatial"
    states.mkdir(parents=True)
    for i, name in enumerate(names):
        torch.save(np.arange(count * 3, dtype=float).reshape(count, 3) + i * 100000, states / f"{name}.pruned_init")
    tasks = tmp_path / "tasks.json"
    tasks.write_text(json.dumps({"tasks": [{"task_name": name} for name in names[:3]]}))
    return root, tasks


@pytest.mark.parametrize("count,final_count", [(50, 40), (65, 50)])
def test_state_split_counts_hash_isolation_and_g0_subset(tmp_path, count, final_count):
    root, tasks = fake_library(tmp_path, count=count)
    output = tmp_path / "states_protocol"
    kwargs = dict(source_revision="a" * 40, development_tasks_path=tasks)
    result = prepare_initial_state_manifests(root, output, **kwargs)
    assert prepare_initial_state_manifests(root, output, **kwargs) == result
    manifests = {name: json.loads((output / filename).read_text()) for name, filename in (
        ("development", "init_states_development.json"), ("test", "init_states_test.json"), ("g0", "g0_development_15.json"))}
    for payload in manifests.values():
        validate_initial_state_manifest(payload)
    assert len(manifests["development"]["states"]) == 100
    assert len(manifests["test"]["states"]) == 10 * final_count
    assert len(manifests["g0"]["states"]) == 15
    ids = {name: {row["initial_state_sha256"] for row in payload["states"]} for name, payload in manifests.items()}
    assert ids["development"].isdisjoint(ids["test"])
    assert ids["g0"] <= ids["development"]
    forged = copy.deepcopy(manifests["g0"])
    forged.pop("content_signature")
    forged["states"][0]["initial_state"][0] += 1
    forged = signed_payload(forged, STATE_NAMESPACE)
    with pytest.raises(ValueError, match="state content hash"):
        validate_initial_state_manifest(forged)


def test_insufficient_official_states_never_generate_or_guess(tmp_path):
    root, tasks = fake_library(tmp_path, count=55)
    output = tmp_path / "states_protocol"
    with pytest.raises(ValueError, match="preregistered"):
        prepare_initial_state_manifests(root, output, source_revision="a" * 40, development_tasks_path=tasks)
    assert (output / "initial_state_inventory.json").is_file()
    assert not (output / "init_states_test.json").exists()

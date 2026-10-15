"""Actual protobuf/framing tests for full-pool windows and sealed-test isolation."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import struct

import numpy as np
import pytest

from cti_vla.data import formal_windows as fw
from cti_vla.data.experiment_protocol import signed_payload, write_frozen_json
from cti_vla.data.sequence_example import _example_class, decode_libero_example
from cti_vla.data.tfrecord import _masked_crc32c

ROOT = Path(__file__).resolve().parents[1]


def example(task, number, n=15):
    proto = _example_class()()
    f = proto.features.feature
    for name, width in (("action", 7), ("observation/state", 8), ("observation/joint_state", 7)):
        f["steps/" + name].float_list.value.extend(np.arange(n * width, dtype=np.float32) + number)
    for name in ("reward", "discount"):
        f["steps/" + name].float_list.value.extend([1.] * n)
    f["steps/is_first"].int64_list.value.extend([1] + [0] * (n - 1))
    for name in ("is_last", "is_terminal"):
        f["steps/" + name].int64_list.value.extend([0] * (n - 1) + [1])
    f["steps/language_instruction"].bytes_list.value.extend([task["instruction"].encode()] * n)
    for name in ("image", "wrist_image"):
        f["steps/observation/" + name].bytes_list.value.extend([b"\xff\xd8synthetic-jpeg\xff\xd9"] * n)
    f["episode_metadata/file_path"].bytes_list.value.append(("/raw/" + task["task_name"] + "_demo.hdf5").encode())
    return proto.SerializeToString()


@pytest.fixture
def project(tmp_path):
    benchmark = tmp_path / "external/LIBERO/libero/libero/benchmark"
    benchmark.mkdir(parents=True)
    for name in ("__init__.py", "libero_suite_task_map.py"):
        shutil.copyfile(ROOT / "external/LIBERO/libero/libero/benchmark" / name, benchmark / name)
    return tmp_path


def create_data(project, suite="libero_object", duplicate=False):
    data = project / "data" / fw.SUITES[suite] / "1.0.0"
    data.mkdir(parents=True)
    catalog = fw.catalog_for_suite(project, suite)
    payloads = [example(task, i, 9 + i % 8) for task in catalog for i in range(10)]
    if duplicate:
        payloads.append(payloads[0])
    shard = suite + "-train.tfrecord-00000-of-00001"
    with (data / shard).open("wb") as stream:
        for payload in payloads:
            length = struct.pack("<Q", len(payload))
            stream.write(length + struct.pack("<I", _masked_crc32c(length)) + payload + struct.pack("<I", _masked_crc32c(payload)))
    info = {"name": suite, "version": "1.0.0", "splits": [{"name": "train", "shardLengths": [len(payloads)]}]}
    (data / "dataset_info.json").write_text(json.dumps(info), encoding="utf-8")
    (data / "features.json").write_text("{}", encoding="utf-8")
    files = [{"path": fw.SUITES[suite] + "/1.0.0/" + p.name, "size": p.stat().st_size,
              "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(data.iterdir())]
    asset = {"repository": "openvla/modified_libero_rlds", "revision": fw.DATASET_REVISION,
             "dataset_path": fw.SUITES[suite] + "/1.0.0", "episode_count": len(payloads),
             "total_bytes": sum(s["size"] for s in files), "files": files}
    asset_path = project / "configs/assets/synthetic.json"
    write_frozen_json(asset_path, asset)
    return data, asset_path, payloads, shard


def freeze(project, **kwargs):
    data, asset, payloads, shard = create_data(project, **kwargs)
    payload = fw.build_formal_protocol(data, asset, project_root=project, suite="libero_object")
    path = project / "configs/manifests/formal_main_v2/libero_object/protocol.json"
    write_frozen_json(path, payload)
    protocol = fw.load_formal_protocol(path)
    return protocol, data, asset, payloads, shard


def test_true_protobuf_full_pool_and_validation_dedup_without_pixels(project, monkeypatch):
    from PIL import Image
    monkeypatch.setattr(Image, "open", lambda *a, **k: pytest.fail("metadata inventory decoded pixels"))
    protocol, _, _, _, _ = freeze(project)
    manifest = fw.build_formal_windows(protocol)
    counts = {s: len(m.episodes) for s, m in protocol.manifests.items()}
    assert counts == {"train": 70, "validation": 10, "test": 20}
    train = [r for r in manifest["windows"] if r["split"] == "train"]
    assert len(train) == sum(e.num_steps - 8 for e in protocol.manifests["train"].episodes)
    for ref in protocol.manifests["train"].episodes:
        assert [r["start_step"] for r in train if r["episode_id"] == ref.episode_id] == list(range(ref.num_steps - 8))
    test_ids = set(protocol.manifests["test"].episode_ids)
    assert not test_ids & {r["episode_id"] for r in manifest["windows"]}
    assert len(manifest["validation_window_ids"]) == sum(len(fw.validation_starts(e.num_steps)) for e in protocol.manifests["validation"].episodes)
    path = protocol.path.with_name("windows.json")
    write_frozen_json(path, manifest)
    assert fw.load_formal_windows(path, protocol) == manifest


@pytest.mark.parametrize("n,expected", [(3, {}), (8, {}), (9, {0: ["first", "middle", "last"]}),
    (10, {0: ["first", "middle"], 1: ["last"]}), (11, {0: ["first"], 1: ["middle"], 2: ["last"]})])
def test_short_valid_windows_are_retained_without_fabricating_three(n, expected):
    assert fw.validation_starts(n) == expected
    assert list(fw.legal_starts(n)) == list(range(max(n - 8, 0)))


def test_duplicate_record_has_one_episode_and_one_split(project):
    protocol, _, _, _, _ = freeze(project, duplicate=True)
    assert protocol.payload["raw_episode_count"] == 101
    assert protocol.payload["unique_episode_count"] == 100
    assert len(protocol.payload["duplicate_aliases"]) == 1
    groups = list(protocol.payload["duplicate_aliases"].values())
    assert groups[0][0]["record_index"] == 0 and groups[0][1]["record_index"] == 100
    assert sum(len(m.episodes) for m in protocol.manifests.values()) == 100


def test_stable_split_does_not_depend_on_locator_or_input_order(project):
    catalog = fw.catalog_for_suite(project, "libero_object")
    items = [fw.probe_formal_episode(example(task, i), "a", task["task_id"] * 10 + i, catalog)
             for task in catalog for i in range(10)]
    refs, _, _ = fw.deduplicate_inventory(items)
    moved = [replace(ref, source_shard="new", record_index=999 - i) for i, ref in enumerate(reversed(refs))]
    first = fw.split_episodes(refs, seed=fw.NEW_SPLIT_SEED)
    second = fw.split_episodes(moved, seed=fw.NEW_SPLIT_SEED)
    assert {s: {e.episode_id for e in rows} for s, rows in first.items()} == {s: {e.episode_id for e in rows} for s, rows in second.items()}


def test_runtime_observation_action_future_alignment_and_split_guard(project):
    protocol, _, _, payloads, shard = freeze(project)
    row = next(r for r in fw.iter_formal_window_rows(protocol) if r["split"] == "train" and r["start_step"] > 0)
    episode = replace(decode_libero_example(payloads[row["record_index"]]), source_shard=shard, record_index=row["record_index"])
    fw.validate_formal_window(row, episode, protocol)
    t = row["start_step"]
    assert row["future_step"] == t + 8 and row["action_stop_exclusive"] == t + 8
    assert np.array_equal(episode.actions[t:t + 8][-1], episode.actions[row["future_step"] - 1])
    for key, value in (("split", "validation"), ("future_step", t + 7), ("task_id", 999), ("record_index", 999)):
        with pytest.raises(ValueError):
            fw.validate_formal_window({**row, key: value}, episode, protocol)
    flags = episode.is_terminal.copy()
    flags[t] = True
    with pytest.raises(ValueError, match="boundary"):
        fw.validate_formal_window(row, replace(episode, is_terminal=flags), protocol)
    test_ref = protocol.manifests["test"].episodes[0]
    with pytest.raises(ValueError, match="test is sealed"):
        fw.validate_formal_window({**row, "episode_id": test_ref.episode_id}, episode, protocol)
    quarantine = replace(protocol, excluded_episode_ids=frozenset({row["episode_id"]}))
    with pytest.raises(ValueError, match="quarantine"):
        fw.validate_formal_window(row, episode, quarantine)


def test_signed_manifest_cannot_reduce_pool_to_subset(project):
    protocol, _, _, _, _ = freeze(project)
    manifest = fw.build_formal_windows(protocol)
    manifest.pop("content_signature")
    manifest["windows"].pop()
    path = protocol.path.with_name("truncated.json")
    write_frozen_json(path, signed_payload(manifest, fw.WINDOW_NAMESPACE))
    with pytest.raises(ValueError, match="complete registered pool"):
        fw.load_formal_windows(path, protocol)


def test_source_byte_tamper_rejected_before_record_inventory(project):
    data, asset, _, shard = create_data(project)
    with (data / shard).open("ab") as stream:
        stream.write(b"tamper")
    with pytest.raises(ValueError, match="bytes/SHA"):
        fw.build_formal_protocol(data, asset, project_root=project, suite="libero_object")


@pytest.mark.parametrize("field", ["steps/is_terminal", "steps/is_first", "steps/is_last"])
def test_metadata_rejects_mid_episode_terminal_restart_or_end(project, field):
    catalog = fw.catalog_for_suite(project, "libero_object")
    proto = _example_class()()
    proto.ParseFromString(example(catalog[0], 0))
    proto.features.feature[field].int64_list.value[4] = 1
    with pytest.raises(ValueError, match="boundary"):
        fw.probe_formal_episode(proto.SerializeToString(), "s", 0, catalog)


def test_native_action_normalization_is_same_pure_operator():
    from cti_vla.data.future_windows import normalize_demo_actions
    assert fw.normalize_demo_actions is normalize_demo_actions


def test_registered_capacity_disk_is_allowed_but_other_project_and_weights_are_not():
    primary, capacity = fw.SERVER_PROJECT_ROOTS
    for project in (primary, capacity):
        assert fw.data_location_allowed(project, capacity + "/data/modified_libero_rlds/libero_object_no_noops/1.0.0")
        assert fw.data_location_allowed(project, primary + "/data/modified_libero_rlds/libero_10_no_noops/1.0.0")
        assert not fw.data_location_allowed(project, capacity + "/models/weights")
        assert not fw.data_location_allowed(project, capacity.replace("CTI-VLA", "DIWA") + "/data/dataset")
        assert not fw.data_location_allowed(project, capacity + "/data/../../DIWA/data")
    assert not fw.data_location_allowed("F:/CTI-VLA", capacity + "/data/dataset")

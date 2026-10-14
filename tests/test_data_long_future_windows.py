"""Long-only CPU tests: actual protobuf timing/isolation and source replay guards."""
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image
import pytest

from cti_vla.data import long_future_windows as long
from cti_vla.data import future_windows as spatial
from cti_vla.data.experiment_protocol import signed_payload, verify_payload, write_frozen_json
from cti_vla.data.identity import file_sha256
from cti_vla.data.initial_states import official_task_catalog
from cti_vla.data.sequence_example import _example_class, decode_libero_example

ROOT = Path(__file__).resolve().parents[1]


def jpeg(value):
    stream = io.BytesIO()
    Image.fromarray(np.full((256, 256, 3), value, np.uint8), mode="RGB").save(stream, format="JPEG")
    return stream.getvalue()


BLACK, WHITE = jpeg(0), jpeg(255)


def example(task_index, episode_index, n=15):
    task = long.official_long_catalog()[task_index]
    proto = _example_class()()
    f = proto.features.feature
    for name, width in (("steps/action", 7), ("steps/observation/state", 8), ("steps/observation/joint_state", 7)):
        values = np.zeros((n, width), np.float32)
        values[:, 0] = np.arange(n) * .01 + episode_index * .1
        f[name].float_list.value.extend(values.ravel())
    for name in ("steps/reward", "steps/discount"):
        f[name].float_list.value.extend([1.] * n)
    f["steps/is_first"].int64_list.value.extend([1] + [0] * (n - 1))
    for name in ("steps/is_last", "steps/is_terminal"):
        f[name].int64_list.value.extend([0] * (n - 1) + [1])
    f["steps/language_instruction"].bytes_list.value.extend([task["instruction"].encode()] * n)
    for name in ("steps/observation/image", "steps/observation/wrist_image"):
        f[name].bytes_list.value.extend([BLACK] * (n - 1) + [WHITE])
    f["episode_metadata/file_path"].bytes_list.value.append(("/foreign/data/" + task["task_name"] + "_demo.hdf5").encode())
    return proto.SerializeToString()


def test_metadata_probe_has_same_stable_identity_without_array_or_rgb_decode(monkeypatch):
    payload = example(0, 4)
    decoded = decode_libero_example(payload)
    def fail(*a, **k):
        raise AssertionError("inventory called full episode/RGB decoder")
    monkeypatch.setattr(long, "decode_libero_example", fail)
    monkeypatch.setattr(Image, "open", fail)
    ref = long.probe_episode_metadata(payload, long.SHARD_NAMES[0], 2)
    assert (ref.episode_id, ref.num_steps, ref.task_name) == (decoded.episode_id, decoded.num_steps, decoded.instructions[0])
    proto = _example_class()()
    proto.ParseFromString(payload)
    proto.features.feature["episode_metadata/file_path"].bytes_list.value[0] = ("/moved/" + long.OFFICIAL_TASK_NAMES[0] + "_demo.hdf5").encode()
    moved = long.probe_episode_metadata(proto.SerializeToString(), long.SHARD_NAMES[1], 9)
    assert moved.episode_id == ref.episode_id


@pytest.mark.parametrize("fault", ["boundary", "length", "task", "instruction", "kind"])
def test_inventory_rejects_invalid_episode_structure(fault):
    proto = _example_class()()
    proto.ParseFromString(example(0, 1))
    f = proto.features.feature
    if fault == "boundary":
        f["steps/is_terminal"].int64_list.value[3] = 1
    elif fault == "length":
        del f["steps/action"].float_list.value[-1]
    elif fault == "task":
        f["episode_metadata/file_path"].bytes_list.value[0] = b"/data/other_demo.hdf5"
    elif fault == "instruction":
        f["steps/language_instruction"].bytes_list.value[2] = b"another task"
    else:
        f["steps/action"].int64_list.value.extend([0] * 105)
    with pytest.raises(ValueError):
        long.probe_episode_metadata(proto.SerializeToString(), long.SHARD_NAMES[0], 0)


@pytest.fixture(scope="module")
def synthetic_assets(tmp_path_factory):
    """Files are synthetic markers; TFRecord envelopes are tested elsewhere.

    Source byte hashes,379 independent real protobuf records, official catalog,
    deterministic split/selection and all selected RGB decoding run for real.
    """
    project = tmp_path_factory.mktemp("long_data")
    directory = project / "data/modified_libero_rlds/libero_10_no_noops/1.0.0"
    directory.mkdir(parents=True)
    info = ROOT / "results/g1_future_long/assets/dataset_info.json"
    shutil.copyfile(info, directory / "dataset_info.json")
    asset = json.loads((ROOT / "configs/assets/libero_long_rlds.json").read_text(encoding="utf-8"))
    records = {}
    serial = 0
    for name, count in long.SHARD_EPISODE_COUNTS.items():
        records[name] = []
        for i in range(count):
            records[name].append(example(serial % 10, serial))
            serial += 1
        path = directory / name
        path.write_bytes(("synthetic TFRecord fixture " + name).encode())
        spec = next(f for f in asset["files"] if f["path"].endswith("/" + name))
        spec["size"], spec["sha256"] = path.stat().st_size, file_sha256(path)
    asset["total_bytes"] = sum(f["size"] for f in asset["files"])
    asset_path = project / "configs/assets/libero_long_rlds.json"
    registration = project / "configs/experiments/g1_future_long_data_v1.json"
    write_frozen_json(asset_path, asset)
    write_frozen_json(registration, long.registration_payload())
    return project, directory, asset_path, registration, records


@pytest.fixture
def protocol(monkeypatch, synthetic_assets):
    project, directory, asset, registration, records = synthetic_assets
    monkeypatch.setattr(long, "iter_tfrecord_records", lambda path: enumerate(records[Path(path).name]))
    payload = long.build_long_future_protocol(directory, asset, registration)
    path = project / "configs/manifests/long_future_v1/protocol.json"
    write_frozen_json(path, payload)
    return long.load_long_future_protocol(path)


def test_protocol_task_mapping_matches_pinned_official_source():
    catalog, provenance = official_task_catalog(ROOT / "external/LIBERO", suite="libero_10")
    assert catalog == [{k: row[k] for k in ("task_id", "task_name")} for row in long.official_long_catalog()]
    assert provenance == long.OFFICIAL_MAPPING
    assert long.registration_payload() == json.loads((ROOT / "configs/experiments/g1_future_long_data_v1.json").read_text(encoding="utf-8"))


def test_complete_metadata_inventory_disjoint_stable_and_fixed_panels(protocol):
    assert sum(len(m.episodes) for m in protocol.manifests.values()) == 379
    ids = [set(m.episode_ids) for m in protocol.manifests.values()]
    assert not any(a & b for i, a in enumerate(ids) for b in ids[i + 1:])
    panel = long.planned_future_episodes(protocol)
    assert {s: len(refs) for s, refs in panel.items()} == {"train": 30, "validation": 20}
    assert all(sum(e.task_name == task["instruction"] for e in panel[s]) == count
               for s, count in (("train", 3), ("validation", 2)) for task in long.official_long_catalog())
    reordered = replace(protocol, manifests={s: replace(m, episodes=tuple(reversed(m.episodes))) for s, m in protocol.manifests.items()})
    assert long.planned_future_episodes(reordered) == panel


def test_cannot_self_claim_test_validation_or_unselected_episode_as_training(protocol):
    for split in ("test", "validation"):
        with pytest.raises(ValueError, match="authoritative episode split"):
            long.require_future_episode(protocol, protocol.manifests[split].episodes[0].episode_id, "train")
    with pytest.raises(ValueError, match="test is sealed"):
        long.require_future_episode(protocol, protocol.manifests["test"].episodes[0].episode_id, "test")
    selected = long.planned_future_episodes(protocol)["train"]
    unselected = next(e for e in protocol.manifests["train"].episodes if e not in selected)
    with pytest.raises(ValueError, match="not in frozen future panel"):
        long._validate_registered_row(long._row(unselected, "train", "early", 0, False), protocol)
    quarantined = replace(protocol, excluded_episode_ids=frozenset({selected[0].episode_id}))
    with pytest.raises(ValueError, match="quarantined"):
        long.require_future_episode(quarantined, selected[0].episode_id, "train")


def resign(payload, namespace):
    return signed_payload({k: v for k, v in payload.items() if k != "content_signature"}, namespace)


@pytest.mark.parametrize("fault", ["split", "source", "selection_seed", "catalog", "test_opened", "locator"])
def test_protocol_recomputed_signature_cannot_override_frozen_authority(protocol, tmp_path, fault):
    payload = json.loads(protocol.path.read_text(encoding="utf-8"))
    if fault == "split":
        payload["episodes_by_split"]["train"][0], payload["episodes_by_split"]["test"][0] = payload["episodes_by_split"]["test"][0], payload["episodes_by_split"]["train"][0]
    elif fault == "source":
        payload["source_files"][long.SHARD_NAMES[0]]["sha256"] = "0" * 64
    elif fault == "selection_seed":
        payload["train_selection_seed"] = 118
    elif fault == "catalog":
        payload["task_catalog"][0]["task_id"] = 5
    elif fault == "test_opened":
        payload["test_pixels_opened"] = True
    else:
        payload["episodes_by_split"]["train"][0]["record_index"] = 100
    path = tmp_path / "protocol.json"
    write_frozen_json(path, resign(payload, long.PROTOCOL_NAMESPACE))
    with pytest.raises(ValueError):
        long.load_long_future_protocol(path, protocol.asset_path, protocol.registration_path)


def test_selected_short_episode_is_not_replaced_or_silently_dropped(protocol):
    victim = long.planned_future_episodes(protocol)["train"][0]
    manifests = {s: replace(m, episodes=tuple(replace(e, num_steps=10) if e == victim else e for e in m.episodes)) for s, m in protocol.manifests.items()}
    with pytest.raises(ValueError, match="no replacement/resampling"):
        long.planned_future_episodes(replace(protocol, manifests=manifests))


@pytest.fixture
def windows(protocol, synthetic_assets, monkeypatch):
    project, directory, _, _, records = synthetic_assets
    selected = {e.episode_id for refs in long.planned_future_episodes(protocol).values() for e in refs}
    seen = []
    def guarded_decode(payload):
        episode = decode_libero_example(payload)
        assert episode.episode_id in selected, "test/unselected data decoded"
        seen.append(episode.episode_id)
        return episode
    monkeypatch.setattr(long, "decode_libero_example", guarded_decode)
    manifest, changes = long.build_future_windows(protocol, directory)
    assert set(seen) == selected and len(seen) == 50
    path = project / "configs/manifests/long_future_v1/windows.json"
    write_frozen_json(path, manifest)
    return protocol, long.load_future_windows(path, protocol), changes


def test_real_selected_decode_has_exact150_h8_windows_without_test(windows, synthetic_assets):
    protocol, manifest, changes = windows
    assert manifest["summary"]["train"]["windows"] == 90
    assert manifest["summary"]["validation"]["windows"] == 60
    assert len(changes["rows"]) == 150 and changes["summary"]["all"]["episodes"] == 50
    verify_payload(changes, "cti-vla:long-future-endpoint-diagnostics:v1")
    records = synthetic_assets[-1]
    for row in manifest["windows"]:
        assert row["future_step"] - row["start_step"] == row["action_stop_exclusive"] - row["action_start"] == 8
        assert row["future_step"] <= row["num_steps"] - 1
        if row["phase"] == "late":
            assert row["future_step"] == row["num_steps"] - 1 and row["future_is_terminal"]
    row = manifest["windows"][0]
    episode = replace(decode_libero_example(records[row["source_shard"]][row["record_index"]]), source_shard=row["source_shard"], record_index=row["record_index"])
    long.validate_future_window(row, episode, protocol)
    assert row["window_id"] != spatial._window_id(row["episode_id"], row["start_step"], 8)
    for update in ({"future_step": row["future_step"] + 1}, {"action_start": 1}, {"split": "test"}):
        with pytest.raises(ValueError):
            long.validate_future_window({**row, **update}, episode, protocol)
    bad_flags = episode.is_terminal.copy()
    bad_flags[4] = True
    with pytest.raises(ValueError, match="boundary violation"):
        long.validate_future_window(row, replace(episode, is_terminal=bad_flags), protocol)
    with pytest.raises(ValueError, match="content ID"):
        long.validate_future_window(row, replace(episode, episode_id="false"), protocol)


@pytest.mark.parametrize("fault", ["missing", "duplicate", "source", "seed", "shift", "selection"])
def test_windows_cannot_be_resigned_to_change_panel_or_alignment(windows, tmp_path, fault):
    protocol, payload, _ = windows
    payload = json.loads(json.dumps(payload))
    if fault == "missing":
        payload["windows"].pop()
    elif fault == "duplicate":
        payload["windows"][0] = payload["windows"][1]
    elif fault == "source":
        payload["source_files"][next(iter(payload["source_files"]))]["sha256"] = "0" * 64
    elif fault == "seed":
        payload["validation_seed"] = 518
    elif fault == "shift":
        payload["windows"][0]["action_stop_exclusive"] += 1
    else:
        payload["selected_episodes"]["train"][0] = protocol.manifests["test"].episodes[0].episode_id
    path = tmp_path / "bad.json"
    write_frozen_json(path, resign(payload, long.WINDOW_NAMESPACE))
    with pytest.raises(ValueError):
        long.load_future_windows(path, protocol)


def test_endpoint_metrics_distinguish_wraparound_and_motion_return():
    assert long.rotation_distance([0, 0, np.pi - .01], [0, 0, -np.pi + .01]) == pytest.approx(.02, abs=1e-10)
    assert long.rotation_distance([0, 0, 0], [0, 0, np.pi]) == pytest.approx(np.pi)
    episode = decode_libero_example(example(0, 1))
    state = np.zeros((15, 8), dtype=np.float32)
    state[:9, 0] = [0, .1, .2, .3, .4, .3, .2, .1, 0]
    state[8, 6:] = [.02, -.02]
    episode = replace(episode, proprio=state, images=(BLACK,) * 8 + (WHITE,) + (BLACK,) * 6)
    row = {"window_id": "test", "episode_id": episode.episode_id, "split": "train", "task_name": "test", "phase": "early", "start_step": 0, "future_step": 8}
    metrics = long.endpoint_change_diagnostics(row, episode)["metrics"]
    assert metrics["position_endpoint_l2_m"] == 0
    assert metrics["position_path_length_m"] == pytest.approx(.8)
    assert metrics["gripper_endpoint_qpos_l2"] == pytest.approx(np.sqrt(2) * .02)
    assert metrics["front_rgb_mae_0_1"] == metrics["front_rgb_rmse_0_1"] == metrics["front_pixel_fraction_abs_gt8"] == 1.
    assert metrics["wrist_rgb_mae_0_1"] == 0.


def test_long_action_target_is_identical_pure_native_operator():
    assert long.normalize_demo_actions is spatial.normalize_demo_actions

"""CPU contracts for G1-F timing, native action targets and split isolation."""

import ast
from dataclasses import replace
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import numpy as np
import pytest

from cti_vla.data.experiment_protocol import load_experiment_protocol, write_frozen_json
from cti_vla.data import future_windows as fw
from cti_vla.data.identity import file_sha256
from cti_vla.data.sequence_example import LiberoEpisode

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def protocol():
    return load_experiment_protocol(ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")


def fake_episode(ref):
    n = ref.num_steps
    first, last = np.zeros(n, dtype=bool), np.zeros(n, dtype=bool)
    first[0], last[-1] = True, True
    return LiberoEpisode(ref.episode_id, ref.episode_file_path, np.arange(n * 7, dtype=np.float32).reshape(n, 7),
                         np.arange(n * 8, dtype=np.float32).reshape(n, 8), np.zeros((n, 7), dtype=np.float32),
                         (b"\xff\xd8front\xff\xd9",) * n, (b"\xff\xd8wrist\xff\xd9",) * n,
                         (ref.task_name,) * n, np.zeros(n, dtype=np.float32), np.ones(n, dtype=np.float32),
                         first, last, last.copy(), ref.source_shard, ref.record_index)


def test_h8_window_endpoints_are_not_native_action_only_tail():
    assert fw.legal_future_starts(20) == (0, 5, 11)
    assert fw.legal_future_starts(11) == (0, 1, 2)
    assert fw.legal_future_starts(10) == ()
    assert fw.legal_future_starts(8) == ()
    with pytest.raises(ValueError, match="horizon8"):
        fw.legal_future_starts(20, 7)


def test_episode_guard_does_not_reuse_old_three_step_whitelist(protocol):
    ref = fw.planned_future_episodes(protocol)["train"][0]
    episode = fake_episode(ref)
    start = fw.legal_future_starts(ref.num_steps)[1]
    row = fw._row(ref, "train", "middle", start, False)
    fw.validate_future_window(row, episode, protocol)
    with pytest.raises(ValueError, match="frozen source manifest"):
        protocol.require_sample(ref.episode_id, start, split="train")
    assert row["future_step"] == start + 8
    assert row["action_stop_exclusive"] == row["future_step"]
    assert episode.actions[row["action_start"]:row["action_stop_exclusive"]].shape == (8, 7)
    assert np.array_equal(episode.actions[start:start + 8][-1], episode.actions[row["future_step"] - 1])


def test_runtime_alignment_rejects_shift_boundary_and_false_identity(protocol):
    ref = fw.planned_future_episodes(protocol)["train"][0]
    episode = fake_episode(ref)
    start = fw.legal_future_starts(ref.num_steps)[-1]
    row = fw._row(ref, "train", "late", start, True)
    fw.validate_future_window(row, episode, protocol)
    assert row["future_step"] == ref.num_steps - 1  # Last stored PRE-action frame.
    for key, value in (("future_step", ref.num_steps), ("action_start", start + 1), ("action_stop_exclusive", ref.num_steps), ("horizon", 7)):
        with pytest.raises(ValueError, match="interval/identity"):
            fw.validate_future_window({**row, key: value}, episode, protocol)
    for changed in (replace(episode, episode_id="different"), replace(episode, record_index=ref.record_index + 1),
                    replace(episode, source_shard="other"), replace(episode, actions=episode.actions[:-1])):
        with pytest.raises(ValueError, match="content ID/length/storage"):
            fw.validate_future_window(row, changed, protocol)
    invalid_flags = episode.is_terminal.copy()
    invalid_flags[start + 2] = True
    with pytest.raises(ValueError, match="boundaries"):
        fw.validate_future_window(row, replace(episode, is_terminal=invalid_flags), protocol)
    with pytest.raises(ValueError, match="instruction changed"):
        fw.validate_future_window(row, replace(episode, instructions=("wrong",) * ref.num_steps), protocol)
    with pytest.raises(ValueError, match="registered future flags"):
        fw.validate_future_window({**row, "future_is_terminal": False}, episode, protocol)


def test_split_and_quarantine_cannot_be_claimed_as_train(protocol):
    for name in ("validation", "test"):
        with pytest.raises(ValueError, match="authoritative episode split|quarantined"):
            fw.require_future_episode(protocol, protocol.manifests[name].episodes[0].episode_id, "train")
    with pytest.raises(ValueError, match="test is sealed"):
        fw.require_future_episode(protocol, protocol.manifests["test"].episodes[0].episode_id, "test")
    with pytest.raises(ValueError, match="quarantined"):
        fw.require_future_episode(protocol, next(iter(protocol.excluded_episode_ids)), "validation")


def test_frozen_selection_counts_and_phase_cover_are_deterministic(protocol):
    first = fw.planned_future_episodes(protocol)
    assert first == fw.planned_future_episodes(protocol)
    assert {k: len(v) for k, v in first.items()} == {"train": 30, "validation": 20}
    assert all(sum(e.task_name == task for e in first["validation"]) == 2 for task in {e.task_name for e in first["train"]})
    assert all(len(set(fw.legal_future_starts(e.num_steps))) == 3 for refs in first.values() for e in refs)
    with pytest.raises(ValueError, match="frozen at517"):
        fw.planned_future_episodes(protocol, 518)


@pytest.fixture
def stats():
    return {"q01": [-.5] * 6 + [0.], "q99": [.5] * 6 + [1.],
            "min": [-1.] * 6 + [0.], "max": [1.] * 6 + [1.], "mask": [True] * 6 + [False]}


def test_native_action_transform_is_not_raw_gripper_or_scaled_gripper(stats):
    raw = np.zeros((8, 7), dtype=np.float32)
    raw[:, 0] = [-2, -.5, -.25, 0, .25, .5, 1, 2]
    raw[:, 6] = [-1, 1, .2, -.2, 0, .5, 2, -2]
    before = raw.copy()
    result = fw.normalize_demo_actions(raw, stats)
    np.testing.assert_array_equal(result[:, 0], [-1, -1, -.5, 0, .5, 1, 1, 1])
    np.testing.assert_allclose(result[:, 6], [1, 0, .8, 1, 1, .5, 0, 1], atol=1e-7)
    np.testing.assert_array_equal(raw, before)
    assert result.dtype == np.float32 and result.shape == (8, 7)
    stats["min"][2] = stats["max"][2] = .1
    result = fw.normalize_demo_actions(raw, stats)
    assert (result[:, 2] == 0).all()


@pytest.mark.parametrize("change", ["missing_mask", "wrong_mask", "bad_quantile", "nan", "short"])
def test_action_targets_fail_closed_on_bad_statistics_or_chunk(stats, change):
    raw = np.zeros((8, 7), dtype=np.float32)
    if change == "missing_mask":
        stats.pop("mask")
    elif change == "wrong_mask":
        stats["mask"][-1] = True
    elif change == "bad_quantile":
        stats["q01"][0] = 20
    elif change == "nan":
        raw[0, 0] = np.nan
    else:
        raw = raw[:-1]
    with pytest.raises(ValueError):
        fw.normalize_demo_actions(raw, stats)


def test_normalization_matches_pinned_native_functions_without_tensorflow(stats):
    base = ROOT / "external/openvla-oft/prismatic/vla/datasets/rlds"
    if not base.exists():
        pytest.skip("pinned upstream audit checkout unavailable")
    def tree_map(value, match, map_fn, prefix=""):
        return {k: (tree_map(v, match, map_fn, f"{prefix}{k}/") if isinstance(v, dict)
                    else map_fn(v) if match(prefix + k, v) else v) for k, v in value.items()}
    tf = SimpleNamespace(where=np.where, clip_by_value=np.clip, concat=lambda xs, axis: np.concatenate(xs, axis),
                         ones_like=np.ones_like, bool=np.bool_)
    ns = {"Dict": dict, "Any": object, "tf": tf, "invert_gripper_actions": lambda x: 1 - x,
          "NormalizationType": SimpleNamespace(NORMAL=0, BOUNDS=1, BOUNDS_Q99=2),
          "dl": SimpleNamespace(transforms=SimpleNamespace(selective_tree_map=tree_map))}
    for path, function in ((base / "oxe/transforms.py", "libero_dataset_transform"),
                           (base / "utils/data_utils.py", "normalize_action_and_proprio")):
        node = next(n for n in ast.parse(path.read_text(encoding="utf-8")).body if isinstance(n, ast.FunctionDef) and n.name == function)
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), ns)
    raw = np.random.default_rng(9).uniform(-1.5, 1.5, (8, 7)).astype(np.float32)
    metadata = {key: {k: np.asarray(v) for k, v in stats.items()} for key in ("action", "proprio")}
    transformed = ns["libero_dataset_transform"]({"action": raw.copy(), "observation": {"state": np.zeros((8, 8), dtype=np.float32)}})
    # TF converts Python/NumPy statistics to the input floating dtype.
    metadata = {key: {k: v if k == "mask" else v.astype(np.float32) for k, v in values.items()} for key, values in metadata.items()}
    actual = ns["normalize_action_and_proprio"](transformed, metadata, 2)["action"]
    np.testing.assert_array_equal(fw.normalize_demo_actions(raw, stats), actual)


@pytest.fixture
def synthetic_manifest(tmp_path, protocol, monkeypatch):
    project = tmp_path / "project"
    panel_dir = project / "configs/manifests/spatial_g0g1_v1"
    panel_dir.mkdir(parents=True)
    shutil.copyfile(protocol.path.parent / "diagnostic_90.json", panel_dir / "diagnostic_90.json")
    local_protocol = replace(protocol, path=panel_dir / "protocol.json")
    planned = fw.planned_future_episodes(local_protocol)
    by_shard = {}
    by_id = {}
    for refs in planned.values():
        for ref in refs:
            by_shard.setdefault(ref.source_shard, {})[ref.record_index] = ref
            by_id[ref.episode_id] = ref
    data = project / "data"
    data.mkdir()
    asset = {"repository": "openvla/modified_libero_rlds", "revision": "6ce6aaaaabdbe590b1eef5cd29c0d33f14a08551", "files": []}
    for name in by_shard:
        (data / name).write_bytes(b"synthetic")
        asset["files"].append({"path": name, "size": 9, "lfs_oid": file_sha256(data / name)})
    asset_path = project / "configs/assets/libero_spatial_rlds.json"
    write_frozen_json(asset_path, asset)
    monkeypatch.setattr(fw, "iter_tfrecord_records", lambda path: ((index, ref.episode_id.encode()) for index, ref in sorted(by_shard[path.name].items())))
    monkeypatch.setattr(fw, "decode_libero_example", lambda value: fake_episode(by_id[value.decode()]))
    payload = fw.build_future_windows(local_protocol, data, asset_path)
    path = project / "configs/manifests/spatial_future_v1/windows.json"
    write_frozen_json(path, payload)
    return path, local_protocol, payload, data, asset_path


def test_manifest_integrates_150_windows_and_strictly_replays_selection(synthetic_manifest):
    path, protocol, payload, *_ = synthetic_manifest
    assert fw.load_future_windows(path, protocol) == payload
    assert payload["summary"]["train"]["windows"] == 90
    assert payload["summary"]["validation"]["windows"] == 60
    assert not payload["exclusions"]
    assert len({r["window_id"] for r in payload["windows"]}) == 150


@pytest.mark.parametrize("change", ["seed", "interval", "missing", "source", "summary", "test"])
def test_resigned_manifest_cannot_override_rules_or_self_pin_source(synthetic_manifest, change):
    path, protocol, payload, *_ = synthetic_manifest
    if change == "seed":
        payload["validation_seed"] = 518
    elif change == "interval":
        payload["windows"][0]["action_stop_exclusive"] += 1
    elif change == "missing":
        payload["windows"].pop()
    elif change == "source":
        next(iter(payload["source_files"].values()))["sha256"] = "0" * 64
    elif change == "summary":
        payload["summary"]["train"]["windows"] -= 1
    else:
        payload["windows"][0]["split"] = "test"
    payload.pop("content_signature")
    payload["content_signature"] = fw._signature(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        fw.load_future_windows(path, protocol)


def test_actual_source_bytes_checked_before_selected_episode_decode(synthetic_manifest):
    _, protocol, _, data, asset_path = synthetic_manifest
    next(data.iterdir()).write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="source hash differs"):
        fw.build_future_windows(protocol, data, asset_path)

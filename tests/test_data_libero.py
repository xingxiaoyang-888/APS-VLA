from dataclasses import replace
import json

import pytest

from cti_vla.data.identity import canonical_mapping_signature, file_set_signature, stable_sample_id
from cti_vla.data.libero import (
    LiberoEpisodeRef, LiberoSampleRef, STAGES, assert_episode_disjoint,
    build_stage_covered_manifest, load_manifest, save_manifest, split_episodes,
)

SOURCE = "sha256:" + "a" * 64


def episodes(tasks=2, per_task=10):
    return [LiberoEpisodeRef(f"task-{task}/demo-{index}", 9 + index, f"task-{task}",
                            "train.tfrecord", task * per_task + index)
            for task in range(tasks) for index in range(per_task)]


def manifest(values=None, **kwargs):
    return build_stage_covered_manifest(episodes() if values is None else values,
                                       split="train", source_signature=SOURCE, **kwargs)


def test_full_episode_stages_and_endpoints_roundtrip(tmp_path):
    result = manifest(samples_per_episode=5)
    assert result.sample_count == 100
    for episode in result.episodes:
        rows = [row for row in result.samples if row.episode_id == episode.episode_id]
        assert set(row.stage for row in rows) == set(STAGES)
        assert rows[0].step_index == 0
        assert rows[-1].step_index == episode.num_steps - 1
    target = save_manifest(tmp_path / "train.json", result)
    assert load_manifest(target) == result
    with pytest.raises(FileExistsError):
        save_manifest(target, result)


def test_splits_have_no_episode_leakage_and_all_tasks():
    values = episodes()
    splits = split_episodes(values, seed=17)
    assert splits == split_episodes(reversed(values), seed=17)
    assert splits != split_episodes(values, seed=18)
    assert {key: len(value) for key, value in splits.items()} == {"train": 14, "validation": 2, "test": 4}
    results = []
    for split, values in splits.items():
        assert {row.task_name for row in values} == {"task-0", "task-1"}
        results.append(build_stage_covered_manifest(values, split=split, source_signature=SOURCE, seed=17))
    assert_episode_disjoint(*results)
    with pytest.raises(ValueError, match="episode-overlapping"):
        assert_episode_disjoint(results[0], results[0])


def test_sampling_stable_under_input_order_and_truncates_short_episodes():
    values = episodes()
    assert manifest(values, samples_per_episode=7, seed=7) == manifest(reversed(values), samples_per_episode=7, seed=7)
    assert manifest(values, samples_per_episode=7, seed=7) != manifest(values, samples_per_episode=7, seed=8)
    tiny = [LiberoEpisodeRef("a", 3, "task", "shard", 0)]
    assert manifest(tiny, samples_per_episode=8).sample_count == 3


def test_manifests_fail_closed_for_stale_or_forged_metadata(tmp_path):
    result = manifest()
    with pytest.raises(ValueError, match="coverage"):
        replace(result, samples=tuple(row for row in result.samples if row.stage != "late"))
    with pytest.raises(ValueError, match="stage disagrees"):
        replace(result, samples=(replace(result.samples[0], stage="late"),) + result.samples[1:])
    with pytest.raises(ValueError, match="identity"):
        replace(result.samples[0], sample_id=123)
    with pytest.raises(ValueError, match="duplicate original"):
        manifest([episodes()[0], episodes()[0]])
    with pytest.raises(ValueError, match="too few episodes"):
        split_episodes(episodes(per_task=2), seed=0)
    old = tmp_path / "old.json"
    old.write_text(json.dumps({"schema_version": 1, "samples": []}))
    with pytest.raises(ValueError, match="historical pilots"):
        load_manifest(old)


def test_original_episode_identity_survives_resharding():
    episode = episodes()[0]
    shifted = replace(episode, source_shard="other-shard", record_index=7)
    assert LiberoSampleRef.create(episode, 0) == LiberoSampleRef.create(shifted, 0)
    with pytest.raises(ValueError, match="episode-overlapping"):
        assert_episode_disjoint(manifest([episode]), manifest([shifted]))


def test_identity_is_strict_and_file_signature_is_portable(tmp_path):
    for step in (-1, True, 1.5):
        with pytest.raises(ValueError):
            stable_sample_id("data", "episode", step)
    assert stable_sample_id("a\x1fb", "c", 0) != stable_sample_id("a", "b\x1fc", 0)
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()
    for root in (source, dest):
        (root / "one").write_bytes(b"1")
        (root / "two").write_bytes(b"2")
    assert file_set_signature(source.iterdir(), namespace="test") == file_set_signature(dest.iterdir(), namespace="test")
    with pytest.raises(ValueError, match="unique basenames"):
        file_set_signature([source / "one", dest / "one"], namespace="test")
    with pytest.raises(ValueError):
        canonical_mapping_signature({"invalid": float("nan")}, namespace="test")

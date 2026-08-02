import pytest

from diwa.data.libero import (
    LiberoManifest,
    LiberoSampleRef,
    assert_episode_disjoint,
    build_pilot_manifest,
    load_manifest,
    save_manifest,
)


def test_pilot_manifest_is_stable_sorted_and_contract_checked(tmp_path):
    manifest = build_pilot_manifest(["episode-2", "episode-1"], steps_per_episode=2)
    assert manifest.sample_count == 4
    assert manifest.episode_count == 2
    assert [sample.episode_id for sample in manifest.samples] == [
        "episode-1",
        "episode-1",
        "episode-2",
        "episode-2",
    ]
    assert manifest.samples[0].sample_id == LiberoSampleRef.create("episode-1", 0).sample_id
    path = save_manifest(tmp_path / "pilot.json", manifest)
    assert load_manifest(path) == manifest


def test_manifest_rejects_episode_leakage_and_duplicate_rows():
    train = build_pilot_manifest(["shared"], steps_per_episode=1, split="train")
    valid = build_pilot_manifest(["shared"], steps_per_episode=1, split="valid")
    with pytest.raises(ValueError, match="episode-overlapping"):
        assert_episode_disjoint(train, valid)
    duplicate = LiberoSampleRef.create("episode", 0)
    with pytest.raises(ValueError, match="duplicate"):
        LiberoManifest(split="bad", samples=(duplicate, duplicate))


def test_manifest_rejects_stale_temp_and_contract_mismatch(tmp_path):
    manifest = build_pilot_manifest(["episode"], steps_per_episode=1)
    path = tmp_path / "pilot.json"
    path.with_suffix(".json.tmp").write_text("incomplete", encoding="utf-8")
    with pytest.raises(FileExistsError, match="temporary"):
        save_manifest(path, manifest)
    with pytest.raises(ValueError, match="action/image contract"):
        LiberoManifest(split="bad", samples=manifest.samples, action_dim=14)

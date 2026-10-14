"""CPU journal/statistical behavior, not a G1 experiment or scientific result."""

import importlib.util
import json
from pathlib import Path

import pytest
import torch

from cti_vla.data.experiment_protocol import load_experiment_protocol
from cti_vla.data.identity import file_sha256
from cti_vla.evaluation.teacher_diagnostics import (
    ActionQueryCache, atomic_json, json_signature, run_exact_selection,
    run_intervention_panel, run_repeatability,
)
from cti_vla.labeling.sampling import fixed_anchor_panel

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


d4 = load_script("analyze_g1_d4")


@pytest.fixture(scope="module")
def journal(tmp_path_factory):
    root = tmp_path_factory.mktemp("g1-journal")
    visual = torch.arange(512, dtype=torch.float32)[None, :, None] / 512
    def forward(source, indices):
        selected = source[:, indices[0]]
        value = selected.square().mean() + .3 * selected.mean()
        return value.expand(1, 8, 7).clone()
    observation = {"sample_id": 34, "episode_id": "toy-episode", "task_name": "toy-task", "stage": "middle", "is_last_step": False}
    path = root / "34.jsonl"
    oracle = ActionQueryCache(visual, forward, identity={"config_sha256": "toy-config", "sample": observation}, journal_path=path)
    fixed = fixed_anchor_panel(34, seed=517)
    panel = run_intervention_panel(oracle, fixed)
    exact = run_exact_selection(oracle, sample_id=34, seed=517)
    repeated = run_repeatability(oracle, fixed[0].candidate_indices[0])
    return path, observation, panel, exact, repeated


def test_replay_recomputes_real_queries_without_policy(journal):
    path, observation, panel, exact, repeated = journal
    oracle = d4.JournalActions(path, config_sha="toy-config", observation=observation)
    fixed = fixed_anchor_panel(34, seed=517)
    d4.assert_same(panel, run_intervention_panel(oracle, fixed))
    d4.assert_same(exact, run_exact_selection(oracle, sample_id=34, seed=517))
    d4.assert_same(repeated, run_repeatability(oracle, fixed[0].candidate_indices[0]))
    assert oracle.ledger["sample_forwards_completed"] == oracle.ledger["sample_forwards_attempted"]
    with pytest.raises(ValueError, match="absent"):
        oracle.query((0, 256), category="unregistered", repeat_id="unissued")


def test_replay_rejects_modified_action_bytes(tmp_path, journal):
    path, observation, *_ = journal
    events = [json.loads(line) for line in path.read_text().splitlines()]
    next(row for row in events if row["event"] == "complete")["action"][0][0][0] += 1
    changed = tmp_path / "changed.jsonl"
    changed.write_text("\n".join(json.dumps(row) for row in events) + "\n")
    with pytest.raises(ValueError, match="checksum"):
        d4.JournalActions(changed, config_sha="toy-config", observation=observation)


def test_paired_statistics_do_not_count_seeds_or_tokens_as_observations(journal):
    _, observation, panel, exact, _ = journal
    metrics, candidates = d4.observation_metrics(observation, panel, exact, noise_tolerance=1e-6)
    assert len(candidates) == 5 * 16 * 2
    deltas = [r for r in metrics if r["family"] == "teacher_paired_delta" and r["variant"] == "full_loo_static" and r["keep_count"] == 256]
    assert len(deltas) == 19 and all(row["value"] == 0 for row in deltas)
    random = [r for r in metrics if r["family"] == "selection_action" and r["keep_count"] == 64 and r["metric"] == "mean_l1"]
    values = {row["variant"]: row["value"] for row in random}
    assert values["random_mean"] == pytest.approx(sum(values[f"random_seed_{s}"] for s in (17, 23, 41)) / 3)
    with pytest.raises(ValueError, match="pseudoreplication"):
        d4.summarize([metrics[0], metrics[0]], repeats=100)


def test_bootstrap_preserves_whole_episode_clusters():
    rows = [{"episode_id": episode, "value": value} for episode, value in (("a", 0.), ("b", 10.)) for _ in range(3)]
    result = d4.clustered_interval(rows, repeats=1000, seed=17)
    assert result["n_observations"] == 6 and result["n_episodes"] == 2
    assert result["mean"] == 5 and result["ci95_low"] == 0 and result["ci95_high"] == 10
    assert result == d4.clustered_interval(rows, repeats=1000, seed=17)
    single = d4.clustered_interval(rows[:3], repeats=1000, seed=17)
    assert single["ci95_low"] is None and single["ci95_high"] is None


def test_undefined_rank_remains_missing_and_stored_summary_checked():
    result = d4.clustered_interval([{"episode_id": "a", "value": None}, {"episode_id": "b", "value": None}], repeats=1000, seed=17)
    assert result["mean"] is None and result["n_undefined"] == 2 and result["ci95_low"] is None
    with pytest.raises(ValueError, match="recomputation"):
        d4.assert_same({"signed": -.1}, {"signed": .1})


@pytest.fixture
def finalized_panel(tmp_path):
    protocol = load_experiment_protocol(ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")
    asset_path = ROOT / "configs/assets/openvla_oft_libero_spatial.json"
    asset = json.loads(asset_path.read_text(encoding="utf-8"))
    producer = load_script("run_teacher_diagnostics")
    panel = producer.build_observation_panel(protocol, repeat_seed=617)
    config = {"stage": "G1", "diagnostics_version": d4.DIAGNOSTICS_VERSION,
              "model_revision": asset["revision"], "asset_manifest_sha256": file_sha256(asset_path),
              "protocol_signature": protocol.payload["content_signature"], "panel_sha256": json_signature(panel),
              "repeat_seed": 617, "source_snapshot": {name: file_sha256(ROOT / name) for name in
                  ("src/cti_vla/evaluation/teacher_diagnostics.py", "src/cti_vla/labeling/sampling.py")}}
    atomic_json(tmp_path / "config.json", config)
    atomic_json(tmp_path / "observation_panel.json", panel)
    receipt = {"status": "verified", "config_sha256": json_signature(config), "checkpoint_unchanged": True,
               "checkpoint_verification": {"repository": asset["repository"], "revision": asset["revision"],
                                            "file_count": len(asset["files"]), "total_bytes": asset["total_bytes"]},
               "observation_files": {}, "query_journals": {}}
    for row in panel["observations"]:
        key = str(row["sample_id"])
        for folder, suffix, mapping in (("observations", ".json", "observation_files"), ("queries", ".jsonl", "query_journals")):
            path = tmp_path / folder / (key + suffix)
            atomic_json(path, {"synthetic": True})
            receipt[mapping][key] = file_sha256(path)
    atomic_json(tmp_path / "finalization.json", receipt)
    return tmp_path, protocol, panel, config, receipt


def test_panel_uses_real_registered_90_12_and_receipt_hashes(finalized_panel):
    path, protocol, _, _, _ = finalized_panel
    _, rows, _ = d4.verify_panel(path, protocol)
    assert len(rows) == 90 and sum(row["exact_selection"] for row in rows) == 12
    key = str(rows[0]["sample_id"])
    atomic_json(path / "queries" / (key + ".jsonl"), {"changed": True})
    with pytest.raises(ValueError, match="no longer binds"):
        d4.verify_panel(path, protocol)


def test_panel_rejects_wrong_split_even_if_hashes_recomputed(finalized_panel):
    path, protocol, panel, config, receipt = finalized_panel
    test_sample = protocol.manifests["test"].samples[0]
    panel["observations"][0]["episode_id"] = test_sample.episode_id
    panel["observations"][0]["step_index"] = test_sample.step_index
    config["panel_sha256"] = json_signature(panel)
    receipt["config_sha256"] = json_signature(config)
    atomic_json(path / "observation_panel.json", panel)
    atomic_json(path / "config.json", config)
    atomic_json(path / "finalization.json", receipt)
    with pytest.raises(ValueError, match="authoritative episode split"):
        d4.verify_panel(path, protocol)


def test_incomplete_panel_and_missing_final_verification_rejected(finalized_panel):
    path, protocol, _, _, receipt = finalized_panel
    receipt["checkpoint_unchanged"] = False
    atomic_json(path / "finalization.json", receipt)
    with pytest.raises(ValueError, match="finalization"):
        d4.verify_panel(path, protocol)


def test_unregistered_query_and_different_checkpoint_receipt_rejected(finalized_panel):
    path, protocol, _, _, receipt = finalized_panel
    receipt["checkpoint_verification"]["revision"] = "another-model"
    atomic_json(path / "finalization.json", receipt)
    with pytest.raises(ValueError, match="registered Spatial asset"):
        d4.verify_panel(path, protocol)


def test_extra_query_file_cannot_hide_unregistered_teacher_cost(finalized_panel):
    path, protocol, _, _, _ = finalized_panel
    atomic_json(path / "queries" / "unregistered.jsonl", {"synthetic": True})
    with pytest.raises(ValueError, match="unregistered"):
        d4.verify_panel(path, protocol)


def test_figures_export_as_standalone_scientific_artifacts(tmp_path, journal):
    _, observation, panel, exact, _ = journal
    metrics, _ = d4.observation_metrics(observation, panel, exact, noise_tolerance=1e-6)
    groups = d4.summarize(metrics, repeats=100)
    paths = d4.make_figures(tmp_path, groups, synthetic=True)
    assert len(paths) == 6 and all((tmp_path / name).stat().st_size > 1000 for name in paths)

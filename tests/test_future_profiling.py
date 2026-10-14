"""CPU contract tests, synthetic arrays/policy only; no GPU performance claim."""
from contextlib import nullcontext
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation import libero_runtime
from cti_vla.evaluation.future_profiling import (CaptureDense, FixedStepObservation, load_future_raw_panel,
    load_script, profile_states, save_dense_episode, validate_new_output_paths, write_future_panel)
from cti_vla.evaluation.future_trials import load_future_development_panel
from cti_vla.evaluation.profiling import ProfileConfig, ProfileJournal, ProfileMethod, profile_methods, read_profile_cost, verify_measurement_journal
from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
from test_selector_runtime import env_observation, STATS_KEY
from test_future_runtime import good_policy, synthetic_policy
from test_observation_profiling import Clock

ROOT = Path(__file__).resolve().parents[1]
STATES = ROOT / "configs/manifests/spatial_initial_states_v1"
DEV, G0 = STATES / "init_states_development.json", STATES / "g0_development_15.json"


class SteppingEnv:
    def __init__(self, length):
        self.length = length
    def reset(self):
        self.step_count = 0
    def observation(self):
        obs = env_observation()
        obs["agentview_image"].fill(self.step_count)
        obs["robot0_eye_in_hand_image"].fill(self.step_count + 1)
        return obs
    def set_init_state(self, values):
        return self.observation()
    def step(self, action):
        self.step_count += 1
        return self.observation(), 0, self.length < 220 and self.step_count == self.length + 10, {}


def panel_fixture(tmp_path):
    panel = load_future_development_panel(DEV, G0)
    provenance = {"checkpoint_unchanged": True, "model_revision": "synthetic", "runtime_sha256": "a" * 64}
    episodes = []
    for state, length in zip(profile_states(panel), (9, 81, 220)):
        capture = CaptureDense(good_policy)
        result = libero_runtime.run_episode(SteppingEnv(length), capture, "pick the bowl", state["initial_state"])
        episodes.append(save_dense_episode(tmp_path / f"task_{state['task_id']}", state, "pick the bowl", result,
            capture.captured, provenance=provenance))
    write_future_panel(tmp_path, panel, episodes, provenance=provenance)
    return tmp_path / "panel.json"


def load(path):
    return load_future_raw_panel(path, development_path=DEV, g0_panel_path=G0)


def resign_panel(path, payload):
    payload["content_signature"] = json_signature({k: v for k, v in payload.items() if k != "content_signature"})
    atomic_json(path, payload)


def mutate_receipt(panel_path, mutate):
    panel = json.loads(panel_path.read_text(encoding="utf-8"))
    reference = panel["episodes"][1]["receipt"]
    path = panel_path.parent / reference["path"]
    receipt = json.loads(path.read_text(encoding="utf-8"))
    mutate(receipt, path)
    atomic_json(path, receipt)
    reference["sha256"] = file_sha256(path)
    resign_panel(panel_path, panel)


def test_capture_uses_control_step_after_wait_and_never_substitutes_last_frame(tmp_path):
    path = panel_fixture(tmp_path)
    samples, metadata = load(path)
    assert [s.control_step for s in samples] == [0, 0, 80, 0, 80, 160]
    assert [int(s.observation["agentview_image"][0, 0, 0]) for s in samples] == [10, 10, 90, 10, 90, 170]
    assert samples[2].phase == "control_step_80"
    assert metadata["target_observations"] == 9 and metadata["observations"] == 6
    assert [m["control_step"] for m in metadata["missing"]] == [80, 160, 160]
    assert sum(r["policy_calls"] for r in metadata["collection_cost_excluded"]) == 2 + 11 + 28


@pytest.mark.parametrize("change", ["missing", "query", "trace", "terminal", "state", "raw", "path", "runtime"])
def test_even_resigned_receipt_cannot_change_fixed_step_or_raw_source(tmp_path, change):
    path = panel_fixture(tmp_path)
    def mutate(receipt, receipt_path):
        if change == "missing":
            receipt["observations"].pop()
        elif change == "query":
            receipt["observations"][1]["query_index"] = 9
        elif change == "trace":
            receipt["chunks"][10]["control_step"] = 79
        elif change == "terminal":
            receipt["termination"] = "task_horizon"
            receipt["success"] = False
        elif change == "state":
            receipt["source_state_index"] += 1
        elif change == "runtime":
            receipt["provenance"]["runtime_sha256"] = "b" * 64
        elif change == "path":
            receipt["observations"][0]["arrays"]["path"] = "../../outside.npz"
        else:
            ref = receipt["observations"][0]["arrays"]
            target = receipt_path.parent / ref["path"]
            with np.load(target, allow_pickle=False) as archive:
                arrays = {key: archive[key].copy() for key in archive.files}
            arrays["agentview_image"] += 1
            np.savez(target, **arrays)
            ref["sha256"] = file_sha256(target)
    mutate_receipt(path, mutate)
    with pytest.raises((ValueError, FileNotFoundError)):
        load(path)


def test_test_split_is_rejected_before_opening_any_references(tmp_path, monkeypatch):
    path = tmp_path / "panel.json"
    atomic_json(path, {"split": "test", "test_opened": False})
    original = Path.read_text
    def read(p, *args, **kwargs):
        assert p == path, "must not open final-state references"
        return original(p, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", read)
    with pytest.raises(ValueError, match="final-test"):
        load(path)


def test_three_first_states_are_fixed_independent_of_outcomes(tmp_path):
    path = panel_fixture(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["episodes"][0]["state_trial_id"] = payload["episodes"][1]["state_trial_id"]
    resign_panel(path, payload)
    with pytest.raises(ValueError, match="predeclared"):
        load(path)


def test_failed_trajectory_does_not_create_valid_panel(tmp_path):
    panel = load_future_development_panel(DEV, G0)
    with pytest.raises(ValueError, match="failed dense"):
        save_dense_episode(tmp_path / "bad", profile_states(panel)[0], "instruction", {"status": "policy_error"}, {}, provenance={})
    assert not (tmp_path / "bad").exists()


def test_snapshot_weights_and_prior_results_cannot_be_overwritten(tmp_path):
    project = tmp_path / "project"
    source = project / "snapshots/v1"
    weights = project / "checkpoints/A"
    base = dict(project_root=project, source_root=source, cache=project / "cache", weight_roots=[weights])
    validate_new_output_paths(output=project / "results/new", **base)
    for output in (source / "new", weights / "new", tmp_path / "outside"):
        with pytest.raises(ValueError):
            validate_new_output_paths(output=output, **base)
    prior = project / "results/prior"
    prior.mkdir(parents=True)
    with pytest.raises(FileExistsError):
        validate_new_output_paths(output=prior, **base)


def test_actual_future_adapter_and_matched_baselines_share_uninstrumented_primary_pass(tmp_path, monkeypatch):
    policy, components, _ = synthetic_policy(tmp_path, monkeypatch, record_selection=False)
    baseline = load_script(ROOT, "profile_observation_to_action")
    factories = {}
    created = []
    for name in ("dense", "uniform128", "future_A", "future_B"):
        def factory(name=name):
            p = policy if name.startswith("future") else baseline.MatchedBaseline(components, object(), stats_key=STATS_KEY, method=name)
            created.append(name)
            return ProfileMethod(p, {"cache_scope": "none", "instruction_cache_enabled": False},
                lambda context: setattr(p, "stage_context", context or (lambda _: nullcontext())))
        factories[name] = factory
    sample = FixedStepObservation("sample", "episode", "task", "first", 80, env_observation())
    clock = Clock()
    journal_path = tmp_path / "calls.jsonl"
    result = profile_methods([sample], factories, config=ProfileConfig(warmup_calls=1, repeats=1,
        component_repeats=1, synthetic=True), clock=clock, emit=ProfileJournal(journal_path, {"synthetic": True}), timer=clock.timer)
    result["cost"] = read_profile_cost(journal_path)
    verify_measurement_journal(result, journal_path)
    assert result["cost"]["completed"] == 20
    assert components.vla.vision_calls == len(components.vla.language_model.model.calls) == 20
    assert all("components" not in row for row in result["rows"] if row["kind"] == "main")
    assert all(row["phase"] == "control_step_80" for row in result["rows"])
    assert len(created) == 8


def test_collector_prepare_only_does_not_import_environment_or_accept_gate():
    script = load_script(ROOT, "collect_future_profile_panel")
    result = script.run(SimpleNamespace(development_states=DEV, g0_panel=G0, prepare_only=True))
    assert result["gpu_calls"] == 0 and len(result["state_trial_ids"]) == 3 and not result["test_opened"]


def test_profiler_prepare_only_validates_panel_without_loading_checkpoint(tmp_path):
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    path = panel_fixture(tmp_path)
    asset_path = ROOT / "configs/assets/openvla_oft_libero_spatial.json"
    asset = load_checkpoint_manifest(asset_path)
    expected = {"model_revision": asset.revision, "input_version": libero_runtime.INPUTS_VERSION,
        "packing_version": PACKING_VERSION, "action_version": libero_runtime.ACTION_VERSION,
        "stats_key": "libero_spatial_no_noops", "runtime_sha256": file_sha256(libero_runtime.__file__)}
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["provenance"].update(expected)
    for episode in payload["episodes"]:
        receipt_path = path.parent / episode["receipt"]["path"]
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["provenance"] = payload["provenance"]
        atomic_json(receipt_path, receipt)
        episode["receipt"]["sha256"] = file_sha256(receipt_path)
    resign_panel(path, payload)
    script = load_script(ROOT, "profile_future_observation_to_action")
    result = script.run(SimpleNamespace(panel=path, development_states=DEV, g0_panel=G0,
        prepare_only=True, asset_manifest=asset_path, stats_key="libero_spatial_no_noops", order_seed=1017))
    assert result["planned_full_pipeline_calls"] == 4 * (50 + 6 * 2 * 6)
    assert result["checkpoint_validated"] is result["f01_accepted"] is result["cache_enabled"] is False

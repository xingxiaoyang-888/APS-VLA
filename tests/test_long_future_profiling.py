"""Long profiling protocol tests use synthetic arrays/clock, never latency claims."""
from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys

import numpy as np
import pytest

from cti_vla.data.identity import file_sha256
from cti_vla.data.long_initial_states import load_long_development_panel
from cti_vla.evaluation import future_long_profiling as p, libero_runtime
from cti_vla.evaluation.future_dense_reuse import load_dense_reference
from cti_vla.evaluation.future_profiling import load_script
from cti_vla.evaluation.profiling import ProfileJournal, ProfileMethod, read_profile_cost
from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
from test_observation_profiling import Clock, sample
from test_future_profiling import SteppingEnv
from test_future_runtime import good_policy

ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = ROOT / "configs/experiments/g1_future_long_k64_v1.json"
PANEL = ROOT / "configs/manifests/long_initial_states_v1/development_panel_30.json"
REFERENCE = ROOT / "results/g1_future_long_v1/closed_loop"


def registration():
    return json.loads(REGISTRATION.read_text(encoding="utf-8"))


def test_registered_long_steps_derive_from_original_dense_not_new_outcomes():
    panel = load_long_development_panel(PANEL)
    reference = load_dense_reference(REFERENCE, panel)
    states = p.fixed_long_profile_states(panel, reference, registration())
    assert [s["task_id"] for s in states] == [0, 3, 5]
    assert [s["source_state_index"] for s in states] == [0, 3, 2]
    assert [s["reference_control_steps"] for s in states] == [380, 220, 148]
    assert [s["requested_control_steps"] for s in states] == [[0, 184, 336], [0, 104, 192], [0, 72, 128]]
    changed = registration()
    changed["profiling"]["task_control_steps"]["0"] = [0, 80, 160]
    with pytest.raises(ValueError, match="preregistration"):
        p.fixed_long_profile_states(panel, reference, changed)


def panel_fixture(tmp_path, monkeypatch):
    panel = load_long_development_panel(PANEL)
    reference = load_dense_reference(REFERENCE, panel)
    states = p.fixed_long_profile_states(panel, reference, registration())
    probe = SteppingEnv(380)
    probe.reset()
    probe.step_count = 10
    for state in states:
        state["reference_initial_observation_sha256"] = libero_runtime._observation_hash(probe.observation())
    monkeypatch.setattr(p, "fixed_long_profile_states", lambda *a: states)
    provenance = {"checkpoint_unchanged": True, "synthetic": True}
    episodes = []
    for state, length in zip(states, (380, 120, 148)):
        class LongSteppingEnv(SteppingEnv):
            def observation(self):
                # Preserve the exact synthetic initial observation shape/proprio.
                from test_selector_runtime import env_observation
                base = env_observation()
                base["agentview_image"].fill(self.step_count % 256)
                base["robot0_eye_in_hand_image"].fill((self.step_count + 1) % 256)
                return base
            def step(self, action):
                self.step_count += 1
                return self.observation(), 0, self.step_count == self.length + 10, {}
        capture = p.CaptureLongDense(good_policy, state["requested_control_steps"])
        result = libero_runtime.run_episode(LongSteppingEnv(length), capture, "synthetic instruction",
            state["initial_state"], max_steps=520)
        episodes.append(p.save_long_dense_episode(tmp_path / f"task_{state['task_id']}", state,
            "synthetic instruction", result, capture.captured, provenance=provenance))
    p.write_long_raw_panel(tmp_path, panel, episodes, provenance=provenance, registration=registration())
    return tmp_path / "panel.json", panel, reference


def load_panel(args):
    path, panel, reference = args
    return p.load_long_raw_panel(path, development_panel=panel, dense_reference=reference, registration=registration())


def test_long_collector_preserves_missing_late_query_without_substitution(tmp_path, monkeypatch):
    fixture = panel_fixture(tmp_path, monkeypatch)
    samples, meta = load_panel(fixture)
    assert [s.control_step for s in samples] == [0, 184, 336, 0, 104, 0, 72, 128]
    assert meta["observations"] == 8 and meta["target_observations"] == 9
    assert len(meta["missing"]) == 1 and meta["missing"][0]["control_step"] == 192
    assert meta["test_opened"] is False


@pytest.mark.parametrize("change", ["first", "missing", "query", "raw", "terminal", "source_state"])
def test_long_panel_rejects_even_resigned_bad_trajectory_evidence(tmp_path, monkeypatch, change):
    fixture = panel_fixture(tmp_path, monkeypatch)
    path = fixture[0]
    panel = json.loads(path.read_text(encoding="utf-8"))
    ref = panel["episodes"][1]["receipt"]
    receipt_path = path.parent / ref["path"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if change == "first":
        receipt["chunks"][0]["observation_sha256"] = "f" * 64
    elif change == "missing":
        receipt["missing"] = []
    elif change == "query":
        receipt["observations"][1]["control_step"] = 112
    elif change == "raw":
        rec = receipt["observations"][0]["arrays"]
        array_path = receipt_path.parent / rec["path"]
        with np.load(array_path, allow_pickle=False) as archive:
            arrays = {key: archive[key].copy() for key in archive.files}
        arrays["robot0_eef_pos"] += 1
        np.savez(array_path, **arrays)
        rec["sha256"] = file_sha256(array_path)
    elif change == "terminal":
        receipt["termination"] = "task_horizon"
        receipt["success"] = False
    else:
        receipt["source_state_index"] += 1
    atomic_json(receipt_path, receipt)
    ref["sha256"] = file_sha256(receipt_path)
    panel["content_signature"] = json_signature({k: v for k, v in panel.items() if k != "content_signature"})
    atomic_json(path, panel)
    with pytest.raises(ValueError):
        load_panel(fixture)


def test_long_panel_rejects_test_before_reference_or_array_access(tmp_path):
    path = tmp_path / "panel.json"
    atomic_json(path, {"split": "test", "test_opened": False})
    with pytest.raises(ValueError, match="never reads test"):
        p.load_long_raw_panel(path, development_panel=None, dense_reference=None, registration={})


def test_balanced_schedule_exact_count_common_observations_and_fixed_order():
    ids = ["z-first", "a-middle", "m-last"]
    schedule = p.balanced_schedule(ids)
    assert schedule == p.balanced_schedule(ids)
    assert len(schedule) == 20
    for block in schedule:
        assert set(block["method_order"]) == set(p.LONG_METHODS)
        assert set(block["observation_order"]) == set(ids)
    for name in p.LONG_METHODS:
        counts = [sum(b["method_order"][i] == name for b in schedule) for i in range(13)]
        assert max(counts) - min(counts) == 1


def test_original_module_switch_restores_both_import_paths_after_exception():
    import cti_vla.training as package
    from cti_vla.training import future_auxiliary
    original = future_auxiliary
    fake = SimpleNamespace(marker="frozen exact module")
    with pytest.raises(RuntimeError, match="test failure"):
        with p.original_auxiliary_module(fake):
            from cti_vla.training import future_auxiliary as actual
            assert actual is fake
            assert sys.modules["cti_vla.training.future_auxiliary"] is fake
            with pytest.raises(RuntimeError, match="strictly serial"):
                with p.original_auxiliary_module(fake):
                    pass
            raise RuntimeError("test failure")
    assert package.future_auxiliary is original
    assert sys.modules["cti_vla.training.future_auxiliary"] is original


def test_snapshot_loader_rejects_shared_execution_dependency_drift(tmp_path):
    source, current = tmp_path / "old", tmp_path / "new"
    content = {
        "src/cti_vla/evaluation/future_runtime.py": "def future_deployment_source_hashes(root):\n from pathlib import Path\n from cti_vla.data.identity import file_sha256\n return {'src/cti_vla/training/future_auxiliary.py': file_sha256(Path(root) / 'src/cti_vla/training/future_auxiliary.py')}\n",
        "src/cti_vla/training/future_auxiliary.py": "marker = 'original'\n",
        "src/cti_vla/models/test_model.py": "x = 1\n",
        "src/cti_vla/selection/test_selector.py": "x = 2\n",
        "src/cti_vla_baselines/acl_matched.py": "x = 3\n",
        "src/cti_vla/evaluation/libero_runtime.py": "x = 4\n"}
    hashes = {}
    for key, value in content.items():
        for root in (source, current):
            path = root / key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value, encoding="utf-8")
        hashes[key] = file_sha256(source / key)
    inventory = tmp_path / "inventory.json"
    atomic_json(inventory, {"files": hashes})
    runtime, aux, receipt = p.load_snapshot_deployment_modules(source, inventory, current_root=current)
    assert aux.marker == "original" and receipt["deployment_source_files"]
    (current / "src/cti_vla/selection/test_selector.py").write_text("x=9", encoding="utf-8")
    with pytest.raises(ValueError, match="shared model/selection/input"):
        p.load_snapshot_deployment_modules(source, inventory, current_root=current)


def synthetic_run(tmp_path, *, failing=None, bad_tokens=None):
    log, factories = [], {}
    for name in p.LONG_METHODS:
        @contextmanager
        def factory(name=name):
            context = None
            def set_context(value):
                nonlocal context
                context = value
            def policy(observation, instruction):
                assert context is None, "main and warmup must have no component hooks"
                log.append((name, instruction, observation["agentview_image"].shape))
                if name == failing:
                    raise RuntimeError("synthetic deployment failure")
                budget = 512 if name == "dense" else int(name.split("_")[0][1:])
                metadata = {"policy_calls": 1, "vision_calls": 1, "visual_tokens": budget,
                    "language_cache": "disabled", "future_head_calls": 0, "scorer_calls": 1}
                if name == bad_tokens:
                    metadata["visual_tokens"] = 128 if budget == 64 else 64
                return SimpleNamespace(environment_actions=np.zeros((8, 7)), metadata=metadata)
            yield ProfileMethod(policy, {"cache_scope": "none", "instruction_cache_enabled": False,
                "future_head_deployed": False}, set_context)
        factories[name] = factory
    samples = [sample(2), sample(0), sample(1)]
    config = {**registration()["profiling"], "synthetic": True}
    path = tmp_path / "calls.jsonl"
    clock = Clock()
    result = p.profile_long_methods(samples, factories, config=config, clock=clock,
        emit=ProfileJournal(path, {"synthetic": True}), timer=clock.timer)
    result["cost"] = read_profile_cost(path)
    return result, path, log


def test_all13_complete_uncached_paths_counted_and_json_roundtrip_order_preserved(tmp_path):
    result, path, log = synthetic_run(tmp_path)
    assert len(log) == 13 * (20 + 3 * 20)
    assert len(result["rows"]) == 13 * 3 * 20
    p.verify_long_profile_journal(result, path)
    reloaded = json.loads(json.dumps(result, sort_keys=True))
    p.verify_long_profile_journal(reloaded, path)
    summary = p.summarize_long_profile(reloaded)
    assert len(summary["primary"]) == 13
    assert len(summary["per_observation"]) == 39
    assert len(summary["seed_equal_weight_summaries"]) == 4
    assert all(r["median"] == 1 and r["p95"] == 1 for r in summary["primary"])
    assert result["cost"]["attempts_by_pass"] == {"warmup": 260, "main": 780, "components": 0}
    corrupted = deepcopy(reloaded)
    corrupted["rows"].pop()
    with pytest.raises(ValueError, match="raw|durable"):
        p.verify_long_profile_journal(corrupted, path)
    with pytest.raises(ValueError, match="finite complete"):
        p.summarize_long_profile(corrupted)


@pytest.mark.parametrize("argument", ["failing", "bad_tokens"])
def test_failed_or_wrong_budget_call_is_retained_and_never_silently_retried(tmp_path, argument):
    with pytest.raises((ValueError, RuntimeError)):
        synthetic_run(tmp_path, **{argument: p.balanced_schedule(["obs2", "obs0", "obs1"])[0]["method_order"][0]})
    cost = read_profile_cost(tmp_path / "calls.jsonl")
    assert cost["failed"] == 1 and cost["sample_policy_forwards_attempted"] == 1
    assert cost["unknown_completion"] == 0


def test_offline_analysis_preserves_summary_across_sorted_json_serialization(tmp_path):
    result, journal, _ = synthetic_run(tmp_path)
    reg = registration()
    identity = {"version": p.LONG_PROFILE_VERSION, "test_opened": False,
        "registration_signature": json_signature(reg), "config": reg["profiling"],
        "cache_scope": "none", "future_head_deployed": False,
        "all_instances_share_one_loaded_base": True,
        "uncontended_gpu_attested_and_checked": True, "panel": {"fixture": True}}
    # Synthetic fixture stands in for a fully recorded run; no model or GPU.
    events = [json.loads(line) for line in journal.read_text().splitlines()]
    events[0]["identity"] = identity
    events[0]["identity_sha256"] = json_signature(identity)
    journal.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in events))
    result.update(provenance=identity, checkpoint_unchanged=True, synthetic=False,
        execution_wall_seconds_including_model_loading=1.0)
    summary = p.summarize_long_profile(result)
    assert list(result["observation_episodes"]) != sorted(result["observation_episodes"])
    atomic_json(tmp_path / "config.json", identity)
    atomic_json(tmp_path / "measurements.json", result)
    atomic_json(tmp_path / "summary.json", {**summary, "cost": result["cost"],
        "config_sha256": file_sha256(tmp_path / "config.json"),
        "measurements_sha256": file_sha256(tmp_path / "measurements.json"),
        "journal_sha256": file_sha256(journal)})
    before = {path.name: file_sha256(path) for path in tmp_path.iterdir() if path.is_file()}
    rebuilt = p.analyze_long_profile(tmp_path, reg)
    assert all(rebuilt[key] == value for key, value in summary.items())
    assert before == {path.name: file_sha256(path) for path in tmp_path.iterdir() if path.is_file()}


def test_gpu_attestation_accepts_only_own_allocated_device_process(monkeypatch):
    script = load_script(ROOT, "profile_long_future_observation_to_action")
    own = os.getpid()
    def response(value):
        monkeypatch.setattr(script.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout=value))
    response(f"GPU-mine, {own}\nGPU-other, 34567\n")
    assert script.uncontended_device()["other_compute_processes"] == 0
    response(f"GPU-mine, {own}\nGPU-mine, 34567\n")
    with pytest.raises(RuntimeError, match="shares"):
        script.uncontended_device()
    response("GPU-other, 34567\n")
    with pytest.raises(RuntimeError, match="unique allocated"):
        script.uncontended_device()


def test_collector_preparation_reads_only_frozen_development_evidence():
    script = load_script(ROOT, "collect_long_future_profile_panel")
    result = script.run(SimpleNamespace(registration=REGISTRATION, development_panel=PANEL,
        dense_reference=REFERENCE, prepare_only=True))
    assert result["gpu_calls"] == 0 and len(result["states"]) == 3
    assert result["new_success_trials"] is False and result["test_opened"] is False

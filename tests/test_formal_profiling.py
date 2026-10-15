"""Scientific boundary, temporal alignment, coverage and replay tests (CPU)."""
from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from cti_vla.data.experiment_protocol import signed_payload
from cti_vla.data.formal_initial_states import STATE_NAMESPACE, split_state_indices
from cti_vla.data.identity import file_sha256
from cti_vla.data.initial_states import initial_state_sha256
from cti_vla.evaluation import formal_profiling as p
from cti_vla.evaluation.formal_runtime import FormalRolloutPolicy
from cti_vla.evaluation.formal_trials import expected_method_ids
from cti_vla.evaluation.libero_runtime import PolicyChunk, run_episode
from cti_vla.evaluation.profiling import RawObservation, ProfileMethod, read_profile_cost
from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature

ROOT = Path(__file__).resolve().parents[1]


def registration():
    return json.loads((ROOT / "configs/experiments/formal_main_v2.json").read_text(encoding="utf-8"))


def raw(value):
    return {"agentview_image": np.full((4, 4, 3), value, dtype=np.uint8),
        "robot0_eye_in_hand_image": np.full((4, 4, 3), value, dtype=np.uint8),
        "robot0_eef_pos": np.full(3, value, dtype=np.float64),
        "robot0_eef_quat": np.array([0., 0., 0., 1.]), "robot0_gripper_qpos": np.zeros(2)}


class FakeEnv:
    def __init__(self, controls=19):
        self.controls, self.steps = controls, 0
        self.obs = raw(0)
    def reset(self):
        self.steps = 0
    def set_init_state(self, state):
        return self.obs
    def step(self, action):
        self.steps += 1
        # Deliberately mutate the same simulator buffers: capture must copy.
        self.obs["agentview_image"][:] = self.steps
        self.obs["robot0_eye_in_hand_image"][:] = self.steps
        self.obs["robot0_eef_pos"][:] = self.steps
        return self.obs, 0., self.steps == self.controls + 10, {}


def dense(observation, instruction):
    return PolicyChunk(np.zeros((8, 7)), np.zeros((8, 7)), {})


def development():
    tasks = [{"task_id": i, "task_name": f"task{i}"} for i in range(10)]
    rows = []
    for task in tasks:
        for index in split_state_indices(task["task_name"])[0]:
            values = [float(task["task_id"]), float(index)]
            rows.append(dict(**task, trial_id=f"libero_10:{task['task_name']}:state-{index:04d}:env-0",
                source_state_index=index, source_file=task["task_name"] + ".pruned_init", initial_state=values,
                initial_state_sha256=initial_state_sha256(values)))
    return signed_payload(dict(schema_version=2, suite="libero_10", split="development", environment_seed=0,
        task_catalog=tasks, states=list(reversed(rows)), source={"files": [dict(**t, count=50,
            source_file=t["task_name"] + ".pruned_init") for t in tasks]}), STATE_NAMESPACE)


def panel_fixture(tmp_path):
    dev, reg = development(), registration()
    provenance = dict(dense_identity={"method_id": "dense"}, checkpoint_unchanged=True)
    episodes = []
    for state in p.fixed_profile_states(dev):
        capture = p.CaptureControlObservations(FakeEnv())
        result = run_episode(capture, dense, "move object", state["initial_state"], max_steps=520)
        episodes.append(p.save_dense_collection(tmp_path / f"task{state['task_id']:02d}", state,
            "move object", result, capture.captured, provenance=provenance))
    p.write_profile_panel(tmp_path, dev, episodes, provenance=provenance, registration=reg)
    return dev, reg, provenance["dense_identity"]


def test_all_control_step_capture_uses_actual_preaction_observations_not_chunks():
    capture = p.CaptureControlObservations(FakeEnv(19))
    result = run_episode(capture, dense, "move", [0.], max_steps=520)
    assert result["control_steps"] == len(capture.captured) == 19
    assert [r["control_step"] for r in result["chunks"]] == [0, 8, 16]
    assert p.selected_control_steps(19) == [0, 9, 18]
    assert [int(capture.captured[i]["agentview_image"][0, 0, 0]) for i in (0, 9, 18)] == [10, 19, 28]
    assert int(capture.captured[0]["agentview_image"][0, 0, 0]) == 10
    with pytest.raises(ValueError, match="one trajectory"):
        capture.reset()


@pytest.mark.parametrize("count", [0, 1, 2, -1, 3.0, True])
def test_collection_never_pads_short_or_invalid_trajectory(count):
    with pytest.raises(ValueError, match="three distinct"):
        p.selected_control_steps(count)


def test_panel_roundtrip_all10_tasks_lowest_development_state(tmp_path):
    dev, reg, identity = panel_fixture(tmp_path)
    samples, receipt = p.load_profile_panel(tmp_path / "panel.json", development=dev, registration=reg, dense_identity=identity)
    assert len(samples) == 30 and receipt["episodes"] == 10 and not receipt["test_opened"]
    assert [s.phase for s in samples] == ["first", "middle", "last"] * 10
    assert [int(s.observation["robot0_eef_pos"][0]) for s in samples] == [10, 19, 28] * 10
    assert all(not a.flags.writeable for s in samples for a in s.observation.values())
    for i, state in enumerate(p.fixed_profile_states(dev)):
        assert state["source_state_index"] == min(r["source_state_index"] for r in dev["states"] if r["task_id"] == i)


@pytest.mark.parametrize("corruption", ["step", "hash", "state", "raw", "missing", "dense"])
def test_panel_rejects_resigned_misaligned_or_substituted_evidence(tmp_path, corruption):
    dev, reg, identity = panel_fixture(tmp_path)
    panelpath = tmp_path / "panel.json"
    panel = json.loads(panelpath.read_text(encoding="utf-8"))
    ref = panel["episodes"][0]["receipt"]
    receiptpath = tmp_path / ref["path"]
    receipt = json.loads(receiptpath.read_text(encoding="utf-8"))
    if corruption == "step":
        receipt["observations"][1]["control_step"] = 8
    elif corruption == "hash":
        receipt["all_control_observation_sha256"][8] = "f" * 64
    elif corruption == "state":
        receipt["state"]["source_state_index"] += 1
    elif corruption == "missing":
        receipt["observations"].pop()
    elif corruption == "dense":
        identity = {"method_id": "other dense version"}
    else:
        ar = receipt["observations"][0]["arrays"]
        ap = receiptpath.parent / ar["path"]
        with np.load(ap, allow_pickle=False) as archive:
            arrays = {k: archive[k].copy() for k in archive.files}
        arrays["robot0_eef_pos"] += 1
        np.savez(ap, **arrays)
        ar["sha256"] = file_sha256(ap)
    receipt = p._signed({k: v for k, v in receipt.items() if k != "content_signature"})
    atomic_json(receiptpath, receipt)
    ref["sha256"] = file_sha256(receiptpath)
    atomic_json(panelpath, p._signed({k: v for k, v in panel.items() if k != "content_signature"}))
    with pytest.raises(ValueError):
        p.load_profile_panel(panelpath, development=dev, registration=reg, dense_identity=identity)


def test_final_manifest_and_panel_fail_before_loading_development_or_weights(tmp_path, monkeypatch):
    monkeypatch.setattr(p, "validate_execution_manifest", lambda *a, **k: pytest.fail("called execution loader"))
    with pytest.raises(ValueError, match="only reads development"):
        p.validate_profile_manifest({"split": "final"}, registration())
    path = tmp_path / "panel.json"
    atomic_json(path, {"split": "final", "test_opened": False})
    with pytest.raises(ValueError, match="never reads final"):
        p.load_profile_panel(path, development=None, registration={}, dense_identity={})


@pytest.mark.parametrize("mutation", [None, "missing_instance", "other_checkpoint", "no_freeze"])
def test_profile_binds_complete22_methods_to_the88_success_freeze(mutation):
    from test_formal_deployment import freeze_fixture
    from cti_vla.evaluation.formal_trials import ENVIRONMENT
    reg, matrix = registration(), freeze_fixture()
    matrix["registration_sha256"] = json_signature(reg)
    manifest = dict(schema="formal_main_v2", kind="evaluation_execution", split="development", suite="libero_10",
        registration_sha256=json_signature(reg), environment={**ENVIRONMENT, "max_steps": 520},
        methods=[{"identity": deepcopy(r)} for r in matrix["instances"] if r["suite"] == "libero_10"])
    if mutation == "missing_instance":
        manifest["methods"].pop()
    elif mutation == "other_checkpoint":
        manifest["methods"][-1]["identity"]["checkpoint_sha256"] = "0" * 64
    elif mutation == "no_freeze":
        matrix = None
    if mutation:
        with pytest.raises(ValueError):
            p.validate_profile_manifest(manifest, reg, global_freeze=matrix)
    else:
        assert p.validate_profile_manifest(manifest, reg, global_freeze=matrix) == expected_method_ids()
        manifest["methods"] = manifest["methods"][:1]
        assert p.validate_profile_manifest(manifest, reg, collect=True) == ["dense"]


@pytest.mark.parametrize("suite", ["libero_10", "libero_spatial", "libero_object", "libero_goal"])
def test_collect_prepare_only_actual_registered_development_without_gpu(tmp_path, monkeypatch, suite):
    """Real development values, synthetic identity: CPU selection only, no weights."""
    from cti_vla.evaluation.future_profiling import load_script
    from cti_vla.evaluation.formal_trials import baseline_instance_identity, ENVIRONMENT
    cli, reg = load_script(ROOT, "profile_formal"), registration()
    identity = baseline_instance_identity(suite=suite, method="dense", visual_tokens=512,
        model_revision=reg["suites"][suite]["model_revision"], frozen_model_sha256="0" * 64,
        source_files={"synthetic-test-only": "1" * 64}, input_acceptance_sha256="2" * 64)
    manifest = dict(schema="formal_main_v2", kind="evaluation_execution", split="development", suite=suite,
        registration_sha256=json_signature(reg), environment={**ENVIRONMENT, "max_steps": p.FORMAL_SUITES[suite]["max_steps"]},
        methods=[{"identity": identity}])
    target = tmp_path / "synthetic_identity_manifest.json"
    atomic_json(target, manifest)
    monkeypatch.setattr(cli, "load_execution", lambda *a: pytest.fail("prepare-only loaded model identity"))
    result = cli.run(SimpleNamespace(command="collect", registration=ROOT / "configs/experiments/formal_main_v2.json",
        execution_manifest=target, global_freeze=None, development_panel=ROOT / reg["suites"][suite]["initial_states_root"] / "development.json",
        prepare_only=True))
    assert result["observations"] == 30 and len(result["fixed_state_ids"]) == 10
    assert result["gpu_calls"] == 0 and result["weights_validated"] is False and result["test_opened"] is False


def test_schedule_rotates_one_seeded_permutation_preserves_common_observation_order():
    ids = ["z-first", "a-middle", "q-last"]
    schedule = p.balanced_schedule(ids)
    assert len(schedule) == 20 and schedule == p.balanced_schedule(ids)
    for r, block in enumerate(schedule):
        assert block["observation_order"] == ids
        base = schedule[0]["method_order"]
        assert block["method_order"] == base[r:] + base[:r]
    for mid in expected_method_ids():
        counts = [sum(b["method_order"][i] == mid for b in schedule) for i in range(22)]
        assert max(counts) == 1 and min(counts) == 0 and sum(counts) == 20


class Clock:
    def __init__(self):
        self.value = 0
    def timer(self):
        self.value += 1000000
        return self.value
    def synchronize(self):
        pass
    def reset_peak(self):
        pass
    def memory(self):
        return {"allocated": 0}
    def event(self):
        return None


def method_identity(mid):
    if mid == "dense":
        arm, budget, seed = "dense", 512, None
    elif mid.startswith("uniform"):
        arm, budget, seed = "uniform", int(mid[7:]), None
    else:
        arm, budget, seed = mid[0], int(mid[1:].split("_")[0]), int(mid.split("seed")[1])
    return dict(method_id=mid, method=arm, visual_tokens=budget, suite="libero_10", training_seed=seed,
        checkpoint_sha256="a" * 64, pair_id="b" * 64)


def synthetic_run(tmp_path, pass_name="full", failure=None, bad_budget=False):
    clock, events, factories, calls = Clock(), [], {}, []
    for mid in expected_method_ids():
        identity = method_identity(mid)
        @contextmanager
        def factory(mid=mid, identity=identity):
            current = None
            def set_context(context):
                nonlocal current
                current = context
            def policy(observation, instruction):
                assert (current is None) == (pass_name == "full")
                calls.append((mid, instruction))
                if failure == mid:
                    raise RuntimeError("synthetic failed attempt")
                if current:
                    for phase in p.PHASES:
                        with current(phase):
                            pass
                metadata = dict(schema="formal_main_v2", suite="libero_10", method=identity["method"],
                    visual_tokens=identity["visual_tokens"] + int(bad_budget), policy_calls=1, vision_calls=1, packing_calls=1,
                    scorer_calls=int(identity["method"] in ("A", "B")), future_head_calls=0,
                    language_cache="disabled", diagnostic_indices_recorded=False, training_seed=identity["training_seed"],
                    selector_checkpoint_sha256=identity["checkpoint_sha256"], pair_id=identity["pair_id"])
                if len(calls) == 51:
                    clock.value += 9999000000  # One real-looking spike; never filter it.
                return PolicyChunk(np.zeros((8, 7)), np.zeros((8, 7)), metadata)
            yield ProfileMethod(policy, dict(identity=identity, cache_scope="none", instruction_cache_enabled=False,
                future_head_deployed=False), set_context)
        factories[mid] = factory
    samples = [RawObservation(oid, "episode0", "task0", oid, phase, raw(i))
        for i, (oid, phase) in enumerate(zip(("z-first", "a-middle", "q-last"), ("first", "middle", "last")))]
    identity = {"synthetic": True}
    events.append(dict(event="identity", identity=identity, identity_sha256=json_signature(identity)))
    path = tmp_path / "calls.jsonl"
    try:
        result = p.profile_formal_methods(samples, factories, pass_name=pass_name, clock=clock,
            emit=events.append, timer=clock.timer, synthetic=True)
    finally:
        path.write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in events), encoding="utf-8")
    result["cost"] = read_profile_cost(path)
    return result, path, calls


@pytest.mark.parametrize("pass_name", ["full", "components"])
def test_full_and_independent_components_all22_counts_raw_journal_json_roundtrip(tmp_path, pass_name):
    result, path, calls = synthetic_run(tmp_path, pass_name)
    assert len(calls) == 22 * (50 + 20 * 3)
    assert len(result["rows"]) == 22 * 20 * 3
    assert max(r["elapsed_ms"] for r in result["rows"]) > 9999
    p.verify_profile_journal(result, path)
    summary = p.summarize_formal_profile(result)
    roundtrip = json.loads(json.dumps(result, sort_keys=True))
    p.verify_profile_journal(roundtrip, path)
    assert summary == p.summarize_formal_profile(roundtrip)
    assert summary["primary_inference_latency"] is (pass_name == "full")
    assert all(r["count"] == 60 for r in summary["primary"])
    assert len(summary["seed_equal_weight_summaries"]) == 6
    assert bool(summary["components"]) is (pass_name == "components")


@pytest.mark.parametrize("change", ["dropped_spike", "duplicate", "warmup_reordered"])
def test_journal_rejects_filtered_duplicated_or_changed_warmup(tmp_path, change):
    result, path, _ = synthetic_run(tmp_path)
    if change == "dropped_spike":
        result["rows"] = [r for r in result["rows"] if r["elapsed_ms"] < 9999]
    elif change == "duplicate":
        result["rows"][1] = result["rows"][0]
    else:
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        for e in events:
            if e.get("call_id") == 0:
                e["observation_id"] = "a-middle"
        path.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    with pytest.raises(ValueError):
        p.verify_profile_journal(result, path)


def test_failed_attempt_stays_charged_and_does_not_continue(tmp_path):
    first = p.balanced_schedule(["x"])[0]["method_order"][0]
    with pytest.raises(RuntimeError, match="synthetic failed"):
        synthetic_run(tmp_path, failure=first)
    cost = read_profile_cost(tmp_path / "calls.jsonl")
    assert cost["api_calls_attempted"] == cost["failed"] == 1
    assert cost["completed"] == cost["unknown_completion"] == 0


def test_wrong_hard_budget_rejected_and_charged(tmp_path):
    with pytest.raises(ValueError, match="boundary"):
        synthetic_run(tmp_path, bad_budget=True)
    assert read_profile_cost(tmp_path / "calls.jsonl")["failed"] == 1


def test_runtime_component_instrumentation_keeps_shared_forward_and_removes_hook():
    backbone = torch.nn.Linear(1, 1)
    policy = FormalRolloutPolicy.__new__(FormalRolloutPolicy)
    clock, recorder = Clock(), None
    calls, hooks_seen = [], []
    def shared(*args, **kwargs):
        hooks_seen.append(len(backbone._forward_pre_hooks))
        calls.append(kwargs)
        return backbone(torch.ones(1))
    policy.token_policy = SimpleNamespace(forward_from_full_tokens=shared,
        prefix_adapter=SimpleNamespace(language_backbone=backbone))
    inputs = dict(normalized_proprio=None, input_ids=None, attention_mask=None)
    policy.component_timing = False
    baseline = policy._policy_forward(None, inputs, None)
    recorder = p.ComponentRecorder(clock, clock.timer)
    policy.component_timing, policy.stage_context = True, recorder.phase
    # _policy_forward owns only these two middle regions.
    observed = []
    @contextmanager
    def record(name):
        observed.append(("start", name))
        yield
        observed.append(("end", name))
    policy.stage_context = record
    instrumented = policy._policy_forward(None, inputs, None)
    assert torch.equal(baseline, instrumented)
    assert calls[0] == calls[1] and hooks_seen == [0, 1]
    assert observed == [("start", "packing"), ("end", "packing"), ("start", "llm_action"), ("end", "llm_action")]
    assert not backbone._forward_pre_hooks
    def fail(*a, **k):
        raise RuntimeError("packing failure")
    policy.token_policy.forward_from_full_tokens = fail
    with pytest.raises(RuntimeError):
        policy._policy_forward(None, inputs, None)
    assert not backbone._forward_pre_hooks


def test_component_recorder_rejects_nested_missing_and_unregistered_phases():
    clock = Clock()
    rec = p.ComponentRecorder(clock, clock.timer)
    with rec.phase("preprocess"):
        with pytest.raises(ValueError):
            with rec.phase("vision"):
                pass
    with pytest.raises(ValueError):
        rec.report(10.)
    with pytest.raises(ValueError):
        with rec.phase("policy"):
            pass

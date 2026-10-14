from copy import deepcopy
import importlib.util
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image
import pytest
import torch

from cti_vla.evaluation import libero_runtime as runtime


ROOT = Path(__file__).resolve().parents[1]


def observation():
    return {"agentview_image": np.arange(6 * 7 * 3, dtype=np.uint8).reshape(6, 7, 3),
            "robot0_eye_in_hand_image": np.full((6, 7, 3), 150, dtype=np.uint8),
            "robot0_eef_pos": np.array([0.1, 0.2, 0.3]), "robot0_eef_quat": np.array([0., 0., 0., 1.]),
            "robot0_gripper_qpos": np.array([0.02, -0.02])}


def stats():
    return {"q01": [-0.7] * 8, "q99": [0.9] * 8, "mask": [True] * 7 + [False]}


def test_quaternion_convention_and_no_mutation():
    quat = np.array([0., 0., np.sqrt(0.5), np.sqrt(0.5)])
    np.testing.assert_allclose(runtime.quaternion_to_axis_angle(quat), [0, 0, np.pi / 2])
    invalid_w = np.array([0., 0., 0., 1.0000001])
    before = invalid_w.copy()
    np.testing.assert_equal(runtime.quaternion_to_axis_angle(invalid_w), np.zeros(3))
    np.testing.assert_equal(invalid_w, before)
    np.testing.assert_allclose(runtime.raw_proprio_from_observation(observation()), [.1, .2, .3, 0, 0, 0, .02, -.02])


def test_action_postprocessing_preserves_arm_and_binarizes_exactly_once():
    actions = np.zeros((8, 7))
    actions[:, 0] = np.arange(8) / 10
    actions[:, -1] = [-.5, 0, .49, .5, .51, 1, 1.5, .2]
    before = actions.copy()
    actual = runtime.postprocess_actions(actions)
    np.testing.assert_equal(actual[:, -1], [1, 1, 1, 0, -1, -1, -1, 1])
    np.testing.assert_equal(actual[:, :-1], actions[:, :-1])
    np.testing.assert_equal(actions, before)
    with pytest.raises(ValueError):
        runtime.postprocess_actions(np.full((8, 7), np.nan))


def test_proprio_dtype_mask_and_clip_match_official_arithmetic():
    raw = np.array([-.8, -.7, -.2, 0, .5, .9, 2, 2], dtype=np.float32)
    bounds = stats()
    low, high = np.array(bounds["q01"]), np.array(bounds["q99"])
    expected = np.clip(np.where(bounds["mask"], 2 * (raw - low) / (high - low + 1e-8) - 1, raw), -1, 1)
    np.testing.assert_array_equal(runtime.normalize_eval_proprio(raw, bounds), expected)
    assert runtime.normalize_eval_proprio(raw, bounds).dtype == np.float64
    with pytest.raises(ValueError):
        runtime.normalize_eval_proprio(np.zeros(7), bounds)


def test_uniform_grid_uses_both_camera_axes_and_original_order():
    indices = runtime.uniform128_indices()
    assert indices.shape == (128,) and np.all(np.diff(indices) > 0)
    np.testing.assert_array_equal(indices[64:], indices[:64] + 256)
    assert set(indices[:64] % 16) == set(range(0, 16, 2))
    assert set(indices[:64] // 16) == set(range(0, 16, 2))


def test_camera_simulation_rotates_once_rlds_never_again(monkeypatch):
    captured = []
    monkeypatch.setattr(runtime, "resize_image_for_policy", lambda image: captured.append(image.copy()) or image)
    monkeypatch.setattr(runtime, "center_crop_image", Image.fromarray)
    image = observation()["agentview_image"]
    runtime.process_camera(image)
    runtime.process_camera(image, already_rotated=True)
    np.testing.assert_array_equal(captured[0], image[::-1, ::-1])
    np.testing.assert_array_equal(captured[1], image)


def test_official_cpu_image_reference_when_tensorflow_available():
    pytest.importorskip("tensorflow")
    if not (ROOT / "external/openvla-oft").exists():
        pytest.skip("pinned reference checkout unavailable")
    reference = runtime.load_official_reference_functions(ROOT / "external/openvla-oft")
    obs = observation()
    rng = np.random.default_rng(17)
    obs["agentview_image"] = rng.integers(0, 256, (256, 256, 3), dtype=np.uint8)
    obs["robot0_eye_in_hand_image"] = rng.integers(0, 256, (256, 256, 3), dtype=np.uint8)
    checked = runtime.verify_observation_preprocessing(obs, stats(), reference)
    assert checked == {"images_equal": True, "raw_proprio_equal": True, "normalized_proprio_max_abs_error": 0.0}
    assert not runtime._tensorflow().config.get_visible_devices("GPU")


def test_prepared_dual_views_prompt_and_proprio_conversion(monkeypatch):
    seen = []
    def processor(prompt, image, return_tensors):
        seen.append(prompt)
        pixels = torch.full((1, 6, 224, 224), float(np.asarray(image)[0, 0, 0]))
        return {"input_ids": torch.tensor([[1, 7, 9]]), "attention_mask": torch.ones(1, 3, dtype=torch.long), "pixel_values": pixels}
    rotations = []
    def camera(image, *, already_rotated=False):
        rotations.append(already_rotated)
        return Image.fromarray(np.broadcast_to(image[:1, :1], (224, 224, 3)).copy())
    monkeypatch.setattr(runtime, "process_camera", camera)
    obs = observation()
    result = runtime.prepare_observation_inputs(obs, "Pick Bowl", processor, stats(), device="cpu", dtype=torch.bfloat16)
    assert result["pixel_values"].shape == (1, 12, 224, 224)
    assert result["pixel_values"][0, 6, 0, 0] == 150
    assert rotations == [False, False]
    assert seen == ["In: What action should the robot take to pick bowl?\nOut:"] * 2
    expected = torch.tensor(runtime.normalize_eval_proprio(runtime.raw_proprio_from_observation(obs), stats()), dtype=torch.float32).to(torch.bfloat16)[None]
    assert torch.equal(result["normalized_proprio"], expected)
    stream = BytesIO()
    Image.fromarray(obs["agentview_image"]).save(stream, format="PNG")
    episode = SimpleNamespace(num_steps=1, images=[stream.getvalue()], wrist_images=[stream.getvalue()],
                              instructions=["Pick Bowl"], proprio=[np.zeros(8)])
    runtime.prepare_rlds_eval_inputs(episode, 0, processor, stats(), device="cpu", dtype=torch.float32)
    assert rotations[-2:] == [True, True]


class FakeEnv:
    def __init__(self, done_at=None, error_at=None):
        self.actions = []
        self.done_at, self.error_at = done_at, error_at
        self.resets = 0

    def reset(self):
        self.resets += 1
        self.actions = []

    def set_init_state(self, value):
        self.initial_state = value.copy()
        return observation()

    def step(self, action):
        if self.error_at == len(self.actions):
            raise RuntimeError("renderer disconnected")
        self.actions.append(action)
        return observation(), 0, len(self.actions) == self.done_at, {}


class FakePolicy:
    def __init__(self):
        self.calls, self.resets = 0, 0

    def reset(self):
        self.calls = 0
        self.resets += 1

    def __call__(self, observation, instruction):
        self.calls += 1
        actions = np.zeros((8, 7))
        actions[:, 0] = np.arange(8) / 10
        actions[:, -1] = -1
        return runtime.PolicyChunk(actions, actions, {"test": True})


def test_chunk8_queue_wait_steps_and_horizon():
    env, policy = FakeEnv(), FakePolicy()
    row = runtime.run_episode(env, policy, "task", [1, 2], max_steps=17)
    assert row["status"] == "completed" and not row["success"]
    assert row["wait_steps"] == 10 and row["control_steps"] == 17
    assert row["policy_calls"] == 3 and policy.calls == 3
    assert [chunk["control_step"] for chunk in row["chunks"]] == [0, 8, 16]
    np.testing.assert_array_equal(env.actions[:10], [runtime.DUMMY_ACTION] * 10)
    np.testing.assert_allclose(np.array(env.actions[10:])[:, 0], list(np.arange(8) / 10) * 2 + [0])
    assert env.resets == 1 and policy.resets == 1
    runtime.run_episode(env, policy, "task", [3, 4], max_steps=1)
    assert policy.calls == 1 and policy.resets == 2


def test_success_ends_mid_chunk_without_extra_calls():
    result = runtime.run_episode(FakeEnv(done_at=13), FakePolicy(), "task", [1], max_steps=220)
    assert result["success"] and result["control_steps"] == 3 and result["policy_calls"] == 1
    assert len(result["executed_actions"]) == 3


@pytest.mark.parametrize("kind", ["nan", "out_of_bounds", "exception"])
def test_method_errors_are_recorded_without_executing_invalid_action(kind):
    def broken(obs, instruction):
        if kind == "exception":
            raise RuntimeError("model OOM")
        actions = np.zeros((8, 7))
        actions[0, 0] = np.nan if kind == "nan" else 2
        return runtime.PolicyChunk(actions, actions, {})
    result = runtime.run_episode(FakeEnv(), broken, "task", [1], wait_steps=0)
    assert result["status"] == "policy_error" and not result["success"]
    assert result["policy_calls"] == 1 and result["control_steps"] == 0


def test_environment_failure_remains_retryable_infrastructure():
    result = runtime.run_episode(FakeEnv(error_at=0), FakePolicy(), "task", [1])
    assert result["status"] == "infrastructure_error" and result["policy_calls"] == 0


def test_watchdog_rejects_late_return(monkeypatch):
    times = iter([0., 1., 62., 63.])
    monkeypatch.setattr(runtime.time, "perf_counter", lambda: next(times))
    result = runtime.run_episode(FakeEnv(), FakePolicy(), "task", [1], wait_steps=0)
    assert result["status"] == "policy_error" and result["termination"] == "TimeoutError"
    assert result["control_steps"] == 0


def test_ledger_resumes_infrastructure_but_never_repeats_policy_failure(tmp_path):
    path = tmp_path / "trials.jsonl"
    ledger = runtime.TrialLedger(path, run_signature="frozen")
    ledger.append({"trial_id": "a", "event": "start"})
    ledger.append({"trial_id": "a", "event": "result", "status": "infrastructure_error"})
    assert not ledger.completed()
    ledger.append({"trial_id": "a", "event": "result", "status": "policy_error"})
    resumed = runtime.TrialLedger(path, run_signature="frozen")
    assert set(resumed.completed()) == {"a"}
    with pytest.raises(ValueError, match="twice"):
        resumed.append({"trial_id": "a", "event": "result", "status": "completed"})
    with pytest.raises(ValueError, match="different frozen"):
        runtime.TrialLedger(path, run_signature="changed")


def test_ledger_preserves_interrupted_tail_and_fails_interior_corruption(tmp_path):
    path = tmp_path / "trials.jsonl"
    ledger = runtime.TrialLedger(path, run_signature="a")
    ledger.append({"trial_id": "x", "event": "result", "status": "completed"})
    with path.open("ab") as stream:
        stream.write(b'{"partial":')
    resumed = runtime.TrialLedger(path, run_signature="a")
    assert Path(resumed.recovered_tail).read_bytes() == b'{"partial":'
    assert set(resumed.completed()) == {"x"}
    resumed.append({"trial_id": "y", "event": "result", "status": "completed"})
    assert len(runtime.TrialLedger(path, run_signature="a").completed()) == 2
    path.write_bytes(b"broken\n" + path.read_bytes())
    with pytest.raises(ValueError, match="corrupt ledger"):
        runtime.TrialLedger(path, run_signature="a")


def test_dense_comparison_reports_first_action_or_observation_divergence():
    official = runtime.run_episode(FakeEnv(), FakePolicy(), "task", [1], max_steps=9)
    assert runtime.compare_dense_trials(official, deepcopy(official))["passed"]
    changed = deepcopy(official)
    changed["chunks"][0]["normalized_actions"][0][0] += .003
    comparison = runtime.compare_dense_trials(official, changed)
    assert not comparison["passed"] and comparison["first_divergence"]["chunk"] == 0
    changed = deepcopy(official)
    changed["chunks"][1]["observation_sha256"] = "drift"
    comparison = runtime.compare_dense_trials(official, changed)
    assert not comparison["passed"] and not comparison["observations_equal"]


def test_real_g0_initial_state_panel_disjointness_and_summary_is_not_full_g0_gate(tmp_path):
    spec = importlib.util.spec_from_file_location("eval_libero_test", ROOT / "scripts/eval_libero.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    folder = ROOT / "configs/manifests/spatial_initial_states_v1"
    panel, split_check = module.load_development_panel(folder / "g0_development_15.json", folder / "init_states_test.json")
    assert len(panel["states"]) == 15 and split_check["overlap"] == 0
    ledger = runtime.TrialLedger(tmp_path / "trials.jsonl", run_signature="test")
    report = module.summarize(ledger, panel, {}, split_check, True)
    assert report["stage"] == "g0_closed_loop" and report["status"] != "passed"
    assert report["closed_loop"]["expected_trials"] == 45


def test_source_archive_inventory_verifies_every_listed_file(tmp_path):
    spec = importlib.util.spec_from_file_location("eval_libero_source_test", ROOT / "scripts/eval_libero.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path / "official.py"
    source.write_text("def audited(): return 1\n", encoding="utf-8")
    revision, archive_hash = "a" * 40, "b" * 64
    (tmp_path / "SOURCE_REVISION.json").write_text(json.dumps({"revision": revision, "archive_sha256": archive_hash}))
    (tmp_path / "SOURCE_FILES.json").write_text(json.dumps({"revision": revision, "archive_sha256": archive_hash,
                                                          "files": {"official.py": module.sha256(source)}}))
    assert module.verify_source_checkout(tmp_path, revision)["file_count"] == 1
    source.write_text("def audited(): return 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="file verification failed"):
        module.verify_source_checkout(tmp_path, revision)

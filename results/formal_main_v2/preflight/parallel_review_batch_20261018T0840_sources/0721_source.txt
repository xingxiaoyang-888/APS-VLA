"""G1-F development-only raw panel at fixed control steps, never final frames.

The measured runner is shared with profiling.py. Collection/NPZ loading is
outside that boundary; all methods receive the same immutable raw arrays.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path

import numpy as np

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation import libero_runtime
from cti_vla.evaluation.future_trials import load_future_development_panel
from cti_vla.evaluation.profiling import RAW_KEYS, RawObservation
from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature

FUTURE_PANEL_VERSION = "g1f-development-dense-control-0-80-160-v1"
CONTROL_STEPS = (0, 80, 160)


def load_script(root, name):
    spec = importlib.util.spec_from_file_location("cti_future_" + name, Path(root) / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def profile_states(panel):
    """First means the lowest frozen source-state index, not first success."""
    return [min((row for row in panel["states"] if row["task_id"] == task),
                key=lambda row: row["source_state_index"]) for task in (0, 3, 5)]


@dataclass(frozen=True)
class FixedStepObservation:
    observation_id: str
    episode_id: str
    task_name: str
    instruction: str
    control_step: int
    observation: dict

    def __post_init__(self):
        if type(self.control_step) is not int or self.control_step not in CONTROL_STEPS:
            raise ValueError("G1-F panel accepts only actual control steps0,80,160")
        # Reuse raw shape/dtype checks without mislabelling step80 as a midpoint.
        RawObservation(self.observation_id, self.episode_id, self.task_name,
                       self.instruction, "first", self.observation)

    @property
    def phase(self):
        return f"control_step_{self.control_step}"


class CaptureDense:
    """Observe the shared chunk8 rollout; no extra model calls or final fill."""
    def __init__(self, policy):
        self.policy = policy
        self.reset()

    def reset(self):
        self.calls, self.captured = 0, {}
        if hasattr(self.policy, "reset"):
            self.policy.reset()

    def __call__(self, observation, instruction):
        control_step = self.calls * 8
        self.calls += 1
        if control_step in CONTROL_STEPS:
            self.captured[control_step] = {key: np.asarray(observation[key]).copy() for key in RAW_KEYS}
        return self.policy(observation, instruction)


def save_dense_episode(directory, state, instruction, result, captured, *, provenance):
    """Save a completed trajectory and its exact requested raw observations."""
    if result.get("status") != "completed":
        raise ValueError("failed dense trajectory cannot become a latency panel")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    chunks = {row["control_step"]: row for row in result["chunks"]}
    expected = set(CONTROL_STEPS) & set(chunks)
    if set(captured) != expected:
        raise ValueError("captured steps differ from the actual dense query trace")
    records = []
    for step in sorted(expected):
        arrays = captured[step]
        sample = FixedStepObservation(f"{state['trial_id']}:control_step_{step}", state["trial_id"],
            state["task_name"], instruction, step, arrays)
        digest = libero_runtime._observation_hash(arrays)
        if digest != chunks[step]["observation_sha256"]:
            raise ValueError("captured raw bytes differ from the dense policy input")
        path = directory / f"control_step_{step:03d}.npz"
        np.savez(path, **sample.observation)
        records.append({"observation_id": sample.observation_id, "control_step": step,
            "query_index": step // 8, "raw_observation_sha256": digest,
            "arrays": {"path": path.name, "sha256": file_sha256(path)}})
    receipt = {**result, "method": "dense", "state_trial_id": state["trial_id"],
        "task_id": state["task_id"], "task_name": state["task_name"], "instruction": instruction,
        "initial_state_sha256": state["initial_state_sha256"], "source_state_index": state["source_state_index"],
        "requested_control_steps": list(CONTROL_STEPS), "observations": records,
        "missing": [{"control_step": step, "reason": "dense_trajectory_ended_before_query", "termination": result["termination"]}
                    for step in CONTROL_STEPS if step not in expected], "provenance": dict(provenance)}
    atomic_json(directory / "dense_receipt.json", receipt)
    return {"state_trial_id": state["trial_id"], "task_id": state["task_id"],
        "receipt": {"path": directory.name + "/dense_receipt.json", "sha256": file_sha256(directory / "dense_receipt.json")}}


def write_future_panel(directory, development_panel, episodes, *, provenance):
    directory = Path(directory)
    atomic_json(directory / "development_panel.json", development_panel)
    payload = {"version": FUTURE_PANEL_VERSION, "split": "development", "test_opened": False,
        "source_kind": "simulator_raw", "arrays_preprocessed": False, "requested_control_steps": list(CONTROL_STEPS),
        "selection_rule": "task0,3,5 lowest existing development source_state_index; no resampling or final-frame substitution",
        "development_panel": {"path": "development_panel.json", "sha256": file_sha256(directory / "development_panel.json")},
        "episodes": episodes, "provenance": dict(provenance)}
    payload["content_signature"] = json_signature(payload)
    atomic_json(directory / "panel.json", payload)
    return payload


def _reference(root, reference):
    path = (root / reference["path"]).resolve()
    if root.resolve() not in path.parents or file_sha256(path) != reference["sha256"]:
        raise ValueError("G1-F panel reference must have matching bytes inside its archive")
    return path


def load_future_raw_panel(path, *, development_path, g0_panel_path, expected_versions=None):
    """Validate exact first-dev-state trajectories and all present/missing steps."""
    path = Path(path)
    panel = json.loads(path.read_text(encoding="utf-8"))
    # Reject test before opening any referenced artifact or array.
    if panel.get("split") != "development" or panel.get("test_opened") is not False:
        raise ValueError("G1-F latency never reads final-test panels")
    if panel.get("version") != FUTURE_PANEL_VERSION or panel.get("content_signature") != json_signature({k: v for k, v in panel.items() if k != "content_signature"}):
        raise ValueError("G1-F latency panel signature/version mismatch")
    if panel.get("source_kind") != "simulator_raw" or panel.get("arrays_preprocessed") is not False or panel.get("requested_control_steps") != list(CONTROL_STEPS):
        raise ValueError("G1-F latency requires raw simulator inputs at fixed control steps")
    provenance = panel["provenance"]
    if provenance.get("checkpoint_unchanged") is not True or any(provenance.get(k) != v for k, v in (expected_versions or {}).items()):
        raise ValueError("dense panel checkpoint/runtime identity mismatch")
    authoritative = load_future_development_panel(development_path, g0_panel_path)
    stored = json.loads(_reference(path.parent, panel["development_panel"]).read_text(encoding="utf-8"))
    if stored != authoritative:
        raise ValueError("dense panel development states differ from the frozen source")
    states = {s["trial_id"]: s for s in profile_states(authoritative)}
    episodes = panel["episodes"]
    if len(episodes) != 3 or {r["state_trial_id"] for r in episodes} != set(states):
        raise ValueError("dense panel must contain exactly the predeclared three development states")
    samples, missing, costs = [], [], []
    for row in episodes:
        state = states[row["state_trial_id"]]
        receipt_path = _reference(path.parent, row["receipt"])
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        expected = {"method": "dense", "status": "completed", "state_trial_id": state["trial_id"],
            "task_id": state["task_id"], "task_name": state["task_name"], "initial_state_sha256": state["initial_state_sha256"],
            "source_state_index": state["source_state_index"], "requested_control_steps": list(CONTROL_STEPS)}
        if row["task_id"] != state["task_id"] or any(receipt.get(k) != v for k, v in expected.items()) or receipt.get("provenance") != provenance:
            raise ValueError("dense receipt does not match the paired development source/runtime")
        steps, chunks = receipt["control_steps"], receipt["chunks"]
        if type(steps) is not int or not 1 <= steps <= 220 or receipt["wait_steps"] != 10 or receipt["policy_calls"] != len(chunks) or [c["control_step"] for c in chunks] != list(range(0, steps, 8)):
            raise ValueError("dense receipt violates the chunk8 trajectory query schedule")
        if receipt["termination"] not in ("task_horizon", "environment_success") or receipt["success"] != (receipt["termination"] == "environment_success") or (receipt["termination"] == "task_horizon" and steps != 220):
            raise ValueError("dense missing observations require an actual terminal trajectory")
        present = [step for step in CONTROL_STEPS if step < steps]
        records = receipt["observations"]
        expected_missing = [{"control_step": step, "reason": "dense_trajectory_ended_before_query", "termination": receipt["termination"]}
                            for step in CONTROL_STEPS if step not in present]
        if [r["control_step"] for r in records] != present or receipt["missing"] != expected_missing:
            raise ValueError("dense panel omitted or substituted fixed-step observations")
        for record in records:
            step = record["control_step"]
            if record["query_index"] != step // 8 or record["observation_id"] != f"{state['trial_id']}:control_step_{step}":
                raise ValueError("dense observation query identity mismatch")
            with np.load(_reference(receipt_path.parent, record["arrays"]), allow_pickle=False) as archive:
                arrays = {key: archive[key].copy() for key in archive.files}
            sample = FixedStepObservation(record["observation_id"], state["trial_id"], state["task_name"], receipt["instruction"], step, arrays)
            if libero_runtime._observation_hash(arrays) != record["raw_observation_sha256"] or record["raw_observation_sha256"] != chunks[step // 8]["observation_sha256"]:
                raise ValueError("raw panel differs from actual dense policy input bytes")
            samples.append(sample)
        missing.extend({"state_trial_id": state["trial_id"], **m} for m in expected_missing)
        costs.append({"state_trial_id": state["trial_id"], "policy_calls": receipt["policy_calls"], "wall_seconds": receipt["wall_seconds"]})
    return samples, {"panel_sha256": file_sha256(path), "content_signature": panel["content_signature"],
        "version": FUTURE_PANEL_VERSION, "split": "development", "test_opened": False,
        "observations": len(samples), "target_observations": 9, "episodes": 3, "missing": missing,
        "collection_cost_excluded": costs, "provenance": provenance}


def validate_new_output_paths(*, project_root, source_root, output, cache, weight_roots):
    project, source, output = Path(project_root).resolve(), Path(source_root).resolve(), Path(output).resolve()
    if project != source and project not in source.parents:
        raise ValueError("source snapshot must belong to the declared project")
    for target in (output, Path(cache).resolve()):
        if project not in target.parents or (source != project and (target == source or source in target.parents)):
            raise ValueError("artifacts/cache must remain in project outside immutable source snapshot")
        if any(target == Path(root).resolve() or Path(root).resolve() in target.parents for root in weight_roots):
            raise ValueError("artifacts/cache must remain outside immutable weight directories")
    if output.exists():
        raise FileExistsError("use a new output; retain prior/failed collection or timing evidence")

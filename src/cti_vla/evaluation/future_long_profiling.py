"""Registered Long raw-observation timing, independent of old Spatial timing.

The panel consists only of fixed development observations. Old 128-token
selectors execute their original frozen runtime and hard selector; no receipt
source check is weakened to load an old selector under new training code.
"""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
import importlib.util
import json
import random
import sys
import threading
import time
from pathlib import Path

import numpy as np

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation import libero_runtime
from cti_vla.evaluation.future_profiling import _reference, profile_states
from cti_vla.evaluation.profiling import (RAW_KEYS, RawObservation, _latency_stats,
    _validate_chunk, observation_signature, read_profile_cost)
from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature

LONG_PROFILE_VERSION = "long-o2a-13-deployments-v1"
LONG_PANEL_VERSION = "long-dense-preregistered-control-steps-v1"
LONG_METHODS = ("dense", *[f"{arm}{budget}_seed{seed}" for budget in (128, 64)
    for seed in (17, 23, 41) for arm in ("A", "B")])
LONG_CONTROL_STEPS = {"0": [0, 184, 336], "3": [0, 104, 192], "5": [0, 72, 128]}
_MODULE_LOCK = threading.Lock()


def profile_registration(registration):
    value = registration["profiling"]
    expected = {"version": LONG_PROFILE_VERSION, "warmup_calls": 20, "repeats": 20,
        "component_repeats": 0, "order_seed": 1017, "max_pipeline_calls": 2600,
        "task_control_steps": LONG_CONTROL_STEPS, "method_names": list(LONG_METHODS),
        "source_dense_trials_sha256": "ff68b045e16c7e96ee2205471112e68c8596526b32ebef753db653a46e0bcad0"}
    if any(value.get(key) != item for key, item in expected.items()):
        raise ValueError("Long profiling differs from the bounded preregistration")
    return value


def fixed_long_profile_states(panel, dense_reference, registration):
    """Derive the preselected times from already archived dense trajectories."""
    from cti_vla.evaluation.future_dense_reuse import validate_dense_reference
    validate_dense_reference(dense_reference, panel)
    spec = profile_registration(registration)
    dense = {r["state_trial_id"]: r for r in dense_reference["dense_results"]}
    selected = []
    for state in profile_states(panel):
        old = dense[state["trial_id"]]
        length = old["control_steps"]
        steps = [int((length - 1) * fraction // 8) * 8 for fraction in (0, .5, .9)]
        if steps != spec["task_control_steps"][str(state["task_id"])]:
            raise ValueError("registered Long times do not match original dense trajectory lengths")
        selected.append({**state, "requested_control_steps": steps,
            "reference_control_steps": length,
            "reference_initial_observation_sha256": old["initial_observation_sha256"]})
    return selected


@dataclass(frozen=True)
class LongFixedObservation:
    observation_id: str
    episode_id: str
    task_name: str
    instruction: str
    control_step: int
    observation: dict

    def __post_init__(self):
        if type(self.control_step) is not int or self.control_step < 0 or self.control_step % 8:
            raise ValueError("Long profiling requires actual chunk8 query boundaries")
        RawObservation(self.observation_id, self.episode_id, self.task_name,
            self.instruction, "first", self.observation)

    @property
    def phase(self):
        return f"control_step_{self.control_step}"


class CaptureLongDense:
    """Copies only the registered raw queries; early termination is not filled."""
    def __init__(self, policy, steps):
        self.policy, self.steps = policy, tuple(steps)
        if len(set(self.steps)) != 3 or self.steps[0] != 0 or any(s < 0 or s % 8 for s in self.steps):
            raise ValueError("three distinct registered chunk boundaries are required")
        self.reset()

    def reset(self):
        self.calls, self.captured = 0, {}
        if hasattr(self.policy, "reset"):
            self.policy.reset()

    def __call__(self, observation, instruction):
        step = self.calls * 8
        self.calls += 1
        if step in self.steps:
            self.captured[step] = {key: np.asarray(observation[key]).copy() for key in RAW_KEYS}
        return self.policy(observation, instruction)


def save_long_dense_episode(directory, state, instruction, result, captured, *, provenance):
    if result.get("status") != "completed":
        raise ValueError("failed trajectory cannot become a Long timing panel")
    chunks = {row["control_step"]: row for row in result["chunks"]}
    if chunks[0]["observation_sha256"] != state["reference_initial_observation_sha256"]:
        raise ValueError("Long collection first raw observation differs from original dense state")
    steps = state["requested_control_steps"]
    present = [s for s in steps if s in chunks]
    if set(captured) != set(present):
        raise ValueError("captured observations differ from the registered actual dense queries")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    records = []
    for step in present:
        arrays = captured[step]
        sample = LongFixedObservation(f"{state['trial_id']}:control_step_{step}",
            state["trial_id"], state["task_name"], instruction, step, arrays)
        digest = libero_runtime._observation_hash(arrays)
        if digest != chunks[step]["observation_sha256"]:
            raise ValueError("captured raw bytes differ from actual policy input")
        path = directory / f"control_step_{step:03d}.npz"
        np.savez(path, **sample.observation)
        records.append({"observation_id": sample.observation_id, "control_step": step,
            "query_index": step // 8, "raw_observation_sha256": digest,
            "arrays": {"path": path.name, "sha256": file_sha256(path)}})
    receipt = {**result, "method": "dense", "state_trial_id": state["trial_id"],
        "task_id": state["task_id"], "task_name": state["task_name"], "instruction": instruction,
        "initial_state_sha256": state["initial_state_sha256"],
        "source_state_index": state["source_state_index"], "requested_control_steps": steps,
        "reference_control_steps": state["reference_control_steps"],
        "reference_initial_observation_sha256": state["reference_initial_observation_sha256"],
        "observations": records, "missing": [{"control_step": s,
            "reason": "dense_trajectory_ended_before_registered_query", "termination": result["termination"]}
            for s in steps if s not in present], "provenance": dict(provenance)}
    atomic_json(directory / "dense_receipt.json", receipt)
    return {"state_trial_id": state["trial_id"], "task_id": state["task_id"],
        "receipt": {"path": directory.name + "/dense_receipt.json",
            "sha256": file_sha256(directory / "dense_receipt.json")}}


def write_long_raw_panel(directory, development_panel, episodes, *, provenance, registration):
    profile_registration(registration)
    directory = Path(directory)
    atomic_json(directory / "development_panel.json", development_panel)
    payload = {"version": LONG_PANEL_VERSION, "split": "development", "test_opened": False,
        "source_kind": "simulator_raw", "arrays_preprocessed": False,
        "registration_signature": json_signature(registration),
        "requested_task_control_steps": LONG_CONTROL_STEPS,
        "selection_rule": "task0,3,5 minimum frozen source_state_index; original dense length fractions0,.5,.9 rounded down to chunk8; no replacement",
        "development_panel": {"path": "development_panel.json",
            "sha256": file_sha256(directory / "development_panel.json")},
        "episodes": episodes, "provenance": dict(provenance)}
    payload["content_signature"] = json_signature(payload)
    atomic_json(directory / "panel.json", payload)
    return payload


def load_long_raw_panel(path, *, development_panel, dense_reference, registration, expected_versions=None):
    path = Path(path)
    panel = json.loads(path.read_text(encoding="utf-8"))
    if panel.get("split") != "development" or panel.get("test_opened") is not False:
        raise ValueError("Long profiling never reads test observations")
    if (panel.get("version") != LONG_PANEL_VERSION or panel.get("content_signature") !=
            json_signature({k: v for k, v in panel.items() if k != "content_signature"})
            or panel.get("registration_signature") != json_signature(registration)
            or panel.get("requested_task_control_steps") != LONG_CONTROL_STEPS
            or panel.get("source_kind") != "simulator_raw" or panel.get("arrays_preprocessed") is not False):
        raise ValueError("Long raw panel identity/preregistration mismatch")
    if json.loads(_reference(path.parent, panel["development_panel"]).read_text(encoding="utf-8")) != development_panel:
        raise ValueError("Long panel development states differ from frozen source")
    provenance = panel["provenance"]
    if provenance.get("checkpoint_unchanged") is not True or any(provenance.get(k) != v for k, v in (expected_versions or {}).items()):
        raise ValueError("Long raw panel checkpoint/runtime identity mismatch")
    states = {s["trial_id"]: s for s in fixed_long_profile_states(development_panel, dense_reference, registration)}
    episodes = panel["episodes"]
    if len(episodes) != 3 or {r["state_trial_id"] for r in episodes} != set(states):
        raise ValueError("Long raw panel requires the three preselected development states")
    samples, missing, costs = [], [], []
    for row in episodes:
        state = states[row["state_trial_id"]]
        receipt_path = _reference(path.parent, row["receipt"])
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        expected = {"method": "dense", "status": "completed", "state_trial_id": state["trial_id"],
            **{k: state[k] for k in ("task_id", "task_name", "initial_state_sha256", "source_state_index",
                "requested_control_steps", "reference_control_steps", "reference_initial_observation_sha256")}}
        if row["task_id"] != state["task_id"] or any(receipt.get(k) != v for k, v in expected.items()) or receipt.get("provenance") != provenance:
            raise ValueError("Long dense receipt differs from frozen state/runtime")
        length, chunks = receipt["control_steps"], receipt["chunks"]
        if (type(length) is not int or not 1 <= length <= 520 or receipt["wait_steps"] != 10
                or receipt["policy_calls"] != len(chunks)
                or [c["control_step"] for c in chunks] != list(range(0, length, 8))
                or chunks[0]["observation_sha256"] != state["reference_initial_observation_sha256"]):
            raise ValueError("Long dense receipt violates fixed state/chunk8/horizon")
        if (receipt["termination"] not in ("task_horizon", "environment_success")
                or receipt["success"] != (receipt["termination"] == "environment_success")
                or (receipt["termination"] == "task_horizon" and length != 520)):
            raise ValueError("Long missing observations need actual terminal trajectory evidence")
        present = [s for s in state["requested_control_steps"] if s < length]
        expected_missing = [{"control_step": s, "reason": "dense_trajectory_ended_before_registered_query",
            "termination": receipt["termination"]} for s in state["requested_control_steps"] if s not in present]
        records = receipt["observations"]
        if [r["control_step"] for r in records] != present or receipt["missing"] != expected_missing:
            raise ValueError("Long panel omitted or replaced a predeclared observation")
        for record in records:
            step = record["control_step"]
            if record["query_index"] != step // 8 or record["observation_id"] != f"{state['trial_id']}:control_step_{step}":
                raise ValueError("Long raw observation query identity mismatch")
            with np.load(_reference(receipt_path.parent, record["arrays"]), allow_pickle=False) as archive:
                arrays = {key: archive[key].copy() for key in archive.files}
            sample = LongFixedObservation(record["observation_id"], state["trial_id"], state["task_name"], receipt["instruction"], step, arrays)
            if (libero_runtime._observation_hash(arrays) != record["raw_observation_sha256"]
                    or record["raw_observation_sha256"] != chunks[step // 8]["observation_sha256"]):
                raise ValueError("Long raw panel bytes differ from actual dense query")
            samples.append(sample)
        missing.extend({"state_trial_id": state["trial_id"], **m} for m in expected_missing)
        costs.append({"state_trial_id": state["trial_id"], "policy_calls": receipt["policy_calls"], "wall_seconds": receipt["wall_seconds"]})
    return samples, {"panel_sha256": file_sha256(path), "content_signature": panel["content_signature"],
        "version": LONG_PANEL_VERSION, "split": "development", "test_opened": False,
        "observations": len(samples), "target_observations": 9, "episodes": 3, "missing": missing,
        "collection_cost_excluded_from_call_latency": costs, "provenance": provenance}


def balanced_schedule(observation_ids, *, methods=LONG_METHODS, repeats=20, seed=1017):
    """One random base permutation, rotating blocks; position counts differ <=1."""
    if not observation_ids or len(set(observation_ids)) != len(observation_ids) or len(set(methods)) != len(methods):
        raise ValueError("schedule needs nonempty unique observations and method identities")
    rng = random.Random(seed)
    base = list(methods)
    rng.shuffle(base)
    result = []
    for repeat in range(repeats):
        offset = repeat % len(base)
        order = base[offset:] + base[:offset]
        observations = list(observation_ids)
        rng.shuffle(observations)
        result.append({"round": repeat, "method_order": order, "observation_order": observations})
    return result


@contextmanager
def original_auxiliary_module(module):
    """Serial, exception-safe module switch outside every measured block.

    Original frozen FutureRolloutPolicy imports hard_select_future inside its
    call. This context ensures that import resolves to its exact original
    module, while all model, selection and preprocessing dependencies are
    byte-identical and shared. No prediction head is constructed.
    """
    import cti_vla.training as package
    if not _MODULE_LOCK.acquire(blocking=False):
        raise RuntimeError("snapshot runtime switches must be strictly serial")
    name = "cti_vla.training.future_auxiliary"
    missing = object()
    previous, previous_attr = sys.modules.get(name, missing), getattr(package, "future_auxiliary", missing)
    try:
        sys.modules[name] = module
        setattr(package, "future_auxiliary", module)
        yield
    finally:
        if previous is missing:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        if previous_attr is missing:
            delattr(package, "future_auxiliary")
        else:
            setattr(package, "future_auxiliary", previous_attr)
        _MODULE_LOCK.release()


def _load_frozen_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def load_snapshot_deployment_modules(source_root, source_inventory, *, current_root):
    """Verify original source bytes; all shared execution dependencies must match."""
    source_root, current_root = Path(source_root), Path(current_root)
    inventory = json.loads(Path(source_inventory).read_text(encoding="utf-8"))
    files = inventory["files"]
    runtime_path = "src/cti_vla/evaluation/future_runtime.py"
    aux_path = "src/cti_vla/training/future_auxiliary.py"
    shared = [key for key in files if key.startswith(("src/cti_vla/models/", "src/cti_vla/selection/")) and key.endswith(".py")]
    shared += ["src/cti_vla_baselines/acl_matched.py", "src/cti_vla/evaluation/libero_runtime.py"]
    for key in [runtime_path, aux_path, *shared]:
        if key not in files or file_sha256(source_root / key) != files[key]:
            raise ValueError("frozen deployment snapshot bytes differ: " + key)
    for key in shared:
        if file_sha256(current_root / key) != files[key]:
            raise ValueError("shared model/selection/input dependency differs across snapshots: " + key)
    suffix = json_signature({"root": str(source_root.resolve()), "inventory": file_sha256(source_inventory)})[:16]
    aux = _load_frozen_module(source_root / aux_path, "cti_long_profile_aux_" + suffix)
    runtime = _load_frozen_module(source_root / runtime_path, "cti_long_profile_runtime_" + suffix)
    hashes = runtime.future_deployment_source_hashes(source_root)
    if any(files.get(key) != value for key, value in hashes.items()):
        raise ValueError("snapshot deployment source hashes differ from original inventory")
    return runtime, aux, {"source_root": str(source_root), "source_inventory_sha256": file_sha256(source_inventory),
        "runtime_sha256": files[runtime_path], "auxiliary_module_sha256": files[aux_path],
        "shared_source_files": {key: files[key] for key in shared}, "deployment_source_files": hashes}


def profile_long_methods(samples, factories, *, config, clock, emit, telemetry=lambda: {}, timer=time.perf_counter_ns):
    """Uninstrumented primary calls; no caches, component pass, or outlier removal."""
    if tuple(factories) != LONG_METHODS or not samples or len({s.observation_id for s in samples}) != len(samples):
        raise ValueError("Long profiling needs all13 registered instances and unique raw observations")
    if not config.get("synthetic", False) and getattr(clock, "device", None).type != "cuda":
        raise ValueError("real Long timing requires the allocated CUDA device")
    if (config["warmup_calls"], config["repeats"], config["component_repeats"], config["order_seed"]) != (20, 20, 0, 1017):
        raise ValueError("Long timing uses fixed20 warmups,20 rounds and no components")
    inputs = {s.observation_id: observation_signature(s) for s in samples}
    by_id = {s.observation_id: s for s in samples}
    schedule = balanced_schedule(list(by_id))
    rows, blocks, descriptions, warmed = [], [], {}, set()
    call_id = 0

    def call(name, method, sample, kind, round_index):
        nonlocal call_id
        method.set_stage_context(None)
        meta = {"call_id": call_id, "method": name, "instruction_mode": "uncached", "kind": kind,
            "round": round_index, "observation_id": sample.observation_id, "episode_id": sample.episode_id,
            "task_name": sample.task_name, "phase": sample.phase}
        call_id += 1
        emit({"event": "start", **meta})
        clock.synchronize()
        clock.reset_peak()
        began = timer()
        try:
            chunk = method.policy(sample.observation, sample.instruction)
            clock.synchronize()
            elapsed = (timer() - began) / 1e6
            _validate_chunk(chunk)
            metadata = chunk.metadata
            expected_tokens = 512 if name == "dense" else int(name.split("_")[0][1:])
            if (metadata.get("policy_calls") != 1 or metadata.get("vision_calls") != 1
                    or metadata.get("visual_tokens") != expected_tokens
                    or metadata.get("language_cache") != "disabled"
                    or (name != "dense" and (metadata.get("future_head_calls") != 0 or metadata.get("scorer_calls") != 1))):
                raise ValueError("timed policy violated actual deployment call/token/cache boundary")
            row = {**meta, "elapsed_ms": elapsed, "memory_bytes": clock.memory()}
            emit({"event": "complete", **row})
            if kind == "main":
                rows.append(row)
        except BaseException as exc:
            emit({"event": "failed", **meta, "error": f"{type(exc).__name__}: {exc}"})
            raise

    for block_schedule in schedule:
        for position, name in enumerate(block_schedule["method_order"]):
            # Loading a selector and switching its immutable runtime module are
            # setup, outside latency; allocation wall time still includes them.
            with factories[name]() as method:
                if method.metadata.get("cache_scope") != "none" or method.metadata.get("instruction_cache_enabled") is not False or method.metadata.get("future_head_deployed") is not False:
                    raise ValueError("Long timing forbids language/features/teacher/future caches and future deployment heads")
                description = dict(method.metadata)
                if name in descriptions and descriptions[name] != description:
                    raise ValueError("deployment identity changed between timing rounds")
                descriptions[name] = description
                clock.synchronize()
                block = {"round": block_schedule["round"], "method": name, "position": position,
                    "method_order": block_schedule["method_order"], "observation_order": block_schedule["observation_order"],
                    "telemetry_before": telemetry(), "resident_memory_bytes": clock.memory()}
                if name not in warmed:
                    for index in range(20):
                        call(name, method, samples[index % len(samples)], "warmup", -1)
                    warmed.add(name)
                for oid in block_schedule["observation_order"]:
                    call(name, method, by_id[oid], "main", block_schedule["round"])
                block["telemetry_after"] = telemetry()
                blocks.append(block)
    if inputs != {s.observation_id: observation_signature(s) for s in samples}:
        raise ValueError("timed deployment mutated the shared immutable raw panel")
    return {"profiling_version": LONG_PROFILE_VERSION, "status": "completed_measurement",
        "synthetic": config.get("synthetic", False), "config": dict(config), "methods": descriptions,
        "observations": len(samples), "observation_ids": [s.observation_id for s in samples],
        "observation_episodes": {s.observation_id: s.episode_id for s in samples},
        "episodes": len({s.episode_id for s in samples}), "sample_policy_forwards": call_id,
        "rows": rows, "blocks": blocks, "schedule": schedule,
        "boundary": "Raw simulator arrays + instruction ready -> executable CPU action chunk8 ready; batch1, CUDA sync before and after.",
        "included": "camera/proprio/prompt preprocessing, visual encoding, DIE when present, packing, one VLA forward, action D2H/unnormalization/gripper postprocessing",
        "excluded": "disk/model/checkpoint loading, simulator stepping/rendering, module activation, journal IO, telemetry; included in total allocation cost",
        "future_head_deployed": False, "cache_scope": "none", "component_passes": 0,
        "outlier_filter": "none; retain all measured calls and failures"}


def verify_long_profile_journal(result, path):
    cost = read_profile_cost(path)
    expected = {"warmup": 13 * 20, "main": 13 * 20 * result["observations"], "components": 0}
    if cost["failed"] or cost["unknown_completion"] or cost["attempts_by_pass"] != expected or cost != result.get("cost"):
        raise ValueError("Long timing journal cost/coverage differs from registration")
    events = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]
    completed = [{k: v for k, v in row.items() if k != "event"} for row in events if row.get("event") == "complete" and row["kind"] == "main"]
    if result["rows"] != completed:
        raise ValueError("Long timing rows differ from durable measured calls")
    if (len(result["observation_ids"]) != result["observations"]
            or set(result["observation_ids"]) != set(result["observation_episodes"])):
        raise ValueError("Long timing observation order/identity mismatch")
    planned = balanced_schedule(result["observation_ids"])
    if result["schedule"] != planned or len(result["blocks"]) != 260:
        raise ValueError("Long measured schedule differs from fixed balanced order")
    sequence = [(b["round"], name, oid) for b in planned for name in b["method_order"] for oid in b["observation_order"]]
    if [(r["round"], r["method"], r["observation_id"]) for r in completed] != sequence:
        raise ValueError("Long timing omitted/reordered a registered method/observation call")
    return cost


def summarize_long_profile(result):
    if result.get("status") != "completed_measurement" or tuple(result["methods"]) != LONG_METHODS:
        # JSON encoders may sort mapping keys: insertion order is not evidence.
        if result.get("status") != "completed_measurement" or set(result["methods"]) != set(LONG_METHODS):
            raise ValueError("Long summary requires all13 complete deployment instances")
    rows = result["rows"]
    expected_keys = {(m, r, oid) for m in LONG_METHODS for r in range(20) for oid in result["observation_episodes"]}
    keys = [(r["method"], r["round"], r["observation_id"]) for r in rows]
    if len(set(keys)) != len(keys) or set(keys) != expected_keys or any(not np.isfinite(r["elapsed_ms"]) or r["elapsed_ms"] <= 0 for r in rows):
        raise ValueError("Long latency requires finite complete paired observations; no dropping spikes")
    groups, obs_groups, comparisons = [], [], []
    for name in LONG_METHODS:
        subset = [r for r in rows if r["method"] == name]
        groups.append({"method": name, **_latency_stats([r["elapsed_ms"] for r in subset]),
            "observations": result["observations"], "repeats_per_observation": 20})
        for oid in result["observation_episodes"]:
            selected = [r["elapsed_ms"] for r in subset if r["observation_id"] == oid]
            obs_groups.append({"method": name, "observation_id": oid,
                "episode_id": result["observation_episodes"][oid], **_latency_stats(selected)})
    paired = {(r["method"], r["round"], r["observation_id"]): r["elapsed_ms"] for r in rows}
    pairs = [(name, "dense") for name in LONG_METHODS if name != "dense"]
    pairs += [(f"B{b}_seed{s}", f"A{b}_seed{s}") for b in (128, 64) for s in (17, 23, 41)]
    pairs += [(f"B64_seed{s}", f"A128_seed{s}") for s in (17, 23, 41)]
    for treatment, reference in pairs:
        x = [paired[(reference, r, oid)] for r in range(20) for oid in result["observation_episodes"]]
        y = [paired[(treatment, r, oid)] for r in range(20) for oid in result["observation_episodes"]]
        comparisons.append({"treatment": treatment, "reference": reference,
            "paired_calls": len(x), "speedup_ratio_of_means": float(np.mean(x) / np.mean(y)),
            "ratio_of_medians": float(np.median(x) / np.median(y)),
            "mean_paired_difference_ms": float(np.mean(np.asarray(y) - np.asarray(x)))})
    families, pooled = [], []
    for family in ("A128", "B128", "A64", "B64"):
        instances = [r for r in groups if r["method"].startswith(family + "_")]
        families.append({"method_family": family, "training_seeds": [17, 23, 41],
            "mean_of_seed_medians_ms": float(np.mean([r["median"] for r in instances])),
            "mean_of_seed_p95_ms": float(np.mean([r["p95"] for r in instances])),
            "seed_median_range_ms": [min(r["median"] for r in instances), max(r["median"] for r in instances)]})
        pooled.append({"method_family": family, "training_seeds": [17, 23, 41],
            **_latency_stats([r["elapsed_ms"] for r in rows if r["method"].startswith(family + "_")]),
            "unit_note": "descriptive pooled calls; no independent-observation inference"})
    return {"status": "completed_latency_analysis", "unit": "ms/action_chunk8", "synthetic": result["synthetic"],
        "primary": groups, "per_observation": obs_groups, "paired_comparisons": comparisons,
        "seed_equal_weight_summaries": families, "pooled_summaries": pooled,
        "retained_all_calls": True, "test_opened": False,
        "limitations": "Nine fixed observations from three development trajectories at most; repeats and training seeds are not independent observations. No population latency or task-success equivalence claim."}


def analyze_long_profile(directory, registration):
    """Rebuild actual latency summaries from the durable full-call journal.

    Nonweight evidence only: no remote checkpoint access or GPU calls. The
    collector validates raw bytes; its panel receipt stays bound in config.
    """
    profile_registration(registration)
    directory = Path(directory)
    config, result, saved = [json.loads((directory / name).read_text(encoding="utf-8"))
        for name in ("config.json", "measurements.json", "summary.json")]
    if (config.get("version") != LONG_PROFILE_VERSION or config.get("test_opened") is not False
            or config.get("registration_signature") != json_signature(registration)
            or config.get("config") != registration["profiling"]
            or config.get("cache_scope") != "none" or config.get("future_head_deployed") is not False
            or config.get("all_instances_share_one_loaded_base") is not True
            or config.get("uncontended_gpu_attested_and_checked") is not True
            or result.get("provenance") != config or result.get("checkpoint_unchanged") is not True
            or result.get("synthetic") is not False):
        raise ValueError("Long latency identity/runtime/evidence is incomplete or synthetic")
    events = [json.loads(line) for line in (directory / "calls.jsonl").read_text(encoding="utf-8").splitlines()]
    if not events or events[0].get("identity") != config:
        raise ValueError("Long timing journal uses a different deployment identity")
    verify_long_profile_journal(result, directory / "calls.jsonl")
    for key, name in (("measurements_sha256", "measurements.json"), ("journal_sha256", "calls.jsonl"), ("config_sha256", "config.json")):
        if saved.get(key) != file_sha256(directory / name):
            raise ValueError("Long latency summary artifact hash differs from raw evidence")
    rebuilt = summarize_long_profile(result)
    if any(saved.get(key) != value for key, value in rebuilt.items()) or saved.get("cost") != result["cost"]:
        raise ValueError("Long latency summary differs from raw call recomputation")
    return {**rebuilt, "cost": result["cost"], "panel": config["panel"],
        "verified_from_raw_call_journal": True, "config_sha256": file_sha256(directory / "config.json"),
        "measurements_sha256": file_sha256(directory / "measurements.json"),
        "journal_sha256": file_sha256(directory / "calls.jsonl"),
        "execution_wall_seconds_including_model_loading": result["execution_wall_seconds_including_model_loading"]}

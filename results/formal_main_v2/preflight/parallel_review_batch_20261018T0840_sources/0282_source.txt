"""Formal development observations and complete, uncached deployment timings.

This module never opens sealed final states. Collection is engineering work,
not additional success trials. Main and instrumented measurements are distinct
passes; every attempted call is retained in the append-only journal.
"""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import random
import time

import numpy as np

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation import libero_runtime
from cti_vla.evaluation.formal_runtime import FORMAL_SCHEMA, FORMAL_SUITES, FORMAL_BUDGETS, FORMAL_SEEDS
from cti_vla.evaluation.formal_trials import expected_method_ids, validate_execution_manifest, validate_freeze_matrix
from cti_vla.evaluation.profiling import RAW_KEYS, RawObservation, observation_signature, read_profile_cost, _validate_chunk
from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature

PROFILE_VERSION = "formal-main-v2-o2a-1"
PANEL_VERSION = "formal-main-v2-control-observations-1"
PHASES = ("preprocess", "vision", "condition_selection", "packing", "llm_action", "postprocess")
STATE_FIELDS = ("trial_id", "task_id", "task_name", "source_state_index", "source_file", "initial_state_sha256")


def profile_registration(registration):
    if registration.get("schema") != FORMAL_SCHEMA:
        raise ValueError("formal profiling requires the formal_main_v2 registration")
    config = registration.get("profiling", {})
    expected = dict(hardware="NVIDIA L40", observations_per_suite=30, warmups_per_instance=50,
        rounds=20, instances_per_suite=22, order_seed=20261016, keep_all_spikes=True,
        cross_call_feature_or_language_cache=False, independent_component_pass=True,
        component_pass_same_panel_warmups_rounds=True, load_disk_simulator_included=False)
    if any(config.get(k) != v for k, v in expected.items()):
        raise ValueError("formal profiling counts, boundary, cache or component protocol changed")
    return dict(config)


def validate_profile_manifest(manifest, registration, *, collect=False, global_freeze=None):
    profile_registration(registration)
    # Reject before a loader can follow any final-state path.
    if manifest.get("split") != "development":
        raise ValueError("formal profiling only reads development observations")
    identifiers = validate_execution_manifest(manifest, registration_sha256=json_signature(registration))
    expected = ["dense"] if collect else expected_method_ids()
    if identifiers != expected:
        raise ValueError("profiling requires the fixed dense-only or ordered22-instance manifest")
    if not collect:
        frozen = validate_freeze_matrix(global_freeze or {}, registration_sha256=json_signature(registration))
        if any(row["identity"] != frozen[(manifest["suite"], row["identity"]["method_id"])] for row in manifest["methods"]):
            raise ValueError("profiling checkpoint differs from the frozen success evaluation")
    return identifiers


def fixed_profile_states(development):
    from cti_vla.data.formal_initial_states import validate_formal_development_panel
    validate_formal_development_panel(development)
    return [min((r for r in development["states"] if r["task_id"] == task),
                key=lambda r: r["source_state_index"]) for task in range(10)]


def selected_control_steps(count):
    if type(count) is not int or count < 3:
        raise ValueError("collection needs three distinct actual control observations; never pad or substitute")
    return [0, (count - 1) // 2, count - 1]


class CaptureControlObservations:
    """Environment proxy copies pre-action arrays at EVERY actual control step.

    Waiting is counted separately. Copying precedes env.step, so simulator buffer
    reuse cannot silently turn an earlier observation into a later one. The
    standard rollout owns reset, queues, actions, success and horizon semantics.
    """
    def __init__(self, env, *, wait_steps=10):
        if wait_steps != 10:
            raise ValueError("formal collection fixes ten wait steps")
        self.env, self.wait_steps = env, wait_steps
        self.observation, self.steps, self.captured = None, 0, []

    def reset(self):
        if self.steps or self.captured:
            raise ValueError("collection proxy is one trajectory only; no resampling")
        return self.env.reset()

    def set_init_state(self, initial_state):
        self.observation = self.env.set_init_state(initial_state)
        return self.observation

    def step(self, action):
        if self.observation is None:
            raise ValueError("collection state must be set before stepping")
        if self.steps >= self.wait_steps:
            self.captured.append({k: np.array(self.observation[k], copy=True) for k in RAW_KEYS})
        value = self.env.step(action)
        self.observation = value[0]
        self.steps += 1
        return value


def _signed(payload):
    return {**payload, "content_signature": json_signature(payload)}


def _verify_signature(payload):
    if payload.get("content_signature") != json_signature({k: v for k, v in payload.items() if k != "content_signature"}):
        raise ValueError("formal profiling signed content changed")


def _local_ref(root, ref):
    path = (root / ref["path"]).resolve()
    if root.resolve() not in path.parents or Path(ref["path"]).is_absolute():
        raise ValueError("panel artifact escapes its immutable collection directory")
    if file_sha256(path) != ref["sha256"]:
        raise ValueError("formal collection artifact SHA256 changed")
    return path


def save_dense_collection(directory, state, instruction, result, captured, *, provenance):
    """Persist all trajectory hashes and exactly three raw observations."""
    if (result.get("status") != "completed" or result.get("wait_steps") != 10
            or result.get("control_steps") != len(captured)):
        raise ValueError("collection failed or did not capture every actual control step")
    indices = selected_control_steps(len(captured))
    hashes = [libero_runtime._observation_hash(obs) for obs in captured]
    if [r["control_step"] for r in result["chunks"]] != list(range(0, len(captured), 8)):
        raise ValueError("dense collection action-query cadence differs from chunk8")
    if any(r["observation_sha256"] != hashes[r["control_step"]] for r in result["chunks"]):
        raise ValueError("collected pre-action observations differ from actual dense inputs")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    observations = []
    for phase, step in zip(("first", "middle", "last"), indices):
        oid = f"task{state['task_id']:02d}:state{state['source_state_index']:04d}:step{step:04d}"
        sample = RawObservation(oid, state["trial_id"], state["task_name"], instruction, phase, captured[step])
        target = directory / (phase + ".npz")
        np.savez(target, **sample.observation)
        observations.append(dict(observation_id=oid, control_step=step, phase=phase,
            raw_sha256=observation_signature(sample), rollout_observation_sha256=hashes[step],
            arrays={"path": target.name, "sha256": file_sha256(target)}))
    receipt = _signed(dict(version=PANEL_VERSION, split="development", test_opened=False,
        new_success_trials=False, state={k: state[k] for k in STATE_FIELDS}, instruction=instruction,
        trajectory=result, all_control_observation_sha256=hashes, observations=observations,
        provenance=dict(provenance)))
    atomic_json(directory / "receipt.json", receipt)
    return {"task_id": state["task_id"], "receipt": {"path": directory.name + "/receipt.json",
        "sha256": file_sha256(directory / "receipt.json")}}


def write_profile_panel(directory, development, episodes, *, provenance, registration):
    if [r["task_id"] for r in episodes] != list(range(10)):
        raise ValueError("formal panel requires one fixed collection trajectory on every task")
    value = _signed(dict(version=PANEL_VERSION, suite=development["suite"], split="development",
        test_opened=False, new_success_trials=False, registration_sha256=json_signature(registration),
        development_panel_sha256=json_signature(development), provenance=dict(provenance), episodes=episodes,
        selection_rule="actual pre-action control steps 0,floor((N-1)/2),N-1; no padding or replacement"))
    atomic_json(Path(directory) / "panel.json", value)
    return value


def load_profile_panel(path, *, development, registration, dense_identity):
    path = Path(path)
    panel = json.loads(path.read_text(encoding="utf-8"))
    if panel.get("split") != "development" or panel.get("test_opened") is not False:
        raise ValueError("formal profiling never reads final observations")
    profile_registration(registration)
    states = fixed_profile_states(development)
    _verify_signature(panel)
    if (panel.get("version") != PANEL_VERSION or panel.get("suite") != development["suite"]
            or panel.get("registration_sha256") != json_signature(registration)
            or panel.get("development_panel_sha256") != json_signature(development)
            or panel.get("new_success_trials") is not False
            or panel.get("provenance", {}).get("dense_identity") != dense_identity
            or panel["provenance"].get("checkpoint_unchanged") is not True
            or [e["task_id"] for e in panel.get("episodes", [])] != list(range(10))):
        raise ValueError("formal panel selection, suite, source or immutable dense identity differs")
    samples, artifacts = [], {}
    for episode, state in zip(panel["episodes"], states):
        receipt_path = _local_ref(path.parent, episode["receipt"])
        artifacts[episode["receipt"]["path"]] = episode["receipt"]["sha256"]
        row = json.loads(receipt_path.read_text(encoding="utf-8"))
        _verify_signature(row)
        if (row.get("version") != PANEL_VERSION or row.get("split") != "development"
                or row.get("state") != {k: state[k] for k in STATE_FIELDS}
                or row.get("test_opened") is not False or row.get("new_success_trials") is not False
                or row.get("provenance") != panel["provenance"]):
            raise ValueError("formal collection receipt state/provenance differs")
        trajectory = row["trajectory"]
        count = trajectory["control_steps"]
        steps = selected_control_steps(count)
        hashes = row["all_control_observation_sha256"]
        if (trajectory.get("status") != "completed" or trajectory.get("wait_steps") != 10
                or count > FORMAL_SUITES[development["suite"]]["max_steps"] or len(hashes) != count
                or len(trajectory["executed_actions"]) != count
                or [c["control_step"] for c in trajectory["chunks"]] != list(range(0, count, 8))
                or trajectory.get("policy_calls") != len(trajectory["chunks"])
                or [o["control_step"] for o in row["observations"]] != steps
                or [o["phase"] for o in row["observations"]] != ["first", "middle", "last"]):
            raise ValueError("formal collection must use actual first/middle/last control steps without replacement")
        if any(c["observation_sha256"] != hashes[c["control_step"]] for c in trajectory["chunks"]):
            raise ValueError("dense collection query hashes disagree with pre-action control sequence")
        for observation in row["observations"]:
            archive_path = _local_ref(receipt_path.parent, observation["arrays"])
            artifacts[archive_path.relative_to(path.parent.resolve()).as_posix()] = observation["arrays"]["sha256"]
            with np.load(archive_path, allow_pickle=False) as archive:
                arrays = {k: archive[k].copy() for k in archive.files}
            step = observation["control_step"]
            expected_oid = f"task{state['task_id']:02d}:state{state['source_state_index']:04d}:step{step:04d}"
            sample = RawObservation(observation["observation_id"], state["trial_id"], state["task_name"],
                row["instruction"], observation["phase"], arrays)
            if (sample.observation_id != expected_oid or observation_signature(sample) != observation["raw_sha256"]
                    or libero_runtime._observation_hash(arrays) != observation["rollout_observation_sha256"]
                    or observation["rollout_observation_sha256"] != hashes[step]):
                raise ValueError("raw arrays differ from their registered actual trajectory observation")
            # Prevent accidental deployment mutation of the common CPU panel.
            for value in arrays.values():
                value.flags.writeable = False
            samples.append(sample)
    if len(samples) != 30 or len({s.observation_id for s in samples}) != 30:
        raise ValueError("formal profiling requires all30 unique observation identities")
    return samples, {"version": PANEL_VERSION, "panel_sha256": file_sha256(path),
        "content_signature": panel["content_signature"], "suite": panel["suite"], "observations": 30,
        "observation_ids": [s.observation_id for s in samples], "episodes": 10,
        "provenance": panel["provenance"], "artifact_sha256": artifacts, "test_opened": False}


def balanced_schedule(observation_ids):
    if len(set(observation_ids)) != len(observation_ids) or not observation_ids:
        raise ValueError("formal schedule requires a nonempty unique ordered observation panel")
    base = expected_method_ids()
    random.Random(20261016).shuffle(base)
    return [dict(round=r, method_order=base[r:] + base[:r], observation_order=list(observation_ids)) for r in range(20)]


class ComponentRecorder:
    """Host and CUDA-stream intervals, sequential and never nested.

    There are no per-phase synchronizations. CUDA events include CPU launch
    gaps; they are not pure kernel time. Host and stream times overlap and must
    not be added together. Unclassified host time includes measurement overhead.
    """
    def __init__(self, clock, timer=time.perf_counter_ns):
        self.clock, self.timer, self.active, self.intervals = clock, timer, False, []

    @contextmanager
    def phase(self, name):
        if name not in PHASES or self.active or name in [r[0] for r in self.intervals]:
            raise ValueError("formal component regions must be unique sequential registered phases")
        self.active = True
        start, stop = self.clock.event(), self.clock.event()
        if start is not None:
            start.record()
        began = self.timer()
        try:
            yield
        finally:
            host_ms = (self.timer() - began) / 1e6
            if stop is not None:
                stop.record()
            self.intervals.append((name, host_ms, start, stop))
            self.active = False

    def report(self, elapsed_ms):
        if self.active or [r[0] for r in self.intervals] != list(PHASES):
            raise ValueError("formal runtime must expose all six complete ordered component phases")
        result = {name: {"host_ms": host, "cuda_stream_elapsed_ms": None if start is None else float(start.elapsed_time(stop))}
            for name, host, start, stop in self.intervals}
        overhead = elapsed_ms - sum(r["host_ms"] for r in result.values())
        if overhead < -1e-6:
            raise ValueError("component host regions overlap or exceed the complete instrumented boundary")
        result["unclassified"] = {"host_ms": overhead, "cuda_stream_elapsed_ms": None}
        return result


def _validate_timed_chunk(chunk, identity):
    _validate_chunk(chunk)
    if not isinstance(chunk.environment_actions, np.ndarray):
        raise ValueError("profiling endpoint must already be executable CPU NumPy actions")
    meta = chunk.metadata
    required = dict(schema=FORMAL_SCHEMA, suite=identity["suite"], method=identity["method"],
        visual_tokens=identity["visual_tokens"], policy_calls=1, vision_calls=1, packing_calls=1,
        scorer_calls=int(identity["method"] in ("A", "B")), future_head_calls=0,
        language_cache="disabled", diagnostic_indices_recorded=False)
    if any(meta.get(k) != v for k, v in required.items()):
        raise ValueError("timed call violated its deployed identity, token, cache or single-forward boundary")
    if identity["method"] in ("A", "B") and any(meta.get(k) != v for k, v in {
            "selector_checkpoint_sha256": identity["checkpoint_sha256"], "training_seed": identity["training_seed"],
            "pair_id": identity["pair_id"]}.items()):
        raise ValueError("timed checkpoint differs from the success-evaluation checkpoint")
    array = np.ascontiguousarray(chunk.environment_actions)
    return hashlib.sha256(str(array.dtype).encode() + str(array.shape).encode() + array.tobytes()).hexdigest()


def profile_formal_methods(samples, factories, *, pass_name, clock, emit, telemetry=lambda: {},
        timer=time.perf_counter_ns, synthetic=False):
    if pass_name not in ("full", "components") or list(factories) != expected_method_ids():
        raise ValueError("formal timing needs a distinct full/components pass and all22 ordered instances")
    if not synthetic and (getattr(getattr(clock, "device", None), "type", None) != "cuda" or len(samples) != 30):
        raise ValueError("real formal timing requires CUDA and all30 fixed raw observations")
    ids = [s.observation_id for s in samples]
    schedule = balanced_schedule(ids)
    by_id = {s.observation_id: s for s in samples}
    signatures = {s.observation_id: observation_signature(s) for s in samples}
    descriptions, rows, blocks, warmed = {}, [], [], set()
    call_id = 0

    def call(name, method, sample, kind, round_index):
        nonlocal call_id
        recorder = ComponentRecorder(clock, timer) if pass_name == "components" else None
        method.set_stage_context(recorder.phase if recorder else None)
        meta = dict(call_id=call_id, method=name, instruction_mode="uncached", kind=kind,
            round=round_index, observation_id=sample.observation_id, episode_id=sample.episode_id,
            task_name=sample.task_name, phase=sample.phase)
        call_id += 1
        emit({"event": "start", **meta})
        try:
            clock.synchronize()
            clock.reset_peak()
            began = timer()
            chunk = method.policy(sample.observation, sample.instruction)
            clock.synchronize()
            elapsed = (timer() - began) / 1e6
            action_sha = _validate_timed_chunk(chunk, method.metadata["identity"])
            if not np.isfinite(elapsed) or elapsed <= 0:
                raise ValueError("elapsed wall time must be finite positive milliseconds")
            row = {**meta, "elapsed_ms": elapsed, "action_sha256": action_sha, "memory_bytes": clock.memory()}
            if recorder:
                row["components"] = recorder.report(elapsed)
            emit({"event": "complete", **row})
            if kind != "warmup":
                rows.append(row)
        except BaseException as exc:
            emit({"event": "failed", **meta, "error": f"{type(exc).__name__}: {exc}"})
            raise
        finally:
            method.set_stage_context(None)

    for round_plan in schedule:
        for position, name in enumerate(round_plan["method_order"]):
            with factories[name]() as method:
                description = dict(method.metadata)
                if (description.get("cache_scope") != "none" or description.get("instruction_cache_enabled") is not False
                        or description.get("future_head_deployed") is not False
                        or description.get("identity", {}).get("method_id") != name):
                    raise ValueError("formal profiling forbids teacher, feature, language and future-head deployment caches")
                if name in descriptions and descriptions[name] != description:
                    raise ValueError("formal deployment changed between timing rounds")
                descriptions[name] = description
                clock.synchronize()
                block = dict(round=round_plan["round"], method=name, position=position,
                    telemetry_before=telemetry(), resident_memory_bytes=clock.memory())
                if name not in warmed:
                    for i in range(50):
                        call(name, method, samples[i % len(samples)], "warmup", -1)
                    warmed.add(name)
                for oid in ids:
                    call(name, method, by_id[oid], "main" if pass_name == "full" else "components", round_plan["round"])
                block["telemetry_after"] = telemetry()
                blocks.append(block)
    if signatures != {s.observation_id: observation_signature(s) for s in samples}:
        raise ValueError("deployment mutated the immutable common raw observation panel")
    return dict(version=PROFILE_VERSION, status="completed_measurement", pass_name=pass_name, synthetic=synthetic,
        method_ids=expected_method_ids(), observation_ids=ids,
        observation_episodes={s.observation_id: s.episode_id for s in samples}, methods=descriptions,
        observations=len(samples), episodes=len({s.episode_id for s in samples}), rows=rows, blocks=blocks,
        schedule=schedule, sample_policy_forwards=call_id, warmups_per_instance=50, rounds=20,
        boundary="raw simulator arrays and instruction ready -> CPU executable action chunk8 ready; CUDA sync before/after",
        included="preprocessing, vision, DIE/conditions, packing, LLM/action head, D2H/unnormalization/action postprocessing",
        excluded="disk, model loading, simulator, activation, telemetry and journal IO; all charged in allocation cost",
        cache_scope="none", future_head_deployed=False, outlier_filter="none; retain all spikes and failures", test_opened=False)


def _validate_result_layout(result):
    ids, methods = result["observation_ids"], expected_method_ids()
    if (result.get("version") != PROFILE_VERSION or result.get("status") != "completed_measurement"
            or result.get("pass_name") not in ("full", "components") or result.get("method_ids") != methods
            or set(result["methods"]) != set(methods) or set(result["observation_episodes"]) != set(ids)
            or len(set(ids)) != len(ids) or result["observations"] != len(ids)
            or result.get("episodes") != len(set(result["observation_episodes"].values()))
            or result.get("warmups_per_instance") != 50 or result.get("rounds") != 20
            or result.get("sample_policy_forwards") != 22 * (50 + 20 * len(ids))
            or result["schedule"] != balanced_schedule(ids)):
        raise ValueError("formal timing layout/order/counts differ from the registration")
    sequence = [(p["round"], mid, oid) for p in result["schedule"] for mid in p["method_order"] for oid in ids]
    if [(r["round"], r["method"], r["observation_id"]) for r in result["rows"]] != sequence:
        raise ValueError("formal timing omitted, duplicated or reordered a measured call")
    if any(not np.isfinite(r["elapsed_ms"]) or r["elapsed_ms"] <= 0 for r in result["rows"]):
        raise ValueError("formal summary needs every finite positive measured call, including spikes")
    for row in result["rows"]:
        if row["episode_id"] != result["observation_episodes"][row["observation_id"]]:
            raise ValueError("timing row belongs to a different observation episode")
        if result["pass_name"] == "full" and "components" in row:
            raise ValueError("main latency may not include component instrumentation")
        if result["pass_name"] == "components":
            if set(row.get("components", {})) != set((*PHASES, "unclassified")):
                raise ValueError("component pass is incomplete")
            for value in row["components"].values():
                if (not np.isfinite(value["host_ms"]) or value["host_ms"] < -1e-6
                        or (value["cuda_stream_elapsed_ms"] is not None
                            and (not np.isfinite(value["cuda_stream_elapsed_ms"]) or value["cuda_stream_elapsed_ms"] < 0))):
                    raise ValueError("component intervals must be finite nonnegative measurements")
    return sequence


def verify_profile_journal(result, path):
    _validate_result_layout(result)
    cost = read_profile_cost(path)
    kind = "main" if result["pass_name"] == "full" else "components"
    expected = {"warmup": 1100, "main": 0, "components": 0}
    expected[kind] = 22 * 20 * result["observations"]
    if cost["failed"] or cost["unknown_completion"] or cost["attempts_by_pass"] != expected or cost != result.get("cost"):
        raise ValueError("formal timing journal has missing calls, failures or different cost counts")
    events = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]
    completed = [{k: v for k, v in e.items() if k != "event"} for e in events if e.get("event") == "complete"]
    if [e for e in completed if e["kind"] != "warmup"] != result["rows"]:
        raise ValueError("formal timing values differ from their durable raw journal")
    expected_sequence, warmed = [], set()
    for plan in result["schedule"]:
        for mid in plan["method_order"]:
            if mid not in warmed:
                expected_sequence.extend((mid, "warmup", -1, result["observation_ids"][i % result["observations"]]) for i in range(50))
                warmed.add(mid)
            expected_sequence.extend((mid, kind, plan["round"], oid) for oid in result["observation_ids"])
    if [(r["method"], r["kind"], r["round"], r["observation_id"]) for r in completed] != expected_sequence:
        raise ValueError("formal warmup/main call order differs from the frozen schedule")
    if [(b["round"], b["method"], b["position"]) for b in result["blocks"]] != [
            (p["round"], mid, pos) for p in result["schedule"] for pos, mid in enumerate(p["method_order"])]:
        raise ValueError("formal timing telemetry blocks differ from method ordering")
    return cost


def latency_stats(values):
    values = np.asarray(values, dtype=np.float64)
    if not len(values) or not np.isfinite(values).all():
        raise ValueError("latency statistics require finite nonempty measurements")
    return dict(count=len(values), median=float(np.median(values)), p95=float(np.quantile(values, .95)), mean=float(values.mean()))


def summarize_formal_profile(result):
    _validate_result_layout(result)
    ids, methods, rows = result["observation_ids"], result["method_ids"], result["rows"]
    values = {(r["method"], r["round"], r["observation_id"]): r for r in rows}
    primary, per_observation, components = [], [], []
    for mid in methods:
        ordered = [values[(mid, r, oid)] for r in range(20) for oid in ids]
        primary.append({"method": mid, **latency_stats([v["elapsed_ms"] for v in ordered])})
        for oid in ids:
            per_observation.append(dict(method=mid, observation_id=oid, episode_id=result["observation_episodes"][oid],
                **latency_stats([values[(mid, r, oid)]["elapsed_ms"] for r in range(20)])))
        if result["pass_name"] == "components":
            for phase in (*PHASES, "unclassified"):
                stream = [v["components"][phase]["cuda_stream_elapsed_ms"] for v in ordered]
                components.append(dict(method=mid, phase=phase,
                    host_ms=latency_stats([v["components"][phase]["host_ms"] for v in ordered]),
                    cuda_stream_elapsed_ms=None if all(v is None for v in stream) else latency_stats(stream)))
    stats = {r["method"]: r for r in primary}
    comparisons = []
    pairs = [(mid, "dense") for mid in methods[1:]]
    pairs += [(f"B{k}_seed{s}", f"A{k}_seed{s}") for k in FORMAL_BUDGETS for s in FORMAL_SEEDS]
    pairs += [(f"B64_seed{s}", f"A128_seed{s}") for s in FORMAL_SEEDS]
    for treatment, reference in pairs:
        x = np.asarray([values[(reference, r, oid)]["elapsed_ms"] for r in range(20) for oid in ids])
        y = np.asarray([values[(treatment, r, oid)]["elapsed_ms"] for r in range(20) for oid in ids])
        comparisons.append(dict(treatment=treatment, reference=reference, paired_calls=len(x),
            ratio_of_medians=float(np.median(x) / np.median(y)), ratio_of_p95=float(np.quantile(x, .95) / np.quantile(y, .95)),
            speedup_ratio_of_means=float(x.mean() / y.mean()), mean_paired_difference_ms=float(np.mean(y - x))))
    families = []
    for k in FORMAL_BUDGETS:
        for arm in ("A", "B"):
            group = [stats[f"{arm}{k}_seed{s}"] for s in FORMAL_SEEDS]
            families.append(dict(method_family=f"{arm}{k}", training_seeds=list(FORMAL_SEEDS),
                **{key: {"seed_mean": float(np.mean([v[key] for v in group])),
                          "seed_sample_std": float(np.std([v[key] for v in group], ddof=1))} for key in ("median", "p95", "mean")}))
    return dict(version=PROFILE_VERSION, status="completed_latency_analysis", pass_name=result["pass_name"],
        primary_inference_latency=result["pass_name"] == "full", unit="ms/action_chunk8", synthetic=result["synthetic"],
        primary=primary, per_observation=per_observation, paired_comparisons=comparisons,
        seed_equal_weight_summaries=families, components=components, retained_all_calls=True,
        test_opened=False, limitations="30 fixed observations from10 development trajectories; repeats and training seeds are not independent observations. Instrumented totals do not replace full timings; host and stream intervals overlap.")


def analyze_formal_profile(directory, registration):
    """Offline rebuild; explicit ordered ID lists survive sorted JSON storage."""
    profile_registration(registration)
    directory = Path(directory)
    config, result, saved = [json.loads((directory / name).read_text(encoding="utf-8"))
        for name in ("config.json", "measurements.json", "summary.json")]
    if (config.get("version") != PROFILE_VERSION or config.get("registration_sha256") != json_signature(registration)
            or config.get("cache_scope") != "none" or config.get("future_head_deployed") is not False
            or config.get("test_opened") is not False or result.get("provenance") != config
            or config.get("all_instances_share_one_loaded_base") is not True
            or config.get("profiling_registration") != registration["profiling"]
            or result.get("checkpoint_unchanged") is not True or result.get("synthetic") is not False
            or result.get("observations") != 30):
        raise ValueError("formal profiling identity is incomplete, changed or synthetic")
    identities = {r["identity"]["method_id"]: r["identity"] for r in config["manifest"]["methods"]}
    if set(identities) != set(expected_method_ids()) or any(result["methods"][m]["identity"] != identities[m] for m in identities):
        raise ValueError("formal timing deployment differs from its verified success identities")
    events = [json.loads(line) for line in (directory / "calls.jsonl").read_text(encoding="utf-8").splitlines()]
    if events[0].get("identity") != config:
        raise ValueError("formal profile journal belongs to another execution")
    verify_profile_journal(result, directory / "calls.jsonl")
    for field, name in (("config_sha256", "config.json"), ("measurements_sha256", "measurements.json"), ("journal_sha256", "calls.jsonl")):
        if saved.get(field) != file_sha256(directory / name):
            raise ValueError("formal profiling immutable artifact SHA changed")
    rebuilt = summarize_formal_profile(result)
    if any(saved.get(k) != v for k, v in rebuilt.items()):
        raise ValueError("saved formal summary disagrees with complete raw timing calls")
    uuid = config["allocation"]["gpu_uuid"]
    for block in result["blocks"]:
        for key in ("telemetry_before", "telemetry_after"):
            allocation = block[key]["uncontended_device"]
            if allocation["gpu_uuid"] != uuid or allocation["other_compute_processes"] != 0:
                raise ValueError("formal timings changed GPU or shared it with competing compute")
    return {**rebuilt, "cost": result["cost"], "measurements_sha256": file_sha256(directory / "measurements.json"),
        "execution_wall_seconds_including_model_loading": result["execution_wall_seconds_including_model_loading"]}

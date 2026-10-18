"""Full raw-observation latency measurement; component passes are separate.

No model, observation panel or selected tokens are cached by this module.
Disk reads, telemetry and durable journal writes stay outside measured calls.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import subprocess
import time
from typing import Callable, Mapping, Sequence

import numpy as np
import torch

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation.teacher_diagnostics import json_signature

PROFILING_VERSION = "raw-simulator-o2a-separate-components-v1"
PANEL_NAMESPACE = "cti-vla:raw-observation-latency-panel:v1"
PHASES = ("preprocess", "vision", "condition_selection", "policy", "postprocess")
RAW_KEYS = ("agentview_image", "robot0_eye_in_hand_image", "robot0_eef_pos",
            "robot0_eef_quat", "robot0_gripper_qpos")


@dataclass(frozen=True)
class RawObservation:
    observation_id: str
    episode_id: str
    task_name: str
    instruction: str
    phase: str
    observation: Mapping[str, np.ndarray]

    def __post_init__(self):
        if any(not isinstance(x, str) or not x for x in (self.observation_id, self.episode_id, self.task_name, self.instruction)):
            raise ValueError("observation/episode/task/instruction identities must be nonempty")
        if self.phase not in ("first", "middle", "last") or set(self.observation) != set(RAW_KEYS):
            raise ValueError("profiling accepts only the five raw simulator arrays and query phases")
        for key in RAW_KEYS:
            value = self.observation[key]
            if not isinstance(value, np.ndarray) or not np.isfinite(value).all():
                raise ValueError("raw observation arrays must be finite NumPy values")
            if key.endswith("image"):
                if value.ndim != 3 or value.shape[-1] != 3 or value.dtype != np.uint8:
                    raise ValueError("raw camera arrays must be uint8 [H,W,3]")
            elif value.shape != {"robot0_eef_pos": (3,), "robot0_eef_quat": (4,), "robot0_gripper_qpos": (2,)}[key]:
                raise ValueError("invalid raw simulator proprio shape")


def observation_signature(sample: RawObservation) -> str:
    digest = hashlib.sha256()
    for key in RAW_KEYS:
        value = np.ascontiguousarray(sample.observation[key])
        digest.update(json.dumps([key, value.dtype.str, value.shape]).encode())
        digest.update(value.tobytes())
    return digest.hexdigest()


def load_raw_panel(path, *, formal=False, freeze_receipt=None, methods_sha256=None, expected_freeze=None):
    """Verify raw simulator archives against actual dense trajectory receipts.

    Final-state artifacts are opened only after an explicit formal mode and a
    matching configuration freeze. No RLDS manifest or test split is discovered.
    """
    from collections import Counter
    from cti_vla.data.experiment_protocol import verify_payload
    from cti_vla.data.initial_states import validate_initial_state_manifest
    from cti_vla.evaluation.libero_runtime import _observation_hash
    path = Path(path)
    panel = json.loads(path.read_text(encoding="utf-8"))
    verify_payload(panel, PANEL_NAMESPACE)
    if panel.get("schema_version") != 1 or panel.get("source_kind") != "simulator_raw" or panel.get("arrays_preprocessed") is not False:
        raise ValueError("main latency accepts only unprocessed raw simulator arrays, never RLDS inputs")
    if panel.get("split") not in ("development", "test"):
        raise ValueError("raw panel must declare its authoritative initial-state split")
    frozen = None
    if panel["split"] == "test":
        # This guard precedes opening any state, trajectory or array reference.
        if not formal or freeze_receipt is None:
            raise ValueError("final/test timing is unavailable before an explicit configuration freeze")
        freeze_path = Path(freeze_receipt)
        frozen = json.loads(freeze_path.read_text(encoding="utf-8"))
        if frozen.get("status") != "configuration_frozen" or frozen.get("stage") != "final_evaluation" or panel.get("configuration_freeze_sha256") != file_sha256(freeze_path) or frozen.get("methods_sha256") != methods_sha256 or frozen.get("model_revision") != panel.get("model_revision"):
            raise ValueError("final panel/method configuration freeze mismatch")
        required = {"model_revision", "input_version", "packing_version", "action_version", "stats_key", "g0_report_sha256",
                    "runtime_sha256", "asset_manifest_sha256", "protocol_manifest_sha256"}
        if not isinstance(expected_freeze, Mapping) or set(expected_freeze) != required or any(frozen.get(key) != value for key, value in expected_freeze.items()):
            raise ValueError("formal runtime/G0/statistics protocol differs from the approved freeze")
    elif formal:
        raise ValueError("development inputs cannot be reported as a formal shared panel")

    def reference(value):
        candidate = (path.parent / value["path"]).resolve()
        if path.parent.resolve() not in candidate.parents or file_sha256(candidate) != value["sha256"]:
            raise ValueError("panel reference must be inside its archive with matching bytes")
        return candidate

    states = json.loads(reference(panel["initial_states_manifest"]).read_text(encoding="utf-8"))
    validate_initial_state_manifest(states)
    if states["split"] != panel["split"]:
        raise ValueError("raw observations use another initial-state split")
    if frozen is not None and panel["initial_states_manifest"]["sha256"] != frozen.get("initial_states_manifest_sha256"):
        raise ValueError("final initial states differ from the predeclared freeze receipt")
    authoritative = {row["trial_id"]: row for row in states["states"]}
    episodes, observations = panel["episodes"], panel["observations"]
    if not episodes or len({row["episode_id"] for row in episodes}) != len(episodes):
        raise ValueError("raw panel episode identities must be unique and nonempty")
    if frozen is not None:
        ids = {row["episode_id"] for row in episodes}
        if ids != set(frozen["profile_panel_state_ids"]) or len(ids) != 100 or len(Counter(row["task_name"] for row in episodes)) != 10 or set(Counter(row["task_name"] for row in episodes).values()) != {10}:
            raise ValueError("formal panel must use the preregistered ten states for each of ten tasks")
    expected, receipt_chunks = {}, {}
    for episode in episodes:
        eid = episode["episode_id"]
        state = authoritative.get(eid)
        if state is None or state["task_name"] != episode["task_name"]:
            raise ValueError("raw panel episode is outside authoritative initial states")
        receipt = json.loads(reference(episode["dense_receipt"]).read_text(encoding="utf-8"))
        if receipt.get("method") != "dense" or receipt.get("status") != "completed" or receipt.get("state_trial_id") != eid or receipt.get("initial_state_sha256") != state["initial_state_sha256"] or receipt.get("instruction") != episode["instruction"] or receipt.get("model_revision") != panel.get("model_revision"):
            raise ValueError("raw panel requires the matching completed dense trajectory")
        if frozen is not None and receipt.get("configuration_freeze_sha256") != panel["configuration_freeze_sha256"]:
            raise ValueError("formal dense trajectory predates the frozen evaluation configuration")
        chunks = receipt["chunks"]
        if not chunks or len(chunks) != receipt["policy_calls"] or episode["policy_calls"] != len(chunks):
            raise ValueError("dense trajectory has inconsistent policy-query coverage")
        indices = [(0, "first")] if len(chunks) == 1 else ([(0, "first"), (1, "last")] if len(chunks) == 2 else [(0, "first"), ((len(chunks) - 1) // 2, "middle"), (len(chunks) - 1, "last")])
        for index, phase in indices:
            expected[(eid, index)] = (phase, episode["task_name"], episode["instruction"])
            receipt_chunks[(eid, index)] = chunks[index]["observation_sha256"]
    if len(observations) != len(expected) or {(row["episode_id"], row["query_index"]) for row in observations} != set(expected):
        raise ValueError("raw panel omits or adds predeclared first/middle/last dense queries")
    result = []
    for row in observations:
        key = (row["episode_id"], row["query_index"])
        phase, task, instruction = expected[key]
        if row["phase"] != phase:
            raise ValueError("raw panel query phase mismatch")
        with np.load(reference(row["arrays"]), allow_pickle=False) as archive:
            arrays = {name: archive[name].copy() for name in archive.files}
        sample = RawObservation(row["observation_id"], key[0], task, instruction, phase, arrays)
        if _observation_hash(arrays) != receipt_chunks[key]:
            raise ValueError("raw array bytes differ from the actual dense query observation")
        result.append(sample)
    if len({s.observation_id for s in result}) != len(result):
        raise ValueError("raw panel observation IDs are duplicated")
    return result, {"panel_sha256": file_sha256(path), "panel_signature": panel["content_signature"],
                    "split": panel["split"], "formal": formal, "observations": len(result), "episodes": len(episodes),
                    "target_observations": 300 if formal else None,
                    "short_trajectory_observations_missing": 3 * len(episodes) - len(result),
                    "configuration_freeze_sha256": panel.get("configuration_freeze_sha256"), "model_revision": panel["model_revision"]}


@dataclass(frozen=True)
class ProfileConfig:
    warmup_calls: int = 50
    repeats: int = 5
    component_repeats: int = 1
    order_seed: int = 1017
    instruction_modes: tuple[str, ...] = ("cold", "hot")
    synthetic: bool = False

    def __post_init__(self):
        if any(type(x) is not int or x < 0 for x in (self.warmup_calls, self.repeats, self.component_repeats, self.order_seed)):
            raise ValueError("profiling counts/seed must be nonnegative integers")
        if self.repeats < 1 or not self.instruction_modes or len(set(self.instruction_modes)) != len(self.instruction_modes) or not set(self.instruction_modes) <= {"cold", "hot"}:
            raise ValueError("profiling needs repeats and distinct cold/hot instruction modes")
        if not self.synthetic and (self.warmup_calls != 50 or self.repeats != 5 or self.component_repeats != 1 or set(self.instruction_modes) != {"cold", "hot"}):
            raise ValueError("formal protocol fixes 50 warmups, five main rounds, one separate component round and cold/hot")


@dataclass
class ProfileMethod:
    """Factory result: a full raw-observation policy, with language-only hooks.

    clear/prime hooks must never perform vision/selection/policy forwards.
    The current adapters cache no language; the no-op hooks make that explicit.
    """
    policy: Callable
    metadata: Mapping
    set_stage_context: Callable
    clear_instruction: Callable = lambda: None
    prime_instruction: Callable = lambda instruction: None


class TorchClock:
    def __init__(self, device):
        self.device = torch.device(device)

    def synchronize(self):
        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)

    def event(self):
        return torch.cuda.Event(enable_timing=True) if self.device.type == "cuda" else None

    def reset_peak(self):
        if self.device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(self.device)

    def memory(self):
        if self.device.type != "cuda":
            return {name: None for name in ("allocated", "reserved", "peak_allocated", "peak_reserved")}
        return {"allocated": torch.cuda.memory_allocated(self.device), "reserved": torch.cuda.memory_reserved(self.device),
                "peak_allocated": torch.cuda.max_memory_allocated(self.device), "peak_reserved": torch.cuda.max_memory_reserved(self.device)}


class StageRecorder:
    """CUDA stream events and host wall time, without per-stage synchronization.

    Host and stream intervals may overlap and are not additive. CUDA intervals
    include launch gaps on the stream; they are not pure kernel execution time.
    """
    def __init__(self, clock, timer=time.perf_counter_ns):
        self.clock, self.timer = clock, timer
        self.intervals, self.active = [], False

    @contextmanager
    def phase(self, name):
        if name not in PHASES or self.active:
            raise ValueError("profiling phases must be known, nonnested sequential regions")
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

    def report(self):
        # Caller synchronized once at the end of the entire component pass.
        if self.active or {row[0] for row in self.intervals} != set(PHASES):
            raise ValueError("component adapter must expose all five complete profiling phases")
        values = {}
        for name, host, start, stop in self.intervals:
            row = values.setdefault(name, {"host_ms": 0.0, "cuda_stream_elapsed_ms": 0.0 if start is not None else None, "regions": 0})
            row["host_ms"] += host
            if start is not None:
                row["cuda_stream_elapsed_ms"] += float(start.elapsed_time(stop))
            row["regions"] += 1
        return values


class ProfileJournal:
    """New-run-only journal: starts survive hard kills and remain charged.

    Timing runs are not silently resumed or merged across thermal conditions.
    Failed attempts remain in this run; a planned rerun uses a new output.
    """
    def __init__(self, path: Path, identity: Mapping):
        self.path, self.identity_sha = Path(path), json_signature(identity)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps({"event": "identity", "identity": identity, "identity_sha256": self.identity_sha}, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def __call__(self, event):
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())


def read_profile_cost(path):
    """Ledger-only accounting, including starts left by a killed process."""
    with Path(path).open(encoding="utf-8") as stream:
        events = [json.loads(line) for line in stream]
    if not events or events[0].get("event") != "identity" or events[0].get("identity_sha256") != json_signature(events[0]["identity"]):
        raise ValueError("profiling journal identity mismatch")
    calls = {}
    for event in events[1:]:
        index = event["call_id"]
        if event["event"] == "start":
            if index != len(calls):
                raise ValueError("profiling starts must use consecutive unique IDs")
            calls[index] = {**event, "completion": "unknown"}
        elif event["event"] in ("complete", "failed"):
            if index not in calls or calls[index]["completion"] != "unknown" or any(event[key] != calls[index][key] for key in ("method", "instruction_mode", "kind", "round", "observation_id", "episode_id")):
                raise ValueError("invalid or duplicate profiling completion")
            calls[index]["completion"] = event["event"]
        else:
            raise ValueError("unknown profiling journal event")
    return {"sample_policy_forwards_attempted": len(calls), "api_calls_attempted": len(calls),
            "completed": sum(row["completion"] == "complete" for row in calls.values()),
            "failed": sum(row["completion"] == "failed" for row in calls.values()),
            "unknown_completion": sum(row["completion"] == "unknown" for row in calls.values()),
            "attempts_by_pass": {kind: sum(row["kind"] == kind for row in calls.values()) for kind in ("warmup", "main", "components")},
            "scope": "Batch1 full-pipeline policy attempts; includes warmup/component passes. Hard-kill total wall/GPU cost requires scheduler accounting."}


def verify_measurement_journal(result, path):
    cost = read_profile_cost(path)
    if cost["failed"] or cost["unknown_completion"] or result.get("cost") != cost:
        raise ValueError("measurement cost differs from complete durable call evidence")
    events = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]
    rows = [{key: value for key, value in event.items() if key != "event"} for event in events
            if event.get("event") == "complete" and event["kind"] != "warmup"]
    if rows != result["rows"]:
        raise ValueError("latency rows differ from durable measured call values")
    config, methods, count = result["config"], len(result["methods"]), result["observations"]
    modes = len(config["instruction_modes"])
    expected = {"warmup": methods * config["warmup_calls"], "main": methods * count * modes * config["repeats"],
                "components": methods * count * modes * config["component_repeats"]}
    if cost["attempts_by_pass"] != expected:
        raise ValueError("measured pass counts differ from the fixed warmup/repeat protocol")
    return cost

def _validate_chunk(chunk):
    actions = np.asarray(chunk.environment_actions)
    if actions.shape != (8, 7) or not np.isfinite(actions).all() or (np.abs(actions) > 1.00001).any():
        raise ValueError("timing endpoint requires a finite executable CPU action chunk [8,7]")


def profile_methods(samples: Sequence[RawObservation], factories: Mapping[str, Callable[[], ProfileMethod]], *,
                    config: ProfileConfig, clock, emit: Callable, telemetry: Callable = lambda: {},
                    timer=time.perf_counter_ns) -> dict:
    """Complete raw-input calls only. Primary passes install no phase hooks."""
    if not samples or len({s.observation_id for s in samples}) != len(samples) or "dense" not in factories:
        raise ValueError("a unique nonempty raw panel and matched dense method are required")
    if not config.synthetic and getattr(clock, "device", torch.device("cpu")).type != "cuda":
        raise ValueError("formal latency measurement requires the allocated CUDA device")
    input_hashes = {s.observation_id: observation_signature(s) for s in samples}
    rng = random.Random(config.order_seed)
    warmed, rows, blocks, descriptions = set(), [], [], {}
    call_id = 0

    def call(method_name, method, sample, mode, kind, round_index):
        nonlocal call_id
        # Clearing the instruction cache is experiment setup. Filling it is
        # excluded only for explicitly hot instruction; cold encoding is inside.
        if mode == "cold":
            method.clear_instruction()
        elif method.metadata.get("instruction_cache_enabled", False):
            method.prime_instruction(sample.instruction)
        recorder = StageRecorder(clock, timer) if kind == "components" else None
        method.set_stage_context(recorder.phase if recorder else None)
        meta = {"call_id": call_id, "method": method_name, "instruction_mode": mode, "kind": kind,
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
            # Validation occurs after the measured endpoint, while conversion,
            # D2H, unnormalization and gripper processing belong in the policy.
            _validate_chunk(chunk)
            row = {**meta, "elapsed_ms": elapsed, "memory_bytes": clock.memory()}
            if recorder:
                row["components"] = recorder.report()
            emit({"event": "complete", **row})
            if kind != "warmup":
                rows.append(row)
        except BaseException as exc:
            emit({"event": "failed", **meta, "error": f"{type(exc).__name__}: {exc}"})
            raise
        finally:
            method.set_stage_context(None)

    for kind, repeats in (("main", config.repeats), ("components", config.component_repeats)):
        for round_index in range(repeats):
            order = list(factories)
            rng.shuffle(order)
            for name in order:
                method = factories[name]()
                if method.metadata.get("cache_scope", "none") not in ("none", "language_only"):
                    raise ValueError("profiling forbids visual/indices/action/output caches")
                description = dict(method.metadata)
                if name in descriptions and descriptions[name] != description:
                    raise ValueError("method/checkpoint identity changed between rounds")
                descriptions[name] = description
                clock.synchronize()
                block = {"kind": kind, "round": round_index, "method": name, "method_order": order,
                         "resident_memory_bytes": clock.memory(), "telemetry_before": telemetry()}
                if name not in warmed:
                    for index in range(config.warmup_calls):
                        call(name, method, samples[index % len(samples)], "cold", "warmup", -1)
                    warmed.add(name)
                modes = list(config.instruction_modes)
                rng.shuffle(modes)
                for mode in modes:
                    for sample in samples:
                        call(name, method, sample, mode, kind, round_index)
                block["telemetry_after"] = telemetry()
                blocks.append(block)
                # Factories must not retain prior methods/scorers on the GPU.
                del method
    if input_hashes != {s.observation_id: observation_signature(s) for s in samples}:
        raise ValueError("policy mutated the shared raw observation panel")
    return {"profiling_version": PROFILING_VERSION, "status": "completed_measurement", "synthetic": config.synthetic,
            "config": asdict(config), "methods": descriptions, "observations": len(samples),
            "observation_episodes": {s.observation_id: s.episode_id for s in samples},
            "episodes": len({s.episode_id for s in samples}), "sample_policy_forwards": call_id,
            "rows": rows, "blocks": blocks,
            "boundary": "Raw simulator arrays and instruction ready to executable CPU action chunk ready, ms/chunk, batch=1.",
            "component_scope": "Separate instrumented full-pipeline passes; host and CUDA stream intervals overlap and are not additive. Policy phase includes packing, LLM and action head.",
            "excluded": "File loading/decoding, model loading, simulator stepping/rendering, journal IO, telemetry; language priming excluded only in hot mode."}


def summarize_latencies(result: Mapping, *, bootstrap_repeats=2000, seed=1117) -> dict:
    """Paired episode-cluster intervals after averaging repeated observations."""
    if type(bootstrap_repeats) is not int or bootstrap_repeats < 100:
        raise ValueError("latency bootstrap needs at least 100 replicates")
    rows = [r for r in result["rows"] if r["kind"] == "main"]
    if not rows or any(not math.isfinite(r["elapsed_ms"]) or r["elapsed_ms"] <= 0 for r in rows):
        raise ValueError("latency records must contain finite positive primary timings")
    keys = [(r["method"], r["instruction_mode"], r["round"], r["observation_id"]) for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate latency observation/round record")
    identities = result["observation_episodes"]
    if len(identities) != result["observations"]:
        raise ValueError("declared observation coverage disagrees with raw panel identity")
    expected_keys = {(method, mode, repeat, oid) for method in result["methods"]
                     for mode in result["config"]["instruction_modes"]
                     for repeat in range(result["config"]["repeats"]) for oid in identities}
    if set(keys) != expected_keys or any(identities[r["observation_id"]] != r["episode_id"] for r in rows):
        raise ValueError("primary latency records omit/add declared methods, modes, rounds or observations")
    groups, comparisons = [], []
    for mode in sorted({r["instruction_mode"] for r in rows}):
        dense = {(r["round"], r["observation_id"]): r for r in rows if r["method"] == "dense" and r["instruction_mode"] == mode}
        for method in sorted({r["method"] for r in rows}):
            subset = [r for r in rows if r["method"] == method and r["instruction_mode"] == mode]
            paired = {(r["round"], r["observation_id"]): r for r in subset}
            if not dense or paired.keys() != dense.keys() or any(paired[k]["episode_id"] != dense[k]["episode_id"] for k in dense):
                raise ValueError("all methods need the same observation/round/episode panel as dense")
            values = np.asarray([r["elapsed_ms"] for r in subset])
            by_round = {str(i): _latency_stats([r["elapsed_ms"] for r in subset if r["round"] == i]) for i in sorted({r["round"] for r in subset})}
            memory = {}
            for field in ("peak_allocated", "peak_reserved"):
                measured = [r["memory_bytes"][field] for r in subset]
                memory[field] = max(measured) if all(v is not None for v in measured) else None
            groups.append({"method": method, "instruction_mode": mode, **_latency_stats(values), "by_round": by_round,
                           "peak_memory_bytes": memory})
            if method == "dense":
                continue
            obs = sorted({r["observation_id"] for r in subset})
            per_obs = []
            for oid in obs:
                matching = [k for k in paired if k[1] == oid]
                per_obs.append((paired[matching[0]]["episode_id"],
                                np.mean([dense[k]["elapsed_ms"] for k in matching]),
                                np.mean([paired[k]["elapsed_ms"] for k in matching])))
            episodes = sorted({v[0] for v in per_obs})
            sums = np.asarray([[sum(v[1] for v in per_obs if v[0] == ep), sum(v[2] for v in per_obs if v[0] == ep)] for ep in episodes])
            rng = np.random.default_rng(seed)
            interval = None
            if len(episodes) >= 2:
                draws = rng.integers(0, len(episodes), (bootstrap_repeats, len(episodes)))
                totals = sums[draws].sum(1)
                interval = np.quantile(totals[:, 0] / totals[:, 1], [.025, .975]).tolist()
            comparisons.append({"method": method, "instruction_mode": mode,
                                "speedup_ratio_of_paired_means": float(sums[:, 0].sum() / sums[:, 1].sum()),
                                "speedup_ci95_episode_cluster": interval, "observations": len(obs), "episode_clusters": len(episodes)})
    components = []
    for method in sorted(result["methods"]):
        for mode in sorted({r["instruction_mode"] for r in rows}):
            selected = [r for r in result["rows"] if r["kind"] == "components" and r["method"] == method and r["instruction_mode"] == mode]
            for phase in PHASES:
                if selected:
                    host = [r["components"][phase]["host_ms"] for r in selected]
                    device = [r["components"][phase]["cuda_stream_elapsed_ms"] for r in selected]
                    components.append({"method": method, "instruction_mode": mode, "phase": phase,
                                       "host_ms": _latency_stats(host), "cuda_stream_elapsed_ms": _latency_stats(device) if all(v is not None for v in device) else None})
    return {"status": "completed_latency_analysis", "synthetic": result["synthetic"], "unit": "ms/action_chunk8",
            "primary": groups, "paired_dense_comparisons": comparisons, "components_separate_pass": components,
            "bootstrap": {"repeats": bootstrap_repeats, "seed": seed, "unit": "episode", "repeated_observations_averaged_before_resampling": True},
            "interpretation": "Latency only. No success-rate, scientific go or acceleration claim without actual matched measurements."}


def _latency_stats(values):
    array = np.asarray(values, dtype=np.float64)
    return {"count": len(array), "mean": float(array.mean()), "median": float(np.median(array)), "p95": float(np.quantile(array, .95))}


def hardware_telemetry() -> dict:
    result = {"cpu": platform.processor(), "cpu_count": os.cpu_count(), "python": platform.python_version(),
              "torch": torch.__version__, "torch_cuda": torch.version.cuda,
              "slurm": {key: os.environ.get(key) for key in ("SLURM_JOB_ID", "SLURM_CPUS_PER_TASK", "SLURM_MEM_PER_NODE", "SLURM_JOB_GPUS")}}
    try:
        result["cpu_affinity"] = sorted(os.sched_getaffinity(0))
    except AttributeError:
        result["cpu_affinity"] = None
    try:
        query = "index,uuid,name,driver_version,temperature.gpu,power.draw,clocks.current.sm,clocks.current.memory,memory.used,utilization.gpu"
        completed = subprocess.run(["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5, check=True)
        result["nvidia_smi_columns"] = query.split(",")
        result["nvidia_smi_rows"] = completed.stdout.strip().splitlines()
    except (OSError, subprocess.SubprocessError) as exc:
        result["nvidia_smi_unavailable"] = str(exc)
    return result


__all__ = ["PROFILING_VERSION", "PANEL_NAMESPACE", "PHASES", "RAW_KEYS", "RawObservation", "ProfileConfig", "ProfileMethod",
           "TorchClock", "StageRecorder", "ProfileJournal", "profile_methods", "summarize_latencies", "observation_signature", "hardware_telemetry", "load_raw_panel", "read_profile_cost", "verify_measurement_journal"]

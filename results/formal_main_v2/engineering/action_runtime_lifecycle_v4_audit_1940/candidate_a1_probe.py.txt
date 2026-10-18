"""Undeployed, bounded engineering candidate. No scientific trial/retry entry.

The CPU inspector reads existing development-only metadata. GPU execution needs
a separately hashed root preregistration and fresh Slurm process; this candidate
and its manifest alone do not authorize execution.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager, ExitStack
from datetime import datetime, timezone
import gc
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import random
import re
import struct
import sys
import time
import traceback

VERSION = "action-execution-gpu-candidate-1940-v4-runtime-lifecycle"
GPU_VERSION = "formal_main_v2_action_execution_compat_gpu_v4"
PROJECT = Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
SOURCE_NAME = "formal_main_v2_run_564be0995e"
SOURCE_SHA = "dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e"
INVENTORY_SHA = "5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926"
ADAPTER_SHA = "b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185"
ADAPTER_CPU = {
    "action_adapter_root_review": ("69b6220c13f41b40661d9a9fc8e6234e568030e3852841024d794e58781ea52b", "passed_CPU_only_pending_registered_controller_GPU_acceptance"),
    "action_adapter_independent_review": ("171b93b145431bdffb9138eea48673e9185dcadbef226e468d0ab140a7a470f1", "passed_CPU_review_GPU_acceptance_pending"),
}
SUITES = ("libero_10", "libero_spatial", "libero_object", "libero_goal")
METHODS = ("dense", "uniform128", "A128_seed17", "B128_seed17")
STATE_INDICES = dict(zip(SUITES, (0, 3, 5, 7)))
PANELS = {s: f"configs/manifests/formal_main_v2/{s}/initial_states/development.json" for s in SUITES}
LIMITS = dict(env_seed=0, runtime_seed=17, wait_steps=10, max_control_steps=8,
    action_chunk=8, cells=16, max_vla_calls=16, max_vision_calls=16,
    policy_watchdog_seconds=60, wall_seconds=3600)
PAYLOAD_SUFFIXES = {".pt", ".pth", ".bin", ".ckpt", ".safetensors", ".pkl", ".pickle", ".npz", ".npy", ".init", ".pruned_init"}


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def signature(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def metadata_path(root, relative, *, panels=False):
    """No resolve/stat/hash of state or weight aliases before lexical rejection."""
    require(isinstance(relative, str) and relative and "\\" not in relative and ":" not in relative, "invalid metadata path")
    p = PurePosixPath(relative)
    require(not p.is_absolute() and p.as_posix() == relative and ".." not in p.parts, "metadata traversal")
    lower = [part.lower() for part in p.parts]
    source = p.suffix == ".py" and p.parts[0] in {"src", "scripts", "tests"}
    state = any(any(stem in part for stem in ("init_state", "initial_state", "final_state", "test_state")) for part in lower)
    require(not any("sealed" in part or part in {"test", "weights", "checkpoints"} for part in lower)
        and "final_registry" not in relative.lower() and p.suffix.lower() not in PAYLOAD_SUFFIXES
        and not ("final" in lower and p.name == "panel.json")
        and (not state or source or (panels and relative in PANELS.values())), "forbidden metadata/state path")
    root, target = Path(root), Path(root) / relative
    require(root.resolve() in target.resolve().parents and target.resolve() == target.absolute(), "metadata alias/traversal")
    for part in (target, *target.parents):
        if part == root:
            break
        require(not part.is_symlink(), "metadata symlink")
    return target


class Evidence:
    def __init__(self, project, source):
        self.project, self.source, self.seen = Path(project), Path(source), {}

    def bytes(self, relative, expected=None, *, source=False, panels=False):
        path = metadata_path(self.source if source else self.project, relative, panels=panels)
        data = path.read_bytes(); digest = hashlib.sha256(data).hexdigest()
        require(expected is None or digest == expected, "input SHA mismatch: " + relative)
        require(str(path) not in self.seen or self.seen[str(path)] == digest, "input changed during reads")
        self.seen[str(path)] = digest
        return data

    def json(self, relative, expected=None, **kwargs):
        return json.loads(self.bytes(relative, expected, **kwargs))

    def reference(self, ref, **kwargs):
        data = self.bytes(ref["path"], ref["sha256"], **kwargs)
        require(len(data) == ref["bytes"], "input byte count differs")
        return json.loads(data)

    def unchanged(self):
        for path, expected in self.seen.items():
            require(sha(path) == expected, "input changed: " + path)


def state_hash(values):
    require(isinstance(values, list) and values and all(type(v) in (float, int) and math.isfinite(v) for v in values), "invalid development state")
    return hashlib.sha256(b"cti-vla:libero-init-state:v1\x00" + struct.pack("<q", len(values))
        + b"".join(struct.pack("<d", v) for v in values)).hexdigest()


def selected_state(panel, suite, expected):
    require(panel["suite"] == suite and panel["split"] == "development" and panel["environment_seed"] == 0, "development panel identity")
    rows = [r for r in panel["states"] if r["task_id"] == 0]
    require(rows, "task0 development state missing")
    row = min(rows, key=lambda r: r["source_state_index"])
    require(sum(r["source_state_index"] == row["source_state_index"] for r in rows) == 1, "duplicate selected development row")
    require(row["source_state_index"] == STATE_INDICES[suite] and row["initial_state_sha256"] == state_hash(row["initial_state"]), "minimum development index/state SHA")
    require(signature(row) == expected["row_canonical_sha256"] and len(row["initial_state"]) == expected["vector_length"]
        and {k: v for k, v in row.items() if k != "initial_state"} == {k: v for k, v in expected.items() if k not in {"row_canonical_sha256", "vector_length"}}, "exact development row differs")
    return copy.deepcopy(row)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(Path(path).read_bytes(), str(path), "exec"), module.__dict__)
    return module


def prepare(project, source, manifest_path, expected_manifest_sha):
    """CPU-only existing metadata verification. Does not import torch or an env."""
    e = Evidence(project, source)
    manifest = e.json(manifest_path, expected_manifest_sha)
    require(manifest["schema"] == "formal_main_v2" and manifest["version"] == VERSION
        and manifest["candidate_only"] is True and manifest["gpu_submission_authorized"] is False
        and tuple(manifest["suite_order"]) == SUITES and tuple(manifest["method_order"]) == METHODS
        and manifest["limits"] == LIMITS and set(manifest["suites"]) == set(SUITES), "candidate scope differs")
    inv = e.reference(manifest["source_inventory"])
    require(manifest["source_inventory"]["sha256"] == INVENTORY_SHA and len(inv["files"]) == 173
        and inv["source_sha256"] == SOURCE_SHA
        and hashlib.sha256(json.dumps(inv["files"], sort_keys=True).encode()).hexdigest() == SOURCE_SHA, "frozen source identity")
    for name, digest in inv["files"].items():
        e.bytes(name, digest, source=True)
    for name, digest in manifest["read_evidence_sha256"].items():
        e.bytes(name, digest, panels=name in PANELS.values())
    require(manifest["action_adapter"]["sha256"] == ADAPTER_SHA, "action adapter differs")
    require(manifest["action_adapter"]["path"] == "results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py", "published action adapter path differs")
    for name, (digest, status) in ADAPTER_CPU.items():
        require(manifest[name]["sha256"] == digest and e.reference(manifest[name])["status"] == status,
            "published CPU action-adapter gate differs")
    # Exact root-provided Python 3.11 CPU proof; not a GPU acceptance.
    require(manifest["constructor_server_cpu"]["sha256"] == "15ba7a1dae8326a03d30f255282d176b5ac173be6491ad66014ea4fa84f5fc80", "constructor server CPU SHA differs")
    server_cpu = e.reference(manifest["constructor_server_cpu"])
    check = json.loads(server_cpu["stdout"])
    require(server_cpu["exit_code"] == server_cpu["SSH_exit_code"] == server_cpu["GPU_seconds"] == 0
        and check["status"] == "passed_CPU_only" and check["checks_passed"] == 16
        and check["candidate_sha256"] == ADAPTER_SHA and check["source173_unchanged"] is True
        and check["no_GPU_calls"] is True, "constructor server CPU gate differs")
    reg = e.reference(manifest["formal_registration"])
    states = {}
    for suite, row in manifest["suites"].items():
        require(row["spec"] == reg["suites"][suite] and row["panel"]["path"] == PANELS[suite], "suite registration/panel path differs")
        panel = e.reference(row["panel"], panels=True)
        states[suite] = selected_state(panel, suite, row["state"])
        pair = e.reference(row["pair_config"])
        registered = next(p for p in reg["pairs"] if (p["suite"], p["visual_tokens"], p["seed"]) == (suite, 128, 17))
        require((row["pair_config"]["path"], row["pair_config"]["sha256"]) == (registered["path"], registered["sha256"]), "registered seed17 pair differs")
        root, ind, server, gate = [e.reference(row[k]) for k in ("training_root", "training_independent", "selected_server", "acceptance_root")]
        require(all(x["status"] == "passed" and x["suite"] == suite for x in (root, ind, server, gate))
            and root["completed_by_arm"] == {"A": 5000, "B": 5000} and root["allowed_next_segment_end"] is None
            and ind["allowed_next_segment_end"] is None and server["remote_returncode"] == 0, "complete own-suite training/acceptance required")
        require(ind["read_evidence_sha256"][row["training_root"]["path"]] == row["training_root"]["sha256"]
            and server["input_sha256"][row["training_root"]["path"]] == row["training_root"]["sha256"], "final proof chain differs")
        require(tuple(m["identity"]["method_id"] for m in row["methods"]) == METHODS, "four fixed methods required")
        for method in row["methods"]:
            identity = method["identity"]
            require(identity["suite"] == suite and identity["future_head_deployed"] is False, "cross-suite/future-head identity")
            if identity["method"] not in ("A", "B"):
                continue
            arm = identity["method"]; receipt = e.reference(method["receipt"]); report = e.reference(method["training_report"])
            points = receipt["evaluations"]; best = min(points, key=lambda r: (r["validation_metric"], r["update"]))
            saved = next(r for r in server["server_selected_checks"] if r["arm"] == arm)
            require([p["update"] for p in points] == list(range(0, 5001, 500)) and receipt["completed_updates"] == 5000
                and receipt["training_complete"] and receipt["pair_config"] == pair and report["training_updates_completed"] == 5000
                and receipt["metadata"]["update"] == report["best_update"] == method["selected_update"] == best["update"]
                and saved["stable_during_hash"] and saved["exists"] and saved["bytes"] == method["checkpoint_bytes"]
                and saved["path"] == method["checkpoint"] == registered["checkpoint_root_server"] + f"/{arm}/best.pt"
                and saved["sha256"] == receipt["checkpoint_sha256"] == identity["checkpoint_sha256"] == report["best_checkpoint_sha256"]
                and identity["training_seed"] == 17 and identity["visual_tokens"] == 128, "selected checkpoint chain differs")
            for key in ("receipt", "training_report"):
                ref = method[key]
                require(root["files"][ref["path"]] == server["input_sha256"][ref["path"]] == ref["sha256"], "selected artifact SHA chain")
        expected_keys = ({"runtime_compatibility", "component_compatibility"} if suite == "libero_goal" else
            {"runtime_compatibility"} if suite == "libero_object" else set())
        require(set(row["compatibility"]) == expected_keys, "suite compatibility scope differs")
        for key, contract in row["compatibility"].items():
            require(root[key] == gate[key] == contract and len(contract["files"]) == (4 if key == "component_compatibility" else 6), "acceptance/training compatibility differs")
            for name, digest in contract["files"].items():
                e.bytes(name, digest)
    e.unchanged()
    return dict(evidence=e, manifest=manifest, states=states, inventory=inv, registration=reg)


class Journal:
    def __init__(self, output, job, limit):
        self.path = Path(output) / "events.jsonl"
        self.stream = self.path.open("xb")
        self.job, self.limit, self.started, self.events = job, limit, time.monotonic(), []
        self.context = {}

    def emit(self, event, **fields):
        require(not set(fields).intersection({"schema", "kind", "version", "job_id", "seq", "utc", "elapsed_seconds", "event"}),
            "event attempts to replace immutable journal identity")
        require(all(key not in fields or fields[key] == value for key, value in self.context.items()),
            "event context conflicts with active suite/method")
        row = dict(schema="formal_main_v2", kind="bounded_action_execution_acceptance_event", version=VERSION,
            job_id=self.job, seq=len(self.events), utc=datetime.now(timezone.utc).isoformat(),
            elapsed_seconds=time.monotonic()-self.started, event=event)
        row.update(self.context); row.update(fields)
        self.stream.write(encoded(row) + b"\n"); self.stream.flush(); os.fsync(self.stream.fileno())
        self.events.append(row)

    def deadline(self):
        require(time.monotonic()-self.started < self.limit, "registered wall limit reached")

    def close(self):
        self.stream.close()


def publish(output, name, value):
    path = Path(output) / name
    with path.open("xb") as stream:
        stream.write(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False).encode() + b"\n")
        stream.flush(); os.fsync(stream.fileno())
    return dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size)


class GlobalBudget:
    def __init__(self):
        self.counts = dict(policy=0, vla_backbone=0, vision=0)

    def consume(self, key):
        require(self.counts[key] < 16, "seventeenth policy/model call forbidden")
        self.counts[key] += 1


class EnvironmentAudit:
    """Observe original loop input before env.step, never clip or substitute it."""
    def __init__(self, env, state, dummy_action, journal):
        self.env, self.state, self.dummy, self.journal = env, state, list(dummy_action), journal
        self.resets, self.sets, self.attempts, self.confirmed = 0, 0, 0, 0
        self.queue = None

    def reset(self):
        require(self.resets == 0, "more than one independent reset")
        self.resets += 1
        self.journal.emit("environment_reset")
        return self.env.reset()

    def set_init_state(self, value):
        require(self.resets == 1 and self.sets == 0 and state_hash(value.tolist()) == self.state["initial_state_sha256"], "reset development state differs")
        self.sets += 1
        self.journal.emit("initial_state_set", initial_state_sha256=self.state["initial_state_sha256"])
        return self.env.set_init_state(value)

    def step(self, action):
        self.journal.deadline()
        require(self.attempts == self.confirmed and self.attempts < 18 and self.sets == 1, "extra or retried environment step")
        index = self.attempts
        if index < 10:
            expected, kind = self.dummy, "wait"
        else:
            require(self.queue is not None and index-10 < len(self.queue), "control action without unique original chunk")
            expected, kind = self.queue[index-10], "control"
        actual = list(action)
        require(encoded(actual) == encoded(expected), "env.step action differs from original PolicyChunk queue")
        self.journal.emit("environment_step_start", step_kind=kind, step_index=index, action=actual,
            original_action_sha256=signature(expected), unchanged=True)
        self.attempts += 1
        result = self.env.step(action)
        require(len(result) == 4, "unexpected environment step API")
        self.confirmed += 1
        self.journal.emit("environment_step_end", step_kind=kind, step_index=index, confirmed_steps=self.confirmed,
            environment_done=bool(result[2]))
        return result


def check_controller(controller, expected):
    require(controller["controller_type"] == expected["controller_type"] and controller["actual_use_delta"] is True
        and controller["actual_delta_branch_enabled"] is True and controller["set_goal_dispatches_to_bound_scale_action"] is True
        and controller["limits"] == expected["limits"], "actual controller class/delta/limits/dispatch differs")


def validate_scope_events(events):
    """Successful capture requires raw restoration evidence, not only no exception."""
    def rows(name, suite=None):
        return [r for r in events if r["event"] == name and (suite is None or r.get("suite") == suite)]
    starts, ends = rows("action_execution_candidate_enter"), rows("action_execution_candidate_exit")
    require(len(starts) == len(ends) == 1, "one action execution scope required")
    end = ends[0]
    require(end["identity_sha256"] == starts[0]["identity"]["identity_sha256"]
        and all(end.get(k) is True for k in ("original_bindings_restored", "scope_binding_and_code_intact",
            "finite_shape_and_observation_helpers_intact", "source_inputs_unchanged",
            "policy_chunk_construction_intact", "policy_chunk_construction_restored"))
        and end.get("fresh_runtime_required") is False and end.get("runner_raised") is False
        and end.get("changed_inputs") == [], "action execution scope was not intact/restored")
    for suite in SUITES:
        metadata = suite in ("libero_object", "libero_goal")
        for event in ("asset_metadata_compat_enter", "asset_metadata_compat_load_start", "asset_metadata_compat_load_complete", "asset_metadata_compat_exit"):
            require(len(rows(event, suite)) == int(metadata), "unexpected metadata scope/call count")
        if metadata:
            end = rows("asset_metadata_compat_exit", suite)[0]
            require(all(end.get(k) is True for k in ("original_loader_restored", "directory_verifier_unchanged",
                "binding_intact", "original_loader_code_unchanged", "directory_verifier_code_unchanged", "frozen_source_and_inputs_unchanged"))
                and end.get("runner_raised") is False and end.get("passthrough_calls") == 0
                and end.get("adapted_calls_attempted") == end.get("adapted_calls_completed") == 1,
                "metadata loader scope was not intact/restored")
        goal = suite == "libero_goal"
        for event, count in (("goal_component_compat_enter", 1), ("goal_component_load_start", 2),
                ("goal_component_load_complete", 2), ("goal_component_compat_exit", 1)):
            require(len(rows(event, suite)) == (count if goal else 0), "unexpected Goal component scope/call count")
        if goal:
            end = rows("goal_component_compat_exit", suite)[0]
            require(all(end.get(k) is True for k in ("original_loader_restored", "original_function_codes_unchanged",
                "binding_intact", "torch_load_unchanged", "source_inputs_unchanged", "component_files_unchanged"))
                and end.get("runner_raised") is False and end.get("rejected_calls") == 0
                and end.get("component_calls_attempted") == end.get("component_calls_completed") == 2,
                "Goal component scope was not intact/restored")
            require([r["call_id"] for r in rows("goal_component_load_start", suite)] == [0, 1]
                and [r["call_id"] for r in rows("goal_component_load_complete", suite)] == [0, 1], "Goal component call order differs")
    require(not any(r["event"].endswith(("_failed", "_rejected")) for r in events), "failed/rejected compatibility event")


@contextmanager
def counted_function(module, name, counts, key, maximum):
    original = getattr(module, name); code = original.__code__
    def observe(*args, **kwargs):
        require(getattr(module, name) is observe and original.__code__ is code, "counted source function changed")
        require(counts[key] < maximum, "repeated " + key + " forbidden")
        counts[key] += 1
        return original(*args, **kwargs)
    setattr(module, name, observe)
    try:
        yield
    finally:
        intact = getattr(module, name) is observe and original.__code__ is code
        original.__code__ = code; setattr(module, name, original)
        require(intact, "counted function changed; restored original")


@contextmanager
def policy_counters(policy, components, budget):
    from cti_vla.models import openvla_oft_policy
    from cti_vla.training import formal_future
    counts = dict(vla_backbone=0, vision=0, action_head=0, scorer=0, topk=0, packing=0)
    handles = []
    modules = [("vla_backbone", components.vla.language_model.model), ("vision", components.vla.vision_backbone),
        ("action_head", components.action_head.model)]
    if policy.selector is not None:
        modules.append(("scorer", policy.selector.estimator))
    try:
        for key, module in modules:
            def count(_module, _inputs, key=key):
                require(counts[key] == 0, "second " + key + " forward forbidden before execution")
                if key in ("vla_backbone", "vision"):
                    budget.consume(key)
                counts[key] += 1
            handles.append(module.register_forward_pre_hook(count))
        with counted_function(openvla_oft_policy, "pack_equal_length", counts, "packing", 1), \
                counted_function(formal_future, "formal_hard_select", counts, "topk", int(policy.selector is not None)):
            yield counts
    finally:
        for handle in handles:
            handle.remove()


def run_cell(runtime, policy, env, instruction, state, identity, journal, budget, counter_context):
    """Call only the scoped original loop: max_steps8 forces exactly one chunk."""
    import numpy as np
    gate = EnvironmentAudit(env, state, runtime.DUMMY_ACTION, journal)
    calls = []; observation_sha = None
    class CheckedPolicy:
        def reset(self):
            policy.reset()
        def __call__(self, observation, text):
            nonlocal observation_sha
            require(not calls and gate.confirmed == 10 and gate.attempts == 10, "policy outside first single-chunk boundary")
            budget.consume("policy"); journal.deadline()
            observation_sha = runtime._observation_hash(observation)
            journal.emit("policy_start", observation_sha256=observation_sha, instruction_sha256=hashlib.sha256(text.encode()).hexdigest(), identity=identity)
            with counter_context() as counts:
                chunk = policy(observation, text)
            require(isinstance(chunk, runtime.PolicyChunk), "original PolicyChunk required")
            require(runtime._observation_hash(observation) == observation_sha, "policy input mutated")
            meta = dict(chunk.metadata); learned = identity["method"] in ("A", "B")
            expected = dict(vla_backbone=1, vision=1, action_head=1, scorer=int(learned), topk=int(learned), packing=1)
            require(dict(counts) == expected, "observed model/selection/packing counts differ")
            require(meta["schema"] == "formal_main_v2" and meta["suite"] == identity["suite"] and meta["method"] == identity["method"]
                and meta["visual_tokens"] == identity["visual_tokens"] and meta["future_head_calls"] == 0
                and meta["policy_calls"] == meta["vision_calls"] == meta["packing_calls"] == 1
                and meta["scorer_calls"] == int(learned) and meta["language_cache"] == "disabled", "formal deployment metadata differs")
            indices = meta["retained_indices"]; count = identity["visual_tokens"]
            require(indices == sorted(set(indices)) and len(indices) == count and all(type(i) is int and 0 <= i < 512 for i in indices)
                and sum(i < 256 for i in indices) == count//2, "hard ordered equal-view packing differs")
            if learned:
                require(meta["selector_checkpoint_sha256"] == identity["checkpoint_sha256"] and meta["training_seed"] == 17, "selected checkpoint deployed differs")
            gate.queue = chunk.environment_actions.tolist()
            calls.append(dict(counts))
            journal.emit("policy_chunk", normalized_actions=chunk.normalized_actions.tolist(), environment_actions=gate.queue,
                metadata=meta, observed_counts=dict(counts), future_head_constructed=False,
                future_head_evidence="Frozen loader constructs estimator only; no future-head object or state is loaded")
            return chunk
    result = runtime.run_episode(gate, CheckedPolicy(), instruction, state["initial_state"], wait_steps=10, max_steps=8, policy_watchdog_seconds=60)
    journal.emit("bounded_episode_return", raw_frozen_result=result, attempted_environment_steps=gate.attempts, confirmed_environment_steps=gate.confirmed)
    require(result["status"] == "completed", "bounded engineering cell failed: " + str(result.get("error", result["status"])))
    require(len(calls) == result["policy_calls"] == len(result["chunks"]) == 1 and gate.resets == gate.sets == 1
        and result["wait_steps"] == 10 and 1 <= result["control_steps"] <= 8
        and gate.confirmed == gate.attempts == 10+result["control_steps"]
        and result["executed_actions"] == gate.queue[:result["control_steps"]], "bounded reset/chunk/step evidence differs")
    return dict(method_id=identity["method_id"], identity=identity, observation_sha256=observation_sha,
        actual_control_steps=result["control_steps"], unexecuted_chunk_tail=gate.queue[result["control_steps"]:],
        raw_result=result, observed_counts=calls[0], no_external_action_transform=True)


def validate_cpu_reviews(project, reg, probe_sha, manifest_sha):
    require(set(reg["cpu_reviews"]) == {"action_adapter_independent", "candidate_independent", "root_acceptance"}, "pending CPU prerequisite")
    identity = dict(probe_sha256=probe_sha, manifest_sha256=manifest_sha, action_adapter_sha256=ADAPTER_SHA)
    expected = {
        "candidate_independent": ("bounded_action_execution_GPU_candidate_independent_CPU_review", "passed_CPU_independent_review_pending_registered_GPU"),
        "root_acceptance": ("bounded_action_execution_GPU_candidate_root_CPU_review", "passed_CPU_root_review_pending_registered_GPU"),
    }
    for name, value in reg["cpu_reviews"].items():
        p = metadata_path(project, value["path"])
        require(sha(p) == value["sha256"], "CPU review SHA differs")
        receipt = json.loads(p.read_bytes())
        if name == "action_adapter_independent":
            digest, status = ADAPTER_CPU["action_adapter_independent_review"]
            require(value["sha256"] == digest and value["accepted_status"] == receipt["status"] == status
                and receipt["schema"] == "formal_main_v2" and receipt["kind"] == "action_constructor_identity_independent_CPU_review"
                and receipt.get("candidate_sha256") == ADAPTER_SHA,
                "published adapter independent CPU gate differs")
            continue
        kind, status = expected[name]
        require(receipt.get("schema") == "formal_main_v2" and receipt.get("kind") == kind and receipt.get("version") == VERSION
            and receipt.get("status") == value["accepted_status"] == status and receipt.get("candidate_identity") == identity,
            "candidate CPU gate type or current bytes differ")
        refs = receipt.get("candidate_files", {})
        require(set(refs) == {"probe", "manifest", "action_adapter"}, "candidate CPU gate file identity missing")
        for key, digest in (("probe", probe_sha), ("manifest", manifest_sha), ("action_adapter", ADAPTER_SHA)):
            ref = refs[key]; metadata_path(project, ref["path"])
            require(ref["sha256"] == digest and receipt.get("evidence_sha256", {}).get(ref["path"]) == digest,
                "candidate CPU evidence map differs")
        require(refs["action_adapter"]["path"] == "results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py", "CPU adapter source path differs")
        if name == "root_acceptance":
            ref = reg["cpu_reviews"]["candidate_independent"]
            require(receipt.get("candidate_independent_review") == {k:ref[k] for k in ("path", "sha256")},
                "root CPU gate did not bind exact independent review")


def validate_gpu_registration(args, manifest_sha):
    require(args.execute_gpu and re.fullmatch(r"[0-9]+", args.job_id or "") and os.environ.get("SLURM_JOB_ID") == args.job_id,
        "explicit fresh root Slurm GPU invocation required")
    require(Path(args.project_root) == PROJECT and Path(args.source_root) == PROJECT/"snapshots"/SOURCE_NAME, "registered server/snapshot required")
    path = metadata_path(PROJECT, args.gpu_registration)
    require(sha(path) == args.gpu_registration_sha256, "root GPU registration SHA differs")
    reg = json.loads(path.read_bytes())
    require(reg["schema"] == "formal_main_v2" and reg["version"] == GPU_VERSION
        and reg["status"] == "registered_single_attempt" and reg["gpu_submission_authorized"] is True
        and reg["candidate_manifest"] == dict(path=args.manifest, sha256=manifest_sha)
        and reg["entrypoint"] == dict(path=str(Path(__file__).resolve()), sha256=args.script_sha256)
        and sha(__file__) == args.script_sha256 and reg["limits"] == LIMITS
        and reg.get("output_root") == str(PROJECT/"results/formal_main_v2/engineering"/GPU_VERSION)
        and "output" not in reg
        and tuple(reg["suite_order"]) == SUITES and tuple(reg["method_order"]) == METHODS
        and reg["gpus"] == 1 and reg["attempt"] == 1 and reg["automatic_retry"] is False, "root engineering invocation contract differs")
    validate_cpu_reviews(PROJECT, reg, args.script_sha256, manifest_sha)
    return reg


class PrismaticProcessLifecycle:
    """One frozen installer per fresh process; subsequent frozen-loader validation."""
    NAMES = frozenset(("prismatic", "prismatic.training", "prismatic.training.train_utils",
        "prismatic.vla", "prismatic.vla.constants"))

    def __init__(self, checkpoints):
        require(len(checkpoints) == 4 and len(set(map(str, checkpoints))) == 4,
            "exact four own-suite checkpoints required")
        self.checkpoints = tuple(map(str, checkpoints))
        self.completed = 0
        self.failed = False
        self.modules = None
        self.attributes = None
        self.codes = None

    @staticmethod
    def current():
        return {name: module for name, module in sys.modules.items()
            if name == "prismatic" or name.startswith("prismatic.")}

    def verify(self):
        require(self.modules is not None and set(self.current()) == self.NAMES,
            "runtime module membership changed")
        for name, module in self.modules.items():
            require(sys.modules.get(name) is module, "runtime module identity changed")
            attrs = self.attributes[name]
            require(set(vars(module)) == set(attrs) and
                all(getattr(module, key) is value for key, value in attrs.items()),
                "runtime module attribute changed")
            require(module.__name__ == name and module.__loader__ is None and
                module.__spec__.name == name and module.__spec__.loader is None,
                "runtime module provenance changed")
            package = name in ("prismatic", "prismatic.training", "prismatic.vla")
            require(module.__package__ == (name if package else name.rsplit(".", 1)[0]),
                "runtime module package changed")
            require((module.__path__ == [] and module.__spec__.submodule_search_locations == [])
                if package else module.__spec__.submodule_search_locations is None,
                "runtime module search path changed")
        for function, code in self.codes:
            require(function.__code__ is code, "runtime helper implementation changed")

    def load(self, loader, checkpoint, *, device):
        try:
            require(not self.failed and self.completed < 4, "runtime lifecycle is failed or exhausted")
            require(str(checkpoint) == self.checkpoints[self.completed], "suite checkpoint order changed")
            first = self.completed == 0
            if first:
                require(not self.current(), "fresh process contains unregistered prismatic modules")
            else:
                self.verify()
            value = loader(checkpoint, device=device, use_minimal_prismatic_compat=first)
            if first:
                self.modules = self.current()
                require(set(self.modules) == self.NAMES, "first load did not install the exact frozen modules")
                self.attributes = {name: dict(vars(module)) for name, module in self.modules.items()}
                helpers = self.modules["prismatic.training.train_utils"]
                self.codes = [(getattr(helpers, name), getattr(helpers, name).__code__)
                    for name in ("get_current_action_mask", "get_next_actions_mask")]
            self.verify()
            self.completed += 1
            return value
        except BaseException:
            self.failed = True
            raise

    def finish(self):
        try:
            require(not self.failed and self.completed == 4, "incomplete runtime lifecycle")
            self.verify()
        except BaseException:
            self.failed = True
            raise


def gpu_body(prepared, project, source, output, journal, shared, adapter):
    """Only called after external preregistration; never used by CPU tests."""
    e, manifest = prepared["evidence"], prepared["manifest"]
    cache = Path(output)/"hf_cache"
    for path in (cache, cache/"hub", cache/"modules"):
        path.mkdir(parents=True, exist_ok=True)
    os.environ.update(HF_HOME=str(cache), HF_HUB_CACHE=str(cache/"hub"), HF_MODULES_CACHE=str(cache/"modules"),
        HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
        LIBERO_CONFIG_PATH=manifest["server_paths"]["libero_config"])
    import numpy as np
    import torch
    from transformers import AutoProcessor
    from cti_vla.evaluation import libero_runtime, formal_runtime, formal_trials, checkpoint_manifest
    from cti_vla.training.formal_future import formal_source_hashes
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.evaluation.formal_acceptance import (require_formal_acceptance, require_formal_input_acceptance,
        select_formal_acceptance_windows, verify_formal_operator_journal, module_parameter_sha256)
    from cti_vla.evaluation.future_input_acceptance import verify_input_acceptance_journal
    from cti_vla.training.formal_resume_acceptance import require_formal_resume_acceptance, verify_resume_journal
    from cti_vla.data.formal_windows import load_formal_protocol, load_formal_windows
    actual = dict(torch=torch.__version__, python=platform.python_version(), gpu=torch.cuda.get_device_name(), cuda=torch.version.cuda, numpy=np.__version__)
    require(torch.cuda.device_count() == 1 and actual == manifest["runtime"], "registered single-L40 runtime differs")
    torch.cuda.set_device(0); sources = formal_source_hashes(source)
    runtime_source = {k: shared.verify_runtime_checkout(Path(manifest["server_paths"][name]), manifest["official_source_verification"][k], e)
        for k, name in (("libero", "libero_source"), ("openvla_oft", "oft_source"))}
    journal.emit("official_runtime_verified", source_verification=runtime_source)
    cfg = Path(manifest["server_paths"]["libero_config"])/"config.yaml"
    require(cfg.is_file(), "existing LIBERO config required"); e.seen[str(cfg)] = sha(cfg)
    from libero.libero import benchmark, get_libero_path
    from libero.libero.envs import OffScreenRenderEnv
    import libero.libero as installed_libero
    import robosuite
    require(Path(manifest["server_paths"]["libero_source"]).resolve() in Path(installed_libero.__file__).resolve().parents
        and robosuite.__version__ == manifest["actual_controller_evidence"]["reference_robosuite_version"], "pinned environment import differs")
    budget, results = GlobalBudget(), []
    lifecycle = PrismaticProcessLifecycle([manifest["suites"][s]["spec"]["model_root_server"] for s in SUITES])
    with adapter.install_action_execution_compat(project_root=project, source_root=source, runtime_module=libero_runtime,
            formal_trials_module=formal_trials, expected_adapter_sha256=ADAPTER_SHA, emit=journal.emit) as action_identity:
        publish(output, "action_execution_identity.json", action_identity)
        for suite in SUITES:
            journal.deadline(); journal.context = {"suite": suite}
            row = manifest["suites"][suite]; spec = row["spec"]; gate = row["acceptance"]
            pair = e.reference(row["pair_config"])
            protocol = load_formal_protocol(project/spec["protocol"], project_root=project)
            windows = load_formal_windows(project/spec["windows"], protocol)
            fixed = select_formal_acceptance_windows(windows, protocol)
            f00 = e.reference(gate["input_acceptance.json"]); f01 = e.reference(gate["f01_k128.json"]); f03 = e.reference(gate["resume_acceptance.json"])
            require_formal_input_acceptance(f00, config=pair, window_manifest_sha256=row["windows"]["sha256"],
                data_protocol_sha256=row["protocol"]["sha256"], asset_manifest_sha256=row["model_manifest"]["sha256"], source_files=sources, selected_windows=fixed)
            verify_input_acceptance_journal(project/gate["input_calls.jsonl"]["path"], f00)
            require_formal_acceptance(f01, config=pair, window_manifest_sha256=row["windows"]["sha256"],
                input_acceptance_sha256=gate["input_acceptance.json"]["sha256"], source_files=sources, selected_windows=fixed)
            verify_formal_operator_journal(project/gate["operator_calls.jsonl"]["path"], f01)
            require_formal_resume_acceptance(f03, config=pair, window_manifest_sha256=row["windows"]["sha256"],
                input_acceptance_sha256=gate["input_acceptance.json"]["sha256"], source_files=sources, selected_windows=fixed[:2], frozen_model_sha256=f00["frozen_model_sha256"])
            verify_resume_journal(project/gate["f03_calls.jsonl"]["path"], f03)
            with ExitStack() as compatibility:
                contract = row["compatibility"]
                if "runtime_compatibility" in contract:
                    c = contract["runtime_compatibility"]; meta = load_module(project/c["adapter"], "_engineering_metadata_adapter_"+suite)
                    compatibility.enter_context(meta.install_asset_metadata_compat(project_root=project, source_root=source,
                        registration_path=project/c["registration"], expected_adapter_sha256=c["files"][c["adapter"]], emit=journal.emit))
                if "component_compatibility" in contract:
                    c = contract["component_compatibility"]; goal = load_module(project/c["adapter"], "_engineering_goal_component_adapter")
                    compatibility.enter_context(goal.install_goal_component_compat(project_root=project, source_root=source, contract=c, emit=journal.emit))
                asset = checkpoint_manifest.load_checkpoint_manifest(source/spec["model_manifest"])
                checkpoint = Path(spec["model_root_server"])
                before = checkpoint_manifest.verify_checkpoint_directory(checkpoint, asset)
                journal.emit("base_load_start", checkpoint=str(checkpoint), asset_revision=asset.revision)
                components = lifecycle.load(load_openvla_oft_components, checkpoint, device=torch.device("cuda:0"))
                journal.emit("runtime_compat_lifecycle_verified", suite_index=lifecycle.completed - 1, minimal_installed_this_load=lifecycle.completed == 1)
                require(module_parameter_sha256(components) == f00["frozen_model_sha256"], "own-suite frozen base differs")
                processor = AutoProcessor.from_pretrained(checkpoint, trust_remote_code=True, local_files_only=True)
                journal.emit("base_load_complete", frozen_model_sha256=f00["frozen_model_sha256"])
            selected = {}
            for item in row["methods"]:
                identity = item["identity"]
                if identity["method"] in ("A", "B"):
                    receipt = e.reference(item["receipt"])
                    expected = dict(suite=suite, model_revision=asset.revision, stats_key=suite+"_no_noops",
                        input_version=libero_runtime.INPUTS_VERSION, packing_version=receipt["metadata"]["packing_version"],
                        visual_tokens=128, per_camera_budgets=[64,64], window_manifest_sha256=row["windows"]["sha256"],
                        input_acceptance_sha256=gate["input_acceptance.json"]["sha256"], f01_report_sha256=gate["f01_k128.json"]["sha256"],
                        frozen_model_sha256=f00["frozen_model_sha256"], data_protocol_sha256=row["protocol"]["sha256"], selection_protocol_sha256=signature(pair["selection"]))
                    chosen = formal_runtime.load_formal_selector_checkpoint(Path(item["checkpoint"]), receipt,
                        expected_versions=expected, expected_source_hashes=sources, device="cuda:0")
                    require(formal_trials.selector_instance_identity(chosen.provenance) == identity, "actual selector deployment identity differs")
                    selected[identity["method"]] = chosen
                else:
                    require(formal_trials.baseline_instance_identity(suite=suite, method=identity["method"], visual_tokens=identity["visual_tokens"],
                        model_revision=asset.revision, frozen_model_sha256=f00["frozen_model_sha256"], source_files=sources,
                        input_acceptance_sha256=gate["input_acceptance.json"]["sha256"]) == identity, "actual baseline identity differs")
            formal_runtime.validate_formal_pair(selected["A"], selected["B"])
            task = benchmark.get_benchmark_dict()[suite](task_order_index=0).get_task(0)
            require(task.name == row["state"]["task_name"], "actual task0 mapping differs")
            bddl = Path(get_libero_path("bddl_files"))/task.problem_folder/task.bddl_file
            require(str(bddl.resolve()) in e.seen, "actual BDDL not verified in pinned archive")
            same_observation = None
            for item in row["methods"]:
                identity = item["identity"]; journal.context = {"suite":suite, "method_id":identity["method_id"]}
                random.seed(17); np.random.seed(17); torch.manual_seed(17)
                env = None; journal.emit("cell_start", identity=identity, state_identity=row["state"], environment_seed=0, runtime_seed=17,
                    runtime_rng_sha256=shared.rng_digest(shared.rng_state(torch)))
                try:
                    env = OffScreenRenderEnv(bddl_file_name=str(bddl), camera_heights=256, camera_widths=256); env.seed(0)
                    controller = shared.actual_controller(env, manifest, e); check_controller(controller, manifest["controller_expected"])
                    journal.emit("actual_controller_verified", controller=controller)
                    policy = formal_runtime.FormalRolloutPolicy(components, processor, suite=suite, method=identity["method"],
                        total_tokens=identity["visual_tokens"], selector=selected.get(identity["method"]))
                    result = run_cell(libero_runtime, policy, env, task.language, prepared["states"][suite], identity,
                        journal, budget, lambda: policy_counters(policy, components, budget))
                    if same_observation is None:
                        same_observation = result["observation_sha256"]
                    require(result["observation_sha256"] == same_observation, "independent reset produced different first observation")
                    after_controller = shared.actual_controller(env, manifest, e)
                    require(after_controller == controller, "controller changed inside bounded cell")
                    results.append(dict(suite=suite, **result)); journal.emit("cell_complete", result=result, controller_identity_unchanged=True)
                finally:
                    if env is not None:
                        env.close()
            require(before == checkpoint_manifest.verify_checkpoint_directory(checkpoint, asset)
                and module_parameter_sha256(components) == f00["frozen_model_sha256"], "frozen base changed")
            for item in row["methods"]:
                if "checkpoint" in item:
                    require(sha(item["checkpoint"]) == item["identity"]["checkpoint_sha256"], "selected checkpoint changed")
            del policy, selected, components, processor
            gc.collect(); torch.cuda.empty_cache()
            journal.context = {"suite":suite}; journal.emit("suite_complete", models_unchanged=True)
        lifecycle.finish()
        require(len(results) == 16 and budget.counts == dict(policy=16, vla_backbone=16, vision=16), "incomplete16-cell engineering capture")
    journal.context = {}
    validate_scope_events(journal.events)
    return dict(runtime=actual, cells=results, global_counts=budget.counts, actual_cells=16,
        total_control_steps=sum(r["actual_control_steps"] for r in results), success_rate_computed=False,
        latency_claim=False, scientific_complete=False, previous_results_replaced=False)


def execute(args):
    # Nothing below runs from import or from the CPU inspector.
    gpu_reg = validate_gpu_registration(args, args.manifest_sha256)
    project, source = Path(args.project_root), Path(args.source_root)
    require(not any(n == "cti_vla" or n.startswith("cti_vla.") for n in sys.modules), "fresh frozen-source process required")
    output = Path(gpu_reg["output_root"])/args.job_id
    output.mkdir(parents=True, exist_ok=False)
    journal = Journal(output, args.job_id, LIMITS["wall_seconds"])
    prepared = None; result = None; error = None; code = 1
    try:
        journal.emit("engineering_start", candidate_sha256=args.script_sha256, manifest_sha256=args.manifest_sha256,
            root_registration_sha256=args.gpu_registration_sha256, no_retry=True, expected_cells=16, limits=LIMITS)
        prepared = prepare(project, source, args.manifest, args.manifest_sha256)
        e, manifest = prepared["evidence"], prepared["manifest"]
        e.seen[str(Path(__file__).resolve())] = args.script_sha256
        e.bytes(args.gpu_registration, args.gpu_registration_sha256)
        for ref in gpu_reg["cpu_reviews"].values():
            e.bytes(ref["path"], ref["sha256"])
        shared = load_module(project/manifest["shared_probe"]["path"], "_bounded_acceptance_shared_probe")
        adapter = load_module(project/manifest["action_adapter"]["path"], "_bounded_acceptance_action_adapter")
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(source/"src"))
        for key in ("libero_source", "oft_source"):
            sys.path.insert(0, manifest["server_paths"][key])
        publish(output, "inputs.json", dict(manifest_sha256=args.manifest_sha256, watched_files=e.seen))
        with shared.reject_state_file_reads():
            result = gpu_body(prepared, project, source, output, journal, shared, adapter)
        e.unchanged(); journal.deadline(); code = 0
    except BaseException as exc:
        error = dict(type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
        journal.emit("engineering_failure", error=error)
    finally:
        unchanged = False
        if prepared is not None:
            try:
                prepared["evidence"].unchanged(); unchanged = True
            except BaseException as exc:
                code = 1; error = dict(type=type(exc).__name__, message=str(exc), previous_error=error)
        journal.context = {}
        journal.emit("engineering_end", exit_code=code, status="captured_pending_root_review" if code == 0 else "failed",
            source_inputs_unchanged=unchanged, error=error)
        journal.close()
        publish(output, "completion.json", dict(schema="formal_main_v2", kind="bounded_action_execution_gpu_acceptance_completion",
            version=VERSION, job_id=args.job_id, status="captured_pending_root_review" if code == 0 else "failed", exit_code=code,
            candidate_sha256=args.script_sha256, manifest_sha256=args.manifest_sha256,
            root_registration_sha256=args.gpu_registration_sha256, events_sha256=sha(journal.path), events_bytes=journal.path.stat().st_size,
            result=result, error=error, source_inputs_unchanged=unchanged,
            read_evidence_sha256=prepared["evidence"].seen if prepared else {}, wall_seconds=time.monotonic()-journal.started,
            GPU_cost_status="pending_root_Slurm_terminal_accounting_including_all_failed_attempts",
            success_rate_computed=False, latency_claim=False, scientific_complete=False, final_states_opened=False,
            weights_copied=False, original_results_replaced=False, automatic_retry=False))
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--inspect-cpu", action="store_true")
    parser.add_argument("--execute-gpu", action="store_true")
    parser.add_argument("--job-id")
    parser.add_argument("--script-sha256")
    parser.add_argument("--gpu-registration")
    parser.add_argument("--gpu-registration-sha256")
    args = parser.parse_args()
    if args.inspect_cpu:
        require(not args.execute_gpu, "choose CPU inspection or registered GPU execution")
        p = prepare(args.project_root, args.source_root, args.manifest, args.manifest_sha256)
        print(json.dumps(dict(status="metadata_ready_GPU_preregistration_pending", suites=list(SUITES), cells=16,
            selected_state_indices=STATE_INDICES, verified_metadata_inputs=len(p["evidence"].seen), gpu_seconds=0)))
        return 0
    return execute(args)


if __name__ == "__main__":
    raise SystemExit(main())

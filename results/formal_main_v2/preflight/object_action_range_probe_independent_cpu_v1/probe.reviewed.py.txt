"""Registered capture-only Object diagnostic; no rollout completion or repair.

CPU tests import the pure boundaries.  The production CLI requires an explicit
GPU flag, a root-pinned script SHA, a fresh Slurm job, and the registered server
paths.  Never invoke this file to repeat or replace an original development cell.
"""
from __future__ import annotations

import argparse
import ast
import builtins
import copy
import hashlib
import importlib.util
import inspect
import io
import json
import os
from pathlib import Path
import platform
import random
import re
import struct
import sys
import textwrap
import time
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone

VERSION = "object-action-range-probe-candidate-v1"
P = Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
REG = "configs/experiments/formal_main_v2_object_action_range_probe_v1.json"
REG_SHA = "c87c76f8a3175bd760551c530f65990d08a88ab6a41d2771b44120e9cea25a3d"
SOURCE_NAME = "formal_main_v2_run_564be0995e"
PANEL = "configs/manifests/formal_main_v2/libero_object/initial_states/development.json"
INVOCATION = "results/formal_main_v2/invocations/libero_object_development_8c843c1d4ee8383c_attempt03.json"
INVOCATION_SHA = "1f4f0abc0d9dceedd051966a049c075605998102fbfd9baf7ad5a54b97c5df4e"
META = "scripts/ops/formal_asset_metadata_adapter.py"
META_REG = "configs/experiments/formal_main_v2_asset_metadata_compat_v1.json"
META_FILES = {
    META: "d1ca08465ffcf2682569b1224e2018f17fdba61feac1896f864cc981759397d0",
    META_REG: "25c90cbfe2db6fdb130a16e6b98ab7ccfc8373a2853578bf73ef0d38283cfb44",
    "configs/assets/formal_main_v2_strict/libero_object.json": "d8f1f9a5c1c8c040aa499fd9df35ebe4a039fd6c756b565cf6055046be0cf8b3",
    "configs/assets/formal_main_v2_strict/libero_goal.json": "e55eac83f28854318524ba87fc6554c7a9708b328700232c055deb66a72e0d6c",
    "scripts/server/run_formal_asset_stage.py": "9c49bbd536646c8b677c611328e79e7ff3a16a6bca7c5309c8e69cdce3250996",
    "scripts/server/formal_asset_main.slurm": "9d54e0486a078a8358c8443bb92db8c8096d9ac3988eff693fa69b250d97c36a",
}
PAYLOAD = {".pt", ".pth", ".bin", ".ckpt", ".safetensors", ".pkl", ".pickle", ".init", ".pruned_init"}


def utc():
    return datetime.now(timezone.utc).isoformat()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def signature(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def forbidden_state_path(value):
    """Pure lexical check; Python source names are not state-value payloads."""
    raw = os.fsdecode(value).replace("\\", "/").lower()
    parts = raw.split("/")
    leaf = parts[-1]
    return (any("sealed" in part for part in parts) or "final_registry" in raw
        or any(part in ("initial_states", "init_states", "test") for part in parts[:-1])
        or leaf.endswith((".init", ".pruned_init"))
        or (not leaf.endswith((".py", ".pyc", ".pyo"))
            and any(marker in leaf for marker in ("init_state", "initial_state", "final_state", "test_state")))
        or ("final" in parts[:-1] and leaf == "panel.json"))


def metadata_path(root, relative):
    # Lexical rejection precedes resolve/stat/open, including malicious aliases.
    raw = str(relative).replace("\\", "/")
    p = Path(raw)
    lower = raw.lower().split("/")
    if (p.is_absolute() or ":" in raw or ".." in p.parts or p.suffix.lower() in PAYLOAD
            or any("sealed" in part or part in ("weights", "checkpoints", "final") for part in lower)
            or "final_registry" in raw.lower() or p.name == "panel.json"
            or (raw != PANEL and forbidden_state_path(raw))):
        raise ValueError("unapproved metadata/state path")
    target = Path(root) / p
    if target.resolve() != target.absolute() or Path(root).resolve() not in target.resolve().parents:
        raise ValueError("metadata alias/traversal")
    return target


class Evidence:
    def __init__(self, project):
        self.project, self.seen = Path(project), {}

    def bytes(self, relative, expected=None):
        path = metadata_path(self.project, relative)
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if expected is not None and digest != expected:
            raise ValueError("evidence SHA mismatch: " + str(relative))
        if str(path) in self.seen and self.seen[str(path)] != digest:
            raise ValueError("evidence changed during read")
        self.seen[str(path)] = digest
        return data

    def json(self, relative, expected=None):
        return json.loads(self.bytes(relative, expected))

    def unchanged(self):
        for path, expected in self.seen.items():
            if sha(path) != expected:
                raise ValueError("input changed: " + path)


def state_hash(values):
    import math
    if not isinstance(values, list) or not values or not all(type(v) in (int, float) and math.isfinite(v) for v in values):
        raise ValueError("invalid state vector")
    return hashlib.sha256(b"cti-vla:libero-init-state:v1\x00" + struct.pack("<q", len(values))
        + b"".join(struct.pack("<d", v) for v in values)).hexdigest()


def select_state(panel, target):
    if panel.get("suite") != "libero_object" or panel.get("split") != "development" or panel.get("environment_seed") != 0:
        raise ValueError("development-only Object panel required")
    rows = [row for row in panel["states"] if row.get("trial_id") == target["state_trial_id"]]
    if len(rows) != 1:
        raise ValueError("target development row is not unique")
    row = rows[0]
    if (any(row.get(k) != target[k] for k in ("task_id", "task_name", "source_state_index", "initial_state_sha256"))
            or len(row["initial_state"]) != 110 or state_hash(row["initial_state"]) != target["initial_state_sha256"]):
        raise ValueError("target state identity/vector differs")
    return row


def prepare(project, source):
    """Read only nonweight evidence; no simulator/model imports or state files."""
    e = Evidence(project)
    registration = e.json(REG, REG_SHA)
    inventory = e.json(registration["fixed_identity"]["source_inventory"],
        registration["read_evidence_sha256"][registration["fixed_identity"]["source_inventory"]])
    if (len(inventory["files"]) != 173 or inventory["source_sha256"] != registration["fixed_identity"]["frozen_runtime_source_sha256"]
            or Path(source) != Path(project) / "snapshots" / SOURCE_NAME):
        raise ValueError("frozen source identity differs")
    for name, checksum in inventory["files"].items():
        metadata_path(source, name)
        path = Path(source) / name
        if sha(path) != checksum:
            raise ValueError("frozen source bytes changed: " + name)
        e.seen[str(path)] = checksum
    for relative, checksum in registration["read_evidence_sha256"].items():
        if relative in inventory["files"]:
            if inventory["files"][relative] != checksum:
                raise ValueError("historical source reference differs from frozen snapshot")
            # Exact-byte historical references resolve to the registered snapshot;
            # no dependency on mutable project/src copies on the server.
            continue
        e.bytes(relative, checksum)
    for relative, checksum in META_FILES.items():
        e.bytes(relative, checksum)
    original = registration["original_evidence"]
    diagnosis = e.json(original["root_diagnosis"])
    config = e.json(original["raw_config"])
    archive = e.json(original["immutable_archive"])
    ledger = e.bytes(original["raw_ledger"])
    if not ledger.endswith(b"\n"):
        raise ValueError("incomplete original ledger")
    matches = [json.loads(line) for line in ledger.splitlines() if original["trial_id"].encode() in line]
    terminal = [r for r in matches if r.get("event") == "result" and r.get("trial_id") == original["trial_id"]]
    if len(terminal) != 1 or terminal[0] != diagnosis["policy_error"]:
        raise ValueError("diagnosis differs from the unique raw terminal record")
    record = terminal[0]
    if (record["status"] != "policy_error" or record["method"] != "dense" or record["control_steps"] != 56
            or record["policy_calls"] != 8 or len(record["executed_actions"]) != 56 or len(record["chunks"]) != 7
            or record["run_signature"] != original["run_signature"]):
        raise ValueError("registered failure boundary differs")
    checkpoints = [{"control_step": x["control_step"], "observation_sha256": x["observation_sha256"]} for x in record["chunks"]]
    if checkpoints != registration["reconstruction"]["mandatory_exact_checkpoints"] or signature(record["executed_actions"]) != registration["reconstruction"]["executed_actions_source"]["canonical_json_sha256"]:
        raise ValueError("action/checkpoint prefix differs")
    for name in (original["raw_ledger"], original["raw_config"]):
        rows = [r for r in archive["files"] if r["archive"] == name]
        if len(rows) != 1 or rows[0]["sha256"] != e.seen[str(Path(project) / name)]:
            raise ValueError("immutable archive mapping differs")
    panel = e.json(PANEL, registration["initial_state"]["source_sha256"])
    state = select_state(panel, registration["initial_state"])
    dense = next(r["identity"] for r in config["manifest"]["methods"] if r["identity"]["method_id"] == "dense")
    if (dense != registration["fixed_identity"]["dense_deployment_identity"] or config["runtime"] != registration["fixed_identity"]["runtime"]
            or config["manifest"]["environment"] != dict(action_chunk=8,environment_seed=0,max_steps=280,runtime_seed=17,wait_steps=10)):
        raise ValueError("original deployment/config differs")
    invocation = e.json(INVOCATION, INVOCATION_SHA)
    argv = invocation["argv"]
    def arg(name):
        if argv.count(name) != 1:
            raise ValueError("ambiguous original invocation argument: " + name)
        return argv[argv.index(name) + 1]
    if arg("--source-root") != inventory["source_root_server"] or arg("--development-panel") != (P / PANEL).as_posix():
        raise ValueError("original source/panel argument differs")
    f00_rel = arg("--input-acceptance").removeprefix(P.as_posix() + "/")
    f00 = e.json(f00_rel, dense["input_acceptance_sha256"])
    if f00["frozen_model_sha256"] != dense["frozen_model_sha256"] or f00["status"] != "passed" or f00["test_opened"]:
        raise ValueError("dense F00 identity differs")
    return dict(evidence=e, registration=registration, config=config, state=state, record=record,
        invocation=invocation, arg=arg, inventory=inventory, f00=f00)


@contextmanager
def reject_state_file_reads():
    """Also protect library I/O. This scope never reads even official init bytes."""
    originals = [(builtins, "open", builtins.open), (io, "open", io.open), (os, "open", os.open),
        (Path, "open", Path.open)]
    def rejected(value):
        if isinstance(value, (str, bytes, os.PathLike)):
            if forbidden_state_path(value):
                raise PermissionError("initial-state file I/O forbidden inside diagnostic runtime")
    def wrap(fn):
        def checked(file, *args, **kwargs):
            rejected(file)
            return fn(file, *args, **kwargs)
        return checked
    wrappers = [wrap(fn) for _, _, fn in originals]
    for (module, attr, _), wrapper in zip(originals, wrappers):
        setattr(module, attr, wrapper)
    try:
        yield
    finally:
        intact = all(getattr(module, attr) is wrapper for (module, attr, _), wrapper in zip(originals, wrappers))
        for module, attr, fn in originals:
            setattr(module, attr, fn)
        if not intact:
            raise RuntimeError("state-file guard was rebound")


class Journal:
    def __init__(self, output, job):
        self.path, self.job = Path(output) / "events.jsonl", job
        self.stream = self.path.open("xb")
        self.events = []
        self.started = time.monotonic()

    def emit(self, event, **fields):
        row = dict(schema="formal_main_v2", kind="action_range_probe_event", version=VERSION,
            job_id=self.job, seq=len(self.events), utc=utc(), elapsed_seconds=time.monotonic()-self.started,
            event=event, **fields)
        self.stream.write(encoded(row) + b"\n"); self.stream.flush(); os.fsync(self.stream.fileno())
        self.events.append(row)

    def deadline(self):
        if time.monotonic() - self.started >= 900:
            raise TimeoutError("registered 900-second bound reached")

    def close(self):
        self.stream.close()


def publish(output, name, value):
    path = Path(output) / name
    with path.open("xb") as f:
        f.write((json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)+"\n").encode())
        f.flush(); os.fsync(f.fileno())
    return dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size)


class ReplayEnvironment:
    def __init__(self, env, emit):
        self.env, self.emit, self.steps, self.locked = env, emit, 0, False

    def step(self, action, *, kind, index):
        if self.locked or self.steps >= 66:
            raise RuntimeError("env.step forbidden at or after control step56")
        expected_kind = "wait" if self.steps < 10 else "recorded_control"
        expected_index = self.steps if self.steps < 10 else self.steps - 10
        if kind != expected_kind or index != expected_index:
            raise ValueError("replay step order differs")
        self.emit("environment_step_start", step_kind=kind, index=index, action=list(action))
        value = self.env.step(list(action))
        self.steps += 1
        if len(value) != 4:
            raise ValueError("unexpected LIBERO step API")
        self.emit("environment_step_end", step_kind=kind, index=index, steps_confirmed=self.steps)
        if bool(value[2]):
            raise RuntimeError("premature terminal environment; reconstruction stopped")
        return value[0]


def replay_to56(env, state, actions, checkpoints, observation_hash, dummy_action, journal):
    import numpy as np
    values = np.asarray(actions)
    if values.shape != (56, 7) or not np.isfinite(values).all() or np.any(np.abs(values)>1.00001):
        raise ValueError("recorded prefix must be56 finite already-valid actions")
    if [x["control_step"] for x in checkpoints] != list(range(0, 56, 8)):
        raise ValueError("exact seven checkpoints required")
    gate = ReplayEnvironment(env, journal.emit)
    env.reset()
    observation = env.set_init_state(np.asarray(state, dtype=np.float64))
    for i in range(10):
        journal.deadline()
        observation = gate.step(dummy_action, kind="wait", index=i)
    expected = {x["control_step"]: x["observation_sha256"] for x in checkpoints}
    for i, action in enumerate(actions):
        journal.deadline()
        if i in expected:
            actual = observation_hash(observation)
            journal.emit("observation_checkpoint", control_step=i, actual_sha256=actual,
                expected_sha256=expected[i], equal=actual == expected[i])
            if actual != expected[i]:
                raise ValueError("observation checkpoint mismatch at" + str(i))
        observation = gate.step(action, kind="recorded_control", index=i)
    gate.locked = True
    journal.emit("reconstruction_complete", confirmed_environment_steps=gate.steps, recorded_control_steps=56,
        new_t56_observation_sha256=observation_hash(observation), original_t56_observation_available=False)
    return gate, observation


def rng_state(torch):
    import numpy as np
    return (random.getstate(), np.random.get_state(), torch.get_rng_state().clone(),
        [x.clone() for x in torch.cuda.get_rng_state_all()])


def restore_rng(torch, state):
    import numpy as np
    random.setstate(state[0]); np.random.set_state(state[1]); torch.set_rng_state(state[2])
    torch.cuda.set_rng_state_all(state[3])


def rng_digest(state):
    return signature([state[0], [state[1][0], state[1][1].tolist(), *state[1][2:]],
        state[2].tolist(), [x.tolist() for x in state[3]]])


def action_record(value):
    import numpy as np
    a = np.asarray(value)
    if a.shape != (8, 7) or not np.isfinite(a).all():
        raise ValueError("capture must be finite8x7")
    return dict(shape=list(a.shape), dtype=str(a.dtype), values=a.tolist(),
        bytes_sha256=hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest())


def capture_pair(observation, instruction, capture, *, snapshot_rng, reset_rng, hash_rng, observation_hash, journal):
    import numpy as np
    saved = snapshot_rng(); before_rng = hash_rng(saved); obs_sha = observation_hash(observation)
    captures = {}
    try:
        for name in ("official_native_dense", "frozen_token_dense"):
            journal.deadline(); reset_rng(saved)
            if hash_rng(snapshot_rng()) != before_rng:
                raise ValueError("RNG restoration differs")
            current = copy.deepcopy(observation)
            if observation_hash(current) != obs_sha:
                raise ValueError("paired raw input differs")
            journal.emit("capture_start", path=name, observation_sha256=obs_sha, input_rng_sha256=before_rng,
                instruction_sha256=hashlib.sha256(instruction.encode()).hexdigest())
            result = capture(name, current, instruction)
            if observation_hash(current) != obs_sha or observation_hash(observation) != obs_sha:
                raise ValueError("capture mutated input observation")
            arrays = {key: action_record(result[key]) for key in ("normalized", "physical", "postprocessed")}
            if result["calls"].get("vla_backbone") != 1 or result["calls"].get("vision") != 1:
                raise ValueError("capture must have one actual VLA/vision forward")
            post = np.asarray(result["postprocessed"])
            record = dict(arrays=arrays, calls=result["calls"], metadata=result["metadata"],
                extra_native_head_recapture=name=="official_native_dense",
                frozen_guard_rejects=bool(np.any(np.abs(post)>1.00001)),
                violating_components=[dict(row=int(i), column=int(j), value=float(post[i,j]))
                    for i,j in np.argwhere(np.abs(post)>1.00001)])
            captures[name] = record
            journal.emit("capture_complete", path=name, capture=record)
    finally:
        reset_rng(saved)
    comparisons = {}
    for layer in ("normalized", "physical", "postprocessed"):
        a, b = (np.asarray(captures[name]["arrays"][layer]["values"]) for name in captures)
        comparisons[layer] = dict(exact_equal=bool(np.array_equal(a,b)), maximum_absolute_difference=float(np.max(np.abs(a-b))))
    return dict(captures=captures, comparisons=comparisons, observation_sha256=obs_sha,
        input_rng_sha256=before_rng, total_VLA_forwards=2, future_head_calls=0, DIE_calls=0,
        env_steps_after_t56=0, success_collected=False, original_failed_values_available=False)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(Path(path).read_bytes(), str(path), "exec"), module.__dict__)
    return module


def verify_runtime_checkout(path, expected, evidence):
    """Bind original archive, verify non-state runtime bytes, never hash init files."""
    path = Path(path)
    inv_path, marker_path = path/"SOURCE_FILES.json", path/"SOURCE_REVISION.json"
    inv, marker = (json.loads(p.read_bytes()) for p in (inv_path, marker_path))
    if sha(inv_path) != expected["inventory_sha256"] or any(x["revision"] != expected["revision"] or x["archive_sha256"] != expected["archive_sha256"] for x in (inv,marker)) or len(inv["files"]) != expected["file_count"]:
        raise ValueError("official checkout archive identity differs")
    evidence.seen.update({str(inv_path):sha(inv_path),str(marker_path):sha(marker_path)})
    checked, skipped = 0, []
    for rel, checksum in inv["files"].items():
        parts = rel.lower().replace("\\","/").split("/")
        if (Path(rel).suffix.lower() in PAYLOAD or any(x in ("init_states","initial_states") or "sealed" in x for x in parts)):
            skipped.append(rel); continue
        target = metadata_path(path, rel)
        if sha(target) != checksum:
            raise ValueError("official runtime byte mismatch: " + rel)
        evidence.seen[str(target)] = checksum; checked += 1
    return dict(original_archive_identity=expected, verification="non_state_runtime_files_sha256",
        verified_files=checked, intentionally_unopened_state_or_payload_files=skipped,
        historical_full_archive_verification_only=True)


def actual_controller(env, registration, evidence):
    import numpy as np
    objects, current = [], env
    for _ in range(5):
        objects.append(current)
        if hasattr(current, "robots"):
            break
        current = getattr(current,"env",None)
        if current is None:
            raise ValueError("actual robot controller is unavailable")
    robots = current.robots
    if len(robots) != 1:
        raise ValueError("registered single robot expected")
    robot, controller = robots[0], robots[0].controller
    methods = {}
    expected = registration["actual_controller_evidence"]["installed_source_reference_from_root_diagnosis"]
    for name, relative in (("scale_action","controllers/base_controller.py"),("set_goal","controllers/osc.py")):
        bound = getattr(controller,name)
        fn = getattr(bound,"__func__",None)
        path = Path(inspect.getsourcefile(fn))
        if bound.__self__ is not controller or str(path) != expected[relative]["path"] or sha(path) != expected[relative]["sha256"]:
            raise ValueError("actual bound controller source differs")
        evidence.seen[str(path)] = sha(path)
        methods[name] = dict(path=str(path),sha256=sha(path),function=fn.__qualname__,source=inspect.getsource(fn))
    goal_ast = ast.parse(textwrap.dedent(methods["set_goal"]["source"]))
    dispatch = any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="scale_action"
        and isinstance(n.func.value,ast.Name) and n.func.value.id=="self" for n in ast.walk(goal_ast))
    use_delta = getattr(controller,"use_delta",None)
    if type(use_delta) not in (bool,np.bool_) or not dispatch:
        raise ValueError("actual delta controller dispatch cannot be established")
    config = getattr(robot,"controller_config",{})
    configured = config.get("control_delta") if isinstance(config,dict) else None
    ctor_source = inspect.getsource(type(controller).__init__)
    ctor_tree = ast.parse(textwrap.dedent(ctor_source))
    binding = any(isinstance(n,ast.Assign) and isinstance(n.value,ast.Name) and n.value.id=="control_delta"
        and any(isinstance(t,ast.Attribute) and isinstance(t.value,ast.Name) and t.value.id=="self" and t.attr=="use_delta" for t in n.targets) for n in ast.walk(ctor_tree))
    if configured is not None and bool(configured) != bool(use_delta):
        raise ValueError("actual control_delta config and use_delta disagree")
    if configured is None and not binding:
        raise ValueError("resolved control_delta cannot be bound to constructor")
    limits = {}
    for name in ("input_min","input_max","output_min","output_max"):
        a=np.asarray(getattr(controller,name))
        if a.ndim != 1 or not np.isfinite(a).all():raise ValueError("controller bounds invalid")
        limits[name]=a.tolist()
    return dict(controller_type=type(controller).__module__+"."+type(controller).__qualname__,
        control_delta=bool(use_delta),configured_control_delta=configured,actual_use_delta=bool(use_delta),
        control_delta_resolution="robot.controller_config" if configured is not None else "actual use_delta plus constructor self.use_delta=control_delta binding",
        constructor_source=ctor_source,limits=limits,methods=methods,set_goal_dispatches_to_bound_scale_action=dispatch,
        actual_delta_branch_enabled=bool(use_delta),captured_action_applied=False)


@contextmanager
def forward_counters(components):
    calls={"vla_backbone":0,"vision":0,"action_head":0}
    handles=[]
    for key,module in (("vla_backbone",components.vla.language_model.model),
            ("vision",components.vla.vision_backbone),("action_head",components.action_head.model)):
        def count(_module,_args,key=key):
            calls[key]+=1
            if key in ("vla_backbone","vision") and calls[key]>1:
                raise RuntimeError("second forward forbidden before kernel execution")
        handles.append(module.register_forward_pre_hook(count))
    try:yield calls
    finally:
        for handle in handles:handle.remove()


def gpu_body(prepared, project, source, output, journal):
    e,reg,arg=prepared["evidence"],prepared["registration"],prepared["arg"]
    cache=Path(output)/"hf_cache"
    for path in (cache,cache/"hub",cache/"modules"):path.mkdir(parents=True,exist_ok=True)
    os.environ.update(HF_HOME=str(cache),HF_HUB_CACHE=str(cache/"hub"),HF_MODULES_CACHE=str(cache/"modules"),
        HF_HUB_OFFLINE="1",TRANSFORMERS_OFFLINE="1",TOKENIZERS_PARALLELISM="false")
    os.environ["LIBERO_CONFIG_PATH"]=arg("--libero-config")
    import numpy as np
    import torch
    from transformers import AutoProcessor
    from cti_vla.evaluation import libero_runtime, formal_runtime, formal_trials
    from cti_vla.evaluation import checkpoint_manifest
    from cti_vla.evaluation.formal_acceptance import module_parameter_sha256
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.training.formal_future import formal_source_hashes
    actual=dict(torch=torch.__version__,python=platform.python_version(),gpu=torch.cuda.get_device_name(),cuda=torch.version.cuda,numpy=np.__version__)
    if torch.cuda.device_count()!=1 or actual!=reg["fixed_identity"]["runtime"]:
        raise ValueError("registered single-L40 runtime identity differs")
    torch.cuda.set_device(0)
    sources=formal_source_hashes(source)
    if sources!=prepared["config"]["source_files"]:
        raise ValueError("formal deployment source map differs")
    before_source={key:verify_runtime_checkout(Path(arg(flag)),reg["fixed_identity"]["official_source_verification"][key],e)
        for key,flag in (("libero","--libero-source"),("openvla_oft","--oft-source"))}
    journal.emit("official_runtime_verified",sources=before_source)
    config_path=Path(arg("--libero-config"))/"config.yaml"
    if not config_path.is_file():raise ValueError("existing LIBERO config required")
    e.seen[str(config_path)]=sha(config_path)
    asset_path=Path(source)/reg["fixed_identity"]["model_manifest"]
    asset=checkpoint_manifest.load_checkpoint_manifest(asset_path)
    if asset.revision!=reg["fixed_identity"]["model_revision"]:raise ValueError("asset revision differs")
    checkpoint=Path(arg("--checkpoint"))
    before=checkpoint_manifest.verify_checkpoint_directory(checkpoint,asset)
    journal.emit("base_load_start",checkpoint=str(checkpoint),asset_revision=asset.revision)
    components=load_openvla_oft_components(checkpoint,device=torch.device("cuda:0"),use_minimal_prismatic_compat=True)
    fingerprint=module_parameter_sha256(components)
    if fingerprint!=prepared["f00"]["frozen_model_sha256"]:raise ValueError("loaded frozen model differs")
    dense_identity=formal_trials.baseline_instance_identity(suite="libero_object",method="dense",visual_tokens=512,
        model_revision=asset.revision,frozen_model_sha256=fingerprint,source_files=sources,
        input_acceptance_sha256=reg["fixed_identity"]["dense_deployment_identity"]["input_acceptance_sha256"])
    if dense_identity!=reg["fixed_identity"]["dense_deployment_identity"]:raise ValueError("dense identity differs")
    processor=AutoProcessor.from_pretrained(checkpoint,trust_remote_code=True,local_files_only=True)
    reference=libero_runtime.load_official_reference_functions(arg("--oft-source"))
    native=libero_runtime.OpenVLARolloutPolicy(components,processor,stats_key="libero_object_no_noops",method="official_dense",reference=reference)
    token=formal_runtime.FormalRolloutPolicy(components,processor,suite="libero_object",method="dense",total_tokens=512)
    stats=components.vla.norm_stats["libero_object_no_noops"]["action"]
    statistics=checkpoint/"dataset_statistics.json"
    e.seen[str(statistics)]=sha(statistics)
    journal.emit("base_loaded",frozen_model_sha256=fingerprint,dense_identity=dense_identity,
        action_statistics=stats,dataset_statistics_sha256=e.seen[str(statistics)])
    from libero.libero import benchmark,get_libero_path
    from libero.libero.envs import OffScreenRenderEnv
    import libero.libero as installed_libero
    import robosuite
    if Path(arg("--libero-source")).resolve() not in Path(installed_libero.__file__).resolve().parents or robosuite.__version__!=reg["actual_controller_evidence"]["reference_robosuite_version"]:
        raise ValueError("imported environment identity differs")
    suite=benchmark.get_benchmark_dict()["libero_object"](task_order_index=0)
    task=suite.get_task(8)
    if task.name!=prepared["state"]["task_name"]:raise ValueError("task mapping differs")
    bddl=Path(get_libero_path("bddl_files"))/task.problem_folder/task.bddl_file
    if str(bddl.resolve()) not in e.seen:raise ValueError("actual BDDL was not verified in the pinned runtime archive")
    random.seed(17);np.random.seed(17);torch.manual_seed(17)
    env=None
    try:
        env=OffScreenRenderEnv(bddl_file_name=str(bddl),camera_heights=256,camera_widths=256)
        env.seed(0)
        gate,obs=replay_to56(env,prepared["state"]["initial_state"],prepared["record"]["executed_actions"],
            reg["reconstruction"]["mandatory_exact_checkpoints"],libero_runtime._observation_hash,libero_runtime.DUMMY_ACTION,journal)
        controller=actual_controller(env,reg,e)
        publish(output,"controller.json",controller);journal.emit("actual_controller_verified",controller=controller)
        def capture(name,current,instruction):
            policy=native if name=="official_native_dense" else token
            with forward_counters(components) as calls:
                chunk=policy(current,instruction)
            physical=components.vla._unnormalize_actions(chunk.normalized_actions,"libero_object_no_noops")
            if not np.array_equal(libero_runtime.postprocess_actions(physical),chunk.environment_actions):
                raise ValueError("reconstructed physical/postprocessed layers differ")
            expected_heads=2 if name=="official_native_dense" else 1
            if calls["action_head"]!=expected_heads:raise ValueError("unexpected action-head evaluation count")
            return dict(normalized=chunk.normalized_actions,physical=physical,postprocessed=chunk.environment_actions,
                calls=dict(calls),metadata=dict(chunk.metadata))
        captured=capture_pair(obs,task.language,capture,snapshot_rng=lambda:rng_state(torch),reset_rng=lambda s:restore_rng(torch,s),
            hash_rng=rng_digest,observation_hash=libero_runtime._observation_hash,journal=journal)
        if gate.steps!=66 or not gate.locked:raise ValueError("replay environment boundary changed")
        publish(output,"captures.json",captured)
    finally:
        if env is not None:env.close()
    if before!=checkpoint_manifest.verify_checkpoint_directory(checkpoint,asset) or module_parameter_sha256(components)!=fingerprint:
        raise ValueError("base model changed during capture")
    # The preloaded development panel is rehashed by execute after the state-I/O
    # guard exits. Reopening it here would correctly trip that guard.
    journal.deadline()
    return dict(runtime=actual,diagnostic=captured,controller_evidence_sha256=sha(Path(output)/"controller.json"),
        dense_identity=dense_identity,base_checkpoint_unchanged=True,model_parameters_unchanged=True)


def execute(args):
    if not args.execute_gpu or not re.fullmatch(r"[0-9]+",args.job_id) or os.environ.get("SLURM_JOB_ID")!=args.job_id:
        raise ValueError("explicit root-authorized Slurm GPU invocation required")
    project,source=Path(args.project_root),Path(args.source_root)
    if project!=P or source!=P/"snapshots"/SOURCE_NAME or sha(__file__)!=args.script_sha256:
        raise ValueError("root-pinned candidate/server paths differ")
    if any(name=="cti_vla" or name.startswith("cti_vla.") for name in sys.modules):
        raise ValueError("fresh process required before frozen imports")
    output=project/"results/formal_main_v2/engineering/object_action_range_probe_v1"/args.job_id
    output.mkdir(parents=True,exist_ok=False)
    journal=Journal(output,args.job_id);prepared=None;error=None;result=None;exit_code=1
    try:
        journal.emit("probe_start",candidate_sha256=args.script_sha256,registration_sha256=REG_SHA,
            original_result_replacement=False,automatic_retry=False,wall_limit_seconds=900)
        prepared=prepare(project,source)
        prepared["evidence"].seen[str(Path(__file__).absolute())]=args.script_sha256
        publish(output,"inputs.json",dict(registration_sha256=REG_SHA,watched_files=prepared["evidence"].seen))
        journal.emit("inputs_verified",watched_files=prepared["evidence"].seen)
        sys.dont_write_bytecode=True
        sys.path.insert(0,str(source/"src"))
        for flag in ("--libero-source","--oft-source"):sys.path.insert(0,prepared["arg"](flag))
        adapter=load_module(project/META,"_object_probe_metadata_adapter")
        with reject_state_file_reads(),adapter.install_asset_metadata_compat(project_root=project,source_root=source,
                registration_path=project/META_REG,expected_adapter_sha256=META_FILES[META],emit=journal.emit) as identity:
            publish(output,"metadata_identity.json",identity)
            result=gpu_body(prepared,project,source,output,journal)
        exits=[x for x in journal.events if x["event"]=="asset_metadata_compat_exit"]
        loads=[x for x in journal.events if x["event"]=="asset_metadata_compat_load_complete"]
        flags=("original_loader_restored","directory_verifier_unchanged","binding_intact","original_loader_code_unchanged",
            "directory_verifier_code_unchanged","frozen_source_and_inputs_unchanged")
        if len(exits)!=1 or any(exits[0].get(k) is not True for k in flags) or exits[0]["runner_raised"] or exits[0]["passthrough_calls"]!=0 or exits[0]["adapted_calls_attempted"]!=1 or exits[0]["adapted_calls_completed"]!=1 or len(loads)!=1 or loads[0]["suite"]!="libero_object":
            raise ValueError("exact Object metadata context proof missing")
        prepared["evidence"].unchanged();journal.deadline();exit_code=0
    except BaseException as exc:
        error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
        journal.emit("probe_failure",error=error)
    finally:
        unchanged=False
        if prepared is not None:
            try:prepared["evidence"].unchanged();unchanged=True
            except BaseException as exc:
                exit_code=1;error={"type":type(exc).__name__,"message":str(exc),"previous_error":error}
        journal.emit("probe_end",status="captured_pending_root_review" if exit_code==0 else "failed",exit_code=exit_code,
            source_inputs_unchanged=unchanged,success_collected=False,env_steps_after_t56=0,error=error)
        journal.close()
        publish(output,"completion.json",dict(schema="formal_main_v2",kind="bounded_action_range_probe_completion",version=VERSION,
            job_id=args.job_id,status="captured_pending_root_review" if exit_code==0 else "failed",exit_code=exit_code,
            candidate_sha256=args.script_sha256,registration_sha256=REG_SHA,source_inputs_unchanged=unchanged,
            events_sha256=sha(journal.path),events_bytes=journal.path.stat().st_size,
            result=result,error=error,read_evidence_sha256=prepared["evidence"].seen if prepared else {},
            wall_seconds=time.monotonic()-journal.started,GPU_cost_status="pending_root_Slurm_accounting_count_job_once",
            original_results_replaced=False,scientific_complete=False,final_states_read=False,weights_copied=False))
    return exit_code


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-gpu",action="store_true")
    parser.add_argument("--project-root",type=Path,required=True)
    parser.add_argument("--source-root",type=Path,required=True)
    parser.add_argument("--job-id",required=True)
    parser.add_argument("--script-sha256",required=True)
    args=parser.parse_args()
    return execute(args)


if __name__=="__main__":
    raise SystemExit(main())

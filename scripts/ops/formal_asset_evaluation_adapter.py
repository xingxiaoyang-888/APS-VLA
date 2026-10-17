"""Explicit Object/Goal composition around the unchanged formal evaluation adapter.

The original scientific argv and runners are reused in this process. Historical
acceptance/training wrappers are dependencies only, never downstream entrypoints.
This does not issue jobs, build manifests, open a release, or infer trial success.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback
import uuid


P = Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
SCHEMA, VERSION = "formal_main_v2", "formal-downstream-assets-v1"
ENTRY = "scripts/ops/formal_asset_evaluation_adapter.py"
LEGACY = "scripts/ops/formal_evaluation_adapter.py"
LEGACY_SHA = "b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd"
WRAPPER = "scripts/server/run_formal_downstream.py"
CONTROLLER = "scripts/ops/formal_downstream_supervisor.py"
REGISTRATION = "configs/experiments/formal_main_v2.json"
SOURCE_NAME = "formal_main_v2_run_564be0995e"
SOURCE_SHA = "dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e"
INVENTORY = "results/formal_main_v2/source/" + SOURCE_NAME + ".json"
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
GOAL = "scripts/ops/formal_goal_component_adapter.py"
GOAL_REG = "configs/experiments/formal_main_v2_goal_component_compat_v1.json"
GOAL_FILES = {
    GOAL: "60db92e78f62e3dc54c7a791debee9085a2651cfbcd99d4ce725c68428f1c6ea",
    GOAL_REG: "c8c56d17ab2425226ad7964f966e523fbbb518e147679b9504c66dafc654cb84",
    "scripts/server/run_formal_goal_asset_stage.py": "fc7d8756ef2124b15c4709a84d83df929b92fb77dd5230ddfaf210b6274fa039",
    "scripts/server/formal_goal_asset_main.slurm": "ad29920d056b95be82d0257907d2010ba1a97be9166664a65029bdfd001d896a",
}
STAGES = ("development", "final", "collect", "full", "components")
PAYLOAD_SUFFIXES = {".pt", ".pth", ".bin", ".ckpt", ".safetensors", ".pkl", ".pickle", ".init", ".pruned_init"}


def sha(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            result.update(block)
    return result.hexdigest()


def direct(value):
    path = Path(value).absolute()
    if path.resolve() != path:
        raise ValueError("Compatibility paths must be direct, without aliases/traversal")
    return path


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def publish_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".partial")
    with temporary.open("xb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink()


def publish(path, value):
    publish_bytes(path, (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2,
        allow_nan=False) + "\n").encode())


def metadata_contract():
    return dict(schema=SCHEMA, kind="asset_metadata_compatibility", version="formal-asset-metadata-compat-v1",
        wrapper="scripts/server/run_formal_asset_stage.py", slurm="scripts/server/formal_asset_main.slurm",
        adapter=META, registration=META_REG, files=dict(META_FILES))


def component_contract():
    return dict(schema=SCHEMA, kind="goal_component_filename_compatibility", version="formal-goal-components-v1",
        suite="libero_goal", wrapper="scripts/server/run_formal_goal_asset_stage.py",
        slurm="scripts/server/formal_goal_asset_main.slurm", adapter=GOAL, registration=GOAL_REG, files=dict(GOAL_FILES))


def contract_files(suite):
    if suite not in ("libero_object", "libero_goal"):
        raise ValueError("Only Object/Goal use this explicit downstream composition")
    return {ENTRY, LEGACY, WRAPPER, CONTROLLER, *META_FILES, *(GOAL_FILES if suite == "libero_goal" else {})}


def validate_contract(value, suite, project):
    expected = dict(schema=SCHEMA, kind="formal_downstream_asset_compatibility", version=VERSION, suite=suite,
        entrypoint=ENTRY, evaluation_adapter=LEGACY, wrapper=WRAPPER, controller=CONTROLLER,
        metadata_implementation=metadata_contract(), legacy_stage_wrappers_executed=False)
    if suite == "libero_goal":
        expected["component_implementation"] = component_contract()
    if (not isinstance(value, dict) or set(value) != {*expected, "files"}
            or any(value.get(k) != v for k, v in expected.items())
            or value.get("legacy_stage_wrappers_executed") is not False
            or not isinstance(value.get("files"), dict) or set(value["files"]) != contract_files(suite)):
        raise ValueError("Explicit downstream contract or suite-specific implementation identity differs")
    pinned = {LEGACY: LEGACY_SHA, **META_FILES, **(GOAL_FILES if suite == "libero_goal" else {})}
    if any(value["files"][k] != v for k, v in pinned.items()):
        raise ValueError("A frozen adapter/implementation dependency changed")
    for name, checksum in value["files"].items():
        if not re.fullmatch(r"[a-f0-9]{64}", str(checksum)) or sha(direct(project / name)) != checksum:
            raise ValueError("Registered downstream implementation changed: " + name)
    return value


def nonpayload_path(path, *, development_path=None):
    """Refuse payload paths before calling any old resolve/stat/read helper."""
    path = Path(path).absolute()
    if (any("sealed" in p.lower() or p.lower() in ("weights", "checkpoints") for p in path.parts)
            or "initial_states" in {p.lower() for p in path.parts} and path != development_path
            or set(path.suffixes) & PAYLOAD_SUFFIXES):
        raise ValueError("Operational metadata must not open weights or final-state paths")
    return path


def argument_path_guard(args, project, registration, suite):
    development = project / registration["suites"][suite]["initial_states_root"] / "development.json"
    if args.development_panel is not None:
        if Path(args.development_panel).absolute() != development:
            raise ValueError("Development argument must be the registered current panel before any path resolution")
        nonpayload_path(args.development_panel, development_path=development)
    # The two explicit final arguments remain lexical references here. The
    # unchanged check_paths/release/load_formal_panel sequence owns their use.
    for name, value in vars(args).items():
        if isinstance(value, Path) and name not in ("development_panel", "final_registry", "sealed_final"):
            nonpayload_path(value)


def safe_watch(path, project, registration, *, development_path):
    path = nonpayload_path(path, development_path=development_path)
    initial_roots = [project / s["initial_states_root"] for s in registration["suites"].values()]
    if (project not in path.parents
            or any(root == path or root in path.parents for root in initial_roots) and path != development_path):
        raise ValueError("Operational watch must not open weights or final-state paths")
    return direct(path)


def validate(invocation, path, checksum, project, legacy):
    suite, stage = invocation.get("suite"), invocation.get("stage")
    mode = "evaluate" if stage in ("development", "final") else stage
    source = project / "snapshots" / SOURCE_NAME
    if (invocation.get("schema") != SCHEMA or invocation.get("kind") != "formal_downstream_invocation"
            or invocation.get("version") != "formal-downstream-root-v1" or stage not in STAGES
            or suite not in ("libero_object", "libero_goal") or invocation.get("source_root") != str(source)
            or invocation.get("source_sha256") != SOURCE_SHA or invocation.get("entrypoint") != ENTRY
            or invocation.get("adapter_sha256") != LEGACY_SHA or invocation.get("wrapper") != WRAPPER
            or invocation.get("scientific_settings_changed") is not False or invocation.get("final_values_read_locally") is not False
            or any(k in invocation for k in ("runtime_compatibility", "component_compatibility"))
            or type(invocation.get("resume")) is not bool
            or not re.fullmatch(r"[A-Za-z0-9_-]+", invocation.get("stage_key", ""))):
        raise ValueError("Unregistered downstream invocation; historical stage contracts are not execution contracts")
    contract = validate_contract(invocation.get("downstream_asset_compatibility"), suite, project)
    if (invocation.get("support_files") != contract["files"]
            or invocation.get("wrapper_sha256") != contract["files"][WRAPPER]):
        raise ValueError("Invocation support/wrapper bytes differ from its actual downstream contract")
    argv = invocation.get("argv")
    if (not isinstance(argv, list) or not argv or argv[0] != mode
            or any(not isinstance(x, str) or "\0" in x for x in argv)):
        raise ValueError("Original scientific argv/mode required")
    flags = [v for v in argv if v.startswith("--")]
    if len(flags) != len(set(flags)) or "--prepare-only" in flags:
        raise ValueError("Real execution requires unique flags and forbids preparation-only jobs")
    args = legacy.parser().parse_args(argv)
    if (args.source_root != source or args.source_inventory != project / INVENTORY or args.project_root != project
            or args.adapter_sha256 != LEGACY_SHA or args.resume != invocation["resume"]
            or str(args.output) != invocation.get("run_root") or str(args.execution_manifest) != invocation.get("execution_manifest")
            or args.policy_watchdog_seconds != 60. or args.stop_after != invocation.get("stop_after")
            or (mode != "evaluate" and (args.resume or args.stop_after is not None or not args.uncontended_gpu))
            or (args.stop_after is not None and args.stop_after <= 0)):
        raise ValueError("Original runner arguments differ from the registered invocation")
    inventory = legacy.verify_snapshot(project, source, args.source_inventory, adapter_sha256=LEGACY_SHA)
    if (sha(args.source_inventory) != invocation.get("source_inventory_sha256")
            or invocation.get("source_inventory") != str(args.source_inventory)
            or args.registration != project / REGISTRATION
            or sha(args.registration) != inventory["files"][REGISTRATION]
            or sha(args.registration) != invocation.get("registration_sha256")):
        raise ValueError("Source inventory or original scientific registration changed")
    registration = read(args.registration)
    argument_path_guard(args, project, registration, suite)
    legacy.metadata_path(args.execution_manifest, project)
    if sha(args.execution_manifest) != invocation.get("execution_manifest_sha256"):
        raise ValueError("Execution manifest SHA differs")
    manifest = read(args.execution_manifest)
    legacy.check_paths(args, mode, registration, manifest, source)
    if (manifest.get("suite") != suite or manifest.get("split") != ("final" if stage == "final" else "development")
            or [row["identity"]["method_id"] for row in manifest["methods"]] != invocation.get("method_ids")
            or args.checkpoint.as_posix() != Path(registration["suites"][suite]["model_root_server"]).as_posix()):
        raise ValueError("Suite, method, split or original model identity differs")
    # Retain the original manifest/release validator. No final registry/value
    # path is touched in this metadata-only preflight.
    with legacy.source_imports(source):
        from cti_vla.evaluation import formal_trials, formal_profiling
        formal_trials.validate_execution_manifest(manifest, registration_sha256=legacy.signature(registration))
        if stage == "final":
            if not args.release_sha256 or sha(args.release) != args.release_sha256:
                raise ValueError("Exact root-issued final release required before installing loaders")
            release = read(args.release)
            formal_trials.validate_final_release(release, manifest.get("global_freeze"), registration_sha256=legacy.signature(registration))
            if release != manifest.get("release"):
                raise ValueError("Execution manifest carries another final release")
        elif mode != "evaluate":
            formal_profiling.validate_profile_manifest(manifest, registration, collect=mode == "collect",
                global_freeze=read(args.global_freeze) if args.global_freeze else None)
    required = {str(source / n) for n in inventory["files"]} | {str(project / n) for n in contract["files"]}
    required.update(str(p) for p in (args.source_inventory, args.registration, args.execution_manifest,
        args.protocol, args.windows, args.asset_manifest, args.input_acceptance))
    for p in (args.development_panel, args.release, args.global_freeze, args.panel):
        if p is not None: required.add(str(p))
    declared = invocation.get("watched_files", {})
    if not isinstance(declared, dict) or not required.issubset(declared):
        raise ValueError("Invocation omits required nonweight immutable inputs")
    watched = {str(path): checksum}
    for name, expected in declared.items():
        candidate = safe_watch(name, project, registration, development_path=args.development_panel)
        if not re.fullmatch(r"[a-f0-9]{64}", str(expected)) or sha(candidate) != expected:
            raise ValueError("Registered nonweight input changed: " + name)
        watched[str(candidate)] = expected
    return dict(args=args, source=source, output=direct(args.output), contract=contract,
        registration=registration, manifest=manifest, watched=watched)


def unchanged(watched):
    if any(sha(direct(name)) != checksum for name, checksum in watched.items()):
        raise ValueError("Downstream immutable source/input bytes changed")


def legacy_evidence(project, output, job, invocation):
    root = project / f"results/{SCHEMA}/adapter_invocations"
    paths = sorted(p for p in root.glob(job + "_*") if re.fullmatch(re.escape(job) + r"_[a-f0-9]{32}\.(json|jsonl)", p.name))
    artifacts = []
    for path in paths:
        before = path.stat(); data = path.read_bytes(); after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise ValueError("Original evaluation adapter evidence is still changing")
        artifacts.append(dict(source=str(path), path=str(output / "adapter_invocations" / path.name),
            sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))
    receipts = [p for p in paths if p.suffix == ".json"]
    if not paths:
        return None, artifacts
    if len(receipts) != 1 or len(paths) != 2 or receipts[0].with_suffix(".jsonl") not in paths:
        raise ValueError("The job must retain exactly one original adapter attempt and journal")
    receipt = read(receipts[0])
    if (receipt.get("job_id") != job or receipt.get("attempt_id") != receipts[0].stem
            or receipt.get("output") != str(output) or receipt.get("adapter_sha256") != LEGACY_SHA
            or receipt.get("frozen_source_sha256") != SOURCE_SHA
            or receipt.get("execution_manifest_sha256") != invocation["execution_manifest_sha256"]
            or receipt.get("events_path") != str(receipts[0].with_suffix(".jsonl"))
            or receipt.get("events_sha256") != sha(receipts[0].with_suffix(".jsonl"))):
        raise ValueError("Original adapter evidence belongs to another job/source/manifest")
    return dict(attempt_id=receipt["attempt_id"], status=receipt.get("status"), runner_status=receipt.get("runner_status"),
        receipt=next(a for a in artifacts if a["source"].endswith(".json")),
        journal=next(a for a in artifacts if a["source"].endswith(".jsonl")),
        archive_owner="parent downstream wrapper; copies are verified by root after SHA pull"), artifacts


def success_checks(events, suite, metadata_identity, component_identity):
    expected = ["downstream_asset_start", "asset_metadata_compat_enter"]
    if suite == "libero_goal": expected += ["goal_component_compat_enter"]
    expected += ["legacy_adapter_start", "asset_metadata_compat_load_start", "asset_metadata_compat_load_complete"]
    if suite == "libero_goal": expected += ["goal_component_load_start", "goal_component_load_complete"] * 2
    expected += ["legacy_adapter_return"]
    if suite == "libero_goal": expected += ["goal_component_compat_exit"]
    expected += ["asset_metadata_compat_exit"]
    if [r["event"] for r in events] != expected:
        raise ValueError("Successful compatibility requires its exact suite-specific load sequence")
    rows = {r["event"]: r for r in events}
    meta = rows["asset_metadata_compat_exit"]
    required = ("original_loader_restored", "directory_verifier_unchanged", "binding_intact",
        "original_loader_code_unchanged", "directory_verifier_code_unchanged", "frozen_source_and_inputs_unchanged")
    if (any(meta.get(k) is not True for k in required) or meta.get("runner_raised") is not False
            or [meta.get(k) for k in ("adapted_calls_attempted", "adapted_calls_completed", "passthrough_calls")] != [1, 1, 0]
            or rows["asset_metadata_compat_enter"].get("identity") != metadata_identity
            or rows["asset_metadata_compat_load_start"].get("view") != metadata_identity["views"][suite]
            or rows["asset_metadata_compat_load_complete"].get("suite") != suite):
        raise ValueError("Successful downstream execution requires exactly one matching manifest adaptation and restoration")
    if suite == "libero_goal":
        last = rows["goal_component_compat_exit"]
        required = ("original_loader_restored", "original_function_codes_unchanged", "binding_intact",
            "torch_load_unchanged", "source_inputs_unchanged", "component_files_unchanged")
        if (any(last.get(k) is not True for k in required) or last.get("runner_raised") is not False
                or [last.get(k) for k in ("component_calls_attempted", "component_calls_completed", "rejected_calls")] != [2, 2, 0]
                or rows["goal_component_compat_enter"].get("identity") != component_identity):
            raise ValueError("Goal requires exactly two restored official component loads")
        for event in ("goal_component_load_start", "goal_component_load_complete"):
            selected = [r for r in events if r["event"] == event]
            if [r.get("call_id") for r in selected] != [0, 1] or [r.get("mapping") for r in selected] != component_identity["mappings"]:
                raise ValueError("Goal official component order/path differs")


def execute(invocation_path, invocation_sha256, *, project_root=P):
    project, path = direct(project_root), direct(invocation_path)
    job = os.environ.get("SLURM_JOB_ID", "")
    root = project / f"results/{SCHEMA}"
    if (direct(__file__) != project / ENTRY or path.parent != root / "invocations"
            or not re.fullmatch(r"[0-9]+", job) or sha(path) != invocation_sha256
            or sha(project / LEGACY) != LEGACY_SHA):
        raise ValueError("Fresh root-registered downstream invocation and unchanged evaluation adapter required")
    invocation = read(path)
    directory = root / "downstream_asset_invocations" / job
    directory.mkdir(parents=True, exist_ok=False)
    identity_path, events_path, completion_path = (directory / name for name in ("identity.json", "events.jsonl", "completion.json"))
    stage = invocation.get("stage")
    shared = dict(schema=SCHEMA, version=VERSION, job_id=job, invocation_sha256=invocation_sha256,
        mode="evaluate" if stage in ("development", "final") else stage,
        **{k: invocation.get(k) for k in ("stage", "stage_key", "suite", "source_root", "source_sha256", "execution_manifest_sha256")})
    started, started_utc = time.perf_counter(), datetime.now(timezone.utc).isoformat()
    events, errors, artifacts, old_artifacts = [], [], [], []
    plan = identity = proof = None
    code, result, inputs_unchanged, run_unchanged = 1, None, False, False
    legacy = load(project / LEGACY, "original_downstream_evaluation_adapter")
    old_run, old_code = legacy.run, legacy.run.__code__
    run_code_sha = legacy.code_sha(old_run)

    def emit(event, **fields):
        if (set(fields) & {"kind", "seq", "utc", "event"}
                or any(fields[k] != shared[k] for k in set(fields) & set(shared))):
            raise ValueError("Compatibility event cannot replace invocation identity")
        row = dict(**shared, kind="formal_downstream_asset_event", seq=len(events), utc=datetime.now(timezone.utc).isoformat(),
            event=event, **{k: v for k, v in fields.items() if k not in shared})
        with events_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush(); os.fsync(stream.fileno())
        events.append(row)

    def failed(error):
        errors.append(dict(error_type=type(error).__name__, error=str(error)))
        traceback.print_exception(type(error), error, error.__traceback__)

    def copy(original):
        target = plan["output"] / "asset_compatibility" / job / original.name
        data = original.read_bytes(); publish_bytes(target, data)
        checksum = hashlib.sha256(data).hexdigest()
        if sha(original) != checksum or sha(target) != checksum:
            raise ValueError("Downstream compatibility archive changed")
        return dict(source=str(original), path=str(target), sha256=checksum, bytes=len(data))

    emit("downstream_asset_start", entrypoint=ENTRY, argv=invocation.get("argv"),
        downstream_asset_compatibility=invocation.get("downstream_asset_compatibility"))
    try:
        plan = validate(invocation, path, invocation_sha256, project, legacy)
        if list((root / "adapter_invocations").glob(job + "_*")):
            raise ValueError("This Slurm job already has an evaluation adapter attempt; do not overwrite it")
        metadata = load(project / META, "downstream_original_metadata_adapter")
        meta_args = dict(project_root=project, source_root=plan["source"], registration_path=project / META_REG,
            expected_adapter_sha256=META_FILES[META])
        meta_identity = metadata.validate_asset_metadata_compat(**meta_args)
        goal, goal_args, goal_identity = None, None, None
        if shared["suite"] == "libero_goal":
            goal = load(project / GOAL, "downstream_original_goal_component_adapter")
            goal_args = dict(project_root=project, source_root=plan["source"], contract=plan["contract"]["component_implementation"])
            goal_identity = goal.validate_goal_component_compat(**goal_args)
        identity = dict(**shared, kind="formal_downstream_asset_identity", invocation_path=str(path),
            downstream_asset_compatibility=plan["contract"], evaluation_adapter_path=str(project / LEGACY),
            evaluation_adapter_sha256=LEGACY_SHA, original_adapter_run_code_sha256=run_code_sha,
            fingerprint_marshal_version=2, metadata_identity=meta_identity,
            watched_files=plan["watched"], expected_frozen_base_load_calls=1,
            base_call_evidence="Frozen original runner callsite; no model-loading or timed-call instrumentation added",
            legacy_stage_wrappers_executed=False)
        if goal_identity is not None: identity["component_identity"] = goal_identity
        publish(identity_path, identity)
        with legacy.exclusive(root / "stage_locks" / (invocation["stage_key"] + "_downstream_assets.lock")):
            with ExitStack() as scopes:
                if scopes.enter_context(metadata.install_asset_metadata_compat(**meta_args, emit=emit)) != meta_identity:
                    raise ValueError("Installed metadata identity changed after preflight")
                if goal is not None and scopes.enter_context(goal.install_goal_component_compat(**goal_args, emit=emit)) != goal_identity:
                    raise ValueError("Installed Goal identity changed after preflight")
                emit("legacy_adapter_start", identity_sha256=sha(identity_path), evaluation_adapter_path=str(project / LEGACY),
                    original_adapter_run_code_sha256=run_code_sha)
                try:
                    args = plan["args"]
                    result = legacy.run(args, mode=shared["mode"], source_root=args.source_root, source_inventory=args.source_inventory,
                        adapter_sha256=LEGACY_SHA, resume=args.resume)
                except BaseException as error:
                    emit("legacy_adapter_exception", error_type=type(error).__name__, error=str(error))
                    raise
                proof, old_artifacts = legacy_evidence(project, plan["output"], job, invocation)
                emit("legacy_adapter_return", legacy_adapter_proof=proof,
                    runner_status=result.get("status") if isinstance(result, dict) else None)
                if not proof or proof["status"] != "returned":
                    raise ValueError("Original evaluation adapter lacks its complete returned receipt")
            success_checks(events, shared["suite"], meta_identity, goal_identity)
            code = 0
    except BaseException as error:
        failed(error)
    finally:
        run_unchanged = legacy.run is old_run and old_run.__code__ is old_code
        old_run.__code__, legacy.run = old_code, old_run
        if not run_unchanged:
            code = 1; failed(RuntimeError("Original evaluation adapter run binding changed"))
        if plan is not None:
            try:
                unchanged(plan["watched"]); inputs_unchanged = True
                proof, old_artifacts = legacy_evidence(project, plan["output"], job, invocation)
            except BaseException as error:
                code = 1; failed(error)
        meta_exit = next((r for r in reversed(events) if r["event"] == "asset_metadata_compat_exit"), {})
        goal_exit = next((r for r in reversed(events) if r["event"] == "goal_component_compat_exit"), {})
        restored = meta_exit.get("original_loader_restored") is True and (shared["suite"] != "libero_goal" or goal_exit.get("original_loader_restored") is True)
        end = dict(status="returned" if code == 0 else "failed", exit_code=code,
            loader_bindings_restored=restored, original_adapter_run_unchanged=run_unchanged,
            source_inputs_unchanged=inputs_unchanged, errors=errors)
        emit("downstream_asset_end", **end, identity_sha256=sha(identity_path) if identity_path.is_file() else None)
        if plan is not None:
            try:
                artifacts = [copy(p) for p in (identity_path, events_path) if p.is_file()]
            except BaseException as error:
                code = 1; failed(error)
        complete = dict(**shared, kind="formal_downstream_asset_completion", started_utc=started_utc,
            **{**end, "status": "returned" if code == 0 else "failed", "exit_code": code, "errors": errors},
            wall_seconds=time.perf_counter()-started,
            cost_scope="Nested diagnostic only; count the entire Slurm allocation once",
            run_root=str(plan["output"]) if plan else None, downstream_asset_compatibility=invocation.get("downstream_asset_compatibility"),
            legacy_stage_wrappers_executed=False, legacy_adapter_proof=proof, legacy_adapter_artifacts=old_artifacts,
            compatibility_artifacts=artifacts, completion_source=str(completion_path),
            completion_path=str(plan["output"] / "asset_compatibility" / job / completion_path.name) if plan else None,
            scientific_completion_not_inferred=True)
        publish(completion_path, complete)
        if plan is not None: copy(completion_path)
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--invocation", type=Path, required=True)
    parser.add_argument("--invocation-sha256", required=True)
    args = parser.parse_args()
    if os.name != "posix":
        raise RuntimeError("Registered real downstream execution requires Linux Slurm")
    raise SystemExit(execute(args.invocation, args.invocation_sha256))


if __name__ == "__main__":
    main()

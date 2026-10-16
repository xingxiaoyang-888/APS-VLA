"""Run one registered Object/Goal stage with explicit asset-metadata evidence.

The frozen runner, its argv, source and input identities remain unchanged. This
external wrapper adds the reviewed strict-view adapter in the runner process.
Uncatchable termination leaves an unfinished durable journal, never a success.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import runpy
import sys
import time
import traceback
import uuid


P = Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
ROUND, VERSION = "formal_main_v2", "formal-asset-stage-v1"
FROZEN_NAME = "formal_main_v2_run_564be0995e"
FROZEN_SHA = "dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e"
WRAPPER = "scripts/server/run_formal_asset_stage.py"
SLURM = "scripts/server/formal_asset_main.slurm"
ADAPTER = "scripts/ops/formal_asset_metadata_adapter.py"
REGISTRATION = "configs/experiments/formal_main_v2_asset_metadata_compat_v1.json"
PINNED = {
    ADAPTER: "d1ca08465ffcf2682569b1224e2018f17fdba61feac1896f864cc981759397d0",
    REGISTRATION: "25c90cbfe2db6fdb130a16e6b98ab7ccfc8373a2853578bf73ef0d38283cfb44",
    "configs/assets/formal_main_v2_strict/libero_object.json": "d8f1f9a5c1c8c040aa499fd9df35ebe4a039fd6c756b565cf6055046be0cf8b3",
    "configs/assets/formal_main_v2_strict/libero_goal.json": "e55eac83f28854318524ba87fc6554c7a9708b328700232c055deb66a72e0d6c",
}
ENTRIES = {"acceptance": "scripts/verify_formal_acceptance.py", "train": "scripts/run_formal_future.py"}
SUITES = ("libero_object", "libero_goal")


def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            value.update(block)
    return value.hexdigest()


def direct(path):
    path = Path(path).absolute()
    if path.resolve() != path:
        raise ValueError("Stage metadata paths must be direct, without aliases or traversal")
    return path


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def publish_bytes(path, data):
    """Atomic, exclusive publication; a previous receipt is never overwritten."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".partial")
    with temporary.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink()
    if os.name == "posix":
        descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def publish(path, value):
    publish_bytes(path, (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2,
        allow_nan=False) + "\n").encode())


@contextmanager
def stage_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if os.name == "posix":
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)
        else:  # CPU fixture support; the production CLI requires Linux Slurm.
            import msvcrt
            handle.seek(0, os.SEEK_END)
            if not handle.tell():
                handle.write(b"0"); handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                yield
            finally:
                handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def arguments(argv):
    if not isinstance(argv, list) or any(not isinstance(x, str) or "\0" in x for x in argv):
        raise ValueError("Invalid original runner argv")
    result, index = {}, 0
    while index < len(argv):
        key = argv[index]
        if not key.startswith("--") or key in result:
            raise ValueError("Runner flags must be unique")
        count = 3 if key == "--configs" else 0 if key == "--resume" else 1
        values = argv[index + 1:index + count + 1]
        if len(values) != count or any(v.startswith("--") for v in values):
            raise ValueError("Runner flag value missing")
        result[key] = values if count == 3 else True if not count else values[0]
        index += count + 1
    return result


def validate(invocation, path, checksum, project):
    source = project / "snapshots" / FROZEN_NAME
    if (invocation.get("schema") != ROUND or invocation.get("suite") not in SUITES
            or invocation.get("stage") not in ENTRIES or invocation.get("source_root") != str(source)
            or invocation.get("source_sha256") != FROZEN_SHA
            or invocation.get("entrypoint") != ENTRIES[invocation["stage"]]):
        raise ValueError("Unregistered suite/stage/frozen entrypoint")
    stage, suite = invocation["stage"], invocation["suite"]
    compat = invocation.get("runtime_compatibility", {})
    expected = dict(schema=ROUND, kind="asset_metadata_compatibility", version="formal-asset-metadata-compat-v1",
        wrapper=WRAPPER, slurm=SLURM, adapter=ADAPTER, registration=REGISTRATION)
    if set(compat) != set(expected) | {"files"} or any(compat.get(k) != v for k, v in expected.items()):
        raise ValueError("Explicit runtime compatibility contract is missing or changed")
    support = compat["files"]
    if (not isinstance(support, dict) or set(support) != set(PINNED) | {WRAPPER, SLURM}
            or any(support.get(k) != v for k, v in PINNED.items())
            or any(not re.fullmatch("[0-9a-f]{64}", str(v)) for v in support.values())
            or direct(__file__) != project / WRAPPER):
        raise ValueError("Compatibility support file allowlist/SHA differs")
    watched = {str(path): checksum}
    for name, expected_sha in support.items():
        candidate = direct(project / name)
        if sha(candidate) != expected_sha:
            raise ValueError("Compatibility support file changed: " + name)
        watched[str(candidate)] = expected_sha
    inventory_path = direct(source / "source_manifest.json")
    inventory = read(inventory_path)
    files = inventory.get("files", {})
    if (len(files) != 173 or inventory.get("source_sha256") != FROZEN_SHA
            or hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest() != FROZEN_SHA):
        raise ValueError("Frozen173-file source inventory differs")
    watched[str(inventory_path)] = sha(inventory_path)
    for name, expected_sha in files.items():
        candidate = direct(source / name)
        if source not in candidate.parents or sha(candidate) != expected_sha:
            raise ValueError("Frozen source changed: " + name)
        watched[str(candidate)] = expected_sha
    registry_path = source / "configs/experiments/formal_main_v2.json"
    registry = read(registry_path)
    if invocation.get("registration_sha256") != sha(registry_path):
        raise ValueError("Original scientific registration identity changed")
    spec = registry["suites"][suite]
    opts = arguments(invocation.get("argv"))
    common = {"--protocol": str(project / spec["protocol"]), "--windows": str(project / spec["windows"]),
        "--checkpoint": spec["model_root_server"], "--asset-manifest": str(source / spec["model_manifest"]),
        "--data-directory": spec["data_root_server"], "--cache-directory": str(project / (".local/formal-hf-" + suite)),
        "--feature-cache": spec["cache_root_server"]}
    output = direct(opts.get("--output", project))
    required_watched = {common["--protocol"], common["--windows"], common["--asset-manifest"]}
    if stage == "acceptance":
        if (invocation.get("stage_key") != suite + "_acceptance" or invocation.get("segment_end") is not None
                or output.parent != project / f"results/{ROUND}/{suite}/acceptance"
                or not re.fullmatch(r"attempt[0-9]{2,}", output.name)):
            raise ValueError("Acceptance stage/output identity differs")
        expected_opts = {**common, "--suite": suite, "--configs": [str(source / f"configs/experiments/{ROUND}/{suite}_k{k}_seed17.json") for k in (128, 256, 64)],
            "--oft-source": str(project / "external/openvla-oft"), "--project-root": str(project), "--output": str(output)}
        required_watched.update(expected_opts["--configs"])
    else:
        match = re.fullmatch(re.escape(suite) + r"_train_k(256|128|64)_seed(17|23|41)", invocation.get("stage_key", ""))
        target = invocation.get("segment_end")
        if not match or type(target) is not int or target not in range(500, 5001, 500):
            raise ValueError("Training pair/segment identity differs")
        budget, seed = map(int, match.groups())
        pair = next(p for p in registry["pairs"] if (p["suite"], p["visual_tokens"], p["seed"]) == (suite, budget, seed))
        if output != project / f"results/{ROUND}/{suite}/k{budget}/seed{seed}/training":
            raise ValueError("Training output differs from registered pair")
        f00 = direct(opts.get("--input-acceptance-report", project))
        if (f00.name != "input_acceptance.json" or f00.parent.parent != project / f"results/{ROUND}/{suite}/acceptance"
                or not re.fullmatch(r"attempt[0-9]{2,}", f00.parent.name)):
            raise ValueError("Training acceptance path differs from its suite")
        wall = float(opts.get("--max-wall-seconds", "nan"))
        if not math.isfinite(wall) or wall <= 0:
            raise ValueError("Invalid registered engineering wall-time bound")
        expected_opts = {**common, "--config": str(source / pair["path"]), "--training-checkpoints": pair["checkpoint_root_server"],
            "--input-acceptance-report": str(f00), "--acceptance-report": str(f00.parent / f"f01_k{budget}.json"),
            "--output": str(output), "--arm": "both", "--stop-after-updates": str(target),
            "--max-wall-seconds": opts["--max-wall-seconds"]}
        if opts.get("--resume") is True:
            expected_opts["--resume"] = True
        required_watched.add(expected_opts["--config"])
        required_watched.update(str(f00.parent / name) for name in ("input_acceptance.json", f"f01_k{budget}.json",
            "resume_acceptance.json", "f03_calls.jsonl", "acceptance_complete.json"))
    if opts != expected_opts or set(invocation.get("watched_files", {})) != required_watched:
        raise ValueError("Original runner argv/watch contract changed")
    for name, expected_sha in invocation["watched_files"].items():
        if sha(direct(name)) != expected_sha:
            raise ValueError("Registered input changed: " + name)
        watched[name] = expected_sha
    return dict(invocation=invocation, source=source, output=output, watched=watched)


def unchanged(watched):
    for name, checksum in watched.items():
        if sha(direct(name)) != checksum:
            raise ValueError("Stage source/input/support bytes changed: " + name)


def load_adapter(project):
    path = project / ADAPTER
    spec = importlib.util.spec_from_file_location("registered_formal_asset_adapter", path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def run_frozen(source, entrypoint, argv):
    old_argv, old_cwd = sys.argv, Path.cwd()
    try:
        os.chdir(source)
        sys.argv = [str(source / entrypoint), *argv]
        runpy.run_path(str(source / entrypoint), run_name="__main__")
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)


def system_exit_code(error):
    return (0 if error.code is None else int(error.code)) if error.code is None or isinstance(error.code, int) else 1


def execute(invocation_path, invocation_sha256, *, project_root=P):
    project, path = direct(project_root), direct(invocation_path)
    result_root = project / f"results/{ROUND}"
    job = os.environ.get("SLURM_JOB_ID", "")
    if not re.fullmatch(r"[0-9]+", job) or path.parent != result_root / "invocations":
        raise ValueError("Registered Slurm job/invocation path required")
    receipt_path = result_root / "job_receipts" / (job + ".json")
    if receipt_path.exists():
        raise FileExistsError("This job already has an immutable receipt")
    if not re.fullmatch(r"[0-9a-f]{64}", invocation_sha256) or sha(path) != invocation_sha256:
        raise ValueError("Invocation SHA256 differs from root submission")
    invocation = read(path)
    directory = result_root / "compatibility_invocations" / job
    directory.mkdir(parents=True, exist_ok=False)
    journal, identity_path = directory / "compatibility_events.jsonl", directory / "identity.json"
    started, started_utc = time.perf_counter(), datetime.now(timezone.utc).isoformat()
    base = dict(schema=ROUND, version=VERSION, job_id=job,
        **{k: invocation.get(k) for k in ("stage", "stage_key", "suite", "source_root", "source_sha256")},
        invocation_sha256=invocation_sha256)
    events, errors, artifacts = [], [], []
    phase, ended, loader_restored, inputs_unchanged = "preflight", False, False, False
    termination, runner_code, exit_code, identity_sha = "not_started", None, 1, None
    plan = None

    def emit(event, **fields):
        if (set(fields) & {"kind", "seq", "utc", "event"}
                or any(fields[key] != base[key] for key in set(fields) & set(base))):
            raise ValueError("Compatibility event tried to replace its registered job identity")
        fields = {key: value for key, value in fields.items() if key not in base}
        row = dict(**base, kind="formal_asset_stage_event", seq=len(events),
            utc=datetime.now(timezone.utc).isoformat(), event=event, **fields)
        with journal.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush(); os.fsync(stream.fileno())
        events.append(row)

    def failure(error, at_phase):
        errors.append(dict(phase=at_phase, error_type=type(error).__name__, error=str(error)))
        traceback.print_exception(type(error), error, error.__traceback__)

    def finish(output=None):
        nonlocal ended
        status = "returned" if exit_code == 0 else "failed"
        emit("stage_end", status=status, exit_code=exit_code, runner_termination=termination,
            runner_exit_code=runner_code, loader_restored=loader_restored,
            source_inputs_unchanged=inputs_unchanged, errors=errors, identity_sha256=identity_sha)
        ended = True
        if output is not None:
            for original in (identity_path, journal):
                if not original.is_file():
                    continue
                data = original.read_bytes()
                target = output / "compatibility" / job / original.name
                publish_bytes(target, data)
                checksum = hashlib.sha256(data).hexdigest()
                if sha(original) != checksum or sha(target) != checksum:
                    raise ValueError("Compatibility archive differs from its original bytes")
                artifacts.append(dict(source=str(original), path=str(target), sha256=checksum, bytes=len(data)))

    raw_argv = invocation.get("argv")
    output_argument = (raw_argv[raw_argv.index("--output") + 1]
        if isinstance(raw_argv, list) and raw_argv.count("--output") == 1
        and raw_argv.index("--output") + 1 < len(raw_argv) else None)
    emit("stage_start", entrypoint=invocation.get("entrypoint"), argv=raw_argv,
        run_root=output_argument,
        runtime_compatibility=invocation.get("runtime_compatibility"))
    try:
        plan = validate(invocation, path, invocation_sha256, project)
        phase = "stage_lock"
        with stage_lock(result_root / "stage_locks" / (invocation["stage_key"] + ".lock")):
            try:
                phase = "compatibility_validation"
                adapter = load_adapter(project)
                kwargs = dict(project_root=project, source_root=plan["source"], registration_path=project / REGISTRATION,
                    expected_adapter_sha256=PINNED[ADAPTER])
                identity = adapter.validate_asset_metadata_compat(**kwargs)
                plan["watched"].update(identity["watched_files"])
                publish(identity_path, dict(**base, kind="formal_asset_stage_identity",
                    invocation_path=str(path), runtime_compatibility=invocation["runtime_compatibility"], identity=identity))
                identity_sha = sha(identity_path)
                phase = "runner"
                with adapter.install_asset_metadata_compat(**kwargs, emit=emit) as installed:
                    if installed != identity:
                        raise ValueError("Installed compatibility identity changed after validation")
                    emit("stage_runner_start", entrypoint=invocation["entrypoint"], argv=invocation["argv"],
                        cwd=str(plan["source"]), run_name="__main__", identity_sha256=identity_sha)
                    try:
                        run_frozen(plan["source"], invocation["entrypoint"], invocation["argv"])
                    except SystemExit as error:
                        termination, runner_code = "system_exit", system_exit_code(error)
                        if runner_code:
                            emit("stage_runner_exception", runner_termination=termination, runner_exit_code=runner_code,
                                error_type=type(error).__name__, error=str(error))
                            raise
                    except BaseException as error:
                        termination, runner_code = "exception", 130 if isinstance(error, KeyboardInterrupt) else 1
                        emit("stage_runner_exception", runner_termination=termination, runner_exit_code=runner_code,
                            error_type=type(error).__name__, error=str(error))
                        raise
                    else:
                        termination, runner_code = "returned", 0
                    emit("stage_runner_return", runner_termination=termination, runner_exit_code=runner_code)
                exits = [e for e in events if e["event"] == "asset_metadata_compat_exit"]
                starts = [e for e in events if e["event"] == "asset_metadata_compat_load_start"]
                completions = [e for e in events if e["event"] == "asset_metadata_compat_load_complete"]
                required = ("original_loader_restored", "directory_verifier_unchanged", "binding_intact",
                    "original_loader_code_unchanged", "directory_verifier_code_unchanged", "frozen_source_and_inputs_unchanged")
                if (len(exits) != 1 or any(exits[0].get(k) is not True for k in required)
                        or exits[0].get("runner_raised") is not False
                        or len(starts) != 1 or len(completions) != 1
                        or starts[0].get("call_id") != 0 or completions[0].get("call_id") != 0
                        or starts[0].get("view") != identity["views"][invocation["suite"]]
                        or completions[0].get("suite") != invocation["suite"]
                        or exits[0].get("adapted_calls_attempted") != 1 or exits[0].get("adapted_calls_completed") != 1
                        or exits[0].get("passthrough_calls") != 0):
                    raise ValueError("Successful stage needs exactly one target-suite load and complete compatibility restoration")
                exit_code = 0
            except BaseException as error:
                exit_code = runner_code if runner_code not in (None, 0) else 1
                failure(error, phase)
            finally:
                phase = "finalization"
                exits = [e for e in events if e["event"] == "asset_metadata_compat_exit"]
                loader_restored = len(exits) == 1 and exits[0].get("original_loader_restored") is True
                try:
                    unchanged(plan["watched"])
                    inputs_unchanged = len(exits) == 1 and exits[0].get("frozen_source_and_inputs_unchanged") is True
                except BaseException as error:
                    exit_code = 1; failure(error, phase)
                finish(plan["output"])
    except BaseException as error:
        exit_code = 1; failure(error, phase)
    finally:
        if not ended:
            finish()
        receipt = dict(**base, kind="formal_asset_stage_job", entrypoint=invocation.get("entrypoint"),
            run_root=str(plan["output"]) if plan else None, started_utc=started_utc,
            exit_code=exit_code, wall_seconds=time.perf_counter()-started,
            runtime_compatibility=invocation.get("runtime_compatibility"), wrapper_sha256=sha(__file__),
            compatibility_artifacts=artifacts, loader_restored=loader_restored, source_inputs_unchanged=inputs_unchanged,
            status="returned" if exit_code == 0 else "failed", runner_termination=termination,
            runner_exit_code=runner_code, errors=errors)
        publish(receipt_path, receipt)
    return exit_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--invocation", type=Path, required=True)
    parser.add_argument("--invocation-sha256", required=True)
    args = parser.parse_args()
    if os.name != "posix":
        raise RuntimeError("Formal asset stages run only in Linux Slurm allocations")
    raise SystemExit(execute(args.invocation, args.invocation_sha256))


if __name__ == "__main__":
    main()

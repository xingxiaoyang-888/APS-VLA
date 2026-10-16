"""Goal-only outer component compatibility; inner metadata evidence stays intact."""
from __future__ import annotations

import argparse
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


P = Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
ROUND, VERSION = "formal_main_v2", "formal-goal-components-v1"
ADAPTER = "scripts/ops/formal_goal_component_adapter.py"
WRAPPER = "scripts/server/run_formal_goal_asset_stage.py"
SLURM = "scripts/server/formal_goal_asset_main.slurm"
REGISTRATION = "configs/experiments/formal_main_v2_goal_component_compat_v1.json"
INNER = "scripts/server/run_formal_asset_stage.py"
INNER_SHA = "9c49bbd536646c8b677c611328e79e7ff3a16a6bca7c5309c8e69cdce3250996"


def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            value.update(block)
    return value.hexdigest()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def ref(path):
    return dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size)


def execute(invocation_path, invocation_sha256, *, project_root=P):
    project = Path(project_root).absolute()
    if project.resolve() != project or sha(project / INNER) != INNER_SHA:
        raise ValueError("Use the unchanged explicitly audited inner metadata wrapper")
    inner = load_module(project / INNER, "unchanged_formal_asset_stage")
    path = inner.direct(invocation_path)
    job = os.environ.get("SLURM_JOB_ID", "")
    root = project / f"results/{ROUND}"
    if (not re.fullmatch(r"[0-9]+", job) or path.parent != root / "invocations"
            or sha(path) != invocation_sha256 or (root / "job_receipts" / (job + ".json")).exists()
            or inner.direct(__file__) != project / WRAPPER):
        raise ValueError("Fresh registered Goal Slurm invocation required")
    invocation = inner.read(path)
    global_dir = root / "component_compatibility_invocations" / job
    global_dir.mkdir(parents=True, exist_ok=False)
    identity_path, events_path, complete_path = (global_dir / name for name in ("identity.json", "events.jsonl", "completion.json"))
    shared = dict(schema=ROUND, version=VERSION, job_id=job, invocation_sha256=invocation_sha256,
        **{key: invocation.get(key) for key in ("stage", "stage_key", "suite", "source_root", "source_sha256")})
    started, utc = time.perf_counter(), datetime.now(timezone.utc).isoformat()
    errors, events, artifacts = [], [], []
    output = plan = identity = None
    identity_sha, inner_receipt, inner_receipt_sha = None, None, None
    metadata_artifacts, code, inner_code, restored, unchanged, target_unchanged = [], 1, None, False, False, False
    phase = "preflight"

    def emit(event, **fields):
        if (set(fields) & {"kind", "seq", "utc", "event"}
                or any(fields[k] != shared[k] for k in set(fields) & set(shared))):
            raise ValueError("Component event attempted to replace its registered identity")
        fields = {k: v for k, v in fields.items() if k not in shared}
        row = dict(**shared, kind="formal_goal_component_event", seq=len(events),
            utc=datetime.now(timezone.utc).isoformat(), event=event, **fields)
        with events_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush(); os.fsync(stream.fileno())
        events.append(row)

    def failed(error):
        errors.append(dict(phase=phase, error_type=type(error).__name__, error=str(error)))
        traceback.print_exception(type(error), error, error.__traceback__)

    def copy_artifact(original):
        data = original.read_bytes()
        target = output / "component_compatibility" / job / original.name
        inner.publish_bytes(target, data)
        checksum = hashlib.sha256(data).hexdigest()
        if sha(original) != checksum or sha(target) != checksum:
            raise ValueError("Component evidence archive changed")
        return dict(source=str(original), path=str(target), sha256=checksum, bytes=len(data))

    emit("component_stage_start", entrypoint=invocation.get("entrypoint"), argv=invocation.get("argv"),
        runtime_compatibility=invocation.get("runtime_compatibility"), component_compatibility=invocation.get("component_compatibility"))
    try:
        if invocation.get("suite") != "libero_goal" or invocation.get("stage") not in ("acceptance", "train"):
            raise ValueError("Component compatibility is only registered for Goal acceptance/train")
        plan = inner.validate(invocation, path, invocation_sha256, project)
        output = plan["output"]
        component = invocation.get("component_compatibility")
        expected = dict(schema=ROUND, kind="goal_component_filename_compatibility", version=VERSION,
            suite="libero_goal", wrapper=WRAPPER, adapter=ADAPTER, slurm=SLURM, registration=REGISTRATION)
        if (not isinstance(component, dict) or set(component) != {*expected, "files"}
                or any(component.get(k) != v for k, v in expected.items())
                or set(component.get("files", {})) != {WRAPPER, ADAPTER, SLURM, REGISTRATION}):
            raise ValueError("Explicit exact4 component compatibility contract required")
        for name, checksum in component["files"].items():
            if not re.fullmatch("[0-9a-f]{64}", str(checksum)) or sha(inner.direct(project / name)) != checksum:
                raise ValueError("Component support file differs: " + name)
            plan["watched"][str(project / name)] = checksum
        adapter = load_module(project / ADAPTER, "registered_formal_goal_component_adapter")
        kwargs = dict(project_root=project, source_root=plan["source"], contract=component)
        identity = adapter.validate_goal_component_compat(**kwargs)
        plan["watched"].update(identity["watched_files"])
        inner.publish(identity_path, dict(**shared, kind="formal_goal_component_identity",
            invocation_path=str(path), runtime_compatibility=invocation["runtime_compatibility"],
            component_compatibility=component, inner_wrapper_path=str(project / INNER), inner_wrapper_sha256=INNER_SHA,
            identity=identity))
        identity_sha = sha(identity_path)
        phase = "inner_stage"
        # Original stage_key lock remains acquired by inner.execute itself.
        # This additional lock excludes another Goal component runner.
        with inner.stage_lock(root / "stage_locks" / (invocation["stage_key"] + "_goal_components.lock")):
            with adapter.install_goal_component_compat(**kwargs, emit=emit) as installed:
                if installed != identity:
                    raise ValueError("Installed Goal component identity changed after validation")
                emit("component_inner_start", inner_wrapper_path=str(project / INNER), inner_wrapper_sha256=INNER_SHA,
                    entry_function="execute", identity_sha256=identity_sha)
                try:
                    inner_code = inner.execute(path, invocation_sha256, project_root=project)
                except BaseException as error:
                    emit("component_inner_exception", error_type=type(error).__name__, error=str(error))
                    raise
                inner_path = root / "job_receipts" / (job + ".json")
                inner_receipt, inner_receipt_sha = inner.read(inner_path), sha(inner_path)
                metadata_artifacts = inner_receipt.get("compatibility_artifacts", [])
                emit("component_inner_return", inner_exit_code=inner_code, inner_job_receipt=ref(inner_path),
                    metadata_artifacts=metadata_artifacts)
                if inner_code != 0:
                    raise RuntimeError("Inner frozen scientific runner returned nonzero: " + str(inner_code))
            exits = [r for r in events if r["event"] == "goal_component_compat_exit"]
            starts = [r for r in events if r["event"] == "goal_component_load_start"]
            completed = [r for r in events if r["event"] == "goal_component_load_complete"]
            flags = ("original_loader_restored", "original_function_codes_unchanged", "binding_intact",
                "torch_load_unchanged", "source_inputs_unchanged", "component_files_unchanged")
            if (len(exits) != 1 or any(exits[0].get(k) is not True for k in flags)
                    or exits[0].get("runner_raised") is not False or exits[0].get("rejected_calls") != 0
                    or exits[0].get("component_calls_attempted") != 2 or exits[0].get("component_calls_completed") != 2
                    or [r.get("call_id") for r in starts] != [0, 1] or [r.get("call_id") for r in completed] != [0, 1]
                    or [r.get("mapping") for r in starts] != identity["mappings"]
                    or [r.get("mapping") for r in completed] != identity["mappings"]):
                raise ValueError("Successful Goal stage needs both exact mapped loads and restoration")
            if (inner_receipt.get("exit_code") != 0 or inner_receipt.get("status") != "returned"
                    or inner_receipt.get("invocation_sha256") != invocation_sha256
                    or inner_receipt.get("runtime_compatibility") != invocation["runtime_compatibility"]
                    or len(metadata_artifacts) != 2):
                raise ValueError("Original metadata stage receipt is incomplete or belongs to another invocation")
            code = 0
    except BaseException as error:
        code = inner_code if type(inner_code) is int and inner_code != 0 else 1
        failed(error)
    finally:
        phase = "finalization"
        exits = [r for r in events if r["event"] == "goal_component_compat_exit"]
        restored = len(exits) == 1 and exits[0].get("original_loader_restored") is True
        target_unchanged = len(exits) == 1 and exits[0].get("component_files_unchanged") is True
        if plan is not None:
            try:
                inner.unchanged(plan["watched"])
                unchanged = len(exits) == 1 and exits[0].get("source_inputs_unchanged") is True
                if inner_receipt_sha is not None and sha(root / "job_receipts" / (job + ".json")) != inner_receipt_sha:
                    raise ValueError("Original inner job receipt changed")
                for artifact in metadata_artifacts:
                    if sha(artifact["source"]) != artifact["sha256"] or sha(artifact["path"]) != artifact["sha256"]:
                        raise ValueError("Original metadata artifact changed")
            except BaseException as error:
                code = 1; failed(error)
        emit("component_stage_end", status="returned" if code == 0 else "failed", exit_code=code,
            inner_exit_code=inner_code, original_loader_restored=restored, source_inputs_unchanged=unchanged,
            component_files_unchanged=target_unchanged, errors=errors, identity_sha256=identity_sha)
        if output is not None:
            try:
                for original in (identity_path, events_path):
                    if original.is_file():
                        artifacts.append(copy_artifact(original))
            except BaseException as error:
                code = 1; failed(error)
        inner_path = root / "job_receipts" / (job + ".json")
        completion = dict(**shared, kind="formal_goal_component_completion", started_utc=utc,
            status="returned" if code == 0 else "failed", exit_code=code, inner_exit_code=inner_code,
            wall_seconds=time.perf_counter()-started, cost_scope="Nested diagnostic only; count the entire Slurm allocation once",
            runtime_compatibility=invocation.get("runtime_compatibility"), component_compatibility=invocation.get("component_compatibility"),
            run_root=str(output) if output else None, inner_job_receipt=ref(inner_path) if inner_path.is_file() else None,
            metadata_artifacts=metadata_artifacts, component_artifacts=artifacts,
            completion_source=str(complete_path), completion_path=str(output / "component_compatibility" / job / complete_path.name) if output else None,
            original_loader_restored=restored, source_inputs_unchanged=unchanged,
            component_files_unchanged=target_unchanged, errors=errors)
        inner.publish(complete_path, completion)
        if output is not None:
            copy_artifact(complete_path)
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--invocation", type=Path, required=True)
    parser.add_argument("--invocation-sha256", required=True)
    args = parser.parse_args()
    if os.name != "posix":
        raise RuntimeError("Goal component compatibility requires the registered Linux Slurm allocation")
    raise SystemExit(execute(args.invocation, args.invocation_sha256))


if __name__ == "__main__":
    main()

"""Run only the SHA-registered downstream adapter; preserve every job attempt."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import time
import uuid

P = Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
ROUND = "formal_main_v2"
ADAPTER = "scripts/ops/formal_evaluation_adapter.py"
WRAPPER = "scripts/server/run_formal_downstream.py"
CONTROLLER = "scripts/ops/formal_downstream_supervisor.py"
ADAPTER_SHA = "b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd"
FROZEN_SHA = "dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e"
SOURCE = P / "snapshots/formal_main_v2_run_564be0995e"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def publish_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".partial")
    with temporary.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("Existing immutable wrapper artifact differs")
    else:
        os.link(temporary, path)
    temporary.unlink()


def publish(path, value):
    publish_bytes(path, (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())


def safe(path, *, root=P, allow_development=False):
    path = Path(path)
    parts = [p.lower() for p in path.parts]
    if (not path.is_absolute() or root not in path.parents or path.resolve() != path
            or any("sealed" in p or p in ("weights", "checkpoints") for p in parts)
            or set(path.suffixes) & {".pt", ".pth", ".bin", ".ckpt", ".safetensors", ".pkl", ".pickle", ".init", ".pruned_init"}
            or ("initial_states" in parts and not (allow_development and path.name == "development.json"))):
        raise ValueError("Wrapper may only hash explicit nonweight, nonsealed paths")
    return path


def validate_shape(invocation):
    stage = invocation.get("stage")
    if (invocation.get("schema") != ROUND or invocation.get("kind") != "formal_downstream_invocation"
            or invocation.get("version") != "formal-downstream-root-v1"
            or stage not in ("development", "final", "collect", "full", "components")
            or invocation.get("source_root") != SOURCE.as_posix() or invocation.get("source_sha256") != FROZEN_SHA
            or invocation.get("entrypoint") != ADAPTER or invocation.get("adapter_sha256") != ADAPTER_SHA
            or invocation.get("wrapper") != WRAPPER or invocation.get("scientific_settings_changed") is not False
            or invocation.get("final_values_read_locally") is not False
            or type(invocation.get("resume")) is not bool
            or not re.fullmatch(r"[A-Za-z0-9_-]+", invocation.get("stage_key", ""))):
        raise ValueError("Unregistered downstream wrapper/adapter identity")
    support = invocation.get("support_files", {})
    if set(support) != {ADAPTER, WRAPPER, CONTROLLER} or support[ADAPTER] != ADAPTER_SHA or support[WRAPPER] != invocation.get("wrapper_sha256"):
        raise ValueError("Downstream support file allowlist differs")
    argv = invocation.get("argv")
    if not isinstance(argv, list) or any(not isinstance(x, str) or "\0" in x for x in argv):
        raise ValueError("Invalid registered downstream argv")
    expected_mode = "evaluate" if stage in ("development", "final") else stage
    if not argv or argv[0] != expected_mode or "--prepare-only" in argv:
        raise ValueError("Stage/adapter mode differs; no preparation-only GPU jobs")
    flags = [x for x in argv[1:] if x.startswith("--")]
    if len(flags) != len(set(flags)):
        raise ValueError("Duplicate adapter flags are not a registered invocation")
    if ("--resume" in flags) != invocation["resume"] or (stage in ("collect", "full", "components") and "--uncontended-gpu" not in flags):
        raise ValueError("Resume/uncontended-GPU flags differ")


def verify(invocation):
    validate_shape(invocation)
    if sha(P / WRAPPER) != invocation["wrapper_sha256"]:
        raise ValueError("Server wrapper changed after root registration")
    for name, expected in invocation["support_files"].items():
        if sha(safe(P / name)) != expected:
            raise ValueError("Registered support file changed")
    path = safe(P / ADAPTER)
    spec = importlib.util.spec_from_file_location("registered_formal_adapter", path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    args = adapter.parser().parse_args(invocation["argv"])
    if (str(args.source_root) != invocation["source_root"] or str(args.source_inventory) != invocation["source_inventory"]
            or args.adapter_sha256 != ADAPTER_SHA or str(args.output) != invocation["run_root"]
            or str(args.execution_manifest) != invocation["execution_manifest"] or args.project_root != P
            or args.policy_watchdog_seconds != 60. or args.stop_after != invocation.get("stop_after")):
        raise ValueError("Adapter arguments differ from their registered wrapper identity")
    safe(args.execution_manifest)
    safe(args.registration)
    if sha(args.execution_manifest) != invocation["execution_manifest_sha256"] or sha(args.registration) != invocation["registration_sha256"]:
        raise ValueError("Execution manifest or registration bytes changed")
    if sha(safe(args.source_inventory)) != invocation["source_inventory_sha256"]:
        raise ValueError("Frozen source inventory changed")
    adapter.verify_snapshot(P, SOURCE, args.source_inventory, adapter_sha256=ADAPTER_SHA)
    registration = json.loads(args.registration.read_text(encoding="utf-8"))
    manifest = json.loads(args.execution_manifest.read_text(encoding="utf-8"))
    adapter.check_paths(args, args.mode, registration, manifest, SOURCE)
    if manifest["suite"] != invocation["suite"] or [r["identity"]["method_id"] for r in manifest["methods"]] != invocation["method_ids"]:
        raise ValueError("Registered method ordering/suite changed")
    for name, expected in invocation["watched_files"].items():
        if sha(safe(name, allow_development=True)) != expected:
            raise ValueError("Registered downstream input changed: " + name)
    return args


def archive_adapter_evidence(*, root, output, job_id, invocation):
    """Copy only this exact job's JSON/JSONL bytes, including unfinished journals.
    No arbitrary folder copy, checkpoint access, or initial-state payloads.
    """
    if not re.fullmatch(r"[0-9]+", job_id):
        raise ValueError("Invalid Slurm job identity")
    source_dir = root / "results/formal_main_v2/adapter_invocations"
    artifacts, receipts = [], []
    for path in sorted(source_dir.glob(job_id + "_*")):
        if not re.fullmatch(re.escape(job_id) + r"_[0-9a-f]{32}\.(json|jsonl)", path.name):
            continue
        safe(path, root=root)
        before = path.stat()
        data = path.read_bytes()
        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise ValueError("Adapter evidence is still changing after subprocess exit")
        target = output / "adapter_invocations" / path.name
        safe(target, root=root)
        publish_bytes(target, data)
        checksum = hashlib.sha256(data).hexdigest()
        if sha(target) != checksum or sha(path) != checksum:
            raise ValueError("Archived adapter evidence bytes changed")
        artifacts.append(dict(source=str(path), path=str(target), sha256=checksum, bytes=len(data)))
        if path.suffix == ".json":
            receipt = json.loads(data)
            if (receipt.get("job_id") != job_id or receipt.get("attempt_id") != path.stem
                    or receipt.get("output") != invocation["run_root"] or receipt.get("adapter_sha256") != ADAPTER_SHA
                    or receipt.get("frozen_source_sha256") != FROZEN_SHA):
                raise ValueError("Adapter receipt is not this exact registered job/output")
            journal = path.with_suffix(".jsonl")
            if receipt.get("events_path") != str(journal) or not journal.is_file() or sha(journal) != receipt.get("events_sha256"):
                raise ValueError("Adapter receipt lost its exact raw invocation journal")
            receipts.append(dict(path=str(target), status=receipt.get("status"), runner_status=receipt.get("runner_status")))
    return artifacts, receipts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--invocation", type=Path, required=True)
    parser.add_argument("--invocation-sha256", required=True)
    args = parser.parse_args()
    job = os.environ.get("SLURM_JOB_ID", "")
    if os.name != "posix" or not re.fullmatch(r"[0-9]+", job):
        raise ValueError("Downstream wrapper requires the registered server Slurm job")
    path = safe(args.invocation)
    if path.parent != P / "results/formal_main_v2/invocations" or sha(path) != args.invocation_sha256:
        raise ValueError("Invocation path/SHA differs from the submitted root command")
    invocation = json.loads(path.read_text(encoding="utf-8"))
    validate_shape(invocation)
    output = safe(Path(invocation["run_root"]))
    if P / "results/formal_main_v2" not in output.parents:
        raise ValueError("Downstream output leaves formal results")
    started = time.perf_counter()
    receipt = dict(schema=ROUND, kind="formal_downstream_job_receipt", job_id=job, stage=invocation["stage"],
        stage_key=invocation["stage_key"], run_root=str(output), invocation_sha256=sha(path), source_sha256=FROZEN_SHA,
        adapter_sha256=ADAPTER_SHA, wrapper_sha256=invocation["wrapper_sha256"],
        started_utc=datetime.now(timezone.utc).isoformat(), stage_completed_claimed=False,
        cost_scope="Complete Slurm allocation is billed separately, including preflight and every failed attempt")
    code = 1
    try:
        from contextlib import ExitStack
        import fcntl
        locks = P / "results/formal_main_v2/stage_locks"
        locks.mkdir(parents=True, exist_ok=True)
        with ExitStack() as stack:
            # Per-instance locks also prevent accidentally overlapping grouped
            # manifests from concurrent independently registered submissions.
            names = [invocation["stage_key"], *[f"{invocation['suite']}_{invocation['stage']}_{mid}" for mid in invocation["method_ids"]]]
            for name in sorted(names):
                if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
                    raise ValueError("Invalid registered stage/instance lock")
                lock = stack.enter_context((locks / (name + ".lock")).open("a"))
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            verify(invocation)
            result = subprocess.run([sys.executable, str(P / ADAPTER), *invocation["argv"]], cwd=SOURCE)
            code = result.returncode
    except BaseException as error:
        receipt.update(error_type=type(error).__name__, error=str(error))
    finally:
        try:
            artifacts, adapter_receipts = archive_adapter_evidence(root=P, output=output, job_id=job, invocation=invocation)
            receipt.update(adapter_artifacts=artifacts, adapter_receipts=adapter_receipts)
            for name, expected in invocation["support_files"].items():
                if sha(safe(P / name)) != expected:
                    raise ValueError("Support bytes changed during execution")
            if code == 0 and (not adapter_receipts or any(r["status"] != "returned" for r in adapter_receipts)):
                raise ValueError("Successful subprocess lacks its complete adapter invocation evidence")
        except BaseException as error:
            code = 1
            receipt.update(archive_error_type=type(error).__name__, archive_error=str(error))
        receipt.update(exit_code=code, status="returned" if code == 0 else "failed", wall_seconds=time.perf_counter() - started,
                       finished_utc=datetime.now(timezone.utc).isoformat())
        publish(P / "results/formal_main_v2/job_receipts" / (job + ".json"), receipt)
    raise SystemExit(code)


if __name__ == "__main__":
    main()

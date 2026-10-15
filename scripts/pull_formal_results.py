"""Pull stable non-weight evidence for registered formal-main-v2 terminal jobs.

This local-only helper never changes supervisor state or submits/cancels jobs.
Downloads are quarantined until a second remote inventory and accounting check
agree. A verified file snapshot is not a scientific acceptance/completion claim.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]
P = "/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA"
H = "/share/home/u15016/XXY_CVPR/CTI-VLA"
ROUND = "formal_main_v2"
STATE = ROOT / "results/experiment_supervisor/state.json"
SSH = ["ssh", "-o", "BatchMode=yes", "tongji-cvpr"]
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL",
            "PREEMPTED", "BOOT_FAIL", "DEADLINE", "REVOKED", "SPECIAL_EXIT"}
ALLOWED_SUFFIXES = {".json", ".jsonl", ".txt", ".md", ".csv", ".tsv", ".log", ".out", ".err",
                    ".yaml", ".yml", ".npz", ".npy", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".html"}
WEIGHT_SUFFIXES = {".pt", ".pth", ".pkl", ".pickle", ".ckpt", ".safetensors", ".bin", ".onnx",
                   ".h5", ".hdf5", ".model", ".pb", ".msgpack", ".init", ".bddl"}
FORBIDDEN_PARTS = {"checkpoints", "checkpoint", "weights", "models", "sealed", "sealed_final",
                   "initial_states", "initial_state", "init_states", "final_states", "test_states"}


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            result.update(block)
    return result.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".partial")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


@contextmanager
def pull_lock():
    path = ROOT / f"results/{ROUND}/pulls/.writer.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)


def registered_jobs(state):
    result = []
    for row in state["registered_jobs"]:
        if row.get("experiment") != ROUND:
            continue
        job_id = str(row.get("job_id", ""))
        name = row.get("name", "")
        root = row.get("run_root", "")
        path = PurePosixPath(root)
        base = PurePosixPath(P) / "results" / ROUND
        if not job_id.isascii() or not job_id.isdigit() or not re.fullmatch(r"cti-[A-Za-z0-9_-]+", name):
            raise ValueError("Invalid registered formal Slurm identity")
        if not path.is_absolute() or str(path) != root or ".." in path.parts or base not in path.parents:
            raise ValueError("Registered run_root must be strictly inside this project's formal results")
        if any(part.lower() in FORBIDDEN_PARTS or "sealed" in part.lower() or "initial_state" in part.lower()
               for part in path.relative_to(base).parts):
            raise ValueError("Registered run_root cannot name weights or sealed state data")
        result.append({key: row.get(key) for key in ("job_id", "name", "run_root", "mode", "stage_key", "source_sha256")})
        result[-1]["job_id"] = job_id
    if len({row["job_id"] for row in result}) != len(result):
        raise ValueError("Duplicate formal job registration")
    return sorted(result, key=lambda row: int(row["job_id"]))


def query_accounting(jobs, timeout):
    if not jobs:
        return {"raw": "", "jobs": {}}
    ids = [row["job_id"] for row in jobs]
    command = "sacct -n -X -P -j " + ",".join(ids) + " --format=JobIDRaw,State,ExitCode,ElapsedRaw,AllocTRES,NodeList"
    raw = subprocess.run(SSH + [command], check=True, capture_output=True, text=True, timeout=timeout).stdout
    found = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        fields = line.split("|")
        if len(fields) < 6 or fields[0] not in ids or fields[0] in found:
            raise ValueError("Unexpected or duplicate Slurm accounting row")
        status = fields[1].split()
        if not status or not re.fullmatch(r"\d+:\d+", fields[2]) or not fields[3].isascii() or not fields[3].isdigit():
            raise ValueError("Invalid Slurm status/exit code/allocation duration")
        found[fields[0]] = dict(status=status[0].rstrip("+"), raw_status=fields[1],
            exit_code=fields[2], elapsed_seconds=int(fields[3]), allocation=fields[4], node=fields[5])
    if set(found) != set(ids):
        raise ValueError("Accounting incomplete; no final snapshot may be inferred")
    return {"raw": raw, "jobs": found}


def overlapping(left, right):
    a, b = PurePosixPath(left), PurePosixPath(right)
    return a == b or a in b.parents or b in a.parents


def build_request(jobs, accounting, requested_ids):
    known = {row["job_id"] for row in jobs}
    if requested_ids and not set(requested_ids) <= known:
        raise ValueError("Requested job is not registered for formal_main_v2")
    nonterminal = [row for row in jobs if accounting["jobs"][row["job_id"]]["status"] not in TERMINAL]
    selected, skipped = [], []
    for row in jobs:
        if requested_ids and row["job_id"] not in requested_ids:
            continue
        if accounting["jobs"][row["job_id"]]["status"] not in TERMINAL:
            skipped.append({"job_id": row["job_id"], "reason": "job_not_terminal"})
            continue
        blocked = [other["job_id"] for other in nonterminal if overlapping(row["run_root"], other["run_root"])]
        selected.append(dict(row, include_run_root=not blocked, active_overlapping_job_ids=blocked))
    return {"jobs": selected}, skipped


# No project imports: adding this helper must not change the GPU source contract.
# Requests are passed over SSH stdin, never interpolated into a shell command.
REMOTE_PROGRAM = r'''
import hashlib, json, os, stat, sys
from pathlib import Path
PROJECT = Path(PROJECT_LITERAL)
RESULTS = PROJECT / "results/formal_main_v2"
SLURM = PROJECT / "results/slurm"

def forbidden(path):
    parts = [part.lower() for part in path.relative_to(PROJECT).parts]
    if any(part in FORBIDDEN_PARTS or "sealed" in part or "initial_state" in part for part in parts):
        return "sealed_initial_states_or_weight_directory"
    suffixes = {x.lower() for x in path.suffixes}
    if suffixes & WEIGHT_SUFFIXES:
        return "weight_or_initial_state_suffix"
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        return "unregistered_nonweight_extension"
    return None

def panel_guard(path):
    # The rollout runner writes actual initial-state values to panel.json,
    # including after final release. Classify it using its non-state config
    # before opening or even hashing that panel. The profiling panel contains
    # only development observation references and remains transferable.
    if path.name.lower() != "panel.json":
        return None, {}
    config_path = safe(path.parent / "config.json", RESULTS)
    if not config_path.is_file():
        return "panel_without_classifying_execution_config", {}
    with open_regular(config_path) as handle:
        raw = handle.read((16 << 20) + 1)
    if len(raw) > 16 << 20:
        raise ValueError("Panel execution config exceeds the metadata bound")
    config = json.loads(raw)
    manifest = config.get("manifest", {})
    if config.get("schema") == "formal_main_v2" and config.get("kind") == "evaluation_run":
        if manifest.get("split") == "final":
            return "final_rollout_panel_contains_initial_state_values", {}
        role = "development_evaluation" if manifest.get("split") == "development" else None
    elif (config.get("version") == "formal-main-v2-control-observations-1"
          and config.get("command") == "collect" and config.get("test_opened") is False
          and manifest.get("split") == "development"):
        role = "development_profile"
    else:
        role = None
    if role is None:
        return "panel_without_development_identity", {}
    return None, {"panel_role": role, "panel_config_sha256": hashlib.sha256(raw).hexdigest()}

def safe(path, prefix):
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts or path == prefix or prefix not in path.parents:
        raise ValueError("Remote path outside exact allowed results root")
    for item in [path, *path.parents]:
        if item.is_symlink():
            raise ValueError("Symlink evidence is forbidden: " + str(path))
        if item == PROJECT:
            break
    if path.resolve() != path:
        raise ValueError("Remote path alias is forbidden")
    return path

def open_regular(path):
    # On the Linux server, every ancestor and the file itself are opened without
    # following symlinks, including a replacement between inventory and read.
    if os.name == "posix":
        fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in path.parts[1:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
            result = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        finally:
            os.close(fd)
    else:  # CPU path/manifest tests only; production SSH server is Linux.
        result = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    if not stat.S_ISREG(os.fstat(result).st_mode):
        os.close(result)
        raise ValueError("Non-regular result file")
    return os.fdopen(result, "rb")

def stamp(value):
    return {"bytes": value.st_size, "mtime_ns": value.st_mtime_ns,
            "ctime_ns": value.st_ctime_ns, "device": value.st_dev, "inode": value.st_ino}

def inspect(path, *, stream=False, expected=None):
    with open_regular(path) as handle:
        before = stamp(os.fstat(handle.fileno()))
        if expected and any(before[key] != expected[key] for key in before):
            raise ValueError("Remote file changed before transfer")
        digest = hashlib.sha256()
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
            if stream:
                sys.stdout.buffer.write(block)
        after = stamp(os.fstat(handle.fileno()))
    if before != after or stamp(path.stat(follow_symlinks=False)) != before:
        raise ValueError("Remote file changed during read")
    result = dict(before, sha256=digest.hexdigest())
    if expected and result["sha256"] != expected["sha256"]:
        raise ValueError("Remote file SHA changed during transfer")
    return result

def inventory(request):
    candidates, excluded, missing = {}, [], []
    def add(path, prefix, job, kind):
        reason = forbidden(path)
        if reason or path.is_symlink():
            excluded.append({"path": str(path), "reason": reason or "symlink", "job_id": job})
            return
        safe(path, prefix)
        if not path.exists():
            missing.append({"path": str(path), "job_id": job, "kind": kind})
            return
        if not path.is_file():
            raise ValueError("Expected regular file: " + str(path))
        reason, panel_identity = panel_guard(path)
        if reason:
            excluded.append({"path": str(path), "reason": reason, "job_id": job})
            return
        entry = candidates.setdefault(str(path), {"path": str(path), "relative": path.relative_to(PROJECT).as_posix(),
                                                   "job_ids": [], "kind": kind, **panel_identity})
        if job not in entry["job_ids"]:
            entry["job_ids"].append(job)
    for job in request["jobs"]:
        root = safe(Path(job["run_root"]), RESULTS)
        if job["include_run_root"]:
            if not root.exists():
                missing.append({"path": str(root), "job_id": job["job_id"], "kind": "run_root"})
            else:
                for folder, directories, names in os.walk(root, followlinks=False):
                    for name in list(directories):
                        path = Path(folder) / name
                        parts = [x.lower() for x in path.relative_to(PROJECT).parts]
                        if path.is_symlink() or any(x in FORBIDDEN_PARTS or "sealed" in x or "initial_state" in x for x in parts):
                            directories.remove(name)
                            excluded.append({"path": str(path), "reason": "forbidden_directory_or_symlink", "job_id": job["job_id"]})
                    for name in sorted(names):
                        add(Path(folder) / name, RESULTS, job["job_id"], "run_root")
        for suffix in ("out", "err"):
            add(SLURM / (job["name"] + "_" + job["job_id"] + "." + suffix), SLURM, job["job_id"], "slurm_log")
        add(RESULTS / "job_receipts" / (job["job_id"] + ".json"), RESULTS, job["job_id"], "job_receipt")
    files = []
    for path, item in sorted(candidates.items()):
        item.update(inspect(Path(path)))
        item["job_ids"].sort()
        files.append(item)
    return {"files": files, "excluded": sorted(excluded, key=lambda x: (x["path"], x["job_id"])),
            "missing": sorted(missing, key=lambda x: (x["path"], x["job_id"]))}

if REQUEST["command"] == "inventory":
    print(json.dumps(inventory(REQUEST)))
elif REQUEST["command"] == "download":
    row = REQUEST["file"]
    prefix = SLURM if row["kind"] == "slurm_log" else RESULTS
    path = safe(Path(row["path"]), prefix)
    if forbidden(path):
        raise ValueError("Forbidden nonweight download")
    reason, panel_identity = panel_guard(path)
    if reason or any(row.get(key) != value for key, value in panel_identity.items()):
        raise ValueError("Panel identity changed or contains final state values")
    inspect(path, stream=True, expected=row)
else:
    raise ValueError("Unknown read-only command")
'''


def remote_code(request):
    constants = "\n".join(name + " = set(" + repr(sorted(value)) + ")" for name, value in (
        ("ALLOWED_SUFFIXES", ALLOWED_SUFFIXES), ("WEIGHT_SUFFIXES", WEIGHT_SUFFIXES), ("FORBIDDEN_PARTS", FORBIDDEN_PARTS)))
    return constants + "\nREQUEST = " + repr(request) + "\n" + REMOTE_PROGRAM.replace("PROJECT_LITERAL", repr(P))


def remote_inventory(request, timeout):
    command = shlex.quote(H + "/venv/bin/python") + " -"
    result = subprocess.run(SSH + [command], input=remote_code(dict(request, command="inventory")),
        text=True, capture_output=True, check=True, timeout=timeout)
    return json.loads(result.stdout)


def download_file(row, target, timeout):
    command = shlex.quote(H + "/venv/bin/python") + " -"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as handle:
        result = subprocess.run(SSH + [command], input=remote_code({"command": "download", "file": row}).encode(),
            stdout=handle, stderr=subprocess.PIPE, timeout=timeout)
        handle.flush()
        os.fsync(handle.fileno())
    if result.returncode:
        raise RuntimeError("Remote transfer failed: " + result.stderr.decode("utf-8", errors="replace"))


def local_target(row, request):
    """Validate untrusted remote inventory before creating any local path."""
    path = PurePosixPath(row["path"])
    rel = PurePosixPath(row["relative"])
    if rel.is_absolute() or ".." in rel.parts or str(rel) != row["relative"] or str(path) != row["path"] or path != PurePosixPath(P) / rel:
        raise ValueError("Remote manifest path is not canonical project-relative evidence")
    parts = [x.lower() for x in rel.parts]
    if any(any(c in part for c in '\\:*?"<>|') or any(ord(c) < 32 for c in part) or part.rstrip(". ") != part
           or re.fullmatch(r"(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part, re.I) for part in rel.parts):
        raise ValueError("Remote filename is not safe on the local Windows filesystem")
    if any(x in FORBIDDEN_PARTS or "sealed" in x or "initial_state" in x for x in parts):
        raise ValueError("Remote manifest names forbidden state/weight data")
    if {x.lower() for x in rel.suffixes} & WEIGHT_SUFFIXES or rel.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValueError("Remote manifest names a forbidden or unsupported suffix")
    if rel.name.lower() == "panel.json" and (row.get("panel_role") not in ("development_profile", "development_evaluation")
            or not re.fullmatch("[a-f0-9]{64}", row.get("panel_config_sha256", ""))):
        raise ValueError("Panel download requires a classified development execution")
    jobs = {job["job_id"]: job for job in request["jobs"]}
    if not row.get("job_ids") or not set(row["job_ids"]) <= set(jobs):
        raise ValueError("Remote manifest has unregistered job ownership")
    for job_id in row["job_ids"]:
        job = jobs[job_id]
        if row["kind"] == "run_root":
            valid = job["include_run_root"] and PurePosixPath(job["run_root"]) in path.parents
        elif row["kind"] == "slurm_log":
            valid = path in [PurePosixPath(P) / "results/slurm" / f'{job["name"]}_{job_id}.{suffix}' for suffix in ("out", "err")]
        elif row["kind"] == "job_receipt":
            valid = path == PurePosixPath(P) / f"results/{ROUND}/job_receipts/{job_id}.json"
        else:
            valid = False
        if not valid:
            raise ValueError("Remote manifest file is outside its registered job scope")
    if type(row.get("bytes")) is not int or row["bytes"] < 0 or not re.fullmatch("[a-f0-9]{64}", row.get("sha256", "")):
        raise ValueError("Invalid remote size/SHA")
    target = ROOT.joinpath(*rel.parts)
    if target.resolve() != target.absolute() or ROOT.resolve() not in target.resolve().parents:
        raise ValueError("Local evidence path resolves outside project or through an alias")
    return target


def validate_inventory(inventory, request):
    """Check the entire manifest, including Windows aliases, before transfer."""
    rows, local_names = {}, set()
    for row in inventory["files"]:
        target = local_target(row, request)
        # Windows treats names case-insensitively, even though the Linux source
        # can contain two files with distinct case. Such evidence is ambiguous.
        key = str(target.absolute()).casefold()
        if row["path"] in rows or key in local_names:
            raise ValueError("Duplicate or locally aliased remote inventory file")
        rows[row["path"]] = row
        local_names.add(key)
    for row in rows.values():
        if PurePosixPath(row["relative"]).name.lower() == "panel.json":
            config = rows.get(str(PurePosixPath(row["path"]).parent / "config.json"))
            if config is None or config["sha256"] != row["panel_config_sha256"]:
                raise ValueError("Panel classification is not bound to its inventoried config")
    return rows


def pull(requested_ids=(), *, timeout=180):
    with pull_lock():
        state_bytes = STATE.read_bytes()
        jobs = registered_jobs(json.loads(state_bytes))
        accounting = query_accounting(jobs, timeout)
        request, skipped = build_request(jobs, accounting, set(requested_ids))
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:12]
        attempt = ROOT / f"results/{ROUND}/pulls/{stamp}"
        attempt.mkdir(parents=True)
        report = {"schema": ROUND, "kind": "nonweight_pull", "started_utc": utc(), "status": "in_progress",
            "supervisor_state_sha256": hashlib.sha256(state_bytes).hexdigest(), "registered_jobs": jobs,
            "requested_job_ids": sorted(requested_ids), "selected_jobs": request["jobs"], "skipped": skipped,
            "accounting_before": accounting, "files": [], "weights_copied": False, "sealed_initial_states_copied": False,
            "scientific_completion_inferred": False, "final_evidence": False}
        atomic_json(attempt / "receipt.json", report)
        try:
            if not request["jobs"]:
                report.update(status="no_terminal_jobs", completed_utc=utc())
                atomic_json(attempt / "receipt.json", report)
                return report, attempt / "receipt.json"
            inventory = remote_inventory(request, timeout)
            atomic_json(attempt / "inventory_before.json", inventory)
            validate_inventory(inventory, request)
            for row in inventory["files"]:
                target = local_target(row, request)
                record = dict(row, local_path=str(target), action="same_sha_skipped")
                staged = attempt / "pending" / row["relative"]
                if not target.is_file() or target.stat().st_size != row["bytes"] or sha(target) != row["sha256"]:
                    download_file(row, staged, timeout)
                    if staged.stat().st_size != row["bytes"] or sha(staged) != row["sha256"]:
                        raise ValueError("Downloaded bytes differ from pre-transfer remote SHA: " + row["path"])
                    record["action"] = "downloaded_pending"
                report["files"].append(record)
            after = remote_inventory(request, timeout)
            atomic_json(attempt / "inventory_after.json", after)
            if inventory != after:
                raise ValueError("Remote evidence changed during pull; staged files remain non-final")
            report["accounting_after"] = query_accounting(jobs, timeout)
            again, _ = build_request(jobs, report["accounting_after"], set(requested_ids))
            if again != request:
                raise ValueError("Job state or shared active writer changed; staged evidence is non-final")
            if any(accounting["jobs"][row["job_id"]] != report["accounting_after"]["jobs"][row["job_id"]]
                   for row in request["jobs"]):
                raise ValueError("Terminal job accounting changed during pull; allocation cost is not final")
            if registered_jobs(json.loads(STATE.read_bytes())) != jobs:
                raise ValueError("Supervisor registration changed; re-inventory before publishing evidence")
            for record in report["files"]:
                target = local_target(record, request)
                staged = attempt / "pending" / record["relative"]
                if record["action"] == "same_sha_skipped":
                    if not target.is_file() or sha(target) != record["sha256"]:
                        raise ValueError("Previously matching local evidence changed during pull")
                    continue
                if not staged.is_file() or staged.stat().st_size != record["bytes"] or sha(staged) != record["sha256"]:
                    raise ValueError("Quarantined bytes changed before publication")
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    original_sha = sha(target)
                    previous = attempt / "previous_versions" / record["relative"]
                    previous.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(target, previous)
                    if sha(previous) != original_sha or sha(target) != original_sha:
                        raise ValueError("Local previous evidence changed before archival")
                    record.update(previous_sha256=original_sha, previous_version=str(previous))
                os.replace(staged, target)
                if sha(target) != record["sha256"]:
                    raise ValueError("Published local SHA mismatch")
                record["action"] = "downloaded_verified"
            report.update(status="verified_nonweight_snapshot", completed_utc=utc(), final_evidence=True,
                missing=inventory["missing"], excluded=inventory["excluded"], inventory_sha256=sha(attempt / "inventory_before.json"))
            atomic_json(attempt / "receipt.json", report)
            return report, attempt / "receipt.json"
        except BaseException as error:
            report.update(status="failed_nonfinal", completed_utc=utc(), error_type=type(error).__name__, error=str(error))
            atomic_json(attempt / "receipt.json", report)
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", action="append", default=[], help="Registered formal job ID; repeat to select several")
    parser.add_argument("--timeout-seconds", type=int, default=180, help="Per SSH call timeout")
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("timeout-seconds must be positive")
    report, path = pull(args.job_id, timeout=args.timeout_seconds)
    print(json.dumps({"status": report["status"], "files": len(report["files"]), "skipped_jobs": report["skipped"],
        "receipt": str(path), "weights_copied": False, "scientific_completion_inferred": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()

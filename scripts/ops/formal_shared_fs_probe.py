"""Bounded, CPU-only two-node probe of project-local flock/SQLite locking.

Production uses only a fresh /share probe directory and copies JSON evidence to
the project's SSD results directory. Local smoke evidence is never a cross-node
pass. No training package, model, dataset, initial state or cache is opened.
"""
from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import socket
import sqlite3
import sys
import time
from datetime import datetime, timezone


VERSION = "formal-shared-fs-lock-probe-v1"
PROJECT = Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
SHARED_PROJECT = Path("/share/home/u15016/XXY_CVPR/CTI-VLA")
SQLITE_TIMEOUT_SECONDS = 1.5


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    if path.exists():
        raise FileExistsError("Refuse to replace probe evidence: " + str(path))
    temporary = path.with_name(path.name + "." + str(os.getpid()) + ".partial")
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def lock(handle, *, release=False, nonblocking=False, smoke=False):
    if os.name == "nt":
        if not smoke:
            raise RuntimeError("Production probe requires POSIX flock")
        import msvcrt
        handle.seek(0)
        mode = msvcrt.LK_UNLCK if release else msvcrt.LK_NBLCK
        msvcrt.locking(handle.fileno(), mode, 1)
    else:
        import fcntl
        mode = fcntl.LOCK_UN if release else fcntl.LOCK_EX
        if nonblocking and not release:
            mode |= fcntl.LOCK_NB
        fcntl.flock(handle.fileno(), mode)


class Probe:
    def __init__(self, args):
        self.args = args
        self.started = time.monotonic()
        self.deadline = self.started + args.timeout_seconds
        self.script_sha = digest(__file__)
        if not re.fullmatch(r"[a-f0-9]{64}", args.expected_script_sha256):
            raise ValueError("Expected source SHA256 is required")
        if self.script_sha != args.expected_script_sha256:
            raise ValueError("Probe source differs from root-registered SHA256")
        if args.local_smoke:
            if args.rank not in (0, 1) or args.node_id not in (0, 1):
                raise ValueError("Local smoke requires explicit rank/node-id 0 or 1")
            if not args.job_id or not re.fullmatch(r"smoke-[A-Za-z0-9_-]+", args.job_id):
                raise ValueError("Local smoke requires a new smoke-* job identifier")
            self.rank, self.node_id, self.job = args.rank, args.node_id, args.job_id
            local = Path(__file__).resolve().parents[2]
            self.directory = local / ".local/fs_parallel_probe" / self.job
            self.output = self.directory / "local_smoke_results"
        else:
            if any(value is not None for value in (args.rank, args.node_id, args.job_id)):
                raise ValueError("Production identity comes exclusively from Slurm")
            if os.name != "posix":
                raise RuntimeError("Production requires Linux/POSIX")
            self.job = os.environ.get("SLURM_JOB_ID", "")
            self.rank = int(os.environ.get("SLURM_PROCID", "-1"))
            self.node_id = int(os.environ.get("SLURM_NODEID", "-1"))
            if (not self.job.isascii() or not self.job.isdigit() or self.rank not in (0, 1)
                    or self.node_id not in (0, 1)
                    or os.environ.get("SLURM_NTASKS") != "2"
                    or os.environ.get("SLURM_NNODES", os.environ.get("SLURM_JOB_NUM_NODES")) != "2"):
                raise ValueError("Production requires exactly two Slurm nodes, one rank each")
            for key in ("SLURM_GPUS", "SLURM_GPUS_ON_NODE", "SLURM_GPUS_PER_TASK"):
                if os.environ.get(key) not in (None, "", "0"):
                    raise ValueError("CPU-only probe cannot use a GPU allocation")
            self.directory = SHARED_PROJECT / ".local/fs_parallel_probe" / self.job
            self.output = PROJECT / "results/formal_main_v2/preflight/fs_parallel_probe" / self.job
        self.host = socket.gethostname()
        self.identity = dict(version=VERSION, job_id=self.job, rank=self.rank,
            node_id=self.node_id, host=self.host, pid=os.getpid(),
            local_smoke=args.local_smoke, script_sha256=self.script_sha)
        self.initialized = False
        self.events = None
        self.checks = {}

    def event(self, event, **values):
        row = dict(self.identity, event=event, utc=utc(),
            rank_elapsed_seconds=time.monotonic() - self.started, **values)
        self.events.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
        self.events.flush()
        os.fsync(self.events.fileno())

    def publish(self, name, **values):
        atomic_json(self.directory / (name + ".json"), dict(self.identity, utc=utc(), **values))

    def wait(self, name, *, ignore_failure=False):
        path = self.directory / (name + ".json")
        while time.monotonic() < self.deadline:
            if not ignore_failure:
                failure = self.directory / ("rank" + str(1 - self.rank) + ".failure.json")
                if failure.is_file():
                    raise RuntimeError("Peer failed: " + failure.read_text(encoding="utf-8"))
            if path.is_file():
                value = json.loads(path.read_text(encoding="utf-8"))
                if (value.get("job_id") != self.job or value.get("script_sha256") != self.script_sha
                        or value.get("local_smoke") is not self.args.local_smoke):
                    raise ValueError("Probe handshake identity mismatch: " + name)
                return value
            time.sleep(.05)
        raise TimeoutError("120s-bounded probe handshake timed out: " + name)

    def initialize(self):
        if self.rank == 0:
            parent = self.directory.parent
            parent.mkdir(parents=True, exist_ok=True)
            scope = Path(__file__).resolve().parents[2] if self.args.local_smoke else SHARED_PROJECT.resolve()
            if scope not in parent.resolve().parents:
                raise ValueError("Probe parent resolves outside project")
            self.directory.mkdir(exist_ok=False)
            self.initialized = True
            self.output.parent.mkdir(parents=True, exist_ok=True)
            output_scope = scope if self.args.local_smoke else PROJECT.resolve()
            if output_scope not in self.output.parent.resolve().parents:
                raise ValueError("Result parent resolves outside project")
            self.output.mkdir(exist_ok=False)
            self.publish("init", timeout_seconds=self.args.timeout_seconds,
                sqlite_timeout_seconds=SQLITE_TIMEOUT_SECONDS)
        else:
            self.wait("init")
            self.initialized = True
        self.events = (self.directory / f"rank{self.rank}.events.jsonl").open("x", encoding="utf-8", newline="\n")
        self.publish(f"rank{self.rank}.hello")
        peer = self.wait(f"rank{1-self.rank}.hello")
        if peer.get("rank") != 1-self.rank:
            raise ValueError("Duplicate/wrong peer rank")
        distinct = peer.get("host") != self.host and peer.get("node_id") != self.node_id
        if not self.args.local_smoke and not distinct:
            raise ValueError("Production needs two distinct hostnames and node IDs")
        self.checks["distinct_nodes"] = distinct
        self.event("participants_verified", peer_host=peer["host"], peer_node_id=peer["node_id"],
            distinct_nodes=distinct, lock_api="msvcrt_smoke_only" if os.name == "nt" else "fcntl.flock")

    def flock_test(self):
        path = self.directory / "probe.lock"
        if self.rank == 0:
            with path.open("x+b") as handle:
                handle.write(b"0"); handle.flush(); os.fsync(handle.fileno())
                lock(handle, nonblocking=True, smoke=self.args.local_smoke)
                try:
                    self.publish("flock.held")
                    blocked = self.wait("flock.blocked")
                    if blocked.get("blocked") is not True:
                        raise AssertionError("Peer did not prove exclusion")
                    self.event("flock_peer_blocked", peer_errno=blocked.get("errno"))
                finally:
                    lock(handle, release=True, smoke=self.args.local_smoke)
            self.publish("flock.released")
            acquired = self.wait("flock.acquired")
            if acquired.get("acquired") is not True:
                raise AssertionError("Peer did not acquire released flock")
        else:
            self.wait("flock.held")
            with path.open("r+b") as handle:
                try:
                    lock(handle, nonblocking=True, smoke=self.args.local_smoke)
                except OSError as exc:
                    if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                        raise
                    self.publish("flock.blocked", blocked=True, errno=exc.errno)
                    self.event("flock_nonblocking_correctly_blocked", errno=exc.errno)
                else:
                    lock(handle, release=True, smoke=self.args.local_smoke)
                    raise AssertionError("Flock did not exclude the other node")
                self.wait("flock.released")
                lock(handle, nonblocking=True, smoke=self.args.local_smoke)
                lock(handle, release=True, smoke=self.args.local_smoke)
                self.publish("flock.acquired", acquired=True)
        self.checks["flock_exclusion_then_release"] = True
        self.event("flock_check_passed")

    def connection(self):
        connection = sqlite3.connect(self.directory / "probe.sqlite3",
            timeout=SQLITE_TIMEOUT_SECONDS, isolation_level=None)
        connection.execute("PRAGMA synchronous=FULL")
        if connection.execute("PRAGMA journal_mode").fetchone()[0].lower() != "delete":
            connection.close()
            raise AssertionError("Unexpected SQLite journal mode")
        return connection

    def sqlite_test(self):
        connection = None
        try:
            if self.rank == 0:
                connection = self.connection()
                connection.execute("CREATE TABLE probe(value INTEGER NOT NULL)")
                connection.execute("INSERT INTO probe VALUES (0)")
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("UPDATE probe SET value=17")
                self.publish("sqlite.held", uncommitted_value=17)
                blocked = self.wait("sqlite.blocked")
                if blocked.get("locked") is not True or blocked.get("elapsed_seconds", 0) < 1.:
                    raise AssertionError("Peer did not prove SQLite busy timeout")
                connection.commit()
                self.publish("sqlite.committed", committed_value=17)
                updated = self.wait("sqlite.updated")
                if updated.get("read_before") != 17 or updated.get("committed_value") != 41:
                    raise AssertionError("Peer did not observe/commit expected values")
                if connection.execute("SELECT value FROM probe").fetchone() != (41,):
                    raise AssertionError("Rank0 cannot observe peer commit")
                self.publish("sqlite.confirmed", committed_value=41)
            else:
                self.wait("sqlite.held")
                connection = self.connection()
                started = time.monotonic()
                try:
                    connection.execute("BEGIN IMMEDIATE")
                except sqlite3.OperationalError as exc:
                    elapsed = time.monotonic() - started
                    if "locked" not in str(exc).lower() or elapsed < 1.:
                        raise AssertionError("Expected bounded SQLite locked timeout") from exc
                    self.publish("sqlite.blocked", locked=True, elapsed_seconds=elapsed,
                        exception_type=type(exc).__name__, exception=str(exc))
                    self.event("sqlite_correctly_locked", elapsed_seconds=elapsed, exception=str(exc))
                else:
                    connection.rollback()
                    raise AssertionError("SQLite allowed two immediate writers")
                self.wait("sqlite.committed")
                connection.execute("BEGIN IMMEDIATE")
                before = connection.execute("SELECT value FROM probe").fetchone()
                if before != (17,):
                    raise AssertionError("Rank1 did not read rank0 commit")
                connection.execute("UPDATE probe SET value=41")
                connection.commit()
                if connection.execute("SELECT value FROM probe").fetchone() != (41,):
                    raise AssertionError("Rank1 commit was not durable to its next read")
                self.publish("sqlite.updated", read_before=17, committed_value=41)
                self.wait("sqlite.confirmed")
            self.checks["sqlite_exclusion_then_visible_commits"] = True
            self.event("sqlite_check_passed", sqlite_version=sqlite3.sqlite_version, final_value=41)
        finally:
            if connection is not None:
                connection.close()

    def finish(self, error):
        if digest(__file__) != self.script_sha:
            error = error or RuntimeError("Probe script changed during execution")
        result = dict(self.identity, status="failed" if error else ("local_smoke_passed" if self.args.local_smoke else "passed"),
            cross_node_passed=not error and not self.args.local_smoke and self.checks.get("distinct_nodes", False),
            checks=self.checks, finished_utc=utc(), elapsed_seconds=time.monotonic()-self.started,
            error=None if error is None else dict(type=type(error).__name__, message=str(error)),
            probe_directory=str(self.directory), result_directory=str(self.output),
            sqlite_timeout_seconds=SQLITE_TIMEOUT_SECONDS, gpu_calls=0,
            training_or_cache_files_opened=False, original_files_deleted=False)
        if self.events is not None:
            self.event("rank_finished", status=result["status"], error=result["error"])
            self.events.close()
        if self.initialized:
            if error:
                self.publish(f"rank{self.rank}.failure", exception=result["error"])
            self.publish(f"rank{self.rank}.result", result=result)
            if self.rank == 0:
                peer = None
                try:
                    peer = self.wait("rank1.result", ignore_failure=True)["result"]
                except Exception as exc:
                    result["peer_finalization_error"] = str(exc)
                if peer is None or peer["status"] not in ("passed", "local_smoke_passed"):
                    result["status"], result["cross_node_passed"] = "failed", False
                result["ranks"] = [result.copy(), peer]
                # Only tiny JSON evidence is copied. Synthetic SQLite/lock files
                # remain in this new probe directory; no real cache is touched.
                for path in sorted(self.directory.iterdir()):
                    if path.suffix in (".json", ".jsonl"):
                        data = path.read_bytes()
                        with (self.output / path.name).open("xb") as stream:
                            stream.write(data)
                atomic_json(self.output / "summary.json", result)
        print(json.dumps({k:result[k] for k in ("version", "job_id", "rank", "host", "status", "cross_node_passed", "error", "result_directory")}, sort_keys=True), flush=True)
        return 0 if result["status"] in ("passed", "local_smoke_passed") else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-script-sha256", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--local-smoke", action="store_true")
    parser.add_argument("--rank", type=int)
    parser.add_argument("--node-id", type=int)
    parser.add_argument("--job-id")
    args = parser.parse_args()
    if not 5 <= args.timeout_seconds <= 120:
        parser.error("timeout must be 5..120 seconds")
    probe = None
    try:
        probe = Probe(args)
        if os.name == "posix":
            def timeout_handler(signum, frame):
                raise TimeoutError("Probe exceeded its bounded protocol deadline")
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(args.timeout_seconds)
        error = None
        try:
            probe.initialize()
            probe.flock_test()
            probe.sqlite_test()
        except BaseException as exc:
            error = exc
        finally:
            if os.name == "posix":
                signal.alarm(0)
        return probe.finish(error)
    except BaseException as exc:
        print(json.dumps(dict(version=VERSION, status="failed", cross_node_passed=False,
            error=dict(type=type(exc).__name__, message=str(exc)),
            rank=None if probe is None else probe.rank), sort_keys=True), flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

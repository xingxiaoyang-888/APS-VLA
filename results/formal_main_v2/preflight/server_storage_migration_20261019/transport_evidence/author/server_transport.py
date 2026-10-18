"""Project-local transport only; original scientific/dispatch code stays intact."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import time
import uuid
import fcntl

VERSION = "cti-server-control-transport-v1"
H = Path("/share/home/u15016/XXY_CVPR/CTI-VLA")
P = Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
R = H / "control_repo"
S = P / "snapshots/formal_main_v2_run_564be0995e"
BUNDLE = Path(__file__).resolve().parent
INVENTORY = "results/formal_main_v2/source/formal_main_v2_run_564be0995e.json"
INVENTORY_SHA = "5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926"
SOURCE_SHA = "dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e"
PREFIX = "CTI_SERVER_CONTROL_"
WEIGHT_SUFFIXES = {".pt", ".pth", ".bin", ".ckpt", ".safetensors", ".pkl", ".pickle",
                  ".onnx", ".h5", ".hdf5", ".model", ".pb", ".msgpack", ".init", ".pruned_init"}


def require(value, message):
    if not value:
        raise ValueError(message)


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def no_links(path):
    path = Path(path)
    require(path.is_absolute(), "absolute path required")
    for item in (path, *path.parents):
        require(not item.is_symlink(), "symlink path rejected")
    require(path.resolve() == path.absolute(), "aliased path rejected")
    return path


def project_path(value, *, copy_target=False):
    # This lexical decision happens before resolve/stat/open.
    require(isinstance(value, str) and value and "\0" not in value and "\\" not in value
            and ":" not in value, "invalid copy path")
    pp = PurePosixPath(value)
    require(pp.is_absolute() and pp.as_posix() == value and ".." not in pp.parts,
            "copy path must be canonical and absolute")
    path = Path(value)
    require(any(path != base and base in path.parents for base in (R, P, H)),
            "copy outside R/P/H project roots")
    low = [x.lower() for x in pp.parts]
    source = path.suffix == ".py" and any(x in low for x in ("src", "scripts", "tests"))
    require(not any("sealed" in x or x in {"weights", "weight", "checkpoints", "checkpoint", "test"} for x in low)
            and not any(s in WEIGHT_SUFFIXES for s in path.suffixes)
            and not any(x in value.lower() for x in ("final_registry",))
            and (source or not any(stem in x for x in low
                for stem in ("initial_state", "init_state", "final_state", "test_state")))
            and path.name.lower() != "panel.json", "weight/state copy forbidden")
    if copy_target:
        require("snapshots" not in low and S not in path.parents,
                "snapshot destination forbidden")
    return no_links(path)


def open_directory(path):
    """Walk with openat/O_NOFOLLOW so parent substitutions cannot escape."""
    path = Path(path)
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new
        return fd
    except BaseException:
        os.close(fd)
        raise


def read_regular(path):
    parent = open_directory(path.parent)
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally:
        os.close(parent)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise ValueError("regular file required")
    return fd


def signature(st):
    return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns


def copy_single(source, destination):
    src = project_path(source)
    dst = project_path(destination, copy_target=True)
    require(src != dst, "source and destination must differ")
    source_fd = read_regular(src)
    directory = None
    temporary = None
    try:
        before = os.fstat(source_fd)
        directory = open_directory(dst.parent)
        try:
            existing = os.open(dst.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        except FileNotFoundError:
            existing = None
        if existing is not None:
            try:
                initial = os.fstat(existing)
                require(stat.S_ISREG(initial.st_mode), "destination not regular")
                left, right = hashlib.sha256(), hashlib.sha256()
                with os.fdopen(os.dup(source_fd), "rb") as f:
                    for block in iter(lambda: f.read(8 << 20), b""): left.update(block)
                with os.fdopen(os.dup(existing), "rb") as f:
                    for block in iter(lambda: f.read(8 << 20), b""): right.update(block)
                require(signature(initial) == signature(os.fstat(existing))
                        and signature(before) == signature(os.fstat(source_fd)), "file changed during comparison")
                require(left.digest() == right.digest() and before.st_size == initial.st_size,
                        "refuse overwriting different destination bytes")
                return dict(action="same_bytes_no_write", bytes=before.st_size, sha256=left.hexdigest())
            finally:
                os.close(existing)
        temporary = "." + dst.name + ".transport-" + uuid.uuid4().hex + ".partial"
        out = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
        h = hashlib.sha256()
        count = 0
        with os.fdopen(out, "wb") as target, os.fdopen(os.dup(source_fd), "rb") as source_stream:
            for block in iter(lambda: source_stream.read(8 << 20), b""):
                target.write(block); h.update(block); count += len(block)
            target.flush(); os.fsync(target.fileno())
        require(signature(before) == signature(os.fstat(source_fd)) and count == before.st_size,
                "source changed during copy")
        # Exclusive atomic publication. An unrelated pre-existing file is never replaced.
        os.link(temporary, dst.name, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
        os.unlink(temporary, dir_fd=directory); temporary = None
        os.fsync(directory)
        return dict(action="copied_exclusive", bytes=count, sha256=h.hexdigest())
    finally:
        if temporary is not None and directory is not None:
            # Preserve failed transfer bytes for root inspection; no implicit repair.
            pass
        os.close(source_fd)
        if directory is not None: os.close(directory)


def verify_bundle(expected):
    require(re.fullmatch("[0-9a-f]{64}", expected or ""), "bundle SHA missing")
    manifest = no_links(BUNDLE / "bundle_manifest.json")
    require(file_sha(manifest) == expected, "bundle manifest SHA differs")
    data = json.loads(manifest.read_bytes())
    require(data.get("version") == VERSION and data.get("kind") == "server_control_transport_bundle"
            and data.get("control_root") == str(R) and data.get("runtime_root") == str(P),
            "transport bundle identity differs")
    expected_paths = {"server_transport.py", "run_server_control.py", "bin/ssh", "bin/scp"}
    require(set(data.get("files", {})) == expected_paths, "bundle file set differs")
    for rel, checksum in data["files"].items():
        path = no_links(BUNDLE / rel)
        require(file_sha(path) == checksum, "transport source SHA differs: " + rel)
    return data


def verify_frozen():
    inventory_path = no_links(R / INVENTORY)
    require(file_sha(inventory_path) == INVENTORY_SHA, "frozen inventory SHA differs")
    inv = json.loads(inventory_path.read_bytes())
    require(len(inv["files"]) == 173 and inv["source_sha256"] == SOURCE_SHA
            and inv["source_root_server"] == str(S), "frozen inventory identity differs")
    for rel, checksum in inv["files"].items():
        pp = PurePosixPath(rel)
        require(not pp.is_absolute() and pp.as_posix() == rel and ".." not in pp.parts,
                "noncanonical frozen source")
        for base in (R, S):
            require(file_sha(no_links(base / rel)) == checksum, "frozen bytes differ: " + str(base / rel))
    return inv["files"]


def journal_path(value):
    require(isinstance(value, str), "audit path missing")
    pp = PurePosixPath(value)
    prefix = R / "results/formal_main_v2/control_transport"
    path = Path(value)
    require(pp.is_absolute() and pp.as_posix() == value and ".." not in pp.parts
            and path.parent == prefix and path.suffix == ".jsonl",
            "audit must be a single new control_transport JSONL")
    return no_links(path)


def emit(path, event, **fields):
    row = dict(version=VERSION, event=event, time_ns=time.time_ns(), pid=os.getpid(),
               parent_pid=os.getppid(), **fields)
    directory = open_directory(path.parent)
    try:
        fd = os.open(path.name, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW, dir_fd=directory)
    finally:
        os.close(directory)
    with os.fdopen(fd, "ab") as f:
        require(stat.S_ISREG(os.fstat(f.fileno()).st_mode), "audit is not regular")
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write((json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode())
        f.flush(); os.fsync(f.fileno())


def scope():
    require(os.environ.get(PREFIX + "ROOT") == str(R)
            and os.environ.get(PREFIX + "BIN") == str(BUNDLE / "bin")
            and os.environ.get(PREFIX + "VERSION") == VERSION, "inactive or different control scope")
    verify_bundle(os.environ.get(PREFIX + "MANIFEST_SHA256"))
    cwd = no_links(Path.cwd())
    require(cwd == R or R in cwd.parents, "transport only active from control repository")
    return journal_path(os.environ.get(PREFIX + "JOURNAL"))


def run_ssh(argv):
    require(len(argv) == 4 and argv[:3] == ["-o", "BatchMode=yes", "tongji-cvpr"]
            and isinstance(argv[3], str) and argv[3] and "\0" not in argv[3],
            "unsupported SSH host/options/command shape")
    audit = scope()
    token = uuid.uuid4().hex
    # Login initialization supplies the same cluster tools as the SSH login.
    # Then restore only this child scope's PATH and cwd, passing the original
    # command as a separate argument (no string interpolation).
    bootstrap = 'export PATH="$CTI_SERVER_CONTROL_BIN:$PATH"; cd -- "$CTI_SERVER_CONTROL_ROOT" || exit 125; exec /bin/bash -c "$1"'
    actual = ["/bin/bash", "-lc", bootstrap, "cti-server-control", argv[3]]
    emit(audit, "ssh_start", call_id=token, original_argv=["ssh", *argv], actual_argv=actual,
         command_sha256=hashlib.sha256(argv[3].encode()).hexdigest(), cwd=str(Path.cwd()))
    code = 125
    try:
        code = subprocess.run(actual, cwd=R, env=os.environ.copy()).returncode
        return code if code >= 0 else 128 - code
    finally:
        emit(audit, "ssh_end", call_id=token, returncode=code)


def parse_scp(argv):
    require(len(argv) == 3 and argv[0] == "-q", "only quiet single-file SCP is supported")
    endpoints = argv[1:]
    remote = [x.startswith("tongji-cvpr:") for x in endpoints]
    require(sum(remote) == 1, "SCP requires exactly one tongji-cvpr endpoint")
    paths = []
    for item, is_remote in zip(endpoints, remote):
        value = item[len("tongji-cvpr:"):] if is_remote else item
        if not is_remote and not value.startswith("/"):
            require(":" not in value and ".." not in PurePosixPath(value).parts, "unknown host/traversal")
            value = str(Path.cwd() / value)
        paths.append(value)
    project_path(paths[0]); project_path(paths[1], copy_target=True)
    return paths


def run_scp(argv):
    source, destination = parse_scp(argv)
    audit = scope()
    token = uuid.uuid4().hex
    emit(audit, "scp_start", call_id=token, original_argv=["scp", *argv],
         source=source, destination=destination)
    try:
        result = copy_single(source, destination)
    except BaseException as exc:
        emit(audit, "scp_end", call_id=token, returncode=1, error_type=type(exc).__name__, message=str(exc))
        raise
    emit(audit, "scp_end", call_id=token, returncode=0, **result)
    return 0


def shim_main(kind, argv):
    try:
        return (run_ssh if kind == "ssh" else run_scp)(argv)
    except Exception as exc:
        print("CTI control transport rejected: " + str(exc), file=sys.stderr)
        return 255 if kind == "ssh" else 1

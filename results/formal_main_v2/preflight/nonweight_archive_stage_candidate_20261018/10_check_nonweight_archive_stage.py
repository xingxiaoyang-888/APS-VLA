"""Read-only Git-index delivery check for one explicit nonweight archive.

Only the new project-local scratch clone is written. Git is never asked to
add/remove/refresh/commit anything. This checks delivery bytes, not science.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile


SCHEMA = "cti_nonweight_archive_stage_v1"
VERSION = "nonweight-index-stage-1"
LIMIT = 100 << 20
INVENTORY = "results/formal_main_v2/source/formal_main_v2_run_564be0995e.json"
INVENTORY_SHA256 = "5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926"
FROZEN_COUNT = 173
CODEC = "scripts/ops/nonweight_archive.py"
CODEC_SHA256 = "f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2"
SELF = "scripts/ops/check_nonweight_archive_stage.py"
WEIGHT_SUFFIXES = {".pt", ".pth", ".bin", ".ckpt", ".safetensors", ".pkl", ".pickle",
                   ".onnx", ".model", ".pb", ".msgpack", ".h5", ".hdf5", ".init", ".pruned_init"}


class StageError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise StageError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_codec():
    path = Path(__file__).parent / "nonweight_archive.py"
    require(sha(path.read_bytes()) == CODEC_SHA256, "Audited codec source changed")
    spec = importlib.util.spec_from_file_location("_pinned_nonweight_archive", path)
    codec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    return codec


def lexical(value, *, payload=True):
    require(isinstance(value, str) and value and "\\" not in value, "Use canonical relative paths")
    path = PurePosixPath(value)
    require(not path.is_absolute() and str(path) == value and ".." not in path.parts, "Unsafe repository path")
    for part in path.parts:
        require(part == part.rstrip(". ") and part not in (".", "..", ".git")
                and not any(c in part for c in '\\:*?"<>|') and not any(ord(c) < 32 for c in part)
                and re.fullmatch(r"(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part, re.I) is None,
                "Aliased repository path")
    require(not ({s.lower() for s in path.suffixes} & WEIGHT_SUFFIXES), "Weight/state payload forbidden")
    source = path.parts[0] in {"src", "scripts", "tests"} and path.suffix == ".py"
    require(not any(p.lower() in {"weights", "checkpoints", "checkpoint"}
                    or (p.lower() == "models" and not source) for p in path.parts), "Weight directory forbidden")
    if not payload:
        return path  # Index names/sizes only; never open pre-existing state values.
    require(not any(p.lower() == "test" or "sealed" in p.lower() for p in path.parts),
            "Sealed/test directory forbidden")
    # Scientific source names can describe state handling; data cannot bypass
    # the codec's state-value boundary by being submitted as required evidence.
    require(source or not any(stem in p.lower() for p in path.parts
                             for stem in ("init_state", "initial_state", "final_state", "test_state")),
            "State-value metadata forbidden")
    require(path.name.lower() != "panel.json" or "final" not in {p.lower() for p in path.parts},
            "Final state-value panel forbidden")
    return path


def local_path(root, name, codec):
    path = lexical(name)
    current = root
    for part in path.parts[:-1]:
        current /= part
        require(codec.no_link(current, directory=True) is not None, "Missing local parent")
    target = root.joinpath(*path.parts)
    require(codec.no_link(target) is not None, "Missing local retained file: " + name)
    return target


def local_bytes(root, name, codec, *, maximum=LIMIT):
    target = local_path(root, name, codec)
    before = codec.no_link(target)
    require(before.st_size <= maximum, "Local file exceeds size bound")
    with target.open("rb") as stream:
        initial = os.fstat(stream.fileno())
        require(codec.stable_id(initial) == codec.stable_id(before), "Local file changed before read")
        data = stream.read(maximum + 1)
        after = codec.no_link(local_path(root, name, codec))
        require(after is not None and codec.stable_id(initial) == codec.stable_id(after)
                == codec.stable_id(os.fstat(stream.fileno())), "Local file changed during read")
    require(len(data) <= maximum, "Local file exceeds size bound")
    return data


class Index:
    """One immutable logical index view and a read-only cat-file process."""
    def __init__(self, root):
        self.root = root
        self.env = dict(os.environ)
        for key in list(self.env):
            if key.startswith("GIT_"):
                self.env.pop(key)
        self.env["GIT_OPTIONAL_LOCKS"] = "0"
        top = Path(self.git("rev-parse", "--show-toplevel").decode().strip())
        require(top.absolute() == root, "Project root is not the Git worktree root")
        self.format = self.git("rev-parse", "--show-object-format").decode().strip()
        require(self.format in ("sha1", "sha256"), "Unsupported Git object format")
        self.before = self.snapshot()
        self.entries = {}
        for row in self.before[0].split(b"\0"):
            if not row:
                continue
            header, raw_path = row.split(b"\t", 1)
            mode, oid, stage = header.decode("ascii").split()
            name = raw_path.decode("utf-8")
            # Listing is not payload access. Protected source names are allowed
            # here; later content reads use the same strict lexical boundary.
            lexical(name, payload=False)
            require(stage == "0" and mode in ("100644", "100755"), "Unmerged/symlink/submodule index entry")
            require(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", oid), "Invalid Git object id")
            require(name not in self.entries, "Duplicate index path")
            self.entries[name] = {"mode": mode, "oid": oid}
        require(len({p.casefold() for p in self.entries}) == len(self.entries), "Windows-aliased index paths")
        identifiers = sorted({row["oid"] for row in self.entries.values()})
        metadata = self.git("cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)",
                            data=("\n".join(identifiers) + "\n").encode())
        rows = metadata.decode("ascii").splitlines()
        require(len(rows) == len(identifiers), "Incomplete index object size inventory")
        self.sizes = {}
        for wanted, line in zip(identifiers, rows):
            oid, kind, size = line.split()
            require(oid == wanted and kind == "blob" and size.isdecimal() and int(size) <= LIMIT,
                    "Index has missing/nonblob/over-100MiB content")
            self.sizes[oid] = int(size)
        self.changed = self.parse_changes(self.before[1])
        self.reader = subprocess.Popen(self.command("cat-file", "--batch"), env=self.env,
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.cache = {}

    def command(self, *args):
        return ["git", "-c", "core.quotePath=false", "-C", str(self.root), *args]

    def git(self, *args, data=None):
        result = subprocess.run(self.command(*args), input=data, env=self.env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        require(result.returncode == 0, "Read-only Git command failed: " + result.stderr.decode("utf-8", "replace"))
        return result.stdout

    def snapshot(self):
        head = self.git("rev-parse", "--verify", "HEAD").strip()
        return (self.git("ls-files", "--stage", "-z"),
                self.git("diff", "--cached", "--name-status", "--no-renames", "--no-ext-diff", "--no-textconv", "-z"), head)

    @staticmethod
    def parse_changes(data):
        rows = data.split(b"\0")
        require(rows[-1] == b"" and (len(rows) - 1) % 2 == 0, "Malformed staged name/status output")
        result = {}
        for status, path in zip(rows[0:-1:2], rows[1:-1:2]):
            name = path.decode("utf-8"); lexical(name, payload=False)
            require(status in (b"A", b"M", b"D", b"T") and name not in result, "Unknown staged change")
            result[name] = status.decode()
        return result

    def blob(self, name):
        lexical(name)
        require(name in self.entries, "Missing required index blob: " + name)
        row = self.entries[name]
        if row["oid"] in self.cache:
            return self.cache[row["oid"]]
        self.reader.stdin.write(row["oid"].encode() + b"\n"); self.reader.stdin.flush()
        header = self.reader.stdout.readline().decode("ascii").strip().split()
        size = self.sizes[row["oid"]]
        require(header == [row["oid"], "blob", str(size)], "Index object identity changed")
        chunks, remaining = [], size
        while remaining:
            block = self.reader.stdout.read(min(1 << 20, remaining))
            require(block, "Truncated Git blob")
            chunks.append(block); remaining -= len(block)
        data = b"".join(chunks)
        require(self.reader.stdout.read(1) == b"\n", "Invalid Git blob framing")
        oid = hashlib.new(self.format, b"blob " + str(size).encode() + b"\0" + data).hexdigest()
        require(oid == row["oid"], "Git blob does not match index object identity")
        if size <= 1 << 20:
            self.cache[row["oid"]] = data
        return data

    def unchanged(self):
        require(self.snapshot() == self.before, "Git index or HEAD changed during review")

    def close(self):
        self.reader.stdin.close()
        remaining = self.reader.stdout.read()
        errors = self.reader.stderr.read()
        code = self.reader.wait()
        require(code == 0 and not remaining, "Read-only Git object process failed: " + errors.decode("utf-8", "replace"))


@contextmanager
def index_reader(root):
    index = Index(root)
    try:
        yield index
    finally:
        index.close()


def same_local_index(index, name, codec, expected=None):
    data = index.blob(name)
    require(local_bytes(index.root, name, codec) == data, "Working tree differs from index: " + name)
    ref = {"path": name, "sha256": sha(data), "bytes": len(data)}
    if expected is not None:
        require(ref == expected, "Required index SHA/bytes differ: " + name)
    return data, ref


def required_value(value, codec):
    codec.exact(value, ("schema", "kind", "files"), "Required delivery list")
    require(value["schema"] == SCHEMA and value["kind"] == "required_files", "Unknown required-files format")
    require(isinstance(value["files"], list) and 0 < len(value["files"]) <= 100000, "Explicit required files missing")
    for row in value["files"]:
        codec.exact(row, ("path", "sha256", "bytes"), "Required file")
        lexical(row["path"]); codec.checksum(row["sha256"]); codec.integer(row["bytes"])
    codec.unique_paths(value["files"])
    return value["files"]


def extract_archive(index, clone, snapshot, snapshot_sha256, codec, watched):
    def copy(ref, role):
        codec.reference(ref, role)
        data, actual = same_local_index(index, ref["path"], codec, ref)
        if ref["path"] in watched:
            require(watched[ref["path"]] == actual, "Conflicting archive references")
        else:
            target = codec.checked_path(clone, ref["path"], role)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream: stream.write(data)
            watched[ref["path"]] = actual
        return data

    data, ref = same_local_index(index, snapshot, codec)
    require(ref["sha256"] == snapshot_sha256, "Snapshot index SHA differs")
    value = codec.decoded(copy(ref, "snapshot"))
    codec.exact(value, ("schema", "kind", "raw_chunk_bytes", "producer", "request", "provenance", "files"), "Snapshot")
    request = codec.request_value(codec.decoded(copy(value["request"], "metadata")))
    require(value["provenance"] == sorted(request["provenance"], key=lambda x: x["path"]), "Snapshot/request provenance differs")
    for row in value["provenance"]:
        copy(row, "metadata")
    require(isinstance(value["files"], list) and len(value["files"]) == len(request["files"]), "Snapshot file count differs")
    for row, original in zip(value["files"], sorted(request["files"], key=lambda x: x["path"])):
        codec.exact(row, ("path", "sha256", "bytes", "manifest"), "Snapshot mapping")
        require({k: row[k] for k in ("path", "sha256", "bytes")} == original, "Snapshot mapping differs")
        obj = codec.object_value(codec.decoded(copy(row["manifest"], "archive")), row["sha256"], row["bytes"])
        for part in obj["chunks"]:
            copy({"path": part["path"], "sha256": part["compressed_sha256"], "bytes": part["compressed_bytes"]}, "archive")
    return value


def compare_originals(root, clone, ref, codec):
    codec.verify_ref(root, ref, "raw")
    codec.verify_ref(clone, ref, "raw")
    with codec.opened(root, ref["path"], "raw") as left, codec.opened(clone, ref["path"], "raw") as right:
        while True:
            a, b = left.read(1 << 20), right.read(1 << 20)
            require(a == b, "Restored bytes differ from retained original")
            if not a: break


def check(project, snapshot, snapshot_sha256, raw_paths, required_files):
    codec = load_codec()
    codec.lexical(snapshot, "snapshot"); codec.lexical(required_files, "metadata"); codec.checksum(snapshot_sha256)
    require(isinstance(raw_paths, list) and raw_paths, "Explicit raw-path whitelist required")
    for name in raw_paths: codec.lexical(name, "raw")
    require(len({p.casefold() for p in raw_paths}) == len(raw_paths), "Duplicate raw whitelist path")
    root = codec.project_root(project)
    tool_sha = sha(Path(__file__).read_bytes())
    with index_reader(root) as index:
        # The fixed inventory must be present in both places and itself pinned.
        inv_data, inv_ref = same_local_index(index, INVENTORY, codec)
        require(inv_ref["sha256"] == INVENTORY_SHA256, "Formal frozen inventory pin differs")
        inventory = codec.decoded(inv_data)
        require(isinstance(inventory.get("files"), dict) and len(inventory["files"]) == FROZEN_COUNT, "Frozen inventory count differs")
        frozen = {}
        for name, expected in inventory["files"].items():
            require(name not in index.changed, "Frozen scientific file is staged: " + name)
            _, ref = same_local_index(index, name, codec)
            require(ref["sha256"] == expected, "Frozen source SHA differs: " + name)
            frozen[name] = ref
        for name, expected in ((CODEC, CODEC_SHA256), (SELF, tool_sha)):
            _, ref = same_local_index(index, name, codec)
            require(ref["sha256"] == expected, "Archive implementation not delivered byte-exactly: " + name)
        raw_set = set(raw_paths)
        require(not raw_set.intersection(index.entries), "Archived raw must be absent from index, even if below 100MiB")
        checked = {}
        markdown = []
        for name, status in index.changed.items():
            if status == "D":
                require(name in raw_set, "Non-whitelisted staged deletion: " + name)
            else:
                require(status in ("A", "M"), "Staged type change forbidden")
                local_path(root, name, codec)
                if name.endswith(".md"):
                    markdown.append(name)  # Existing staging convention only.
                else:
                    _, checked[name] = same_local_index(index, name, codec)
        required_data, required_ref = same_local_index(index, required_files, codec)
        require(len(required_data) <= codec.METADATA_LIMIT, "Required list too large")
        required = required_value(codec.decoded(required_data), codec)
        require(required_files not in {r["path"] for r in required}, "Self-referencing required list")
        # All required bytes are checked regardless of the legacy .md exception.
        for row in required:
            if row["path"] not in raw_set:
                _, checked[row["path"]] = same_local_index(index, row["path"], codec, row)
        scratch_parent = root / ".local"
        if codec.no_link(scratch_parent, directory=True) is None: scratch_parent.mkdir()
        require(codec.no_link(scratch_parent, directory=True) is not None, "Unsafe scratch parent")
        clone = Path(tempfile.mkdtemp(prefix="nonweight-index-review-", dir=scratch_parent))
        archive = {}
        value = extract_archive(index, clone, snapshot, snapshot_sha256, codec, archive)
        mappings = [{k: row[k] for k in ("path", "sha256", "bytes")} for row in value["files"]]
        require({r["path"] for r in mappings} == raw_set and len(mappings) == len(raw_paths), "Whitelist must exactly equal all snapshot entries")
        by_path = {r["path"]: r for r in mappings}
        for row in required:
            if row["path"] in raw_set: require(by_path[row["path"]] == row, "Required raw differs from snapshot")
        # No raw data is copied from the worktree into this clone.
        verified = codec.verify(clone, snapshot, snapshot_sha256)
        restored = codec.restore(clone, snapshot, snapshot_sha256)
        for row in mappings: compare_originals(root, clone, row, codec)
        for name, ref in {INVENTORY: inv_ref, required_files: required_ref, **frozen, **checked, **archive}.items():
            same_local_index(index, name, codec, ref)
        require(sha(Path(__file__).read_bytes()) == tool_sha, "Stage checker source changed")
        require(sha((Path(__file__).parent / "nonweight_archive.py").read_bytes()) == CODEC_SHA256, "Codec source changed")
        index.unchanged()
        return {"schema": SCHEMA, "version": VERSION, "status": "verified_index_archive_delivery",
                "snapshot": snapshot, "snapshot_sha256": snapshot_sha256, "scratch_clone": clone.relative_to(root).as_posix(),
                "index_sha256": sha(index.before[0]), "staged_changes_sha256": sha(index.before[1]),
                "head": index.before[2].decode(), "index_files_checked_for_size_and_mode": len(index.entries),
                "ordinary_staged_files_verified": len(checked), "markdown_legacy_byte_exceptions": sorted(markdown),
                "allowed_raw_deletions": sorted(p for p in raw_paths if index.changed.get(p) == "D"),
                "raw_paths_restored_exactly": mappings, "required_files": required_ref, "required_count": len(required),
                "archive_index_files": archive, "frozen_inventory_sha256": INVENTORY_SHA256,
                "frozen_files_verified_in_worktree_and_index": len(frozen), "codec_sha256": CODEC_SHA256,
                "checker_sha256": tool_sha, "archive_verification": verified["status"], "restore_verification": restored["status"],
                "git_write_commands": False, "real_originals_changed": False, "scientific_completion_inferred": False,
                "gpu_seconds": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--snapshot-sha256", required=True)
    parser.add_argument("--raw-path", action="append", required=True)
    parser.add_argument("--required-files", required=True)
    args = parser.parse_args(argv)
    try:
        result = check(args.project_root, args.snapshot, args.snapshot_sha256, args.raw_path, args.required_files)
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"status": "rejected", "error_type": type(error).__name__, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

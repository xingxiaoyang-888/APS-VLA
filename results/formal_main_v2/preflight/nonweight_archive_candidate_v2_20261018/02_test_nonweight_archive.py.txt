"""Isolated, synthetic byte archives only: no real evidence, Git, SSH or GPU."""
from copy import deepcopy
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/ops/nonweight_archive.py"
spec = importlib.util.spec_from_file_location("archive_under_test", SCRIPT)
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
REQUEST = "results/requests/synthetic.json"
SNAPSHOT = a.PREFIX + "/snapshots/synthetic.json"


def put(root, name, data):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"path": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def case(root, files=None, *, request_name=REQUEST):
    root.mkdir(parents=True, exist_ok=True)
    files = files or {"results/synthetic/a.jsonl": b'{"synthetic":true}\r\n\xe6\xb1\x89\x00\xff'}
    refs = [put(root, path, data) for path, data in files.items()]
    provenance = put(root, "results/provenance/synthetic_root_review.json", b'{"synthetic":true}\n')
    request = {"schema": a.SCHEMA, "kind": "archive_request", "files": refs, "provenance": [provenance]}
    put(root, request_name, a.encoded(request))
    return files, request


def packed(root, files=None):
    files, request = case(root, files)
    result = a.pack(root, REQUEST, SNAPSHOT)
    return files, request, result


def clone_package(source, target):
    target.mkdir(parents=True)
    for name in (a.PREFIX, "results/requests", "results/provenance"):
        shutil.copytree(source / name, target / name)
    return target


def snapshot(root):
    return json.loads((root / SNAPSHOT).read_bytes())


def rebound_object(root, edit):
    """Rebind synthetic outer SHAs to exercise semantic validation, not only SHA."""
    snap = snapshot(root)
    obj_ref = snap["files"][0]["manifest"]
    obj = json.loads((root / obj_ref["path"]).read_bytes())
    edit(obj)
    updated = put(root, obj_ref["path"], a.encoded(obj))
    for row in snap["files"]:
        if row["manifest"]["path"] == updated["path"]:
            row["manifest"] = updated
    return put(root, SNAPSHOT, a.encoded(snap))["sha256"]


def rebound_chunk(root, payload):
    def edit(obj):
        row = obj["chunks"][0]
        ref = put(root, a.PREFIX + "/chunks/sha256/" + a.digest(payload) + ".gz", payload)
        row.update(path=ref["path"], compressed_sha256=ref["sha256"], compressed_bytes=ref["bytes"])
    return rebound_object(root, edit)


def test_real_16mib_boundary_dedup_and_roundtrip(tmp_path):
    # The first Chinese UTF8 character straddles the fixed raw byte boundary.
    common = b"x" * (a.CHUNK_BYTES - 1) + "汉".encode()
    first, second = common + b'\r\n{"tail":1}', common + b"\x00\xffno-final-LF"
    files = {"results/synthetic/中文/a.jsonl": first, "results/synthetic/copy.jsonl": first,
             "results/synthetic/b.jsonl": second, "results/synthetic/empty.jsonl": b""}
    source = tmp_path / "source"
    _, _, report = packed(source, files)
    assert report["unique_objects"] == 3
    assert report["unique_compressed_chunks"] == 3
    assert all((source / path).read_bytes() == data for path, data in files.items())
    snap = snapshot(source)
    for row in snap["files"]:
        obj = json.loads((source / row["manifest"]["path"]).read_bytes())
        if row["bytes"]:
            assert [p["offset"] for p in obj["chunks"]] == [0, a.CHUNK_BYTES]
            assert obj["chunks"][0]["raw_bytes"] == 16 * 1024 * 1024
            for part in obj["chunks"]:
                blob = (source / part["path"]).read_bytes()
                assert blob[:10] == a.GZIP_HEADER and len(blob) < 32 * 1024 * 1024
    clone = clone_package(source, tmp_path / "clone")
    assert a.verify(clone, SNAPSHOT, report["snapshot_sha256"])["status"] == "verified"
    restored = a.restore(clone, SNAPSHOT, report["snapshot_sha256"])
    assert all(row["action"] == "restored" for row in restored["paths"])
    for path, data in files.items():
        assert (clone / path).read_bytes() == data
    identities = {p: ((clone / p).stat().st_ino, (clone / p).stat().st_mtime_ns) for p in files}
    again = a.restore(clone, SNAPSHOT, report["snapshot_sha256"])
    assert all(row["action"] == "same_bytes_present" for row in again["paths"])
    assert identities == {p: ((clone / p).stat().st_ino, (clone / p).stat().st_mtime_ns) for p in files}


def test_reproducible_pack_and_same_snapshot_idempotence(tmp_path):
    roots = [tmp_path / "one", tmp_path / "two"]
    reports = [packed(root)[2] for root in roots]
    assert reports[0]["snapshot_sha256"] == reports[1]["snapshot_sha256"]
    for path in (roots[0] / a.PREFIX).rglob("*"):
        if path.is_file() and path.name != ".writer.lock":
            assert path.read_bytes() == (roots[1] / path.relative_to(roots[0])).read_bytes()
    before = (roots[0] / SNAPSHOT).stat().st_mtime_ns
    assert a.pack(roots[0], REQUEST, SNAPSHOT)["snapshot_sha256"] == reports[0]["snapshot_sha256"]
    assert (roots[0] / SNAPSHOT).stat().st_mtime_ns == before


def test_append_version_keeps_both_original_sha_snapshots(tmp_path):
    root = tmp_path / "project"
    original, _, first = packed(root)
    raw = next(iter(original))
    old_request = (root / REQUEST).read_bytes()
    _, request = case(root, {raw: original[raw] + b"\nnew attempt\n"}, request_name="results/requests/v2.json")
    new_snapshot = a.PREFIX + "/snapshots/v2.json"
    second = a.pack(root, "results/requests/v2.json", new_snapshot)
    assert first["snapshot_sha256"] != second["snapshot_sha256"]
    assert (root / REQUEST).read_bytes() == old_request
    assert a.verify(root, SNAPSHOT, first["snapshot_sha256"])["status"] == "verified"
    assert a.verify(root, new_snapshot, second["snapshot_sha256"])["status"] == "verified"
    assert (root / raw).read_bytes() == original[raw] + b"\nnew attempt\n"


@pytest.mark.parametrize("mode", ["missing", "corrupt", "extra_bytes"])
def test_bad_chunk_rejects_before_any_restore(tmp_path, mode):
    source = tmp_path / "source"
    files, _, report = packed(source, {"results/synthetic/a.jsonl": b"first\n", "results/synthetic/z.jsonl": b"second\r\n"})
    clone = clone_package(source, tmp_path / "clone")
    obj = json.loads((clone / snapshot(clone)["files"][-1]["manifest"]["path"]).read_bytes())
    blob = clone / obj["chunks"][0]["path"]
    if mode == "missing":
        blob.unlink()
    elif mode == "corrupt":
        data = bytearray(blob.read_bytes()); data[-1] ^= 1; blob.write_bytes(data)
    else:
        blob.write_bytes(blob.read_bytes() + b"extra")
    with pytest.raises((a.ArchiveError, FileNotFoundError)):
        a.restore(clone, SNAPSHOT, report["snapshot_sha256"])
    assert all(not (clone / name).exists() for name in files)
    assert not (clone / "results/synthetic").exists()


@pytest.mark.parametrize("field,value", [("index", 1), ("offset", 1), ("raw_bytes", 1),
                                         ("compressed_bytes", a.COMPRESSED_LIMIT), ("raw_sha256", "0" * 64)])
def test_manifest_field_tampering_beyond_outer_sha(tmp_path, field, value):
    _, _, report = packed(tmp_path)
    expected = rebound_object(tmp_path, lambda obj: obj["chunks"][0].update({field: value}))
    with pytest.raises(a.ArchiveError):
        a.verify(tmp_path, SNAPSHOT, expected)


@pytest.mark.parametrize("mode", ["duplicate", "reversed", "missing"])
def test_chunk_list_index_order_and_count(tmp_path, mode):
    packed(tmp_path, {"results/synthetic/a.jsonl": b"z" * (a.CHUNK_BYTES + 5)})
    def edit(obj):
        if mode == "duplicate": obj["chunks"][1] = deepcopy(obj["chunks"][0])
        if mode == "reversed": obj["chunks"].reverse()
        if mode == "missing": obj["chunks"].pop()
    expected = rebound_object(tmp_path, edit)
    with pytest.raises(a.ArchiveError):
        a.verify(tmp_path, SNAPSHOT, expected)


@pytest.mark.parametrize("mode", ["trailing", "second_member", "truncated", "expanded", "filename", "mtime"])
def test_gzip_structural_rejection_even_rehashed(tmp_path, mode):
    files, _, report = packed(tmp_path)
    original = next(iter(files.values()))
    blob = a.compress(original)
    if mode == "trailing": blob += b"garbage"
    elif mode == "second_member": blob += a.compress(b"second")
    elif mode == "truncated": blob = blob[:-1]
    elif mode == "expanded": blob = a.compress(original + b"expansion")
    else:
        stream = io.BytesIO()
        with gzip.GzipFile(fileobj=stream, mode="wb", filename="name" if mode == "filename" else "",
                           mtime=1 if mode == "mtime" else 0, compresslevel=6) as f:
            f.write(original)
        blob = stream.getvalue()
    expected = rebound_chunk(tmp_path, blob)
    with pytest.raises(a.ArchiveError):
        a.verify(tmp_path, SNAPSHOT, expected)


@pytest.mark.parametrize("name", ["/results/x.jsonl", "C:/results/x.jsonl", "../results/x.jsonl",
    "results/a/../x.jsonl", "results//x.jsonl", "results/./x.jsonl", "results\\x.jsonl",
    "results/weights/x.jsonl", "results/models/x.jsonl", "results/checkpoints/x.jsonl",
    "results/sealed_final/x.jsonl", "results/initial_states/x.jsonl", "results/x.pt.jsonl",
    "results/CON.jsonl", "results/bad. /x.jsonl", "results/x:stream.jsonl", "outside/x.jsonl",
    "results/panel.json", a.PREFIX + "/copied.jsonl"])
def test_lexical_input_rejected_before_target_stat_or_read(tmp_path, monkeypatch, name):
    _, request = case(tmp_path)
    request["files"][0]["path"] = name
    put(tmp_path, REQUEST, a.encoded(request))
    visited = []
    original = a.checked_path
    def spy(root, relative, role):
        visited.append(relative)
        assert relative != name, "The invalid original reached filesystem checks"
        return original(root, relative, role)
    monkeypatch.setattr(a, "checked_path", spy)
    with pytest.raises(a.ArchiveError): a.pack(tmp_path, REQUEST, SNAPSHOT)
    assert not (tmp_path / a.PREFIX).exists()


def test_duplicate_case_alias_and_bad_provenance_rejected(tmp_path):
    _, request = case(tmp_path)
    duplicate = deepcopy(request["files"][0]); duplicate["path"] = duplicate["path"].replace("/synthetic/", "/Synthetic/")
    request["files"].append(duplicate)
    put(tmp_path, REQUEST, a.encoded(request))
    with pytest.raises(a.ArchiveError): a.pack(tmp_path, REQUEST, SNAPSHOT)
    request["files"].pop(); request["provenance"][0]["path"] = "results/sealed/root.json"
    put(tmp_path, REQUEST, a.encoded(request))
    with pytest.raises(a.ArchiveError): a.pack(tmp_path, REQUEST, SNAPSHOT)


@pytest.mark.parametrize("name", ["init_states_test", "INIT_STATE", "initial_state_values",
    "final_states", "test_states", "sealed_test", "test/initial", "TeSt/initial"])
@pytest.mark.parametrize("field,suffix", [("files", ".jsonl"), ("provenance", ".json")])
def test_state_stems_and_test_directory_rejected_before_filesystem(tmp_path, monkeypatch, name, field, suffix):
    _, request = case(tmp_path)
    forbidden = "results/formal_main_v2/" + name + suffix
    request[field][0]["path"] = forbidden
    put(tmp_path, REQUEST, a.encoded(request))
    original = a.checked_path
    visited = []
    def spy(root, relative, role):
        visited.append(relative)
        assert relative != forbidden, "Forbidden state input reached stat/open"
        return original(root, relative, role)
    monkeypatch.setattr(a, "checked_path", spy)
    with pytest.raises(a.ArchiveError, match="sealed-state"):
        a.pack(tmp_path, REQUEST, SNAPSHOT)
    assert visited and set(visited) == {REQUEST}
    assert not (tmp_path / a.PREFIX).exists()


@pytest.mark.parametrize("operation", ["request", "snapshot"])
def test_state_metadata_arguments_rejected_before_target_read(tmp_path, monkeypatch, operation):
    tmp_path.mkdir(exist_ok=True)
    forbidden = "results/formal_main_v2/init_states_test.json"
    def no_target_access(*args, **kwargs):
        raise AssertionError("Forbidden metadata reached filesystem validation")
    monkeypatch.setattr(a, "checked_path", no_target_access)
    with pytest.raises(a.ArchiveError, match="sealed-state"):
        if operation == "request": a.pack(tmp_path, forbidden, SNAPSHOT)
        else: a.verify(tmp_path, forbidden, "0" * 64)


def test_legal_final_trial_log_still_packs_and_restores(tmp_path):
    source = tmp_path / "source"
    name = "results/formal_main_v2/libero_10/downstream/final/attempt01/trials.jsonl"
    files, _, report = packed(source, {name: b'{"synthetic":true,"stage":"final"}\n'})
    clone = clone_package(source, tmp_path / "clone")
    assert a.restore(clone, SNAPSHOT, report["snapshot_sha256"])["status"] == "restored_verified"
    assert (clone / name).read_bytes() == files[name]


def test_existing_conflict_global_preflight_no_partial_restore(tmp_path):
    source = tmp_path / "source"
    files, _, report = packed(source, {"results/synthetic/a.jsonl": b"first", "results/synthetic/z.jsonl": b"second"})
    clone = clone_package(source, tmp_path / "clone")
    put(clone, "results/synthetic/z.jsonl", b"different existing bytes")
    with pytest.raises(a.ArchiveError): a.restore(clone, SNAPSHOT, report["snapshot_sha256"])
    assert not (clone / "results/synthetic/a.jsonl").exists()
    assert (clone / "results/synthetic/z.jsonl").read_bytes() == b"different existing bytes"
    assert list(clone.rglob("*.partial")) == []


def test_staging_failure_before_publication_preserves_all_original_paths(tmp_path, monkeypatch):
    source = tmp_path / "source"
    files, _, report = packed(source, {"results/synthetic/a.jsonl": b"first", "results/synthetic/z.jsonl": b"second"})
    clone = clone_package(source, tmp_path / "clone")
    real = a.verify_object
    def fail_on_second(*args, **kwargs):
        if kwargs.get("sink") is not None and args[2] == a.digest(b"second"):
            raise OSError("Synthetic staging I/O failure")
        return real(*args, **kwargs)
    monkeypatch.setattr(a, "verify_object", fail_on_second)
    with pytest.raises(OSError): a.restore(clone, SNAPSHOT, report["snapshot_sha256"])
    assert all(not (clone / name).exists() for name in files)
    assert list(clone.rglob("*.partial")) == []


def test_source_sha_mismatch_and_unknown_schema_fail_before_archive(tmp_path):
    _, request = case(tmp_path)
    request["files"][0]["sha256"] = "0" * 64
    put(tmp_path, REQUEST, a.encoded(request))
    with pytest.raises(a.ArchiveError): a.pack(tmp_path, REQUEST, SNAPSHOT)
    assert not (tmp_path / a.PREFIX).exists()
    request["extra"] = True
    put(tmp_path, REQUEST, a.encoded(request))
    with pytest.raises(a.ArchiveError): a.pack(tmp_path, REQUEST, SNAPSHOT)


def test_existing_snapshot_cannot_be_overwritten(tmp_path):
    files, _, report = packed(tmp_path)
    before = (tmp_path / SNAPSHOT).read_bytes()
    case(tmp_path, {"results/synthetic/new.jsonl": b"new"}, request_name="results/requests/new.json")
    with pytest.raises(a.ArchiveError): a.pack(tmp_path, "results/requests/new.json", SNAPSHOT)
    assert (tmp_path / SNAPSHOT).read_bytes() == before
    assert all((tmp_path / path).read_bytes() == data for path, data in files.items())


@pytest.mark.parametrize("where", ["input", "archive", "destination"])
def test_real_symlink_refused(tmp_path, where):
    source = tmp_path / "source"
    if where == "input":
        files, request = case(source)
        target = source / request["files"][0]["path"]
        outside = tmp_path / "outside.jsonl"; outside.write_bytes(target.read_bytes()); target.unlink()
        link, destination = target, outside
    else:
        _, _, report = packed(source)
        source = clone_package(source, tmp_path / "clone")
        if where == "archive":
            obj = json.loads((source / snapshot(source)["files"][0]["manifest"]["path"]).read_bytes())
            target = source / obj["chunks"][0]["path"]
            outside = tmp_path / "outside.gz"; outside.write_bytes(target.read_bytes()); target.unlink()
            link, destination = target, outside
        else:
            outside = tmp_path / "outside_dir"; outside.mkdir()
            link, destination = source / "results/synthetic", outside
    try:
        link.symlink_to(destination, target_is_directory=where == "destination")
    except OSError as error:
        pytest.skip("OS does not permit a real symlink: " + str(error))
    with pytest.raises(a.ArchiveError):
        if where == "input": a.pack(source, REQUEST, SNAPSHOT)
        else: a.restore(source, SNAPSHOT, report["snapshot_sha256"])
    assert link.is_symlink()


def test_windows_reparse_guard_without_following(tmp_path, monkeypatch):
    _, request = case(tmp_path)
    target = tmp_path / request["files"][0]["path"]
    real = Path.lstat
    class Reparse:
        st_mode = 0o100644
        st_file_attributes = 0x400
    def guarded(path, *args, **kwargs):
        return Reparse() if path == target else real(path, *args, **kwargs)
    monkeypatch.setattr(Path, "lstat", guarded)
    with pytest.raises(a.ArchiveError): a.pack(tmp_path, REQUEST, SNAPSHOT)


def test_lock_and_duplicate_json_key(tmp_path):
    case(tmp_path)
    with a.operation_lock(tmp_path):
        with pytest.raises(a.ArchiveError): a.pack(tmp_path, REQUEST, SNAPSHOT)
    put(tmp_path, REQUEST, b'{"schema":"a","schema":"b"}')
    with pytest.raises(a.ArchiveError): a.pack(tmp_path, REQUEST, SNAPSHOT)


def test_cli_fresh_process_pack_verify_restore_and_wrong_sha(tmp_path):
    source = tmp_path / "source"
    files, _ = case(source)
    base = [sys.executable, "-B", str(SCRIPT)]
    first = subprocess.run(base + ["pack", "--project-root", str(source), "--files-list", REQUEST, "--snapshot", SNAPSHOT],
                           capture_output=True, text=True, check=True)
    result = json.loads(first.stdout)
    clone = clone_package(source, tmp_path / "clone")
    for command in ("verify", "restore"):
        run = subprocess.run(base + [command, "--project-root", str(clone), "--snapshot", SNAPSHOT,
                             "--snapshot-sha256", result["snapshot_sha256"]], capture_output=True, text=True, check=True)
        assert json.loads(run.stdout)["status"].endswith("verified")
    bad = subprocess.run(base + ["verify", "--project-root", str(clone), "--snapshot", SNAPSHOT,
                         "--snapshot-sha256", "0" * 64], capture_output=True, text=True)
    assert bad.returncode == 2 and json.loads(bad.stderr)["status"] == "rejected"
    assert all((clone / name).read_bytes() == data for name, data in files.items())

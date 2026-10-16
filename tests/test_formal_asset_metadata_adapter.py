"""CPU-only strict-view checks. All copied sources and receipts stay in .local.

No real model files, data records or initial-state values are read. Only the
published173 source/config allowlist is copied into an explicitly synthetic tree.
"""
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
import uuid

import pytest


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = "scripts/ops/formal_asset_metadata_adapter.py"
REGISTRATION = "configs/experiments/formal_main_v2_asset_metadata_compat_v1.json"
INVENTORY = "results/formal_main_v2/source/formal_main_v2_run_564be0995e.json"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load(path):
    spec = importlib.util.spec_from_file_location("asset_compat_test_" + uuid.uuid4().hex, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module", autouse=True)
def original173_unchanged():
    expected = read(ROOT / INVENTORY)["files"]
    assert len(expected) == 173
    assert {p: digest(ROOT / p) for p in expected} == expected
    yield
    assert {p: digest(ROOT / p) for p in expected} == expected


@pytest.fixture(scope="module")
def synthetic(tmp_path_factory):
    project = tmp_path_factory.mktemp("synthetic_asset_compat")
    assert ROOT / ".local" in project.parents
    source = project / "snapshots/formal_main_v2_run_564be0995e"
    inventory = read(ROOT / INVENTORY)
    for name in inventory["files"]:
        destination = source / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
    files = [ADAPTER, REGISTRATION, "configs/assets/formal_main_v2_strict/libero_object.json",
             "configs/assets/formal_main_v2_strict/libero_goal.json"]
    for name in files:
        destination = project / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
    inventory["source_root_server"] = str(source)
    target = project / INVENTORY
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(inventory) + "\n", encoding="utf-8")
    module = load(project / ADAPTER)
    kwargs = dict(project_root=project, source_root=source, registration_path=project / REGISTRATION,
                  expected_adapter_sha256=digest(project / ADAPTER))
    return SimpleNamespace(project=project, source=source, module=module, kwargs=kwargs)


@contextmanager
def changed(path, content):
    before = path.read_bytes()
    try:
        path.write_bytes(content)
        yield
    finally:
        path.write_bytes(before)


def process(fixture, body):
    # The real integration starts a fresh Python process. Do the same here so
    # canonical imports cannot silently reuse the developer checkout's package.
    prelude = r'''
from pathlib import Path
from contextlib import contextmanager
import importlib.util, json, os, sys, hashlib
project, source = Path(sys.argv[1]), Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("synthetic_asset_adapter", project / "scripts/ops/formal_asset_metadata_adapter.py")
adapter = importlib.util.module_from_spec(spec); spec.loader.exec_module(adapter)
kwargs = dict(project_root=project, source_root=source,
    registration_path=project / adapter.REGISTRATION,
    expected_adapter_sha256=adapter.digest(project / adapter.ADAPTER))
events = []
journal = project / (sys.argv[3] + ".jsonl")
def emit(event, **fields):
    row = dict(event=event, synthetic=True, **fields)
    with journal.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(row, sort_keys=True) + "\n"); stream.flush(); os.fsync(stream.fileno())
    events.append(row)
@contextmanager
def raises(kind, contains=None):
    try: yield
    except kind as exc:
        if contains is not None: assert contains in str(exc), str(exc)
    else: raise AssertionError("expected " + kind.__name__)
'''
    result = subprocess.run([sys.executable, "-B", "-c", prelude + "\n" + body,
        str(fixture.project), str(fixture.source), "synthetic_events_" + uuid.uuid4().hex],
        capture_output=True, text=True, timeout=30, cwd=fixture.project)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def test_exact_views_and_identity_keep_all_original_inputs(synthetic):
    identity = synthetic.module.validate_asset_metadata_compat(**synthetic.kwargs)
    assert identity["verified_frozen_file_count"] == 173
    assert identity["original_manifest_identity_retained"] is True
    assert len(identity["watched_files"]) == 178
    assert set(identity["views"]) == {"libero_object", "libero_goal"}
    registration = read(synthetic.project / REGISTRATION)
    for suite, view in identity["views"].items():
        original = read(view["original_path"])
        derived = read(view["derived_path"])
        assert set(original) - set(derived) == set(synthetic.module.OMITTED)
        assert derived == {k: original[k] for k in synthetic.module.FIELDS}
        assert registration["views"][suite]["files_equal"] == original["files"] == derived["files"]
        assert view["file_count"] == 25
        assert sum("sha256" in x for x in derived["files"]) == 9
        assert sum("git_blob_sha1" in x for x in derived["files"]) == 16
    (synthetic.project / "synthetic_validation_identity.json").write_text(
        json.dumps(dict(synthetic=True, status="cpu_metadata_only_verified", identity=identity), indent=2) + "\n",
        encoding="utf-8", newline="\n")


def test_real_original_loader_strictness_and_restore(synthetic):
    process(synthetic, r'''
sys.path.insert(0, str(source / "src"))
from cti_vla.evaluation import checkpoint_manifest as cm
original, verifier = cm.load_checkpoint_manifest, cm.verify_checkpoint_directory
long = source / "configs/assets/openvla_oft_libero_long.json"
spatial = source / "configs/assets/openvla_oft_libero_spatial.json"
references = [original(p) for p in (long, spatial)]
for relative, _ in adapter.ORIGINALS.values():
    with raises(ValueError, "keys mismatch"): original(source / relative)
with adapter.install_asset_metadata_compat(**kwargs, emit=emit) as identity:
    for suite, row in identity["views"].items():
        # Mirrors the frozen runner's function-local import.
        from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest
        value = load_checkpoint_manifest(row["original_path"])
        assert value == original(row["derived_path"])
        assert value.revision == row["revision"] and len(value.files) == 25
    assert [cm.load_checkpoint_manifest(p) for p in (long, spatial)] == references
    assert cm.verify_checkpoint_directory is verifier
assert cm.load_checkpoint_manifest is original and cm.verify_checkpoint_directory is verifier
for relative, _ in adapter.ORIGINALS.values():
    with raises(ValueError, "keys mismatch"): cm.load_checkpoint_manifest(source / relative)
assert [e['event'] for e in events] == ['asset_metadata_compat_enter',
    'asset_metadata_compat_load_start','asset_metadata_compat_load_complete',
    'asset_metadata_compat_load_start','asset_metadata_compat_load_complete','asset_metadata_compat_exit']
assert events[-1]['adapted_calls_completed'] == events[-1]['adapted_calls_attempted'] == 2
assert events[-1]['passthrough_calls'] == 2
assert events[-1]['frozen_source_and_inputs_unchanged'] is True
assert events[-1]['original_loader_restored'] is True
''')


def test_unregistered_identical_copy_and_extra_metadata_are_not_adapted(synthetic):
    process(synthetic, r'''
unknown = project / "same_bytes_but_unregistered.json"
raw = source / adapter.ORIGINALS['libero_object'][0]
unknown.write_bytes(raw.read_bytes())
with adapter.install_asset_metadata_compat(**kwargs, emit=emit):
    from cti_vla.evaluation import checkpoint_manifest as cm
    with raises(ValueError, 'keys mismatch'): cm.load_checkpoint_manifest(unknown)
    malformed = project / "unknown_extra.json"
    value = json.loads((source / 'configs/assets/openvla_oft_libero_long.json').read_text())
    value['source'] = 'unregistered'
    malformed.write_text(json.dumps(value))
    with raises(ValueError, 'keys mismatch'): cm.load_checkpoint_manifest(malformed)
assert events[-1]['adapted_calls_attempted'] == 0
assert events[-1]['passthrough_calls'] == 2
''')


def test_directory_verifier_still_checks_synthetic_file_bytes(synthetic):
    process(synthetic, r'''
tiny = project / "synthetic_tiny_checkpoint"; tiny.mkdir(exist_ok=True)
data = b"CPU synthetic data, not a model"
(tiny / "sample.bin").write_bytes(data)
manifest = project / "synthetic_strict_manifest.json"
manifest.write_text(json.dumps(dict(schema_version=1, repository='synthetic/test', revision='a'*40,
    total_bytes=len(data), files=[dict(path='sample.bin',size=len(data),sha256=hashlib.sha256(data).hexdigest())])))
with adapter.install_asset_metadata_compat(**kwargs, emit=emit):
    from cti_vla.evaluation import checkpoint_manifest as cm
    value = cm.load_checkpoint_manifest(manifest)
    assert cm.verify_checkpoint_directory(tiny, value).file_count == 1
    (tiny / "sample.bin").write_bytes(b"X"*len(data))
    with raises(ValueError, 'hash mismatch'): cm.verify_checkpoint_directory(tiny, value)
assert events[-1]['adapted_calls_attempted'] == 0
''')


def test_runner_failure_restores_and_records_failure(synthetic):
    process(synthetic, r'''
with raises(RuntimeError, 'synthetic runner failure'):
    with adapter.install_asset_metadata_compat(**kwargs, emit=emit):
        from cti_vla.evaluation import checkpoint_manifest as cm
        cm.load_checkpoint_manifest(source / adapter.ORIGINALS['libero_goal'][0])
        raise RuntimeError('synthetic runner failure')
assert events[-1]['runner_raised'] is True
assert events[-1]['original_loader_restored'] is True
assert events[-1]['frozen_source_and_inputs_unchanged'] is True
with raises(ValueError, 'keys mismatch'):
    cm.load_checkpoint_manifest(source / adapter.ORIGINALS['libero_goal'][0])
''')


@pytest.mark.parametrize("symbol", ["load_checkpoint_manifest", "verify_checkpoint_directory"])
def test_rebinding_inside_scope_is_detected_and_original_restored(synthetic, symbol):
    process(synthetic, r'''
with raises(RuntimeError, 'binding changed'):
    with adapter.install_asset_metadata_compat(**kwargs, emit=emit):
        from cti_vla.evaluation import checkpoint_manifest as cm
        setattr(cm, SYMBOL, lambda *a, **k: None)
with raises(ValueError, 'keys mismatch'):
    cm.load_checkpoint_manifest(source / adapter.ORIGINALS['libero_object'][0])
assert events[-1]['original_loader_restored'] is True
assert events[-1]['binding_intact'] is (SYMBOL != 'load_checkpoint_manifest')
assert events[-1]['directory_verifier_unchanged'] is (SYMBOL != 'verify_checkpoint_directory')
'''.replace("SYMBOL", repr(symbol)))


def test_nested_installation_refuses_without_losing_outer_binding(synthetic):
    process(synthetic, r'''
with adapter.install_asset_metadata_compat(**kwargs, emit=emit):
    from cti_vla.evaluation import checkpoint_manifest as cm
    current = cm.load_checkpoint_manifest
    with raises(RuntimeError, 'already active'):
        with adapter.install_asset_metadata_compat(**kwargs, emit=emit): pass
    assert cm.load_checkpoint_manifest is current
    assert cm.load_checkpoint_manifest(source / adapter.ORIGINALS['libero_object'][0]).files
assert len([e for e in events if e['event']=='asset_metadata_compat_enter']) == 1
''')


@pytest.mark.parametrize("symbol", ["load_checkpoint_manifest", "verify_checkpoint_directory"])
def test_original_function_in_place_code_mutation_is_detected_and_restored(synthetic, symbol):
    process(synthetic, r'''
sys.path.insert(0, str(source / 'src'))
from cti_vla.evaluation import checkpoint_manifest as cm
original = getattr(cm, SYMBOL)
original_code = original.__code__
with raises(RuntimeError, 'binding changed'):
    with adapter.install_asset_metadata_compat(**kwargs, emit=emit):
        original.__code__ = (lambda *args, **kwargs: None).__code__
assert getattr(cm, SYMBOL) is original and original.__code__ is original_code
assert events[-1]['original_loader_code_unchanged'] is (SYMBOL != 'load_checkpoint_manifest')
assert events[-1]['directory_verifier_code_unchanged'] is (SYMBOL != 'verify_checkpoint_directory')
assert events[-1]['directory_verifier_unchanged'] is (SYMBOL != 'verify_checkpoint_directory')
with raises(ValueError, 'keys mismatch'):
    cm.load_checkpoint_manifest(source / adapter.ORIGINALS['libero_object'][0])
'''.replace("SYMBOL", repr(symbol)))


def test_function_reference_cannot_escape_explicit_scope(synthetic):
    process(synthetic, r'''
with adapter.install_asset_metadata_compat(**kwargs, emit=emit):
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest
    assert load_checkpoint_manifest(source / adapter.ORIGINALS['libero_goal'][0]).files
with raises(RuntimeError, 'installation scope'):
    load_checkpoint_manifest(source / adapter.ORIGINALS['libero_goal'][0])
from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest as restored
with raises(ValueError, 'keys mismatch'):
    restored(source / adapter.ORIGINALS['libero_goal'][0])
''')


def test_mandatory_emitter_and_callback_failure_do_not_leave_binding(synthetic):
    process(synthetic, r'''
with raises(ValueError, 'callback'):
    with adapter.install_asset_metadata_compat(**kwargs, emit=None): pass
def failed_emit(*args, **kw): raise RuntimeError('synthetic journal failure')
with raises(RuntimeError, 'journal failure'):
    with adapter.install_asset_metadata_compat(**kwargs, emit=failed_emit): pass
from cti_vla.evaluation import checkpoint_manifest as cm
with raises(ValueError, 'keys mismatch'):
    cm.load_checkpoint_manifest(source / adapter.ORIGINALS['libero_object'][0])
with adapter.install_asset_metadata_compat(**kwargs, emit=emit): pass
''')


def test_existing_package_from_wrong_source_is_rejected(synthetic):
    process(synthetic, "sys.path.insert(0, " + repr(str(ROOT / "src")) + r''')
from cti_vla.evaluation import checkpoint_manifest as cm
old = cm.load_checkpoint_manifest
with raises(ValueError, 'another source'):
    with adapter.install_asset_metadata_compat(**kwargs, emit=emit): pass
assert cm.load_checkpoint_manifest is old and not events
''')


def test_already_rebound_loader_is_rejected(synthetic):
    process(synthetic, r'''
sys.path.insert(0, str(source / 'src'))
from cti_vla.evaluation import checkpoint_manifest as cm
cm.load_checkpoint_manifest = lambda path: None
with raises(ValueError, 'already rebound'):
    with adapter.install_asset_metadata_compat(**kwargs, emit=emit): pass
assert not events
''')


@pytest.mark.parametrize("name", [
    "configs/assets/openvla_oft_libero_object.json",
    "configs/assets/openvla_oft_libero_goal.json",
    "src/cti_vla/evaluation/checkpoint_manifest.py",
    "configs/experiments/formal_main_v2.json",
])
def test_any_original_source_mutation_is_rejected(synthetic, name):
    path = synthetic.source / name
    with changed(path, path.read_bytes() + b"\n"):
        with pytest.raises(ValueError, match="Frozen source bytes changed"):
            synthetic.module.validate_asset_metadata_compat(**synthetic.kwargs)


@pytest.mark.parametrize("name,error", [
    (REGISTRATION, "registration SHA256"),
    ("configs/assets/formal_main_v2_strict/libero_object.json", "Original/derived"),
    ("configs/assets/formal_main_v2_strict/libero_goal.json", "Original/derived"),
])
def test_derived_or_compat_registration_byte_tamper_is_rejected(synthetic, name, error):
    path = synthetic.project / name
    with changed(path, path.read_bytes() + b"\n"):
        with pytest.raises(ValueError, match=error):
            synthetic.module.validate_asset_metadata_compat(**synthetic.kwargs)


def test_wrong_adapter_sha_or_registration_path_is_rejected(synthetic):
    with pytest.raises(ValueError, match="adapter path/SHA256"):
        synthetic.module.validate_asset_metadata_compat(**{**synthetic.kwargs, "expected_adapter_sha256": "0"*64})
    with pytest.raises(ValueError, match="registration paths"):
        synthetic.module.validate_asset_metadata_compat(**{**synthetic.kwargs, "registration_path": synthetic.project / "other.json"})


def test_in_scope_mutation_fails_before_use_and_restores(synthetic):
    process(synthetic, r'''
target = project / 'configs/assets/formal_main_v2_strict/libero_object.json'
before = target.read_bytes()
try:
    with raises(ValueError, 'input/source changed'):
        with adapter.install_asset_metadata_compat(**kwargs, emit=emit):
            from cti_vla.evaluation import checkpoint_manifest as cm
            target.write_bytes(before+b'\n')
            cm.load_checkpoint_manifest(source / adapter.ORIGINALS['libero_object'][0])
    assert events[-1]['original_loader_restored'] is True
    assert events[-1]['frozen_source_and_inputs_unchanged'] is False
    assert events[-1]['adapted_calls_attempted'] == 0
    with raises(ValueError, 'keys mismatch'):
        cm.load_checkpoint_manifest(source / adapter.ORIGINALS['libero_object'][0])
finally: target.write_bytes(before)
''')


def test_install_refuses_target_load_from_another_thread(synthetic):
    process(synthetic, r'''
import threading
errors=[]
with adapter.install_asset_metadata_compat(**kwargs, emit=emit):
    from cti_vla.evaluation import checkpoint_manifest as cm
    def other_thread():
        try: cm.load_checkpoint_manifest(source / adapter.ORIGINALS['libero_object'][0])
        except BaseException as exc: errors.append(exc)
    thread=threading.Thread(target=other_thread);thread.start();thread.join()
assert len(errors)==1 and isinstance(errors[0],RuntimeError)
assert 'installing thread' in str(errors[0])
assert events[-1]['adapted_calls_attempted']==0
''')

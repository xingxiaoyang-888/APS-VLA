"""Explicit, SHA-pinned metadata views for the two annotated formal assets.

The original manifest remains the declared input, including its original SHA.
Only its exact registered path may be parsed through a proven five-key view by
the unchanged frozen loader. Callers must separately register this adapter and
archive every emitted event. This module neither submits jobs nor loads weights.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import importlib
import importlib.util
import json
import marshal
from pathlib import Path
import sys
import threading
import uuid


VERSION = "formal-asset-metadata-compat-v1"
ADAPTER = "scripts/ops/formal_asset_metadata_adapter.py"
REGISTRATION = "configs/experiments/formal_main_v2_asset_metadata_compat_v1.json"
REGISTRATION_SHA256 = "25c90cbfe2db6fdb130a16e6b98ab7ccfc8373a2853578bf73ef0d38283cfb44"
FROZEN_NAME = "formal_main_v2_run_564be0995e"
SOURCE_INVENTORY = "results/formal_main_v2/source/" + FROZEN_NAME + ".json"
FROZEN_SHA256 = "dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e"
LOADER = "src/cti_vla/evaluation/checkpoint_manifest.py"
LOADER_MODULE = "cti_vla.evaluation.checkpoint_manifest"
LOADER_SHA256 = "6bad8f22b9b683de4785a3f05827f6383759a5689ca178efe71ea078211f368a"
FIELDS = ("schema_version", "repository", "revision", "total_bytes", "files")
OMITTED = ("source", "formal_experiment", "registered_utc")
ORIGINALS = {
    "libero_object": ("configs/assets/openvla_oft_libero_object.json",
        "3c3e3b614fa0bf4134825d95d22b69173d79bfb4a594f9c113c832156d0f6a24"),
    "libero_goal": ("configs/assets/openvla_oft_libero_goal.json",
        "6aaef6cd88a3968a13591fc196a3498c1780c7aab7a5e782a53c1967911a0ed5"),
}
_INSTALL_LOCK = threading.Lock()


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            result.update(block)
    return result.hexdigest()


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def code_sha(function):
    # Version2 is independent of temporary references/GC; compare in one runtime.
    return hashlib.sha256(marshal.dumps(function.__code__, 2)).hexdigest()


def _direct(value):
    path = Path(value).absolute()
    if path.resolve() != path:
        raise ValueError("Asset compatibility paths must be direct without aliases or traversal")
    return path


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


@contextmanager
def _reference_loader(source):
    """Load the pinned original file without changing the canonical module."""
    name = "formal_asset_reference_" + uuid.uuid4().hex
    spec = importlib.util.spec_from_file_location(name, source / LOADER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        # Compile the exact SHA-checked source bytes, not an optional .pyc.
        # The canonical import below must match this independent reference.
        exec(compile((source / LOADER).read_bytes(), str(source / LOADER), "exec"), module.__dict__)
        yield module
    finally:
        sys.modules.pop(name, None)


def _view(project, source, suite, row, loader):
    relative, expected = ORIGINALS[suite]
    derived_relative = "configs/assets/formal_main_v2_strict/" + suite + ".json"
    if (row.get("original_path") != relative or row.get("original_sha256") != expected
            or row.get("derived_path") != derived_relative):
        raise ValueError("Asset view may only name the two exact registered manifests")
    original, derived = _direct(source / relative), _direct(project / derived_relative)
    if digest(original) != expected or digest(derived) != row.get("derived_sha256"):
        raise ValueError("Original/derived asset SHA256 differs")
    raw, strict = _read(original), _read(derived)
    if not isinstance(raw, dict) or set(raw) != set(FIELDS + OMITTED):
        raise ValueError("Only the three registered metadata fields may be omitted")
    projected = {key: raw[key] for key in FIELDS}
    if (strict != projected or set(strict) != set(FIELDS)
            or row.get("omitted_metadata") != {key: raw[key] for key in OMITTED}
            or row.get("equal_header") != {key: raw[key] for key in FIELDS if key != "files"}
            or row.get("files_equal") != raw["files"]
            or row.get("file_count") != len(raw["files"])
            or row.get("file_specs_sha256") != signature(raw["files"])
            or row.get("projected_payload_sha256") != signature(projected)):
        raise ValueError("Asset view is not an exact header and per-file projection")
    # All structural checks, per-file digest rules and total-byte checks stay
    # in the original strict loader; directory verification is never rebound.
    manifest = loader(derived)
    return dict(suite=suite, original_path=str(original), original_sha256=expected,
        derived_path=str(derived), derived_sha256=row["derived_sha256"],
        file_count=len(manifest.files), total_bytes=manifest.total_bytes,
        repository=manifest.repository, revision=manifest.revision,
        file_specs_sha256=row["file_specs_sha256"],
        projected_payload_sha256=row["projected_payload_sha256"], omitted_metadata_fields=list(OMITTED))


def validate_asset_metadata_compat(*, project_root, source_root, registration_path,
                                   expected_adapter_sha256):
    """Read-only identity/projection verification; returns inputs to watch.

    ``source_root`` must be the original173-file snapshot under ``project_root``.
    The caller supplies a previously registered adapter SHA, never an unchecked
    value computed immediately before a production run. No weight paths open.
    """
    project, source = _direct(project_root), _direct(source_root)
    registration_path = _direct(registration_path)
    if source != project / "snapshots" / FROZEN_NAME or registration_path != project / REGISTRATION:
        raise ValueError("Use the exact frozen source and compatibility registration paths")
    adapter_path = _direct(__file__)
    if adapter_path != project / ADAPTER or digest(adapter_path) != expected_adapter_sha256:
        raise ValueError("Root-registered adapter path/SHA256 differs")
    if digest(registration_path) != REGISTRATION_SHA256:
        raise ValueError("Compatibility registration SHA256 differs")
    registration = _read(registration_path)
    inventory_path = _direct(project / SOURCE_INVENTORY)
    inventory = _read(inventory_path)
    files = inventory.get("files", {})
    if (inventory.get("schema") != "formal_main_v2" or len(files) != 173
            or hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest() != FROZEN_SHA256
            or inventory.get("source_sha256") != FROZEN_SHA256
            or inventory.get("source_root_server") != str(source)):
        raise ValueError("Frozen173-file inventory identity differs")
    for relative, expected in files.items():
        path = _direct(source / relative)
        if source not in path.parents or digest(path) != expected:
            raise ValueError("Frozen source bytes changed: " + relative)
    expected_registration = dict(schema="formal_main_v2", kind="asset_metadata_compatibility_registration",
        version=VERSION, frozen_source_inventory=SOURCE_INVENTORY, frozen_source_sha256=FROZEN_SHA256,
        frozen_file_count=173, original_registration="configs/experiments/formal_main_v2.json",
        adapter_path=ADAPTER, strict_fields=list(FIELDS), omitted_metadata_fields=list(OMITTED),
        scientific_settings_changed=False, weights_changed=False, original_manifest_identity_retained=True)
    if (any(registration.get(k) != v for k, v in expected_registration.items())
            or set(registration.get("views", {})) != set(ORIGINALS)
            or registration.get("original_registration_sha256") != files[registration["original_registration"]]
            or files.get(LOADER) != LOADER_SHA256):
        raise ValueError("Compatibility registration is outside its fixed metadata-only scope")
    registered = _read(source / registration["original_registration"])
    views = {}
    with _reference_loader(source) as reference:
        loader_code = code_sha(reference.load_checkpoint_manifest)
        verifier_code = code_sha(reference.verify_checkpoint_directory)
        for suite, row in registration["views"].items():
            original, checksum = ORIGINALS[suite]
            spec = registered["suites"][suite]
            if (spec["model_manifest"], spec["model_manifest_sha256"]) != (original, checksum):
                raise ValueError("Original suite registration/model identity changed")
            views[suite] = _view(project, source, suite, row, reference.load_checkpoint_manifest)
            if spec["model_revision"] != views[suite]["revision"]:
                raise ValueError("Projected model revision differs from original registration")
    watched = {str(adapter_path): expected_adapter_sha256, str(registration_path): REGISTRATION_SHA256,
        str(inventory_path): digest(inventory_path)}
    watched.update({str(source / name): checksum for name, checksum in files.items()})
    watched.update({view["derived_path"]: view["derived_sha256"] for view in views.values()})
    return dict(schema="formal_main_v2", kind="asset_metadata_compatibility", version=VERSION,
        project_root=str(project), source_root=str(source), source_inventory=str(inventory_path),
        source_inventory_sha256=watched[str(inventory_path)], frozen_source_sha256=FROZEN_SHA256,
        verified_frozen_file_count=173, adapter_path=str(adapter_path), adapter_sha256=expected_adapter_sha256,
        registration_path=str(registration_path), registration_sha256=REGISTRATION_SHA256,
        loader_path=str(source / LOADER), loader_sha256=LOADER_SHA256,
        original_loader_code_sha256=loader_code, directory_verifier_code_sha256=verifier_code,
        fingerprint_marshal_version=2, original_manifest_identity_retained=True,
        views=views, watched_files=watched)


def _canonical_loader(source):
    prefix = source / "src"
    for name in ("cti_vla", "cti_vla.evaluation", LOADER_MODULE):
        module = sys.modules.get(name)
        if module is not None and prefix not in _direct(module.__file__).parents:
            raise ValueError("Start a fresh process; a checkpoint-loader package belongs to another source")
    previous = list(sys.path)
    sys.path.insert(0, str(prefix))
    try:
        module = importlib.import_module(LOADER_MODULE)
    finally:
        sys.path[:] = previous
    if _direct(module.__file__) != source / LOADER:
        raise ValueError("Canonical checkpoint loader did not come from the frozen source")
    return module


def _unchanged(identity):
    for name, expected in identity["watched_files"].items():
        if digest(_direct(name)) != expected:
            raise ValueError("Asset compatibility input/source changed: " + name)


@contextmanager
def install_asset_metadata_compat(*, project_root, source_root, registration_path,
                                  expected_adapter_sha256, emit):
    """Temporarily install the exact two-path mapping, with mandatory events.

    ``emit(event, **fields)`` must durably record events in the enclosing job's
    journal. Install before the frozen runner imports its loader locally. Never
    run concurrently with another compatibility context in the same process.
    The original loader and directory verifier are restored/checked on exit,
    including runner failure. The yielded identity must enter the job receipt.
    """
    if not callable(emit):
        raise ValueError("A durable job event callback is required for explicit installation")
    if not _INSTALL_LOCK.acquire(blocking=False):
        raise RuntimeError("Asset compatibility installation is already active")
    try:
        identity = validate_asset_metadata_compat(project_root=project_root, source_root=source_root,
            registration_path=registration_path, expected_adapter_sha256=expected_adapter_sha256)
        module = _canonical_loader(Path(identity["source_root"]))
        original, verifier = module.load_checkpoint_manifest, module.verify_checkpoint_directory
        if (code_sha(original) != identity["original_loader_code_sha256"]
                or code_sha(verifier) != identity["directory_verifier_code_sha256"]):
            raise ValueError("Frozen checkpoint loader/verifier was already rebound")
        original_code, verifier_code = original.__code__, verifier.__code__
        owner, calls, completed, passthrough = threading.get_ident(), 0, 0, 0
        scope_active = False
        views = {Path(row["original_path"]): row for row in identity["views"].values()}

        def adapted(path):
            nonlocal calls, completed, passthrough
            if not scope_active:
                raise RuntimeError("Asset compatibility loader is no longer in its explicit installation scope")
            if original.__code__ is not original_code or verifier.__code__ is not verifier_code:
                raise RuntimeError("Original checkpoint loader/verifier code changed inside compatibility context")
            view = views.get(Path(path))
            if view is None:
                passthrough += 1
                return original(path)
            if threading.get_ident() != owner:
                raise RuntimeError("Registered metadata adaptation must run on the installing thread")
            _unchanged(identity)
            call_id = calls
            calls += 1
            emit("asset_metadata_compat_load_start", call_id=call_id, view=view)
            try:
                value = original(view["derived_path"])
                if original.__code__ is not original_code or verifier.__code__ is not verifier_code:
                    raise RuntimeError("Original checkpoint loader/verifier code changed inside compatibility context")
                _unchanged(identity)
            except BaseException as exc:
                emit("asset_metadata_compat_load_failed", call_id=call_id,
                    suite=view["suite"], error_type=type(exc).__name__, error=str(exc))
                raise
            completed += 1
            emit("asset_metadata_compat_load_complete", call_id=call_id, suite=view["suite"],
                file_count=len(value.files), total_bytes=value.total_bytes)
            return value

        adapted_code = adapted.__code__
        emit("asset_metadata_compat_enter", identity=identity, binding_code_sha256=code_sha(adapted))
        scope_active = True
        module.load_checkpoint_manifest = adapted
        failed = False
        try:
            yield identity
        except BaseException:
            failed = True
            raise
        finally:
            scope_active = False
            original_code_intact = original.__code__ is original_code
            verifier_code_intact = verifier.__code__ is verifier_code
            binding_intact = module.load_checkpoint_manifest is adapted and adapted.__code__ is adapted_code
            verifier_intact = module.verify_checkpoint_directory is verifier and verifier_code_intact
            original.__code__, verifier.__code__ = original_code, verifier_code
            module.load_checkpoint_manifest = original
            module.verify_checkpoint_directory = verifier
            unchanged = False
            try:
                _unchanged(identity)
                unchanged = True
            finally:
                emit("asset_metadata_compat_exit", original_loader_restored=module.load_checkpoint_manifest is original,
                    directory_verifier_unchanged=verifier_intact, binding_intact=binding_intact,
                    original_loader_code_unchanged=original_code_intact,
                    directory_verifier_code_unchanged=verifier_code_intact,
                    frozen_source_and_inputs_unchanged=unchanged, runner_raised=failed,
                    adapted_calls_attempted=calls, adapted_calls_completed=completed,
                    passthrough_calls=passthrough)
            if not binding_intact or not verifier_intact or not original_code_intact:
                raise RuntimeError("Frozen loader/verifier binding changed inside compatibility context")
    finally:
        _INSTALL_LOCK.release()

"""Scoped, registered Goal filename mapping; the frozen tensor loader is reused.

Only the two exact requests in the immutable official Goal directory may be
mapped. This never aliases files, changes weights or replaces torch.load.
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
import types


SCHEMA, VERSION = "formal_main_v2", "formal-goal-components-v1"
ADAPTER = "scripts/ops/formal_goal_component_adapter.py"
WRAPPER = "scripts/server/run_formal_goal_asset_stage.py"
SLURM = "scripts/server/formal_goal_asset_main.slurm"
REGISTRATION = "configs/experiments/formal_main_v2_goal_component_compat_v1.json"
SOURCE_NAME = "formal_main_v2_run_564be0995e"
SOURCE_SHA = "dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e"
SOURCE_INVENTORY = "results/formal_main_v2/source/" + SOURCE_NAME + ".json"
LOADER = "src/cti_vla/models/openvla_oft_loader.py"
LOADER_SHA = "e3782154cd7363364e2e8d7e88740e0ca6b4c8b423368360de5b2ff7607e5e22"
LOADER_MODULE = "cti_vla.models.openvla_oft_loader"
MODEL = "configs/assets/openvla_oft_libero_goal.json"
MODEL_SHA = "6aaef6cd88a3968a13591fc196a3498c1780c7aab7a5e782a53c1967911a0ed5"
MODEL_ROOT = "/share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-goal-c2d0f9f"
MODEL_REPOSITORY = "moojink/openvla-7b-oft-finetuned-libero-goal"
MODEL_REVISION = "c2d0f9fbbd82674683b397ff923168a12f6a307b"
MAPPINGS = [
    dict(requested="action_head--150000_checkpoint.pt", target="action_head--50000_checkpoint.pt", size=302242654,
        sha256="b97c2e8939ede32d8a1b29e9565d70f22040ba9e54925665e81989a0cc13ccff"),
    dict(requested="proprio_projector--150000_checkpoint.pt", target="proprio_projector--50000_checkpoint.pt", size=67275184,
        sha256="780595e9cca5292348697686f9ccc83d39d9d3d303e860d62c6d4609952dfff1"),
]
SYMBOLS = ("_load_component_state", "remove_uniform_ddp_prefix", "load_openvla_oft_components")
_LOCK = threading.Lock()


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            value.update(block)
    return value.hexdigest()


def direct(value):
    path = Path(value).absolute()
    if path.resolve() != path:
        raise ValueError("Component paths must be direct, without aliases/traversal")
    return path


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def code_sha(function):
    return hashlib.sha256(marshal.dumps(function.__code__, 2)).hexdigest()


def registration_payload():
    return dict(schema=SCHEMA, kind="goal_component_filename_compatibility_registration", version=VERSION,
        suite="libero_goal", source_inventory=SOURCE_INVENTORY, source_sha256=SOURCE_SHA,
        loader=LOADER, loader_sha256=LOADER_SHA, target_symbol=SYMBOLS[0], model_manifest=MODEL,
        model_manifest_sha256=MODEL_SHA, model_repository=MODEL_REPOSITORY, model_revision=MODEL_REVISION,
        checkpoint_root=MODEL_ROOT, mappings=MAPPINGS, other_component_requests="reject",
        original_component_loader_used=True, torch_load_replaced=False, official_directory_modified=False,
        scientific_settings_changed=False, weights_changed=False,
        acceptance_required="original_real_F00_F01_F03_and_root_review")


def _reference_codes(path):
    name = "_formal_goal_component_frozen_reference"
    if name in sys.modules:
        raise RuntimeError("Frozen reference namespace is already in use")
    reference = types.ModuleType(name)
    reference.__file__ = str(path)
    sys.modules[name] = reference
    try:
        exec(compile(path.read_bytes(), str(path), "exec"), reference.__dict__)
        return {name: code_sha(getattr(reference, name)) for name in SYMBOLS}
    finally:
        del sys.modules[name]


def _canonical_loader(source):
    prefix = source / "src"
    for name in ("cti_vla", "cti_vla.models", LOADER_MODULE):
        module = sys.modules.get(name)
        if module is not None and prefix not in direct(module.__file__).parents:
            raise ValueError("Component loader requires a fresh process on the frozen PYTHONPATH")
    old = list(sys.path)
    sys.path.insert(0, str(prefix))
    try:
        module = importlib.import_module(LOADER_MODULE)
    finally:
        sys.path[:] = old
    if direct(module.__file__) != source / LOADER:
        raise ValueError("Component loader is not the frozen canonical module")
    return module


def validate_goal_component_compat(*, project_root, source_root, contract):
    """Metadata-only identity validation; target tensors are checked at install/load."""
    project, source = direct(project_root), direct(source_root)
    expected = dict(schema=SCHEMA, kind="goal_component_filename_compatibility", version=VERSION,
        suite="libero_goal", wrapper=WRAPPER, adapter=ADAPTER, slurm=SLURM, registration=REGISTRATION)
    if (source != project / "snapshots" / SOURCE_NAME or not isinstance(contract, dict)
            or set(contract) != {*expected, "files"} or any(contract.get(k) != v for k, v in expected.items())
            or set(contract.get("files", {})) != {WRAPPER, ADAPTER, SLURM, REGISTRATION}
            or direct(__file__) != project / ADAPTER):
        raise ValueError("Goal component runtime contract differs")
    watched = {}
    for relative, checksum in contract["files"].items():
        path = direct(project / relative)
        if digest(path) != checksum:
            raise ValueError("Registered component support bytes differ: " + relative)
        watched[str(path)] = checksum
    if read(project / REGISTRATION) != registration_payload():
        raise ValueError("Goal component registration is not the exact two-file mapping")
    inventory_path = project / SOURCE_INVENTORY
    inventory = read(inventory_path)
    files = inventory.get("files", {})
    if (inventory.get("schema") != SCHEMA or len(files) != 173 or inventory.get("source_sha256") != SOURCE_SHA
            or inventory.get("source_root_server") != str(source)
            or hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest() != SOURCE_SHA):
        raise ValueError("Component compatibility requires the original173 source identity")
    watched[str(inventory_path)] = digest(inventory_path)
    for relative, checksum in files.items():
        path = direct(source / relative)
        if source not in path.parents or digest(path) != checksum:
            raise ValueError("Frozen source changed: " + relative)
        watched[str(path)] = checksum
    manifest = read(source / MODEL)
    formal = read(source / "configs/experiments/formal_main_v2.json")["suites"]["libero_goal"]
    if (files.get(LOADER) != LOADER_SHA or files.get(MODEL) != MODEL_SHA
            or (formal["model_manifest"], formal["model_manifest_sha256"], formal["model_root_server"], formal["model_revision"])
            != (MODEL, MODEL_SHA, MODEL_ROOT, MODEL_REVISION)
            or manifest["repository"] != MODEL_REPOSITORY or manifest["revision"] != MODEL_REVISION):
        raise ValueError("Original Goal model/loader identity changed")
    manifest_files = {r["path"]: r for r in manifest["files"]}
    for row in MAPPINGS:
        if (row["requested"] in manifest_files or manifest_files.get(row["target"]) !=
                dict(path=row["target"], size=row["size"], sha256=row["sha256"])):
            raise ValueError("Mapped component is not the exact official file specification")
    return dict(schema=SCHEMA, kind="goal_component_identity", version=VERSION, suite="libero_goal",
        project_root=str(project), source_root=str(source), source_sha256=SOURCE_SHA,
        source_inventory=str(inventory_path), source_inventory_sha256=digest(inventory_path),
        verified_frozen_file_count=173, component_compatibility=contract, loader_path=str(source / LOADER),
        loader_sha256=LOADER_SHA, original_function_code_sha256=_reference_codes(source / LOADER),
        fingerprint_marshal_version=2, model_manifest=str(source / MODEL), model_manifest_sha256=MODEL_SHA,
        checkpoint_root=MODEL_ROOT, mappings=[dict(row, requested_path=MODEL_ROOT + "/" + row["requested"],
            target_path=MODEL_ROOT + "/" + row["target"]) for row in MAPPINGS],
        other_component_requests="reject", original_component_loader_used=True, torch_load_replaced=False,
        scientific_settings_changed=False, weights_changed=False, watched_files=watched)


def _unchanged(identity):
    for path, checksum in identity["watched_files"].items():
        if digest(direct(path)) != checksum:
            raise ValueError("Goal component source/input changed: " + path)


def _verify_target(row):
    """Check bytes before and after each actual original-loader invocation."""
    target, requested = direct(row["target_path"]), direct(row["requested_path"])
    if requested.exists() or requested.is_symlink():
        raise ValueError("A requested150000 alias/file must not be created")
    if target.parent != requested.parent or not target.is_file() or target.is_symlink():
        raise ValueError("Official component target is missing or escaped its directory")
    before = target.stat()
    if before.st_size != row["size"] or digest(target) != row["sha256"]:
        raise ValueError("Official component target size/SHA256 differs")
    after = target.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError("Official component target changed while hashing")
    return target


@contextmanager
def _scoped_component_loader(module, identity, emit):
    originals = {name: getattr(module, name) for name in SYMBOLS}
    if any(code_sha(fn) != identity["original_function_code_sha256"][name] for name, fn in originals.items()):
        raise ValueError("Frozen component loader/helper was already changed")
    codes = {name: fn.__code__ for name, fn in originals.items()}
    torch_module, torch_load = module.torch, module.torch.load
    torch_code = getattr(torch_load, "__code__", None)
    owner, attempted, completed, rejected = threading.get_ident(), 0, 0, 0
    active, raised = False, False
    mappings = identity["mappings"]
    for row in mappings:
        _verify_target(row)

    def intact():
        return (all(fn.__code__ is codes[name] for name, fn in originals.items())
            and all(getattr(module, name) is originals[name] for name in SYMBOLS[1:])
            and module.torch is torch_module and torch_module.load is torch_load
            and getattr(torch_load, "__code__", None) is torch_code)

    def adapted(path):
        nonlocal attempted, completed, rejected
        if not active or threading.get_ident() != owner or not intact():
            raise RuntimeError("Component binding is outside its owner scope or its original loader changed")
        # Normalize separators only: do not resolve traversal or aliases into
        # an allowed request. The fixed metadata uses POSIX server paths.
        requested = Path(path).as_posix()
        if attempted >= len(mappings) or requested != Path(mappings[attempted]["requested_path"]).as_posix():
            rejected += 1
            emit("goal_component_request_rejected", requested_path=requested, next_call_id=attempted)
            raise ValueError("Only the exact two Goal component requests, once in registered order, are allowed")
        row, call_id = mappings[attempted], attempted
        attempted += 1
        emit("goal_component_load_start", call_id=call_id, mapping=row)
        try:
            _unchanged(identity)
            target = _verify_target(row)
            value = originals[SYMBOLS[0]](target)
            _verify_target(row)
            _unchanged(identity)
            if not intact():
                raise RuntimeError("Original component loader/helper changed while loading")
        except BaseException as error:
            emit("goal_component_load_failed", call_id=call_id, error_type=type(error).__name__, error=str(error))
            raise
        completed += 1
        emit("goal_component_load_complete", call_id=call_id, mapping=row, state_tensor_count=len(value),
            state_keys_sha256=hashlib.sha256(json.dumps(sorted(value), separators=(",", ":")).encode()).hexdigest())
        return value

    adapted_code = adapted.__code__
    emit("goal_component_compat_enter", identity=identity, binding_code_sha256=code_sha(adapted))
    active = True
    module._load_component_state = adapted
    try:
        yield identity
    except BaseException:
        raised = True
        raise
    finally:
        active = False
        original_intact = intact()
        binding_intact = module._load_component_state is adapted and adapted.__code__ is adapted_code
        for name, fn in originals.items():
            fn.__code__ = codes[name]
            setattr(module, name, fn)
        if torch_code is not None:
            torch_load.__code__ = torch_code
        module.torch = torch_module
        torch_module.load = torch_load
        inputs_unchanged, targets_unchanged = False, False
        try:
            _unchanged(identity)
            inputs_unchanged = True
            for row in mappings:
                _verify_target(row)
            targets_unchanged = True
        finally:
            emit("goal_component_compat_exit", original_loader_restored=module._load_component_state is originals[SYMBOLS[0]],
                original_function_codes_unchanged=original_intact, binding_intact=binding_intact,
                torch_load_unchanged=original_intact, source_inputs_unchanged=inputs_unchanged,
                component_files_unchanged=targets_unchanged, runner_raised=raised,
                component_calls_attempted=attempted, component_calls_completed=completed, rejected_calls=rejected)
        if not original_intact or not binding_intact:
            raise RuntimeError("Component function binding changed inside its registered scope")


@contextmanager
def install_goal_component_compat(*, project_root, source_root, contract, emit):
    if not callable(emit) or not _LOCK.acquire(blocking=False):
        raise RuntimeError("Goal component installation requires one exclusive durable event owner")
    try:
        identity = validate_goal_component_compat(project_root=project_root, source_root=source_root, contract=contract)
        module = _canonical_loader(Path(identity["source_root"]))
        with _scoped_component_loader(module, identity, emit) as installed:
            yield installed
    finally:
        _LOCK.release()

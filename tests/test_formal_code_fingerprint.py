"""CPU-only regression for the adapter's reference-independent code identity.

Only source modules and synthetic functions are loaded. No evaluator, model,
simulator, checkpoint, final-state reader, Git command or remote process runs.
"""
from contextlib import nullcontext
import gc
import hashlib
import importlib.util
import json
import marshal
from pathlib import Path
import platform
from types import CodeType
import uuid

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/ops/formal_evaluation_adapter.py"
FIELDS = ("co_consts", "co_names", "co_varnames")
SAMPLE = """def subject(value):
    offset = 37
    record = {"label": "fingerprint payload", "nested": ("alpha", None, 3.25)}
    def inner(number):
        return len(str(number)) + offset
    return inner(value) + len(record)
"""
MUTATION_SAMPLE = """def subject(value):
    def inner(number):
        return number + 17
    return inner(value) * 3
"""


def load_adapter():
    spec = importlib.util.spec_from_file_location(
        "formal_fingerprint_" + uuid.uuid4().hex, SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_function(source=SAMPLE):
    namespace = {}
    exec(compile(source, "<formal-code-fingerprint-synthetic>", "exec"), namespace)
    return namespace["subject"]


def code_tree(code):
    yield code
    for value in code.co_consts:
        if isinstance(value, CodeType):
            yield from code_tree(value)


def hold_metadata(functions):
    return [getattr(code, field)
            for function in functions for code in code_tree(function.__code__)
            for field in FIELDS]


def explicit_sha(code, version):
    return hashlib.sha256(marshal.dumps(code, version)).hexdigest()


@pytest.fixture
def adapter():
    return load_adapter()


def test_declared_format_is_explicit_marshal_two(adapter):
    function = synthetic_function()
    assert adapter.CODE_MARSHAL_VERSION == 2
    assert adapter.VERSION == "formal-evaluation-explicit-archive-resume-adapter-v2-marshal2"
    assert adapter.code_sha(function) == explicit_sha(function.__code__, 2)


@pytest.mark.parametrize("field", FIELDS)
def test_external_metadata_references_and_gc_leave_identity_unchanged(adapter, field):
    function = synthetic_function()
    code = function.__code__
    before = adapter.code_sha(function)
    for count in (1, 7, 64):
        references = [getattr(code, field)] * count
        assert references[0] is getattr(code, field)
        gc.collect()
        assert function.__code__ is code
        assert adapter.code_sha(function) == before
        references.clear()
        gc.collect()
        assert adapter.code_sha(function) == before


def test_nested_code_metadata_and_collected_cycles_leave_identity_unchanged(adapter):
    function = synthetic_function()
    before = adapter.code_sha(function)
    assert len(list(code_tree(function.__code__))) > 1
    for _ in range(3):
        references = hold_metadata([function])
        cycle = [references]
        cycle.append(cycle)
        gc.collect()
        assert adapter.code_sha(function) == before
        del references, cycle
        gc.collect()
        assert adapter.code_sha(function) == before


def test_repeated_private_imports_are_stable_under_live_references_and_gc(adapter):
    def fingerprints(module):
        return {
            "code_sha": module.code_sha(module.code_sha),
            "recorded_bindings": module.code_sha(module.recorded_bindings.__wrapped__),
            "verify_snapshot": module.code_sha(module.verify_snapshot),
        }
    before = fingerprints(adapter)
    references = hold_metadata([
        adapter.code_sha, adapter.recorded_bindings.__wrapped__, adapter.verify_snapshot])
    for _ in range(4):
        module = load_adapter()
        assert module is not adapter
        assert module.code_sha.__code__ is not adapter.code_sha.__code__
        gc.collect()
        assert fingerprints(module) == before
        assert fingerprints(adapter) == before
        del module
    references.clear()
    gc.collect()
    assert fingerprints(adapter) == before


@pytest.mark.parametrize("mutation", ["replace_code", "constant", "nested_code"])
def test_code_or_constant_changes_are_still_detected(adapter, mutation):
    function = synthetic_function(MUTATION_SAMPLE)
    original = function.__code__
    before = adapter.code_sha(function)
    expected = function(5)
    if mutation == "replace_code":
        replacement = synthetic_function("def subject(value):\n    return value - 91\n")
        function.__code__ = replacement.__code__
    elif mutation == "constant":
        function.__code__ = original.replace(co_consts=tuple(
            5 if type(value) is int and value == 3 else value
            for value in original.co_consts))
        assert function.__code__.co_code == original.co_code
    else:
        inner = next(value for value in original.co_consts if isinstance(value, CodeType))
        changed = inner.replace(co_consts=tuple(
            29 if type(value) is int and value == 17 else value
            for value in inner.co_consts))
        function.__code__ = original.replace(co_consts=tuple(
            changed if value is inner else value for value in original.co_consts))
        assert function.__code__.co_code == original.co_code
    assert function(5) != expected
    assert adapter.code_sha(function) != before
    function.__code__ = original
    assert adapter.code_sha(function) == before


def test_retains_minimal_legacy_reference_diagnostic_without_platform_failure_gate(
        adapter, tmp_path, record_property):
    """Default/v4 instability is evidence, not a mandatory interpreter behavior."""
    function = synthetic_function()
    code = function.__code__
    def fingerprints():
        return {
            "default_sha256": hashlib.sha256(marshal.dumps(code)).hexdigest(),
            "explicit_v4_sha256": explicit_sha(code, 4),
            "explicit_v2_sha256": adapter.code_sha(function),
        }
    before = fingerprints()
    references = hold_metadata([function])
    gc.collect()
    held = fingerprints()
    assert function.__code__ is code
    references.clear()
    gc.collect()
    released = fingerprints()
    evidence = {
        "kind": "synthetic_legacy_code_fingerprint_reference_diagnostic",
        "python": platform.python_version(), "implementation": platform.python_implementation(),
        "default_marshal_version": marshal.version,
        "adapter_file_sha256": hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
        "synthetic_source_sha256": hashlib.sha256(SAMPLE.encode()).hexdigest(),
        "same_code_object": function.__code__ is code,
        "before": before, "held_references": held, "released_references": released,
        "default_changed_with_references": before["default_sha256"] != held["default_sha256"],
        "explicit_v4_changed_with_references": before["explicit_v4_sha256"] != held["explicit_v4_sha256"],
        "legacy_change_is_not_required_on_every_python": True,
    }
    path = tmp_path / "legacy_marshal_reference_diagnostic.json"
    path.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    record_property("legacy_marshal_reference_diagnostic", str(path))
    assert before["explicit_v2_sha256"] == held["explicit_v2_sha256"] == released["explicit_v2_sha256"]


def actual_bindings(adapter):
    # Importing these source modules does not execute any rollout or Git check.
    from cti_vla.evaluation import future_profiling
    evaluate = adapter.private_module(ROOT, "eval_formal_selector_libero")
    legacy = adapter.private_module(ROOT, "eval_libero")
    return evaluate, legacy, future_profiling


class SyntheticBodyFailure(Exception):
    pass


@pytest.mark.parametrize("raise_body", [False, True])
def test_actual_binding_objects_restore_with_strict_before_after_sha_equality(
        adapter, raise_body):
    evaluate, legacy, helpers = actual_bindings(adapter)
    original_verify, original_loader, original_execute = (
        evaluate.verify_checkout, helpers.load_script, evaluate.execute)
    originals = [original_verify, original_loader, original_execute, legacy.verify_source_checkout]
    before = [adapter.code_sha(function) for function in originals]
    events = []
    def emit(event, **values):
        events.append(json.loads(json.dumps(dict(event=event, **values))))
    scope = pytest.raises(SyntheticBodyFailure) if raise_body else nullcontext()
    with scope:
        with adapter.recorded_bindings(evaluate, legacy, helpers, ROOT, emit) as bindings:
            assert evaluate.verify_checkout is not original_verify
            assert helpers.load_script is not original_loader
            assert evaluate.execute is original_execute
            assert helpers.load_script(ROOT, "eval_formal_selector_libero") is evaluate
            other = helpers.load_script(ROOT, "eval_libero")
            assert other is not evaluate
            assert adapter.code_sha(other.verify_source_checkout) == before[3]
            assert bindings[0]["original_code_sha256"] == before[0]
            assert bindings[1]["original_code_sha256"] == before[1]
            assert bindings[0]["adapter_binding_code_sha256"] == adapter.code_sha(evaluate.verify_checkout)
            assert bindings[1]["adapter_binding_code_sha256"] == adapter.code_sha(helpers.load_script)
            references = hold_metadata(originals + [evaluate.verify_checkout, helpers.load_script])
            gc.collect()
            if raise_body:
                raise SyntheticBodyFailure("synthetic interrupted evaluation body")
    assert evaluate.verify_checkout is original_verify
    assert helpers.load_script is original_loader
    assert evaluate.execute is original_execute
    assert [adapter.code_sha(function) for function in originals] == before
    enter = next(row for row in events if row["event"] == "bindings_enter")
    restored = events[-1]
    assert restored["event"] == "bindings_restored"
    # This is the existing root reader's unchanged strict restoration contract.
    assert restored["original_verify_code_sha256"] == enter["bindings"][0]["original_code_sha256"]
    assert restored["original_loader_code_sha256"] == enter["bindings"][1]["original_code_sha256"]
    assert enter["frozen_execute_code_sha256"] == before[2]
    references.clear()
    gc.collect()
    assert [adapter.code_sha(function) for function in originals] == before


def test_replacing_execute_still_triggers_existing_object_identity_guard(adapter):
    evaluate, legacy, helpers = actual_bindings(adapter)
    original_verify, original_loader, original_execute = (
        evaluate.verify_checkout, helpers.load_script, evaluate.execute)
    replacement = synthetic_function()
    try:
        with pytest.raises(RuntimeError, match="Frozen execute was replaced"):
            with adapter.recorded_bindings(evaluate, legacy, helpers, ROOT, lambda *a, **kw: None):
                evaluate.execute = replacement
        assert evaluate.verify_checkout is original_verify
        assert helpers.load_script is original_loader
    finally:
        evaluate.execute = original_execute


def test_mutating_original_code_cannot_pass_strict_restoration_sha_contract(adapter):
    evaluate, legacy, helpers = actual_bindings(adapter)
    original = evaluate.verify_checkout
    original_code, original_loader = original.__code__, helpers.load_script
    events = []
    def emit(event, **values):
        events.append(dict(event=event, **values))
    try:
        with adapter.recorded_bindings(evaluate, legacy, helpers, ROOT, emit):
            original.__code__ = synthetic_function().__code__
        assert evaluate.verify_checkout is original
        assert helpers.load_script is original_loader
        enter, restored = events[0], events[-1]
        assert restored["event"] == "bindings_restored"
        assert restored["original_verify_code_sha256"] != enter["bindings"][0]["original_code_sha256"]
        assert restored["original_loader_code_sha256"] == enter["bindings"][1]["original_code_sha256"]
    finally:
        original.__code__ = original_code

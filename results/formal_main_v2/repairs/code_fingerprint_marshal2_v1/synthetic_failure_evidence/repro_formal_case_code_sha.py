"""Local read-only diagnostic. No production edits, state, weights or network."""
import gc
import hashlib
import importlib.util
import json
import marshal
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
mode = sys.argv[1]
target = ROOT / "scripts/eval_formal_selector_libero.py"

def load(name):
    spec = importlib.util.spec_from_file_location(name, target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

old = load("case_diagnostic_old") if mode != "fresh" else None
current = load("case_diagnostic_current")
fn = current.verify_checkout
code = fn.__code__
if mode == "duplicate_drop":
    old = None

def hashes():
    return {str(version): hashlib.sha256(marshal.dumps(code, version)).hexdigest()
        for version in (marshal.version, 2)}

before_semantics = (code.co_code, code.co_consts, code.co_names, code.co_varnames, code.co_filename, code.co_firstlineno)
before = hashes()
collected = gc.collect()
after = hashes()
row = dict(python=sys.version, mode=mode, target=str(target), marshal_default_version=marshal.version,
    same_function=fn is current.verify_checkout, same_code_object=code is current.verify_checkout.__code__,
    semantic_attributes_unchanged=before_semantics == (code.co_code, code.co_consts, code.co_names,
        code.co_varnames, code.co_filename, code.co_firstlineno), before=before, after=after, gc_collected=collected,
    source_sha256=hashlib.sha256(target.read_bytes()).hexdigest(), source_modified=False)
try:
    assert before[str(marshal.version)] == after[str(marshal.version)], "Default marshal SHA changed although the exact code object was retained"
except AssertionError:
    row["diagnostic_assertion_traceback"] = traceback.format_exc()
path = ROOT / ".local" / ("formal_case_code_sha_gc_only_" + mode + ".json")
with path.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(row, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps(row, ensure_ascii=False))

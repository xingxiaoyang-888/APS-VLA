"""Exact-version G5 consumer. No release, scheduler access, or mutable state.

Old genuine reviews are delegated intact to the fixed old whole-chain consumer.
New reviews are rebuilt from their actual invocation and immutable job snapshot.
"""
from __future__ import annotations
import sys
import contextvars
import types
from pathlib import Path

VERSION = "formal-downstream-action-v1"
OLD_VERSION = "formal-downstream-root-v1"
_ACTIVE = contextvars.ContextVar("formal_action_review_stack", default=())


def _reviewer(evidence):
    path = evidence.project / "scripts/ops/formal_action_deployment_v1/reviewer.py"
    if path.is_symlink() or path.resolve() != path:
        raise ValueError("Noncanonical reviewer")
    checksum = evidence.watch(path)
    name = "_g5_explicit_reviewer_" + checksum
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name); module.__file__ = str(path); module.__package__ = ""
        sys.modules[name] = module
        try:
            exec(compile(path.read_bytes(), str(path), "exec", dont_inherit=True), module.__dict__)
        except BaseException:
            sys.modules.pop(name, None); raise
    return module


def review_downstream_output(evidence, reference, *, expected_stage, suite, run_root=None, require_complete=True):
    # Stage rejection precedes any reference or filesystem access, even for v1.
    if expected_stage not in ("development", "collect", "full", "components"):
        raise ValueError("Final/unknown stage cannot be consumed by action-v1")
    mod = _reviewer(evidence)
    mod.ref(reference)
    mod.require(reference["path"].startswith("results/formal_main_v2/downstream_reviews/"),
                "Immutable downstream root review required")
    mod.require(evidence.watch(reference["path"]) == reference["sha256"], "Root review SHA changed")
    saved = evidence.read(reference["path"])
    mod.require(saved.get("stage") == expected_stage and saved.get("schema") == "formal_main_v2"
        and saved.get("kind") == "root_downstream_review" and saved.get("status") == "passed"
        and saved.get("reviewed_by") == "root", "Not a matching root review")
    output = mod.remote_relative(saved.get("run_root", "/invalid"))
    mod.require(run_root is None or mod.remote_relative(run_root) == output, "Output identity differs")
    mod.require(saved.get("source_provenance", {}).get("suite") == suite, "Root suite differs")
    version = saved.get("execution_version", OLD_VERSION)
    if version == OLD_VERSION:
        mod.require(require_complete, "Legacy partial continuation belongs to the original explicit prefix gate")
        original = mod.load(evidence, mod.OLD_HELPER, mod.PINNED[mod.OLD_HELPER])
        # Original consumer and its entire original reviewer/scheduler are used
        # unchanged. No new inv/report is projected into that old execution.
        return original.review_downstream_output(evidence, reference, expected_stage=expected_stage,
                                                 suite=suite, run_root=run_root)
    mod.require(version == VERSION and saved.get("version") == mod.REVIEW_VERSION, "Unknown review version")
    mod.require(type(require_complete) is bool and type(saved.get("scientific_complete")) is bool, "Explicit completion scope required")
    if require_complete:
        mod.require(saved["scientific_complete"], "Partial result cannot release a complete scientific stage")
    snapshot = saved.get("registered_jobs_at_review")
    mod.require(isinstance(snapshot, list) and snapshot, "Missing immutable terminal job snapshot")
    matches = [j for j in snapshot if j.get("job_id") == saved.get("job_id")]
    mod.require(len(matches) == 1 and matches[0].get("suite") == suite, "Actual registered job missing")
    contract_ref = saved["action_execution_contract"]
    contract = evidence.read(contract_ref["path"])
    mod.require(evidence.watch(contract_ref["path"]) == contract_ref["sha256"]
        and contract["files"].get(mod.REVIEWER) == evidence.watch(mod.REVIEWER)
        and contract["files"].get(mod.CONSUMER) == evidence.watch(mod.CONSUMER)
        and Path(__file__).resolve() == evidence.path(mod.CONSUMER), "Exact new consumer/reviewer source required")
    # A report cannot recursively name itself or another report already active.
    stack = _ACTIVE.get()
    mod.require(reference["path"] not in stack, "Cyclic root review references")
    token = _ACTIVE.set(stack + (reference["path"],))
    try:
        rebuilt = mod.review(evidence.project, job=matches[0], invocation_ref=saved["invocation_ref"],
            pull_ref=saved["pull_ref"], registered_jobs=snapshot, expected_contract_ref=contract_ref)
    finally:
        _ACTIVE.reset(token)
    mod.require({k: v for k, v in saved.items() if k != "reviewed_utc"} ==
                {k: v for k, v in rebuilt.items() if k != "reviewed_utc"}, "New root review does not exactly rebuild")
    for field in ("files", "evidence_sha256", "audit_source_sha256"):
        mapping = rebuilt.get(field)
        mod.require(isinstance(mapping, dict) and mapping, "Missing reconstructed evidence map")
        mod._merge(evidence, mapping)
    evidence.unchanged()
    return rebuilt


def require_matching_o2a(evidence, development_refs, full_ref, components_ref, *, suite):
    """Only consume full artifacts; never extrapolate speed or fabricate release."""
    mod = _reviewer(evidence)
    mod.require(isinstance(development_refs, list) and development_refs, "Completed development proofs required")
    development = [review_downstream_output(evidence, item, expected_stage="development", suite=suite)
                   for item in development_refs]
    full = review_downstream_output(evidence, full_ref, expected_stage="full", suite=suite)
    components = review_downstream_output(evidence, components_ref, expected_stage="components", suite=suite)
    records = development + [full, components]
    mod.require(all(x.get("execution_version") == VERSION for x in records),
                "Legacy reuse requires an explicit registered equivalence map; unavailable")
    mod.require(len({x["action_semantics_sha256"] for x in records}) == 1,
                "Development and O2A use different action execution semantics")
    mod.require(full["execution_manifest_sha256"] == components["execution_manifest_sha256"],
                "Full and component timing selected identities differ")
    # Full reconstruction independently checks all88 frozen identities and each
    # same-checkpoint runtime method. Component pass never substitutes full pass.
    mod.require(full.get("observations") == components.get("observations") == 30
        and full.get("methods") == components.get("methods") == 22
        and full.get("attempted_policy_forwards") == components.get("attempted_policy_forwards") == 14300,
        "Incomplete original timing protocol")
    return dict(schema="formal_main_v2", kind="formal_action_O2A_identity_verification", status="verified",
        execution_version=VERSION, action_semantics_sha256=full["action_semantics_sha256"],
        full=full_ref, components=components_ref, development=development_refs,
        scientific_results_recomputed=False, final_release=False)

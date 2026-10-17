"""CPU-only consumption boundaries; no real final values or GPU completion.

The source cases use the frozen provenance parsers with synthetic GPU science
receipts. The operational cases use actual E04 planning, adapter writers, raw
trial validation and root review, with the explicit GPU/source stand-ins in
test_formal_asset_downstream_integration. Unit reconstruction doubles below
test exact transport only; they do not stand in for scientific success.
"""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import test_formal_execution_manifests as manifests
import test_formal_asset_downstream_review as sources
import test_formal_asset_downstream_integration as operational
import test_formal_downstream_supervisor as scheduler_fixtures
from test_formal_analysis import a


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def reference(tool, root, path):
    return dict(path=path.relative_to(root).as_posix(), sha256=tool.digest(path))


@pytest.fixture(scope="module")
def source_project(tmp_path_factory):
    retained = sources.project.__wrapped__(tmp_path_factory)
    yield next(retained)
    with pytest.raises(StopIteration):
        next(retained)


@pytest.mark.parametrize("suite", manifests.runtime.FORMAL_SUITES)
def test_builder_routes_all_suites_to_actual_source_parser_without_state(source_project, suite):
    c, t = sources.acceptance(source_project, suite), manifests.load_tool()
    e = t.Evidence(c.root)
    jobs = t.source_snapshot_jobs(e, c.registration, suite, c.method_rows)
    proof = t.source_provenance_for_rows(e, c.registration, suite, c.method_rows,
        inventory=c.inventory, jobs=jobs)
    assert proof is e.source_provenance[suite]
    assert proof["status"] == "verified" and proof["suite"] == suite
    assert set(proof["method_bindings"]) == {"dense"}
    assert ("metadata_implementation" in proof) == (suite in ("libero_object", "libero_goal"))
    assert ("component_implementation" in proof) == (suite == "libero_goal")
    assert t.MUTABLE_STATE not in e.files
    assert proof["evidence_sha256"].items() <= e.files.items()


@pytest.mark.parametrize("suite", ["libero_object", "libero_goal"])
def test_builder_uses_complete5000_immutable_history_and_exact_selected_identity(source_project, suite):
    c, t = sources.completed_pair(source_project, suite), manifests.load_tool()
    e = t.Evidence(c.accepted.root)
    jobs = t.source_snapshot_jobs(e, c.accepted.registration, suite, c.rows)
    assert {j["job_id"] for j in jobs} == {j["job_id"] for j in c.jobs}
    proof = t.source_provenance_for_rows(e, c.accepted.registration, suite, c.rows,
        inventory=c.accepted.inventory, jobs=jobs)
    assert proof["method_bindings"]["A128_seed17"]["registered_training_job_ids"] == [
        c.prior.job["job_id"], c.last.job["job_id"]]
    changed = deepcopy(c.rows)
    changed[0]["identity"]["checkpoint_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        t.source_provenance_for_rows(t.Evidence(c.accepted.root), c.accepted.registration,
            suite, changed, inventory=c.accepted.inventory, jobs=jobs)
    assert t.MUTABLE_STATE not in e.files


@pytest.mark.parametrize("change", ["absent", "partial", "wrong_source", "wrong_output"])
def test_global_freeze_refuses_missing_or_mismatched_development_root_proof(tmp_path, monkeypatch, change):
    t = manifests.load_tool()
    p = manifests.project.__wrapped__(tmp_path, monkeypatch, t)
    index = manifests.write_development_runs(p)
    suite = "libero_goal"
    if change == "absent":
        index["root_reviews"].pop(suite)
    elif change == "partial":
        index["root_reviews"][suite] = []
    else:
        ref = index["root_reviews"][suite][0]
        item = json.loads((p.root / ref["path"]).read_text(encoding="utf-8"))
        if change == "wrong_source":
            item["source_provenance"]["shared_projection"]["suite"] = "libero_object"
        else:
            item["run_root"] += "/another"
        save(p.root / ref["path"], item)
        ref["sha256"] = t.digest(p.root / ref["path"])
    save(p.root / "development_index.json", index)
    with pytest.raises(ValueError):
        t.build_global(t.Evidence(p.root), p.registration, p.sources, "development_index.json", "frozen",
            checkpoint_inventory="checkpoint_inventory.json")
    assert not (p.root / "frozen/global_freeze.json").exists()


def reconstruction_case(tmp_path, monkeypatch):
    """Small transport double; original scientific reconstruction is tested below."""
    t = manifests.load_tool()
    paths = {name: save(tmp_path / name, dict(synthetic_transport=True)) for name in (
        "results/formal_main_v2/libero_goal/downstream/final/all22/config.json",
        "results/formal_main_v2/pulls/synthetic/receipt.json", "scripts/audit.json")}
    output = "results/formal_main_v2/libero_goal/downstream/final/all22"
    job = dict(job_id="9", status="COMPLETED", experiment=t.SCHEMA, suite="libero_goal", mode="final")
    saved = dict(schema=t.SCHEMA, kind="root_downstream_review", status="passed", reviewed_by="root",
        stage="final", scientific_complete=True, job_id="9", run_root=str(t.P / output), reviewed_utc="before",
        pull_receipt="results/formal_main_v2/pulls/synthetic/receipt.json", registered_jobs_at_review=[job],
        source_provenance=dict(suite="libero_goal", evidence="synthetic-only"),
        asset_runtime_review=dict(status="synthetic-only"), cost=dict(allocations=[]),
        files={output + "/config.json": t.digest(paths[output + "/config.json"])},
        evidence_sha256={"results/formal_main_v2/pulls/synthetic/receipt.json": t.digest(paths["results/formal_main_v2/pulls/synthetic/receipt.json"])},
        audit_source_sha256={"scripts/audit.json": t.digest(paths["scripts/audit.json"])})
    root = save(tmp_path / "results/formal_main_v2/downstream_reviews/9.json", saved)
    ctx = SimpleNamespace(tool=t, saved=saved, rebuilt=deepcopy(saved), root=root, calls=[])
    ctx.rebuilt["reviewed_utc"] = "after"
    def rebuild(job_id, pull, *, project, state, scheduler, helper):
        ctx.calls.append(deepcopy(state))
        assert job_id == "9" and pull == saved["pull_receipt"]
        return deepcopy(ctx.rebuilt)
    scheduler = SimpleNamespace(formal_jobs=lambda state: deepcopy(state["registered_jobs"]), TERMINAL={"COMPLETED"},
        require_root_review=lambda *args, **kwargs: None)
    reviewer = SimpleNamespace(review=rebuild)
    monkeypatch.setattr(t, "load_audit_module", lambda e, name, **kw: scheduler if name == t.DOWNSTREAM_SUPERVISOR
        else reviewer if name == t.DOWNSTREAM_REVIEW else t)
    return ctx


def test_exact_root_rebuild_changes_timestamp_only_and_never_reads_state(tmp_path, monkeypatch):
    c = reconstruction_case(tmp_path, monkeypatch)
    e = c.tool.Evidence(tmp_path)
    result = c.tool.review_downstream_output(e, reference(c.tool, tmp_path, c.root), expected_stage="final", suite="libero_goal")
    assert result == c.rebuilt and c.calls == [dict(registered_jobs=c.saved["registered_jobs_at_review"])]
    assert c.tool.MUTABLE_STATE not in e.files
    assert tmp_path / "results/formal_main_v2/libero_goal/downstream/final/all22/panel.json" in e.forbidden_paths


@pytest.mark.parametrize("field", ["source_provenance", "asset_runtime_review", "cost", "files",
    "registered_jobs_at_review", "audit_source_sha256", "evidence_sha256", "scientific_complete"])
def test_root_rebuild_rejects_any_non_timestamp_change(tmp_path, monkeypatch, field):
    c = reconstruction_case(tmp_path, monkeypatch)
    c.rebuilt[field] = False if field == "scientific_complete" else {}
    with pytest.raises(ValueError, match="exactly rebuild"):
        c.tool.review_downstream_output(c.tool.Evidence(tmp_path), reference(c.tool, tmp_path, c.root),
            expected_stage="final", suite="libero_goal")


@pytest.mark.parametrize("value", ["sealed_final.json", "x/sealed_final.json", "weights/model.json",
    "a.pt", "../outside.json", "results/formal_main_v2/libero_goal/downstream/final/a/panel.json"])
def test_both_consumers_reject_sensitive_paths_before_resolve_stat_or_open(tmp_path, monkeypatch, value):
    t = manifests.load_tool()
    builder, reader = t.Evidence(tmp_path), a.Evidence(tmp_path)
    def forbidden(*args, **kwargs):
        pytest.fail("Sensitive reference reached filesystem resolution or I/O")
    with monkeypatch.context() as guard:
        for name in ("resolve", "stat", "open"):
            guard.setattr(Path, name, forbidden)
        with pytest.raises(ValueError):
            builder.path(value)
        with pytest.raises(ValueError):
            reader.path(dict(path=value, sha256="a" * 64), "forbidden")


def allocation(job, status="COMPLETED", seconds=10):
    return dict(job_id=job, status=status, exit_code="0:0" if status == "COMPLETED" else "1:0",
        elapsed_seconds=seconds, gpus=1, experiment="formal_main_v2", mode="synthetic")


def test_root_cost_includes_zero_call_failure_and_source_once_in_same_accounting(tmp_path):
    reader = a.Evidence(tmp_path)
    rows = [allocation("1", "FAILED", 7), allocation("2", seconds=19), allocation("3", seconds=31)]
    report = dict(cost=dict(allocations=rows[:2]), source_provenance=dict(registered_source_jobs=rows[2:]))
    a.record_root_allocations(reader, report)
    a.record_root_allocations(reader, report)
    a.verify_root_accounting(reader, dict(jobs=rows))
    cost = a.summarize_cost(dict(jobs=rows), expected_job_ids=[r["job_id"] for r in rows], observed_job_ids=set(reader.root_allocations))
    assert cost["actual_allocated_gpu_seconds"] == 57 and cost["unique_jobs"] == 3
    with pytest.raises(a.PendingEvidence, match="root-reviewed allocation: 1"):
        a.verify_root_accounting(reader, dict(jobs=rows[1:]))


@pytest.mark.parametrize("key,value", [("elapsed_seconds", 11), ("gpus", 0), ("exit_code", "9:0"), ("status", "FAILED")])
def test_root_accounting_requires_exact_terminal_allocation(tmp_path, key, value):
    reader, row = a.Evidence(tmp_path), allocation("5")
    a.record_root_allocations(reader, dict(cost=dict(allocations=[row])))
    changed = {**row, key: value}
    with pytest.raises(ValueError, match="accounting differs"):
        a.verify_root_accounting(reader, dict(jobs=[changed]))


@pytest.mark.parametrize("stage", ["final", "full", "components"])
def test_analyzer_requires_exact_root_reviewed_raw_paths_and_merges_hashes(tmp_path, monkeypatch, stage):
    t, reader = manifests.load_tool(), a.Evidence(tmp_path)
    e = t.Evidence(tmp_path)
    directory = tmp_path / f"results/formal_main_v2/libero_goal/downstream/{stage}/all22"
    names = {"config": "config.json", "report": "closed_loop_report.json", "trials": "trials.jsonl"} if stage == "final" else {
        "config": "config.json", "summary": "summary.json", "measurements": "measurements.json", "calls": "calls.jsonl"}
    refs = {key: reference(t, tmp_path, save(directory / name, dict(synthetic_transport=True))) for key, name in names.items()}
    root_ref = reference(t, tmp_path, save(tmp_path / "results/formal_main_v2/downstream_reviews/8.json", dict(synthetic=True)))
    refs["root_review"] = root_ref
    report = dict(job_id="8", scientific_complete=True, source_provenance=dict(suite="libero_goal"),
        cost=dict(allocations=[allocation("8")]), files={ref["path"]: ref["sha256"] for key, ref in refs.items() if key != "root_review"})
    calls = []
    def root_check(evidence, reference, **kwargs):
        calls.append((reference, kwargs))
        evidence.watch(reference["path"])
        return deepcopy(report)
    monkeypatch.setattr(t, "review_downstream_output", root_check)
    reader.root_helper, reader.root_evidence = t, e
    result = a.verify_root_output(reader, refs, suite="libero_goal", stage=stage)
    assert result == report and calls[0][0] == root_ref
    assert calls[0][1] == dict(expected_stage=stage, suite="libero_goal", run_root=directory)
    assert str(tmp_path / root_ref["path"]) in reader.seen and "8" in reader.root_allocations
    if stage == "final":
        assert directory / "panel.json" in e.forbidden_paths
    changed = deepcopy(refs)
    changed["config"] = reference(t, tmp_path, save(directory / "other/config.json", dict(synthetic_transport=True)))
    with pytest.raises(ValueError, match="exact root-reviewed"):
        a.verify_root_output(reader, changed, suite="libero_goal", stage=stage)


def test_analyzer_missing_root_review_stops_before_output_access(tmp_path, monkeypatch):
    reader = a.Evidence(tmp_path)
    monkeypatch.setattr(reader, "path", lambda *a, **kw: pytest.fail("Raw result accessed before its root review"))
    with pytest.raises(a.PendingEvidence, match="root_review"):
        a.verify_root_output(reader, {"config": dict(path="sealed_final.json", sha256="a" * 64)}, suite="libero_goal", stage="final")


def test_analyzer_refuses_mutable_state_or_conflicting_proof_hash_merge(tmp_path):
    t, reader = manifests.load_tool(), a.Evidence(tmp_path)
    reader.root_helper, reader.root_evidence = t, t.Evidence(tmp_path)
    reader.root_evidence.files[t.MUTABLE_STATE] = "a" * 64
    with pytest.raises(ValueError, match="Mutable supervisor"):
        a.merge_root_evidence(reader)
    reader.root_evidence.files.clear()
    path = save(tmp_path / "stable.json", dict(synthetic=True))
    reader.root_evidence.watch(path)
    reader.seen[str(path)] = "0" * 64
    with pytest.raises(ValueError, match="conflicts"):
        a.merge_root_evidence(reader)


@pytest.fixture(scope="module")
def actual_project(tmp_path_factory):
    retained = operational.actual_project.__wrapped__(tmp_path_factory)
    yield next(retained)
    with pytest.raises(StopIteration):
        next(retained)


@pytest.mark.parametrize("suite", ["libero_object", "libero_goal"])
def test_actual_plan_writer_resumed_complete_root_is_consumed_by_builder(actual_project, monkeypatch, suite):
    """Actual operational/scientific parsers; declared upstream/GPU stand-ins only."""
    c = operational.prepare(actual_project, monkeypatch, suite)
    first = operational.execute_plan(c, monkeypatch)
    assert first["completed_trials"] == 1 and not first["scientific_complete"]
    with pytest.raises(ValueError, match="complete matching"):
        c.helper.review_downstream_output(c.helper.Evidence(c.p.root), reference(c.helper, c.p.root, c.p.root / c.review_ref),
            expected_stage="development", suite=suite)
    c.args.prior_review, c.args.resume, c.args.stop_after = c.review_ref, True, None
    c.case.job = str(int(c.case.job) + 1000)
    c.plan = c.t.plan(c.args, c.state, project=c.p.root, helper=c.helper)
    complete = operational.execute_plan(c, monkeypatch)
    assert complete["scientific_complete"] and complete["completed_trials"] == 100
    assert len(complete["cost"]["allocations"]) == 2
    reviewer = scheduler_fixtures.module("scripts/review_formal_downstream.py")
    original = c.helper.load_audit_module
    def audits(evidence, name, **kwargs):
        if name == c.helper.DOWNSTREAM_SUPERVISOR:
            evidence.watch(name)
            return c.t
        if name == c.helper.DOWNSTREAM_REVIEW:
            evidence.watch(name)
            return reviewer
        if name == "scripts/formal_execution_manifests.py":
            evidence.watch(name)
            return c.helper
        return original(evidence, name, **kwargs)
    monkeypatch.setattr(c.helper, "load_audit_module", audits)
    e = c.helper.Evidence(c.p.root)
    rebuilt = c.helper.review_downstream_output(e, reference(c.helper, c.p.root, c.p.root / c.review_ref),
        expected_stage="development", suite=suite, run_root=c.p.root / c.actual.relative)
    assert {k: v for k, v in rebuilt.items() if k != "reviewed_utc"} == {
        k: v for k, v in complete.items() if k != "reviewed_utc"}
    assert rebuilt["asset_runtime_review"]["metadata_loads"] == 1
    assert rebuilt["asset_runtime_review"]["component_loads"] == (2 if suite == "libero_goal" else 0)
    assert c.t.STATE not in e.files
    # The parent ledger grew; an old partial receipt cannot be relabelled as a
    # complete final receipt or rebuilt against the now-extended raw ledger.
    assert first["completed_trials"] == 1 and len(rebuilt["raw_invocation_job_ids"]) == 2

"""Independent CPU checks for the external asset submitter's resume gate.

All checkpoint references are metadata only. No checkpoint, network client,
GPU library, Slurm process, or project state is opened by these tests.
"""
from argparse import Namespace
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "asset_resume_independent_test", ROOT / "scripts/ops/formal_asset_supervisor.py")
ops = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ops)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def case_factory(tmp_path):
    def factory(*, completed=(3500, 3500), prior_target=3500, target=4000,
                omitted_reports=(), unstarted=(), final_arms=()):
        root = tmp_path / "project"
        outrel = "results/formal_main_v2/libero_object/k128/seed17/training"
        pair = dict(checkpoint_root_server=(
            "/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/"
            "formal_main_v2/libero_object/k128/seed17"))
        runtime = dict(ops.RUNTIME_KEYS, files={
            **ops.PINNED_FILES,
            ops.RUNTIME_KEYS["wrapper"]: "8" * 64,
            ops.RUNTIME_KEYS["slurm"]: "9" * 64})
        latest = dict(job_id="9000001", segment_end=prior_target)
        review = dict(schema=ops.ROUND, kind="root_segment_review", status="passed",
            job_id=latest["job_id"], runtime_compatibility=runtime,
            requested_segment_end=prior_target, allowed_next_segment_end=target,
            completed_by_arm=dict(zip("AB", completed)),
            server_resume_checks=[], server_resume_checklist=[], evidence_sha256={})
        reports, paths = {}, {}

        def write_report(arm, changes=None, *, bind=True):
            if changes:
                reports[arm].update(changes)
            path = paths[arm]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(reports[arm], sort_keys=True) + "\n", encoding="utf-8")
            if bind:
                review["evidence_sha256"][path.relative_to(root).as_posix()] = digest(path)

        for index, arm in enumerate("AB"):
            checkpoint = pair["checkpoint_root_server"] + "/" + arm + "/resume.pt"
            checksum = ("a" if arm == "A" else "b") * 64
            started = arm not in unstarted
            review["server_resume_checklist"].append(dict(arm=arm, path=checkpoint,
                must_exist=started, sha256=checksum if started else None))
            actual = dict(arm=arm, path=checkpoint, exists=started)
            if started:
                actual.update(sha256=checksum, bytes=100 + index)
            review["server_resume_checks"].append(actual)
            paths[arm] = root / outrel / arm / (
                "training_report.json" if arm in final_arms else "progress_report.json")
            # These scalar fields match the frozen progress writer. The final
            # writer deliberately does not emit resume_checkpoint/resume_sha256.
            reports[arm] = dict(schema=ops.ROUND, arm=arm,
                status="completed" if arm in final_arms else "checkpointed",
                training_updates_completed=completed[index],
                committed_samples=completed[index] * 8,
                next_sample_cursor=completed[index] * 8,
                vla_parameters_unchanged=True)
            if arm not in final_arms:
                reports[arm].update(resume_checkpoint=checkpoint, resume_sha256=checksum)
            else:
                reports[arm].update(best_checkpoint=pair["checkpoint_root_server"] +
                    "/" + arm + "/best.pt", best_checkpoint_sha256="c" * 64)
                journal = root / outrel / arm / "attempts/20261016T000000_fixture/cost_events.jsonl"
                journal.parent.mkdir(parents=True, exist_ok=True)
                rows = [dict(event="checkpoint_commit", attempt_id=journal.parent.name,
                    job_id=latest["job_id"], completed_update=5000,
                    seconds=0.1, resume_sha256=checksum),
                    dict(event="attempt_end", attempt_id=journal.parent.name,
                    job_id=latest["job_id"], status="completed", completed_update=5000)]
                journal.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
                review["evidence_sha256"][journal.relative_to(root).as_posix()] = digest(journal)
            if arm not in omitted_reports and started:
                write_report(arm)
        return SimpleNamespace(root=root, pair=pair, outrel=outrel, latest=latest,
            review=review, runtime=runtime, target=target, reports=reports,
            paths=paths, write_report=write_report)
    return factory


def validate(case):
    return ops.validate_pair_resume(case.root, case.pair, case.outrel, case.latest,
        case.review, case.runtime, case.target)


def test_complete_common_boundary_requires_next_500(case_factory):
    case = case_factory()
    checks = validate(case)
    assert checks == case.review["server_resume_checks"]
    assert [c["arm"] for c in checks] == ["A", "B"]


def test_partial_boundary_can_only_finish_original_target(case_factory):
    case = case_factory(completed=(3500, 3400), target=3500)
    assert len(validate(case)) == 2


def test_reviewed_unstarted_arm_requires_absence_not_missing_started_evidence(case_factory):
    case = case_factory(completed=(500, 0), prior_target=500, target=500, unstarted=("B",))
    assert validate(case)[1] == dict(arm="B",
        path=case.pair["checkpoint_root_server"] + "/B/resume.pt", exists=False)


@pytest.mark.parametrize("field", ["server_resume_checks", "server_resume_checklist"])
@pytest.mark.parametrize("change", ["missing", "duplicate"])
def test_missing_or_duplicate_arm_rejected(case_factory, field, change):
    case = case_factory()
    case.review[field] = case.review[field][:1] if change == "missing" else [
        deepcopy(case.review[field][0]), deepcopy(case.review[field][0])]
    with pytest.raises(ValueError, match="unique A and B"):
        validate(case)


@pytest.mark.parametrize("collection,field,value", [
    ("server_resume_checks", "path", "/wrong/B/resume.pt"),
    ("server_resume_checklist", "path", "/wrong/B/resume.pt"),
    ("server_resume_checks", "exists", False),
    ("server_resume_checklist", "must_exist", False),
    ("server_resume_checks", "sha256", "0" * 64),
    ("server_resume_checklist", "sha256", "0" * 64),
    ("server_resume_checks", "bytes", 0),
    ("server_resume_checks", "bytes", True),
])
def test_invalid_server_resume_metadata_rejected(case_factory, collection, field, value):
    case = case_factory()
    case.review[collection][1][field] = value
    with pytest.raises(ValueError, match="Resume path|Server resume"):
        validate(case)


@pytest.mark.parametrize("field,value", [
    ("arm", "A"), ("training_updates_completed", 3000),
    ("next_sample_cursor", 27999), ("resume_checkpoint", "/wrong/B/resume.pt"),
    ("resume_sha256", "not-a-sha"),
])
def test_wrong_progress_identity_rejected_even_if_its_bytes_are_bound(case_factory, field, value):
    case = case_factory()
    case.write_report("B", {field: value})
    with pytest.raises(ValueError, match="Progress arm/boundary/cursor/resume"):
        validate(case)


def test_progress_bytes_changed_after_review_are_rejected(case_factory):
    case = case_factory()
    case.write_report("B", {"extra": "changed"}, bind=False)
    with pytest.raises(ValueError, match="Unreviewed pair progress"):
        validate(case)


def test_started_arm_missing_progress_cannot_be_reinitialized(case_factory):
    case = case_factory(omitted_reports=("B",))
    with pytest.raises(ValueError, match="Missing started-arm"):
        validate(case)


def test_unstarted_arm_with_attempt_journal_is_rejected(case_factory):
    case = case_factory(completed=(500, 0), prior_target=500, target=500, unstarted=("B",))
    journal = case.root / case.outrel / "B/attempts/started/cost_events.jsonl"
    journal.parent.mkdir(parents=True)
    journal.write_text('{"event":"attempt_start"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="Missing started-arm"):
        validate(case)


@pytest.mark.parametrize("mutation", ["skip", "repeat", "rollback", "review_target",
    "review_latest_target", "overrun", "missing_arm", "negative", "noninteger", "runtime", "job"])
def test_boundary_and_review_identity_fail_closed(case_factory, mutation):
    case = case_factory()
    if mutation in ("skip", "repeat", "rollback"):
        case.target = {"skip": 4500, "repeat": 3500, "rollback": 3000}[mutation]
        case.review["allowed_next_segment_end"] = case.target
    elif mutation == "review_target":
        case.review["allowed_next_segment_end"] = 4500
    elif mutation == "review_latest_target":
        case.review["requested_segment_end"] = 3000
    elif mutation == "overrun":
        case.review["completed_by_arm"]["B"] = 3501
    elif mutation == "missing_arm":
        del case.review["completed_by_arm"]["B"]
    elif mutation == "negative":
        case.review["completed_by_arm"]["B"] = -1
    elif mutation == "noninteger":
        case.review["completed_by_arm"]["B"] = True
    elif mutation == "runtime":
        case.review["runtime_compatibility"] = {}
    elif mutation == "job":
        case.review["job_id"] = "9000002"
    with pytest.raises(ValueError):
        validate(case)


def test_completed_5000_pair_cannot_be_extended(case_factory):
    case = case_factory(completed=(5000, 5000), prior_target=5000, target=5500)
    with pytest.raises(ValueError, match="next500"):
        validate(case)


def test_completed_final_arm_writer_shape_allows_other_arm_to_finish(case_factory):
    case = case_factory(completed=(5000, 4900), prior_target=5000, target=5000, final_arms=("A",))
    assert "resume_sha256" not in case.reports["A"]
    assert validate(case) == case.review["server_resume_checks"]


@pytest.mark.parametrize("mutation", ["unbound", "changed_bytes", "wrong_commit", "wrong_sha", "conflicting_commit"])
def test_final_arm_resume_requires_bound_exact_final_commit(case_factory, mutation):
    case = case_factory(completed=(5000, 4900), prior_target=5000, target=5000, final_arms=("A",))
    journal = next((case.root / case.outrel / "A/attempts").glob("*/cost_events.jsonl"))
    relative = journal.relative_to(case.root).as_posix()
    rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]
    if mutation == "unbound":
        del case.review["evidence_sha256"][relative]
    else:
        if mutation == "wrong_commit":
            rows[0]["completed_update"] = 4950
        elif mutation == "wrong_sha":
            rows[0]["resume_sha256"] = "0" * 64
        elif mutation == "conflicting_commit":
            rows.insert(1, dict(rows[0], resume_sha256="0" * 64))
        else:
            rows[0]["seconds"] = 0.2
        journal.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        if mutation != "changed_bytes":
            case.review["evidence_sha256"][relative] = digest(journal)
    with pytest.raises(ValueError):
        validate(case)


def test_remote_hash_check_uses_only_registered_metadata_and_preserves_unknown_arm(case_factory, monkeypatch):
    case = case_factory(completed=(500, 0), prior_target=500, target=500, unstarted=("B",))
    checks = validate(case)
    commands = []
    monkeypatch.setattr(ops.f, "remote", lambda cmd: commands.append(cmd) or json.dumps(checks))
    assert ops.verify_remote_resumes(checks) is None
    assert len(commands) == 1
    assert "hashlib.sha256" in commands[0] and "torch" not in commands[0]
    assert all(row["path"] in commands[0] for row in checks)


@pytest.mark.parametrize("mutation", ["sha", "bytes", "missing", "extra", "swapped", "absent"])
def test_remote_rehash_mismatch_rejects_before_submission(case_factory, monkeypatch, mutation):
    checks = validate(case_factory())
    observed = deepcopy(checks)
    if mutation == "sha":
        observed[0]["sha256"] = "0" * 64
    elif mutation == "bytes":
        observed[0]["bytes"] += 1
    elif mutation == "missing":
        observed.pop()
    elif mutation == "extra":
        observed.append(deepcopy(observed[-1]))
    elif mutation == "swapped":
        observed.reverse()
    else:
        observed[0] = {k: v for k, v in observed[0].items() if k not in ("sha256", "bytes")}
        observed[0]["exists"] = False
    monkeypatch.setattr(ops.f, "remote", lambda command: json.dumps(observed))
    with pytest.raises(ValueError, match="Server resume bytes changed"):
        ops.verify_remote_resumes(checks)


@pytest.mark.parametrize("failed_gate", ["progress", "resume"])
def test_submit_gate_failure_never_writes_invocation_or_calls_scp_sbatch(case_factory, monkeypatch, failed_gate):
    case = case_factory()
    checks = validate(case)
    calls, writes = [], []
    invocation = dict(stage_key="libero_object_train_k128_seed17", stage="train")
    plan = dict(invocation=invocation, prior_job_ids=[case.latest["job_id"]],
        output=ops.f.P + "/" + case.outrel, server_resume_checks=checks)
    monkeypatch.setattr(ops, "capacity", lambda *a: None)
    monkeypatch.setattr(ops, "build_plan", lambda *a: plan)
    monkeypatch.setattr(ops, "verify_remote_inputs", lambda *a: calls.append("inputs"))

    def progress(*args):
        calls.append("progress")
        if failed_gate == "progress":
            raise ValueError("synthetic stale remote progress")
    monkeypatch.setattr(ops.f, "verify_remote_training_progress", progress)
    monkeypatch.setattr(ops.f, "remote", lambda cmd: calls.append("resume") or "[]")
    monkeypatch.setattr(ops.f, "write", lambda *args: writes.append(args))
    monkeypatch.setattr(ops.subprocess, "run", lambda *a, **k: pytest.fail("must not spawn SCP/Slurm"))
    state = dict(pending_submission=None)
    with pytest.raises(ValueError):
        ops.submit(Namespace(stage="train"), state, [case.latest])
    assert calls == (["inputs", "progress"] if failed_gate == "progress" else ["inputs", "progress", "resume"])
    assert not writes and state["pending_submission"] is None


def test_unknown_sbatch_outcome_retains_pending_record_without_retry(monkeypatch):
    calls, writes = [], []
    invocation = dict(stage="acceptance", suite="libero_object", stage_key="libero_object_acceptance",
        source_root="/frozen", source_sha256="a" * 64, registered_utc="2026-10-16T00:00:00Z",
        runtime_compatibility={"slurm": ops.RUNTIME_KEYS["slurm"]})
    plan = dict(invocation=invocation, prior_job_ids=[], output="/output",
        remote_preflight="test ! -e /output", invocation_relative="results/synthetic/invocation.json")
    monkeypatch.setattr(ops, "capacity", lambda *a: None)
    monkeypatch.setattr(ops, "build_plan", lambda *a: plan)
    monkeypatch.setattr(ops, "verify_remote_inputs", lambda *a: None)
    monkeypatch.setattr(ops.f, "remote", lambda cmd: calls.append(("remote", cmd)) or "")
    monkeypatch.setattr(ops.f, "sha", lambda *a: "d" * 64)
    monkeypatch.setattr(ops.f, "write", lambda path, payload: writes.append((str(path), deepcopy(payload))))

    def run(command, **kwargs):
        calls.append(("subprocess", command))
        return SimpleNamespace(returncode=0, stdout="", stderr="") if command[0] == "scp" else (
            SimpleNamespace(returncode=255, stdout="", stderr="synthetic SSH connection lost"))
    monkeypatch.setattr(ops.subprocess, "run", run)
    state = dict(registered_jobs=[], pending_submission=None, current_round_cost={"registered_jobs": 0})
    with pytest.raises(ValueError, match="unresolved"):
        ops.submit(Namespace(stage="acceptance"), state, [])
    assert state["pending_submission"]["invocation_sha256"] == "d" * 64
    assert state["registered_jobs"] == []
    assert len([c for kind, c in calls if kind == "subprocess" and "sbatch" in c[-1]]) == 1
    assert writes[-1][1]["pending_submission"] == state["pending_submission"]

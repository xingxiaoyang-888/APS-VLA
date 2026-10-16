"""CPU-only Goal dispatcher checks; all writes and remote calls are synthetic."""
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
    "goal_asset_supervisor_independent", ROOT / "scripts/ops/formal_goal_asset_supervisor.py")
ops = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ops)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def arguments(**changes):
    values = dict(stage="acceptance", suite="libero_goal", budget=128, seed=17,
        segment=500, wall_seconds=12600, resume=False, repair_record=None,
        source_inventory=Path(ops.base.SOURCE_INVENTORY),
        runtime_registration=Path(ops.BASE_REG),
        component_execution_registration=Path("synthetic/goal_execution.json"))
    values.update(changes)
    return Namespace(**values)


@pytest.fixture
def contract_case(tmp_path):
    """Only the old pinned text files are copied; no model/cache/data is read."""
    root = tmp_path / "project"
    for rel in (ops.BASE_REG, ops.BASE_TOOL, ops.TOOL):
        destination = root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / rel).read_bytes())
    files = {}
    for key in ("wrapper", "adapter", "slurm", "registration"):
        rel = ops.COMPONENT_KEYS[key]
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("synthetic " + key + "\n", encoding="utf-8")
        files[rel] = sha(f)
    review = root / "synthetic/cpu_review.json"
    write(review, {"status": "passed", "scope": "synthetic only"})
    contract = dict(ops.COMPONENT_KEYS, files=files)
    registration = dict(schema=ops.ROUND, kind="goal_component_execution_registration",
        status="reviewed", metadata_execution_registration=ops.BASE_REG,
        metadata_execution_registration_sha256=ops.BASE_REG_SHA,
        source_inventory_sha256=ops.base.SOURCE_INVENTORY_SHA,
        component_compatibility=contract, root_submission_tool=ops.TOOL,
        root_submission_tool_sha256=sha(root / ops.TOOL),
        review_inputs={review.relative_to(root).as_posix(): sha(review)})
    path = root / "synthetic/goal_execution.json"
    write(path, registration)
    return SimpleNamespace(root=root, args=arguments(), registration=registration,
        path=path, contract=contract, review_path=review)


def save_registration(case):
    write(case.path, case.registration)


def test_exact_four_contract_accepts_bound_synthetic_bytes(contract_case):
    case = contract_case
    assert ops.component_contract(case.root, case.args) == case.contract
    assert len(case.contract["files"]) == 4


@pytest.mark.parametrize("change", ["missing", "extra", "wrong_suite", "wrong_wrapper", "bad_sha", "changed_file"])
def test_component_contract_rejects_changed_file_set_or_identity(contract_case, change):
    case = contract_case
    contract = case.registration["component_compatibility"]
    if change == "missing":
        del contract["files"][ops.COMPONENT_KEYS["adapter"]]
    elif change == "extra":
        contract["files"]["synthetic/unregistered.py"] = "0" * 64
    elif change == "wrong_suite":
        contract["suite"] = "libero_object"
    elif change == "wrong_wrapper":
        contract["wrapper"] = "scripts/server/run_formal_asset_stage.py"
    elif change == "bad_sha":
        contract["files"][ops.COMPONENT_KEYS["adapter"]] = "not-a-sha"
    else:
        (case.root / ops.COMPONENT_KEYS["adapter"]).write_text("changed\n", encoding="utf-8")
    save_registration(case)
    with pytest.raises(ValueError):
        ops.component_contract(case.root, case.args)


@pytest.mark.parametrize("change", ["unreviewed", "metadata_registration", "metadata_sha", "source_sha",
    "tool_path", "tool_sha", "missing_reviews", "changed_review", "changed_base", "changed_base_registration"])
def test_component_contract_binds_pinned_metadata_root_and_reviews(contract_case, change):
    case = contract_case
    keys = {"unreviewed": "status", "metadata_registration": "metadata_execution_registration",
        "metadata_sha": "metadata_execution_registration_sha256", "source_sha": "source_inventory_sha256",
        "tool_path": "root_submission_tool", "tool_sha": "root_submission_tool_sha256"}
    if change in keys:
        case.registration[keys[change]] = "wrong"
    elif change == "missing_reviews":
        case.registration["review_inputs"] = {}
    elif change == "changed_review":
        write(case.review_path, {"status": "changed"})
    elif change == "changed_base":
        (case.root / ops.BASE_TOOL).write_text("changed\n", encoding="utf-8")
    else:
        write(case.root / ops.BASE_REG, {"status": "changed"})
    save_registration(case)
    with pytest.raises(ValueError):
        ops.component_contract(case.root, case.args)


def test_contract_refuses_external_review_path(contract_case):
    case = contract_case
    outside = case.root.parent / "outside.json"
    write(outside, {"synthetic": True})
    case.registration["review_inputs"] = {str(outside): sha(outside)}
    save_registration(case)
    with pytest.raises(ValueError, match="belong to CTI-VLA"):
        ops.component_contract(case.root, case.args)


def component_evidence(case, job_id):
    """Use the actual helper's summary field names, with local synthetic bytes."""
    helper = case.root / ops.REVIEW_HELPER
    if not helper.exists():
        helper.parent.mkdir(parents=True, exist_ok=True)
        helper.write_bytes((ROOT / ops.REVIEW_HELPER).read_bytes())
    evidence = {}
    for name in ("identity.json", "events.jsonl", "completion.json"):
        f = case.root / f"synthetic/component/{job_id}" / name
        write(f, {"job_id": job_id, "synthetic": True, "artifact": name})
        evidence[f.relative_to(case.root).as_posix()] = sha(f)
    return dict(schema=ops.ROUND, kind="goal_component_compatibility_review", status="verified",
        suite="libero_goal", job_id=job_id, component_compatibility=case.contract,
        helper_sha256=sha(helper), evidence_sha256=evidence)


def gate_review(case, job_id):
    return dict(schema=ops.ROUND, status="passed", job_id=job_id, suite="libero_goal",
        component_compatibility=case.contract,
        component_compatibility_review=component_evidence(case, job_id))


def test_own_component_review_reads_sha_bound_helper_evidence(contract_case):
    case = contract_case
    review = gate_review(case, "9001000")
    job = dict(job_id="9001000", component_compatibility=case.contract)
    assert ops.verify_component_review(case.root, review, job, case.contract) is None


@pytest.mark.parametrize("change", ["job_contract", "review_contract", "nested_contract", "status",
    "job_id", "helper", "empty_evidence", "changed_evidence"])
def test_own_component_review_rejects_missing_or_stale_evidence(contract_case, change):
    case = contract_case
    review = gate_review(case, "9001000")
    job = dict(job_id="9001000", component_compatibility=case.contract)
    ev = review["component_compatibility_review"]
    if change == "job_contract":
        del job["component_compatibility"]
    elif change == "review_contract":
        del review["component_compatibility"]
    elif change == "nested_contract":
        ev["component_compatibility"] = {}
    elif change == "status":
        ev["status"] = "pending"
    elif change == "job_id":
        ev["job_id"] = "9001001"
    elif change == "helper":
        ev["helper_sha256"] = "0" * 64
    elif change == "empty_evidence":
        ev["evidence_sha256"] = {}
    else:
        write(case.root / next(iter(ev["evidence_sha256"])), {"changed": True})
    with pytest.raises(ValueError):
        ops.verify_component_review(case.root, review, job, case.contract)


@pytest.mark.parametrize("suite", ["libero_10", "libero_spatial", "libero_object"])
def test_goal_only_guard_runs_before_reading_contract_or_base(monkeypatch, suite):
    monkeypatch.setattr(ops, "component_contract", lambda *a: pytest.fail("must reject suite first"))
    with pytest.raises(ValueError, match="Goal only"):
        ops.build_plan(arguments(suite=suite), {}, [])


def base_plan(case, *, prior=()):
    metadata = json.loads((ROOT / ops.BASE_REG).read_text(encoding="utf-8"))["runtime_compatibility"]
    invocation = dict(schema=ops.ROUND, stage="train", stage_key="libero_goal_train_k128_seed17",
        suite="libero_goal", source_root=ops.f.P + "/snapshots/formal_main_v2_run_564be0995e",
        source_sha256="d" * 64, entrypoint="scripts/run_formal_future.py", argv=["--config", "/original/config"],
        watched_files={"/original/config": "c" * 64}, runtime_compatibility=metadata,
        registered_utc="2026-10-16T00:00:00Z", segment_end=500)
    return dict(invocation=invocation, prior_job_ids=list(prior),
        invocation_relative="results/synthetic/invocation.json",
        output=ops.f.P + "/results/formal_main_v2/libero_goal/k128/seed17/training",
        remote_preflight="test ! -e /synthetic", server_resume_checks=[])


def test_goal_delegates_base_plan_and_adds_only_separate_contract(contract_case, monkeypatch):
    case = contract_case
    plan = base_plan(case)
    plan["invocation"]["stage"] = "acceptance"
    original = deepcopy(plan)
    seen = []
    monkeypatch.setattr(ops.base, "build_plan", lambda *a, **k: seen.append((a, k)) or deepcopy(plan))
    result = ops.build_plan(case.args, {}, [], root=case.root)
    assert seen and seen[0][1] == {"root": case.root}
    assert result["invocation"].pop("component_compatibility") == case.contract
    assert result == original


def test_training_requires_own_goal_component_acceptance_and_latest_resume(contract_case, monkeypatch):
    case = contract_case
    plan = base_plan(case, prior=("9001001",))
    accept = gate_review(case, "9001000")
    resume = gate_review(case, "9001001")
    write(case.root / "results/formal_main_v2/libero_goal/acceptance/root_review.json", accept)
    relative = plan["output"][len(ops.f.P) + 1:]
    write(case.root / relative / "segment_reviews/9001001.json", resume)
    jobs = [dict(job_id="9001000", component_compatibility=case.contract),
        dict(job_id="9001001", component_compatibility=case.contract, submitted_utc="2026-10-16T00:00:00Z")]
    monkeypatch.setattr(ops.base, "build_plan", lambda *a, **k: deepcopy(plan))
    assert ops.build_plan(arguments(stage="train"), {}, jobs, root=case.root)["invocation"]["component_compatibility"] == case.contract
    resume["component_compatibility_review"]["status"] = "pending"
    write(case.root / relative / "segment_reviews/9001001.json", resume)
    with pytest.raises(ValueError, match="has not been root-verified"):
        ops.build_plan(arguments(stage="train"), {}, jobs, root=case.root)


@pytest.mark.parametrize("which", ["component", "execution_registration"])
def test_failure_repair_additionally_binds_goal_contract_and_execution(contract_case, monkeypatch, which):
    case = contract_case
    plan = base_plan(case)
    monkeypatch.setattr(ops.base, "build_plan", lambda *a, **k: deepcopy(plan))
    repair = case.root / "synthetic/repair.json"
    payload = dict(component_compatibility=case.contract,
        component_execution_registration_sha256=sha(case.path))
    payload["component_compatibility" if which == "component" else "component_execution_registration_sha256"] = "wrong"
    write(repair, payload)
    with pytest.raises(ValueError, match="Repair record"):
        ops.build_plan(arguments(repair_record=repair), {}, [], root=case.root)


def test_actual_base_builder_keeps_all_failed_attempt_repair_requirement(tmp_path, monkeypatch):
    """Exercise the real old builder; no real invocation or input is changed."""
    root = tmp_path / "project"
    inventory = json.loads((ROOT / ops.base.SOURCE_INVENTORY).read_text(encoding="utf-8"))
    registration = json.loads((ROOT / "configs/experiments/formal_main_v2.json").read_text(encoding="utf-8"))
    suite = registration["suites"]["libero_goal"]
    # Keep the real builder's project boundary intact even when pytest's default
    # temporary directory is outside this checkout. Only pinned source/config
    # text and the development/training manifests are copied, never tensors or
    # sealed initial-state files.
    copied = set(inventory["files"]) | {
        ops.base.SOURCE_INVENTORY, suite["protocol"], suite["windows"]}
    for relative in copied:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / relative).read_bytes())
    metadata = json.loads((ROOT / ops.BASE_REG).read_text(encoding="utf-8"))["runtime_compatibility"]
    component = dict(ops.COMPONENT_KEYS, files={ops.COMPONENT_KEYS[k]: "a" * 64
        for k in ("wrapper", "adapter", "slurm", "registration")})
    execution = root / "execution.json"
    write(execution, {"synthetic": True})
    repair = root / "repair.json"
    payload = dict(status="reviewed", stage_key="libero_goal_acceptance",
        target_source_sha256=inventory["source_sha256"],
        segment_end=None, runtime_compatibility=metadata, failed_job_ids=["9001000", "9001001"],
        component_compatibility=component, component_execution_registration_sha256=sha(execution))
    write(repair, payload)
    jobs = [dict(job_id=str(j), stage_key="libero_goal_acceptance", status="FAILED", exit_code="1:0")
        for j in (9001000, 9001001)]
    monkeypatch.setattr(ops, "component_contract", lambda *a: component)
    monkeypatch.setattr(ops.base, "runtime_contract", lambda *a: metadata)
    args = arguments(repair_record=repair, component_execution_registration=execution)
    plan = ops.build_plan(args, {}, jobs, root=root)
    assert plan["invocation_relative"].endswith("attempt03.json")
    assert plan["invocation"]["runtime_compatibility"] == metadata
    payload["failed_job_ids"] = ["9001001"]
    write(repair, payload)
    with pytest.raises(ValueError, match="all failed jobs"):
        ops.build_plan(args, {}, jobs, root=root)


def test_remote_component_verification_checks_exact_four_files(contract_case, monkeypatch):
    expected = {ops.f.P + "/" + p: h for p, h in contract_case.contract["files"].items()}
    commands = []
    monkeypatch.setattr(ops.f, "remote", lambda cmd: commands.append(cmd) or json.dumps(expected))
    assert ops.verify_remote_components({"component_compatibility": contract_case.contract}) is None
    assert len(commands) == 1 and all(path in commands[0] for path in expected)


@pytest.mark.parametrize("change", ["missing", "extra", "sha"])
def test_remote_component_sha_mismatch_rejected(contract_case, monkeypatch, change):
    expected = {ops.f.P + "/" + p: h for p, h in contract_case.contract["files"].items()}
    if change == "missing":
        expected.pop(next(iter(expected)))
    elif change == "extra":
        expected["/extra"] = "0" * 64
    else:
        expected[next(iter(expected))] = "0" * 64
    monkeypatch.setattr(ops.f, "remote", lambda cmd: json.dumps(expected))
    with pytest.raises(ValueError, match="Remote Goal runtime"):
        ops.verify_remote_components({"component_compatibility": contract_case.contract})


@pytest.mark.parametrize("status", ["PENDING", "RUNNING", "SUBMITTED"])
def test_eight_requested_slots_prevent_any_goal_contract_or_submission(monkeypatch, status):
    jobs = [dict(job_id=str(i), mode="train", status=status, gpus=0 if status == "PENDING" else 1)
        for i in range(8)]
    monkeypatch.setattr(ops, "build_plan", lambda *a: pytest.fail("must reject capacity before plan"))
    with pytest.raises(ValueError, match="eight"):
        ops.submit(arguments(), {"pending_submission": None}, jobs)


def test_unresolved_submission_stops_before_any_new_plan(monkeypatch):
    monkeypatch.setattr(ops, "build_plan", lambda *a: pytest.fail("must reject unresolved submission"))
    with pytest.raises(ValueError, match="Unresolved"):
        ops.submit(arguments(), {"pending_submission": {"invocation": "old.json"}}, [])


@pytest.mark.parametrize("status", ["PENDING", "RUNNING", "SUBMITTED"])
def test_active_same_goal_stage_cannot_be_submitted_again(tmp_path, monkeypatch, status):
    metadata = json.loads((ROOT / ops.BASE_REG).read_text())["runtime_compatibility"]
    monkeypatch.setattr(ops, "component_contract", lambda *a: {})
    monkeypatch.setattr(ops.base, "runtime_contract", lambda *a: metadata)
    with pytest.raises(ValueError, match="already has an active"):
        ops.build_plan(arguments(), {}, [dict(job_id="9001000", stage_key="libero_goal_acceptance", status=status)])


@pytest.fixture
def submit_stub(contract_case, monkeypatch):
    case = contract_case
    plan = base_plan(case)
    plan["invocation"].update(stage="acceptance", stage_key="libero_goal_acceptance", segment_end=None,
        component_compatibility=case.contract)
    calls, writes = [], []
    monkeypatch.setattr(ops.base, "capacity", lambda *a: calls.append("capacity"))
    monkeypatch.setattr(ops, "build_plan", lambda *a: deepcopy(plan))
    monkeypatch.setattr(ops.base, "verify_remote_inputs", lambda *a: calls.append("metadata_sha"))
    monkeypatch.setattr(ops, "verify_remote_components", lambda *a: calls.append("component_sha"))
    monkeypatch.setattr(ops.f, "remote", lambda cmd: calls.append(("remote", cmd)) or "")
    monkeypatch.setattr(ops.f, "sha", lambda path: "e" * 64)
    monkeypatch.setattr(ops.f, "write", lambda path, payload: writes.append((str(path), deepcopy(payload))))
    state = dict(registered_jobs=[], pending_submission=None, current_round_cost={"registered_jobs": 0})
    return SimpleNamespace(plan=plan, calls=calls, writes=writes, state=state, case=case)


def test_submitted_job_uses_new_slurm_and_retains_old_metadata_contract(submit_stub, monkeypatch):
    data = submit_stub
    spawned = []
    monkeypatch.setattr(ops.subprocess, "run", lambda cmd, **kwargs: spawned.append(cmd) or (
        SimpleNamespace(returncode=0, stdout="" if cmd[0] == "scp" else "9001234;cluster\n", stderr="")))
    ops.submit(arguments(), data.state, [])
    job = data.state["registered_jobs"][0]
    assert job["status"] == "SUBMITTED" and job["gpus"] == 1
    assert job["runtime_compatibility"] == data.plan["invocation"]["runtime_compatibility"]
    assert job["component_compatibility"] == data.case.contract
    assert ops.COMPONENT_KEYS["slurm"] in spawned[-1][-1]
    assert ops.base.RUNTIME_KEYS["slurm"] not in spawned[-1][-1]
    assert data.calls[:3] == ["capacity", "metadata_sha", "component_sha"]
    assert all("job_receipts" not in path for path, payload in data.writes)
    assert data.state["pending_submission"] is None


def test_remote_component_failure_precedes_all_writes_or_sbatch(submit_stub, monkeypatch):
    data = submit_stub
    def refuse(*args):
        raise ValueError("Remote Goal runtime differs")
    monkeypatch.setattr(ops, "verify_remote_components", refuse)
    monkeypatch.setattr(ops.subprocess, "run", lambda *a, **k: pytest.fail("cannot spawn"))
    with pytest.raises(ValueError, match="Remote Goal runtime"):
        ops.submit(arguments(), data.state, [])
    assert not data.writes and data.state["pending_submission"] is None


def test_unknown_goal_sbatch_outcome_retains_pending_without_retry(submit_stub, monkeypatch):
    data = submit_stub
    spawned = []
    def run(cmd, **kwargs):
        spawned.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="") if cmd[0] == "scp" else (
            SimpleNamespace(returncode=255, stdout="", stderr="synthetic lost connection"))
    monkeypatch.setattr(ops.subprocess, "run", run)
    with pytest.raises(ValueError, match="unresolved"):
        ops.submit(arguments(), data.state, [])
    assert data.state["pending_submission"]["invocation_sha256"] == "e" * 64
    assert data.state["registered_jobs"] == []
    assert len([c for c in spawned if "sbatch" in c[-1]]) == 1
    assert data.writes[-1][1]["pending_submission"] == data.state["pending_submission"]


def test_goal_resume_rechecks_both_original_resume_files_before_writes(submit_stub, monkeypatch):
    data = submit_stub
    data.plan["prior_job_ids"] = ["9001001"]
    data.plan["server_resume_checks"] = [{"arm": "A"}, {"arm": "B"}]
    monkeypatch.setattr(ops.f, "verify_remote_training_progress", lambda *a: data.calls.append("remote_progress"))
    def refuse(checks):
        data.calls.append("remote_resume")
        assert checks == data.plan["server_resume_checks"]
        raise ValueError("synthetic stale resume SHA")
    monkeypatch.setattr(ops.base, "verify_remote_resumes", refuse)
    monkeypatch.setattr(ops.subprocess, "run", lambda *a, **k: pytest.fail("cannot spawn"))
    with pytest.raises(ValueError, match="stale resume"):
        ops.submit(arguments(stage="train"), data.state, [dict(job_id="9001001")])
    assert data.calls == ["capacity", "metadata_sha", "component_sha", "remote_progress", "remote_resume"]
    assert not data.writes

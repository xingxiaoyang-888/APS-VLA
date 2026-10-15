"""Synthetic CPU root scheduling tests; transport is never real SSH/sbatch."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

from cti_vla.evaluation import formal_trials as trials
import test_formal_execution_manifests as fixtures

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    path = ROOT / name
    spec = importlib.util.spec_from_file_location("downstream_test_" + path.stem, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


@pytest.fixture(scope="module", autouse=True)
def unchanged_frozen_sources_and_adapter():
    tool = module("scripts/ops/formal_downstream_supervisor.py")
    inventory = json.loads((ROOT / tool.SOURCE_INVENTORY).read_text(encoding="utf-8"))
    before = {name: tool.digest(ROOT / name) for name in inventory["files"]}
    assert before == inventory["files"] and len(before) == 173
    assert tool.digest(ROOT / tool.ADAPTER) == tool.ADAPTER_SHA256
    yield
    assert before == {name: tool.digest(ROOT / name) for name in before}
    assert tool.digest(ROOT / tool.ADAPTER) == tool.ADAPTER_SHA256


@pytest.fixture
def project(tmp_path, monkeypatch):
    t = module("scripts/ops/formal_downstream_supervisor.py")
    helper = fixtures.load_tool()
    p = fixtures.project.__wrapped__(tmp_path, monkeypatch, helper)
    state = {"registered_jobs": [], "pending_submission": None, "current_round_cost": {"registered_jobs": 0}}
    def save(name, data):
        fixtures.save(helper, tmp_path / name, data)
    for relative in (t.ADAPTER, t.WRAPPER, "scripts/ops/formal_downstream_supervisor.py", "scripts/formal_execution_manifests.py"):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, path)
    # Reuse actual non-weight5000/selection receipt constructors. Only the GPU
    # gate and original173-file source proof are substituted in this fixture;
    # the production source proof is independently exercised below.
    source_info = json.loads((tmp_path / "source_inventory.json").read_text())
    save(t.SOURCE_INVENTORY, source_info)
    p.registration["profiling"] = json.loads((ROOT / t.REGISTRATION).read_text(encoding="utf-8"))["profiling"]
    for index, (suite, spec) in enumerate(p.registration["suites"].items()):
        base = f"results/{t.ROUND}/{suite}/acceptance/attempt01"
        spec.update(protocol=f"configs/manifests/{t.ROUND}/{suite}/protocol.json", windows=f"configs/manifests/{t.ROUND}/{suite}/windows.json",
            model_manifest=f"configs/assets/{suite}.json", model_root_server=str(t.P / "weights" / suite))
        for name in (spec["protocol"], spec["windows"], spec["model_manifest"]):
            save(name, {"synthetic": True, "suite": suite})
        for name in ("input_calls.jsonl", "operator_calls.jsonl", "resume_acceptance.json", "f03_calls.jsonl", "acceptance_complete.json"):
            save(base + "/" + name, {"synthetic_gate": True})
        review_files = {path.name: t.digest(path) for path in (tmp_path / base).iterdir()}
        job_id = str(10 + index)
        save(f"results/{t.ROUND}/{suite}/acceptance/root_review.json", dict(status="passed", job_id=job_id,
            output_relative=base, source_sha256=t.FROZEN_SHA256, files=review_files))
        state["registered_jobs"].append(dict(job_id=job_id, experiment=t.ROUND, mode="acceptance", status="COMPLETED", exit_code="0:0",
            source_sha256=t.FROZEN_SHA256, run_root=str(t.P / base), submitted_utc=f"2000-{index:02d}"))
    for index, pair in enumerate(p.registration["pairs"]):
        directory = helper.pair_directory(helper.Evidence(tmp_path), pair)
        job_id = str(100 + index)
        summary = json.loads((directory / "training_summary.json").read_text())
        summary["job_id"] = job_id
        fixtures.save(helper, directory / "training_summary.json", summary)
        finalize = json.loads((directory / "finalizations/synthetic.json").read_text())
        finalize.update(job_id=job_id, result_sha256=t.digest(directory / "training_summary.json"))
        fixtures.save(helper, directory / "finalizations/synthetic.json", finalize)
        invrel = f"results/{t.ROUND}/invocations/train_{job_id}.json"
        save(invrel, {"synthetic_training_invocation": job_id})
        files = {path.relative_to(tmp_path).as_posix(): t.digest(path) for path in directory.rglob("*.json")}
        # This is the real producer's two-layer shape. Its full evidence map
        # contains a historical mutable state hash; stable files is a subset.
        review = dict(schema=t.ROUND, kind="root_segment_review", status="passed", job_id=job_id,
            completed_by_arm={"A": 5000, "B": 5000}, allowed_next_segment_end=None,
            continuation="formal_training_complete_no_extension", source_sha256=t.FROZEN_SHA256,
            invocation_sha256=t.digest(tmp_path / invrel), files=files,
            evidence_sha256={**files, t.STATE: "f" * 64})
        fixtures.save(helper, directory / "segment_reviews" / (job_id + ".json"), review)
        state["registered_jobs"].append(dict(job_id=job_id, experiment=t.ROUND, mode="train", status="COMPLETED", exit_code="0:0",
            source_sha256=t.FROZEN_SHA256, segment_end=5000, run_root=pair["run_root_server"] + "/training",
            invocation=invrel, invocation_sha256=t.digest(tmp_path / invrel), submitted_utc=f"2001-{index:02d}"))
    save(t.REGISTRATION, p.registration)
    inventory = {**source_info, "source_root_server": str(t.P / "snapshots" / t.FROZEN_NAME), "source_sha256": t.FROZEN_SHA256}
    monkeypatch.setattr(t, "check_source", lambda evidence, helper, source: (inventory, p.sources))
    state["current_round_cost"]["registered_jobs"] = len(state["registered_jobs"])
    args = SimpleNamespace(stage="development", execution_manifest=f"results/{t.ROUND}/execution/dev.json",
        source_inventory=t.SOURCE_INVENTORY, output_relative=None, freeze_directory=None, profile_panel=None,
        prior_review=None, collection_review=None, repair_record=None, resume=False, stop_after=10)
    rows = helper.suite_rows(helper.Evidence(tmp_path), p.registration, "libero_10", p.sources,
        ["dense", "uniform256", "uniform128", "uniform64"])
    save(args.execution_manifest, helper.make_execution(p.registration, "libero_10", rows))
    return SimpleNamespace(**vars(p), scheduler=t, state=state, args=args, save=save, helper=helper)


def make_plan(p):
    return p.scheduler.plan(p.args, p.state, project=p.root, helper=p.helper)


def retained_attempt(p, *, status="COMPLETED", complete=False, unfinished=False):
    """Actual durable-ledger, pull and wrapper shapes; never synthetic weights."""
    t = p.scheduler
    first = make_plan(p)
    invocation, output, job_id = first["invocation"], first["output_relative"], "500"
    p.save(first["invocation_relative"], invocation)
    job = dict(job_id=job_id, name="cti-formal-downstream", experiment=t.ROUND, mode=p.args.stage,
        suite="libero_10", stage_key=invocation["stage_key"], method_ids=invocation["method_ids"],
        source_sha256=t.FROZEN_SHA256, adapter_sha256=t.ADAPTER_SHA256, status=status,
        exit_code="0:0" if status.split()[0].rstrip("+") == "COMPLETED" else "1:0", elapsed_seconds=35, gpus=1,
        run_root=invocation["run_root"], invocation=first["invocation_relative"],
        invocation_sha256=t.digest(p.root / first["invocation_relative"]),
        execution_manifest_sha256=invocation["execution_manifest_sha256"], submitted_utc="2002-01-01")
    p.state["registered_jobs"].append(job)
    manifest = json.loads((p.root / p.args.execution_manifest).read_text())
    spec = p.registration["suites"]["libero_10"]
    panel = json.loads((p.root / spec["initial_states_root"] / "development.json").read_text())
    config = dict(schema=t.ROUND, kind="evaluation_run", manifest=manifest, source_files=p.sources,
        registration_sha256=t.signature(p.registration), policy_watchdog_seconds=60., panel_signature=t.signature(panel))
    p.save(output + "/config.json", config)
    p.save(output + "/panel.json", panel)
    sig = t.signature(config)
    events = [dict(event="invocation", slurm_job_id=job_id, run_signature=sig)]
    identities = [trials._identity(panel, state, mid) for state in panel["states"] for mid in invocation["method_ids"]]
    completed = {}
    for identity in (identities if complete else identities[:1]):
        start = dict(**identity, event="start", run_signature=sig)
        result = dict(**identity, event="result", run_signature=sig, status="completed", success=False, policy_calls=1)
        events.extend((start, result))
        completed[identity["trial_id"]] = result
    if unfinished:
        events.append(dict(**identities[1], event="start", run_signature=sig))
    ledger_path = p.root / output / "trials.jsonl"
    ledger_path.write_bytes("".join(json.dumps(row) + "\n" for row in events).encode())
    ledger = SimpleNamespace(path=ledger_path, events=events, completed=lambda: completed)
    report = trials.summarize_formal_trials(panel, invocation["method_ids"], ledger,
        provenance={"run_signature": sig}, checkpoint_unchanged=True)
    p.save(output + "/closed_loop_report.json", report)
    attempt = job_id + "_" + "a" * 32
    archive = output + "/adapter_invocations/"
    event_name, receipt_name = archive + attempt + ".jsonl", archive + attempt + ".json"
    p.save(event_name, {"synthetic_adapter_journal": True})
    p.save(receipt_name, dict(schema=t.ROUND, kind="formal_evaluation_adapter", job_id=job_id, attempt_id=attempt,
        output=job["run_root"], adapter_sha256=t.ADAPTER_SHA256, frozen_source_sha256=t.FROZEN_SHA256,
        status="returned" if job["exit_code"] == "0:0" else "failed",
        events_path=str(t.P / f"results/{t.ROUND}/adapter_invocations" / (attempt + ".jsonl")),
        events_sha256=t.digest(p.root / event_name)))
    artifacts = [dict(source=str(t.P / f"results/{t.ROUND}/adapter_invocations" / Path(name).name),
        path=str(t.P / name), bytes=(p.root / name).stat().st_size, sha256=t.digest(p.root / name))
        for name in (receipt_name, event_name)]
    receipt = dict(schema=t.ROUND, kind="formal_downstream_job_receipt", job_id=job_id, stage=p.args.stage,
        stage_key=invocation["stage_key"], run_root=job["run_root"], invocation_sha256=job["invocation_sha256"],
        source_sha256=t.FROZEN_SHA256, adapter_sha256=t.ADAPTER_SHA256, adapter_artifacts=artifacts,
        status="returned" if job["exit_code"] == "0:0" else "failed", exit_code=0 if job["exit_code"] == "0:0" else 1)
    p.save(f"results/{t.ROUND}/job_receipts/{job_id}.json", receipt)
    for ext in ("out", "err"):
        p.save(f"results/slurm/{job['name']}_{job_id}.{ext}", {"synthetic_log": ext})
    pull_relative = f"results/{t.ROUND}/pulls/synthetic500/receipt.json"
    review_relative = f"results/{t.ROUND}/downstream_reviews/{job_id}.json"
    review = dict(schema=t.ROUND, kind="root_downstream_review", status="passed", reviewed_by="root", job_id=job_id,
        stage=p.args.stage, stage_key=job["stage_key"], source_sha256=t.FROZEN_SHA256, adapter_sha256=t.ADAPTER_SHA256,
        invocation_sha256=job["invocation_sha256"], run_root=job["run_root"], execution_manifest_sha256=job["execution_manifest_sha256"],
        terminal_status=status.split()[0].rstrip("+"), exit_code=job["exit_code"], scientific_complete=complete,
        pull_receipt=pull_relative, run_signature=sig, completed_trials=len(completed),
        unfinished_attempts_unknown_cost=int(unfinished))
    result = SimpleNamespace(first=first, job=job, output=output, ledger=ledger_path, review=review,
        review_relative=review_relative, pull_relative=pull_relative, receipt_name=receipt_name)
    repull_attempt(p, result)
    p.args.prior_review = review_relative
    return result


def repull_attempt(p, attempt):
    """Explicitly re-create synthetic immutable transfer evidence after mutations."""
    t, job = p.scheduler, attempt.job
    names = [path.relative_to(p.root).as_posix() for path in (p.root / attempt.output).rglob("*") if path.is_file()]
    names.extend([f"results/{t.ROUND}/job_receipts/{job['job_id']}.json",
        *[f"results/slurm/{job['name']}_{job['job_id']}.{ext}" for ext in ("out", "err")]])
    rows = [dict(relative=name, path=str(t.P / name), bytes=(p.root / name).stat().st_size,
        sha256=t.digest(p.root / name), job_ids=[job["job_id"]]) for name in sorted(names)]
    inventory = dict(files=rows)
    directory = str(Path(attempt.pull_relative).parent).replace("\\", "/")
    for name in ("inventory_before.json", "inventory_after.json"):
        p.save(directory + "/" + name, inventory)
    accounting = {**job, "status": job["status"].split()[0].rstrip("+")}
    pull = dict(schema=t.ROUND, kind="nonweight_pull", status="verified_nonweight_snapshot", final_evidence=True,
        weights_copied=False, sealed_initial_states_copied=False, selected_jobs=[{**job, "include_run_root": True}],
        accounting_before={"jobs": {job["job_id"]: accounting}}, accounting_after={"jobs": {job["job_id"]: accounting}},
        files=[{**row, "action": "downloaded_verified"} for row in rows],
        inventory_sha256=t.digest(p.root / directory / "inventory_before.json"))
    p.save(attempt.pull_relative, pull)
    attempt.review["files"] = {row["relative"]: row["sha256"] for row in rows}
    p.save(attempt.review_relative, attempt.review)


def repair_attempt(p, attempt):
    t = p.scheduler
    p.args.repair_record = f"results/{t.ROUND}/repairs/synthetic500.json"
    p.save(p.args.repair_record, dict(schema=t.ROUND, kind="downstream_repair", status="reviewed", reviewed_by="root",
        stage_key=attempt.job["stage_key"], target_source_sha256=t.FROZEN_SHA256, adapter_sha256=t.ADAPTER_SHA256,
        execution_manifest_sha256=attempt.job["execution_manifest_sha256"],
        prior_review_sha256=t.digest(p.root / attempt.review_relative), failed_job_ids=[attempt.job["job_id"]],
        diagnosis="Synthetic infrastructure interruption with complete retained JSON ledger",
        bounded_fix="Resume the same registered incomplete trials with unchanged scientific inputs"))


def freeze_project(p):
    """Existing production freezer on synthetic72 receipts and8800 dev trials."""
    import hashlib
    t = p.scheduler
    info = json.loads((p.root / "source_inventory.json").read_text())
    info["files"][t.REGISTRATION] = t.digest(p.root / t.REGISTRATION)
    info["source_sha256"] = hashlib.sha256(json.dumps(info["files"], sort_keys=True).encode()).hexdigest()
    p.save("source_inventory.json", info)
    inventory = json.loads((p.root / "checkpoint_inventory.json").read_text())
    inventory.update(registration_sha256=t.signature(p.registration), registration_file_sha256=t.digest(p.root / t.REGISTRATION),
        source_inventory_file_sha256=t.digest(p.root / "source_inventory.json"), source_sha256=info["source_sha256"])
    p.save("checkpoint_inventory.json", inventory)
    fixtures.write_development_runs(p)
    directory = f"results/{t.ROUND}/global_freeze/synthetic"
    p.helper.build_global(p.helper.Evidence(p.root), p.registration, p.sources, "development_index.json", directory,
        checkpoint_inventory="checkpoint_inventory.json")
    p.helper.release_global(p.helper.Evidence(p.root), p.registration, directory, release=True, created_utc="synthetic-root-time")
    return directory


def test_development_first_plan_is_read_only_and_binds_adapter_environment(project, monkeypatch):
    p, t = project, project.scheduler
    before = {x.relative_to(p.root).as_posix(): t.digest(x) for x in p.root.rglob("*") if x.is_file()}
    def forbidden(*a, **kw):
        raise AssertionError("Pure plan cannot call network or submit a job")
    monkeypatch.setattr(t.subprocess, "run", forbidden)
    value = make_plan(p)
    assert value["invocation"]["method_ids"] == ["dense", "uniform256", "uniform128", "uniform64"]
    assert value["invocation"]["argv"][0] == "evaluate"
    assert "--resume" not in value["invocation"]["argv"]
    assert value["invocation"]["adapter_sha256"] == t.ADAPTER_SHA256
    assert value["invocation"]["final_values_read_locally"] is False
    assert value["invocation"]["scientific_settings_changed"] is False
    assert before == {x.relative_to(p.root).as_posix(): t.digest(x) for x in p.root.rglob("*") if x.is_file()}
    command = t.submission_command(value, "1" * 64)
    assert "--no-requeue" in command and "CUDA_VISIBLE_DEVICES" not in command
    assert "TF_NUM_INTEROP_THREADS=1" in command and "--invocation-sha256" in command


def test_real173_source_guard_and_adapter_remain_compatible():
    t = module("scripts/ops/formal_downstream_supervisor.py")
    helper = fixtures.load_tool()
    inventory, sources = t.check_source(helper.Evidence(ROOT), helper, t.SOURCE_INVENTORY)
    assert len(inventory["files"]) == 173 and sources


@pytest.mark.parametrize("status", ["SUBMITTED", "RUNNING", "PENDING", "UNKNOWN"])
def test_active_and_unknown_stage_prevent_duplicate(project, status):
    p, t = project, project.scheduler
    first = make_plan(p)
    inv = first["invocation"]
    p.state["registered_jobs"].append(dict(job_id="500", experiment=t.ROUND, mode="development", suite="libero_10",
        stage_key=inv["stage_key"], method_ids=inv["method_ids"], status=status, run_root=inv["run_root"]))
    with pytest.raises(ValueError, match="active or unresolved"):
        make_plan(p)


def test_overlapping_method_groups_cannot_create_duplicate_trials(project):
    p, t = project, project.scheduler
    p.state["registered_jobs"].append(dict(job_id="500", experiment=t.ROUND, mode="development", suite="libero_10",
        stage_key="different_group", method_ids=["dense"], status="COMPLETED"))
    with pytest.raises(ValueError, match="overlaps"):
        make_plan(p)


def test_pending_submission_blocks_planning_without_refresh(project):
    project.state["pending_submission"] = {"stage_key": "prior_unknown"}
    with pytest.raises(ValueError, match="Unresolved submission"):
        make_plan(project)


@pytest.mark.parametrize("mutation", ["partial", "wrong_checkpoint", "wrong_environment", "final_split"])
def test_incomplete_selector_and_manifest_identity_never_reach_plan(project, mutation):
    p, t = project, project.scheduler
    methods = ["A128_seed17", "B128_seed17"]
    rows = p.helper.suite_rows(p.helper.Evidence(p.root), p.registration, "libero_10", p.sources, methods)
    manifest = p.helper.make_execution(p.registration, "libero_10", rows)
    if mutation == "partial":
        path = p.root / "results/formal_main_v2/libero_10/k128/seed17/training/A/deployment_receipt.json"
        receipt = json.loads(path.read_text())
        receipt["completed_updates"] = 500
        fixtures.save(p.helper, path, receipt)
    elif mutation == "wrong_checkpoint":
        manifest["methods"][0]["checkpoint"] = str(t.H / "checkpoints/formal_main_v2/other/A/best.pt")
    elif mutation == "wrong_environment":
        manifest["environment"]["wait_steps"] = 1
    else:
        manifest["split"] = "final"
    p.save(p.args.execution_manifest, manifest)
    with pytest.raises(ValueError):
        make_plan(p)


def test_completed_selector_uses_real_review_fields_without_freezing_current_state(project):
    p = project
    rows = p.helper.suite_rows(p.helper.Evidence(p.root), p.registration, "libero_10", p.sources, ["A128_seed17", "B128_seed17"])
    p.save(p.args.execution_manifest, p.helper.make_execution(p.registration, "libero_10", rows))
    p.save(p.scheduler.STATE, {"changed_after_historical_review": True})
    value = make_plan(p)
    assert value["invocation"]["method_ids"] == ["A128_seed17", "B128_seed17"]
    assert p.scheduler.STATE not in value["invocation"]["root_evidence_sha256"]


def test_final_without_global_release_fails_before_any_final_value_access(project, monkeypatch):
    p = project
    manifest = json.loads((p.root / p.args.execution_manifest).read_text())
    manifest["split"] = "final"
    p.save(p.args.execution_manifest, manifest)
    p.args.stage = "final"
    original = Path.open
    touched = []
    def protected(path, *a, **kw):
        if "sealed_final" in path.name:
            touched.append(path)
            raise AssertionError("No sealed values may be accessed")
        return original(path, *a, **kw)
    monkeypatch.setattr(Path, "open", protected)
    with pytest.raises(ValueError):
        make_plan(p)
    assert touched == []


def test_complete_final_plan_uses_actual_global_release_without_reading_sealed_values(project, monkeypatch):
    p, t = project, project.scheduler
    opened = []
    original = Path.open
    def protected(path, *a, **kw):
        if "sealed" in path.name or path.suffix in t.FORBIDDEN:
            opened.append(path)
            raise AssertionError("Local final plan may not read sealed or checkpoint bytes")
        return original(path, *a, **kw)
    monkeypatch.setattr(Path, "open", protected)
    directory = freeze_project(p)
    p.args.stage, p.args.freeze_directory = "final", directory
    p.args.execution_manifest = directory + "/final_execution/libero_10.json"
    value = make_plan(p)
    inv = value["invocation"]
    assert len(inv["method_ids"]) == 22 and inv["argv"][0] == "evaluate"
    assert "--development-panel" not in inv["argv"]
    assert inv["argv"][inv["argv"].index("--sealed-final") + 1] == str(t.P / p.registration["suites"]["libero_10"]["initial_states_root"] / "sealed_final.json")
    assert inv["argv"][inv["argv"].index("--release-sha256") + 1] == t.digest(p.root / directory / "root_release.json")
    assert not any("sealed" in name for name in inv["root_evidence_sha256"])
    assert inv["final_values_read_locally"] is False and opened == []


@pytest.mark.parametrize("stage", ["full", "components"])
def test_valid_timing_plan_binds_complete_freeze_and_audited_raw_development_panel(project, stage):
    from cti_vla.evaluation import formal_profiling as profiling
    from cti_vla.evaluation.libero_runtime import run_episode
    from test_formal_profiling import FakeEnv, dense
    p, t = project, project.scheduler
    directory = freeze_project(p)
    p.args.stage, p.args.stop_after = "collect", None
    rows = p.helper.suite_rows(p.helper.Evidence(p.root), p.registration, "libero_10", p.sources, ["dense"])
    p.save(p.args.execution_manifest, p.helper.make_execution(p.registration, "libero_10", rows))
    attempt = retained_attempt(p, complete=True)
    # Replace the rollout-only fixture files with the real collector's signed
    # trajectory/raw-observation producer. No simulator or model is imported.
    for name in ("config.json", "panel.json", "trials.jsonl", "closed_loop_report.json"):
        (p.root / attempt.output / name).unlink()
    dev = json.loads((p.root / p.registration["suites"]["libero_10"]["initial_states_root"] / "development.json").read_text())
    provenance = dict(dense_identity=rows[0]["identity"], checkpoint_unchanged=True)
    episodes = []
    for state in profiling.fixed_profile_states(dev):
        capture = profiling.CaptureControlObservations(FakeEnv())
        result = run_episode(capture, dense, "synthetic instruction", state["initial_state"], max_steps=520)
        episodes.append(profiling.save_dense_collection(p.root / attempt.output / f"task{state['task_id']:02d}", state,
            "synthetic instruction", result, capture.captured, provenance=provenance))
    profiling.write_profile_panel(p.root / attempt.output, dev, episodes, provenance=provenance, registration=p.registration)
    for key in ("run_signature", "completed_trials", "unfinished_attempts_unknown_cost"):
        attempt.review.pop(key)
    repull_attempt(p, attempt)
    p.args.stage, p.args.freeze_directory = stage, directory
    p.args.collection_review, p.args.prior_review = attempt.review_relative, None
    p.args.profile_panel = attempt.output + "/panel.json"
    p.args.execution_manifest = f"results/{t.ROUND}/execution/all22_for_timing.json"
    methods = p.helper.suite_rows(p.helper.Evidence(p.root), p.registration, "libero_10", p.sources, trials.expected_method_ids())
    p.save(p.args.execution_manifest, p.helper.make_execution(p.registration, "libero_10", methods))
    value = make_plan(p)
    inv = value["invocation"]
    assert inv["argv"][0] == stage and len(inv["method_ids"]) == 22
    assert "--uncontended-gpu" in inv["argv"] and "--resume" not in inv["argv"]
    assert len([name for name in inv["watched_files"] if name.endswith(".npz")]) == 30
    assert inv["argv"][inv["argv"].index("--panel") + 1] == str(t.P / p.args.profile_panel)


def test_caller_metadata_cannot_be_a_sealed_path(project):
    p = project
    p.args.execution_manifest = "configs/manifests/formal_main_v2/libero_10/initial_states/sealed_final.json"
    with pytest.raises(ValueError, match="sealed values"):
        make_plan(p)


def test_dense_collection_preserves_own_mode_and_cannot_reuse_panel(project):
    p = project
    p.args.stage, p.args.stop_after = "collect", None
    rows = p.helper.suite_rows(p.helper.Evidence(p.root), p.registration, "libero_10", p.sources, ["dense"])
    p.save(p.args.execution_manifest, p.helper.make_execution(p.registration, "libero_10", rows))
    value = make_plan(p)
    assert value["invocation"]["argv"][0] == "collect" and "--uncontended-gpu" in value["invocation"]["argv"]
    p.args.profile_panel = "results/formal_main_v2/old/panel.json"
    with pytest.raises(ValueError, match="substitute"):
        make_plan(p)


def fake_supervisor(p):
    tool = module("scripts/formal_supervisor.py")
    tool.ROOT, tool.STATE = p.root, p.root / p.scheduler.STATE
    return tool


@pytest.mark.parametrize("outcome", ["ambiguous", "transport_error", "confirmed"])
def test_submission_is_exactly_once_and_unknown_outcomes_retain_pending(project, outcome):
    p, t = project, project.scheduler
    value = make_plan(p)
    calls = []
    class Transport:
        def prepare(self, plan, path):
            calls.append("prepare")
            assert path.is_file()
        def submit(self, command):
            calls.append("submit")
            if outcome == "transport_error":
                raise TimeoutError("synthetic unknown SSH outcome")
            return SimpleNamespace(returncode=0, stdout="5000\n" if outcome == "confirmed" else "5000\nunexpected extra reply\n")
    supervisor = fake_supervisor(p)
    if outcome == "confirmed":
        result = t.submit_plan(value, p.state, project=p.root, supervisor=supervisor, transport=Transport(), expected_plan_sha256=value["plan_sha256"])
        assert result["job_id"] == "5000" and p.state["pending_submission"] is None
        assert p.state["registered_jobs"][-1]["mode"] == "development"
        assert p.state["current_round_cost"]["registered_jobs"] == len(p.state["registered_jobs"])
        with pytest.raises(ValueError, match="already exists"):
            t.submit_plan(value, p.state, project=p.root, supervisor=supervisor, transport=Transport(), expected_plan_sha256=value["plan_sha256"])
    else:
        with pytest.raises((RuntimeError, TimeoutError)):
            t.submit_plan(value, p.state, project=p.root, supervisor=supervisor, transport=Transport(), expected_plan_sha256=value["plan_sha256"])
        assert p.state["pending_submission"]["phase"] == "sbatch_outcome_pending"
        saved = json.loads(supervisor.STATE.read_text(encoding="utf-8"))
        assert saved["pending_submission"] == p.state["pending_submission"]
        with pytest.raises(ValueError, match="Unresolved submission"):
            make_plan(p)
    assert calls == ["prepare", "submit"]


def test_unreviewed_or_changed_plan_never_reaches_transport(project):
    p, t = project, project.scheduler
    value = make_plan(p)
    class NoTransport:
        def prepare(self, *a):
            raise AssertionError("Changed plan cannot reach remote")
    with pytest.raises(ValueError, match="changed reviewed plan"):
        t.submit_plan(value, p.state, project=p.root, supervisor=fake_supervisor(p), transport=NoTransport(), expected_plan_sha256="0" * 64)
    assert not (p.root / value["invocation_relative"]).exists()


def test_existing_output_and_new_resume_flag_are_not_guessed(project):
    p = project
    value = make_plan(p)
    (p.root / value["output_relative"]).mkdir(parents=True)
    with pytest.raises(ValueError, match="existence"):
        make_plan(p)
    p.args.resume = True
    with pytest.raises(ValueError, match="No registered prior"):
        make_plan(p)


def test_explicit_resume_binds_raw_prefix_and_does_not_rewrite_terminal_trial(project):
    p = project
    attempt = retained_attempt(p)
    before = attempt.ledger.read_bytes()
    p.args.resume = True
    value = make_plan(p)
    assert value["output_relative"] == attempt.output
    assert value["invocation"]["prior_job_ids"] == ["500"]
    assert "--resume" in value["invocation"]["argv"]
    assert value["invocation"]["watched_files"][str(p.scheduler.P / attempt.output / "trials.jsonl")] == p.scheduler.digest(attempt.ledger)
    assert attempt.ledger.read_bytes() == before


@pytest.mark.parametrize("status", ["FAILED", "CANCELLED by 15016", "TIMEOUT+"])
def test_failed_resume_requires_repair_and_retains_unknown_attempt_cost(project, status):
    p = project
    attempt = retained_attempt(p, status=status, unfinished=True)
    p.args.resume = True
    before = attempt.ledger.read_bytes()
    with pytest.raises(ValueError, match="repair record"):
        make_plan(p)
    repair_attempt(p, attempt)
    value = make_plan(p)
    cost = value["invocation"]["prior_allocation_cost"][0]
    assert cost["raw_status"] == status and cost["elapsed_seconds"] == 35
    assert cost["status"] == status.split()[0].rstrip("+")
    assert p.state["registered_jobs"][-1]["status"] == status
    assert attempt.ledger.read_bytes() == before


@pytest.mark.parametrize("change", ["no_resume", "complete", "manifest", "ledger", "no_lf", "missing_ledger", "pull_sha", "omitted_pulled_file", "wrong_job_receipt", "unknown_cost"])
def test_resume_rejects_missing_mismatched_or_completed_evidence(project, change):
    p, t = project, project.scheduler
    attempt = retained_attempt(p, complete=change == "complete")
    p.args.resume = change != "no_resume"
    if change == "manifest":
        config = json.loads((p.root / attempt.output / "config.json").read_text())
        config["policy_watchdog_seconds"] = 1.
        p.save(attempt.output + "/config.json", config)
        repull_attempt(p, attempt)
    elif change == "ledger":
        attempt.ledger.write_bytes(attempt.ledger.read_bytes().replace(b'"run_signature": "', b'"run_signature": "bad'))
        repull_attempt(p, attempt)
    elif change == "no_lf":
        attempt.ledger.write_bytes(attempt.ledger.read_bytes().rstrip(b"\n"))
        repull_attempt(p, attempt)
    elif change == "missing_ledger":
        attempt.ledger.unlink()
        repull_attempt(p, attempt)
    elif change == "pull_sha":
        attempt.ledger.write_bytes(attempt.ledger.read_bytes() + b"\n")
    elif change == "omitted_pulled_file":
        pull = json.loads((p.root / attempt.pull_relative).read_text())
        pull["files"] = [r for r in pull["files"] if not r["relative"].endswith("trials.jsonl")]
        p.save(attempt.pull_relative, pull)
    elif change == "wrong_job_receipt":
        name = f"results/{t.ROUND}/job_receipts/500.json"
        receipt = json.loads((p.root / name).read_text())
        receipt["invocation_sha256"] = "0" * 64
        p.save(name, receipt)
        repull_attempt(p, attempt)
    elif change == "unknown_cost":
        attempt.review["unfinished_attempts_unknown_cost"] = 1
        repull_attempt(p, attempt)
    before = attempt.ledger.read_bytes() if attempt.ledger.exists() else None
    with pytest.raises((ValueError, FileNotFoundError)):
        make_plan(p)
    assert (attempt.ledger.read_bytes() if attempt.ledger.exists() else None) == before


def test_new_profile_attempt_requires_failed_evidence_and_a_fresh_output(project):
    p = project
    p.args.stage, p.args.stop_after = "collect", None
    rows = p.helper.suite_rows(p.helper.Evidence(p.root), p.registration, "libero_10", p.sources, ["dense"])
    p.save(p.args.execution_manifest, p.helper.make_execution(p.registration, "libero_10", rows))
    attempt = retained_attempt(p, status="FAILED")
    repair_attempt(p, attempt)
    value = make_plan(p)
    assert value["output_relative"] != attempt.output and value["output_relative"].endswith("attempt02")
    assert value["invocation"]["prior_job_ids"] == ["500"]
    p.args.output_relative = attempt.output
    with pytest.raises(ValueError, match="fresh directories"):
        make_plan(p)


def test_wrapper_archives_exact_current_job_bytes_only(tmp_path):
    wrapper = module("scripts/server/run_formal_downstream.py")
    job = "555"
    current = job + "_" + "a" * 32
    directory = tmp_path / "results/formal_main_v2/adapter_invocations"
    directory.mkdir(parents=True)
    output = tmp_path / "results/formal_main_v2/libero_10/downstream/development/run"
    journal = directory / (current + ".jsonl")
    journal.write_bytes(b'{"synthetic_failed_event": true}\n')
    receipt = dict(job_id=job, attempt_id=current, output=str(output), adapter_sha256=wrapper.ADAPTER_SHA,
        frozen_source_sha256=wrapper.FROZEN_SHA, events_path=str(journal), events_sha256=wrapper.sha(journal), status="failed")
    (directory / (current + ".json")).write_text(json.dumps(receipt), encoding="utf-8")
    (directory / ("556_" + "b" * 32 + ".json")).write_bytes(b"OTHER JOB MUST NOT BE COPIED")
    (directory / (job + "_" + "c" * 32 + ".jsonl")).write_bytes(b'{"unfinished":')
    artifacts, receipts = wrapper.archive_adapter_evidence(root=tmp_path, output=output, job_id=job, invocation={"run_root": str(output)})
    assert len(artifacts) == 3 and len(receipts) == 1 and receipts[0]["status"] == "failed"
    assert len(list((output / "adapter_invocations").iterdir())) == 3
    for row in artifacts:
        assert Path(row["source"]).read_bytes() == Path(row["path"]).read_bytes()


def test_wrapper_rejects_unapproved_entrypoint_and_duplicate_flags(project):
    p = project
    wrapper = module("scripts/server/run_formal_downstream.py")
    invocation = make_plan(p)["invocation"]
    wrapper.validate_shape(invocation)
    changed = deepcopy(invocation)
    changed["entrypoint"] = "scripts/eval_formal_selector_libero.py"
    with pytest.raises(ValueError):
        wrapper.validate_shape(changed)
    changed = deepcopy(invocation)
    changed["argv"].extend(["--output", "malicious_replacement"])
    with pytest.raises(ValueError, match="Duplicate"):
        wrapper.validate_shape(changed)


def test_remote_metadata_request_uses_stdin_not_windows_command_line(monkeypatch):
    tool = module("scripts/ops/formal_downstream_supervisor.py")
    sent = []
    def fake(args, **kwargs):
        sent.append((args, kwargs))
        return SimpleNamespace(stdout="[]\n")
    monkeypatch.setattr(tool.subprocess, "run", fake)
    script = "#173 frozen paths plus hashes\n" + "#" * 90000
    assert tool.Transport(ROOT).remote(script) == "[]\n"
    args, kwargs = sent[0]
    assert len(" ".join(args)) < 1000 and kwargs["input"] == script
    assert kwargs["check"] is True and kwargs["text"] is True

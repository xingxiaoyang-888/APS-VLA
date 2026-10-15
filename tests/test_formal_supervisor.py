"""Submission/accounting failure boundaries; no SSH or real jobs are invoked."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def coordinator(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts/formal_supervisor.py"
    spec = importlib.util.spec_from_file_location("formal_coordinator_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setattr(mod, "STATE", tmp_path / "results/state.json")
    return mod


def test_accounting_only_registered_ids_and_includes_failed_allocations(coordinator, monkeypatch):
    m = coordinator
    state = {"registered_jobs": [
        {"job_id": "100", "experiment": "formal_main_v2"},
        {"job_id": "101", "experiment": "formal_main_v2"},
        {"job_id": "999", "experiment": "historical"}], "current_round_cost": {}}
    calls = []
    def remote(command):
        calls.append(command)
        return "100|FAILED|1:0|50|cpu=7,gres/gpu=1|gpu1\n101|COMPLETED|0:0|90|cpu=4|cpu1\n"
    monkeypatch.setattr(m, "remote", remote)
    m.refresh(state)
    assert "-j 100,101 " in calls[0] and "999" not in calls[0]
    assert state["current_round_cost"]["allocated_gpu_seconds"] == 50
    assert state["registered_jobs"][0]["status"] == "FAILED"


def test_incomplete_accounting_never_implies_completion(coordinator, monkeypatch):
    m = coordinator
    state = {"registered_jobs": [{"job_id": "100", "experiment": "formal_main_v2"}], "current_round_cost": {}}
    monkeypatch.setattr(m, "remote", lambda _: "")
    with pytest.raises(ValueError, match="Accounting incomplete"):
        m.refresh(state)
    assert not m.STATE.exists()


def test_state_lock_rejects_second_writer(coordinator):
    with coordinator.supervisor_lock():
        with pytest.raises(OSError):
            with coordinator.supervisor_lock():
                pytest.fail("Concurrent writer entered")


@pytest.fixture
def training_request(coordinator, monkeypatch):
    m = coordinator
    suite = "libero_10"
    protocol, windows, asset, config = "protocol.json", "windows.json", "asset.json", "config.json"
    for rel in (protocol, windows, asset, config):
        m.write(m.ROOT / rel, {"fixture": rel})
    source = m.P + "/snapshots/formal_main_v2_test"
    inventory = m.ROOT / "inventory.json"
    m.write(inventory, {"source_root_server": source, "source_sha256": "source-sha", "files": {}})
    pair = {"suite": suite, "visual_tokens": 128, "seed": 17, "path": config,
            "checkpoint_root_server": m.H + "/checkpoints/formal_main_v2/test"}
    registration = {"suites": {suite: {"protocol": protocol, "windows": windows, "model_manifest": asset,
        "model_root_server": m.H + "/models/test", "data_root_server": m.H + "/data/test",
        "cache_root_server": m.H + "/data/formal_main_v2/" + suite}}, "pairs": [pair]}
    m.write(m.ROOT / "configs/experiments/formal_main_v2.json", registration)
    gatebase = "results/formal_main_v2/libero_10/acceptance/attempt01"
    names = ("input_acceptance.json", "f01_k128.json", "resume_acceptance.json", "f03_calls.jsonl", "acceptance_complete.json")
    for filename in names:
        m.write(m.ROOT / gatebase / filename, {"fixture": filename})
    m.write(m.ROOT / "results/formal_main_v2/libero_10/acceptance/root_review.json",
        {"status": "passed", "job_id": "100", "output_relative": gatebase,
         "files": {name: m.sha(m.ROOT / gatebase / name) for name in names}})
    accepted = {"job_id": "100", "experiment": "formal_main_v2", "status": "COMPLETED", "exit_code": "0:0"}
    state = {"registered_jobs": [accepted], "current_round_cost": {"registered_jobs": 1}}
    args = SimpleNamespace(stage="train", suite=suite, source_inventory=inventory, budget=128,
        seed=17, segment=500, wall_seconds=12600, resume=False, repair_record=None)
    monkeypatch.setattr(m, "remote", lambda _: "")
    calls = []
    def run(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stdout="101\n" if argv[0] == "ssh" else "", stderr="")
    monkeypatch.setattr(m.subprocess, "run", run)
    return m, args, state, calls


def test_unknown_submission_keeps_pending_receipt(training_request, monkeypatch):
    m, args, state, calls = training_request
    monkeypatch.setattr(m.subprocess, "run", lambda argv, **kw: SimpleNamespace(returncode=0, stdout="", stderr=""))
    with pytest.raises(RuntimeError, match="unresolved"):
        m.submit(args, state, state["registered_jobs"])
    saved = m.read(m.STATE)
    assert saved["pending_submission"]["stage_key"] == "libero_10_train_k128_seed17"
    assert len(saved["registered_jobs"]) == 1
    with pytest.raises(ValueError, match="Unresolved submission"):
        m.submit(args, saved, saved["registered_jobs"])


def test_confirmed_submission_registers_exactly_once_and_watches_resume_gate(training_request):
    m, args, state, calls = training_request
    m.submit(args, state, state["registered_jobs"])
    saved = m.read(m.STATE)
    assert saved["pending_submission"] is None
    assert [j["job_id"] for j in saved["registered_jobs"]] == ["100", "101"]
    invocation = m.read(m.ROOT / saved["registered_jobs"][-1]["invocation"])
    assert any(path.endswith("resume_acceptance.json") for path in invocation["watched_files"])
    assert any(path.endswith("f03_calls.jsonl") for path in invocation["watched_files"])


def test_completed_report_takes_precedence_over_stale_progress(training_request):
    m, args, state, calls = training_request
    base = m.ROOT / "results/formal_main_v2/libero_10/k128/seed17/training"
    for arm in ("A", "B"):
        m.write(base / arm / "progress_report.json", {"training_updates_completed": 4500})
        m.write(base / arm / "training_report.json", {"training_updates_completed": 5000})
    args.segment = 5000
    with pytest.raises(ValueError, match="already completed"):
        m.submit(args, state, state["registered_jobs"])
    assert calls == []


def test_partially_completed_pair_can_resume_same_segment(training_request):
    m, args, state, calls = training_request
    base = m.ROOT / "results/formal_main_v2/libero_10/k128/seed17/training"
    for arm, n in (("A", 500), ("B", 200)):
        m.write(base / arm / "progress_report.json", {"training_updates_completed": n})
    m.write(base / "registered_config.json", {"fixture": True})
    found={p.relative_to(base).as_posix():m.sha(p) for p in base.rglob('*.json')}
    m.remote=lambda command: json.dumps(found) if ' -c ' in command else ''
    previous = {"job_id": "99", "experiment": "formal_main_v2", "status": "COMPLETED",
                "stage_key": "libero_10_train_k128_seed17"}
    state["registered_jobs"].append(previous)
    args.resume = True
    m.submit(args, state, state["registered_jobs"])
    invocation = m.read(m.ROOT / state["registered_jobs"][-1]["invocation"])
    assert "--resume" in invocation["argv"]


def test_missing_local_results_cannot_repeat_completed_remote_segment(training_request):
    m, args, state, calls = training_request
    previous={"job_id":"99","experiment":"formal_main_v2","status":"COMPLETED",
              "stage_key":"libero_10_train_k128_seed17","segment_end":500}
    state["registered_jobs"].append(previous)
    args.resume=True
    m.remote=lambda command: json.dumps({'registered_config.json':'remote-registration-sha',
        'A/progress_report.json':'remote-A500-sha','B/progress_report.json':'remote-B500-sha'})
    with pytest.raises(ValueError,match='Pull and verify latest remote'):
        m.submit(args,state,state["registered_jobs"])
    assert calls==[]


def test_repair_receipt_cannot_authorize_another_stage(training_request):
    m, args, state, calls = training_request
    state["registered_jobs"].append({"job_id": "99", "status": "FAILED", "stage_key": "libero_10_train_k128_seed17"})
    args.repair_record = m.ROOT / "repair.json"
    m.write(args.repair_record, {"status": "reviewed", "stage_key": "libero_spatial_train_k128_seed17",
        "failed_job_ids": ["99"], "target_source_sha256": "source-sha", "segment_end": 500})
    with pytest.raises(ValueError, match="Repair must bind"):
        m.submit(args, state, state["registered_jobs"])
    assert calls == []

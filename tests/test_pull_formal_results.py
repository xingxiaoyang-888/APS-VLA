"""Read-only transfer boundary tests; no SSH, Slurm allocation or large weights."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


@pytest.fixture
def puller(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts/pull_formal_results.py"
    spec = importlib.util.spec_from_file_location("formal_puller_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "STATE", tmp_path / "results/supervisor/state.json")
    return module


def job(m, number="101", root="long/train"):
    return {"job_id": number, "name": "cti-formal", "experiment": "formal_main_v2", "mode": "train",
            "run_root": m.P + "/results/formal_main_v2/" + root, "source_sha256": "a" * 64}


def account(jobs, **states):
    return {"raw": "synthetic accounting", "jobs": {row["job_id"]: {"status": states.get(row["job_id"], "COMPLETED"),
        "exit_code": "0:0", "elapsed_seconds": 10} for row in jobs}}


def entry(m, payload=b'{"status":"passed"}\n', *, rel="results/formal_main_v2/long/train/summary.json", kind="run_root"):
    return {"path": m.P + "/" + rel, "relative": rel, "kind": kind, "job_ids": ["101"], "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(), "mtime_ns": 1, "ctime_ns": 1, "device": 1, "inode": 1}


def fake_transfer(m, monkeypatch, *, payload=b'{"status":"passed"}\n'):
    jobs = [job(m)]
    m.atomic_json(m.STATE, {"registered_jobs": jobs})
    row = entry(m, payload)
    calls = []
    monkeypatch.setattr(m, "query_accounting", lambda registered, timeout: account(registered))
    inventory = {"files": [row], "excluded": [], "missing": []}
    monkeypatch.setattr(m, "remote_inventory", lambda *args: copy.deepcopy(inventory))
    def download(row, target, timeout):
        calls.append(row["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    monkeypatch.setattr(m, "download_file", download)
    return row, calls, inventory


def test_only_registered_formal_ids_are_queried(puller, monkeypatch):
    m = puller
    registered = m.registered_jobs({"registered_jobs": [job(m), dict(job(m, "999"), experiment="other_project")]})
    calls = []
    def run(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(stdout="101|FAILED|1:0|32|gres/gpu=1|node\n")
    monkeypatch.setattr(m.subprocess, "run", run)
    result = m.query_accounting(registered, 10)
    assert "-j 101 " in calls[0][-1] and "999" not in calls[0][-1]
    assert result["jobs"]["101"]["status"] == "FAILED"
    with pytest.raises(ValueError, match="not registered"):
        m.build_request(registered, result, {"999"})
    monkeypatch.setattr(m.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout=""))
    with pytest.raises(ValueError, match="incomplete"):
        m.query_accounting(registered, 10)


@pytest.mark.parametrize("root", ["/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/test",
    "/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/results/formal_main_v2",
    "/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/results/formal_main_v2/../other"])
def test_registration_cannot_expand_remote_scope(puller, root):
    row = job(puller)
    row["run_root"] = root
    with pytest.raises(ValueError, match="run_root"):
        puller.registered_jobs({"registered_jobs": [row]})


@pytest.mark.parametrize("root", ["weights", "sealed_final", "initial_states/long"])
def test_registered_root_itself_cannot_be_weight_or_state_directory(puller, root):
    with pytest.raises(ValueError, match="weights or sealed"):
        puller.registered_jobs({"registered_jobs": [job(puller, root=root)]})


@pytest.mark.parametrize("raw", ["101||0:0|3||node\n", "101|COMPLETED|0:0|-1||node\n",
    "101|COMPLETED|bad|3||node\n", "101|COMPLETED|0:0|3||node\n101|COMPLETED|0:0|3||node\n"])
def test_invalid_or_duplicate_slurm_bill_not_accepted(puller, monkeypatch, raw):
    monkeypatch.setattr(puller.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout=raw))
    with pytest.raises(ValueError):
        puller.query_accounting([job(puller)], 10)


def test_running_shared_or_nested_output_never_finalized(puller):
    m = puller
    jobs = [job(m), job(m, "102", "long/train"), job(m, "103", "other")]
    request, skipped = m.build_request(jobs, account(jobs, **{"102": "RUNNING"}), set())
    assert [x["job_id"] for x in request["jobs"]] == ["101", "103"]
    assert request["jobs"][0]["include_run_root"] is False
    assert request["jobs"][0]["active_overlapping_job_ids"] == ["102"]
    assert skipped == [{"job_id": "102", "reason": "job_not_terminal"}]
    assert m.overlapping(m.P + "/data", m.P + "/data/child")
    assert not m.overlapping(m.P + "/data", m.P + "/database")


def test_atomic_pull_skips_same_sha_and_preserves_previous_version(puller, monkeypatch):
    m = puller
    row, calls, inventory = fake_transfer(m, monkeypatch)
    target = m.ROOT / row["relative"]
    target.parent.mkdir(parents=True)
    target.write_text("previous evidence", encoding="utf-8")
    state_before = m.STATE.read_bytes()
    result, receipt = m.pull()
    assert result["status"] == "verified_nonweight_snapshot" and result["final_evidence"] is True
    assert result["scientific_completion_inferred"] is False
    assert m.sha(target) == row["sha256"] and len(calls) == 1
    assert Path(result["files"][0]["previous_version"]).read_text() == "previous evidence"
    assert json.loads(receipt.read_text())["files"][0]["action"] == "downloaded_verified"
    second, _ = m.pull()
    assert second["files"][0]["action"] == "same_sha_skipped" and len(calls) == 1
    assert m.STATE.read_bytes() == state_before


def test_changed_remote_file_stays_quarantined(puller, monkeypatch):
    m = puller
    row, calls, inventory = fake_transfer(m, monkeypatch)
    count = []
    def changing(*args):
        count.append(1)
        copy_inventory = copy.deepcopy(inventory)
        if len(count) == 2:
            copy_inventory["files"][0]["mtime_ns"] += 1
        return copy_inventory
    monkeypatch.setattr(m, "remote_inventory", changing)
    with pytest.raises(ValueError, match="changed during pull"):
        m.pull()
    assert not (m.ROOT / row["relative"]).exists()
    receipts = list((m.ROOT / "results/formal_main_v2/pulls").glob("*/receipt.json"))
    failed = json.loads(receipts[0].read_text())
    assert failed["status"] == "failed_nonfinal" and failed["final_evidence"] is False
    assert (receipts[0].parent / "pending" / row["relative"]).is_file()


def test_changed_terminal_cost_cannot_be_published_as_final(puller, monkeypatch):
    m = puller
    row, _, _ = fake_transfer(m, monkeypatch)
    calls = []
    def changing(jobs, timeout):
        calls.append(1)
        result = account(jobs)
        if len(calls) == 2:
            result["jobs"]["101"]["elapsed_seconds"] += 1
        return result
    monkeypatch.setattr(m, "query_accounting", changing)
    with pytest.raises(ValueError, match="Terminal job accounting changed"):
        m.pull()
    assert not (m.ROOT / row["relative"]).exists()
    receipt = next((m.ROOT / "results/formal_main_v2/pulls").glob("*/receipt.json"))
    assert json.loads(receipt.read_text())["final_evidence"] is False


def test_running_only_selection_never_inventories_or_downloads(puller, monkeypatch):
    m = puller
    fake_transfer(m, monkeypatch)
    monkeypatch.setattr(m, "query_accounting", lambda jobs, timeout: account(jobs, **{"101": "RUNNING"}))
    monkeypatch.setattr(m, "remote_inventory", lambda *args: pytest.fail("live output inventoried"))
    result, _ = m.pull()
    assert result["status"] == "no_terminal_jobs" and not result["final_evidence"]


def test_windows_case_aliases_rejected_before_any_download(puller, monkeypatch):
    m = puller
    row, downloads, inventory = fake_transfer(m, monkeypatch)
    alias = copy.deepcopy(row)
    alias["path"] = alias["path"].replace("summary.json", "SUMMARY.json")
    alias["relative"] = alias["relative"].replace("summary.json", "SUMMARY.json")
    inventory["files"].append(alias)
    with pytest.raises(ValueError, match="aliased"):
        m.pull()
    assert downloads == []


def test_staged_local_change_does_not_replace_previous_evidence(puller, monkeypatch):
    m = puller
    row, _, inventory = fake_transfer(m, monkeypatch)
    target = m.ROOT / row["relative"]
    target.parent.mkdir(parents=True)
    target.write_bytes(b"original")
    calls = []
    def inventory_with_local_edit(*args):
        calls.append(1)
        if len(calls) == 2:
            staged = next((m.ROOT / "results/formal_main_v2/pulls").glob("*/pending/" + row["relative"]))
            staged.write_bytes(b"corrupt staged copy")
        return copy.deepcopy(inventory)
    monkeypatch.setattr(m, "remote_inventory", inventory_with_local_edit)
    with pytest.raises(ValueError, match="Quarantined bytes"):
        m.pull()
    assert target.read_bytes() == b"original"


def test_failed_download_keeps_original_and_partial_evidence(puller, monkeypatch):
    m = puller
    row, calls, inventory = fake_transfer(m, monkeypatch)
    target = m.ROOT / row["relative"]
    target.parent.mkdir(parents=True)
    target.write_text("original", encoding="utf-8")
    def failed_download(row, staged, timeout):
        staged.parent.mkdir(parents=True)
        staged.write_bytes(b"partial")
        raise RuntimeError("synthetic interrupted SSH")
    monkeypatch.setattr(m, "download_file", failed_download)
    with pytest.raises(RuntimeError, match="interrupted SSH"):
        m.pull()
    assert target.read_text() == "original"
    receipts = list((m.ROOT / "results/formal_main_v2/pulls").glob("*/receipt.json"))
    assert (receipts[0].parent / "pending" / row["relative"]).read_bytes() == b"partial"
    assert "interrupted SSH" in json.loads(receipts[0].read_text())["error"]


def test_new_job_registration_invalidates_publication(puller, monkeypatch):
    m = puller
    row, calls, inventory = fake_transfer(m, monkeypatch)
    count = []
    def query(jobs, timeout):
        count.append(1)
        if len(count) == 2:
            m.atomic_json(m.STATE, {"registered_jobs": [job(m), job(m, "102")]})
        return account(jobs)
    monkeypatch.setattr(m, "query_accounting", query)
    with pytest.raises(ValueError, match="registration changed"):
        m.pull()
    assert not (m.ROOT / row["relative"]).exists()


@pytest.mark.parametrize("relative", ["results/formal_main_v2/long/train/best.pt", "results/formal_main_v2/long/train/a.pt.json",
    "results/formal_main_v2/long/train/sealed_final.json", "results/formal_main_v2/long/train/initial_states/data.json",
    "results/formal_main_v2/long/train/weights/report.json", "results/formal_main_v2/long/train/con.json",
    "results/formal_main_v2/long/train/a.json ", "results/formal_main_v2/long/train/../escape.json",
    "results/formal_main_v2/long/train/a?b.json", "results/formal_main_v2/long/train/a*b.json",
    "results/formal_main_v2/long/train/a|b.json", "results/formal_main_v2/long/train/a<b.json",
    'results/formal_main_v2/long/train/a"b.json'])
def test_manifest_cannot_copy_weights_sealed_states_or_escape(puller, relative):
    m = puller
    request = {"jobs": [dict(job(m), include_run_root=True)]}
    with pytest.raises(ValueError):
        m.local_target(entry(m, rel=relative), request)


def test_unregistered_job_claim_and_unclassified_panel_are_rejected(puller):
    m = puller
    request = {"jobs": [dict(job(m), include_run_root=True)]}
    row = entry(m)
    row["job_ids"] = ["999"]
    with pytest.raises(ValueError, match="unregistered job"):
        m.local_target(row, request)
    panel = entry(m, rel="results/formal_main_v2/long/train/panel.json")
    with pytest.raises(ValueError, match="classified development"):
        m.local_target(panel, request)
    panel.update(panel_role="development_profile", panel_config_sha256="a" * 64)
    with pytest.raises(ValueError, match="bound to its inventoried config"):
        m.validate_inventory({"files": [panel]}, request)


def test_remote_program_inventories_and_streams_exact_registered_files(puller, tmp_path, monkeypatch):
    m = puller
    project = tmp_path / "server"
    monkeypatch.setattr(m, "P", project.as_posix())
    root = project / "results/formal_main_v2/long/train"
    root.mkdir(parents=True)
    (root / "summary.json").write_text('{"ok":true}', encoding="utf-8")
    (root / "best.pt").write_bytes(b"never copy weights")
    (root / "sealed_final.json").write_text("never copy states")
    (root / "weights").mkdir()
    (root / "weights/report.json").write_text("never enter")
    request = {"command": "inventory", "jobs": [dict(job(m), include_run_root=True)]}
    result = subprocess.run([sys.executable, "-"], input=m.remote_code(request), capture_output=True, text=True, check=True)
    inventory = json.loads(result.stdout)
    assert [row["relative"] for row in inventory["files"]] == ["results/formal_main_v2/long/train/summary.json"]
    assert len(inventory["excluded"]) == 3 and len(inventory["missing"]) == 3
    row = inventory["files"][0]
    result = subprocess.run([sys.executable, "-"], input=m.remote_code({"command": "download", "file": row}).encode(),
                            capture_output=True, check=True)
    assert result.stdout == (root / "summary.json").read_bytes()
    (root / "summary.json").write_text("changed", encoding="utf-8")
    changed = subprocess.run([sys.executable, "-"], input=m.remote_code({"command": "download", "file": row}).encode(),
                             capture_output=True)
    assert changed.returncode != 0 and b"changed before transfer" in changed.stderr and changed.stdout == b""


@pytest.mark.parametrize("kind", ["final", "development", "profile", "unclassified"])
def test_remote_panel_classification_never_opens_final_state_values(puller, tmp_path, monkeypatch, kind):
    m = puller
    project = tmp_path / "server"
    monkeypatch.setattr(m, "P", project.as_posix())
    root = project / "results/formal_main_v2/long/train"
    root.mkdir(parents=True)
    if kind == "profile":
        config = dict(version="formal-main-v2-control-observations-1", command="collect",
            test_opened=False, manifest={"split": "development"})
    else:
        config = dict(schema="formal_main_v2", kind="evaluation_run", manifest={"split": kind})
    (root / "config.json").write_text(json.dumps(config), encoding="utf-8")
    (root / "panel.json").write_bytes(b"synthetic opaque panel; no actual state values")
    request = {"command": "inventory", "jobs": [dict(job(m), include_run_root=True)]}
    code = m.remote_code(request)
    if kind in ("final", "unclassified"):
        # Prove exclusion happens before opening/hashing panel bytes. Only the
        # adjacent, non-state execution config may be read to classify it.
        code = code.replace("def open_regular(path):", "def open_regular(path):\n    if path.name == 'panel.json':\n        raise AssertionError('state bytes were opened')")
    result = subprocess.run([sys.executable, "-"], input=code, capture_output=True, text=True, check=True)
    inventory = json.loads(result.stdout)
    panels = [r for r in inventory["files"] if r["relative"].endswith("/panel.json")]
    if kind in ("final", "unclassified"):
        assert panels == [] and any(Path(r["path"]).name == "panel.json" for r in inventory["excluded"])
    else:
        assert len(panels) == 1
        assert panels[0]["panel_role"] == ("development_profile" if kind == "profile" else "development_evaluation")
        assert panels[0]["panel_config_sha256"] == m.sha(root / "config.json")
        # A formerly permitted panel becoming final between inventory and
        # transfer cannot stream even one byte.
        (root / "config.json").write_text(json.dumps(dict(schema="formal_main_v2", kind="evaluation_run", manifest={"split": "final"})))
        download = subprocess.run([sys.executable, "-"], input=m.remote_code({"command": "download", "file": panels[0]}).encode(), capture_output=True)
        assert download.returncode != 0 and download.stdout == b"" and b"final state values" in download.stderr


"""Independent focused tests for the versioned startup pull ownership partition.

Only the canonical-failure reconstruction is replaced by an explicit synthetic
oracle in fixture tests.  The production shared Evidence/require_pulled and the
new partition function execute unchanged.  The real-data case uses the original
canonical failure verifier as well.  No Slurm, tensor or production writes.
"""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest

R = Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
D = R / ".local/cuda_recovery_independent_0943"
SOURCE = R / ".local/cuda_terminal_review_0943/review_formal_segment_startup.py"
SOURCE_SHA = "ee0efc4b762e879e91e5e184fbc33dc236741cf71d51a6f5b4711710812f47b4"
spec = importlib.util.spec_from_file_location("independent_startup_0943", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
ORIGINAL_STARTUP = m._startup

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def write(root, name, raw):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw if isinstance(raw, bytes) else json.dumps(raw, sort_keys=True).encode())
    return path

@pytest.fixture
def fixture(tmp_path, monkeypatch):
    root = tmp_path / "project"
    root.mkdir()
    current = dict(job_id="3039258", mode="train", name="cti-formal",
                   stage_key="libero_object_train_k256_seed23",
                   run_root=str(m.P / "results/formal_main_v2/libero_object/k256/seed23/training"),
                   source_sha256="1" * 64, status="COMPLETED", exit_code="0:0",
                   elapsed_seconds=6512, gpus=1)
    old = dict(current, job_id="3028460", status="FAILED", exit_code="1:0", elapsed_seconds=84,
               invocation="results/formal_main_v2/invocations/old.json")
    old["invocation_sha256"] = digest(write(root, old["invocation"], {"version": "old"}).read_bytes())
    external = [f"results/formal_main_v2/job_receipts/{old['job_id']}.json",
                *[f"results/slurm/cti-formal_{old['job_id']}.{ext}" for ext in ("out", "err")]]
    shared = "results/formal_main_v2/libero_object/k256/seed23/training/runtime_compat/old_identity.json"
    new = f"results/formal_main_v2/job_receipts/{current['job_id']}.json"
    required = external + [shared, new]
    rows = []
    for i, rel in enumerate(required):
        raw = json.dumps({"synthetic": True, "i": i}).encode()
        write(root, rel, raw)
        rows.append(dict(relative=rel, path=str(m.P / rel), sha256=digest(raw), bytes=len(raw),
                         job_ids=[old["job_id"]] if rel in external else [old["job_id"], current["job_id"]]))
    selected = []
    for job in (old, current):
        # Exactly the real pull writer projection: no invocation/status fields.
        selected.append({**{k: job[k] for k in ("job_id", "mode", "name", "stage_key", "run_root", "source_sha256")},
                         "include_run_root": True, "active_overlapping_job_ids": []})
    accounting = {"jobs": {j["job_id"]: {**{k: j[k] for k in ("status", "exit_code", "elapsed_seconds")},
                         "allocation": "cpu=1,gres/gpu=1,gres/gpu:l40=1"} for j in (old, current)}}
    receipt_rel = "results/formal_main_v2/pulls/synthetic/receipt.json"
    receipt = dict(schema="formal_main_v2", kind="nonweight_pull", status="verified_nonweight_snapshot",
                   final_evidence=True, weights_copied=False, sealed_initial_states_copied=False,
                   selected_jobs=selected, registered_jobs=[{k: v for k, v in x.items()
                     if k not in ("include_run_root", "active_overlapping_job_ids")} for x in selected],
                   accounting_before=copy.deepcopy(accounting), accounting_after=copy.deepcopy(accounting),
                   missing=[], skipped=[], files=[dict(x, action="downloaded_verified") for x in rows])
    inventory = dict(files=copy.deepcopy(rows))
    canonical = dict(status="verified_startup_failure", retained_failure_files=required[:-1],
                     evidence_bundle={r["relative"]: {"sha256": r["sha256"], "bytes": r["bytes"]} for r in rows})
    calls = []
    def canonical_oracle(evidence, *, job, saved):
        calls.append(job["job_id"])
        assert job["job_id"] == old["job_id"] and saved == canonical
        return canonical
    monkeypatch.setattr(m, "_startup", SimpleNamespace(require_saved=canonical_oracle))
    f = SimpleNamespace(root=root, old=old, current=current, required=required,
                        external=external, shared=shared, new=new, rows=rows,
                        receipt=receipt, inventory=inventory, canonical=canonical,
                        receipt_rel=receipt_rel, calls=calls)
    def publish(*, different_after=False):
        before = write(root, str(Path(receipt_rel).parent / "inventory_before.json"), inventory)
        write(root, str(Path(receipt_rel).parent / "inventory_after.json"),
              dict(inventory, altered=True) if different_after else inventory)
        receipt["inventory_sha256"] = digest(before.read_bytes())
        write(root, receipt_rel, receipt)
    f.publish = publish
    def run(history=True):
        publish()
        return m.require_pulled_startup_ownership(m.Evidence(root), receipt_rel, current, required,
                 {old["job_id"]: old, current["job_id"]: current},
                 {old["job_id"]: canonical} if history else {})
    f.run = run
    return f

def test_real_writer_projection_and_precise_partition(fixture):
    f = fixture
    assert "invocation_sha256" not in f.receipt["selected_jobs"][0]
    assert "invocation_sha256" not in f.receipt["registered_jobs"][0]
    assert f.run() == {rel: f.old["job_id"] for rel in sorted(f.external)}
    assert f.calls == [f.old["job_id"]]

@pytest.mark.parametrize("mutation", [
    "old_owned_by_current", "old_shared_membership", "shared_missing_current",
    "wrong_old_path", "wrong_old_bytes", "wrong_old_hash", "wrong_old_action",
    "missing_old_file", "duplicate_receipt", "duplicate_inventory",
    "incomplete_retained", "incomplete_required", "changed_invocation",
    "old_wrong_status", "old_wrong_exit", "old_wrong_seconds", "old_wrong_gpu",
    "selected_wrong_source", "selected_wrong_root", "selected_wrong_mode",
    "selected_wrong_name", "selected_wrong_stage", "selected_duplicated",
    "selected_not_final", "active_overlap", "missing_files", "skipped_files",
    "saved_not_verified"
])
def test_partition_rejects_corruption(fixture, mutation):
    f = fixture
    r = f.receipt["files"][0]
    inv = f.inventory["files"][0]
    if mutation == "old_owned_by_current":
        r["job_ids"] = inv["job_ids"] = [f.current["job_id"]]
    elif mutation == "old_shared_membership":
        r["job_ids"] = inv["job_ids"] = [f.old["job_id"], f.current["job_id"]]
    elif mutation == "shared_missing_current":
        for rows in (f.receipt["files"], f.inventory["files"]):
            next(x for x in rows if x["relative"] == f.shared)["job_ids"] = [f.old["job_id"]]
    elif mutation.startswith("wrong_old_"):
        key, value = {"wrong_old_path": ("path", "/different/raw.json"),
                      "wrong_old_bytes": ("bytes", r["bytes"] + 1),
                      "wrong_old_hash": ("sha256", "0" * 64),
                      "wrong_old_action": ("action", "unverified")}[mutation]
        r[key] = value
        if key != "action": inv[key] = value
    elif mutation == "missing_old_file":
        f.receipt["files"].pop(0)
    elif mutation == "duplicate_receipt":
        f.receipt["files"].append(copy.deepcopy(r))
    elif mutation == "duplicate_inventory":
        f.inventory["files"].append(copy.deepcopy(inv))
    elif mutation == "incomplete_retained":
        f.canonical["retained_failure_files"].remove(f.external[0])
    elif mutation == "incomplete_required":
        f.required.remove(f.external[0])
    elif mutation == "changed_invocation":
        write(f.root, f.old["invocation"], {"version": "changed"})
    elif mutation.startswith("old_wrong_"):
        field, value = {"old_wrong_status": ("status", "COMPLETED"),
                        "old_wrong_exit": ("exit_code", "0:0"),
                        "old_wrong_seconds": ("elapsed_seconds", 0),
                        "old_wrong_gpu": ("allocation", "cpu=1,gres/gpu=0")}[mutation]
        f.receipt["accounting_after"]["jobs"][f.old["job_id"]][field] = value
    elif mutation.startswith("selected_wrong_"):
        field = {"source": "source_sha256", "root": "run_root", "mode": "mode",
                 "name": "name", "stage": "stage_key"}[mutation.removeprefix("selected_wrong_")]
        f.receipt["selected_jobs"][0][field] = "incorrect"
    elif mutation == "selected_duplicated":
        f.receipt["selected_jobs"].append(copy.deepcopy(f.receipt["selected_jobs"][0]))
    elif mutation == "selected_not_final":
        f.receipt["selected_jobs"][0]["include_run_root"] = False
    elif mutation == "active_overlap":
        f.receipt["selected_jobs"][0]["active_overlapping_job_ids"] = ["999"]
    elif mutation == "missing_files":
        f.receipt["missing"].append({"relative": f.external[0]})
    elif mutation == "skipped_files":
        f.receipt["skipped"].append({"job_id": f.old["job_id"]})
    elif mutation == "saved_not_verified":
        f.canonical["status"] = "passed"
    with pytest.raises(ValueError):
        f.run()

def test_nonstartup_path_preserves_original_current_ownership(fixture):
    f = fixture
    f.required = [f.shared, f.new]
    assert f.run(history=False) == {}
    f.receipt["files"][-1]["job_ids"] = [f.old["job_id"]]
    f.inventory["files"][-1]["job_ids"] = [f.old["job_id"]]
    with pytest.raises(ValueError, match="Required evidence"):
        f.run(history=False)

def test_unstable_double_inventory_rejected(fixture):
    f = fixture
    f.publish(different_after=True)
    with pytest.raises(ValueError, match="stable double"):
        m.require_pulled_startup_ownership(m.Evidence(f.root), f.receipt_rel, f.current, f.required,
            {f.old["job_id"]: f.old, f.current["job_id"]: f.current},
            {f.old["job_id"]: f.canonical})

def test_exact_source_and_existing_review_binding():
    assert digest(SOURCE.read_bytes()) == SOURCE_SHA
    old = (R / ".local/cuda_startup_recovery_0840/review_formal_segment_startup.py").read_text()
    new = SOURCE.read_text()
    a, b = ast.parse(old), ast.parse(new)
    af = {x.name: ast.dump(x, include_attributes=False) for x in a.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))}
    bf = {x.name: ast.dump(x, include_attributes=False) for x in b.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert set(bf) - set(af) == {"require_pulled_startup_ownership"}
    assert [key for key in af if af[key] != bf[key]] == ["review"]
    assert '"startup_failure_consumer", "startup_pull_ownership")' in new
    assert "prior[\"invocation_sha256\"]" in new
    assert "selected[0].get(\"invocation_sha256\")" not in new

def test_real_read_only_exact_partition_uses_original_failure_verifier(monkeypatch):
    monkeypatch.setattr(m, "_startup", ORIGINAL_STARTUP)
    rel = ".local/cuda_terminal_review_0943/actual_local_review.json"
    evidence = m.Evidence(R)
    actual = evidence.read(rel)
    assert evidence.watch(rel) == "9d8c57dd948172d1a51afb5dee674e4bc06122246c41e78072936f5d97965801"
    jobs = {str(row["job_id"]): row for row in actual["registered_pair_jobs_at_review"]}
    pull = "results/formal_main_v2/pulls/20261019T095542Z_e5d54e39d3ae/receipt.json"
    assert evidence.watch(pull) == "8cf02df4314a103db61824fbf64a238994a1572757bc443682ab6d5d319be0e8"
    result = m.require_pulled_startup_ownership(evidence, pull, jobs["3039258"],
             list(actual["files"]), jobs, actual["startup_failure_history"])
    assert result == actual["startup_pull_ownership"]
    assert len(result) == 3
    evidence.unchanged()

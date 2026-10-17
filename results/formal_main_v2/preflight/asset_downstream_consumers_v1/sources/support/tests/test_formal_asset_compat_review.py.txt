"""Synthetic wrapper metadata only; no weights, final state values or SSH.

The fixture copies the actual173 frozen source/config files and exact original
asset manifests. Wrapper execution is covered separately with its real writer;
these fixtures target the independent parser's deliberate corruptions.
"""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
HELPER = "scripts/ops/formal_asset_compat_review.py"


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    project = tmp_path_factory.mktemp("synthetic_asset_review")
    assert ROOT / ".local" in project.parents
    m = load(HELPER, "synthetic_asset_review_helper")
    shared = load("scripts/review_formal_acceptance.py", "synthetic_asset_review_shared")
    inventory = json.loads((ROOT / m.SOURCE_INVENTORY).read_text())
    extra = [HELPER, m.SOURCE_INVENTORY, m.ADAPTER, m.REGISTRATION, *m.STRICT.values()]
    for relative in [*inventory["files"], *extra]:
        source, target = ROOT / relative, project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    for relative in (m.WRAPPER, m.SLURM):
        # Only the independent receipt validator is under test here. A real
        # wrapper-writer integration fixture is supplied by its own CPU tests.
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# synthetic wrapper contract bytes; never executed\n", encoding="utf-8")
    before = {name: sha(ROOT / name) for name in inventory["files"]}
    yield SimpleNamespace(root=project, m=m, shared=shared, inventory=inventory, sequence=0)
    assert {name: sha(ROOT / name) for name in inventory["files"]} == before


def make_case(project, suite="libero_object", stage="acceptance"):
    p, m = project.root, project.m
    project.sequence += 1
    job_id = str(8100000 + project.sequence)
    runtime = dict(schema=m.SCHEMA, kind="asset_metadata_compatibility", version=m.VERSION,
        wrapper=m.WRAPPER, slurm=m.SLURM, adapter=m.ADAPTER, registration=m.REGISTRATION,
        files={relative: sha(p / relative) for relative in (m.WRAPPER, m.SLURM, m.ADAPTER, m.REGISTRATION, *m.STRICT.values())})
    relative = f"results/{m.SCHEMA}/{suite}/acceptance/attempt{project.sequence:02d}"
    if stage == "train":
        relative = f"results/{m.SCHEMA}/{suite}/k128/seed17/training"
    output = str(m.P / relative)
    job = dict(job_id=job_id, suite=suite, mode=stage, experiment=m.SCHEMA, status="COMPLETED", exit_code="0:0",
        source_root=str(m.SOURCE), source_sha256=m.SOURCE_SHA256, stage_key=suite + "_" + stage,
        run_root=output, invocation=f"results/{m.SCHEMA}/invocations/synthetic_{job_id}.json", runtime_compatibility=runtime)
    entry = "scripts/verify_formal_acceptance.py" if stage == "acceptance" else "scripts/run_formal_future.py"
    inv = dict(schema=m.SCHEMA, stage=stage, stage_key=job["stage_key"], suite=suite, source_root=str(m.SOURCE),
        source_sha256=m.SOURCE_SHA256, entrypoint=entry, runtime_compatibility=runtime,
        argv=["--asset-manifest", str(m.SOURCE / m.ORIGINALS[suite][0])], watched_files={})
    save(p / job["invocation"], inv)
    job["invocation_sha256"] = sha(p / job["invocation"])
    common = dict(job_id=job_id, stage=stage, stage_key=job["stage_key"], suite=suite,
        source_root=str(m.SOURCE), source_sha256=m.SOURCE_SHA256, invocation_sha256=job["invocation_sha256"])
    # Independently construct the producer's exact metadata identity from the
    # fixed registration, without using helper.expected_identity().
    registration = json.loads((p / m.REGISTRATION).read_text())
    views = {}
    for key, row in registration["views"].items():
        header = row["equal_header"]
        views[key] = dict(suite=key, original_path=str(m.SOURCE / row["original_path"]), original_sha256=row["original_sha256"],
            derived_path=str(m.P / row["derived_path"]), derived_sha256=row["derived_sha256"], file_count=row["file_count"],
            total_bytes=header["total_bytes"], repository=header["repository"], revision=header["revision"],
            file_specs_sha256=row["file_specs_sha256"], projected_payload_sha256=row["projected_payload_sha256"],
            omitted_metadata_fields=list(m.OMITTED))
    watched = {str(m.P / m.ADAPTER): sha(p / m.ADAPTER), str(m.P / m.REGISTRATION): sha(p / m.REGISTRATION),
        str(m.P / m.SOURCE_INVENTORY): sha(p / m.SOURCE_INVENTORY),
        **{str(m.SOURCE / name): digest for name, digest in project.inventory["files"].items()},
        **{str(m.P / row["derived_path"]): row["derived_sha256"] for row in registration["views"].values()}}
    identity = dict(schema=m.SCHEMA, kind="asset_metadata_compatibility", version=m.VERSION,
        project_root=str(m.P), source_root=str(m.SOURCE), source_inventory=str(m.P / m.SOURCE_INVENTORY),
        source_inventory_sha256=sha(p / m.SOURCE_INVENTORY), frozen_source_sha256=m.SOURCE_SHA256,
        verified_frozen_file_count=173, adapter_path=str(m.P / m.ADAPTER), adapter_sha256=sha(p / m.ADAPTER),
        registration_path=str(m.P / m.REGISTRATION), registration_sha256=sha(p / m.REGISTRATION),
        loader_path=str(m.SOURCE / m.LOADER), loader_sha256=m.LOADER_SHA256,
        original_loader_code_sha256="a" * 64, directory_verifier_code_sha256="b" * 64,
        fingerprint_marshal_version=2, original_manifest_identity_retained=True, views=views, watched_files=watched)
    payload = dict(schema=m.SCHEMA, kind="formal_asset_stage_identity", version=m.STAGE_VERSION, **common,
        invocation_path=str(m.P / job["invocation"]), runtime_compatibility=runtime, identity=identity)
    copied = p / relative / "compatibility" / job_id
    identity_path = save(copied / "identity.json", payload)
    identity_sha = sha(identity_path)
    rows = []
    start = datetime(2026, 10, 17, tzinfo=timezone.utc)
    def event(name, **fields):
        rows.append(dict(schema=m.SCHEMA, kind="formal_asset_stage_event", version=m.STAGE_VERSION, **common,
            utc=(start + timedelta(seconds=len(rows))).isoformat(), seq=len(rows), event=name, **fields))
    event("stage_start", entrypoint=entry, argv=inv["argv"], run_root=output, runtime_compatibility=runtime)
    event("asset_metadata_compat_enter", identity=identity, binding_code_sha256="c" * 64)
    event("stage_runner_start", entrypoint=entry, argv=inv["argv"], cwd=str(m.SOURCE), run_name="__main__", identity_sha256=identity_sha)
    event("asset_metadata_compat_load_start", call_id=0, view=views[suite])
    event("asset_metadata_compat_load_complete", call_id=0, file_count=25, total_bytes=views[suite]["total_bytes"])
    event("stage_runner_return", runner_termination="returned", runner_exit_code=0)
    event("asset_metadata_compat_exit", original_loader_restored=True, directory_verifier_unchanged=True,
        binding_intact=True, original_loader_code_unchanged=True, directory_verifier_code_unchanged=True,
        frozen_source_and_inputs_unchanged=True, runner_raised=False,
        adapted_calls_attempted=1, adapted_calls_completed=1, passthrough_calls=0)
    end = dict(status="returned", exit_code=0, runner_termination="returned", runner_exit_code=0,
        loader_restored=True, source_inputs_unchanged=True, errors=[])
    event("stage_end", **end, identity_sha256=identity_sha)
    receipt = dict(schema=m.SCHEMA, kind="formal_asset_stage_job", version=m.STAGE_VERSION,
        **common,
        entrypoint=entry, run_root=output, runtime_compatibility=runtime,
        wrapper_sha256=runtime["files"][m.WRAPPER], started_utc=start.isoformat(), wall_seconds=10., **end)
    c = SimpleNamespace(**project.__dict__, job=job, invocation=inv, runtime=runtime, payload=payload,
        copied=copied, rows=rows, receipt=receipt, relative=relative)
    reseal(c)
    return c


def reseal(c):
    m, p, job_id = c.m, c.root, c.job["job_id"]
    save(c.copied / "identity.json", c.payload)
    events = c.copied / "compatibility_events.jsonl"
    events.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in c.rows), encoding="utf-8", newline="\n")
    c.receipt["compatibility_artifacts"] = [dict(source=str(m.P / f"results/{m.SCHEMA}/compatibility_invocations/{job_id}" / name),
        path=str(m.P / c.relative / "compatibility" / job_id / name), bytes=(c.copied / name).stat().st_size,
        sha256=sha(c.copied / name)) for name in m.ARTIFACT_NAMES]
    receipt_path = save(p / f"results/{m.SCHEMA}/job_receipts/{job_id}.json", c.receipt)
    files = [c.copied / name for name in m.ARTIFACT_NAMES] + [receipt_path]
    rows = [dict(relative=path.relative_to(p).as_posix(), path=str(m.P / path.relative_to(p).as_posix()),
        job_ids=[job_id], sha256=sha(path), bytes=path.stat().st_size) for path in files]
    c.pull = p / f"results/{m.SCHEMA}/pulls/synthetic_{job_id}/receipt.json"
    before = save(c.pull.parent / "inventory_before.json", dict(files=rows))
    save(c.pull.parent / "inventory_after.json", dict(files=rows))
    accounting = dict(jobs={job_id: dict(status="COMPLETED", exit_code="0:0")})
    save(c.pull, dict(schema=m.SCHEMA, kind="nonweight_pull", status="verified_nonweight_snapshot", final_evidence=True,
        weights_copied=False, sealed_initial_states_copied=False, selected_jobs=[dict(c.job, include_run_root=True)],
        accounting_before=accounting, accounting_after=accounting, inventory_sha256=sha(before),
        files=[dict(row, action="downloaded_verified") for row in rows]))


def review(c, pulled=False):
    evidence = c.shared.Evidence(c.root)
    kwargs = dict(job=c.job, invocation=c.invocation, receipt=c.receipt, inventory=c.inventory)
    result = (c.shared.review_runtime_compatibility(evidence, **kwargs, pull_receipt=c.pull)
        if pulled else c.m.review_job(evidence, **kwargs))
    evidence.unchanged()
    return result


@pytest.mark.parametrize("suite,stage", [("libero_object", "acceptance"), ("libero_goal", "acceptance"),
    ("libero_object", "train"), ("libero_goal", "train")])
def test_complete_contract_with_actual_projection_and_verified_pull(project, suite, stage):
    c = make_case(project, suite, stage)
    result = review(c, pulled=True)
    assert result["status"] == "verified" and result["exact_target_suite_loads"] == 1
    assert len(result["required_pulled_files"]) == 2 and result["runtime_compatibility"] == c.runtime
    assert result["pull_receipt"]["sha256"] == sha(c.pull)
    saved = dict(runtime_compatibility=c.runtime, runtime_compatibility_review=result)
    rebuilt = c.shared.require_saved_runtime_review(c.shared.Evidence(c.root), saved=saved, job=c.job, inventory=c.inventory)
    assert rebuilt == result


@pytest.mark.parametrize("change", ["wrong_suite", "wrong_job", "wrong_source", "wrong_seq", "duplicate_load",
    "extra_event", "missing_exit", "not_restored", "code_changed", "runner_raised", "passthrough", "load_count",
    "wrong_call", "return_nonzero", "failure_status", "identity_mismatch", "wrong_copy_source", "empty_artifacts",
    "receipt_source", "unregistered_runtime"])
def test_corruption_rejected_even_with_new_artifact_and_pull_hashes(project, change):
    c = make_case(project)
    if change == "wrong_suite": c.rows[3]["view"] = c.payload["identity"]["views"]["libero_goal"]
    elif change == "wrong_job": c.rows[4]["job_id"] = "123"
    elif change == "wrong_source": c.rows[2]["source_sha256"] = "0" * 64
    elif change == "wrong_seq": c.rows[4]["seq"] = 3
    elif change == "duplicate_load": c.rows.insert(5, deepcopy(c.rows[3]))
    elif change == "extra_event": c.rows.append(deepcopy(c.rows[-1]))
    elif change == "missing_exit": c.rows.pop(6)
    elif change == "not_restored": c.rows[6]["original_loader_restored"] = False
    elif change == "code_changed": c.rows[6]["directory_verifier_code_unchanged"] = False
    elif change == "runner_raised": c.rows[6]["runner_raised"] = True
    elif change == "passthrough": c.rows[6]["passthrough_calls"] = 1
    elif change == "load_count": c.rows[6]["adapted_calls_completed"] = 0
    elif change == "wrong_call": c.rows[4]["call_id"] = 1
    elif change == "return_nonzero": c.rows[5]["runner_exit_code"] = 1
    elif change == "failure_status": c.receipt["status"] = "failed"
    elif change == "receipt_source": c.receipt["source_root"] = "/unregistered/snapshot"
    elif change == "unregistered_runtime": c.job.pop("runtime_compatibility")
    elif change == "identity_mismatch": c.payload["identity"]["views"]["libero_goal"]["file_count"] = 24
    reseal(c)
    if change == "wrong_copy_source": c.receipt["compatibility_artifacts"][0]["source"] = "/elsewhere/identity.json"
    if change == "empty_artifacts": c.receipt["compatibility_artifacts"] = []
    with pytest.raises(ValueError): review(c, pulled=True)


def test_unterminated_tail_and_unverified_pull_are_rejected(project):
    c = make_case(project)
    path = c.copied / "compatibility_events.jsonl"
    path.write_bytes(path.read_bytes().rstrip(b"\n"))
    c.receipt["compatibility_artifacts"][1].update(bytes=path.stat().st_size, sha256=sha(path))
    with pytest.raises(ValueError, match="unterminated"): review(c)
    reseal(c)
    pull = json.loads(c.pull.read_text()); pull["final_evidence"] = False; save(c.pull, pull)
    with pytest.raises(ValueError, match="pull receipt"): review(c, pulled=True)


@pytest.mark.parametrize("suite", ["libero_object", "libero_goal"])
def test_compatibility_cannot_be_omitted_or_silently_consumed(project, suite):
    c = make_case(project, suite)
    c.invocation.pop("runtime_compatibility")
    with pytest.raises(ValueError, match="requires explicit"): review(c)
    with pytest.raises(ValueError, match="not integrated"):
        c.m.reject_unintegrated_consumer(suite=suite, review=dict(status="passed"), consumer="synthetic downstream")


def test_exact_six_files_and_fixed_adapter_are_required(project):
    c = make_case(project)
    c.runtime["files"]["unregistered.py"] = "a" * 64
    with pytest.raises(ValueError, match="exactly six"): review(c)
    c.runtime["files"].pop("unregistered.py")
    c.runtime["files"][c.m.ADAPTER] = "0" * 64
    with pytest.raises(ValueError, match="bytes changed"): review(c)


@pytest.mark.parametrize("suite", ["libero_10", "libero_spatial"])
def test_legacy_branch_performs_no_compatibility_io(project, suite):
    class NoIO:
        def __getattr__(self, name): pytest.fail("Legacy compatibility branch attempted IO: " + name)
    job = dict(suite=suite)
    assert project.m.review_job(NoIO(), job=job, invocation={}, receipt={}, inventory={}) is None
    project.m.reject_unintegrated_consumer(suite=suite, review=dict(status="passed"), consumer="legacy")
    with pytest.raises(ValueError, match="legacy suite"):
        project.m.review_job(NoIO(), job=job, invocation=dict(runtime_compatibility=None), receipt={}, inventory={})


def test_actual_long_historical_wrapper_receipt_remains_legacy(project):
    state = json.loads((ROOT / "results/experiment_supervisor/state.json").read_text())
    job = next(row for row in state["registered_jobs"] if row.get("job_id") == "3012151")
    invocation_path, receipt_path = ROOT / job["invocation"], ROOT / "results/formal_main_v2/job_receipts/3012151.json"
    before = {str(path): sha(path) for path in (invocation_path, receipt_path)}
    assert project.m.review_job(project.shared.Evidence(ROOT), job=job,
        invocation=json.loads(invocation_path.read_text()), receipt=json.loads(receipt_path.read_text()), inventory={}) is None
    assert {str(path): sha(path) for path in (invocation_path, receipt_path)} == before


@pytest.mark.parametrize("suite", ["libero_object", "libero_goal"])
def test_existing_execution_builder_refuses_compatibility_before_raw_gates(project, suite):
    execution = load("scripts/formal_execution_manifests.py", "synthetic_asset_downstream_gate")
    p = project.root / f"results/formal_main_v2/{suite}/acceptance/root_review.json"
    save(p, dict(status="passed", runtime_compatibility=dict(synthetic=True)))
    with pytest.raises(ValueError, match="not integrated"):
        execution.load_suite_acceptance(execution.Evidence(project.root), dict(suites={suite: {}}), suite, {})


@pytest.fixture(scope="module")
def actual_writer_project(tmp_path_factory):
    """Execute the real wrapper/adapter with only its GPU runner replaced.

    The writer fixture imports the frozen checkpoint-manifest parser and keeps
    all173 source bytes and six operational inputs. Its runpy.run_path stand-in
    loads only manifest metadata; no model, scientific gate or data is run.
    """
    writer = load("tests/test_formal_asset_stage.py", "synthetic_actual_asset_writer")
    actual = writer.synthetic.__wrapped__(tmp_path_factory)
    normalized = tmp_path_factory.mktemp("synthetic_asset_writer_server_transport")
    m = load(HELPER, "synthetic_writer_review_helper")
    shared = load("scripts/review_formal_acceptance.py", "synthetic_writer_review_shared")
    inventory = json.loads((ROOT / m.SOURCE_INVENTORY).read_text())
    for relative in inventory["files"]:
        target = normalized / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(actual.source / relative, target)
    for relative in [HELPER, m.SOURCE_INVENTORY, *writer.SUPPORT]:
        source = ROOT / relative if relative in (HELPER, m.SOURCE_INVENTORY) else actual.project / relative
        target = normalized / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    before = {name: sha(ROOT / name) for name in [*inventory["files"], *writer.SUPPORT]}
    yield SimpleNamespace(root=normalized, m=m, shared=shared, inventory=inventory, writer=writer, actual=actual)
    assert {name: sha(ROOT / name) for name in before} == before


def transport_actual_writer(project, source_case, source_receipt):
    """Synthetic path transport only; no field invention to repair a writer.

    Replace the Windows temporary root by the registered POSIX root. Rebind
    only hashes whose bytes necessarily change: inventory, invocation,
    identity and journal. Keep unmodified writer copies and record their SHA.
    The root review helper and verified-pull parser are not mocked.
    """
    m, p, actual = project.m, project.root, project.actual
    original_root = actual.project.as_posix()
    def translate(value):
        if isinstance(value, dict):
            return {translate(key): translate(item) for key, item in value.items()}
        if isinstance(value, list):
            return [translate(item) for item in value]
        if isinstance(value, str):
            normalized = value.replace("\\", "/")
            if normalized == original_root or normalized.startswith(original_root + "/"):
                return str(m.P) + normalized[len(original_root):]
        return value
    inv, receipt = translate(source_case.value), translate(source_receipt)
    relative = source_case.output.relative_to(actual.project).as_posix()
    invocation_rel = source_case.path.relative_to(actual.project).as_posix()
    save(p / invocation_rel, inv)
    inv_sha = sha(p / invocation_rel)
    copied = p / relative / "compatibility" / source_case.job
    source_files = {Path(a["path"]).name: Path(a["path"]) for a in source_receipt["compatibility_artifacts"]}
    originals = {str(path): sha(path) for path in [source_case.path, source_case.receipt, *source_files.values()]}
    payload = translate(json.loads(source_files["identity.json"].read_text()))
    rows = translate([json.loads(line) for line in source_files["compatibility_events.jsonl"].read_text().splitlines()])
    payload["invocation_sha256"] = inv_sha
    inventory_sha = sha(p / m.SOURCE_INVENTORY)
    for identity in [payload["identity"], *(row["identity"] for row in rows if row["event"] == "asset_metadata_compat_enter")]:
        identity["source_inventory_sha256"] = inventory_sha
        identity["watched_files"][str(m.P / m.SOURCE_INVENTORY)] = inventory_sha
    save(copied / "identity.json", payload)
    identity_sha = sha(copied / "identity.json")
    for row in rows:
        row["invocation_sha256"] = inv_sha
        if "identity_sha256" in row:
            row["identity_sha256"] = identity_sha
    receipt["invocation_sha256"] = inv_sha
    job = dict(job_id=source_case.job, suite=inv["suite"], mode=inv["stage"], experiment=m.SCHEMA,
        status="COMPLETED", exit_code="0:0", source_root=str(m.SOURCE), source_sha256=m.SOURCE_SHA256,
        stage_key=inv["stage_key"], run_root=str(m.P / relative), invocation=invocation_rel,
        invocation_sha256=inv_sha, runtime_compatibility=inv["runtime_compatibility"])
    c = SimpleNamespace(**project.__dict__, job=job, invocation=inv, runtime=inv["runtime_compatibility"],
        payload=payload, copied=copied, rows=rows, receipt=receipt, relative=relative)
    reseal(c)
    assert {name: sha(name) for name in originals} == originals
    save(copied.parent / "synthetic_transport.json", dict(synthetic=True, science_executed=False,
        source_files_sha256=originals, path_mapping={original_root: str(m.P)},
        rebound_sha256_fields=["source_inventory", "invocation", "identity", "compatibility_events", "pull"],
        validator_mocks=False))
    return c


@pytest.mark.parametrize("suite,stage", [("libero_object", "acceptance"), ("libero_goal", "acceptance"),
    ("libero_object", "train"), ("libero_goal", "train")])
def test_actual_wrapper_writer_through_verified_pull_and_saved_review(actual_writer_project, suite, stage):
    project = actual_writer_project
    source_case = project.writer.invocation(project.actual, suite=suite, stage=stage)
    source_receipt = project.writer.run(project.actual, source_case)
    c = transport_actual_writer(project, source_case, source_receipt)
    result = review(c, pulled=True)
    assert result["status"] == "verified" and result["exact_target_suite_loads"] == 1
    assert result["runtime_compatibility"] == source_receipt["runtime_compatibility"]
    saved = dict(runtime_compatibility=c.runtime, runtime_compatibility_review=result)
    assert c.shared.require_saved_runtime_review(c.shared.Evidence(c.root), saved=saved, job=c.job,
        inventory=c.inventory) == result


@pytest.mark.parametrize("suite,behavior", [("libero_object", "zero_load"), ("libero_goal", "exception")])
def test_actual_failed_wrapper_cannot_become_success_even_with_complete_pull(actual_writer_project, suite, behavior):
    project = actual_writer_project
    source_case = project.writer.invocation(project.actual, suite=suite)
    source_receipt = project.writer.run(project.actual, source_case, behavior=behavior, expected=1)
    assert source_receipt["status"] == "failed"
    c = transport_actual_writer(project, source_case, source_receipt)
    # Deliberately claim a successful Slurm pull to show that return/accounting
    # labels cannot hide the actual failed compatibility context.
    with pytest.raises(ValueError):
        review(c, pulled=True)

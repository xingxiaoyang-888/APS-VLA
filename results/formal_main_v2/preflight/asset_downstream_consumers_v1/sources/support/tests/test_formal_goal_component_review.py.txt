"""Synthetic nonweight proofs for Goal's separately registered component path fix."""
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
HELPER = "scripts/ops/formal_goal_component_review.py"


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    old = load("tests/test_formal_asset_compat_review.py", "goal_review_metadata_fixtures")
    generator = old.project.__wrapped__(tmp_path_factory)
    base = next(generator)
    goal = load(HELPER, "synthetic_goal_review")
    for name in [HELPER, *goal.FILES, goal.INNER, base.m.SLURM]:
        target = base.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    before = {name: sha(ROOT / name) for name in [*base.inventory["files"], goal.METADATA_HELPER]}
    yield SimpleNamespace(**base.__dict__, old=old, g=goal)
    assert {name: sha(ROOT / name) for name in before} == before
    with pytest.raises(StopIteration):
        next(generator)


def make_case(project, stage="acceptance"):
    c = project.old.make_case(project, "libero_goal", stage)
    g, p = project.g, project.root
    component = dict(schema=g.SCHEMA, kind="goal_component_filename_compatibility", version=g.VERSION,
        suite=g.SUITE, wrapper=g.WRAPPER, adapter=g.ADAPTER, slurm=g.SLURM, registration=g.REGISTRATION,
        files={name: sha(p / name) for name in g.FILES})
    c.job["component_compatibility"] = component
    c.invocation["component_compatibility"] = component
    save(p / c.job["invocation"], c.invocation)
    inv_sha = sha(p / c.job["invocation"])
    c.job["invocation_sha256"] = c.payload["invocation_sha256"] = c.receipt["invocation_sha256"] = inv_sha
    project.old.save(c.copied / "identity.json", c.payload)
    metadata_identity_sha = sha(c.copied / "identity.json")
    for row in c.rows:
        row["invocation_sha256"] = inv_sha
        if "identity_sha256" in row:
            row["identity_sha256"] = metadata_identity_sha
    project.old.reseal(c)
    registration = read(p / g.REGISTRATION)
    mapping = [dict(row, requested_path=str(g.MODEL_ROOT / row["requested"]),
        target_path=str(g.MODEL_ROOT / row["target"])) for row in registration["mappings"]]
    watched = {**{str(g.P / name): digest for name, digest in component["files"].items()},
        str(g.P / g.SOURCE_INVENTORY): sha(p / g.SOURCE_INVENTORY),
        **{str(g.SOURCE / name): digest for name, digest in c.inventory["files"].items()}}
    identity = dict(schema=g.SCHEMA, kind="goal_component_identity", version=g.VERSION, suite=g.SUITE,
        project_root=str(g.P), source_root=str(g.SOURCE), source_sha256=g.SOURCE_SHA256,
        source_inventory=str(g.P / g.SOURCE_INVENTORY), source_inventory_sha256=sha(p / g.SOURCE_INVENTORY),
        verified_frozen_file_count=173, component_compatibility=component, loader_path=str(g.SOURCE / g.LOADER),
        loader_sha256=g.LOADER_SHA256, original_function_code_sha256={name: ch * 64 for name, ch in zip(g.SYMBOLS, "abc")},
        fingerprint_marshal_version=2, model_manifest=str(g.SOURCE / g.MANIFEST), model_manifest_sha256=g.MANIFEST_SHA256,
        checkpoint_root=str(g.MODEL_ROOT), mappings=mapping, other_component_requests="reject",
        original_component_loader_used=True, torch_load_replaced=False, scientific_settings_changed=False,
        weights_changed=False, watched_files=watched)
    shared = dict(schema=g.SCHEMA, version=g.VERSION, job_id=c.job["job_id"], stage=stage, stage_key=c.job["stage_key"],
        suite=g.SUITE, source_root=str(g.SOURCE), source_sha256=g.SOURCE_SHA256, invocation_sha256=inv_sha)
    c.component_payload = dict(**shared, kind="formal_goal_component_identity", invocation_path=str(g.P / c.job["invocation"]),
        runtime_compatibility=c.runtime, component_compatibility=component, inner_wrapper_path=str(g.P / g.INNER),
        inner_wrapper_sha256=g.INNER_SHA256, identity=identity)
    c.component_dir = p / c.relative / "component_compatibility" / c.job["job_id"]
    c.component_rows = []
    base_time = datetime(2026, 10, 17, tzinfo=timezone.utc)
    offsets = [-3, -2, -1, 2.2, 2.3, 3.2, 4., 8., 9., 10.]
    def event(name, **fields):
        i = len(c.component_rows)
        c.component_rows.append(dict(**shared, kind="formal_goal_component_event", seq=i,
            utc=(base_time + timedelta(seconds=offsets[i])).isoformat(), event=name, **fields))
    receipt_path = p / f"results/{g.SCHEMA}/job_receipts/{c.job['job_id']}.json"
    receipt_ref = dict(path=str(g.P / receipt_path.relative_to(p).as_posix()), sha256=sha(receipt_path), bytes=receipt_path.stat().st_size)
    event("component_stage_start", entrypoint=c.invocation["entrypoint"], argv=c.invocation["argv"],
        runtime_compatibility=c.runtime, component_compatibility=component)
    event("goal_component_compat_enter", identity=deepcopy(identity), binding_code_sha256="d" * 64)
    event("component_inner_start", inner_wrapper_path=str(g.P / g.INNER), inner_wrapper_sha256=g.INNER_SHA256,
        entry_function="execute", identity_sha256="0" * 64)
    for i in range(2):
        event("goal_component_load_start", call_id=i, mapping=mapping[i])
        event("goal_component_load_complete", call_id=i, mapping=mapping[i], state_tensor_count=1, state_keys_sha256="e" * 64)
    event("component_inner_return", inner_exit_code=0, inner_job_receipt=receipt_ref, metadata_artifacts=deepcopy(c.receipt["compatibility_artifacts"]))
    event("goal_component_compat_exit", original_loader_restored=True, original_function_codes_unchanged=True,
        binding_intact=True, torch_load_unchanged=True, source_inputs_unchanged=True, component_files_unchanged=True,
        runner_raised=False, component_calls_attempted=2, component_calls_completed=2, rejected_calls=0)
    end = dict(status="returned", exit_code=0, inner_exit_code=0, original_loader_restored=True,
        source_inputs_unchanged=True, component_files_unchanged=True, errors=[])
    event("component_stage_end", **end, identity_sha256="0" * 64)
    c.component = component
    global_root = g.P / f"results/{g.SCHEMA}/component_compatibility_invocations/{c.job['job_id']}"
    copied_root = g.P / c.relative / "component_compatibility" / c.job["job_id"]
    c.completion = dict(**shared, kind="formal_goal_component_completion", **end,
        started_utc=(base_time - timedelta(seconds=3)).isoformat(), wall_seconds=13., cost_scope=g.COST_SCOPE,
        runtime_compatibility=c.runtime, component_compatibility=component, run_root=c.job["run_root"],
        inner_job_receipt=deepcopy(receipt_ref), metadata_artifacts=deepcopy(c.receipt["compatibility_artifacts"]),
        component_artifacts=[], completion_source=str(global_root / "completion.json"), completion_path=str(copied_root / "completion.json"))
    seal_component(c)
    return c


def refresh_pull(c):
    p, g = c.root, c.g
    paths = [*(c.copied / name for name in c.m.ARTIFACT_NAMES),
        p / f"results/{g.SCHEMA}/job_receipts/{c.job['job_id']}.json",
        *(c.component_dir / name for name in g.ARTIFACT_NAMES)]
    entries = [dict(relative=path.relative_to(p).as_posix(), path=str(g.P / path.relative_to(p).as_posix()),
        job_ids=[c.job["job_id"]], sha256=sha(path), bytes=path.stat().st_size) for path in paths]
    for name in ("inventory_before.json", "inventory_after.json"):
        save(c.pull.parent / name, dict(files=entries))
    pull = read(c.pull)
    pull.update(inventory_sha256=sha(c.pull.parent / "inventory_before.json"),
        files=[dict(entry, action="downloaded_verified") for entry in entries], selected_jobs=[dict(c.job, include_run_root=True)])
    save(c.pull, pull)


def seal_component(c):
    g = c.g
    save(c.component_dir / "identity.json", c.component_payload)
    checksum = sha(c.component_dir / "identity.json")
    for row in c.component_rows:
        if "identity_sha256" in row:
            row["identity_sha256"] = checksum
    events = c.component_dir / "events.jsonl"
    events.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in c.component_rows), encoding="utf-8", newline="\n")
    global_root = g.P / f"results/{g.SCHEMA}/component_compatibility_invocations/{c.job['job_id']}"
    copied_root = g.P / c.relative / "component_compatibility" / c.job["job_id"]
    c.completion["component_artifacts"] = [dict(source=str(global_root / name), path=str(copied_root / name),
        sha256=sha(c.component_dir / name), bytes=(c.component_dir / name).stat().st_size) for name in g.ARTIFACT_NAMES[:2]]
    save(c.component_dir / "completion.json", c.completion)
    refresh_pull(c)


def review(c, *, evidence=None):
    evidence = evidence or c.shared.Evidence(c.root)
    metadata = c.shared.review_runtime_compatibility(evidence, job=c.job, invocation=c.invocation,
        receipt=c.receipt, inventory=c.inventory, pull_receipt=c.pull)
    result = c.shared.review_component_compatibility(evidence, job=c.job, invocation=c.invocation,
        receipt=c.receipt, inventory=c.inventory, metadata_review=metadata, pull_receipt=c.pull)
    evidence.unchanged()
    return metadata, result


@pytest.mark.parametrize("stage", ["acceptance", "train"])
def test_exact_two_component_proofs_and_saved_root_review(project, stage):
    c = make_case(project, stage)
    metadata, result = review(c)
    assert result["status"] == "verified" and result["exact_component_loads"] == 2
    assert len(result["required_pulled_files"]) == 3 and result["component_compatibility"] == c.component
    saved = dict(component_compatibility=c.component, component_compatibility_review=result)
    assert c.shared.require_saved_component_review(c.shared.Evidence(c.root), saved=saved, job=c.job,
        inventory=c.inventory, metadata_review=metadata) == result


@pytest.mark.parametrize("change", ["missing_contract", "wrong_job_contract", "wrong_suite", "extra_file", "missing_event",
    "wrong_order", "wrong_mapping", "wrong_size", "wrong_target", "wrong_call", "empty_state", "not_restored",
    "code_changed", "torch_changed", "target_changed", "rejected_request", "runner_raised", "failure_status",
    "inner_receipt_sha", "metadata_artifact_sha", "metadata_contract", "fake_copy_path", "fake_bytes", "out_of_runner"])
def test_invalid_component_proof_rejected_even_after_valid_pull_hashes(project, change):
    c = make_case(project)
    if change == "missing_contract": c.invocation.pop("component_compatibility")
    elif change == "wrong_job_contract": c.job.pop("component_compatibility")
    elif change == "wrong_suite": c.completion["suite"] = "libero_object"
    elif change == "extra_file": c.component["files"]["unexpected.py"] = "0" * 64
    elif change == "missing_event": c.component_rows.pop(6)
    elif change == "wrong_order": c.component_rows[3], c.component_rows[5] = c.component_rows[5], c.component_rows[3]
    elif change == "wrong_mapping": c.component_rows[3]["mapping"] = deepcopy(c.component_rows[5]["mapping"])
    elif change == "wrong_size": c.component_payload["identity"]["mappings"][0]["size"] += 1
    elif change == "wrong_target": c.component_payload["identity"]["mappings"][0]["target_path"] = "/elsewhere/head.pt"
    elif change == "wrong_call": c.component_rows[6]["call_id"] = 0
    elif change == "empty_state": c.component_rows[4]["state_tensor_count"] = 0
    elif change == "not_restored": c.component_rows[8]["original_loader_restored"] = False
    elif change == "code_changed": c.component_rows[8]["original_function_codes_unchanged"] = False
    elif change == "torch_changed": c.component_rows[8]["torch_load_unchanged"] = False
    elif change == "target_changed": c.component_rows[8]["component_files_unchanged"] = False
    elif change == "rejected_request": c.component_rows[8]["rejected_calls"] = 1
    elif change == "runner_raised": c.component_rows[8]["runner_raised"] = True
    elif change == "failure_status": c.completion["status"] = "failed"
    elif change == "inner_receipt_sha": c.completion["inner_job_receipt"]["sha256"] = "0" * 64
    elif change == "metadata_artifact_sha": c.completion["metadata_artifacts"][0]["sha256"] = "0" * 64
    elif change == "metadata_contract": c.completion["runtime_compatibility"] = dict(synthetic_wrong=True)
    elif change == "out_of_runner": c.component_rows[3]["utc"] = "2026-10-17T00:00:01.500000+00:00"
    seal_component(c)
    if change == "fake_copy_path": c.completion["component_artifacts"][0]["path"] = "/unregistered/identity.json"
    if change == "fake_bytes": c.completion["component_artifacts"][0]["bytes"] += 1
    if change in ("fake_copy_path", "fake_bytes"):
        save(c.component_dir / "completion.json", c.completion); refresh_pull(c)
    with pytest.raises(ValueError):
        review(c)


def test_source_proof_allows_server_bytecode_and_excludes_mutable_parent_reads(project):
    c = make_case(project)
    # Valid, deliberately different opaque same-runtime fingerprints; no local
    # Python3.10 versus server3.11 bytecode equality is inferred.
    codes = {name: hashlib.sha256(("synthetic-other-python-runtime:" + name).encode()).hexdigest() for name in c.g.SYMBOLS}
    c.component_payload["identity"]["original_function_code_sha256"] = codes
    c.component_rows[1]["identity"]["original_function_code_sha256"] = codes
    seal_component(c)
    mutable = "results/experiment_supervisor/state.json"
    save(c.root / mutable, dict(synthetic_mutable_parent_state=True))
    evidence = c.shared.Evidence(c.root); evidence.read(mutable)
    _, result = review(c, evidence=evidence)
    assert mutable not in result["evidence_sha256"]
    assert all(c.shared.sha(c.root / name) == checksum for name, checksum in result["evidence_sha256"].items())
    assert result["helper_sha256"] == sha(c.root / HELPER)
    save(c.root / mutable, dict(synthetic_mutable_parent_state="changed after completed review"))
    assert all(sha(c.root / name) == checksum for name, checksum in result["evidence_sha256"].items())


def test_metadata_only_goal_success_cannot_skip_component_proof(project):
    c = project.old.make_case(project, "libero_goal", "acceptance")
    evidence = c.shared.Evidence(c.root)
    metadata = c.shared.review_runtime_compatibility(evidence, job=c.job, invocation=c.invocation,
        receipt=c.receipt, inventory=c.inventory, pull_receipt=c.pull)
    assert metadata["status"] == "verified"
    with pytest.raises(ValueError, match="requires exact component_compatibility"):
        c.shared.review_component_compatibility(evidence, job=c.job, invocation=c.invocation,
            receipt=c.receipt, inventory=c.inventory, metadata_review=metadata, pull_receipt=c.pull)


def test_component_journal_partial_tail_cannot_be_rehashed_as_success(project):
    c = make_case(project)
    path = c.component_dir / "events.jsonl"
    path.write_bytes(path.read_bytes().rstrip(b"\n"))
    c.completion["component_artifacts"][1].update(sha256=sha(path), bytes=path.stat().st_size)
    save(c.component_dir / "completion.json", c.completion); refresh_pull(c)
    with pytest.raises(ValueError, match="unterminated"):
        review(c)


@pytest.mark.parametrize("suite", ["libero_object", "libero_spatial", "libero_10"])
def test_other_suites_unchanged_and_forbid_goal_contract_without_io(project, suite):
    class NoIO:
        def __getattr__(self, key): pytest.fail("Non-Goal component branch attempted I/O: " + key)
    assert project.g.review_job(NoIO(), job=dict(suite=suite), invocation={}, receipt={}, inventory={}, metadata_review=None) is None
    with pytest.raises(ValueError, match="Goal only"):
        project.g.review_job(NoIO(), job=dict(suite=suite, component_compatibility={}), invocation={}, receipt={}, inventory={}, metadata_review=None)


@pytest.fixture(scope="module")
def actual_writer_project(tmp_path_factory):
    writer = load("tests/test_formal_goal_component_stage.py", "actual_goal_writer_for_root_review")
    actual = writer.project.__wrapped__(tmp_path_factory)
    old = load("tests/test_formal_asset_compat_review.py", "actual_goal_metadata_transport")
    goal = load(HELPER, "actual_goal_review_helper")
    metadata = load(goal.METADATA_HELPER, "actual_goal_preserved_metadata_helper")
    normalized = tmp_path_factory.mktemp("synthetic_goal_server_transport")
    inventory = read(ROOT / goal.SOURCE_INVENTORY)
    for name in inventory["files"]:
        target = normalized / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(actual.source / name, target)
    for name in [HELPER, goal.METADATA_HELPER, goal.SOURCE_INVENTORY, *writer.NEW, *actual.helper.SUPPORT]:
        original = ROOT / name if name in (HELPER, goal.METADATA_HELPER, goal.SOURCE_INVENTORY) else actual.project / name
        target = normalized / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
    before = {name: sha(ROOT / name) for name in [*inventory["files"], goal.METADATA_HELPER, *writer.NEW, *actual.helper.SUPPORT]}
    yield SimpleNamespace(root=normalized, g=goal, m=metadata, old=old, writer=writer, actual=actual,
        shared=load("scripts/review_formal_acceptance.py", "actual_goal_shared_root_review"), inventory=inventory)
    assert {name: sha(ROOT / name) for name in before} == before


def transport_writer(project, case):
    """Preserve raw writer bytes; explicit synthetic Windows→POSIX transport.

    Producer fixture substitutes the GPU runner and only the official-component
    target I/O boundary, while real torch.load reads two tiny synthetic files.
    Both wrapper/adapter writers and both root proof validators execute as-is.
    """
    receipt = read(case.receipt)
    c = project.old.transport_actual_writer(project, case, receipt)
    g, actual = project.g, project.actual
    original_root = actual.project.as_posix()
    def translate(value):
        if isinstance(value, dict): return {translate(key): translate(item) for key, item in value.items()}
        if isinstance(value, list): return [translate(item) for item in value]
        if isinstance(value, str):
            normalized = value.replace("\\", "/")
            if normalized == original_root or normalized.startswith(original_root + "/"):
                return str(g.P) + normalized[len(original_root):]
        return value
    source_dir = case.output / "component_compatibility" / case.job
    originals = {str(source_dir / name): sha(source_dir / name) for name in g.ARTIFACT_NAMES}
    c.component = c.invocation["component_compatibility"]
    c.job["component_compatibility"] = c.component
    c.component_payload = translate(read(source_dir / "identity.json"))
    c.component_rows = translate([json.loads(line) for line in (source_dir / "events.jsonl").read_text().splitlines()])
    c.completion = translate(read(source_dir / "completion.json"))
    c.component_dir = c.root / c.relative / "component_compatibility" / case.job
    inv_sha, inventory_sha = c.job["invocation_sha256"], sha(c.root / g.SOURCE_INVENTORY)
    c.component_payload["invocation_sha256"] = c.completion["invocation_sha256"] = inv_sha
    for identity in [c.component_payload["identity"], *(row["identity"] for row in c.component_rows if row["event"] == "goal_component_compat_enter")]:
        identity["source_inventory_sha256"] = inventory_sha
        identity["watched_files"][str(g.P / g.SOURCE_INVENTORY)] = inventory_sha
    receipt_path = c.root / f"results/{g.SCHEMA}/job_receipts/{case.job}.json"
    receipt_ref = dict(path=str(g.P / receipt_path.relative_to(c.root).as_posix()), sha256=sha(receipt_path), bytes=receipt_path.stat().st_size)
    for row in c.component_rows:
        row["invocation_sha256"] = inv_sha
        if "inner_job_receipt" in row: row["inner_job_receipt"] = deepcopy(receipt_ref)
        if "metadata_artifacts" in row: row["metadata_artifacts"] = deepcopy(c.receipt["compatibility_artifacts"])
    c.completion.update(inner_job_receipt=deepcopy(receipt_ref), metadata_artifacts=deepcopy(c.receipt["compatibility_artifacts"]))
    seal_component(c)
    assert all(sha(path) == checksum for path, checksum in originals.items())
    save(c.component_dir.parent / "synthetic_goal_transport.json", dict(synthetic=True, scientific_runner_executed=False,
        official_weights_loaded=False, raw_component_files_sha256=originals, path_mapping={original_root: str(g.P)},
        substitutions=["GPU runner", "official component target I/O boundary mapped to tiny real tensors"],
        rebindings=["inventory", "invocation", "metadata identity/events/receipt", "component identity/events/completion", "pull"],
        review_mocks=False))
    return c


@pytest.mark.parametrize("stage", ["acceptance", "train"])
def test_actual_outer_inner_writers_to_pull_and_root_saved_review(actual_writer_project, stage):
    p = actual_writer_project
    case = p.writer.new_case(p.actual, stage=stage)
    p.writer.run_case(p.actual, case)
    c = transport_writer(p, case)
    metadata, result = review(c)
    assert result["status"] == "verified" and result["exact_component_loads"] == 2
    saved = dict(component_compatibility=c.component, component_compatibility_review=result)
    assert c.shared.require_saved_component_review(c.shared.Evidence(c.root), saved=saved, job=c.job,
        inventory=c.inventory, metadata_review=metadata) == result
    assert result["cost_scope"] == c.g.COST_SCOPE


def test_actual_successful_inner_but_zero_component_outer_is_rejected(actual_writer_project):
    p = actual_writer_project
    case = p.writer.new_case(p.actual)
    completion = p.writer.run_case(p.actual, case, behavior="zero", expected=1)
    assert read(case.receipt)["status"] == "returned" and completion["status"] == "failed"
    c = transport_writer(p, case)
    with pytest.raises(ValueError):
        review(c)

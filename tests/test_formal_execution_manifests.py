"""Metadata-only manifest/release tests; all evidence and states are synthetic."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from cti_vla.evaluation import formal_runtime as runtime, formal_trials as trials
from cti_vla.evaluation.teacher_diagnostics import json_signature
from test_formal_deployment import pair_fixture, synthetic_panel


def load_tool():
    path = Path(__file__).resolve().parents[1] / "scripts/formal_execution_manifests.py"
    spec = importlib.util.spec_from_file_location("formal_execution_test_tool", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def tool():
    return load_tool()


def save(tool, path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(tool.encoded(value))
    return path


@pytest.fixture
def project(tmp_path, monkeypatch, tool):
    """Core receipt/ledger regression; GPU and new operational root proofs are isolated.

    The separate asset-consumer suite exercises the real provenance/audit
    boundary. These historical synthetic5000 records are not actual root jobs.
    """
    sources = {"src/cti_vla/training/formal_future.py": "a" * 64}
    registration = dict(schema=tool.SCHEMA, suites={}, pairs=[])
    gates = {}
    selector_identities = []
    for suite in runtime.FORMAL_SUITES:
        state_root = f"configs/manifests/formal_main_v2/{suite}/initial_states"
        panel = synthetic_panel(suite)
        registry, _ = synthetic_panel(suite, "final")
        save(tool, tmp_path / state_root / "development.json", panel)
        save(tool, tmp_path / state_root / "final_registry.json", registry)
        # This sentinel is deliberately invalid JSON and must never be accessed.
        (tmp_path / state_root / "sealed_final.json").write_text("NEVER READ THIS SENTINEL")
        registration["suites"][suite] = dict(initial_states_root=state_root, model_revision="synthetic-base")
        gate_root = tmp_path / f"results/formal_main_v2/{suite}/acceptance/attempt01"
        f00_path = save(tool, gate_root / "input_acceptance.json", dict(frozen_model_sha256="b" * 64))
        f01s = {k: save(tool, gate_root / f"f01_k{k}.json", dict(synthetic=True, visual_tokens=k)) for k in runtime.FORMAL_BUDGETS}
        gates[suite] = dict(f00=dict(frozen_model_sha256="b" * 64), f00_path=f00_path,
            f00_sha=tool.digest(f00_path), f01s=f01s, resume_sha="c" * 64, resume_journal_sha="d" * 64,
            window_sha="e" * 64, protocol_sha="f" * 64)
        save(tool, gate_root.parent / "root_review.json", dict(status="synthetic_gate_replaced_by_fixture"))
        for total in runtime.FORMAL_BUDGETS:
            for seed in runtime.FORMAL_SEEDS:
                pair = pair_fixture(suite=suite, total=total, seed=seed)
                pair_rel = f"configs/experiments/formal_main_v2/{suite}_k{total}_seed{seed}.json"
                save(tool, tmp_path / pair_rel, pair)
                run_relative = f"results/formal_main_v2/{suite}/k{total}/seed{seed}"
                entry = dict(suite=suite, visual_tokens=total, seed=seed, path=pair_rel,
                    sha256=tool.digest(tmp_path / pair_rel), run_root_server=str(tool.P / run_relative),
                    checkpoint_root_server=str(tool.H / f"checkpoints/formal_main_v2/{suite}/k{total}/seed{seed}"))
                registration["pairs"].append(entry)
                training = tmp_path / run_relative / "training"
                save(tool, training / "registered_config.json", pair)
                reports = {}
                gate = gates[suite]
                for arm in ("A", "B"):
                    config = {**pair, "arm": arm}
                    metadata = runtime.make_formal_checkpoint_metadata(arm=arm, seed=seed,
                        scorer_dimensions=pair["scorer_dimensions"], training_config=config, pair_config=pair,
                        window_manifest_sha256=gate["window_sha"], model_revision=pair["model_revision"], stats_key=pair["stats_key"],
                        training_source_files=sources, update=500, validation_metric=.1, input_acceptance_sha256=gate["f00_sha"],
                        frozen_model_sha256=gate["f00"]["frozen_model_sha256"], data_protocol_sha256=gate["protocol_sha"],
                        selection_protocol_sha256=json_signature(pair["selection"]), training_complete=True)
                    evaluations = [dict(update=u, validation_metric=.2 if u == 0 else .1) for u in runtime.FORMAL_EVALUATION_UPDATES]
                    # Never create/read a checkpoint. This is the production non-weight receipt shape.
                    checkpoint_sha = json_signature(dict(suite=suite, total=total, seed=seed, arm=arm))
                    receipt = dict(schema=runtime.FORMAL_SCHEMA, kind="deployment_receipt", metadata=metadata,
                        metadata_sha256=json_signature(metadata), checkpoint_sha256=checkpoint_sha,
                        training_config=config, pair_config=pair, f01_report_sha256=tool.digest(f01s[total]),
                        planned_updates=5000, completed_updates=5000, evaluations=evaluations,
                        training_complete=True, base_frozen=True, checkpoint_unchanged=True)
                    runtime.validate_formal_receipt(receipt, metadata)
                    selector_identities.append(trials.selector_instance_identity({**metadata,
                        "selector_checkpoint_sha256": checkpoint_sha, "deployment_receipt_sha256": json_signature(receipt),
                        "f01_report_sha256": receipt["f01_report_sha256"]}))
                    save(tool, training / arm / "deployment_receipt.json", receipt)
                    identity = dict(pair_config_sha256=json_signature(pair), training_config_sha256=metadata["config_sha256"],
                        training_source_files=sources, window_manifest_sha256=gate["window_sha"], data_protocol_sha256=gate["protocol_sha"],
                        input_acceptance_sha256=gate["f00_sha"], f01_report_sha256=tool.digest(f01s[total]),
                        frozen_model_sha256=metadata["frozen_model_sha256"], resume_acceptance_sha256=gate["resume_sha"],
                        resume_journal_sha256=gate["resume_journal_sha"])
                    report = dict(schema=runtime.FORMAL_SCHEMA, status="completed", arm=arm, identity=identity,
                        training_updates_completed=5000, committed_samples=40000, next_sample_cursor=40000,
                        evaluations=evaluations, best_update=500, best_validation_metric=.1,
                        best_checkpoint=str(tool.PurePosixPath(entry["checkpoint_root_server"]) / arm / "best.pt"),
                        best_checkpoint_sha256=checkpoint_sha, frozen_model_sha256=metadata["frozen_model_sha256"],
                        vla_parameters_unchanged=True, initial_scorer_sha256="1" * 64, sample_order_sha256="2" * 64)
                    reports[arm] = report
                    save(tool, training / arm / "training_report.json", report)
                summary = dict(schema=runtime.FORMAL_SCHEMA, status="completed", pair_complete=True,
                    checkpoint_unchanged=True, test_opened=False, planned_updates_per_arm=5000, source_files=sources,
                    arms=reports, job_id="100")
                save(tool, training / "training_summary.json", summary)
                save(tool, training / "finalizations/synthetic.json", dict(status="verified", kind="training",
                    result_status="completed", checkpoint_unchanged=True, result_sha256=tool.digest(training / "training_summary.json"),
                    source_files=sources, job_id="100"))
    save(tool, tmp_path / tool.REGISTRATION, registration)
    import hashlib
    from datetime import datetime, timezone
    files = {**sources, tool.REGISTRATION: tool.digest(tmp_path / tool.REGISTRATION),
        **{row["path"]: row["sha256"] for row in registration["pairs"]}}
    source_info = dict(schema=tool.SCHEMA, files=files,
        source_sha256=hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
        source_root_server=str(tool.P / "snapshots/formal_main_v2_run_synthetic"))
    save(tool, tmp_path / "source_inventory.json", source_info)
    index = {(row["suite"], row["method_id"]): row for row in selector_identities}
    checkpoint_receipt = dict(schema=tool.SCHEMA, kind="server_checkpoint_inventory", status="verified",
        execution="linux_server_cpu_read_only_hash", created_utc=datetime.now(timezone.utc).isoformat(),
        server_project_root=str(tool.P), gpu_used=False, test_opened=False,
        registration_sha256=json_signature(registration), registration_file_sha256=tool.digest(tmp_path / tool.REGISTRATION),
        source_inventory="source_inventory.json", source_inventory_file_sha256=tool.digest(tmp_path / "source_inventory.json"),
        source_sha256=source_info["source_sha256"], source_root_server=source_info["source_root_server"],
        source_files_sha256=json_signature(sources), checker_source_sha256=tool.digest(tool.__file__), required_checkpoints=72,
        checkpoints=[{**row, "checkpoint_sha256": index[(row["suite"], row["method_id"])]["checkpoint_sha256"],
            "exists": True, "bytes": 1024, "stable_during_hash": True, "mtime_ns_before": 1, "mtime_ns_after": 1}
            for row in tool.checkpoint_specs(registration)])
    save(tool, tmp_path / "checkpoint_inventory.json", checkpoint_receipt)
    def accepted(evidence, reg, suite, actual_sources):
        assert actual_sources == sources
        gate = gates[suite]
        for path in [gate["f00_path"], *gate["f01s"].values()]:
            evidence.watch(path)
        return gate
    monkeypatch.setattr(tool, "load_suite_acceptance", accepted)
    def source_proof(evidence, reg, suite, rows, **kwargs):
        value = dict(schema=tool.SCHEMA, kind="asset_downstream_source_provenance", status="verified", suite=suite,
            helper_sha256=tool.SOURCE_REVIEW_SHA256, shared_projection=dict(suite=suite, synthetic=True),
            method_bindings={row["identity"]["method_id"]: dict(suite=suite,
                method_id=row["identity"]["method_id"], identity=row["identity"]) for row in rows},
            evidence_sha256={name: checksum for name, checksum in evidence.files.items()
                if not name.startswith("results/formal_main_v2/downstream_reviews/")},
            registered_source_jobs=[], scientific_gates_replaced=False)
        evidence.source_provenance[suite] = value
        return value
    monkeypatch.setattr(tool, "source_provenance_for_rows", source_proof)
    def root_review(evidence, reference, *, expected_stage, suite, run_root=None):
        assert expected_stage == "development"
        assert evidence.watch(reference["path"]) == reference["sha256"]
        value = evidence.read(reference["path"])
        assert value["synthetic_operational_gate_stub"] is True
        return value
    monkeypatch.setattr(tool, "review_downstream_output", root_review)
    return SimpleNamespace(root=tmp_path, tool=tool, sources=sources, registration=registration, gates=gates,
        selector_identities=selector_identities)


def write_development_runs(project):
    t, root, registration = project.tool, project.root, project.registration
    index = dict(schema=t.SCHEMA, kind="development_output_index", suites={}, root_reviews={})
    for suite in runtime.FORMAL_SUITES:
        ev = t.Evidence(root)
        rows = t.suite_rows(ev, registration, suite, project.sources, trials.expected_method_ids())
        manifest = t.make_execution(registration, suite, rows)
        panel = json.loads((root / registration["suites"][suite]["initial_states_root"] / "development.json").read_text())
        config = dict(manifest=manifest, panel_signature=json_signature(panel))
        signature = json_signature(config)
        relative = f"results/formal_main_v2/{suite}/development/all22"
        directory = root / relative
        save(t, directory / "config.json", config)
        save(t, directory / "panel.json", panel)
        events, completed = [], {}
        for state in panel["states"]:
            for mid in trials.expected_method_ids():
                identity = trials._identity(panel, state, mid)
                events.append(dict(**identity, event="start", run_signature=signature))
                result = dict(**identity, event="result", run_signature=signature, status="completed", success=False, policy_calls=1)
                events.append(result)
                completed[identity["trial_id"]] = result
        path = directory / "trials.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in events), encoding="utf-8")
        ledger = SimpleNamespace(path=path, events=events, completed=lambda: completed)
        report = trials.summarize_formal_trials(panel, trials.expected_method_ids(), ledger,
            provenance={"run_signature": signature}, checkpoint_unchanged=True)
        save(t, directory / "closed_loop_report.json", report)
        index["suites"][suite] = [relative]
        review_path = f"results/formal_main_v2/downstream_reviews/synthetic_{suite}.json"
        save(t, root / review_path, dict(synthetic_operational_gate_stub=True, run_root=str(t.P / relative),
            job_id="100", source_provenance=ev.source_provenance[suite], completed_trials=2200,
            cost=dict(allocations=[])))
        index["root_reviews"][suite] = [dict(path=review_path, sha256=t.digest(root / review_path))]
    save(t, root / "development_index.json", index)
    return index


def test_receipt_constructs_server_identity_without_accessing_any_weight(project, monkeypatch):
    t = project.tool
    def forbidden(*args, **kwargs):
        raise AssertionError("No model/checkpoint loader is allowed in this local metadata tool")
    monkeypatch.setattr(runtime, "load_formal_selector_checkpoint", forbidden)
    import torch
    monkeypatch.setattr(torch, "load", forbidden)
    ev = t.Evidence(project.root)
    rows = t.suite_rows(ev, project.registration, "libero_10", project.sources,
        ["dense", "uniform256", "A128_seed17", "B128_seed17"])
    assert [row["identity"]["method_id"] for row in rows] == ["dense", "uniform256", "A128_seed17", "B128_seed17"]
    assert all(row["checkpoint"].startswith(str(t.H)) for row in rows if "checkpoint" in row)
    assert not any(name.endswith(".pt") for name in ev.files)
    trials.validate_execution_manifest(t.make_execution(project.registration, "libero_10", rows),
        registration_sha256=json_signature(project.registration))


@pytest.mark.parametrize("change", ["partial", "later_tie", "wrong_hash", "f03", "pair_order", "missing_finalization"])
def test_development_rejects_incomplete_or_mismatched_training(project, change):
    t = project.tool
    entry = next(p for p in project.registration["pairs"] if (p["suite"], p["visual_tokens"], p["seed"]) == ("libero_10", 128, 17))
    directory = t.pair_directory(t.Evidence(project.root), entry)
    receipt_path, report_path = directory / "A/deployment_receipt.json", directory / "A/training_report.json"
    receipt, report = json.loads(receipt_path.read_text()), json.loads(report_path.read_text())
    if change == "partial":
        receipt["completed_updates"] = 500
    elif change == "later_tie":
        receipt["metadata"]["update"] = 1000
        receipt["metadata_sha256"] = json_signature(receipt["metadata"])
    elif change == "wrong_hash":
        report["best_checkpoint_sha256"] = "0" * 64
    elif change == "f03":
        report["identity"]["resume_acceptance_sha256"] = "0" * 64
    elif change == "pair_order":
        report["sample_order_sha256"] = "3" * 64
        summary_path = directory / "training_summary.json"
        summary = json.loads(summary_path.read_text())
        summary["arms"]["A"] = report
        save(t, summary_path, summary)
    else:
        (directory / "finalizations/synthetic.json").unlink()
    save(t, receipt_path, receipt)
    save(t, report_path, report)
    with pytest.raises(ValueError):
        t.selected_pair(t.Evidence(project.root), entry, project.gates["libero_10"], project.sources)


def test_missing_formal_receipts_report_all_missing_and_never_freeze(project):
    t = project.tool
    names = []
    for pair in project.registration["pairs"][:2]:
        path = t.pair_directory(t.Evidence(project.root), pair) / "A/deployment_receipt.json"
        names.append(path.relative_to(project.root).as_posix())
        path.unlink()
    with pytest.raises(t.MissingEvidence) as error:
        t.build_global(t.Evidence(project.root), project.registration, project.sources, "not-needed.json", "freeze",
            checkpoint_inventory="checkpoint_inventory.json")
    assert set(names) <= set(error.value.missing)
    assert not (project.root / "freeze").exists()


def test_complete_matrix_raw8800_and_explicit_release_never_read_sealed_values(project, monkeypatch):
    t = project.tool
    write_development_runs(project)
    real_open = Path.open
    def guarded_open(path, *args, **kwargs):
        assert "sealed_final" not in path.name and path.suffix not in t.WEIGHT_SUFFIXES
        return real_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded_open)
    matrix = t.build_global(t.Evidence(project.root), project.registration, project.sources, "development_index.json", "freeze",
        checkpoint_inventory="checkpoint_inventory.json")
    assert len(matrix["instances"]) == 88
    assert sum(row["method"] in ("A", "B") for row in matrix["instances"]) == 72
    assert matrix["server_checkpoint_inventory_sha256"] == t.digest(project.root / "checkpoint_inventory.json")
    evidence_record = json.loads((project.root / "freeze/freeze_evidence.json").read_text())
    assert matrix["evidence_files_sha256"] == json_signature(evidence_record["files"])
    for suite in runtime.FORMAL_SUITES:
        receipt = json.loads((project.root / "freeze/development_completion" / (suite + ".json")).read_text())
        assert receipt["completed_trials"] == 2200 and receipt["unique_initial_states"] == 100
    assert not (project.root / "freeze/root_release.json").exists()
    result = t.release_global(t.Evidence(project.root), project.registration, "freeze")
    assert result["status"] == "verified_not_released"
    assert not (project.root / "freeze/root_release.json").exists()
    result = t.release_global(t.Evidence(project.root), project.registration, "freeze", release=True, created_utc="synthetic-root-time")
    assert result["status"] == "root_released" and result["final_values_read"] is False
    assert len(list((project.root / "freeze/final_execution").glob("*.json"))) == 4
    release = json.loads((project.root / "freeze/root_release.json").read_text())
    trials.validate_final_release(release, matrix, registration_sha256=json_signature(project.registration))
    # An unchanged explicit rerun is idempotent and retains the original root timestamp.
    assert t.release_global(t.Evidence(project.root), project.registration, "freeze", release=True)["release_file_sha256"] == result["release_file_sha256"]


def test_raw_development_not_summary_claim_controls_freeze(project):
    t = project.tool
    index = write_development_runs(project)
    path = project.root / index["suites"]["libero_10"][0] / "trials.jsonl"
    lines = path.read_text().splitlines()
    event = json.loads(lines[-1]);event["success"] = True
    lines[-1] = json.dumps(event)
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="durable raw"):
        t.build_global(t.Evidence(project.root), project.registration, project.sources, "development_index.json", "freeze",
            checkpoint_inventory="checkpoint_inventory.json")
    assert not (project.root / "freeze/global_freeze.json").exists()


def test_changed_evidence_blocks_release_and_preserves_existing_freeze(project):
    t = project.tool
    write_development_runs(project)
    t.build_global(t.Evidence(project.root), project.registration, project.sources, "development_index.json", "freeze",
        checkpoint_inventory="checkpoint_inventory.json")
    entry = project.registration["pairs"][0]
    path = t.pair_directory(t.Evidence(project.root), entry) / "A/deployment_receipt.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="bytes changed"):
        t.release_global(t.Evidence(project.root), project.registration, "freeze", release=True)
    assert not (project.root / "freeze/root_release.json").exists()


@pytest.mark.parametrize("value", ["sealed_final.json", "x/sealed_final.json", "a.pt", "a.safetensors", "../outside.json"])
def test_forbidden_input_is_rejected_before_any_io(tool, tmp_path, value, monkeypatch):
    def no_io(*args, **kwargs):
        pytest.fail("Forbidden input reached filesystem I/O")
    monkeypatch.setattr(Path, "open", no_io)
    with pytest.raises(ValueError):
        tool.Evidence(tmp_path).read(value)


def test_actual_failed_suite_review_cannot_generate_even_dense(tool, tmp_path):
    review = "results/formal_main_v2/libero_10/acceptance/root_review.json"
    save(tool, tmp_path / review, dict(status="failed", output_relative="results/formal_main_v2/libero_10/acceptance/attempt01", job_id="100"))
    with pytest.raises(ValueError, match="explicit root review"):
        tool.load_suite_acceptance(tool.Evidence(tmp_path), {"suites": {"libero_10": {}}}, "libero_10", {})


def test_actual_missing_f03_evidence_cannot_generate_dense(tool, tmp_path):
    base = "results/formal_main_v2/libero_10/acceptance/attempt01"
    save(tool, tmp_path / "results/formal_main_v2/libero_10/acceptance/root_review.json",
        dict(status="passed", output_relative=base, job_id="100", files={}))
    for name in ("input_acceptance.json", "input_calls.jsonl", "operator_calls.jsonl", "acceptance_complete.json",
            "f01_k128.json", "f01_k256.json", "f01_k64.json"):
        save(tool, tmp_path / base / name, {})
    with pytest.raises(tool.MissingEvidence) as error:
        tool.load_suite_acceptance(tool.Evidence(tmp_path), {"suites": {"libero_10": {}}}, "libero_10", {})
    assert any(name.endswith("resume_acceptance.json") for name in error.value.missing)
    assert any(name.endswith("f03_calls.jsonl") for name in error.value.missing)


def test_immutable_artifact_refuses_rewrite(tool, tmp_path):
    path = tmp_path / "manifest.json"
    tool.immutable_write(path, {"a": 1})
    tool.immutable_write(path, {"a": 1})
    with pytest.raises(ValueError, match="overwrite"):
        tool.immutable_write(path, {"a": 2})
    assert json.loads(path.read_text()) == {"a": 1}


def test_frozen_inventory_also_binds_registration_bytes(tool, tmp_path, monkeypatch):
    import hashlib
    from cti_vla.training import formal_future
    source_path = tmp_path / "src/producer.py"
    source_path.parent.mkdir(parents=True)
    source_path.write_text("# synthetic frozen producer\n")
    registration_path = save(tool, tmp_path / tool.REGISTRATION, dict(schema=tool.SCHEMA))
    sources = {"src/producer.py": tool.digest(source_path)}
    files = {**sources, tool.REGISTRATION: tool.digest(registration_path)}
    save(tool, tmp_path / "inventory.json", dict(schema=tool.SCHEMA, files=files,
        source_sha256=hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
        source_root_server=str(tool.P / "snapshots/formal_main_v2_run_synthetic")))
    monkeypatch.setattr(formal_future, "formal_source_hashes", lambda _: sources)
    assert tool.source_contract(tool.Evidence(tmp_path), "inventory.json") == sources
    registration_path.write_bytes(registration_path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="after GPU source freeze"):
        tool.source_contract(tool.Evidence(tmp_path), "inventory.json")


@pytest.mark.parametrize("change", ["pair_bytes", "server_weights", "missing_pair"])
def test_registration_requires_all36_exact_pairs_and_server_only_weights(project, change):
    t, reg = project.tool, deepcopy(project.registration)
    if change == "pair_bytes":
        pair_path = project.root / reg["pairs"][0]["path"]
        pair_path.write_bytes(pair_path.read_bytes() + b" ")
    elif change == "server_weights":
        reg["pairs"][0]["checkpoint_root_server"] = str(project.root / "local_weights")
    else:
        reg["pairs"].pop()
    save(t, project.root / t.REGISTRATION, reg)
    with pytest.raises(ValueError):
        t.registration_contract(t.Evidence(project.root), t.REGISTRATION)


@pytest.mark.parametrize("change", ["missing", "duplicate", "path", "hash", "absent", "unstable", "stale", "source"])
def test_checkpoint_inventory_requires72_fresh_exact_server_hashes(project, change):
    t = project.tool
    path = project.root / "checkpoint_inventory.json"
    report = json.loads(path.read_text())
    t.validate_checkpoint_inventory(t.Evidence(project.root), path, project.registration, project.sources, project.selector_identities)
    if change == "missing":
        report["checkpoints"].pop()
    elif change == "duplicate":
        report["checkpoints"][-1] = report["checkpoints"][0]
    elif change == "path":
        report["checkpoints"][0]["checkpoint"] = str(t.H / "checkpoints/formal_main_v2/engineering/libero_10/probe.pt")
    elif change == "hash":
        report["checkpoints"][0]["checkpoint_sha256"] = "0" * 64
    elif change == "absent":
        report["checkpoints"][0]["exists"] = False
    elif change == "unstable":
        report["checkpoints"][0]["mtime_ns_after"] = 2
    elif change == "stale":
        report["created_utc"] = "2000-01-01T00:00:00+00:00"
    else:
        report["source_files_sha256"] = "0" * 64
    save(t, path, report)
    with pytest.raises(ValueError):
        t.validate_checkpoint_inventory(t.Evidence(project.root), path, project.registration, project.sources, project.selector_identities)


def test_server_checker_rejects_local_execution_before_weight_access(tool, tmp_path, monkeypatch):
    monkeypatch.setattr(tool, "hash_checkpoint_paths", lambda *a, **k: pytest.fail("Local checker accessed server weights"))
    with pytest.raises(ValueError, match="server-only"):
        tool.server_checkpoint_inventory(tool.Evidence(tmp_path), {}, "missing_inventory.json", "output.json")


def test_server_hash_primitive_detects_missing_and_mutating_synthetic_bytes(tool, tmp_path, monkeypatch):
    # Tiny synthetic byte fixtures, not model parameters or downloaded weights.
    path = tmp_path / "registered/best.pt"
    path.parent.mkdir()
    path.write_bytes(b"synthetic-byte-fixture")
    rows = tool.hash_checkpoint_paths([path], allowed_root=tmp_path)
    assert rows[0]["checkpoint_sha256"] == tool.digest(path) and rows[0]["exists"]
    with pytest.raises(tool.MissingEvidence):
        tool.hash_checkpoint_paths([path, tmp_path / "registered/missing.pt"], allowed_root=tmp_path)
    original = tool.digest
    def mutate(value):
        checksum = original(value)
        Path(value).write_bytes(b"different-synthetic-byte-fixture")
        return checksum
    monkeypatch.setattr(tool, "digest", mutate)
    with pytest.raises(ValueError, match="changed"):
        tool.hash_checkpoint_paths([path], allowed_root=tmp_path)

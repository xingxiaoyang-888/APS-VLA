"""CPU-only compatibility evidence; never load real checkpoints or final states."""
from contextlib import nullcontext
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

from cti_vla.evaluation import formal_trials, future_profiling, libero_runtime
from cti_vla.training.formal_future import formal_source_hashes
from test_formal_deployment import synthetic_panel, freeze_fixture

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/ops/formal_evaluation_adapter.py"
spec = importlib.util.spec_from_file_location("formal_adapter_under_test", SCRIPT)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
INVENTORY = ROOT / "results/formal_main_v2/source" / (adapter.FROZEN_SNAPSHOT + ".json")


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


@pytest.fixture(scope="module", autouse=True)
def immutable_source_evidence():
    inventory = adapter.read(INVENTORY)
    before = {name: adapter.digest(ROOT / name) for name in inventory["files"]}
    assert before == inventory["files"] and len(before) == 173
    yield
    assert {name: adapter.digest(ROOT / name) for name in before} == before


@pytest.fixture(scope="module")
def frozen_copy(tmp_path_factory):
    # Only the registered source/config allowlist is copied. No real panel,
    # checkpoint, training data, result payload or external repository is read.
    project = tmp_path_factory.mktemp("adapter_synthetic_project")
    source = project / "snapshots" / adapter.FROZEN_SNAPSHOT
    inventory = adapter.read(INVENTORY)
    for name in inventory["files"]:
        destination = source / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
    registration = project / adapter.REGISTRATION
    registration.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source / adapter.REGISTRATION, registration)
    inventory = {**inventory, "source_root_server": str(source)}
    inventory_path = project / "results/formal_main_v2/source" / (adapter.FROZEN_SNAPSHOT + ".json")
    write(inventory_path, inventory)
    return SimpleNamespace(project=project, source=source, inventory=inventory_path,
                           registration=adapter.read(registration))


def arguments(project, source, registration, *, suite="libero_10", output_name="synthetic_eval"):
    suite_config = registration["suites"][suite]
    return SimpleNamespace(project_root=project, registration=project / adapter.REGISTRATION,
        execution_manifest=project / "results/formal_main_v2" / (output_name + "_manifest.json"),
        protocol=project / suite_config["protocol"], windows=project / suite_config["windows"],
        asset_manifest=source / suite_config["model_manifest"],
        input_acceptance=project / "results/formal_main_v2/synthetic_acceptance/input_acceptance.json",
        checkpoint=project / "weights/synthetic_base", oft_source=project / "external/openvla-oft",
        libero_source=project / "external/LIBERO", libero_config=project / "configs/libero_runtime",
        development_panel=project / suite_config["initial_states_root"] / "development.json",
        final_registry=None, sealed_final=None, release=None, release_sha256=None,
        global_freeze=None, panel=None, output=project / "results/formal_main_v2" / output_name,
        cache_directory=project / ".cache/synthetic_eval", prepare_only=False,
        policy_watchdog_seconds=60., stop_after=1, uncontended_gpu=True)


def manifest_for(registration, *, suite="libero_10"):
    identity = formal_trials.baseline_instance_identity(suite=suite, method="dense", visual_tokens=512,
        model_revision="synthetic", frozen_model_sha256="a" * 64,
        source_files={"synthetic_source": "b" * 64}, input_acceptance_sha256="c" * 64)
    return dict(schema=adapter.ROUND, kind="evaluation_execution", suite=suite, split="development",
        registration_sha256=adapter.signature(registration), methods=[dict(identity=identity)],
        environment={**formal_trials.ENVIRONMENT, "max_steps": formal_trials.FORMAL_SUITES[suite]["max_steps"]})


def saved_run(tmp_path):
    output = tmp_path / "saved_run"
    output.mkdir()
    panel = synthetic_panel()
    manifest = manifest_for({"synthetic": True})
    sources = {"synthetic.py": "b" * 64}
    registration_sha = manifest["registration_sha256"]
    config = dict(schema=adapter.ROUND, kind="evaluation_run", manifest=manifest,
        registration_sha256=registration_sha, panel_signature=adapter.signature(panel),
        source_files=sources, policy_watchdog_seconds=60., watched_files={"synthetic": "d" * 64}, runtime={})
    write(output / "config.json", config)
    write(output / "panel.json", panel)
    signature = adapter.signature(config)
    ledger = libero_runtime.TrialLedger(output / "trials.jsonl", run_signature=signature)
    ledger.append(dict(event="invocation", slurm_job_id="synthetic-1"))
    args = SimpleNamespace(output=output, policy_watchdog_seconds=60.)
    return SimpleNamespace(args=args, manifest=manifest, panel=panel, sources=sources,
        registration_sha=registration_sha, config=config, signature=signature, ledger=ledger)


def guard(saved, *, resume=True, existed=True):
    return adapter.resume_guard(saved.args, saved.manifest, saved.panel, saved.registration_sha,
        saved.sources, validators=formal_trials, resume=resume, existed=existed)


def trial_events(panel, index, *, status=None, success=False):
    identity = formal_trials._identity(panel, panel["states"][index], "dense")
    rows = [dict(**identity, event="start")]
    if status:
        rows.append(dict(**identity, event="result", status=status, success=success,
                         policy_calls=0, control_steps=0, wait_steps=0, attempt_wall_seconds=.1))
    return rows


def test_all_registered_source_extensions_and_adapter_sha_are_checked(frozen_copy):
    value = adapter.verify_snapshot(frozen_copy.project, frozen_copy.source, frozen_copy.inventory,
                                    adapter_sha256=adapter.digest(SCRIPT))
    assert len(value["files"]) == 173
    assert "AGENTS.md" in value["files"]
    assert any(name.endswith(".txt") for name in value["files"])
    with pytest.raises(ValueError, match="adapter SHA256"):
        adapter.verify_snapshot(frozen_copy.project, frozen_copy.source, frozen_copy.inventory,
                                adapter_sha256="0" * 64)


def test_frozen_source_tamper_fails_without_modifying_originals(frozen_copy):
    path = frozen_copy.source / "scripts/eval_libero.py"
    original = path.read_bytes()
    try:
        path.write_bytes(original + b"\n# synthetic mutation\n")
        with pytest.raises(ValueError, match="Frozen source changed"):
            adapter.verify_snapshot(frozen_copy.project, frozen_copy.source, frozen_copy.inventory,
                                    adapter_sha256=adapter.digest(SCRIPT))
    finally:
        path.write_bytes(original)


@pytest.mark.parametrize("mode", ["evaluate", "collect", "full", "components"])
def test_misdirected_development_panel_rejected_without_resolving_or_reading(frozen_copy, monkeypatch, mode):
    args = arguments(frozen_copy.project, frozen_copy.source, frozen_copy.registration)
    manifest = manifest_for(frozen_copy.registration)
    args.development_panel = args.development_panel.with_name("sealed_final.json")
    protected = args.development_panel
    original_resolve, original_open = Path.resolve, Path.open
    touched = []
    def resolve(path, *a, **kw):
        if path == protected:
            touched.append("resolve")
            raise AssertionError("sealed path resolved before release")
        return original_resolve(path, *a, **kw)
    def open_file(path, *a, **kw):
        if path == protected:
            touched.append("open")
            raise AssertionError("sealed path read before release")
        return original_open(path, *a, **kw)
    monkeypatch.setattr(Path, "resolve", resolve)
    monkeypatch.setattr(Path, "open", open_file)
    with pytest.raises(ValueError, match="registered development.json"):
        adapter.check_paths(args, mode, frozen_copy.registration, manifest, frozen_copy.source)
    assert touched == []


@pytest.mark.parametrize("field", ["input_acceptance", "global_freeze", "panel"])
def test_other_metadata_flags_cannot_read_sealed_paths(frozen_copy, field):
    args = arguments(frozen_copy.project, frozen_copy.source, frozen_copy.registration)
    setattr(args, field, args.development_panel.with_name("sealed_final.json"))
    with pytest.raises(ValueError, match="nonsealed scope"):
        adapter.check_paths(args, "collect", frozen_copy.registration, manifest_for(frozen_copy.registration), frozen_copy.source)


@pytest.mark.parametrize("field", ["protocol", "windows", "asset_manifest", "oft_source", "libero_source", "libero_config"])
def test_runtime_paths_remain_exact_registered_locations(frozen_copy, field):
    args = arguments(frozen_copy.project, frozen_copy.source, frozen_copy.registration)
    setattr(args, field, frozen_copy.project / "other" / Path(getattr(args, field)).name)
    with pytest.raises(ValueError):
        adapter.check_paths(args, "evaluate", frozen_copy.registration, manifest_for(frozen_copy.registration), frozen_copy.source)


def test_no_final_stat_or_read_until_original_release_gate(frozen_copy, tmp_path, monkeypatch):
    args = arguments(frozen_copy.project, frozen_copy.source, frozen_copy.registration)
    manifest = {**manifest_for(frozen_copy.registration), "split": "final"}
    args.final_registry = args.development_panel.with_name("final_registry.json")
    args.sealed_final = args.development_panel.with_name("sealed_final.json")
    args.development_panel = None
    args.release = frozen_copy.project / "results/formal_main_v2/synthetic_invalid_release.json"
    write(args.release, {"synthetic": "invalid release; no final files exist"})
    protected = {args.final_registry, args.sealed_final}
    touched = []
    original_open, original_stat, original_resolve = Path.open, Path.stat, Path.resolve
    def protect(function):
        def wrapped(path, *a, **kw):
            if path in protected:
                touched.append(str(path))
                raise AssertionError("final content accessed before a valid complete release")
            return function(path, *a, **kw)
        return wrapped
    monkeypatch.setattr(Path, "open", protect(original_open))
    monkeypatch.setattr(Path, "stat", protect(original_stat))
    monkeypatch.setattr(Path, "resolve", protect(original_resolve))
    adapter.check_paths(args, "evaluate", frozen_copy.registration, manifest, frozen_copy.source)
    with pytest.raises(ValueError):
        formal_trials.load_formal_panel(suite="libero_10", split="final",
            final_registry_path=args.final_registry, sealed_final_path=args.sealed_final,
            release_path=args.release, release_file_sha256=adapter.digest(args.release),
            matrix=freeze_fixture(), registration_sha256=adapter.signature(frozen_copy.registration))
    assert touched == []


@pytest.mark.parametrize("mutation", ["manifest", "panel", "source", "watchdog", "registration", "run_signature"])
def test_wrong_resume_identity_refuses_before_ledger_append(tmp_path, mutation):
    saved = saved_run(tmp_path)
    if mutation == "manifest":
        saved.manifest = {**saved.manifest, "extra_changed": True}
    elif mutation == "panel":
        saved.panel = {**saved.panel, "extra_changed": True}
    elif mutation == "source":
        saved.sources = {"other.py": "a" * 64}
    elif mutation == "watchdog":
        saved.args.policy_watchdog_seconds = 1.
    elif mutation == "registration":
        saved.registration_sha = "0" * 64
    else:
        row = adapter.read(saved.ledger.path)
        row["run_signature"] = "0" * 64
        write(saved.ledger.path, row)
    original = saved.ledger.path.read_bytes()
    with pytest.raises(ValueError):
        guard(saved)
    assert saved.ledger.path.read_bytes() == original


@pytest.mark.parametrize("resume,existed,error", [(False, True, FileExistsError), (True, False, FileNotFoundError)])
def test_explicit_resume_and_existing_output_must_agree(tmp_path, resume, existed, error):
    saved = saved_run(tmp_path)
    with pytest.raises(error):
        guard(saved, resume=resume, existed=existed)


@pytest.mark.parametrize("tail", [b'{"event":', b'\xff', b'\n'])
def test_corrupt_tail_is_never_repaired_or_truncated(tmp_path, tail):
    saved = saved_run(tmp_path)
    raw = saved.ledger.path.read_bytes() + tail
    saved.ledger.path.write_bytes(raw)
    before_files = set(saved.args.output.iterdir())
    with pytest.raises(ValueError, match="(Malformed trial JSON|tail lacks final LF)"):
        guard(saved)
    assert saved.ledger.path.read_bytes() == raw
    assert set(saved.args.output.iterdir()) == before_files


def test_complete_last_json_without_newline_is_preserved_but_refused(tmp_path):
    saved = saved_run(tmp_path)
    raw = saved.ledger.path.read_bytes().rstrip(b"\n")
    saved.ledger.path.write_bytes(raw)
    with pytest.raises(ValueError, match="tail lacks final LF"):
        guard(saved)
    assert saved.ledger.path.read_bytes() == raw


def test_unknown_attempts_and_all_prior_invocations_are_retained(tmp_path):
    saved = saved_run(tmp_path)
    for row in trial_events(saved.panel, 0) * 2:
        saved.ledger.append(row)
    raw = saved.ledger.path.read_bytes()
    prefix = guard(saved)
    assert prefix["unfinished_attempts_unknown_cost"] == 2
    loaded = libero_runtime.TrialLedger(saved.ledger.path, run_signature=saved.signature)
    loaded.append(dict(event="invocation", slurm_job_id="synthetic-2"))
    adapter.unchanged_prefix(saved.ledger.path, prefix)
    assert saved.ledger.path.read_bytes().startswith(raw)
    current = guard(saved)
    assert current["invocation_job_ids"] == ["synthetic-1", "synthetic-2"]
    assert current["unfinished_attempts_unknown_cost"] == 2


@pytest.mark.parametrize("missing,claims", [(True, 0), (False, 1)])
def test_missing_or_empty_ledger_cannot_replace_prior_report(tmp_path, missing, claims):
    saved = saved_run(tmp_path)
    if missing:
        saved.ledger.path.unlink()
    else:
        saved.ledger.path.write_bytes(b"")
    write(saved.args.output / "closed_loop_report.json", dict(status="in_progress", completed_trials=claims,
        provenance={"run_signature": saved.signature}))
    with pytest.raises(ValueError, match="(no durable trials.jsonl|completion disagrees)"):
        guard(saved)


def test_original_loop_skips_both_terminal_statuses_and_retries_infrastructure(tmp_path, monkeypatch):
    saved = saved_run(tmp_path)
    for index, status in enumerate(("completed", "policy_error", "infrastructure_error")):
        for row in trial_events(saved.panel, index, status=status, success=index == 0):
            saved.ledger.append(row)
    prefix = guard(saved)
    raw = saved.ledger.path.read_bytes()
    seen = []
    def make_environment(state):
        seen.append(state["trial_id"])
        return SimpleNamespace(close=lambda: None), "synthetic instruction"
    monkeypatch.setattr(formal_trials, "run_episode", lambda *a, **kw: dict(status="completed", success=False, policy_calls=0))
    result = formal_trials.evaluate_formal_trials(saved.panel, {"dense": object()}, saved.ledger,
        make_environment, reseed=lambda: None, stop_after=1)
    assert result == 1 and seen == [saved.panel["states"][2]["trial_id"]]
    assert saved.ledger.path.read_bytes().startswith(raw)
    adapter.unchanged_prefix(saved.ledger.path, prefix)
    assert len(guard(saved)["terminal_trial_ids"]) == 3
    # The infrastructure result remains and is not re-labelled as a completed
    # attempt or silently removed from subsequent cost reconciliation.
    rows = [json.loads(line) for line in saved.ledger.path.read_bytes().splitlines()]
    assert sum(r.get("status") == "infrastructure_error" for r in rows) == 1


def test_terminal_restart_refused(tmp_path):
    saved = saved_run(tmp_path)
    for row in trial_events(saved.panel, 0, status="policy_error"):
        saved.ledger.append(row)
    saved.ledger.append(trial_events(saved.panel, 0)[0])
    with pytest.raises(ValueError, match="terminal trial"):
        guard(saved)


@pytest.mark.parametrize("key,value", [("task_id", 9), ("initial_state_sha256", "0" * 64), ("method", "uniform64")])
def test_foreign_trial_identity_refused_without_rewriting(tmp_path, key, value):
    saved = saved_run(tmp_path)
    row = trial_events(saved.panel, 0)[0]
    saved.ledger.append({**row, key: value})
    raw = saved.ledger.path.read_bytes()
    with pytest.raises(ValueError, match="another panel/method/environment identity"):
        guard(saved)
    assert saved.ledger.path.read_bytes() == raw


def test_exact_private_binding_uses_frozen_archive_verifier_and_restores(frozen_copy, tmp_path):
    evaluate = adapter.private_module(frozen_copy.source, "eval_formal_selector_libero")
    legacy = adapter.private_module(frozen_copy.source, "eval_libero")
    archive = tmp_path / "archive"
    archive.mkdir()
    source_file = archive / "tiny.py"
    source_file.write_bytes(b"synthetic = True\n")
    revision = "synthetic-revision"
    write(archive / "SOURCE_REVISION.json", dict(revision=revision, archive_sha256="a" * 64))
    write(archive / "SOURCE_FILES.json", dict(revision=revision, archive_sha256="a" * 64,
                                             files={"tiny.py": adapter.digest(source_file)}))
    calls, events = [], []
    def original_loader(root, name):
        calls.append((root, name))
        return "untouched loader"
    helpers = SimpleNamespace(load_script=original_loader)
    original_verify, original_execute = evaluate.verify_checkout, evaluate.execute
    def emit(event, **values):
        events.append(dict(event=event, **values))
    with pytest.raises(ValueError, match="archive file verification"):
        with adapter.recorded_bindings(evaluate, legacy, helpers, frozen_copy.source, emit) as bindings:
            result = evaluate.verify_checkout(archive, revision)
            assert result["verification"] == "archive_all_files_sha256" and result["file_count"] == 1
            assert helpers.load_script(frozen_copy.source, "eval_formal_selector_libero") is evaluate
            assert helpers.load_script(frozen_copy.source, "eval_libero") == "untouched loader"
            assert helpers.load_script(tmp_path, "eval_formal_selector_libero") == "untouched loader"
            assert len(calls) == 2 and evaluate.execute is original_execute
            assert all(len(row["original_code_sha256"]) == 64 and len(row["adapter_binding_code_sha256"]) == 64 for row in bindings)
            assert bindings[0]["replacement_file"] == str(frozen_copy.source / "scripts/eval_libero.py")
            source_file.write_bytes(b"synthetic = False\n")
            evaluate.verify_checkout(archive, revision)
    assert helpers.load_script is original_loader and evaluate.verify_checkout is original_verify
    assert evaluate.execute is original_execute and events[-1]["event"] == "bindings_restored"


def test_exclusive_output_lock_refuses_second_owner(tmp_path):
    path = tmp_path / "adapter.lock"
    with adapter.exclusive(path):
        with pytest.raises(OSError):
            with adapter.exclusive(path):
                raise AssertionError("second writer must not acquire this output")


def test_original_collect_uses_same_scoped_archive_verifier(frozen_copy, tmp_path, monkeypatch):
    from cti_vla.data import initial_states
    from cti_vla.data.formal_windows import LIBERO_REVISION
    evaluate = adapter.private_module(frozen_copy.source, "eval_formal_selector_libero")
    legacy = adapter.private_module(frozen_copy.source, "eval_libero")
    profile = adapter.private_module(frozen_copy.source, "profile_formal")
    roots = {}
    for name, revision in (("oft_source", libero_runtime.OFT_COMMIT), ("libero_source", LIBERO_REVISION)):
        directory = tmp_path / name
        directory.mkdir()
        (directory / "tiny.py").write_bytes(b"synthetic = True\n")
        write(directory / "SOURCE_REVISION.json", dict(revision=revision, archive_sha256="a" * 64))
        write(directory / "SOURCE_FILES.json", dict(revision=revision, archive_sha256="a" * 64,
            files={"tiny.py": adapter.digest(directory / "tiny.py")}))
        roots[name] = directory
    class StopBeforeSimulator(Exception):
        pass
    def stop(*a, **kw):
        raise StopBeforeSimulator("both source checks completed; no model or simulator")
    monkeypatch.setattr(initial_states, "official_task_catalog", stop)
    events = []
    def emit(event, **values):
        events.append(dict(event=event, **values))
    original_loader = future_profiling.load_script
    with pytest.raises(StopBeforeSimulator):
        with adapter.recorded_bindings(evaluate, legacy, future_profiling, frozen_copy.source, emit):
            profile.collect(SimpleNamespace(**roots), {}, {"suite": "libero_10"}, {}, {}, None, None,
                            lambda: None, lambda: None)
    verified = [r for r in events if r["event"] == "official_source_verified"]
    assert len(verified) == 2 and all(r["verification"]["verification"] == "archive_all_files_sha256" for r in verified)
    assert sum(r["event"] == "private_eval_loader_used" for r in events) == 1
    assert future_profiling.load_script is original_loader


def test_prepare_only_runs_frozen_gates_in_fresh_process_without_weights(frozen_copy):
    args = arguments(frozen_copy.project, frozen_copy.source, frozen_copy.registration, output_name="prepare_only")
    write(args.execution_manifest, manifest_for(frozen_copy.registration))
    write(args.development_panel, synthetic_panel())
    command = [sys.executable, str(SCRIPT), "evaluate", "--source-root", str(frozen_copy.source),
        "--source-inventory", str(frozen_copy.inventory), "--adapter-sha256", adapter.digest(SCRIPT), "--prepare-only"]
    for key in ("project_root", "registration", "execution_manifest", "protocol", "windows", "input_acceptance",
                "asset_manifest", "checkpoint", "oft_source", "libero_source", "libero_config", "cache_directory", "output", "development_panel"):
        command += ["--" + key.replace("_", "-"), str(getattr(args, key))]
    env = {k: v for k, v in os.environ.items() if k not in ("SLURM_JOB_ID", "PYTHONPATH")}
    env["CUDA_VISIBLE_DEVICES"] = ""
    result = subprocess.run(command, capture_output=True, text=True, timeout=60, env=env, cwd=frozen_copy.project)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["status"] == "prepared_only" and payload["expected_trials"] == 100
    assert payload["gpu_calls"] == 0 and payload["test_opened"] is False and payload["weights_validated"] is False
    assert payload["adapter_sha256"] == adapter.digest(SCRIPT)
    assert not args.checkpoint.exists() and not args.output.exists()


def test_recorded_run_invokes_execute_and_preserves_failed_prefix(frozen_copy, monkeypatch):
    """Only the GPU execute and fresh-import context are substituted in this test;
    manifest/panel/source gates, locks, bindings and receipts are real."""
    args = arguments(frozen_copy.project, frozen_copy.source, frozen_copy.registration, output_name="mocked_execute")
    manifest = manifest_for(frozen_copy.registration)
    panel = synthetic_panel()
    write(args.execution_manifest, manifest)
    write(args.development_panel, panel)
    sources = formal_source_hashes(frozen_copy.source)
    calls = []
    def fake_execute(actual_args, actual_manifest, actual_panel, registration_sha):
        assert actual_args is args and actual_manifest == manifest and actual_panel == panel
        calls.append("execute")
        config = dict(schema=adapter.ROUND, kind="evaluation_run", manifest=manifest,
            registration_sha256=registration_sha, panel_signature=adapter.signature(panel),
            source_files=sources, policy_watchdog_seconds=60., runtime={}, watched_files={})
        write(args.output / "config.json", config)
        write(args.output / "panel.json", panel)
        ledger = libero_runtime.TrialLedger(args.output / "trials.jsonl", run_signature=adapter.signature(config))
        ledger.append(dict(event="invocation", slurm_job_id="synthetic-registered"))
        for row in trial_events(panel, 0, status="policy_error"):
            ledger.append(row)
        return {"status": "synthetic_return"}
    evaluate = adapter.private_module(frozen_copy.source, "eval_formal_selector_libero")
    evaluate.execute = fake_execute
    original_module = adapter.private_module
    monkeypatch.setattr(adapter, "private_module", lambda source, name: evaluate if name == "eval_formal_selector_libero" else original_module(source, name))
    monkeypatch.setattr(adapter, "source_imports", lambda source: nullcontext())
    monkeypatch.setattr(adapter, "require_server", lambda: None)
    monkeypatch.setenv("SLURM_JOB_ID", "synthetic-registered")
    original_loader, original_verify = future_profiling.load_script, evaluate.verify_checkout
    options = dict(mode="evaluate", source_root=frozen_copy.source, source_inventory=frozen_copy.inventory,
                   adapter_sha256=adapter.digest(SCRIPT))
    assert adapter.run(args, **options)["status"] == "synthetic_return" and calls == ["execute"]
    receipts = args.project_root / "results/formal_main_v2/adapter_invocations"
    first = [adapter.read(path) for path in receipts.glob("*.json")]
    assert len(first) == 1 and first[0]["frozen_source_unchanged"] is True
    assert first[0]["after_ledger"]["invocation_job_ids"] == ["synthetic-registered"]
    assert len(first[0]["bindings"]) == 2 and first[0]["adapter_sha256"] == adapter.digest(SCRIPT)
    bad_tail = (args.output / "trials.jsonl").read_bytes() + b'{"unfinished":'
    (args.output / "trials.jsonl").write_bytes(bad_tail)
    with pytest.raises(ValueError, match="tail lacks final LF"):
        adapter.run(args, resume=True, **options)
    assert calls == ["execute"] and (args.output / "trials.jsonl").read_bytes() == bad_tail
    second = [adapter.read(path) for path in receipts.glob("*.json")]
    failed = [r for r in second if r["status"] == "failed"]
    assert len(failed) == 1 and failed[0]["old_ledger_prefix_unchanged"] is True
    assert future_profiling.load_script is original_loader and evaluate.verify_checkout is original_verify

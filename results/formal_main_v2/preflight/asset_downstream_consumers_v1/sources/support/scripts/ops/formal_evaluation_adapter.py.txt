"""Explicit, recorded compatibility wrapper around the frozen formal runners.

Only the private eval module's source verifier is rebound. A scoped profile
loader supplies that same private module for one exact script/snapshot pair.
Policy, environment, deployment, release gates and trial loops remain frozen.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import marshal
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import uuid

PROJECT = Path(__file__).resolve().parents[2]
ROUND = "formal_main_v2"
VERSION = "formal-evaluation-explicit-archive-resume-adapter-v2-marshal2"
CODE_MARSHAL_VERSION = 2
FROZEN_SOURCE_SHA256 = "dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e"
FROZEN_FILE_COUNT = 173
FROZEN_SNAPSHOT = "formal_main_v2_run_564be0995e"
REGISTRATION = "configs/experiments/formal_main_v2.json"


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            value.update(block)
    return value.hexdigest()


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def code_sha(function):
    # Default marshal reference tracking can change bytes when temporary
    # references/GC change, even for the very same immutable code object.
    # Format2 omits that tracking. Compare only within one Python runtime;
    # the registered file hashes remain the cross-host source identity.
    return hashlib.sha256(marshal.dumps(function.__code__, CODE_MARSHAL_VERSION)).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def append(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def publish(path, value):
    temporary = path.with_name(path.name + ".partial")
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.link(temporary, path)
    temporary.unlink()


def direct_path(value):
    path = Path(value).absolute()
    if path.resolve() != path:
        raise ValueError("Adapter paths must be direct, without aliases/symlinks or traversal")
    return path


def metadata_path(path, project):
    if path is None:
        raise ValueError("Required adapter metadata path is absent")
    path = direct_path(path)
    if (project not in path.parents or path.suffix.lower() not in (".json", ".jsonl", ".py")
            or "sealed" in path.name.lower() or any(p.lower() in ("weights", "checkpoints", "initial_states") for p in path.parts)):
        raise ValueError("Adapter metadata path is outside its nonweight, nonsealed scope")
    return path


def verify_snapshot(project, source, inventory_path, *, adapter_sha256):
    project, source = direct_path(project), direct_path(source)
    inventory_path = metadata_path(inventory_path, project)
    if (source != project / "snapshots" / FROZEN_SNAPSHOT
            or inventory_path != project / "results/formal_main_v2/source" / (FROZEN_SNAPSHOT + ".json")):
        raise ValueError("Adapter requires the exact registered formal source snapshot/inventory")
    inventory = read(inventory_path)
    files = inventory.get("files", {})
    source_sha = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    if (inventory.get("schema") != ROUND or len(files) != FROZEN_FILE_COUNT
            or source_sha != FROZEN_SOURCE_SHA256 or inventory.get("source_sha256") != source_sha
            or inventory.get("source_root_server") != str(source)):
        raise ValueError("Adapter only supports the registered173-file frozen snapshot")
    for relative, expected in files.items():
        # The immutable allowlist also contains AGENTS.md, licenses and shell
        # files. Its registered map hash, not a metadata suffix filter, binds it.
        path = direct_path(source / relative)
        if source not in path.parents or digest(path) != expected:
            raise ValueError("Frozen source changed: " + relative)
    if digest(Path(__file__)) != adapter_sha256:
        raise ValueError("Adapter bytes differ from the root-registered adapter SHA256")
    return inventory


def private_module(source, name):
    path = source / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location("cti_adapter_private_" + name + "_" + uuid.uuid4().hex, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextmanager
def source_imports(source):
    """Production is a fresh process; never mix cached modules from another tree."""
    prefix = source / "src"
    for name, module in list(sys.modules.items()):
        if name == "cti_vla" or name.startswith(("cti_vla.", "cti_vla_baselines")):
            origin = getattr(module, "__file__", None)
            if origin and prefix not in Path(origin).resolve().parents:
                raise RuntimeError("Start the adapter in a fresh process using the frozen PYTHONPATH")
    previous = list(sys.path)
    sys.path.insert(0, str(prefix))
    try:
        yield
    finally:
        sys.path[:] = previous


@contextmanager
def exclusive(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            handle.seek(0, os.SEEK_END)
            if not handle.tell():
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def check_paths(args, mode, registration, manifest, source):
    """No development/final-state file is read or hashed by this path guard."""
    project = direct_path(args.project_root)
    suite = manifest.get("suite")
    if suite not in registration.get("suites", {}):
        raise ValueError("Unknown registered formal suite")
    spec = registration["suites"][suite]
    if direct_path(args.registration) != project / REGISTRATION:
        raise ValueError("Use the canonical formal registration")
    initial = project / spec["initial_states_root"]
    for key in ("input_acceptance", "global_freeze", "panel"):
        value = getattr(args, key, None)
        if value is not None:
            metadata_path(value, project)
    split = manifest.get("split") if mode == "evaluate" else "development"
    if split == "development":
        if (args.development_panel is None
                or Path(args.development_panel).absolute() != initial / "development.json"
                or direct_path(args.development_panel) != initial / "development.json"):
            raise ValueError("Development panel must be the registered development.json before any loader runs")
        if any(getattr(args, key, None) is not None for key in ("final_registry", "sealed_final", "release", "release_sha256")):
            raise ValueError("Development/profile execution cannot accept final-state arguments")
    elif split == "final":
        # Pure lexical comparison: even stat/resolve of sealed paths waits for the
        # original load_formal_panel release gate. Never hash either path here.
        for key, name in (("final_registry", "final_registry.json"), ("sealed_final", "sealed_final.json")):
            value = getattr(args, key, None)
            if value is None or str(Path(value).absolute()) != str(initial / name):
                raise ValueError("Final path differs from the registered suite path")
        if args.development_panel is not None:
            raise ValueError("Final evaluation cannot substitute a development panel")
        metadata_path(args.release, project)
    else:
        raise ValueError("Explicit development/final split required")
    for key in ("protocol", "windows"):
        value = getattr(args, key, None)
        if value is not None and direct_path(value) != project / spec[key]:
            raise ValueError("Registered suite data path changed: " + key)
    if args.asset_manifest is not None and direct_path(args.asset_manifest) != source / spec["model_manifest"]:
        raise ValueError("Use the suite asset manifest from the frozen snapshot")
    for key, suffix in (("oft_source", "external/openvla-oft"), ("libero_source", "external/LIBERO"), ("libero_config", "configs/libero_runtime")):
        if direct_path(getattr(args, key)) != project / suffix:
            raise ValueError("Official runtime source/config path changed")
    output, cache = direct_path(args.output), direct_path(args.cache_directory)
    if project / "results/formal_main_v2" not in output.parents:
        raise ValueError("Output must remain in formal_main_v2 results")
    for path in (output, cache):
        if (project not in path.parents or source in path.parents or path == source
                or path in source.parents
                or any(part.lower() in ("weights", "checkpoints", "initial_states") or "sealed" in part.lower() for part in path.parts)
                or (args.checkpoint is not None and (path == direct_path(args.checkpoint) or direct_path(args.checkpoint) in path.parents))):
            raise ValueError("Output/cache overlaps source, weights or another project")
    if cache == output or cache in output.parents or output in cache.parents:
        raise ValueError("Evaluation output and mutable model cache must be separate")


def checked_ledger(path, signature_value, *, panel, identifiers, validators):
    """Read only; unlike TrialLedger, never repair/truncate a malformed tail."""
    if not path.is_file():
        raise ValueError("Existing output has no durable trials.jsonl; root must review the interrupted initialization")
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        raise ValueError("Trial JSON tail lacks final LF; retain original bytes, no automatic tail repair")
    rows, terminal, active, unfinished = [], {}, set(), 0
    for number, line in enumerate(raw.splitlines(), 1):
        try:
            row = json.loads(line)
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError(f"Malformed trial JSON line{number}; retain original bytes, no automatic tail repair") from exc
        if not isinstance(row, dict) or row.get("run_signature") != signature_value:
            raise ValueError("Raw trial belongs to another run_signature")
        kind, trial = row.get("event"), row.get("trial_id")
        if kind == "start":
            if trial in terminal:
                raise ValueError("A terminal trial was restarted")
            unfinished += int(trial in active)
            active.add(trial)
        elif kind == "result":
            if trial not in active or row.get("status") not in ("completed", "policy_error", "infrastructure_error") or type(row.get("success")) is not bool:
                raise ValueError("Trial result lacks a valid start/status/outcome")
            active.remove(trial)
            if row["status"] != "completed" and row["success"]:
                raise ValueError("A failed trial cannot be a success")
            if row["status"] in ("completed", "policy_error"):
                terminal[trial] = row
        elif kind not in ("invocation", "cleanup_error"):
            raise ValueError("Unrecognized frozen trial event")
        rows.append(row)
    validators.validate_trial_identities(panel, identifiers, SimpleNamespace(events=rows))
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), terminal_trial_ids=sorted(terminal),
        invocation_job_ids=sorted({str(r["slurm_job_id"]) for r in rows if r.get("event") == "invocation"}),
        active_trial_ids=sorted(active), unfinished_attempts_unknown_cost=unfinished + len(active), events=len(rows))


def resume_guard(args, manifest, panel, registration_sha, sources, *, validators, resume, existed):
    if existed and not resume:
        raise FileExistsError("Existing output requires explicit --resume")
    if resume and not existed:
        raise FileNotFoundError("--resume cannot silently start a fresh evaluation")
    path = args.output / "trials.jsonl"
    if not existed:
        return dict(bytes=0, sha256=hashlib.sha256(b"").hexdigest(), terminal_trial_ids=[], invocation_job_ids=[], active_trial_ids=[], events=0)
    config_path, panel_path = args.output / "config.json", args.output / "panel.json"
    if not config_path.is_file() or not panel_path.is_file():
        raise ValueError("Existing output has no complete frozen config/panel identity")
    config = read(config_path)
    expected = dict(schema=ROUND, kind="evaluation_run", manifest=manifest, registration_sha256=registration_sha,
        panel_signature=signature(panel), source_files=sources, policy_watchdog_seconds=args.policy_watchdog_seconds)
    if any(config.get(k) != v for k, v in expected.items()) or read(panel_path) != panel:
        raise ValueError("Resume config/panel/manifest identity differs")
    result = checked_ledger(path, signature(config), panel=panel,
        identifiers=[r["identity"]["method_id"] for r in manifest["methods"]], validators=validators)
    report_path = args.output / "closed_loop_report.json"
    if report_path.exists():
        report = read(report_path)
        claimed = report.get("completed_trials")
        actual = len(result["terminal_trial_ids"])
        if (type(claimed) is not int or claimed < 0 or claimed > actual
                or report.get("provenance", {}).get("run_signature") != signature(config)
                or (report.get("status") == "completed" and claimed != len(panel["states"]) * len(manifest["methods"]))):
            raise ValueError("Existing report completion disagrees with its durable trial ledger")
        result["prior_report_sha256"] = digest(report_path)
    result.update(run_signature=signature(config), config_sha256=digest(config_path), panel_sha256=digest(panel_path))
    return result


def unchanged_prefix(path, prefix):
    if not path.exists():
        if prefix["bytes"]:
            raise ValueError("Existing trial ledger disappeared")
        return
    with path.open("rb") as stream:
        actual = stream.read(prefix["bytes"])
    if len(actual) != prefix["bytes"] or hashlib.sha256(actual).hexdigest() != prefix["sha256"]:
        raise ValueError("Original trial ledger prefix was truncated or rewritten")


def require_server():
    if os.name == "nt" or not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Real adapter execution requires a root-registered server Slurm allocation")


@contextmanager
def recorded_bindings(evaluate, legacy, profiler_helpers, source, emit):
    """The two explicit bindings are isolated/restored; original execute is called."""
    original_verify, original_loader, original_execute = evaluate.verify_checkout, profiler_helpers.load_script, evaluate.execute
    bindings = [dict(kind="private_module_function_binding", snapshot=str(source),
        target_file=str(source / "scripts/eval_formal_selector_libero.py"), target_symbol="verify_checkout",
        original_code_sha256=code_sha(original_verify), replacement_file=str(source / "scripts/eval_libero.py"),
        replacement_symbol="verify_source_checkout", replacement_code_sha256=code_sha(legacy.verify_source_checkout)),
        dict(kind="scoped_exact_script_loader", snapshot=str(source),
            target_file=str(source / "src/cti_vla/evaluation/future_profiling.py"),
            target_symbol="cti_vla.evaluation.future_profiling.load_script",
            original_code_sha256=code_sha(original_loader), intercepted_name="eval_formal_selector_libero", other_loads="original unchanged")]
    def verifier(path, revision):
        result = legacy.verify_source_checkout(path, revision)
        emit("official_source_verified", path=str(Path(path).resolve()), expected_revision=revision, verification=result)
        return result
    def loader(root, name):
        if Path(root).resolve() == source and name == "eval_formal_selector_libero":
            emit("private_eval_loader_used", snapshot=str(source), script=name)
            return evaluate
        return original_loader(root, name)
    bindings[0]["adapter_binding_code_sha256"] = code_sha(verifier)
    bindings[1]["adapter_binding_code_sha256"] = code_sha(loader)
    emit("bindings_enter", bindings=bindings, frozen_execute_code_sha256=code_sha(original_execute))
    evaluate.verify_checkout, profiler_helpers.load_script = verifier, loader
    try:
        yield bindings
    finally:
        evaluate.verify_checkout, profiler_helpers.load_script = original_verify, original_loader
        if evaluate.execute is not original_execute:
            raise RuntimeError("Frozen execute was replaced during adapter execution")
        emit("bindings_restored", original_verify_code_sha256=code_sha(original_verify), original_loader_code_sha256=code_sha(original_loader))


def run(args, *, mode, source_root, source_inventory, adapter_sha256, resume=False):
    if mode not in ("evaluate", "collect", "full", "components"):
        raise ValueError("Unknown registered adapter mode")
    args.command = mode
    project, source = direct_path(args.project_root), direct_path(source_root)
    if direct_path(args.registration) != project / REGISTRATION:
        raise ValueError("Read only the canonical registration before panel resolution")
    metadata_path(args.execution_manifest, project)
    inventory = verify_snapshot(project, source, source_inventory, adapter_sha256=adapter_sha256)
    if digest(args.registration) != inventory["files"][REGISTRATION]:
        raise ValueError("Live formal registration differs from the frozen registration")
    registration, manifest = read(args.registration), read(args.execution_manifest)
    check_paths(args, mode, registration, manifest, source)
    with source_imports(source):
        from cti_vla.evaluation import formal_trials, future_profiling
        from cti_vla.training.formal_future import formal_source_hashes
        evaluate, legacy = private_module(source, "eval_formal_selector_libero"), private_module(source, "eval_libero")
        profile = private_module(source, "profile_formal") if mode != "evaluate" else None
        registration_sha = signature(registration)
        panel, identifiers = None, None
        if mode == "evaluate":
            identifiers = formal_trials.validate_execution_manifest(manifest, registration_sha256=registration_sha)
            panel = formal_trials.load_formal_panel(suite=manifest["suite"], split=manifest["split"],
                development_path=args.development_panel, final_registry_path=args.final_registry, sealed_final_path=args.sealed_final,
                release_path=args.release, release_file_sha256=args.release_sha256, matrix=manifest.get("global_freeze"),
                registration_sha256=registration_sha)
            if manifest["split"] == "final" and read(args.release) != manifest["release"]:
                raise ValueError("Original root release and execution manifest differ")
        if args.prepare_only:
            # Original profile run retains its own manifest/panel/release-related
            # preparation checks. Evaluation gates above are the original ones.
            if mode != "evaluate":
                result = profile.run(args)
            else:
                result = dict(schema=ROUND, status="prepared_only", suite=manifest["suite"], split=manifest["split"],
                    unique_initial_states=len(panel["states"]), methods=identifiers,
                    expected_trials=len(panel["states"]) * len(identifiers), gpu_calls=0,
                    test_opened=manifest["split"] == "final", weights_validated=False)
            return {**result, "adapter_version": VERSION, "adapter_sha256": adapter_sha256,
                    "source_inventory_sha256": digest(source_inventory), "frozen_source_sha256": inventory["source_sha256"]}
        require_server()
        if mode != "evaluate" and resume:
            raise ValueError("Collection/timing retain fresh outputs; this adapter does not alter their trial loops")
        sources = formal_source_hashes(source)
        external_lock = args.output.parent / ("." + args.output.name + ".adapter.lock")
        with exclusive(external_lock):
            existed = args.output.exists()
            if mode != "evaluate" and existed:
                raise FileExistsError("Retain prior collection/timing output and register a new attempt")
            if mode == "evaluate" and existed != resume:
                raise ValueError("Existing output and explicit --resume must agree")
            attempt = os.environ["SLURM_JOB_ID"] + "_" + uuid.uuid4().hex
            record_root = project / "results/formal_main_v2/adapter_invocations"
            record_root.mkdir(parents=True, exist_ok=True)
            events_path = record_root / (attempt + ".jsonl")
            receipt_path = record_root / (attempt + ".json")
            context = dict(schema=ROUND, kind="formal_evaluation_adapter", version=VERSION, attempt_id=attempt,
                job_id=os.environ["SLURM_JOB_ID"], mode=mode, resume=resume, output=str(args.output),
                source_root=str(source), source_inventory=str(Path(source_inventory).resolve()),
                source_inventory_sha256=digest(source_inventory), frozen_source_sha256=inventory["source_sha256"],
                verified_frozen_file_count=len(inventory["files"]), adapter_path=str(Path(__file__).resolve()),
                adapter_sha256=adapter_sha256, execution_manifest_sha256=digest(args.execution_manifest),
                registration_sha256=registration_sha, eval_script_sha256=inventory["files"]["scripts/eval_formal_selector_libero.py"],
                legacy_validator_file_sha256=inventory["files"]["scripts/eval_libero.py"],
                frozen_execute_code_sha256=code_sha(evaluate.execute),
                frozen_trial_loop_code_sha256=code_sha(formal_trials.evaluate_formal_trials))
            if profile is not None:
                context.update(profiler_script_sha256=inventory["files"]["scripts/profile_formal.py"],
                    frozen_profiler_run_code_sha256=code_sha(profile.run),
                    frozen_profiler_collect_code_sha256=code_sha(profile.collect))
            def emit(event, **values):
                append(events_path, dict(event=event, attempt_id=attempt, job_id=context["job_id"],
                    utc=datetime.now(timezone.utc).isoformat(), **values))
            emit("adapter_start", identity=context)
            prefix, raw_prefix, result, error = None, None, None, None
            try:
                with recorded_bindings(evaluate, legacy, future_profiling, source, emit) as bindings:
                    context["bindings"] = bindings
                    if mode == "evaluate":
                        with exclusive(args.output / ".evaluation.lock"):
                            raw_path = args.output / "trials.jsonl"
                            raw_prefix = dict(bytes=raw_path.stat().st_size, sha256=digest(raw_path)) if raw_path.exists() else dict(bytes=0, sha256=hashlib.sha256(b"").hexdigest())
                            context["before_ledger_raw"] = raw_prefix
                            prefix = resume_guard(args, manifest, panel, registration_sha, sources,
                                validators=formal_trials, resume=resume, existed=existed)
                            context["before_ledger"] = prefix
                            emit("resume_preflight_passed", evidence=prefix, panel_signature=signature(panel))
                            # The original execute repeats config/runtime/checkpoint
                            # checks before creating/appending its TrialLedger.
                            result = evaluate.execute(args, manifest, panel, registration_sha)
                            unchanged_prefix(args.output / "trials.jsonl", prefix)
                            config = read(args.output / "config.json")
                            context["after_ledger"] = checked_ledger(args.output / "trials.jsonl", signature(config),
                                panel=panel, identifiers=identifiers, validators=formal_trials)
                    else:
                        result = profile.run(args)
                context["status"] = "returned"
                context["runner_status"] = result.get("status")
                return result
            except BaseException as exc:
                error = exc
                context.update(status="failed", error_type=type(exc).__name__, error=str(exc))
                raise
            finally:
                try:
                    if raw_prefix is not None:
                        unchanged_prefix(args.output / "trials.jsonl", raw_prefix)
                    verify_snapshot(project, source, source_inventory, adapter_sha256=adapter_sha256)
                    context["frozen_source_unchanged"] = True
                    context["old_ledger_prefix_unchanged"] = raw_prefix is not None
                except BaseException as integrity:
                    context.update(status="failed_integrity", integrity_error=str(integrity))
                    if error is None:
                        error = integrity
                emit("adapter_end", status=context.get("status"), runner_status=context.get("runner_status"))
                context.update(events_path=str(events_path), events_sha256=digest(events_path), finished_utc=datetime.now(timezone.utc).isoformat())
                publish(receipt_path, context)
                if context.get("status") == "failed_integrity" and error is not None:
                    raise error


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("mode", choices=("evaluate", "collect", "full", "components"))
    for name in ("source-root", "source-inventory"):
        result.add_argument("--" + name, type=Path, required=True)
    result.add_argument("--adapter-sha256", required=True)
    result.add_argument("--resume", action="store_true")
    for name in ("execution-manifest", "registration", "protocol", "windows", "input-acceptance", "asset-manifest", "checkpoint",
                 "oft-source", "libero-source", "libero-config", "cache-directory", "output"):
        result.add_argument("--" + name, type=Path, required=True)
    for name in ("development-panel", "final-registry", "sealed-final", "release", "global-freeze", "panel"):
        result.add_argument("--" + name, type=Path)
    result.add_argument("--release-sha256")
    result.add_argument("--project-root", type=Path, default=PROJECT)
    result.add_argument("--stop-after", type=int)
    result.add_argument("--policy-watchdog-seconds", type=float, default=60.)
    result.add_argument("--prepare-only", action="store_true")
    result.add_argument("--uncontended-gpu", action="store_true")
    return result


def main():
    args = parser().parse_args()
    args.command = args.mode
    value = run(args, mode=args.mode, source_root=args.source_root, source_inventory=args.source_inventory,
                adapter_sha256=args.adapter_sha256, resume=args.resume)
    print(json.dumps(value, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

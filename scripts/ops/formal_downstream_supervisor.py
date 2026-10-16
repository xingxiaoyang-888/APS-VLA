"""Root-only formal downstream planning/submission. Planning has no side effects.

This consumes existing execution manifests and root audits; it neither creates
scientific manifests/releases nor reads checkpoint or sealed state values.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
P = PurePosixPath("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
H = PurePosixPath("/share/home/u15016/XXY_CVPR/CTI-VLA")
ROUND = "formal_main_v2"
VERSION = "formal-downstream-root-v1"
STAGES = ("development", "final", "collect", "full", "components")
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL", "PREEMPTED", "BOOT_FAIL", "DEADLINE", "REVOKED", "SPECIAL_EXIT"}
REGISTRATION = "configs/experiments/formal_main_v2.json"
STATE = "results/experiment_supervisor/state.json"
ADAPTER = "scripts/ops/formal_evaluation_adapter.py"
WRAPPER = "scripts/server/run_formal_downstream.py"
ADAPTER_SHA256 = "b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd"
FROZEN_NAME = "formal_main_v2_run_564be0995e"
FROZEN_SHA256 = "dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e"
SOURCE_INVENTORY = f"results/{ROUND}/source/{FROZEN_NAME}.json"
FORBIDDEN = {".pt", ".pth", ".bin", ".ckpt", ".safetensors", ".pkl", ".pickle", ".init", ".pruned_init"}
sys.path.insert(0, str(ROOT / "src"))


def load(relative, project=ROOT):
    spec = importlib.util.spec_from_file_location("downstream_" + uuid.uuid4().hex, Path(project) / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def relative(value):
    path = PurePosixPath(str(value).replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or "." in path.parts or ":" in str(path) or str(path) != str(value):
        raise ValueError("Use canonical project-relative paths")
    if not path.parts or any("sealed" in p.lower() or p.lower() in ("weights", "checkpoints") for p in path.parts) or set(path.suffixes) & FORBIDDEN:
        raise ValueError("Downstream metadata cannot name weights or sealed values")
    return str(path)


def local(project, value):
    result = Path(project) / relative(value)
    if result.resolve() != result.absolute() or Path(project).resolve() not in result.resolve().parents:
        raise ValueError("Project evidence must be a direct path")
    return result


def result_relative(value):
    value = relative(value)
    if PurePosixPath(f"results/{ROUND}") not in PurePosixPath(value).parents:
        raise ValueError("Artifact must remain under formal result root")
    return value


def check_source(evidence, helper, source_inventory):
    if relative(source_inventory) != SOURCE_INVENTORY:
        raise ValueError("Use the registered173-file inventory")
    inventory = evidence.read(source_inventory)
    files = inventory.get("files", {})
    if (inventory.get("schema") != ROUND or len(files) != 173
            or hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest() != FROZEN_SHA256
            or inventory.get("source_sha256") != FROZEN_SHA256
            or inventory.get("source_root_server") != str(P / "snapshots" / FROZEN_NAME)):
        raise ValueError("Frozen173-file source identity differs")
    for name, sha in files.items():
        if evidence.watch(name) != sha:
            raise ValueError("Frozen file changed: " + name)
    if evidence.watch(ADAPTER) != ADAPTER_SHA256:
        raise ValueError("The separately audited adapter changed")
    return inventory, helper.source_contract(evidence, source_inventory)


def formal_jobs(state):
    # Match the existing puller's sacct convention without rewriting the
    # supervisor's original State text (e.g. CANCELLED by15016 / COMPLETED+).
    jobs = [{**j, "raw_status": j.get("status"), "status": str(j.get("status", "")).split()[0].rstrip("+")
             if str(j.get("status", "")).split() else ""}
            for j in state.get("registered_jobs", []) if j.get("experiment") == ROUND]
    if len({str(j.get("job_id")) for j in jobs}) != len(jobs) or any(not re.fullmatch(r"[0-9]+", str(j.get("job_id", ""))) for j in jobs):
        raise ValueError("Invalid or duplicate registered formal jobs")
    return jobs


def successful_job(jobs, job_id, *, mode, output=None):
    found = [j for j in jobs if str(j["job_id"]) == str(job_id)]
    if len(found) != 1:
        raise ValueError("Required producer job is not uniquely registered")
    job = found[0]
    if (job.get("status") != "COMPLETED" or job.get("exit_code") != "0:0" or job.get("mode") != mode
            or job.get("source_sha256") != FROZEN_SHA256 or (output and job.get("run_root") != output)):
        raise ValueError("Required producer has no completed registered identity")
    return job


def check_completed_training(evidence, helper, registration, rows, jobs):
    wanted = {(r["identity"]["visual_tokens"], r["identity"]["training_seed"]) for r in rows if r["identity"]["method"] in ("A", "B")}
    suite = rows[0]["identity"]["suite"]
    for pair in registration["pairs"]:
        if pair["suite"] != suite or (pair["visual_tokens"], pair["seed"]) not in wanted:
            continue
        directory = helper.pair_directory(evidence, pair)
        report = evidence.read(directory / "training_summary.json")
        job = successful_job(jobs, report["job_id"], mode="train", output=pair["run_root_server"] + "/training")
        if job.get("segment_end") != 5000:
            raise ValueError("Development selectors require the completed5000-update job")
        review = evidence.read(directory / "segment_reviews" / (str(job["job_id"]) + ".json"))
        if (review.get("kind") != "root_segment_review" or review.get("status") != "passed"
                or review.get("job_id") != str(job["job_id"]) or review.get("completed_by_arm") != {"A": 5000, "B": 5000}
                or review.get("allowed_next_segment_end") is not None
                or review.get("continuation") != "formal_training_complete_no_extension"
                or review.get("source_sha256") != FROZEN_SHA256
                or review.get("invocation_sha256") != job.get("invocation_sha256")):
            raise ValueError("Selected pair lacks its final root segment audit")
        for name, sha in review.get("files", {}).items():
            if evidence.watch(name) != sha:
                raise ValueError("Final training audit bytes changed")
        if not review.get("files") or evidence.watch(job["invocation"]) != job["invocation_sha256"]:
            raise ValueError("Final training invocation/audit is not bound")


def validate_inputs(args, state, project, helper):
    from cti_vla.data.formal_initial_states import load_formal_development_panel
    from cti_vla.evaluation import formal_trials as trials, formal_profiling as profiling
    evidence = helper.Evidence(project)
    # All caller-controlled paths are screened before any JSON/panel loader.
    for key in ("execution_manifest", "source_inventory", "freeze_directory", "profile_panel", "prior_review", "collection_review", "repair_record"):
        value = getattr(args, key, None)
        if value is not None:
            local(project, value)
            if key not in ("source_inventory",):
                result_relative(value)
    inventory, sources = check_source(evidence, helper, args.source_inventory)
    registration = helper.registration_contract(evidence, REGISTRATION)
    manifest = evidence.read(args.execution_manifest)
    suite = manifest.get("suite")
    if suite not in registration["suites"] or args.stage not in STAGES:
        raise ValueError("Unknown suite/stage")
    expected_split = "final" if args.stage == "final" else "development"
    if manifest.get("split") != expected_split:
        raise ValueError("Stage cannot use another split")
    identifiers = trials.validate_execution_manifest(manifest, registration_sha256=signature(registration))
    rows = helper.suite_rows(evidence, registration, suite, sources, identifiers)
    if manifest["methods"] != rows:
        raise ValueError("Manifest method/checkpoint paths differ from completed receipts")
    jobs = formal_jobs(state)
    acceptance_path = f"results/{ROUND}/{suite}/acceptance/root_review.json"
    acceptance = evidence.read(acceptance_path)
    gate_job = successful_job(jobs, acceptance["job_id"], mode="acceptance", output=str(P / acceptance["output_relative"]))
    if acceptance.get("status") != "passed" or acceptance.get("source_sha256") != FROZEN_SHA256:
        raise ValueError("Suite acceptance root review differs from this source")
    check_completed_training(evidence, helper, registration, rows, jobs)
    spec = registration["suites"][suite]
    development_path = spec["initial_states_root"] + "/development.json"
    matrix = release = None
    if args.stage in ("final", "full", "components"):
        if not args.freeze_directory:
            raise ValueError("This stage requires the complete global freeze")
        helper.release_global(evidence, registration, args.freeze_directory, release=False)
        matrix = evidence.read(args.freeze_directory + "/global_freeze.json")
        if args.stage == "final":
            release = evidence.read(args.freeze_directory + "/root_release.json")
            trials.validate_final_release(release, matrix, registration_sha256=signature(registration))
            if manifest != helper.make_execution(registration, suite, rows, split="final", matrix=matrix, release=release):
                raise ValueError("Final manifest is not the exact released matrix")
        elif manifest.get("global_freeze") is not None or manifest.get("release") is not None:
            raise ValueError("Profiling must use development manifest identity")
    elif args.freeze_directory is not None:
        raise ValueError("An unrelated global freeze cannot change this stage")
    if args.stage != "final":
        evidence.watch(development_path)
        development = load_formal_development_panel(evidence.path(development_path))
        if development["suite"] != suite:
            raise ValueError("Wrong registered development panel")
        if "development_panel" in manifest and (manifest["development_panel"] != development_path
                or manifest.get("development_panel_sha256") != evidence.watch(development_path)):
            raise ValueError("Development manifest panel changed")
    else:
        # Final state values are never opened here, even after release. The
        # original server loader owns that operation after rechecking release.
        development = None
    panel_artifacts = {}
    if args.stage in ("collect", "full", "components"):
        profiling.validate_profile_manifest(manifest, registration, collect=args.stage == "collect", global_freeze=matrix)
        if args.stage == "collect":
            if args.profile_panel is not None or args.collection_review is not None:
                raise ValueError("Collection cannot substitute an existing observation panel")
        else:
            if not args.profile_panel or not args.collection_review:
                raise ValueError("Timing requires the original audited collection panel")
            _, panel = profiling.load_profile_panel(evidence.path(args.profile_panel), development=development,
                registration=registration, dense_identity=rows[0]["identity"])
            panel_artifacts = {str(PurePosixPath(args.profile_panel).parent / name): sha for name, sha in panel["artifact_sha256"].items()}
            panel_artifacts[args.profile_panel] = evidence.watch(args.profile_panel)
            for name, sha in panel_artifacts.items():
                if evidence.watch(name) != sha:
                    raise ValueError("Timing observation artifact changed")
            collection = require_root_review(evidence, args.collection_review, jobs, expected_stage="collect")
            if collection["scientific_complete"] is not True or str(P / args.profile_panel) != collection["run_root"] + "/panel.json":
                raise ValueError("Timing panel has no completed collection audit")
    elif args.profile_panel is not None or args.collection_review is not None:
        raise ValueError("Rollout stages cannot accept timing panel flags")
    return dict(evidence=evidence, inventory=inventory, sources=sources, registration=registration, manifest=manifest,
        suite=suite, methods=identifiers, acceptance=acceptance, gate_job=gate_job,
        development_path=development_path, development=development, matrix=matrix, release=release, panel_artifacts=panel_artifacts)


def require_root_review(evidence, path, jobs, *, expected_stage):
    """Consume a root-written audit, and independently recheck stable SHA pulls.
    Producing this audit is deliberately outside the scheduler's remit.
    """
    report = evidence.read(path)
    matches = [j for j in jobs if str(j["job_id"]) == report.get("job_id")]
    if len(matches) != 1:
        raise ValueError("Downstream audit job is not registered")
    job = matches[0]
    expected = dict(schema=ROUND, kind="root_downstream_review", status="passed", reviewed_by="root",
        stage=expected_stage, stage_key=job.get("stage_key"), source_sha256=FROZEN_SHA256,
        adapter_sha256=ADAPTER_SHA256, invocation_sha256=job.get("invocation_sha256"),
        run_root=job.get("run_root"), execution_manifest_sha256=job.get("execution_manifest_sha256"))
    if (any(report.get(k) != v for k, v in expected.items()) or job.get("mode") != expected_stage
            or job.get("status") not in TERMINAL or type(report.get("scientific_complete")) is not bool
            or report.get("terminal_status") != job["status"] or report.get("exit_code") != job.get("exit_code")):
        raise ValueError("Downstream root audit has another job/source/outcome")
    if report["scientific_complete"] and (job["status"] != "COMPLETED" or job.get("exit_code") != "0:0"):
        raise ValueError("Failed allocation cannot establish completed downstream work")
    pull_path = result_relative(report["pull_receipt"])
    if not pull_path.startswith(f"results/{ROUND}/pulls/"):
        raise ValueError("Require the formal nonweight pull receipt")
    pull = evidence.read(pull_path)
    wanted = dict(schema=ROUND, kind="nonweight_pull", status="verified_nonweight_snapshot", final_evidence=True,
                  weights_copied=False, sealed_initial_states_copied=False)
    selected = [r for r in pull.get("selected_jobs", []) if r.get("job_id") == job["job_id"]]
    if (any(pull.get(k) != v for k, v in wanted.items()) or len(selected) != 1
            or selected[0].get("include_run_root") is not True or selected[0].get("run_root") != job["run_root"]
            or selected[0].get("source_sha256") != FROZEN_SHA256):
        raise ValueError("Latest audit has no terminal SHA-pulled output")
    before_path = str(PurePosixPath(pull_path).parent / "inventory_before.json")
    after_path = str(PurePosixPath(pull_path).parent / "inventory_after.json")
    before, after = evidence.read(before_path), evidence.read(after_path)
    if before != after or evidence.watch(before_path) != pull.get("inventory_sha256"):
        raise ValueError("Downstream pull changed during transfer")
    for when in ("accounting_before", "accounting_after"):
        actual = pull.get(when, {}).get("jobs", {}).get(job["job_id"], {})
        if any(actual.get(k) != job.get(k) for k in ("status", "exit_code", "elapsed_seconds")):
            raise ValueError("Downstream terminal accounting differs from supervisor")
    if type(job.get("elapsed_seconds")) is not int or job["elapsed_seconds"] < 0 or job.get("gpus") != 1:
        raise ValueError("Missing complete downstream allocation cost")
    rows = {r["relative"]: r for r in pull.get("files", [])}
    original = {r["relative"]: r for r in before.get("files", [])}
    if len(rows) != len(pull.get("files", [])) or len(original) != len(before.get("files", [])):
        raise ValueError("Duplicate SHA-pull evidence")
    run_relative = PurePosixPath(job["run_root"]).relative_to(P).as_posix()
    required = {name for name, row in original.items() if name.startswith(run_relative + "/") and job["job_id"] in row.get("job_ids", [])}
    required |= {f"results/{ROUND}/job_receipts/{job['job_id']}.json", *[f"results/slurm/{job['name']}_{job['job_id']}.{ext}" for ext in ("out", "err")]}
    if not required or not any(name.startswith(run_relative + "/adapter_invocations/") for name in required):
        raise ValueError("Root audit must retain this job's adapter evidence")
    for name in required:
        relative(name)
        if expected_stage == "final" and name == run_relative + "/panel.json":
            raise ValueError("Final state-value panels must not be copied or opened locally")
        row, initial = rows.get(name, {}), original.get(name, {})
        sha = evidence.watch(name)
        if (report.get("files", {}).get(name) != sha or row.get("sha256") != sha or initial.get("sha256") != sha
                or row.get("path") != str(P / name) or initial.get("path") != str(P / name)
                or row.get("bytes") != evidence.path(name).stat().st_size or initial.get("bytes") != row.get("bytes")
                or job["job_id"] not in row.get("job_ids", []) or job["job_id"] not in initial.get("job_ids", [])
                or row.get("action") not in ("same_sha_skipped", "downloaded_verified")):
            raise ValueError("Root audit/pull/raw file SHA identity differs: " + name)
    if evidence.watch(job["invocation"]) != job["invocation_sha256"]:
        raise ValueError("Original downstream invocation changed")
    receipt = evidence.read(f"results/{ROUND}/job_receipts/{job['job_id']}.json")
    expected_receipt = dict(schema=ROUND, kind="formal_downstream_job_receipt", job_id=job["job_id"],
        stage=expected_stage, stage_key=job["stage_key"], run_root=job["run_root"],
        source_sha256=FROZEN_SHA256, adapter_sha256=ADAPTER_SHA256, invocation_sha256=job["invocation_sha256"])
    if any(receipt.get(k) != v for k, v in expected_receipt.items()) or not receipt.get("adapter_artifacts"):
        raise ValueError("Root audit lacks the exact registered wrapper/adapter receipt")
    for artifact in receipt["adapter_artifacts"]:
        name = PurePosixPath(artifact.get("path", "")).relative_to(P).as_posix()
        filename = PurePosixPath(name).name
        if (not re.fullmatch(re.escape(job["job_id"]) + r"_[0-9a-f]{32}\.(json|jsonl)", filename)
                or name != run_relative + "/adapter_invocations/" + filename
                or artifact.get("source") != str(P / f"results/{ROUND}/adapter_invocations" / filename)
                or name not in required or artifact.get("sha256") != rows[name]["sha256"]
                or artifact.get("bytes") != rows[name]["bytes"]):
            raise ValueError("Wrapper copied another job's adapter evidence")
    report = dict(report)
    report["verified_files"] = {name: evidence.watch(name) for name in sorted(required)}
    return report


def prior_contract(args, state, validated, project):
    evidence, stage, suite, methods = validated["evidence"], args.stage, validated["suite"], validated["methods"]
    jobs = formal_jobs(state)
    tag = signature(methods)[:16]
    stage_key = f"{suite}_{stage}_{tag}"
    prior = [j for j in jobs if j.get("mode") == stage and j.get("suite") == suite
             and (not j.get("method_ids") or set(j["method_ids"]) & set(methods))]
    if any(j.get("stage_key") != stage_key or j.get("method_ids") != methods for j in prior):
        raise ValueError("Another registered stage overlaps these method/state instances")
    if any(j.get("status") not in TERMINAL for j in prior):
        raise ValueError("This downstream stage already has an active or unresolved job")
    for job in prior:
        if (type(job.get("elapsed_seconds")) is not int or job["elapsed_seconds"] < 0 or job.get("gpus") != 1
                or job.get("source_sha256") != FROZEN_SHA256 or job.get("adapter_sha256") != ADAPTER_SHA256):
            raise ValueError("Every prior allocation must retain its source and complete GPU cost")
    prior.sort(key=lambda j: (j.get("submitted_utc", ""), int(j["job_id"])))
    base = f"results/{ROUND}/{suite}/downstream/{stage}/{tag}"
    output = result_relative(args.output_relative or (PurePosixPath(prior[-1]["run_root"]).relative_to(P).as_posix()
        if prior and stage in ("development", "final") else f"{base}/attempt{len(prior)+1:02d}"))
    if PurePosixPath(base) not in PurePosixPath(output).parents:
        raise ValueError("Output differs from this registered stage identity")
    review = None
    if prior:
        if not args.prior_review:
            raise ValueError("Newest terminal attempt requires its root audit and stable SHA pull")
        review = require_root_review(evidence, args.prior_review, jobs, expected_stage=stage)
        if review["job_id"] != prior[-1]["job_id"]:
            raise ValueError("Only the newest terminal attempt can authorize continuation")
        if review["scientific_complete"]:
            raise ValueError("This downstream stage is already scientifically completed")
        if review["execution_manifest_sha256"] != evidence.watch(args.execution_manifest):
            raise ValueError("Continuation cannot change its manifest/checkpoint identities")
        if stage in ("development", "final"):
            if not args.resume or str(P / output) != prior[-1]["run_root"]:
                raise ValueError("Existing rollouts require explicit resume of the same output")
            from cti_vla.evaluation import formal_trials
            adapter = load(ADAPTER, project)
            config = evidence.read(output + "/config.json")
            if (config.get("manifest") != validated["manifest"] or config.get("source_files") != validated["sources"]
                    or config.get("registration_sha256") != signature(validated["registration"])
                    or config.get("schema") != ROUND or config.get("kind") != "evaluation_run"
                    or config.get("policy_watchdog_seconds") != 60.):
                raise ValueError("Resume run config has another frozen identity")
            panel = validated["development"]
            if stage == "final":
                # A registry holds only identifiers/hashes, sufficient for the
                # raw trial validator. Never read the output's final panel.
                spec = validated["registration"]["suites"][suite]
                registry_path = spec["initial_states_root"] + "/final_registry.json"
                if evidence.watch(registry_path) != validated["matrix"]["suites"][suite]["final_registry_sha256"]:
                    raise ValueError("Released final index registry changed")
                panel = evidence.read(registry_path)
                if any("initial_state" in row for row in panel.get("states", [])):
                    raise ValueError("Final registry must contain no state values")
                panel = {**panel, "release_file_sha256": evidence.watch(args.freeze_directory + "/root_release.json")}
            elif evidence.read(output + "/panel.json") != panel or config.get("panel_signature") != signature(panel):
                raise ValueError("Resume development panel changed")
            ledger = adapter.checked_ledger(evidence.path(output + "/trials.jsonl"), signature(config),
                panel=panel, identifiers=methods, validators=formal_trials)
            if (review.get("run_signature") != signature(config) or review.get("completed_trials") != len(ledger["terminal_trial_ids"])
                    or set(ledger["invocation_job_ids"]) != {j["job_id"] for j in prior}
                    or review.get("unfinished_attempts_unknown_cost") != ledger["unfinished_attempts_unknown_cost"]
                    or len(ledger["terminal_trial_ids"]) >= len(panel["states"]) * len(methods)):
                raise ValueError("Resume audit does not match incomplete raw trials")
            report = evidence.read(output + "/closed_loop_report.json")
            if report.get("completed_trials") != len(ledger["terminal_trial_ids"]) or report.get("provenance", {}).get("run_signature") != signature(config):
                raise ValueError("Resume report and raw ledger disagree")
        elif args.resume or str(P / output) in {j["run_root"] for j in prior}:
            raise ValueError("Profile attempts use fresh directories; never resume or overwrite")
    elif args.resume or args.prior_review:
        raise ValueError("No registered prior attempt exists to resume/audit")
    failures = [j for j in prior if j["status"] != "COMPLETED" or j.get("exit_code") != "0:0"]
    if failures:
        if not args.repair_record:
            raise ValueError("Failed attempts require an explicit retained root repair record")
        repair = evidence.read(args.repair_record)
        expected = dict(schema=ROUND, kind="downstream_repair", status="reviewed", reviewed_by="root", stage_key=stage_key,
            target_source_sha256=FROZEN_SHA256, adapter_sha256=ADAPTER_SHA256,
            execution_manifest_sha256=evidence.watch(args.execution_manifest), prior_review_sha256=evidence.watch(args.prior_review))
        if any(repair.get(k) != v for k, v in expected.items()) or set(repair.get("failed_job_ids", [])) != {j["job_id"] for j in failures}:
            raise ValueError("Repair record does not bind all failed attempts and unchanged scientific identity")
        if not isinstance(repair.get("diagnosis"), str) or not repair["diagnosis"].strip() or not isinstance(repair.get("bounded_fix"), str) or not repair["bounded_fix"].strip():
            raise ValueError("Root repair must describe a concrete diagnosis and bounded correction")
    elif args.repair_record:
        raise ValueError("Repair record supplied without failed registered jobs")
    for job in jobs:
        old = PurePosixPath(job.get("run_root", "/invalid"))
        new = P / output
        if old == new and job in prior and args.resume:
            continue
        if old == new or old in new.parents or new in old.parents:
            raise ValueError("Output overlaps another registered job")
    if (local(project, output).exists()) != bool(prior and args.resume):
        raise ValueError("Local output existence differs from the explicit new/resume plan")
    return stage_key, output, prior, review


def plan(args, state, *, project=ROOT, helper=None):
    if state.get("pending_submission") is not None:
        raise ValueError("Unresolved submission blocks all new downstream submissions")
    project = Path(project).resolve()
    helper = helper or load("scripts/formal_execution_manifests.py", project)
    value = validate_inputs(args, state, project, helper)
    evidence = value["evidence"]
    key, output, prior, review = prior_contract(args, state, value, project)
    stage, suite = args.stage, value["suite"]
    if args.stop_after is not None and (stage not in ("development", "final") or type(args.stop_after) is not int or args.stop_after <= 0):
        raise ValueError("Only rollouts accept a positive engineering stop-after count")
    source = PurePosixPath(value["inventory"]["source_root_server"])
    spec, acceptance = value["registration"]["suites"][suite], value["acceptance"]
    mode = "evaluate" if stage in ("development", "final") else stage
    values = {"source-root": str(source), "source-inventory": str(P / args.source_inventory), "adapter-sha256": ADAPTER_SHA256,
        "execution-manifest": str(P / args.execution_manifest), "registration": str(P / REGISTRATION),
        "protocol": str(P / spec["protocol"]), "windows": str(P / spec["windows"]),
        "input-acceptance": str(P / acceptance["output_relative"] / "input_acceptance.json"),
        "asset-manifest": str(source / spec["model_manifest"]), "checkpoint": spec["model_root_server"],
        "oft-source": str(P / "external/openvla-oft"), "libero-source": str(P / "external/LIBERO"),
        "libero-config": str(P / "configs/libero_runtime"), "cache-directory": str(P / (".local/formal-hf-" + suite)),
        "output": str(P / output), "project-root": str(P), "policy-watchdog-seconds": "60"}
    if stage == "final":
        values.update({"final-registry": str(P / spec["initial_states_root"] / "final_registry.json"),
            "sealed-final": str(P / spec["initial_states_root"] / "sealed_final.json"),
            "release": str(P / args.freeze_directory / "root_release.json"),
            "release-sha256": evidence.watch(args.freeze_directory + "/root_release.json")})
    else:
        values["development-panel"] = str(P / value["development_path"])
    if stage in ("full", "components"):
        values.update({"global-freeze": str(P / args.freeze_directory / "global_freeze.json"), "panel": str(P / args.profile_panel)})
    if args.stop_after is not None:
        values["stop-after"] = str(args.stop_after)
    argv = [mode, *[x for name, item in values.items() for x in ("--" + name, item)]]
    if args.resume:
        argv.append("--resume")
    if stage in ("collect", "full", "components"):
        argv.append("--uncontended-gpu")
    support = {ADAPTER: evidence.watch(ADAPTER), WRAPPER: evidence.watch(WRAPPER),
        "scripts/ops/formal_downstream_supervisor.py": evidence.watch("scripts/ops/formal_downstream_supervisor.py")}
    # Runtime repeats every actual gate/checkpoint check. Local-only review and
    # pull files are bound to the invocation, not falsely assumed on the server.
    watched = {str(source / name): sha for name, sha in value["inventory"]["files"].items()}
    runtime_names = {REGISTRATION, args.source_inventory, args.execution_manifest, spec["protocol"], spec["windows"],
        *support, *[acceptance["output_relative"] + "/" + name for name in acceptance["files"]],
        *value["panel_artifacts"]}
    if stage != "final":
        runtime_names.add(value["development_path"])
    for row in value["manifest"]["methods"]:
        runtime_names.update(row[k] for k in ("receipt", "pair_config", "f01_report") if k in row)
    publish = {**support, args.source_inventory: evidence.watch(args.source_inventory), args.execution_manifest: evidence.watch(args.execution_manifest)}
    if args.freeze_directory:
        runtime_names.add(args.freeze_directory + "/global_freeze.json")
        publish[args.freeze_directory + "/global_freeze.json"] = evidence.watch(args.freeze_directory + "/global_freeze.json")
        if stage == "final":
            runtime_names.add(args.freeze_directory + "/root_release.json")
            publish[args.freeze_directory + "/root_release.json"] = evidence.watch(args.freeze_directory + "/root_release.json")
    for name in runtime_names:
        watched[str(P / relative(name))] = evidence.watch(name)
    if review:
        watched.update({str(P / name): sha for name, sha in review["verified_files"].items()})
    invocation = dict(schema=ROUND, kind="formal_downstream_invocation", version=VERSION, stage=stage, stage_key=key,
        suite=suite, method_ids=value["methods"], source_root=str(source), source_sha256=FROZEN_SHA256,
        source_inventory=str(P / args.source_inventory), source_inventory_sha256=evidence.watch(args.source_inventory),
        entrypoint=ADAPTER, adapter_sha256=ADAPTER_SHA256, wrapper=WRAPPER, wrapper_sha256=support[WRAPPER],
        support_files=support, argv=argv, run_root=str(P / output), resume=bool(args.resume),
        execution_manifest=str(P / args.execution_manifest), execution_manifest_sha256=evidence.watch(args.execution_manifest),
        registration_sha256=evidence.watch(REGISTRATION), watched_files=dict(sorted(watched.items())),
        root_evidence_sha256=dict(sorted(evidence.files.items())),
        prior_job_ids=[j["job_id"] for j in prior], prior_review=args.prior_review,
        prior_allocation_cost=[{k: j.get(k) for k in ("job_id", "status", "raw_status", "exit_code", "elapsed_seconds", "gpus")} for j in prior],
        repair_record=args.repair_record, stop_after=args.stop_after,
        scientific_settings_changed=False, final_values_read_locally=False)
    evidence.unchanged()
    invrel = f"results/{ROUND}/invocations/{key}_attempt{len(prior)+1:02d}.json"
    if local(project, invrel).exists():
        raise ValueError("Invocation already exists; resolve its outcome before another submission")
    result = dict(schema=ROUND, kind="formal_downstream_plan", invocation_relative=invrel, invocation=invocation,
        publish_files=publish, output_relative=output, output_must_exist=bool(args.resume),
        resources=dict(job_name="cti-formal-downstream", account="p_p15016", qos="cpu-500_core-l40-8_card-a800-8_card",
            partition="L40", nodes=1, ntasks=1, cpus_per_task=7, gres="gpu:l40:1", mem="64G", time="04:00:00"))
    result["plan_sha256"] = signature(result)
    return result


def submission_command(plan_value, invocation_sha256):
    invocation, resources = plan_value["invocation"], plan_value["resources"]
    source = invocation["source_root"]
    lines = ["set -euo pipefail", "cd " + shlex.quote(source),
        "export PYTHONPATH=" + shlex.quote(source + "/src") + " PYTHONDONTWRITEBYTECODE=1",
        "export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7 TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1",
        "export TOKENIZERS_PARALLELISM=false MUJOCO_GL=egl LIBERO_CONFIG_PATH=" + shlex.quote(str(P / "configs/libero_runtime")),
        "exec srun " + " ".join(shlex.quote(x) for x in [str(H / "venv/bin/python"), str(P / WRAPPER),
            "--invocation", str(P / plan_value["invocation_relative"]), "--invocation-sha256", invocation_sha256])]
    flags = ["sbatch", "--parsable", "--no-requeue", *["--" + k.replace("_", "-") + "=" + str(v) for k, v in resources.items()],
        "--output=results/slurm/%x_%j.out", "--error=results/slurm/%x_%j.err", "--wrap", "bash -lc " + shlex.quote("\n".join(lines))]
    return "cd " + shlex.quote(str(P)) + " && " + " ".join(shlex.quote(x) for x in flags)


class Transport:
    """Only explicit submit uses this transport; CPU tests replace it entirely."""
    def __init__(self, project):
        self.project = Path(project)

    def remote(self, code):
        #173 snapshot paths exceed Windows' process command-line limit when
        # embedded in -c. Send the exact script on stdin, without a shell heredoc.
        command = shlex.quote(str(H / "venv/bin/python")) + " -"
        return subprocess.run(["ssh", "-o", "BatchMode=yes", "tongji-cvpr", command], check=True,
                              input=code, capture_output=True, text=True, timeout=180).stdout

    def prepare(self, value, invpath):
        uploads = {**value["publish_files"], value["invocation_relative"]: digest(invpath)}
        watched = {**value["invocation"]["watched_files"], str(P / value["invocation_relative"]): digest(invpath)}
        request = dict(watched=watched, uploads={str(P / name): sha for name, sha in uploads.items()},
            output=value["invocation"]["run_root"], exists=value["output_must_exist"])
        code = """import hashlib,json,os
from pathlib import Path
r=REQUEST
missing=[]
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as stream:
  for block in iter(lambda:stream.read(8<<20),b''): h.update(block)
 return h.hexdigest()
for name,sha in r['watched'].items():
 p=Path(name)
 if p.is_symlink() or p.resolve()!=p: raise ValueError('Noncanonical watched path')
 if p.exists():
  if not p.is_file() or digest(p)!=sha: raise ValueError('Remote registered input differs: '+name)
 elif name not in r['uploads']: raise ValueError('Remote runtime evidence absent: '+name)
 else:
  p.parent.mkdir(parents=True,exist_ok=True); missing.append(name)
if Path(r['output']).exists()!=r['exists']: raise ValueError('Remote output existence differs')
print(json.dumps(missing))
""".replace("REQUEST", repr(request), 1)
        missing = json.loads(self.remote(code))
        if not isinstance(missing, list) or len(set(missing)) != len(missing) or set(missing) - set(request["uploads"]):
            raise ValueError("Unexpected remote upload request")
        for name in missing:
            relative_name = PurePosixPath(name).relative_to(P).as_posix()
            path = local(self.project, relative_name)
            stage = name + "." + uuid.uuid4().hex + ".partial"
            subprocess.run(["scp", "-q", str(path), "tongji-cvpr:" + stage], check=True, timeout=180)
            publish = """import hashlib,os
from pathlib import Path
target,stage,sha=VALUES
p,t=Path(target),Path(stage)
if hashlib.sha256(t.read_bytes()).hexdigest()!=sha: raise ValueError('Uploaded SHA mismatch')
if p.exists():
 if hashlib.sha256(p.read_bytes()).hexdigest()!=sha: raise ValueError('Existing publication differs')
else: os.link(t,p)
t.unlink()
""".replace("VALUES", repr((name, stage, request["uploads"][name])), 1)
            self.remote(publish)

    def submit(self, command):
        return subprocess.run(["ssh", "-o", "BatchMode=yes", "tongji-cvpr", command], capture_output=True, text=True, timeout=180)


def submit_plan(value, state, *, project, supervisor, transport, expected_plan_sha256):
    """Caller holds the original supervisor lock and refreshed registered IDs."""
    if state.get("pending_submission") is not None or value.get("plan_sha256") != expected_plan_sha256:
        raise ValueError("Unresolved submission or changed reviewed plan")
    if signature({k: v for k, v in value.items() if k != "plan_sha256"}) != value["plan_sha256"]:
        raise ValueError("Plan content changed")
    helper = load("scripts/formal_execution_manifests.py", project)
    invocation = {**value["invocation"], "registered_utc": datetime.now(timezone.utc).isoformat(), "plan_sha256": value["plan_sha256"]}
    path = local(project, value["invocation_relative"])
    if path.exists():
        raise ValueError("Invocation already exists; no automatic retry")
    helper.immutable_write(path, invocation)
    state["pending_submission"] = dict(stage_key=invocation["stage_key"], invocation=value["invocation_relative"],
        invocation_sha256=digest(path), plan_sha256=value["plan_sha256"], phase="preparing_downstream", utc=invocation["registered_utc"])
    supervisor.write(supervisor.STATE, state)
    transport.prepare(value, path)
    state["pending_submission"]["phase"] = "sbatch_outcome_pending"
    supervisor.write(supervisor.STATE, state)
    answer = transport.submit(submission_command(value, digest(path)))
    if answer.returncode or not re.fullmatch(r"[0-9]+(?:;[A-Za-z0-9_.-]+)?", answer.stdout.strip()):
        raise RuntimeError("Submission outcome unresolved; pending retained, do not resubmit")
    job_id = answer.stdout.strip().split(";")[0]
    if job_id in {str(j.get("job_id")) for j in state["registered_jobs"]}:
        raise RuntimeError("Returned job ID already registered; retain pending for root reconciliation")
    job = dict(job_id=job_id, name="cti-formal-downstream", experiment=ROUND, mode=invocation["stage"],
        stage_key=invocation["stage_key"], suite=invocation["suite"], method_ids=invocation["method_ids"],
        source_root=invocation["source_root"], source_sha256=FROZEN_SHA256, adapter_sha256=ADAPTER_SHA256,
        run_root=invocation["run_root"], invocation=value["invocation_relative"], invocation_sha256=digest(path),
        execution_manifest_sha256=invocation["execution_manifest_sha256"], status="SUBMITTED", gpus=1,
        submitted_utc=invocation["registered_utc"], resume=invocation["resume"], prior_job_ids=invocation["prior_job_ids"],
        purpose="Registered frozen formal downstream stage; all attempts and GPU allocations retained")
    state["registered_jobs"].append(job)
    state["pending_submission"] = None
    state["stage"] = ROUND + "_" + invocation["stage"]
    state["current_round_cost"]["registered_jobs"] = len(formal_jobs(state))
    supervisor.write(supervisor.STATE, state)
    helper.immutable_write(local(project, f"results/{ROUND}/submissions/{job_id}.json"), job)
    return job


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "submit"))
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--execution-manifest", required=True)
    parser.add_argument("--source-inventory", default=SOURCE_INVENTORY)
    for name in ("output-relative", "freeze-directory", "profile-panel", "prior-review", "collection-review", "repair-record"):
        parser.add_argument("--" + name)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--stop-after", type=int)
    parser.add_argument("--expected-plan-sha256")
    parser.add_argument("--root-submit", action="store_true")
    args = parser.parse_args()
    supervisor = load("scripts/formal_supervisor.py")
    if args.command == "plan":
        value = plan(args, supervisor.read(ROOT / STATE))
    else:
        if not args.root_submit or not args.expected_plan_sha256:
            parser.error("submit requires explicit --root-submit and the reviewed --expected-plan-sha256")
        with supervisor.supervisor_lock():
            state = supervisor.read(supervisor.STATE)
            if state.get("pending_submission") is not None:
                raise ValueError("Resolve pending submission before any remote calls")
            supervisor.refresh(state)
            value = plan(args, state)
            value = submit_plan(value, state, project=ROOT, supervisor=supervisor, transport=Transport(ROOT),
                                expected_plan_sha256=args.expected_plan_sha256)
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

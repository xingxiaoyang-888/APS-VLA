"""Root, local-only review of SHA-pulled formal downstream evidence.

No simulator, checkpoint deserialization, SSH, submission, or state mutation.
A passed review means reconstructible evidence, not necessarily scientific completion.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
from functools import lru_cache
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
VERSION = "formal-downstream-review-v1"


@lru_cache(maxsize=None)
def load(name):
    spec = importlib.util.spec_from_file_location("downstream_review_" + Path(name).stem, ROOT / name)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), "Invalid SHA256 identity")
    return value


def number(value, name, *, positive=False):
    require(type(value) in (int, float) and math.isfinite(value) and (value > 0 if positive else value >= 0),
            "Invalid nonnegative cost/measurement: " + name)
    return value


def lines(path):
    """Read-only and streaming: never repair or truncate even valid JSON without LF."""
    with Path(path).open("rb") as stream:
        for index, raw in enumerate(stream, 1):
            require(raw.endswith(b"\n") and raw.strip(), f"Incomplete/empty JSONL line {index}: {path.name}")
            row = json.loads(raw, parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Nonfinite JSON: " + x)))
            require(isinstance(row, dict), "Journal event must be an object")
            yield row


def remote_relative(value, scheduler):
    path = PurePosixPath(value)
    require(path.is_absolute() and str(path) == value and ".." not in path.parts, "Noncanonical server path")
    return scheduler.relative(path.relative_to(scheduler.P).as_posix())


def options(invocation):
    values, argv = {}, invocation["argv"]
    index = 1
    while index < len(argv):
        flag = argv[index]
        require(flag.startswith("--") and flag not in values, "Duplicate or positional adapter argument")
        if flag in ("--resume", "--uncontended-gpu"):
            values[flag] = True
            index += 1
        else:
            require(index + 1 < len(argv) and not argv[index + 1].startswith("--"), "Missing adapter argument")
            values[flag] = argv[index + 1]
            index += 2
    return values


class CandidateEvidence:
    """Verify a candidate in memory before publishing any passed artifact."""
    def __init__(self, evidence, candidate):
        self.evidence, self.candidate = evidence, candidate

    def read(self, name):
        return self.candidate if name == "in_memory_candidate" else self.evidence.read(name)

    def __getattr__(self, name):
        return getattr(self.evidence, name)


def pulled_candidate(evidence, scheduler, job, pull_path, jobs):
    pull = evidence.read(scheduler.result_relative(pull_path))
    output = remote_relative(job["run_root"], scheduler)
    # Screen every path before hashing. In particular, never open an accidentally
    # copied final state-value panel, irrespective of a purported pull attestation.
    for row in pull.get("files", []):
        name = scheduler.relative(row["relative"])
        require(not (job["mode"] == "final" and name == output + "/panel.json"), "Final value panel must not be read")
    candidate = dict(schema=scheduler.ROUND, kind="root_downstream_review", status="passed", reviewed_by="root",
        job_id=job["job_id"], stage=job["mode"], stage_key=job["stage_key"], source_sha256=scheduler.FROZEN_SHA256,
        adapter_sha256=scheduler.ADAPTER_SHA256, invocation_sha256=job["invocation_sha256"], run_root=job["run_root"],
        execution_manifest_sha256=job["execution_manifest_sha256"], terminal_status=job["status"], exit_code=job["exit_code"],
        scientific_complete=False, pull_receipt=pull_path, files={row["relative"]: row["sha256"] for row in pull.get("files", [])})
    checked = scheduler.verify_review_pull(CandidateEvidence(evidence, candidate), "in_memory_candidate", jobs, expected_stage=job["mode"])
    candidate["files"] = checked["verified_files"]
    before = evidence.read(str(PurePosixPath(pull_path).parent / "inventory_before.json"))
    require(not any(str(r.get("job_id")) == job["job_id"] for r in before.get("missing", [])), "Incomplete terminal pull inventory")
    for row in before.get("excluded", []):
        if str(row.get("job_id")) == job["job_id"]:
            final_panel = (job["mode"] == "final" and row.get("path") == job["run_root"] + "/panel.json"
                           and row.get("reason") == "final_rollout_panel_contains_initial_state_values")
            evaluation_lock = (job["mode"] in ("development", "final")
                               and row.get("path") == job["run_root"] + "/.evaluation.lock"
                               and row.get("reason") == "unregistered_nonweight_extension")
            require(final_panel or evaluation_lock, "Unexpected excluded downstream evidence")
    return candidate


def validate_invocation(evidence, scheduler, helper, state, job, invocation):
    fields = ("stage_key", "suite", "method_ids", "run_root", "source_sha256", "adapter_sha256", "execution_manifest_sha256")
    require(all(invocation.get(k) == job.get(k) for k in fields) and invocation["stage"] == job["mode"], "Registered invocation/job mismatch")
    for name, checksum in invocation["support_files"].items():
        require(evidence.watch(name) == checksum, "Downstream support source changed")
    opt = options(invocation)
    source = PurePosixPath(invocation["source_root"])
    stage = job["mode"]
    registration = helper.registration_contract(evidence, scheduler.REGISTRATION)
    suite = invocation["suite"]
    require(suite in registration["suites"], "Unregistered suite")
    spec = registration["suites"][suite]
    # This comparison precedes every panel loader, including preparation paths.
    development = str(scheduler.P / spec["initial_states_root"] / "development.json")
    require((opt.get("--development-panel") == development if stage != "final" else "--development-panel" not in opt),
            "Development input must be the registered panel, never a sealed path")
    freeze = None
    if stage == "final":
        require(opt.get("--final-registry") == str(scheduler.P / spec["initial_states_root"] / "final_registry.json")
                and opt.get("--sealed-final") == str(scheduler.P / spec["initial_states_root"] / "sealed_final.json"), "Final metadata paths differ")
        freeze = str(PurePosixPath(remote_relative(opt["--release"], scheduler)).parent)
    elif stage in ("full", "components"):
        freeze = str(PurePosixPath(remote_relative(opt["--global-freeze"], scheduler)).parent)
    manifest_path = remote_relative(invocation["execution_manifest"], scheduler)
    collection_review = None
    if stage in ("full", "components"):
        panel_path = remote_relative(opt["--panel"], scheduler)
        matches = []
        for path, checksum in invocation.get("root_evidence_sha256", {}).items():
            if "downstream_reviews" in PurePosixPath(path).parts:
                item = evidence.read(path)
                require(evidence.watch(path) == checksum, "Original collection review changed")
                if item.get("stage") == "collect" and item.get("run_root") + "/panel.json" == opt["--panel"]:
                    matches.append(path)
        require(len(matches) == 1, "Timing must bind exactly one original collection root review")
        collection_review = matches[0]
    args = SimpleNamespace(stage=stage, execution_manifest=manifest_path, source_inventory=remote_relative(invocation["source_inventory"], scheduler),
        freeze_directory=freeze, profile_panel=remote_relative(opt["--panel"], scheduler) if "--panel" in opt else None,
        collection_review=collection_review, prior_review=None, repair_record=None)
    value = scheduler.validate_inputs(args, state, evidence.project, helper)
    for name, checksum in value["evidence"].files.items():
        require(evidence.watch(name) == checksum, "Gate inputs changed")
    scheduler.validate_invocation_shape(evidence, job, invocation, value["source_provenance"])
    require(invocation.get("source_provenance") == value["source_provenance"], "Invocation original source provenance differs")
    require(job.get("source_provenance_sha256") == scheduler.signature(value["source_provenance"]),
        "Registered downstream job lost its source provenance identity")
    prefix = scheduler.resume_prefix_inputs(invocation)
    if prefix:
        prior = evidence.read(invocation["prior_review"])
        require(evidence.watch(invocation["prior_review"]) == invocation["root_evidence_sha256"].get(invocation["prior_review"]),
            "Resume original root review changed")
        for path, checksum in prefix.items():
            require(prior.get("files", {}).get(remote_relative(path, scheduler)) == checksum,
                "Resume execution-before prefix SHA differs from the prior root review")
    require(invocation["source_inventory_sha256"] == evidence.watch(args.source_inventory)
            and invocation["registration_sha256"] == evidence.watch(scheduler.REGISTRATION)
            and invocation["execution_manifest_sha256"] == evidence.watch(manifest_path), "Invocation immutable input hash mismatch")
    expected = {"--source-root": str(source), "--source-inventory": str(scheduler.P / args.source_inventory),
        "--adapter-sha256": scheduler.ADAPTER_SHA256, "--execution-manifest": invocation["execution_manifest"],
        "--registration": str(scheduler.P / scheduler.REGISTRATION), "--protocol": str(scheduler.P / spec["protocol"]),
        "--windows": str(scheduler.P / spec["windows"]), "--input-acceptance": str(scheduler.P / value["acceptance"]["output_relative"] / "input_acceptance.json"),
        "--asset-manifest": str(source / spec["model_manifest"]), "--checkpoint": spec["model_root_server"],
        "--oft-source": str(scheduler.P / "external/openvla-oft"), "--libero-source": str(scheduler.P / "external/LIBERO"),
        "--libero-config": str(scheduler.P / "configs/libero_runtime"), "--cache-directory": str(scheduler.P / (".local/formal-hf-" + suite)),
        "--output": job["run_root"], "--project-root": str(scheduler.P), "--policy-watchdog-seconds": "60"}
    if stage == "final":
        expected.update({"--final-registry": str(scheduler.P / spec["initial_states_root"] / "final_registry.json"),
            "--sealed-final": str(scheduler.P / spec["initial_states_root"] / "sealed_final.json"),
            "--release": str(scheduler.P / freeze / "root_release.json"), "--release-sha256": evidence.watch(freeze + "/root_release.json")})
    else:
        expected["--development-panel"] = development
    if stage in ("full", "components"):
        expected.update({"--global-freeze": str(scheduler.P / freeze / "global_freeze.json"), "--panel": str(scheduler.P / args.profile_panel)})
    if stage in ("collect", "full", "components"):
        expected["--uncontended-gpu"] = True
    if invocation.get("stop_after") is not None:
        require(stage in ("development", "final") and type(invocation["stop_after"]) is int and invocation["stop_after"] > 0, "Invalid engineering stop-after")
        expected["--stop-after"] = str(invocation["stop_after"])
    if invocation["resume"]:
        expected["--resume"] = True
    require(opt == expected, "Exact registered downstream arguments differ")
    key = f"{suite}_{stage}_{scheduler.signature(value['methods'])[:16]}"
    require(job["stage_key"] == key and invocation["method_ids"] == value["methods"]
            and PurePosixPath(f"results/{scheduler.ROUND}/{suite}/downstream/{stage}/{scheduler.signature(value['methods'])[:16]}")
                in PurePosixPath(remote_relative(job["run_root"], scheduler)).parents, "Stage/output identity differs from registered method set")
    value.update(args=args, opt=opt, invocation=invocation, output=remote_relative(job["run_root"], scheduler))
    return value


def runtime_inputs(evidence, scheduler, value, config):
    """Verify declared checkpoint hashes without opening checkpoint bytes."""
    inv, opt = value["invocation"], value["opt"]
    suite = value["registration"]["suites"][value["suite"]]
    paths = [opt[k] for k in ("--execution-manifest", "--registration", "--asset-manifest", "--protocol", "--windows", "--input-acceptance")]
    gate = PurePosixPath(opt["--input-acceptance"]).parent
    paths += [str(gate / n) for n in ("input_calls.jsonl", "resume_acceptance.json", "f03_calls.jsonl")]
    primary = next(p for p in value["registration"]["pairs"] if p["suite"] == value["suite"] and p["visual_tokens"] == 128 and p["seed"] == 17)
    paths.append(str(scheduler.P / primary["path"]))
    stage = inv["stage"]
    if stage == "final":
        paths += [opt[k] for k in ("--release", "--final-registry", "--sealed-final")]
    else:
        paths.append(opt["--development-panel"])
    if stage in ("collect", "full", "components"):
        paths += [str(PurePosixPath(inv["source_root"]) / n) for n in ("scripts/profile_formal.py", "scripts/eval_libero.py", "src/cti_vla/evaluation/formal_profiling.py")]
    if stage in ("full", "components"):
        paths += [opt["--global-freeze"], opt["--panel"]]
    weights = {}
    for row in value["manifest"]["methods"]:
        if row["identity"]["method"] in ("A", "B"):
            weights[row["checkpoint"]] = row["identity"]["checkpoint_sha256"]
            paths += [row["checkpoint"], *[str(scheduler.P / row[k]) for k in ("receipt", "pair_config", "f01_report")],
                      str((scheduler.P / row["f01_report"]).parent / "operator_calls.jsonl")]
    watched = config.get("watched_files", {})
    require(set(watched) == set(paths), "Runtime input/checkpoint watch set differs from frozen runner")
    source = PurePosixPath(inv["source_root"])
    for path, checksum in watched.items():
        sha(checksum)
        if path in weights:
            require(checksum == weights[path], "Runtime selected checkpoint hash differs")
        elif stage == "final" and path == opt["--sealed-final"]:
            # Opaque server attestation only. Registry+release and raw identities
            # are checked locally; never stat/hash/read the state-value file.
            continue
        else:
            p = PurePosixPath(path)
            name = p.relative_to(source).as_posix() if source in p.parents else remote_relative(path, scheduler)
            require(evidence.watch(name) == checksum, "Runtime input changed: " + name)
    require(config.get("source_files") == value["sources"] and config.get("manifest") == value["manifest"]
            and config.get("registration_sha256") == scheduler.signature(value["registration"]), "Runtime frozen method/source/config mismatch")
    asset = evidence.read(suite["model_manifest"])
    return dict(repository=asset["repository"], revision=asset["revision"], file_count=len(asset["files"]), total_bytes=asset["total_bytes"])


def adapters(evidence, scheduler, value, job, config, files):
    wrapper = evidence.read(f"results/{scheduler.ROUND}/job_receipts/{job['job_id']}.json")
    require(wrapper.get("wrapper_sha256") == value["invocation"]["wrapper_sha256"] and wrapper.get("stage_completed_claimed") is False,
            "Wrapper identity/completion claim differs")
    number(wrapper.get("wall_seconds"), "wrapper wall")
    require(wrapper["wall_seconds"] <= job["elapsed_seconds"] + 1, "Wrapper wall exceeds allocation")
    if job["status"] == "COMPLETED" and job["exit_code"] == "0:0":
        require(wrapper.get("status") == "returned" and wrapper.get("exit_code") == 0, "Successful Slurm job has failed wrapper")
    archive = value["output"] + "/adapter_invocations/"
    names = [remote_relative(a["path"], scheduler) for a in wrapper["adapter_artifacts"]]
    receipts = [n for n in names if n.endswith(".json")]
    require(len(receipts) == 1 and set(names) == {receipts[0], receipts[0][:-5] + ".jsonl"}, "Exactly one adapter attempt per registered wrapper required")
    receipt = evidence.read(receipts[0])
    journal_path = receipts[0][:-5] + ".jsonl"
    events = list(lines(evidence.path(journal_path)))
    attempt = PurePosixPath(receipts[0]).stem
    mode = "evaluate" if job["mode"] in ("development", "final") else job["mode"]
    inv = value["invocation"]
    expected = dict(schema=scheduler.ROUND, kind="formal_evaluation_adapter", version="formal-frozen-evaluation-adapter-v1", attempt_id=attempt,
        job_id=job["job_id"], mode=mode, resume=inv["resume"], output=job["run_root"], source_root=inv["source_root"],
        source_inventory=inv["source_inventory"], source_inventory_sha256=inv["source_inventory_sha256"],
        frozen_source_sha256=scheduler.FROZEN_SHA256, verified_frozen_file_count=173,
        adapter_path=str(scheduler.P / scheduler.ADAPTER), adapter_sha256=scheduler.ADAPTER_SHA256,
        execution_manifest_sha256=inv["execution_manifest_sha256"], registration_sha256=scheduler.signature(value["registration"]),
        eval_script_sha256=value["inventory"]["files"]["scripts/eval_formal_selector_libero.py"],
        legacy_validator_file_sha256=value["inventory"]["files"]["scripts/eval_libero.py"])
    # Version is pinned by the adapter's immutable bytes; use its declared constant.
    expected["version"] = load(scheduler.ADAPTER).VERSION
    require(all(receipt.get(k) == v for k, v in expected.items()), "Archived adapter identity mismatch")
    require(events and events[0].get("event") == "adapter_start" and events[-1].get("event") == "adapter_end", "Incomplete adapter journal")
    require(all(e.get("attempt_id") == attempt and e.get("job_id") == job["job_id"] and isinstance(e.get("utc"), str) for e in events), "Mixed adapter attempts")
    initial = events[0].get("identity", {})
    require(all(initial.get(k) == v for k, v in expected.items()) and all(receipt.get(k) == v for k, v in initial.items()), "Adapter start/receipt differs")
    require(receipt.get("events_path") == str(scheduler.P / f"results/{scheduler.ROUND}/adapter_invocations" / (attempt + ".jsonl"))
            and receipt.get("events_sha256") == files[journal_path] and receipt.get("frozen_source_unchanged") is True,
            "Adapter journal hash/source finalization missing")
    require(receipt.get("status") in ("returned", "failed") and events[-1].get("status") == receipt["status"]
            and events[-1].get("runner_status") == receipt.get("runner_status"), "Adapter final outcome differs")
    require(wrapper.get("adapter_receipts") == [dict(path=str(scheduler.P / receipts[0]), status=receipt["status"], runner_status=receipt.get("runner_status"))],
            "Wrapper adapter outcome differs")
    enters = [i for i, e in enumerate(events) if e["event"] == "bindings_enter"]
    exits = [i for i, e in enumerate(events) if e["event"] == "bindings_restored"]
    require(len(enters) == len(exits) == 1 and 0 < enters[0] < exits[0] < len(events)-1, "Adapter scoped binding lifecycle incomplete")
    enter, restored = events[enters[0]], events[exits[0]]
    bindings = enter.get("bindings", [])
    source = PurePosixPath(inv["source_root"])
    required = [dict(kind="private_module_function_binding", snapshot=str(source), target_file=str(source / "scripts/eval_formal_selector_libero.py"),
        target_symbol="verify_checkout", replacement_file=str(source / "scripts/eval_libero.py"), replacement_symbol="verify_source_checkout"),
        dict(kind="scoped_exact_script_loader", snapshot=str(source), target_file=str(source / "src/cti_vla/evaluation/future_profiling.py"),
        target_symbol="cti_vla.evaluation.future_profiling.load_script", intercepted_name="eval_formal_selector_libero", other_loads="original unchanged")]
    require(len(bindings) == 2 and receipt.get("bindings") == bindings, "Adapter binding receipt differs")
    for binding, spec in zip(bindings, required):
        require(all(binding.get(k) == v for k, v in spec.items()), "Adapter changed scoped symbols or snapshot")
        sha(binding.get("original_code_sha256")); sha(binding.get("adapter_binding_code_sha256"))
    sha(bindings[0].get("replacement_code_sha256"))
    require(restored.get("original_verify_code_sha256") == bindings[0]["original_code_sha256"]
            and restored.get("original_loader_code_sha256") == bindings[1]["original_code_sha256"], "Adapter did not restore original functions")
    for field in ("frozen_execute_code_sha256", "frozen_trial_loop_code_sha256"):
        sha(receipt.get(field)); require(initial.get(field) == receipt[field], "Adapter execute/trial function identity changed")
    require(enter.get("frozen_execute_code_sha256") == receipt["frozen_execute_code_sha256"], "Frozen execute binding changed")
    allowed = {"adapter_start", "adapter_end", "bindings_enter", "bindings_restored", "official_source_verified", "private_eval_loader_used", "resume_preflight_passed"}
    require(all(e["event"] in allowed for e in events), "Unrecognized adapter event")
    verified = {}
    for i, event in enumerate(events):
        if event["event"] == "private_eval_loader_used":
            require(mode != "evaluate" and enters[0] < i < exits[0] and event.get("snapshot") == str(source)
                    and event.get("script") == "eval_formal_selector_libero", "Adapter intercepted another loader")
        if event["event"] == "official_source_verified":
            require(enters[0] < i < exits[0], "Source verification outside scoped binding")
            key = {str(scheduler.P / "external/openvla-oft"): "openvla_oft", str(scheduler.P / "external/LIBERO"): "libero"}.get(event.get("path"))
            require(key is not None and key not in verified, "Unexpected/duplicate official checkout attestation")
            row = event["verification"]
            require(row.get("revision") == event.get("expected_revision") and row.get("verification") == "archive_all_files_sha256"
                    and type(row.get("file_count")) is int and row["file_count"] > 0, "Missing archive all-files verification")
            sha(row.get("archive_sha256")); sha(row.get("inventory_sha256"))
            verified[key] = row
    if mode in ("evaluate", "collect"):
        from cti_vla.data.formal_windows import LIBERO_REVISION
        from cti_vla.evaluation.libero_runtime import OFT_COMMIT
        require(set(verified) == {"libero", "openvla_oft"} and verified["libero"]["revision"] == LIBERO_REVISION
                and verified["openvla_oft"]["revision"] == OFT_COMMIT, "Official source revisions differ")
        official = evidence.read("results/setup/runtime_sources.json")
        for key, suffix in (("libero", "external/LIBERO"), ("openvla_oft", "external/openvla-oft")):
            matches = [r for r in official.get("sources", []) if r.get("directory") == str(scheduler.P / suffix)]
            require(len(matches) == 1 and all(verified[key].get(k) == matches[0].get(k) for k in ("revision", "archive_sha256")),
                    "Verified external archive differs from registered setup")
    else:
        require(not verified, "Timing must not create fresh simulator observations")
    if mode != "evaluate":
        require(receipt.get("profiler_script_sha256") == value["inventory"]["files"]["scripts/profile_formal.py"], "Profiler source differs")
        for field in ("frozen_profiler_run_code_sha256", "frozen_profiler_collect_code_sha256"):
            sha(receipt.get(field)); require(initial.get(field) == receipt[field], "Profiler function identity changed")
    receipt["verified_official_sources"] = verified
    return receipt


def verify_saved_provenance(evidence, report, jobs, *, scheduler=None):
    """Leaf verifier shared by E04 and release consumers; no recursive review.

    This rechecks source and actual runtime provenance. The full review() still
    rebuilds scientific trials/profiling and cost independently. No mutable
    supervisor file or final state values are opened here.
    """
    scheduler = scheduler or load("scripts/ops/formal_downstream_supervisor.py")
    selected = [j for j in jobs if j.get("job_id") == report.get("job_id")]
    require(len(selected) == 1, "Saved review job is not uniquely registered")
    job = selected[0]
    snapshot = report.get("registered_jobs_at_review")
    require(isinstance(snapshot, list) and snapshot, "Immutable registered job snapshot missing")
    saved = scheduler.formal_jobs({"registered_jobs": snapshot})
    require(len(saved) == len(snapshot) and all(j["status"] in scheduler.TERMINAL for j in saved),
        "Review job snapshot must contain only registered terminal formal jobs")
    current = {j["job_id"]: j for j in jobs}
    provenance = scheduler.provenance_helper(evidence)
    for item in saved:
        actual = current.get(item["job_id"])
        require(actual is not None and provenance.job_identity(item) == provenance.job_identity(actual),
            "Saved terminal job identity differs from registered accounting")
        for key in ("method_ids", "adapter_sha256", "execution_manifest_sha256", "downstream_asset_compatibility", "source_provenance_sha256"):
            require(item.get(key) == actual.get(key), "Saved downstream execution identity changed: " + key)
    require(job["job_id"] in {j["job_id"] for j in saved}, "Review omitted its own terminal allocation")
    inventory = evidence.read(scheduler.SOURCE_INVENTORY)
    registration = evidence.read(scheduler.REGISTRATION)
    invocation = evidence.read(job["invocation"])
    require(evidence.watch(job["invocation"]) == job["invocation_sha256"], "Saved invocation SHA differs")
    manifest = evidence.read(remote_relative(invocation["execution_manifest"], scheduler))
    require(evidence.watch(remote_relative(invocation["execution_manifest"], scheduler)) == invocation["execution_manifest_sha256"],
        "Saved execution manifest SHA differs")
    proof = scheduler.source_provenance(evidence, registration=registration, suite=job["suite"],
        inventory=inventory, rows=manifest["methods"], jobs=jobs)
    require(report.get("source_provenance") == proof == invocation.get("source_provenance")
        and job.get("source_provenance_sha256") == scheduler.signature(proof), "Saved source proof cannot be rebuilt")
    scheduler.validate_invocation_shape(evidence, job, invocation, proof)
    raw_jobs = report.get("raw_invocation_job_ids")
    require(isinstance(raw_jobs, list) and raw_jobs, "Saved review omitted its raw invocation allocations")
    require(report.get("cost") == allocation_cost(evidence, scheduler, jobs, job, invocation, raw_jobs),
        "Saved review allocation history/cost cannot be rebuilt")
    if job["suite"] in scheduler.ASSET_SUITES:
        output = remote_relative(job["run_root"], scheduler)
        value = dict(invocation=invocation, output=output, registration=registration, inventory=inventory)
        config = evidence.read(output + "/config.json")
        old = adapters(evidence, scheduler, value, job, config, report["files"])
        runtime = provenance.review_invocation(evidence, job=job, invocation=invocation,
            wrapper_receipt=evidence.read(f"results/{scheduler.ROUND}/job_receipts/{job['job_id']}.json"),
            inventory=inventory, pull_receipt=report["pull_receipt"],
            source_provenance=proof, legacy_adapter_review=old)
        require(report.get("asset_runtime_review") == runtime, "Saved actual runtime proof cannot be rebuilt")
    else:
        receipt = evidence.read(f"results/{scheduler.ROUND}/job_receipts/{job['job_id']}.json")
        require("asset_runtime_review" not in report and not any(k in receipt for k in (
            "downstream_asset_compatibility", "asset_compatibility_artifacts", "runtime_compatibility", "component_compatibility")),
            "Legacy runtime cannot retain an asset compatibility claim")
        require(not any("/asset_compatibility/" in name for name in report.get("files", {})),
            "Legacy output contains unexpected asset execution artifacts")
    return proof


def trajectory(row, identity, *, selection=True):
    import numpy as np
    from cti_vla.evaluation.formal_runtime import FORMAL_SUITES
    validator = load("scripts/analyze_formal.py").validate_chunk
    status = row.get("status")
    require(status in ("completed", "policy_error", "infrastructure_error") and type(row.get("success")) is bool, "Invalid raw trajectory outcome")
    require(status == "completed" or row["success"] is False, "Failed attempt cannot be success")
    controls = row.get("control_steps")
    require(type(controls) is int and 0 <= controls <= FORMAL_SUITES[identity["suite"]]["max_steps"], "Invalid control horizon")
    require(row.get("wait_steps") == 10 or (status == "infrastructure_error" and type(row.get("wait_steps")) is int and 0 <= row["wait_steps"] <= 10), "Wait-step evidence differs")
    chunks = row.get("chunks")
    require(isinstance(chunks, list), "Missing raw action chunks")
    for chunk in chunks:
        if not selection:
            require("retained_indices" not in chunk.get("metadata", {}) and identity["method"] == "dense", "Collection selection instrumentation differs")
            chunk = {**chunk, "metadata": {**chunk["metadata"], "retained_indices": list(range(512))}}
        validator(chunk, identity)
        sha(chunk.get("observation_sha256"))
    actions = np.asarray(row.get("executed_actions"), dtype=np.float64)
    submitted = controls + int(status == "infrastructure_error" and row.get("error_phase") == "environment" and actions.size == (controls + 1) * 7)
    require(actions.size == submitted * 7 and (not submitted or actions.shape == (submitted, 7)) and np.isfinite(actions).all()
            and np.all(np.abs(actions) <= 1.00001), "Executed actions missing/invalid")
    # Infrastructure failure can occur after querying a chunk, before stepping.
    expected_starts = list(range(0, controls, 8))
    actual_starts = [c.get("control_step") for c in chunks]
    allowed_extra = status == "infrastructure_error" and row.get("error_phase") == "environment" and controls % 8 == 0 and actual_starts == expected_starts + [controls]
    require(actual_starts == expected_starts or allowed_extra, "Chunk/control queue cadence differs")
    calls = row.get("policy_calls")
    require(type(calls) is int and calls == len(chunks) + int(status == "policy_error"), "Policy call count differs from raw chunks")
    if submitted:
        require(chunks and np.array_equal(actions, np.concatenate([c["environment_actions"] for c in chunks])[:submitted]), "Executed actions differ from policy chunks")
    if status == "completed":
        require(controls > 0 and ((row["success"] and row.get("termination") == "environment_success") or
                (not row["success"] and row.get("termination") == "task_horizon" and controls == FORMAL_SUITES[identity["suite"]]["max_steps"])), "Success/horizon termination differs")
    if "wall_seconds" in row:
        number(row["wall_seconds"], "trajectory wall")


def rollout(evidence, scheduler, value, job, config, adapter):
    from cti_vla.evaluation import formal_trials as trials
    from cti_vla.data.formal_initial_states import validate_formal_final_registry
    output = value["output"]
    require(config.get("schema") == scheduler.ROUND and config.get("kind") == "evaluation_run" and config.get("policy_watchdog_seconds") == 60., "Rollout config mismatch")
    require(config.get("source_verification") == adapter["verified_official_sources"], "Runtime source attestations differ")
    panel = value["development"]
    if job["mode"] == "final":
        ref = value["registration"]["suites"][value["suite"]]["initial_states_root"] + "/final_registry.json"
        require(evidence.watch(ref) == value["matrix"]["suites"][value["suite"]]["final_registry_sha256"], "Final registry differs from release")
        panel = evidence.read(ref)
        validate_formal_final_registry(panel)
        require(not any("initial_state" in s for s in panel["states"]), "Registry contains state values")
        panel = {**panel, "release_file_sha256": value["opt"]["--release-sha256"]}
    else:
        require(evidence.read(output + "/panel.json") == panel and config.get("panel_signature") == scheduler.signature(panel), "Development panel changed")
    sha(config.get("panel_signature"))
    signature = scheduler.signature(config)
    identities = {r["identity"]["method_id"]: r["identity"] for r in value["manifest"]["methods"]}
    expected = {i["trial_id"]: i for state in panel["states"] for mid in value["methods"] for i in [trials._identity(panel, state, mid)]}
    compact, active, completed, invocations, first_obs = [], {}, {}, [], {}
    path = evidence.path(output + "/trials.jsonl")
    for row in lines(path):
        require(row.get("run_signature") == signature, "Mixed rollout run signatures")
        event = row.get("event")
        if event == "invocation":
            jid = str(row.get("slurm_job_id"))
            require(jid.isdigit() and jid not in invocations, "Invalid or duplicate ledger invocation")
            invocations.append(jid)
        else:
            tid = row.get("trial_id")
            require(invocations and tid in expected and all(row.get(k) == v for k, v in expected[tid].items()), "Unregistered raw trial identity")
            if event == "start":
                require(tid not in completed, "Terminal trial was repeated")
                require(active.get(tid) != invocations[-1], "Duplicate start inside one invocation")
                active[tid] = invocations[-1]
            elif event == "result":
                require(tid in active, "Result without a start")
                active.pop(tid)
                trajectory(row, identities[row["method"]])
                number(row.get("attempt_wall_seconds"), "attempt wall")
                if row["chunks"]:
                    observed = row["chunks"][0]["observation_sha256"]
                    state_id = row["state_trial_id"]
                    require(first_obs.setdefault(state_id, observed) == observed, "Paired initial observation differs across methods/attempts")
                if row["status"] in ("completed", "policy_error"):
                    completed[tid] = {k: v for k, v in row.items() if k not in ("chunks", "executed_actions")}
            else:
                require(event == "cleanup_error" and tid in active, "Unknown or orphan raw rollout event")
        compact.append({k: v for k, v in row.items() if k not in ("chunks", "executed_actions")})
    require(invocations and invocations[-1] == job["job_id"], "Latest raw invocation differs from registered job")
    report = evidence.read(output + "/closed_loop_report.json")
    provenance = report.get("provenance", {})
    require(provenance.get("run_signature") == signature and provenance.get("checkpoint") == value["checkpoint"], "Report base/checkpoint/run mismatch")
    require(all(provenance.get(k) == v for k, v in config.items() if k != "runtime")
            and provenance.get("runtime") == {**config.get("runtime", {}), "slurm_job_id": job["job_id"]}, "Report execution/runtime provenance differs")
    require(bool(config.get("runtime")) and report.get("checkpoint_unchanged") in (None, True), "Missing runtime/final immutable check")
    ledger = SimpleNamespace(path=path, events=compact, completed=lambda: completed)
    rebuilt = trials.summarize_formal_trials(panel, value["methods"], ledger, provenance=provenance, checkpoint_unchanged=report.get("checkpoint_unchanged"))
    require(report == rebuilt, "Saved rollout report is stale or differs from raw trials")
    preflights = [e for e in lines(evidence.path(output + "/adapter_invocations/" + adapter["attempt_id"] + ".jsonl")) if e["event"] == "resume_preflight_passed"]
    require(len(preflights) == 1 and preflights[0].get("panel_signature") == config["panel_signature"], "Adapter panel preflight differs")
    prefix = adapter.get("before_ledger_raw")
    require(isinstance(prefix, dict) and prefix == {k: preflights[0]["evidence"].get(k) for k in ("bytes", "sha256")}
            and adapter.get("before_ledger") == preflights[0]["evidence"]
            and adapter.get("old_ledger_prefix_unchanged") is True, "Missing original ledger prefix proof")
    size = prefix.get("bytes")
    require(type(size) is int and 0 <= size <= path.stat().st_size, "Invalid ledger prefix length")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        remaining = size
        while remaining:
            block = stream.read(min(remaining, 8 << 20)); require(bool(block), "Truncated original ledger prefix")
            digest.update(block); remaining -= len(block)
    require(digest.hexdigest() == prefix.get("sha256"), "Old raw ledger bytes changed")
    require(value["invocation"]["resume"] == (size > 0), "Resume prefix differs from invocation")
    if value["invocation"]["resume"]:
        previous = evidence.read(value["invocation"]["prior_review"])
        require(previous.get("run_signature") == signature and previous.get("files", {}).get(output + "/trials.jsonl") == prefix["sha256"]
                and previous["files"].get(output + "/config.json") == evidence.watch(output + "/config.json"), "Resume does not preserve previously reviewed config/ledger")
        if job["mode"] == "development":
            require(previous["files"].get(output + "/panel.json") == evidence.watch(output + "/panel.json"), "Previously reviewed development panel changed")
        previous_pull = evidence.read(previous["pull_receipt"])
        old_rows = [r for r in previous_pull.get("files", []) if r.get("relative") == output + "/trials.jsonl"]
        require(len(old_rows) == 1 and old_rows[0].get("bytes") == size, "Resume prefix length differs from terminal pull")
    if adapter["status"] == "returned":
        after = adapter.get("after_ledger", {})
        unknown = rebuilt["cost"]["unfinished_attempts_unknown_cost"]
        require(after.get("sha256") == evidence.watch(output + "/trials.jsonl") and after.get("bytes") == path.stat().st_size
                and after.get("terminal_trial_ids") == sorted(completed) and after.get("invocation_job_ids") == sorted(invocations)
                and after.get("active_trial_ids") == sorted(active) and after.get("unfinished_attempts_unknown_cost") == unknown
                and after.get("events") == len(compact) and adapter.get("runner_status") == rebuilt["status"]
                and report["checkpoint_unchanged"] is True, "Adapter returned ledger summary differs")
    return dict(scientific_complete=rebuilt["status"] == "completed", run_signature=signature, completed_trials=len(completed),
        expected_trials=rebuilt["expected_trials"], unfinished_attempts_unknown_cost=rebuilt["cost"]["unfinished_attempts_unknown_cost"],
        raw_invocation_job_ids=invocations, reconstructed_summary=rebuilt)


def collect(evidence, scheduler, value, job, config, adapter):
    from cti_vla.evaluation import formal_profiling as fp
    from cti_vla.evaluation.profiling import RawObservation, observation_signature
    from cti_vla.evaluation.libero_runtime import _observation_hash
    import numpy as np
    output = value["output"]
    states = fp.fixed_profile_states(value["development"])
    signature = scheduler.signature(config)
    events = list(lines(evidence.path(output + "/collection_trials.jsonl")))
    expected_ids = [s["trial_id"] for s in states]
    results, active = [], None
    for row in events:
        require(row.get("run_signature") == signature and row.get("method") == "dense", "Collection run identity differs")
        if row.get("event") == "start":
            require(active is None and len(results) < 10 and row.get("trial_id") == expected_ids[len(results)], "Collection fixed task/state order changed")
            require(not results or results[-1]["status"] == "completed", "Collection continued after failure")
            active = row["trial_id"]
        elif row.get("event") == "result":
            require(active is not None and row.get("trial_id") == active, "Collection result lacks fixed start")
            trajectory(row, value["manifest"]["methods"][0]["identity"], selection=False)
            active = None
            results.append(row)
        else:
            raise ValueError("Collection has an unknown event")
    summary = evidence.read(output + "/summary.json")
    # Validate every known completed trajectory even in a partial failed
    # collection. A missing receipt is not guessed to have been saved later.
    expected_provenance = {**config, "source_verification": adapter["verified_official_sources"], "checkpoint_unchanged": True}
    for row, state in zip(results, states):
        if row["status"] != "completed":
            continue
        ref = output + f"/task{state['task_id']:02d}/receipt.json"
        receipt = evidence.read(ref)
        fp._verify_signature(receipt)
        require(receipt.get("version") == fp.PANEL_VERSION and receipt.get("split") == "development"
                and receipt.get("test_opened") is False and receipt.get("new_success_trials") is False
                and receipt.get("state") == {k: state[k] for k in fp.STATE_FIELDS}
                and receipt.get("provenance") == expected_provenance
                and receipt.get("trajectory") == {k: v for k, v in row.items() if k not in ("event", "trial_id", "method", "run_signature")},
                "Collected trajectory differs from raw result or fixed state/provenance")
        count = row["control_steps"]
        hashes = receipt.get("all_control_observation_sha256", [])
        observations = receipt.get("observations", [])
        require(len(hashes) == count and [o.get("control_step") for o in observations] == fp.selected_control_steps(count)
                and [o.get("phase") for o in observations] == ["first", "middle", "last"]
                and all(c["observation_sha256"] == hashes[c["control_step"]] for c in row["chunks"]), "Partial collection temporal alignment differs")
        for item in observations:
            archive = fp._local_ref(evidence.path(ref).parent, item["arrays"])
            require(archive.suffix == ".npz", "Collection raw input must be NPZ")
            evidence.watch(archive)
            with np.load(archive, allow_pickle=False) as data:
                arrays = {k: data[k].copy() for k in data.files}
            sample = RawObservation(item["observation_id"], state["trial_id"], state["task_name"], receipt["instruction"], item["phase"], arrays)
            step = item["control_step"]
            require(sample.observation_id == f"task{state['task_id']:02d}:state{state['source_state_index']:04d}:step{step:04d}"
                    and observation_signature(sample) == item["raw_sha256"]
                    and _observation_hash(arrays) == item["rollout_observation_sha256"] == hashes[step], "Partial collection raw observation differs")
    if summary.get("status") != "completed_collection":
        require(summary.get("status") == "failed" and summary.get("command") == "collect" and summary.get("test_opened") is False
                and summary.get("cost") is None and adapter["status"] == "failed", "Incomplete collection lacks a consistent failed summary")
        require(not evidence.path(output + "/panel.json").exists(), "Failed collection with panel requires manual forensic review")
        return dict(scientific_complete=False, completed_collection_trajectories=sum(r["status"] == "completed" for r in results),
            unfinished_attempts_unknown_cost=int(active is not None), known_policy_calls=sum(r["policy_calls"] for r in results),
            raw_invocation_job_ids=[job["job_id"]], limitation="No complete30-observation panel; no success or latency result")
    samples, panel = fp.load_profile_panel(evidence.path(output + "/panel.json"), development=value["development"],
        registration=value["registration"], dense_identity=value["manifest"]["methods"][0]["identity"])
    require(len(results) == 10 and active is None and all(r["status"] == "completed" for r in results), "Collection panel without10 complete raw trajectories")
    require(panel["provenance"] == {**config, "source_verification": adapter["verified_official_sources"], "checkpoint_unchanged": True}, "Collection provenance differs")
    payload = evidence.read(output + "/panel.json")
    for row, episode in zip(results, payload["episodes"]):
        receipt = evidence.read(output + "/" + episode["receipt"]["path"])
        require(receipt["trajectory"] == {k: v for k, v in row.items() if k not in ("event", "trial_id", "method", "run_signature")}, "Collected trajectory differs from raw result")
    for name, checksum in panel["artifact_sha256"].items():
        require(evidence.watch(output + "/" + name) == checksum, "Collected raw artifact changed")
    require(summary.get("panel") == panel and summary.get("observations") == len(samples) == 30
            and summary.get("policy_calls") == sum(r["policy_calls"] for r in results)
            and summary.get("new_success_trials") is False and summary.get("test_opened") is False
            and adapter.get("runner_status") == "completed_collection" and adapter["status"] == "returned", "Collection summary differs from raw evidence")
    return dict(scientific_complete=True, completed_collection_trajectories=10, observations=30,
        known_policy_calls=summary["policy_calls"], unfinished_attempts_unknown_cost=0, raw_invocation_job_ids=[job["job_id"]], panel=panel)


def profile(evidence, scheduler, value, job, config, adapter):
    from cti_vla.evaluation import formal_profiling as fp
    output = value["output"]
    summary = evidence.read(output + "/summary.json")
    require(summary.get("status") != "failed", "Incomplete timing requires a separate forensic review; no passed timing receipt")
    samples, panel = fp.load_profile_panel(evidence.path(value["args"].profile_panel), development=value["development"],
        registration=value["registration"], dense_identity=value["manifest"]["methods"][0]["identity"])
    require(config.get("panel") == panel and config.get("panel_sha256") == panel["panel_sha256"]
            and panel["provenance"].get("runtime") == config.get("runtime"), "Timing panel/runtime differs from collection")
    result = evidence.read(output + "/measurements.json")
    require(result.get("provenance") == config and result.get("pass_name") == job["mode"]
            and result.get("observation_ids") == [s.observation_id for s in samples]
            and result.get("observation_episodes") == {s.observation_id: s.episode_id for s in samples}, "Timing raw input or mode mismatch")
    for row in value["manifest"]["methods"]:
        identity = row["identity"]
        expected = dict(identity=identity, cache_scope="none", instruction_cache_enabled=False, future_head_deployed=False,
                        precision="base_bfloat16_DIE_float32", attention="sdpa", batch_size=1)
        require(result.get("methods", {}).get(identity["method_id"]) == expected, "Timing deployment identity/cache/precision differs")
    by_id = {s.observation_id: s for s in samples}
    journal = output + "/calls.jsonl"
    for index, event in enumerate(lines(evidence.path(journal))):
        if index == 0:
            require(event == {"event": "identity", "identity": config, "identity_sha256": scheduler.signature(config)}, "Timing journal identity differs")
            continue
        require(event.get("event") in ("start", "complete") and event.get("observation_id") in by_id, "Failed/unknown timing event")
        sample = by_id[event["observation_id"]]
        require(event.get("episode_id") == sample.episode_id and event.get("task_name") == sample.task_name and event.get("phase") == sample.phase
                and event.get("instruction_mode") == "uncached", "Timing event input/phase/instruction differs")
        if event["event"] == "complete":
            sha(event.get("action_sha256")); number(event.get("elapsed_ms"), "timed call", positive=True)
            require(job["mode"] != "full" or "components" not in event, "Full timing includes instrumentation")
    rebuilt = fp.analyze_formal_profile(evidence.path(output), value["registration"])
    require(summary.get("cost") == rebuilt["cost"] and summary.get("checkpoint_unchanged") is True
            and summary.get("panel") == panel and summary.get("execution_wall_seconds_including_model_loading") == rebuilt["execution_wall_seconds_including_model_loading"],
            "Saved timing cost/panel/finalization differs from raw measurement")
    require(rebuilt["cost"]["sample_policy_forwards_attempted"] == 14300 and adapter["status"] == "returned"
            and adapter.get("runner_status") == summary.get("status"), "Timing completion/call count differs")
    return dict(scientific_complete=True, raw_invocation_job_ids=[job["job_id"]], reconstructed_summary=rebuilt,
        observations=30, methods=22, attempted_policy_forwards=14300, unfinished_attempts_unknown_cost=0)


def profile_config(evidence, scheduler, value, job, config):
    from cti_vla.evaluation.formal_profiling import PROFILE_VERSION, PANEL_VERSION
    attempt = evidence.read(value["output"] + "/attempt.json")
    expected = dict(version=PROFILE_VERSION, command=job["mode"], suite=value["suite"],
        registration_sha256=scheduler.signature(value["registration"]), execution_manifest_sha256=job["execution_manifest_sha256"],
        slurm_job_id=job["job_id"], test_opened=False)
    require(attempt == expected, "Profiling attempt identity differs")
    expected["version"] = PANEL_VERSION if job["mode"] == "collect" else PROFILE_VERSION
    require(all(config.get(k) == v for k, v in expected.items()) and config.get("checkpoint") == value["checkpoint"]
            and config.get("dense_identity") == value["manifest"]["methods"][0]["identity"]
            and config.get("all_instances_share_one_loaded_base") is True and config.get("cache_scope") == "none"
            and config.get("future_head_deployed") is False and config.get("compile") == "disabled; native eager SDPA"
            and config.get("profiling_registration") == value["registration"]["profiling"], "Profiling execution contract differs")
    for field, path in (("profiler_script_sha256", "scripts/profile_formal.py"), ("profiler_module_sha256", "src/cti_vla/evaluation/formal_profiling.py")):
        require(config.get(field) == value["inventory"]["files"][path], "Profiling source identity differs")
    require(config.get("allocation", {}).get("other_compute_processes") == 0 and config["allocation"].get("gpu_uuid")
            and config.get("runtime", {}).get("gpu") == "NVIDIA L40", "Profiling allocation is not uncontended L40")
    number(config.get("model_loading_seconds_excluded_from_calls"), "base loading")
    if job["mode"] in ("full", "components"):
        require(config.get("global_freeze_sha256") == evidence.watch(value["args"].freeze_directory + "/global_freeze.json"), "Timing global freeze differs")


def allocation_cost(evidence, scheduler, jobs, job, invocation, observed):
    by_id = {j["job_id"]: j for j in jobs}
    ids = invocation.get("prior_job_ids", []) + [job["job_id"]]
    require(len(set(ids)) == len(ids) and set(observed) == (set(ids) if job["mode"] in ("development", "final") else {job["job_id"]}), "Raw job coverage differs from all registered attempts")
    rows = []
    earlier = [j for j in jobs if j.get("stage_key") == job["stage_key"] and
        (j.get("submitted_utc", ""), int(j["job_id"])) <= (job.get("submitted_utc", ""), int(job["job_id"]))]
    earlier.sort(key=lambda j: (j.get("submitted_utc", ""), int(j["job_id"])))
    require([j["job_id"] for j in earlier] == ids, "Prior attempt list omits or reorders registered allocation")
    for jid in ids:
        item = by_id.get(jid, {})
        require(item.get("mode") == job["mode"] and item.get("stage_key") == job["stage_key"] and item.get("method_ids") == job["method_ids"]
                and item.get("source_sha256") == scheduler.FROZEN_SHA256 and item.get("adapter_sha256") == scheduler.ADAPTER_SHA256
                and item.get("execution_manifest_sha256") == job["execution_manifest_sha256"] and item.get("status") in scheduler.TERMINAL
                and type(item.get("elapsed_seconds")) is int and item["elapsed_seconds"] >= 0 and item.get("gpus") == 1,
                "Every attempted allocation needs its registered terminal identity/cost")
        if job["mode"] in ("development", "final"):
            require(item["run_root"] == job["run_root"], "Rollout attempts changed output")
        rows.append({k: item.get(k) for k in ("job_id", "status", "raw_status", "exit_code", "elapsed_seconds", "gpus")})
        require(evidence.watch(item["invocation"]) == item["invocation_sha256"], "Prior invocation changed")
    require(invocation.get("prior_allocation_cost", []) == rows[:-1], "Original prior allocation accounting changed")
    current_output = remote_relative(job["run_root"], scheduler)
    mutable = {current_output + "/trials.jsonl", current_output + "/closed_loop_report.json"} if job["mode"] in ("development", "final") else set()
    for index, jid in enumerate(ids[:-1]):
        # Walk every adjacent continuation, not just the most recent review:
        # older Slurm logs/job receipts live outside the shared run directory.
        next_invocation = evidence.read(by_id[ids[index + 1]]["invocation"])
        historical_path = next_invocation.get("prior_review")
        historical = evidence.read(historical_path)
        require(historical.get("job_id") == jid and historical.get("kind") == "root_downstream_review"
                and historical.get("status") == "passed" and historical.get("scientific_complete") is False
                and historical.get("run_root") == by_id[jid]["run_root"]
                and evidence.watch(historical_path) == next_invocation["root_evidence_sha256"].get(historical_path), "Historical review chain changed")
        pull_path = historical["pull_receipt"]
        historical_pull = evidence.read(pull_path)
        require(historical_pull.get("final_evidence") is True and historical_pull.get("status") == "verified_nonweight_snapshot"
                and evidence.watch(pull_path) == next_invocation["root_evidence_sha256"].get(pull_path), "Missing or changed historical terminal pull")
        previous = {r["relative"]: r["sha256"] for r in historical_pull["files"]}
        require(all(previous.get(k) == v for k, v in historical["files"].items()), "Historical root review/pull disagree")
        for path, checksum in historical["files"].items():
            scheduler.relative(path)
            require(not (job["mode"] == "final" and path == current_output + "/panel.json"), "Historical final value panel must not be read")
            if path not in mutable:
                require(evidence.watch(path) == checksum, "Historical immutable evidence changed after resume: " + path)
    # Historical root review/pull bytes stay immutable even though a resumed
    # run's current ledger/report has grown. Bind their historical file map, not
    # today's bytes to yesterday's digest.
    if ids[:-1]:
        prior_path = invocation.get("prior_review")
        prior = evidence.read(prior_path)
        require(prior.get("job_id") == ids[-2] and prior.get("status") == "passed" and prior.get("kind") == "root_downstream_review"
                and prior.get("scientific_complete") is False and prior.get("run_root") == by_id[ids[-2]]["run_root"]
                and evidence.watch(prior_path) == invocation["root_evidence_sha256"].get(prior_path), "Prior review not bound to invocation")
        failures = {r["job_id"] for r in rows[:-1] if r["status"] != "COMPLETED" or r["exit_code"] != "0:0"}
        if failures:
            repair_path = invocation.get("repair_record")
            repair = evidence.read(repair_path)
            require(repair.get("schema") == scheduler.ROUND and repair.get("kind") == "downstream_repair"
                    and repair.get("status") == "reviewed" and repair.get("reviewed_by") == "root"
                    and set(repair.get("failed_job_ids", [])) == failures and repair.get("stage_key") == job["stage_key"]
                    and repair.get("target_source_sha256") == scheduler.FROZEN_SHA256 and repair.get("adapter_sha256") == scheduler.ADAPTER_SHA256
                    and repair.get("prior_review_sha256") == evidence.watch(prior_path)
                    and repair.get("execution_manifest_sha256") == job["execution_manifest_sha256"]
                    and repair.get("diagnosis") and repair.get("bounded_fix")
                    and evidence.watch(repair_path) == invocation["root_evidence_sha256"].get(repair_path), "Failed attempts lack bound repair evidence")
    return dict(allocations=rows, current_gpu_seconds=job["elapsed_seconds"], all_attempt_gpu_seconds=sum(r["elapsed_seconds"] for r in rows),
                scope="Every registered allocation counted once, including model loading, warmup, failures and idle/setup time; not only timed calls")


def review(job_id, pull_receipt, *, project=ROOT, state=None, scheduler=None, helper=None):
    scheduler = scheduler or load("scripts/ops/formal_downstream_supervisor.py")
    helper = helper or load("scripts/formal_execution_manifests.py")
    # These root-only analysis dependencies are outside the frozen GPU map.
    # Bind the actual imported files too, so an audit remains attributable.
    audit_paths = [Path(__file__).resolve(), Path(helper.__file__).resolve(), Path(scheduler.__file__).resolve(),
        ROOT / "scripts/analyze_formal.py", ROOT / scheduler.ADAPTER, ROOT / scheduler.WRAPPER,
        ROOT / scheduler.ASSET_REVIEW]
    audit_sources = {p.relative_to(ROOT).as_posix(): scheduler.digest(p) for p in audit_paths}
    evidence = helper.Evidence(Path(project).resolve())
    # The caller holds the supervisor lock. Only immutable terminal job
    # projections are retained; unrelated jobs changing state must not invalidate
    # an old root audit or become part of its stable evidence file map.
    state = state if state is not None else json.loads(evidence.path(scheduler.STATE).read_text(encoding="utf-8"))
    jobs = scheduler.formal_jobs(state)
    matches = [j for j in jobs if j["job_id"] == str(job_id)]
    require(len(matches) == 1 and matches[0].get("mode") in scheduler.STAGES, "Not a uniquely registered downstream job")
    job = matches[0]
    require(job["status"] in scheduler.TERMINAL, "Only terminal jobs can be reviewed")
    output = remote_relative(job["run_root"], scheduler)
    require(not any(j["job_id"] != job["job_id"] and j.get("status") not in scheduler.TERMINAL
                    and (j.get("run_root") == job["run_root"] or PurePosixPath(j.get("run_root", "/invalid")) in PurePosixPath(job["run_root"]).parents)
                    for j in jobs), "An active registered job can still change these outputs")
    candidate = pulled_candidate(evidence, scheduler, job, pull_receipt, jobs)
    invocation = evidence.read(job["invocation"])
    value = validate_invocation(evidence, scheduler, helper, state, job, invocation)
    config = evidence.read(output + "/config.json")
    value["checkpoint"] = runtime_inputs(evidence, scheduler, value, config)
    adapter = adapters(evidence, scheduler, value, job, config, candidate["files"])
    candidate["source_provenance"] = value["source_provenance"]
    candidate["registered_jobs_at_review"] = [dict(j) for j in state.get("registered_jobs", [])
        if j.get("experiment") == scheduler.ROUND
        and str(j.get("status", "")).split() and str(j["status"]).split()[0].rstrip("+") in scheduler.TERMINAL]
    if job["suite"] in scheduler.ASSET_SUITES:
        candidate["asset_runtime_review"] = scheduler.provenance_helper(evidence).review_invocation(evidence,
            job=job, invocation=invocation,
            wrapper_receipt=evidence.read(f"results/{scheduler.ROUND}/job_receipts/{job['job_id']}.json"),
            inventory=value["inventory"], pull_receipt=pull_receipt,
            source_provenance=value["source_provenance"], legacy_adapter_review=adapter)
    if job["mode"] in ("development", "final"):
        result = rollout(evidence, scheduler, value, job, config, adapter)
    else:
        profile_config(evidence, scheduler, value, job, config)
        result = collect(evidence, scheduler, value, job, config, adapter) if job["mode"] == "collect" else profile(evidence, scheduler, value, job, config, adapter)
        duration = evidence.read(output + "/summary.json").get("execution_wall_seconds_including_model_loading")
        number(duration, "profile/collection execution wall")
        require(duration <= job["elapsed_seconds"] + 1, "Profile execution wall exceeds allocation")
    costs = allocation_cost(evidence, scheduler, jobs, job, invocation, result["raw_invocation_job_ids"])
    # A failed allocation can retain apparently complete scientific rows; it
    # cannot establish successful scientific finalization.
    result["scientific_complete"] = result["scientific_complete"] and job["status"] == "COMPLETED" and job["exit_code"] == "0:0" and adapter["status"] == "returned"
    candidate.update(result, cost=costs, version=VERSION, reviewed_utc=datetime.now(timezone.utc).isoformat(),
        reviewer_source_sha256=scheduler.digest(__file__), audit_source_sha256=audit_sources, final_state_values_read=False, weights_read=False,
        code_identity_scope="Exact173 source hashes and explicit function/path attestations; Python marshal code hashes cross-checked within server journal, not regenerated on a different Python host")
    scheduler.require_root_review(CandidateEvidence(evidence, candidate), "in_memory_candidate", jobs, expected_stage=job["mode"])
    # Every run artifact consumed by a scientific validator must be part of the
    # stable current pull. Input panel artifacts outside this run stay separately
    # bound by the original invocation and collection review.
    for name, checksum in evidence.files.items():
        if name.startswith(output + "/"):
            require(candidate["files"].get(name) == checksum, "Scientific artifact absent from complete SHA pull")
    evidence.unchanged()
    require(audit_sources == {p.relative_to(ROOT).as_posix(): scheduler.digest(p) for p in audit_paths}, "Root audit implementation changed during review")
    candidate["evidence_sha256"] = dict(sorted(evidence.files.items()))
    return candidate


def publish_review(path, report, *, root_review=False):
    require(root_review, "Writing a root audit requires explicit --root-review")
    path = Path(path)
    require(not path.exists(), "Root review output must be a new immutable file")
    load("scripts/formal_execution_manifests.py").immutable_write(path, report)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--pull-receipt", required=True)
    parser.add_argument("--output")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--root-review", action="store_true")
    args = parser.parse_args(argv)
    require(args.write == bool(args.output) and (not args.write or args.root_review), "Use --write --root-review --output together")
    scheduler = load("scripts/ops/formal_downstream_supervisor.py")
    if args.output:
        scheduler.result_relative(args.output)
        require(args.output.startswith(f"results/{scheduler.ROUND}/downstream_reviews/"), "Review must use its separate immutable directory")
        require(not scheduler.local(ROOT, args.output).exists(), "Do not overwrite any prior root review")
    supervisor = load("scripts/formal_supervisor.py")
    # No refresh: root must already have reconciled terminal accounting. The
    # existing project lock prevents a simultaneous local submission/state edit.
    with supervisor.supervisor_lock():
        result = review(args.job_id, args.pull_receipt)
        if args.write:
            publish_review(scheduler.local(ROOT, args.output), result, root_review=args.root_review)
    print(json.dumps({k: result[k] for k in ("status", "job_id", "stage", "scientific_complete", "cost")}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()

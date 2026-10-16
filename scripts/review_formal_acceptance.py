"""Root-only local review of SHA-pulled formal F00/F01/F03 evidence.

No model/checkpoint or sealed state is opened. No jobs are submitted/cancelled.
Optional accounting refresh delegates to the existing registered-job supervisor.
A passed root_review is published only after every identity and raw-log gate.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
P = PurePosixPath("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
ROUND = "formal_main_v2"
STATE = "results/experiment_supervisor/state.json"
REGISTRATION = f"configs/experiments/{ROUND}.json"
BUDGETS = (128, 256, 64)
NAMES = ("input_acceptance.json", "input_calls.jsonl", "operator_calls.jsonl",
         "f01_k128.json", "f01_k256.json", "f01_k64.json", "resume_acceptance.json",
         "f03_calls.jsonl", "acceptance_complete.json")
FORBIDDEN = {".pt", ".pth", ".ckpt", ".safetensors", ".bin", ".pickle", ".pkl", ".init", ".pruned_init"}
_compat_spec = importlib.util.spec_from_file_location("formal_asset_compat_review", ROOT / "scripts/ops/formal_asset_compat_review.py")
_compat = importlib.util.module_from_spec(_compat_spec)
_compat_spec.loader.exec_module(_compat)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            result.update(chunk)
    return result.hexdigest()


class Evidence:
    def __init__(self, root):
        self.root, self.hashes = Path(root).resolve(), {}

    def path(self, name):
        path = Path(name)
        if not path.is_absolute():
            path = self.root / path
        if (set(s.lower() for s in path.suffixes) & FORBIDDEN
                or any("sealed" in part.lower() or part.lower() in ("initial_states", "checkpoints", "weights") for part in path.parts)):
            raise ValueError("Review cannot access weights or sealed initial states")
        if path.resolve() != path.absolute() or self.root not in path.resolve().parents:
            raise ValueError("Review evidence must be a direct local project file")
        return path

    def watch(self, name):
        path = self.path(name)
        relative = path.relative_to(self.root).as_posix()
        digest = sha(path)
        if relative in self.hashes and self.hashes[relative] != digest:
            raise ValueError("Evidence changed during review: " + relative)
        self.hashes[relative] = digest
        return digest

    def read(self, name):
        self.watch(name)
        return json.loads(self.path(name).read_text(encoding="utf-8"))

    def unchanged(self):
        for relative, digest in self.hashes.items():
            if sha(self.path(relative)) != digest:
                raise ValueError("Evidence changed before review publication: " + relative)


def expect(actual, expected, label):
    if any(actual.get(key) != value for key, value in expected.items()):
        raise ValueError(label + " identity/completion mismatch")


def registered_source(evidence, inventory_path, job):
    from cti_vla.training.formal_future import formal_source_hashes
    inventory = evidence.read(inventory_path)
    files = inventory.get("files", {})
    signature = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    expect(inventory, dict(schema=ROUND, source_sha256=signature, source_root_server=job["source_root"]), "Source inventory")
    if signature != job["source_sha256"] or not job["source_root"].startswith(str(P / "snapshots/formal_main_v2_run_")):
        raise ValueError("Job does not use the registered GPU source inventory")
    current = formal_source_hashes(evidence.root)
    if not current or any(files.get(name) != digest for name, digest in current.items()):
        raise ValueError("Current formal_source_hashes differ from the frozen job source")
    for name, digest in current.items():
        if evidence.watch(name) != digest:
            raise ValueError("Current source changed while hashing")
    return inventory, current


def require_pulled(evidence, receipt_path, job, required):
    receipt_path = evidence.path(receipt_path)
    pull_root = evidence.root / f"results/{ROUND}/pulls"
    if pull_root not in receipt_path.parents:
        raise ValueError("Pull receipt must belong to this formal round")
    receipt = evidence.read(receipt_path)
    expect(receipt, dict(schema=ROUND, kind="nonweight_pull", status="verified_nonweight_snapshot",
        final_evidence=True, weights_copied=False, sealed_initial_states_copied=False), "SHA pull receipt")
    selected = [r for r in receipt.get("selected_jobs", []) if r.get("job_id") == job["job_id"]]
    if (len(selected) != 1 or selected[0].get("run_root") != job["run_root"]
            or selected[0].get("source_sha256") != job["source_sha256"] or selected[0].get("include_run_root") is not True):
        raise ValueError("Pull did not finalize this exact registered run_root")
    for key in ("accounting_before", "accounting_after"):
        expect(receipt.get(key, {}).get("jobs", {}).get(job["job_id"], {}),
               dict(status="COMPLETED", exit_code="0:0"), "Pulled job accounting")
    before_path, after_path = receipt_path.parent / "inventory_before.json", receipt_path.parent / "inventory_after.json"
    before, after = evidence.read(before_path), evidence.read(after_path)
    if before != after or evidence.watch(before_path) != receipt.get("inventory_sha256"):
        raise ValueError("Pull has no stable double remote SHA inventory")
    rows = {r["relative"]: r for r in receipt.get("files", [])}
    remote = {r["relative"]: r for r in before.get("files", [])}
    if len(rows) != len(receipt.get("files", [])) or len(remote) != len(before.get("files", [])):
        raise ValueError("Duplicate pull inventory entries")
    for relative in required:
        row, original = rows.get(relative, {}), remote.get(relative, {})
        digest = evidence.watch(relative)
        if (row.get("sha256") != digest or original.get("sha256") != digest
                or row.get("path") != str(P / relative) or original.get("path") != str(P / relative)
                or job["job_id"] not in row.get("job_ids", []) or job["job_id"] not in original.get("job_ids", [])
                or row.get("bytes") != evidence.path(relative).stat().st_size
                or original.get("bytes") != row.get("bytes")
                or row.get("action") not in ("same_sha_skipped", "downloaded_verified")):
            raise ValueError("Required evidence is not a verified SHA-pulled file: " + relative)


def review_runtime_compatibility(evidence, *, job, invocation, receipt, inventory, pull_receipt):
    """Additional operational audit; never replaces the original scientific gates."""
    result = _compat.review_job(evidence, job=job, invocation=invocation, receipt=receipt, inventory=inventory)
    if result is None:
        return None
    required = [*result["required_pulled_files"], f"results/{ROUND}/job_receipts/{job['job_id']}.json"]
    require_pulled(evidence, pull_receipt, job, required)
    relative = evidence.path(pull_receipt).relative_to(evidence.root).as_posix()
    return dict(result, pull_receipt=dict(path=relative, sha256=evidence.watch(relative)))


def require_saved_runtime_review(evidence, *, saved, job, inventory):
    """Reconstruct a reused root attestation from its raw, SHA-pulled artifacts."""
    invocation = evidence.read(job["invocation"])
    receipt = evidence.read(f"results/{ROUND}/job_receipts/{job['job_id']}.json")
    runtime = _compat.contract(evidence, job=job, invocation=invocation)
    if runtime is None:
        if any(key in saved for key in ("runtime_compatibility", "runtime_compatibility_review")):
            raise ValueError("Legacy root review unexpectedly contains runtime compatibility")
        return None
    previous = saved.get("runtime_compatibility_review", {})
    pull = previous.get("pull_receipt", {})
    if (saved.get("runtime_compatibility") != runtime or not pull.get("path")
            or evidence.watch(pull["path"]) != pull.get("sha256")):
        raise ValueError("Reused compatibility root review lacks its immutable pull/provenance")
    actual = review_runtime_compatibility(evidence, job=job, invocation=invocation, receipt=receipt,
        inventory=inventory, pull_receipt=pull["path"])
    if actual != previous:
        raise ValueError("Reused compatibility review does not rebuild from its raw artifacts")
    return actual


def publish_review(path, report):
    """No failed/partial review, and never replace a previous accepted identity."""
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        stable = ("schema", "kind", "status", "suite", "job_id", "output_relative", "files", "source_sha256", "invocation_sha256",
                  "runtime_compatibility", "runtime_compatibility_review")
        if any(previous.get(k) != report.get(k) for k in stable):
            raise ValueError("An existing root review has a different accepted identity")
        return previous
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".partial")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.link(temporary, path)  # exclusive publication; cannot replace another root writer
    except BaseException:
        raise
    else:
        temporary.unlink()
    return report


def review(job_id, *, source_inventory, pull_receipt, root=ROOT):
    from cti_vla.data.formal_windows import load_formal_protocol, load_formal_windows
    from cti_vla.evaluation.formal_acceptance import (select_formal_acceptance_windows,
        require_formal_input_acceptance, require_formal_acceptance, verify_formal_operator_journal)
    from cti_vla.evaluation.future_input_acceptance import verify_input_acceptance_journal
    from cti_vla.evaluation.libero_runtime import OFT_COMMIT
    from cti_vla.training.formal_future import validate_formal_training_config
    from cti_vla.training.formal_resume_acceptance import require_formal_resume_acceptance, verify_resume_journal

    evidence = Evidence(root)
    if not re.fullmatch(r"[0-9]+", str(job_id)):
        raise ValueError("Invalid registered job ID")
    state = evidence.read(STATE)
    jobs = [r for r in state["registered_jobs"] if str(r.get("job_id")) == str(job_id)]
    if len(jobs) != 1:
        raise ValueError("Acceptance job must have exactly one supervisor registration")
    job = jobs[0]
    suite = job.get("suite")
    expect(job, dict(job_id=str(job_id), experiment=ROUND, mode="acceptance", status="COMPLETED", exit_code="0:0",
                     stage_key=f"{suite}_acceptance", name="cti-formal"), "Supervisor job")
    output = PurePosixPath(job["run_root"])
    expected_parent = P / f"results/{ROUND}/{suite}/acceptance"
    if output.parent != expected_parent or not re.fullmatch(r"attempt[0-9]{2,}", output.name):
        raise ValueError("Acceptance output is not this suite's registered attempt")
    relative = output.relative_to(P).as_posix()
    base = evidence.path(relative)
    if (base / "failure.json").exists() or (base / "resume_acceptance_failure.json").exists():
        raise ValueError("A failed acceptance attempt cannot receive a passed review")
    inventory, sources = registered_source(evidence, source_inventory, job)
    registration = evidence.read(REGISTRATION)
    if registration.get("schema") != ROUND or suite not in registration.get("suites", {}):
        raise ValueError("Unknown formal suite registration")
    if evidence.watch(REGISTRATION) != inventory["files"].get(REGISTRATION):
        raise ValueError("Formal registration changed after source freeze")
    spec = registration["suites"][suite]
    pairs, pair_paths = {}, {}
    for budget in BUDGETS:
        matches = [p for p in registration["pairs"] if (p["suite"], p["visual_tokens"], p["seed"]) == (suite, budget, 17)]
        if len(matches) != 1:
            raise ValueError("Exactly one registered seed17 pair per acceptance budget is required")
        row = matches[0]
        expected_path = f"configs/experiments/{ROUND}/{suite}_k{budget}_seed17.json"
        if row["path"] != expected_path or evidence.watch(row["path"]) != row["sha256"] or inventory["files"].get(row["path"]) != row["sha256"]:
            raise ValueError("Acceptance pair configuration bytes differ from registration/source")
        pairs[budget], pair_paths[budget] = evidence.read(row["path"]), row["path"]
        validate_formal_training_config(pairs[budget])
        expect(pairs[budget], dict(suite=suite, seed=17, tokens_per_camera=budget // 2,
            model_revision=spec["model_revision"], data={"protocol": spec["protocol"], "windows": spec["windows"]}), "Acceptance pair")
    primary = pairs[128]
    protocol_path, windows_path = evidence.path(spec["protocol"]), evidence.path(spec["windows"])
    protocol_bytes = evidence.read(protocol_path)
    if (protocol_bytes["dataset_asset"] != spec["data_manifest"]
            or evidence.watch(spec["data_manifest"]) != spec["data_manifest_sha256"]
            or inventory["files"].get(spec["data_manifest"]) != spec["data_manifest_sha256"]):
        raise ValueError("Data asset differs from suite registration/source")
    for dependency in (protocol_bytes["dataset_asset"],):
        evidence.watch(dependency)
    if protocol_bytes.get("inherited_protocol"):
        evidence.watch(protocol_bytes["inherited_protocol"]["path"])
    for name in ("__init__.py", "libero_suite_task_map.py"):
        evidence.watch("external/LIBERO/libero/libero/benchmark/" + name)
    protocol = load_formal_protocol(protocol_path, evidence.root)
    windows = load_formal_windows(windows_path, protocol)
    if protocol.payload["suite"] != suite:
        raise ValueError("Registered protocol belongs to a different suite")
    fixed = select_formal_acceptance_windows(windows, protocol)
    window_sha, protocol_sha = evidence.watch(windows_path), evidence.watch(protocol_path)
    asset = evidence.read(spec["model_manifest"])
    asset_sha = evidence.watch(spec["model_manifest"])
    if asset_sha != spec["model_manifest_sha256"] or inventory["files"].get(spec["model_manifest"]) != asset_sha or asset["revision"] != spec["model_revision"]:
        raise ValueError("Official model asset identity changed")
    invocation = evidence.read(job["invocation"])
    inv_sha = evidence.watch(job["invocation"])
    expect(invocation, dict(schema=ROUND, stage="acceptance", stage_key=job["stage_key"], suite=suite,
        source_root=job["source_root"], source_sha256=job["source_sha256"], entrypoint="scripts/verify_formal_acceptance.py",
        registration_sha256=evidence.watch(REGISTRATION), segment_end=None), "Invocation")
    if inv_sha != job["invocation_sha256"]:
        raise ValueError("Registered invocation SHA changed")
    source = PurePosixPath(job["source_root"])
    expected_argv = ["--suite", suite, "--configs", *[str(source / pair_paths[k]) for k in BUDGETS],
        "--protocol", str(P / spec["protocol"]), "--windows", str(P / spec["windows"]),
        "--checkpoint", spec["model_root_server"], "--asset-manifest", str(source / spec["model_manifest"]),
        "--data-directory", spec["data_root_server"], "--cache-directory", str(P / (".local/formal-hf-" + suite)),
        "--feature-cache", spec["cache_root_server"], "--oft-source", str(P / "external/openvla-oft"),
        "--project-root", str(P), "--output", str(output)]
    watched = {str(P / spec["protocol"]): protocol_sha, str(P / spec["windows"]): window_sha,
        str(source / spec["model_manifest"]): asset_sha,
        **{str(source / path): evidence.watch(path) for path in pair_paths.values()}}
    if invocation.get("argv") != expected_argv or invocation.get("watched_files") != watched:
        raise ValueError("Invocation argv or frozen input SHA scope changed")
    receipt_relative = f"results/{ROUND}/job_receipts/{job_id}.json"
    receipt = evidence.read(receipt_relative)
    expect(receipt, dict(schema=ROUND, job_id=str(job_id), stage="acceptance", stage_key=job["stage_key"],
        invocation_sha256=inv_sha, source_sha256=job["source_sha256"], exit_code=0), "Server job receipt")
    wall = receipt.get("wall_seconds")
    if isinstance(wall, bool) or not isinstance(wall, (float, int)) or not math.isfinite(wall) or wall <= 0:
        raise ValueError("Server job receipt has no finite positive cost")
    runtime_review = review_runtime_compatibility(evidence, job=job, invocation=invocation,
        receipt=receipt, inventory=inventory, pull_receipt=pull_receipt)
    required = [relative + "/" + name for name in NAMES] + [receipt_relative] + [f"results/slurm/cti-formal_{job_id}.{ext}" for ext in ("out", "err")]
    require_pulled(evidence, pull_receipt, job, required)
    reports = {name: evidence.read(base / name) for name in NAMES if name.endswith(".json")}
    f00 = reports["input_acceptance.json"]
    shared = dict(window_manifest_sha256=window_sha, source_files=sources)
    expect(f00, dict(job_id=str(job_id), official_source_revision=OFT_COMMIT), "F00 job/reference")
    expect(f00.get("checkpoint", {}), dict(repository=asset["repository"], revision=asset["revision"],
        file_count=len(asset["files"]), total_bytes=sum(row["size"] for row in asset["files"])), "F00 verified base assets")
    require_formal_input_acceptance(f00, config=primary, **shared, data_protocol_sha256=protocol_sha,
        asset_manifest_sha256=asset_sha, selected_windows=fixed)
    verify_input_acceptance_journal(base / "input_calls.jsonl", f00)
    f00_sha = evidence.watch(base / "input_acceptance.json")
    for i, budget in enumerate(BUDGETS):
        f01 = reports[f"f01_k{budget}.json"]
        expect(f01, dict(job_id=str(job_id), frozen_model_sha256=f00["frozen_model_sha256"],
                         operator_probes_completed=(i + 1) * 21), "F01 job/frozen base/cumulative work")
        require_formal_acceptance(f01, config=pairs[budget], **shared, input_acceptance_sha256=f00_sha, selected_windows=fixed)
        verify_formal_operator_journal(base / "operator_calls.jsonl", f01)
    final_f01 = reports["f01_k64.json"]
    if final_f01["operator_journal_prefix_bytes"] != (base / "operator_calls.jsonl").stat().st_size:
        raise ValueError("Operator journal has unreviewed trailing work")
    resume = reports["resume_acceptance.json"]
    expect(resume, dict(job_id=str(job_id)), "F03 job")
    require_formal_resume_acceptance(resume, config=primary, **shared, input_acceptance_sha256=f00_sha,
        selected_windows=fixed[:2], frozen_model_sha256=f00["frozen_model_sha256"])
    verify_resume_journal(base / "f03_calls.jsonl", resume)
    complete = reports["acceptance_complete.json"]
    expect(complete, dict(schema=ROUND, status="passed", suite=suite, job_id=str(job_id), test_opened=False,
        source_files=sources, frozen_model_sha256=f00["frozen_model_sha256"], checkpoint_unchanged=True,
        input_acceptance_sha256=f00_sha, input_calls=6, operator_probes=63,
        operator_calls_sha256=evidence.watch(base / "operator_calls.jsonl"), resume_acceptance_passed=True,
        resume_acceptance_sha256=evidence.watch(base / "resume_acceptance.json"),
        f03_calls_sha256=evidence.watch(base / "f03_calls.jsonl")), "Acceptance completion")
    expected_operators = [{"visual_tokens": k, "path": str(output / f"f01_k{k}.json"),
        "sha256": evidence.watch(base / f"f01_k{k}.json")} for k in BUDGETS]
    if complete.get("operator_acceptances") != expected_operators:
        raise ValueError("Acceptance completion must bind all three unique ordered budget reports")
    report = dict(schema=ROUND, kind="root_acceptance_review", status="passed", suite=suite, job_id=str(job_id),
        output_relative=relative, files={name: evidence.watch(base / name) for name in NAMES},
        source_sha256=job["source_sha256"], source_files=sources, invocation_sha256=inv_sha,
        reviewed_utc=datetime.now(timezone.utc).isoformat(), job_at_review=job,
        selected_windows=fixed, reviewed_counts=dict(input_forwards=6, operator_probes=63, f03_forward_backward_samples=48),
        weights_opened=False, sealed_initial_states_opened=False, evidence_sha256=dict(evidence.hashes))
    if runtime_review is not None:
        report.update(runtime_compatibility=runtime_review["runtime_compatibility"], runtime_compatibility_review=runtime_review)
        report["files"].update({PurePosixPath(name).relative_to(relative).as_posix(): evidence.watch(name)
            for name in runtime_review["required_pulled_files"]})
        report["evidence_sha256"] = dict(evidence.hashes)
    evidence.unchanged()
    target = evidence.path(f"results/{ROUND}/{suite}/acceptance/root_review.json")
    return publish_review(target, report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--source-inventory", type=Path, required=True)
    parser.add_argument("--pull-receipt", type=Path, required=True)
    parser.add_argument("--refresh", action="store_true", help="Refresh only supervisor-registered jobs before review")
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("cti_formal_review_supervisor", ROOT / "scripts/formal_supervisor.py")
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    with supervisor.supervisor_lock():
        if args.refresh:
            supervisor.refresh(supervisor.read(supervisor.STATE))
        result = review(args.job_id, source_inventory=args.source_inventory, pull_receipt=args.pull_receipt)
    print(json.dumps({"status": result["status"], "job_id": result["job_id"], "suite": result["suite"],
        "output_relative": result["output_relative"], "files": len(result["files"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Review one registered formal training segment without loading torch or weights.

The default is a local, read-only audit and an exact server SHA checklist. Only
--verify-server-resume hashes the registered pair's two resume.pt files over SSH;
only a successful complete audit then publishes an immutable segment review.
No Slurm submission/cancellation, checkpoint deserialization or sealed-state IO.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath
import random
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

# Explicit candidate-only failure consumer; never modifies the original module.
import importlib.util as _startup_importlib
_startup_spec = _startup_importlib.spec_from_file_location("formal_startup_failure_candidate", Path(__file__).with_name("startup_failure_evidence.py"))
_startup = _startup_importlib.module_from_spec(_startup_spec)
_startup_spec.loader.exec_module(_startup)
_spec = importlib.util.spec_from_file_location("formal_segment_evidence", ROOT / "scripts/review_formal_acceptance.py")
_shared = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_shared)
Evidence, expect, sha, require_pulled = _shared.Evidence, _shared.expect, _shared.sha, _shared.require_pulled
P, ROUND, STATE, REGISTRATION = _shared.P, _shared.ROUND, _shared.STATE, _shared.REGISTRATION
H = PurePosixPath("/share/home/u15016/XXY_CVPR/CTI-VLA")
ENTRYPOINTS = ("run_formal_future.py", "verify_formal_acceptance.py", "eval_formal_selector_libero.py", "verify_long_inputs.py")
ACTIVE = {"PENDING", "RUNNING", "CONFIGURING", "COMPLETING", "SUSPENDED", "REQUEUED", "RESIZING", "SUBMITTED"}
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL", "PREEMPTED", "BOOT_FAIL", "DEADLINE", "REVOKED", "SPECIAL_EXIT"}



def require_pulled_startup_ownership(evidence, receipt_path, job, required, jobs, failure_history):
    """Preserve per-job ownership for only the three external files of a verified startup failure."""
    external = {}
    for failed_id, saved in failure_history.items():
        prior = jobs[failed_id]
        expect(prior, dict(job_id=failed_id, status="FAILED", exit_code="1:0", gpus=1), "Retained startup allocation")
        if failed_id == job["job_id"] or saved.get("status") != "verified_startup_failure":
            raise ValueError("Only separately verified historical startup failures are eligible")
        canonical = _startup.require_saved(evidence, job=prior, saved=saved)
        if evidence.watch(prior["invocation"]) != prior["invocation_sha256"]:
            raise ValueError("Historical actual invocation SHA differs")
        exact = [f"results/{ROUND}/job_receipts/{failed_id}.json",
                 *[f"results/slurm/cti-formal_{failed_id}.{ext}" for ext in ("out", "err")]]
        if not set(exact) <= set(canonical["retained_failure_files"]) or not set(exact) <= set(required):
            raise ValueError("Historical external file set is incomplete")
        for rel in exact:
            if rel in external:
                raise ValueError("Conflicting historical file ownership")
            external[rel] = (prior, canonical["evidence_bundle"][rel])
    # Every current file and every shared run-root failure/compatibility artifact still
    # passes the unchanged original completed-job verifier.
    require_pulled(evidence, receipt_path, job, sorted(set(required) - set(external)))
    receipt = evidence.read(receipt_path)
    if receipt.get("missing") or receipt.get("skipped"):
        raise ValueError("Startup terminal review requires a complete stable pull")
    before = evidence.read(evidence.path(receipt_path).parent / "inventory_before.json")
    after = evidence.read(evidence.path(receipt_path).parent / "inventory_after.json")
    if before != after or evidence.watch(evidence.path(receipt_path).parent / "inventory_before.json") != receipt["inventory_sha256"]:
        raise ValueError("Historical evidence double inventory differs")
    rows = {r["relative"]: r for r in receipt["files"]}
    originals = {r["relative"]: r for r in before["files"]}
    if len(rows) != len(receipt["files"]) or len(originals) != len(before["files"]):
        raise ValueError("Duplicate historical pull entries")
    for rel, (prior, archived) in external.items():
        failed_id = prior["job_id"]
        selected = [r for r in receipt["selected_jobs"] if r.get("job_id") == failed_id]
        if (len(selected) != 1 or selected[0].get("include_run_root") is not True
                or selected[0].get("active_overlapping_job_ids")
                or any(selected[0].get(k) != prior[k] for k in ("mode", "name", "stage_key", "run_root", "source_sha256"))):
            raise ValueError("Historical pull source/job identity differs")
        for when in ("accounting_before", "accounting_after"):
            observed = receipt[when]["jobs"].get(failed_id, {})
            expect(observed, {k: prior[k] for k in ("status", "exit_code", "elapsed_seconds")}, "Historical failed allocation")
            resources = dict(x.split("=", 1) for x in observed.get("allocation", "").split(",") if "=" in x)
            if resources.get("gres/gpu") != "1":
                raise ValueError("Historical failed GPU allocation differs")
        digest = evidence.watch(rel)
        if digest != archived["sha256"]:
            raise ValueError("Historical bytes differ from canonical failure evidence")
        for row in (rows.get(rel, {}), originals.get(rel, {})):
            if (row.get("sha256") != digest or row.get("path") != str(P / rel)
                    or row.get("bytes") != evidence.path(rel).stat().st_size
                    or row.get("job_ids") != [failed_id]):
                raise ValueError("Historical external evidence ownership/hash/path/length differs")
        if rows[rel].get("action") not in ("same_sha_skipped", "downloaded_verified"):
            raise ValueError("Historical pull publication is incomplete")
    return {rel: owner["job_id"] for rel, (owner, _) in sorted(external.items())}


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def digest_value(value):
    if not isinstance(value, str) or not re.fullmatch("[0-9a-f]{64}", value):
        raise ValueError("Missing or malformed SHA256 evidence")
    return value


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Nonfinite or nonnumeric training evidence")
    return value


def same_number(value, expected):
    if not math.isclose(finite(value), expected, rel_tol=1e-7, abs_tol=1e-9):
        raise ValueError("Independently recomputed metric/count differs")


def alpha(update):
    return .1 + .95 * (1 + math.cos(math.pi * (update - 1) / 4999))


def literals(path):
    return {node.targets[0].id: ast.literal_eval(node.value) for node in ast.parse(Path(path).read_text(encoding="utf-8")).body
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id.startswith("FORMAL_")}


def order_for(pool, seed):
    rng, result = random.Random(seed), []
    while len(result) < 40000:
        epoch = list(pool)
        rng.shuffle(epoch)
        result.extend(epoch[:40000 - len(result)])
    return result


def local_server_file(server, relative):
    path, base = PurePosixPath(server), P / relative
    if ".." in path.parts or base not in path.parents:
        raise ValueError("Artifact path leaves this registered nonweight run")
    return path.relative_to(P).as_posix()


def journal(evidence, relative, *, allow_tail=False):
    evidence.watch(relative)
    lines = evidence.path(relative).read_bytes().splitlines(keepends=True)
    rows, tail = [], 0
    for i, line in enumerate(lines):
        try:
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("Journal row is not an object")
            rows.append(row)
        except (ValueError, UnicodeDecodeError):
            if not allow_tail or i != len(lines) - 1 or line.endswith(b"\n"):
                raise ValueError("Journal corruption is not a retained failed-attempt tail")
            tail = len(line)
    return rows, tail


def validation(evidence, relative, *, arm, update, attempt, job_id, manifest, budget, metric):
    report = evidence.read(relative)
    rows = report.get("observations", [])
    ids = manifest["validation_window_ids"]
    expect(report, dict(arm=arm, update=update, attempt_id=attempt, job_id=job_id,
                       windows=len(ids), metric=metric), "Hard validation")
    if [r.get("window_id") for r in rows] != ids:
        raise ValueError("Validation must contain the entire registered ordered panel")
    lookup, by_task = {r["window_id"]: r for r in manifest["windows"]}, defaultdict(list)
    for row in rows:
        ref = lookup[row["window_id"]]
        expect(row, {key: ref[key] for key in ("episode_id", "task_id")}, "Validation window")
        indices = row.get("retained_indices", [])
        if (len(indices) != budget or any(type(i) is not int or not 0 <= i < 512 for i in indices)
                or indices != sorted(set(indices)) or sum(i < 256 for i in indices) != budget // 2):
            raise ValueError("Hard validation violates the registered per-view token budget/packing order")
        actions = row.get("normalized_actions", [])
        if len(actions) != 8 or any(not isinstance(x, list) or len(x) != 7 for x in actions):
            raise ValueError("Hard validation action chunk is not8x7")
        for value in [v for action in actions for v in action] + [row["teacher_l1"], row["demonstration_l1"]]:
            finite(value)
        if row["teacher_l1"] < 0 or row["demonstration_l1"] < 0:
            raise ValueError("Negative action error")
        by_task[str(ref["task_id"])].append(row)
    per_task = {task: {"windows": len(values), **{key: sum(v[key] for v in values) / len(values)
        for key in ("teacher_l1", "demonstration_l1")}} for task, values in by_task.items()}
    if set(report.get("per_task", {})) != set(per_task) or report.get("tasks") != len(per_task):
        raise ValueError("Hard validation task coverage changed")
    for task, values in per_task.items():
        for key, value in values.items():
            same_number(report["per_task"][task].get(key), value)
    for key, field in (("teacher_l1", "validation_metric"), ("demonstration_l1", "demonstration_l1")):
        same_number(report.get(field), sum(v[key] for v in per_task.values()) / len(per_task))
    same_number(report.get("window_weighted_teacher_l1_diagnostic"), sum(r["teacher_l1"] for r in rows) / len(rows))
    return report


def audit_arm(evidence, *, arm, relative, pair, config, manifest, identity, constants, jobs, target):
    base = f"{relative}/{arm}"
    report_path = f"{base}/training_report.json" if evidence.path(f"{base}/training_report.json").exists() else f"{base}/progress_report.json"
    if not evidence.path(report_path).exists():
        if evidence.path(base).exists() and any(evidence.path(base).rglob("*.json*")):
            raise ValueError("An arm with training evidence cannot be treated as not_started")
        return dict(status="not_started", completed=0, resume_sha256=None, initial=None, evaluations=[], samples=0), []
    report = evidence.read(report_path)
    completed = report.get("training_updates_completed")
    if type(completed) is not int or not 0 <= completed <= target <= 5000:
        raise ValueError("Progress is outside the registered planned5000 schedule")
    finished = completed == 5000
    expect(report, dict(schema=ROUND, status="completed" if finished else "checkpointed", arm=arm,
        next_sample_cursor=completed * 8, committed_samples=completed * 8, vla_parameters_unchanged=True,
        frozen_model_sha256=identity["frozen_model_sha256"]), "Arm progress")
    if not finished:
        expect(report, dict(planned_updates=5000, final_deployment_receipt_emitted=False), "Partial arm")
    expected_identity = {**identity, "training_config_sha256": signature({**config, "arm": arm})}
    if report.get("identity") != expected_identity:
        raise ValueError("Progress config/source/gate/numerics identity mismatch")
    resume_path = str(PurePosixPath(pair["checkpoint_root_server"]) / arm / "resume.pt")
    if not finished and report.get("resume_checkpoint") != resume_path:
        raise ValueError("Progress recovery file is not the registered arm resume.pt")
    if not finished:
        digest_value(report.get("resume_sha256"))
    order = order_for(manifest["train_window_ids"], config["seed"])
    expected_order = dict(version=constants["FORMAL_ORDER_VERSION"], seed=config["seed"],
        train_pool_size=len(manifest["train_window_ids"]), train_pool_sha256=signature(manifest["train_window_ids"]),
        samples=order, order_sha256=signature(order), initial_scorer_sha256=digest_value(report.get("initial_scorer_sha256")))
    if evidence.read(f"{base}/training_order.json") != expected_order or report.get("sample_order_sha256") != signature(order):
        raise ValueError("Arm order differs from seeded shuffle of the complete registered pool")
    prefix, lookup = order[:completed * 8], {r["window_id"]: r for r in manifest["windows"]}
    by_task = defaultdict(list)
    for window in prefix:
        by_task[str(lookup[window]["task_id"])].append(window)
    sampling = {task: dict(samples=len(ids), unique_windows=len(set(ids)),
        unique_episodes=len({lookup[i]["episode_id"] for i in ids}),
        phase_sample_counts=dict(Counter(lookup[i]["phase"] for i in ids))) for task, ids in by_task.items()}
    expect(report, dict(unique_committed_windows=len(set(prefix)), train_pool_windows=len(manifest["train_window_ids"]),
                        committed_sampling_by_task=sampling), "Committed sampling")
    same_number(report.get("effective_epochs"), len(prefix) / len(manifest["train_window_ids"]))
    ledgers = sorted(evidence.path(base).glob("attempts/*/cost_events.jsonl"))
    if not ledgers:
        raise ValueError("No raw training/commit journal")
    previous_commit, previous_sha, total_samples, known_jobs, artifacts, truncated = 0, None, 0, set(), {}, 0
    peaks = {key: 0 for key in ("peak_cuda_memory_allocated_bytes", "peak_cuda_memory_reserved_bytes")}
    needed = [report_path, f"{base}/training_order.json"]
    for index, path in enumerate(ledgers):
        rel, attempt = path.relative_to(evidence.root).as_posix(), path.parent.name
        rows, tail = journal(evidence, rel, allow_tail=True)
        if not rows or rows[0].get("event") != "attempt_start":
            raise ValueError("Attempt lacks its initialization/resume event")
        job_id = rows[0].get("job_id")
        if job_id not in jobs or any(r.get("job_id") != job_id or r.get("attempt_id") != attempt for r in rows):
            raise ValueError("Raw attempt belongs to an unregistered or mixed job")
        successful_job = jobs[job_id]["status"] == "COMPLETED" and jobs[job_id]["exit_code"] == "0:0"
        if successful_job and tail:
            raise ValueError("A completed job cannot have a crash-truncated ledger")
        start = rows[0]
        expect(start, dict(identity=expected_identity, completed_update=previous_commit,
                          next_sample_cursor=previous_commit * 8, resumed=index > 0), "Attempt start")
        current, active, micro, sample_active, validating, ended = previous_commit, None, 0, False, None, False
        for event in rows[1:]:
            name = event.get("event")
            if ended:
                raise ValueError("Work appears after attempt_end")
            if name == "update_start":
                if active is not None or validating is not None or event.get("update") != current + 1:
                    raise ValueError("Skipped, duplicated or concurrent update")
                if current % 50 == 0 and previous_commit != current:
                    raise ValueError("An engineering50-update commit is missing before subsequent work")
                active, micro = current + 1, 0
                if event.get("window_ids") != order[(active - 1) * 8:active * 8]:
                    raise ValueError("Actual update used a different sample order")
            elif name in ("sample_start", "sample_end"):
                if active is None or micro >= 8:
                    raise ValueError("Sample outside an active eight-sample update")
                expect(event, dict(update=active, micro_batch_index=micro, window_id=order[(active - 1) * 8 + micro]), "Actual sample")
                if (name == "sample_start") == sample_active:
                    raise ValueError("Unpaired sample forward/backward event")
                sample_active = name == "sample_start"
                if name == "sample_end":
                    micro += 1
                    total_samples += 1
            elif name == "update_end":
                if active is None or micro != 8 or sample_active or event.get("update") != active:
                    raise ValueError("Update committed without exactly eight completed samples")
                expect(event, dict(forward_backward_samples=8), "Completed update")
                same_number(event.get("alpha"), alpha(active))
                for key in ("grad_norm", "loss", "action_loss", "teacher_l1", "demonstration_l1", "seconds"):
                    if finite(event.get(key)) < 0:
                        raise ValueError("Negative training metric/cost")
                for key in peaks:
                    if type(event.get(key)) is not int or event[key] <= 0:
                        raise ValueError("Actual GPU training lacks peak CUDA memory evidence")
                    peaks[key] = max(peaks[key], event[key])
                expected_loss = event["action_loss"] + (0 if arm == "A" else .1 * finite(event.get("future_mse")))
                if (not math.isclose(event["action_loss"], .5 * (event["teacher_l1"] + event["demonstration_l1"]), rel_tol=1e-5, abs_tol=1e-7)
                        or not math.isclose(event["loss"], expected_loss, rel_tol=1e-5, abs_tol=1e-7)):
                    raise ValueError("Logged loss does not match the fixed A/B objective")
                current, active = active, None
            elif name == "validation_start":
                if active is not None or validating is not None or event.get("update") != current or current % 500:
                    raise ValueError("Validation is outside its registered completed-update point")
                expect(event, dict(windows=len(manifest["validation_window_ids"])), "Validation start")
                validating = current
            elif name == "validation_end":
                if validating is None or event.get("update") != validating:
                    raise ValueError("Unpaired validation completion")
                artifact = f"{base}/attempts/{attempt}/validation_{validating:05d}.json"
                checked = validation(evidence, artifact, arm=arm, update=validating, attempt=attempt,
                    job_id=job_id, manifest=manifest, budget=2 * config["tokens_per_camera"], metric=constants["FORMAL_METRIC"])
                expect(event, dict(window_forwards=len(manifest["validation_window_ids"]),
                    artifact_sha256=evidence.watch(artifact), validation_metric=checked["validation_metric"]), "Validation completion")
                artifacts[artifact] = checked
                needed.append(artifact)
                validating = None
            elif name == "checkpoint_commit":
                if active is not None or validating is not None or event.get("completed_update") != current:
                    raise ValueError("Checkpoint commit is not after a complete update/validation")
                if current > 0 and current % 500 == 0 and not any(v["update"] == current for v in artifacts.values()):
                    raise ValueError("A validation-boundary resume was saved before its validation evidence")
                previous_commit, previous_sha = current, digest_value(event.get("resume_sha256"))
            elif name == "attempt_end":
                phase_status = event.get("status")
                clean_end = phase_status in ("checkpointed", "completed")
                field = "completed_update" if clean_end else "completed_update_in_memory"
                expect(event, {field: current}, "Attempt completion")
                if clean_end and (phase_status != ("completed" if current == 5000 else "checkpointed") or active is not None or validating is not None or previous_commit != current):
                    raise ValueError("Successful attempt has no clean committed endpoint")
                if phase_status not in ("checkpointed", "completed", "failed") or (successful_job and not clean_end):
                    raise ValueError("Completed job contains a failed/unknown arm attempt")
                ended = True
            else:
                raise ValueError("Unrecognized training journal event: " + str(name))
        if successful_job and not ended:
            raise ValueError("Completed job has no attempt_end")
        needed.append(rel)
        truncated += tail
        known_jobs.add(job_id)
    if previous_commit != completed or (not finished and previous_sha != report["resume_sha256"]):
        raise ValueError("Latest progress and raw committed recovery checkpoint differ")
    expect(report, dict(attempted_forward_backward_samples_completed=total_samples, job_ids=sorted(known_jobs)), "Actual work accounting")
    for key, value in peaks.items():
        if type(report.get(key)) is not int or report[key] < value:
            raise ValueError("Progress peak memory is absent or below raw actual usage")
    evaluations = report.get("evaluations", [])
    if [row.get("update") for row in evaluations] != list(range(0, completed + 1, 500)):
        raise ValueError("Progress omitted or reordered a registered validation point")
    selected = []
    for row in evaluations:
        artifact = local_server_file(row["artifact_path"], base)
        checked = artifacts.get(artifact)
        if checked is None or evidence.watch(artifact) != row.get("artifact_sha256") or row.get("validation_metric") != checked["validation_metric"]:
            raise ValueError("Selection evidence is not a verified raw validation result")
        candidate = str(PurePosixPath(pair["checkpoint_root_server"]) / arm / "candidates" /
                        f"{checked['attempt_id']}_update{row['update']:05d}.pt")
        if row.get("candidate_path") != candidate:
            raise ValueError("Candidate checkpoint path escaped the registered arm")
        digest_value(row.get("candidate_sha256"))
        selected.append(checked)
    if finished:
        receipt_rel = f"{base}/deployment_receipt.json"
        deployment = evidence.read(receipt_rel)
        metadata = deployment.get("metadata", {})
        best = min(evaluations, key=lambda r: (r["validation_metric"], r["update"]))
        expect(deployment, dict(schema=ROUND, kind="deployment_receipt", pair_config=config,
            training_config={**config, "arm": arm}, planned_updates=5000, completed_updates=5000,
            training_complete=True, base_frozen=True, checkpoint_unchanged=True, evaluations=evaluations,
            f01_report_sha256=identity["f01_report_sha256"], metadata_sha256=signature(metadata)), "Completed deployment receipt")
        expect(metadata, dict(schema=ROUND, suite=config["suite"], seed=config["seed"], arm=arm,
            visual_tokens=2 * config["tokens_per_camera"], per_camera_budgets=[config["tokens_per_camera"]] * 2,
            training_complete=True, base_frozen=True, checkpoint_unchanged=True, update=best["update"],
            validation_metric=best["validation_metric"], pair_id=signature(config), config_sha256=expected_identity["training_config_sha256"],
            training_source_files=identity["training_source_files"], training_source_sha256=signature(identity["training_source_files"]),
            frozen_model_sha256=identity["frozen_model_sha256"], window_manifest_sha256=identity["window_manifest_sha256"],
            data_protocol_sha256=identity["data_protocol_sha256"], input_acceptance_sha256=identity["input_acceptance_sha256"],
            selection_protocol_sha256=identity["selection_protocol_sha256"], selection_metric=constants["FORMAL_METRIC"]), "Selected checkpoint metadata")
        expect(report, dict(best_update=best["update"], best_validation_metric=best["validation_metric"],
            best_checkpoint=str(PurePosixPath(pair["checkpoint_root_server"]) / arm / "best.pt"),
            best_checkpoint_sha256=digest_value(deployment.get("checkpoint_sha256"))), "Completed selected artifact")
        needed.append(receipt_rel)
    return dict(status="completed" if finished else "checkpointed", completed=completed, resume_sha256=previous_sha,
        initial=report["initial_scorer_sha256"], evaluations=selected, samples=total_samples,
        replayed_or_uncommitted_samples=total_samples - completed * 8, truncated_failed_tail_bytes=truncated,
        unique_windows=len(set(prefix)), effective_epochs=len(prefix) / len(manifest["train_window_ids"])), needed


def probe_registered_resume(specs):
    """Only two exact registered resume files; bytes are hashed on the server."""
    if len(specs) != 2 or {s["arm"] for s in specs} != {"A", "B"}:
        raise ValueError("Recovery probe requires precisely the registered A/B pair")
    for row in specs:
        path = PurePosixPath(row["path"])
        if (H / "checkpoints" / ROUND not in path.parents or ".." in path.parts
                or path.name != "resume.pt" or path.parent.name != row["arm"]):
            raise ValueError("Recovery probe path is outside the registered checkpoint scope")
    if len({str(PurePosixPath(row["path"]).parent.parent) for row in specs}) != 1:
        raise ValueError("Recovery probe cannot combine different registered pairs")
    code = """import hashlib,json,os,stat
from pathlib import Path
specs=INPUT
out=[]
for row in specs:
 p=Path(row['path'])
 for parent in [*reversed(p.parents),p]:
  if parent.is_symlink(): raise ValueError('Symlink checkpoint path')
 if not p.exists(): out.append(dict(arm=row['arm'],path=str(p),exists=False)); continue
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as f:
  before=os.fstat(f.fileno())
  if not stat.S_ISREG(before.st_mode): raise ValueError('Not a regular resume file')
  h=hashlib.sha256()
  for b in iter(lambda:f.read(8<<20),b''): h.update(b)
  after=os.fstat(f.fileno())
  if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns): raise ValueError('Resume changed during hash')
  current=os.stat(p,follow_symlinks=False)
  if (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)!=(current.st_dev,current.st_ino,current.st_size,current.st_mtime_ns): raise ValueError('Resume path replaced during hash')
 out.append(dict(arm=row['arm'],path=str(p),exists=True,bytes=after.st_size,sha256=h.hexdigest()))
print(json.dumps(out))
""".replace("INPUT", repr(specs), 1)
    command = shlex.quote(str(H / "venv/bin/python")) + " -c " + shlex.quote(code)
    result = subprocess.run(["ssh", "-o", "BatchMode=yes", "tongji-cvpr", command], check=True,
                            capture_output=True, text=True, timeout=180)
    return json.loads(result.stdout)


def review(job_id, *, source_inventory, pull_receipt, verify_server_resume=False, root=ROOT):
    from cti_vla.data.formal_windows import load_formal_protocol, load_formal_windows
    evidence = Evidence(root)
    job_id = str(job_id)
    if not re.fullmatch(r"[0-9]+", job_id):
        raise ValueError("Invalid registered Slurm job ID")
    state = evidence.read(STATE)
    matches = [j for j in state["registered_jobs"] if str(j.get("job_id")) == str(job_id)]
    if len(matches) != 1:
        raise ValueError("Exactly one registered training job is required")
    job = matches[0]
    suite, budget, seed, target = (job.get(k) for k in ("suite", "visual_tokens", "training_seed", "segment_end"))
    expect(job, dict(job_id=str(job_id), experiment=ROUND, mode="train", status="COMPLETED", exit_code="0:0",
        stage_key=f"{suite}_train_k{budget}_seed{seed}"), "Terminal training job")
    if type(target) is not int or target not in range(500, 5001, 500):
        raise ValueError("Segment review supports registered targets500..5000")
    relative = f"results/{ROUND}/{suite}/k{budget}/seed{seed}/training"
    if job["run_root"] != str(P / relative):
        raise ValueError("Job output is not the registered training pair")
    jobs = {j["job_id"]: j for j in state["registered_jobs"] if j.get("experiment") == ROUND and j.get("stage_key") == job["stage_key"]}
    if any(j.get("status") not in TERMINAL for j in jobs.values()) or state.get("pending_submission") is not None:
        raise ValueError("An active/pending submission prevents a stable segment review")
    if max(jobs.values(), key=lambda j: j["submitted_utc"])["job_id"] != job["job_id"]:
        raise ValueError("Review the newest terminal allocation for this pair")
    inventory = evidence.read(source_inventory)
    files = inventory["files"]
    source_sha = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    expect(inventory, dict(schema=ROUND, source_root_server=job["source_root"], source_sha256=source_sha), "Source inventory")
    if source_sha != job["source_sha256"] or not job["source_root"].startswith(str(P / "snapshots/formal_main_v2_run_")):
        raise ValueError("Job source differs from frozen inventory")
    source_paths = [*sorted((evidence.root / "src").rglob("*.py")), *[evidence.root / "scripts" / n for n in ENTRYPOINTS]]
    sources = {p.relative_to(evidence.root).as_posix(): evidence.watch(p) for p in source_paths}
    if any(files.get(k) != v for k, v in sources.items()):
        raise ValueError("Current runtime bytes differ from frozen source")
    constants = literals(evidence.path("src/cti_vla/training/formal_future.py"))
    registration = evidence.read(REGISTRATION)
    if evidence.watch(REGISTRATION) != files.get(REGISTRATION) or registration.get("schema") != ROUND:
        raise ValueError("Formal registration changed after freeze")
    pairs = [p for p in registration["pairs"] if (p["suite"], p["visual_tokens"], p["seed"]) == (suite, budget, seed)]
    if len(pairs) != 1:
        raise ValueError("Unknown or duplicated registered pair")
    pair, suite_spec = pairs[0], registration["suites"][suite]
    expected_checkpoint_root = str(H / f"checkpoints/{ROUND}/{suite}/k{budget}/seed{seed}")
    if pair["checkpoint_root_server"] != expected_checkpoint_root or pair["run_root_server"] != str(P / relative).removesuffix("/training"):
        raise ValueError("Pair checkpoint/output root is not canonical")
    config = evidence.read(pair["path"])
    if evidence.watch(pair["path"]) != pair["sha256"] or files.get(pair["path"]) != pair["sha256"]:
        raise ValueError("Pair config changed")
    expect(config, dict(schema=ROUND, suite=suite, seed=seed, tokens_per_camera=budget // 2), "Pair config")
    if evidence.read(f"{relative}/registered_config.json") != config:
        raise ValueError("Run did not register this exact pair")
    gate = evidence.read(f"results/{ROUND}/{suite}/acceptance/root_review.json")
    expect(gate, dict(status="passed", suite=suite, source_files=sources, source_sha256=source_sha), "Root engineering review")
    gate_job = next((j for j in state["registered_jobs"] if j["job_id"] == gate["job_id"]), {})
    expect(gate_job, dict(experiment=ROUND, mode="acceptance", status="COMPLETED", exit_code="0:0"), "Accepted GPU job")
    gates = {}
    for name in ("input_acceptance.json", f"f01_k{budget}.json", "resume_acceptance.json", "f03_calls.jsonl", "acceptance_complete.json"):
        path = gate["output_relative"] + "/" + name
        if evidence.watch(path) != gate["files"].get(name):
            raise ValueError("Accepted engineering evidence changed")
        if name.endswith(".json"):
            gates[name] = evidence.read(path)
    protocol_bytes = evidence.read(suite_spec["protocol"])
    evidence.watch(protocol_bytes["dataset_asset"])
    if protocol_bytes.get("inherited_protocol"):
        evidence.watch(protocol_bytes["inherited_protocol"]["path"])
    for name in ("__init__.py", "libero_suite_task_map.py"):
        evidence.watch("external/LIBERO/libero/libero/benchmark/" + name)
    protocol = load_formal_protocol(evidence.path(suite_spec["protocol"]), evidence.root)
    manifest = load_formal_windows(evidence.path(suite_spec["windows"]), protocol)
    protocol_sha, windows_sha = evidence.watch(suite_spec["protocol"]), evidence.watch(suite_spec["windows"])
    asset_sha = evidence.watch(suite_spec["model_manifest"])
    if asset_sha != suite_spec["model_manifest_sha256"] or files.get(suite_spec["model_manifest"]) != asset_sha:
        raise ValueError("Frozen model asset manifest changed")
    if protocol.payload["suite"] != suite or manifest["suite"] != suite:
        raise ValueError("Full-pool data belongs to another suite")
    f00 = gates["input_acceptance.json"]
    expect(f00, dict(window_manifest_sha256=windows_sha, data_protocol_sha256=protocol_sha, source_files=sources), "Accepted full-pool identity")
    invocation = evidence.read(job["invocation"])
    inv_sha = evidence.watch(job["invocation"])
    expect(invocation, dict(schema=ROUND, stage="train", stage_key=job["stage_key"], suite=suite,
        source_root=job["source_root"], source_sha256=source_sha, entrypoint="scripts/run_formal_future.py",
        registration_sha256=evidence.watch(REGISTRATION), segment_end=target), "Training invocation")
    if inv_sha != job["invocation_sha256"]:
        raise ValueError("Registered invocation SHA changed")
    args = invocation.get("argv", [])
    resume = "--resume" in args
    values = args[:-1] if resume and args[-1] == "--resume" else args
    if len(values) % 2 or len(set(values[::2])) != len(values[::2]):
        raise ValueError("Malformed training invocation arguments")
    arguments = dict(zip(values[::2], values[1::2]))
    source = PurePosixPath(job["source_root"])
    expected_arguments = {"--config": str(source / pair["path"]), "--protocol": str(P / suite_spec["protocol"]),
        "--windows": str(P / suite_spec["windows"]), "--checkpoint": suite_spec["model_root_server"],
        "--asset-manifest": str(source / suite_spec["model_manifest"]), "--data-directory": suite_spec["data_root_server"],
        "--cache-directory": str(P / (".local/formal-hf-" + suite)), "--feature-cache": suite_spec["cache_root_server"],
        "--training-checkpoints": pair["checkpoint_root_server"], "--output": str(P / relative), "--arm": "both",
        "--input-acceptance-report": str(P / gate["output_relative"] / "input_acceptance.json"),
        "--acceptance-report": str(P / gate["output_relative"] / f"f01_k{budget}.json"), "--stop-after-updates": str(target),
        "--max-wall-seconds": arguments.get("--max-wall-seconds")}
    if arguments != expected_arguments or finite(float(arguments["--max-wall-seconds"])) <= 0 or (len(jobs) > 1 and not resume):
        raise ValueError("Invocation changed the registered arm/data/segment/resume contract")
    expected_watched = {str(P / suite_spec["protocol"]): protocol_sha, str(P / suite_spec["windows"]): windows_sha,
        str(source / suite_spec["model_manifest"]): asset_sha, str(source / pair["path"]): pair["sha256"],
        **{str(P / gate["output_relative"] / name): gate["files"][name] for name in
           ("input_acceptance.json", f"f01_k{budget}.json", "resume_acceptance.json", "f03_calls.jsonl", "acceptance_complete.json")}}
    if invocation.get("watched_files") != expected_watched:
        raise ValueError("Invocation omitted or changed a required source/data/gate binding")
    for path, digest in invocation["watched_files"].items():
        rel = PurePosixPath(path).relative_to(source if source in PurePosixPath(path).parents else P).as_posix()
        if evidence.watch(rel) != digest:
            raise ValueError("Watched invocation file changed")
    complete_pair = evidence.path(f"{relative}/training_summary.json").exists()
    result_rel = f"{relative}/training_summary.json" if complete_pair else f"{relative}/training_progress.json"
    result_status = "completed" if complete_pair else "checkpointed"
    result = evidence.read(result_rel)
    expect(result, dict(schema=ROUND, status=result_status, planned_updates_per_arm=5000, job_id=job_id,
        requested_arms=["A", "B"], pair_complete=complete_pair, test_opened=False, checkpoint_unchanged=True, source_files=sources), "Pair finalization")
    final_paths = list(evidence.path(relative).glob(f"finalizations/{job_id}_*.json"))
    if len(final_paths) != 1:
        raise ValueError("Exactly one completed finalization for this allocation is required")
    final = evidence.read(final_paths[0])
    expect(final, dict(status="verified", kind="training" if complete_pair else "engineering_segment", checkpoint_unchanged=True, job_id=job_id,
        result_status=result_status, result_sha256=evidence.watch(result_rel), source_files=sources), "Allocation finalization")
    receipt_rel = f"results/{ROUND}/job_receipts/{job_id}.json"
    receipt = evidence.read(receipt_rel)
    expect(receipt, dict(schema=ROUND, job_id=job_id, stage="train", stage_key=job["stage_key"], exit_code=0,
                        invocation_sha256=inv_sha, source_sha256=source_sha), "Allocation receipt")
    if finite(receipt.get("wall_seconds")) <= 0:
        raise ValueError("Missing allocation wall cost")
    runtime_review = _shared.review_runtime_compatibility(evidence, job=job, invocation=invocation,
        receipt=receipt, inventory=inventory, pull_receipt=pull_receipt)
    component_review = _shared.review_component_compatibility(evidence, job=job, invocation=invocation,
        receipt=receipt, inventory=inventory, metadata_review=runtime_review, pull_receipt=pull_receipt)
    # Failed allocations are retained separately, never disguised as successful scopes.
    startup_failure_history = {}
    for failed_id, failed_job in jobs.items():
        if failed_job.get("status") != "COMPLETED" or failed_job.get("exit_code") != "0:0":
            startup_failure_history[failed_id] = _startup.require_saved(evidence, job=failed_job)
    runtime_history = None
    if runtime_review is not None:
        gate_runtime = _shared.require_saved_runtime_review(evidence, saved=gate, job=gate_job, inventory=inventory)
        if gate_runtime is None or gate_runtime["runtime_compatibility"] != runtime_review["runtime_compatibility"]:
            raise ValueError("Training compatibility runtime differs from the reviewed suite acceptance")
        runtime_history = {job_id: runtime_review}
        for prior_id, prior_job in jobs.items():
            if prior_id == job_id:
                continue
            if prior_id in startup_failure_history:
                failed_runtime = startup_failure_history[prior_id]["runtime_failure_evidence"]
                if failed_runtime is None or failed_runtime["runtime_compatibility"] != runtime_review["runtime_compatibility"]:
                    raise ValueError("Failed startup metadata implementation differs from acceptance")
                continue
            prior_invocation = evidence.read(prior_job["invocation"])
            prior_receipt = evidence.read(f"results/{ROUND}/job_receipts/{prior_id}.json")
            prior_runtime = _shared.review_runtime_compatibility(evidence, job=prior_job,
                invocation=prior_invocation, receipt=prior_receipt, inventory=inventory, pull_receipt=pull_receipt)
            if prior_runtime is None or prior_runtime["runtime_compatibility"] != runtime_review["runtime_compatibility"]:
                raise ValueError("A prior pair allocation used another compatibility runtime")
            runtime_history[prior_id] = prior_runtime
    elif any(key in gate for key in ("runtime_compatibility", "runtime_compatibility_review")):
        raise ValueError("Legacy training cannot inherit a compatibility-only acceptance")
    component_history = None
    if component_review is not None:
        gate_component = _shared.require_saved_component_review(evidence, saved=gate, job=gate_job,
            inventory=inventory, metadata_review=gate_runtime)
        if gate_component is None or gate_component["component_compatibility"] != component_review["component_compatibility"]:
            raise ValueError("Goal training component runtime differs from the reviewed suite acceptance")
        component_history = {job_id: component_review}
        for prior_id, prior_job in jobs.items():
            if prior_id == job_id:
                continue
            if prior_id in startup_failure_history:
                raise ValueError("Goal startup failure needs its own component recovery registration")
            prior_component = _shared.review_component_compatibility(evidence, job=prior_job,
                invocation=evidence.read(prior_job["invocation"]),
                receipt=evidence.read(f"results/{ROUND}/job_receipts/{prior_id}.json"), inventory=inventory,
                metadata_review=runtime_history[prior_id], pull_receipt=pull_receipt)
            if prior_component is None or prior_component["component_compatibility"] != component_review["component_compatibility"]:
                raise ValueError("A prior Goal pair allocation used another component runtime")
            component_history[prior_id] = prior_component
    elif any(key in gate for key in ("component_compatibility", "component_compatibility_review")):
        raise ValueError("Non-Goal training cannot inherit Goal component compatibility")
    first = next((result["arms"].get(a, {}) for a in ("A", "B") if result["arms"].get(a, {}).get("status") != "not_started"), None)
    if first is None:
        raise ValueError("No actual training evidence to review")
    cache = first["identity"]["cache_identity"]
    expected_cache = dict(suite=suite, model_revision=config["model_revision"], asset_manifest_sha256=asset_sha,
        data_protocol_sha256=protocol_sha, window_manifest_sha256=windows_sha,
        dataset_statistics_sha256=digest_value(cache.get("dataset_statistics_sha256")), producer_source_files=sources)
    if cache != expected_cache:
        raise ValueError("Cache producer/data identity differs")
    identity = dict(window_manifest_sha256=windows_sha, data_protocol_sha256=protocol_sha,
        selection_protocol_sha256=signature(config["selection"]), input_acceptance_sha256=gate["files"]["input_acceptance.json"],
        f01_report_sha256=gate["files"][f"f01_k{budget}.json"], resume_acceptance_sha256=gate["files"]["resume_acceptance.json"],
        resume_journal_sha256=gate["files"]["f03_calls.jsonl"], frozen_model_sha256=f00["frozen_model_sha256"],
        asset_manifest_sha256=asset_sha, training_source_files=sources, cache_identity=cache,
        training_order_version=constants["FORMAL_ORDER_VERSION"], pair_config_sha256=signature(config),
        training_version=constants["FORMAL_TRAINING_VERSION"], training_numerics=constants["FORMAL_NUMERICS"],
        specification=dict(seed=seed, tokens_per_camera=budget // 2, updates=5000, effective_batch=8, validation_every=500,
            checkpoint_every=50, learning_rate=.0001, weight_decay=.01, gradient_clip_norm=1., alpha_start=2., alpha_end=.1, future_weight=.1))
    required = [f"{relative}/registered_config.json", result_rel, final_paths[0].relative_to(evidence.root).as_posix(),
                receipt_rel, *[f"results/slurm/cti-formal_{job_id}.{ext}" for ext in ("out", "err")]]
    if runtime_history is not None:
        required.extend(path for reviewed in runtime_history.values() for path in reviewed["required_pulled_files"])
    if component_history is not None:
        required.extend(path for reviewed in component_history.values() for path in reviewed["required_pulled_files"])
    arms = {}
    for arm in ("A", "B"):
        arms[arm], needed = audit_arm(evidence, arm=arm, relative=relative, pair=pair, config=config, manifest=manifest,
            identity=identity, constants=constants, jobs=jobs, target=target)
        required.extend(needed)
        arm_name = "training_report.json" if arms[arm]["status"] == "completed" else "progress_report.json"
        actual = evidence.read(f"{relative}/{arm}/{arm_name}") if arms[arm]["status"] != "not_started" else dict(status="not_started", planned_updates=5000)
        if result["arms"].get(arm) != actual:
            raise ValueError("Pair finalization and individual arm progress disagree")
    if all(arms[a]["initial"] for a in arms):
        if arms["A"]["initial"] != arms["B"]["initial"]:
            raise ValueError("A/B did not share the same initial DIE")
        fields = ("window_id", "episode_id", "task_id", "teacher_l1", "demonstration_l1", "retained_indices", "normalized_actions")
        initial_rows = [[{k: r[k] for k in fields} for r in arms[a]["evaluations"][0]["observations"]] for a in ("A", "B")]
        if initial_rows[0] != initial_rows[1]:
            raise ValueError("A/B initial hard behavior differs")
    cache_version = literals(evidence.path("src/cti_vla/training/formal_records.py"))["FORMAL_CACHE_VERSION"]
    cache_hash, cache_counts, component_seconds = signature({"cache_version": cache_version, **cache}), Counter(), defaultdict(float)
    cache_paths = sorted(evidence.path(relative).glob("cache_events/*.jsonl"))
    if not cache_paths:
        raise ValueError("Training has no retained shared-cache cost ledger")
    for path in cache_paths:
        rel = path.relative_to(evidence.root).as_posix()
        rows, tail = journal(evidence, rel, allow_tail=True)
        for row in rows:
            if row.get("job_id") not in jobs or row.get("cache_identity_sha256") != cache_hash:
                raise ValueError("Cache cost belongs to another job/producer")
            if tail and jobs[row["job_id"]]["status"] == "COMPLETED":
                raise ValueError("Successful cache ledger has an incomplete tail")
            cache_counts[row["event"]] += 1
            if row["event"] == "feature_generate_end":
                expect(row, dict(teacher_forwards=1, current_vision_forwards=1, future_vision_forwards=1,
                    future_target_detached=True, window_alignment_validated=True), "Shared cache generation")
                for key in ("current_preprocess_vision_projection_seconds", "teacher_forward_seconds", "future_preprocess_vision_target_seconds", "window_diagnostic_seconds"):
                    component_seconds[key] += finite(row.get(key))
        required.append(rel)
    for path in sorted(evidence.path(relative).glob("failures/*.json")):
        failed_job = path.name.split("_", 1)[0]
        if failed_job not in jobs or jobs[failed_job]["status"] == "COMPLETED":
            raise ValueError("An unregistered/completed allocation has an unreviewed failure artifact")
        expect(evidence.read(path), dict(status="failed"), "Retained failure")
        required.append(path.relative_to(evidence.root).as_posix())
    for failed_review in startup_failure_history.values():
        required.extend(failed_review["retained_failure_files"])
    startup_pull_ownership = require_pulled_startup_ownership(evidence, pull_receipt, job, sorted(set(required)), jobs, startup_failure_history)
    pull = evidence.read(pull_receipt)
    pulled_rows = {r["relative"]: r for r in pull["files"]}
    inventory_rows = {r["relative"]: r for r in evidence.read(evidence.path(pull_receipt).parent / "inventory_before.json")["files"]}
    for j in jobs.values():
        if type(j.get("gpus")) is not int or j["gpus"] != 1 or type(j.get("elapsed_seconds")) is not int or j["elapsed_seconds"] < 0:
            raise ValueError("Registered allocation lacks final GPU accounting")
        for when in ("accounting_before", "accounting_after"):
            observed = pull[when]["jobs"].get(j["job_id"], {})
            expect(observed, {k: j[k] for k in ("status", "exit_code", "elapsed_seconds")}, "Retained pair allocation bill")
            resources = dict(x.split("=", 1) for x in observed.get("allocation", "").split(",") if "=" in x)
            if resources.get("gres/gpu") != "1":
                raise ValueError("GPU count differs from Slurm allocation evidence")
        for suffix in ("out", "err"):
            log = f"results/slurm/cti-formal_{j['job_id']}.{suffix}"
            digest = evidence.watch(log)
            for row in (pulled_rows.get(log, {}), inventory_rows.get(log, {})):
                if (row.get("sha256") != digest or row.get("path") != str(P / log)
                        or row.get("bytes") != evidence.path(log).stat().st_size or j["job_id"] not in row.get("job_ids", [])):
                    raise ValueError("A historical pair allocation log is not retained in the verified pull")
    completed = {a: arms[a]["completed"] for a in arms}
    equal_boundary = completed["A"] == completed["B"] == target
    done = completed["A"] == completed["B"] == 5000
    if done != complete_pair:
        raise ValueError("Completed arms and final pair receipt disagree")
    next_target = None if done else target + 500 if equal_boundary else target
    resume_specs = [dict(arm=a, path=str(PurePosixPath(pair["checkpoint_root_server"]) / a / "resume.pt"),
        must_exist=arms[a]["status"] != "not_started", sha256=arms[a]["resume_sha256"]) for a in ("A", "B")]
    summary = dict(schema=ROUND, kind="root_segment_review", status="local_passed_remote_required", job_id=job_id,
        suite=suite, visual_tokens=budget, seed=seed, output_relative=relative, source_sha256=source_sha,
        invocation_sha256=inv_sha, requested_segment_end=target, completed_by_arm=completed,
        ab_same_registered_boundary=equal_boundary, allowed_next_segment_end=next_target, resume_required=not done,
        continuation="formal_training_complete_no_extension" if done else "advance_one_registered_boundary" if equal_boundary else "complete_original_boundary_only",
        completed_training_receipts=[f"{relative}/{a}/deployment_receipt.json" for a in ("A", "B")] if done else [],
        server_resume_checklist=resume_specs, files={rel: evidence.watch(rel) for rel in sorted(set(required))},
        registered_pair_jobs_at_review=list(jobs.values()), pair_allocated_gpu_seconds=sum(j["gpus"] * j["elapsed_seconds"] for j in jobs.values()),
        attempted_forward_backward_samples=sum(arms[a]["samples"] for a in arms),
        replayed_or_uncommitted_samples=sum(arms[a].get("replayed_or_uncommitted_samples", 0) for a in arms),
        cache_event_counts=dict(cache_counts), cache_generation_component_seconds=dict(component_seconds),
        optimizer_rng_deserialized=False, weights_copied=False, sealed_states_opened=False,
        limits=["Server resume bytes are hashed only; optimizer/RNG/candidate content is revalidated by the frozen training core on resume.",
                "Cache timings are nested diagnostics; the complete Slurm allocation is the GPU bill."])
    if startup_failure_history:
        summary["startup_failure_history"] = startup_failure_history
        summary["startup_pull_ownership"] = startup_pull_ownership
        summary["startup_failure_consumer"] = dict(path=Path(__file__).relative_to(evidence.root).as_posix(),
            sha256=evidence.watch(Path(__file__)), verifier_sha256=evidence.watch(Path(_startup.__file__)))
    if runtime_review is not None:
        summary.update(runtime_compatibility=runtime_review["runtime_compatibility"],
            runtime_compatibility_review=runtime_review, runtime_compatibility_history=runtime_history)
    if component_review is not None:
        summary.update(component_compatibility=component_review["component_compatibility"],
            component_compatibility_review=component_review, component_compatibility_history=component_history)
    if verify_server_resume:
        checks = probe_registered_resume(resume_specs)
        if len(checks) != 2 or {r.get("arm") for r in checks} != {"A", "B"}:
            raise ValueError("Server recovery response is not exactly the registered pair")
        for wanted in resume_specs:
            actual = next(r for r in checks if r["arm"] == wanted["arm"])
            expect(actual, dict(path=wanted["path"], exists=wanted["must_exist"]), "Server resume existence")
            if wanted["must_exist"] and (actual.get("sha256") != wanted["sha256"] or type(actual.get("bytes")) is not int or actual["bytes"] <= 0):
                raise ValueError("Server recovery file differs from the committed SHA receipt; never fresh-restart this arm")
        summary.update(status="passed", server_resume_checks=checks, reviewed_utc=datetime.now(timezone.utc).isoformat(),
                       reviewer_sha256=sha(Path(__file__)), evidence_sha256=dict(evidence.hashes))
        evidence.unchanged()
        path = evidence.path(f"{relative}/segment_reviews/{job_id}.json")
        if path.exists():
            previous = evidence.read(path)
            for key in ("files", "source_sha256", "invocation_sha256", "completed_by_arm", "allowed_next_segment_end", "server_resume_checks",
                        "runtime_compatibility", "runtime_compatibility_review", "runtime_compatibility_history",
                        "component_compatibility", "component_compatibility_review", "component_compatibility_history",
                        "startup_failure_history", "startup_failure_consumer", "startup_pull_ownership"):
                if previous.get(key) != summary.get(key):
                    raise ValueError("Existing immutable segment review differs")
            return previous
        return _shared.publish_review(path, summary)
    evidence.unchanged()
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--source-inventory", type=Path, required=True)
    parser.add_argument("--pull-receipt", type=Path, required=True)
    parser.add_argument("--verify-server-resume", action="store_true", help="Root only: hash exactly this registered pair's two server resume paths")
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("segment_supervisor_lock", ROOT / "scripts/formal_supervisor.py")
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    with supervisor.supervisor_lock():
        result = review(args.job_id, source_inventory=args.source_inventory, pull_receipt=args.pull_receipt,
                        verify_server_resume=args.verify_server_resume)
    print(json.dumps({key: result[key] for key in ("status", "job_id", "completed_by_arm", "allowed_next_segment_end",
        "continuation", "server_resume_checklist", "pair_allocated_gpu_seconds")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

"""Read-only, conditional formal-main-v2 resource planning from real journals.

No model loading, cache tensors, sealed states, SSH, or job submission. Missing
measurements remain pending. Allocation bills and simulated costs are separate.
"""
from __future__ import annotations

import argparse
from collections import Counter, OrderedDict, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = "formal-resource-planning-v2"
SCHEMA = "formal_main_v2"
SUITES = ("libero_10", "libero_spatial", "libero_object", "libero_goal")
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL",
            "PREEMPTED", "BOOT_FAIL", "DEADLINE", "REVOKED", "SPECIAL_EXIT"}
CACHE_VERSION = "formal-main-v2-shared-bounded-ordinary-cpu-records-v1"
ORDER_VERSION = "python-random-private-seeded-full-pool-shuffle-cycle-v1"
CAPACITY = 128 * 1024**3
COMPONENTS = ("current_preprocess_vision_projection_seconds", "teacher_forward_seconds",
              "future_preprocess_vision_target_seconds", "window_diagnostic_seconds")
PRESSURE_ASSUMPTIONS = {
    "version": "formal-resource-planning-v1",
    "timing_interval": "minimum/maximum of all complete measured intervals, not a confidence interval or guaranteed bound",
    "unmeasured_suite_rate_multiplier": [.75, 1.5],
    "unmeasured_training_budget_rate_multiplier": [.9, 1.25],
    "unmeasured_hard_validation_budget_rate_multiplier": [.5, 2.],
    "unseen_record_size_multiplier_of_measured_min_max": [1., 1.25],
    "job_overhead_multiplier": [.5, 2.],
    "final_selected_export": "one additional resume-save duration per arm as an unmeasured proxy for best.pt/receipt export",
    "black_disk_hit_proxy": "if first invocation has no measured black-record disk hit, use measured ordinary-record disk-hit bounds; explicitly an estimate",
    "future_failed_allocation_fraction": [0., .15],
    "disk_cache_bytes_per_suite": CAPACITY,
    "ram_record_capacity_per_invocation": 2,
    "shared_schedule": "serial suites in registration order; Long128seed17 first; remaining pairs in registration order; each pair completes5000 via ten A500-then-B500 invocations",
    "invocation_count": "one successful invocation per500-update pair segment; extra interruption/restart work is an explicit15% upper planning allowance, not an observed reliability bound",
    "schedule_status": "engineering resource scenario only; later actual budget/seed scheduling is not preregistered",
    "cache_initial_state": "cold current namespace per suite; one pinned black record; constant observed per-window bytes where known, empirical size scenarios otherwise",
    "private_schedule": "each arm independently cold with128GiB disk cache and ten invocations; no cross-arm/seed/budget sharing",
    "minimal_A_alternative": "hypothetically omit future target and future-change diagnostics only for train-record generation; retain validation diagnostics and original record sizes; not implemented or measured as an A-only producer",
    "scope": "fresh complete72-arm training scenario, not remaining cost and not additive to already-incurred training; engineering/evaluation costs reported separately",
    "no_extra_runs_authorized": True,
}
MEAN_PLANNING_ASSUMPTIONS = {
    "version": "observed-mean-planning-point-v1",
    "statistic": "arithmetic mean of every complete measured interval; no trimming, winsorizing, spike filtering or percentile substitution",
    "record_size": "known Long keys retain their measured bytes (observed maximum if republished with varying size); unseen keys use ceiling of mean bytes over all measured window publications",
    "black_size": "ceiling of mean bytes over all verified black publications, including accepted same-namespace preparation",
    "unmeasured_suite_rate_multiplier": 1.,
    "unmeasured_training_budget_rate_multiplier": 1.,
    "unmeasured_hard_validation_budget_rate_multiplier": 1.,
    "job_overhead_multiplier": 1.,
    "proxy_status": "Long128 measured means are unvalidated proxies for other suites and token budgets; this is not a measured72-arm total",
    "failure_allowance_options": [0., .15],
    "failure_allowance_interpretation": "separate optional reserve amounts, not a confidence interval, probability estimate or measured failure rate",
    "cache_schedule": "same actual full-pool/RNG/LRU replay and cold-start serial engineering assumptions as the retained pressure scenarios",
    "scope": "fresh complete72-arm training; not remaining time, not additional to actual billed training; unmeasured rollout and profiling costs excluded",
}
ASSUMPTIONS = {**PRESSURE_ASSUMPTIONS, "version": VERSION,
    "retained_pressure_scenarios": PRESSURE_ASSUMPTIONS,
    "observed_mean_planning_point": MEAN_PLANNING_ASSUMPTIONS}


class Pending(Exception):
    def __init__(self, *missing):
        self.missing = list(missing)
        super().__init__("; ".join(missing))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def signature(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class Evidence:
    def __init__(self, root):
        self.root, self.used = Path(root).resolve(), {}

    def path(self, ref, label):
        if not isinstance(ref, dict) or not ref.get("path") or not ref.get("sha256"):
            raise Pending(label + ": missing path/SHA reference")
        raw = Path(ref["path"])
        path = (self.root / raw).resolve()
        if (self.root not in path.parents or path.suffix.lower() not in (".json", ".jsonl")
                or any("sealed" in p.lower() or p.lower() in ("weights", "checkpoints", "initial_states") for p in path.parts)
                or path.name.lower() in ("panel.json", "init_states_test.json")):
            raise ValueError("resource planning reads only project metadata/journals, never weights or state values")
        if not path.is_file():
            raise Pending(label + ": missing " + str(path))
        sha = digest(path)
        if sha != ref["sha256"]:
            raise ValueError("resource evidence SHA mismatch: " + label)
        self.used[str(path)] = sha
        return path

    def read(self, ref, label):
        return json.loads(self.path(ref, label).read_text(encoding="utf-8"))

    def lines(self, ref, label):
        path = self.path(ref, label)
        with path.open("rb") as handle:
            handle.seek(0, 2)
            if handle.tell():
                handle.seek(-1, 2)
                if handle.read(1) != b"\n":
                    raise Pending(label + ": incomplete JSONL tail retained; never repaired")
            handle.seek(0)
            return [json.loads(line) for line in handle]

    def unchanged(self):
        if any(digest(p) != sha for p, sha in self.used.items()):
            raise ValueError("resource evidence changed during read")


def finite(value, label, *, positive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
            or value < 0 or (positive and value == 0)):
        raise ValueError("invalid measured " + label)
    return float(value)


def describe(values):
    values = [finite(x, "duration/size") for x in values]
    if not values:
        raise Pending("missing complete measured timing/size samples")
    return dict(count=len(values), minimum=min(values), maximum=max(values),
        mean=statistics.fmean(values), median=statistics.median(values),
        interval_kind="observed minimum/maximum; not a confidence or guaranteed future bound")


def bounds(values):
    value = describe(values)
    return [value["minimum"], value["maximum"]]


def sample_order(pool, seed, samples=40000):
    """Exact private Python RNG algorithm from formal_future.fixed_window_order."""
    pool = list(pool)
    if (not pool or len(set(pool)) != len(pool) or any(not isinstance(x, str) or not x for x in pool)
            or type(samples) is not int or samples < 0 or type(seed) is not int):
        raise ValueError("full pool requires unique nonempty window identities")
    rng, result = random.Random(seed), []
    while len(result) < samples:
        epoch = pool.copy()
        rng.shuffle(epoch)
        result.extend(epoch[:samples - len(result)])
    return result


def registration_check(registration):
    if (registration.get("schema") != SCHEMA or registration.get("suite_order") != list(SUITES)
            or registration.get("budgets") != [256, 128, 64] or registration.get("seeds") != [17, 23, 41]
            or registration.get("training_arms") != 72):
        raise ValueError("only the registered72-arm full training matrix is estimable")
    expected = {(suite, k, s) for suite in SUITES for k in (256, 128, 64) for s in (17, 23, 41)}
    actual = [(r["suite"], r["visual_tokens"], r["seed"]) for r in registration["pairs"]]
    if len(actual) != 36 or set(actual) != expected:
        raise ValueError("resource pair inventory is not the registered complete36 pairs")


def account_snapshot(state, accounting):
    registered = {}
    for row in state["registered_jobs"]:
        if row.get("experiment") != SCHEMA:
            continue
        job = str(row.get("job_id", ""))
        if not job.isascii() or not job.isdigit() or job in registered:
            raise ValueError("invalid/duplicate registered formal job")
        registered[job] = row
    rows, total, final, failed, by_mode = {}, 0., 0., 0., defaultdict(float)
    for row in accounting.get("jobs", []):
        job = str(row.get("job_id", ""))
        if job not in registered or job in rows or row.get("experiment") != SCHEMA:
            raise ValueError("accounting includes unregistered, foreign or duplicate allocations")
        elapsed = finite(row.get("elapsed_seconds"), "Slurm elapsed seconds")
        gpus = row.get("gpus")
        if type(gpus) is not int or gpus < 0:
            raise ValueError("GPU allocation count must be explicitly measured, not assumed")
        status = str(row.get("status", "")).split()
        if not status:
            raise ValueError("allocation lacks status")
        status = status[0].rstrip("+")
        value = elapsed * gpus
        total += value
        if status in TERMINAL:
            final += value
            if status != "COMPLETED":
                failed += value
        by_mode[row.get("mode", "unspecified")] += value
        rows[job] = {**row, "status": status, "gpu_seconds": value}
    missing = sorted(set(registered) - set(rows))
    return dict(status="complete_terminal_snapshot" if not missing and all(r["status"] in TERMINAL for r in rows.values())
                else "incomplete_or_provisional_snapshot",
        measured_allocation_gpu_seconds_through_snapshot=total, finalized_gpu_seconds=final,
        finalized_failed_gpu_seconds=failed, provisional_gpu_seconds=total - final,
        missing_registered_job_ids=missing, gpu_seconds_by_mode=dict(by_mode), unique_jobs=len(rows),
        scope="Only actual registered allocation seconds; every job counted once. Never add nested phase times or projected cache costs.",
        jobs=rows), registered


def read_windows(reader, refs, registration):
    result = {}
    for suite in SUITES:
        ref = refs.get(suite)
        value = reader.read(ref, suite + ":full windows")
        if (value.get("suite") != suite or value.get("version") != "formal-main-v2-full-pool-h8"
                or value.get("test_pixels_opened") is not False or value.get("horizon") != 8
                or ref["path"].replace("\\", "/") != registration["suites"][suite]["windows"]):
            raise ValueError("resource projection requires the registered full legal pool")
        train, valid = value["train_window_ids"], value["validation_window_ids"]
        rows = {r["window_id"]: r for r in value["windows"]}
        if (not train or not valid or len(set(train)) != len(train) or len(set(valid)) != len(valid)
                or len(rows) != len(value["windows"]) or set(train) & set(valid) or set(rows) != set(train) | set(valid)):
            raise ValueError("full-pool train/validation identities overlap or are incomplete")
        episodes, tasks = {}, defaultdict(set)
        for split, ids in (("train", train), ("validation", valid)):
            for wid in ids:
                row = rows[wid]
                if row["split"] != split or row["task_id"] not in range(10):
                    raise ValueError("window split/task differs from full-pool manifest")
                if row["episode_id"] in episodes and episodes[row["episode_id"]] != split:
                    raise ValueError("episode leakage in resource manifest")
                episodes[row["episode_id"]] = split
                tasks[split].add(row["task_id"])
        if any(tasks[x] != set(range(10)) for x in ("train", "validation")):
            raise ValueError("resource manifest must retain all ten tasks")
        result[suite] = dict(train=list(train), validation=list(valid), rows=rows, sha256=ref["sha256"])
    if len(result["libero_10"]["validation"]) != 165:
        raise ValueError("Long calibration must measure the frozen full165-window validation")
    return result


def read_cache_preparation(reader, specs, *, expected_namespace, expected_window_sha256, frozen_model_sha256,
                           registration, accounting, registered, training_cache_rows):
    """Use accepted preparation solely for black-record size/cold publish time.

    The root review anchors the verified pull, which anchors the journal bytes.
    Acceptance feature/teacher/update timings never enter training calibration.
    """
    if not isinstance(specs, list):
        raise ValueError("acceptance_cache_preparation must be an explicit reference list")
    publications, seen_jobs = [], set()
    training_times = [row.get("time_unix_ns") for row in training_cache_rows]
    if specs and (not training_times or any(type(t) is not int or t <= 0 for t in training_times)):
        raise ValueError("preparation chronology requires timestamped training cache evidence")
    for spec in specs:
        job = str(spec.get("job_id", ""))
        record, bill = registered.get(job), accounting["jobs"].get(job)
        if job in seen_jobs or not record or record.get("mode") != "acceptance" or record.get("suite") != "libero_10":
            raise ValueError("cache preparation requires a unique registered Long acceptance job")
        seen_jobs.add(job)
        if (not bill or bill.get("status") != "COMPLETED" or bill.get("exit_code") != "0:0"
                or bill.get("gpus") != 1):
            raise ValueError("cache preparation needs successful terminal single-GPU accounting")
        loaded = {name: reader.read(spec.get(name), "cache preparation:" + name)
            for name in ("root_review", "pull_receipt", "acceptance_complete", "job_receipt")}
        review, pull, complete, receipt = [loaded[k] for k in
            ("root_review", "pull_receipt", "acceptance_complete", "job_receipt")]
        relative = lambda item: reader.path(item, "cache preparation reference").relative_to(reader.root).as_posix()
        paths = {name: relative(spec.get(name)) for name in loaded}
        paths["cache_events"] = relative(spec.get("cache_events"))
        if (review.get("schema") != SCHEMA or review.get("kind") != "root_acceptance_review"
                or review.get("status") != "passed" or str(review.get("job_id")) != job
                or review.get("suite") != "libero_10" or review.get("sealed_initial_states_opened") is not False
                or review.get("weights_opened") is not False
                or review.get("source_sha256") != record.get("source_sha256")
                or review.get("invocation_sha256") != record.get("invocation_sha256")):
            raise ValueError("cache preparation has no matching passed root acceptance review")
        for name in ("pull_receipt", "acceptance_complete", "job_receipt"):
            if review.get("evidence_sha256", {}).get(paths[name]) != spec[name]["sha256"]:
                raise ValueError("root acceptance review does not SHA-bind preparation evidence")
        for key in ("job_id", "mode", "suite", "run_root", "source_sha256", "invocation_sha256"):
            if review.get("job_at_review", {}).get(key) != record.get(key):
                raise ValueError("root acceptance job identity differs from supervision")
        if (review.get("job_at_review", {}).get("status") != "COMPLETED"
                or review.get("job_at_review", {}).get("elapsed_seconds") != bill["elapsed_seconds"]
                or review.get("evidence_sha256", {}).get(registration["suites"]["libero_10"]["windows"])
                != expected_window_sha256):
            raise ValueError("root acceptance bill or window binding is missing")
        if (complete.get("schema") != SCHEMA or complete.get("status") != "passed"
                or str(complete.get("job_id")) != job or complete.get("suite") != "libero_10"
                or complete.get("frozen_model_sha256") != frozen_model_sha256
                or complete.get("checkpoint_unchanged") is not True or complete.get("test_opened") is not False
                or complete.get("resume_acceptance_passed") is not True
                or complete.get("source_files") != review.get("source_files")):
            raise ValueError("preparation acceptance is not the accepted frozen base/source")
        if (receipt.get("schema") != SCHEMA or str(receipt.get("job_id")) != job
                or receipt.get("stage") != "acceptance" or receipt.get("stage_key") != record.get("stage_key")
                or receipt.get("exit_code") != 0 or receipt.get("source_sha256") != record.get("source_sha256")
                or receipt.get("invocation_sha256") != record.get("invocation_sha256")
                or finite(receipt.get("wall_seconds"), "preparation stage wall seconds", positive=True) > bill["elapsed_seconds"] + 2):
            raise ValueError("preparation stage receipt is not the registered successful invocation")
        if (pull.get("schema") != SCHEMA or pull.get("kind") != "nonweight_pull"
                or pull.get("status") != "verified_nonweight_snapshot" or pull.get("final_evidence") is not True
                or pull.get("weights_copied") is not False or pull.get("sealed_initial_states_copied") is not False
                or pull.get("scientific_completion_inferred") is not False or pull.get("missing") != []):
            raise ValueError("preparation requires a complete verified nonweight pull")
        selected = [row for row in pull.get("selected_jobs", []) if str(row.get("job_id")) == job]
        if (len(selected) != 1 or selected[0].get("include_run_root") is not True
                or selected[0].get("active_overlapping_job_ids") != []
                or any(selected[0].get(k) != record.get(k) for k in ("mode", "run_root", "source_sha256", "stage_key"))):
            raise ValueError("verified pull did not select the registered preparation run")
        before = pull.get("accounting_before", {}).get("jobs", {}).get(job)
        after = pull.get("accounting_after", {}).get("jobs", {}).get(job)
        if (not before or before != after or any(before.get(k) != bill.get(k)
                for k in ("status", "exit_code", "elapsed_seconds", "allocation", "node"))):
            raise ValueError("preparation pull accounting is unstable or differs from the terminal bill")
        output = review.get("output_relative")
        if not isinstance(output, str) or not output:
            raise ValueError("root acceptance output directory is missing")
        for name, filename in (("cache_events", "cache_cost_events.jsonl"), ("acceptance_complete", "acceptance_complete.json")):
            if paths[name] != output + "/" + filename:
                raise ValueError("preparation evidence is outside the reviewed acceptance directory")
        for name in ("cache_events", "acceptance_complete", "job_receipt"):
            matches = [row for row in pull.get("files", []) if row.get("relative") == paths[name]]
            if (len(matches) != 1 or matches[0].get("sha256") != spec[name]["sha256"]
                    or job not in matches[0].get("job_ids", [])
                    or matches[0].get("action") not in ("downloaded_verified", "same_sha_skipped")
                    or matches[0].get("bytes") != reader.path(spec[name], name).stat().st_size):
                raise ValueError("verified pull does not bind the preparation file bytes")
            if name != "job_receipt" and matches[0].get("path") != record["run_root"].rstrip("/") + "/" + Path(paths[name]).name:
                raise ValueError("preparation pull points to another server run directory")
        rows = reader.lines(spec.get("cache_events"), "accepted preparation cache journal")
        times = [row.get("time_unix_ns") for row in rows]
        if (not rows or any(str(row.get("job_id")) != job or row.get("cache_identity_sha256") != expected_namespace for row in rows)
                or any(type(t) is not int or t <= 0 for t in times) or times != sorted(times)
                or max(times) >= min(training_times)):
            raise ValueError("preparation cache journal has another namespace/job or invalid chronology")
        expected_key = hashlib.sha256((expected_namespace + ":shared:black-image").encode()).hexdigest()
        phase, generation_seconds, count = None, None, 0
        for row in rows:
            event = row.get("event")
            if row.get("logical_key") == "shared:black-image" and event == "cache_miss":
                if phase is not None or row.get("key") != expected_key:
                    raise ValueError("preparation black miss has no unique namespace key")
                phase = "miss"
            elif event == "shared_black_generate_start":
                if phase != "miss":
                    raise ValueError("preparation black generation has no cache miss")
                phase = "generating"
            elif event == "shared_black_generate_end":
                if phase != "generating" or row.get("vision_forwards") != 1:
                    raise ValueError("preparation black generation is not a complete single vision forward")
                generation_seconds = finite(row.get("seconds"), "black generation seconds", positive=True)
                phase = "generated"
            elif row.get("logical_key") == "shared:black-image" and event == "cache_publish":
                duration = finite(row.get("seconds"), "black publication seconds", positive=True)
                checksum = row.get("sha256")
                if (phase != "generated" or row.get("key") != expected_key or generation_seconds > duration + .01
                        or type(row.get("bytes")) is not int or row["bytes"] <= 0
                        or not isinstance(checksum, str) or len(checksum) != 64 or any(c not in "0123456789abcdef" for c in checksum)):
                    raise ValueError("preparation black publication is incomplete or lacks identity/size")
                publications.append(dict(job_id=job, cache_identity_sha256=expected_namespace,
                    key=expected_key, bytes=row["bytes"], seconds=duration, record_sha256=checksum,
                    generation_seconds_nested=generation_seconds, publication_time_unix_ns=row["time_unix_ns"],
                    cache_journal_sha256=spec["cache_events"]["sha256"], root_review_sha256=spec["root_review"]["sha256"],
                    pull_receipt_sha256=spec["pull_receipt"]["sha256"]))
                phase, generation_seconds, count = None, None, count + 1
        if phase is not None or not count:
            raise ValueError("accepted preparation lacks a complete black publication")
    return publications


def read_reference(reader, spec, registration, windows, accounting, registered):
    pair = next(r for r in registration["pairs"] if (r["suite"], r["visual_tokens"], r["seed"]) == ("libero_10", 128, 17))
    config = reader.read({"path": pair["path"], "sha256": pair["sha256"]}, "registered Long128seed17 config")
    if (config.get("schema") != SCHEMA or config.get("suite") != "libero_10" or config.get("seed") != 17
            or config.get("tokens_per_camera") != 64 or config["training"].get("updates") != 5000
            or config["training"].get("effective_batch") != 8 or config["training"].get("checkpoint_every_updates") != 50
            or config["selection"].get("updates") != list(range(0, 5001, 500))):
        raise ValueError("reference cannot be a pilot, changed budget or shortened training")
    wm = windows["libero_10"]
    order = sample_order(wm["train"], 17)
    reports, attempts, cost_rows, job_ids = {}, [], [], set()
    for arm in ("A", "B"):
        entry = spec.get("arms", {}).get(arm, {})
        report = reader.read(entry.get("report"), arm + ":formal progress")
        ordering = reader.read(entry.get("training_order"), arm + ":full sample order")
        identity = report.get("identity", {})
        if (report.get("schema") != SCHEMA or report.get("arm") != arm
                or report.get("status") not in ("checkpointed", "completed")
                or report.get("vla_parameters_unchanged") is not True
                or identity.get("pair_config_sha256") != signature(config)
                or identity.get("training_config_sha256") != signature({**config, "arm": arm})
                or identity.get("window_manifest_sha256") != wm["sha256"]
                or report.get("sample_order_sha256") != signature(order)
                or report.get("train_pool_windows") != len(wm["train"])
                or ordering.get("version") != ORDER_VERSION or ordering.get("seed") != 17
                or ordering.get("samples") != order or ordering.get("order_sha256") != signature(order)
                or ordering.get("train_pool_sha256") != signature(wm["train"])
                or ordering.get("train_pool_size") != len(wm["train"])
                or ordering.get("initial_scorer_sha256") != report.get("initial_scorer_sha256")):
            raise ValueError("formal progress/order/base identity differs from the registered complete pool")
        completed = report.get("training_updates_completed")
        if type(completed) is not int or not 0 <= completed <= 5000 or report.get("next_sample_cursor") != completed * 8:
            raise ValueError("formal committed cursor is inconsistent")
        if completed < 500:
            raise Pending(arm + ": need at least the first500 committed formal updates")
        if (report.get("committed_samples") != completed * 8
                or report.get("unique_committed_windows") != len(set(order[:completed * 8]))
                or [r["update"] for r in report.get("evaluations", [])] != list(range(0, completed + 1, 500))):
            raise ValueError("formal progress lacks committed sample/validation coverage")
        refs = entry.get("cost_events", [])
        if not refs:
            raise Pending(arm + ": all cost_events journals missing")
        seen_attempts, rows_for_arm = set(), []
        for ref in refs:
            rows = reader.lines(ref, arm + ":cost_events")
            if not rows or rows[0].get("event") != "attempt_start":
                raise ValueError("cost journal must begin with its attempt identity")
            first = rows[0]
            aid, job = first["attempt_id"], str(first["job_id"])
            if aid in seen_attempts or first.get("identity") != identity or job not in registered:
                raise ValueError("cost attempt is duplicate, unregistered or from another trained arm")
            seen_attempts.add(aid)
            expected_run_root = pair["run_root_server"].rstrip("/") + "/training"
            if registered[job].get("mode") != "train" or registered[job].get("run_root") != expected_run_root:
                raise ValueError("calibration allocation is outside this registered training pair")
            if job not in accounting["jobs"] or accounting["jobs"][job]["status"] not in TERMINAL:
                raise Pending("reference training job lacks terminal accounting: " + job)
            if accounting["jobs"][job].get("gpus") != 1:
                raise ValueError("calibration requires one registered GPU per training allocation")
            if any(r.get("attempt_id") != aid or str(r.get("job_id")) != job for r in rows):
                raise ValueError("mixed cost journal attempt/job IDs")
            elapsed = [finite(r.get("attempt_elapsed_seconds"), "event elapsed seconds") for r in rows]
            if elapsed != sorted(elapsed):
                raise ValueError("cost journal elapsed clock moved backwards")
            if rows[-1].get("event") != "attempt_end":
                raise Pending("reference attempt lacks terminal cost interval: " + aid)
            last = rows[-1]
            if last.get("status") not in ("completed", "checkpointed", "failed"):
                raise ValueError("unknown training attempt terminal status")
            attempt_seconds = finite(last.get("seconds"), "attempt wall seconds", positive=True)
            # Frozen trainer evaluates seconds first, then _peak_memory(),
            # then event() records attempt_elapsed_seconds. This applies to
            # checkpointed/completed/failed exits alike. Scheduling and CUDA
            # statistics can delay the event; these are ordered clock samples,
            # not two equal timestamps subject to a10ms tolerance.
            if not elapsed[-2] <= attempt_seconds <= elapsed[-1]:
                raise ValueError("attempt wall time is outside its preceding-event/terminal-event timestamps")
            normalized = [{**r, "arm": arm} for r in rows]
            cost_rows.extend(normalized)
            rows_for_arm.extend(normalized)
            attempts.append(dict(arm=arm, job_id=job, attempt_id=aid, seconds=attempt_seconds,
                terminal_event_elapsed_seconds=elapsed[-1],
                status=last["status"], resumed=first.get("resumed"), start_update=first["completed_update"],
                end_update=last.get("completed_update", last.get("completed_update_in_memory"))))
            job_ids.add(job)
        if (set(map(str, report.get("job_ids", []))) != {str(r["job_id"]) for r in rows_for_arm}
                or report.get("attempted_forward_backward_samples_completed") != sum(r["event"] == "sample_end" for r in rows_for_arm)):
            raise Pending(arm + ": journals do not cover every reported job/attempted completed sample")
        reports[arm] = report
    for key in ("initial_scorer_sha256", "sample_order_sha256", "frozen_model_sha256"):
        if not reports["A"].get(key) or reports["A"].get(key) != reports["B"].get(key):
            raise ValueError("A/B calibration initialization/order/base identities differ")
    comparable = lambda value: {k: v for k, v in value.items() if k != "training_config_sha256"}
    if comparable(reports["A"]["identity"]) != comparable(reports["B"]["identity"]):
        raise ValueError("A/B resource reference did not share the same frozen implementation")
    cache_refs = spec.get("cache_events", [])
    if not cache_refs:
        raise Pending("complete reference cache_events journals missing")
    cache_rows, seen_refs = [], set()
    for ref in cache_refs:
        key = (ref.get("path"), ref.get("sha256"))
        if key in seen_refs:
            raise ValueError("duplicate cache journal reference would double charge work")
        seen_refs.add(key)
        cache_rows.extend(reader.lines(ref, "reference cache_events"))
    cache_identity = {"cache_version": CACHE_VERSION, **reports["A"]["identity"]["cache_identity"]}
    expected_cache = signature(cache_identity)
    if any(str(r.get("job_id")) not in job_ids or r.get("cache_identity_sha256") != expected_cache for r in cache_rows):
        raise ValueError("cache journal belongs to another allocation/source/model/window namespace")
    receipts = {}
    for ref in spec.get("job_receipts", []):
        value = reader.read(ref, "registered stage job receipt")
        job = str(value.get("job_id"))
        if (value.get("schema") != SCHEMA or value.get("stage") != "train" or job not in job_ids or job in receipts
                or value.get("source_sha256") != registered[job].get("source_sha256")
                or value.get("invocation_sha256") != registered[job].get("invocation_sha256")):
            raise ValueError("stage receipt differs from registered training invocation")
        finite(value.get("wall_seconds"), "stage wall time", positive=True)
        receipts[job] = value
    missing = job_ids - set(receipts)
    if missing:
        raise Pending("missing reference stage receipts: " + ",".join(sorted(missing)))
    preparation = read_cache_preparation(reader, spec.get("acceptance_cache_preparation", []),
        expected_namespace=expected_cache, expected_window_sha256=wm["sha256"],
        frozen_model_sha256=reports["A"]["frozen_model_sha256"],
        registration=registration, accounting=accounting, registered=registered, training_cache_rows=cache_rows)
    return dict(config=config, reports=reports, order=order, attempts=attempts,
        cost_rows=cost_rows, cache_rows=cache_rows, job_ids=job_ids, receipts=receipts,
        accepted_cache_preparation=preparation)


def measured_rates(reference, windows, accounting):
    """Disjoint update/validation/cache/checkpoint durations, never a new bill."""
    wm = windows["libero_10"]
    requests, cache_work = defaultdict(list), defaultdict(float)
    cache_hit, publish, black_publish, black_hit = [], [], [], []
    sizes, pinned_sizes = defaultdict(list), []
    components_by_arm = {a: {k: [] for k in COMPONENTS} for a in ("A", "B")}
    counts, request_counts, evicted_bytes = Counter(), defaultdict(Counter), 0
    for row in reference["cache_rows"]:
        event, job, arm = row["event"], str(row["job_id"]), row.get("arm")
        counts[event] += 1
        if event in ("cache_orphan_cleanup", "cache_eviction"):
            if event == "cache_eviction":
                evicted_bytes += finite(row.get("bytes"), "evicted cache bytes", positive=True)
            continue
        if arm not in ("A", "B"):
            raise ValueError("cache measurement lost its A/B owner")
        group = (job, arm, row.get("phase"), row.get("update"))
        logical = row.get("logical_key")
        if event in ("cache_hit", "cache_miss") and logical and logical.startswith("window:"):
            wid = logical[len("window:"):]
            requests[group].append(wid)
            request_counts[(arm, row.get("phase"))][event] += 1
        elif event == "ram_cache_hit":
            requests[group].append(row["window_id"])
            request_counts[(arm, row.get("phase"))][event] += 1
        if event in ("cache_hit", "cache_publish"):
            seconds = finite(row.get("seconds"), "cache operation seconds")
            cache_work[group] += seconds
            if logical == "shared:black-image":
                (black_hit if event == "cache_hit" else black_publish).append(seconds)
                if event == "cache_publish":
                    if type(row.get("bytes")) is not int or row["bytes"] <= 0:
                        raise ValueError("pinned black publication lacks measured entry bytes")
                    pinned_sizes.append(row["bytes"])
            elif logical and logical.startswith("window:"):
                (cache_hit if event == "cache_hit" else publish).append(seconds)
                if event == "cache_publish":
                    wid = logical[len("window:"):]
                    if wid not in wm["rows"] or type(row.get("bytes")) is not int or row["bytes"] <= 0:
                        raise ValueError("cache publication lacks a registered window/actual entry size")
                    sizes[wid].append(row["bytes"])
            else:
                raise ValueError("unknown cache logical key")
        if event == "feature_generate_end":
            wid = row["window_id"]
            if wid not in wm["rows"] or row.get("future_target_required_by_current_arm") is not (arm == "B"):
                raise ValueError("generated record has unknown window/arm future requirement")
            values = {k: finite(row.get(k), k) for k in COMPONENTS}
            seconds = finite(row.get("seconds"), "feature generation seconds")
            if sum(values.values()) > seconds + .01:
                raise ValueError("feature subintervals exceed their parent duration")
            if (row.get("teacher_forwards") != 1 or row.get("vision_forwards") != 2
                    or row.get("future_target_detached") is not True or row.get("window_alignment_validated") is not True):
                raise ValueError("cache producer is not the registered shared current/teacher/future pipeline")
            for key in COMPONENTS:
                components_by_arm[arm][key].append(values[key])
    update_raw, update_core = defaultdict(list), defaultdict(list)
    validation_raw, validation_core, commits = defaultdict(list), defaultdict(list), defaultdict(list)
    validation_io, attempt_residual, failed_residual, observed_updates = [], [], [], defaultdict(set)
    pending_start, phase_seconds, attempted_samples, samples_open = {}, defaultdict(float), Counter(), {}
    for row in reference["cost_rows"]:
        arm, job, event, aid = row["arm"], str(row["job_id"]), row["event"], row["attempt_id"]
        update = row.get("update")
        phase = "training" if event.startswith("update_") or event.startswith("sample_") else "validation"
        key = (aid, arm, phase, update)
        group = (job, arm, phase, update)
        if event in ("update_start", "validation_start"):
            if key in pending_start:
                raise ValueError("duplicate phase start")
            pending_start[key] = row
            if event == "update_start":
                expected = reference["order"][(update - 1) * 8:update * 8]
                # A failed attempt may end part-way through this phase. Its
                # work remains in actual allocation costs, not calibration.
                if row.get("window_ids") != expected or requests[group] != expected[:len(requests[group])]:
                    raise ValueError("actual full-pool training/cache request order differs from registration")
            elif row.get("windows") != len(wm["validation"]) or requests[group] != wm["validation"][:len(requests[group])]:
                raise ValueError("actual validation/cache requests do not cover the full165-window panel")
        elif event == "sample_start":
            sample = (aid, update, row.get("micro_batch_index"))
            expected = reference["order"][(update - 1) * 8:update * 8]
            micro = row.get("micro_batch_index")
            if (key not in pending_start or sample in samples_open or type(micro) is not int or not 0 <= micro < 8
                    or row.get("window_id") != expected[micro]):
                raise ValueError("sample start does not follow registered micro-batch order")
            samples_open[sample] = row["window_id"]
        elif event == "sample_end":
            sample = (aid, update, row.get("micro_batch_index"))
            if samples_open.pop(sample, None) != row.get("window_id"):
                raise ValueError("sample completion lacks its matching start/window")
            attempted_samples[(aid, update)] += 1
        elif event in ("update_end", "validation_end"):
            start = pending_start.pop(key, None)
            if start is None:
                raise ValueError("completed measured phase lacks its start")
            expected = reference["order"][(update - 1) * 8:update * 8] if event == "update_end" else wm["validation"]
            if requests[group] != expected:
                raise ValueError("completed measured phase lacks all cache request evidence")
            seconds = finite(row.get("seconds"), "phase seconds", positive=True)
            residual = seconds - cache_work[group]
            if residual < -.05:
                raise ValueError("cache operations exceed enclosing phase; would double count or mix attempts")
            residual = max(0., residual)
            if event == "update_end":
                if row.get("forward_backward_samples") != 8 or attempted_samples[(aid, update)] != 8:
                    raise ValueError("update timing is not a complete effective-batch8 update")
                update_raw[arm].append(seconds)
                update_core[arm].append(residual)
                observed_updates[arm].add(update)
                phase_seconds[aid] += seconds
            else:
                if row.get("window_forwards") != 165:
                    raise ValueError("partial validation cannot calibrate a full validation stage")
                validation_raw[arm].append(seconds)
                validation_core[arm].append(residual / 165.)
                # validation_end.seconds excludes JSON/candidate checkpoint
                # writes. Its elapsed start->end span includes those writes.
                enclosing = row["attempt_elapsed_seconds"] - start["attempt_elapsed_seconds"]
                extra = enclosing - seconds
                if extra < -.05:
                    raise ValueError("validation wall boundary is smaller than model/cache work")
                validation_io.append(max(0., extra))
                phase_seconds[aid] += seconds + max(0., extra)
        elif event == "checkpoint_commit":
            seconds = finite(row.get("seconds"), "resume checkpoint save seconds")
            commits[arm].append(seconds)
            phase_seconds[aid] += seconds
        elif event == "attempt_end" and row.get("status") != "failed":
            if any(k[0] == aid for k in pending_start) or any(k[0] == aid for k in samples_open):
                raise ValueError("successful attempt contains an incomplete update/validation/sample")
    for arm in ("A", "B"):
        if not set(range(1, 501)) <= observed_updates[arm] or len(validation_raw[arm]) < 2:
            raise Pending(arm + ": complete first500 updates and both full validation stages are required")
    by_job, terminal_by_job = defaultdict(float), defaultdict(float)
    for attempt in reference["attempts"]:
        aid = attempt["attempt_id"]
        extra = attempt["seconds"] - phase_seconds[aid]
        if extra < -.1:
            raise ValueError("disjoint phase intervals exceed the enclosing arm wall time")
        (failed_residual if attempt["status"] == "failed" else attempt_residual).append(max(0., extra))
        by_job[attempt["job_id"]] += attempt["seconds"]
        terminal_by_job[attempt["job_id"]] += attempt.get("terminal_event_elapsed_seconds", attempt["seconds"])
    job_overheads, job_rows = [], []
    for job in sorted(reference["job_ids"]):
        bill = accounting["jobs"][job]
        receipt = reference["receipts"][job]
        gap = bill["elapsed_seconds"] - by_job[job]
        if (gap < -2 or receipt["wall_seconds"] > bill["elapsed_seconds"] + 2
                or terminal_by_job[job] > bill["elapsed_seconds"] + 2):
            raise ValueError("calibration arm/stage intervals exceed allocated wall time")
        gap = max(0., gap)
        job_overheads.append(gap)
        job_rows.append(dict(job_id=job, actual_allocated_gpu_seconds=bill["gpu_seconds"],
            arm_attempt_wall_seconds=by_job[job], outside_arm_wall_seconds=gap,
            arm_terminal_event_elapsed_seconds=terminal_by_job[job],
            arm_terminal_event_recording_lag_seconds=terminal_by_job[job] - by_job[job],
            stage_wall_seconds=receipt["wall_seconds"],
            allocation_outside_stage_seconds=max(0., bill["elapsed_seconds"] - receipt["wall_seconds"])))
    training_black_publications = len(black_publish)
    preparation = reference.get("accepted_cache_preparation", [])
    # Earlier acceptance is already in the unique Slurm bill. Only its black
    # record calibrates a hypothetical cold namespace; no phase/cache work is
    # charged to these training attempts, and no ordinary record rates leak in.
    black_publish.extend(row["seconds"] for row in preparation)
    pinned_sizes.extend(row["bytes"] for row in preparation)
    if not sizes or not publish or not cache_hit or not pinned_sizes or not black_publish:
        raise Pending("need measured window publications/sizes and disk hits plus black publication/size from training or strictly verified same-namespace acceptance preparation")
    flat_components = {k: [v for a in ("A", "B") for v in components_by_arm[a][k]] for k in COMPONENTS}
    if any(not flat_components[k] for k in COMPONENTS):
        raise Pending("shared feature generation component timings are missing")
    known_sizes = {wid: max(values) for wid, values in sizes.items()}
    return dict(
        observed=dict(
            per_arm={a: dict(update_wall_seconds=describe(update_raw[a]), update_seconds_excluding_cache=describe(update_core[a]),
                updates_per_gpu_second_including_cache=1. / statistics.fmean(update_raw[a]),
                full165_validation_seconds=describe(validation_raw[a]),
                hard_validation_per_window_seconds_excluding_cache=describe(validation_core[a]),
                resume_checkpoint_write_seconds=describe(commits[a]),
                shared_feature_components_seconds={k: describe(v) if v else None for k, v in components_by_arm[a].items()},
                peak_cuda_memory_allocated_bytes=reference["reports"][a].get("peak_cuda_memory_allocated_bytes"),
                committed_updates=reference["reports"][a]["training_updates_completed"],
                committed_samples=reference["reports"][a]["committed_samples"],
                unique_committed_windows=reference["reports"][a]["unique_committed_windows"])
                for a in ("A", "B")},
            cache_events=dict(counts), published_window_bytes=describe([n for values in sizes.values() for n in values]),
            cache_request_counts_by_arm_phase={a + ":" + p: dict(v) for (a, p), v in request_counts.items()},
            evicted_cache_bytes=evicted_bytes,
            pinned_black_bytes=describe(pinned_sizes), disk_hit_seconds=describe(cache_hit),
            black_cache_calibration=dict(training_publications=training_black_publications,
                accepted_preparation_publications=preparation,
                acceptance_contributes_to_training_throughput=False,
                acceptance_cost_already_in_unique_slurm_bill=True,
                calibration_use="black record bytes and cold cache-publish duration only; no actual cost is added"),
            window_publish_seconds_including_generation=describe(publish),
            generation_components_seconds={k: describe(v) for k, v in flat_components.items()},
            future_generation_triggered_by_A_seconds=sum(components_by_arm["A"]["future_preprocess_vision_target_seconds"]),
            future_diagnostics_triggered_by_A_seconds=sum(components_by_arm["A"]["window_diagnostic_seconds"]),
            future_generation_note="Shared provider generates future targets even when A triggers the miss; A loss does not use them. These nested seconds are already in the allocation bill.",
            validation_artifact_and_candidate_write_seconds=describe(validation_io),
            within_arm_other_seconds_per_attempt=describe(attempt_residual),
            failed_attempt_residual_seconds=failed_residual,
            black_record_disk_hit_seconds=(describe(black_hit) if black_hit else {
                "status": "unmeasured", "projection_proxy": "ordinary-record disk-hit bounds, never zero-cost"}),
            jobs=job_rows, job_setup_loading_verification_teardown_seconds=describe(job_overheads),
            isolated_model_loading_seconds=dict(status="not_separately_measured", included_in="outside_arm_wall_seconds",
                limitation="Existing journals cannot separate model loading, hashing, optimizer restore, data checks and scheduler/process overhead."),
            initial_cache_state="not asserted empty; observed hits may predate this evidence; cold-state projections are scenarios",
            failed_allocations_retained=True,
            scope="Phase durations are diagnostics; nested feature/cache components are never added to actual GPU bills."),
        rates=dict(update={a: bounds(update_core[a]) for a in ("A", "B")},
            validation={a: bounds(validation_core[a]) for a in ("A", "B")},
            resume_save={a: bounds(commits[a]) for a in ("A", "B")},
            validation_save=bounds(validation_io), arm_other=bounds(attempt_residual),
            job_other=bounds(job_overheads), cache_hit=bounds(cache_hit), cache_publish=bounds(publish),
            black_publish=bounds(black_publish), black_hit=bounds(black_hit) if black_hit else bounds(cache_hit),
            future_train_avoidable=[min(flat_components[COMPONENTS[2]]) + min(flat_components[COMPONENTS[3]]),
                                    max(flat_components[COMPONENTS[2]]) + max(flat_components[COMPONENTS[3]])]),
        mean_rates=dict(update={a: statistics.fmean(update_core[a]) for a in ("A", "B")},
            validation={a: statistics.fmean(validation_core[a]) for a in ("A", "B")},
            resume_save={a: statistics.fmean(commits[a]) for a in ("A", "B")},
            validation_save=statistics.fmean(validation_io), arm_other=statistics.fmean(attempt_residual),
            job_other=statistics.fmean(job_overheads), cache_hit=statistics.fmean(cache_hit),
            cache_publish=statistics.fmean(publish), black_publish=statistics.fmean(black_publish),
            black_hit=statistics.fmean(black_hit if black_hit else cache_hit),
            future_train_avoidable=statistics.fmean(flat_components[COMPONENTS[2]]) + statistics.fmean(flat_components[COMPONENTS[3]])),
        known_sizes=known_sizes, size_bounds=[min(known_sizes.values()), math.ceil(max(known_sizes.values()) * 1.25)],
        mean_record_bytes=math.ceil(statistics.fmean([n for values in sizes.values() for n in values])),
        mean_black_bytes=math.ceil(statistics.fmean(pinned_sizes)),
        black_size=max(pinned_sizes), reference_job_count=len(reference["job_ids"]))


class CacheReplay:
    """Provider's disk LRU + two-record RAM LRU; RAM hits do not touch disk."""
    def __init__(self, capacity, size_for, black_bytes, ram_capacity=2):
        if type(capacity) is not int or capacity <= 0 or type(ram_capacity) is not int or ram_capacity < 0:
            raise ValueError("cache capacities must be nonnegative integers, with positive disk capacity")
        self.capacity, self.size_for, self.black_bytes = capacity, size_for, black_bytes
        self.ram_capacity = ram_capacity
        self.disk, self.ram, self.total, self.peak = OrderedDict(), OrderedDict(), 0, 0
        self.counts, self.groups = Counter(), defaultdict(Counter)
        self.job = None

    def _access(self, key, size, group, *, pinned=False):
        if key in self.disk:
            self.disk.move_to_end(key)
            self.counts["disk_hits"] += 1
            self.groups[group]["black_hits" if pinned else "disk_hits"] += 1
            return
        if type(size) is not int or not 0 < size <= self.capacity:
            raise ValueError("simulated record size exceeds cache capacity")
        while self.total + size > self.capacity:
            victim = next((k for k in self.disk if k != "__black__"), None)
            if victim is None:
                raise ValueError("pinned black plus one record exceed cache capacity")
            self.total -= self.disk.pop(victim)
            self.counts["evictions"] += 1
        self.disk[key] = size
        self.total += size
        self.peak = max(self.peak, self.total)
        self.counts["misses"] += 1
        self.groups[group]["black_misses" if pinned else "misses"] += 1

    def request(self, job, arm, phase, wid):
        group = (arm, phase)
        if job != self.job:
            self.job = job
            self.ram.clear()
            self._access("__black__", self.black_bytes, group, pinned=True)
        self.counts["requests"] += 1
        self.groups[group]["requests"] += 1
        if wid in self.ram:
            self.ram.move_to_end(wid)
            self.counts["ram_hits"] += 1
            self.groups[group]["ram_hits"] += 1
            return
        self._access(wid, self.size_for(wid), group)
        if self.ram_capacity:
            self.ram[wid] = True
            self.ram.move_to_end(wid)
            while len(self.ram) > self.ram_capacity:
                self.ram.popitem(last=False)

    def summary(self):
        return dict(counts=dict(self.counts), peak_disk_bytes=self.peak, final_disk_bytes=self.total,
            groups={a + ":" + p: dict(v) for (a, p), v in self.groups.items()})


def pair_schedule(order, validation, *, paired=True, arm="A", updates=5000, batch=8, segment=500):
    if (any(type(x) is not int or x <= 0 for x in (updates, batch, segment))
            or updates % segment or len(order) != updates * batch or arm not in ("A", "B")):
        raise ValueError("resource schedule needs complete equally sized update segments")
    for end in range(segment, updates + 1, segment):
        for owner in (("A", "B") if paired else (arm,)):
            if end == segment:
                for wid in validation:
                    yield end, owner, "validation", wid
            for wid in order[(end - segment) * batch:end * batch]:
                yield end, owner, "training", wid
            for wid in validation:
                yield end, owner, "validation", wid


def cache_projection(registration, windows, measured, *, endpoint, shared):
    if endpoint not in (0, 1, "mean"):
        raise ValueError("unknown registered resource scenario")
    unknown_bytes = measured["mean_record_bytes"] if endpoint == "mean" else measured["size_bounds"][endpoint]
    black_bytes = measured["mean_black_bytes"] if endpoint == "mean" else measured["black_size"]
    ordering = sorted(registration["pairs"], key=lambda r: (r["suite"] != "libero_10" or r["visual_tokens"] != 128 or r["seed"] != 17,))
    outputs, shared_caches, orders, peaks = [], {}, {}, []
    for pair_index, pair in enumerate(ordering):
        suite, budget, seed = pair["suite"], pair["visual_tokens"], pair["seed"]
        wm = windows[suite]
        key = (suite, seed)
        if key not in orders:
            orders[key] = sample_order(wm["train"], seed)
        size_for = lambda wid, s=suite: measured["known_sizes"].get(wid, unknown_bytes) if s == "libero_10" else unknown_bytes
        if shared:
            if suite not in shared_caches:
                shared_caches[suite] = CacheReplay(CAPACITY, size_for, black_bytes)
            replay = shared_caches[suite]
            before = {k: Counter(v) for k, v in replay.groups.items()}
            for segment, arm, phase, wid in pair_schedule(orders[key], wm["validation"]):
                replay.request((pair_index, segment), arm, phase, wid)
            groups = {a + ":" + phase: dict(replay.groups[(a, phase)] - before.get((a, phase), Counter()))
                for a in ("A", "B") for phase in ("training", "validation")}
            outputs.append(dict(suite=suite, budget=budget, seed=seed, groups=groups))
        else:
            # Independent A and B have identical requests. Replay once and
            # relabel the measured counts, without sharing any cache state.
            replay = CacheReplay(CAPACITY, size_for, black_bytes)
            for segment, arm, phase, wid in pair_schedule(orders[key], wm["validation"], paired=False):
                replay.request(segment, arm, phase, wid)
            groups = {a + ":" + phase: dict(replay.groups[("A", phase)]) for a in ("A", "B") for phase in ("training", "validation")}
            outputs.append(dict(suite=suite, budget=budget, seed=seed, groups=groups))
        peaks.append(replay.peak)
    return dict(mode="suite_shared_serial_scenario" if shared else "independent_128GiB_per_arm_scenario",
        size_endpoint={0: "measured_or_empirical_small", 1: "measured_or_empirical_large",
            "mean": "measured_keys_or_mean_of_all_measured_publications"}[endpoint],
        pair_order=[dict(suite=p["suite"], budget=p["visual_tokens"], seed=p["seed"]) for p in ordering],
        order_is_resource_assumption=True, rows=outputs,
        maximum_suite_disk_bytes=max(peaks),
        cache_records_are_simulated=True)


def project_observed_mean(registration, windows, measured):
    """A separate unvalidated planning point; retained extremes are untouched."""
    rates, scenarios = measured["mean_rates"], {}
    for shared in (True, False):
        replay = cache_projection(registration, windows, measured, endpoint="mean", shared=shared)
        rows, total, avoidable = [], 0., 0.
        for row in replay["rows"]:
            suite = row["suite"]
            for arm in ("A", "B"):
                groups = [row["groups"][arm + ":" + phase] for phase in ("training", "validation")]
                core = 5000 * rates["update"][arm]
                validation = 11 * len(windows[suite]["validation"]) * rates["validation"][arm]
                saving = 103 * rates["resume_save"][arm] + 11 * rates["validation_save"]
                cache = sum(g.get("misses", 0) * rates["cache_publish"]
                    + g.get("disk_hits", 0) * rates["cache_hit"]
                    + g.get("black_misses", 0) * rates["black_publish"]
                    + g.get("black_hits", 0) * rates["black_hit"] for g in groups)
                other = 10 * rates["arm_other"]
                subtotal = core + validation + saving + cache + other
                A_triggered = groups[0].get("misses", 0) * rates["future_train_avoidable"] if arm == "A" else 0.
                hypothetical = A_triggered if not shared else 0.
                total += subtotal
                avoidable += hypothetical
                rows.append(dict(suite=suite, budget=row["budget"], seed=row["seed"], arm=arm,
                    update_compute_excluding_cache_seconds=core,
                    hard_validation_excluding_cache_seconds=validation,
                    checkpoint_and_validation_artifact_seconds=saving, cache_operations_seconds=cache,
                    within_arm_other_seconds=other, subtotal_seconds=subtotal,
                    A_triggered_train_future_and_diagnostic_component_seconds=A_triggered,
                    A_hypothetical_independent_train_future_savings_seconds=hypothetical,
                    uses_unvalidated_Long128_proxy=(suite != "libero_10" or row["budget"] != 128),
                    cache_requests=sum(g.get("requests", 0) for g in groups),
                    cache_counts={p: row["groups"][arm + ":" + p] for p in ("training", "validation")}))
        jobs = 360 if shared else 720
        overhead = jobs * rates["job_other"]
        base = total + overhead
        name = "shared_cache_serial" if shared else "independent_cache_per_arm"
        scenarios[name] = dict(trained_arms=len(rows), planned_jobs=jobs,
            component_seconds=total, job_setup_loading_verification_teardown_seconds=overhead,
            base_planning_gpu_seconds=base, base_planning_gpu_hours=base / 3600.,
            failure_reserve_options=[dict(fraction=fraction, reserve_gpu_seconds=base * fraction,
                total_planning_gpu_seconds=base * (1. + fraction),
                total_planning_gpu_hours=base * (1. + fraction) / 3600.)
                for fraction in MEAN_PLANNING_ASSUMPTIONS["failure_allowance_options"]],
            rows=rows, cache_replay=replay, hypothetical_A_avoidable_future_seconds=avoidable)
    return dict(status="conditional_observed_mean_planning_point", assumptions=MEAN_PLANNING_ASSUMPTIONS,
        assumptions_sha256=signature(MEAN_PLANNING_ASSUMPTIONS), mean_rates_seconds=rates,
        unseen_record_bytes=measured["mean_record_bytes"], black_record_bytes=measured["mean_black_bytes"],
        known_Long_record_keys=len(measured["known_sizes"]), scenarios=scenarios,
        all_complete_observations_included=True, spike_filtering=False,
        unmeasured_suite_and_budget_multipliers=1., proxy_validated=False,
        confidence_interval=False, fresh_training_only=True, remaining_cost_not_identified=True,
        rollout_and_profiling_costs_included=False)


def project_training(registration, windows, measured):
    scenarios, rates = {}, measured["rates"]
    for shared in (True, False):
        ends, details = [], []
        for endpoint in (0, 1):
            replay = cache_projection(registration, windows, measured, endpoint=endpoint, shared=shared)
            rows, total, avoided = [], 0., 0.
            for row in replay["rows"]:
                suite, budget = row["suite"], row["budget"]
                suite_factor = 1. if suite == "libero_10" else ASSUMPTIONS["unmeasured_suite_rate_multiplier"][endpoint]
                train_factor = 1. if budget == 128 else ASSUMPTIONS["unmeasured_training_budget_rate_multiplier"][endpoint]
                val_factor = 1. if budget == 128 else ASSUMPTIONS["unmeasured_hard_validation_budget_rate_multiplier"][endpoint]
                for arm in ("A", "B"):
                    groups = [row["groups"][arm + ":" + phase] for phase in ("training", "validation")]
                    core = 5000 * rates["update"][arm][endpoint] * train_factor
                    validation = 11 * len(windows[suite]["validation"]) * rates["validation"][arm][endpoint] * val_factor
                    # Fresh arm: initial commit + post-update0 validation commit
                    # + every50 updates through5000 =102 resume writes. The
                    # additional write is an explicit final-export proxy.
                    saving = 103 * rates["resume_save"][arm][endpoint] + 11 * rates["validation_save"][endpoint]
                    cache = sum(g.get("misses", 0) * rates["cache_publish"][endpoint]
                        + g.get("disk_hits", 0) * rates["cache_hit"][endpoint]
                        + g.get("black_misses", 0) * rates["black_publish"][endpoint]
                        + g.get("black_hits", 0) * rates["black_hit"][endpoint] for g in groups)
                    arm_other = 10 * rates["arm_other"][endpoint]
                    subtotal = (core + validation + saving + cache + arm_other) * suite_factor
                    A_triggered_future = (groups[0].get("misses", 0) * rates["future_train_avoidable"][endpoint] * suite_factor
                        if arm == "A" else 0.)
                    # In a shared cache B still needs the future target, so
                    # work triggered by A cannot be labeled globally avoidable.
                    hypothetical_avoidable = A_triggered_future if not shared else 0.
                    avoided += hypothetical_avoidable
                    total += subtotal
                    rows.append(dict(suite=suite, budget=budget, seed=row["seed"], arm=arm,
                        update_compute_excluding_cache_seconds=core * suite_factor,
                        hard_validation_excluding_cache_seconds=validation * suite_factor,
                        checkpoint_and_validation_artifact_seconds=saving * suite_factor,
                        cache_operations_seconds=cache * suite_factor,
                        within_arm_other_seconds=arm_other * suite_factor, subtotal_seconds=subtotal,
                        A_triggered_train_future_and_diagnostic_component_seconds=A_triggered_future,
                        A_hypothetical_independent_train_future_savings_seconds=hypothetical_avoidable,
                        cache_requests=row["groups"][arm + ":training"].get("requests", 0) + row["groups"][arm + ":validation"].get("requests", 0),
                        cache_counts={p: row["groups"][arm + ":" + p] for p in ("training", "validation")}))
            base_jobs = 360 if shared else 720
            # Additional interruptions are not simulated; their upper planning
            # allowance is separate, never relabeled as measured work.
            overhead = base_jobs * rates["job_other"][endpoint] * ASSUMPTIONS["job_overhead_multiplier"][endpoint]
            before_failure = total + overhead
            failure_allowance = before_failure * ASSUMPTIONS["future_failed_allocation_fraction"][endpoint]
            ends.append(before_failure + failure_allowance)
            details.append(dict(endpoint=endpoint, trained_arms=len(rows), planned_jobs=base_jobs,
                component_seconds=total, job_setup_loading_verification_teardown_seconds=overhead,
                assumed_future_failure_allowance_seconds=failure_allowance,
                total_scenario_gpu_seconds=ends[-1], rows=rows, cache_replay=replay,
                hypothetical_A_avoidable_future_seconds=avoided))
        name = "shared_cache_serial" if shared else "independent_cache_per_arm"
        # Larger records can change the hit pattern non-monotonically per arm;
        # report the actual two scenario endpoints plus their ordered envelope.
        scenarios[name] = dict(scenario_gpu_seconds=ends, envelope_gpu_hours=[min(ends) / 3600., max(ends) / 3600.],
            interval_kind="explicit conditional resource scenarios, not confidence limits or a guarantee",
            endpoints=details)
    return dict(status="conditional_training_scenarios_available", assumptions=ASSUMPTIONS,
        assumptions_sha256=signature(ASSUMPTIONS), reference="formal Long128seed17 full-pool first500 or more updates of both A/B",
        retained_pressure_assumptions=PRESSURE_ASSUMPTIONS,
        retained_pressure_assumptions_sha256=signature(PRESSURE_ASSUMPTIONS),
        observed_mean_planning_point=project_observed_mean(registration, windows, measured),
        unmeasured_suites=["libero_spatial", "libero_object", "libero_goal"],
        measured_budget=128, unmeasured_budgets=[256, 64], training_arms=72, updates_per_arm=5000,
        scenarios=scenarios, fresh_training_only=True, remaining_cost_not_identified=True,
        interpretation="Do not add this fresh72-arm scenario to actual training already spent. It is not a remaining-cost forecast. Cache-miss rates follow the stated scheduling hypothesis and may change with real concurrent scheduling; phase times are not an extra allocation bill.")


def estimate(evidence, registration, *, root):
    registration_check(registration)
    reader = Evidence(root)
    if (evidence.get("schema") != SCHEMA or evidence.get("kind") != "resource_evidence"
            or evidence.get("registration_sha256") != signature(registration)):
        raise ValueError("resource evidence belongs to another registration")
    result = dict(version=VERSION, schema=SCHEMA, registration_sha256=signature(registration),
        script_sha256=digest(__file__), evidence_sha256=signature(evidence), assumptions=ASSUMPTIONS,
        measured_results_fabricated=False, weights_read=False, sealed_states_read=False,
        actual_cost=None, training_projection=None,
        evaluation_cost=dict(status="pending_measurements", missing=[
            "registered development/final rollout throughput including simulator/reset work",
            "formal collection and full/component profiling job throughput and loading cost"],
            no_spatial_or_pilot_latency_substitution=True),
        main_experiment_resource_total=dict(status="pending", reason="evaluation costs and cross-suite performance remain unmeasured"),
        new_jobs_submitted=False)
    try:
        actual, registered = account_snapshot(reader.read(evidence.get("supervisor_state"), "supervisor registration"),
            reader.read(evidence.get("accounting"), "registered Slurm accounting"))
        result["actual_cost"] = actual
        if actual["missing_registered_job_ids"]:
            raise Pending("Slurm snapshot misses registered jobs: " + ",".join(actual["missing_registered_job_ids"]))
        missing = [suite + ":full-pool windows" for suite in SUITES if suite not in evidence.get("windows", {})]
        if not evidence.get("reference_pair"):
            missing.append("Long128seed17 A/B formal500 progress, complete cost/cache journals and stage receipts")
        if missing:
            raise Pending(*missing)
        windows = read_windows(reader, evidence["windows"], registration)
        reference = read_reference(reader, evidence["reference_pair"], registration, windows, actual, registered)
        measured = measured_rates(reference, windows, actual)
        result["measured_training"] = measured["observed"]
        result["training_projection"] = project_training(registration, windows, measured)
        result["status"] = "conditional_training_estimate_evaluation_pending"
    except Pending as exc:
        result.update(status="pending", missing=exc.missing)
    reader.unchanged()
    result["read_evidence_sha256"] = reader.used
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registration", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    registration = json.loads(args.registration.read_text(encoding="utf-8"))
    if args.evidence.is_file():
        result = estimate(json.loads(args.evidence.read_text(encoding="utf-8")), registration, root=args.project_root)
    else:
        registration_check(registration)
        result = dict(version=VERSION, status="pending", missing=["resource_evidence manifest not available"],
            actual_cost=None, training_projection=None, evaluation_cost={"status": "pending_measurements"},
            weights_read=False, sealed_states_read=False, new_jobs_submitted=False, script_sha256=digest(__file__))
    if args.output:
        output = args.output.resolve()
        if args.project_root.resolve() not in output.parents or output.exists() or output.suffix.lower() != ".json":
            raise ValueError("resource output must be a new project JSON artifact")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "missing") if k in result}, ensure_ascii=False))


if __name__ == "__main__":
    main()

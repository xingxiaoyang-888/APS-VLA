"""Read-only, SHA-bound independent disk-cache operation replay. No tensors.

Actual Slurm allocation costs and counterfactual cache-operation estimates are
separate. No global timing/size proxies, no model imports, no network clients.
"""
from __future__ import annotations

import argparse
from array import array
from collections import Counter, OrderedDict, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics
import sys

SCHEMA = "formal_main_v2"
VERSION = "formal-independent-disk-cache-replay-v1"
CACHE_VERSION = "formal-main-v2-shared-bounded-ordinary-cpu-records-v1"
ORDER_VERSION = "python-random-private-seeded-full-pool-shuffle-cycle-v1"
SUITES = ("libero_10", "libero_spatial", "libero_object", "libero_goal")
CAPACITY = 128 * 1024**3
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL", "PREEMPTED", "BOOT_FAIL", "DEADLINE"}
ASSUMPTIONS = {
    "scope": "independent disk-cache operation cost estimate; never a complete independent GPU bill",
    "disk_bytes": CAPACITY, "ram_window_records": 2, "black": "pinned disk entry and separate process-memory reference",
    "schedule": "each arm independently cold; ten500-update processes; disk persists, RAM/black reference reset",
    "requests": "40000 fixed training requests and11 full ordered validations; no failed/replayed updates",
    "size": "only actual same-namespace/key publication or committed eviction bytes; conflicts/missing remain unknown",
    "timing": "same namespace/key/operation/fully evidenced hardware identity; all measured spikes retained",
    "range": "empirical minimum/maximum, neither confidence interval nor guaranteed bounds",
    "exclusions": "RAM-hit/wrapper/shard prelude and unidentifiable counterfactual contention/episode/disk effects",
    "A": "unchanged shared provider includes future targets; no hypothetical A-only producer",
}


class Pending(Exception):
    pass


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha(value):
    if not isinstance(value, str) or not re.fullmatch("[0-9a-f]{64}", value):
        raise ValueError("invalid SHA256")
    return value


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
        raise ValueError("duration must be finite and nonnegative")
    return float(value)


def positive_int(value):
    if type(value) is not int or value <= 0:
        raise ValueError("expected positive integer")
    return value


def unique(values, label):
    if not isinstance(values, list) or len(values) != len(set(values)):
        raise ValueError("duplicate/invalid " + label)
    return set(values)


def metadata_path(root, raw):
    """Validate metadata paths before checking existence or reading any bytes."""
    if not isinstance(raw, str) or Path(raw).is_absolute() or re.match(r"^[A-Za-z]:", raw):
        raise ValueError("references must be project-relative")
    def forbidden(parts):
        return any(p in ("", ".", "..") or "sealed" in p.lower() or p.lower() in
                   ("weights", "checkpoints", "initial_states", "test", "tests") for p in parts)
    if forbidden(raw.replace("\\", "/").split("/")):
        raise ValueError("forbidden metadata path")
    p = (root / raw).resolve()
    if (root not in p.parents or p.suffix.lower() not in (".json", ".jsonl")
            or p.name.lower() in ("panel.json", "init_states_test.json")):
        raise ValueError("only project nonweight metadata/journals are readable")
    if forbidden(p.relative_to(root).parts):
        raise ValueError("forbidden resolved metadata path")
    return p


def top_level_reference(root, path):
    raw = path.relative_to(root).as_posix() if path.is_absolute() else path.as_posix()
    p = metadata_path(root, raw)
    return {"path": p.relative_to(root).as_posix(), "sha256": digest(p) if p.is_file() else "0" * 64}


class Evidence:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.used, self.tails = {}, []

    def path(self, ref, label="evidence"):
        if not isinstance(ref, dict) or not ref.get("path") or not ref.get("sha256"):
            raise Pending(label + ": missing path/SHA reference")
        raw = ref["path"]
        p = metadata_path(self.root, raw)
        if not p.is_file():
            raise Pending(label + ": file missing: " + raw)
        if digest(p) != sha(ref["sha256"]):
            raise ValueError(label + ": byte SHA mismatch")
        name = p.relative_to(self.root).as_posix()
        if name in self.used and self.used[name] != ref["sha256"]:
            raise ValueError("one path has conflicting identities")
        self.used[name] = ref["sha256"]
        return p

    def read(self, ref, label="evidence"):
        return json.loads(self.path(ref, label).read_text(encoding="utf-8-sig"))

    def lines(self, ref, label="journal"):
        p = self.path(ref, label)
        rows, lines = [], p.read_bytes().splitlines(keepends=True)
        for n, line in enumerate(lines, 1):
            source = {"path": p.relative_to(self.root).as_posix(), "sha256": ref["sha256"], "line": n}
            if not line.endswith(b"\n"):
                self.tails.append({**source, "kind": "uncommitted_or_truncated_tail", "bytes": len(line)})
                break  # Never salvage a possibly uncommitted last JSON object.
            try:
                row = json.loads(line)
            except (ValueError, UnicodeDecodeError) as exc:
                raise ValueError(label + ": non-tail JSONL corruption") from exc
            if not isinstance(row, dict):
                raise ValueError("journal row must be an object")
            rows.append((row, source))
        return rows

    def unchanged(self):
        if any(digest(self.root / p) != h for p, h in self.used.items()):
            raise ValueError("evidence changed during analysis")


def sample_order(pool, seed, samples=40000):
    unique(pool, "training pool")
    if not pool or type(seed) is not int:
        raise ValueError("invalid registered sample stream")
    rng, result = random.Random(seed), []
    while len(result) < samples:
        epoch = pool.copy()
        rng.shuffle(epoch)
        result.extend(epoch[:samples - len(result)])
    return result


def check_registration(reg):
    expected = {(s, k, n) for s in SUITES for k in (256, 128, 64) for n in (17, 23, 41)}
    pairs = [(p["suite"], p["visual_tokens"], p["seed"]) for p in reg.get("pairs", [])]
    if (reg.get("schema") != SCHEMA or reg.get("suite_order") != list(SUITES)
            or reg.get("budgets") != [256, 128, 64] or reg.get("seeds") != [17, 23, 41]
            or reg.get("arms") != ["A", "B"] or reg.get("training_arms") != 72
            or len(pairs) != 36 or set(pairs) != expected):
        raise ValueError("only the registered72-arm5000-update matrix is supported")
    return {key: p for key, p in zip(pairs, reg["pairs"])}


def read_accounting(reader, manifest, reg):
    state = reader.read(manifest.get("supervisor_state"), "supervision snapshot")
    account = reader.read(manifest.get("accounting"), "actual Slurm accounting")
    registered = {}
    for row in state.get("registered_jobs", []):
        if row.get("experiment") == SCHEMA:
            job = str(row["job_id"])
            if not job.isascii() or not job.isdigit() or job in registered:
                raise ValueError("duplicate/invalid registered job")
            registered[job] = row
    rows = {}
    for row in account.get("jobs", []):
        job = str(row.get("job_id", ""))
        if job not in registered or job in rows or row.get("experiment") != SCHEMA:
            raise ValueError("foreign/unregistered/duplicate allocation")
        for k in ("mode", "suite", "source_sha256", "invocation_sha256", "run_root"):
            if row.get(k) != registered[job].get(k):
                raise ValueError("accounting identity differs from supervision")
        states = str(row.get("status", "")).split()
        if not states:
            raise ValueError("allocation lacks terminal status")
        status = states[0].rstrip("+")
        if status not in TERMINAL:
            raise Pending("allocation not terminal: " + job)
        if type(row.get("gpus")) is not int or row["gpus"] < 0:
            raise ValueError("GPU count is not measured")
        rows[job] = {**row, "job_id": job, "status": status,
                     "gpu_seconds": finite(row.get("elapsed_seconds")) * row["gpus"]}
    if set(rows) != set(registered):
        raise Pending("terminal bills do not cover all registered formal jobs")
    result = {"status": "observed_terminal_snapshot", "jobs": list(rows.values()),
              "gpu_seconds": sum(x["gpu_seconds"] for x in rows.values()),
              "failed_gpu_seconds": sum(x["gpu_seconds"] for x in rows.values() if x["status"] != "COMPLETED"),
              "scope": "actual allocation ledger, each job once; no cache/phase estimate is added"}
    return registered, rows, result


def read_windows(reader, specs, reg):
    result = {}
    for suite, spec in specs.items():
        if suite not in SUITES:
            raise ValueError("unexpected suite")
        refs = reg["suites"][suite]
        for key in ("windows", "protocol"):
            if spec.get(key, {}).get("path") != refs[key]:
                raise ValueError("suite data path differs from registration")
        wm = reader.read(spec["windows"], suite + ": windows")
        reader.read(spec["protocol"], suite + ": episode protocol")
        if (wm.get("suite") != suite or wm.get("version") != "formal-main-v2-full-pool-h8"
                or wm.get("horizon") != 8 or wm.get("test_pixels_opened") is not False):
            raise ValueError("wrong full-pool manifest")
        train, val = wm["train_window_ids"], wm["validation_window_ids"]
        allids = unique(train, "train IDs") | unique(val, "validation IDs")
        rows = {x["window_id"]: x for x in wm["windows"]}
        if not train or not val or set(train) & set(val) or set(rows) != allids or len(rows) != len(wm["windows"]):
            raise ValueError("incomplete/overlapping window partitions")
        episodes, tasks = {}, defaultdict(set)
        for split, ids in (("train", train), ("validation", val)):
            for wid in ids:
                row = rows[wid]
                if row["split"] != split or type(row["task_id"]) is not int or row["task_id"] not in range(10):
                    raise ValueError("window split/task mismatch")
                previous = episodes.setdefault(row["episode_id"], split)
                if previous != split:
                    raise ValueError("episode leakage")
                tasks[split].add(row["task_id"])
        if any(tasks[x] != set(range(10)) for x in ("train", "validation")):
            raise ValueError("all ten tasks must be present")
        result[suite] = {"train": train, "validation": val, "rows": rows,
                         "windows_sha256": spec["windows"]["sha256"], "protocol_sha256": spec["protocol"]["sha256"]}
    return result


def verify_pull(reader, ref, job, bill, file_refs):
    pull = reader.read(ref, "verified pull")
    if (pull.get("schema") != SCHEMA or pull.get("kind") != "nonweight_pull"
            or pull.get("status") != "verified_nonweight_snapshot" or pull.get("final_evidence") is not True
            or pull.get("weights_copied") is not False or pull.get("sealed_initial_states_copied") is not False
            or pull.get("scientific_completion_inferred") is not False or pull.get("missing") != []):
        raise ValueError("unverified/nonfinal pull")
    selected = [x for x in pull.get("selected_jobs", []) if str(x.get("job_id")) == job["job_id"]]
    if (len(selected) != 1 or selected[0].get("include_run_root") is not True
            or selected[0].get("active_overlapping_job_ids") != []
            or any(selected[0].get(k) != job.get(k) for k in ("mode", "run_root", "stage_key", "source_sha256"))):
        raise ValueError("pull did not select this registered inactive run")
    before = pull.get("accounting_before", {}).get("jobs", {}).get(job["job_id"])
    after = pull.get("accounting_after", {}).get("jobs", {}).get(job["job_id"])
    if not before or before != after or any(before.get(k) != bill.get(k) for k in
                                            ("status", "exit_code", "elapsed_seconds", "allocation", "node")):
        raise ValueError("pull/terminal accounting mismatch")
    for f in file_refs:
        p = reader.path(f)
        name = p.relative_to(reader.root).as_posix()
        matches = [x for x in pull.get("files", []) if x.get("relative") == name]
        if (len(matches) != 1 or matches[0].get("sha256") != f["sha256"]
                or matches[0].get("bytes") != p.stat().st_size or job["job_id"] not in matches[0].get("job_ids", [])
                or matches[0].get("action") not in ("downloaded_verified", "same_sha_skipped")):
            raise ValueError("pull does not bind exact source bytes: " + name)
        if "/cache_events/" in name or name.endswith("cache_cost_events.jsonl") or "/attempts/" in name:
            marker = name.split("/training/", 1)[-1] if "/training/" in name else Path(name).name
            if matches[0].get("path") != job["run_root"].rstrip("/") + "/" + marker:
                raise ValueError("journal points to another server run")
    return pull


def job_hardware(reader, spec, job, bill, verified_pull):
    # sacct proves a GPU class, not a particular driver/runtime/device.
    match = re.search(r"(?:^|,)gres/gpu:([^=,]+)=([0-9]+)(?:,|$)", bill.get("allocation", ""))
    known = {"job_id": job["job_id"], "node": bill.get("node"),
             "gpu_class": match[1] if match else None, "allocation": bill.get("allocation")}
    if bill.get("gpus") != 1 or not match or int(match[2]) != 1:
        raise ValueError("cache observations require one explicit GPU allocation")
    ref = spec.get("hardware_record")
    if ref:
        value = reader.read(ref, "job-local hardware evidence")
        verify_pull(reader, verified_pull, job, bill, [ref])
        if str(value.get("job_id")) != job["job_id"]:
            raise ValueError("hardware evidence belongs to another job")
        fields = ("gpu_name", "torch_version", "cuda_version", "driver_version", "device_uuid")
        known.update({k: value[k] for k in fields if isinstance(value.get(k), str) and value[k]})
    required = ("gpu_name", "torch_version", "cuda_version", "driver_version", "device_uuid")
    complete = all(known.get(k) for k in required)
    return {**known, "identity_sha256": signature({k: known[k] for k in required}) if complete else None,
            "status": "complete_job_local_identity" if complete else "gpu_class_or_partial_only",
            "missing": [k for k in required if not known.get(k)]}


def check_arm(reader, item, pair, wm, reg, bills):
    arm, seed, budget, suite = item["arm"], pair["seed"], pair["visual_tokens"], pair["suite"]
    config = reader.read({"path": pair["path"], "sha256": pair["sha256"]}, "registered pair")
    if (config.get("suite") != suite or config.get("seed") != seed or config.get("tokens_per_camera") != budget // 2
            or config.get("training", {}).get("updates") != 5000 or config["training"].get("effective_batch") != 8
            or config.get("selection", {}).get("updates") != list(range(0, 5001, 500))):
        raise ValueError("changed formal configuration")
    report = reader.read(item.get("report"), "training report")
    order_file = reader.read(item.get("training_order"), "full sample order")
    order = sample_order(wm["train"], seed)
    identity = report.get("identity", {})
    cache_identity = identity.get("cache_identity", {})
    if (report.get("schema") != SCHEMA or report.get("arm") != arm or arm not in ("A", "B")
            or identity.get("pair_config_sha256") != signature(config)
            or identity.get("training_config_sha256") != signature({**config, "arm": arm})
            or identity.get("window_manifest_sha256") != wm["windows_sha256"]
            or identity.get("data_protocol_sha256") != wm["protocol_sha256"]
            or cache_identity.get("window_manifest_sha256") != wm["windows_sha256"]
            or cache_identity.get("data_protocol_sha256") != wm["protocol_sha256"]
            or cache_identity.get("producer_source_files") != identity.get("training_source_files")
            or not identity.get("training_source_files")
            or cache_identity.get("suite") != suite
            or cache_identity.get("model_revision") != reg["suites"][suite]["model_revision"]
            or cache_identity.get("asset_manifest_sha256") != reg["suites"][suite]["model_manifest_sha256"]
            or report.get("vla_parameters_unchanged") is not True
            or report.get("frozen_model_sha256") != identity.get("frozen_model_sha256")):
        raise ValueError("trained data/base/source/namespace identity differs")
    sha(identity.get("frozen_model_sha256")); sha(cache_identity.get("dataset_statistics_sha256"))
    if (order_file.get("version") != ORDER_VERSION or order_file.get("seed") != seed
            or order_file.get("samples") != order or order_file.get("order_sha256") != signature(order)
            or order_file.get("train_pool_sha256") != signature(wm["train"])
            or order_file.get("train_pool_size") != len(wm["train"])
            or report.get("sample_order_sha256") != signature(order)
            or order_file.get("initial_scorer_sha256") != report.get("initial_scorer_sha256")):
        raise ValueError("sample order/initialization differs from registration")
    complete = report.get("status") == "completed" and report.get("training_updates_completed") == 5000
    completed = report.get("training_updates_completed")
    if type(completed) is not int or not 0 <= completed <= 5000 or report.get("committed_samples") != completed * 8:
        raise ValueError("invalid committed training cursor")
    if report.get("status") not in ("completed", "checkpointed"):
        raise ValueError("unexpected training status")
    if report.get("next_sample_cursor") != completed * 8 or report.get("train_pool_windows") != len(wm["train"]):
        raise ValueError("training cursor/pool mismatch")
    if [x["update"] for x in report.get("evaluations", [])] != list(range(0, completed + 1, 500)):
        raise ValueError("committed validation history missing")
    if complete:
        receipt = reader.read(item.get("receipt"), "deployment receipt")
        md = receipt.get("metadata", {})
        if (receipt.get("schema") != SCHEMA or receipt.get("kind") != "deployment_receipt"
                or receipt.get("pair_config") != config or receipt.get("training_config") != {**config, "arm": arm}
                or receipt.get("metadata_sha256") != signature(md)
                or receipt.get("planned_updates") != 5000 or receipt.get("completed_updates") != 5000
                or any(receipt.get(k) is not True for k in ("training_complete", "base_frozen", "checkpoint_unchanged"))
                or receipt.get("evaluations") != report["evaluations"]
                or receipt.get("checkpoint_sha256") != report.get("best_checkpoint_sha256")
                or receipt.get("f01_report_sha256") != identity.get("f01_report_sha256")):
            raise ValueError("deployment receipt does not bind completed training")
        bindings = {"arm": arm, "suite": suite, "seed": seed, "visual_tokens": budget, "training_complete": True,
                    "pair_id": signature(config), "config_sha256": signature({**config, "arm": arm}),
                    "window_manifest_sha256": wm["windows_sha256"], "frozen_model_sha256": identity["frozen_model_sha256"],
                    "data_protocol_sha256": wm["protocol_sha256"], "selection_protocol_sha256": signature(config["selection"]),
                    "training_source_files": identity["training_source_files"], "model_revision": config["model_revision"]}
        if any(md.get(k) != v for k, v in bindings.items()):
            raise ValueError("receipt selected checkpoint identity differs")
        best = min(report["evaluations"], key=lambda x: (finite(x["validation_metric"]), x["update"]))
        if (md.get("update"), md.get("validation_metric")) != (best["update"], best["validation_metric"]):
            raise ValueError("receipt violates earliest minimum selection")
        sha(receipt["checkpoint_sha256"])
    namespace = signature({"cache_version": CACHE_VERSION, **cache_identity})
    return dict(item=item, pair=pair, config=config, report=report, identity=identity, namespace=namespace,
                order=order, windows=wm, complete=complete, key=(suite, budget, seed, arm))


def parse_attempt(reader, ref, arm, registered, bills):
    rows = reader.lines(ref, "attempt journal")
    if not rows or rows[0][0].get("event") != "attempt_start":
        raise ValueError("attempt lacks start identity")
    first = rows[0][0]
    job, aid = str(first.get("job_id")), first.get("attempt_id")
    record, bill = registered.get(job), bills.get(job)
    if (not record or not bill or first.get("identity") != arm["identity"] or record.get("mode") != "train"
            or record.get("suite") != arm["key"][0]
            or record.get("run_root") != arm["pair"]["run_root_server"].rstrip("/") + "/training"):
        raise ValueError("attempt job/pair/source identity mismatch")
    start = first.get("completed_update")
    if type(start) is not int or not 0 <= start <= 5000 or first.get("next_sample_cursor") != start * 8:
        raise ValueError("invalid resume start")
    groups, open_phase, current, sample, elapsed, completed_updates, sample_ends = {}, None, start, None, -1., set(), 0
    for row, source in rows:
        if str(row.get("job_id")) != job or row.get("attempt_id") != aid:
            raise ValueError("mixed attempt identity")
        clock = finite(row.get("attempt_elapsed_seconds"))
        if clock < elapsed:
            raise ValueError("attempt elapsed clock regressed")
        elapsed = clock
        event, update = row.get("event"), row.get("update")
        if event in ("update_start", "validation_start"):
            phase = "training" if event == "update_start" else "validation"
            if open_phase is not None or sample is not None or (phase, update) in groups:
                raise ValueError("nested/duplicate phase")
            expected = arm["order"][(update - 1) * 8:update * 8] if phase == "training" else arm["windows"]["validation"]
            if phase == "training" and (update != current + 1 or row.get("window_ids") != expected):
                raise ValueError("training update/order mismatch")
            if phase == "validation" and (update not in range(0, 5001, 500) or update != current or row.get("windows") != len(expected)):
                raise ValueError("validation point/count mismatch")
            open_phase = (phase, update)
            groups[open_phase] = dict(expected=expected, sample_starts=0, sample_ends=0, complete=False, source=source)
        elif event == "sample_start":
            if open_phase != ("training", update) or sample is not None:
                raise ValueError("sample outside update")
            group = groups[open_phase]; index = group["sample_starts"]
            if index >= 8 or row.get("micro_batch_index") != index or row.get("window_id") != group["expected"][index]:
                raise ValueError("microbatch request mismatch")
            sample = (index, row["window_id"]); group["sample_starts"] += 1
        elif event == "sample_end":
            if open_phase != ("training", update) or sample != (row.get("micro_batch_index"), row.get("window_id")):
                raise ValueError("sample end lacks matching start")
            groups[open_phase]["sample_ends"] += 1; sample_ends += 1; sample = None
        elif event in ("update_end", "validation_end"):
            phase = "training" if event == "update_end" else "validation"
            if open_phase != (phase, update) or sample is not None:
                raise ValueError("phase completion lacks matching start")
            group = groups[open_phase]
            if phase == "training":
                if group["sample_ends"] != 8 or row.get("forward_backward_samples") != 8:
                    raise ValueError("incomplete effective batch")
                current = update; completed_updates.add(update)
            elif row.get("window_forwards") != len(group["expected"]):
                raise ValueError("incomplete validation")
            finite(row.get("seconds")); group["complete"] = True; open_phase = None
    ended = rows[-1][0].get("event") == "attempt_end"
    last = rows[-1][0]
    if ended and last.get("status") in ("completed", "checkpointed"):
        if open_phase or sample or last.get("completed_update") != current:
            raise ValueError("successful attempt leaves unfinished phase")
    elif bill["status"] == "COMPLETED":
        raise Pending("successful allocation lacks complete attempt journal: " + aid)
    return dict(job=job, aid=aid, groups=groups, completed_updates=completed_updates,
                sample_ends=sample_ends, failed_or_partial=not ended or last.get("status") == "failed", ref=ref)


def parse_cache(reader, ref, *, job, namespace, windows, hardware):
    rows = reader.lines(ref, "cache journal")
    pending, sizes, observations, requests, unknown, evictions = {}, [], [], defaultdict(list), [], []
    clock = -1
    for row, source in rows:
        event = row.get("event")
        if str(row.get("job_id")) != job or row.get("cache_identity_sha256") != namespace:
            raise ValueError("cache namespace/job mismatch")
        stamp = row.get("time_unix_ns")
        if type(stamp) is not int or stamp <= 0 or stamp < clock:
            raise ValueError("invalid cache event clock")
        clock = stamp
        context = (row.get("arm"), row.get("phase"), row.get("update"))
        logical = row.get("logical_key")
        key = row.get("key")
        if logical is not None:
            if key != hashlib.sha256((namespace + ":" + logical).encode()).hexdigest():
                raise ValueError("cache key is not its namespace/logical hash")
            if logical != "shared:black-image" and (not logical.startswith("window:") or logical[7:] not in windows):
                raise ValueError("cache accesses unregistered window")
        if event in ("cache_hit", "cache_miss", "ram_cache_hit"):
            if event == "ram_cache_hit":
                wid = row.get("window_id")
                if wid not in windows:
                    raise ValueError("RAM hit outside legal windows")
            elif logical and logical.startswith("window:"):
                wid = logical[7:]
            else:
                wid = None
            if wid is not None:
                requests[context].append(wid)
        if event == "cache_miss":
            if key in pending:
                raise ValueError("duplicate open cache miss")
            pending[key] = dict(logical=logical, context=context, source=source, generated=False, generating=False)
        elif event in ("feature_generate_start", "shared_black_generate_start", "feature_generate_end", "shared_black_generate_end"):
            target = "shared:black-image" if event.startswith("shared_black") else "window:" + str(row.get("window_id"))
            target_key = hashlib.sha256((namespace + ":" + target).encode()).hexdigest()
            active = pending.get(target_key)
            if not active or active["context"] != context:
                raise ValueError("generation lacks matching cache miss")
            if event.endswith("start"):
                if active["generating"] or active["generated"]:
                    raise ValueError("duplicate generation start")
                active["generating"] = True
            else:
                if not active["generating"] or active["generated"]:
                    raise ValueError("generation end lacks start")
                active["generated"] = True
                active["seconds"] = finite(row.get("seconds"))
                if event == "feature_generate_end" and (row.get("teacher_forwards") != 1 or row.get("vision_forwards") != 2
                        or row.get("future_target_detached") is not True or row.get("window_alignment_validated") is not True):
                    raise ValueError("different cache producer")
        elif event == "cache_publish":
            active = pending.pop(key, None)
            duration = finite(row.get("seconds")); size = positive_int(row.get("bytes"))
            if (not active or not active["generated"] or active["context"] != context
                    or active["seconds"] > duration + .01):
                raise ValueError("publication lacks complete generation/transaction evidence")
            sha(row.get("sha256"))
            sizes.append(dict(namespace=namespace, key=key, logical_key=logical, bytes=size, source=source,
                              record_sha256=row["sha256"], kind="publication"))
        elif event == "cache_eviction":
            sha(key); positive_int(row.get("bytes"))
            if key == hashlib.sha256((namespace + ":shared:black-image").encode()).hexdigest():
                raise ValueError("pinned black cannot be evicted")
            # The event namespace belongs to the publisher; victim may be from
            # another namespace. Resolve victim by its full hashed key later.
            evictions.append(dict(key=key, bytes=row["bytes"], source=source, kind="committed_eviction"))
        elif event == "cache_orphan_cleanup":
            unknown.append(dict(kind="orphan_cleanup_not_a_committed_record_size", source=source,
                                key=key, bytes=row.get("bytes")))
        elif event not in ("cache_hit", "ram_cache_hit", "shard_index_verified", "cache_orphan_cleanup"):
            raise ValueError("unrecognized cache event: " + str(event))
        if event in ("cache_publish", "cache_hit"):
            if event == "cache_hit" and key in pending:
                raise ValueError("hit while same journal has uncompleted miss")
            observations.append(dict(namespace=namespace, key=key, logical_key=logical, operation=event,
                seconds=finite(row.get("seconds")), job_id=job, hardware=hardware,
                source=source, context={"arm": context[0], "phase": context[1], "update": context[2]}))
    for key, value in pending.items():
        unknown.append(dict(kind="ambiguous_unlogged_commit_or_incomplete_generation", key=key,
                            namespace=namespace, source=value["source"]))
    return dict(sizes=sizes, observations=observations, requests=dict(requests), unknown=unknown, evictions=evictions)


def replay_counts(order, validation, namespace, size_observations, *, capacity=CAPACITY, segment=500, batch=8):
    """Exact isolated logical LRU. Size evidence, never proxy sizes, drives eviction."""
    if len(order) % (segment * batch) or not order or not validation:
        raise ValueError("incomplete counterfactual request schedule")
    logicals = {"window:" + x for x in order + validation} | {"shared:black-image"}
    keys = {x: hashlib.sha256((namespace + ":" + x).encode()).hexdigest() for x in logicals}
    sizes, missing, conflict = {}, [], []
    size_index = size_observations if isinstance(size_observations, dict) else defaultdict(set)
    if not isinstance(size_observations, dict):
        for row in size_observations:
            size_index[row["key"]].add(positive_int(row["bytes"]))
    for logical, key in sorted(keys.items()):
        values = set(size_index.get(key, ()))
        if not values:
            missing.append({"logical_key": logical, "key": key})
        elif len(values) != 1:
            conflict.append({"logical_key": logical, "key": key, "bytes": sorted(values)})
        else:
            sizes[key] = values.pop()
    if missing or conflict:
        return {"status": "unknown_sizes", "counts": None, "missing_sizes": missing, "conflicting_sizes": conflict}
    black = keys["shared:black-image"]
    if sizes[black] > capacity or any(sizes[k] + sizes[black] > capacity for k in sizes if k != black):
        raise ValueError("pinned black plus record cannot fit registered capacity")
    disk, ram, total, peak = OrderedDict(), OrderedDict(), 0, 0
    counts, operations = Counter(), Counter()
    requests_hash, decisions_hash = hashlib.sha256(), hashlib.sha256()
    def emit(h, value):
        h.update((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
    def access(logical, phase, seg):
        nonlocal total, peak
        key = keys[logical]
        emit(requests_hash, [seg, phase, logical])
        if key != black:
            counts["window_requests"] += 1
        if key != black and key in ram:
            ram.move_to_end(key); counts["ram_hits"] += 1
            emit(decisions_hash, [seg, phase, key, "ram_hit", []]); return
        victims = []
        if key in disk:
            disk.move_to_end(key); op = "cache_hit"
        else:
            while total + sizes[key] > capacity:
                victim = next((k for k in disk if k != black), None)
                if victim is None:
                    raise ValueError("no evictable record")
                total -= disk.pop(victim); victims.append(victim); counts["evictions"] += 1
            disk[key] = sizes[key]; total += sizes[key]; peak = max(peak, total); op = "cache_publish"
        counts[("black_" if key == black else "window_") + op.removeprefix("cache_")] += 1
        operations[(key, op)] += 1
        emit(decisions_hash, [seg, phase, key, op, victims])
        if key != black:
            ram[key] = True
            while len(ram) > 2:
                ram.popitem(last=False)
    segments = len(order) // (segment * batch)
    for seg in range(segments):
        ram.clear()
        access("shared:black-image", "process_start", seg)
        if seg == 0:
            for wid in validation:
                access("window:" + wid, "validation0", seg)
        for wid in order[seg * segment * batch:(seg + 1) * segment * batch]:
            access("window:" + wid, "training", seg)
        for wid in validation:
            access("window:" + wid, "validation", seg)
    return dict(status="exact_under_registered_no_failure_schedule", counts=dict(counts), peak_disk_bytes=peak,
                final_disk_bytes=total, request_stream_sha256=requests_hash.hexdigest(), decision_stream_sha256=decisions_hash.hexdigest(),
                operations=[dict(key=k, operation=op, count=n) for (k, op), n in sorted(operations.items())])


class ObservationIndex:
    """One shared source index, never72 copies of millions of timing rows.

    Incomplete hardware observations remain addressable by original journal
    SHA/line; they are never pooled into eligible timing calibration groups.
    """
    def __init__(self):
        self.journals, self.groups, self.count = {}, {}, 0

    def add(self, row):
        source = row["source"]; identity = (source["path"], source["sha256"])
        if identity not in self.journals:
            self.journals[identity] = dict(id=len(self.journals), path=identity[0], sha256=identity[1],
                lines=array("I"), operations=Counter(), job_ids=set(), hardware_identity_sha256=row["hardware"].get("identity_sha256"))
        journal = self.journals[identity]
        journal["lines"].append(source["line"]); journal["operations"][row["operation"]] += 1
        journal["job_ids"].add(row["job_id"]); self.count += 1
        hid = row["hardware"].get("identity_sha256")
        if not hid:
            return
        key = (row["namespace"], row["key"], row["operation"], hid)
        if key not in self.groups:
            self.groups[key] = dict(id=len(self.groups), times=array("d"), sources=defaultdict(lambda: array("I")))
        group = self.groups[key]
        group["times"].append(row["seconds"]); group["sources"][journal["id"]].append(source["line"])

    def get(self, key):
        group = self.groups.get(key)
        if not group:
            return None
        times = group["times"]
        return dict(id=group["id"], mean=statistics.fmean(times), minimum=min(times), maximum=max(times), observations=len(times))

    def summary(self):
        return dict(observations=self.count, journals=[dict(id=j["id"], path=j["path"], sha256=j["sha256"],
            completed_operation_lines=list(j["lines"]), operations=dict(j["operations"]), job_ids=sorted(j["job_ids"]),
            hardware_identity_sha256=j["hardware_identity_sha256"]) for j in self.journals.values()],
            eligible_calibration=[dict(namespace=k[0], key=k[1], operation=k[2], hardware_identity_sha256=k[3],
                **self.get(k), sources=[dict(journal_id=jid, lines=list(lines)) for jid, lines in g["sources"].items()])
                for k,g in self.groups.items()],
            raw_values="All seconds remain in SHA-bound original journal lines; no spike is removed.")


def compact_replay(value):
    out = {k: v for k,v in value.items() if k not in ("operations", "missing_sizes", "conflicting_sizes")}
    for name in ("missing_sizes", "conflicting_sizes"):
        if name in value:
            out[name + "_count"] = len(value[name])
            out[name + "_sha256"] = signature(value[name])
    if "operations" in value:
        out["operation_key_count"] = len(value["operations"])
        out["operation_counts_sha256"] = signature(value["operations"])
    return out


def calibrate(replay, namespace, observations, hardware_identity, *, compact=False):
    if replay["status"] != "exact_under_registered_no_failure_schedule":
        return {"status": "unknown_counts", "complete_seconds": None}
    index = observations
    if not isinstance(index, ObservationIndex):
        index = defaultdict(list)
        for row in observations:
            index[(row["namespace"], row["key"], row["operation"], row["hardware"].get("identity_sha256"))].append(row)
    covered, unknown, mean, lower, upper, detail = 0, [], 0., 0., 0., []
    for op in replay["operations"]:
        lookup = (namespace, op["key"], op["operation"], hardware_identity)
        stats = index.get(lookup) if isinstance(index, ObservationIndex) and hardware_identity else None
        values = index[lookup] if not isinstance(index, ObservationIndex) and hardware_identity else []
        if not stats and not values:
            unknown.append({**op, "reason": "unknown_hardware_identity" if not hardware_identity else "no_same_key_operation_hardware_observation"})
            continue
        if not stats:
            times = [x["seconds"] for x in values]
            stats = dict(mean=statistics.fmean(times), minimum=min(times), maximum=max(times), observations=len(times))
        covered += op["count"]; mean += op["count"] * stats["mean"]
        lower += op["count"] * stats["minimum"]; upper += op["count"] * stats["maximum"]
        if not compact:
            detail.append({**op, **stats, "sources": [x["source"] for x in values]})
    total = sum(x["count"] for x in replay["operations"])
    measured = {"mean": mean, "empirical_min_sum": lower, "empirical_max_sum": upper}
    result = {"status": "estimated_with_limitations" if not unknown else "partial_unknown",
            "complete_seconds": measured if not unknown else None,
            "covered_operation_seconds": measured if covered else None,
            "covered_operations": covered, "requested_disk_operations": total,
            "operation_coverage": covered / total if total else None, "unknown": unknown, "calibration": detail,
            "interval_kind": "all-observation empirical range; not CI or guaranteed bound",
            "unmeasured": ["RAM and wrapper", "counterfactual lock/episode/storage/eviction state effects"]}
    if compact:
        result.pop("calibration"); result.pop("unknown")
        result["unknown_operation_keys"] = len(unknown)
        result["unknown_operations"] = sum(x["count"] for x in unknown)
        result["unknown_by_reason"] = dict(Counter({reason: sum(x["count"] for x in unknown if x["reason"] == reason)
                                                   for reason in {x["reason"] for x in unknown}}))
        result["unknown_stream_sha256"] = signature(unknown)
    return result


def analyze(reader, registration_ref, manifest_ref):
    reg = reader.read(registration_ref, "formal registration"); pairs = check_registration(reg)
    out = dict(schema=SCHEMA, kind="independent_disk_cache_operation_cost_estimate", version=VERSION,
               assumptions=ASSUMPTIONS, assumptions_sha256=signature(ASSUMPTIONS), registration_sha256=signature(reg),
               status="pending_evidence", missing=[], actual_allocation=None, arms=[], observation_index=None, transaction_unknown=[])
    try:
        manifest = reader.read(manifest_ref, "cache replay evidence manifest")
        if manifest.get("schema") != SCHEMA or manifest.get("kind") != "cache_replay_evidence" or manifest.get("registration_sha256") != signature(reg):
            raise ValueError("wrong replay evidence manifest")
        registered, bills, out["actual_allocation"] = read_accounting(reader, manifest, reg)
        windows = read_windows(reader, manifest.get("suites", {}), reg)
        arms, attempts, groups, names = {}, {}, {}, {}
        for item in manifest.get("training", []):
            key = (item["suite"], item["visual_tokens"], item["seed"], item["arm"])
            if key[:3] not in pairs or key[3] not in ("A", "B") or key in arms:
                raise ValueError("duplicate/foreign trained instance")
            if key[0] not in windows:
                raise Pending("missing suite windows: " + key[0])
            arm = check_arm(reader, item, pairs[key[:3]], windows[key[0]], reg, bills)
            arms[key] = arm
            names[arm["namespace"]] = arm["windows"]["rows"]
            completed_updates, validations, samples, arm_jobs = set(), set(), 0, set()
            for ref in item.get("cost_events", []):
                attempt = parse_attempt(reader, ref, arm, registered, bills)
                ak = (attempt["job"], key[3])
                if ak in attempts:
                    raise ValueError("more than one attempt for one arm/job")
                attempts[ak] = attempt; arm_jobs.add(attempt["job"])
                completed_updates |= attempt["completed_updates"]; samples += attempt["sample_ends"]
                for (phase, update), group in attempt["groups"].items():
                    groups[(attempt["job"], key[3], phase, update)] = group
                    if phase == "validation" and group["complete"]:
                        validations.add(update)
            if arm_jobs != set(map(str, arm["report"].get("job_ids", []))) or samples != arm["report"].get("attempted_forward_backward_samples_completed"):
                raise Pending("all reported attempt/sample evidence required: " + str(key))
            if arm["complete"] and (completed_updates != set(range(1, 5001)) or validations != set(range(0, 5001, 500))):
                raise Pending("completed report lacks complete update/validation journals: " + str(key))
        # Incomplete reports are still audited; never turn a1000-update prefix
        # into a completed72-arm result merely because its cache parser works.
        expected = {(*key, a) for key in pairs for a in ("A", "B")}
        out["missing"] += ["complete training instance: " + str(k) for k in sorted(expected - arms.keys())]
        out["missing"] += ["5000-update completion/receipt: " + str(k) for k, a in arms.items() if not a["complete"]]
        for key, arm in arms.items():
            partner = arms.get((*key[:3], "B" if key[3] == "A" else "A"))
            if partner and any(arm["report"].get(k) != partner["report"].get(k) for k in
                               ("initial_scorer_sha256", "sample_order_sha256", "frozen_model_sha256")):
                raise ValueError("A/B initialization/order/base mismatch")
        size_rows, observations, cache_requests, seen_jobs, evidence_files, hardware = defaultdict(set), ObservationIndex(), {}, set(), {}, {}
        size_source_counts = Counter()
        pulled_bytes = set()
        for spec in manifest.get("cache_jobs", []):
            job_id = str(spec.get("job_id", "")); job = registered.get(job_id); bill = bills.get(job_id)
            if not job or job_id in seen_jobs or job.get("mode") not in ("train", "acceptance"):
                raise ValueError("duplicate/foreign cache job")
            seen_jobs.add(job_id)
            refs = spec.get("cache_events", [])
            job_attempt_refs = [x["ref"] for (j, _), x in attempts.items() if j == job_id]
            job_files = refs + job_attempt_refs
            receipt = reader.read(spec.get("job_receipt"), "job receipt")
            if (str(receipt.get("job_id")) != job_id or receipt.get("schema") != SCHEMA
                    or any(receipt.get(k) != job.get(k) for k in ("source_sha256", "invocation_sha256", "stage_key"))
                    or receipt.get("stage") != job.get("mode")):
                raise ValueError("job receipt identity mismatch")
            if finite(receipt.get("wall_seconds")) > finite(bill["elapsed_seconds"]) + 2:
                raise ValueError("job receipt exceeds allocation wall boundary")
            if bill["status"] == "COMPLETED" and (receipt.get("exit_code") != 0 or bill.get("exit_code") != "0:0"):
                raise ValueError("successful job has inconsistent exit status")
            review = reader.read(spec.get("root_review"), "root cache evidence review")
            if (review.get("schema") != SCHEMA or str(review.get("job_id")) != job_id
                    or review.get("source_sha256") != job.get("source_sha256")
                    or review.get("invocation_sha256") != job.get("invocation_sha256")
                    or review.get("status") not in ("passed", "recorded_failure")):
                raise ValueError("cache evidence lacks matching root review")
            for flag in ("sealed_states_opened", "sealed_initial_states_opened", "weights_copied", "weights_opened"):
                if review.get(flag) is True:
                    raise ValueError("review reports forbidden state/weight access")
            namespace = spec.get("namespace_sha256"); sha(namespace)
            if namespace not in names:
                raise Pending("namespace has no trained-arm/data identity: " + namespace)
            if job.get("mode") == "acceptance":
                complete = reader.read(spec.get("acceptance_complete"), "accepted cache preparation")
                if (review.get("kind") != "root_acceptance_review" or review.get("status") != "passed"
                        or complete.get("status") != "passed" or str(complete.get("job_id")) != job_id
                        or complete.get("test_opened") is not False or complete.get("checkpoint_unchanged") is not True
                        or bill["status"] != "COMPLETED" or receipt.get("exit_code") != 0):
                    raise ValueError("preparation is not a successfully accepted run")
                owners = [a for a in arms.values() if a["namespace"] == namespace]
                if any(complete.get("frozen_model_sha256") != a["identity"]["frozen_model_sha256"] for a in owners):
                    raise ValueError("preparation base differs")
                if any(complete.get("source_files") != a["identity"]["training_source_files"] for a in owners):
                    raise ValueError("preparation producer source differs")
                job_files.append(spec["acceptance_complete"])
            else:
                owners = [a for a in arms.values() if job_id in a["report"].get("job_ids", [])]
                if owners and any(a["namespace"] != namespace for a in owners):
                    raise ValueError("training cache namespace differs from arm")
            job_files.append(spec["job_receipt"])
            pull = verify_pull(reader, spec.get("verified_pull"), job, bill, job_files)
            pulled_bytes.update((x.get("relative"), x.get("sha256")) for x in pull.get("files", [])
                if x.get("action") in ("downloaded_verified", "same_sha_skipped")
                and x.get("bytes") is not None)
            # Historical acceptance review anchors the pull, not each journal
            # directly. The already-verified pull provides the transitive byte
            # binding; do not require a field that its frozen writer lacks.
            anchors = [spec["verified_pull"], spec["job_receipt"]]
            if spec.get("acceptance_complete"):
                anchors.append(spec["acceptance_complete"])
            for ref in anchors:
                if review.get("evidence_sha256", {}).get(ref["path"]) != ref["sha256"]:
                    raise ValueError("root review lacks byte binding")
            for ref in refs:
                existing = review.get("evidence_sha256", {}).get(ref["path"])
                if existing is not None and existing != ref["sha256"]:
                    raise ValueError("root review contradicts pull journal SHA")
            hw = job_hardware(reader, spec, job, bill, spec["verified_pull"]); hardware[job_id] = hw
            for ref in refs:
                if ref["path"] in evidence_files:
                    raise ValueError("duplicate cache journal")
                evidence_files[ref["path"]] = ref["sha256"]
                parsed = parse_cache(reader, ref, job=job_id, namespace=namespace, windows=names[namespace], hardware=hw)
                for row in parsed["sizes"] + parsed["evictions"]:
                    size_rows[row["key"]].add(row["bytes"])
                    size_source_counts[(row["source"]["path"],row["source"]["sha256"],row["kind"])] += 1
                for row in parsed["observations"]:
                    observations.add(row)
                out["transaction_unknown"] += parsed["unknown"]
                for context, values in parsed["requests"].items():
                    if job.get("mode") == "train":
                        group_key = (job_id, *context)
                        if group_key in cache_requests:
                            raise ValueError("phase split across journals")
                        cache_requests[group_key] = values
            # Fail closed if the pull inventory contains omitted attempt/cache
            # files for this job. Do not inspect their contents speculatively.
            relevant = {x["relative"]: x["sha256"] for x in pull.get("files", [])
                if job_id in x.get("job_ids", []) and ("/cache_events/" in x.get("relative", "")
                or x.get("relative", "").endswith("cache_cost_events.jsonl") or x.get("relative", "").endswith("cost_events.jsonl"))}
            supplied = {x["path"]: x["sha256"] for x in refs + job_attempt_refs}
            # Earlier immutable attempts can be present in a later pull; their
            # SHA must occur elsewhere in this manifest, never be silently lost.
            all_journals = {f["path"]: f["sha256"] for a in manifest.get("training", []) for f in a.get("cost_events", [])}
            all_journals.update({f["path"]: f["sha256"] for j in manifest.get("cache_jobs", []) for f in j.get("cache_events", [])})
            if any(all_journals.get(p) != h for p, h in relevant.items()):
                raise Pending("pull contains omitted immutable journals: " + job_id)
        for key, group in groups.items():
            got = cache_requests.pop(key, [])
            expected_ids = group["expected"]
            if got != expected_ids[:len(got)] or len(got) > len(expected_ids):
                raise ValueError("cache request order differs from exact trainer stream")
            if group["complete"] and got != expected_ids:
                raise Pending("completed phase lacks cache requests: " + str(key))
            if key[2] == "training" and len(got) > group["sample_starts"]:
                raise ValueError("cache requests exceed actual attempted samples")
        if cache_requests:
            raise ValueError("cache requests lack matching attempt phases")
        for arm in arms.values():
            for name in ("report", "training_order", "receipt"):
                ref = arm["item"].get(name)
                if ref and (ref["path"], ref["sha256"]) not in pulled_bytes:
                    raise ValueError("training artifact lacks a verified pull byte binding: " + name)
        missing_cache_jobs = {j for j, _ in attempts} - seen_jobs
        out["missing"] += ["cache evidence job: " + j for j in sorted(missing_cache_jobs)]
        out["observation_index"], out["hardware"] = observations.summary(), hardware
        out["size_evidence"] = dict(keys=len(size_rows), conflicting_keys=sum(len(v)!=1 for v in size_rows.values()),
            source_counts=[dict(path=p,sha256=h,kind=k,rows=n) for (p,h,k),n in size_source_counts.items()],
            scope="Actual bytes remain in original SHA-bound publication/eviction rows; no size proxies.")
        out["transaction_unknown"] += reader.tails
        out["audited_training_instances"] = len(arms)
        # Only a root-closed evidence inventory establishes that earlier failed
        # jobs, preparation and all source logs have not been omitted.
        inventory = reader.read(manifest.get("root_cost_inventory"), "root final cost/evidence inventory")
        if (inventory.get("schema") != SCHEMA or inventory.get("kind") != "final_cost_inventory"
                or inventory.get("issued_by") != "root" or inventory.get("complete") is not True
                or inventory.get("registration_sha256") != signature(reg)):
            raise Pending("root has not closed the final cost inventory")
        if unique(inventory.get("job_ids"), "root job IDs") != set(bills):
            raise ValueError("root bill inventory differs")
        if unique(inventory.get("cache_job_ids"), "cache job IDs") != seen_jobs:
            raise ValueError("root cache-job inventory differs")
        required_files = {ref["path"]: ref["sha256"] for a in manifest.get("training", [])
                          for ref in [a["report"], a["training_order"], *a.get("cost_events", [])] + ([a["receipt"]] if a.get("receipt") else [])}
        required_files.update(evidence_files)
        required_files.update({manifest[k]["path"]: manifest[k]["sha256"] for k in ("supervisor_state", "accounting")})
        required_files.update({f["path"]: f["sha256"] for s in manifest.get("suites", {}).values() for f in s.values()})
        for spec in manifest.get("cache_jobs", []):
            for key in ("root_review", "verified_pull", "job_receipt", "acceptance_complete", "hardware_record"):
                if spec.get(key):
                    required_files[spec[key]["path"]] = spec[key]["sha256"]
        if any(inventory.get("evidence_sha256", {}).get(p) != h for p, h in required_files.items()):
            raise ValueError("root final inventory does not bind all evidence")
        if out["missing"] or set(windows) != set(SUITES):
            out["missing"] += ["full suite metadata: " + s for s in SUITES if s not in windows]
            return out
        for key, arm in sorted(arms.items()):
            replay = replay_counts(arm["order"], arm["windows"]["validation"], arm["namespace"], size_rows)
            target_job = manifest.get("target_hardware_job_by_suite", {}).get(key[0])
            hwid = hardware.get(str(target_job), {}).get("identity_sha256")
            if target_job is not None and (str(target_job) not in hardware or registered[str(target_job)].get("suite") != key[0]):
                raise ValueError("target hardware is not an evidenced same-suite job")
            estimate = calibrate(replay, arm["namespace"], observations, hwid, compact=True)
            out["arms"].append(dict(suite=key[0], visual_tokens=key[1], seed=key[2], arm=key[3],
                namespace_sha256=arm["namespace"], replay=compact_replay(replay), timing=estimate, target_hardware_job=target_job))
        out["status"] = "completed_estimate_with_limitations"
        out["limitations"] = ["counts are a no-failure isolated-cache counterfactual, not shared-run disk history",
            "missing/conflicting sizes yield unknown counts; missing operations/hardware yield unknown timing",
            "publication includes nested generation/lock/IO; never add feature components",
            "no complete independent training GPU bill is identified; actual allocations remain separate"]
        return out
    except Pending as exc:
        out["missing"].append(str(exc))
        return out
    finally:
        reader.unchanged()
        out["evidence_sha256"] = dict(sorted(reader.used.items()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--registration", type=Path, default=Path("configs/experiments/formal_main_v2.json"))
    parser.add_argument("--evidence", type=Path, default=Path("results/formal_main_v2/cache_replay_evidence.json"))
    parser.add_argument("--output", type=Path, help="optional NEW JSON only; defaults to stdout")
    args = parser.parse_args(); root = args.project_root.resolve()
    reader = Evidence(root)
    try:
        result = analyze(reader, top_level_reference(root, args.registration), top_level_reference(root, args.evidence))
    except (ValueError, KeyError, TypeError) as exc:
        result = {"schema": SCHEMA, "version": VERSION, "status": "rejected_evidence", "error": str(exc)}
    result["analyzer_sha256"] = digest(Path(__file__))
    text = json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        output = (root / args.output).resolve()
        if root not in output.parents or output.suffix.lower() != ".json" or output.exists():
            raise ValueError("output must be a NEW project JSON; existing artifacts are immutable")
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text, end="")
    return 2 if result["status"] == "rejected_evidence" else 0


if __name__ == "__main__":
    sys.exit(main())

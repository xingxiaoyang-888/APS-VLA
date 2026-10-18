"""Read-only execution contract for the unchanged formal trainer.

The controller owns locking, transport, state, submission and original root review.
This module never loads weights, submits jobs, writes results, or repairs failures.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re

VERSION = "formal-autonomous-training-execution-v1"
SCHEMA = "formal_main_v2"
CONTROL_ROOT = Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
P = "/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA"
H = "/share/home/u15016/XXY_CVPR/CTI-VLA"
SOURCE = P + "/snapshots/formal_main_v2_run_564be0995e"
INVENTORY = "results/formal_main_v2/source/formal_main_v2_run_564be0995e.json"
INVENTORY_SHA = "5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926"
SOURCE_SHA = "dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e"
REGISTRATION = "configs/experiments/formal_main_v2.json"
REGISTRATION_SHA = "a3f35d8e96d701c1a9ebadc2ad02259372cf6c91da6c9cb8d57c231892cf6ff9"
AUTHORIZATION = "configs/experiments/formal_main_v2_autonomous_execution_authorization_v1.json"
AUTHORIZATION_SHA = "b709b1a822a6e07c583166496598566408c3fb012aeeadd315746ae817b4ab4d"
TARGET, SOFT_WALL, ALLOCATION_TIME = 5000, 169200, "48:00:00"
REVIEWER = "scripts/review_formal_segment.py"
DEPENDENCY_PINS = {
 "scripts/review_formal_segment.py": "566408f7f72bd3d878204175573a9c08b01db67be69358ed4a8ac2d0e0603790",
 "scripts/review_formal_acceptance.py": "373bcaea3ca8da63ee684ab8c3af6adcd329daa8fcc952422984882c0c206926",
 "scripts/ops/formal_asset_compat_review.py": "6ad55ddac4bfb692c72e3b1a9c37f41d6d831d7d03a2f2fbbde7f3c0dcf8f46b",
 "scripts/ops/formal_goal_component_review.py": "f220ff71084c460b1fb66d56d63e10f0256dc1fb98874fd0f6f916c293734871",
}
PAIR_RE = re.compile(r"(libero_10|libero_spatial|libero_object|libero_goal)_k(256|128|64)_seed(17|23|41)")
WEIGHT_SUFFIXES = {".pt", ".pth", ".bin", ".ckpt", ".safetensors", ".pkl", ".pickle", ".init", ".pruned_init"}
GATE_NAMES = ("input_acceptance.json", "resume_acceptance.json", "f03_calls.jsonl", "acceptance_complete.json")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            result.update(block)
    return result.hexdigest()


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def status(job):
    text = str(job.get("status", "")).strip()
    return text.split()[0].rstrip("+") if text else ""


def pair_id(pair):
    return f"{pair['suite']}_k{pair['visual_tokens']}_seed{pair['seed']}"


class Evidence:
    def __init__(self, root):
        self.root = Path(root)
        require(self.root == CONTROL_ROOT and self.root.resolve() == self.root, "wrong server control root")
        self.hashes = {}

    def path(self, name):
        require(isinstance(name, str) and name and "\\" not in name and "\0" not in name,
                "evidence path must be project-relative POSIX")
        p = PurePosixPath(name)
        require(not p.is_absolute() and all(x not in ("", ".", "..") for x in name.split("/")),
                "absolute/traversal evidence path")
        lower = name.lower()
        is_source = p.suffix in (".py", ".pyc", ".pyo")
        require(not ({x.lower() for x in p.suffixes} & WEIGHT_SUFFIXES) and
                not any(x.lower() in ("weights", "checkpoints", "sealed", "test") or "sealed" in x.lower() for x in p.parts)
                and (is_source or not any(x in lower for x in ("init_state", "initial_state", "final_state", "test_state"))),
                "weight/sealed/state evidence is forbidden")
        result = self.root / name
        require(result.resolve() == result and self.root in result.parents, "symlink or noncanonical evidence path")
        return result

    def watch(self, name, expected=None):
        value = sha(self.path(name))
        if expected is not None:
            require(value == expected, "evidence SHA differs: " + name)
        require(name not in self.hashes or self.hashes[name] == value, "evidence changed: " + name)
        self.hashes[name] = value
        return value

    def read(self, name, expected=None):
        self.watch(name, expected)
        return json.loads(self.path(name).read_bytes())

    def ref(self, ref):
        require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "exact path/SHA reference required")
        require(re.fullmatch("[0-9a-f]{64}", ref["sha256"] or ""), "invalid reference SHA")
        return self.read(ref["path"], ref["sha256"])

    def unchanged(self):
        for name, expected in self.hashes.items():
            require(sha(self.path(name)) == expected, "input changed during plan/review: " + name)


def context(e, key):
    require(PAIR_RE.fullmatch(key or ""), "unregistered pair identifier")
    auth = e.read(AUTHORIZATION, AUTHORIZATION_SHA)
    require(auth.get("pair_target_updates_per_arm") == TARGET and auth.get("soft_wall_seconds") == SOFT_WALL
            and auth.get("allocation_time") == ALLOCATION_TIME and auth.get("final_release_unchanged") is True,
            "execution authorization differs")
    inventory = e.read(INVENTORY, INVENTORY_SHA)
    require(len(inventory.get("files", {})) == 173 and inventory.get("source_root_server") == SOURCE
            and inventory.get("source_sha256") == SOURCE_SHA
            and hashlib.sha256(json.dumps(inventory["files"], sort_keys=True).encode()).hexdigest() == SOURCE_SHA,
            "frozen173 inventory differs")
    for name, digest in inventory["files"].items():
        e.watch(name, digest)
    for name, digest in DEPENDENCY_PINS.items():
        e.watch(name, digest)
    reg = e.read(REGISTRATION, REGISTRATION_SHA)
    require(auth.get("scientific_registration") == dict(path=REGISTRATION, sha256=REGISTRATION_SHA)
            and auth.get("source_inventory") == dict(path=INVENTORY, sha256=INVENTORY_SHA),
            "authorization does not bind scientific registration")
    matches = [x for x in reg["pairs"] if pair_id(x) == key]
    require(len(matches) == 1, "pair is not unique in registration")
    pair = matches[0]
    e.watch(pair["path"], pair["sha256"])
    return reg, pair, reg["suites"][pair["suite"]], inventory


def stage_key(pair):
    return f"{pair['suite']}_train_k{pair['visual_tokens']}_seed{pair['seed']}"


def pair_jobs(jobs, pair):
    rows = [j for j in jobs if j.get("experiment") == SCHEMA and j.get("stage_key") == stage_key(pair)]
    require(len({j["job_id"] for j in rows}) == len(rows), "duplicate registered pair job")
    for j in rows:
        require(j.get("mode") == "train" and j.get("suite") == pair["suite"]
                and j.get("visual_tokens") == pair["visual_tokens"] and j.get("training_seed") == pair["seed"]
                and j.get("source_root") == SOURCE and j.get("source_sha256") == SOURCE_SHA
                and j.get("gpus") == 1, "registered pair job identity differs")
    return sorted(rows, key=lambda j: (j["submitted_utc"], j["job_id"]))


def require_clean_history(rows):
    require(all(status(j) == "COMPLETED" and j.get("exit_code") == "0:0" for j in rows),
            "active, unknown, or failed allocation requires explicit separate review; no automatic retry")


def verify_rebuilt(saved, rebuilt):
    # The caller supplies the exact original reviewer result from the same
    # locked transaction, not a hand-written admission summary.
    ignored = {"status", "reviewed_utc", "reviewer_sha256", "evidence_sha256", "server_resume_checks"}
    require(rebuilt.get("status") in ("passed", "local_passed_remote_required"), "original raw reconstruction did not pass")
    require({k: v for k, v in saved.items() if k not in ignored} ==
            {k: v for k, v in rebuilt.items() if k not in ignored}, "saved and rebuilt original review differ")


def resume_checks(pair, review, actual, saved_checks=None):
    wanted = review.get("server_resume_checklist", [])
    saved = review.get("server_resume_checks", []) if saved_checks is None else saved_checks
    for rows in (wanted, saved, actual):
        require(isinstance(rows, list) and len(rows) == 2 and {x.get("arm") for x in rows} == {"A", "B"},
                "exact current A/B recovery existence and SHA proof required")
    result = []
    for arm in ("A", "B"):
        a, b, c = (next(x for x in rows if x["arm"] == arm) for rows in (wanted, saved, actual))
        path = pair["checkpoint_root_server"] + "/" + arm + "/resume.pt"
        require(a.get("path") == b.get("path") == c.get("path") == path, "recovery path differs")
        require(type(a.get("must_exist")) is bool and b.get("exists") == c.get("exists") == a["must_exist"],
                "recovery existence differs")
        if a["must_exist"]:
            require(re.fullmatch("[0-9a-f]{64}", a.get("sha256") or "")
                    and b.get("sha256") == c.get("sha256") == a["sha256"]
                    and type(b.get("bytes")) is int and b["bytes"] > 0
                    and c.get("bytes") == b["bytes"], "current recovery bytes differ")
        else:
            require(review["completed_by_arm"][arm] == 0 and a.get("sha256") is None
                    and not any(x.get("sha256") is not None for x in (b, c)),
                    "missing started arm recovery cannot be treated as fresh")
        result.append(copy.deepcopy(c))
    return result


def read_events(e, relative):
    e.watch(relative)
    raw = e.path(relative).read_bytes()
    require(raw and raw.endswith(b"\n"), "incomplete training journal")
    rows = [json.loads(line) for line in raw.splitlines()]
    require(all(isinstance(row, dict) for row in rows), "invalid journal row")
    return rows


def classify_terminal(root, *, pair_key, job, review_ref, rebuilt_review, actual_resume_checks):
    """Classify only AFTER the backend rebuilt the original scientific review.

    No state, transport or GPU file is read here. actual_resume_checks are fresh
    exact server hashes collected by the backend, never tensor deserialization.
    """
    if status(job) != "COMPLETED" or job.get("exit_code") != "0:0":
        return dict(decision="blocked", reason="abnormal_or_unknown_allocation", job_id=job.get("job_id"),
                    automatic_retry=False)
    e = Evidence(root)
    _, pair, _, _ = context(e, pair_key)
    document = e.ref(review_ref)
    machine = document.get("kind") == "automatic_machine_training_review"
    if machine:
        require(document.get("schema") == SCHEMA
                and document.get("version") == "autonomous-training-machine-review-v1"
                and document.get("status") == "passed_machine_reconstruction"
                and document.get("root_signature_claimed") is False
                and document.get("independent_review") is False
                and document.get("reviewer") == dict(path=REVIEWER, sha256=e.watch(REVIEWER)),
                "machine reconstruction must not impersonate root/independent review")
        review = document.get("original_review", {})
        require(review.get("status") == "local_passed_remote_required",
                "machine envelope must preserve original reviewer status")
        saved_checks = document.get("server_resume_checks", [])
    else:
        review = document
        require(review.get("status") == "passed" and review.get("reviewer_sha256") == e.watch(REVIEWER),
                "original root reviewer proof required")
        saved_checks = review.get("server_resume_checks", [])
    require(review.get("schema") == SCHEMA and review.get("kind") == "root_segment_review"
            and review.get("job_id") == job["job_id"], "latest original segment review required")
    require(review.get("suite") == pair["suite"] and review.get("visual_tokens") == pair["visual_tokens"]
            and review.get("seed") == pair["seed"] and review.get("source_sha256") == SOURCE_SHA,
            "review belongs to another pair/source")
    verify_rebuilt(review, rebuilt_review)
    histories = pair_jobs(review.get("registered_pair_jobs_at_review", []), pair)
    require(histories and histories[-1] == job, "latest registered job differs from original review")
    require_clean_history(histories)
    require(review.get("pair_allocated_gpu_seconds") == sum(j["elapsed_seconds"] * j["gpus"] for j in histories)
            and all(type(j["elapsed_seconds"]) is int and j["elapsed_seconds"] >= 0 for j in histories),
            "complete pair allocation bill differs")
    for name, digest in review.get("files", {}).items():
        e.watch(name, digest)
    require(review.get("files"), "original raw evidence file map missing")
    inv = e.read(job["invocation"], job["invocation_sha256"])
    require(inv.get("stage_key") == stage_key(pair) and inv.get("source_sha256") == SOURCE_SHA
            and review.get("invocation_sha256") == job["invocation_sha256"], "invocation/source mismatch")
    if "autonomous_execution" in inv:
        verify_execution_contract(e, inv)
        require(job.get("autonomous_execution") == inv["autonomous_execution"]
                and job.get("allocation_time") == ALLOCATION_TIME and job.get("soft_wall_seconds") == SOFT_WALL,
                "registered allocation execution contract differs")
    checks = resume_checks(pair, review, actual_resume_checks, saved_checks)
    completed = review.get("completed_by_arm", {})
    target = review.get("requested_segment_end")
    require(set(completed) == {"A", "B"} and type(target) is int and target in range(500, 5001, 500)
            and job.get("segment_end") == inv.get("segment_end") == target
            and all(type(x) is int and 0 <= x <= target for x in completed.values()), "invalid training boundary")
    out = f"results/{SCHEMA}/{pair['suite']}/k{pair['visual_tokens']}/seed{pair['seed']}/training"
    require(review["output_relative"] == out and job["run_root"] == P + "/" + out, "output identity differs")
    done = completed == {"A": 5000, "B": 5000}
    result_rel = out + ("/training_summary.json" if done else "/training_progress.json")
    require(result_rel in review["files"], "pair finalization not bound by root")
    result = e.read(result_rel)
    require(result.get("job_id") == job["job_id"] and result.get("pair_complete") == done
            and result.get("status") == ("completed" if done else "checkpointed"), "pair result mismatch")
    current_attempts, wall_stops, completed_a_current = 0, 0, False
    for arm in ("A", "B"):
        arm_report = result["arms"][arm]
        if arm_report.get("status") == "not_started":
            require(completed[arm] == 0 and next(x for x in checks if x["arm"] == arm)["exists"] is False,
                    "not-started arm has recovery evidence")
            continue
        report_rel = f"{out}/{arm}/" + ("training_report.json" if completed[arm] == 5000 else "progress_report.json")
        require(report_rel in review["files"] and e.read(report_rel) == arm_report, "arm/result bytes differ")
        require(arm_report.get("training_updates_completed") == completed[arm]
                and arm_report.get("next_sample_cursor") == completed[arm] * 8
                and arm_report.get("vla_parameters_unchanged") is True
                and [x["update"] for x in arm_report["evaluations"]] == list(range(0, completed[arm] + 1, 500)),
                "arm cursor/validation/frozen identity differs")
        own = []
        prefix = f"{out}/{arm}/attempts/"
        for name in review["files"]:
            if name.startswith(prefix) and name.endswith("/cost_events.jsonl"):
                rows = read_events(e, name)
                if any(r.get("job_id") == job["job_id"] for r in rows):
                    require(all(r.get("job_id") == job["job_id"] for r in rows), "mixed allocation journal")
                    own.append(rows)
        require(len(own) <= 1, "multiple training attempts in one allocation")
        if not own:
            # The unchanged runner legitimately skips already completed A, or
            # never enters B after A consumes the remaining soft wall.
            require(any(j["job_id"] != job["job_id"] for j in histories), "fresh arm has no attempt")
            require(completed[arm] == 5000 or (arm == "B" and (wall_stops or completed_a_current)),
                    "an unfinished arm was skipped without the original A-then-B wall boundary")
            continue
        current_attempts += 1
        rows = own[0]
        require(rows[0].get("event") == "attempt_start" and rows[-1].get("event") == "attempt_end"
                and rows[-1].get("status") == ("completed" if completed[arm] == 5000 else "checkpointed")
                and rows[-1].get("completed_update") == completed[arm], "unclean attempt lifecycle")
        commits = [r for r in rows if r.get("event") == "checkpoint_commit"]
        require(commits and commits[-1].get("completed_update") == completed[arm]
                and commits[-1].get("resume_sha256") == next(x for x in checks if x["arm"] == arm)["sha256"],
                "last committed update differs from current recovery")
        if arm == "A" and completed[arm] == 5000:
            completed_a_current = True
        if completed[arm] < 5000:
            reason = arm_report.get("stop_reason")
            if reason == "engineering_wall_limit_after_complete_update":
                wall_stops += 1
            else:
                require(target < 5000 and completed[arm] == target
                        and reason == "registered_engineering_segment_boundary", "unexplained normal stop")
    require(current_attempts > 0, "allocation performed no verifiable training attempt")
    if done:
        require(review.get("allowed_next_segment_end") is None
                and len(review.get("completed_training_receipts", [])) == 2, "final5000 cannot continue")
        decision, reason = "complete", "both_arms5000_original_final_receipts"
    elif target == 5000:
        contract = verify_execution_contract(e, inv)
        # If A completes at the time limit, the unchanged outer runner can
        # stop before entering B; its wall receipt plus skipped B and completed
        # current A establish this specific branch, not an arbitrary stop.
        outer_wall = False
        if not wall_stops and completed_a_current and completed["B"] < 5000:
            receipt_rel = f"results/{SCHEMA}/job_receipts/{job['job_id']}.json"
            require(receipt_rel in review["files"], "allocation wall receipt missing")
            receipt = e.read(receipt_rel)
            outer_wall = type(receipt.get("wall_seconds")) in (int, float) and math.isfinite(receipt["wall_seconds"]) and receipt["wall_seconds"] >= SOFT_WALL
        require(wall_stops > 0 or outer_wall, "target5000 partial needs clean softwall evidence")
        require(all(completed[a] >= contract["completed_before"][a] for a in ("A", "B")),
                "autonomous invocation regressed a committed arm")
        decision, reason = "ready", "clean_softwall_resume_same5000_target"
    else:
        require(all(value == target for value in completed.values()) or wall_stops > 0,
                "legacy partial boundary lacks a clean engineering exit")
        decision, reason = "ready", "migrate_reviewed_legacy_boundary_to5000"
    e.unchanged()
    return dict(schema=SCHEMA, kind="autonomous_training_admission", version=VERSION, decision=decision,
                reason=reason, pair_key=pair_key, mode="resume", job_id=job["job_id"], review_ref=review_ref,
                completed_by_arm=completed, next_target=5000 if decision == "ready" else None,
                server_resume_checks=checks, pair_allocated_gpu_seconds=review["pair_allocated_gpu_seconds"],
                original_raw_review_reconstructed=True,
                verification_origin="automatic_machine_reconstruction" if machine else "existing_root_review_reconstructed",
                root_signature_claimed=False, independent_review=False, evidence_sha256=e.hashes)


def _gate(e, pair, jobs, admission):
    path = f"results/{SCHEMA}/{pair['suite']}/acceptance/root_review.json"
    gate = e.read(path)
    require(gate.get("schema") == SCHEMA and gate.get("kind") == "root_acceptance_review"
            and gate.get("status") == "passed" and gate.get("suite") == pair["suite"]
            and gate.get("source_sha256") == SOURCE_SHA, "own suite original GPU acceptance required")
    accepted = [j for j in jobs if j.get("job_id") == gate.get("job_id") and j.get("experiment") == SCHEMA]
    require(len(accepted) == 1 and status(accepted[0]) == "COMPLETED" and accepted[0].get("exit_code") == "0:0"
            and accepted[0].get("suite") == pair["suite"] and accepted[0].get("mode") == "acceptance",
            "registered suite acceptance allocation missing")
    for name, digest in gate["files"].items():
        e.watch(gate["output_relative"] + "/" + name, digest)
    for field, present in (("runtime_compatibility", pair["suite"] in ("libero_object", "libero_goal")),
                           ("component_compatibility", pair["suite"] == "libero_goal")):
        require((field in gate) == present and (field in accepted[0]) == present, "suite compatibility scope differs")
        if present:
            value = gate[field]
            require(value == accepted[0][field], "acceptance compatibility identity differs")
            expected_count = 6 if field == "runtime_compatibility" else 4
            require(len(value.get("files", {})) == expected_count, "compatibility file count differs")
            for name, digest in value["files"].items():
                e.watch(name, digest)
            proof = gate.get(field + "_review", {})
            require(proof.get("status") == "verified" and proof.get(field) == value, "compatibility root proof missing")
            for name, digest in proof.get("evidence_sha256", {}).items():
                e.watch(name, digest)
    if admission.get("mode") == "fresh":
        require(admission.get("acceptance_review_ref") == dict(path=path, sha256=e.watch(path)),
                "fresh admission acceptance ref differs")
        rebuilt = admission.get("rebuilt_acceptance")
        require(isinstance(rebuilt, dict), "fresh admission must carry original rebuilt acceptance")
        ignored = {"reviewed_utc", "evidence_sha256"}
        require({k: v for k, v in gate.items() if k not in ignored} ==
                {k: v for k, v in rebuilt.items() if k not in ignored}, "rebuilt acceptance differs")
    return gate


def build_base_invocation(root, *, pair_key, source_inventory, jobs, admission, registered_utc):
    """Pure assembler. Does not read state, check live Slurm, or create paths.

    Caller holds the project writer lock and has just refreshed all registered
    jobs. Fresh admission includes the original rebuilt acceptance result.
    Resume admission must come from classify_terminal in that transaction.
    """
    e = Evidence(root)
    require(source_inventory == dict(path=INVENTORY, sha256=INVENTORY_SHA), "source inventory pin differs")
    reg, pair, suite, inventory = context(e, pair_key)
    histories = pair_jobs(jobs, pair)
    require_clean_history(histories)
    require(admission.get("decision") == "ready" and admission.get("pair_key") == pair_key, "pair not admitted")
    require(admission.get("mode") == ("resume" if histories else "fresh"), "fresh/resume mode differs")
    require(isinstance(registered_utc, str) and registered_utc.endswith(("+00:00", "Z")), "UTC registration required")
    if histories:
        require(admission.get("schema") == SCHEMA and admission.get("kind") == "autonomous_training_admission"
                and admission.get("version") == VERSION and admission.get("job_id") == histories[-1]["job_id"]
                and admission.get("original_raw_review_reconstructed") is True and admission.get("next_target") == 5000,
                "latest reconstructed resume admission required")
        for name, digest in admission.get("evidence_sha256", {}).items():
            e.watch(name, digest)
        require(admission.get("evidence_sha256"), "resume evidence map missing")
    gate = _gate(e, pair, jobs, admission)
    outrel = f"results/{SCHEMA}/{pair['suite']}/k{pair['visual_tokens']}/seed{pair['seed']}/training"
    require(not e.path(outrel + "/training_summary.json").exists(), "pair already finalized5000")
    if not histories:
        require(not e.path(outrel).exists(), "unregistered existing training output; never fresh-reset")
    watched = {}
    def watch(rel, server=None):
        watched[server or P + "/" + rel] = e.watch(rel)
    for rel in (suite["protocol"], suite["windows"]):
        watch(rel)
    watch(suite["model_manifest"], SOURCE + "/" + suite["model_manifest"])
    watch(pair["path"], SOURCE + "/" + pair["path"])
    for name in (*GATE_NAMES, f"f01_k{pair['visual_tokens']}.json"):
        watch(gate["output_relative"] + "/" + name)
    common = ["--protocol", P + "/" + suite["protocol"], "--windows", P + "/" + suite["windows"],
              "--checkpoint", suite["model_root_server"], "--asset-manifest", SOURCE + "/" + suite["model_manifest"],
              "--data-directory", suite["data_root_server"], "--cache-directory", P + "/.local/formal-hf-" + pair["suite"],
              "--feature-cache", suite["cache_root_server"]]
    argv = ["--config", SOURCE + "/" + pair["path"], *common, "--training-checkpoints", pair["checkpoint_root_server"],
            "--input-acceptance-report", P + "/" + gate["output_relative"] + "/input_acceptance.json",
            "--acceptance-report", P + "/" + gate["output_relative"] + f"/f01_k{pair['visual_tokens']}.json",
            "--output", P + "/" + outrel, "--arm", "both", "--stop-after-updates", "500", "--max-wall-seconds", "12600"]
    previous = None
    if histories:
        latest = histories[-1]
        previous = e.read(latest["invocation"], latest["invocation_sha256"])
        require(previous.get("source_root") == SOURCE and previous.get("source_sha256") == SOURCE_SHA
                and previous.get("entrypoint") == "scripts/run_formal_future.py"
                and previous.get("watched_files") == watched
                and previous.get("stage_key") == stage_key(pair), "previous science/source/gate identity differs")
        raw = previous["argv"]
        values = raw[:-1] if raw[-1:] == ["--resume"] else raw
        require(len(values) % 2 == 0 and len(set(values[::2])) == len(values[::2]), "invalid previous argv")
        old = dict(zip(values[::2], values[1::2]))
        expected = dict(zip(argv[::2], argv[1::2]))
        for key in ("--stop-after-updates", "--max-wall-seconds"):
            expected[key] = old.get(key)
        require(old == expected and old["--stop-after-updates"] == str(latest["segment_end"])
                and math.isfinite(float(old["--max-wall-seconds"])) and float(old["--max-wall-seconds"]) > 0,
                "previous invocation changed scientific inputs")
        argv = list(values) + ["--resume"]
    invocation = dict(schema=SCHEMA, stage="train", stage_key=stage_key(pair), suite=pair["suite"],
        source_root=SOURCE, source_sha256=SOURCE_SHA, entrypoint="scripts/run_formal_future.py",
        argv=argv, watched_files=watched, registered_utc=registered_utc, registration_sha256=REGISTRATION_SHA,
        segment_end=int(argv[argv.index("--stop-after-updates") + 1]), repair_record=None)
    for field in ("runtime_compatibility", "component_compatibility"):
        if field in gate:
            invocation[field] = copy.deepcopy(gate[field])
        if previous is not None:
            require(previous.get(field) == invocation.get(field), "previous runtime compatibility changed")
    if pair["suite"] == "libero_goal":
        wrapper_rel = "scripts/server/formal_goal_asset_main.slurm"
    elif pair["suite"] == "libero_object":
        wrapper_rel = "scripts/server/formal_asset_main.slurm"
    else:
        wrapper_rel = "scripts/server/formal_main.slurm"
    wrapper = (SOURCE if pair["suite"] in ("libero_10", "libero_spatial") else P) + "/" + wrapper_rel
    wrapper_sha = e.watch(wrapper_rel)
    if pair["suite"] in ("libero_10", "libero_spatial"):
        require(wrapper_sha == inventory["files"][wrapper_rel], "original wrapper changed")
    else:
        field = "component_compatibility" if pair["suite"] == "libero_goal" else "runtime_compatibility"
        require(invocation[field]["files"].get(wrapper_rel) == wrapper_sha, "registered compatibility wrapper changed")
    invrel = f"results/{SCHEMA}/invocations/{stage_key(pair)}_attempt{len(histories)+1:02d}.json"
    require(not e.path(invrel).exists(), "invocation already exists; resolve unknown outcome")
    e.unchanged()
    return dict(pair_key=pair_key, pair=copy.deepcopy(pair), invocation=invocation, invocation_relative=invrel,
        wrapper=wrapper, wrapper_sha256=wrapper_sha, source_inventory=source_inventory,
        prior_job_ids=[j["job_id"] for j in histories], output=P + "/" + outrel,
        server_resume_checks=copy.deepcopy(admission.get("server_resume_checks", [])),
        completed_before=copy.deepcopy(admission.get("completed_by_arm", {"A": 0, "B": 0})),
        predecessor_review=copy.deepcopy(admission.get("review_ref")),
        acceptance_review=dict(path=f"results/{SCHEMA}/{pair['suite']}/acceptance/root_review.json",
                               sha256=e.watch(f"results/{SCHEMA}/{pair['suite']}/acceptance/root_review.json")),
        preflight=dict(require_no_training_summary=P + "/" + outrel + "/training_summary.json",
                       require_absent_if_fresh=[] if histories else [P + "/" + outrel, pair["checkpoint_root_server"]]),
        evidence_sha256=e.hashes)


def verify_execution_contract(e, invocation):
    c = invocation.get("autonomous_execution", {})
    expected = dict(schema=SCHEMA, kind="autonomous_training_execution", version=VERSION,
        authorization=dict(path=AUTHORIZATION, sha256=AUTHORIZATION_SHA),
        source_inventory=dict(path=INVENTORY, sha256=INVENTORY_SHA),
        target_updates_per_arm=TARGET, soft_wall_seconds=SOFT_WALL, allocation_time=ALLOCATION_TIME,
        original_sequential_A_B=True, scientific_source_unchanged=True, scientific_argv_unchanged=True,
        validation_updates=list(range(0, 5001, 500)), checkpoint_every_updates=50,
        failed_unknown_or_signal_terminated_auto_retry=False)
    require(all(c.get(k) == v for k, v in expected.items()), "autonomous execution contract differs")
    ref = c.get("adapter", {})
    require(set(ref) == {"path", "sha256"} and ref["sha256"] == sha(Path(__file__)),
            "autonomous adapter identity differs")
    e.watch(ref["path"], ref["sha256"])
    base = copy.deepcopy(invocation)
    del base["autonomous_execution"]
    changes = c.get("changed_options", {})
    require(set(changes) == {"--stop-after-updates", "--max-wall-seconds"}, "unexpected changed argument")
    for flag, after in (("--stop-after-updates", "5000"), ("--max-wall-seconds", str(SOFT_WALL))):
        require(base["argv"].count(flag) == 1 and changes[flag].get("after") == after,
                "autonomous option identity differs")
        index = base["argv"].index(flag) + 1
        require(base["argv"][index] == after and isinstance(changes[flag].get("before"), str),
                "actual argv differs from execution contract")
        base["argv"][index] = changes[flag]["before"]
    base["segment_end"] = int(changes["--stop-after-updates"]["before"])
    require(signature(base) == c.get("base_invocation_sha256"), "original invocation provenance differs")
    require(set(c.get("completed_before", {})) == {"A", "B"} and
            all(type(v) is int and 0 <= v <= 5000 for v in c["completed_before"].values()),
            "invalid admitted starting update")
    return c


def build_execution(root, base_plan, *, adapter_ref):
    """Return the only changed allocation contract; controller must register it."""
    e = Evidence(root)
    require(e.watch(AUTHORIZATION, AUTHORIZATION_SHA) == AUTHORIZATION_SHA, "authorization mismatch")
    require(isinstance(adapter_ref, dict) and set(adapter_ref) == {"path", "sha256"}
            and adapter_ref["sha256"] == sha(Path(__file__)), "execution adapter identity differs")
    e.watch(adapter_ref["path"], adapter_ref["sha256"])
    for name, digest in base_plan["evidence_sha256"].items():
        e.watch(name, digest)
    result = copy.deepcopy(base_plan)
    invocation = result["invocation"]
    require("autonomous_execution" not in invocation and invocation["stage"] == "train"
            and invocation["entrypoint"] == "scripts/run_formal_future.py"
            and invocation["repair_record"] is None, "invalid base invocation")
    original = copy.deepcopy(invocation)
    for flag, value in (("--stop-after-updates", str(TARGET)), ("--max-wall-seconds", str(SOFT_WALL))):
        require(invocation["argv"].count(flag) == 1, "duplicate/missing execution argument")
        invocation["argv"][invocation["argv"].index(flag) + 1] = value
    invocation["segment_end"] = TARGET
    contract = dict(schema=SCHEMA, kind="autonomous_training_execution", version=VERSION,
        authorization=dict(path=AUTHORIZATION, sha256=AUTHORIZATION_SHA), adapter=adapter_ref,
        base_invocation_sha256=signature(original), source_inventory=result["source_inventory"],
        original_wrapper=dict(path=result["wrapper"], sha256=result["wrapper_sha256"]),
        target_updates_per_arm=TARGET, soft_wall_seconds=SOFT_WALL, allocation_time=ALLOCATION_TIME,
        original_sequential_A_B=True, scientific_source_unchanged=True, scientific_argv_unchanged=True,
        validation_updates=list(range(0, 5001, 500)), checkpoint_every_updates=50,
        changed_options={"--stop-after-updates": {"before": original["argv"][original["argv"].index("--stop-after-updates")+1], "after": "5000"},
                         "--max-wall-seconds": {"before": original["argv"][original["argv"].index("--max-wall-seconds")+1], "after": str(SOFT_WALL)}},
        predecessor_review=result["predecessor_review"], acceptance_review=result["acceptance_review"],
        completed_before=result["completed_before"], resume_checks_before=result["server_resume_checks"],
        failed_unknown_or_signal_terminated_auto_retry=False)
    invocation["autonomous_execution"] = contract
    result.update(sbatch_options=["--time=" + ALLOCATION_TIME], target_updates_per_arm=TARGET,
                  allocation_seconds=172800, soft_wall_seconds=SOFT_WALL,
                  execution_contract=contract, evidence_sha256=e.hashes,
                  requires_root_activation=True, submits_jobs=False)
    e.unchanged()
    return result

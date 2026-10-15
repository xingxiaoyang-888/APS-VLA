"""Build formal execution/freeze receipts from non-weight evidence only.

This root-side tool never opens a checkpoint or sealed_final.json, never calls
Slurm, and never infers checkpoint existence from its server path. The frozen
server evaluation entrypoint still verifies actual checkpoint bytes before
inference. Final release is a separate, explicit --release operation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
P = PurePosixPath("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
H = PurePosixPath("/share/home/u15016/XXY_CVPR/CTI-VLA")
SCHEMA = "formal_main_v2"
REGISTRATION = "configs/experiments/formal_main_v2.json"
WEIGHT_SUFFIXES = {".pt", ".pth", ".bin", ".safetensors", ".ckpt"}
SUITES = ("libero_spatial", "libero_object", "libero_goal", "libero_10")
BUDGETS, SEEDS = (256, 128, 64), (17, 23, 41)
CHECKPOINT_INVENTORY_MAX_AGE_SECONDS = 3600
PRODUCER_ENTRYPOINTS = {"scripts/" + name for name in (
    "run_formal_future.py", "verify_formal_acceptance.py", "eval_formal_selector_libero.py", "verify_long_inputs.py")}


class MissingEvidence(ValueError):
    def __init__(self, missing):
        self.missing = sorted(set(str(p) for p in missing))
        super().__init__("Required evidence is missing: " + ", ".join(self.missing))


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def canonical_signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            value.update(block)
    return value.hexdigest()


def immutable_write(path, value):
    """Exclusive immutable artifact; interrupted partial files stay identifiable."""
    path = Path(path)
    content = encoded(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError("Refuse to overwrite a different frozen artifact: " + str(path))
        return
    temporary = path.with_name(path.name + ".partial")
    with temporary.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    # Hard-link publication is exclusive on both Windows and POSIX; unlike
    # replace(), it cannot overwrite another concurrent root writer's receipt.
    try:
        os.link(temporary, path)
    except FileExistsError:
        if path.read_bytes() != content:
            raise ValueError("Concurrent frozen artifact differs: " + str(path))
    else:
        temporary.unlink()


class Evidence:
    def __init__(self, project):
        self.project = Path(project).resolve()
        self.files = {}

    def path(self, value):
        path = Path(value)
        path = (self.project / path).resolve() if not path.is_absolute() else path.resolve()
        if self.project not in path.parents:
            raise ValueError("Metadata must remain inside CTI-VLA: " + str(value))
        if path.suffix.lower() in WEIGHT_SUFFIXES or "sealed_final" in path.name.lower():
            raise ValueError("This tool cannot access weights or sealed final values: " + str(value))
        return path

    def relative(self, path):
        return self.path(path).relative_to(self.project).as_posix()

    def require(self, paths):
        checked = [self.path(path) for path in paths]
        missing = [p.relative_to(self.project).as_posix() for p in checked if not p.is_file()]
        if missing:
            raise MissingEvidence(missing)

    def watch(self, value):
        path = self.path(value)
        self.require([path])
        checksum = digest(path)
        key = self.relative(path)
        if key in self.files and self.files[key] != checksum:
            raise ValueError("Evidence changed during this audit: " + key)
        self.files[key] = checksum
        return checksum

    def read(self, value):
        path = self.path(value)
        self.watch(path)
        return json.loads(path.read_text(encoding="utf-8"))

    def unchanged(self):
        for relative, checksum in self.files.items():
            if digest(self.path(relative)) != checksum:
                raise ValueError("Evidence changed during this audit: " + relative)


def source_contract(evidence, inventory_path):
    from cti_vla.training.formal_future import formal_source_hashes
    inventory = evidence.read(inventory_path)
    files = inventory.get("files", {})
    expected = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    if (inventory.get("schema") != SCHEMA or expected != inventory.get("source_sha256")
            or not inventory.get("source_root_server", "").startswith(str(P / "snapshots/formal_main_v2_run_"))):
        raise ValueError("Not the registered immutable formal GPU source inventory")
    current = formal_source_hashes(evidence.project)
    if any(files.get(name) != checksum for name, checksum in current.items()):
        raise ValueError("Local frozen producer modules differ from the GPU source inventory")
    for name in current:
        evidence.watch(name)
    for name, checksum in files.items():
        if name == REGISTRATION or name.startswith(("configs/experiments/formal_main_v2/", "configs/assets/")):
            if evidence.watch(name) != checksum:
                raise ValueError("Registered configuration/asset changed after GPU source freeze: " + name)
    return current


def registration_contract(evidence, path):
    registration = evidence.read(path)
    expected = {(s, k, seed) for s in SUITES for k in BUDGETS for seed in SEEDS}
    rows = registration.get("pairs", [])
    if (registration.get("schema") != SCHEMA or set(registration.get("suites", {})) != set(SUITES)
            or len(rows) != 36 or {(r["suite"], r["visual_tokens"], r["seed"]) for r in rows} != expected):
        raise ValueError("Formal registration must contain all36 A/B pairs and four suites")
    for row in rows:
        relative = f"results/{SCHEMA}/{row['suite']}/k{row['visual_tokens']}/seed{row['seed']}"
        if (row["run_root_server"] != str(P / relative)
                or row["checkpoint_root_server"] != str(H / f"checkpoints/{SCHEMA}/{row['suite']}/k{row['visual_tokens']}/seed{row['seed']}")):
            raise ValueError("Pair output/checkpoint server path is not the registered suite/budget/seed")
        pair = evidence.read(row["path"])
        if (evidence.watch(row["path"]) != row["sha256"]
                or (pair.get("suite"), 2 * pair.get("tokens_per_camera", 0), pair.get("seed"))
                    != (row["suite"], row["visual_tokens"], row["seed"])):
            raise ValueError("Registered pair bytes or suite/budget/seed changed")
    return registration


def checkpoint_specs(registration):
    return [dict(suite=pair["suite"], visual_tokens=pair["visual_tokens"], training_seed=pair["seed"], method=arm,
        method_id=f"{arm}{pair['visual_tokens']}_seed{pair['seed']}",
        checkpoint=str(PurePosixPath(pair["checkpoint_root_server"]) / arm / "best.pt"))
        for pair in registration["pairs"] for arm in ("A", "B")]


def hash_checkpoint_paths(paths, *, allowed_root):
    """Server checker primitive; callers supply only the72 registered best paths."""
    allowed = Path(allowed_root).resolve()
    missing = []
    for path in paths:
        path = Path(path)
        if allowed not in path.resolve().parents or path.is_symlink():
            raise ValueError("Checkpoint path escapes its registered server tree or is a symlink")
        if not path.is_file():
            missing.append(str(path))
    if missing:
        raise MissingEvidence(missing)
    rows = []
    for path in paths:
        path = Path(path)
        before = path.stat()
        checksum = digest(path)
        after = path.stat()
        if before.st_size <= 0 or (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise ValueError("Checkpoint changed or was empty during server hashing: " + str(path))
        rows.append(dict(exists=True, bytes=after.st_size, checkpoint_sha256=checksum,
            mtime_ns_before=before.st_mtime_ns, mtime_ns_after=after.st_mtime_ns, stable_during_hash=True))
    return rows


def server_checkpoint_inventory(evidence, registration, source_inventory, output):
    """CPU-only server path: no VLA imports, torch loading, Slurm, or sealed data."""
    if sys.platform != "linux" or evidence.project != Path(str(P)).resolve():
        raise ValueError("Checkpoint byte verification is server-only at the exact registered P project; local mode is metadata-only")
    if registration_contract(evidence, REGISTRATION) != registration:
        raise ValueError("Server checker received a different registration than the on-disk frozen matrix")
    info = evidence.read(source_inventory)
    files = info.get("files", {})
    inventory_sha = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    source = PurePosixPath(info.get("source_root_server", ""))
    if (info.get("schema") != SCHEMA or info.get("source_sha256") != inventory_sha
            or source.parent != P / "snapshots" or not source.name.startswith("formal_main_v2_run_")):
        raise ValueError("Server checker requires the immutable formal GPU producer inventory")
    actual = evidence.read(str(source / "source_manifest.json"))
    if actual != info:
        raise ValueError("Server source manifest differs from the copied root inventory")
    for relative, checksum in files.items():
        if evidence.watch(str(source / relative)) != checksum:
            raise ValueError("Frozen server source changed: " + relative)
    for relative in [REGISTRATION, *[pair["path"] for pair in registration["pairs"]]]:
        if files.get(relative) != evidence.watch(relative):
            raise ValueError("Server registered configuration differs from its frozen source inventory")
    specs = checkpoint_specs(registration)
    if len(specs) != 72 or len({r["checkpoint"] for r in specs}) != 72:
        raise ValueError("Server checker accepts exactly72 distinct registered final best checkpoints")
    measurements = hash_checkpoint_paths([row["checkpoint"] for row in specs],
        allowed_root=Path(str(H / "checkpoints/formal_main_v2")))
    producer_files = {name: checksum for name, checksum in files.items()
        if (name.startswith("src/") and name.endswith(".py")) or name in PRODUCER_ENTRYPOINTS}
    evidence.unchanged()
    report = dict(schema=SCHEMA, kind="server_checkpoint_inventory", status="verified",
        execution="linux_server_cpu_read_only_hash", created_utc=datetime.now(timezone.utc).isoformat(),
        server_project_root=str(P), hostname=socket.gethostname(), gpu_used=False, test_opened=False,
        registration_sha256=canonical_signature(registration), registration_file_sha256=evidence.watch(REGISTRATION),
        source_inventory=evidence.relative(source_inventory), source_inventory_file_sha256=evidence.watch(source_inventory),
        source_sha256=inventory_sha, source_root_server=str(source), source_files_sha256=canonical_signature(producer_files),
        checker_source_sha256=digest(__file__), required_checkpoints=72,
        checkpoints=[{**spec, **measurement} for spec, measurement in zip(specs, measurements)],
        scope="Only registered72 A/B best.pt bytes; no resume/engineering weights or sealed states accessed")
    immutable_write(evidence.path(output), report)
    return dict(status="server_checkpoint_inventory_written", output=output, checkpoints=72, gpu_used=False, test_opened=False)


def validate_checkpoint_inventory(evidence, path, registration, sources, identities, *, require_fresh=True):
    report = evidence.read(path)
    info = evidence.read(report["source_inventory"])
    producer_root = PurePosixPath(info.get("source_root_server", ""))
    expected_source_sha = hashlib.sha256(json.dumps(info.get("files", {}), sort_keys=True).encode()).hexdigest()
    expected = dict(schema=SCHEMA, kind="server_checkpoint_inventory", status="verified",
        execution="linux_server_cpu_read_only_hash", server_project_root=str(P), gpu_used=False, test_opened=False,
        registration_sha256=canonical_signature(registration), registration_file_sha256=evidence.watch(REGISTRATION),
        source_inventory_file_sha256=evidence.watch(report["source_inventory"]), source_sha256=expected_source_sha,
        source_root_server=info.get("source_root_server"), source_files_sha256=canonical_signature(sources),
        checker_source_sha256=digest(__file__), required_checkpoints=72)
    if (any(report.get(k) != v for k, v in expected.items()) or info.get("schema") != SCHEMA
            or producer_root.parent != P / "snapshots" or not producer_root.name.startswith("formal_main_v2_run_")
            or info.get("source_sha256") != expected_source_sha
            or any(info.get("files", {}).get(name) != checksum for name, checksum in sources.items())
            or any(info.get("files", {}).get(name) != evidence.watch(name)
                for name in [REGISTRATION, *[pair["path"] for pair in registration["pairs"]]])):
        raise ValueError("Server checkpoint inventory has another source/configuration/checker identity")
    recorded = datetime.fromisoformat(report["created_utc"])
    if recorded.tzinfo is None:
        raise ValueError("Server checkpoint inventory timestamp requires a timezone")
    age = (datetime.now(timezone.utc) - recorded).total_seconds()
    if require_fresh and not -120 <= age <= CHECKPOINT_INVENTORY_MAX_AGE_SECONDS:
        raise ValueError("Server checkpoint inventory is stale; obtain a new server-only hash receipt within one hour of freeze")
    specs = {(row["suite"], row["method_id"]): row for row in checkpoint_specs(registration)}
    selected = {(row["suite"], row["method_id"]): row for row in identities if row["method"] in ("A", "B")}
    rows = report.get("checkpoints", [])
    if len(rows) != 72 or len({(row.get("suite"), row.get("method_id")) for row in rows}) != 72 or set(selected) != set(specs):
        raise ValueError("Server checkpoint inventory must cover all72 selected identities exactly once")
    for row in rows:
        key = row["suite"], row["method_id"]
        if (key not in specs or any(row.get(k) != v for k, v in specs[key].items())
                or row.get("exists") is not True or row.get("stable_during_hash") is not True
                or type(row.get("bytes")) is not int or row["bytes"] <= 0
                or type(row.get("mtime_ns_before")) is not int or row["mtime_ns_before"] != row.get("mtime_ns_after")
                or row.get("checkpoint_sha256") != selected[key]["checkpoint_sha256"]):
            raise ValueError("Server checkpoint is missing, changed, or not the exact frozen best checkpoint")
    return report


def load_suite_acceptance(evidence, registration, suite, sources):
    from cti_vla.evaluation.formal_acceptance import (select_formal_acceptance_windows,
        require_formal_input_acceptance, require_formal_acceptance, verify_formal_operator_journal)
    from cti_vla.evaluation.future_input_acceptance import verify_input_acceptance_journal
    from cti_vla.evaluation.formal_runtime import FORMAL_BUDGETS
    from cti_vla.training.formal_resume_acceptance import require_formal_resume_acceptance, verify_resume_journal
    spec = registration["suites"][suite]
    review = evidence.read(f"results/{SCHEMA}/{suite}/acceptance/root_review.json")
    base = evidence.path(review["output_relative"])
    expected_parent = evidence.path(f"results/{SCHEMA}/{suite}/acceptance")
    if (review.get("status") != "passed" or expected_parent not in base.parents
            or not str(review.get("job_id", "")).isdigit()):
        raise ValueError("Suite acceptance must have an explicit root review of its own attempt")
    names = ["input_acceptance.json", "input_calls.jsonl", "operator_calls.jsonl", "resume_acceptance.json",
        "f03_calls.jsonl", "acceptance_complete.json", *[f"f01_k{k}.json" for k in FORMAL_BUDGETS]]
    evidence.require([base / name for name in names])
    for name, checksum in review.get("files", {}).items():
        if evidence.watch(base / name) != checksum:
            raise ValueError("Acceptance file differs from its root review: " + name)
    for name in ("input_acceptance.json", "resume_acceptance.json", "f03_calls.jsonl", "acceptance_complete.json",
            *[f"f01_k{k}.json" for k in FORMAL_BUDGETS]):
        if name not in review.get("files", {}):
            raise ValueError("Root review is missing an engineering receipt hash: " + name)
    protocol, windows = evidence.read(spec["protocol"]), evidence.read(spec["windows"])
    # Signed protocol payload fields live at the top level.
    fixed = select_formal_acceptance_windows(windows, protocol)
    primary_entry = next(p for p in registration["pairs"] if (p["suite"], p["visual_tokens"], p["seed"]) == (suite, 128, 17))
    primary = evidence.read(primary_entry["path"])
    asset_sha = evidence.watch(spec["model_manifest"])
    if asset_sha != spec["model_manifest_sha256"] or primary["model_revision"] != spec["model_revision"]:
        raise ValueError("Suite official asset identity changed")
    f00_path = base / "input_acceptance.json"
    f00, complete = evidence.read(f00_path), evidence.read(base / "acceptance_complete.json")
    shared = dict(window_manifest_sha256=evidence.watch(spec["windows"]), source_files=sources)
    require_formal_input_acceptance(f00, config=primary, **shared, selected_windows=fixed,
        data_protocol_sha256=evidence.watch(spec["protocol"]), asset_manifest_sha256=asset_sha)
    verify_input_acceptance_journal(base / "input_calls.jsonl", f00)
    f00_sha = evidence.watch(f00_path)
    f01s = {}
    for budget in FORMAL_BUDGETS:
        path = base / f"f01_k{budget}.json"
        f01 = evidence.read(path)
        pair = next(p for p in registration["pairs"] if (p["suite"], p["visual_tokens"], p["seed"]) == (suite, budget, 17))
        require_formal_acceptance(f01, config=evidence.read(pair["path"]), **shared,
            input_acceptance_sha256=f00_sha, selected_windows=fixed)
        verify_formal_operator_journal(base / "operator_calls.jsonl", f01)
        if f01["frozen_model_sha256"] != f00["frozen_model_sha256"]:
            raise ValueError("Suite F00/F01 frozen model mismatch")
        f01s[budget] = path
    resume_path, resume_journal = base / "resume_acceptance.json", base / "f03_calls.jsonl"
    resume = evidence.read(resume_path)
    require_formal_resume_acceptance(resume, config=primary, **shared, input_acceptance_sha256=f00_sha,
        selected_windows=fixed[:2], frozen_model_sha256=f00["frozen_model_sha256"])
    verify_resume_journal(resume_journal, resume)
    expected = dict(schema=SCHEMA, status="passed", suite=suite, job_id=str(review["job_id"]),
        input_acceptance_sha256=f00_sha, source_files=sources, frozen_model_sha256=f00["frozen_model_sha256"],
        checkpoint_unchanged=True, test_opened=False, resume_acceptance_passed=True,
        resume_acceptance_sha256=evidence.watch(resume_path), f03_calls_sha256=evidence.watch(resume_journal),
        input_calls=6, operator_probes=63, operator_calls_sha256=evidence.watch(base / "operator_calls.jsonl"))
    if any(complete.get(k) != v for k, v in expected.items()):
        raise ValueError("Suite acceptance completion does not bind all F00/F01/F03 evidence")
    if {r["visual_tokens"]: r["sha256"] for r in complete.get("operator_acceptances", [])} != {
            budget: evidence.watch(path) for budget, path in f01s.items()}:
        raise ValueError("Suite engineering completion omits or changes a trained budget")
    for name in names:
        evidence.watch(base / name)
    return dict(f00=f00, f00_path=f00_path, f00_sha=f00_sha, f01s=f01s,
        resume_sha=evidence.watch(resume_path), resume_journal_sha=evidence.watch(resume_journal),
        window_sha=shared["window_manifest_sha256"], protocol_sha=evidence.watch(spec["protocol"]))


def pair_directory(evidence, pair):
    return evidence.path(PurePosixPath(pair["run_root_server"]).relative_to(P).as_posix() + "/training")


def selected_pair(evidence, pair_entry, gate, sources):
    """Validate both complete arms and reconstruct identities without weights."""
    from cti_vla.evaluation.formal_runtime import formal_metadata, validate_formal_receipt, validate_formal_pair
    from cti_vla.evaluation.formal_trials import selector_instance_identity
    from cti_vla.evaluation.teacher_diagnostics import json_signature
    from types import SimpleNamespace
    pair = evidence.read(pair_entry["path"])
    directory = pair_directory(evidence, pair_entry)
    evidence.require([directory / name for name in ("training_summary.json", "registered_config.json")]
        + [directory / arm / name for arm in ("A", "B") for name in ("training_report.json", "deployment_receipt.json")])
    if evidence.read(directory / "registered_config.json") != pair:
        raise ValueError("Completed training output belongs to another registered pair")
    summary_path = directory / "training_summary.json"
    summary = evidence.read(summary_path)
    if (summary.get("schema") != SCHEMA or summary.get("status") != "completed" or summary.get("pair_complete") is not True
            or summary.get("checkpoint_unchanged") is not True or summary.get("test_opened") is not False
            or summary.get("planned_updates_per_arm") != 5000 or summary.get("source_files") != sources):
        raise ValueError("Pair has not completed all5000 updates and immutable final checks")
    rows, provenances, reports = [], [], []
    f01_path = gate["f01s"][pair_entry["visual_tokens"]]
    for arm in ("A", "B"):
        receipt_path = directory / arm / "deployment_receipt.json"
        receipt, report = evidence.read(receipt_path), evidence.read(directory / arm / "training_report.json")
        metadata = formal_metadata(receipt["metadata"])
        validate_formal_receipt(receipt, metadata)
        checkpoint = str(PurePosixPath(pair_entry["checkpoint_root_server"]) / arm / "best.pt")
        expected = dict(suite=pair_entry["suite"], seed=pair_entry["seed"], arm=arm, visual_tokens=pair_entry["visual_tokens"],
            model_revision=pair["model_revision"], training_source_files=sources, frozen_model_sha256=gate["f00"]["frozen_model_sha256"],
            input_acceptance_sha256=gate["f00_sha"], window_manifest_sha256=gate["window_sha"], data_protocol_sha256=gate["protocol_sha"])
        if receipt["pair_config"] != pair or any(metadata.get(k) != v for k, v in expected.items()):
            raise ValueError("Selected receipt differs from registered pair/source/engineering identity")
        identity = report.get("identity", {})
        report_expected = dict(schema=SCHEMA, status="completed", arm=arm, training_updates_completed=5000,
            next_sample_cursor=40000, committed_samples=40000, best_checkpoint=checkpoint,
            best_checkpoint_sha256=receipt["checkpoint_sha256"], evaluations=receipt["evaluations"],
            best_update=metadata["update"], best_validation_metric=metadata["validation_metric"],
            frozen_model_sha256=metadata["frozen_model_sha256"], vla_parameters_unchanged=True)
        identity_expected = dict(pair_config_sha256=json_signature(pair), training_config_sha256=metadata["config_sha256"],
            training_source_files=sources, window_manifest_sha256=gate["window_sha"], data_protocol_sha256=gate["protocol_sha"],
            input_acceptance_sha256=gate["f00_sha"], f01_report_sha256=evidence.watch(f01_path),
            frozen_model_sha256=metadata["frozen_model_sha256"], resume_acceptance_sha256=gate["resume_sha"],
            resume_journal_sha256=gate["resume_journal_sha"])
        if (any(report.get(k) != v for k, v in report_expected.items())
                or any(identity.get(k) != v for k, v in identity_expected.items())
                or summary.get("arms", {}).get(arm) != report or receipt["f01_report_sha256"] != evidence.watch(f01_path)):
            raise ValueError("Selected receipt is not bound to the complete training report and F03 gate")
        provenance = {**metadata, "selector_checkpoint_sha256": receipt["checkpoint_sha256"],
            "deployment_receipt_sha256": json_signature(receipt), "f01_report_sha256": receipt["f01_report_sha256"]}
        provenances.append(SimpleNamespace(provenance=provenance))
        reports.append(report)
        rows.append(dict(identity=selector_instance_identity(provenance), checkpoint=checkpoint,
            receipt=evidence.relative(receipt_path), pair_config=pair_entry["path"], f01_report=evidence.relative(f01_path)))
    validate_formal_pair(*provenances)
    for key in ("initial_scorer_sha256", "sample_order_sha256"):
        from cti_vla.evaluation.formal_runtime import require_sha
        require_sha(reports[0].get(key), key)
        if reports[0].get(key) != reports[1].get(key):
            raise ValueError("Matched A/B initialization or sample order differs")
    finalizations = []
    for path in sorted((directory / "finalizations").glob("*.json")):
        item = evidence.read(path)
        if (item.get("kind") == "training" and item.get("result_status") == "completed"
                and item.get("result_sha256") == evidence.watch(summary_path)):
            if (item.get("status") != "verified" or item.get("checkpoint_unchanged") is not True
                    or item.get("source_files") != sources or item.get("job_id") != summary.get("job_id")):
                raise ValueError("Completed pair finalization identity differs")
            finalizations.append(path)
    if not finalizations:
        raise MissingEvidence([evidence.relative(directory / "finalizations") + "/<matching-complete-finalization>.json"])
    return rows


def suite_rows(evidence, registration, suite, sources, method_ids):
    from cti_vla.evaluation.formal_trials import expected_method_ids, baseline_instance_identity
    from cti_vla.evaluation.formal_runtime import FORMAL_BUDGETS
    if not method_ids or len(set(method_ids)) != len(method_ids) or set(method_ids) - set(expected_method_ids()):
        raise ValueError("Requested methods must be unique registered formal instance IDs")
    gate = load_suite_acceptance(evidence, registration, suite, sources)
    candidates = {}
    for method, total in [("dense", 512), *[("uniform", budget) for budget in FORMAL_BUDGETS]]:
        identity = baseline_instance_identity(suite=suite, method=method, visual_tokens=total,
            model_revision=registration["suites"][suite]["model_revision"], frozen_model_sha256=gate["f00"]["frozen_model_sha256"],
            source_files=sources, input_acceptance_sha256=gate["f00_sha"])
        candidates[identity["method_id"]] = {"identity": identity}
    for pair in registration["pairs"]:
        if pair["suite"] == suite and any(f"{arm}{pair['visual_tokens']}_seed{pair['seed']}" in method_ids for arm in ("A", "B")):
            for row in selected_pair(evidence, pair, gate, sources):
                candidates[row["identity"]["method_id"]] = row
    return [candidates[mid] for mid in expected_method_ids() if mid in method_ids]


def make_execution(registration, suite, rows, *, split="development", matrix=None, release=None):
    from cti_vla.evaluation.formal_trials import ENVIRONMENT, validate_execution_manifest
    from cti_vla.evaluation.formal_runtime import FORMAL_SUITES
    from cti_vla.evaluation.teacher_diagnostics import json_signature
    value = dict(schema=SCHEMA, kind="evaluation_execution", registration_sha256=json_signature(registration),
        suite=suite, split=split, environment={**ENVIRONMENT, "max_steps": FORMAL_SUITES[suite]["max_steps"]}, methods=rows)
    if split == "final":
        value.update(global_freeze=matrix, release=release)
    validate_execution_manifest(value, registration_sha256=json_signature(registration))
    return value


def preflight_all_pairs(evidence, registration):
    required = []
    for pair in registration["pairs"]:
        directory = pair_directory(evidence, pair)
        required.extend(directory / name for name in ("training_summary.json", "registered_config.json"))
        required.extend(directory / arm / name for arm in ("A", "B") for name in ("training_report.json", "deployment_receipt.json"))
    for suite in registration["suites"]:
        required.append(f"results/{SCHEMA}/{suite}/acceptance/root_review.json")
    evidence.require(required)


def build_global(evidence, registration, sources, development_index, output_directory, *, checkpoint_inventory):
    from cti_vla.evaluation.formal_trials import expected_method_ids, audit_development_outputs, validate_freeze_matrix
    from cti_vla.data.formal_initial_states import load_formal_development_panel, validate_formal_final_registry
    from cti_vla.evaluation.teacher_diagnostics import json_signature
    from cti_vla.evaluation.formal_runtime import FORMAL_SUITES
    preflight_all_pairs(evidence, registration)
    evidence.require([checkpoint_inventory])
    index = evidence.read(development_index)
    if (index.get("schema") != SCHEMA or index.get("kind") != "development_output_index"
            or set(index.get("suites", {})) != set(FORMAL_SUITES)):
        raise ValueError("Development index must explicitly list all four suites' raw output directories")
    all_rows, suites, artifacts = {}, {}, {}
    for suite in FORMAL_SUITES:
        rows = suite_rows(evidence, registration, suite, sources, expected_method_ids())
        all_rows[suite] = rows
        identities = [row["identity"] for row in rows]
        states_root = evidence.path(registration["suites"][suite]["initial_states_root"])
        dev_path, registry_path = states_root / "development.json", states_root / "final_registry.json"
        evidence.watch(dev_path)
        panel = load_formal_development_panel(dev_path)
        if panel["suite"] != suite:
            raise ValueError("Registered development panel suite differs")
        directories = [evidence.path(path) for path in index["suites"][suite]]
        if not directories or len(set(directories)) != len(directories):
            raise ValueError("Development index contains missing or duplicate output directories")
        for directory in directories:
            for name in ("config.json", "panel.json", "closed_loop_report.json", "trials.jsonl"):
                evidence.watch(directory / name)
        completion = audit_development_outputs(directories, panel=panel,
            registration_sha256=json_signature(registration), expected_identities=identities)
        # Paths are portable project-relative references, not machine-specific F:/ or P roots.
        for item in completion["outputs"]:
            item["path"] = evidence.relative(item["path"])
        registry = evidence.read(registry_path)  # indices and hashes only; never sealed_final values
        validate_formal_final_registry(registry)
        if registry["suite"] != suite or registry["source"] != panel["source"] or registry["task_catalog"] != panel["task_catalog"]:
            raise ValueError("Final index registry differs from the audited development panel source")
        dev_states = {(r["task_id"], r["source_state_index"]) for r in panel["states"]}
        if dev_states & {(r["task_id"], r["source_state_index"]) for r in registry["states"]}:
            raise ValueError("Development and final index registries overlap")
        completion_name = f"development_completion/{suite}.json"
        artifacts[completion_name] = completion
        suites[suite] = dict(development_panel_sha256=evidence.watch(dev_path),
            development_completion_sha256=hashlib.sha256(encoded(completion)).hexdigest(),
            final_registry_sha256=evidence.watch(registry_path), panel_source_sha256=json_signature(panel["source"]),
            development_completed=True, development_unique_initial_states=100, development_method_ids=expected_method_ids())
    matrix = dict(schema=SCHEMA, kind="global_final_freeze", registration_sha256=json_signature(registration),
        instances=[row["identity"] for suite in FORMAL_SUITES for row in all_rows[suite]], suites=suites)
    validate_freeze_matrix(matrix, registration_sha256=json_signature(registration))
    validate_checkpoint_inventory(evidence, checkpoint_inventory, registration, sources, matrix["instances"])
    evidence.unchanged()
    # The existing release binds json_signature(matrix), so these additive
    # fields bind the new evidence without changing any frozen runtime module.
    matrix.update(evidence_files_sha256=json_signature(dict(sorted(evidence.files.items()))),
        server_checkpoint_inventory=evidence.relative(checkpoint_inventory),
        server_checkpoint_inventory_sha256=evidence.watch(checkpoint_inventory))
    artifacts["global_freeze.json"] = matrix
    artifacts["execution_rows.json"] = dict(schema=SCHEMA, kind="frozen_execution_rows", suites=all_rows)
    artifacts["freeze_evidence.json"] = dict(schema=SCHEMA, kind="global_freeze_evidence", test_opened=False,
        builder_source_sha256=digest(__file__),
        checkpoint_bytes_read_locally=False, checkpoint_presence_claimed=True,
        server_checkpoint_inventory=evidence.relative(checkpoint_inventory),
        checkpoint_verification="Fresh server-only72-file existence/SHA receipt plus completed development; server execution rechecks bytes",
        registration_sha256=json_signature(registration), global_freeze_sha256=json_signature(matrix),
        files=dict(sorted(evidence.files.items())),
        outputs={name: hashlib.sha256(encoded(value)).hexdigest() for name, value in artifacts.items()})
    for name, value in artifacts.items():
        immutable_write(evidence.path(Path(output_directory) / name), value)
    return matrix


def release_global(evidence, registration, directory, *, release=False, created_utc=None):
    from cti_vla.evaluation.formal_trials import validate_freeze_matrix, make_final_release
    from cti_vla.evaluation.teacher_diagnostics import json_signature
    directory = evidence.path(directory)
    audit = evidence.read(directory / "freeze_evidence.json")
    if (audit.get("schema") != SCHEMA or audit.get("kind") != "global_freeze_evidence"
            or audit.get("test_opened") is not False or audit.get("registration_sha256") != json_signature(registration)):
        raise ValueError("Global freeze evidence is missing or belongs to another registration")
    if audit.get("builder_source_sha256") != digest(__file__):
        raise ValueError("Root must rebuild/review this freeze after changing the manifest builder")
    for relative, checksum in {**audit["files"], **{
            evidence.relative(directory / name): value for name, value in audit["outputs"].items()}}.items():
        if evidence.watch(relative) != checksum:
            raise ValueError("Global freeze input/output bytes changed: " + relative)
    matrix = evidence.read(directory / "global_freeze.json")
    validate_freeze_matrix(matrix, registration_sha256=json_signature(registration))
    if json_signature(matrix) != audit["global_freeze_sha256"]:
        raise ValueError("Global freeze differs from its audited evidence")
    if (matrix.get("evidence_files_sha256") != json_signature(dict(sorted(audit["files"].items())))
            or matrix.get("server_checkpoint_inventory") != audit.get("server_checkpoint_inventory")
            or evidence.watch(matrix["server_checkpoint_inventory"]) != matrix.get("server_checkpoint_inventory_sha256")):
        raise ValueError("Global release does not bind its complete evidence and server checkpoint inventory")
    for suite, row in matrix["suites"].items():
        if evidence.watch(directory / "development_completion" / (suite + ".json")) != row["development_completion_sha256"]:
            raise ValueError("Global freeze is not bound to its rebuilt development receipt")
    rows = evidence.read(directory / "execution_rows.json")
    from cti_vla.evaluation.formal_trials import expected_method_ids
    if (rows.get("schema") != SCHEMA or rows.get("kind") != "frozen_execution_rows"
            or set(rows.get("suites", {})) != set(matrix["suites"])
            or any([row["identity"]["method_id"] for row in methods] != expected_method_ids()
                for methods in rows["suites"].values())):
        raise ValueError("Frozen execution rows must contain all22 methods in each of four suites")
    dry_release = make_final_release(matrix, registration_sha256=json_signature(registration), created_utc="validation-only")
    for suite, methods in rows["suites"].items():
        make_execution(registration, suite, methods, split="final", matrix=matrix, release=dry_release)
    evidence.unchanged()
    if not release:
        return dict(schema=SCHEMA, status="verified_not_released", global_freeze_sha256=json_signature(matrix), test_opened=False)
    release_path = directory / "root_release.json"
    if release_path.exists():
        existing = evidence.read(release_path)
        created_utc = existing["created_utc"]
    value = make_final_release(matrix, registration_sha256=json_signature(registration),
        created_utc=created_utc or datetime.now(timezone.utc).isoformat())
    manifests = {suite: make_execution(registration, suite, methods, split="final", matrix=matrix, release=value)
        for suite, methods in rows["suites"].items()}
    immutable_write(release_path, value)
    for suite, manifest in manifests.items():
        immutable_write(directory / "final_execution" / (suite + ".json"), manifest)
    return dict(schema=SCHEMA, status="root_released", release=evidence.relative(release_path),
        release_file_sha256=digest(release_path), test_opened=False, final_values_read=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--registration", default=REGISTRATION)
    sub = parser.add_subparsers(dest="command", required=True)
    development = sub.add_parser("development")
    development.add_argument("--suite", choices=SUITES, required=True)
    development.add_argument("--methods", nargs="+")
    development.add_argument("--source-inventory", required=True)
    development.add_argument("--output", required=True)
    freeze = sub.add_parser("freeze")
    freeze.add_argument("--source-inventory", required=True)
    freeze.add_argument("--development-index", required=True)
    freeze.add_argument("--checkpoint-inventory", required=True)
    freeze.add_argument("--output-directory", required=True)
    final = sub.add_parser("release")
    final.add_argument("--directory", required=True)
    final.add_argument("--release", action="store_true", help="Explicit root release; omitted means verification only")
    checker = sub.add_parser("checkpoint-inventory", help="CPU-only server hash receipt for exactly72 registered best.pt files")
    checker.add_argument("--source-inventory", required=True)
    checker.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    evidence = Evidence(args.project_root)
    try:
        registration = registration_contract(evidence, args.registration)
        if args.command == "checkpoint-inventory":
            result = server_checkpoint_inventory(evidence, registration, args.source_inventory, args.output)
        elif args.command == "release":
            result = release_global(evidence, registration, args.directory, release=args.release)
        else:
            sources = source_contract(evidence, args.source_inventory)
            if args.command == "development":
                from cti_vla.evaluation.formal_trials import expected_method_ids
                from cti_vla.evaluation.teacher_diagnostics import json_signature
                from cti_vla.data.formal_initial_states import load_formal_development_panel
                panel_path = evidence.path(registration["suites"][args.suite]["initial_states_root"] + "/development.json")
                evidence.watch(panel_path)
                panel = load_formal_development_panel(panel_path)
                if panel["suite"] != args.suite:
                    raise ValueError("Development panel belongs to another suite")
                rows = suite_rows(evidence, registration, args.suite, sources, args.methods or expected_method_ids())
                manifest = make_execution(registration, args.suite, rows)
                manifest.update(development_panel=evidence.relative(panel_path),
                    development_panel_sha256=evidence.watch(panel_path))
                evidence.unchanged()
                immutable_write(evidence.path(args.output), manifest)
                immutable_write(evidence.path(args.output + ".evidence.json"), dict(schema=SCHEMA,
                    kind="development_execution_evidence", manifest_sha256=json_signature(manifest),
                    files=evidence.files, checkpoint_bytes_read_locally=False, test_opened=False))
                result = dict(status="development_manifest_written", methods=len(rows), output=args.output, test_opened=False)
            else:
                matrix = build_global(evidence, registration, sources, args.development_index, args.output_directory,
                    checkpoint_inventory=args.checkpoint_inventory)
                result = dict(status="frozen_not_released", instances=len(matrix["instances"]),
                    output_directory=args.output_directory, test_opened=False)
    except (ValueError, FileNotFoundError, KeyError) as error:
        result = dict(status="blocked", error=str(error), test_opened=False)
        if isinstance(error, MissingEvidence):
            result.update(missing_count=len(error.missing), missing=error.missing)
        print(json.dumps(result, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

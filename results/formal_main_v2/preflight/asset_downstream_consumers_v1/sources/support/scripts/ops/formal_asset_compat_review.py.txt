"""Read-only root audit for the explicitly registered metadata adapter.

This is operational provenance, outside the frozen173 scientific source. It
never installs an adapter, opens weights, reads final state values or submits a
job. Callers must also require SHA-pulled copies of ``required_pulled_files``.
"""
from __future__ import annotations

import hashlib
from datetime import datetime
import json
import math
from pathlib import Path, PurePosixPath
import re


SCHEMA = "formal_main_v2"
VERSION = "formal-asset-metadata-compat-v1"
STAGE_VERSION = "formal-asset-stage-v1"
P = PurePosixPath("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
SOURCE = P / "snapshots/formal_main_v2_run_564be0995e"
SOURCE_SHA256 = "dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e"
SOURCE_INVENTORY = "results/formal_main_v2/source/formal_main_v2_run_564be0995e.json"
REGISTRATION = "configs/experiments/formal_main_v2_asset_metadata_compat_v1.json"
REGISTRATION_SHA256 = "25c90cbfe2db6fdb130a16e6b98ab7ccfc8373a2853578bf73ef0d38283cfb44"
FORMAL_REGISTRATION = "configs/experiments/formal_main_v2.json"
ADAPTER = "scripts/ops/formal_asset_metadata_adapter.py"
ADAPTER_SHA256 = "d1ca08465ffcf2682569b1224e2018f17fdba61feac1896f864cc981759397d0"
WRAPPER = "scripts/server/run_formal_asset_stage.py"
SLURM = "scripts/server/formal_asset_main.slurm"
LOADER = "src/cti_vla/evaluation/checkpoint_manifest.py"
LOADER_SHA256 = "6bad8f22b9b683de4785a3f05827f6383759a5689ca178efe71ea078211f368a"
FIELDS = ("schema_version", "repository", "revision", "total_bytes", "files")
OMITTED = ("source", "formal_experiment", "registered_utc")
ORIGINALS = {
    "libero_object": ("configs/assets/openvla_oft_libero_object.json",
        "3c3e3b614fa0bf4134825d95d22b69173d79bfb4a594f9c113c832156d0f6a24"),
    "libero_goal": ("configs/assets/openvla_oft_libero_goal.json",
        "6aaef6cd88a3968a13591fc196a3498c1780c7aab7a5e782a53c1967911a0ed5"),
}
STRICT = {suite: "configs/assets/formal_main_v2_strict/" + suite + ".json" for suite in ORIGINALS}
STRICT_SHA256 = {
    "libero_object": "d8f1f9a5c1c8c040aa499fd9df35ebe4a039fd6c756b565cf6055046be0cf8b3",
    "libero_goal": "e55eac83f28854318524ba87fc6554c7a9708b328700232c055deb66a72e0d6c",
}
LEGACY = ("libero_10", "libero_spatial")
ARTIFACT_NAMES = ("identity.json", "compatibility_events.jsonl")


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError("Asset compatibility review: " + message)


def sha_value(value):
    require(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value), "invalid SHA256")
    return value


def same(actual, expected, label):
    require(isinstance(actual, dict) and all(actual.get(k) == v
        and (not isinstance(v, bool) or type(actual.get(k)) is bool) for k, v in expected.items()), label + " differs")


def contract(evidence, *, job, invocation):
    """Return the validated exact contract, or None for untouched legacy jobs.

    Object/Goal cannot omit compatibility provenance, even if legacy field
    validators would accept their scientific outputs. Long/Spatial cannot carry
    a compatibility field (including null); their original branch is unchanged.
    """
    suite = job.get("suite")
    found = invocation.get("runtime_compatibility")
    if suite in LEGACY:
        require("runtime_compatibility" not in invocation and "runtime_compatibility" not in job,
            "legacy suite unexpectedly uses a compatibility runtime")
        return None
    require(suite in ORIGINALS, "unknown suite")
    require(isinstance(found, dict), "Object/Goal requires explicit runtime_compatibility")
    expected = dict(schema=SCHEMA, kind="asset_metadata_compatibility", version=VERSION,
        wrapper=WRAPPER, slurm=SLURM, adapter=ADAPTER, registration=REGISTRATION)
    require(set(found) == {*expected, "files"}, "runtime contract keys differ")
    same(found, expected, "runtime contract")
    require(isinstance(found["files"], dict) and set(found["files"]) ==
        {WRAPPER, SLURM, ADAPTER, REGISTRATION, *STRICT.values()}, "runtime must bind exactly six files")
    require(job.get("source_root") == str(SOURCE) and job.get("source_sha256") == SOURCE_SHA256,
        "runtime compatibility belongs to another frozen source")
    require(job.get("runtime_compatibility") == found, "registered job runtime contract missing or differs")
    pins = {ADAPTER: ADAPTER_SHA256, REGISTRATION: REGISTRATION_SHA256,
        **{STRICT[suite]: checksum for suite, checksum in STRICT_SHA256.items()}}
    for relative, checksum in found["files"].items():
        sha_value(checksum)
        require(evidence.watch(relative) == checksum, "runtime input bytes changed: " + relative)
        require(relative not in pins or pins[relative] == checksum, "unregistered adapter/metadata version")
    return found


def expected_identity(evidence, *, inventory, runtime):
    """Rebuild path/header/per-file equivalence and all178 producer inputs.

    Python code fingerprints are produced and compared in the server's single
    interpreter. They are opaque SHA values here: local and server Python may
    have different bytecode. Source bytes, exact adapter version and emitted
    identity equality bind that producer check without claiming cross-version
    bytecode equality.
    """
    files = inventory.get("files", {})
    require(len(files) == 173 and inventory.get("schema") == SCHEMA
        and inventory.get("source_root_server") == str(SOURCE)
        and inventory.get("source_sha256") == SOURCE_SHA256
        and hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest() == SOURCE_SHA256,
        "frozen173 inventory differs")
    inventory_sha = evidence.watch(SOURCE_INVENTORY)
    require(evidence.read(SOURCE_INVENTORY) == inventory, "source inventory argument differs from pinned file")
    for relative, checksum in files.items():
        require(evidence.watch(relative) == checksum, "frozen source changed: " + relative)
    registration = evidence.read(REGISTRATION)
    same(registration, dict(schema=SCHEMA, kind="asset_metadata_compatibility_registration", version=VERSION,
        frozen_source_inventory=SOURCE_INVENTORY, frozen_source_sha256=SOURCE_SHA256,
        frozen_file_count=173, original_registration=FORMAL_REGISTRATION,
        original_registration_sha256=files[FORMAL_REGISTRATION], adapter_path=ADAPTER,
        strict_fields=list(FIELDS), omitted_metadata_fields=list(OMITTED),
        scientific_settings_changed=False, weights_changed=False, original_manifest_identity_retained=True),
        "compatibility registration")
    require(set(registration.get("views", {})) == set(ORIGINALS), "view whitelist differs")
    formal = evidence.read(FORMAL_REGISTRATION)
    views = {}
    for suite, (original, original_sha) in ORIGINALS.items():
        row, spec = registration["views"][suite], formal["suites"][suite]
        raw, strict = evidence.read(original), evidence.read(STRICT[suite])
        require(files.get(original) == original_sha and evidence.watch(original) == original_sha,
            "original manifest differs")
        require(set(raw) == set(FIELDS + OMITTED), "original metadata fields differ")
        projected = {key: raw[key] for key in FIELDS}
        require(strict == projected and set(strict) == set(FIELDS), "strict view is not an exact projection")
        same(row, dict(original_path=original, original_sha256=original_sha, derived_path=STRICT[suite],
            derived_sha256=STRICT_SHA256[suite], omitted_metadata={key: raw[key] for key in OMITTED},
            equal_header={key: raw[key] for key in FIELDS if key != "files"}, files_equal=raw["files"],
            file_count=len(raw["files"]), file_specs_sha256=signature(raw["files"]),
            projected_payload_sha256=signature(projected)), "registered projection")
        require((spec["model_manifest"], spec["model_manifest_sha256"], spec["model_revision"]) ==
            (original, original_sha, raw["revision"]), "original formal model identity changed")
        views[suite] = dict(suite=suite, original_path=str(SOURCE / original), original_sha256=original_sha,
            derived_path=str(P / STRICT[suite]), derived_sha256=STRICT_SHA256[suite], file_count=len(raw["files"]),
            total_bytes=raw["total_bytes"], repository=raw["repository"], revision=raw["revision"],
            file_specs_sha256=signature(raw["files"]), projected_payload_sha256=signature(projected),
            omitted_metadata_fields=list(OMITTED))
    watched = {str(P / ADAPTER): runtime["files"][ADAPTER], str(P / REGISTRATION): REGISTRATION_SHA256,
        str(P / SOURCE_INVENTORY): inventory_sha, **{str(SOURCE / name): checksum for name, checksum in files.items()},
        **{str(P / STRICT[suite]): checksum for suite, checksum in STRICT_SHA256.items()}}
    require(len(watched) == 178 and files.get(LOADER) == LOADER_SHA256, "pinned loader/input set differs")
    return dict(schema=SCHEMA, kind="asset_metadata_compatibility", version=VERSION,
        project_root=str(P), source_root=str(SOURCE), source_inventory=str(P / SOURCE_INVENTORY),
        source_inventory_sha256=inventory_sha, frozen_source_sha256=SOURCE_SHA256, verified_frozen_file_count=173,
        adapter_path=str(P / ADAPTER), adapter_sha256=runtime["files"][ADAPTER],
        registration_path=str(P / REGISTRATION), registration_sha256=REGISTRATION_SHA256,
        loader_path=str(SOURCE / LOADER), loader_sha256=LOADER_SHA256, fingerprint_marshal_version=2,
        original_manifest_identity_retained=True, views=views, watched_files=watched)


def reject_unintegrated_consumer(*, suite, review, consumer):
    """Explicit temporary gate: unknown compatibility fields are never ignored."""
    if suite in ORIGINALS or any(key in review for key in ("runtime_compatibility", "runtime_compatibility_review")):
        raise ValueError(consumer + " has not integrated the asset-metadata runtime provenance; refuse compatibility outputs")


def review_job(evidence, *, job, invocation, receipt, inventory):
    """Audit a *successful* wrapper, returning extra raw files to SHA-pull.

    This never treats return0 as scientific acceptance. The existing callers
    still reconstruct F00/F01/F03 or every training/validation update. Failed or
    truncated compatibility evidence stays retained but cannot receive this
    successful-runtime attestation.
    """
    runtime = contract(evidence, job=job, invocation=invocation)
    if runtime is None:
        require(not any(k in receipt for k in ("runtime_compatibility", "compatibility_artifacts",
            "loader_restored", "source_inputs_unchanged")), "legacy receipt contains compatibility evidence")
        return None
    require(job.get("mode") in ("acceptance", "train"), "only acceptance/training compatibility is integrated")
    job_id, suite = str(job["job_id"]), job["suite"]
    require(re.fullmatch(r"[0-9]+", job_id), "invalid job ID")
    invocation_rel = job["invocation"]
    invocation_sha = evidence.watch(invocation_rel)
    require(invocation_sha == job["invocation_sha256"] and evidence.read(invocation_rel) == invocation,
        "registered invocation bytes differ")
    shared = dict(job_id=job_id, stage=job["mode"], stage_key=job["stage_key"], suite=suite,
        source_root=str(SOURCE), source_sha256=SOURCE_SHA256, invocation_sha256=invocation_sha)
    entry = "scripts/verify_formal_acceptance.py" if job["mode"] == "acceptance" else "scripts/run_formal_future.py"
    require(invocation.get("entrypoint") == entry and invocation.get("stage") == job["mode"], "entrypoint differs")
    output = PurePosixPath(job["run_root"])
    require(str(output) == job["run_root"] and P in output.parents and ".." not in output.parts,
        "noncanonical run root")
    global_root = P / f"results/{SCHEMA}/compatibility_invocations/{job_id}"
    copy_root = output / "compatibility" / job_id
    artifacts = receipt.get("compatibility_artifacts")
    require(isinstance(artifacts, list) and len(artifacts) == 2, "exactly two copied compatibility artifacts required")
    required, artifacts_by_name = [], {}
    for artifact in artifacts:
        require(isinstance(artifact, dict) and set(artifact) == {"source", "path", "sha256", "bytes"},
            "copied artifact fields differ")
        name = PurePosixPath(artifact["path"]).name
        require(name in ARTIFACT_NAMES and name not in artifacts_by_name, "unknown/duplicate compatibility artifact")
        require(artifact["path"] == str(copy_root / name) and artifact["source"] == str(global_root / name),
            "artifact is not this job's exact global-to-run copy")
        relative = (copy_root / name).relative_to(P).as_posix()
        require(type(artifact["bytes"]) is int and artifact["bytes"] > 0
            and evidence.path(relative).stat().st_size == artifact["bytes"]
            and evidence.watch(relative) == sha_value(artifact["sha256"]), "copied artifact bytes/SHA differ")
        artifacts_by_name[name] = artifact
        required.append(relative)
    identity_rel = (copy_root / ARTIFACT_NAMES[0]).relative_to(P).as_posix()
    events_rel = (copy_root / ARTIFACT_NAMES[1]).relative_to(P).as_posix()
    payload = evidence.read(identity_rel)
    expected_outer = dict(schema=SCHEMA, kind="formal_asset_stage_identity", version=STAGE_VERSION,
        **shared, invocation_path=str(P / invocation_rel), runtime_compatibility=runtime)
    require(set(payload) == {*expected_outer, "identity"}, "identity envelope keys differ")
    same(payload, expected_outer, "identity envelope")
    identity = payload["identity"]
    wanted = expected_identity(evidence, inventory=inventory, runtime=runtime)
    fingerprints = ("original_loader_code_sha256", "directory_verifier_code_sha256")
    require(isinstance(identity, dict) and set(identity) == {*wanted, *fingerprints}, "adapter identity keys differ")
    same(identity, wanted, "adapter identity and metadata projection")
    for key in fingerprints:
        sha_value(identity[key])
    raw = evidence.path(events_rel).read_bytes()
    require(raw.endswith(b"\n"), "unterminated compatibility journal")
    try:
        rows = [json.loads(line) for line in raw.splitlines()]
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Asset compatibility review: malformed journal") from exc
    order = ["stage_start", "asset_metadata_compat_enter", "stage_runner_start", "asset_metadata_compat_load_start",
        "asset_metadata_compat_load_complete", "stage_runner_return", "asset_metadata_compat_exit", "stage_end"]
    require(len(rows) == len(order), "successful journal must have exactly eight events and one target load")
    times = []
    for seq, (row, event) in enumerate(zip(rows, order)):
        same(row, dict(schema=SCHEMA, kind="formal_asset_stage_event", version=STAGE_VERSION,
            **shared, event=event, seq=seq), "journal sequence/job/source envelope")
        require(type(row["seq"]) is int, "journal sequence must be an integer")
        try:
            timestamp = datetime.fromisoformat(row["utc"])
            require(timestamp.utcoffset() is not None, "journal UTC has no timezone")
        except (TypeError, KeyError, ValueError) as exc:
            raise ValueError("Asset compatibility review: invalid journal timestamp") from exc
        times.append(timestamp)
    require(times == sorted(times), "journal timestamps move backwards")
    same(rows[0], dict(entrypoint=entry, argv=invocation["argv"], run_root=job["run_root"],
        runtime_compatibility=runtime), "stage start")
    same(rows[1], dict(identity=identity), "adapter-enter identity")
    sha_value(rows[1].get("binding_code_sha256"))
    identity_sha = evidence.watch(identity_rel)
    same(rows[2], dict(entrypoint=entry, argv=invocation["argv"], cwd=str(SOURCE), run_name="__main__",
        identity_sha256=identity_sha), "runner start")
    same(rows[3], dict(call_id=0, view=identity["views"][suite]), "target load start")
    same(rows[4], dict(call_id=0, suite=suite, file_count=identity["views"][suite]["file_count"],
        total_bytes=identity["views"][suite]["total_bytes"]), "target load completion")
    require(type(rows[3].get("call_id")) is int and type(rows[4].get("call_id")) is int,
        "load call IDs must be integer0")
    termination = rows[5].get("runner_termination")
    require(termination in ("returned", "system_exit"), "runner did not return successfully")
    same(rows[5], dict(runner_exit_code=0), "runner return")
    require(type(rows[5].get("runner_exit_code")) is int, "runner exit code is not integer0")
    flags = dict(original_loader_restored=True, directory_verifier_unchanged=True, binding_intact=True,
        original_loader_code_unchanged=True, directory_verifier_code_unchanged=True,
        frozen_source_and_inputs_unchanged=True, runner_raised=False)
    same(rows[6], dict(**flags, adapted_calls_attempted=1, adapted_calls_completed=1, passthrough_calls=0), "adapter exit")
    for key in ("adapted_calls_attempted", "adapted_calls_completed", "passthrough_calls"):
        require(type(rows[6].get(key)) is int, "adapter counters must be integers")
    terminal = dict(status="returned", exit_code=0, runner_termination=termination, runner_exit_code=0,
        loader_restored=True, source_inputs_unchanged=True, errors=[], identity_sha256=identity_sha)
    same(rows[7], terminal, "stage end")
    expected_receipt = dict(schema=SCHEMA, kind="formal_asset_stage_job", version=STAGE_VERSION,
        **shared,
        entrypoint=entry, run_root=job["run_root"], runtime_compatibility=runtime,
        wrapper_sha256=runtime["files"][WRAPPER], **{key: terminal[key] for key in terminal if key != "identity_sha256"})
    same(receipt, expected_receipt, "wrapper receipt")
    require(type(receipt.get("exit_code")) is int and type(receipt.get("runner_exit_code")) is int,
        "receipt exit code is not integer0")
    wall = receipt.get("wall_seconds")
    require(type(wall) in (float, int) and math.isfinite(wall) and wall > 0, "missing positive wrapper cost")
    helper = "scripts/ops/formal_asset_compat_review.py"
    return dict(schema=SCHEMA, kind="asset_metadata_compatibility_review", status="verified", **shared,
        runtime_compatibility=runtime, identity_sha256=identity_sha, events_sha256=evidence.watch(events_rel),
        required_pulled_files=required, wrapper_sha256=runtime["files"][WRAPPER],
        helper_sha256=evidence.watch(helper), exact_target_suite_loads=1, event_count=8,
        original_manifest_identity_retained=True, metadata_projection_equivalent=True,
        loader_restored=True, source_inputs_unchanged=True,
        deployment_integration_status="pending_explicit_downstream_adapter_integration")

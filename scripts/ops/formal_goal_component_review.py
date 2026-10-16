"""Read-only audit of the registered Goal component-filename compatibility.

The original metadata runtime remains a separate, unchanged proof. This module
opens only source, configuration and nonweight receipts; Slurm allocation cost
is still counted by the existing reviewers, never by nested wrapper timings.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath
import re


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "formal_main_v2"
VERSION = "formal-goal-components-v1"
SUITE = "libero_goal"
P = PurePosixPath("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
SOURCE = P / "snapshots/formal_main_v2_run_564be0995e"
SOURCE_SHA256 = "dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e"
SOURCE_INVENTORY = "results/formal_main_v2/source/formal_main_v2_run_564be0995e.json"
FORMAL_REGISTRATION = "configs/experiments/formal_main_v2.json"
REGISTRATION = "configs/experiments/formal_main_v2_goal_component_compat_v1.json"
WRAPPER = "scripts/server/run_formal_goal_asset_stage.py"
ADAPTER = "scripts/ops/formal_goal_component_adapter.py"
SLURM = "scripts/server/formal_goal_asset_main.slurm"
FILES = (WRAPPER, ADAPTER, SLURM, REGISTRATION)
LOADER = "src/cti_vla/models/openvla_oft_loader.py"
LOADER_SHA256 = "e3782154cd7363364e2e8d7e88740e0ca6b4c8b423368360de5b2ff7607e5e22"
MANIFEST = "configs/assets/openvla_oft_libero_goal.json"
MANIFEST_SHA256 = "6aaef6cd88a3968a13591fc196a3498c1780c7aab7a5e782a53c1967911a0ed5"
MODEL_ROOT = PurePosixPath("/share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-goal-c2d0f9f")
METADATA_HELPER = "scripts/ops/formal_asset_compat_review.py"
METADATA_HELPER_SHA256 = "6ad55ddac4bfb692c72e3b1a9c37f41d6d831d7d03a2f2fbbde7f3c0dcf8f46b"
INNER = "scripts/server/run_formal_asset_stage.py"
INNER_SHA256 = "9c49bbd536646c8b677c611328e79e7ff3a16a6bca7c5309c8e69cdce3250996"
SYMBOLS = ("_load_component_state", "remove_uniform_ddp_prefix", "load_openvla_oft_components")
MAPPINGS = [
    dict(requested="action_head--150000_checkpoint.pt", target="action_head--50000_checkpoint.pt", size=302242654,
        sha256="b97c2e8939ede32d8a1b29e9565d70f22040ba9e54925665e81989a0cc13ccff"),
    dict(requested="proprio_projector--150000_checkpoint.pt", target="proprio_projector--50000_checkpoint.pt", size=67275184,
        sha256="780595e9cca5292348697686f9ccc83d39d9d3d303e860d62c6d4609952dfff1"),
]
ARTIFACT_NAMES = ("identity.json", "events.jsonl", "completion.json")
COST_SCOPE = "Nested diagnostic only; count the entire Slurm allocation once"


class ScopedEvidence:
    """Record only this proof's inputs, never caller state/progress side reads."""
    def __init__(self, parent):
        self.parent, self.hashes = parent, {}

    def path(self, name):
        return self.parent.path(name)

    def watch(self, name):
        value = self.parent.watch(name)
        self.hashes[self.path(name).relative_to(self.parent.root).as_posix()] = value
        return value

    def read(self, name):
        self.watch(name)
        return json.loads(self.path(name).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError("Goal component review: " + message)


def same(actual, expected, label):
    require(isinstance(actual, dict) and all(actual.get(k) == v
        and (not isinstance(v, bool) or type(actual.get(k)) is bool) for k, v in expected.items()), label + " differs")


def sha_value(value):
    require(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value), "invalid SHA256")
    return value


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def contract(evidence, *, job, invocation):
    """Goal success always needs the registered contract; other suites reject it."""
    if job.get("suite") != SUITE:
        require("component_compatibility" not in job and "component_compatibility" not in invocation,
            "component compatibility is registered for Goal only")
        return None
    value = invocation.get("component_compatibility")
    expected = dict(schema=SCHEMA, kind="goal_component_filename_compatibility", version=VERSION,
        suite=SUITE, wrapper=WRAPPER, adapter=ADAPTER, slurm=SLURM, registration=REGISTRATION)
    require(isinstance(value, dict) and set(value) == {*expected, "files"}, "Goal requires exact component_compatibility contract")
    same(value, expected, "component contract")
    require(job.get("component_compatibility") == value, "registered job component contract missing or differs")
    require(job.get("source_root") == str(SOURCE) and job.get("source_sha256") == SOURCE_SHA256,
        "component runtime belongs to another frozen source")
    require(isinstance(value["files"], dict) and set(value["files"]) == set(FILES),
        "component contract must bind exactly four files")
    for name, checksum in value["files"].items():
        require(evidence.watch(name) == sha_value(checksum), "component runtime file changed: " + name)
    return value


def verified_metadata(evidence, *, job, invocation, receipt, inventory, metadata_review):
    """Recompute the old proof without changing or wrapping its implementation."""
    require(evidence.watch(METADATA_HELPER) == METADATA_HELPER_SHA256, "original metadata reviewer changed")
    path = ROOT / METADATA_HELPER
    require(hashlib.sha256(path.read_bytes()).hexdigest() == METADATA_HELPER_SHA256,
        "loaded metadata reviewer differs from the pinned source")
    spec = importlib.util.spec_from_file_location("goal_review_original_metadata", path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    actual = module.review_job(evidence, job=job, invocation=invocation, receipt=receipt, inventory=inventory)
    require(isinstance(metadata_review, dict) and isinstance(metadata_review.get("pull_receipt"), dict)
        and {k: v for k, v in metadata_review.items() if k != "pull_receipt"} == actual,
        "metadata review does not rebuild from its raw identity/journal")
    return actual


def expected_identity(evidence, *, inventory, component):
    formal = evidence.read(FORMAL_REGISTRATION)["suites"][SUITE]
    manifest = evidence.read(MANIFEST)
    require(evidence.watch(LOADER) == LOADER_SHA256 and inventory["files"].get(LOADER) == LOADER_SHA256
        and evidence.watch(MANIFEST) == MANIFEST_SHA256 and inventory["files"].get(MANIFEST) == MANIFEST_SHA256,
        "original Goal loader/model source differs")
    repository, revision = "moojink/openvla-7b-oft-finetuned-libero-goal", "c2d0f9fbbd82674683b397ff923168a12f6a307b"
    same(formal, dict(model_manifest=MANIFEST, model_manifest_sha256=MANIFEST_SHA256,
        model_root_server=str(MODEL_ROOT), model_revision=revision), "registered Goal model")
    same(manifest, dict(repository=repository, revision=revision), "official Goal manifest")
    manifest_files = {row["path"]: row for row in manifest["files"]}
    for row in MAPPINGS:
        require(row["requested"] not in manifest_files and manifest_files.get(row["target"]) ==
            dict(path=row["target"], size=row["size"], sha256=row["sha256"]), "exact two official components differ")
    expected_registration = dict(schema=SCHEMA, kind="goal_component_filename_compatibility_registration", version=VERSION,
        suite=SUITE, source_inventory=SOURCE_INVENTORY, source_sha256=SOURCE_SHA256,
        loader=LOADER, loader_sha256=LOADER_SHA256, target_symbol=SYMBOLS[0], model_manifest=MANIFEST,
        model_manifest_sha256=MANIFEST_SHA256, model_repository=repository, model_revision=revision,
        checkpoint_root=str(MODEL_ROOT), mappings=MAPPINGS, other_component_requests="reject",
        original_component_loader_used=True, torch_load_replaced=False, official_directory_modified=False,
        scientific_settings_changed=False, weights_changed=False,
        acceptance_required="original_real_F00_F01_F03_and_root_review")
    require(evidence.read(REGISTRATION) == expected_registration, "component registration differs from the fixed official mapping")
    inventory_sha = evidence.watch(SOURCE_INVENTORY)
    watched = {**{str(P / name): checksum for name, checksum in component["files"].items()},
        str(P / SOURCE_INVENTORY): inventory_sha,
        **{str(SOURCE / name): checksum for name, checksum in inventory["files"].items()}}
    require(len(watched) == 178, "component producer input set differs")
    return dict(schema=SCHEMA, kind="goal_component_identity", version=VERSION, suite=SUITE,
        project_root=str(P), source_root=str(SOURCE), source_sha256=SOURCE_SHA256,
        source_inventory=str(P / SOURCE_INVENTORY), source_inventory_sha256=inventory_sha,
        verified_frozen_file_count=173, component_compatibility=component, loader_path=str(SOURCE / LOADER),
        loader_sha256=LOADER_SHA256, fingerprint_marshal_version=2, model_manifest=str(SOURCE / MANIFEST),
        model_manifest_sha256=MANIFEST_SHA256, checkpoint_root=str(MODEL_ROOT),
        mappings=[dict(row, requested_path=str(MODEL_ROOT / row["requested"]),
            target_path=str(MODEL_ROOT / row["target"])) for row in MAPPINGS],
        other_component_requests="reject", original_component_loader_used=True, torch_load_replaced=False,
        scientific_settings_changed=False, weights_changed=False, watched_files=watched)


def read_journal(evidence, relative, *, shared, order):
    raw = evidence.path(relative).read_bytes()
    evidence.watch(relative)
    require(raw.endswith(b"\n"), "unterminated component journal")
    try:
        rows = [json.loads(line) for line in raw.splitlines()]
    except (ValueError, UnicodeError) as error:
        raise ValueError("Goal component review: malformed component journal") from error
    require(len(rows) == len(order), "successful component journal must have exactly ten events")
    times = []
    for seq, (row, event) in enumerate(zip(rows, order)):
        same(row, dict(**shared, kind="formal_goal_component_event", seq=seq, event=event), "component event envelope/order")
        require(type(row.get("seq")) is int, "component sequence must be integer")
        try:
            when = datetime.fromisoformat(row["utc"])
            require(when.utcoffset() is not None, "component event timezone absent")
        except (KeyError, ValueError, TypeError) as error:
            raise ValueError("Goal component review: invalid component timestamp") from error
        times.append(when)
    require(times == sorted(times), "component timestamps move backwards")
    return rows, times


def review_job(evidence, *, job, invocation, receipt, inventory, metadata_review):
    value = contract(evidence, job=job, invocation=invocation)
    if value is None:
        require(not any(key in receipt for key in ("component_compatibility", "component_compatibility_artifacts")),
            "non-Goal job receipt contains component compatibility")
        return None
    evidence = ScopedEvidence(evidence)
    # Re-watch the four contract files in this proof's own immutable input map.
    contract(evidence, job=job, invocation=invocation)
    metadata = verified_metadata(evidence, job=job, invocation=invocation, receipt=receipt,
        inventory=inventory, metadata_review=metadata_review)
    require(job.get("mode") in ("acceptance", "train"), "only Goal acceptance/training is integrated")
    require(not any(key in receipt for key in ("component_compatibility", "component_compatibility_artifacts")),
        "original metadata job receipt must remain separate and unchanged")
    runtime = invocation["runtime_compatibility"]
    require(runtime["files"].get(INNER) == INNER_SHA256, "the original metadata wrapper changed")
    job_id = str(job["job_id"])
    invocation_sha = evidence.watch(job["invocation"])
    shared = dict(schema=SCHEMA, version=VERSION, job_id=job_id, stage=job["mode"], stage_key=job["stage_key"],
        suite=SUITE, source_root=str(SOURCE), source_sha256=SOURCE_SHA256, invocation_sha256=invocation_sha)
    output = PurePosixPath(job["run_root"])
    global_root = P / f"results/{SCHEMA}/component_compatibility_invocations/{job_id}"
    copy_root = output / "component_compatibility" / job_id
    relatives = {name: (copy_root / name).relative_to(P).as_posix() for name in ARTIFACT_NAMES}
    complete = evidence.read(relatives["completion.json"])
    payload = evidence.read(relatives["identity.json"])
    identity_sha = evidence.watch(relatives["identity.json"])
    outer = dict(**shared, kind="formal_goal_component_identity", invocation_path=str(P / job["invocation"]),
        runtime_compatibility=runtime, component_compatibility=value, inner_wrapper_path=str(P / INNER),
        inner_wrapper_sha256=INNER_SHA256)
    require(set(payload) == {*outer, "identity"}, "component identity envelope keys differ")
    same(payload, outer, "component identity envelope")
    identity = payload["identity"]
    wanted = expected_identity(evidence, inventory=inventory, component=value)
    require(isinstance(identity, dict) and set(identity) == {*wanted, "original_function_code_sha256"},
        "component producer identity keys differ")
    same(identity, wanted, "component producer identity")
    codes = identity["original_function_code_sha256"]
    require(isinstance(codes, dict) and set(codes) == set(SYMBOLS), "original component function set differs")
    for checksum in codes.values():
        sha_value(checksum)
    # These bytecode hashes are same-interpreter producer checks; source SHA is
    # the portable root proof, as in the preserved metadata reviewer.
    artifacts = complete.get("component_artifacts")
    require(isinstance(artifacts, list) and len(artifacts) == 2, "component identity/events archive missing")
    actual_names = []
    for artifact in artifacts:
        require(isinstance(artifact, dict) and set(artifact) == {"source", "path", "sha256", "bytes"},
            "component archive fields differ")
        name = PurePosixPath(artifact["path"]).name
        require(name in ARTIFACT_NAMES[:2] and name not in actual_names, "unknown/duplicate component archive")
        actual_names.append(name)
        require(artifact["source"] == str(global_root / name) and artifact["path"] == str(copy_root / name),
            "component archive path differs")
        require(type(artifact["bytes"]) is int and artifact["bytes"] > 0
            and evidence.path(relatives[name]).stat().st_size == artifact["bytes"]
            and evidence.watch(relatives[name]) == sha_value(artifact["sha256"]), "component archive bytes/SHA differ")
    receipt_rel = f"results/{SCHEMA}/job_receipts/{job_id}.json"
    inner_receipt = dict(path=str(P / receipt_rel), sha256=evidence.watch(receipt_rel), bytes=evidence.path(receipt_rel).stat().st_size)
    require(evidence.read(receipt_rel) == receipt, "metadata job receipt argument differs from raw bytes")
    end_fields = dict(status="returned", exit_code=0, inner_exit_code=0, original_loader_restored=True,
        source_inputs_unchanged=True, component_files_unchanged=True, errors=[])
    same(complete, dict(**shared, kind="formal_goal_component_completion", **end_fields,
        runtime_compatibility=runtime, component_compatibility=value, run_root=job["run_root"],
        inner_job_receipt=inner_receipt, metadata_artifacts=receipt["compatibility_artifacts"],
        completion_source=str(global_root / "completion.json"), completion_path=str(copy_root / "completion.json"),
        cost_scope=COST_SCOPE), "component completion")
    require(type(complete.get("exit_code")) is int and type(complete.get("inner_exit_code")) is int,
        "component completion exit codes must be integer0")
    wall = complete.get("wall_seconds")
    require(type(wall) in (int, float) and math.isfinite(wall) and wall > 0 and wall >= receipt["wall_seconds"],
        "outer diagnostic cost must include the inner wrapper duration")
    order = ["component_stage_start", "goal_component_compat_enter", "component_inner_start",
        "goal_component_load_start", "goal_component_load_complete", "goal_component_load_start",
        "goal_component_load_complete", "component_inner_return", "goal_component_compat_exit", "component_stage_end"]
    rows, times = read_journal(evidence, relatives["events.jsonl"], shared=shared, order=order)
    same(rows[0], dict(entrypoint=invocation["entrypoint"], argv=invocation["argv"], runtime_compatibility=runtime,
        component_compatibility=value), "component stage start")
    same(rows[1], dict(identity=identity), "component enter identity")
    sha_value(rows[1].get("binding_code_sha256"))
    same(rows[2], dict(inner_wrapper_path=str(P / INNER), inner_wrapper_sha256=INNER_SHA256,
        entry_function="execute", identity_sha256=identity_sha), "component inner start")
    for call_id, (start, end) in enumerate(((3, 4), (5, 6))):
        for index in (start, end):
            same(rows[index], dict(call_id=call_id, mapping=identity["mappings"][call_id]), "exact ordered component load")
            require(type(rows[index].get("call_id")) is int, "component call ID must be integer")
        require(type(rows[end].get("state_tensor_count")) is int and rows[end]["state_tensor_count"] > 0,
            "original component loader returned no tensor mapping")
        sha_value(rows[end].get("state_keys_sha256"))
    same(rows[7], dict(inner_exit_code=0, inner_job_receipt=inner_receipt, metadata_artifacts=receipt["compatibility_artifacts"]),
        "component inner return")
    require(type(rows[7].get("inner_exit_code")) is int, "inner return exit code must be integer0")
    flags = dict(original_loader_restored=True, original_function_codes_unchanged=True, binding_intact=True,
        torch_load_unchanged=True, source_inputs_unchanged=True, component_files_unchanged=True, runner_raised=False)
    same(rows[8], dict(**flags, component_calls_attempted=2, component_calls_completed=2, rejected_calls=0), "component exit")
    for key in ("component_calls_attempted", "component_calls_completed", "rejected_calls"):
        require(type(rows[8].get(key)) is int, "component exit counters must be integers")
    same(rows[9], dict(**end_fields, identity_sha256=identity_sha), "component stage end")
    require(type(rows[9].get("exit_code")) is int and type(rows[9].get("inner_exit_code")) is int,
        "component end exit codes must be integer0")
    metadata_events_rel = next(name for name in metadata["required_pulled_files"] if name.endswith("/compatibility_events.jsonl"))
    metadata_rows = [json.loads(line) for line in evidence.path(metadata_events_rel).read_bytes().splitlines()]
    metadata_times = [datetime.fromisoformat(row["utc"]) for row in metadata_rows]
    require(times[2] <= metadata_times[0] <= metadata_times[-1] <= times[7]
        and metadata_times[2] <= times[3] <= times[6] <= metadata_times[5],
        "component loads do not occur inside the same metadata runner interval")
    helper_sha = evidence.watch("scripts/ops/formal_goal_component_review.py")
    return dict(schema=SCHEMA, kind="goal_component_compatibility_review", status="verified", job_id=job_id,
        suite=SUITE, stage=job["mode"], stage_key=job["stage_key"], source_sha256=SOURCE_SHA256,
        invocation_sha256=invocation_sha, component_compatibility=value, runtime_compatibility=runtime,
        helper_sha256=helper_sha, metadata_helper_sha256=METADATA_HELPER_SHA256,
        metadata_identity_sha256=metadata["identity_sha256"], metadata_events_sha256=metadata["events_sha256"],
        identity_sha256=identity_sha, events_sha256=evidence.watch(relatives["events.jsonl"]),
        completion_sha256=evidence.watch(relatives["completion.json"]), inner_job_receipt=inner_receipt,
        required_pulled_files=list(relatives.values()), exact_component_loads=2, event_count=10,
        original_loader_restored=True, source_inputs_unchanged=True, component_files_unchanged=True,
        original_component_loader_used=True, torch_load_replaced=False, mappings=identity["mappings"],
        outer_wall_seconds=wall, cost_scope=COST_SCOPE, evidence_sha256=dict(evidence.hashes),
        deployment_integration_status="pending_explicit_downstream_adapter_integration")

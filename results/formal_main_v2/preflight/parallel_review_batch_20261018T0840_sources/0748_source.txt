"""Bounded real-GPU resume probe for formal-main-v2, never a trained selector.

The CPU suite checks the trainer's transaction/control flow. This independent
probe checks the actual CUDA frozen-model backward, AdamW serialization and
all RNG streams using the same serializer, loss and RNG helpers. It retains
engineering weights only on the server and cannot emit a deployment receipt.
"""
from __future__ import annotations

from datetime import datetime, timezone
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time

import numpy as np
import torch

from cti_vla.selection import ConditionalInfluenceEstimator
from cti_vla.training.future_auxiliary import FutureAuxiliaryHead
from cti_vla.training.formal_future import (
    FORMAL_SCHEMA, FORMAL_METRIC, FORMAL_NUMERICS, append_event, atomic_json_save, atomic_torch_save,
    capture_rng, cpu_state, file_sha256, formal_auxiliary_loss, json_signature,
    load_torch, make_formal_batch, parameter_fingerprint, restore_rng, seed_training_rng,
    tensor_signature, validate_formal_training_config,
)

PROBE_VERSION = "formal-main-v2-real-resume-bitwise-v2"
CHECKS = ("scorer_equal", "head_equal", "optimizer_equal", "rng_equal", "rng_probe_equal",
          "next_sample_cursor_equal", "scheduler_position_equal", "step1_snapshot_equal",
          "die_updated", "frozen_model_unchanged", "vla_gradients_absent")


def cpu_tree(value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().clone()
    if isinstance(value, dict):
        return {key: cpu_tree(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(cpu_tree(item) for item in value)
    if isinstance(value, list):
        return [cpu_tree(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported resume tree type: {type(value).__name__}")


def tree_sha256(value):
    digest = hashlib.sha256()
    def add(item):
        if isinstance(item, torch.Tensor):
            tensor = item.detach().cpu().contiguous()
            digest.update(b"tensor:")
            digest.update(json.dumps([str(tensor.dtype), list(tensor.shape)]).encode())
            digest.update(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
        elif isinstance(item, dict):
            digest.update(b"dict{")
            for key in sorted(item, key=lambda k: (type(k).__name__, str(k))):
                add(key)
                add(item[key])
            digest.update(b"}")
        elif isinstance(item, (tuple, list)):
            digest.update((type(item).__name__ + "[").encode())
            for child in item:
                add(child)
            digest.update(b"]")
        elif item is None or isinstance(item, (str, int, float, bool)):
            digest.update(type(item).__name__.encode() + b":" + json.dumps(item, allow_nan=False).encode() + b";")
        else:
            raise TypeError("unsupported resume tree value")
    add(value)
    return digest.hexdigest()


def compare_trees(reference, resumed):
    differences = []
    def visit(a, b, path):
        if type(a) is not type(b):
            differences.append({"path": path, "reason": "type"})
        elif isinstance(a, torch.Tensor):
            if a.dtype != b.dtype or a.shape != b.shape:
                differences.append({"path": path, "reason": "dtype_or_shape"})
            elif not torch.equal(a.detach().cpu().contiguous().reshape(-1).view(torch.uint8),
                                 b.detach().cpu().contiguous().reshape(-1).view(torch.uint8)):
                delta = (a.cpu().double() - b.cpu().double()).abs()
                differences.append({"path": path, "reason": "tensor_bytes",
                    "max_abs": float(delta.max()) if delta.numel() else 0.,
                    "unequal_elements": int((a.cpu() != b.cpu()).sum())})
        elif isinstance(a, dict):
            if set(a) != set(b):
                differences.append({"path": path, "reason": "mapping_keys"})
            else:
                for key in a:
                    visit(a[key], b[key], path + "." + str(key))
        elif isinstance(a, (tuple, list)):
            if len(a) != len(b):
                differences.append({"path": path, "reason": "length"})
            else:
                for i, (x, y) in enumerate(zip(a, b)):
                    visit(x, y, path + f"[{i}]")
        elif a != b:
            differences.append({"path": path, "reason": "value"})
    visit(reference, resumed, "state")
    # Keep all mismatch paths. These are diagnostics, not model weights.
    return {"equal": not differences, "differences": differences,
            "reference_sha256": tree_sha256(reference), "resumed_sha256": tree_sha256(resumed)}


def rng_probe(device):
    """Observable sentinels ensure RNG restoration is tested even without dropout."""
    return {"python": [random.random() for _ in range(3)],
            "numpy": np.random.random(3).tolist(), "torch_cpu": torch.rand(3),
            "torch_cuda": torch.rand(3, device=device).cpu() if torch.device(device).type == "cuda" else None}


def run_formal_resume_acceptance(*, config, records, windows, student, components,
        checkpoint_root: Path, events_path: Path, job_id: str, source_files: dict,
        window_manifest_sha256: str, input_acceptance_sha256: str):
    spec = validate_formal_training_config(config)
    if config["seed"] != 17 or config["tokens_per_camera"] != 64:
        raise ValueError("resume engineering probe is registered at primary128 budget seed17")
    if len(records) != 2 or len(windows) != 2 or [row["task_id"] for row in windows] != [0, 3]:
        raise ValueError("resume probe requires the first two fixed F00 windows (task0/3)")
    if len({row["window_id"] for row in windows}) != 2 or any(row["split"] != "train" for row in windows):
        raise ValueError("resume probe may read only the two distinct registered train windows")
    device = next(components.vla.parameters()).device
    real_gpu = device.type == "cuda"
    root, events_path = Path(checkpoint_root).resolve(), Path(events_path)
    server_root = Path("/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/engineering") / config["suite"]
    if real_gpu and (not os.environ.get("SLURM_JOB_ID") or (root != server_root and server_root not in root.parents)):
        raise ValueError("real resume engineering weights must stay in this suite's server checkpoint tree")
    if not job_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in str(job_id)):
        raise ValueError("invalid engineering job ID")
    run_root = root / ("job_" + str(job_id))
    if run_root.exists() or events_path.exists():
        raise ValueError("resume engineering attempt already exists; retain it and use a new registered attempt")
    run_root.mkdir(parents=True)
    started = time.perf_counter()
    context = {"job_id": str(job_id), "probe_version": PROBE_VERSION, "suite": config["suite"]}
    def event(name, **kwargs):
        append_event(events_path, {**context, "event": name, "seconds_since_start": time.perf_counter() - started,
                                  "utc": datetime.now(timezone.utc).isoformat(), **kwargs})
    def sync():
        if real_gpu:
            torch.cuda.synchronize(device)
    modules = {name: getattr(components, name) for name in ("vla", "action_head", "proprio_projector")}
    frozen_before = parameter_fingerprint(modules)
    base_rng = capture_rng()
    selected_ids = [row["window_id"] for row in windows]
    order = (selected_ids * 8)[:16]
    arms = {}
    def construct(arm):
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(spec.seed)
            scorer = ConditionalInfluenceEstimator(**config["scorer_dimensions"])
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(spec.seed + 10000)
            head = FutureAuxiliaryHead(config["scorer_dimensions"]["token_dim"]) if arm == "B" else None
        scorer = scorer.to(device).train()
        if head is not None:
            head = head.to(device).train()
        parameters = list(scorer.parameters()) + ([] if head is None else list(head.parameters()))
        optimizer = torch.optim.AdamW(parameters, lr=spec.learning_rate, weight_decay=spec.weight_decay)
        return scorer, head, parameters, optimizer
    def snapshot(scorer, head, optimizer, step):
        return {"schema": "formal_main_v2_engineering_resume", "formal_selector": False,
            "scorer": cpu_state(scorer), "head": None if head is None else cpu_state(head),
            "optimizer": cpu_tree(optimizer.state_dict()), "rng": capture_rng(),
            "completed_update": step, "next_sample_cursor": step * spec.effective_batch,
            "next_update": step + 1, "next_alpha": spec.alpha(step + 1), "planned_updates": spec.updates,
            "sample_order_sha256": json_signature(order), "pair_config_sha256": json_signature(config)}
    def step(scorer, head, parameters, optimizer, update, *, arm, branch):
        sync()
        start = time.perf_counter()
        ids = order[(update - 1) * spec.effective_batch:update * spec.effective_batch]
        event("step_start", arm=arm, branch=branch, update=update, next_sample_cursor=(update - 1) * 8,
              window_ids=ids, alpha=spec.alpha(update))
        optimizer.zero_grad(set_to_none=True)
        metrics = {"loss": 0., "teacher_l1": 0., "demonstration_l1": 0., "future_mse": 0.}
        for i, window_id in enumerate(ids):
            event("sample_start", arm=arm, branch=branch, update=update, micro_batch_index=i, window_id=window_id)
            batch = make_formal_batch(records[selected_ids.index(window_id)], device, include_future=arm == "B")
            value = formal_auxiliary_loss(scorer, student, batch, alpha=spec.alpha(update),
                auxiliary_head=head, auxiliary_weight=0. if arm == "A" else spec.future_weight, tokens_per_camera=64)
            (value.loss / spec.effective_batch).backward()
            for key in metrics:
                item = getattr(value, key)
                if item is not None:
                    metrics[key] += float(item.detach()) / spec.effective_batch
            event("sample_end", arm=arm, branch=branch, update=update, micro_batch_index=i, window_id=window_id)
            del value, batch
        grad_norm = float(torch.nn.utils.clip_grad_norm_(parameters, spec.gradient_clip_norm, error_if_nonfinite=True))
        optimizer.step()
        student.require_frozen()
        sync()
        event("step_end", arm=arm, branch=branch, update=update, next_sample_cursor=update * 8,
              seconds=time.perf_counter() - start, forward_backward_samples=8, grad_norm=grad_norm, **metrics)
    def save(path, payload, *, arm, label):
        event("save_start", arm=arm, label=label, checkpoint=str(path))
        start = time.perf_counter()
        atomic_torch_save(path, payload)
        event("save_end", arm=arm, label=label, checkpoint=str(path), checkpoint_sha256=file_sha256(path),
              state_sha256=tree_sha256(payload), seconds=time.perf_counter() - start)
    event("probe_start", execution="real_frozen_openvla_slurm" if real_gpu else "synthetic_cpu",
          selected_windows=windows, pair_config_sha256=json_signature(config), frozen_model_sha256=frozen_before,
          planned_updates=spec.updates, effective_batch=spec.effective_batch, sample_order=order,
          window_manifest_sha256=window_manifest_sha256, input_acceptance_sha256=input_acceptance_sha256,
          source_sha256=json_signature(source_files))
    try:
        for arm in ("A", "B"):
            event("arm_start", arm=arm)
            scorer, head, parameters, optimizer = construct(arm)
            initial_sha = tensor_signature(cpu_state(scorer))
            seed_training_rng(spec.seed + 20000)
            step(scorer, head, parameters, optimizer, 1, arm=arm, branch="continuous")
            first = snapshot(scorer, head, optimizer, 1)
            path = run_root / arm / "step1_resume.pt"
            save(path, first, arm=arm, label="step1")
            continuous_rng_probe = rng_probe(device)
            event("rng_probe", arm=arm, branch="continuous", value_sha256=tree_sha256(continuous_rng_probe))
            step(scorer, head, parameters, optimizer, 2, arm=arm, branch="continuous")
            continuous = snapshot(scorer, head, optimizer, 2)
            reference_path = run_root / arm / "continuous_step2.pt"
            save(reference_path, continuous, arm=arm, label="continuous_step2")
            del scorer, head, parameters, optimizer
            gc.collect()
            if real_gpu:
                torch.cuda.empty_cache()
            # Deliberately disturb every RNG stream. Recreating modules alone
            # must not accidentally make a missing restore appear correct.
            seed_training_rng(spec.seed + 90000)
            rng_probe(device)
            event("restore_start", arm=arm, checkpoint=str(path), checkpoint_sha256=file_sha256(path))
            loaded = load_torch(path)
            first_comparison = compare_trees(first, loaded)
            scorer, head, parameters, optimizer = construct(arm)
            scorer.load_state_dict(loaded["scorer"], strict=True)
            if head is not None:
                head.load_state_dict(loaded["head"], strict=True)
            optimizer.load_state_dict(loaded["optimizer"])
            restore_rng(loaded["rng"])
            if loaded["next_sample_cursor"] != 8 or loaded["next_update"] != 2 or loaded["next_alpha"] != spec.alpha(2):
                raise ValueError("engineering resume cursor/annealing differs from the saved boundary")
            event("restore_end", arm=arm, state_sha256=tree_sha256(loaded), next_sample_cursor=8,
                  next_update=2, next_alpha=spec.alpha(2))
            resumed_rng_probe = rng_probe(device)
            event("rng_probe", arm=arm, branch="resumed", value_sha256=tree_sha256(resumed_rng_probe))
            step(scorer, head, parameters, optimizer, 2, arm=arm, branch="resumed")
            resumed = snapshot(scorer, head, optimizer, 2)
            resumed_path = run_root / arm / "resumed_step2.pt"
            save(resumed_path, resumed, arm=arm, label="resumed_step2")
            comparisons = {name: compare_trees(continuous[name], resumed[name])
                           for name in ("scorer", "head", "optimizer", "rng")}
            comparisons["rng_probe"] = compare_trees(continuous_rng_probe, resumed_rng_probe)
            checks = {name + "_equal": row["equal"] for name, row in comparisons.items()}
            checks.update(next_sample_cursor_equal=continuous["next_sample_cursor"] == resumed["next_sample_cursor"] == 16,
                scheduler_position_equal=(continuous["completed_update"], continuous["next_update"], continuous["next_alpha"])
                    == (resumed["completed_update"], resumed["next_update"], resumed["next_alpha"]),
                step1_snapshot_equal=first_comparison["equal"],
                die_updated=initial_sha != tensor_signature(first["scorer"]) != tensor_signature(continuous["scorer"]),
                frozen_model_unchanged=parameter_fingerprint(modules) == frozen_before,
                vla_gradients_absent=all(not p.requires_grad and p.grad is None for module in modules.values() for p in module.parameters()))
            row = {"arm": arm, "checks": checks, "comparisons": comparisons,
                "initial_scorer_sha256": initial_sha, "sample_order_sha256": json_signature(order),
                "planned_updates": 5000, "completed_probe_updates": 2, "next_sample_cursor": 16,
                "forward_backward_samples_including_replayed_step": 24,
                "step1_checkpoint": str(path), "step1_checkpoint_sha256": file_sha256(path),
                "continuous_step2_checkpoint": str(reference_path), "continuous_step2_sha256": file_sha256(reference_path),
                "resumed_step2_checkpoint": str(resumed_path), "resumed_step2_sha256": file_sha256(resumed_path)}
            arms[arm] = row
            event("compare", arm=arm, checks=checks,
                  component_hashes={key: {k: value[k] for k in ("reference_sha256", "resumed_sha256")} for key, value in comparisons.items()})
            event("arm_end", arm=arm, status="passed" if all(checks.values()) else "failed")
            del scorer, head, parameters, optimizer, first, loaded, continuous, resumed
            gc.collect()
        passed = all(all(row["checks"].values()) for row in arms.values())
        matched = arms["A"]["initial_scorer_sha256"] == arms["B"]["initial_scorer_sha256"]
        passed = passed and matched
        event("probe_end", status="passed" if passed else "failed", actual_forward_backward_samples=48,
              matched_ab_initialization=matched, seconds=time.perf_counter() - started)
        report = {"schema": FORMAL_SCHEMA, "kind": "resume_acceptance", "probe_version": PROBE_VERSION,
            "status": "passed" if passed else "failed", "execution": "real_frozen_openvla_slurm" if real_gpu else "synthetic_cpu",
            "suite": config["suite"], "model_revision": config["model_revision"], "stats_key": config["stats_key"],
            "accepted_pair_config": config, "accepted_pair_id": json_signature(config),
            "window_manifest_sha256": window_manifest_sha256, "input_acceptance_sha256": input_acceptance_sha256,
            "source_files": source_files, "frozen_model_sha256": frozen_before, "selected_windows": windows,
            "planned_updates": 5000, "validation_updates": spec.validation_updates, "selection_metric": FORMAL_METRIC,
            "selection_tie_break": "earliest_update", "alpha_first": spec.alpha(1), "alpha_last": spec.alpha(5000),
            "alpha_probe_updates": [spec.alpha(1), spec.alpha(2)], "effective_batch": 8,
            "arms": arms, "matched_ab_initialization": matched, "formal_selector_produced": False,
            "engineering_weights_reused_for_training": False, "test_opened": False,
            "comparison": "bitwise equality; no numeric tolerance applied", "training_numerics": dict(FORMAL_NUMERICS),
            "actual_forward_backward_samples": 48, "job_id": str(job_id),
            "checkpoint_root": str(run_root), "wall_seconds": time.perf_counter() - started,
            "journal_bytes": events_path.stat().st_size, "journal_sha256": file_sha256(events_path),
            "torch_version": str(torch.__version__), "cuda_version": torch.version.cuda,
            "gpu_name": torch.cuda.get_device_name(device) if real_gpu else None,
            "peak_cuda_memory_allocated_bytes": torch.cuda.max_memory_allocated(device) if real_gpu else 0}
        return report
    except BaseException as error:
        event("probe_failed", error_type=type(error).__name__, error=str(error), seconds=time.perf_counter() - started)
        atomic_json_save(events_path.parent / "resume_acceptance_failure.json",
            {"schema": FORMAL_SCHEMA, "status": "failed", "error_type": type(error).__name__, "error": str(error),
             "arms_completed": arms, "job_id": str(job_id), "wall_seconds": time.perf_counter() - started,
             "journal_sha256": file_sha256(events_path), "checkpoint_root": str(run_root)})
        raise
    finally:
        restore_rng(base_rng)


def require_formal_resume_acceptance(report, *, config, window_manifest_sha256, input_acceptance_sha256,
        source_files, selected_windows, frozen_model_sha256):
    accepted = report.get("accepted_pair_config", {})
    strip = lambda value: {k: v for k, v in value.items() if k not in ("seed", "run_id", "tokens_per_camera")}
    if (accepted.get("seed") != 17 or accepted.get("tokens_per_camera") != 64
            or config.get("seed") not in (17, 23, 41) or config.get("tokens_per_camera") not in (32, 64, 128)
            or strip(accepted) != strip(config)):
        raise ValueError("formal resume gate permits only registered seed/budget/run_id differences")
    expected = {"schema": FORMAL_SCHEMA, "kind": "resume_acceptance", "probe_version": PROBE_VERSION,
        "status": "passed", "execution": "real_frozen_openvla_slurm", "suite": config["suite"],
        "model_revision": config["model_revision"], "stats_key": config["stats_key"],
        "accepted_pair_id": json_signature(accepted), "window_manifest_sha256": window_manifest_sha256,
        "input_acceptance_sha256": input_acceptance_sha256, "source_files": source_files,
        "frozen_model_sha256": frozen_model_sha256, "selected_windows": selected_windows,
        "planned_updates": 5000, "validation_updates": list(range(0, 5001, 500)),
        "selection_metric": FORMAL_METRIC, "selection_tie_break": "earliest_update",
        "alpha_first": 2., "alpha_last": .1, "effective_batch": 8, "matched_ab_initialization": True,
        "formal_selector_produced": False, "engineering_weights_reused_for_training": False,
        "test_opened": False, "actual_forward_backward_samples": 48, "training_numerics": dict(FORMAL_NUMERICS)}
    if any(report.get(key) != value for key, value in expected.items()):
        raise ValueError("formal real-GPU resume gate identity/plan/checks failed")
    arms = report.get("arms", {})
    if set(arms) != {"A", "B"}:
        raise ValueError("formal resume gate requires both matched arms")
    for arm, row in arms.items():
        if row.get("arm") != arm or any(row.get("checks", {}).get(key) is not True for key in CHECKS):
            raise ValueError("formal optimizer/RNG/model resume was not bitwise equivalent")
        if (row.get("planned_updates") != 5000 or row.get("completed_probe_updates") != 2
                or row.get("next_sample_cursor") != 16 or row.get("forward_backward_samples_including_replayed_step") != 24):
            raise ValueError("formal resume probe skipped required matched sample work")
        for name in ("scorer", "head", "optimizer", "rng", "rng_probe"):
            value = row.get("comparisons", {}).get(name, {})
            digest = value.get("reference_sha256")
            if (value.get("equal") is not True or value.get("differences") != []
                    or not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest)
                    or digest != value.get("resumed_sha256")):
                raise ValueError("formal resume component evidence differs")
    if arms["A"]["initial_scorer_sha256"] != arms["B"]["initial_scorer_sha256"] or arms["A"]["sample_order_sha256"] != arms["B"]["sample_order_sha256"]:
        raise ValueError("formal engineering A/B initialization/order differs")


def verify_resume_journal(path, report):
    path = Path(path)
    if path.stat().st_size != report.get("journal_bytes") or file_sha256(path) != report.get("journal_sha256"):
        raise ValueError("formal resume journal identity changed")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if not rows or rows[0].get("event") != "probe_start" or rows[-1].get("event") != "probe_end":
        raise ValueError("resume journal does not contain a complete bounded probe")
    if any(row.get("job_id") != report.get("job_id") or row.get("probe_version") != PROBE_VERSION
           or row.get("suite") != report.get("suite") for row in rows):
        raise ValueError("resume journal mixes jobs/implementations")
    if (rows[0].get("selected_windows") != report["selected_windows"]
            or rows[0].get("frozen_model_sha256") != report["frozen_model_sha256"]
            or rows[0].get("pair_config_sha256") != report["accepted_pair_id"]
            or rows[0].get("source_sha256") != json_signature(report["source_files"])
            or rows[0].get("execution") != report["execution"]
            or rows[0].get("window_manifest_sha256") != report["window_manifest_sha256"]
            or rows[0].get("input_acceptance_sha256") != report["input_acceptance_sha256"]
            or rows[0].get("planned_updates") != 5000 or rows[0].get("effective_batch") != 8
            or rows[0].get("sample_order") != [row["window_id"] for row in report["selected_windows"]] * 8):
        raise ValueError("resume journal probe identity differs from report")
    expected_global = [("probe_start", None)]
    for arm in ("A", "B"):
        selected = [row for row in rows if row.get("arm") == arm]
        step_events = ["step_start", *[event for _ in range(8) for event in ("sample_start", "sample_end")], "step_end"]
        save_events = ["save_start", "save_end"]
        expected_events = ["arm_start", *step_events, *save_events, "rng_probe", *step_events,
                           *save_events, "restore_start", "restore_end", "rng_probe", *step_events,
                           *save_events, "compare", "arm_end"]
        expected_global.extend((name, arm) for name in expected_events)
        if [row["event"] for row in selected] != expected_events:
            raise ValueError("resume journal step/save/restore event order is incomplete")
        expected_steps = [("continuous", 1), ("continuous", 2), ("resumed", 2)]
        for event in ("step_start", "step_end"):
            actual = [(row.get("branch"), row.get("update")) for row in selected if row["event"] == event]
            if actual != expected_steps:
                raise ValueError("resume journal missing/reordered/duplicated optimizer steps")
        for branch, update in expected_steps:
            subset = [row for row in selected if row.get("branch") == branch and row.get("update") == update]
            samples = [row for row in subset if row["event"] in ("sample_start", "sample_end")]
            if [(row["event"], row.get("micro_batch_index")) for row in samples] != [
                    (event, index) for index in range(8) for event in ("sample_start", "sample_end")]:
                raise ValueError("resume journal contains incomplete/repeated micro-batches")
            expected_ids = [row["window_id"] for row in report["selected_windows"]] * 4
            if any([row.get("window_id") for row in samples if row["event"] == event] != expected_ids
                   for event in ("sample_start", "sample_end")):
                raise ValueError("resume journal changed the two fixed-window sample sequence")
            start = next(row for row in subset if row["event"] == "step_start")
            end = next(row for row in subset if row["event"] == "step_end")
            if (start.get("window_ids") != expected_ids or start.get("next_sample_cursor") != (update - 1) * 8
                    or end.get("next_sample_cursor") != update * 8 or end.get("forward_backward_samples") != 8
                    or start.get("alpha") != report["alpha_probe_updates"][update - 1]
                    or not math.isfinite(end.get("grad_norm", float("nan"))) or end["grad_norm"] <= 0):
                raise ValueError("resume journal optimizer/cursor/annealing evidence differs")
        saves = [row for row in selected if row["event"] == "save_end"]
        if [row.get("label") for row in saves] != ["step1", "continuous_step2", "resumed_step2"]:
            raise ValueError("resume journal lacks checkpoint serialization evidence")
        for row, field in zip(saves, ("step1_checkpoint_sha256", "continuous_step2_sha256", "resumed_step2_sha256")):
            if row.get("checkpoint_sha256") != report["arms"][arm][field]:
                raise ValueError("resume journal checkpoint hashes differ")
        starts = [row for row in selected if row["event"] == "save_start"]
        path_fields = ("step1_checkpoint", "continuous_step2_checkpoint", "resumed_step2_checkpoint")
        if any(start.get("checkpoint") != end.get("checkpoint") or end.get("checkpoint") != report["arms"][arm][field]
               or start.get("label") != end.get("label") for start, end, field in zip(starts, saves, path_fields)):
            raise ValueError("resume journal saved checkpoint paths differ")
        restored = next(row for row in selected if row["event"] == "restore_end")
        restore_start = next(row for row in selected if row["event"] == "restore_start")
        if (restore_start.get("checkpoint") != saves[0]["checkpoint"]
                or restore_start.get("checkpoint_sha256") != saves[0]["checkpoint_sha256"]
                or restored.get("state_sha256") != saves[0]["state_sha256"]
                or restored.get("next_sample_cursor") != 8 or restored.get("next_update") != 2
                or restored.get("next_alpha") != report["alpha_probe_updates"][1]):
            raise ValueError("resume journal restored a different snapshot or cursor")
        sentinels = [row for row in selected if row["event"] == "rng_probe"]
        comparison = report["arms"][arm]["comparisons"]["rng_probe"]
        if ([row.get("branch") for row in sentinels] != ["continuous", "resumed"]
                or sentinels[0].get("value_sha256") != comparison["reference_sha256"]
                or sentinels[1].get("value_sha256") != comparison["resumed_sha256"]):
            raise ValueError("resume journal RNG sentinel evidence differs")
        compare = [row for row in selected if row["event"] == "compare"]
        hashes = {key: {k: value[k] for k in ("reference_sha256", "resumed_sha256")}
                  for key, value in report["arms"][arm]["comparisons"].items()}
        if (len(compare) != 1 or compare[0].get("checks") != report["arms"][arm]["checks"]
                or compare[0].get("component_hashes") != hashes
                or selected[-1].get("status") != ("passed" if all(report["arms"][arm]["checks"].values()) else "failed")):
            raise ValueError("resume journal comparison evidence differs")
    expected_global.append(("probe_end", None))
    if [(row["event"], row.get("arm")) for row in rows] != expected_global:
        raise ValueError("resume journal global event order or unexpected work differs")
    if (rows[-1].get("status") != report["status"] or rows[-1].get("actual_forward_backward_samples") != 48
            or rows[-1].get("matched_ab_initialization") != report["matched_ab_initialization"]):
        raise ValueError("resume journal final status/cost differs")
    return {"status": "verified", "samples": 48, "events": len(rows), "journal_sha256": file_sha256(path)}

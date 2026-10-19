"""G1 signed interventions and exhaustive staged teacher diagnostics.

All calls are one observation (B=1), with the real packed policy supplied as a
callback. The action journal contains no model weights and can resume across
processes. This module computes offline normalized-action diagnostics, not
closed-loop quality or deployment latency.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Callable, Mapping, Sequence

import torch

from cti_vla.labeling.sampling import DiagnosticSet, camera_balanced_set, named_seed

DIAGNOSTICS_VERSION = "g1-packed-signed-fixed-full-mean-v1"
JOURNAL_VERSION = 1


def json_signature(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def tensor_signature(tensors: Mapping[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(tensors.items()):
        value = value.detach().cpu().contiguous()
        digest.update(json.dumps([name, str(value.dtype), list(value.shape)]).encode())
        digest.update(value.view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def atomic_json(path: str | Path, payload: object) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + f".{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def require_g0(report: Mapping, *, model_revision: str, input_version: str,
               packing_version: str) -> None:
    """A smoke report or a user-provided boolean cannot bypass formal G0."""
    if report.get("stage") != "G0" or report.get("status") != "passed":
        raise ValueError("formal G1 requires a passed G0 report")
    for key in ("dense_parity", "closed_loop", "initial_state_split"):
        if not isinstance(report.get(key), Mapping) or report[key].get("passed") is not True:
            raise ValueError(f"G0 {key} did not pass")
    loop = report["closed_loop"]
    if type(loop.get("num_tasks")) is not int or loop["num_tasks"] < 3 or type(loop.get("episodes_per_task")) is not int or loop["episodes_per_task"] < 5:
        raise ValueError("G0 must include at least three tasks and five states per task")
    expected = {"model_revision": model_revision, "input_version": input_version,
                "packing_version": packing_version}
    if any(report.get("provenance", {}).get(key) != value for key, value in expected.items()):
        raise ValueError("G0 provenance does not match this model/input/packing protocol")


class ActionQueryCache:
    """Actual calls, cache hits, failures and original lengths in one ledger.

    `forward(full_visual, indices[1,K])` must use the common normalized-action
    policy. Replacement modifies only one original visual feature before the
    same gather/packing callback. The fixed means are computed in FP32 from the
    original full features and cast back to their input dtype.

    A journal writes start/completion events durably. An interrupted start has
    an unknown completion status: it is counted as an attempted call, never a
    completed query, and its cost/time is explicitly marked unknown. Restarted
    attempts consume the same fixed budget; no hidden free retries.
    """

    def __init__(self, visual: torch.Tensor, forward: Callable, *, identity: Mapping,
                 num_cameras: int = 2, action_shape: tuple[int, int] = (8, 7),
                 max_sample_forwards: int = 1100, journal_path: str | Path | None = None,
                 sequence_overhead_tokens: int | None = None):
        if visual.ndim != 3 or visual.shape[0] != 1 or not visual.is_floating_point() or not torch.isfinite(visual).all():
            raise ValueError("G1 visual features must be finite floating [1,N,D]")
        if type(num_cameras) is not int or num_cameras <= 0 or visual.shape[1] % num_cameras:
            raise ValueError("visual tokens must be camera-major with equal camera sizes")
        if max_sample_forwards <= 0:
            raise ValueError("query budget must be positive")
        self.visual = visual.detach()
        self.forward = forward
        self.num_cameras = num_cameras
        self.camera_size = visual.shape[1] // num_cameras
        self.full_indices = tuple(range(visual.shape[1]))
        self.action_shape = action_shape
        self.max_sample_forwards = max_sample_forwards
        self.sequence_overhead_tokens = sequence_overhead_tokens
        self.fixed_means = self.visual.float().reshape(1, num_cameras, self.camera_size, -1).mean(2).to(visual.dtype)
        self.identity = dict(identity, diagnostics_version=DIAGNOSTICS_VERSION,
                             visual_sha256=tensor_signature({"visual": visual}),
                             num_cameras=num_cameras, action_shape=list(action_shape),
                             sequence_overhead_tokens=sequence_overhead_tokens)
        self.cache: dict[str, torch.Tensor] = {}
        self.requests: list[dict] = []
        self.calls: dict[int, dict] = {}
        self.journal_path = Path(journal_path) if journal_path is not None else None
        self.journal_io_seconds = 0.0
        self.recovered_from_journal = False
        if self.journal_path is not None:
            self.journal_path.parent.mkdir(parents=True, exist_ok=True)
            if self.journal_path.exists():
                self._restore()
                self.recovered_from_journal = True
            else:
                self._append({"event": "identity", "schema_version": JOURNAL_VERSION,
                              "identity": self.identity, "identity_sha256": json_signature(self.identity)})

    def _append(self, event: dict) -> None:
        if self.journal_path is None:
            return
        started = time.perf_counter()
        with self.journal_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.journal_io_seconds += time.perf_counter() - started

    def _restore(self) -> None:
        # Reject torn/corrupted journals. Do not silently discard a charged call.
        with self.journal_path.open(encoding="utf-8") as handle:
            events = [json.loads(line) for line in handle]
        if not events or events[0] != {"event": "identity", "schema_version": JOURNAL_VERSION,
                                      "identity": self.identity, "identity_sha256": json_signature(self.identity)}:
            raise ValueError("query journal identity/schema mismatch")
        for event in events[1:]:
            kind = event.get("event")
            if kind == "start":
                if event["call_id"] in self.calls:
                    raise ValueError("duplicate query journal call ID")
                self.calls[event["call_id"]] = dict(event, status="interrupted_unknown")
                self.requests.append(event)
            elif kind in ("complete", "failed"):
                call = self.calls[event["call_id"]]
                if call["status"] != "interrupted_unknown":
                    raise ValueError("duplicate query completion")
                call.update(event, status=kind)
                if kind == "complete":
                    action = torch.tensor(event["action"], dtype=torch.float32)
                    self._validate_action(action)
                    if event["action_sha256"] != tensor_signature({"action": action}):
                        raise ValueError("query action checksum mismatch")
                    self.cache[call["key"]] = action
            elif kind == "hit":
                if event["key"] not in self.cache:
                    raise ValueError("cache hit preceding a completed action")
                self.requests.append(event)
            else:
                raise ValueError("unknown query journal event")

    def _validate_action(self, action: torch.Tensor) -> None:
        if not isinstance(action, torch.Tensor) or tuple(action.shape) != (1, *self.action_shape) or not action.is_floating_point() or not bool(torch.isfinite(action).all()):
            raise ValueError(f"callback must return finite normalized [1,{self.action_shape}] actions")

    def _sync(self) -> None:
        if self.visual.device.type == "cuda":
            torch.cuda.synchronize(self.visual.device)

    def query(self, retained: Sequence[int], *, category: str,
              replace_index: int | None = None, repeat_id: str | None = None) -> torch.Tensor:
        retained = tuple(retained)
        if not retained or any(type(i) is not int or not 0 <= i < len(self.full_indices) for i in retained) or tuple(sorted(set(retained))) != retained:
            raise ValueError("retained indices must be nonempty unique ascending original indices")
        if replace_index is not None and (type(replace_index) is not int or replace_index not in retained):
            raise ValueError("replacement candidate must be retained")
        key = json_signature({"retained": retained, "replace_index": replace_index, "repeat_id": repeat_id})
        meta = {"key": key, "category": category, "retained_indices": list(retained),
                "replace_index": replace_index, "repeat_id": repeat_id,
                "physical_visual_tokens": len(retained),
                "total_sequence_tokens": (len(retained) + self.sequence_overhead_tokens
                                           if self.sequence_overhead_tokens is not None else None)}
        if key in self.cache:
            event = dict(meta, event="hit")
            self.requests.append(event)
            self._append(event)
            return self.cache[key].clone()
        if len(self.calls) >= self.max_sample_forwards:
            raise RuntimeError("per-observation teacher sample-forward budget exhausted")
        source = self.visual
        if replace_index is not None:
            source = self.visual.clone()
            source[:, replace_index] = self.fixed_means[:, replace_index // self.camera_size]
        indices = torch.tensor([retained], device=source.device, dtype=torch.long)
        call_id = len(self.calls)
        event = dict(meta, event="start", call_id=call_id)
        self._append(event)
        self.requests.append(event)
        self.calls[call_id] = dict(event, status="interrupted_unknown")
        self._sync()
        started = time.perf_counter()
        try:
            with torch.no_grad():
                action = self.forward(source, indices)
            self._sync()
            elapsed = time.perf_counter() - started
            self._validate_action(action)
            action = action.detach().float().cpu().clone()
            event = {"event": "complete", "call_id": call_id, "seconds": elapsed,
                     "action": action.tolist(), "action_sha256": tensor_signature({"action": action})}
        except Exception as error:
            event = {"event": "failed", "call_id": call_id,
                     "seconds": time.perf_counter() - started,
                     "error": f"{type(error).__name__}: {error}"}
            self._append(event)
            self.calls[call_id].update(event, status="failed")
            raise
        self._append(event)
        self.calls[call_id].update(event, status="complete")
        self.cache[key] = action
        return action.clone()

    def ledger(self) -> dict:
        return _query_cost_ledger(self.calls, self.requests, self.journal_path,
                                  self.journal_io_seconds, self.recovered_from_journal)


def _query_cost_ledger(calls_by_id: Mapping, requests: Sequence[dict], journal_path: Path | None,
                       journal_io_seconds: float = 0.0, recovered_from_journal: bool = False) -> dict:
        calls = list(calls_by_id.values())
        completed = [c for c in calls if c["status"] == "complete"]
        unknown = [c for c in calls if c["status"] == "interrupted_unknown"]
        by_length = {}
        for count in sorted({c["physical_visual_tokens"] for c in calls}):
            group = [c for c in calls if c["physical_visual_tokens"] == count]
            by_length[str(count)] = {"api_calls_attempted": len(group), "sample_forwards_attempted": len(group),
                                    "sample_forwards_completed": sum(c["status"] == "complete" for c in group),
                                    "known_policy_seconds": sum(c.get("seconds", 0.0) for c in group)}
        return {"batch_size": 1, "requests": len(requests),
                "cache_hits": sum(r["event"] == "hit" for r in requests),
                "api_calls_attempted": len(calls), "sample_forwards_attempted": len(calls),
                "sample_forwards_completed": len(completed),
                "failed_calls": sum(c["status"] == "failed" for c in calls),
                "interrupted_calls_unknown_completion": len(unknown),
                "known_policy_seconds": sum(c.get("seconds", 0.0) for c in calls),
                "policy_seconds_total": None if unknown else sum(c.get("seconds", 0.0) for c in calls),
                "by_visual_length": by_length,
                "attempts_by_category": dict(Counter(c["category"] for c in calls)),
                "unique_cached_actions": len({c["key"] for c in completed}),
                "journal_bytes": journal_path.stat().st_size if journal_path is not None else 0,
                "current_process_journal_io_seconds": journal_io_seconds,
                "recovered_from_journal": recovered_from_journal,
                "timing_scope": "Synchronized packed-policy callback from cached projected features; excludes vision/preprocessing, CPU action copy and journal IO. Not deployment latency."}


def read_query_journal_ledger(path: str | Path, *, expected_fields: Mapping) -> dict:
    """Reconcile charges even if a process died before observation finalization.

    Does not execute a model or need visual features. The expected observation
    and config fields prevent accidentally summing another run's journal.
    """
    path = Path(path)
    with path.open(encoding="utf-8") as handle:
        events = [json.loads(line) for line in handle]
    if not events or events[0].get("event") != "identity" or events[0].get("schema_version") != JOURNAL_VERSION:
        raise ValueError("invalid query journal header")
    identity = events[0]["identity"]
    if events[0].get("identity_sha256") != json_signature(identity) or any(identity.get(k) != v for k, v in expected_fields.items()):
        raise ValueError("query journal belongs to different observation/config")
    calls, requests, completed_keys = {}, [], set()
    for event in events[1:]:
        kind = event.get("event")
        if kind == "start":
            if event["call_id"] != len(calls):
                raise ValueError("nonsequential or duplicate query call ID")
            calls[event["call_id"]] = dict(event, status="interrupted_unknown")
            requests.append(event)
        elif kind in ("complete", "failed"):
            call = calls[event["call_id"]]
            if call["status"] != "interrupted_unknown" or not math.isfinite(event["seconds"]) or event["seconds"] < 0:
                raise ValueError("duplicate completion or invalid query timing")
            call.update(event, status=kind)
            if kind == "complete":
                completed_keys.add(call["key"])
        elif kind == "hit":
            if event["key"] not in completed_keys:
                raise ValueError("query journal cache hit lacks completed action")
            requests.append(event)
        else:
            raise ValueError("unrecognized query journal event")
    return _query_cost_ledger(calls, requests, path)


def action_error(action: torch.Tensor, reference: torch.Tensor) -> dict:
    delta = (action.float() - reference.float()).abs()[0]
    if delta.ndim != 2 or delta.shape[-1] != 7:
        raise ValueError("normalized action diagnostics require [1,chunk,7]")
    return {"mean_l1": float(delta.mean()), "by_chunk_step": delta.mean(-1).tolist(),
            "by_action_dimension": delta.mean(0).tolist(),
            "position_mean_l1": float(delta[:, :3].mean()),
            "rotation_mean_l1": float(delta[:, 3:6].mean()),
            "gripper_mean_l1": float(delta[:, 6].mean())}


def _rank(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: (values[i], i))
    ranks = [0.] * len(values)
    start = 0
    while start < len(values):
        stop = start + 1
        while stop < len(values) and values[order[stop]] == values[order[start]]:
            stop += 1
        for j in range(start, stop):
            ranks[order[j]] = (start + stop - 1) / 2
        start = stop
    return ranks


def compare_labels(left: Sequence[float], right: Sequence[float], *, noise_tolerance: float) -> dict:
    if len(left) != len(right) or not left or noise_tolerance < 0:
        raise ValueError("label comparisons require matched nonempty candidates and nonnegative tolerance")
    x, y = _rank(left), _rank(right)
    mx, my = sum(x) / len(x), sum(y) / len(y)
    denominator = math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
    reliable = [(a, b) for a, b in zip(left, right) if abs(a) > noise_tolerance and abs(b) > noise_tolerance]
    return {"spearman": sum((a - mx) * (b - my) for a, b in zip(x, y)) / denominator if denominator else None,
            "mean_absolute_label_difference": sum(abs(a - b) for a, b in zip(left, right)) / len(left),
            "sign_flips_outside_noise": sum((a > 0) != (b > 0) for a, b in reliable),
            "sign_comparison_count": len(reliable), "candidate_count": len(left),
            "noise_tolerance": noise_tolerance}


def run_intervention_panel(oracle: ActionQueryCache, panel: Sequence[DiagnosticSet], *, noise_tolerance: float = 1e-6) -> dict:
    reference = oracle.query(oracle.full_indices, category="full_reference")
    records = []
    for item in panel:
        if len(set(item.candidate_indices)) != len(item.candidate_indices) or not set(item.candidate_indices).issubset(item.retained_indices):
            raise ValueError("panel candidates must be unique members of S")
        base = oracle.query(item.retained_indices, category="panel_base")
        base_error = action_error(base, reference)
        deleted_error, replaced_error, deletions, replacements = [], [], [], []
        for candidate in item.candidate_indices:
            deleted = oracle.query(tuple(i for i in item.retained_indices if i != candidate), category="panel_deletion")
            replaced = oracle.query(item.retained_indices, replace_index=candidate, category="panel_replacement")
            de, re = action_error(deleted, reference), action_error(replaced, reference)
            deletions.append(de["mean_l1"] - base_error["mean_l1"])
            replacements.append(re["mean_l1"] - base_error["mean_l1"])
            deleted_error.append(de)
            replaced_error.append(re)
        records.append({"name": item.name, "retained_indices": list(item.retained_indices),
                        "candidate_indices": list(item.candidate_indices), "base_error": base_error,
                        "deletion_labels": deletions, "replacement_labels": replacements,
                        "deleted_error": deleted_error, "replaced_error": replaced_error,
                        "deletion_vs_replacement": compare_labels(deletions, replacements, noise_tolerance=noise_tolerance)})
    if records and any(row["candidate_indices"] != records[0]["candidate_indices"] for row in records):
        raise ValueError("D2 requires identical fixed-anchor candidates across sets")
    return {"full_action": reference.tolist(), "sets": records,
            "full_vs_partial_deletion": {row["name"]: compare_labels(records[0]["deletion_labels"], row["deletion_labels"], noise_tolerance=noise_tolerance)
                                         for row in records[1:]},
            "replacement_definition": "Only candidate in physically packed S becomes fixed FP32 full-camera mean cast to feature dtype; every other retained feature, original position and mask is unchanged."}


def _balanced_topk(scores: Mapping[int, float], *, oracle: ActionQueryCache, per_camera: int) -> tuple[int, ...]:
    retained = []
    for camera in range(oracle.num_cameras):
        pool = [i for i in scores if i // oracle.camera_size == camera]
        if len(pool) < per_camera:
            raise ValueError("insufficient current-set tokens for camera budget")
        retained.extend(sorted(pool, key=lambda i: (-scores[i], i))[:per_camera])
    return tuple(sorted(retained))


def run_exact_selection(oracle: ActionQueryCache, *, sample_id: object, seed: int = 17,
                        per_camera_budgets: tuple[int, ...] = (128, 64, 32),
                        grid_shape: tuple[int, int] = (16, 16),
                        random_seeds: tuple[int, ...] = (17, 23, 41)) -> dict:
    if math.prod(grid_shape) != oracle.camera_size or not per_camera_budgets or any(a <= b for a, b in zip((oracle.camera_size, *per_camera_budgets), per_camera_budgets)):
        raise ValueError("exact diagnostic budgets must strictly decrease on this camera grid")
    reference = oracle.query(oracle.full_indices, category="full_reference")
    current, initial_scores = oracle.full_indices, None
    methods: dict[str, list[dict]] = {"teacher_staged": [], "full_loo_static": [], "uniform": []}
    for random_seed in random_seeds:
        methods[f"random_seed_{random_seed}"] = []
    stage_labels = []
    for budget in per_camera_budgets:
        base = oracle.query(current, category="teacher_stage_base")
        base_error = action_error(base, reference)["mean_l1"]
        scores = {}
        for candidate in current:
            deleted = oracle.query(tuple(i for i in current if i != candidate), category="teacher_all_candidates")
            scores[candidate] = action_error(deleted, reference)["mean_l1"] - base_error
        if initial_scores is None:
            initial_scores = scores.copy()
        stage_labels.append({"retained_indices": list(current), "candidate_indices": list(scores),
                             "signed_deletion_labels": list(scores.values()), "base_error": base_error})
        current = _balanced_topk(scores, oracle=oracle, per_camera=budget)
        action = oracle.query(current, category="teacher_stage_evaluation")
        methods["teacher_staged"].append({"keep_count": len(current), "retained_indices": list(current),
                                           "error": action_error(action, reference)})
    for budget in per_camera_budgets:
        sets = {"full_loo_static": _balanced_topk(initial_scores, oracle=oracle, per_camera=budget),
                "uniform": camera_balanced_set(per_camera=budget, grid_shape=grid_shape,
                                               num_cameras=oracle.num_cameras, mode="uniform")}
        sets.update({f"random_seed_{s}": camera_balanced_set(per_camera=budget, grid_shape=grid_shape,
                                                           num_cameras=oracle.num_cameras, mode="random",
                                                           seed=named_seed(seed, sample_id, "exact-random", s, budget))
                     for s in random_seeds})
        for name, retained in sets.items():
            action = oracle.query(retained, category=f"comparison_{name}")
            methods[name].append({"keep_count": len(retained), "retained_indices": list(retained),
                                  "error": action_error(action, reference)})
    if methods["teacher_staged"][0] != methods["full_loo_static"][0]:
        raise AssertionError("initial teacher stage must exactly equal full-LOO static selection")
    return {"methods": methods, "stage_labels": stage_labels, "random_seeds": list(random_seeds),
            "meaning": "Exhaustive current-set marginals at each fixed stage; not globally optimal subset search or a deployment baseline."}


def run_repeatability(oracle: ActionQueryCache, candidate: int) -> dict:
    """Two extra actual calls, with resume-safe keys distinct from cached calls."""
    full = oracle.query(oracle.full_indices, category="full_reference")
    without = tuple(i for i in oracle.full_indices if i != candidate)
    original = oracle.query(without, category="repeatability_cached_intervention")
    full_repeat = oracle.query(oracle.full_indices, category="repeatability_full", repeat_id="g1-repeat-full-1")
    deletion_repeat = oracle.query(without, category="repeatability_deletion", repeat_id="g1-repeat-deletion-1")
    first = action_error(original, full)["mean_l1"]
    second = action_error(deletion_repeat, full_repeat)["mean_l1"]
    return {"candidate_index": candidate, "first_full_deletion_label": first,
            "repeat_full_deletion_label": second, "label_absolute_difference": abs(first - second),
            "full_action_max_abs_difference": float((full - full_repeat).abs().max()),
            "deleted_action_max_abs_difference": float((original - deletion_repeat).abs().max())}

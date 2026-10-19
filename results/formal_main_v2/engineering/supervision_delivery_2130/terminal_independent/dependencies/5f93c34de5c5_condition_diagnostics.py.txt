"""Preregistered legal-language D1 diagnostics with independent full teachers."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

import torch

from cti_vla.data.experiment_protocol import verify_payload
from cti_vla.evaluation.teacher_diagnostics import ActionQueryCache, action_error

PAIR_NAMESPACE = "cti-vla:d1-legal-instruction-pairs:v1"
D1_VERSION = "d1-full512-eight-shared-deletions-independent-condition-reference-retry-v2"
FIXED_CANDIDATES = (85, 91, 181, 187, 341, 347, 437, 443)
DEFAULT_MAX_ATTEMPTS_PER_CONDITION = 12


def validate_attempt_cap(value: int) -> None:
    if type(value) is not int or not 9 <= value <= 32:
        raise ValueError("D1 attempt cap must be an integer from 9 through 32")


def sum_query_costs(costs: Sequence[Mapping]) -> dict:
    total = {key: sum(row[key] for row in costs) for key in (
        "api_calls_attempted", "sample_forwards_attempted", "sample_forwards_completed", "cache_hits",
        "failed_calls", "interrupted_calls_unknown_completion", "known_policy_seconds", "journal_bytes")}
    total["unique_successful_queries"] = sum(row["unique_cached_actions"] for row in costs)
    total["policy_seconds_total"] = (None if total["interrupted_calls_unknown_completion"]
                                     else total["known_policy_seconds"])
    return total


def validate_pair_manifest(payload: Mapping, protocol, *, input_version: str) -> None:
    verify_payload(dict(payload), PAIR_NAMESPACE)
    if payload["schema_version"] != 1 or payload["input_version"] != input_version or payload["protocol_signature"] != protocol.payload["content_signature"]:
        raise ValueError("D1 manifest input/data protocol mismatch")
    if payload["labels_seen_before_freeze"] is not False or payload["formal_d1_queries_before_freeze"] != 0:
        raise ValueError("D1 pairs must be frozen before viewing any D1 labels")
    pairs = payload["pairs"]
    if not isinstance(pairs, list) or len(pairs) > 10 or len({row["pair_id"] for row in pairs}) != len(pairs) or len({row["sample_id"] for row in pairs}) != len(pairs):
        raise ValueError("D1 needs at most ten unique observation/pair IDs")
    if not pairs:
        if payload["status"] != "not_applicable" or not payload["exclusions"]:
            raise ValueError("empty D1 panel requires explicit not_applicable exclusions")
        return
    if payload["status"] != "frozen_before_labels":
        raise ValueError("D1 pairs have not been frozen after visual review")
    for pair in pairs:
        episode, sample = protocol.require_sample(pair["episode_id"], pair["step_index"], split="train")
        if sample.sample_id != pair["sample_id"] or pair["split"] != "train" or pair["step_index"] != 0 or sample.stage != "early":
            raise ValueError("D1 pair is not a registered early train step-zero observation")
        if pair["source_shard"] != episode.source_shard or pair["record_index"] != episode.record_index:
            raise ValueError("D1 pair storage coordinates mismatch")
        instructions, targets = pair["instructions"], pair["target_object_ids"]
        if len(instructions) != 2 or len(set(instructions)) != 2 or any(not isinstance(value, str) or not value.strip() for value in instructions):
            raise ValueError("D1 requires two distinct nonempty legal instructions")
        if instructions[0] != episode.task_name or targets != ["akita_black_bowl_1", "akita_black_bowl_2"]:
            raise ValueError("D1 original task/target object identity mismatch")
        if pair["target_goal_predicates"] != ["On(akita_black_bowl_1,plate_1)", "On(akita_black_bowl_2,plate_1)"]:
            raise ValueError("D1 counterfactual physical targets are not explicit")
        if pair["candidate_indices"] != list(FIXED_CANDIDATES) or pair["retained_set"] != "full512":
            raise ValueError("D1 requires the shared fixed eight-candidate/full512 panel")
        review = pair["visual_review"]
        if any(review[key] is not True for key in ("approved", "formal_crops_reviewed", "two_unique_targets_visible", "destination_visible_and_free")):
            raise ValueError("D1 pair lacks formal-image legality review")
        if not review["evidence"] or not pair["bddl_sha256"]:
            raise ValueError("D1 physical legality evidence is missing")
        for view in ("main", "wrist"):
            values = pair["views"][view]
            if values["shape"] != [224, 224, 3] or values["official_reference_equal"] is not True:
                raise ValueError("D1 review images do not use verified formal preprocessing")
            for key in ("raw_jpeg_sha256", "rgb_sha256", "png_sha256"):
                value = values[key]
                if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
                    raise ValueError("invalid D1 visual evidence hash")


def run_condition_pair(visual: torch.Tensor, forwards: Sequence, *, identity: Mapping,
                       candidate_indices: Sequence[int] = FIXED_CANDIDATES,
                       journal_directory: str | Path | None = None,
                       sequence_overheads: Sequence[int | None] = (None, None),
                       max_attempts_per_condition: int = DEFAULT_MAX_ATTEMPTS_PER_CONDITION) -> dict:
    """Exactly 18 unique successful queries, with separately bounded attempts.

    Each callback binds its own instruction and the SAME normalized proprio.
    Full references are never shared between conditions. S is always full, so
    the signed E(S-i)-E(S) formula is theoretically nonnegative in this panel.
    Failed/unknown attempts stay charged across restarts. They do not populate
    the successful cache. Exceptions propagate; restart retries that same query
    within the unchanged attempt cap (default 12 per condition).
    """
    validate_attempt_cap(max_attempts_per_condition)
    if visual.ndim != 3 or visual.shape[:2] != (1, 512) or len(forwards) != 2 or len(sequence_overheads) != 2:
        raise ValueError("D1 requires one full512 observation and two condition callbacks")
    if tuple(candidate_indices) != FIXED_CANDIDATES:
        raise ValueError("D1 candidate set must match the frozen panel")
    if len(identity["instructions"]) != 2 or len(set(identity["instructions"])) != 2:
        raise ValueError("D1 cache identity must carry both distinct instructions")
    conditions = []
    for condition, forward in enumerate(forwards):
        journal = Path(journal_directory) / f"condition_{condition}.jsonl" if journal_directory is not None else None
        queries = ActionQueryCache(visual, forward, identity={**identity, "d1_version": D1_VERSION,
                                  "max_attempts_per_condition": max_attempts_per_condition,
                                  "unique_successful_queries_required": 9,
                                  "condition_index": condition, "instruction": identity["instructions"][condition]},
                                  journal_path=journal, max_sample_forwards=max_attempts_per_condition,
                                  sequence_overhead_tokens=sequence_overheads[condition])
        reference = queries.query(queries.full_indices, category="D1_condition_full")
        baseline_error = action_error(reference, reference)
        deletions = []
        for token in candidate_indices:
            retained = tuple(index for index in queries.full_indices if index != token)
            action = queries.query(retained, category="D1_actual_deletion")
            error = action_error(action, reference)
            deletions.append({"source_index": token, "camera_id": token // 256,
                              "physical_visual_tokens": len(retained), "action": action.tolist(),
                              "error": error, "signed_label": error["mean_l1"] - baseline_error["mean_l1"]})
        conditions.append({"condition_index": condition, "instruction": identity["instructions"][condition],
                           "full_reference_action": reference.tolist(), "baseline_error": baseline_error,
                           "deletions": deletions, "cost": queries.ledger()})
    differences = [right["signed_label"] - left["signed_label"] for left, right in zip(conditions[0]["deletions"], conditions[1]["deletions"])]
    total = sum_query_costs([row["cost"] for row in conditions])
    return {"status": "completed", "d1_version": D1_VERSION, "conditions": conditions, "cost": total,
            "unique_successful_queries_required": 18, "max_attempts_per_condition": max_attempts_per_condition,
            "label_difference_condition1_minus_condition0": differences,
            "mean_absolute_label_difference": sum(abs(value) for value in differences) / len(differences),
            "label_definition": "FP32 normalized mean L1(8x7), E_c(full-i)-E_c(full), separate full reference per c",
            "interpretation": "Frozen-teacher label sensitivity to two physically meaningful instructions; not causal language identification, environment success, or a trained-selector benefit."}


__all__ = ["PAIR_NAMESPACE", "D1_VERSION", "FIXED_CANDIDATES", "DEFAULT_MAX_ATTEMPTS_PER_CONDITION",
           "validate_pair_manifest", "validate_attempt_cap", "sum_query_costs", "run_condition_pair"]

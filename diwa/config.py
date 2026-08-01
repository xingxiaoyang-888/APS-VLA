"""Strict loading for the fixed primary DIWA experiment configuration."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from diwa.data.identity import canonical_mapping_signature


REQUIRED_STAGE_A_KEYS = {
    "base_checkpoint",
    "action_chunk_size",
    "action_dim",
    "num_images_in_input",
    "use_proprio",
    "use_l1_regression",
    "use_diffusion",
    "use_film",
    "precision",
    "die_hidden_dim",
    "die_metadata_dim",
    "die_dropout",
    "candidate_num_top",
    "candidate_num_stratified",
    "candidate_num_hard_negative",
    "candidate_audit_size",
    "candidate_audit_frequency_steps",
    "stage_a_learning_rate",
    "stage_a_weight_decay",
    "stage_a_regression_beta",
    "stage_a_ranking_weight",
    "stage_a_ranking_temperature",
    "stage_a_ranking_tie_margin",
    "stage_a_max_grad_norm",
    "teacher_cache_max_samples_per_shard",
    "teacher_cache_max_candidates_per_sample",
    "expansion_min_candidate_top1_coverage",
    "expansion_max_candidate_oracle_regret",
    "expansion_max_full_retention_abs_error",
    "expansion_min_packed_speedup",
    "expansion_min_content_permutation_change",
}


def validate_stage_a_config(config: dict[str, Any]) -> dict[str, Any]:
    if set(config) != REQUIRED_STAGE_A_KEYS:
        missing = sorted(REQUIRED_STAGE_A_KEYS - set(config))
        extra = sorted(set(config) - REQUIRED_STAGE_A_KEYS)
        raise ValueError(f"Stage-A config keys mismatch; missing={missing}, extra={extra}")
    fixed = {
        "base_checkpoint": "moojink/openvla-7b-oft-finetuned-libero-spatial",
        "action_chunk_size": 8,
        "action_dim": 7,
        "num_images_in_input": 2,
        "use_proprio": True,
        "use_l1_regression": True,
        "use_diffusion": False,
        "use_film": False,
        "precision": "bf16",
    }
    mismatches = {key: (config[key], expected) for key, expected in fixed.items() if config[key] != expected}
    if mismatches:
        raise ValueError(f"primary DIWA architecture mismatch: {mismatches}")
    positive = (
        "die_hidden_dim",
        "die_metadata_dim",
        "candidate_num_top",
        "candidate_num_stratified",
        "candidate_num_hard_negative",
        "candidate_audit_size",
        "candidate_audit_frequency_steps",
        "stage_a_learning_rate",
        "stage_a_regression_beta",
        "stage_a_ranking_temperature",
        "stage_a_max_grad_norm",
        "teacher_cache_max_samples_per_shard",
        "teacher_cache_max_candidates_per_sample",
        "expansion_min_packed_speedup",
    )
    if any(
        isinstance(config[key], bool)
        or not isinstance(config[key], (int, float))
        or not math.isfinite(float(config[key]))
        or config[key] <= 0
        for key in positive
    ):
        raise ValueError("positive Stage-A configuration values are invalid")
    integer_fields = (
        "action_chunk_size",
        "action_dim",
        "num_images_in_input",
        "die_hidden_dim",
        "die_metadata_dim",
        "candidate_num_top",
        "candidate_num_stratified",
        "candidate_num_hard_negative",
        "candidate_audit_size",
        "candidate_audit_frequency_steps",
        "teacher_cache_max_samples_per_shard",
        "teacher_cache_max_candidates_per_sample",
    )
    if any(not isinstance(config[key], int) or isinstance(config[key], bool) for key in integer_fields):
        raise ValueError("architecture/count configuration values must be integers")
    if config["candidate_num_top"] + config["candidate_num_stratified"] + config["candidate_num_hard_negative"] > config["candidate_audit_size"]:
        raise ValueError("audit size must cover every regular candidate")
    if config["teacher_cache_max_candidates_per_sample"] < config["candidate_audit_size"]:
        raise ValueError("cache candidate limit must cover audit size")
    if config["teacher_cache_max_samples_per_shard"] > 4096 or config["teacher_cache_max_candidates_per_sample"] > 16:
        raise ValueError("cache limits exceed the hard bounded schema")
    other_numeric = (
        "die_dropout",
        "stage_a_weight_decay",
        "stage_a_ranking_weight",
        "stage_a_ranking_tie_margin",
    )
    if any(
        isinstance(config[key], bool)
        or not isinstance(config[key], (int, float))
        or not math.isfinite(float(config[key]))
        for key in other_numeric
    ):
        raise ValueError("Stage-A numeric values must be finite numbers")
    if not 0 <= config["die_dropout"] < 1 or config["stage_a_weight_decay"] < 0 or config["stage_a_ranking_weight"] < 0:
        raise ValueError("dropout/weight decay/ranking weight are out of range")
    threshold_values = (
        "expansion_min_candidate_top1_coverage",
        "expansion_max_candidate_oracle_regret",
        "expansion_max_full_retention_abs_error",
        "expansion_min_packed_speedup",
        "expansion_min_content_permutation_change",
    )
    if any(
        isinstance(config[key], bool)
        or not isinstance(config[key], (int, float))
        or not math.isfinite(float(config[key]))
        or config[key] < 0
        for key in threshold_values
    ):
        raise ValueError("expansion thresholds must be finite non-negative numbers")
    if config["expansion_min_candidate_top1_coverage"] > 1 or config["expansion_min_packed_speedup"] <= 1:
        raise ValueError("expansion coverage/speedup thresholds are invalid")
    return dict(config)


def load_stage_a_config(path: str | Path) -> tuple[dict[str, Any], str]:
    config_path = Path(path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Stage-A config root must be an object")
    validated = validate_stage_a_config(config)
    return validated, canonical_mapping_signature(validated, namespace="diwa-stage-a-config-v1")


__all__ = ["REQUIRED_STAGE_A_KEYS", "load_stage_a_config", "validate_stage_a_config"]

"""Hard gates that prevent scaling experiments before mandatory audits pass."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ExpansionGateConfig:
    min_candidate_top1_coverage: float = 0.75
    max_candidate_oracle_regret: float = 0.05
    max_full_retention_abs_error: float = 0.002
    min_packed_speedup: float = 1.05
    min_content_permutation_change: float = 1e-4

    def __post_init__(self) -> None:
        values = (
            self.min_candidate_top1_coverage,
            self.max_candidate_oracle_regret,
            self.max_full_retention_abs_error,
            self.min_packed_speedup,
            self.min_content_permutation_change,
        )
        if any(not isinstance(value, (int, float)) or not math.isfinite(float(value)) for value in values):
            raise ValueError("expansion gate thresholds must be finite numbers")
        if not 0 <= self.min_candidate_top1_coverage <= 1:
            raise ValueError("coverage threshold must be in [0, 1]")
        if self.max_candidate_oracle_regret < 0 or self.max_full_retention_abs_error < 0:
            raise ValueError("regret/error thresholds must be non-negative")
        if self.min_packed_speedup <= 1:
            raise ValueError("packed speedup threshold must exceed 1")
        if self.min_content_permutation_change < 0:
            raise ValueError("permutation threshold must be non-negative")


def check_expansion_gates(metrics: dict[str, float], config: ExpansionGateConfig | None = None) -> None:
    config = config or ExpansionGateConfig()
    required = {
        "candidate_top1_coverage",
        "candidate_oracle_regret",
        "full_retention_max_abs_error",
        "packed_speedup",
        "content_permutation_mean_abs_change",
    }
    missing = required - set(metrics)
    if missing:
        raise ValueError(f"mandatory expansion metrics missing: {sorted(missing)}")
    if any(not isinstance(metrics[key], (int, float)) or not math.isfinite(float(metrics[key])) for key in required):
        raise ValueError("mandatory expansion metrics must be finite numbers")
    if not 0 <= metrics["candidate_top1_coverage"] <= 1:
        raise ValueError("candidate_top1_coverage must be in [0, 1]")
    if any(metrics[key] < 0 for key in ("candidate_oracle_regret", "full_retention_max_abs_error", "packed_speedup", "content_permutation_mean_abs_change")):
        raise ValueError("mandatory expansion metrics cannot be negative")
    failures = []
    if metrics["candidate_top1_coverage"] < config.min_candidate_top1_coverage:
        failures.append("candidate_top1_coverage")
    if metrics["candidate_oracle_regret"] > config.max_candidate_oracle_regret:
        failures.append("candidate_oracle_regret")
    if metrics["full_retention_max_abs_error"] > config.max_full_retention_abs_error:
        failures.append("full_retention_max_abs_error")
    if metrics["packed_speedup"] < config.min_packed_speedup:
        failures.append("packed_speedup")
    if metrics["content_permutation_mean_abs_change"] < config.min_content_permutation_change:
        failures.append("content_permutation_mean_abs_change")
    if failures:
        raise RuntimeError(f"experiment expansion blocked by failed audits: {failures}")


__all__ = ["ExpansionGateConfig", "check_expansion_gates"]

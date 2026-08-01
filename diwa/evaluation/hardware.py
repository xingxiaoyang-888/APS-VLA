"""Hardware-tier validation for the cost-bounded DIWA experiment plan."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Workload = Literal[
    "data_preprocess",
    "cache_verify",
    "analysis",
    "fp16_compatibility",
    "checkpoint_smoke",
    "teacher_pilot",
    "stage_a",
    "ablation",
    "final_profile",
    "final_scale",
]


@dataclass(frozen=True)
class ComputeEnvironment:
    accelerator: str
    device_count: int
    memory_gib_per_device: float
    bf16_supported: bool
    cpu_cores: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.accelerator, str) or not self.accelerator.strip():
            raise ValueError("accelerator must be a non-empty string")
        if not isinstance(self.device_count, int) or isinstance(self.device_count, bool) or self.device_count < 0:
            raise ValueError("device_count must be a non-negative integer")
        if not isinstance(self.cpu_cores, int) or isinstance(self.cpu_cores, bool) or self.cpu_cores < 0:
            raise ValueError("cpu_cores must be a non-negative integer")
        if self.memory_gib_per_device < 0:
            raise ValueError("memory_gib_per_device cannot be negative")

    @property
    def normalized_accelerator(self) -> str:
        name = self.accelerator.lower().replace(" ", "")
        if "a800" in name:
            return "a800"
        if "a100" in name:
            return "a100"
        if "v100" in name:
            return "v100"
        if name in ("cpu", "none"):
            return "cpu"
        return "unknown"


@dataclass(frozen=True)
class ComputeValidation:
    tier: str
    workload: Workload
    precision: str
    primary_result_allowed: bool


CPU_WORKLOADS = {"data_preprocess", "cache_verify", "analysis"}
A100_WORKLOADS = {"checkpoint_smoke", "teacher_pilot", "stage_a", "ablation"}
A800_WORKLOADS = {"final_profile", "final_scale"}


def validate_compute_environment(
    environment: ComputeEnvironment,
    workload: Workload,
    *,
    requested_precision: str,
) -> ComputeValidation:
    accelerator = environment.normalized_accelerator
    if requested_precision not in ("bf16", "fp16", "fp32"):
        raise ValueError("requested_precision must be bf16, fp16, or fp32")

    if accelerator == "cpu":
        if workload not in CPU_WORKLOADS:
            raise RuntimeError("CPU tier is limited to preprocessing, cache verification, and analysis")
        if not 12 <= environment.cpu_cores <= 64:
            raise RuntimeError("CPU tier requires 12-64 CPU cores")
        return ComputeValidation("cpu", workload, requested_precision, False)

    if accelerator == "v100":
        if workload != "fp16_compatibility":
            raise RuntimeError("V100 is compatibility-only and cannot produce primary DIWA results")
        if requested_precision != "fp16":
            raise RuntimeError("V100 has no native bf16 support; compatibility runs must use fp16")
        if not 1 <= environment.device_count <= 4:
            raise RuntimeError("V100 compatibility tier supports one or four devices")
        return ComputeValidation("v100", workload, "fp16", False)

    if accelerator == "a100":
        if workload not in A100_WORKLOADS:
            raise RuntimeError("2xA100 is the primary development/pilot tier, not the final-scale tier")
        if environment.device_count != 2:
            raise RuntimeError("the primary A100 tier requires exactly two devices")
        if environment.memory_gib_per_device < 40:
            raise RuntimeError("the A100 tier requires at least 40 GiB per device")
        if requested_precision != "bf16" or not environment.bf16_supported:
            raise RuntimeError("primary A100 runs require native bf16")
        return ComputeValidation("2xa100", workload, "bf16", True)

    if accelerator == "a800":
        if workload not in A800_WORKLOADS:
            raise RuntimeError("4xA800 is reserved for final profiling or final-scale runs")
        if environment.device_count != 4:
            raise RuntimeError("A800 runs require exactly four devices; 8xA800 is unsupported")
        if environment.memory_gib_per_device < 80:
            raise RuntimeError("the A800 tier requires at least 80 GiB per device")
        if requested_precision != "bf16" or not environment.bf16_supported:
            raise RuntimeError("primary A800 runs require native bf16")
        return ComputeValidation("4xa800", workload, "bf16", True)

    raise RuntimeError(f"unsupported accelerator: {environment.accelerator}")


__all__ = ["ComputeEnvironment", "ComputeValidation", "Workload", "validate_compute_environment"]

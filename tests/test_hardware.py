import pytest

from diwa.evaluation.hardware import ComputeEnvironment, validate_compute_environment


def test_two_a100_is_primary_bf16_pilot_tier():
    result = validate_compute_environment(
        ComputeEnvironment("NVIDIA A100-SXM4-40GB", 2, 40, True),
        "teacher_pilot",
        requested_precision="bf16",
    )
    assert result.tier == "2xa100"
    assert result.primary_result_allowed


def test_v100_is_fp16_compatibility_only():
    environment = ComputeEnvironment("Tesla V100", 4, 32, False)
    result = validate_compute_environment(
        environment, "fp16_compatibility", requested_precision="fp16"
    )
    assert not result.primary_result_allowed
    with pytest.raises(RuntimeError, match="compatibility-only"):
        validate_compute_environment(environment, "stage_a", requested_precision="fp16")
    with pytest.raises(RuntimeError, match="no native bf16"):
        validate_compute_environment(environment, "fp16_compatibility", requested_precision="bf16")


def test_four_a800_is_burst_tier_and_eight_is_rejected():
    result = validate_compute_environment(
        ComputeEnvironment("NVIDIA A800 80GB", 4, 80, True),
        "final_profile",
        requested_precision="bf16",
    )
    assert result.tier == "4xa800"
    with pytest.raises(RuntimeError, match="8xA800 is unsupported"):
        validate_compute_environment(
            ComputeEnvironment("NVIDIA A800 80GB", 8, 80, True),
            "final_scale",
            requested_precision="bf16",
        )


def test_two_a800_is_validation_only():
    environment = ComputeEnvironment("NVIDIA A800-SXM4-80GB", 2, 79.318, True)
    result = validate_compute_environment(
        environment,
        "checkpoint_smoke",
        requested_precision="bf16",
    )
    assert result.tier == "2xa800-validation"
    assert not result.primary_result_allowed
    with pytest.raises(RuntimeError, match="validation-only"):
        validate_compute_environment(environment, "stage_a", requested_precision="bf16")


def test_cpu_tier_requires_requested_core_range():
    validate_compute_environment(
        ComputeEnvironment("cpu", 0, 0, False, cpu_cores=12),
        "cache_verify",
        requested_precision="fp32",
    )
    with pytest.raises(RuntimeError, match="12-64"):
        validate_compute_environment(
            ComputeEnvironment("cpu", 0, 0, False, cpu_cores=8),
            "analysis",
            requested_precision="fp32",
        )

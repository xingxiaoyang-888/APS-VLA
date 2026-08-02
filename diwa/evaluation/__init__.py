"""Server preflight and mandatory experiment audits."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from .audit_log import AuditRecord, save_audit_record
from .gates import ExpansionGateConfig, check_expansion_gates
from .hardware import ComputeEnvironment, ComputeValidation, validate_compute_environment
from .checkpoint_manifest import (
    CheckpointFileSpec,
    CheckpointManifest,
    CheckpointVerification,
    load_checkpoint_manifest,
    verify_checkpoint_directory,
    verify_checkpoint_file,
)
if TYPE_CHECKING:
    from .preflight import EquivalenceReport, LatencyReport


_PREFLIGHT_EXPORTS = frozenset(
    {
        "EquivalenceReport",
        "LatencyReport",
        "compare_action_outputs",
        "content_permutation_audit",
        "measure_forward_latency",
        "validate_openvla_oft_structure",
    }
)


def __getattr__(name: str):
    if name not in _PREFLIGHT_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(".preflight", __name__), name)
    globals()[name] = value
    return value

__all__ = [
    "AuditRecord",
    "ComputeEnvironment",
    "ComputeValidation",
    "CheckpointFileSpec",
    "CheckpointManifest",
    "CheckpointVerification",
    "EquivalenceReport",
    "ExpansionGateConfig",
    "LatencyReport",
    "compare_action_outputs",
    "content_permutation_audit",
    "measure_forward_latency",
    "validate_openvla_oft_structure",
    "check_expansion_gates",
    "save_audit_record",
    "validate_compute_environment",
    "load_checkpoint_manifest",
    "verify_checkpoint_directory",
    "verify_checkpoint_file",
]

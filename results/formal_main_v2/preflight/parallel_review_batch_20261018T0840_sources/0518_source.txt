"""Minimal runtime boundary required by the frozen OpenVLA-OFT remote code."""

from __future__ import annotations

from enum import Enum
import hashlib
from importlib.machinery import ModuleSpec
import inspect
from types import ModuleType
import sys
import textwrap

import torch


IGNORE_INDEX = -100
ACTION_TOKEN_BEGIN_IDX = 31743
STOP_INDEX = 2
NUM_ACTIONS_CHUNK = 8
ACTION_DIM = 7
PROPRIO_DIM = 8


class NormalizationType(str, Enum):
    NORMAL = "normal"
    BOUNDS = "bounds"
    BOUNDS_Q99 = "bounds_q99"


ACTION_PROPRIO_NORMALIZATION_TYPE = NormalizationType.BOUNDS_Q99

# Normalized inspect.getsource(LlamaSdpaAttention.forward), from the pinned
# moojink/transformers-openvla-oft commit below. Ordinary transformers with the
# same version number uses causal SDPA and is NOT an equivalent runtime.
TRANSFORMERS_OFT_COMMIT = "bc339d9ad707454c0c115970db43c260067c61ab"
OFT_SDPA_FORWARD_SHA256 = "46e487c53cd67d3ffbbf9f0274d6c855c214b03e8169bb4b9258dd1e2d7948e1"


def validate_oft_sdpa_runtime() -> None:
    """Fail closed if the installed SDPA implementation is not the locked fork.

    A changed upstream/runtime requires re-audit and an explicit new source hash;
    silently falling back to causal attention invalidates the frozen policy.
    """
    from transformers.models.llama.modeling_llama import LlamaSdpaAttention

    try:
        source = textwrap.dedent(inspect.getsource(LlamaSdpaAttention.forward)).strip()
    except (OSError, TypeError) as exc:
        raise RuntimeError("cannot verify the locked OFT SDPA runtime source") from exc
    actual = hashlib.sha256(source.replace("\r\n", "\n").encode("utf-8")).hexdigest()
    if actual != OFT_SDPA_FORWARD_SHA256:
        raise RuntimeError(
            "OFT requires the audited non-causal SDPA fork at "
            f"{TRANSFORMERS_OFT_COMMIT}; installed forward SHA256={actual}"
        )


def get_current_action_mask(token_ids: torch.Tensor) -> torch.Tensor:
    non_ignored = token_ids != IGNORE_INDEX
    cumulative = torch.cumsum(non_ignored, dim=1)
    return (1 <= cumulative) & (cumulative <= ACTION_DIM) & (token_ids > ACTION_TOKEN_BEGIN_IDX)


def get_next_actions_mask(token_ids: torch.Tensor) -> torch.Tensor:
    non_ignored = token_ids != IGNORE_INDEX
    cumulative = torch.cumsum(non_ignored, dim=1)
    return (cumulative > ACTION_DIM) & (token_ids > ACTION_TOKEN_BEGIN_IDX)


def _package(name: str) -> ModuleType:
    module = ModuleType(name)
    module.__path__ = []
    module.__package__ = name
    module.__spec__ = ModuleSpec(name, loader=None, is_package=True)
    return module


def _module(name: str, package: str) -> ModuleType:
    module = ModuleType(name)
    module.__package__ = package
    module.__spec__ = ModuleSpec(name, loader=None, is_package=False)
    return module


def _validate_constants(constants: ModuleType) -> None:
    actual = (
        getattr(constants, "NUM_ACTIONS_CHUNK", None),
        getattr(constants, "ACTION_DIM", None),
        getattr(constants, "PROPRIO_DIM", None),
        str(getattr(constants, "ACTION_PROPRIO_NORMALIZATION_TYPE", "")),
    )
    expected = (NUM_ACTIONS_CHUNK, ACTION_DIM, PROPRIO_DIM, "NormalizationType.BOUNDS_Q99")
    if actual != expected:
        raise RuntimeError(f"prismatic constants are not the frozen LIBERO contract: {actual}")


def install_prismatic_runtime_compat(*, use_minimal_compat: bool = False) -> bool:
    """Install only the two modules imported by checkpoint remote code.

    Returns `True` when the compatibility modules were installed. If a real
    `prismatic` package exists, it is imported and validated instead.
    """

    if not use_minimal_compat:
        from prismatic.vla import constants

        _validate_constants(constants)
        return False

    existing = [name for name in sys.modules if name == "prismatic" or name.startswith("prismatic.")]
    if existing:
        raise RuntimeError(
            "minimal prismatic compatibility must be installed before any prismatic import; "
            f"found {sorted(existing)}"
        )

    root = _package("prismatic")
    training = _package("prismatic.training")
    vla = _package("prismatic.vla")
    train_utils = _module("prismatic.training.train_utils", "prismatic.training")
    constants = _module("prismatic.vla.constants", "prismatic.vla")

    train_utils.get_current_action_mask = get_current_action_mask
    train_utils.get_next_actions_mask = get_next_actions_mask
    for name in (
        "IGNORE_INDEX",
        "ACTION_TOKEN_BEGIN_IDX",
        "STOP_INDEX",
        "NUM_ACTIONS_CHUNK",
        "ACTION_DIM",
        "PROPRIO_DIM",
        "NormalizationType",
        "ACTION_PROPRIO_NORMALIZATION_TYPE",
    ):
        setattr(constants, name, globals()[name])

    root.training = training
    root.vla = vla
    training.train_utils = train_utils
    vla.constants = constants
    sys.modules.update(
        {
            "prismatic": root,
            "prismatic.training": training,
            "prismatic.training.train_utils": train_utils,
            "prismatic.vla": vla,
            "prismatic.vla.constants": constants,
        }
    )
    _validate_constants(constants)
    return True


__all__ = ["install_prismatic_runtime_compat", "validate_oft_sdpa_runtime"]

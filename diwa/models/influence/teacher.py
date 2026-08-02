"""Sequential, graph-free paired counterfactual teacher."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Optional, Protocol

import torch
from torch import nn

from diwa.data.contracts import TokenBatch
from diwa.data.interventions import apply_intervention
from diwa.losses.action_distance import normalized_action_chunk_distance
from diwa.models.influence.sampling import CandidateSet


class TokenActionPolicy(Protocol):
    training: bool

    def forward_from_tokens(
        self,
        tokens: torch.Tensor,
        proprio: torch.Tensor,
        **kwargs: torch.Tensor,
    ) -> torch.Tensor:
        """Return normalized action chunks shaped [B, K, action_dim]."""


@dataclass(frozen=True)
class TeacherTargets:
    influence: torch.Tensor
    candidate_count: torch.Tensor
    base_intervened_count: torch.Tensor

    def __post_init__(self) -> None:
        batch = self.influence.shape[0]
        if self.influence.ndim != 1 or not self.influence.is_floating_point():
            raise ValueError("influence must be floating [B]")
        if self.candidate_count.shape != (batch,) or self.base_intervened_count.shape != (batch,):
            raise ValueError("teacher metadata must have shape [B]")
        if self.influence.requires_grad:
            raise ValueError("teacher influence must be detached")


@dataclass(frozen=True)
class CandidateTeacherTargets:
    influence: torch.Tensor
    valid_candidates: torch.Tensor
    source_indices: torch.Tensor
    base_intervened_count: torch.Tensor

    def __post_init__(self) -> None:
        if self.influence.ndim != 2 or not self.influence.is_floating_point():
            raise ValueError("influence must be floating [B, C]")
        batch, candidates = self.influence.shape
        if self.valid_candidates.shape != (batch, candidates) or self.valid_candidates.dtype != torch.bool:
            raise ValueError("valid_candidates must be bool [B, C]")
        if self.source_indices.shape != (batch, candidates) or self.source_indices.dtype != torch.long:
            raise ValueError("source_indices must be long [B, C]")
        if self.base_intervened_count.shape != (batch,) or self.base_intervened_count.dtype != torch.long:
            raise ValueError("base_intervened_count must be long [B]")
        if self.influence.requires_grad or not torch.isfinite(self.influence).all():
            raise ValueError("candidate teacher targets must be finite and detached")
        if bool((self.influence[~self.valid_candidates] != 0).any()):
            raise ValueError("invalid candidate slots must have zero influence")


class CounterfactualTeacher:
    """Measures Delta(candidate | intervened set) with two sequential forwards.

    The policy is required to be in eval mode. The first action chunk is cloned in
    fp32 and all references to its input/output are deleted before the second
    branch, preventing paired 7B activations from being live simultaneously.
    """

    def __init__(
        self,
        policy: nn.Module,
        huber_delta: float = 1.0,
        action_chunk_shape: tuple[int, int] = (8, 7),
    ) -> None:
        if not hasattr(policy, "forward_from_tokens"):
            raise TypeError("policy must implement forward_from_tokens(tokens, proprio)")
        if not isinstance(huber_delta, (int, float)) or not math.isfinite(float(huber_delta)) or huber_delta <= 0:
            raise ValueError("huber_delta must be positive")
        if len(action_chunk_shape) != 2 or any(
            not isinstance(value, int) or value <= 0 for value in action_chunk_shape
        ):
            raise ValueError("action_chunk_shape must be a positive (chunk, action_dim) tuple")
        self.policy = policy
        self.huber_delta = huber_delta
        self.action_chunk_shape = action_chunk_shape

    @staticmethod
    def _validate_action_chunk(
        action: torch.Tensor, batch_size: int, action_chunk_shape: tuple[int, int]
    ) -> None:
        if not isinstance(action, torch.Tensor) or action.ndim != 3:
            raise ValueError("policy action output must be tensor [B, K, action_dim]")
        if action.shape[0] != batch_size or tuple(action.shape[1:]) != action_chunk_shape or not action.is_floating_point():
            raise ValueError("policy action output has invalid batch or dtype")
        if not torch.isfinite(action).all():
            raise ValueError("policy action output contains NaN/Inf")

    @torch.inference_mode()
    def estimate(
        self,
        batch: TokenBatch,
        baseline: torch.Tensor,
        intervened_mask: torch.Tensor,
        candidate_mask: torch.Tensor,
        policy_inputs: Optional[Mapping[str, torch.Tensor]] = None,
    ) -> TeacherTargets:
        if self.policy.training:
            raise RuntimeError("counterfactual teacher requires policy.eval(); refusing stochastic/train-mode target")
        for name, mask in (
            ("intervened_mask", intervened_mask),
            ("candidate_mask", candidate_mask),
        ):
            if mask.shape != batch.valid.shape or mask.dtype != torch.bool:
                raise ValueError(f"{name} must be bool [B, N]")
            if mask.device != batch.z.device:
                raise ValueError(f"{name} and tokens must share device")
            if bool((mask & ~batch.valid).any()):
                raise ValueError(f"{name} cannot select invalid/padded tokens")
        if bool((intervened_mask & candidate_mask).any()):
            raise ValueError("candidate_mask must be disjoint from the base intervened set")
        candidate_count = candidate_mask.sum(dim=1)
        if not bool((candidate_count > 0).all()):
            raise ValueError("each sample must include at least one candidate token")
        if not bool((batch.valid & ~(intervened_mask | candidate_mask)).any(dim=1).all()):
            raise ValueError("paired intervention must leave at least one valid token untouched")

        forward_kwargs = dict(policy_inputs or {})
        if any(not isinstance(key, str) or not isinstance(value, torch.Tensor) for key, value in forward_kwargs.items()):
            raise TypeError("policy_inputs must map string names to tensors")
        if any(value.device != batch.z.device for value in forward_kwargs.values()):
            raise ValueError("policy_inputs and TokenBatch must share device")

        base_tokens = apply_intervention(
            batch.z,
            intervened_mask,
            baseline,
            allow_empty=True,
        )
        base_output = self.policy.forward_from_tokens(base_tokens, batch.proprio, **forward_kwargs)
        self._validate_action_chunk(base_output, batch.batch_size, self.action_chunk_shape)
        # Action chunks are tiny (LIBERO: 56 values/sample); fp32 cloning makes
        # the target stable without retaining model outputs or bf16 activations.
        base_action = base_output.detach().float().clone()
        del base_output, base_tokens

        expanded_mask = intervened_mask | candidate_mask
        candidate_tokens = apply_intervention(batch.z, expanded_mask, baseline)
        candidate_output = self.policy.forward_from_tokens(candidate_tokens, batch.proprio, **forward_kwargs)
        self._validate_action_chunk(candidate_output, batch.batch_size, self.action_chunk_shape)
        candidate_action = candidate_output.detach().float()
        influence = normalized_action_chunk_distance(
            base_action,
            candidate_action,
            huber_delta=self.huber_delta,
            reduction="none",
        ).detach()
        del candidate_output, candidate_action, candidate_tokens, base_action

        return TeacherTargets(
            influence=influence,
            candidate_count=candidate_count.detach().clone(),
            base_intervened_count=intervened_mask.sum(dim=1).detach().clone(),
        )

    @torch.inference_mode()
    def estimate_candidates(
        self,
        batch: TokenBatch,
        baseline: torch.Tensor,
        intervened_mask: torch.Tensor,
        candidates: CandidateSet,
        policy_inputs: Optional[Mapping[str, torch.Tensor]] = None,
    ) -> CandidateTeacherTargets:
        if self.policy.training:
            raise RuntimeError("counterfactual teacher requires policy.eval()")
        if candidates.masks.shape[0] != batch.batch_size or candidates.masks.shape[2] != batch.num_tokens:
            raise ValueError("candidate set must match TokenBatch dimensions")
        if candidates.masks.device != batch.z.device:
            raise ValueError("candidate set and TokenBatch must share device")
        if candidates.masks.dtype != torch.bool or candidates.source_indices.dtype != torch.long:
            raise TypeError("candidate masks/indices have invalid dtype")
        if intervened_mask.shape != batch.valid.shape or intervened_mask.dtype != torch.bool:
            raise ValueError("intervened_mask must be bool [B, N]")
        if bool((candidates.masks & intervened_mask[:, None]).any()):
            raise ValueError("candidate set must be disjoint from prior interventions")
        if bool((candidates.masks & ~batch.valid[:, None]).any()):
            raise ValueError("candidate set selects invalid tokens")
        forward_kwargs = dict(policy_inputs or {})
        if any(not isinstance(key, str) or not isinstance(value, torch.Tensor) for key, value in forward_kwargs.items()):
            raise TypeError("policy_inputs must map string names to tensors")
        if any(value.device != batch.z.device for value in forward_kwargs.values()):
            raise ValueError("policy_inputs and TokenBatch must share device")

        base_tokens = apply_intervention(batch.z, intervened_mask, baseline, allow_empty=True)
        base_output = self.policy.forward_from_tokens(base_tokens, batch.proprio, **forward_kwargs)
        self._validate_action_chunk(base_output, batch.batch_size, self.action_chunk_shape)
        base_action = base_output.detach().float().clone()
        del base_output, base_tokens

        influence = torch.zeros(
            candidates.valid_candidates.shape, dtype=torch.float32, device=batch.z.device
        )
        for slot in range(candidates.masks.shape[1]):
            active = candidates.valid_candidates[:, slot]
            if not bool(active.any()):
                continue
            if not bool(active.all()):
                raise ValueError("ragged candidate slots are unsupported; bucket by candidate count")
            expanded_mask = intervened_mask | candidates.masks[:, slot]
            candidate_tokens = apply_intervention(batch.z, expanded_mask, baseline)
            candidate_output = self.policy.forward_from_tokens(
                candidate_tokens, batch.proprio, **forward_kwargs
            )
            self._validate_action_chunk(candidate_output, batch.batch_size, self.action_chunk_shape)
            slot_influence = normalized_action_chunk_distance(
                base_action,
                candidate_output.detach().float(),
                huber_delta=self.huber_delta,
                reduction="none",
            )
            influence[:, slot] = slot_influence
            del candidate_output, candidate_tokens, slot_influence
        del base_action
        return CandidateTeacherTargets(
            influence=influence.detach(),
            valid_candidates=candidates.valid_candidates.detach().clone(),
            source_indices=candidates.source_indices.detach().clone(),
            base_intervened_count=intervened_mask.sum(dim=1).detach().clone().long(),
        )


__all__ = [
    "CandidateTeacherTargets",
    "CounterfactualTeacher",
    "TeacherTargets",
    "TokenActionPolicy",
]

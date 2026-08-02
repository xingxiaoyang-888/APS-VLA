"""Normalized OpenVLA-OFT action policy starting from projected visual tokens."""

from __future__ import annotations

from typing import Optional
import weakref

import numpy as np
import torch
from torch import nn

from diwa.data.contracts import OFTPackedBatch
from diwa.models.oft_adapter import OFTPackedPrefixAdapter


def _resolve_language_backbone(vla: nn.Module) -> nn.Module:
    """Resolve the Llama decoder without retaining all-layer HF outputs."""

    candidates = (
        ("language_model", "model"),
        ("model", "language_model", "model"),
    )
    for path in candidates:
        value = vla
        for name in path:
            value = getattr(value, name, None)
            if value is None:
                break
        if isinstance(value, nn.Module):
            return value
    raise AttributeError(
        "cannot resolve OpenVLA-OFT language backbone; pass language_backbone explicitly "
        "after checking the loaded checkpoint structure"
    )


class OpenVLAOFTTokenPolicy(nn.Module):
    """Runs the deterministic OFT L1 head from projected visual patch tokens.

    `forward_from_tokens` always returns normalized actions. Dataset-specific
    unnormalization is deliberately isolated in `predict_rollout_from_tokens`, so
    counterfactual teacher distances cannot accidentally mix physical units.
    """

    def __init__(
        self,
        vla: nn.Module,
        action_head: nn.Module,
        proprio_projector: nn.Module,
        *,
        num_patches_full: int,
        action_chunk_size: int = 8,
        action_dim: int = 7,
        placeholder_token_id: int = 1,
        stop_token_id: int = 2,
        assistant_empty_token_id: Optional[int] = 29871,
        language_backbone: Optional[nn.Module] = None,
    ) -> None:
        super().__init__()
        if num_patches_full <= 1:
            raise ValueError("num_patches_full must be greater than one")
        if action_chunk_size <= 0 or action_dim <= 0:
            raise ValueError("action_chunk_size and action_dim must be positive")
        if placeholder_token_id < 0 or stop_token_id < 0:
            raise ValueError("placeholder and stop token ids must be non-negative")
        if assistant_empty_token_id is not None and assistant_empty_token_id < 0:
            raise ValueError("assistant_empty_token_id must be non-negative or None")
        if not hasattr(vla, "get_input_embeddings"):
            raise TypeError("vla must implement get_input_embeddings()")
        if not hasattr(action_head, "predict_action"):
            raise TypeError("deterministic OFT action_head must implement predict_action()")

        self.action_head = action_head
        self.proprio_projector = proprio_projector
        self.num_patches_full = num_patches_full
        self.action_chunk_size = action_chunk_size
        self.action_dim = action_dim
        self.placeholder_token_id = placeholder_token_id
        self.stop_token_id = stop_token_id
        self.assistant_empty_token_id = assistant_empty_token_id
        backbone = language_backbone or _resolve_language_backbone(vla)
        embedding_layer = vla.get_input_embeddings()
        if not isinstance(embedding_layer, nn.Module):
            raise TypeError("vla.get_input_embeddings() must return an nn.Module")
        if not any(module is embedding_layer for module in backbone.modules()):
            raise ValueError("input embedding layer must belong to the resolved language backbone")
        # The registered computation graph owns the language backbone once. Weak
        # references avoid duplicate VLA/backbone state_dict paths and 7B saves.
        object.__setattr__(self, "_vla_ref", weakref.ref(vla))
        object.__setattr__(self, "_embedding_layer_ref", weakref.ref(embedding_layer))
        # Dense prefixes are required by the counterfactual teacher; physically
        # shortened prefixes remain validated through OFTPackedBatch metadata.
        self.prefix_adapter = OFTPackedPrefixAdapter(
            backbone,
            action_chunk_size=action_chunk_size,
            action_dim=action_dim,
            require_shortened_prefix=False,
        )

    @property
    def action_token_count(self) -> int:
        return self.action_chunk_size * self.action_dim

    @staticmethod
    def _validate_prompt(input_ids: torch.Tensor, attention_mask: torch.Tensor, batch: int) -> None:
        if input_ids.ndim != 2 or input_ids.shape[0] != batch or input_ids.dtype not in (
            torch.int32,
            torch.int64,
            torch.long,
        ):
            raise ValueError("input_ids must be integer [B, S]")
        if input_ids.shape[1] < 2:
            raise ValueError("input_ids must contain BOS and at least one prompt token")
        if attention_mask.shape != input_ids.shape or attention_mask.dtype not in (
            torch.bool,
            torch.int32,
            torch.int64,
            torch.long,
        ):
            raise ValueError("attention_mask must be bool/integer [B, S]")
        if input_ids.device != attention_mask.device:
            raise ValueError("input_ids and attention_mask must share device")
        if not bool((attention_mask != 0).all()):
            raise ValueError(
                "padded prompts are unsupported; bucket/trim to equal prompt length before appending action tokens"
            )

    def _build_oft_text_inputs(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        batch = input_ids.shape[0]
        action_ids = torch.full(
            (batch, self.action_token_count),
            self.placeholder_token_id,
            dtype=input_ids.dtype,
            device=input_ids.device,
        )
        stop_ids = torch.full(
            (batch, 1), self.stop_token_id, dtype=input_ids.dtype, device=input_ids.device
        )
        full_ids = torch.cat((input_ids, action_ids, stop_ids), dim=1)
        mask_extension = torch.ones(
            (batch, self.action_token_count + 1),
            dtype=attention_mask.dtype,
            device=attention_mask.device,
        )
        full_attention = torch.cat((attention_mask, mask_extension), dim=1)
        action_mask = torch.zeros_like(full_ids, dtype=torch.bool)
        action_mask[:, input_ids.shape[1] : input_ids.shape[1] + self.action_token_count] = True
        prompt_counts = torch.full(
            (batch,), input_ids.shape[1] - 1, dtype=torch.long, device=input_ids.device
        )
        return full_ids, full_attention, action_mask, prompt_counts

    def _ensure_assistant_empty_token(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if self.assistant_empty_token_id is None:
            return input_ids, attention_mask
        has_empty = input_ids[:, -1] == self.assistant_empty_token_id
        if bool(has_empty.all()):
            return input_ids, attention_mask
        if bool(has_empty.any()):
            raise ValueError("mixed assistant empty-token state would create prompt index drift")
        extension = torch.full(
            (input_ids.shape[0], 1),
            self.assistant_empty_token_id,
            dtype=input_ids.dtype,
            device=input_ids.device,
        )
        mask_extension = torch.ones(
            (attention_mask.shape[0], 1),
            dtype=attention_mask.dtype,
            device=attention_mask.device,
        )
        return torch.cat((input_ids, extension), dim=1), torch.cat(
            (attention_mask, mask_extension), dim=1
        )

    def forward_from_tokens(
        self,
        tokens: torch.Tensor,
        proprio: torch.Tensor,
        *,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        patch_keep_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Return normalized action chunks `[B, 8, 7]` without CPU copies."""

        if tokens.ndim != 3 or not tokens.is_floating_point():
            raise ValueError("tokens must be floating [B, N_keep, D]")
        if not torch.isfinite(tokens).all():
            raise ValueError("tokens contain NaN/Inf")
        batch, keep_count, hidden = tokens.shape
        if not 0 < keep_count <= self.num_patches_full:
            raise ValueError("token count must satisfy 0 < N_keep <= num_patches_full")
        if proprio.ndim != 2 or proprio.shape[0] != batch or not proprio.is_floating_point():
            raise ValueError("normalized proprio must be floating [B, proprio_dim]")
        if proprio.device != tokens.device or proprio.dtype != tokens.dtype:
            raise ValueError("tokens and proprio must share device/dtype")
        if not torch.isfinite(proprio).all():
            raise ValueError("proprio contains NaN/Inf")
        self._validate_prompt(input_ids, attention_mask, batch)
        if input_ids.device != tokens.device:
            raise ValueError("prompt tensors and projected tokens must share device")
        input_ids, attention_mask = self._ensure_assistant_empty_token(input_ids, attention_mask)

        if patch_keep_mask is None:
            if keep_count != self.num_patches_full:
                raise ValueError("shortened tokens require the original patch_keep_mask")
            patch_keep_mask = torch.ones(
                (batch, self.num_patches_full), dtype=torch.bool, device=tokens.device
            )
        if patch_keep_mask.shape != (batch, self.num_patches_full) or patch_keep_mask.dtype != torch.bool:
            raise ValueError("patch_keep_mask must be bool [B, N_full]")
        if patch_keep_mask.device != tokens.device:
            raise ValueError("patch_keep_mask and tokens must share device")
        keep_counts = patch_keep_mask.sum(dim=1)
        if not torch.equal(keep_counts, torch.full_like(keep_counts, keep_count)):
            raise ValueError("patch_keep_mask count disagrees with physical token length")

        full_ids, full_attention, action_mask, prompt_counts = self._build_oft_text_inputs(
            input_ids, attention_mask
        )
        embedding_layer = self._embedding_layer_ref()
        if embedding_layer is None:
            raise RuntimeError("VLA input embedding layer was released")
        input_embeddings = embedding_layer(full_ids)
        if input_embeddings.shape != (batch, full_ids.shape[1], hidden):
            raise RuntimeError("VLA input embedding dimension disagrees with projected token dimension")
        if input_embeddings.device != tokens.device or input_embeddings.dtype != tokens.dtype:
            raise RuntimeError("VLA text embeddings and projected tokens must share device/dtype")

        proprio_token = self.proprio_projector(proprio)
        if proprio_token.shape != (batch, hidden):
            raise RuntimeError("proprio_projector must return [B, language_hidden_dim]")
        if proprio_token.device != tokens.device or proprio_token.dtype != tokens.dtype:
            raise RuntimeError("projected proprio and visual tokens must share device/dtype")
        if not torch.isfinite(proprio_token).all():
            raise RuntimeError("proprio projector produced NaN/Inf")

        packed_batch = OFTPackedBatch(
            projected_patches=tokens,
            proprio_token=proprio_token.unsqueeze(1),
            patch_keep_mask=patch_keep_mask,
            num_patches_full=self.num_patches_full,
            num_patches_keep=keep_counts.to(dtype=torch.long),
            num_prompt_tokens=prompt_counts,
            action_chunk_shape=(self.action_chunk_size, self.action_dim),
        )
        prefix_output = self.prefix_adapter(
            input_embeddings,
            packed_batch,
            full_attention,
            action_mask,
        )
        normalized_actions = self.action_head.predict_action(prefix_output.action_hidden_states)
        expected_shape = (batch, self.action_chunk_size, self.action_dim)
        if not isinstance(normalized_actions, torch.Tensor) or normalized_actions.shape != expected_shape:
            raise RuntimeError(f"action_head must return normalized actions shaped {expected_shape}")
        if normalized_actions.device != tokens.device:
            raise RuntimeError("action_head output and projected tokens must share device")
        if not normalized_actions.is_floating_point() or not torch.isfinite(normalized_actions).all():
            raise RuntimeError("action_head produced invalid normalized actions")
        return normalized_actions

    @torch.inference_mode()
    def predict_rollout_from_tokens(
        self,
        tokens: torch.Tensor,
        proprio: torch.Tensor,
        *,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        unnorm_key: Optional[str] = None,
        patch_keep_mask: Optional[torch.Tensor] = None,
    ) -> np.ndarray:
        """Return physical-unit actions for environment rollout only."""

        normalized = self.forward_from_tokens(
            tokens,
            proprio,
            input_ids=input_ids,
            attention_mask=attention_mask,
            patch_keep_mask=patch_keep_mask,
        )
        vla = self._vla_ref()
        if vla is None:
            raise RuntimeError("source VLA was released; rollout unnormalization is unavailable")
        unnormalize = getattr(vla, "_unnormalize_actions", None)
        if not callable(unnormalize):
            raise AttributeError("vla must implement _unnormalize_actions() for rollout")
        return unnormalize(normalized.detach().float().cpu().numpy(), unnorm_key)


__all__ = ["OpenVLAOFTTokenPolicy"]

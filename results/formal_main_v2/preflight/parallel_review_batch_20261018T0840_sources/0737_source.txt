"""OpenVLA-OFT-compatible packed visual-prefix forward boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

import torch
from torch import nn

from cti_vla.models.abstraction.packing import OFTPackedBatch


class LanguageBackboneOutput(Protocol):
    last_hidden_state: torch.Tensor


@dataclass
class OFTPackedPrefixOutput:
    action_hidden_states: torch.Tensor
    multimodal_attention_mask: Optional[torch.Tensor]
    sequence_length: int
    num_visual_prefix_tokens: int
    position_ids: torch.Tensor

    def __post_init__(self) -> None:
        if self.action_hidden_states.ndim != 3:
            raise ValueError("action_hidden_states must be [B, K*d_a, D]")
        if self.sequence_length <= 0 or self.num_visual_prefix_tokens <= 0:
            raise ValueError("sequence lengths must be positive")


class OFTPackedPrefixAdapter(nn.Module):
    """Runs the OFT language-model segment from a physically packed prefix.

    The wrapped module should be the underlying HF language backbone (for example,
    `vla.language_model.model`) and return only `last_hidden_state`. This adapter
    intentionally does not own
    the vision encoder or action head, so paired teacher branches can reuse one
    projected patch tensor instead of encoding images twice.
    """

    def __init__(
        self,
        language_backbone: nn.Module,
        action_chunk_size: int = 8,
        action_dim: int = 7,
        require_shortened_prefix: bool = True,
    ) -> None:
        super().__init__()
        if action_chunk_size <= 0 or action_dim <= 0:
            raise ValueError("action_chunk_size and action_dim must be positive")
        self.language_backbone = language_backbone
        self.action_chunk_size = action_chunk_size
        self.action_dim = action_dim
        self.require_shortened_prefix = require_shortened_prefix

    @property
    def action_token_count(self) -> int:
        return self.action_chunk_size * self.action_dim

    @staticmethod
    def build_multimodal_prefix(
        input_embeddings: torch.Tensor,
        packed_prefix: torch.Tensor,
        attention_mask: Optional[torch.Tensor],
    ) -> tuple[torch.Tensor, Optional[torch.Tensor]]:
        if input_embeddings.ndim != 3 or packed_prefix.ndim != 3:
            raise ValueError("input_embeddings and packed_prefix must be [B, S, D]")
        if input_embeddings.shape[0] != packed_prefix.shape[0] or input_embeddings.shape[2] != packed_prefix.shape[2]:
            raise ValueError("input_embeddings and packed_prefix batch/hidden dimensions must match")
        if input_embeddings.device != packed_prefix.device or input_embeddings.dtype != packed_prefix.dtype:
            raise ValueError("input_embeddings and packed_prefix must share device/dtype")
        if input_embeddings.shape[1] < 2:
            raise ValueError("input_embeddings must contain BOS and at least one following token")

        multimodal = torch.cat(
            (input_embeddings[:, :1], packed_prefix, input_embeddings[:, 1:]), dim=1
        ).contiguous()
        if attention_mask is None:
            return multimodal, None
        if attention_mask.ndim != 2 or attention_mask.shape != input_embeddings.shape[:2]:
            raise ValueError("attention_mask must match input embedding [B, S]")
        if attention_mask.device != input_embeddings.device:
            raise ValueError("attention_mask and embeddings must share device")
        prefix_mask = torch.ones(
            packed_prefix.shape[:2], dtype=attention_mask.dtype, device=attention_mask.device
        )
        multimodal_mask = torch.cat(
            (attention_mask[:, :1], prefix_mask, attention_mask[:, 1:]), dim=1
        ).contiguous()
        return multimodal, multimodal_mask

    def forward(
        self,
        input_embeddings: torch.Tensor,
        packed_batch: OFTPackedBatch,
        attention_mask: Optional[torch.Tensor],
        action_token_mask: torch.Tensor,
    ) -> OFTPackedPrefixOutput:
        if input_embeddings.ndim != 3:
            raise ValueError("input_embeddings must be [B, S, D]")
        batch, seq, hidden = input_embeddings.shape
        if attention_mask is not None:
            if attention_mask.shape != (batch, seq) or attention_mask.dtype not in (torch.bool, torch.int32, torch.int64):
                raise ValueError("attention_mask must be bool/integer [B, S]")
            if not bool((attention_mask == 1).all()):
                raise ValueError("padded or nonbinary prompts are unsupported; bucket/trim prompts first")
        if batch != packed_batch.batch_size:
            raise ValueError("input_embeddings batch does not match packed_batch")
        if action_token_mask.shape != (batch, seq) or action_token_mask.dtype != torch.bool:
            raise ValueError("action_token_mask must be bool [B, S]")
        if action_token_mask.device != input_embeddings.device:
            raise ValueError("action_token_mask and input_embeddings must share device")
        counts = action_token_mask.sum(dim=1)
        if not torch.equal(
            counts,
            torch.full_like(counts, self.action_token_count),
        ):
            raise ValueError(f"each sample must contain exactly {self.action_token_count} action tokens")
        if packed_batch.action_chunk_shape != (self.action_chunk_size, self.action_dim):
            raise ValueError("packed_batch action_chunk_shape disagrees with adapter configuration")
        if packed_batch.num_patches_keep.unique().numel() != 1:
            raise ValueError("OFT packed forward requires equal-length buckets")
        if packed_batch.projected_patches.shape[1] != packed_batch.packed_num_patches:
            raise ValueError("projected_patches contains padding; true packed forward requires physical K")
        if (
            self.require_shortened_prefix
            and packed_batch.projected_patches.shape[1] >= packed_batch.num_patches_full
        ):
            raise ValueError("packed forward refuses a non-shortened visual sequence")

        # OpenVLA-OFT appends proprio to the projected visual patch tokens.
        packed_prefix = torch.cat(
            (packed_batch.projected_patches, packed_batch.proprio_token), dim=1
        ).contiguous()
        expected_visual_prefix = packed_batch.packed_num_patches + 1
        if packed_prefix.shape[1] != expected_visual_prefix:
            raise RuntimeError("packed visual/proprio prefix length mismatch")

        # Validate the regression span BEFORE a costly backbone invocation. OFT
        # retains its next-token shifted action readout even with parallel actions.
        prompt_counts = packed_batch.num_prompt_tokens.unique()
        if prompt_counts.numel() != 1:
            raise ValueError("OFT packed forward requires equal prompt lengths per bucket")
        prompt_count = int(prompt_counts.item())
        start = expected_visual_prefix + prompt_count
        end = start + self.action_token_count
        expected_action_mask = torch.zeros_like(action_token_mask)
        first_placeholder = prompt_count + 1
        after_placeholder = first_placeholder + self.action_token_count
        if after_placeholder >= seq:
            raise ValueError("action placeholders require a trailing stop token")
        expected_action_mask[:, first_placeholder:after_placeholder] = True
        if not torch.equal(action_token_mask, expected_action_mask):
            raise ValueError("num_prompt_tokens/action_token_mask disagree with OFT shifted convention")

        # Match official OFT behavior: action placeholder embeddings are zeroed.
        zeroed_inputs = input_embeddings.masked_fill(action_token_mask.unsqueeze(-1), 0)
        multimodal, multimodal_mask = self.build_multimodal_prefix(
            zeroed_inputs, packed_prefix, attention_mask
        )
        position_ids = packed_batch.original_position_ids(seq)
        if position_ids.shape != multimodal.shape[:2]:
            raise RuntimeError("original position IDs do not match packed sequence")
        output: LanguageBackboneOutput = self.language_backbone(
            input_ids=None,
            attention_mask=multimodal_mask,
            position_ids=position_ids,
            past_key_values=None,
            inputs_embeds=multimodal,
            use_cache=False,
            output_attentions=False,
            output_hidden_states=False,
            return_dict=True,
        )
        last_hidden = getattr(output, "last_hidden_state", None)
        if last_hidden is None:
            raise RuntimeError(
                "language backbone must return last_hidden_state; refusing all-layer hidden-state fallback"
            )
        if last_hidden.shape != multimodal.shape:
            raise RuntimeError("language model hidden-state shape changed unexpectedly")

        if end > last_hidden.shape[1]:
            raise IndexError("action hidden-state slice exceeds language-model sequence")
        action_hidden = last_hidden[:, start:end, :]
        if action_hidden.shape[1] != self.action_token_count:
            raise RuntimeError("action hidden-state slice length mismatch")

        return OFTPackedPrefixOutput(
            action_hidden_states=action_hidden,
            multimodal_attention_mask=multimodal_mask,
            sequence_length=last_hidden.shape[1],
            num_visual_prefix_tokens=expected_visual_prefix,
            position_ids=position_ids,
        )


__all__ = ["OFTPackedPrefixAdapter", "OFTPackedPrefixOutput"]

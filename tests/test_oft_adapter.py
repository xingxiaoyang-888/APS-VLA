from dataclasses import dataclass

import pytest
import torch
from torch import nn

from cti_vla.models.abstraction.packing import OFTPackedBatch
from cti_vla.models.abstraction.packing import (
    PACKING_VERSION, PackedPatches, deterministic_topk_mask, mask_from_indices, pack_equal_length,
)
from cti_vla.models.oft_adapter import OFTPackedPrefixAdapter


@dataclass
class FakeBackboneOutput:
    last_hidden_state: torch.Tensor


class FakeLanguageBackbone(nn.Module):
    """Identity-like backbone exposing only the final hidden state."""

    def __init__(self):
        super().__init__()
        self.last_call = None

    def forward(self, **kwargs):
        self.last_call = kwargs
        return FakeBackboneOutput(last_hidden_state=kwargs["inputs_embeds"] + 10.0)


def make_oft_inputs(batch=2, seq=9, hidden=4):
    # Sequence layout before visual prefix: BOS, prompt x2, action x4, stop/pad x2.
    input_embeddings = torch.arange(batch * seq * hidden, dtype=torch.float32).reshape(batch, seq, hidden)
    attention_mask = torch.ones(batch, seq, dtype=torch.long)
    action_mask = torch.zeros(batch, seq, dtype=torch.bool)
    action_mask[:, 3:7] = True
    patches = torch.arange(batch * 6 * hidden, dtype=torch.float32).reshape(batch, 6, hidden)
    scores = torch.tensor([[6.0, 1.0, 5.0, 2.0, 4.0, 3.0], [1.0, 6.0, 2.0, 5.0, 3.0, 4.0]])
    keep_mask = deterministic_topk_mask(scores, keep_count=3)
    packed = pack_equal_length(patches, keep_mask)
    packed_batch = OFTPackedBatch(
        projected_patches=packed.patches,
        proprio_token=torch.full((batch, 1, hidden), 99.0),
        patch_keep_mask=packed.keep_mask,
        num_patches_full=packed.num_patches_full,
        num_patches_keep=torch.full((batch,), 3, dtype=torch.long),
        num_prompt_tokens=torch.full((batch,), 2, dtype=torch.long),
        action_chunk_shape=(2, 2),
    )
    return input_embeddings, attention_mask, action_mask, packed_batch


def test_topk_is_stable_and_respects_valid_mask():
    scores = torch.tensor([[1.0, 1.0, 1.0, 2.0]])
    valid = torch.tensor([[True, True, False, True]])
    keep = deterministic_topk_mask(scores, keep_count=2, valid_mask=valid)
    assert torch.equal(keep, torch.tensor([[True, False, False, True]]))


def test_pack_equal_length_physically_shortens_sequence():
    patches = torch.arange(2 * 5 * 3, dtype=torch.float32).reshape(2, 5, 3)
    mask = torch.tensor([[True, False, True, False, False], [False, True, False, True, False]])
    packed = pack_equal_length(patches, mask)
    assert packed.patches.shape == (2, 2, 3)
    assert packed.num_patches_full == 5
    assert packed.patches.is_contiguous()


def test_pack_rejects_ragged_and_full_shapes():
    patches = torch.ones(2, 4, 3)
    with pytest.raises(ValueError, match="ragged"):
        pack_equal_length(patches, torch.tensor([[True, False, False, False], [True, True, False, False]]))
    with pytest.raises(ValueError, match="reduce"):
        pack_equal_length(patches, torch.ones(2, 4, dtype=torch.bool))


def test_oft_adapter_slices_exact_action_tokens_without_all_layer_states():
    embeddings, attention, action_mask, packed_batch = make_oft_inputs()
    backbone = FakeLanguageBackbone()
    adapter = OFTPackedPrefixAdapter(backbone, action_chunk_size=2, action_dim=2)
    output = adapter(embeddings, packed_batch, attention, action_mask)

    # 3 retained visual patches + 1 proprio + 2 prompt tokens.
    assert packed_batch.action_hidden_start(0) == 6
    assert output.num_visual_prefix_tokens == 4
    assert output.sequence_length == embeddings.shape[1] + 4
    assert output.action_hidden_states.shape == (2, 4, embeddings.shape[-1])
    assert backbone.last_call["output_hidden_states"] is False
    assert backbone.last_call["use_cache"] is False

    # Official OFT slice contains the last prompt state followed by the first
    # three zeroed action-placeholder states (causal next-token convention).
    assert torch.equal(output.action_hidden_states[:, 1:], torch.full_like(output.action_hidden_states[:, 1:], 10.0))
    assert torch.equal(output.action_hidden_states[:, 0], embeddings[:, 2] + 10.0)


def test_oft_adapter_rejects_wrong_prompt_count():
    embeddings, attention, action_mask, packed_batch = make_oft_inputs()
    packed_batch.num_prompt_tokens.fill_(1)
    backbone = FakeLanguageBackbone()
    adapter = OFTPackedPrefixAdapter(backbone, action_chunk_size=2, action_dim=2)
    with pytest.raises(ValueError, match="disagree"):
        adapter(embeddings, packed_batch, attention, action_mask)
    assert backbone.last_call is None


def test_oft_adapter_rejects_wrong_action_count_before_forward():
    embeddings, attention, action_mask, packed_batch = make_oft_inputs()
    action_mask[:, 6] = False
    backbone = FakeLanguageBackbone()
    adapter = OFTPackedPrefixAdapter(backbone, action_chunk_size=2, action_dim=2)
    with pytest.raises(ValueError, match="exactly 4"):
        adapter(embeddings, packed_batch, attention, action_mask)
    assert backbone.last_call is None


def test_sparse_positions_preserve_visual_proprio_and_text_original_ids():
    embeddings, attention, action_mask, packed_batch = make_oft_inputs()
    backbone = FakeLanguageBackbone()
    output = OFTPackedPrefixAdapter(backbone, action_chunk_size=2, action_dim=2)(
        embeddings, packed_batch, attention, action_mask,
    )
    # Full layout: BOS=0, visuals=1..6, proprio=7, original text=8..15.
    # Different selections share the exact same proprio/text/action IDs.
    expected = torch.tensor([
        [0, 1, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        [0, 2, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    ])
    assert torch.equal(output.position_ids, expected)
    assert torch.equal(backbone.last_call["position_ids"], expected)
    assert output.multimodal_attention_mask.shape == expected.shape
    assert bool(output.multimodal_attention_mask.all())
    # Action readout uses physical offsets 6..9, not semantic IDs 9..12.
    assert torch.equal(output.action_hidden_states[:, 0], embeddings[:, 2] + 10)
    assert PACKING_VERSION == "oft-original-positions-v1"


def test_dense_positions_are_contiguous_and_compatible_with_default_rope():
    embeddings, attention, action_mask, sample = make_oft_inputs()
    dense = OFTPackedBatch(
        torch.ones(2, 6, 4), sample.proprio_token,
        torch.ones(2, 6, dtype=torch.bool), 6, torch.full((2,), 6),
        sample.num_prompt_tokens, sample.action_chunk_shape,
    )
    output = OFTPackedPrefixAdapter(
        FakeLanguageBackbone(), action_chunk_size=2, action_dim=2, require_shortened_prefix=False,
    )(embeddings, dense, attention, action_mask)
    assert torch.equal(output.position_ids, torch.arange(16).expand(2, -1))


@pytest.mark.parametrize("bad_mask", [0, 2, -1])
def test_adapter_rejects_nonbinary_or_padded_prompts_before_forward(bad_mask):
    embeddings, attention, action_mask, sample = make_oft_inputs()
    attention[0, -1] = bad_mask
    backbone = FakeLanguageBackbone()
    with pytest.raises(ValueError, match="padded or nonbinary"):
        OFTPackedPrefixAdapter(backbone, action_chunk_size=2, action_dim=2)(
            embeddings, sample, attention, action_mask,
        )
    assert backbone.last_call is None


@pytest.mark.parametrize("indices", [torch.tensor([[1, 1]]), torch.tensor([[3, 1]]), torch.tensor([[0, 6]]), torch.tensor([[-1, 1]])])
def test_original_indices_reject_duplicates_reordering_and_out_of_range(indices):
    with pytest.raises(ValueError):
        mask_from_indices(indices, 6)


def test_packed_metadata_rejects_false_source_indices():
    patches = torch.ones(1, 2, 3)
    mask = torch.tensor([[True, False, True]])
    with pytest.raises(ValueError, match="source_indices"):
        PackedPatches(patches, mask, torch.tensor([[0, 1]]), 3)


def test_full_teacher_packing_is_explicit_and_sparse_values_remain_original():
    patches = torch.arange(18, dtype=torch.float32).reshape(1, 6, 3)
    dense = pack_equal_length(patches, torch.ones(1, 6, dtype=torch.bool), allow_dense=True)
    assert torch.equal(dense.patches, patches)
    mask = mask_from_indices(torch.tensor([[1, 4]]), 6)
    sparse = pack_equal_length(patches, mask)
    assert torch.equal(sparse.patches, patches[:, [1, 4]])
    assert torch.equal(sparse.source_indices, torch.tensor([[1, 4]]))

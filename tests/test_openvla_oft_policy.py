from dataclasses import dataclass

import numpy as np
import pytest
import torch
from torch import nn

from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy


@dataclass
class FakeBackboneOutput:
    last_hidden_state: torch.Tensor


class FakeLanguageBackbone(nn.Module):
    def __init__(self, vocab_size: int, hidden: int):
        super().__init__()
        self.embed_tokens = nn.Embedding(vocab_size, hidden)
        self.last_call = None

    def get_input_embeddings(self):
        return self.embed_tokens

    def forward(self, **kwargs):
        self.last_call = kwargs
        return FakeBackboneOutput(last_hidden_state=kwargs["inputs_embeds"] + 1.0)


class FakeLanguageModel(nn.Module):
    def __init__(self, backbone: nn.Module):
        super().__init__()
        self.model = backbone


class FakeVLA(nn.Module):
    def __init__(self, backbone: FakeLanguageBackbone):
        super().__init__()
        self.language_model = FakeLanguageModel(backbone)
        self.last_unnorm_key = None

    def get_input_embeddings(self):
        return self.language_model.model.get_input_embeddings()

    def _unnormalize_actions(self, normalized_actions, unnorm_key=None):
        self.last_unnorm_key = unnorm_key
        return normalized_actions * 2.0


class FakeProprioProjector(nn.Module):
    def __init__(self, proprio_dim: int, hidden: int):
        super().__init__()
        self.linear = nn.Linear(proprio_dim, hidden, bias=False)

    def forward(self, proprio):
        return self.linear(proprio)


class FakeL1ActionHead(nn.Module):
    def __init__(self, chunk: int, action_dim: int):
        super().__init__()
        self.chunk = chunk
        self.action_dim = action_dim
        self.last_hidden = None

    def predict_action(self, action_hidden_states):
        self.last_hidden = action_hidden_states
        batch = action_hidden_states.shape[0]
        return action_hidden_states.reshape(batch, self.chunk, -1)[..., : self.action_dim]


def make_policy_inputs(batch=2, keep=3, full=5, hidden=4):
    torch.manual_seed(0)
    backbone = FakeLanguageBackbone(vocab_size=32, hidden=hidden)
    vla = FakeVLA(backbone)
    action_head = FakeL1ActionHead(chunk=2, action_dim=2)
    policy = OpenVLAOFTTokenPolicy(
        vla,
        action_head,
        FakeProprioProjector(proprio_dim=3, hidden=hidden),
        num_patches_full=full,
        action_chunk_size=2,
        action_dim=2,
        assistant_empty_token_id=None,
        language_backbone=backbone,
    )
    tokens = torch.randn(batch, keep, hidden)
    proprio = torch.randn(batch, 3)
    input_ids = torch.tensor([[3, 4, 5], [6, 7, 8]], dtype=torch.long)
    attention_mask = torch.ones_like(input_ids)
    keep_mask = torch.tensor(
        [[True, False, True, False, True], [False, True, True, True, False]]
    )
    return policy, vla, backbone, action_head, tokens, proprio, input_ids, attention_mask, keep_mask


def test_forward_from_tokens_uses_official_oft_l1_boundary():
    policy, _, backbone, head, tokens, proprio, input_ids, attention, keep_mask = make_policy_inputs()
    actions = policy.forward_from_tokens(
        tokens,
        proprio,
        input_ids=input_ids,
        attention_mask=attention,
        patch_keep_mask=keep_mask,
    )

    assert actions.shape == (2, 2, 2)
    assert actions.device == tokens.device
    assert not actions.requires_grad
    assert head.last_hidden.shape == (2, 4, 4)
    assert backbone.last_call["use_cache"] is False
    assert backbone.last_call["output_hidden_states"] is False
    # BOS + 3 patches + proprio + 2 prompt + 4 action placeholders + stop.
    assert backbone.last_call["inputs_embeds"].shape[1] == 12


def test_dense_teacher_path_preserves_full_patch_count_without_fake_acceleration():
    policy, _, backbone, _, tokens, proprio, input_ids, attention, _ = make_policy_inputs(keep=5)
    actions = policy.forward_from_tokens(
        tokens,
        proprio,
        input_ids=input_ids,
        attention_mask=attention,
    )
    assert actions.shape == (2, 2, 2)
    assert backbone.last_call["inputs_embeds"].shape[1] == 14


def test_shortened_tokens_require_original_keep_mask_before_forward():
    policy, _, backbone, _, tokens, proprio, input_ids, attention, _ = make_policy_inputs()
    with pytest.raises(ValueError, match="original patch_keep_mask"):
        policy.forward_from_tokens(
            tokens,
            proprio,
            input_ids=input_ids,
            attention_mask=attention,
        )
    assert backbone.last_call is None


def test_padded_prompt_is_rejected_to_prevent_action_index_drift():
    policy, _, backbone, _, tokens, proprio, input_ids, attention, keep_mask = make_policy_inputs()
    attention[0, -1] = 0
    with pytest.raises(ValueError, match="padded prompts"):
        policy.forward_from_tokens(
            tokens,
            proprio,
            input_ids=input_ids,
            attention_mask=attention,
            patch_keep_mask=keep_mask,
        )
    assert backbone.last_call is None


def test_rollout_unnormalization_is_explicit_and_teacher_output_stays_normalized():
    policy, vla, _, _, tokens, proprio, input_ids, attention, keep_mask = make_policy_inputs()
    normalized = policy.forward_from_tokens(
        tokens,
        proprio,
        input_ids=input_ids,
        attention_mask=attention,
        patch_keep_mask=keep_mask,
    )
    physical = policy.predict_rollout_from_tokens(
        tokens,
        proprio,
        input_ids=input_ids,
        attention_mask=attention,
        patch_keep_mask=keep_mask,
        unnorm_key="libero_spatial",
    )
    assert isinstance(physical, np.ndarray)
    assert np.allclose(physical, normalized.detach().numpy() * 2.0)
    assert vla.last_unnorm_key == "libero_spatial"


def test_policy_does_not_register_the_entire_vla_twice():
    policy, _, _, _, _, _, _, _, _ = make_policy_inputs()
    keys = tuple(policy.state_dict().keys())
    assert not any(key.startswith("vla.") for key in keys)
    assert any(key.startswith("prefix_adapter.language_backbone.") for key in keys)


def test_official_assistant_empty_token_is_appended_before_action_placeholders():
    policy, _, backbone, _, tokens, proprio, input_ids, attention, keep_mask = make_policy_inputs()
    policy.assistant_empty_token_id = 9
    policy.forward_from_tokens(
        tokens,
        proprio,
        input_ids=input_ids,
        attention_mask=attention,
        patch_keep_mask=keep_mask,
    )
    # One official empty token is inserted, increasing the multimodal sequence by one.
    assert backbone.last_call["inputs_embeds"].shape[1] == 13


def test_policy_remains_frozen_eval_and_never_backpropagates_to_input_features():
    policy, vla, backbone, _, tokens, proprio, input_ids, attention, keep_mask = make_policy_inputs()
    policy.train()
    assert not policy.training
    assert not backbone.training
    assert not any(parameter.requires_grad for parameter in policy.parameters())
    assert not any(parameter.requires_grad for parameter in vla.parameters())
    tokens.requires_grad_(True)
    proprio.requires_grad_(True)
    output = policy.forward_from_tokens(
        tokens, proprio, input_ids=input_ids, attention_mask=attention, patch_keep_mask=keep_mask,
    )
    assert not output.requires_grad


def test_full_token_callback_and_prepacked_boundary_have_identical_actions_and_layout():
    policy, _, backbone, _, full, proprio, input_ids, attention, keep_mask = make_policy_inputs(keep=5)
    indices = torch.tensor([[0, 2, 4], [1, 2, 3]])
    from_full = policy.forward_from_full_tokens(
        full, proprio, input_ids=input_ids, attention_mask=attention, retained_indices=indices,
    )
    from_full_embeds = backbone.last_call["inputs_embeds"].clone()
    from_full_positions = backbone.last_call["position_ids"].clone()
    packed = full.gather(1, indices.unsqueeze(-1).expand(-1, -1, full.shape[-1]))
    from_packed = policy.forward_from_tokens(
        packed, proprio, input_ids=input_ids, attention_mask=attention, patch_keep_mask=keep_mask,
    )
    assert torch.equal(from_full, from_packed)
    assert torch.equal(from_full_embeds, backbone.last_call["inputs_embeds"])
    assert torch.equal(from_full_positions, backbone.last_call["position_ids"])
    assert torch.equal(backbone.last_call["inputs_embeds"][:, 1:4], packed)


def test_dense_callback_and_explicit_full_set_agree():
    policy, _, backbone, _, tokens, proprio, input_ids, attention, _ = make_policy_inputs(keep=5)
    dense = policy.forward_from_full_tokens(tokens, proprio, input_ids=input_ids, attention_mask=attention)
    explicit = policy.forward_from_full_tokens(
        tokens, proprio, input_ids=input_ids, attention_mask=attention,
        retained_indices=torch.arange(5).expand(2, -1),
    )
    assert torch.equal(dense, explicit)
    assert torch.equal(backbone.last_call["position_ids"], torch.arange(14).expand(2, -1))


def test_language_and_normalized_proprio_are_preserved_under_deletion():
    policy, _, backbone, _, tokens, proprio, input_ids, attention, _ = make_policy_inputs(keep=5)
    policy.forward_from_full_tokens(tokens, proprio, input_ids=input_ids, attention_mask=attention)
    dense_inputs = backbone.last_call["inputs_embeds"].clone()
    dense_positions = backbone.last_call["position_ids"].clone()
    policy.forward_from_full_tokens(
        tokens, proprio, input_ids=input_ids, attention_mask=attention,
        retained_indices=torch.tensor([[1, 3], [0, 4]]),
    )
    sparse_inputs = backbone.last_call["inputs_embeds"]
    # After BOS and visual tokens, proprio and every language/action token agree.
    assert torch.equal(dense_inputs[:, 6:], sparse_inputs[:, 3:])
    assert torch.equal(dense_positions[:, 6:], backbone.last_call["position_ids"][:, 3:])
    assert torch.equal(sparse_inputs[:, 3], policy.proprio_projector(proprio))


class ContextBackbone(FakeLanguageBackbone):
    """Small deterministic contextual model for deletion/condition behavior only."""

    def forward(self, **kwargs):
        self.last_call = kwargs
        x = kwargs["inputs_embeds"]
        # Prefix sums stand in for causal contextual mixing; this is not a VLA.
        context = x.cumsum(1)
        return FakeBackboneOutput(context + kwargs["position_ids"].unsqueeze(-1) / 10)


def test_actual_removal_and_both_conditions_can_affect_contextual_actions():
    torch.manual_seed(41)
    backbone = ContextBackbone(32, 4)
    vla = FakeVLA(backbone)
    policy = OpenVLAOFTTokenPolicy(
        vla, FakeL1ActionHead(2, 2), FakeProprioProjector(3, 4), num_patches_full=5,
        action_chunk_size=2, action_dim=2, assistant_empty_token_id=None,
    )
    tokens = torch.ones(1, 5, 4)
    proprio = torch.ones(1, 3)
    ids = torch.tensor([[3, 4, 5]])
    attention = torch.ones_like(ids)
    def run(visual, state, prompt, selection=None):
        return policy.forward_from_full_tokens(
            visual, state, input_ids=prompt, attention_mask=attention, retained_indices=selection,
        )
    full = run(tokens, proprio, ids)
    sparse = run(tokens, proprio, ids, torch.tensor([[0, 2, 4]]))
    assert backbone.last_call["inputs_embeds"].shape[1] == 12
    assert not torch.equal(full, sparse)
    assert not torch.equal(full, run(tokens, proprio * 2, ids))
    assert not torch.equal(full, run(tokens, proprio, torch.tensor([[3, 9, 5]])))


def test_assistant_empty_token_is_not_duplicated():
    policy, _, backbone, _, tokens, proprio, ids, attention, keep = make_policy_inputs()
    policy.assistant_empty_token_id = 9
    ids[:, -1] = 9
    policy.forward_from_tokens(tokens, proprio, input_ids=ids, attention_mask=attention, patch_keep_mask=keep)
    assert backbone.last_call["inputs_embeds"].shape[1] == 12

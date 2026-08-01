from dataclasses import dataclass

import numpy as np
import pytest
import torch
from torch import nn

from diwa.data.contracts import TokenBatch
from diwa.data.interventions import MatchedMeanBaseline
from diwa.models.influence.teacher import CounterfactualTeacher
from diwa.models.openvla_oft_policy import OpenVLAOFTTokenPolicy


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
    assert actions.requires_grad
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


def test_counterfactual_teacher_integrates_with_dense_oft_token_policy():
    policy, _, _, _, tokens, proprio, input_ids, attention, _ = make_policy_inputs(keep=5)
    batch = TokenBatch(
        z=tokens + 1.0,
        token_type=torch.tensor([[0, 0, 1, 1, 1], [0, 0, 1, 1, 1]]),
        frame_id=torch.tensor([[0, 0, 0, 1, 1], [0, 0, 0, 1, 1]]),
        camera_id=torch.tensor([[0, 0, 0, 1, 1], [0, 0, 0, 1, 1]]),
        valid=torch.ones(2, 5, dtype=torch.bool),
        query=torch.ones(2, 4),
        proprio=proprio,
    )
    baseline = MatchedMeanBaseline()(batch.z, batch.token_type, batch.frame_id, batch.camera_id)
    candidate = torch.zeros_like(batch.valid)
    candidate[:, 0] = True
    targets = CounterfactualTeacher(policy.eval(), action_chunk_shape=(2, 2)).estimate(
        batch,
        baseline,
        torch.zeros_like(batch.valid),
        candidate,
        policy_inputs={"input_ids": input_ids, "attention_mask": attention},
    )
    assert targets.influence.shape == (2,)
    assert not targets.influence.requires_grad

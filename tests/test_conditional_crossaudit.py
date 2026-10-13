"""Independent packing/readout oracles and the real-policy smoke interface."""

from types import SimpleNamespace

import pytest
import torch
from torch import nn

from cti_vla.evaluation.conditional_smoke import run_conditional_smoke
from cti_vla.labeling import LabelProvenance
from cti_vla.models.abstraction.packing import PACKING_VERSION
from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy


class PositionBackbone(nn.Module):
    def __init__(self, hidden=4):
        super().__init__()
        self.embed_tokens = nn.Embedding(40, hidden)
        self.calls = []

    def forward(self, **kwargs):
        self.calls.append(kwargs)
        hidden = kwargs["position_ids"].to(kwargs["inputs_embeds"].dtype)[..., None].expand_as(kwargs["inputs_embeds"])
        return SimpleNamespace(last_hidden_state=hidden)


class VLA(nn.Module):
    def __init__(self, backbone):
        super().__init__()
        self.backbone = backbone

    def get_input_embeddings(self):
        return self.backbone.embed_tokens


class Head(nn.Module):
    def __init__(self, chunk, action_dim):
        super().__init__()
        self.chunk, self.action_dim = chunk, action_dim

    def predict_action(self, hidden):
        return hidden[..., 0].reshape(hidden.shape[0], self.chunk, self.action_dim)


def make_policy(full=6, chunk=2, action_dim=2):
    backbone = PositionBackbone()
    vla = VLA(backbone)
    policy = OpenVLAOFTTokenPolicy(
        vla, Head(chunk, action_dim), nn.Linear(3, 4), num_patches_full=full,
        action_chunk_size=chunk, action_dim=action_dim, assistant_empty_token_id=None, language_backbone=backbone,
    )
    return policy, vla, backbone


def test_original_positions_keep_proprio_text_and_shifted_actions_fixed_after_deletion():
    policy, vla, backbone = make_policy()
    features, proprio = torch.randn(2, 6, 4), torch.zeros(2, 3)
    ids = torch.tensor([[3, 4, 5, 6], [3, 7, 8, 9]])
    attention = torch.ones_like(ids)
    dense = policy.forward_from_full_tokens(features, proprio, input_ids=ids, attention_mask=attention)
    sparse = policy.forward_from_full_tokens(features, proprio, input_ids=ids, attention_mask=attention,
                                             retained_indices=torch.tensor([[0, 4], [1, 5]]))
    # Full semantic positions: BOS0, visual1..6, proprio7, prompt8..10,
    # placeholders11..14, stop15. OFT reads the LAST prompt hidden (10)
    # plus the first 3 placeholders (11..13), preserving the prediction shift.
    expected_actions = torch.tensor([[[10., 11.], [12., 13.]]] * 2)
    torch.testing.assert_close(dense, expected_actions)
    torch.testing.assert_close(sparse, expected_actions)
    assert backbone.calls[0]["position_ids"].tolist() == [list(range(16))] * 2
    assert backbone.calls[1]["position_ids"].tolist() == [
        [0, 1, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        [0, 2, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    ]
    call = backbone.calls[1]
    assert call["attention_mask"].shape == (2, 12) and call["attention_mask"].all()
    assert not call["inputs_embeds"][:, 7:11].any()  # Only placeholder embeddings are zeroed.
    torch.testing.assert_close(call["inputs_embeds"][:, -1], vla.get_input_embeddings()(torch.tensor([2, 2])))
    assert call["past_key_values"] is None and call["use_cache"] is False


def test_real_policy_smoke_interface_uses_seven_queries_then_one_deployment(tmp_path):
    policy, vla, backbone = make_policy(full=512, chunk=8, action_dim=7)
    with torch.inference_mode():
        projected = torch.randn(1, 512, 4)
        ids = torch.tensor([[3, 4, 5, 6]])
        inputs = {"input_ids": ids, "attention_mask": torch.ones_like(ids), "normalized_proprio": torch.zeros(1, 3)}
    provenance = LabelProvenance(("a",), ("episode-a",), "train", "mock", "mock", "mock",
                                  PACKING_VERSION, "mock", "mock")
    result = run_conditional_smoke(policy, projected, inputs, provenance, cache_directory=tmp_path, hidden_dim=8)
    assert result["teacher_batched_calls"] == result["teacher_calls_per_observation"] == 7
    assert result["teacher_sample_forwards"] == 7 and result["final_deployment_policy_calls"] == 1
    assert len(backbone.calls) == 8 and result["scale_fit_labels"] == 4 and result["optimizer_labels"] == 2
    assert result["scale_fit_unique_observations"] == 1 and len(result["selected_indices"][0]) == 64
    assert result["cache_roundtrip"] and result["scorer_updated"] and not result["policy_gradients"]
    assert not list(tmp_path.iterdir())  # No model weight or cache survives this smoke.
    with torch.inference_mode(), pytest.raises(ValueError, match="outside"):
        run_conditional_smoke(policy, projected, inputs, provenance, cache_directory=tmp_path)

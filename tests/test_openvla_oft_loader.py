from collections import OrderedDict

import pytest
import torch

from cti_vla.models.openvla_oft_loader import (
    OpenVLAOFTL1ActionHead,
    OpenVLAOFTProprioProjector,
    remove_uniform_ddp_prefix,
)
from cti_vla.models.openvla_oft_runtime_compat import (
    ACTION_DIM,
    ACTION_TOKEN_BEGIN_IDX,
    IGNORE_INDEX,
    get_current_action_mask,
    get_next_actions_mask,
    install_prismatic_runtime_compat,
    validate_oft_sdpa_runtime,
)


def test_ddp_prefix_removal_is_uniform_and_collision_safe():
    weight = torch.ones(2)
    stripped = remove_uniform_ddp_prefix(
        OrderedDict((key, weight) for key in ("module.first", "module.second"))
    )
    assert list(stripped) == ["first", "second"]
    with pytest.raises(ValueError, match="mixes"):
        remove_uniform_ddp_prefix({"module.first": weight, "second": weight})
    with pytest.raises(ValueError, match="empty"):
        remove_uniform_ddp_prefix({})
    with pytest.raises(TypeError, match="tensors"):
        remove_uniform_ddp_prefix({"module.first": object()})


def test_l1_action_head_enforces_chunk_hidden_contract():
    head = OpenVLAOFTL1ActionHead(hidden_dim=4, action_chunk_size=2, action_dim=3)
    hidden = torch.randn(2, 6, 4)
    assert head.predict_action(hidden).shape == (2, 2, 3)
    with pytest.raises(ValueError, match="action hidden states"):
        head.predict_action(torch.randn(2, 5, 4))
    invalid = hidden.clone()
    invalid[0, 0, 0] = float("nan")
    with pytest.raises(ValueError, match="NaN/Inf"):
        head.predict_action(invalid)


def test_proprio_projector_enforces_eight_dimensional_boundary():
    projector = OpenVLAOFTProprioProjector(hidden_dim=4, proprio_dim=8)
    assert projector(torch.randn(2, 8)).shape == (2, 4)
    with pytest.raises(ValueError, match=r"\[B, 8\]"):
        projector(torch.randn(2, 7))


def test_remote_code_action_masks_match_frozen_libero_definition():
    labels = torch.tensor(
        [[IGNORE_INDEX, ACTION_TOKEN_BEGIN_IDX + 1] * (ACTION_DIM + 1)], dtype=torch.long
    )
    current = get_current_action_mask(labels)
    following = get_next_actions_mask(labels)
    expected_current = (labels > ACTION_TOKEN_BEGIN_IDX) & (
        torch.cumsum(labels != IGNORE_INDEX, dim=1) <= ACTION_DIM
    )
    assert torch.equal(current, expected_current)
    assert not bool((current & following).any())
    assert torch.equal(current | following, labels > ACTION_TOKEN_BEGIN_IDX)


def test_minimal_runtime_refuses_to_override_imported_prismatic(monkeypatch):
    monkeypatch.setitem(__import__("sys").modules, "prismatic", object())
    with pytest.raises(RuntimeError, match="before any prismatic import"):
        install_prismatic_runtime_compat(use_minimal_compat=True)


def test_runtime_rejects_a_different_same_named_sdpa_implementation(monkeypatch):
    import sys
    from types import ModuleType
    module = ModuleType("transformers.models.llama.modeling_llama")
    class UnverifiedSdpa:
        def forward(self, value):
            return value
    module.LlamaSdpaAttention = UnverifiedSdpa
    monkeypatch.setitem(sys.modules, module.__name__, module)
    with pytest.raises(RuntimeError, match="audited non-causal SDPA fork"):
        validate_oft_sdpa_runtime()

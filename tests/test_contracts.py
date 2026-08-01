import pytest
import torch

from diwa.data.contracts import OFTPackedBatch, TokenBatch
from diwa.data.interventions import EMABaseline, MatchedMeanBaseline, apply_intervention


def make_tokens(batch=2, tokens=4, hidden=3):
    z = torch.arange(batch * tokens * hidden, dtype=torch.float32).reshape(batch, tokens, hidden) + 1
    meta = torch.zeros((batch, tokens), dtype=torch.long)
    return TokenBatch(
        z=z,
        token_type=meta.clone(),
        frame_id=meta.clone(),
        camera_id=meta.clone(),
        valid=torch.ones((batch, tokens), dtype=torch.bool),
        query=torch.ones((batch, hidden)),
        proprio=torch.ones((batch, 2)),
    )


def test_token_batch_contract():
    batch = make_tokens()
    assert batch.batch_size == 2
    assert batch.num_tokens == 4
    assert batch.hidden_dim == 3


def test_token_batch_rejects_missing_valid_token():
    batch = make_tokens()
    batch.valid[0, :] = False
    with pytest.raises(ValueError, match="at least one valid token"):
        TokenBatch(**batch.__dict__)


def test_packed_batch_preserves_action_index():
    packed = OFTPackedBatch(
        projected_patches=torch.ones(2, 2, 3),
        proprio_token=torch.ones(2, 1, 3),
        patch_keep_mask=torch.tensor([[True, False, True], [False, True, True]]),
        num_patches_full=3,
        num_patches_keep=torch.tensor([2, 2]),
        num_prompt_tokens=torch.tensor([5, 5]),
    )
    assert packed.action_hidden_start(0) == 8


def test_packed_batch_rejects_index_mismatch():
    with pytest.raises(ValueError, match="disagrees"):
        OFTPackedBatch(
            projected_patches=torch.ones(1, 2, 3),
            proprio_token=torch.ones(1, 1, 3),
            patch_keep_mask=torch.tensor([[True, False, True]]),
            num_patches_full=3,
            num_patches_keep=torch.tensor([1]),
            num_prompt_tokens=torch.tensor([5]),
        )


def test_zero_baseline_is_forbidden():
    z = make_tokens().z
    with pytest.raises(ValueError, match="all-zero"):
        apply_intervention(z, torch.tensor([[True, False, False, False], [True, False, False, False]]), torch.zeros_like(z))


def test_matched_mean_and_intervention_are_detached():
    batch = make_tokens()
    baseline = MatchedMeanBaseline()(batch.z, batch.token_type, batch.frame_id, batch.camera_id)
    intervened = apply_intervention(batch.z, torch.tensor([[True, False, False, False]] * 2), baseline)
    assert not baseline.requires_grad
    assert not intervened.requires_grad
    assert not torch.equal(intervened, batch.z)


def test_ema_requires_update():
    ema = EMABaseline()
    with pytest.raises(RuntimeError, match="uninitialized"):
        ema(torch.ones(2, 3))
    ema.update(torch.ones(2, 3))
    with pytest.raises(ValueError, match="all-zero"):
        # Explicitly exercise the safety check through an invalid prototype.
        ema._prototype.zero_()
        ema(torch.ones(2, 3))


def test_token_batch_rejects_nonfinite_float_fields():
    batch = make_tokens()
    batch.query[0, 0] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        TokenBatch(**batch.__dict__)

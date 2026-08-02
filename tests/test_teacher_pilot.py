import torch

from diwa.data.interventions import MatchedMeanBaseline
from diwa.evaluation.teacher_pilot_openvla_oft import _build_token_batch, _make_selector_scores


def test_teacher_pilot_builds_explicit_two_camera_metadata_and_full_count():
    projected = torch.zeros(1, 512, 8, dtype=torch.bfloat16)
    projected[:, :256] = 1
    projected[:, 256:] = 2
    proprio = torch.ones(1, 8, dtype=torch.bfloat16)
    batch = _build_token_batch(projected, proprio)

    assert batch.z.shape == (1, 512, 8)
    assert torch.all(batch.frame_id == 0)
    assert torch.equal(batch.camera_id[0, :256], torch.zeros(256, dtype=torch.long))
    assert torch.equal(batch.camera_id[0, 256:], torch.ones(256, dtype=torch.long))
    baseline = MatchedMeanBaseline()(batch.z, batch.token_type, batch.frame_id, batch.camera_id, batch.valid)
    assert float(baseline.abs().mean()) > 0.0


def test_teacher_pilot_selector_is_finite_and_masks_invalid_tokens():
    projected = torch.randn(1, 512, 8, dtype=torch.bfloat16)
    batch = _build_token_batch(projected, torch.ones(1, 8, dtype=torch.bfloat16))
    batch.valid[:, 7] = False
    scores = _make_selector_scores(batch)
    assert scores.shape == (1, 512)
    assert torch.isfinite(scores).all()
    assert scores[0, 7] == 0
    assert not scores.requires_grad

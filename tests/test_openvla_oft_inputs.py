from io import BytesIO
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from PIL import Image

from cti_vla.models.openvla_oft_inputs import format_prompt, normalize_proprio, prepare_rlds_inputs


def test_prompt_uses_official_question_template():
    assert format_prompt("Pick Up The Cup") == "In: What action should the robot take to pick up the cup?\nOut:"
    with pytest.raises(ValueError):
        format_prompt("")


def test_proprio_mask_and_bounds_match_checkpoint_normalization():
    stats = {"q01": np.zeros(8), "q99": np.full(8, 2), "mask": [True] * 7 + [False]}
    raw = np.array([0, 1, 2, 3, -1, .5, 1.5, .25])
    expected = np.array([-1, 0, 1, 1, -1, -.5, .5, .25], dtype=np.float32)
    assert np.allclose(normalize_proprio(raw, stats), expected)
    assert normalize_proprio(raw, stats).dtype == np.float32
    stats["q99"][0] = -1
    with pytest.raises(ValueError, match="upper bounds"):
        normalize_proprio(raw, stats)


def test_prepare_preserves_camera_order_and_allows_last_observation():
    def jpeg(color):
        output = BytesIO()
        Image.new("RGB", (16, 16), color=color).save(output, format="JPEG")
        return output.getvalue()
    def processor(prompt, image, return_tensors):
        # A deterministic stand-in, used only to inspect input routing.
        value = np.asarray(image).mean() / 255
        return {"input_ids": torch.tensor([[1, 3, 5]]), "attention_mask": torch.ones(1, 3, dtype=torch.long),
                "pixel_values": torch.full((1, 6, 4, 4), float(value))}
    episode = SimpleNamespace(
        num_steps=1, instructions=("move cup",), images=(jpeg("white"),), wrist_images=(jpeg("black"),),
        proprio=np.ones((1, 8)),
    )
    result = prepare_rlds_inputs(
        episode, 0, processor, {"q01": np.zeros(8), "q99": np.full(8, 2)},
        device="cpu", dtype=torch.float32,
    )
    assert result["pixel_values"].shape == (1, 12, 4, 4)
    assert torch.equal(result["pixel_values"][:, :6], torch.ones(1, 6, 4, 4))
    assert torch.equal(result["pixel_values"][:, 6:], torch.zeros(1, 6, 4, 4))
    assert torch.allclose(result["normalized_proprio"], torch.zeros(1, 8))
    assert result["inputs_version"] == "rlds-processor-only-oft-prompt-bounds-q99-v1"

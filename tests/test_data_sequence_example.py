import math
import struct

import numpy as np
import pytest

from cti_vla.data.sequence_example import _example_class, decode_libero_example, iter_libero_examples
from cti_vla.data.tfrecord import _masked_crc32c


def _payload(*, steps=3, mutate=None):
    message = _example_class()()
    features = message.features.feature
    features["episode_metadata/file_path"].bytes_list.value.append(b"task/demo_0")
    features["steps/action"].float_list.value.extend(float(index) for index in range(steps * 7))
    features["steps/observation/state"].float_list.value.extend(float(index) for index in range(steps * 8))
    features["steps/observation/joint_state"].float_list.value.extend(float(index) for index in range(steps * 7))
    features["steps/reward"].float_list.value.extend([0.0] * (steps - 1) + [1.0])
    features["steps/discount"].float_list.value.extend([1.0] * steps)
    features["steps/is_first"].int64_list.value.extend([1] + [0] * (steps - 1))
    features["steps/is_last"].int64_list.value.extend([0] * (steps - 1) + [1])
    features["steps/is_terminal"].int64_list.value.extend([0] * steps)
    features["steps/language_instruction"].bytes_list.value.extend([b"pick up the block"] * steps)
    features["steps/observation/image"].bytes_list.value.extend([b"\xff\xd8rgb\xff\xd9"] * steps)
    features["steps/observation/wrist_image"].bytes_list.value.extend([b"\xff\xd8wrist\xff\xd9"] * steps)
    if mutate is not None:
        mutate(features)
    return message.SerializeToString()


def _record(payload):
    length = struct.pack("<Q", len(payload))
    return length + struct.pack("<I", _masked_crc32c(length)) + payload + struct.pack("<I", _masked_crc32c(payload))


def test_flat_example_decodes_timestep_aligned_contract(tmp_path):
    payload = _payload(steps=3)
    episode = decode_libero_example(payload)
    assert episode.episode_id.startswith("libero-episode-sha256:")
    assert episode.episode_file_path == "task/demo_0"
    assert episode.actions.shape == (3, 7)
    assert episode.proprio.shape == (3, 8)
    assert episode.joint_state.shape == (3, 7)
    assert len(episode.images) == len(episode.wrist_images) == 3
    assert episode.instructions == ("pick up the block",) * 3
    assert not episode.actions.flags.writeable

    path = tmp_path / "sample.tfrecord"
    path.write_bytes(_record(payload))
    streamed = list(iter_libero_examples(path))
    assert [item.episode_id for item in streamed] == [episode.episode_id]
    assert streamed[0].episode_file_path == "task/demo_0"
    assert streamed[0].record_index == 0


@pytest.mark.parametrize(
    "mutate,match",
    [
        (lambda features: features.pop("steps/action"), "missing required"),
        (lambda features: features["steps/action"].float_list.value.pop(), "steps/action has"),
        (lambda features: features["steps/observation/state"].float_list.value.pop(), "observation/state has"),
        (lambda features: features["steps/observation/wrist_image"].bytes_list.value.pop(), "wrist_image has"),
        (lambda features: features["steps/action"].float_list.value.__setitem__(0, math.nan), "NaN or Inf"),
        (lambda features: features["steps/is_first"].int64_list.value.__setitem__(1, 1), "true only"),
        (lambda features: features["steps/observation/image"].bytes_list.value.__setitem__(0, b"not-jpeg"), "non-JPEG"),
    ],
)
def test_flat_example_rejects_contract_violations(mutate, match):
    with pytest.raises(ValueError, match=match):
        decode_libero_example(_payload(mutate=mutate))


def test_decoder_enforces_episode_and_record_bounds(tmp_path):
    with pytest.raises(ValueError, match="step count"):
        decode_libero_example(_payload(steps=3), max_episode_steps=2)
    path = tmp_path / "sample.tfrecord"
    payload = _payload()
    path.write_bytes(_record(payload))
    with pytest.raises(ValueError, match="safety limit"):
        list(iter_libero_examples(path, max_record_bytes=len(payload) - 1))


def test_original_id_stays_stable_and_duplicates_are_rejected(tmp_path):
    from cti_vla.data.sequence_example import discover_episodes
    path = tmp_path / "first.tfrecord"
    other = tmp_path / "second.tfrecord"
    path.write_bytes(_record(_payload()))
    other.write_bytes(_record(_payload()))
    assert list(iter_libero_examples(path))[0].episode_id == list(iter_libero_examples(other))[0].episode_id
    inventory = discover_episodes([path])
    assert inventory[0].episode_id.startswith("libero-episode-sha256:")
    assert inventory[0].episode_file_path == "task/demo_0"
    assert inventory[0].task_name == "pick up the block"
    with pytest.raises(ValueError, match="duplicate original"):
        discover_episodes([path, other])


def test_wrong_feature_kind_and_malformed_proto_rejected():
    with pytest.raises(ValueError, match="must use float_list"):
        decode_libero_example(_payload(mutate=lambda features: features["steps/action"].bytes_list.value.append(b"1")))
    with pytest.raises(ValueError, match="protobuf"):
        decode_libero_example(b"\xff")


def test_nonconstant_language_needs_explicit_adapter(tmp_path):
    from cti_vla.data.sequence_example import discover_episodes
    path = tmp_path / "changing.tfrecord"
    path.write_bytes(_record(_payload(mutate=lambda features: features["steps/language_instruction"].bytes_list.value.__setitem__(1, b"other task"))))
    with pytest.raises(ValueError, match="changing instructions"):
        discover_episodes([path])


def test_content_identity_ignores_storage_path_but_distinguishes_demos(tmp_path):
    from cti_vla.data.sequence_example import discover_episodes
    original = _payload()
    renamed = _payload(mutate=lambda f: f["episode_metadata/file_path"].bytes_list.value.__setitem__(0, b"other/machine/task.hdf5"))
    another_demo = _payload(mutate=lambda f: f["steps/action"].float_list.value.__setitem__(0, 1.0))
    assert decode_libero_example(original).episode_id == decode_libero_example(renamed).episode_id
    assert decode_libero_example(original).episode_id != decode_libero_example(another_demo).episode_id
    path = tmp_path / "many-demos-one-hdf5.tfrecord"
    path.write_bytes(_record(original) + _record(another_demo))
    assert len(discover_episodes([path])) == 2
    path.write_bytes(_record(original) + _record(renamed))
    with pytest.raises(ValueError, match="duplicate original"):
        discover_episodes([path])

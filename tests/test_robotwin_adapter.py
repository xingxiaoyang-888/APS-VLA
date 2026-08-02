import io
import json

import numpy as np
import pytest

from diwa.data.robotwin import (
    ROBOTWIN_ACTION_REPRESENTATION,
    RobotTwinHDF5Adapter,
    reject_libero_openvla_oft_for_robotwin,
    validate_robotwin_native_contract,
)


h5py = pytest.importorskip("h5py")
Image = pytest.importorskip("PIL.Image")


def make_episode(tmp_path, *, nonfinite=False):
    dataset_root = tmp_path / "dataset"
    episode_root = dataset_root / "task_a" / "aloha-agilex_clean_50"
    data_root = episode_root / "data"
    instructions_root = episode_root / "instructions"
    data_root.mkdir(parents=True)
    instructions_root.mkdir()
    instructions_root.joinpath("episode0.json").write_text(
        json.dumps({"seen": ["move the object"]}), encoding="utf-8"
    )

    encoded_buffer = io.BytesIO()
    Image.new("RGB", (8, 6), color=(10, 20, 30)).save(encoded_buffer, format="JPEG")
    encoded = encoded_buffer.getvalue()
    action = np.arange(12 * 14, dtype=np.float64).reshape(12, 14) / 100
    if nonfinite:
        action[3, 2] = np.nan
    episode_path = data_root / "episode0.hdf5"
    with h5py.File(episode_path, "w") as handle:
        joint = handle.create_group("joint_action")
        joint.create_dataset("vector", data=action)
        joint.create_dataset("left_arm", data=action[:, :6])
        joint.create_dataset("left_gripper", data=action[:, 6])
        joint.create_dataset("right_arm", data=action[:, 7:13])
        joint.create_dataset("right_gripper", data=action[:, 13])
        endpose = handle.create_group("endpose")
        endpose.create_dataset("left_endpose", data=np.ones((12, 7)))
        endpose.create_dataset("left_gripper", data=np.ones(12))
        endpose.create_dataset("right_endpose", data=np.ones((12, 7)))
        endpose.create_dataset("right_gripper", data=np.ones(12))
        observation = handle.create_group("observation")
        for camera in ("head_camera", "right_camera"):
            camera_group = observation.create_group(camera)
            camera_group.create_dataset("rgb", data=np.asarray([encoded] * 12, dtype=f"S{len(encoded)}"))
    return dataset_root, episode_path


def test_robotwin_sample_uses_next_action_and_bounded_decode(tmp_path):
    dataset_root, episode_path = make_episode(tmp_path)
    adapter = RobotTwinHDF5Adapter(dataset_root)
    sample = adapter.load_sample(episode_path, 0)
    assert sample.action_representation == ROBOTWIN_ACTION_REPRESENTATION
    assert sample.proprio.shape == (14,)
    assert sample.action_chunk.shape == (8, 14)
    assert np.allclose(sample.action_chunk[0], np.arange(14, 28) / 100)
    assert sample.action_valid_mask.all()
    assert sample.images["head_camera"].shape == (6, 8, 3)
    assert sample.instruction == "move the object"


def test_robotwin_tail_chunk_has_explicit_mask_and_padding(tmp_path):
    dataset_root, episode_path = make_episode(tmp_path)
    sample = RobotTwinHDF5Adapter(dataset_root).load_sample(episode_path, 10, decode_images=False)
    assert sample.action_valid_mask.tolist() == [True, False, False, False, False, False, False, False]
    assert np.allclose(sample.action_chunk, sample.action_chunk[0])
    assert sample.images == {}


def test_robotwin_audit_rejects_nonfinite_actions(tmp_path):
    dataset_root, episode_path = make_episode(tmp_path, nonfinite=True)
    with pytest.raises(ValueError, match="NaN/Inf"):
        RobotTwinHDF5Adapter(dataset_root).inspect_episode(episode_path)


def test_native_contract_and_libero_policy_gate_are_separate():
    with pytest.raises(ValueError, match="do not slice 14D"):
        validate_robotwin_native_contract(action_dim=7, proprio_dim=8, num_images=2)
    validate_robotwin_native_contract(action_dim=14, proprio_dim=14, num_images=2)
    with pytest.raises(RuntimeError, match="RoboTwin-trained policy"):
        reject_libero_openvla_oft_for_robotwin()

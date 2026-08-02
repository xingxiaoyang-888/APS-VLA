"""Read-only RoboTwin HDF5 contracts and bounded dataset auditing."""

from __future__ import annotations

import io
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

import numpy as np

from .identity import stable_sample_id


ROBOTWIN_ACTION_DIM = 14
ROBOTWIN_PROPRIO_DIM = 14
ROBOTWIN_CAMERAS = ("front_camera", "head_camera", "left_camera", "right_camera")
ROBOTWIN_ACTION_REPRESENTATION = "joint_position_absolute_bimanual"
_EPISODE_PATTERN = re.compile(r"^episode(\d+)\.hdf5$")


def _require_h5py() -> Any:
    try:
        import h5py
    except ImportError as error:
        raise RuntimeError("RoboTwin support requires the 'robotwin' optional dependencies") from error
    return h5py


def _episode_index(path: Path) -> int:
    match = _EPISODE_PATTERN.fullmatch(path.name)
    if match is None:
        raise ValueError(f"invalid RoboTwin episode filename: {path.name}")
    return int(match.group(1))


def validate_robotwin_native_contract(
    *,
    action_dim: int,
    proprio_dim: int,
    num_images: int,
) -> None:
    actual = (action_dim, proprio_dim, num_images)
    required = (ROBOTWIN_ACTION_DIM, ROBOTWIN_PROPRIO_DIM, 2)
    if actual != required:
        raise ValueError(
            "RoboTwin native joint contract mismatch: "
            f"got action/proprio/images={actual}, required={required}; do not slice 14D bimanual "
            "actions into the LIBERO 7D action head"
        )


def reject_libero_openvla_oft_for_robotwin() -> None:
    raise RuntimeError(
        "the selected LIBERO OpenVLA-OFT checkpoint has a 7D single-arm action/proprio contract, "
        "but native RoboTwin uses 14D absolute bimanual joints; a RoboTwin-trained policy/action "
        "head and matching normalization statistics are required before model-level DIWA tests"
    )


@dataclass(frozen=True)
class RobotTwinEpisodeMetadata:
    path: Path
    task: str
    embodiment: str
    episode_index: int
    num_steps: int
    action_dim: int
    proprio_dim: int
    cameras: tuple[str, ...]
    max_checked_encoded_image_bytes: int


@dataclass(frozen=True)
class RobotTwinSample:
    sample_id: int
    task: str
    embodiment: str
    episode_index: int
    step_index: int
    instruction: str
    proprio: np.ndarray
    action_chunk: np.ndarray
    action_valid_mask: np.ndarray
    images: Mapping[str, np.ndarray]
    action_representation: str = ROBOTWIN_ACTION_REPRESENTATION

    def __post_init__(self) -> None:
        if self.proprio.shape != (ROBOTWIN_PROPRIO_DIM,) or self.proprio.dtype != np.float32:
            raise ValueError("RoboTwin proprio must be float32 [14]")
        if self.action_chunk.ndim != 2 or self.action_chunk.shape[1] != ROBOTWIN_ACTION_DIM:
            raise ValueError("RoboTwin action_chunk must have shape [K,14]")
        if self.action_chunk.dtype != np.float32:
            raise TypeError("RoboTwin action_chunk must be float32")
        if self.action_valid_mask.shape != (self.action_chunk.shape[0],):
            raise ValueError("action_valid_mask must have shape [K]")
        if self.action_valid_mask.dtype != np.bool_ or not self.action_valid_mask.any():
            raise ValueError("action_valid_mask must be bool with at least one valid action")
        if not np.isfinite(self.proprio).all() or not np.isfinite(self.action_chunk).all():
            raise ValueError("RoboTwin proprio/action must contain only finite values")
        for camera, image in self.images.items():
            if camera not in ROBOTWIN_CAMERAS:
                raise ValueError(f"unknown RoboTwin camera: {camera}")
            if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
                raise ValueError("decoded RoboTwin images must be uint8 [H,W,3]")


@dataclass(frozen=True)
class RobotTwinAuditSummary:
    dataset_root: str
    tasks: tuple[str, ...]
    episodes_checked: int
    min_steps: int
    max_steps: int
    action_dim: int
    proprio_dim: int
    cameras: tuple[str, ...]
    max_checked_encoded_image_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RobotTwinHDF5Adapter:
    """Read native RoboTwin episodes without mutating or eagerly decoding them."""

    def __init__(
        self,
        dataset_root: str | Path,
        *,
        cameras: Sequence[str] = ("head_camera", "right_camera"),
        action_chunk_size: int = 8,
        max_episode_steps: int = 100_000,
        max_encoded_image_bytes: int = 8 * 1024 * 1024,
        max_decoded_pixels: int = 16 * 1024 * 1024,
    ) -> None:
        self.dataset_root = Path(dataset_root)
        if not self.dataset_root.is_dir():
            raise FileNotFoundError(self.dataset_root)
        self.cameras = tuple(cameras)
        if len(self.cameras) != 2 or len(set(self.cameras)) != 2:
            raise ValueError("RoboTwin/OpenVLA pilot requires exactly two distinct cameras")
        if any(camera not in ROBOTWIN_CAMERAS for camera in self.cameras):
            raise ValueError(f"cameras must be selected from {ROBOTWIN_CAMERAS}")
        if not isinstance(action_chunk_size, int) or isinstance(action_chunk_size, bool) or action_chunk_size <= 0:
            raise ValueError("action_chunk_size must be a positive integer")
        if max_encoded_image_bytes <= 0 or max_decoded_pixels <= 0:
            raise ValueError("image safety limits must be positive")
        if not isinstance(max_episode_steps, int) or isinstance(max_episode_steps, bool) or max_episode_steps < 2:
            raise ValueError("max_episode_steps must be an integer >= 2")
        self.action_chunk_size = action_chunk_size
        self.max_episode_steps = max_episode_steps
        self.max_encoded_image_bytes = int(max_encoded_image_bytes)
        self.max_decoded_pixels = int(max_decoded_pixels)

    def iter_episode_paths(self, *, max_episodes_per_task: int | None = None) -> Iterator[Path]:
        if max_episodes_per_task is not None and (
            not isinstance(max_episodes_per_task, int)
            or isinstance(max_episodes_per_task, bool)
            or max_episodes_per_task <= 0
        ):
            raise ValueError("max_episodes_per_task must be a positive integer or None")
        for task_directory in sorted(path for path in self.dataset_root.iterdir() if path.is_dir()):
            episode_paths: list[Path] = []
            for embodiment_directory in sorted(path for path in task_directory.iterdir() if path.is_dir()):
                data_directory = embodiment_directory / "data"
                if data_directory.is_dir():
                    episode_paths.extend(data_directory.glob("episode*.hdf5"))
            episode_paths.sort(key=lambda path: (_episode_index(path), str(path)))
            if max_episodes_per_task is not None:
                episode_paths = episode_paths[:max_episodes_per_task]
            yield from episode_paths

    def inspect_episode(self, path: str | Path) -> RobotTwinEpisodeMetadata:
        episode_path = Path(path)
        task, embodiment = self._relative_identity(episode_path)
        h5py = _require_h5py()
        with h5py.File(episode_path, "r") as handle:
            action = self._required_dataset(handle, "joint_action/vector")
            if action.ndim != 2 or action.shape[1] != ROBOTWIN_ACTION_DIM or action.shape[0] < 2:
                raise ValueError(f"{episode_path}: joint_action/vector must have shape [T>=2,14]")
            if not np.issubdtype(action.dtype, np.floating):
                raise TypeError(f"{episode_path}: joint_action/vector must be floating point")
            num_steps = int(action.shape[0])
            if num_steps > self.max_episode_steps:
                raise ValueError(f"{episode_path}: episode exceeds max_episode_steps={self.max_episode_steps}")
            for start in range(0, num_steps, 4096):
                action_values = np.asarray(action[start : start + 4096], dtype=np.float32)
                if not np.isfinite(action_values).all():
                    raise ValueError(f"{episode_path}: joint_action/vector contains NaN/Inf")

            required_shapes = {
                "joint_action/left_arm": (num_steps, 6),
                "joint_action/right_arm": (num_steps, 6),
                "joint_action/left_gripper": (num_steps,),
                "joint_action/right_gripper": (num_steps,),
                "endpose/left_endpose": (num_steps, 7),
                "endpose/right_endpose": (num_steps, 7),
                "endpose/left_gripper": (num_steps,),
                "endpose/right_gripper": (num_steps,),
            }
            for dataset_name, expected_shape in required_shapes.items():
                dataset = self._required_dataset(handle, dataset_name)
                if dataset.shape != expected_shape:
                    raise ValueError(f"{episode_path}: {dataset_name} shape {dataset.shape} != {expected_shape}")

            max_encoded_bytes = 0
            for camera in self.cameras:
                rgb = self._required_dataset(handle, f"observation/{camera}/rgb")
                if rgb.ndim != 1 or rgb.shape[0] != num_steps or rgb.dtype.kind not in ("S", "O"):
                    raise ValueError(f"{episode_path}: {camera}/rgb must be encoded byte frames [T]")
                for frame_index in (0, num_steps - 1):
                    encoded = self._encoded_frame(rgb[frame_index], episode_path, camera)
                    max_encoded_bytes = max(max_encoded_bytes, len(encoded))

        return RobotTwinEpisodeMetadata(
            path=episode_path,
            task=task,
            embodiment=embodiment,
            episode_index=_episode_index(episode_path),
            num_steps=num_steps,
            action_dim=ROBOTWIN_ACTION_DIM,
            proprio_dim=ROBOTWIN_PROPRIO_DIM,
            cameras=self.cameras,
            max_checked_encoded_image_bytes=max_encoded_bytes,
        )

    def load_sample(
        self,
        path: str | Path,
        step_index: int,
        *,
        decode_images: bool = True,
        instruction_index: int = 0,
    ) -> RobotTwinSample:
        metadata = self.inspect_episode(path)
        if not isinstance(step_index, int) or isinstance(step_index, bool) or not 0 <= step_index < metadata.num_steps - 1:
            raise IndexError("step_index must leave at least one next-step action")
        if not isinstance(instruction_index, int) or isinstance(instruction_index, bool) or instruction_index < 0:
            raise ValueError("instruction_index must be a non-negative integer")
        h5py = _require_h5py()
        images: dict[str, np.ndarray] = {}
        with h5py.File(metadata.path, "r") as handle:
            action = handle["joint_action/vector"]
            proprio = np.asarray(action[step_index], dtype=np.float32)
            stop = min(metadata.num_steps, step_index + 1 + self.action_chunk_size)
            valid_actions = np.asarray(action[step_index + 1 : stop], dtype=np.float32)
            action_valid_mask = np.zeros(self.action_chunk_size, dtype=np.bool_)
            action_valid_mask[: valid_actions.shape[0]] = True
            action_chunk = np.empty((self.action_chunk_size, ROBOTWIN_ACTION_DIM), dtype=np.float32)
            action_chunk[: valid_actions.shape[0]] = valid_actions
            action_chunk[valid_actions.shape[0] :] = valid_actions[-1]
            if decode_images:
                for camera in self.cameras:
                    rgb = handle[f"observation/{camera}/rgb"]
                    encoded = self._encoded_frame(rgb[step_index], metadata.path, camera)
                    images[camera] = self._decode_image(encoded, metadata.path, camera)

        relative_episode = metadata.path.relative_to(self.dataset_root).as_posix()
        return RobotTwinSample(
            sample_id=stable_sample_id("robotwin2-native-joint-v1", relative_episode, step_index),
            task=metadata.task,
            embodiment=metadata.embodiment,
            episode_index=metadata.episode_index,
            step_index=step_index,
            instruction=self._load_instruction(metadata.path, instruction_index),
            proprio=proprio,
            action_chunk=action_chunk,
            action_valid_mask=action_valid_mask,
            images=images,
        )

    def audit(self, *, max_episodes_per_task: int | None = None) -> RobotTwinAuditSummary:
        metadata = [
            self.inspect_episode(path)
            for path in self.iter_episode_paths(max_episodes_per_task=max_episodes_per_task)
        ]
        if not metadata:
            raise ValueError(f"no RoboTwin HDF5 episodes found under {self.dataset_root}")
        return RobotTwinAuditSummary(
            dataset_root=str(self.dataset_root.resolve()),
            tasks=tuple(sorted({item.task for item in metadata})),
            episodes_checked=len(metadata),
            min_steps=min(item.num_steps for item in metadata),
            max_steps=max(item.num_steps for item in metadata),
            action_dim=ROBOTWIN_ACTION_DIM,
            proprio_dim=ROBOTWIN_PROPRIO_DIM,
            cameras=self.cameras,
            max_checked_encoded_image_bytes=max(item.max_checked_encoded_image_bytes for item in metadata),
        )

    def _relative_identity(self, episode_path: Path) -> tuple[str, str]:
        if not episode_path.is_file():
            raise FileNotFoundError(episode_path)
        try:
            relative = episode_path.resolve().relative_to(self.dataset_root.resolve())
        except ValueError as error:
            raise ValueError(f"episode must be inside dataset_root: {episode_path}") from error
        if len(relative.parts) != 4 or relative.parts[2] != "data":
            raise ValueError("expected RoboTwin path <task>/<embodiment>/data/episodeN.hdf5")
        _episode_index(episode_path)
        return relative.parts[0], relative.parts[1]

    @staticmethod
    def _required_dataset(handle: Any, name: str) -> Any:
        if name not in handle:
            raise ValueError(f"missing required RoboTwin dataset: {name}")
        dataset = handle[name]
        if not hasattr(dataset, "shape") or not hasattr(dataset, "dtype"):
            raise ValueError(f"RoboTwin path is not a dataset: {name}")
        return dataset

    def _encoded_frame(self, value: Any, episode_path: Path, camera: str) -> bytes:
        encoded = bytes(value).rstrip(b"\0")
        if not encoded:
            raise ValueError(f"{episode_path}: empty encoded frame for {camera}")
        if len(encoded) > self.max_encoded_image_bytes:
            raise ValueError(f"{episode_path}: encoded frame exceeds byte safety limit for {camera}")
        if not (encoded.startswith(b"\xff\xd8\xff") or encoded.startswith(b"\x89PNG\r\n\x1a\n")):
            raise ValueError(f"{episode_path}: unsupported image encoding for {camera}")
        return encoded

    def _decode_image(self, encoded: bytes, episode_path: Path, camera: str) -> np.ndarray:
        try:
            from PIL import Image
        except ImportError as error:
            raise RuntimeError("RoboTwin image decoding requires Pillow") from error
        with Image.open(io.BytesIO(encoded)) as image:
            width, height = image.size
            if width <= 0 or height <= 0 or width * height > self.max_decoded_pixels:
                raise ValueError(f"{episode_path}: decoded image exceeds pixel safety limit for {camera}")
            decoded = np.asarray(image.convert("RGB"), dtype=np.uint8).copy()
        return decoded

    def _load_instruction(self, episode_path: Path, instruction_index: int) -> str:
        instruction_path = episode_path.parent.parent / "instructions" / f"episode{_episode_index(episode_path)}.json"
        if not instruction_path.is_file():
            raise FileNotFoundError(instruction_path)
        payload = json.loads(instruction_path.read_text(encoding="utf-8"))
        seen = payload.get("seen") if isinstance(payload, dict) else None
        if not isinstance(seen, list) or not seen or any(not isinstance(item, str) or not item.strip() for item in seen):
            raise ValueError(f"{instruction_path}: expected a non-empty string list at 'seen'")
        if instruction_index >= len(seen):
            raise IndexError("instruction_index exceeds available deterministic instructions")
        return seen[instruction_index]


__all__ = [
    "ROBOTWIN_ACTION_DIM",
    "ROBOTWIN_ACTION_REPRESENTATION",
    "ROBOTWIN_CAMERAS",
    "ROBOTWIN_PROPRIO_DIM",
    "RobotTwinAuditSummary",
    "RobotTwinEpisodeMetadata",
    "RobotTwinHDF5Adapter",
    "RobotTwinSample",
    "reject_libero_openvla_oft_for_robotwin",
    "validate_robotwin_native_contract",
]

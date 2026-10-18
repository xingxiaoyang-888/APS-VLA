"""Bounded TensorFlow-Example decoder for LIBERO RLDS episode records.

The OpenVLA LIBERO shards store one episode per TFRecord payload.  Although
the keys use RLDS ``steps/...`` names, each payload is a flat
``tf.train.Example``: timestep values are concatenated in ``Features`` rather
than nested in ``SequenceExample.feature_lists``.  This module defines the
minimal protobuf schema locally so the inference environment does not need
TensorFlow or TFDS.

Images remain compressed JPEG bytes on CPU.  Numeric values are materialized
once as bounded, read-only NumPy arrays; no image decoding, torch import, CUDA
allocation, or model loading occurs here.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache
import hashlib
import math
from pathlib import Path
import struct
from typing import Any, Iterator, Mapping, Sequence

import numpy as np
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
from google.protobuf.message import DecodeError

from .libero import LIBERO_ACTION_DIM, LIBERO_PROPRIO_DIM
from .tfrecord import iter_tfrecord_records
from .libero import LiberoEpisodeRef

LIBERO_JOINT_STATE_DIM = 7
DEFAULT_MAX_EPISODE_STEPS = 10_000

_SCALAR_STEP_FIELDS = (
    "steps/reward",
    "steps/discount",
    "steps/is_first",
    "steps/is_last",
    "steps/is_terminal",
    "steps/language_instruction",
    "steps/observation/image",
    "steps/observation/wrist_image",
)
_VECTOR_STEP_FIELDS = {
    "steps/action": LIBERO_ACTION_DIM,
    "steps/observation/state": LIBERO_PROPRIO_DIM,
    "steps/observation/joint_state": LIBERO_JOINT_STATE_DIM,
}


def _field(message, name: str, number: int, field_type: int, *, label: int = 1, type_name: str = "") -> None:
    item = message.field.add(name=name, number=number, type=field_type, label=label)
    if type_name:
        item.type_name = type_name


@lru_cache(maxsize=1)
def _example_class():
    """Build the small subset of TensorFlow's Example proto that we consume."""

    file_proto = descriptor_pb2.FileDescriptorProto(
        name="cti_vla_tf_example.proto",
        package="cti_vla.tf",
        syntax="proto3",
    )
    bytes_list = file_proto.message_type.add(name="BytesList")
    _field(bytes_list, "value", 1, descriptor_pb2.FieldDescriptorProto.TYPE_BYTES, label=3)
    float_list = file_proto.message_type.add(name="FloatList")
    _field(float_list, "value", 1, descriptor_pb2.FieldDescriptorProto.TYPE_FLOAT, label=3)
    int64_list = file_proto.message_type.add(name="Int64List")
    _field(int64_list, "value", 1, descriptor_pb2.FieldDescriptorProto.TYPE_INT64, label=3)

    feature = file_proto.message_type.add(name="Feature")
    feature.oneof_decl.add(name="kind")
    _field(feature, "bytes_list", 1, descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE, type_name=".cti_vla.tf.BytesList")
    _field(feature, "float_list", 2, descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE, type_name=".cti_vla.tf.FloatList")
    _field(feature, "int64_list", 3, descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE, type_name=".cti_vla.tf.Int64List")
    for item in feature.field:
        item.oneof_index = 0

    features = file_proto.message_type.add(name="Features")
    feature_entry = features.nested_type.add(name="FeatureEntry", options=descriptor_pb2.MessageOptions(map_entry=True))
    _field(feature_entry, "key", 1, descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
    _field(feature_entry, "value", 2, descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE, type_name=".cti_vla.tf.Feature")
    _field(features, "feature", 1, descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE, label=3, type_name=".cti_vla.tf.Features.FeatureEntry")

    example = file_proto.message_type.add(name="Example")
    _field(example, "features", 1, descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE, type_name=".cti_vla.tf.Features")
    pool = descriptor_pool.DescriptorPool()
    descriptor = pool.Add(file_proto).message_types_by_name["Example"]
    return message_factory.GetMessageClass(descriptor)


def _feature_values(feature: Any, key: str) -> tuple[Any, ...]:
    kind = feature.WhichOneof("kind")
    expected = None
    if key in _VECTOR_STEP_FIELDS or key in ("steps/reward", "steps/discount"):
        expected = "float_list"
    elif key in ("steps/is_first", "steps/is_last", "steps/is_terminal"):
        expected = "int64_list"
    elif key in ("episode_metadata/file_path", "steps/language_instruction", "steps/observation/image", "steps/observation/wrist_image"):
        expected = "bytes_list"
    if expected is not None and kind != expected:
        raise ValueError(f"feature {key!r} must use {expected}, got {kind}")
    if kind == "bytes_list":
        return tuple(feature.bytes_list.value)
    if kind == "float_list":
        return tuple(feature.float_list.value)
    if kind == "int64_list":
        return tuple(feature.int64_list.value)
    raise ValueError(f"feature {key!r} has no supported value list")


def _require_fields(features: Mapping[str, tuple[Any, ...]]) -> None:
    missing = sorted((set(_SCALAR_STEP_FIELDS) | set(_VECTOR_STEP_FIELDS) | {"episode_metadata/file_path"}) - features.keys())
    if missing:
        raise ValueError(f"LIBERO Example is missing required fields: {missing}")


def _episode_content_id(message: Any) -> str:
    """Identify a trajectory independently of shard and source machine path.

    Upstream file_path only identifies a task HDF5 (many demonstrations), and
    contains no demonstration ID. Hash the ordered values of all required step
    fields. Length-prefixed keys and canonical Feature encoding are unambiguous;
    map order and omitted/redundant protobuf packing do not change the result.
    """
    digest = hashlib.sha256(b"cti-vla:libero-episode-content:v1\x00")
    for key in sorted(set(_SCALAR_STEP_FIELDS) | set(_VECTOR_STEP_FIELDS)):
        encoded_key = key.encode("utf-8")
        feature = message.features.feature[key].SerializeToString(deterministic=True)
        digest.update(struct.pack("<Q", len(encoded_key)))
        digest.update(encoded_key)
        digest.update(struct.pack("<Q", len(feature)))
        digest.update(feature)
    return "libero-episode-sha256:" + digest.hexdigest()


def _read_episode_id(values: Sequence[Any]) -> str:
    if len(values) != 1 or not isinstance(values[0], bytes):
        raise ValueError("episode_metadata/file_path must contain exactly one bytes value")
    episode_id = values[0].decode("utf-8", errors="strict")
    if not episode_id.strip():
        raise ValueError("episode_metadata/file_path must be non-empty")
    return episode_id


def _finite_array(values: Sequence[Any], *, shape: tuple[int, ...], key: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float32)
    if array.size != math.prod(shape):
        raise ValueError(f"{key} has {array.size} values; expected {math.prod(shape)} for shape {shape}")
    array = np.ascontiguousarray(array.reshape(shape))
    if not np.isfinite(array).all():
        raise ValueError(f"{key} contains NaN or Inf")
    array.setflags(write=False)
    return array


def _flag_array(values: Sequence[Any], *, steps: int, key: str) -> np.ndarray:
    if len(values) != steps or any(value not in (0, 1) for value in values):
        raise ValueError(f"{key} must contain exactly {steps} binary values")
    array = np.asarray(values, dtype=np.bool_)
    array.setflags(write=False)
    return array


def _jpeg_tuple(values: Sequence[Any], *, steps: int, key: str) -> tuple[bytes, ...]:
    if len(values) != steps:
        raise ValueError(f"{key} has {len(values)} frames; expected {steps}")
    output = tuple(values)
    if any(not isinstance(value, bytes) or len(value) < 4 or not value.startswith(b"\xff\xd8") or not value.endswith(b"\xff\xd9") for value in output):
        raise ValueError(f"{key} contains a non-JPEG frame")
    return output


def _instructions(values: Sequence[Any], *, steps: int) -> tuple[str, ...]:
    if len(values) != steps or any(not isinstance(value, bytes) for value in values):
        raise ValueError(f"steps/language_instruction must contain exactly {steps} bytes values")
    output = tuple(value.decode("utf-8", errors="strict") for value in values)
    if any(not value.strip() for value in output):
        raise ValueError("steps/language_instruction contains an empty instruction")
    return output


@dataclass(frozen=True, eq=False)
class LiberoEpisode:
    """One validated CPU episode. Actions/proprio are RAW dataset values.

    Checkpoint-specific action/proprio normalization and image preprocessing
    must be applied by the model adapter, not silently assumed here.
    """

    episode_id: str
    episode_file_path: str
    actions: np.ndarray
    proprio: np.ndarray
    joint_state: np.ndarray
    images: tuple[bytes, ...]
    wrist_images: tuple[bytes, ...]
    instructions: tuple[str, ...]
    rewards: np.ndarray
    discounts: np.ndarray
    is_first: np.ndarray
    is_last: np.ndarray
    is_terminal: np.ndarray
    source_shard: str = ""
    record_index: int = -1

    @property
    def num_steps(self) -> int:
        return int(self.actions.shape[0])


def decode_libero_example(payload: bytes, *, max_episode_steps: int = DEFAULT_MAX_EPISODE_STEPS,
                          max_payload_bytes: int = 512 * 1024 * 1024) -> LiberoEpisode:
    """Decode and validate one flat LIBERO episode Example payload."""

    if not isinstance(payload, bytes) or not payload:
        raise ValueError("Example payload must be non-empty bytes")
    if type(max_payload_bytes) is not int or max_payload_bytes <= 0 or len(payload) > max_payload_bytes:
        raise ValueError("Example payload exceeds max_payload_bytes or invalid bound")
    if not isinstance(max_episode_steps, int) or isinstance(max_episode_steps, bool) or max_episode_steps <= 0:
        raise ValueError("max_episode_steps must be a positive integer")
    message = _example_class()()
    try:
        message.ParseFromString(payload)
    except DecodeError as error:
        raise ValueError("invalid flat tf.train.Example protobuf payload") from error
    features = {key: _feature_values(value, key) for key, value in message.features.feature.items()}
    _require_fields(features)

    steps = len(features["steps/observation/image"])
    if not 0 < steps <= max_episode_steps:
        raise ValueError(f"episode step count must be in [1, {max_episode_steps}], got {steps}")
    for key in _SCALAR_STEP_FIELDS:
        if len(features[key]) != steps:
            raise ValueError(f"{key} has {len(features[key])} values; expected {steps}")

    actions = _finite_array(features["steps/action"], shape=(steps, LIBERO_ACTION_DIM), key="steps/action")
    proprio = _finite_array(features["steps/observation/state"], shape=(steps, LIBERO_PROPRIO_DIM), key="steps/observation/state")
    joint_state = _finite_array(features["steps/observation/joint_state"], shape=(steps, LIBERO_JOINT_STATE_DIM), key="steps/observation/joint_state")
    rewards = _finite_array(features["steps/reward"], shape=(steps,), key="steps/reward")
    discounts = _finite_array(features["steps/discount"], shape=(steps,), key="steps/discount")
    is_first = _flag_array(features["steps/is_first"], steps=steps, key="steps/is_first")
    is_last = _flag_array(features["steps/is_last"], steps=steps, key="steps/is_last")
    is_terminal = _flag_array(features["steps/is_terminal"], steps=steps, key="steps/is_terminal")
    if not is_first[0] or is_first[1:].any():
        raise ValueError("steps/is_first must be true only at timestep 0")
    if not is_last[-1] or is_last[:-1].any():
        raise ValueError("steps/is_last must be true only at the final timestep")
    if is_terminal[:-1].any():
        raise ValueError("steps/is_terminal cannot be true before the final timestep")

    episode_file_path = _read_episode_id(features["episode_metadata/file_path"])
    return LiberoEpisode(
        episode_id=_episode_content_id(message),
        episode_file_path=episode_file_path,
        actions=actions,
        proprio=proprio,
        joint_state=joint_state,
        images=_jpeg_tuple(features["steps/observation/image"], steps=steps, key="steps/observation/image"),
        wrist_images=_jpeg_tuple(features["steps/observation/wrist_image"], steps=steps, key="steps/observation/wrist_image"),
        instructions=_instructions(features["steps/language_instruction"], steps=steps),
        rewards=rewards,
        discounts=discounts,
        is_first=is_first,
        is_last=is_last,
        is_terminal=is_terminal,
    )


def iter_libero_examples(
    path: str | Path,
    *,
    max_record_bytes: int = 512 * 1024 * 1024,
    max_episode_steps: int = DEFAULT_MAX_EPISODE_STEPS,
) -> Iterator[LiberoEpisode]:
    """Stream validated episodes from one TFRecord shard with CRC checks."""

    input_path = Path(path)
    for record_index, payload in iter_tfrecord_records(input_path, max_record_bytes=max_record_bytes):
        try:
            episode = decode_libero_example(payload, max_episode_steps=max_episode_steps,
                                            max_payload_bytes=max_record_bytes)
        except ValueError as error:
            raise ValueError(f"invalid LIBERO Example at record {record_index}: {error}") from error
        # Storage locators are NOT episode identities; content IDs survive
        # resharding and task-level HDF5 paths need not be unique per episode.
        yield replace(episode, source_shard=input_path.name, record_index=record_index)


def discover_episodes(paths: Sequence[str | Path]) -> tuple[LiberoEpisodeRef, ...]:
    """Validate every episode and return small metadata suitable for splitting.

    Instruction text identifies tasks; all steps must agree. Non-constant
    instructions require an explicit dataset adapter instead of silent grouping.
    Images stay compressed and are released after each record.
    """
    paths = sorted(Path(path) for path in paths)
    if not paths or len({path.name for path in paths}) != len(paths):
        raise ValueError("shards must be non-empty with unique basenames")
    output = []
    seen = set()
    for path in paths:
        for episode in iter_libero_examples(path):
            if episode.episode_id in seen:
                raise ValueError(f"duplicate original episode_id across records: {episode.episode_id!r}")
            seen.add(episode.episode_id)
            if len(set(episode.instructions)) != 1:
                raise ValueError(f"episode {episode.episode_id!r} has changing instructions")
            output.append(LiberoEpisodeRef(episode.episode_id, episode.num_steps,
                                          episode.instructions[0], episode.source_shard,
                                          episode.record_index, episode.episode_file_path))
    return tuple(sorted(output, key=lambda item: item.episode_id))


__all__ = [
    "DEFAULT_MAX_EPISODE_STEPS",
    "LIBERO_JOINT_STATE_DIM",
    "LiberoEpisode",
    "decode_libero_example",
    "discover_episodes",
    "iter_libero_examples",
]

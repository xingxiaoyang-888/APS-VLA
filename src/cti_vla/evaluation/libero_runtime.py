"""Versioned LIBERO observation/action adapters and resumable development trials.

Image operations match moojink/openvla-oft commit
e4287e94541f459edc4feabc4e181f537cd569a8. TensorFlow is CPU-only and lazily
imported for its exact JPEG/Lanczos/crop semantics; no approximation with PIL.
"""
from __future__ import annotations

import ast
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any, Callable, Mapping, Optional, Tuple, Union

import numpy as np
from PIL import Image

from cti_vla.models.openvla_oft_inputs import format_prompt


OFT_COMMIT = "e4287e94541f459edc4feabc4e181f537cd569a8"
INPUTS_VERSION = "libero-oft-eval-rotate180-jpeg-lanczos3-crop09-boundsq99-v1"
LIBERO_EVAL_INPUT_VERSION = INPUTS_VERSION
ACTION_VERSION = "libero-oft-boundsq99-gripper-sign-invert-chunk8-v1"
METHODS = ("official_dense", "dense", "uniform128")
IMAGE_SIZE = 224
DUMMY_ACTION = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0)


@lru_cache(maxsize=1)
def _tensorflow():
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    import tensorflow as tf
    # Never allow image preprocessing to reserve the model's GPU memory.
    tf.config.set_visible_devices([], "GPU")
    if tf.config.get_visible_devices("GPU"):
        raise RuntimeError("TensorFlow image processing must run on CPU")
    return tf


def _rgb(image: Any) -> np.ndarray:
    value = np.asarray(image)
    if value.ndim != 3 or value.shape[-1] != 3 or value.dtype != np.uint8:
        raise ValueError("camera image must be uint8 [H, W, 3]")
    return value


def resize_image_for_policy(image: np.ndarray) -> np.ndarray:
    """Exact official JPEG round trip followed by antialiased Lanczos3."""
    tf = _tensorflow()
    image = tf.image.encode_jpeg(_rgb(image))
    image = tf.io.decode_image(image, expand_animations=False, dtype=tf.uint8)
    image = tf.image.resize(image, (IMAGE_SIZE, IMAGE_SIZE), method="lanczos3", antialias=True)
    return tf.cast(tf.clip_by_value(tf.round(image), 0, 255), tf.uint8).numpy()


def center_crop_image(image: np.ndarray) -> Image.Image:
    """Official 0.9-area crop: side length sqrt(0.9), bilinear resize to 224."""
    tf = _tensorflow()
    image = tf.convert_to_tensor(_rgb(image))
    original_dtype = image.dtype
    image = tf.image.convert_image_dtype(image, tf.float32)
    side = tf.reshape(tf.clip_by_value(tf.sqrt(0.9), 0, 1), (1,))
    offset = (1 - side) / 2
    boxes = tf.stack((offset, offset, offset + side, offset + side), axis=1)
    image = tf.image.crop_and_resize(tf.expand_dims(image, 0), boxes, tf.range(1), (IMAGE_SIZE, IMAGE_SIZE))[0]
    image = tf.image.convert_image_dtype(tf.clip_by_value(image, 0, 1), original_dtype, saturate=True)
    return Image.fromarray(image.numpy()).convert("RGB")


def process_camera(image: np.ndarray, *, already_rotated: bool = False) -> Image.Image:
    value = _rgb(image)
    if not already_rotated:
        value = value[::-1, ::-1]
    # Official prepare_observation resizes once even if an image already is 224.
    return center_crop_image(resize_image_for_policy(np.ascontiguousarray(value)))


def quaternion_to_axis_angle(quaternion: np.ndarray) -> np.ndarray:
    """Official XYZW conversion, without mutating the simulator observation."""
    quat = np.asarray(quaternion).copy()
    if quat.shape != (4,) or not np.isfinite(quat).all():
        raise ValueError("eef quaternion must be finite XYZW [4]")
    quat[3] = np.clip(quat[3], -1.0, 1.0)
    denominator = np.sqrt(1.0 - quat[3] * quat[3])
    if math.isclose(float(denominator), 0.0):
        return np.zeros(3)
    return quat[:3] * 2.0 * math.acos(float(quat[3])) / denominator


def raw_proprio_from_observation(observation: Mapping[str, Any]) -> np.ndarray:
    position = np.asarray(observation["robot0_eef_pos"])
    gripper = np.asarray(observation["robot0_gripper_qpos"])
    if position.shape != (3,) or gripper.shape != (2,):
        raise ValueError("LIBERO proprio requires eef position [3] and gripper qpos [2]")
    state = np.concatenate((position, quaternion_to_axis_angle(observation["robot0_eef_quat"]), gripper))
    if not np.isfinite(state).all():
        raise ValueError("proprio must be finite")
    return state


def postprocess_actions(physical_actions: np.ndarray) -> np.ndarray:
    """Physical actions -> LIBERO controls; never apply this to teacher labels."""
    actions = np.asarray(physical_actions).copy()
    if actions.ndim not in (1, 2) or actions.shape[-1] != 7 or not np.isfinite(actions).all():
        raise ValueError("physical actions must be finite [..., 7]")
    actions[..., -1] = -np.sign(2.0 * actions[..., -1] - 1.0)
    return actions


def normalize_eval_proprio(raw, stats) -> np.ndarray:
    """Exact official NumPy dtype promotion, bounds mask and clipping."""
    raw = np.asarray(raw)
    low, high = np.array(stats["q01"]), np.array(stats["q99"])
    mask = np.asarray(stats.get("mask", np.ones_like(low, dtype=bool)), dtype=bool)
    if any(value.shape != (8,) for value in (raw, low, high, mask)):
        raise ValueError("proprio, bounds and mask must have shape [8]")
    if not all(np.isfinite(value).all() for value in (raw, low, high)) or np.any(high < low):
        raise ValueError("invalid proprio normalization statistics or observation")
    return np.clip(np.where(mask, 2 * (raw - low) / (high - low + 1e-8) - 1, raw), -1.0, 1.0)


def uniform128_indices() -> np.ndarray:
    """8x8 grid in each original 16x16 patch grid, main camera then wrist."""
    axis = np.arange(0, 16, 2)
    local = (axis[:, None] * 16 + axis[None, :]).reshape(-1)
    return np.concatenate((local, local + 256)).astype(np.int64)


def _prepare_processed_inputs(images, raw_proprio, instruction, processor, norm_stats, *, device, dtype):
    import torch
    prompt = format_prompt(instruction)
    primary, wrist = (processor(prompt, image, return_tensors="pt") for image in images)
    if not torch.equal(primary["input_ids"], wrist["input_ids"]) or not torch.equal(primary["attention_mask"], wrist["attention_mask"]):
        raise RuntimeError("two cameras produced different language tokens/masks")
    ids = primary["input_ids"].to(device=device)
    attention = primary["attention_mask"].to(device=device)
    if ids.ndim != 2 or ids.shape[0] != 1 or attention.shape != ids.shape or not bool((attention == 1).all()):
        raise RuntimeError("rollout requires one unpadded language prompt")
    pixels = torch.cat((primary["pixel_values"], wrist["pixel_values"]), dim=1).to(device=device, dtype=dtype)
    if pixels.shape != (1, 12, IMAGE_SIZE, IMAGE_SIZE):
        raise RuntimeError(f"unexpected dual-view pixel tensor: {tuple(pixels.shape)}")
    normalized = normalize_eval_proprio(raw_proprio, norm_stats)
    return {
        "pixel_values": pixels, "input_ids": ids, "attention_mask": attention,
        # Native predict_action constructs torch.Tensor(numpy), hence float32
        # before converting to the model dtype. Match this conversion exactly.
        "normalized_proprio": torch.tensor(normalized, dtype=torch.float32).unsqueeze(0).to(device=device, dtype=dtype),
        "normalized_proprio_numpy": normalized, "prompt": prompt, "inputs_version": INPUTS_VERSION,
        "image_sizes": [list(image.size) for image in images],
    }


def prepare_observation_inputs(observation, instruction, processor, norm_stats, *, device, dtype):
    images = [process_camera(observation[key]) for key in ("agentview_image", "robot0_eye_in_hand_image")]
    return _prepare_processed_inputs(images, raw_proprio_from_observation(observation), instruction, processor, norm_stats, device=device, dtype=dtype)


def prepare_rlds_eval_inputs(episode, step_index, processor, norm_stats, *, device, dtype):
    """RLDS images already have the camera rotation; apply no second rotation."""
    from io import BytesIO
    if type(step_index) is not int or not 0 <= step_index < episode.num_steps:
        raise ValueError("step_index is outside the episode")
    images = []
    for encoded in (episode.images[step_index], episode.wrist_images[step_index]):
        with Image.open(BytesIO(encoded)) as image:
            images.append(process_camera(np.asarray(image.convert("RGB")), already_rotated=True))
    return _prepare_processed_inputs(images, episode.proprio[step_index], episode.instructions[step_index], processor, norm_stats, device=device, dtype=dtype)


_REFERENCE_FILES = {
    "experiments/robot/openvla_utils.py": ("eed754d7c5f9821aae2fe0531dbe01df8c11df0d5c79b4aeeb9bb4452124bdf5", ("resize_image_for_policy", "crop_and_resize", "center_crop_image", "normalize_proprio")),
    "experiments/robot/libero/libero_utils.py": ("489c16dc8220845b2936ddb81aafd7469061d2009b0edddb2f85703bc51a204f", ("get_libero_image", "get_libero_wrist_image", "quat2axisangle")),
    "experiments/robot/robot_utils.py": ("93541b01edd4de49fcc9a1d9249e11fea008b9502fd755096503aaec93773da0", ("normalize_gripper_action", "invert_gripper_action")),
}


def load_official_reference_functions(source_root: str | Path) -> dict[str, Any]:
    """Load only audited pure functions, avoiding upstream package import effects."""
    from cti_vla.models.openvla_oft_runtime_compat import NormalizationType
    namespace = {"np": np, "tf": _tensorflow(), "Image": Image, "math": math,
                 "Union": Union, "Tuple": Tuple, "Dict": dict, "Any": Any,
                 "OPENVLA_IMAGE_SIZE": IMAGE_SIZE, "NormalizationType": NormalizationType,
                 "ACTION_PROPRIO_NORMALIZATION_TYPE": NormalizationType.BOUNDS_Q99}
    for relative, (expected, names) in _REFERENCE_FILES.items():
        path = Path(source_root) / relative
        source = path.read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(source).hexdigest() != expected:
            raise ValueError(f"official source hash mismatch: {relative}; expected commit {OFT_COMMIT}")
        module = ast.parse(source.decode("utf-8"), filename=str(path))
        selected = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name in names]
        if {node.name for node in selected} != set(names):
            raise ValueError("official reference function set changed")
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


def verify_observation_preprocessing(observation, norm_stats, reference) -> dict[str, Any]:
    """CPU pixel/proprio verification against unmodified pinned source functions."""
    for key, function in (("agentview_image", "get_libero_image"), ("robot0_eye_in_hand_image", "get_libero_wrist_image")):
        expected = reference["center_crop_image"](reference["resize_image_for_policy"](reference[function](observation), IMAGE_SIZE))
        if not np.array_equal(np.asarray(process_camera(observation[key])), np.asarray(expected)):
            raise RuntimeError(f"official image preprocessing differs for {key}")
    expected_raw = np.concatenate((observation["robot0_eef_pos"], reference["quat2axisangle"](np.asarray(observation["robot0_eef_quat"]).copy()), observation["robot0_gripper_qpos"]))
    actual_raw = raw_proprio_from_observation(observation)
    if not np.array_equal(actual_raw, expected_raw):
        raise RuntimeError("official proprio construction differs")
    expected_normalized = reference["normalize_proprio"](expected_raw, norm_stats)
    actual_normalized = normalize_eval_proprio(actual_raw, norm_stats)
    max_error = float(np.max(np.abs(actual_normalized - expected_normalized)))
    if max_error != 0:
        raise RuntimeError(f"proprio normalization differs from official source: {max_error}")
    return {"images_equal": True, "raw_proprio_equal": True, "normalized_proprio_max_abs_error": max_error}


@dataclass(frozen=True)
class PolicyChunk:
    normalized_actions: np.ndarray
    environment_actions: np.ndarray
    metadata: Mapping[str, Any]

    def __post_init__(self):
        for name in ("normalized_actions", "environment_actions"):
            value = np.asarray(getattr(self, name))
            if value.shape != (8, 7) or not np.isfinite(value).all():
                raise ValueError(f"{name} must be finite [8, 7]")
            object.__setattr__(self, name, value.copy())


class OpenVLARolloutPolicy:
    """Native dense, migrated dense and fixed uniform128 on one frozen model."""
    def __init__(self, components, processor, *, stats_key: str, method: str, reference=None):
        if method not in METHODS:
            raise ValueError(f"unsupported G0 method: {method}")
        import torch
        from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
        self.components, self.processor = components, processor
        self.stats_key, self.method, self.reference = stats_key, method, reference
        self.device = next(components.vla.parameters()).device
        self.dtype = next(components.vla.parameters()).dtype
        self.token_policy = OpenVLAOFTTokenPolicy(components.vla, components.action_head, components.proprio_projector, num_patches_full=512)
        self.indices = torch.from_numpy(uniform128_indices()).unsqueeze(0).to(self.device)
        self.checked = False

    def reset(self):
        self.checked = False

    def __call__(self, observation, instruction) -> PolicyChunk:
        import torch
        vla = self.components.vla
        stats = vla.norm_stats[self.stats_key]["proprio"]
        verification = None
        if self.reference is not None and not self.checked:
            verification = verify_observation_preprocessing(observation, stats, self.reference)
            self.checked = True
        inputs = prepare_observation_inputs(observation, instruction, self.processor, stats, device=self.device, dtype=self.dtype)
        with torch.inference_mode():
            if self.method == "official_dense":
                physical, hidden = vla.predict_action(
                    input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"], pixel_values=inputs["pixel_values"],
                    proprio=inputs["normalized_proprio_numpy"], proprio_projector=self.components.proprio_projector,
                    action_head=self.components.action_head, unnorm_key=self.stats_key, use_film=False,
                )
                normalized = self.components.action_head.predict_action(hidden).float().cpu().numpy()[0]
                physical = np.asarray(physical)
                # Native public API returns physical actions; verify capture of
                # normalized output from its returned action hidden states.
                expected = vla._unnormalize_actions(normalized, self.stats_key)
                if not np.array_equal(physical, expected):
                    raise RuntimeError("native action-head recapture changed physical actions")
            else:
                projected = vla._process_vision_features(inputs["pixel_values"], None, False)
                normalized = self.token_policy.forward_from_full_tokens(
                    projected, inputs["normalized_proprio"], input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"],
                    retained_indices=self.indices if self.method == "uniform128" else None,
                ).float().cpu().numpy()[0]
                physical = vla._unnormalize_actions(normalized, self.stats_key)
        actions = postprocess_actions(physical)
        if self.reference is not None:
            expected_actions = self.reference["invert_gripper_action"](self.reference["normalize_gripper_action"](physical, binarize=True))
            if not np.array_equal(actions, expected_actions):
                raise RuntimeError("official gripper/action postprocessing differs")
        return PolicyChunk(normalized, actions, {"method": self.method, "visual_tokens": 128 if self.method == "uniform128" else 512,
            "inputs_version": INPUTS_VERSION, "action_version": ACTION_VERSION, "preprocessing_verification": verification,
            "policy_calls": 1, "normalized_proprio": inputs["normalized_proprio_numpy"].tolist()})


def _observation_hash(observation: Mapping[str, Any]) -> str:
    digest = hashlib.sha256()
    for name in ("agentview_image", "robot0_eye_in_hand_image", "robot0_eef_pos", "robot0_eef_quat", "robot0_gripper_qpos"):
        value = np.ascontiguousarray(observation[name])
        digest.update(name.encode() + str(value.dtype).encode() + str(value.shape).encode() + value.tobytes())
    return digest.hexdigest()


def run_episode(env, predict_chunk: Callable, instruction: str, initial_state, *, wait_steps=10, max_steps=220, policy_watchdog_seconds=60.0) -> dict[str, Any]:
    """One independent reset. The watchdog is a hang guard, not real-time control.

    A synchronously returned request exceeding the guard is rejected. A wedged
    CUDA process still requires the enclosing Slurm time limit; no unsafe thread
    cancellation is attempted.
    """
    if wait_steps < 0 or max_steps <= 0 or policy_watchdog_seconds <= 0:
        raise ValueError("invalid episode limits")
    started = time.perf_counter()
    result = {"status": "completed", "success": False, "termination": "task_horizon", "control_steps": 0,
              "wait_steps": 0, "policy_calls": 0, "chunks": [], "executed_actions": []}
    phase = "environment"
    try:
        env.reset()
        observation = env.set_init_state(np.asarray(initial_state, dtype=np.float64))
        if hasattr(predict_chunk, "reset"):
            predict_chunk.reset()
        for _ in range(wait_steps):
            observation, _, _, _ = env.step(list(DUMMY_ACTION))
            result["wait_steps"] += 1
        queue = deque()
        for control_step in range(max_steps):
            if not queue:
                phase = "policy"
                query_started = time.perf_counter()
                result["policy_calls"] += 1
                chunk = predict_chunk(observation, instruction)
                elapsed = time.perf_counter() - query_started
                if not isinstance(chunk, PolicyChunk):
                    raise TypeError("policy must return a validated PolicyChunk")
                if elapsed > policy_watchdog_seconds:
                    raise TimeoutError(f"policy watchdog exceeded: {elapsed:.3f}s")
                if bool((np.abs(chunk.environment_actions) > 1.00001).any()):
                    raise ValueError("environment action outside normalized controller [-1, 1] range")
                result["chunks"].append({"control_step": control_step, "observation_sha256": _observation_hash(observation),
                    "normalized_actions": chunk.normalized_actions.tolist(), "environment_actions": chunk.environment_actions.tolist(),
                    "engineering_seconds": elapsed, "metadata": dict(chunk.metadata)})
                queue.extend(np.asarray(chunk.environment_actions).copy())
            action = queue.popleft()
            result["executed_actions"].append(action.tolist())
            phase = "environment"
            observation, _, done, _ = env.step(action.tolist())
            result["control_steps"] += 1
            if bool(done):
                result.update(success=True, termination="environment_success")
                break
    except Exception as exc:
        result.update(status="policy_error" if phase == "policy" else "infrastructure_error", termination=type(exc).__name__, error=str(exc), error_phase=phase)
    result["wall_seconds"] = time.perf_counter() - started
    return result


class TrialLedger:
    """Append-only start/result events; completed trial IDs cannot run twice."""
    def __init__(self, path: str | Path, *, run_signature: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.run_signature = run_signature
        self.events = []
        self.recovered_tail = None
        if self.path.exists():
            content = self.path.read_bytes()
            lines = content.splitlines(keepends=True)
            valid_bytes = 0
            for index, line in enumerate(lines):
                try:
                    event = json.loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    # Only an unterminated last line can be an interrupted write.
                    # Preserve its bytes before truncating; interior corruption
                    # always fails instead of silently dropping trial records.
                    if index == len(lines) - 1 and not line.endswith(b"\n"):
                        backup = self.path.with_name(self.path.name + ".interrupted-" + hashlib.sha256(line).hexdigest()[:12])
                        backup.write_bytes(line)
                        with self.path.open("r+b") as stream:
                            stream.truncate(valid_bytes)
                            stream.flush()
                            os.fsync(stream.fileno())
                        self.recovered_tail = str(backup)
                        break
                    raise ValueError(f"corrupt ledger line {index + 1}; preserve and repair before resume") from exc
                if event.get("run_signature") != run_signature:
                    raise ValueError("ledger belongs to a different frozen run configuration")
                self.events.append(event)
                valid_bytes += len(line)
            # A complete JSON record may lack newline after interruption.
            if self.path.stat().st_size and not self.path.read_bytes().endswith(b"\n"):
                with self.path.open("ab") as stream:
                    stream.write(b"\n")
                    stream.flush()
                    os.fsync(stream.fileno())
        self._validate_duplicates()

    def _validate_duplicates(self):
        seen = set()
        for event in self.events:
            if event.get("event") == "result" and event.get("status") in ("completed", "policy_error"):
                if event["trial_id"] in seen:
                    raise ValueError("duplicate completed trial_id in ledger")
                seen.add(event["trial_id"])

    def completed(self) -> dict[str, dict]:
        return {row["trial_id"]: row for row in self.events if row.get("event") == "result" and row.get("status") in ("completed", "policy_error")}

    def append(self, event: Mapping[str, Any]) -> None:
        row = {**event, "run_signature": self.run_signature}
        if row.get("event") == "result" and row["trial_id"] in self.completed():
            raise ValueError("refusing to count a completed trial twice")
        encoded = json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        self.events.append(row)


def compare_dense_trials(official: Mapping[str, Any], migrated: Mapping[str, Any], *, atol=0.002) -> dict[str, Any]:
    """Report first observed divergence; never hide rollout drift behind averages."""
    first = None
    max_error = 0.0
    gripper_equal = True
    observations_equal = True
    compared_chunks = 0
    for index, (left, right) in enumerate(zip(official["chunks"], migrated["chunks"])):
        error = float(np.max(np.abs(np.asarray(left["normalized_actions"]) - np.asarray(right["normalized_actions"]))))
        grip = np.array_equal(np.asarray(left["environment_actions"])[:, -1], np.asarray(right["environment_actions"])[:, -1])
        same_obs = left["observation_sha256"] == right["observation_sha256"]
        max_error = max(max_error, error)
        gripper_equal &= grip
        observations_equal &= same_obs
        compared_chunks += 1
        if first is None and (error != 0 or not grip or not same_obs):
            first = {"chunk": index, "control_step": left["control_step"], "normalized_max_abs_error": error, "same_observation": same_obs, "gripper_equal": grip}
    same_counts = len(official["chunks"]) == len(migrated["chunks"])
    same_terminal = official["success"] == migrated["success"] and official["termination"] == migrated["termination"] and official["control_steps"] == migrated["control_steps"]
    passed = official["status"] == migrated["status"] == "completed" and compared_chunks > 0 and same_counts and same_terminal and observations_equal and gripper_equal and max_error <= atol
    return {"passed": passed, "atol": atol, "normalized_max_abs_error": max_error,
            "gripper_equal": bool(gripper_equal), "observations_equal": bool(observations_equal),
            "same_chunk_count": same_counts, "same_terminal": same_terminal,
            "compared_chunks": compared_chunks, "first_divergence": first}


__all__ = ["INPUTS_VERSION", "LIBERO_EVAL_INPUT_VERSION", "ACTION_VERSION", "METHODS", "PolicyChunk", "OpenVLARolloutPolicy", "TrialLedger",
    "process_camera", "raw_proprio_from_observation", "postprocess_actions", "uniform128_indices", "quaternion_to_axis_angle",
    "prepare_observation_inputs", "prepare_rlds_eval_inputs", "load_official_reference_functions", "verify_observation_preprocessing",
    "normalize_eval_proprio", "run_episode", "compare_dense_trials"]

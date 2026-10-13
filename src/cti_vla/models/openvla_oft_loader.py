"""Side-effect-free loader for the frozen OpenVLA-OFT LIBERO checkpoint."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping

import torch
from torch import nn


LIBERO_ACTION_CHUNK_SIZE = 8
LIBERO_ACTION_DIM = 7
LIBERO_PROPRIO_DIM = 8
OPENVLA_HIDDEN_DIM = 4096


class _MLPResNetBlock(nn.Module):
    def __init__(self, hidden_dim: int) -> None:
        super().__init__()
        self.ffn = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return inputs + self.ffn(inputs)


class _MLPResNet(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int) -> None:
        super().__init__()
        self.layer_norm1 = nn.LayerNorm(input_dim)
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.mlp_resnet_blocks = nn.ModuleList(
            [_MLPResNetBlock(hidden_dim), _MLPResNetBlock(hidden_dim)]
        )
        self.layer_norm2 = nn.LayerNorm(hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, output_dim)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        hidden = self.relu(self.fc1(self.layer_norm1(inputs)))
        for block in self.mlp_resnet_blocks:
            hidden = block(hidden)
        return self.fc2(self.layer_norm2(hidden))


class OpenVLAOFTL1ActionHead(nn.Module):
    """Official deterministic OFT head with an explicit `[B, 8, 7]` contract."""

    def __init__(
        self,
        hidden_dim: int = OPENVLA_HIDDEN_DIM,
        *,
        action_chunk_size: int = LIBERO_ACTION_CHUNK_SIZE,
        action_dim: int = LIBERO_ACTION_DIM,
    ) -> None:
        super().__init__()
        if hidden_dim <= 0 or action_chunk_size <= 0 or action_dim <= 0:
            raise ValueError("action-head dimensions must be positive")
        self.hidden_dim = hidden_dim
        self.action_chunk_size = action_chunk_size
        self.action_dim = action_dim
        self.model = _MLPResNet(
            input_dim=hidden_dim * action_dim,
            hidden_dim=hidden_dim,
            output_dim=action_dim,
        )

    def predict_action(self, action_hidden_states: torch.Tensor) -> torch.Tensor:
        expected = (self.action_chunk_size * self.action_dim, self.hidden_dim)
        if action_hidden_states.ndim != 3 or action_hidden_states.shape[1:] != expected:
            raise ValueError(
                "action hidden states must be "
                f"[B, {self.action_chunk_size * self.action_dim}, {self.hidden_dim}]"
            )
        if not action_hidden_states.is_floating_point():
            raise TypeError("action hidden states must be floating point")
        if not torch.isfinite(action_hidden_states).all():
            raise ValueError("action hidden states contain NaN/Inf")
        batch_size = action_hidden_states.shape[0]
        grouped = action_hidden_states.reshape(batch_size, self.action_chunk_size, -1)
        actions = self.model(grouped)
        expected_output = (batch_size, self.action_chunk_size, self.action_dim)
        if actions.shape != expected_output or not torch.isfinite(actions).all():
            raise RuntimeError("OFT action head produced an invalid action chunk")
        return actions

    def forward(self, action_hidden_states: torch.Tensor) -> torch.Tensor:
        return self.predict_action(action_hidden_states)


class OpenVLAOFTProprioProjector(nn.Module):
    """Official two-layer OFT proprio projector."""

    def __init__(
        self,
        hidden_dim: int = OPENVLA_HIDDEN_DIM,
        proprio_dim: int = LIBERO_PROPRIO_DIM,
    ) -> None:
        super().__init__()
        if hidden_dim <= 0 or proprio_dim <= 0:
            raise ValueError("proprio-projector dimensions must be positive")
        self.hidden_dim = hidden_dim
        self.proprio_dim = proprio_dim
        self.fc1 = nn.Linear(proprio_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.act_fn1 = nn.GELU()

    def forward(self, proprio: torch.Tensor) -> torch.Tensor:
        if proprio.ndim != 2 or proprio.shape[1] != self.proprio_dim:
            raise ValueError(f"proprio must be [B, {self.proprio_dim}]")
        if not proprio.is_floating_point() or not torch.isfinite(proprio).all():
            raise ValueError("proprio must be finite floating point")
        output = self.fc2(self.act_fn1(self.fc1(proprio)))
        if output.shape != (proprio.shape[0], self.hidden_dim) or not torch.isfinite(output).all():
            raise RuntimeError("proprio projector produced invalid features")
        return output


@dataclass(frozen=True)
class OpenVLAOFTComponents:
    vla: nn.Module
    action_head: OpenVLAOFTL1ActionHead
    proprio_projector: OpenVLAOFTProprioProjector
    num_patches_full: int


def remove_uniform_ddp_prefix(state_dict: Mapping[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    """Remove an all-or-none `module.` prefix and reject ambiguous checkpoints."""

    if not state_dict:
        raise ValueError("component state dict must not be empty")
    if not all(isinstance(key, str) and isinstance(value, torch.Tensor) for key, value in state_dict.items()):
        raise TypeError("component state dict must map string keys to tensors")
    prefixed = [key.startswith("module.") for key in state_dict]
    if any(prefixed) and not all(prefixed):
        raise ValueError("component state dict mixes DDP-prefixed and unprefixed keys")
    stripped = {
        key[7:] if has_prefix else key: value
        for (key, value), has_prefix in zip(state_dict.items(), prefixed)
    }
    if any(not key for key in stripped) or len(stripped) != len(state_dict):
        raise ValueError("invalid or colliding keys after removing DDP prefix")
    return stripped


def _load_component_state(path: Path) -> dict[str, torch.Tensor]:
    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(path)
    try:
        state = torch.load(str(path), map_location="cpu", weights_only=True, mmap=True)
    except TypeError:
        state = torch.load(path, map_location="cpu", weights_only=True)
    if not isinstance(state, Mapping):
        raise TypeError(f"component checkpoint is not a state dict: {path}")
    return remove_uniform_ddp_prefix(state)


def _module_device(module: nn.Module) -> torch.device:
    devices = {parameter.device for parameter in module.parameters()}
    if len(devices) != 1:
        raise RuntimeError(f"module parameters span unexpected devices: {sorted(map(str, devices))}")
    return next(iter(devices))


def load_openvla_oft_components(
    checkpoint: str | Path,
    *,
    device: str | torch.device = "cuda:0",
    dtype: torch.dtype = torch.bfloat16,
    num_images_in_input: int = 2,
    local_files_only: bool = True,
    use_minimal_prismatic_compat: bool = False,
) -> OpenVLAOFTComponents:
    """Load the immutable model and OFT components without upstream file mutation."""

    checkpoint_path = Path(checkpoint).resolve()
    if checkpoint_path.is_symlink() or not checkpoint_path.is_dir():
        raise FileNotFoundError(checkpoint_path)
    if checkpoint_path.name.startswith(".") or "partial" in checkpoint_path.name.lower():
        raise ValueError("refusing to load a partial/hidden checkpoint directory")
    target_device = torch.device(device)
    if target_device.type != "cuda" or target_device.index is None:
        raise ValueError("real 7B smoke requires an explicit CUDA device such as cuda:0")
    if not torch.cuda.is_available() or target_device.index >= torch.cuda.device_count():
        raise RuntimeError(f"requested CUDA device is unavailable: {target_device}")
    with torch.cuda.device(target_device):
        supports_bf16 = torch.cuda.is_bf16_supported()
    if dtype is not torch.bfloat16 or not supports_bf16:
        raise RuntimeError("OpenVLA-OFT smoke requires bf16 on a bf16-capable GPU")
    if num_images_in_input != 2:
        raise ValueError("the frozen CTI-VLA/OpenVLA-OFT boundary requires exactly two images")

    from cti_vla.models.openvla_oft_runtime_compat import (
        install_prismatic_runtime_compat, validate_oft_sdpa_runtime,
    )

    install_prismatic_runtime_compat(use_minimal_compat=use_minimal_prismatic_compat)
    validate_oft_sdpa_runtime()

    from transformers import AutoModelForVision2Seq

    vla = AutoModelForVision2Seq.from_pretrained(
        checkpoint_path,
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
        trust_remote_code=True,
        local_files_only=local_files_only,
        attn_implementation="sdpa",
    )
    vla.eval().requires_grad_(False)
    vla.to(target_device)

    statistics_path = checkpoint_path / "dataset_statistics.json"
    if statistics_path.is_symlink() or not statistics_path.is_file():
        raise FileNotFoundError(f"missing dataset statistics: {statistics_path}")
    dataset_statistics = json.loads(statistics_path.read_text(encoding="utf-8"))
    if not isinstance(dataset_statistics, dict) or not dataset_statistics:
        raise ValueError("dataset_statistics.json must contain a non-empty object")
    vla.norm_stats = dataset_statistics

    hidden_dim = int(getattr(vla, "llm_dim", 0))
    if hidden_dim != OPENVLA_HIDDEN_DIM:
        raise RuntimeError(f"expected OpenVLA hidden dim 4096, got {hidden_dim}")
    vision_backbone = getattr(vla, "vision_backbone", None)
    projector = getattr(vla, "projector", None)
    language_model = getattr(vla, "language_model", None)
    language_backbone = getattr(language_model, "model", None)
    if not all(isinstance(item, nn.Module) for item in (vision_backbone, projector, language_backbone)):
        raise RuntimeError("checkpoint is missing a required OpenVLA module boundary")
    if getattr(getattr(language_backbone, "config", None), "_attn_implementation", None) != "sdpa":
        raise RuntimeError("OFT must use the audited bidirectional SDPA implementation")
    embedding = vla.get_input_embeddings()
    if not isinstance(embedding, nn.Module) or not any(embedding is item for item in language_backbone.modules()):
        raise RuntimeError("input embeddings do not belong to vla.language_model.model")
    if _module_device(vla) != target_device:
        raise RuntimeError("VLA parameters did not move wholly to the requested device")

    vision_backbone.set_num_images_in_input(num_images_in_input)
    patches_per_image = int(vision_backbone.get_num_patches())
    num_patches_full = patches_per_image * int(vision_backbone.get_num_images_in_input())
    if patches_per_image != 256 or num_patches_full != 512:
        raise RuntimeError("the frozen CTI-VLA checkpoint requires 256 patches per image and 512 total")

    action_head = OpenVLAOFTL1ActionHead(hidden_dim).to(dtype=dtype)
    action_state = _load_component_state(checkpoint_path / "action_head--150000_checkpoint.pt")
    action_head.load_state_dict(action_state, strict=True)
    del action_state
    action_head.to(target_device).eval().requires_grad_(False)

    proprio_projector = OpenVLAOFTProprioProjector(hidden_dim, LIBERO_PROPRIO_DIM).to(dtype=dtype)
    proprio_state = _load_component_state(checkpoint_path / "proprio_projector--150000_checkpoint.pt")
    proprio_projector.load_state_dict(proprio_state, strict=True)
    del proprio_state
    proprio_projector.to(target_device).eval().requires_grad_(False)

    for name, module in (
        ("VLA", vla),
        ("action head", action_head),
        ("proprio projector", proprio_projector),
    ):
        if module.training or any(parameter.requires_grad for parameter in module.parameters()):
            raise RuntimeError(f"{name} must be frozen and in eval mode")
        if _module_device(module) != target_device:
            raise RuntimeError(f"{name} is not wholly on {target_device}")
        if any(parameter.dtype is not dtype for parameter in module.parameters()):
            raise RuntimeError(f"{name} contains a non-bf16 parameter")

    return OpenVLAOFTComponents(
        vla=vla,
        action_head=action_head,
        proprio_projector=proprio_projector,
        num_patches_full=num_patches_full,
    )


__all__ = [
    "LIBERO_ACTION_CHUNK_SIZE",
    "LIBERO_ACTION_DIM",
    "LIBERO_PROPRIO_DIM",
    "OPENVLA_HIDDEN_DIM",
    "OpenVLAOFTComponents",
    "OpenVLAOFTL1ActionHead",
    "OpenVLAOFTProprioProjector",
    "load_openvla_oft_components",
    "remove_uniform_ddp_prefix",
]

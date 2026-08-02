"""Single-card, offline OpenVLA-OFT checkpoint structure and OOM smoke test."""

from __future__ import annotations

import argparse
import gc
import json
import os
from pathlib import Path
import time


def _configure_huggingface_cache(cache_directory: Path) -> None:
    cache_directory = cache_directory.resolve()
    for child in (cache_directory, cache_directory / "hub", cache_directory / "modules"):
        child.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(cache_directory)
    os.environ["HF_HUB_CACHE"] = str(cache_directory / "hub")
    os.environ["HF_MODULES_CACHE"] = str(cache_directory / "modules")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--cache-directory", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()

    _configure_huggingface_cache(args.cache_directory)

    import torch

    from diwa.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from diwa.evaluation.preflight import validate_openvla_oft_structure
    from diwa.models.openvla_oft_loader import load_openvla_oft_components

    if torch.cuda.device_count() != 1:
        raise RuntimeError(
            "smoke process must expose exactly one GPU; set CUDA_VISIBLE_DEVICES to one device"
        )
    target_device = torch.device(args.device)
    if target_device != torch.device("cuda:0"):
        raise ValueError("inside the single-visible-GPU process, --device must be cuda:0")
    torch.cuda.set_device(target_device)
    torch.cuda.init()

    manifest = load_checkpoint_manifest(args.manifest)
    before = verify_checkpoint_directory(args.checkpoint, manifest)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(target_device)
    started = time.perf_counter()
    components = load_openvla_oft_components(
        args.checkpoint,
        device=target_device,
        use_minimal_prismatic_compat=True,
    )
    torch.cuda.synchronize(target_device)
    load_seconds = time.perf_counter() - started

    structure = validate_openvla_oft_structure(
        components.vla,
        components.action_head,
        components.proprio_projector,
    )
    result = {
        "checkpoint_revision": before.revision,
        "checkpoint_file_count": before.file_count,
        "loaded_class": f"{type(components.vla).__module__}.{type(components.vla).__name__}",
        "parameter_count": sum(parameter.numel() for parameter in components.vla.parameters()),
        "trainable_parameter_count": sum(
            parameter.numel() for parameter in components.vla.parameters() if parameter.requires_grad
        ),
        "model_dtype": sorted({str(parameter.dtype) for parameter in components.vla.parameters()}),
        "model_device": sorted({str(parameter.device) for parameter in components.vla.parameters()}),
        "llm_dim": int(components.vla.llm_dim),
        "num_patches_full": components.num_patches_full,
        "structure": structure,
        "load_seconds": load_seconds,
        "allocated_bytes": torch.cuda.memory_allocated(target_device),
        "reserved_bytes": torch.cuda.memory_reserved(target_device),
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(target_device),
    }
    print("STRUCTURAL_SMOKE_RESULT=" + json.dumps(result, sort_keys=True), flush=True)

    del components
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.synchronize(target_device)
    released = {
        "allocated_bytes": torch.cuda.memory_allocated(target_device),
        "reserved_bytes": torch.cuda.memory_reserved(target_device),
    }
    if released["allocated_bytes"] != 0:
        raise RuntimeError(f"CUDA tensors remain allocated after component release: {released}")
    print("POST_RELEASE=" + json.dumps(released, sort_keys=True), flush=True)

    after = verify_checkpoint_directory(args.checkpoint, manifest)
    if after != before:
        raise RuntimeError("checkpoint verification changed across side-effect-free load")
    print("POST_LOAD_CHECKPOINT=" + json.dumps(after.__dict__, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

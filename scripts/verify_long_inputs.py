"""Three fixed Long train frames: official public dense and input/action parity.

This produces G1-F00-input-parity, not G0 or a closed-loop result. Only root
submits real execution; prepare-only performs metadata checks without a GPU.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict, replace
from io import BytesIO
import importlib.util
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]


def training_runner():
    spec = importlib.util.spec_from_file_location("long_input_shared_training", ROOT / "scripts/run_g1_future.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_one(episode, window, components, processor, policy, reference, *, stats_key, query):
    import numpy as np
    from PIL import Image
    import torch
    from cti_vla.data.future_windows import normalize_demo_actions
    from cti_vla.evaluation import libero_runtime as runtime
    vla = components.vla
    device, dtype = next(vla.parameters()).device, next(vla.parameters()).dtype
    step = window["start_step"]
    stats = vla.norm_stats[stats_key]
    inputs = runtime.prepare_rlds_eval_inputs(episode, step, processor, stats["proprio"], device=device, dtype=dtype)
    prompt = f"In: What action should the robot take to {episode.instructions[step].lower()}?\nOut:"
    official_cameras, raw_equal = [], True
    for key, fn, encoded in zip(("agentview_image", "robot0_eye_in_hand_image"),
            ("get_libero_image", "get_libero_wrist_image"), (episode.images[step], episode.wrist_images[step])):
        with Image.open(BytesIO(encoded)) as image:
            decoded = np.asarray(image.convert("RGB"))
        expected = reference["center_crop_image"](reference["resize_image_for_policy"](decoded, 224))
        official_cameras.append(processor(prompt, expected, return_tensors="pt"))
        # RLDS was already rotated. Probe the raw-camera orientation boundary
        # on its inverse without claiming this is a newly captured sim frame.
        raw = np.ascontiguousarray(decoded[::-1, ::-1])
        raw_expected = reference["center_crop_image"](reference["resize_image_for_policy"](reference[fn]({key: raw}), 224))
        raw_equal &= np.array_equal(np.asarray(runtime.process_camera(raw)), np.asarray(raw_expected))
        raw_equal &= np.array_equal(np.asarray(raw_expected), np.asarray(expected))
    official_pixels = torch.cat([x["pixel_values"] for x in official_cameras], dim=1).to(device=device, dtype=dtype)
    pixels_equal = torch.equal(inputs["pixel_values"], official_pixels)
    prompt_equal = all(torch.equal(inputs[k], x[k].to(device)) for x in official_cameras for k in ("input_ids", "attention_mask"))
    official_prop = reference["normalize_proprio"](np.asarray(episode.proprio[step]).copy(), stats["proprio"])
    prop_error = float(np.max(np.abs(inputs["normalized_proprio_numpy"] - official_prop)))
    if not pixels_equal or not prompt_equal or not raw_equal or prop_error > 1e-6:
        raise RuntimeError("Long raw/RLDS image, prompt or proprio differs from pinned official functions")
    raw_actions = episode.actions[window["action_start"]:window["action_stop_exclusive"]]
    demonstration = normalize_demo_actions(raw_actions, stats["action"])
    physical_demo = vla._unnormalize_actions(demonstration, stats_key)
    expected_demo = np.asarray(raw_actions, dtype=np.float32).copy()
    expected_demo[:, -1] = 1 - np.clip(expected_demo[:, -1], 0, 1)
    low, high = np.asarray(stats["action"]["q01"]), np.asarray(stats["action"]["q99"])
    mask = np.asarray(stats["action"]["mask"], dtype=bool)
    expected_demo = np.where(mask, np.clip(expected_demo, low, high), expected_demo)
    constant = np.asarray(stats["action"]["min"]) == np.asarray(stats["action"]["max"])
    expected_demo = np.where(constant, np.where(mask, (low + high) / 2, 0), expected_demo)
    demo_error = float(np.max(np.abs(physical_demo - expected_demo)))
    if not np.isfinite(demonstration).all() or demo_error > 1e-5:
        raise RuntimeError("Long demonstration normalization disagrees with native inverse bounds/gripper")

    def official_forward():
        physical, hidden = vla.predict_action(input_ids=official_cameras[0]["input_ids"].to(device),
            attention_mask=official_cameras[0]["attention_mask"].to(device), pixel_values=official_pixels,
            proprio=official_prop, proprio_projector=components.proprio_projector,
            action_head=components.action_head, unnorm_key=stats_key, use_film=False)
        normalized = components.action_head.predict_action(hidden).float().cpu().numpy()[0]
        return np.asarray(physical), normalized

    def shared_forward():
        visual = vla._process_vision_features(inputs["pixel_values"], None, False)
        return policy.forward_from_full_tokens(visual, inputs["normalized_proprio"],
            input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"]).float().cpu().numpy()[0]

    with torch.inference_mode():
        native_physical, official = query("official_dense", official_forward)
        migrated = query("shared_dense", shared_forward)
    error = float(np.max(np.abs(official - migrated)))
    native_equal = np.array_equal(native_physical, vla._unnormalize_actions(official, stats_key))
    expected_control = reference["invert_gripper_action"](reference["normalize_gripper_action"](native_physical, binarize=True))
    migrated_control = runtime.postprocess_actions(vla._unnormalize_actions(migrated, stats_key))
    post_equal = np.array_equal(runtime.postprocess_actions(native_physical), expected_control)
    gripper_equal = np.array_equal(migrated_control[:, -1], expected_control[:, -1])
    passed = bool(error <= .002 and native_equal and post_equal and gripper_equal)
    row = dict(window=window, pixels_equal=bool(pixels_equal), prompt_equal=bool(prompt_equal),
        raw_camera_bridge_equal=bool(raw_equal), proprio_max_abs_error=prop_error, dense_max_abs_error=error,
        native_physical_equal=bool(native_equal), action_postprocess_equal=bool(post_equal),
        gripper_equal=bool(gripper_equal), demonstration_normalization_valid=True,
        demonstration_inverse_max_abs_error=demo_error, passed=passed)
    if not passed:
        raise RuntimeError(f"Long official dense/action parity failed: {row}")
    return row


def run(args):
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation.future_input_acceptance import select_input_windows, INPUT_ACCEPTANCE_VERSION, require_long_input_acceptance, verify_input_acceptance_journal
    from cti_vla.evaluation.future_profiling import validate_new_output_paths
    from cti_vla.evaluation import libero_runtime as runtime
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    shared = training_runner()
    config, asset = shared.read_json(args.config), load_checkpoint_manifest(args.asset_manifest)
    suite, protocol, manifest, windows_api = shared.data_registration(args, config, asset)
    if suite != "libero_10":
        raise ValueError("this bounded input acceptance is exclusively Long")
    selected = select_input_windows(manifest, protocol)
    if args.prepare_only:
        return {"status": "prepared_only", "suite": suite, "selected_windows": selected,
            "gpu_calls": 0, "planned_policy_forwards": 6, "planned_vision_forwards": 6, "test_opened": False}
    if os.name == "nt" or not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Long real input acceptance requires a server Slurm allocation")
    validate_new_output_paths(project_root=args.project_root, source_root=ROOT,
        output=args.output, cache=args.cache_directory, weight_roots=[args.checkpoint])
    sources = shared.source_hashes()
    watched = {str(p.resolve()): shared.file_hash(p) for p in
        (args.config, args.protocol, args.windows, args.asset_manifest, Path(__file__))}
    before = verify_checkpoint_directory(args.checkpoint, asset)
    for folder in (args.cache_directory, args.cache_directory / "hub", args.cache_directory / "modules"):
        folder.mkdir(parents=True, exist_ok=True)
    os.environ.update(HF_HOME=str(args.cache_directory), HF_HUB_CACHE=str(args.cache_directory / "hub"),
        HF_MODULES_CACHE=str(args.cache_directory / "modules"), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    import torch
    from transformers import AutoProcessor
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
    from cti_vla.data.sequence_example import decode_libero_example
    from cti_vla.data.tfrecord import iter_tfrecord_records
    if torch.cuda.device_count() != 1:
        raise RuntimeError("Long input acceptance requires exactly one allocated GPU")
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    torch.manual_seed(17)
    reference = runtime.load_official_reference_functions(args.oft_source)
    watched.update({str((args.oft_source / p).resolve()): shared.file_hash(args.oft_source / p) for p in runtime._REFERENCE_FILES})
    args.output.mkdir(parents=True, exist_ok=False)
    journal = args.output / "calls.jsonl"
    started, call_count, completed_count = time.perf_counter(), 0, 0
    try:
        components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
        processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
        policy = OpenVLAOFTTokenPolicy(components.vla, components.action_head, components.proprio_projector, num_patches_full=512)
        torch.cuda.reset_peak_memory_stats(device)
        by_shard = defaultdict(lambda: defaultdict(list))
        for row in selected:
            by_shard[row["source_shard"]][row["record_index"]].append(row)
        checked = {}
        for shard, wanted in sorted(by_shard.items()):
            path = args.data_directory / shard
            if {"bytes": path.stat().st_size, "sha256": shared.file_hash(path)} != manifest["source_files"][shard]:
                raise ValueError("Long source shard differs from the frozen windows")
            for index, payload in iter_tfrecord_records(path):
                if index not in wanted:
                    continue
                episode = replace(decode_libero_example(payload), source_shard=shard, record_index=index)
                for row in wanted[index]:
                    windows_api.validate_future_window(row, episode, protocol)
                    def query(kind, fn):
                        nonlocal call_count, completed_count
                        meta = {"call_id": call_count, "window_id": row["window_id"], "kind": kind,
                                "job_id": os.environ["SLURM_JOB_ID"]}
                        call_count += 1
                        shared.append_json(journal, {"event": "start", **meta})
                        began = time.perf_counter()
                        try:
                            result = fn()
                            torch.cuda.synchronize(device)
                        except BaseException as exc:
                            shared.append_json(journal, {"event": "failed", **meta, "error": str(exc)})
                            raise
                        shared.append_json(journal, {"event": "complete", **meta, "seconds": time.perf_counter() - began})
                        completed_count += 1
                        return result
                    checked[row["window_id"]] = verify_one(episode, row, components, processor, policy, reference,
                        stats_key=args.stats_key, query=query)
        observations = [checked[r["window_id"]] for r in selected]
        after = verify_checkpoint_directory(args.checkpoint, asset)
        if before != after or sources != shared.source_hashes() or any(shared.file_hash(Path(p)) != sha for p, sha in watched.items()):
            raise ValueError("Long input acceptance source/config/checkpoint changed")
        report = {"stage": "G1-F00-input-parity", "status": "passed", "execution": "real_frozen_openvla_l40",
            "version": INPUT_ACCEPTANCE_VERSION, "suite": suite, "stats_key": args.stats_key,
            "model_revision": asset.revision, "config_sha256": json_signature(config),
            "window_manifest_sha256": shared.file_hash(args.windows), "protocol_sha256": shared.file_hash(args.protocol),
            "asset_manifest_sha256": shared.file_hash(args.asset_manifest), "source_files": sources,
            "verification_script_sha256": shared.file_hash(Path(__file__)),
            "input_version": runtime.INPUTS_VERSION, "action_version": runtime.ACTION_VERSION, "packing_version": PACKING_VERSION,
            "checkpoint_unchanged": True, "checkpoint": asdict(after), "observations": observations,
            "dataset_statistics_sha256": shared.file_hash(args.checkpoint / "dataset_statistics.json"),
            "policy_sample_forwards": completed_count, "vision_forwards": completed_count,
            "policy_attempts": call_count, "calls_jsonl_sha256": shared.file_hash(journal),
            "official_source_revision": runtime.OFT_COMMIT,
            "official_reference_files": {p: shared.file_hash(args.oft_source / p) for p in runtime._REFERENCE_FILES},
            "hardware": torch.cuda.get_device_name(), "peak_memory_allocated_bytes": torch.cuda.max_memory_allocated(device),
            "wall_seconds": time.perf_counter() - started, "job_id": os.environ["SLURM_JOB_ID"], "test_opened": False,
            "scope": "Three fixed registered train frames; RLDS raw-camera orientation bridge, not a simulator rollout or latency result."}
        require_long_input_acceptance(report, config=config, window_manifest_sha256=shared.file_hash(args.windows),
            protocol_sha256=shared.file_hash(args.protocol), asset_manifest_sha256=shared.file_hash(args.asset_manifest),
            source_files=sources, verification_script_sha256=shared.file_hash(Path(__file__)), selected_windows=selected)
        verify_input_acceptance_journal(journal, report)
        atomic_json(args.output / "input_acceptance.json", report)
        return report
    except BaseException as exc:
        atomic_json(args.output / "failure.json", {"status": "failed", "error": f"{type(exc).__name__}: {exc}",
            "attempted_policy_calls": call_count, "completed_policy_calls": completed_count,
            "wall_seconds": time.perf_counter() - started, "test_opened": False,
            "scope": "Starts without completions remain charged; hard-kill cost requires journal and Slurm accounting."})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("config", "windows", "protocol", "checkpoint", "asset-manifest", "data-directory",
                 "oft-source", "cache-directory", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--suite", choices=("libero_10",), required=True)
    parser.add_argument("--stats-key", choices=("libero_10_no_noops",), required=True)
    parser.add_argument("--prepare-only", action="store_true")
    print(json.dumps(run(parser.parse_args()), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

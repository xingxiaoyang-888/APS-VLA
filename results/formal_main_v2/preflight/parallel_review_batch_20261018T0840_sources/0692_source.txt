"""G0: 90 frozen train observations, official preprocessing and dense parity."""
from __future__ import annotations

import argparse
from collections import Counter
from io import BytesIO
import json
import os
from pathlib import Path
import time

from smoke_openvla import configure_cache, _official_normalized


def run(args):
    configure_cache(args.cache_directory, args.checkpoint)
    import numpy as np
    from PIL import Image
    import torch
    from transformers import AutoProcessor
    from cti_vla.data.identity import file_sha256
    from cti_vla.data.experiment_protocol import load_experiment_protocol
    from cti_vla.data.libero import load_manifest
    from cti_vla.data.sequence_example import iter_libero_examples
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation.libero_runtime import (
        INPUTS_VERSION, ACTION_VERSION, load_official_reference_functions,
        prepare_rlds_eval_inputs, postprocess_actions,
    )
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
    protocol = load_experiment_protocol(args.protocol)
    panel = load_manifest(args.panel)
    expected_panel = protocol.payload['panels']['diagnostic_90']['sha256']
    if file_sha256(args.panel) != expected_panel or panel.split != 'train' or panel.sample_count != 90:
        raise ValueError('G0 requires the frozen 90-observation training panel')
    for sample in panel.samples:
        protocol.require_sample(sample.episode_id, sample.step_index, split='train')
    if torch.cuda.device_count() != 1:
        raise RuntimeError('G0 must run inside a one-GPU allocation')
    device = torch.device('cuda:0')
    torch.cuda.set_device(device)
    torch.manual_seed(17)
    reference = load_official_reference_functions(args.oft_source)
    checkpoint_manifest = load_checkpoint_manifest(args.checkpoint_manifest)
    verify_checkpoint_directory(args.checkpoint, checkpoint_manifest)
    components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
    vla = components.vla
    processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
    stats_key = args.stats_key
    stats = vla.norm_stats[stats_key]['proprio']
    policy = OpenVLAOFTTokenPolicy(vla, components.action_head, components.proprio_projector, num_patches_full=512)
    args.output.mkdir(parents=True, exist_ok=True)
    record_path = args.output / 'observations.jsonl'
    if record_path.exists():
        raise FileExistsError('G0 verification output already exists; preserve it and use a new run directory')
    started = time.monotonic()
    rows = []
    by_shard = {}
    samples = {}
    for ref in panel.episodes:
        by_shard.setdefault(ref.source_shard, {})[ref.record_index] = ref
    for sample in panel.samples:
        samples.setdefault(sample.episode_id, []).append(sample)
    with record_path.open('x', encoding='utf-8', newline='\n') as output:
        for shard, wanted in sorted(by_shard.items()):
            found = set()
            for episode in iter_libero_examples(args.data_directory / shard):
                if episode.record_index not in wanted:
                    continue
                ref = wanted[episode.record_index]
                if episode.episode_id != ref.episode_id or episode.num_steps != ref.num_steps:
                    raise ValueError('RLDS episode content does not match the frozen panel')
                found.add(episode.record_index)
                for sample in samples[episode.episode_id]:
                    index = sample.step_index
                    inputs = prepare_rlds_eval_inputs(episode, index, processor, stats, device=device, dtype=torch.bfloat16)
                    # Independently execute unmodified pinned upstream functions.
                    prompt = f'In: What action should the robot take to {episode.instructions[index].lower()}?\nOut:'
                    official_camera_inputs = []
                    for encoded in (episode.images[index], episode.wrist_images[index]):
                        with Image.open(BytesIO(encoded)) as image:
                            raw = np.asarray(image.convert('RGB'))
                        # Official regenerate_libero_dataset.py documents that
                        # RLDS conversion already rotates images by 180 degrees.
                        image = reference['center_crop_image'](reference['resize_image_for_policy'](raw, 224))
                        official_camera_inputs.append(processor(prompt, image, return_tensors='pt'))
                    expected_pixels = torch.cat([item['pixel_values'] for item in official_camera_inputs], dim=1).to(device=device, dtype=torch.bfloat16)
                    pixels_equal = torch.equal(inputs['pixel_values'], expected_pixels)
                    prompt_equal = all(torch.equal(inputs[key], camera[key].to(device))
                                       for camera in official_camera_inputs for key in ('input_ids', 'attention_mask'))
                    expected_proprio = reference['normalize_proprio'](np.asarray(episode.proprio[index]).copy(), stats)
                    prop_error = float(np.max(np.abs(inputs['normalized_proprio_numpy'] - expected_proprio)))
                    with torch.inference_mode():
                        visual = vla._process_vision_features(inputs['pixel_values'], None, False)
                        official = _official_normalized(components, visual, inputs)
                        migrated = policy.forward_from_full_tokens(visual, inputs['normalized_proprio'], input_ids=inputs['input_ids'], attention_mask=inputs['attention_mask'])
                    error = float((official.float() - migrated.float()).abs().max().item())
                    native_physical = vla._unnormalize_actions(official.float().cpu().numpy()[0], stats_key)
                    migrated_physical = vla._unnormalize_actions(migrated.float().cpu().numpy()[0], stats_key)
                    expected_control = reference['invert_gripper_action'](reference['normalize_gripper_action'](native_physical, binarize=True))
                    migrated_control = postprocess_actions(migrated_physical)
                    gripper_equal = bool(np.array_equal(expected_control[:, -1], migrated_control[:, -1]))
                    postprocess_equal = bool(np.array_equal(postprocess_actions(native_physical), expected_control))
                    passed = pixels_equal and prompt_equal and prop_error <= 1e-6 and error <= args.atol and gripper_equal and postprocess_equal
                    row = dict(sample_id=sample.sample_id, episode_id=sample.episode_id, step_index=index, stage=sample.stage,
                        task=ref.task_name, pixels_equal=pixels_equal, prompt_equal=prompt_equal,
                        proprio_max_abs_error=prop_error, dense_max_abs_error=error, gripper_equal=gripper_equal,
                        action_postprocess_equal=postprocess_equal, passed=passed)
                    if error != 0 or not passed:
                        row['official_normalized_actions'] = official.float().cpu().numpy()[0].tolist()
                        row['migrated_normalized_actions'] = migrated.float().cpu().numpy()[0].tolist()
                    output.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')
                    output.flush()
                    os.fsync(output.fileno())
                    rows.append(row)
                    print(f'G0 observation {len(rows)}/90 passed={passed} max_error={error:.6g}', flush=True)
                    if not passed:
                        raise RuntimeError(f'G0 observation parity failed: {row}')
            if found != set(wanted):
                raise RuntimeError('missing observations in source shard')
    verify_checkpoint_directory(args.checkpoint, checkpoint_manifest)
    from importlib.metadata import version
    result = {
        'stage': 'g0_observation_parity', 'status': 'passed' if len(rows) == 90 else 'failed',
        'dense_parity': {'passed': len(rows) == 90 and all(x['passed'] for x in rows), 'observations': len(rows),
                         'max_abs_error': max(x['dense_max_abs_error'] for x in rows), 'atol': args.atol},
        'coverage': {'tasks': len(set(x['task'] for x in rows)), 'phases': dict(Counter(x['stage'] for x in rows))},
        'checkpoint_unchanged': True,
        'observations_jsonl_sha256': file_sha256(record_path),
        'provenance': {'model_revision': checkpoint_manifest.revision, 'input_version': INPUTS_VERSION,
                       'action_version': ACTION_VERSION, 'packing_version': PACKING_VERSION, 'panel_sha256': file_sha256(args.panel),
                       'checkpoint_manifest_sha256': file_sha256(args.checkpoint_manifest),
                       'protocol_signature': protocol.payload['content_signature'],
                       'script_sha256': file_sha256(Path(__file__)),
                       'reference_script_sha256': file_sha256(Path(__file__).with_name('smoke_openvla.py')),
                       'runtime_sha256': file_sha256(Path(__file__).resolve().parents[1] / 'src/cti_vla/evaluation/libero_runtime.py'),
                       'slurm_job_id': os.environ.get('SLURM_JOB_ID'),
                       'torch': torch.__version__, 'tensorflow_cpu': version('tensorflow-cpu'), 'gpu': torch.cuda.get_device_name()},
        'policy_sample_forwards': len(rows) * 2, 'vision_forwards': len(rows), 'wall_seconds': time.monotonic() - started,
        'note': 'Engineering acceptance only; not a method-success or end-to-end-speed result.'}
    (args.output / 'observation_report.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--checkpoint-manifest', type=Path, default=Path('configs/assets/openvla_oft_libero_spatial.json'))
    parser.add_argument('--protocol', type=Path, default=Path('configs/manifests/spatial_g0g1_v1/protocol.json'))
    parser.add_argument('--panel', type=Path, default=Path('configs/manifests/spatial_g0g1_v1/diagnostic_90.json'))
    parser.add_argument('--data-directory', type=Path, required=True)
    parser.add_argument('--oft-source', type=Path, required=True)
    parser.add_argument('--cache-directory', type=Path, default=Path('.local/huggingface'))
    parser.add_argument('--stats-key', default='libero_spatial_no_noops')
    parser.add_argument('--atol', type=float, default=0.002)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not 0 < args.atol <= 0.002:
        parser.error('G0 tolerance must be positive and no looser than 0.002')
    if args.output.resolve() == args.checkpoint.resolve() or args.checkpoint.resolve() in args.output.resolve().parents:
        parser.error('output must be outside the immutable checkpoint')
    run(args)

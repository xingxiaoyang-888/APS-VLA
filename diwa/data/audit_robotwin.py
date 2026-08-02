"""Bounded, read-only RoboTwin schema and sample smoke test."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .robotwin import RobotTwinHDF5Adapter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--max-episodes-per-task", type=int, default=2)
    parser.add_argument("--cameras", nargs=2, default=("head_camera", "right_camera"))
    parser.add_argument("--decode-one-sample", action="store_true")
    args = parser.parse_args()

    adapter = RobotTwinHDF5Adapter(args.dataset_root, cameras=args.cameras)
    summary = adapter.audit(max_episodes_per_task=args.max_episodes_per_task)
    result = summary.to_dict()
    if args.decode_one_sample:
        first_path = next(adapter.iter_episode_paths(max_episodes_per_task=1))
        sample = adapter.load_sample(first_path, 0, decode_images=True)
        result["sample"] = {
            "sample_id": sample.sample_id,
            "task": sample.task,
            "episode_index": sample.episode_index,
            "proprio_shape": list(sample.proprio.shape),
            "action_chunk_shape": list(sample.action_chunk.shape),
            "valid_actions": int(sample.action_valid_mask.sum()),
            "image_shapes": {name: list(image.shape) for name, image in sample.images.items()},
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

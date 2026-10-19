#!/usr/bin/env python3
"""Validate all Spatial shards and freeze episode-disjoint temporal samples."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from cti_vla.data.identity import file_set_signature
from cti_vla.data.libero import assert_episode_disjoint, build_stage_covered_manifest, save_manifest, split_episodes
from cti_vla.data.sequence_example import discover_episodes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-directory", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--samples-per-episode", type=int, default=3)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    paths = sorted(args.data_directory.glob("libero_spatial-train.tfrecord-*-of-00016"))
    if len(paths) != 16:
        raise ValueError("Require all 16 pinned Spatial shards before freezing suite splits")
    args.output_directory.mkdir(parents=True, exist_ok=True)
    outputs = [args.output_directory / f"{name}.json" for name in ("train", "validation", "test", "summary")]
    if any(path.exists() for path in outputs):
        raise FileExistsError("Split outputs already exist; choose a new versioned output directory")
    source = file_set_signature(paths, namespace="cti-vla:libero-source:v1")
    episodes = discover_episodes(paths)
    if len(episodes) != 432:
        raise ValueError(f"Expected 432 Spatial episodes; found {len(episodes)}")
    if len({episode.task_name for episode in episodes}) != 10:
        raise ValueError("Expected all 10 Spatial task instructions")
    manifests = [build_stage_covered_manifest(
        values, split=name, source_signature=source,
        samples_per_episode=args.samples_per_episode, seed=args.seed,
    ) for name, values in split_episodes(episodes, seed=args.seed).items()]
    assert_episode_disjoint(*manifests)
    summary = {"dataset": "libero_spatial_no_noops", "source_signature": source,
               "source_episode_count": len(episodes), "source_task_count": 10,
               "seed": args.seed, "phase_definition": "temporal thirds, not semantic phases",
               "purpose": "offline teacher/selector development; closed-loop evaluation uses held-out simulator initial states",
               "splits": {}}
    for manifest in manifests:
        save_manifest(args.output_directory / f"{manifest.split}.json", manifest)
        summary["splits"][manifest.split] = {
            "episodes": manifest.episode_count, "observations": manifest.sample_count,
            "stages": dict(Counter(sample.stage for sample in manifest.samples)),
            "task_episode_counts": dict(Counter(episode.task_name for episode in manifest.episodes)),
        }
    (args.output_directory / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

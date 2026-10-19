"""CPU-only formal image preparation for preregistering legal D1 pairs.

This produces review images and receipts, not an approved pair manifest. The
formal cropped images must be visually reviewed before admitting each pair.
"""
from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path

import numpy as np
from PIL import Image


def run(args):
    from cti_vla.data.experiment_protocol import load_experiment_protocol, write_frozen_json
    from cti_vla.data.identity import file_sha256
    from cti_vla.data.sequence_example import iter_libero_examples
    from cti_vla.evaluation.libero_runtime import INPUTS_VERSION, load_official_reference_functions, process_camera
    import cti_vla.evaluation.libero_runtime as runtime
    import hashlib
    protocol = load_experiment_protocol(args.protocol)
    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    if len(candidates) > 10 or len({row["sample_id"] for row in candidates}) != len(candidates):
        raise ValueError("D1 candidate panel must contain at most ten unique samples")
    reference = load_official_reference_functions(args.official_source)
    args.output.mkdir(parents=True, exist_ok=True)
    prepared = []
    for candidate in candidates:
        ref, sample = protocol.require_sample(candidate["episode_id"], candidate["step_index"], split="train")
        if sample.sample_id != candidate["sample_id"] or sample.stage != "early" or sample.step_index != 0:
            raise ValueError("D1 visual review is restricted to registered early train step-zero candidates")
        if ref.source_shard != candidate["source_shard"] or ref.record_index != candidate["record_index"]:
            raise ValueError("candidate storage location differs from the frozen manifest")
        episode = next(row for row in iter_libero_examples(args.data_directory / ref.source_shard) if row.record_index == ref.record_index)
        if episode.episode_id != ref.episode_id or episode.instructions[sample.step_index] != candidate["instruction"]:
            raise ValueError("decoded candidate content/instruction mismatch")
        views = {}
        for name, encoded in (("main", episode.images[sample.step_index]), ("wrist", episode.wrist_images[sample.step_index])):
            if hashlib.sha256(encoded).hexdigest() != candidate["views"][name]["sha256"]:
                raise ValueError("raw camera bytes differ from the predeclared candidate")
            with Image.open(BytesIO(encoded)) as image:
                raw = np.asarray(image.convert("RGB"))
            actual = process_camera(raw, already_rotated=True)
            expected = reference["center_crop_image"](reference["resize_image_for_policy"](raw, 224))
            if not np.array_equal(actual, expected):
                raise ValueError("formal D1 pixels differ from pinned official reference")
            filename = f"{sample.sample_id}_{name}.png"
            stream = BytesIO()
            actual.save(stream, format="PNG")
            data = stream.getvalue()
            destination = args.output / filename
            if destination.exists() and destination.read_bytes() != data:
                raise FileExistsError("refusing to replace a different formal review image")
            destination.write_bytes(data)
            views[name] = {"file": filename, "png_sha256": hashlib.sha256(data).hexdigest(),
                           "rgb_sha256": hashlib.sha256(np.ascontiguousarray(actual).tobytes()).hexdigest(),
                           "shape": list(np.asarray(actual).shape), "raw_jpeg_sha256": hashlib.sha256(encoded).hexdigest(),
                           "official_reference_equal": True}
        prepared.append({**{key: candidate[key] for key in ("sample_id", "episode_id", "step_index", "instruction", "source_shard", "record_index")},
                         "split": "train", "views": views,
                         "raw_proprio_sha256": hashlib.sha256(np.asarray(episode.proprio[sample.step_index], dtype="<f4").tobytes()).hexdigest()})
    report = {"schema_version": 1, "status": "awaiting_visual_review", "formal_d1_queries": 0,
              "input_version": INPUTS_VERSION, "runtime_sha256": file_sha256(runtime.__file__),
              "candidate_registry_sha256": file_sha256(args.candidates), "protocol_signature": protocol.payload["content_signature"],
              "observations": prepared}
    write_frozen_json(args.output / "prepared_images.json", report)
    return {"status": report["status"], "observations": len(prepared), "output": str(args.output)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--data-directory", type=Path, required=True)
    parser.add_argument("--official-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(run(parser.parse_args())), flush=True)

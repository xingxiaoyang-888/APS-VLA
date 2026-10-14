"""Recompute latency summaries from finalized complete raw-input measurements."""
import argparse
import json
from pathlib import Path

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation.profiling import verify_measurement_journal, summarize_latencies
from cti_vla.evaluation.teacher_diagnostics import atomic_json

ROOT = Path(__file__).resolve().parents[1]


def run(args):
    source = args.measurements.resolve()
    project_root, target = args.project_root.resolve(), args.output.resolve()
    if source.parent in target.parents or project_root not in target.parents or (project_root != ROOT.resolve() and ROOT.resolve() in target.parents):
        raise ValueError("analysis must be inside the project and outside the finalized run/source snapshot")
    receipt = json.loads((source.parent / "summary.json").read_text(encoding="utf-8"))
    if receipt.get("checkpoint_unchanged") is not True or receipt.get("measurements_sha256") != file_sha256(source) or receipt.get("journal_sha256") != file_sha256(source.parent / "calls.jsonl"):
        raise ValueError("measurements lack matching immutable-checkpoint finalization")
    data = json.loads(source.read_text(encoding="utf-8"))
    cost = verify_measurement_journal(data, source.parent / "calls.jsonl")
    if data.get("status") != "completed_measurement" or data.get("checkpoint_unchanged") is not True:
        raise ValueError("cannot analyze incomplete or failed primary measurement runs")
    result = summarize_latencies(data, bootstrap_repeats=args.bootstrap_repeats, seed=args.bootstrap_seed)
    result.update(source_measurements_sha256=file_sha256(source), cost=cost)
    atomic_json(args.output, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measurements", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--bootstrap-repeats", type=int, default=2000)
    parser.add_argument("--bootstrap-seed", type=int, default=1117)
    result = run(parser.parse_args())
    print(json.dumps({"status": result["status"], "synthetic": result["synthetic"]}))

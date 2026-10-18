"""Read-only complete17/23/41 Long analysis; reuse dense once, count new jobs once."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def single_analyzer():
    spec = importlib.util.spec_from_file_location("long_seed_single_analysis", ROOT / "scripts/analyze_g1_future.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(args):
    from cti_vla.data.long_initial_states import load_long_development_panel
    from cti_vla.data.long_future_windows import load_long_future_protocol, load_future_windows
    from cti_vla.evaluation.future_dense_reuse import load_dense_reference, require_dense_compatibility, SOURCE_FILES
    from cti_vla.evaluation.future_multiseed import summarize_seed_vectors
    from cti_vla.evaluation.future_runtime import _validate_receipt
    a = single_analyzer()
    evidence = a.Evidence()
    project = args.project_root.resolve()
    reg = evidence.read(args.registration)
    if (reg.get("schema") != "g1_future_long_multiseed_v1" or reg.get("all_training_seeds") != [17, 23, 41]
            or reg.get("new_training_seeds") != [23, 41] or reg["analysis"]["bootstrap_repeats"] != 2000
            or reg["analysis"]["bootstrap_seed"] != 1517):
        raise ValueError("analysis requires the fixed complete three-seed registration")
    for relative, digest in reg["frozen_evidence_sha256"].items():
        if a.digest(project / relative) != digest:
            raise ValueError("registered parent evidence changed: " + relative)
        evidence.files[str((project / relative).resolve())] = digest
    panel_path = project / reg["evaluation"]["panel"]
    panel = load_long_development_panel(panel_path)
    dense_path = project / reg["evaluation"]["dense_reference"]
    reference = load_dense_reference(dense_path, panel)
    for name in SOURCE_FILES:
        evidence.files[str((dense_path / name).resolve())] = a.digest(dense_path / name)
    windows_path = project / "configs/manifests/long_future_v1/windows.json"
    protocol = load_long_future_protocol(project / "configs/manifests/long_future_v1/protocol.json")
    windows = load_future_windows(windows_path, protocol)
    parent_config = evidence.read(project / reg["parent_config"])
    per_seed, offline, costs, initial_hashes, pending = {}, {}, {}, {}, []
    for seed in (17, 23, 41):
        if seed == 17:
            config, run_root = parent_config, dense_path.parent
        else:
            entry = reg["new_configs"][str(seed)]
            if a.digest(project / entry["path"]) != entry["sha256"]:
                raise ValueError("registered seed config changed")
            config, run_root = evidence.read(project / entry["path"]), project / entry["result_root"]
            if config.get("seed") != seed or {k: v for k, v in config.items() if k not in ("seed", "run_id")} != {k: v for k, v in parent_config.items() if k not in ("seed", "run_id")}:
                raise ValueError("new training configuration changed beyond seed/run_id")
        training, reports = a.analyze_training(run_root / "training", windows, a.digest(windows_path), config, evidence)
        closed = a.analyze_closed_loop(run_root / "closed_loop", reports, evidence,
            suite="libero_10", panel_path=panel_path)
        offline[str(seed)] = training
        if training["status"] != "analyzed" or closed["status"] != "analyzed":
            pending.append(seed)
            continue
        loop_config = evidence.read(run_root / "closed_loop/config.json")
        require_dense_compatibility(reference, panel, loop_config)
        if seed != 17 and (loop_config.get("training_seed") != seed or loop_config.get("methods") != ["future_A", "future_B"]
                or loop_config.get("dense_reference") != reference):
            raise ValueError("new seed must have60 A/B-only trials bound to the original dense reference")
        for arm in ("A", "B"):
            receipt = evidence.read(run_root / f"training/{arm}/deployment_receipt.json")
            _validate_receipt(receipt, receipt["metadata"])
            if (receipt["pair_config"] != config or receipt["metadata"]["seed"] != seed
                    or receipt["checkpoint_sha256"] != reports[arm]["best_checkpoint_sha256"]
                    or receipt["metadata_sha256"] != a.signature(receipt["metadata"])
                    or loop_config["selectors"][arm]["deployment_receipt_sha256"] != a.signature(receipt)):
                raise ValueError("seed training/checkpoint/deployment receipt identity mismatch")
        initial_hashes[seed] = reports["A"]["initial_scorer_sha256"]
        per_seed[seed] = closed
        if seed != 17:
            files = [run_root / "training" / rel for rel in ("cost_events.jsonl", "A/cost_events.jsonl", "B/cost_events.jsonl")]
            costs[str(seed)] = {"event_files": [a.analyze_cost_events(p, evidence) for p in files if p.exists()],
                "missing_event_files": [str(p) for p in files if not p.exists()],
                "validation_completed_seconds_lower_bound": {arm: training["arms"][arm]["validation_completed_seconds_lower_bound"] for arm in ("A", "B")},
                "closed_loop": closed["cost"], "parent_cache_and_dense_cost_added": False}
    if len(initial_hashes) == 3 and len(set(initial_hashes.values())) != 3:
        raise ValueError("fresh training seeds unexpectedly share the same initial DIE")
    parent_jobs = {"2993273", "2993299", "2993307", "2993338"}
    registered_first_jobs = set()
    missing_submissions = []
    for seed in (23, 41):
        run_root = project / reg["new_configs"][str(seed)]["result_root"]
        for stage in ("train", "closed_loop"):
            path = run_root / f"submission_{stage}.json"
            if not path.exists():
                missing_submissions.append(str(path))
                continue
            submitted = evidence.read(path)
            if submitted.get("mode", submitted.get("scope")) != stage or submitted.get("training_seed") != seed:
                raise ValueError("new job submission identity differs from registered seed/stage")
            registered_first_jobs.add(str(submitted["job_id"]))
    accounted_jobs = set()
    for path in args.slurm_accounting:
        payload = evidence.read(path)
        for row in payload["jobs"]:
            if row.get("scope") not in ("train", "closed_loop") or row.get("training_seed") not in (23, 41):
                raise ValueError("new allocation accounting contains another experiment/seed")
            accounted_jobs.add(str(row["job_id"]))
    job_ids = tuple(args.new_job_id) if args.new_job_id else tuple(sorted(accounted_jobs | registered_first_jobs))
    if len(job_ids) != len(set(job_ids)) or parent_jobs.intersection(job_ids):
        raise ValueError("new-job accounting must not repeat parent allocations")
    if not accounted_jobs.issubset(job_ids) or not registered_first_jobs.issubset(job_ids):
        raise ValueError("accounting cannot omit failed/retried or registered allocations")
    allocation = a.analyze_slurm(args.slurm_accounting, evidence, job_ids=job_ids) if job_ids else {
        "status": "pending", "reason": "supply the complete explicit newly registered allocation IDs; parent jobs are never inferred"}
    if missing_submissions:
        allocation.update(registration_complete=False, allocated_gpu_hours_total=None)
    parent_accounting = a.analyze_slurm([dense_path.parent / "slurm_accounting.json"], evidence, job_ids=tuple(sorted(parent_jobs)))
    summary = {"stage": "G1-F_Long_three_seed_analysis", "status": "pending" if pending else "analyzed",
        "pending_seeds": pending, "offline_all_seeds": offline,
        "closed_loop": summarize_seed_vectors(panel, per_seed, reference) if not pending else {"status": "pending"},
        "new_costs": {"new_training_arms": 4, "new_training_seeds": [23, 41], "by_seed": costs,
            "allocated_gpu": allocation, "missing_submission_files": missing_submissions,
            "scope": "Only newly registered allocations, counted once. Parent cache, F00/F01 and dense costs are historical and not added. Nested event/episode durations must not be added to allocation totals."},
        "historical_parent_costs_excluded_from_new_total": parent_accounting,
        "test_opened": False, "expanded_experiments_authorized": False, "scientific_decision": "manual_review_required",
        "evidence_sha256": evidence.files, "analyzer_sha256": a.digest(__file__)}
    evidence.unchanged()
    output = args.output_directory.resolve()
    if project not in output.parents or any(str((output / name).resolve()) in evidence.files for name in ("summary.json", "report.md")):
        raise ValueError("analysis output must be separate project evidence")
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    lines = ["# Long 三训练 seed 开发结果", "", "状态：" + summary["status"] + "。三个训练 seed 为17、23、41；固定30个初态，dense参考仅30次。", ""]
    if not pending:
        lines += ["|训练seed|A成功/30|B成功/30|B−A|", "|---|---:|---:|---:|"]
        for seed, result in per_seed.items():
            lines.append(f"|{seed}|{result['methods']['future_A']['successes']}|{result['methods']['future_B']['successes']}|{100 * result['paired_B_minus_A']['mean']:.2f}个百分点|")
        contrast = summary["closed_loop"]["contrasts"]["B_minus_A"]
        lines += ["", f"B−A三seed均值：{100*contrast['mean']:.2f}个百分点；按task分层、完整初态seed向量重采样95%区间：{[round(100*x,2) for x in contrast['ci95_percentile']]}个百分点。",
            f"训练seed间样本SD：{100*contrast['training_seed_mean_sample_sd']:.2f}个百分点；范围：{[round(100*x,2) for x in contrast['training_seed_mean_range']]}个百分点。"]
    lines += ["", "同一初态跨seed重复不是独立初态；区间仅描述这3个训练seed和3个任务。保留全部seed、离线误差和token重合结果，不选择最好seed。新增GPU分配费用与嵌套计时分别报告，不重计父缓存或dense。不推断总体显著性，不授权扩大或test。"]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--registration", type=Path, default=ROOT / "configs/experiments/g1_future_long_multiseed_v1.json")
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--slurm-accounting", action="append", type=Path, default=[])
    parser.add_argument("--new-job-id", action="append", default=[])
    args = parser.parse_args()
    result = run(args)
    print(json.dumps({"status": result["status"], "pending_seeds": result["pending_seeds"]}))


if __name__ == "__main__":
    main()

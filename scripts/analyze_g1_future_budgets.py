"""Audit all Long64/128 seed evidence and measured complete-pipeline latency.

Reads nonweight artifacts only. No jobs, model loading, sealed data, source
mutation, or automatic C experiment are performed by this analysis.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEEDS = (17, 23, 41)


def single_analyzer():
    spec = importlib.util.spec_from_file_location("long_budget_single_analysis", ROOT / "scripts/analyze_g1_future.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require_deployed_budget(config, events, budget, reference, training_seed):
    from cti_vla.evaluation.future_runtime import future_budget
    if future_budget(config) * 2 != budget or any(
            future_budget(config["selectors"][arm]) * 2 != budget
            or config["selectors"][arm]["seed"] != training_seed for arm in ("A", "B")):
        raise ValueError("closed-loop budget/seed differs from its actual trained selectors")
    if budget == 64 and (config.get("methods") != ["future_A", "future_B"]
            or config.get("training_seed") != training_seed or config.get("dense_reference") != reference
            or not config.get("budget_reuse_registration_sha256")):
        raise ValueError("new64 requires60 A/B-only trials and explicit original-dense/new-budget binding")
    initial = {row["state_trial_id"]: row["initial_observation_sha256"] for row in reference["dense_results"]}
    count = 0
    for event in events:
        if event.get("event") != "result" or event.get("method") not in ("future_A", "future_B"):
            continue
        chunks = event.get("chunks", [])
        if chunks and chunks[0]["observation_sha256"] != initial[event["state_trial_id"]]:
            raise ValueError("paired closed loop starts from a different raw observation")
        for chunk in chunks:
            meta = chunk["metadata"]
            indices = meta.get("retained_indices", [])
            arm = event["method"][-1]
            if (meta.get("visual_tokens") != budget or meta.get("per_camera_budgets") != [budget // 2] * 2
                    or any(meta.get(k) != 1 for k in ("policy_calls", "vision_calls", "scorer_calls"))
                    or meta.get("future_head_calls") != 0 or meta.get("language_cache") != "disabled"
                    or meta.get("selector_checkpoint_sha256") != config["selectors"][arm]["selector_checkpoint_sha256"]
                    or len(indices) != budget or indices != sorted(set(indices))
                    or any(type(i) is not int or not 0 <= i < 512 for i in indices)
                    or sum(i < 256 for i in indices) != budget // 2):
                raise ValueError("rollout chunk violates trained hard budget/one-forward/no-future deployment")
            count += 1
    return {"verified_policy_chunks": count, "visual_tokens": budget,
        "initial_observation_matches_original_dense": True, "future_head_calls": 0}


def tradeoff_diagnostics(closed, latency):
    if closed.get("status") == "pending":
        return {"status": "pending_closed_loop", "C_execution_authorized": False}
    decisions = {"status": "conditional_development_diagnostics", "C_execution_authorized": False,
        "same_budget": {}, "strict_B64_over_A128": None, "manual_review_required": True}
    families = {r["method_family"]: r for r in latency.get("seed_equal_weight_summaries", [])}
    for budget in (64, 128):
        contrast = closed["contrasts"][f"B{budget}_minus_A{budget}"]
        row = {"paired_success_mean": contrast["mean"], "conditional_ci95": contrast["ci95_percentile"],
            "positive_success_with_lower_bound_above_zero": contrast["mean"] > 0 and contrast["ci95_percentile"][0] > 0}
        if families:
            a, b = families[f"A{budget}"], families[f"B{budget}"]
            row.update(mean_seed_median_B_minus_A_ms=b["mean_of_seed_medians_ms"] - a["mean_of_seed_medians_ms"],
                mean_seed_p95_B_minus_A_ms=b["mean_of_seed_p95_ms"] - a["mean_of_seed_p95_ms"])
        decisions["same_budget"][str(budget)] = row
    contrast = closed["contrasts"]["B64_minus_A128"]
    decisions["B64_over_A128_success"] = {"mean": contrast["mean"], "conditional_ci95": contrast["ci95_percentile"]}
    if families:
        a, b = families["A128"], families["B64"]
        decisions.update(strict_B64_over_A128=contrast["mean"] > 0 and contrast["ci95_percentile"][0] > 0
            and b["mean_of_seed_medians_ms"] < a["mean_of_seed_medians_ms"]
            and b["mean_of_seed_p95_ms"] < a["mean_of_seed_p95_ms"],
            B64_over_A128_latency={"aggregation": "equal-weight mean of3seed medians and of3seed p95 values",
                "median_ratio_A128_over_B64": a["mean_of_seed_medians_ms"] / b["mean_of_seed_medians_ms"],
                "p95_ratio_A128_over_B64": a["mean_of_seed_p95_ms"] / b["mean_of_seed_p95_ms"]})
    else:
        decisions["latency_status"] = "pending; token count alone cannot establish acceleration"
    decisions["limits"] = "Conditional fixed-development diagnostics only. Failure to meet the strict rule is not equivalence; no future-prediction/task-difficulty causal claim and no automatic C run."
    return decisions


def run(args):
    from cti_vla.data.long_initial_states import load_long_development_panel
    from cti_vla.data.long_future_windows import load_long_future_protocol, load_future_windows
    from cti_vla.evaluation.future_dense_reuse import load_dense_reference, require_dense_compatibility, SOURCE_FILES
    from cti_vla.evaluation.future_budget_comparison import summarize_budget_comparison
    from cti_vla.evaluation.future_runtime import _metadata, _validate_receipt, future_budget
    a, project = single_analyzer(), args.project_root.resolve()
    evidence = a.Evidence()
    reg = evidence.read(args.registration)
    if (reg.get("schema") != "g1_future_long_k64_v1" or reg.get("training_seeds") != list(SEEDS)
            or reg["analysis"]["bootstrap_repeats"] != 2000 or reg["analysis"]["bootstrap_seed"] != 1517
            or reg["evaluation"]["total_new_AB_trials"] != 180 or reg["stop"]["C_execution_authorized"] is not False):
        raise ValueError("requires complete preregistered64-token Long three-seed experiment")
    for relative, digest in reg["frozen_evidence_sha256"].items():
        path = project / relative
        if a.digest(path) != digest:
            raise ValueError("registered historical evidence changed: " + relative)
        evidence.files[str(path.resolve())] = digest
    parent_config = evidence.read(project / reg["parent_config"])
    panel_path = project / reg["evaluation"]["panel"]
    panel = load_long_development_panel(panel_path)
    dense_path = project / reg["evaluation"]["reuse_dense_reference"]
    reference = load_dense_reference(dense_path, panel)
    for name in SOURCE_FILES:
        evidence.files[str((dense_path / name).resolve())] = a.digest(dense_path / name)
    windows_path = project / "configs/manifests/long_future_v1/windows.json"
    protocol = load_long_future_protocol(project / "configs/manifests/long_future_v1/protocol.json")
    windows = load_future_windows(windows_path, protocol)
    closed, offline, initial, costs, pending, deployment, checkpoints = {64: {}, 128: {}}, {}, {}, {}, [], {}, {}
    for budget in (128, 64):
        offline[str(budget)] = {}
        initial[budget] = {}
        for seed in SEEDS:
            if budget == 128:
                run_root = project / reg["evaluation"]["reuse128_roots"][str(seed)]
                config = evidence.read(run_root / "training/A/deployment_receipt.json")["pair_config"]
            else:
                entry = reg["new_configs"][str(seed)]
                if a.digest(project / entry["path"]) != entry["sha256"]:
                    raise ValueError("new seed configuration changed")
                config, run_root = evidence.read(project / entry["path"]), project / entry["result_root"]
            allowed = {"seed", "run_id", "tokens_per_camera"}
            if (config.get("seed") != seed or config.get("tokens_per_camera") != budget // 2
                    or {k: v for k, v in config.items() if k not in allowed} != {k: v for k, v in parent_config.items() if k not in allowed}):
                raise ValueError("training changed beyond registered seed/run_id/budget")
            training, reports = a.analyze_training(run_root / "training", windows, a.digest(windows_path), config, evidence)
            loop = a.analyze_closed_loop(run_root / "closed_loop", reports, evidence, suite="libero_10", panel_path=panel_path)
            offline[str(budget)][str(seed)] = training
            if training["status"] != "analyzed" or loop["status"] != "analyzed":
                pending.append({"budget": budget, "seed": seed, "training_status": training["status"], "closed_loop_status": loop["status"]})
                continue
            loop_config = evidence.read(run_root / "closed_loop/config.json")
            require_dense_compatibility(reference, panel, loop_config)
            events, partial = evidence.lines(run_root / "closed_loop/trials.jsonl")
            if partial:
                raise ValueError("finalized trial ledger cannot have a partial tail")
            deployment[f"{budget}_seed{seed}"] = require_deployed_budget(loop_config, events, budget, reference, seed)
            for arm in ("A", "B"):
                receipt = evidence.read(run_root / f"training/{arm}/deployment_receipt.json")
                metadata = _metadata(receipt["metadata"])
                _validate_receipt(receipt, metadata)
                if (receipt["pair_config"] != config or metadata["seed"] != seed or future_budget(metadata) * 2 != budget
                        or receipt["checkpoint_sha256"] != reports[arm]["best_checkpoint_sha256"]
                        or loop_config["selectors"][arm]["deployment_receipt_sha256"] != a.signature(receipt)):
                    raise ValueError("trained budget/checkpoint/receipt/closed-loop binding differs")
                checkpoints[f"{arm}{budget}_seed{seed}"] = receipt["checkpoint_sha256"]
            initial[budget][seed] = reports["A"]["initial_scorer_sha256"]
            closed[budget][seed] = loop
            if budget == 64:
                event_paths = [run_root / "training" / rel for rel in ("cost_events.jsonl", "A/cost_events.jsonl", "B/cost_events.jsonl")]
                costs[str(seed)] = {"training_events": [a.analyze_cost_events(p, evidence) for p in event_paths if p.exists()],
                    "closed_loop": loop["cost"], "nested_costs_are_not_added_to_allocation": True}
        if len(initial[budget]) == 3 and len(set(initial[budget].values())) != 3:
            raise ValueError("distinct training seeds must use distinct fresh DIE initializations")
    result = summarize_budget_comparison(panel, closed, reference) if not pending else {"status": "pending"}
    latency = {"status": "pending", "reason": "matched complete Long latency not supplied"}
    if args.latency_directory is not None:
        from cti_vla.evaluation.future_long_profiling import analyze_long_profile
        for path in args.latency_directory.glob("*"):
            if path.is_file() and path.suffix in (".json", ".jsonl"):
                evidence.files[str(path.resolve())] = a.digest(path)
        required = ("config.json", "measurements.json", "summary.json", "calls.jsonl")
        missing = [str(args.latency_directory / name) for name in required if not (args.latency_directory / name).is_file()]
        latency = ({"status": "pending", "missing": missing} if missing
            else analyze_long_profile(args.latency_directory, reg))
        # The profiler binds receipt identities internally; also bind its exact
        # instantiated checkpoints to the6 paired success experiments here.
        measured_path = args.latency_directory / "measurements.json"
        if measured_path.is_file() and latency.get("status") == "completed_latency_analysis":
            measured = evidence.read(measured_path)
            for method, expected in checkpoints.items():
                identity = measured["methods"][method]
                provenance = identity.get("provenance", identity)
                actual = provenance.get("selector", provenance).get("selector_checkpoint_sha256")
                if actual != expected:
                    raise ValueError("latency used a different checkpoint from closed-loop comparison: " + method)
    accounting_paths = args.slurm_accounting
    accounted = set()
    for path in accounting_paths:
        payload = evidence.read(path)
        for row in payload["jobs"]:
            if row.get("scope") not in ("acceptance", "train", "closed_loop", "profiling", "profile", "latency", "collection", "collect"):
                raise ValueError("new allocation contains an unrelated scope")
            accounted.add(str(row["job_id"]))
    submitted = set()
    round_root = project / "results/g1_future_long_k64_v1"
    for path in round_root.rglob("submission_*.json"):
        submitted.add(str(evidence.read(path)["job_id"]))
    job_ids = tuple(args.new_job_id) if args.new_job_id else tuple(sorted(accounted | submitted))
    historical_ids = {"2993273", "2993299", "2993307", "2993338", "2993590", "2993591", "2993645", "2993646"}
    if (len(job_ids) != len(set(job_ids)) or historical_ids.intersection(job_ids)
            or not accounted.issubset(job_ids) or not submitted.issubset(job_ids)):
        raise ValueError("new GPU cost cannot omit failed/registered jobs or recount historical allocations")
    allocation = a.analyze_slurm(accounting_paths, evidence, job_ids=job_ids)
    summary = {"stage": "G1-F_Long64_vs128", "status": "pending" if pending else "closed_loop_analyzed",
        "pending_runs": pending, "closed_loop": result, "offline_all_budgets": offline,
        "deployment_audits": deployment, "latency": latency, "tradeoff_diagnostics": tradeoff_diagnostics(result, latency),
        "new_costs": {"new_training_arms": 6, "new_closed_loop_trials": 180, "by_seed": costs, "allocated_gpu": allocation,
            "historical_gpu_seconds_excluded": reg["cost"]["parent128_cost_gpu_seconds"],
            "scope": "Count each new allocated GPU-second once, including acceptance,train,validation,collection,rollouts,profiling,failures,retries. Do not add nested timings."},
        "test_opened": False, "automatic_C_execution": False, "evidence_sha256": evidence.files,
        "analyzer_sha256": a.digest(__file__), "scientific_decision": "manual_review_required"}
    if not pending and latency.get("status") == "completed_latency_analysis" and allocation.get("allocated_gpu_hours_total") is not None:
        summary["status"] = "analyzed"
    evidence.unchanged()
    output = args.output_directory.resolve()
    if project not in output.parents or any(str((output / name).resolve()) in evidence.files for name in ("summary.json", "report.md")):
        raise ValueError("analysis output must be separate project evidence")
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    lines = ["# Long64/128三种子比较", "", "状态：" + summary["status"] + "。固定30个唯一开发初态；所有seed17/23/41保留。", ""]
    if not pending:
        lines += ["|方法|seed17|seed23|seed41|均值|", "|---|---:|---:|---:|---:|"]
        for method, values in result["methods"].items():
            cells = [f"{values['per_seed'][str(s)]['successes']}/30" for s in SEEDS]
            lines.append("|" + "|".join([method, *cells, f"{100*values['equal_seed_mean']['mean']:.2f}%"]) + "|")
        lines += [f"", f"Dense参考：{result['dense']['successes']}/30；仅复用原30次结果。"]
        for key in ("B64_minus_A64", "B128_minus_A128", "B64_minus_A128"):
            r = result["contrasts"][key]
            lines.append(f"{key}：{100*r['mean']:.2f}个百分点，条件95%区间{[round(100*x,2) for x in r['ci95_percentile']]}。")
    lines += ["", "区间仅描述固定任务、初态与3seed；同一初态跨seed重复不视为独立初态。不显著不等于等价，token减少不等于实测加速。完整逐任务/种子动作误差、token重合、延迟和分配成本见summary.json。C仅候选，不自动运行，test封存。"]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--registration", type=Path, default=ROOT / "configs/experiments/g1_future_long_k64_v1.json")
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--latency-directory", type=Path)
    parser.add_argument("--slurm-accounting", action="append", type=Path, default=[])
    parser.add_argument("--new-job-id", action="append", default=[])
    result = run(parser.parse_args())
    print(json.dumps({"status": result["status"], "pending_runs": result["pending_runs"]}))


if __name__ == "__main__":
    main()

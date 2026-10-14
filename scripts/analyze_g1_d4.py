"""Recompute G1 diagnostics from finalized journals; never issues a go decision.

CPU-only, no model loading. The 90/12 panels and every action query are checked
before producing observation-level statistics and episode-cluster intervals.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from dataclasses import asdict
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import platform

import numpy as np
import torch

from cti_vla.data.experiment_protocol import load_experiment_protocol
from cti_vla.data.identity import file_sha256
from cti_vla.data.libero import load_manifest
from cti_vla.evaluation.teacher_diagnostics import (
    DIAGNOSTICS_VERSION, action_error, atomic_json, json_signature,
    read_query_journal_ledger, run_exact_selection, run_intervention_panel,
    run_repeatability, tensor_signature,
)
from cti_vla.labeling.sampling import fixed_anchor_panel, named_seed

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_VERSION = "g1-journal-d4-episode-bootstrap-v1"
GROUP_KINDS = ("all", "task", "stage", "final_frame")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def assert_same(actual, expected, *, path="result", atol=1e-7):
    """Reject stale numeric summaries and changed selected token sets."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or actual.keys() != expected.keys():
            raise ValueError(f"{path}: result fields differ from recomputation")
        for key, value in expected.items():
            assert_same(actual[key], value, path=f"{path}.{key}", atol=atol)
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise ValueError(f"{path}: result lengths differ from recomputation")
        for index, value in enumerate(expected):
            assert_same(actual[index], value, path=f"{path}[{index}]", atol=atol)
    elif isinstance(expected, float):
        if isinstance(actual, bool) or not isinstance(actual, (int, float)) or not math.isfinite(actual) or not math.isclose(actual, expected, rel_tol=1e-6, abs_tol=atol):
            raise ValueError(f"{path}: stored value differs from journal recomputation")
    elif actual != expected or type(actual) is not type(expected):
        raise ValueError(f"{path}: stored identity differs from recomputation")


class JournalActions:
    """A read-only oracle: every requested action must already be in the log."""

    num_cameras = 2
    camera_size = 256
    full_indices = tuple(range(512))

    def __init__(self, path, *, config_sha, observation):
        self.ledger = read_query_journal_ledger(path, expected_fields={
            "config_sha256": config_sha, "sample": observation})
        events = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]
        self.identity = events[0]["identity"]
        if self.identity.get("num_cameras") != 2 or self.identity.get("action_shape") != [8, 7] or self.identity.get("diagnostics_version") != DIAGNOSTICS_VERSION:
            raise ValueError("journal does not describe the registered two-camera 8x7 diagnostic")
        starts, self.actions = {}, {}
        for event in events[1:]:
            if event["event"] == "start":
                retained = event["retained_indices"]
                if not retained or retained != sorted(set(retained)) or any(type(i) is not int or not 0 <= i < 512 for i in retained):
                    raise ValueError("journal retained indices are invalid")
                replacement = event["replace_index"]
                if replacement is not None and replacement not in retained:
                    raise ValueError("journal replacement lies outside S")
                key = json_signature({"retained": retained, "replace_index": replacement,
                                      "repeat_id": event["repeat_id"]})
                if key != event["key"] or event["physical_visual_tokens"] != len(retained):
                    raise ValueError("journal query key or sequence length is inconsistent")
                starts[event["call_id"]] = event
            elif event["event"] == "complete":
                value = torch.tensor(event["action"], dtype=torch.float32)
                if value.shape != (1, 8, 7) or not torch.isfinite(value).all() or event["action_sha256"] != tensor_signature({"action": value}):
                    raise ValueError("journal action checksum/shape is invalid")
                self.actions[starts[event["call_id"]]["key"]] = value

    def query(self, retained, *, category, replace_index=None, repeat_id=None):
        key = json_signature({"retained": list(retained), "replace_index": replace_index, "repeat_id": repeat_id})
        if key not in self.actions:
            raise ValueError(f"required {category} action is absent from the completed query journal")
        return self.actions[key].clone()


def verify_panel(directory, protocol):
    """Validate finalized files and authoritative panel membership, no writes."""
    directory = Path(directory)
    config, panel, receipt = (read_json(directory / name) for name in
                              ("config.json", "observation_panel.json", "finalization.json"))
    config_sha = json_signature(config)
    if config.get("stage") != "G1" or config.get("diagnostics_version") != DIAGNOSTICS_VERSION or config.get("protocol_signature") != protocol.payload["content_signature"] or config.get("panel_sha256") != json_signature(panel):
        raise ValueError("G1 config/panel/protocol mismatch")
    implementation = "src/cti_vla/evaluation/teacher_diagnostics.py"
    sampler = "src/cti_vla/labeling/sampling.py"
    if any(config.get("source_snapshot", {}).get(name) != file_sha256(ROOT / name) for name in (implementation, sampler)):
        raise ValueError("diagnostic or sampling implementation differs from the producer; use its pinned source to recompute")
    if receipt.get("status") != "verified" or receipt.get("config_sha256") != config_sha or receipt.get("checkpoint_unchanged") is not True:
        raise ValueError("D4 requires completed immutable-checkpoint finalization")
    asset_path = ROOT / "configs/assets/openvla_oft_libero_spatial.json"
    asset = read_json(asset_path)
    expected_checkpoint = {"repository": asset["repository"], "revision": asset["revision"],
                           "file_count": len(asset["files"]), "total_bytes": asset["total_bytes"]}
    if config.get("model_revision") != asset["revision"] or config.get("asset_manifest_sha256") != file_sha256(asset_path) or receipt.get("checkpoint_verification") != expected_checkpoint:
        raise ValueError("final checkpoint verification differs from the registered Spatial asset")
    refs = protocol.payload["panels"]
    diagnostic = load_manifest(protocol.path.parent / refs["diagnostic_90"]["path"])
    teacher = load_manifest(protocol.path.parent / refs["teacher_12"]["path"])
    expected = {s.sample_id: s for s in diagnostic.samples}
    exact_ids = {s.sample_id for s in teacher.samples}
    rows = panel["observations"]
    if len(rows) != 90 or len(expected) != 90 or len(exact_ids) != 12 or len({r["sample_id"] for r in rows}) != 90 or {r["sample_id"] for r in rows} != set(expected):
        raise ValueError("D4 requires exactly the complete frozen 90/12 panel")
    expected_names = {str(sample_id) for sample_id in expected}
    for folder, suffix in (("observations", "*.json"), ("queries", "*.jsonl")):
        if {path.stem for path in (directory / folder).glob(suffix)} != expected_names:
            raise ValueError("G1 run contains missing or unregistered observation/query files")
    if any(panel.get(f"{kind}_manifest_sha256") != refs[name]["sha256"] for kind, name in (("diagnostic", "diagnostic_90"), ("teacher", "teacher_12"))):
        raise ValueError("panel source manifest hashes differ")
    task_names = sorted({r["task_name"] for r in rows})
    repeat_ids = set()
    for index, task in enumerate(task_names):
        stage = ("early", "middle", "late")[index % 3]
        candidates = [r for r in rows if r["task_name"] == task and r["stage"] == stage]
        if not candidates:
            raise ValueError("panel lacks registered task/stage coverage")
        repeat_ids.add(min(candidates, key=lambda r: named_seed(config["repeat_seed"], "repeat", r["sample_id"]))["sample_id"])
    observation_hashes, journal_hashes = {}, {}
    for row in rows:
        episode, sample = protocol.require_sample(row["episode_id"], row["step_index"], split="train")
        required = {**asdict(sample), "task_name": episode.task_name, "source_shard": episode.source_shard,
                    "record_index": episode.record_index, "is_last_step": sample.step_index == episode.num_steps - 1,
                    "exact_selection": sample.sample_id in exact_ids, "repeatability": sample.sample_id in repeat_ids}
        if row != required or sample != expected[sample.sample_id]:
            raise ValueError("G1 row differs from the authoritative registered train observation")
        key = str(sample.sample_id)
        observation_hashes[key] = file_sha256(directory / "observations" / f"{key}.json")
        journal_hashes[key] = file_sha256(directory / "queries" / f"{key}.jsonl")
    if receipt.get("observation_files") != observation_hashes or receipt.get("query_journals") != journal_hashes:
        raise ValueError("finalization no longer binds every observation and query journal")
    return config, rows, {"config_sha256": config_sha,
                          "finalization_sha256": file_sha256(directory / "finalization.json"),
                          "panel_sha256": file_sha256(directory / "observation_panel.json"),
                          "observation_files": observation_hashes, "query_journals": journal_hashes}


def error_metrics(error):
    result = {key: error[key] for key in ("mean_l1", "position_mean_l1", "rotation_mean_l1", "gripper_mean_l1")}
    result.update({f"action_dim_{i}": value for i, value in enumerate(error["by_action_dimension"])})
    result.update({f"chunk_step_{i}": value for i, value in enumerate(error["by_chunk_step"])})
    return result


def append_metrics(target, observation, family, variant, keep_count, values):
    meta = {name: observation[name] for name in ("sample_id", "episode_id", "task_name", "stage", "is_last_step")}
    for metric, value in values.items():
        target.append({**meta, "family": family, "variant": variant, "keep_count": keep_count,
                       "metric": metric, "value": value})


def comparison_metrics(value):
    return {"spearman": value["spearman"], "mean_absolute_label_difference": value["mean_absolute_label_difference"],
            "sign_flip_fraction_outside_noise": value["sign_flips_outside_noise"] / value["sign_comparison_count"] if value["sign_comparison_count"] else None,
            "reliable_sign_fraction": value["sign_comparison_count"] / value["candidate_count"]}


def observation_metrics(observation, interventions, exact, *, noise_tolerance):
    metrics, candidates = [], []
    for item in interventions["sets"]:
        name, count = item["name"], len(item["retained_indices"])
        append_metrics(metrics, observation, "D3", name, count, comparison_metrics(item["deletion_vs_replacement"]))
        if name in interventions["full_vs_partial_deletion"]:
            append_metrics(metrics, observation, "D2", name, count, comparison_metrics(interventions["full_vs_partial_deletion"][name]))
        for intervention, label_key, errors_key in (("deletion", "deletion_labels", "deleted_error"),
                                                     ("replacement", "replacement_labels", "replaced_error")):
            labels = np.asarray(item[label_key], dtype=np.float64)
            append_metrics(metrics, observation, "signed_labels", f"{name}:{intervention}", count,
                           {"mean_signed": float(labels.mean()), "mean_absolute": float(np.abs(labels).mean()),
                            "negative_fraction": float((labels < -noise_tolerance).mean()),
                            "positive_fraction": float((labels > noise_tolerance).mean()),
                            "within_noise_fraction": float((np.abs(labels) <= noise_tolerance).mean())})
            error_rows = [error_metrics(error) for error in item[errors_key]]
            append_metrics(metrics, observation, "intervention_action", f"{name}:{intervention}", count,
                           {key: sum(row[key] for row in error_rows) / len(error_rows) for key in error_rows[0]})
            for index, candidate in enumerate(item["candidate_indices"]):
                candidates.append({**{key: observation[key] for key in ("sample_id", "episode_id", "task_name", "stage", "is_last_step")},
                                   "set": name, "keep_count": count, "intervention": intervention, "candidate_index": candidate,
                                   "signed_label": float(labels[index]), "base_error": item["base_error"]["mean_l1"],
                                   "intervened_error": item[errors_key][index]["mean_l1"]})
    if exact is not None:
        methods = {name: {row["keep_count"]: error_metrics(row["error"]) for row in values}
                   for name, values in exact["methods"].items()}
        random_names = [f"random_seed_{seed}" for seed in exact["random_seeds"]]
        methods["random_mean"] = {count: {key: sum(methods[name][count][key] for name in random_names) / len(random_names)
                                          for key in methods[random_names[0]][count]} for count in methods["teacher_staged"]}
        for name, by_budget in methods.items():
            for count, errors in by_budget.items():
                append_metrics(metrics, observation, "selection_action", name, count, errors)
                if name != "teacher_staged":
                    append_metrics(metrics, observation, "teacher_paired_delta", name, count,
                                   {key: methods["teacher_staged"][count][key] - value for key, value in errors.items()})
    return metrics, candidates


@lru_cache(maxsize=64)
def _episode_draws(episodes, repeats, seed):
    rng = np.random.default_rng(named_seed(seed, "episode-bootstrap", *episodes))
    return rng.integers(0, len(episodes), size=(repeats, len(episodes)))


def clustered_interval(rows, *, repeats, seed):
    """Observation mean, resampling entire episodes (including all its phases).

    Repeated random seeds/candidates are reduced within observation upstream.
    Undefined correlations stay undefined and have a separate missing count.
    """
    valid = [row for row in rows if row["value"] is not None]
    episodes = sorted({row["episode_id"] for row in rows})
    counts = np.asarray([sum(row["episode_id"] == e for row in valid) for e in episodes], dtype=np.float64)
    sums = np.asarray([sum(row["value"] for row in valid if row["episode_id"] == e) for e in episodes], dtype=np.float64)
    finite = np.asarray([row["value"] for row in valid], dtype=np.float64)
    if not np.isfinite(finite).all():
        raise ValueError("nonfinite analysis metric")
    result = {"n_observations": len(rows), "n_defined": len(valid), "n_undefined": len(rows) - len(valid),
              "n_episodes": len(episodes), "n_episodes_with_defined_values": int((counts > 0).sum()),
              "mean": float(finite.mean()) if len(finite) else None,
              "median": float(np.median(finite)) if len(finite) else None,
              "p95": float(np.quantile(finite, .95)) if len(finite) else None,
              "ci95_low": None, "ci95_high": None, "valid_bootstrap_replicates": 0}
    if (counts > 0).sum() < 2:
        return result
    draws = _episode_draws(tuple(episodes), repeats, seed)
    denominator = counts[draws].sum(axis=1)
    numerator = sums[draws].sum(axis=1)
    samples = numerator[denominator > 0] / denominator[denominator > 0]
    result.update(ci95_low=float(np.quantile(samples, .025)), ci95_high=float(np.quantile(samples, .975)),
                  valid_bootstrap_replicates=len(samples))
    return result


def summarize(metrics, *, repeats=10000, seed=917):
    if repeats < 100 or repeats > 100000:
        raise ValueError("bootstrap repetitions must be in [100,100000]")
    groups = defaultdict(list)
    for row in metrics:
        base = tuple(row[key] for key in ("family", "variant", "keep_count", "metric"))
        for kind, value in (("all", "all"), ("task", row["task_name"]), ("stage", row["stage"]),
                            ("final_frame", "final" if row["is_last_step"] else "nonfinal")):
            groups[(*base, kind, value)].append(row)
    output = []
    for index, (key, rows) in enumerate(sorted(groups.items())):
        if len({row["sample_id"] for row in rows}) != len(rows):
            raise ValueError("candidate/seed pseudoreplication reached the observation-level summary")
        output.append(dict(zip(("family", "variant", "keep_count", "metric", "group_kind", "group"), key),
                           **clustered_interval(rows, repeats=repeats, seed=seed)))
        if (index + 1) % 2000 == 0:
            print(f"Summarized {index + 1}/{len(groups)} metric groups", flush=True)
    return output


def write_csv(path, rows):
    if not rows:
        raise ValueError("refusing an empty scientific output table")
    with Path(path).open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def make_figures(output, groups, *, synthetic=False):
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".local" / "matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "figure.dpi": 140, "savefig.dpi": 200, "pdf.fonttype": 42})
    files = []
    def save(fig, name):
        if synthetic:
            fig.text(.5, .01, "SYNTHETIC CPU TEST - not a research result", ha="center", color="darkred", fontsize=8)
        for extension in ("png", "pdf"):
            path = output / f"{name}.{extension}"
            fig.savefig(path, bbox_inches="tight")
            files.append(path.name)
        plt.close(fig)
    def heatmap(ax, rows, title, *, vmin=None, vmax=None, cmap="viridis"):
        variants = sorted({row["variant"] for row in rows})
        stages = ("early", "middle", "late")
        values = {(r["variant"], r["group"]): r["mean"] for r in rows}
        data = np.asarray([[np.nan if values.get((v, s)) is None else values[(v, s)] for s in stages] for v in variants])
        im = ax.imshow(data, aspect="auto", vmin=vmin, vmax=vmax, cmap=cmap)
        ax.set_xticks(range(3), stages)
        ax.set_yticks(range(len(variants)), variants)
        ax.set_title(title)
        for i in range(len(variants)):
            for j in range(3):
                ax.text(j, i, "undef." if np.isnan(data[i, j]) else f"{data[i, j]:.2f}", ha="center", va="center", color="black")
        ax.figure.colorbar(im, ax=ax, fraction=.04)
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.5), constrained_layout=True)
    for ax, family, title in zip(axes, ("D2", "D3"), ("D2: full vs subset deletion ranks", "D3: deletion vs replacement ranks")):
        heatmap(ax, [r for r in groups if r["family"] == family and r["metric"] == "spearman" and r["group_kind"] == "stage"], title, vmin=-1, vmax=1, cmap="coolwarm")
    fig.suptitle("Offline diagnostic mean Spearman; undefined ranks excluded and reported in CSV")
    save(fig, "d2_d3_stage_ranks")
    fig, ax = plt.subplots(figsize=(7.5, 4.2), constrained_layout=True)
    coverage = next(r for r in groups if r["family"] == "selection_action" and r["variant"] == "teacher_staged" and r["metric"] == "mean_l1" and r["keep_count"] == 64 and r["group_kind"] == "all")
    for name, offset in (("full_loo_static", -.12), ("uniform", 0), ("random_mean", .12)):
        rows = sorted([r for r in groups if r["family"] == "teacher_paired_delta" and r["variant"] == name and r["metric"] == "mean_l1" and r["group_kind"] == "all"], key=lambda r: -r["keep_count"])
        x = np.arange(len(rows)) + offset
        y = np.asarray([r["mean"] for r in rows])
        ax.scatter(x, y, label=name, s=22)
        for position, row in zip(x, rows):
            if row["ci95_low"] is not None:
                ax.vlines(position, row["ci95_low"], row["ci95_high"])
    ax.axhline(0, color="grey", linewidth=.8)
    ax.set_xticks(range(3), [256, 128, 64])
    ax.set_xlabel("Total retained visual tokens")
    ax.set_ylabel("Paired normalized L1: teacher - baseline (lower better)")
    ax.set_title(f"Teacher path: {coverage['n_observations']} observations / {coverage['n_episodes']} episode clusters\n95% episode bootstrap; exploratory, no automatic go")
    ax.legend(fontsize=8)
    save(fig, "teacher_paired_delta")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    for ax, prefix, count, label in ((axes[0], "action_dim_", 7, "Action dimension (0-2 position, 3-5 rotation, 6 gripper)"),
                                    (axes[1], "chunk_step_", 8, "Action chunk step")):
        for name in ("teacher_staged", "full_loo_static", "uniform", "random_mean"):
            lookup = {r["metric"]: r["mean"] for r in groups if r["family"] == "selection_action" and r["variant"] == name and r["keep_count"] == 64 and r["group_kind"] == "all"}
            ax.plot(range(count), [lookup[f"{prefix}{i}"] for i in range(count)], marker="o", markersize=3, label=name)
        ax.set_xlabel(label)
        ax.set_ylabel("Normalized absolute error vs full teacher")
        ax.set_title(f"K=64; descriptive means, {coverage['n_episodes']} episodes")
        ax.legend(fontsize=7)
    save(fig, "action_dimension_and_chunk")
    return files


def analyze(directory, output, *, protocol_path, repeats=10000, seed=917, figures=True):
    directory, output = Path(directory).resolve(), Path(output).resolve()
    if directory == output or directory in output.parents or output in directory.parents:
        raise ValueError("analysis must use a separate directory outside the immutable G1 run")
    if ROOT != output and ROOT not in output.parents:
        raise ValueError("analysis products must remain within the CTI-VLA project")
    protocol = load_experiment_protocol(protocol_path)
    config, rows, evidence = verify_panel(directory, protocol)
    metrics, candidates, costs, repeatability = [], [], [], []
    for index, row in enumerate(rows):
        result = read_json(directory / "observations" / f"{row['sample_id']}.json")
        if result.get("status") != "completed" or result.get("config_sha256") != evidence["config_sha256"] or result.get("observation") != row:
            raise ValueError("observation is incomplete or belongs to another input/config")
        oracle = JournalActions(directory / "queries" / f"{row['sample_id']}.jsonl", config_sha=evidence["config_sha256"], observation=row)
        fixed = fixed_anchor_panel(row["sample_id"], seed=config["set_seed"])
        interventions = run_intervention_panel(oracle, fixed, noise_tolerance=config["noise_tolerance"])
        assert_same(result["interventions"], interventions, path=f"{row['sample_id']}.interventions")
        exact = None
        if row["exact_selection"]:
            exact = run_exact_selection(oracle, sample_id=row["sample_id"], seed=config["set_seed"], random_seeds=tuple(config["random_seeds"]))
            assert_same(result.get("exact_selection"), exact, path=f"{row['sample_id']}.exact")
        elif "exact_selection" in result:
            raise ValueError("unregistered teacher selection result")
        if row["repeatability"]:
            repeated = run_repeatability(oracle, fixed[0].candidate_indices[0])
            assert_same(result.get("repeatability"), repeated, path=f"{row['sample_id']}.repeatability")
            repeatability.append({"sample_id": row["sample_id"], **repeated})
        values, labels = observation_metrics(row, interventions, exact, noise_tolerance=config["noise_tolerance"])
        metrics.extend(values)
        candidates.extend(labels)
        costs.append(oracle.ledger)
        if (index + 1) % 10 == 0:
            print(f"Recomputed {index + 1}/90 observations from existing CPU journals", flush=True)
    print("Computing episode-cluster bootstrap summaries", flush=True)
    groups = summarize(metrics, repeats=repeats, seed=seed)
    cost_keys = ("sample_forwards_attempted", "sample_forwards_completed", "failed_calls", "interrupted_calls_unknown_completion", "cache_hits", "known_policy_seconds")
    cost = {key: sum(item[key] for item in costs) for key in cost_keys}
    cost["policy_seconds_total"] = None if cost["interrupted_calls_unknown_completion"] else cost["known_policy_seconds"]
    coverage = {"diagnostic_observations": len(rows), "diagnostic_episodes": len({r["episode_id"] for r in rows}),
                "diagnostic_tasks": len({r["task_name"] for r in rows}), "teacher_observations": sum(r["exact_selection"] for r in rows),
                "teacher_episodes": len({r["episode_id"] for r in rows if r["exact_selection"]}),
                "teacher_tasks": len({r["task_name"] for r in rows if r["exact_selection"]}),
                "late_equals_final_frame": all((r["stage"] == "late") == r["is_last_step"] for r in rows)}
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "observation_metrics.csv", metrics)
    write_csv(output / "candidate_labels.csv", candidates)
    write_csv(output / "grouped_metrics.csv", groups)
    products = make_figures(output, groups) if figures else []
    summary = {"analysis_version": ANALYSIS_VERSION, "status": "completed_offline_analysis", "gpu_calls": 0,
               "runtime": {"python": platform.python_version(), "torch": torch.__version__, "numpy": np.__version__},
               "go_no_go": "not_decided_requires_scientific_review", "source_directory": str(directory),
               "source_evidence": evidence, "script_sha256": file_sha256(__file__), "coverage": coverage,
               "bootstrap": {"unit": "episode", "repetitions": repeats, "seed": seed, "interval": "percentile 95%",
                             "estimate": "observation mean; resample entire episode clusters within each reported group",
                             "multiplicity": "pointwise exploratory intervals; no multiple-comparison correction or automatic significance decision",
                             "random_baseline": "average three preregistered random seeds within each observation; individual seeds also reported",
                             "undefined": "constant-label Spearman/sign comparison with no reliable candidates remains null; missing counts reported; no CI with fewer than two defined episode clusters"},
               "teacher_cost": cost, "repeatability": repeatability, "groups": groups,
               "limitations": ["Teacher selection has only four episode clusters (one per selected task); its intervals are exploratory and do not establish small gains or task generalization.",
                               "Late and final-frame groups coincide in the frozen panel; their effects cannot be disentangled. Final frame is not proof of a stationary state.",
                               "Candidate tokens, stages and random seeds are not independent replicates. Candidate statistics are averaged within observation before episode bootstrap.",
                               "D2/D3 and signed labels are offline teacher diagnostics; no closed-loop success, deployment latency or scientific go is inferred.",
                               "Teacher policy seconds exclude preprocessing, feature encoding, model loading and hard-kill overhead; reconcile complete costs from observation attempts and scheduler receipts."],
               "products": ["observation_metrics.csv", "candidate_labels.csv", "grouped_metrics.csv", *products]}
    atomic_json(output / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, default=ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")
    parser.add_argument("--bootstrap-repetitions", type=int, default=10000)
    parser.add_argument("--bootstrap-seed", type=int, default=917)
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args()
    summary = analyze(args.run_directory, args.output_directory, protocol_path=args.protocol,
                      repeats=args.bootstrap_repetitions, seed=args.bootstrap_seed, figures=not args.no_figures)
    print(json.dumps({key: summary[key] for key in ("status", "gpu_calls", "go_no_go", "coverage")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

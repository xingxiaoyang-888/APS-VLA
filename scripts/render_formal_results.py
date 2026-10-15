"""Render completed formal analysis without deriving new statistics.

This local CPU step reads one nonweight JSON. It does not follow evidence
references, open final states, or load models. Synthetic fixtures require
both an input marker and --synthetic and watermark every page.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = "formal-main-v2-render-1"
ANALYSIS_VERSION = "formal-main-v2-analysis-1"
PROFILE_VERSION = "formal-main-v2-o2a-1"
SCHEMA = "formal_main_v2"
SUITES = ("libero_10", "libero_spatial", "libero_object", "libero_goal")
DISPLAY_SUITES = ("libero_spatial", "libero_object", "libero_goal", "libero_10")
LABELS = dict(libero_spatial="Spatial", libero_object="Object", libero_goal="Goal", libero_10="Long", all="All suites")
BUDGETS, SEEDS = (256, 128, 64), (17, 23, 41)
PHASES = ("preprocess", "vision", "condition_selection", "packing", "llm_action", "postprocess", "unclassified")
METHODS = ("dense", "uniform256", "uniform128", "uniform64") + tuple(
    f"{arm}{budget}_seed{seed}" for budget in BUDGETS for seed in SEEDS for arm in ("A", "B"))
FAMILIES = ("dense", "uniform256", "uniform128", "uniform64") + tuple(f"{arm}{budget}" for budget in BUDGETS for arm in ("A", "B"))
INTERVAL_NOTE = ("95% percentile cluster-bootstrap intervals, 10,000 draws; task-stratified initial states carry all three "
    "training seeds. Suites, tasks and training seeds have equal weight. SD is sample SD across training seeds (ddof=1), "
    "not a confidence interval. Intervals condition on these 40 tasks and three seeds; crossing zero does not establish equivalence.")
LATENCY_NOTE = ("Complete observation-to-CPU-action chunk8 latency; 30 fixed development observations, 20 repeats each, "
    "50 warmups per instance. A/B family values are the equal-weight mean and sample SD of the three seed-specific "
    "medians/p95s/means, not percentiles of pooled calls. No latency CI is supplied. Component timings are a separate "
    "instrumented pass; host and CUDA-stream intervals overlap and are never added to full latency.")
PENDING = "pending / not supplied"


class MissingFields(Exception):
    def __init__(self, *fields):
        self.fields = list(fields)
        super().__init__("; ".join(fields))


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def need(row, key, prefix):
    if not isinstance(row, dict) or key not in row:
        raise MissingFields(prefix + "." + key)
    return row[key]


def number(value, label, low=None, high=None):
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
            or (low is not None and value < low) or (high is not None and value > high)):
        raise ValueError("Invalid finite numeric summary: " + label)
    return value


def interval(row, label, *, difference=False):
    low = -1 if difference else 0
    number(need(row, "estimate", label), label + ".estimate", low, 1)
    bounds = need(row, "ci95_percentile", label)
    if not isinstance(bounds, list) or len(bounds) != 2:
        raise ValueError("Invalid percentile interval: " + label)
    for value in bounds:
        number(value, label + ".ci95_percentile", low, 1)
    if bounds[0] > bounds[1]:
        raise ValueError("Reversed percentile interval: " + label)


def indexed(rows, field, keys, label):
    if not isinstance(rows, list):
        raise ValueError("Expected summary rows: " + label)
    values = [need(row, field, label) for row in rows]
    if len(values) != len(set(values)):
        raise ValueError("Duplicate summary instance: " + label)
    missing, extra = set(keys) - set(values), set(values) - set(keys)
    if extra:
        raise ValueError("Unexpected summary instances: " + label + ": " + str(sorted(extra)))
    if missing:
        raise MissingFields(*(label + ":" + str(value) for value in sorted(missing)))
    return {row[field]: row for row in rows}


def latency_stats(row, label):
    if need(row, "count", label) != 600:
        raise ValueError("Expected all 600 timed calls per instance/phase: " + label)
    for key in ("median", "p95", "mean"):
        number(need(row, key, label), label + "." + key, 0)


def validate_completed(data, *, synthetic):
    """Check presentation fields without recomputing any estimator."""
    if data.get("schema") != SCHEMA or data.get("status") != "completed_core_analysis":
        raise ValueError("Only completed_core_analysis may render figures")
    if data.get("weights_loaded") is not False or data.get("sealed_state_values_read") is not False:
        raise ValueError("Analysis must explicitly be nonweight and sealed-value-free")
    for key in ("registration_sha256", "evidence_manifest_sha256", "read_evidence_sha256", "retained_failed_attempts",
                "success", "latency", "diagnostics", "cost", "standalone_cache_cost", "main_experiment_delivery_complete"):
        need(data, key, "analysis")
    stats = data["success"]
    if (need(stats, "method_ids", "success") != list(METHODS) or need(stats, "suite_order", "success") != list(SUITES)
            or need(stats, "training_seeds", "success") != list(SEEDS)
            or need(stats, "unique_initial_states", "success") != 1600
            or need(stats, "states_per_suite", "success") != 400
            or need(stats, "final_trials", "success") != 35200
            or need(stats, "primary_comparison", "success") != "B128_minus_A128"):
        raise ValueError("Formal matrix, comparison or independent-state counts changed")
    boot = need(stats, "bootstrap", "success")
    for key, expected in dict(seed=20261016, repeats=10000, percentile_method="linear",
                              seed_resampling=False, p_values_reported=False).items():
        if need(boot, key, "success.bootstrap") != expected:
            raise ValueError("Unsupported bootstrap protocol: " + key)
    need(stats, "limits", "success")
    instances = indexed(need(stats, "instances", "success"), "method_id", METHODS, "success.instances")
    for mid, row in instances.items():
        interval(row, mid)
        for suite in SUITES:
            interval(need(need(row, "suites", mid), suite, mid + ".suites"), suite + ":" + mid)
    families = need(stats, "families", "success")
    for family in FAMILIES:
        row = need(families, family, "success.families")
        for scope, value in [("all", row)] + [(s, need(need(row, "suites", family), s, family + ".suites")) for s in SUITES]:
            interval(value, scope + ":" + family)
            learned = family.startswith(("A", "B"))
            seeds, sd = need(value, "per_seed", family), need(value, "seed_sample_std", family)
            if learned:
                if not isinstance(seeds, dict) or set(seeds) != {str(s) for s in SEEDS}:
                    raise MissingFields(scope + ":" + family + ": all three seed values")
                number(sd, family + ".seed_sample_std", 0)
                for seed in SEEDS:
                    number(seeds[str(seed)], family + ".per_seed", 0, 1)
            elif seeds is not None or sd is not None:
                raise ValueError("Dense/uniform cannot have invented training-seed variability")
    comparisons = need(stats, "comparisons", "success")
    for budget in BUDGETS:
        key = f"B{budget}_minus_A{budget}"
        row = need(comparisons, key, "success.comparisons")
        if (row.get("left"), row.get("right"), row.get("positive_favors")) != (f"B{budget}", f"A{budget}", f"B{budget}"):
            raise ValueError("Paired gain direction changed: " + key)
        for scope, value in [("all", row)] + [(s, need(need(row, "suites", key), s, key + ".suites")) for s in SUITES]:
            interval(value, scope + ":" + key, difference=True)
            number(need(value, "seed_sample_std", key), key + ".seed_sample_std", 0)
            per_seed = need(value, "per_seed", key)
            if not isinstance(per_seed, dict) or set(per_seed) != {str(s) for s in SEEDS}:
                raise MissingFields(scope + ":" + key + ": all three paired seed values")
            for seed in SEEDS:
                interval(per_seed[str(seed)], key + ":" + str(seed), difference=True)
    for suite in SUITES:
        profiles = need(data["latency"], suite, "latency")
        for pass_name in ("full", "components"):
            profile = need(profiles, pass_name, "latency." + suite)
            if (profile.get("version") != PROFILE_VERSION or profile.get("status") != "completed_latency_analysis"
                    or profile.get("pass_name") != pass_name or profile.get("unit") != "ms/action_chunk8"
                    or profile.get("primary_inference_latency") is not (pass_name == "full")
                    or profile.get("retained_all_calls") is not True or profile.get("synthetic") is not synthetic
                    or profile.get("test_opened") is not False):
                raise ValueError("Incomplete/mixed/synthetic timing summary: " + suite + ":" + pass_name)
            primary = indexed(need(profile, "primary", suite), "method", METHODS, suite + ":" + pass_name)
            for mid, row in primary.items():
                latency_stats(row, suite + ":" + mid)
                if row["median"] <= 0:
                    raise ValueError("Complete latency must be positive")
            summaries = indexed(need(profile, "seed_equal_weight_summaries", suite), "method_family", FAMILIES[4:], suite + ":seed latency")
            for family, row in summaries.items():
                if row.get("training_seeds") != list(SEEDS):
                    raise ValueError("Latency family lacks all three training seeds")
                for stat in ("median", "p95", "mean"):
                    for key in ("seed_mean", "seed_sample_std"):
                        number(need(need(row, stat, family), key, family + "." + stat), family + "." + key, 0)
            if pass_name == "components":
                component_rows = need(profile, "components", suite)
                keys = [(r.get("method"), r.get("phase")) for r in component_rows]
                expected = {(mid, phase) for mid in METHODS for phase in PHASES}
                if len(set(keys)) != len(keys) or set(keys) - expected:
                    raise ValueError("Duplicate or unregistered component rows")
                if expected - set(keys):
                    raise MissingFields(*(suite + ":components:" + str(k) for k in sorted(expected - set(keys))))
                for row in component_rows:
                    latency_stats(need(row, "host_ms", suite), suite + ":host component")
                    stream = need(row, "cuda_stream_elapsed_ms", suite)
                    if stream is not None:
                        latency_stats(stream, suite + ":CUDA component")
            else:
                ratios = [r for r in need(profile, "paired_comparisons", suite) if r.get("reference") == "dense"]
                for row in indexed(ratios, "treatment", METHODS[1:], suite + ":dense latency ratios").values():
                    if row.get("paired_calls") != 600:
                        raise ValueError("Incomplete paired latency ratios")
                    for key in ("ratio_of_medians", "ratio_of_p95", "speedup_ratio_of_means"):
                        number(need(row, key, suite), suite + ":" + key, 0)
    diagnostics = data["diagnostics"]
    expected = {(s, mid) for s in SUITES for mid in METHODS[4:]}
    rows = need(diagnostics, "selected_action_errors", "diagnostics")
    keys = [(r.get("suite"), r.get("method_id")) for r in rows]
    if len(keys) != len(set(keys)) or set(keys) - expected:
        raise ValueError("Duplicate/unregistered selected training diagnostics")
    if expected - set(keys):
        raise MissingFields(*(str(k) + ":selected_action_errors" for k in sorted(expected - set(keys))))
    for row in rows:
        if row.get("selected_update") not in range(0, 5001, 500) or row.get("committed_samples") != 40000:
            raise ValueError("Diagnostics do not represent complete 5000-update training")
        for key in ("teacher_l1", "demonstration_l1"):
            number(need(need(row, "action_error_task_macro", "diagnostics"), key, "diagnostics"), key, 0)
        memory = row.get("peak_cuda_memory_allocated_bytes")
        if memory is not None:
            number(memory, "training peak allocated memory", 0)
    overlap = need(diagnostics, "AB_token_overlap", "diagnostics")
    keys = [(r.get("suite"), r.get("visual_tokens"), r.get("seed")) for r in overlap]
    expected = {(s, b, seed) for s in SUITES for b in BUDGETS for seed in SEEDS}
    if len(keys) != len(set(keys)) or set(keys) - expected:
        raise ValueError("Duplicate/unregistered token overlap diagnostics")
    if expected - set(keys):
        raise MissingFields(*(str(k) + ":token_overlap" for k in sorted(expected - set(keys))))
    for row in overlap:
        for key in ("overlap_fraction_task_macro", "jaccard_task_macro"):
            number(need(row, key, "token_overlap"), key, 0, 1)
    cost = data["cost"]
    for key in ("actual_allocated_gpu_seconds", "actual_allocated_gpu_hours"):
        number(need(cost, key, "cost"), "cost." + key, 0)
    jobs = need(cost, "jobs", "cost")
    if need(cost, "unique_jobs", "cost") != len(jobs) or len({str(r.get("job_id")) for r in jobs}) != len(jobs):
        raise ValueError("Cost summary must preserve all unique job rows")
    for row in jobs:
        for key in ("job_id", "status", "elapsed_seconds", "gpus"):
            need(row, key, "cost.jobs")
    for mode, value in need(cost, "gpu_seconds_by_mode", "cost").items():
        number(value, "cost.mode." + mode, 0)
    need(cost, "scope", "cost")
    cache = data["standalone_cache_cost"]
    # The current analyzer leaves independent cache costs pending.
    # Refuse fabricated completed add-ons.
    if cache.get("status") != "pending_real_training_logs" or cache.get("not_assumed_zero") is not True:
        raise ValueError("Unsupported standalone-cost schema; no invented cost attribution")
    need(cache, "missing", "standalone_cache_cost")


def fmt(value, digits=2):
    return f"{value:.{digits}f}"


def success_cell(row, *, sd=True):
    text = fmt(row["estimate"] * 100)
    if sd and row.get("seed_sample_std") is not None:
        text += " ± " + fmt(row["seed_sample_std"] * 100)
    return text + f" [{fmt(row['ci95_percentile'][0] * 100)}, {fmt(row['ci95_percentile'][1] * 100)}]"


def table(stem, title, columns, rows, notes="", *, figure=True):
    return dict(stem=stem, title=title, columns=columns, rows=rows, notes=notes, figure=figure)


def make_tables(data):
    """Copy analysis values into cells; conversions are only units/rounding."""
    stats = data["success"]
    tables, main_rows, all_success, family_success, gains, latency, diagnostics, overlaps, ratios = [], [], [], [], [], [], [], [], []
    for suite in (*DISPLAY_SUITES, "all"):
        get = lambda row: row if suite == "all" else row["suites"][suite]
        main_rows.append([LABELS[suite]] + [success_cell(get(stats["families"][family])) for family in ("dense", "uniform128", "A128", "B128")])
        for row in stats["instances"]:
            all_success.append([LABELS[suite], row["method_id"], success_cell(get(row), sd=False)])
        for family in FAMILIES:
            family_success.append([LABELS[suite], family, success_cell(get(stats["families"][family]))])
        for budget in BUDGETS:
            row = get(stats["comparisons"][f"B{budget}_minus_A{budget}"])
            gains.append([LABELS[suite], str(budget), "seed mean ± SD", success_cell(row)])
            for seed in SEEDS:
                gains.append([LABELS[suite], str(budget), str(seed), success_cell(row["per_seed"][str(seed)], sd=False)])
    tables.append(table("main_success", "Primary budget 128 success rate (%)", ["Suite", "Dense512", "Uniform128", "A128", "B128"], main_rows, INTERVAL_NOTE))
    tables.append(table("success_all_instances", "Success rate: every deployment instance (%)", ["Suite", "Instance", "Estimate [95% CI]"], all_success, INTERVAL_NOTE))
    tables.append(table("success_families", "All budgets: success rate by family (%)", ["Suite", "Family", "Mean ± seed SD [95% CI]"], family_success,
        "Dense/uniform have one shared reference and no training-seed SD. " + INTERVAL_NOTE))
    tables.append(table("paired_gains", "Paired B minus A gain (percentage points)", ["Suite", "Budget", "Training seed", "B - A [95% CI]"], gains,
        "Positive favors B. Seed-mean rows report mean ± sample SD; individual seed rows have no SD. " + INTERVAL_NOTE))
    for suite in DISPLAY_SUITES:
        profile = data["latency"][suite]["full"]
        for row in profile["primary"]:
            latency.append([LABELS[suite], row["method"], *[fmt(row[k], 3) for k in ("median", "p95", "mean")]])
        for row in profile["seed_equal_weight_summaries"]:
            latency.append([LABELS[suite], row["method_family"] + " mean ± SD", *[
                fmt(row[k]["seed_mean"], 3) + " ± " + fmt(row[k]["seed_sample_std"], 3) for k in ("median", "p95", "mean")]])
        for row in profile["paired_comparisons"]:
            if row["reference"] == "dense":
                ratios.append([LABELS[suite], row["treatment"], *[fmt(row[k], 4) for k in
                    ("ratio_of_medians", "ratio_of_p95", "speedup_ratio_of_means")]])
        component_rows = []
        for row in data["latency"][suite]["components"]["components"]:
            component_rows.append([row["method"], row["phase"], *[fmt(row["host_ms"][k], 4) for k in ("median", "p95", "mean")], *[
                "not measured" if row["cuda_stream_elapsed_ms"] is None else fmt(row["cuda_stream_elapsed_ms"][k], 4) for k in ("median", "p95", "mean")]])
        tables.append(table("components_" + suite, LABELS[suite] + " separate component timings (ms)",
            ["Instance", "Phase", "Host median", "Host p95", "Host mean", "Stream median", "Stream p95", "Stream mean"], component_rows, LATENCY_NOTE, figure=False))
    tables.append(table("latency", "Complete observation-to-action latency (ms/chunk8)", ["Suite", "Instance / family", "Median", "p95", "Mean"], latency, LATENCY_NOTE))
    for row in data["diagnostics"]["selected_action_errors"]:
        memory = row.get("peak_cuda_memory_allocated_bytes")
        diagnostics.append([LABELS[row["suite"]], row["method_id"], str(row["selected_update"]),
            fmt(row["action_error_task_macro"]["teacher_l1"], 6), fmt(row["action_error_task_macro"]["demonstration_l1"], 6),
            PENDING if memory is None else fmt(memory / 1024 ** 3, 3), PENDING])
    tables.append(table("action_memory", "Selected action error and allocated GPU memory",
        ["Suite", "Instance", "Update", "Teacher L1", "Demo L1", "Train peak GiB", "Deploy peak GiB"], diagnostics,
        "Action errors are task-equal validation diagnostics. Training peak allocated CUDA memory differs from reserved and deployment memory. "
        "Deployment memory is not included in strict analysis output and remains pending; no raw logs or weights are read here."))
    for row in data["diagnostics"]["AB_token_overlap"]:
        overlaps.append([LABELS[row["suite"]], str(row["visual_tokens"]), str(row["seed"]),
            fmt(row["overlap_fraction_task_macro"], 6), fmt(row["jaccard_task_macro"], 6)])
    tables.append(table("token_overlap", "A/B selected-token overlap",
        ["Suite", "Budget", "Seed", "Intersection / budget", "Jaccard"], overlaps,
        "Task-equal validation diagnostics; all36 matched A/B pairs retained. No seed or budget selected by outcome."))
    tables.append(table("latency_ratios", "Measured Dense / pruned latency ratios",
        ["Suite", "Instance", "Median ratio", "p95 ratio", "Mean ratio"], ratios,
        "Copied paired timing ratios; above1 means lower measured pruned latency. These are not training-cost efficiency or amortization claims. " + LATENCY_NOTE))
    cost = data["cost"]
    rows = [["Actual allocated GPU seconds", fmt(cost["actual_allocated_gpu_seconds"], 3)],
        ["Actual allocated GPU hours", fmt(cost["actual_allocated_gpu_hours"], 6)], ["Unique registered jobs", str(cost["unique_jobs"])]]
    rows += [["GPU seconds: " + mode, fmt(seconds, 3)] for mode, seconds in cost["gpu_seconds_by_mode"].items()]
    rows += [["Independent A/B cache cost attribution", "PENDING; not assumed zero"],
        ["Experiment fully delivered", "NO: auxiliary cost attribution incomplete"]]
    tables.append(table("cost", "Actual GPU cost and unresolved attribution", ["Quantity", "Reported value"], rows,
        cost["scope"] + " " + "; ".join(data["standalone_cache_cost"]["missing"])))
    tables.append(table("cost_jobs", "Complete allocation ledger (including failed attempts)",
        ["Job", "Mode", "Status", "Elapsed allocation seconds", "GPUs"],
        [[str(r["job_id"]), str(r.get("mode", "unspecified")), str(r["status"]),
            str(r["elapsed_seconds"]), str(r["gpus"])] for r in cost["jobs"]], cost["scope"], figure=False))
    return tables


def plot_points(data, suite):
    """Coordinates are existing estimates, never pooled/reestimated values."""
    profile = data["latency"][suite]["full"]
    primary = {r["method"]: r for r in profile["primary"]}
    seed_means = {r["method_family"]: r for r in profile["seed_equal_weight_summaries"]}
    instances = {r["method_id"]: r for r in data["success"]["instances"]}
    rows = []
    for family in FAMILIES:
        success = data["success"]["families"][family]["suites"][suite]
        learned = family.startswith(("A", "B"))
        x = seed_means[family]["median"]["seed_mean"] if learned else primary[family]["median"]
        rows.append(dict(suite=suite, family=family, instance=None, median_ms=x, success_pct=success["estimate"] * 100,
            ci_pct=[v * 100 for v in success["ci95_percentile"]]))
        if learned:
            for seed in SEEDS:
                mid = f"{family}_seed{seed}"
                rows.append(dict(suite=suite, family=family, instance=mid, median_ms=primary[mid]["median"],
                    success_pct=instances[mid]["suites"][suite]["estimate"] * 100, ci_pct=None))
    return rows


def markdown_table(item, banner):
    def clean(value):
        return str(value).replace("|", "\\|").replace("\n", "<br>")
    lines = [banner, "", "# " + item["title"], "", item["notes"], "",
        "| " + " | ".join(map(clean, item["columns"])) + " |",
        "| " + " | ".join("---" for _ in item["columns"]) + " |"]
    lines += ["| " + " | ".join(map(clean, row)) + " |" for row in item["rows"]]
    return "\n".join(lines) + "\n"


def render_figures(directory, prefix, tables, data, *, synthetic, input_sha):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import textwrap

    footer = "SYNTHETIC - NOT EXPERIMENTAL RESULTS" if synthetic else "Core analysis only; independent cache-cost attribution pending"
    metadata = {"Title": prefix + "CTI-VLA formal results", "Author": "CTI-VLA",
        "Subject": footer + "; input SHA256=" + input_sha, "Keywords": VERSION + (" SYNTHETIC" if synthetic else "")}
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 9, "pdf.fonttype": 42, "ps.fonttype": 42,
                         "axes.spines.top": False, "axes.spines.right": False}), PdfPages(directory / (prefix + "formal_results.pdf"), metadata=metadata) as pdf:
        def save(fig, name):
            fig.text(.5, .017, footer, ha="center", fontsize=9, color="#b22222" if synthetic else "#555555")
            if synthetic:
                fig.text(.5, .5, "SYNTHETIC", color="#b22222", alpha=.12, rotation=25, fontsize=48, ha="center")
            pdf.savefig(fig)
            fig.savefig(directory / (prefix + name + ".png"), dpi=160,
                metadata={"Description": metadata["Subject"], "Software": VERSION})
            plt.close(fig)

        def page(item, rows, name, suffix=""):
            width = 14 if len(item["columns"]) > 5 else 12
            fig, ax = plt.subplots(figsize=(width, max(4.1, 2 + len(rows) * .26)))
            ax.axis("off")
            ax.set_title(item["title"] + suffix, loc="left", pad=16, fontsize=12, fontweight="bold")
            tab = ax.table(cellText=rows, colLabels=item["columns"], loc="center", cellLoc="left", colLoc="left")
            tab.auto_set_font_size(False)
            tab.set_fontsize(7.2 if len(item["columns"]) > 6 else 8.5)
            tab.scale(1, 1.45)
            for (row, col), cell in tab.get_celld().items():
                cell.set_edgecolor("#d5dce3")
                cell.set_linewidth(.4)
                if row == 0:
                    cell.set_facecolor("#e7edf3")
                    cell.set_text_props(weight="bold")
                elif row % 2 == 0:
                    cell.set_facecolor("#f7f9fb")
            if len(item["columns"]) <= 5:
                tab.auto_set_column_width(range(len(item["columns"])))
            note = textwrap.fill(item["notes"], 165 if width == 14 else 140)
            fig.text(.035, .055, note, ha="left", va="bottom", fontsize=7)
            fig.subplots_adjust(left=.035, right=.965, top=.85, bottom=.22)
            save(fig, name)

        for item in tables:
            if not item["figure"]:
                continue
            for start in range(0, len(item["rows"]), 28):
                suffix = "" if len(item["rows"]) <= 28 else f" (page {start // 28 + 1})"
                name = item["stem"] if not suffix else item["stem"] + f"_{start // 28 + 1:02d}"
                page(item, item["rows"][start:start + 28], name, suffix)
        # The compact component book copies means. Markdown retains each
        # phase's reported median/p95/mean and all training seeds.
        for suite in DISPLAY_SUITES:
            components = {(r["method"], r["phase"]): r for r in data["latency"][suite]["components"]["components"]}
            for key, label in (("host_ms", "Host"), ("cuda_stream_elapsed_ms", "CUDA stream")):
                rows = [[mid] + ["not measured" if components[(mid, p)][key] is None else fmt(components[(mid, p)][key]["mean"], 3) for p in PHASES] for mid in METHODS]
                item = table("", LABELS[suite] + " " + label + " component means (ms)",
                    ["Instance", "Preprocess", "Vision", "DIE / cond.", "Packing", "LLM/action", "Postprocess", "Unclassified"], rows,
                    "Independent instrumented pass; not added to full timing. Full median/p95/mean values are in components_" + suite + ".md. " + LATENCY_NOTE)
                page(item, rows, "components_" + suite + "_" + key)
        fig, axes = plt.subplots(2, 2, figsize=(12, 8.3))
        colors = dict(A="#0072B2", B="#D55E00", uniform="#777777", dense="#111111")
        for ax, suite in zip(axes.flat, DISPLAY_SUITES):
            points = plot_points(data, suite)
            summary = {r["family"]: r for r in points if r["instance"] is None}
            for family in FAMILIES:
                row = summary[family]
                arm = family[0] if family.startswith(("A", "B")) else ("dense" if family == "dense" else "uniform")
                ax.vlines(row["median_ms"], *row["ci_pct"], color=colors[arm], alpha=.55, lw=1)
            for arm, marker in (("uniform", "s"), ("A", "o"), ("B", "^")):
                rows = [summary[f"{arm}{k}"] for k in BUDGETS]
                ax.plot([r["median_ms"] for r in rows], [r["success_pct"] for r in rows], marker=marker,
                    color=colors[arm], lw=1.3, ms=6, label=arm if arm != "uniform" else "Uniform")
                for index, (budget, row) in enumerate(zip(BUDGETS, rows)):
                    offset = (-30, -16 - index * 11) if arm == "uniform" else ((-30, 12 + index * 11) if arm == "A" else (8, 12 + index * 11))
                    ax.annotate(str(budget), (row["median_ms"], row["success_pct"]), xytext=offset,
                        textcoords="offset points", fontsize=7, color=colors[arm],
                        arrowprops=dict(arrowstyle="-", color=colors[arm], alpha=.35, lw=.5))
            dense = summary["dense"]
            ax.scatter([dense["median_ms"]], [dense["success_pct"]], marker="D", color=colors["dense"], label="Dense512", s=35, zorder=5)
            for seed, marker in zip(SEEDS, ("o", "s", "^")):
                for arm in ("A", "B"):
                    rows = [r for r in points if r["instance"] and r["instance"].endswith("_seed" + str(seed)) and r["family"].startswith(arm)]
                    ax.scatter([r["median_ms"] for r in rows], [r["success_pct"] for r in rows], s=18, marker=marker,
                        edgecolors=colors[arm], facecolors="none", alpha=.6, linewidths=.65)
            ax.set(title=LABELS[suite], xlabel="Full O2A median (ms/chunk8)", ylabel="Success rate (%)", ylim=(-2, 102))
            ax.grid(alpha=.18)
        handles, labels = axes.flat[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(.5, .96))
        fig.suptitle("Success versus complete observation-to-action latency", y=.995, fontsize=13)
        fig.text(.5, .055, "A/B: equal-weight seed means; thin vertical lines: 95% state-cluster CI. Small open markers: seeds17(o),23(s),41(^).\n"
            "Lines join registered budgets only; no interpolation claim. Latency variability/SD is in the tables.", ha="center", fontsize=8)
        fig.subplots_adjust(top=.86, bottom=.15, hspace=.38, wspace=.26)
        save(fig, "success_latency")
    return matplotlib.__version__


def render(analysis_path, output_directory, *, project_root=ROOT, synthetic=False):
    root, source, output = Path(project_root).resolve(), Path(analysis_path).resolve(), Path(output_directory).resolve()
    if root not in source.parents or source.suffix.lower() != ".json" or any(s in source.name.lower() for s in ("sealed", "init_states_test")):
        raise ValueError("Input must be a project nonweight analysis JSON, never sealed state values")
    if root not in output.parents or output.exists():
        raise ValueError("Output must be a new project directory; existing artifacts are never overwritten")
    receipt = dict(version=VERSION, kind="formal_result_render", created_utc=datetime.now(timezone.utc).isoformat(),
        renderer_sha256=sha256(__file__), synthetic=synthetic, input_path=str(source), input_sha256=None,
        weights_loaded=False, sealed_state_values_read=False, new_statistics_computed=False,
        main_table_generated=False, main_experiment_delivery_complete=False, artifacts=[])
    missing, data = [], None
    if not source.is_file():
        missing = ["analysis JSON: " + str(source)]
    else:
        raw = source.read_bytes()
        receipt["input_sha256"] = hashlib.sha256(raw).hexdigest()
        data = json.loads(raw)
        if data.get("version") != ANALYSIS_VERSION:
            raise ValueError("Unsupported analysis version")
        if data.get("analysis_script_sha256") != sha256(Path(__file__).with_name("analyze_formal.py")):
            raise ValueError("Analysis source SHA differs; regenerate with the audited analyzer or preserve its exact source")
        if data.get("synthetic", False) is not synthetic:
            raise ValueError("Synthetic rendering requires marked input and --synthetic; mixed use rejected")
        receipt.update(analysis_version=data["version"], analysis_script_sha256=data["analysis_script_sha256"],
                       analysis_status=data.get("status"))
        if data.get("status") == "pending":
            missing = data.get("missing") or ["strict analysis lacks a completed evidence inventory"]
        elif data.get("status") == "completed_core_analysis":
            try:
                validate_completed(data, synthetic=synthetic)
            except MissingFields as exc:
                missing = exc.fields
        else:
            raise ValueError("Analysis status must be pending or completed_core_analysis")
    output.mkdir(parents=True, exist_ok=False)
    if missing:
        receipt.update(status="pending", missing=missing, note="No main figures/tables produced from incomplete input.")
    else:
        prefix = "synthetic_" if synthetic else ""
        banner = ("**SYNTHETIC — NOT EXPERIMENTAL RESULTS.**" if synthetic else "**正式核心分析输出；独立缓存成本归属未完成，不代表实验已全部交付。**")
        banner += "\n\nInput SHA256: `" + receipt["input_sha256"] + "`; renderer: `" + VERSION + "`."
        tables = make_tables(data)
        for item in tables:
            (output / (prefix + item["stem"] + ".md")).write_text(markdown_table(item, banner), encoding="utf-8")
        points = [r for suite in DISPLAY_SUITES for r in plot_points(data, suite)]
        (output / (prefix + "plot_coordinates.json")).write_text(json.dumps(dict(synthetic=synthetic,
            input_sha256=receipt["input_sha256"], points=points), indent=2, allow_nan=False) + "\n", encoding="utf-8")
        version = render_figures(output, prefix, tables, data, synthetic=synthetic, input_sha=receipt["input_sha256"])
        missing_aux = ["independent A/B cache attribution"]
        missing_aux += [r["suite"] + ":" + r["method_id"] + ":training peak memory" for r in data["diagnostics"]["selected_action_errors"]
            if r.get("peak_cuda_memory_allocated_bytes") is None]
        index = [banner, "", "# CTI-VLA 正式图表", "", "全部结果均从严格分析输出直接排版；未重新抽样、合并种子或计算新统计。",
            "", "1600 个唯一最终初态、35200 条最终闭环。每套件400个初态；三种子复用初态，不能视为独立初态。",
            "", INTERVAL_NOTE, "", LATENCY_NOTE, "", "主预算为128；Dense使用512 tokens。A/B每个预算均保留seed17/23/41。",
            "", "独立缓存成本归属仍pending；失败/重试及加载成本保留在完整Slurm账单。登记的显存指标为训练峰值，详见动作误差与显存表。",
            "", "## 产物", "", f"- [静态图表PDF]({prefix}formal_results.pdf)", f"- [成功率—完整延迟曲线]({prefix}success_latency.png)"]
        index += [f"- [{item['title']}]({prefix}{item['stem']}.md)" for item in tables]
        index += ["", "分项PNG/PDF使用已报告均值；对应Markdown保留每实例各分项的median/p95/mean。全部分项来自独立计时，不与完整O2A相加。",
                  "", "本生成器不打开上游证据引用、不读取权重或封存状态；证据真实性由已绑定版本的严格分析器负责校验。"]
        (output / (prefix + "README.md")).write_text("\n".join(index) + "\n", encoding="utf-8")
        receipt.update(status="rendered_core_results_auxiliary_pending", main_table_generated=True,
            matplotlib_version=version, python_version=sys.version, auxiliary_missing=missing_aux,
            cost_attribution_status=data["standalone_cache_cost"]["status"],
            upstream_main_experiment_delivery_complete=data["main_experiment_delivery_complete"],
            production_results=not synthetic, interval_description=INTERVAL_NOTE, latency_description=LATENCY_NOTE)
        receipt["artifacts"] = [dict(path=p.name, bytes=p.stat().st_size, sha256=sha256(p)) for p in sorted(output.iterdir()) if p.is_file()]
    if ((receipt["input_sha256"] is None and source.exists())
            or (receipt["input_sha256"] is not None and (not source.is_file() or receipt["input_sha256"] != sha256(source)))
            or receipt["renderer_sha256"] != sha256(__file__)
            or (receipt.get("analysis_script_sha256") is not None
                and receipt["analysis_script_sha256"] != sha256(Path(__file__).with_name("analyze_formal.py")))):
        raise ValueError("Analysis changed during rendering; partial output retained without successful receipt")
    (output / "render_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--synthetic", action="store_true", help="Explicit synthetic fixture; watermark all outputs")
    args = parser.parse_args()
    receipt = render(args.analysis, args.output_directory, project_root=args.project_root, synthetic=args.synthetic)
    print(json.dumps({k: receipt[k] for k in ("status", "synthetic", "main_table_generated", "main_experiment_delivery_complete")}, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""All-seed paired success comparisons across the trained64 and128 budgets.

Dense is one historical30-state reference. Each bootstrap state keeps its
complete three-seed vector; no repeated seed-state cell is a new initial state.
"""
from __future__ import annotations

from collections import Counter

from cti_vla.data.long_initial_states import validate_long_development_panel
from cti_vla.evaluation.future_dense_reuse import validate_dense_reference
from cti_vla.evaluation.future_multiseed import SEEDS, state_vector_interval

METHODS = ("A128", "B128", "A64", "B64")
CONTRASTS = (("B128", "A128"), ("B64", "A64"), ("B64", "A128"),
             ("A64", "A128"), ("B64", "B128"), *[(m, "dense") for m in METHODS])


def _cells(rows):
    counts = Counter({"left_only": 0, "right_only": 0, "both": 0, "neither": 0})
    for left, right in rows:
        counts["both" if left and right else "left_only" if left else "right_only" if right else "neither"] += 1
    return dict(counts)


def summarize_budget_comparison(panel, per_budget, dense_reference):
    """`per_budget[64|128][seed]` is independently replayed single-run analysis."""
    validate_long_development_panel(panel)
    validate_dense_reference(dense_reference, panel)
    if set(per_budget) != {64, 128} or any(set(per_budget[b]) != set(SEEDS) for b in per_budget):
        raise ValueError("comparison requires both budgets and every17/23/41 seed")
    states = {row["trial_id"]: row for row in panel["states"]}
    keyed = {}
    for budget in (64, 128):
        for seed in SEEDS:
            rows = per_budget[budget][seed]["pairs"]
            table = {row["state_trial_id"]: row for row in rows}
            if len(rows) != 30 or set(table) != set(states):
                raise ValueError("each trained budget/seed requires exactly the same30 unique states")
            for identity, row in table.items():
                if row["task_id"] != states[identity]["task_id"] or any(type(row[k]) is not bool for k in ("A_success", "B_success")):
                    raise ValueError("budget/seed trial state identity or outcome differs")
            keyed[budget, seed] = table
    dense = {row["state_trial_id"]: bool(row["success"]) for row in dense_reference["dense_results"]}
    vectors = []
    for identity, state in states.items():
        value = {method: [int(keyed[int(method[1:]), seed][identity][method[0] + "_success"]) for seed in SEEDS]
            for method in METHODS}
        vectors.append({"state_trial_id": identity, "task_id": state["task_id"], "dense_success": dense[identity],
            "method_seed_vectors": value})
    contrasts = {}
    for left, right in CONTRASTS:
        paired = [{"state_trial_id": row["state_trial_id"], "task_id": row["task_id"],
            "seed_vector": [a - b for a, b in zip(row["method_seed_vectors"][left],
                [int(row["dense_success"])] * 3 if right == "dense" else row["method_seed_vectors"][right])]} for row in vectors]
        per_seed = {}
        for index, seed in enumerate(SEEDS):
            def pairs(subset):
                return [(row["method_seed_vectors"][left][index],
                    int(row["dense_success"]) if right == "dense" else row["method_seed_vectors"][right][index]) for row in subset]
            group = pairs(vectors)
            per_seed[str(seed)] = {"left": left, "right": right, "left_minus_right": sum(a - b for a, b in group) / 30,
                "paired_counts": _cells(group), "by_task": {str(task): {
                    "left_minus_right": sum(a - b for a, b in pairs([r for r in vectors if r["task_id"] == task])) / 10,
                    "paired_counts": _cells(pairs([r for r in vectors if r["task_id"] == task]))} for task in (0, 3, 5)}}
        contrasts[left + "_minus_" + right] = {**state_vector_interval(paired), "per_seed": per_seed,
            "state_vectors": paired, "positive_favors": left}
    methods = {}
    for method in METHODS:
        per_seed = {}
        for index, seed in enumerate(SEEDS):
            total = sum(row["method_seed_vectors"][method][index] for row in vectors)
            per_seed[str(seed)] = {"trials": 30, "successes": total, "success_rate": total / 30,
                "by_task": {str(task): {"trials": 10,
                    "successes": sum(r["method_seed_vectors"][method][index] for r in vectors if r["task_id"] == task),
                    "success_rate": sum(r["method_seed_vectors"][method][index] for r in vectors if r["task_id"] == task) / 10}
                    for task in (0, 3, 5)}}
        rows = [{"state_trial_id": r["state_trial_id"], "task_id": r["task_id"],
            "seed_vector": r["method_seed_vectors"][method]} for r in vectors]
        methods[method] = {"per_seed": per_seed, "equal_seed_mean": state_vector_interval(rows),
            "by_task_equal_seed_mean": {str(task): sum(r["method_seed_vectors"][method][i]
                for r in vectors if r["task_id"] == task for i in range(3)) / 30 for task in (0, 3, 5)}}
    dense_summary = {"unique_trials": 30, "successes": sum(dense.values()), "success_rate": sum(dense.values()) / 30,
        "by_task": {str(task): {"trials": 10, "successes": sum(dense[k] for k, r in states.items() if r["task_id"] == task),
            "success_rate": sum(dense[k] for k, r in states.items() if r["task_id"] == task) / 10} for task in (0, 3, 5)},
        "new_inferences": 0, "new_gpu_seconds": 0, "reference_signature": dense_reference["signature"]}
    return {"training_seeds": list(SEEDS), "unique_initial_states": 30, "paired_seed_state_cells_per_contrast": 90,
        "new64_AB_trials": 180, "historical128_AB_trials": 180, "dense": dense_summary,
        "methods": methods, "contrasts": contrasts, "state_vectors": vectors,
        "limits": ["All3 training seeds retained; repeated seed-state cells are not independent initial states.",
            "Intervals condition on these3 tasks and3 seeds; seed variation is reported separately, not resampled.",
            "No significant difference does not establish equivalence; fewer tokens do not establish measured acceleration.",
            "Performance-speed tradeoff requires separately measured complete Long observation-to-action latency; no Spatial timing substitution."]}

"""Descriptive three-seed Long analysis with initial-state cluster resampling."""
from __future__ import annotations

from collections import Counter
import numpy as np

from cti_vla.data.long_initial_states import validate_long_development_panel
from cti_vla.evaluation.future_dense_reuse import validate_dense_reference

SEEDS = (17, 23, 41)


def state_vector_interval(rows, *, repeats=2000, seed=1517):
    """Each selected state carries all three seed values in each bootstrap draw."""
    if repeats != 2000 or seed != 1517:
        raise ValueError("registered multiseed bootstrap fixes2000 draws and seed1517")
    if (len(rows) != 30 or len({r["state_trial_id"] for r in rows}) != 30
            or Counter(r["task_id"] for r in rows) != {0: 10, 3: 10, 5: 10}):
        raise ValueError("bootstrap needs30 unique states in the three fixed tasks")
    values = np.asarray([r["seed_vector"] for r in rows], dtype=float)
    if values.shape != (30, 3) or not np.isfinite(values).all():
        raise ValueError("each state must retain its complete three-seed vector")
    rng = np.random.default_rng(seed)
    replicates = np.zeros((repeats, 3))
    for task in (0, 3, 5):
        group = sorted((r for r in rows if r["task_id"] == task), key=lambda r: r["state_trial_id"])
        block = np.asarray([r["seed_vector"] for r in group], dtype=float)
        replicates += block[rng.integers(0, 10, (repeats, 10))].sum(axis=1)
    seed_means = values.mean(axis=0)
    return {"mean": float(values.mean()), "ci95_percentile": np.quantile(replicates.mean(axis=1) / 30, [.025, .975]).tolist(),
        "unique_initial_states": 30, "training_seeds": list(SEEDS), "paired_seed_state_cells": 90,
        "repeats": repeats, "bootstrap_seed": seed, "resampling_unit": "state_trial_id with complete3-seed vector",
        "stratified_by": "task_id", "per_training_seed_mean": dict(zip(map(str, SEEDS), seed_means.tolist())),
        "training_seed_mean_sample_sd": float(seed_means.std(ddof=1)), "training_seed_mean_range": [float(seed_means.min()), float(seed_means.max())],
        "interpretation": "Descriptive interval conditional on these3 trained seeds and3 tasks; training seeds are not resampled. Three seeds do not establish broad population generalization."}


def summarize_seed_vectors(panel, per_seed, dense_reference):
    validate_long_development_panel(panel)
    validate_dense_reference(dense_reference, panel)
    if set(per_seed) != set(SEEDS):
        raise ValueError("all17/23/41 seed results are required; never choose best seeds")
    expected = {r["trial_id"]: r for r in panel["states"]}
    keyed = {}
    for seed, report in per_seed.items():
        rows = report["pairs"]
        keyed[seed] = {r["state_trial_id"]: r for r in rows}
        if len(rows) != 30 or set(keyed[seed]) != set(expected):
            raise ValueError("seed result lacks exact30 paired development states")
        for identity, row in keyed[seed].items():
            if row["task_id"] != expected[identity]["task_id"] or any(type(row[k]) is not bool for k in ("A_success", "B_success")):
                raise ValueError("seed state/task/outcome identity mismatch")
    dense = {r["state_trial_id"]: r for r in dense_reference["dense_results"]}
    vectors, all_results = [], []
    for identity, state in expected.items():
        av = [int(keyed[s][identity]["A_success"]) for s in SEEDS]
        bv = [int(keyed[s][identity]["B_success"]) for s in SEEDS]
        vectors.append({"state_trial_id": identity, "task_id": state["task_id"],
            "dense_success": dense[identity]["success"], "A_seed_vector": av, "B_seed_vector": bv})
        all_results.extend({"training_seed": s, "state_trial_id": identity, "task_id": state["task_id"],
            "A_success": bool(av[i]), "B_success": bool(bv[i]), "B_minus_A": bv[i] - av[i]}
            for i, s in enumerate(SEEDS))
    contrasts = {}
    for name in ("A_success", "B_success", "B_minus_A", "A_minus_dense", "B_minus_dense"):
        rows = []
        for r in vectors:
            a, b, d = np.array(r["A_seed_vector"]), np.array(r["B_seed_vector"]), int(r["dense_success"])
            value = {"A_success": a, "B_success": b, "B_minus_A": b - a, "A_minus_dense": a - d, "B_minus_dense": b - d}[name]
            rows.append({"state_trial_id": r["state_trial_id"], "task_id": r["task_id"], "seed_vector": value.tolist()})
        contrasts[name] = state_vector_interval(rows)
    dense_summary = {"unique_trials": 30, "successes": sum(r["success"] for r in dense.values()),
        "by_task": {str(t): {"trials": 10, "successes": sum(r["success"] for r in dense.values() if r["task_id"] == t)} for t in (0, 3, 5)},
        "source_training_seed": 17, "reused_without_new_inference": True, "additional_gpu_seconds": 0}
    return {"training_seeds": list(SEEDS), "unique_initial_states": 30, "new_AB_trials": 120,
        "all_AB_seed_state_pairs": 90, "dense_reference": dense_summary, "contrasts": contrasts,
        "state_vectors": vectors, "all_paired_results": all_results,
        "per_seed": {str(s): {"methods": per_seed[s]["methods"], "paired_counts": per_seed[s]["paired_counts"],
            "paired_B_minus_A": per_seed[s]["paired_B_minus_A"], "paired_vs_dense": per_seed[s]["paired_vs_dense"]} for s in SEEDS},
        "limits": "Same initial states recur across training seeds.90 cells are not90 independent states. Report every seed and conditional cluster intervals; no test, broad significance or automatic expansion."}

"""Synthetic-only resource accounting, phase boundaries and bounded cache replay."""
from collections import Counter
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("formal_resource_under_test", ROOT / "scripts/estimate_formal_resources.py")
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def ref(root, name, payload, *, lines=False):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in payload) if lines else json.dumps(payload), encoding="utf-8")
    return {"path": path.relative_to(root).as_posix(), "sha256": r.digest(path)}


def registered_matrix():
    return dict(schema=r.SCHEMA, suite_order=list(r.SUITES), budgets=[256, 128, 64], seeds=[17, 23, 41],
        training_arms=72, suites={s: {"windows": f"manifests/{s}/windows.json"} for s in r.SUITES},
        pairs=[dict(suite=s, visual_tokens=k, seed=seed, path=f"configs/{s}/k{k}s{seed}.json",
            run_root_server=f"/CTI-VLA/results/{s}/k{k}s{seed}")
            for s in r.SUITES for k in (256, 128, 64) for seed in (17, 23, 41)])


@pytest.fixture(scope="module")
def synthetic(tmp_path_factory):
    root = tmp_path_factory.mktemp("resource-synthetic")
    registration = registered_matrix()
    window_refs = {}
    for suite in r.SUITES:
        train = [f"{suite}:train:{i}" for i in range(5000)]
        valid = [f"{suite}:validation:{i}" for i in range(165)]
        rows = [dict(window_id=wid, split=split, task_id=i % 10, episode_id=f"{suite}:{split}:episode{i % 10}")
            for split, ids in (("train", train), ("validation", valid)) for i, wid in enumerate(ids)]
        window_refs[suite] = ref(root, registration["suites"][suite]["windows"],
            dict(version="formal-main-v2-full-pool-h8", suite=suite, horizon=8, test_pixels_opened=False,
                train_window_ids=train, validation_window_ids=valid, windows=rows))
    for pair in registration["pairs"]:
        config = dict(schema=r.SCHEMA, suite=pair["suite"], seed=pair["seed"], tokens_per_camera=pair["visual_tokens"] // 2,
            training=dict(updates=5000, effective_batch=8, checkpoint_every_updates=50),
            selection=dict(updates=list(range(0, 5001, 500))))
        pair["sha256"] = ref(root, pair["path"], config)["sha256"]
    pair = next(p for p in registration["pairs"] if (p["suite"], p["visual_tokens"], p["seed"]) == ("libero_10", 128, 17))
    config = json.loads((root / pair["path"]).read_text(encoding="utf-8"))
    windows = r.read_windows(r.Evidence(root), window_refs, registration)
    wm = windows["libero_10"]
    order = r.sample_order(wm["train"], 17)
    cache_identity = {"suite": "libero_10", "source": "synthetic-producer", "window_manifest_sha256": wm["sha256"]}
    cache_sha = r.signature({"cache_version": r.CACHE_VERSION, **cache_identity})
    cache_rows, cost_rows, reports, attempts = [], [], {}, []
    cache_disk = set()
    arms, arm_walls = {}, []
    job = "1001"

    def cache_get(wid, arm, phase, update):
        context = dict(job_id=job, arm=arm, phase=phase, update=update, cache_identity_sha256=cache_sha)
        logical = "window:" + wid
        if wid in cache_disk:
            cache_rows.append(dict(event="cache_hit", logical_key=logical, seconds=.005, **context))
            return .005
        cache_disk.add(wid)
        cache_rows.append(dict(event="cache_miss", logical_key=logical, **context))
        cache_rows.append(dict(event="feature_generate_start", window_id=wid, split=wm["rows"][wid]["split"], **context))
        cache_rows.append(dict(event="feature_generate_end", window_id=wid, seconds=.03,
            teacher_forwards=1, vision_forwards=2, current_vision_forwards=1, future_vision_forwards=1,
            current_preprocess_vision_projection_seconds=.005, teacher_forward_seconds=.01,
            future_preprocess_vision_target_seconds=.01, window_diagnostic_seconds=.005,
            future_target_required_by_current_arm=arm == "B", future_target_detached=True,
            window_alignment_validated=True, **context))
        cache_rows.append(dict(event="cache_publish", logical_key=logical, seconds=.04, bytes=1024**2, **context))
        return .04

    for arm in ("A", "B"):
        identity = dict(pair_config_sha256=r.signature(config), training_config_sha256=r.signature({**config, "arm": arm}),
            window_manifest_sha256=wm["sha256"], cache_identity=cache_identity, frozen_model_sha256="synthetic-base")
        events, elapsed, aid = [], 0., "attempt_" + arm

        def event(name, **fields):
            events.append(dict(event=name, job_id=job, attempt_id=aid, attempt_elapsed_seconds=elapsed, **fields))

        event("attempt_start", resumed=False, completed_update=0, next_sample_cursor=0, identity=identity)
        elapsed += .01
        event("checkpoint_commit", completed_update=0, seconds=.01)
        for update in range(501):
            if update:
                ids = order[(update - 1) * 8:update * 8]
                event("update_start", update=update, window_ids=ids)
                cache_work = 0.
                for micro, wid in enumerate(ids):
                    event("sample_start", update=update, micro_batch_index=micro, window_id=wid)
                    value = cache_get(wid, arm, "training", update)
                    elapsed += value + (1. if arm == "A" else 1.2) / 8.
                    cache_work += value
                    event("sample_end", update=update, micro_batch_index=micro, window_id=wid)
                event("update_end", update=update, seconds=cache_work + (1. if arm == "A" else 1.2), forward_backward_samples=8)
            if update in (0, 500):
                event("validation_start", update=update, windows=165)
                black = 0.
                if arm == "A" and update == 0:
                    black = .02
                    context = dict(job_id=job, arm=arm, phase="validation", update=update, cache_identity_sha256=cache_sha)
                    cache_rows.extend([dict(event="cache_miss", logical_key="shared:black-image", **context),
                        dict(event="cache_publish", logical_key="shared:black-image", seconds=black, bytes=4096, **context)])
                work = black + sum(cache_get(wid, arm, "validation", update) for wid in wm["validation"])
                elapsed += work + .33 + .02
                event("validation_end", update=update, seconds=work + .33, window_forwards=165)
            if update % 50 == 0:
                elapsed += .01
                event("checkpoint_commit", completed_update=update, seconds=.01)
        elapsed += .2
        event("attempt_end", status="checkpointed", completed_update=500, seconds=elapsed)
        report = dict(schema=r.SCHEMA, status="checkpointed", arm=arm, identity=identity,
            training_updates_completed=500, next_sample_cursor=4000, committed_samples=4000,
            unique_committed_windows=len(set(order[:4000])), train_pool_windows=len(wm["train"]),
            evaluations=[dict(update=0), dict(update=500)], initial_scorer_sha256="synthetic-init",
            sample_order_sha256=r.signature(order), vla_parameters_unchanged=True,
            frozen_model_sha256="synthetic-base", attempted_forward_backward_samples_completed=4000,
            job_ids=[job], peak_cuda_memory_allocated_bytes=12345)
        ordering = dict(version=r.ORDER_VERSION, seed=17, train_pool_size=len(wm["train"]),
            train_pool_sha256=r.signature(wm["train"]), samples=order, order_sha256=r.signature(order),
            initial_scorer_sha256="synthetic-init")
        arms[arm] = dict(report=ref(root, f"reference/{arm}/progress_report.json", report),
            training_order=ref(root, f"reference/{arm}/training_order.json", ordering),
            cost_events=[ref(root, f"reference/{arm}/attempts/one/cost_events.jsonl", events, lines=True)])
        reports[arm] = report
        attempts.append(dict(arm=arm, job_id=job, attempt_id=aid, seconds=elapsed, status="checkpointed",
            resumed=False, start_update=0, end_update=500))
        cost_rows.extend({**row, "arm": arm} for row in events)
        arm_walls.append(elapsed)
    total = sum(arm_walls) + 10.
    receipt = dict(schema=r.SCHEMA, job_id=job, stage="train", source_sha256="source",
        invocation_sha256="invocation", wall_seconds=total - 1., exit_code=0)
    state = dict(registered_jobs=[dict(job_id=job, experiment=r.SCHEMA, mode="train", run_root=pair["run_root_server"],
        source_sha256="source", invocation_sha256="invocation"),
        dict(job_id="1002", experiment=r.SCHEMA, mode="acceptance", run_root="/CTI-VLA/results/acceptance")])
    bills = dict(jobs=[dict(job_id=job, experiment=r.SCHEMA, mode="train", status="COMPLETED", elapsed_seconds=total, gpus=1),
        dict(job_id="1002", experiment=r.SCHEMA, mode="acceptance", status="FAILED", elapsed_seconds=7., gpus=1)])
    accounting, registered = r.account_snapshot(state, bills)
    evidence = dict(schema=r.SCHEMA, kind="resource_evidence", registration_sha256=r.signature(registration),
        supervisor_state=ref(root, "state.json", state), accounting=ref(root, "accounting.json", bills),
        windows=window_refs, reference_pair=dict(arms=arms,
            cache_events=[ref(root, "reference/cache_events/one.jsonl", cache_rows, lines=True)],
            job_receipts=[ref(root, "receipts/1001.json", receipt)]))
    reference = dict(config=config, reports=reports, order=order, attempts=attempts,
        cost_rows=cost_rows, cache_rows=cache_rows, job_ids={job}, receipts={job: receipt})
    return dict(root=root, registration=registration, evidence=evidence, windows=windows,
        reference=reference, accounting=accounting, registered=registered, state=state, bills=bills)


def test_sampler_matches_frozen_implementation_without_global_rng_changes():
    from cti_vla.training.formal_future import fixed_window_order
    pool = ["z", "a", "x", "q", "m"]
    before = random.getstate()
    assert r.sample_order(pool, 17, 21) == fixed_window_order(pool, seed=17, samples=21)
    assert before == random.getstate()
    assert r.sample_order(pool, 23, 21) != r.sample_order(pool, 17, 21)


@pytest.mark.parametrize("pool,seed,n", [([], 17, 1), (["a", "a"], 17, 1), (["a"], 17, -1), (["a"], True, 1)])
def test_sampler_rejects_nonregistered_shapes(pool, seed, n):
    with pytest.raises(ValueError):
        r.sample_order(pool, seed, n)


def test_lru_pinned_black_ram_hit_does_not_refresh_disk_and_restart_clears_ram():
    cache = r.CacheReplay(7, lambda _: 2, 1, ram_capacity=2)
    for wid in ("a", "b", "a", "c", "d"):
        cache.request("j1", "A", "training", wid)
    assert cache.counts["ram_hits"] == 1
    assert "a" not in cache.disk and "__black__" in cache.disk
    assert cache.counts["evictions"] == 1 and cache.peak == 7
    cache.request("j2", "B", "training", "d")
    assert cache.groups[("B", "training")]["black_hits"] == 1
    assert cache.groups[("B", "training")]["disk_hits"] == 1
    assert cache.groups[("B", "training")]["ram_hits"] == 0


@pytest.mark.parametrize("capacity,size,black", [(0, 1, 1), (5, 6, 1), (5, 5, 1)])
def test_replay_cannot_silently_exceed_capacity(capacity, size, black):
    with pytest.raises(ValueError):
        r.CacheReplay(capacity, lambda _: size, black).request("job", "A", "training", "x")


def test_schedule_complete72_protocol_and_shared_invocation_boundary():
    order = [str(i) for i in range(40000)]
    rows = list(r.pair_schedule(order, [f"v{i}" for i in range(165)]))
    counts = Counter((arm, phase) for _, arm, phase, _ in rows)
    assert counts == {("A", "training"): 40000, ("B", "training"): 40000,
        ("A", "validation"): 1815, ("B", "validation"): 1815}
    assert len({job for job, _, _, _ in rows}) == 10
    assert rows[0] == (500, "A", "validation", "v0")
    assert rows[165] == (500, "A", "training", "0")
    assert rows[4330] == (500, "B", "validation", "v0")
    with pytest.raises(ValueError):
        list(r.pair_schedule(order[:-1], ["v"]))


def test_shared_and_independent_cache_replay_are_different():
    kwargs = dict(updates=2, batch=2, segment=1)
    shared = r.CacheReplay(100, lambda _: 3, 1)
    for job, arm, phase, wid in r.pair_schedule(["a", "b", "c", "d"], ["v"], **kwargs):
        shared.request(job, arm, phase, wid)
    independent = r.CacheReplay(100, lambda _: 3, 1)
    for job, arm, phase, wid in r.pair_schedule(["a", "b", "c", "d"], ["v"], paired=False, **kwargs):
        independent.request(job, arm, phase, wid)
    assert shared.counts["misses"] == independent.counts["misses"] == 6  # pinned+5 unique
    assert shared.groups[("B", "training")]["misses"] == 0
    assert independent.groups[("A", "training")]["misses"] == 4
    assert shared.counts["requests"] == 2 * independent.counts["requests"]


def test_actual_allocation_unique_includes_failed_and_provisional(synthetic):
    state, bills = deepcopy(synthetic["state"]), deepcopy(synthetic["bills"])
    state["registered_jobs"].append(dict(job_id="1003", experiment=r.SCHEMA, mode="train"))
    bills["jobs"].append(dict(job_id="1003", experiment=r.SCHEMA, mode="train", status="RUNNING", elapsed_seconds=3., gpus=2))
    value, _ = r.account_snapshot(state, bills)
    assert value["finalized_failed_gpu_seconds"] == 7.
    assert value["provisional_gpu_seconds"] == 6.
    assert value["unique_jobs"] == 3 and value["status"] == "incomplete_or_provisional_snapshot"
    assert value["measured_allocation_gpu_seconds_through_snapshot"] == pytest.approx(sum(x["elapsed_seconds"] * x["gpus"] for x in bills["jobs"]))


@pytest.mark.parametrize("mutation", ["duplicate", "foreign", "unknown", "negative", "missing_gpu"])
def test_bad_bills_never_get_implicit_cost(synthetic, mutation):
    bills = deepcopy(synthetic["bills"])
    if mutation == "duplicate":
        bills["jobs"].append(bills["jobs"][0].copy())
    elif mutation == "foreign":
        bills["jobs"][0]["experiment"] = "other_project"
    elif mutation == "unknown":
        bills["jobs"][0]["job_id"] = "9999"
    elif mutation == "negative":
        bills["jobs"][0]["elapsed_seconds"] = -1
    else:
        del bills["jobs"][0]["gpus"]
    with pytest.raises(ValueError):
        r.account_snapshot(synthetic["state"], bills)


def test_missing_evidence_reports_pending_without_numerical_projection(synthetic):
    evidence = deepcopy(synthetic["evidence"])
    del evidence["reference_pair"]
    value = r.estimate(evidence, synthetic["registration"], root=synthetic["root"])
    assert value["status"] == "pending" and value["training_projection"] is None
    assert value["actual_cost"]["finalized_failed_gpu_seconds"] == 7.
    assert value["evaluation_cost"]["status"] == "pending_measurements"
    assert "Long128seed17" in value["missing"][0]


def test_read_reference_real_schema_synthetic_journals_and_full_calibration(synthetic):
    s = synthetic
    reader = r.Evidence(s["root"])
    reference = r.read_reference(reader, s["evidence"]["reference_pair"], s["registration"], s["windows"], s["accounting"], s["registered"])
    measured = r.measured_rates(reference, s["windows"], s["accounting"])
    reader.unchanged()
    assert measured["rates"]["update"]["A"] == pytest.approx([1., 1.])
    assert measured["rates"]["update"]["B"] == pytest.approx([1.2, 1.2])
    assert measured["rates"]["validation"]["A"] == pytest.approx([.002, .002])
    assert measured["rates"]["job_other"] == pytest.approx([10., 10.])
    assert measured["rates"]["arm_other"] == pytest.approx([.2, .2])
    assert measured["rates"]["cache_publish"] == [.04, .04]
    assert measured["rates"]["black_hit"] == [.005, .005]  # explicit nonzero proxy
    actual = measured["observed"]
    assert actual["per_arm"]["A"]["update_wall_seconds"]["count"] == 500
    assert actual["per_arm"]["B"]["full165_validation_seconds"]["count"] == 2
    assert actual["future_generation_triggered_by_A_seconds"] == pytest.approx(4165 * .01)
    assert actual["future_diagnostics_triggered_by_A_seconds"] == pytest.approx(4165 * .005)
    assert actual["isolated_model_loading_seconds"]["status"] == "not_separately_measured"
    assert actual["black_record_disk_hit_seconds"]["status"] == "unmeasured"
    assert actual["cache_request_counts_by_arm_phase"]["B:training"] == {"cache_hit": 4000}
    assert actual["published_window_bytes"]["minimum"] == 1024**2


def test_fewer_than500_committed_updates_stays_pending(synthetic):
    s = synthetic
    evidence = deepcopy(s["evidence"])
    report = deepcopy(s["reference"]["reports"]["A"])
    report.update(training_updates_completed=499, next_sample_cursor=3992)
    evidence["reference_pair"]["arms"]["A"]["report"] = ref(s["root"], "incomplete500/report.json", report)
    result = r.estimate(evidence, s["registration"], root=s["root"])
    assert result["status"] == "pending" and result["training_projection"] is None
    assert "first500" in result["missing"][0]


def test_reference_cache_namespace_and_job_identity_are_bound(synthetic):
    s = synthetic
    evidence = deepcopy(s["evidence"])
    cache = deepcopy(s["reference"]["cache_rows"])
    cache[0]["cache_identity_sha256"] = "other-model-source"
    evidence["reference_pair"]["cache_events"] = [ref(s["root"], "wrong_namespace/cache.jsonl", cache, lines=True)]
    with pytest.raises(ValueError, match="namespace"):
        r.read_reference(r.Evidence(s["root"]), evidence["reference_pair"], s["registration"], s["windows"], s["accounting"], s["registered"])
    registered = deepcopy(s["registered"])
    registered["1001"]["run_root"] = "/some-other-project"
    with pytest.raises(ValueError, match="outside this registered"):
        r.read_reference(r.Evidence(s["root"]), s["evidence"]["reference_pair"], s["registration"], s["windows"], s["accounting"], registered)


@pytest.mark.parametrize("mutation", ["missing_sample", "wrong_order", "missing_request", "bad_future_arm", "nested_exceeds_parent", "too_much_cache", "incomplete_success"])
def test_calibration_rejects_partial_or_misidentified_measurements(synthetic, mutation):
    reference = deepcopy(synthetic["reference"])
    if mutation == "missing_sample":
        reference["cost_rows"] = [x for x in reference["cost_rows"] if not (x["event"] == "sample_end" and x.get("update") == 1 and x.get("micro_batch_index") == 0 and x["arm"] == "A")]
    elif mutation == "wrong_order":
        row = next(x for x in reference["cost_rows"] if x["event"] == "update_start")
        row["window_ids"] = row["window_ids"][::-1]
    elif mutation == "missing_request":
        index = next(i for i, x in enumerate(reference["cache_rows"]) if x["event"] == "cache_miss" and x.get("phase") == "training")
        reference["cache_rows"].pop(index)
    elif mutation == "bad_future_arm":
        next(x for x in reference["cache_rows"] if x["event"] == "feature_generate_end")["future_target_required_by_current_arm"] = True
    elif mutation == "nested_exceeds_parent":
        next(x for x in reference["cache_rows"] if x["event"] == "feature_generate_end")["teacher_forward_seconds"] = 10.
    elif mutation == "too_much_cache":
        next(x for x in reference["cache_rows"] if x["event"] == "cache_publish")["seconds"] = 100.
    else:
        row = next(x for x in reference["cost_rows"] if x["event"] == "attempt_end")
        index = reference["cost_rows"].index(row)
        reference["cost_rows"].insert(index, dict(event="update_start", arm="A", job_id="1001", attempt_id="attempt_A",
            update=501, window_ids=reference["order"][4000:4008], attempt_elapsed_seconds=row["seconds"]))
    with pytest.raises(ValueError):
        r.measured_rates(reference, synthetic["windows"], synthetic["accounting"])


def test_failed_partial_work_retained_but_not_used_as_complete_update(synthetic):
    reference, accounting = deepcopy(synthetic["reference"]), deepcopy(synthetic["accounting"])
    row = dict(event="attempt_start", arm="A", job_id="1004", attempt_id="failed", attempt_elapsed_seconds=0)
    reference["cost_rows"].extend([row,
        {**row, "event": "update_start", "update": 501, "window_ids": reference["order"][4000:4008]},
        {**row, "event": "sample_start", "update": 501, "micro_batch_index": 0, "window_id": reference["order"][4000]},
        {**row, "event": "attempt_end", "status": "failed", "seconds": 3., "attempt_elapsed_seconds": 3.}])
    reference["attempts"].append(dict(arm="A", job_id="1004", attempt_id="failed", status="failed", seconds=3.))
    reference["job_ids"].add("1004")
    reference["receipts"]["1004"] = {"wall_seconds": 4.}
    accounting["jobs"]["1004"] = {"elapsed_seconds": 5., "gpu_seconds": 5.}
    measured = r.measured_rates(reference, synthetic["windows"], accounting)
    assert measured["observed"]["failed_attempt_residual_seconds"] == [3.]
    assert measured["observed"]["per_arm"]["A"]["update_wall_seconds"]["count"] == 500
    assert next(x for x in measured["observed"]["jobs"] if x["job_id"] == "1004")["actual_allocated_gpu_seconds"] == 5.


@pytest.mark.parametrize("name", ["sealed_values.json", "weights/a.json", "initial_states/a.json", "panel.json", "init_states_test.json"])
def test_forbidden_evidence_is_rejected_before_file_read(tmp_path, monkeypatch, name):
    def forbidden(*args, **kwargs):
        raise AssertionError("forbidden metadata path was opened")
    monkeypatch.setattr(r, "digest", forbidden)
    with pytest.raises(ValueError, match="never weights or state values"):
        r.Evidence(tmp_path).read({"path": name, "sha256": "not-read"}, "unsafe")


def test_sha_and_partial_jsonl_fail_closed_without_repair(tmp_path):
    item = ref(tmp_path, "journal.jsonl", [{"event": "a"}], lines=True)
    reader = r.Evidence(tmp_path)
    with pytest.raises(ValueError, match="SHA mismatch"):
        reader.lines({**item, "sha256": "wrong"}, "journal")
    path = tmp_path / item["path"]
    path.write_bytes(b'{"event":"unfinished"}')
    item["sha256"] = r.digest(path)
    before = path.read_bytes()
    with pytest.raises(r.Pending, match="incomplete JSONL"):
        reader.lines(item, "journal")
    assert path.read_bytes() == before


def test_readonly_complete_pipeline_uses_real_evidence_and_keeps_evaluation_pending(synthetic, monkeypatch):
    monkeypatch.setattr(r, "project_training", lambda *args: {"status": "synthetic-projection-checked-separately"})
    result = r.estimate(synthetic["evidence"], synthetic["registration"], root=synthetic["root"])
    assert result["status"] == "conditional_training_estimate_evaluation_pending"
    assert result["evaluation_cost"]["status"] == "pending_measurements"
    assert result["main_experiment_resource_total"]["status"] == "pending"
    assert result["actual_cost"]["unique_jobs"] == 2
    assert result["weights_read"] is result["sealed_states_read"] is result["new_jobs_submitted"] is False
    assert len(result["read_evidence_sha256"]) == 15


def test_projection_has72_arms_disjoint_components_explicit_cost_assumptions(synthetic, monkeypatch):
    measured = r.measured_rates(synthetic["reference"], synthetic["windows"], synthetic["accounting"])
    calls = []

    def replay(registration, windows, measured, *, endpoint, shared):
        calls.append((endpoint, shared))
        counts = {a + ":" + phase: dict(requests=40000 if phase == "training" else 1815,
            misses=100, disk_hits=200, black_misses=1, black_hits=9) for a in ("A", "B") for phase in ("training", "validation")}
        return dict(rows=[dict(suite=p["suite"], budget=p["visual_tokens"], seed=p["seed"], groups=counts)
            for p in registration["pairs"]], order_is_resource_assumption=True)

    monkeypatch.setattr(r, "cache_projection", replay)
    value = r.project_training(synthetic["registration"], synthetic["windows"], measured)
    assert calls == [(0, True), (1, True), (0, False), (1, False)]
    assert value["fresh_training_only"] is True and value["remaining_cost_not_identified"] is True
    assert value["unmeasured_suites"] == list(r.SUITES[1:]) and value["unmeasured_budgets"] == [256, 64]
    assert "not preregistered" in value["assumptions"]["schedule_status"]
    scenario = value["scenarios"]["shared_cache_serial"]["endpoints"][0]
    row = next(x for x in scenario["rows"] if (x["suite"], x["budget"], x["seed"], x["arm"]) == ("libero_10", 128, 17, "A"))
    assert row["update_compute_excluding_cache_seconds"] == pytest.approx(5000.)
    assert row["hard_validation_excluding_cache_seconds"] == pytest.approx(11 * 165 * .002)
    assert row["cache_operations_seconds"] == pytest.approx(2 * (100 * .04 + 200 * .005 + .02 + 9 * .005))
    assert row["A_triggered_train_future_and_diagnostic_component_seconds"] == pytest.approx(100 * .015)
    assert row["A_hypothetical_independent_train_future_savings_seconds"] == 0.
    assert row["checkpoint_and_validation_artifact_seconds"] == pytest.approx(103 * .01 + 11 * .02)
    parts = ("update_compute_excluding_cache_seconds", "hard_validation_excluding_cache_seconds",
        "checkpoint_and_validation_artifact_seconds", "cache_operations_seconds", "within_arm_other_seconds")
    assert row["subtotal_seconds"] == pytest.approx(sum(row[k] for k in parts))
    assert scenario["trained_arms"] == 72 and scenario["planned_jobs"] == 360
    assert scenario["total_scenario_gpu_seconds"] == pytest.approx(sum(x["subtotal_seconds"] for x in scenario["rows"]) + 360 * 10. * .5)
    assert value["scenarios"]["independent_cache_per_arm"]["endpoints"][0]["planned_jobs"] == 720
    independent = value["scenarios"]["independent_cache_per_arm"]["endpoints"][0]
    independent_A = next(x for x in independent["rows"] if (x["suite"], x["budget"], x["seed"], x["arm"]) == ("libero_10", 128, 17, "A"))
    assert independent_A["A_hypothetical_independent_train_future_savings_seconds"] == pytest.approx(100 * .015)


def test_cache_projection_reference_pair_first_and_all36_pairs_retained(synthetic, monkeypatch):
    measured = r.measured_rates(synthetic["reference"], synthetic["windows"], synthetic["accounting"])
    original = r.pair_schedule
    # Keep the production ordering and replay; limit only synthetic request
    # counts here. The complete40000+11x165 schedule is checked independently.
    monkeypatch.setattr(r, "pair_schedule", lambda order, validation, **kw:
        original(order[:4], validation[:3], updates=2, batch=2, segment=1, **kw))
    value = r.cache_projection(synthetic["registration"], synthetic["windows"], measured, endpoint=0, shared=True)
    assert value["pair_order"][0] == dict(suite="libero_10", budget=128, seed=17)
    remaining = [dict(suite=p["suite"], budget=p["visual_tokens"], seed=p["seed"]) for p in synthetic["registration"]["pairs"]
        if (p["suite"], p["visual_tokens"], p["seed"]) != ("libero_10", 128, 17)]
    assert value["pair_order"][1:] == remaining
    assert len(value["rows"]) == 36 and value["maximum_suite_disk_bytes"] < r.CAPACITY
    assert value["order_is_resource_assumption"] and value["cache_records_are_simulated"]

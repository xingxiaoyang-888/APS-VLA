"""Explicitly synthetic presentation fixtures; no experiments are run."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("formal_render_under_test", ROOT / "scripts/render_formal_results.py")
r = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r)


def estimate(value=.7):
    return dict(estimate=value, ci95_percentile=[value - .05, value + .05])


def family_value(family):
    learned = family.startswith(("A", "B"))
    base = .72 if family.startswith("B") else .7
    return dict(**estimate(base), per_seed={str(seed): base + delta for seed, delta in zip(r.SEEDS, (-.1, 0, .1))}
        if learned else None, seed_sample_std=.1 if learned else None)


def profile(pass_name):
    primary = [dict(method=mid, count=600, median=200.123, p95=222.234, mean=205.345) for mid in r.METHODS]
    summaries = [dict(method_family=family, training_seeds=list(r.SEEDS),
        **{stat: dict(seed_mean=value, seed_sample_std=.987654) for stat, value in
           (("median", 200.123), ("p95", 222.234), ("mean", 205.345))}) for family in r.FAMILIES[4:]]
    phases = [dict(method=mid, phase=phase,
        host_ms=dict(count=600, median=2.1234, p95=3.2345, mean=2.3456),
        cuda_stream_elapsed_ms=None if phase == "unclassified" else dict(count=600, median=1.1234, p95=2.2345, mean=1.3456))
        for mid in r.METHODS for phase in r.PHASES] if pass_name == "components" else []
    return dict(version=r.PROFILE_VERSION, status="completed_latency_analysis", pass_name=pass_name,
        synthetic=True, primary_inference_latency=pass_name == "full", retained_all_calls=True,
        test_opened=False, unit="ms/action_chunk8", primary=primary, components=phases,
        seed_equal_weight_summaries=summaries,
        paired_comparisons=[dict(treatment=mid, reference="dense", paired_calls=600,
            ratio_of_medians=1.123456, ratio_of_p95=1.234567, speedup_ratio_of_means=1.345678) for mid in r.METHODS[1:]])


def completed_fixture():
    families, instances = {}, []
    for family in r.FAMILIES:
        families[family] = {**family_value(family), "suites": {s: family_value(family) for s in r.SUITES}}
    for mid in r.METHODS:
        base = .72 if mid.startswith("B") else .7
        instances.append(dict(method_id=mid, **estimate(base), suites={s: estimate(base) for s in r.SUITES}))
    comparisons = {}
    for budget in r.BUDGETS:
        value = dict(**estimate(.02), seed_sample_std=.012345,
            per_seed={str(seed): estimate(.02) for seed in r.SEEDS})
        comparisons[f"B{budget}_minus_A{budget}"] = dict(left=f"B{budget}", right=f"A{budget}", positive_favors=f"B{budget}",
            **deepcopy(value), suites={s: deepcopy(value) for s in r.SUITES})
    stats = dict(method_ids=list(r.METHODS), suite_order=list(r.SUITES), training_seeds=list(r.SEEDS),
        unique_initial_states=1600, states_per_suite=400, final_trials=35200, primary_comparison="B128_minus_A128",
        bootstrap=dict(seed=20261016, repeats=10000, percentile_method="linear", seed_resampling=False, p_values_reported=False),
        instances=instances, families=families, comparisons=comparisons, limits="Explicit synthetic presentation fixture.")
    diagnostics = dict(selected_action_errors=[dict(suite=suite, method_id=mid, checkpoint_sha256="c" * 64,
        selected_update=1500, committed_samples=40000, action_error_task_macro=dict(teacher_l1=.0123456, demonstration_l1=.1234567),
        peak_cuda_memory_allocated_bytes=23 * 1024 ** 3) for suite in r.SUITES for mid in r.METHODS[4:]],
        AB_token_overlap=[dict(suite=suite, visual_tokens=budget, seed=seed,
            overlap_fraction_task_macro=.5432109, jaccard_task_macro=.4321098)
            for suite in r.SUITES for budget in r.BUDGETS for seed in r.SEEDS])
    cost = dict(actual_allocated_gpu_seconds=3700., actual_allocated_gpu_hours=1.0277777777777777, unique_jobs=3,
        gpu_seconds_by_mode=dict(acceptance=50., train=3600., profile=50.),
        jobs=[dict(job_id="1", mode="acceptance", status="FAILED", elapsed_seconds=50., gpus=1),
              dict(job_id="2", mode="train", status="COMPLETED", elapsed_seconds=3600., gpus=1),
              dict(job_id="3", mode="profile", status="TIMEOUT", elapsed_seconds=50., gpus=1)],
        scope="Synthetic: every allocation once, including failed/retried attempts; nested phase times not added.")
    return dict(version=r.ANALYSIS_VERSION, schema=r.SCHEMA, status="completed_core_analysis", synthetic=True,
        analysis_script_sha256=r.sha256(ROOT / "scripts/analyze_formal.py"),
        registration_sha256="a" * 64, evidence_manifest_sha256="b" * 64,
        read_evidence_sha256={"never_follow/sealed_final.json": "c" * 64},
        retained_failed_attempts=[dict(suite="libero_10", infrastructure_failures=1)],
        weights_loaded=False, sealed_state_values_read=False, main_experiment_delivery_complete=False,
        standalone_cache_cost=dict(status="pending_real_training_logs", not_assumed_zero=True,
            missing=["actual cache component times", "independent A/B cache replay"]),
        success=stats, latency={s: {p: profile(p) for p in ("full", "components")} for s in r.SUITES},
        diagnostics=diagnostics, cost=cost)


def write_input(tmp_path, data):
    path = tmp_path / "analysis.json"
    path.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    return path


def pending_fixture():
    return dict(version=r.ANALYSIS_VERSION, status="pending",
        analysis_script_sha256=r.sha256(ROOT / "scripts/analyze_formal.py"),
        missing=["global_freeze", "release", "libero_10:final trials"])


def test_pending_produces_only_missing_receipt_and_never_loads_plotting(tmp_path, monkeypatch):
    data = pending_fixture()
    data["success"] = {"forbidden_partial_estimate": .99}
    path = write_input(tmp_path, data)
    monkeypatch.setattr(r, "render_figures", lambda *a, **k: pytest.fail("pending rendered"))
    result = r.render(path, tmp_path / "pending", project_root=tmp_path)
    assert result["status"] == "pending" and result["missing"] == data["missing"]
    assert result["main_table_generated"] is False and result["artifacts"] == []
    assert [p.name for p in (tmp_path / "pending").iterdir()] == ["render_receipt.json"]
    assert result["input_sha256"] == r.sha256(path)
    assert "success" not in result


def test_missing_input_produces_only_explicit_pending(tmp_path):
    result = r.render(tmp_path / "missing.json", tmp_path / "pending", project_root=tmp_path)
    assert result["status"] == "pending" and result["input_sha256"] is None
    assert "missing.json" in result["missing"][0]
    assert not result["main_experiment_delivery_complete"]


@pytest.mark.parametrize("section", ["success", "latency", "diagnostics", "cost"])
def test_claimed_completed_but_incomplete_is_pending_without_figures(tmp_path, section):
    data = completed_fixture()
    del data[section]
    result = r.render(write_input(tmp_path, data), tmp_path / "out", project_root=tmp_path, synthetic=True)
    assert result["status"] == "pending" and section in result["missing"][0]
    assert len(list((tmp_path / "out").iterdir())) == 1


def test_missing_one_seed_never_renders_partial_success(tmp_path):
    data = completed_fixture()
    data["success"]["instances"] = [v for v in data["success"]["instances"] if v["method_id"] != "B64_seed41"]
    result = r.render(write_input(tmp_path, data), tmp_path / "out", project_root=tmp_path, synthetic=True)
    assert result["status"] == "pending"
    assert result["missing"] == ["success.instances:B64_seed41"]


@pytest.mark.parametrize("change,match", [
    (lambda d: d["success"].update(unique_initial_states=4800), "independent-state"),
    (lambda d: d["success"]["bootstrap"].update(seed_resampling=True), "bootstrap"),
    (lambda d: d["success"]["families"]["dense"].update(seed_sample_std=0), "Dense/uniform"),
    (lambda d: d["success"]["comparisons"]["B64_minus_A64"].update(positive_favors="A64"), "direction"),
    (lambda d: d["latency"]["libero_10"]["full"].update(primary_inference_latency=False), "timing summary"),
    (lambda d: d["latency"]["libero_10"]["full"]["primary"][0].update(count=599), "600 timed"),
    (lambda d: d["latency"]["libero_10"]["full"]["primary"][0].update(median=-1), "finite numeric"),
    (lambda d: d["latency"]["libero_10"]["full"].update(synthetic=False), "synthetic"),
    (lambda d: d["diagnostics"]["selected_action_errors"][0].update(committed_samples=4000), "5000-update"),
    (lambda d: d["standalone_cache_cost"].update(status="completed"), "standalone-cost"),
])
def test_invalid_scientific_summary_is_rejected_before_writing(tmp_path, change, match):
    data = completed_fixture()
    change(data)
    with pytest.raises(ValueError, match=match):
        r.render(write_input(tmp_path, data), tmp_path / "out", project_root=tmp_path, synthetic=True)
    assert not (tmp_path / "out").exists()


def test_nan_and_reversed_intervals_rejected():
    data = completed_fixture()
    data["success"]["families"]["B128"]["ci95_percentile"] = [float("nan"), .8]
    with pytest.raises(ValueError, match="finite numeric"):
        r.validate_completed(data, synthetic=True)
    data["success"]["families"]["B128"]["ci95_percentile"] = [.8, .6]
    with pytest.raises(ValueError, match="Reversed"):
        r.validate_completed(data, synthetic=True)


def test_source_binding_unknown_status_and_synthetic_opt_in(tmp_path):
    data = completed_fixture()
    path = write_input(tmp_path, data)
    with pytest.raises(ValueError, match="Synthetic"):
        r.render(path, tmp_path / "out", project_root=tmp_path)
    data["synthetic"] = False
    path = write_input(tmp_path, data)
    with pytest.raises(ValueError, match="Synthetic"):
        r.render(path, tmp_path / "out", project_root=tmp_path, synthetic=True)
    data["synthetic"] = True
    data["analysis_script_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source SHA"):
        r.render(write_input(tmp_path, data), tmp_path / "out", project_root=tmp_path, synthetic=True)
    data["analysis_script_sha256"] = r.sha256(ROOT / "scripts/analyze_formal.py")
    data["status"] = "partly_completed"
    with pytest.raises(ValueError, match="status"):
        r.render(write_input(tmp_path, data), tmp_path / "out", project_root=tmp_path, synthetic=True)
    assert not (tmp_path / "out").exists()


def test_output_is_new_and_sealed_file_name_is_rejected_before_read(tmp_path):
    path = write_input(tmp_path, pending_fixture())
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("preserve")
    with pytest.raises(ValueError, match="new project directory"):
        r.render(path, output, project_root=tmp_path)
    assert sentinel.read_text() == "preserve"
    with pytest.raises(ValueError, match="sealed"):
        r.render(tmp_path / "sealed_final.json", tmp_path / "out", project_root=tmp_path)
    with pytest.raises(ValueError, match="project"):
        r.render(path, tmp_path.parent / "outside-output", project_root=tmp_path)


def test_complete_fixture_values_are_copied_with_no_new_aggregation():
    data = completed_fixture()
    r.validate_completed(data, synthetic=True)
    tables = {t["stem"]: t for t in r.make_tables(data)}
    assert tables["main_success"]["rows"][0][4] == "72.00 ± 10.00 [67.00, 77.00]"
    assert "±" not in tables["main_success"]["rows"][0][1]
    assert len(tables["success_all_instances"]["rows"]) == 22 * 5
    assert len(tables["success_families"]["rows"]) == 10 * 5
    assert len(tables["paired_gains"]["rows"]) == 5 * 3 * 4
    assert len(tables["latency"]["rows"]) == 4 * (22 + 6)
    assert len(tables["action_memory"]["rows"]) == 72
    assert len(tables["token_overlap"]["rows"]) == 36
    assert tables["action_memory"]["rows"][0][3:6] == ["0.012346", "0.123457", "23.000"]
    assert tables["latency_ratios"]["rows"][0][2:] == ["1.1235", "1.2346", "1.3457"]
    assert tables["cost_jobs"]["rows"][0][2] == "FAILED"
    assert tables["cost_jobs"]["rows"][2][2] == "TIMEOUT"
    assert r.PENDING in tables["action_memory"]["rows"][0]
    for suite in r.SUITES:
        assert len(tables["components_" + suite]["rows"]) == 22 * 7
        points = r.plot_points(data, suite)
        assert len(points) == 10 + 18
        assert len([p for p in points if p["instance"]]) == 18
        for point in points:
            assert point["median_ms"] == 200.123
    # Deliberately distinct supplied summaries test pure copying, not pooling.
    data["latency"]["libero_10"]["full"]["seed_equal_weight_summaries"][0]["median"]["seed_mean"] = 123.456789
    assert next(p for p in r.plot_points(data, "libero_10") if p["family"] == "A256" and p["instance"] is None)["median_ms"] == 123.456789


def test_missing_memory_stays_pending_and_does_not_become_zero():
    data = completed_fixture()
    data["diagnostics"]["selected_action_errors"][0]["peak_cuda_memory_allocated_bytes"] = None
    r.validate_completed(data, synthetic=True)
    rows = next(t["rows"] for t in r.make_tables(data) if t["stem"] == "action_memory")
    assert rows[0][-2:] == [r.PENDING, r.PENDING]


def test_valid_analyzer_unspecified_cost_mode_is_preserved():
    data = completed_fixture()
    del data["cost"]["jobs"][0]["mode"]
    data["cost"]["gpu_seconds_by_mode"]["unspecified"] = data["cost"]["gpu_seconds_by_mode"].pop("acceptance")
    r.validate_completed(data, synthetic=True)
    rows = next(t["rows"] for t in r.make_tables(data) if t["stem"] == "cost_jobs")
    assert rows[0][1:3] == ["unspecified", "FAILED"]


def test_actual_analyzer_and_profiler_summary_contract():
    """Use real summary producers on synthetic arrays/calls, no GPU or states."""
    import numpy as np
    from cti_vla.evaluation.formal_profiling import summarize_formal_profile, balanced_schedule
    spec = importlib.util.spec_from_file_location("formal_analysis_render_contract", ROOT / "scripts/analyze_formal.py")
    analyzer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analyzer)
    data = completed_fixture()
    states = [[[f"synthetic:{suite}:{task}:{i}" for i in range(40)] for task in range(10)] for suite in r.SUITES]
    outcomes = np.arange(4 * 10 * 40 * 22).reshape(4, 10, 40, 22) % 3 != 0
    data["success"] = analyzer.summarize_success(outcomes, state_ids=states)
    for pass_name in ("full", "components"):
        ids = [f"synthetic-observation-{i}" for i in range(30)]
        episodes = {oid: f"synthetic-episode-{i // 3}" for i, oid in enumerate(ids)}
        schedule = balanced_schedule(ids)
        rows = []
        for order in schedule:
            for mid in order["method_order"]:
                for oid in ids:
                    row = dict(method=mid, observation_id=oid, episode_id=episodes[oid], round=order["round"], elapsed_ms=1.)
                    if pass_name == "components":
                        row["components"] = {phase: dict(host_ms=.1, cuda_stream_elapsed_ms=None if phase == "unclassified" else .01)
                            for phase in r.PHASES}
                    rows.append(row)
        raw = dict(version=r.PROFILE_VERSION, status="completed_measurement", pass_name=pass_name, synthetic=True,
            observation_ids=ids, observation_episodes=episodes, observations=30, episodes=10,
            method_ids=list(r.METHODS), methods={mid: {} for mid in r.METHODS}, rounds=20, warmups_per_instance=50,
            sample_policy_forwards=22 * (50 + 20 * 30), schedule=schedule, rows=rows)
        summary = summarize_formal_profile(raw)
        for suite in r.SUITES:
            data["latency"][suite][pass_name] = deepcopy(summary)
    r.validate_completed(data, synthetic=True)
    tables = {t["stem"]: t for t in r.make_tables(data)}
    assert len(tables["success_all_instances"]["rows"]) == 110
    assert len(tables["latency"]["rows"]) == 112


def test_actual_static_render_is_synthetic_hashed_and_keeps_all_seeds(tmp_path):
    pytest.importorskip("matplotlib")
    from PIL import Image
    source = write_input(tmp_path, completed_fixture())
    result = r.render(source, tmp_path / "synthetic-preview", project_root=tmp_path, synthetic=True)
    output = tmp_path / "synthetic-preview"
    assert result["status"] == "rendered_core_results_auxiliary_pending"
    assert result["synthetic"] is True and result["production_results"] is False
    assert result["main_experiment_delivery_complete"] is False
    assert result["main_table_generated"] is True and result["new_statistics_computed"] is False
    assert result["renderer_sha256"] == r.sha256(ROOT / "scripts/render_formal_results.py")
    assert result["input_sha256"] == r.sha256(source)
    for artifact in result["artifacts"]:
        assert artifact["path"].startswith("synthetic_")
        path = output / artifact["path"]
        assert artifact["sha256"] == r.sha256(path)
        assert artifact["bytes"] == path.stat().st_size
        if path.suffix == ".md":
            assert "SYNTHETIC — NOT EXPERIMENTAL RESULTS" in path.read_text(encoding="utf-8")
        if path.suffix == ".png":
            with Image.open(path) as image:
                assert image.width > 1000 and image.height > 500
                assert "SYNTHETIC" in image.info["Description"]
                assert result["input_sha256"] in image.info["Description"]
    pdf = output / "synthetic_formal_results.pdf"
    assert pdf.read_bytes().startswith(b"%PDF-")
    coordinates = json.loads((output / "synthetic_plot_coordinates.json").read_text())
    assert len(coordinates["points"]) == 4 * 28 and coordinates["synthetic"] is True
    assert len(list(output.glob("*.png"))) >= 20
    for seed in r.SEEDS:
        assert f"B64_seed{seed}" in (output / "synthetic_success_all_instances.md").read_text()
    assert "成本归属仍pending" in (output / "synthetic_README.md").read_text(encoding="utf-8")


def test_input_mutation_keeps_partial_output_without_success_receipt(tmp_path, monkeypatch):
    source = write_input(tmp_path, completed_fixture())
    def changed(*args, **kwargs):
        source.write_text("changed", encoding="utf-8")
        return "synthetic-test"
    monkeypatch.setattr(r, "render_figures", changed)
    with pytest.raises(ValueError, match="changed during rendering"):
        r.render(source, tmp_path / "out", project_root=tmp_path, synthetic=True)
    assert (tmp_path / "out").exists()
    assert not (tmp_path / "out" / "render_receipt.json").exists()


def test_disappearing_input_cannot_receive_a_success_receipt(tmp_path, monkeypatch):
    source = write_input(tmp_path, completed_fixture())
    def removed(*args, **kwargs):
        source.unlink()
        return "synthetic-test"
    monkeypatch.setattr(r, "render_figures", removed)
    with pytest.raises(ValueError, match="changed during rendering"):
        r.render(source, tmp_path / "out", project_root=tmp_path, synthetic=True)
    assert not (tmp_path / "out" / "render_receipt.json").exists()


def test_truthy_string_is_not_an_explicit_synthetic_marker(tmp_path):
    data = completed_fixture()
    data["synthetic"] = "true"
    with pytest.raises(ValueError, match="Synthetic"):
        r.render(write_input(tmp_path, data), tmp_path / "out", project_root=tmp_path, synthetic=True)

"""Synthetic-only formal statistics and immutable evidence audit tests."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation.formal_trials import expected_method_ids, make_final_release, ENVIRONMENT
from cti_vla.evaluation.teacher_diagnostics import json_signature

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("formal_analysis_under_test", ROOT / "scripts/analyze_formal.py")
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def registration():
    # Synthetic fields exactly sufficient to check the frozen scientific matrix.
    return dict(schema="formal_main_v2", suite_order=list(a.SUITES), budgets=[256, 128, 64], seeds=[17, 23, 41],
        training_arms=72, final_trials=35200, statistics=deepcopy(a.STATISTICAL_PROTOCOL))


def states():
    return [[[f"{suite}:{task}:{i}" for i in range(40)] for task in range(10)] for suite in a.SUITES]


def ref(tmp_path, name, payload, *, lines=False):
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in payload) if lines else json.dumps(payload), encoding="utf-8")
    return dict(path=path.relative_to(tmp_path).as_posix(), sha256=file_sha256(path))


@pytest.fixture(scope="module")
def statistics_fixture():
    methods = expected_method_ids()
    rng = np.random.default_rng(44)
    outcomes = rng.integers(0, 2, size=(4, 10, 40, 22)).astype(bool)
    # Three seed vectors cancel exactly within every initial-state cluster.
    # Independent seed resampling would incorrectly introduce uncertainty here.
    outcomes[..., methods.index("A128_seed17")] = True
    outcomes[..., methods.index("B128_seed17")] = False
    outcomes[..., methods.index("A128_seed23")] = False
    outcomes[..., methods.index("B128_seed23")] = True
    outcomes[..., methods.index("B128_seed41")] = outcomes[..., methods.index("A128_seed41")]
    result = a.summarize_success(outcomes, state_ids=states())
    return outcomes, result


def test_cluster_keeps_three_seeds_and_all_methods_together(statistics_fixture):
    outcomes, result = statistics_fixture
    contrast = result["comparisons"]["B128_minus_A128"]
    assert contrast["estimate"] == pytest.approx(0., abs=1e-15)
    assert contrast["ci95_percentile"] == pytest.approx([0., 0.], abs=1e-15)
    assert result["bootstrap"]["repeats"] == 10000
    assert result["bootstrap"]["seed"] == 20261016
    assert result["bootstrap"]["seed_resampling"] is False
    assert result["unique_initial_states"] == 1600 and result["final_trials"] == 35200
    assert [contrast["per_seed"][str(s)]["estimate"] for s in (17, 23, 41)] == [-1., 1., 0.]
    assert contrast["seed_sample_std"] == pytest.approx(1.)
    assert len(contrast["seed_task_pairs"]) == 4 * 10 * 3
    assert all(sum(r[k] for k in ("left_only", "right_only", "both", "neither")) == 40 for r in contrast["seed_task_pairs"])


def test_four_suites_tasks_and_seeds_equal_weight_and_seed_sample_sd(statistics_fixture):
    outcomes, result = statistics_fixture
    methods = expected_method_ids()
    family = result["families"]["A256"]
    indices = [methods.index(f"A256_seed{s}") for s in (17, 23, 41)]
    seed_means = outcomes[..., indices].mean(axis=(0, 1, 2))
    assert family["estimate"] == pytest.approx(seed_means.mean())
    assert family["seed_sample_std"] == pytest.approx(seed_means.std(ddof=1))
    assert [family["per_seed"][str(s)] for s in (17, 23, 41)] == pytest.approx(seed_means)
    assert result["families"]["dense"]["per_seed"] is None
    assert result["families"]["uniform64"]["seed_sample_std"] is None
    assert result["primary_comparison"] == "B128_minus_A128"
    assert len(result["comparisons"]) == 13
    assert not result["bootstrap"]["p_values_reported"]


def test_bootstrap_all22_share_draws_identical_methods_have_identical_intervals(statistics_fixture):
    outcomes, _ = statistics_fixture
    copied = outcomes.copy()
    copied[..., 4] = copied[..., 0]
    suite_draws, digest = a.cluster_bootstrap(copied)
    assert np.array_equal(suite_draws[..., 0], suite_draws[..., 4])
    again, digest2 = a.cluster_bootstrap(copied)
    assert digest == digest2 and np.array_equal(suite_draws, again)


def test_2pp_practical_goal_uses_lower_interval_not_point_or_zero_test(statistics_fixture):
    _, result = statistics_fixture
    for name, row in result["comparisons"].items():
        if row["right"] == "dense":
            assert row["practical_2pp_target_supported"] == (row["ci95_percentile"][0] > -.02)
    # A zero-centered interval can still support the -2pp target; equivalence
    # is never asserted and the target is not a non-significance test.
    assert "equivalent" not in json.dumps(result).lower()


def test_changed_preregistered_bootstrap_seed_or_weighting_is_rejected():
    reg = registration()
    reg["statistics"]["bootstrap_seed"] = 17
    with pytest.raises(ValueError, match="bootstrap"):
        a.require_registration(reg)


def test_2pp_exact_boundary_roundoff_does_not_cross_strict_target():
    result = a.interval(np.full(10000, -.02 + 2e-16), -.02)
    assert result["ci95_percentile"] == [-.02, -.02]
    assert not result["ci95_percentile"][0] > -.02


@pytest.mark.parametrize("bad", [np.zeros((4, 10, 40, 22)), np.zeros((4, 10, 120, 22), dtype=bool), np.zeros((1, 10, 40, 22), dtype=bool)])
def test_wrong_type_or_seed_inflated_initial_state_count_is_rejected(bad):
    with pytest.raises(ValueError, match="bool"):
        a.cluster_bootstrap(bad)


def test_json_sorted_roundtrip_retains_state_and_method_order(statistics_fixture):
    _, result = statistics_fixture
    value = json.loads(json.dumps(result, sort_keys=True))
    assert value == result
    assert value["state_ids"] == states() and value["method_ids"] == expected_method_ids()


def test_missing_freeze_release_pending_never_touches_final_reference(tmp_path, monkeypatch):
    reg = registration()
    manifest = dict(schema="formal_main_v2", kind="analysis_evidence", registration_sha256=json_signature(reg),
        suites={suite: {"runs": [{"trials": {"path": "sealed_final.json", "sha256": "a" * 64}}]} for suite in a.SUITES})
    monkeypatch.setattr(a.Evidence, "path", lambda *args: pytest.fail("final evidence touched before release"))
    result = a.analyze(manifest, reg, project_root=tmp_path)
    assert result["status"] == "pending" and set(result["missing"]) == {"global_freeze", "release"}
    assert result["main_table_generated"] is False and "success" not in result


def test_valid_gate_with_missing_results_reports_explicit_pending_no_fake_main_table(tmp_path):
    from test_formal_deployment import freeze_fixture
    reg, matrix = registration(), freeze_fixture()
    matrix["registration_sha256"] = json_signature(reg)
    release = make_final_release(matrix, registration_sha256=json_signature(reg), created_utc="synthetic")
    manifest = dict(schema="formal_main_v2", kind="analysis_evidence", registration_sha256=json_signature(reg),
        global_freeze=ref(tmp_path, "freeze.json", matrix), release=ref(tmp_path, "release.json", release))
    result = a.analyze(manifest, reg, project_root=tmp_path)
    assert result["status"] == "pending" and len(result["missing"]) == 23
    assert "libero_10:runs" in result["missing"] and "accounting" in result["missing"]
    assert "success" not in result and "latency" not in result
    assert result["standalone_cache_cost"]["status"] == "pending_real_training_logs"
    assert result["main_experiment_delivery_complete"] is False


@pytest.mark.parametrize("path", ["sealed_final.json", "init_states_test.json", "model.pt", "../other.json"])
def test_analysis_reader_never_opens_sealed_values_weights_or_outside_project(tmp_path, path):
    reader = a.Evidence(tmp_path)
    with pytest.raises(ValueError, match="never sealed"):
        reader.read({"path": path, "sha256": "a" * 64}, "forbidden")


def test_readonly_journal_keeps_incomplete_tail_and_rejects_corruption(tmp_path):
    reader = a.Evidence(tmp_path)
    path = tmp_path / "trials.jsonl"
    raw = b'{"event":"start"}\n{"event":'
    path.write_bytes(raw)
    with pytest.raises(a.PendingEvidence, match="tail retained"):
        reader.lines({"path": path.name, "sha256": file_sha256(path)}, "trial")
    assert path.read_bytes() == raw
    path.write_bytes(b'{bad json}\n')
    before = path.read_bytes()
    with pytest.raises(ValueError, match="without repair"):
        reader.lines({"path": path.name, "sha256": file_sha256(path)}, "trial")
    assert path.read_bytes() == before and len(list(tmp_path.iterdir())) == 1


def test_reader_rejects_changed_immutable_sha(tmp_path):
    reader = a.Evidence(tmp_path)
    reference = ref(tmp_path, "report.json", {"value": 1})
    reader.read(reference, "report")
    (tmp_path / "report.json").write_text('{"value":2}', encoding="utf-8")
    with pytest.raises(ValueError, match="changed while"):
        reader.unchanged()


def test_final_outcome_assembly_has_no_extra_seed_states_and_checks_paired_first_obs():
    ids, registries, rows = states(), {}, []
    for s, suite in enumerate(a.SUITES):
        registered = []
        for task in range(10):
            for index in range(40):
                tid = ids[s][task][index]
                registered.append(dict(task_id=task, source_state_index=index, trial_id=tid, initial_state_sha256="a" * 64))
                for mid in expected_method_ids():
                    rows.append(dict(suite=suite, state_trial_id=tid, initial_state_sha256="a" * 64,
                        task_id=task, method=mid, success=False, chunks=[dict(control_step=0, observation_sha256=f"obs:{tid}")]))
        registries[suite] = {"states": list(reversed(registered))}
    outcomes, observed = a.assemble_outcomes(registries, rows)
    assert outcomes.shape == (4, 10, 40, 22) and not outcomes.any() and observed == ids
    with pytest.raises(ValueError, match="duplicate"):
        a.assemble_outcomes(registries, rows + rows[:1])
    with pytest.raises(a.PendingEvidence, match="1 missing"):
        a.assemble_outcomes(registries, rows[:-1])
    changed = deepcopy(rows)
    changed[1]["chunks"][0]["observation_sha256"] = "other observation"
    with pytest.raises(ValueError, match="different raw observations"):
        a.assemble_outcomes(registries, changed)


def test_gpu_cost_counts_actual_shared_and_failed_jobs_once():
    jobs = [dict(job_id="1", experiment="formal_main_v2", status="COMPLETED", elapsed_seconds=100, gpus=1, mode="shared_cache"),
            dict(job_id="2", experiment="formal_main_v2", status="FAILED", elapsed_seconds=40, gpus=1, mode="training"),
            dict(job_id="3", experiment="formal_main_v2", status="COMPLETED", elapsed_seconds=200, gpus=1, mode="training"),
            dict(job_id="4", experiment="formal_main_v2", status="COMPLETED", elapsed_seconds=900, gpus=0, mode="cpu_data")]
    summary = a.summarize_cost({"jobs": jobs}, expected_job_ids=["1", "2", "3", "4"], observed_job_ids={"2", "3"})
    assert summary["actual_allocated_gpu_seconds"] == 340 and summary["unique_jobs"] == 4
    assert summary["gpu_seconds_by_mode"]["training"] == 240
    with pytest.raises(ValueError, match="duplicate"):
        a.summarize_cost({"jobs": jobs + jobs[:1]}, expected_job_ids=["1", "2", "3", "4"], observed_job_ids={"2", "3"})
    with pytest.raises(a.PendingEvidence, match="complete job inventory"):
        a.summarize_cost({"jobs": jobs}, expected_job_ids=["1", "2", "3", "4", "5"], observed_job_ids={"2", "3"})
    jobs[-1]["status"] = "RUNNING"
    with pytest.raises(a.PendingEvidence, match="nonterminal"):
        a.summarize_cost({"jobs": jobs}, expected_job_ids=["1", "2", "3", "4"], observed_job_ids={"2", "3"})


def test_all_terminal_failure_allocations_are_charged_without_cache_estimate():
    rows = [dict(job_id=str(i + 1), experiment="formal_main_v2", status=status, elapsed_seconds=7,
                 gpus=1, mode="failed_attempt") for i, status in enumerate(sorted(a.TERMINAL_JOBS))]
    result = a.summarize_cost({"jobs": rows}, expected_job_ids=[r["job_id"] for r in rows], observed_job_ids=set())
    assert result["actual_allocated_gpu_seconds"] == 7 * len(rows)
    assert "standalone_cache_estimate" not in result
    assert a.pending_cache_cost()["status"] == "pending_real_training_logs"
    rows[0]["job_id"] = None
    with pytest.raises(ValueError, match="job ID"):
        a.summarize_cost({"jobs": rows}, expected_job_ids=[r["job_id"] for r in rows], observed_job_ids=set())


def final_run_fixture(tmp_path):
    """One synthetic dense400-state run, with400 explicit policy errors."""
    from test_formal_deployment import freeze_fixture, synthetic_panel
    matrix, reg = freeze_fixture(), registration()
    matrix["registration_sha256"] = json_signature(reg)
    release = make_final_release(matrix, registration_sha256=json_signature(reg), created_utc="synthetic")
    registry, _ = synthetic_panel(suite="libero_10", split="final")
    identity = next(r for r in matrix["instances"] if r["suite"] == "libero_10" and r["method_id"] == "dense")
    manifest = dict(schema="formal_main_v2", kind="evaluation_execution", registration_sha256=json_signature(reg),
        split="final", suite="libero_10", environment={**ENVIRONMENT, "max_steps": 520}, methods=[{"identity": identity}],
        global_freeze=matrix, release=release)
    config = dict(schema="formal_main_v2", kind="evaluation_run", manifest=manifest, registration_sha256=json_signature(reg),
        runtime=dict(python="synthetic", torch="synthetic", numpy="synthetic", cuda="synthetic", gpu="synthetic"))
    signature = json_signature(config)
    events = [dict(event="invocation", slurm_job_id="999", run_signature=signature)]
    for state in registry["states"]:
        common = dict(trial_id=state["trial_id"] + ":dense", state_trial_id=state["trial_id"], method="dense", suite="libero_10",
            split="final", task_id=state["task_id"], task_name=state["task_name"], initial_state_sha256=state["initial_state_sha256"],
            source_state_index=state["source_state_index"], environment_seed=0, runtime_seed=17, configured_wait_steps=10,
            action_chunk=8, run_signature=signature)
        events.extend([{**common, "event": "start"}, {**common, "event": "result", "status": "policy_error",
            "success": False, "wait_steps": 10, "control_steps": 0, "policy_calls": 1, "chunks": [], "executed_actions": []}])
    refs = {"config": ref(tmp_path, "config.json", config), "trials": ref(tmp_path, "trials.jsonl", events, lines=True)}
    report = dict(schema="formal_main_v2", kind="evaluation_summary", suite="libero_10", split="final", status="completed",
        checkpoint_unchanged=True, expected_trials=400, completed_trials=400, unique_initial_states=400,
        trials_jsonl_sha256=refs["trials"]["sha256"], provenance={**config, "run_signature": signature},
        methods={"dense": dict(trials=400, successes=0, per_task={str(t): dict(trials=40, successes=0) for t in range(10)})})
    refs["report"] = ref(tmp_path, "report.json", report)
    return refs, registry, matrix, release, reg, events


def test_replay_includes_policy_errors_but_not_infrastructure_failures_as_outcomes(tmp_path):
    refs, registry, matrix, release, reg, events = final_run_fixture(tmp_path)
    rows, cost = a.read_final_run(a.Evidence(tmp_path), refs, registry=registry, matrix=matrix, release=release,
        registration_sha=json_signature(reg))
    assert len(rows) == cost["policy_errors"] == 400 and not any(r["success"] for r in rows)
    # Add a known failed infrastructure attempt before the first successful
    # terminal (policy-error) outcome: preserve charge, never add an outcome.
    start, terminal = events[1:3]
    infra = {**terminal, "status": "infrastructure_error"}
    events[1:1] = [deepcopy(start), infra]
    refs["trials"] = ref(tmp_path, "trials.jsonl", events, lines=True)
    report = json.loads((tmp_path / "report.json").read_text())
    report["trials_jsonl_sha256"] = refs["trials"]["sha256"]
    refs["report"] = ref(tmp_path, "report.json", report)
    rows, cost = a.read_final_run(a.Evidence(tmp_path), refs, registry=registry, matrix=matrix, release=release,
        registration_sha=json_signature(reg))
    assert len(rows) == 400 and cost["infrastructure_failures"] == 1


def test_replay_rejects_policy_error_called_success_and_duplicate_result(tmp_path):
    refs, registry, matrix, release, reg, events = final_run_fixture(tmp_path)
    events[2]["success"] = True
    refs["trials"] = ref(tmp_path, "trials.jsonl", events, lines=True)
    report = json.loads((tmp_path / "report.json").read_text())
    report["trials_jsonl_sha256"] = refs["trials"]["sha256"]
    refs["report"] = ref(tmp_path, "report.json", report)
    with pytest.raises(ValueError, match="cannot be counted"):
        a.read_final_run(a.Evidence(tmp_path), refs, registry=registry, matrix=matrix, release=release,
            registration_sha=json_signature(reg))
    events[2]["success"] = False
    events.insert(3, deepcopy(events[2]))
    refs["trials"] = ref(tmp_path, "trials.jsonl", events, lines=True)
    report["trials_jsonl_sha256"] = refs["trials"]["sha256"]
    refs["report"] = ref(tmp_path, "report.json", report)
    with pytest.raises(ValueError, match="lacks its start"):
        a.read_final_run(a.Evidence(tmp_path), refs, registry=registry, matrix=matrix, release=release,
            registration_sha=json_signature(reg))


def test_final_runtime_may_add_job_id_but_cannot_change_software(tmp_path):
    refs, registry, matrix, release, reg, _ = final_run_fixture(tmp_path)
    report = json.loads((tmp_path / "report.json").read_text())
    report["provenance"]["runtime"]["slurm_job_id"] = "999"
    refs["report"] = ref(tmp_path, "report.json", report)
    rows, _ = a.read_final_run(a.Evidence(tmp_path), refs, registry=registry, matrix=matrix, release=release,
        registration_sha=json_signature(reg))
    assert len(rows) == 400
    report["provenance"]["runtime"]["torch"] = "changed"
    refs["report"] = ref(tmp_path, "report.json", report)
    with pytest.raises(ValueError, match="runtime differs"):
        a.read_final_run(a.Evidence(tmp_path), refs, registry=registry, matrix=matrix, release=release,
            registration_sha=json_signature(reg))


def test_actual_episode_success_queue_is_replayed_and_changed_action_rejected(tmp_path):
    from cti_vla.evaluation.libero_runtime import run_episode, PolicyChunk, INPUTS_VERSION, ACTION_VERSION
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    refs, registry, matrix, release, reg, events = final_run_fixture(tmp_path)
    class Environment:
        def reset(self):
            self.steps = 0
        def set_init_state(self, state):
            return {"agentview_image": np.zeros((2, 2, 3), dtype=np.uint8),
                "robot0_eye_in_hand_image": np.zeros((2, 2, 3), dtype=np.uint8),
                "robot0_eef_pos": np.zeros(3), "robot0_eef_quat": np.array([0., 0., 0., 1.]),
                "robot0_gripper_qpos": np.zeros(2)}
        def step(self, action):
            self.steps += 1
            return self.set_init_state(None), 0., self.steps == 19, {}
    actions = np.zeros((8, 7), dtype=np.float32)
    metadata = dict(schema="formal_main_v2", suite="libero_10", method="dense", visual_tokens=512,
        per_camera_budgets=[256, 256], policy_calls=1, vision_calls=1, packing_calls=1, scorer_calls=0,
        future_head_calls=0, language_cache="disabled", inputs_version=INPUTS_VERSION,
        action_version=ACTION_VERSION, packing_version=PACKING_VERSION, retained_indices=list(range(512)))
    episode = run_episode(Environment(), lambda *_: PolicyChunk(actions, actions, metadata), "synthetic", [], max_steps=520)
    assert episode["success"] and episode["control_steps"] == 9 and episode["policy_calls"] == 2
    events[2].update(episode)
    refs["trials"] = ref(tmp_path, "trials.jsonl", events, lines=True)
    report = json.loads((tmp_path / "report.json").read_text())
    report["trials_jsonl_sha256"] = refs["trials"]["sha256"]
    report["methods"]["dense"]["successes"] = 1
    report["methods"]["dense"]["per_task"][str(events[2]["task_id"])]["successes"] = 1
    refs["report"] = ref(tmp_path, "report.json", report)
    rows, _ = a.read_final_run(a.Evidence(tmp_path), refs, registry=registry, matrix=matrix, release=release,
        registration_sha=json_signature(reg))
    assert sum(r["success"] for r in rows) == 1
    events[2]["executed_actions"][8][0] = .5
    refs["trials"] = ref(tmp_path, "trials.jsonl", events, lines=True)
    report["trials_jsonl_sha256"] = refs["trials"]["sha256"]
    refs["report"] = ref(tmp_path, "report.json", report)
    with pytest.raises(ValueError, match="differ from returned"):
        a.read_final_run(a.Evidence(tmp_path), refs, registry=registry, matrix=matrix, release=release,
            registration_sha=json_signature(reg))


def test_selected_validation_recomputed_for_all72_and_overlap_for_all36_pairs(tmp_path):
    from test_formal_deployment import checkpoint_fixture
    from cti_vla.evaluation.formal_trials import selector_instance_identity
    from cti_vla.evaluation.formal_runtime import uniform_formal_indices
    entries, instances, registered_pairs, manifests = [], [], [], {}
    for suite in a.SUITES:
        manifests[suite] = dict(validation_window_ids=[f"{suite}:w{t}" for t in range(10)],
            windows=[dict(window_id=f"{suite}:w{t}", episode_id=f"{suite}:ep{t}", task_id=t, split="validation") for t in range(10)])
        for budget in (256, 128, 64):
            for seed in (17, 23, 41):
                pair_ref = None
                for arm in ("A", "B"):
                    mid = f"{arm}{budget}_seed{seed}"
                    _, _, receipt, _, _ = checkpoint_fixture(tmp_path, suite=suite, total=budget, arm=arm, seed=seed)
                    observations = [{**w, "retained_indices": uniform_formal_indices(budget).tolist(),
                        "teacher_l1": .1, "demonstration_l1": .2} for w in manifests[suite]["windows"]]
                    val = dict(update=500, arm=arm, validation_metric=.1, observations=observations)
                    val_ref = ref(tmp_path, f"{suite}/{mid}/validation_00500.json", val)
                    receipt["evaluations"][1]["artifact_sha256"] = val_ref["sha256"]
                    if pair_ref is None:
                        pair_ref = ref(tmp_path, f"pairs/{suite}_k{budget}_seed{seed}.json", receipt["pair_config"])
                        registered_pairs.append(dict(suite=suite, visual_tokens=budget, seed=seed, **pair_ref))
                    identity = selector_instance_identity({**receipt["metadata"],
                        "selector_checkpoint_sha256": receipt["checkpoint_sha256"],
                        "deployment_receipt_sha256": json_signature(receipt), "f01_report_sha256": receipt["f01_report_sha256"]})
                    instances.append(identity)
                    report = dict(status="completed", training_updates_completed=5000, best_update=500,
                        best_checkpoint_sha256=receipt["checkpoint_sha256"], evaluations=receipt["evaluations"],
                        vla_parameters_unchanged=True, committed_samples=40000, next_sample_cursor=40000,
                        initial_scorer_sha256="a" * 64, sample_order_sha256="b" * 64, job_ids=[str(len(entries) + 1)])
                    entries.append(dict(suite=suite, method_id=mid, selected_validation=val_ref,
                        report=ref(tmp_path, f"{suite}/{mid}/training_report.json", report),
                        receipt=ref(tmp_path, f"{suite}/{mid}/deployment_receipt.json", receipt)))
    result, jobs = a.read_training_diagnostics(a.Evidence(tmp_path), entries, {"instances": instances},
        {"pairs": registered_pairs}, manifests)
    assert len(result["selected_action_errors"]) == len(jobs) == 72
    assert len(result["AB_token_overlap"]) == 36
    assert all(row["action_error_task_macro"]["teacher_l1"] == pytest.approx(.1) for row in result["selected_action_errors"])
    assert all(row["overlap_fraction_task_macro"] == row["jaccard_task_macro"] == 1. for row in result["AB_token_overlap"])
    # A raw selected validation edit cannot be hidden by keeping its summary.
    changed = deepcopy(entries)
    val = json.loads((tmp_path / changed[0]["selected_validation"]["path"]).read_text())
    val["observations"][0]["teacher_l1"] = 100.
    changed[0]["selected_validation"] = ref(tmp_path, "tampered_validation.json", val)
    with pytest.raises(ValueError, match="not the selected"):
        a.read_training_diagnostics(a.Evidence(tmp_path), changed, {"instances": instances}, {"pairs": registered_pairs}, manifests)
    missing_jobs = deepcopy(entries)
    report = json.loads((tmp_path / entries[0]["report"]["path"]).read_text())
    report.pop("job_ids")
    missing_jobs[0]["report"] = ref(tmp_path, "report_without_allocation_ids.json", report)
    with pytest.raises(a.PendingEvidence, match="allocation job IDs"):
        a.read_training_diagnostics(a.Evidence(tmp_path), missing_jobs, {"instances": instances}, {"pairs": registered_pairs}, manifests)


def test_cli_missing_evidence_manifest_outputs_pending(tmp_path, monkeypatch, capsys):
    reg = ref(tmp_path, "registration.json", registration())
    monkeypatch.setattr(a.sys, "argv", ["analyze_formal.py", "--registration", str(tmp_path / reg["path"]),
        "--evidence", str(tmp_path / "not_yet_created.json"), "--project-root", str(tmp_path)])
    a.main()
    value = json.loads(capsys.readouterr().out)
    assert value["status"] == "pending" and value["main_table_generated"] is False

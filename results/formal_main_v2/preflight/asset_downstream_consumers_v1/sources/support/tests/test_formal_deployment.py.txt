"""Synthetic CPU formal contracts; no real weights, final files, or GPU results."""
from copy import deepcopy
from contextlib import contextmanager
import importlib.util
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image
import pytest
import torch

from cti_vla.data.identity import file_sha256
from cti_vla.data.initial_states import initial_state_sha256
from cti_vla.data.experiment_protocol import signed_payload
from cti_vla.data.formal_initial_states import STATE_NAMESPACE, REGISTRY_NAMESPACE, split_state_indices
from cti_vla.evaluation import formal_runtime as runtime, formal_trials as trials, formal_acceptance as gates, libero_runtime
from cti_vla.evaluation.teacher_diagnostics import json_signature
from cti_vla.models.abstraction.packing import PACKING_VERSION
from cti_vla.selection import ConditionalInfluenceEstimator
from test_selector_runtime import VLA, Head, Env, STATS_KEY


@pytest.fixture(autouse=True)
def single_cpu_thread():
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


def pair_fixture(*, suite="libero_spatial", total=256, seed=17):
    return dict(schema=runtime.FORMAL_SCHEMA, suite=suite, seed=seed, tokens_per_camera=total // 2,
        training=dict(updates=5000, effective_batch=8), model_revision="synthetic-base", stats_key=suite + "_no_noops",
        scorer_dimensions=dict(token_dim=4, language_dim=4, proprio_dim=8, hidden_dim=8,
            num_cameras=2, patches_per_camera=256, max_instruction_tokens=128),
        selection=dict(metric=runtime.FORMAL_SELECTION_METRIC, updates=list(runtime.FORMAL_EVALUATION_UPDATES), tie_break="earliest_update"))


def checkpoint_fixture(tmp_path, *, suite="libero_spatial", total=256, arm="A", seed=17):
    pair = pair_fixture(suite=suite, total=total, seed=seed)
    config = {**pair, "arm": arm}
    sources = {"src/cti_vla/training/formal_future.py": "a" * 64}
    metadata = runtime.make_formal_checkpoint_metadata(arm=arm, seed=seed, scorer_dimensions=pair["scorer_dimensions"],
        training_config=config, pair_config=pair, window_manifest_sha256="b" * 64, model_revision=pair["model_revision"],
        stats_key=pair["stats_key"], training_source_files=sources, update=500, validation_metric=.1,
        input_acceptance_sha256="c" * 64, frozen_model_sha256="d" * 64, data_protocol_sha256="e" * 64,
        selection_protocol_sha256=json_signature(pair["selection"]), training_complete=True)
    saved = {**metadata, "estimator_state_dict": ConditionalInfluenceEstimator(**pair["scorer_dimensions"]).state_dict()}
    path = tmp_path / f"{suite}_{total}_{arm}_{seed}.pt"
    torch.save(saved, path)
    receipt = runtime.make_formal_deployment_receipt(path, metadata, training_config=config, pair_config=pair,
        f01_report_sha256="f" * 64, planned_updates=5000, completed_updates=5000,
        evaluations=[dict(update=i, validation_metric=.2 if i == 0 else .1) for i in runtime.FORMAL_EVALUATION_UPDATES])
    expected = {k: metadata[k] for k in ("suite", "visual_tokens", "per_camera_budgets", "model_revision", "stats_key", "input_version",
        "packing_version", "window_manifest_sha256", "input_acceptance_sha256", "frozen_model_sha256", "data_protocol_sha256", "selection_protocol_sha256")}
    expected["f01_report_sha256"] = "f" * 64
    return path, saved, receipt, expected, sources


@pytest.mark.parametrize("suite", runtime.FORMAL_SUITES)
@pytest.mark.parametrize("total", [256, 128, 64])
def test_new_schema_loads_exact_trained_budget_suite(tmp_path, suite, total):
    path, saved, receipt, expected, sources = checkpoint_fixture(tmp_path, suite=suite, total=total, arm="B")
    loaded = runtime.load_formal_selector_checkpoint(path, receipt, expected_versions=expected, expected_source_hashes=sources)
    assert loaded.provenance["visual_tokens"] == total
    assert loaded.provenance["future_head_deployed"] is False
    assert loaded.provenance["update"] == 500
    assert not hasattr(loaded, "future_head")
    identity = trials.selector_instance_identity(loaded.provenance)
    assert identity["method_id"] == f"B{total}_seed17"


@pytest.mark.parametrize("mutation", ["pilot", "budget", "suite", "source", "fingerprint", "partial", "missing_validation", "later_tie", "nan", "byte_change"])
def test_checkpoint_mismatch_never_reuses_pilot_or_changes_budget(tmp_path, mutation):
    path, saved, receipt, expected, sources = checkpoint_fixture(tmp_path)
    if mutation == "pilot":
        receipt["schema"] = "g1-future-v1"
    elif mutation == "budget":
        expected.update(visual_tokens=128, per_camera_budgets=[64, 64])
    elif mutation == "suite":
        expected["suite"] = "libero_10"
    elif mutation == "source":
        sources[next(iter(sources))] = "0" * 64
    elif mutation == "fingerprint":
        expected["frozen_model_sha256"] = "0" * 64
    elif mutation == "partial":
        receipt["completed_updates"] = 500
    elif mutation == "missing_validation":
        receipt["evaluations"].pop(2)
    elif mutation == "later_tie":
        receipt["evaluations"][0]["validation_metric"] = .1
    elif mutation == "nan":
        saved["estimator_state_dict"]["camera_embedding.weight"][0, 0] = float("nan")
        torch.save(saved, path)
        receipt["checkpoint_sha256"] = file_sha256(path)
    else:
        path.write_bytes(path.read_bytes() + b"mutated")
    with pytest.raises(ValueError):
        runtime.load_formal_selector_checkpoint(path, receipt, expected_versions=expected, expected_source_hashes=sources)


def test_uniform_grids_are_nested_and_128_is_exact_g0_rule():
    small, middle, large = [runtime.uniform_formal_indices(k) for k in (64, 128, 256)]
    assert np.array_equal(middle, libero_runtime.uniform128_indices())
    assert set(small) < set(middle) < set(large)
    for total, indices in zip((64, 128, 256), (small, middle, large)):
        assert len(indices) == len(set(indices)) == total
        assert np.all(indices[1:] > indices[:-1])
        assert (indices < 256).sum() == total // 2
    with pytest.raises(ValueError):
        runtime.uniform_formal_indices(32)


@pytest.mark.parametrize("suite", runtime.FORMAL_SUITES)
@pytest.mark.parametrize("method,total", [("dense", 512), ("uniform", 256), ("uniform", 128), ("uniform", 64), ("A", 256), ("B", 64)])
def test_one_pass_deployment_all_suites_and_baselines(tmp_path, monkeypatch, suite, method, total):
    class SuiteVLA(VLA):
        def _unnormalize_actions(self, actions, stats_key):
            assert stats_key == suite + "_no_noops"
            return actions.copy()
    vla = SuiteVLA()
    vla.norm_stats[suite + "_no_noops"] = vla.norm_stats[STATS_KEY]
    components = SimpleNamespace(vla=vla, action_head=Head(), proprio_projector=torch.nn.Linear(8, 4))
    loaded = None
    if method in ("A", "B"):
        path, _, receipt, expected, sources = checkpoint_fixture(tmp_path, suite=suite, total=total, arm=method)
        loaded = runtime.load_formal_selector_checkpoint(path, receipt, expected_versions=expected, expected_source_hashes=sources)
    def prepare(*_args, **_kwargs):
        ids = torch.tensor([[1, 17, 2]])
        return dict(pixel_values=torch.zeros(1), input_ids=ids, attention_mask=torch.ones_like(ids), normalized_proprio=torch.zeros(1, 8))
    monkeypatch.setattr(libero_runtime, "prepare_observation_inputs", prepare)
    policy = runtime.FormalRolloutPolicy(components, object(), suite=suite, method=method, total_tokens=total, selector=loaded)
    score_calls = []
    if loaded:
        def score(batch, retained):
            score_calls.append(retained.clone())
            return torch.zeros_like(batch.valid, dtype=torch.float32)
        monkeypatch.setattr(loaded.estimator, "forward", score)
    chunk = policy({}, "instruction")
    assert vla.vision_calls == len(vla.language_model.model.calls) == 1
    assert len(score_calls) == int(loaded is not None)
    assert chunk.metadata["future_head_calls"] == 0
    kept = chunk.metadata["retained_indices"]
    assert len(kept) == total and sum(i < 256 for i in kept) == total // 2
    assert kept == sorted(set(kept))
    call = vla.language_model.model.calls[0]
    assert call["inputs_embeds"].shape == (1, total + 62, 4)
    assert call["position_ids"][0, 1:total + 1].tolist() == [i + 1 for i in kept]
    assert call["position_ids"][0, total + 1].item() == 513
    assert not call["output_hidden_states"] and not call["use_cache"]
    assert components.action_head.hidden_shapes == [(1, 56, 4)]
    if method == "uniform":
        assert kept == runtime.uniform_formal_indices(total).tolist()


def synthetic_panel(suite="libero_10", split="development"):
    catalog = [dict(task_id=i, task_name=f"synthetic_task_{i}") for i in range(10)]
    source = {"synthetic_fixture": True, "files": [dict(task_id=i, source_file=f"synthetic_task_{i}.pruned_init", count=50) for i in range(10)]}
    states = []
    for task in catalog:
        indices = split_state_indices(task["task_name"])[0 if split == "development" else 1]
        for index in indices:
            values = [float(task["task_id"]), float(index), .25]
            states.append({**task, "trial_id": f"{suite}:{task['task_name']}:state-{index:04d}:env-0",
                "source_state_index": index, "source_file": task["task_name"] + ".pruned_init",
                "initial_state": values, "initial_state_sha256": initial_state_sha256(values)})
    common = dict(schema_version=2, suite=suite, split=split, environment_seed=0, source=source, task_catalog=catalog)
    if split == "development":
        return signed_payload({**common, "states": states}, STATE_NAMESPACE)
    registry = signed_payload({**common, "states": [{k: v for k, v in r.items() if k != "initial_state"} for r in states],
        "state_values_included": False}, REGISTRY_NAMESPACE)
    panel = signed_payload({**common, "states": states, "registry_signature": registry["content_signature"],
        "release_required": "root-complete-frozen-experiment-matrix"}, STATE_NAMESPACE)
    return registry, panel


def freeze_fixture():
    entries = []
    suites = {}
    for suite in runtime.FORMAL_SUITES:
        for method, total, seed in [("dense", 512, None), *[("uniform", k, None) for k in runtime.FORMAL_BUDGETS],
                *[(a, k, s) for k in runtime.FORMAL_BUDGETS for s in runtime.FORMAL_SEEDS for a in ("A", "B")]]:
            row = dict(schema=runtime.FORMAL_SCHEMA, suite=suite, method=method, visual_tokens=total, training_seed=seed,
                method_id=trials.method_id(method, total, seed), model_revision="synthetic-base", stats_key=suite + "_no_noops",
                config_sha256="a" * 64, frozen_model_sha256="b" * 64, source_sha256="c" * 64,
                input_acceptance_sha256="d" * 64, future_head_deployed=False)
            if method in ("A", "B"):
                row.update({k: "e" * 64 for k in ("checkpoint_sha256", "deployment_receipt_sha256", "pair_id",
                    "f01_report_sha256", "selection_protocol_sha256", "window_manifest_sha256", "data_protocol_sha256")})
                row["training_complete"] = True
            entries.append(row)
        suites[suite] = {**{k: "f" * 64 for k in ("development_panel_sha256", "development_completion_sha256",
            "final_registry_sha256", "panel_source_sha256")}, "development_completed": True,
            "development_unique_initial_states": 100, "development_method_ids": trials.expected_method_ids()}
    return dict(schema=runtime.FORMAL_SCHEMA, kind="global_final_freeze", registration_sha256="0" * 64, instances=entries, suites=suites)


@pytest.mark.parametrize("mutation", ["one_model_missing", "baseline_missing", "dev_incomplete", "base_mix", "head", "seed", "duplicate"])
def test_global_release_refuses_partial_matrix(mutation):
    matrix = freeze_fixture()
    trials.validate_freeze_matrix(matrix, registration_sha256="0" * 64)
    if mutation == "one_model_missing":
        matrix["instances"].pop()
    elif mutation == "baseline_missing":
        matrix["instances"].pop(0)
    elif mutation == "dev_incomplete":
        matrix["suites"]["libero_10"]["development_completed"] = False
    elif mutation == "base_mix":
        matrix["instances"][-1]["frozen_model_sha256"] = "0" * 64
    elif mutation == "head":
        matrix["instances"][-1]["future_head_deployed"] = True
    elif mutation == "seed":
        matrix["instances"][-1]["training_seed"] = 5
    else:
        matrix["instances"].append(matrix["instances"][0])
    with pytest.raises(ValueError):
        trials.make_final_release(matrix, registration_sha256="0" * 64, created_utc="synthetic")


def test_no_final_read_or_stat_before_complete_release(tmp_path, monkeypatch):
    accessed = []
    def forbidden(*args, **kwargs):
        accessed.append(args)
        raise AssertionError("final path touched")
    monkeypatch.setattr(trials, "file_sha256", forbidden)
    with pytest.raises(ValueError, match="root release"):
        trials.load_formal_panel(suite="libero_10", split="final", final_registry_path=tmp_path / "forbidden_registry",
            sealed_final_path=tmp_path / "forbidden_values", matrix=freeze_fixture(), registration_sha256="0" * 64)
    assert accessed == []


def test_release_opens_only_exact400_frozen_states_then_rejects_tamper(tmp_path):
    matrix = freeze_fixture()
    registry, panel = synthetic_panel(split="final")
    registry_path, panel_path, release_path = (tmp_path / name for name in ("registry.json", "sealed.json", "release.json"))
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    panel_path.write_text(json.dumps(panel), encoding="utf-8")
    matrix["suites"]["libero_10"].update(final_registry_sha256=file_sha256(registry_path), panel_source_sha256=json_signature(registry["source"]))
    release = trials.make_final_release(matrix, registration_sha256="0" * 64, created_utc="synthetic")
    release_path.write_text(json.dumps(release), encoding="utf-8")
    kwargs = dict(suite="libero_10", split="final", final_registry_path=registry_path, sealed_final_path=panel_path,
        release_path=release_path, release_file_sha256=file_sha256(release_path), matrix=matrix, registration_sha256="0" * 64)
    loaded = trials.load_formal_panel(**kwargs)
    assert len(loaded["states"]) == 400
    panel["states"][0]["initial_state"][0] += 1
    panel_path.write_text(json.dumps(panel), encoding="utf-8")
    with pytest.raises(ValueError):
        trials.load_formal_panel(**kwargs)


@pytest.mark.parametrize("suite,horizon", [("libero_spatial", 220), ("libero_object", 280), ("libero_goal", 300), ("libero_10", 520)])
def test_paired_trials_use_suite_horizon_and100_not_seed_replicates(tmp_path, monkeypatch, suite, horizon):
    panel = synthetic_panel(suite=suite)
    ledger = libero_runtime.TrialLedger(tmp_path / "trials.jsonl", run_signature="synthetic")
    seen = []
    def episode(env, policy, instruction, initial, **kwargs):
        seen.append(kwargs)
        return dict(status="completed", success=True, wall_seconds=.1, policy_calls=1)
    monkeypatch.setattr(trials, "run_episode", episode)
    policies = {"A256_seed17": object(), "B256_seed17": object()}
    trials.evaluate_formal_trials(panel, policies, ledger, lambda state: (Env(), state["task_name"]), reseed=lambda: None)
    assert len(seen) == 200 and all(k["max_steps"] == horizon and k["wait_steps"] == 10 for k in seen)
    summary = trials.summarize_formal_trials(panel, policies, ledger, provenance={}, checkpoint_unchanged=True)
    assert summary["status"] == "completed" and summary["unique_initial_states"] == 100
    assert all(value["success_rate"] == 1 for value in summary["methods"].values())
    assert trials.evaluate_formal_trials(panel, policies, ledger, lambda _: pytest.fail("duplicate execution"), reseed=lambda: None) == 0


def test_infrastructure_attempt_is_preserved_and_resumable(tmp_path, monkeypatch):
    panel = synthetic_panel()
    ledger = libero_runtime.TrialLedger(tmp_path / "trials.jsonl", run_signature="synthetic")
    def failed(_):
        raise OSError("synthetic infrastructure")
    with pytest.raises(RuntimeError, match="retained"):
        trials.evaluate_formal_trials(panel, {"dense": object()}, ledger, failed, reseed=lambda: None)
    assert not ledger.completed()
    monkeypatch.setattr(trials, "run_episode", lambda *args, **kwargs: dict(status="policy_error", success=False, policy_calls=1))
    trials.evaluate_formal_trials(panel, {"dense": object()}, ledger, lambda row: (Env(), row["task_name"]), reseed=lambda: None, stop_after=1)
    summary = trials.summarize_formal_trials(panel, ["dense"], ledger, provenance={})
    assert summary["completed_trials"] == 1 and summary["cost"]["recorded_result_attempts"] == 2
    assert summary["methods"]["dense"]["success_rate"] == 0


def test_fixed_acceptance_windows_and_seed_reuse_cannot_change_budget():
    candidates = [dict(window_id=f"t{t}e{e}s{s}", task_id=t, episode_id=e, start_step=s, split="train")
        for t in (0, 3, 5) for e in ("z", "a") for s in (8, 0)]
    selected = gates.select_formal_acceptance_windows(dict(suite="libero_10", windows=candidates), {"suite": "libero_10"})
    assert [r["window_id"] for r in selected] == [f"t{t}eas0" for t in (0, 3, 5)]
    config = pair_fixture(suite="libero_10")
    report = dict(schema=runtime.FORMAL_SCHEMA, kind="operator_acceptance", status="passed", execution="real_frozen_openvla_slurm",
        suite=config["suite"], stats_key=config["stats_key"], model_revision=config["model_revision"], visual_tokens=256,
        per_camera_budgets=[128, 128], accepted_pair_config=config, accepted_pair_id=json_signature(config),
        window_manifest_sha256="a" * 64, input_acceptance_sha256="b" * 64, frozen_model_sha256="c" * 64, source_files={"x": "d" * 64},
        input_version=libero_runtime.INPUTS_VERSION, packing_version=PACKING_VERSION, checkpoint_unchanged=True, test_opened=False,
        observations=[dict(window_id=r["window_id"], task_id=r["task_id"], checks={k: True for k in gates.OPERATOR_FLAGS},
            action_gradient_norm=.1, future_gradient_norm=.1, future_head_gradient_norm=.1, dense_max_abs=0., hard_max_abs=0.,
            deployment_max_abs=0., soft_gate_mass_per_camera=[128., 128.]) for r in selected])
    kwargs = dict(window_manifest_sha256="a" * 64, input_acceptance_sha256="b" * 64, source_files={"x": "d" * 64}, selected_windows=selected)
    gates.require_formal_acceptance(report, config={**config, "seed": 41}, **kwargs)
    with pytest.raises(ValueError, match="seed/run_id"):
        gates.require_formal_acceptance(report, config={**config, "seed": 23, "tokens_per_camera": 64}, **kwargs)
    report["observations"][0]["checks"]["future_gradient_to_die"] = False
    with pytest.raises(ValueError, match="check failed"):
        gates.require_formal_acceptance(report, config=config, **kwargs)


def test_real_operator_function_executes_gradients_and256_hard_deployment_on_cpu_fixture(monkeypatch):
    from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
    from cti_vla_baselines.acl_matched import FrozenDifferentiableOFTPolicy
    from cti_vla.training.future_auxiliary import frozen_future_target
    config = pair_fixture(total=256)
    vla = VLA()
    vla.projector = torch.nn.Linear(5, 4)
    raw = torch.randn(1, 512, 5)
    ids, attention, proprio = torch.tensor([[1, 17, 2]]), torch.ones(1, 3, dtype=torch.long), torch.zeros(1, 8)
    def vision(*args):
        return vla.projector(raw)
    monkeypatch.setattr(vla, "_process_vision_features", vision)
    monkeypatch.setattr(libero_runtime, "prepare_observation_inputs", lambda *args, **kwargs:
        dict(pixel_values=torch.zeros(1), input_ids=ids, attention_mask=attention, normalized_proprio=proprio))
    monkeypatch.setattr(gates, "raw_observation_bridge", lambda *_: {})
    components = SimpleNamespace(vla=vla, action_head=Head(), proprio_projector=torch.nn.Linear(8, 4))
    policy = OpenVLAOFTTokenPolicy(vla, components.action_head, components.proprio_projector, num_patches_full=512)
    student = FrozenDifferentiableOFTPolicy(policy, vla.projector, model_revision="synthetic-base", input_version=libero_runtime.INPUTS_VERSION)
    with torch.no_grad():
        visual = vla.projector(raw)
        teacher = policy.forward_from_full_tokens(visual, proprio, input_ids=ids, attention_mask=attention)
        record = dict(raw_tokens=raw, black_tokens=torch.randn_like(raw), visual=visual,
            language=vla.get_input_embeddings()(ids), input_ids=ids, attention_mask=attention, normalized_proprio=proprio,
            teacher_actions=teacher, demonstration_actions=teacher.clone(), future_target=frozen_future_target(torch.randn_like(visual)))
    before = gates.module_parameter_sha256(components)
    calls = []
    def query(kind, fn):
        calls.append(kind)
        return fn()
    result = gates.run_formal_operator_window(config=config, window=dict(window_id="synthetic", task_id=0, start_step=0),
        record=record, components=components, processor=object(), policy=policy, student=student,
        episode=SimpleNamespace(instructions=["first"]), query=query)
    assert gates.module_parameter_sha256(components) == before
    assert len(calls) == 7 and result["deployment_measured_calls"] == dict(vision=1, scorer=1, vla=1, head=0)
    assert result["action_gradient_norm"] > 0 and result["future_gradient_norm"] > 0


def test_rlds_inverse_raw_bridge_preserves_camera_and_proprio():
    rgb = np.arange(12 * 12 * 3, dtype=np.uint8).reshape(12, 12, 3)
    buffer = BytesIO()
    Image.fromarray(rgb).save(buffer, format="PNG")
    prop = np.array([.1, .2, .3, .2, .5, -.4, .02, -.02])
    episode = SimpleNamespace(images=[buffer.getvalue()], wrist_images=[buffer.getvalue()], proprio=[prop])
    observation = gates.raw_observation_bridge(episode, 0)
    assert np.array_equal(observation["agentview_image"], rgb[::-1, ::-1])
    assert np.allclose(libero_runtime.raw_proprio_from_observation(observation), prop, atol=1e-6, rtol=0)


def load_script(name):
    path = Path(__file__).resolve().parents[1] / "scripts" / name
    spec = importlib.util.spec_from_file_location("synthetic_" + name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_registered_capacity_cache_and_weights_paths_are_supported_without_widening_other_artifacts(tmp_path):
    acceptance = load_script("verify_formal_acceptance.py")
    evaluation = load_script("eval_formal_selector_libero.py")
    project, capacity = tmp_path / "source_project", tmp_path / "capacity_project"
    cache = capacity / "data/formal_main_v2/libero_10"
    checkpoint = capacity / "checkpoints/formal_main_v2/libero_10/k256/seed17/A/best.pt"
    assert acceptance.validate_feature_cache_path(project, cache, "libero_10", capacity_root=capacity) == cache.resolve()
    assert evaluation.resolve_project_path(project, checkpoint, checkpoint=True, capacity_root=capacity) == checkpoint.resolve()
    with pytest.raises(ValueError):
        acceptance.validate_feature_cache_path(project, capacity / "data/formal_main_v2/libero_object", "libero_10", capacity_root=capacity)
    with pytest.raises(ValueError):
        acceptance.validate_feature_cache_path(project, project / "models/scratch", "libero_10", capacity_root=capacity)
    with pytest.raises(ValueError):
        evaluation.resolve_project_path(project, checkpoint, capacity_root=capacity)
    with pytest.raises(ValueError):
        evaluation.resolve_project_path(project, capacity / "checkpoints/old_project/best.pt", checkpoint=True, capacity_root=capacity)
    # Match the actual registered server split without reading those paths.
    actual = acceptance.CAPACITY_ROOT / "data/formal_main_v2/libero_10"
    assert acceptance.validate_feature_cache_path(project, actual, "libero_10") == actual.resolve()


def test_component_hooks_observe_shared_packing_and_backbone_without_changing_output(monkeypatch):
    vla = VLA()
    components = SimpleNamespace(vla=vla, action_head=Head(), proprio_projector=torch.nn.Linear(8, 4))
    ids = torch.tensor([[1, 17, 2]])
    monkeypatch.setattr(libero_runtime, "prepare_observation_inputs", lambda *args, **kwargs:
        dict(pixel_values=torch.zeros(1), input_ids=ids, attention_mask=torch.ones_like(ids), normalized_proprio=torch.zeros(1, 8)))
    plain = runtime.FormalRolloutPolicy(components, object(), suite="libero_spatial", method="uniform", total_tokens=256)
    reference = plain({}, "first")
    stages, active = [], []
    @contextmanager
    def stage(name):
        assert not active
        active.append(name)
        stages.append(name)
        try:
            yield
        finally:
            active.pop()
    measured = runtime.FormalRolloutPolicy(components, object(), suite="libero_spatial", method="uniform", total_tokens=256, stage_context=stage)
    result = measured({}, "first")
    assert np.array_equal(reference.normalized_actions, result.normalized_actions)
    assert stages == ["preprocess", "vision", "condition_selection", "packing", "llm_action", "postprocess"]
    assert not active and not measured.token_policy.prefix_adapter.language_backbone._forward_pre_hooks


def test_operator_journal_prefix_is_verified_after_later_budget_append(tmp_path):
    path = tmp_path / "operator_calls.jsonl"
    rows = []
    for i, (window, kind) in enumerate((window, kind) for window in ("t0", "t3", "t5") for kind in gates.OPERATOR_PROBES):
        common = dict(call_id=i, window_id=window, kind=kind, job_id="synthetic", visual_tokens=128)
        rows.extend([dict(event="start", **common), dict(event="complete", seconds=.01, **common)])
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    report = dict(visual_tokens=128, job_id="synthetic", operator_journal_prefix_bytes=path.stat().st_size,
        operator_journal_prefix_sha256=file_sha256(path), operator_probes_completed=21,
        observations=[dict(window_id=f"t{i}") for i in (0, 3, 5)])
    gates.verify_formal_operator_journal(path, report)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(dict(event="start", call_id=21, visual_tokens=256)) + "\n")
    gates.verify_formal_operator_journal(path, report)
    report["operator_journal_prefix_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="prefix changed"):
        gates.verify_formal_operator_journal(path, report)


def test_incomplete_release_never_touches_final_paths_after_reading_release(tmp_path, monkeypatch):
    matrix = freeze_fixture()
    release = trials.make_final_release(matrix, registration_sha256="0" * 64, created_utc="synthetic")
    release_path = tmp_path / "release.json"
    release_path.write_text(json.dumps(release), encoding="utf-8")
    digest = file_sha256(release_path)
    matrix["instances"].pop()
    touched = []
    def safe_hash(path):
        touched.append(Path(path))
        assert Path(path) == release_path
        return file_sha256(path)
    monkeypatch.setattr(trials, "file_sha256", safe_hash)
    with pytest.raises(ValueError, match="all72"):
        trials.load_formal_panel(suite="libero_10", split="final", final_registry_path=tmp_path / "forbidden_registry",
            sealed_final_path=tmp_path / "forbidden_states", release_path=release_path, release_file_sha256=digest,
            matrix=matrix, registration_sha256="0" * 64)
    assert touched == [release_path]


def test_development_completion_is_reconstructed_from_all22_methods_raw_evidence(tmp_path, monkeypatch):
    panel = synthetic_panel()
    identities = [row for row in freeze_fixture()["instances"] if row["suite"] == "libero_10"]
    manifest = dict(schema=runtime.FORMAL_SCHEMA, kind="evaluation_execution", registration_sha256="0" * 64,
        suite="libero_10", split="development", environment={**trials.ENVIRONMENT, "max_steps": 520},
        methods=[dict(identity=row) for row in identities])
    config = dict(manifest=manifest, panel_signature=json_signature(panel))
    signature = json_signature(config)
    for name, value in (("config.json", config), ("panel.json", panel)):
        (tmp_path / name).write_text(json.dumps(value), encoding="utf-8")
    ledger = libero_runtime.TrialLedger(tmp_path / "trials.jsonl", run_signature=signature)
    methods = trials.expected_method_ids()
    # Synthetic durable completed evidence, with the exact22x100 identities.
    for state in panel["states"]:
        for method in methods:
            row = trials._identity(panel, state, method)
            ledger.append({**row, "event": "start"})
            ledger.append({**row, "event": "result", "status": "completed", "success": False, "policy_calls": 1})
    report = trials.summarize_formal_trials(panel, methods, ledger, provenance={"run_signature": signature}, checkpoint_unchanged=True)
    report_path = tmp_path / "closed_loop_report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    result = trials.audit_development_outputs([tmp_path], panel=panel, registration_sha256="0" * 64, expected_identities=identities)
    assert result["completed_trials"] == 2200 and result["unique_initial_states"] == 100
    report["methods"]["dense"]["successes"] = 1
    report_path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="durable raw"):
        trials.audit_development_outputs([tmp_path], panel=panel, registration_sha256="0" * 64, expected_identities=identities)


def test_engineering_weight_probe_stays_in_registered_server_suite_directory(tmp_path):
    script = load_script("verify_formal_acceptance.py")
    capacity = tmp_path / "capacity"
    expected = capacity / "checkpoints/formal_main_v2/engineering/libero_10"
    assert script.validate_engineering_checkpoint_path(None, "libero_10", capacity_root=capacity) == expected.resolve()
    assert script.validate_engineering_checkpoint_path(expected / "job17", "libero_10", capacity_root=capacity) == (expected / "job17").resolve()
    for path in (capacity / "checkpoints/formal_main_v2/engineering/libero_object", tmp_path / "local_weights"):
        with pytest.raises(ValueError, match="registered capacity"):
            script.validate_engineering_checkpoint_path(path, "libero_10", capacity_root=capacity)

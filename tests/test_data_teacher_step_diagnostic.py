"""CPU-only optional-teacher recovery/budget/provenance tests; no experiment."""

from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import shutil

import pytest
import torch

from cti_vla.data.experiment_protocol import load_experiment_protocol
from cti_vla.data.identity import file_sha256
from cti_vla.evaluation.teacher_diagnostics import (
    ActionQueryCache, atomic_json, json_signature, run_exact_selection,
)

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("optional_step_diagnostic", ROOT / "scripts/run_teacher_step_diagnostic.py")
step = importlib.util.module_from_spec(spec)
spec.loader.exec_module(step)
SCHEDULE = (192, 128, 96, 64, 48, 32)


def toy_forward(source, indices):
    value = source[:, indices[0]].square().mean() + .3 * source[:, indices[0]].mean()
    return value.expand(1, 8, 7).clone()


def write_in_memory_journal(oracle, path):
    """Serialize actual CPU query events, without thousands of test fsyncs."""
    events = [{"event": "identity", "schema_version": 1, "identity": oracle.identity,
               "identity_sha256": json_signature(oracle.identity)}]
    for request in oracle.requests:
        events.append(request)
        if request["event"] == "start":
            call = oracle.calls[request["call_id"]]
            if call["status"] == "complete":
                events.append({key: call[key] for key in ("event", "call_id", "seconds", "action", "action_sha256")})
            elif call["status"] == "failed":
                events.append({key: call[key] for key in ("event", "call_id", "seconds", "error")})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")


def test_registration_reconstructs_true_train_three_phases_and_rejects_tamper(tmp_path):
    protocol = load_experiment_protocol(ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")
    registration = step.load_registration(ROOT / "configs/manifests/spatial_g1_step_diagnostic_v1.json", protocol)
    assert [r["stage"] for r in registration["samples"]] == ["early", "middle", "late"]
    assert len({r["episode_id"] for r in registration["samples"]}) == 3
    assert registration["followup_per_camera_budgets"] == list(SCHEDULE)
    registration["samples"][0]["step_index"] += 1
    path = tmp_path / "tampered.json"
    atomic_json(path, registration)
    with pytest.raises(ValueError, match="signature"):
        step.load_registration(path, protocol)
    registration["content_signature"] = "sha256:" + json_signature({k: v for k, v in registration.items() if k != "content_signature"})
    atomic_json(path, registration)
    with pytest.raises(ValueError, match="samples/seeds"):
        step.load_registration(path, protocol)


def test_activation_requires_review_and_exact_source_hashes(tmp_path):
    path = tmp_path / "activation.json"
    receipt = {"schema_version": 1, "decision": "activate_optional_step_diagnostic", "main_g1_scientific_decision": "no_go",
               "registration_sha256": "reg", "g1_config_sha256": "config", "g1_finalization_sha256": "final",
               "d4_summary_sha256": "analysis", "reviewed_by": "CPU fixture, not authorization", "reviewed_utc": "fixture", "review_notes": "fixture"}
    evidence = {"config_sha256": "config", "finalization_sha256": "final"}
    atomic_json(path, receipt)
    assert step.require_activation(path, registration_sha="reg", evidence=evidence, analysis_sha="analysis") == receipt
    for key, value in (("d4_summary_sha256", "changed"), ("main_g1_scientific_decision", "go"), ("review_notes", "")):
        atomic_json(path, {**receipt, key: value})
        with pytest.raises(ValueError, match="reviewed no-go"):
            step.require_activation(path, registration_sha="reg", evidence=evidence, analysis_sha="analysis")


def test_snapshot_output_cache_and_weight_paths_are_separate(tmp_path):
    source, output, cache, weights, main = [tmp_path / p for p in ("snapshots/v1", "results/optional", "runtime/cache", "weights", "results/main")]
    step.validate_paths(tmp_path, output, source_root=source, cache=cache, checkpoint=weights, main=main)
    for bad in (source / "results", weights / "cache", main / "child", tmp_path.parent / "escape"):
        with pytest.raises(ValueError):
            step.validate_paths(tmp_path, output, source_root=source, cache=bad, checkpoint=weights, main=main)
    with pytest.raises(ValueError, match="source snapshot"):
        step.validate_paths(tmp_path, output, source_root=tmp_path.parent / "elsewhere")


def test_matching_version_strings_cannot_hide_changed_packing_implementation():
    config = {"source_snapshot": {path.relative_to(ROOT).as_posix(): file_sha256(path) for path in (ROOT / "src/cti_vla").rglob("*.py")}}
    step.verify_main_implementation(config)
    config["source_snapshot"]["src/cti_vla/models/abstraction/packing.py"] = "another-source"
    with pytest.raises(ValueError, match="implementation differs"):
        step.verify_main_implementation(config)


@pytest.fixture(scope="module")
def computed(tmp_path_factory):
    path = tmp_path_factory.mktemp("small-step-computed")
    visual = torch.arange(512, dtype=torch.float32)[None, :, None] / 512
    row = {"sample_id": 34, "episode_id": "toy-episode", "task_name": "toy-task", "stage": "middle", "is_last_step": False}
    main = ActionQueryCache(visual, toy_forward, identity={"config_sha256": "main", "sample": row, "input_sha256": "input"})
    original = run_exact_selection(main, sample_id=34, seed=517)
    config = {"main_input_identities": {"34": main.identity}, "main_full_actions": {"34": main.query(main.full_indices, category="full_reference").tolist()},
              "reference_atol": 1e-6, "followup_per_camera_budgets": list(SCHEDULE),
              "expected_checkpoint_verification": {"repository": "toy", "revision": "r", "file_count": 1, "total_bytes": 0}}
    oracle = ActionQueryCache(visual, toy_forward, identity={"config_sha256": json_signature(config), "sample": row, "input_sha256": "input"}, max_sample_forwards=2000)
    exact = run_exact_selection(oracle, sample_id=34, seed=517, per_camera_budgets=SCHEDULE)
    write_in_memory_journal(oracle, path / "queries/34.jsonl")
    atomic_json(path / "observations/34.json", {"status": "completed", "observation": row, "config_sha256": json_signature(config),
                "exact_selection": exact, "main_schedule_exact": original, "comparison": step.result_comparison(original, exact),
                "full_reference_max_abs_difference": 0.})
    return path, visual, row, config, {"34": original}, exact, oracle


def test_fresh_bound_and_identical_control_semantics(computed):
    _, _, _, _, originals, exact, oracle = computed
    assert 1500 < oracle.ledger()["unique_cached_actions"] <= 1604
    assert oracle.ledger()["sample_forwards_attempted"] == oracle.ledger()["unique_cached_actions"]
    assert [len(r["retained_indices"]) for r in exact["stage_labels"]] == [512, 384, 256, 192, 128, 96]
    comparison = step.result_comparison(originals["34"], exact)
    assert len(comparison) == 18
    for row in comparison:
        assert row["keep_count"] in (256, 128, 64)
        if row["method"] != "teacher_staged":
            assert row["main_retained_indices"] == row["followup_retained_indices"]
            assert row["followup_minus_main_mean_l1"] == 0


def test_partial_failure_recovery_has_no_free_attempts(tmp_path, computed):
    _, visual, row, config, _, exact, _ = computed
    calls = 0
    def failure(source, indices):
        nonlocal calls
        calls += 1
        if calls == 6:
            raise RuntimeError("synthetic interruption")
        return toy_forward(source, indices)
    path = tmp_path / "34.jsonl"
    kwargs = {"identity": {"config_sha256": json_signature(config), "sample": row, "input_sha256": "input"},
              "max_sample_forwards": 2000, "journal_path": path}
    oracle = ActionQueryCache(visual, failure, **kwargs)
    with pytest.raises(RuntimeError, match="interruption"):
        run_exact_selection(oracle, sample_id=34, seed=517, per_camera_budgets=SCHEDULE)
    assert oracle.ledger()["failed_calls"] == 1
    restored = ActionQueryCache(visual, toy_forward, **kwargs)
    # Memory appends keep this test fast after actual on-disk recovery.
    restored._append = lambda event: None
    recovered = run_exact_selection(restored, sample_id=34, seed=517, per_camera_budgets=SCHEDULE)
    step.d4_helpers().assert_same(recovered, exact)
    assert restored.ledger()["sample_forwards_attempted"] == restored.ledger()["unique_cached_actions"] + 1
    assert restored.ledger()["cache_hits"] >= 5


def test_2000_cap_counts_failed_and_unknown_calls_before_forward(tmp_path, computed):
    _, visual, row, config, *_ = computed
    identity = {"config_sha256": json_signature(config), "sample": row, "input_sha256": "input"}
    oracle = ActionQueryCache(visual, toy_forward, identity=identity, max_sample_forwards=2000)
    oracle.query(oracle.full_indices, category="toy")
    template = next(r for r in oracle.requests if r["event"] == "start")
    events = [{"event": "identity", "schema_version": 1, "identity": oracle.identity, "identity_sha256": json_signature(oracle.identity)}]
    for index in range(2000):
        events.append({**template, "call_id": index})
        if index < 1999:
            events.append({"event": "failed", "call_id": index, "seconds": .01, "error": "synthetic"})
    path = tmp_path / "queries/34.jsonl"
    path.parent.mkdir()
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    def must_not_call(*args):
        pytest.fail("cap must be checked before invoking policy")
    recovered = ActionQueryCache(visual, must_not_call, identity=identity, max_sample_forwards=2000, journal_path=path)
    with pytest.raises(RuntimeError, match="budget exhausted"):
        recovered.query(recovered.full_indices, category="retry")
    summary = step.summarize(tmp_path, config, [row], {})
    assert summary["completed_observations"] == 0
    assert summary["cost"]["sample_forwards_attempted"] == 2000
    assert summary["cost"]["failed_calls"] == 1999
    assert summary["cost"]["interrupted_calls_unknown_completion"] == 1
    assert summary["cost"]["policy_seconds_total"] is None


@dataclass(frozen=True)
class ToyVerification:
    repository: str = "toy"
    revision: str = "r"
    file_count: int = 1
    total_bytes: int = 0


def test_completed_json_needs_final_checkpoint_and_bound_journals(tmp_path, computed):
    path, _, row, config, originals, *_ = computed
    shutil.copytree(path, tmp_path, dirs_exist_ok=True)
    summary = step.summarize(tmp_path, config, [row], originals)
    assert summary["status"] == "awaiting_final_verification"
    with pytest.raises(ValueError, match="checkpoint verification"):
        step.finalize(tmp_path, config, [row], ToyVerification(revision="wrong"))
    step.finalize(tmp_path, config, [row], ToyVerification())
    assert step.summarize(tmp_path, config, [row], originals)["status"] == "completed"
    with (tmp_path / "queries/34.jsonl").open("a", encoding="utf-8") as stream:
        last = json.loads((tmp_path / "queries/34.jsonl").read_text().splitlines()[1])
        last.update(event="hit")
        stream.write(json.dumps(last) + "\n")
    with pytest.raises(ValueError, match="finalization no longer"):
        step.summarize(tmp_path, config, [row], originals)


def test_resume_recomputes_comparison_and_reference_not_stored_claims(tmp_path, computed):
    path, _, row, config, originals, *_ = computed
    shutil.copytree(path, tmp_path, dirs_exist_ok=True)
    file = tmp_path / "observations/34.json"
    result = step.read_json(file)
    result["comparison"][0]["followup_minus_main_mean_l1"] += 1
    atomic_json(file, result)
    with pytest.raises(ValueError, match="recomputation"):
        step.summarize(tmp_path, config, [row], originals)
    result = step.read_json(path / "observations/34.json")
    result["full_reference_max_abs_difference"] = 1.
    atomic_json(file, result)
    with pytest.raises(ValueError, match="full_reference_comparison"):
        step.summarize(tmp_path, config, [row], originals)
    with pytest.raises(ValueError, match="noise tolerance"):
        step.reference_difference(torch.ones(1, 8, 7) * 100, config, 34)


def test_interrupted_outer_attempt_retains_unknown_wall_and_cpu(tmp_path, computed):
    _, _, row, config, *_ = computed
    atomic_json(tmp_path / "attempts/dead.json", {"config_sha256": json_signature(config), "status": "running", "model_loading_seconds": 2.})
    summary = step.summarize(tmp_path, config, [row], {})
    assert summary["cost"]["attempts"]["unfinalized"] == 1
    assert summary["cost"]["attempts"]["wall_seconds_total"] is None
    assert summary["cost"]["attempts"]["cpu_seconds_total"] is None
    assert summary["cost"]["attempts"]["recorded_model_loading_seconds_lower_bound"] == 2.

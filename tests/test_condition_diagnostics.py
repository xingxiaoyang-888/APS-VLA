from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest
import torch

from cti_vla.data.experiment_protocol import load_experiment_protocol, signed_payload
from cti_vla.evaluation.condition_diagnostics import (FIXED_CANDIDATES, PAIR_NAMESPACE,
                                                     run_condition_pair, validate_pair_manifest)
from cti_vla.evaluation.libero_runtime import INPUTS_VERSION

ROOT = Path(__file__).resolve().parents[1]


def test_condition_references_are_independent_and_real_deletions_cost_18():
    visual = torch.arange(512, dtype=torch.float32).reshape(1, 512, 1)
    calls = []
    def bind(condition):
        def forward(full, retained):
            indices = retained[0].tolist()
            calls.append((condition, indices))
            # Large condition offset exposes accidental sharing of full refs;
            # distinct slopes give a known candidate-dependent label change.
            value = full[:, retained[0]].sum() * (condition + 1) / 512 + 100 * condition
            return value.expand(1, 8, 7).clone()
        return forward
    result = run_condition_pair(visual, [bind(0), bind(1)], identity={"instructions": ["target one", "target two"]})
    assert len(calls) == result["cost"]["sample_forwards_completed"] == 18
    assert [len(indices) for _, indices in calls] == ([512] + [511] * 8) * 2
    for condition in (0, 1):
        assert calls[condition * 9][1] == list(range(512))
        for j, token in enumerate(FIXED_CANDIDATES):
            assert calls[condition * 9 + j + 1][1] == [i for i in range(512) if i != token]
            assert result["conditions"][condition]["deletions"][j]["signed_label"] == pytest.approx(token * (condition + 1) / 512)
    assert result["label_difference_condition1_minus_condition0"] == pytest.approx([token / 512 for token in FIXED_CANDIDATES])


def test_completed_journals_resume_without_new_policy_queries(tmp_path):
    visual = torch.ones(1, 512, 2)
    calls = []
    def forward(full, indices):
        calls.append(indices.shape[1])
        return torch.full((1, 8, 7), float(indices.shape[1]))
    identity = {"instructions": ["target one", "target two"], "sample_id": 123}
    first = run_condition_pair(visual, [forward, forward], identity=identity, journal_directory=tmp_path)
    def forbidden(*args):
        raise AssertionError("resuming completed actions must not make new calls")
    second = run_condition_pair(visual, [forbidden, forbidden], identity=identity, journal_directory=tmp_path)
    assert len(calls) == 18 and second["cost"]["sample_forwards_attempted"] == 18
    assert second["cost"]["cache_hits"] == 18
    assert first["label_difference_condition1_minus_condition0"] == second["label_difference_condition1_minus_condition0"]
    with pytest.raises(ValueError, match="identity"):
        run_condition_pair(visual, [forbidden, forbidden], identity={**identity, "instructions": ["changed", "target two"]}, journal_directory=tmp_path)


def test_d1_rejects_changed_candidate_budget_and_missing_condition_identity():
    visual = torch.ones(1, 512, 2)
    forward = lambda full, indices: torch.ones(1, 8, 7)
    with pytest.raises(ValueError, match="candidate"):
        run_condition_pair(visual, [forward, forward], identity={"instructions": ["a", "b"]}, candidate_indices=range(8))
    with pytest.raises(ValueError, match="distinct"):
        run_condition_pair(visual, [forward, forward], identity={"instructions": ["a", "a"]})


def manifest():
    return json.loads((ROOT / "configs/manifests/spatial_d1_v1/pairs.json").read_text(encoding="utf-8"))


def protocol():
    return load_experiment_protocol(ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json")


def resign(payload):
    unsigned = deepcopy(payload)
    unsigned.pop("content_signature")
    return signed_payload(unsigned, PAIR_NAMESPACE)


def test_frozen_pair_has_formal_visual_review_and_one_preregistered_observation():
    value = manifest()
    validate_pair_manifest(value, protocol(), input_version=INPUTS_VERSION)
    assert len(value["pairs"]) == 1 and len(value["exclusions"]) == 3
    assert value["formal_d1_queries_before_freeze"] == 0
    assert value["pairs"][0]["sample_id"] == 8748964886254849455


@pytest.mark.parametrize("change", ["labels_seen", "unreviewed", "candidate_change", "identity_change"])
def test_manifest_rejects_unreviewed_or_posthoc_changes(change):
    value = manifest()
    if change == "labels_seen":
        value["labels_seen_before_freeze"] = True
    elif change == "unreviewed":
        value["pairs"][0]["visual_review"]["formal_crops_reviewed"] = False
    elif change == "candidate_change":
        value["pairs"][0]["candidate_indices"][0] = 0
    else:
        value["pairs"][0]["episode_id"] = "not-a-registered-training-episode"
    with pytest.raises((ValueError, KeyError)):
        validate_pair_manifest(resign(value), protocol(), input_version=INPUTS_VERSION)


def test_condition_input_view_changes_only_instruction():
    spec = importlib.util.spec_from_file_location("run_d1_test", ROOT / "scripts/run_condition_diagnostics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    episode = SimpleNamespace(num_steps=2, images=[b"main0", b"main1"], wrist_images=[b"wrist0", b"wrist1"],
                              proprio=torch.ones(2, 8), instructions=["original", "later"])
    changed = module.condition_episode(episode, 0, "alternative")
    assert changed.instructions == ["alternative", "later"] and episode.instructions == ["original", "later"]
    assert changed.images is episode.images and changed.wrist_images is episode.wrist_images and changed.proprio is episode.proprio


def test_final_cost_and_labels_are_reconciled_with_condition_journals(tmp_path):
    spec = importlib.util.spec_from_file_location("run_d1_reconcile_test", ROOT / "scripts/run_condition_diagnostics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pair = manifest()["pairs"][0]
    identity = {"config_sha256": "frozen", "pair": pair, "instructions": pair["instructions"]}
    visual = torch.arange(512, dtype=torch.float32).reshape(1, 512, 1)
    def forward(full, indices):
        return (full[:, indices[0]].sum() / 512).expand(1, 8, 7).clone()
    row = run_condition_pair(visual, [forward, forward], identity=identity,
                             journal_directory=tmp_path / "queries" / pair["pair_id"])
    row["pair"] = pair
    cost = module.reconcile_pair_queries(tmp_path, row, "frozen")
    assert cost["sample_forwards_attempted"] == cost["sample_forwards_completed"] == 18
    row["conditions"][0]["deletions"][0]["signed_label"] = 999
    with pytest.raises(ValueError, match="durable own-condition"):
        module.reconcile_pair_queries(tmp_path, row, "frozen")


def runner_module():
    spec = importlib.util.spec_from_file_location("run_d1_audit_test", ROOT / "scripts/run_condition_diagnostics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("interrupted", [False, True], ids=["failed", "start_only_interrupted"])
def test_failed_or_unknown_attempt_is_charged_and_resume_finishes_unique_panel(tmp_path, interrupted):
    module = runner_module()
    pair = manifest()["pairs"][0]
    identity = {"config_sha256": "frozen", "pair": pair, "instructions": pair["instructions"]}
    visual = torch.arange(512, dtype=torch.float32).reshape(1, 512, 1)
    journal = tmp_path / "queries" / pair["pair_id"]
    calls = []
    failure = KeyboardInterrupt if interrupted else RuntimeError

    def fail(full, indices):
        calls.append(indices.shape[1])
        raise failure("synthetic process interruption" if interrupted else "synthetic transient failure")

    with pytest.raises(failure):
        run_condition_pair(visual, [fail, fail], identity=identity, journal_directory=journal,
                           max_attempts_per_condition=12)

    def recover(full, indices):
        calls.append(indices.shape[1])
        return (full[:, indices[0]].sum() / 512).expand(1, 8, 7).clone()

    result = run_condition_pair(visual, [recover, recover], identity=identity,
                                journal_directory=journal, max_attempts_per_condition=12)
    result["pair"] = pair
    cost = module.reconcile_pair_queries(tmp_path, result, "frozen")
    assert len(calls) == cost["sample_forwards_attempted"] == 19
    assert cost["sample_forwards_completed"] == 18
    assert cost["failed_calls"] == int(not interrupted)
    assert cost["interrupted_calls_unknown_completion"] == int(interrupted)
    assert len(result["conditions"]) == 2
    assert all(len(row["deletions"]) == 8 for row in result["conditions"])
    if interrupted:
        assert result["conditions"][0]["cost"]["policy_seconds_total"] is None

    def forbidden(*args):
        raise AssertionError("completed results must be reused even with charged failed history")

    resumed = run_condition_pair(visual, [forbidden, forbidden], identity=identity,
                                 journal_directory=journal, max_attempts_per_condition=12)
    assert resumed["cost"]["sample_forwards_attempted"] == 19
    assert resumed["cost"]["sample_forwards_completed"] == 18
    assert resumed["label_difference_condition1_minus_condition0"] == result["label_difference_condition1_minus_condition0"]


def test_repeated_failure_cannot_exceed_frozen_attempt_budget(tmp_path):
    from cti_vla.evaluation.teacher_diagnostics import read_query_journal_ledger
    visual = torch.ones(1, 512, 2)
    identity = {"instructions": ["target one", "target two"]}
    calls = []

    def fail(full, indices):
        calls.append(indices.shape[1])
        raise RuntimeError("synthetic repeated failure")

    for _ in range(10):
        with pytest.raises(RuntimeError, match="synthetic repeated failure"):
            run_condition_pair(visual, [fail, fail], identity=identity, journal_directory=tmp_path,
                               max_attempts_per_condition=10)
    with pytest.raises(RuntimeError, match="budget exhausted"):
        run_condition_pair(visual, [fail, fail], identity=identity, journal_directory=tmp_path,
                           max_attempts_per_condition=10)
    ledger = read_query_journal_ledger(tmp_path / "condition_0.jsonl", expected_fields=identity)
    assert len(calls) == ledger["sample_forwards_attempted"] == ledger["failed_calls"] == 10
    assert ledger["sample_forwards_completed"] == 0
    assert not (tmp_path / "condition_1.jsonl").exists()


@pytest.mark.parametrize("interrupted", [False, True], ids=["failed", "start_only_interrupted"])
def test_partial_cost_recovers_durable_charge_without_pair_result(tmp_path, interrupted):
    module = runner_module()
    pair = manifest()["pairs"][0]
    identity = {"config_sha256": "frozen", "pair": pair, "instructions": pair["instructions"]}
    visual = torch.ones(1, 512, 2)
    failure = KeyboardInterrupt if interrupted else RuntimeError

    def fail(full, indices):
        raise failure("synthetic failure before pair JSON can be written")

    with pytest.raises(failure):
        run_condition_pair(visual, [fail, fail], identity=identity,
                           journal_directory=tmp_path / "queries" / pair["pair_id"],
                           max_attempts_per_condition=12)
    assert not (tmp_path / "pairs").exists()
    summary = module.summarize_partial_queries(tmp_path, [pair], "frozen", max_attempts_per_condition=12)
    assert summary["stage"] == "D1" and summary["status"] == "partial"
    assert summary["cost"]["sample_forwards_attempted"] == 1
    assert summary["cost"]["sample_forwards_completed"] == 0
    assert summary["cost"]["unique_successful_queries"] == 0
    assert summary["cost"]["failed_calls"] == int(not interrupted)
    assert summary["cost"]["interrupted_calls_unknown_completion"] == int(interrupted)
    assert summary["journals_present"] and summary["journals_missing"]
    if interrupted:
        assert summary["cost"]["policy_seconds_total"] is None
    else:
        assert summary["cost"]["policy_seconds_total"] == summary["cost"]["known_policy_seconds"]


def test_attempt_budget_cannot_change_when_resuming_journal(tmp_path):
    visual = torch.ones(1, 512, 2)
    identity = {"instructions": ["target one", "target two"]}

    def fail(full, indices):
        raise RuntimeError("synthetic failure")

    with pytest.raises(RuntimeError, match="synthetic failure"):
        run_condition_pair(visual, [fail, fail], identity=identity, journal_directory=tmp_path,
                           max_attempts_per_condition=12)
    with pytest.raises(ValueError, match="identity"):
        run_condition_pair(visual, [fail, fail], identity=identity, journal_directory=tmp_path,
                           max_attempts_per_condition=13)


def copy_review_evidence(target):
    for relative in ("results/g1_preflight/d1_visual_candidates", "results/g1_preflight/d1_processed_candidates"):
        shutil.copytree(ROOT / relative, target / relative)
    return target


def test_review_evidence_chain_matches_the_frozen_pair_and_all_exclusions(tmp_path):
    module = runner_module()
    evidence = copy_review_evidence(tmp_path)
    assert module.verify_pair_evidence(manifest(), evidence) is not None


@pytest.mark.parametrize("changed", ["prepared_receipt", "registry", "approved_png", "excluded_png", "raw_jpeg", "pair_proprio"])
def test_review_evidence_tampering_is_rejected_before_model_loading(tmp_path, changed):
    module = runner_module()
    evidence = copy_review_evidence(tmp_path)
    value = manifest()
    relative = {
        "prepared_receipt": "results/g1_preflight/d1_processed_candidates/prepared_images.json",
        "registry": "results/g1_preflight/d1_visual_candidates/candidates.json",
        "approved_png": "results/g1_preflight/d1_processed_candidates/8748964886254849455_main.png",
        "excluded_png": "results/g1_preflight/d1_processed_candidates/8751944970463498635_main.png",
        "raw_jpeg": "results/g1_preflight/d1_visual_candidates/8748964886254849455_wrist.jpg",
    }
    if changed == "pair_proprio":
        value["pairs"][0]["raw_proprio_sha256"] = "0" * 64
        value = resign(value)
    else:
        path = evidence / relative[changed]
        # Appended whitespace is valid in JSON and after an image trailer;
        # ordinary parsing alone cannot establish the frozen byte identity.
        path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError):
        module.verify_pair_evidence(value, evidence)


@pytest.mark.parametrize("gate", ["smoke", "failed_parity"])
def test_formal_d1_requires_g0_gate_before_loading_gpu(tmp_path, gate):
    module = runner_module()
    report = {"stage": "smoke", "status": "passed"} if gate == "smoke" else {
        "stage": "G0", "status": "passed", "dense_parity": {"passed": False}}
    gate_path = tmp_path / "gate.json"
    gate_path.write_text(json.dumps(report), encoding="utf-8")
    args = SimpleNamespace(
        pairs=ROOT / "configs/manifests/spatial_d1_v1/pairs.json",
        protocol=ROOT / "configs/manifests/spatial_g0g1_v1/protocol.json",
        checkpoint_manifest=ROOT / "configs/assets/openvla_oft_libero_spatial.json",
        libero_source=ROOT / "external/LIBERO", evidence_root=ROOT,
        g0_report=gate_path, checkpoint=tmp_path / "weights", cache_directory=tmp_path / "cache",
        data_directory=tmp_path / "data", output=tmp_path / "output",
        stats_key="libero_spatial_no_noops", prepare_only=False, max_attempts_per_condition=12)
    with pytest.raises(ValueError, match="G0"):
        module.run(args)
    assert not args.output.exists() and not args.cache_directory.exists()


def test_completed_pair_cannot_hide_missing_journal_as_zero_cost(tmp_path):
    module = runner_module()
    pair = manifest()["pairs"][0]
    identity = {"config_sha256": "frozen", "pair": pair, "instructions": pair["instructions"]}
    journal = tmp_path / "queries" / pair["pair_id"]
    forward = lambda full, indices: torch.full((1, 8, 7), float(indices.shape[1]))
    result = run_condition_pair(torch.ones(1, 512, 2), [forward, forward], identity=identity,
                                journal_directory=journal)
    result.update(pair=pair, config_sha256="frozen")
    saved = tmp_path / "pairs" / f"{pair['pair_id']}.json"
    saved.parent.mkdir()
    saved.write_text(json.dumps(result), encoding="utf-8")
    (journal / "condition_0.jsonl").unlink()
    with pytest.raises(ValueError):
        module.summarize_partial_queries(tmp_path, [pair], "frozen")


def test_rejected_invocation_does_not_rewrite_prior_accepted_summary(tmp_path, monkeypatch):
    module = runner_module()
    (tmp_path / "config.json").write_text(json.dumps({
        "pair_manifest_signature": manifest()["content_signature"],
        "per_condition_sample_forward_cap": 12}), encoding="utf-8")
    saved = tmp_path / "summary.json"
    saved.write_text('{"status":"completed","accepted_prior_run":true}', encoding="utf-8")
    prior = saved.read_bytes()

    def rejected(args):
        raise ValueError("new configuration was not accepted")

    monkeypatch.setattr(module, "_run", rejected)
    args = SimpleNamespace(output=tmp_path, pairs=ROOT / "configs/manifests/spatial_d1_v1/pairs.json")
    with pytest.raises(ValueError, match="not accepted"):
        module.run(args)
    assert saved.read_bytes() == prior


def test_finalized_condition_difference_is_recomputed_from_durable_labels(tmp_path):
    module = runner_module()
    pair = manifest()["pairs"][0]
    identity = {"config_sha256": "frozen", "pair": pair, "instructions": pair["instructions"]}
    forward = lambda full, indices: torch.full((1, 8, 7), float(indices.shape[1]))
    result = run_condition_pair(torch.ones(1, 512, 2), [forward, forward], identity=identity,
                                journal_directory=tmp_path / "queries" / pair["pair_id"])
    result["pair"] = pair
    result["label_difference_condition1_minus_condition0"][0] = 1e6
    result["mean_absolute_label_difference"] = 1e6 / 8
    with pytest.raises(ValueError):
        module.reconcile_pair_queries(tmp_path, result, "frozen")


def test_unreadable_query_journal_reports_unknown_cost_instead_of_zero(tmp_path):
    module = runner_module()
    pair = manifest()["pairs"][0]
    journal = tmp_path / "queries" / pair["pair_id"] / "condition_0.jsonl"
    journal.parent.mkdir(parents=True)
    journal.write_text('{"event":', encoding="utf-8")
    result = module.write_partial_summary(tmp_path, [pair], "frozen", status="failed",
                                          error="synthetic damaged-journal recovery")
    assert result["status"] == "failed" and result["cost"] is None
    assert result["checkpoint_unchanged"] is None
    assert result["cost_reconciliation_error"]
    assert json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))["cost"] is None
    assert journal.read_text(encoding="utf-8") == '{"event":'


@pytest.mark.parametrize("interrupted", [False, True], ids=["failed", "python_interrupt"])
def test_accepted_invocation_exception_persists_durable_partial_cost(tmp_path, monkeypatch, interrupted):
    from cti_vla.evaluation.teacher_diagnostics import json_signature
    module = runner_module()
    panel = manifest()
    pair = panel["pairs"][0]
    config = {"per_condition_sample_forward_cap": 12, "pair_manifest_signature": panel["content_signature"]}
    identity = {"config_sha256": json_signature(config), "pair": pair, "instructions": pair["instructions"]}
    failure = KeyboardInterrupt if interrupted else RuntimeError

    def fail(full, indices):
        raise failure("synthetic charged query failure")

    def accepted(args):
        args._active_d1_config, args._active_d1_pairs = config, panel
        return run_condition_pair(torch.ones(1, 512, 2), [fail, fail], identity=identity,
                                  journal_directory=tmp_path / "queries" / pair["pair_id"])

    monkeypatch.setattr(module, "_run", accepted)
    with pytest.raises(failure):
        module.run(SimpleNamespace(output=tmp_path))
    saved = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert saved["status"] == "failed" and saved["checkpoint_unchanged"] is None
    assert saved["cost"]["sample_forwards_attempted"] == 1
    assert saved["cost"]["sample_forwards_completed"] == 0
    assert saved["cost"]["failed_calls"] == int(not interrupted)
    assert saved["cost"]["interrupted_calls_unknown_completion"] == int(interrupted)
    if interrupted:
        assert saved["cost"]["policy_seconds_total"] is None

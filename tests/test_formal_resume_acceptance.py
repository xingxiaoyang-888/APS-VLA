"""Synthetic CPU validation of the real-GPU probe; never GPU acceptance evidence."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from test_future_auxiliary import example, cpu_threads
from test_formal_future import one_record, toy_config
from cti_vla.training import formal_future as formal
from cti_vla.training import formal_resume_acceptance as probe


def run_probe(example, tmp_path, monkeypatch):
    config = toy_config()
    # Only the miniature fixture's dimensions/model identity bypass production
    # validation. The actual5000 schedule and8-microbatch update remain intact.
    monkeypatch.setattr(probe, "validate_formal_training_config", lambda _: formal.FormalTrainingSpec(17, 64))
    example.vla.projector = example.student.visual_projector
    components = SimpleNamespace(vla=example.vla, action_head=example.teacher.action_head,
                                 proprio_projector=example.teacher.proprio_projector)
    rows = [{"task_id": task, "window_id": f"train{task}", "split": "train"} for task in (0, 3)]
    first = one_record(example.batch)
    second = {key: value[1:2] for key, value in {
        "visual": example.batch.conditions.visual, "language": example.batch.conditions.instruction_embeddings,
        "normalized_proprio": example.batch.conditions.normalized_proprio,
        **{name: getattr(example.batch, name) for name in ("raw_tokens", "black_tokens", "input_ids", "attention_mask",
            "teacher_actions", "demonstration_actions", "future_target")}}.items()}
    report = probe.run_formal_resume_acceptance(config=config, records=[first, second], windows=rows,
        student=example.student, components=components, checkpoint_root=tmp_path / "weights",
        events_path=tmp_path / "f03_calls.jsonl", job_id="synthetic", source_files={"fixture.py": "a" * 64},
        window_manifest_sha256="b" * 64, input_acceptance_sha256="c" * 64)
    return report


def gate(report, config=None):
    return probe.require_formal_resume_acceptance(report, config=config or report["accepted_pair_config"],
        source_files=report["source_files"], window_manifest_sha256=report["window_manifest_sha256"],
        input_acceptance_sha256=report["input_acceptance_sha256"], selected_windows=report["selected_windows"],
        frozen_model_sha256=report["frozen_model_sha256"])


def test_actual_save_reload_probe_matches_both_arms_and_restores_outer_rng(example, tmp_path, monkeypatch):
    before = formal.capture_rng()
    report = run_probe(example, tmp_path, monkeypatch)
    assert probe.compare_trees(before, formal.capture_rng())["equal"]
    assert report["status"] == "passed" and report["execution"] == "synthetic_cpu"
    assert report["actual_forward_backward_samples"] == 48
    assert report["planned_updates"] == 5000 and report["alpha_probe_updates"][1] > 1.99
    assert report["alpha_last"] == .1
    assert report["matched_ab_initialization"] is True
    for arm, result in report["arms"].items():
        assert all(result["checks"].values())
        assert all(row["equal"] for row in result["comparisons"].values())
        continuous = formal.load_torch(Path(result["continuous_step2_checkpoint"]))
        resumed = formal.load_torch(Path(result["resumed_step2_checkpoint"]))
        assert probe.compare_trees(continuous, resumed)["equal"]
        assert continuous["formal_selector"] is False and "estimator_state_dict" not in continuous
        assert continuous["next_sample_cursor"] == 16 and continuous["next_update"] == 3
        assert (continuous["head"] is None) == (arm == "A")
        assert continuous["optimizer"]["state"]
    assert probe.verify_resume_journal(tmp_path / "f03_calls.jsonl", report)["samples"] == 48
    with pytest.raises(ValueError, match="real-GPU"):
        gate(report)
    # In-memory schema exercise only: no synthetic report is persisted as GPU.
    declared = copy.deepcopy(report)
    declared["execution"] = "real_frozen_openvla_slurm"
    gate(declared)
    for seed in (17, 23, 41):
        for budget in (32, 64, 128):
            config = dict(declared["accepted_pair_config"], seed=seed, tokens_per_camera=budget, run_id="other")
            gate(declared, config)
    config = dict(declared["accepted_pair_config"], suite="libero_object")
    with pytest.raises(ValueError, match="differences"):
        gate(declared, config)
    declared["arms"]["B"]["checks"]["optimizer_equal"] = False
    with pytest.raises(ValueError, match="bitwise"):
        gate(declared)
    with pytest.raises(ValueError, match="already exists"):
        run_probe(example, tmp_path, monkeypatch)


def test_missing_rng_restore_is_detected_and_retained(example, tmp_path, monkeypatch):
    original = probe.restore_rng
    calls = []
    def omit_reload(state):
        calls.append(state)
        # First two restores are A/B reload; final one restores the outer RNG.
        if len(calls) >= 3:
            original(state)
    monkeypatch.setattr(probe, "restore_rng", omit_reload)
    report = run_probe(example, tmp_path, monkeypatch)
    assert report["status"] == "failed"
    assert all(row["checks"]["rng_probe_equal"] is False for row in report["arms"].values())
    assert all(row["checks"]["rng_equal"] is False for row in report["arms"].values())
    assert all(Path(row["resumed_step2_checkpoint"]).is_file() for row in report["arms"].values())
    assert probe.verify_resume_journal(tmp_path / "f03_calls.jsonl", report)["samples"] == 48


def test_missing_or_changed_journal_work_rejected_even_with_rehashed_report(example, tmp_path, monkeypatch):
    report = run_probe(example, tmp_path, monkeypatch)
    path = tmp_path / "f03_calls.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    sample = next(i for i, row in enumerate(rows) if row["event"] == "sample_end")
    rows.pop(sample)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    with pytest.raises(ValueError, match="identity"):
        probe.verify_resume_journal(path, report)
    report.update(journal_bytes=path.stat().st_size, journal_sha256=formal.file_sha256(path))
    with pytest.raises(ValueError, match="incomplete"):
        probe.verify_resume_journal(path, report)


def test_bitwise_comparison_detects_signed_zero_and_optimizer_mutation():
    left = {"tensor": torch.tensor([0., 1.]), "optimizer": {0: {"step": torch.tensor(2.)}}}
    right = copy.deepcopy(left)
    right["tensor"][0] = -0.
    assert torch.equal(left["tensor"], right["tensor"])
    comparison = probe.compare_trees(left, right)
    assert comparison["equal"] is False and comparison["reference_sha256"] != comparison["resumed_sha256"]
    right = copy.deepcopy(left)
    right["optimizer"][0]["step"] += 1
    assert probe.compare_trees(left, right)["differences"][0]["path"] == "state.optimizer.0.step"

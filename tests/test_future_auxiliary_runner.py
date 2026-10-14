"""CPU-only runner integration using real shared classes and a synthetic VLA.

Acceptance report writes are captured in memory. These tests never produce a
real-model F01 gate or touch a server/GPU.
"""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import torch
import pytest

from test_future_auxiliary import cpu_threads, example
from cti_vla.selection import ConditionalInfluenceEstimator
from cti_vla.training.future_auxiliary import FutureAuxiliaryHead


ROOT = Path(__file__).resolve().parents[1]


def runner_module():
    spec = importlib.util.spec_from_file_location("synthetic_g1f_runner_test", ROOT / "scripts/run_g1_future.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def one_record(batch):
    return {"visual": batch.conditions.visual[:1], "language": batch.conditions.instruction_embeddings[:1],
            "normalized_proprio": batch.conditions.normalized_proprio[:1],
            **{name: getattr(batch, name)[:1] for name in
               ("raw_tokens", "black_tokens", "input_ids", "attention_mask", "teacher_actions",
                "demonstration_actions", "future_target")}}


def test_runner_acceptance_calls_real_shared_loss_and_packing_on_cpu(example, monkeypatch, tmp_path):
    runner = runner_module()
    record = one_record(example.batch)
    # Include the real toy projector in the runner's byte-level frozen hash.
    example.vla.projector = example.student.visual_projector
    components = SimpleNamespace(vla=example.vla, action_head=example.teacher.action_head,
                                 proprio_projector=example.teacher.proprio_projector)
    monkeypatch.setattr(runner, "load_torch", lambda path: record)
    monkeypatch.setattr(runner, "file_hash", lambda path: "0" * 64)
    monkeypatch.setattr(runner, "source_hashes", lambda: {"synthetic_cpu_fixture": "1" * 64})
    for name in ("reset_peak_memory_stats", "synchronize"):
        monkeypatch.setattr(torch.cuda, name, lambda *a, **k: None)
    monkeypatch.setattr(torch.cuda, "max_memory_allocated", lambda: 0)
    monkeypatch.setattr(torch.cuda, "get_device_name", lambda: "synthetic CPU fixture, no GPU")
    monkeypatch.setenv("SLURM_JOB_ID", "synthetic-cpu-only")
    writes = []
    monkeypatch.setattr("cti_vla.evaluation.teacher_diagnostics.atomic_json", lambda path, value: writes.append((path, value)))
    config = {"seed": 17, "model_revision": "synthetic-model",
              "scorer_dimensions": {"token_dim": 8, "language_dim": 8, "proprio_dim": 8, "hidden_dim": 16}}
    args = SimpleNamespace(config=tmp_path / "synthetic-config", windows=tmp_path / "synthetic-windows", output=tmp_path)
    index = [{"path": "memory-only", "identity": {"window": {"window_id": "synthetic-window"}}}]
    report = runner.acceptance(args, config, index, components, example.teacher, example.student)
    # The fixture's cached teacher was computed at B=2 and replayed at B=1;
    # CPU GEMM may differ by a float32 ULP. Hard parity uses the same B=1 path.
    assert report["status"] == "passed" and report["dense_max_abs"] < 1e-6
    assert report["hard_max_abs"] == 0
    assert report["action_gradient_norm"] > 0 and report["future_gradient_norm"] > 0
    assert report["future_head_gradient_norm"] > 0
    assert report["checks"]["vla_parameters_unchanged"]
    assert report["hardware"] == "synthetic CPU fixture, no GPU"
    assert len(writes) == 1 and not list(tmp_path.iterdir())


def test_runner_validation_consumes_shared_hard_indices_and_future_head_api(example):
    runner = runner_module()
    record = one_record(example.batch)
    records = [({"identity": {"window": {"window_id": "synthetic-validation", "split": "validation"}}}, record)]
    scorer = ConditionalInfluenceEstimator(8, 8, 8, hidden_dim=16)
    head = FutureAuxiliaryHead(8)
    result = runner.validate_hard(scorer, head, records, example.teacher, example.student, alpha=.5)
    assert result["windows"] == 1
    row = result["observations"][0]
    assert len(row["retained_indices"]) == 128
    assert sum(i < 256 for i in row["retained_indices"]) == 64
    assert row["retained_indices"] == sorted(set(row["retained_indices"]))
    for key in ("validation_metric", "demonstration_l1", "future_mse", "future_zero_visual_mse", "future_reversed_action_mse"):
        assert 0 <= result[key] < float("inf")
    assert scorer.training
    assert all(p.grad is None for p in example.student.parameters())


@pytest.mark.parametrize("suite", [None, "libero_10"])
def test_runner_resumes_after_validation_zero_without_duplicate_history(example, monkeypatch, tmp_path, suite):
    """Exercise real two-update A/B loops and actual tiny checkpoint serialization.

    Ninety/sixty distinct synthetic window IDs satisfy the runner's panel size;
    their tensors intentionally reuse one fixture. No scientific data or gate
    is represented by this integration test.
    """
    runner = runner_module()
    record = one_record(example.batch)
    example.vla.projector = example.student.visual_projector
    components = SimpleNamespace(vla=example.vla, action_head=example.teacher.action_head,
                                 proprio_projector=example.teacher.proprio_projector)
    index = [{"path": f"memory-{split}-{i}", "identity": {"window": {
                "window_id": f"synthetic-{split}-{i}", "split": split}}}
             for split, count in [("train", 90), ("validation", 60)] for i in range(count)]
    original_load = runner.load_torch
    monkeypatch.setattr(runner, "load_torch", lambda path: record if str(path).startswith("memory-") else original_load(path))
    original_hash = runner.file_hash
    monkeypatch.setattr(runner, "file_hash", lambda path: original_hash(path) if Path(path).exists() else "0" * 64)
    monkeypatch.setattr(runner, "source_hashes", lambda: {"synthetic_cpu_fixture": "1" * 64})
    for name in ("reset_peak_memory_stats", "synchronize", "empty_cache"):
        monkeypatch.setattr(torch.cuda, name, lambda *a, **k: None)
    monkeypatch.setattr(torch.cuda, "max_memory_allocated", lambda: 0)
    monkeypatch.setenv("SLURM_JOB_ID", "synthetic-cpu-only")
    monkeypatch.setattr("cti_vla.evaluation.checkpoint_manifest.load_checkpoint_manifest", lambda path: None)
    monkeypatch.setattr("cti_vla.evaluation.checkpoint_manifest.verify_checkpoint_directory", lambda *a: None)
    writes = []
    monkeypatch.setattr("cti_vla.evaluation.teacher_diagnostics.atomic_json", lambda path, value: writes.append((path, value)))
    config = {"seed": 17, "model_revision": "synthetic-model", "stats_key": "synthetic-stats", "arms": ["A", "B"],
              "scorer_dimensions": {"token_dim": 8, "language_dim": 8, "proprio_dim": 8, "hidden_dim": 16,
                                    "num_cameras": 2, "patches_per_camera": 256, "max_instruction_tokens": 128},
              "training": {"updates": 2, "effective_batch": 1, "learning_rate": 1e-4, "weight_decay": .01,
                           "gradient_clip_norm": 1.},
              "selection": {"updates": [0, 2], "metric": "hard_validation_teacher_l1"},
              "future": {"weight_A": 0., "weight_B": .1}}
    args = SimpleNamespace(output=tmp_path / "synthetic-output", training_checkpoints=tmp_path / "synthetic-checkpoints",
                           windows=tmp_path / "synthetic-windows", checkpoint=tmp_path / "synthetic-base",
                           asset_manifest=tmp_path / "synthetic-assets", acceptance_report=tmp_path / "synthetic-F01")
    if suite is not None:
        config.update(suite=suite, stats_key="libero_10_no_noops")
        args.input_acceptance_report=tmp_path / "synthetic-input-acceptance"
    events = []
    interrupted = [False]

    def interrupt_once(path, row):
        events.append((path, row))
        if row["event"] == "update_start" and not interrupted[0]:
            interrupted[0] = True
            raise RuntimeError("synthetic interruption after validation0 checkpoint")

    monkeypatch.setattr(runner, "append_json", interrupt_once)
    with pytest.raises(RuntimeError, match="synthetic interruption"):
        runner.train_pair(args, config, index, components, example.teacher, example.student)
    resume = original_load(args.training_checkpoints / "A/resume.pt")
    assert resume["completed_update"] == 0
    assert [r["update"] for r in resume["evaluations"]] == [0]
    if suite is not None:
        assert resume["suite"]==suite and resume["input_acceptance_sha256"]=="0"*64
        assert resume["f01_report_sha256"]=="0"*64
        runner.save_torch(args.training_checkpoints / "A/resume.pt",{**resume,"input_acceptance_sha256":"f"*64})
        with pytest.raises(ValueError,match="another suite/input/F01"):
            runner.train_pair(args,config,index,components,example.teacher,example.student)
        runner.save_torch(args.training_checkpoints / "A/resume.pt",resume)
    report = runner.train_pair(args, config, index, components, example.teacher, example.student)
    assert report["status"] == "completed"
    for arm in ("A", "B"):
        result = report["arms"][arm]
        assert [r["update"] for r in result["evaluations"]] == [0, 2]
        assert result["vla_parameters_unchanged"] and result["training_updates_completed"] == 2
    assert report["arms"]["A"]["initial_scorer_sha256"] == report["arms"]["B"]["initial_scorer_sha256"]
    assert report["arms"]["A"]["sample_order_sha256"] == report["arms"]["B"]["sample_order_sha256"]
    assert sum(row["event"] == "update_end" for _, row in events) == 4

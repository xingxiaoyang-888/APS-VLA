"""CPU engineering evidence; no claim about real VLA success or GPU cost."""
import copy
import json
from pathlib import Path
import random

import numpy as np
import pytest
import torch

from test_future_auxiliary import example, cpu_threads
from cti_vla.training import formal_future as formal
from cti_vla.training.future_auxiliary import future_auxiliary_loss, hard_select_future


@pytest.fixture
def preserve_numerics(monkeypatch):
    enabled = torch.are_deterministic_algorithms_enabled()
    warn = torch.is_deterministic_algorithms_warn_only_enabled()
    benchmark, deterministic = torch.backends.cudnn.benchmark, torch.backends.cudnn.deterministic
    monkeypatch.setenv("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    yield
    torch.use_deterministic_algorithms(enabled, warn_only=warn)
    torch.backends.cudnn.benchmark, torch.backends.cudnn.deterministic = benchmark, deterministic


def test_training_numerics_scope_and_restore(preserve_numerics):
    before = (torch.backends.cuda.flash_sdp_enabled(), torch.backends.cuda.mem_efficient_sdp_enabled(),
              torch.backends.cuda.math_sdp_enabled())
    assert formal.configure_formal_training_numerics() == formal.FORMAL_NUMERICS
    with formal.formal_student_attention_context("cuda:0"):
        assert not torch.backends.cuda.flash_sdp_enabled()
        assert torch.backends.cuda.mem_efficient_sdp_enabled() and torch.backends.cuda.math_sdp_enabled()
    assert before == (torch.backends.cuda.flash_sdp_enabled(), torch.backends.cuda.mem_efficient_sdp_enabled(),
                      torch.backends.cuda.math_sdp_enabled())
    # Determinism must persist for backward after the forward-only context.
    assert torch.are_deterministic_algorithms_enabled()
    with pytest.raises(RuntimeError, match="injected"):
        with formal.formal_student_attention_context("cuda:0"):
            raise RuntimeError("injected forward error")
    assert torch.backends.cuda.flash_sdp_enabled() == before[0]
    with formal.formal_student_attention_context("cpu"):
        assert torch.backends.cuda.flash_sdp_enabled() == before[0]


def test_cuda_numerics_fail_closed(preserve_numerics, monkeypatch):
    formal.configure_formal_training_numerics()
    torch.use_deterministic_algorithms(True, warn_only=True)
    with pytest.raises(RuntimeError, match="not configured"):
        formal.formal_student_attention_context("cuda:0")
    monkeypatch.setattr(torch.cuda, "is_initialized", lambda: True)
    monkeypatch.setenv("CUBLAS_WORKSPACE_CONFIG", ":16:8")
    with pytest.raises(RuntimeError, match="before CUDA"):
        formal.configure_formal_training_numerics()


@pytest.mark.parametrize("budget", [32, 64])
@pytest.mark.parametrize("arm", ["A", "B"])
def test_historical_loss_and_gradients_identical(example, budget, arm):
    head = example.auxiliary if arm == "B" else None
    old = future_auxiliary_loss(example.scorer, example.student, example.batch, alpha=.7,
                               auxiliary_head=head, tokens_per_camera=budget)
    old.loss.backward()
    gradients = {name: value.grad.clone() for name, value in example.scorer.named_parameters()}
    head_gradients = None if head is None else {name: value.grad.clone() for name, value in head.named_parameters()}
    example.scorer.zero_grad(set_to_none=True)
    if head is not None:
        head.zero_grad(set_to_none=True)
    new = formal.formal_auxiliary_loss(example.scorer, example.student, example.batch, alpha=.7,
                                       auxiliary_head=head, tokens_per_camera=budget)
    new.loss.backward()
    for name in ("loss", "action_loss", "teacher_l1", "demonstration_l1", "gates", "predicted_actions"):
        assert torch.equal(getattr(old, name), getattr(new, name))
    for name, value in example.scorer.named_parameters():
        assert torch.equal(gradients[name], value.grad)
    if head is not None:
        for name, value in head.named_parameters():
            assert torch.equal(head_gradients[name], value.grad)
    example.scorer.eval()
    assert torch.equal(hard_select_future(example.scorer, example.batch.conditions, tokens_per_camera=budget).source_indices,
                       formal.formal_hard_select(example.scorer, example.batch.conditions, tokens_per_camera=budget).source_indices)


def test_new256_budget_gradients_and_one_hard_forward(example):
    output = formal.formal_auxiliary_loss(example.scorer, example.student, example.batch, alpha=2.,
        auxiliary_head=example.auxiliary, tokens_per_camera=128)
    output.loss.backward()
    assert sum(float(p.grad.abs().sum()) for p in example.scorer.parameters()) > 0
    assert sum(float(p.grad.abs().sum()) for p in example.auxiliary.parameters()) > 0
    assert torch.allclose(output.gates.reshape(2, 2, 256).sum(-1), torch.full((2, 2), 128.), atol=.002)
    example.student.require_frozen()
    example.scorer.eval()
    count = []
    hook = example.scorer.register_forward_hook(lambda *_: count.append(1))
    selected = formal.formal_hard_select(example.scorer, example.batch.conditions, tokens_per_camera=128).source_indices
    hook.remove()
    assert len(count) == 1 and selected.shape == (2, 256)
    assert (selected < 256).sum(-1).tolist() == [128, 128]
    assert (selected[:, 1:] > selected[:, :-1]).all()
    calls = example.vla.language_model.model.calls
    example.teacher.forward_from_full_tokens(example.batch.conditions.visual, example.batch.conditions.normalized_proprio,
        input_ids=example.batch.input_ids, attention_mask=example.batch.attention_mask, retained_indices=selected)
    assert example.vla.language_model.model.calls == calls + 1
    with pytest.raises(ValueError):
        hard_select_future(example.scorer, example.batch.conditions, tokens_per_camera=128)


@pytest.mark.parametrize("value", [True, 64., 0, 256, 31])
def test_budget_contract_is_exact(value):
    with pytest.raises(ValueError):
        formal.formal_budget(value)


def test_full_pool_cycle_rng_independence_and_task_equal_selection():
    pool = ["a", "b", "c", "d", "e", "f", "g"]
    before = random.getstate()
    order = formal.fixed_window_order(pool, seed=17, samples=20)
    assert random.getstate() == before
    assert set(order[:7]) == set(pool) and set(order[7:14]) == set(pool)
    assert len(order) == 20 and order == formal.fixed_window_order(pool, seed=17, samples=20)
    assert order != formal.fixed_window_order(pool, seed=23, samples=20)
    rows = [dict(task_id=0, teacher_l1=1., demonstration_l1=0.)] * 3 + [dict(task_id=1, teacher_l1=9., demonstration_l1=4.)]
    result = formal.aggregate_validation(rows)
    assert result["validation_metric"] == 5. and result["window_weighted_teacher_l1_diagnostic"] == 3.
    assert result["demonstration_l1"] == 2.
    assert formal.choose_earliest([{"update": 1000, "validation_metric": 1.},
                                   {"update": 500, "validation_metric": 1.}])["update"] == 500


def test_rng_weights_only_roundtrip(tmp_path):
    formal.seed_training_rng(123)
    state = formal.capture_rng()
    expected = (random.random(), np.random.rand(), torch.rand(7))
    path = tmp_path / "rng.pt"
    formal.atomic_torch_save(path, state)
    formal.seed_training_rng(999)
    formal.restore_rng(formal.load_torch(path))
    assert random.random() == expected[0] and np.random.rand() == expected[1]
    assert torch.equal(torch.rand(7), expected[2])


def one_record(batch):
    return {"visual": batch.conditions.visual[:1], "language": batch.conditions.instruction_embeddings[:1],
        "normalized_proprio": batch.conditions.normalized_proprio[:1],
        **{name: getattr(batch, name)[:1] for name in ("raw_tokens", "black_tokens", "input_ids", "attention_mask",
            "teacher_actions", "demonstration_actions", "future_target")}}


class ToyProvider:
    def __init__(self, batch):
        self.record = one_record(batch)
        self.train_window_ids = [f"train{i}" for i in range(5)]
        self.validation_window_ids = [f"validation{i}" for i in range(3)]
        self.rows = {name: dict(window_id=name, episode_id=split + str(i), split=split, task_id=i % 2)
            for split, names in (("train", self.train_window_ids), ("validation", self.validation_window_ids))
            for i, name in enumerate(names)}

    def get(self, window_id):
        assert window_id in self.rows
        return self.record


def toy_config(budget=64):
    return {"schema": formal.FORMAL_SCHEMA, "seed": 17, "tokens_per_camera": budget,
        "suite": "libero_10", "model_revision": "synthetic", "stats_key": "synthetic",
        "scorer_dimensions": {"token_dim": 8, "language_dim": 8, "proprio_dim": 8, "hidden_dim": 16,
            "num_cameras": 2, "patches_per_camera": 256, "max_instruction_tokens": 128}}


def toy_metadata(**kwargs):
    return {key: value for key, value in kwargs.items() if key not in ("training_config", "pair_config")}


def toy_receipt(path, metadata, **kwargs):
    assert metadata["training_complete"] is True
    assert "head" not in formal.load_torch(path)
    return {"checkpoint_sha256": formal.file_sha256(path), "metadata": metadata}


def run_toy(example, root, *, arm="B", provider=None, **kwargs):
    modules = {"vla": example.vla, "student": example.student}
    identity = {"frozen_model_sha256": formal.parameter_fingerprint(modules),
        "window_manifest_sha256": "a" * 64, "data_protocol_sha256": "b" * 64,
        "selection_protocol_sha256": "c" * 64, "input_acceptance_sha256": "d" * 64,
        "training_source_files": {"synthetic.py": "e" * 64}, "f01_report_sha256": "f" * 64}
    return formal.train_formal_arm(config=toy_config(), arm=arm,
        spec=formal.FormalTrainingSpec(17, 64, updates=4, effective_batch=2, validation_every=2, checkpoint_every=2),
        provider=provider or ToyProvider(example.batch), policy=example.teacher, student=example.student,
        frozen_modules=modules, identity=identity, output=root / "results", checkpoints=root / "weights",
        metadata_factory=toy_metadata, receipt_factory=toy_receipt, **kwargs)


def assert_state_equal(a, b):
    if isinstance(a, torch.Tensor):
        assert torch.equal(a, b)
    elif isinstance(a, dict):
        assert set(a) == set(b)
        for k in a:
            assert_state_equal(a[k], b[k])
    elif isinstance(a, (list, tuple)):
        assert len(a) == len(b)
        for x, y in zip(a, b):
            assert_state_equal(x, y)
    else:
        assert a == b


@pytest.mark.parametrize("arm", ["A", "B"])
def test_interrupted_optimizer_rng_next_window_resume_is_exact(example, tmp_path, monkeypatch, arm):
    original_loss = formal.formal_auxiliary_loss
    def stochastic_loss(*args, **kwargs):
        value = original_loss(*args, **kwargs)
        # Actual stochastic gradient changes expose missing Python, NumPy or
        # Torch RNG restoration; deterministic fixture-only tests would not.
        value.loss = value.loss * (.7 + .1 * random.random() + .1 * float(np.random.rand()) + .1 * torch.rand(()))
        return value
    monkeypatch.setattr(formal, "formal_auxiliary_loss", stochastic_loss)
    baseline = run_toy(example, tmp_path / "baseline", arm=arm)
    def interrupt(row):
        if row["update"] == 3:
            raise RuntimeError("injected after optimizer step before checkpoint")
    with pytest.raises(RuntimeError, match="injected"):
        run_toy(example, tmp_path / "resumed", arm=arm, progress=interrupt)
    partial = formal.load_torch(tmp_path / "resumed/weights/resume.pt")
    assert partial["completed_update"] == 2 and partial["next_sample_cursor"] == 4
    formal.seed_training_rng(654321)
    resumed = run_toy(example, tmp_path / "resumed", arm=arm, resume=True)
    continuous = formal.load_torch(tmp_path / "baseline/weights/resume.pt")
    recovered = formal.load_torch(tmp_path / "resumed/weights/resume.pt")
    for key in ("scorer", "head", "optimizer", "rng", "next_sample_cursor"):
        assert_state_equal(continuous[key], recovered[key])
    assert resumed["committed_samples"] == baseline["committed_samples"] == 8
    assert resumed["attempted_forward_backward_samples_completed"] == 10
    assert resumed["unique_committed_windows"] == 5 and resumed["effective_epochs"] == 1.6
    assert resumed["best_update"] == baseline["best_update"]
    assert resumed["best_validation_metric"] == baseline["best_validation_metric"]
    assert resumed["attempts"] == 2 and resumed["next_sample_cursor"] == 8
    example.student.require_frozen()


def test_segment_stop_preserves5000_style_schedule_and_no_deployment(example, tmp_path):
    partial = run_toy(example, tmp_path / "segment", stop_after_updates=2)
    assert partial["status"] == "checkpointed" and partial["planned_updates"] == 4
    assert partial["training_updates_completed"] == 2
    assert not (tmp_path / "segment/weights/best.pt").exists()
    assert not (tmp_path / "segment/results/deployment_receipt.json").exists()
    assert not (tmp_path / "segment/results/training_report.json").exists()
    events = [json.loads(line) for path in (tmp_path / "segment/results/attempts").glob("*/cost_events.jsonl") for line in path.read_text().splitlines()]
    steps = [row for row in events if row["event"] == "update_end"]
    assert steps[-1]["alpha"] > .1  # segment is not treated as an entire schedule
    resumed = run_toy(example, tmp_path / "segment", resume=True)
    baseline = run_toy(example, tmp_path / "baseline")
    assert resumed["best_validation_metric"] == baseline["best_validation_metric"]
    assert_state_equal(formal.load_torch(tmp_path / "segment/weights/resume.pt")["scorer"],
                       formal.load_torch(tmp_path / "baseline/weights/resume.pt")["scorer"])


def test_a_b_initial_selector_behavior_and_order_match(example, tmp_path):
    a = run_toy(example, tmp_path / "A", arm="A")
    b = run_toy(example, tmp_path / "B", arm="B")
    assert a["initial_scorer_sha256"] == b["initial_scorer_sha256"]
    assert a["sample_order_sha256"] == b["sample_order_sha256"]
    a0 = json.loads(Path(a["evaluations"][0]["artifact_path"]).read_text())
    b0 = json.loads(Path(b["evaluations"][0]["artifact_path"]).read_text())
    assert a0["observations"] == b0["observations"]
    assert a["future_head_parameters"] == 0 and b["future_head_parameters"] > 0


def test_wall_stop_commits_whole_update_without_extra_selection_point(example, tmp_path):
    partial = run_toy(example, tmp_path / "wall", max_wall_seconds=.00001)
    assert partial["training_updates_completed"] == 1
    assert [row["update"] for row in partial["evaluations"]] == [0]
    assert partial["next_sample_cursor"] == 2
    saved = formal.load_torch(tmp_path / "wall/weights/resume.pt")
    assert saved["completed_update"] == 1 and saved["next_sample_cursor"] == 2
    resumed = run_toy(example, tmp_path / "wall", resume=True)
    baseline = run_toy(example, tmp_path / "baseline")
    assert resumed["best_validation_metric"] == baseline["best_validation_metric"]
    assert_state_equal(formal.load_torch(tmp_path / "wall/weights/resume.pt")["optimizer"],
                       formal.load_torch(tmp_path / "baseline/weights/resume.pt")["optimizer"])


def test_atomic_checkpoint_failure_keeps_previous_complete_file(tmp_path, monkeypatch):
    path = tmp_path / "resume.pt"
    formal.atomic_torch_save(path, {"update": 50, "value": torch.ones(2)})
    original = formal.os.replace
    def fail(*args, **kwargs):
        raise OSError("injected pre-commit filesystem failure")
    monkeypatch.setattr(formal.os, "replace", fail)
    with pytest.raises(OSError, match="pre-commit"):
        formal.atomic_torch_save(path, {"update": 100, "value": torch.zeros(2)})
    assert formal.load_torch(path)["update"] == 50
    assert torch.equal(formal.load_torch(path)["value"], torch.ones(2))


def test_resume_rejects_changed_cost_prefix_and_cursor(example, tmp_path):
    run_toy(example, tmp_path, stop_after_updates=2)
    saved = formal.load_torch(tmp_path / "weights/resume.pt")
    saved["next_sample_cursor"] += 1
    formal.atomic_torch_save(tmp_path / "weights/resume.pt", saved)
    with pytest.raises(ValueError, match="cursor"):
        run_toy(example, tmp_path, resume=True)
    saved["next_sample_cursor"] -= 1
    formal.atomic_torch_save(tmp_path / "weights/resume.pt", saved)
    prefix_path = Path(saved["cost_ledger_prefix"]["path"])
    prefix_path.write_bytes(b"x" + prefix_path.read_bytes()[1:])
    with pytest.raises(ValueError, match="ledger prefix"):
        run_toy(example, tmp_path, resume=True)


def test_episode_split_guard(example):
    provider = ToyProvider(example.batch)
    provider.rows[provider.validation_window_ids[0]]["episode_id"] = "train0"
    with pytest.raises(ValueError, match="leakage"):
        formal.validate_provider_partition(provider)


def test_registered_production_configs_and_reject_small_pilot():
    root = Path(__file__).resolve().parents[1]
    files = list((root / "configs/experiments/formal_main_v2").glob("*.json"))
    assert len(files) == 36
    for path in files:
        spec = formal.validate_formal_training_config(json.loads(path.read_text(encoding="utf-8")))
        assert spec.updates == 5000 and spec.validation_updates == list(range(0, 5001, 500))
    value = json.loads(files[0].read_text(encoding="utf-8"))
    value["training"]["updates"] = 100
    with pytest.raises(ValueError, match="registration"):
        formal.validate_formal_training_config(value)

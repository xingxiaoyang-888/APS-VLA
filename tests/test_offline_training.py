"""Synthetic CPU checks; temporary toy checkpoints are not research training."""

from dataclasses import asdict, replace
import json
import random
import importlib.util
from argparse import Namespace
from pathlib import Path

import numpy as np
import pytest
import torch
from torch import nn

from cti_vla.data.experiment_protocol import ExperimentProtocol, load_experiment_protocol
from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
from cti_vla.labeling import DeletionTeacher, LabelProvenance
from cti_vla.labeling.deletion import LABEL_VERSION
from cti_vla.selection import ConditionalInfluenceEstimator, ConditionalTokenBatch
from cti_vla.training.offline import (
    OFFLINE_CACHE_VERSION, OfflineDataset, OfflineObservation, OfflineTrainConfig,
    initial_training_assignments, load_offline_observation, require_g1,
    sample_initial_sets, save_offline_observation, seed_training, train_offline, validate_packed,
)
from cti_vla.training.conditional import TrainingLabelScale


@pytest.fixture
def protocol():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    real = load_experiment_protocol(root / "configs/manifests/spatial_g0g1_v1/protocol.json")
    manifests = dict(real.manifests)
    for split in ("train", "validation"):
        source = manifests[split]
        episode = next(e for e in source.episodes if e.episode_id not in real.excluded_episode_ids)
        manifests[split] = replace(source, episodes=(episode,), samples=tuple(s for s in source.samples if s.episode_id == episode.episode_id))
    return ExperimentProtocol(real.path, dict(real.payload, content_signature="synthetic-protocol"), manifests, real.excluded_episode_ids)


def observation(protocol, split, sample):
    episode, _ = protocol.require_sample(sample.episode_id, sample.step_index, split=split)
    generator = torch.Generator().manual_seed(sample.sample_id % 2147483647)
    batch = ConditionalTokenBatch(torch.randn(1, 8, 4, generator=generator),
                                  torch.randn(1, 3, 5, generator=generator), torch.ones(1, 3, dtype=torch.bool),
                                  torch.randn(1, 2, generator=generator), torch.tensor([[0] * 4 + [1] * 4]),
                                  torch.tensor([[0, 1, 2, 3] * 2]), torch.ones(1, 8, dtype=torch.bool))
    provenance = LabelProvenance((str(sample.sample_id),), (sample.episode_id,), split,
                                 "fake-model", protocol.payload["source_signature"], "fake-input", "fake-packing", "fake-condition", "normalized-8x7")
    def callback(data, indices):
        return data.visual[:, indices[0]].sum().expand(1, 8, 7)
    teacher = DeletionTeacher(nn.Identity().eval(), callback)
    reference = teacher.reference(batch, provenance)
    full = batch.valid.clone()
    partial = torch.zeros_like(full)
    partial[:, [0, 2, 4, 6]] = True
    labels = tuple(teacher.label(batch, mask, torch.tensor([[0, 4]]), provenance, full_reference=reference)
                   for mask in (full, partial))
    metadata = {"sample_id": sample.sample_id, "episode_id": sample.episode_id,
                "step_index": sample.step_index, "stage": sample.stage, "task_name": episode.task_name}
    return OfflineObservation(batch, labels, torch.tensor([[1, 2, 3]]), torch.ones(1, 3, dtype=torch.long), metadata)


def dataset(tmp_path, protocol, split):
    root = tmp_path / split
    rows = []
    config = {"split": split, "protocol_signature": protocol.payload["content_signature"],
              "model_revision": "fake-model", "dataset_version": protocol.payload["source_signature"], "input_version": "fake-input",
              "packing_version": "fake-packing", "condition_version": "fake-condition",
              "action_version": "normalized-8x7", "label_version": LABEL_VERSION}
    for sample in protocol.manifests[split].samples:
        item = observation(protocol, split, sample)
        item = replace(item, metadata=dict(item.metadata, build_config_sha256=json_signature(config)))
        path = root / f"{sample.sample_id}.pt"
        digest = save_offline_observation(path, item)
        rows.append({**item.metadata, "path": path.name, "sha256": digest})
    index = {"cache_version": OFFLINE_CACHE_VERSION, "status": "completed", "split": split,
             "build_config": config, "build_config_sha256": json_signature(config),
             "protocol_signature": protocol.payload["content_signature"],
             "expected_observations": len(rows), "observations": rows}
    atomic_json(root / "index.json", index)
    return OfflineDataset(root / "index.json", protocol, split=split)


def test_detached_cache_roundtrip_and_real_split_guard(tmp_path, protocol):
    sample = protocol.manifests["train"].samples[0]
    original = observation(protocol, "train", sample)
    path = tmp_path / "cache.pt"
    digest = save_offline_observation(path, original)
    restored = load_offline_observation(path, expected_sha256=digest, protocol=protocol, required_split="train")
    assert torch.equal(restored.batch.visual, original.batch.visual)
    assert all(not getattr(restored.batch, name).requires_grad for name in restored.batch.__dataclass_fields__)
    with pytest.raises(ValueError, match="wrong split"):
        load_offline_observation(path, expected_sha256=digest, protocol=protocol, required_split="validation")
    with pytest.raises(ValueError, match="hash"):
        load_offline_observation(path, expected_sha256="0" * 64, protocol=protocol)


def test_empty_and_partial_indices_cannot_enter_training(tmp_path, protocol):
    config = {"split": "train", "protocol_signature": protocol.payload["content_signature"], "dataset_version": protocol.payload["source_signature"]}
    index = {"cache_version": OFFLINE_CACHE_VERSION, "status": "completed", "split": "train",
             "build_config": config, "build_config_sha256": json_signature(config),
             "protocol_signature": protocol.payload["content_signature"], "expected_observations": 0, "observations": []}
    atomic_json(tmp_path / "index.json", index)
    with pytest.raises(ValueError, match="empty"):
        OfflineDataset(tmp_path / "index.json", protocol, split="train")
    complete = dataset(tmp_path, protocol, "train")
    incomplete = complete.index.copy()
    incomplete["observations"] = incomplete["observations"][:1]
    incomplete["expected_observations"] = 1
    atomic_json(complete.path, incomplete)
    with pytest.raises(ValueError, match="full registered split"):
        OfflineDataset(complete.path, protocol, split="train")


def test_initial_sampler_has_two_sets_eight_candidates_and_balanced_cameras(protocol):
    manifest = protocol.manifests["train"]
    assignments = initial_training_assignments(manifest)
    assert assignments == initial_training_assignments(manifest)
    for assignment in assignments.values():
        sets = sample_initial_sets(assignment)
        assert len(sets[0][0]) == 512 and len(sets[1][0]) in (256, 128)
        for kept, candidates in sets:
            assert len(candidates) == len(set(candidates)) == 8
            assert set(candidates) <= set(kept)
            assert sum(i < 256 for i in candidates) == 4


def _model():
    return ConditionalInfluenceEstimator(4, 5, 2, hidden_dim=8, patches_per_camera=4)


def _validation(observation, indices):
    assert not torch.is_grad_enabled()
    return observation.batch.visual[:, indices[0]].sum().expand(1, 8, 7)


def test_resume_matches_uninterrupted_optimizer_rng_and_selected_model(tmp_path, protocol):
    train = dataset(tmp_path, protocol, "train")
    validation = dataset(tmp_path, protocol, "validation")
    config = OfflineTrainConfig(max_epochs=4, hidden_dim=8, effective_batch_records=4,
                                validation_camera_budgets=((2, 2), (1, 1)))
    seed_training(17)
    full = _model()
    full_result = train_offline(full, train, validation, _validation, config=config,
                                checkpoint_directory=tmp_path / "full", run_identity={"synthetic": True})
    seed_training(17)
    split = _model()
    first = train_offline(split, train, validation, _validation, config=config,
                         checkpoint_directory=tmp_path / "resume", run_identity={"synthetic": True}, stop_after_epochs=1)
    assert first["status"] == "paused_at_epoch_boundary" and first["best_epoch"] is None
    random.random(); np.random.random(); torch.rand(100)
    resumed = _model()
    second = train_offline(resumed, train, validation, _validation, config=config,
                          checkpoint_directory=tmp_path / "resume", run_identity={"synthetic": True}, resume=True)
    assert second["status"] == "completed"
    assert second["optimizer_steps"] == full_result["optimizer_steps"] == 8
    assert second["validation_sample_forwards"] == 6
    assert second["best_epoch"] == full_result["best_epoch"]
    for left, right in zip(full.parameters(), resumed.parameters()):
        assert torch.equal(left, right)
    for name in ("full", "resume"):
        saved = torch.load(tmp_path / name / "latest.pt", weights_only=True)
        assert saved["scale"]["label_count"] == 12
        assert saved["scale"]["training_episodes"] == protocol.manifests["train"].episode_ids
    changed = replace(config, learning_rate=1e-4)
    with pytest.raises(ValueError, match="identity mismatch"):
        train_offline(_model(), train, validation, _validation, config=changed,
                      checkpoint_directory=tmp_path / "resume", run_identity={"synthetic": True}, resume=True)


def test_g1_completion_without_scientific_go_does_not_authorize_labels():
    report = {"stage": "G1", "status": "completed", "completed_observations": 90, "exact_observations": 12}
    versions = dict(model_revision="m", input_version="i", packing_version="p", protocol_signature="s")
    with pytest.raises(ValueError, match="reviewed"):
        require_g1(report, **versions)
    report.update(status="passed", go_no_go={"decision": "go"}, provenance=dict(versions))
    require_g1(report, **versions)
    report["provenance"]["input_version"] = "old-processor-only"
    with pytest.raises(ValueError, match="provenance"):
        require_g1(report, **versions)


def test_orphan_receipt_prevents_repinning_modified_policy_prompt(tmp_path, protocol):
    from cti_vla.data.identity import file_sha256
    item = observation(protocol, "train", protocol.manifests["train"].samples[0])
    path = tmp_path / "orphan.pt"
    save_offline_observation(path, item)
    payload = torch.load(path, weights_only=True)
    payload["input_ids"][0, 1] += 1
    torch.save(payload, path)
    # Even using the newly calculated file hash cannot bless altered input IDs:
    # the independent prepublication receipt pins the original bytes and prompt.
    with pytest.raises(ValueError, match="receipt"):
        load_offline_observation(path, expected_sha256=file_sha256(path), protocol=protocol)


def test_cache_index_cannot_claim_different_model_from_labels(tmp_path, protocol):
    data = dataset(tmp_path, protocol, "train")
    data.build_config["model_revision"] = "different-model"
    data.index["build_config_sha256"] = json_signature(data.build_config)
    with pytest.raises(ValueError, match="metadata.*build config"):
        data.observation(0)


def test_validation_macro_weights_temporal_stages_equally(tmp_path, protocol):
    train = dataset(tmp_path, protocol, "train")
    validation = dataset(tmp_path, protocol, "validation")
    class ImbalancedDiagnostic:
        split = "validation"
        # Duplicate early observations to ensure they cannot dominate the metric.
        entries = [0, 0, 0, 1, 2]
        def observation(self, index):
            return validation.observation(self.entries[index])
    def action(observation, indices):
        delta = {"early": 1., "middle": 3., "late": 5.}[observation.metadata["stage"]]
        return observation.labels[0].full_action + delta
    config = OfflineTrainConfig(max_epochs=2, hidden_dim=8, validation_camera_budgets=((2, 2), (1, 1)))
    result = validate_packed(_model(), ImbalancedDiagnostic(), action, config=config,
                             scale=TrainingLabelScale.fit(train.labels()), device="cpu")
    assert result["mean_l1_task_stage_macro"] == pytest.approx(3.)
    assert result["teacher_sample_forwards"] == 5


def test_g2_cli_rejects_unreviewed_g1_before_checkpoint_or_cuda(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("cache_cli_gate", root / "scripts/build_training_cache.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = tmp_path / "g1.json"
    report.write_text(json.dumps({"status": "completed", "stage": "G1"}))
    monkeypatch.setattr(torch.cuda, "device_count", lambda: pytest.fail("G1 guard reached CUDA"))
    args = Namespace(protocol=root / "configs/manifests/spatial_g0g1_v1/protocol.json",
                     asset_manifest=root / "configs/assets/openvla_oft_libero_spatial.json",
                     sampling_seed=717, audit_seed=817, split="train", output=tmp_path / "out", prepare_only=False,
                     checkpoint=tmp_path / "nonexistent-model", cache_directory=tmp_path / "hf",
                     data_directory=tmp_path / "rlds", g1_report=report)
    with pytest.raises(ValueError, match="reviewed"):
        module.run(args)
    assert not (args.output / "observations").exists()


def test_equal_validation_keeps_earlier_checkpoint_and_stops_after_five_checks(tmp_path, protocol):
    train = dataset(tmp_path, protocol, "train")
    validation = dataset(tmp_path, protocol, "validation")
    config = OfflineTrainConfig(max_epochs=30, hidden_dim=8, effective_batch_records=6,
                                validation_camera_budgets=((2, 2), (1, 1)))
    seed_training(17)
    model = _model()
    result = train_offline(model, train, validation, lambda item, _: item.labels[0].full_action,
                           config=config, checkpoint_directory=tmp_path / "constant-validation",
                           run_identity={"synthetic_constant_validation": True})
    assert result["best_epoch"] == 2
    assert result["completed_epochs"] == 12
    assert result["validation_sample_forwards"] == 18
    assert result["status"] == "completed"

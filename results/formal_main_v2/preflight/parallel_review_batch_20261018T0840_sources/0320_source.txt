"""Detached observation caches and resumable scorer-only G2/G3 training.

The large frozen policy is supplied only to the validation callback. Training
uses individual set records with gradient accumulation, so different prompt
lengths never need padding/repacking and an effective batch means set records.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import random
import tempfile
import time
from typing import Callable, Mapping, Sequence

import numpy as np
import torch

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature, tensor_signature
from cti_vla.labeling import DeletionLabels, LabelProvenance
from cti_vla.labeling.deletion import feature_fingerprint
from cti_vla.labeling.sampling import camera_balanced_set, named_seed
from cti_vla.selection import ConditionalInfluenceEstimator, ConditionalTokenBatch, staged_topk
from cti_vla.training.conditional import ConditionalTrainConfig, TrainingLabelScale, signed_influence_loss

OFFLINE_CACHE_VERSION = "cti-detached-observation-two-sets-v1"
OFFLINE_TRAIN_VERSION = "cti-epoch-resume-packed-validation-v1"
LABEL_TENSORS = ("retained_mask", "candidate_indices", "influence", "base_error", "deleted_error", "full_action")


def require_g1(report: Mapping, *, model_revision: str, input_version: str,
               packing_version: str, protocol_signature: str) -> None:
    if report.get("stage") != "G1" or report.get("status") != "passed" or report.get("go_no_go", {}).get("decision") != "go":
        raise ValueError("formal G2 requires a scientifically reviewed, passed G1 go decision")
    if type(report.get("completed_observations")) is not int or report["completed_observations"] < 90 or type(report.get("exact_observations")) is not int or report["exact_observations"] < 12:
        raise ValueError("G1 must complete the registered 90/12-observation diagnostics")
    versions = {"model_revision": model_revision, "input_version": input_version,
                "packing_version": packing_version, "protocol_signature": protocol_signature}
    if any(report.get("provenance", {}).get(key) != value for key, value in versions.items()):
        raise ValueError("G1 provenance differs from the requested cache protocol")


def initial_training_assignments(manifest, *, seed: int = 717) -> dict[int, dict]:
    """Alternate 256/128 within each task/stage; four-cycle balances set sources."""
    if manifest.split not in ("train", "validation"):
        raise ValueError("initial G2 cache only accepts train or effective validation")
    episode_map = {e.episode_id: e for e in manifest.episodes}
    groups = defaultdict(list)
    for sample in manifest.samples:
        groups[(episode_map[sample.episode_id].task_name, sample.stage)].append(sample)
    choices = ((256, "random"), (128, "uniform"), (256, "uniform"), (128, "random"))
    assignments = {}
    for key, values in sorted(groups.items()):
        ordered = sorted(values, key=lambda s: (named_seed(seed, "assignment", s.sample_id), s.sample_id))
        offset = named_seed(seed, "assignment-offset", *key) % 4
        for index, sample in enumerate(ordered):
            budget, mode = choices[(index + offset) % 4]
            assignments[sample.sample_id] = {"partial_budget": budget, "partial_mode": mode,
                                            "sampling_seed": named_seed(seed, "sets", sample.sample_id)}
    return assignments


def sample_initial_sets(assignment: Mapping, *, grid_shape=(16, 16), num_cameras: int = 2,
                        candidates_per_camera: int = 4) -> tuple[tuple[tuple[int, ...], tuple[int, ...]], ...]:
    size = math.prod(grid_shape)
    budget = assignment["partial_budget"]
    if budget % num_cameras or budget >= size * num_cameras:
        raise ValueError("partial budget must be balanced and smaller than full")
    partial = camera_balanced_set(per_camera=budget // num_cameras, grid_shape=grid_shape,
                                  num_cameras=num_cameras, mode=assignment["partial_mode"], seed=assignment["sampling_seed"])
    output = []
    for name, retained in (("full", tuple(range(size * num_cameras))), ("partial", partial)):
        candidates = []
        for camera in range(num_cameras):
            pool = [i for i in retained if i // size == camera]
            rng = random.Random(named_seed(assignment["sampling_seed"], name, "candidates", camera))
            candidates.extend(rng.sample(pool, candidates_per_camera))
        output.append((retained, tuple(sorted(candidates))))
    return tuple(output)


@dataclass(frozen=True)
class OfflineObservation:
    batch: ConditionalTokenBatch
    labels: tuple[DeletionLabels, ...]
    input_ids: torch.Tensor
    attention_mask: torch.Tensor
    metadata: dict

    def validate(self, protocol=None, *, required_split: str | None = None) -> None:
        self.batch.__post_init__()
        if self.batch.visual.shape[0] != 1 or len(self.labels) != 2:
            raise ValueError("offline cache needs one observation and exactly two set records")
        for labels in self.labels:
            labels.validate_for(self.batch, labels.retained_mask, labels.provenance)
        first, second = self.labels
        if first.provenance != second.provenance or not torch.equal(first.full_action, second.full_action):
            raise ValueError("set records must share exactly the same full teacher and conditions")
        if not torch.equal(first.retained_mask, self.batch.valid) or int(second.retained_mask.sum()) >= int(first.retained_mask.sum()):
            raise ValueError("initial offline cache must contain full plus one smaller retained set")
        if first.candidate_indices.shape != second.candidate_indices.shape:
            raise ValueError("both initial sets need the same candidate count")
        if self.input_ids.shape != self.attention_mask.shape or self.input_ids.shape != self.batch.instruction_mask.shape or self.input_ids.dtype != torch.long or not bool((self.attention_mask == 1).all()):
            raise ValueError("cached policy prompt must be an unpadded integer prompt matching conditions")
        if not torch.equal(self.attention_mask.bool(), self.batch.instruction_mask):
            raise ValueError("cached policy/selector instruction masks differ")
        p = first.provenance
        if p.episode_ids != (self.metadata["episode_id"],) or p.sample_ids != (str(self.metadata["sample_id"]),):
            raise ValueError("cache metadata and label sample identities disagree")
        if required_split is not None and p.split != required_split:
            raise ValueError("offline cache has the wrong split")
        if protocol is not None:
            episode, sample = protocol.require_sample(self.metadata["episode_id"], self.metadata["step_index"], split=p.split)
            if (sample.sample_id, sample.stage, episode.task_name) != (self.metadata["sample_id"], self.metadata["stage"], self.metadata["task_name"]):
                raise ValueError("offline metadata disagrees with authoritative episode manifest")

    def to(self, device) -> "OfflineObservation":
        batch = ConditionalTokenBatch(**{name: getattr(self.batch, name).to(device) for name in self.batch.__dataclass_fields__})
        labels = tuple(DeletionLabels(**{name: getattr(record, name).to(device) for name in LABEL_TENSORS},
                                      provenance=record.provenance, feature_sha256=record.feature_sha256,
                                      teacher_calls=record.teacher_calls) for record in self.labels)
        return OfflineObservation(batch, labels, self.input_ids.to(device), self.attention_mask.to(device), self.metadata)


def _atomic_torch_save(path: Path, payload: dict, *, overwrite: bool, receipt: dict | None = None) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            torch.save(payload, handle)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists() and not overwrite:
            raise FileExistsError(path)
        if receipt is not None:
            # Write the expected immutable-file checksum before publishing the
            # tensor file. Therefore an existing observation always has an
            # independent receipt, including an index-update interruption.
            atomic_json(path.with_suffix(".receipt.json"), dict(receipt, cache_sha256=file_sha256(temporary)))
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def save_offline_observation(path: str | Path, observation: OfflineObservation) -> str:
    observation.validate()
    cpu = observation.to("cpu")
    payload = {"schema_version": 1, "cache_version": OFFLINE_CACHE_VERSION,
               "batch": {name: getattr(cpu.batch, name).detach().contiguous() for name in cpu.batch.__dataclass_fields__},
               "labels": [{"tensors": {name: getattr(label, name).detach().contiguous() for name in LABEL_TENSORS},
                           "provenance": asdict(label.provenance), "feature_sha256": label.feature_sha256,
                           "teacher_calls": label.teacher_calls} for label in cpu.labels],
               "input_ids": cpu.input_ids.detach(), "attention_mask": cpu.attention_mask.detach(),
               "metadata": cpu.metadata}
    receipt = {"cache_version": OFFLINE_CACHE_VERSION, "metadata_sha256": json_signature(cpu.metadata),
               "feature_sha256": feature_fingerprint(cpu.batch),
               "policy_inputs_sha256": tensor_signature({"input_ids": cpu.input_ids, "attention_mask": cpu.attention_mask,
                                                         "normalized_proprio": cpu.batch.normalized_proprio})}
    _atomic_torch_save(Path(path), payload, overwrite=False, receipt=receipt)
    return file_sha256(path)


def load_offline_observation(path: str | Path, *, expected_sha256: str, protocol=None,
                             required_split: str | None = None) -> OfflineObservation:
    if file_sha256(path) != expected_sha256:
        raise ValueError("detached observation cache file hash mismatch")
    receipt = json.loads(Path(path).with_suffix(".receipt.json").read_text(encoding="utf-8"))
    if receipt.get("cache_sha256") != expected_sha256 or receipt.get("cache_version") != OFFLINE_CACHE_VERSION:
        raise ValueError("detached cache receipt disagrees with registered file hash/version")
    payload = torch.load(Path(path), map_location="cpu", weights_only=True)
    if payload.get("schema_version") != 1 or payload.get("cache_version") != OFFLINE_CACHE_VERSION:
        raise ValueError("unsupported detached observation cache")
    batch = ConditionalTokenBatch(**payload["batch"])
    labels = tuple(DeletionLabels(**row["tensors"], provenance=LabelProvenance(**row["provenance"]),
                                  feature_sha256=row["feature_sha256"], teacher_calls=row["teacher_calls"])
                   for row in payload["labels"])
    observation = OfflineObservation(batch, labels, payload["input_ids"], payload["attention_mask"], payload["metadata"])
    observation.validate(protocol, required_split=required_split)
    expected_receipt = {"metadata_sha256": json_signature(observation.metadata), "feature_sha256": feature_fingerprint(batch),
                        "policy_inputs_sha256": tensor_signature({"input_ids": observation.input_ids,
                                                                  "attention_mask": observation.attention_mask,
                                                                  "normalized_proprio": batch.normalized_proprio})}
    if any(receipt.get(key) != value for key, value in expected_receipt.items()):
        raise ValueError("detached cache receipt does not bind its features, policy prompt and metadata")
    return observation


class OfflineDataset:
    """An index is usable for training only when every registered sample exists."""

    def __init__(self, index_path: str | Path, protocol, *, split: str):
        if split not in ("train", "validation"):
            raise ValueError("offline trainer cannot read test")
        self.path = Path(index_path)
        self.index = json.loads(self.path.read_text(encoding="utf-8"))
        self.protocol, self.split = protocol, split
        if self.index.get("cache_version") != OFFLINE_CACHE_VERSION or self.index.get("status") != "completed" or self.index.get("split") != split:
            raise ValueError("training requires a complete cache of the requested split")
        if self.index.get("protocol_signature") != protocol.payload["content_signature"]:
            raise ValueError("cache and authoritative split protocol differ")
        self.build_config = self.index.get("build_config")
        if not isinstance(self.build_config, dict) or self.index.get("build_config_sha256") != json_signature(self.build_config):
            raise ValueError("cache build config hash mismatch")
        if self.build_config.get("protocol_signature") != protocol.payload["content_signature"] or self.build_config.get("split") != split:
            raise ValueError("build config does not bind the authoritative split")
        if self.build_config.get("dataset_version") != protocol.payload["source_signature"]:
            raise ValueError("cache dataset version differs from authoritative source data")
        self.entries = self.index["observations"]
        if not self.entries or len(self.entries) != self.index.get("expected_observations"):
            raise ValueError("empty or incomplete label cache")
        if len({entry["sample_id"] for entry in self.entries}) != len(self.entries):
            raise ValueError("duplicate cached observation")
        expected_ids = {sample.sample_id for sample in protocol.manifests[split].samples
                        if sample.episode_id not in protocol.excluded_episode_ids}
        if {entry["sample_id"] for entry in self.entries} != expected_ids:
            raise ValueError("cache does not cover the full registered split after exclusions")
        for entry in self.entries:
            _, sample = protocol.require_sample(entry["episode_id"], entry["step_index"], split=split)
            if sample.sample_id != entry["sample_id"]:
                raise ValueError("cache index sample identity mismatch")
            target = (self.path.parent / entry["path"]).resolve()
            if self.path.parent.resolve() not in target.parents:
                raise ValueError("cache record path leaves its registered cache directory")
        self.signature = file_sha256(self.path)

    def __len__(self) -> int:
        return 2 * len(self.entries)

    def observation(self, index: int) -> OfflineObservation:
        entry = self.entries[index]
        value = load_offline_observation(self.path.parent / entry["path"], expected_sha256=entry["sha256"],
                                         protocol=self.protocol, required_split=self.split)
        if value.metadata["sample_id"] != entry["sample_id"]:
            raise ValueError("cache file differs from its index sample")
        if any(value.metadata.get(key) != expected for key, expected in entry.items() if key not in ("path", "sha256")):
            raise ValueError("cache record metadata/sampling assignment differs from its registered index")
        if value.metadata.get("build_config_sha256") != self.index["build_config_sha256"]:
            raise ValueError("cache file metadata and index build config differ")
        versions = {"model_revision": "model_revision", "dataset_version": "dataset_version",
                    "preprocessing_version": "input_version", "packing_version": "packing_version",
                    "condition_version": "condition_version", "action_version": "action_version", "label_version": "label_version"}
        for labels in value.labels:
            if any(getattr(labels.provenance, field) != self.build_config.get(config_key) for field, config_key in versions.items()):
                raise ValueError("label provenance differs from the cache/model/input/condition config")
        if value.batch.visual.shape[1] == 512:
            expected = sample_initial_sets(value.metadata["assignment"])
            for labels, (retained, candidates) in zip(value.labels, expected):
                if labels.retained_mask.nonzero()[:, 1].tolist() != list(retained) or labels.candidate_indices[0].tolist() != list(candidates):
                    raise ValueError("cached S/candidates differ from the frozen sampling assignment")
        return value

    def record(self, index: int) -> tuple[OfflineObservation, DeletionLabels]:
        observation = self.observation(index // 2)
        return observation, observation.labels[index % 2]

    def labels(self):
        for index in range(len(self.entries)):
            yield from self.observation(index).labels


@dataclass(frozen=True)
class OfflineTrainConfig:
    seed: int = 17
    max_epochs: int = 30
    effective_batch_records: int = 16
    learning_rate: float = 3e-4
    weight_decay: float = 1e-4
    validate_every: int = 2
    patience_checks: int = 5
    hidden_dim: int = 256
    validation_camera_budgets: tuple[tuple[int, ...], ...] = ((128, 128), (64, 64))

    def __post_init__(self):
        if type(self.seed) is not int or not 2 <= self.max_epochs <= 30 or self.effective_batch_records <= 0 or self.validate_every != 2 or self.patience_checks != 5 or self.hidden_dim <= 0:
            raise ValueError("invalid fixed G3 training protocol")
        if not math.isfinite(self.learning_rate) or self.learning_rate <= 0 or not math.isfinite(self.weight_decay) or self.weight_decay < 0:
            raise ValueError("invalid AdamW hyperparameters")


def seed_training(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def rng_state() -> dict:
    state = np.random.get_state()
    return {"python": random.getstate(), "torch_cpu": torch.get_rng_state(),
            "torch_cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
            "numpy": {"name": state[0], "keys": torch.tensor(state[1].astype(np.int64)),
                      "position": state[2], "has_gauss": state[3], "cached_gaussian": state[4]}}


def restore_rng(state: Mapping) -> None:
    random.setstate(state["python"])
    torch.set_rng_state(state["torch_cpu"])
    if state["torch_cuda"]:
        if not torch.cuda.is_available() or len(state["torch_cuda"]) != torch.cuda.device_count():
            raise ValueError("checkpoint CUDA RNG topology differs from this runtime")
        torch.cuda.set_rng_state_all(state["torch_cuda"])
    value = state["numpy"]
    np.random.set_state((value["name"], value["keys"].numpy().astype(np.uint32), value["position"], value["has_gauss"], value["cached_gaussian"]))


def validate_packed(estimator, dataset, forward_retained: Callable, *, config: OfflineTrainConfig,
                    scale: TrainingLabelScale, device) -> dict:
    if dataset.split != "validation":
        raise ValueError("checkpoint selection requires validation, never train/test")
    groups = defaultdict(list)
    rows = []
    estimator.eval()
    with torch.no_grad():
        for index in range(len(dataset.entries)):
            observation = dataset.observation(index).to(device)
            scale.validate(observation.labels[0].provenance)
            selection = staged_topk(estimator, observation.batch, config.validation_camera_budgets)
            action = forward_retained(observation, selection.source_indices)
            reference = observation.labels[0].full_action
            if action.shape != reference.shape or not torch.isfinite(action).all() or action.requires_grad:
                raise ValueError("validation callback must return detached finite normalized actions")
            error = float((action.float() - reference.float()).abs().mean())
            metadata = observation.metadata
            groups[(metadata["task_name"], metadata["stage"])].append(error)
            rows.append({"sample_id": metadata["sample_id"], "task_name": metadata["task_name"],
                         "stage": metadata["stage"], "mean_l1": error,
                         "retained_indices": selection.source_indices[0].cpu().tolist()})
    if not rows:
        raise ValueError("validation panel is empty")
    tasks = sorted({key[0] for key in groups})
    if any({stage for task, stage in groups if task == name} != {"early", "middle", "late"} for name in tasks):
        raise ValueError("validation must cover each task at all three temporal stages")
    task_scores = {task: sum(sum(groups[(task, stage)]) / len(groups[(task, stage)])
                             for stage in ("early", "middle", "late")) / 3 for task in tasks}
    return {"mean_l1_task_stage_macro": sum(task_scores.values()) / len(task_scores),
            "per_task": task_scores, "observations": rows, "teacher_sample_forwards": len(rows),
            "api_calls": len(rows), "target_visual_tokens": sum(config.validation_camera_budgets[-1])}


def train_offline(estimator: ConditionalInfluenceEstimator, train_dataset, validation_dataset,
                  forward_validation: Callable, *, config: OfflineTrainConfig,
                  checkpoint_directory: str | Path, run_identity: Mapping,
                  device="cpu", resume: bool = False, stop_after_epochs: int | None = None) -> dict:
    """Resume at a completed epoch boundary, preserving optimizer/RNG/selection.

    `stop_after_epochs` bounds one invocation and is excluded from experiment
    identity. An interrupted incomplete epoch is retrained from latest; its
    attempted work must remain in the caller's job/cost log.
    """
    if train_dataset.split != "train" or validation_dataset.split != "validation" or len(train_dataset) == 0:
        raise ValueError("training requires nonempty train labels and separate validation")
    checkpoint_directory = Path(checkpoint_directory)
    checkpoint_directory.mkdir(parents=True, exist_ok=True)
    latest, best = checkpoint_directory / "latest.pt", checkpoint_directory / "best.pt"
    identity = {"training_version": OFFLINE_TRAIN_VERSION, "config": asdict(config),
                "train_cache_sha256": train_dataset.signature, "validation_cache_sha256": validation_dataset.signature,
                "run_identity": dict(run_identity)}
    identity_sha = json_signature(identity)
    scale = TrainingLabelScale.fit(train_dataset.labels())
    estimator.to(device=device, dtype=torch.float32)
    optimizer = torch.optim.AdamW(estimator.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    start_epoch, best_score, best_epoch, stale, optimizer_steps, history = 0, math.inf, None, 0, 0, []
    if resume:
        if not latest.exists():
            raise FileNotFoundError("--resume requires an existing latest.pt")
        saved = torch.load(latest, map_location="cpu", weights_only=True)
        if saved.get("identity_sha256") != identity_sha or saved.get("identity") != identity:
            raise ValueError("training checkpoint config/cache/version identity mismatch")
        if saved.get("scale") != asdict(scale):
            raise ValueError("training labels or global RMS scale changed on resume")
        estimator.load_state_dict(saved["estimator"], strict=True)
        optimizer.load_state_dict(saved["optimizer"])
        for state in optimizer.state.values():
            for key, value in state.items():
                if isinstance(value, torch.Tensor) and key != "step":
                    state[key] = value.to(device)
        start_epoch, best_score, best_epoch, stale = saved["next_epoch"], saved["best_score"], saved["best_epoch"], saved["checks_without_improvement"]
        optimizer_steps, history = saved["optimizer_steps"], saved["history"]
        restore_rng(saved["rng"])
    elif latest.exists() or best.exists():
        raise FileExistsError("checkpoint directory already contains a run; use --resume or a new directory")
    else:
        # The caller seeds BEFORE constructing the scorer; seed again to make
        # epoch shuffle independent of incidental initialization RNG draws.
        seed_training(config.seed)
    loss_config = ConditionalTrainConfig()
    epochs_this_call = 0
    for epoch in range(start_epoch, config.max_epochs):
        if stale >= config.patience_checks:
            break
        started = time.perf_counter()
        order = list(range(len(train_dataset)))
        random.shuffle(order)
        epoch_loss, label_count = 0.0, 0
        estimator.train()
        for offset in range(0, len(order), config.effective_batch_records):
            record_ids = order[offset:offset + config.effective_batch_records]
            optimizer.zero_grad(set_to_none=True)
            for record_id in record_ids:
                observation, _ = train_dataset.record(record_id)
                observation = observation.to(device)
                labels = observation.labels[record_id % 2]
                scale.validate(labels.provenance)
                if labels.provenance.split != "train":
                    raise ValueError("validation/test label reached the optimizer")
                predicted = estimator(observation.batch, labels.retained_mask).gather(1, labels.candidate_indices)
                loss, _, _ = signed_influence_loss(predicted, labels.influence.float() / scale.value, loss_config)
                if not torch.isfinite(loss):
                    raise FloatingPointError("nonfinite scorer loss")
                (loss / len(record_ids)).backward()
                epoch_loss += float(loss.detach())
                label_count += labels.influence.numel()
            torch.nn.utils.clip_grad_norm_(estimator.parameters(), 1.0, error_if_nonfinite=True)
            optimizer.step()
            optimizer_steps += 1
        row = {"epoch": epoch + 1, "loss": epoch_loss / len(order), "records": len(order),
               "labels": label_count, "optimizer_steps_total": optimizer_steps,
               "training_seconds": time.perf_counter() - started}
        improved = False
        if (epoch + 1) % config.validate_every == 0:
            started = time.perf_counter()
            validation = validate_packed(estimator, validation_dataset, forward_validation,
                                         config=config, scale=scale, device=device)
            row["validation"] = validation
            row["validation_seconds"] = time.perf_counter() - started
            score = validation["mean_l1_task_stage_macro"]
            if score < best_score:
                best_score, best_epoch, stale, improved = score, epoch + 1, 0, True
            else:
                stale += 1
        history.append(row)
        payload = {"schema_version": 1, "identity": identity, "identity_sha256": identity_sha,
                   "estimator": estimator.state_dict(), "optimizer": optimizer.state_dict(),
                   "scale": asdict(scale), "next_epoch": epoch + 1, "best_score": best_score,
                   "best_epoch": best_epoch, "checks_without_improvement": stale,
                   "optimizer_steps": optimizer_steps, "history": history, "rng": rng_state()}
        if improved:
            _atomic_torch_save(best, payload, overwrite=True)
        _atomic_torch_save(latest, payload, overwrite=True)
        atomic_json(checkpoint_directory / "history.json", {"identity_sha256": identity_sha, "epochs": history})
        epochs_this_call += 1
        if stop_after_epochs is not None and epochs_this_call >= stop_after_epochs:
            break
    completed_epochs = history[-1]["epoch"] if history else start_epoch
    finished = completed_epochs >= config.max_epochs or stale >= config.patience_checks
    if finished and best_epoch is not None:
        chosen = torch.load(best, map_location="cpu", weights_only=True)
        if chosen.get("identity_sha256") != identity_sha or chosen["best_epoch"] != best_epoch:
            raise ValueError("best checkpoint differs from latest selection state")
        estimator.load_state_dict(chosen["estimator"], strict=True)
    return {"status": "completed" if finished else "paused_at_epoch_boundary", "identity_sha256": identity_sha,
            "completed_epochs": completed_epochs, "best_epoch": best_epoch,
            "best_validation_mean_l1": best_score if math.isfinite(best_score) else None,
            "optimizer_steps": optimizer_steps, "scale": asdict(scale), "history": history,
            "latest_checkpoint": str(latest), "best_checkpoint": str(best) if best_epoch is not None else None,
            "validation_sample_forwards": sum(r.get("validation", {}).get("teacher_sample_forwards", 0) for r in history),
            "resume_boundary": "completed epoch; interrupted partial-epoch compute is additional attempted cost"}

"""Trained CTI selector deployment through the frozen G0 observation/action path.

This adapter has CPU contract tests only until a recorded GPU rollout accepts
the exact checkpoint. It neither evaluates a teacher nor saves checkpoints.
"""
from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Mapping

import torch

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation import libero_runtime
from cti_vla.evaluation.teacher_diagnostics import json_signature
from cti_vla.labeling.deletion import LABEL_VERSION
from cti_vla.models.abstraction.packing import PACKING_VERSION
from cti_vla.selection import ConditionalInfluenceEstimator, ConditionalTokenBatch, staged_topk
from cti_vla.training.conditional import TrainingLabelScale
from cti_vla.training.offline import OFFLINE_TRAIN_VERSION


SELECTOR_RUNTIME_VERSION = "cti-g3-staged-libero-deployment-v1"
NORMALIZED_ACTION_VERSION = "normalized-l1-8x7-v1"


def deployment_source_hashes(source_root) -> dict:
    root = Path(source_root)
    paths = [*sorted((root / "src/cti_vla/models").rglob("*.py")),
             *sorted((root / "src/cti_vla/selection").rglob("*.py")),
             root / "src/cti_vla/evaluation/libero_runtime.py"]
    if not paths or any(not path.is_file() for path in paths):
        raise ValueError("deployment source tree is incomplete")
    return {path.relative_to(root).as_posix(): file_sha256(path) for path in paths}


def selector_expected_versions(model_revision: str, protocol, stats_key: str) -> dict:
    return {"model_revision": model_revision, "dataset_version": protocol.payload["source_signature"],
            "input_version": libero_runtime.INPUTS_VERSION, "packing_version": PACKING_VERSION,
            "condition_version": f"{libero_runtime.INPUTS_VERSION}:{stats_key}:frozen-prompt-embeddings",
            "protocol_signature": protocol.payload["content_signature"]}


def camera_budget_schedule(target_tokens: int) -> tuple[tuple[int, int], ...]:
    if type(target_tokens) is not int or target_tokens not in (256, 128, 64):
        raise ValueError("trained selector deployment target must be 256, 128 or 64")
    stages = ((128, 128), (64, 64), (32, 32))
    return stages[:{256: 1, 128: 2, 64: 3}[target_tokens]]


@dataclass(frozen=True)
class LoadedSelector:
    estimator: ConditionalInfluenceEstimator
    scale: TrainingLabelScale
    provenance: Mapping


def validate_selector_training_coverage(selector: LoadedSelector, training_report: Mapping, protocol) -> None:
    """Formal v1 must come from all registered train/effective-val observations."""
    train = protocol.manifests["train"]
    validation = protocol.manifests["validation"]
    expected_episodes = set(train.episode_ids)
    episodes = selector.scale.training_episodes
    validation_count = sum(sample.episode_id not in protocol.excluded_episode_ids for sample in validation.samples)
    if set(episodes) != expected_episodes or len(episodes) != len(expected_episodes):
        raise ValueError("selector RMS must cover exactly the registered train episodes")
    if training_report.get("train_observations") != len(train.samples) or training_report.get("validation_observations") != validation_count:
        raise ValueError("G3 report does not cover the full train/effective-validation observation panels")
    if selector.scale.label_count != len(train.samples) * 16:
        raise ValueError("formal v1 selector scale requires the complete initial sixteen-label-per-observation panel")


def load_selector_checkpoint(path, training_report: Mapping, *, expected_versions: Mapping,
                             expected_source_hashes: Mapping, device="cpu") -> LoadedSelector:
    """Load only the hash-pinned G3 validation-selected best scorer, safely.

    The G3 report pins the actual file bytes; its checkpoint identity pins cache,
    training configuration and implementation. Optimizer/RNG data are read by
    weights_only deserialization but never applied to the deployment model.
    """
    path = Path(path)
    if training_report.get("stage") != "G3" or training_report.get("status") != "completed" or training_report.get("frozen_base_unchanged") is not True:
        raise ValueError("deployment requires a completed G3 report with unchanged base")
    digest = file_sha256(path)
    if digest != training_report.get("best_checkpoint_sha256"):
        raise ValueError("selector checkpoint hash differs from G3 selected best")
    saved = torch.load(path, map_location="cpu", weights_only=True)
    identity = saved["identity"]
    if saved["schema_version"] != 1 or identity["training_version"] != OFFLINE_TRAIN_VERSION or saved["identity_sha256"] != json_signature(identity) or training_report["identity_sha256"] != saved["identity_sha256"]:
        raise ValueError("selector training identity/schema/version mismatch")
    run, config = identity["run_identity"], identity["config"]
    for name in ("model_revision", "input_version", "packing_version", "protocol_signature"):
        if not expected_versions.get(name) or run.get(name) != expected_versions[name]:
            raise ValueError(f"selector deployment version mismatch: {name}")
    if not expected_source_hashes or any(run.get("source_files", {}).get(name) != digest for name, digest in expected_source_hashes.items()):
        raise ValueError("selector producer/deployment source hashes differ")
    if config["seed"] != training_report["seed"] or config["seed"] not in (17, 23, 41):
        raise ValueError("selector training seed mismatch")
    if tuple(tuple(stage) for stage in config["validation_camera_budgets"]) != camera_budget_schedule(128):
        raise ValueError("checkpoint was not selected with the registered staged128 protocol")
    epoch, score = saved["best_epoch"], saved["best_score"]
    if type(epoch) is not int or epoch <= 0 or epoch != saved["next_epoch"] or epoch != training_report["best_epoch"] or not math.isfinite(score) or score < 0 or score != training_report["best_validation_mean_l1"]:
        raise ValueError("checkpoint is not the registered validation-selected best epoch")
    checks = [row for row in saved["history"] if row["epoch"] == epoch]
    if len(checks) != 1 or checks[0].get("validation", {}).get("mean_l1_task_stage_macro") != score:
        raise ValueError("selected epoch lacks matching packed validation evidence")
    scale = TrainingLabelScale(**saved["scale"])
    versions = (expected_versions["model_revision"], expected_versions["dataset_version"],
                expected_versions["input_version"], expected_versions["packing_version"],
                expected_versions["condition_version"], NORMALIZED_ACTION_VERSION, LABEL_VERSION)
    if tuple(scale.versions) != versions or json_signature(saved["scale"]) != json_signature(training_report["scale"]):
        raise ValueError("selector RMS/condition/label versions differ from deployment")
    dimensions = run["scorer_dimensions"]
    if dimensions["proprio"] != 8 or dimensions["hidden"] != config["hidden_dim"]:
        raise ValueError("selector architecture differs from the registered training configuration")
    estimator = ConditionalInfluenceEstimator(dimensions["visual"], dimensions["language"], dimensions["proprio"],
        hidden_dim=dimensions["hidden"], num_cameras=2, patches_per_camera=256, max_instruction_tokens=128)
    if any(not isinstance(value, torch.Tensor) or not torch.isfinite(value).all() or value.dtype != torch.float32
           for value in saved["estimator"].values()):
        raise ValueError("selector weights must be finite FP32 tensors")
    estimator.load_state_dict(saved["estimator"], strict=True)
    estimator.to(device=device, dtype=torch.float32).eval().requires_grad_(False)
    return LoadedSelector(estimator, scale, {
        "selector_checkpoint_sha256": digest, "training_identity_sha256": saved["identity_sha256"],
        "training_seed": config["seed"], "best_epoch": epoch, "validation_mean_l1": score,
        "model_revision": run["model_revision"], "input_version": run["input_version"],
        "packing_version": run["packing_version"], "condition_version": versions[4],
        "protocol_signature": run["protocol_signature"], "dimensions": dimensions,
        "label_scale": scale.value, "runtime_version": SELECTOR_RUNTIME_VERSION,
        "condition_mode": "all", "selection_mode": "staged_dynamic_set",
    })


class SelectorRolloutPolicy:
    """Same full observation as G0 -> staged scorer -> one packed action chunk.

    stage_context(name) is an optional context-manager factory for a separate
    profiler. Default execution performs no extra timing or synchronization.
    Language, vision, selections and actions are recomputed on every request.
    record_selection=False omits diagnostic CPU index extraction for profiling.
    """
    def __init__(self, components, processor, selector: LoadedSelector, *, stats_key: str,
                 target_tokens: int = 128, stage_context=None, record_selection: bool = True):
        from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
        self.schedule = camera_budget_schedule(target_tokens)
        self.components, self.processor, self.selector = components, processor, selector
        self.stats_key, self.target_tokens = stats_key, target_tokens
        self.stage_context = stage_context or (lambda _: nullcontext())
        self.record_selection = record_selection
        self.device = next(components.vla.parameters()).device
        self.dtype = next(components.vla.parameters()).dtype
        if stats_key not in components.vla.norm_stats:
            raise ValueError("unknown checkpoint normalization statistics key")
        expected_condition = f"{libero_runtime.INPUTS_VERSION}:{stats_key}:frozen-prompt-embeddings"
        if selector.provenance.get("input_version") != libero_runtime.INPUTS_VERSION or selector.provenance.get("packing_version") != PACKING_VERSION or selector.provenance.get("condition_version") != expected_condition:
            raise ValueError("selector uses incompatible input/packing/condition normalization")
        if selector.provenance.get("condition_mode") != "all" or selector.provenance.get("selection_mode") != "staged_dynamic_set":
            raise ValueError("only the trained all-condition staged selector is supported")
        if next(selector.estimator.parameters()).device != self.device:
            raise ValueError("selector and VLA must share the same device")
        if any(parameter.dtype != torch.float32 or parameter.requires_grad for parameter in selector.estimator.parameters()) or selector.estimator.training:
            raise ValueError("deployed selector must be frozen FP32 eval mode")
        self.token_policy = OpenVLAOFTTokenPolicy(components.vla, components.action_head,
                                               components.proprio_projector, num_patches_full=512)
        self.camera_ids = torch.arange(2, device=self.device).repeat_interleave(256)[None]
        self.patch_ids = torch.arange(256, device=self.device).repeat(2)[None]
        self.valid = torch.ones(1, 512, device=self.device, dtype=torch.bool)

    def reset(self):
        """There is no observation, action, or language cache to reset."""

    @torch.no_grad()
    def __call__(self, observation, instruction) -> libero_runtime.PolicyChunk:
        vla, scorer = self.components.vla, self.selector.estimator
        if vla.training or scorer.training:
            raise ValueError("VLA and trained selector must remain in eval mode")
        with self.stage_context("preprocess"):
            inputs = libero_runtime.prepare_observation_inputs(observation, instruction, self.processor,
                vla.norm_stats[self.stats_key]["proprio"], device=self.device, dtype=self.dtype)
        with self.stage_context("vision"):
            visual = vla._process_vision_features(inputs["pixel_values"], None, False).detach()
            if visual.ndim != 3 or visual.shape[:2] != (1, 512):
                raise ValueError("selector deployment requires full dual-view512 visual tokens")
        with self.stage_context("condition_selection"):
            language = vla.get_input_embeddings()(inputs["input_ids"]).detach()
            batch = ConditionalTokenBatch(visual, language, inputs["attention_mask"].bool(),
                inputs["normalized_proprio"].detach(), self.camera_ids, self.patch_ids, self.valid)
            selection = staged_topk(scorer, batch, self.schedule)
        with self.stage_context("policy"):
            normalized = self.token_policy.forward_from_full_tokens(visual, inputs["normalized_proprio"],
                input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"],
                retained_indices=selection.source_indices)
        with self.stage_context("postprocess"):
            normalized = normalized.float().cpu().numpy()[0]
            physical = vla._unnormalize_actions(normalized, self.stats_key)
            actions = libero_runtime.postprocess_actions(physical)
            metadata = {"method": f"cti{self.target_tokens}", "visual_tokens": self.target_tokens,
                "inputs_version": libero_runtime.INPUTS_VERSION, "action_version": libero_runtime.ACTION_VERSION,
                "packing_version": PACKING_VERSION, "selector_runtime_version": SELECTOR_RUNTIME_VERSION,
                "policy_calls": 1, "vision_calls": 1, "scorer_calls": len(self.schedule),
                "per_camera_budgets": [list(stage) for stage in self.schedule],
                "selector_checkpoint_sha256": self.selector.provenance["selector_checkpoint_sha256"],
                "training_seed": self.selector.provenance["training_seed"],
                "normalized_proprio": inputs["normalized_proprio_numpy"].tolist(),
                "language_cache": "disabled", "diagnostic_indices_recorded": self.record_selection}
            if self.record_selection:
                metadata["retained_indices"] = selection.source_indices[0].cpu().tolist()
            return libero_runtime.PolicyChunk(normalized, actions, metadata)


__all__ = ["SELECTOR_RUNTIME_VERSION", "LoadedSelector", "camera_budget_schedule",
           "deployment_source_hashes", "selector_expected_versions", "validate_selector_training_coverage",
           "load_selector_checkpoint", "SelectorRolloutPolicy"]

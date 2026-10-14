"""G1-F one-shot hard deployment; auxiliary future heads are never instantiated.

Real checkpoint/rollout validation is separate from the CPU contract tests.
The frozen G0 observation/action and original-position packing remain shared.
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
from cti_vla.models.abstraction.packing import PACKING_VERSION
from cti_vla.selection import ConditionalInfluenceEstimator, ConditionalTokenBatch

FUTURE_SCHEMA = "g1_future_v1"
FUTURE_RUNTIME_VERSION = "g1-f-full512-score-once-hard128-deployment-v1"
FUTURE_SELECTION_METRIC = "hard_validation_teacher_l1"
FUTURE_SUITES = {"libero_spatial": "libero_spatial_no_noops", "libero_10": "libero_10_no_noops"}
DIMENSIONS = ("token_dim", "language_dim", "proprio_dim", "hidden_dim", "num_cameras",
              "patches_per_camera", "max_instruction_tokens")
METADATA_FIELDS = ("schema", "arm", "seed", "scorer_dimensions", "config_sha256",
    "window_manifest_sha256", "pair_id", "model_revision", "input_version", "packing_version",
    "stats_key", "training_source_files", "training_source_sha256", "update", "selection_metric",
    "validation_metric", "base_frozen", "checkpoint_unchanged", "training_complete")


def _sha(value, name):
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"{name} must be a SHA256 hex digest")


def _metadata(value: Mapping) -> dict:
    metadata = {name: value[name] for name in METADATA_FIELDS}
    # Legacy Spatial checkpoints predate an explicit suite field. Preserve
    # their exact metadata; new Long artifacts must carry both bindings.
    for key in ("suite", "input_acceptance_sha256"):
        if key in value:
            metadata[key] = value[key]
    suite = metadata.get("suite", "libero_spatial")
    if suite not in FUTURE_SUITES:
        raise ValueError("unsupported G1-F suite")
    if "suite" in metadata and metadata["stats_key"] != FUTURE_SUITES[suite]:
        raise ValueError("G1-F suite and normalization key differ")
    if suite == "libero_10":
        _sha(metadata.get("input_acceptance_sha256"), "Long input acceptance")
    if metadata["schema"] != FUTURE_SCHEMA or metadata["arm"] not in ("A", "B"):
        raise ValueError("G1-F requires its independent A/B checkpoint schema")
    if type(metadata["seed"]) is not int or metadata["seed"] < 0 or type(metadata["update"]) is not int or metadata["update"] < 0:
        raise ValueError("G1-F seed/update must be nonnegative integers")
    for key in ("config_sha256", "window_manifest_sha256", "pair_id", "training_source_sha256"):
        _sha(metadata[key], key)
    sources = metadata["training_source_files"]
    if not isinstance(sources, Mapping) or not sources:
        raise ValueError("G1-F training source hashes are required")
    for path, digest in sources.items():
        if not isinstance(path, str) or path.startswith("/") or ":" in path or "\\" in path or ".." in Path(path).parts:
            raise ValueError("training source keys must be project-relative POSIX paths")
        _sha(digest, path)
    if json_signature(sources) != metadata["training_source_sha256"]:
        raise ValueError("G1-F training source signature mismatch")
    dimensions = metadata["scorer_dimensions"]
    if set(dimensions) != set(DIMENSIONS) or any(type(dimensions[k]) is not int or dimensions[k] <= 0 for k in DIMENSIONS):
        raise ValueError("invalid G1-F scorer dimensions")
    if (dimensions["proprio_dim"], dimensions["num_cameras"], dimensions["patches_per_camera"], dimensions["max_instruction_tokens"]) != (8, 2, 256, 128):
        raise ValueError("G1-F uses proprio8, two256-patch views and prompt capacity128")
    if metadata["selection_metric"] != FUTURE_SELECTION_METRIC or not isinstance(metadata["validation_metric"], (int, float)) or not math.isfinite(metadata["validation_metric"]) or metadata["validation_metric"] < 0:
        raise ValueError("G1-F selection requires finite nonnegative hard teacher L1")
    if metadata["base_frozen"] is not True or metadata["checkpoint_unchanged"] is not True or type(metadata["training_complete"]) is not bool:
        raise ValueError("G1-F checkpoint lacks frozen-base evidence")
    if metadata["input_version"] != libero_runtime.INPUTS_VERSION or metadata["packing_version"] != PACKING_VERSION:
        raise ValueError("G1-F checkpoint input/packing mismatch")
    if not isinstance(metadata["model_revision"], str) or not metadata["model_revision"] or not isinstance(metadata["stats_key"], str) or not metadata["stats_key"]:
        raise ValueError("model revision and normalization key are required")
    return metadata


def make_future_checkpoint_metadata(*, arm, seed, scorer_dimensions, training_config,
        pair_config, window_manifest_sha256, model_revision, stats_key, training_source_files,
        update, validation_metric, training_complete=False, input_acceptance_sha256=None) -> dict:
    """Producer helper. Save ``{**metadata, 'estimator_state_dict': ...}``.

    A/B pair_config contains only the predeclared shared training settings.
    The complete arm-specific training_config is hash-bound independently.
    """
    extra = {"suite": pair_config["suite"]} if "suite" in pair_config else {}
    if input_acceptance_sha256 is not None:
        extra["input_acceptance_sha256"] = input_acceptance_sha256
    return _metadata(dict(schema=FUTURE_SCHEMA, arm=arm, seed=seed,
        scorer_dimensions=dict(scorer_dimensions), config_sha256=json_signature(training_config),
        window_manifest_sha256=window_manifest_sha256, pair_id=json_signature(pair_config),
        model_revision=model_revision, input_version=libero_runtime.INPUTS_VERSION,
        packing_version=PACKING_VERSION, stats_key=stats_key,
        training_source_files=dict(training_source_files), training_source_sha256=json_signature(training_source_files),
        update=update, selection_metric=FUTURE_SELECTION_METRIC, validation_metric=validation_metric,
        base_frozen=True, checkpoint_unchanged=True, training_complete=training_complete, **extra))


def _validate_receipt(receipt, metadata):
    if receipt.get("schema") != FUTURE_SCHEMA or receipt.get("kind") != "deployment_receipt":
        raise ValueError("G1-F requires its deployment receipt")
    if receipt.get("metadata") != metadata or receipt.get("metadata_sha256") != json_signature(metadata):
        raise ValueError("receipt/checkpoint metadata mismatch")
    if json_signature(receipt["training_config"]) != metadata["config_sha256"] or json_signature(receipt["pair_config"]) != metadata["pair_id"]:
        raise ValueError("receipt config/pair signature mismatch")
    if receipt["training_config"] != {**receipt["pair_config"], "arm": metadata["arm"]} or receipt["pair_config"].get("seed") != metadata["seed"]:
        raise ValueError("A/B configuration must differ only by its explicit arm")
    _sha(receipt["checkpoint_sha256"], "checkpoint_sha256")
    _sha(receipt["f01_report_sha256"], "f01_report_sha256")
    planned = receipt["planned_updates"]
    if type(planned) is not int or planned <= 0 or receipt["completed_updates"] != planned or receipt.get("training_complete") is not True or receipt.get("base_frozen") is not True or receipt.get("checkpoint_unchanged") is not True:
        raise ValueError("deployment requires completed bounded training with unchanged base")
    common = receipt["pair_config"]
    if common.get("suite", "libero_spatial") != metadata.get("suite", "libero_spatial"):
        raise ValueError("G1-F receipt and checkpoint suites differ")
    if common.get("training", {}).get("updates") != planned or common.get("selection", {}).get("metric") != FUTURE_SELECTION_METRIC:
        raise ValueError("completed training budget/metric differs from the frozen common config")
    if any(common.get(key) != metadata[key] for key in ("scorer_dimensions", "model_revision", "stats_key")):
        raise ValueError("checkpoint architecture/base differs from the common A/B config")
    rows = receipt["evaluations"]
    updates = [row["update"] for row in rows]
    if not rows or any(type(i) is not int for i in updates) or updates != sorted(set(updates)) or updates[0] != 0 or updates[-1] != planned:
        raise ValueError("complete ordered hard-validation history from0 to final update is required")
    if updates != common.get("selection", {}).get("updates"):
        raise ValueError("validation updates differ from the frozen common schedule")
    if any(not isinstance(row["validation_metric"], (int, float)) or not math.isfinite(row["validation_metric"]) or row["validation_metric"] < 0 for row in rows):
        raise ValueError("validation history contains an invalid hard teacher L1")
    best = min(rows, key=lambda row: (row["validation_metric"], row["update"]))
    if (metadata["update"], metadata["validation_metric"]) != (best["update"], best["validation_metric"]):
        raise ValueError("checkpoint is not the lowest hard-validation L1 with earliest tie")


def make_future_deployment_receipt(checkpoint_path, metadata, *, training_config,
        pair_config, f01_report_sha256, planned_updates, completed_updates, evaluations) -> dict:
    """Call only after training and final base verification have completed.

    A best checkpoint saved earlier may have training_complete=False. This
    final receipt binds its bytes to the complete bounded training history.
    """
    metadata = _metadata(metadata)
    receipt = dict(schema=FUTURE_SCHEMA, kind="deployment_receipt", metadata=metadata,
        metadata_sha256=json_signature(metadata), checkpoint_sha256=file_sha256(checkpoint_path),
        training_config=dict(training_config), pair_config=dict(pair_config),
        f01_report_sha256=f01_report_sha256, planned_updates=planned_updates,
        completed_updates=completed_updates, evaluations=list(evaluations),
        training_complete=True, base_frozen=True, checkpoint_unchanged=True)
    _validate_receipt(receipt, metadata)
    return receipt


def require_future_f01(report, *, pair_id, window_manifest_sha256, model_revision,
                       suite="libero_spatial", input_acceptance_sha256=None):
    """Only the recorded real-model F01 acceptance can open this dev runner."""
    if suite not in FUTURE_SUITES or report.get("suite", "libero_spatial") != suite:
        raise ValueError("G1-F requires its own suite's real-model F01")
    expected = {"stage": "G1-F01", "status": "passed", "execution": "real_frozen_openvla_l40",
        "config_sha256": pair_id, "window_manifest_sha256": window_manifest_sha256,
        "model_revision": model_revision, "input_version": libero_runtime.INPUTS_VERSION,
        "packing_version": PACKING_VERSION}
    checks = ("time_alignment", "no_future_leakage", "action_gradient_to_die", "future_gradient_to_die",
              "vla_parameters_unchanged", "hard128_packing", "dense_differentiable_parity")
    if any(report.get(key) != value for key, value in expected.items()) or any(report.get("checks", {}).get(key) is not True for key in checks):
        raise ValueError("G1-F deployment requires matching real-model F01 acceptance, not a CPU test")
    if suite == "libero_10":
        _sha(report.get("input_acceptance_sha256"), "Long input acceptance")
        if report.get("stats_key") != FUTURE_SUITES[suite] or report.get("checks", {}).get("official_input_action_parity") is not True:
            raise ValueError("Long F01 requires its own official input/action parity")
        if input_acceptance_sha256 is not None and report["input_acceptance_sha256"] != input_acceptance_sha256:
            raise ValueError("Long F01 input-acceptance receipt changed")


def future_deployment_source_hashes(source_root):
    root = Path(source_root)
    paths = [*sorted((root / "src/cti_vla/models").rglob("*.py")),
             *sorted((root / "src/cti_vla/selection").rglob("*.py")),
             root / "src/cti_vla/training/future_auxiliary.py",
             root / "src/cti_vla_baselines/acl_matched.py",
             root / "src/cti_vla/evaluation/libero_runtime.py"]
    if any(not path.is_file() for path in paths):
        raise ValueError("G1-F shared deployment source is incomplete")
    return {path.relative_to(root).as_posix(): file_sha256(path) for path in paths}


@dataclass(frozen=True)
class LoadedFutureSelector:
    estimator: ConditionalInfluenceEstimator
    provenance: Mapping


def load_future_selector_checkpoint(path, receipt: Mapping, *, expected_versions: Mapping,
        expected_source_hashes: Mapping, device="cpu") -> LoadedFutureSelector:
    """Safely load only DIE; never construct or run an auxiliary future head."""
    path = Path(path)
    digest = file_sha256(path)
    if digest != receipt.get("checkpoint_sha256"):
        raise ValueError("G1-F checkpoint bytes differ from the deployment receipt")
    saved = torch.load(path, map_location="cpu", weights_only=True)
    metadata = _metadata(saved)
    _validate_receipt(receipt, metadata)
    if metadata.get("suite", "libero_spatial") != expected_versions.get("suite", "libero_spatial"):
        raise ValueError("G1-F deployment identity mismatch: suite")
    if metadata.get("suite") == "libero_10" and metadata["input_acceptance_sha256"] != expected_versions.get("input_acceptance_sha256"):
        raise ValueError("Long deployment requires the accepted input-parity receipt")
    for key in ("model_revision", "input_version", "packing_version", "stats_key", "window_manifest_sha256"):
        if not expected_versions.get(key) or metadata[key] != expected_versions[key]:
            raise ValueError(f"G1-F deployment identity mismatch: {key}")
    if receipt["f01_report_sha256"] != expected_versions.get("f01_report_sha256"):
        raise ValueError("G1-F checkpoint was not accepted by the supplied F01 evidence")
    if not expected_source_hashes or any(metadata["training_source_files"].get(key) != value for key, value in expected_source_hashes.items()):
        raise ValueError("G1-F producer/deployment implementation differs")
    dimensions = metadata["scorer_dimensions"]
    estimator = ConditionalInfluenceEstimator(dimensions["token_dim"], dimensions["language_dim"],
        dimensions["proprio_dim"], **{key: dimensions[key] for key in DIMENSIONS[3:]})
    weights = saved["estimator_state_dict"]
    if not isinstance(weights, Mapping) or not weights or any(not isinstance(t, torch.Tensor) or t.dtype != torch.float32 or not torch.isfinite(t).all() for t in weights.values()):
        raise ValueError("G1-F deployed DIE weights must be finite FP32 tensors")
    estimator.load_state_dict(weights, strict=True)
    estimator.to(device=device, dtype=torch.float32).eval().requires_grad_(False)
    if file_sha256(path) != digest:
        raise ValueError("G1-F checkpoint changed while loading")
    return LoadedFutureSelector(estimator, {**metadata, "selector_checkpoint_sha256": digest,
        "deployment_receipt_sha256": json_signature(receipt), "f01_report_sha256": receipt["f01_report_sha256"],
        "runtime_version": FUTURE_RUNTIME_VERSION, "future_head_deployed": False,
        "selection_mode": "full512_score_once_camera64", "condition_mode": "all",
        "condition_version": f"{libero_runtime.INPUTS_VERSION}:{metadata['stats_key']}:frozen-prompt-embeddings"})


def validate_future_pair(a: LoadedFutureSelector, b: LoadedFutureSelector) -> None:
    if (a.provenance.get("arm"), b.provenance.get("arm")) != ("A", "B"):
        raise ValueError("paired evaluation requires distinct A and B checkpoints")
    if a.provenance.get("suite", "libero_spatial") != b.provenance.get("suite", "libero_spatial") or a.provenance.get("input_acceptance_sha256") != b.provenance.get("input_acceptance_sha256"):
        raise ValueError("G1-F A/B suite/input acceptance mismatch")
    for key in ("pair_id", "seed", "window_manifest_sha256", "model_revision", "input_version",
                "packing_version", "stats_key", "scorer_dimensions", "training_source_sha256", "f01_report_sha256"):
        if a.provenance.get(key) != b.provenance.get(key):
            raise ValueError(f"G1-F A/B paired identity mismatch: {key}")


class FutureRolloutPolicy:
    """Raw observation -> one full-set score -> one hard128 VLA forward."""
    def __init__(self, components, processor, selector: LoadedFutureSelector, *, stats_key,
                 stage_context=None, record_selection=True):
        from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
        self.components, self.processor, self.selector = components, processor, selector
        self.stats_key, self.record_selection = stats_key, record_selection
        self.stage_context = stage_context or (lambda _: nullcontext())
        self.device, self.dtype = next(components.vla.parameters()).device, next(components.vla.parameters()).dtype
        provenance = selector.provenance
        if stats_key not in components.vla.norm_stats or provenance.get("stats_key") != stats_key:
            raise ValueError("G1-F normalization key differs from the checkpoint")
        if provenance.get("input_version") != libero_runtime.INPUTS_VERSION or provenance.get("packing_version") != PACKING_VERSION or provenance.get("selection_mode") != "full512_score_once_camera64" or provenance.get("future_head_deployed") is not False:
            raise ValueError("G1-F deployment input/packing/selection contract mismatch")
        if next(selector.estimator.parameters()).device != self.device or selector.estimator.training or any(p.requires_grad or p.dtype != torch.float32 for p in selector.estimator.parameters()):
            raise ValueError("deployed DIE must be frozen FP32 eval on the VLA device")
        self.token_policy = OpenVLAOFTTokenPolicy(components.vla, components.action_head,
            components.proprio_projector, num_patches_full=512)
        self.camera_ids = torch.arange(2, device=self.device).repeat_interleave(256)[None]
        self.patch_ids = torch.arange(256, device=self.device).repeat(2)[None]
        self.valid = torch.ones(1, 512, dtype=torch.bool, device=self.device)

    def reset(self):
        """No observation, selection, action or instruction cache exists."""

    def clear_instruction_cache(self):
        """Profiling hook: language is recomputed for every call."""

    def prepare_instruction(self, instruction):
        """Profiling hook: no language priming is performed or claimed."""

    @torch.no_grad()
    def __call__(self, observation, instruction):
        # Shared hard selection is also used by G1-F validation/training checks.
        from cti_vla.training.future_auxiliary import hard_select_future
        vla, scorer = self.components.vla, self.selector.estimator
        if vla.training or scorer.training:
            raise ValueError("G1-F deployment modules must remain in eval mode")
        with self.stage_context("preprocess"):
            inputs = libero_runtime.prepare_observation_inputs(observation, instruction, self.processor,
                vla.norm_stats[self.stats_key]["proprio"], device=self.device, dtype=self.dtype)
        with self.stage_context("vision"):
            visual = vla._process_vision_features(inputs["pixel_values"], None, False).detach()
            if visual.ndim != 3 or visual.shape[:2] != (1, 512):
                raise ValueError("G1-F requires full camera-major512 visual features")
        with self.stage_context("condition_selection"):
            language = vla.get_input_embeddings()(inputs["input_ids"]).detach()
            batch = ConditionalTokenBatch(visual, language, inputs["attention_mask"].bool(),
                inputs["normalized_proprio"].detach(), self.camera_ids, self.patch_ids, self.valid)
            selection = hard_select_future(scorer, batch)
        with self.stage_context("policy"):
            normalized = self.token_policy.forward_from_full_tokens(visual, inputs["normalized_proprio"],
                input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"], retained_indices=selection.source_indices)
        with self.stage_context("postprocess"):
            normalized = normalized.float().cpu().numpy()[0]
            actions = libero_runtime.postprocess_actions(vla._unnormalize_actions(normalized, self.stats_key))
            metadata = {"method": f"future_{self.selector.provenance['arm']}", "visual_tokens": 128,
                "per_camera_budgets": [64, 64], "inputs_version": libero_runtime.INPUTS_VERSION,
                "action_version": libero_runtime.ACTION_VERSION, "packing_version": PACKING_VERSION,
                "runtime_version": FUTURE_RUNTIME_VERSION, "policy_calls": 1, "vision_calls": 1,
                "scorer_calls": 1, "future_head_calls": 0, "language_cache": "disabled",
                "selector_checkpoint_sha256": self.selector.provenance["selector_checkpoint_sha256"],
                "pair_id": self.selector.provenance["pair_id"], "diagnostic_indices_recorded": self.record_selection}
            if self.record_selection:
                metadata["retained_indices"] = selection.source_indices[0].cpu().tolist()
            return libero_runtime.PolicyChunk(normalized, actions, metadata)

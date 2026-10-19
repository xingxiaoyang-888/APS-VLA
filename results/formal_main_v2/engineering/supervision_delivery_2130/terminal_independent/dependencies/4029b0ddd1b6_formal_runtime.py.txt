"""Independent formal_main_v2 checkpoints and single-pass hard deployment.

Historical G1-F schemas are deliberately not accepted by this module. A
formal checkpoint binds a trained budget, suite, complete5000-update history,
frozen model, data protocol and task-macro validation selection rule.
"""
from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Mapping

import numpy as np
import torch

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation import libero_runtime
from cti_vla.evaluation.teacher_diagnostics import json_signature
from cti_vla.models.abstraction.packing import PACKING_VERSION
from cti_vla.selection import ConditionalInfluenceEstimator, ConditionalTokenBatch

FORMAL_SCHEMA = "formal_main_v2"
FORMAL_SELECTION_METRIC = "task_macro_hard_validation_teacher_l1"
FORMAL_SUITES = {name: {"stats_key": name + "_no_noops", "max_steps": limit} for name, limit in
    (("libero_spatial", 220), ("libero_object", 280), ("libero_goal", 300), ("libero_10", 520))}
FORMAL_BUDGETS = (256, 128, 64)
FORMAL_SEEDS = (17, 23, 41)
FORMAL_EVALUATION_UPDATES = tuple(range(0, 5001, 500))
DIMENSIONS = ("token_dim", "language_dim", "proprio_dim", "hidden_dim", "num_cameras",
    "patches_per_camera", "max_instruction_tokens")
METADATA_FIELDS = ("schema", "suite", "arm", "seed", "scorer_dimensions", "config_sha256", "pair_id",
    "window_manifest_sha256", "model_revision", "stats_key", "input_version", "packing_version",
    "training_source_files", "training_source_sha256", "update", "selection_metric", "validation_metric",
    "base_frozen", "checkpoint_unchanged", "training_complete", "input_acceptance_sha256",
    "frozen_model_sha256", "data_protocol_sha256", "selection_protocol_sha256", "visual_tokens", "per_camera_budgets")


def require_sha(value, name):
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(name + " must be a SHA256 hex digest")


def formal_budget(value):
    total = value.get("visual_tokens")
    cameras = value.get("per_camera_budgets")
    if (type(total) is not int or total not in FORMAL_BUDGETS or not isinstance(cameras, (list, tuple))
            or len(cameras) != 2 or any(type(k) is not int for k in cameras) or list(cameras) != [total // 2] * 2):
        raise ValueError("formal checkpoint requires its explicit trained256/128/64 equal-view budget")
    return total // 2


def formal_runtime_version(total):
    formal_budget({"visual_tokens": total, "per_camera_budgets": [total // 2] * 2})
    return f"formal-main-v2-full512-score-once-hard{total}"


def formal_metadata(value):
    try:
        result = {key: value[key] for key in METADATA_FIELDS}
    except KeyError as exc:
        raise ValueError("formal checkpoint metadata is incomplete: " + str(exc)) from exc
    if (result["schema"] != FORMAL_SCHEMA or result["suite"] not in FORMAL_SUITES
            or result["arm"] not in ("A", "B") or type(result["seed"]) is not int or result["seed"] not in FORMAL_SEEDS):
        raise ValueError("formal checkpoints require the registered suite/arm/seed schema")
    formal_budget(result)
    if result["stats_key"] != FORMAL_SUITES[result["suite"]]["stats_key"]:
        raise ValueError("formal suite and normalization key differ")
    for key in ("config_sha256", "pair_id", "window_manifest_sha256", "training_source_sha256",
            "input_acceptance_sha256", "frozen_model_sha256", "data_protocol_sha256", "selection_protocol_sha256"):
        require_sha(result[key], key)
    sources = result["training_source_files"]
    if not isinstance(sources, Mapping) or not sources or json_signature(sources) != result["training_source_sha256"]:
        raise ValueError("formal training source signature is missing or changed")
    for path, digest in sources.items():
        if not isinstance(path, str) or path.startswith("/") or ":" in path or "\\" in path or ".." in Path(path).parts:
            raise ValueError("formal source keys must be project-relative POSIX paths")
        require_sha(digest, path)
    dims = result["scorer_dimensions"]
    if (not isinstance(dims, Mapping) or set(dims) != set(DIMENSIONS)
            or any(type(dims[k]) is not int or dims[k] <= 0 for k in DIMENSIONS)
            or tuple(dims[k] for k in DIMENSIONS[2:3] + DIMENSIONS[4:]) != (8, 2, 256, 128)):
        raise ValueError("formal DIE dimensions require proprio8 and2x256 original visual tokens")
    if type(result["update"]) is not int or result["update"] not in FORMAL_EVALUATION_UPDATES:
        raise ValueError("formal checkpoint must come from its500-update validation schedule")
    metric = result["validation_metric"]
    if (result["selection_metric"] != FORMAL_SELECTION_METRIC or isinstance(metric, bool)
            or not isinstance(metric, (int, float)) or not math.isfinite(metric) or metric < 0):
        raise ValueError("formal checkpoint selection requires finite task-macro hard teacher L1")
    if (result["input_version"] != libero_runtime.INPUTS_VERSION or result["packing_version"] != PACKING_VERSION
            or not isinstance(result["model_revision"], str) or not result["model_revision"]
            or result["base_frozen"] is not True or result["checkpoint_unchanged"] is not True
            or type(result["training_complete"]) is not bool):
        raise ValueError("formal frozen model/input/packing identity is invalid")
    return result


def make_formal_checkpoint_metadata(*, arm, seed, scorer_dimensions, training_config, pair_config,
        window_manifest_sha256, model_revision, stats_key, training_source_files, update, validation_metric,
        input_acceptance_sha256, frozen_model_sha256, data_protocol_sha256, selection_protocol_sha256,
        training_complete=False):
    budget = pair_config["tokens_per_camera"]
    return formal_metadata(dict(schema=FORMAL_SCHEMA, suite=pair_config["suite"], arm=arm, seed=seed,
        scorer_dimensions=dict(scorer_dimensions), config_sha256=json_signature(training_config),
        pair_id=json_signature(pair_config), window_manifest_sha256=window_manifest_sha256,
        model_revision=model_revision, stats_key=stats_key, input_version=libero_runtime.INPUTS_VERSION,
        packing_version=PACKING_VERSION, training_source_files=dict(training_source_files),
        training_source_sha256=json_signature(training_source_files), update=update,
        selection_metric=FORMAL_SELECTION_METRIC, validation_metric=validation_metric, base_frozen=True,
        checkpoint_unchanged=True, training_complete=training_complete, input_acceptance_sha256=input_acceptance_sha256,
        frozen_model_sha256=frozen_model_sha256, data_protocol_sha256=data_protocol_sha256,
        selection_protocol_sha256=selection_protocol_sha256, visual_tokens=2 * budget, per_camera_budgets=[budget] * 2))


def validate_formal_receipt(receipt, metadata):
    metadata = formal_metadata(metadata)
    if receipt.get("schema") != FORMAL_SCHEMA or receipt.get("kind") != "deployment_receipt":
        raise ValueError("formal deployment never accepts historical pilot receipts")
    if receipt.get("metadata") != metadata or receipt.get("metadata_sha256") != json_signature(metadata):
        raise ValueError("formal receipt/checkpoint metadata differs")
    pair = receipt["pair_config"]
    if (json_signature(pair) != metadata["pair_id"] or receipt["training_config"] != {**pair, "arm": metadata["arm"]}
            or json_signature(receipt["training_config"]) != metadata["config_sha256"]):
        raise ValueError("formal matched A/B training configuration differs")
    if (pair.get("schema") != FORMAL_SCHEMA or pair.get("seed") != metadata["seed"]
            or pair.get("suite") != metadata["suite"] or pair.get("tokens_per_camera") != formal_budget(metadata)
            or any(pair.get(key) != metadata[key] for key in ("scorer_dimensions", "model_revision", "stats_key"))):
        raise ValueError("formal trained suite/budget/seed/base differs from receipt")
    if (receipt.get("planned_updates") != 5000 or receipt.get("completed_updates") != 5000
            or pair.get("training", {}).get("updates") != 5000 or pair.get("training", {}).get("effective_batch") != 8
            or metadata["training_complete"] is not True
            or any(receipt.get(key) is not True for key in ("training_complete", "base_frozen", "checkpoint_unchanged"))):
        raise ValueError("formal deployment requires completed5000-update batch8 training")
    if (pair.get("selection", {}).get("metric") != FORMAL_SELECTION_METRIC
            or tuple(pair.get("selection", {}).get("updates", [])) != FORMAL_EVALUATION_UPDATES
            or json_signature(pair["selection"]) != metadata["selection_protocol_sha256"]):
        raise ValueError("formal task-macro validation selection protocol changed")
    rows = receipt.get("evaluations", [])
    if tuple(row.get("update") for row in rows) != FORMAL_EVALUATION_UPDATES:
        raise ValueError("formal receipt requires complete ordered0..5000 validation history")
    if any(isinstance(row.get("validation_metric"), bool) or not isinstance(row.get("validation_metric"), (int, float))
            or not math.isfinite(row["validation_metric"]) or row["validation_metric"] < 0 for row in rows):
        raise ValueError("formal validation history is invalid")
    best = min(rows, key=lambda row: (row["validation_metric"], row["update"]))
    if (metadata["update"], metadata["validation_metric"]) != (best["update"], best["validation_metric"]):
        raise ValueError("formal best checkpoint is not minimum task-macro L1 with earliest tie")
    for key in ("checkpoint_sha256", "f01_report_sha256"):
        require_sha(receipt.get(key), key)


def make_formal_deployment_receipt(checkpoint_path, metadata, *, training_config, pair_config,
        f01_report_sha256, planned_updates, completed_updates, evaluations):
    metadata = formal_metadata(metadata)
    receipt = dict(schema=FORMAL_SCHEMA, kind="deployment_receipt", metadata=metadata,
        metadata_sha256=json_signature(metadata), checkpoint_sha256=file_sha256(checkpoint_path),
        training_config=dict(training_config), pair_config=dict(pair_config), f01_report_sha256=f01_report_sha256,
        planned_updates=planned_updates, completed_updates=completed_updates, evaluations=list(evaluations),
        training_complete=True, base_frozen=True, checkpoint_unchanged=True)
    validate_formal_receipt(receipt, metadata)
    return receipt


def formal_deployment_source_hashes(source_root):
    root = Path(source_root)
    paths = [*sorted((root / "src/cti_vla/models").rglob("*.py")),
        *sorted((root / "src/cti_vla/selection").rglob("*.py")),
        *[root / name for name in ("src/cti_vla/training/formal_future.py", "src/cti_vla/training/future_auxiliary.py",
            "src/cti_vla_baselines/acl_matched.py", "src/cti_vla/evaluation/libero_runtime.py",
            "src/cti_vla/evaluation/formal_runtime.py")]]
    if any(not path.is_file() for path in paths):
        raise ValueError("formal deployment source is incomplete")
    return {path.relative_to(root).as_posix(): file_sha256(path) for path in paths}


@dataclass(frozen=True)
class LoadedFormalSelector:
    estimator: ConditionalInfluenceEstimator
    provenance: Mapping


def load_formal_selector_checkpoint(path, receipt, *, expected_versions, expected_source_hashes, device="cpu"):
    path = Path(path)
    digest = file_sha256(path)
    if digest != receipt.get("checkpoint_sha256"):
        raise ValueError("formal checkpoint bytes differ from receipt")
    saved = torch.load(path, map_location="cpu", weights_only=True)
    metadata = formal_metadata(saved)
    validate_formal_receipt(receipt, metadata)
    for key in ("suite", "visual_tokens", "per_camera_budgets", "model_revision", "stats_key", "input_version",
            "packing_version", "window_manifest_sha256", "input_acceptance_sha256", "frozen_model_sha256",
            "data_protocol_sha256", "selection_protocol_sha256"):
        if expected_versions.get(key) != metadata[key]:
            raise ValueError("formal deployment identity mismatch: " + key)
    if receipt["f01_report_sha256"] != expected_versions.get("f01_report_sha256"):
        raise ValueError("formal checkpoint has a different suite/budget engineering gate")
    if not expected_source_hashes or any(metadata["training_source_files"].get(k) != v for k, v in expected_source_hashes.items()):
        raise ValueError("formal producer/deployment source changed")
    estimator = ConditionalInfluenceEstimator(**metadata["scorer_dimensions"])
    state = saved["estimator_state_dict"]
    if not state or any(not isinstance(v, torch.Tensor) or v.dtype != torch.float32 or not torch.isfinite(v).all() for v in state.values()):
        raise ValueError("formal DIE state must contain finite FP32 tensors")
    estimator.load_state_dict(state, strict=True)
    estimator.to(device=device, dtype=torch.float32).eval().requires_grad_(False)
    if file_sha256(path) != digest:
        raise ValueError("formal checkpoint changed during loading")
    return LoadedFormalSelector(estimator, {**metadata, "selector_checkpoint_sha256": digest,
        "deployment_receipt_sha256": json_signature(receipt), "f01_report_sha256": receipt["f01_report_sha256"],
        "runtime_version": formal_runtime_version(metadata["visual_tokens"]), "future_head_deployed": False,
        "selection_mode": f"full512_score_once_camera{formal_budget(metadata)}", "condition_mode": "all"})


def validate_formal_pair(a, b):
    if (a.provenance["arm"], b.provenance["arm"]) != ("A", "B"):
        raise ValueError("formal A/B pair requires distinct arms")
    for key in ("pair_id", "suite", "seed", "window_manifest_sha256", "visual_tokens", "per_camera_budgets",
            "model_revision", "stats_key", "input_version", "packing_version", "scorer_dimensions", "training_source_sha256",
            "f01_report_sha256", "input_acceptance_sha256", "frozen_model_sha256", "data_protocol_sha256", "selection_protocol_sha256"):
        if a.provenance.get(key) != b.provenance.get(key):
            raise ValueError("formal paired identity mismatch: " + key)


def uniform_formal_indices(total):
    """Nested top-left grids;128 is byte-identical to historical G0 uniform128."""
    if type(total) is not int or total not in FORMAL_BUDGETS:
        raise ValueError("formal uniform supports256/128/64 tokens")
    row_step, column_step = {64: (4, 2), 128: (2, 2), 256: (2, 1)}[total]
    local = (np.arange(0, 16, row_step)[:, None] * 16 + np.arange(0, 16, column_step)[None, :]).reshape(-1)
    return np.concatenate((local, local + 256)).astype(np.int64)


class FormalRolloutPolicy:
    """Raw observation to action: dense/uniform or one DIE score and hard Top-k."""
    def __init__(self, components, processor, *, suite, method, total_tokens, selector=None,
            stage_context=None, record_selection=True):
        from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
        if suite not in FORMAL_SUITES or method not in ("dense", "uniform", "A", "B"):
            raise ValueError("unsupported formal deployment suite/method")
        if method == "dense":
            if total_tokens != 512 or selector is not None:
                raise ValueError("formal dense is512 tokens with no selector")
        else:
            formal_budget({"visual_tokens": total_tokens, "per_camera_budgets": [total_tokens // 2] * 2})
        if method == "uniform" and selector is not None:
            raise ValueError("formal uniform has no learned selector")
        self.components, self.processor, self.selector = components, processor, selector
        self.suite, self.method, self.total_tokens = suite, method, total_tokens
        self.stats_key = FORMAL_SUITES[suite]["stats_key"]
        self.component_timing = stage_context is not None
        self.stage_context = stage_context or (lambda _: nullcontext())
        self.record_selection = record_selection
        self.device, self.dtype = next(components.vla.parameters()).device, next(components.vla.parameters()).dtype
        if self.stats_key not in components.vla.norm_stats:
            raise ValueError("formal base lacks suite normalization statistics")
        if method in ("A", "B"):
            p = selector.provenance if selector is not None else {}
            if (p.get("schema") != FORMAL_SCHEMA or p.get("suite") != suite or p.get("arm") != method
                    or p.get("visual_tokens") != total_tokens or p.get("stats_key") != self.stats_key
                    or p.get("future_head_deployed") is not False or p.get("input_version") != libero_runtime.INPUTS_VERSION
                    or p.get("packing_version") != PACKING_VERSION):
                raise ValueError("formal policy differs from trained checkpoint contract")
            if (next(selector.estimator.parameters()).device != self.device or selector.estimator.training
                    or any(v.requires_grad or v.dtype != torch.float32 for v in selector.estimator.parameters())):
                raise ValueError("formal DIE must be frozen FP32 eval on the VLA device")
        self.token_policy = OpenVLAOFTTokenPolicy(components.vla, components.action_head, components.proprio_projector, num_patches_full=512)
        self.camera_ids = torch.arange(2, device=self.device).repeat_interleave(256)[None]
        self.patch_ids = torch.arange(256, device=self.device).repeat(2)[None]
        self.valid = torch.ones((1, 512), dtype=torch.bool, device=self.device)
        self.uniform = torch.as_tensor(uniform_formal_indices(total_tokens), device=self.device)[None] if method == "uniform" else None

    def reset(self):
        """No hidden observation, instruction, selection or action cache."""

    def clear_instruction_cache(self):
        """No language cache exists."""

    def prepare_instruction(self, instruction):
        """No language priming occurs."""

    def _policy_forward(self, visual, inputs, retained):
        def call():
            return self.token_policy.forward_from_full_tokens(visual, inputs["normalized_proprio"],
                input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"], retained_indices=retained)
        if not self.component_timing:
            return call()
        # Component-only instrumentation. It observes the shared implementation
        # without replacing packing, position IDs, action slices or model code.
        active = [None]
        transitioned = [False]
        def before_backbone(_module, _args):
            if transitioned[0]:
                raise RuntimeError("formal deployment invoked the VLA backbone twice")
            active[0].__exit__(None, None, None)
            active[0] = self.stage_context("llm_action")
            active[0].__enter__()
            transitioned[0] = True
        handle = self.token_policy.prefix_adapter.language_backbone.register_forward_pre_hook(before_backbone)
        active[0] = self.stage_context("packing")
        active[0].__enter__()
        try:
            result = call()
            if not transitioned[0]:
                raise RuntimeError("formal deployment did not invoke its VLA backbone")
            return result
        finally:
            active[0].__exit__(None, None, None)
            handle.remove()

    @torch.no_grad()
    def __call__(self, observation, instruction):
        vla = self.components.vla
        if vla.training:
            raise ValueError("formal VLA must remain frozen in eval mode")
        with self.stage_context("preprocess"):
            inputs = libero_runtime.prepare_observation_inputs(observation, instruction, self.processor,
                vla.norm_stats[self.stats_key]["proprio"], device=self.device, dtype=self.dtype)
        with self.stage_context("vision"):
            visual = vla._process_vision_features(inputs["pixel_values"], None, False).detach()
            if visual.shape[:2] != (1, 512) or visual.ndim != 3:
                raise ValueError("formal policy requires complete camera-major512 visual features")
        retained = self.uniform
        with self.stage_context("condition_selection"):
            if self.selector is not None:
                from cti_vla.training.formal_future import formal_hard_select
                language = vla.get_input_embeddings()(inputs["input_ids"]).detach()
                conditions = ConditionalTokenBatch(visual, language, inputs["attention_mask"].bool(),
                    inputs["normalized_proprio"].detach(), self.camera_ids, self.patch_ids, self.valid)
                retained = formal_hard_select(self.selector.estimator, conditions,
                    tokens_per_camera=self.total_tokens // 2).source_indices
        normalized = self._policy_forward(visual, inputs, retained)
        with self.stage_context("postprocess"):
            normalized = normalized.float().cpu().numpy()[0]
            actions = libero_runtime.postprocess_actions(vla._unnormalize_actions(normalized, self.stats_key))
            metadata = {"schema": FORMAL_SCHEMA, "suite": self.suite, "method": self.method, "visual_tokens": self.total_tokens,
                "per_camera_budgets": [self.total_tokens // 2] * 2, "inputs_version": libero_runtime.INPUTS_VERSION,
                "action_version": libero_runtime.ACTION_VERSION, "packing_version": PACKING_VERSION,
                "policy_calls": 1, "vision_calls": 1, "scorer_calls": int(self.selector is not None), "packing_calls": 1,
                "future_head_calls": 0, "language_cache": "disabled", "diagnostic_indices_recorded": self.record_selection}
            if self.selector is not None:
                metadata.update(selector_checkpoint_sha256=self.selector.provenance["selector_checkpoint_sha256"],
                    pair_id=self.selector.provenance["pair_id"], training_seed=self.selector.provenance["seed"])
            if self.record_selection:
                metadata["retained_indices"] = list(range(512)) if retained is None else retained[0].cpu().tolist()
            return libero_runtime.PolicyChunk(normalized, actions, metadata)

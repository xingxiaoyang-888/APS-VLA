"""Formal-main-v2 training: matched A/B, bounded memory, transactional resume.

This module leaves the historical small-panel G1-F contracts unchanged. The
loss is the same ACL-style action objective and fixed future auxiliary head;
only the separately registered data pool, update schedule and budget differ.
"""
from __future__ import annotations

from collections import defaultdict
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time
from typing import Callable, Mapping, Protocol, Sequence
import uuid

import numpy as np
import torch
from torch.nn import functional as F

from cti_vla.evaluation.teacher_diagnostics import json_signature, tensor_signature
from cti_vla.selection import ConditionalInfluenceEstimator, ConditionalTokenBatch, staged_topk
from cti_vla.training.future_auxiliary import (
    FutureAuxiliaryHead, FutureLossOutput, FutureTrainingBatch, validate_full_conditions,
)
from cti_vla_baselines.acl_matched import (
    FrozenDifferentiableOFTPolicy, cosine_alpha, gate_raw_tokens, soft_top_k,
)

FORMAL_SCHEMA = "formal_main_v2"
FORMAL_METRIC = "task_macro_hard_validation_teacher_l1"
FORMAL_TRAINING_VERSION = "formal-main-v2-acl-half-teacher-half-gt-future-fixed-v1"
FORMAL_ORDER_VERSION = "python-random-private-seeded-full-pool-shuffle-cycle-v1"
FORMAL_RESUME_VERSION = "formal-main-v2-optimizer-rng-next-sample-transaction-v1"
FORMAL_NUMERICS = {
    "version": "formal-training-deterministic-sdpa-v1",
    "deterministic_algorithms": True,
    "warn_only": False,
    "cublas_workspace_config": ":4096:8",
    "cudnn_benchmark": False,
    "cudnn_deterministic": True,
    "soft_student_sdpa": "efficient-or-math; flash-disabled",
    "hard_inference_sdpa": "unchanged-runtime-default",
}


def configure_formal_training_numerics() -> dict:
    """Set the engineering reproducibility contract before CUDA initialization.

    PyTorch 2.2 flash SDPA backward has no deterministic implementation. Only
    the differentiable student forward selects efficient/math SDPA below;
    teacher, hard validation and deployed inference keep their usual dispatch.
    The deterministic flag must remain enabled during the later backward.
    """
    workspace = FORMAL_NUMERICS["cublas_workspace_config"]
    if torch.cuda.is_initialized() and os.environ.get("CUBLAS_WORKSPACE_CONFIG") != workspace:
        raise RuntimeError("formal CUBLAS workspace must be configured before CUDA initialization")
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = workspace
    torch.use_deterministic_algorithms(True, warn_only=False)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    return dict(FORMAL_NUMERICS)


def formal_student_attention_context(device):
    """Scope the deterministic CUDA attention choice to the training student."""
    if torch.device(device).type != "cuda":
        return nullcontext()
    if (not torch.are_deterministic_algorithms_enabled()
            or torch.is_deterministic_algorithms_warn_only_enabled()
            or os.environ.get("CUBLAS_WORKSPACE_CONFIG") != FORMAL_NUMERICS["cublas_workspace_config"]
            or torch.backends.cudnn.benchmark or not torch.backends.cudnn.deterministic):
        raise RuntimeError("formal CUDA training numerics contract is not configured")
    return torch.backends.cuda.sdp_kernel(enable_flash=False, enable_mem_efficient=True, enable_math=True)


def formal_budget(tokens_per_camera: int) -> int:
    if type(tokens_per_camera) is not int or tokens_per_camera not in (32, 64, 128):
        raise ValueError("formal per-camera budget must be exactly32,64 or128")
    return tokens_per_camera


@torch.no_grad()
def formal_hard_select(scorer, conditions, *, tokens_per_camera: int):
    """One full-set score and one Top-k per view, with original packing order."""
    validate_full_conditions(conditions)
    budget = formal_budget(tokens_per_camera)
    if not isinstance(scorer, ConditionalInfluenceEstimator):
        raise TypeError("formal training requires the original conditional estimator")
    return staged_topk(scorer, conditions, ((budget, budget),))


def formal_auxiliary_loss(scorer, student, batch, *, alpha: float,
                          auxiliary_head=None, auxiliary_weight=.1,
                          projection_atol=1e-5, tokens_per_camera: int):
    """Historical loss math, under an independent three-budget contract.

The shared representation/head and black-feature mixing remain unchanged.
There is no future or demonstrated-action argument to the selector.
"""
    batch.validate()
    budget = formal_budget(tokens_per_camera)
    if not isinstance(scorer, ConditionalInfluenceEstimator) or not isinstance(student, FrozenDifferentiableOFTPolicy):
        raise TypeError("shared conditional estimator and differentiable frozen OFT student are required")
    if not math.isfinite(auxiliary_weight) or auxiliary_weight < 0 or not math.isfinite(projection_atol) or projection_atol < 0:
        raise ValueError("loss weight and projection tolerance must be finite and nonnegative")
    if auxiliary_head is not None and batch.future_target is None:
        raise ValueError("B requires a matched detached future_target")
    if auxiliary_head is not None and not isinstance(auxiliary_head, FutureAuxiliaryHead):
        raise TypeError("auxiliary_head must be FutureAuxiliaryHead")
    student.require_frozen()
    if not torch.is_grad_enabled():
        raise RuntimeError("formal training requires gradients through frozen VLA inputs")
    conditions = batch.conditions
    with torch.no_grad():
        check = student.visual_projector(batch.raw_tokens)
        if check.shape != conditions.visual.shape or check.dtype != conditions.visual.dtype or not torch.allclose(check, conditions.visual, atol=projection_atol, rtol=0):
            raise ValueError("raw features do not project to the current cached conditions")
    scores = scorer(conditions, conditions.valid)
    if scores.shape != (conditions.visual.shape[0], 512) or not torch.isfinite(scores).all():
        raise ValueError("full-set scorer must return finite [B,512] scores")
    gates = torch.cat([soft_top_k(scores[:, c * 256:(c + 1) * 256], budget, alpha) for c in range(2)], dim=1)
    gated_raw = gate_raw_tokens(batch.raw_tokens, gates, batch.black_tokens)
    gated_projected = student.visual_projector(gated_raw)
    source = torch.arange(512, device=scores.device)[None].expand(scores.shape[0], -1)
    with formal_student_attention_context(gated_projected.device):
        prediction = student(gated_projected, source, input_ids=batch.input_ids, attention_mask=batch.attention_mask,
                             normalized_proprio=conditions.normalized_proprio.to(gated_projected.dtype))
    teacher_l1 = (prediction.float() - batch.teacher_actions.float()).abs().mean()
    demonstration_l1 = (prediction.float() - batch.demonstration_actions.float()).abs().mean()
    action_loss = .5 * teacher_l1 + .5 * demonstration_l1
    future_mse = None
    loss = action_loss
    if auxiliary_head is not None:
        future_prediction = auxiliary_head(gated_projected, batch.demonstration_actions)
        future_mse = F.mse_loss(future_prediction, batch.future_target)
        loss = action_loss + auxiliary_weight * future_mse
    if not loss.requires_grad or not torch.isfinite(loss):
        raise RuntimeError("training loss must be finite and retain a scorer gradient path")
    student.require_frozen()
    return FutureLossOutput(loss, action_loss, teacher_l1, demonstration_l1, future_mse,
                            prediction, scores, gates, source, budget)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def formal_source_hashes(source_root: Path) -> dict:
    root = Path(source_root)
    paths = [*sorted((root / "src").rglob("*.py")), *[root / "scripts" / name for name in (
        "run_formal_future.py", "verify_formal_acceptance.py", "eval_formal_selector_libero.py", "verify_long_inputs.py")]]
    if any(not path.is_file() for path in paths):
        raise ValueError("formal training/acceptance/deployment source snapshot is incomplete")
    return {path.relative_to(root).as_posix(): file_sha256(path) for path in paths}


def _sync_directory(path: Path) -> None:
    if os.name != "nt":
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def atomic_torch_save(path: Path, payload) -> None:
    """Commit one complete file, never an in-place partial optimizer state."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".partial")
    with temporary.open("xb") as handle:
        torch.save(payload, handle)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    _sync_directory(path.parent)


def atomic_json_save(path: Path, payload) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".partial")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    _sync_directory(path.parent)


def append_event(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_torch(path: Path):
    return torch.load(path, map_location="cpu", weights_only=True)


def capture_rng() -> dict:
    numpy_state = np.random.get_state()
    return {"python": random.getstate(),
            "numpy": {"algorithm": numpy_state[0], "keys": numpy_state[1].tolist(),
                      "position": int(numpy_state[2]), "has_gauss": int(numpy_state[3]),
                      "cached_gaussian": float(numpy_state[4])},
            "torch_cpu": torch.get_rng_state().clone(),
            "torch_cuda": [x.clone().cpu() for x in torch.cuda.get_rng_state_all()] if torch.cuda.is_available() else []}


def restore_rng(state: dict) -> None:
    expected_devices = torch.cuda.device_count() if torch.cuda.is_available() else 0
    if len(state["torch_cuda"]) != expected_devices:
        raise ValueError("resume CUDA RNG topology differs from checkpoint")
    random.setstate(state["python"])
    value = state["numpy"]
    np.random.set_state((value["algorithm"], np.asarray(value["keys"], dtype=np.uint32),
                         value["position"], value["has_gauss"], value["cached_gaussian"]))
    torch.set_rng_state(state["torch_cpu"])
    if expected_devices:
        torch.cuda.set_rng_state_all(state["torch_cuda"])


def seed_training_rng(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed % (2**32))
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def cpu_state(module) -> dict:
    return {key: value.detach().cpu().clone() for key, value in module.state_dict().items()}


def parameter_fingerprint(modules: Mapping[str, torch.nn.Module]) -> str:
    """Stream every parameter and buffer, including the frozen vision branch."""
    digest = hashlib.sha256()
    for prefix, module in sorted(modules.items()):
        for name, value in module.state_dict().items():
            digest.update((prefix + "." + name).encode())
            digest.update(str((str(value.dtype), list(value.shape))).encode())
            digest.update(value.detach().contiguous().reshape(-1).view(torch.uint8).cpu().numpy().tobytes())
    return digest.hexdigest()


@dataclass(frozen=True)
class FormalTrainingSpec:
    seed: int
    tokens_per_camera: int
    updates: int = 5000
    effective_batch: int = 8
    validation_every: int = 500
    checkpoint_every: int = 50
    learning_rate: float = 1e-4
    weight_decay: float = .01
    gradient_clip_norm: float = 1.
    alpha_start: float = 2.
    alpha_end: float = .1
    future_weight: float = .1

    def __post_init__(self):
        formal_budget(self.tokens_per_camera)
        for name in ("seed", "updates", "effective_batch", "validation_every", "checkpoint_every"):
            value = getattr(self, name)
            if type(value) is not int or value < (0 if name == "seed" else 1):
                raise ValueError(f"invalid training {name}")
        if self.updates < 2 or self.updates % self.validation_every:
            raise ValueError("validation must include the final update")
        for name in ("learning_rate", "gradient_clip_norm", "alpha_start", "alpha_end"):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(f"invalid training {name}")
        if not 0 < self.alpha_end <= self.alpha_start or self.weight_decay < 0 or self.future_weight < 0:
            raise ValueError("invalid optimizer/loss/gating settings")

    @property
    def validation_updates(self):
        return list(range(0, self.updates + 1, self.validation_every))

    def alpha(self, update):
        return cosine_alpha(max(0, update - 1), self.updates - 1,
                            maximum=self.alpha_start, minimum=self.alpha_end)


def validate_formal_training_config(config: dict) -> FormalTrainingSpec:
    """Production guard. Smaller schedules are available only to CPU unit tests."""
    if config.get("schema") != FORMAL_SCHEMA or config.get("suite") not in (
            "libero_spatial", "libero_object", "libero_goal", "libero_10"):
        raise ValueError("formal config schema/suite mismatch")
    if config.get("stats_key") != config["suite"] + "_no_noops":
        raise ValueError("formal normalization key differs from suite")
    if type(config.get("seed")) is not int or config["seed"] not in (17, 23, 41) or config.get("arms") != ["A", "B"]:
        raise ValueError("formal main v2 registers all three seeds and A/B only")
    training = config["training"]
    fixed = {"updates": 5000, "micro_batch": 1, "effective_batch": 8, "optimizer": "AdamW",
             "learning_rate": 1e-4, "weight_decay": .01, "gradient_clip_norm": 1.,
             "dtype_vla": "bfloat16", "dtype_scorer": "float32", "same_initial_scorer": True,
             "vla_frozen": True, "gradient_through_vla": True, "checkpoint_every_updates": 50}
    if any(training.get(k) != v for k, v in fixed.items()):
        raise ValueError("formal update/batch/optimizer registration changed")
    expected_dimensions = {"token_dim": 4096, "language_dim": 4096, "proprio_dim": 8,
                           "hidden_dim": 256, "num_cameras": 2, "patches_per_camera": 256,
                           "max_instruction_tokens": 128}
    if config.get("scorer_dimensions") != expected_dimensions:
        raise ValueError("formal DIE architecture must remain unchanged")
    if any(config["future"].get(k) != v for k, v in
           {"horizon": 8, "projection_seed": 917, "weight_A": 0., "weight_B": .1,
            "head": "Linear(512+8*7,256),SiLU,Linear(256,512)", "layer_norm_eps": 1e-5}.items()):
        raise ValueError("formal future target/horizon/weights changed")
    if any(config["action_loss"].get(k) != .5 for k in ("teacher_l1_weight", "demonstration_l1_weight")):
        raise ValueError("formal action supervision must remain equally weighted")
    selection = config["selection"]
    if (selection.get("updates") != list(range(0, 5001, 500)) or selection.get("metric") != FORMAL_METRIC
            or selection.get("tie_break") != "earliest_update" or selection.get("future_loss_used") is not False):
        raise ValueError("formal validation/selection protocol changed")
    if (config["gate"].get("alpha_start") != 2. or config["gate"].get("alpha_end") != .1
            or config["gate"].get("schedule") != "cosine across5000updates"):
        raise ValueError("formal gate annealing endpoints changed")
    return FormalTrainingSpec(config["seed"], config["tokens_per_camera"],
                              checkpoint_every=training.get("checkpoint_every_updates", 50))


class RecordProvider(Protocol):
    rows: Mapping[str, dict]
    train_window_ids: Sequence[str]
    validation_window_ids: Sequence[str]

    def get(self, window_id: str) -> dict: ...


def make_formal_batch(record: dict, device, *, include_future=True) -> FutureTrainingBatch:
    move = lambda key: record[key].to(device)
    visual = move("visual")
    if visual.shape[0] != 1:
        raise ValueError("formal micro-batch size is one registered window")
    conditions = ConditionalTokenBatch(visual, move("language"), move("attention_mask").bool(),
        move("normalized_proprio"), torch.arange(2, device=device).repeat_interleave(256)[None],
        torch.arange(256, device=device).repeat(2)[None], torch.ones(1, 512, dtype=torch.bool, device=device))
    return FutureTrainingBatch(conditions, move("raw_tokens"), move("black_tokens"), move("input_ids"),
        move("attention_mask"), move("teacher_actions"), move("demonstration_actions"),
        move("future_target") if include_future else None)


def fixed_window_order(window_ids: Sequence[str], *, seed: int, samples: int) -> list[str]:
    pool = list(window_ids)
    if not pool or len(set(pool)) != len(pool) or any(not isinstance(x, str) or not x for x in pool):
        raise ValueError("training pool must contain unique nonempty window IDs")
    if type(samples) is not int or samples <= 0:
        raise ValueError("sample count must be positive")
    rng, result = random.Random(seed), []
    while len(result) < samples:
        epoch = pool.copy()
        rng.shuffle(epoch)
        result.extend(epoch[:samples - len(result)])
    return result


def validate_provider_partition(provider: RecordProvider) -> None:
    train, validation = list(provider.train_window_ids), list(provider.validation_window_ids)
    if not train or not validation or len(train) != len(set(train)) or len(validation) != len(set(validation)):
        raise ValueError("formal train/validation IDs must be nonempty and unique")
    if set(train) & set(validation) or set(provider.rows) != set(train) | set(validation):
        raise ValueError("formal provider may expose only registered train/validation windows")
    episodes = {}
    tasks = defaultdict(set)
    for split, ids in (("train", train), ("validation", validation)):
        for window_id in ids:
            row = provider.rows[window_id]
            if row["window_id"] != window_id or row["split"] != split:
                raise ValueError("window ID/split does not match provider index")
            episode = row["episode_id"]
            if episode in episodes and episodes[episode] != split:
                raise ValueError("episode leakage between train and validation")
            episodes[episode] = split
            tasks[split].add(str(row["task_id"]))
    if tasks["train"] != tasks["validation"]:
        raise ValueError("every trained task requires registered validation windows")


def aggregate_validation(rows: Sequence[dict]) -> dict:
    if not rows:
        raise ValueError("empty hard validation is not valid for selection")
    by_task = defaultdict(list)
    for row in rows:
        if any(not math.isfinite(float(row[key])) or float(row[key]) < 0 for key in ("teacher_l1", "demonstration_l1")):
            raise ValueError("validation action errors must be finite/nonnegative")
        by_task[str(row["task_id"])].append(row)
    per_task = {task: {"windows": len(values),
                      "teacher_l1": sum(r["teacher_l1"] for r in values) / len(values),
                      "demonstration_l1": sum(r["demonstration_l1"] for r in values) / len(values)}
                for task, values in sorted(by_task.items())}
    return {"metric": FORMAL_METRIC,
            "validation_metric": sum(v["teacher_l1"] for v in per_task.values()) / len(per_task),
            "demonstration_l1": sum(v["demonstration_l1"] for v in per_task.values()) / len(per_task),
            "window_weighted_teacher_l1_diagnostic": sum(r["teacher_l1"] for r in rows) / len(rows),
            "windows": len(rows), "tasks": len(per_task), "per_task": per_task}


def sampling_summary(provider, sample_ids: Sequence[str]) -> dict:
    by_task = defaultdict(list)
    for window_id in sample_ids:
        by_task[str(provider.rows[window_id]["task_id"])].append(window_id)
    result = {}
    for task, ids in sorted(by_task.items()):
        phases = defaultdict(int)
        for window_id in ids:
            phases[provider.rows[window_id].get("phase", "not_available")] += 1
        result[task] = {"samples": len(ids), "unique_windows": len(set(ids)),
                        "unique_episodes": len({provider.rows[i]["episode_id"] for i in ids}),
                        "phase_sample_counts": dict(sorted(phases.items()))}
    return result


@torch.no_grad()
def validate_formal_hard(scorer, provider, policy, *, tokens_per_camera: int) -> dict:
    """Selection is real hard pruning; no future head or soft loss is evaluated."""
    was_training = scorer.training
    scorer.eval()
    device = next(scorer.parameters()).device
    rows = []
    try:
        for window_id in provider.validation_window_ids:
            record = provider.get(window_id)
            batch = make_formal_batch(record, device, include_future=False)
            indices = formal_hard_select(scorer, batch.conditions, tokens_per_camera=tokens_per_camera).source_indices
            prediction = policy.forward_from_full_tokens(batch.conditions.visual, batch.conditions.normalized_proprio,
                input_ids=batch.input_ids, attention_mask=batch.attention_mask, retained_indices=indices).float()
            row = provider.rows[window_id]
            rows.append({"window_id": window_id, "episode_id": row["episode_id"], "task_id": row["task_id"],
                "teacher_l1": float((prediction - batch.teacher_actions).abs().mean()),
                "demonstration_l1": float((prediction - batch.demonstration_actions).abs().mean()),
                "retained_indices": indices[0].cpu().tolist(), "normalized_actions": prediction[0].cpu().tolist(),
                "future_window_diagnostics": record.get("future_window_diagnostics")})
            del batch
    finally:
        scorer.train(was_training)
    diagnostics = [row["future_window_diagnostics"] for row in rows]
    diagnostic_summary = None
    if all(isinstance(row, dict) for row in diagnostics):
        keys = ("raw_proprio_l2_change", "translation_l2_change", "axis_angle_vector_l2_change",
                "gripper_l2_change", "normalized_proprio_l2_change", "visual_summary_mse_change")
        diagnostic_summary = {"fixed_panel": "complete registered validation first/middle/last windows",
            "horizon_control_actions": 8, "selection_uses_these_diagnostics": False,
            "window_means": {key: sum(row[key] for row in diagnostics) / len(diagnostics) for key in keys}}
    return {**aggregate_validation(rows), "observations": rows, "future_alignment_diagnostics": diagnostic_summary}


def choose_earliest(evaluations: Sequence[dict]) -> dict:
    if not evaluations or len({v["update"] for v in evaluations}) != len(evaluations):
        raise ValueError("selection requires unique validated update points")
    if any(not math.isfinite(float(v["validation_metric"])) for v in evaluations):
        raise ValueError("selection metric must be finite")
    return min(evaluations, key=lambda value: (value["validation_metric"], value["update"]))


def _synchronize(device):
    if torch.device(device).type == "cuda":
        torch.cuda.synchronize(device)


def _peak_memory(device):
    if torch.device(device).type != "cuda":
        return {"peak_cuda_memory_allocated_bytes": 0, "peak_cuda_memory_reserved_bytes": 0}
    return {"peak_cuda_memory_allocated_bytes": torch.cuda.max_memory_allocated(device),
            "peak_cuda_memory_reserved_bytes": torch.cuda.max_memory_reserved(device)}


def _read_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    lines = path.read_bytes().splitlines(keepends=True)
    for i, line in enumerate(lines):
        try:
            rows.append(json.loads(line))
        except (ValueError, UnicodeDecodeError):
            # Only a final crash-truncated JSONL line is allowed; preserve it.
            if i != len(lines) - 1 or line.endswith(b"\n"):
                raise ValueError("cost ledger contains non-tail corruption")
    return rows


def _seal_partial_ledger_line(path: Path) -> None:
    """Never concatenate a new event to a crash-truncated ledger tail."""
    if path.exists() and path.stat().st_size:
        with path.open("rb+") as handle:
            handle.seek(-1, os.SEEK_END)
            if handle.read(1) != b"\n":
                raise RuntimeError("cost ledger has an interrupted final line; retain and repair to a separate attempt ledger")


def train_formal_arm(*, config: dict, arm: str, spec: FormalTrainingSpec,
                     provider: RecordProvider, policy, student, frozen_modules: Mapping[str, torch.nn.Module],
                     identity: dict, output: Path, checkpoints: Path,
                     metadata_factory: Callable, receipt_factory: Callable,
                     resume: bool = False, job_id: str = "synthetic-cpu",
                     progress: Callable | None = None, stop_after_updates: int | None = None,
                     max_wall_seconds: float | None = None) -> dict:
    """Train one arm from a shared seeded init, or resume its committed boundary.

    The full sample order is independent of global RNG and cache hits. Resume
    checkpoints include all RNG streams, optimizer and an explicit next-sample
    cursor. Work since the previous commit is replayed deterministically and
    retained in separate attempt ledgers; Slurm remains authoritative for the
    GPU bill, including killed processes and checkpoint/cache overhead.
    """
    if arm not in ("A", "B") or config["seed"] != spec.seed or config["tokens_per_camera"] != spec.tokens_per_camera:
        raise ValueError("arm/config/training spec mismatch")
    if stop_after_updates is not None and (type(stop_after_updates) is not int
            or stop_after_updates not in spec.validation_updates[1:]):
        raise ValueError("engineering stop must be a registered validation boundary")
    if max_wall_seconds is not None and (not math.isfinite(max_wall_seconds) or max_wall_seconds <= 0):
        raise ValueError("engineering wall limit must be finite and positive")
    validate_provider_partition(provider)
    if hasattr(provider, "set_context"):
        provider.set_context(arm=arm, phase="setup")
    output, checkpoints = Path(output), Path(checkpoints)
    output.mkdir(parents=True, exist_ok=True)
    checkpoints.mkdir(parents=True, exist_ok=True)
    device = next(student.visual_projector.parameters()).device
    student.require_frozen()
    initial_frozen_hash = parameter_fingerprint(frozen_modules)
    if identity.get("frozen_model_sha256") != initial_frozen_hash:
        raise ValueError("frozen model bytes differ from accepted identity")
    training_config = {**config, "arm": arm}
    run_identity = {**identity, "training_config_sha256": json_signature(training_config),
                    "pair_config_sha256": json_signature(config), "training_version": FORMAL_TRAINING_VERSION,
                    "training_numerics": dict(FORMAL_NUMERICS),
                    "specification": dict(spec.__dict__)}
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(spec.seed)
        scorer = ConditionalInfluenceEstimator(**config["scorer_dimensions"])
        initial_state = cpu_state(scorer)
    initial_hash = tensor_signature(initial_state)
    scorer = scorer.to(device).train()
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(spec.seed + 10000)
        head = FutureAuxiliaryHead(config["scorer_dimensions"]["token_dim"]) if arm == "B" else None
    if head is not None:
        head = head.to(device).train()
    parameters = list(scorer.parameters()) + ([] if head is None else list(head.parameters()))
    optimizer = torch.optim.AdamW(parameters, lr=spec.learning_rate, weight_decay=spec.weight_decay)
    order = fixed_window_order(provider.train_window_ids, seed=spec.seed, samples=spec.updates * spec.effective_batch)
    order_hash = json_signature(order)
    order_payload = {"version": FORMAL_ORDER_VERSION, "seed": spec.seed,
                     "train_pool_size": len(provider.train_window_ids),
                     "train_pool_sha256": json_signature(list(provider.train_window_ids)),
                     "samples": order, "order_sha256": order_hash,
                     "initial_scorer_sha256": initial_hash}
    order_path = output / "training_order.json"
    if order_path.exists() and json.loads(order_path.read_text(encoding="utf-8")) != order_payload:
        raise ValueError("existing sample order does not match full registered pool")
    if not order_path.exists():
        atomic_json_save(order_path, order_payload)
    resume_path, report_path = checkpoints / "resume.pt", output / "training_report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if report.get("identity") != run_identity or report.get("status") != "completed":
            raise ValueError("existing completion belongs to another experiment")
        if file_sha256(Path(report["best_checkpoint"])) != report["best_checkpoint_sha256"]:
            raise ValueError("completed selected checkpoint changed")
        if (report.get("training_updates_completed") != spec.updates
                or report.get("next_sample_cursor") != spec.updates * spec.effective_batch
                or [row["update"] for row in report.get("evaluations", [])] != spec.validation_updates):
            raise ValueError("completed report lacks the full planned training/validation history")
        payload = load_torch(Path(report["best_checkpoint"]))
        metadata = {key: value for key, value in payload.items() if key != "estimator_state_dict"}
        expected_receipt = receipt_factory(Path(report["best_checkpoint"]), metadata,
            training_config=training_config, pair_config=config, f01_report_sha256=identity["f01_report_sha256"],
            planned_updates=spec.updates, completed_updates=spec.updates, evaluations=report["evaluations"])
        receipt_path = output / "deployment_receipt.json"
        if not receipt_path.is_file() or json.loads(receipt_path.read_text(encoding="utf-8")) != expected_receipt:
            raise ValueError("completed deployment receipt is missing or changed")
        return report
    had_resume = resume_path.exists()
    if had_resume and not resume:
        raise ValueError("existing resumable arm requires explicit --resume")
    completed, evaluations = 0, []
    seed_training_rng(spec.seed + 20000)
    if had_resume:
        saved = load_torch(resume_path)
        if (saved.get("resume_version") != FORMAL_RESUME_VERSION or saved.get("identity") != run_identity
                or saved.get("initial_scorer_sha256") != initial_hash or saved.get("sample_order_sha256") != order_hash):
            raise ValueError("resume provenance/config/initialization/order mismatch")
        ledger_prefix = saved.get("cost_ledger_prefix")
        if ledger_prefix is not None:
            with Path(ledger_prefix["path"]).open("rb") as handle:
                previous = handle.read(ledger_prefix["bytes"])
            if len(previous) != ledger_prefix["bytes"] or hashlib.sha256(previous).hexdigest() != ledger_prefix["sha256"]:
                raise ValueError("committed cost ledger prefix changed")
        completed = saved["completed_update"]
        if type(completed) is not int or not 0 <= completed <= spec.updates or saved.get("next_sample_cursor") != completed * spec.effective_batch:
            raise ValueError("resume update and next sample cursor disagree")
        evaluations = saved["evaluations"]
        expected_validations = [u for u in spec.validation_updates if u <= completed]
        # The initialization checkpoint intentionally precedes validation0.
        if [v["update"] for v in evaluations] not in (expected_validations, [] if completed == 0 else expected_validations):
            raise ValueError("resume validation points are missing or reordered")
        for row in evaluations:
            if file_sha256(Path(row["artifact_path"])) != row["artifact_sha256"] or file_sha256(Path(row["candidate_path"])) != row["candidate_sha256"]:
                raise ValueError("resume validation/candidate evidence changed")
        scorer.load_state_dict(saved["scorer"], strict=True)
        if (head is None) != (saved["head"] is None):
            raise ValueError("resume head does not match arm")
        if head is not None:
            head.load_state_dict(saved["head"], strict=True)
        optimizer.load_state_dict(saved["optimizer"])
        restore_rng(saved["rng"])
    elif any(p.name not in {"resume.pt"} and not p.name.endswith(".partial") for p in checkpoints.iterdir()):
        raise ValueError("new training cannot silently reuse an existing checkpoint directory")
    if stop_after_updates is not None and stop_after_updates < completed:
        raise ValueError("engineering stop precedes the committed resume update")
    attempt_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + uuid.uuid4().hex[:12]
    attempt_dir = output / "attempts" / attempt_id
    attempt_dir.mkdir(parents=True)
    ledger = attempt_dir / "cost_events.jsonl"
    attempt_started = time.perf_counter()
    if torch.device(device).type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
    start_update = completed
    def event(name, **kwargs):
        append_event(ledger, {"event": name, "attempt_id": attempt_id, "job_id": str(job_id),
                             "utc": datetime.now(timezone.utc).isoformat(),
                             "attempt_elapsed_seconds": time.perf_counter() - attempt_started, **kwargs})
    event("attempt_start", resumed=had_resume, completed_update=completed,
          next_sample_cursor=completed * spec.effective_batch, identity=run_identity)
    def commit():
        start = time.perf_counter()
        _synchronize(device)
        ledger_bytes = ledger.read_bytes()
        atomic_torch_save(resume_path, {"resume_version": FORMAL_RESUME_VERSION, "identity": run_identity,
            "initial_scorer_sha256": initial_hash, "sample_order_sha256": order_hash,
            "completed_update": completed, "next_sample_cursor": completed * spec.effective_batch,
            "scorer": cpu_state(scorer), "head": None if head is None else cpu_state(head),
            "optimizer": optimizer.state_dict(), "rng": capture_rng(), "evaluations": evaluations,
            "committed_attempt_id": attempt_id, "ledger_path": str(ledger),
            **_peak_memory(device),
            "cost_ledger_prefix": {"path": str(ledger), "bytes": len(ledger_bytes),
                                   "sha256": hashlib.sha256(ledger_bytes).hexdigest()}})
        event("checkpoint_commit", completed_update=completed, seconds=time.perf_counter() - start,
              resume_sha256=file_sha256(resume_path))
    def evaluate(update):
        start = time.perf_counter()
        if hasattr(provider, "set_context"):
            provider.set_context(arm=arm, phase="validation", update=update)
        event("validation_start", update=update, windows=len(provider.validation_window_ids))
        validation = validate_formal_hard(scorer, provider, policy, tokens_per_camera=spec.tokens_per_camera)
        _synchronize(device)
        elapsed = time.perf_counter() - start
        artifact = attempt_dir / f"validation_{update:05d}.json"
        atomic_json_save(artifact, {**validation, "update": update, "arm": arm, "seconds": elapsed,
                                  "attempt_id": attempt_id, "job_id": str(job_id)})
        metadata = metadata_factory(arm=arm, seed=spec.seed, scorer_dimensions=config["scorer_dimensions"],
            training_config=training_config, pair_config=config,
            window_manifest_sha256=identity["window_manifest_sha256"], model_revision=config["model_revision"],
            stats_key=config["stats_key"], training_source_files=identity["training_source_files"],
            update=update, validation_metric=validation["validation_metric"],
            input_acceptance_sha256=identity["input_acceptance_sha256"], training_complete=False,
            frozen_model_sha256=initial_frozen_hash, data_protocol_sha256=identity["data_protocol_sha256"],
            selection_protocol_sha256=identity["selection_protocol_sha256"])
        candidate = checkpoints / "candidates" / f"{attempt_id}_update{update:05d}.pt"
        atomic_torch_save(candidate, {**metadata, "estimator_state_dict": cpu_state(scorer)})
        evaluations.append({"update": update, "validation_metric": validation["validation_metric"],
                            "artifact_path": str(artifact), "artifact_sha256": file_sha256(artifact),
                            "candidate_path": str(candidate), "candidate_sha256": file_sha256(candidate)})
        event("validation_end", update=update, seconds=elapsed, validation_metric=validation["validation_metric"],
              window_forwards=len(provider.validation_window_ids), artifact_sha256=file_sha256(artifact))
    try:
        if not had_resume:
            commit()
        if not evaluations:
            evaluate(0)
            commit()
        end_update = stop_after_updates or spec.updates
        stop_reason = None
        for update in range(completed + 1, end_update + 1):
            _synchronize(device)
            started = time.perf_counter()
            ids = order[(update - 1) * spec.effective_batch:update * spec.effective_batch]
            if hasattr(provider, "set_context"):
                provider.set_context(arm=arm, phase="training", update=update)
            event("update_start", update=update, window_ids=ids)
            optimizer.zero_grad(set_to_none=True)
            accumulated = defaultdict(float)
            for micro, window_id in enumerate(ids):
                event("sample_start", update=update, micro_batch_index=micro, window_id=window_id)
                batch = make_formal_batch(provider.get(window_id), device, include_future=arm == "B")
                result = formal_auxiliary_loss(scorer, student, batch, alpha=spec.alpha(update), auxiliary_head=head,
                    auxiliary_weight=0. if arm == "A" else spec.future_weight, tokens_per_camera=spec.tokens_per_camera)
                (result.loss / spec.effective_batch).backward()
                for key in ("loss", "action_loss", "teacher_l1", "demonstration_l1", "future_mse"):
                    value = getattr(result, key)
                    if value is not None:
                        accumulated[key] += float(value.detach()) / spec.effective_batch
                event("sample_end", update=update, micro_batch_index=micro, window_id=window_id)
                del result, batch
            grad_norm = float(torch.nn.utils.clip_grad_norm_(parameters, spec.gradient_clip_norm, error_if_nonfinite=True))
            optimizer.step()
            student.require_frozen()
            _synchronize(device)
            completed = update
            event("update_end", update=update, alpha=spec.alpha(update), seconds=time.perf_counter() - started,
                  forward_backward_samples=spec.effective_batch, grad_norm=grad_norm, **accumulated, **_peak_memory(device))
            if progress is not None:
                progress({"arm": arm, "update": update, **accumulated})
            if update in spec.validation_updates:
                evaluate(update)
            if update % spec.checkpoint_every == 0 or update in spec.validation_updates:
                commit()
            if max_wall_seconds is not None and time.perf_counter() - attempt_started >= max_wall_seconds:
                if update % spec.checkpoint_every and update not in spec.validation_updates:
                    commit()
                stop_reason = "engineering_wall_limit_after_complete_update"
                break
        final_frozen_hash = parameter_fingerprint(frozen_modules)
        if final_frozen_hash != initial_frozen_hash:
            raise RuntimeError("frozen VLA parameters/buffers changed")
        if completed < spec.updates:
            event("attempt_end", status="checkpointed", completed_update=completed,
                  seconds=time.perf_counter() - attempt_started, **_peak_memory(device))
            history = [row for path in sorted((output / "attempts").glob("*/cost_events.jsonl")) for row in _read_events(path)]
            progress_report = {"schema": FORMAL_SCHEMA, "status": "checkpointed", "arm": arm,
                "identity": run_identity, "planned_updates": spec.updates, "training_updates_completed": completed,
                "next_sample_cursor": completed * spec.effective_batch, "committed_samples": completed * spec.effective_batch,
                "unique_committed_windows": len(set(order[:completed * spec.effective_batch])),
                "effective_epochs": completed * spec.effective_batch / len(provider.train_window_ids),
                "committed_sampling_by_task": sampling_summary(provider, order[:completed * spec.effective_batch]),
                "train_pool_windows": len(provider.train_window_ids), "evaluations": evaluations,
                "initial_scorer_sha256": initial_hash, "sample_order_sha256": order_hash,
                "vla_parameters_unchanged": True, "frozen_model_sha256": final_frozen_hash,
                "resume_checkpoint": str(resume_path), "resume_sha256": file_sha256(resume_path),
                "stop_reason": stop_reason or "registered_engineering_segment_boundary",
                "final_deployment_receipt_emitted": False, "wall_seconds_this_attempt": time.perf_counter() - attempt_started,
                "peak_cuda_memory_allocated_bytes": max((e.get("peak_cuda_memory_allocated_bytes", 0) for e in history), default=0),
                "peak_cuda_memory_reserved_bytes": max((e.get("peak_cuda_memory_reserved_bytes", 0) for e in history), default=0),
                "attempted_forward_backward_samples_completed": sum(e["event"] == "sample_end" for e in history),
                "job_ids": sorted({e["job_id"] for e in history})}
            atomic_json_save(output / "progress_report.json", progress_report)
            return progress_report
        if [v["update"] for v in evaluations] != spec.validation_updates:
            raise RuntimeError("not all registered validation points completed")
        best = choose_earliest(evaluations)
        payload = load_torch(Path(best["candidate_path"]))
        # Completion is only asserted after all planned training/validation.
        payload["training_complete"] = True
        best_path = checkpoints / "best.pt"
        atomic_torch_save(best_path, payload)
        metadata = {k: v for k, v in payload.items() if k != "estimator_state_dict"}
        receipt = receipt_factory(best_path, metadata, training_config=training_config, pair_config=config,
            f01_report_sha256=identity["f01_report_sha256"], planned_updates=spec.updates,
            completed_updates=completed, evaluations=evaluations)
        atomic_json_save(output / "deployment_receipt.json", receipt)
        event("attempt_end", status="completed", completed_update=completed,
              seconds=time.perf_counter() - attempt_started, **_peak_memory(device))
        all_events = [row for path in sorted((output / "attempts").glob("*/cost_events.jsonl")) for row in _read_events(path)]
        report = {"schema": FORMAL_SCHEMA, "status": "completed", "arm": arm, "identity": run_identity,
            "initial_scorer_sha256": initial_hash, "sample_order_sha256": order_hash,
            "training_updates_completed": completed, "committed_samples": completed * spec.effective_batch,
            "train_pool_windows": len(provider.train_window_ids), "unique_committed_windows": len(set(order)),
            "effective_epochs": len(order) / len(provider.train_window_ids),
            "completed_full_pool_epochs": len(order) // len(provider.train_window_ids),
            "committed_sampling_by_task": sampling_summary(provider, order),
            "validation_pool_windows": len(provider.validation_window_ids), "evaluations": evaluations,
            "best_update": best["update"], "best_validation_metric": best["validation_metric"],
            "best_checkpoint": str(best_path), "best_checkpoint_sha256": file_sha256(best_path),
            "vla_parameters_unchanged": True, "frozen_model_sha256": final_frozen_hash,
            "trainable_parameters": sum(p.numel() for p in parameters),
            "future_head_parameters": 0 if head is None else sum(p.numel() for p in head.parameters()),
            "attempts": sum(e["event"] == "attempt_start" for e in all_events),
            "attempted_forward_backward_samples_completed": sum(e["event"] == "sample_end" for e in all_events),
            "unique_attempted_windows": len({e["window_id"] for e in all_events if e["event"] == "sample_start"}),
            "attempted_completed_sampling_by_task": sampling_summary(provider, [e["window_id"] for e in all_events if e["event"] == "sample_end"]),
            "peak_cuda_memory_allocated_bytes": max((e.get("peak_cuda_memory_allocated_bytes", 0) for e in all_events), default=0),
            "peak_cuda_memory_reserved_bytes": max((e.get("peak_cuda_memory_reserved_bytes", 0) for e in all_events), default=0),
            "completed_update_work_seconds_including_replays": sum(e["seconds"] for e in all_events if e["event"] == "update_end"),
            "completed_validation_work_seconds_including_replays": sum(e["seconds"] for e in all_events if e["event"] == "validation_end"),
            "checkpoint_write_seconds": sum(e["seconds"] for e in all_events if e["event"] == "checkpoint_commit"),
            "wall_seconds_this_attempt": time.perf_counter() - attempt_started,
            "cost_accounting": "phase times overlap nested cache work; use complete Slurm allocation bills, including failed attempts, for total GPU cost",
            "job_ids": sorted({e["job_id"] for e in all_events}), "resumed_from_update": start_update,
            "next_sample_cursor": len(order)}
        atomic_json_save(report_path, report)
        return report
    except BaseException as error:
        # Preserve the last committed state: an interrupted optimizer step is
        # never advertised as resumable, and its actual work remains visible.
        event("attempt_end", status="failed", completed_update_in_memory=completed,
              error_type=type(error).__name__, error=str(error), seconds=time.perf_counter() - attempt_started, **_peak_memory(device))
        raise

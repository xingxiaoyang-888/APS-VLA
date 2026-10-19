"""ACL-style matched adaptation, not the author's native scorer or training.

LapSum and black-image gating follow du-owen/VLA-ACL commit
40b7a7a17f2f5a15acab0564ba1e304bcf6d150d, scorer_train_utils.py.
See LICENSE_ACL_UPSTREAM.txt. Changed: validation, stable Laplace CDF evaluation,
CTI condition scorer, current-set gates, shared original-position packing,
teacher-only loss and registered episode/obs-S cache joins.

This module has no model loader, training CLI, checkpoint writer or GPU job.
The real OFT/raw-black feature producer and formal cost/resume runner remain
integration gates. CPU parity is not a native ACL reproduction result.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import math
import random
import time
from typing import Mapping, Sequence

import torch
from torch import nn

from cti_vla.evaluation.teacher_diagnostics import json_signature, tensor_signature
from cti_vla.labeling.deletion import feature_fingerprint
from cti_vla.models.abstraction.packing import OFTPackedBatch, PACKING_VERSION, mask_from_indices, retained_indices
from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
from cti_vla.selection import ConditionalInfluenceEstimator, staged_topk
from cti_vla.training.offline import OfflineDataset, OfflineObservation, sample_initial_sets

METHOD_ID = "acl-matched-teacher-cti-conditions-staged-adaptation-v1"
UPSTREAM_COMMIT = "40b7a7a17f2f5a15acab0564ba1e304bcf6d150d"
UPSTREAM_UTILS_SHA256 = "67cbf356a5f9fc1df14ada698760d6d66574f539307ba374e8cb9411e96aa282"
SUPPLEMENT_VERSION = "acl-raw-black-bound-to-g2-v1"


def _laplace_cdf(x):
    # Equivalent to upstream's two exponential branches without overflowing
    # the inactive branch for extreme finite logits.
    tail = .5 * torch.exp(-x.abs())
    return torch.where(x <= 0, tail, 1 - tail)


class _LapSum(torch.autograd.Function):
    @staticmethod
    def forward(ctx, scores, k, alpha):
        x = scores.float()
        lo = x.min(-1, keepdim=True).values - 10 * alpha
        hi = x.max(-1, keepdim=True).values + 10 * alpha
        for _ in range(64):
            mid = (lo + hi) * .5
            above = _laplace_cdf((x - mid) / alpha).sum(-1, keepdim=True) > k
            lo, hi = torch.where(above, mid, lo), torch.where(above, hi, mid)
        threshold = (lo + hi) * .5
        ctx.save_for_backward(x, threshold)
        ctx.alpha, ctx.dtype = alpha, scores.dtype
        return _laplace_cdf((x - threshold) / alpha).to(scores.dtype)

    @staticmethod
    def backward(ctx, grad_output):
        x, threshold = ctx.saved_tensors
        pdf = torch.exp(-(x - threshold).abs() / ctx.alpha) / (2 * ctx.alpha)
        gradient = grad_output.float()
        mean = (pdf * gradient).sum(-1, keepdim=True) / pdf.sum(-1, keepdim=True).clamp_min(1e-12)
        return (pdf * (gradient - mean)).to(ctx.dtype), None, None


def soft_top_k(scores: torch.Tensor, k: int, alpha: float) -> torch.Tensor:
    """Author LapSum forward/VJP; k is per camera within the current S."""
    if scores.ndim != 2 or min(scores.shape) <= 0 or not scores.is_floating_point() or not torch.isfinite(scores).all():
        raise ValueError("LapSum requires finite floating [B,N] logits")
    if type(k) is not int or not 0 < k < scores.shape[1] or not math.isfinite(alpha) or alpha <= 0:
        raise ValueError("soft budget must strictly reduce N and alpha must be finite positive")
    result = _LapSum.apply(scores, float(k), float(alpha))
    if not torch.isfinite(result).all() or not torch.allclose(result.float().sum(-1), torch.full((scores.shape[0],), float(k), device=scores.device), atol=max(2e-5, k * 2e-5), rtol=0):
        raise FloatingPointError("LapSum numerical saturation violated the soft budget")
    return result


def cosine_alpha(step: int, end_step: int, *, maximum=2., minimum=.1) -> float:
    if type(step) is not int or step < 0 or type(end_step) is not int or end_step <= 0 or not 0 < minimum <= maximum or not all(math.isfinite(x) for x in (maximum, minimum)):
        raise ValueError("invalid preregistered cosine temperature schedule")
    return minimum + .5 * (maximum - minimum) * (1 + math.cos(math.pi * min(step, end_step) / end_step))


def gate_raw_tokens(raw: torch.Tensor, scores: torch.Tensor, black: torch.Tensor) -> torch.Tensor:
    """Exact author forward; black coefficient is detached intentionally."""
    if raw.ndim != 3 or black.shape != raw.shape or scores.shape != raw.shape[:2]:
        raise ValueError("raw/black features must match [B,N,D] and gate [B,N]")
    if raw.requires_grad or black.requires_grad or not raw.is_floating_point() or not black.is_floating_point():
        raise ValueError("raw and black features must be detached floating tensors")
    if raw.device != black.device or raw.device != scores.device or raw.dtype != black.dtype:
        raise ValueError("raw/black/gates must share device; features must share dtype")
    if not all(bool(torch.isfinite(x).all()) for x in (raw, black, scores)) or bool(((scores < 0) | (scores > 1)).any()):
        raise ValueError("black gating requires finite inputs and scores in [0,1]")
    s = scores.float().unsqueeze(-1)
    # This intentionally is not the full derivative of the forward expression.
    # It reproduces the author's detached stabilizer, not straight-through top-k.
    weight = (1 - s.detach().square()).sqrt()
    return (s * raw.float() + weight * black.float()).to(raw.dtype)


class FrozenDifferentiableOFTPolicy(nn.Module):
    """Separate student path: frozen parameters, gradients to projected tokens.

    Uses existing text helpers, OFTPackedBatch and prefix adapter verbatim. It
    never unwraps or modifies the no_grad CTI teacher methods. The caller must
    keep the source VLA alive and verify the immutable server asset separately.
    """

    def __init__(self, reference: OpenVLAOFTTokenPolicy, visual_projector: nn.Module,
                 *, model_revision: str, input_version: str):
        super().__init__()
        if not isinstance(reference, OpenVLAOFTTokenPolicy) or not model_revision or not input_version:
            raise ValueError("a shared OFT policy and explicit asset/input identity are required")
        self.reference, self.visual_projector = reference, visual_projector
        self.model_revision, self.input_version = model_revision, input_version
        self.requires_grad_(False).eval()

    def train(self, mode=True):
        super().train(False)
        return self

    def require_frozen(self):
        if any(module.training for module in self.modules()) or any(p.requires_grad or p.grad is not None for p in self.parameters()):
            raise RuntimeError("ACL student backbone/projectors/head must remain frozen, eval and gradient-free")

    def forward(self, projected, source_indices, *, input_ids, attention_mask, normalized_proprio):
        self.require_frozen()
        ref = self.reference
        if projected.ndim != 3 or not projected.is_floating_point() or not torch.isfinite(projected).all():
            raise ValueError("student projected tokens must be finite [B,K,D]")
        if source_indices.shape != projected.shape[:2] or source_indices.device != projected.device:
            raise ValueError("student original indices must match physical tokens")
        keep_mask = mask_from_indices(source_indices, ref.num_patches_full)
        ref._validate_prompt(input_ids, attention_mask, projected.shape[0])
        if input_ids.device != projected.device or normalized_proprio.device != projected.device or normalized_proprio.dtype != projected.dtype:
            raise ValueError("student tokens, normalized proprio and prompt have incompatible device/dtype")
        if normalized_proprio.ndim != 2 or normalized_proprio.shape[0] != projected.shape[0] or normalized_proprio.requires_grad or not torch.isfinite(normalized_proprio).all():
            raise ValueError("student proprio must be detached, finite and batched")
        ids, mask = ref._ensure_assistant_empty_token(input_ids, attention_mask)
        ids, mask, action_mask, prompt_counts = ref._build_oft_text_inputs(ids, mask)
        embedding = ref._embedding_layer_ref()
        if embedding is None:
            raise RuntimeError("source VLA embedding module was released")
        with torch.no_grad():
            text = embedding(ids)
            proprio = ref.proprio_projector(normalized_proprio)
        batch = OFTPackedBatch(projected, proprio[:, None], keep_mask, ref.num_patches_full,
                               keep_mask.sum(1).long(), prompt_counts, (ref.action_chunk_size, ref.action_dim))
        hidden = ref.prefix_adapter(text, batch, mask, action_mask).action_hidden_states
        result = ref.action_head.predict_action(hidden)
        if result.shape != (projected.shape[0], ref.action_chunk_size, ref.action_dim) or not torch.isfinite(result).all():
            raise ValueError("student policy must return finite normalized OFT actions")
        if torch.is_grad_enabled() and projected.requires_grad and not result.requires_grad:
            raise RuntimeError("frozen student path blocked input gradients; CTI teacher callback cannot train ACL")
        return result


def supplement_receipt(dataset: OfflineDataset, index: int, raw, black, *, black_preprocessing_signature: str) -> dict:
    """Small provenance record, not a raw-feature producer or disk serializer.

    Real black features must come from a black RGB image through the same frozen
    vision transform/backbone. A tensor of zeros or a camera mean is not valid.
    This semantic property must be verified by the future server producer.
    """
    observation = dataset.observation(index)
    if not black_preprocessing_signature:
        raise ValueError("black-image producer/preprocessing identity is mandatory")
    return {"supplement_version": SUPPLEMENT_VERSION, "source_cache_sha256": dataset.entries[index]["sha256"],
            "build_config_sha256": dataset.index["build_config_sha256"],
            "condition_fingerprint": feature_fingerprint(observation.batch),
            "teacher_action_sha256": tensor_signature({"full_action": observation.labels[0].full_action}),
            "teacher_provenance_sha256": json_signature(asdict(observation.labels[0].provenance)),
            "policy_inputs_sha256": tensor_signature({"input_ids": observation.input_ids, "attention_mask": observation.attention_mask}),
            "raw_sha256": tensor_signature({"raw": raw}), "black_sha256": tensor_signature({"black": black}),
            "black_preprocessing_signature": black_preprocessing_signature}


@dataclass(frozen=True)
class MatchedRecord:
    observation: OfflineObservation
    raw: torch.Tensor
    black: torch.Tensor
    retained_mask: torch.Tensor
    per_camera_target: int
    receipt: dict
    build_config: dict
    receipt_sha256: str

    def to(self, device):
        return replace(self, observation=self.observation.to(device), raw=self.raw.to(device),
                       black=self.black.to(device), retained_mask=self.retained_mask.to(device))

    def validate(self, protocol):
        self.observation.validate(protocol, required_split="train")
        b = self.observation.batch
        if b.visual.shape[0] != 1 or b.visual.shape[1] != 512 or not bool(b.valid.all()):
            raise ValueError("matched Spatial records require one complete 512-token observation")
        if self.raw.shape[:2] != (1, 512) or self.raw.ndim != 3 or self.black.shape != self.raw.shape:
            raise ValueError("matched raw/black features must keep both original camera grids")
        for name in ("raw", "black"):
            value = getattr(self, name)
            if value.requires_grad or value.is_inference() or not value.is_floating_point() or not torch.isfinite(value).all() or value.device != b.visual.device:
                raise ValueError("raw/black features must be ordinary detached finite tensors on the condition device")
        expected_cameras = torch.arange(2, device=b.visual.device).repeat_interleave(256)[None]
        expected_patches = torch.arange(256, device=b.visual.device).repeat(2)[None]
        if not torch.equal(b.camera_ids, expected_cameras) or not torch.equal(b.patch_ids, expected_patches):
            raise ValueError("matched features must preserve original camera-major patch coordinates")
        b.validate_retained(self.retained_mask)
        sets = sample_initial_sets(self.observation.metadata["assignment"])
        current = tuple(retained_indices(self.retained_mask)[0].tolist())
        if current not in [item[0] for item in sets] or len(current) not in (512, 256, 128) or self.per_camera_target != len(current) // 4:
            raise ValueError("matched record must reuse a frozen G2 obs-S and its next half-budget stage")
        if json_signature(self.receipt) != self.receipt_sha256 or self.receipt.get("supplement_version") != SUPPLEMENT_VERSION:
            raise ValueError("raw/black receipt changed or uses an unsupported version")
        expected = {"build_config_sha256": json_signature(self.build_config), "condition_fingerprint": feature_fingerprint(b),
                    "teacher_action_sha256": tensor_signature({"full_action": self.observation.labels[0].full_action}),
                    "teacher_provenance_sha256": json_signature(asdict(self.observation.labels[0].provenance)),
                    "policy_inputs_sha256": tensor_signature({"input_ids": self.observation.input_ids, "attention_mask": self.observation.attention_mask}),
                    "raw_sha256": tensor_signature({"raw": self.raw}), "black_sha256": tensor_signature({"black": self.black})}
        if any(self.receipt.get(key) != value for key, value in expected.items()) or self.observation.metadata.get("build_config_sha256") != expected["build_config_sha256"]:
            raise ValueError("matched supplement is not bound to this feature/prompt/config")
        if self.build_config.get("split") != "train" or self.build_config.get("protocol_signature") != protocol.payload["content_signature"] or self.build_config.get("dataset_version") != protocol.payload["source_signature"]:
            raise ValueError("matched cache source is outside the authoritative train protocol")
        if self.build_config.get("packing_version") != PACKING_VERSION:
            raise ValueError("matched cache packing version changed")


def join_cached_observation(dataset: OfflineDataset, index: int, set_index: int, raw: torch.Tensor,
                            black: torch.Tensor, receipt: Mapping) -> MatchedRecord:
    if dataset.split != "train" or set_index not in (0, 1):
        raise ValueError("matched optimizer records must come from train and one of its two registered sets")
    observation = dataset.observation(index)
    if receipt.get("source_cache_sha256") != dataset.entries[index]["sha256"]:
        raise ValueError("supplement points to a different immutable observation cache")
    # Materialize ordinary frozen tensors even when the future feature producer
    # calls us from inference_mode. Never hide an attached VLA graph by detach.
    if raw.requires_grad or black.requires_grad:
        raise ValueError("raw/black producer must detach its source tensors")
    with torch.inference_mode(False), torch.no_grad():
        raw, black = raw.clone(), black.clone()
    retained = observation.labels[set_index].retained_mask.clone()
    record = MatchedRecord(observation, raw, black, retained, int(retained.sum()) // 4,
                           dict(receipt), dict(dataset.build_config), json_signature(receipt))
    record.validate(dataset.protocol)
    return record


@dataclass
class MatchedCost:
    """In-process counters only; formal durable GPU/resume accounting is pending."""
    student_forwards_started: int = 0
    student_forwards_completed: int = 0
    projector_parity_forwards: int = 0
    backward_started: int = 0
    backward_completed: int = 0
    optimizer_steps: int = 0
    set_records: int = 0
    wall_seconds: float = 0.
    cached_teacher_observations: set[str] = field(default_factory=set)


def matched_loss(scorer: ConditionalInfluenceEstimator, student: FrozenDifferentiableOFTPolicy,
                 record: MatchedRecord, protocol, *, alpha: float, cost: MatchedCost,
                 projection_atol: float = 1e-5):
    """Teacher-only ACL adaptation; never uses CTI influence targets or GT."""
    record.validate(protocol)
    student.require_frozen()
    if not isinstance(scorer, ConditionalInfluenceEstimator):
        raise ValueError("matched adaptation requires the same CTI conditional scorer class")
    if student.model_revision != record.build_config["model_revision"] or student.input_version != record.build_config["input_version"]:
        raise ValueError("student policy and cached full teacher model/input identity differ")
    if not math.isfinite(projection_atol) or projection_atol < 0:
        raise ValueError("projection agreement tolerance must be preregistered finite and nonnegative")
    batch = record.observation.batch
    with torch.no_grad():
        cost.projector_parity_forwards += 1
        projected = student.visual_projector(record.raw)
        if projected.shape != batch.visual.shape or projected.dtype != batch.visual.dtype or not torch.allclose(projected, batch.visual, atol=projection_atol, rtol=0):
            raise ValueError("raw companion does not project to the cached CTI observation features")
    scores = scorer(batch, record.retained_mask)
    source = retained_indices(record.retained_mask)
    gate_parts = []
    for camera in range(2):
        eligible = record.retained_mask & (batch.camera_ids == camera)
        camera_scores = scores.masked_select(eligible).reshape(1, -1)
        gate_parts.append(soft_top_k(camera_scores, record.per_camera_target, alpha))
    gates = torch.cat(gate_parts, 1)
    raw = record.raw[:, source[0]]
    black = record.black[:, source[0]]
    gated = gate_raw_tokens(raw, gates, black)
    projected = student.visual_projector(gated)
    cost.student_forwards_started += 1
    action = student(projected, source, input_ids=record.observation.input_ids,
                     attention_mask=record.observation.attention_mask,
                     normalized_proprio=batch.normalized_proprio.to(projected.dtype))
    if action.device.type == "cuda":
        torch.cuda.synchronize(action.device)
    cost.student_forwards_completed += 1
    target = record.observation.labels[0].full_action
    if target.requires_grad or action.shape != target.shape:
        raise ValueError("full teacher must be detached and share the normalized action shape")
    loss = (action.float() - target.float()).abs().mean()
    if not loss.requires_grad or not torch.isfinite(loss):
        raise RuntimeError("matched student loss has no finite scorer gradient path")
    cost.set_records += 1
    cost.cached_teacher_observations.add(str(record.observation.metadata["sample_id"]))
    return loss, {"method_id": METHOD_ID, "physical_student_visual_tokens": source.shape[1],
                  "soft_target_total": 2 * record.per_camera_target, "alpha": alpha,
                  "gate_sum_by_camera": [float(part.detach().sum()) for part in gate_parts],
                  "source_indices": source.detach(), "teacher_reference": "cached full normalized action",
                  "supervision": "teacher-only mean L1; no CTI influence loss or GT"}


def train_matched_step(scorer, student, optimizer, records: Sequence[MatchedRecord], protocol,
                       *, alpha: float, cost: MatchedCost, effective_batch_records=16):
    """One matching set-record accumulation step; complete epochs are caller-owned."""
    if not records or len(records) > effective_batch_records or effective_batch_records != 16:
        raise ValueError("matched accumulation requires 1..16 records and an effective batch of16")
    wanted = {id(p) for p in scorer.parameters() if p.requires_grad}
    supplied = [p for group in optimizer.param_groups for p in group["params"]]
    if len({id(p) for p in supplied}) != len(supplied) or {id(p) for p in supplied} != wanted:
        raise ValueError("optimizer must contain exactly the trainable conditional scorer parameters")
    # Reject wrong split before any expensive student calls.
    for record in records:
        record.validate(protocol)
    scorer.train()
    student.require_frozen()
    optimizer.zero_grad(set_to_none=True)
    started, losses, traces = time.perf_counter(), [], []
    try:
        for record in records:
            loss, trace = matched_loss(scorer, student, record, protocol, alpha=alpha, cost=cost)
            cost.backward_started += 1
            (loss / len(records)).backward()
            if loss.device.type == "cuda":
                torch.cuda.synchronize(loss.device)
            cost.backward_completed += 1
            losses.append(float(loss.detach()))
            traces.append(trace)
        student.require_frozen()
        torch.nn.utils.clip_grad_norm_(scorer.parameters(), 1., error_if_nonfinite=True)
        optimizer.step()
        cost.optimizer_steps += 1
    finally:
        cost.wall_seconds += time.perf_counter() - started
    return {"method_id": METHOD_ID, "mean_loss": sum(losses) / len(losses), "records": len(records), "traces": traces}


def matched_epoch_order(dataset: OfflineDataset, *, seed: int, epoch: int):
    """Same Python shuffle sequence and two records/observation as CTI G3."""
    if dataset.split != "train" or type(epoch) is not int or epoch < 0:
        raise ValueError("matched epochs use registered train records only")
    rng = random.Random(seed)
    for _ in range(epoch + 1):
        order = list(range(len(dataset)))
        rng.shuffle(order)
    return order


def matched_epoch_batches(dataset: OfflineDataset, *, seed: int, epoch: int):
    """Exactly the CTI record budget; only the final batch may have fewer than16."""
    order = matched_epoch_order(dataset, seed=seed, epoch=epoch)
    return tuple(tuple(order[offset:offset + 16]) for offset in range(0, len(order), 16))


@torch.no_grad()
def select_matched(scorer, batch, *, budget: int):
    """Common hard inference: equal camera budgets, original order, re-score S."""
    if budget not in (256, 128, 64) or batch.visual.shape[1] != 512:
        raise ValueError("matched deployment supports total512→256/128/64 only")
    stages = ((128, 128), (64, 64), (32, 32))[:{256: 1, 128: 2, 64: 3}[budget]]
    return staged_topk(scorer, batch, stages)

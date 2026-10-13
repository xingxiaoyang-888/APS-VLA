"""Engineering integration of the new method with an already loaded policy.

One observation and one temporary optimizer step cannot establish method
quality. No scorer checkpoint is written and no closed-loop claim is made.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import time
from typing import Any

import torch

from cti_vla.labeling import DeletionTeacher, LabelProvenance, load_deletion_labels, save_deletion_labels
from cti_vla.models.abstraction.packing import PACKING_VERSION, retained_indices
from cti_vla.selection import ConditionalInfluenceEstimator, ConditionalTokenBatch, staged_topk
from cti_vla.training import ConditionalTrainer, TrainingLabelScale


def _timed(function, device: torch.device):
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    started = time.perf_counter()
    output = function()
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    return output, time.perf_counter() - started


def run_conditional_smoke(policy, projected: torch.Tensor, inputs: dict[str, Any], provenance: LabelProvenance,
                          *, cache_directory: Path | None = None, hidden_dim: int = 64, seed: int = 0) -> dict:
    """Two 256/128-token sets x two candidates = seven teacher calls total.

    Call outside inference_mode: scorer training needs ordinary autograd. Frozen
    features computed in inference_mode are safely materialized by the batch
    contract. Inputs/normalization must be identical to the dense parity run.
    """
    if torch.is_inference_mode_enabled():
        raise ValueError("call conditional smoke outside torch.inference_mode()")
    if projected.ndim != 3 or projected.shape[1] != 512:
        raise ValueError("conditional integration smoke requires a 512-token two-camera policy")
    if provenance.split != "train" or provenance.packing_version != PACKING_VERSION:
        raise ValueError("smoke provenance must identify its ephemeral train step and shared packing version")
    b, n, token_dim = projected.shape
    if len(provenance.sample_ids) != b:
        raise ValueError("provenance must cover the observation batch")
    device = projected.device
    source_vla = policy._vla_ref()
    if source_vla is None:
        raise RuntimeError("source VLA was released")
    with torch.no_grad():
        language = source_vla.get_input_embeddings()(inputs["input_ids"]).detach()
    data = ConditionalTokenBatch(
        projected.detach(), language, inputs["attention_mask"].bool(), inputs["normalized_proprio"].detach(),
        torch.arange(2, device=device).repeat_interleave(256).expand(b, -1),
        torch.arange(256, device=device).repeat(2).expand(b, -1), torch.ones(b, n, device=device, dtype=torch.bool),
    )
    calls = 0

    def forward_retained(batch, indices):
        nonlocal calls
        calls += 1
        return policy.forward_from_full_tokens(
            batch.visual, batch.normalized_proprio.to(batch.visual.dtype),
            input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"], retained_indices=indices,
        )

    teacher = DeletionTeacher(policy, forward_retained)
    generator = torch.Generator(device="cpu").manual_seed(seed)
    sets = []
    uniform_indices = torch.cat((torch.arange(0, 256, 2), torch.arange(256, 512, 2))).to(device).expand(b, -1)
    sets.append(torch.zeros_like(data.valid).scatter_(1, uniform_indices, True))
    random_mask = torch.zeros_like(data.valid)
    for row in range(b):
        indices = torch.cat((torch.randperm(256, generator=generator)[:64], torch.randperm(256, generator=generator)[:64] + 256)).to(device)
        random_mask[row, indices] = True
    sets.append(random_mask)

    def label_all():
        reference = teacher.reference(data, provenance)
        records = []
        for retained in sets:
            ordered = retained_indices(retained)
            # One candidate per camera, from each concrete retained set.
            candidates = ordered[:, [0, ordered.shape[1] // 2]]
            records.append(teacher.label(data, retained, candidates, provenance, full_reference=reference))
        return records

    records, labeling_seconds = _timed(label_all, device)
    expected_calls = 1 + sum(record.teacher_calls for record in records)
    if calls != expected_calls or expected_calls != 7:
        raise RuntimeError("teacher query count differs from reference + two (base + 2 deletions)")
    if cache_directory is None:
        cache_directory = Path(__file__).resolve().parents[3] / "results" / "smoke"
    cache_directory.mkdir(parents=True, exist_ok=True)

    def cache_roundtrip():
        with tempfile.TemporaryDirectory(prefix="real-conditional-", dir=cache_directory) as directory:
            restored = []
            for i, record in enumerate(records):
                path = save_deletion_labels(Path(directory) / f"labels-{i}.pt", record)
                copied = load_deletion_labels(path, batch=data, retained=record.retained_mask, provenance=provenance)
                torch.testing.assert_close(copied.influence, record.influence)
                restored.append(copied)
        return restored

    restored, cache_seconds = _timed(cache_roundtrip, device)
    torch.manual_seed(seed)
    estimator = ConditionalInfluenceEstimator(
        token_dim, language.shape[-1], data.normalized_proprio.shape[-1], hidden_dim=hidden_dim,
        max_instruction_tokens=max(128, language.shape[1]),
    ).to(device=device, dtype=torch.float32)
    scale = TrainingLabelScale.fit(restored)
    trainer = ConditionalTrainer(estimator, torch.optim.Adam(estimator.parameters(), lr=1e-3), scale)
    original = estimator.output[-1].weight.detach().clone()
    metrics, training_seconds = _timed(lambda: trainer.train_step(data, restored[0], provenance=provenance), device)
    if torch.equal(original, estimator.output[-1].weight):
        raise RuntimeError("temporary scorer did not update")
    if any(p.grad is not None for p in policy.parameters()) or data.visual.requires_grad:
        raise RuntimeError("policy/feature gradient isolation failed")
    estimator.eval()
    selection, selection_seconds = _timed(lambda: staged_topk(estimator, data, ((128, 128), (64, 64), (32, 32))), device)
    if calls != expected_calls:
        raise RuntimeError("scorer training/selection unexpectedly called the policy")
    action, final_policy_seconds = _timed(lambda: forward_retained(data, selection.source_indices), device)
    if calls != expected_calls + 1 or action.shape != (b, 8, 7) or not torch.isfinite(action).all():
        raise RuntimeError("final selected-policy forward failed")
    return {
        "status": "passed", "kind": "conditional_single_observation_engineering_smoke", "seed": seed,
        "batch_size": b, "scorer_hidden_dim": hidden_dim, "scorer_parameter_count": sum(p.numel() for p in estimator.parameters()),
        "packing_version": PACKING_VERSION, "label_sets": ["uniform-256", "random-128"],
        "candidate_count_per_set_per_observation": 2,
        "teacher_batched_calls": expected_calls, "teacher_calls_per_observation": expected_calls,
        "teacher_sample_forwards": b + sum(record.teacher_sample_forwards for record in records),
        "final_deployment_policy_calls": 1, "final_deployment_sample_forwards": b,
        "cache_roundtrip": True, "scorer_updated": True, "policy_gradients": False,
        "scale_fit_labels": scale.label_count, "scale_fit_retained_set_rows": len(records) * b,
        "scale_fit_unique_observations": len(set(provenance.sample_ids)), "scale_fit_unique_episodes": len(set(provenance.episode_ids)),
        "optimizer_steps": 1, "optimizer_labels": metrics["labels"], "scale_value": scale.value,
        "signed_labels": [record.influence.detach().cpu().tolist() for record in records],
        "base_errors": [record.base_error.detach().cpu().tolist() for record in records],
        "training": metrics, "selected_indices": selection.source_indices.detach().cpu().tolist(),
        "selected_action_shape": list(action.shape),
        "engineering_seconds": {"labeling": labeling_seconds, "cache_roundtrip": cache_seconds,
                                "temporary_train_step": training_seconds, "selection": selection_seconds, "final_policy": final_policy_seconds},
        "limitations": "Temporary random scorer, four labels per observation, one optimizer step; no saved trained model, method-quality result, rollout, success rate or speedup. Timings include checks and are not observation-to-action benchmarks.",
    }

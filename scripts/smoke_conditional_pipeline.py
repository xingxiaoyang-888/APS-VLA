"""Synthetic CPU integration smoke; this is NOT a pretrained-policy result.

Runs the shared OFT packing adapter, frozen mock policy, actual deletion labels,
disk-cache validation, scorer training, and staged per-camera selection at B=2.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

import torch
from torch import nn

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cti_vla.labeling import DeletionTeacher, LabelProvenance, load_deletion_labels, save_deletion_labels
from cti_vla.models.abstraction.packing import PACKING_VERSION
from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
from cti_vla.selection import ConditionalInfluenceEstimator, ConditionalTokenBatch, staged_topk
from cti_vla.training import ConditionalTrainer, TrainingLabelScale


class SyntheticBackbone(nn.Module):
    def __init__(self, hidden: int):
        super().__init__()
        self.embed_tokens = nn.Embedding(32, hidden)
        self.calls: list[dict] = []

    def forward(self, **kwargs):
        features, positions = kwargs["inputs_embeds"], kwargs["position_ids"]
        assert positions.shape == features.shape[:2] == kwargs["attention_mask"].shape
        assert not torch.is_grad_enabled() and not self.training
        self.calls.append({"sequence_length": features.shape[1], "position_ids": positions.tolist()})
        # Causal accumulation makes earlier visual deletion change action slots.
        hidden = features.cumsum(1) + positions[..., None].to(features.dtype) * 0.01
        return SimpleNamespace(last_hidden_state=hidden)


class SyntheticVLA(nn.Module):
    def __init__(self, backbone: SyntheticBackbone):
        super().__init__()
        self.backbone = backbone

    def get_input_embeddings(self):
        return self.backbone.embed_tokens


class SyntheticActionHead(nn.Module):
    def predict_action(self, hidden):
        return hidden.reshape(hidden.shape[0], 2, 2, -1).mean(-1)


def run_smoke(cache_dir: Path) -> dict:
    torch.manual_seed(19)
    hidden, samples, tokens = 12, 2, 6
    backbone = SyntheticBackbone(hidden)
    vla = SyntheticVLA(backbone)
    policy = OpenVLAOFTTokenPolicy(vla, SyntheticActionHead(), nn.Linear(3, hidden),
                                  num_patches_full=tokens, action_chunk_size=2, action_dim=2,
                                  assistant_empty_token_id=None, language_backbone=backbone)
    input_ids = torch.tensor([[3, 4, 5, 6], [3, 7, 8, 9]])
    attention = torch.ones_like(input_ids)
    visual_source = torch.randn(samples, tokens, hidden, requires_grad=True)
    data = ConditionalTokenBatch(
        visual_source.detach(), vla.get_input_embeddings()(input_ids).detach(), attention.bool(),
        torch.randn(samples, 3), torch.tensor([[0, 0, 0, 1, 1, 1]]).expand(samples, -1),
        torch.tensor([[0, 1, 2, 0, 1, 2]]).expand(samples, -1), torch.ones(samples, tokens, dtype=torch.bool),
    )
    provenance = LabelProvenance(
        ("synthetic-state-a", "synthetic-state-b"), ("synthetic-episode-a", "synthetic-episode-b"),
        "train", "synthetic-random-frozen-v1", "synthetic-v1", "synthetic-identity-v1", PACKING_VERSION,
        "synthetic-proprio-v1", "synthetic-normalized-2x2-v1",
    )

    def forward_retained(batch, indices):
        return policy.forward_from_full_tokens(
            batch.visual, batch.normalized_proprio, input_ids=input_ids, attention_mask=attention, retained_indices=indices,
        )

    teacher = DeletionTeacher(policy, forward_retained, action_shape=(2, 2))
    reference = teacher.reference(data, provenance)
    reduced = torch.tensor([[True, False, True, True, False, True], [False, True, True, True, True, False]])
    candidates = torch.tensor([[0, 3], [1, 3]])
    dense_labels = teacher.label(data, data.valid, candidates, provenance, full_reference=reference)
    labels = teacher.label(data, reduced, candidates, provenance, full_reference=reference)
    expected_calls = 1 + dense_labels.teacher_calls + labels.teacher_calls
    assert len(backbone.calls) == expected_calls == 6
    path = save_deletion_labels(cache_dir / "synthetic-labels.pt", labels, overwrite=True)
    restored = load_deletion_labels(path, batch=data, retained=reduced, provenance=provenance)
    torch.testing.assert_close(restored.influence, labels.influence)

    estimator = ConditionalInfluenceEstimator(hidden, hidden, 3, hidden_dim=16, patches_per_camera=3, max_instruction_tokens=8)
    scale = TrainingLabelScale.fit([dense_labels, restored])
    trainer = ConditionalTrainer(estimator, torch.optim.Adam(estimator.parameters(), lr=1e-3), scale)
    before = estimator.output[-1].weight.detach().clone()
    metrics = trainer.train_step(data, restored, provenance=provenance)
    assert not torch.equal(before, estimator.output[-1].weight)
    assert visual_source.grad is None and all(p.grad is None for p in policy.parameters())
    assert len(backbone.calls) == expected_calls
    estimator.eval()
    selection = staged_topk(estimator, data, ((2, 2), (1, 1)))
    assert len(backbone.calls) == expected_calls  # Selection never forwards VLA.
    actions = forward_retained(data, selection.source_indices)
    assert actions.shape == (2, 2, 2) and len(backbone.calls) == expected_calls + 1
    return {
        "kind": "synthetic_integration_smoke", "pretrained_vla": False, "closed_loop": False,
        "seed": 19, "device": "cpu", "torch_version": torch.__version__, "packing_version": PACKING_VERSION,
        "batch_size": samples, "visual_tokens": tokens, "teacher_calls": expected_calls,
        "teacher_calls_per_observation": expected_calls,
        "teacher_sample_forwards": samples + dense_labels.teacher_sample_forwards + labels.teacher_sample_forwards,
        "deployment_policy_calls": 1,
        "scale_fit_labels": scale.label_count, "scale_fit_retained_set_rows": 2 * samples,
        "scale_fit_unique_observations": len(set(provenance.sample_ids)),
        "scale_fit_unique_episodes": len(scale.training_episodes), "train_step_labels": metrics["labels"],
        "cache_roundtrip": True, "scorer_updated": True, "policy_or_input_gradients": False,
        "signed_label_min": float(labels.influence.min()), "signed_label_max": float(labels.influence.max()),
        "label_scale": scale.value, "training": metrics, "selected_original_indices": selection.source_indices.tolist(),
        "physical_sequence_lengths": [call["sequence_length"] for call in backbone.calls],
        "note": "Only synthetic interface/gradient/cache checks; no LIBERO success rate or acceleration claim.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON report inside the CTI-VLA project")
    args = parser.parse_args()
    # Temporary artifacts stay within the project and are removed after checks.
    work = PROJECT_ROOT / "results" / "smoke"
    work.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="conditional-", dir=work) as cache_dir:
        result = run_smoke(Path(cache_dir))
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        output = args.output.resolve()
        if not output.is_relative_to(PROJECT_ROOT):
            raise ValueError("smoke report must stay inside the CTI-VLA project")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()

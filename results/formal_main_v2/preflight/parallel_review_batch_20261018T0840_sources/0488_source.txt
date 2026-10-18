"""Independent formal F00/F01 engineering gates for all four suites/budgets."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
import time

import torch

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation import libero_runtime
from cti_vla.evaluation.formal_runtime import FORMAL_SCHEMA, FORMAL_SUITES, FORMAL_BUDGETS, require_sha
from cti_vla.evaluation.teacher_diagnostics import json_signature
from cti_vla.models.abstraction.packing import PACKING_VERSION

INPUT_TASK_IDS = (0, 3, 5)
INPUT_FLAGS = ("pixels_equal", "prompt_equal", "raw_camera_bridge_equal", "native_physical_equal",
    "action_postprocess_equal", "gripper_equal", "demonstration_normalization_valid", "passed")
OPERATOR_FLAGS = ("time_alignment", "no_future_leakage", "action_gradient_to_die", "future_gradient_to_die",
    "future_gradient_to_head", "vla_parameters_unchanged", "vla_gradients_absent", "die_optimizer_updated",
    "hard_budget_packing", "soft_gate_mass", "dense_differentiable_parity", "deployment_single_pass")
OPERATOR_PROBES = ("dense_differentiable", "action_gradient", "future_gradient", "optimizer_step", "hard_deploy", "hard_student", "raw_observation_deploy")


def select_formal_acceptance_windows(manifest, protocol):
    payload = getattr(protocol, "payload", protocol)
    if manifest.get("suite") not in FORMAL_SUITES or payload.get("suite") != manifest["suite"]:
        raise ValueError("formal acceptance manifest/protocol suite mismatch")
    rows = []
    for task_id in INPUT_TASK_IDS:
        candidates = [r for r in manifest["windows"] if r["split"] == "train" and r["task_id"] == task_id]
        if not candidates:
            raise ValueError(f"formal acceptance has no legal train window for fixed task{task_id}")
        rows.append(min(candidates, key=lambda r: (r["episode_id"], r["start_step"], r["window_id"])))
    if len({r["window_id"] for r in rows}) != 3:
        raise ValueError("formal acceptance must use three distinct fixed train windows")
    return rows


def module_parameter_sha256(components):
    from cti_vla.training.formal_future import parameter_fingerprint
    return parameter_fingerprint({name: getattr(components, name) for name in ("vla", "action_head", "proprio_projector")})


def acceptance_source_hashes(source_root):
    from cti_vla.training.formal_future import formal_source_hashes
    return formal_source_hashes(source_root)


def require_formal_input_acceptance(report, *, config, window_manifest_sha256, data_protocol_sha256,
        asset_manifest_sha256, source_files, selected_windows):
    expected = {"schema": FORMAL_SCHEMA, "kind": "input_acceptance", "status": "passed",
        "execution": "real_frozen_openvla_slurm", "suite": config["suite"], "stats_key": config["stats_key"],
        "model_revision": config["model_revision"], "window_manifest_sha256": window_manifest_sha256,
        "data_protocol_sha256": data_protocol_sha256, "asset_manifest_sha256": asset_manifest_sha256,
        "source_files": source_files, "input_version": libero_runtime.INPUTS_VERSION,
        "action_version": libero_runtime.ACTION_VERSION, "packing_version": PACKING_VERSION,
        "checkpoint_unchanged": True, "test_opened": False, "policy_sample_forwards": 6,
        "vision_forwards": 6, "policy_attempts": 6}
    if config["suite"] not in FORMAL_SUITES or any(report.get(k) != v for k, v in expected.items()):
        raise ValueError("formal official-input gate identity/finalization mismatch")
    require_sha(report.get("frozen_model_sha256"), "frozen_model_sha256")
    observations = report.get("observations", [])
    if len(observations) != 3 or [r.get("window") for r in observations] != selected_windows:
        raise ValueError("formal official parity changed its fixed train observations")
    for row in observations:
        if any(row.get(key) is not True for key in INPUT_FLAGS):
            raise ValueError("formal official-input parity did not pass")
        for key, bound in (("proprio_max_abs_error", 1e-6), ("dense_max_abs_error", .002),
                ("demonstration_inverse_max_abs_error", 1e-5)):
            x = row.get(key)
            if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or not 0 <= x <= bound:
                raise ValueError("formal official-input numeric parity failed")


def require_formal_acceptance(report, *, config, window_manifest_sha256, input_acceptance_sha256,
        source_files, selected_windows=None):
    """Reuse only exact seed17 engineering evidence, changing seed/run_id only."""
    accepted = report.get("accepted_pair_config", {})
    strip_seed = lambda value: {k: v for k, v in value.items() if k not in ("seed", "run_id")}
    if (accepted.get("seed") != 17 or config.get("seed") not in (17, 23, 41)
            or strip_seed(accepted) != strip_seed(config)):
        raise ValueError("formal acceptance permits seed/run_id differences only")
    total = config.get("tokens_per_camera", 0) * 2
    expected = {"schema": FORMAL_SCHEMA, "kind": "operator_acceptance", "status": "passed",
        "execution": "real_frozen_openvla_slurm", "suite": config["suite"], "stats_key": config["stats_key"],
        "model_revision": config["model_revision"], "visual_tokens": total,
        "per_camera_budgets": [total // 2] * 2, "accepted_pair_id": json_signature(accepted),
        "window_manifest_sha256": window_manifest_sha256, "input_acceptance_sha256": input_acceptance_sha256,
        "source_files": source_files, "input_version": libero_runtime.INPUTS_VERSION,
        "packing_version": PACKING_VERSION, "checkpoint_unchanged": True, "test_opened": False}
    if total not in FORMAL_BUDGETS or any(report.get(k) != v for k, v in expected.items()):
        raise ValueError("formal suite/budget operator gate identity/finalization mismatch")
    require_sha(report.get("frozen_model_sha256"), "frozen_model_sha256")
    rows = report.get("observations", [])
    if (len(rows) != 3 or [r.get("task_id") for r in rows] != list(INPUT_TASK_IDS)
            or len({r.get("window_id") for r in rows}) != 3):
        raise ValueError("formal operator gate must cover the same fixed three train windows")
    if selected_windows is not None and [r["window_id"] for r in rows] != [r["window_id"] for r in selected_windows]:
        raise ValueError("formal operator gate changed registered acceptance window IDs")
    for row in rows:
        if any(row.get("checks", {}).get(key) is not True for key in OPERATOR_FLAGS):
            raise ValueError("formal operator engineering check failed")
        for key in ("action_gradient_norm", "future_gradient_norm", "future_head_gradient_norm"):
            x = row.get(key)
            if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x <= 0:
                raise ValueError("formal gate requires finite positive action/future gradients")
        for key in ("dense_max_abs", "hard_max_abs", "deployment_max_abs"):
            x = row.get(key)
            if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or not 0 <= x <= .002:
                raise ValueError("formal dense/hard/deployment parity failed")
        if any(not math.isfinite(float(x)) or abs(x - total // 2) > .01 for x in row.get("soft_gate_mass_per_camera", [])) or len(row.get("soft_gate_mass_per_camera", [])) != 2:
            raise ValueError("formal soft gate differs from trained per-view budget")


def verify_formal_operator_journal(path, report):
    """Validate the immutable report prefix even after later budgets append."""
    count = report.get("operator_journal_prefix_bytes")
    if type(count) is not int or count <= 0:
        raise ValueError("formal operator report must bind a durable journal prefix")
    with Path(path).open("rb") as stream:
        prefix = stream.read(count)
    if len(prefix) != count or hashlib.sha256(prefix).hexdigest() != report.get("operator_journal_prefix_sha256"):
        raise ValueError("formal operator journal prefix changed")
    events = [json.loads(line) for line in prefix.splitlines()]
    active, done = None, []
    keys = ("call_id", "window_id", "kind", "job_id", "visual_tokens")
    for row in events:
        if row.get("event") == "start" and active is None and row.get("call_id") == len(done):
            active = row
        elif row.get("event") == "complete" and active is not None and all(row.get(k) == active.get(k) for k in keys):
            elapsed = row.get("seconds")
            if isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed < 0:
                raise ValueError("formal operator journal has invalid measured cost")
            done.append(active)
            active = None
        else:
            raise ValueError("formal successful acceptance cannot hide failed or interrupted probes")
    selected = [row for row in done if row["visual_tokens"] == report["visual_tokens"]]
    expected = [(row["window_id"], kind) for row in report["observations"] for kind in OPERATOR_PROBES]
    if (active is not None or len(done) != report.get("operator_probes_completed")
            or [(row["window_id"], row["kind"]) for row in selected] != expected
            or any(row["job_id"] != report.get("job_id") for row in done)):
        raise ValueError("formal operator journal coverage/order/job identity differs")


def _batch(record, device):
    from cti_vla.selection import ConditionalTokenBatch
    from cti_vla.training.future_auxiliary import FutureTrainingBatch
    move = lambda key: record[key].to(device)
    conditions = ConditionalTokenBatch(move("visual"), move("language"), move("attention_mask").bool(),
        move("normalized_proprio"), torch.arange(2, device=device).repeat_interleave(256)[None],
        torch.arange(256, device=device).repeat(2)[None], torch.ones(1, 512, dtype=torch.bool, device=device))
    return FutureTrainingBatch(conditions=conditions, raw_tokens=move("raw_tokens"), black_tokens=move("black_tokens"),
        input_ids=move("input_ids"), attention_mask=move("attention_mask"), teacher_actions=move("teacher_actions"),
        demonstration_actions=move("demonstration_actions"), future_target=move("future_target"))


def raw_observation_bridge(episode, step):
    """Inverse RLDS orientation/proprio bridge; explicitly not a simulator capture."""
    from io import BytesIO
    from PIL import Image
    import numpy as np
    arrays = []
    for encoded in (episode.images[step], episode.wrist_images[step]):
        with Image.open(BytesIO(encoded)) as image:
            arrays.append(np.ascontiguousarray(np.asarray(image.convert("RGB"))[::-1, ::-1]))
    proprio = np.asarray(episode.proprio[step], dtype=np.float64)
    axis = proprio[3:6]
    angle = float(np.linalg.norm(axis))
    quat = np.r_[axis / angle * np.sin(angle / 2), np.cos(angle / 2)] if angle > 0 else np.array([0., 0., 0., 1.])
    result = dict(agentview_image=arrays[0], robot0_eye_in_hand_image=arrays[1], robot0_eef_pos=proprio[:3],
        robot0_eef_quat=quat, robot0_gripper_qpos=proprio[6:8])
    if not np.allclose(libero_runtime.raw_proprio_from_observation(result), proprio, atol=1e-6, rtol=0):
        raise ValueError("RLDS inverse raw-proprio bridge is numerically invalid")
    return result


def run_formal_operator_window(*, config, window, record, components, processor, policy, student,
        episode, query):
    """Execute real gradient/hard/deployment probes; query journals every probe."""
    import numpy as np
    from cti_vla.selection import ConditionalInfluenceEstimator
    from cti_vla.training.future_auxiliary import FutureAuxiliaryHead
    from cti_vla.training.formal_future import formal_auxiliary_loss, formal_hard_select
    from cti_vla.evaluation.formal_runtime import FormalRolloutPolicy, LoadedFormalSelector
    device = next(components.vla.parameters()).device
    budget = config["tokens_per_camera"]
    torch.manual_seed(17)
    scorer = ConditionalInfluenceEstimator(**config["scorer_dimensions"]).to(device)
    head = FutureAuxiliaryHead(config["scorer_dimensions"]["token_dim"]).to(device)
    batch = _batch(record, device)
    initial = {k: v.detach().clone() for k, v in scorer.state_dict().items()}
    def norm(module):
        return sum(float(p.grad.float().square().sum()) for p in module.parameters() if p.grad is not None) ** .5
    with torch.no_grad():
        dense = query("dense_differentiable", lambda: student(batch.conditions.visual, torch.arange(512, device=device)[None],
            input_ids=batch.input_ids, attention_mask=batch.attention_mask, normalized_proprio=batch.conditions.normalized_proprio))
    parity = float((dense.float() - batch.teacher_actions).abs().max())
    if parity > .002:
        raise RuntimeError("formal differentiable dense differs from accepted teacher")
    a = query("action_gradient", lambda: formal_auxiliary_loss(scorer, student, batch, alpha=2., tokens_per_camera=budget))
    a.loss.backward()
    action_grad, original_scores = norm(scorer), a.scores.detach().clone()
    scorer.zero_grad(set_to_none=True)
    del a
    b = query("future_gradient", lambda: formal_auxiliary_loss(scorer, student, batch, alpha=2., auxiliary_head=head,
        auxiliary_weight=.1, tokens_per_camera=budget))
    if not torch.equal(original_scores, b.scores.detach()):
        raise RuntimeError("formal A/B did not share initial DIE scores")
    b.future_mse.backward()
    future_grad, head_grad = norm(scorer), norm(head)
    if not all(math.isfinite(x) and x > 0 for x in (action_grad, future_grad, head_grad)):
        raise RuntimeError(f"formal missing/nonfinite gradient: action={action_grad}, future={future_grad}, head={head_grad}")
    scorer.zero_grad(set_to_none=True)
    head.zero_grad(set_to_none=True)
    del b
    optimizer = torch.optim.AdamW([*scorer.parameters(), *head.parameters()], lr=1e-4, weight_decay=.01)
    output = query("optimizer_step", lambda: formal_auxiliary_loss(scorer, student, batch, alpha=2., auxiliary_head=head,
        auxiliary_weight=.1, tokens_per_camera=budget))
    masses = output.gates.detach().reshape(-1, 2, 256).sum(-1)
    if not torch.allclose(masses, torch.full_like(masses, float(budget)), atol=.01, rtol=0):
        raise RuntimeError("formal soft gate mass changed trained budget")
    output.loss.backward()
    torch.nn.utils.clip_grad_norm_([*scorer.parameters(), *head.parameters()], 1., error_if_nonfinite=True)
    optimizer.step()
    student.require_frozen()
    if all(torch.equal(initial[k], v) for k, v in scorer.state_dict().items()):
        raise RuntimeError("formal DIE optimizer step changed no parameter")
    scorer.eval()
    with torch.no_grad():
        selection = formal_hard_select(scorer, batch.conditions, tokens_per_camera=budget)
        indices = selection.source_indices
        if (indices.shape != (1, 2 * budget) or len(indices.unique()) != 2 * budget
                or int((indices < 256).sum()) != budget or not bool((indices[:, 1:] > indices[:, :-1]).all())):
            raise RuntimeError("formal hard indices/budget/original source ordering failed")
        hard = query("hard_deploy", lambda: policy.forward_from_full_tokens(batch.conditions.visual,
            batch.conditions.normalized_proprio, input_ids=batch.input_ids, attention_mask=batch.attention_mask, retained_indices=indices))
        packed = batch.conditions.visual.gather(1, indices[..., None].expand(-1, -1, batch.conditions.visual.shape[-1]))
        paired = query("hard_student", lambda: student(packed, indices, input_ids=batch.input_ids,
            attention_mask=batch.attention_mask, normalized_proprio=batch.conditions.normalized_proprio))
        hard_error = float((hard.float() - paired.float()).abs().max())
        mutated = copy.copy(batch)
        object.__setattr__(mutated, "future_target", batch.future_target.flip(-1))
        object.__setattr__(mutated, "demonstration_actions", -batch.demonstration_actions)
        if not torch.equal(scorer(batch.conditions, batch.conditions.valid), scorer(mutated.conditions, mutated.conditions.valid)):
            raise RuntimeError("formal training-only information leaked to DIE")
        scorer.requires_grad_(False)
        provenance = dict(schema=FORMAL_SCHEMA, suite=config["suite"], arm="B", visual_tokens=budget * 2,
            stats_key=config["stats_key"], future_head_deployed=False, input_version=libero_runtime.INPUTS_VERSION,
            packing_version=PACKING_VERSION, selector_checkpoint_sha256=json_signature({"engineering_probe": True}),
            pair_id=json_signature(config), seed=17)
        deployment = FormalRolloutPolicy(components, processor, suite=config["suite"], method="B", total_tokens=2 * budget,
            selector=LoadedFormalSelector(scorer, provenance))
        counts = dict(vision=0, scorer=0, vla=0, head=0)
        # Hooks measure the real single-pass implementation; metadata alone is not proof.
        def hook(key):
            def count(*_):
                counts[key] += 1
            return count
        hooks = [scorer.register_forward_hook(hook("scorer")),
            deployment.token_policy.prefix_adapter.register_forward_hook(hook("vla")), head.register_forward_hook(hook("head"))]
        original_vision = components.vla._process_vision_features
        def vision(*args, **kwargs):
            counts["vision"] += 1
            return original_vision(*args, **kwargs)
        components.vla._process_vision_features = vision
        try:
            chunk = query("raw_observation_deploy", lambda: deployment(raw_observation_bridge(episode, window["start_step"]),
                episode.instructions[window["start_step"]]))
        finally:
            components.vla._process_vision_features = original_vision
            for handle in hooks:
                handle.remove()
        deploy_error = float(np.max(np.abs(chunk.normalized_actions - hard.float().cpu().numpy()[0])))
        if (counts != dict(vision=1, scorer=1, vla=1, head=0) or chunk.metadata["retained_indices"] != indices[0].cpu().tolist()
                or hard_error > .002 or deploy_error > .002):
            raise RuntimeError("formal hard or single-pass raw-observation deployment acceptance failed")
    return {"window_id": window["window_id"], "task_id": window["task_id"],
        "checks": {key: True for key in OPERATOR_FLAGS}, "action_gradient_norm": action_grad,
        "future_gradient_norm": future_grad, "future_head_gradient_norm": head_grad, "dense_max_abs": parity,
        "hard_max_abs": hard_error, "deployment_max_abs": deploy_error,
        "soft_gate_mass_per_camera": masses[0].cpu().tolist(), "deployment_measured_calls": counts,
        "bridge_scope": "Inverse RLDS raw-camera/proprio bridge; no simulator or latency claim."}

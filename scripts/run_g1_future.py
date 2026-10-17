"""Bounded real-VLA G1-F acceptance, cache production and matched A/B training.

Only root submits this runner. It never accesses final-test observations and
stores every trainable checkpoint on the server, outside the frozen base.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import time

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_hashes():
    paths = sorted((ROOT / "src").rglob("*.py")) + [Path(__file__)]
    return {p.relative_to(ROOT).as_posix(): file_hash(p) for p in paths}


def resolve_suite(args, config, asset):
    """No inference from filenames: Long requires explicit suite and stats key."""
    from cti_vla.evaluation.future_runtime import FUTURE_SUITES
    suite = getattr(args, "suite", "libero_spatial")
    if suite not in FUTURE_SUITES or config.get("suite", "libero_spatial") != suite:
        raise ValueError("CLI/config suite mismatch; Long cannot use the Spatial default")
    if config.get("stats_key") != FUTURE_SUITES[suite] or (
            getattr(args, "stats_key", None) is not None and args.stats_key != config["stats_key"]):
        raise ValueError("CLI/config/suite normalization key mismatch")
    repositories = {"libero_spatial": "moojink/openvla-7b-oft-finetuned-libero-spatial",
                    "libero_10": "moojink/openvla-7b-oft-finetuned-libero-10"}
    if asset.repository != repositories[suite] or asset.revision != config["model_revision"]:
        raise ValueError("suite/config and frozen base asset differ")
    if suite == "libero_10":
        if getattr(args, "stats_key", None) != FUTURE_SUITES[suite]:
            raise ValueError("Long requires explicit --stats-key libero_10_no_noops")
        budget_reuse = getattr(args, "budget_reuse_registration", None)
        seed_reuse = getattr(args, "engineering_reuse_registration", None)
        if budget_reuse is not None and seed_reuse is not None:
            raise ValueError("new-budget cache inheritance and old seed-only inheritance are distinct")
        authorized_budget = budget_reuse is not None and type(config.get("seed")) is int and config["seed"] in (17, 23, 41)
        authorized_seed = config.get("seed") in (23, 41) and seed_reuse is not None
        exact = {"seed": config["seed"] if authorized_seed or authorized_budget else 17, "arms": ["A", "B"],
            "tokens_per_camera": 32 if authorized_budget else 64,
            "scorer_dimensions": dict(token_dim=4096, language_dim=4096, proprio_dim=8,
                hidden_dim=256, num_cameras=2, patches_per_camera=256, max_instruction_tokens=128)}
        if any(config.get(k) != v for k, v in exact.items()):
            raise ValueError("Long must keep the registered common initialization/architecture/budget")
        required = {
            "training": {"updates": 100, "micro_batch": 1, "effective_batch": 8,
                "learning_rate": 1e-4, "weight_decay": .01, "gradient_clip_norm": 1.,
                "optimizer": "AdamW", "dtype_vla": "bfloat16", "dtype_scorer": "float32",
                "same_initial_scorer": True, "vla_frozen": True, "gradient_through_vla": True},
            "future": {"horizon": 8, "weight_A": 0., "weight_B": .1, "projection_seed": 917,
                "layer_norm_eps": 1e-5},
            "action_loss": {"teacher_l1_weight": .5, "demonstration_l1_weight": .5},
            "gate": {"alpha_start": 2., "alpha_end": .1},
            "selection": {"updates": [0, 25, 50, 75, 100], "metric": "hard_validation_teacher_l1",
                "tie_break": "earliest_update", "future_loss_used": False}}
        if any(config.get(section, {}).get(k) != v for section, fields in required.items() for k, v in fields.items()):
            raise ValueError("Long training settings differ from the one registered round")
    return suite


def data_registration(args, config, asset):
    suite = resolve_suite(args, config, asset)
    if suite == "libero_10":
        from cti_vla.data import long_future_windows as windows_api
        protocol = windows_api.load_long_future_protocol(args.protocol)
    else:
        from cti_vla.data import future_windows as windows_api
        from cti_vla.data.experiment_protocol import load_experiment_protocol
        protocol = load_experiment_protocol(args.protocol)
    manifest = windows_api.load_future_windows(args.windows, protocol)
    if config["future"]["horizon"] != manifest["horizon"]:
        raise ValueError("registered horizon mismatch")
    if suite == "libero_10" and (manifest.get("suite") != suite or protocol.payload.get("suite") != suite):
        raise ValueError("Long cannot use Spatial windows or protocol")
    return suite, protocol, manifest, windows_api


def require_input_gate(args, config, asset, protocol, manifest):
    from cti_vla.evaluation.teacher_diagnostics import require_g0
    from cti_vla.evaluation.libero_runtime import INPUTS_VERSION
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    if config.get("suite", "libero_spatial") == "libero_10":
        from cti_vla.evaluation.future_input_acceptance import select_input_windows, require_long_input_acceptance, verify_input_acceptance_journal
        path = getattr(args, "input_acceptance_report", None)
        if path is None or getattr(args, "g0_report", None) is not None:
            raise ValueError("Long requires its own --input-acceptance-report, never a Spatial G0")
        report = read_json(path)
        budget_path = getattr(args, "budget_reuse_registration", None)
        if budget_path is not None:
            from cti_vla.evaluation.future_budget_reuse import load_long_budget_reuse
            if args.mode == "acceptance" and config["seed"] != 17:
                raise ValueError("the registered new64-budget operator acceptance uses seed17")
            contract = load_long_budget_reuse(budget_path, config=config,
                project_root=args.project_root, source_root=ROOT,
                expected_paths={"input_acceptance": path, "windows": args.windows,
                    "protocol": args.protocol, "asset_manifest": args.asset_manifest})
            if report.get("dataset_statistics_sha256") != file_hash(args.checkpoint / "dataset_statistics.json"):
                raise ValueError("reused Long normalization statistics changed")
            args._budget_reuse = contract
            return contract.input_acceptance_sha256
        reuse_path = getattr(args, "engineering_reuse_registration", None)
        if reuse_path is not None:
            from cti_vla.evaluation.future_seed_reuse import load_long_seed_reuse
            if args.mode != "train":
                raise ValueError("seed engineering inheritance is train-only, not a new F01")
            contract = load_long_seed_reuse(reuse_path, config=config,
                project_root=args.project_root, source_root=ROOT,
                expected_paths={"input_acceptance":path, "f01_acceptance":args.acceptance_report,
                    "windows":args.windows, "protocol":args.protocol, "asset_manifest":args.asset_manifest})
            if report.get("dataset_statistics_sha256") != file_hash(args.checkpoint / "dataset_statistics.json"):
                raise ValueError("reused Long normalization statistics changed")
            args._engineering_reuse = contract
            return contract.input_acceptance_sha256
        require_long_input_acceptance(report, config=config,
            window_manifest_sha256=file_hash(args.windows), protocol_sha256=file_hash(args.protocol),
            asset_manifest_sha256=file_hash(args.asset_manifest), source_files=source_hashes(),
            verification_script_sha256=file_hash(ROOT / "scripts/verify_long_inputs.py"),
            selected_windows=select_input_windows(manifest, protocol))
        verify_input_acceptance_journal(path.parent / "calls.jsonl", report)
        if report.get("dataset_statistics_sha256") != file_hash(args.checkpoint / "dataset_statistics.json"):
            raise ValueError("Long input acceptance normalization statistics changed")
        return file_hash(path)
    if getattr(args, "g0_report", None) is None or getattr(args, "input_acceptance_report", None) is not None:
        raise ValueError("Spatial keeps its original required --g0-report gate")
    require_g0(read_json(args.g0_report), model_revision=asset.revision,
        input_version=INPUTS_VERSION, packing_version=PACKING_VERSION)
    return None


def append_json(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def save_torch(path, value):
    import torch
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    torch.save(value, temporary)
    os.replace(temporary, path)


def load_torch(path):
    import torch
    return torch.load(path, map_location="cpu", weights_only=True)


def module_hash(components):
    """Every parameter byte, streamed one tensor at a time, including vision."""
    import torch
    digest = hashlib.sha256()
    for prefix in ("vla", "action_head", "proprio_projector"):
        for name, value in getattr(components, prefix).named_parameters():
            digest.update((prefix + "." + name).encode())
            digest.update(value.detach().contiguous().reshape(-1).view(torch.uint8).cpu().numpy().tobytes())
    return digest.hexdigest()


def make_batch(record, device, *, include_future=True):
    import torch
    from cti_vla.selection.conditional import ConditionalTokenBatch
    from cti_vla.training.future_auxiliary import FutureTrainingBatch
    move = lambda key: record[key].to(device)
    conditions = ConditionalTokenBatch(move("visual"), move("language"), move("attention_mask").bool(),
        move("normalized_proprio"), torch.arange(2, device=device).repeat_interleave(256)[None],
        torch.arange(256, device=device).repeat(2)[None], torch.ones(1, 512, dtype=torch.bool, device=device))
    return FutureTrainingBatch(conditions=conditions, raw_tokens=move("raw_tokens"),
        black_tokens=move("black_tokens"), input_ids=move("input_ids"), attention_mask=move("attention_mask"),
        teacher_actions=move("teacher_actions"), demonstration_actions=move("demonstration_actions"),
        future_target=move("future_target") if include_future else None)


def cache_records(args, config, manifest, protocol, components, processor, policy, *, limit=None):
    import numpy as np
    import torch
    if config.get("suite", "libero_spatial") == "libero_10":
        from cti_vla.data.long_future_windows import normalize_demo_actions, validate_future_window
    else:
        from cti_vla.data.future_windows import normalize_demo_actions, validate_future_window
    from cti_vla.data.sequence_example import decode_libero_example
    from cti_vla.data.tfrecord import iter_tfrecord_records
    from cti_vla.evaluation.libero_runtime import prepare_rlds_eval_inputs, _prepare_processed_inputs, process_camera
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
    from cti_vla.training.future_auxiliary import frozen_future_target
    vla = components.vla
    device = next(vla.parameters()).device
    config_sha, window_sha = file_hash(args.config), file_hash(args.windows)
    producer_identity = {"source_files": source_hashes(), "asset_manifest_sha256": file_hash(args.asset_manifest),
        "model_revision": config["model_revision"], "dataset_statistics_sha256": file_hash(args.checkpoint / "dataset_statistics.json")}
    cache_root = args.feature_cache / json_signature(producer_identity)[:20]
    rows = manifest["windows"] if limit is None else [r for r in manifest["windows"] if r["split"] == "train"][:limit]
    by_shard = defaultdict(lambda: defaultdict(list))
    for row in rows:
        by_shard[row["source_shard"]][row["record_index"]].append(row)
    cache_root.mkdir(parents=True, exist_ok=True)
    index = []
    for shard, wanted in sorted(by_shard.items()):
        shard_path = args.data_directory / shard
        if {"bytes": shard_path.stat().st_size, "sha256": file_hash(shard_path)} != manifest["source_files"][shard]:
            raise ValueError("runtime RLDS shard changed from registered data")
        for record_index, payload in iter_tfrecord_records(shard_path):
            if record_index not in wanted:
                continue
            # Do not decode unregistered or held-out episode observations.
            episode = replace(decode_libero_example(payload), source_shard=shard, record_index=record_index)
            for row in wanted[episode.record_index]:
                validate_future_window(row, episode, protocol)
                key = hashlib.sha256(row["window_id"].encode()).hexdigest()
                path, receipt_path = cache_root / (key + ".pt"), cache_root / (key + ".json")
                identity = {"window": row, "config_sha256": config_sha, "window_manifest_sha256": window_sha,
                    "producer": producer_identity}
                if path.exists() and receipt_path.exists():
                    receipt = read_json(receipt_path)
                    if receipt["identity"] != identity or receipt["cache_sha256"] != file_hash(path):
                        raise ValueError("future feature cache identity/hash mismatch")
                    index.append({"path": str(path), **receipt})
                    continue
                started = time.perf_counter()
                append_json(args.output / "cost_events.jsonl", {"event": "cache_start", "window_id": row["window_id"], "job_id": os.environ["SLURM_JOB_ID"]})
                with torch.no_grad():
                    inputs = prepare_rlds_eval_inputs(episode, row["start_step"], processor,
                        vla.norm_stats[config["stats_key"]]["proprio"], device=device, dtype=torch.bfloat16)
                    future = prepare_rlds_eval_inputs(episode, row["future_step"], processor,
                        vla.norm_stats[config["stats_key"]]["proprio"], device=device, dtype=torch.bfloat16)
                    raw = vla.vision_backbone(inputs["pixel_values"]).detach()
                    visual = vla.projector(raw).detach()
                    language = vla.get_input_embeddings()(inputs["input_ids"]).detach()
                    black_image = process_camera(np.zeros((256, 256, 3), dtype=np.uint8), already_rotated=True)
                    black_inputs = _prepare_processed_inputs([black_image, black_image], episode.proprio[row["start_step"]],
                        episode.instructions[row["start_step"]], processor, vla.norm_stats[config["stats_key"]]["proprio"],
                        device=device, dtype=torch.bfloat16)
                    black = vla.vision_backbone(black_inputs["pixel_values"]).detach()
                    teacher = policy.forward_from_full_tokens(visual, inputs["normalized_proprio"],
                        input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"])
                    target = frozen_future_target(vla._process_vision_features(future["pixel_values"], None, False))
                    demonstration = normalize_demo_actions(episode.actions[row["action_start"]:row["action_stop_exclusive"]],
                        vla.norm_stats[config["stats_key"]]["action"])
                    record = {"raw_tokens": raw, "visual": visual, "language": language, "black_tokens": black,
                        "teacher_actions": teacher.float(), "demonstration_actions": torch.as_tensor(demonstration)[None],
                        "future_target": target, **{k: inputs[k] for k in ("input_ids", "attention_mask", "normalized_proprio")}}
                    save_torch(path, {k: v.detach().cpu() for k, v in record.items()})
                torch.cuda.synchronize()
                receipt = {"identity": identity, "cache_sha256": file_hash(path), "cache_bytes": path.stat().st_size,
                    "seconds": time.perf_counter() - started, "teacher_forwards": 1, "vision_forwards": 3,
                    "window_alignment_validated": True, "future_target_detached": True, "checkpoint_normalization": True}
                atomic_json(receipt_path, receipt)
                append_json(args.output / "cost_events.jsonl", {"event": "cache_end", "window_id": row["window_id"], **receipt})
                index.append({"path": str(path), **receipt})
    if len(index) != len(rows):
        raise ValueError("registered future windows missing from RLDS")
    index.sort(key=lambda r: r["identity"]["window"]["window_id"])
    atomic_json(args.output / ("cache_index.json" if limit is None else "acceptance_cache_index.json"), index)
    return index


def acceptance(args, config, index, components, policy, student):
    import copy
    import torch
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    from cti_vla.evaluation.libero_runtime import INPUTS_VERSION
    from cti_vla.selection import ConditionalInfluenceEstimator
    from cti_vla.training.future_auxiliary import FutureAuxiliaryHead, future_auxiliary_loss, hard_select_future
    device = next(components.vla.parameters()).device
    budget = config.get("tokens_per_camera", 64)
    torch.manual_seed(config["seed"])
    scorer = ConditionalInfluenceEstimator(**config["scorer_dimensions"]).to(device)
    head = FutureAuxiliaryHead(config["scorer_dimensions"]["token_dim"]).to(device)
    before = module_hash(components)
    initial = {k: v.detach().clone() for k, v in scorer.state_dict().items()}
    torch.cuda.reset_peak_memory_stats()
    batch = make_batch(load_torch(index[0]["path"]), device)
    full = torch.arange(512, device=device)[None]
    started = time.perf_counter()
    with torch.no_grad():
        dense = student(batch.conditions.visual, full, input_ids=batch.input_ids,
            attention_mask=batch.attention_mask, normalized_proprio=batch.conditions.normalized_proprio)
    parity = float((dense.float() - batch.teacher_actions).abs().max())
    if parity > .002:
        raise RuntimeError(f"differentiable dense path differs from accepted teacher: {parity}")
    a = future_auxiliary_loss(scorer, student, batch, alpha=2.0, tokens_per_camera=budget)
    a.loss.backward()
    action_grad = sum(float(p.grad.float().square().sum()) for p in scorer.parameters() if p.grad is not None) ** .5
    a_scores = a.scores.detach().clone()
    scorer.zero_grad(set_to_none=True)
    del a
    b = future_auxiliary_loss(scorer, student, batch, alpha=2.0, auxiliary_head=head, auxiliary_weight=.1,
        tokens_per_camera=budget)
    if not torch.equal(a_scores, b.scores.detach()):
        raise RuntimeError("A/B differ before future gradient update")
    b.future_mse.backward()
    future_grad = sum(float(p.grad.float().square().sum()) for p in scorer.parameters() if p.grad is not None) ** .5
    head_grad = sum(float(p.grad.float().square().sum()) for p in head.parameters() if p.grad is not None) ** .5
    if not all(0 < x < float("inf") for x in (action_grad, future_grad, head_grad)):
        raise RuntimeError("missing/nonfinite action or future gradient")
    scorer.zero_grad(set_to_none=True)
    head.zero_grad(set_to_none=True)
    del b
    # A complete optimizer step proves updates are confined to the trainable branches.
    optimizer = torch.optim.AdamW(list(scorer.parameters()) + list(head.parameters()), lr=1e-4, weight_decay=.01)
    result = future_auxiliary_loss(scorer, student, batch, alpha=2.0, auxiliary_head=head, auxiliary_weight=.1,
        tokens_per_camera=budget)
    gate_mass = result.gates.detach().reshape(-1, 2, 256).sum(-1)
    if not torch.allclose(gate_mass, torch.full_like(gate_mass, float(budget)), atol=.01, rtol=0):
        raise RuntimeError("soft gate mass differs from registered per-camera budget")
    result.loss.backward()
    torch.nn.utils.clip_grad_norm_(list(scorer.parameters()) + list(head.parameters()), 1.0, error_if_nonfinite=True)
    optimizer.step()
    student.require_frozen()
    if all(torch.equal(initial[k], v) for k, v in scorer.state_dict().items()):
        raise RuntimeError("DIE optimizer step changed no parameter")
    with torch.no_grad():
        scores = scorer(batch.conditions, batch.conditions.valid)
        scorer.eval()
        indices = hard_select_future(scorer, batch.conditions, tokens_per_camera=budget).source_indices
        hard = policy.forward_from_full_tokens(batch.conditions.visual, batch.conditions.normalized_proprio,
            input_ids=batch.input_ids, attention_mask=batch.attention_mask, retained_indices=indices)
        packed = batch.conditions.visual.gather(1, indices[..., None].expand(-1, -1, batch.conditions.visual.shape[-1]))
        paired = student(packed, indices, input_ids=batch.input_ids, attention_mask=batch.attention_mask,
            normalized_proprio=batch.conditions.normalized_proprio)
        hard_diff = float((hard.float() - paired.float()).abs().max())
        if hard_diff > .002 or indices.shape != (1, 2 * budget) or len(indices.unique()) != 2 * budget or int((indices < 256).sum()) != budget:
            raise RuntimeError(f"hard{2 * budget} selection/packing acceptance failed")
        # Change training-only future/GT fields while keeping current conditions fixed.
        mutated = copy.copy(batch)
        object.__setattr__(mutated, "future_target", batch.future_target.flip(-1))
        object.__setattr__(mutated, "demonstration_actions", -batch.demonstration_actions)
        if not torch.equal(scorer(batch.conditions, batch.conditions.valid), scorer(mutated.conditions, mutated.conditions.valid)):
            raise RuntimeError("training-only information reached DIE")
    after = module_hash(components)
    if before != after:
        raise RuntimeError("frozen VLA parameter bytes changed")
    torch.cuda.synchronize()
    report = {"stage": "G1-F01", "status": "passed", "execution": "real_frozen_openvla_l40",
        "config_sha256": json_signature(config), "config_file_sha256": file_hash(args.config), "window_manifest_sha256": file_hash(args.windows),
        "model_revision": config["model_revision"], "input_version": INPUTS_VERSION, "packing_version": PACKING_VERSION,
        "checks": {"time_alignment": True, "no_future_leakage": True, "action_gradient_to_die": True,
            "future_gradient_to_die": True, "vla_parameters_unchanged": True, f"hard{2 * budget}_packing": True,
            "dense_differentiable_parity": True},
        "action_gradient_norm": action_grad, "future_gradient_norm": future_grad, "future_head_gradient_norm": head_grad,
        "dense_max_abs": parity, "hard_max_abs": hard_diff, "vla_parameter_sha256": before,
        "peak_memory_allocated_bytes": torch.cuda.max_memory_allocated(), "seconds": time.perf_counter() - started,
        "hardware": torch.cuda.get_device_name(), "runtime": {"torch": torch.__version__, "python": platform.python_version()},
        "accepted_training_windows": [r["identity"]["window"]["window_id"] for r in index],
        "source_files": source_hashes(), "job_id": os.environ["SLURM_JOB_ID"]}
    if budget == 32:
        report.update(visual_tokens=64, per_camera_budgets=[32, 32],
            soft_gate_mass_per_camera=gate_mass.cpu().tolist(),
            reuse_scope="original inputs/cache only; newly measured64-budget gradients and hard packing")
    if config.get("suite") == "libero_10":
        report.update(suite="libero_10", stats_key=config["stats_key"],
            input_acceptance_sha256=file_hash(args.input_acceptance_report),
            operator_window_id=index[0]["identity"]["window"]["window_id"])
        report["checks"]["official_input_action_parity"] = True
    atomic_json(args.output / "f01_acceptance.json", report)
    return report


def training_order(count, updates, batch_size, seed):
    rng = random.Random(seed)
    order = []
    while len(order) < updates * batch_size:
        epoch = list(range(count))
        rng.shuffle(epoch)
        order.extend(epoch)
    return [order[i * batch_size:(i + 1) * batch_size] for i in range(updates)]


def validate_hard(scorer, head, records, policy, student, *, alpha, tokens_per_camera=64):
    import numpy as np
    import torch
    from cti_vla.training.future_auxiliary import hard_select_future
    from cti_vla_baselines.acl_matched import gate_raw_tokens, soft_top_k
    scorer.eval()
    device = next(scorer.parameters()).device
    rows = []
    with torch.no_grad():
        for item, record in records:
            batch = make_batch(record, device)
            indices = hard_select_future(scorer, batch.conditions, tokens_per_camera=tokens_per_camera).source_indices
            pred = policy.forward_from_full_tokens(batch.conditions.visual, batch.conditions.normalized_proprio,
                input_ids=batch.input_ids, attention_mask=batch.attention_mask, retained_indices=indices).float()
            row = {"window": item["identity"]["window"], "teacher_l1": float((pred - batch.teacher_actions).abs().mean()),
                "demonstration_l1": float((pred - batch.demonstration_actions).abs().mean()),
                "retained_indices": indices[0].cpu().tolist(), "normalized_actions": pred[0].cpu().tolist()}
            if head is not None:
                scores = scorer(batch.conditions, batch.conditions.valid)
                gates = torch.cat([soft_top_k(scores[:, c*256:(c+1)*256], tokens_per_camera, alpha) for c in range(2)], 1)
                projected = student.visual_projector(gate_raw_tokens(batch.raw_tokens, gates, batch.black_tokens))
                future = head(projected, batch.demonstration_actions)
                # Readout interventions diagnose reliance; these are not newly trained arms.
                zero_visual = head(torch.zeros_like(projected), batch.demonstration_actions)
                reversed_actions = head(projected, batch.demonstration_actions.flip(1))
                row.update(future_mse=float((future - batch.future_target).square().mean()),
                    future_zero_visual_mse=float((zero_visual - batch.future_target).square().mean()),
                    future_reversed_action_mse=float((reversed_actions - batch.future_target).square().mean()))
            rows.append(row)
    values = np.asarray([r["teacher_l1"] for r in rows])
    summary = {"validation_metric": float(values.mean()), "teacher_l1_p95": float(np.percentile(values, 95)),
        "demonstration_l1": float(np.mean([r["demonstration_l1"] for r in rows])), "windows": len(rows)}
    if head is not None:
        for key in ("future_mse", "future_zero_visual_mse", "future_reversed_action_mse"):
            summary[key] = float(np.mean([r[key] for r in rows]))
    scorer.train()
    return {**summary, "observations": rows}


def train_pair(args, config, index, components, policy, student):
    import torch
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation.future_runtime import make_future_checkpoint_metadata, make_future_deployment_receipt
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature, tensor_signature
    from cti_vla.selection import ConditionalInfluenceEstimator
    from cti_vla.training.future_auxiliary import FutureAuxiliaryHead, future_auxiliary_loss
    from cti_vla_baselines.acl_matched import cosine_alpha
    device = next(components.vla.parameters()).device
    data = {split: [(r, load_torch(r["path"])) for r in index if r["identity"]["window"]["split"] == split]
        for split in ("train", "validation")}
    if len(data["train"]) != 90 or len(data["validation"]) != 60:
        raise ValueError("registered first G1-F requires its complete90/60 valid-window panels")
    spec = config["training"]
    updates, effective = spec["updates"], spec["effective_batch"]
    budget = config.get("tokens_per_camera", 64)
    schedule = training_order(len(data["train"]), updates, effective, config["seed"])
    source = source_hashes()
    window_sha = file_hash(args.windows)
    long_identity = ({"suite": "libero_10", "input_acceptance_sha256": file_hash(args.input_acceptance_report),
                      "f01_report_sha256": file_hash(args.acceptance_report)} if config.get("suite") == "libero_10" else {})
    torch.manual_seed(config["seed"])
    initial = ConditionalInfluenceEstimator(**config["scorer_dimensions"]).state_dict()
    initial_sha = tensor_signature(initial)
    order_manifest = [[data["train"][j][0]["identity"]["window"]["window_id"] for j in row] for row in schedule]
    atomic_json(args.output / "training_order.json", {"seed": config["seed"], "updates": order_manifest,
        "initial_scorer_sha256": initial_sha, "order_sha256": json_signature(order_manifest)})
    frozen_before = module_hash(components)
    arm_results = {}
    for arm in config["arms"]:
        training_config = {**config, "arm": arm}
        arm_output = args.output / arm
        arm_output.mkdir(parents=True, exist_ok=True)
        arm_checkpoints = args.training_checkpoints / arm
        arm_checkpoints.mkdir(parents=True, exist_ok=True)
        complete_path = arm_output / "training_report.json"
        if complete_path.exists():
            complete = read_json(complete_path)
            if complete["status"] != "completed" or complete["config_sha256"] != json_signature(training_config) or complete["window_manifest_sha256"] != window_sha or complete["source_files"] != source:
                raise ValueError("existing arm completion does not match immutable run")
            if any(complete.get(k) != v for k, v in long_identity.items()):
                raise ValueError("completed Long arm input/F01 identity changed")
            if file_hash(complete["best_checkpoint"]) != complete["best_checkpoint_sha256"]:
                raise ValueError("completed arm best checkpoint changed")
            arm_results[arm] = complete
            continue
        scorer = ConditionalInfluenceEstimator(**config["scorer_dimensions"])
        scorer.load_state_dict(initial, strict=True)
        scorer = scorer.to(device)
        torch.manual_seed(config["seed"] + 10000)
        head = FutureAuxiliaryHead(config["scorer_dimensions"]["token_dim"]).to(device) if arm == "B" else None
        parameters = list(scorer.parameters()) + ([] if head is None else list(head.parameters()))
        optimizer = torch.optim.AdamW(parameters, lr=spec["learning_rate"], weight_decay=spec["weight_decay"])
        evaluations, best, next_update = [], None, 1
        resume_path = arm_checkpoints / "resume.pt"
        had_resume = resume_path.exists()
        if had_resume:
            saved = load_torch(resume_path)
            if saved["config_sha256"] != json_signature(training_config) or saved["window_manifest_sha256"] != window_sha or saved["source_files"] != source or saved["initial_scorer_sha256"] != initial_sha:
                raise ValueError("cannot resume incompatible A/B training")
            if any(saved.get(k) != v for k, v in long_identity.items()):
                raise ValueError("cannot resume Long from another suite/input/F01 acceptance")
            scorer.load_state_dict(saved["scorer"])
            if head is not None:
                head.load_state_dict(saved["head"])
            optimizer.load_state_dict(saved["optimizer"])
            evaluations, best, next_update = saved["evaluations"], saved["best"], saved["completed_update"] + 1
        arm_started = time.perf_counter()
        torch.cuda.reset_peak_memory_stats()
        for update in range(next_update - 1, updates + 1):
            # A resumed boundary has already been evaluated and persisted.
            resumed_boundary = had_resume and update == next_update - 1
            if update >= next_update:
                alpha = cosine_alpha(update - 1, updates - 1)
                start = time.perf_counter()
                append_json(arm_output / "cost_events.jsonl", {"event": "update_start", "update": update,
                    "window_ids": order_manifest[update - 1], "job_id": os.environ["SLURM_JOB_ID"]})
                optimizer.zero_grad(set_to_none=True)
                accumulated = defaultdict(float)
                for j in schedule[update - 1]:
                    batch = make_batch(data["train"][j][1], device, include_future=arm == "B")
                    result = future_auxiliary_loss(scorer, student, batch, alpha=alpha, auxiliary_head=head,
                        auxiliary_weight=config["future"]["weight_" + arm], tokens_per_camera=budget)
                    (result.loss / effective).backward()
                    for key in ("loss", "action_loss", "teacher_l1", "demonstration_l1", "future_mse"):
                        value = getattr(result, key)
                        if value is not None:
                            accumulated[key] += float(value.detach()) / effective
                    del result, batch
                grad_norm = float(torch.nn.utils.clip_grad_norm_(parameters, spec["gradient_clip_norm"], error_if_nonfinite=True))
                optimizer.step()
                student.require_frozen()
                torch.cuda.synchronize()
                append_json(arm_output / "cost_events.jsonl", {"event": "update_end", "update": update, "alpha": alpha,
                    "seconds": time.perf_counter() - start, "forward_backward_samples": effective,
                    "grad_norm": grad_norm, **accumulated, "job_id": os.environ["SLURM_JOB_ID"]})
                print(json.dumps({"arm": arm, "update": update, **accumulated}), flush=True)
            if update in config["selection"]["updates"] and not resumed_boundary:
                started = time.perf_counter()
                validation = validate_hard(scorer, head, data["validation"], policy, student,
                    alpha=cosine_alpha(max(0, update - 1), updates - 1), tokens_per_camera=budget)
                validation.update(update=update, seconds=time.perf_counter() - started, arm=arm)
                atomic_json(arm_output / f"validation_{update:04d}.json", validation)
                evaluations.append({"update": update, "validation_metric": validation["validation_metric"]})
                if best is None or validation["validation_metric"] < best["validation_metric"]:
                    best = make_future_checkpoint_metadata(arm=arm, seed=config["seed"],
                        scorer_dimensions=config["scorer_dimensions"], training_config=training_config, pair_config=config,
                        window_manifest_sha256=window_sha, model_revision=config["model_revision"], stats_key=config["stats_key"],
                        training_source_files=source, update=update, validation_metric=validation["validation_metric"],
                        input_acceptance_sha256=long_identity.get("input_acceptance_sha256"))
                    save_torch(arm_checkpoints / "best.pt", {**best,
                        "estimator_state_dict": {k: v.detach().cpu() for k, v in scorer.state_dict().items()}})
                save_torch(resume_path, {"config_sha256": json_signature(training_config), "window_manifest_sha256": window_sha,
                    "source_files": source, "initial_scorer_sha256": initial_sha, "completed_update": update,
                    "scorer": scorer.state_dict(), "head": None if head is None else head.state_dict(),
                    "optimizer": optimizer.state_dict(), "evaluations": evaluations, "best": best, **long_identity})
        frozen_after = module_hash(components)
        if frozen_before != frozen_after:
            raise RuntimeError("frozen VLA parameters changed during training")
        verify_checkpoint_directory(args.checkpoint, load_checkpoint_manifest(args.asset_manifest))
        receipt = make_future_deployment_receipt(arm_checkpoints / "best.pt", best, training_config=training_config,
            pair_config=config, f01_report_sha256=file_hash(args.acceptance_report), planned_updates=updates,
            completed_updates=updates, evaluations=evaluations)
        atomic_json(arm_output / "deployment_receipt.json", receipt)
        report = {"status": "completed", "arm": arm, "config_sha256": json_signature(training_config),
            "window_manifest_sha256": window_sha, "source_files": source, "evaluations": evaluations,
            "initial_scorer_sha256": initial_sha, "sample_order_sha256": json_signature(order_manifest),
            "best_checkpoint": str(arm_checkpoints / "best.pt"), "best_checkpoint_sha256": receipt["checkpoint_sha256"],
            "best_update": best["update"], "best_validation_metric": best["validation_metric"],
            "vla_parameters_unchanged": True, "vla_parameter_sha256": frozen_after,
            "trainable_parameters": sum(p.numel() for p in parameters),
            "future_head_parameters": 0 if head is None else sum(p.numel() for p in head.parameters()),
            "peak_memory_allocated_bytes": torch.cuda.max_memory_allocated(),
            "wall_seconds_this_attempt": time.perf_counter() - arm_started,
            "training_updates_completed": updates, "attempt_start_update": next_update,
            "teacher_forwards_cached": len(index), "job_id": os.environ["SLURM_JOB_ID"], **long_identity}
        atomic_json(complete_path, report)
        arm_results[arm] = report
        del scorer, head, optimizer, parameters
        torch.cuda.empty_cache()
    report = {"status": "completed", "stage": "G1-F02", "arms": arm_results,
        "interpretation": "Hard action validation only; await paired development closed-loop and full latency before deciding expansion"}
    atomic_json(args.output / "training_summary.json", report)
    return report


def run(args):
    from cti_vla.data.experiment_protocol import write_frozen_json
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation.libero_runtime import INPUTS_VERSION
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, require_g0, json_signature
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    if os.name == "nt" or not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("real VLA execution is server Slurm only")
    config = read_json(args.config)
    asset = load_checkpoint_manifest(args.asset_manifest)
    suite, protocol, manifest, _ = data_registration(args, config, asset)
    input_acceptance_sha = require_input_gate(args, config, asset, protocol, manifest)
    reuse = getattr(args, "_engineering_reuse", None)
    budget_reuse = getattr(args, "_budget_reuse", None)
    input_reuse = budget_reuse if budget_reuse is not None else reuse
    long_sources = source_hashes() if suite == "libero_10" else None
    long_watched = ({str(p.resolve()): file_hash(p) for p in (args.config, args.windows,
        args.protocol, args.asset_manifest, args.input_acceptance_report, args.input_acceptance_report.parent / "calls.jsonl",
        ROOT / "scripts/verify_long_inputs.py", *([args.acceptance_report] if args.mode == "train" else []))}
        if suite == "libero_10" else {})
    if input_reuse is not None:
        from cti_vla.evaluation.future_seed_reuse import require_fresh_seed_destinations, verify_reused_cache
        require_fresh_seed_destinations(args.output, args.training_checkpoints)
        long_watched.update(input_reuse.watched_files)
        reused_index = verify_reused_cache(input_reuse, args.feature_cache)
        for entry in reused_index:
            path = Path(entry["path"])
            long_watched[str(path.resolve())] = entry["cache_sha256"]
            long_watched[str(path.with_suffix(".json").resolve())] = file_hash(path.with_suffix(".json"))
    base = args.checkpoint.resolve()
    project = Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
    weight_root = Path("/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints")
    for path in (args.output, args.feature_cache, args.cache_directory):
        if project not in path.resolve().parents or base in path.resolve().parents or ROOT in path.resolve().parents:
            raise ValueError("runtime outputs must stay in CTI-VLA outside source/base snapshot")
    if weight_root not in args.training_checkpoints.resolve().parents:
        raise ValueError("training weights must stay in the server CTI checkpoint root")
    args.output.mkdir(parents=True, exist_ok=True)
    write_frozen_json(args.output / "registered_config.json", config)
    write_frozen_json(args.output / "registered_windows.json", manifest)
    if input_reuse is not None:
        name = "input_cache_reuse_receipt.json" if budget_reuse is not None else "engineering_reuse_receipt.json"
        atomic_json(args.output / name, input_reuse.receipt)
    if args.mode == "train":
        if budget_reuse is not None:
            from cti_vla.evaluation.future_budget_reuse import require_budget_f01
            gate = require_budget_f01(args.acceptance_report, config=config, source_root=ROOT,
                window_manifest_sha256=file_hash(args.windows), input_acceptance_sha256=input_acceptance_sha)
            long_watched.update(gate["watched_files"])
            atomic_json(args.output / "same_budget_f01_receipt.json", gate["receipt"])
        else:
            from cti_vla.evaluation.future_runtime import require_future_f01
            passed = read_json(args.acceptance_report)
            require_future_f01(passed, pair_id=reuse.parent_pair_id if reuse is not None else json_signature(config), window_manifest_sha256=file_hash(args.windows),
                model_revision=asset.revision, suite=suite, input_acceptance_sha256=input_acceptance_sha)
            finalized = read_json(args.acceptance_report.parent / "acceptance_finalization.json")
            expected_parent_sources = read_json(args.input_acceptance_report)["source_files"] if reuse is not None else source_hashes()
            if passed["source_files"] != expected_parent_sources or finalized.get("status") != "verified" or finalized.get("checkpoint_unchanged") is not True or finalized.get("result_sha256") != file_hash(args.acceptance_report):
                raise ValueError("training requires finalized F01 evidence from this exact implementation")
    for folder in (args.cache_directory, args.cache_directory / "hub", args.cache_directory / "modules"):
        folder.mkdir(parents=True, exist_ok=True)
    os.environ.update(HF_HOME=str(args.cache_directory), HF_HUB_CACHE=str(args.cache_directory / "hub"),
        HF_MODULES_CACHE=str(args.cache_directory / "modules"), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    import torch
    from transformers import AutoProcessor
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
    from cti_vla_baselines.acl_matched import FrozenDifferentiableOFTPolicy
    if torch.cuda.device_count() != 1:
        raise RuntimeError("requires exactly one scheduler-assigned GPU")
    before = verify_checkpoint_directory(base, asset)
    components = load_openvla_oft_components(base, device="cuda:0", use_minimal_prismatic_compat=True)
    processor = AutoProcessor.from_pretrained(base, trust_remote_code=True, local_files_only=True)
    policy = OpenVLAOFTTokenPolicy(components.vla, components.action_head, components.proprio_projector, num_patches_full=512)
    student = FrozenDifferentiableOFTPolicy(policy, components.vla.projector, model_revision=asset.revision, input_version=INPUTS_VERSION)
    if input_reuse is not None:
        index = ([r for r in reused_index if r["identity"]["window"]["split"] == "train"][:2]
            if args.mode == "acceptance" else reused_index)
        atomic_json(args.output / ("acceptance_cache_index.json" if args.mode == "acceptance" else "cache_index.json"), index)
    else:
        index = cache_records(args, config, manifest, protocol, components, processor, policy,
            limit=2 if args.mode == "acceptance" else None)
    if args.mode == "acceptance":
        report = acceptance(args, config, index, components, policy, student)
    else:
        report = train_pair(args, config, index, components, policy, student)
    after = verify_checkpoint_directory(base, asset)
    if before != after or (long_sources is not None and (long_sources != source_hashes() or
            any(file_hash(Path(p)) != sha for p, sha in long_watched.items()))):
        raise RuntimeError("immutable checkpoint verification changed")
    atomic_json(args.output / (args.mode + "_finalization.json"), {"status": "verified", "checkpoint_unchanged": True,
        "checkpoint": asdict(after), "job_id": os.environ["SLURM_JOB_ID"], "result_status": report["status"],
        "result_sha256": file_hash(args.output / ("f01_acceptance.json" if args.mode == "acceptance" else "training_summary.json"))})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("config", "windows", "protocol", "checkpoint", "asset-manifest", "data-directory",
                 "cache-directory", "feature-cache", "training-checkpoints", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--acceptance-report", type=Path)
    parser.add_argument("--g0-report", type=Path)
    parser.add_argument("--input-acceptance-report", type=Path)
    parser.add_argument("--suite", choices=("libero_spatial", "libero_10"), default="libero_spatial")
    parser.add_argument("--stats-key")
    parser.add_argument("--engineering-reuse-registration", "--reuse-registration", type=Path)
    parser.add_argument("--budget-reuse-registration", type=Path)
    parser.add_argument("--project-root", type=Path, default=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA"))
    parser.add_argument("--mode", choices=("acceptance", "train"), required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    try:
        report = run(args)
        print(json.dumps({"status": report["status"], "mode": args.mode}, ensure_ascii=False), flush=True)
    except Exception as error:
        from cti_vla.evaluation.teacher_diagnostics import atomic_json
        atomic_json(args.output / ("failure_" + os.environ.get("SLURM_JOB_ID", "local") + ".json"),
            {"status": "failed", "mode": args.mode, "error_type": type(error).__name__, "error": str(error),
             "seconds": time.perf_counter() - started, "utc": datetime.now(timezone.utc).isoformat()})
        raise


if __name__ == "__main__":
    main()

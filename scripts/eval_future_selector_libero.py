"""Paired G1-F A/B development rollouts on30 fixed states; never test.

Real training checkpoints stay on the server. --prepare-only inspects only
the frozen development panel and does not accept F01 or checkpoint evidence.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _g0_helpers():
    spec = importlib.util.spec_from_file_location("cti_future_g0_helpers", ROOT / "scripts/eval_libero.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_suite_arguments(args):
    """Long is explicit; legacy Spatial defaults remain unchanged."""
    suite = getattr(args, "suite", "libero_spatial")
    if suite not in ("libero_spatial", "libero_10"):
        raise ValueError("unsupported explicit deployment suite")
    long = suite == "libero_10"
    if long and (getattr(args, "panel", None) is None or getattr(args, "config", None) is None):
        raise ValueError("Long requires explicit --suite libero_10 --panel and --config")
    defaults = {"config": ROOT / "configs/experiments/g1_future_v1.json",
        "window_manifest": ROOT / f"configs/manifests/{'long' if long else 'spatial'}_future_v1/windows.json",
        "protocol": ROOT / ("configs/manifests/long_future_v1/protocol.json" if long else "configs/manifests/spatial_g0g1_v1/protocol.json"),
        "asset_manifest": ROOT / f"configs/assets/openvla_oft_libero_{'long' if long else 'spatial'}.json",
        "stats_key": "libero_10_no_noops" if long else "libero_spatial_no_noops",
        "controls": ([] if getattr(args, "dense_reference", None) else ["dense"]) if long else ["dense", "uniform128"]}
    for key, value in defaults.items():
        if getattr(args, key, None) is None:
            setattr(args, key, value)
    args.suite = suite
    if long and _read(args.config).get("suite") != suite:
        raise ValueError("Long requires its own suite-bound configuration")
    if not long and getattr(args, "panel", None) is not None:
        raise ValueError("legacy Spatial uses its original fixed development/G0 manifests")
    return suite


def validate_output_paths(args):
    project, source = args.project_root.resolve(), ROOT.resolve()
    if project != source and project not in source.parents:
        raise ValueError("G1-F source snapshot must belong to the declared project")
    for target in (args.output_directory.resolve(), args.cache_directory.resolve()):
        if project not in target.parents or (source != project and (target == source or source in target.parents)):
            raise ValueError("G1-F artifacts/cache must be inside the project and outside its source snapshot")
        for weight_root in (args.checkpoint.resolve(), args.checkpoint_a.resolve().parent, args.checkpoint_b.resolve().parent):
            if target == weight_root or weight_root in target.parents:
                raise ValueError("G1-F artifacts/cache must stay outside immutable model/checkpoint directories")


@contextmanager
def _exclusive_output(output):
    import fcntl
    output.mkdir(parents=True, exist_ok=True)
    with (output / ".evaluation.lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("another G1-F evaluation owns this output directory") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def run(args):
    from cti_vla.evaluation.future_trials import load_future_development_panel, METHOD_ORDER
    suite = resolve_suite_arguments(args)
    if suite == "libero_10":
        from cti_vla.data.long_initial_states import load_long_development_panel
        panel = load_long_development_panel(args.panel)
    else:
        panel = load_future_development_panel(args.development_states, args.g0_panel)
    controls = tuple(args.controls)
    pair_config = _read(args.config)
    budget = pair_config.get("tokens_per_camera", 64)
    if type(budget) is not int or budget not in (32, 64):
        raise ValueError("G1-F deployment budget must be the registered32 or64 tokens per camera")
    budget_registration = getattr(args, "budget_reuse_registration", None)
    if budget == 32 and (suite != "libero_10" or budget_registration is None):
        raise ValueError("new64-token Long deployment requires explicit budget reuse registration and new F01")
    if len(set(controls)) != len(controls) or set(controls) - {"dense", "uniform128"}:
        raise ValueError("controls may contain dense and uniform128 once each")
    reference_path = getattr(args, "dense_reference", None)
    dense_reference = None
    if reference_path is not None:
        allowed_seeds = (17, 23, 41) if budget == 32 else (23, 41)
        if suite != "libero_10" or controls or pair_config.get("seed") not in allowed_seeds or getattr(args, "seed", 17) != 17:
            raise ValueError("dense reuse requires registered Long training seeds, A/B-only, evaluation seed17")
        from cti_vla.evaluation.future_dense_reuse import load_dense_reference
        dense_reference = load_dense_reference(reference_path, panel)
    elif budget == 32:
        raise ValueError("all new64-token seeds require the unchanged original dense reference and60 A/B trials")
    elif suite == "libero_10" and (controls != ("dense",) or pair_config.get("seed", 17) != 17):
        raise ValueError("Long seed17 fixes dense/A/B90; seeds23/41 require explicit dense reference and60 A/B trials")
    methods = tuple(m for m in METHOD_ORDER if m in controls or m in ("future_A", "future_B"))
    if args.prepare_only:
        return {"stage": "G1-F_Long_development" if suite == "libero_10" else "G1-F_development",
            "status": "panel_prepared_only", "gpu_calls": 0,
            "tasks": [0, 3, 5], "states": 30, "expected_trials": 30 * len(methods), "methods": methods,
            "panel_signature": panel["panel_signature"], "test_opened": False,
            "checkpoint_validated": False, "f01_accepted": False,
            **({"visual_tokens": 64, "per_camera_budgets": [32, 32]} if budget == 32 else {}),
            **({"dense_reference_signature": dense_reference["signature"], "training_seed": pair_config["seed"],
                "evaluation_runtime_seed": 17, "reused_dense_trials": 30} if dense_reference else {})}
    required = ("f01_report", "checkpoint_a", "checkpoint_b", "receipt_a", "receipt_b", "checkpoint",
                "cache_directory", "output_directory")
    if any(getattr(args, key) is None for key in required):
        raise ValueError("G1-F execution requires F01, both checkpoint/receipt pairs, frozen base, cache and output")
    if suite == "libero_10" and getattr(args, "input_acceptance_report", None) is None:
        raise ValueError("Long requires its own official input/action acceptance receipt, not Spatial G0")
    if dense_reference is not None and budget_registration is None and getattr(args, "engineering_reuse_registration", None) is None:
        raise ValueError("new Long training seeds require explicit parent engineering evidence reuse")
    if budget_registration is not None and getattr(args, "engineering_reuse_registration", None) is not None:
        raise ValueError("64-budget acceptance cannot be replaced or mixed with legacy128 F01 inheritance")
    if os.name == "nt" or (suite == "libero_10" and not os.environ.get("SLURM_JOB_ID")):
        raise RuntimeError("real G1-F checkpoints and GPU rollouts remain on the server")
    validate_output_paths(args)
    with _exclusive_output(args.output_directory):
        return _execute(args, panel, methods)


def _execute(args, panel, methods):
    from cti_vla.data.experiment_protocol import load_experiment_protocol, write_frozen_json
    from cti_vla.data.future_windows import load_future_windows
    from cti_vla.data.identity import file_sha256
    from cti_vla.evaluation import future_runtime, future_trials, libero_runtime
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    long = args.suite == "libero_10"
    dense_reference = None
    watched_paths = [args.config, args.window_manifest, args.f01_report, args.receipt_a, args.receipt_b,
                     args.checkpoint_a, args.checkpoint_b, args.asset_manifest]
    if long:
        watched_paths.extend([args.protocol, args.panel, args.input_acceptance_report])
    if getattr(args, "dense_reference", None) is not None:
        from cti_vla.evaluation.future_dense_reuse import load_dense_reference, SOURCE_FILES
        dense_reference = load_dense_reference(args.dense_reference, panel)
        watched_paths.extend(args.dense_reference / name for name in SOURCE_FILES)
    watched = {str(p.resolve()): file_sha256(p) for p in watched_paths}
    def unchanged():
        if any(file_sha256(path) != digest for path, digest in watched.items()):
            raise ValueError("G1-F configuration/evidence/selector bytes changed during evaluation")
    common_config = _read(args.config)
    budget = common_config.get("tokens_per_camera", 64)
    if long:
        from cti_vla.data.long_future_windows import load_long_future_protocol, load_future_windows as load_long_windows
        # The protocol's optional asset is the RLDS asset, never the VLA model
        # manifest. Its frozen dataset path is resolved relative to the protocol.
        protocol = load_long_future_protocol(args.protocol)
        windows = load_long_windows(args.window_manifest, protocol)
    else:
        protocol = load_experiment_protocol(args.protocol)
        windows = load_future_windows(args.window_manifest, protocol)
    asset = load_checkpoint_manifest(args.asset_manifest)
    f01 = _read(args.f01_report)
    pair_for_acceptance = json_signature(common_config)
    if getattr(args, "budget_reuse_registration", None) is not None:
        from cti_vla.evaluation.future_budget_reuse import load_long_budget_reuse, require_budget_f01
        contract = load_long_budget_reuse(args.budget_reuse_registration, config=common_config,
            project_root=args.project_root, source_root=ROOT,
            expected_paths={"input_acceptance": args.input_acceptance_report,
                "windows": args.window_manifest, "protocol": args.protocol, "asset_manifest": args.asset_manifest})
        if contract.input_acceptance_sha256 != watched[str(args.input_acceptance_report.resolve())]:
            raise ValueError("budget reuse registration differs from supplied parent F00")
        accepted = require_budget_f01(args.f01_report, config=common_config, source_root=ROOT,
            window_manifest_sha256=watched[str(args.window_manifest.resolve())],
            input_acceptance_sha256=contract.input_acceptance_sha256)
        if accepted["report_sha256"] != watched[str(args.f01_report.resolve())]:
            raise ValueError("budget acceptance differs from supplied new64 F01")
        pair_for_acceptance = accepted["accepted_pair_id"]
        watched.update({str(Path(p).resolve()): digest for p, digest in contract.watched_files.items()})
        watched.update({str(Path(p).resolve()): digest for p, digest in accepted["watched_files"].items()})
    elif getattr(args, "engineering_reuse_registration", None) is not None:
        from cti_vla.evaluation.future_seed_reuse import load_long_seed_reuse
        contract = load_long_seed_reuse(args.engineering_reuse_registration, config=common_config,
            project_root=args.project_root, source_root=ROOT,
            expected_paths={"input_acceptance": args.input_acceptance_report, "f01_acceptance": args.f01_report,
                "windows": args.window_manifest, "protocol": args.protocol, "asset_manifest": args.asset_manifest})
        if (contract.f01_report_sha256 != watched[str(args.f01_report.resolve())]
                or contract.input_acceptance_sha256 != watched[str(args.input_acceptance_report.resolve())]):
            raise ValueError("engineering reuse registration differs from supplied parent F00/F01")
        pair_for_acceptance = contract.parent_pair_id
        watched.update({str(Path(p).resolve()): digest for p, digest in contract.watched_files.items()})
    acceptance_kwargs = {"suite": args.suite} if long else {}
    future_runtime.require_future_f01(f01, pair_id=pair_for_acceptance,
        window_manifest_sha256=watched[str(args.window_manifest.resolve())], model_revision=asset.revision,
        visual_tokens=2 * budget, per_camera_budgets=(budget, budget),
        **acceptance_kwargs)
    expected = {"model_revision": asset.revision, "input_version": libero_runtime.INPUTS_VERSION,
        "packing_version": PACKING_VERSION, "stats_key": args.stats_key,
        "window_manifest_sha256": watched[str(args.window_manifest.resolve())],
        "f01_report_sha256": watched[str(args.f01_report.resolve())]}
    if budget == 32:
        expected.update(visual_tokens=64, per_camera_budgets=[32, 32])
    if long:
        input_sha = watched[str(args.input_acceptance_report.resolve())]
        if f01.get("input_acceptance_sha256") != input_sha:
            raise ValueError("Long F01 is not bound to the supplied official input/action receipt")
        expected.update(suite=args.suite, input_acceptance_sha256=input_sha)
    sources = future_runtime.future_deployment_source_hashes(ROOT)
    loaded = {}
    for arm in ("A", "B"):
        receipt = _read(getattr(args, "receipt_" + arm.lower()))
        if receipt.get("pair_config") != common_config:
            raise ValueError("G1-F trained pair differs from the frozen common config")
        loaded[arm] = future_runtime.load_future_selector_checkpoint(getattr(args, "checkpoint_" + arm.lower()), receipt,
            expected_versions=expected, expected_source_hashes=sources)
    future_runtime.validate_future_pair(loaded["A"], loaded["B"])
    common = _g0_helpers()
    source_verification = {"openvla_oft": common.verify_source_checkout(args.official_source, libero_runtime.OFT_COMMIT),
                           "libero": common.verify_source_checkout(args.libero_source, common.LIBERO_COMMIT)}
    from cti_vla.data.initial_states import official_task_catalog
    catalog, mapping = official_task_catalog(args.libero_source, suite=panel["suite"])
    if panel["source"]["revision"] != common.LIBERO_COMMIT or any(panel["source"].get(key) != value for key, value in mapping.items()):
        raise ValueError("G1-F development task mapping differs from pinned LIBERO")
    if not (args.libero_config / "config.yaml").is_file():
        raise ValueError("pre-create project LIBERO config; interactive home configuration is prohibited")
    os.environ["LIBERO_CONFIG_PATH"] = str(args.libero_config.resolve())
    common.configure_cache(args.cache_directory, args.checkpoint)
    import numpy as np
    import torch
    from transformers import AutoProcessor
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    if torch.cuda.device_count() != 1:
        raise RuntimeError("G1-F development evaluation requires one allocated visible GPU")
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    before = verify_checkpoint_directory(args.checkpoint, asset)
    components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
    processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
    unchanged()
    policies = {}
    for method in methods:
        if method in ("dense", "uniform128"):
            policies[method] = libero_runtime.OpenVLARolloutPolicy(components, processor, stats_key=args.stats_key, method=method)
        else:
            selector = loaded[method[-1]]
            selector.estimator.to(device)
            policies[method] = future_runtime.FutureRolloutPolicy(components, processor, selector, stats_key=args.stats_key)
    from libero.libero import benchmark, get_libero_path
    from libero.libero.envs import OffScreenRenderEnv
    import libero.libero as installed_libero
    if args.libero_source.resolve() not in Path(installed_libero.__file__).resolve().parents:
        raise ValueError("installed LIBERO lies outside the verified source checkout")
    suite = benchmark.get_benchmark_dict()[panel["suite"]](task_order_index=0)
    for state in panel["states"]:
        if suite.get_task(state["task_id"]).name != state["task_name"] or catalog[state["task_id"]]["task_name"] != state["task_name"]:
            raise ValueError("runtime task ID differs from the frozen G1-F development panel")
    runtime = common.environment_provenance(torch, device)
    config = {"schema": future_runtime.FUTURE_SCHEMA, "stage": "G1-F_Long_development" if long else "G1-F_development",
        "panel_signature": panel["panel_signature"], "pair_id": loaded["A"].provenance["pair_id"],
        "selectors": {arm: dict(selector.provenance) for arm, selector in loaded.items()},
        "watched_artifacts": watched, "window_content_signature": windows["content_signature"],
        "base_model_revision": asset.revision, "source_verification": source_verification,
        "source_hashes": {**sources, **{p.relative_to(ROOT).as_posix(): file_sha256(p) for p in
            (Path(__file__), Path(future_runtime.__file__), Path(future_trials.__file__), ROOT / "scripts/eval_libero.py")}},
        "input_version": libero_runtime.INPUTS_VERSION, "action_version": libero_runtime.ACTION_VERSION,
        "packing_version": PACKING_VERSION, "environment_seed": panel["environment_seed"], "runtime_seed": args.seed,
        "methods": list(methods), "wait_steps": 10, "max_steps": future_trials.future_trial_horizon(panel), "action_chunk": 8,
        "policy_watchdog_seconds": args.policy_watchdog_seconds, "stats_key": args.stats_key, "test_opened": False,
        "runtime": {key: value for key, value in runtime.items() if key != "slurm_job_id"}}
    if long:
        config.update(suite=args.suite, input_acceptance_sha256=expected["input_acceptance_sha256"])
        for relative in ("src/cti_vla/data/long_initial_states.py", "src/cti_vla/data/long_future_windows.py"):
            config["source_hashes"][relative] = file_sha256(ROOT / relative)
    if dense_reference is not None:
        from cti_vla.evaluation.future_dense_reuse import require_dense_compatibility
        config.update(training_seed=common_config["seed"], dense_reference=dense_reference)
        if budget == 32:
            config.update(visual_tokens=64, per_camera_budgets=[32, 32],
                budget_reuse_registration_sha256=file_sha256(args.budget_reuse_registration))
            config["source_hashes"]["src/cti_vla/evaluation/future_budget_reuse.py"] = file_sha256(ROOT / "src/cti_vla/evaluation/future_budget_reuse.py")
        else:
            config["engineering_reuse_registration_sha256"] = file_sha256(args.engineering_reuse_registration)
        config["source_hashes"]["src/cti_vla/evaluation/future_dense_reuse.py"] = file_sha256(ROOT / "src/cti_vla/evaluation/future_dense_reuse.py")
        require_dense_compatibility(dense_reference, panel, config)
    signature = json_signature(config)
    write_frozen_json(args.output_directory / "config.json", config)
    write_frozen_json(args.output_directory / "panel.json", panel)
    ledger = libero_runtime.TrialLedger(args.output_directory / "trials.jsonl", run_signature=signature)
    provenance = {**config, "run_signature": signature, "checkpoint": asdict(before), "runtime": runtime}
    ledger.append({"event": "invocation", "slurm_job_id": runtime["slurm_job_id"],
        "created_utc": datetime.now(timezone.utc).isoformat(), "recovered_tail": ledger.recovered_tail})
    def reseed():
        random.seed(args.seed)
        np.random.seed(args.seed)
        torch.manual_seed(args.seed)
    def create_environment(state):
        task = suite.get_task(state["task_id"])
        env = OffScreenRenderEnv(bddl_file_name=str(Path(get_libero_path("bddl_files")) / task.problem_folder / task.bddl_file),
            camera_heights=256, camera_widths=256)
        env.seed(panel["environment_seed"])
        return env, task.language
    def report(checkpoint_unchanged=None):
        result = future_trials.summarize_future_trials(panel, methods, ledger, provenance=provenance,
            checkpoint_unchanged=checkpoint_unchanged, dense_reference=dense_reference)
        atomic_json(args.output_directory / "closed_loop_report.json", result)
        return result
    def on_result(row):
        report()
        print(json.dumps({"trial_id": row["trial_id"], "status": row["status"], "success": row["success"]}), flush=True)
    try:
        future_trials.evaluate_future_trials(panel, policies, ledger, create_environment, reseed=reseed,
            policy_watchdog_seconds=args.policy_watchdog_seconds, stop_after=args.stop_after, on_result=on_result,
            dense_reference=dense_reference)
        after = verify_checkpoint_directory(args.checkpoint, asset)
        unchanged()
        if before != after:
            raise RuntimeError("immutable VLA checkpoint changed during G1-F evaluation")
    except BaseException:
        report()
        raise
    return report(checkpoint_unchanged=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    states = ROOT / "configs/manifests/spatial_initial_states_v1"
    parser.add_argument("--suite", choices=("libero_spatial", "libero_10"), default="libero_spatial")
    parser.add_argument("--panel", type=Path, help="Long only: explicit frozen development_panel_30.json")
    parser.add_argument("--development-states", type=Path, default=states / "init_states_development.json")
    parser.add_argument("--g0-panel", type=Path, default=states / "g0_development_15.json")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--window-manifest", type=Path)
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--asset-manifest", type=Path)
    parser.add_argument("--official-source", type=Path, default=ROOT / "external/openvla-oft")
    parser.add_argument("--libero-source", type=Path, default=ROOT / "external/LIBERO")
    parser.add_argument("--libero-config", type=Path, default=ROOT / "configs/libero_runtime")
    for name in ("f01-report", "checkpoint-a", "checkpoint-b", "receipt-a", "receipt-b", "checkpoint", "cache-directory", "output-directory"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--input-acceptance-report", type=Path, help="Required Long frame-chain parity receipt; never Spatial G0")
    parser.add_argument("--dense-reference", type=Path, help="New Long training: immutable seed17 closed_loop directory")
    parser.add_argument("--engineering-reuse-registration", type=Path, help="Explicit parent F00/F01/cache evidence contract for new training seeds")
    parser.add_argument("--budget-reuse-registration", type=Path, help="New64 budget: parent F00/cache only; requires new64 F01")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--controls", nargs="*", choices=("dense", "uniform128"))
    parser.add_argument("--stats-key")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--policy-watchdog-seconds", type=float, default=60.)
    parser.add_argument("--stop-after", type=int)
    parser.add_argument("--prepare-only", action="store_true")
    print(json.dumps(run(parser.parse_args()), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

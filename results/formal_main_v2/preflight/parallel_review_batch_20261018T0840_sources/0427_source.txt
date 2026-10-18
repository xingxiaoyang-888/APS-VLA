"""Collect formal dev observations, or run separate full/components L40 timing."""
from __future__ import annotations

import argparse
from contextlib import contextmanager, nullcontext
from dataclasses import asdict
import gc
import json
import os
from pathlib import Path
import random
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def uncontended_device():
    output = subprocess.run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=10, check=True).stdout
    processes = [(v[0].strip(), int(v[1].strip())) for line in output.splitlines()
        if len(v := line.split(",")) == 2 and v[1].strip().isdigit()]
    own = {uuid for uuid, pid in processes if pid == os.getpid()}
    if len(own) != 1:
        raise RuntimeError("cannot attest this process's unique allocated GPU UUID")
    uuid = next(iter(own))
    if any(pid != os.getpid() and gpu == uuid for gpu, pid in processes):
        raise RuntimeError("competing compute process detected; retain this attempt, do not filter or retry")
    return dict(gpu_uuid=uuid, own_pid=os.getpid(), other_compute_processes=0)


def load_execution(args, registration, manifest):
    """Same strict formal acceptance/selector identity validation as rollouts."""
    from cti_vla.data.identity import file_sha256
    from cti_vla.data.formal_windows import load_formal_protocol, load_formal_windows
    from cti_vla.evaluation import formal_runtime, formal_trials, libero_runtime
    from cti_vla.evaluation.formal_acceptance import (select_formal_acceptance_windows,
        require_formal_input_acceptance, require_formal_acceptance, verify_formal_operator_journal)
    from cti_vla.evaluation.future_input_acceptance import verify_input_acceptance_journal
    from cti_vla.evaluation.future_profiling import load_script
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest
    from cti_vla.evaluation.teacher_diagnostics import json_signature
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    from cti_vla.training.formal_future import formal_source_hashes, validate_formal_training_config
    from cti_vla.training.formal_resume_acceptance import require_formal_resume_acceptance, verify_resume_journal
    evaluate = load_script(ROOT, "eval_formal_selector_libero")
    project, suite = args.project_root.resolve(), manifest["suite"]
    suite_config = registration["suites"][suite]
    sources = formal_source_hashes(ROOT)
    asset = load_checkpoint_manifest(args.asset_manifest)
    if (file_sha256(args.asset_manifest) != suite_config["model_manifest_sha256"]
            or asset.revision != suite_config["model_revision"]
            or args.checkpoint.resolve() != Path(suite_config["model_root_server"]).resolve()):
        raise ValueError("profiling base differs from registered matching suite checkpoint")
    protocol = load_formal_protocol(args.protocol, project_root=project)
    windows = load_formal_windows(args.windows, protocol)
    if (windows["suite"] != suite or args.windows.resolve() != (project / suite_config["windows"]).resolve()
            or args.protocol.resolve() != (project / suite_config["protocol"]).resolve()
            or args.development_panel.resolve() != (project / suite_config["initial_states_root"] / "development.json").resolve()):
        raise ValueError("profiling data identities differ from registered suite")
    fixed = select_formal_acceptance_windows(windows, protocol)
    f00 = read(args.input_acceptance)
    f00_sha = file_sha256(args.input_acceptance)
    config = dict(suite=suite, model_revision=asset.revision, stats_key=formal_runtime.FORMAL_SUITES[suite]["stats_key"])
    require_formal_input_acceptance(f00, config=config, window_manifest_sha256=file_sha256(args.windows),
        data_protocol_sha256=file_sha256(args.protocol), asset_manifest_sha256=file_sha256(args.asset_manifest),
        source_files=sources, selected_windows=fixed)
    input_journal = args.input_acceptance.parent / "input_calls.jsonl"
    verify_input_acceptance_journal(input_journal, f00)
    primary = next(p for p in registration["pairs"]
        if p["suite"] == suite and p["visual_tokens"] == 128 and p["seed"] == 17)
    primary_config = project / primary["path"]
    if file_sha256(primary_config) != primary["sha256"]:
        raise ValueError("formal F03 primary pair config changed")
    resume_report = args.input_acceptance.parent / "resume_acceptance.json"
    resume_journal = args.input_acceptance.parent / "f03_calls.jsonl"
    f03 = read(resume_report)
    require_formal_resume_acceptance(f03, config=read(primary_config), window_manifest_sha256=file_sha256(args.windows),
        input_acceptance_sha256=f00_sha, source_files=sources, selected_windows=fixed[:2],
        frozen_model_sha256=f00["frozen_model_sha256"])
    verify_resume_journal(resume_journal, f03)
    watched_paths = [args.registration, args.execution_manifest, args.asset_manifest, args.protocol,
        args.windows, args.input_acceptance, args.development_panel, input_journal,
        primary_config, resume_report, resume_journal,
        Path(__file__), ROOT / "scripts/eval_libero.py", ROOT / "src/cti_vla/evaluation/formal_profiling.py"]
    if args.global_freeze:
        watched_paths.append(args.global_freeze)
    if args.panel:
        watched_paths.append(args.panel)
    loaded = {}
    pairs = {(p["suite"], p["visual_tokens"], p["seed"]): p for p in registration["pairs"]}
    for row in manifest["methods"]:
        identity = row["identity"]
        mid = identity["method_id"]
        if identity["method"] in ("dense", "uniform"):
            actual = formal_trials.baseline_instance_identity(suite=suite, method=identity["method"],
                visual_tokens=identity["visual_tokens"], model_revision=asset.revision,
                frozen_model_sha256=f00["frozen_model_sha256"], source_files=sources, input_acceptance_sha256=f00_sha)
        else:
            paths = {k: evaluate.resolve_project_path(project, row[k], checkpoint=k == "checkpoint")
                for k in ("checkpoint", "receipt", "pair_config", "f01_report")}
            watched_paths.extend(paths.values())
            pair, receipt, f01 = (read(paths[k]) for k in ("pair_config", "receipt", "f01_report"))
            validate_formal_training_config(pair)
            registered = pairs[(suite, identity["visual_tokens"], identity["training_seed"])]
            if (file_sha256(paths["pair_config"]) != registered["sha256"] or pair != receipt["pair_config"]
                    or paths["pair_config"] != (project / registered["path"]).resolve()
                    or paths["checkpoint"] != (Path(registered["checkpoint_root_server"]) / identity["method"] / "best.pt").resolve()):
                raise ValueError("profiling selected checkpoint/config differs from the registered formal training run")
            require_formal_acceptance(f01, config=pair, window_manifest_sha256=file_sha256(args.windows),
                input_acceptance_sha256=f00_sha, source_files=sources, selected_windows=fixed)
            if f01["frozen_model_sha256"] != f00["frozen_model_sha256"]:
                raise ValueError("formal F00/F01 used different frozen model bytes")
            operator_journal = paths["f01_report"].parent / "operator_calls.jsonl"
            verify_formal_operator_journal(operator_journal, f01)
            watched_paths.append(operator_journal)
            expected = dict(suite=suite, model_revision=asset.revision, stats_key=config["stats_key"],
                input_version=libero_runtime.INPUTS_VERSION, packing_version=PACKING_VERSION,
                visual_tokens=identity["visual_tokens"], per_camera_budgets=[identity["visual_tokens"] // 2] * 2,
                window_manifest_sha256=file_sha256(args.windows), input_acceptance_sha256=f00_sha,
                f01_report_sha256=file_sha256(paths["f01_report"]), frozen_model_sha256=f00["frozen_model_sha256"],
                data_protocol_sha256=file_sha256(args.protocol), selection_protocol_sha256=json_signature(pair["selection"]))
            loaded[mid] = formal_runtime.load_formal_selector_checkpoint(paths["checkpoint"], receipt,
                expected_versions=expected, expected_source_hashes=sources, device="cpu")
            actual = formal_trials.selector_instance_identity(loaded[mid].provenance)
        if actual != identity:
            raise ValueError("formal profiling differs from verified success-evaluation identity: " + mid)
    if loaded:
        for budget in formal_runtime.FORMAL_BUDGETS:
            for seed in formal_runtime.FORMAL_SEEDS:
                formal_runtime.validate_formal_pair(loaded[f"A{budget}_seed{seed}"], loaded[f"B{budget}_seed{seed}"])
    watched = {str(p.resolve()): file_sha256(p) for p in watched_paths}
    def unchanged():
        if sources != formal_source_hashes(ROOT) or any(file_sha256(p) != sha for p, sha in watched.items()):
            raise ValueError("formal profiling immutable sources/configuration/checkpoints changed")
    return asset, f00, sources, loaded, watched, unchanged


def load_base(args, asset, f00):
    from cti_vla.evaluation.checkpoint_manifest import verify_checkpoint_directory
    from cti_vla.evaluation.formal_acceptance import module_parameter_sha256
    from cti_vla.evaluation.future_profiling import load_script
    common = load_script(ROOT, "eval_libero")
    common.configure_cache(args.cache_directory, args.checkpoint)
    import torch
    from transformers import AutoProcessor
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    if torch.cuda.device_count() != 1 or torch.cuda.get_device_name(0) != "NVIDIA L40":
        raise RuntimeError("formal profiling requires exactly one allocated NVIDIA L40")
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    torch.manual_seed(17)
    torch.empty(0, device=device)
    allocation = uncontended_device()
    runtime = {k: v for k, v in common.environment_provenance(torch, device).items()
        if k not in ("slurm_job_id", "cpu")}
    before = verify_checkpoint_directory(args.checkpoint, asset)
    began = time.perf_counter()
    components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
    if module_parameter_sha256(components) != f00["frozen_model_sha256"]:
        raise ValueError("formal loaded model parameters differ from accepted/evaluated base")
    processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
    torch.cuda.synchronize(device)
    return components, processor, before, runtime, allocation, time.perf_counter() - began, device


def collect(args, registration, manifest, development, identity, components, processor, unchanged, verify_base):
    import numpy as np
    import torch
    from cti_vla.data.initial_states import official_task_catalog
    from cti_vla.data.formal_windows import LIBERO_REVISION
    from cti_vla.evaluation import formal_runtime, libero_runtime
    from cti_vla.evaluation.future_profiling import load_script
    from cti_vla.evaluation.formal_profiling import (CaptureControlObservations, fixed_profile_states,
        save_dense_collection, write_profile_panel, load_profile_panel)
    from cti_vla.evaluation.teacher_diagnostics import json_signature, atomic_json
    evaluate = load_script(ROOT, "eval_formal_selector_libero")
    verified = {"openvla_oft": evaluate.verify_checkout(args.oft_source, libero_runtime.OFT_COMMIT),
        "libero": evaluate.verify_checkout(args.libero_source, LIBERO_REVISION)}
    catalog, mapping = official_task_catalog(args.libero_source, suite=manifest["suite"])
    if any(development["source"].get(k) != v for k, v in mapping.items()):
        raise ValueError("collection task mapping differs from the registered development panel")
    if not (args.libero_config / "config.yaml").is_file():
        raise ValueError("formal project LIBERO configuration must exist before collection")
    os.environ["LIBERO_CONFIG_PATH"] = str(args.libero_config.resolve())
    from libero.libero import benchmark, get_libero_path
    from libero.libero.envs import OffScreenRenderEnv
    import libero.libero as installed
    if args.libero_source.resolve() not in Path(installed.__file__).resolve().parents:
        raise ValueError("collection imported LIBERO outside the pinned official checkout")
    suite = benchmark.get_benchmark_dict()[manifest["suite"]](task_order_index=0)
    states = fixed_profile_states(development)
    if any(suite.get_task(r["task_id"]).name != r["task_name"] or catalog[r["task_id"]]["task_name"] != r["task_name"] for r in states):
        raise ValueError("collection simulator task order differs from fixed development identities")
    provenance = {**identity, "source_verification": verified, "checkpoint_unchanged": True}
    # The completed panel carries True only after all final immutable checks below.
    policy = formal_runtime.FormalRolloutPolicy(components, processor, suite=manifest["suite"],
        method="dense", total_tokens=512, record_selection=False)
    ledger = libero_runtime.TrialLedger(args.output / "collection_trials.jsonl", run_signature=json_signature(identity))
    episodes = []
    for state in states:
        ledger.append({"event": "start", "trial_id": state["trial_id"], "method": "dense"})
        env = None
        try:
            random.seed(17)
            np.random.seed(17)
            torch.manual_seed(17)
            task = suite.get_task(state["task_id"])
            env = OffScreenRenderEnv(bddl_file_name=str(Path(get_libero_path("bddl_files")) / task.problem_folder / task.bddl_file),
                camera_heights=256, camera_widths=256)
            env.seed(0)
            capture = CaptureControlObservations(env)
            result = libero_runtime.run_episode(capture, policy, task.language, state["initial_state"], wait_steps=10,
                max_steps=formal_runtime.FORMAL_SUITES[manifest["suite"]]["max_steps"], policy_watchdog_seconds=60.)
        finally:
            if env is not None:
                env.close()
        ledger.append({"event": "result", "trial_id": state["trial_id"], "method": "dense", **result})
        if result["status"] != "completed":
            raise RuntimeError("formal collection failed; retain it without substituting a task or state")
        unchanged()
        episodes.append(save_dense_collection(args.output / f"task{state['task_id']:02d}", state,
            task.language, result, capture.captured, provenance=provenance))
        del capture
        print(json.dumps({"task_id": state["task_id"], "actual_control_steps": result["control_steps"],
            "selected_observations": 3, "new_success_trials": False}), flush=True)
    verify_base()
    write_profile_panel(args.output, development, episodes, provenance=provenance, registration=registration)
    samples, panel = load_profile_panel(args.output / "panel.json", development=development,
        registration=registration, dense_identity=manifest["methods"][0]["identity"])
    calls = sum(r.get("policy_calls", 0) for r in ledger.events if r.get("event") == "result")
    return dict(status="completed_collection", observations=len(samples), panel=panel, policy_calls=calls,
        new_success_trials=False, test_opened=False,
        cost_scope="10 dense collection trajectories; all allocation time charged, excluded from success counts and latency samples")


def measure(args, registration, manifest, development, identity, components, processor, loaded, device, unchanged):
    from cti_vla.data.identity import file_sha256
    from cti_vla.evaluation.formal_runtime import FormalRolloutPolicy
    from cti_vla.evaluation.formal_profiling import (load_profile_panel, profile_formal_methods,
        verify_profile_journal, summarize_formal_profile)
    from cti_vla.evaluation.profiling import ProfileJournal, ProfileMethod, TorchClock, hardware_telemetry, read_profile_cost
    from cti_vla.evaluation.teacher_diagnostics import atomic_json
    samples, panel = load_profile_panel(args.panel, development=development, registration=registration,
        dense_identity=manifest["methods"][0]["identity"])
    if panel["provenance"]["runtime"] != identity["runtime"]:
        raise ValueError("profiling software/runtime differs from the fixed dense collection")
    def panel_unchanged():
        if any(file_sha256(args.panel.parent / path) != sha for path, sha in panel["artifact_sha256"].items()):
            raise ValueError("formal profiling raw observations or dense receipts changed")
    identity.update(panel=panel, panel_sha256=file_sha256(args.panel))
    factories = {}
    for row in manifest["methods"]:
        deployment = row["identity"]
        mid = deployment["method_id"]
        @contextmanager
        def factory(mid=mid, deployment=deployment):
            gc.collect()
            selector = loaded.get(mid)
            if selector is not None:
                selector.estimator.to(device)
            policy = FormalRolloutPolicy(components, processor, suite=manifest["suite"],
                method=deployment["method"], total_tokens=deployment["visual_tokens"], selector=selector, record_selection=False)
            def set_context(context):
                policy.stage_context = context or (lambda _: nullcontext())
                policy.component_timing = context is not None
            try:
                yield ProfileMethod(policy, dict(identity=deployment, cache_scope="none", instruction_cache_enabled=False,
                    future_head_deployed=False, precision="base_bfloat16_DIE_float32", attention="sdpa", batch_size=1), set_context)
            finally:
                if selector is not None:
                    selector.estimator.to("cpu")
                del policy
        factories[mid] = factory
    atomic_json(args.output / "config.json", identity)
    journal = ProfileJournal(args.output / "calls.jsonl", identity)
    telemetry = lambda: {**hardware_telemetry(), "uncontended_device": uncontended_device()}
    began = time.perf_counter()
    result = profile_formal_methods(samples, factories, pass_name=args.command, clock=TorchClock(device),
        emit=journal, telemetry=telemetry)
    unchanged()
    panel_unchanged()
    result.update(provenance=identity, checkpoint_unchanged=True,
        cost=read_profile_cost(args.output / "calls.jsonl"),
        wall_seconds_including_measurement_overhead=time.perf_counter() - began,
        execution_wall_seconds_including_model_loading=time.perf_counter() - args.execution_started,
        hardware_after=telemetry())
    verify_profile_journal(result, args.output / "calls.jsonl")
    atomic_json(args.output / "measurements.json", result)
    summary = summarize_formal_profile(result)
    summary.update(cost=result["cost"], checkpoint_unchanged=True, panel=panel,
        measurements_sha256=file_sha256(args.output / "measurements.json"),
        journal_sha256=file_sha256(args.output / "calls.jsonl"), config_sha256=file_sha256(args.output / "config.json"),
        execution_wall_seconds_including_model_loading=result["execution_wall_seconds_including_model_loading"])
    return summary


def run(args):
    from cti_vla.data.identity import file_sha256
    from cti_vla.data.formal_initial_states import load_formal_development_panel
    from cti_vla.evaluation.formal_profiling import (PROFILE_VERSION, PANEL_VERSION, validate_profile_manifest,
        fixed_profile_states, load_profile_panel)
    from cti_vla.evaluation.future_profiling import validate_new_output_paths
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
    registration, manifest = read(args.registration), read(args.execution_manifest)
    global_freeze = read(args.global_freeze) if args.global_freeze else None
    identifiers = validate_profile_manifest(manifest, registration, collect=args.command == "collect", global_freeze=global_freeze)
    development = load_formal_development_panel(args.development_panel)
    suite = manifest["suite"]
    if development["suite"] != suite:
        raise ValueError("profiling deployment and development suite differ")
    if args.command != "collect" and args.panel is None:
        raise ValueError("timing requires the frozen development raw panel")
    panel = None
    if args.command != "collect":
        _, panel = load_profile_panel(args.panel, development=development, registration=registration,
            dense_identity=manifest["methods"][0]["identity"])
    if args.prepare_only:
        return dict(status="prepared_only", command=args.command, suite=suite, methods=identifiers,
            fixed_state_ids=[r["trial_id"] for r in fixed_profile_states(development)], observations=30,
            planned_policy_calls=None if args.command == "collect" else 14300, panel=panel,
            gpu_calls=0, test_opened=False, weights_validated=False)
    if os.name == "nt" or not os.environ.get("SLURM_JOB_ID") or not args.uncontended_gpu:
        raise RuntimeError("real formal profiling requires a root-submitted Slurm allocation with an uncontended L40")
    for key in ("checkpoint", "cache_directory", "output", "protocol", "windows", "input_acceptance", "asset_manifest"):
        if getattr(args, key) is None:
            raise ValueError("real formal execution requires --" + key.replace("_", "-"))
    validate_new_output_paths(project_root=args.project_root, source_root=ROOT, output=args.output,
        cache=args.cache_directory, weight_roots=[args.checkpoint])
    args.output.mkdir(parents=True, exist_ok=False)
    args.execution_started = time.perf_counter()
    attempt = dict(version=PROFILE_VERSION, command=args.command, suite=suite, registration_sha256=json_signature(registration),
        execution_manifest_sha256=file_sha256(args.execution_manifest), slurm_job_id=os.environ["SLURM_JOB_ID"], test_opened=False)
    atomic_json(args.output / "attempt.json", attempt)
    try:
        asset, f00, sources, loaded, watched, unchanged = load_execution(args, registration, manifest)
        components, processor, before, runtime, allocation, loading, device = load_base(args, asset, f00)
        from cti_vla.evaluation.checkpoint_manifest import verify_checkpoint_directory
        from cti_vla.evaluation.formal_acceptance import module_parameter_sha256
        from cti_vla.evaluation.profiling import hardware_telemetry
        def verify_all():
            unchanged()
            if before != verify_checkpoint_directory(args.checkpoint, asset) or module_parameter_sha256(components) != f00["frozen_model_sha256"]:
                raise ValueError("formal base checkpoint/parameters changed")
        identity = {**attempt, "version": PANEL_VERSION if args.command == "collect" else PROFILE_VERSION,
            "source_files": sources, "watched_files": watched, "runtime": runtime, "allocation": allocation,
            "model_loading_seconds_excluded_from_calls": loading, "checkpoint": asdict(before),
            "dense_identity": manifest["methods"][0]["identity"], "manifest": manifest,
            "all_instances_share_one_loaded_base": True, "cache_scope": "none", "future_head_deployed": False,
            "hardware": hardware_telemetry(), "profiler_script_sha256": file_sha256(__file__),
            "profiler_module_sha256": file_sha256(ROOT / "src/cti_vla/evaluation/formal_profiling.py"),
            "compile": "disabled; native eager SDPA", "profiling_registration": registration["profiling"]}
        if args.global_freeze:
            identity["global_freeze_sha256"] = file_sha256(args.global_freeze)
        if args.command == "collect":
            atomic_json(args.output / "config.json", identity)
            summary = collect(args, registration, manifest, development, identity, components, processor, unchanged, verify_all)
            summary["execution_wall_seconds_including_model_loading"] = time.perf_counter() - args.execution_started
        else:
            # Expensive immutable model checks are outside every measured call.
            verify_all()
            summary = measure(args, registration, manifest, development, identity, components, processor, loaded, device, verify_all)
        atomic_json(args.output / "summary.json", summary)
        return {k: summary[k] for k in ("status", "test_opened", "cost", "observations", "policy_calls") if k in summary}
    except BaseException as exc:
        from cti_vla.evaluation.profiling import read_profile_cost
        journal = args.output / "calls.jsonl"
        atomic_json(args.output / "summary.json", dict(status="failed", command=args.command, test_opened=False,
            error=f"{type(exc).__name__}: {exc}", cost=read_profile_cost(journal) if journal.exists() else None,
            execution_wall_seconds_including_model_loading=time.perf_counter() - args.execution_started,
            cost_note="All Slurm allocated GPU seconds, including setup/failed attempts, require scheduler reconciliation; no automatic retry."))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("collect", "full", "components"))
    for name in ("registration", "execution-manifest", "development-panel"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("global-freeze", "panel", "protocol", "windows", "input-acceptance", "asset-manifest",
            "checkpoint", "cache-directory", "output"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--oft-source", type=Path, default=ROOT / "external/openvla-oft")
    parser.add_argument("--libero-source", type=Path, default=ROOT / "external/LIBERO")
    parser.add_argument("--libero-config", type=Path, default=ROOT / "configs/libero_runtime")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--uncontended-gpu", action="store_true")
    print(json.dumps(run(parser.parse_args()), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

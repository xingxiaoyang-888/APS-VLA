"""Formal paired rollouts: all suites/budgets; final requires global root release."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import random
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CAPACITY_ROOT = Path("/share/home/u15016/XXY_CVPR/CTI-VLA")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def resolve_project_path(project, value, *, checkpoint=False, capacity_root=CAPACITY_ROOT):
    project = Path(project).resolve()
    path = Path(value)
    path = (project / path).resolve() if not path.is_absolute() else path.resolve()
    capacity = (Path(capacity_root) / "checkpoints/formal_main_v2").resolve()
    if checkpoint and capacity in path.parents:
        return path
    if project != path and project not in path.parents:
        raise ValueError("formal execution artifact is outside the declared project")
    return path


@contextmanager
def exclusive_output(path):
    import fcntl
    path.mkdir(parents=True, exist_ok=True)
    with (path / ".evaluation.lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("another formal evaluation owns this output directory") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def verify_checkout(path, revision):
    head = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(path), "status", "--porcelain", "--untracked-files=no"], text=True).strip()
    if head != revision or dirty:
        raise ValueError("formal official source checkout is not its clean pinned revision")
    return {"revision": head, "tracked_clean": True}


def run(args):
    from cti_vla.evaluation.formal_trials import validate_execution_manifest, load_formal_panel
    from cti_vla.evaluation.teacher_diagnostics import json_signature
    from cti_vla.evaluation.future_profiling import validate_new_output_paths
    registration = read_json(args.registration)
    manifest = read_json(args.execution_manifest)
    registration_sha = json_signature(registration)
    identifiers = validate_execution_manifest(manifest, registration_sha256=registration_sha)
    split, suite = manifest["split"], manifest["suite"]
    panel = load_formal_panel(suite=suite, split=split, development_path=args.development_panel,
        final_registry_path=args.final_registry, sealed_final_path=args.sealed_final,
        release_path=args.release, release_file_sha256=args.release_sha256,
        matrix=manifest.get("global_freeze"), registration_sha256=registration_sha)
    if split == "final" and read_json(args.release) != manifest["release"]:
        raise ValueError("execution manifest and root final release file differ")
    if args.prepare_only:
        return {"schema": "formal_main_v2", "status": "prepared_only", "suite": suite, "split": split,
            "unique_initial_states": len(panel["states"]), "methods": identifiers,
            "expected_trials": len(panel["states"]) * len(identifiers), "gpu_calls": 0,
            "test_opened": split == "final", "weights_validated": False}
    if os.name == "nt" or not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("formal real evaluation runs only in a root-submitted server Slurm allocation")
    validate_new_output_paths(project_root=args.project_root, source_root=ROOT,
        output=args.output, cache=args.cache_directory, weight_roots=[args.checkpoint])
    with exclusive_output(args.output):
        return execute(args, manifest, panel, registration_sha)


def execute(args, manifest, panel, registration_sha):
    from cti_vla.data.identity import file_sha256
    from cti_vla.data.formal_windows import load_formal_protocol, load_formal_windows
    from cti_vla.data.initial_states import official_task_catalog
    from cti_vla.data.formal_windows import LIBERO_REVISION
    from cti_vla.data.experiment_protocol import write_frozen_json
    from cti_vla.evaluation import formal_runtime, formal_trials, libero_runtime
    from cti_vla.evaluation.formal_acceptance import (select_formal_acceptance_windows, require_formal_input_acceptance,
        require_formal_acceptance, module_parameter_sha256, verify_formal_operator_journal)
    from cti_vla.evaluation.future_input_acceptance import verify_input_acceptance_journal
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    from cti_vla.training.formal_future import formal_source_hashes, validate_formal_training_config
    from cti_vla.training.formal_resume_acceptance import require_formal_resume_acceptance, verify_resume_journal
    project = args.project_root.resolve()
    sources = formal_source_hashes(ROOT)
    registration = read_json(args.registration)
    suite_config = registration["suites"][manifest["suite"]]
    asset = load_checkpoint_manifest(args.asset_manifest)
    if (file_sha256(args.asset_manifest) != suite_config["model_manifest_sha256"]
            or asset.revision != suite_config["model_revision"]
            or args.checkpoint.resolve() != Path(suite_config["model_root_server"]).resolve()):
        raise ValueError("formal evaluation base differs from its registered suite checkpoint")
    protocol = load_formal_protocol(args.protocol, project_root=project)
    windows = load_formal_windows(args.windows, protocol)
    suite_name = manifest["suite"]
    if (windows["suite"] != suite_name or args.windows.resolve() != (project / suite_config["windows"]).resolve()
            or args.protocol.resolve() != (project / suite_config["protocol"]).resolve()):
        raise ValueError("formal evaluation/data suite mismatch")
    fixed = select_formal_acceptance_windows(windows, protocol)
    f00 = read_json(args.input_acceptance)
    config = dict(suite=suite_name, model_revision=asset.revision, stats_key=formal_runtime.FORMAL_SUITES[suite_name]["stats_key"])
    require_formal_input_acceptance(f00, config=config, window_manifest_sha256=file_sha256(args.windows),
        data_protocol_sha256=file_sha256(args.protocol), asset_manifest_sha256=file_sha256(args.asset_manifest),
        source_files=sources, selected_windows=fixed)
    input_journal = args.input_acceptance.parent / "input_calls.jsonl"
    verify_input_acceptance_journal(input_journal, f00)
    resume_path = args.input_acceptance.parent / "resume_acceptance.json"
    resume_journal = args.input_acceptance.parent / "f03_calls.jsonl"
    resume_report = read_json(resume_path)
    primary_registration = next(p for p in registration["pairs"] if p["suite"] == suite_name and p["visual_tokens"] == 128 and p["seed"] == 17)
    primary_path = (project / primary_registration["path"]).resolve()
    if file_sha256(primary_path) != primary_registration["sha256"]:
        raise ValueError("formal primary config used by F03 differs from registration")
    require_formal_resume_acceptance(resume_report, config=read_json(primary_path),
        window_manifest_sha256=file_sha256(args.windows), input_acceptance_sha256=file_sha256(args.input_acceptance),
        source_files=sources, selected_windows=fixed[:2], frozen_model_sha256=f00["frozen_model_sha256"])
    verify_resume_journal(resume_journal, resume_report)
    watched_paths = [args.execution_manifest, args.registration, args.asset_manifest, args.protocol, args.windows,
        args.input_acceptance, input_journal, resume_path, resume_journal, primary_path]
    watched_paths.extend([args.development_panel] if panel["split"] == "development" else [args.release, args.final_registry, args.sealed_final])
    policies, loaded = {}, {}
    registered_pairs = {(p["suite"], p["visual_tokens"], p["seed"]): p for p in registration["pairs"]}
    f00_sha = file_sha256(args.input_acceptance)
    for row in manifest["methods"]:
        identity = row["identity"]
        mid = identity["method_id"]
        if identity["method"] in ("dense", "uniform"):
            actual = formal_trials.baseline_instance_identity(suite=suite_name, method=identity["method"],
                visual_tokens=identity["visual_tokens"], model_revision=asset.revision,
                frozen_model_sha256=f00["frozen_model_sha256"], source_files=sources, input_acceptance_sha256=f00_sha)
        else:
            paths = {key: resolve_project_path(project, row[key], checkpoint=key == "checkpoint") for key in ("checkpoint", "receipt", "pair_config", "f01_report")}
            watched_paths.extend(paths.values())
            pair, receipt, f01 = (read_json(paths[key]) for key in ("pair_config", "receipt", "f01_report"))
            validate_formal_training_config(pair)
            registered = registered_pairs[(suite_name, identity["visual_tokens"], identity["training_seed"])]
            if (file_sha256(paths["pair_config"]) != registered["sha256"] or pair != receipt["pair_config"]
                    or paths["pair_config"] != (project / registered["path"]).resolve()
                    or paths["checkpoint"] != (Path(registered["checkpoint_root_server"]) / identity["method"] / "best.pt").resolve()):
                raise ValueError("formal checkpoint receipt differs from frozen pair config")
            require_formal_acceptance(f01, config=pair, window_manifest_sha256=file_sha256(args.windows),
                input_acceptance_sha256=f00_sha, source_files=sources, selected_windows=fixed)
            if f01["frozen_model_sha256"] != f00["frozen_model_sha256"]:
                raise ValueError("formal input/operator gates used different frozen VLA bytes")
            operator_journal = paths["f01_report"].parent / "operator_calls.jsonl"
            verify_formal_operator_journal(operator_journal, f01)
            watched_paths.append(operator_journal)
            expected = dict(suite=suite_name, model_revision=asset.revision, stats_key=config["stats_key"],
                input_version=libero_runtime.INPUTS_VERSION, packing_version=PACKING_VERSION,
                visual_tokens=identity["visual_tokens"], per_camera_budgets=[identity["visual_tokens"] // 2] * 2,
                window_manifest_sha256=file_sha256(args.windows), input_acceptance_sha256=f00_sha,
                f01_report_sha256=file_sha256(paths["f01_report"]), frozen_model_sha256=f00["frozen_model_sha256"],
                data_protocol_sha256=file_sha256(args.protocol), selection_protocol_sha256=json_signature(pair["selection"]))
            selected = formal_runtime.load_formal_selector_checkpoint(paths["checkpoint"], receipt,
                expected_versions=expected, expected_source_hashes=sources)
            loaded[mid] = selected
            actual = formal_trials.selector_instance_identity(selected.provenance)
        if identity != actual:
            raise ValueError("formal execution instance differs from verified deployment identity: " + mid)
    for budget in formal_runtime.FORMAL_BUDGETS:
        for seed in formal_runtime.FORMAL_SEEDS:
            a, b = (formal_trials.method_id(arm, budget, seed) for arm in ("A", "B"))
            if a in loaded and b in loaded:
                formal_runtime.validate_formal_pair(loaded[a], loaded[b])
    watched = {str(p.resolve()): file_sha256(p) for p in watched_paths}
    def unchanged():
        if sources != formal_source_hashes(ROOT) or any(file_sha256(path) != sha for path, sha in watched.items()):
            raise ValueError("formal evaluation evidence/checkpoint/source bytes changed")
    source_verification = {"openvla_oft": verify_checkout(args.oft_source, libero_runtime.OFT_COMMIT),
        "libero": verify_checkout(args.libero_source, LIBERO_REVISION)}
    catalog, mapping = official_task_catalog(args.libero_source, suite=suite_name)
    if (panel["source"].get("revision") != LIBERO_REVISION
            or any(panel["source"].get(key) != value for key, value in mapping.items())):
        raise ValueError("formal panel task mapping differs from pinned LIBERO")
    if not (args.libero_config / "config.yaml").is_file():
        raise ValueError("formal LIBERO project configuration must exist before evaluation")
    os.environ["LIBERO_CONFIG_PATH"] = str(args.libero_config.resolve())
    for p in (args.cache_directory, args.cache_directory / "hub", args.cache_directory / "modules"):
        p.mkdir(parents=True, exist_ok=True)
    os.environ.update(HF_HOME=str(args.cache_directory), HF_HUB_CACHE=str(args.cache_directory / "hub"),
        HF_MODULES_CACHE=str(args.cache_directory / "modules"), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    import numpy as np
    import torch
    from transformers import AutoProcessor
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    if torch.cuda.device_count() != 1:
        raise RuntimeError("formal rollouts require exactly one allocated visible GPU")
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    before = verify_checkpoint_directory(args.checkpoint, asset)
    components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
    if module_parameter_sha256(components) != f00["frozen_model_sha256"]:
        raise ValueError("formal loaded base parameters/buffers differ from F00 acceptance")
    processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
    for row in manifest["methods"]:
        identity = row["identity"]
        selected = loaded.get(identity["method_id"])
        if selected:
            selected.estimator.to(device)
        policies[identity["method_id"]] = formal_runtime.FormalRolloutPolicy(components, processor,
            suite=suite_name, method=identity["method"], total_tokens=identity["visual_tokens"], selector=selected)
    from libero.libero import benchmark, get_libero_path
    from libero.libero.envs import OffScreenRenderEnv
    import libero.libero as installed_libero
    if args.libero_source.resolve() not in Path(installed_libero.__file__).resolve().parents:
        raise ValueError("formal imported LIBERO lies outside its pinned checkout")
    suite = benchmark.get_benchmark_dict()[suite_name](task_order_index=0)
    if any(suite.get_task(r["task_id"]).name != r["task_name"] or catalog[r["task_id"]]["task_name"] != r["task_name"] for r in panel["states"]):
        raise ValueError("formal simulator task order differs from the registered panel")
    runtime = dict(torch=torch.__version__, python=platform.python_version(), gpu=torch.cuda.get_device_name(),
        cuda=torch.version.cuda, numpy=np.__version__, slurm_job_id=os.environ["SLURM_JOB_ID"])
    run_config = {"schema": formal_runtime.FORMAL_SCHEMA, "kind": "evaluation_run", "manifest": manifest,
        "registration_sha256": registration_sha, "panel_signature": json_signature(panel),
        "source_files": sources, "watched_files": watched, "source_verification": source_verification,
        "runtime": {k: v for k, v in runtime.items() if k != "slurm_job_id"},
        "policy_watchdog_seconds": args.policy_watchdog_seconds}
    signature = json_signature(run_config)
    write_frozen_json(args.output / "config.json", run_config)
    write_frozen_json(args.output / "panel.json", panel)
    ledger = libero_runtime.TrialLedger(args.output / "trials.jsonl", run_signature=signature)
    provenance = {**run_config, "run_signature": signature, "checkpoint": asdict(before), "runtime": runtime}
    ledger.append(dict(event="invocation", slurm_job_id=runtime["slurm_job_id"], created_utc=datetime.now(timezone.utc).isoformat()))
    def reseed():
        random.seed(17)
        np.random.seed(17)
        torch.manual_seed(17)
    def factory(state):
        task = suite.get_task(state["task_id"])
        env = OffScreenRenderEnv(bddl_file_name=str(Path(get_libero_path("bddl_files")) / task.problem_folder / task.bddl_file),
            camera_heights=256, camera_widths=256)
        env.seed(0)
        return env, task.language
    def report(unchanged_flag=None):
        summary = formal_trials.summarize_formal_trials(panel, tuple(policies), ledger, provenance=provenance,
            checkpoint_unchanged=unchanged_flag)
        atomic_json(args.output / "closed_loop_report.json", summary)
        return summary
    def on_result(row):
        report()
        print(json.dumps({k: row[k] for k in ("trial_id", "status", "success")}), flush=True)
    try:
        unchanged()
        formal_trials.evaluate_formal_trials(panel, policies, ledger, factory, reseed=reseed,
            policy_watchdog_seconds=args.policy_watchdog_seconds, stop_after=args.stop_after, on_result=on_result)
        unchanged()
        if before != verify_checkpoint_directory(args.checkpoint, asset) or module_parameter_sha256(components) != f00["frozen_model_sha256"]:
            raise ValueError("formal base checkpoint changed during evaluation")
    except BaseException:
        report()
        raise
    return report(True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("execution-manifest", "registration", "protocol", "windows", "input-acceptance", "asset-manifest", "checkpoint",
            "oft-source", "libero-source", "libero-config", "cache-directory", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("development-panel", "final-registry", "sealed-final", "release"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--release-sha256")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--stop-after", type=int)
    parser.add_argument("--policy-watchdog-seconds", type=float, default=60.)
    parser.add_argument("--prepare-only", action="store_true")
    print(json.dumps(run(parser.parse_args()), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

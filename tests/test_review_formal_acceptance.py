"""Strict synthetic report/journal review. No GPU, real review, weights or sealed values."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

from test_data_formal_windows import project as data_project, freeze
from cti_vla.data import formal_windows
from cti_vla.evaluation import formal_acceptance as gates, libero_runtime
from cti_vla.models.abstraction.packing import PACKING_VERSION
from cti_vla.training import formal_future as formal, formal_resume_acceptance as resume

REPO = Path(__file__).resolve().parents[1]


def tool():
    spec = importlib.util.spec_from_file_location("formal_review_test", REPO / "scripts/review_formal_acceptance.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return path


def journal(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def synthetic_resume(pair, windows, sources, window_sha, input_sha, frozen, path):
    """Create only non-weight synthetic evidence matching the exact real schema."""
    spec = formal.FormalTrainingSpec(17, 64)
    context = dict(job_id="101", probe_version=resume.PROBE_VERSION, suite=pair["suite"])
    rows = []
    def event(name, **fields):
        rows.append(dict(context, event=name, **fields))
    ids = [row["window_id"] for row in windows]
    event("probe_start", execution="real_frozen_openvla_slurm", selected_windows=windows,
        frozen_model_sha256=frozen, pair_config_sha256=formal.json_signature(pair), source_sha256=formal.json_signature(sources),
        window_manifest_sha256=window_sha, input_acceptance_sha256=input_sha, planned_updates=5000, effective_batch=8, sample_order=ids * 8)
    arms = {}
    for arm in ("A", "B"):
        comparisons = {name: dict(equal=True, differences=[], reference_sha256="d" * 64, resumed_sha256="d" * 64)
                       for name in ("scorer", "head", "optimizer", "rng", "rng_probe")}
        checks = {name: True for name in resume.CHECKS}
        paths = {name: "/share/project/engineering/" + arm + "/" + name + ".pt"
                 for name in ("step1", "continuous_step2", "resumed_step2")}
        event("arm_start", arm=arm)
        def step(branch, update):
            fields = dict(arm=arm, branch=branch, update=update)
            event("step_start", **fields, window_ids=ids * 4, next_sample_cursor=(update - 1) * 8, alpha=spec.alpha(update))
            for index, window in enumerate(ids * 4):
                for name in ("sample_start", "sample_end"):
                    event(name, **fields, micro_batch_index=index, window_id=window)
            event("step_end", **fields, next_sample_cursor=update * 8, forward_backward_samples=8, grad_norm=.5)
        def checkpoint(label):
            event("save_start", arm=arm, label=label, checkpoint=paths[label])
            event("save_end", arm=arm, label=label, checkpoint=paths[label], checkpoint_sha256="e" * 64, state_sha256="f" * 64)
        step("continuous", 1)
        checkpoint("step1")
        event("rng_probe", arm=arm, branch="continuous", value_sha256="d" * 64)
        step("continuous", 2)
        checkpoint("continuous_step2")
        event("restore_start", arm=arm, checkpoint=paths["step1"], checkpoint_sha256="e" * 64)
        event("restore_end", arm=arm, state_sha256="f" * 64, next_sample_cursor=8, next_update=2, next_alpha=spec.alpha(2))
        event("rng_probe", arm=arm, branch="resumed", value_sha256="d" * 64)
        step("resumed", 2)
        checkpoint("resumed_step2")
        event("compare", arm=arm, checks=checks, component_hashes={name: {key: value[key] for key in ("reference_sha256", "resumed_sha256")}
                                                                 for name, value in comparisons.items()})
        event("arm_end", arm=arm, status="passed")
        arms[arm] = dict(arm=arm, checks=checks, comparisons=comparisons, initial_scorer_sha256="1" * 64,
            sample_order_sha256=formal.json_signature(ids * 8), planned_updates=5000, completed_probe_updates=2,
            next_sample_cursor=16, forward_backward_samples_including_replayed_step=24,
            step1_checkpoint=paths["step1"], step1_checkpoint_sha256="e" * 64,
            continuous_step2_checkpoint=paths["continuous_step2"], continuous_step2_sha256="e" * 64,
            resumed_step2_checkpoint=paths["resumed_step2"], resumed_step2_sha256="e" * 64)
    event("probe_end", status="passed", actual_forward_backward_samples=48, matched_ab_initialization=True)
    journal(path, rows)
    return dict(schema="formal_main_v2", kind="resume_acceptance", probe_version=resume.PROBE_VERSION,
        status="passed", execution="real_frozen_openvla_slurm", suite=pair["suite"], model_revision=pair["model_revision"],
        stats_key=pair["stats_key"], accepted_pair_config=pair, accepted_pair_id=formal.json_signature(pair),
        window_manifest_sha256=window_sha, input_acceptance_sha256=input_sha, source_files=sources, frozen_model_sha256=frozen,
        selected_windows=windows, planned_updates=5000, validation_updates=spec.validation_updates, selection_metric=formal.FORMAL_METRIC,
        selection_tie_break="earliest_update", alpha_first=2., alpha_last=.1, alpha_probe_updates=[spec.alpha(1), spec.alpha(2)],
        effective_batch=8, matched_ab_initialization=True, formal_selector_produced=False, engineering_weights_reused_for_training=False,
        test_opened=False, actual_forward_backward_samples=48, training_numerics=formal.FORMAL_NUMERICS,
        job_id="101", arms=arms, journal_bytes=path.stat().st_size, journal_sha256=formal.file_sha256(path), synthetic_fixture=True)


@pytest.fixture
def setup(data_project, monkeypatch):
    m, root = tool(), data_project
    protocol, _, data_asset, _, _ = freeze(root)
    suite = "libero_object"
    windows = formal_windows.build_formal_windows(protocol)
    windows_path = save(protocol.path.with_name("windows.json"), windows)
    real_reg = json.loads((REPO / m.REGISTRATION).read_text(encoding="utf-8"))
    spec = copy.deepcopy(real_reg["suites"][suite])
    spec.update(data_manifest=data_asset.relative_to(root).as_posix(), data_manifest_sha256=m.sha(data_asset))
    model_path = root / spec["model_manifest"]
    model_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REPO / spec["model_manifest"], model_path)
    asset = json.loads(model_path.read_text())
    pairs, configs = [], {}
    for budget in m.BUDGETS:
        relative = f"configs/experiments/formal_main_v2/{suite}_k{budget}_seed17.json"
        pair = json.loads((REPO / relative).read_text(encoding="utf-8"))
        save(root / relative, pair)
        pairs.append(dict(suite=suite, visual_tokens=budget, seed=17, path=relative, sha256=m.sha(root / relative)))
        configs[budget] = pair
    save(root / m.REGISTRATION, dict(schema=m.ROUND, suites={suite: spec}, pairs=pairs))
    save(root / "src/frozen.py", {"synthetic_source": True})
    sources = {"src/frozen.py": m.sha(root / "src/frozen.py")}
    monkeypatch.setattr(formal, "formal_source_hashes", lambda project: {key: m.sha(Path(project) / key) for key in sources})
    source_files = {**sources, **{rel: m.sha(root / rel) for rel in [m.REGISTRATION, spec["model_manifest"], spec["data_manifest"], *[p["path"] for p in pairs]]}}
    source_root = str(m.P / "snapshots/formal_main_v2_run_synthetic")
    source_sha = hashlib.sha256(json.dumps(source_files, sort_keys=True).encode()).hexdigest()
    inventory = save(root / "results/formal_main_v2/source/synthetic.json", dict(schema=m.ROUND, source_root_server=source_root,
        source_sha256=source_sha, files=source_files, commit="not-the-current-head"))
    relative = f"results/formal_main_v2/{suite}/acceptance/attempt01"
    base = root / relative
    base.mkdir(parents=True)
    job = dict(job_id="101", name="cti-formal", suite=suite, experiment=m.ROUND, mode="acceptance", status="COMPLETED",
        exit_code="0:0", stage_key=suite + "_acceptance", source_root=source_root, source_sha256=source_sha,
        run_root=str(m.P / relative), invocation="results/formal_main_v2/invocations/test.json", elapsed_seconds=100)
    argv = ["--suite", suite, "--configs", *[source_root + "/" + p["path"] for p in pairs],
        "--protocol", str(m.P / spec["protocol"]), "--windows", str(m.P / spec["windows"]),
        "--checkpoint", spec["model_root_server"], "--asset-manifest", source_root + "/" + spec["model_manifest"],
        "--data-directory", spec["data_root_server"], "--cache-directory", str(m.P / (".local/formal-hf-" + suite)),
        "--feature-cache", spec["cache_root_server"], "--oft-source", str(m.P / "external/openvla-oft"),
        "--project-root", str(m.P), "--output", job["run_root"]]
    watched = {str(m.P / spec["protocol"]): m.sha(protocol.path), str(m.P / spec["windows"]): m.sha(windows_path),
        source_root + "/" + spec["model_manifest"]: m.sha(model_path), **{source_root + "/" + p["path"]: p["sha256"] for p in pairs}}
    save(root / job["invocation"], dict(schema=m.ROUND, stage="acceptance", stage_key=job["stage_key"], suite=suite,
        source_root=source_root, source_sha256=source_sha, entrypoint="scripts/verify_formal_acceptance.py", argv=argv,
        watched_files=watched, registration_sha256=m.sha(root / m.REGISTRATION), segment_end=None))
    job["invocation_sha256"] = m.sha(root / job["invocation"])
    save(root / m.STATE, dict(registered_jobs=[job]))
    save(root / "results/formal_main_v2/job_receipts/101.json", dict(schema=m.ROUND, job_id="101", stage="acceptance",
        stage_key=job["stage_key"], invocation_sha256=job["invocation_sha256"], source_sha256=source_sha, exit_code=0, wall_seconds=99.))
    for suffix in ("out", "err"):
        save(root / f"results/slurm/cti-formal_101.{suffix}", {"synthetic_log": True})
    fixed = gates.select_formal_acceptance_windows(windows, protocol)
    calls = []
    for window in fixed:
        for kind in ("official_dense", "shared_dense"):
            row = dict(call_id=len(calls) // 2, window_id=window["window_id"], kind=kind, job_id="101")
            calls.extend([dict(row, event="start"), dict(row, event="complete", seconds=.01)])
    journal(base / "input_calls.jsonl", calls)
    frozen = "c" * 64
    f00 = dict(schema=m.ROUND, kind="input_acceptance", status="passed", execution="real_frozen_openvla_slurm", suite=suite,
        stats_key=configs[128]["stats_key"], model_revision=spec["model_revision"], window_manifest_sha256=m.sha(windows_path),
        data_protocol_sha256=m.sha(protocol.path), asset_manifest_sha256=m.sha(model_path), source_files=sources,
        input_version=libero_runtime.INPUTS_VERSION, action_version=libero_runtime.ACTION_VERSION, packing_version=PACKING_VERSION,
        checkpoint_unchanged=True, test_opened=False, policy_sample_forwards=6, vision_forwards=6, policy_attempts=6,
        frozen_model_sha256=frozen, observations=[dict(window=w, **{flag: True for flag in gates.INPUT_FLAGS},
            proprio_max_abs_error=0., dense_max_abs_error=0., demonstration_inverse_max_abs_error=0.) for w in fixed],
        checkpoint=dict(repository=asset["repository"], revision=asset["revision"], file_count=len(asset["files"]),
            total_bytes=sum(row["size"] for row in asset["files"])), official_source_revision=libero_runtime.OFT_COMMIT,
        job_id="101", calls_jsonl_sha256=m.sha(base / "input_calls.jsonl"), synthetic_fixture=True)
    save(base / "input_acceptance.json", f00)
    f00_sha = m.sha(base / "input_acceptance.json")
    operators = []
    for budget in m.BUDGETS:
        for window in fixed:
            for kind in gates.OPERATOR_PROBES:
                row = dict(call_id=len(operators) // 2, window_id=window["window_id"], kind=kind, job_id="101", visual_tokens=budget)
                operators.extend([dict(row, event="start"), dict(row, event="complete", seconds=.01)])
        journal(base / "operator_calls.jsonl", operators)
        f01 = dict(schema=m.ROUND, kind="operator_acceptance", status="passed", execution="real_frozen_openvla_slurm",
            suite=suite, stats_key=configs[budget]["stats_key"], model_revision=spec["model_revision"], visual_tokens=budget,
            per_camera_budgets=[budget // 2] * 2, accepted_pair_config=configs[budget], accepted_pair_id=formal.json_signature(configs[budget]),
            window_manifest_sha256=m.sha(windows_path), input_acceptance_sha256=f00_sha, source_files=sources,
            input_version=libero_runtime.INPUTS_VERSION, packing_version=PACKING_VERSION, checkpoint_unchanged=True, test_opened=False,
            frozen_model_sha256=frozen, job_id="101", observations=[dict(window_id=w["window_id"], task_id=w["task_id"],
                checks={flag: True for flag in gates.OPERATOR_FLAGS}, action_gradient_norm=.1, future_gradient_norm=.1,
                future_head_gradient_norm=.1, dense_max_abs=0., hard_max_abs=0., deployment_max_abs=0.,
                soft_gate_mass_per_camera=[budget / 2] * 2) for w in fixed], operator_probes_completed=len(operators) // 2,
            operator_journal_prefix_bytes=(base / "operator_calls.jsonl").stat().st_size,
            operator_journal_prefix_sha256=m.sha(base / "operator_calls.jsonl"), synthetic_fixture=True)
        save(base / f"f01_k{budget}.json", f01)
    save(base / "resume_acceptance.json", synthetic_resume(configs[128], fixed[:2], sources, m.sha(windows_path), f00_sha, frozen, base / "f03_calls.jsonl"))
    complete = dict(schema=m.ROUND, status="passed", suite=suite, job_id="101", test_opened=False, source_files=sources,
        frozen_model_sha256=frozen, checkpoint_unchanged=True, input_acceptance_sha256=f00_sha, input_calls=6, operator_probes=63,
        resume_acceptance_passed=True, synthetic_fixture=True)
    fixture = SimpleNamespace(m=m, root=root, base=base, relative=relative, inventory=inventory, job=job, complete=complete,
                              pull=root / "results/formal_main_v2/pulls/synthetic/receipt.json")
    reseal(fixture)
    return fixture


def reseal(f, *, duplicate_budget=False):
    """Update transport hashes after deliberate semantic corruption, not its meaning."""
    m, root, base = f.m, f.root, f.base
    f.complete.update(operator_calls_sha256=m.sha(base / "operator_calls.jsonl"),
        resume_acceptance_sha256=m.sha(base / "resume_acceptance.json"), f03_calls_sha256=m.sha(base / "f03_calls.jsonl"),
        operator_acceptances=[dict(visual_tokens=k, path=f.job["run_root"] + f"/f01_k{k}.json", sha256=m.sha(base / f"f01_k{k}.json")) for k in m.BUDGETS])
    if duplicate_budget:
        f.complete["operator_acceptances"].append(copy.deepcopy(f.complete["operator_acceptances"][0]))
    save(base / "acceptance_complete.json", f.complete)
    files = [f.relative + "/" + name for name in m.NAMES] + ["results/formal_main_v2/job_receipts/101.json",
        "results/slurm/cti-formal_101.out", "results/slurm/cti-formal_101.err"]
    rows = [dict(relative=rel, path=str(m.P / rel), sha256=m.sha(root / rel), bytes=(root / rel).stat().st_size,
                 job_ids=["101"]) for rel in files]
    inv = dict(files=rows, missing=[], excluded=[])
    save(f.pull.parent / "inventory_before.json", inv)
    save(f.pull.parent / "inventory_after.json", inv)
    accounting = {"jobs": {"101": dict(status="COMPLETED", exit_code="0:0")}}
    save(f.pull, dict(schema=m.ROUND, kind="nonweight_pull", status="verified_nonweight_snapshot", final_evidence=True,
        weights_copied=False, sealed_initial_states_copied=False, selected_jobs=[dict(f.job, include_run_root=True)],
        accounting_before=accounting, accounting_after=accounting, inventory_sha256=m.sha(f.pull.parent / "inventory_before.json"),
        files=[dict(row, action="downloaded_verified") for row in rows]))


def execute(f):
    return f.m.review("101", source_inventory=f.inventory, pull_receipt=f.pull, root=f.root)


def test_complete_strict_raw_gates_publish_idempotently_without_weights(setup, monkeypatch):
    f = setup
    original = Path.open
    def safe_open(path, *args, **kwargs):
        assert not set(path.suffixes) & f.m.FORBIDDEN and "sealed" not in str(path)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", safe_open)
    result = execute(f)
    assert result["status"] == "passed" and len(result["files"]) == 9
    assert result["reviewed_counts"] == dict(input_forwards=6, operator_probes=63, f03_forward_backward_samples=48)
    assert execute(f) == result
    assert (f.base.parent / "root_review.json").is_file()


@pytest.mark.parametrize("change", ["running", "nonzero_exit", "wrong_job_receipt", "source_changed", "invocation_changed",
    "f00_flag", "f01_gradient", "f03_rng", "f03_missing_sample", "wrong_panel", "extra_operator_work", "completion_count",
    "duplicate_budget", "unverified_pull", "mixed_job", "failed_file"])
def test_any_failed_identity_or_raw_gate_never_writes_review(setup, change):
    f = setup
    m, root, base = f.m, f.root, f.base
    def mutate(path, edit):
        value = json.loads(path.read_text())
        edit(value)
        save(path, value)
    if change in ("running", "nonzero_exit"):
        mutate(root / m.STATE, lambda v: v["registered_jobs"][0].update(status="RUNNING") if change == "running"
               else v["registered_jobs"][0].update(exit_code="1:0"))
    elif change == "wrong_job_receipt":
        mutate(root / "results/formal_main_v2/job_receipts/101.json", lambda v: v.update(invocation_sha256="0" * 64))
    elif change == "source_changed":
        (root / "src/frozen.py").write_text("changed")
    elif change == "invocation_changed":
        mutate(root / f.job["invocation"], lambda v: v["argv"].append("--unknown"))
    elif change == "f00_flag":
        mutate(base / "input_acceptance.json", lambda v: v["observations"][0].update(pixels_equal=False))
    elif change == "f01_gradient":
        mutate(base / "f01_k128.json", lambda v: v["observations"][0].update(action_gradient_norm=0.))
    elif change == "f03_rng":
        mutate(base / "resume_acceptance.json", lambda v: v["arms"]["A"]["checks"].update(rng_equal=False))
    elif change == "f03_missing_sample":
        path = base / "f03_calls.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows.pop(next(i for i, r in enumerate(rows) if r["event"] == "sample_end"))
        journal(path, rows)
        mutate(base / "resume_acceptance.json", lambda v: v.update(journal_bytes=path.stat().st_size, journal_sha256=m.sha(path)))
    elif change == "wrong_panel":
        mutate(base / "f01_k256.json", lambda v: v["observations"][0].update(window_id="different-valid-window"))
    elif change == "extra_operator_work":
        with (base / "operator_calls.jsonl").open("a") as handle:
            handle.write('{"event":"failed","call_id":63}\n')
    elif change == "completion_count":
        f.complete["operator_probes"] = 62
    elif change == "mixed_job":
        mutate(base / "resume_acceptance.json", lambda v: v.update(job_id="102"))
    elif change == "failed_file":
        save(base / "failure.json", dict(error="retained failure"))
    reseal(f, duplicate_budget=change == "duplicate_budget")
    if change == "unverified_pull":
        mutate(f.pull, lambda v: v.update(final_evidence=False))
    with pytest.raises((ValueError, KeyError)):
        execute(f)
    assert not (base.parent / "root_review.json").exists()


def test_forbidden_evidence_rejected_before_io(setup, monkeypatch):
    f = setup
    def never(*args, **kwargs):
        pytest.fail("Forbidden file accessed")
    monkeypatch.setattr(Path, "open", never)
    for name in ("weights/best.pt", "configs/sealed_final.json", "initial_states/development.json", "../outside.json"):
        with pytest.raises(ValueError):
            f.m.Evidence(f.root).read(name)


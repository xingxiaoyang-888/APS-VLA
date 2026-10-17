"""CPU-only composition proof, with explicit GPU/official-file I/O stand-ins."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

from cti_vla.evaluation import formal_trials as trials
from cti_vla.evaluation.teacher_diagnostics import json_signature
from test_formal_deployment import synthetic_panel, freeze_fixture


ROOT = Path(__file__).resolve().parents[1]
ENTRY = "scripts/ops/formal_asset_evaluation_adapter.py"
INVENTORY = "results/formal_main_v2/source/formal_main_v2_run_564be0995e.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module", autouse=True)
def original_bytes_unchanged():
    adapter = load(ROOT / ENTRY, "read_only_composition_constants")
    files = {**read(ROOT / INVENTORY)["files"], adapter.LEGACY: adapter.LEGACY_SHA,
        **adapter.META_FILES, **adapter.GOAL_FILES}
    # Helpers are independent provenance consumers and must remain unchanged.
    for name in ("scripts/ops/formal_asset_compat_review.py", "scripts/ops/formal_goal_component_review.py"):
        files[name] = sha(ROOT / name)
    assert all(sha(ROOT / p) == s for p, s in files.items())
    yield
    assert all(sha(ROOT / p) == s for p, s in files.items())


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    helper = load(ROOT / "tests/test_formal_asset_stage.py", "downstream_original_fixture")
    fixture = helper.synthetic.__wrapped__(tmp_path_factory)
    adapter = load(ROOT / ENTRY, "composition_fixture_constants")
    for name in adapter.contract_files("libero_goal"):
        target = fixture.project / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    destination = fixture.project / adapter.REGISTRATION
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(fixture.source / adapter.REGISTRATION, destination)
    fixture.adapter = adapter
    fixture.matrix = freeze_fixture()
    fixture.matrix["registration_sha256"] = json_signature(fixture.registry)
    fixture.counter = 88000
    return fixture


def contract(project, suite):
    a = project.adapter
    value = dict(schema=a.SCHEMA, kind="formal_downstream_asset_compatibility", version=a.VERSION, suite=suite,
        entrypoint=a.ENTRY, evaluation_adapter=a.LEGACY, wrapper=a.WRAPPER, controller=a.CONTROLLER,
        metadata_implementation=a.metadata_contract(), legacy_stage_wrappers_executed=False,
        files={p: sha(project.project / p) for p in a.contract_files(suite)})
    if suite == "libero_goal": value["component_implementation"] = a.component_contract()
    return value


def new_case(project, *, suite="libero_object", stage="development", previous=None):
    project.counter += 1
    job = str(project.counter)
    p, source, a = project.project, project.source, project.adapter
    spec = project.registry["suites"][suite]
    matrix = deepcopy(project.matrix)
    methods = [dict(identity=r) for r in matrix["instances"] if r["suite"] == suite]
    if stage in ("development", "collect"): methods = methods[:1]
    manifest = dict(schema=a.SCHEMA, kind="evaluation_execution", registration_sha256=json_signature(project.registry),
        suite=suite, split="final" if stage == "final" else "development", methods=methods,
        environment={**trials.ENVIRONMENT, "max_steps": trials.FORMAL_SUITES[suite]["max_steps"]})
    mode = "evaluate" if stage in ("development", "final") else stage
    output = p / f"results/formal_main_v2/{suite}/downstream/{stage}/synthetic{job}"
    mp = p / f"results/formal_main_v2/execution/synthetic{job}.json"
    gate = p / f"results/formal_main_v2/{suite}/acceptance/synthetic_cpu/input_acceptance.json"
    for name in (spec["protocol"], spec["windows"]):
        write(p / name, dict(synthetic=True, not_an_actual_data_protocol=True, suite=suite))
    write(gate, dict(synthetic=True, not_an_actual_gpu_acceptance=True, suite=suite))
    args = dict(source_root=source, source_inventory=p / INVENTORY, adapter_sha256=a.LEGACY_SHA,
        execution_manifest=mp, registration=p / a.REGISTRATION, protocol=p / spec["protocol"], windows=p / spec["windows"],
        input_acceptance=gate, asset_manifest=source / spec["model_manifest"], checkpoint=spec["model_root_server"],
        oft_source=p / "external/openvla-oft", libero_source=p / "external/LIBERO", libero_config=p / "configs/libero_runtime",
        cache_directory=p / (".local/formal-hf-" + suite), output=output, project_root=p, policy_watchdog_seconds="60")
    initial = p / spec["initial_states_root"]
    dev = synthetic_panel(suite=suite)
    write(initial / "development.json", dev)
    if stage == "final":
        registry, sealed = synthetic_panel(suite=suite, split="final")
        # These are generated synthetic values, never actual project final data.
        write(initial / "final_registry.json", registry)
        write(initial / "sealed_final.json", sealed)
        matrix["suites"][suite].update(final_registry_sha256=sha(initial / "final_registry.json"),
            panel_source_sha256=json_signature(registry["source"]))
        release = trials.make_final_release(matrix, registration_sha256=json_signature(project.registry), created_utc="synthetic-only")
        rp = p / f"results/formal_main_v2/synthetic_freeze_{job}/root_release.json"
        write(rp, release)
        manifest.update(global_freeze=matrix, release=release)
        args.update(final_registry=initial / "final_registry.json", sealed_final=initial / "sealed_final.json",
            release=rp, release_sha256=sha(rp))
    else:
        args["development_panel"] = initial / "development.json"
    if stage in ("full", "components"):
        fp = p / f"results/formal_main_v2/synthetic_freeze_{job}/global_freeze.json"
        pp = p / f"results/formal_main_v2/synthetic_panel_{job}/panel.json"
        write(fp, matrix); write(pp, dict(synthetic=True, cpu_runner_standin=True, not_an_actual_raw_panel=True))
        args.update(global_freeze=fp, panel=pp)
    if mode == "evaluate": args["stop_after"] = "1"
    if previous:
        output, mp, manifest = previous.output, previous.manifest_path, previous.manifest
        args.update(output=output, execution_manifest=mp)
    else:
        write(mp, manifest)
    argv = [mode, *[x for name, val in args.items() for x in ("--" + name.replace("_", "-"), str(val))]]
    if previous: argv.append("--resume")
    if mode != "evaluate": argv.append("--uncontended-gpu")
    implementation = contract(project, suite)
    inv = dict(schema=a.SCHEMA, kind="formal_downstream_invocation", version="formal-downstream-root-v1", stage=stage,
        stage_key=previous.value["stage_key"] if previous else f"{suite}_{stage}_synthetic{job}", suite=suite,
        method_ids=[r["identity"]["method_id"] for r in methods], source_root=str(source), source_sha256=a.SOURCE_SHA,
        source_inventory=str(p / INVENTORY), source_inventory_sha256=sha(p / INVENTORY), entrypoint=ENTRY,
        adapter_sha256=a.LEGACY_SHA, wrapper=a.WRAPPER, wrapper_sha256=implementation["files"][a.WRAPPER],
        support_files=implementation["files"], argv=argv, run_root=str(output), resume=bool(previous),
        execution_manifest=str(mp), execution_manifest_sha256=sha(mp), registration_sha256=sha(p / a.REGISTRATION),
        stop_after=1 if mode == "evaluate" else None, scientific_settings_changed=False, final_values_read_locally=False,
        downstream_asset_compatibility=implementation)
    watched = {str(source / name): checksum for name, checksum in read(p / INVENTORY)["files"].items()}
    watched.update({str(p / name): checksum for name, checksum in implementation["files"].items()})
    for name in ("source_inventory", "registration", "execution_manifest", "protocol", "windows", "asset_manifest",
                 "input_acceptance", "development_panel", "release", "global_freeze", "panel"):
        if name in args: watched[str(args[name])] = sha(Path(args[name]))
    inv["watched_files"] = watched
    if previous:
        # This fixture represents the root-approved partition for the future
        # compatible E04 branch. It is not proof that the production plan
        # builder has been integrated. The original adapter still owns the
        # exact ledger-prefix and frozen config/panel checks.
        inv["root_evidence_sha256"] = {(output / name).relative_to(p).as_posix(): sha(output / name)
            for name in ("trials.jsonl", "closed_loop_report.json")}
    path = p / f"results/formal_main_v2/invocations/synthetic_downstream_{job}.json"
    write(path, inv)
    return SimpleNamespace(job=job, path=path, value=inv, output=output, manifest=manifest, manifest_path=mp, args=args)


CPU_PROGRAM = r'''
import hashlib,importlib.util,json,os,sys
from pathlib import Path
from types import SimpleNamespace
import torch
p,invpath=map(Path,sys.argv[1:3]); behavior=sys.argv[3]; expected=int(sys.argv[4])
spec=importlib.util.spec_from_file_location('synthetic_actual_asset_composition',p/'scripts/ops/formal_asset_evaluation_adapter.py')
outer=importlib.util.module_from_spec(spec);spec.loader.exec_module(outer)
inv=json.loads(invpath.read_text());source=Path(inv['source_root']);out=Path(inv['run_root']);suite=inv['suite'];job=os.environ['SLURM_JOB_ID']
real_load=outer.load; loaded={}; base_calls=[]; goal_io=[]; protected_touches=[]
small=p/'.local/synthetic_downstream_tensors'/job;small.mkdir(parents=True)
for i,name in enumerate(('action_head--50000_checkpoint.pt','proprio_projector--50000_checkpoint.pt')):
    torch.save({'module.weight':torch.tensor([float(i+1)])},small/name)

def base(args):
    if behavior=='early':raise RuntimeError('synthetic failure before base loading')
    if behavior=='zero':return
    from cti_vla.evaluation import checkpoint_manifest as cm
    chosen=args.asset_manifest
    if behavior=='wrong_manifest':chosen=source/'configs/assets/openvla_oft_libero_object.json'
    asset=cm.load_checkpoint_manifest(chosen);assert len(asset.files)==25
    if behavior=='duplicate_metadata':cm.load_checkpoint_manifest(chosen)
    from cti_vla.models import openvla_oft_loader as oft
    base_calls.append(suite)
    if suite=='libero_goal':
        a=oft._load_component_state(args.checkpoint/'action_head--150000_checkpoint.pt');assert a['weight'].tolist()==[1.]
        if behavior=='duplicate_component':oft._load_component_state(args.checkpoint/'action_head--150000_checkpoint.pt')
        b=oft._load_component_state(args.checkpoint/'proprio_projector--150000_checkpoint.pt');assert b['weight'].tolist()==[2.]
    else:
        # The frozen Object loader is unchanged; it deserializes only tiny CPU
        # fixtures here, in place of the explicitly substituted GPU base load.
        for i,name in enumerate(('action_head--50000_checkpoint.pt','proprio_projector--50000_checkpoint.pt')):
            value=oft._load_component_state(small/name);assert value['weight'].tolist()==[float(i+1)]
    if behavior=='after_load':raise RuntimeError('synthetic failure after both original tensor loads')
    if behavior=='system_exit_zero':raise SystemExit(0)
    if behavior=='mutate_input':args.input_acceptance.write_text('{"synthetic_changed_input":true}\n')
    if behavior=='mutate_run_code':loaded['legacy'].run.__code__=(lambda *a,**kw:None).__code__

def fake_evaluate(args,manifest,panel,registration_sha):
    base(args)
    from cti_vla.evaluation import formal_trials,libero_runtime
    from cti_vla.training.formal_future import formal_source_hashes
    from cti_vla.data.experiment_protocol import write_frozen_json
    from cti_vla.evaluation.teacher_diagnostics import json_signature,atomic_json
    config=dict(schema='formal_main_v2',kind='evaluation_run',manifest=manifest,registration_sha256=registration_sha,
        panel_signature=json_signature(panel),source_files=formal_source_hashes(source),policy_watchdog_seconds=60.,
        watched_files={},runtime={},synthetic_cpu_fixture=True)
    write_frozen_json(args.output/'config.json',config);write_frozen_json(args.output/'panel.json',panel)
    ledger=libero_runtime.TrialLedger(args.output/'trials.jsonl',run_signature=json_signature(config))
    ledger.append(dict(event='invocation',slurm_job_id=job))
    original=formal_trials.run_episode
    formal_trials.run_episode=lambda *a,**k:dict(status='completed',success=False,policy_calls=0,control_steps=0,wait_steps=10,attempt_wall_seconds=.01)
    try:
        formal_trials.evaluate_formal_trials(panel,{r['identity']['method_id']:object() for r in manifest['methods']},ledger,
            lambda state:(SimpleNamespace(close=lambda:None),'synthetic'),reseed=lambda:None,stop_after=args.stop_after)
    finally:formal_trials.run_episode=original
    report=formal_trials.summarize_formal_trials(panel,[r['identity']['method_id'] for r in manifest['methods']],ledger,
        provenance={'run_signature':json_signature(config)},checkpoint_unchanged=True)
    atomic_json(args.output/'closed_loop_report.json',report)
    return report

def fake_profile(args):
    # Original adapter.run, bindings and source/path checks execute. The GPU
    # profile runner is the stand-in; no timings or raw panels are claimed.
    base(args);args.output.mkdir(parents=True,exist_ok=False)
    value=dict(status='synthetic_gpu_runner_returned',synthetic=True,scientific_complete=False,
        actual_profile_calls=0,official_weights_loaded=False,mode=args.command,base_loads=len(base_calls))
    (args.output/'synthetic_profile_standin.json').write_text(json.dumps(value))
    return value

def instrument(path,name):
    module=real_load(path,name)
    if path.name=='formal_evaluation_adapter.py':
        loaded['legacy']=module; original=module.private_module
        def private(source,name):
            value=original(source,name)
            if name=='eval_formal_selector_libero':value.execute=fake_evaluate
            elif name=='profile_formal':value.run=fake_profile
            return value
        module.private_module=private;module.require_server=lambda:None
    if path.name=='formal_goal_component_adapter.py':
        verify=module._verify_target
        def cpu_target(row):
            fixed=next(x for x in module.MAPPINGS if x['target']==row['target'])
            assert all(row[k]==v for k,v in fixed.items()) and row['target_path']==module.MODEL_ROOT+'/'+row['target']
            goal_io.append(row['target']);target=small/row['target']
            return verify(dict(row,target_path=str(target),requested_path=str(small/row['requested']),
                size=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
        module._verify_target=cpu_target
    return module
outer.load=instrument
if behavior=='protect_final':
    registry=json.loads((p/outer.REGISTRATION).read_text());initial=p/registry['suites'][suite]['initial_states_root']
    forbidden={initial/'final_registry.json',initial/'sealed_final.json',p/'models/synthetic_forbidden.safetensors'}
    for method in ('open','stat','resolve'):
        original=getattr(Path,method)
        def guarded(path,*a,_original=original,**k):
            if path in forbidden:protected_touches.append(str(path));raise AssertionError('final path accessed before release')
            return _original(path,*a,**k)
        setattr(Path,method,guarded)
code=outer.execute(invpath,outer.sha(invpath),project_root=p);assert code==expected,(code,expected)
directory=p/'results/formal_main_v2/downstream_asset_invocations'/job
complete=json.loads((directory/'completion.json').read_text());assert complete['exit_code']==expected
assert not protected_touches
if complete['run_root']:
    for name in ('identity.json','events.jsonl','completion.json'):
        if (directory/name).exists():assert (directory/name).read_bytes()==(out/'asset_compatibility'/job/name).read_bytes()
if expected==0:
    assert len(base_calls)==1 and complete['status']=='returned' and complete['loader_bindings_restored']
    assert complete['original_adapter_run_unchanged'] and complete['source_inputs_unchanged']
    assert complete['legacy_adapter_proof']['status']=='returned'
    rows=[json.loads(line) for line in (directory/'events.jsonl').read_text().splitlines()]
    assert [r['seq'] for r in rows]==list(range(14 if suite=='libero_goal' else 8))
    if suite=='libero_goal':assert len(goal_io)==8
    else:assert not goal_io and 'component_implementation' not in complete['downstream_asset_compatibility']
    from cti_vla.evaluation import checkpoint_manifest as cm
    from cti_vla.models import openvla_oft_loader as oft
    assert cm.load_checkpoint_manifest.__name__=='load_checkpoint_manifest' and oft._load_component_state.__name__=='_load_component_state'
    assert complete['scientific_completion_not_inferred'] and not complete['legacy_stage_wrappers_executed']
else:assert complete['status']=='failed' and complete['errors']
'''


def run_case(project, case, *, behavior="normal", expected=0):
    run = subprocess.run([sys.executable, "-B", "-c", CPU_PROGRAM, str(project.project), str(case.path), behavior, str(expected)],
        cwd=project.project, env=dict(os.environ, SLURM_JOB_ID=case.job, PYTHONDONTWRITEBYTECODE="1", CUDA_VISIBLE_DEVICES=""),
        capture_output=True, text=True, timeout=120)
    assert run.returncode == 0, run.stdout + run.stderr
    value = read(project.project / f"results/formal_main_v2/downstream_asset_invocations/{case.job}/completion.json")
    # Execute the actual parent archive/acceptance boundary over the child's
    # raw bytes. The real Slurm subprocess launch and job receipt are not
    # synthesized as though they had run in this CPU fixture.
    parent = load(project.project / project.adapter.WRAPPER, "actual_downstream_parent_archive")
    def parent_boundary():
        old_artifacts, old_receipts = parent.archive_adapter_evidence(root=project.project,
            output=case.output, job_id=case.job, invocation=case.value)
        artifacts, completion = parent.archive_asset_evidence(root=project.project,
            output=case.output, job_id=case.job, invocation=case.value, invocation_sha256=sha(case.path))
        parent.require_asset_completion(artifacts, completion, old_artifacts, old_receipts)
        assert len(artifacts) == 3 and len(old_artifacts) == 2
    if expected == 0:
        parent_boundary()
    else:
        with pytest.raises(ValueError):
            parent_boundary()
    if expected == 0:
        with (project.project / "synthetic_asset_downstream_writer_index.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(dict(synthetic=True, job_id=case.job, suite=case.value["suite"], stage=case.value["stage"],
                invocation=str(case.path), output=str(case.output), resume=case.value["resume"], official_weights_loaded=False,
                actual_parent_archive_and_completion_check=True,
                substitution="GPU eval/profile runner and Goal official target I/O only; original adapter.run, scoped installers, tiny tensor loader, locks, release/ledger gates and writers execute")) + "\n")
    return value


@pytest.mark.parametrize("suite", ["libero_object", "libero_goal"])
@pytest.mark.parametrize("stage", ["development", "final", "collect", "full", "components"])
def test_actual_composed_writers_all_suites_stages(project, suite, stage):
    case = new_case(project, suite=suite, stage=stage)
    run_case(project, case)


@pytest.mark.parametrize("suite", ["libero_object", "libero_goal"])
def test_explicit_resume_partition_preserves_prefix_and_does_not_repeat_terminal(project, suite):
    first = new_case(project, suite=suite)
    run_case(project, first)
    ledger = first.output / "trials.jsonl"
    before = ledger.read_bytes()
    second = new_case(project, suite=suite, previous=first)
    for name in ("trials.jsonl", "closed_loop_report.json"):
        path = first.output / name
        assert str(path) not in second.value["watched_files"]
        assert second.value["root_evidence_sha256"][path.relative_to(project.project).as_posix()] == sha(path)
    run_case(project, second)
    after = ledger.read_bytes()
    assert after.startswith(before)
    rows = [json.loads(x) for x in after.splitlines()]
    done = [r["trial_id"] for r in rows if r["event"] == "result"]
    assert len(done) == len(set(done)) == 2
    assert [r["slurm_job_id"] for r in rows if r["event"] == "invocation"] == [first.job, second.job]


def test_legacy_e04_all_output_watch_refuses_legitimate_resume(project):
    first = new_case(project, suite="libero_goal")
    run_case(project, first)
    before = (first.output / "trials.jsonl").read_bytes()
    second = new_case(project, suite="libero_goal", previous=first)
    # Reproduce the existing E04 plan's verified_files -> watched_files mapping
    # over actual first-attempt outputs. No fabricated successful root review
    # or production builder integration is claimed by this CPU fixture.
    for path in first.output.rglob("*"):
        if path.is_file():
            second.value["watched_files"][str(path)] = sha(path)
    write(second.path, second.value)
    result = run_case(project, second, expected=1)
    assert result["legacy_adapter_proof"]["status"] == "returned"
    assert result["source_inputs_unchanged"] is False
    assert any("immutable source/input bytes changed" in row["error"] for row in result["errors"])
    after = (first.output / "trials.jsonl").read_bytes()
    assert len(after) > len(before) and after.startswith(before)


@pytest.mark.parametrize("behavior", ["early", "after_load", "zero", "duplicate_component", "duplicate_metadata", "wrong_manifest", "mutate_run_code", "system_exit_zero", "mutate_input"])
def test_incomplete_or_changed_runner_keeps_failure_and_restores(project, behavior):
    case = new_case(project, suite="libero_goal")
    result = run_case(project, case, behavior=behavior, expected=1)
    assert result["loader_bindings_restored"]
    assert result["legacy_adapter_proof"]


def test_actual_parent_rejects_final_paths_before_resolve_stat_or_read(project, monkeypatch):
    parent = load(project.project / project.adapter.WRAPPER, "actual_parent_final_path_guard")
    initial = project.project / project.registry["suites"]["libero_goal"]["initial_states_root"]
    forbidden = {initial / "final_registry.json", initial / "sealed_final.json"}
    touched = []
    for name in ("open", "stat", "resolve"):
        original = getattr(Path, name)
        def guarded(path, *args, _original=original, **kwargs):
            if path in forbidden:
                touched.append(str(path))
                raise AssertionError("parent touched a final path before lexical refusal")
            return _original(path, *args, **kwargs)
        monkeypatch.setattr(Path, name, guarded)
    for path in forbidden:
        with pytest.raises(ValueError, match="nonweight, nonsealed"):
            parent.safe(path, root=project.project, allow_development=True)
    assert touched == []


@pytest.mark.parametrize("mutation", ["object_component_null", "goal_missing_component", "wrong_dependency", "legacy_wrapper_executed", "extra_file", "missing_file", "historical_top_field", "wrong_entrypoint", "wrong_mode", "source_sha"])
def test_contract_identity_refused_before_any_loader(project, mutation):
    case = new_case(project, suite="libero_object" if mutation == "object_component_null" else "libero_goal")
    c = case.value["downstream_asset_compatibility"]
    if mutation == "object_component_null": c["component_implementation"] = None
    elif mutation == "goal_missing_component": c.pop("component_implementation")
    elif mutation == "wrong_dependency": c["metadata_implementation"]["files"][project.adapter.META] = "0" * 64
    elif mutation == "legacy_wrapper_executed": c["legacy_stage_wrappers_executed"] = True
    elif mutation == "extra_file": c["files"]["unexpected.py"] = "0" * 64
    elif mutation == "missing_file": c["files"].pop(project.adapter.META)
    elif mutation == "historical_top_field": case.value["runtime_compatibility"] = c["metadata_implementation"]
    elif mutation == "wrong_entrypoint": case.value["entrypoint"] = project.adapter.LEGACY
    elif mutation == "wrong_mode": case.value["argv"][0] = "collect"
    else: case.value["source_sha256"] = "0" * 64
    write(case.path, case.value)
    result = run_case(project, case, expected=1)
    assert result["legacy_adapter_proof"] is None and not result["loader_bindings_restored"]


@pytest.mark.parametrize("mutation", ["invalid_release", "development_is_sealed", "watched_is_sealed", "watched_is_weight",
    "manifest_is_sealed", "input_is_sealed", "release_is_sealed", "global_freeze_is_sealed", "panel_is_sealed"])
def test_final_path_guard_precedes_any_sealed_read_stat_resolve(project, mutation):
    stage = "final" if mutation in ("invalid_release", "release_is_sealed") else "full" if mutation in ("global_freeze_is_sealed", "panel_is_sealed") else "development"
    case = new_case(project, suite="libero_goal", stage=stage)
    initial = project.project / project.registry["suites"]["libero_goal"]["initial_states_root"]
    if mutation == "invalid_release":
        write(case.args["release"], dict(synthetic=True, invalid_release=True))
        index = case.value["argv"].index("--release-sha256") + 1
        case.value["argv"][index] = sha(case.args["release"])
    elif mutation == "development_is_sealed":
        index = case.value["argv"].index("--development-panel") + 1
        case.value["argv"][index] = str(initial / "sealed_final.json")
    elif mutation == "watched_is_sealed":
        case.value["watched_files"][str(initial / "sealed_final.json")] = "0" * 64
    elif mutation == "watched_is_weight":
        case.value["watched_files"][str(project.project / "models/synthetic_forbidden.safetensors")] = "0" * 64
    else:
        flag = {"manifest_is_sealed": "--execution-manifest", "input_is_sealed": "--input-acceptance",
            "release_is_sealed": "--release", "global_freeze_is_sealed": "--global-freeze", "panel_is_sealed": "--panel"}[mutation]
        case.value["argv"][case.value["argv"].index(flag) + 1] = str(initial / "sealed_final.json")
        if mutation == "manifest_is_sealed": case.value["execution_manifest"] = str(initial / "sealed_final.json")
    write(case.path, case.value)
    result = run_case(project, case, behavior="protect_final", expected=1)
    assert result["legacy_adapter_proof"] is None and result["run_root"] is None


def test_contract_exact_counts_and_new_files_lf(project):
    assert len(project.adapter.contract_files("libero_object")) == 10
    assert len(project.adapter.contract_files("libero_goal")) == 14
    for name in (ENTRY, "tests/test_formal_asset_evaluation_adapter.py"):
        assert b"\r" not in (ROOT / name).read_bytes()

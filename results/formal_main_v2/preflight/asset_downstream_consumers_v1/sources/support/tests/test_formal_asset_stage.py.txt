"""Real wrapper/adapter writers with a CPU stand-in for the frozen GPU runner."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
import uuid

import pytest


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = "results/formal_main_v2/source/formal_main_v2_run_564be0995e.json"
WRAPPER = "scripts/server/run_formal_asset_stage.py"
SLURM = "scripts/server/formal_asset_main.slurm"
SUPPORT = (WRAPPER, SLURM, "scripts/ops/formal_asset_metadata_adapter.py",
    "configs/experiments/formal_main_v2_asset_metadata_compat_v1.json",
    "configs/assets/formal_main_v2_strict/libero_object.json",
    "configs/assets/formal_main_v2_strict/libero_goal.json")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


@pytest.fixture(scope="module", autouse=True)
def original_files_unchanged():
    expected = read(ROOT / INVENTORY)["files"]
    expected.update({p: sha(ROOT / p) for p in SUPPORT[2:]})
    assert {p: sha(ROOT / p) for p in expected} == expected
    yield
    assert {p: sha(ROOT / p) for p in expected} == expected


@pytest.fixture(scope="module")
def synthetic(tmp_path_factory):
    project = tmp_path_factory.mktemp("synthetic_formal_asset_stage")
    assert ROOT / ".local" in project.parents
    source = project / "snapshots/formal_main_v2_run_564be0995e"
    inventory = read(ROOT / INVENTORY)
    for name in inventory["files"]:
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    for name in SUPPORT:
        target = project / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    inventory["source_root_server"] = str(source)
    write(project / INVENTORY, inventory)
    write(source / "source_manifest.json", inventory)
    return SimpleNamespace(project=project, source=source, registry=read(source / "configs/experiments/formal_main_v2.json"), counter=99000)


def invocation(fixture, *, suite="libero_object", stage="acceptance", budget=128, seed=17, resume=False):
    fixture.counter += 1
    job = str(fixture.counter)
    p, source = fixture.project, fixture.source
    spec = fixture.registry["suites"][suite]
    for path in (spec["protocol"], spec["windows"]):
        write(p / path, dict(synthetic=True, suite=suite, kind="test_metadata_only"))
    common = ["--protocol", str(p / spec["protocol"]), "--windows", str(p / spec["windows"]),
        "--checkpoint", spec["model_root_server"], "--asset-manifest", str(source / spec["model_manifest"]),
        "--data-directory", spec["data_root_server"], "--cache-directory", str(p / (".local/formal-hf-" + suite)),
        "--feature-cache", spec["cache_root_server"]]
    watched = {str(p / x): sha(p / x) for x in (spec["protocol"], spec["windows"])}
    watched[str(source / spec["model_manifest"])] = spec["model_manifest_sha256"]
    if stage == "acceptance":
        output = p / f"results/formal_main_v2/{suite}/acceptance/attempt{fixture.counter}"
        configs = [source / f"configs/experiments/formal_main_v2/{suite}_k{k}_seed17.json" for k in (128, 256, 64)]
        argv = ["--suite", suite, "--configs", *map(str, configs), *common,
            "--oft-source", str(p / "external/openvla-oft"), "--project-root", str(p), "--output", str(output)]
        watched.update({str(path): sha(path) for path in configs})
        key, segment, entry = suite + "_acceptance", None, "scripts/verify_formal_acceptance.py"
    else:
        pair = next(x for x in fixture.registry["pairs"] if (x["suite"], x["visual_tokens"], x["seed"]) == (suite, budget, seed))
        output = p / f"results/formal_main_v2/{suite}/k{budget}/seed{seed}/training"
        gate = p / f"results/formal_main_v2/{suite}/acceptance/attempt00"
        for name in ("input_acceptance.json", f"f01_k{budget}.json", "resume_acceptance.json", "f03_calls.jsonl", "acceptance_complete.json"):
            path = gate / name
            write(path, dict(synthetic=True, not_an_actual_acceptance=True))
            watched[str(path)] = sha(path)
        config = source / pair["path"]
        watched[str(config)] = pair["sha256"]
        argv = ["--config", str(config), *common, "--training-checkpoints", pair["checkpoint_root_server"],
            "--input-acceptance-report", str(gate / "input_acceptance.json"), "--acceptance-report", str(gate / f"f01_k{budget}.json"),
            "--output", str(output), "--arm", "both", "--stop-after-updates", "500", "--max-wall-seconds", "12600"]
        if resume:
            argv += ["--resume"]
        key, segment, entry = f"{suite}_train_k{budget}_seed{seed}", 500, "scripts/run_formal_future.py"
    compat = dict(schema="formal_main_v2", kind="asset_metadata_compatibility", version="formal-asset-metadata-compat-v1",
        wrapper=WRAPPER, slurm=SLURM, adapter=SUPPORT[2], registration=SUPPORT[3], files={x: sha(p / x) for x in SUPPORT})
    value = dict(schema="formal_main_v2", stage=stage, stage_key=key, suite=suite, source_root=str(source),
        source_sha256="dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e",
        entrypoint=entry, argv=argv, watched_files=watched, segment_end=segment, runtime_compatibility=compat,
        registration_sha256=sha(source / "configs/experiments/formal_main_v2.json"))
    path = p / f"results/formal_main_v2/invocations/synthetic_{job}.json"
    write(path, value)
    return SimpleNamespace(job=job, path=path, value=value, output=output,
        receipt=p / f"results/formal_main_v2/job_receipts/{job}.json")


def run(fixture, case, *, behavior="return", expected=0, mutation=None, extra=""):
    code = r'''
from pathlib import Path
import hashlib,importlib.util,json,os,sys
p, source, invocation_path = map(Path, sys.argv[1:4])
behavior, expected, mutation = sys.argv[4], int(sys.argv[5]), sys.argv[6]
spec=importlib.util.spec_from_file_location('synthetic_real_asset_wrapper',p/'scripts/server/run_formal_asset_stage.py')
wrapper=importlib.util.module_from_spec(spec);spec.loader.exec_module(wrapper)
inv=json.loads(invocation_path.read_text());output=Path(inv['argv'][inv['argv'].index('--output')+1])
calls=[];initial_argv=sys.argv;initial_cwd=Path.cwd();before_protocol=None
def cpu_runner(path,run_name):
    global before_protocol
    assert path==str(source/inv['entrypoint']) and run_name=='__main__'
    assert Path.cwd()==source and sys.argv==[path,*inv['argv']]
    if inv['stage']=='acceptance': assert not output.exists(), 'wrapper pre-created fresh acceptance output'
    calls.append(path)
    if behavior=='early_failure': raise RuntimeError('synthetic failure before output/model load')
    from cti_vla.evaluation import checkpoint_manifest as cm
    original=inv['argv'][inv['argv'].index('--asset-manifest')+1]
    if behavior!='zero_load':
        asset=cm.load_checkpoint_manifest(original)
        assert len(asset.files)==25
        if behavior=='double_load': cm.load_checkpoint_manifest(original)
        if behavior=='passthrough_load': cm.load_checkpoint_manifest(source/'configs/assets/openvla_oft_libero_spatial.json')
    output.mkdir(parents=True,exist_ok=True)
    (output/('synthetic_runner_'+os.environ['SLURM_JOB_ID']+'.json')).write_text(json.dumps(dict(synthetic=True,weights_loaded=False,science_executed=False)))
    if behavior=='exception': raise RuntimeError('synthetic GPU-runner stand-in failure')
    if behavior.startswith('exit'): raise SystemExit(int(behavior[4:]))
    if mutation=='protocol':
        q=Path(inv['argv'][inv['argv'].index('--protocol')+1]);before_protocol=(q,q.read_bytes());q.write_bytes(before_protocol[1]+b'\n')
wrapper.runpy.run_path=cpu_runner
try:
    result=wrapper.execute(invocation_path,wrapper.sha(invocation_path),project_root=p)
    assert result==expected,(result,expected)
    assert sys.argv is initial_argv and Path.cwd()==initial_cwd
finally:
    if before_protocol:before_protocol[0].write_bytes(before_protocol[1])
receipt=json.loads((p/'results/formal_main_v2/job_receipts'/(os.environ['SLURM_JOB_ID']+'.json')).read_text())
assert receipt['exit_code']==expected and receipt['runtime_compatibility']==inv.get('runtime_compatibility')
assert receipt['source_sha256']==inv['source_sha256']
for a in receipt['compatibility_artifacts']:
    original,target=Path(a['source']),Path(a['path'])
    assert original.read_bytes()==target.read_bytes()
    assert hashlib.sha256(target.read_bytes()).hexdigest()==a['sha256'] and target.stat().st_size==a['bytes']
if expected==0:
    assert len(calls)==1 and receipt['status']=='returned' and receipt['loader_restored'] and receipt['source_inputs_unchanged']
    assert len(receipt['compatibility_artifacts'])==2
    events=[json.loads(line) for line in (output/'compatibility'/os.environ['SLURM_JOB_ID']/'compatibility_events.jsonl').read_text().splitlines()]
    assert [e['seq'] for e in events]==list(range(8))
    assert [e['event'] for e in events]==['stage_start','asset_metadata_compat_enter','stage_runner_start','asset_metadata_compat_load_start','asset_metadata_compat_load_complete','stage_runner_return','asset_metadata_compat_exit','stage_end']
    assert all(e['suite']==inv['suite'] and e['invocation_sha256']==receipt['invocation_sha256'] for e in events)
    assert events[3]['view']['original_path']==inv['argv'][inv['argv'].index('--asset-manifest')+1]
else:
    assert receipt['status']=='failed' and receipt['errors']
if 'cti_vla.evaluation.checkpoint_manifest' in sys.modules:
    cm=sys.modules['cti_vla.evaluation.checkpoint_manifest']
    try: cm.load_checkpoint_manifest(inv['argv'][inv['argv'].index('--asset-manifest')+1])
    except ValueError as e: assert 'keys mismatch' in str(e)
    else: raise AssertionError('original strict loader was not restored')
'''
    env = dict(os.environ, SLURM_JOB_ID=case.job, PYTHONDONTWRITEBYTECODE="1")
    value = subprocess.run([sys.executable, "-B", "-c", code + "\n" + extra, str(fixture.project), str(fixture.source),
        str(case.path), behavior, str(expected), mutation or ""], capture_output=True, text=True, timeout=45,
        cwd=fixture.project, env=env)
    assert value.returncode == 0, value.stdout + value.stderr
    return read(case.receipt)


@pytest.mark.parametrize("suite", ["libero_object", "libero_goal"])
def test_acceptance_real_writer_full_chain_without_precreating_output(synthetic, suite):
    case = invocation(synthetic, suite=suite)
    receipt = run(synthetic, case)
    assert receipt["runner_termination"] == "returned"
    index = synthetic.project / "synthetic_success_index.jsonl"
    with index.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(dict(synthetic=True, science_executed=False, suite=suite,
            invocation=str(case.path), receipt=str(case.receipt), output=str(case.output))) + "\n")


@pytest.mark.parametrize("suite,budget,seed,resume", [
    ("libero_object", 256, 17, False), ("libero_goal", 128, 23, True), ("libero_object", 64, 41, True)])
def test_train_budget_seed_resume_original_argv_unchanged(synthetic, suite, budget, seed, resume):
    case = invocation(synthetic, suite=suite, stage="train", budget=budget, seed=seed, resume=resume)
    run(synthetic, case)


@pytest.mark.parametrize("behavior,expected,termination", [
    ("exit0", 0, "system_exit"), ("exit3", 3, "system_exit"),
    ("exception", 1, "exception"), ("early_failure", 1, "exception")])
def test_runner_exits_are_preserved_and_restored(synthetic, behavior, expected, termination):
    case = invocation(synthetic)
    receipt = run(synthetic, case, behavior=behavior, expected=expected)
    assert receipt["runner_termination"] == termination
    assert receipt["loader_restored"] is True and receipt["source_inputs_unchanged"] is True
    assert len(receipt["compatibility_artifacts"]) == 2


@pytest.mark.parametrize("behavior", ["zero_load", "double_load", "passthrough_load"])
def test_no_or_repeated_adapted_load_cannot_claim_success(synthetic, behavior):
    case = invocation(synthetic)
    receipt = run(synthetic, case, behavior=behavior, expected=1)
    assert any("exactly one" in row["error"] for row in receipt["errors"])


def test_live_protocol_change_fails_postcheck(synthetic):
    case = invocation(synthetic)
    receipt = run(synthetic, case, mutation="protocol", expected=1)
    assert receipt["source_inputs_unchanged"] is False
    assert any("bytes changed" in row["error"] for row in receipt["errors"])


@pytest.mark.parametrize("change", ["missing_compat", "extra_support", "adapter_sha", "scope", "asset_path", "argv_extra", "watch_missing"])
def test_preflight_failures_preserve_failure_receipt_without_runner(synthetic, change):
    case = invocation(synthetic)
    value = case.value
    if change == "missing_compat": value.pop("runtime_compatibility")
    elif change == "extra_support": value["runtime_compatibility"]["files"]["unregistered.py"] = "a"*64
    elif change == "adapter_sha": value["runtime_compatibility"]["files"][SUPPORT[2]] = "a"*64
    elif change == "scope": value["suite"] = "libero_10"
    elif change == "asset_path": value["argv"][value["argv"].index("--asset-manifest")+1] = str(synthetic.project / "configs/assets/formal_main_v2_strict/libero_object.json")
    elif change == "argv_extra": value["argv"] += ["--prepare-only"]
    else: value["watched_files"].pop(next(iter(value["watched_files"])))
    write(case.path, value)
    receipt = run(synthetic, case, expected=1)
    assert receipt["runner_termination"] == "not_started" and not case.output.exists()
    assert receipt["compatibility_artifacts"] == []


def test_existing_job_receipt_is_not_overwritten(synthetic):
    case = invocation(synthetic)
    run(synthetic, case, extra=r'''
receipt_path=p/'results/formal_main_v2/job_receipts'/(os.environ['SLURM_JOB_ID']+'.json')
before=receipt_path.read_bytes()
try:wrapper.execute(invocation_path,wrapper.sha(invocation_path),project_root=p)
except FileExistsError:pass
else:raise AssertionError('same job was restarted')
assert receipt_path.read_bytes()==before and len(calls)==1
''')


def test_shared_original_stage_lock_prevents_another_runner(synthetic):
    case = invocation(synthetic)
    spec = importlib.util.spec_from_file_location("synthetic_lock_owner", synthetic.project / WRAPPER)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    path = synthetic.project / "results/formal_main_v2/stage_locks" / (case.value["stage_key"] + ".lock")
    with module.stage_lock(path):
        receipt = run(synthetic, case, expected=1)
    assert receipt["runner_termination"] == "not_started" and not case.output.exists()
    assert any(e["phase"] == "stage_lock" for e in receipt["errors"])


def test_slurm_resource_and_environment_contract_matches_original():
    original = (ROOT / "scripts/server/formal_main.slurm").read_text().splitlines()
    current = (ROOT / SLURM).read_text().splitlines()
    assert [x for x in current if x.startswith("#SBATCH")] == [x for x in original if x.startswith("#SBATCH")]
    assert [x for x in current if x.startswith("export ")] == [x for x in original if x.startswith("export ")]
    assert not any("CUDA_VISIBLE_DEVICES=" in x for x in current)
    assert 'srun python "$P/scripts/server/run_formal_asset_stage.py" --invocation "$INVOCATION" --invocation-sha256 "$INVOCATION_SHA256"' in current
    assert all(b"\r" not in (ROOT / path).read_bytes() for path in (WRAPPER, SLURM))

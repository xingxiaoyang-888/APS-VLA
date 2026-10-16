"""CPU-only Goal compatibility: real small tensors, never official weights."""
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


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = "scripts/ops/formal_goal_component_adapter.py"
WRAPPER = "scripts/server/run_formal_goal_asset_stage.py"
SLURM = "scripts/server/formal_goal_asset_main.slurm"
REGISTRATION = "configs/experiments/formal_main_v2_goal_component_compat_v1.json"
NEW = (ADAPTER, WRAPPER, SLURM, REGISTRATION)
INVENTORY = "results/formal_main_v2/source/formal_main_v2_run_564be0995e.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module", autouse=True)
def frozen_unchanged():
    expected = read(ROOT / INVENTORY)["files"]
    protected = ["scripts/server/run_formal_asset_stage.py", "scripts/server/formal_asset_main.slurm",
        "scripts/ops/formal_asset_metadata_adapter.py", "scripts/ops/formal_asset_compat_review.py",
        "configs/experiments/formal_main_v2_asset_metadata_compat_v1.json", "configs/assets/formal_main_v2_strict/libero_goal.json",
        "configs/assets/formal_main_v2_strict/libero_object.json"]
    expected.update({p: sha(ROOT / p) for p in protected})
    assert all(sha(ROOT / p) == s for p, s in expected.items())
    yield
    assert all(sha(ROOT / p) == s for p, s in expected.items())


@pytest.fixture
def scoped(tmp_path):
    import torch
    assert ROOT / ".local" in tmp_path.parents
    adapter = load(ROOT / ADAPTER, "synthetic_goal_component_adapter_" + tmp_path.name)
    module = load(ROOT / adapter.LOADER, "synthetic_original_component_loader_" + tmp_path.name)
    watched = tmp_path / "synthetic_metadata.json"
    write(watched, dict(synthetic=True))
    rows = []
    for index, mapping in enumerate(adapter.MAPPINGS):
        target = tmp_path / mapping["target"]
        torch.save({"module.weight": torch.tensor([float(index + 1)])}, target)
        rows.append(dict(mapping, requested_path=str(tmp_path / mapping["requested"]),
            target_path=str(target), size=target.stat().st_size, sha256=sha(target)))
    identity = dict(synthetic=True, official_weights_loaded=False, mappings=rows,
        original_function_code_sha256={k: adapter.code_sha(getattr(module, k)) for k in adapter.SYMBOLS},
        watched_files={str(watched): sha(watched)})
    events = []
    def emit(event, **fields):
        events.append(dict(event=event, **fields))
    return SimpleNamespace(adapter=adapter, module=module, identity=identity, emit=emit,
        events=events, rows=rows, watched=watched, torch_load=torch.load)


def test_original_loader_values_and_scope_restored(scoped):
    s = scoped
    original = s.module._load_component_state
    with s.adapter._scoped_component_loader(s.module, s.identity, s.emit):
        escaped = s.module._load_component_state
        for i, row in enumerate(s.rows):
            result = escaped(Path(row["requested_path"]))
            assert list(result) == ["weight"] and result["weight"].tolist() == [float(i + 1)]
        assert s.module.torch.load is s.torch_load
    assert s.module._load_component_state is original and s.module.torch.load is s.torch_load
    assert s.events[-1]["component_calls_completed"] == 2 and s.events[-1]["original_loader_restored"]
    with pytest.raises(RuntimeError, match="outside"):
        escaped(Path(s.rows[0]["requested_path"]))


@pytest.mark.parametrize("case", ["outside", "target_direct", "reverse", "repeat", "traversal"])
def test_unregistered_component_requests_rejected(scoped, case):
    s = scoped
    original = s.module._load_component_state
    with pytest.raises(ValueError, match="exact two Goal"):
        with s.adapter._scoped_component_loader(s.module, s.identity, s.emit):
            if case == "repeat":
                s.module._load_component_state(Path(s.rows[0]["requested_path"]))
            requested = {"outside": Path(s.rows[0]["requested_path"]).parent / "another.pt",
                "target_direct": Path(s.rows[0]["target_path"]), "reverse": Path(s.rows[1]["requested_path"]),
                "repeat": Path(s.rows[0]["requested_path"]),
                "traversal": Path(s.rows[0]["requested_path"]).parent / "sub/../" / Path(s.rows[0]["requested_path"]).name}[case]
            s.module._load_component_state(requested)
    assert s.module._load_component_state is original
    assert s.events[-1]["rejected_calls"] == 1 and s.events[-1]["runner_raised"]


@pytest.mark.parametrize("case", ["target_bytes", "target_missing", "requested_alias", "cross_parent"])
def test_target_verification_checks_real_cpu_bytes_and_paths(scoped, case):
    s = scoped
    row = dict(s.rows[0])
    if case == "target_bytes": Path(row["target_path"]).write_bytes(b"changed synthetic bytes")
    elif case == "target_missing": Path(row["target_path"]).unlink()
    elif case == "requested_alias": Path(row["requested_path"]).write_bytes(b"forbidden alias")
    else: row["target_path"] = str(Path(row["target_path"]).parent.parent / Path(row["target_path"]).name)
    with pytest.raises(ValueError):
        s.adapter._verify_target(row)


def test_component_deserialization_failure_restores_original(scoped):
    s = scoped
    target = Path(s.rows[0]["target_path"])
    target.write_bytes(b"not a pytorch tensor file")
    s.rows[0].update(size=target.stat().st_size, sha256=sha(target))
    original = s.module._load_component_state
    with pytest.raises(Exception):
        with s.adapter._scoped_component_loader(s.module, s.identity, s.emit):
            s.module._load_component_state(Path(s.rows[0]["requested_path"]))
    assert s.module._load_component_state is original
    assert any(r["event"] == "goal_component_load_failed" for r in s.events)
    assert s.events[-1]["runner_raised"] and s.events[-1]["component_calls_completed"] == 0


@pytest.mark.parametrize("case", ["code", "binding", "watched_input"])
def test_scope_detects_mutation_and_restores(scoped, case):
    s = scoped
    original, original_code = s.module._load_component_state, s.module._load_component_state.__code__
    with pytest.raises((RuntimeError, ValueError)):
        with s.adapter._scoped_component_loader(s.module, s.identity, s.emit):
            if case == "code": original.__code__ = (lambda path: {}).__code__
            elif case == "binding": s.module._load_component_state = lambda path: {}
            else: s.watched.write_bytes(b"changed")
    assert s.module._load_component_state is original and original.__code__ is original_code
    assert s.events[-1]["original_loader_restored"]


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    helper = load(ROOT / "tests/test_formal_asset_stage.py", "synthetic_goal_old_writer_helpers")
    fixture = helper.synthetic.__wrapped__(tmp_path_factory)
    for name in NEW:
        target = fixture.project / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    fixture.helper = helper
    return fixture


def new_case(project, *, stage="acceptance", suite="libero_goal"):
    case = project.helper.invocation(project, suite=suite, stage=stage, budget=128, seed=17, resume=stage == "train")
    case.value["component_compatibility"] = dict(schema="formal_main_v2", kind="goal_component_filename_compatibility",
        version="formal-goal-components-v1", suite="libero_goal", wrapper=WRAPPER, adapter=ADAPTER, slurm=SLURM,
        registration=REGISTRATION, files={p: sha(project.project / p) for p in NEW})
    write(case.path, case.value)
    return case


CPU_PROGRAM = r'''
import hashlib,importlib.util,json,os,sys
from pathlib import Path
import torch
p,invocation_path=map(Path,sys.argv[1:3]);behavior=sys.argv[3];expected=int(sys.argv[4])
spec=importlib.util.spec_from_file_location('synthetic_goal_outer',p/'scripts/server/run_formal_goal_asset_stage.py')
outer=importlib.util.module_from_spec(spec);spec.loader.exec_module(outer)
inv=json.loads(invocation_path.read_text());source=Path(inv['source_root'])
output=Path(inv['argv'][inv['argv'].index('--output')+1])
small=p/'synthetic_component_tensors'/os.environ['SLURM_JOB_ID'];small.mkdir(parents=True)
for i,name in enumerate(('action_head--50000_checkpoint.pt','proprio_projector--50000_checkpoint.pt')):
    torch.save({'module.weight':torch.tensor([float(i+1)])},small/name)
real_loader=outer.load_module;called=[];inner_sha_at_return=None
def cpu_runner(path,run_name):
    assert path==str(source/inv['entrypoint']) and run_name=='__main__'
    if inv['stage']=='acceptance':assert not output.exists(),'outer pre-created acceptance output'
    from cti_vla.evaluation import checkpoint_manifest as cm
    asset=cm.load_checkpoint_manifest(inv['argv'][inv['argv'].index('--asset-manifest')+1]);assert len(asset.files)==25
    from cti_vla.models import openvla_oft_loader as oft
    base=Path(inv['argv'][inv['argv'].index('--checkpoint')+1])
    if behavior=='early_failure':raise RuntimeError('synthetic before component loading')
    if behavior!='zero':
        a=oft._load_component_state(base/'action_head--150000_checkpoint.pt');assert a['weight'].tolist()==[1.]
        if behavior=='duplicate':oft._load_component_state(base/'action_head--150000_checkpoint.pt')
        b=oft._load_component_state(base/'proprio_projector--150000_checkpoint.pt');assert b['weight'].tolist()==[2.]
    output.mkdir(parents=True,exist_ok=True)
    (output/'synthetic_runner.json').write_text(json.dumps(dict(synthetic=True,official_weights_loaded=False,scientific_runner_executed=False,synthetic_tensor_files_loaded=True)))
    if behavior=='exception':raise RuntimeError('synthetic after both component loads')
def instrument(path,name):
    module=real_loader(path,name)
    if path.name=='run_formal_asset_stage.py':
        module.runpy.run_path=cpu_runner
    if path.name=='formal_goal_component_adapter.py':
        verify=module._verify_target
        def cpu_target(row):
            # Only the official-file I/O boundary is substituted. Production
            # metadata and both real wrapper/adapter writers are unmodified.
            fixed=next(x for x in module.MAPPINGS if x['target']==row['target'])
            assert all(row[k]==v for k,v in fixed.items())
            assert row['target_path']==module.MODEL_ROOT+'/'+row['target']
            target=small/row['target'];local=dict(row,target_path=str(target),requested_path=str(small/row['requested']),size=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
            called.append(row['target'])
            return verify(local)
        module._verify_target=cpu_target
    return module
outer.load_module=instrument
code=outer.execute(invocation_path,outer.sha(invocation_path),project_root=p);assert code==expected,(code,expected)
globaldir=p/'results/formal_main_v2/component_compatibility_invocations'/os.environ['SLURM_JOB_ID']
completion=json.loads((globaldir/'completion.json').read_text())
assert completion['exit_code']==expected
assert completion['component_compatibility']==inv.get('component_compatibility')
if completion['run_root']:
    for name in ('identity.json','events.jsonl','completion.json'):
        if (globaldir/name).exists():assert (globaldir/name).read_bytes()==(output/'component_compatibility'/os.environ['SLURM_JOB_ID']/name).read_bytes()
receipt_path=p/'results/formal_main_v2/job_receipts'/(os.environ['SLURM_JOB_ID']+'.json')
if receipt_path.exists():
    receipt=json.loads(receipt_path.read_text())
    assert 'component_compatibility' not in receipt and 'component_artifacts' not in receipt
    assert completion['inner_job_receipt']['sha256']==outer.sha(receipt_path)
    for item in receipt['compatibility_artifacts']:
        assert Path(item['source']).read_bytes()==Path(item['path']).read_bytes()
        assert outer.sha(item['path'])==item['sha256']
    assert completion['metadata_artifacts']==receipt['compatibility_artifacts']
if expected==0:
    assert len(called)==8
    assert completion['status']=='returned' and completion['original_loader_restored'] and completion['source_inputs_unchanged'] and completion['component_files_unchanged']
    rows=[json.loads(x) for x in (globaldir/'events.jsonl').read_text().splitlines()]
    assert [r['seq'] for r in rows]==list(range(10))
    assert [r['event'] for r in rows]==['component_stage_start','goal_component_compat_enter','component_inner_start','goal_component_load_start','goal_component_load_complete','goal_component_load_start','goal_component_load_complete','component_inner_return','goal_component_compat_exit','component_stage_end']
    old=[json.loads(x) for x in Path(receipt['compatibility_artifacts'][1]['path']).read_text().splitlines()]
    assert len(old)==8 and old[-1]['status']=='returned'
    from cti_vla.models import openvla_oft_loader as oft
    try:oft._load_component_state(Path(inv['argv'][inv['argv'].index('--checkpoint')+1])/'action_head--150000_checkpoint.pt')
    except FileNotFoundError:pass
    else:raise AssertionError('Original exact path loader was not restored')
else:assert completion['status']=='failed' and completion['errors']
'''


def run_case(project, case, *, behavior="normal", expected=0):
    value = subprocess.run([sys.executable, "-B", "-c", CPU_PROGRAM, str(project.project), str(case.path), behavior, str(expected)],
        capture_output=True, text=True, timeout=100, cwd=project.project,
        env=dict(os.environ, SLURM_JOB_ID=case.job, PYTHONDONTWRITEBYTECODE="1"))
    assert value.returncode == 0, value.stdout + value.stderr
    return read(project.project / f"results/formal_main_v2/component_compatibility_invocations/{case.job}/completion.json")


@pytest.mark.parametrize("stage", ["acceptance", "train"])
def test_actual_outer_inner_both_real_evidence_chains(project, stage):
    case = new_case(project, stage=stage)
    run_case(project, case)
    with (project.project / "synthetic_goal_component_success_index.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(dict(synthetic=True, official_weights_loaded=False, stage=stage,
            substitution="Frozen GPU runner and official component I/O boundary only; actual tiny torch.load and both wrapper/adapter writers",
            invocation=str(case.path), receipt=str(case.receipt), output=str(case.output))) + "\n")


@pytest.mark.parametrize("behavior", ["early_failure", "exception", "zero", "duplicate"])
def test_actual_outer_failure_restores_and_retains_both_records(project, behavior):
    case = new_case(project)
    result = run_case(project, case, behavior=behavior, expected=1)
    assert result["original_loader_restored"] and result["source_inputs_unchanged"]
    assert result["inner_job_receipt"] and len(result["metadata_artifacts"]) == 2


@pytest.mark.parametrize("case_name", ["wrong_suite", "missing", "extra_file", "sha"])
def test_component_contract_fails_before_frozen_runner(project, case_name):
    case = new_case(project, suite="libero_object" if case_name == "wrong_suite" else "libero_goal")
    if case_name == "missing":case.value.pop("component_compatibility")
    elif case_name == "extra_file":case.value["component_compatibility"]["files"]["unexpected.py"]="a"*64
    elif case_name == "sha":case.value["component_compatibility"]["files"][ADAPTER]="a"*64
    write(case.path, case.value)
    result = run_case(project, case, expected=1)
    assert result["inner_job_receipt"] is None


def test_registration_matches_exact_code_and_slurm_resources():
    adapter = load(ROOT / ADAPTER, "goal_registration_only")
    assert read(ROOT / REGISTRATION) == adapter.registration_payload()
    original = (ROOT / "scripts/server/formal_asset_main.slurm").read_text().splitlines()
    current = (ROOT / SLURM).read_text().splitlines()
    assert [x for x in current if x.startswith(("#SBATCH", "export "))] == [x for x in original if x.startswith(("#SBATCH", "export "))]
    assert not any("CUDA_VISIBLE_DEVICES=" in x for x in current)
    assert all(b"\r" not in (ROOT / p).read_bytes() for p in (*NEW, "tests/test_formal_goal_component_stage.py"))

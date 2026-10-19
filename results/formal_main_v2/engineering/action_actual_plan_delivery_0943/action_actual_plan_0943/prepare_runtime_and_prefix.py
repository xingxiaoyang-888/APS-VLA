"""Actual Spatial development inputs only; produces candidate evidence without activation."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib, importlib.util, json, os, sys
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/action_actual_plan_0943'
BASE='results/formal_main_v2/libero_spatial/downstream/development/8c843c1d4ee8383c/attempt01'
PAN='configs/manifests/formal_main_v2/libero_spatial/initial_states/development.json'
PIN={'contract.py':'efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19','runtime_scope.py':'6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53'}
readmap={}
def h(raw):return hashlib.sha256(raw).hexdigest()
def safe(p):
    p=Path(p)
    if not p.is_absolute():p=R/p
    rel=None
    for base in (R,S,P):
        try:rel=p.relative_to(base).as_posix();break
        except ValueError:pass
    assert rel is not None and '..' not in p.parts and p.resolve()==p,str(p)
    assert not any('sealed' in x.lower() or x.lower() in {'test','weights','checkpoints'} for x in p.parts),str(p)
    assert not set(p.suffixes)&{'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init'},str(p)
    assert p.suffix in {'.py','.pyc','.pyo'} or rel==PAN or not any(x in rel.lower() for x in ('init_state','initial_state','final_state','test_state')),str(p)
    return p
def read(p,pin=None):
    p=safe(p);a=p.stat();raw=p.read_bytes();b=p.stat()
    assert (a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_ino,b.st_size,b.st_mtime_ns)
    got=h(raw);assert pin is None or got==pin,(str(p),pin,got)
    assert str(p) not in readmap or readmap[str(p)]==got
    readmap[str(p)]=got;return raw
def jread(p,pin=None):return json.loads(read(p,pin))
def put(name,obj):
    raw=(json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
    with (D/name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return {'path':str((D/name).relative_to(R)),'sha256':h(raw),'bytes':len(raw)}
def guard(event,args):
    if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No processes/network in preparation')
    if event=='open':
        p,mode,flags=args
        if isinstance(p,(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(p));p=p if p.is_absolute() else Path.cwd()/p
            assert not any('sealed' in x.lower() for x in p.parts),str(p)
            assert not set(p.suffixes)&{'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init'},str(p)
            write=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            if write:assert D in p.parents,str(p)
sys.addaudithook(guard)
read(__file__)
plan=jread(D/'scientific_plan.json','43a521e2b1c5b7f8ceff442ce655dde5cae73dfde0f9f7598f65fa57446b4a94')
inv=plan['invocation']
for n,pin in inv['root_evidence_sha256'].items():read(R/n,pin)
mods={}
for n,pin in PIN.items():
    path=R/'scripts/ops/formal_action_deployment_v1'/n;raw=read(path,pin)
    spec=importlib.util.spec_from_file_location('actual_'+n[:-3],path);m=importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),m.__dict__);mods[n]=m
ct=mods['contract.py'];rt=mods['runtime_scope.py']
runtime=rt.make_contract(project_root=R,source_root=S,suite='libero_spatial',stage='development')
watched=rt.validate_contract(runtime,project_root=R,source_root=S)
for p,pin in watched.items():read(p,pin)
inventory=jread(R/ct.INVENTORY,ct.INVENTORY_SHA)
assert len(inventory['files'])==173
for n,pin in inventory['files'].items():read(R/n,pin);read(S/n,pin)
prefix={}
for name in ('trials.jsonl','closed_loop_report.json','config.json','panel.json'):
    rel=BASE+'/'+name;raw=read(R/rel,inv['root_evidence_sha256'][rel])
    read(P/rel,h(raw));prefix[rel]={'sha256':h(raw),'bytes':len(raw)}
raw=read(R/BASE/'trials.jsonl');assert raw.endswith(b'\n')
lines=raw.splitlines(keepends=True);events=[json.loads(line) for line in lines]
panel=jread(R/BASE/'panel.json');config=jread(R/BASE/'config.json')
assert panel['split']=='development' and panel['suite']=='libero_spatial'
assert len(panel['states'])==100 and Counter(x['task_id'] for x in panel['states'])=={i:10 for i in range(10)}
methods=inv['method_ids'];assert methods==['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17']
assert [m['identity']['method_id'] for m in config['manifest']['methods']]==methods
expected=[]
for state in panel['states']:
    for mid in methods:
        expected.append(dict(trial_id=state['trial_id']+':'+mid,state_trial_id=state['trial_id'],method=mid,suite=panel['suite'],split=panel['split'],task_id=state['task_id'],task_name=state['task_name'],initial_state_sha256=state['initial_state_sha256'],source_state_index=state['source_state_index'],environment_seed=0,runtime_seed=17,configured_wait_steps=10,action_chunk=8))
byid={x['trial_id']:x for x in expected};assert len(byid)==600
active=set();terminal={};invocations=[]
for ln,(line,event) in enumerate(zip(lines,events),1):
    assert event['run_signature']=='11e73bfd7978504ba108058445f1e219f3b0810516a9f28564783df21f980096'
    if event['event']=='invocation':
        assert event['slurm_job_id']=='3022743';invocations.append(event);continue
    tid=event['trial_id'];assert tid in byid
    assert all(event.get(k)==v for k,v in byid[tid].items())
    if event['event']=='start':
        assert tid not in active and tid not in terminal;active.add(tid)
    elif event['event']=='result':
        assert tid in active and tid not in terminal;active.remove(tid)
        assert event['status'] in ('completed','policy_error')
        terminal[tid]=dict(trial_id=tid,method=event['method'],task_id=event['task_id'],source_state_index=event['source_state_index'],status=event['status'],success=event['success'],line=ln,line_sha256=h(line))
    else:raise AssertionError('unexpected prefix event '+event['event'])
assert not active and len(invocations)==1 and len(terminal)==12
remaining=[x for x in expected if x['trial_id'] not in terminal]
assert len(remaining)==588 and len({x['trial_id'] for x in remaining})==588
assert not (set(terminal)&{x['trial_id'] for x in remaining})
root=jread(R/inv['prior_review'])
assert root['completed_trials']==12 and root['scientific_complete'] is False
assert inv['prior_allocation_cost']==[{'elapsed_seconds':393,'exit_code':'0:0','gpus':1,'job_id':'3022743','raw_status':'COMPLETED','status':'COMPLETED'}]
assert inv['resume'] is True and inv['stop_after'] is None
assert inv['argv'][-1]=='--resume' and '--stop-after' not in inv['argv']
refs={}
refs['runtime_contract']=put('runtime_contract.json',runtime)
refs['duplicate_check']=put('duplicate_and_prefix_check.json',dict(schema='formal_main_v2',kind='actual_development_continuation_duplicate_check',status='passed_readonly',stage_key=inv['stage_key'],run_root=inv['run_root'],prior_review=inv['prior_review'],prior_cost_GPU_seconds=393,expected_trials=600,prior_terminal_trials=12,prior_statuses=dict(Counter(x['status'] for x in terminal.values())),pending_trials=588,unique_initial_states=100,observed_initial_states=2,terminal_trials_repeated=False,prior_outcomes_replaced=False,initial_state_values_exported=False,files=prefix,terminal_rows=list(terminal.values()),remaining_trials=remaining,method_identities=[m['identity'] for m in config['manifest']['methods']],scientific_inputs_synthetic=False))
for p,pin in list(readmap.items()):assert h(safe(p).read_bytes())==pin,('drift',p)
refs['evidence']=put('runtime_and_prefix_readonly_evidence.json',dict(schema='formal_main_v2',kind='actual_runtime_and_prefix_preparation',status='passed_readonly_not_activation',created_utc=datetime.now(timezone.utc).isoformat(),read_evidence_sha256=readmap,outputs=refs,root_and_snapshot_frozen_source_count=173,scientific_inputs_synthetic=False,new_GPU_jobs=0,published_to_P=False,production_state_modified=False,allowed_stages=['development'],forbidden_stages=['collect','full','components','final','global_freeze'],old_new_outcome_equivalence_established=False))
print(json.dumps(refs,sort_keys=True))

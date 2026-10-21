from pathlib import Path
import ast,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_remaining5_runtime_20261021T0449'
Q=D/'package';O=R/'scripts/ops/formal_goal_full200_gate_v1'
def put(name,text):
 p=Q/name
 with p.open('x',encoding='utf8') as f:f.write(text)
 return hashlib.sha256(p.read_bytes()).hexdigest()
scope=r'''"""Exact immutable remaining-five contexts. No old module global mutation."""
from pathlib import Path
from types import SimpleNamespace
import hashlib,json,re
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
PKG='scripts/ops/formal_goal_remaining5_gate_v1'
VERSION='goal-remaining5-prospective-single-attempt-v1'
KEYS=('libero_goal_k256_seed23','libero_goal_k256_seed41','libero_goal_k64_seed17','libero_goal_k64_seed23','libero_goal_k64_seed41')
SOURCE_FILES=('scope.py','entry.py','storage.py','observer_v3.py','ast_observer_v2.py','paired_input_gate_v1.py','ast_gate_v2.py','consumer.py','run.slurm','registry.json')
PACKAGE_FILES={PKG+'/'+n for n in SOURCE_FILES}|{PKG+'/pairs/'+k+'/'+n for k in KEYS for n in ('config.json','specification.json')}
REGISTRY_SHA='__REGISTRY_SHA_PENDING__'
def require(v,m):
 if not v:raise ValueError(m)
def pinned(path,pin):
 b=Path(path).read_bytes();require(hashlib.sha256(b).hexdigest()==pin,'exact immutable context source differs: '+str(path));return json.loads(b)
def paths(key):
 require(key in KEYS,'only five named Goal pairs')
 x='results/formal_main_v2/execution/goal_remaining5_v1/'+key
 raw=R/'results/formal_main_v2/raw_runtime/goal_remaining5_v1'/key/'attempt01'
 return dict(stage_key='goal_remaining5_v1/'+key,X=x,BASE=P/x,OUTPUT=P/x/'attempt01',RAW=raw,RUN=x+'/attempt01/original_run')
def context(pair_key):
 require(type(pair_key) is str and pair_key in KEYS,'unknown remaining5 pair')
 registry=pinned(Path(__file__).parent/'registry.json',REGISTRY_SHA)
 require(registry['version']==VERSION and tuple(registry['pair_keys'])==KEYS and set(registry['pairs'])==set(KEYS),'exact five registry')
 slot=registry['pairs'][pair_key];c=pinned(Path(__file__).parent/'pairs'/pair_key/'config.json',slot['config_sha256'])
 tokens,seed=map(int,re.fullmatch(r'libero_goal_k(256|64)_seed(17|23|41)',pair_key).groups())
 pd=paths(pair_key);methods=['A'+str(tokens)+'_seed'+str(seed),'B'+str(tokens)+'_seed'+str(seed)]
 obj=SimpleNamespace(**pd,pair_key=pair_key,seed=seed,tokens=tokens,methods=methods,config=c,config_sha=slot['config_sha256'],spec_sha=slot['specification_sha256'],
  CONFIG=P/PKG/'pairs'/pair_key/'config.json',SPEC=P/PKG/'pairs'/pair_key/'specification.json',ENTRY=P/PKG/'entry.py',MANIFEST=P/PKG/'package_manifest.json',
  root_decision=registry['root_fixed_design'],storage_decision=registry['root_storage_decision'],
  AUTH=pd['BASE']/'root_authorization.json',DISPATCH=pd['BASE']/'held_dispatch_record.json',RESERVATION=pd['BASE']/'reservation.json',
  ORIGINAL=Path(c['planned_invocation_path']),plans=c['plans'])
 return obj
'''
# Registry SHA is replaced once during the final plans/decision binding step.
put('scope.py.in',scope)
storage=r'''"""All-five conservative two-root capacity; one own attempt claim, no deletion."""
from pathlib import Path
import os,hashlib,json
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
KEYS=('libero_goal_k256_seed23','libero_goal_k256_seed41','libero_goal_k64_seed17','libero_goal_k64_seed23','libero_goal_k64_seed41')
MAX_CAPTURE_EVENTS=21032
MAX_OBSERVATION_BYTES=393288
MAX_RNG_BLOB_BYTES=65536
MAX_SIM_BYTES_PER_CAPTURE=8192
MAX_CAPTURE_EVENT_BYTES=16384
MAX_GATE_EVENTS=68032
MAX_GATE_EVENT_BYTES=16384
MAX_RESULT_ROW_BYTES=4194304
MAX_CLEANUP_ROW_BYTES=65536
MAX_START_ROW_BYTES=4096
MAX_RUNTIME_LOG_BYTES=2147483648
BOOTSTRAP_LOG_BUDGET_BYTES=4294967296
P_UPPER_BYTES=200*(MAX_RESULT_ROW_BYTES+MAX_CLEANUP_ROW_BYTES+MAX_START_ROW_BYTES)+2*16777216+16777216+16777216+1024*65536+16777216
P_MARGIN_BYTES=134217728
R_UPPER_BYTES=MAX_CAPTURE_EVENTS*(MAX_OBSERVATION_BYTES+MAX_RNG_BLOB_BYTES+MAX_SIM_BYTES_PER_CAPTURE+MAX_CAPTURE_EVENT_BYTES)+MAX_GATE_EVENTS*MAX_GATE_EVENT_BYTES+2*MAX_RUNTIME_LOG_BYTES+BOOTSTRAP_LOG_BUDGET_BYTES
R_MARGIN_BYTES=1073741824
P_REQUIRED_BYTES=P_UPPER_BYTES+P_MARGIN_BYTES
R_REQUIRED_BYTES=R_UPPER_BYTES+R_MARGIN_BYTES
assert (P_UPPER_BYTES,P_REQUIRED_BYTES,R_UPPER_BYTES,R_REQUIRED_BYTES)==(1003782144,1137999872,19871439680,20945181504)
OBS_SCHEMA={'agentview_image':('uint8',[256,256,3],196608),'robot0_eye_in_hand_image':('uint8',[256,256,3],196608),'robot0_eef_pos':('float64',[3],24),'robot0_eef_quat':('float64',[4],32),'robot0_gripper_qpos':('float64',[2],16)}
def require(ok,msg):
 if not ok:raise ValueError(msg)
def paths(key):
 require(key in KEYS,'exact five capacity scope')
 return R/'results/formal_main_v2/raw_runtime/goal_remaining5_v1'/key/'attempt01',P/'results/formal_main_v2/execution/goal_remaining5_v1'/key/'attempt01'
def ancestor(path):
 path=Path(path);require(path.is_absolute() and path.resolve()==path,'exact absolute storage path required')
 for node in [path,*path.parents]:require(not node.is_symlink(),'storage symlink forbidden')
 q=path
 while not q.exists():q=q.parent
 require(q.is_dir() and q.stat().st_uid==os.getuid() and os.access(q,os.W_OK|os.X_OK),'storage ancestor ownership/write permissions differ')
 return q
def inspect(path,required):
 q=ancestor(path);s=os.statvfs(q);return {'path':str(path),'existing_ancestor':str(q),'owner_uid':q.stat().st_uid,'free_bytes':s.f_bavail*s.f_frsize,'required_bytes':required,'st_dev':q.stat().st_dev,'symlink':False,'writable':True}
def verify_storage(ctx,*,must_be_fresh=True,aggregate_pair_keys=KEYS):
 require(type(must_be_fresh) is bool and tuple(aggregate_pair_keys)==KEYS,'whole five budget cannot be narrowed')
 require(ctx.pair_key in KEYS and (ctx.RAW,ctx.OUTPUT)==paths(ctx.pair_key),'exact context paths required')
 if must_be_fresh:require(not ctx.RAW.exists() and not ctx.OUTPUT.exists(),'own once-only claim already exists')
 probes=[];bydev={}
 for key in KEYS:
  raw,out=paths(key)
  for p,n in ((raw,R_REQUIRED_BYTES),(out,P_REQUIRED_BYTES)):
   row=inspect(p,n);probes.append(row);bydev.setdefault(row['st_dev'],[]).append(row)
 checks=[]
 for dev,rows in sorted(bydev.items()):
  need=sum(v['required_bytes'] for v in rows);free=min(v['free_bytes'] for v in rows)
  require(free>=need,'whole-five conservative filesystem capacity insufficient')
  checks.append({'st_dev':dev,'required_bytes':need,'free_bytes':free})
 own={v['path']:v for v in probes}
 return {'version':'goal-remaining5-dual-root-budget-v1','aggregate_pair_keys':list(KEYS),'raw':own[str(ctx.RAW)],'local':own[str(ctx.OUTPUT)],'all_paths':probes,'filesystem_checks':checks,'raw_upper_bytes':R_UPPER_BYTES,'local_upper_bytes':P_UPPER_BYTES,'R_required_per_pair':R_REQUIRED_BYTES,'P_required_per_pair':P_REQUIRED_BYTES,'R_aggregate_required':5*R_REQUIRED_BYTES,'P_aggregate_required':5*P_REQUIRED_BYTES,'no_dedup_credit':True,'no_expected_release_credit':True,'quota_not_proven':True,'filesystem_space_can_change_after_check':True,'exclusive_claim_required_at_execution':True,'new_storage_paths_created':False}
def claim_raw(ctx):
 verify_storage(ctx)
 ctx.RAW.parent.mkdir(parents=True,exist_ok=True);ancestor(ctx.RAW.parent);ctx.RAW.mkdir(exist_ok=False)
 require(ctx.RAW.stat().st_uid==os.getuid() and ctx.RAW.resolve()==ctx.RAW,'exclusive raw claim')
 proof={'version':'goal-remaining5-raw-exclusive-claim-v1','pair_key':ctx.pair_key,'path':str(ctx.RAW),'pid':os.getpid(),'job_id':os.environ['SLURM_JOB_ID'],'purpose':'five raw development observations, passive simulator/RNG payload, observer/gate journals and own runtime logs for this attempt only','old200_HOLD':True,'new_scientific_trials_accepted':0}
 with (ctx.RAW/'claim.json').open('x') as f:json.dump(proof,f,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
 return proof
'''
put('storage.py',storage)
gate=(O/'paired_input_gate_v1.py').read_text()
gate=gate.replace("PREFIX='specification.json'\nPREFIX_SHA='ed0b59bd1acbdab34658f5599f4969aa745e596348bf25d230a38c978aa652ad'\n","")
gate=gate.replace("VERSION='goal-full200-before-policy-integrity-v1'","VERSION='goal-remaining5-before-policy-integrity-v1'")
a=gate.index('def fixed_prefix():');b=gate.index('\ndef identity_signature',a)
gate=gate[:a]+'''def fixed_prefix(ctx):
 p=R/'pairs'/ctx.pair_key/'specification.json';raw=p.read_bytes()
 if sha(raw)!=ctx.spec_sha:raise ValueError('exact pair original full200 identity table changed')
 rows=json.loads(raw)['rows']
 if len(rows)!=200 or [r['method'] for r in rows]!=ctx.methods*100:raise ValueError('exact pair method/order required')
 return rows
'''+gate[b:]
gate=gate.replace('def __init__(self,output,*,allow_cpu_fixture=False,sink=None,raw_observation_root=None):','def __init__(self,ctx,output,*,allow_cpu_fixture=False,sink=None,raw_observation_root=None):')
gate=gate.replace('super().__init__(output,fixed_prefix(),','self.context=ctx\n  super().__init__(output,fixed_prefix(ctx),')
gate=gate.replace("expected_raw=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/results/formal_main_v2/raw_runtime/goal_full200_20261021T0110/attempt01')","expected_raw=ctx.RAW")
gate=gate.replace("'prefix_sha256':PREFIX_SHA","'prefix_sha256':ctx.spec_sha,'pair_key':ctx.pair_key")
gate=gate.replace("self.current['method']=='A256_seed17'","self.current['method']==self.context.methods[0]").replace("self.current['method']=='B256_seed17'","self.current['method']==self.context.methods[1]")
idx=gate.index(' def trial_end(')
gate=gate[:idx]+''' def guard_ledger_event(self,row,ledger):
  # Same encoding as frozen TrialLedger.append; never mutate, truncate or replace.
  def go():
   before=recorder.object_guard(row);rng=recorder.global_rng()
   kind=row.get('event');limits={'start':4096,'result':4194304,'cleanup_error':65536}
   self._need(kind in limits,'unknown original ledger event')
   encoded=(json.dumps({**row,'run_signature':ledger.run_signature},ensure_ascii=False,sort_keys=True,allow_nan=False)+'\\\\n').encode('utf8')
   self._need(len(encoded)<=limits[kind],'original ledger row exceeds prewrite storage bound',event_kind=kind,encoded_bytes=len(encoded),bound=limits[kind])
   self._need(recorder.object_guard(row)==before and recorder.global_rng()==rng,'row serialization guard changed original input/RNG')
  return self._call(go)
'''+gate[idx:]
put('paired_input_gate_v1.py',gate)
astgate=(O/'ast_gate_v2.py').read_text()
# New exact trial observer layout: prewrite guard original dict is evaluated once.
insert=r'''
LEDGER_TEMP='_cti_prefix_ledger_event'
def derive_trials(raw):
 base.require(sha(raw)==base.TRIALS_SHA,'unregistered formal trial source')
 original=base.function_node(raw,'evaluate_formal_trials');derived=copy.deepcopy(original)
 for expr in ('{**identity, "event": "start", "created_utc": datetime.now(timezone.utc).isoformat()}','{**identity, "event": "cleanup_error", "error": str(exc)}'):
  target='ledger.append('+expr+')'
  base.replace_statement(derived,target,[base.parse_stmt(LEDGER_TEMP+' = '+expr),base.parse_stmt(base.NAME+'.guard_ledger_event('+LEDGER_TEMP+', ledger)'),base.parse_stmt('ledger.append('+LEDGER_TEMP+')'),base.parse_stmt('del '+LEDGER_TEMP)])
 base.surround(derived,'ledger.append(row)',before=[base.NAME+'.guard_ledger_event(row, ledger)'])
 # Start hook remains after the exact original append, not before reseeding.
 base.surround(derived,'del '+LEDGER_TEMP,after=[]) if False else None
 # There are two delete-temp sites; select the original start block structurally.
 found=[]
 for node in ast.walk(derived):
  for _,items in ast.iter_fields(node):
   if isinstance(items,list):
    for i,item in enumerate(items):
     if isinstance(item,ast.Assign) and len(item.targets)==1 and isinstance(item.targets[0],ast.Name) and item.targets[0].id==LEDGER_TEMP and 'created_utc' in base.text(item.value):
      found.append((items,i))
 base.require(len(found)==1,'unique start guard')
 items,i=found[0];items.insert(i+4,base.parse_stmt(base.NAME+'.trial_begin(identity, state)'))
 base.surround(derived,'reseed()',after=[base.NAME+'.capture("reseed_after")'])
 base.surround(derived,'env, instruction = environment_factory(state)',before=[base.NAME+'.capture("factory_before")'],after=[base.NAME+'.capture("factory_after", env)'])
 base.surround(derived,'if result["status"] == "infrastructure_error":\n    raise RuntimeError("formal infrastructure attempt retained; repair and resume same trial")',before=[base.NAME+'.trial_end(row, ledger)'])
 ast.fix_missing_locations(derived);return original,derived,base.assert_projection(original,derived)
def restore_ledger_blocks(node):
 # Every erased expression is additionally protected by the complete layout SHA.
 for parent in ast.walk(node):
  for field,items in ast.iter_fields(parent):
   if not isinstance(items,list):continue
   i=0
   while i<len(items):
    x=items[i]
    if isinstance(x,ast.Assign) and len(x.targets)==1 and isinstance(x.targets[0],ast.Name) and x.targets[0].id==LEDGER_TEMP:
     base.require(i+3<len(items),'guarded row block truncated')
     expr=x.value
     base.require(base.text(items[i+1])==base.text(base.parse_stmt(base.NAME+'.guard_ledger_event('+LEDGER_TEMP+', ledger)')) and base.text(items[i+2])==base.text(base.parse_stmt('ledger.append('+LEDGER_TEMP+')')) and base.text(items[i+3])==base.text(base.parse_stmt('del '+LEDGER_TEMP)),'prewrite block differs')
     old=base.parse_stmt('ledger.append(None)');old.value.args=[copy.deepcopy(expr)]
     items[i:i+4]=[old]
    i+=1
 return node
'''
astgate=astgate.replace('class StripGate(base.StripObserver):',insert+'\nclass StripGate(base.StripObserver):\n def visit_FunctionDef(self,node):\n  return self.generic_visit(restore_ledger_blocks(node))')
astgate=astgate.replace("('step_after','step_before')","('step_after','step_before','guard_ledger_event')")
astgate=astgate.replace("base.derive_run=derive_run","base.derive_run=derive_run;base.derive_trials=derive_trials")
# Derive exact new layout without disabling any check in the published source.
tmp=astgate.replace("'25361b2db2ff14d26db2222cf9bba430f6207dec5f1caff22478224da7589849'","'__NEW_LAYOUT__'")
# Compile isolated build source with a proof-capture substitution only in memory.
ns={'__file__':str(Q/'ast_gate_v2.py'),'__name__':'_build_layout'}
probe=tmp.replace('ast.fix_missing_locations(derived);return original,derived,base.assert_projection(original,derived)','ast.fix_missing_locations(derived);return original,derived,None')
exec(compile(probe,str(Q/'ast_gate_v2.py')+'::<build-layout-only>','exec'),ns)
_,node,_=ns['derive_trials']((R/'src/cti_vla/evaluation/formal_trials.py').read_bytes())
layout=hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()
put('ast_gate_v2.py',tmp.replace('__NEW_LAYOUT__',layout))
with (D/'core_build_result.json').open('x') as f:json.dump({'new_trial_AST_sha256':layout,'new_files':[p.name for p in Q.iterdir()],'actual_GPU':False,'no_old_source_modification':True},f,indent=2)
print(json.dumps({'new_trial_AST_sha256':layout,'status':'core_private_sources_written'}))

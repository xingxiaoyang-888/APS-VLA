"""Explicit CPU raw-consumer fixtures and actual old source/adapter evidence, never acceptance."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,math,shutil,sys,traceback,types
D=Path(__file__).parent;R=D.parents[1];K=D/'package';P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
O=D/'CPU_consumer_v1';O.mkdir(exist_ok=False);checks=[];rejections=0
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def ck(n,v,detail=None):
 checks.append({'name':n,'passed':bool(v),'detail':detail})
 if not v:raise AssertionError(n)
def neg(n,f):
 global rejections
 try:f()
 except (ValueError,KeyError,AssertionError,IndexError):rejections+=1;ck(n,True)
 else:ck(n,False)
def load(p,n):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def main():
 c=load(K/'consumer.py','g200_consumer_unit');entry=load(K/'entry.py','g200_consumer_entry')
 # Production rejects these actual CPU traces. A separate in-memory function
 # explicitly expects CPU labels and fixture image shape, and only those guards differ.
 src=D/'CPU_full200_v2';fixture=O/'fixture_attempt';fixture.mkdir()
 shutil.copytree(src/'gated',fixture/'observer')
 rawrows=c.jsonl(src/'gated.jsonl');spec=json.loads((K/'specification.json').read_bytes())
 text=(K/'consumer.py').read_text();tree=ast.parse(text);orig=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='reconstruct_gate')
 node=copy.deepcopy(orig);changes=[]
 for n in ast.walk(node):
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)==2 and isinstance(n.args[1],ast.Constant):
   if n.args[1].value=='CPU fixture forbidden':
    changes.append('CPU labels explicitly required instead of production labels')
    n.args[0]=ast.parse("gate[0]['CPU_fixture_enabled'] is True and gate[0]['runtime_context']=='synthetic_CPU_fixture'",mode='eval').body
  if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='expected_schema':
   changes.append('two image dimensions only:3x4x3 uint8 instead of256x256x3')
   new=ast.literal_eval(n.value);new['agentview_image']=('uint8',[3,4,3],36);new['robot0_eye_in_hand_image']=('uint8',[3,4,3],36);n.value=ast.parse(repr(new),mode='eval').body
 ck('exact_two_CPU_fixture_guard_derivations',len(changes)==2)
 ast.fix_missing_locations(node)
 ns={**c.__dict__,'OUT':fixture.relative_to(R).as_posix(),'RAW':src/'gated/CPU_raw_observations'}
 # read_blob retains complete byte/path/hash validation; only exact fixture root differs.
 readblob=types.FunctionType(c.read_blob.__code__,ns,c.read_blob.__name__,c.read_blob.__defaults__,c.read_blob.__closure__);readblob.__kwdefaults__=c.read_blob.__kwdefaults__;ns['read_blob']=readblob
 exec(compile(ast.Module(body=[node],type_ignores=[]),'<CPU-only reconstruction guards>','exec'),ns)
 f=ns['reconstruct_gate'];proof=f(R,rawrows,specification=spec,job_id='CPU_FIXTURE')
 ck('CPU_raw200_100pair_600query_3400step',all(proof[k]==v for k,v in {'trials':200,'paired_t0_checks':100,'queries':600,'control_steps':3400,'warmup_steps':2000}.items()))
 original_with_roots=types.FunctionType(c.reconstruct_gate.__code__,ns,'unmodified_production_reconstruction',c.reconstruct_gate.__defaults__,c.reconstruct_gate.__closure__);original_with_roots.__kwdefaults__=c.reconstruct_gate.__kwdefaults__
 neg('production_rejects_CPU_fixture_unmodified',lambda:original_with_roots(R,rawrows,specification=spec,job_id='CPU_FIXTURE'))
 rawgate=c.jsonl(fixture/'observer/gate.jsonl');rawevents=c.jsonl(fixture/'observer/events.jsonl')
 def reject(name,rows=None,gates=None,events=None):
  previous=ns['jsonl']
  def virtual(path):
   if Path(path)==fixture/'observer/gate.jsonl':return copy.deepcopy(gates if gates is not None else rawgate)
   if Path(path)==fixture/'observer/events.jsonl':return copy.deepcopy(events if events is not None else rawevents)
   return previous(path)
  ns['jsonl']=virtual
  try:neg(name,lambda:f(R,copy.deepcopy(rawrows if rows is None else rows),specification=spec,job_id='CPU_FIXTURE'))
  finally:ns['jsonl']=previous
 bad=copy.deepcopy(rawrows);next(r for r in bad if r['event']=='result')['status']='policy_error';reject('policy_error_not_completion',rows=bad)
 reject('58_prefix_not200',rows=[r for r in rawrows if r['trial_id'] in {x['trial_id'] for x in spec['rows'][:58]}])
 bad=copy.deepcopy(rawrows);rr=next(r for r in bad if r['event']=='result');rr['executed_actions'][0][0]+=1;reject('changed_original_action',rows=bad)
 bad=copy.deepcopy(rawrows);next(r for r in bad if r['event']=='result')['chunks'][0]['environment_actions'][0][0]+=1;reject('changed_returned_chunk',rows=bad)
 bad=copy.deepcopy(rawrows);next(r for r in bad if r['event']=='result')['wait_steps']=9;reject('warmup_separate_exact',rows=bad)
 bad=copy.deepcopy(rawgate);next(r for r in bad if r['event']=='query_integrity_passed')['input_identity_after']['mapping_id']+=1;reject('query_pointer_change',gates=bad)
 bad=copy.deepcopy(rawgate);next(r for r in bad if r['event']=='t0_pair_gate')['instruction_utf8_hex']='00';reject('instruction_raw_hash_change',gates=bad)
 bad=copy.deepcopy(rawgate);next(r for r in bad if r['event']=='t0_pair_gate')['content']['components']['agentview_image']['sha256']='0'*64;reject('pair_component_change',gates=bad)
 bad=copy.deepcopy(rawgate);next(r for r in bad if r['event']=='policy_step_executed')['control_step']=9;reject('queue_cadence_change',gates=bad)
 bad=copy.deepcopy(rawgate);bad[-1]['executed_policy_steps_recorded']-=1;reject('footer_counter_change',gates=bad)
 bad=copy.deepcopy(rawevents);next(r for r in bad if r.get('observation_arrays'))['observation_arrays']['agentview_image']['blob']['path']=str(src/'other.bin');reject('foreign_blob_root',events=bad)
 bad=copy.deepcopy(rawevents);next(r for r in bad if 'phase' in r)['invariants']['global_rng_unchanged']=False;reject('passive_invariant_change',events=bad)
 bad=copy.deepcopy(rawevents);next(r for r in bad if 'phase' in r)['event_index']=4;reject('capture_sequence_change',events=bad)
 bad=copy.deepcopy(rawevents);bad.append({'event':'observer_abort','phase':'failure'});reject('retained_observer_abort',events=bad)
 write(O/'CPU_raw_reconstruction.json',{'status':'passed_explicit_CPU_fixture_algorithm_only','changes':changes,'original_function_AST_sha256':hashlib.sha256(ast.dump(orig,include_attributes=False).encode()).hexdigest(),'derived_function_AST_sha256':hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest(),'proof':proof,'production_function_unmodified':True,'production_admission':False})
 # Run complete original runtime_inputs and adapters on real old58 files.
 # Only synthetic CPU parent envelope and elapsed bound are supplied; no old
 # job/accounting/ledger is changed or represented as a new full200 result.
 inv=json.loads((R/'results/formal_main_v2/invocations/libero_goal_development_5185766bb353c8e6_attempt01.json').read_bytes())
 contract=json.loads((R/inv['action_execution_contract']['path']).read_bytes())
 rv=load(R/'scripts/ops/formal_action_deployment_v1/reviewer.py','g200_old_reviewer_CPU');ev=rv.Evidence(R)
 old=rv.load(ev,'scripts/review_formal_downstream.py',c.PINS['scripts/review_formal_downstream.py']);sched=rv.load(ev,'scripts/ops/formal_downstream_supervisor.py',c.PINS['scripts/ops/formal_downstream_supervisor.py'])
 run='results/formal_main_v2/engineering/goal_paired_input_gate_20261020T2156/attempt01/original_run'
 config=ev.read(run+'/config.json');source=ev.read(Path(inv['source_inventory']).relative_to(P).as_posix())
 sys.path.insert(0,str(R/'src'));from cti_vla.training.formal_future import formal_source_hashes
 value={'invocation':{**inv,'run_root':str(P/run),'wrapper_sha256':sha(K/'entry.py')},'opt':old.options(inv),'registration':ev.read('configs/experiments/formal_main_v2.json'),'suite':'libero_goal','manifest':ev.read(Path(inv['execution_manifest']).relative_to(P).as_posix()),'inventory':source,'sources':formal_source_hashes(R),'development':ev.read(run+'/panel.json'),'methods':['A256_seed17','B256_seed17'],'output':run}
 baseidentity=old.runtime_inputs(ev,sched,value,config);ck('full_original_runtime_inputs_actual_old58',baseidentity['file_count']>0)
 artifacts=sorted((P/'results/formal_main_v2/adapter_invocations').glob('3054127_*'));ck('exact_actual_old_adapter_pair',len(artifacts)==2)
 receipt=json.loads(next(p for p in artifacts if p.suffix=='.json').read_bytes())
 allowed={p.relative_to(P).as_posix():p for p in artifacts};files={n:sha(p) for n,p in allowed.items()}
 cp=R/'results/formal_main_v2/engineering/goal_paired_input_gate_20261020T2156/attempt01/outer/completion.json';complete=json.loads(cp.read_bytes())
 parent={'wrapper_sha256':sha(K/'entry.py'),'stage_completed_claimed':False,'wall_seconds':complete['wall_seconds'],'status':'returned','exit_code':0,
 'adapter_artifacts':[{'path':str(p)} for p in artifacts],'adapter_receipts':[{'path':str(next(p for p in artifacts if p.suffix=='.json')),'status':receipt['status'],'runner_status':receipt.get('runner_status')}]}
 class CPUReadOnlyOldAdapterEvidence(rv.Evidence):
  def path(self,v):
   if str(v) in allowed:return allowed[str(v)]
   return super().path(v)
  def read(self,v):
   if v=='__explicit_CPU_parent__':return copy.deepcopy(parent)
   return super().read(v)
 testev=CPUReadOnlyOldAdapterEvidence(R)
 n=next(n for n in ast.parse((R/'scripts/review_formal_downstream.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='adapters');q=copy.deepcopy(n)
 target=next(x for x in q.body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id=='wrapper');target.value=ast.parse("evidence.read('__explicit_CPU_parent__')",mode='eval').body;ast.fix_missing_locations(q)
 space=dict(old.__dict__);exec(compile(ast.Module(body=[q],type_ignores=[]),'<typed-parent CPU fixture>','exec'),space)
 cpu_job={'job_id':'3054127','mode':'development','status':'COMPLETED','exit_code':'0:0','run_root':str(P/run),'elapsed_seconds':math.ceil(complete['wall_seconds'])+1}
 adapter=space['adapters'](testev,sched,value,cpu_job,config,files)
 ck('complete_original_adapters_rebuilt_actual58_with_explicit_CPU_parent',adapter['status']=='returned' and adapter['job_id']=='3054127')
 runtime=rv.load(ev,'scripts/ops/formal_action_deployment_v1/runtime_scope.py',contract['files']['scripts/ops/formal_action_deployment_v1/runtime_scope.py'])
 analyzer=rv.load(ev,'scripts/analyze_formal.py',c.PINS['scripts/analyze_formal.py']);trajectory,proof2=rv.trajectory_validator(old,analyzer,runtime)
 raw58=rv.lines(ev,run+'/trials.jsonl')
 for row in [r for r in raw58 if r['event']=='result']:trajectory(row)
 ck('accepted_original_trajectory_all58',len([r for r in raw58 if r['event']=='result'])==58)
 # The complete original rollout keeps the original full200 denominator and
 # rejects any attempt to classify this old58 prefix as full200.
 neg('original_rollout_cannot_complete_old58',lambda:rv.clone(old.rollout,trajectory=trajectory)(testev,sched,value,cpu_job,config,adapter))
 write(O/'actual_old_sources_covered.json',{'scope':'CPU typed-parent adapter interface and original scientific primitives only','actual_old58_trials_checked':58,'original_runtime_inputs':baseidentity,'actual_adapter_refs':{n:{'sha256':h,'server_path':str(allowed[n])} for n,h in files.items()},'actual_adapter_returned':True,'CPU_parent_fixture':True,'CPU_elapsed_fixture_not_Slurm_accounting':True,'old58_is_not_full200':True,'trajectory_derivation':proof2,'metadata_files':ev.files,'source_consumer_sha256':sha(K/'consumer.py'),'production_admission':False,'GPU_submissions':0})
 return {'status':'passed_CPU_typed_consumer_components_not_new_terminal','checks':checks,'rejections':rejections,'actual_new_full200_consumer_run':False,'future_actual_raw_original_consumer_required':True,'old200_HOLD':True,'new_scientific_results':0,'GPU_submissions':0,'Slurm_queries':0,'final_release':False}
try:r=main()
except BaseException as e:
 r={'status':'failed','checks':checks,'error':str(e),'type':type(e).__name__,'traceback':traceback.format_exc(),'rejections':rejections};write(O/'report.json',r);print(json.dumps({'status':'failed','error':str(e)}));raise
write(O/'report.json',r);print(json.dumps({'status':r['status'],'checks':len(checks),'rejections':rejections}))

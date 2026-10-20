"""Production outer CPU integration; real loops/native MjData, fixture policy/model loader.

This never calls main successfully or publishes/authorizes/submits. Every outer
execute is isolated by explicit private namespace redirection recorded below.
"""
from pathlib import Path
from types import SimpleNamespace
from contextlib import contextmanager
import ast,copy,hashlib,importlib.util,json,os,random,shutil,sys,traceback
os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['MUJOCO_GL']='egl'
import numpy as np,mujoco
D=Path(__file__).parent;R=D.parents[1];P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
G=P/'scripts/ops/formal_goal_paired_input_gate_v1'

def independent_write_guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','socket.bind'):raise RuntimeError('independent CPU test forbids process/network')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  mode,flags=args[1:3];w=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if w and not p.is_relative_to(D):raise RuntimeError('independent test output outside private root')
sys.dont_write_bytecode=True;sys.addaudithook(independent_write_guard)

OUT=D/'independent_outer';OUT.mkdir(exist_ok=False);checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):
 with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def ck(n,v,detail=None):
 checks.append({'name':n,'passed':bool(v),'detail':detail})
 if not v:raise AssertionError(n)
def load(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def rejects(n,fn):
 try:fn()
 except ValueError:ck(n,True)
 else:ck(n,False)
entry=load(G/'entry.py','goal_paired_outer_under_CPU_test');gate=load(G/'paired_input_gate_v1.py','goal_paired_fixture_helpers')
sys.path.insert(0,str(S/'src'))
from cti_vla.evaluation import libero_runtime as runtime,formal_trials as trials
accepted=load(P/'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py','goal_actual_action_adapter_for_CPU_outer')
# Reuse the exact prior fixture class/function AST, never copy its policy into production.
prior=R/'.local/goal_cpu_gate_20261020T2054/cpu_check_v1.py';ck('prior_fixture_source_pin',sha(prior)=='8a6cc29c77d890285be69c752d714b2e40b7c8bbc07df2992d349daf1a530e0a')
mainnode=next(x for x in ast.parse(prior.read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='main')
fixture_nodes=[x for x in mainnode.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name in ('Env','Policy','reseed','canon')]
ck('four_explicit_fixture_definitions',len(fixture_nodes)==4)
exec(compile(ast.Module(body=fixture_nodes,type_ignores=[]),str(prior)+'::<four-fixture-definitions>','exec'),globals())
model=mujoco.MjModel.from_xml_string('<mujoco><worldbody><body><joint name="j" type="slide"/><geom type="sphere" size="0.1" mass="1"/></body></worldbody></mujoco>')
class NativeCPUEnv(Env):
 def __init__(self,trace,*,mismatch=None,cleanup_error=False):
  super().__init__(trace,mismatch=mismatch);self.cleanup_error=cleanup_error
  data=mujoco.MjData(model);mujoco.mj_forward(model,data)
  self.env.sim.data=SimpleNamespace(_data=data,time=0.,qpos=data.qpos)
 def close(self):
  super().close()
  if self.cleanup_error:raise RuntimeError('explicit synthetic cleanup error')
def main():
 package=json.loads((G/'package_manifest.json').read_text());manifest_sha=sha(G/'package_manifest.json');config=json.loads((G/'config.json').read_text());config_sha=sha(G/'config.json');entry_sha=sha(G/'entry.py')
 ck('all_package_bytes_exact',set(package['files'])==entry.PACKAGE_FILES and all(sha(G/Path(p).name)==h for p,h in package['files'].items()))
 entry.validate_config(config)
 for field,value in [('seed',23),('tokens',128),('maximum_trials',59),('wait_steps',9),('action_chunk',4),('maximum_attempts',2),('original200_HOLD',False),('new_Goal_science_HOLD',False),('automatic_retry',True),('historical_actions_forced',True),('output','/tmp/other')]:
  bad=copy.deepcopy(config);bad[field]=value;rejects('config_reject_'+field,lambda bad=bad:entry.validate_config(bad))
 bad=copy.deepcopy(config);bad['resources']['no_requeue']=False;rejects('config_reject_requeue',lambda:entry.validate_config(bad))
 rejects('private_main_cannot_execute',lambda:entry.main(['--authorization',str(entry.AUTH),'--authorization-sha256','a'*64]))
 # Pure in-memory validator fixtures. They are never saved as root authorizations.
 auth={'schema':'formal_main_v2','kind':'root_goal_prefix58_single_attempt_authorization','version':entry.VERSION,'status':'approved','reviewed_by':'root','stage_key':entry.STAGE,'config_sha256':config_sha,'package_manifest_sha256':manifest_sha,'entrypoint_sha256':entry_sha,'maximum_gpu_jobs':1,'maximum_attempts':1,'maximum_wall_seconds':1800,'counts_against_8_GPU_slots':True,'automatic_retry':False,'scientific_release':False,'original_goal200_HOLD':True,'new_Goal_science_HOLD':True,'maximum_trials':58,'resources':entry.RESOURCES,'dispatch_record_path':str(entry.DISPATCH),'reservation_path':str(entry.RESERVATION),'root_review':{'path':str(entry.BASE/'root_readiness.json'),'sha256':'b'*64},'independent_review':{'path':str(entry.BASE/'independent_readiness.json'),'sha256':'c'*64}}
 entry.validate_authorization(auth,config_sha,manifest_sha,entry_sha);ck('new_authorization_validator_positive_CPU_fixture',True)
 for field,value in [('version','goal-prefix58-single-attempt-v2'),('stage_key','goal_prefix58_20261020T1825'),('maximum_gpu_jobs',2),('maximum_attempts',2),('scientific_release',True),('config_sha256','e'*64),('maximum_wall_seconds',3600),('automatic_retry',True)]:
  bad=copy.deepcopy(auth);bad[field]=value;rejects('auth_reject_'+field,lambda bad=bad:entry.validate_authorization(bad,config_sha,manifest_sha,entry_sha))
 bad=copy.deepcopy(auth);bad['independent_review']=bad['root_review'];rejects('auth_reject_same_review',lambda:entry.validate_authorization(bad,config_sha,manifest_sha,entry_sha))
 review={'schema':'formal_main_v2','kind':'goal_prefix58_single_attempt_CPU_readiness','status':'passed','reviewed_by':'root','version':entry.VERSION,'package_manifest_sha256':manifest_sha,'config_sha256':config_sha,'original_chain_preserved':True,'observer_gaps_fixed':True,'paired_input_gate_CPU_passed':True,'pre_policy_pair_equality_gate':True,'all_query_input_integrity_gate':True,'original_policy_error_retained_then_halt':True,'real_GPU_acceptance':False,'scientific_release':False}
 entry.check_review(review,'root',manifest_sha,config_sha);ck('new_readiness_positive_CPU_fixture',True)
 for field in ('paired_input_gate_CPU_passed','pre_policy_pair_equality_gate','all_query_input_integrity_gate','original_policy_error_retained_then_halt'):
  bad=copy.deepcopy(review);bad.pop(field);rejects('readiness_missing_'+field,lambda bad=bad:entry.check_review(bad,'root',manifest_sha,config_sha))
 authsha='d'*64;job='999999';ressha='f'*64
 dispatch={'schema':'formal_main_v2','kind':'root_goal_prefix58_held_dispatch','status':'held_registered_before_release','stage_key':entry.STAGE,'job_id':job,'authorization':{'path':str(entry.AUTH),'sha256':authsha},'request_token':'cti-goal-paired-input-v1:'+authsha,'capacity_limit_all_GPU_modes':8,'reserved_slots':1,'maximum_attempts':1,'new_submissions':1,'no_requeue':True,'scientific_release':False,'resources':entry.RESOURCES,'occupied_job_ids':[job],'state_after_sha256':'0'*64,'reservation':{'path':str(entry.RESERVATION),'sha256':ressha}}
 reservation={'schema':'formal_main_v2','kind':'root_goal_prefix58_GPU_slot_reservation','status':'approved_for_exact_prefix58','stage_key':entry.STAGE,'authorization':dispatch['authorization'],'reserved_slots':1,'capacity_limit_all_GPU_modes':8,'maximum_wall_seconds':1800,'automatic_retry':False,'scientific_release':False}
 entry.validate_dispatch(dispatch,reservation,auth,authsha,job,ressha);ck('new_held_dispatch_positive_CPU_fixture',True)
 for field,value in [('request_token','cti-goal-prefix58-v2:'+authsha),('job_id','999998'),('occupied_job_ids',[job,job]),('occupied_job_ids',[str(i) for i in range(8)]+[job]),('occupied_job_ids',[]),('new_submissions',2),('no_requeue',False),('state_after_sha256',None)]:
  bad=copy.deepcopy(dispatch);bad[field]=value;rejects('dispatch_reject_'+field+str(value),lambda bad=bad:entry.validate_dispatch(bad,reservation,auth,authsha,job,ressha))
 for field,value in [('stage_key','goal_prefix58_20261020T1825'),('reserved_slots',2),('automatic_retry',True)]:
  bad=copy.deepcopy(reservation);bad[field]=value;rejects('reservation_reject_'+field,lambda bad=bad:entry.validate_dispatch(dispatch,bad,auth,authsha,job,ressha))
 inv=json.loads(entry.ORIGINAL.read_text());panel=json.loads((Path(inv['run_root'])/'panel.json').read_text());prefix=gate.fixed_prefix()
 @contextmanager
 def imports(source):
  ck('fixture_still_targets_exact_frozen_S',source==S);yield
 legacy_holder=SimpleNamespace(source_imports=imports)
 entry.validate_prefix(inv,legacy_holder,prefix)
 bad=copy.deepcopy(prefix);bad[0],bad[1]=bad[1],bad[0];rejects('prefix_reject_B_before_A',lambda:entry.validate_prefix(inv,legacy_holder,bad))
 # Isolate only outer filesystem namespace and original-model-loading call.
 # Entry source and frozen loops remain exact. No checkpoint/model runs here.
 privateP=OUT/'private_production_namespace';privatePkg=privateP/entry.PKG;privatePkg.mkdir(parents=True)
 for p in (G).iterdir():shutil.copyfile(p,privatePkg/p.name)
 entry.P=privateP
 original_runtime=(runtime.run_episode,trials.evaluate_formal_trials);attempts=[]
 def make_context(name,kind=None,mutation=None,at=1):
  trace=[];policies={m:Policy(trace,mutation=mutation if m=='A256_seed17' else None,at=at) for m in ('A256_seed17','B256_seed17')};counter=[0];ledgers=[]
  def factory(state):
   counter[0]+=1;second=counter[0]==2
   if kind=='environment_exception':raise RuntimeError('synthetic factory failure')
   trace.append(('factory',state['task_id'],state['source_state_index']))
   return NativeCPUEnv(trace,mismatch=kind if second and kind in ('bytes','dtype','shape') else None,cleanup_error=kind=='cleanup_error'),('other instruction' if second and kind=='instruction' else 'fixed instruction')
  def actual_frozen_loop_runner(a,**kwargs):
   ck(name+'_original_runner_kwargs',kwargs==dict(mode='evaluate',source_root=S,source_inventory=Path(inv['source_inventory']),adapter_sha256=entry.LSHA,resume=False))
   Path(a.output).mkdir(exist_ok=False);ledger=runtime.TrialLedger(Path(a.output)/'trials.jsonl',run_signature='a'*64);ledgers.append(ledger)
   return trials.evaluate_formal_trials(panel,policies,ledger,factory,reseed=reseed,stop_after=a.stop_after)
  def contexts(fn,*,project_root,source_root,contract,asset_contract,emit):
   ck(name+'_runtime_inputs_preserved',source_root==S and contract=={'CPU_fixture_model_loader':True})
   with accepted.install_action_execution_compat(project_root=P,source_root=S,runtime_module=runtime,formal_trials_module=trials,expected_adapter_sha256='b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185',emit=emit):return fn()
  def verify(events,*args,**kwargs):
   ck(name+'_runtime_restored_before_completion',original_runtime==(runtime.run_episode,trials.evaluate_formal_trials))
   return {'all_source_and_binding_contexts_restored':True,'CPU_fixture_runtime_assets_not_real_model_loader':True}
  rt=SimpleNamespace(expected_asset_identities=lambda **kwargs:{'CPU_fixture':True},run_with_asset_contexts=contexts,verify_runtime_events=verify)
  legacy=SimpleNamespace(run=actual_frozen_loop_runner,source_imports=imports,code_sha=lambda fn:hashlib.sha256(repr(fn.__code__.co_code).encode()).hexdigest())
  ctx={'args':SimpleNamespace(output=Path(inv['run_root']),stop_after=None),'runtime':rt,'execution_contract':{'runtime_contract':{'CPU_fixture_model_loader':True}},'original_plan':{'invocation':{}}}
  return legacy,ctx,trace,policies,counter,ledgers
 # Baseline executes same original accepted actions and loops without observer.
 baseline_trace=[];baseline_q={m:Policy(baseline_trace) for m in ('A256_seed17','B256_seed17')};baseline_ledger=runtime.TrialLedger(OUT/'baseline.jsonl',run_signature='a'*64)
 def baseline_factory(state):baseline_trace.append(('factory',state['task_id'],state['source_state_index']));return NativeCPUEnv(baseline_trace),'fixed instruction'
 with accepted.install_action_execution_compat(project_root=P,source_root=S,runtime_module=runtime,formal_trials_module=trials,expected_adapter_sha256='b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185',emit=lambda *args,**kwargs:None):
  trials.evaluate_formal_trials(panel,baseline_q,baseline_ledger,baseline_factory,reseed=reseed,stop_after=58)
 baseline_rng=gate.recorder.global_rng()
 for name,kind,mutation,at in [('success',None,None,1),('B_bytes','bytes',None,1),('B_instruction','instruction',None,1),('mutation0',None,'bytes',1),('mutation1',None,'bytes',2),('policy_exception',None,'exception',1),('cleanup','cleanup_error',None,1),('factory_error','environment_exception',None,1)]:
  legacy,ctx,trace,policies,counter,ledgers=make_context(name,kind,mutation,at)
  entry.OUTPUT=OUT/name;entry.prepare_original=lambda legacy=legacy,ctx=ctx:(inv,None,ctx,legacy)
  rc=entry.execute(config,{},'CPU_ONLY_'+name,package,{'auth_sha':'CPU_fixture_not_authorization','manifest_sha':manifest_sha})
  result=json.loads((entry.OUTPUT/'outer/completion.json').read_bytes());rows=ledgers[0].events if ledgers else[];original_rows=[r for r in rows if r.get('event')=='result']
  ck(name+'_returned_expected_code',rc==(0 if name=='success' else 1))
  ck(name+'_retains_HOLD_no_science',result['original_goal200_HOLD'] and result['new_Goal_science_HOLD'] and result['scientific_trials_added']==0 and not result['automatic_retry'])
  ck(name+'_all_code_bindings_restored',original_runtime==(runtime.run_episode,trials.evaluate_formal_trials))
  ck(name+'_durable_completion_and_original_rows',result['raw_event_sha256']==sha(entry.OUTPUT/'outer/events.jsonl') and (entry.OUTPUT/'original_run/trials.jsonl').exists())
  first=json.loads((entry.OUTPUT/'observer/gate.jsonl').read_text().splitlines()[0]);ck(name+'_real_entry_has_no_CPU_fixture',first['CPU_fixture_enabled'] is False and first['runtime_context']=='real_environment_engineering' and 'GPU_authorized' not in first)
  if name=='success':
   ck('outer_full58_29_pairs',result['observer_finished']==58 and result['paired_t0_checks_retained']==29 and result['accepted_queries_retained']==174 and result['executed_policy_steps_retained']==986)
   ck('outer_success_call_action_trace_identical',trace==baseline_trace)
   ck('outer_success_original_ledger_identical_except_time',canon(rows)==canon(baseline_ledger.events))
   ck('outer_success_global_RNG_identical',baseline_rng==gate.recorder.global_rng())
   rejects('outer_duplicate_attempt_no_overwrite',lambda:entry.execute(config,{},'CPU_ONLY_success',package,{'auth_sha':'CPU_fixture_not_authorization','manifest_sha':manifest_sha}))
  elif name.startswith('B_'):
   ck(name+'_B_policy_never_called',policies['B256_seed17'].calls==0 and counter[0]==2 and len(original_rows)==1 and rows[-1]['event']=='start')
   ck(name+'_mismatch_abort_retained',result['last_paired_input_abort']['reason']=='paired_t0_input_mismatch_before_B_policy')
  elif name.startswith('mutation'):
   ck(name+'_partial_actions_retained',result['executed_policy_steps_retained']==8*(at-1) and len(original_rows)==0 and policies['A256_seed17'].calls==at and counter[0]==1)
   ck(name+'_inplace_abort_retained',result['last_paired_input_abort']['reason']=='policy_changed_input_identity_or_bytes')
  elif name=='policy_exception':
   ck('outer_original_policy_error_durable_then_no_second_trial',len(original_rows)==1 and original_rows[0]['status']=='policy_error' and counter[0]==1 and policies['B256_seed17'].calls==0)
   ck('outer_policy_error_original_not_rewritten',original_rows[0]['termination']=='RuntimeError' and original_rows[0]['error']=='synthetic retained policy failure')
  elif name=='cleanup':ck('outer_cleanup_row_preserved_then_stop',counter[0]==1 and any(r.get('event')=='cleanup_error' for r in rows))
  else:ck('outer_factory_failure_preserved_then_stop',counter[0]==1 and len(original_rows)==1 and original_rows[0]['status']=='infrastructure_error')
  attempts.append({'name':name,'exit_code':rc,'begun':result['observer_begun'],'finished':result['observer_finished'],'original_result_rows':len(original_rows),'executed_actions':result['executed_policy_steps_retained'],'completion_sha256':sha(entry.OUTPUT/'outer/completion.json'),'raw_original_ledger_sha256':sha(entry.OUTPUT/'original_run/trials.jsonl'),'CPU_harness_only':True})
 ck('package_not_mutated',all(sha(G/Path(p).name)==h for p,h in package['files'].items()))
 cuda=sys.modules.get('torch.cuda');ck('CUDA_not_initialized',cuda is None or not cuda.__dict__.get('_initialized'))
 write(OUT/'attempts.json',attempts)
 return {'status':'passed_CPU_production_outer_integration','checks':checks,'check_count':len(checks),'attempts':attempts,'real_original_source_functions':True,'actual_native_MjData':True,'synthetic_policy_and_environment_dynamics':True,'model_loader_replaced_with_explicit_CPU_fixture':True,'outer_execute_filesystem_namespace_redirected_to_private_test_root':True,'main_success_never_called':True,'GPU_jobs':0,'Slurm_calls':0,'state_Git_or_production_file_changes':0,'scientific_trials_added':0,'old200_HOLD':True,'new_Goal_science_HOLD':True,'real_GPU_acceptance':False}
try:report=main()
except BaseException as e:
 report={'status':'failed_CPU_outer_integration','checks':checks,'error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()};write(OUT/'report.json',report);print(json.dumps({k:report[k] for k in ('status','error_type','error')}));raise
write(OUT/'report.json',report);print(json.dumps({k:report[k] for k in ('status','check_count','GPU_jobs')}))

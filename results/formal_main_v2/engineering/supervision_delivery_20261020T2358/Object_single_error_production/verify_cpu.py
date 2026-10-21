"""Read-only verification or server-private CPU report. No simulator, policy inference, Slurm or P write."""
from pathlib import Path
import argparse,copy,hashlib,json,sys,traceback,types
from datetime import datetime,timezone,timedelta
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/object_single_error_production_20261020T2358'
S=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_run_564be0995e')
sys.path[:0]=[str(D),str(S/'src')]
import fixed as F,constants as C,adoption as A,execution as E,wrapper as W,gateway_contract as G,reviewer as V,iterator as I
from cti_vla.evaluation import formal_trials as M,libero_runtime as L,formal_runtime as Q
import numpy as np
positive=[];negative=[]
def ok(value,label):
 if not value:raise AssertionError(label)
 positive.append(label)
def no(fn,label,contains=None):
 try:fn()
 except (ValueError,KeyError,TypeError,RuntimeError,AttributeError) as e:
  if contains is not None and contains not in str(e):raise AssertionError(label+' rejected for wrong reason: '+str(e))
  negative.append(dict(check=label,error=str(e)));return
 raise AssertionError('incorrectly accepted: '+label)
def clone(x,**kw):r=copy.deepcopy(x);r.update(kw);return r
def encode(rows):return b''.join((json.dumps(r,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n').encode() for r in rows)

def checks():
 for p in D.glob('*.py'):compile(p.read_bytes(),str(p),'exec')
 inputs=F.load_inputs(M);ok(F.sig(inputs['scope'])==F.SCOPE_SHA,'173 and full original600/599/cost rebuilt')
 adoption=A.rebuild(inputs);ok(adoption['legacy_equivalent_trials']==599 and adoption['current_generated_trials']==0,'actual root599 table all rows rebuilt')
 A.require_independent(R,C.ref(R,C.ADOPTION_INDEPENDENT),adoption)
 ok(True,'actual separate31550check canonical599 independent review consumed')
 original,current,astproof=C.load(R,C.ACTION,C.ACTION_SHA).derive_function(L,F.read(S,F.RUNTIME,F.RUNTIME_SHA))
 oldM=M.run_episode
 try:
  L.run_episode=M.run_episode=current
  proof=E.current_episode(M,L)
  ok(proof['current_run_episode_code_sha256']==E.code(current),'live current action code/aliases/helpers independently rebuilt')
  M.run_episode=lambda *a:None
  no(lambda:E.current_episode(M,L),'changed live run_episode global rejects','alias')
  M.run_episode=current
  oldhash=L._observation_hash
  try:
   L._observation_hash=lambda *a:'0'*64
   no(lambda:E.current_episode(M,L),'changed observation hash rejects','observation')
  finally:L._observation_hash=oldhash
  no(lambda:E.current_episode(M,L,source=R),'wrong loaded module origin rejects','module')
 finally:L.run_episode=original;M.run_episode=oldM
 ok(L.run_episode is original and M.run_episode is oldM,'current action CPU scope restored')
 orig,derived,lp=I.derive_loop(M,F.read(S,F.LOOP,F.LOOP_SHA))
 ok(lp['inserted_node_count']==1 and lp['allowlist']==[F.CELL],'exact iterator insertion; original100x6 guards retained')
 # Code/identity tests use uninitialized policy containers only. No model weights,
 # tensors, inference or new observations are constructed.
 from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
 components=object();processor=object();policies={}
 for item in inputs['manifest']['methods']:
  ident=item['identity'];p=object.__new__(Q.FormalRolloutPolicy)
  p.suite='libero_object';p.method=ident['method'];p.total_tokens=ident['visual_tokens']
  p.record_selection=True;p.component_timing=False;p.components=components;p.processor=processor
  p.token_policy=object.__new__(OpenVLAOFTTokenPolicy);p.selector=None
  if item['identity']['method'] in ('A','B'):
   rr=json.loads((R/item['receipt']).read_text());provenance={**rr['metadata'],
    'selector_checkpoint_sha256':ident['checkpoint_sha256'],'deployment_receipt_sha256':ident['deployment_receipt_sha256'],
    'f01_report_sha256':ident['f01_report_sha256']}
   p.selector=types.SimpleNamespace(provenance=provenance)
  policies[ident['method_id']]=p
 pol=E.policy_closure(policies,inputs['manifest'])
 ok(len(pol['methods'])==6,'live exact policy class/metadata closures reconstructed without model load')
 bad=dict(policies);bad['dense']=object()
 no(lambda:E.policy_closure(bad,inputs['manifest']),'opaque policy callback rejected','opaque')
 bad=dict(policies);bad['dense']=copy.copy(policies['dense']);bad['dense'].__call__=lambda *a:None
 no(lambda:E.policy_closure(bad,inputs['manifest']),'instance policy method override rejected','overridden')
 oldfn=Q.FormalRolloutPolicy.reset
 try:
  Q.FormalRolloutPolicy.reset=lambda self:None
  no(lambda:E.policy_closure(policies,inputs['manifest']),'changed class policy code rejected','reset')
 finally:Q.FormalRolloutPolicy.reset=oldfn
 bad=dict(policies);bad.pop('B128_seed17')
 no(lambda:E.policy_closure(bad,inputs['manifest']),'dropped sixth method rejected','six')
 for key,val in [('component_timing',True),('total_tokens',64),('record_selection',False)]:
  bad=dict(policies);bad['dense']=copy.copy(policies['dense']);setattr(bad['dense'],key,val)
  no(lambda bad=bad:E.policy_closure(bad,inputs['manifest']),'wrong live policy '+key,'identity')
 old_token_method=OpenVLAOFTTokenPolicy.train
 try:
  OpenVLAOFTTokenPolicy.train=lambda self,*args:self
  no(lambda:E.policy_closure(policies,inputs['manifest']),'token policy live class method changed','train')
 finally:OpenVLAOFTTokenPolicy.train=old_token_method
 import entry as N
 no(lambda:N.bootstrap(['--verify','--plan','/tmp/arbitrary','--plan-sha256','0'*64]),'private entry refuses before project module imports','actual-P')
 # Journal comparison tests are CPU structures, not new runtime evidence.
 execute=E.compiled_function(F.read(S,'scripts/eval_formal_selector_libero.py',
  inputs['config']['source_files']['scripts/eval_formal_selector_libero.py']),S/'scripts/eval_formal_selector_libero.py','execute')
 adapter_run=E.compiled_function(F.read(F.P,C.LEGACY,C.LEGACY_SHA),F.P/C.LEGACY,'run')
 install=E.compiled_function((D/'execution.py').read_bytes(),F.P/C.BASE/'execution.py','install')
 claims=dict(original_execute_code_sha256=I.codesig(execute),
  original_adapter_run_code_sha256=I.codesig(adapter_run),
  guard_code_sha256=I.codesig(I.nested(I.nested(install,'bindings'),'guarded')),
  original_execute_callbacks={n:I.codesig(I.nested(execute,n)) for n in ('factory','reseed','on_result')},
  policy_methods_code_sha256=pol['policy_methods_code_sha256'],source_sha256=pol['source_sha256'],
  token_policy_methods_code_sha256=pol['token_policy_methods_code_sha256'],token_policy_source_sha256=pol['token_policy_source_sha256'])
 journal=[{n:claims[n] for n in ('original_execute_code_sha256','original_adapter_run_code_sha256','guard_code_sha256')},
  dict(original_execute_callbacks=claims['original_execute_callbacks'],policy_closure=pol)]
 V.validate_code_claims(journal,claims);V.reject_synthetic({'synthetic_input':False},[{}],[{}])
 ok(True,'canonical-filename code projection and journal comparator verified; no actual-P execution inferred')
 for key in ('original_execute_code_sha256','original_adapter_run_code_sha256','guard_code_sha256'):
  bad=copy.deepcopy(journal);bad[0][key]='0'*64
  no(lambda bad=bad:V.validate_code_claims(bad,claims),'runtime journal changed '+key,key)
 for key in ('factory','reseed','on_result'):
  bad=copy.deepcopy(journal);bad[1]['original_execute_callbacks'][key]='0'*64
  no(lambda bad=bad:V.validate_code_claims(bad,claims),'runtime journal changed callback '+key,'callbacks')
 for key in ('policy_methods_code_sha256','source_sha256','token_policy_methods_code_sha256','token_policy_source_sha256'):
  bad=copy.deepcopy(journal);bad[1]['policy_closure'][key]={} if isinstance(claims[key],dict) else '0'*64
  no(lambda bad=bad:V.validate_code_claims(bad,claims),'runtime journal changed '+key,key)
 bad=copy.deepcopy(journal);bad[1]['policy_closure']['opaque_callbacks_allowed']=True
 no(lambda:V.validate_code_claims(bad,claims),'runtime journal opaque callback rejected','opaque')
 no(lambda:V.reject_synthetic({'synthetic_input':True},[{}],[{}]),'synthetic_input true rejected','synthetic')
 for kind in ('action','iterator'):
  for field in ('synthetic','synthetic_fixture'):
   action=[{field:True}] if kind=='action' else [{}]
   itr=[{field:True}] if kind=='iterator' else [{}]
   no(lambda action=action,itr=itr:V.reject_synthetic({'synthetic_input':False},action,itr),'synthetic '+kind+' '+field+' rejected','synthetic')
 # Real original failed trajectory, in an explicitly synthetic three-row ledger,
 # demonstrates raw validation. No result outcome or missing query8 is invented.
 config=inputs['config'];sig=F.sig(config)
 start=json.loads(inputs['raw'][F.START['byte_offset']:F.START['byte_offset']+F.START['bytes']])
 result=copy.deepcopy(inputs['results'][F.CELL])
 rows=[dict(event='invocation',created_utc='CPU_FIXTURE_NOT_ACTUAL',slurm_job_id='9900001',run_signature=sig),start,result]
 raw=encode(rows)
 def parse(rr):return V.parse_raw(rr,config=config,panel=inputs['panel'],manifest=inputs['manifest'],
   job_id='9900001',inputs=inputs)
 parsed=parse(raw)
 ok(parsed['result']['status']=='policy_error' and parsed['result']['policy_calls']==8
  and len(parsed['result']['chunks'])==7,'real recorded failed trajectory parsed without inventing query8')
 no(lambda:parse(raw[:-1]),'truncated raw rejects')
 no(lambda:parse(inputs['raw']),'ordinary600 ledger cannot become linked attempt')
 bad=copy.deepcopy(rows);bad.append(copy.deepcopy(result))
 no(lambda:parse(encode(bad)),'second result rejects')
 bad=copy.deepcopy(rows);bad[-1].update(chunks=[],executed_actions=[],control_steps=0,policy_calls=0,status='completed',success=True,termination='environment_success')
 no(lambda:parse(encode(bad)),'empty action success rejected by actual original trajectory consumer','termination')
 bad=copy.deepcopy(rows);bad[-1]['executed_actions'][0][0]+=0.01
 no(lambda:parse(encode(bad)),'altered emitted action byte rejected','differ')
 bad=copy.deepcopy(rows);bad[-1]['chunks'][0]['metadata']['visual_tokens']=64
 no(lambda:parse(encode(bad)),'wrong chunk budget rejects')
 bad=copy.deepcopy(rows);bad[-1]['chunks'][0]['observation_sha256']='0'*64
 no(lambda:parse(encode(bad)),'different reset initial observation rejects','observation')
 for field,val in [('task_id',0),('source_state_index',1),('method','A128_seed17'),('environment_seed',1),('runtime_seed',23)]:
  bad=copy.deepcopy(rows);bad[-1][field]=val
  no(lambda bad=bad:parse(encode(bad)),'raw '+field+' mismatch')
 bad=copy.deepcopy(rows);bad[0]['slurm_job_id']='3021844'
 no(lambda:parse(encode(bad)),'old invocation cannot impersonate new')
 badconfig=copy.deepcopy(config);badconfig['source_files']={}
 no(lambda:V.parse_raw(raw,config=badconfig,panel=inputs['panel'],manifest=inputs['manifest'],
  job_id='9900001',inputs=inputs),'wrong runtime source map rejects','source')
 badconfig=copy.deepcopy(config);badconfig['watched_files']={}
 no(lambda:V.parse_raw(raw,config=badconfig,panel=inputs['panel'],manifest=inputs['manifest'],
  job_id='9900001',inputs=inputs),'missing model/data/checkpoint watch rejects','watch')
 now=datetime(2026,10,21,0,0,tzinfo=timezone.utc)
 state={'pending_submission':None,'autonomous_training_v1':{'controller_job_id':'3034538','pending_submission':None,
  'root_confirmed_normal_training_exit':dict(controller_job_id='3034538',status='COMPLETED',exit_code='0:0',
   lease_released=True,restart_needed=False,training_arms=72,training_pairs=36)},
  'registered_jobs':[dict(job_id='3034538',mode='controller',status='COMPLETED',exit_code='0:0',gpus=0)]}
 state_raw=json.dumps(state,sort_keys=True);state_sha=F.sha(state_raw.encode())
 snap=dict(schema='formal_main_v2',kind='Object_single_error_pre_submission_snapshot',observed_utc=now.isoformat(),
  state=state,state_raw=state_raw,state_sha256=state_sha,expected_state_sha256=state_sha,registered_projection=[],slurm_projection=[],
  query_receipt={'status':'complete','unknown_ids':[],'raw_sha256':'a'*64},
  writer_lock_path='results/experiment_supervisor/.writer.lock',reserved_gpu_slots=0,output_exists=False,attempt_claim_exists=False)
 plan={'CPU_fixture':True,'scope_sha256':F.SCOPE_SHA}
 checked=G.inspect_snapshot(snap,plan,now=now)
 ok(checked['next_GPU_slots']==1 and checked['submit_authorized'] is False,'gateway contract has no submit authority even on valid projection')
 no(lambda:G.submit(),'missing atomic gateway always HOLD','HOLD')
 for claimed in ('0'*64,None,'not-a-sha'):
  no(lambda claimed=claimed:G.bound_registration({}, {'registered_jobs':[{'job_id':'9900001','invocation_sha256':'1'*64}]},
   job_id='9900001',invocation_sha256=claimed),'execution rejects changed/missing root invocation byte pin '+str(claimed),'immutable invocation bytes')
 for status in ['COMPLETED','FAILED','TIMEOUT','PREEMPTED','UNKNOWN']:
  bad=copy.deepcopy(snap);bad['registered_projection']=[dict(mode=G.MODE,logical_trial_id=F.CELL,status=status)]
  no(lambda bad=bad:G.inspect_snapshot(bad,plan,now=now),'incomplete prior samecell '+status+' blocks duplicate','resubmission')
 for field,val in [('output_exists',True),('attempt_claim_exists',True),('reserved_gpu_slots',8)]:
  no(lambda field=field,val=val:G.inspect_snapshot(clone(snap,**{field:val}),plan,now=now),'gateway '+field+' block')
 no(lambda:G.inspect_snapshot(clone(snap,observed_utc=(now-timedelta(seconds=31)).isoformat()),plan,now=now),'stale Slurm evidence rejected')
 no(lambda:G.inspect_snapshot(clone(snap,state_sha256='0'*64),plan,now=now),'raw state CAS mismatch rejected')
 known=dict(job_id='9912345',job_name='cti_other',slurm_comment='exact-other-token',account='acct',
  partition='GPU',slurm_output='/exact/output',gpus=1,status='RUNNING',pair_id='other')
 actual={**known,'state':'RUNNING'};s=clone(snap,registered_projection=[known],slurm_projection=[actual])
 ok(G.inspect_snapshot(s,plan,now=now)['active_GPU_slots']==1,'actual allmode registered Slurm identity accepted')
 for field in G.FIELDS:
  bad=copy.deepcopy(s);bad['slurm_projection'][0][field]='wrong'
  no(lambda bad=bad:G.inspect_snapshot(bad,plan,now=now),'actual Slurm '+field+' conflict rejected',field)
 bad=copy.deepcopy(s);bad['slurm_projection'][0]['state']='ALIEN'
 no(lambda:G.inspect_snapshot(bad,plan,now=now),'unknown actual job state rejects')
 bad=copy.deepcopy(s);bad['slurm_projection']=[]
 no(lambda:G.inspect_snapshot(bad,plan,now=now),'missing active allocation rejects')
 bad=copy.deepcopy(s);bad['registered_projection'][0]['pair_id']=F.PAIR
 no(lambda:G.inspect_snapshot(bad,plan,now=now),'same pair active rejects')
 no(lambda:G.inspect_snapshot(clone(s,reserved_gpu_slots=7),plan,now=now),'all modes plus reservations eight reject')
 no(lambda:W.verify_plan({'stage':'final'}),'actual-P guard rejects arbitrary/final plan before data')
 no(lambda:W.reference_context(project=Path('/tmp/not_project')),'reference outside exact server root rejected')
 context=W.reference_context()
 ok(context['args_diff']=={'output':{'original':str(F.P/F.RUN),'actual':str(F.P/F.OUT)},'stop_after':{'original':12,'actual':None}},'genuine original wrapper.verify and all actual-P scientific input gates rebuilt; only typed two-argument difference')
 old,helper,evidence,*_=V.validators()
 scheduler=C.load(R,C.SCHEDULER,C.SCHEDULER_SHA)
 state_real=json.loads((R/'results/experiment_supervisor/state.json').read_text())
 value=V.reference_value(evidence,scheduler,helper,state_real)
 ok(value['manifest']==inputs['manifest'] and value['output']==F.OUT,'genuine original planner/source/config/checkpoint metadata guard rebuilt before explicit analysis projection')
 legacy_review=json.loads(F.read(R,'results/formal_main_v2/downstream_reviews/3021844.json',F.PINS['results/formal_main_v2/downstream_reviews/3021844.json']))
 historical=old.review('3021844',legacy_review['pull_receipt'],project=R,state=state_real)
 ok(historical['completed_trials']==600 and historical['cost']['all_attempt_gpu_seconds']==6713,'real old600 original raw consumer rebuilt including adapter2bindings full input/pull/trajectory/report/cost closure')
 # Entire consumer is an executable reconstruction function, not an input receipt
 # checklist. The actual terminal chain cannot run before canonical installation.
 no(lambda:V.consume({'status':'passed','all_guards':True},job_id='9900001',pull_receipt='fake',
  state={'registered_jobs':[]}),'synthetic terminal consumer flags cannot establish nonexistent job','uniquely')
 return dict(schema='formal_main_v2',kind='Object_single_error_production_CPU_reconstruction',
  status='passed_CPU_candidate_HOLD',positive=positive,negative=negative,positive_count=len(positive),negative_count=len(negative),
  original_legacy_adoption=adoption,current_action_proof=proof,iterator_derivation=lp,policy_code_proof=pol,
  raw_test_scope='Original saved failed row in synthetic job9900001 envelope; no new simulator/policy action or query8',
  actual_P_installed=False,actual_P_verified=False,actual_GPU_executed=False,atomic_gateway_missing=True,
  full_new_terminal_chain_executed=False,new_raw_terminal_chain_requires_actual_source_install_and_future_evidence=True,
  code_filename_projection_only=True,live_controller_lease_probe_missing=True,
  full_pipeline_positive_GPU_not_claimed=True,new_scientific_trials=0,new_GPU_seconds=0,final_values_read=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--report');p.add_argument('--verify-saved')
 a=p.parse_args();before={n:C.digest(D/n) for n in C.SOURCE_NAMES}
 try:
  result=checks();assert before=={n:C.digest(D/n) for n in C.SOURCE_NAMES}
  result['source_closure']=C.closure(D)
  if a.verify_saved:
   saved=json.loads((D/a.verify_saved).read_text());assert result==saved
   print(json.dumps(dict(status='read_only_rebuild_passed',positive=len(positive),negative=len(negative)),sort_keys=True));return
  if a.report:
   out=D/a.report;assert out.parent==D
   with out.open('x') as f:json.dump(result,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
  print(json.dumps(dict(status=result['status'],positive=len(positive),negative=len(negative)),sort_keys=True))
 except BaseException as e:
  if a.report:
   out=D/('failure_'+a.report)
   with out.open('x') as f:json.dump(dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),
    completed_positive=positive,completed_negative=negative,source_closure=before,new_GPU_seconds=0),f,ensure_ascii=False,indent=2)
  raise
if __name__=='__main__':main()

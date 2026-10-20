"""Server-only CPU fixtures. No simulator/model/GPU/Slurm call or production write."""
from pathlib import Path
import copy,hashlib,json,sys,traceback,types,importlib.util
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/object_single_error_candidate_20261020T2253'
sys.path.insert(0,str(D));sys.path.insert(0,str(R/'src'))
import fixed as F, iterator as I, gate as G, terminal as T
from cti_vla.evaluation import formal_trials as M,libero_runtime as L
import numpy as np

checks=[];rejects=[]
def ok(v,label):
 if not v:raise AssertionError(label)
 checks.append(label)
def no(call,label):
 try:call()
 except (ValueError,KeyError,TypeError):rejects.append(label);return
 raise AssertionError('negative accepted: '+label)
def cloned(v,**changes):
 r=copy.deepcopy(v);r.update(changes);return r
def publish(name,row):
 with (D/name).open('x',encoding='utf8') as f:json.dump(row,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
def canonical(row):return json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()

def main():
 inputs=F.load_inputs(M);scope=inputs['scope'];F.check_scope(scope)
 ok(F.sig(scope)==F.SCOPE_SHA,'real immutable scope and599 source inputs reconstructed')
 oldrawsha=F.sha(inputs['raw'])
 o,d,proof=I.derive_loop(M,(R/F.LOOP).read_bytes())
 ok(proof==json.loads((D/'iterator_derivation.json').read_text()),'exact one-node AST derivation reproduced')
 ok(proof['original_ast_sha256']=='ba5df6d5b4440f11693a3fa4a0d147f4b26f0b829df472ab12835682ba771b41'
  and proof['derived_ast_sha256']=='7750474862c77354b3115962ac667d3d1d0c60b830c5eef9af842430b4f85585','independently fixed full AST identities')
 no(lambda:I.derive_loop(M,(R/F.LOOP).read_bytes()+b'\n'),'source-byte change rejected')
 source=(R/F.LOOP).read_bytes()
 original=M._identity
 try:
  M._identity=lambda *a:None
  no(lambda:I.derive_loop(M,source),'modified identity helper rejected')
 finally:M._identity=original
 panel,manifest,config=(inputs[x] for x in ('panel','manifest','config'))
 no(lambda:F.validate_panel_manifest(cloned(panel,states=panel['states'][:1]),manifest,config,M),'one-state panel forbidden')
 no(lambda:F.validate_panel_manifest(cloned(panel,split='final'),manifest,config,M),'final panel forbidden before sealed access')
 m=copy.deepcopy(manifest);m['methods']=m['methods'][:1]
 no(lambda:F.validate_panel_manifest(panel,m,config,M),'single-method manifest forbidden')
 m=copy.deepcopy(manifest);m['methods'][4]['identity']['checkpoint_sha256']='0'*64
 no(lambda:F.validate_panel_manifest(panel,m,config,M),'wrong selected checkpoint forbidden')
 p=copy.deepcopy(panel);p['states'][0]['initial_state'][0]=9
 no(lambda:F.validate_panel_manifest(p,manifest,config,M),'changed initial-state vector forbidden')
 m=copy.deepcopy(manifest);m['environment']['runtime_seed']=41
 no(lambda:F.validate_panel_manifest(panel,m,config,M),'changed runtime seed forbidden')

 class Ledger:
  def __init__(self):
   self.events=[dict(event='invocation',created_utc='CPU_FIXTURE',slurm_job_id='9900001',run_signature=F.sig(config))]
  def append(self,row):self.events.append(dict(row,run_signature=F.sig(config)))
  def completed(self):return {r['trial_id'] for r in self.events if r.get('event')=='result' and r.get('status') in ('completed','policy_error')}
 trace=[];saved=inputs['results'][F.CELL]['chunks'][0]
 class Boundary:
  def __init__(self):self.n=0;self.actions=[]
  def reset(self):trace.append('reset')
  def set_init_state(self,state):
   target=next(x for x in panel['states'] if x['trial_id']+':dense'==F.CELL)
   ok(np.array_equal(state,np.asarray(target['initial_state'],dtype=np.float64)),'exact failed initial vector passed at full reset')
   trace.append('set_init_state');return observation()
  def step(self,action):
   self.n+=1;self.actions.append(list(action));return observation(),0,self.n>=18,{}
  def close(self):trace.append('close')
 def observation():
  return dict(agentview_image=np.zeros((2,2,3),dtype=np.uint8),robot0_eye_in_hand_image=np.zeros((2,2,3),dtype=np.uint8),
   robot0_eef_pos=np.zeros(3),robot0_eef_quat=np.zeros(4),robot0_gripper_qpos=np.zeros(2))
 class Recorded:
  def __init__(self,mid):self.mid=mid
  def reset(self):trace.append('policy_reset:'+self.mid)
  def __call__(self,*args):
   ok(self.mid=='dense','only dense actual policy callback')
   trace.append('recorded_chunk')
   return L.PolicyChunk(np.array(saved['normalized_actions']),np.array(saved['environment_actions']),saved['metadata'])
 policies={m:Recorded(m) for m in F.METHODS}
 ledger=Ledger();envs=[]
 def factory(state):
  ok(state['task_id']==8 and state['source_state_index']==49,'only exact task8 source49 environment factory')
  trace.append('factory');e=Boundary();envs.append(e);return e,'CPU recorded chunk replay only'
 def reseed():trace.append('reseed')
 def callcheck(ledger=ledger,**over):
  args=dict(panel=panel,manifest=manifest,config=config,policies=policies,ledger=ledger,job_id='9900001',
   run_signature=F.sig(config),stop_after=None,policy_watchdog_seconds=60.,scope=scope,loop_proof=proof);args.update(over)
  return I.check_runtime_call(M,**args)
 ok(callcheck()['production_authorized'] is False,'runtime precheck has no GPU authority')
 no(lambda:callcheck(stop_after=1),'stop_after1 cannot target wrong first cell')
 no(lambda:callcheck(policy_watchdog_seconds=30.),'watchdog change forbidden')
 no(lambda:callcheck(policies={'dense':Recorded('dense')}),'all6 original verified policy bindings required')
 no(lambda:callcheck(job_id='3021844'),'legacy job cannot impersonate new invocation')
 bad=Ledger();bad.events.append(dict(event='result',trial_id=F.CELL,status='completed'))
 no(lambda:callcheck(ledger=bad),'fake completion in new ledger rejected')
 bad=Ledger();bad.events=[]
 no(lambda:callcheck(ledger=bad),'missing actual new invocation rejected')
 no(lambda:callcheck(loop_proof=cloned(proof,derived_ast_sha256='0'*64)),'forged derived AST proof rejected')

 action=R/'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py'
 ok(F.sha(action.read_bytes())=='b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185','pinned current action derivation source')
 module=types.ModuleType('_cpu_existing_action');module.__file__=str(action);exec(compile(action.read_bytes(),str(action),'exec'),module.__dict__)
 old_episode,current_episode,actionproof=module.derive_function(L,(R/F.RUNTIME).read_bytes())
 previous=M.run_episode;outcomes=[]
 try:
  M.run_episode=current_episode
  ran=d(panel,policies,ledger,factory,reseed=reseed,stop_after=None,policy_watchdog_seconds=60.,on_result=outcomes.append)
 finally:M.run_episode=previous
 ok(ran==1 and len(ledger.events)==3 and len(outcomes)==1,'derived full-panel loop emitted exactly one invocation/start/result')
 ok(trace==['reseed','factory','reset','set_init_state','policy_reset:dense','recorded_chunk','close'],'full reseed/reset/wait/policy lifecycle unchanged')
 ok(len(envs)==1 and len(envs[0].actions)==18 and envs[0].actions[:10]==[list(L.DUMMY_ACTION)]*10,'original10dummy then8control actions')
 ok(np.asarray(envs[0].actions[10:],dtype='<f8').tobytes()==np.asarray(saved['environment_actions'],dtype='<f8').tobytes(),'saved emitted action bytes unchanged through iterator/current action code')
 ok(M.evaluate_formal_trials is o and M.run_episode is previous,'CPU original loop/action bindings restored')
 no(lambda:callcheck(ledger=ledger),'completed new attempt cannot execute again')
 raw=b''.join(canonical(x)+b'\n' for x in ledger.events)
 parse=T.parse_new(raw,formal=M,panel=panel,scope=scope,job_id='9900001',run_signature=F.sig(config))
 ok(parse['result']['trial_id']==F.CELL,'typed new raw parser binds exact logical cell')
 # The synthetic outcome below tests structural assembly only; no real attempt or GPU time is created.
 alloc=[dict(job_id='9900001',gpus=1,elapsed_seconds=100,status='COMPLETED',raw_status='COMPLETED',exit_code='0:0')]
 receipts={}
 for role in ('root','independent'):
  receipts[role]=dict(kind='Object_single_error_full_terminal_consumer',reviewed_by=role,status='passed',blockers=[],
   job_id='9900001',new_raw_sha256=F.sha(raw),original_raw_sha256=oldrawsha,
   original_config_manifest_model_checkpoint_source_environment_guards=True,current_action_runtime_and_adapter_provenance_verified=True,
   all_chunks_trajectory_hashes_statistics_rebuilt=True,full100_initial_state_and6_method_identity_verified=True,
   old599_compatibility_root_adopted=True,final_allowed=False,synthetic_fixture=True)
 view=T.assemble_candidate(inputs,raw,config,alloc,formal=M,receipts=receipts)
 ok(view['logical_cells']==600 and view['legacy_equivalent_cells']==599 and view['current_attempt_cells']==1
  and view['raw_historical_attempts']==600 and view['new_attempts']==1 and view['unchanged_unique_initial_states']==100,'typed599legacy+1new logical reference assembly')
 ok(view['production_admitted'] is False and view['retained_old_failure']['rejected_query8_unknown'] is True,'synthetic assembly does not admit production or inventquery8')
 ok(view['cost']['all_attempt_gpu_seconds']==6813,'synthetic allocation cost6713+100 counted once')
 no(lambda:T.assemble_candidate(inputs,raw,config,alloc*2,formal=M,receipts=receipts),'duplicate new allocation rejected')
 no(lambda:T.account_allocations(scope['legacy_allocations'][1:],alloc),'missing original386second allocation rejected')
 no(lambda:T.account_allocations(cloned(scope['legacy_allocations'][0],elapsed_seconds=0) if False else scope['legacy_allocations']+[scope['legacy_allocations'][0]],alloc),'duplicate old allocation rejected')
 no(lambda:T.assemble_candidate(inputs,raw,cloned(config,source_files={}),alloc,formal=M,receipts=receipts),'terminal source omission rejected')
 no(lambda:T.assemble_candidate(inputs,raw,config,alloc,formal=M,receipts={'root':receipts['root']}),'missing independent terminal review rejected')
 rr=copy.deepcopy(receipts);rr['independent']['all_chunks_trajectory_hashes_statistics_rebuilt']=False
 no(lambda:T.assemble_candidate(inputs,raw,config,alloc,formal=M,receipts=rr),'partial runtime-only terminal audit rejected')
 no(lambda:T.parse_new(raw[:-1],formal=M,panel=panel,scope=scope,job_id='9900001',run_signature=F.sig(config)),'malformed new ledger tail rejected')
 no(lambda:T.parse_new(inputs['raw'],formal=M,panel=panel,scope=scope,job_id='9900001',run_signature=F.sig(config)),'old600 ledger cannot become new correction ledger')
 rr=copy.deepcopy(ledger.events);rr[-1]['trial_id']='other'
 no(lambda:T.parse_new(b''.join(canonical(x)+b'\n' for x in rr),formal=M,panel=panel,scope=scope,job_id='9900001',run_signature=F.sig(config)),'foreign cell raw result rejected')
 failed_alloc=[cloned(alloc[0],status='FAILED',raw_status='FAILED',exit_code='1:0')]
 hold=T.assemble_candidate(inputs,raw,config,failed_alloc,formal=M,receipts={})
 ok(hold['status'].startswith('HOLD') and hold['auto_retry'] is False and hold['new_attempt_retained'],'failed allocation preserved without retry or assembly')
 # A failed current policy outcome is kept as a failure; no success-conditioned retry.
 errored=copy.deepcopy(ledger.events);errored[-1].update(status='policy_error',success=False,termination='CPU_fixture')
 errorraw=b''.join(canonical(x)+b'\n' for x in errored);er=copy.deepcopy(receipts)
 for x in er.values():x['new_raw_sha256']=F.sha(errorraw)
 ev=T.assemble_candidate(inputs,errorraw,config,alloc,formal=M,receipts=er)
 ok(ev['method_counts']['dense']['success']==view['method_counts']['dense']['success']-1,'new negative outcome retained in candidate counts')
 source_map={F.BASE+'/'+n:F.sha((D/n).read_bytes()) for n in ('fixed.py','iterator.py','gate.py','terminal.py','scope.json')}
 bundle=F.sig(source_map);plan=G.proposal(scope,bundle,'0123456789abcdef'*3)
 now=datetime.now(timezone.utc)
 snapshot=dict(kind='all_modes_registered_live_snapshot',project='CTI-VLA',captured_utc=now.isoformat(),state_sha256='1'*64,
  controller={'job_id':'3034538','status':'COMPLETED','exit_code':'0:0','lifetime_lease_held':False},
  registered_jobs=[],slurm_rows=[],pending=[],reserved_gpu_slots=0,output_exists=False,ledger_exists=False,unknown_registered_activity=False)
 obj={}
 for key in G.RECEIPT_NAMES:
  obj[key]=dict(schema='formal_main_v2',kind=key,status='passed',blockers=[],reviewed_by='independent' if key=='independent_runtime_review' else 'root',
   proposal_sha256=F.sig(plan),scope_sha256=F.sig(scope),bundle_sha256=bundle,final_allowed=False,synthetic_fixture=True)
 obj['root_legacy_adoption'].update(legacy_independent_review_sha256=F.PINS[F.OLD_PROOF+'/independent_review.json'],
  legacy_independent_review=dict(path=F.PROOF_ARCHIVE,sha256=F.PINS[F.PROOF_ARCHIVE]),
  legacy_equivalent_trials=599,current_wrapper_generated_legacy_trials=0,raw_historical_trials=600,retained_policy_errors=1,legacy_gpu_seconds=6713)
 obj['root_repair'].update(original_failed_result=F.RESULT,all_prior_job_ids=list(F.JOBS),ordinary_resume=False,new_attempt_limit=1,
  rejected_query8_unknown=True,old_ledger_modified=False)
 obj['independent_runtime_review'].update(typed_iterator_reviewed=True,typed_gateway_reviewed=True,
  typed_parent_child_provenance_reviewed=True,typed_terminal_consumer_reviewed=True,all_mode_capacity_and_pending_ACK_reviewed=True)
 obj['runtime_readiness'].update(actual_P_verified=True,production_chain_complete=True,original173_unchanged=True,
  actual_sources=source_map,expected_sources=source_map,same_registered_Object_base_and_all6_methods_verified=True,new_ledger_absent=True,
  actual_project_root=str(F.P),source_root=str(F.S))
 obj['root_submission_review']['exact_once_registered']=True
 def enc(ob):
  blobs={k:canonical(v) for k,v in ob.items()}
  refs={k:dict(path=F.EX+'/'+k+'.json',sha256=F.sha(v)) for k,v in blobs.items()}
  return blobs,refs
 blobs,refs=enc(obj)
 def pending(snap=snapshot,ob=obj,**over):
  bb,rr=enc(ob);kw=dict(now=now,writer_lock_held=True,actual_state_sha256=snap['state_sha256'],invocation_sha256='a'*64);kw.update(over)
  return G.prepare_pending_intent(plan,scope,snap,bb,rr,**kw)
 intent=pending()
 ok(intent['mutation_performed'] is False and intent['submit_performed'] is False and intent['production_authorized'] is False,'CPU pending intent performs no transaction or submit')
 for key,value in [('stage','final'),('mode','full'),('suite','libero_spatial'),('ordinary_resume',True),('auto_retry',True),
                   ('max_new_trials',600),('allowlist',[F.CELL,'other']),('original_method_ids',['dense']),('runtime_seed',41),
                   ('output',str(F.P/F.RUN)),('action_semantics_sha256','0'*64),('all_prior_job_ids',['3021844']),
                   ('legacy_gpu_seconds',4926),('profile_allowed',True),('final_allowed',True),('source_root',str(F.R))]:
  no(lambda key=key,value=value:G.validate_proposal(cloned(plan,**{key:value}),scope),'proposal rejects '+key)
 no(lambda:G.proposal(cloned(scope,allowlist=['other']),bundle,'0'*48),'scope forgery rejected')
 no(lambda:pending(writer_lock_held=False),'writer lock absent')
 no(lambda:pending(actual_state_sha256='b'*64),'state CAS changed')
 no(lambda:pending(snap=cloned(snapshot,pending=[{'token':'uncertain','ack':None}])),'uncertain ACK/pending blocks not cleared')
 no(lambda:pending(snap=cloned(snapshot,unknown_registered_activity=True)),'unknown registered activity blocks')
 no(lambda:pending(snap=cloned(snapshot,output_exists=True)),'existing output blocks duplicate')
 no(lambda:pending(snap=cloned(snapshot,ledger_exists=True)),'existing ledger blocks duplicate')
 no(lambda:pending(snap=cloned(snapshot,captured_utc='2020-01-01T00:00:00+00:00')),'stale live snapshot rejected')
 no(lambda:pending(snap=cloned(snapshot,controller=cloned(snapshot['controller'],lifetime_lease_held=True))),'second active training controller forbidden')
 for key in G.RECEIPT_NAMES:
  rr=copy.deepcopy(obj);rr.pop(key)
  no(lambda rr=rr:pending(ob=rr),'missing receipt '+key)
 rr=copy.deepcopy(obj);rr['root_legacy_adoption']['legacy_independent_review']['path']='.local/private.json'
 no(lambda:pending(ob=rr),'private599 proof cannot authorize production')
 rr=copy.deepcopy(obj);rr['root_repair']['rejected_query8_unknown']=False
 no(lambda:pending(ob=rr),'fabricated query8 diagnosis rejected')
 rr=copy.deepcopy(obj);rr['runtime_readiness']['actual_P_verified']=False
 no(lambda:pending(ob=rr),'CPU candidate cannot impersonate actual P verification')
 rr=copy.deepcopy(obj);rr['runtime_readiness']['actual_sources']={**source_map,F.BASE+'/iterator.py':'0'*64}
 no(lambda:pending(ob=rr),'actual P source differs')
 rr=copy.deepcopy(obj);rr['runtime_readiness']['actual_sources']=rr['runtime_readiness']['expected_sources']={**source_map,F.BASE+'/iterator.py':'0'*64}
 no(lambda:pending(ob=rr),'self-consistent forged P source closure rejected')
 rr=copy.deepcopy(obj);rr['independent_runtime_review']['typed_terminal_consumer_reviewed']=False
 no(lambda:pending(ob=rr),'no consumer audit no deployment')
 def with_jobs(n,mode='engineering'):
  snap=copy.deepcopy(snapshot)
  for i in range(n):
   job=str(9900100+i);snap['registered_jobs'].append(dict(job_id=job,project='CTI-VLA',mode=mode,pair_id='foreign_pair'))
   snap['slurm_rows'].append(dict(job_id=job,state='RUNNING',gpus=1))
  return snap
 ok(pending(snap=with_jobs(7))['capacity']['slots_after_submit']==8,'all-mode seventh occupied permits eighth only')
 no(lambda:pending(snap=with_jobs(8)),'engineering eight slots count against global limit')
 no(lambda:pending(snap=cloned(with_jobs(7),reserved_gpu_slots=1)),'reservation consumes eighth slot')
 snap=with_jobs(1);snap['registered_jobs'][0]['pair_id']=F.PAIR
 no(lambda:pending(snap=snap),'same pair active conflicts even different mode')
 snap=with_jobs(1);snap['registered_jobs'][0]['logical_trial_id']=F.CELL
 no(lambda:pending(snap=snap),'same exact cell active conflicts')
 for key,value in [('linked_original_result_sha256',F.RESULT['sha256']),('output',plan['output']),('submission_token',plan['submission_token']),('comment',plan['comment'])]:
  snap=with_jobs(1);snap['registered_jobs'][0][key]=value;snap['slurm_rows'][0]['state']='FAILED'
  no(lambda snap=snap:pending(snap=snap),'already attempted/ACK '+key+' blocks even FAILED')
 snap=with_jobs(1);snap['slurm_rows'][0]['state']='UNKNOWN'
 no(lambda:pending(snap=snap),'unknown Slurm terminal state blocks')
 snap=with_jobs(1);snap['slurm_rows']=[]
 no(lambda:pending(snap=snap),'missing registered Slurm identity blocks')
 snap=with_jobs(1);snap['registered_jobs'][0]['project']='another_project'
 no(lambda:pending(snap=snap),'foreign project cannot be managed')
 snap=with_jobs(1);snap['slurm_rows'][0]['gpus']=2
 no(lambda:pending(snap=snap),'non-independent multi-GPU row rejects')
 snap=with_jobs(1);snap['slurm_rows'].append(copy.deepcopy(snap['slurm_rows'][0]))
 no(lambda:pending(snap=snap),'duplicate account row rejects')
 ok(G.inspect_candidate(plan,scope)['status']=='HOLD_CPU_candidate_only','true candidate stays HOLD regardless CPU success')
 ok(F.sha((R/F.RUN/'trials.jsonl').read_bytes())==oldrawsha,'old raw600 byte hash unchanged after all tests')
 ok(M.evaluate_formal_trials is o and M.run_episode is previous,'all CPU monkeypatched scientific bindings restored')
 # Fixtures retain unmistakable synthetic markers and cannot serve as actual root/Slurm evidence.
 publish('cpu_gate_fixtures.json',dict(synthetic_fixture=True,not_production_evidence=True,plan=plan,
  all_modes_snapshot=snapshot,synthetic_receipt_payloads=obj,source_map=source_map,bundle_sha256=bundle,
  fake_job_ids=['9900001'],synthetic_cost_seconds=100,actual_new_GPU_seconds=0))
 publish('cpu_tests.json',dict(schema='formal_main_v2',kind='Object_single_error_CPU_tests',
  status='passed_CPU_candidate_only',positive_checks=len(checks),negative_checks=len(rejects),checks=checks,rejections=rejects,
  original_sources173_verified=True,original600_unchanged=True,original6713_GPU_seconds_unchanged=True,
  derivation=proof,source_map=source_map,bundle_sha256=bundle,synthetic_rollouts=1,synthetic_terminal_cost_examples_not_real=True,
  simulator_calls=0,model_inference_calls=0,GPU_calls=0,Slurm_submissions=0,new_scientific_trials=0,
  production_admitted=False,final_state_values_read=False,remaining_blockers=G.BLOCKERS))
 print(json.dumps(dict(status='passed_CPU_candidate_only',positive=len(checks),negative=len(rejects),
  test_sha256=F.sha((D/'cpu_tests.json').read_bytes()),source_bundle_sha256=bundle),ensure_ascii=False))

if __name__=='__main__':
 try:main()
 except BaseException as e:
  index=1
  while (D/('cpu_failure_%02d.json'%index)).exists():index+=1
  publish('cpu_failure_%02d.json'%index,dict(error=str(e),traceback=traceback.format_exc(),checks=checks,rejections=rejects,
   source_sha256={p.name:F.sha(p.read_bytes()) for p in D.glob('*.py')},actual_GPU_seconds=0,new_scientific_trials=0))
  raise

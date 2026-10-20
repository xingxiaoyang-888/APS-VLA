"""Independent CPU-only candidate audit. No production writes/submissions."""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,hashlib,importlib.util,json,random,sys,tarfile,traceback
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/goal_cpu_gate_20261020T2054';O=Path(__file__).parent
checks=[]
def digest(raw):return hashlib.sha256(raw).hexdigest()
def sha(p):return digest(Path(p).read_bytes())
def ck(n,ok,detail=None):
 checks.append({'name':n,'passed':bool(ok),'detail':detail})
 if not ok:raise AssertionError(n)
def write(n,v):
 with (O/n).open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
def load(p,name):
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def canon(rows):
 out=copy.deepcopy(rows)
 for row in out:
  for k in ('created_utc','attempt_wall_seconds','wall_seconds'):row.pop(k,None)
  for ch in row.get('chunks',[]):ch.pop('engineering_seconds',None)
 return out
def expect_abort(name,fn,kind):
 try:fn()
 except kind:ck(name,True)
 else:ck(name,False)
def main():
 manifest=D/'delivery_manifest.json';ck('author_manifest_exact',sha(manifest)=='ab07dec9d6fcf8334c52b9bb836ce3b79402a3b77268d0c85c63ad3cdb42b4e4')
 man=json.loads(manifest.read_text())
 for item in man['files']:
  p=R/item['path'];ck('candidate_file_'+p.name,p.is_relative_to(D) and p.stat().st_size==item['bytes'] and sha(p)==item['sha256'])
 ck('candidate_explicit_no_GPU_or_science_or_entrypoint',man['GPU_runs']==man['scientific_trials_added']==0 and not man['production_entrypoint_integrated'] and not man['single_attempt_GPU_authorization_granted'] and not man['old200_accepted'])
 inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text())['files']
 for root in (R,S):ck('173_before_'+root.name,len(inventory)==173 and all(sha(root/k)==v for k,v in inventory.items()))
 idx=json.loads((D/'CPU_evidence_archive_index.json').read_text());members={r['path']:r for r in idx['members']};archive={}
 with tarfile.open(D/'CPU_evidence.tar.gz','r:gz') as tf:
  names=[x.name for x in tf.getmembers()];ck('archive_exact_491_unique_members',len(names)==len(set(names))==len(members)==491 and set(names)==set(members))
  for entry in tf.getmembers():
   ck('archive_safe_'+entry.name,entry.isfile() and not Path(entry.name).is_absolute() and '..' not in Path(entry.name).parts)
   raw=tf.extractfile(entry).read();m=members[entry.name];ck('archive_sha_'+entry.name,len(raw)==m['bytes'] and digest(raw)==m['sha256']);archive[entry.name]=raw
 rows=lambda n:[json.loads(x) for x in archive[n].splitlines()]
 base=rows('CPU_attempt01/baseline.jsonl');gated=rows('CPU_attempt01/gated.jsonl');ck('raw_archive_baseline_gated_equivalence',canon(base)==canon(gated))
 gr=rows('CPU_attempt01/gated/gate.jsonl');pairs=[x for x in gr if x['event']=='t0_pair_gate'];steps=[x for x in gr if x['event']=='policy_step_executed'];queries=[x for x in gr if x['event']=='query_integrity_passed']
 ck('raw_archive_58_trials_29_pairs_174_queries_986_steps',len([x for x in gated if x['event']=='result'])==len(pairs)==58 and sum(x['pairing']=='exact_before_policy_pair_passed' for x in pairs)==29 and len(queries)==174 and len(steps)==986)
 ck('raw_archive_complete59_not_present',max(x['ordinal'] for x in pairs)==58)
 ev=rows('CPU_attempt01/gated/events.jsonl');capture_rows=[x for x in ev if x.get('phase') in ('t0_query_before','t0_query_after','query_before','query_after')]
 ck('archive_348_query_capture_boundaries',len(capture_rows)==348)
 for i,x in enumerate(capture_rows):
  for key,v in x['observation_arrays'].items():
   b=archive['CPU_attempt01/gated/'+v['blob']['path']];ck('query_blob_%d_%s'%(i,key),len(b)==v['bytes'] and digest(b)==v['sha256']==v['blob']['sha256'])
 reg=json.loads((D/'proposed_engineering_registration_NOT_AUTHORIZED.json').read_text());par=R/reg['parent_design']['path']
 ck('parent_design_pin',sha(par)==reg['parent_design']['sha256'])
 ck('bounded_draft_only',reg['status']=='draft_not_submittable_not_registered_no_GPU_authority' and reg['maximum_attempts']==1 and reg['maximum_trials']==58 and reg['GPUs']==1 and reg['counts_toward_eight_slots'] and reg['old200_HOLD'] and reg['new_Goal_science_HOLD'])
 # Re-execute author's fixed assertions with only its output directory relocated.
 original=(D/'cpu_check_v1.py').read_text();needle="OUT=D/'CPU_attempt01';OUT.mkdir(exist_ok=False);checks=[]"
 ck('replay_source_patch_exact_single_output',original.count(needle)==1)
 replacement="OUT=Path("+repr(str(O/'author_assertions_reexecuted'))+");OUT.mkdir(exist_ok=False);checks=[]"
 replay=original.replace(needle,replacement,1);ns={'__file__':str(D/'cpu_check_v1.py'),'__name__':'_independent_replay_of_pinned_author_assertions'}
 exec(compile(replay,str(D/'cpu_check_v1.py')+'::<output-only-relocation>','exec'),ns)
 report=ns['report'];ck('independently_reexecuted_66_author_assertions',report['status']=='passed_CPU_source_candidate_only' and report['check_count']==66 and all(x['passed'] for x in report['checks']))
 write('author_reexecution_derivation.json',{'original_source_sha256':digest(original.encode()),'in_memory_derived_sha256':digest(replay.encode()),'only_change':'OUT rebased to independent private directory; D/R/sources/66 assertions unchanged','actual_source_modified':False})
 gate=load(D/'paired_input_gate_v1.py','independent_goal_gate');adapter=load(D/'ast_gate_v2.py','independent_goal_ast')
 from cti_vla.evaluation import libero_runtime as runtime,formal_trials as trials
 accepted_path=P/'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py';accepted=load(accepted_path,'independent_goal_accepted_action')
 ck('GateAbort_not_Exception',issubclass(gate.GateAbort,BaseException) and not issubclass(gate.GateAbort,Exception))
 panel=json.loads((P/'results/formal_main_v2/libero_goal/downstream/development/5185766bb353c8e6/attempt01/panel.json').read_text())
 class Env:
  def __init__(self,mode):
   self.mode=mode;self.n=0;self.closed=0
   native=SimpleNamespace(time=0.,**{k:np.zeros(2,dtype=np.float64) for k in gate.recorder.SIM_FIELDS})
   self.env=SimpleNamespace(sim=SimpleNamespace(data=native),timestep=0,np_random=np.random.RandomState(71))
  def obs(self):
   result={'agentview_image':np.full((2,3,3),self.n,np.uint8),'robot0_eye_in_hand_image':np.zeros((2,3,3),np.uint8),'robot0_eef_pos':np.ones(3),'robot0_eef_quat':np.array([0.,0.,0.,1.]),'robot0_gripper_qpos':np.zeros(2)}
   if self.mode=='missing_component':result.pop('robot0_eef_quat')
   return result
  def reset(self):self.n=0;return self.obs()
  def set_init_state(self,state):return self.obs()
  def step(self,a):
   self.n+=1
   if self.mode=='environment_error' and self.n==11:raise RuntimeError('independent synthetic env failure')
   return self.obs(),0.,self.n>=11,{}
  def close(self):
   self.closed+=1
   if self.mode=='cleanup_error':raise RuntimeError('independent synthetic close failure')
 class Policy:
  def __init__(self,mode):self.mode=mode;self.calls=0
  def reset(self):self.calls=0
  def __call__(self,o,ins):
   self.calls+=1;a=np.ones((8,7))*1.4
   if self.mode=='nonfinite_chunk':a[0,0]=np.nan
   return runtime.PolicyChunk(a,a,{})
 def reseed():random.seed(17);np.random.seed(17)
 events=[]
 original_functions=(runtime.run_episode,trials.evaluate_formal_trials)
 with accepted.install_action_execution_compat(project_root=P,source_root=S,runtime_module=runtime,formal_trials_module=trials,expected_adapter_sha256='b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185',emit=lambda event,**kw:events.append({'event':event,**kw})):
  for mode in ('missing_component','environment_error','cleanup_error','nonfinite_chunk'):
   led=runtime.TrialLedger(O/(mode+'.jsonl'),run_signature='e'*64);ob=gate.PairedInputGate(O/('independent_'+mode),allow_cpu_fixture=True);made=[];pol=Policy(mode);q={'A256_seed17':pol,'B256_seed17':Policy('normal')}
   def factory(state):e=Env(mode);made.append(e);return e,'fixed instruction'
   with adapter.observer_scope(runtime,trials,ob,emit=lambda event,**kw:events.append({'event':event,**kw})):
    expect_abort('independent_failstop_'+mode,lambda:trials.evaluate_formal_trials(panel,q,led,factory,reseed=reseed,stop_after=58),gate.GateAbort)
   ck('independent_no_next_trial_'+mode,ob.dead and ob.finished==0 and len(made)==1 and made[0].closed==1 and q['B256_seed17'].calls==0)
   result=[x for x in led.events if x['event']=='result']
   if mode=='missing_component':ck('missing_component_before_policy_no_fake_result',pol.calls==0 and not result)
   elif mode=='environment_error':ck('environment_error_original_row_retained',len(result)==1 and result[0]['status']=='infrastructure_error')
   elif mode=='cleanup_error':ck('cleanup_error_and_original_result_retained',len(result)==1 and len([x for x in led.events if x['event']=='cleanup_error'])==1)
   else:ck('policychunk_invalid_original_policy_error_retained',len(result)==1 and result[0]['status']=='policy_error')
   expect_abort('independent_failed_finish_'+mode,ob.finish,gate.GateAbort)
 # Direct API guard tests are separate from actual-loop re-execution claims.
 for name,op in [
  ('bad_state_hash',lambda g: g.trial_begin(trials._identity(panel,panel['states'][0],'A256_seed17'),{**panel['states'][0],'initial_state_sha256':'0'*64})),
  ('bad_identity_method',lambda g:g.trial_begin({**trials._identity(panel,panel['states'][0],'A256_seed17'),'method':'B256_seed17'},panel['states'][0])),
  ('post_without_pre',lambda g:(g.trial_begin(trials._identity(panel,panel['states'][0],'A256_seed17'),panel['states'][0]),g.capture('t0_query_after',Env('normal'),Env('normal').obs(),control_step=0,instruction='fixed',chunk=runtime.PolicyChunk(np.zeros((8,7)),np.zeros((8,7)),{})))),
  ('missing_query_index',lambda g:(g.trial_begin(trials._identity(panel,panel['states'][0],'A256_seed17'),panel['states'][0]),g.capture('query_before',Env('normal'),Env('normal').obs(),control_step=8,instruction='fixed'))),
  ('wrong_t0_marker',lambda g:(g.trial_begin(trials._identity(panel,panel['states'][0],'A256_seed17'),panel['states'][0]),g.capture('query_before',Env('normal'),Env('normal').obs(),control_step=0,instruction='fixed'))),
  ('invalid_control_step',lambda g:g.capture('t0_query_before',Env('normal'),Env('normal').obs(),control_step=True,instruction='fixed'))]:
  g=gate.PairedInputGate(O/('independent_'+name),allow_cpu_fixture=True);expect_abort('direct_guard_'+name,lambda:g and op(g),gate.GateAbort);ck('direct_guard_latched_'+name,g.dead)
 expect_abort('CPU_sink_forbidden_without_fixture_flag',lambda:gate.PairedInputGate(O/'forbidden_sink',sink=lambda x:None),gate.GateAbort)
 ck('all_original_functions_restored_after_extra_failures',(runtime.run_episode,trials.evaluate_formal_trials)==original_functions)
 for root in (R,S):ck('173_after_'+root.name,all(sha(root/k)==v for k,v in inventory.items()))
 ck('source_manifest_still_exact',sha(manifest)=='ab07dec9d6fcf8334c52b9bb836ce3b79402a3b77268d0c85c63ad3cdb42b4e4' and all(sha(R/i['path'])==i['sha256'] for i in man['files']))
 ck('no_CUDA_or_Mujoco',not (sys.modules.get('torch.cuda') and sys.modules['torch.cuda'].__dict__.get('_initialized')) and not any(k.startswith('mujoco') for k in sys.modules))
 write('independent_scope_events.json',events)
 return {'status':'independent_CPU_candidate_passed_not_production_authorized','checks':checks,'check_count':len(checks),'author_assertions_independently_reexecuted':66,'CPU_synthetic_only':True,'GPU_jobs':0,'Slurm_calls':0,'production_writes':0,'scientific_trials_added':0,'old200_HOLD':True,'new_Goal_science_HOLD':True,'final_release':False,'real_environment_validation':False,'P_source_closure_verified':False,'limits':['Gate compares SHA-bound persisted bytes at query boundaries; not exact prior history replay','CPU synthetic policy/env cannot prove production MuJoCo/CUDA passive-read validity','No new production wrapper, source readiness, GPU registration or result admission','All query copies and I/O are engineering-only, not O2A timing','Successful future engineering cannot validate old200 or automatically authorize science']}
try:
 report=main();write('report.json',report);print(json.dumps({k:report[k] for k in ('status','check_count','author_assertions_independently_reexecuted','GPU_jobs')}))
except BaseException as e:
 write('FAILED_report.json',{'status':'audit_failed','checks':checks,'exception':repr(e),'traceback':traceback.format_exc(),'GPU_jobs':0});raise

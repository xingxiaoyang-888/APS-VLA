"""CPU-only execution of real pinned loops using synthetic environments/policies."""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,hashlib,importlib.util,json,random,sys,time,traceback,os
import numpy as np
D=Path(__file__).parent;R=D.parents[1];P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
G=P/'scripts/ops/formal_goal_paired_input_gate_v1'

def independent_write_guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','socket.bind'):raise RuntimeError('independent CPU test forbids process/network')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  mode,flags=args[1:3];w=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if w and not p.is_relative_to(D):raise RuntimeError('independent test output outside private root')
sys.dont_write_bytecode=True;sys.addaudithook(independent_write_guard)

OUT=D/'independent_core';OUT.mkdir(exist_ok=False);checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):
 with p.open('x',encoding='utf8') as f:json.dump(x,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def ck(n,v,detail=None):
 checks.append({'name':n,'passed':bool(v),'detail':detail})
 if not v:raise AssertionError(n)
def load(p,name):
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def excepts(n,f,types):
 try:f()
 except types:ck(n,True)
 else:ck(n,False)
def main():
 gate=load(G/'paired_input_gate_v1.py','goal_paired_gate_cpu');adapter=load(G/'ast_gate_v2.py','goal_paired_ast_cpu')
 sys.path.insert(0,str(S/'src'))
 from cti_vla.evaluation import libero_runtime as runtime,formal_trials as trials
 accepted_path=P/'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py'
 ck('accepted_adapter_exact',sha(accepted_path)=='b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185')
 accepted=load(accepted_path,'goal_cpu_existing_accepted_action')
 frozen=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text())['files']
 for root in (R,S):ck('frozen173_before_'+root.name,len(frozen)==173 and all(sha(root/k)==v for k,v in frozen.items()))
 panelpath=P/'results/formal_main_v2/libero_goal/downstream/development/5185766bb353c8e6/attempt01/panel.json'
 ck('fixed_development_panel',sha(panelpath)=='ce8e3d31ab8f7616c87dd4d4031af41825713907ac184c6ea5b01d9040985aa9')
 panel=json.loads(panelpath.read_text());prefix=gate.fixed_prefix()
 accepted_ast,derived_ast,proof=adapter.derive_run(Path(runtime.__file__).read_bytes())
 a,b,tproof=adapter.base.derive_trials(Path(trials.__file__).read_bytes())
 write(OUT/'AST_proof.json',{'run_episode':proof,'trials':tproof,'recorder':gate.recorder.derivation})
 (OUT/'instrumented_run_episode.txt').write_text(ast.unparse(derived_ast)+'\n')
 ck('exact_AST_projection',proof['stripped_ast_sha256']==proof['original_ast_sha256'])
 ck('identical_original_call_sequence',proof['original_calls']==proof['projected_calls'])
 for mut in ('extra_step','change_query_order','clip_action','move_timer','change_hook_arg','remove_step_hook'):
  bad=copy.deepcopy(derived_ast)
  if mut=='extra_step':bad.body.append(ast.parse('env.step([0]*7)').body[0])
  elif mut=='change_query_order':next(x for x in ast.walk(bad) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='predict_chunk').args.reverse()
  elif mut=='clip_action':bad.body.append(ast.parse('action = np.clip(action, -1, 1)').body[0])
  elif mut=='move_timer':next(x for x in ast.walk(bad) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='query_started' for t in x.targets)).value=ast.Constant(0.)
  elif mut=='change_hook_arg':next(x for x in ast.walk(bad) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=='capture').args.append(ast.Constant('extra'))
  else:
   for node in ast.walk(bad):
    for field,ls in ast.iter_fields(node):
     if isinstance(ls,list):ls[:]=[x for x in ls if not (isinstance(x,ast.Expr) and isinstance(x.value,ast.Call) and isinstance(x.value.func,ast.Attribute) and x.value.func.attr=='step_after')]
  excepts('reject_AST_'+mut,lambda bad=bad:adapter.base.assert_projection(accepted_ast,bad),(ValueError,))
 class Env:
  def __init__(self,trace,*,mismatch=None):
   self.trace=trace;self.n=0;self.mismatch=mismatch
   native=SimpleNamespace(time=0.,**{k:np.zeros((3,),dtype=np.float64) for k in gate.recorder.SIM_FIELDS})
   self.env=SimpleNamespace(sim=SimpleNamespace(data=native),timestep=0,np_random=np.random.RandomState(81))
  def obs(self):
   o=dict(agentview_image=np.full((3,4,3),self.n,dtype=np.uint8),robot0_eye_in_hand_image=np.full((3,4,3),self.n+1,dtype=np.uint8),
     robot0_eef_pos=np.array([self.n,1,2],dtype=np.float64),robot0_eef_quat=np.array([0,0,0,1.],dtype=np.float64),robot0_gripper_qpos=np.array([.1,.2],dtype=np.float64))
   if self.mismatch=='bytes':o['agentview_image'][0,0,0]+=1
   if self.mismatch=='dtype':o['robot0_eef_pos']=o['robot0_eef_pos'].astype(np.float32)
   if self.mismatch=='shape':o['agentview_image']=o['agentview_image'].reshape(4,3,3)
   if self.mismatch=='missing':o.pop('robot0_eef_quat')
   return o
  def reset(self):self.trace.append(('reset',));self.n=0;return self.obs()
  def set_init_state(self,state):self.trace.append(('init',state.dtype.str,state.tobytes().hex()));return self.obs()
  def step(self,action):
   self.trace.append(('step',tuple(action)));self.n+=1;self.env.timestep=self.n;self.env.sim.data.time=float(self.n);self.env.sim.data.qpos[:]=self.n
   return self.obs(),0.,self.n==27,{}
  def close(self):self.trace.append(('close',))
  def render(self):raise AssertionError('no extra render allowed')
 class Policy:
  def __init__(self,trace,*,mutation=None,at=1):self.trace=trace;self.mutation=mutation;self.at=at;self.calls=0
  def reset(self):self.calls=0;self.trace.append(('policy_reset',))
  def __call__(self,ob,ins):
   self.calls+=1;self.trace.append(('query',runtime._observation_hash(ob),ins))
   if self.calls==self.at:
    if self.mutation=='bytes':ob['agentview_image'][0,0,0]+=1
    elif self.mutation=='identity':ob['agentview_image']=ob['agentview_image'].copy()
    elif self.mutation=='exception':raise RuntimeError('synthetic retained policy failure')
   arr=np.full((8,7),1.5+np.random.uniform(0,.01)+random.random()/100)
   return runtime.PolicyChunk(arr,arr,{'synthetic':True,'query':self.calls})
 def reseed():random.seed(17);np.random.seed(17)
 def canon(rows):
  rows=copy.deepcopy(rows)
  for row in rows:
   for k in ('created_utc','attempt_wall_seconds','wall_seconds'):row.pop(k,None)
   for chunk in row.get('chunks',[]):chunk.pop('engineering_seconds',None)
  return rows
 events=[]
 def emit(event,**fields):events.append({'event':event,**fields})
 original=(runtime.run_episode,trials.evaluate_formal_trials)
 with accepted.install_action_execution_compat(project_root=P,source_root=S,runtime_module=runtime,formal_trials_module=trials,
    expected_adapter_sha256='b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185',emit=emit):
  action_fn=runtime.run_episode;trace0=[];pol0={m:Policy(trace0) for m in ('A256_seed17','B256_seed17')}
  led0=runtime.TrialLedger(OUT/'baseline.jsonl',run_signature='a'*64)
  def fac0(state):trace0.append(('factory',state['task_id'],state['source_state_index']));return Env(trace0),'fixed instruction'
  trials.evaluate_formal_trials(panel,pol0,led0,fac0,reseed=reseed,stop_after=58)
  rng0=gate.recorder.global_rng();trace1=[];pol1={m:Policy(trace1) for m in ('A256_seed17','B256_seed17')}
  led1=runtime.TrialLedger(OUT/'gated.jsonl',run_signature='a'*64);ob=gate.PairedInputGate(OUT/'gated',allow_cpu_fixture=True)
  def fac1(state):trace1.append(('factory',state['task_id'],state['source_state_index']));return Env(trace1),'fixed instruction'
  with adapter.observer_scope(runtime,trials,ob,emit=emit):n=trials.evaluate_formal_trials(panel,pol1,led1,fac1,reseed=reseed,stop_after=58)
  result=ob.finish();write(OUT/'completion.json',result)
  ck('full58_29_exactpairs',n==58 and result['exact_paired_t0_checks']==29)
  ck('all174_queries_986_policy_steps',result['all_query_checks']==174 and result['executed_policy_steps_recorded']==986)
  ck('same_call_and_action_trace',trace0==trace1)
  ck('same_original_ledger_except_wall_and_UTC',canon(led0.events)==canon(led1.events))
  ck('same_final_global_RNG',rng0==gate.recorder.global_rng())
  ck('accepted_actions_above1_not_clipped',all(r['executed_actions'][0][0]>1 for r in led1.events if r['event']=='result'))
  ck('source_bindings_restored_after_success',runtime.run_episode is action_fn and trials.run_episode is action_fn)
  # Mismatch gate runs before B's first policy invocation. Completed A remains
  # durable; B start and exact capture remain, with no fake result appended.
  for kind in ('bytes','dtype','shape','instruction'):
   trace=[];q={m:Policy(trace) for m in ('A256_seed17','B256_seed17')};led=runtime.TrialLedger(OUT/(kind+'.jsonl'),run_signature='b'*64)
   bad=gate.PairedInputGate(OUT/('mismatch_'+kind),allow_cpu_fixture=True);count=[0]
   def factory(state):
    count[0]+=1; second=count[0]==2
    return Env(trace,mismatch=kind if second and kind!='instruction' else None),('other instruction' if second and kind=='instruction' else 'fixed instruction')
   with adapter.observer_scope(runtime,trials,bad,emit=emit):
    excepts('reject_paired_'+kind,lambda:trials.evaluate_formal_trials(panel,q,led,factory,reseed=reseed,stop_after=58),(gate.GateAbort,))
   rows=[r for r in led.events if r['event']=='result']
   ck('pre_B_failstop_'+kind,len(rows)==1 and q['B256_seed17'].calls==0 and count[0]==2 and bad.dead)
   ck('partial_A_and_Bstart_retained_'+kind,len(led.events)==3 and led.events[-1]['event']=='start' and len([x for x in trace if x[0]=='close'])==2)
   ck('mismatch_bytes_durable_'+kind,(bad.output/'events.jsonl').exists() and bad.last_gate_abort['reason']=='paired_t0_input_mismatch_before_B_policy')
   excepts('failed_finish_rejected_'+kind,bad.finish,(gate.GateAbort,))
  # Mutation after a previous accepted chunk preserves executed step sidecar.
  for kind,at in [('bytes',1),('identity',1),('bytes',2)]:
   trace=[];led=runtime.TrialLedger(OUT/f'mutation_{kind}{at}.jsonl',run_signature='c'*64)
   bad=gate.PairedInputGate(OUT/f'mutation_{kind}{at}',allow_cpu_fixture=True);pa=Policy(trace,mutation=kind,at=at)
   with adapter.observer_scope(runtime,trials,bad,emit=emit):
    excepts('reject_input_mutation_'+kind+str(at),lambda:trials.evaluate_formal_trials(panel,{'A256_seed17':pa,'B256_seed17':Policy(trace)},led,lambda state:(Env(trace),'fixed instruction'),reseed=reseed,stop_after=58),(gate.GateAbort,))
   ck('mutation_stops_before_next_action_'+kind+str(at),pa.calls==at and bad.executed_policy_steps==8*(at-1) and not any(r['event']=='result' for r in led.events))
   ck('mutation_detected_reason_'+kind+str(at),bad.last_gate_abort['reason']=='policy_changed_input_identity_or_bytes')
  # Policy exceptions stay the original durable result; gate halts after it.
  trace=[];bad=gate.PairedInputGate(OUT/'policy_exception',allow_cpu_fixture=True);led=runtime.TrialLedger(OUT/'policy_exception.jsonl',run_signature='d'*64)
  with adapter.observer_scope(runtime,trials,bad,emit=emit):
   excepts('original_policy_exception_retained',lambda:trials.evaluate_formal_trials(panel,{'A256_seed17':Policy(trace,mutation='exception'),'B256_seed17':Policy(trace)},led,lambda state:(Env(trace),'fixed instruction'),reseed=reseed,stop_after=58),(gate.GateAbort,))
  ck('original_policy_error_row_retained',len(led.events)==2 and led.events[1]['status']=='policy_error' and bad.dead)
  # Capture failures do not enter original Exception-only retry loops.
  for kind in ('observation','rng','sim'):
   e=Env([]);o=e.obs()
   def sink(event,kind=kind):
    if kind=='observation':o['agentview_image'][0,0,0]+=1
    elif kind=='rng':np.random.random()
    else:e.env.sim.data.qpos[0]+=1
   bad=gate.PairedInputGate(OUT/('observer_mutation_'+kind),allow_cpu_fixture=True,sink=sink)
   excepts('reject_observer_'+kind,lambda:bad.capture('sentinel',e,o),(gate.GateAbort,))
   ck('observer_failstop_'+kind,bad.dead)
  bad=gate.PairedInputGate(OUT/'bad_order',allow_cpu_fixture=True)
  identity=trials._identity(panel,panel['states'][0],'B256_seed17')
  excepts('wrong_method_order_rejected',lambda:bad.trial_begin(identity,panel['states'][0]),(gate.GateAbort,))
  ck('wrong_order_latched',bad.dead)
  bad=gate.PairedInputGate(OUT/'journal_failure',allow_cpu_fixture=True)
  def badrecord(event):raise OSError('synthetic write failure')
  bad._record=badrecord
  e=Env([]);o=e.obs();bad.current={k:prefix[0][k] for k in gate.recorder.IDENTITY_KEYS};bad.begun=1;bad.query_counts[bad.current['trial_id']]=0
  excepts('journal_failure_stops_before_policy',lambda:bad.capture('t0_query_before',e,o,control_step=0,instruction='fixed instruction'),(gate.GateAbort,))
  ck('journal_failure_has_in_memory_receipt',bad.dead and bad.last_gate_abort.get('abort_record_failure') is not None)
  excepts('no_retry_after_journal_failure',lambda:bad.capture('t0_query_before',e,o,control_step=0,instruction='fixed instruction'),(gate.GateAbort,))
 ck('original_functions_restored',original==(runtime.run_episode,trials.evaluate_formal_trials))
 for root in (R,S):ck('frozen173_after_'+root.name,all(sha(root/k)==v for k,v in frozen.items()))
 torch=sys.modules.get('torch');cuda=sys.modules.get('torch.cuda')
 ck('CUDA_not_initialized',cuda is None or not cuda.__dict__.get('_initialized'))
 ck('no_mujoco_import',not any(k.startswith('mujoco') for k in sys.modules))
 write(OUT/'scope_events.json',events)
 return {'status':'passed_CPU_source_candidate_only','checks':checks,'check_count':len(checks),'GPU_jobs':0,'Slurm_queries':0,'production_state_changes':0,'scientific_trials_added':0,'old200_HOLD':True,'new_Goal_science_HOLD':True,'final_release':False,'real_GPU_acceptance':False}
try:report=main()
except BaseException as e:
 report={'status':'failed_CPU_candidate','checks':checks,'error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'GPU_jobs':0,'scientific_trials_added':0};write(OUT/'report.json',report);print(json.dumps({k:report[k] for k in ('status','error_type','error')}));raise
write(OUT/'report.json',report);print(json.dumps({k:report[k] for k in ('status','check_count','GPU_jobs')}))

from pathlib import Path
from types import SimpleNamespace
import ast, copy, hashlib, importlib.util, json, random, sys, time, traceback
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=Path(__file__).parent;C=R/'.local/goal_prefix58_repair_20261020T1825';O=D/'attempt02'
checks=[];negative=[];sources=[];started=time.process_time()
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):
 p=Path(p)
 base=R if p.is_relative_to(R) else P
 assert p.is_relative_to(base),str(p)
 return dict(path=p.relative_to(base).as_posix(),server_root=str(base),sha256=h(p),bytes=p.stat().st_size)
def write(name,value):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
 return ref(p)
def ck(name,ok):
 checks.append(dict(name=name,passed=bool(ok)))
 if not ok:raise AssertionError(name)
def load(p,name,pin):
 ck('source pin '+name,h(p)==pin);sources.append(ref(p));spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def reject(name,fn,typ,contains=None):
 try:fn()
 except typ as e:
  ck(name,contains is None or contains in str(e));negative.append(dict(name=name,error_type=type(e).__name__,error=str(e),rejected=True));return e
 raise AssertionError('accepted negative '+name)
def hooks(tree):return [x for x in ast.walk(tree) if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call) and isinstance(x.value.func,ast.Attribute) and isinstance(x.value.func.value,ast.Name) and x.value.func.value.id=='_cti_prefix_observer']
def remove_hook(tree,hook):
 for n in ast.walk(tree):
  for k,v in ast.iter_fields(n):
   if isinstance(v,list) and hook in v:v.remove(hook);return
 raise AssertionError('hook missing')
class JournalProxy:
 def __init__(self,path,callback):self.path=path;self.callback=callback;self.called=False
 def open(self,mode):
  delegate=self.path.open(mode);parent=self
  class Stream:
   def __enter__(self):delegate.__enter__();return self
   def write(self,b):return delegate.write(b)
   def __exit__(self,*args):
    result=delegate.__exit__(*args)
    if not parent.called:parent.called=True;parent.callback()
    return result
  return Stream()
class NativeFixtureEnv:
 def __init__(self,trace=None):
  self.trace=[] if trace is None else trace
  native=SimpleNamespace(qpos=np.zeros(3),qvel=np.zeros(3),act=np.zeros(2),ctrl=np.zeros(7),qacc_warmstart=np.zeros(3),mocap_pos=np.zeros((1,3)),mocap_quat=np.zeros((1,4)),time=0.)
  self.env=SimpleNamespace(sim=SimpleNamespace(data=native),np_random=np.random.RandomState(47),rng2=np.random.default_rng(49),timestep=0,cur_time=0.,done=False,hard_reset=True,deterministic_reset=False)
  self.steps=0
 def observation(self):
  return {'agentview_image':np.full((3,3,3),self.steps,dtype=np.uint8),'robot0_eye_in_hand_image':np.full((3,3,3),self.steps+1,dtype=np.uint8),'robot0_eef_pos':self.env.sim.data.qpos.copy(),'robot0_eef_quat':np.array([0.,0.,0.,1.]),'robot0_gripper_qpos':np.array([.01,.02])}
 def reset(self):
  self.steps=0;self.trace.append(['reset',float(np.random.random()),random.random()]);return self.observation()
 def set_init_state(self,initial):
  self.trace.append(['set_init_state',np.asarray(initial).tolist()]);self.env.sim.data.qpos[:]=np.asarray(initial)[:3];return self.observation()
 def step(self,action):
  self.steps+=1;self.env.timestep+=1;self.env.sim.data.qpos[0]+=float(action[0]);self.env.sim.data.time+=.05
  self.trace.append(['step',list(action)]);return self.observation(),0.,self.steps>=27,{}
 def close(self):self.trace.append(['close'])
class Ledger:
 def __init__(self):self.events=[]
 def completed(self):return {r['trial_id'] for r in self.events if r.get('event')=='result' and r.get('status')=='completed'}
 def append(self,row):self.events.append(copy.deepcopy(row))
def canonical(value):
 if type(value) is dict:return {k:canonical(v) for k,v in value.items() if k not in ('created_utc','wall_seconds','engineering_seconds','attempt_wall_seconds')}
 if type(value) in (tuple,list):return [canonical(v) for v in value]
 return value
def main():
 O.mkdir(exist_ok=False)
 ad=load(C/'revision01/ast_observer_v2.py','ind_g58_ast','e88222ea96c290019b2ec838ff68fe25a9f94d115ae996d92735e18e4cf0800e')
 ob=load(C/'revision01/observer_v3.py','ind_g58_observer','7a33c4ec531e0524a5e30b51e18205dc7d354868afa6190e3f39dcf14b283241')
 oldad=load(C/'original_sources/ast_observer.py','ind_g58_old_ast','defb33269acd7e464095ff622723a0168b324f19f68f7ed317475a83895cb89e')
 oldob=load(C/'original_sources/observer_v2.py','ind_g58_old_observer','9fc6b3eb8e54c624edafcb67e98385a974b8dbcb850a12cf8a540583660da85f')
 source_manifest=C/'revision01/source_manifest.json';ck('candidate manifest pin',h(source_manifest)=='44b4aef4e80053f6b9567a2aca954853b116f30f4cf2c5c072a97d1b6dadb3aa');sources.append(ref(source_manifest))
 prefixp=C/'inputs/original_prefix58.json';ck('original prefix pin',h(prefixp)=='1e786af6b4aafb52dba32bce1494c5e4dd4ef05c41f10cb3b9a77342c2cbcb28');prefix=json.loads(prefixp.read_bytes())['rows'];sources.append(ref(prefixp))
 raw=(S/'src/cti_vla/evaluation/libero_runtime.py').read_bytes();t_raw=(S/'src/cti_vla/evaluation/formal_trials.py').read_bytes()
 a,b,rproof=ad.derive_run(raw);ta,tb,tproof=ad.derive_trials(t_raw)
 oa,obn,op=oldad.derive_run(raw);ota,otb,otp=oldad.derive_trials(t_raw)
 ck('both exact original and instrumented ASTs unchanged',all(ad.text(x)==ad.text(y) for x,y in [(a,oa),(b,obn),(ta,ota),(tb,otb)]))
 ck('all scientific call expressions/order identical after projection',rproof['original_calls']==rproof['projected_calls'] and tproof['original_calls']==tproof['projected_calls'])
 ck('normalization whitelist matches exact pinned old layouts',ad.OBSERVER_LAYOUT_V2=={a.name:(h0:=ad.sha(ad.text(oa).encode()),ad.sha(ad.text(obn).encode())),ta.name:(ad.sha(ad.text(ota).encode()),ad.sha(ad.text(otb).encode()))})
 write('independent_AST_proof.json',dict(run=rproof,trials=tproof,whitelist=ad.OBSERVER_LAYOUT_V2,scientific_AST_changed=False))
 for base,derived,label in [(a,b,'episode'),(ta,tb,'trials')]:
  for mutation in ['sideeffect_arg','sideeffect_keyword','sideeffect_stararg','sideeffect_doublekw','duplicate','omit','move','phase','method','reset_return']:
   bad=copy.deepcopy(derived);hook=hooks(bad)[0]
   if mutation=='sideeffect_arg':hook.value.args.append(ast.parse('env.step([0.0] * 7)',mode='eval').body)
   elif mutation=='sideeffect_keyword':hook.value.keywords.append(ast.keyword(arg='wait_steps',value=ast.parse('np.random.random()',mode='eval').body))
   elif mutation=='sideeffect_stararg':hook.value.args.append(ast.Starred(value=ast.parse('expensive_side_effect()',mode='eval').body,ctx=ast.Load()))
   elif mutation=='sideeffect_doublekw':hook.value.keywords.append(ast.keyword(arg=None,value=ast.parse('side_effect_kwargs()',mode='eval').body))
   elif mutation=='duplicate':bad.body.append(copy.deepcopy(hook))
   elif mutation=='omit':remove_hook(bad,hook)
   elif mutation=='move':remove_hook(bad,hook);bad.body.append(hook)
   elif mutation=='phase':hook.value.args[0]=ast.Constant('altered-phase')
   elif mutation=='method':hook.value.func.attr='trial_end' if hook.value.func.attr!='trial_end' else 'capture'
   else:bad.body.append(ast.parse('_cti_prefix_reset_return = env.reset()').body[0])
   if mutation in ('sideeffect_arg','sideeffect_keyword','sideeffect_stararg','sideeffect_doublekw','duplicate','omit','move','phase','method'):
    oldad.assert_projection(base,bad);ck('old gap demonstrably accepted '+label+' '+mutation,True)
   reject('exact layout rejects '+label+' '+mutation,lambda bad=bad,base=base:ad.assert_projection(base,bad),ValueError,'versioned whitelist')
 reject('unregistered raw source',lambda:ad.derive_run(raw+b'\n'),ValueError,'unregistered')
 for guard in ['global_rng','object_guard','passive_environment']:
  for et in [RuntimeError,KeyboardInterrupt,SystemExit,ob.ObserverAbort]:
   name=guard+'_'+et.__name__;item=ob.PassiveObserver(O/('initial_'+name),prefix,allow_cpu_fixture=True);original=getattr(ob,guard)
   def broken(*args,et=et,**kwargs):raise et('injected initial '+name)
   setattr(ob,guard,broken)
   try:reject('initial guard '+name,lambda:item.capture('independent_initial'),ob.ObserverAbort,'injected initial')
   finally:setattr(ob,guard,original)
   rows=[json.loads(x) for x in item.journal.read_text().splitlines()];ck('initial latched and retained '+name,item.dead and item.event_count==0 and len(rows)==1 and rows[0]['event']=='observer_abort' and not rows[0]['automatic_retry'])
   reject('no retry '+name,lambda:item.capture('retry'),ob.ObserverAbort,'no retry')
 olditem=oldob.PassiveObserver(O/'old_initial_gap',prefix,allow_cpu_fixture=True);original=oldob.global_rng
 def broken_old():raise RuntimeError('old initial gap')
 oldob.global_rng=broken_old
 try:reject('old reader raises ordinary error',lambda:olditem.capture('initial'),RuntimeError,'old initial gap')
 finally:oldob.global_rng=original
 olditem.capture('old_retry_accepted');ck('old reader did not latch unlike repair',not olditem.dead and olditem.event_count==1)
 for et in [OSError,KeyboardInterrupt,SystemExit]:
  item=ob.PassiveObserver(O/('recorder_'+et.__name__),prefix,allow_cpu_fixture=True)
  class BrokenJournal:
   def open(self,*a):raise et('injected record failure')
  item.journal=BrokenJournal();original=ob.global_rng
  def broken():raise ValueError('initial failing read')
  ob.global_rng=broken
  try:reject('abort recorder '+et.__name__,lambda:item.capture('initial'),ob.ObserverAbort,'initial failing read')
  finally:ob.global_rng=original
  ck('in-memory abort retained '+et.__name__,item.dead and item.last_abort['abort_record_error_type']==et.__name__ and item.last_abort['error_type']=='ValueError')
  write('recorder_'+et.__name__+'_memory.json',item.last_abort)
 mutations=list(ob.SIM_FIELDS)+['sim_time','env_scalar','env_RandomState','env_Generator','observation','global_numpy','global_python']
 for name in mutations:
  env=NativeFixtureEnv();obs=env.observation();item=ob.PassiveObserver(O/('late_'+name),prefix,allow_cpu_fixture=True);journal=item.journal;rs=random.getstate();ns=np.random.get_state()
  def mutate(name=name):
   if name in ob.SIM_FIELDS:getattr(env.env.sim.data,name).flat[0]+=1
   elif name=='sim_time':env.env.sim.data.time+=1
   elif name=='env_scalar':env.env.timestep+=1
   elif name=='env_RandomState':env.env.np_random.random_sample()
   elif name=='env_Generator':env.env.rng2.random()
   elif name=='observation':obs['agentview_image'].flat[0]+=1
   elif name=='global_numpy':np.random.random()
   else:random.random()
  item.journal=JournalProxy(journal,mutate)
  try:reject('journal exit mutation '+name,lambda:item.capture('journal_exit',env,obs),ob.ObserverAbort,'journal write changed')
  finally:random.setstate(rs);np.random.set_state(ns)
  rows=[json.loads(x) for x in journal.read_text().splitlines()];ck('late abort preserved '+name,item.dead and item.event_count==0 and len(rows)==2 and rows[-1]['event']=='observer_abort')
  reject('late retry '+name,lambda:item.capture('retry',env,obs),ob.ObserverAbort,'no retry')
 oldenv=NativeFixtureEnv();olditem=oldob.PassiveObserver(O/'old_late_gap',prefix,allow_cpu_fixture=True);j=olditem.journal
 olditem.journal=JournalProxy(j,lambda:oldenv.env.rng2.random());olditem.capture('old_late',oldenv,oldenv.observation());ck('old final environment RNG gap demonstrated',not olditem.dead and olditem.event_count==1)
 # The frozen trial and episode functions execute the entire original 58-prefix
 # with independent CPU policy/environment substitutes; real source is not modified.
 sys.path.insert(0,str(S/'src'));from cti_vla.evaluation import libero_runtime as rt,formal_trials as ft
 adapter=load(P/'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py','ind_g58_action_context','b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185')
 panelp=P/'results/formal_main_v2/libero_goal/downstream/development/5185766bb353c8e6/attempt01/panel.json';ck('official development panel byte identity',h(panelp)=='ce8e3d31ab8f7616c87dd4d4031af41825713907ac184c6ea5b01d9040985aa9');panel=json.loads(panelp.read_bytes());ck('only development panel read',panel['suite']=='libero_goal' and panel['split']=='development')
 identities=[{k:ft._identity(panel,st,mid)[k] for k in ob.IDENTITY_KEYS} for st in panel['states'] for mid in ['A256_seed17','B256_seed17']][:58]
 ck('fixed 58/29 original identity ordering',identities==[{k:x[k] for k in ob.IDENTITY_KEYS} for x in prefix] and len({x['state_trial_id'] for x in identities})==29)
 ck('target last pair task2 index42',all(x['task_id']==2 and x['source_state_index']==42 for x in identities[-2:]))
 write('prefix_identity.json',dict(rows=identities,source=ref(prefixp),synthetic_trials_only=True))
 events=[]
 def emit(event,**kw):events.append(dict(event=event,**kw))
 class Policy:
  def __init__(self,trace,label):self.trace=trace;self.label=label;self.n=0
  def reset(self):self.n=0;self.trace.append(['policy_reset',self.label])
  def __call__(self,observation,instruction):
   self.n+=1;draw=float(np.random.random());rd=random.random();self.trace.append(['query',self.label,self.n,draw,rd])
   actions=np.full((8,7),.2);actions[0,0]=1.2
   return rt.PolicyChunk(np.zeros((8,7)),actions,{'synthetic_CPU':True,'method':self.label})
 def execute(observe):
  trace=[];ledger=Ledger();policies={k:Policy(trace,k) for k in ['A256_seed17','B256_seed17']}
  def reseed():random.seed(17);np.random.seed(17);trace.append(['reseed',17])
  def factory(state):trace.append(['factory',state['trial_id']]);return NativeFixtureEnv(trace),'fixed CPU instruction'
  item=ob.PassiveObserver(O/'complete_prefix58',prefix,allow_cpu_fixture=True) if observe else None
  if item:
   with ad.observer_scope(rt,ft,item,emit=emit):ran=ft.evaluate_formal_trials(panel,policies,ledger,factory,reseed=reseed,stop_after=58)
   result=item.finish()
  else:ran=ft.evaluate_formal_trials(panel,policies,ledger,factory,reseed=reseed,stop_after=58);result=None
  return dict(ran=ran,ledger=canonical(ledger.events),trace=trace,rng=ob.global_rng(),observer_result=result)
 original_bindings=(rt.run_episode,ft.run_episode,ft.evaluate_formal_trials)
 with adapter.install_action_execution_compat(project_root=P,source_root=S,runtime_module=rt,formal_trials_module=ft,expected_adapter_sha256='b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185',emit=emit):
  active=(rt.run_episode,ft.run_episode,ft.evaluate_formal_trials);base=execute(False);observed=execute(True)
  ck('all 58 exact frozen-trial baseline/observed results',base['ran']==observed['ran']==58 and base['ledger']==observed['ledger'])
  ck('all 58 original env/policy call traces and RNG match',base['trace']==observed['trace'] and base['rng']==observed['rng'])
  ck('accepted action bindings restored',active==(rt.run_episode,ft.run_episode,ft.evaluate_formal_trials))
 ck('all original bindings restored',original_bindings==(rt.run_episode,ft.run_episode,ft.evaluate_formal_trials))
 rows=[x for x in observed['ledger'] if x['event']=='result'];ck('no policy clipping/action count drift',len(rows)==58 and all(x['wait_steps']==10 and x['control_steps']==17 and x['policy_calls']==3 and x['executed_actions'][0][0]>1 for x in rows))
 caprows=[json.loads(x) for x in (O/'complete_prefix58/events.jsonl').read_text().splitlines()];ck('all 58 phases plus finish retained',sum(x.get('event')=='trial_end' for x in caprows)==58 and caprows[-1]['phase']=='original_runner_returned' and not any(x.get('event')=='observer_abort' for x in caprows))
 write('complete_prefix58_comparison.json',dict(baseline=base,observed=observed,synthetic_CPU_only=True));write('context_events.json',events)
 inv=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_bytes());ck('173 frozen source count',len(inv['files'])==173)
 for n,pin in inv['files'].items():
  for basepath,label in [(R,'R'),(S,'S')]:ck('frozen '+label+' '+n,h(basepath/n)==pin)
 cuda=sys.modules.get('torch.cuda');ck('no CUDA initialized',cuda is None or not cuda.__dict__.get('_initialized',False))
 report=dict(schema='formal_main_v2',kind='independent_goal_prefix58_bounded_repair_CPU_review',status='passed_CPU_repair_review_not_GPU_admission',checks=checks,passed=len(checks),negative_cases=negative,negative_count=len(negative),sources=sources,three_original_findings_closed_in_CPU=True,original_hook_layout_and_scientific_AST_unchanged=True,full58_original_trial_CPU_trace_and_rng_equal=True,real_GPU_executed=False,original_200_HOLD=True,new_Goal_scientific_HOLD=True,sealed_final_read=False,production_or_state_or_Git_or_Slurm_writes=False,source173_R_S_unchanged=True,CPU_seconds=time.process_time()-started,limits=['CPU fixtures do not establish native MuJoCo/CUDA passivity or reproduce the original GPU anomaly.','If both initial reader and all journaling fail, dead and last_abort are retained in memory only; a separately reviewed outer must retain the fatal exit/error.','Original performance timers remain in their original AST positions; passive observations add CPU/I/O wall time and are not valid O2A timing.','A separately reviewed one-attempt outer, source identity admission, reservation, and root registration are still required before any GPU invocation.'],blockers_for_three_bounded_repairs=[])
 print(json.dumps(dict(review=write('independent_review.json',report),passed=len(checks),negative_count=len(negative),CPU_seconds=report['CPU_seconds'])))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  if not O.exists():O.mkdir()
  write('failure.json',dict(status='independent_CPU_harness_failed',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),checks=checks,negative_cases=negative,CPU_seconds=time.process_time()-started));raise

"""Independent CPU audit only; no GPU, simulator, deployment, or scientific admission."""
from __future__ import annotations
import ast, copy, hashlib, importlib.util, json, random, sys, time, traceback, types
from pathlib import Path
from types import SimpleNamespace
import numpy as np

R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
A=R/'.local/goal_prefix58_candidate_20261020T1644'
D=Path(__file__).parent
OUT=D/'attempt01'
MANIFEST_SHA='9a2f425a7d6e715c6a108a400bd1a92fe713e2b368bdc3a2ab2e0e3a4da76595'
PINS={'observer_v2.py':'9fc6b3eb8e54c624edafcb67e98385a974b8dbcb850a12cf8a540583660da85f','ast_observer.py':'defb33269acd7e464095ff622723a0168b324f19f68f7ed317475a83895cb89e','prepare_candidate_v1.py':'1ea7f134bf20a59983bc2930b7d14d598e6be3e5823326b58af84f13ac5a4fe5'}
checks=[]; negatives=[]; findings=[]; artifacts={}; entered=time.monotonic(); entered_cpu=time.process_time()

def h(path):
 digest=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):digest.update(block)
 return digest.hexdigest()
def write(rel,obj):
 path=OUT/rel;path.parent.mkdir(exist_ok=True,parents=True)
 with path.open('x',encoding='utf-8') as f:json.dump(obj,f,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
 return {'source':str(path.relative_to(R)),'path':str(path.relative_to(D)),'sha256':h(path),'bytes':path.stat().st_size}
def ck(label,ok,detail=None):
 checks.append({'name':label,'passed':bool(ok),'detail':detail})
 if not ok:raise AssertionError(label)
def load(path,name,pin=None):
 if pin is not None:ck('source pin '+name,h(path)==pin)
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def audit_guard(event,args):
 if event in ('subprocess.Popen','os.system','os.exec','os.posix_spawn','socket.connect'):
  raise RuntimeError('independent CPU audit forbids process/network execution')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes)):
   p=Path(path).resolve();writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and bool(flags & (1|2|64|512|1024)))
   if writing and not p.is_relative_to(D):raise RuntimeError('write outside independent private directory: '+str(p))
   if not writing and (p.suffix in ('.pt','.pth','.safetensors','.pruned_init') or '/sealed/' in str(p)):
    raise RuntimeError('weight/sealed-state read forbidden in independent CPU audit')
def clean_result(row):
 row=copy.deepcopy(row)
 for key in ('wall_seconds','attempt_wall_seconds','created_utc'):row.pop(key,None)
 for chunk in row.get('chunks',[]):chunk.pop('engineering_seconds',None)
 return row

def run():
 OUT.mkdir(exist_ok=False)
 sys.dont_write_bytecode=True
 sys.addaudithook(audit_guard)
 ck('candidate delivery manifest pin',h(A/'delivery_manifest.json')==MANIFEST_SHA)
 m=json.loads((A/'delivery_manifest.json').read_text()); ck('manifest unique paths',len({x['path'] for x in m['files']})==len(m['files'])==192)
 actual=[]
 for row in m['files']:
  p=A/row['path'];ck('member '+row['path'],p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(A) and p.stat().st_size==row['bytes'] and h(p)==row['sha256']);actual.append(row)
 ck('manifest full inventory',set(x['path'] for x in m['files'])=={str(p.relative_to(A)) for p in A.rglob('*') if p.is_file()}-{'delivery_manifest.json'})
 artifacts['candidate_inventory']=write('candidate_inventory.json',{'manifest_sha256':MANIFEST_SHA,'files':actual,'total_bytes':sum(x['bytes'] for x in actual)})
 inv=R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';ck('frozen inventory pin',h(inv)=='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 frozen=json.loads(inv.read_text())['files'];ck('173 frozen files',len(frozen)==173)
 frozen_before={str(root):{p:h(root/p) for p in frozen} for root in (R,S)}
 for root,vals in frozen_before.items():ck('173 exact before '+root,vals==frozen)
 observer=load(A/'observer_v2.py','ind_prefix_observer',PINS['observer_v2.py']);adapter=load(A/'ast_observer.py','ind_prefix_ast',PINS['ast_observer.py'])
 prefix_path=A/'inputs/original_prefix58.json';ck('prefix identity pin',h(prefix_path)=='1e786af6b4aafb52dba32bce1494c5e4dd4ef05c41f10cb3b9a77342c2cbcb28')
 prefix=json.loads(prefix_path.read_text())['rows'];ck('prefix 58 records and 29 states',len(prefix)==58 and len({r['state_trial_id'] for r in prefix})==29)
 ck('prefix original 56 actions/query counters',sum(r['policy_calls'] for r in prefix[:56])==916 and sum(r['control_steps'] for r in prefix[:56])==7124)
 ck('57/58 anomaly task and source',all(r['task_id']==2 and r['source_state_index']==42 for r in prefix[56:]) and [r['method'] for r in prefix[56:]]==['A256_seed17','B256_seed17'])
 sys.path.insert(0,str(S/'src'))
 from cti_vla.evaluation import libero_runtime as runtime,formal_trials as trials
 accepted=load(P/'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py','ind_prefix_accepted','b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185')
 ck('real pinned source bodies',h(runtime.__file__)==adapter.RUNTIME_SHA and h(trials.__file__)==adapter.TRIALS_SHA)
 base,derived,proof=adapter.derive_run(Path(runtime.__file__).read_bytes());tb,td,tp=adapter.derive_trials(Path(trials.__file__).read_bytes())
 ck('accepted AST projection',proof['original_ast_sha256']==proof['stripped_ast_sha256'] and tp['original_ast_sha256']==tp['stripped_ast_sha256'])
 ck('original call expressions after projection',proof['original_calls']==proof['projected_calls'] and tp['original_calls']==tp['projected_calls'])
 # Inspect the exact installed candidate hooks as well as the projection proof.
 hooks=[]
 for label,tree in [('run',derived),('trials',td)]:
  for node in ast.walk(tree):
   if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id==adapter.NAME:
    hooks.append({'function':label,'call':ast.unparse(node)})
    for expression in node.args+[x.value for x in node.keywords]:
     ck('exact installed hook has no nested call '+ast.unparse(node),not any(isinstance(x,ast.Call) for x in ast.walk(expression)))
 artifacts['ast_proof']=write('ast_proof.json',{'run':proof,'trial_loop':tp,'installed_hooks':hooks})
 # Original projection rejects ordinary mutations; then test the uncovered hook argument surface.
 for label,statement in [('step','env.step([0.0]*7)'),('render','env.render()'),('rng','random.random()')]:
  bad=copy.deepcopy(derived);bad.body.append(ast.parse(statement).body[0])
  try:adapter.assert_projection(base,bad)
  except ValueError as e:negatives.append({'test':'ordinary_extra_'+label,'rejected':True,'error':str(e)})
  else:raise AssertionError('ordinary mutation accepted')
 counter=[]
 for label,statement in [('step_argument',adapter.NAME+'.capture("extra", env.step([0.0]*7))'),('rng_keyword',adapter.NAME+'.capture("extra", wait_steps=np.random.random())')]:
  bad=copy.deepcopy(derived);bad.body.insert(0,ast.parse(statement).body[0]);verdict=adapter.assert_projection(base,bad)
  counter.append({'mutation':statement,'accepted_by_projection':True,'stripped_sha256':verdict['stripped_ast_sha256']})
 ck('projection counterexample observed',len(counter)==2)
 artifacts['projection_counterexample']=write('projection_counterexample.json',{'scope':'synthetic AST only; current exact derive hooks separately contain no nested calls','cases':counter})
 findings.append({'id':'G58-AST-01','severity':'medium','category':'proof coverage','source':'ast_observer.py:68-88','observed':'Projection removes observer call expressions without validating their arguments; extra env.step/RNG in such arguments is accepted by the projection.','current_candidate_limit':'Exact current derived hooks were independently inspected and contain no nested calls. No extra environment step or RNG draw was observed from those exact hooks.','minimal_fix':'Validate exact inserted hook AST against a versioned whitelist, including argument expressions and count/order, before inverse projection; reject these two negative cases.'})
 panelpath=P/'results/formal_main_v2/libero_goal/downstream/development/5185766bb353c8e6/attempt01/panel.json';panel=json.loads(panelpath.read_text())
 ck('development panel only',panel['suite']=='libero_goal' and panel['split']=='development' and len(panel['states'])==100)
 methods=['A256_seed17','B256_seed17'];ids=[trials._identity(panel,st,mid) for st in panel['states'] for mid in methods][:58]
 keys=observer.IDENTITY_KEYS
 ck('all original first58 identities', [{k:x[k] for k in keys} for x in ids]==[{k:x[k] for k in keys} for x in prefix])
 artifacts['identity_evidence']=write('identity_evidence.json',{'panel':{'source':str(panelpath),'sha256':h(panelpath)},'prefix_source':{'source':str(prefix_path.relative_to(R)),'sha256':h(prefix_path)},'identities':ids,'development_only':True,'initial_state_values_copied_into_report':False})
 class Env:
  def __init__(self,trace,success_at=23):
   self.trace=trace;self.t=0;self.success_at=success_at
   self.env=SimpleNamespace(sim=SimpleNamespace(data=SimpleNamespace(time=0.0,**{k:np.zeros((4,),dtype=np.float64) for k in observer.SIM_FIELDS})),timestep=0,cur_time=0.0,np_random=np.random.default_rng(829))
  def obs(self):
   image=(np.arange(72,dtype=np.uint8).reshape(4,6,3)+self.t)[:,::-1,:]
   wrist=np.asfortranarray((np.arange(36,dtype=np.uint8).reshape(3,4,3)+self.t))
   pos=np.array([self.t,2.,3.,4.,5.,6.])[::2]
   return {'agentview_image':image,'robot0_eye_in_hand_image':wrist,'robot0_eef_pos':pos,'robot0_eef_quat':np.array([0.,0.,0.,1.]),'robot0_gripper_qpos':np.array([self.t/100.,.2]),'shared_image_view':image[::2]}
  def reset(self):self.trace.append(['reset']);self.t=0;return self.obs()
  def set_init_state(self,value):self.trace.append(['set_init_state',value.dtype.str,hashlib.sha256(value.tobytes()).hexdigest()]);return self.obs()
  def step(self,value):
   self.trace.append(['step',list(value)]);self.t+=1;self.env.timestep=self.t;self.env.cur_time=self.t/50;self.env.sim.data.time=self.env.cur_time;self.env.sim.data.qpos[:]=self.t
   self.env.np_random.random()
   return self.obs(),0.0,self.t==self.success_at,{}
  def close(self):self.trace.append(['close'])
  def render(self):raise AssertionError('forbidden render')
  def get_sim_state(self):raise AssertionError('forbidden simulator accessor')
 class Policy:
  def __init__(self,trace):self.trace=trace;self.count=0
  def reset(self):self.count=0;self.trace.append(['policy_reset'])
  def __call__(self,obs,instruction):
   self.count+=1;self.trace.append(['query',runtime._observation_hash(obs),instruction])
   scalar=random.random()+np.random.random()
   actions=np.arange(56,dtype=np.float64).reshape(8,7)/100+1.2+scalar/100
   return runtime.PolicyChunk(actions/2,actions,{'synthetic':True,'query':self.count})
 emitted=[]
 def emit(event,**kw):emitted.append({'event':event,**kw})
 original_run=runtime.run_episode;original_eval=trials.evaluate_formal_trials
 with accepted.install_action_execution_compat(project_root=P,source_root=S,runtime_module=runtime,formal_trials_module=trials,expected_adapter_sha256='b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185',emit=emit):
  active=runtime.run_episode
  traces=[];results=[];rngs=[]
  for instrumented in (False,True):
   random.seed(4501);np.random.seed(4501);trace=[];env=Env(trace);policy=Policy(trace)
   if instrumented:
    obs=observer.PassiveObserver(OUT/'passive_episode',prefix,allow_cpu_fixture=True);obs.current={k:ids[0][k] for k in keys};obs.begun=1
    with adapter.observer_scope(runtime,trials,obs,emit=emit):row=runtime.run_episode(env,policy,'independent synthetic instruction',[1.,2.,3.],wait_steps=10,max_steps=300)
   else:row=runtime.run_episode(env,policy,'independent synthetic instruction',[1.,2.,3.],wait_steps=10,max_steps=300)
   traces.append(trace);results.append(clean_result(row));rngs.append(observer.global_rng())
  ck('independent exact original reset/step/query order',traces[0]==traces[1]);ck('independent exact original actions/results excluding timers',results[0]==results[1]);ck('independent final global RNG identical',rngs[0]==rngs[1])
  ck('independent no clipping and exact counts',results[1]['executed_actions'][0][0]>1.0 and results[1]['wait_steps']==10 and results[1]['control_steps']==13 and results[1]['policy_calls']==2)
  ck('accepted aliases restored',runtime.run_episode is active and trials.run_episode is active and trials.evaluate_formal_trials is original_eval)
  events=[json.loads(l) for l in obs.journal.read_text().splitlines()]
  ck('independent exact capture phase order',[x['phase'] for x in events]==['reset_before','reset_after','set_init_before','set_init_after']+sum((['wait_before','wait_after'] for _ in range(10)),[])+['t0_query_before','t0_query_after'])
  ck('observer exact original aggregate hash',events[-1]['observation_sha256']==results[1]['chunks'][0]['observation_sha256'])
  ck('noncontiguous array branch exercised',any(not m['c_contiguous'] for e in events for m in e['observation_arrays'].values()))
  for ei,event in enumerate(events):
   for key,m in event['observation_arrays'].items():
    raw=(obs.output/m['blob']['path']).read_bytes();ck('exact raw array '+str(ei)+' '+key,hashlib.sha256(raw).hexdigest()==m['sha256'] and len(raw)==m['bytes'] and np.frombuffer(raw,dtype=m['dtype']).reshape(m['shape']).tobytes()==raw)
  artifacts['episode_comparison']=write('episode_comparison.json',{'baseline_trace':traces[0],'observer_trace':traces[1],'baseline_result_excluding_timers':results[0],'observer_result_excluding_timers':results[1],'global_rng_after_equal':rngs[0]==rngs[1],'synthetic_only':True})
  # Execute the original formal loop on CPU fakes for the exact 58 identities.
  # This neither loads a model nor runs a simulator; success is synthetic and excluded.
  trace=[];ledger=runtime.TrialLedger(OUT/'synthetic_prefix58_ledger.jsonl',run_signature='c'*64)
  policies={name:Policy(trace) for name in methods}
  def reseed():random.seed(17);np.random.seed(17);trace.append(['reseed'])
  def factory(st):trace.append(['factory',st['task_id'],st['source_state_index']]);return Env(trace,success_at=11),'synthetic prefix only'
  pobj=observer.PassiveObserver(OUT/'passive_prefix58',prefix,allow_cpu_fixture=True)
  with adapter.observer_scope(runtime,trials,pobj,emit=emit):ran=trials.evaluate_formal_trials(panel,policies,ledger,factory,reseed=reseed,stop_after=58)
  finish=pobj.finish();rows=[x for x in ledger.events if x.get('event')=='result']
  ck('independent original 58 iteration order',ran==58 and [{k:x[k] for k in keys} for x in rows]==[{k:x[k] for k in keys} for x in prefix])
  ck('one fresh env/reseed/close per original identity',sum(t[0]=='factory' for t in trace)==sum(t[0]=='reseed' for t in trace)==sum(t[0]=='close' for t in trace)==58)
  ck('independent original dummy steps',sum(r['wait_steps'] for r in rows)==580 and sum(r['policy_calls'] for r in rows)==58 and sum(r['control_steps'] for r in rows)==58)
  ck('no history actions forced',sum(r['control_steps'] for r in rows)!=sum(r['control_steps'] for r in prefix))
  ck('engineering only finish',finish['scientific_trials_added']==0 and not finish['GPU_acceptance_inferred'] and finish['Goal_scientific_HOLD_unchanged'])
  artifacts['prefix_loop']=write('prefix_loop.json',{'finish':finish,'trace':trace,'synthetic_outcomes_only':True,'historical_action_replay':False,'num_completed':ran})
  # Abort and restore under a policy exception, without advancing to B.
  class BadPolicy(Policy):
   def __call__(self,obs,instruction):self.trace.append(['query_raises']);raise RuntimeError('independent synthetic policy failure')
  ftrace=[];failed_ledger=runtime.TrialLedger(OUT/'synthetic_failure_ledger.jsonl',run_signature='d'*64);fobs=observer.PassiveObserver(OUT/'policy_failure_observer',prefix,allow_cpu_fixture=True)
  def failfactory(st):ftrace.append(['factory']);return Env(ftrace),'failstop fixture'
  try:
   with adapter.observer_scope(runtime,trials,fobs,emit=emit):trials.evaluate_formal_trials(panel,{methods[0]:BadPolicy(ftrace),methods[1]:Policy(ftrace)},failed_ledger,failfactory,reseed=lambda:None,stop_after=58)
  except observer.ObserverAbort as error:negatives.append({'test':'policy error stops prefix','rejected':True,'error':str(error)})
  else:raise AssertionError('policy failure did not stop')
  failrows=[x for x in failed_ledger.events if x.get('event')=='result'];ck('only first failed A retained',len(failrows)==1 and failrows[0]['status']=='policy_error' and failrows[0]['method']==methods[0]);ck('scope rollback under failure',runtime.run_episode is active and trials.run_episode is active and trials.evaluate_formal_trials is original_eval)
 ck('original callable bindings restored after both scopes',runtime.run_episode is original_run and trials.run_episode is original_run and trials.evaluate_formal_trials is original_eval and adapter.NAME not in runtime.__dict__ and adapter.NAME not in trials.__dict__)
 # Independent mutation sentinels inside the already-guarded sink.
 for kind in ['numpy_rng','python_rng','env_rng','sim_array','object_bytes','object_id']:
  env=Env([]);observation=env.obs()
  def sink(ev,kind=kind):
   if kind=='numpy_rng':np.random.random()
   elif kind=='python_rng':random.random()
   elif kind=='env_rng':env.env.np_random.random()
   elif kind=='sim_array':env.env.sim.data.qpos[0]+=1
   elif kind=='object_bytes':observation['agentview_image'][0,0,0]+=1
   elif kind=='object_id':observation['agentview_image']=observation['agentview_image'].copy()
  o=observer.PassiveObserver(OUT/('negative_'+kind),prefix,allow_cpu_fixture=True,sink=sink)
  try:o.capture('negative',env,observation)
  except observer.ObserverAbort as error:negatives.append({'test':kind,'rejected':True,'error':str(error)})
  else:raise AssertionError('mutation not rejected '+kind)
  ck('fail-stop '+kind,o.dead)
  try:o.capture('retry',env,observation)
  except observer.ObserverAbort as error:negatives.append({'test':kind+' retry','rejected':True,'error':str(error)})
  else:raise AssertionError('failed observer retried')
 # Narrow final-write fault injection. The final write mutates only the fake sim.
 # This is evidence of guard coverage, not evidence that normal OS writes mutate MuJoCo.
 env=Env([]);observation=env.obs();o=observer.PassiveObserver(OUT/'counterexample_final_write',prefix,allow_cpu_fixture=True)
 original_open=Path.open;injected=[]
 class Wrapped:
  def __init__(self,f):self.f=f
  def __enter__(self):self.f.__enter__();return self
  def __exit__(self,*args):return self.f.__exit__(*args)
  def write(self,value):
   result=self.f.write(value);env.env.sim.data.qpos[0]+=1;injected.append(True);return result
 def open_for_test(path,*args,**kwargs):
  f=original_open(path,*args,**kwargs)
  return Wrapped(f) if path==o.journal and args and args[0]=='ab' else f
 before=float(env.env.sim.data.qpos[0])
 Path.open=open_for_test
 try:o.capture('sentinel',env,observation)
 finally:Path.open=original_open
 recorded=json.loads(o.journal.read_text().splitlines()[0]);after=float(env.env.sim.data.qpos[0])
 ck('final-write simulator guard counterexample observed',before==0 and after==1 and len(injected)==1 and not o.dead and recorded['invariants']['passive_sim_and_environment_rng_unchanged'] is True)
 artifacts['final_write_counterexample']=write('final_write_counterexample.json',{'before_qpos0':before,'after_qpos0':after,'observer_dead':o.dead,'event_count':o.event_count,'journal_invariant':recorded['invariants'],'fault_injection':'Path.open wrapper for this private fake journal only, restored immediately','actual_MuJoCo_or_OS_mutation_claimed':False})
 findings.append({'id':'G58-GUARD-02','severity':'medium','category':'invariant coverage','source':'observer_v2.py:243-255','observed':'Simulator/environment RNG equality is checked before the final journal write only; a synthetic journal-write callback can change the fake simulator while the record still declares passive_sim_and_environment_rng_unchanged=true and the observer continues.','current_candidate_limit':'Ordinary filesystem writing was not shown to mutate real simulator state. The original anomaly cause is not inferred.','minimal_fix':'Recheck passive_environment after final write alongside the existing object/global-RNG checks; fail-stop on mismatch and retain the failed event. Add this negative case.'})
 # Failure while collecting initial guard values is outside try, hence not latched.
 env=Env([]);observation=env.obs();o=observer.PassiveObserver(OUT/'counterexample_initial_rng_error',prefix,allow_cpu_fixture=True)
 original_rng=observer.global_rng
 def failing_rng():raise RuntimeError('independent synthetic existing-generator get_state error')
 observer.global_rng=failing_rng
 try:
  try:o.capture('initial_guard_failure',env,observation)
  except RuntimeError as error:first_error=str(error)
  else:raise AssertionError('missing synthetic get_state error')
 finally:observer.global_rng=original_rng
 was_dead=o.dead;journal_existed=o.journal.exists();o.capture('explicit_test_retry',env,observation)
 ck('initial-guard failure latch counterexample observed',not was_dead and not journal_existed and o.event_count==1)
 artifacts['initial_guard_counterexample']=write('initial_guard_counterexample.json',{'raised_type':'RuntimeError','error':first_error,'dead_after_failure':was_dead,'failure_journal_existed':journal_existed,'same_instance_explicit_CPU_retry_accepted':True,'automatic_real_retry_performed':False})
 findings.append({'id':'G58-FAILSTOP-03','severity':'medium','category':'failure containment','source':'observer_v2.py:214-217','observed':'Errors in initial global_rng/object_guard/passive_environment occur outside the fail-stop try block. A synthetic RNG reader error was not journaled or latched; the same object accepted an explicit later CPU capture.','current_candidate_limit':'No automatic GPU retry exists in this package and none was run. A future outer runner still must stop on any observer exception; the current internal dead/no-retry guarantee is incomplete.','minimal_fix':'Include initial guard collection inside the same fail-stop boundary and retain an abort record when possible; add reader-failure/no-retry negatives for all three initial guard calls.'})
 # Check no execution path is available, without re-running author preparation.
 prep=load(A/'prepare_candidate_v1.py','ind_prefix_prepare',PINS['prepare_candidate_v1.py']);reads=[]
 def forbidden(*args,**kw):reads.append(True);raise AssertionError('prepare tried I/O before --execute rejection')
 prep.sha=forbidden;prep.load=forbidden
 try:prep.main(['--execute'])
 except RuntimeError as e:negatives.append({'test':'prepare execute rejected before read','rejected':True,'error':str(e)})
 else:raise AssertionError('CPU candidate enabled execution')
 ck('execute rejected before reading sources or creating output',not reads)
 ck('no CUDA initialization',not ('torch.cuda' in sys.modules and sys.modules['torch.cuda'].__dict__.get('_initialized')))
 ck('no native simulator imported','mujoco' not in sys.modules and 'robosuite' not in sys.modules)
 ck('no candidate directory alteration',h(A/'delivery_manifest.json')==MANIFEST_SHA and all(h(A/x['path'])==x['sha256'] for x in m['files']) and set(x['path'] for x in m['files'])=={str(p.relative_to(A)) for p in A.rglob('*') if p.is_file()}-{'delivery_manifest.json'})
 frozen_after={str(root):{p:h(root/p) for p in frozen} for root in (R,S)}
 ck('all173 unchanged after',frozen_after==frozen_before)
 artifacts['frozen_identity']=write('frozen_identity.json',{'before':frozen_before,'after':frozen_after,'all173_unchanged':True})
 artifacts['scope_events']=write('scope_events.json',emitted)
 return {'schema':'formal_main_v2','kind':'independent_goal_prefix58_CPU_audit','status':'completed_with_findings_not_GPU_ready','candidate_manifest':{'source':str((A/'delivery_manifest.json').relative_to(R)),'sha256':MANIFEST_SHA},'checked_exact_sources':PINS,'checks':checks,'negative_cases':negatives,'findings':findings,'artifacts':artifacts,'passed_check_count':sum(x['passed'] for x in checks),'negative_case_count':len(negatives),'new_GPU_jobs':0,'new_GPU_seconds':0,'scientific_trials_added':0,'real_GPU_acceptance':False,'Goal_original_200_HOLD_unchanged':True,'new_Goal_science_HOLD_unchanged':True,'known_remaining_before_GPU':['actual reviewed single-attempt original-chain outer runner missing','tighten observer proof/fail-stop coverage and independent negative tests','root slot/authorization/source-checkpoint binding and real bounded engineering acceptance'],'CPU_seconds':time.process_time()-entered_cpu,'wall_seconds':time.monotonic()-entered,'limits':['All new observations/actions/outcomes are CPU synthetic. Original development panel identities were read, no sealed state values or model weights.','Existing exact hooks preserved baseline trace/actions/RNG in CPU fixtures. This is not real MuJoCo/CUDA determinism or evidence of the original t0 anomaly cause.','Projection/current hooks and fault-injected guard coverage are distinguished. Original historical actions are not forced.']}

if __name__=='__main__':
 try:
  result=run();write('independent_review.json',result);print(json.dumps({k:result[k] for k in ['status','passed_check_count','negative_case_count','CPU_seconds','new_GPU_seconds']}));print(json.dumps({'findings':[x['id'] for x in findings],'report_sha256':h(OUT/'independent_review.json')}))
 except BaseException as e:
  OUT.mkdir(exist_ok=True,parents=True)
  payload={'status':'audit_harness_failed','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'checks':checks,'negative_cases':negatives,'findings':findings,'artifacts':artifacts,'CPU_seconds':time.process_time()-entered_cpu,'wall_seconds':time.monotonic()-entered}
  with (OUT/'harness_failure.json').open('x') as f:json.dump(payload,f,sort_keys=True,indent=2);f.write('\n')
  print(json.dumps({'status':payload['status'],'error':str(e),'failure_sha256':h(OUT/'harness_failure.json')}));raise

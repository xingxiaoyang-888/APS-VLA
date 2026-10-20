"""CPU checks targeted at the three reviewed observer gaps; no production writes."""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,hashlib,importlib.util,json,random,sys,time,traceback
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=Path(__file__).parent;O=D/'CPU_attempt01';E=R/'results/formal_main_v2/engineering/supervision_delivery_20261020T1644/Goal_prefix58_candidate'
checks=[];neg=[];start=time.process_time()
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,v):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
 return dict(path=p.relative_to(D).as_posix(),sha256=h(p),bytes=p.stat().st_size)
def ck(n,b):
 checks.append(dict(name=n,passed=bool(b)))
 if not b:raise AssertionError(n)
def load(p,name,pin):
 ck('source '+p.name,h(p)==pin);sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def reject(n,fn,kind,message=None):
 try:fn()
 except kind as error:
  ck(n,message is None or message in str(error));neg.append(dict(name=n,error_type=type(error).__name__,error=str(error),rejected=True));return
 raise AssertionError('not rejected: '+n)
def main():
 O.mkdir(exist_ok=False)
 ob=load(D/'revision01/observer_v3.py','g58_repair_ob','7a33c4ec531e0524a5e30b51e18205dc7d354868afa6190e3f39dcf14b283241');ad=load(D/'revision01/ast_observer_v2.py','g58_repair_ast','e88222ea96c290019b2ec838ff68fe25a9f94d115ae996d92735e18e4cf0800e');old=load(D/'original_sources/ast_observer.py','g58_old_ast','defb33269acd7e464095ff622723a0168b324f19f68f7ed317475a83895cb89e')
 prefixp=D/'inputs/original_prefix58.json';ck('exact original prefix pin',h(prefixp)=='1e786af6b4aafb52dba32bce1494c5e4dd4ef05c41f10cb3b9a77342c2cbcb28');prefix=json.loads(prefixp.read_bytes())['rows']
 sys.path.insert(0,str(S/'src'));from cti_vla.evaluation import libero_runtime as runtime,formal_trials as trials
 raw=Path(runtime.__file__).read_bytes();traw=Path(trials.__file__).read_bytes();original,derived,proof=ad.derive_run(raw);torig,tderived,tproof=ad.derive_trials(traw);oldorig,oldderived,oldproof=old.derive_run(raw);oldtorig,oldtd,oldtp=old.derive_trials(traw)
 ck('original and current hooks identical',ad.text(original)==ad.text(oldorig) and ad.text(derived)==ad.text(oldderived) and ad.text(torig)==ad.text(oldtorig) and ad.text(tderived)==ad.text(oldtd))
 ck('original full call ordering unchanged',proof['original_calls']==proof['projected_calls'] and tproof['original_calls']==tproof['projected_calls'])
 write('AST_proofs.json',dict(run=proof,trials=tproof,versioned_whitelist=ad.OBSERVER_LAYOUT_V2));write('hook_AST_texts.json',dict(original_run=ad.text(original),observer_run=ad.text(derived),original_trials=ad.text(torig),observer_trials=ad.text(tderived)))
 for label,expr in [('extra_step_argument','_cti_prefix_observer.capture("extra", env.step([0.0]*7))'),('extra_RNG_keyword','_cti_prefix_observer.capture("extra", wait_steps=np.random.random())')]:
  bad=copy.deepcopy(derived);bad.body.append(ast.parse(expr).body[0]);old.assert_projection(original,bad);reject(label,lambda bad=bad:ad.assert_projection(original,bad),ValueError,'versioned whitelist')
 for name in ['nested_existing_arg','duplicate_hook','missing_hook','moved_hook','trial_side_effect']:
  x=copy.deepcopy(tderived if name=='trial_side_effect' else derived);base=torig if name=='trial_side_effect' else original
  hooks=[n for n in ast.walk(x) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id==ad.NAME]
  hook=hooks[0]
  if name in ('nested_existing_arg','trial_side_effect'):hook.value.args[0]=ast.parse('np.random.random()',mode='eval').body
  elif name=='duplicate_hook':x.body.append(copy.deepcopy(hook))
  else:
   parent=next(n for n in ast.walk(x) if any(isinstance(v,list) and hook in v for _,v in ast.iter_fields(n)));items=next(v for _,v in ast.iter_fields(parent) if isinstance(v,list) and hook in v);items.remove(hook)
   if name=='moved_hook':x.body.append(hook)
  reject(name,lambda x=x,base=base:ad.assert_projection(base,x),ValueError,'versioned whitelist')
 # Reuse the exact original CPU fake environment/policy classes, not a mirrored fixture family.
 src=(E/'cpu_selfcheck_v1.py').read_text();ck('original fixture source pin',h(E/'cpu_selfcheck_v1.py')=='da56bb01191cbe96a9b4f76034775b545ca5e8c225a3d3ff299ada3e0217f00a');run=next(x for x in ast.parse(src).body if isinstance(x,ast.FunctionDef) and x.name=='run');nodes=[copy.deepcopy(x) for x in run.body if isinstance(x,(ast.ClassDef,ast.FunctionDef)) and x.name in ('FakeEnv','FakePolicy','canonical_result')];ck('three exact prior fixture definitions',len(nodes)==3);ns=dict(np=np,random=random,copy=copy,SimpleNamespace=SimpleNamespace,observer=ob,runtime=runtime);exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<pinned-original-CPU-fixtures>','exec'),ns);Env=ns['FakeEnv'];Policy=ns['FakePolicy']
 for name in ['global_rng','object_guard','passive_environment']:
  item=ob.PassiveObserver(O/('initial_'+name),prefix,allow_cpu_fixture=True);orig=getattr(ob,name)
  def broken(*args,**kwargs):raise RuntimeError('targeted initial '+name+' failure')
  setattr(ob,name,broken)
  try:reject('initial '+name,lambda:item.capture('initial_reader'),ob.ObserverAbort,'targeted initial')
  finally:setattr(ob,name,orig)
  ck('initial latched '+name,item.dead and item.event_count==0);rows=[json.loads(x) for x in item.journal.read_text().splitlines()];ck('initial abort retained '+name,len(rows)==1 and rows[0]['event']=='observer_abort' and rows[0]['automatic_retry'] is False);reject('initial retry '+name,lambda:item.capture('after_initial_failure'),ob.ObserverAbort,'no retry')
 class JournalProxy:
  def __init__(self,path,callback):self.path=path;self.callback=callback;self.called=False
  def open(self,mode):
   delegate=self.path.open(mode);parent=self
   class File:
    def __enter__(self):delegate.__enter__();return self
    def __exit__(self,*args):return delegate.__exit__(*args)
    def write(self,b):
     n=delegate.write(b)
     if not parent.called:parent.called=True;parent.callback()
     return n
   return File()
 for name in ['simulator','environment_rng']:
  env=Env([]);obs=env.observation();item=ob.PassiveObserver(O/('final_write_'+name),prefix,allow_cpu_fixture=True);journal=item.journal
  def mutate(name=name):
   if name=='simulator':env.env.sim.data.qpos[0]+=1
   else:env.env.np_random.random_sample()
  item.journal=JournalProxy(journal,mutate);reject('final write '+name,lambda:item.capture('final_write',env,obs),ob.ObserverAbort,'journal write changed passive simulator or environment RNG state');ck('final write latched '+name,item.dead and item.event_count==0);rows=[json.loads(x) for x in journal.read_text().splitlines()];ck('event then abort retained '+name,len(rows)==2 and rows[-1]['event']=='observer_abort');reject('final write retry '+name,lambda:item.capture('retry',env,obs),ob.ObserverAbort,'no retry')
 # Abort-record I/O failure cannot mask the required fail-stop exception.
 item=ob.PassiveObserver(O/'abort_record_failure',prefix,allow_cpu_fixture=True)
 class BrokenJournal:
  def open(self,*args):raise OSError('targeted abort recorder failure')
 item.journal=BrokenJournal();orig=ob.global_rng
 def broken_rng():raise RuntimeError('targeted initial RNG failure with recorder failure')
 ob.global_rng=broken_rng
 try:reject('abort recorder remains BaseException fail-stop',lambda:item.capture('initial'),ob.ObserverAbort,'initial RNG failure')
 finally:ob.global_rng=orig
 ck('abort last record retained in memory',item.dead and item.last_abort['abort_record_error_type']=='OSError');write('abort_record_failure.json',item.last_abort);reject('abort recorder retry',lambda:item.capture('retry'),ob.ObserverAbort,'no retry')
 # Exact real frozen loop and accepted action context, one normal CPU episode.
 accepted=load(P/'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py','g58_accepted_context','b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185');events=[]
 def emit(event,**fields):events.append(dict(event=event,**fields))
 before_bindings=(runtime.run_episode,trials.run_episode,trials.evaluate_formal_trials)
 with accepted.install_action_execution_compat(project_root=P,source_root=S,runtime_module=runtime,formal_trials_module=trials,expected_adapter_sha256='b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185',emit=emit):
  active=runtime.run_episode;random.seed(117);np.random.seed(117);trace1=[];baseline=runtime.run_episode(Env(trace1),Policy(trace1),'same instruction',[0.,1.,2.],wait_steps=10,max_steps=300);rng1=ob.global_rng()
  random.seed(117);np.random.seed(117);trace2=[];item=ob.PassiveObserver(O/'exact_trace_episode',prefix,allow_cpu_fixture=True);item.current={k:prefix[0][k] for k in ob.IDENTITY_KEYS};item.begun=1
  with ad.observer_scope(runtime,trials,item,emit=emit):result=runtime.run_episode(Env(trace2),Policy(trace2),'same instruction',[0.,1.,2.],wait_steps=10,max_steps=300)
  rng2=ob.global_rng();ck('exact original trace actions and RNG',trace1==trace2 and rng1==rng2 and ns['canonical_result'](baseline)==ns['canonical_result'](result));ck('same original calls no clipping',(result['policy_calls'],result['wait_steps'],result['control_steps'])==(3,10,17) and result['executed_actions'][0][0]>1);ck('accepted context restored',runtime.run_episode is active and trials.run_episode is active)
  rows=[json.loads(x) for x in item.journal.read_text().splitlines()];ck('26 original capture markers',len(rows)==26 and rows[-2]['phase']=='t0_query_before' and rows[-1]['phase']=='t0_query_after');ck('all final captures accepted',not item.dead and item.event_count==26 and all(all(v for v in row['invariants'].values()) for row in rows));ck('same t0 hash as original',rows[-1]['observation_sha256']==result['chunks'][0]['observation_sha256']);write('episode_trace_comparison.json',dict(baseline=ns['canonical_result'](baseline),observed=ns['canonical_result'](result),baseline_trace=trace1,observed_trace=trace2,RNG_equal=rng1==rng2,synthetic_CPU_only=True))
 ck('all original bindings restored',before_bindings==(runtime.run_episode,trials.run_episode,trials.evaluate_formal_trials));write('context_events.json',events)
 panelp=P/'results/formal_main_v2/libero_goal/downstream/development/5185766bb353c8e6/attempt01/panel.json';ck('original development panel exact',h(panelp)=='ce8e3d31ab8f7616c87dd4d4031af41825713907ac184c6ea5b01d9040985aa9');panel=json.loads(panelp.read_bytes());actual=[{k:v for k,v in trials._identity(panel,state,mid).items() if k in ob.IDENTITY_KEYS} for state in panel['states'] for mid in ['A256_seed17','B256_seed17']][:58];ck('same fixed58 identity and order',actual==[{k:row[k] for k in ob.IDENTITY_KEYS} for row in prefix]);ck('29 unique existing development states',len({x['state_trial_id'] for x in actual})==29);ck('original anomalies at57and58',all(x['task_id']==2 and x['source_state_index']==42 for x in actual[-2:]));write('fixed58_identity_check.json',dict(identities=actual,scientific_trials_added=0))
 inv=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_bytes());ck('173 frozen R and S unchanged',len(inv['files'])==173 and all(h(base/n)==pin for base in (R,S) for n,pin in inv['files'].items()));ck('no CUDA initialized',not sys.modules.get('torch.cuda').__dict__.get('_initialized'))
 report=dict(status='passed_bounded_repair_CPU_only',checks=checks,passed=len(checks),negative_cases=neg,negative_count=len(neg),source_pins=dict(observer_v3=h(D/'revision01/observer_v3.py'),ast_observer_v2=h(D/'revision01/ast_observer_v2.py')),original_hook_AST_unchanged=True,trace_actions_RNG_equal=True,original_fixed58_identities_exact=True,full58_GPU_or_new_CPU_rollouts_executed=False,existing_original_full58_CPU_evidence_retained=True,three_reviewed_gaps_closed_in_CPU=True,GPU_calls=0,production_state_written=False,Goal_original200_HOLD=True,new_Goal_science_HOLD=True,CPU_seconds=time.process_time()-start,limits='One paired baseline/instrumented CPU episode plus exact58 identity reconstruction. Existing original58 CPU evidence remains pinned. Native MuJoCo/CUDA and any single-attempt GPU outer runner remain unaudited and unexecuted.')
 print(json.dumps(dict(report=write('CPU_review.json',report),passed=len(checks),negative_count=len(neg),CPU_seconds=report['CPU_seconds'])))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  write('failure.json',dict(status='CPU_author_failure',error=str(e),error_type=type(e).__name__,traceback=traceback.format_exc(),checks=checks,negative_cases=neg,CPU_seconds=time.process_time()-start,GPU_calls=0));raise

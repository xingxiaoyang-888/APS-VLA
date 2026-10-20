"""Independent CPU/metadata audit. No GPU, Slurm, canonical state or source writes."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,random,signal,sys,time,types,traceback
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=Path(__file__).resolve().parent;C=R/'.local/goal_t0_probe_candidate_20261020T1418'
sys.dont_write_bytecode=True
STARTED=time.monotonic();checks=[];notes=[];reads=[];writes=[];denials=[]
def check(ok,label):
 if not ok:raise AssertionError(label)
 checks.append(label)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def put(p,value):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
def load(p,name):
 spec=importlib.util.spec_from_file_location(name,p);mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
def ref(p):return dict(path=str(p),sha256=sha(p),bytes=Path(p).stat().st_size)
def audit(event,args):
 if event=='open':
  path,mode,flags=args
  if isinstance(path,int):return
  p=Path(os.fsdecode(path)).absolute()
  writing=(isinstance(mode,str) and any(v in mode for v in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if writing:
   if not (p==D or D in p.parents):denials.append(dict(event=event,path=str(p)));raise RuntimeError('audit forbids outside private write: '+str(p))
   writes.append(str(p))
  else:
   if p.suffix.lower() in ('.pt','.pth','.safetensors') or ('sealed' in p.name.lower() and p.suffix not in ('.py','.pyc')):
    denials.append(dict(event=event,path=str(p)));raise RuntimeError('audit forbids tensor or sealed value read: '+str(p))
   if str(p).startswith((str(R),str(P))):reads.append(str(p))
 elif event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.symlink','os.link'):
  paths=args[:2] if event in ('os.rename','os.symlink','os.link') else args[:1]
  for path in paths:
   p=Path(os.fsdecode(path)).absolute()
   if not (p==D or D in p.parents):denials.append(dict(event=event,path=str(p)));raise RuntimeError('private mutations only')
 elif event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect'):
  denials.append(dict(event=event));raise RuntimeError('audit forbids subprocess/network/GPU/Slurm')
sys.addaudithook(audit)
def reject(fn,label,types_allowed=(ValueError,KeyError)):
 try:fn()
 except types_allowed:checks.append(label);return
 raise AssertionError('not rejected: '+label)
def extract_function(file,name,cls=None):
 tree=ast.parse(Path(file).read_text())
 if cls:tree=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls)
 return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
try:
 check(sha(C/'delivery_manifest.json')=='763262a0a04e5e2feb89271fef7acafd3f150c66d4f5918e9e3e707499cdfc31','author sealed delivery SHA')
 check(sha(C/'handoff.json')=='774051f9132e194296d9d84978e69f9622a229ef912f990ce96bf7def7f3d984','author exact handoff SHA')
 delivery=read(C/'delivery_manifest.json');listed=set()
 for row in delivery['files']:
  p=C/row['relative'];check(p.resolve()==p and p.is_file() and str(p)==row['path'] and C in p.parents,'candidate canonical '+row['relative'])
  check(sha(p)==row['sha256'] and p.stat().st_size==row['bytes'],'candidate exact '+row['relative']);listed.add(row['relative'])
 check(listed=={p.relative_to(C).as_posix() for p in C.rglob('*') if p.is_file() and p.name!='delivery_manifest.json'},'complete candidate manifest with retained drafts/fixtures')
 check(len(listed)==624,'624 candidate evidence files')
 config=read(C/'config.json');m=load(C/'probe.py','goal_probe_independent_exact_candidate')
 check(m.validate_config(config),'fixed exact configuration validated')
 for key,val in [('task_id',1),('source_state_index',41),('split','final'),('method_ids',['dense']),('resets',13),('wait_steps',11),('policy_actions_executed',1),('maximum_gpu_jobs',2),('maximum_wall_seconds',3600),('application_deadline_seconds',1801),('environment_seed',17),('runtime_seed',0),('scientific_acceptance_enabled',True),('final_evaluation_enabled',True),('output_root',str(D/'unsafe_override'))]:
  v=copy.deepcopy(config);v[key]=val;reject(lambda v=v:m.validate_config(v),'reject altered '+key)
 for name,expected in config['bundle_sources'].items():check(sha(C/name)==expected,'bundle source '+name)
 inv=read(config['pinned_inputs']['original_invocation']['path']);manifest=read(config['pinned_inputs']['original_manifest']['path'])
 for key,row in config['pinned_inputs'].items():check(sha(row['path'])==row['sha256'],'exact original input '+key)
 check(inv['suite']=='libero_goal' and inv['stage']=='development' and inv['method_ids']==config['method_ids'],'original invocation development two methods')
 check(manifest['methods']==config['methods'],'same original selected checkpoint metadata; no replacement')
 inventory=read(R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json')
 check(len(inventory['files'])==173,'frozen inventory 173')
 for path,h in inventory['files'].items():
  check(sha(R/path)==sha(S/path)==h,'canonical/frozen source unchanged '+path)
 panel=read(config['pinned_inputs']['development_panel']['path'])
 check(panel['split']=='development','only development values loaded')
 selected=[v for v in panel['states'] if v['task_id']==2 and v['source_state_index']==42]
 check(len(selected)==1 and selected[0]['initial_state_sha256']==m.INITIAL_SHA and selected[0]['task_name']==m.TASK,'exact existing development task2/index42')
 # Load only pure initial-state digest helper, no final loader.
 sys.path.insert(0,str(S/'src'));from cti_vla.data.initial_states import initial_state_sha256
 check(initial_state_sha256(selected[0]['initial_state'])==m.INITIAL_SHA,'selected real development values digest')
 proof=m.validate_prefix(S/'scripts/eval_formal_selector_libero.py',C/'original_loading_prefix.py',config['prefix_proof'])
 check(proof['original_prefix_ast_unchanged'] and proof['original_statements']==72,'original all 72 loading/gating statements exact AST')
 original=extract_function(S/'scripts/eval_formal_selector_libero.py','execute')
 reseed=next(n for n in original.body if isinstance(n,ast.FunctionDef) and n.name=='reseed')
 candtree=ast.parse((C/'probe.py').read_text());creseed=next(n for n in ast.walk(candtree) if isinstance(n,ast.FunctionDef) and n.name=='reseed')
 check(ast.dump(reseed,include_attributes=False)==ast.dump(creseed,include_attributes=False),'all original reseed calls exactly same AST: Python NumPy Torch seed17')
 origevaluate=extract_function(S/'src/cti_vla/evaluation/formal_trials.py','evaluate_formal_trials')
 calls=[n.func.id if isinstance(n.func,ast.Name) else n.func.attr if isinstance(n.func,ast.Attribute) else '' for n in ast.walk(origevaluate) if isinstance(n,ast.Call)]
 check(all(x in calls for x in ['reseed','environment_factory','run_episode']),'original trial reseed before factory verified in source')
 policy=extract_function(S/'src/cti_vla/evaluation/formal_runtime.py','reset','FormalRolloutPolicy')
 check(len(policy.body)==1 and isinstance(policy.body[0],ast.Expr) and isinstance(policy.body[0].value,ast.Constant),'original selector reset is no-cache docstring only')
 # Independent baseline hash function from its actual frozen AST.
 ohash=extract_function(S/'src/cti_vla/evaluation/libero_runtime.py','_observation_hash');ohash.returns=None
 for arg in ohash.args.args:arg.annotation=None
 ns={'np':np,'hashlib':hashlib};exec(compile(ast.Module(body=[ohash],type_ignores=[]),'<exact-original-hash>','exec'),ns)
 def obs():return dict(agentview_image=np.arange(48,dtype=np.uint8).reshape(4,4,3),robot0_eye_in_hand_image=np.full((4,4,3),7,dtype=np.uint8),robot0_eef_pos=np.array([.1,.2,.3]),robot0_eef_quat=np.array([0.,0.,0.,1.]),robot0_gripper_qpos=np.array([.02,-.02]))
 o=obs();check(m.aggregate(m.arrays(o))==ns['_observation_hash'](o),'candidate hash equals actual original hash for five fields')
 snap=m.arrays(o);o['robot0_eef_pos'][0]+=1;check(snap['robot0_eef_pos'][0]==.1,'deep snapshot survives alias mutation')
 rng1=m.capture_rng();rng2=m.capture_rng();check(rng1==rng2,'RNG state capture itself does not advance Python NumPy state')
 class Sim:
  def __init__(self):self.data=types.SimpleNamespace(qpos=np.zeros(3),qvel=np.zeros(3));self.gets=0
  def get_state(self):self.gets+=1;return np.r_[self.data.qpos,self.data.qvel]
 class Env:
  def __init__(self):self.sim=Sim();self.ob=obs();self.steps=[];self.resets=0;self.inits=0;self.closed=False
  def reset(self):self.resets+=1;return self.ob
  def set_init_state(self,st):self.inits+=1;return self.ob
  def step(self,action):
   check(action==list(m.DUMMY),'only exact original dummy action');self.steps.append(action);self.sim.data.qpos+=.001;self.ob['robot0_eef_pos'][2]+=.001;return self.ob,0.,False,{}
  def close(self):self.closed=True
 class Policy:
  def __init__(self,kind):self.kind=kind;self.calls=0;self.resets=0
  def reset(self):self.resets+=1
  def __call__(self,ob,language):
   self.calls+=1
   if self.kind=='inplace':ob['robot0_eef_quat'][0]+=.25
   if self.kind=='replace':ob['agentview_image']=255-ob['agentview_image']
   if self.kind=='failure':raise RuntimeError('independent intentional failure')
   if self.kind=='timeout':time.sleep(.15)
   return {'unused_policy_actions':np.full((8,7),.91)}
 synthetic=[]
 def case(label,mutation=None,failure=None,remaining=60.):
  out=D/label;out.mkdir();rec=m.Recorder(out);envs=[];pols={a:Policy((mutation if a==m.METHODS[1] else 'constant') if failure is None else failure) for a in m.METHODS};seeds=[]
  def factory(st):
   seeds.append((random.random(),float(np.random.random())));env=Env();envs.append(env);return env,'fabricated CPU only',{'synthetic':True}
  def rseed():random.seed(17);np.random.seed(17)
  result=error=None
  try:result=m.run_fixed_queries(state={'initial_state':[0.,1.]},policies=pols,factory=factory,reseed=rseed,recorder=rec,check_chunk=lambda mid,ch:dict(synthetic=True),absolute_deadline=time.monotonic()+remaining)
  except (RuntimeError,TimeoutError) as exc:error={'type':type(exc).__name__,'message':str(exc)}
  stored={'label':label,'result':result,'error':error,'resets':sum(e.resets for e in envs),'set_init':sum(e.inits for e in envs),'wait_actions':sum(len(e.steps) for e in envs),'closed':sum(e.closed for e in envs),'policy_calls':sum(p.calls for p in pols.values()),'archives':rec.arrays_written,'synthetic':True};put(out/'summary.json',stored);synthetic.append(stored)
  return result,error,envs,pols,rec,seeds
 result,error,envs,pols,rec,seeds=case('independent_constant')
 check(error is None and len(envs)==12 and all(e.resets==e.inits==1 and e.closed for e in envs),'12 independent wrapper resets/init/close')
 check([x['method_id'] for x in result['query_records']]==list(m.ORDER),'fixed ABBA x3 order unconditioned on observations')
 check(all(p.calls==p.resets==6 for p in pols.values()),'six queries and resets per actual method')
 check(len(set(seeds))==1,'same per-query Python and NumPy reseed results')
 check(sum(len(e.steps) for e in envs)==120,'120 dummy actions zero predicted actions')
 check(rec.arrays_written==288 and all(e.sim.gets==24 for e in envs),'24 observation and read-only simulator snapshots per query')
 check(result['all_current_probe_pairs_equal'] and result['scientific_gate']=='HOLD' and result['scientific_trials_accepted']==0 and result['retry_authorized'] is False,'even constant reproduction retains science HOLD')
 for event in rec.events:
  if event['event']=='observation':
   with np.load(event['raw_archive']['path'],allow_pickle=False) as z:vals={f:np.array(z[f]) for f in m.FIELDS};simvals={f:np.array(z['sim_'+f]) for f in ('qpos','qvel','flattened')}
   check(m.aggregate(vals)==event['aggregate_sha256'] and m.array_meta(vals)==event['arrays'] and m.array_meta(simvals)==event['simulation'],'raw archive reconstructs exact observation and sim event')
 for label,kind in [('independent_inplace','inplace'),('independent_replace','replace')]:
  res,err,env,pol,rr,seed=case(label,mutation=kind)
  check(err is None and len(res['query_records'])==12 and sum(not x['input_unchanged'] for x in res['query_records'])==6,'detect B-only '+kind+' mutation at all six queries')
  check(all(x['prequery_equal'] and not x['postquery_equal'] for x in res['pair_diagnostics']),'mutation diagnostics separate pre/postquery '+kind)
  check(rr.arrays_written==288 and res['scientific_gate']=='HOLD','mutation retains fixed counts and HOLD '+kind)
 res,err,env,pol,rr,seed=case('independent_failure',failure='failure')
 check(res is None and err['type']=='RuntimeError' and len(env)==1 and env[0].closed and rr.arrays_written==23,'query exception stops after first query and retains partial arrays')
 res,err,env,pol,rr,seed=case('independent_deadline',failure='timeout',remaining=.08)
 check(res is None and err['type']=='TimeoutError' and len(env)==1 and env[0].closed,'Python query deadline stops bounded fake query with cleanup')
 # Exact original reset AST: finite fake underlying resets expose exception swallowing without an infinite wait.
 reset=extract_function(P/'external/LIBERO/libero/libero/envs/env_wrapper.py','reset','ControlEnv')
 class RandomizationError(Exception):pass
 ns={'RandomizationError':RandomizationError};exec(compile(ast.Module(body=[reset],type_ignores=[]),'<exact-original-reset>','exec'),ns)
 def reset_swallow(exc):
  class Under:
   def __init__(self):self.calls=0
   def reset(self):
    self.calls+=1
    if self.calls==1:raise exc
    return {'synthetic_success_after_swallowed_exception':True}
  v=types.SimpleNamespace(env=Under());ret=ns['reset'](v);return dict(returned=ret,underlying_reset_calls=v.env.calls,exception=type(exc).__name__)
 reset_findings=[reset_swallow(ValueError('sentinel')),reset_swallow(TimeoutError('SIGALRM handler sentinel'))]
 check(all(v['underlying_reset_calls']==2 for v in reset_findings),'original reset swallows non-randomization and timer exceptions: limitation reproduced')
 put(D/'original_reset_exception_limitation.json',dict(status='confirmed_limitation',synthetic_only=True,reset_source_sha256=sha(P/'external/LIBERO/libero/libero/envs/env_wrapper.py'),findings=reset_findings,implication='12 means external reset calls; internal retries and 28min SIGALRM exit are not guaranteed. Slurm 30min --no-requeue is hard allocation boundary.'))
 observe=extract_function(C/'probe.py','observe','Recorder');sim=extract_function(C/'probe.py','sim_snapshot')
 readcalls=[n.func.attr for n in ast.walk(sim) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
 check('get_state' in readcalls and not any(x in readcalls for x in ('step','forward','render','set_state','reset','_get_observations','_update_observables')),'sim instrumentation invokes get_state/copies only, no explicit stepping/forward/render')
 check(not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('step','forward','render','reset','_get_observations','_update_observables') for n in ast.walk(observe)),'observation instrumentation consumes returned arrays without forcing another render')
 # Exact selected state and wrapper gates, guarded metadata-only actual P verification.
 started=time.monotonic();prepared,verified,vinv=m.prepare_only(C/'config.json')
 check(prepared['status']=='cpu_prepared_not_GPU_run' and prepared['original_wrapper_metadata_verified'] and prepared['weights_loaded'] is False,'actual P wrapper prepare passes without tensor reads')
 check(vinv==inv and read(verified['args'].execution_manifest)['methods']==config['methods'],'actual prepared original invocation and checkpoint metadata exact')
 put(D/'actual_metadata_prepare.json',dict(status='passed',prepared=prepared,elapsed_seconds=time.monotonic()-started,actual_GPU_evidence=False,tensor_reads=0,configuration=ref(C/'config.json'),entrypoint=ref(C/'probe.py')))
 reject(lambda:m.validate_authorization({},config,C/'config.json',C/'probe.py'),'unsigned root authorization fails')
 # Review gate checks with deliberately labeled private CPU synthetic receipts; never usable root authorization.
 authdir=D/'synthetic_authorization_only';authdir.mkdir()
 for role in ('root','independent'):put(authdir/(role+'.json'),dict(status='passed',config_sha256=sha(C/'config.json'),entrypoint_sha256=sha(C/'probe.py'),synthetic=True,not_production_evidence=True))
 auth=dict(schema='formal_main_v2',kind='root_bounded_engineering_probe_authorization',status='approved',reviewed_by='root',config_sha256=sha(C/'config.json'),entrypoint_sha256=sha(C/'probe.py'),root_review=ref(authdir/'root.json'),independent_review=ref(authdir/'independent.json'),maximum_gpu_jobs=1,maximum_wall_seconds=1800,counts_against_8_GPU_slots=True,scientific_release=False,original_goal_failure_retained=True)
 check(m.validate_authorization(auth,config,C/'config.json',C/'probe.py'),'synthetic exact-ref review gate exercise only')
 for key,val in [('config_sha256','0'*64),('entrypoint_sha256','0'*64),('maximum_gpu_jobs',2),('maximum_wall_seconds',1801),('scientific_release',True),('counts_against_8_GPU_slots',False),('original_goal_failure_retained',False)]:
  bad=copy.deepcopy(auth);bad[key]=val;reject(lambda bad=bad:m.validate_authorization(bad,config,C/'config.json',C/'probe.py'),'authorization rejects '+key)
 bad=copy.deepcopy(auth);bad['independent_review']=bad['root_review'];reject(lambda:m.validate_authorization(bad,config,C/'config.json',C/'probe.py'),'same root/independent review rejected')
 slurm=(C/'candidate.slurm').read_text()
 check(all(x in slurm for x in ('#SBATCH --gres=gpu:l40:1','#SBATCH --time=00:30:00','#SBATCH --no-requeue')),'Slurm exact 1GPU 30min no-requeue hard boundary')
 check('sbatch' not in slurm and 'scancel' not in slurm,'wrapper only srun; no further submissions/cancellations')
 check('torch' not in sys.modules,'audit completed without Torch import or GPU')
 check(not denials,'metadata/CPU audit had no attempted forbidden IO/process actions')
 # No source or candidate changes during audit.
 check(sha(C/'delivery_manifest.json')=='763262a0a04e5e2feb89271fef7acafd3f150c66d4f5918e9e3e707499cdfc31','sealed candidate manifest unchanged after tests')
 for name,h in inventory['files'].items():check(sha(R/name)==sha(S/name)==h,'post audit frozen173 unchanged '+name)
 limitations=[
  'Original ControlEnv.reset swallows arbitrary internal errors including SIGALRM; 28min is best-effort early exit only, and 12 resets means 12 external wrapper calls with unobserved internal retry counts. Root must explicitly register this; only actual Slurm time=30min no-requeue enforces allocation bound.',
  'This freshly loaded single-state ABBA probe follows identical reseed/reset/set_init/wait/query APIs, but it does not replay the prior 200-trial process history, GPU allocator/render-context history or full policy execution. No reproduction result exonerates or replaces original failed trials.',
  'get_state and raw-array copies have no explicit step/forward/render/RNG calls; synthetic tests confirm nonmutation. Real MuJoCo rendering and real PolicyChunk behavior are not CPU verified, remain engineering GPU evidence.',
  'Runtime authorization validates exact distinct review bytes and resource claims but does not itself reconcile Slurm submission token/job IDs. Root must register one exact token/job with pending/lease and <=8 slots before submission; fixed output exclusive mkdir prevents completed attempt reuse.',
  'Instrumentation writes, hashes and RNG collection contaminate timings. Query durations are not scientific O2A latency.',
  'Metadata prepare validates original identities without loading checkpoint tensors. Original loader rechecks selected checkpoint bytes and model identity at actual runtime; no weights have been loaded by this audit.'
 ]
 report=dict(schema='formal_main_v2',kind='independent_bounded_engineering_probe_review',status='passed',decision='conditionally_runnable_bounded_engineering_only',reviewed_by='independent_agent_devplans_audit_20261020_1418',config_sha256=sha(C/'config.json'),entrypoint_sha256=sha(C/'probe.py'),candidate_delivery=ref(C/'delivery_manifest.json'),checks=checks,check_count=len(checks),metadata_prepare=ref(D/'actual_metadata_prepare.json'),reset_limitation=ref(D/'original_reset_exception_limitation.json'),limitations=limitations,root_required_conditions=['Actual root review binding same exact bytes','Root authorization includes all listed limitations and one submission token/job identity','Fresh <=8 GPU slot accounting and no duplicate/pending submission','One 1GPU Slurm30min --no-requeue job only; no blind retry','Original200 retained and all Goal science remains HOLD regardless outcome'],production_ready=False,real_GPU_acceptance=False,GPU_jobs_submitted=0,Slurm_operations=0,scientific_release=False,sealed_values_read=False,checkpoint_tensor_reads=0,state_mutations=0,canonical_mutations=0,elapsed_seconds=time.monotonic()-STARTED)
 put(D/'independent_review.json',report)
 put(D/'io_audit.json',dict(status='passed',writes=sorted(set(writes)),read_paths=sorted(set(reads)),denials=denials,subprocess_count=0,GPU_count=0,sealed_read_count=0))
 print(json.dumps(dict(status='passed',report=ref(D/'independent_review.json'),checks=len(checks),limitations=limitations),ensure_ascii=False))
except BaseException as exc:
 failure=dict(status='failed',error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc(),checks=checks,denials=denials,elapsed_seconds=time.monotonic()-STARTED)
 put(D/'audit_v1_failure.json',failure);print(json.dumps(failure,ensure_ascii=False));raise

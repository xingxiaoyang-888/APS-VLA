"""Object legacy599 source/history and recorded-chunk CPU replay candidate.
No simulated task execution, model load, Slurm, production writes or admission.
The deterministic control-flow replay technique is adapted from prior Long tooling;
all input evidence and conclusions below are independently Object-specific.
"""
import ast,copy,hashlib,importlib,json,math,os,random,struct,sys,time,types,zipfile,tarfile,subprocess
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=R/'.local/object_legacy_integration_20261020T2156'
RUN='results/formal_main_v2/libero_object/downstream/development/8c843c1d4ee8383c/attempt01'
ROOT='results/formal_main_v2/downstream_reviews/3021844.json';MAN='results/formal_main_v2/execution/libero_object_development_first_pair_v1.json';INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';REG='configs/experiments/formal_main_v2_action_execution_compat_v1.json'
TARGET='results/formal_main_v2/execution/object_collect_action_v1_20261020T1825/execution_contract.json';NEWROOT='results/formal_main_v2/downstream_reviews/3053518.json'
ADAPTER='results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py'
V4='results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v4/3039197/events.jsonl'
DIAG='results/formal_main_v2/engineering/supervision_delivery_20261020T2054/Object_raw_root/diagnostic.json'
IND='results/formal_main_v2/engineering/supervision_delivery_20261020T2054/Object_raw_independent/independent_diagnostic.json'
METHODS=['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17'];JOBS=['3021394','3021603','3021844']
SEM='9a5f5935100bb04bf8fb91f6405b94efc93de236b3a75896d0f08cdb2aa1ee02'
BAD='libero_object:pick_up_the_chocolate_pudding_and_place_it_in_the_basket:state-0049:env-0:dense'
PINS={ROOT:'004a810edd7f097bbeec755315beed11bbfa86640a78ffd75ef0ff78a769ee37',MAN:'34062573869c7b947fbd3c37b09da476bec673e8e16fc4ea49c6ce8c5932db5a',INV:'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926',REG:'0917bff60e632a5be3c2db50b16daa0b904e4754a3ba31334802060f75d3eefe',TARGET:'dde9c5437348cf202c02af9933b1bcab42ee9c10b6b05932b7ed11a565710eaa',NEWROOT:'a6fee864f172a895ffe7be3ff7a44f4ecd340eb6b9368afbf7f08d819fc2df65',ADAPTER:'b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185',V4:'54f92fbd0354bae27b95f17c5193c186cb387781f223e7af1655ea825a84459c',DIAG:'9ff4f7adee16f01f390c31a0bb417acf7a85edd1668eb8806831a222fd352ac6',IND:'90e9c034208aee087fe57eeb71dfa76b3e3a598ccbe52fa8e380ddfa15db92e2',RUN+'/trials.jsonl':'d93ad5a4eb4ae3edb7a9b20e640a72fe4971ca0e4eeb62eea71acc4d71a257d1',RUN+'/config.json':'ccbb680ade2c6cab783568ea34f2fd3d3ae9abb69a62e7088f53d7150dad27a5','results/setup/after_libero_freeze.txt':'8bac807b631bb9c9691df977eae1b26f202b6a2d8d4a440153a74bb96b7a9b06','configs/assets/libero_wheels_transfer.json':'bfd7901791c5858e405188cfc1e917fdd3db73a277a2468dd94b8d620ec0cb23','configs/requirements-libero.txt':'d255285a470c034692b493904ca8335847e58ffec6388775ddef7ccc8419987c'}
seen={};checks=[];BEGAN=time.perf_counter();CPU=time.process_time()
def need(v,msg):
 if not v:raise ValueError(msg)
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def encode(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
def sig(v):return digest(encode(v))
def pairs(xs):
 d={}
 for k,v in xs:need(k not in d,'duplicate JSON key');d[k]=v
 return d
def decode(b):
 def bad(x):raise ValueError('nonfinite JSON '+x)
 return json.loads(b,object_pairs_hook=pairs,parse_constant=bad)
def watch(rel,h=None):
 p=Path(rel);p=p if p.is_absolute() else R/p;need(p.resolve()==p and '..' not in p.parts,'canonical path');actual=sha(p);need(h is None or h==actual,'SHA mismatch '+str(p));key=p.relative_to(R).as_posix() if R in p.parents else str(p)
 need(key not in seen or seen[key]['sha256']==actual,'changed evidence');seen[key]={'sha256':actual,'bytes':p.stat().st_size};return {'path':key,'sha256':actual}
def read(rel,h=None):
 watch(rel,h);p=Path(rel);return (p if p.is_absolute() else R/p).read_bytes()
def meta(rel,h=None):return decode(read(rel,h))
def write(name,obj,jl=False):
 b=b''.join(encode(x)+b'\n' for x in obj) if jl else json.dumps(obj,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2).encode()+b'\n'
 with (D/name).open('xb') as f:f.write(b)
 return {'path':(D/name).relative_to(R).as_posix(),'sha256':digest(b),'bytes':len(b)}
def guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','socket.bind'):raise RuntimeError('no process or network inside CPU proof')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  need(not any('sealed' in q.lower() or q.lower() in ('weights','checkpoints') for q in p.parts) and not set(p.suffixes)&{'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init'} and not (p.name=='panel.json' and 'final' in p.parts) and p.name!='init_states_test.json','forbidden values')
  mode,flags=args[1:3];writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if writing:need(p.parent==D,'write outside private directory')
def f64(matrix):
 need(type(matrix) is list,'matrix list');a=[]
 for row in matrix:
  need(type(row) is list and len(row)==7,'seven columns')
  for x in row:need(type(x) in (int,float) and math.isfinite(x),'finite action');a.append(float(x))
 return struct.pack('<'+'d'*len(a),*a)
def rng():
 n=np.random.get_state();return sig({'python':random.getstate(),'numpy':[n[0],n[1].tolist(),n[2],n[3],n[4]]})
def refline(n,o,b):return {'line':n,'byte_offset':o,'bytes':len(b),'sha256':digest(b)}
def load(path,name):
 m=types.ModuleType(name);m.__file__=str(path);m.__package__='';sys.modules[name]=m;exec(compile(path.read_bytes(),str(path),'exec',dont_inherit=True),m.__dict__);return m

def replay(row,fn,runtime):
 # The same old serialized PolicyChunks feed each runtime. No policy inference,
 # image reconstruction, simulator, hidden-state replay or RNG restore occurs.
 obs={'agentview_image':np.zeros((1,1,3),dtype=np.uint8),'robot0_eye_in_hand_image':np.zeros((1,1,3),dtype=np.uint8),'robot0_eef_pos':np.zeros(3),'robot0_eef_quat':np.array([0.,0.,0.,1.]),'robot0_gripper_qpos':np.zeros(2)}
 class FakeEnv:
  def __init__(self):self.actions=[]
  def reset(self):return obs
  def set_init_state(self,x):return obs
  def step(self,action):
   self.actions.append(action)
   return obs,0.,bool(row['success'] and len(self.actions)==10+row['control_steps']),{}
 class RecordedPolicy:
  def __init__(self):self.i=0
  def reset(self):self.i=0
  def __call__(self,ob,text):
   c=row['chunks'][self.i];self.i+=1
   return runtime.PolicyChunk(np.asarray(c['normalized_actions'],dtype=np.float32),np.asarray(c['environment_actions'],dtype=np.float64),c['metadata'])
 env=FakeEnv();before=rng();out=fn(env,RecordedPolicy(),'recorded trace CPU check',np.zeros(1),wait_steps=10,max_steps=280,policy_watchdog_seconds=60.)
 need(rng()==before,'CPU replay consumed Python/NumPy RNG')
 for k in ['status','success','termination','control_steps','wait_steps','policy_calls']:need(out[k]==row[k],'replay differs: '+k)
 need(len(out['chunks'])==len(row['chunks']),'replay chunks')
 for a,b in zip(out['chunks'],row['chunks']):
  need(f64(a['normalized_actions'])==f64(b['normalized_actions']) and f64(a['environment_actions'])==f64(b['environment_actions']) and a['metadata']==b['metadata'],'replay emitted chunk changed')
 need(f64(out['executed_actions'])==f64(row['executed_actions']),'replay executed bytes changed')
 need(f64(env.actions[:10])==f64([list(runtime.DUMMY_ACTION)]*10),'wait action changed')
 need(f64(env.actions[10:])==f64(row['executed_actions']),'env boundary differs')
 return {'executed_f64le_sha256':digest(f64(env.actions[10:])), 'all_wait_and_control_actions_f64le_sha256':digest(f64(env.actions)), 'python_numpy_RNG_unchanged':True,'new_GPU_or_simulator_execution':False}

def validate_candidate(m,rows,raw,failed):
 need(m['kind']=='Object_legacy599_source_trace_candidate' and m['status']=='pending_root_and_independent_adoption','candidate type')
 need(m['suite']=='libero_object' and m['split']=='development','Object dev only')
 need(m['legacy_root']=={'path':ROOT,'sha256':PINS[ROOT]},'old root')
 need(m['raw_ledger']=={'path':RUN+'/trials.jsonl','sha256':PINS[RUN+'/trials.jsonl']},'immutable ledger')
 need(m['target']['contract']=={'path':TARGET,'sha256':PINS[TARGET]} and m['target']['action_semantics_sha256']==SEM,'target identity')
 need(m['new_GPU_seconds']==0 and m['accepted_scientific_trials_added']==0 and m['production_reuse_authorized'] is False and m['final_release'] is False,'no admission')
 need(m['historical_GPU_seconds']==6713 and m['historical_jobs_once']==JOBS,'cost all attempts')
 need(m['environment']=={'action_chunk':8,'environment_seed':0,'runtime_seed':17,'wait_steps':10,'max_steps':280},'environment settings')
 need(m['legacy_execution_version']=='formal-downstream-root-v1' and not m['old_invocation_ran_current_wrapper'],'no relabel')
 need(not m['old_controller_instance_hash_recorded'] and not m['old_RNG_dump_recorded'] and not m['old_RNG_dump_required'],'historical facts')
 need(len(rows)==599 and len(raw)==600 and set(x['trial_id'] for x in rows)==set(raw)-{BAD},'exact raw subset no outcome selection')
 need(failed['trial_id']==BAD and failed['result']['sha256']=='d7f134683c6e01c8667731c6ca6807290d91d7816d28197f48232de9bc271eb0' and failed['status']=='policy_error' and failed['success'] is False,'failure immutable')
 need(failed['rejected_eighth_chunk_recorded'] is False and failed['new_semantics_outcome_unknown'] is True,'no invented rejected action')
 need(m['failed_trial_ref']=={'path':str((D/'failed_trial_retained.json').relative_to(R)),'sha256':digest(json.dumps(failed,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2).encode()+b'\n'),'bytes':len(json.dumps(failed,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2).encode()+b'\n')},'failed ref binding')
 for x in rows:
  r=raw[x['trial_id']];need(r['status']=='completed' and x['status']=='completed' and x['success'] is r['success'],'all original outcomes unchanged')
  need(x['method_identity']==m['method_identities'][r['method']] and x['initial_state_sha256']==r['initial_state_sha256'] and x['task_id']==r['task_id'] and x['source_state_index']==r['source_state_index'],'trial identity')
  need(x['source_job_id'] in JOBS and x['target_action_semantics_sha256']==SEM,'job and semantics')
  need(x['old_runtime_replay']==x['current_runtime_replay'] and x['old_runtime_replay']['executed_f64le_sha256']==digest(f64(r['executed_actions'])),'exact action replay')
  need(x['all_chunks_finite_old_threshold'] and x['clip_changed_all7']==x['clip_changed_arm6']==0 and not x['reuse_authorized'],'action/approval')
 return {'validated_candidates':599,'retained_exception':1,'new_admission':0}

def main():
 need(Path(__file__).parent==D,'private directory')
 # Read-only Git object anchoring is explicit and narrow; no Git index or refs written.
 anchor='5c15d256796661cfd91375ac4721356d1e1888dc';gitrows=[]
 for rel in ['results/setup/after_libero_freeze.txt','configs/assets/libero_wheels_transfer.json','configs/requirements-libero.txt']:
  argv=['git','-C',str(R),'show',anchor+':'+rel]
  z=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'});need(digest(z.stdout)==PINS[rel],'historical Git exact bytes');gitrows.append({'commit':anchor,'path':rel,'sha256':digest(z.stdout)})
 z=subprocess.run(['git','-C',str(R),'show','-s','--format=%cI',anchor],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'});need(z.stdout.decode().strip().startswith('2026-10-14'),'historical time');anchor_time=z.stdout.decode().strip()
 sys.dont_write_bytecode=True;sys.addaudithook(guard)
 for p,h in PINS.items():watch(p,h)
 inv=meta(INV);need(len(inv['files'])==173,'173 count')
 for rel,h in inv['files'].items():
  for base in (R,S,R/'snapshots/formal_main_v2_run_564be0995e'):watch(base/rel,h)
 root=meta(ROOT);man=meta(MAN);config=meta(RUN+'/config.json');newroot=meta(NEWROOT);target=meta(TARGET);diag=meta(DIAG);meta(IND)
 recheck=meta(D/'legacy_root_recheck.json');need(recheck['status']=='passed_original_whole_chain' and recheck['completed_trials']==600,'original whole-chain consumer')
 for p,h in recheck['evidence_sha256'].items():watch(p,h)
 need(root['raw_invocation_job_ids']==JOBS and root['completed_trials']==600 and root['run_root']==str(P/RUN),'old root600')
 need(config['manifest']==man and [x['identity']['method_id'] for x in man['methods']]==METHODS,'same original manifest')
 identities={x['identity']['method_id']:x['identity'] for x in man['methods']}
 need(root['source_provenance']['shared_projection']==newroot['source_provenance']['shared_projection'],'Object own old/current source projection')
 need(newroot['action_semantics_sha256']==SEM and newroot['status']=='passed','actual current target accepted')
 for p,h in {**target['files'],**target['GPU_acceptance'],**target['runtime_contract']['dependencies']}.items():watch(p,h)
 rc=target['runtime_contract'];need(sig({'execution_version':'formal-downstream-action-v1','files':target['files'],'runtime_contract_without_stage':{k:v for k,v in rc.items() if k!='stage'},'GPU_acceptance':target['GPU_acceptance'],'source_inventory':target['source_inventory']})==SEM,'exact semantic function')
 need(rc['suite']=='libero_object' and rc['source_sha256']==root['source_sha256'] and rc['source_root']==str(S),'target exact source')
 for item in man['methods']:
  ident=item['identity'];need(ident['model_revision']=='4c89574e1c538b6c102f43f0526d60a9d3650148' and ident['frozen_model_sha256']=='33285a7643de7073e41bd2062cbbc80b4df8fddff915c0a86a13d0bbae48edce' and not ident['future_head_deployed'],'same Object model')
  if 'checkpoint' in item:
   need(config['watched_files'][item['checkpoint']]==ident['checkpoint_sha256'],'checkpoint identity')
   watch(item['receipt'],config['watched_files'][str(P/item['receipt'])])
 panel=meta(RUN+'/panel.json','6b7e6dd9fb5b6351ee47c7bb30eab911e7c144d700cd88f7e5162641738b2d6a');need(panel['split']=='development' and panel['suite']=='libero_object' and len(panel['states'])==100,'fixed panel')
 watch(man['development_panel'],man['development_panel_sha256']);stateby={x['trial_id']:x for x in panel['states']};need(len(stateby)==100,'unique fixed initial states')
 checks.append('Object own old/current model metadata, selected checkpoints, full frozen source and fixed100 panel')
 history=[]
 for job in JOBS:
  ps=list((R/RUN/'adapter_invocations').glob(job+'_*.json'));need(len(ps)==1,'single actual adapter')
  a=meta(ps[0],root['files'][ps[0].relative_to(R).as_posix()]);jp=ps[0].with_suffix('.jsonl');events=[decode(b) for b in read(jp,a['events_sha256']).splitlines()]
  off=[e for e in events if e['event']=='official_source_verified'];need(len(off)==2 and {e['verification']['revision'] for e in off}=={config['source_verification'][k]['revision'] for k in ['libero','openvla_oft']},'official revisions')
  for e in off:
   k='libero' if e['path'].endswith('/LIBERO') else 'openvla_oft';need(e['verification']==config['source_verification'][k],'full archives from each actual old job')
  need(a['verified_frozen_file_count']==173 and a['frozen_source_unchanged'] and a['old_ledger_prefix_unchanged'],'actual frozen/rerun prefix')
  stderr=read('results/slurm/cti-formal-downstream_'+job+'.err').decode();need('/share/home/u15016/XXY_CVPR/CTI-VLA/venv/lib/python3.11/site-packages/robosuite' in stderr and 'No private macro file found' in stderr,'old same environment stderr')
  history.append({'job_id':job,'adapter':watch(ps[0]),'journal':watch(jp),'official_source_events':off,'old_runtime_controller_capture':False,'old_RNG_capture':False,'frozen_source_unchanged':True,'old_prefix_unchanged':True})
 # Recover historical installation evidence from original artifacts, not Long conclusions.
 freeze=read(P/'results/setup/after_libero_freeze.txt',PINS['results/setup/after_libero_freeze.txt']).decode();install=read(P/'results/setup/install_libero_local_attempt4.log').decode()
 need('Successfully installed libero-0.1.0' in install and 'runtime_imports_passed' in install and 'robosuite-1.4.1' in install and 'mujoco-2.3.7' in install and '2026-10-14' in install,'pre-Object successful runtime install')
 wheel=P/'external/wheels-libero/robosuite-1.4.1-py3-none-any.whl';watch(wheel,'62587cd5888d9d3d813f3ffcc7017f6f77efa618952527a0b9bb139ffd0a3741')
 members=['robosuite/controllers/__init__.py','robosuite/controllers/base_controller.py','robosuite/controllers/config/osc_pose.json','robosuite/controllers/osc.py','robosuite/robots/single_arm.py'];memberproof={}
 with zipfile.ZipFile(wheel) as z:
  for name in members:
   old=z.read(name);p=R.parent/'venv/lib/python3.11/site-packages'/name;watch(p,digest(old));memberproof[name]={'historical_wheel_member_sha256':digest(old),'current_installed_file':watch(p)}
  oscconfig=decode(z.read('robosuite/controllers/config/osc_pose.json'));need(oscconfig['type']=='OSC_POSE' and oscconfig['input_max']==1 and oscconfig['input_min']==-1 and oscconfig['control_delta'] is True,'registered controller defaults')
 tar=P/'external/libero-8f1084e.tar';watch(tar,config['source_verification']['libero']['archive_sha256'])
 with tarfile.open(tar) as t:
  names=[n for n in t.getmembers() if n.name.endswith('/libero/libero/envs/env_wrapper.py') or n.name=='libero/libero/envs/env_wrapper.py'];need(len(names)==1,'exact env wrapper archive member');liberob=t.extractfile(names[0]).read();watch(P/'external/LIBERO/libero/libero/envs/env_wrapper.py',digest(liberob))
 need(b'OSC_POSE' in liberob and b'load_controller_config' in liberob,'LIBERO controller factory')
 evalsrc=read('scripts/eval_formal_selector_libero.py',inv['files']['scripts/eval_formal_selector_libero.py']).decode();nodes=ast.parse(evalsrc)
 named={n.name:ast.get_source_segment(evalsrc,n) for n in ast.walk(nodes) if isinstance(n,ast.FunctionDef) and n.name in ['factory','reseed']};need('OffScreenRenderEnv' in named['factory'] and 'env.seed(0)' in named['factory'] and 'camera_heights=256' in named['factory'] and 'random.seed(17)' in named['reseed'] and 'np.random.seed(17)' in named['reseed'] and 'torch.manual_seed(17)' in named['reseed'],'same frozen factory/reseed')
 sys.path.insert(0,str(S/'src'));runtime=importlib.import_module('cti_vla.evaluation.libero_runtime');need(Path(runtime.__file__)==S/'src/cti_vla/evaluation/libero_runtime.py','frozen runtime import')
 adapter=load(R/ADAPTER,'_object599_exact_adapter');before=rng();old,new,proof=adapter.derive_function(runtime,read(S/'src/cti_vla/evaluation/libero_runtime.py'));need(rng()==before and proof['removed_if_count']==1 and proof['other_AST_nodes_unchanged'],'one branch no new RNG')
 # Actual Object cells only, accepted engineering is not new599 inference or denominator.
 v4={}
 for e in [decode(b) for b in read(V4).splitlines()]:
  if e.get('suite')=='libero_object' and e.get('method_id') in ['dense','uniform128','A128_seed17','B128_seed17']:v4.setdefault(e['method_id'],{}).setdefault(e['event'],[]).append(e)
 need(len(v4)==4,'four actual Object cells')
 controllers=[]
 for method,es in v4.items():
  start=es['cell_start'][0];need(start['identity']==identities[method],'Object current acceptance identity');c=es['actual_controller_verified'][0]['controller'];need(c['actual_use_delta'] is True and c['configured_control_delta'] is True and c['set_goal_dispatches_to_bound_scale_action'] is True,'actual Object controller')
  need(c['limits']['input_max']==[1.]*6 and c['limits']['input_min']==[-1.]*6 and c['limits']['output_max']==[.05,.05,.05,.5,.5,.5],'actual same controller config')
  controllers.append({'method':method,'controller':{k:v for k,v in c.items() if k not in ['constructor_source','methods']},'state_identity':start['state_identity'],'runtime_rng_sha256':start['runtime_rng_sha256']})
 checks.append('Three Object actual journals + pre-run Git-pinned installation/wheel + same LIBERO factory and four Object current GPU cells')
 raw={};candidates=[];perchunk=[];start=None;job=None;offset=0;allcounts=Counter();normalcounts=Counter();failed=None;comparisons=[]
 for lineno,b in enumerate((R/RUN/'trials.jsonl').open('rb'),1):
  need(b.endswith(b'\n'),'complete raw line');lr=refline(lineno,offset,b);offset+=len(b);r=decode(b)
  if r['event']=='invocation':need(start is None,'unfinished invocation');job=r['slurm_job_id'];need(job in JOBS,'known job');continue
  if r['event']=='start':need(start is None,'overlap');start=(r,lr);continue
  need(r['event']=='result' and start is not None,'paired start/result');st,sr=start;start=None
  need(r['trial_id'] not in raw,'no duplicate terminal');raw[r['trial_id']]=r
  for k in ['action_chunk','configured_wait_steps','environment_seed','initial_state_sha256','method','run_signature','runtime_seed','source_state_index','split','state_trial_id','suite','task_id','task_name','trial_id']:need(r[k]==st[k],'start/result '+k)
  need(r['method']==METHODS[(len(raw)-1)%6] and r['suite']=='libero_object' and r['split']=='development' and r['environment_seed']==0 and r['runtime_seed']==17 and r['action_chunk']==8 and r['wait_steps']==10,'original scope/order')
  state=stateby[r['state_trial_id']];need(r['initial_state_sha256']==state['initial_state_sha256'] and r['task_id']==state['task_id'] and r['source_state_index']==state['source_state_index'],'exact fixed state')
  ident=identities[r['method']];queue=[];clip7=clip6=0;mds=[]
  for i,c in enumerate(r['chunks']):
   need(c['control_step']==i*8 and len(c['normalized_actions'])==len(c['environment_actions'])==8,'full8 chunk');eb=f64(c['environment_actions']);nb=f64(c['normalized_actions']);a=np.asarray(c['environment_actions'],dtype=np.float64);need(bool((np.abs(a)<=1.00001).all()),'full emitted chunk old range')
   clip7+=int(np.count_nonzero(a.view(np.uint64)!=np.clip(a,-1.,1.).view(np.uint64)));arm=a[:,:6].copy();clip6+=int(np.count_nonzero(arm.view(np.uint64)!=np.clip(arm,-1.,1.).view(np.uint64)))
   md=c['metadata'];need(md['suite']=='libero_object' and md['method']==ident['method'] and md['visual_tokens']==ident['visual_tokens'] and md['future_head_calls']==0 and md['vision_calls']==md['packing_calls']==md['policy_calls']==1 and md['language_cache']=='disabled','same policy metadata')
   need(md['inputs_version']==runtime.INPUTS_VERSION and md['action_version']==runtime.ACTION_VERSION and md['packing_version']=='oft-original-positions-v1' and md['per_camera_budgets']==[ident['visual_tokens']//2]*2,'preprocess/packing/action semantics')
   idx=md['retained_indices'];need(len(idx)==len(set(idx))==ident['visual_tokens'] and sum(x<256 for x in idx)==ident['visual_tokens']//2 and all(type(x) is int and 0<=x<512 for x in idx),'token indices')
   if ident['method'] in ['A','B']:need(md['selector_checkpoint_sha256']==ident['checkpoint_sha256'],'selector checkpoint')
   queue+=c['environment_actions'];mds.append(sig(md));perchunk.append({'trial_id':r['trial_id'],'chunk_index':i,'environment_f64le_sha256':digest(eb),'normalized_f64le_sha256':digest(nb),'metadata_sha256':sig(md),'observation_sha256':c['observation_sha256']})
  need(f64(queue[:r['control_steps']])==f64(r['executed_actions']) and len(r['executed_actions'])==r['control_steps'] and clip7==clip6==0,'exact action queue/clip inactive')
  allcounts.update(trials=1,chunks=len(r['chunks']),actions=r['control_steps'])
  if r['trial_id']==BAD:
   need(r['status']=='policy_error' and r['success'] is False and r['policy_calls']==8 and len(r['chunks'])==7 and r['control_steps']==56 and r['error']=='environment action outside normalized controller [-1, 1] range','exact exceptional trial')
   failed=copy.deepcopy(diag['exception']);need(failed['result']==lr and failed['start']==sr and failed['executed_float64le_sha256']==digest(f64(r['executed_actions'])),'independently bound original failure');continue
  need(r['status']=='completed' and len(r['chunks'])==r['policy_calls']==math.ceil(r['control_steps']/8),'599 complete rows')
  a=replay(r,old,runtime);bnew=replay(r,new,runtime);need(a==bnew,'Object old/current recorded action trace')
  out={k:r[k] for k in ['trial_id','state_trial_id','task_id','task_name','source_state_index','initial_state_sha256','method','status','success','termination','control_steps','policy_calls']}
  out.update(method_identity=ident,source_job_id=job,start=sr,result=lr,old_execution_version='formal-downstream-root-v1',target_action_semantics_sha256=SEM,all_chunks_finite_old_threshold=True,clip_changed_all7=clip7,clip_changed_arm6=clip6,full_chunks=len(r['chunks']),all_emitted_f64le_sha256=digest(f64(queue)),metadata_sequence_sha256=sig(mds),old_runtime_replay=a,current_runtime_replay=bnew,reuse_authorized=False)
  candidates.append(out);normalcounts.update(trials=1,chunks=len(r['chunks']),actions=r['control_steps'])
  if r['method'] in v4:
   es=v4[r['method']];st4=es['cell_start'][0]
   if st4['state_identity']['trial_id']==r['state_trial_id']:
    ch=es['policy_chunk'];need(len(ch)==1,'one current engineering chunk');comparisons.append({'method':r['method'],'state_sha256':r['initial_state_sha256'],'same_method_identity':st4['identity']==ident,'current_engineering_first_chunk_equal':f64(ch[0]['environment_actions'])==f64(r['chunks'][0]['environment_actions']),'actual_current_control_steps':8,'old_control_steps':r['control_steps'],'whole_trajectory_equivalence_claimed':False})
 need(start is None and set(raw)=={state+':'+m for state in stateby for m in METHODS} and len(candidates)==599 and failed is not None,'all600 fixed cells preserved')
 need(allcounts==Counter(trials=600,chunks=11727,actions=92001) and normalcounts==Counter(trials=599,chunks=11720,actions=91945),'exact Object counts')
 need(len(comparisons)==4 and runtime.run_episode is old,'four bounded current comparisons and original function unpatched')
 need(root['cost']['all_attempt_gpu_seconds']==6713 and [x['job_id'] for x in root['cost']['allocations']]==JOBS and sum(x['elapsed_seconds']*x['gpus'] for x in root['cost']['allocations'])==6713,'6713 actual GPU seconds exactly once')
 failedref=write('failed_trial_retained.json',failed);rowsref=write('per_trial_599.jsonl',candidates,True);chunksref=write('per_chunk_all600.jsonl',perchunk,True)
 historyref=write('Object_controller_history.json',{'kind':'Object_original_history_reconstruction','status':'historical_source_chain_available_adoption_pending','Git_anchor':{'commit':anchor,'commit_time':anchor_time,'files':gitrows},'original_actual_jobs':history,'same_installed_controller_members':memberproof,'controller_config':oscconfig,'same_frozen_factory_reseed_source':named,'same_LIBERO_wrapper_sha256':digest(liberob),'current_actual_Object_controller_cells':controllers,'Object_current_first_chunk_comparisons':comparisons,'old_instance_hash_recorded':False,'old_RNG_dump_recorded':False,'old_RNG_dump_required_by_registration':False,'same_controller_environment_condition':'Source chain recovered from pre-run installation, Object own all3 source journals and unchanged factory; explicit root/independent adoption still required. No retrospective instance hashes or proof of every unlogged historical in-place edit claimed.'})
 mapping={'schema':'formal_main_v2','kind':'Object_legacy599_source_trace_candidate','status':'pending_root_and_independent_adoption','suite':'libero_object','split':'development','legacy_root':watch(ROOT),'raw_ledger':watch(RUN+'/trials.jsonl'),'legacy_execution_version':'formal-downstream-root-v1','old_invocation_ran_current_wrapper':False,'target':{'contract':watch(TARGET),'action_semantics_sha256':SEM,'actual_target_root':watch(NEWROOT)},'registration':watch(REG),'method_identities':identities,'environment':man['environment'],'trial_records':rowsref,'failed_trial_ref':failedref,'controller_history':historyref,'old_controller_instance_hash_recorded':False,'old_RNG_dump_recorded':False,'old_RNG_dump_required':False,'historical_GPU_seconds':6713,'historical_jobs_once':JOBS,'original_allocations':root['cost']['allocations'],'coverage':{'raw_trials':600,'conditional_candidates':599,'retained_policy_error':1,'unique_initial_states':100,'tasks':10,'methods':6,'no_outcome_filtering':True,'normal_counts':dict(normalcounts),'all_counts':dict(allcounts)},'new_GPU_seconds':0,'accepted_scientific_trials_added':0,'production_reuse_authorized':False,'final_release':False,'single_removed_branch_AST_proof':proof,'CPU_replay_scope':'Exact actual recorded chunks through old and current derived run_episode, deterministic fake environment/observations and original stop length. This proves action/control-flow/RNG equivalence conditional on source/controller identity, not a regenerated model or LIBERO trajectory.','source_guard':'All173 frozen files rehashed R/S/mirror; no writes outside private proof or authorized transport journal.'}
 validate_candidate(mapping,candidates,raw,failed);negative=[]
 for case in ['missing_normal','drop_failed','changed_action','changed_outcome','wrong_state','wrong_checkpoint','wrong_method','changed_environment','fake_version','fake_old_controller','fake_rejected_chunk','cost_underreport','admission','wrong_target']:
  m=copy.deepcopy(mapping);rs=copy.deepcopy(candidates);f=copy.deepcopy(failed)
  if case=='missing_normal':rs.pop()
  elif case=='drop_failed':f={}
  elif case=='changed_action':rs[0]['current_runtime_replay']['executed_f64le_sha256']='0'*64
  elif case=='changed_outcome':rs[0]['success']=not rs[0]['success']
  elif case=='wrong_state':rs[0]['initial_state_sha256']='0'*64
  elif case=='wrong_checkpoint':rs[-1]['method_identity']['checkpoint_sha256']='0'*64
  elif case=='wrong_method':rs[0]['method_identity']['method']='B'
  elif case=='changed_environment':m['environment']['max_steps']=520
  elif case=='fake_version':m['legacy_execution_version']='formal-downstream-action-v1'
  elif case=='fake_old_controller':m['old_controller_instance_hash_recorded']=True
  elif case=='fake_rejected_chunk':f['rejected_eighth_chunk_recorded']=True
  elif case=='cost_underreport':m['historical_GPU_seconds']=4926
  elif case=='admission':m['production_reuse_authorized']=True
  elif case=='wrong_target':m['target']['action_semantics_sha256']='0'*64
  try:validate_candidate(m,rs,raw,f)
  except (ValueError,KeyError):negative.append({'case':case,'rejected':True})
  else:raise ValueError('negative accepted '+case)
 for p,x in seen.items():need(sha(Path(p) if Path(p).is_absolute() else R/p)==x['sha256'],'changed evidence '+p)
 mapref=write('Object599_candidate.json',mapping);evidence=write('evidence.json',seen)
 report={'kind':'Object599_author_CPU_proof','status':'passed_CPU_candidate_pending_independent_root','map':mapref,'evidence':evidence,'history':historyref,'legacy_root_recheck':watch(D/'legacy_root_recheck.json'),'single_removed_branch_AST_proof':proof,'counts':dict(normalcounts),'retained_all_counts':dict(allcounts),'checks':checks+['599 exact old/current CPU replays and11720fullchunks; all600 raw attempts separately retained','Original600 Cartesian cells no outcome selection; failure not a compatibility candidate','14 typed-map negative mutations rejected'],'negative_checks':negative,'new_GPU_seconds':0,'accepted_scientific_trials_added':0,'pending_gates':['Independent recomputation of Object599 raw/source/controller proof.','Root explicit same-controller/environment historical source-chain assessment.','Separate exact typed consumer integration before any development freeze or O2A admission.','One failed dense cell remainsHOLD; ordinary ledger resume skips it and is not a replacement.'],'CPU_seconds':time.process_time()-CPU,'wall_seconds':time.perf_counter()-BEGAN,'current_engineering_first_chunk_comparisons':comparisons,'production_state_Git_frozen173_or_P_entries_changed':False}
 reportref=write('report.json',report);print(json.dumps({'report':reportref,'candidate':mapref,'normal_counts':dict(normalcounts),'all_counts':dict(allcounts),'CPU_seconds':report['CPU_seconds'],'wall_seconds':report['wall_seconds']}),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as e:
  import traceback
  write('failure_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json',{'error':str(e),'traceback':traceback.format_exc(),'checks':checks,'new_GPU_seconds':0});raise

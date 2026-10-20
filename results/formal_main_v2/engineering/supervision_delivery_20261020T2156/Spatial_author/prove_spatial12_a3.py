"""Exact Spatial3022743 legacy12 compatibility author proof; CPU only.
Uses full existing traces and source-derived historical identity, never a new rollout.
Only writes this private directory. Original source/ledger/attempts remain immutable.
"""
from pathlib import Path
import ast,copy,hashlib,importlib,importlib.util,json,math,os,random,struct,sys,time,zipfile
from collections import Counter
from datetime import datetime,timezone
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e';SP=R.parent/'venv/lib/python3.11/site-packages'
D=R/'.local/spatial588_integration_20261020T2156'
RUN='results/formal_main_v2/libero_spatial/downstream/development/8c843c1d4ee8383c/attempt01'
ROOT='results/formal_main_v2/downstream_reviews/3022743.json'
MAN='results/formal_main_v2/execution/libero_spatial_development_first_pair_v1.json'
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
REG='configs/experiments/formal_main_v2_action_execution_compat_v1.json'
ADAPT='results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py'
TARGET='results/formal_main_v2/execution/action_spatial_resume_0943/execution_contract.json'
V4='results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v4/3039197/events.jsonl'
METHODS=['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17']
IDS=['action_chunk','configured_wait_steps','environment_seed','initial_state_sha256','method','run_signature','runtime_seed','source_state_index','split','state_trial_id','suite','task_id','task_name','trial_id']
PINS={ROOT:'9e14b86a1e556c53ef1cbd8c7bdc1733c3d5eb744f62ffee8df9395645816650',MAN:'efc2fc4435442ba6458a033876c813a33de2afd69e952fae8ef86afd8727be03',INV:'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926',REG:'0917bff60e632a5be3c2db50b16daa0b904e4754a3ba31334802060f75d3eefe',ADAPT:'b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185',TARGET:'b63689d9f3fb3dece0c2fee8c219ad94cd8e1e694962afdb2cd66a40bf551bc0',V4:'54f92fbd0354bae27b95f17c5193c186cb387781f223e7af1655ea825a84459c',RUN+'/trials.jsonl':'3a175dbc5dd7a23cd2c3c8385cb6ff3c525f09d4e607ff32a69a10869672a2f9',RUN+'/config.json':'41458e92e1b4f8d6ef7ca3230c5154c9b87c83d107ca51c334ad8850018f699d',RUN+'/panel.json':'07718b648bfb767472506c48b0ef1837a5e6af992c2460e7567c275064809c91','results/slurm/cti-formal-downstream_3022743.err':'472124b2227d7edbd0d17a1ca390676b3335b17f4f7edbba057b331ffe04f7db','results/setup/after_libero_freeze.txt':'8bac807b631bb9c9691df977eae1b26f202b6a2d8d4a440153a74bb96b7a9b06','configs/assets/libero_wheels_transfer.json':'bfd7901791c5858e405188cfc1e917fdd3db73a277a2468dd94b8d620ec0cb23','scripts/ops/formal_downstream_supervisor.py':'f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571','scripts/formal_execution_manifests.py':'614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89','scripts/ops/formal_action_deployment_v1/reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','scripts/ops/formal_action_deployment_v1/consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'}
watched={};checks=Counter()
def need(v,m,g='general'):
 if not v:raise ValueError(m)
 checks[g]+=1
def digest(b):return hashlib.sha256(b).hexdigest()
def sig(v):return digest(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def unique(items):
 d={}
 for k,v in items:
  if k in d:raise ValueError('duplicate JSON key')
  d[k]=v
 return d
def decode(b):return json.loads(b,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def watch(rel,h=None):
 p=Path(rel);p=p if p.is_absolute() else R/p
 need(p.resolve()==p and p.is_file() and not p.is_symlink(),'noncanonical evidence '+str(p),'paths')
 key=p.relative_to(R).as_posix() if R in p.parents else str(p);v=sha(p)
 need(h is None or v==h,'SHA differs '+key,'pins');need(key not in watched or watched[key]['sha256']==v,'evidence changed '+key,'pins')
 watched[key]={'sha256':v,'bytes':p.stat().st_size};return dict(path=key,**watched[key])
def read(rel,h=None):
 watch(rel,h);p=Path(rel);return decode((p if p.is_absolute() else R/p).read_bytes())
def load(name,rel):
 p=R/rel;spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m
 exec(compile(p.read_bytes(),str(p),'exec',dont_inherit=True),m.__dict__);return m
def save(name,x,jsonl=False):
 p=D/name
 with p.open('x',encoding='utf-8') as f:
  if jsonl:
   for row in x:f.write(json.dumps(row,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n')
  else:f.write(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n')
 return dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p))
def f64(m):
 need(type(m)is list,'action matrix list','actions');flat=[]
 for row in m:
  need(type(row)is list and len(row)==7,'7 action columns','actions')
  for v in row:need(type(v)in(int,float) and math.isfinite(v),'finite numeric action','actions');flat.append(float(v))
 return struct.pack('<'+'d'*len(flat),*flat)
def rng():
 n=np.random.get_state();return sig({'python':random.getstate(),'numpy':[n[0],n[1].tolist(),n[2],n[3],n[4]]})
def guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','socket.bind'):raise RuntimeError('No subprocess/network/scheduler')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0])).absolute()
  if set(p.suffixes)&{'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init'} or any(x.lower() in ('weights','checkpoints','sealed') for x in p.parts) or p.name=='init_states_test.json' or ('final' in p.parts and p.name=='panel.json'):raise RuntimeError('No weights/sealed payload')
  mode,flags=args[1:3];writing=any(c in str(mode or '') for c in 'wax+') or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC)))
  if writing and D not in p.parents:raise RuntimeError('Private writes only')
sys.dont_write_bytecode=True;sys.addaudithook(guard)
def replay(row,fn,rt):
 obs={'agentview_image':np.zeros((1,1,3),dtype=np.uint8),'robot0_eye_in_hand_image':np.zeros((1,1,3),dtype=np.uint8),'robot0_eef_pos':np.zeros(3),'robot0_eef_quat':np.array([0.,0.,0.,1.]),'robot0_gripper_qpos':np.zeros(2)}
 class Env:
  def __init__(self):self.actions=[];self.calls=[]
  def reset(self):self.calls.append('reset');return obs
  def set_init_state(self,x):self.calls.append('set_init_state');return obs
  def step(self,a):self.actions.append(a);return obs,0.,bool(row['success'] and len(self.actions)==10+row['control_steps']),{}
 class Policy:
  def __init__(self):self.i=0
  def reset(self):self.i=0
  def __call__(self,ob,lang):
   c=row['chunks'][self.i];self.i+=1;return rt.PolicyChunk(np.asarray(c['normalized_actions'],dtype=np.float32),np.asarray(c['environment_actions'],dtype=np.float64),c['metadata'])
 env=Env();before=rng();out=fn(env,Policy(),'CPU recorded Spatial trace',np.zeros(1),wait_steps=10,max_steps=220,policy_watchdog_seconds=60.)
 need(rng()==before,'replay RNG changed','replay');need(env.calls==['reset','set_init_state'],'reset order','replay')
 for k in ['status','success','termination','control_steps','wait_steps','policy_calls']:need(out[k]==row[k],'replay differs '+k,'replay')
 need(f64(env.actions[:10])==f64([list(rt.DUMMY_ACTION)]*10),'wait bytes','replay')
 need(f64(env.actions[10:])==f64(row['executed_actions'])==f64(out['executed_actions']),'all env action bytes','replay')
 need(len(out['chunks'])==len(row['chunks']),'all emitted chunks','replay')
 for x,y in zip(out['chunks'],row['chunks']):need(f64(x['environment_actions'])==f64(y['environment_actions']) and f64(x['normalized_actions'])==f64(y['normalized_actions']) and x['metadata']==y['metadata'],'chunk bytes/metadata','replay')
 return {'all_wait_and_control_f64le_sha256':digest(f64(env.actions)),'executed_f64le_sha256':digest(f64(out['executed_actions'])),'RNG_unchanged':True,'new_simulator_execution':False}
def main():
 began=time.perf_counter();need(Path(__file__).parent==D,'private exact directory')
 for rel,h in PINS.items():watch(rel,h)
 inv=read(INV);need(len(inv['files'])==173,'173 frozen files','source')
 for rel,h in inv['files'].items():
  for base in (R,S,R/'snapshots/formal_main_v2_run_564be0995e'):watch(base/rel,h)
 root=read(ROOT);need(root['status']=='passed' and not root['scientific_complete'] and root['completed_trials']==12 and root['expected_trials']==600 and root['raw_invocation_job_ids']==['3022743'],'genuine prefix identity','root')
 helper=load('_sp12_original_helper','scripts/formal_execution_manifests.py');sched=load('_sp12_original_scheduler','scripts/ops/formal_downstream_supervisor.py');ev=helper.Evidence(R)
 checked=sched.require_root_review(ev,ROOT,sched.formal_jobs({'registered_jobs':root['registered_jobs_at_review']}),expected_stage='development')
 need(checked['job_id']=='3022743' and checked['completed_trials']==12 and checked['scientific_complete'] is False and all(checked.get(k)==v for k,v in root.items()),'original partial root gate unchanged','root');ev.unchanged()
 for rel,h in ev.files.items():watch(rel,h)
 man=read(MAN);cfg=read(RUN+'/config.json');panel=read(RUN+'/panel.json');report=read(RUN+'/closed_loop_report.json',root['files'][RUN+'/closed_loop_report.json'])
 need(cfg['manifest']==report['provenance']['manifest']==man and sig(cfg)==root['run_signature']==report['provenance']['run_signature'],'config manifest signature','identity')
 need(man['split']=='development' and man['suite']=='libero_spatial' and man['environment']==dict(environment_seed=0,runtime_seed=17,wait_steps=10,action_chunk=8,max_steps=220),'scope/environment','identity')
 identities={m['identity']['method_id']:m['identity'] for m in man['methods']};need(list(identities)==METHODS,'6 methods','identity')
 need(all(x['model_revision']=='6d0231af0e48c5985f1ff86908f4674b84bc049b' and x['frozen_model_sha256']=='6a34ed9b4790fa889eb36406a1182d3d89ee539f7a65cb2f72d67e8326d557e7' and x['future_head_deployed'] is False for x in identities.values()),'same frozen Spatial base','identity')
 need(identities['A128_seed17']['checkpoint_sha256']=='68953d2b4f0325b54df698b3ed7aadb19ac1d53b2b53bb9e0b8ff7abb0c84a40' and identities['B128_seed17']['checkpoint_sha256']=='ea56dea4fd9f67c99c2b149b123a2112ae7e5971249fe86f697128000d7d1b7e','same selected A/B checkpoints','identity')
 target=read(TARGET);reviewer=load('_sp12_action_reviewer','scripts/ops/formal_action_deployment_v1/reviewer.py');semantic=reviewer.semantic_identity(target)
 for rel,h in {**target['files'],**target['GPU_acceptance'],**target['runtime_contract']['dependencies']}.items():watch(rel,h)
 need(target['runtime_contract']['suite']=='libero_spatial' and target['runtime_contract']['stage']=='development' and target['runtime_contract']['policy']['action_values']=='unchanged' and target['scientific_settings_changed'] is False and target['final_evaluation_enabled'] is False,'target semantics bounded','identity')
 sys.path.insert(0,str(S/'src'));rt=importlib.import_module('cti_vla.evaluation.libero_runtime');need(Path(rt.__file__)==S/'src/cti_vla/evaluation/libero_runtime.py','exact original runtime','source')
 adapter=load('_sp12_actual_adapter',ADAPT);before=rng();oldfn,newfn,astproof=adapter.derive_function(rt,(S/'src/cti_vla/evaluation/libero_runtime.py').read_bytes())
 need(rng()==before and astproof['removed_if_count']==1 and astproof['other_AST_nodes_unchanged'],'only no-RNG range branch removed','source')
 # Verify same historically installed distribution directly, not Long verdict.
 transfer=read('configs/assets/libero_wheels_transfer.json');cutoff=datetime(2026,10,17,tzinfo=timezone.utc).timestamp();packages=[];members=[]
 for wheel,prefix,count in [('robosuite-1.4.1-py3-none-any.whl','robosuite/',1019),('mujoco-2.3.7-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl','mujoco/',39)]:
  info=next(x for x in transfer['files'] if x['path']==wheel);w=P/'external/wheels-libero'/wheel;watch(w,info['sha256']);rows=[]
  with zipfile.ZipFile(w) as z:
   for zi in z.infolist():
    if not zi.filename.startswith(prefix) or zi.is_dir():continue
    p=SP/zi.filename;need(p.is_file() and p.resolve()==p and not p.is_symlink(),'installed source canonical','historical')
    a=p.stat();raw=p.read_bytes();b=p.stat();h=digest(raw);need(h==digest(z.read(zi)),'wheel/current exact bytes','historical')
    need((a.st_ino,a.st_size,a.st_ctime_ns,a.st_mtime_ns)==(b.st_ino,b.st_size,b.st_ctime_ns,b.st_mtime_ns),'stable installed source','historical')
    need(a.st_ctime<cutoff and a.st_mtime<cutoff,'installed source changed after old run','historical')
    rows.append(dict(path=str(p),member=zi.filename,sha256=h,bytes=a.st_size,device=a.st_dev,inode=a.st_ino,ctime_ns=a.st_ctime_ns,mtime_ns=a.st_mtime_ns))
  need(len(rows)==count,'full package coverage','historical');members.extend(rows);packages.append(dict(wheel=str(w),sha256=info['sha256'],members=count,max_ctime_utc=datetime.fromtimestamp(max(x['ctime_ns'] for x in rows)/1e9,timezone.utc).isoformat()))
 need(not (SP/'robosuite/macros_private.py').exists(),'no new private macros','historical')
 freeze=(R/'results/setup/after_libero_freeze.txt').read_text();need('robosuite-1.4.1-py3-none-any.whl#sha256=62587cd5888d9d3d813f3ffcc7017f6f77efa618952527a0b9bb139ffd0a3741' in freeze and 'mujoco-2.3.7' in freeze,'historical exact installed freeze','historical')
 install=P/'results/setup/install_libero_local_attempt4.log';watch(install,'2f89cb36baf0e7e6695090a6b858c8dc17db27f703cbf74a72736a8214bd7822');text=install.read_text();need(all(x in text for x in ['Verified transferred runtime packages: 11','Successfully installed','runtime_imports_passed']),'old successful install','historical')
 err=(R/'results/slurm/cti-formal-downstream_3022743.err').read_text();need(str(SP/'robosuite/__init__.py') in err and 'No private macro file found!' in err,'actual old Spatial import warning','historical')
 journal=next((R/RUN/'adapter_invocations').glob('3022743_*.jsonl'));watch(journal,root['files'][journal.relative_to(R).as_posix()]);events=[decode(b) for b in journal.read_bytes().splitlines()]
 official=[e for e in events if e['event']=='official_source_verified'];need(len(official)==2,'official verifier events','historical')
 lib=next(e for e in official if e['path'].endswith('/LIBERO'));need(lib['verification']['archive_sha256']=='e0a261753ce056649da67f4c71938391a8d7c55a3eae53e4c17a5d79649da55c' and lib['expected_revision']=='8f1084e3132a39270c3a13ebe37270a43ece2a01','old Spatial exact LIBERO','historical')
 need(datetime.fromisoformat(lib['utc']).timestamp()>cutoff,'package source predates old Spatial','historical')
 wrapper=P/'external/LIBERO/libero/libero/envs/env_wrapper.py';watch(wrapper,'2880cad5b3fe46ea105816f42798faf4c22e16839098b679ebcad7b51acfdbd0');need(wrapper.stat().st_ctime<cutoff,'LIBERO source predates old Spatial','historical')
 need('controller="OSC_POSE"' in wrapper.read_text() and 'suite.load_controller_config(default_controller=controller)' in wrapper.read_text(),'same controller factory','historical')
 limits=decode((SP/'robosuite/controllers/config/osc_pose.json').read_bytes());need(limits['control_delta'] is True and limits['input_max']==1 and limits['input_min']==-1,'delta/input default','historical')
 v4=[decode(b) for b in (R/V4).read_bytes().splitlines()];controllers=[e for e in v4 if e.get('event')=='actual_controller_verified' and e.get('suite')=='libero_spatial'];need(len(controllers)==4,'actual target Spatial controllers','historical')
 for e in controllers:
  c=e['controller'];need(c['controller_type']=='robosuite.controllers.osc.OperationalSpaceController' and c['actual_use_delta'] is True and c['limits']==dict(input_max=[1.]*6,input_min=[-1.]*6,output_max=limits['output_max'],output_min=limits['output_min']),'actual current Spatial matches source-derived old','historical')
  for item in c['methods'].values():watch(item['path'],item['sha256'])
 # Registered source identity carries environment factory/reseed and policy unchanged.
 factory=(R/'scripts/eval_formal_selector_libero.py').read_text();tree=ast.parse(factory);execute=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute');nested={n.name:n for n in execute.body if isinstance(n,ast.FunctionDef)}
 need(ast.unparse(nested['reseed'])=='def reseed():\n    random.seed(17)\n    np.random.seed(17)\n    torch.manual_seed(17)','exact reseed calls','rng')
 need('env.seed(0)' in ast.unparse(nested['factory']) and 'camera_heights=256, camera_widths=256' in ast.unparse(nested['factory']),'same factory seeds/render size','rng')
 trials=ast.parse((R/'src/cti_vla/evaluation/formal_trials.py').read_text());loop=next(n for n in trials.body if isinstance(n,ast.FunctionDef) and n.name=='evaluate_formal_trials');calls=[ast.unparse(n) for n in ast.walk(loop) if isinstance(n,ast.Call)]
 need('reseed()' in calls and 'environment_factory(state)' in calls,'per-trial reseed/factory frozen','rng')
 # Only actual12 are candidates; exact full600 panel and order determine remaining588.
 need(panel['split']=='development' and panel['suite']=='libero_spatial' and len(panel['states'])==100 and sig(panel)==cfg['panel_signature'],'unchanged complete development panel','identity')
 states={x['trial_id']:x for x in panel['states']};expected=[st['trial_id']+':'+m for st in panel['states'] for m in METHODS]
 pertrial=[];perchunk=[];active=None;offset=0;job=None;counts=Counter();allrows=[]
 for n,b in enumerate((R/RUN/'trials.jsonl').open('rb'),1):
  need(b.endswith(b'\n'),'ledger newline','raw');row=decode(b);line=dict(line=n,byte_offset=offset,bytes=len(b),sha256=digest(b));offset+=len(b);allrows.append(row)
  need(row['run_signature']==root['run_signature'],'run signature','raw')
  if row['event']=='invocation':need(job is None and active is None and row['slurm_job_id']=='3022743','one real execution','raw');job=row['slurm_job_id'];continue
  if row['event']=='start':need(active is None,'no overlapping attempt','raw');active=(row,line);continue
  need(row['event']=='result' and active is not None,'start before result','raw');start,sl=active;active=None
  need(all(row[k]==start[k] for k in IDS),'paired identities','raw');need(row['trial_id']==expected[len(pertrial)],'exact first12 fixed order','raw')
  need(row['status']=='completed' and row['policy_calls']==len(row['chunks'])==math.ceil(row['control_steps']/8) and row['control_steps']<=220,'completed/full chunk capture','raw')
  state=states[row['state_trial_id']];need(all(row[k]==state[k] for k in ['initial_state_sha256','source_state_index','task_id','task_name']),'exact development state','identity')
  need(row['environment_seed']==0 and row['runtime_seed']==17 and row['wait_steps']==row['configured_wait_steps']==10 and row['action_chunk']==8,'same seed/control settings','identity')
  identity=identities[row['method']];queue=[];clip6=clip7=0;mds=[]
  for i,c in enumerate(row['chunks']):
   need(c['control_step']==i*8 and len(c['environment_actions'])==len(c['normalized_actions'])==8,'full 8x7 including unused suffix','actions');eb=f64(c['environment_actions']);nb=f64(c['normalized_actions']);a=np.asarray(c['environment_actions'],dtype='<f8');md=c['metadata']
   need((np.abs(a)<=1.00001).all(),'old branch never taken','actions');clip6+=int(np.count_nonzero(a[:,:6].copy().view(np.uint64)!=np.clip(a[:,:6],-1,1).view(np.uint64)));clip7+=int(np.count_nonzero(a.view(np.uint64)!=np.clip(a,-1,1).view(np.uint64)))
   need(md['suite']=='libero_spatial' and md['method']==identity['method'] and md['visual_tokens']==identity['visual_tokens'] and md['per_camera_budgets']==[identity['visual_tokens']//2]*2,'per-chunk method/budget','identity')
   need(md['policy_calls']==md['vision_calls']==md['packing_calls']==1 and md['future_head_calls']==0 and md['scorer_calls']==int(identity['method']in('A','B')) and md['language_cache']=='disabled','same deployment inputs/calls','identity')
   if identity['method']in('A','B'):need(md['selector_checkpoint_sha256']==identity['checkpoint_sha256'] and md['training_seed']==17,'actual selected selector','identity')
   queue.extend(c['environment_actions']);mds.append(sig(md));perchunk.append(dict(trial_id=row['trial_id'],chunk=i,environment_f64le_sha256=digest(eb),normalized_f64le_sha256=digest(nb),metadata_sha256=sig(md),observation_sha256=c['observation_sha256']))
  need(clip6==clip7==0,'controller clipping exact identity','actions');need(f64(row['executed_actions'])==f64(queue[:row['control_steps']]),'actual executed queue prefix','actions')
  old=replay(row,oldfn,rt);new=replay(row,newfn,rt);need(old==new,'same old/current action trace','replay')
  rec={k:row[k] for k in IDS};rec.update(source=dict(job_id='3022743',start_line=sl,result_line=line),outcome={k:row[k] for k in ['status','success','termination','control_steps']},method_identity_sha256=sig(identity),full_emitted_chunks=len(row['chunks']),executed_actions=row['control_steps'],full_emitted_f64le_sha256=digest(f64(queue)),executed_f64le_sha256=digest(f64(row['executed_actions'])),old_runtime=old,target_runtime=new,target_action_semantics_sha256=semantic,clip6_changed_components=0,clip7_diagnostic_changed_components=0,metadata_sequence_sha256=sig(mds),legacy_origin_preserved=True,new_scientific_trial=False)
  pertrial.append(rec);counts.update(trials=1,chunks=len(row['chunks']),executed_actions=row['control_steps'])
 need(active is None and counts==dict(trials=12,chunks=122,executed_actions=917) and len(expected)==600 and offset==592887,'complete exact prefix12','raw')
 need(rt.run_episode is oldfn,'original runtime unchanged','source')
 # Explicit machine-readable minimal proof with immutable original prefix refs.
 history=dict(kind='source_derived_historical_Spatial_controller_identity',job_id='3022743',actual_historical_controller_instance_capture=False,installation_freeze=PINS['results/setup/after_libero_freeze.txt'],installation_success=watch(install),old_import_log=watch('results/slurm/cti-formal-downstream_3022743.err'),official_source_events=official,packages=packages,member_evidence=save('installed_package_members.json',members),LIBERO_env_wrapper=watch(wrapper),limits=limits,target_actual_Spatial_controller_methods=[e['method_id'] for e in controllers],source_continuity_inference='Exact historical wheel/install plus old actual venv import and archive verifier; all1058 installed bytes match wheels with stable ctime/mtime before old job. This is source-derived identity, not a retrospectively captured controller instance.',RNG=dict(historical_full_snapshot_required=False,old_full_snapshot_recorded=False,per_trial_reseed=['random.seed(17)','np.random.seed(17)','torch.manual_seed(17)'],environment_seed=0,same_frozen_factory_and_trial_loop=True,only_removed_branch_is_pure_numpy_range_predicate=True,no_new_rng_calls_or_action_changes=True,CPU_python_numpy_unchanged=True,proof=astproof))
 h=save('historical_identity.json',history);t=save('per_trial_compatibility.jsonl',pertrial,True);c=save('per_chunk_compatibility.jsonl',perchunk,True)
 proof=dict(schema='formal_main_v2',kind='bounded_Spatial12_legacy_development_compatibility_candidate',status='author_compatibility_passed_pending_independent_root_adoption',version='spatial12-exact-action-identity-v1',scope=dict(stage='development',suite='libero_spatial',methods=METHODS,total_panel_trials=600,legacy_trials=12,remaining_trials=588),original_prefix=dict(path=RUN+'/trials.jsonl',bytes=592887,sha256=PINS[RUN+'/trials.jsonl'],root_review=dict(path=ROOT,sha256=PINS[ROOT]),job_id='3022743',run_signature=root['run_signature']),original_config=dict(path=RUN+'/config.json',sha256=PINS[RUN+'/config.json']),manifest=dict(path=MAN,sha256=PINS[MAN]),panel=dict(path=RUN+'/panel.json',sha256=PINS[RUN+'/panel.json']),method_identities=identities,environment=man['environment'],target=dict(contract=dict(path=TARGET,sha256=PINS[TARGET]),action_semantics_sha256=semantic),counts=dict(counts),full122_chunks_and917_executed_actions_byte_equal=True,no_controller_clipping_changed_components=True,history=h,per_trial=t,per_chunk=c,legacy_trial_ids=expected[:12],remaining_trial_ids_sha256=sig(expected[12:]),legacy_origin_label='original formal-downstream-root-v1; compatible under exact action semantics, never relabeled as produced by current wrapper',unknown_historical_instance_capture_not_invented=True,forbidden_use=['other_trial','other_suite','profiling','final','automatic_submission','general_consumer_bypass'],new_GPU_seconds=0,new_scientific_trials=0,weights_read=False,sealed_values_read=False,production_admission=False)
 save('compatibility_proof.json',proof)
 for rel,x in watched.items():
  p=Path(rel);p=p if p.is_absolute() else R/p;need(sha(p)==x['sha256'],'evidence changed at end '+rel,'final')
 save('evidence.json',watched);summary=dict(status='passed_author_compatibility_candidate',checks=dict(checks),check_count=sum(checks.values()),counts=dict(counts),source173_verified=True,scientific_reuse_authorized=False,requires_independent_and_root_adoption=True,proof_sha256=sha(D/'compatibility_proof.json'),duration_seconds=time.perf_counter()-began)
 save('report.json',summary);print(json.dumps(summary,sort_keys=True))
if __name__=='__main__':main()

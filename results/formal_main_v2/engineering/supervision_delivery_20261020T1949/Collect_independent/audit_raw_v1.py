from __future__ import annotations
from pathlib import Path
import os,sys,json,hashlib,importlib.util,traceback,copy
from datetime import datetime,timezone
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/collect_terminal_independent_20261020T1949'
I='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
OBS='results/formal_main_v2/preflight/heartbeat_20261021T0349/initial_observation.json'
OLD='.local/Long_collect_terminal_independent_0927/audit_a2.py'
PINS={I:'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926',OBS:'190779141d8168fc0714a2f0451e0bc424e4418dadcf8a960553d7a8d8bad0cd','scripts/ops/formal_action_deployment_v1/reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','scripts/ops/formal_action_deployment_v1/consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034','src/cti_vla/evaluation/formal_profiling.py':'56f9fec509a67b5687393e4d020f26722ee16f237df27261bbf38c1437278a80'}
JOBS=[dict(suite='libero_spatial',job='3053503',seconds=363,maximum=220,indices=[3,7,5,1,7,3,13,3,1,6],prefix='spatial',config='d3efd2457bbdf1f924ed41e0f43fc1bb3ce0372e8550f28ab757bea8d26a76e1',panel='7307b64cf285c23249f35096725c97227cc3f49e280bd1d54b0799f7812db662',summary='b07550eb7a778b72510eea4b5eda6fd18c124f2f70637e6496722c4c9724b60f',ledger='15a58c0f571d10ec380d5f895b7aa1acc0eb9aac03c08c7b09141bb0f8fd0b28',inv='b1bb8e736cb886f3c0e948ca0b4586ec5ec71ac9fc9dfb7199e25cbe32dce7d9',science='44529fba06f45d5d9e7ca3563bafc88ad624e5af797c3162f22785b8335e63fb',effective='0ed890e69b47155eb83dd388e05c68a84b635e79b596b2b0e39cd4f903a2f5b7',contract='747b4b3a9f0be6814d7451d88ffb9593b2320c3da6a8c98ade8a8ac087ca1486',manifest='788611fd20e81853f8500172efb08c73148c02a2188c8eabec2dad37f3fc7777',revision='6d0231af0e48c5985f1ff86908f4674b84bc049b'),dict(suite='libero_object',job='3053518',seconds=360,maximum=280,indices=[5,8,0,1,2,11,3,7,1,2],prefix='object',config='6d58a6c406f94aeb71cafc1193e7f1e64c91b4ef155ae676039c5b01736373f6',panel='a63c8a77f22f9138ebe91982a88259fe2d5cb5e01875021a388435f42af15e74',summary='19cd7f6fd7d3282f70237d9f85d76d95855c60333e30d97b8932fcc23dbd938a',ledger='7da9c22f3df3bde18b6a467a5528fa17cae7381600a8096c6e76046be71ad1e4',inv='ed96b7d16e3c9b9281659bba84729c9b7d637c6cac940bdba8384475b7c72777',science='5b42b93d87a2b6a1eda303c0ca0f86ac9ad30a255e69b62cb104f8f00d58abf0',effective='7002d950c23e3dcb76862089f428f3305d78a87e6c84ab01389fc32bfd1c6ee5',contract='dde9c5437348cf202c02af9933b1bcab42ee9c10b6b05932b7ed11a565710eaa',manifest='45197f0dc711ebc09a685e25a8edc251c25b881eb1ad477ef8dbbe89a9aed13d',revision='4c89574e1c538b6c102f43f0526d60a9d3650148')]
checks=[]; watched={}
def check(ok,label):
 if not ok:raise AssertionError(label)
 checks.append(label)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sig(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def parse(b):
 def unique(pairs):
  d={}
  for k,v in pairs:
   if k in d:raise ValueError('duplicate JSON key')
   d[k]=v
  return d
 return json.loads(b,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite')))
def watch(p):
 p=Path(p);b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
 if str(p) in watched:check(watched[str(p)]==h,'unchanged reread:'+str(p))
 watched[str(p)]=h;return b
def read(p):return parse(watch(p))
def ref(rel):return dict(path=rel,sha256=digest(R/rel))
def save(n,d):
 with (D/n).open('x',encoding='utf-8') as f:f.write(json.dumps(d,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n')
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect','socket.bind'):raise RuntimeError('No process/network from audit')
 if event=='open':
  p,mode,flags=args
  if isinstance(p,(str,bytes)):
   q=Path(os.fsdecode(p)).absolute()
   wr=any(x in str(mode or '') for x in 'wax+') or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
   if wr and D not in q.parents:raise RuntimeError('Write outside private directory')
   if q.suffix.lower() in ('.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init') or any(x.lower() in ('sealed','test','final') for x in q.parts):raise RuntimeError('Weight/sealed data forbidden')
   if q==R/'results/experiment_supervisor/state.json':raise RuntimeError('Mutable state is not immutable evidence')
sys.addaudithook(guard)
def main():
 for rel,h in PINS.items():check(digest(R/rel)==h,'pin:'+rel)
 invsource=read(R/I);check(len(invsource['files'])==173,'173 source files')
 for rel,h in invsource['files'].items():
  check(digest(R/rel)==h,'R frozen:'+rel);check(digest(S/rel)==h,'S frozen:'+rel)
 sys.path.insert(0,str(S/'src'))
 from cti_vla.evaluation import formal_profiling as fp
 from cti_vla.evaluation.profiling import RAW_KEYS,RawObservation,observation_signature
 from cti_vla.evaluation.libero_runtime import _observation_hash
 obs=read(R/OBS);acct=[row.split('|') for row in obs['observation']['raw_sacct'].splitlines() if row]
 reg=read(R/'configs/experiments/formal_main_v2.json');allfiles=[];reports=[]
 for item in JOBS:
  suite,jid=item['suite'],item['job'];C='results/formal_main_v2/execution/'+item['prefix']+'_collect_action_v1_20261020T1825/'
  Orel='results/formal_main_v2/'+suite+'/downstream/collect/648ce4233e78353e/attempt01';O=P/Orel
  allocation=[r for r in acct if r[0]==jid];check(len(allocation)==1 and allocation[0][1:4]==['COMPLETED','0:0',str(item['seconds'])] and 'gres/gpu=1' in allocation[0][4],suite+' exact immutable Slurm cost')
  for name,k in [('config.json','config'),('panel.json','panel'),('summary.json','summary'),('collection_trials.jsonl','ledger')]:check(digest(O/name)==item[k],suite+' raw pin:'+name)
  files=[p for p in sorted(O.rglob('*')) if p.is_file()];check(len(files)==50,suite+' 50 original product files')
  for p in files:
   check(not p.is_symlink(),suite+' real file:'+p.name);b=watch(p);allfiles.append(dict(relative=p.relative_to(P).as_posix(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),source=str(p)))
  for name,k in [('scientific_plan.json','science'),('effective_plan.json','effective'),('execution_contract.json','contract'),('dense_development.json','manifest')]:
   check(digest(R/(C+name))==item[k],suite+' canonical plan:'+name);check(digest(P/(C+name))==item[k],suite+' P plan:'+name)
  science=read(R/(C+'scientific_plan.json')); effective=read(R/(C+'effective_plan.json'));contract=read(R/(C+'execution_contract.json'));manifest=read(R/(C+'dense_development.json'))
  IN='results/formal_main_v2/invocations/'+suite+'_collect_648ce4233e78353e_attempt01.json'
  check(digest(R/IN)==digest(P/IN)==item['inv'],suite+' actual invocation bytes')
  inv=read(R/IN);check(inv['stage']=='collect' and inv['method_ids']==['dense'] and inv['prior_job_ids']==[] and inv['resume'] is False,suite+' fixed dense/no retry invocation')
  check(inv['scientific_settings_changed'] is False and inv['final_values_read_locally'] is False,suite+' invocation bounds')
  for label,p in [('science',science),('effective',effective)]:
   check(sig({k:v for k,v in p.items() if k!='plan_sha256'})==p['plan_sha256'],suite+' '+label+' semantic hash');check(p['invocation_relative']==IN and p['output_relative']==Orel,suite+' '+label+' bound output')
  for path,h in contract['files'].items():check(digest(R/path)==h and digest(P/path)==h,suite+' full source closure:'+path)
  development=read(R/('configs/manifests/formal_main_v2/'+suite+'/initial_states/development.json'))
  states=[min([s for s in development['states'] if s['task_id']==t],key=lambda s:s['source_state_index']) for t in range(10)]
  check([s['source_state_index'] for s in states]==item['indices'] and fp.fixed_profile_states(development)==states,suite+' independent ten minimum source indices')
  config=read(O/'config.json');panel=read(O/'panel.json');summary=read(O/'summary.json');identity=manifest['methods'][0]['identity']
  first=read(R/('results/formal_main_v2/execution/'+suite+'_development_first_pair_v1.json'))
  check(identity==first['methods'][0]['identity']==config['dense_identity'],suite+' original official Dense reference')
  check(identity['model_revision']==item['revision'] and identity['visual_tokens']==512 and identity['future_head_deployed'] is False,suite+' exact base and budget')
  check(config['command']=='collect' and config['slurm_job_id']==jid and config['future_head_deployed'] is False and config['test_opened'] is False,suite+' actual command and bounds')
  check(manifest['environment']==dict(action_chunk=8,environment_seed=0,max_steps=item['maximum'],runtime_seed=17,wait_steps=10),suite+' environment contract')
  check(config['manifest']==manifest and config['source_files']==panel['provenance']['source_files'],suite+' actual science and provenance')
  check(panel['development_panel_sha256']==sig(development) and panel['content_signature']==sig({k:v for k,v in panel.items() if k!='content_signature'}),suite+' canonical panel digest separate from bytes')
  samples,meta=fp.load_profile_panel(O/'panel.json',development=development,registration=reg,dense_identity=identity)
  check(len(samples)==30 and meta==summary['panel'] and all(not a.flags.writeable for s in samples for a in s.observation.values()),suite+' original panel loader / immutable30')
  events=[parse(b) for b in watch(O/'collection_trials.jsonl').splitlines()]
  check(len(events)==20 and [e['event'] for e in events]==['start','result']*10,suite+' ten exact one-attempt start result pairs')
  totalsteps=calls=0;details=[]
  shapes={'agentview_image':('uint8',(256,256,3)),'robot0_eye_in_hand_image':('uint8',(256,256,3)),'robot0_eef_pos':('float64',(3,)),'robot0_eef_quat':('float64',(4,)),'robot0_gripper_qpos':('float64',(2,))}
  for task,state in enumerate(states):
   st,row=events[task*2:task*2+2];receipt=read(O/f'task{task:02d}/receipt.json');tr=receipt['trajectory'];n=tr['control_steps'];selected=[0,(n-1)//2,n-1]
   for e in (st,row):check(e['trial_id']==state['trial_id'] and e['method']=='dense' and e['run_signature']==sig(config),suite+f' fixed trial {task}')
   check(receipt['state']=={k:state[k] for k in fp.STATE_FIELDS},suite+f' full dev metadata {task}')
   check(receipt['content_signature']==sig({k:v for k,v in receipt.items() if k!='content_signature'}),suite+f' receipt canonical hash {task}')
   check(tr=={k:v for k,v in row.items() if k not in ('event','method','trial_id','run_signature')},suite+f' raw trajectory equality {task}')
   check(tr['status']=='completed' and tr['wait_steps']==10 and 3<=n<=item['maximum'],suite+f' steps/wait {task}')
   check((tr['success'] is True and tr['termination']=='environment_success') or (tr['success'] is False and n==item['maximum'] and tr['termination']=='task_horizon'),suite+f' termination no replacement {task}')
   hashes=receipt['all_control_observation_sha256'];check(len(hashes)==n and all(len(h)==64 for h in hashes),suite+f' all captured hashes {task}')
   check([x['control_step'] for x in receipt['observations']]==selected and len(set(selected))==3,suite+f' actual first mid last {task}')
   check([c['control_step'] for c in tr['chunks']]==list(range(0,n,8)) and tr['policy_calls']==len(tr['chunks'])==(n+7)//8 and len(tr['executed_actions'])==n,suite+f' chunk8 action lengths {task}')
   for c in tr['chunks']:
    step=c['control_step'];m=c['metadata'];check(c['observation_sha256']==hashes[step],suite+f' query raw hash {task}:{step}')
    check(np.array_equal(np.asarray(tr['executed_actions'][step:min(step+8,n)]),np.asarray(c['environment_actions'][:min(8,n-step)])),suite+f' actual FIFO actions {task}:{step}')
    a=np.asarray(c['environment_actions']);norm=np.asarray(c['normalized_actions']);check(a.shape==norm.shape==(8,7) and np.isfinite(a).all() and np.isfinite(norm).all(),suite+f' finite actions {task}:{step}')
    check(m['suite']==suite and m['method']=='dense' and m['future_head_calls']==0 and m['visual_tokens']==512 and m['per_camera_budgets']==[256,256] and m['policy_calls']==m['vision_calls']==m['packing_calls']==1 and m['scorer_calls']==0,suite+f' actual deploy counters {task}:{step}')
    check(m['action_version']=='libero-oft-boundsq99-gripper-sign-invert-chunk8-v1' and m['packing_version']=='oft-original-positions-v1' and m['inputs_version']=='libero-oft-eval-rotate180-jpeg-lanczos3-crop09-boundsq99-v1' and m['language_cache']=='disabled',suite+f' actual action/input contract {task}:{step}')
   for entry,step,phase in zip(receipt['observations'],selected,('first','middle','last')):
    p=O/f'task{task:02d}'/entry['arrays']['path'];check(p.name==phase+'.npz' and entry['phase']==phase and digest(p)==entry['arrays']['sha256'],suite+f' NPZ bytes {task}:{phase}')
    with np.load(p,allow_pickle=False) as z:
     check(set(z.files)==set(RAW_KEYS)==set(shapes),suite+f' raw inputs only {task}:{phase}');arrays={k:z[k].copy() for k in z.files}
    check(all(not a.dtype.hasobject and np.isfinite(a).all() for a in arrays.values()),suite+f' no pickle/NaN {task}:{phase}')
    check(all((str(arrays[k].dtype),arrays[k].shape)==shapes[k] for k in arrays),suite+f' native dimensions {task}:{phase}')
    h1=hashlib.sha256();h2=hashlib.sha256()
    for k in RAW_KEYS:
     a=np.ascontiguousarray(arrays[k]);h1.update(json.dumps([k,a.dtype.str,a.shape]).encode());h1.update(a.tobytes());h2.update(k.encode()+str(a.dtype).encode()+str(a.shape).encode()+a.tobytes())
    sample=RawObservation(entry['observation_id'],state['trial_id'],state['task_name'],receipt['instruction'],phase,arrays)
    check(h1.hexdigest()==entry['raw_sha256']==observation_signature(sample),suite+f' independent raw digest {task}:{phase}')
    check(h2.hexdigest()==entry['rollout_observation_sha256']==hashes[step]==_observation_hash(arrays),suite+f' independent timestep digest {task}:{phase}')
    check(entry['observation_id']==f"task{task:02d}:state{state['source_state_index']:04d}:step{step:04d}",suite+f' exact sample id {task}:{phase}')
   check(receipt['test_opened'] is False and receipt['new_success_trials'] is False and receipt['provenance']==panel['provenance'],suite+f' no new success or sealed data {task}')
   details.append(dict(task_id=task,source_state_index=state['source_state_index'],control_steps=n,selected_control_steps=selected,policy_calls=tr['policy_calls'],termination=tr['termination'],success_collection_diagnostic_only=tr['success']))
   totalsteps+=n;calls+=tr['policy_calls']
  check(summary['policy_calls']==calls and summary['observations']==30 and summary['status']=='completed_collection',suite+' aggregate actual collection')
  check(summary['new_success_trials'] is False and summary['test_opened'] is False and panel['new_success_trials'] is False,suite+' no success denominator or final')
  load=config['model_loading_seconds_excluded_from_calls'];wall=summary['execution_wall_seconds_including_model_loading'];check(0<load<wall<item['seconds'],suite+' collection wall and loading within allocation')
  reports.append(dict(suite=suite,job_id=jid,status='passed_raw_observation_checks',panel=dict(path=Orel+'/panel.json',sha256=digest(O/'panel.json')),observations=30,collection_trajectories=10,control_steps=totalsteps,policy_calls=calls,tasks=details,gpu_seconds=item['seconds'],gpu_hours=item['seconds']/3600,wall_including_load_seconds=wall,model_load_seconds=load,scientific_success_trials_added=0,O2A_or_component_timing_samples=0,root_reviewer_and_consumer_pending=True))
 for rel,h in invsource['files'].items():check(digest(R/rel)==h and digest(S/rel)==h,'unchanged source:'+rel)
 for path,h in watched.items():check(digest(path)==h,'stable input:'+path)
 save('P_raw_files.json',dict(kind='independent_original_P_nonweight_file_inventory',files=allfiles,weights_copied=False,files_copied=False))
 save('raw_observation_review.json',dict(schema='formal_main_v2',kind='independent_collect_raw_observation_precheck',status='passed_raw_observation_checks_not_terminal_acceptance',reviewed_by='independent',checks_passed=len(checks),checks=checks,jobs=reports,original_Long_audit_reference=ref(OLD),source_inventory=ref(I),immutable_Slurm_observation=ref(OBS),frozen_files_unchanged=173,scientific_success_trials_added=0,latency_samples_added=0,final_release=False,models_loaded=False,weight_bytes_read=False,Slurm_queries=False,production_or_state_or_Git_writes=False,limitations=['Full root reviewer and original consumer reconstruction still required before terminal acceptance.','Dense successes in collection are diagnostics only and are not additional evaluation trials.'],inputs_sha256=watched,utc=datetime.now(timezone.utc).isoformat()))
 print(json.dumps(dict(status='passed_raw_observation_checks_not_terminal_acceptance',checks=len(checks),jobs=[{k:r[k] for k in ['suite','job_id','observations','control_steps','policy_calls','gpu_seconds']} for r in reports],report_sha256=digest(D/'raw_observation_review.json'))))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  save('raw_failure_v1.json',dict(status='failed',type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),checks_passed=len(checks)));raise

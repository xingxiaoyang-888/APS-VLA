"""Bounded read-only checks for the two already completed fixed collect jobs.
Original reviewer/consumer remain unchanged and execute only from the root helper.
"""
from pathlib import Path
import hashlib, importlib.util, json, sys, zipfile
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/collect_terminal_20261020T1949'
INPUT_SHA='5f3ad7c8ed294d27a6a4cf2b37851511dde751014b57ada728459c653551b4d5'
JOB_IDS=('3053503','3053518')
SUITES={'3053503':('libero_spatial',220,363,[3,7,5,1,7,3,13,3,1,6]),'3053518':('libero_object',280,360,[5,8,0,1,2,11,3,7,1,2])}
SHAPES={'agentview_image':('uint8',(256,256,3)),'robot0_eye_in_hand_image':('uint8',(256,256,3)),'robot0_eef_pos':('float64',(3,)),'robot0_eef_quat':('float64',(4,)),'robot0_gripper_qpos':('float64',(2,))}

def need(value,label):
 if not value: raise ValueError(label)

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()

def sig(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(path):
 def unique(pairs):
  out={}
  for k,v in pairs:
   need(k not in out,'duplicate JSON key');out[k]=v
  return out
 return json.loads(Path(path).read_bytes(),object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))

def write(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x',encoding='utf-8') as f:json.dump(value,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 return {'path':str(path.relative_to(R)),'sha256':sha(path)}

def load(rel,pin,name):
 p=R/rel;need(p.resolve()==p and not p.is_symlink() and sha(p)==pin,'source pin: '+rel)
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def inputs():
 need(sha(D/'inputs.json')==INPUT_SHA,'input inventory pin')
 value=read(D/'inputs.json')
 need([str(j['job_id']) for j in value['selected_registered_jobs']]==list(JOB_IDS),'exact two job list')
 for rel,pin in value['sources'].items():need(sha(R/rel)==pin,'source identity: '+rel)
 return value

def validate_job(job,expected):
 need(job==expected,'registered job changed from author input snapshot')
 jid=str(job.get('job_id'));need(jid in SUITES,'unregistered collect job')
 suite,horizon,seconds,minimum=SUITES[jid]
 need(job.get('experiment')=='formal_main_v2' and job.get('mode')=='collect' and job.get('suite')==suite,'exact suite/stage')
 need(job.get('status')=='COMPLETED' and job.get('exit_code')=='0:0' and job.get('gpus')==1 and job.get('elapsed_seconds')==seconds,'successful final allocation identity')
 need(job.get('method_ids')==['dense'] and job.get('prior_job_ids')==[] and job.get('resume') is False,'one dense collect allocation only')
 need(job.get('source_sha256')=='dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e','173 frozen source identity')
 need(job.get('run_root')==str(P/f'results/formal_main_v2/{suite}/downstream/collect/648ce4233e78353e/attempt01'),'exact output root')
 return suite,horizon,seconds,minimum

def validate_files(value,base):
 need(base in (R,P),'only exact server roots')
 expected={f['relative']:f for f in value['output_files']}
 need(len(expected)==106 and len(value['output_files'])==106,'exact two53-file inventories')
 found=set()
 for j in value['selected_registered_jobs']:
  root=base/Path(j['run_root']).relative_to(P)
  need(root.resolve()==root and not root.is_symlink(),'canonical output directory')
  paths=[p for p in root.rglob('*') if p.is_file()]
  paths += [base/f"results/slurm/{j['name']}_{j['job_id']}.{x}" for x in ('out','err')]
  paths += [base/f"results/formal_main_v2/job_receipts/{j['job_id']}.json"]
  for p in paths:
   rel=p.relative_to(base).as_posix();need(rel in expected,'unexpected nonweight output')
   row=expected[rel];need(row['job_id']==j['job_id'] and row['source']==str(P/rel),'original file ownership')
   need(p.resolve()==p and not p.is_symlink(),'no output path alias')
   need(p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'original output bytes: '+rel);found.add(rel)
 need(found==set(expected),'missing original outputs')
 return expected

def check_phase(item,step,phase,state):
 need(item['phase']==phase and item['control_step']==step,'fixed first/middle/last indices')
 need(item['arrays']['path']==phase+'.npz','exact raw NPZ basename')
 need(item['observation_id']==f"task{state['task_id']:02d}:state{state['source_state_index']:04d}:step{step:04d}",'fixed observation ID')

def check_arrays(arrays):
 need(set(arrays)==set(SHAPES),'only five current observation arrays')
 for key,a in arrays.items():
  need((str(a.dtype),a.shape)==SHAPES[key] and not a.dtype.hasobject and np.isfinite(a).all(),'native finite array shape/type: '+key)

def inspect_raw(value,base):
 validate_files(value,base)
 if str(R/'src') not in sys.path:sys.path.insert(0,str(R/'src'))
 from cti_vla.evaluation import formal_profiling as fp
 from cti_vla.evaluation.profiling import RAW_KEYS,RawObservation,observation_signature
 from cti_vla.evaluation.libero_runtime import _observation_hash
 reg=read(R/'configs/experiments/formal_main_v2.json')
 reports=[];allow=[]
 for job in value['selected_registered_jobs']:
  suite,horizon,seconds,minimum=validate_job(job,job);jid=job['job_id'];o=base/Path(job['run_root']).relative_to(P)
  cfg=read(o/'config.json');panel=read(o/'panel.json');summary=read(o/'summary.json')
  development=read(R/f'configs/manifests/formal_main_v2/{suite}/initial_states/development.json')
  states=[min([s for s in development['states'] if s['task_id']==i],key=lambda x:x['source_state_index']) for i in range(10)]
  need([s['source_state_index'] for s in states]==minimum and fp.fixed_profile_states(development)==states,'original per-task minimum state selection')
  need(cfg['command']=='collect' and cfg['suite']==suite and cfg['slurm_job_id']==jid,'runtime collect identity')
  need(cfg['manifest']['environment']==dict(action_chunk=8,environment_seed=0,max_steps=horizon,runtime_seed=17,wait_steps=10),'frozen environment settings')
  need(cfg['manifest']['split']=='development' and cfg['test_opened'] is False and cfg['future_head_deployed'] is False,'development-only no future head')
  need(cfg['dense_identity']==cfg['manifest']['methods'][0]['identity'] and cfg['dense_identity']['visual_tokens']==512 and cfg['checkpoint']['revision']==cfg['dense_identity']['model_revision'],'official frozen dense identity')
  need(cfg['profiler_module_sha256']==value['sources']['src/cti_vla/evaluation/formal_profiling.py'],'frozen profiler module')
  need(summary['new_success_trials'] is False and summary['test_opened'] is False and summary['status']=='completed_collection','complete non-scientific collection')
  samples,meta=fp.load_profile_panel(o/'panel.json',development=development,registration=reg,dense_identity=cfg['dense_identity'])
  need(len(samples)==30 and meta==summary['panel'],'original immutable profile-panel loader')
  events=[json.loads(b) for b in (o/'collection_trials.jsonl').read_bytes().splitlines()]
  need(len(events)==20 and [e['event'] for e in events]==['start','result']*10,'ten fixed start/result records, no replacement')
  total=0;calls=0;tasks=[]
  for i,state in enumerate(states):
   start,row=events[2*i:2*i+2];receipt=read(o/f'task{i:02d}/receipt.json');tr=receipt['trajectory'];n=tr['control_steps']
   need(all(e['trial_id']==state['trial_id'] and e['run_signature']==sig(cfg) and e['method']=='dense' for e in (start,row)),'fixed trial identity')
   need(receipt['state']=={k:state[k] for k in fp.STATE_FIELDS},'original state metadata')
   need(tr=={k:v for k,v in row.items() if k not in ('event','trial_id','method','run_signature')},'receipt/raw trajectory equality')
   need(receipt['provenance']==panel['provenance'] and receipt['test_opened'] is False and receipt['new_success_trials'] is False,'receipt provenance and science scope')
   need(tr['status']=='completed' and tr['wait_steps']==10 and 3<=n<=horizon,'real wait/horizon')
   need((tr['success'] and tr['termination']=='environment_success') or (tr['success'] is False and tr['termination']=='task_horizon' and n==horizon),'retained result without filtering')
   need(len(tr['executed_actions'])==n and [c['control_step'] for c in tr['chunks']]==list(range(0,n,8)) and tr['policy_calls']==len(tr['chunks'])==(n+7)//8,'actual chunk8 cadence and action count')
   hashes=receipt['all_control_observation_sha256'];need(len(hashes)==n,'all observed control-step hashes')
   for c in tr['chunks']:
    step=c['control_step'];m=c['metadata'];need(c['observation_sha256']==hashes[step],'policy observation chronology')
    need(np.array_equal(np.asarray(tr['executed_actions'][step:min(step+8,n)]),np.asarray(c['environment_actions'][:min(8,n-step)])),'actual action queue equals policy chunks')
    need(m['method']=='dense' and m['visual_tokens']==512 and m['per_camera_budgets']==[256,256] and m['future_head_calls']==0 and m['policy_calls']==1 and m['vision_calls']==1 and m['scorer_calls']==0 and m['packing_calls']==1,'dense deployment counters')
   selected=[0,(n-1)//2,n-1];need(len(receipt['observations'])==3,'exact three observations')
   for item,step,phase in zip(receipt['observations'],selected,('first','middle','last')):
    check_phase(item,step,phase,state);path=o/f'task{i:02d}'/(phase+'.npz')
    need(path.stat().st_size==394644 and sha(path)==item['arrays']['sha256'],'original NPZ file SHA and length')
    with zipfile.ZipFile(path) as z:
     names=z.namelist();need(len(names)==5 and set(names)=={k+'.npy' for k in RAW_KEYS},'no hidden/duplicate NPZ members')
    with np.load(path,allow_pickle=False) as z:arrays={k:z[k].copy() for k in z.files}
    check_arrays(arrays);raw=hashlib.sha256();roll=hashlib.sha256()
    for k in RAW_KEYS:
     a=np.ascontiguousarray(arrays[k]);raw.update(json.dumps([k,a.dtype.str,a.shape]).encode());raw.update(a.tobytes());roll.update(k.encode()+str(a.dtype).encode()+str(a.shape).encode()+a.tobytes())
    sample=RawObservation(item['observation_id'],state['trial_id'],state['task_name'],receipt['instruction'],phase,arrays)
    need(raw.hexdigest()==item['raw_sha256']==observation_signature(sample),'recomputed original raw observation SHA')
    need(roll.hexdigest()==item['rollout_observation_sha256']==hashes[step]==_observation_hash(arrays),'recomputed rollout observation SHA')
    allow.append(dict(path=str(path.relative_to(base)),sha256=sha(path),bytes=path.stat().st_size,job_id=jid,suite=suite,task_id=i,source_state_index=state['source_state_index'],phase=phase,control_step=step,arrays={k:{'shape':list(a.shape),'dtype':str(a.dtype)} for k,a in arrays.items()}))
   total+=n;calls+=tr['policy_calls'];tasks.append(dict(task_id=i,source_state_index=state['source_state_index'],actual_control_steps=n,selected_control_steps=selected,policy_calls=tr['policy_calls'],termination=tr['termination'],collection_outcome_diagnostic_only=tr['success']))
  need(summary['policy_calls']==calls,'summary real query count')
  need(0<cfg['model_loading_seconds_excluded_from_calls']<summary['execution_wall_seconds_including_model_loading']<=seconds+1,'allocation includes all loading/collection')
  completion=read(o/f'action_execution/{jid}/completion.json')
  need(completion.get('status')=='returned','actual action wrapper returned')
  reports.append(dict(job_id=jid,suite=suite,observations=30,trajectories=10,control_steps=total,policy_calls=calls,tasks=tasks,checkpoint_metadata=cfg['checkpoint'],dense_identity=cfg['dense_identity'],environment=cfg['manifest']['environment'],allocation_gpu_seconds=seconds,cost_already_in_root_total=True,cost_increment=0,new_scientific_trials=0,O2A_or_components_measured=False,final_release=False))
 return dict(kind='author_collect_raw_byte_validation',status='passed_raw_checks_only',original_root_review_executed=False,original_consumer_executed=False,root_acceptance_pending=True,independent_acceptance_pending=True,jobs=reports,observation_npz_allowlist=allow,total_original_npz_bytes=sum(x['bytes'] for x in allow),new_scientific_trials=0,new_gpu_submissions=0,weights_read=False,sealed_values_read=False)

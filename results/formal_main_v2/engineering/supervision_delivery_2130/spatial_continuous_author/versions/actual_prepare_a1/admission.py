"""Exact Spatial64 seed23 continuation after retained CUDA-startup failure.
No submit/state writes. Original reviewer/173 scientific code remain unchanged.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import copy, hashlib, importlib.util, json, os, re, stat, sys
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
H=Path('/share/home/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
VERSION='spatial-cuda-continuous-admission-v1'
PAIR='libero_spatial_k64_seed23'
STAGE='libero_spatial_train_k64_seed23'
OUT='results/formal_main_v2/libero_spatial/k64/seed23/training'
STATE='results/experiment_supervisor/state.json'
INVREL='results/formal_main_v2/invocations/'+STAGE+'_attempt05.json'
CANON='scripts/ops/formal_spatial_cuda_continuous_admission_v1/'
REVIEWER='scripts/formal_cuda_terminal_review_v1/review_formal_segment_startup.py'
FAILURE='scripts/formal_cuda_terminal_review_v1/startup_failure_evidence.py'
OLD_REVIEWER='.local/cuda_terminal_review_0943/review_formal_segment_startup.py'
OLD_FAILURE='.local/cuda_terminal_review_0943/startup_failure_evidence.py'
REVIEWER_SHA='ee0efc4b762e879e91e5e184fbc33dc236741cf71d51a6f5b4711710812f47b4'
FAILURE_SHA='c07c5b686d103aaabfe8a7280c62ff2a8b61fcb3ab5d07ff7592011fabbfa480'
SOURCE_SHA='dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e'
INVENTORY='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
INV_SHA='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
EXECUTION='scripts/ops/formal_autonomous_training_v1/execution.py'
EXEC_SHA='f74cd59b04bf616a29564784a07d1e36a5f31e33f565830d5b2aee905d75755b'
AUTHORIZATION={'path':'configs/experiments/formal_main_v2_autonomous_execution_authorization_v1.json','sha256':'b709b1a822a6e07c583166496598566408c3fb012aeeadd315746ae817b4ab4d'}
ACTIVATION={'path':'configs/experiments/formal_main_v2_autonomous_execution_activation_v2.json','sha256':'7391c3bb17c36f8b0dbce540e28714ac6f721662118ddb7338d7c0288aa0bcef'}
NODE={'path':'configs/experiments/formal_main_v2_node_exclusion_v1.json','sha256':'bb14944d4c27bc56685f1b845553a68dbff0545360e37331316d95508a12ce38'}
ROOT_PATH=OUT+'/segment_reviews/3043399.json'
INDEPENDENT_PATH=OUT+'/segment_reviews/3043399_independent.json'
FAILURE_REVIEW={'path':OUT+'/startup_failure_reviews/3028522.json','sha256':'e3e00f34b1cbc5e8cb83f3aad7b470373d532239efe2057d95956004cebafae5'}
PROOF_KEYS=('root_recovery_review','independent_recovery_review','canonical_failure_review','terminal_pull')
SLURM='scripts/server/formal_main.slurm'
SLURM_SHA='4e0b7b714b2d6cb0440acc145dab770c4f53a9ba561fa208931af7ce9ae364ab'
HISTORY_IDS=['3024716','3025205','3028522','3043399']
HISTORICAL_SECONDS=11958
DEPENDENCIES={REVIEWER:REVIEWER_SHA,FAILURE:FAILURE_SHA,EXECUTION:EXEC_SHA,
 'scripts/review_formal_acceptance.py':'373bcaea3ca8da63ee684ab8c3af6adcd329daa8fcc952422984882c0c206926'}
def require(ok,message):
 if not ok:raise ValueError(message)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()+b'\n'
def relative(name):
 require(isinstance(name,str) and '\\' not in name and ':' not in name,'relative canonical path required')
 p=PurePosixPath(name)
 require(not p.is_absolute() and p.as_posix()==name and '..' not in p.parts,'path escape')
 require(not any('sealed' in x.lower() or x.lower() in {'test','weights','checkpoints'} for x in p.parts),'forbidden path')
 require(not any(x.lower() in {'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init'} for x in p.suffixes),'weight/state payload')
 require(p.suffix=='.py' or not any(x in name.lower() for x in ('init_state','initial_state','final_state','test_state')),'state payload')
 return p
def direct(path):
 p=Path(path).absolute()
 require(not any(x.is_symlink() for x in (p,*p.parents)),'symlink')
 require('..' not in p.parts,'traversal')
 return p
def stable(path):
 p=direct(path);a=p.stat();require(stat.S_ISREG(a.st_mode),'regular file required');h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 z=p.stat();require((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns),'changed while hashing')
 return {'sha256':h.hexdigest(),'bytes':a.st_size}
def load(path,pin,name):
 p=direct(path);raw=p.read_bytes();require(digest(raw)==pin,'module SHA differs: '+str(p))
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);exec(compile(raw,str(p),'exec'),m.__dict__);return m
class Evidence:
 def __init__(self,root):self.root=direct(root);self.hashes={}
 def watch(self,rel,pin=None):
  relative(rel);require(rel!=STATE,'state must be CAS-bound, not immutable evidence')
  h=stable(self.root/rel)['sha256'];require(pin is None or h==pin,'SHA differs: '+rel)
  require(rel not in self.hashes or self.hashes[rel]==h,'evidence drift: '+rel);self.hashes[rel]=h;return h
 def read(self,rel,pin=None):
  self.watch(rel,pin);return json.loads((self.root/rel).read_bytes())
 def ref(self,ref):
  require(isinstance(ref,dict) and set(ref)=={'path','sha256'},'exact reference required')
  return self.read(ref['path'],ref['sha256'])
 def unchanged(self):
  for rel,h in list(self.hashes.items()):self.watch(rel,h)
def proof_refs(auth):
 refs={key:auth.get(key) for key in PROOF_KEYS}
 for key,value in refs.items():
  require(isinstance(value,dict) and set(value)=={'path','sha256'},'exact terminal proof reference required: '+key)
  relative(value['path']);require(re.fullmatch('[0-9a-f]{64}',str(value['sha256'])),'invalid proof SHA')
 require(refs['root_recovery_review']['path']==ROOT_PATH and refs['independent_recovery_review']['path']==INDEPENDENT_PATH,'wrong Spatial recovery proof path')
 require(refs['canonical_failure_review']==FAILURE_REVIEW,'canonical failed allocation proof differs')
 require(re.fullmatch(r'results/formal_main_v2/pulls/[0-9]{8}T[0-9]{6}Z_[0-9a-f]{12}/receipt.json',refs['terminal_pull']['path']),'registered stable pull path required')
 return refs

def history(state):
 rows=[j for j in state['registered_jobs'] if j.get('experiment')=='formal_main_v2' and
  (j.get('stage_key')==STAGE or j.get('mode')=='train' and (j.get('suite'),j.get('visual_tokens'),j.get('training_seed'))==('libero_spatial',64,23))]
 rows=sorted(rows,key=lambda j:(j['submitted_utc'],j['job_id']))
 require([j['job_id'] for j in rows]==HISTORY_IDS,'exact four-job history required; new attempt/unknown blocks')
 for j,status,code,seconds,target in zip(rows,['COMPLETED','COMPLETED','FAILED','COMPLETED'],['0:0','0:0','1:0','0:0'],[3281,5203,73,3401],[500,1000,1500,1500]):
  expected=dict(experiment='formal_main_v2',mode='train',stage_key=STAGE,suite='libero_spatial',visual_tokens=64,training_seed=23,
   status=status,exit_code=code,elapsed_seconds=seconds,gpus=1,source_root=str(S),source_sha256=SOURCE_SHA,segment_end=target,run_root=str(P/OUT))
  require(all(j.get(k)==v for k,v in expected.items()),'retained job identity/cost differs')
 require(sum(j['elapsed_seconds']*j['gpus'] for j in rows)==HISTORICAL_SECONDS,'history bill omitted')
 return rows

def compare_reconstruction(saved,rebuilt,reviewer_path):
 require(saved.get('reviewer_sha256')==REVIEWER_SHA and saved.get('status')=='passed','wrong signed recovery reviewer')
 expected=copy.deepcopy(saved)
 # Only this recorded same-byte source relocation is allowed; no outcome exemption.
 old=expected.get('startup_failure_consumer',{})
 require(old in ({'path':p,'sha256':REVIEWER_SHA,'verifier_sha256':FAILURE_SHA} for p in (OLD_REVIEWER,REVIEWER)),'original reviewer source differs')
 require(reviewer_path in (OLD_REVIEWER,REVIEWER),'unregistered reviewer publication')
 expected['startup_failure_consumer']['path']=reviewer_path
 ignored={'status','reviewed_utc','reviewer_sha256','evidence_sha256','server_resume_checks'}
 require({k:v for k,v in expected.items() if k not in ignored}=={k:v for k,v in rebuilt.items() if k not in ignored},'original raw reconstruction differs')
 require(rebuilt.get('status')=='local_passed_remote_required','unexpected reconstruction status')
def continuation(old,auth,auth_ref,stamp,resumes,files):
 require(old.get('stage_key')==STAGE and old.get('segment_end')==1500 and old['argv'][-1:]==['--resume'],'not exact prior resume')
 new=copy.deepcopy(old);new['registered_utc']=stamp;new['segment_end']=5000
 for flag,before,after in [('--stop-after-updates','1500','5000'),('--max-wall-seconds','12600','169200')]:
  require(old['argv'].count(flag)==1 and old['argv'][old['argv'].index(flag)+1]==before,'execution option differs')
  new['argv'][new['argv'].index(flag)+1]=after
 new['continuous_admission']={'schema':'formal_main_v2','kind':'root_once_cuda_recovered_continuation','version':VERSION,
  'authorization':auth_ref,'pair_key':PAIR,'prior_job_ids':list(HISTORY_IDS),'historical_GPU_seconds':HISTORICAL_SECONDS,
  **copy.deepcopy(proof_refs(auth)),'completed_before':{'A':1500,'B':1500},'sample_cursor_before':{'A':12000,'B':12000},
  'resume_checks_before':copy.deepcopy(resumes),'target_updates_per_arm':5000,'allocation_time':'48:00:00','soft_wall_seconds':169200,
  'validation_updates':list(range(0,5001,500)),'checkpoint_every_updates':50,'single_new_attempt':True,'automatic_retry':False,
  'controller_admission_changed':False,'scientific_settings_changed':False,'gateway_files':files}
 return new
class Science:
 """Pinned reviewer does real raw reconstruction; test injection never reaches CLI."""
 def __init__(self,root,*,reviewer=None):
  self.root=direct(root);self.e=Evidence(root);self.reviewer=reviewer
 def prepare(self,state,auth,auth_ref):
  e=self.e;rows=history(state);refs=proof_refs(auth)
  saved=e.ref(refs['root_recovery_review']);ind=e.ref(refs['independent_recovery_review']);failure=e.ref(FAILURE_REVIEW);e.ref(refs['terminal_pull'])
  require(saved['registered_pair_jobs_at_review']==rows,'registered history changed since double review')
  require(saved['completed_by_arm']=={'A':1500,'B':1500} and saved['pair_allocated_gpu_seconds']==HISTORICAL_SECONDS and saved['requested_segment_end']==1500,'recovery boundary/cost differs')
  require(ind.get('kind')=='CUDA_original_target_recovery_independent_review' and ind.get('status')=='passed_original_target_recovery_only'
   and ind.get('root_review')==refs['root_recovery_review'] and ind.get('historical_failure_preserved') is True
   and ind.get('cost')==dict(all_pair_allocated_GPU_seconds=HISTORICAL_SECONDS,nested_phases_added=False,retained_FAILED_GPU_seconds=73,successful_recovery_GPU_seconds=3401,historical_success_GPU_seconds=8484,allocations=[dict(job_id=j,GPU_seconds=n) for j,n in zip(HISTORY_IDS,[3281,5203,73,3401])]),'independent proof differs')
  require(ind['actual_server_resume_checks']==saved['server_resume_checks'],'double-reviewed resume differs')
  require(ind.get('job_id')=='3043399' and ind.get('failed_job_id')=='3028522' and ind.get('original_target')==1500
   and ind.get('version')=='cuda-recovery-independent-2130-v1' and ind.get('suite')=='libero_spatial'
   and ind.get('visual_tokens')==64 and ind.get('seed')==23 and ind.get('continuous5000_admission_authorized') is False
   and ind.get('all173_source_R_and_S_match') is True and ind.get('same_AB_initialization_and_full40000_order') is True,'independent scope differs')
  for arm in ('A','B'):
   require(all(ind['arms'][arm].get(k)==v for k,v in {'completed_updates':1500,'cursor':12000,'sample_uses':12000,'replayed_or_uncommitted_samples':0}.items()),'independent cursor/replay differs')
   require([row['update'] for row in ind['arms'][arm]['validation']]==[0,500,1000,1500],'independent validation nodes differ')
   require(all(row.get('windows')==189 for row in ind['arms'][arm]['original_arm_primitive']['evaluations']),'full Spatial189 validation required')
  for proof in (saved,ind):
   for rel,h in proof.get('evidence_sha256',proof.get('read_evidence_sha256',{})).items():
    if rel!=STATE:e.watch(rel,h) # Historical STATE hash remains historical; full current history is matched above.
  inv=e.read(rows[-1]['invocation'],rows[-1]['invocation_sha256'])
  inventory=e.read(INVENTORY,INV_SHA);require(len(inventory['files'])==173 and inventory['source_sha256']==SOURCE_SHA,'source inventory differs')
  for rel,h in inventory['files'].items():e.watch(rel,h)
  e.ref(AUTHORIZATION)
  for rel,h in DEPENDENCIES.items():
   if rel not in (REVIEWER,FAILURE) or self.reviewer is None:e.watch(rel,h)
  reviewer=self.reviewer or load(self.root/REVIEWER,REVIEWER_SHA,'_continuous_original_review')
  require(reviewer.ROOT==self.root and stable(reviewer.__file__)['sha256']==REVIEWER_SHA,'reviewer root/source differs')
  require(stable(reviewer._startup.__file__)['sha256']==FAILURE_SHA,'failure verifier differs')
  rebuilt=reviewer.review('3043399',source_inventory=INVENTORY,pull_receipt=refs['terminal_pull']['path'],verify_server_resume=False,root=self.root)
  compare_reconstruction(saved,rebuilt,Path(reviewer.__file__).relative_to(self.root).as_posix())
  require(not (self.root/OUT/'training_summary.json').exists(),'already complete/new output')
  # Original rebuild validated all argv/watch/data/acceptance identities.
  stamp=datetime.now(timezone.utc).isoformat()
  new=continuation(inv,auth,auth_ref,stamp,saved['server_resume_checks'],auth['gateway_files'])
  require(not (self.root/INVREL).exists(),'invocation already published; do not reattempt')
  require('runtime_compatibility' not in new and new['entrypoint']=='scripts/run_formal_future.py','Spatial must use original frozen entry')
  require(inventory['files'][SLURM]==SLURM_SHA,'frozen Slurm wrapper differs')
  e.unchanged()
  return dict(invocation=new,invocation_relative=INVREL,wrapper=str(S/SLURM),wrapper_sha256=SLURM_SHA,
    inventory=inventory,root_review=saved,prior_jobs=rows,evidence_sha256=dict(e.hashes),
    server_resume_checks=saved['server_resume_checks'],prior_invocation=inv,original_raw_reconstructed=True)
class NativeIO:
 """Only registered project metadata and two exact resume files, hash-only."""
 def _verify(self,plan,published=False):
  if not published:require(not direct(P/INVREL).exists(),'server invocation already published')
  else:require(stable(P/INVREL)=={'sha256':digest(canonical(plan['invocation'])),'bytes':len(canonical(plan['invocation']))},'published invocation drift')
  require(not direct(P/OUT/'training_summary.json').exists(),'server pair already complete')
  watched={str(S/rel):h for rel,h in plan['inventory']['files'].items()}
  watched.update(plan['invocation']['watched_files'])
  watched.update({str(P/rel):h for rel,h in plan['root_review']['files'].items()})
  observed={}
  for name,h in watched.items():
   p=Path(name);base=S if p.is_relative_to(S) else P;relative(p.relative_to(base).as_posix())
   got=stable(p);require(got['sha256']==h,'server raw/source input changed: '+name);observed[name]=got
  expected={p[len(OUT)+1:] for p in plan['root_review']['files'] if p.startswith(OUT+'/')}
  actual=set()
  for d,dirs,files in os.walk(direct(P/OUT),followlinks=False):
   for n in dirs:direct(Path(d)/n)
   for n in files:actual.add(direct(Path(d)/n).relative_to(P/OUT).as_posix())
  require(actual==expected|{'.training.lock'} and (P/OUT/'.training.lock').stat().st_size==0,'server output added/missing after review')
  checks=[]
  for row in plan['server_resume_checks']:
   require(row['arm'] in ('A','B') and row['path']==str(H/'checkpoints/formal_main_v2/libero_spatial/k64/seed23'/row['arm']/'resume.pt') and row.get('exists') is True,'exact resume path required')
   got=stable(row['path']);require(got=={'sha256':row['sha256'],'bytes':row['bytes']},'checkpoint bytes changed')
   checks.append(copy.deepcopy(row))
  require(len(checks)==2 and {x['arm'] for x in checks}=={'A','B'},'exact two resume files required')
  return dict(server_files=observed,server_resume_checks=checks,optimizer_rng_deserialized=False,models_loaded=False)
 def preflight(self,plan):return self._verify(plan)
 def recheck(self,plan):return self._verify(plan,published=True)
 def publish(self,plan,raw,immutable):
  immutable(P/plan['invocation_relative'],raw)
  require(stable(P/plan['invocation_relative'])=={'sha256':digest(raw),'bytes':len(raw)},'published bytes differ')

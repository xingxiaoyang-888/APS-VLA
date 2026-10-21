"""Exact nonweight Goal3054717 archive inventory; no scientific admission."""
from pathlib import Path
import hashlib,json,importlib.util,sys,os,stat
import numpy as np
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/goal_terminal_archive_20261021T0334'
REL='results/formal_main_v2/engineering/goal_full200_20261021T0110/attempt01'
A=P/REL;O=R/'results/formal_main_v2/raw_runtime/goal_full200_20261021T0110/attempt01'
OBS='results/formal_main_v2/preflight/heartbeat_20261021T1134/initial_observation.json'
OBS_SHA='0c0520630396e633c5b417a401da18bd100974e79d5f962308cf892bd945ac41'
CONSUMER=P/'scripts/ops/formal_goal_full200_gate_v1/consumer.py'
CPIN='c12a6a5b99c4e34ff19f535a4725fecd9fcabc70ba1f37dc2c6c32c979ad3c4b'
META=['.original_run.adapter.lock','outer/events.jsonl','outer/typed_parent.json','outer/completion.json','observer/events.jsonl','observer/gate.jsonl','original_run/panel.json','original_run/trials.jsonl','original_run/closed_loop_report.json','original_run/.evaluation.lock','original_run/config.json','original_run/adapter_invocations/3054717_7d1b72f843be43459123540a6c7846c2.json','original_run/adapter_invocations/3054717_7d1b72f843be43459123540a6c7846c2.jsonl']
KEYS={'agentview_image','robot0_eye_in_hand_image','robot0_eef_pos','robot0_eef_quat','robot0_gripper_qpos'}
def require(v,m):
 if not v:raise ValueError(m)
def sh(b):return hashlib.sha256(b).hexdigest()
def stable(p):
 p=Path(p);require(p.resolve()==p and not any(v.is_symlink() for v in (p,*p.parents)),'symlink/noncanonical '+str(p))
 s=p.stat();require(stat.S_ISREG(s.st_mode),'not regular '+str(p));return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def filehash(p):
 a=stable(p);h=hashlib.sha256()
 with p.open('rb') as f:
  while True:
   b=f.read(1024*1024)
   if not b:break
   h.update(b)
 require(stable(p)==a,'source changed during hashing');return h.hexdigest(),a[2]
def write(name,v):
 with (D/name).open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
def refs(x):
 if type(x)is dict:
  if 'storage' in x and 'path' in x and 'sha256' in x and 'bytes' in x:yield x
  for v in x.values():yield from refs(v)
 elif type(x)is list:
  for v in x:yield from refs(v)
def main():
 D.mkdir(exist_ok=True)
 require(filehash(R/OBS)[0]==OBS_SHA,'terminal observation changed')
 terminal=json.loads((R/OBS).read_bytes());matches=[]
 def jobs(x):
  if type(x)is dict:
   if str(x.get('job_id',''))=='3054717' and x.get('elapsed_seconds')==2205:matches.append(x)
   for v in x.values():jobs(v)
  elif type(x)is list:
   for v in x:jobs(v)
 jobs(terminal)
 require(matches and all(x.get('status')=='COMPLETED' and x.get('exit_code')=='0:0' and x.get('gpus')==1 for x in matches),'not exact original terminal allocation')
 require(filehash(CONSUMER)[0]==CPIN,'original consumer changed')
 sp=importlib.util.spec_from_file_location('_goal_terminal_original_read_blob',CONSUMER);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c
 exec(compile(CONSUMER.read_bytes(),str(CONSUMER),'exec'),c.__dict__)
 actual=[]
 for p in A.rglob('*'):
  require(not p.is_symlink(),'symlink anywhere under exact attempt')
  if p.is_file() and not p.is_relative_to(A/'observer/blobs'):actual.append(p.relative_to(A).as_posix())
 require(sorted(actual)==sorted(META),'unknown or missing attempt metadata '+str(sorted(set(actual)^set(META))))
 metadata=[]
 for rel in META:
  p=A/rel;h,n=filehash(p);metadata.append(dict(namespace='P_attempt_metadata',source=str(p),restore_root='P',restore_relative=REL+'/'+rel,archive_path='P_attempt/'+rel,bytes=n,sha256=h))
 claim=json.loads((O/'claim.json').read_bytes());require(str(claim.get('job_id'))=='3054717' and claim.get('path')==str(O),'raw exclusive claim identity')
 h,n=filehash(O/'claim.json');metadata.append(dict(namespace='R_observation_metadata',source=str(O/'claim.json'),restore_root='R',restore_relative=str((O/'claim.json').relative_to(R)),archive_path='R_observations/claim.json',bytes=n,sha256=h))
 allow={};occurrences=0;capture_count=0;read_refs={}
 def admit(ref,namespace,role,index):
  nonlocal occurrences
  require(set(ref)=={'path','bytes','sha256','storage'},'unexpected blob ref fields')
  observation=namespace=='R_observations';suffix='.bin' if observation or role!='global_rng' else '.rng.json'
  require(ref['storage']==('root_approved_raw_observations' if observation else 'attempt_local'),'wrong storage class')
  p=Path(ref['path']) if observation else A/'observer'/ref['path']
  expected=(O if observation else A/'observer/blobs')/(ref['sha256']+suffix)
  require(p==expected,'blob path/suffix is not exact content address')
  require(type(ref['bytes']) is int and 0<=ref['bytes']<=(196608 if observation else 65536),'component storage ceiling')
  key=str(p);occurrences+=1
  if key not in allow:
   before=stable(p);raw=c.read_blob(ref,observation=observation,output_root=A,read_refs=read_refs)
   require(stable(p)==before,'blob changed during original read_blob')
   allow[key]=dict(namespace=namespace,source=key,restore_root='R' if observation else 'P',
    restore_relative=str(p.relative_to(R if observation else P)),archive_path=namespace+'/'+p.name,bytes=len(raw),sha256=sh(raw),
    event_reference_count=0,roles=[],first_capture=index,last_capture=index,original_consumer_read_blob_verified=True)
  v=allow[key];require(v['bytes']==ref['bytes'] and v['sha256']==ref['sha256'],'conflicting repeated ref')
  v['event_reference_count']+=1;v['last_capture']=index
  if role not in v['roles']:v['roles'].append(role)
 before=stable(A/'observer/events.jsonl')
 with (A/'observer/events.jsonl').open('rb') as f:
  for lineno,line in enumerate(f,1):
   require(line.endswith(b'\n'),'incomplete event tail');x=c.strict(line)
   local=[]
   if 'phase' in x:
    capture_count+=1;require(x.get('event_index')==capture_count and capture_count<=21032,'capture order/bound')
    arrays=x.get('observation_arrays');require(type(arrays)is dict and set(arrays)<=KEYS,'not exact five-component mapping')
    for key,m in arrays.items():
     require(type(m)is dict and 'blob'in m,'observation blob reference missing')
     dtype=np.dtype(m['dtype']);require(not dtype.hasobject and int(np.prod(m['shape']))*dtype.itemsize==m['bytes']==m['blob']['bytes'],'numeric component size mismatch')
     admit(m['blob'],'R_observations',key,capture_count);local.append(m['blob'])
    require(type(x.get('sim_array_blobs'))is dict,'passive sim mapping missing')
    for key,ref in x['sim_array_blobs'].items():admit(ref,'P_passive','sim:'+key,capture_count);local.append(ref)
    admit(x['global_rng'],'P_passive','global_rng',capture_count);local.append(x['global_rng'])
   require(list(refs(x))==local or sorted(json.dumps(v,sort_keys=True) for v in refs(x))==sorted(json.dumps(v,sort_keys=True) for v in local),'unknown event blob reference location')
 require(stable(A/'observer/events.jsonl')==before,'events changed while scanning')
 gate_refs=0
 before=stable(A/'observer/gate.jsonl')
 with (A/'observer/gate.jsonl').open('rb') as f:
  for line in f:
   require(line.endswith(b'\n'),'incomplete gate tail')
   for ref in refs(c.strict(line)):
    gate_refs+=1;obs=ref.get('storage')=='root_approved_raw_observations'
    require(ref.get('storage') in ('root_approved_raw_observations','attempt_local'),'unknown gate storage')
    p=Path(ref['path']) if obs else A/'observer'/ref['path']
    require(str(p) in allow and allow[str(p)]['sha256']==ref['sha256'] and allow[str(p)]['bytes']==ref['bytes'],'gate references blob absent from admitted events')
 require(stable(A/'observer/gate.jsonl')==before,'gate changed while scanning')
 actualobs=[]
 for p in O.iterdir():
  require(p.is_file() and not p.is_symlink(),'nonregular raw child')
  if p.name!='claim.json':actualobs.append(str(p))
 actualpass=[]
 for p in (A/'observer/blobs').iterdir():
  require(p.is_file() and not p.is_symlink(),'nonregular passive child');actualpass.append(str(p))
 expectedobs=[k for k,v in allow.items() if v['namespace']=='R_observations']
 expectedpass=[k for k,v in allow.items() if v['namespace']=='P_passive']
 require(set(actualobs)==set(expectedobs),'unknown/unreferenced or missing observation blobs')
 require(set(actualpass)==set(expectedpass),'unknown/unreferenced or missing passive/RNG blobs')
 members=sorted(allow.values(),key=lambda x:x['archive_path'])+metadata
 for item in metadata:require(filehash(Path(item['source']))==(item['sha256'],item['bytes']),'metadata changed at end')
 counts={k:dict(files=sum(v['namespace']==k for v in members),bytes=sum(v['bytes'] for v in members if v['namespace']==k)) for k in sorted({v['namespace'] for v in members})}
 inventory=dict(schema='formal_main_v2',kind='Goal3054717_exact_nonweight_terminal_archive_inventory',status='exact_event_allowlist_and_original_read_blob_verified',
  job_id='3054717',original_allocation_GPU_seconds=2205,terminal_observation=dict(path=OBS,sha256=OBS_SHA),
  source_consumer=dict(path=str(CONSUMER),sha256=CPIN),capture_count=capture_count,event_blob_references=occurrences,gate_blob_references=gate_refs,
  counts=counts,member_count=len(members),member_bytes=sum(x['bytes'] for x in members),members=members,
  unknown_unreferenced_files=[],symlinks=[],weights_or_final_values=False,scientific_admission=False,new_trials=0,new_GPU_jobs=0,
  restore_root_aliases=dict(R=str(R),P=str(P)),raw_sources_not_modified=True)
 write('inventory.json',inventory);print(json.dumps({k:inventory[k] for k in ('status','capture_count','event_blob_references','gate_blob_references','counts','member_count','member_bytes')},sort_keys=True),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as e:
  D.mkdir(exist_ok=True)
  with (D/'inventory_failure.json').open('x') as f:json.dump(dict(error_type=type(e).__name__,error=str(e),scientific_admission=False,new_GPU_jobs=0),f,indent=2)
  raise

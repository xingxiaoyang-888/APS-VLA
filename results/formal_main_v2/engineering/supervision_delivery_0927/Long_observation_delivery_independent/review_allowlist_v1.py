from pathlib import Path,PurePosixPath
import hashlib,json,io,zipfile,datetime
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
O=R/'.local/Git_observation_delivery_review_0927'
A='results/formal_main_v2/preflight/heartbeat_20261020T1727/observation_npz_delivery_allowlist.json'
Q='results/formal_main_v2/downstream_reviews/3047982.json'
AP='b23a11f750ded441b0dfd1f3c066eb032c783b186e567975b34a14f0856880e1'
QP='45e76fbb32159d53dc7be7e5ca6b25d4d52815d44d0234063f30a69500567479'
RUN='results/formal_main_v2/libero_10/downstream/collect/648ce4233e78353e/attempt01'
EXPECTED={'agentview_image':{'dtype':'|u1','shape':[256,256,3]},
 'robot0_eye_in_hand_image':{'dtype':'|u1','shape':[256,256,3]},
 'robot0_eef_pos':{'dtype':'<f8','shape':[3]},'robot0_eef_quat':{'dtype':'<f8','shape':[4]},
 'robot0_gripper_qpos':{'dtype':'<f8','shape':[2]}}
refs={}
def sha(b):return hashlib.sha256(b).hexdigest()
def read(rel,pin):
 p=R/rel
 assert not p.is_symlink() and p.is_file()
 for parent in p.parents:
  if parent==R:break
  assert not parent.is_symlink()
 b=p.read_bytes();assert sha(b)==pin,(rel,sha(b),pin)
 refs[rel]={'path':rel,'sha256':pin,'bytes':len(b)}
 return b

def js(rel,pin):return json.loads(read(rel,pin))
def out(name,value):
 p=O/name
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 return {'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}

allow=js(A,AP);root=js(Q,QP)
assert allow['kind']=='exact_collected_development_observation_NPZ_delivery_allowlist'
assert allow['root_collect_review']=={'path':Q,'sha256':QP}
assert allow['status']=='passed' and allow['observations']==30 and allow['tasks']==10
assert allow['numpy_allow_pickle'] is False and allow['one_off_allowlist_not_general_NPZ_permission'] is True
assert root['status']=='passed' and root['stage']=='collect' and root['suite']=='libero_10' and str(root['job_id'])=='3047982'
assert not root['final_release'] and not root['final_state_values_read']
assert root['run_root']==str(P/RUN)
assert len(allow['files'])==30
allow_by={x['path']:x for x in allow['files']};assert len(allow_by)==30
expected_paths={f'{RUN}/task{task:02d}/{phase}.npz' for task in range(10) for phase in ['first','middle','last']}
assert set(allow_by)==expected_paths
root_npz={k:v for k,v in root['files'].items() if k.endswith('.npz')}
assert set(root_npz)==expected_paths
pullref=root['pull_ref'];pull=js(pullref['path'],pullref['sha256'])
assert pull['status']=='verified_nonweight_snapshot' and pull['weights_copied'] is False and pull['sealed_initial_states_copied'] is False
assert pull['requested_job_ids']==['3047982'] and not pull['missing']
pullrows={x['relative']:x for x in pull['files']};assert len(pullrows)==len(pull['files'])
assert {k for k in pullrows if k.endswith('.npz')}==expected_paths
panelrel=RUN+'/panel.json';panel=js(panelrel,root['files'][panelrel])
assert panel['split']=='development' and panel['suite']=='libero_10' and panel['test_opened'] is False and panel['new_success_trials'] is False
assert panel['selection_rule']=='actual pre-action control steps 0,floor((N-1)/2),N-1; no padding or replacement'
assert len(panel['episodes'])==10 and {int(x['task_id']) for x in panel['episodes']}==set(range(10))
observations={}
for ep in panel['episodes']:
 task=int(ep['task_id']);epref=ep['receipt'];rel=f'{RUN}/task{task:02d}/receipt.json'
 assert epref['path']==f'task{task:02d}/receipt.json' and root['files'][rel]==epref['sha256']
 rec=js(rel,epref['sha256'])
 assert rec['split']=='development' and rec['test_opened'] is False and rec['new_success_trials'] is False
 assert rec['state']['task_id']==task and len(rec['observations'])==3
 n=rec['trajectory']['control_steps'];assert n>0
 phase_steps={'first':0,'middle':(n-1)//2,'last':n-1}
 assert {x['phase'] for x in rec['observations']}==set(phase_steps)
 for ob in rec['observations']:
  phase=ob['phase'];assert ob['control_step']==phase_steps[phase]
  assert ob['arrays']['path']==phase+'.npz'
  name=f'{RUN}/task{task:02d}/{phase}.npz'
  assert name not in observations and ob['arrays']['sha256']==allow_by[name]['sha256']==root_npz[name]
  observations[name]={'task_id':task,'phase':phase,'control_step':ob['control_step'],'observation_id':ob['observation_id']}
assert set(observations)==expected_paths
files=[]
for name in sorted(expected_paths):
 row=allow_by[name];assert row['array_schema']==EXPECTED and row['bytes']==394644
 assert PurePosixPath(name).as_posix()==name and not any(v in PurePosixPath(name).parts for v in ['test','final','sealed','weights','checkpoints'])
 item=pullrows[name]
 assert item['sha256']==row['sha256'] and item['bytes']==row['bytes'] and item['job_ids']==['3047982']
 assert item['path']==str(P/name) and item['local_path']==str(R/name) and item['action']=='downloaded_verified'
 b=read(name,row['sha256']);assert len(b)==394644 and len(b)<100*(1<<20)
 with zipfile.ZipFile(io.BytesIO(b)) as z:
  members=z.infolist()
  assert len(members)==5 and {x.filename for x in members}=={k+'.npy' for k in EXPECTED}
  assert not z.comment and all(not x.is_dir() and not x.flag_bits & 1 for x in members)
  assert z.testzip() is None
 with np.load(io.BytesIO(b),allow_pickle=False) as z:
  assert len(z.files)==5 and set(z.files)==set(EXPECTED)
  for key,schema in EXPECTED.items():
   arr=z[key];assert arr.dtype.str==schema['dtype'] and list(arr.shape)==schema['shape']
   assert not arr.dtype.hasobject and np.isfinite(arr).all()
 # Byte identity against runtime origin, independently of the pull receipt.
 pb=(P/name).read_bytes();assert len(pb)==len(b) and sha(pb)==sha(b)
 files.append({**refs[name],**observations[name],'schema_verified':True,'runtime_origin_bytes_identical':True})
assert len(files)==30 and sum(x['bytes'] for x in files)==11839320==allow['total_bytes']
assert {str(p.relative_to(R)) for p in (R/RUN).glob('task??/*.npz')}==expected_paths
report={'schema':1,'kind':'independent_exact_development_observation_NPZ_Git_delivery_review','status':'passed',
 'reviewer':'/root/long128s41_terminal_0530','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'allowlist':refs[A],'root_collect_review':refs[Q],'pull':refs[pullref['path']],'panel':refs[panelrel],
 'array_schema':EXPECTED,'files':files,'observations':30,'tasks':10,'bytes_per_file':394644,'total_bytes':11839320,
 'numpy_allow_pickle':False,'no_object_arrays':True,'no_extra_zip_members':True,
 'exact_path_set_matches_panel_pull_root_allowlist_and_directory':True,'runtime_origin_bytes_identical':True,
 'scope':'One exact set of 30 task00..task09 first/middle/last development observation files. No general NPZ permission.',
 'suggested_commit_guard':'Any .npz must be in this exact pinned allowlist and match SHA256, bytes and the five-array schema. Every other .npz remains rejected. The staged index bytes must equal the verified worktree bytes.',
 'not_a_scientific_runtime_reaudit':True,'independent_scientific_acceptance_inferred':False,
 'no_model_weights_read':True,'no_sealed_or_final_initial_state_values_read':True,
 'GPU_jobs_run':False,'Git_mutation':False,'state_modified':False,'production_modified':False,'new_GPU_seconds':0,
 'sources':[v for k,v in refs.items() if not k.endswith('.npz')],'blockers':[]}
answer=out('typed_allowlist_review.json',report)
manifest_files=[]
for p in sorted(O.iterdir()):
 if p.is_file():manifest_files.append({'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size})
man=out('manifest.json',{'schema':1,'status':'passed','files':manifest_files,'note':'Transport closure log is separate because it is written after this script exits.'})
print(json.dumps({'status':'passed','review':answer,'manifest':man,'observations':30,'total_bytes':11839320,'GPU_seconds':0}))

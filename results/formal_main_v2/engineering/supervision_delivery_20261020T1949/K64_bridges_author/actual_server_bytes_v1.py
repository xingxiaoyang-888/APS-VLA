import sys,json,hashlib,os,datetime
from pathlib import Path
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
POLICIES={'spatial':'b4d18e84600de25dc193149903492cdda16df11d76e35a9d702c14ca0054b557','object':'2740fdd578a24d6c74a39d76b34223af46e6457932d797b9e0096124e479edcd'}
def h(p):
 q=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):q.update(b)
 return q.hexdigest()
def ref(x):
 p=R/x['path'];assert h(p)==x['sha256'];return json.loads(p.read_text())
rows=[]
for suite,pin in POLICIES.items():
 pp=D/suite/'revision02/package/policy_v1.json';assert h(pp)==pin;pol=json.loads(pp.read_text());root=ref(pol['references']['final_root']);ref(pol['references']['final_independent']);selected=ref(pol['references']['selected_server'])
 checkpoints=[]
 for arm,row in pol['selected_checkpoints'].items():
  p=Path(row['path']);assert p==Path(pol['pair']['checkpoint_root_server'])/arm/'best.pt';assert not p.is_symlink();actual=h(p);assert actual==row['sha256'];checkpoints.append({**row,'arm':arm,'kind':'best','actual_sha256':actual,'bytes':p.stat().st_size,'weights_copied':False,'deserialized':False})
 for row in root['server_resume_checks']:
  p=Path(row['path']);assert p==Path(pol['pair']['checkpoint_root_server'])/row['arm']/'resume.pt';assert not p.is_symlink();actual=h(p);assert actual==row['sha256'];assert p.stat().st_size==row['bytes'];checkpoints.append({**row,'kind':'resume','actual_sha256':actual,'weights_copied':False,'deserialized':False})
 config=[]
 for base in [R,P,S]:
  q=base/pol['pair']['path'];exists=q.is_file();actual=h(q) if exists else None
  if exists:assert actual==pol['pair']['sha256']
  config.append({'path':str(q),'exists':exists,'actual_sha256':actual,'expected':pol['pair']['sha256']})
 rows.append({'suite':pol['suite'],'policy':{'path':pp.relative_to(R).as_posix(),'sha256':pin},'checkpoints':checkpoints,'config':config,'all_pair_GPU_seconds':pol['total_GPU_seconds'],'failed_GPU_seconds_retained':pol['failed_GPU_seconds']})
o={'status':'passed_actual_server_checkpoint_bytes_only','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pairs':rows,'new_GPU_runs':0,'scientific_trials':0,'Slurm_calls':0,'no_weights_copied':True,'no_checkpoint_deserialization':True,'new_root_or_independent_training_acceptance_claimed':False}
p=D/'actual_server_bytes.json';p.write_text(json.dumps(o,sort_keys=True,indent=2)+'\n');print(json.dumps({'path':p.relative_to(R).as_posix(),'sha256':h(p),'pairs':len(rows),'checkpoint_files':sum(len(x['checkpoints']) for x in rows)}))

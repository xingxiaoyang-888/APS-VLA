from pathlib import Path
import json,hashlib,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1832';E='results/formal_main_v2/engineering/supervision_delivery_1032'
PACKAGES=[dict(base='.local/Long_legacy6_consumer_candidate_1032',manifest='manifest.json',pin='5fbdf3c85d730867f204dd6d298e2d257fcc5a09b68aafab116c7c1447745e5a',archive='Long_legacy6_consumer_candidate'),dict(base='.local/Long_legacy6_admission_independent_1032',manifest='manifest.json',pin='bb2ee0a9e88aa828c79c47458ac7a5739d9631740364776f963ad93e4f46c61c',archive='Long_legacy6_admission_independent')]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def clone(rel,b):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
 return ref(rel)
def save(rel,x):return clone(rel,(json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode())
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archive1032ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json');deliveries=[]
 for item in PACKAGES:
  base=Path(item['base']);mp=base/item['manifest'];assert h(R/mp)==item['pin']
  m=json.loads((R/mp).read_bytes());rows=[]
  for original in m['files']:
   row=dict(original);p=Path(row['path'])
   if not p.is_relative_to(base):p=base/p
   assert p.is_relative_to(base) and '..' not in p.parts and not p.is_absolute()
   row['path']=p.as_posix();rows.append(row)
  rows.append(dict(path=mp.as_posix(),sha256=h(R/mp),bytes=(R/mp).stat().st_size))
  copies=[]
  for row in rows:
   source=R/row['path'];assert source.is_file() and not source.is_symlink() and source.stat().st_size==row['bytes'] and h(source)==row['sha256']
   assert source.suffix not in ['.pt','.pth','.bin','.safetensors','.ckpt','.pyc','.npz','.npy'] and source.stat().st_size<100*(1<<20)
   dst=E+'/'+item['archive']+'/'+Path(row['path']).relative_to(base).as_posix()
   copies.append(dict(source=row,archive=clone(dst,source.read_bytes())))
  deliveries.append(save(B+'/'+item['archive']+'_delivery.json',dict(source_manifest=ref(mp.as_posix()),copies=copies,no_source_transformation=True,production_modified=False,new_GPU_jobs=0)))
 for name in ['observe_formal_1032.py','verify_runtime_inode_chain_1032.py','archive_1032_evidence.py']:
  clone(B+'/root_operations/'+name,(R/'.local'/name).read_bytes())
 clone(B+'/previous_Git_push_verified.json',(R/'.local/github_push_0927_verified.json').read_bytes())
 assert before==h(R/'results/experiment_supervisor/state.json')
 print(json.dumps(dict(status='evidence_archived_only',packages=deliveries,state_changed=False,new_GPU_jobs=0)),flush=True)

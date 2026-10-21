"""Archive exact private author/reviewer manifests; no runtime admission."""
from pathlib import Path
import argparse,hashlib,importlib.util,io,json,os,sys,tarfile
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261021T0910';E='results/formal_main_v2/engineering/supervision_delivery_20261021T0110'
ALLOWED={'.local/object_single_error_gateway_20261021T0110':'Object_single_error_gateway','.local/goal_full200_author_20261021T0110':'Goal_full200','.local/downstream_runtime_independent_20261021T0110':'Downstream_runtime_independent','.local/delivery_independent_20261021T0110':'Delivery_independent','.local/goal_full200_dispatch_20261021T0110':'Goal_full200_dispatch','.local/spatial_terminal_independent_20261021T0110':'Spatial_terminal_independent','.local/goal_full200_author_20261021T0110_v2':'Goal_full200_v2','.local/goal_full200_dispatch_20261021T0110_v2':'Goal_full200_dispatch_v2'}
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(p):
 p=Path(p);assert p.is_absolute() and p.resolve()==p and not any(x.is_symlink() for x in (p,*p.parents));return p
def cp(p,q):
 safe(p);safe(q);q.parent.mkdir(parents=True,exist_ok=True)
 if q.exists():assert q.read_bytes()==p.read_bytes()
 else:
  with q.open('xb') as f:f.write(p.read_bytes())
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,sort_keys=True,indent=2,ensure_ascii=False);f.write('\n')
def main():
 a=argparse.ArgumentParser();a.add_argument('--manifest',required=True);a.add_argument('--sha256',required=True);a=a.parse_args()
 p=safe(R/a.manifest);assert h(p)==a.sha256
 root=next((s for s in ALLOWED if str(p.relative_to(R)).startswith(s+'/')),None);assert root
 m=json.loads(p.read_bytes());files=m['files']
 declared=m.get('source_root',str(p.parent))
 if declared is not None:
  declared=safe(Path(declared));assert declared.is_relative_to(R/root)
  declared_prefix=declared.relative_to(R/root)
 else:declared_prefix=Path('.')
 if isinstance(files,dict):files=[dict(v,path=k) for k,v in files.items()]
 count=m.get('file_count',len(files));assert type(count)is int
 assert len(files)==count;rows=[];seen=set()
 for row in files:
  n=row.get('source',row.get('path'))
  if n.startswith(root+'/'):n=n[len(root)+1:]
  elif declared is not None:n=(declared_prefix/n).as_posix()
  assert n and not Path(n).is_absolute() and '..' not in Path(n).parts and n not in seen;seen.add(n)
  src=safe(R/root/n);assert src.is_file() and src.stat().st_size==row['bytes'] and h(src)==row['sha256']
  assert src.suffix.lower() not in ('.pt','.pth','.ckpt','.safetensors','.h5','.hdf5','.npy','.npz','.pkl','.pickle','.init','.pruned_init')
  assert src.suffix.lower()!='.bin'
  assert row['bytes']<100*(1<<20);rows.append(dict(name=n,source=root+'/'+n,sha256=row['sha256'],bytes=row['bytes']))
 cpath=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cpath)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
 sp=importlib.util.spec_from_file_location('archive2156ctl',cpath);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
 with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
  before=h(R/'results/experiment_supervisor/state.json');dst=R/E/ALLOWED[root];raws=[x for x in rows if Path(x['name']).suffix.lower()=='.bin']
  for row in rows:
   if row in raws:continue
   cp(R/row['source'],dst/row['name'])
  tarref=None
  assert not raws
  cp(p,dst/(p.stem+'_original.json'))
  assert h(R/'results/experiment_supervisor/state.json')==before
  out=dict(status='immutable_nonweight_package_archived',manifest=dict(path=a.manifest,sha256=a.sha256),destination=dst.relative_to(R).as_posix(),file_count=len(rows),bytes=sum(r['bytes'] for r in rows),CPU_binary_archive=tarref,state_unchanged=True,GPU_jobs_added=0,not_runtime_admission=True,member_root=declared.relative_to(R).as_posix(),copied_files=[dict(path=(dst/r['name']).relative_to(R).as_posix(),source=r['source'],sha256=r['sha256'],bytes=r['bytes']) for r in rows])
  save(R/B/(ALLOWED[root]+'_'+p.stem+'_archive.json'),out);print(json.dumps(out))
if __name__=='__main__':main()

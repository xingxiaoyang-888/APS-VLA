from pathlib import Path
import argparse,json,hashlib,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T2218';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1418'
ap=argparse.ArgumentParser();ap.add_argument('--base',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--archive',required=True);a=ap.parse_args()
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def put(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw
 else:
  with p.open('xb') as f:f.write(raw)
base=Path(a.base);assert base.parts[0]=='.local' and not base.is_absolute() and '..' not in base.parts
assert '/' not in a.archive and '\\' not in a.archive and a.archive not in ('','.','..')
m=base/a.manifest;assert m.is_relative_to(base) and '..' not in m.parts and h(R/m)==a.sha256
data=json.loads((R/m).read_bytes())
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archive20261020T1418',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json')
 rows=data['files']+[dict(path=m.as_posix(),sha256=a.sha256,bytes=(R/m).stat().st_size)];copies=[]
 for row in rows:
  rel=Path(row['path'])
  if not rel.is_relative_to(base):rel=base/rel
  assert rel.is_relative_to(base) and not rel.is_absolute() and '..' not in rel.parts
  src=R/rel;assert src.is_file() and not any(p.is_symlink() for p in [src,*src.parents])
  assert h(src)==row['sha256'] and src.stat().st_size==row['bytes']
  assert src.suffix not in ('.pt','.pth','.ckpt','.bin','.safetensors','.pyc','.npz','.npy','.h5','.hdf5') and src.stat().st_size<100*(1<<20)
  dst=E+'/'+a.archive+'/'+rel.relative_to(base).as_posix();put(R/dst,src.read_bytes())
  copies.append(dict(source={**row,'path':rel.as_posix()},archive=ref(dst)))
 out=B+'/'+a.archive+'_delivery.json'
 put(R/out,(json.dumps(dict(source_manifest=ref(m.as_posix()),copies=copies,no_source_transformation=True,new_GPU_jobs=0),sort_keys=True,indent=2)+'\n').encode())
 assert h(R/'results/experiment_supervisor/state.json')==before
 put(R/B/'root_operations/archive_private_20261020T1418.py',Path(__file__).read_bytes())
 print(json.dumps(dict(receipt=ref(out),files=len(copies),state_unchanged=True)))

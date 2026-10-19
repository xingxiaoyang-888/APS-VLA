from pathlib import Path
import hashlib,json,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0530'
D=R/'.local/spatial_continuous_admission_independent_2130';DEST=R/'results/formal_main_v2/engineering/supervision_delivery_2130/spatial_continuous_independent'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
mp=D/'archive_closure.json';assert h(mp)=='f5dece6634cd812196cd5d8a6d01cef42ba4193e95a73d702f25762f745aa652'
m=json.loads(mp.read_bytes());rows=m['files']+m['external_transport']+[dict(path=mp.relative_to(R).as_posix(),sha256=h(mp),bytes=mp.stat().st_size)]
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archiveind2130ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json');out=[]
 for row in rows:
  src=R/row['path'];assert not src.is_symlink() and src.is_file() and h(src)==row['sha256'] and src.stat().st_size==row['bytes']
  assert src.suffix not in ('.pt','.pth','.ckpt','.safetensors','.pyc','.bin','.init')
  rel=src.relative_to(D) if src.is_relative_to(D) else Path('transport')/src.name
  dst=DEST/rel;dst.parent.mkdir(parents=True,exist_ok=True)
  if dst.exists():assert h(dst)==row['sha256'] and dst.stat().st_size==row['bytes']
  else:
   with dst.open('xb') as f:f.write(src.read_bytes())
  out.append(dict(source=row['path'],path=dst.relative_to(R).as_posix(),sha256=h(dst),bytes=dst.stat().st_size))
 assert h(R/'results/experiment_supervisor/state.json')==before
 p=R/B/'Spatial_continuous_independent_archive_map.json'
 with p.open('x') as f:json.dump(dict(schema='formal_main_v2',files=out,state_changed=False,weight_files_copied=False),f,sort_keys=True,indent=2);f.write('\n')
 dst=R/B/'root_operations/archive_spatial_continuous_independent_2130.py'
 with dst.open('xb') as f:f.write(Path(__file__).read_bytes())
 print(json.dumps(dict(files=len(out),bytes=sum(x['bytes'] for x in out),archive_map_sha256=h(p))))

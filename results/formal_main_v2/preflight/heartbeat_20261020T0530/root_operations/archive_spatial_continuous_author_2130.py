from pathlib import Path
import json,hashlib,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
BASE=R/'.local/spatial_continuous_admission_2130'
D=R/'results/formal_main_v2/engineering/supervision_delivery_2130/spatial_continuous_author'
B=R/'results/formal_main_v2/preflight/heartbeat_20261020T0530'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
mp=BASE/'archive_manifest.json';assert h(mp)=='053c9e1f74f5e75d09aa3a938fc291fba3150529590700ca5778713b1f55fa72'
m=json.loads(mp.read_text())
rows=m['files']+[dict(path=mp.relative_to(R).as_posix(),sha256=h(mp),bytes=mp.stat().st_size)]
for row in rows:
 p=R/row['path'];assert p.is_file() and not p.is_symlink() and p.stat().st_size==row['bytes'] and h(p)==row['sha256']
 assert p.suffix not in ('.pt','.pth','.ckpt','.pyc','.safetensors','.bin','.init')
 assert p.stat().st_size < 100*1024*1024
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archive_spatial_2130ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state0=h(R/'results/experiment_supervisor/state.json')
 out=[]
 for row in rows:
  p=R/row['path']
  rel=p.relative_to(BASE) if p.is_relative_to(BASE) else Path('transport')/p.name
  dst=D/rel;dst.parent.mkdir(parents=True,exist_ok=True)
  with dst.open('xb') as f:f.write(p.read_bytes())
  assert h(dst)==row['sha256'];out.append(dict(source=row['path'],path=dst.relative_to(R).as_posix(),sha256=row['sha256'],bytes=row['bytes']))
 assert h(R/'results/experiment_supervisor/state.json')==state0
 record=dict(schema='formal_main_v2',kind='root_exact_candidate_archive',manifest=dict(path=mp.relative_to(R).as_posix(),sha256=h(mp)),files=out,weights_copied=False,state_changed=False,source_files_published=False)
 with (B/'spatial_continuous_author_archive_map.json').open('x') as f:json.dump(record,f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(dict(files=len(out),bytes=sum(x['bytes'] for x in out),map_sha256=h(B/'spatial_continuous_author_archive_map.json'))))

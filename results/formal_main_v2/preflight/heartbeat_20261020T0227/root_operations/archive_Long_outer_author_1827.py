
from pathlib import Path
import json,hashlib,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0227'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base='.local/long_action_outer_1827';m=R/base/'archive_manifest.json';assert h(m)=='16543bc948950e2b1bd1279ec587cacc56037163dc655fef973ae87c65536afc'
items=json.loads(m.read_text())['files']+[dict(path=m.relative_to(R).as_posix(),sha256=h(m),bytes=m.stat().st_size)]
rows=[]
for row in items:
 p=R/row['path'];assert p.is_file() and not p.is_symlink() and h(p)==row['sha256'] and p.stat().st_size==row['bytes']
 if p.is_relative_to(R/base):dest=B+'/packages/long_outer_author/'+p.relative_to(R/base).as_posix()
 else:dest=B+'/packages/long_outer_author/provenance/'+p.relative_to(R).as_posix()
 assert p.suffix not in ('.pt','.ckpt','.pyc','.safetensors') and '.pytest_cache' not in p.parts
 rows.append(dict(source=row['path'],path=dest,sha256=row['sha256'],bytes=row['bytes']))
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archive1827ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 for row in rows:
  q=R/row['path'];q.parent.mkdir(parents=True,exist_ok=True)
  with q.open('xb') as f:f.write((R/row['source']).read_bytes())
  assert h(q)==row['sha256']
 out=R/B/'author_archive_publication.json'
 with out.open('x') as f:json.dump(dict(schema='formal_main_v2',files=rows,source_bytes_preserved=True,weights_copied=False),f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(dict(path=out.relative_to(R).as_posix(),sha256=h(out),files=len(rows),bytes=sum(x['bytes'] for x in rows))))

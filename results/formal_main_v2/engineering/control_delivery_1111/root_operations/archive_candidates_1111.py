from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
OUT='results/formal_main_v2/engineering/control_delivery_1111'
B='results/formal_main_v2/preflight/heartbeat_20261019T1911'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(rel,raw):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists()
 with p.open('xb') as f:f.write(raw)
def save(rel,v):write(rel,(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('root_archive1111',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json');rows=[]
 cuda=R/'.local/cuda_continuous_admission_1111';guard=R/'.local/action_mixed_prefix_guard_1111'
 assert h(cuda/'candidate_review.json')=='33b52d49492ef25d1c024b2e0bfa855db0a8d29462349312b63718fc1db9fffa'
 assert h(guard/'archive_closure.json')=='76635436c51bcce97bca1e3339644b5e1b1bc2a470370a3fa7fec904ceb35dc3'
 sources=[(p,OUT+'/cuda_author/'+p.name) for p in sorted(cuda.iterdir()) if p.is_file()]
 closure=json.loads((guard/'archive_closure.json').read_text())
 for rel,v in closure['files'].items():
  p=guard/rel;assert h(p)==v['sha256'] and p.stat().st_size==v['bytes'];sources.append((p,OUT+'/guard_author/'+rel))
 sources.append((guard/'archive_closure.json',OUT+'/guard_author/archive_closure.json'))
 for name in ['archive_candidates_1111.py','observe_formal_1111.py']:
  sources.append((R/'.local'/name,OUT+'/root_operations/'+name))
 for src,dst in sources:
  assert src.is_file() and not src.is_symlink() and src.is_relative_to(R/'.local') and src.stat().st_size<10_000_000
  raw=src.read_bytes();pin=hashlib.sha256(raw).hexdigest();write(dst,raw);assert h(src)==pin==h(R/dst)
  rows.append(dict(source=src.relative_to(R).as_posix(),archive=dst,sha256=pin,bytes=len(raw)))
 save(OUT+'/author_archive_manifest.json',dict(schema='formal_main_v2',kind='nonweight_engineering_original_byte_archive',utc=datetime.now(timezone.utc).isoformat(),files=rows,
  excluded=['Rebuildable pytest directories and caches; retained only on server'],production_sources_published=False,GPU_submitted=False,state_changed=False))
 assert h(R/'results/experiment_supervisor/state.json')==before
 print(json.dumps(dict(archived_files=len(rows),manifest=OUT+'/author_archive_manifest.json',sha256=h(R/OUT/'author_archive_manifest.json'))))

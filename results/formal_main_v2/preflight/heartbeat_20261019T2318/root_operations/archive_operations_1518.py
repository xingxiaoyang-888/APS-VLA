from pathlib import Path
import hashlib,json,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261019T2318'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cp(src,target,pin):
 p=R/src;q=R/target;assert h(p)==pin and not p.is_symlink();q.parent.mkdir(parents=True,exist_ok=True)
 if q.exists():assert h(q)==pin
 else:
  with q.open('xb') as f:f.write(p.read_bytes())
 assert h(q)==pin;return dict(source=src,path=target,sha256=pin,bytes=q.stat().st_size)
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';sp=importlib.util.spec_from_file_location('archops1518',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 manifest='.local/spatial_failure_diagnosis_1518/delivery_files.json';assert h(R/manifest)=='bbf19d2ae8934114e20f3b47dd4d554dd15c3da3b1ed9d6eae84aecdbf5f7e41';v=json.loads((R/manifest).read_text());rows=[]
 for row in v['files']:
  assert row['path'].startswith('.local/spatial_failure_diagnosis_1518/') and (R/row['path']).stat().st_size==row['bytes']
  rows.append(cp(row['path'],B+'/spatial_failure_diagnosis/'+Path(row['path']).name,row['sha256']))
 rows.append(cp(manifest,B+'/spatial_failure_diagnosis/delivery_files.json',h(R/manifest)))
 base=R/'.local/spatial_pending_reconciliation_independent_1518'
 for p in sorted(base.iterdir()):
  if p.is_file() and p.suffix in ['.py','.json','.txt','.log']:
   rows.append(cp(p.relative_to(R).as_posix(),B+'/pending_reconciliation_independent/'+p.name,h(p)))
 for p in sorted((R/'.local').glob('*1518*.py')):
  if p.is_file():rows.append(cp(p.relative_to(R).as_posix(),B+'/root_operations/'+p.name,h(p)))
 out=R/B/'root_and_independent_operations_archive.json'
 with out.open('x') as f:json.dump(dict(schema='formal_main_v2',files=rows,originals_retained=True,rebuildable_fixtures_excluded=True),f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(dict(archived=len(rows),manifest=out.relative_to(R).as_posix(),sha256=h(out))))

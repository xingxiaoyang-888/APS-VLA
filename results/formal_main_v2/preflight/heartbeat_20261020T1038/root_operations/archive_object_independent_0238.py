from pathlib import Path
import json,hashlib,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1038'
E='results/formal_main_v2/engineering/supervision_delivery_0238/Object64_recovery_independent'
D='.local/object64_recovery_independent_0238'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archiveObj0238',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json')
 name=D+'/delivery_files.json';assert h(R/name)=='bc10a436ed4873855e6359848c197dfb2c7e615c8d3bfbf50cbda5f031e6faf0'
 m=json.loads((R/name).read_bytes());rows=m['files']
 if isinstance(rows,dict):rows=[dict(path=D+'/'+p,**v) for p,v in rows.items()]
 rows=rows+[ref(name)];assert len(rows)==15
 copies=[]
 for row in rows:
  p=R/row['path'];assert p.is_relative_to(R/D) and p.is_file() and not p.is_symlink()
  assert p.stat().st_size==row['bytes'] and h(p)==row['sha256']
  dst=R/E/p.relative_to(R/D);dst.parent.mkdir(parents=True,exist_ok=True)
  with dst.open('xb') as f:f.write(p.read_bytes())
  copies.append(dict(original=row,archive=ref(dst.relative_to(R).as_posix())))
 result=dict(status='exact_archive_copied',manifest=ref(name),copies=copies,total_bytes=sum(x['original']['bytes'] for x in copies),canonical_independent=ref('results/formal_main_v2/libero_object/k64/seed23/training/segment_reviews/3044017_independent.json'),existing_dependencies_not_duplicated=True,state_changed=False,new_GPU_submissions=0)
 assert result['total_bytes']==517071
 with (R/B/'Object3044017_independent_delivery.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
 with (R/B/'root_operations/archive_object_independent_0238.py').open('xb') as f:f.write(Path(__file__).read_bytes())
 assert h(R/'results/experiment_supervisor/state.json')==before
 print(json.dumps(dict(status='archived',delivery=ref(B+'/Object3044017_independent_delivery.json'),files=len(rows),bytes=result['total_bytes'])),flush=True)

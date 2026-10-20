from pathlib import Path
import json,hashlib,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1038'
E='results/formal_main_v2/engineering/supervision_delivery_0238/Spatial_pending_independent'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size)
def rd(rel):return json.loads((R/rel).read_bytes())
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 return ref(rel)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archiveSpatial0238',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json')
 man='.local/spatial_pending_independent_0238/archive_closure.json';assert h(R/man)=='bf04f4559e0ce279cea8d79121d18de8399bc58b5859b40dfe145d31dc3c8653'
 m=rd(man);assert m['frozen'] and m['file_count']==len(m['files'])==7
 ind=rd('.local/spatial_pending_independent_0238/independent_review.json');assert ind['status']=='passed_read_only_precommit_review' and not ind['blockers']
 assert ind['candidate']['sha256']=='6cc0bce095f6f33bacd1fe6bd65ce2e3e1c8baa72ebaf0d27d96193c07e097cb'
 assert h(R/'.local/spatial_pending_independent_0238/independent_review.json')=='19e4acfccb4fe6fb07dc9c81e6aae40c2bbc1de00117744da33e1825d7e4988d'
 tr=m['external_transport'];assert h(R/tr['path'])==tr['sha256']
 copies=[]
 for row in m['files']+[ref(man)]:
  p=R/row['path'];assert p.parent==R/Path(man).parent and p.is_file() and not p.is_symlink()
  assert ref(row['path'])==row
  dst=R/E/p.name;dst.parent.mkdir(parents=True,exist_ok=True)
  with dst.open('xb') as f:f.write(p.read_bytes())
  copies.append(dict(original=row,archive=ref(dst.relative_to(R).as_posix())))
 op=R/B/'root_operations';op.mkdir(exist_ok=True)
 names=['observe_formal_0238.py','run_spatial_continuous_0238.py','reconcile_spatial_pending_0238.py','reconcile_spatial_pending_0238_a2.py','review_object64_recovery_0238.py','review_object64_recovery_0238_a2.py','archive_spatial_0238.py']
 ops=[]
 for n in names:
  p=R/'.local'/n;compile(p.read_bytes(),n,'exec')
  with (op/n).open('xb') as f:f.write(p.read_bytes())
  ops.append(ref((op/n).relative_to(R).as_posix()))
 with (R/B/'previous_Git_push_verified.json').open('xb') as f:f.write((R/'.local/github_push_0137_verified.json').read_bytes())
 result=save(B+'/Spatial_pending_independent_delivery.json',dict(status='exact_archive_copied',manifest=ref(man),files=copies,external_transport=tr,root_operations=ops,candidate_a1_executed=False,candidate_a2_committed=True,pending_reconciliation=ref(B+'/Spatial3044479_pending_reconciliation.json'),new_GPU_submissions=0))
 assert h(R/'results/experiment_supervisor/state.json')==before
 print(json.dumps(dict(status='archived',delivery=result),ensure_ascii=False))

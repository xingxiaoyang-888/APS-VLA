from pathlib import Path
import json,hashlib,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B=R/'results/formal_main_v2/preflight/heartbeat_20261020T0021'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';sp=importlib.util.spec_from_file_location('archive1621ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 mappings=[]
 for folder,manifest,pin,dest in [('.local/spatial_resume_1621','delivery_files_v2.json','44028949206c6ddc8ca00dde5a77b10f77650617ac1eac1f9b3fcf2a118ccaf2','spatial_resume_candidate'),('.local/spatial_cuda_reservation_audit_1621','archive_closure.json','7f049f5ec6bf2405345eddbb7b8c6a4d886e93212f1637c8e918bc8f2e61d388','spatial_cuda_reservation_independent')]:
  src=R/folder;mp=src/manifest;assert h(mp)==pin;v=json.loads(mp.read_text());rows=v['files']
  if isinstance(rows,dict):rows=[dict(path=folder+'/'+n,**x) for n,x in rows.items()]
  rows=rows+[dict(path=folder+'/'+manifest,sha256=pin,bytes=mp.stat().st_size)]
  for row in rows:
   p=R/row['path'];assert p.parent==src and p.is_file() and not p.is_symlink() and p.stat().st_size==row['bytes'] and h(p)==row['sha256']
   assert p.suffix in {'.py','.json','.log','.txt','.md','.xml'}
   target=B/dest/p.name;target.parent.mkdir(parents=True,exist_ok=True)
   with target.open('xb') as f:f.write(p.read_bytes())
   assert h(target)==row['sha256'];mappings.append(dict(source=row['path'],path=target.relative_to(R).as_posix(),sha256=h(target),bytes=target.stat().st_size))
 out=B/'candidate_and_cuda_review_archive.json'
 with out.open('x') as f:json.dump(dict(schema='formal_main_v2',kind='exact_nonweight_private_evidence_archive',files=mappings,originals_retained=True,production_activation_of_candidate=False),f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(dict(receipt=out.relative_to(R).as_posix(),sha256=h(out),files=len(mappings))))

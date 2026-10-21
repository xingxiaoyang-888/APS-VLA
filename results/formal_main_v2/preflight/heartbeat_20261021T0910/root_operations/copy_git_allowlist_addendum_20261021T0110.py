from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');A='.local/delivery_allowlist_independent_20261021T0110';D='results/formal_main_v2/engineering/supervision_delivery_20261021T0110/Delivery_allowlist_independent';B='results/formal_main_v2/preflight/heartbeat_20261021T0910'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--manifest',required=True);ap.add_argument('--sha256',required=True);a=ap.parse_args()
p=R/a.manifest;assert a.manifest.startswith(A+'/') and p.resolve()==p and h(p)==a.sha256
m=json.loads(p.read_bytes());files=m['files'];assert isinstance(files,list) and 1<=len(files)<=12
rows=[]
for row in files:
 n=row['path']
 if n.startswith(A+'/'):n=n[len(A)+1:]
 assert not Path(n).is_absolute() and '..' not in Path(n).parts
 src=R/A/n;dst=R/D/n;assert src.resolve()==src and dst.resolve()==dst and src.suffix in ('.json','.py','.md') and not any(q.is_symlink() for q in (src,*src.parents,dst,*dst.parents))
 assert h(src)==row['sha256'] and src.stat().st_size==row['bytes']<10*(1<<20)
 rows.append((src,dst,row))
cpath=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cpath)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('copy_git_addendum0910',cpath);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 st=R/'results/experiment_supervisor/state.json';before=h(st);assert before=='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa'
 for src,dst,row in rows:
  dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();dst.open('xb').write(src.read_bytes())
 dst=R/D/(p.stem+'_original.json');assert not dst.exists();dst.open('xb').write(p.read_bytes())
 out=dict(status='exact_supplemental_audit_copied',manifest=dict(path=a.manifest,sha256=a.sha256),copied_files=[dict(path=d.relative_to(R).as_posix(),source=s.relative_to(R).as_posix(),sha256=r['sha256'],bytes=r['bytes']) for s,d,r in rows],state_unchanged=True,new_GPU_jobs=[],no_scientific_changes=True)
 q=R/B/'git_allowlist_supplement_copy.json';q.open('x').write(json.dumps(out,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
 assert h(st)==before;print(json.dumps(out))

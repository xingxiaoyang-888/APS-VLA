from pathlib import Path
import json,hashlib,sys,importlib.util,tarfile
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T2330';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1530'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(src,dst,pin):
 assert h(src)==pin and src.is_relative_to(R) and (dst.is_relative_to(R) or dst.is_relative_to(P))
 for p in (src,*src.parents,dst,*dst.parents):assert not p.is_symlink()
 assert src.suffix not in ['.pt','.pth','.ckpt','.safetensors','.bin','.h5','.hdf5','.pyc']
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():assert dst.read_bytes()==src.read_bytes()
 else:
  with dst.open('xb') as f:f.write(src.read_bytes())
 return dict(source=dict(path=src.relative_to(R).as_posix(),sha256=pin,bytes=src.stat().st_size),archive=dict(path=dst.relative_to(R).as_posix(),sha256=h(dst)))
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archive1530ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
items=[('.local/goal64s17_terminal_20261020T1530','manifest.json','cc654ac3c847f3f47c355846cf81b348da2f873b0d51b43b78ec5c00a95aeff3','training_independent'),('.local/devterminal_independent_20261020T1530','manifest.json','b0bae47a60d4149e6414ccf8c7fa3b147ef47b538fdade958596c8d879ccee4e','terminal_independent'),('.local/devterminal_independent_20261020T1530','recompute_delivery_manifest.json','b9735b0b82fbc0144f8ad0097e97309bf88d9a8865a1bc32b034983cecbf8796','terminal_independent'),('.local/goal_t0_probe_independent_20261020T1530','delivery_manifest.json','a2466fa55bcb2de4dc2a85a8896983dcbab5b9e2d5bbad6fa9cdb2299784cfdf','Goal_probe_independent')]
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json');rows=[];fixture=None
 for srcdir,mn,mpin,dstdir in items:
  root=R/srcdir;manifest=root/mn;assert h(manifest)==mpin;data=json.loads(manifest.read_bytes());files=data['files']
  if dstdir=='Goal_probe_independent':
   tar=root/'synthetic_fixtures.tar.gz';assert h(tar)=='7d5cb59579290146cee8b5a12c96571233b0c8a1f885f1d6fb55b913220057fb'
   members={}
   with tarfile.open(tar,'r:gz') as f:
    for m in f.getmembers():
     assert m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts
     payload=f.extractfile(m).read();members[m.name]=dict(sha256=hashlib.sha256(payload).hexdigest(),bytes=len(payload))
   assert len(members)==944
   for v in files:
    if v['relative'] in members:assert members[v['relative']]==dict(sha256=v['sha256'],bytes=v['bytes']) and h(root/v['relative'])==v['sha256']
   covered={v['relative'] for v in files if v['relative'] in members};assert covered==set(members)
   fixture=dict(member_count=944,all_members_restored_in_memory_and_SHA_verified=True,synthetic_only=True,archive=dict(path=E+'/'+dstdir+'/synthetic_fixtures.tar.gz',sha256=h(tar)))
   files=[v for v in files if v['relative'] not in covered]
  for v in files:
   src=Path(v['path']);src=src if src.is_absolute() else R/src;relative=src.relative_to(root);rows.append(copy(src,R/E/dstdir/relative,v['sha256']))
  rows.append(copy(manifest,R/E/dstdir/mn,mpin))
 dep=R/'.local/nonLong64_development_plans_20261020T1530/attempt01/dependency_preview_v1/required_P_copies.json';assert h(dep)=='679e6a72d62f36f994e3e5f63fdeefd8585fd85c33cb6e5627f4ccaea117df5f';d=json.loads(dep.read_bytes());print('DEPENDENCY_KEYS',list(d))
 # Exact fixed original configs, no new methods or runtime implementation.
 published=[]
 for suite in ['libero_spatial','libero_object']:
  for seed in [17,41]:
   rel=f'configs/experiments/formal_main_v2/{suite}_k64_seed{seed}.json';src=R/rel;dst=P/rel
   assert h(src)==h(P/'snapshots/formal_main_v2_run_564be0995e'/rel);dst.parent.mkdir(parents=True,exist_ok=True)
   if dst.exists():assert dst.read_bytes()==src.read_bytes()
   else:
    with dst.open('xb') as f:f.write(src.read_bytes())
   published.append(dict(path=rel,sha256=h(dst)))
 # Canonical independent training receipt, exactly the independently sealed bytes.
 src=R/'.local/goal64s17_terminal_20261020T1530/3043762_independent_review.json'
 rows.append(copy(src,R/'results/formal_main_v2/libero_goal/k64/seed17/training/segment_reviews/3043762_independent.json','97a69fda379c85a6c07b56c78cddc134004359076cb2ce12b5703b73c73f5cee'))
 assert h(R/'results/experiment_supervisor/state.json')==before
 out=dict(status='exact_independent_nonweight_evidence_archived',copies=rows,binary_fixtures_archive=fixture,extra_config_publication=published,state_unchanged=True,new_jobs=0)
 p=R/B/'independent_evidence_delivery.json'
 with p.open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(dict(receipt=p.relative_to(R).as_posix(),sha256=h(p),copies=len(rows),configs=published)))

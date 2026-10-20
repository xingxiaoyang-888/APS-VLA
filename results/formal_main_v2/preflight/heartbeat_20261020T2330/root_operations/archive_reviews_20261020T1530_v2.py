from pathlib import Path
import json,hashlib,tarfile,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T2330';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1530'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=h(p),bytes=p.stat().st_size)
def cp(src,dst,pin):
 assert src.is_relative_to(R) and dst.is_relative_to(R) and h(src)==pin and src.stat().st_size<100*(1<<20)
 assert not any(z.is_symlink() for z in [src,*src.parents,dst,*dst.parents])
 assert src.suffix not in ('.pt','.pth','.ckpt','.bin','.safetensors','.pyc','.init','.npz','.npy','.h5','.hdf5')
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():assert dst.read_bytes()==src.read_bytes()
 else:
  with dst.open('xb') as f:f.write(src.read_bytes())
 return dict(source=ref(src),archive=ref(dst))
items=[('.local/goal_t0_dispatch_independent_20261020T1530','delivery_manifest.json','fd3280ae9b03e9051db6fff652931cfbfd6d9e1be4eda2c51e7767264f46c8d5','Goal_dispatch_independent'),('.local/nonLong64_development_independent_20261020T1530','delivery_manifest.json','0ffe6a36c8155ba916630fee4b7a002df7b5decd94eb2d0cb573eddf1590d14a','plan_independent'),('.local/integration_candidate_20261020T1530','manifest.json','7d5b7b077b92ef7ee53c1c8995c88e4ca09245163c3f6d30c2cdf560b9bb182b','integration_author'),('.local/completed_integration_independent_20261020T1530','complete_manifest.json','76aec59c3453641ee00768dd63b879ecb8872ffc17229d7ec908fa5c5af33736','integration_independent')]
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archivereviews1530ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json');copies=[];fixtures=[]
 for rootname,mn,mpin,dest in items:
  root=R/rootname;manifest=root/mn;assert h(manifest)==mpin
  files=json.loads(manifest.read_bytes())['files'];listed={}
  for row in files:
   src=Path(row['path']);src=src if src.is_absolute() else R/src
   rel=src.relative_to(root).as_posix();assert h(src)==row['sha256'] and src.stat().st_size==row['bytes'];listed[rel]=row
  covered=set()
  if dest=='Goal_dispatch_independent':
   for fn,pin,count in [('CPU_synthetic_dispatch_fixtures.tar.gz','6af948b60932af2da523b5aee0e9dfe264154be795ea0d108e7adaf3fab8ccc4',672),('actual_reconciliation_synthetic_fixtures.tar.gz','e5bce1a5cedc5864763409f03d6b2f9139cef8d6a785cbe339512f3a32f2871d',312)]:
    assert h(root/fn)==pin and listed[fn]['sha256']==pin
    names=[]
    with tarfile.open(root/fn,'r:gz') as t:
     for m in t.getmembers():
      assert m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts and m.name not in covered
      raw=t.extractfile(m).read();row=listed[m.name];assert hashlib.sha256(raw).hexdigest()==row['sha256'] and len(raw)==row['bytes']
      assert m.name.startswith(('fixtures/','actual/fixtures/'))
      covered.add(m.name);names.append(m.name)
    assert len(names)==count
    fixtures.append(dict(archive=dict(path=E+'/'+dest+'/'+fn,sha256=pin),member_count=count,all_members_restored_in_memory_and_SHA_verified=True,synthetic_only=True))
  for rel,row in listed.items():
   if rel not in covered:copies.append(cp(root/rel,R/E/dest/rel,row['sha256']))
  copies.append(cp(manifest,R/E/dest/mn,mpin))
 assert h(R/'results/experiment_supervisor/state.json')==before
 out=R/B/'completed_and_dispatch_review_delivery.json'
 with out.open('x') as f:json.dump(dict(status='exact_immutable_reviews_archived',copies=copies,synthetic_fixtures_archives=fixtures,state_unchanged=True,new_GPU_jobs=0),f,sort_keys=True,indent=2);f.write('
')
 print(json.dumps(dict(receipt=ref(out),files=len(copies),fixture_members=sum(x['member_count'] for x in fixtures))),flush=True)

from pathlib import Path
import hashlib,importlib.util,json,sys,tarfile
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0044';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1644'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=h(p),bytes=p.stat().st_size)
def put(p,b):
 assert p.is_relative_to(R) and not any(z.is_symlink() for z in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b
 else:
  with p.open('xb') as f:f.write(b)
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n'.replace('\\n','\n')).encode()
def save(n,v):put(R/n,(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+chr(10)).encode());return ref(R/n)
def mod(n,pin,name):
 p=R/n;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','archiveLast1644ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json');copies=[];packages=[]
 for private,pin,label in [('.local/object_bridge_production_independent_20261020T1644','a3728f93c079db51898613806e7c1891e5dede4be49c26d1763e37a4acd383af','Object_production_independent'),('.local/goal_prefix58_independent_20261020T1644','6ea9d9ec70af001e3ac960e9ce0b43695ca48499c55066378a59957398192488','Goal_prefix58_independent')]:
  root=R/private;m=root/'delivery_manifest.json';assert h(m)==pin;v=json.loads(m.read_bytes());paths={}
  for row in v['files']:
   n=row['path'];assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=root/n
   if 'source' in row:assert row['source']==p.relative_to(R).as_posix()
   assert h(p)==row['sha256'] and p.stat().st_size==row['bytes'] and not any(z.is_symlink() for z in [p,*p.parents]);paths[n]=p
  assert len(paths)==len(v['files']) and {p for p in root.rglob('*') if p.is_file()}==set(paths.values())|{m}
  blobs={n:p for n,p in paths.items() if p.suffix=='.bin'};members=[]
  if blobs:
   assert label=='Goal_prefix58_independent' and len(blobs)==432
   tarpath=root/'synthetic_blobs_lossless.tar.gz';assert h(tarpath)=='efc0884788806d464c3a4e6fbbe11554f7b56d5e1968701387d53af8d404a001'
   with tarfile.open(tarpath,'r:gz') as tar:
    entries=tar.getmembers();assert len(entries)==460 and len({q.name for q in entries})==460
    for q in entries:
     assert q.isfile() and q.name in paths and q.size==paths[q.name].stat().st_size;raw=tar.extractfile(q).read();assert hashlib.sha256(raw).hexdigest()==h(paths[q.name]);members.append(dict(member=q.name,source=ref(paths[q.name])))
    assert set(blobs)<={q.name for q in entries}
  for n,p in {**paths,'delivery_manifest.json':m}.items():
   if n in blobs:continue
   assert p.suffix not in ('.pt','.pth','.ckpt','.safetensors','.pyc','.init','.npz','.npy','.h5','.hdf5') and p.stat().st_size<100*(1<<20)
   dst=R/E/label/n;put(dst,p.read_bytes());copies.append(dict(source=ref(p),archive=ref(dst)))
  if blobs:save(E+'/'+label+'/root_binary_archive_verification.json',dict(status='all_synthetic_members_reconstructed',archive=ref(R/E/label/'synthetic_blobs_lossless.tar.gz'),members=members,model_or_checkpoint_bytes=False,new_GPU_jobs=0))
  packages.append(dict(manifest=ref(m),archive_manifest=ref(R/E/label/'delivery_manifest.json'),files=len(paths),bin_files_losslessly_archived=len(blobs)))
 receipt=save(B+'/Object_and_Goal_independent_delivery.json',dict(status='exact_complete_nonweight_packages_archived',copies=copies,packages=packages,Goal_engineering_not_GPU_ready=True,Goal_HOLD=True,new_GPU_jobs=0,state_unchanged=h(R/'results/experiment_supervisor/state.json')==before))
 print(json.dumps(dict(receipt=receipt,files=len(copies))),flush=True)
 m=mod('scripts/ops/nonweight_archive.py','f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2','archiveLast1644codec')
 old=R/'results/formal_main_v2/nonweight_archives/v1/snapshots/Goal64seed41_20261020T1530.json';assert h(old)=='caf74020b7a320bf41fb975ec8a8dcd10b54d9dc800ac51c28cd61d027ee341c'
 raw=[{k:x[k] for k in ['path','sha256','bytes']} for x in json.loads(old.read_bytes())['files']];provenance=[ref(old)]
 for n,pin,pair in [('results/formal_main_v2/pulls/20261020T170126Z_1fd1cd88b439/receipt.json','f0633ec7db1a6f09aa92afb332d452e91f81c9d69c6c356bf27df45bdb338036','libero_goal/k64/seed23'),('results/formal_main_v2/pulls/20261020T175321Z_d93105850084/receipt.json','892b66bae4074e0a88712113233ea10da4c05e39cb8a8f9c014e2d34f9ff1b06','libero_object/k64/seed23')]:
  pp=R/n;assert h(pp)==pin;pull=json.loads(pp.read_bytes());assert pull['status']=='verified_nonweight_snapshot';provenance.append(ref(pp))
  rows=[x for x in pull['files'] if x['relative'].startswith('results/formal_main_v2/'+pair+'/training/') and x['bytes']>20*(1<<20)];assert len(rows)==3
  for row in rows:
   q=R/row['relative'];rr=ref(q);assert q.suffix=='.jsonl' and rr['sha256']==row['sha256'] and rr['bytes']==row['bytes'];raw.append(rr)
 assert len(raw)==9 and len({x['path'] for x in raw})==9
 request=save(B+'/last_training_lossless_archive_request.json',dict(schema=m.SCHEMA,kind='archive_request',files=raw,provenance=provenance));snap='results/formal_main_v2/nonweight_archives/v1/snapshots/last_training_20261020T1644.json';result=m.pack(R,request['path'],snap);assert result['status']=='packed_verified' and result['original_bytes']==sum(x['bytes'] for x in raw)
 ip=R/'.gitignore';original=ip.read_text();added=['/'+x['path'] for x in raw if '/'+x['path'] not in original.splitlines()]
 if added:ip.write_text(original+chr(10)+'# Lossless raw training evidence, root verified 20261020T1644.'+chr(10)+chr(10).join(added)+chr(10))
 out=save(B+'/last_training_lossless_archive.json',dict(status='packed_verified_originals_retained',snapshot=ref(R/snap),request=request,raw=raw,result=result,all_costs_already_ledgered=True,new_GPU_jobs=0))
 assert h(R/'results/experiment_supervisor/state.json')==before
 print(json.dumps(dict(lossless=out,snapshot=ref(R/snap),raw_files=9,original_bytes=result['original_bytes'])),flush=True)

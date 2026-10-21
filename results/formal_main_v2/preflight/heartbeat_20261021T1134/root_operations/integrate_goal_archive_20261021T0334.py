from pathlib import Path,PurePosixPath
import hashlib,json,tarfile,shutil,sys,importlib.util,os
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261021T1134'
E='results/formal_main_v2/engineering/supervision_delivery_20261021T0334/Goal_archive'
PRIVATE='.local/goal_terminal_archive_20261021T0334'
def h(p):
 x=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):x.update(b)
 return x.hexdigest()
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
 return dict(path=rel,sha256=h(p),bytes=p.stat().st_size)
def read(rel,pin):
 p=R/rel;assert h(p)==pin;return json.loads(p.read_text())
assert os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R)
manifest=read(PRIVATE+'/delivery_manifest.json','b395e025b469f72e3b0e2bcbcf75258fd662c4e57b23309f24ecf4ebe86b37a1')
inv=read(PRIVATE+'/inventory.json','db4d8a05cd7f21af5aac0687d2190297cd571eb1a6ffc83eb74d235d53eb7ac1')
arc=read(PRIVATE+'/archive_manifest.json','18c61e6a89047e7c4a0cdab7e6111f73a36db0421a3c2b1627a2f01944cf4d21')
review=read(B+'/Goal_terminal_review.json','96de85c4c3954d8176461950f53bb6fb6dc6dd441454401a3d8fe5364bb9e18b')
actual=review['raw_gate']['raw_blob_refs'];expected={}
for m in inv['members']:
 if m['namespace'] in ('R_observations','P_passive'):
  expected[str(R/m['restore_relative'])]=dict(sha256=m['sha256'],bytes=m['bytes'])
assert expected==actual and len(expected)==35062
assert len(manifest['files'])==len({r['path'] for r in manifest['files']})==57
for row in manifest['files']:
 src=R/row['path'];assert src.is_relative_to(R/PRIVATE) and src.resolve()==src and not src.is_symlink()
 assert src.stat().st_size==row['bytes'] and h(src)==row['sha256'] and row['bytes']<100*(1<<20)
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archive_root_controller',p);ctl=importlib.util.module_from_spec(sp);sys.modules[sp.name]=ctl;sp.loader.exec_module(ctl)
with ctl.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';assert h(state)=='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa'
 mapping=[]
 for row in manifest['files']+[dict(path=PRIVATE+'/delivery_manifest.json',sha256=h(R/PRIVATE/'delivery_manifest.json'),bytes=(R/PRIVATE/'delivery_manifest.json').stat().st_size)]:
  rel=Path(row['path']).relative_to(PRIVATE).as_posix();dst=R/E/rel;assert not dst.exists() and '..' not in Path(rel).parts
  dst.parent.mkdir(parents=True,exist_ok=True)
  with (R/row['path']).open('rb') as src,dst.open('xb') as out:shutil.copyfileobj(src,out,1024*1024)
  assert h(dst)==row['sha256'];mapping.append(dict(source=row['path'],path=str(dst.relative_to(R)),sha256=row['sha256'],bytes=row['bytes']))
 mapref=save(B+'/Goal_archive_source_mapping.json',dict(kind='exact_original_bytes_publication_mapping',files=mapping))
# Independent root archive stream reconstruction, separate from author verifier.
seen=set();raw_total=0;partreports=[]
for part in arc['parts']:
 p=R/E/part['path'];assert h(p)==part['sha256'] and p.stat().st_size==part['bytes']<90*(1<<20)
 members=[inv['members'][i] for i in part['member_indices']];i=0
 with tarfile.open(p,mode='r|gz') as tf:
  for entry in tf:
   assert i<len(members);m=members[i];i+=1
   assert entry.name==m['archive_path'] and entry.isfile() and not entry.issym() and not entry.islnk()
   q=PurePosixPath(entry.name);assert not q.is_absolute() and '..' not in q.parts and str(q)==entry.name
   assert entry.name not in seen and entry.size==m['bytes'];seen.add(entry.name)
   f=tf.extractfile(entry);dh=hashlib.sha256();size=0
   for data in iter(lambda:f.read(1024*1024),b''):size+=len(data);dh.update(data)
   assert size==m['bytes'] and dh.hexdigest()==m['sha256'];raw_total+=size
 assert i==part['member_count']==len(members);partreports.append(dict(path=part['path'],sha256=part['sha256'],members=i))
assert len(seen)==35076 and raw_total==1680131983 and len(partreports)==24
assert sorted(i for p in arc['parts'] for i in p['member_indices'])==list(range(35076))
with ctl.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert h(state)=='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa'
 ref=save(B+'/Goal_archive_root_verification.json',dict(schema='formal_main_v2',kind='independent_root_archive_stream_reconstruction',
 status='passed',source_mapping=mapref,archive_manifest=dict(path=E+'/archive_manifest.json',sha256=h(R/E/'archive_manifest.json')),
 root_raw_scientific_review=dict(path=B+'/Goal_terminal_review.json',sha256=h(R/B/'Goal_terminal_review.json')),
 exact_scientific_blob_set_equal=True,verified_blobs=35062,verified_members=len(seen),verified_raw_bytes=raw_total,verified_volumes=partreports,
 compressed_bytes=sum(p['bytes'] for p in arc['parts']),weights_copied=False,sealed_values_read=False,extraction_performed=False,
 scientific_acceptance_by_archive=False,state_unchanged=True))
print(json.dumps(ref))

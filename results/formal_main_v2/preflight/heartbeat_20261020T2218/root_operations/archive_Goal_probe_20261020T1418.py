from pathlib import Path,PurePosixPath
import json,hashlib,tarfile,gzip,io,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
BASE=R/'.local/goal_t0_probe_candidate_20261020T1418'
E='results/formal_main_v2/engineering/supervision_delivery_20261020T1418/Goal_t0_probe_candidate'
B='results/formal_main_v2/preflight/heartbeat_20261020T2218'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
manifest=BASE/'delivery_manifest.json'
assert h(manifest)=='763262a0a04e5e2feb89271fef7acafd3f150c66d4f5918e9e3e707499cdfc31'
m=json.loads(manifest.read_bytes());assert m['GPU_jobs_submitted']==0 and m['real_GPU_acceptance'] is False and m['file_count']==624
rows=m['files']+[dict(relative=manifest.name,path=str(manifest),sha256=h(manifest),bytes=manifest.stat().st_size)]
binary=[];ordinary=[]
for row in rows:
 rel=row['relative'];q=PurePosixPath(rel)
 assert not q.is_absolute() and '..' not in q.parts and '\\' not in rel
 p=BASE/rel;assert str(p)==row['path'] and not p.is_symlink() and h(p)==row['sha256'] and p.stat().st_size==row['bytes']
 if p.suffix=='.npz':
  assert rel.startswith('cpu_fixture/') and '/arrays/' in rel
  binary.append(row)
 else:
  assert p.suffix in ('.py','.json','.jsonl','.md','.slurm','.log')
  ordinary.append(row)
assert len(binary)==599 and len(ordinary)==26
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w',format=tarfile.USTAR_FORMAT) as tf:
 for row in sorted(binary,key=lambda x:x['relative']):
  raw=(BASE/row['relative']).read_bytes();info=tarfile.TarInfo(row['relative']);info.size=len(raw);info.mtime=0;info.mode=0o600
  tf.addfile(info,io.BytesIO(raw))
archive=gzip.compress(buf.getvalue(),compresslevel=9,mtime=0)
with tarfile.open(fileobj=io.BytesIO(gzip.decompress(archive)),mode='r:') as tf:
 members=tf.getmembers();assert len(members)==len(binary)
 by={x['relative']:x for x in binary};assert set(tf.getnames())==set(by)
 for member in members:
  assert member.isfile() and not member.issym() and not member.islnk()
  raw=tf.extractfile(member).read();row=by[member.name];assert len(raw)==row['bytes'] and digest(raw)==row['sha256']
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('goalprobearchive1418ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json');copies=[]
 for row in ordinary:
  p=R/E/row['relative'];p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write((BASE/row['relative']).read_bytes())
  copies.append(dict(source=dict(path=str(Path(row['path']).relative_to(R)),sha256=row['sha256'],bytes=row['bytes']),archive=dict(path=p.relative_to(R).as_posix(),sha256=h(p))))
 ar=R/E/'CPU_synthetic_arrays.tar.gz'
 with ar.open('xb') as f:f.write(archive)
 out=R/B/'Goal_t0_probe_candidate_delivery.json'
 record=dict(status='unreviewed_candidate_and_CPU_evidence_preserved_no_GPU_no_submission',copies=copies,
  binary_fixtures_archive=dict(path=ar.relative_to(R).as_posix(),sha256=h(ar),bytes=len(archive),format='gzip mtime0 USTAR sorted regular files only',members=binary,member_count=599,all_members_restored_in_memory_and_SHA_verified=True),
  original_complete_manifest_sha256=h(manifest),real_GPU_acceptance=False,scientific_HOLD_unchanged=True,new_GPU_jobs=0,state_unchanged=True)
 with out.open('x') as f:json.dump(record,f,sort_keys=True,indent=2);f.write('\n')
 assert h(R/'results/experiment_supervisor/state.json')==before
 print(json.dumps(dict(receipt=dict(path=out.relative_to(R).as_posix(),sha256=h(out)),ordinary=len(ordinary),lossless_CPU_fixture_count=599,archive_bytes=len(archive),new_GPU=0)))

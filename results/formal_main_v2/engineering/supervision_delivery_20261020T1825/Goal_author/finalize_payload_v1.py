from pathlib import Path
import gzip,hashlib,json,tarfile,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_prefix58_repair_20261020T1825';start=time.process_time();A=D/'CPU_arrays_delivery';A.mkdir(exist_ok=False)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in D.rglob('*.bin') if p.is_file());assert len(files)==48
members=[]
for p in files:
 assert p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]);name=p.relative_to(D).as_posix();assert '..' not in Path(name).parts
 members.append(dict(path=name,source=str(p.relative_to(R)),sha256=h(p),bytes=p.stat().st_size,synthetic_CPU_only=True))
archive=A/'synthetic_CPU_arrays.tar.gz'
with archive.open('xb') as f:
 with gzip.GzipFile(filename='',mode='wb',fileobj=f,mtime=0) as z:
  with tarfile.open(mode='w',fileobj=z,format=tarfile.PAX_FORMAT) as tar:
   for item in members:
    p=R/item['source'];info=tarfile.TarInfo(item['path']);info.size=item['bytes'];info.mtime=0;info.uid=info.gid=0;info.uname=info.gname='';info.mode=0o644
    with p.open('rb') as src:tar.addfile(info,src)
with tarfile.open(archive,'r:gz') as tar:
 actual=tar.getmembers();assert [x.name for x in actual]==[x['path'] for x in members]
 for t,item in zip(actual,members):
  assert t.isfile() and t.size==item['bytes'];f=tar.extractfile(t);hh=hashlib.sha256();length=0
  for block in iter(lambda:f.read(1<<20),b''):hh.update(block);length+=len(block)
  assert length==item['bytes'] and hh.hexdigest()==item['sha256'] and h(R/item['source'])==item['sha256']
report=dict(schema='formal_main_v2',kind='synthetic_CPU_arrays_lossless_archive',archive=dict(path=str(archive.relative_to(R)),sha256=h(archive),bytes=archive.stat().st_size),members=members,member_count=len(members),uncompressed_bytes=sum(x['bytes'] for x in members),streaming_member_SHA_and_size_verified=True,originals_preserved=True,GPU_calls=0,scientific_trials=0,CPU_seconds=time.process_time()-start)
(A/'member_manifest.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(archive=report['archive'],member_manifest_sha256=h(A/'member_manifest.json'),CPU_seconds=report['CPU_seconds'])))

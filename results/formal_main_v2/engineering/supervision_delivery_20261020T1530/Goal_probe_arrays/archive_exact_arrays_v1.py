"""Lossless archive of exactly288 already-used development NPZ, private author output only."""
from pathlib import Path,PurePosixPath
import gzip,hashlib,json,tarfile,time
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/goal_probe_terminal_20261020T1530/arrays_delivery';BASE=P/'results/formal_main_v2/engineering/goal_t0_probe_20261020T1418/attempt01'
SOURCE=R/'.local/goal_probe_terminal_20261020T1530/npz_manifest.json';PIN='ab0deed3e6a564302aa1bd08c0615b78b1f762ce96821cc07b6938f7e61b0161'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def raw(x):return (json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
def write(name,b):
 with (D/name).open('xb') as f:f.write(b)
def require(v,m):
 if not v:raise ValueError(m)
class StreamHash:
 def __init__(self,f):self.f=f;self.h=hashlib.sha256();self.n=0
 def read(self,n=-1):
  b=self.f.read(n);self.h.update(b);self.n+=len(b);return b
start=time.perf_counter();cpu=time.process_time();require(sha(SOURCE)==PIN,'sealed input manifest SHA')
s=json.loads(SOURCE.read_bytes());require(s['count']==288 and s['total_bytes']==43327608,'exact registered count/bytes')
write('source_npz_manifest.json',SOURCE.read_bytes());members=[];names=set()
for row in sorted(s['files'],key=lambda x:x['source']):
 p=Path(row['source']);require(p.is_absolute() and p.resolve()==p and p.is_relative_to(BASE/'arrays'),'canonical allowed current development array path')
 for part in [p,*p.parents]:
  if part==P:break
  require(not part.is_symlink(),'symlink refused')
 rel=p.relative_to(BASE).as_posix();q=PurePosixPath(rel)
 require(not q.is_absolute() and '..' not in q.parts and q.parts[0]=='arrays' and len(q.parts)==2 and p.suffix=='.npz','only arrays relative members')
 require(rel not in names,'duplicate member');names.add(rel)
 require(p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'original source changed')
 members.append(dict(name=rel,source=str(p),bytes=row['bytes'],sha256=row['sha256'],query_label=row['query_label'],phase=row['phase']))
require(len(members)==288 and sum(x['bytes'] for x in members)==43327608,'manifest exact aggregate')
archive=D/'goal_t0_probe_3050711_development_arrays.tar.gz'
with archive.open('xb') as fout:
 with gzip.GzipFile(fileobj=fout,mode='wb',filename='',mtime=0,compresslevel=6) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
   for row in members:
    info=tarfile.TarInfo(row['name']);info.size=row['bytes'];info.mode=0o644;info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
    with Path(row['source']).open('rb') as fin:
     stream=StreamHash(fin);tf.addfile(info,stream)
     require(stream.n==row['bytes'] and stream.h.hexdigest()==row['sha256'],'streamed source bytes differ')
require(archive.stat().st_size<100*(1<<20),'Git single archive exceeds100MiB')
expected={r['name']:r for r in members};seen=set();verification=[]
with tarfile.open(archive,mode='r|gz') as tf:
 for entry in tf:
  require(entry.isfile() and not entry.issym() and not entry.islnk(),'archive member must be regular file')
  require(entry.name in expected and entry.name not in seen,'extra/duplicate member');row=expected[entry.name];seen.add(entry.name)
  require(entry.size==row['bytes'],'member size differs')
  fin=tf.extractfile(entry);h=hashlib.sha256();n=0
  while True:
   b=fin.read(1<<20)
   if not b:break
   n+=len(b);h.update(b)
  require(n==row['bytes'] and h.hexdigest()==row['sha256'],'lossless stream extraction mismatch')
  verification.append(dict(name=entry.name,bytes=n,sha256=h.hexdigest(),matches_original=True))
require(seen==set(expected),'missing archived member');require(sha(SOURCE)==PIN,'source manifest mutated')
for row in members:require(sha(row['source'])==row['sha256'] and Path(row['source']).stat().st_size==row['bytes'],'original NPZ not preserved')
write('member_manifest.json',raw(dict(schema='formal_main_v2',kind='lossless_current_development_array_members',job_id='3050711',source_manifest=dict(path=str(SOURCE),sha256=PIN),member_count=288,total_uncompressed_bytes=43327608,member_names='arrays/<original_npz_basename>',files=members)))
write('lossless_verification.json',raw(dict(status='all288_members_stream_reconstructed_exact_original_bytes',members=verification,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,member_count=288,total_uncompressed_bytes=43327608,no_extra_members=True,source_NPZ_unchanged=True,no_extract_to_filesystem=True,weights_included=False,sealed_values_included=False)))
write('README.md',('非权重开发观测完整交付。tar.gz只含288个arrays/相对路径NPZ，单文件小于100MiB，流式解包后每个原SHA和长度均通过。原NPZ保留P，未修改任何JSONL归档器或绕过断言。此私有包可由root精确复制并提交GitHub，作者未改state/docs/Git、未提交GPU。原Goal200科学HOLD不变；归档不增加科学试验。\n').encode())
report=dict(status='passed_private_lossless_array_archive_not_published',created_utc=datetime.now(timezone.utc).isoformat(),source_manifest_sha256=PIN,archive=dict(path=str(archive.relative_to(R)),sha256=sha(archive),bytes=archive.stat().st_size),members=288,total_uncompressed_bytes=43327608,CPU_process_seconds=time.process_time()-cpu,CPU_wall_seconds=time.perf_counter()-start,new_GPU_jobs=0,canonical_mutations=False,scientific_release=False,all_original_NPZ_retained=True,existing_JSONL_archiver_unchanged=True)
write('archive_report.json',raw(report))
files=[dict(path=str(p.relative_to(R)),relative_path=str(p.relative_to(D)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(D.iterdir()) if p.is_file()]
write('delivery_manifest.json',raw(dict(status='sealed_lossless_arrays_delivery_candidate',files=files,file_count=len(files),total_bytes=sum(x['bytes'] for x in files),new_GPU_jobs=0,nonweight_only=True,scientific_release=False,root_only_copy_and_Git=True)))
print(json.dumps(dict(status=report['status'],manifest=dict(path=str((D/'delivery_manifest.json').relative_to(R)),sha256=sha(D/'delivery_manifest.json')),archive=report['archive'],CPU_process_seconds=report['CPU_process_seconds'],CPU_wall_seconds=report['CPU_wall_seconds'],members=288),ensure_ascii=False))

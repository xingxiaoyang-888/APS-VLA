from pathlib import Path
import json,hashlib,tarfile,io
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent;A=R/'.local/goal_full200_author_20261021T0110'
def sh(b):return hashlib.sha256(b).hexdigest()
m=json.loads((A/'delivery_manifest.json').read_bytes());assert sh((A/'delivery_manifest.json').read_bytes())=='56c590f04b514de9bd3a4dcde0fcba93aa7dafe7f739f651c1ee97a1e99b0f53'
for x in m['files']:
 p=A/x['path'];assert p.is_relative_to(A) and not p.is_symlink();b=p.read_bytes();assert sh(b)==x['sha256'] and len(b)==x['bytes']
a=json.loads((A/'author_report.json').read_bytes());count=0;archives=[]
for x in a['archives']:
 ix=json.loads((A/x['members']['path']).read_bytes());assert len(ix['files'])==ix['file_count']
 with tarfile.open(A/x['archive']['path'],'r:gz') as tf:
  rows=tf.getmembers();assert len(rows)==len(ix['files'])
  for row,expected in zip(rows,ix['files']):
   assert row.isfile() and not row.issym() and not row.islnk() and row.name==expected['path'];data=tf.extractfile(row).read();assert len(data)==expected['bytes'] and sh(data)==expected['sha256'];count+=1
   direct=A/Path(x['archive']['path']).name.removesuffix('.tar.gz')/row.name
   assert direct.is_file() and sh(direct.read_bytes())==expected['sha256']
 archives.append({'path':x['archive']['path'],'members':len(rows)})
assert count==2282
proof={'status':'passed_exact_author_and_direct_CPU_raw_bytes','author_manifest_sha256':sh((A/'delivery_manifest.json').read_bytes()),'author_file_count':len(m['files']),'CPU_archived_and_direct_member_count':count,'archives':archives,'extraction_performed':False,'new_GPU_jobs':[]}
p=D/'v1_archive_and_input_verification.json'
with p.open('x') as f:json.dump(proof,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'path':str(p.relative_to(R)),'sha256':sh(p.read_bytes())}))

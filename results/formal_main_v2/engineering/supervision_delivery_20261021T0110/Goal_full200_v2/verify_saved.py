"""Read-only v2 delivery archive verification, no execution/retry/admission."""
from pathlib import Path
import hashlib,json,tarfile
D=Path(__file__).parent
def sha(b):return hashlib.sha256(b).hexdigest()
m=json.loads((D/'delivery_manifest.json').read_bytes());count=0
for row in m['files']:
 p=D/row['path'];assert p.is_file() and not p.is_symlink()
 b=p.read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256'];count+=1
for bundle in m['archives']:
 members=json.loads((D/bundle['members']['path']).read_bytes())['files']
 with tarfile.open(D/bundle['archive']['path'],'r:gz') as t:
  actual=t.getmembers();assert all(a.isfile() for a in actual) and len(actual)==len(members)
  wanted={x['path']:x for x in members};assert set(wanted)=={a.name for a in actual}
  for a in actual:
   b=t.extractfile(a).read();row=wanted[a.name];assert len(b)==row['bytes'] and sha(b)==row['sha256']
print(json.dumps({'status':'passed_read_only_v2_delivery_byte_verification','files':count,'archive_members':sum(a['file_count'] for a in m['archives']),'production_admission':False,'GPU_submissions':0}))

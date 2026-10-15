"""Copy only explicit non-weight artifacts from this registered round."""
from pathlib import Path
from collections import defaultdict
import argparse, hashlib, json, shlex, subprocess

p = argparse.ArgumentParser()
p.add_argument('stage', choices=['all','17','23','41','acceptance','profile_panel','profiling'])
a = p.parse_args()
root = Path('F:/CTI-VLA')
relative = 'results/g1_future_long_k64_v1' + ('' if a.stage == 'all' else '/' + ('seed'+a.stage if a.stage.isdigit() else a.stage))
remote_root = '/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/' + relative
remote_code = '''from pathlib import Path
import json,hashlib
r=Path(REMOTE_ROOT)
out=[]
for p in sorted(r.rglob('*')):
 if p.is_file() and p.suffix in ('.json','.jsonl','.txt','.md','.npz','.out','.err'):
  out.append({'path':p.relative_to(r).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
print(json.dumps(out))
'''.replace('REMOTE_ROOT', repr(remote_root))
manifest = json.loads(subprocess.check_output(['ssh','-o','BatchMode=yes','tongji-cvpr','/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -c '+shlex.quote(remote_code)],text=True))
grouped = defaultdict(list)
for row in manifest:
    rel = Path(row['path'])
    assert not rel.is_absolute() and '..' not in rel.parts
    grouped[rel.parent.as_posix()].append(row)
for parent, rows in grouped.items():
    target = root / relative / parent
    target.mkdir(parents=True, exist_ok=True)
    sources = ['tongji-cvpr:'+remote_root+'/'+x['path'] for x in rows]
    subprocess.run(['scp','-q','-o','BatchMode=yes']+sources+[str(target)],check=True)
    for row in rows:
        local = root / relative / row['path']
        assert local.stat().st_size == row['bytes'] and hashlib.sha256(local.read_bytes()).hexdigest() == row['sha256'], row['path']
(root/relative/'download_receipt.json').write_text(json.dumps({'weights_copied':False,'files':manifest},indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'scope':a.stage,'nonweight_files':len(manifest),'bytes':sum(x['bytes'] for x in manifest),'all_SHA_match':True}))

from pathlib import Path
import json,hashlib,os
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=D/'independent_stage_precheck.json'
assert h(report)=='1e6df258495d98b54e8d2dc7abb6f1f40f11bac0f3f027140615e6d34e4fcfd0'
v=json.loads(report.read_bytes());assert v['status']=='passed_git_stage_precheck' and v['blockers']==[] and not v['actual_stage_executed']
for rel,pin in [('.local/stage_delivery_20261021T0334_v3.py','39eb510bf1bd023efc817e9936074e6c81f6833480463ffe20fdff039abffc51'),('.local/stage_delivery_20261021T0334_v4.py','4b05a503efab9e57bc8e8b5747dc12fa3474a4d14aade6e8dd61c3a1d52db048')]:
 p=R/rel;assert h(p)==pin
 with (D/p.name).open('xb') as f:f.write(p.read_bytes())
p=R/'results/formal_main_v2/control_transport/git_stage_precheck_independent_20261021T0334.jsonl';data=p.read_bytes();rows=[json.loads(x) for x in data.splitlines()]
assert rows[-1]['event']=='control_end' and rows[-1]['returncode']==0 and rows[-1]['source173_and_entrypoint_unchanged']
with (D/'audit_transport.jsonl').open('xb') as f:f.write(data)
files=[]
for p in sorted(D.rglob('*')):
 assert not p.is_symlink()
 if p.is_file():
  assert p.name!='delivery_manifest.json';files.append(dict(path=p.relative_to(D).as_posix(),bytes=p.stat().st_size,sha256=h(p)))
v=dict(schema='formal_main_v2',kind='Git_stage_precheck_independent_delivery',status='passed_git_stage_precheck',source_root=str(D),file_count=len(files),files=files,review=dict(path='independent_stage_precheck.json',sha256=h(report)),actual_staging=False,canonical_state_Git_modified=False,new_Slurm_queries=0,new_GPU_jobs=0)
p=D/'delivery_manifest.json'
with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps(dict(manifest_sha256=h(p),report_sha256=h(report),files=len(files),bytes=sum(x['bytes'] for x in files))))

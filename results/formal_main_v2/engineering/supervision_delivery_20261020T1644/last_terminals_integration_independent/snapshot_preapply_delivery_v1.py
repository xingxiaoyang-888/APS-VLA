from pathlib import Path
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/last_terminal_integration_independent_20261020T1644'
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,b):
 assert p.is_relative_to(D) and not p.is_symlink()
 if p.exists():assert p.read_bytes()==b
 else:
  with p.open('xb') as f:f.write(b)
transport=R/'results/formal_main_v2/control_transport/last_terminal_integration_independent_v1_20261020T1644.jsonl'
write(D/'preapply_transport.jsonl',transport.read_bytes())
report=D/'preapply_review.json';assert sha(report)=='df89bc8aabb9ec3805276d7dd0a361fcf2ea7e62c158df6a3187ea3c8ce8697f'
files=[]
for p in sorted(D.rglob('*')):
 if p.is_file() and p.name not in ('preapply_delivery_manifest.json',):
  assert not p.is_symlink();files.append(dict(source=p.relative_to(R).as_posix(),path=p.relative_to(D).as_posix(),sha256=sha(p),bytes=p.stat().st_size))
out=D/'preapply_delivery_manifest.json';write(out,enc(dict(schema='formal_main_v2',kind='independent_preapply_audit_snapshot',status='passed_preview_only',files=files,files_count=len(files),total_bytes=sum(x['bytes'] for x in files),preapply_review=dict(source=report.relative_to(R).as_posix(),path=report.name,sha256=sha(report)),pending='Independent actual apply postcheck; this snapshot manifest is not final directory seal.',production_state_written=False,GPU_calls=0,Git_or_Slurm_calls=0)))
print(json.dumps(dict(path=out.relative_to(R).as_posix(),sha256=sha(out),files=len(files),bytes=sum(x['bytes'] for x in files))))

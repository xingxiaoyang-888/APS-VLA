#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_bounded_diagnostic_20261020T2358'
def sha(b):return hashlib.sha256(b).hexdigest()
assert Path(__file__).resolve().parent==D
assert not (D/'delivery_manifest.json').exists()
for name in ['goal_bounded_diagnostic_20261020T2358_attempt01.jsonl','goal_bounded_diagnostic_20261020T2358_specification01.jsonl']:
 p=R/'results/formal_main_v2/control_transport'/name
 b=p.read_bytes()
 q=D/name
 assert not q.exists()
 q.write_bytes(b)
files={}
for p in sorted(D.iterdir()):
 assert p.is_file() and not p.is_symlink() and p.name!='delivery_manifest.json'
 b=p.read_bytes();files[p.name]={'sha256':sha(b),'bytes':len(b)}
m={'schema':'formal_main_v2','kind':'Goal_fixed_bounded_CPU_diagnostic_and_prospective_design',
 'status':'author_CPU_checks_passed_independent_review_pending','files':files,'file_count':len(files),
 'scientific_trials_added':0,'GPU_seconds_added':0,'new_GPU_jobs':0,'old200_HOLD':True,'new_Goal_science_HOLD':True,
 'production_ready':False,'final_release':False,'root_relative':D.relative_to(R).as_posix()}
p=D/'delivery_manifest.json';p.write_bytes(json.dumps(m,ensure_ascii=False,sort_keys=True,indent=2).encode()+b'\n')
for name in ['boundary_evidence.json','source_timing_and_hash_contract.json','prospective_full200_specification.json','execution_report.json','delivery_manifest.json']:
 p=D/name;print(json.dumps({'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size},ensure_ascii=False))
print('file_count',len(files))

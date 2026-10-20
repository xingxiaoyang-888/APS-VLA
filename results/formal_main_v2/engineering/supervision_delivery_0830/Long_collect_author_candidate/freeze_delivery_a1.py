"""Freeze author-candidate delivery bytes, retaining all earlier CPU failures."""
from pathlib import Path
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/long_collection_prepare_0830'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=D/'a2/candidate_review.json'
assert sha(report)=='f7bd2f0641d15f8fe63858ca5fa84c620195bd71a75b0c6f45efb68f684af974'
v=json.loads(report.read_bytes());assert v['review_role']=='author_candidate_not_independent' and not v['submission_authorized'] and v['new_GPU_seconds']==0
sources=[p for p in sorted(D.rglob('*')) if p.is_file()]
assert not(D/'delivery_files.json').exists()
rows=[]
for p in sources:
 assert p.resolve()==p and p.suffix not in ('.pt','.pth','.safetensors','.pkl','.ckpt')
 rows.append(dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
for rel in ['results/formal_main_v2/control_transport/long_collection_prepare_0830_input_a2.jsonl','results/formal_main_v2/control_transport/long_collection_prepare_0830_plan_a1.jsonl','results/formal_main_v2/control_transport/long_collection_prepare_0830_fresh_collect_a1.jsonl','results/formal_main_v2/control_transport/long_collection_prepare_0830_plan_a2.jsonl']:
 p=R/rel;rows.append(dict(path=rel,bytes=p.stat().st_size,sha256=sha(p)))
out=dict(schema='formal_main_v2',kind='Long_collect_author_candidate_delivery',status='frozen_author_CPU_candidate_pending_root_and_independent_readiness',private_root=D.relative_to(R).as_posix(),review=dict(path=report.relative_to(R).as_posix(),sha256=sha(report)),author_not_independent=True,production_code_changed=False,GPU_jobs_submitted=0,failed_CPU_attempts_retained=['prepare_plan_a1 fresh-process guard'],unexecuted_source_corrections_retained=['prepare_input_a1 environment key corrected to a2 before execution'],files=rows,file_count=len(rows),final_values_read=False,weights_deserialized=False,submission_authorized=False)
p=D/'delivery_files.json'
with p.open('x') as f:json.dump(out,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
print(json.dumps(dict(path=p.relative_to(R).as_posix(),sha256=sha(p),bytes=p.stat().st_size,file_count=len(rows))))

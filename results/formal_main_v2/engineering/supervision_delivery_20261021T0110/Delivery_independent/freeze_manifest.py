from pathlib import Path
import argparse,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--report',required=True);ap.add_argument('--report-sha256',required=True);a=ap.parse_args()
p=D/a.report
assert p.resolve()==p and p.is_relative_to(D) and p.is_file() and h(p)==a.report_sha256
r=json.loads(p.read_bytes())
assert r['status']=='passed_final_delivery_review' and not r['blockers'] and r['source173_verified'] and r['final_sealed']
assert h(R/'results/experiment_supervisor/state.json')==r['state_sha256']
out=D/'delivery_manifest.json';assert not out.exists()
files=[]
for q in sorted(D.rglob('*')):
 if not q.is_file():continue
 assert q.resolve()==q and not any(x.is_symlink() for x in (q,*q.parents))
 assert q.suffix in ('.py','.json','.md','.txt','.jsonl')
 files.append(dict(path=q.relative_to(D).as_posix(),sha256=h(q),bytes=q.stat().st_size))
assert len(files)==len({v['path'] for v in files}) and a.report in {v['path'] for v in files}
m=dict(schema='formal_main_v2',kind='root_final_delivery_independent_manifest',status='frozen_final_delivery_review',reviewed_by='independent',reviewer_agent='/root/goal_cpu_gate_2054',source_root=str(D),files=files,file_count=len(files),independent_review=dict(path=p.relative_to(R).as_posix(),sha256=a.report_sha256,bytes=p.stat().st_size),state_sha256=r['state_sha256'],scope=r['scope'],check_count=len(r['checks']),inherited_preliminary_check_count=r['inherited_preliminary_checks'],retained_prior_failed_auditor_encoding_assertion=True,own_Goal_algorithm_independently_reviewed_here=False,source173_verified=True,final_sealed=True,actual_Git_commit_or_push_verified=False,new_live_Slurm_queries=0,new_GPU_submissions=0,state_writes=0,Git_operations=0,P_writes=0)
with out.open('x') as f:json.dump(m,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
print(json.dumps(dict(status=m['status'],manifest=out.relative_to(R).as_posix(),sha256=h(out),file_count=len(files),review_sha256=a.report_sha256,checks=m['check_count'])))

from pathlib import Path
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=D/'independent_review.json';assert h(p)=='af0ed2e56d4dc477f73d604fac1174dbb5a2b5669447ae5c80a6c46aae8e8122'
v=json.loads(p.read_bytes());assert v['status']=='passed_actual_publication_original_ACK_single_release' and v['blockers']==[]
t=D/'transport';t.mkdir();n='goal_actual_facts_independent_20261021T0110.jsonl';original=R/'results/formal_main_v2/control_transport'/n
logs=[json.loads(x) for x in original.read_text().splitlines() if x];assert logs[-1].get('returncode',logs[-1].get('exit_code'))==0
with (t/n).open('xb') as f:f.write(original.read_bytes())
files=[]
for q in sorted(D.rglob('*')):
 assert not q.is_symlink()
 if q.is_file():files.append(dict(path=q.relative_to(D).as_posix(),bytes=q.stat().st_size,sha256=h(q)))
out=D/'Goal_actual_manifest.json'
with out.open('x') as f:json.dump(dict(schema='formal_main_v2',kind='Goal_full200_actual_facts_independent_delivery_manifest',source_root=D.relative_to(R).as_posix(),files=files,file_count=len(files),review=dict(path='independent_review.json',sha256=h(p)),new_Slurm_queries=0,new_GPU_submissions_by_auditor=0,scientific_trials_accepted=0),f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(manifest=str(out.relative_to(R)),sha256=h(out),file_count=len(files),review_sha256=h(p))))

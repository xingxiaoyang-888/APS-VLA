from pathlib import Path
import json,hashlib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/Spatial64seed23_terminal_1032'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=sha(p),bytes=p.stat().st_size)
report=json.loads((D/'independent_review.json').read_text());assert report['status']=='passed_complete_training_only' and report['completed_by_arm']=={'A':5000,'B':5000} and report['new_reviewed_arm_updates']==7000 and report['final_release_authorized'] is False
logs=[]
for p in sorted((R/'results/formal_main_v2/control_transport').glob('Spatial64seed23_terminal_1032_a*.jsonl')):
 v=[json.loads(x) for x in p.read_text().splitlines()];assert v[-1]['event']=='control_end' and v[-1]['source173_and_entrypoint_unchanged'] is True;logs.append({**ref(p),'returncode':v[-1]['returncode'],'wall_seconds':(v[-1]['time_ns']-v[0]['time_ns'])/1e9})
assert logs and logs[-1]['returncode']==0
m=dict(schema='formal_main_v2',kind='Spatial64_seed23_independent_terminal_delivery',files=[ref(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json'],independent_review=ref(D/'independent_review.json'),transport_logs=logs,root_operations_candidates_author_executed=False,weights_copied_or_deserialized=False,final_release_authorized=False)
p=D/'delivery_manifest.json'
with p.open('x') as f:json.dump(m,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(manifest=ref(p),report=ref(D/'independent_review.json'),transport=logs)))

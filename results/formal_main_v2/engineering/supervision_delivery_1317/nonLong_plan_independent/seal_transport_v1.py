from pathlib import Path
import sys,json,hashlib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/nonLong_development_plans_independent_1317'
def ref(p):return dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def dump(name,obj):
 p=D/name
 with p.open('x') as f:json.dump(obj,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
post_sha,prior_sha=sys.argv[1:3]
assert ref(D/'post_readiness/post_readiness_independent_review.json')['sha256']==post_sha
assert ref(D/'final_manifest.json')['sha256']==prior_sha
rows=[]
for suffix in ['inputs_a1','plans_a1','post_a1']:
 p=R/f'results/formal_main_v2/control_transport/nonLong_development_independent_1317_{suffix}.jsonl';v=[json.loads(x) for x in p.read_text().splitlines()]
 assert v[0]['event']=='control_start' and v[-1]['event']=='control_end' and v[-1]['returncode']==0 and v[-1]['source173_and_entrypoint_unchanged'] is True
 rows.append(dict(**ref(p),returncode=0,wall_seconds=(v[-1]['time_ns']-v[0]['time_ns'])/1e9))
transport=dump('transport_delivery.json',dict(schema='formal_main_v2',kind='independent_nonLong1317_transport_delivery',closed_logs=rows,total_recorded_wall_seconds=sum(x['wall_seconds'] for x in rows),new_GPU_seconds=0,experimental_failures_added=False,all173_unchanged=True))
files=[ref(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='final_manifest_v2.json']
m=dump('final_manifest_v2.json',dict(schema='formal_main_v2',kind='nonLong_development_plan_and_actual_P_verification_delivery',reviewer='/root/goal256_s41_terminal_0333',files=files,post_readiness_review=ref(D/'post_readiness/post_readiness_independent_review.json'),prior_final_manifest=ref(D/'final_manifest.json'),transport_delivery=transport,production_modified=False,new_GPU_seconds=0,new_trials=0,final_release=False,submission_authorized_by_this_audit=False))
print(json.dumps(dict(manifest=m,post_review=ref(D/'post_readiness/post_readiness_independent_review.json'),transport=transport,recorded_CPU_command_wall_seconds=sum(x['wall_seconds'] for x in rows))))

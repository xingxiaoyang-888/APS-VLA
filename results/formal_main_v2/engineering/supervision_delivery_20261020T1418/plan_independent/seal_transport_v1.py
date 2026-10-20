from pathlib import Path
import sys,json,hashlib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/devplans_independent_20261020T1418'
def ref(p):return dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def dump(name,obj):
 p=D/name
 with p.open('x') as f:json.dump(obj,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
post_sha,prior_sha=sys.argv[1:3]
assert ref(D/'post_readiness/post_readiness_independent_review.json')['sha256']==post_sha
assert ref(D/'final_manifest.json')['sha256']==prior_sha
rows=[]
for suffix,expected_rc in [('inputs_v2',1),('inputs_v3',0),('plans_v2',0),('post_v2',0)]:
 p=R/f'results/formal_main_v2/control_transport/independent_devplans_20261020T1418_{suffix}.jsonl';v=[json.loads(x) for x in p.read_text().splitlines()]
 assert v[0]['event']=='control_start' and v[-1]['event']=='control_end' and v[-1]['returncode']==expected_rc and v[-1]['source173_and_entrypoint_unchanged'] is True
 target=D/'closed_transport'/p.name;target.parent.mkdir(exist_ok=True)
 with target.open('xb') as f:f.write(p.read_bytes())
 assert ref(target)['sha256']==ref(p)['sha256']
 rows.append(dict(archive=ref(target),**ref(p),returncode=expected_rc,wall_seconds=(v[-1]['time_ns']-v[0]['time_ns'])/1e9))
transport=dump('transport_delivery.json',dict(schema='formal_main_v2',kind='independent_devplans20261020T1418_transport_delivery',closed_logs=rows,total_recorded_wall_seconds=sum(x['wall_seconds'] for x in rows),new_GPU_seconds=0,experimental_failures_added=False,all173_unchanged=True))
files=[ref(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='final_manifest_v2.json']
m=dump('final_manifest_v2.json',dict(schema='formal_main_v2',kind='nonLong_development_plan_and_actual_P_verification_delivery',reviewer='/root/devplans_audit_20261020_1418',files=files,post_readiness_review=ref(D/'post_readiness/post_readiness_independent_review.json'),prior_final_manifest=ref(D/'final_manifest.json'),transport_delivery=transport,production_modified=False,new_GPU_seconds=0,new_trials=0,final_release=False,submission_authorized_by_this_audit=False))
print(json.dumps(dict(manifest=m,post_review=ref(D/'post_readiness/post_readiness_independent_review.json'),transport=transport,recorded_CPU_command_wall_seconds=sum(x['wall_seconds'] for x in rows))))

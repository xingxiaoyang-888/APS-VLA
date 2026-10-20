from pathlib import Path
import json,hashlib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/nonLong_development_plans_independent_1220'
def ref(p):return dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def dump(name,obj):
 p=D/name
 with p.open('x') as f:json.dump(obj,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
assert ref(D/'post_readiness/post_readiness_independent_review.json')['sha256']=='1370999c9aa66361fb41abfd0fcc72f969016d9d13f356e3148c49df4909fb9f'
assert ref(D/'final_manifest.json')['sha256']=='c0dacd99ad4f710fb287df574b445b918bae8c241c02af74ce781a44f5120d1a'
assert not (R/'results/formal_main_v2/control_transport/nonLong_development_independent_1220_post_a1.jsonl').exists()
err=dump('post_transport_rejection_a1.json',dict(kind='pre_entry_transport_rejection_record',error_type='ValueError',error='bundle SHA missing',incorrect_argument='3726e3249403e3afa1d4fd1688b0dbce540e28714ac6f721662118ddb7338d7c0288aa0bcef',required_bundle_sha256='3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149',entry_started=False,transport_log_created=False,production_modified=False,GPU_seconds=0,correction='Only command argument corrected to original reviewed bundle SHA; unchanged candidate then completed under unique post_a2 log.'))
rows=[]
for suffix,rc in [('inputs_a1',1),('inputs_a2',0),('plans_a1',1),('plans_a2',0),('post_a2',0)]:
 p=R/f'results/formal_main_v2/control_transport/nonLong_development_independent_1220_{suffix}.jsonl';v=[json.loads(x) for x in p.read_text().splitlines()]
 assert v[-1]['event']=='control_end' and v[-1]['returncode']==rc and v[-1]['source173_and_entrypoint_unchanged'] is True
 rows.append(dict(**ref(p),returncode=rc,wall_seconds=(v[-1]['time_ns']-v[0]['time_ns'])/1e9))
transport=dump('transport_delivery.json',dict(schema='formal_main_v2',kind='independent_nonLong1220_transport_delivery',closed_logs=rows,total_recorded_wall_seconds=sum(x['wall_seconds'] for x in rows),pre_entry_rejected_command=err,new_GPU_seconds=0,experimental_failures_added=False,all173_unchanged=True))
files=[ref(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='final_manifest_v2.json']
m=dump('final_manifest_v2.json',dict(schema='formal_main_v2',kind='nonLong_development_plan_and_actual_P_verification_delivery',reviewer='/root/goal256_s41_terminal_0333',files=files,post_readiness_review=ref(D/'post_readiness/post_readiness_independent_review.json'),prior_final_manifest=ref(D/'final_manifest.json'),transport_delivery=transport,production_modified=False,new_GPU_seconds=0,new_trials=0,final_release=False,submission_authorized_by_this_audit=False))
print(json.dumps(dict(manifest=m,post_review=ref(D/'post_readiness/post_readiness_independent_review.json'),transport=transport,recorded_CPU_command_wall_seconds=sum(x['wall_seconds'] for x in rows))))

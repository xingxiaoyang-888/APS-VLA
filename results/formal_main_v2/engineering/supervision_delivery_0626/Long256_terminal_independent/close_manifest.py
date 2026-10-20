from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent
JOBS={'3046779':(17,2937),'3046798':(23,3159)}
def ref(p):
 b=p.read_bytes();return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(name,v):
 p=D/name;b=json.dumps(v,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2).encode()+bytes([10])
 with p.open('xb') as f:f.write(b)
 return ref(p)
reports={};children=[];all_stored=[];panels=set()
for jid,(seed,secs) in JOBS.items():
 child=D/('job'+jid);mf=json.loads((child/'manifest.json').read_bytes())
 assert mf['status']=='frozen'
 for row in mf['files']:assert ref(R/row['path'])==row
 p=child/'independent_review.json';v=json.loads(p.read_bytes())
 assert v['status']=='passed' and v['scientific_complete'] is True and v['job_id']==jid and v['stage']=='development'
 assert v['method_ids']==[f'A256_seed{seed}',f'B256_seed{seed}'] and v['completed_trials']==v['expected_trials']==200 and v['unique_initial_states']==100
 assert v['cost']['current_GPU_seconds']==v['cost']['all_attempt_GPU_seconds']==secs and v['cost']['allocations']==1
 assert v['final_release'] is False and v['O2A_latency_verified'] is False and v['legacy_terminal_trials_reused']==0
 cp=json.loads((R/v['cross_seed_panel_identity']['path']).read_bytes());panels.add(cp['same_exact_development_panel']['sha256'])
 reports[jid]={'review':ref(p),'seed':seed,'successes':v['successes'],'per_task':v['per_task'],'per_task_B_minus_A_success_rate':v['per_task_B_minus_A_success_rate'],'paired_outcomes':v['paired_outcomes'],'B_minus_A_success_rate':v['B_minus_A_success_rate'],'GPU_seconds':secs,'action_checks':v['action_checks'],'initial_observation_token_overlap_mean':v['initial_observation_token_overlap_mean']}
 children.append(ref(child/'manifest.json'))
assert len(panels)==1
summary=save('summary.json',{'schema':'formal_main_v2','kind':'independent_Long256_two_development_jobs_summary','status':'passed','utc':datetime.now(timezone.utc).isoformat(),'jobs':reports,'completed_trials':400,'unique_initial_states':100,'same_initial_states_across_seeds':True,'sum_actual_GPU_seconds':sum(x[1] for x in JOBS.values()),'sum_actual_GPU_hours':sum(x[1] for x in JOBS.values())/3600,'budget':256,'seeds':[17,23],'seed41_included':False,'legacy_action_trials_included':0,'final_release':False,'O2A_latency_verified':False,'scientific_equivalence_or_significance_claim':False})
files=[ref(p) for p in sorted(D.rglob('*')) if p.is_file()]
manifest=save('manifest.json',{'schema':'formal_main_v2','kind':'independent_Long256_development_archive','status':'frozen','root':str(D),'files':files,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'summary':summary,'child_manifests':children,'no_weights_or_sealed_values':True})
print(json.dumps({'summary':summary,'manifest':manifest,'files':len(files),'GPU_seconds':6096,'trials':400,'unique_initial_states':100}))

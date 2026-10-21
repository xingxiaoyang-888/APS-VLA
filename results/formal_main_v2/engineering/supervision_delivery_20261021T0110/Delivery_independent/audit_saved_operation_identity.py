"""Additional saved-operation identity audit only; no live queries or Goal algorithm review."""
from pathlib import Path
import hashlib,json,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent
B='results/formal_main_v2/preflight/heartbeat_20261021T0910'
X='results/formal_main_v2/engineering/goal_full200_20261021T0110'
checks=[];refs={}
def ck(n,v):
 checks.append(dict(name=n,passed=bool(v)));assert v,n
def read(n,pin):
 p=R/n;b=p.read_bytes();ck('sha/'+n,hashlib.sha256(b).hexdigest()==pin);refs[n]=dict(sha256=pin,bytes=len(b));return json.loads(b)
s=read('results/experiment_supervisor/state.json','bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa')
before=read(B+'/final_state_before.json','2e53569c6435abd3fc9d1d9898d33938205c4ddef916938ac4b6af632202f104')
o=read(B+'/latest_actual_operation_observation.json','e74210cf407e119e1f8a838bf822194b00f1d5a26b24301145d3f499bfa3559d')
post=read(X+'/dispatch_attempt01/post_release_observation.json','88e68958535098af680ed0c8e2ee5a6fcce88d372a99c2fdcc2d8963f4507b93')
ack=read(X+'/dispatch_attempt01/sbatch_result.json','50a20e43a29ad77d8354152f052905a34d91304e446d19537b98be289424a73a')
release=read(X+'/dispatch_attempt01/release_attempt.json','e893dae69c538aa5d6ad01b37fe7fa176ed46e0aef98257d339e6aa4c36710b2')
released=read(X+'/dispatch_attempt01/release_result.json','833cb4646d4ffe597cea4efe393ca18c1c03e7a3149eb82e9f9d7bd7435ccce7')
committed=read(X+'/dispatch_attempt01/committed.json','2dc2533380c38b22f2697471e30d0c4f37b11a82bf5b2c9b0e1e82c5e945e183')
held=read(X+'/held_dispatch_record.json','47dc4866ac0cf3ae61fcbba113a27f68952412332ffc4bfbfdc116b3bf604384')
ck('actual_observation_projection_no_change',o['observation']==post['observation'] and o['lease']==post['lease'] and o['utc']==post['utc'])
ck('saved_operation_cost_capacity_exact',o['occupied']==post['derived']['occupied']==['3054717'] and o['allocated_GPU_seconds']==post['derived']['allocated_formal_GPU_seconds']==1992263 and o['registered_formal_allocations']==273)
jobs=[j for j in s['registered_jobs'] if str(j['job_id'])=='3054717']
ck('one_exact_Goal_registration',len(jobs)==1);job=jobs[0]
token='cti-goal-full200-v1:07a265e02fd283603b1ec4c7e555d75d00318e821c824f02dbf419988987dc5b'
ck('unique_original_ACK_bound',ack['returncode']==0 and ack['stdout']==job['original_sbatch_ACK']=='3054717\n' and held['job_id']==committed['job_id']=='3054717')
ck('held_original_argv_exact',ack['actual_sbatch_argv']==held['actual_sbatch_argv']==job['goal_full200_gateway']['actual_sbatch_argv']==job['downstream_gateway']['actual_sbatch_argv'])
ck('token_and_comment_exact',job['submission_token']==job['slurm_comment']==job['goal_full200_gateway']['request_token']==held['request_token']==release['submission_token']==token and '--comment='+token in ack['actual_sbatch_argv'])
ck('one_hold_one_gpu_no_requeue',all(x in ack['actual_sbatch_argv'] for x in ['--hold','--no-requeue','--gres=gpu:l40:1']) and held['new_submissions']==held['maximum_attempts']==job['maximum_attempts']==1 and not job['automatic_retry'] and not committed['automatic_retry'])
ck('release_bound_once',release['argv']==released['argv']==['scontrol','release','3054717'] and released['returncode']==0 and release['state_sha256']==held['state_after_sha256'])
ck('committed_exact_before_snapshot',committed['state_sha256']=='2e53569c6435abd3fc9d1d9898d33938205c4ddef916938ac4b6af632202f104' and committed['status']=='submitted_once_registered_then_released' and before['registered_jobs']==s['registered_jobs'])
detail=post['details']['3054717'];ck('saved_scheduler_identity',detail['Comment']==token and detail['Command']==ack['actual_sbatch_argv'][-1] and detail['JobName']==job['job_name'] and detail['Restarts']=='0' and detail['Requeue']=='0')
ck('saved_pending_is_not_actual_allocation',detail['JobState']==o['observation']['rows']['3054717']['status']=='PENDING' and o['observation']['rows']['3054717']['gpus']==0 and job['gpus']==1)
ck('single_prospective_scope_no_science',job['maximum_trials']==200 and job['maximum_control_steps']==60000 and job['maximum_policy_queries']==7600 and job['scientific_trials']==0 and not job['final_states_opened'] and not held['scientific_release'])
ck('held_capacity_includes_all_modes',held['capacity_limit_all_GPU_modes']==8 and len(held['occupied_job_ids'])<=8)
raw=o['observation']['raw_sacct']
ck('saved_raw_sacct_linked_to_original_query',any(q['argv'][0]=='sacct' and q['returncode']==0 and q['stdout']==raw for q in o['observation']['queries']))
parsed={}
for line in raw.splitlines():
 c=line.split('|');ck('raw_exact_eight_columns/'+c[0],len(c)==8 and c[0] not in parsed)
 m=re.search(r'(?:^|,)gres/gpu=(\d+)(?:,|$)',c[4]);gpus=int(m.group(1)) if m else 0
 parsed[c[0]]=dict(status=c[1].split()[0].rstrip('+'),exit_code=c[2],elapsed_seconds=int(c[3]),gpus=gpus)
formal=[j for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2'];ids=[str(j['job_id']) for j in formal]
ck('formal273_unique',len(ids)==len(set(ids))==273)
cost=0
for jid in ids:
 p=parsed[jid];row=o['observation']['rows'][jid]
 ck('raw_rebuilt_cost_fields/'+jid,all(p[k]==row[k] for k in p))
 cost+=p['gpus']*p['elapsed_seconds']
ck('raw_rebuilt_273_cost_total',cost==1992263==s['current_round_cost']['allocated_gpu_seconds'])
ck('Object_saved_terminal_not_science_admission',parsed['3054409']==dict(status='COMPLETED',exit_code='0:0',elapsed_seconds=326,gpus=1) and s['formal_main_progress']['completed_final_trials']==0)
ck('final_state_unchanged',hashlib.sha256((R/'results/experiment_supervisor/state.json').read_bytes()).hexdigest()=='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa')
value=dict(schema='formal_main_v2',status='passed_saved_operation_identity_review',reviewed_by='independent',scope='Saved exact Goal ACK/held registration/single release identity, final operation projection and raw sacct arithmetic only; not Goal runtime algorithm or new terminal acceptance.',checks=list(checks),blockers=[],state_sha256='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa',observed_utc=o['utc'],registered_formal_allocations=273,allocated_GPU_seconds=cost,Goal_original_ACK='3054717',Goal_requested_active_jobs=1,Goal_allocated_GPUs_at_observation=0,Object_3054409_completed_seconds=326,new_live_Slurm_queries=0,new_GPU_submissions=0,new_scientific_admissions=0,state_writes=0,Git_operations=0,P_writes=0,refs=refs)
out=D/'saved_operation_identity_review.json'
with out.open('x') as f:json.dump(value,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(status=value['status'],checks=len(checks),sha256=hashlib.sha256(out.read_bytes()).hexdigest())))

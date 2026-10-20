from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0653';BASE='results/formal_main_v2/engineering/goal_paired_input_gate_20261020T2156';I='.local/goal_terminal_independent_20261020T2253'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return {'path':n,'sha256':h(R/n)}
def put(n,b):
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b
 else:p.open('xb').write(b)
def save(n,x):put(n,(json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode())
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';spec=importlib.util.spec_from_file_location('goal2253int',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
for n,pin in {B+'/live_observation.json':'b16ee5b23e3ab2e4a7edea7734bbf2871e0b936b51b6800e41c20fdfc4a8feac',B+'/Goal_terminal_root_review.json':'612766294af9462d0c21edbdcb177433a0cd1f2897b1d613ab9eb674f43bbb19',I+'/terminal_review.json':'e48e5f5a0855c81280ea9cd4eb014aefe45c3b18d324836930b5a5ef1e1d4d61',I+'/archive_review.json':'3b7166d6422cbf4551fcd54a0f7d15a08e30d6b0f2de8d2d644f5578f6dd8fd5'}.items():assert h(R/n)==pin
root=rd(B+'/Goal_terminal_root_review.json');ind=rd(I+'/terminal_review.json');arc=rd(I+'/archive_review.json');obs=rd(B+'/live_observation.json');assert ind['status']=='passed_engineering_terminal_only' and arc['status']=='passed_all_raw_members_and_metadata' and not ind['blockers'] and not arc['blockers']
assert root['GPU_seconds']==ind['allocated_GPU_seconds']==840 and root['prefix_trials']==58 and root['paired_inputs']==29 and root['accepted_queries']==940 and root['executed_steps']==7302
assert ind['scientific_trials_added']==0 and ind['old_cause_identified'] is False and ind['old_failure_repaired'] is False and ind['new_Goal_science_HOLD']
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);assert before=='63c74e7e591283409a792a7597fdb9bf99d1936ff1311e123bd687a83237a51f';s=rd('results/experiment_supervisor/state.json');f=s['formal_main_progress'];old=copy.deepcopy(f);assert s['pending_submission'] is None
 j=next(j for j in s['registered_jobs'] if str(j['job_id'])=='3054127');assert j['mode']=='engineering' and j['status']=='RUNNING';o=obs['observation']['rows']['3054127'];assert o['status']=='COMPLETED' and o['exit_code']=='0:0' and o['elapsed_seconds']==840 and o['gpus']==1
 put(B+'/state_before_Goal_terminal.json',sp.read_bytes())
 for name in ['terminal_review.json','archive_review.json']:
  put(BASE+'/attempt01/reviews/independent_'+name,(R/I/name).read_bytes())
 acceptance={'schema':'formal_main_v2','kind':'root_Goal_paired_input_engineering_terminal_acceptance','status':'root_and_independent_engineering_only_accepted','job_id':'3054127','Slurm_status':'COMPLETED','Slurm_exit_code':'0:0','GPU_seconds':840,'prefix_trials':58,'paired_inputs':29,'accepted_queries':940,'executed_steps':7302,'root_review':ref(B+'/Goal_terminal_root_review.json'),'independent_review':ref(BASE+'/attempt01/reviews/independent_terminal_review.json'),'independent_archive_review':ref(BASE+'/attempt01/reviews/independent_archive_review.json'),'archive_manifest':ref(BASE+'/attempt01/observer/blob_archive_manifest.json'),'slurm_observation':ref(B+'/live_observation.json'),'old_cause_identified':False,'old_failure_repaired':False,'old200_adopted':False,'new_Goal_science_HOLD':True,'new_scientific_trials':0,'new_GPU_submissions':0,'automatic_retry':False,'final_release':False,'O2A_admitted':False}
 save(B+'/Goal_terminal_acceptance.json',acceptance);aref=ref(B+'/Goal_terminal_acceptance.json')
 for k in ['status','exit_code','elapsed_seconds','allocation','node']:j[k]=o[k]
 j['engineering_terminal_acceptance']=aref
 f['Goal_paired_input_engineering_registration'].update(status='root_and_independent_engineering_only_accepted',terminal_acceptance=aref,GPU_seconds=840,old_cause_identified=False,old_failure_repaired=False)
 s['autonomous_training_v1']['occupied_job_ids']=[]
 s['current_round_cost'].update(allocated_gpu_seconds=1985302,allocated_gpu_hours=1985302/3600,registered_jobs=270,final=True,scope='All270 registered formal allocations once, including full840 seconds of Goal3054127; no future allocation included.')
 f['parallel_execution'].update(registered_requested_active_GPU_jobs=0,actual_running_allocated_GPUs=0)
 for k in ['root_and_independent_completed_arms','root_and_independent_reviewed_arm_updates','current_action_development_trial_count','completed_development_trials','completed_final_trials','test_opened','global_release_created','completed_training_pairs']:assert f[k]==old[k]
 c.atomic_json(sp,s,before);save(B+'/Goal_terminal_state_update.json',{'status':'terminal_engineering_registered_without_scientific_admission','before':before,'after':h(sp),'acceptance':aref,'GPU_seconds_total':1985302,'GPU_seconds_newly_accounted':623,'new_scientific_trials':0,'new_GPU_submissions':0})
 print(json.dumps({'acceptance':aref,'state_sha256':h(sp),'GPU_seconds':1985302,'active_GPU':0,'Goal_science_HOLD':True}))

from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0044';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1644';D='results/formal_main_v2/execution/object256seed23_source_control_v1_20261020T1644'
AUTH_SHA='e6a6a2165c46187e42338764f16417d90e8d42dd1892d8d06f61bce6d32c5047';A={'path':D+'/submission_authorization.json','sha256':AUTH_SHA};G='results/formal_main_v2/downstream_gateway/'+AUTH_SHA
DOCS=['实验进度','完整实验计划','正式主实验规划','正式主实验阶段结论','正式自动连续训练执行登记']
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return dict(path=n,sha256=h(R/n))
def check(x):assert h(R/x['path'])==x['sha256'];return rd(x['path'])
def save(n,x):
 p=R/n;assert p.is_relative_to(R) and not any(z.is_symlink() for z in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write(chr(10))
ap=argparse.ArgumentParser();ap.add_argument('--job-id',required=True);ap.add_argument('--materials',required=True);ap.add_argument('--materials-sha256',required=True);a=ap.parse_args();assert a.job_id.isdigit();materials=check(dict(path=a.materials,sha256=a.materials_sha256));assert materials['status']=='root_reviewed_delivery_materials'
for rr in materials['archive_receipts']:check(rr)
ctrlp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(ctrlp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';sp=importlib.util.spec_from_file_location('CloseTurn1644',ctrlp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sn='results/experiment_supervisor/state.json';s=rd(sn);before=h(R/sn);f=s['formal_main_progress'];old=copy.deepcopy(s)
 assert f['root_and_independent_completed_arms']==72 and f['root_and_independent_reviewed_arm_updates']==360000 and f['current_action_development_trial_count']==5200 and f['completed_development_trials']==6412
 assert f['last_terminals_integrity_review_20261020T1644']['status']=='passed';check(f['last_terminals_integrity_review_20261020T1644']['independent_review']);check(f['last_terminals_integrity_review_20261020T1644']['root_acceptance'])
 assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created'] and s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0 and s['autonomous_training_v1']['root_submission_hold'] is None
 j=next(x for x in s['registered_jobs'] if str(x['job_id'])==a.job_id);assert j['downstream_gateway']['authorization']==A and j['suite']=='libero_object' and j['mode']=='development' and j['method_ids']==['A256_seed23','B256_seed23'] and not j['resume'] and j['prior_job_ids']==[]
 committed=rd(G+'/committed.json');assert committed['status']=='submitted_once_reconciled_after_accounting_delay' and str(committed['job']['job_id'])==a.job_id and committed['reservation_consumed'] is True
 assert s['autonomous_training_v1']['downstream_reservations_consumed'][AUTH_SHA]['job_id']==a.job_id
 for rr in [ref(D+'/post_readiness_independent_review.json'),ref(B+'/Object_runtime_readiness_root.json')]:check(rr)
 goalhandoff=rd(E+'/Goal_prefix58_candidate/handoff_summary.json');assert goalhandoff['CPU_checks_passed']==212 and not goalhandoff['real_GPU_runner_implemented'] and not goalhandoff['real_engineering_GPU_acceptance_completed']
 extra_goal=materials['Goal_independent_review'];goal_ind=check(extra_goal);assert goal_ind['status']=='completed_with_findings_not_GPU_ready'
 utc=datetime.now(timezone.utc).isoformat();seconds=s['current_round_cost']['allocated_gpu_seconds'];hours=s['current_round_cost']['allocated_gpu_hours'];assert abs(hours-seconds/3600)<1e-9
 summary=dict(schema='formal_main_v2',kind='root_heartbeat_closeout',utc=utc,status='72_training_arms800_development_accepted_Object256s23_submitted_once_Goal_held',root_and_independent_completed_arms=72,total_training_arms=72,reviewed_arm_updates=360000,newly_root_reviewed_training_jobs=['3043877','3043813','3044844'],new_training_arms_reviewed=6,new_GPU_jobs=[a.job_id],new_development_reviews_accepted=800,current_action_development_trials=5200,compatible_legacy_development_trials=600,current_compatible_development_total=5800,unique_development_initial_states=400,historical_accepted_development_trials=6412,allocated_GPU_seconds=seconds,allocated_GPU_hours=hours,cost_source='latest actual Slurm reconciliation recorded by root submission, including running allocation lower bound and all failed attempts',registered_requested_active_GPU_jobs=f['parallel_execution']['registered_requested_active_GPU_jobs'],new_job=ref('results/formal_main_v2/submissions/'+a.job_id+'.json'),invocation=ref(j['invocation']),submission=ref(G+'/committed.json'),Object_root_actual_P_readiness=ref(B+'/Object_runtime_readiness_root.json'),Object_post_independent_review=ref(D+'/post_readiness_independent_review.json'),Object_source_control_scope='Only first full Object256s23 paired200 development; no general profile/global-release/final compatibility is implied',Goal_original200_HOLD=True,all_new_Goal_scientific_HOLD=True,Goal_prefix58_CPU_checks=212,Goal_prefix58_real_runner_implemented=False,Goal_prefix58_real_GPU_acceptance=False,Goal_prefix58_independent_review=extra_goal,training_controller_complete_after_inherited_root_admission=True,root_integrity=f['last_terminals_integrity_review_20261020T1644'],archive_receipts=materials['archive_receipts'],previous_root_supervision=s['last_root_supervision_snapshot'],sealed_final_trials=0,global_release=False,normal_training_left_to_controller=True,no_normal_GPU_realtime_polling=True,weights_on_server_only=True)
 save(B+'/final_summary.json',summary)
 f.setdefault('downstream_followups_history',[]).append(f['downstream_followups_20261020T1644']);f['downstream_followups_20261020T1644']=ref(B+'/final_summary.json');s['last_root_supervision_snapshot']=ref(B+'/final_summary.json')
 line=('2026-10-21 本轮补充：训练 root＋独审完成 72/72 组（360000 reviewed updates）。Object256 seed23 已完成新控制路径、实际 P wrapper、checkpoint 字节及 post 独审，并仅提交一次开发作业 '+a.job_id+'（A/B 共 200 条、100 个既定初态）；本轮新增800条开发结果已完成原root与独立复核，当前动作5200条加兼容Long600条，共5800条，仍为400唯一开发初态。最新真实提交对账为 '+str(summary['registered_requested_active_GPU_jobs'])+' 个登记活动 GPU 作业，累计分配 '+format(hours,'.3f')+' GPUh（含在运下界及失败成本）。Goal 原 200 条与新增科学开发继续 HOLD；前 58 条观察器 CPU 候选 212 检查通过，但独审发现3项隔离保护缺口，单次 GPU 外层入口与真实工程验收仍未完成。最终 35200 条继续封存。非权重证据仅服务器归档并待本轮 Git 同步；全部历史记录保留。')
 for n in DOCS:
  p=R/'docs'/(n+'.md');oldbytes=p.read_bytes();p.write_bytes((line+'\n\n').replace('\\n','\n').encode()+oldbytes)
 p=R/'docs/正式下游阻塞登记_20261020T1644.md';p.write_bytes((line+'\n\n').replace('\\n','\n').encode()+p.read_bytes())
 assert s['registered_jobs']==old['registered_jobs'] and s['autonomous_training_v1']==old['autonomous_training_v1'] and s['current_round_cost']==old['current_round_cost']
 c.atomic_json(R/sn,s,before)
 exact=[]
 for root in [R/D,R/'scripts/ops/formal_object256s23_source_bridge_v1',R/G]:
  for p in sorted(root.rglob('*')):
   if p.is_file():exact.append(ref(p.relative_to(R).as_posix()))
 scope=check(materials['delivery_scope']);assert scope['status']=='root_reviewed_delivery_scope'
 for x in scope['additional_exact']:assert (R/x['path']).is_file() and h(R/x['path'])==x['sha256'];exact.append(x)
 exact.extend([ref(j['invocation']),ref('results/formal_main_v2/submissions/'+a.job_id+'.json')])
 rootfiles=list(materials['additional_root_files'])
 for n in [a.materials,materials['delivery_scope']['path'],'.local/github_push_20261020T1644.py','.local/github_push_20261020T1530_verified.json','.local/git_commit_20261020T1530.json','.local/accept_post_20261020T1644_creation_attempt01_failure.json','.local/archive_final_manifest_shape_failure_20261020T1644.json']:
  rootfiles.append(ref(n))
 extra=dict(status='root_exact_delivery_scope',baseline='88a0fea9b76a7f904ec0e9ce0c848b3b3413f36d',root_completed_arms=72,new_development_accepted=800,additional_root_files=rootfiles,archive_receipts=[x['path'] for x in materials['archive_receipts']],additional_exact=exact,exact_gitignore_exceptions=scope.get('exact_gitignore_exceptions',[]),new_GPU_jobs=[a.job_id],commit_message='Complete 72 formal training reviews and accept 800 development trials')
 save(B+'/git_extra_inputs.json',extra)
 print(json.dumps(dict(summary=ref(B+'/final_summary.json'),GPU_hours=hours,active_GPU=summary['registered_requested_active_GPU_jobs'],root_completed=72,new_job=a.job_id,git_extra_inputs=ref(B+'/git_extra_inputs.json'))),flush=True)

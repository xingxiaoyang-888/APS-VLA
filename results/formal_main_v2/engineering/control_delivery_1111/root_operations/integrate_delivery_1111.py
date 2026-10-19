from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261019T1911';O='results/formal_main_v2/engineering/control_delivery_1111'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel,pin):
 p=R/rel;assert h(p)==pin;return json.loads(p.read_text())
def ref(rel):return {'path':rel,'sha256':h(R/rel)}
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(rel)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('integrate1111',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=h(state);s=json.loads(state.read_text());baseline=copy.deepcopy(s)
 assert s['pending_submission'] is None and s['autonomous_training_v1']['controller_job_id']=='3034538'
 obs=read(B+'/closing_observation.json','ba47a3b3c94e309b0f7ed936eba465a3e4f1631cf7b607216a6c9c034e99bc34')
 publication=read(B+'/engineering_publication.json','bb00f0b569e213a73ce468fc3052c87b84cc087ea0bf68f9fd26f8a726c8be2a')
 canonical=read(B+'/cuda_continuous_canonical_preflight.json','f3b4045658096f6eabe68b15a3a0083009138ec965858d8b2f81a416e93c6020')
 assert canonical['status']=='passed_readonly_actual_evidence' and not canonical['GPU_submitted'] and not canonical['invocation_published']
 assert len(obs['capacity']['occupied'])==8 and not obs['capacity']['unknown'] and not obs['capacity']['findings']
 for p in publication['published']:assert h(R/p['path'])==p['sha256']
 assert s['formal_main_progress']['completed_final_trials']==0 and not s['formal_main_progress']['global_release_created']
 assert len(s['formal_main_progress']['completed_training_pairs'])*2==obs['root_independent_complete']==44
 stamp=datetime.now(timezone.utc).isoformat();local=datetime.fromisoformat(obs['utc']).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='root_scheduled_supervision',utc=stamp,prior_root_snapshot=s['last_root_supervision_snapshot'],observation=ref(B+'/closing_observation.json'),root_and_independent_completed_arms=44,machine_and_prior_completed_arms=44,root_reviewed_arm_updates=231000,active_GPU_jobs=8,allocated_GPU_hours_at_observation=obs['allocated_GPU_hours'],allocated_GPU_seconds_at_observation=obs['allocated_GPU_seconds'],cost_is_final=False,controller_job_id='3034538',controller_healthy_at_observation=True,global_pending_at_observation=None,engineering_publication=ref(B+'/engineering_publication.json'),cuda_authorization=publication['cuda_authorization'],cuda_actual_preflight=publication['cuda_actual_preflight'],CUDA_future_submission_requires='Exact single gateway, no previous request footprint, original evidence and both resume SHAs unchanged, healthy controller owner/lease, all actual registered jobs consistent, occupied plus existing reserved slots plus1 at most8.',guard_root_review=publication['guard_root_review'],guard_activated=False,actual_new_deployment_trials=0,retained_development_trials=1212,retained_Object_policy_errors=1,final_trials=0,final_release=False,normal_training_unmodified=True,submitted_GPU_jobs_this_turn=[],spatial_reserved_slots=1,spatial_authorization=ref('results/formal_main_v2/execution/action_spatial_resume_0943/submission_authorization.json'),no_intra_turn_GPU_polling_needed=True,next=['At next scheduled supervision reconcile all registry/pending/owner/lease once; when exact reserved slot opens submit preapproved Spatial588 request.','When unreserved capacity exists use newly approved Object256s23 exact one-time500-to5000 gateway. Never clear failure/block history or consume Spatial reservation.','Two other CUDA original-target recoveries remain separately bounded; no unreviewed retries.','Integrate ancestry guard explicitly before any O2A/global freeze consumption; no old-prefix outcome equivalence established.','Normal controller continues5000, retain every500 validation and all72 fixed scientific identities.']))
 issue=s['formal_main_progress']['CUDA_startup_issue']
 issue['status']='Object256_seed23_original500_passed_continuous5000_registered_waiting_unreserved_capacity_other_two_blocked'
 issue['continuous5000_admission_3039258']={'status':'approved_exact_once_not_submitted','authorization':publication['cuda_authorization'],'root_review':publication['cuda_root_review'],'actual_preflight':publication['cuda_actual_preflight'],'independent_review':ref(O+'/cuda_independent/independent_review.json'),'scientific_settings_changed':False,'automatic_retry':False,'controller_block_preserved':True,'existing_Spatial_reservation_preserved':True,'future_submission_needs_fresh_all_registered_job_check':True}
 issue['original_target_recovery_3039258']['continuous5000_admission']=True
 issue['next']='Exact500-to5000 gateway is CPU/root/independently reviewed and canonical real evidence passed; submit only when unreserved capacity passes, retaining old FAILED and two other exception holds.'
 issue['scheduler_next']='Normal controller continues healthy pairs. Spatial reservation has priority; CUDA gateway may only use additional unreserved capacity. No request was submitted this supervision.'
 issue['single_recovery_authorizations'][0]['status']='original_target500_double_reviewed_continuous_admission_registered_not_submitted'
 action=s['formal_main_progress']['downstream_action_range_issue']
 action['transitive_execution_guard_v1']={'status':'CPU_reviewed_published_not_activated','root_review':publication['guard_root_review'],'independent_review':ref(O+'/guard_independent/independent_review.json'),'actual_O2A_join_verified':False,'production_callers_changed':False,'legacy_prefix_equivalence_established':False}
 action['status']='v4_GPU_passed_Spatial588_plan_ready_waiting_reserved_capacity_ancestry_guard_CPU_published'
 action['next']='Spatial exact development-only588 request is already approved; fresh queue/identity gate still required. O2A/global freeze remain closed until explicit guarded caller integration and complete compatible raw evidence; no old-prefix equivalence assumed.'
 s['next_actions']=json.loads((R/B/'summary.json').read_text())['next'];s['next_allowed_action']=issue['scheduler_next']+' Later O2A/freeze/final remain closed under typed ancestry checks.'
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=stamp;s['updated_utc']=stamp
 assert s['autonomous_training_v1']==baseline['autonomous_training_v1'] and s['registered_jobs']==baseline['registered_jobs'] and s['current_round_cost']==baseline['current_round_cost']
 assert s['formal_main_progress']['completed_training_pairs']==baseline['formal_main_progress']['completed_training_pairs']
 c.atomic_json(state,s,before)
 common=local+' CST监督：完整训练仍44/72组（Long18、Spatial16、Object8、Goal2），8卡正常运行；累计346.435 GPU小时，含失败及运行中分配，非最终成本。Object256 seed23原500步恢复后的连续5000入口已完成CPU双审、root登记和实际canonical路径/原始日志/两resume SHA复核；不清除历史FAILED或blocked，只允许额外非预留空槽的一次精确请求。本轮未提交新GPU作业，Spatial588的1槽预约保持，正常训练交控制器继续。'
 link='[本轮收据](../'+B+'/summary.json)。'
 paragraphs={
 '正式自动连续训练执行登记':common+' 正常5000/每500验证与173冻结源不变，异常不自动重试。'+link,
 '正式CUDA启动失败恢复登记':local+' CST：新增独立入口 scripts/ops/formal_cuda_continuous_admission_v1 与授权 configs/experiments/formal_main_v2_cuda_continuous_3039258_v1.json，精确Object256 seed23从A/B500、cursor4000恢复至5000；48小时分配、169200秒软时限，11次验证。作者38项CPU检查、独立20项入口＋3项原控制器pending检查通过；实际canonical原日志重建及211份服务器输入、两resume SHA通过。历史84＋6512＝6596 GPU秒保留；本次只做hash-only预检，完整optimizer/RNG/cursor由实际恢复训练加载验证。当前8满且Spatial保留1槽，未提交；正常控制器不接管异常历史。若该次软时限仍未完成或异常，先root重新复核；完成5000需原始证据root和独审后显式继承。其他两组仍待原目标有界恢复。'+link,
 '正式动作执行入口接入记录':local+' CST：新增 scripts/ops/formal_action_consumption_guard_v1 两个独立消费文件，作者23项、独立13项CPU检查通过，原7个部署文件不改。逐SHA追溯全部继承前缀，旧执行记录不能由最新顶层版本号取得O2A或全局冻结准入；无等价例外。原O2A验证和 release_global(release=False)在明确synthetic上游的CPU fixture中验证兼容，不能作为真实GPU或主结果。该候选仅发布，未接入生产调用；actual_O2A_join_verified=false。Spatial原12条＋追加588的具体授权保持，8满未提交；旧前缀未证明可比，O2A/freeze/final继续关闭。'+link,
 '实验进度':common+' 新增的是异常恢复及历史执行链消费检查，无新科学成功率或完整延迟。开发1212条（含1条policy_error）原样保留，最终0/35200封存。'+link,
 '完整实验计划':common+' 后续按已登记入口及空槽推进；混合旧执行前缀的O2A/global freeze检查已完成CPU双审，调用方尚未启用，仍须完整真实链。全部72组与35200最终评测门槛不变。'+link,
 '正式主实验规划':common+' 不新增科学分支、种子或预算；当前只完成工程准入，无新增主结果。最终0/35200继续封存，root全局release门槛不变。'+link,
 '正式主实验阶段结论':common+' 本轮无新增正式成功率、完整O2A或最终评测结果。CPU工程通过与原500恢复不支持未来监督收益结论；训练和正式证据交付继续，最终0/35200。'+link}
 inv=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text());changed=[]
 for name,paragraph in paragraphs.items():
  rel='docs/'+name+'.md';assert rel not in inv['files'];p=R/rel;old=p.read_text();head,rest=old.split('\n',1);p.write_text(head+'\n\n'+paragraph+'\n'+rest);changed.append(ref(rel))
 for name in ['integrate_delivery_1111.py','observe_closing_1111.py']:
  p=R/O/'root_operations'/name
  with p.open('xb') as f:f.write((R/'.local'/name).read_bytes())
 result=save(B+'/integration_receipt.json',dict(schema='formal_main_v2',summary=summary,utc=stamp,state_sha256_before=before,state_sha256_after=h(state),controller_settings_unchanged=True,registered_jobs_unchanged=True,all_scientific_completion_and_cost_fields_unchanged=True,docs=changed))
 print(json.dumps(dict(summary=summary,integration=result)))

from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1630';E='results/formal_main_v2/engineering/supervision_delivery_0830';O='results/formal_main_v2/execution/long_collect_action_v1_0830'
SD='.local/long_collect_submission_independent_0830'
AR=dict(path=O+'/submission_authorization.json',sha256='e00503d5d79d397a8fc8016cb674c7d9f728c05e8229c3b3fe5e101f36e3f67b')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def rd(rel,pin=None):
 p=R/rel
 if pin:assert h(p)==pin,rel
 return json.loads(p.read_bytes())
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as stream:json.dump(v,stream,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
 return ref(rel)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('integrate0830ctl',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=rd('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 assert f['root_and_independent_completed_arms']==62 and f['root_and_independent_reviewed_arm_updates']==314000
 assert f['completed_development_trials']==2812 and f['current_action_development_trial_count']==1600 and f['current_action_development_unique_initial_states']==100
 assert f['historical_other_action_semantics_development_trials']==1212 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 accepted=rd(B+'/Long_development_acceptance.json','d80d71092b63694d34759babb4c1df86d74fed43e7a4b8c714065dc7f235bc28')
 root=rd('results/formal_main_v2/downstream_reviews/3047443.json','20f91c0060f086bcf402cc0b9b4e9863397c27876f4809dd9bef211aa0c87c25')
 lind=rd('results/formal_main_v2/downstream_reviews/3047443_independent.json','0a04480cfae7c48beb8b4a81b99c5611d2273bd6f7c685a522beb096a7fd71d1')
 assert root['status']==lind['status']=='passed' and root['scientific_complete'] and lind['scientific_complete']
 assert root['completed_trials']==lind['completed_trials']==200 and lind['successes']=={'A64_seed41':90,'B64_seed41':94}
 statsref=ref(E+'/Long64_terminal_independent/Long64_three_seed_statistics.json')
 stats=rd(statsref['path'],'510cfc9c907b0d721df0ce39b6d528adddaf7b04575e848ec21e5622ba6f98d4')
 rv=rd(B+'/Long64_root_statistics_verification.json','796e79da6edcae3f8dcc0425f7d87da9117c3821d26af5d8fa3b943dfc2e9e37')
 assert stats['status']==rv['status']=='passed' and stats['total_trials']==600 and stats['unique_initial_states']==100
 assert not stats['O2A_latency_verified'] and not stats['final_release'] and not stats['test_opened']
 diagref=ref(B+'/Long64_diagnostics_root_verification.json')
 assert diagref['sha256']=='1f5d4dfe53cc73493d2c12720768331abea70acb9269e002bb05af34135b7f9c'
 assert f['Long_legacy6_equivalence_followup']['old_RNG_dump_not_registered_requirement'] and not f['Long_legacy6_equivalence_followup']['production_reuse_authorized']
 auth=rd(AR['path'],AR['sha256']);rec=rd(B+'/Long3047982_pending_reconciliation.json','371b146a0cf25bc0ba87a1b0c6064bc900755dbb2e11e21c1b94191a80cb75ab')
 assert rec['status']=='exact_original_ACK_job_reconciled' and rec['job']['job_id']=='3047982' and rec['new_submissions']==0 and not rec['automatic_retry']
 assert ctl['downstream_reservations_consumed'][AR['sha256']]['job_id']=='3047982'
 jobs=[j for j in s['registered_jobs'] if str(j['job_id'])=='3047982'];assert len(jobs)==1
 job=jobs[0];variable={'status','elapsed_seconds','exit_code','node','allocation'}
 assert {k:v for k,v in job.items() if k not in variable}=={k:v for k,v in rec['job'].items() if k not in variable}
 assert job['stage_key']=='libero_10_collect_648ce4233e78353e' and job['method_ids']==['dense']
 assert h(R/job['invocation'])==h(P/job['invocation'])==job['invocation_sha256']=='4f12f98f6c7027961eb14d3de07fd27387e8f30dc4edab2490a7649b0b2109be'
 ind=rd(SD+'/independent_review.json','833f15230ad781a3fca5e30951bb3a2b1fa2e2c01461e280e7b226d35ce093f3');assert ind['status']=='passed'
 assert ind['job_id']=='3047982' and ind['authorization']==AR and ind['root_reconciliation']==ref(B+'/Long3047982_pending_reconciliation.json')
 assert ind['occupied_before']==5 and ind['occupied_after']==6 and ind['dedicated_reserved_slots_before']==1 and ind['dedicated_reserved_slots_after']==0
 assert ind['single_submission'] and ind['exact_original_ACK_reconciled'] and ind['original_reconcile_function_passed'] and ind['actual_P_outer_verify_passed'] and ind['source173_unchanged']
 assert not ind['automatic_retry'] and not ind['duplicate_submission_found'] and not ind['final_values_read'] and ind['new_GPU_calls']==0
 manifest=rd(SD+'/manifest.json','90afe9cb47464f714e899313e77e5d80dc9072649e98cfa30b53b22e864d149b')
 rows=[]
 for raw in manifest['files']:
  row=dict(raw);p=Path(row['path'])
  if not p.is_relative_to(Path(SD)):p=Path(SD)/p
  assert p.is_relative_to(SD) and '..' not in p.parts and not p.is_absolute()
  row['path']=p.as_posix();rows.append(row)
 rows.append(dict(path=SD+'/manifest.json',sha256=h(R/SD/'manifest.json'),bytes=(R/SD/'manifest.json').stat().st_size))
 copies=[]
 for row in rows:
  src=R/row['path'];assert src.is_file() and not src.is_symlink() and h(src)==row['sha256'] and src.stat().st_size==row['bytes']
  assert src.suffix not in ['.pt','.pth','.bin','.safetensors','.ckpt','.pyc'] and src.stat().st_size<100*(1<<20)
  dst=R/E/'Long_collect_submission_independent'/Path(row['path']).relative_to(SD);dst.parent.mkdir(parents=True,exist_ok=True)
  assert not dst.exists()
  with dst.open('xb') as stream:stream.write(src.read_bytes())
  copies.append(dict(source=row,archive=ref(dst.relative_to(R).as_posix())))
 delivery=save(B+'/Long_collect_submission_independent_delivery.json',dict(copies=copies,source_manifest=ref(SD+'/manifest.json'),report=ref(E+'/Long_collect_submission_independent/independent_review.json'),original_ACK_reconciled_once=True,no_new_GPU_submission=True,no_collection_completion_claim=True))
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])<=8
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 assert obs['rows']['3047443']['status']=='COMPLETED' and obs['rows']['3047443']['elapsed_seconds']==3039
 assert obs['rows']['3047982']['status'] in ['RUNNING','PENDING','CONFIGURING','COMPLETED']
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost']['allocated_gpu_seconds']
 inventory=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():assert h(R/rel)==h(P/'snapshots/formal_main_v2_run_564be0995e'/rel)==pin
 collection=dict(job_id='3047982',status='submitted_once_original_ACK_reconciled_and_independently_reviewed',scheduler_status_at_snapshot=obs['rows']['3047982']['status'],planned_observations=30,planned_dense_trajectories=10,accepted_observations=0,new_success_rate_trials=0,development_panel_only=True,source_rule='minimum source_state_index per each of original10tasks;first/mid floor((N-1)/2)/last actualpreactionobs',method_ids=['dense'],source_state_indices=[0,4,7,3,6,2,3,6,8,2],authorization=AR,scientific_plan=ref(O+'/scientific_plan.json'),effective_plan=ref(O+'/effective_plan.json'),readiness=ref(O+'/runtime_readiness.json'),root_reconciliation=ref(B+'/Long3047982_pending_reconciliation.json'),independent_submission_review=ref(E+'/Long_collect_submission_independent/independent_review.json'),invocation=ref(job['invocation']),original_failure_retained=ref('results/formal_main_v2/downstream_gateway/'+AR['sha256']+'/failed_transaction.json'),full_latency_executed=False,components_executed=False,final_opened=False)
 assert 'Long_fixed_observation_collection' not in f
 f['Long_fixed_observation_collection']=collection
 s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 next_actions=['Leave healthy5000-step automatictraining to registered controller; no real-time normalGPU polling. Next scheduledheartbeat reviews genuine terminal evidence.',
 'At genuine3047982 terminal, pull nonweight collector/action/Slurm artifacts and verify exactly10 originaldevtrajectories/30observations with root plus independent review; no replacement or successbasedfilter. Preserve nonweight panel artifacts through the registered P-to-R-to-GitHub archive policy; weights onlyserver.',
 'Bounded independent review of legacyLong600 typed equivalence bridge using recovered historical installation and factory provenance, full600 actiontrace and registered action-executor evidence. Old fullRNGdump is not a registeredrequirement. No productionreuse or blindrerun until exactbridge accepted.',
 'Keep negativeLong128 seed23/41 alongside all256/64seeds. Current1600 trials share100uniqueinitialstates; old1212 remain separate. No confirmed successlatency tradeoff or Dense2pp conclusion.',
 'FullO2A/components retain original88identity/foursuite developmentfreeze; sealed35200finaltrials require all72checkpoint plus16refs plus rootglobalrelease. No finalvalues,selectionchange or scopeexpansion.']
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='scheduled_supervision_Long64_three_seed_development_and_fixed_observation_collection',utc=now,root_independent_complete=62,total_arms=72,completed_by_suite={'libero_10':18,'libero_spatial':16,'libero_object':16,'libero_goal':12},new_completed_training_groups=0,root_independent_updates=314000,new_reviewed_arm_updates=0,new_development_trials_accepted=200,new_development_GPU_seconds=3039,all_historical_and_new_development_trials=2812,current_action_development_trials=1600,current_action_unique_initial_states=100,historical_other_action_trials_not_pooled=1212,Long64_seed41=f['new_action_development_verified_by_job']['3047443'],Long64_three_seed_statistics=statsref,root_statistics_verification=ref(B+'/Long64_root_statistics_verification.json'),selected_checkpoint_diagnostics=ref(B+'/Long64_selected_diagnostics_delivery.json'),root_diagnostics_verification=diagref,Long_legacy6_provenance_correction=copy.deepcopy(f['Long_legacy6_equivalence_followup']),Long_collection=collection,independent_submission_delivery=delivery,new_GPU_submissions_by_root=['3047982'],original_ACK_reconciled_no_resubmit=True,new_duplicate_submissions=0,scheduler=obs,capacity=cap,active_GPU_jobs=len(cap['occupied']),reserved_GPU_slots=0,allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,cost_is_final=False,completed_final_trials=0,expected_final_trials=35200,final_sealed=True,normal_training_left_to_controller=True,server_only=True,scientific_files_unchanged=173,next=next_actions))
 f['latest_incremental_review']=summary;f['incremental_review_history'].append(summary)
 f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied'])
 f['parallel_execution']['actual_running_allocated_GPUs']=sum(obs['rows'][x]['gpus'] for x in cap['occupied'] if obs['rows'][x]['status']=='RUNNING')
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']='2026-10-20'
 s['current_work']=f'62/72 trainings root+independentcomplete (Long18 Spatial16 Object16 Goal12),314000 reviewedupdates. Long64seed41 A90/B94 accepted200. Long64 three-seed A87.333 B90.333, paired+3pp,CI[-0.333,+6.333]pp;1600 currentactiondevelopment share100uniqueinitialstates;old1212separate. Long fixed30observationcollect3047982 submittedonce,accepted0observations. Legacyinstallation/factoryprovenance recovered; typedbridge stillpending;fullRNGdumpnotrequired. {len(cap["occupied"])}activeGPU, {seconds/3600:.3f}GPUh;final0/35200sealed.'
 s['next_actions']=next_actions;s['next_allowed_action']=next_actions[0]
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 assert f['completed_training_pairs']==old['formal_main_progress']['completed_training_pairs']
 assert f['new_action_development_verified_by_job']==old['formal_main_progress']['new_action_development_verified_by_job']
 c.atomic_json(sp,s,before)
 text=f'{stamp}：训练仍为 **62/72组完成并经root与独立复核**（Long18、Spatial16、Object16、Goal12），314000已审臂更新。新增Long64 seed41的200条开发结果：A90/100、B94/100，配对+4个百分点；作业3047443完整分配3039GPU秒（0.844小时），动作收据和全部原始结果通过双审。\n\n'
 text+='Long64三seed全部保留：seed17 A87/B88、seed23 A85/B89、seed41 A90/B94；A均值87.333%、B90.333%，种子间SD分别2.517和3.215个百分点；B−A均值+3.000，SD1.732个百分点。按任务内初态簇携三seed重采样10000次，95%区间[-0.333,+6.333]个百分点；root从原始600条结果独立重算全部draw通过。区间包含零，尚不能确认稳定改善，不能解释为等效。完整O2A尚未完成，不作成功率—延迟折中或Dense2个百分点目标结论。逐任务、选中checkpoint动作误差与token重合率见专篇。\n\n'
 text+=f'Long新增16选择器已完成全部1600开发试验，仍对应100个唯一初态；旧1212条不同语义分列，总归档2812。固定测速输入已在结果前登记：原10任务各一条Dense开发轨迹、首中末共30观测，单次作业3047982；目前验收观测为0，不能计入成功率分母。提交后Slurm记账延迟已按原ACK、token及真实作业身份复核，未重复提交。当前{len(cap["occupied"])}卡活动，累计 **{seconds/3600:.3f} GPU小时**（包含失败、加载和运行中分配，非最终）。正常训练交自动控制器及后续定时监督。\n\n'
 text+='更正前轮历史证据表述：已从旧Git提交、实际安装日志、所有6作业导入路径及固定wheel恢复robosuite1.4.1/MuJoCo2.3.7安装与默认OSC_POSE工厂链；这不是补造当时控制器实例测量。原登记未要求历史全RNG dump，因此不把缺失dump设为新增门槛。完整600条动作trace及有类型约束的复用桥接仍需最终独立验收，暂未复用或重跑旧600。完整测速仍遵守原88身份与四套件开发冻结；最终0/35200封存，173科学文件不变。\n\n'
 text+=f'[本轮证据](../{B}/summary.json)，[Long64逐任务与诊断](正式Long64三种子开发结论.md)，[固定观测采集登记](正式Long固定测速观测采集登记.md)。\n\n'
 short=f'{stamp}：62/72训练组双审通过。本轮Long64 seed41开发A90/B94，200条验收；三seed A均值87.333%、B90.333%、配对+3个百分点，10000次簇bootstrap区间[-0.333,+6.333]，尚无稳定收益或实测折中结论。当前动作语义1600条共享100初态，历史1212另列。固定30观测采集3047982已单次提交，验收0观测；{len(cap["occupied"])}卡活动，累计{seconds/3600:.3f}GPU小时（非最终）。旧Long600已恢复历史安装/工厂来源，旧RNG dump不属原登记要求；完整复用桥仍待审，未复用或重跑。最终0/35200封存。详见[Long64结论](正式Long64三种子开发结论.md)及[本轮证据](../{B}/summary.json)。\n\n'
 docs=[]
 updates={name:(text if name=='实验进度' else short) for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式Long其余16选择器开发登记']}
 updates['正式Long256三种子与64预算开发进展']=f'{stamp}补充：Long64 seed41已完成双审；完整三seed结果见[Long64结论](正式Long64三种子开发结论.md)。下文保留15:50历史进展，未用后续结果覆盖当时记录。\n\n'
 updates['正式Long固定测速观测采集登记']=f'{stamp}执行登记：单次作业 **3047982** 已提交并独审通过，原ACK会计延迟已精确对账，无重提交。计划30观测、当前验收0；后续定时监督待真实产物双审，完整O2A/分项测速及最终评测未运行。[提交证据](../{B}/Long3047982_pending_reconciliation.json)。\n\n'
 for name,addition in updates.items():
  rel='docs/'+name+'.md';assert rel not in inventory['files'];p=R/rel;oldsha=h(p);first,tail=p.read_text().split('\n',1);p.write_text(first+'\n\n'+addition+tail.lstrip('\n'));docs.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 op=R/B/'root_operations';op.mkdir(exist_ok=True)
 names=['observe_formal_0830.py','pull_terminal_0830.py','review_long_3047443_0830.py','verify_long64_stats_0830.py','publish_Long_collect_input_0830.py','publish_Long_collect_plans_0830.py','review_Long_collect_root_0830.py','accept_Long64_development_0830.py','accept_Long64_development_0830_v2.py','archive_Long_diagnostics_collection_0830.py','archive_Long_diagnostics_collection_0830_v2.py','authorize_Long_collect_0830.py','dispatch_Long_collect_0830.py','reconcile_Long_collect_0830.py','integrate_0830.py']
 for name in names:
  raw=(R/'.local'/name).read_bytes();compile(raw,name,'exec')
  with (op/name).open('xb') as stream:stream.write(raw)
 with (R/B/'previous_Git_push_verified.json').open('xb') as stream:stream.write((R/'.local/github_push_0727_verified.json').read_bytes())
 save(B+'/root_integration.json',dict(status='integrated',state_before_sha256=before,state_after_sha256=h(sp),summary=summary,docs=docs,controller_and_registry_unchanged_by_integration=True,training_acceptances_unchanged=True,new_GPU_jobs=['3047982'],frozen_scientific_files=173,all_CPU_failed_attempts_and_dispatch_delay_preserved=True,normal_GPU_realtime_polling=False))
 print(json.dumps(dict(status='integrated',root_completed=62,reviewed_updates=314000,new_development=200,active_GPU_jobs=len(cap['occupied']),GPU_hours=seconds/3600,summary=summary)),flush=True)

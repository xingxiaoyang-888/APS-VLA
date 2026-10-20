from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1527';E='results/formal_main_v2/engineering/supervision_delivery_0727'
LD='.local/independent_long_development_0727';SD='.local/independent_long64s41_submission_0727';ED='.local/long_legacy6_followup_0727'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def read(rel):return json.loads((R/rel).read_bytes())
def checked(rel,pin):
 assert h(R/rel)==pin,rel
 return read(rel)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as stream:json.dump(x,stream,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
 return ref(rel)
def manifest_rows(rel,pin):
 manifest=checked(rel,pin);base=Path(rel).parent;rows=[]
 for raw in manifest['files']:
  row=dict(raw);rp=Path(row['path'])
  if not rp.is_relative_to(base):rp=base/rp
  assert rp.is_relative_to(base) and '..' not in rp.parts and not rp.is_absolute(),rp
  row['path']=rp.as_posix();rows.append(row)
 rows.append(dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size))
 seen=set()
 for row in rows:
  assert row['path'] not in seen;seen.add(row['path']);p=R/row['path']
  assert p.is_file() and not p.is_symlink() and p.resolve().is_relative_to((R/base).resolve())
  assert h(p)==row['sha256'] and p.stat().st_size==row['bytes'],row['path']
  assert p.suffix not in ['.pt','.pth','.bin','.safetensors','.ckpt','.pyc'] and p.stat().st_size<100*(1<<20)
 for row in manifest.get('execution_audits',[]):
  assert h(R/row['path'])==row['sha256'] and (R/row['path']).stat().st_size==row['bytes']
 return rows,base
def archive(rows,base,subdir):
 copies=[]
 for row in rows:
  source=R/row['path'];dest=R/E/subdir/Path(row['path']).relative_to(base);dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as stream:stream.write(source.read_bytes())
  copies.append(dict(source=row,archive=ref(dest.relative_to(R).as_posix())))
 return copies

cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('root_integrate0727',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and f['root_and_independent_completed_arms']==62 and f['root_and_independent_reviewed_arm_updates']==314000
 assert f['completed_development_trials']==2012 and f['current_action_development_trial_count']==800 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert ctl['reserved_GPU_slots']==0
 lrows,lbase=manifest_rows(LD+'/manifest.json','6a8559a9ed7cb9bd6de58a8e6d75aaa4078fe092b6015f38f3fbe8717f11957d')
 linds={};lroots={}
 job_data=[('3047152',256,41,'07c46b463db75271d7bdc6ecc43b43f9a20e4c88a351a88d16a735daf39ad03b','57ba312dbf5931bbe644dff9492cea7f12ec844cb28050f69012d33c27e80ec7',92,94,3130),('3047156',64,17,'9bd3713f5260d9b6da1397c6507330503ce429c59a4ea4a15986ac9a5d50e190','9cb561881876e7a40cc850bae9f38e12d1612960b16c6c5b27f0ec34ba2cb3d5',87,88,3025),('3047163',64,23,'5a1cc6e631a421f0891da6f6810fb0824717a37cd6d18fa26800e930acdac0bc','f507905b5a1ff214674ed39e2847fcda67224f62ec183915b2d5b5cd57dd9d57',85,89,3038)]
 for job,budget,seed,rpin,ipin,aa,bb,cost in job_data:
  lr='results/formal_main_v2/downstream_reviews/'+job+'.json';li=LD+'/job'+job+'/independent_review.json'
  lroot=checked(lr,rpin);lind=checked(li,ipin);lroots[job]=lroot;linds[job]=lind
  assert lroot['status']==lind['status']=='passed' and lroot['scientific_complete'] and lind['scientific_complete'] and lind['blockers']==[]
  assert lroot['completed_trials']==lind['completed_trials']==200 and lind['unique_initial_states']==100
  assert lind['successes']=={f'A{budget}_seed{seed}':aa,f'B{budget}_seed{seed}':bb}
  assert lind['cost']['all_attempt_GPU_seconds']==lroot['cost']['all_attempt_gpu_seconds']==cost and lind['root_review']==ref(lr)
  assert not lind['final_state_values_read'] and not lind['final_release'] and not lind['O2A_latency_verified'] and not lind['synthetic_evidence_used_for_scientific_acceptance'] and not lind['legacy_terminal_trials_reused']
  assert lind['action_checks']['executed_actions_exactly_match_chunk_prefixes'] and lind['action_checks']['future_head_calls']==0
  for path,pin in lind['evidence_sha256'].items():assert h(R/path)==pin,path
  assert len([x for x in f['Long_remaining16_development_submissions'] if x['job_id']==job and x['completed_trials_accepted']==0])==1
 combined=checked(LD+'/summary.json','ee5fffe324a18c865f737b347f2a4e32914ad9664e66d350db6493917e6f3ca3')
 assert combined['status']=='passed' and combined['completed_trials']==600 and combined['unique_initial_states']==100 and combined['sum_actual_current_GPU_seconds']==9193
 shared=checked(combined['shared_development_panel_check']['path'],combined['shared_development_panel_check']['sha256'])
 assert shared['status']=='passed' and shared['current_trials']==600 and shared['prior_trials']==800 and shared['unique_initial_states_across_all_seven_jobs']==100
 assert shared['not_independent_across_budget_or_seed'] and not shared['old1212_action_trials_merged']
 stats=checked(LD+'/Long256_three_seed_statistics.json','3ad37e5a918b92d7c9e8d5d0ea538584fe548a24bd0c9a03fd97c6ce28f69abb')
 rv=checked(B+'/Long256_root_statistics_verification.json','4a0e29680747c1ccef15d0ad1eb9494b0faec4efe915daa44c40cb293ccb4d7a')
 assert rv['status']=='passed' and rv['all30000_reported_draw_values_verified'] and rv['raw_trial_outcomes_verified']==600 and rv['unique_initial_state_clusters']==100
 assert stats['status']=='passed' and stats['cost']['actual_development_GPU_seconds']==9226 and not stats['practical_dense_margin_evaluated']
 sind=checked(SD+'/independent_review.json','57775df709c416f2c01425852e9f703902198cf8be1fce180e069f1937886086')
 assert sind['status']=='passed' and sind['blockers']==[] and sind['planned_trials']==200 and sind['new_trials_completed_by_this_review']==0
 assert sind['capacity_sequence']==[{'before':5,'after':6}] and [j['job_id'] for j in sind['jobs']]==['3047443']
 srows,sbase=manifest_rows(SD+'/manifest.json','eb895e0f22fd77162263b2d91819820912157e11605a099e5507bfbb3758d146')
 row=sind['jobs'][0];jobid='3047443';auth=row['authorization'];assert ref(auth['path'])==auth
 rec=checked(row['root_reconciliation']['path'],row['root_reconciliation']['sha256'])
 assert rec['status']=='exact_original_ACK_job_reconciled' and rec['new_submissions']==0 and rec['job']['job_id']==jobid
 ad='results/formal_main_v2/downstream_gateway/'+auth['sha256']
 assert read(ad+'/committed.json')['root_reconciliation']==row['root_reconciliation']
 js=[j for j in s['registered_jobs'] if str(j['job_id'])==jobid];assert len(js)==1
 assert js[0]['method_ids']==['A64_seed41','B64_seed41'] and h(R/js[0]['invocation'])==js[0]['invocation_sha256']
 assert ctl['downstream_reservations_consumed'][auth['sha256']]['job_id']==jobid
 submission=dict(job_id=jobid,suite='libero_10',visual_tokens=64,seed=41,method_ids=js[0]['method_ids'],planned_trials=200,unique_development_initial_states=100,completed_trials_accepted=0,status='submitted_once_original_ACK_and_full_identity_reconciled',authorization=auth,reconciliation=row['root_reconciliation'],independent_submission_review=dict(path=E+'/Long64s41_submission_independent/independent_review.json',sha256=h(R/SD/'independent_review.json')),failure_retained=ref(ad+'/failed_transaction.json'),original_failure_type=row['original_failure_type'],exact_reservation_consumed=True,automatic_retry=False,final_evaluation_enabled=False)
 assert not any(x['job_id']==jobid for x in f['Long_remaining16_development_submissions'])
 erows,ebase=manifest_rows(ED+'/delivery_final.json','c1309c1066274cdf5bbd876117aa185795c7ae6d3444d0e0dac18b8d22ecd001')
 proposal=checked(ED+'/minimum_followup_plan.json','2e8f7a13557b69041a4eba4b0f6963b1f9911a6114912b1e01fc2b6472464826')
 legacy=checked(ED+'/report.json','22a47a847ed81d7a18360354dd6a53b8e1153c716df78a87264bcbca25c49f18')
 assert legacy['completed_trials_checked']==600 and legacy['counts']==dict(trials=600,chunks=23179,actions=183676)
 assert not legacy['environment_rng_evidence']['historical_controller_equivalence_proven'] and not legacy['production_consumer_modified'] and legacy['new_scientific_trials']==legacy['new_GPU_seconds']==0
 assert not proposal['cpu_candidate']['unconditional_reuse_authorized'] and proposal['implementation_status']=='proposal_only_no_production_consumer_or_scheduler_change'
 for ev in proposal['source_pins']:assert h(R/ev['path'])==ev['sha256']
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])<=8 and obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 for job,_,_,_,_,_,_,secs in job_data:assert obs['rows'][job]['status']=='COMPLETED' and obs['rows'][job]['elapsed_seconds']==secs
 assert obs['rows'][jobid]['status'] in ['RUNNING','PENDING','CONFIGURING','COMPLETED']
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost']['allocated_gpu_seconds']
 inventory=checked('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():assert h(R/rel)==h(P/'snapshots/formal_main_v2_run_564be0995e'/rel)==pin
 assert not (R/B/'summary.json').exists()
 for job in linds:assert not (R/'results/formal_main_v2/downstream_reviews'/f'{job}_independent.json').exists()
 lcopies=archive(lrows,lbase,'Long_terminal_independent');scopies=archive(srows,sbase,'Long64s41_submission_independent');ecopies=archive(erows,ebase,'Long_legacy6_CPU_candidate')
 for job in linds:
  dest=R/'results/formal_main_v2/downstream_reviews'/f'{job}_independent.json'
  with dest.open('xb') as stream:stream.write((R/LD/('job'+job)/'independent_review.json').read_bytes())
 ldelivery=save(B+'/Long_terminal_independent_delivery.json',dict(copies=lcopies,source_manifest=ref(LD+'/manifest.json'),no_GPU_execution=True))
 sdelivery=save(B+'/Long64s41_submission_independent_delivery.json',dict(copies=scopies,report=ref(E+'/Long64s41_submission_independent/independent_review.json'),source_manifest=ref(SD+'/manifest.json'),no_GPU_execution=True))
 edelivery=save(B+'/Long_legacy6_CPU_candidate_delivery.json',dict(copies=ecopies,source_manifest=ref(ED+'/delivery_final.json'),author_CPU_candidate_only=True,root_acceptance_of_equivalence=False,independent_equivalence_review=False,production_reuse_authorized=False,no_GPU_execution=True,historical_controller_identity_gap_retained=True,recorded600_not_counted_again=True))
 newdevs=[];verified=f['new_action_development_verified_by_job'];assert set(verified)=={'3043709','3045322','3046779','3046798'}
 for job,budget,seed,_,_,_,_,cost in job_data:
  lind=linds[job];lr='results/formal_main_v2/downstream_reviews/'+job+'.json';li=lr.replace('.json','_independent.json');delta=round(lind['B_minus_A_success_rate']*100,8)
  newdev=dict(job_id=job,suite='libero_10',visual_tokens=budget,seed=seed,completed_trials=200,unique_initial_states=100,root_review=ref(lr),independent_review=ref(li),successes=lind['successes'],B_minus_A_percentage_points=delta,paired_outcomes=lind['paired_outcomes'],per_task=lind['per_task'],initial_observation_token_overlap_mean=lind['initial_observation_token_overlap_mean'],token_overlap_scope=lind['token_overlap_scope'],action_semantics_sha256=lind['action_semantics_sha256'],GPU_seconds=cost,O2A_complete=False,whole_suite_development_complete=False,no_legacy_semantics_equivalence_claimed=True)
  verified[job]=newdev;newdevs.append(newdev)
  prior=[x for x in f['Long_remaining16_development_submissions'] if x['job_id']==job][0]
  prior.update(status='passed_root_and_independent_terminal',completed_trials_accepted=200,root_terminal_review=ref(lr),independent_terminal_review=ref(li),terminal_GPU_seconds=cost,successes=lind['successes'],B_minus_A_percentage_points=delta)
 f['latest_new_action_development_verified']=newdevs[-1]
 f['completed_development_trials']=2612;f['current_action_development_trial_count']=1400;f['current_action_development_unique_initial_states']=100;f['historical_other_action_semantics_development_trials']=1212
 f['Long_remaining16_development_submissions'].append(submission)
 statref=ref(E+'/Long_terminal_independent/Long256_three_seed_statistics.json')
 f['Long256_three_seed_development_statistics']=dict(statistics=statref,root_reconstruction=ref(B+'/Long256_root_statistics_verification.json'),development_only=True,mean_difference_percentage_points=100*rv['point_difference'],CI95_B_minus_A_percentage_points=[x*100 for x in rv['CI95_B_minus_A']],unique_initial_state_clusters=100,final_or_latency_conclusion=False)
 f['Long_legacy6_equivalence_followup']=dict(status='author_CPU_candidate_historical_controller_identity_unresolved',delivery=edelivery,minimum_next_proposal=ref(E+'/Long_legacy6_CPU_candidate/minimum_followup_plan.json'),original600_reused=False,original600_rerun=False,new_scientific_trials=0,production_consumer_changed=False)
 keys=[]
 for k,v in f['completed_training_pairs'].items():
  if v.get('root_review') and v.get('independent_review'):
   for role in ['root_review','independent_review']:assert h(R/v[role])==v[role+'_sha256']
   keys.append(k)
  elif v.get('terminal_root_and_independent_review'):
   x=v['terminal_root_and_independent_review'];assert x['completed_by_arm']=={'A':5000,'B':5000}
   for role in ['root_review','independent_review']:assert ref(x[role]['path'])==x[role]
   keys.append(k)
 assert len(keys)==31
 suites={suite:2*sum(k.startswith(suite+'_k') for k in keys) for suite in ['libero_10','libero_spatial','libero_object','libero_goal']}
 assert suites=={'libero_10':18,'libero_spatial':16,'libero_object':16,'libero_goal':12}
 s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 next_actions=['Leave healthy automatic5000 training to controller; no continuous in-turn GPU polling. Next scheduled heartbeat reviews genuine terminal evidence.',
 'Review registered Long64seed41 development3047443 only after genuine terminal; planned200,accepted0 at this integration. No duplicate submission.',
 'Prepare fixed Long30-observation collection via accepted action runtime after immutable dense-only registration, independent readiness and oneGPU reservation; collect does not require globalfreeze. No substitute observations after failures.',
 'Keep legacy Long600 as historical only: full recorded-action trace passed an author CPU candidate, historical controller identity remains unresolved. Recover admissible evidence and review a typed bridge before reuse; do not bypass planner dedup or rerun by renaming.',
 'Full O2A and independent components keep original all88identity/four-suite-development freeze gate; all72checkpoint+16reference and rootglobalrelease required before sealed35200 final trials. No result-based reselection or scope expansion.']
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='scheduled_supervision_three_development_pairs_accepted_one_slot_refilled',utc=now,root_independent_complete=62,total_arms=72,completed_by_suite=suites,new_completed_training_groups=0,root_independent_updates=314000,new_reviewed_arm_updates=0,new_development_trials_accepted=600,new_development_GPU_seconds=9193,all_historical_and_new_development_trials=2612,current_action_development_trials=1400,current_action_unique_initial_states=100,historical_other_action_trials_not_pooled=1212,Long_development=newdevs,Long_terminal_independent_delivery=ldelivery,Long256_three_seed_statistics=statref,root_statistics_verification=ref(B+'/Long256_root_statistics_verification.json'),Long_legacy6_CPU_candidate=edelivery,new_GPU_submissions_by_root=[jobid],Long64s41_development_submission=submission,Long64s41_submission_independent_delivery=sdelivery,original_ACK_reconciled_no_resubmit=True,new_duplicate_submissions=0,scheduler=obs,capacity=cap,active_GPU_jobs=len(cap['occupied']),reserved_GPU_slots=0,allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,cost_is_final=False,completed_final_trials=0,expected_final_trials=35200,final_sealed=True,normal_training_left_to_controller=True,server_only=True,scientific_files_unchanged=173,next=next_actions))
 f['latest_incremental_review']=summary;f['incremental_review_history'].append(summary)
 f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied']);f['parallel_execution']['actual_running_allocated_GPUs']=sum(obs['rows'][x]['gpus'] for x in cap['occupied'] if obs['rows'][x]['status']=='RUNNING')
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']='2026-10-20'
 s['current_work']=f'62/72 training root+independent complete (Long18,Spatial16,Object16,Goal12),314000 reviewed arm updates unchanged. New600 Long development accepted:256s41 A92/B94,64s17 A87/B88,64s23 A85/B89. Long256 all3seed mean A92.667/B95,paired+2.333pp,CI[-1,+6]pp;development only,not confirmed improvement or O2A. Currentruntime1400 trials share100states;old1212 separate. Long64s41 job3047443 planned200,accepted0. Legacy600 authorCPU action trace checked but controller historical identity unresolved;no reuse/rerun. {len(cap["occupied"])} active GPU jobs;final0/35200sealed.'
 s['next_actions']=next_actions;s['next_allowed_action']=next_actions[0]
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 assert f['completed_training_pairs']==old['formal_main_progress']['completed_training_pairs']
 c.atomic_json(sp,s,before)
 text=f'{stamp}：训练仍为 **62/72组完成并通过root与独立复核**（Long18、Spatial16、Object16、Goal12），314000已审臂更新。本轮新增3组开发共600条双审通过：Long256 seed41 A92/100、B94/100（+2个百分点）；Long64 seed17 A87/100、B88/100（+1），seed23 A85/100、B89/100（+4）。新增作业全部分配成本3130+3025+3038=9193 GPU秒（2.554小时），不重复叠加嵌套阶段。\n\n'
 text+='Long256的17/23/41三seed已齐：A均值92.667%（种子间SD1.155个百分点），B95.000%（SD1.000），B−A均值+2.333个百分点（SD0.577）。按原登记seed20261016、10000次任务内初态簇携三seed的配对bootstrap，95%区间[-1.000,+6.000]个百分点；root另从600条原始结果以整数簇重算全部30000个draw值通过。这是开发结果，区间包含零，不能确认稳定提升，也不能认定等效；完整O2A与最终主表未完成，未评价Dense的2个百分点目标。此前Long128 seed23/41 A95/B92的负结果保留。\n\n'
 text+=f'当前动作语义共1400条试验仍只有100个共同开发初态，旧1212条不同语义分列，总归档2612。Long64 seed41已单次提交3047443；原提交后记账缺行已保留，仅对原ACK/token精确对账，未重发。当前{len(cap["occupied"])}卡活动，累计 **{seconds/3600:.3f} GPU小时**（含失败、加载及运行中分配，非最终）。该200条尚未验收，正常作业交自动控制器及后续定时监督。\n\n'
 text+='旧Long6方法600条已做全量CPU动作证据检查，23179完整chunk含未执行尾部，未发现动作差异；但历史robosuite控制器实例/源码身份与RNG快照未记录，不能用当前记录补造历史证据。作者CPU候选和失败修订均归档，尚未通过复用准入，不重跑600条或绕过去重。下一工程项是固定Long30观测面板采集的登记与验收；采集可先行，完整测速仍遵守88身份及四套件开发冻结门槛。最终0/35200继续封存，173科学文件不变。\n\n'
 text+=f'[本轮证据](../{B}/summary.json)，[逐种子逐任务结果](正式Long256三种子与64预算开发进展.md)。\n\n'
 short=f'{stamp}：62/72训练组双审通过；本轮600条Long开发双审通过（256s41 A92/B94，64s17 A87/B88，64s23 A85/B89）。Long256三seed B−A均值+2.333个百分点，10000次簇bootstrap 95%区间[-1,+6]，仅开发结果，尚无稳定收益或实测加速结论。当前语义1400条共享100初态，旧1212条分列；新3047443 Long64s41计划200条未验收。{len(cap["occupied"])}卡活动、累计{seconds/3600:.3f} GPU小时（非最终），最终0/35200封存。旧Long600等价复用仍缺历史控制器身份证据；固定30观测采集待登记准入，完整测速保留全局冻结门槛。[证据](../{B}/summary.json)。\n\n'
 docs=[]
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式Long其余16选择器开发登记']:
  rel='docs/'+name+'.md';p=R/rel;assert rel not in inventory['files'];first,tail=p.read_text().split('\n',1);oldsha=h(p);p.write_text(first+'\n\n'+(text if name=='实验进度' else short)+tail.lstrip('\n'));docs.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 report='# 正式Long256三种子与64预算开发进展\n\n'+stamp+'；仅formal_main_v2开发结果，不是最终主表。\n\n'
 report+='保持Long官方基座和登记训练设置：各预算从头训练5000更新、有效batch8、seed17/23/41，h8、λ0.1；每500步按任务等权硬teacher L1选checkpoint。部署移除未来头，一次硬Top-k、统一packing和一次VLA前向。10任务各10共同开发初态、环境seed0/runtime17、等待10、chunk8、最多520步。\n\n'
 report+='| 预算 | seed | A成功/100 | B成功/100 | B−A百分点 | 初观测token重合率 | 开发GPU秒 |\n|---|---:|---:|---:|---:|---:|---:|\n'
 for seed in [17,23,41]:
  v=stats['per_seed'][str(seed)];report+=f'|256|{seed}|{v["A_successes"]}|{v["B_successes"]}|{100*v["B_minus_A"]:+.3f}|{v["token_overlap_initial_observation_mean"]:.9f}|{v["development_GPU_seconds"]}|\n'
 for job,seed in [('3047156',17),('3047163',23)]:
  v=linds[job];report+=f'|64|{seed}|{v["successes"][f"A64_seed{seed}"]}|{v["successes"][f"B64_seed{seed}"]}|{v["B_minus_A_success_rate"]*100:+.3f}|{v["initial_observation_token_overlap_mean"]:.9f}|{v["cost"]["all_attempt_GPU_seconds"]}|\n'
 report+='\nLong64 seed41的200条已登记3047443，本报告不填入未验收结果，不计算缺一seed的三seed统计。token重合率仅针对100个共同初始观测，后续轨迹已经分叉，不能视为共同后续观测诊断。\n\n'
 report+='Long256 A均值92.667%±1.155个百分点、B95.000%±1.000（±为种子间样本标准差，ddof1）；配对差+2.333±0.577个百分点。10000次配对bootstrap（seed20261016），每任务内重采样初态，每簇携全部三seed和A/B，95%百分位区间[-1.000,+6.000]个百分点。600条不是600个独立初态；此区间以登记任务和种子为条件。区间包含零，尚不能确认稳定改善，不把差异不显著当等效。\n\n'
 report+='| 任务ID | 256s17 A/B（各/10） | 256s23 A/B | 256s41 A/B | 三seed平均B−A百分点 | 64s17 A/B | 64s23 A/B |\n|---|---:|---:|---:|---:|---:|---:|\n'
 for t in range(10):
  vals=[]
  for seed in [17,23,41]:
   v=stats['per_seed'][str(seed)]['per_task'];vals.append(str(v[f'A256_seed{seed}'][str(t)]['successes'])+'/'+str(v[f'B256_seed{seed}'][str(t)]['successes']))
  vals.append(f'{stats["per_task"][str(t)]["B_minus_A_mean"]*100:+.3f}')
  for job,seed in [('3047156',17),('3047163',23)]:
   v=linds[job]['per_task'];vals.append(str(v[f'A64_seed{seed}'][str(t)]['successes'])+'/'+str(v[f'B64_seed{seed}'][str(t)]['successes']))
  report+='|'+str(t)+'|'+'|'.join(vals)+'|\n'
 report+='\n逐任务负差也全部保留（如256预算任务4、9）；任务完整名称、逐初态三seed成功向量、全部bootstrap draw及源脚本见归档统计。此前128预算seed23/41 A95/B92，两者B−A均为−3个百分点，仍完整保留，不能按预算或种子择优报告。\n\n'
 for job,budget,seed,*_ in job_data:
  v=linds[job];o=v['paired_outcomes'];ac=v['action_checks'];report+=f'{budget}/seed{seed}：共同成功{o["(1, 1)"]}、仅A成功{o["(1, 0)"]}、仅B成功{o["(0, 1)"]}、均失败{o["(0, 0)"]}；原始{ac["raw_policy_calls"]}个动作chunk、{ac["executed_control_steps"]}控制步逐步匹配，未来头调用0。\n\n'
 report+='本轮新增600条开发作业分配9193GPU秒；Long256三seed开发累计9226秒，后者包含前轮已记成本，不能再与本轮数相加。全正式轮成本以本轮Slurm快照为准。当前语义1400条共享100唯一初态；旧1212条另列。训练动作误差见各选模原始记录，统一诊断汇总尚待完成；完整O2A和独立分项计时未完成，不作速度或成功率—延迟折中结论，也未评价相对Dense的2个百分点目标。封存最终初态未读取。\n\n'
 report+=f'[本轮总收据](../{B}/summary.json)，[统计及完整逐初态向量入口](../{E}/Long_terminal_independent/Long256_three_seed_statistics.json)，[root独立重算](../{B}/Long256_root_statistics_verification.json)。\n'
 p=R/'docs/正式Long256三种子与64预算开发进展.md'
 with p.open('x') as stream:stream.write(report)
 docs.append(dict(path=p.relative_to(R).as_posix(),after_sha256=h(p)))
 op=R/B/'root_operations';op.mkdir(exist_ok=True)
 names=['observe_formal_0727.py','pull_terminal_0727.py','review_long_3047152_0727.py','review_long_3047156_0727.py','review_long_3047163_0727.py','reserve_Long64seed41_0727.py','dispatch_long64seed41_0727.py','reconcile_long64s41_pending_0727.py','verify_long256_stats_0727.py','integrate_0727.py']
 for name in names:
  raw=(R/'.local'/name).read_bytes();compile(raw,name,'exec')
  with (op/name).open('xb') as stream:stream.write(raw)
 with (R/B/'previous_Git_push_verified.json').open('xb') as stream:stream.write((R/'.local/github_push_0626_verified.json').read_bytes())
 save(B+'/root_integration.json',dict(status='integrated',state_before_sha256=before,state_after_sha256=h(sp),summary=summary,docs=docs,controller_and_registry_unchanged_by_integration=True,training_acceptances_unchanged=True,new_GPU_jobs=[jobid],frozen_scientific_files=173,normal_gpu_realtime_polling=False))
 print(json.dumps(dict(status='integrated',root_completed=62,reviewed_updates=314000,new_development=600,active_GPU_jobs=len(cap['occupied']),GPU_hours=seconds/3600,summary=summary)),flush=True)

from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1330';E='results/formal_main_v2/engineering/supervision_delivery_0530'
NR='results/formal_main_v2/libero_goal/k128/seed41/training/segment_reviews/3039988.json';NI=NR.replace('.json','_independent.json')
IND='.local/independent_goal3039988_0530/3039988_independent_review.json';MAN='.local/independent_goal3039988_0530/delivery_files.json'
LIND='.local/independent_long3045322_0530/independent_review.json';LMAN='.local/independent_long3045322_0530/manifest.json'
LR='results/formal_main_v2/downstream_reviews/3045322.json';LI=LR.replace('.json','_independent.json')
SIND='.local/independent_long256_submissions_0530/independent_review.json';SMAN='.local/independent_long256_submissions_0530/manifest.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def read(rel):return json.loads((R/rel).read_text())
def checked(rel,pin):
 assert h(R/rel)==pin,rel
 return read(rel)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as stream:json.dump(x,stream,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
 return ref(rel)
def manifest_rows(rel,pin):
 manifest=checked(rel,pin);rows=[]
 for raw in manifest['files']:
  row=dict(raw)
  if Path(row['path']).parent==Path('.'):row['path']=(Path(rel).parent/row['path']).as_posix()
  rows.append(row)
 rows.append(dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size))
 for row in rows:
  source=R/row['path'];assert source.parent==R/Path(rel).parent and source.is_file() and not source.is_symlink()
  assert h(source)==row['sha256'] and source.stat().st_size==row['bytes'],row['path']
  assert source.suffix not in ['.pt','.pth','.bin','.safetensors','.ckpt','.pyc'] and source.stat().st_size<100*(1<<20)
 return rows
def archive(rows,subdir):
 copies=[]
 for row in rows:
  source=R/row['path'];dest=R/E/subdir/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as stream:stream.write(source.read_bytes())
  copies.append(dict(source=row,archive=ref(dest.relative_to(R).as_posix())))
 return copies
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('root_integrate0530',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and f['root_and_independent_completed_arms']==58 and f['root_and_independent_reviewed_arm_updates']==296000
 assert f['completed_development_trials']==1412 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert ctl['reserved_GPU_slots']==0
 root=checked(NR,'b6b23fab1123cade9f779c4a665ac9f4411356992c64f3840e1c34e5eadfd9b3')
 ind=checked(IND,'a078a33979e88a2114d60551139d014898ae79875abbf4b8f5caa62f09d3a9f1')
 assert root['status']=='passed' and ind['status']=='passed_complete_training_only' and root['completed_by_arm']==ind['completed_by_arm']=={'A':5000,'B':5000}
 assert root['pair_allocated_gpu_seconds']==ind['cost']['all_pair_allocated_GPU_seconds']==75191
 assert ind['cost']['allocations']==[{'GPU_seconds':3583,'job_id':'3028483'},{'GPU_seconds':71608,'job_id':'3039988'}]
 assert ind['same_AB_initialization_and_full40000_order'] and ind['all173_R_and_S_match'] and ind['new_reviewed_arm_updates']==9000
 assert not ind['scientific_closed_loop_claimed'] and not ind['final_release_authorized']
 proof=ind['parallel_root_reconstruction'];assert proof['path']==NR and proof['sha256']==h(R/NR) and proof['new_reviewed_arm_updates']==9000 and not proof['fresh_pair'] and proof['prior_reviewed_updates_per_arm']==500
 assert proof['selected_server_proof']==ref(B+'/3039988_selected_server.json')
 for path,pin in ind['read_evidence_sha256'].items():assert h(R/path)==pin,path
 grows=manifest_rows(MAN,'12c08b6520d47af972466fb2240ffcc0adc3f2fdcc8d78b7d9c785129a6a07d1')
 lroot=checked(LR,'d27e9bbf12e435ba3fd1341757b451e666b77528cd5fede6cb07ab19eb790699')
 lind=checked(LIND,'a1824a68cc0120b485df2271701c56c188b18793903e378273fff12cb33759e6')
 assert lroot['status']==lind['status']=='passed' and lroot['scientific_complete'] and lind['scientific_complete'] and lind['blockers']==[]
 assert lroot['completed_trials']==lind['completed_trials']==200 and lind['unique_initial_states']==100
 assert lind['successes']=={'A128_seed41':95,'B128_seed41':92} and lind['B_minus_A_success_rate']==-.03
 assert lind['cost']['all_attempt_GPU_seconds']==lroot['cost']['all_attempt_gpu_seconds']==3466
 assert lind['root_review']==ref(LR) and not lind['final_state_values_read'] and not lind['final_release'] and not lind['O2A_latency_verified']
 assert not lind['synthetic_evidence_used_for_scientific_acceptance'] and not lind['legacy_terminal_trials_reused']
 for path,pin in lind['evidence_sha256'].items():assert h(R/path)==pin,path
 cross=checked(lind['cross_seed_panel_identity']['path'],lind['cross_seed_panel_identity']['sha256'])
 assert cross['trial_count_across_two_seeds']==400 and cross['unique_initial_states_across_seed23_and41']==100 and cross['independent_initial_states_not_doubled'] and not cross['seed17_included'] and cross['legacy_action_trials_included']==0
 assert cross['old_seed23_review']==f['new_action_development_verified']['root_review']
 lrows=manifest_rows(LMAN,'59b366576d5732605a64ab0346f1612c5aec3725ee02c0ed47f0fd1ec431950f')
 sind=checked(SIND,'fb494eecbb9946cd210a5fee8a75be598f8226c84aca8ebb8a84cc1603889f5f')
 assert sind['status']=='passed' and sind['blockers']==[] and sind['planned_trials']==400 and sind['new_trials_completed_by_this_review']==0 and sind['capacity_sequence']==[6,7,8]
 assert {j['job_id'] for j in sind['jobs']}=={'3046779','3046798'}
 srows=manifest_rows(SMAN,'980b320c12d9f506049345bdd0d344e94e0a2354d3e4a1d9805d99001659fe79')
 submissions=[]
 invpins={17:'94f108d569f8b35e5f14abe9c84dc03da38b5f0d1ad311f0fb293fcbf0e4dd4f',23:'4acebf35167b3742e34b258e2811f065a1f1644485184774be402867ae3e58d9'}
 for row in sind['jobs']:
  jobid=row['job_id'];seed=row['seed'];auth=row['authorization'];assert ref(auth['path'])==auth
  rec=checked(row['root_reconciliation']['path'],row['root_reconciliation']['sha256'])
  assert rec['status']=='exact_original_ACK_job_reconciled' and rec['new_submissions']==0 and rec['job']['job_id']==jobid
  ad='results/formal_main_v2/downstream_gateway/'+auth['sha256']
  assert read(ad+'/committed.json')['root_reconciliation']==row['root_reconciliation']
  js=[j for j in s['registered_jobs'] if str(j['job_id'])==jobid];assert len(js)==1
  assert js[0]['method_ids']==[f'A256_seed{seed}',f'B256_seed{seed}'] and js[0]['invocation_sha256']==invpins[seed]
  assert ctl['downstream_reservations_consumed'][auth['sha256']]['job_id']==jobid
  submissions.append(dict(job_id=jobid,suite='libero_10',visual_tokens=256,seed=seed,method_ids=js[0]['method_ids'],planned_trials=200,unique_development_initial_states=100,completed_trials_accepted=0,status='submitted_once_pending_accounting_delay_reconciled',authorization=auth,reconciliation=row['root_reconciliation'],independent_submission_review=dict(path=E+'/Long256_submissions_independent/independent_review.json',sha256=h(R/SIND)),failure_retained=ref(ad+'/failed_transaction.json'),exact_reservation_consumed=True,automatic_retry=False,final_evaluation_enabled=False))
 entry=f['completed_training_pairs']['libero_goal_k128_seed41'];assert entry['verification_kind']=='machine_automatic_not_independent'
 selected=[]
 for a in ['A','B']:
  dr='results/formal_main_v2/libero_goal/k128/seed41/training/'+a+'/deployment_receipt.json';d=read(dr);ar=ind['arms'][a]
  assert ar['completed_updates']==5000 and ar['sample_uses']==40000 and ar['unique_windows']==33859 and ar['cursor']==40000
  assert d['checkpoint_sha256']==ar['best_sha256'] and d['metadata']['update']==ar['earliest_selected_update']=={'A':1500,'B':5000}[a] and d['metadata']['validation_metric']==ar['selected_teacher_l1']
  selected.append(dict(arm=a,path='/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_goal/k128/seed41/'+a+'/best.pt',expected_sha256=d['checkpoint_sha256'],selected_update=ar['earliest_selected_update'],validation_metric=ar['selected_teacher_l1'],metadata_source=ref(dr)))
 assert not any(x.get('job_id')=='3039988' and x.get('independent_review') for x in f['completed_engineering_segments'])
 history=f['Long_remaining16_development_submissions'];prior=[x for x in history if x['job_id']=='3045322']
 assert len(prior)==1 and prior[0]['completed_trials_accepted']==0 and not any(x['job_id'] in ['3046779','3046798'] for x in history)
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])<=8 and obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 assert obs['rows']['3039988']['status']=='COMPLETED' and obs['rows']['3039988']['elapsed_seconds']==71608 and obs['rows']['3045322']['status']=='COMPLETED' and obs['rows']['3045322']['elapsed_seconds']==3466
 for jobid in ['3046779','3046798']:assert obs['rows'][jobid]['status'] in ['RUNNING','PENDING','CONFIGURING'] and jobid in cap['occupied']
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost']['allocated_gpu_seconds']
 inventory=checked('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():assert h(R/rel)==h(P/'snapshots/formal_main_v2_run_564be0995e'/rel)==pin
 assert not (R/NI).exists() and not (R/LI).exists() and not (R/B/'summary.json').exists()
 gcopies=archive(grows,'Goal128seed41_independent');lcopies=archive(lrows,'Long128seed41_terminal_independent');scopies=archive(srows,'Long256_submissions_independent')
 for dest,source in [(NI,IND),(LI,LIND)]:
  with (R/dest).open('xb') as stream:stream.write((R/source).read_bytes())
 delivery=save(B+'/Goal3039988_independent_delivery.json',dict(copies=gcopies,canonical=ref(NI),source_manifest=ref(MAN),no_GPU_execution=True))
 ldelivery=save(B+'/Long3045322_independent_delivery.json',dict(copies=lcopies,canonical=ref(LI),source_manifest=ref(LMAN),no_GPU_execution=True))
 sdelivery=save(B+'/Long256_submissions_independent_delivery.json',dict(copies=scopies,report=ref(E+'/Long256_submissions_independent/independent_review.json'),source_manifest=ref(SMAN),no_GPU_execution=True))
 binding=save(B+'/3039988_selected_binding.json',dict(status='root_and_independent_selected_identity_verified',root_review=ref(NR),independent_review=ref(NI),actual_server_bytes=ref(B+'/3039988_selected_server.json'),selected_checkpoints=selected,weights_copied=False))
 entry.update(job_id='3039988',suite='libero_goal',visual_tokens=128,seed=41,root_review=NR,root_review_sha256=h(R/NR),independent_review=NI,independent_review_sha256=h(R/NI),selected_checkpoints=selected,selected_server_review=binding['path'],selected_server_review_sha256=binding['sha256'],verification_kind='machine_automatic_plus_root_and_independent_raw_reconstruction')
 f['root_and_independent_completed_arms']=60;f['root_and_independent_reviewed_arm_updates']+=9000
 f['completed_engineering_segments'].append(dict(job_id='3039988',suite='libero_goal',visual_tokens=128,seed=41,status='passed_root_and_independent_complete_training',updates_by_arm={'A':5000,'B':5000},allocated_gpu_seconds=71608,pair_total_gpu_seconds=75191,root_review=NR,root_review_sha256=h(R/NR),independent_review=NI,independent_review_sha256=h(R/NI),new_reviewed_arm_updates=9000,prior_root_independent_updates_per_arm=500))
 newdev=dict(job_id='3045322',suite='libero_10',visual_tokens=128,seed=41,completed_trials=200,unique_initial_states=100,root_review=ref(LR),independent_review=ref(LI),successes=lind['successes'],B_minus_A_percentage_points=-3,paired_outcomes=lind['paired_outcomes'],per_task=lind['per_task'],initial_observation_token_overlap_mean=lind['initial_observation_token_overlap_mean'],token_overlap_scope=lind['token_overlap_scope'],action_semantics_sha256=lind['action_semantics_sha256'],GPU_seconds=3466,O2A_complete=False,whole_suite_development_complete=False,no_legacy_semantics_equivalence_claimed=True)
 verified=f.setdefault('new_action_development_verified_by_job',{});assert not verified
 verified['3043709']=copy.deepcopy(f['new_action_development_verified']);verified['3045322']=newdev
 f['latest_new_action_development_verified']=newdev
 f['completed_development_trials']=1612
 f['current_action_development_trial_count']=400
 f['current_action_development_unique_initial_states']=100
 f['historical_other_action_semantics_development_trials']=1212
 prior[0].update(status='passed_root_and_independent_terminal',completed_trials_accepted=200,root_terminal_review=ref(LR),independent_terminal_review=ref(LI),terminal_GPU_seconds=3466,successes=lind['successes'],B_minus_A_percentage_points=-3)
 history.extend(submissions)
 keys=[]
 for k,v in f['completed_training_pairs'].items():
  if v.get('root_review') and v.get('independent_review'):
   for role in ['root_review','independent_review']:assert h(R/v[role])==v[role+'_sha256']
   keys.append(k)
  elif v.get('terminal_root_and_independent_review'):
   x=v['terminal_root_and_independent_review'];assert x['completed_by_arm']=={'A':5000,'B':5000}
   for role in ['root_review','independent_review']:assert ref(x[role]['path'])==x[role]
   keys.append(k)
 assert len(keys)==30
 suites={suite:2*sum(k.startswith(suite+'_k') for k in keys) for suite in ['libero_10','libero_spatial','libero_object','libero_goal']}
 assert suites=={'libero_10':18,'libero_spatial':16,'libero_object':14,'libero_goal':12}
 s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 next_actions=['Leave healthy auto5000 training to the controller; next scheduled heartbeat handles terminals and exceptions, no continuous in-turn polling.',
 'Long256 seed17/23 development3046779/3046798 are registered once for400 trials; review terminal artifacts at next scheduled supervision, never rerun accepted Long3043709/3045322.',
 'After an actual free slot, continue remaining registered development and latency work through exact authorization and shared8-slot accounting. Retain every historical failure and recovery cost.',
 'All72 selected checkpoints+16reference identities+4suite complete development receipts and root globalrelease remain required before final35200; no final-state reading or result-based reselection.']
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='scheduled_supervision_training_and_development_accepted_two_slots_refilled',utc=now,root_independent_complete=60,machine_complete=f['trained_arms'],completed_by_suite=suites,total_arms=72,new_completed_training_groups=2,root_independent_updates=305000,new_reviewed_arm_updates=9000,Goal128seed41_root=ref(NR),Goal128seed41_independent=ref(NI),selected_identity=binding,independent_delivery=delivery,training_sample_uses_per_arm=40000,unique_training_windows_per_arm=33859,second_traversal_uses_per_arm=6141,validation_nodes_per_arm=11,validation_windows_per_node=186,terminal_training_segment_GPU_seconds=71608,all_training_pair_GPU_seconds=75191,new_development_trials_accepted=200,all_historical_and_new_development_trials=1612,current_action_development_trials=400,current_action_unique_initial_states=100,historical_other_action_trials_not_pooled=1212,Long128seed41_development=newdev,Long_terminal_independent_delivery=ldelivery,new_GPU_submissions_by_root=['3046779','3046798'],Long256_development_submissions=submissions,Long_submissions_independent_delivery=sdelivery,original_ack_accounting_delays_reconciled_no_resubmit=True,new_duplicate_submissions=0,scheduler=obs,capacity=cap,active_GPU_jobs=len(cap['occupied']),reserved_GPU_slots=ctl['reserved_GPU_slots'],allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,cost_is_final=False,completed_final_trials=0,expected_final_trials=35200,final_sealed=True,normal_training_left_to_controller=True,server_only=True,scientific_files_unchanged=173,nonweight_archive=ind['archive_reconstruction']['snapshot'],new_archived_raw_bytes=169428644,independent_review_limitations=ind['limitations'],next=next_actions))
 f['latest_incremental_review']=summary;f['incremental_review_history'].append(summary)
 f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied']);f['parallel_execution']['actual_running_allocated_GPUs']=sum(obs['rows'][x]['gpus'] for x in cap['occupied'] if obs['rows'][x]['status']=='RUNNING')
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']='2026-10-20'
 s['current_work']=f'60/72 complete groups root+independent accepted (Long18,Spatial16,Object14,Goal12),305000 reviewed arm updates. New Goal128seed41 A/B500-to5000,11x186 cumulative validations,40000 uses/33859 unique windows,A1500/B5000 selected. Long128seed41 development3045322 accepted200 trials A95/B92 over100 shared initial states; no O2A claim. Long256seed17/23 development3046779/3046798 registered once,400 planned not accepted;{len(cap["occupied"])} active GPUs. Development1612 archived includes1212 historical different semantics and400 current over100 unique states;final0/35200 sealed.'
 s['next_actions']=next_actions;s['next_allowed_action']=next_actions[0]
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 c.atomic_json(sp,s,before)
 text=f'{stamp}：正式训练 **60/72组通过root与独立复核**（Long18、Spatial16、Object14、Goal12）。新增Goal128 seed41 A/B各完成5000步；保留先前500步双审，本次新增9000已审臂更新，累计305000。独立重建11×186验证、相同初始化及40000次样本顺序，33859个唯一窗口、第二轮6141次使用。A选1500步、B选5000步，teacher L1为0.01776323/0.01836487；实际best/resume SHA通过，3份新增大日志169428644字节无损重建，历史小日志保留。优化器/RNG恢复依据原真实验收、冻结加载实现和断点哈希链，本次未独立反序列化张量。该pair历次3583+71608=75191 GPU秒计入一次。\n\n'
 text+=f'Long128 seed41作业3045322的 **200条开发评测双审通过：A95/100、B92/100，B−A为−3个百分点**；共同成功91、仅A4、仅B1、均失败4。动作实际执行与8×7 chunk前缀一致，6835次推理、54014控制步，分配3466 GPU秒；初始观测token集合重合率0.881796875。seed23与41使用同100开发初态，当前动作语义下合计400条，不作200个独立初态；旧1212条不同动作语义结果保留但不混入比较。未据此宣称显著差异、等效或速度折中改善。\n\n'
 text+=f'两张空卡已分别启动Long256 seed17/23的登记开发评测3046779/3046798，共400条待验收；提交后记账延迟按原ACK、精确token及scontrol逐一对账，仅消费各自预约，均无重发。当前 **{len(cap["occupied"])}卡活动（6训练、2开发），正式轮累计{seconds/3600:.3f} GPU小时**，含失败、设置和运行中分配，非最终成本。开发归档1612条，最终0/35200继续封存。正常作业交自动运行，下次定时监督处理终态。[本轮收据](../{B}/summary.json)。\n\n'
 short=f'{stamp}：60/72组训练双审通过；新增Goal128 seed41 A/B各5000步，本次新增9000已审更新。Long128 seed41开发200条双审通过，A95%、B92%、配对−3个百分点；seed23/41同100初态，400条当前语义结果与1212条历史结果分列。Long256 seed17/23新作业3046779/3046798各200条待验收，两次均单次提交。{len(cap["occupied"])}卡活动，累计{seconds/3600:.3f} GPU小时（非最终）。未形成完整延迟/三seed结论，最终0/35200封存，173科学文件不变。[证据](../{B}/summary.json)。\n\n'
 docs=[]
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式Long其余16选择器开发登记']:
  rel='docs/'+name+'.md';p=R/rel;assert rel not in inventory['files'];first,tail=p.read_text().split('\n',1);oldsha=h(p);p.write_text(first+'\n\n'+(text if name=='实验进度' else short)+tail.lstrip('\n'));docs.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 report='# 正式Long128种子41开发结果\n\n'+stamp+'，formal_main_v2；仅开发结果，不是最终主表。\n\n'
 report+='原配置不变：Long官方基座；128总tokens、每视角64；seed41；5000更新、batch8；h8、λ0.1。checkpoint依原任务等权硬teacher L1选模。10任务×10共同开发初态，A/B配对200条，等待10步、chunk8、最多520控制步。一次硬Top-k及统一packing；训练期未来头、教师缓存和后续真实动作均不进入部署。\n\n'
 report+='| 任务ID | A成功/10 | B成功/10 | B−A（百分点） |\n|---|---:|---:|---:|\n'
 for t in range(10):
  a=lind['per_task']['A128_seed41'][str(t)]['successes'];b=lind['per_task']['B128_seed41'][str(t)]['successes']
  report+=f'| {t} | {a} | {b} | {(b-a)*10:+d} |\n'
 report+='| 全部100初态 | 95/100 | 92/100 | −3 |\n\n'
 report+='配对结果：共同成功91、仅A成功4、仅B成功1、共同失败4。初始观测token集合重合率0.881796875，仅比较相同起始观测，不视作不同策略后续轨迹同状态统计。执行日志核对6835个8×7 chunk、54014实际控制步，动作有限且绝对值≤1，每次实际动作与对应chunk前缀相等；未来头调用为0。\n\n'
 report+='全部Slurm分配3466 GPU秒（0.962778 GPU小时），包含加载和设置，不把子阶段成本重复累加。完整O2A、组件计时及正式动作误差汇总尚未完成，本记录不报告速度收益。\n\n'
 report+='seed23现有结果A95%、B92%完整保留；seed23和41共用100初态，400条trial仍为100个独立初态簇，不扩大样本量；尚未做三seed平均或最终统计。旧1212条不同动作执行语义记录另列，不能拼接进此对照。当前seed41 B低3个百分点，不预设未来监督有效，也不把未做显著性检验解释为等效。封存最终初态未开放，不据本结果改变方法、预算、窗口或选模。\n\n'
 report+=f'root收据：[3045322](../{LR})；独立收据：[完整审计](../{LI})；[原始trial](../results/formal_main_v2/libero_10/downstream/development/428eafaeb10a5ce3/attempt01/trials.jsonl)。独立重建原consumer及全部证据，173份R/S/实际镜像源一致；权重未回存。终态sacct空Comment通过原提交精确token、节点、invocation及计划身份补充核验，原失败、修正和三次审计入口日志均保留，未改变科学源或校验器。\n'
 p=R/'docs/正式Long128种子41开发结果.md';assert not p.exists();p.write_text(report);docs.append(dict(path=p.relative_to(R).as_posix(),after_sha256=h(p)))
 op=R/B/'root_operations';op.mkdir(exist_ok=True)
 for name in ['observe_formal_0530.py','reserve_Long256seed17_0530.py','dispatch_long256seed17_0530.py','reconcile_long256s17_pending_0530.py','reserve_Long256seed23_0530.py','dispatch_long256seed23_0530.py','reconcile_long256s23_pending_0530.py','review_terminal_0530.py','archive_results_0530.py','pull_long_0530.py','review_long_0530.py','integrate_0530.py']:
  raw=(R/'.local'/name).read_bytes();compile(raw,name,'exec')
  with (op/name).open('xb') as stream:stream.write(raw)
 with (R/B/'previous_Git_push_verified.json').open('xb') as stream:stream.write((R/'.local/github_push_0428_verified.json').read_bytes())
 save(B+'/root_integration.json',dict(status='integrated',state_before_sha256=before,state_after_sha256=h(sp),summary=summary,docs=docs,controller_and_registry_unchanged_by_integration=True,new_GPU_jobs=['3046779','3046798'],frozen_scientific_files=173,normal_gpu_realtime_polling=False))
 print(json.dumps(dict(status='integrated',root_completed=60,reviewed_updates=305000,new_development=200,active_GPU_jobs=len(cap['occupied']),GPU_hours=seconds/3600,summary=summary)),flush=True)

from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T2117';E='results/formal_main_v2/engineering/supervision_delivery_1317'
IND=E+'/Goal_terminal_independent/independent_review.json';IND_SHA='7cda4fb3d421242efcc9255c732a08952d4e0288d3866f0088220cd6c3e3cea9'
DISPATCH_REF={"path":"results/formal_main_v2/preflight/heartbeat_20261020T2117/dispatch_root_report.json","sha256":"d8408e661e9b48f3d5fe38c9bdd1458aba55125c19222a2bb0aefe06749e139a"}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel,pin=None):
 if pin:assert h(R/rel)==pin,rel
 return json.loads((R/rel).read_bytes())
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def put(rel,raw):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as out:out.write(raw)
 return ref(rel)
def save(rel,x):return put(rel,(json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode())
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spc=importlib.util.spec_from_file_location('integrate1317ctl',p);c=importlib.util.module_from_spec(spc);sys.modules[spc.name]=c;spc.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=rd('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 assert f['root_and_independent_completed_arms']==64 and f['root_and_independent_reviewed_arm_updates']==321000
 assert f['completed_development_trials']==3212 and f['current_action_development_trial_count']==2000
 assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 joint=rd(IND,IND_SHA);assert joint['status']=='passed' and joint['totals']['trials']==800 and joint['totals']['allocated_gpu_seconds']==7799
 paired_ref=ref(E+'/Goal_terminal_independent/paired_development_states.json')
 assert paired_ref['sha256']==joint['paired_states']['sha256']=='0dac8194680d5473ca746c3e10b8f0a5d46e040a2196ff7926a6f2df8f45d226'
 assert joint['source173_R_and_S_unchanged'] and not joint['checkpoint_bytes_read'] and joint['new_GPU_jobs']==0 and not joint['sealed_final_values_read']
 assert joint['unique_initial_states']==100 and joint['all_eight_methods_same_t0_observation_for_each_state']
 assert not joint['bootstrap_computed'] and not joint['CI_claimed']
 indref=put('results/formal_main_v2/downstream_reviews/Goal_seed17_23_1317_independent.json',(R/IND).read_bytes())
 newly=[]
 for jid,seed,n,gpusec,rootsha in [
  ('3048609',17,600,5780,'7e3fc5858ed27baacfb878cec8adea70e8e43df736e9f2f785eb1a189c5f31a8'),
  ('3049191',23,200,2019,'56a9bf2d1145ec5adc3efdc3a1ac145ac8d59a49a00325924068e7c49f7b7feb')]:
  assert jid not in f['new_action_development_verified_by_job']
  rootrel='results/formal_main_v2/downstream_reviews/'+jid+'.json';root=rd(rootrel,rootsha);j=joint['jobs'][jid]
  assert root['status']==j['status']=='passed' and root['scientific_complete'] and root['suite']==j['suite']=='libero_goal'
  assert root['completed_trials']==j['trials']==n and j['unique_initial_states']==100 and j['allocated_GPU_seconds']==gpusec and j['seed']==seed
  assert j['root_receipt']==ref(rootrel) and j['raw_start_result_pairs_exact'] and j['full_original_consumer_reconstruction_passed']
  rs=root['reconstructed_summary'];successes={k:v['successes'] for k,v in rs['methods'].items()}
  assert successes==j['successes']
  a='A128_seed'+str(seed);b='B128_seed'+str(seed)
  assert (j['A_success'],j['B_success'])==(successes[a],successes[b])
  pair=rs['paired_AB']['k128_seed'+str(seed)];assert pair['completed_pairs']==100 and len(pair['results'])==100
  assert abs(pair['B_minus_A_success_rate']*100-j['B_minus_A_pp'])<1e-10
  ledger=j['raw_ledger'];assert h(R/ledger['path'])==h(P/ledger['path'])==ledger['sha256']
  t0=j['t0_token_diagnostics'];assert t0['paired_observations']==100 and t0['all_t0_observation_hashes_equal']
  for diag in j['offline_validation_diagnostics'].values():rd(diag['validation_ref']['path'],diag['validation_ref']['sha256'])
  entry=dict(job_id=jid,suite='libero_goal',seed=seed,visual_tokens=128,visual_tokens_scope='A/B only; dense512 and uniform256/128/64 references separately recorded.',completed_trials=n,unique_initial_states=100,
   successes=successes,B_minus_A_percentage_points=j['B_minus_A_pp'],paired_outcomes=j['discordance'],per_task=j['per_task'],
   root_review=ref(rootrel),independent_review=indref,independent_review_scope='Exact joint independent report member selected by job_id.',
   raw_ledger=ledger,GPU_seconds=gpusec,GPU_cost_scope='Existing allocation counted once in global Slurm total; acceptance adds no new GPU allocation.',
   initial_observation_token_overlap_mean=t0['mean_intersection_over_128'],initial_observation_token_Jaccard_mean=t0['mean_Jaccard'],
   token_overlap_scope='Only100 equal-hash paired initial observations; later divergent observations not paired.',
   offline_validation_diagnostics=j['offline_validation_diagnostics'],action_semantics_sha256=root['action_semantics_sha256'],
   reference_trials=j['reference_trials'],AB_trials=j['AB_trials'],references=j.get('references',{}),
   no_legacy_semantics_equivalence_claimed=True,whole_suite_development_complete=False,O2A_complete=False)
  f['new_action_development_verified_by_job'][jid]=entry;newly.append(entry)
  group='nonLong_development_submissions_1032' if seed==17 else 'nonLong_development_submissions_1220'
  row=next(x for x in f[group] if x['job_id']==jid);assert row['completed_trials_accepted']==0
  row.update(completed_trials_accepted=n,observed_status='COMPLETED',scientific_terminal_acceptance_pending=False,terminal_root_review=ref(rootrel),terminal_independent_review=indref)
 current=f['new_action_development_verified_by_job'];assert sum(v['completed_trials'] for v in current.values())==2800
 states_by_suite={}
 for entry in current.values():
  rr=entry['root_review'];data=rd(rr['path'],rr['sha256']);states=states_by_suite.setdefault(data['suite'],set())
  for pair in data['reconstructed_summary']['paired_AB'].values():states.update(x['state_trial_id'] for x in pair['results'])
 expected={x:100 for x in ['libero_10','libero_spatial','libero_object','libero_goal']}
 assert {k:len(v) for k,v in states_by_suite.items()}==expected
 f['completed_development_trials']+=800;f['current_action_development_trial_count']=2800;f['current_action_development_unique_initial_states']=400
 f['current_action_development_unique_initial_states_by_suite']=expected
 assert f['historical_other_action_semantics_development_trials']==1212 and f['Long22_development_statistics']['explicit_legacy_equivalent_trials']==600
 assert joint['available_two_seed_mean_percent']==dict(A128=97.0,B128=97.0,B_minus_A_pp=0.0)
 stats=save(B+'/Goal_seed17_23_development_diagnostics.json',dict(schema='formal_main_v2',kind='accepted_two_seed_Goal_development_diagnostics',jobs=newly,
  total_trials=800,unique_initial_states=100,all_job_GPU_seconds=7799,GPU_cost_already_in_Slurm_total=True,
  per_task_and_full_paired_trials=paired_ref,source_independent=indref,available_training_seeds=[17,23],missing_training_seed=41,
  available_two_seed_mean_percent=joint['available_two_seed_mean_percent'],
  observation_scope='Initial paired observations only for token overlap; validation hard-pruning L1 only for action error.',
  inference='Goal128 seed17 B-A +1pp and seed23 -1pp. Two-seed descriptive means both97%; no equivalence, final or measured latency tradeoff conclusion.',
  bootstrap_three_seed_claimed=False,O2A_measured=False,final_results=False))
 f['latest_new_action_development_verified']=stats;f['Goal128_partial_development_statistics']=stats
 dispatch=rd(DISPATCH_REF['path'],DISPATCH_REF['sha256']);assert dispatch['status']=='all_selected_requests_registered_once'
 submissions=dispatch['submissions'];assert 0<len(submissions)<=4
 for row in submissions:
  jid=row['job_id'];matches=[j for j in s['registered_jobs'] if str(j['job_id'])==jid];assert len(matches)==1
  assert row['planned_trials']==200 and row['completed_trials_accepted']==0
  j=matches[0];assert j['suite']==row['suite'] and j['method_ids']==row['method_ids'] and row['completed_trials_accepted']==0
  assert rd(row['authorization']['path'],row['authorization']['sha256'])
  rec=rd(row['root_reconciliation']['path'],row['root_reconciliation']['sha256'])
  assert rec['status']=='exact_original_ACK_job_reconciled' and rec['new_submissions']==0
  apin=row['authorization']['sha256'];ad='results/formal_main_v2/downstream_gateway/'+apin
  assert rd(ad+'/sbatch_result.json')['stdout']==jid+'\n' and ctl['downstream_reservations_consumed'][apin]['job_id']==jid
  assert rd(ad+'/committed.json')['root_reconciliation']==row['root_reconciliation']
  assert (R/j['invocation']).read_bytes()==(P/j['invocation']).read_bytes()
 assert 'nonLong_development_submissions_1317' not in f
 f['nonLong_development_submissions_1317']=copy.deepcopy(submissions)
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['unknown'] and not cap['findings'] and len(cap['occupied'])<=8
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost']['allocated_gpu_seconds']
 s['current_round_cost'].update(allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied'])
 inventory=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 assert len(inventory['files'])==173
 for name,pin in inventory['files'].items():assert h(R/name)==h(P/'snapshots/formal_main_v2_run_564be0995e'/name)==pin
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 summary=save(B+'/summary_after_dispatch.json',dict(schema='formal_main_v2',kind='Goal800_accepted_registered_development_refill',utc=now,
  state_before_sha256=before,root_independent_complete=64,total_training_arms=72,root_independent_updates=321000,
  completed_by_suite={'libero_10':18,'libero_spatial':18,'libero_object':16,'libero_goal':12},new_development_trials=800,
  raw_historical_and_current_development_trials=4012,current_action_development_trials=2800,current_action_unique_initial_states=400,
  unique_current_initial_states_by_suite=expected,explicit_legacy_equivalent_Long_trials=600,
  compatible_current_and_explicit_legacy_trials=3400,legacy1212_preserved_and_not_relabelled=True,
  accepted_jobs=newly,diagnostics=stats,new_submissions=submissions,new_planned_trials=200*len(submissions),
  active_GPU_jobs=len(cap['occupied']),capacity=cap,scheduler=obs,allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,
  includes_all_registered_allocations=True,cost_is_final=False,controller='3034538',controller_owner_id=ctl['owner_id'],
  pending=None,reserved_GPU_slots=0,new_final_trials=0,final_completed=0,final_expected=35200,final_release=False,source173_unchanged=True,
  scientific_settings_changed=False,automatic_expansion=False,full_72_training_complete=False,
  submission_independent_integration_review_pending=True))
 f['latest_capacity_refill']=summary
 s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']=stamp[:10];s['last_root_supervision_snapshot']=summary;s['last_root_health_check']=summary;s['last_healthy_supervision']=summary
 ids=[x['job_id'] for x in submissions]
 s['current_work']=f"64/72 root+independent training groups;321000 reviewed updates. NewGoal800 development accepted: seed17 A97/B98,seed23 A97/B96,dense97. {200*len(submissions)} development dispatched once {ids}. {len(cap['occupied'])} occupied GPU;{seconds/3600:.3f}GPUh. Current2800+explicitLong600 compatible development,400 unique states across4suites. Final0/35200sealed."
 s['next_actions']=[
  'Leave healthy normal training and development running; use scheduled supervision, no continuous polling.',
  'Review genuine terminals for remaining8 training arms and registered development jobs; never resubmit an existing identity.',
  'Fill real free slots only after original plan, checkpoint, independent readiness and duplicate/capacity gates.',
  'Retain Goal128 two-seed opposite differences and Long128 three-seed negative2.67pp; no tuning or equivalence claim.',
  'Final35200 and same-checkpointO2A/components retain globalfreeze/release gates; no sealed values read.']
 s['next_allowed_action']=s['next_actions'][0]
 assert ctl==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 assert f['completed_training_pairs']==old['formal_main_progress']['completed_training_pairs'] and f['automatic_machine_verified_pairs']==old['formal_main_progress']['automatic_machine_verified_pairs']
 put(B+'/root_operations/integrate_1317.py',Path(__file__).read_bytes())
 c.atomic_json(sp,s,before)
 brief=f"{stamp}：训练仍64/72组双审；新增Goal800条开发验收，128预算seed17 A97%/B98%、seed23 A97%/B96%，两seed描述均值均97%，共享100唯一初态，不能视为等效。Dense97%，均匀256/128/64分别95%/92%/68%。已按固定矩阵补位{200*len(submissions)}条开发（{','.join(ids)}），当前{len(cap['occupied'])}GPU占槽，累计{seconds/3600:.3f}GPU小时（非最终）。最终0/35200封存。见[本轮汇总](../{B}/summary_after_dispatch.json)及[Goal开发记录](正式Goal主预算开发结果.md)。"
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记']:
  p=R/'docs'/f'{name}.md';prior=p.read_text();first,rest=prior.split('\n',1);p.write_text(first+'\n\n'+brief+'\n'+rest)
 lines=['# 正式Goal主预算开发结果','',f'更新：{stamp}。当前为固定128预算seed17/23及四个共享参考，全部10任务×10开发初态。800条记录共100个唯一Goal初态，seed41及其他预算A/B尚待验收；最终集仍封存。','',
 '| 训练seed | A成功/100 | B成功/100 | B−A (pp) | t0交集/128 | t0 Jaccard |','|---|---:|---:|---:|---:|---:|']
 for j in newly:
  seed=j['seed'];lines.append(f"| {seed} | {j['successes']['A128_seed'+str(seed)]} | {j['successes']['B128_seed'+str(seed)]} | {j['B_minus_A_percentage_points']:+.0f} | {j['initial_observation_token_overlap_mean']:.6f} | {j['initial_observation_token_Jaccard_mean']:.6f} |")
 lines+=['','两seed描述均值A/B均97%，差异方向相反；不构成等效证明或三seed结论，未计算缺seed41的三seed区间。没有完整O2A结果，不能认定成功率—延迟折中改善。','',
 '| 共享参考 | 成功/100 |','|---|---:|']
 for name in ['dense','uniform256','uniform128','uniform64']:lines.append(f"| {name} | {newly[0]['successes'][name]} |")
 lines+=['','600条原作业5780GPU秒、另200条2019GPU秒，共7799GPU秒，已包含在Slurm总账；验收不重复加费。Dense/均匀参考没有训练seed，不复制三遍。','',
 '| seed/臂 | 选中update | 硬验证teacher L1 | 硬验证示范L1 | 验证窗口 |','|---|---:|---:|---:|---:|']
 for j in newly:
  for arm,dg in j['offline_validation_diagnostics'].items():lines.append(f"| {j['seed']}/{arm} | {dg['selected_update']} | {dg['hard_validation_teacher_L1_task_equal']:.8f} | {dg['hard_validation_demonstration_L1_task_equal']:.8f} | {dg['validation_windows']} |")
 lines+=['','上表为既定validation选中checkpoint的离线硬剪枝诊断，不是闭环动作误差；开发成败不参与选模。Token重合只在相同hash的t0观测上配对，后续不同轨迹不混作同观测。','',
 '| seed | task_id | A成功/10 | B成功/10 | B−A (pp) |','|---|---:|---:|---:|---:|']
 for j in newly:
  for t in j['per_task']:lines.append(f"| {j['seed']} | {t['task_id']} | {t['A_success']} | {t['B_success']} | {t['B_minus_A_pp']:+.0f} |")
 lines+=['','| task_id | Dense | Uniform256 | Uniform128 | Uniform64 |','|---|---:|---:|---:|---:|']
 for i in range(10):
  vals=[next(t['successes'] for t in newly[0]['references'][n]['per_task'] if t['task_id']==i) for n in ['dense','uniform256','uniform128','uniform64']]
  lines.append('| '+str(i)+' | '+' | '.join(map(str,vals))+' |')
 lines+=['',f"[逐任务名称、完整配对与诊断](../{stats['path']})；[原始配对记录](../{paired_ref['path']})；[原双批独审](../{indref['path']})。旧Long负结果、旧动作语义记录与全部失败保留，不据本轮开发结果调参。",'']
 put('docs/正式Goal主预算开发结果.md','\n'.join(lines).encode())
 p=R/'docs/正式非Long开发结果.md';t=p.read_text();first,rest=t.split('\n',1);p.write_text(first+'\n\n'+f"{stamp}增量：Goal新800条完成双审，seed17/23 A/B两seed均值均97%，仅描述、不代表等效。四参考和逐任务结果见[Goal开发记录](正式Goal主预算开发结果.md)；下方Spatial/Object历史结果保留。\n"+rest)
 print(json.dumps(dict(summary=summary,state_sha256=h(sp),GPU_hours=seconds/3600,occupied=len(cap['occupied']),newly_accepted=800,new_submissions=ids),ensure_ascii=False),flush=True)

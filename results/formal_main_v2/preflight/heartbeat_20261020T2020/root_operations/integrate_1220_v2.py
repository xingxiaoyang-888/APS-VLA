from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T2020';E='results/formal_main_v2/engineering/supervision_delivery_1220'
IND=E+'/nonLong_terminal_independent/independent_review.json';IND_SHA='67c2e32b61a1aa2ec02202d03ff2e28112e971f3968c2f8a88e3ad5100e1f120'
SUB_REVIEW={"path":"results/formal_main_v2/engineering/supervision_delivery_1220/nonLong_submission_independent/independent_review.json","sha256":"7e272e3787d4027c9593544e98f82affcdb55c1ff9e99daca2d38c4cefd016fe"}
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
spc=importlib.util.spec_from_file_location('integrate1220ctl',p);c=importlib.util.module_from_spec(spc);sys.modules[spc.name]=c;spc.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=rd('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 assert f['root_and_independent_completed_arms']==64 and f['root_and_independent_reviewed_arm_updates']==321000
 assert f['completed_development_trials']==2812 and f['current_action_development_trial_count']==1600
 assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 joint=rd(IND,IND_SHA);assert joint['status']=='passed' and joint['totals']['trials']==400 and joint['totals']['allocated_gpu_seconds']==4551
 assert h(R/E/'nonLong_terminal_independent/paired_development_states.json')==joint['paired_states']['sha256']=='8b767f80a3154778c8b0d3e31119f095eabaaf542b80e0b091564150e3a44346'
 assert joint['source173_R_and_S_unchanged'] and not joint['checkpoint_bytes_read'] and joint['new_GPU_jobs']==0 and not joint['sealed_final_values_read']
 indref=put('results/formal_main_v2/downstream_reviews/nonLong_seed23_1220_independent.json',(R/IND).read_bytes())
 sub=rd(SUB_REVIEW['path'],SUB_REVIEW['sha256']);assert sub['status']=='passed'
 indjobs={j['job_id']:j for j in joint['jobs'].values()}
 newly=[]
 for jid,suite,successes,gpusec,rootsha in [
  ('3048572','libero_spatial',{'A128_seed23':97,'B128_seed23':96},2365,'2de761a00124078123e759d83aca0a4025215ccff566cb651a32c7243a3bfffc'),
  ('3048581','libero_object',{'A128_seed23':98,'B128_seed23':99},2186,'f6ad23ece984823aaf4272e5acde5e1071d413282ddd6df561876b293c43957f')]:
  assert jid not in f['new_action_development_verified_by_job']
  rootrel='results/formal_main_v2/downstream_reviews/'+jid+'.json';root=rd(rootrel,rootsha);j=indjobs[jid]
  assert root['status']==j['status']=='passed' and root['scientific_complete'] and root['suite']==suite
  assert root['completed_trials']==j['trials']==200 and j['unique_initial_states']==100 and j['allocated_GPU_seconds']==gpusec
  assert j['root_receipt']==ref(rootrel) and j['raw_start_result_pairs_exact'] and j['full_original_consumer_reconstruction_passed']
  rs=root['reconstructed_summary'];assert {k:v['successes'] for k,v in rs['methods'].items()}==successes
  assert (j['A_success'],j['B_success'])==(successes['A128_seed23'],successes['B128_seed23'])
  pair=rs['paired_AB']['k128_seed23'];assert pair['completed_pairs']==100 and len(pair['results'])==100
  assert abs(pair['B_minus_A_success_rate']*100-j['B_minus_A_pp'])<1e-10
  ledger=j['raw_ledger'];assert h(R/ledger['path'])==h(P/ledger['path'])==ledger['sha256']
  t0=j['t0_token_diagnostics'];assert t0['paired_observations']==100 and t0['all_t0_observation_hashes_equal']
  for diag in j['offline_validation_diagnostics'].values():rd(diag['validation_ref']['path'],diag['validation_ref']['sha256'])
  entry=dict(job_id=jid,suite=suite,seed=23,visual_tokens=128,completed_trials=200,unique_initial_states=100,
   successes=successes,B_minus_A_percentage_points=j['B_minus_A_pp'],paired_outcomes=j['discordance'],per_task=j['per_task'],
   root_review=ref(rootrel),independent_review=indref,independent_review_scope='Exact original joint independent report, jobs member selected by job_id; no new independent review invented.',
   raw_ledger=ledger,GPU_seconds=gpusec,GPU_cost_scope='Existing allocation counted once in global Slurm total; not added a second time on acceptance.',
   initial_observation_token_overlap_mean=t0['mean_intersection_over_128'],initial_observation_token_Jaccard_mean=t0['mean_Jaccard'],
   token_overlap_scope='Only100 equal-hash paired initial observations; later divergent observations not paired.',
   offline_validation_diagnostics=j['offline_validation_diagnostics'],action_semantics_sha256=root['action_semantics_sha256'],
   no_legacy_semantics_equivalence_claimed=True,whole_suite_development_complete=False,O2A_complete=False)
  f['new_action_development_verified_by_job'][jid]=entry;newly.append(entry)
  row=next(x for x in f['nonLong_development_submissions_1032'] if x['job_id']==jid)
  assert row['completed_trials_accepted']==0
  row.update(completed_trials_accepted=200,observed_status='COMPLETED',scientific_terminal_acceptance_pending=False,terminal_root_review=ref(rootrel),terminal_independent_review=indref)
 current=f['new_action_development_verified_by_job'];assert sum(v['completed_trials'] for v in current.values())==2000
 states_by_suite={}
 for jid,entry in current.items():
  rr=entry['root_review'];data=rd(rr['path'],rr['sha256']);su=data['suite'];states=states_by_suite.setdefault(su,set())
  for pair in data['reconstructed_summary']['paired_AB'].values():
   states.update(x['state_trial_id'] for x in pair['results'])
 assert {k:len(v) for k,v in states_by_suite.items()}=={'libero_10':100,'libero_spatial':100,'libero_object':100}
 f['completed_development_trials']+=400;f['current_action_development_trial_count']=2000;f['current_action_development_unique_initial_states']=300
 f['current_action_development_unique_initial_states_by_suite']={k:len(v) for k,v in states_by_suite.items()}
 assert f['historical_other_action_semantics_development_trials']==1212 and f['Long22_development_statistics']['explicit_legacy_equivalent_trials']==600
 stats=save(B+'/nonLong_seed23_development_diagnostics.json',dict(schema='formal_main_v2',kind='accepted_single_seed_nonLong_development_diagnostics',jobs=newly,
  total_trials=400,unique_initial_states=200,all_job_GPU_seconds=4551,GPU_cost_already_in_Slurm_total=True,
  per_task_and_full_paired_trials=ref(E+'/nonLong_terminal_independent/paired_development_states.json'),source_independent=indref,
  observation_scope='Initial paired observations only for token overlap; validation hard-pruning L1 only for action error.',
  inference='One seed each, Spatial B-A -1pp and Object +1pp. Does not establish stable gain, equivalence, final success or latency tradeoff.',
  bootstrap_three_seed_claimed=False,O2A_measured=False,final_results=False))
 f['latest_new_action_development_verified']=stats
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['unknown'] and not cap['findings'] and len(cap['occupied'])<=8
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 submissions=[]
 for jid,suite,seed,label,apin in [
  ('3049132','libero_spatial',41,'Spatial','c657885d23b4b7741a3b99227f3c12dcda492c4c0fd2ae1d0d9dbfc928b2dc60'),
  ('3049172','libero_object',41,'Object','3c3531e1d721dd357c5df0db7582334b5b45748ff1b0034f3685ed23ae8d7f8a'),
  ('3049191','libero_goal',23,'Goal','efcfa42b97d4d780999f344f8024ff369d5f466825b25d7119ad0c118cbfa117')]:
  job=next(j for j in s['registered_jobs'] if str(j['job_id'])==jid)
  assert sum(str(j['job_id'])==jid for j in s['registered_jobs'])==1 and job['suite']==suite
  methods=['A128_seed'+str(seed),'B128_seed'+str(seed)];assert job['method_ids']==methods
  rec=rd(B+'/'+label+jid+'_pending_reconciliation.json');assert rec['status']=='exact_original_ACK_job_reconciled' and rec['new_submissions']==0
  authpath='results/formal_main_v2/execution/nonLong_action_v1_1220/'+suite+'_k128_seed'+str(seed)+'/submission_authorization.json'
  rd(authpath,apin);ad='results/formal_main_v2/downstream_gateway/'+apin
  assert rd(ad+'/sbatch_result.json')['stdout']==jid+'\n' and ctl['downstream_reservations_consumed'][apin]['job_id']==jid
  assert rd(ad+'/committed.json')['root_reconciliation']==ref(B+'/'+label+jid+'_pending_reconciliation.json')
  assert (R/job['invocation']).read_bytes()==(P/job['invocation']).read_bytes()
  submissions.append(dict(job_id=jid,suite=suite,seed=seed,method_ids=methods,planned_trials=200,completed_trials_accepted=0,
   unique_development_initial_states=100,authorization=ref(authpath),root_reconciliation=ref(B+'/'+label+jid+'_pending_reconciliation.json'),
   independent_submission_review=SUB_REVIEW,original_failed_transaction=ref(ad+'/failed_transaction.json'),original_ACK=ref(ad+'/sbatch_result.json'),
   observed_status=obs['rows'][jid]['status'],scientific_terminal_acceptance_pending=True,duplicate_submissions=0,final_evaluation_enabled=False))
 assert 'nonLong_development_submissions_1220' not in f;f['nonLong_development_submissions_1220']=submissions
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost']['allocated_gpu_seconds']
 s['current_round_cost'].update(allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied'])
 inventory=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 assert len(inventory['files'])==173
 for name,pin in inventory['files'].items():assert h(R/name)==h(P/'snapshots/formal_main_v2_run_564be0995e'/name)==pin
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 summary=save(B+'/summary_after_dispatch.json',dict(schema='formal_main_v2',kind='nonLong400_accepted_next600_dispatched',utc=now,
  state_before_sha256=before,root_independent_complete=64,total_training_arms=72,root_independent_updates=321000,
  completed_by_suite={'libero_10':18,'libero_spatial':18,'libero_object':16,'libero_goal':12},new_development_trials=400,
  raw_historical_and_current_development_trials=3212,current_action_development_trials=2000,current_action_unique_initial_states=300,
  unique_current_initial_states_by_suite={k:len(v) for k,v in states_by_suite.items()},explicit_legacy_equivalent_Long_trials=600,
  compatible_current_and_explicit_legacy_trials=2600,legacy1212_preserved_and_not_relabelled=True,
  accepted_jobs=newly,diagnostics=stats,new_submissions=submissions,active_GPU_jobs=len(cap['occupied']),capacity=cap,scheduler=obs,
  allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,includes_all_registered_allocations=True,cost_is_final=False,
  controller='3034538',controller_owner_id=ctl['owner_id'],pending=None,reserved_GPU_slots=0,new_final_trials=0,
  final_completed=0,final_expected=35200,final_release=False,source173_unchanged=True,
  lock_contention_before_submission=dict(Object='First invocation failed before writer lock, no pending/invocation/audit/job; rechecked then original gateway invoked once more with new transport audit.',Goal='Same bounded pre-lock retry; no sbatch from first invocation.'),
  scientific_settings_changed=False,automatic_expansion=False))
 f['latest_capacity_refill']=summary
 s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']=stamp[:10];s['last_root_supervision_snapshot']=summary;s['last_root_health_check']=summary;s['last_healthy_supervision']=summary
 s['current_work']=f"64/72 root+independent training groups;321000 reviewed updates. New400 development accepted (Spatial128seed23 A97/B96,Object A98/B99). New600 dispatched3049132/3049172/3049191 once. {len(cap['occupied'])} occupied GPU;{seconds/3600:.3f}GPUh. Current2000+explicitLong600 compatible development,300 unique states across3suites. Final0/35200sealed."
 s['next_actions']=[
  'Leave healthy normal training and development running; use scheduled supervision, no continuous polling.',
  'Review genuine terminals for remaining8 training arms and the registered development jobs; never resubmit3049132/3049172/3049191 or prior3048609.',
  'Fill actual free slots with remaining preregistered suite/budget/seed development only after original plan, checkpoint, independent readiness and duplicate/capacity gates.',
  'Retain single-seed Spatial -1pp/Object +1pp and Long128 three-seed negative2.67pp; no tuning or equivalence claim.',
  'Final35200 and complete same-checkpointO2A/components remain behind original globalfreeze/release gates; no sealed values read.']
 s['next_allowed_action']=s['next_actions'][0]
 assert ctl==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 assert f['completed_training_pairs']==old['formal_main_progress']['completed_training_pairs'] and f['automatic_machine_verified_pairs']==old['formal_main_progress']['automatic_machine_verified_pairs']
 put(B+'/root_operations/integrate_1220_v2.py',Path(__file__).read_bytes())
 c.atomic_json(sp,s,before)
 brief=f"{stamp}：训练仍为64/72组双审完成；新增400条开发验收，Spatial128 seed23 A97%/B96%，Object128 seed23 A98%/B99%，均为100个唯一配对开发初态的单seed结果。另3批600条已按原配置一次提交（3049132/3049172/3049191）；当前{len(cap['occupied'])}GPU占槽，累计{seconds/3600:.3f}GPU小时（非最终）。最终0/35200继续封存。见[本轮汇总](../{B}/summary_after_dispatch.json)及[非Long开发结果](正式非Long开发结果.md)。"
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记']:
  p=R/'docs'/f'{name}.md';prior=p.read_text();first,rest=prior.split('\n',1);p.write_text(first+'\n\n'+brief+'\n'+rest)
 lines=['# 正式非Long开发结果','',f'更新：{stamp}。固定主预算128、seed23，全部10任务×10开发初态。以下仅为当前动作执行入口的开发诊断，全部种子/预算及完整O2A尚未齐备。最终初态仍封存。','',
 '| 套件 | A成功/100 | B成功/100 | B−A (pp) | t0交集/128 | t0 Jaccard | GPU秒 |','|---|---:|---:|---:|---:|---:|---:|']
 for j in newly:
  label={'libero_spatial':'Spatial','libero_object':'Object'}[j['suite']]
  lines.append(f"| {label} | {j['successes']['A128_seed23']} | {j['successes']['B128_seed23']} | {j['B_minus_A_percentage_points']:+.0f} | {j['initial_observation_token_overlap_mean']:.6f} | {j['initial_observation_token_Jaccard_mean']:.6f} | {j['GPU_seconds']} |")
 lines+=['','400条原始试验共4551GPU秒，已包含在Slurm总账；本轮验收不重复加费。训练成本保留在原训练收据。单seed差异不能证明稳定收益或等效，也不能据此声称成功率—延迟折中改善。t0仅比较相同hash的初始观测，后续轨迹分歧不作同观测配对。','',
 '| 套件/臂 | 选中update | 硬验证teacher L1 | 硬验证示范L1 | 验证窗口 |','|---|---:|---:|---:|---:|']
 for j in newly:
  for arm,dg in j['offline_validation_diagnostics'].items():
   lines.append(f"| {j['suite']}/{arm} | {dg['selected_update']} | {dg['hard_validation_teacher_L1_task_equal']:.8f} | {dg['hard_validation_demonstration_L1_task_equal']:.8f} | {dg['validation_windows']} |")
 lines+=['','上表是既定validation选中checkpoint的离线硬剪枝诊断，非闭环动作误差，未用开发成功率重选模。','',
 '| 套件 | task_id | A成功/10 | B成功/10 | B−A (pp) |','|---|---:|---:|---:|---:|']
 for j in newly:
  for t in j['per_task']:lines.append(f"| {j['suite']} | {t['task_id']} | {t['A_success']} | {t['B_success']} | {t['B_minus_A_pp']:+.0f} |")
 lines+=['','完整任务名称、逐初态配对、token重合和原始日志见本轮JSON及原审计。历史Object600和Spatial12仍单列；未证明其语义等价，不能混入当前结果。Long已接受的显式等价600条只复用、不重复执行或加分母。','',
 f'[本轮诊断](../{stats["path"]}) · [原始独审](../{indref["path"]}) · [计划与提交](../{B}/summary_after_dispatch.json)','']
 put('docs/正式非Long开发结果.md','\n'.join(lines).encode())
 print(json.dumps(dict(summary=summary,accepted400=True,new600=True,training64=True,GPU_hours=seconds/3600,occupied=len(cap['occupied']),state_after_sha256=h(sp))))

"""Root-only integration. Default private preview; explicit --apply required.
No GPU submissions, checkpoint reads, sealed values, or source changes.
"""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone,timedelta
import argparse,copy,hashlib,importlib.util,json,os,sys,uuid
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T2218'
E='results/formal_main_v2/engineering/supervision_delivery_20261020T1418/terminal_independent'
PRIVATE='.local/integration_candidate_20261020T1418'
PINS={
 'independent':(E+'/independent_review.json','ad8c588b38df5d774f7da678ff75b2931743156de8b1e4d373f1f5358c22fead'),
 'statistics':(E+'/development_statistics.json','26db7c37f100857e7e789dc7fbea74e0c2c2728e864a8b35f8fdde7ddc97c1cd'),
 'goal_diagnosis':(E+'/Goal256_seed17_failure_diagnosis.json','40ba1fb5d72cb85ce9298f8263174f5d46a5e730ba4b8da98fc690c3c1e39abc'),
 'goal_failure':(B+'/3049679_root_review_failure_20261020T1418.json','49b226c91f99cd9fd3584ab645992244794f4d720e0128d9ab693e82bcca6793'),
 'object_failure':('results/formal_main_v2/engineering/supervision_delivery_20261020T1418/plan_author/Object256seed23_original_factory_block.json','6176cc4caf5266bd76a743e5e6bdfa79b208d7cb86f14e2d4b5092a2c54037fd'),
 'pull':('results/formal_main_v2/pulls/20261020T142621Z_02800e667ffb/receipt.json','20139adbe331ea4d217e7011f22b4e3d6e008f6c59e87ff1d00a0735ef290493'),
 'terminal_snapshot':(B+'/terminal_jobs_snapshot.json','4417ed6bc2d89611d6507d1ad2cabc544c89faa8b1eb0340cca563706322ba1a'),
 'inventory':('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'),
 'paired':(E+'/paired_development_states.json','fc9f11c9217df2c1cdec615f3a223b43a06997051049cfd325892f4ab6c67d0b'),
 'matrix':(E+'/Goal128_paired_matrix.json','35104178cba959a5650b0e5fb7a5b06d6cdf27704e7a0602d3d649b8bfecf362'),
 'root_bootstrap':(B+'/Goal128_root_bootstrap_recomputation.json','4fa41c33af982608618ed7eeb85abbd646abedd2302c2c0a185cf4db65033dd1')}
JOBS=[
 ('3049132','libero_spatial',128,41,2315,'d705c821e83b0bc9121102c62fc6aeb4917b490b1a8b22a647f7851f03b75910'),
 ('3049172','libero_object',128,41,2213,'2aba593e2014ee9996083a35dc3185376e81af49e4896141fd78e1fe068bf138'),
 ('3049622','libero_goal',128,41,2039,'ffc074a3cc374a7d348488bdac0ac28c5575865630dd551ba97858a841671c23'),
 ('3049632','libero_spatial',256,17,2351,'a07278ca96d6c6c461283b590ba09e1c9acd9427bac40a7380a8f244a64ee56b'),
 ('3049657','libero_object',256,17,2198,'3c063f479ae499d57aa38ae6682141abfbcc3f3c5a66291a0c450fd42e66fbec')]
SUMMARY=B+'/summary_after_dispatch.json';BLOCKERS=B+'/downstream_blockers_20261020T1418.json';STATS=B+'/accepted_nonLong_development_diagnostics.json'
DOCS=['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式非Long开发结果','正式Goal主预算开发结果']
def require(ok,msg):
 if not ok:raise ValueError(msg)
def path(rel,root=R):
 q=PurePosixPath(rel);require(rel and not q.is_absolute() and '..' not in q.parts and '\\' not in rel,'unsafe path')
 p=root.joinpath(*q.parts)
 for z in [p,*p.parents]:
  if z==root:break
  require(not z.is_symlink(),'symlink path')
 require(p.resolve().is_relative_to(root.resolve()),'escaped root');return p
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for part in iter(lambda:f.read(1<<20),b''):h.update(part)
 return h.hexdigest()
def rawjson(x):return (json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def rd(rel,pin=None):
 p=path(rel)
 if pin:require(sha(p)==pin,'SHA mismatch '+rel)
 return json.loads(p.read_bytes())
def ref(rel,pin=None):return dict(path=rel,sha256=pin or sha(path(rel)))
def pref(k):return ref(*PINS[k])
def mod(rel,pin,name):
 require(sha(path(rel))==pin,'module SHA mismatch');sp=importlib.util.spec_from_file_location(name,path(rel));m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def inputs():
 d={k:rd(*v) for k,v in PINS.items()};j=d['independent'];g=d['goal_diagnosis'];o=d['object_failure'];st=d['statistics']
 require(j['status']=='passed' and j['totals']['trials']==1000 and j['totals']['allocated_gpu_seconds']==11116,'terminal totals')
 require(set(j['jobs'])=={x[0] for x in JOBS} and j['held_job_ids']==['3049679'],'terminal scope')
 require(j['source173_R_and_S_unchanged'] and not j['checkpoint_bytes_read'] and not j['sealed_final_values_read'] and j['new_GPU_jobs']==0,'audit scope')
 require(j['paired_states']['sha256']==PINS['paired'][1],'paired rows')
 require(g['status']=='confirmed_blocker_no_scientific_acceptance' and g['accepted_trials']==0 and g['retained_trials']==200 and g['actual_GPU_seconds']==2034,'held scope')
 require(g['original_guard_reproduced']['message']=='Paired initial observation differs across methods/attempts' and not g['existing_raw_arrays_available'],'held guard')
 require(g['root_failure_ref']['sha256']==PINS['goal_failure'][1] and g['next_bounded_engineering_proposal']['status']=='proposed_not_run_not_scientific_trial','proposal not executed')
 require(o['status']=='blocked_no_bypass' and not o['copy_only_repair_available'] and o['missing_in_ordinary_metadata_history']==['3028460'] and o['ordinary_metadata_history_job_ids']==['3039258','3042627'],'Object preserved failure')
 require(st['new_GPU_jobs']==0 and not st['sealed_final_values_read'] and not st['final_release'] and not st['latency_executed'],'stats scope')
 require(st['suites']['libero_goal']['available_seeds']==[17,23,41] and st['suites']['libero_goal']['bootstrap_repeats']==10000,'Goal seeds')
 for suite in ['libero_spatial','libero_object']:
  v=st['suites'][suite];require(v['available_seeds']==[23,41] and v['missing_seeds']==[17] and not v['bootstrap_computed'],'no fabricated three seeds')
 entries=[]
 for jid,suite,budget,seed,secs,pin in JOBS:
  rel='results/formal_main_v2/downstream_reviews/'+jid+'.json';rr=rd(rel,pin);v=j['jobs'][jid]
  require(rr['status']==v['status']=='passed' and rr['scientific_complete'] and rr['suite']==v['suite']==suite,'review')
  require(rr['completed_trials']==v['trials']==200 and v['unique_initial_states']==100 and v['allocated_GPU_seconds']==secs and v['seed']==seed and v['A_B_visual_tokens']==budget,'identity')
  require(v['root_receipt']==ref(rel,pin) and v['raw_start_result_pairs_exact'] and v['full_original_consumer_reconstruction_passed'],'original consumer')
  rs=rr['reconstructed_summary'];successes={k:x['successes'] for k,x in rs['methods'].items()};a=f'A{budget}_seed{seed}';b=f'B{budget}_seed{seed}'
  require(successes==v['successes'] and set(successes)=={a,b} and (v['A_success'],v['B_success'])==(successes[a],successes[b]),'success reconstruction')
  pair=rs['paired_AB'][f'k{budget}_seed{seed}'];require(pair['completed_pairs']==len(pair['results'])==100 and abs(pair['B_minus_A_success_rate']*100-v['B_minus_A_pp'])<1e-9,'paired summary')
  lr=v['raw_ledger'];require(sha(path(lr['path']))==sha(path(lr['path'],P))==lr['sha256'],'R/P ledger')
  t=v['t0_token_diagnostics'];require(t['paired_observations']==len(t['rows'])==100 and t['all_t0_observation_hashes_equal'],'t0 rows')
  for dg in v['offline_validation_diagnostics'].values():rd(dg['validation_ref']['path'],dg['validation_ref']['sha256'])
  entries.append(dict(job_id=jid,suite=suite,seed=seed,visual_tokens=budget,completed_trials=200,unique_initial_states=100,successes=successes,
   B_minus_A_percentage_points=v['B_minus_A_pp'],paired_outcomes=v['discordance'],per_task=v['per_task'],root_review=ref(rel,pin),independent_review=pref('independent'),
   independent_review_scope='Exact report member selected by job_id; post-integration review not yet claimed.',raw_ledger=lr,GPU_seconds=secs,
   GPU_cost_scope='Existing allocation included once in global Slurm total; acceptance adds zero GPU.',
   initial_observation_token_overlap_mean=t['mean_intersection_over_budget'],initial_observation_token_Jaccard_mean=t['mean_Jaccard'],
   token_overlap_scope='100 equal-hash t0 observations only; divergent later trajectories not paired.',offline_validation_diagnostics=v['offline_validation_diagnostics'],
   action_semantics_sha256=rr['action_semantics_sha256'],reference_trials=0,AB_trials=200,full_action_chunks=v['full_action_chunks'],executed_control_actions=v['executed_control_actions'],
   no_legacy_semantics_equivalence_claimed=True,whole_suite_development_complete=False,O2A_complete=False))
 inventory=d['inventory'];require(len(inventory['files'])==173,'frozen source count')
 for rel,pin in inventory['files'].items():require(sha(path(rel))==sha(path('snapshots/formal_main_v2_run_564be0995e/'+rel,P))==pin,'frozen source changed')
 d['entries']=entries;return d

def precondition(s):
 f=s['formal_main_progress'];c=s['autonomous_training_v1']
 require(s['pending_submission'] is None and c['reserved_GPU_slots']==0 and c['root_submission_hold'] is None,'pending/hold/reservation must be resolved, never cleared here')
 require(f['root_and_independent_completed_arms']==64 and f['root_and_independent_reviewed_arm_updates']==321000,'training acceptance changed; re-audit candidate')
 require(f['completed_development_trials']==4012 and f['current_action_development_trial_count']==2800,'accepted counts changed or integration already applied')
 require(f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created'],'final sealed')
 require('nonLong_development_submissions_1418' not in f and 'downstream_blockers_20261020T1418' not in f,'duplicate integration')
 require(c['controller_job_id']=='3034538','controller changed; re-audit')
def verify_dispatch(s,dispatch):
 require(dispatch['status']=='all_selected_requests_registered_once' and dispatch['new_GPU_jobs']==3 and dispatch['new_planned_trials']==600 and dispatch['new_completed_trials']==0,'dispatch totals')
 require(dispatch['pending'] is None and dispatch['reserved_GPU_slots']==0 and not dispatch['duplicate_stage_keys'] and dispatch['exact_ACK_reconciliation_no_resubmissions'],'dispatch reconciliation')
 rows=dispatch['submissions'];expected={('libero_spatial',256,23),('libero_spatial',256,41),('libero_object',256,41)}
 require(len(rows)==3 and {(x['suite'],x['budget'],x['seed']) for x in rows}==expected and len({x['job_id'] for x in rows})==3,'exact three clean groups')
 for row in rows:
  jid=row['job_id'];matches=[j for j in s['registered_jobs'] if str(j['job_id'])==jid];require(len(matches)==1,'registered job missing/duplicate');j=matches[0]
  require(j['suite']==row['suite'] and j['method_ids']==row['method_ids'],'registered identity')
  require(row['planned_trials']==200 and row['completed_trials_accepted']==0 and row['scientific_terminal_acceptance_pending'] and not row['automatic_retry'],'premature acceptance/retry')
  for key in ['authorization','invocation','exact_original_ACK','root_acceptance','pre_execution_independent','submission','root_reconciliation','original_accounting_delay']:
   r=row[key];rd(r['path'],r['sha256'])
  rec=rd(row['root_reconciliation']['path'],row['root_reconciliation']['sha256']);require(rec['status']=='exact_original_ACK_job_reconciled' and rec['new_submissions']==0,'reconciliation')
  ack=rd(row['exact_original_ACK']['path'],row['exact_original_ACK']['sha256']);require(ack['stdout']==jid+'\n','exact ACK')
  pin=row['authorization']['sha256'];base='results/formal_main_v2/downstream_gateway/'+pin
  require(s['autonomous_training_v1']['downstream_reservations_consumed'][pin]['job_id']==jid,'consumed reservation')
  require(rd(base+'/committed.json')['root_reconciliation']==row['root_reconciliation'],'commit receipt')
  require(sha(path(j['invocation']))==sha(path(j['invocation'],P))==row['invocation']['sha256'],'R/P invocation')
 return copy.deepcopy(rows)
def accept_terminals(s,d):
 f=s['formal_main_progress'];cur=f['new_action_development_verified_by_job']
 for e in d['entries']:
  jid=e['job_id'];require(jid not in cur,'already accepted')
  group='nonLong_development_submissions_1220' if jid in {'3049132','3049172'} else 'nonLong_development_submissions_1317'
  rows=[x for x in f[group] if x['job_id']==jid];require(len(rows)==1 and rows[0]['completed_trials_accepted']==0,'original pending record')
  rows[0].update(completed_trials_accepted=200,observed_status='COMPLETED',scientific_terminal_acceptance_pending=False,terminal_root_review=e['root_review'],terminal_independent_review=e['independent_review']);cur[jid]=copy.deepcopy(e)
 require('3049679' not in cur,'held job already accepted')
 held=[x for x in f['nonLong_development_submissions_1317'] if x['job_id']=='3049679'];require(len(held)==1 and held[0]['completed_trials_accepted']==0,'held record')
 held[0].update(observed_status='COMPLETED',scientific_terminal_acceptance_pending=True,terminal_review_status='HOLD_initial_observation_mismatch',terminal_root_failure=pref('goal_failure'),terminal_independent_diagnosis=pref('goal_diagnosis'),retained_unaccepted_trials=200,GPU_seconds_retained=2034,automatic_retry=False)
 require(sum(x['completed_trials'] for x in cur.values())==3800,'accepted total')
 bysuite={}
 for e in cur.values():
  rr=e['root_review'];v=rd(rr['path'],rr['sha256']);states=bysuite.setdefault(v['suite'],set())
  for pair in v['reconstructed_summary']['paired_AB'].values():states.update(x['state_trial_id'] for x in pair['results'])
 expected={x:100 for x in ['libero_10','libero_spatial','libero_object','libero_goal']};require({k:len(v) for k,v in bysuite.items()}==expected,'unique initials')
 f['completed_development_trials']=5012;f['current_action_development_trial_count']=3800;f['current_action_development_unique_initial_states']=400;f['current_action_development_unique_initial_states_by_suite']=expected
 require(f['historical_other_action_semantics_development_trials']==1212 and f['Long22_development_statistics']['explicit_legacy_equivalent_trials']==600,'legacy truth retained')
 return expected

def prepare(s,before,d,dispatch,dispatchref,obs,cap,now):
 old=copy.deepcopy(s);s=copy.deepcopy(s);precondition(s);rows=verify_dispatch(s,dispatch)
 require(not cap['unknown'] and not cap['findings'] and len(cap['occupied'])<=8,'fresh capacity')
 require(obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0,'controller health')
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 require(seconds>=s['current_round_cost']['allocated_gpu_seconds'],'GPU accounting regressed')
 for jid,_,_,_,sec,_ in JOBS:
  row=obs['rows'][jid];require(row['status']=='COMPLETED' and row['exit_code']=='0:0' and row['gpus']==1 and row['elapsed_seconds']==sec,'terminal accounting')
 row=obs['rows']['3049679'];require(row['status']=='COMPLETED' and row['exit_code']=='0:0' and row['gpus']==1 and row['elapsed_seconds']==2034,'held accounting')
 expected=accept_terminals(s,d);f=s['formal_main_progress'];f['nonLong_development_submissions_1418']=rows
 g=d['goal_diagnosis'];o=d['object_failure']
 block=dict(schema='formal_main_v2',status='two_scoped_blockers',
  Goal256_seed17=dict(status='HOLD',job_id='3049679',retained_trials=200,accepted_trials=0,actual_GPU_seconds=2034,
   scope='Pause new Goal scientific development until cause and bounded engineering repair independently accepted; retain validGoal128.',
   root_failure=pref('goal_failure'),independent_diagnosis=pref('goal_diagnosis'),cause_status=g['cause_status'],mismatching_initials=g['mismatching_states'],
   next_bounded_engineering_proposal=g['next_bounded_engineering_proposal'],proposal_run=False,scientific_retry_authorized=False),
  Object256_seed23=dict(status='HOLD_original_downstream_metadata_consumer',pair='libero_object_k256_seed23',root_training_completion_unchanged=True,
   evidence=pref('object_failure'),reason=o['reason'],normal_history_job_ids=o['ordinary_metadata_history_job_ids'],startup_failure_review=o['startup_failure_review'],
   required_future_work=o['required_future_work'],fake_metadata_repair_allowed=False,new_GPU_seconds=0,new_scientific_trials=0),
  existing_failure_costs_retained=True,no_gate_waiver=True,no_new_jobs_by_integration=True,sealed_final_values_read=False)
 suites={}
 for suite,v in d['statistics']['suites'].items():
  suites[suite]={k:v[k] for k in ['available_seeds','missing_seeds','unique_initial_states','trial_count','means_percent','seed_sample_SD_pp','bootstrap_computed']}
  if 'bootstrap_interval95_pp' in v:suites[suite]['bootstrap_interval95_pp']=v['bootstrap_interval95_pp']
 stats=dict(schema='formal_main_v2',kind='accepted_nonLong_development_diagnostics',new_trials=1000,suites=suites,
  full_seed_task_outcomes_tokens_and_offline_validation_L1=pref('statistics'),terminal_review=pref('independent'),Goal_paired_matrix=pref('matrix'),root_bootstrap_recomputation=pref('root_bootstrap'),
  accepted_jobs_GPU_seconds=11116,held_job_GPU_seconds=2034,costs_already_in_global_Slurm_total=True,development_only=True,
  action_error_scope='Selected checkpoint offline hard validation teacher/demo L1, not closed-loop action error.',no_equivalence_or_O2A_claim=True,final_results=False)
 blockref=ref(BLOCKERS,hashlib.sha256(rawjson(block)).hexdigest());statref=ref(STATS,hashlib.sha256(rawjson(stats)).hexdigest())
 f['downstream_blockers_20261020T1418']=blockref;f['latest_new_action_development_verified']=statref;f['Goal128_three_seed_development_statistics']=statref
 f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied']);s['current_round_cost'].update(allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 summary=dict(schema='formal_main_v2',kind='five_nonLong_terminals_accepted_two_scoped_blockers_three_development_dispatches',utc=now,state_before_sha256=before,
  root_independent_complete=64,total_training_arms=72,root_independent_updates=321000,new_training_groups_accepted=0,completed3043762_not_accepted_here=True,
  new_development_trials=1000,raw_historical_and_current_accepted_development_trials=5012,current_action_development_trials=3800,current_action_unique_initial_states=400,
  unique_current_initial_states_by_suite=expected,explicit_legacy_equivalent_Long_trials=600,compatible_current_and_explicit_legacy_trials=4400,
  historical_other_semantics1212_preserved=True,held_Goal256_job='3049679',held_trials=200,held_trials_in_success_rate_denominator=False,
  accepted_jobs=d['entries'],diagnostics=statref,blockers=blockref,new_submissions=rows,new_planned_trials=600,new_submitted_trials_accepted=0,dispatch=dispatchref,
  active_GPU_jobs=len(cap['occupied']),capacity=cap,scheduler=obs,allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,includes_all_registered_allocations=True,cost_is_final=False,
  controller='3034538',controller_owner_id=s['autonomous_training_v1']['owner_id'],pending=None,reserved_GPU_slots=0,final_completed=0,final_expected=35200,final_release=False,
  source173_unchanged=True,scientific_settings_changed=False,automatic_expansion=False,post_integration_independent_review_pending=True)
 summaryref=ref(SUMMARY,hashlib.sha256(rawjson(summary)).hexdigest());f['latest_capacity_refill']=summaryref
 s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d');s['last_root_supervision_snapshot']=summaryref;s['last_root_health_check']=summaryref
 # Preserve last_healthy_supervision: this delivery includes scoped failures.
 ids=[x['job_id'] for x in rows]
 s['current_work']=f"64/72 root+independent training,321000 reviewed updates. Five jobs accepted1000 development;Goal256s17 original200HOLD. Goal128 three seeds A97.333% B96%,B-A -1.333pp CI[-3.667,+0.667]. Clean256600 dispatched once {ids},not yet accepted. {len(cap['occupied'])}GPU occupied;{seconds/3600:.3f}GPUh. Current3800+explicitLong600 compatible;400unique initials. Final0/35200sealed. Object256s23 metadata blocked."
 s['next_actions']=[
  'Leave healthy training/development to controller and scheduled supervision; no continuous polling or duplicate submission.',
  'Review genuine training terminals including3043762 with original root+independent gates; machine completion alone adds no accepted groups.',
  'Goal256s17 original200HOLD; bounded t0 engineering proposal is not run. No science retry or newGoal development until independent repair acceptance.',
  'Object256s23 ordinary metadata excludes preserved3028460 startup failure. Separate versioned consumer compatibility needs audit; never fake metadata.',
  'Preserve Goal128 three-seed negative1.333pp,Long128 negative2.67pp,partialSpatial/Object23/41. No tuning/equivalence/unmeasured speed claim.',
  'Final35200 and same-checkpoint O2A/components retain globalfreeze/release; sealed final values unread.']
 s['next_allowed_action']=s['next_actions'][0]
 require(s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs'],'controller/registry overwritten')
 require(f['completed_training_pairs']==old['formal_main_progress']['completed_training_pairs'] and f['automatic_machine_verified_pairs']==old['formal_main_progress']['automatic_machine_verified_pairs'],'training fields overwritten')
 return s,summary,{SUMMARY:rawjson(summary),BLOCKERS:rawjson(block),STATS:rawjson(stats),B+'/root_operations/integrate_1418_v1.py':Path(__file__).read_bytes()}

def prepend(raw,text):
 first,sep,rest=raw.partition(b'\n');require(bool(sep),'document heading');return first+b'\n\n'+text.encode()+b'\n\n'+rest

def documents(d,summary,stamp):
 ids=','.join(x['job_id'] for x in summary['new_submissions']);hours=summary['allocated_GPU_hours'];occupied=summary['active_GPU_jobs']
 brief=f"{stamp}：训练仍64/72组双审，本轮不把刚完成的3043762自动计入。新增5批1000条开发验收；Goal256 seed17原200条因t0观测不一致整批HOLD，保留2034GPU秒。Goal128三seed A97.333%/B96.000%，B−A −1.333pp，95%配对簇bootstrap区间[−3.667,+0.667]pp，无等效或实测加速结论。Spatial/Object128目前仅23/41两seed可比。3个已审256组补位600条（{ids}），未计完成。当前{occupied}GPU占槽、累计{hours:.3f}GPU小时，Slurm总账只计一次。当前动作验收3800条，加显式兼容Long旧600为4400条，4套件共400唯一初态；含其他旧语义的验收记录5012条另保留。最终0/35200封存。见[汇总](../{SUMMARY})与[下游阻塞](正式下游阻塞登记_20261020T1418.md)。"
 sections={name:brief for name in DOCS}
 lines=['本轮新增验收均为每方法100条开发试验，不能作为封存最终成绩。','', '| 套件 | tokens | seed | A/100 | B/100 | B−A pp | t0交集/预算 | t0 Jaccard |','|---|---:|---:|---:|---:|---:|---:|---:|']
 for e in d['entries']:
  b=e['visual_tokens'];seed=e['seed'];lines.append(f"| {e['suite']} | {b} | {seed} | {e['successes'][f'A{b}_seed{seed}']} | {e['successes'][f'B{b}_seed{seed}']} | {e['B_minus_A_percentage_points']:+.0f} | {e['initial_observation_token_overlap_mean']:.6f} | {e['initial_observation_token_Jaccard_mean']:.6f} |")
 lines+=['','128预算：Spatial已验收23/41为97/96与95/96，两seed描述均值A/B均96%；Object为98/99与97/98，均值97.5%/98.5%。历史seed17未通过当前动作语义接纳，不能补成三seed均值或区间。Spatial旧12条、未执行的588补充及Object旧失败记录保留，不纳入当前比较。','',
  f'Goal三seed见[Goal开发结果](正式Goal主预算开发结果.md)。全部逐任务、逐seed与离线teacher/示范L1见[统计原件](../{E}/development_statistics.json)。L1是选中checkpoint的离线硬验证诊断，不是闭环动作误差；开发成败不参与选模。Token重合仅在同t0观测上配对。','',
  '5个验收作业11116GPU秒、Goal隔离作业2034GPU秒均已纳入Slurm总账，不重复累加。下面保留历史记录。']
 sections['正式非Long开发结果']=brief+'\n\n'+'\n'.join(lines)
 g=d['statistics']['suites']['libero_goal'];lines=['当前三seed共用100个唯一Goal开发初态，A/B共600条，四个无训练seed参考共享400条。','',
  '| seed | A/100 | B/100 | B−A pp | t0交集/128 | t0 Jaccard |','|---|---:|---:|---:|---:|---:|']
 for v in g['per_seed']:lines.append(f"| {v['seed']} | {v['A_successes']} | {v['B_successes']} | {v['B_minus_A_pp']:+.0f} | {v['token_intersection_over_128']:.6f} | {v['token_Jaccard']:.6f} |")
 lines+=['','三seed均值A97.333%/B96.000%，B−A −1.333pp；种子间样本SD（ddof=1）分别0.577、2.000、2.517pp。固定10000次任务内初态簇bootstrap，RNG seed20261016；抽中初态携带三seed与A/B，任务等权。95%百分位区间：A[94.667,99.667]%，B[92.667,98.667]%，B−A[−3.667,+0.667]pp。100初态不因seed重复增至300。','',
  '共享Dense97/100。A−Dense +0.333pp、区间[−2.667,+3.667]pp；B−Dense −1.000pp、区间[−4.333,+2.000]pp。均未满足区间下界严格高于−2pp的开发诊断目标，不能解释为等效。没有同checkpoint完整O2A，尚不能判断成功率—延迟折中。','',
  '| seed | task_id | A/10 | B/10 | B−A pp |','|---|---:|---:|---:|---:|']
 for t in g['per_task']:lines.append(f"| {t['seed']} | {t['task_id']} | {t['A_successes']} | {t['B_successes']} | {t['B_minus_A_pp']:+.0f} |")
 lines+=['','| seed/臂 | 选中update | 硬验证teacher L1 | 硬验证示范L1 | 验证窗口 |','|---|---:|---:|---:|---:|']
 for v in g['per_seed']:
  for arm,dg in v['offline_validation_diagnostics'].items():lines.append(f"| {v['seed']}/{arm} | {dg['selected_update']} | {dg['hard_validation_teacher_L1_task_equal']:.8f} | {dg['hard_validation_demonstration_L1_task_equal']:.8f} | {dg['validation_windows']} |")
 lines+=['','L1为原validation选中checkpoint的离线硬剪枝诊断，不是闭环动作误差；开发成败不参与选模。当前未来监督未显示稳定收益，不据此调参或堆模块。Goal256 seed17原200条整批HOLD，不能混入128或256成功率。','',
  f'[固定配对矩阵](../{E}/Goal128_paired_matrix.json)；[全部配对与诊断](../{E}/development_statistics.json)；[root独立重算收据](../{PINS["root_bootstrap"][0]})。下面保留此前两seed与参考历史。']
 sections['正式Goal主预算开发结果']=brief+'\n\n'+'\n'.join(lines)
 docs={};pins={}
 for name in DOCS:
  rel='docs/'+name+'.md';raw=path(rel).read_bytes();pins[rel]=hashlib.sha256(raw).hexdigest();docs[rel]=prepend(raw,sections[name])
 lines=['# 正式下游阻塞登记 20261020T1418','',
  'Goal256 seed17作业3049679原200条整批HOLD，验收0条、分配2034GPU秒保留。task2开发source index42在同一登记初态/seed/wait下A/B t0观测hash不等。其余99对一致，不能据此删除单条或接受其余199条。现有日志无分量原数组，不能凭相同成败放行。已验收Goal128三seed与参考在该初态hash一致，原有效128结果保留。','',
  '下一步仅登记工程建议，尚未运行：固定task2/source42、原A/B checkpoint与环境，3次A→B/B→A顺序，共12次reset/t0查询；最多1GPU/30分钟，不执行10等待动作以外的policy动作。记录两相机及3个proprio分量数组原值、dtype/shape/hash、reset/逐等待状态、predict前后输入、RNG与模型加载顺序。原因/修复独审前不重跑科学试验、不恢复新Goal开发。','',
  'Object256 seed23训练双审身份不变，但原下游consumer要求所有allocation覆盖普通metadata。3028460为真实CUDA启动失败，普通history只有3039258/3042627，失败证据独立保存在startup_failure_history。无法只复制文件修复，不得伪造普通metadata；推进须有保留原入口/失败/成本的版本化consumer兼容修正与独审，当前未提交该组开发。','',
  '健康训练和已审其他开发继续。两项HOLD不改变损失、跨度、任务、seed、初态划分、选中checkpoint或最终封存门槛。','',
  f'[精确阻塞证据与未执行方案](../{BLOCKERS})；[Goal独审原件](../{E}/Goal256_seed17_failure_diagnosis.json)；[Object原consumer失败](../{PINS["object_failure"][0]})。','']
 docs['docs/正式下游阻塞登记_20261020T1418.md']='\n'.join(lines).encode();return docs,pins

def write_new(rel,raw):
 p=path(rel);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def replace_document(rel,raw,pin):
 p=path(rel);require(sha(p)==pin,'document CAS '+rel);tmp=p.with_name(p.name+'.'+uuid.uuid4().hex+'.partial')
 with tmp.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 require(sha(p)==pin,'document changed before replace');os.replace(tmp,p)
def run(args):
 c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','integrate1418controller')
 d=inputs();dispatchref=ref(args.dispatch_ref,args.sha);dispatch=rd(args.dispatch_ref,args.sha)
 with c.exclusive_lock(path('results/experiment_supervisor/.writer.lock')):
  sp=path('results/experiment_supervisor/state.json');before=sha(sp);s=rd('results/experiment_supervisor/state.json');precondition(s);verify_dispatch(s,dispatch)
  obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,s['autonomous_training_v1']['controller_job_id'])
  now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
  after,summary,outputs=prepare(s,before,d,dispatch,dispatchref,obs,cap,now);docs,pins=documents(d,summary,stamp)
  for rel in outputs:require(not path(rel).exists(),'output exists; reconcile prior transaction '+rel)
  for rel in docs:
   if rel not in pins:require(not path(rel).exists(),'new doc already exists')
  require(sha(sp)==before,'state changed while locked')
  if not args.apply:
   base=PRIVATE+'/preview_'+uuid.uuid4().hex[:12]
   for rel,raw in {**outputs,**docs}.items():write_new(base+'/'+rel,raw)
   write_new(base+'/state_candidate.json',rawjson(after))
   receipt=dict(status='private_preview_only_not_applied',state_before_sha256=before,dispatch=dispatchref,preview_root=base,
    canonical_state_unchanged=sha(sp)==before,canonical_docs_unchanged=all(sha(path(p))==v for p,v in pins.items()),new_GPU_jobs=0,
    accepted_increment=1000,held_unaccepted200=True,current_action3800=True,total_accepted5012=True,compatible4400=True,unique400=True,training64=True,
    new_planned600=True,GPU_hours=summary['allocated_GPU_hours'],occupied=len(cap['occupied']))
   write_new(base+'/receipt.json',rawjson(receipt));print(json.dumps(receipt,ensure_ascii=False));return
  # Immutable intent and exclusive outputs make an interrupted transaction detectable.
  # If interrupted, root must reconcile; never remove intent or blindly apply again.
  intent=dict(schema='formal_main_v2',kind='root_integration_intent',utc=now,state_before_sha256=before,dispatch=dispatchref,
   source=ref(str(Path(__file__).relative_to(R))),state_candidate_sha256=hashlib.sha256(rawjson(after)).hexdigest(),
   writes={rel:hashlib.sha256(raw).hexdigest() for rel,raw in {**outputs,**docs}.items()},previous_document_sha256=pins)
  write_new(B+'/integration_1418_intent.json',rawjson(intent));write_new(B+'/integration_1418_state_before.json',rawjson(s))
  for rel,raw in outputs.items():write_new(rel,raw)
  for rel,raw in docs.items():
   if rel in pins:replace_document(rel,raw,pins[rel])
   else:write_new(rel,raw)
  c.atomic_json(sp,after,before)
  result=dict(status='root_integrated_post_independent_review_pending',state_before_sha256=before,state_after_sha256=sha(sp),dispatch=dispatchref,
   summary=ref(SUMMARY),documents={rel:ref(rel) for rel in docs},controller_registry_unchanged=True,new_GPU_jobs_by_integration=0,
   new_development_trials_accepted=1000,held_trials=200,new_dispatch_trials_accepted=0)
  write_new(B+'/integration_1418_completion.json',rawjson(result));print(json.dumps(result,ensure_ascii=False))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--dispatch-ref',required=True);ap.add_argument('--sha',required=True);ap.add_argument('--apply',action='store_true',help='Root explicit publication only; default private preview.')
 args=ap.parse_args();require(len(args.sha)==64 and all(c in '0123456789abcdef' for c in args.sha),'exact SHA required');run(args)
if __name__=='__main__':main()

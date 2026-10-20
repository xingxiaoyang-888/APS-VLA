from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,difflib,traceback,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/integration_independent_1317'
B='results/formal_main_v2/preflight/heartbeat_20261020T2117'
E='results/formal_main_v2/engineering/supervision_delivery_1317'
checks=[];inputs={};start=time.time()
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(rel,pin=None,base=R,track=True):
 p=base/rel
 assert p.is_file() and not p.is_symlink(),str(p)
 b=p.read_bytes();h=sha(b)
 if pin is not None:assert h==pin,(str(p),h,pin)
 if track:inputs[str(p)]=dict(path=str(p),sha256=h,bytes=len(b))
 return b
def rd(rel,pin=None,base=R):return json.loads(raw(rel,pin,base))
def rr(ref,base=R):return rd(ref['path'],ref['sha256'],base)
def rf(rel):b=raw(rel);return dict(path=rel,sha256=sha(b))
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
def test(name,v):assert v,name;checks.append(dict(check=name,status='passed'))
def out(name,x):
 p=D/name
 assert p.parent==D and not p.exists(),str(p)
 p.write_bytes((json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode())
 return dict(path=str(p.relative_to(R)),sha256=sha(p.read_bytes()),bytes=p.stat().st_size)
def main():
 source=raw('.local/integrate_1317.py','eb5e2c45e534611639238e04cbf7ca34527c1538367959b4f68f061c5f5ed58f')
 draft=raw('.local/integrate_1317_planned.py','7c4e61f24567f3c24c834b4d4f3f53973b2b9733c72dbf57080bc86ed1a6ae49')
 raw(B+'/root_operations/integrate_1317.py',sha(source))
 compile(source,'root_integrate_reviewed_only','exec')
 text=source.decode();dt=draft.decode()
 expected=dt.replace('NOT_YET_CREATED_DO_NOT_EXECUTE','d8408e661e9b48f3d5fe38c9bdd1458aba55125c19222a2bb0aefe06749e139a')
 expected=expected.replace("visual_tokens=128,completed_trials=n","visual_tokens=128,visual_tokens_scope='A/B only; dense512 and uniform256/128/64 references separately recorded.',completed_trials=n")
 expected=expected.replace("  j=matches[0];assert j['suite']","  assert row['planned_trials']==200 and row['completed_trials_accepted']==0\n  j=matches[0];assert j['suite']")
 test('exactly_three_bounded_draft_revisions',expected==text)
 test('root_shared_writer_lock_CAS_and_preservation_guards',
  "with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock')" in text and 'c.atomic_json(sp,s,before)' in text and
  "assert ctl==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']" in text and
  "f['completed_training_pairs']==old['formal_main_progress']['completed_training_pairs']" in text and
  "f['automatic_machine_verified_pairs']==old['formal_main_progress']['automatic_machine_verified_pairs']" in text)
 (D/'reviewed_root_integrate_1317.py').write_bytes(source)
 (D/'draft_to_actual.diff').write_text(''.join(difflib.unified_diff(dt.splitlines(True),text.splitlines(True),fromfile='unexecuted_planned',tofile='actual_pinned')))
 tlog='results/formal_main_v2/control_transport/heartbeat_1317_integration.jsonl'
 tl=[json.loads(x) for x in raw(tlog,'cbc71e5d1959087f4291d99b4096f79cd48788d28f12a2a9ff20b06b8e948e61').decode().splitlines() if x.strip()]
 test('root_integration_original_transport_success',tl[-1]['returncode']==0 and tl[-1]['source173_and_entrypoint_unchanged'] is True)
 summ=rd(B+'/summary_after_dispatch.json','91a102f6f2ea3edfc0cf7441b1bd72a40f1f90e7040fe064c8aaf7d6aafb6037')
 dispatch=rd(B+'/dispatch_root_report.json','d8408e661e9b48f3d5fe38c9bdd1458aba55125c19222a2bb0aefe06749e139a')
 stbytes=raw('results/experiment_supervisor/state.json');state=json.loads(stbytes)
 f=state['formal_main_progress'];auto=state['autonomous_training_v1']
 test('training64_and_reviewed321000_preserved',f['root_and_independent_completed_arms']==summ['root_independent_complete']==64 and f['root_and_independent_reviewed_arm_updates']==summ['root_independent_updates']==321000)
 test('no_final_release_or_values',f['completed_final_trials']==summ['final_completed']==0 and not f['test_opened'] and not f['global_release_created'] and summ['final_expected']==35200 and not summ['final_release'])
 test('pending_cleared_reserved_slot_exactly_consumed',state['pending_submission'] is None and auto['reserved_GPU_slots']==0 and auto['root_submission_hold'] is None and summ['pending'] is None and summ['reserved_GPU_slots']==0)
 test('controller_identity_preserved',auto['controller_job_id']==summ['controller']=='3034538' and auto['owner_id']==summ['controller_owner_id']=='6b3beba5cdeb41df9d749b0b2054d485')
 jointref=dict(path=E+'/Goal_terminal_independent/independent_review.json',sha256='7cda4fb3d421242efcc9255c732a08952d4e0288d3866f0088220cd6c3e3cea9')
 joint=rr(jointref)
 raw('results/formal_main_v2/downstream_reviews/Goal_seed17_23_1317_independent.json',jointref['sha256'])
 diag=rd(B+'/Goal_seed17_23_development_diagnostics.json','0760916e0e21bc377c57d3fb7bd5e6e71d439e7bc768fb5f00d347b388a3a292')
 test('Goal_original_full_raw_audit_reused_without_rerun',joint['status']=='passed' and joint['totals']['trials']==800 and joint['source173_R_and_S_unchanged'] and joint['new_GPU_jobs']==0)
 test('Goal_diagnostics_exact_accepted_jobs',diag['jobs']==summ['accepted_jobs'] and diag['total_trials']==800 and diag['unique_initial_states']==joint['unique_initial_states']==100 and diag['available_training_seeds']==[17,23] and diag['missing_training_seed']==41)
 paired=diag['per_task_and_full_paired_trials']
 test('paired_record_archival_reference',paired['path']==E+'/Goal_terminal_independent/paired_development_states.json' and paired['sha256']==joint['paired_states']['sha256']=='0dac8194680d5473ca746c3e10b8f0a5d46e040a2196ff7926a6f2df8f45d226')
 raw(paired['path'],paired['sha256'])
 test('diagnostics_no_three_seed_CI_equivalence_or_latency_claim',not diag['bootstrap_three_seed_claimed'] and not diag['O2A_measured'] and not diag['final_results'] and not joint['bootstrap_computed'] and not joint['CI_claimed'] and diag['available_two_seed_mean_percent']=={'A128':97.0,'B128':97.0,'B_minus_A_pp':0.0})
 goalstates=set()
 for accepted in summ['accepted_jobs']:
  jid=accepted['job_id'];j=joint['jobs'][jid]
  test('Goal_'+jid+'_exact_state_member',f['new_action_development_verified_by_job'][jid]==accepted)
  test('Goal_'+jid+'_scope_and_original_evidence',accepted['visual_tokens_scope']=='A/B only; dense512 and uniform256/128/64 references separately recorded.' and accepted['completed_trials']==j['trials'] and accepted['successes']==j['successes'] and accepted['per_task']==j['per_task'] and accepted['references']==j.get('references',{}) and accepted['reference_trials']==j['reference_trials'] and accepted['AB_trials']==j['AB_trials'] and accepted['root_review']==j['root_receipt'])
  test('Goal_'+jid+'_paired_diagnostics',accepted['paired_outcomes']==j['discordance'] and accepted['B_minus_A_percentage_points']==j['B_minus_A_pp'] and accepted['initial_observation_token_overlap_mean']==j['t0_token_diagnostics']['mean_intersection_over_128'] and accepted['initial_observation_token_Jaccard_mean']==j['t0_token_diagnostics']['mean_Jaccard'] and accepted['offline_validation_diagnostics']==j['offline_validation_diagnostics'])
  root=rr(accepted['root_review'])
  test('Goal_'+jid+'_root_summary_successes',root['scientific_complete'] and root['status']=='passed' and {k:v['successes'] for k,v in root['reconstructed_summary']['methods'].items()}==j['successes'])
  for pair in root['reconstructed_summary']['paired_AB'].values():
   goalstates.update(x['state_trial_id'] for x in pair['results'])
  oldgroup='nonLong_development_submissions_1032' if j['seed']==17 else 'nonLong_development_submissions_1220'
  oldrow=next(x for x in f[oldgroup] if x['job_id']==jid)
  test('Goal_'+jid+'_existing_submission_marked_accepted_once',oldrow['completed_trials_accepted']==j['trials'] and not oldrow['scientific_terminal_acceptance_pending'])
 test('Goal100_clusters_shared_800_method_trials',len(goalstates)==100 and joint['all_eight_methods_same_t0_observation_for_each_state'])
 test('raw_current_compatible_counts',f['completed_development_trials']==summ['raw_historical_and_current_development_trials']==3212+800==4012 and f['current_action_development_trial_count']==summ['current_action_development_trials']==2000+800==2800 and sum(x['completed_trials'] for x in f['new_action_development_verified_by_job'].values())==2800 and f['historical_other_action_semantics_development_trials']==1212 and f['Long22_development_statistics']['explicit_legacy_equivalent_trials']==summ['explicit_legacy_equivalent_Long_trials']==600 and summ['compatible_current_and_explicit_legacy_trials']==2800+600)
 unique={k:100 for k in ['libero_10','libero_spatial','libero_object','libero_goal']}
 test('unique_initial_states_300_to400_no_cross_seed_inflation',f['current_action_development_unique_initial_states']==summ['current_action_unique_initial_states']==400 and f['current_action_development_unique_initial_states_by_suite']==summ['unique_current_initial_states_by_suite']==unique)
 preindref=dict(path=E+'/nonLong_plan_independent/post_readiness/post_readiness_independent_review.json',sha256='738f91a8c772825794e8ff52a5086875aa69ba1edb1e51f02e40f31dda4b95f9')
 preind=rr(preindref);test('four_original_actual_P_preexecution_independent_evidence',preind['status']=='passed' and preind['actual_full_P_wrapper_verifications']==4 and preind['Slurm_submissions']==0 and not preind['actual_GPU_runtime_chain_verified'])
 expectedjobs=['3049622','3049632','3049657','3049679']
 test('exact_four_ordered_200trial_unaccepted_new_jobs',[r['job_id'] for r in dispatch['submissions']]==expectedjobs and summ['new_submissions']==dispatch['submissions']==f['nonLong_development_submissions_1317'] and summ['new_planned_trials']==800 and all(r['planned_trials']==200 and r['completed_trials_accepted']==0 for r in dispatch['submissions']))
 jobchecks=[]
 for n,row in enumerate(dispatch['submissions']):
  jid=row['job_id'];a=rr(row['authorization']);apin=row['authorization']['sha256'];token='cti-downstream-gateway-v1:'+apin
  plan=rr(a['plan']);science=rr(a['scientific_plan']);prepared=rr(a['prepared_invocation']);ready=rr(a['runtime_readiness']);reservation=rr(a['root_reservation'])
  pp=next(p for p in preind['plans'] if p['group_key']==row['group_key'])
  test(jid+'_single_use_authorization',a['maximum_attempts']==1 and not a['automatic_retry'] and a['controller_job_id']=='3034538' and not a['final_release_authorized_by_gateway'] and a['status']=='approved_for_exactly_one_registered_downstream_submission' and a['plan_arguments']['stage']=='development' and a['plan_arguments']['freeze_directory'] is None and a['plan_arguments']['profile_panel'] is None and a['plan_arguments']['stop_after'] is None)
  test(jid+'_exact_both_plan_hash_semantics',plan['plan_sha256']==sha(canonical({k:v for k,v in plan.items() if k!='plan_sha256'})) and pp['plan_sha256']==plan['plan_sha256'] and a['plan']==pp['effective_plan'] and a['scientific_plan']==pp['scientific_plan'])
  test(jid+'_prepared_invocation_contract',prepared==dict(plan['invocation'],registered_utc=prepared['registered_utc'],plan_sha256=plan['plan_sha256'],runtime_readiness=a['runtime_readiness']))
  inv=rr(row['invocation']);raw(row['invocation']['path'],row['invocation']['sha256'],P)
  test(jid+'_R_P_invocation_exact_registered_prepared',inv==prepared and row['invocation']['sha256']==a['prepared_invocation']['sha256'] and row['invocation']['path']==plan['invocation_relative'] and inv['stage']=='development' and inv['method_ids']==row['method_ids']==pp['methods'] and inv['suite']==row['suite']==pp['suite'] and inv['final_values_read_locally'] is False and inv['scientific_settings_changed'] is False and inv['resume'] is False)
  test(jid+'_readiness_binds_real_double_reviews',ready['status']=='passed' and ready['expected_trials']==200 and ready['unique_development_initial_states']==100 and ready['allowed_stages']==['development'] and ready['allowed_suite']==row['suite'] and ready['method_ids']==row['method_ids'] and ready['effective_plan']==a['plan'] and ready['scientific_plan']==a['scientific_plan'] and ready['root_review']!=ready['independent_review'] and ready['root_review']==pp['root_review'] and ready['independent_review']==pp['independent_review'] and not ready['final_evaluation_enabled'] and not ready['O2A_enabled'] and not ready['global_freeze_enabled'])
  for ref in [ready['root_review'],ready['independent_review'],a['runtime_readiness'],inv['action_execution_contract']]:
   rr(ref);raw(ref['path'],ref['sha256'],P)
  for ref in [a['plan'],a['scientific_plan']]:raw(ref['path'],ref['sha256'],P)
  precheck=rr(row['root_acceptance'])
  test(jid+'_root_actual_P_CPU_precheck',precheck['full_P_wrapper_verify'] and precheck['real_full_registry_scientific_reconstruction'] and precheck['authorization']==row['authorization'] and precheck['readiness']==a['runtime_readiness'] and precheck['independent_review']==ready['independent_review'] and precheck['new_trials']==0)
  ad='results/formal_main_v2/downstream_gateway/'+apin
  pref=rd(ad+'/preflight.json');ack=rd(ad+'/sbatch_result.json');failed=rd(ad+'/failed_transaction.json');committed=rd(ad+'/committed.json');rec=rr(row['root_reconciliation']);submission=rr(row['submission'])
  test(jid+'_saved_original_delay_and_single_ACK',ack['returncode']==0 and ack['stdout']==jid+'\n' and failed['error']=='post-submit accounting incomplete' and failed['status']=='stopped_requires_root_reconciliation_no_retry' and not failed['automatic_retry'] and ack['actual_sbatch_argv']==pref['actual_sbatch_argv'])
  for key,name in [('original_ACK','sbatch_result.json'),('original_failure','failed_transaction.json'),('original_preflight','preflight.json')]:
   test(jid+'_'+key+'_exact_ref',rec[key]==rf(ad+'/'+name))
  test(jid+'_original_pending_exact_ID_token_and_no_resubmit',rec['status']=='exact_original_ACK_job_reconciled' and rec['new_submissions']==0 and not rec['automatic_retry'] and rec['pending_before']['known_job_id']==jid and rec['pending_before']['request_token']==token and rec['pending_before']['authorization']==row['authorization'] and rec['pending_before']['invocation']==row['invocation']['path'] and rec['pending_before']['invocation_sha256']==row['invocation']['sha256'])
  test(jid+'_committed_submission_and_job_identity',committed['job']==rec['job']==submission and committed['reservation_consumed'] and committed['root_reconciliation']==row['root_reconciliation'] and committed['request_token']==token and committed['status']=='submitted_once_reconciled_after_accounting_delay')
  job=committed['job'];live=[j for j in state['registered_jobs'] if str(j['job_id'])==jid];test(jid+'_registry_job_unique',len(live)==1)
  dynamic={'node','exit_code','status','allocation','elapsed_seconds'}
  test(jid+'_registry_immutable_identity',{k:v for k,v in live[0].items() if k not in dynamic}=={k:v for k,v in job.items() if k not in dynamic})
  test(jid+'_registered_stage_token_no_duplicate',sum(j.get('stage_key')==job['stage_key'] for j in state['registered_jobs'])==1 and sum(j.get('downstream_gateway',{}).get('request_token')==token for j in state['registered_jobs'])==1)
  test(jid+'_reservation_one_slot_exact_consumption',reservation['reserved_slots']==1 and reservation['capacity_limit_all_GPU_modes']==8 and reservation['stage_key']==inv['stage_key'] and reservation['authorization_path']==row['authorization']['path'] and rec['exact_reservation_consumed']==a['root_reservation'] and auto['downstream_reservations_consumed'][apin]=={'job_id':jid,'request_token':token,'reservation':a['root_reservation']})
  test(jid+'_owner_lifecycle_and_science_preserved',rec['lifecycle_lease_held'] and rec['all173_R_and_S_match'] and rec['unrelated_controller_fields_unchanged'] and not rec['final_release_authorized'] and rec['controller_owner']['owner_id']==auto['owner_id'])
  argv=ack['actual_sbatch_argv'];wrap=argv[-1]
  test(jid+'_single_GPU_exact_original_sbatch',argv.count('--no-requeue')==1 and '--gres=gpu:l40:1' in argv and '--comment='+token in argv and '--time=04:00:00' in argv and '--wrap'==argv[-2] and str(P/row['invocation']['path']) in wrap and row['invocation']['sha256'] in wrap and str(P/inv['wrapper']) in wrap)
  detail=rec['actual_scontrol_detail']
  test(jid+'_captured_scontrol_exact_ID_token_resources',detail['returncode']==0 and detail['argv']==['scontrol','show','job','-o',jid] and ('JobId='+jid+' ') in detail['stdout'] and ('Comment='+token) in detail['stdout'] and 'Requeue=0' in detail['stdout'] and 'Restarts=0' in detail['stdout'] and 'WorkDir='+str(P) in detail['stdout'])
  preocc=pref['capacity']['occupied'];postocc=rec['capacity']['occupied']
  test(jid+'_saved_capacity_exact4to8',len(preocc)==4+n and len(postocc)==5+n and set(postocc)==set(preocc)|{jid} and not pref['capacity']['unknown'] and not rec['capacity']['unknown'] and not pref['capacity']['findings'] and not rec['capacity']['findings'])
  test(jid+'_preflight_unrun_output_and_published_inputs',pref['runtime_preflight']['output_exists'] is False and pref['runtime_preflight']['missing_publications']==[] and pref['invocation_relative']==row['invocation']['path'] and pref['invocation_sha256']==row['invocation']['sha256'] and pref['request_token']==token)
  raw(inv['wrapper'],inv['wrapper_sha256']);raw(inv['wrapper'],inv['wrapper_sha256'],P)
  jobchecks.append(dict(job_id=jid,suite=row['suite'],seed=row['seed'],budget=row['budget'],methods=row['method_ids'],planned=200,accepted=0,authority=row['authorization'],invocation=row['invocation'],reconciliation=row['root_reconciliation'],preoccupied=len(preocc),postoccupied=len(postocc),original_delay_retained=True,no_resubmission=True))
 # Recompute allocation cost solely from the saved summary snapshot; no scheduler calls.
 ids=[str(j['job_id']) for j in state['registered_jobs'] if j.get('experiment')=='formal_main_v2']
 rows=summ['scheduler']['rows']
 test('all_registered_snapshot_rows_available',all(j in rows for j in ids) and len(ids)==len(set(ids)))
 seconds=sum(rows[j]['elapsed_seconds']*rows[j]['gpus'] for j in ids)
 test('all_allocations_cost_no_acceptance_double_charge',seconds==summ['allocated_GPU_seconds']==1921157 and abs(summ['allocated_GPU_hours']-seconds/3600)<1e-12 and diag['all_job_GPU_seconds']==7799 and diag['GPU_cost_already_in_Slurm_total'] and summ['includes_all_registered_allocations'] and not summ['cost_is_final'])
 test('saved_snapshot_eight_running_GPU_slots',summ['active_GPU_jobs']==len(summ['capacity']['occupied'])==8 and all(rows[j]['status']=='RUNNING' and rows[j]['gpus']==1 for j in summ['capacity']['occupied']) and not summ['capacity']['findings'] and not summ['capacity']['unknown'])
 invt=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 test('frozen173_inventory_count',len(invt['files'])==173)
 for rel,pin in invt['files'].items():raw(rel,pin,track=False);raw(rel,pin,S,track=False)
 checks.append(dict(check='frozen173_R_and_S_actual_bytes',status='passed',count=173))
 docs={}
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记']:
  rel='docs/'+name+'.md';data=raw(rel);txt=data.decode();intro=txt.split('\n')[2:5]
  test('doc_'+name+'_new_progress',all(x in '\n'.join(intro) for x in ['64/72','Goal800','800条开发','8GPU','533.655GPU小时','最终0/35200']))
  docs[rel]=sha(data)
 gd=raw('docs/正式Goal主预算开发结果.md').decode()
 test('Goal_doc_scope_and_shared_references',all(x in gd for x in ['100个唯一Goal初态','两seed描述均值A/B均97%','不构成等效','没有完整O2A','7799GPU秒','验收不重复加费','后续不同轨迹不混作同观测','| dense | 97 |','| uniform256 | 95 |','| uniform128 | 92 |','| uniform64 | 68 |']))
 for j in summ['accepted_jobs']:
  seed=j['seed'];wanted=f"| {seed} | {j['successes']['A128_seed'+str(seed)]} | {j['successes']['B128_seed'+str(seed)]} | {j['B_minus_A_percentage_points']:+.0f} | {j['initial_observation_token_overlap_mean']:.6f} | {j['initial_observation_token_Jaccard_mean']:.6f} |"
  test('Goal_doc_seed'+str(seed),wanted in gd)
  for t in j['per_task']:assert f"| {seed} | {t['task_id']} | {t['A_success']} | {t['B_success']} | {t['B_minus_A_pp']:+.0f} |" in gd
  for arm,v in j['offline_validation_diagnostics'].items():assert f"| {seed}/{arm} | {v['selected_update']} | {v['hard_validation_teacher_L1_task_equal']:.8f} | {v['hard_validation_demonstration_L1_task_equal']:.8f} | {v['validation_windows']} |" in gd
 for i in range(10):
  vals=[next(t['successes'] for t in summ['accepted_jobs'][0]['references'][n]['per_task'] if t['task_id']==i) for n in ['dense','uniform256','uniform128','uniform64']]
  assert '| '+str(i)+' | '+' | '.join(map(str,vals))+' |' in gd
 test('Goal_doc_per_task_and_offline_exact',True)
 nldoc=raw('docs/正式非Long开发结果.md').decode();test('nonLong_document_preserves_scope',all(x in nldoc for x in ['Goal新800条完成双审','Spatial/Object历史结果保留']))
 evidence=out('check_evidence.json',dict(schema='formal_main_v2',status='passed',checks=checks,input_refs=list(inputs.values()),state_observed_sha256=sha(stbytes),state_observation_scope='One read of atomic live state; no demand that controller mutable fields equal integration-time bytes.',dynamic_registry_fields=sorted(dynamic),saved_snapshot_utc=summ['utc'],jobs=jobchecks,document_hashes=docs,allocation_seconds=seconds))
 report=out('independent_review.json',dict(schema='formal_main_v2',kind='independent_submission_and_integration_review',status='passed',reviewer='/root/object64_pending_0333_audit',utc=datetime.now(timezone.utc).isoformat(),
  source_ref=dict(path=str(Path(__file__).relative_to(R)),sha256=sha(Path(__file__).read_bytes())),root_source_ref=dict(path='.local/integrate_1317.py',sha256=sha(source)),
  check_evidence=evidence,checks_passed=len(checks),findings=[],blocking_findings=[],audit_only_correction='a1 incorrectly compared a reservation ref with its enclosing state consumption record. Original failure retained; a2 validates both actual schemas without altering production evidence.',
  submission_jobs=jobchecks,Goal800_original_raw_audit_reused=jointref,new_raw_ledgers_parsed=0,new_consumer_runs=0,new_scheduler_queries=0,new_GPU_jobs=0,new_GPU_seconds=0,
  training_complete=64,training_total=72,reviewed_arm_updates=321000,raw_development=4012,current_action_development=2800,explicit_legacy_Long_equivalent=600,compatible_development=3400,unique_initial_states=400,unique_Goal_initial_states=100,shared_Goal_references_not_seed_replicated=True,
  new_planned_development=800,new_planned_accepted=0,saved_snapshot_utc=summ['utc'],snapshot_GPU_slots=8,snapshot_allocated_GPU_seconds=seconds,snapshot_allocated_GPU_hours=seconds/3600,cost_is_final=False,
  Goal_two_seed_means_percent=diag['available_two_seed_mean_percent'],Goal_two_seed_descriptive_only=True,Goal_L1_offline_validation_only=True,Goal_token_overlap_equal_hash_t0_only=True,
  final_completed=0,final_expected=35200,final_release=False,sealed_values_read=False,checkpoint_bytes_read=False,source173_R_and_S_unchanged=True,
  shared_state_modified=False,Git_modified=False,Slurm_modified=False,root_integration_executed_by_this_auditor=False,
  limitations=['Submission acceptance only for four new jobs; no terminal success claims.','Previously completed 800-trial full raw audit reused, not repeated.','Root integration transport proves its original lock/CAS preservation assertions executed; this audit did not capture an independent pre-integration state.','Saved scheduler snapshot used; no live GPU polling.','No final evaluation, O2A, equivalence or three-seed Goal conclusion.'],
  CPU_wall_seconds=time.time()-start))
 files=[]
 for p in sorted(D.iterdir()):
  if p.is_file() and p.name!='manifest.json':files.append(dict(path=str(p.relative_to(R)),sha256=sha(p.read_bytes()),bytes=p.stat().st_size))
 manifest=out('manifest.json',dict(schema='formal_main_v2',kind='independent_private_audit_manifest',status='passed',files=files))
 print(json.dumps(dict(status='passed',report=report,manifest=manifest,check_evidence=evidence,checks=len(checks)),ensure_ascii=False))
if __name__=='__main__':
 try:main()
 except Exception as exc:
  failure=dict(status='failed',error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc(),checks_completed=checks,scope='audit script and evidence check failure; no production mutation')
  out('failure_a2.json',failure);raise

from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,json,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/delivery_independent_20261021T0334/final';B='results/formal_main_v2/preflight/heartbeat_20261021T1134';E='results/formal_main_v2/engineering/supervision_delivery_20261021T0334'
STATE='54ee7389fe300b4ec553998d91b9bf727ca3231c2066e35a86716559a3c1406d';SUMMARY='35a12c33d2bf81331e96aad4fe2879ae06fa7269a518fc14933fea8dc65aac02';BEFORE='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa'
checks=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(n,ok):
 if not ok:raise AssertionError(n)
 checks.append(dict(name=n,passed=True))
def get(n,pin=None):
 p=R/n
 if pin:ck('pin:'+n,h(p)==pin)
 return json.loads(p.read_bytes())
def rf(n):p=R/n;return dict(path=n,sha256=h(p),bytes=p.stat().st_size)
def checkref(r):
 ck('ref:'+r['path'],rf(r['path'])==r if 'bytes' in r else h(R/r['path'])==r['sha256'])
 return get(r['path'])
def save(n,x):
 with (D/n).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
s=get('results/experiment_supervisor/state.json',STATE);before=get(B+'/supervisor_snapshot_before.json',BEFORE);z=get(B+'/final_summary.json',SUMMARY)
receipt=get(B+'/root_integration_receipt.json','ff5f2134b1bfa7c45da4aa680bdf82abac5e71a3971bf868c21ba890d8339068')
ck('receipt_exact_state_and_summary',receipt['state_before_sha256']==BEFORE and receipt['state_after']==rf('results/experiment_supervisor/state.json') and receipt['summary']==rf(B+'/final_summary.json'))
obs=checkref(z['cost_basis']);rows=obs['projection']['observation']['rows'];raw={}
for line in obs['projection']['observation']['raw_sacct'].splitlines():
 if not line.strip():continue
 v=line.split('|');ck('raw_sacct_main_unique:'+v[0],v[0] not in raw and v[0].isdigit() and len(v)>=8)
 matches=re.findall(r'(?:^|,)gres/gpu=(\d+)(?:,|$)',v[4]);gpus=int(matches[0]) if matches else 0
 raw[v[0]]=dict(status=v[1].split()[0].rstrip('+'),exit_code=v[2],elapsed_seconds=int(v[3]),allocation=v[4],node=v[5],gpus=gpus)
 ck('raw_accounting_matches_saved_row:'+v[0],all(rows[v[0]][k]==value for k,value in raw[v[0]].items()))
jobs=[j for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2'];ids=[j['job_id'] for j in jobs]
ck('273_unique_formal_allocation_ids',len(ids)==len(set(ids))==273)
cost=sum(raw[j]['elapsed_seconds']*raw[j]['gpus'] for j in ids)
ck('actual_saved_unique_cost1994468',cost==obs['formal_GPU_seconds']==z['allocated_GPU_seconds']==s['current_round_cost']['allocated_gpu_seconds']==1994468)
ck('only2205_global_increment_not_recount326',cost-before['current_round_cost']['allocated_gpu_seconds']==z['newly_accounted_GPU_seconds']==2205 and raw['3054409']['elapsed_seconds']==326 and raw['3054717']['elapsed_seconds']==2205)
terminal={'COMPLETED','FAILED','CANCELLED','TIMEOUT','PREEMPTED','NODE_FAIL','OUT_OF_MEMORY','BOOT_FAIL','DEADLINE','REVOKED','SPECIAL_EXIT'}
ck('all_current_formal_terminal_and_no_active_projection',all(raw[j]['status'] in terminal for j in ids) and not any(obs['projection']['derived'].values()) and z['active_registered_GPU_jobs']==[] and z['actual_running_allocated_GPUs']==0)
ck('controller_normal_exit_and_lease_released',raw['3034538']['status']=='COMPLETED' and raw['3034538']['exit_code']=='0:0' and obs['projection']['lease']['lease_available_measured'] and s['autonomous_training_v1']['root_confirmed_normal_training_exit']['lease_released'])
ck('training72_36_360000_unchanged',z['root_completed_arms']==72 and z['root_completed_pairs']==36 and z['root_reviewed_arm_updates']==360000 and s['formal_main_progress']['completed_training_pairs']==before['formal_main_progress']['completed_training_pairs'])
ck('source_flags_and_sealed_final',z['final_sealed'] and z['global_release'] is False and z['O2A_released'] is False and z['final_trials']==0 and z['final_total']==35200 and s['formal_main_progress']['test_opened'] is False)
oa=checkref(z['Object_linked_single_error_and600']);ga=checkref(z['Goal_prospective200'])
oi=checkref(oa['independent_review']);gi=checkref(ga['independent_review']);orev=checkref(oa['root_review']);grev=checkref(ga['root_review'])
ck('Object_original_scientific_review_inherited_exact',oi['status']=='passed' and not oi['blockers'] and oi['full_original_consumer_reconstructed'] and oi['root_review']==oa['root_review'] and oi['job_id']=='3054409' and orev['original_review']['logical_reference_view_complete'])
ck('Goal_different_agent_real_scientific_consumer_inherited_exact',gi['status']=='passed_new200_terminal_independent_review' and not gi['blockers'] and gi['complete_original_scientific_consumer'] and gi['reviewed_by_agent']=='/root/spatial588_recovery_audit_2054' and gi['root_review']['sha256']==ga['root_review']['sha256']==gi['canonical_consumer_reconstruction_sha256'])
ck('Goal_only_new200_inputs_and_actions',ga['status']=='accepted_new200_only' and ga['current_trials']==gi['trials']==200 and ga['policy_queries']==gi['policy_queries']==3027 and ga['executed_policy_steps']==gi['executed_policy_steps']==23508 and ga['paired_pre_policy_inputs']==gi['paired_preB_checks']==100)
ck('Goal97_96_retained_not_effectiveness_claim',ga['methods']['A256_seed17']['successes']==gi['methods']['A256_seed17']['success']==97 and ga['methods']['B256_seed17']['successes']==gi['methods']['B256_seed17']['success']==96)
ck('Goal_old200_and_other1000_and_O2A_HOLD',ga['old200_retained_HOLD'] and ga['old_failure_cause_identified'] is False and ga['remaining1000_scientific_HOLD'] and ga['O2A_result'] is False and ga['final_release'] is False and gi['old200_HOLD'] and gi['other1000_HOLD'])
ck('Object_mixed_origin600_all601_original_error_retained',oa['logical_complete_trials']==600 and oa['legacy_equivalent_trials']==599 and oa['current_trials']==1 and oa['total_linked_attempts']==601 and oa['original_policy_error_retained'] and oa['original_refused_chunk_unknown'] and oa['no_fake_legacy_ledger'] and oa['raw_new_ledger_stays_partial1_of600'])
ck('Object_count_success_and_cost',oa['successes']==521 and oa['normal_task_failures']==79 and oa['original_three_allocation_GPU_seconds']==6713 and oa['new_allocation_GPU_seconds']==326 and oa['total_unique_GPU_seconds']==7039)
checkref(oa['typed_bridge']);origin_bytes=(R/oa['logical_origin_view']['path']).read_bytes();checkref_origin=rf(oa['logical_origin_view']['path']);ck('origin_view_exact_pin',checkref_origin==oa['logical_origin_view'])
origin=[json.loads(x) for x in origin_bytes.splitlines()];oldtable='results/formal_main_v2/execution/object_single_error_v1/legacy599_adoption_rows.jsonl';ck('legacy_adoption_table_unchanged',h(R/oldtable)=='ac792e8d88f251f097f3f0e110e6c32aa45dbacd103404c0189b3bebf56ccb5e')
legacy=[json.loads(x) for x in (R/oldtable).read_bytes().splitlines()]
expected=[dict(trial_id=x['trial_id'],method=x['method'],success=x['success'],status=x['status'],origin='legacy_equivalent',source_job_id=x['source_job_id'],adoption_table=oldtable,adoption_row=i+1,original_result=x['result']) for i,x in enumerate(legacy)]
last=origin[-1];rawpath=last['raw_ledger'];newlines=(R/rawpath).read_bytes().splitlines(keepends=True);newrow=json.loads(newlines[-1])
expected.append(dict(trial_id=newrow['trial_id'],method=newrow['method'],success=newrow['success'],status=newrow['status'],origin='current_linked_attempt',source_job_id='3054409',raw_ledger=rawpath,result_line=3,result_raw_line_sha256=hashlib.sha256(newlines[-1]).hexdigest()))
ck('origin600_reconstructed_without_fake_ledger',origin==expected and len(origin)==len({x['trial_id'] for x in origin})==600 and len(newlines)==3 and sum(x['success'] for x in origin)==521)
fp=s['formal_main_progress'];oldfp=before['formal_main_progress']
ck('complete_current_and_history_arithmetic',oldfp['current_action_development_trial_count']==6388 and fp['current_action_development_trial_count']==z['current_action_development_trials']==6388+201==6589 and fp['completed_development_trials']==z['all_historical_catalog_development_rows']==7600+201==7801 and fp['complete_development_batches_accepted_trials']==z['compatible_development_trials']==7000+201+599==7800)
ck('legacy1211_and400_unique',fp['complete_development_batches_compatible_legacy_trials']==600+12+599==1211 and z['unique_development_initial_states']==fp['current_action_development_unique_initial_states']==oldfp['current_action_development_unique_initial_states']==400 and z['new_unique_initial_states']==0)
ck('suite_counts_consistent',sum(x['current'] for x in z['per_suite'].values())==6589 and sum(x['legacy'] for x in z['per_suite'].values())==1211 and sum(x['complete'] for x in z['per_suite'].values())==7800 and all(x['current']+x['legacy']==x['complete'] for x in z['per_suite'].values()))
ck('remaining_exact5_no_admission',[(x['budget'],x['seed'],x['trials']) for x in z['remaining_scientific_pairs']]==[(256,23,200),(256,41,200),(64,17,200),(64,23,200),(64,41,200)] and z['Goal_remaining1000_HOLD'] and z['Goal_old200_HOLD'] and z['new_GPU_jobs']==[])
# Require all preexisting state data outside this named metadata update to stay intact.
oldjobs={x['job_id']:x for x in before['registered_jobs']};newjobs={x['job_id']:x for x in s['registered_jobs']}
ck('registered_jobs_membership_and_order_unchanged',[x['job_id'] for x in before['registered_jobs']]==[x['job_id'] for x in s['registered_jobs']])
for jid,old in oldjobs.items():
 target=copy.deepcopy(old)
 if jid in ('3054409','3054717'):
  for k in ('status','raw_status','exit_code','elapsed_seconds','gpus','node','allocation'):target[k]=rows[jid]['status'] if k=='raw_status' else rows[jid][k]
  target['terminal_root_acceptance']=z['Object_linked_single_error_and600'] if jid=='3054409' else z['Goal_prospective200']
 ck('exact_registered_job_delta:'+jid,newjobs[jid]==target)
a=copy.deepcopy(before['autonomous_training_v1']);a['occupied_job_ids']=[]
ck('only_controller_occupied_projection_changes',s['autonomous_training_v1']==a and before['autonomous_training_v1']['occupied_job_ids']==['3054717'])
a=copy.deepcopy(oldfp['parallel_execution']);a['registered_requested_active_GPU_jobs']=0
ck('only_parallel_requested_projection_changes',fp['parallel_execution']==a and a['actual_running_allocated_GPUs']==0)
allowed_fp={'Object3054409_terminal_acceptance_20261021T0334','Goal3054717_terminal_acceptance_20261021T0334','current_action_development_trial_count','completed_development_trials','complete_development_batches_accepted_trials','complete_development_batches_compatible_legacy_trials','completed_development_trials_catalog_semantics','new_action_development_verified_by_job','downstream_followups_20261021T0334','first_object_development','parallel_execution'}
ck('all_other_formal_progress_unchanged',{k:v for k,v in fp.items() if k not in allowed_fp}=={k:v for k,v in oldfp.items() if k not in allowed_fp})
ck('only201_new_current_job_entries',set(fp['new_action_development_verified_by_job'])-set(oldfp['new_action_development_verified_by_job'])=={'3054409','3054717'} and all(fp['new_action_development_verified_by_job'][k]==v for k,v in oldfp['new_action_development_verified_by_job'].items()))
allowed_top={'autonomous_training_v1','current_round_cost','current_work','formal_main_progress','last_root_health_check','last_root_supervision_snapshot','last_supervision_utc','next_actions','next_allowed_action','registered_jobs','updated_utc','updated_date'}
ck('all_other_supervisor_fields_unchanged',{k:v for k,v in s.items() if k not in allowed_top}=={k:v for k,v in before.items() if k not in allowed_top})
ck('pending_and_reservations_unchanged_empty',s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0 and s['autonomous_training_v1']['root_submission_hold'] is None)
ck('latest_summary_and_cost_final_binding',s['last_root_supervision_snapshot']==rf(B+'/final_summary.json') and s['current_round_cost']['final'] is True and s['current_round_cost']['registered_jobs']==273 and obs['root_utc'] in s['current_round_cost']['scope'])
# Reconstruct the prepended documentation block without replaying any writer.
src=R/'.local/integrate_terminals_20261021T0334_v4.py';ck('integrator_exact_v4',h(src)=='1701253256acaa4483edd754d60b7c887a443396ddf4752f164bc4ec874c5c59');tree=ast.parse(src.read_text())
section_node=next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='section' for t in n.targets))
section=eval(compile(ast.Expression(section_node),'<read-only-doc-expression>','eval'),{'__builtins__':{}},{'now':z['utc'],'B':B})
for doc in receipt['document_changes']:
 p=R/doc['path'];text=p.read_text();first,sep,rest=text.partition('\n');prefix=section+'\n';ck('document_only_exact_prepend:'+doc['path'],h(p)==doc['after_sha256'] and rest.startswith(prefix) and hashlib.sha256((first+'\n'+rest[len(prefix):]).encode()).hexdigest()==doc['before_sha256'])
ck('document_counts_and_HOLD_qualifiers',all(x in section for x in ['7800/8800','6589 current','历史目录7801','不是新增800','旧200','HOLD','非最终有效性','最终0/35200']))
frozen=get('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')['files'];ck('source173_count',len(frozen)==173)
for n,pin in frozen.items():ck('source173_R_S_unchanged:'+n,h(R/n)==h(S/n)==pin)
arc=checkref(ga['archive_root_verification']);am=checkref(ga['archive_manifest'])
ck('Goal_complete_archive_scope_pinned_inherited',arc['status']=='passed' and arc['exact_scientific_blob_set_equal'] and arc['verified_members']==35076 and len(am['parts'])==24 and gi['unique_blob_count']==35062)
ck('final_state_summary_still_exact',h(R/'results/experiment_supervisor/state.json')==STATE and h(R/B/'final_summary.json')==SUMMARY)
report=dict(schema='formal_main_v2',kind='actual_terminal_integration_delivery_review_before_index',status='passed_actual_integration_pending_index',reviewed_by='independent',blockers=[],state_sha256=STATE,state_before_sha256=BEFORE,summary_sha256=SUMMARY,integration_receipt=rf(B+'/root_integration_receipt.json'),source173_verified=True,final_sealed=True,counts=dict(training_arms=72,training_pairs=36,updates=360000,current=6589,legacy=1211,complete=7800,historical_catalog=7801,unique_initial_states=400),cost=dict(unique_formal_allocations=273,GPU_seconds=cost,GPU_hours=cost/3600,saved_observation_utc=obs['root_utc'],new_queries_by_auditor=0),inherited_scientific_terminal_reviews=dict(Object=oa['independent_review'],Goal=ga['independent_review'],Goal_auditor=gi['reviewed_by_agent'],scope='Exact original completed terminal reviews inherited and bound; this audit newly checks integration/state/docs/cost delivery, not rerunning scientific terminal review or its own Goal runtime.'),Goal_old200_HOLD=True,Goal_remaining1000_HOLD=True,O2A_released=False,global_release=False,Git_index_review_pending=True,future_commit_or_push_verified=False,new_GPU_submissions=0,new_Slurm_queries=0,state_writes=False,Git_writes=False,check_count=len(checks),checks=checks,utc=datetime.now(timezone.utc).isoformat())
save('actual_integration_review.json',report);print(json.dumps(dict(status=report['status'],checks=len(checks),report_sha256=h(D/'actual_integration_review.json'))))

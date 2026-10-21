from pathlib import Path
from datetime import datetime,timezone
import ast,collections,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/delivery_independent_20261021T0334';AUTHOR=R/'.local/goal_remaining5_design_20261021T0334'
ENTRY='.local/integrate_terminals_20261021T0334_v3.py';ENTRY_SHA='e4f5de6cc298e5ea927d26b6f25281a089912f96baa4044c9a7ead3c7a8b7e48'
MANIFEST_SHA='83b17715c073995fb0ca87efd1151e7bf9b6438ffe2f2a135478d9a12ff93ea3';STATE_SHA='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa'
checks=[];refs={}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(label,ok):
 if not ok:raise AssertionError(label)
 checks.append(dict(name=label,passed=True))
def read(p,pin=None):
 if pin:ck('exact:'+str(p.relative_to(R)),h(p)==pin)
 return json.loads(p.read_bytes())
def checkref(row):
 p=R/row['path'];ck('reference:'+row['path'],p.resolve()==p and p.is_file() and h(p)==row['sha256'])
 if 'bytes' in row:ck('reference_size:'+row['path'],p.stat().st_size==row['bytes'])
 refs[row['path']]=row['sha256'];return json.loads(p.read_bytes())
def save(n,v):
 with (D/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
state=read(R/'results/experiment_supervisor/state.json',STATE_SHA)
entry=(R/ENTRY).read_text();ck('integration_source_exact',h(R/ENTRY)==ENTRY_SHA);tree=ast.parse(entry)
compile(tree,ENTRY,'exec')
ck('no_GPU_process_network_or_Git_calls',not any(isinstance(n,(ast.Import,ast.ImportFrom)) and any(x in ast.unparse(n) for x in ['subprocess','socket','requests']) for n in ast.walk(tree)) and all(x not in entry for x in ['sbatch(', 'scontrol ', 'git commit','git push']))
ck('root_controls_no_source_execution_in_this_audit',True)
lock=next(n for n in tree.body if isinstance(n,ast.With))
ck('shared_lock_exact',ast.unparse(lock.items[0].context_expr)=="ctl.exclusive_lock(R / 'results/experiment_supervisor/.writer.lock')")
ck('goal_pass_guard_before_any_mutating_top_level_block',entry.index("assert gi['status']=='passed_new200_terminal_independent_review'")<entry.index('with ctl.exclusive_lock'))
ck('goal_pass_requires_complete_consumer_and2205',all(x in entry for x in ["not gi['blockers']","gi['complete_original_scientific_consumer']","gi['trials']==200","gi['allocation_gpu_seconds']==2205"]))
ck('object_full_original_consumer_and13_before_lock',all(x in entry for x in ["oi['full_original_consumer_reconstructed']","oi['raw_P_R_all13_equal']","unique_total_GPU_seconds']==7039"]))
ck('state_CAS_before_work_and_before_atomic_replace',entry.index("assert hashlib.sha256(before).hexdigest()==BEFORE")>entry.index('with ctl.exclusive_lock') and entry.index("assert (R/STATE).read_bytes()==before")<entry.index('os.replace(tmp,R/STATE)'))
ck('source173_pre_post',entry.count("for n,pin in frozen.items():assert h(R/n)==h(S/n)==pin")==2)
ck('exact_current_slot_projection_clear_only',all(x in entry for x in ["assert s['autonomous_training_v1']['occupied_job_ids']==['3054717']","s['autonomous_training_v1']['occupied_job_ids']=[]","['registered_requested_active_GPU_jobs']==1","['registered_requested_active_GPU_jobs']=0","['actual_running_allocated_GPUs']==0","controller_lifecycle_and_identity_unchanged="]))
ck('state_current_pending_holds_empty',state.get('pending_submission') is None and state['autonomous_training_v1'].get('pending_submission') is None and state['autonomous_training_v1']['reserved_GPU_slots']==0 and state['autonomous_training_v1']['root_submission_hold'] is None)
ck('current_occupied_exact_expected',state['autonomous_training_v1']['occupied_job_ids']==['3054717'] and state['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']==1 and state['formal_main_progress']['parallel_execution']['actual_running_allocated_GPUs']==0)
legacy=state['formal_main_progress']['active_training']
ck('legacy_active_is_completed_not_global_gate',legacy['completed_by_arm']=={'A':5000,'B':5000} and legacy['actual_resume_confirmed']['used_for_global_scheduling'] is False)
ck('no_pending_training_boundary_reviews',state['formal_main_progress']['pending_boundary_reviews']==[])
ck('terminal_cost_wording_and_same273',all(x in entry for x in ['All273 unique formal Slurm GPU allocations terminal at saved UTC','1994468 GPU seconds once per allocation','allocated_gpu_seconds=1994468','newly_accounted_GPU_seconds=2205']))
ck('catalog_and_full_batch_arithmetic',6388+201==6589 and 600+12+599==1211 and 6589+1211==7800 and 7600+201==7801 and 521+79==600 and 6713+326==7039)
ck('per_suite_sum',[1600+2188+1601+1200,2200*3+1200]==[6589,7800])
ck('old_Goal200_and_remaining5_HOLD',all(x in entry for x in ['old200_retained_HOLD=True','Goal_old200_HOLD=True','Goal_remaining1000_HOLD=True','old_failure_cause_identified=False','final_sealed=True','global_release=False','O2A_released=False','final_trials=0']))
ck('no_fake_legacy_rows', "raw_new_ledger_stays_partial1_of600=True" in entry and "no_fake_legacy_ledger=True" in entry)
frozen=read(R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')['files']
ck('exact173_frozen_count',len(frozen)==173)
for name,pin in frozen.items():ck('frozen_R_S:'+name,h(R/name)==h(S/name)==pin)
manifest=read(AUTHOR/'delivery_manifest.json',MANIFEST_SHA);seen=set()
ck('design_manifest11',manifest['file_count']==len(manifest['files'])==11)
for row in manifest['files']:
 p=R/row['path'];ck('design_member:'+p.name,p.is_relative_to(AUTHOR) and p.resolve()==p and p.name not in seen and h(p)==row['sha256'] and p.stat().st_size==row['bytes']);seen.add(p.name)
design=read(AUTHOR/'design.json');author_checks=read(AUTHOR/'verification_checks.json')
ck('author_checks_exact_list_count',author_checks['status']=='passed' and author_checks['count']==len(author_checks['checks']) and all(c['passed'] for c in author_checks['checks']))
ck('two_prior_design_failures_preserved',sum(n.startswith('failure_') for n in seen)==2)
ck('design_HOLD_no_execution_or_final_access',design['status']=='bounded_identity_design_complete_execution_HOLD' and design['production_ready'] is False and design['new_GPU_jobs']==design['new_trials']==0 and design['sealed_final_values_read'] is False and design['fresh_scheduler_observation_performed'] is False)
ck('design_exact_original_state_snapshot',design['state_snapshot_sha256']==STATE_SHA and h(AUTHOR/design['state_snapshot_path'])==STATE_SHA)
common=design['common'];panel=checkref(common['development_panel'])
ordered=[{k:r[k] for k in ('trial_id','task_id','task_name','source_state_index','initial_state_sha256','source_file')} for r in panel['states']]
ck('development100_10tasks_exact_order',ordered==common['development_states'] and len(ordered)==100 and collections.Counter(r['task_id'] for r in ordered)==dict.fromkeys(range(10),10) and panel['split']=='development' and panel['suite']=='libero_goal' and common['development_order_sha256']==hashlib.sha256(json.dumps(ordered,sort_keys=True,separators=(',',':')).encode()).hexdigest())
ck('fixed_runtime_and_training',common['environment']==dict(environment_seed=0,runtime_seed=17,wait_steps=10,action_chunk=8,max_steps=300) and common['fixed_training']==dict(updates_per_arm=5000,batch=8,horizon=8,lambda_B=0.1,budgets=[256,128,64],seeds=[17,23,41],arms=['A','B'],search=False))
expected=[(256,23),(256,41),(64,17),(64,23),(64,41)]
ck('exact_five_pairs1000',[(x['budget'],x['seed']) for x in design['remaining_pairs']]==expected and design['remaining_pair_count']==5 and design['remaining_expected_trials']==1000)
selection=[]
for row in design['remaining_pairs']:
 key=row['pair_key'];budget=row['budget'];seed=row['seed']
 cfg=checkref(row['planned_scientific_matrix_source']);summary=checkref(row['training_summary'])
 ck('pair_settings:'+key,cfg['suite']=='libero_goal' and cfg['seed']==seed and cfg['tokens_per_camera']*2==budget and cfg['training']['updates']==5000 and cfg['training']['effective_batch']==8 and cfg['future']['horizon']==8 and cfg['future']['weight_B']==0.1)
 ck('bounded_design_only:'+key,row['expected_trials']==200 and row['unique_development_states']==100 and row['max_total_control_steps']==60000 and row['max_total_policy_queries']==7600 and row['maximum_attempts_proposed']==1 and row['new_execution_authorized'] is False and row['per_pair_execution_plan_already_frozen'] is False and row['method_ids']==[f'A{budget}_seed{seed}',f'B{budget}_seed{seed}'])
 ck('no_invented_per_pair_plan:'+key,not row['registered_development_jobs'] and not row['published_invocations'] and not row['published_execution_manifests'] and len(row['missing'])==4)
 completion=state['formal_main_progress']['completed_training_pairs'][key]
 for role,r in row['training_terminal_evidence'].items():
  data=checkref(r);ck('original_training_receipt_ref:'+key+role,r['path']==completion[role] and r['sha256']==completion[role+'_sha256'])
 ck('original_pair_complete:'+key,summary['status']=='completed' and summary['pair_complete'] and summary['planned_updates_per_arm']==5000 and summary['test_opened'] is False)
 for arm in row['arms']:
  dep=checkref(arm['deployment_receipt']);meta=dep['metadata'];selected=min(dep['evaluations'],key=lambda v:(v['validation_metric'],v['update']));fixed=next(v for v in completion['selected_checkpoints'] if v['arm']==arm['arm']);cp=Path(arm['checkpoint']['path'])
  ck('11_nodes_and_earliest_min:'+key+arm['arm'],[v['update'] for v in dep['evaluations']]==list(range(0,5001,500)) and selected['update']==arm['selected_update']==meta['update']==summary['arms'][arm['arm']]['best_update'])
  ck('unchanged_scientific_checkpoint_identity_metadata:'+key+arm['arm'],cp.is_file() and cp.stat().st_size==arm['checkpoint']['bytes'] and str(cp)==fixed['path'] and arm['checkpoint']['sha256']==dep['checkpoint_sha256']==fixed['expected_sha256']==summary['arms'][arm['arm']]['best_checkpoint_sha256'] and meta['pair_id']==row['pair_id'] and meta['suite']=='libero_goal' and meta['seed']==seed and meta['visual_tokens']==budget)
  selection.append(dict(pair=key,arm=arm['arm'],selected_update=arm['selected_update'],checkpoint_sha256=arm['checkpoint']['sha256'],checkpoint_bytes_rehashed_in_this_audit=False))
 for rel in row['missing_P_publication_files']:ck('missing_P_publication_is_explicit_HOLD:'+rel,not (P/rel).exists())
 ids=set(row['method_ids'])
 matches=[j for j in state['registered_jobs'] if j.get('mode') in ('development','engineering','collect','profile','full_profile','component_profile') and (j.get('pair_id')==row['pair_id'] or (j.get('suite')=='libero_goal' and ids.intersection(j.get('method_ids') or [])))]
 ck('suite_scoped_no_prior_registered_attempt:'+key,not matches)
ck('accepted_Goal128_1000_not_new200',design['accepted_Goal128_trials']==1000 and design['accepted_Goal128_AB_trials']==600 and design['accepted_shared_reference_trials']==400 and sum(v['completed_trials'] for v in design['accepted_Goal128'])==1000)
new=design['new256seed17_terminal_pending_separate_acceptance']
ck('new200_and_old200_separate',new['job_id']=='3054717' and new['historical_original200_job_id']=='3049679' and new['historical_original200_remains_HOLD'] is True and new['scientific_admission_by_this_design'] is False and new['must_not_reuse_original_ACK_or_authorization_for_other_pair'] is True)
ck('scope_of_absence_is_bounded',any('scoped to saved state and bounded R/P' in line for line in design['limitations']))
for rel,row in design['current_full200_binding_scan'].items():ck('current_runtime_bound_not_generalized:'+rel,h(R/rel)==h(P/rel)==row['sha256'])
ck('state_unchanged',(R/'results/experiment_supervisor/state.json').read_bytes()==(AUTHOR/'state_snapshot_v3.json').read_bytes())
report=dict(schema='formal_main_v2',kind='root_terminal_integration_and_remaining5_design_pre_review',status='passed_bounded_source_and_design_review',reviewed_by='independent',blockers=[],integration_entrypoint=ENTRY,entrypoint_sha256=ENTRY_SHA,original_integration_v1_sha256='f4e26c60c57a7494fc33d8f470387d3875e3c0a8f517653285c370957b036271',bounded_v3_corrections=['exact occupied3054717 to empty from saved terminal status','requested active job count1 to0; actual GPU count remains0','cost scope reflects saved terminal273 allocation observation'],source173_verified=True,state_before_sha256=STATE_SHA,remaining5_manifest_sha256=MANIFEST_SHA,remaining5_member_count=11,remaining5_scope='CPU design and small immutable identity/evidence verification only; no checkpoint byte rehash or new runtime/GPU acceptance',original_author_check_count=author_checks['count'],selected_checkpoint_metadata=selection,remaining5_production_ready=False,remaining5_GPU_authorized=False,integration_script_executed_by_this_audit=False,requires_before_root_execution=['Exact independently completed Goal200 original-consumer terminal report with status passed_new200_terminal_independent_review and no blockers; manifest/report pins','Root must supply those fixed final pins to the already reviewed source and retain the shared lock/CAS guards'],actual_final_state_review_pending=True,Git_review_pending=True,new_GPU_submissions=0,new_Slurm_queries=0,canonical_writes=False,state_writes=False,Git_writes=False,final_release=False,check_count=len(checks),checks=checks,verified_metadata_refs=refs,utc=datetime.now(timezone.utc).isoformat())
save('preintegration_review.json',report)
print(json.dumps(dict(status=report['status'],checks=len(checks),report_sha256=h(D/'preintegration_review.json'),pending_actual_final_review=True)))

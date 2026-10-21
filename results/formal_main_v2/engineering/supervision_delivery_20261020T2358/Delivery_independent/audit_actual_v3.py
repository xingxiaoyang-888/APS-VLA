from pathlib import Path
from datetime import datetime,timezone
import argparse,ast,copy,hashlib,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e';M=R/'snapshots/formal_main_v2_run_564be0995e';D=R/'.local/delivery_independent_20261020T2358'
B='results/formal_main_v2/preflight/heartbeat_20261021T0758';E='results/formal_main_v2/engineering/supervision_delivery_20261020T2358';X='results/formal_main_v2/execution/object_single_error_v1'
ap=argparse.ArgumentParser()
for n in ['state','summary','inputs']:ap.add_argument('--'+n+'-sha256',required=True)
a=ap.parse_args()
H=lambda b:hashlib.sha256(b).hexdigest()
checks=[];read_refs={}
def ck(x,n):
 if not x:raise AssertionError(n)
 checks.append({'check':n,'passed':True})
def path(n):
 p=Path(n);p=p if p.is_absolute() else R/p
 ck(p.is_relative_to(R) or p.is_relative_to(S),'allowed_read:'+str(p))
 ck(p.is_file() and p.resolve()==p and not any(q.is_symlink() for q in [p,*p.parents]),'regular:'+str(p))
 return p
def rb(n,sha=None):
 p=path(n);b=p.read_bytes();key=str(p.relative_to(R)) if p.is_relative_to(R) else str(p)
 if sha is not None:ck(H(b)==sha,'pin:'+key)
 v={'path':key,'sha256':H(b),'bytes':len(b)}
 if key in read_refs:ck(read_refs[key]==v,'stable:'+key)
 read_refs[key]=v
 return b
def rd(n,sha=None):return json.loads(rb(n,sha))
def ref(n):rb(n);p=Path(n);key=str(p.relative_to(R)) if p.is_absolute() and p.is_relative_to(R) else str(p);return read_refs[key]
def exactref(v):return rd(v['path'],v['sha256'])
def save(n,x):
 p=D/n;ck(p.parent==D and not p.exists(),'private_new_output:'+n)
 b=(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return {'path':str(p.relative_to(R)),'sha256':H(b),'bytes':len(b)}
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect','socket.bind'):raise RuntimeError('No subprocess, Git, Slurm or network in independent delivery auditor')
 if event=='open':
  p,mode,flags=args
  if isinstance(p,(str,bytes)) and ((mode and any(v in mode for v in 'wax+')) or (isinstance(flags,int) and flags&(1|2|64|512|1024))):
   if not Path(p).resolve().is_relative_to(D):raise RuntimeError('Write outside private audit directory')
sys.addaudithook(guard)
def audit():
 baseline=rd(D/'baseline_capture.json','2c0012f2d4badd50d7d8f9a3edfa9dfeb7f02148519a24913f6785dfcdfb992e')
 old=exactref(baseline['baseline_state']);ck(baseline['baseline_state']['sha256']=='a0d4d98f112adc082a04789c764d8c6006a2133cb61834f4b0e2097f5b64fb10','exact_pre_snapshot_state')
 static=rd(D/'static_review_v6.json','bc6988f3a4053fa4066ee4dd761ca8b13e98292d502a4ab1b71ef7d21a07ae3b');ck(static['status']=='passed_static_review_actual_snapshot_pending' and len(static['checks'])==72,'72_static_helper_checks_only')
 for v in static['source_refs'].values():rb(v['path'],v['sha256'])
 delta=rd(D/'static_review_v7.json','bae3320d61fe52c84a4ff5a9ef451d527ac032bc4832696123deb1a71df8b800');ck(delta['status']=='passed_static_review_actual_snapshot_pending' and len(delta['checks'])==19,'19_exact_v5_helper_delta_checks')
 for v in delta['source_refs']:rb(v['path'],v['sha256'])
 s=rd('results/experiment_supervisor/state.json',a.state_sha256);summary=rd(B+'/final_summary.json',a.summary_sha256);inputs=rd(B+'/final_snapshot_inputs.json',a.inputs_sha256)
 update=rd(B+'/state_and_document_update.json')
 ck(update['state_before']==baseline['baseline_state']['sha256'] and update['state_after']==a.state_sha256,'root_state_receipt_before_after_exact')
 ck(update['summary']==s['last_root_supervision_snapshot']=={'path':B+'/final_summary.json','sha256':a.summary_sha256},'state_summary_exact_pin')
 f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 ck(s['registered_jobs']==old['registered_jobs'] and s['pending_submission']==old['pending_submission'] is None,'registration_and_pending_unchanged')
 ck(ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None,'reservation_and_hold_empty')
 for k in set(ctl)-{'occupied_job_ids'}:ck(ctl[k]==old['autonomous_training_v1'][k],'controller_unmodified:'+k)
 ck(ctl['occupied_job_ids']==['3054201'],'one_registered_active_GPU_identity')
 pairs=ctl['completed_pairs'];want={f'{suite}_k{k}_seed{seed}' for suite in ['libero_10','libero_spatial','libero_object','libero_goal'] for k in [256,128,64] for seed in [17,23,41]}
 ck(set(pairs)==want,'36_fixed_matrix_pairs_preserved')
 for name,v in pairs.items():ck(v['decision']=='complete' and v['completed_by_arm']=={'A':5000,'B':5000} and v['validation_updates']==list(range(0,5001,500)) and v['selected_checkpoints_verified'],'complete_and_11_validation_nodes:'+name)
 ck((f['root_and_independent_completed_arms'],f['root_and_independent_reviewed_arm_updates'],f['current_action_development_trial_count'],f['completed_development_trials'],f['completed_final_trials'])==(72,360000,5800,7012,0),'72_360000_5800_7012_final0')
 for k in ['root_completed_arms','root_completed_pairs','root_reviewed_arm_updates','current_action_development_trials','compatible_development_trials','compatible_legacy_Long_trials','all_historical_accepted_development_trials','unique_development_initial_states','accepted_fixed_observations_including_Long','final_total','final_trials']:
  ck(summary[k]=={'root_completed_arms':72,'root_completed_pairs':36,'root_reviewed_arm_updates':360000,'current_action_development_trials':5800,'compatible_development_trials':6400,'compatible_legacy_Long_trials':600,'all_historical_accepted_development_trials':7012,'unique_development_initial_states':400,'accepted_fixed_observations_including_Long':90,'final_total':35200,'final_trials':0}[k],'unchanged_summary_count:'+k)
 ck(not f['test_opened'] and not f['global_release_created'] and summary['final_sealed'] and not summary['global_release'] and not summary['O2A_released'],'sealed_final_and_O2A')
 ck(summary['new_GPU_jobs']==[] and summary['new_development_accepted']==0 and summary['new_unique_initial_states']==0 and update['new_GPU_jobs']==[] and update['new_development_accepted']==0,'round_zero_new_GPU_and_science')
 # Check inherited final training root/independent receipts without reopening weights or claiming a fresh checkpoint audit.
 for key in ['last_terminals_integrity_review_20261020T1644','supervision_integrity_review_20261020T1644']:
  v=f[key];ck(v['status']=='passed' and v['scientific_gate_changed'] is False,'prior_training_acceptance:'+key)
  for sub in ['root_acceptance','independent_review','summary']:exactref(v[sub])
 obs=rd(B+'/live_observation.json','36b9bfbc9d09e5aeca5fedb1b82abb021dcc41633d6676ab18d68aeef4f4c102');rows=obs['observation']['rows']
 ck(obs['utc']=='2026-10-21T00:03:34.399916+00:00' and obs['state_sha256']==baseline['baseline_state']['sha256'],'one_existing_timestamped_observation_only')
 formal=[j for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2'];ids=[str(v['job_id']) for v in formal]
 ck(len(ids)==len(set(ids))==271,'271_unique_formal_allocations')
 raw_alloc={}
 for line in obs['observation']['raw_sacct'].splitlines():
  parts=line.split('|')
  if parts[0] not in ids:continue
  ck(len(parts)==8 and parts[0] not in raw_alloc,'one_raw_sacct_parent_allocation:'+parts[0])
  tres=dict(x.split('=',1) for x in parts[4].split(',') if '=' in x)
  ngpu=int(tres['gres/gpu']) if 'gres/gpu' in tres else sum(int(v) for k,v in tres.items() if k.startswith('gres/gpu:'))
  raw_alloc[parts[0]]={'GPU_seconds':ngpu*int(parts[3]),'elapsed_seconds':int(parts[3]),'gpus':ngpu}
  ck(rows[parts[0]]['elapsed_seconds']==int(parts[3]) and rows[parts[0]]['gpus']==ngpu,'raw_sacct_independent_GPU_TRES_and_elapsed:'+parts[0])
 ck(set(raw_alloc)==set(ids) and sum(v['GPU_seconds'] for v in raw_alloc.values())==1987496,'all271_raw_allocations_independent_sum_no_double_TRES')
 queue_lines=[line.split('|') for line in obs['observation']['raw_squeue'].splitlines()]
 ck(queue_lines==[['3054201','RUNNING','cti-downstream-gateway-v1:d0143bc88b855ad9f4d6b6008e8373272d55c953d36bba88fbd8840a1090f7d5']],'raw_squeue_exact_one_registered_ACK_token')
 costs={jid:rows[jid]['gpus']*rows[jid]['elapsed_seconds'] for jid in ids};ck(sum(costs.values())==obs['allocated_GPU_seconds']==summary['allocated_GPU_seconds']==1987496,'all_allocations_counted_once_1987496')
 ck(summary['allocated_GPU_hours']==1987496/3600 and summary['cost_final_for_current_registered_set'] is False and summary['cost_observed_utc']==obs['utc'],'GPU_cost_lower_bound_at_observed_UTC')
 prev=exactref(baseline['prior_summary']);ck(summary['newly_accounted_GPU_seconds']==1987496-prev['allocated_GPU_seconds']==1485,'cost_delta1485_only_elapsed_increment')
 ck(rows['3054201']['status']=='RUNNING' and rows['3054201']['elapsed_seconds']==2194 and rows['3054201']['gpus']==1 and obs['capacity']['occupied']==['3054201'] and obs['capacity']['unknown']==[] and obs['capacity']['findings']==[],'one_running_Spatial_at_prior_observation_no_poll')
 ck(rows['3034538']['status']=='COMPLETED' and rows['3034538']['exit_code']=='0:0' and rows['3034538']['gpus']==0 and obs['controller_lease_released'] and not summary['controller_restarted'],'CPU_training_controller_terminal_not_restarted')
 ck(summary['Spatial588']['completed_new_trials_accepted']==0 and summary['Spatial588']['retained_legacy_trials']==12 and summary['Spatial588']['remaining_current_trials_requested']==588 and summary['Spatial588']['mixed600_batch_not_yet_accepted'] and summary['Spatial588']['resubmissions']==0,'Spatial12_legacy_588_current_not_accepted_or_repeated')
 ck(summary['Spatial588']['last_observed_completed_raw_trials'] is None and summary['Spatial588']['live_raw_progress_not_archived'] is True and summary['Spatial588']['status_at_last_observation']=='RUNNING','Spatial_unarchived_progress_not_claimed_or_denominator')
 ck(summary['new_GPU_jobs']==[] and inputs['new_GPU_jobs']==[] and inputs['runtime_installed'] is False and inputs['new_scientific_trials']==0,'CPU_delivery_inputs_no_runtime_GPU_science')
 evidence={}
 for name,v in inputs['evidence'].items():
  ck(v['path'].startswith(E+'/') and '..' not in Path(v['path']).parts,'typed_archived_evidence:'+name);evidence[name]=exactref(v)
 ck(summary['engineering_evidence_manifests']==inputs['evidence'],'summary_exact_input_evidence')
 for name in ['Object_single_error_CPU_review','Object_single_error_production_candidate']:
  ck(summary[name]==inputs[name] and summary[name]['production_ready'] is False,'summary_original_independent_scope:'+name)
  rr=exactref(summary[name]['independent_review']);ck(summary[name]['independent_status']==rr['status'],'actual_independent_status:'+name)
 obj=rd(X+'/root_legacy_adoption.json','c431646cbac00f461177e95361fb8d31d66c78bcfbbfc2b5c766edb8eabd6d24')
 adrows=[json.loads(b) for b in rb(X+'/legacy599_adoption_rows.jsonl','ac792e8d88f251f097f3f0e110e6c32aa45dbacd103404c0189b3bebf56ccb5e').splitlines()]
 add=evidence['Object599_addendum'];ck(add['status']=='passed_legacy599_only' and add['audit_checks_passed']==len(add['checks'])==31550,'Object599_independent_exact31550_checks')
 ck(len(adrows)==obj['legacy_equivalent_trials']==599 and obj['status']=='passed_legacy599_only' and obj['new_scientific_trials']==0 and obj['current_wrapper_generated_trials']==0 and not obj['whole600_admitted'] and not obj['GPU_execution_authorized'],'canonical_Object599_reference_adoption_only')
 ck(add['successes']==520 and add['negative_outcomes']==79 and add['original_GPU_seconds_once']==6713 and not add['whole600_admitted'] and add['all599_exact_raw_start_result_and_executed_byte_links_verified'],'all79_negative_and6713_prior_seconds_preserved')
 ck(summary['Object599']['legacy599_root_adopted'] and summary['Object599']['whole600_production_adopted'] is False and summary['Object599']['single_failure_GPU_authorized'] is False and summary['Object599']['production_runtime_installed'] is False,'Object599_not_whole600_or_new_GPU')
 cpu=evidence['Object_CPU_review'];ck(cpu['status']==inputs['Object_single_error_CPU_review']['independent_status'],'CPU_report_original_status_preserved')
 goal=evidence['Goal_CPU_final_review'];ck(goal['status']=='passed' and goal['blockers']==[] and goal['check_count']==goal['checks_passed_total']==len(goal['checks'])==2068 and not goal['production_ready'] and not goal['prospective_full200_GPU_authorized'],'Goal2068_actual_CPU_checks_not_runtime')
 spec=evidence['Goal_specification'];ck((spec['row_count'],spec['unique_development_states'],spec['maximum_new_attempts'],spec['maximum_control_steps'],spec['maximum_policy_queries'])==(200,100,1,60000,7600) and not spec['production_ready'] and not spec['automatic_retry'] and not spec['final_release'],'Goal_fixed_one_full200_spec_bounds')
 gd=rd(B+'/Goal_prospective_root_decision.json');ck(gd['kind']=='root_prospective_Goal_fixed200_design_choice' and gd['status']=='fixed_design_adopted_runtime_and_GPU_HOLD' and gd['reviewed_by']=='root','Goal_root_design_choice_only')
 ck((gd['maximum_new_attempts'],gd['maximum_trials'],gd['maximum_control_steps'],gd['maximum_policy_queries'])==(1,200,60000,7600) and gd['normal_task_failures_retained'],'Goal_root_exact_bounds_and_negatives')
 ck(gd['specification']==inputs['evidence']['Goal_specification'] and gd['independent_CPU_review']==inputs['evidence']['Goal_CPU_final_review'],'Goal_root_decision_exact_spec_review')
 ck(gd['new_output_path'] is None and gd['submission_token'] is None and not gd['GPU_execution_authorized'] and not gd['production_runtime_installed'] and gd['new_scientific_trials']==0 and not gd['final_release'],'Goal_no_new_runtime_output_token_GPU_science')
 ck(gd['old200']=='retain_whole_batch_historical_HOLD_not_adopted' and gd['remaining_gates']==spec['required_future_gates'][1:],'Goal_old200_HOLD_and_remaining_runtime_gates')
 gsum=copy.deepcopy(inputs['Goal_bounded_CPU_diagnostic']);gsum['root_design_decision']={'path':B+'/Goal_prospective_root_decision.json','sha256':H(rb(B+'/Goal_prospective_root_decision.json'))}
 ck(summary['Goal_bounded_CPU_diagnostic']==gsum,'Goal_summary_only_adds_root_design_ref')
 ck(gsum['query_index']==9 and gsum['query_index_zero_based'] and gsum['policy_call_ordinal']==10 and gsum['step']==72 and gsum['mismatch_pair_in_original200']=={'ordinals':[57,58],'task_id':2,'source_state_index':42} and gsum['two_engineering_trace_difference']=={'ordinal':30,'task_id':1,'source_state_index':12},'old200_and_engineering_mismatches_distinct_zero_based_query')
 ck(gsum['cause_identified'] is False and gsum['old200_HOLD'] and gsum['additional1000_HOLD'] and summary['Goal_original200_and_new_science_HOLD'],'Goal_no_causal_or_old_admission_claim')
 ck(summary['Goal_paired_input_engineering']==prev['Goal_paired_input_engineering'] and summary['Goal_paired_input_engineering']['scientific_trials_added']==0 and summary['Goal_paired_input_engineering']['old200_adopted'] is False,'prior58_engineering_not_reclassified')
 # Independently rebuild the complete state delta: only explicit metadata, cost and document references may change.
 expected=copy.deepcopy(old);expected['last_root_supervision_snapshot']={'path':B+'/final_summary.json','sha256':a.summary_sha256}
 expected['current_round_cost'].update(registered_jobs=271,allocated_gpu_seconds=1987496,allocated_gpu_hours=1987496/3600,final=False,scope='All271 unique formal allocations at '+obs['utc']+'; Spatial3054201 running2194seconds included once, no future/CPU estimate added.')
 expected['autonomous_training_v1']['occupied_job_ids']=['3054201'];ef=expected['formal_main_progress']
 ef['parallel_execution'].update(actual_running_allocated_GPUs=1,registered_requested_active_GPU_jobs=1,status='training_complete_development_recovery_and_bounded_CPU_repairs',latest_root_observation={'path':B+'/live_observation.json','sha256':H(rb(B+'/live_observation.json'))})
 ef['Object599_legacy_adoption_20261020T2358']=summary['Object599'];ef['Goal_bounded_CPU_diagnostic_20261020T2358']=gsum
 ef['Object_single_error_CPU_progress_20261020T2358']={'CPU_review':summary['Object_single_error_CPU_review'],'production_candidate':summary['Object_single_error_production_candidate']}
 ef['downstream_followups_20261020T2358']={'summary':expected['last_root_supervision_snapshot'],'Goal_original200_and_new_science_HOLD':True,'Spatial588_job_id':'3054201','Object599_root_legacy_adopted':True,'Object600_typed_completion_HOLD':True,'single_failure_GPU_authorized':False,'O2A_released':False,'global_release':False}
 ck(s==expected,'entire_state_exact_reconstruction_no_unlisted_change')
 # Verify each immutable package via its actual manifest, including logs ignored by Git.
 archived=[];seen_members={}
 for receiptpath in sorted((R/B).glob('*_archive.json')):
  receipt=rd(receiptpath)
  if receipt.get('status')!='immutable_nonweight_package_archived':continue
  dest=receipt['destination'];ck(dest.startswith(E+'/') and receipt['GPU_jobs_added']==0 and receipt['not_runtime_admission'] and receipt['state_unchanged'],'archive_scope:'+receiptpath.name)
  oldmanifest=receipt['manifest'];parent=Path(oldmanifest['path']).parent;archmanifest=dest+'/'+Path(oldmanifest['path']).stem+'_original.json'
  m=rd(archmanifest,oldmanifest['sha256']);ck(rb(oldmanifest['path'],oldmanifest['sha256'])==rb(archmanifest),'original_manifest_bytes:'+archmanifest)
  members=m['files'];members=[dict(v,path=k) for k,v in members.items()] if isinstance(members,dict) else members;ck(len(members)==receipt['file_count'],'manifest_count:'+dest)
  total=0
  for v in members:
   name=v.get('source',v.get('path'));ck(isinstance(name,str),'manifest_path_string')
   pp=parent.as_posix();relative=name[len(pp)+1:] if name.startswith(pp+'/') else name
   ck(relative and not Path(relative).is_absolute() and '..' not in Path(relative).parts,'manifest_relative:'+relative)
   dst=dest+'/'+relative;src=name if name.startswith(pp+'/') else (parent/relative).as_posix()
   content=rb(dst,v['sha256']);ck(len(content)==v['bytes'],'archived_size:'+dst);ck(content==rb(src,v['sha256']),'source_archive_byte_identity:'+dst)
   if dst in seen_members:ck(seen_members[dst]==v['sha256'],'overlapping_manifest_same_bytes:'+dst)
   seen_members[dst]=v['sha256'];total+=len(content)
  ck(total==receipt['bytes'],'archive_total_bytes:'+dest);archived.append({'receipt':ref(receiptpath),'destination':dest,'manifest':ref(archmanifest),'file_count':len(members),'bytes':total})
 ck(len(archived)>=5,'all_current_CPU_author_independent_packages_archived')
 # Documentation changes are exact additive prefixes, preserving old content bytes by prior hashes.
 snapshotsrc=rb('.local/final_snapshot_20261020T2358_v5.py','23f00b8ca94f92fcf5b34a5c13be9c66ab26c0c707ea6a444ab2d429d84b0b45').decode()
 tree=ast.parse(snapshotsrc)
 def assign_expr(name):
  return next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
 title='## 2026-10-21 07:58监督交付（实际UTC '+summary['utc']+'）'
 common=eval(compile(ast.Expression(assign_expr('common')),'<audited-constant-fstring>','eval'),{'__builtins__':{}},{'title':title,'obsdoc':obs,'cost':1987496,'B':B})
 paperprefix=ast.literal_eval(assign_expr('prefix'));ck('第10次调用' in common and '原因已查明' in common,'corrected_zero_based_timing_wording_retained')
 docchanges=update['document_changes'];ck(set(docchanges)=={x['path'] for x in baseline['documents_before'].values()},'only_seven_prior_docs_changed')
 for name,oldref in baseline['documents_before'].items():
  rel=oldref['path'];raw=rb(rel);prefix=paperprefix if name=='论文方法与实验设置草稿' else common
  ck(raw.startswith(prefix.encode()) and H(raw[len(prefix.encode()):])==oldref['sha256'],'unchanged_document_original_body:'+rel)
  ck(docchanges[rel]=={'before_sha256':oldref['sha256'],'after_sha256':H(raw)},'exact_doc_change_receipt:'+rel)
 blocker=rb('docs/正式下游阻塞登记_20261020T2358.md');ck(blocker==('# 正式下游阻塞登记 20261020T2358\n'+common+'\n'+inputs['blocker_details_markdown']+'\n').encode(),'new_blocker_doc_exact_input_and_summary')
 ck(update['new_blocker_document']['sha256']==H(blocker),'blocker_doc_pinned')
 inv=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');ck(len(inv['files'])==173,'173_source_inventory')
 for rel,want in inv['files'].items():
  for root in [R,S,M]:rb(root/rel,want)
 ck(rb('results/experiment_supervisor/state.json',a.state_sha256)==rb('results/experiment_supervisor/state.json'),'final_state_stable')
 ck(rb(B+'/final_summary.json',a.summary_sha256)==rb(B+'/final_summary.json') and rb(B+'/final_snapshot_inputs.json',a.inputs_sha256)==rb(B+'/final_snapshot_inputs.json'),'final_inputs_summary_stable')
 return {'schema':'formal_main_v2','kind':'root_final_delivery_independent_review','status':'passed_final_delivery_review','reviewed_by':'independent_goal_cpu_gate_2054','blockers':[],'state_sha256':a.state_sha256,'source173_verified':True,'source173_roots':[str(R),str(S),str(M)],'final_sealed':True,'summary':{'path':B+'/final_summary.json','sha256':a.summary_sha256},'inputs':{'path':B+'/final_snapshot_inputs.json','sha256':a.inputs_sha256},'scope':'Actual state, additive documents, explicit frozen CPU package archives, inherited completion receipts, single prior Slurm observation and unique cost reconstruction. No new checkpoint rehash or current Slurm query; no Git index/commit/push execution verified.','training':{'completed_pairs':36,'completed_arms':72,'updates':360000,'all_11_validation_nodes_preserved':True,'fresh_weight_bytes_read':False},'development':{'current':5800,'compatible_whole_batches':6400,'historical':7012,'unique_states':400,'Object_legacy599_adopted_separately':True,'Object599_successes':520,'Object599_negative_outcomes':79,'Object_whole600_admitted':False,'new_scientific_trials':0},'cost':{'observation_utc':obs['utc'],'allocations':271,'GPU_seconds':1987496,'hours':1987496/3600,'lower_bound':True,'new_elapsed_GPU_seconds':1485,'Spatial3054201_seconds':2194,'new_GPU_submissions':0},'Goal':{'old200_and_additional1000_HOLD':True,'cause_identified':False,'root_fixed200_design_adopted_only':True,'runtime_installed':False,'new_output':None,'submission_token':None,'GPU_authorized':False,'max_attempts':1,'max_trials':200,'max_control_steps':60000,'max_policy_queries':7600},'Object_production_candidate':summary['Object_single_error_production_candidate'],'archived_packages':archived,'archived_unique_file_count':len(seen_members),'read_refs':read_refs,'check_count':len(checks),'checks':list(checks),'Git_commit_and_push_pending':True,'Git_source_static_review':ref(D/'static_review_v6.json'),'Git_source_v5_delta_review':ref(D/'static_review_v7.json'),'additional_Slurm_queries':0,'production_state_Git_P_canonical_writes':0,'utc':datetime.now(timezone.utc).isoformat()}
try:
 report=audit()
 # Final immutable check list is copied only after all source reads and private output-path checks.
 out=D/'final_independent_review.json';assert not out.exists()
 report['checks']=tuple(checks);report['check_count']=len(checks)
 b=(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 with out.open('xb') as f:f.write(b)
 print(json.dumps({'status':report['status'],'check_count':len(checks),'path':str(out.relative_to(R)),'sha256':H(b),'bytes':len(b),'state_sha256':a.state_sha256}))
except Exception as exc:
 out=D/'actual_audit_failure_v3.json'
 if not out.exists():
  with out.open('xb') as f:f.write((json.dumps({'error':repr(exc),'traceback':traceback.format_exc(),'checks_completed':checks,'read_refs':read_refs,'state_sha256_argument':a.state_sha256,'no_production_writes':True},sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode())
 raise

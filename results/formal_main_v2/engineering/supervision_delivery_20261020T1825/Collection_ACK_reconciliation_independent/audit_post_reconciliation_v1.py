from pathlib import Path
from datetime import datetime,timezone
import copy,fcntl,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/spatial_collect_reconcile_independent_20261020T1825';H='4d81461eddac21c2e847dbb374f3ef6bcc580918bc297ac30774cc2870c9f705';J='3053503';A=R/'results/formal_main_v2/downstream_gateway'/H
B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0225';SOURCE=R/'.local/reconcile_collect_3053503_20261020T1825_v3.py';SOURCE_SHA='ce6b387be67958c7202c3257daaff09134c63505f08bb9861bb9f45eceaa599f'
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()+b'\n'
def read(p):return json.loads(p.read_bytes())
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def save(name,v):
 p=D/name
 with p.open('xb') as f:f.write(canonical(v))
 return ref(p)
checks=[]
def check(name,v):
 assert v,name;checks.append(name)
check('approved_root_helper_unchanged',sha(SOURCE.read_bytes())==SOURCE_SHA)
with (D/'root_helper_v3_accepted_exact_source.py').open('xb') as f:f.write(SOURCE.read_bytes())
initial=read(D/'pending_state_snapshot.json');commit=read(A/'committed.json');reconciled=read(A/'root_reconciled_submission_observation.json');original_failure=read(A/'failed_transaction.json');job=read(R/('results/formal_main_v2/submissions/'+J+'.json'))
check('canonical_receipts_exact_same',(A/'committed.json').read_bytes()==(B/'Spatial_collect_pending_reconciliation.json').read_bytes())
check('receipt_records_no_resubmit',commit['status']=='submitted_once_reconciled_known_ack' and commit['submission_calls_this_reconciliation']==0 and commit['submitted_once_original_ACK'] is True and commit['original_failure_retained'] is True)
check('single_known_ack_bound',commit['job']==job==read(D/'original_gateway_rebuilt_job.json') and job['job_id']==J and commit['request_token']==initial['pending_submission']['request_token'])
check('original_failure_retained',ref(A/'failed_transaction.json')['sha256']=='54e40ba4e6cea265cad4fd15143c999787433c49a1013ca7656f7d8b0da761c7' and original_failure['state_sha256']==reconciled['state_before'])
check('known_input_preflight_retained',ref(A/'preflight.json')['sha256']=='b5efcf4d3b0748986325b5cee46bc709eb66b73c7c9c868c2991f02949e6cf5e' and ref(A/'sbatch_result.json')['sha256']=='dd2b072922d49d749f3f1b99dd2d1dc3e823c9ec4118b273d7ebe9975d222137')
expected=copy.deepcopy(initial);expected['registered_jobs'].append(job);expected['pending_submission']=None;ctl=expected['autonomous_training_v1'];auth=read(R/'results/formal_main_v2/execution/spatial_collect_action_v1_20261020T1825/submission_authorization.json')
ctl['reserved_GPU_slots']=0;ctl.setdefault('downstream_reservations_consumed',{})[H]={'job_id':J,'reservation':auth['root_reservation'],'request_token':commit['request_token']}
obs=reconciled['observation'];caps=reconciled['capacity'];ids={str(j['job_id']) for j in expected['registered_jobs']};check('all_original_registered_plus_one_observed',set(obs['rows'])==ids and set(obs['queue'])<=ids and not caps['unknown'] and not caps['findings'])
spent=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in expected['registered_jobs'] if j.get('experiment')=='formal_main_v2')
expected['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in expected['registered_jobs']),allocated_gpu_seconds=spent,allocated_gpu_hours=spent/3600,final=False)
expected['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']=len(caps['occupied'])
expected_sha=sha(canonical(expected));check('exact_reconstructed_root_state_matches_real_commit_SHA',expected_sha==commit['state_sha256'])
check('all_original_registry_unchanged',expected['registered_jobs'][:-1]==initial['registered_jobs'])
check('training_and_final_seal_unchanged',expected['formal_main_progress']['root_and_independent_completed_arms']==72 and expected['formal_main_progress']['root_and_independent_reviewed_arm_updates']==360000 and expected['formal_main_progress']['completed_final_trials']==0 and expected['formal_main_progress']['test_opened'] is False and expected['formal_main_progress']['global_release_created'] is False)
with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
 fcntl.flock(lock,fcntl.LOCK_SH)
 try:
  actual_raw=(R/'results/experiment_supervisor/state.json').read_bytes();actual=json.loads(actual_raw)
 finally:fcntl.flock(lock,fcntl.LOCK_UN)
actual_known=[j for j in actual['registered_jobs'] if str(j['job_id'])==J];check('actual_registry_exactly_one_known_job',actual_known==[job])
check('actual_known_pending_not_represented',not actual.get('pending_submission') or actual['pending_submission'].get('request_token')!=commit['request_token'])
check('actual_consumed_reservation_matches',actual['autonomous_training_v1']['downstream_reservations_consumed'][H]==ctl['downstream_reservations_consumed'][H])
actual_same=sha(actual_raw)==expected_sha
if actual_same:check('actual_state_whole_bytes_match_commit',actual_raw==canonical(expected))
save('reconstructed_exact_root_commit_state.json',expected)
post=save('post_reconciliation_independent_review.json',dict(schema='formal_main_v2',kind='Spatial3053503_pending_reconciliation_independent_post_review',status='passed_exact_root_reconciliation',created_utc=datetime.now(timezone.utc).isoformat(),job_id=J,checks=checks,checks_passed=len(checks),root_committed_state_sha256=expected_sha,actual_state_sha256_at_read=sha(actual_raw),actual_state_whole_matches_commit=actual_same,later_mutable_state_changes=not actual_same,later_state_changes_not_audited_here=not actual_same,root_exact_state_reconstructed_from_original_pending_plus_original_reconciliation=True,actual_single_known_registration=True,known_pending_consumed=True,original_failure_and_ACK_retained=True,allocation_seconds_in_reconciliation=obs['rows'][J]['elapsed_seconds'],allocated_GPU_seconds_total_at_reconciliation=spent,cost_recomputed_without_double_add=True,root_registration_does_not_accept_GPU_collect_outputs=True,training72_development_and_final_denominators_unchanged=True,post_read_queries=0,Slurm_submission_calls=0,production_state_writes=0,GPU_results_read=False,refs=[ref(p) for p in [SOURCE,A/'committed.json',A/'root_reconciled_submission_observation.json',A/'failed_transaction.json',R/('results/formal_main_v2/submissions/'+J+'.json'),D/'helper_source_independent_review.json']]))
print(json.dumps(post))

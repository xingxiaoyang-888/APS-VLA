from pathlib import Path
import copy,hashlib,json
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/spatial588_ack_independent_20261020T2253'
AUTH='d0143bc88b855ad9f4d6b6008e8373272d55c953d36bba88fbd8840a1090f7d5'
DG=R/'results/formal_main_v2/downstream_gateway'/AUTH
B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0653'
EXPECTED_STATE='b66d21f7305273a9ac79abc641ea61a0c77b0001f9c2fe40c8b1374addaab2ac'
checks=[];evidence={}
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p,pin=None):
 p=Path(p);b=p.read_bytes()
 if pin is not None:assert hashlib.sha256(b).hexdigest()==pin,str(p)
 evidence[p.relative_to(R).as_posix()]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 return json.loads(b)
def check(name,test):
 if not test:raise AssertionError(name)
 checks.append(name)
def ref(p):return {'path':Path(p).relative_to(R).as_posix(),'sha256':h(p)}
before=read(D/'original_state_snapshot.json')
CURRENT_STATE='a0d4d98f112adc082a04789c764d8c6006a2133cb61834f4b0e2097f5b64fb10'
current=read(R/'results/experiment_supervisor/state.json',CURRENT_STATE)
comm=read(DG/'committed.json','952759f9c8fb1daaf46359cbf046f097233eb94d127d4f22039651da57668fbb')
obs=read(DG/'root_reconciled_submission_observation.json','d38314a320c4e31ab644b2f499ae09a4e78cc1b2256c2cece8e57d360ab51d6c')
dispatch=read(B/'Spatial_dispatch.json')
recon=read(B/'Spatial588_pending_reconciliation.json')
job=read(R/'results/formal_main_v2/submissions/3054201.json')
predicted=read(D/'reconstructed_registered_job.json')
s=copy.deepcopy(before);s['registered_jobs'].append(job);s['pending_submission']=None
s['autonomous_training_v1']['reserved_GPU_slots']=0
s['autonomous_training_v1'].setdefault('downstream_reservations_consumed',{})[AUTH]={'job_id':'3054201','reservation':before['autonomous_training_v1']['reservation_root_record'],'request_token':'cti-downstream-gateway-v1:'+AUTH}
allcost=[obs['observation']['rows'][str(j['job_id'])]['elapsed_seconds']*obs['observation']['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2']
s['current_round_cost'].update(registered_jobs=len(allcost),allocated_gpu_seconds=sum(allcost),allocated_gpu_hours=sum(allcost)/3600,final=False)
s['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']=len(obs['capacity']['occupied'])
reconstructed_bytes=json.dumps(s,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()+b'\n'
check('reconstructed_committed_state_exact_SHA',hashlib.sha256(reconstructed_bytes).hexdigest()==EXPECTED_STATE)
update=read(B/'state_and_document_update.json','e20926b5a6fead9d6fa64f50012450e63392ba37ba6d30c16653a92e6f8993f4')
summary=read(B/'final_summary.json','f4d17e968396671b9e8072de1503133652b437e1dd9eee040f74c5d37a56b12d')
check('root_metadata_update_chain_exact',update['state_before']==EXPECTED_STATE and update['state_after']==CURRENT_STATE and update['summary']==ref(B/'final_summary.json'))
normal=copy.deepcopy(current)
check('root_occupied_ids_exact',normal['autonomous_training_v1']['occupied_job_ids']==obs['capacity']['occupied']==['3054201'])
normal['autonomous_training_v1']['occupied_job_ids']=s['autonomous_training_v1']['occupied_job_ids']
check('root_cost_scope_only_changed',{k:v for k,v in current['current_round_cost'].items() if k!='scope'}=={k:v for k,v in s['current_round_cost'].items() if k!='scope'})
normal['current_round_cost']['scope']=s['current_round_cost']['scope']
extra_progress=['Object599_compatibility_review_20261020T2253','Spatial588_recovery_registration_20261020T2253','downstream_followups_20261020T2253','latest_posttraining_CPU_evidence_20261020T2253']
for key in extra_progress:
 check('only_new_root_metadata:'+key,key in normal['formal_main_progress'] and key not in s['formal_main_progress'])
 del normal['formal_main_progress'][key]
parallel=normal['formal_main_progress']['parallel_execution'];oldparallel=s['formal_main_progress']['parallel_execution']
check('root_parallel_actual_running',parallel['actual_running_allocated_GPUs']==1 and parallel['status']=='training_complete_development_exact_recovery_active')
for key in ['actual_running_allocated_GPUs','status','latest_root_observation']:
 if key in oldparallel:parallel[key]=oldparallel[key]
 else:del parallel[key]
check('root_last_snapshot_exact',normal['last_root_supervision_snapshot']==ref(B/'final_summary.json'))
normal['last_root_supervision_snapshot']=s['last_root_supervision_snapshot']
check('all_current_registration_cost_reservation_and_other_state_unchanged',normal==s)
with (D/'reconstructed_committed_state.json').open('xb') as f:f.write(reconstructed_bytes)

review=read(D/'independent_review.json','60eb3a6e0f79f9a4943a3e6904a65a2d9f94684ff932ab923064faddd8da8568')
check('review_binds_exact_executed_helper',review['helper']=={'path':'.local/reconcile_spatial588_3054201_20261020T2253_v2.py','sha256':'8febf8111c1bcb71c89f05600359865d5708b2e32019295a056f5d7674f2b46f'})
check('exact_job_row_matches_readonly_reconstruction',job==predicted)
check('one_job_append_original_registry_unchanged',s['registered_jobs']==before['registered_jobs']+[job])
check('all_registry_ids_unique',len(s['registered_jobs'])==len({str(j['job_id']) for j in s['registered_jobs']}))
check('pending_cleared_once',before['pending_submission']['known_job_id']=='3054201' and s['pending_submission'] is None)
ctl=s['autonomous_training_v1'];oldctl=before['autonomous_training_v1']
check('existing_slot_consumed',oldctl['reserved_GPU_slots']==1 and ctl['reserved_GPU_slots']==0)
consumed=ctl['downstream_reservations_consumed']
check('only_own_consumed_entry_added',set(consumed)==set(oldctl.get('downstream_reservations_consumed',{}))|{AUTH} and AUTH not in oldctl.get('downstream_reservations_consumed',{}))
check('prior_consumptions_unchanged',all(consumed[k]==v for k,v in oldctl.get('downstream_reservations_consumed',{}).items()))
check('exact_consumption_record',consumed[AUTH]=={'job_id':'3054201','reservation':oldctl['reservation_root_record'],'request_token':'cti-downstream-gateway-v1:'+AUTH})
check('committed_and_copy_exact',comm==recon and comm['job']==job and comm['state_sha256']==EXPECTED_STATE and comm['automatic_retry'] is False and comm['submission_calls_this_reconciliation']==0 and comm['submitted_once_original_ACK'] is True)
check('observed_original_pending_state',obs['state_before']=='182fd8474eb0919f094e9266ca4af487e6f356da34dbbac41e1d291cb6ced55b' and obs['job_id']=='3054201' and obs['submission_calls_this_reconciliation']==0)
check('no_scientific_acceptance',obs['scientific_results_admitted']==0 and obs['mutable_output_proof']['scientific_results_admitted']==0 and obs['immutable_P_rows_verified']==227)
check('exact_mutable_validator',obs['mutable_validator']=={'path':'.local/spatial588_ack_independent_20261020T2253/validate_mutable_outputs_v1.py','sha256':'191dbe411df56fc7ed7bf45d5209655d4939a10be70fd59030c17796998f199a'})
check('original_ACK_retained',h(DG/'sbatch_result.json')=='cba65b7776348747bc6dfa62f4b336643fac38f880e1e6a375df0dfc3b25f52f')
check('original_failure_retained',h(DG/'failed_transaction.json')=='18897d313b1460cf14bbef535171090ff3a72bd29adf03018a65bd02ec1525ff')
check('original_preflight_retained',h(DG/'preflight.json')=='77de2bf6f02d5ea8ca7629a286898105f5c0358c66e2b397717f64ea318254b1')
rows=obs['observation']['rows']
costs={str(j['job_id']):rows[str(j['job_id'])]['elapsed_seconds']*rows[str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2'}
seconds=sum(costs.values())
check('all_formal_allocations_counted_once',s['current_round_cost']['allocated_gpu_seconds']==seconds and s['current_round_cost']['registered_jobs']==len(costs) and s['current_round_cost']['allocated_gpu_hours']==seconds/3600)
check('cost_nonfinal',s['current_round_cost']['final'] is False)
check('legacy393_plus_predispatch2_once',costs['3022743']==393 and costs['3042529']==2 and job['typed_predispatch_history']['prior_GPU_seconds']==395)
check('capacity_all_modes_at_most_8',len(obs['capacity']['occupied'])<=8 and s['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']==len(obs['capacity']['occupied']))
check('dispatch_exact_reconciliation',dispatch['job_id']=='3054201' and dispatch['state_sha256']==EXPECTED_STATE and dispatch['scheduler_observation']==ref(DG/'root_reconciled_submission_observation.json') and dispatch['final_release'] is False and dispatch['new_scientific_results']==0)
# Prove all state differences are exactly the authorized append/reservation/cost/pending/capacity.
expected=copy.deepcopy(before);expected['registered_jobs'].append(job);expected['pending_submission']=None
expected['autonomous_training_v1']['reserved_GPU_slots']=0
expected['autonomous_training_v1'].setdefault('downstream_reservations_consumed',{})[AUTH]=consumed[AUTH]
expected.setdefault('current_round_cost',{}).update(registered_jobs=len(costs),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600,final=False)
expected['formal_main_progress'].setdefault('parallel_execution',{})['registered_requested_active_GPU_jobs']=len(obs['capacity']['occupied'])
check('entire_state_has_only_expected_delta',s==expected)
check('state_unchanged_during_audit',h(R/'results/experiment_supervisor/state.json')==CURRENT_STATE)
report={'schema':'formal_main_v2','kind':'Spatial588_known_ACK_post_registration_independent_review','status':'passed','reviewed_by':'independent','job_id':'3054201','checks':checks,'evidence':evidence,'state_sha256':CURRENT_STATE,'reconstructed_committed_state_sha256':EXPECTED_STATE,'root_metadata_update':ref(B/'state_and_document_update.json'),'preserved_prior_state_pin_refusal':ref(D/'post_registration_audit_v1_failure.json'),'registered_once':True,'pending_submission':None,'reserved_GPU_slots':0,'request_token':'cti-downstream-gateway-v1:'+AUTH,'original_ACK':ref(DG/'sbatch_result.json'),'original_failure':ref(DG/'failed_transaction.json'),'committed':ref(DG/'committed.json'),'root_scheduler_observation':ref(DG/'root_reconciled_submission_observation.json'),'scheduler_status_from_root_snapshot':rows['3054201']['status'],'allocated_GPU_seconds_at_root_snapshot':seconds,'job_GPU_seconds_at_root_snapshot':costs['3054201'],'historical_GPU_seconds':395,'new_Slurm_queries':0,'new_GPU_submissions':0,'state_P_Git_mutations':0,'scientific_results_admitted':0,'final_release':False,'all_success_or_failure_outcomes_unreviewed':True,'utc':datetime.now(timezone.utc).isoformat()}
b=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
with (D/'post_registration_independent_review.json').open('xb') as f:f.write(b)
print(json.dumps({'status':'passed','report':ref(D/'post_registration_independent_review.json'),'checks':len(checks),'allocated_GPU_seconds':seconds,'job_GPU_seconds':costs['3054201'],'new_Slurm_queries':0}))

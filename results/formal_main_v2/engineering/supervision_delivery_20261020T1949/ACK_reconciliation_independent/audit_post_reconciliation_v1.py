from pathlib import Path
from contextlib import contextmanager
import fcntl,hashlib,json,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/k64_spatial_reconcile_independent_20261020T1949';B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0349';A='79d22ee8370f95551c259894ad7deccffa7bebc4a1ffecab1c9d567d393cf855';J='3053875';T=R/'results/formal_main_v2/downstream_gateway'/A
checks=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p.relative_to(R)),'sha256':h(p)}
def ck(n,v):assert v,n;checks.append(n)
def save(name,x):
 p=D/name
 with p.open('x') as f:json.dump(x,f,sort_keys=True,indent=2);f.write('\n')
 return ref(p)
with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
 fcntl.flock(lock,fcntl.LOCK_SH)
 try:
  statep=R/'results/experiment_supervisor/state.json';start=h(statep);s=read(statep)
  comp=read(B/'Spatial64s23_dispatch/completion.json');commit=read(T/'committed.json');root=read(B/'Spatial64s23_pending_reconciliation.json');obs=read(T/'root_reconciled_submission_observation.json');job=read(R/('results/formal_main_v2/submissions/'+J+'.json'));expected=read(D/'helper_proposed_state.json')
  ck('root_helper_exact_pin',h(R/'.local/reconcile_k64_spatial_3053875_20261020T1949.py')=='ffe310f91a936291ac766c190956cb048feeea7fc4d034726a73618861728368')
  ck('root_committed_identical_receipt',root==commit)
  ck('known_job_identical_registry',job==commit['job']==expected['registered_jobs'][-1])
  ck('single_original_ACK',read(T/'sbatch_result.json')['stdout']=='3053875\n' and comp['job_id']==J and commit['submission_calls_this_reconciliation']==0 and comp['submission_calls_this_reconciliation']==0)
  ck('no_automatic_retry',commit['automatic_retry'] is False and comp['automatic_retry'] is False and commit['submitted_once_original_ACK'] is True)
  ck('original_failure_retained',read(T/'failed_transaction.json')['state_sha256']=='13ceb3c9789d93a42c63e7fdc10757744438b7cd51301e47f4527718da531c9a' and commit['original_failure_retained'] is True)
  ck('original_preflight_retained',h(T/'preflight.json')=='82f9b835caa6e85f7ff23ce0607f1dcf3ec9b4584299e1c8c6ffcccbd9bd65c6')
  ck('root_observed_exact_registry',set(obs['observation']['rows'])=={str(j['job_id']) for j in expected['registered_jobs']})
  ck('known_token',obs['request_token']==commit['request_token']=='cti-downstream-gateway-v1:'+A and job['downstream_gateway']['request_token']==commit['request_token'])
  ck('original_full_capacity_clean',obs['capacity']['unknown']==[] and obs['capacity']['findings']==[] and len(obs['capacity']['occupied'])<=8)
  ck('known_requested_single_gpu',obs['observation']['rows'][J]['gpus']==1 and job['gpus']==1)
  oldcost=expected['current_round_cost'];oldcost['registered_jobs']=sum(j.get('experiment')=='formal_main_v2' for j in expected['registered_jobs']);oldcost['allocated_gpu_seconds']=sum(obs['observation']['rows'][str(j['job_id'])]['elapsed_seconds']*obs['observation']['rows'][str(j['job_id'])]['gpus'] for j in expected['registered_jobs'] if j.get('experiment')=='formal_main_v2');oldcost['allocated_gpu_hours']=oldcost['allocated_gpu_seconds']/3600;oldcost['final']=False
  expected['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']=len(obs['capacity']['occupied'])
  digest=hashlib.sha256((json.dumps(expected,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()).hexdigest()
  ck('reconstructed_exact_entire_committed_state',digest==commit['state_sha256']==comp['state_sha256'])
  ck('reconstruction_cleared_only_original_pending',expected['pending_submission'] is None and expected['autonomous_training_v1']['reserved_GPU_slots']==0)
  ck('reservation_consumed_once',expected['autonomous_training_v1']['downstream_reservations_consumed'][A]['job_id']==J)
  ck('current_registry_has_same_job_once',sum(str(j['job_id'])==J for j in s['registered_jobs'])==1 and next(j for j in s['registered_jobs'] if str(j['job_id'])==J)==job)
  ck('current_pending_not_spatial',not s.get('pending_submission') or s['pending_submission'].get('known_job_id')!=J)
  ck('root72_final_still_sealed',expected['formal_main_progress']['root_and_independent_completed_arms']==72 and s['formal_main_progress']['root_and_independent_completed_arms']==72 and s['formal_main_progress']['completed_final_trials']==0 and s['formal_main_progress']['global_release_created'] is False)
  ck('independent_post_ref',comp['post_readiness_review']=={'path':'.local/k64_seed23_bridges_independent_20261020T1949/post_readiness/Spatial/post_readiness_independent.json','sha256':'31ef1a9894d37d9a07d99351fc07121d0397fedcc6d7e119ae3df8f66bfcb8de'})
  ck('root_readiness_ref',comp['root_readiness_receipt']=={'path':str((B/'Spatial64s23_runtime_readiness_root.json').relative_to(R)),'sha256':'9a85ad40763f3d31a5b7bf6fa3c2c23abf82ff27f3499e3663db9dd88d6c3f1e'})
  ck('state_readonly',h(statep)==start)
 finally:fcntl.flock(lock,fcntl.LOCK_UN)
proof=save('actual_reconstructed_committed_state.json',expected)
r=save('post_reconciliation_independent_review.json',{'schema':'formal_main_v2','kind':'exact_3053875_pending_reconciliation_post_review','status':'passed','reviewed_by':'independent','job_id':J,'entrypoint_sha256':'ffe310f91a936291ac766c190956cb048feeea7fc4d034726a73618861728368','checks':checks,'checks_passed':len(checks),'reconstructed_entire_committed_state':proof,'completion':ref(B/'Spatial64s23_dispatch/completion.json'),'committed':ref(T/'committed.json'),'root_observation':ref(T/'root_reconciled_submission_observation.json'),'original_failure':ref(T/'failed_transaction.json'),'state_at_read_sha256':start,'current_state_may_include_following_Object_transaction':True,'scientific_trials_added':0,'GPU_results_read':False,'submission_calls':0,'Slurm_queries':0,'state_writes':0,'blockers':[]})
print(json.dumps(r))

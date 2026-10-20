from pathlib import Path
from contextlib import contextmanager
import fcntl,hashlib,json,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/k64_spatial_reconcile_independent_20261020T1949/Object3053894';B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0349';A='36b24fd96344e48b5241a5253b807e4f8f6e65a997713c796d8f471f8c2f2b74';J='3053894';T=R/'results/formal_main_v2/downstream_gateway'/A
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
  comp=read(B/'Object64s23_dispatch/completion.json');commit=read(T/'committed.json');root=read(B/'Object64s23_pending_reconciliation.json');obs=read(T/'root_reconciled_submission_observation.json');job=read(R/('results/formal_main_v2/submissions/'+J+'.json'));expected=read(D/'actual_pending_state_before.json');expected['registered_jobs'].append(read(D/'original_gateway_rebuilt_job.json'));expected['pending_submission']=None;expected['autonomous_training_v1']['reserved_GPU_slots']=0;expected['autonomous_training_v1'].setdefault('downstream_reservations_consumed',{})[A]={'job_id':J,'reservation':expected['autonomous_training_v1']['reservation_root_record'],'request_token':'cti-downstream-gateway-v1:'+A}
  ck('root_helper_exact_pin',h(R/'.local/reconcile_k64_object_3053894_20261020T1949.py')=='313d9db3fbf3750012695df185c34279b04aa768b7c9c6b9daa5fe3bd8acd2ef')
  ck('root_committed_identical_receipt',root==commit)
  ck('known_job_identical_registry',job==commit['job']==expected['registered_jobs'][-1])
  ck('single_original_ACK',read(T/'sbatch_result.json')['stdout']=='3053894\n' and comp['job_id']==J and commit['submission_calls_this_reconciliation']==0 and comp['submission_calls_this_reconciliation']==0)
  ck('no_automatic_retry',commit['automatic_retry'] is False and comp['automatic_retry'] is False and commit['submitted_once_original_ACK'] is True)
  ck('original_failure_retained',read(T/'failed_transaction.json')['state_sha256']=='692d9d53a9707671526eab64546e41c87fa12d6716c0762212e04e448079fcf9' and commit['original_failure_retained'] is True)
  ck('original_preflight_retained',h(T/'preflight.json')=='2f1e28cc16d1d23bade3626377a267cfcab0fb782b2503826aa1022f13b20627')
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
  ck('current_pending_not_Object',not s.get('pending_submission') or s['pending_submission'].get('known_job_id')!=J)
  ck('root72_final_still_sealed',expected['formal_main_progress']['root_and_independent_completed_arms']==72 and s['formal_main_progress']['root_and_independent_completed_arms']==72 and s['formal_main_progress']['completed_final_trials']==0 and s['formal_main_progress']['global_release_created'] is False)
  ck('independent_post_ref',comp['post_readiness_review']=={'path':'.local/k64_seed23_bridges_independent_20261020T1949/post_readiness/Object/post_readiness_independent.json','sha256':'714a5e5468e3366b548617b7fb8f58638830b25aff75062f16c1f560994b9719'})
  ck('root_readiness_ref',comp['root_readiness_receipt']=={'path':str((B/'Object64s23_runtime_readiness_root.json').relative_to(R)),'sha256':'24e7511cba602382662a900ed4b673ab5c5ae729186078c582c24e64890340ea'})
  ck('state_readonly',h(statep)==start)
 finally:fcntl.flock(lock,fcntl.LOCK_UN)
proof=save('actual_reconstructed_committed_state.json',expected)
r=save('post_reconciliation_independent_review.json',{'schema':'formal_main_v2','kind':'exact_3053894_pending_reconciliation_post_review','status':'passed','reviewed_by':'independent','job_id':J,'entrypoint_sha256':'313d9db3fbf3750012695df185c34279b04aa768b7c9c6b9daa5fe3bd8acd2ef','checks':checks,'checks_passed':len(checks),'reconstructed_entire_committed_state':proof,'completion':ref(B/'Object64s23_dispatch/completion.json'),'committed':ref(T/'committed.json'),'root_observation':ref(T/'root_reconciled_submission_observation.json'),'original_failure':ref(T/'failed_transaction.json'),'state_at_read_sha256':start,'current_state_may_include_following_root_transactions':True,'scientific_trials_added':0,'GPU_results_read':False,'submission_calls':0,'Slurm_queries':0,'state_writes':0,'blockers':[]})
print(json.dumps(r))

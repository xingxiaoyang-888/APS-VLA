from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,sys,fcntl,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261019T2318'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','commit1518_ctl')
g=load('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','commit1518_gateway')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';before=h(statepath);old=json.loads(statepath.read_text());s=copy.deepcopy(old);p=s['pending_submission'];ctl=s['autonomous_training_v1']
 assert p['known_job_id']=='3042529' and p['status']=='submitted_identifier_observed' and p['automatic_retry'] is False
 ref={'path':'results/formal_main_v2/execution/action_spatial_resume_0943/submission_authorization.json','sha256':'55f6c06a83847f8f60850309cdade6991cc70ba3e83451f086632c3d76504cd6'}
 assert p['authorization']==ref and p['request_token']=='cti-downstream-gateway-v1:'+ref['sha256']
 auth,e,plan,scientific,prepared=g.validate_authorization(R,ref)
 assert ctl['reserved_GPU_slots']==1 and ctl['reservation_root_record']==auth['root_reservation']
 assert ref['sha256'] not in ctl.get('downstream_reservations_consumed',{})
 owner=c.read_json(R/'results/formal_main_v2/autonomous_training/run_v1/owner.json')
 assert owner['owner_id']==ctl['owner_id'] and str(owner['coordinator_job_id'])==ctl['controller_job_id']==auth['controller_job_id']=='3034538'
 lease=Path(owner['lock']);assert lease==R/'results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock' and lease.is_file() and not lease.is_symlink()
 with lease.open('rb') as f:
  held=False
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
  except BlockingIOError:held=True
 assert held
 prepared_bytes=(R/auth['prepared_invocation']['path']).read_bytes();assert json.loads(prepared_bytes)==prepared
 assert h(R/p['invocation'])==h(P/p['invocation'])==p['invocation_sha256']==hashlib.sha256(prepared_bytes).hexdigest()=='6984d4dceeac9a88cb424fd986daef31595cae3e107581e9acfc4b7c96468261'
 audit=R/p['audit_relative'];ack=json.loads((audit/'sbatch_result.json').read_text());assert ack['returncode']==0 and ack['stdout']=='3042529\n' and not ack['stderr'] and ack['actual_sbatch_argv']==p['actual_sbatch_argv']
 original_fail=h(audit/'failed_transaction.json')
 bundle={'plan':plan,'invocation':prepared,'invocation_bytes':prepared_bytes}
 assert g.submission_argv(bundle,p['request_token'])==p['actual_sbatch_argv']
 gateway=g.Gateway(R,c,None,None,None,auth,ref,e);job=gateway._job('3042529',bundle,p['request_token'],p['actual_sbatch_argv'])
 assert not any(str(j['job_id'])=='3042529' for j in s['registered_jobs'])
 assert not (R/'results/formal_main_v2/submissions/3042529.json').exists() and not (R/B/'Spatial_pending_reconciliation.json').exists()
 jobs=s['registered_jobs']+[job];scheduler=c.Slurm(timeout=45);snapshot=scheduler.observe(jobs)
 corroboration=g.corroborate_new_job(scheduler,job,snapshot);caps=g.reconcile_submission(c,jobs,snapshot,job,p['request_token'],auth['controller_job_id'],corroboration)
 assert snapshot['rows']['3034538']['status']=='RUNNING' and snapshot['rows']['3034538']['gpus']==0 and len(caps['occupied'])<=8
 row=snapshot['rows']['3042529'];assert row['status']=='FAILED' and row['exit_code']=='1:0' and row['elapsed_seconds']==2 and row['gpus']==1 and row['node']=='gpu4002'
 job.update(status=row['status'],exit_code=row['exit_code'],elapsed_seconds=row['elapsed_seconds'],node=row['node'],reconciled_after_failed_submission_transaction=True)
 s['registered_jobs'].append(job);s['pending_submission']=None
 seconds=sum(snapshot['rows'][str(j['job_id'])]['elapsed_seconds']*snapshot['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 cost=s.setdefault('current_round_cost',{});cost.update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 ctl['reserved_GPU_slots']=0;ctl.setdefault('downstream_reservations_consumed',{})[ref['sha256']]=dict(job_id='3042529',reservation=auth['root_reservation'],request_token=p['request_token'])
 s.setdefault('formal_main_progress',{}).setdefault('parallel_execution',{})['registered_requested_active_GPU_jobs']=len(caps['occupied'])
 assert s['registered_jobs'][:-1]==old['registered_jobs']
 before_ctl=copy.deepcopy(old['autonomous_training_v1']);after_ctl=copy.deepcopy(ctl)
 for k in ('reserved_GPU_slots','downstream_reservations_consumed'):before_ctl.pop(k,None);after_ctl.pop(k,None)
 assert before_ctl==after_ctl
 expected=copy.deepcopy(old);expected['registered_jobs']=copy.deepcopy(s['registered_jobs']);expected['pending_submission']=None;expected['current_round_cost']=copy.deepcopy(cost);expected['autonomous_training_v1']=copy.deepcopy(ctl)
 expected['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']=len(caps['occupied']);assert expected==s
 e.unchanged();assert h(statepath)==before and h(audit/'failed_transaction.json')==original_fail
 receipt=dict(schema='formal_main_v2',kind='root_exact_pending_reconciliation',status='failed_job_registered_no_retry',utc=datetime.now(timezone.utc).isoformat(),pending_before=p,state_before_sha256=before,job=job,observation=snapshot,scontrol_corroboration=corroboration,capacity=caps,controller_owner=owner,lifecycle_lease_held=held,read_evidence_sha256=e.hashes,original_failed_transaction_sha256=original_fail,reservation_consumed=True,scientific_stage_complete=False,scientific_results_added=0,submissions=0,automatic_retry=False,job_GPU_seconds=2,all_formal_GPU_seconds=seconds)
 g.record(R/B/'Spatial_pending_reconciliation.json',receipt)
 g.record(R/'results/formal_main_v2/submissions/3042529.json',job)
 c.atomic_json(statepath,s,before)
 g.record(R/B/'Spatial_pending_reconciliation_commit.json',dict(status='committed_failed_job_only',state_after_sha256=h(statepath),receipt={'path':B+'/Spatial_pending_reconciliation.json','sha256':h(R/B/'Spatial_pending_reconciliation.json')},job_id='3042529',pending_cleared_after_exact_identity_proof=True,reservation_remaining=0,submissions=0,automatic_retry=False))
 print(json.dumps(dict(status='failed_job_registered_no_retry',job='3042529',pending=None,occupied=len(caps['occupied']),GPU_hours=seconds/3600,receipt=B+'/Spatial_pending_reconciliation.json',sha256=h(R/B/'Spatial_pending_reconciliation.json'))))

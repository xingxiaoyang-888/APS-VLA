from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import copy,fcntl,hashlib,importlib.util,json,subprocess,sys
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/spatial_collect_reconcile_independent_20261020T1825/Object3053518'
J='3053518';H='83c82bdaa4a61695d0d35b739dde63e88144a2034b9a5f24c10553f75c9254d5';A=R/'results/formal_main_v2/downstream_gateway'/H
G='scripts/ops/formal_action_deployment_posttraining_v1/gateway.py';GP='4a11a62e817cd96523cd8f06aa0c3c71e12208f1b3a6b487799160915e59ec83'
C='scripts/ops/formal_autonomous_training_v1/controller.py';CP='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes())}
def save(n,v):
 p=D/n
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
def load(rel,pin,name):
 raw=(R/rel).read_bytes();assert sha(raw)==pin
 sp=importlib.util.spec_from_file_location(name,R/rel);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;exec(compile(raw,str(R/rel),'exec'),m.__dict__);return m
calls=[]
def runner(argv,**kw):
 assert argv[0] in {'sacct','squeue','scontrol'}
 assert J in argv or any(x==J for x in argv)
 if argv[0] in {'sacct','squeue'}:assert argv[argv.index('-j')+1]==J
 else:assert argv==['scontrol','show','job','-o',J]
 calls.append(argv);return subprocess.run(argv,**kw)
g=load(G,GP,'spatial_reconcile_ind_gateway');c=load(C,CP,'spatial_reconcile_ind_controller')
with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
 fcntl.flock(lock,fcntl.LOCK_SH)
 try:
  raw=(R/g.STATE).read_bytes();state=json.loads(raw);pending=state['pending_submission']
  assert pending['known_job_id']==J and pending['status']=='submitted_identifier_observed' and pending['authorization']['sha256']==H
  assert pending['automatic_retry'] is False and pending['requested_gpus']==1
  assert not any(str(j['job_id'])==J for j in state['registered_jobs'])
  before_sha=sha(raw)
  pre=json.loads((A/'preflight.json').read_bytes());ack=json.loads((A/'sbatch_result.json').read_bytes());fail=json.loads((A/'failed_transaction.json').read_bytes())
  assert g.parse_ack(SimpleNamespace(**ack),{str(j['job_id']) for j in state['registered_jobs']})==J
  assert ack['stdout']==J+'\n' and ack['returncode']==0
  assert fail['error']=='post-submit accounting incomplete' and fail['automatic_retry'] is False and fail['state_sha256']==before_sha
  assert pending['actual_sbatch_argv']==ack['actual_sbatch_argv']==pre['actual_sbatch_argv']
  assert pending['request_token']==pre['request_token']=='cti-downstream-gateway-v1:'+H
  for k in ['authorization','invocation_sha256','plan_sha256']:
   if k!='plan_sha256':assert pending[k]==pre[k]
  auth,e,plan,science,prepared=g.validate_authorization(R,pending['authorization'])
  assert state['autonomous_training_v1']['reserved_GPU_slots']==1 and state['autonomous_training_v1']['reservation_root_record']==auth['root_reservation']
  invraw=(R/plan['invocation_relative']).read_bytes()
  assert sha(invraw)==pending['invocation_sha256']==pre['invocation_sha256']
  assert (P/plan['invocation_relative']).read_bytes()==invraw and json.loads(invraw)==prepared
  assert plan['plan_sha256']==pending['plan_sha256'] and plan['invocation']['stage']=='collect' and plan['invocation']['suite']=='libero_object'
  gateway=g.Gateway(R,c,None,None,None,auth,pending['authorization'],e)
  job=gateway._job(J,{'plan':plan,'invocation':prepared,'invocation_bytes':invraw},pending['request_token'],pending['actual_sbatch_argv'])
  scheduler=c.Slurm(runner=runner,timeout=30);obs=scheduler.observe([job]);cor=g.corroborate_new_job(scheduler,job,obs)
  assert set(obs['rows'])=={J};row=obs['rows'][J]
  g.check_observed_identity(job,row,obs['queue'].get(J),c.TERMINAL,required_token=pending['request_token'],corroboration=cor)
  assert row['gpus']==1
  if row['scheduler_comment']:assert row['scheduler_comment']==pending['request_token']
  assert (R/g.STATE).read_bytes()==raw
  e.unchanged()
  save('pending_state_snapshot.json',state)
 finally:fcntl.flock(lock,fcntl.LOCK_UN)
save('exact_job_observation.json',dict(observation=obs,corroboration=cor,query_argv=calls))
save('original_gateway_rebuilt_job.json',job)
report=save('submission_evidence_independent_review.json',dict(schema='formal_main_v2',kind='Object3053518_known_submission_readonly_independent_review',status='passed_exact_known_submission_identity_pending_root_registration',created_utc=datetime.now(timezone.utc).isoformat(),job_id=J,state_sha256=before_sha,authorization=pending['authorization'],request_token=pending['request_token'],invocation_sha256=pending['invocation_sha256'],root_preflight=ref(A/'preflight.json'),exact_ACK=ref(A/'sbatch_result.json'),retained_failure=ref(A/'failed_transaction.json'),registered_before=False,pending_retained=True,reserved_slots_before=1,actual_status=row['status'],actual_gpus=row['gpus'],identity_corroborated=True,rebuilt_job=ref(D/'original_gateway_rebuilt_job.json'),queries_exact_known_job_only=True,original_authorization_revalidated=True,root_and_runtime_invocation_bytes_identical=True,scientific_GPU_result_read=False,Slurm_submissions=0,production_writes=0,required_next_step='Root single-use writer-lock+CAS reconciliation of registered history plus exactly known job with original gateway.reconcile_submission; preserve failure, write original job/submission/committed records, consume original reservation, clear only matching pending after exact identity; no sbatch or invocation rewrite'))
print(json.dumps(report))

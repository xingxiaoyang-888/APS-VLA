from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,sys,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261019T2318'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def save(rel,v):
 with (R/rel).open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','reconcile1518_ctl')
g=load('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','reconcile1518_gateway')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';before=h(statepath);s=json.loads(statepath.read_text());p=s['pending_submission'];assert p['known_job_id']=='3042529'
 ref={'path':'results/formal_main_v2/execution/action_spatial_resume_0943/submission_authorization.json','sha256':'55f6c06a83847f8f60850309cdade6991cc70ba3e83451f086632c3d76504cd6'}
 assert p['authorization']==ref
 auth,e,plan,scientific,prepared=g.validate_authorization(R,ref)
 prepared_bytes=(R/auth['prepared_invocation']['path']).read_bytes();assert json.loads(prepared_bytes)==prepared
 assert h(R/p['invocation'])==h(P/p['invocation'])==p['invocation_sha256']==hashlib.sha256(prepared_bytes).hexdigest()
 audit=R/p['audit_relative'];ack=json.loads((audit/'sbatch_result.json').read_text());assert ack['returncode']==0 and ack['stdout']=='3042529\n' and not ack['stderr'] and ack['actual_sbatch_argv']==p['actual_sbatch_argv']
 bundle={'plan':plan,'invocation':prepared,'invocation_bytes':prepared_bytes}
 assert g.submission_argv(bundle,p['request_token'])==p['actual_sbatch_argv']
 gateway=g.Gateway(R,c,None,None,None,auth,ref,e);job=gateway._job('3042529',bundle,p['request_token'],p['actual_sbatch_argv'])
 assert not any(j['job_id']=='3042529' for j in s['registered_jobs'])
 jobs=s['registered_jobs']+[job];scheduler=c.Slurm(timeout=45);snapshot=scheduler.observe(jobs)
 result=dict(schema='formal_main_v2',utc=datetime.now(timezone.utc).isoformat(),state_sha256=before,pending=p,job=job,observation=snapshot,read_evidence_sha256=e.hashes,missing_rows=sorted({j['job_id'] for j in jobs}-set(snapshot['rows'])),extra_rows=sorted(set(snapshot['rows'])-{j['job_id'] for j in jobs}),unexpected_queue=sorted(set(snapshot['queue'])-{j['job_id'] for j in jobs}),previous_failure=json.loads((audit/'failed_transaction.json').read_text()),writes_to_state=False,submissions=0)
 try:
  corroboration=g.corroborate_new_job(scheduler,job,snapshot);caps=g.reconcile_submission(c,jobs,snapshot,job,p['request_token'],auth['controller_job_id'],corroboration)
  result.update(status='actual_identity_and_capacity_passed',scontrol_corroboration=corroboration,capacity=caps)
 except Exception as ex:result.update(status='reconciliation_still_blocked',error=str(ex))
 e.unchanged();assert h(statepath)==before
 save(B+'/Spatial_pending_probe_v2.json',result)
 print(json.dumps({k:result.get(k) for k in ['status','missing_rows','extra_rows','unexpected_queue','capacity','error']}))
 print(json.dumps(dict(receipt=B+'/Spatial_pending_probe_v2.json',sha256=h(R/B/'Spatial_pending_probe_v2.json'),job=job['job_id'],state_unchanged=True)))

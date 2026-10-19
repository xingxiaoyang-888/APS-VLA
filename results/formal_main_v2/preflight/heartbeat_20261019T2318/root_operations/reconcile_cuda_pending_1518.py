from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,sys,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261019T2318'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','cuda1518ctl')
d=load('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','cuda1518identity')
g=load('scripts/ops/formal_cuda_continuous_admission_v1/gateway.py','a0f81f18ccdb6f9b0cd5f5f3f871b3f6ab451809a1c6386e347ea3602abd9792','cuda1518gateway')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';before=h(statepath);old=json.loads(statepath.read_text());s=copy.deepcopy(old);p=s['pending_submission'];jid='3042627';ctl=s['autonomous_training_v1']
 ref={'path':'configs/experiments/formal_main_v2_cuda_continuous_3039258_v1.json','sha256':'5f86034d43017d3f89b0d3a73cd90dd8bd22b0b8a54461d0b0a51e5f8df6220e'}
 assert p['kind']=='cuda_continuous_admission_pending' and p['known_job_id']==jid and p['status']=='submitted_identifier_observed' and p['retry_permitted'] is False
 assert p['authorization']==ref and p['request_token']=='cti-cuda-continuous-v1:'+ref['sha256'] and p['pair_key']=='libero_object_k256_seed23'
 assert not any(str(j['job_id'])==jid for j in s['registered_jobs']) and not (R/f'results/formal_main_v2/submissions/{jid}.json').exists()
 auth,e=g.validate_authorization(R,ref);audit=R/p['audit_relative'];ack=json.loads((audit/'sbatch_result.json').read_text());pre=json.loads((audit/'preflight.json').read_text());original_fail=h(audit/'failed_transaction.json')
 assert ack['returncode']==0 and ack['stdout']==jid+'\n' and ack['stderr']=='' and ack['actual_sbatch_argv']==p['actual_sbatch_argv']==pre['actual_sbatch_argv']
 invraw=(R/p['invocation']).read_bytes();assert h(R/p['invocation'])==h(P/p['invocation'])==p['invocation_sha256']==pre['invocation_sha256']=='69af3f5116e56c1ca89e8993f2f7e7685105c91c4d9ce2f35613972e5de9f47e'
 inv=json.loads(invraw);assert inv==pre['invocation'];plan=dict(invocation=inv,invocation_relative=p['invocation'],wrapper=str(P/'scripts/server/formal_asset_main.slurm'))
 args,raw,invsha,token=g.sbatch_argv(plan,ref);assert args==p['actual_sbatch_argv'] and raw==invraw and invsha==p['invocation_sha256'] and token==p['request_token']
 gateway=g.Gateway(R,c,d,None,None,None,auth,ref,e);job=gateway.job(jid,plan,invsha,args,token);jobs=s['registered_jobs']+[job]
 scheduler=c.Slurm(timeout=45);obs=scheduler.observe(jobs);cor=d.corroborate_new_job(scheduler,job,obs);cap=d.reconcile_submission(c,jobs,obs,job,token,auth['controller_job_id'],cor)
 owner=g.controller_owner(R,s,obs,auth);assert owner==pre['controller_owner']
 row=obs['rows'][jid];assert row['status'] in ('RUNNING','PENDING') and row['gpus']==1 and len(cap['occupied'])+ctl.get('reserved_GPU_slots',0)<=8
 assert 'libero_object_k256_seed23' in ctl['blocked_pairs']
 job.update(status=row['status'],elapsed_seconds=row['elapsed_seconds'],exit_code=row['exit_code'],node=row['node'],reconciled_after_submission_accounting_failure=True)
 s['registered_jobs'].append(job);s['pending_submission']=None
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 tracking=s['formal_main_progress']['parallel_execution']['pair_tracking'];assert p['pair_key'] in tracking
 tracking[p['pair_key']].update(active_job_id=jid,segment_target=5000,continuous_admission=ref)
 s['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied'])
 assert s['registered_jobs'][:-1]==old['registered_jobs'] and s['autonomous_training_v1']==old['autonomous_training_v1']
 expected=copy.deepcopy(old);expected['registered_jobs']=copy.deepcopy(s['registered_jobs']);expected['pending_submission']=None;expected['current_round_cost']=copy.deepcopy(s['current_round_cost']);expected['formal_main_progress']['parallel_execution']=copy.deepcopy(s['formal_main_progress']['parallel_execution']);assert s==expected
 e.unchanged();assert h(statepath)==before and h(audit/'failed_transaction.json')==original_fail
 receipt=dict(schema='formal_main_v2',kind='root_exact_pending_reconciliation',status='known_active_CUDA_continuation_registered_no_resubmit',utc=datetime.now(timezone.utc).isoformat(),pending_before=p,state_before_sha256=before,job=job,observation=obs,scontrol_corroboration=cor,capacity=cap,controller_owner=owner,read_evidence_sha256=e.hashes,original_failed_transaction_sha256=original_fail,reservations_consumed=False,controller_block_preserved=True,scientific_training_complete=False,submissions=0,automatic_retry=False,all_formal_GPU_seconds=seconds)
 g.record(R/B/'CUDA_pending_reconciliation.json',receipt);g.record(R/f'results/formal_main_v2/submissions/{jid}.json',job);c.atomic_json(statepath,s,before)
 g.record(R/B/'CUDA_pending_reconciliation_commit.json',dict(status='committed_existing_active_job_only',job_id=jid,state_after_sha256=h(statepath),receipt=dict(path=B+'/CUDA_pending_reconciliation.json',sha256=h(R/B/'CUDA_pending_reconciliation.json')),pending_cleared_after_exact_identity=True,submissions=0,automatic_retry=False))
 print(json.dumps(dict(status='existing_CUDA_job_registered',job_id=jid,job_state=row['status'],GPU_jobs=len(cap['occupied']),GPU_hours=seconds/3600,receipt=B+'/CUDA_pending_reconciliation.json',sha256=h(R/B/'CUDA_pending_reconciliation.json'))))

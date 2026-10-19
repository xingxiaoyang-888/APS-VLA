from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,importlib.util,json,os,subprocess,sys,traceback
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/cuda_pending_reconciliation_independent_1518'
pins={
'.local/reconcile_cuda_pending_1518.py':'000987b4f724d3777757f0ff82eabc8660fc150ae875c444030b09b65db4e54a',
'scripts/ops/formal_autonomous_training_v1/controller.py':'acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363',
'scripts/ops/formal_action_deployment_v1/gateway.py':'8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a',
'scripts/ops/formal_cuda_continuous_admission_v1/gateway.py':'a0f81f18ccdb6f9b0cd5f5f3f871b3f6ab451809a1c6386e347ea3602abd9792'}
evidence={};traces=[];checks=[];out={'schema':'formal_main_v2','kind':'independent_known_CUDA_submission_readonly_check','job_id':'3042627','queries':traces,'checks':checks,'production_writes':False,'submissions':0,'cancellations':0,'created_utc':datetime.now(timezone.utc).isoformat()}
def read(p):
 raw=Path(p).read_bytes();evidence[str(p)]=hashlib.sha256(raw).hexdigest();return raw
def load(rel,name):
 raw=read(R/rel);assert hashlib.sha256(raw).hexdigest()==pins[rel]
 sp=importlib.util.spec_from_file_location(name,R/rel);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;exec(compile(raw,str(R/rel),'exec'),m.__dict__);return m
def check(name,value):
 assert value,name
 checks.append(name)
def runner(argv,**kwargs):
 assert argv[0] in ('sacct','squeue','scontrol')
 answer=subprocess.run(argv,**kwargs)
 traces.append(dict(argv=argv,returncode=answer.returncode,stdout=answer.stdout,stderr=answer.stderr))
 return answer
try:
 raw=read(R/'.local/reconcile_cuda_pending_1518.py');check('candidate exact SHA',hashlib.sha256(raw).hexdigest()==pins['.local/reconcile_cuda_pending_1518.py'])
 tree=ast.parse(raw)
 check('no submit, cancellation or Science prepare call',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('submit','prepare') for n in ast.walk(tree)))
 check('original writer lock retained',any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='exclusive_lock' for n in ast.walk(tree)))
 c=load('scripts/ops/formal_autonomous_training_v1/controller.py','cuda_ind_ctl')
 d=load('scripts/ops/formal_action_deployment_v1/gateway.py','cuda_ind_identity')
 g=load('scripts/ops/formal_cuda_continuous_admission_v1/gateway.py','cuda_ind_gateway')
 statepath=R/'results/experiment_supervisor/state.json';state_raw=read(statepath);old=json.loads(state_raw);s=copy.deepcopy(old);pending=s['pending_submission'];jid='3042627'
 ref={'path':'configs/experiments/formal_main_v2_cuda_continuous_3039258_v1.json','sha256':'5f86034d43017d3f89b0d3a73cd90dd8bd22b0b8a54461d0b0a51e5f8df6220e'}
 check('known pending exact identity',pending['kind']=='cuda_continuous_admission_pending' and pending['known_job_id']==jid and pending['status']=='submitted_identifier_observed' and pending['retry_permitted'] is False and pending['authorization']==ref and pending['request_token']=='cti-cuda-continuous-v1:'+ref['sha256'] and pending['pair_key']=='libero_object_k256_seed23')
 check('known job not already registered',not any(str(j['job_id'])==jid for j in s['registered_jobs']) and not (R/f'results/formal_main_v2/submissions/{jid}.json').exists())
 auth,e=g.validate_authorization(R,ref);audit=R/pending['audit_relative'];ack=json.loads(read(audit/'sbatch_result.json'));pre=json.loads(read(audit/'preflight.json'));failure_raw=read(audit/'failed_transaction.json');failure=json.loads(failure_raw)
 check('ACK and original exact submitted argv',ack['returncode']==0 and ack['stdout']==jid+'\n' and ack['stderr']=='' and ack['actual_sbatch_argv']==pending['actual_sbatch_argv']==pre['actual_sbatch_argv'])
 invraw=read(R/pending['invocation']);praw=read(P/pending['invocation']);inv=json.loads(invraw)
 check('original raw invocation R/P/preflight',invraw==praw and hashlib.sha256(invraw).hexdigest()==pending['invocation_sha256']==pre['invocation_sha256']=='69af3f5116e56c1ca89e8993f2f7e7685105c91c4d9ce2f35613972e5de9f47e' and inv==pre['invocation'])
 plan=dict(invocation=inv,invocation_relative=pending['invocation'],wrapper=str(P/'scripts/server/formal_asset_main.slurm'))
 args,reconstructed,invsha,token=g.sbatch_argv(plan,ref)
 check('exact original command and byte reconstruction',args==pending['actual_sbatch_argv'] and reconstructed==invraw and invsha==pending['invocation_sha256'] and token==pending['request_token'])
 gate=g.Gateway(R,c,d,None,None,None,auth,ref,e);job=gate.job(jid,plan,invsha,args,token);jobs=s['registered_jobs']+[job]
 scheduler=c.Slurm(runner=runner,timeout=45);obs=scheduler.observe(jobs);out['observation']=obs
 out['accounting_coverage']={'registered_plus_known':len(jobs),'observed':len(obs['rows']),'missing':sorted(set(j['job_id'] for j in jobs)-set(obs['rows'])),'extra':sorted(set(obs['rows'])-set(j['job_id'] for j in jobs))}
 cor=d.corroborate_new_job(scheduler,job,obs);cap=d.reconcile_submission(c,jobs,obs,job,token,auth['controller_job_id'],cor)
 owner=g.controller_owner(R,s,obs,auth)
 check('same actual owner and held lease',owner==pre['controller_owner'])
 row=obs['rows'][jid];ctl=s['autonomous_training_v1']
 check('current running/pending one GPU and full reserved capacity',row['status'] in ('RUNNING','PENDING') and row['gpus']==1 and len(cap['occupied'])+ctl.get('reserved_GPU_slots',0)<=8)
 check('retained pair block',pending['pair_key'] in ctl['blocked_pairs'])
 history=[j for j in s['registered_jobs'] if j['job_id'] in ('3028460','3039258')]
 check('failed84 and recovered6512 preserved',len(history)==2 and {j['job_id']:(j['status'],j['elapsed_seconds']) for j in history}=={'3028460':('FAILED',84),'3039258':('COMPLETED',6512)})
 job.update(status=row['status'],elapsed_seconds=row['elapsed_seconds'],exit_code=row['exit_code'],node=row['node'],reconciled_after_submission_accounting_failure=True)
 s['registered_jobs'].append(job);s['pending_submission']=None
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 tracking=s['formal_main_progress']['parallel_execution']['pair_tracking'];check('pair tracking exists',pending['pair_key'] in tracking)
 prior_tracking=copy.deepcopy(tracking)
 tracking[pending['pair_key']].update(active_job_id=jid,segment_target=5000,continuous_admission=ref)
 s['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied'])
 check('all existing rows and entire controller unchanged',s['registered_jobs'][:-1]==old['registered_jobs'] and s['autonomous_training_v1']==old['autonomous_training_v1'])
 expected=copy.deepcopy(old);expected['registered_jobs']=old['registered_jobs']+[job];expected['pending_submission']=None;expected['current_round_cost']=copy.deepcopy(s['current_round_cost'])
 expected['formal_main_progress']['parallel_execution']['pair_tracking'][pending['pair_key']].update(active_job_id=jid,segment_target=5000,continuous_admission=ref)
 expected['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied'])
 check('exact allowed in-memory state delta only',s==expected)
 e.unchanged()
 for rel,sha in e.hashes.items():evidence[rel]=sha
 for rel,sha in pins.items():check('source unchanged '+rel,hashlib.sha256((R/rel).read_bytes()).hexdigest()==sha)
 out.update(status='passed_readonly_and_exact_in_memory_projection',pending=pending,new_job=job,capacity=cap,controller_owner=owner,scontrol_corroboration=cor,old_registered_count=len(old['registered_jobs']),new_registered_count=len(s['registered_jobs']),original_pair_GPU_seconds=6596,all_formal_GPU_seconds=seconds,blocked_unchanged=True,reservations_unchanged=True,reserved_slots=ctl.get('reserved_GPU_slots',0),state_snapshot_sha256=hashlib.sha256(state_raw).hexdigest(),state_current_sha256=hashlib.sha256(statepath.read_bytes()).hexdigest(),actual_main_executed=False,original_failed_transaction=failure,original_post_submit_missing_ID='not recorded; cause unknown',allowed_top_level_deltas=['registered_jobs append exact existing job','pending_submission exact known cleared','current_round_cost same observation totals','formal_main_progress only this pair active_job_id/segment_target/continuous_admission and active GPU count'])
except BaseException as exc:
 out.update(status='failed_independent_check',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
out['read_evidence_sha256']=dict(sorted(evidence.items()))
dest=D/'readonly_and_projection.json';raw=(json.dumps(out,sort_keys=True,indent=2)+'\n').encode()
with dest.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
print(json.dumps({'status':out['status'],'checks':len(checks),'job':out.get('new_job',{}).get('job_id'),'row':out.get('observation',{}).get('rows',{}).get('3042627'),'capacity':out.get('capacity'),'coverage':out.get('accounting_coverage'),'receipt':str(dest),'sha256':hashlib.sha256(raw).hexdigest(),'error':out.get('error'),'query_count':len(traces)}))
if out['status'].startswith('failed'):sys.exit(1)

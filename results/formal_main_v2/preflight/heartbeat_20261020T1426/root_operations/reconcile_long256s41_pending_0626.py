from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,sys,copy,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1426'
AR={'path':'results/formal_main_v2/execution/long_remaining16_action_v1_1827/k256_seed41/submission_authorization.json','sha256':'9b5f2280f9e1f3b5c78aeb98292fa23c788f73a1de5f8dfe3077ed5b664367d2'}
AD='results/formal_main_v2/downstream_gateway/'+AR['sha256']
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel,pin=None):
 p=R/rel
 if pin:assert h(p)==pin
 return json.loads(p.read_bytes())
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
g=load('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','long0626s23pendinggw')
c=load(g.CONTROLLER,g.CONTROLLER_SHA,'long0626s23pendingctl')
auth,e,plan,science,prepared=g.validate_authorization(R,AR)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/g.STATE;before=h(sp);s=rd(g.STATE);old=copy.deepcopy(s);pending=s['pending_submission'];ctl=s['autonomous_training_v1']
 assert pending['known_job_id']=='3047152' and pending['status']=='submitted_identifier_observed' and pending['automatic_retry'] is False
 assert pending['authorization']==AR and pending['audit_relative']==AD and pending['request_token']=='cti-downstream-gateway-v1:'+AR['sha256']
 assert pending['stage_key']=='libero_10_development_460db0e9701de590' and pending['requested_gpus']==1 and pending['version']==g.VERSION
 pre=rd(AD+'/preflight.json','b06b69c7414269dae2f6440593b984289401bb1efbbefa271ad92cc9691989fb')
 ack=rd(AD+'/sbatch_result.json','e170f6e12796720cf59d1371ea8281f4c3c6bc60606f54906cbab0931c9ca55f')
 fail=rd(AD+'/failed_transaction.json','abaebb84ce5daa3b7905d644f6ede0ddcd25a97296844df7edc0cfe608cd748e')
 assert fail['error']=='post-submit accounting incomplete' and fail['status']=='stopped_requires_root_reconciliation_no_retry'
 assert ack['returncode']==0 and ack['stdout']=='3047152\n' and ack['stderr']=='' and ack['actual_sbatch_argv']==pending['actual_sbatch_argv']==pre['actual_sbatch_argv']
 assert pre['authorization']==AR and pre['plan']==auth['plan'] and pre['prepared_invocation']==auth['prepared_invocation']
 assert [j['job_id'] for j in pre['registered_jobs']]==[j['job_id'] for j in s['registered_jobs']]
 variable={'status','elapsed_seconds','exit_code','node','allocation'}
 for a,b in zip(pre['registered_jobs'],s['registered_jobs']):assert {k:v for k,v in a.items() if k not in variable}=={k:v for k,v in b.items() if k not in variable}
 invrel=pending['invocation'];assert invrel==pre['invocation_relative']==plan['invocation_relative']
 raw=(R/invrel).read_bytes();assert raw==(P/invrel).read_bytes()==(R/auth['prepared_invocation']['path']).read_bytes()
 assert json.loads(raw)==prepared and prepared['method_ids']==['A256_seed41','B256_seed41'] and prepared['stage']=='development' and prepared['suite']=='libero_10' and prepared['resume'] is False and prepared['prior_job_ids']==[]
 assert h(R/invrel)==pending['invocation_sha256']==pre['invocation_sha256']==auth['prepared_invocation']['sha256']=='2551eb5fb98e4e060316ff4c2bdfe4065f31431f3f6800edad23276c9a5ef80b'
 assert pending['plan_sha256']==prepared['plan_sha256']==plan['plan_sha256']=='45e3bd1278bbb4c57b761eec8c235958b6079f20df21ba6cbad5b969949438a7'
 bundle=dict(plan=plan,invocation=prepared,invocation_bytes=raw);token=pending['request_token'];argv=g.submission_argv(bundle,token)
 assert argv==pending['actual_sbatch_argv']
 assert ctl['reserved_GPU_slots']==1 and ctl['reservation_root_record']==auth['root_reservation'] and ctl['root_submission_hold'] is None
 assert AR['sha256'] not in ctl.get('downstream_reservations_consumed',{})
 assert not any(str(j['job_id'])=='3047152' or j.get('stage_key')==pending['stage_key'] for j in s['registered_jobs'])
 assert not (R/'results/formal_main_v2/submissions/3047152.json').exists() and not (R/AD/'committed.json').exists()
 owner=rd('results/formal_main_v2/autonomous_training/run_v1/owner.json')
 assert owner['owner_id']==ctl['owner_id']=='6b3beba5cdeb41df9d749b0b2054d485' and str(owner['coordinator_job_id'])==ctl['controller_job_id']==auth['controller_job_id']=='3034538'
 with Path(owner['lock']).open('rb') as f:
  held=False
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
  except BlockingIOError:held=True
 assert held
 gw=g.Gateway(R,c,None,None,None,auth,AR,e);job=gw._job('3047152',bundle,token,argv)
 jobs=s['registered_jobs']+[job];scheduler=c.Slurm(timeout=45);snapshot=scheduler.observe(jobs)
 corroboration=g.corroborate_new_job(scheduler,job,snapshot)
 caps=g.reconcile_submission(c,jobs,snapshot,job,token,auth['controller_job_id'],corroboration)
 detail_argv=['scontrol','show','job','-o','3047152'];detail=scheduler.run(detail_argv)
 assert detail.returncode==0 and not detail.stderr.strip()
 assert len(caps['occupied'])<=8 and '3047152' in caps['occupied'] and snapshot['rows']['3047152']['status'] in ['RUNNING','PENDING','CONFIGURING']
 assert snapshot['rows']['3034538']['status']=='RUNNING' and snapshot['rows']['3034538']['gpus']==0
 for field,value in [('JobId','3047152'),('JobName','cti-formal-downstream'),('JobState',snapshot['rows']['3047152']['status']),('WorkDir',str(P)),('Comment',token),('Requeue','0'),('Restarts','0'),('ExcNodeList','gpu4020'),('TimeLimit','04:00:00'),('StdOut',str(P/'results/slurm/cti-formal-downstream_3047152.out')),('StdErr',str(P/'results/slurm/cti-formal-downstream_3047152.err'))]:assert field+'='+value in detail.stdout.split(),field
 inventory=rd(g.INVENTORY,g.INVENTORY_SHA);assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():assert h(R/rel)==h(g.S/rel)==pin
 e.unchanged();assert h(sp)==before
 s['registered_jobs'].append(job);s['pending_submission']=None
 ctl['reserved_GPU_slots']=0;ctl.setdefault('downstream_reservations_consumed',{})[AR['sha256']]=dict(job_id='3047152',reservation=auth['root_reservation'],request_token=token)
 s['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']=len(caps['occupied'])
 seconds=sum(snapshot['rows'][str(j['job_id'])]['elapsed_seconds']*snapshot['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')==g.ROUND)
 s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')==g.ROUND for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 expected=copy.deepcopy(old);expected['registered_jobs'].append(job);expected['pending_submission']=None;expected['current_round_cost']=copy.deepcopy(s['current_round_cost'])
 expected['autonomous_training_v1']['reserved_GPU_slots']=0;expected['autonomous_training_v1'].setdefault('downstream_reservations_consumed',{})[AR['sha256']]=copy.deepcopy(ctl['downstream_reservations_consumed'][AR['sha256']])
 expected['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']=len(caps['occupied'])
 assert s==expected
 receipt=dict(schema=g.ROUND,status='exact_original_ACK_job_reconciled',utc=datetime.now(timezone.utc).isoformat(),pending_before=pending,state_before_sha256=before,job=job,scheduler=snapshot,scontrol_corroboration=corroboration,actual_scontrol_detail=dict(argv=detail_argv,returncode=detail.returncode,stdout=detail.stdout,stderr=detail.stderr),capacity=caps,controller_owner=owner,lifecycle_lease_held=True,original_preflight=ref(AD+'/preflight.json'),original_ACK=ref(AD+'/sbatch_result.json'),original_failure=ref(AD+'/failed_transaction.json'),all173_R_and_S_match=True,new_submissions=0,automatic_retry=False,exact_reservation_consumed=auth['root_reservation'],unrelated_controller_fields_unchanged=True,final_release_authorized=False)
 g.record(R/B/'Long3047152_pending_reconciliation.json',receipt)
 g.record(R/AD/'submitted_job_observation.json',dict(job_id='3047152',request_token=token,observation=snapshot,scontrol_corroboration=corroboration,capacity=caps,root_pending_reconciliation=ref(B+'/Long3047152_pending_reconciliation.json')))
 g.record(R/'results/formal_main_v2/submissions/3047152.json',job)
 c.atomic_json(sp,s,before)
 g.record(R/AD/'committed.json',dict(schema=g.ROUND,kind='formal_downstream_server_committed',status='submitted_once_reconciled_after_accounting_delay',job=job,state_sha256=h(sp),request_token=token,reservation_consumed=True,automatic_retry=False,root_reconciliation=ref(B+'/Long3047152_pending_reconciliation.json')))
 print(json.dumps(dict(status='registered_original_job_no_resubmission',job_id='3047152',active_GPU_jobs=len(caps['occupied']),pending=None,GPU_hours=seconds/3600,receipt=ref(B+'/Long3047152_pending_reconciliation.json'))))

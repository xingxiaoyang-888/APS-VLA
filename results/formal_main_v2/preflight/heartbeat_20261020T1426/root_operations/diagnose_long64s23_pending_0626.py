from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,sys,copy,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1426'
AR={'path':'results/formal_main_v2/execution/long_remaining16_action_v1_1827/k64_seed23/submission_authorization.json','sha256':'775b318f5534c67f41c828aed5592d3bc1c0403e4989cdcfc95aaa7d3b207573'}
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
 assert pending['known_job_id']=='3047163' and pending['status']=='submitted_identifier_observed' and pending['automatic_retry'] is False
 assert pending['authorization']==AR and pending['audit_relative']==AD and pending['request_token']=='cti-downstream-gateway-v1:'+AR['sha256']
 assert pending['stage_key']=='libero_10_development_2eea5a76505a0f3c' and pending['requested_gpus']==1 and pending['version']==g.VERSION
 pre=rd(AD+'/preflight.json','3f00fa6d69fbb69a6e79e331dd855c9b3d81f4b82a41273754343cb201a83571')
 ack=rd(AD+'/sbatch_result.json','9a9f99e3935351bfaefe90a8cd9fec25784caa84cfa052da642e1c3a7ff043e3')
 fail=rd(AD+'/failed_transaction.json','d5556ed05a26eede778884e50b549bb08b584ce39169c3c8b8b052ed44a81dee')
 assert fail['error']=='registered Slurm name differs' and fail['status']=='stopped_requires_root_reconciliation_no_retry'
 assert ack['returncode']==0 and ack['stdout']=='3047163\n' and ack['stderr']=='' and ack['actual_sbatch_argv']==pending['actual_sbatch_argv']==pre['actual_sbatch_argv']
 assert pre['authorization']==AR and pre['plan']==auth['plan'] and pre['prepared_invocation']==auth['prepared_invocation']
 assert [j['job_id'] for j in pre['registered_jobs']]==[j['job_id'] for j in s['registered_jobs']]
 variable={'status','elapsed_seconds','exit_code','node','allocation'}
 for a,b in zip(pre['registered_jobs'],s['registered_jobs']):assert {k:v for k,v in a.items() if k not in variable}=={k:v for k,v in b.items() if k not in variable}
 invrel=pending['invocation'];assert invrel==pre['invocation_relative']==plan['invocation_relative']
 raw=(R/invrel).read_bytes();assert raw==(P/invrel).read_bytes()==(R/auth['prepared_invocation']['path']).read_bytes()
 assert json.loads(raw)==prepared and prepared['method_ids']==['A64_seed23','B64_seed23'] and prepared['stage']=='development' and prepared['suite']=='libero_10' and prepared['resume'] is False and prepared['prior_job_ids']==[]
 assert h(R/invrel)==pending['invocation_sha256']==pre['invocation_sha256']==auth['prepared_invocation']['sha256']=='657469914d10e9462ec3cbc789167eea2ac5434582456a9a24ffe2364d40ca5d'
 assert pending['plan_sha256']==prepared['plan_sha256']==plan['plan_sha256']=='84737cbbe8b9006dab432aeca7c590390ef057796b6cd490b791c265f9f469a9'
 bundle=dict(plan=plan,invocation=prepared,invocation_bytes=raw);token=pending['request_token'];argv=g.submission_argv(bundle,token)
 assert argv==pending['actual_sbatch_argv']
 assert ctl['reserved_GPU_slots']==1 and ctl['reservation_root_record']==auth['root_reservation'] and ctl['root_submission_hold'] is None
 assert AR['sha256'] not in ctl.get('downstream_reservations_consumed',{})
 assert not any(str(j['job_id'])=='3047163' or j.get('stage_key')==pending['stage_key'] for j in s['registered_jobs'])
 assert not (R/'results/formal_main_v2/submissions/3047163.json').exists() and not (R/AD/'committed.json').exists()
 owner=rd('results/formal_main_v2/autonomous_training/run_v1/owner.json')
 assert owner['owner_id']==ctl['owner_id']=='6b3beba5cdeb41df9d749b0b2054d485' and str(owner['coordinator_job_id'])==ctl['controller_job_id']==auth['controller_job_id']=='3034538'
 with Path(owner['lock']).open('rb') as f:
  held=False
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
  except BlockingIOError:held=True
 assert held
 gw=g.Gateway(R,c,None,None,None,auth,AR,e);job=gw._job('3047163',bundle,token,argv)
 jobs=s['registered_jobs']+[job];scheduler=c.Slurm(timeout=45);snapshot=scheduler.observe(jobs)
 detail=scheduler.run(['scontrol','show','job','-o','3047163'])
 mismatches=[{'job_id':str(j['job_id']),'registered':j.get('name'),'observed':snapshot['rows'].get(str(j['job_id']),{}).get('scheduler_name')} for j in jobs if j.get('name') and snapshot['rows'].get(str(j['job_id']),{}).get('scheduler_name')!=j['name']]
 g.record(R/B/'Long3047163_pending_diagnostic.json',dict(schema=g.ROUND,kind='read_only_pending_name_diagnostic',original_failure=ref(AD+'/failed_transaction.json'),original_ACK=ref(AD+'/sbatch_result.json'),observation=snapshot,name_mismatches=mismatches,scontrol=dict(returncode=detail.returncode,stdout=detail.stdout,stderr=detail.stderr),state_sha256=before,state_unchanged=h(sp)==before,new_submissions=0))
 assert h(sp)==before
 print(json.dumps(dict(name_mismatches=mismatches,new_job=snapshot['rows'].get('3047163'),scontrol_returncode=detail.returncode,receipt=ref(B+'/Long3047163_pending_diagnostic.json'))),flush=True)

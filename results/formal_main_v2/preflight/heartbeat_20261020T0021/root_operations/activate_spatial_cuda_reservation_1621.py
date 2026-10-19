from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,fcntl,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0021'
AUTH={'path':'configs/experiments/formal_main_v2_cuda_single_recovery_3028522_v1.json','sha256':'7411a2e5e0d7e2123eea8bfea4c2bbaccb037d54b09697180340a597e3cfb18a'}
IND={'path':'.local/spatial_cuda_reservation_audit_1621/independent_review.json','sha256':'332843905be34cfe246436fc1948d4a4497f18304f4d9bb2919993b565b6a236'}
def h(p):
 z=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):z.update(b)
 return z.hexdigest()
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return dict(path=rel,sha256=h(p))
g=load('.local/cuda_recovery_autonomous_1940/gateway.py','c97b66100a0a21a722b17e32129b7a220fac7b2b2cb8b9cc9678b88f605476c3','root1621_cuda_gateway')
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','root1621_slot_controller')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=json.loads(sp.read_text());old=copy.deepcopy(s);ctl=s['autonomous_training_v1']
 auth,e=g.validate_authorization(R,AUTH)
 assert h(R/IND['path'])==IND['sha256'];ind=json.loads((R/IND['path']).read_text())
 assert ind['kind']=='spatial_cuda_reservation_independent_review' and ind['status']=='PASS_reservation_preparation_only' and ind['review_role']=='independent'
 assert ind['authorization']==AUTH and ind['root_reservation']==auth['root_reservation'] and ind['completed_by_arm']=={'A':1000,'B':1000} and ind['next_sample_cursor']=={'A':8000,'B':8000}
 for rel,pin in ind['files'].items():assert h(R/rel)==pin,rel
 for x in ind['resume_checks']:
  p=Path(x['path']);assert p.is_file() and not p.is_symlink() and p.stat().st_size==x['bytes'] and h(p)==x['sha256']
 assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 assert AUTH['sha256'] not in ctl.get('cuda_recovery_reservations_consumed',{})
 assert not (R/'results/formal_main_v2/startup_recoveries/3028522'/AUTH['sha256']).exists()
 own=[j for j in s['registered_jobs'] if j.get('stage_key')=='libero_spatial_train_k64_seed23']
 assert [j['job_id'] for j in own]==['3024716','3025205','3028522'] and own[-1]['status']=='FAILED' and own[-1]['elapsed_seconds']==73
 assert ctl['blocked_pairs']['libero_spatial_k64_seed23']['failed_job_ids']==['3028522']
 owner=json.loads((R/'results/formal_main_v2/autonomous_training/run_v1/owner.json').read_text());assert owner['owner_id']==ctl['owner_id'] and str(owner['coordinator_job_id'])==ctl['controller_job_id']=='3034538'
 lease=Path(owner['lock']);assert lease==R/'results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock' and not lease.is_symlink()
 with lease.open('rb') as f:
  held=False
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
  except BlockingIOError:held=True
 assert held
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['unknown'] and not cap['findings'] and len(cap['occupied'])<=8 and 'libero_spatial_k64_seed23' not in cap['active_pairs']
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 assert obs['rows']['3028522']['status']=='FAILED' and obs['rows']['3028522']['elapsed_seconds']==73
 e.unchanged();now=datetime.now(timezone.utc).isoformat()
 observation=save(B+'/reservation_activation_scheduler.json',dict(schema='formal_main_v2',utc=now,observation=obs,capacity=cap,owner=owner,lease_held=True))
 record=save(B+'/Spatial64_seed23_reservation_activation.json',dict(schema='formal_main_v2',kind='root_existing_single_recovery_reservation_activation',status='activated_for_next_free_GPU_slot_only',utc=now,authorization=AUTH,reservation=auth['root_reservation'],independent_review=IND,source_gateway_SHA=g.GATEWAY_SHA if hasattr(g,'GATEWAY_SHA') else h(R/'.local/cuda_recovery_autonomous_1940/gateway.py'),fresh_observation=observation,actual_GPU_occupied=len(cap['occupied']),failed_job_id='3028522',completed_by_arm={'A':1000,'B':1000},next_sample_cursor={'A':8000,'B':8000},target=1500,total_schedule=5000,resume_bytes_rehashed=True,GPU_tensor_restore_verified=False,no_new_invocation_or_GPU_submission=True,no_healthy_job_cancelled=True,failed_and_blocked_history_preserved=True,final_release=False,Spatial_development_3042529_authorization_remains_consumed=True,priority_reason='The unchanged training recovery is already independently admitted; new development startup continuation is not yet submission-ready. Both remain exceptional root-only work.',next_action='At a later real free slot, root executes original exact gateway full preflight then a single submit; never infer capacity or ignore pending.'))
 ctl['reserved_GPU_slots']=1;ctl['reservation_root_record']=auth['root_reservation']
 assert {k:v for k,v in ctl.items() if k not in ('reserved_GPU_slots','reservation_root_record')}=={k:v for k,v in old['autonomous_training_v1'].items() if k not in ('reserved_GPU_slots','reservation_root_record')}
 s['formal_main_progress']['latest_cuda_reservation_activation']=record
 c.atomic_json(sp,s,before)
 save(B+'/reservation_state_CAS.json',dict(state_before=before,state_after=h(sp),activation=record,registered_jobs_unchanged=s['registered_jobs']==old['registered_jobs'],pending_unchanged=s['pending_submission']==old['pending_submission'],normal_controller_sources_unchanged=True))
 print(json.dumps(dict(record=record,active_GPU=len(cap['occupied']),reserved_slots=1,new_GPU_submissions=0,root_complete=s['formal_main_progress']['root_and_independent_completed_arms'])))

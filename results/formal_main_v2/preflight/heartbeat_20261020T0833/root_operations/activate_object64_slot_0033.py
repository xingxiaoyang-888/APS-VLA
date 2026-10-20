from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,sys,json,copy,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B=R/'results/formal_main_v2/preflight/heartbeat_20261020T0833'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mod(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','reserve0033ctl')
g=mod('.local/cuda_recovery_autonomous_1940/gateway.py','c97b66100a0a21a722b17e32129b7a220fac7b2b2cb8b9cc9678b88f605476c3','reserve0033gateway')
ref={'path':'configs/experiments/formal_main_v2_cuda_single_recovery_3028468_v1.json','sha256':'0f8c1eab2e196c544bbf1302d440085abf052bc0bbc32a6dc3d9377bcdb0aec0'}
auth,e=g.validate_authorization(R,ref)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=c.read_json(sp);old=copy.deepcopy(s);ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 assert ref['sha256'] not in ctl.get('cuda_recovery_reservations_consumed',{})
 owner=c.read_json(R/'results/formal_main_v2/autonomous_training/run_v1/owner.json')
 assert owner['owner_id']==ctl['owner_id'] and str(owner['coordinator_job_id'])==ctl['controller_job_id']=='3034538'
 with Path(owner['lock']).open('rb') as stream:
  held=False
  try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(stream,fcntl.LOCK_UN)
  except BlockingIOError:held=True
 assert held
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['unknown'] and not cap['findings'] and len(cap['occupied'])<8
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 pair=[j for j in s['registered_jobs'] if j.get('suite')=='libero_object' and j.get('visual_tokens')==64 and j.get('training_seed')==23 and j.get('mode')=='train']
 assert [str(j['job_id']) for j in pair]==['3028468'] and obs['rows']['3028468']['status']=='FAILED' and obs['rows']['3028468']['elapsed_seconds']==69
 assert not (R/'results/formal_main_v2/startup_recoveries/3028468'/ref['sha256']).exists()
 e.unchanged()
 ctl['reserved_GPU_slots']=1;ctl['reservation_root_record']=auth['root_reservation']
 c.atomic_json(sp,s,before)
 receipt=dict(schema='formal_main_v2',status='existing_single_original_target_reservation_activated',utc=datetime.now(timezone.utc).isoformat(),authorization=ref,root_reservation=auth['root_reservation'],failed_job_id='3028468',retained_failed_GPU_seconds=69,original_target=500,continuous5000_admission=False,state_before_sha256=before,state_after_sha256=h(sp),previous_reservation_record=old['autonomous_training_v1'].get('reservation_root_record'),capacity_before=cap,scheduler=obs,controller_owner=owner,lifecycle_lease_held=True,new_GPU_submissions=[],normal_jobs_not_cancelled=True,reason='Use genuine spare capacity for already reviewed Object original-target recovery while precise Spatial historical-operation-doc binding is separately reviewed.')
 p=B/'Object64_original_target_reservation_activation.json'
 with p.open('x') as stream:json.dump(receipt,stream,sort_keys=True,indent=2);stream.write('\n')
 print(json.dumps(dict(status=receipt['status'],occupied=len(cap['occupied']),reserved=1,receipt=p.relative_to(R).as_posix(),sha256=h(p))))

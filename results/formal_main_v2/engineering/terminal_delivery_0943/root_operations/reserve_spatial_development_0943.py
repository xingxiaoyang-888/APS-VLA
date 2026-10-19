from pathlib import Path
from datetime import datetime,timezone
import json,sys,importlib.util,fcntl,copy,subprocess,hashlib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261019T1743'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(rel,v):
 p=R/rel;raw=(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n').encode()
 with p.open('xb') as f:f.write(raw)
 return dict(path=rel,sha256=h(p))
gp=R/'scripts/ops/formal_action_deployment_v1/gateway.py';assert h(gp)=='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a'
sp=importlib.util.spec_from_file_location('root_spatial_reservation_gateway',gp);g=importlib.util.module_from_spec(sp);sys.modules[sp.name]=g;sp.loader.exec_module(g)
ar=dict(path='results/formal_main_v2/execution/action_spatial_resume_0943/submission_authorization.json',sha256='55f6c06a83847f8f60850309cdade6991cc70ba3e83451f086632c3d76504cd6')
a,e,plan,scientific,prepared=g.validate_authorization(R,ar)
c=g.load(R/g.CONTROLLER,g.CONTROLLER_SHA,'root_spatial_reservation_controller')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 old=c.file_sha(R/g.STATE);s=c.read_json(R/g.STATE);baseline=copy.deepcopy(s);ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl.get('root_submission_hold') is None
 assert ctl['controller_job_id']==a['controller_job_id']=='3034538' and ctl['activation_sha256']==g.ACTIVATION['sha256']
 owner=c.read_json(R/'results/formal_main_v2/autonomous_training/run_v1/owner.json')
 assert owner['owner_id']==ctl['owner_id'] and str(owner['coordinator_job_id'])=='3034538'
 lease=Path(owner['lock']);assert lease==R/'results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock' and lease.is_file() and not lease.is_symlink()
 with lease.open('rb') as f:
  held=False
  try:
   fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
  except BlockingIOError:held=True
  assert held,'controller lifecycle lease not held'
 snap=c.Slurm(timeout=45).observe(s['registered_jobs']);caps=c.capacity(s['registered_jobs'],snap,'3034538')
 assert not caps['unknown'] and not caps['findings'] and len(caps['occupied'])<=8
 assert snap['rows']['3034538']['status']=='RUNNING' and snap['rows']['3034538']['gpus']==0
 for j in s['registered_jobs']:g.check_observed_identity(j,snap['rows'][str(j['job_id'])],snap['queue'].get(str(j['job_id'])),c.TERMINAL)
 overlap=[j for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2' and j.get('suite')=='libero_spatial' and j.get('mode')=='development']
 assert len(overlap)==1 and str(overlap[0]['job_id'])=='3022743' and snap['rows']['3022743']['status']=='COMPLETED'
 assert not (R/plan['invocation_relative']).exists() and not (g.P/plan['invocation_relative']).exists()
 ctl['reserved_GPU_slots']=1;ctl['reservation_root_record']=a['root_reservation']
 ctlcheck=copy.deepcopy(ctl);oldctl=copy.deepcopy(baseline['autonomous_training_v1'])
 for x in ['reserved_GPU_slots','reservation_root_record']:ctlcheck.pop(x,None);oldctl.pop(x,None)
 assert ctlcheck==oldctl
 gpu_seconds=sum(snap['rows'][str(j['job_id'])]['gpus']*snap['rows'][str(j['job_id'])]['elapsed_seconds'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 receipt=save(B+'/spatial_slot_reservation_activation.json',dict(schema='formal_main_v2',kind='root_specific_downstream_reservation_activation',status='reserved_next_available_slot_no_healthy_job_cancelled',
  utc=datetime.now(timezone.utc).isoformat(),authorization=ar,reservation=a['root_reservation'],previous_reservation=baseline['autonomous_training_v1'].get('reservation_root_record'),
  state_before_sha256=old,controller_owner=owner,controller_lease_held=True,capacity=caps,observation=snap,
  allocated_GPU_seconds_snapshot=gpu_seconds,allocated_GPU_hours_snapshot=gpu_seconds/3600,registered_jobs=len(s['registered_jobs']),submitted=False))
 c.atomic_json(R/g.STATE,s,old)
 print(json.dumps(dict(reservation_activation=receipt,occupied=len(caps['occupied']),GPU_hours=gpu_seconds/3600,state_after_sha256=c.file_sha(R/g.STATE))),flush=True)
argv=[sys.executable,'-B',str(gp),'--authorization',ar['path'],'--authorization-sha256',ar['sha256'],'--gateway-sha256',h(gp)]
out=subprocess.run(argv,cwd=R,capture_output=True,text=True,timeout=180)
for name,data in [('spatial_check_only.stdout.txt',out.stdout),('spatial_check_only.stderr.txt',out.stderr)]:
 with (R/B/name).open('x') as f:f.write(data)
blocked=out.returncode!=0 and 'eight GPU slots occupied' in out.stderr
result=save(B+'/spatial_actual_check_only.json',dict(argv=argv,returncode=out.returncode,status='blocked_all_eight_slots_occupied' if blocked else ('passed_check_only_not_submitted' if out.returncode==0 else 'unexpected_failure_preserved_requires_review'),
 stdout=dict(path=B+'/spatial_check_only.stdout.txt',sha256=h(R/B/'spatial_check_only.stdout.txt')),stderr=dict(path=B+'/spatial_check_only.stderr.txt',sha256=h(R/B/'spatial_check_only.stderr.txt')),submitted=False))
print(json.dumps(dict(actual_check_only=result,status='capacity_full' if blocked else out.returncode)))
assert blocked or out.returncode==0

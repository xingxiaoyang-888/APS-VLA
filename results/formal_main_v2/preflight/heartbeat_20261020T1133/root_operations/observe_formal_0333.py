from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B=R/'results/formal_main_v2/preflight/heartbeat_20261020T1133'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('root_0333_controller',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state_path=R/'results/experiment_supervisor/state.json';before=h(state_path);s=c.read_json(state_path);ctl=s['autonomous_training_v1']
 owner=c.read_json(R/'results/formal_main_v2/autonomous_training/run_v1/owner.json')
 assert owner['owner_id']==ctl['owner_id'] and str(owner['coordinator_job_id'])==ctl['controller_job_id']=='3034538'
 lease=Path(owner['lock']);assert lease==R/'results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock' and lease.is_file() and not lease.is_symlink()
 with lease.open('rb') as f:
  held=False
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
  except BlockingIOError:held=True
 assert held
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['unknown'] and not cap['findings'] and len(cap['occupied'])<=8
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 pairs=s['formal_main_progress']['completed_training_pairs'];reviewed=[]
 for key,v in pairs.items():
  if v.get('root_review') and v.get('independent_review'):
   for role in ['root_review','independent_review']:assert h(R/v[role])==v[role+'_sha256']
   reviewed.append(key)
  elif v.get('terminal_root_and_independent_review'):
   x=v['terminal_root_and_independent_review'];assert x['completed_by_arm']=={'A':5000,'B':5000}
   for role in ['root_review','independent_review']:assert h(R/x[role]['path'])==x[role]['sha256']
   reviewed.append(key)
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 active=[dict(job_id=j['job_id'],suite=j.get('suite'),budget=j.get('visual_tokens'),seed=j.get('training_seed'),mode=j.get('mode'),**{k:obs['rows'][str(j['job_id'])][k] for k in ['status','elapsed_seconds','node']}) for j in s['registered_jobs'] if str(j['job_id']) in cap['occupied']]
 result=dict(schema='formal_main_v2',utc=datetime.now(timezone.utc).isoformat(),state_sha256=before,controller_owner=owner,lifecycle_lease_held=True,controller_last_tick=ctl.get('last_tick_utc'),
  pending=s['pending_submission'],capacity=cap,active_jobs=active,reserved_GPU_slots=ctl['reserved_GPU_slots'],reservation_root_record=ctl.get('reservation_root_record'),
  machine_and_prior_complete=2*len(pairs),root_independent_complete=2*len(reviewed),root_independent_pair_keys=reviewed,
  root_independent_updates=s['formal_main_progress']['root_and_independent_reviewed_arm_updates'],allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,
  blocked_pairs=ctl['blocked_pairs'],observation=obs,root_state_unchanged=True)
 assert h(state_path)==before
 B.mkdir(parents=True,exist_ok=True)
 out=B/'initial_observation.json'
 with out.open('x') as f:json.dump(result,f,sort_keys=True);f.write('\n')
 print(json.dumps(dict(receipt=out.relative_to(R).as_posix(),sha256=h(out),root_complete=result['root_independent_complete'],machine_complete=result['machine_and_prior_complete'],
  GPU_hours=result['allocated_GPU_hours'],occupied=len(cap['occupied']),reservation=ctl['reserved_GPU_slots'],active=active)))

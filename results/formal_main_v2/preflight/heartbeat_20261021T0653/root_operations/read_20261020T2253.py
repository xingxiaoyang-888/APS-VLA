from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,sys,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261021T0653'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','read2253c')
g=load('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','read2253g')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);state=json.loads(sp.read_bytes());assert before=='63c74e7e591283409a792a7597fdb9bf99d1936ff1311e123bd687a83237a51f'
 obs=c.Slurm(timeout=60).observe(state['registered_jobs']);cap=c.capacity(state['registered_jobs'],obs,'3034538')
 for j in state['registered_jobs']:g.check_observed_identity(j,obs['rows'][str(j['job_id'])],obs['queue'].get(str(j['job_id'])),c.TERMINAL)
 formal=[j for j in state['registered_jobs'] if j.get('experiment')=='formal_main_v2'];assert len(formal)==len({str(j['job_id']) for j in formal})
 secs=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in formal)
 with (R/'results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock').open('rb') as q:fcntl.flock(q,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(q,fcntl.LOCK_UN)
 out=dict(utc=datetime.now(timezone.utc).isoformat(),state_sha256=before,observation=obs,capacity=cap,formal_allocations=len(formal),allocated_GPU_seconds=secs,allocated_GPU_hours=secs/3600,controller_lease_released=True,pending=state['pending_submission'],Goal_job=next(j for j in formal if str(j['job_id'])=='3054127'))
 d=R/B;d.mkdir(parents=True,exist_ok=True);f=d/'live_observation.json';f.open('x').write(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n');assert h(sp)==before
 print(json.dumps({k:out[k] for k in ['utc','formal_allocations','allocated_GPU_seconds','allocated_GPU_hours','controller_lease_released','pending']}))
 print(json.dumps({'capacity':cap,'Goal_job':out['Goal_job'],'Goal_sacct':obs['rows']['3054127'],'controller':obs['rows']['3034538'],'observation_sha256':h(f)},ensure_ascii=False))
root=P/'results/formal_main_v2/engineering/goal_paired_input_gate_20261020T2156/attempt01';assert root.resolve()==root and not root.is_symlink()
rows=[]
if root.exists():
 for p in sorted(root.iterdir()):
  if p.is_file():
   row=dict(name=p.name,bytes=p.stat().st_size,sha256=h(p));rows.append(row)
   if p.suffix=='.json' and p.stat().st_size<100000:print(json.dumps({'artifact':row,'content':json.loads(p.read_bytes())},ensure_ascii=False))
  elif p.is_dir():rows.append(dict(directory=p.name,count=sum(1 for x in p.iterdir() if x.is_file())))
print(json.dumps({'artifact_root':str(root),'root_entries':rows},ensure_ascii=False))

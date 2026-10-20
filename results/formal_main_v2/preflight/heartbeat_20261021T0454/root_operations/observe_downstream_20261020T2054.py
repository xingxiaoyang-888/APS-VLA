from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,os,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261021T0454'
BUNDLE='3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mod(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
assert os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R) and os.environ.get('CTI_SERVER_CONTROL_MANIFEST_SHA256')==BUNDLE
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','obs2054ctl')
g=mod('scripts/ops/formal_action_deployment_posttraining_k64s23_v1/gateway.py','873d0145f8d3ed51e916f39e1e36cb0251d10777a6f98429621f526d37a2c7bb','obs2054gw')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 p=R/'results/experiment_supervisor/state.json';raw=p.read_bytes();s=json.loads(raw);ctl=s['autonomous_training_v1'];f=s['formal_main_progress'];jobs=s['registered_jobs']
 assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 assert f['root_and_independent_completed_arms']==72 and f['root_and_independent_reviewed_arm_updates']==360000
 assert f['completed_final_trials']==0 and f['test_opened'] is False and f['global_release_created'] is False
 snap=c.Slurm().observe(jobs);capacity=c.capacity(jobs,snap,ctl['controller_job_id'])
 assert not capacity['unknown'] and not capacity['findings'] and len(capacity['occupied'])<=8
 for j in jobs:g.check_observed_identity(j,snap['rows'][j['job_id']],snap['queue'].get(j['job_id']),c.TERMINAL)
 assert snap['rows']['3034538']['status']=='COMPLETED' and snap['rows']['3034538']['exit_code']=='0:0'
 cost=sum(snap['rows'][j['job_id']]['elapsed_seconds']*snap['rows'][j['job_id']]['gpus'] for j in jobs if j.get('experiment')=='formal_main_v2')
 record={'schema':'formal_main_v2','kind':'root_registered_downstream_observation','utc':datetime.now(timezone.utc).isoformat(),'state_sha256':hashlib.sha256(raw).hexdigest(),'observation':snap,'capacity':capacity,'formal_GPU_seconds':cost,'formal_GPU_hours':cost/3600,'training_complete_arms':72,'final_release':False,'state_unchanged':True,'pending_submission':None}
 out=R/B/'initial_observation.json';out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('x') as f:json.dump(record,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
 assert p.read_bytes()==raw
 print(json.dumps({'receipt':{'path':str(out.relative_to(R)),'sha256':h(out)},'active':capacity['occupied'],'GPU_hours':cost/3600,'target_statuses':{j:snap['rows'][j]['status'] for j in ['3053875','3053894']}}))

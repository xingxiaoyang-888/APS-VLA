from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,os,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261021T1134'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
assert os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R)
g=load('scripts/ops/formal_object_single_error_gateway_v1/gateway.py','8471bba1419a9e0ca31f84e7e55ff232cd6fb0fcb4bcb89320140ea76292d727','obs0334g')
out=g.observe_only()
assert out['state_sha256']=='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa'
s=json.loads((R/'results/experiment_supervisor/state.json').read_bytes());rows=out['projection']['observation']['rows']
assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0 and s['autonomous_training_v1']['root_submission_hold'] is None
assert rows['3034538']['status']=='COMPLETED' and rows['3034538']['exit_code']=='0:0'
jobs=[j for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2'];assert len(jobs)==len({j['job_id'] for j in jobs})==273
cost=sum(rows[j['job_id']]['elapsed_seconds']*rows[j['job_id']]['gpus'] for j in jobs)
out.update(formal_GPU_seconds=cost,formal_GPU_hours=cost/3600,formal_unique_allocations=len(jobs),root_utc=datetime.now(timezone.utc).isoformat(),scientific_acceptance_inferred=False)
p=R/B/'initial_observation.json';p.parent.mkdir(parents=True,exist_ok=True)
with p.open('x') as f:json.dump(out,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
print(json.dumps({'receipt':str(p.relative_to(R)),'sha256':h(p),'state_unchanged':h(R/'results/experiment_supervisor/state.json')==out['state_sha256'],'cost_GPU_seconds':cost,'target_statuses':{j:rows[j] for j in ['3054409','3054717']},'derived':out['projection']['derived'],'lease':out['projection']['lease']}))

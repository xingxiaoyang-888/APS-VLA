from pathlib import Path
from datetime import datetime,timezone
import hashlib,sys,importlib.util,json,copy,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1426'
D='results/formal_main_v2/execution/long_remaining16_action_v1_1827/k256_seed41'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mod(rel,pin,name):
 p=R/rel;assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def read(rel):return json.loads((R/rel).read_text())
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','reserve0626ctl')
g=mod('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','reserve0626gw')
ar=dict(path=D+'/submission_authorization.json',sha256='9b5f2280f9e1f3b5c78aeb98292fa23c788f73a1de5f8dfe3077ed5b664367d2')
a,e,plan,science,prepared=g.validate_authorization(R,ar)
accept='results/formal_main_v2/preflight/heartbeat_20261020T0227/Long_development_runtime_root_acceptance.json'
assert h(R/accept)=='c8d3ea33012b23a810bda6cf1b9f9aded2a7cc9632ecaf2bc7df28226ddf02fc'
ready=read(a['runtime_readiness']['path'])
for role in ['root_review','independent_review']:
 gate=read(ready[role]['path'])
 assert h(R/ready[role]['path'])==ready[role]['sha256']
 assert gate['effective_plan']==a['plan'] and gate['scientific_plan']==a['scientific_plan']
 assert gate['plan_sha256']==plan['plan_sha256']
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read('results/experiment_supervisor/state.json');old=copy.deepcopy(s);ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 consumed=ctl['downstream_reservations_consumed']['e436e498db113a851dfdab2e9a23ef3313d599d02278705261926413ddebe909']
 assert consumed['request_token']=='cti-downstream-gateway-v1:e436e498db113a851dfdab2e9a23ef3313d599d02278705261926413ddebe909'
 previous_job_id=consumed['job_id']
 assert ctl['reservation_root_record']==consumed['reservation']
 owner=read('results/formal_main_v2/autonomous_training/run_v1/owner.json')
 assert owner['owner_id']==ctl['owner_id'] and str(owner['coordinator_job_id'])==ctl['controller_job_id']=='3034538'
 with Path(owner['lock']).open('rb') as f:
  held=False
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
  except BlockingIOError:held=True
 assert held
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['unknown'] and not cap['findings'] and len(cap['occupied'])<8
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 j=next(j for j in s['registered_jobs'] if j['job_id']==previous_job_id)
 prior_observed=obs['rows'][previous_job_id]
 assert prior_observed['status'] in ['RUNNING','PENDING','CONFIGURING','COMPLETED'] and prior_observed['gpus']==1
 if prior_observed['status']=='COMPLETED':assert prior_observed['exit_code']=='0:0'
 g.check_observed_identity(j,prior_observed,obs['queue'].get(previous_job_id),c.TERMINAL)
 bundle=g.FrozenPlan(R,a,e,plan,science,prepared).prepare(s)
 assert not (R/plan['invocation_relative']).exists() and not (P/plan['invocation_relative']).exists()
 assert not (P/plan['output_relative']).exists()
 assert not any(j.get('stage_key')==plan['invocation']['stage_key'] for j in s['registered_jobs'])
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 out=B+'/Long256seed41_reservation_activation.json'
 proof=dict(schema='formal_main_v2',kind='root_activate_existing_exact_Long_development_reservation',utc=datetime.now(timezone.utc).isoformat(),status='activated_for_next_actual_free_slot_not_submitted',authorization=ar,reservation=a['root_reservation'],prior_exact_downstream_reservation_consumed=consumed,prior_root_acceptance=ref(accept),full_original_scientific_plan_rebuilt=True,explicit_nested_review_plan_bindings_verified=True,controller_owner=owner,lifecycle_lease_held=True,scheduler=obs,capacity=cap,allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,pending=None,new_GPU_submissions=[],planned_trials=200,new_trials=0,final_release=False,state_before_sha256=before)
 with (R/out).open('x') as f:json.dump(proof,f,sort_keys=True,indent=2);f.write('\n')
 ctl['reserved_GPU_slots']=1;ctl['reservation_root_record']=a['root_reservation']
 ctl.setdefault('root_reservation_activation_history',[]).append(ref(out))
 assert s['registered_jobs']==old['registered_jobs'] and ctl['blocked_pairs']==old['autonomous_training_v1']['blocked_pairs'] and s['current_round_cost']==old['current_round_cost']
 c.atomic_json(sp,s,before)
 print(json.dumps(dict(status=proof['status'],receipt=ref(out),occupied=len(cap['occupied']),GPU_hours=seconds/3600,next='Long256seed41_development200',new_GPU_submissions=[])))

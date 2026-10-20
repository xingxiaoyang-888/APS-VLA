from pathlib import Path
from datetime import datetime,timezone
import hashlib,sys,importlib.util,json,copy,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T2117'
AUTHORIZATION={"path":"results/formal_main_v2/execution/nonLong_action_v1_1317/libero_goal_k128_seed41/submission_authorization.json","sha256":"7b8b860d709366770fb8f7f91015f49c06a66cdb03582a6f71bd1735e20f02f9"}
ROOT_ACCEPTANCE={"path":"results/formal_main_v2/execution/nonLong_action_v1_1317/libero_goal_k128_seed41/root_pre_execution_check.json","sha256":"a7a1591af3252eedc412f16ed0aa282a89ffb4258f9c79db0f10e50bd725006e"}
POST_READINESS_INDEPENDENT={"path":"results/formal_main_v2/engineering/supervision_delivery_1317/nonLong_plan_independent/post_readiness/post_readiness_independent_review.json","sha256":"738f91a8c772825794e8ff52a5086875aa69ba1edb1e51f02e40f31dda4b95f9"}
BATCH='libero_goal_k128_seed41'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel):return json.loads((R/rel).read_bytes())
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def check(rr):assert h(R/rr['path'])==rr['sha256'];return read(rr['path'])
def mod(rel,pin,name):
 p=R/rel;assert h(p)==pin
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','nonlongres1317ctl')
g=mod('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','nonlongres1317gw')
a,e,plan,science,prepared=g.validate_authorization(R,AUTHORIZATION)
accepted=check(ROOT_ACCEPTANCE);post=check(POST_READINESS_INDEPENDENT)
assert accepted['status']=='passed_actual_unchanged_P_wrapper_verify_and_NativeIO' and accepted['authorization']==AUTHORIZATION and accepted['full_P_wrapper_verify']
assert any(x['authorization']==AUTHORIZATION and x['root_pre_execution']==ROOT_ACCEPTANCE for x in post['plans'])
assert post['status']=='passed' and post['actual_full_P_wrapper_verifications']==4 and not post['actual_GPU_runtime_chain_verified']
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/g.STATE;before=h(sp);s=read(g.STATE);old=copy.deepcopy(s);ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
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
 for jid in cap['occupied']:
  job=next(j for j in s['registered_jobs'] if str(j['job_id'])==str(jid))
  g.check_observed_identity(job,obs['rows'][str(jid)],obs['queue'].get(str(jid)),c.TERMINAL)
 bundle=g.FrozenPlan(R,a,e,plan,science,prepared).prepare(s)
 assert not (R/plan['invocation_relative']).exists() and not (P/plan['invocation_relative']).exists() and not (P/plan['output_relative']).exists()
 assert not any(j.get('stage_key')==plan['invocation']['stage_key'] for j in s['registered_jobs'])
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 out=B+'/'+BATCH+'_reservation_activation.json'
 proof=dict(schema='formal_main_v2',kind='root_activate_exact_nonLong_development_reservation',utc=datetime.now(timezone.utc).isoformat(),status='activated_for_next_actual_free_slot_not_submitted',authorization=AUTHORIZATION,reservation=a['root_reservation'],root_acceptance=ROOT_ACCEPTANCE,post_readiness_independent=POST_READINESS_INDEPENDENT,full_original_scientific_plan_rebuilt=True,controller_owner=owner,lifecycle_lease_held=True,scheduler=obs,capacity=cap,allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,pending=None,new_GPU_submissions=[],planned_trials=accepted['method_ids'].__len__()*100,new_trials=0,final_release=False,state_before_sha256=before,previous_reservation_record_preserved=ctl['reservation_root_record'])
 with (R/out).open('x') as f:json.dump(proof,f,sort_keys=True,indent=2);f.write('\n')
 with (R/B/'root_operations'/('reserve_'+BATCH+'_1317.py')).open('xb') as f:f.write(Path(__file__).read_bytes())
 ctl['reserved_GPU_slots']=1;ctl['reservation_root_record']=a['root_reservation'];ctl.setdefault('root_reservation_activation_history',[]).append(ref(out))
 assert s['registered_jobs']==old['registered_jobs'] and ctl['blocked_pairs']==old['autonomous_training_v1']['blocked_pairs'] and s['current_round_cost']==old['current_round_cost']
 c.atomic_json(sp,s,before)
 print(json.dumps(dict(status=proof['status'],receipt=ref(out),occupied=len(cap['occupied']),GPU_hours=seconds/3600,batch=BATCH,new_GPU_submissions=[])))

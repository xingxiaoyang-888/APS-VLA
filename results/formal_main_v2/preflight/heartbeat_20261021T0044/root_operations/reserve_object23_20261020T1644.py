from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,sys,importlib.util,json,copy,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261021T0044';D='results/formal_main_v2/execution/object256seed23_source_control_v1_20261020T1644'
AUTH={'path':D+'/submission_authorization.json','sha256':'e6a6a2165c46187e42338764f16417d90e8d42dd1892d8d06f61bce6d32c5047'}
ROOT={'path':D+'/root_pre_execution_check.json','sha256':'4dff5677a601cb71f4d41a1c5f64008d54d466e5853987b95625d5960b326523'}
READY={'path':B+'/Object_runtime_readiness_root.json','sha256':'4a9ae0aa406884ba7ee3d2f29799ff26186b19e42c4b1359de498df3cb400233'}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(n):return json.loads((R/n).read_bytes())
def ref(n):return dict(path=n,sha256=h(R/n))
def check(x):assert h(R/x['path'])==x['sha256'];return read(x['path'])
def mod(n,pin,label):
 p=R/n;assert h(p)==pin;sp=importlib.util.spec_from_file_location(label,p);m=importlib.util.module_from_spec(sp);sys.modules[label]=m;sp.loader.exec_module(m);return m
def save(n,x):
 p=R/n;assert p.is_relative_to(R) and not any(z.is_symlink() for z in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,sort_keys=True,indent=2,allow_nan=False);f.write(chr(10))
ap=argparse.ArgumentParser();ap.add_argument('--post-review',required=True);ap.add_argument('--post-review-sha256',required=True);args=ap.parse_args();postref={'path':args.post_review,'sha256':args.post_review_sha256}
ctrl=mod('scripts/ops/formal_object256s23_source_bridge_v1/control.py','09ae3486565e17bd2c41b09adbfaa7a6d99f38754d3e77071f77851c9ac54f6f','ObjectReserve1644control');g=ctrl.gateway_module();c=g.load(R/g.CONTROLLER,g.CONTROLLER_SHA,'ObjectReserve1644controller')
a,e,plan,science,prepared=g.validate_authorization(R,AUTH);accepted=check(ROOT);check(READY);post=check(postref)
assert accepted['status']=='passed_actual_unchanged_P_wrapper_verify_and_NativeIO' and accepted['authorization']==AUTH and accepted['full_P_wrapper_verify']
assert post['status']=='passed' and post['authorization']==AUTH and post['root_pre_execution']==ROOT and post['root_readiness_receipt']==READY and post['actual_full_P_wrapper_verifications']==1 and post['actual_GPU_runtime_chain_verified'] is False and post['selected_checkpoint_bytes_verified'] is True and post['explicit_source_control']==ctrl.descriptor()
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/g.STATE;before=h(sp);s=read(g.STATE);old=copy.deepcopy(s);ctl=s['autonomous_training_v1'];assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 assert s['formal_main_progress']['root_and_independent_completed_arms']==68 and s['formal_main_progress']['completed_final_trials']==0 and not s['formal_main_progress']['global_release_created']
 owner=read('results/formal_main_v2/autonomous_training/run_v1/owner.json');assert owner['owner_id']==ctl['owner_id'] and str(owner['coordinator_job_id'])==ctl['controller_job_id']=='3034538'
 with Path(owner['lock']).open('rb') as f:
  held=False
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
  except BlockingIOError:held=True
 assert held
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538');assert not cap['unknown'] and not cap['findings'] and len(cap['occupied'])<8
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 for jid in cap['occupied']:
  job=next(j for j in s['registered_jobs'] if str(j['job_id'])==str(jid));g.check_observed_identity(job,obs['rows'][str(jid)],obs['queue'].get(str(jid)),c.TERMINAL)
 bundle=g.FrozenPlan(R,a,e,plan,science,prepared).prepare(s)
 assert not (R/plan['invocation_relative']).exists() and not (P/plan['invocation_relative']).exists() and not (P/plan['output_relative']).exists()
 assert not any(j.get('stage_key')==plan['invocation']['stage_key'] for j in s['registered_jobs'])
 e.unchanged();check(postref);assert h(sp)==before
 outpost=D+'/post_readiness_independent_review.json';pp=R/outpost
 if pp.exists():assert h(pp)==postref['sha256']
 else:
  with pp.open('xb') as f:f.write((R/postref['path']).read_bytes())
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 out=B+'/Object256s23_reservation_activation.json'
 proof=dict(schema='formal_main_v2',kind='root_activate_exact_Object256s23_development_reservation',utc=datetime.now(timezone.utc).isoformat(),status='activated_for_next_actual_free_slot_not_submitted',authorization=AUTH,reservation=a['root_reservation'],root_acceptance=ROOT,post_readiness_independent=ref(outpost),explicit_source_control=ctrl.descriptor(),full_original_scientific_plan_rebuilt=True,controller_owner=owner,lifecycle_lease_held=True,scheduler=obs,capacity=cap,allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,pending=None,new_GPU_submissions=[],planned_trials=200,unique_development_initial_states=100,new_trials=0,final_release=False,state_before_sha256=before,previous_reservation_record_preserved=ctl['reservation_root_record'])
 save(out,proof);ctl['reserved_GPU_slots']=1;ctl['reservation_root_record']=a['root_reservation'];ctl.setdefault('root_reservation_activation_history',[]).append(ref(out))
 assert s['registered_jobs']==old['registered_jobs'] and ctl['blocked_pairs']==old['autonomous_training_v1']['blocked_pairs'] and s['current_round_cost']==old['current_round_cost']
 c.atomic_json(sp,s,before);print(json.dumps(dict(status=proof['status'],receipt=ref(out),occupied=len(cap['occupied']),GPU_hours=seconds/3600,new_GPU_submissions=[])),flush=True)

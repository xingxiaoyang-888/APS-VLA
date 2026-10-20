from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,copy,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0653';X='results/formal_main_v2/execution/spatial588_pre_dispatch_v1';AUTH='d0143bc88b855ad9f4d6b6008e8373272d55c953d36bba88fbd8840a1090f7d5'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_bytes())
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':h(p)}
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(d,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin;spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
ap=argparse.ArgumentParser();ap.add_argument('--post-review',required=True);ap.add_argument('--sha256',required=True);a=ap.parse_args();assert a.post_review.startswith('.local/spatial_gateway_independent_20261020T2253/') and h(R/a.post_review)==a.sha256
post=rd(R/a.post_review);ar={'path':X+'/submission_authorization_v2.json','sha256':AUTH};assert post['status']=='passed' and post['authorization']==ar and post['actual_P_outer_verified'] is True and post['new_GPU_submissions']==0 and post['final_release'] is False
assert h(R/B/'Spatial_submission_readiness.json')=='781295f45ece3572a2966748e44cf7c286c1868cade244cb35c09834f68c2b9c'
g=load('scripts/ops/formal_action_deployment_posttraining_spatial588_v1/gateway.py','aba5868a8dc4e480262177785b2e62123d014046624f37924248721a9575c99c','sp588dispatchg');c=load(g.CONTROLLER,g.CONTROLLER_SHA,'sp588dispatchc')
auth,e,plan,science,prepared=g.validate_authorization(R,ar)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);assert before=='a05ea99476dc64d87977dbf72c0cd870dee12dd273fbf9dd1eaf4ff01312e8c0';s=rd(sp);old=copy.deepcopy(s);ctl=s['autonomous_training_v1'];assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 assert not (R/'results/formal_main_v2/downstream_gateway'/AUTH).exists() and not (R/plan['invocation_relative']).exists() and not (g.P/plan['invocation_relative']).exists()
 assert s['formal_main_progress']['root_and_independent_completed_arms']==72 and not s['formal_main_progress']['global_release_created']
 ctl['reserved_GPU_slots']=1;ctl['reservation_root_record']=auth['root_reservation']
 save(R/B/'Spatial_reservation.json',{'schema':'formal_main_v2','status':'single_exact_root_reservation','authorization':ar,'post_review':ref(R/a.post_review),'readiness':ref(R/B/'Spatial_submission_readiness.json'),'state_before':before,'reservation':auth['root_reservation'],'no_training_restart':True,'final_release':False})
 c.atomic_json(sp,s,before);reserved=h(sp)
assert h(R/'results/experiment_supervisor/state.json')==reserved
engine=g.Gateway(R,c,c.Slurm(),g.FrozenPlan(R,auth,e,plan,science,prepared),g.NativeIO(R),auth,ar,e)
try:result=engine.run(submit=True)
except BaseException as ex:
 with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
  s=rd(R/'results/experiment_supervisor/state.json');save(R/B/'Spatial_dispatch_stopped.json',{'status':'stopped_preserve_pending_no_resubmit','error_type':type(ex).__name__,'error':str(ex),'state_sha256':h(R/'results/experiment_supervisor/state.json'),'pending_submission':s.get('pending_submission'),'authorization':ar,'new_submit_calls_maximum':1,'retry_authorized':False})
 raise
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 s=rd(R/'results/experiment_supervisor/state.json');assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0
 jid=result['job']['job_id'];assert len([j for j in s['registered_jobs'] if str(j['job_id'])==jid])==1
 D=R/'results/formal_main_v2/downstream_gateway'/AUTH;obs=rd(D/'submitted_job_observation.json');assert obs['job_id']==jid
 out={'schema':'formal_main_v2','status':'submitted_once','job_id':jid,'authorization':ar,'post_readiness_review':ref(R/a.post_review),'root_readiness':ref(R/B/'Spatial_submission_readiness.json'),'invocation':plan['invocation_relative'],'state_sha256':h(R/'results/experiment_supervisor/state.json'),'committed':ref(D/'committed.json'),'scheduler_observation':ref(D/'submitted_job_observation.json'),'scheduler_status_at_dispatch':obs['observation']['rows'][jid]['status'],'remaining_new_trials':588,'retained_compatible_legacy_trials':12,'legacy_GPU_seconds':395,'automatic_retry':False,'new_scientific_results':0,'final_release':False}
 save(R/B/'Spatial_dispatch.json',out);print(json.dumps({k:out[k] for k in ['status','job_id','scheduler_status_at_dispatch','remaining_new_trials','final_release']}))

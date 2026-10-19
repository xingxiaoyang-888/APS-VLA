from pathlib import Path
import hashlib,importlib.util,json,sys
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D='results/formal_main_v2/execution/action_spatial_resume_0943'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert sha(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def put(rel,b):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
 return {'path':rel,'sha256':sha(p)}
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','transition_controller')
contract=load('scripts/ops/formal_action_deployment_v1/contract.py','efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19','transition_contract')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';state_before=sha(statepath);state=json.loads(statepath.read_text())
 assert state.get('pending_submission') is None and state['autonomous_training_v1'].get('pending_submission') is None
 request=R/'.local/action_actual_plan_0943/transition_root_request.json';assert sha(request)=='80565bc2294c81957f7b71ecad14029cf17927119847f556b6058f2e6fc1786e'
 req=json.loads(request.read_text());v=req['draft_payload']
 planpath=R/'.local/action_actual_plan_0943/scientific_plan.json';assert sha(planpath)=='43a521e2b1c5b7f8ceff442ce655dde5cae73dfde0f9f7598f65fa57446b4a94'
 plan=json.loads(planpath.read_text());inv=contract.validate_inner(plan)
 assert inv['suite']=='libero_spatial' and inv['stage']=='development' and inv['resume'] is True
 assert inv['prior_job_ids']==['3022743'] and inv['stop_after'] is None
 prior=json.loads((R/inv['prior_review']).read_text())
 assert sha(R/inv['prior_review'])=='9e14b86a1e556c53ef1cbd8c7bdc1733c3d5eb744f62ffee8df9395645816650'
 history=[j for j in state['registered_jobs'] if j.get('stage_key')==inv['stage_key']]
 assert [str(j['job_id']) for j in history]==['3022743']
 assert all(j['status']=='COMPLETED' and j['exit_code']=='0:0' for j in history)
 assert v['allowed_stages']==['development'] and not v['old_new_outcome_equivalence_established']
 assert v['files']=={k:prior['files'][k] for k in v['files']} and len(v['files'])==4
 for rel,pin in v['files'].items():assert sha(R/rel)==pin and sha(P/rel)==pin,rel
 raw=R/req['independent_raw']['path'];assert sha(raw)==req['independent_raw']['sha256']=='476fda4dd3cbd25fd7b095dabd0fe4d8820d34985c0b3f74508127b493a3e066'
 ind=json.loads(raw.read_text());assert ind['original_terminal_trials']==12 and ind['remaining_trial_ids']==588 and ind['files']==v['files'] and not ind['terminal_trials_repeated']
 records=[]
 for origin,target,pin in [
  (req['independent_raw']['path'],D+'/prefix_independent.json',req['independent_raw']['sha256']),
  ('.local/action_actual_plan_independent_0943/existing_development_readonly_review.json',D+'/existing_development_readonly_review.json','8afbc3f597e5cfd8347af877a66681ea6305a55888b31b175774f358c36726f0'),
  ('.local/action_actual_plan_independent_0943/actual_original_plan_reconstruction.json',D+'/actual_original_plan_independent.json','2a29cb6c7954c341c6d76a823d4a9cd4add06b07c3bdf22d1bc5a5482ac871b9')]:
  assert sha(R/origin)==pin
  q=put(target,(R/origin).read_bytes());records.append({'origin':origin,'published':q})
 v.update(status='root_reviewed',root_reviewed_utc=datetime.now(timezone.utc).isoformat(),original_terminal_trials_preserved=12,remaining_trial_ids=588,production_readiness_issued=False,submission_authorized_by_this_transition=False)
 assert contract.validate_transition(v,plan,root=R)
 tr=put(D+'/transition.json',(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
 put(D+'/root_transition_review.json',(json.dumps({'transition':tr,'independent_archives':records,'scientific_plan':{'path':str(planpath.relative_to(R)),'sha256':sha(planpath)},'only_development_prefix_preservation':True,'state_unchanged':sha(statepath)==state_before,'new_GPU_jobs':0,'no_O2A_or_final_permission':True},ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
 assert sha(statepath)==state_before
 print(json.dumps({'transition':tr,'allowed_stage':'development','preserved':12,'remaining':588,'readiness_issued':False,'new_GPU_jobs':0}),flush=True)

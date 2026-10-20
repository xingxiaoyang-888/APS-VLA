from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,copy,fcntl,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261021T0653';X='results/formal_main_v2/execution/spatial588_pre_dispatch_v1'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_bytes())
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':h(p)}
def put(p,b):
 assert p.resolve()==p and not any(t.is_symlink() for t in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,str(p)
 else:p.open('xb').write(b)
def save(p,d):put(p,(json.dumps(d,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode());return ref(p)
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
ap=argparse.ArgumentParser();ap.add_argument('--independent-review',required=True);ap.add_argument('--sha256',required=True);a=ap.parse_args()
assert a.independent_review.startswith('.local/spatial_gateway_independent_20261020T2253/') and h(R/a.independent_review)==a.sha256
ind=rd(R/a.independent_review);assert ind['kind']=='formal_downstream_server_gateway_independent_CPU_review' and ind['status']=='passed_CPU_review' and not ind['blockers'] and ind['files']['scripts/ops/formal_action_deployment_v1/gateway.py']=='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a'
g=load('scripts/ops/formal_action_deployment_posttraining_spatial588_v1/gateway.py','aba5868a8dc4e480262177785b2e62123d014046624f37924248721a9575c99c','sp588auth2gateway')
with (R/'results/experiment_supervisor/.writer.lock').open('a+b') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=rd(sp);assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0
 oldref=ref(R/X/'submission_authorization.json');assert oldref['sha256']=='5f9f641ab807850b173f51c6ef43d9622654d40a149bb223bf52895d6a25e1f7'
 old=rd(R/X/'submission_authorization.json');auth=copy.deepcopy(old);ready=rd(R/X/'runtime_readiness.json');prepared=rd(R/X/'prepared_invocation.json');plan=rd(R/X/'effective_plan.json');science=rd(R/X/'scientific_plan.json')
 assert ref(R/X/'runtime_readiness.json')['sha256']=='85e83ddee3954d3b6aca027ae08a44d1a231fa3c2f3fbf510dd50ab4a29f60df'
 assert not (R/plan['invocation_relative']).exists() and not (P/plan['invocation_relative']).exists()
 assert not (R/'results/formal_main_v2/downstream_gateway'/oldref['sha256']).exists()
 put(R/X/'gateway_independent_full_review_v2.json',(R/a.independent_review).read_bytes());auth['independent_review']=ref(R/X/'gateway_independent_full_review_v2.json');auth.pop('root_reservation')
 reserve=rd(R/X/'reservation_root_record.json');reserve.update(authorization_path=X+'/submission_authorization_v2.json',authorization_intent_sha256=g.intent_sha(auth));save(R/X/'reservation_root_record_v2.json',reserve);auth['root_reservation']=ref(R/X/'reservation_root_record_v2.json');save(R/X/'submission_authorization_v2.json',auth)
 assert {k:v for k,v in auth.items() if k not in ['independent_review','root_reservation']}=={k:v for k,v in old.items() if k not in ['independent_review','root_reservation']}
 checked,e,p,sc,pr=g.validate_authorization(R,ref(R/X/'submission_authorization_v2.json'));bundle=g.FrozenPlan(R,checked,e,p,sc,pr).prepare(s);bundle['readiness_files']={**ready['runtime_publication_files'],X+'/runtime_readiness.json':h(R/X/'runtime_readiness.json')};live=g.NativeIO(R).preflight(bundle)
 wp=P/'scripts/ops/formal_action_deployment_v1/wrapper.py';assert h(wp)=='d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33';spec=importlib.util.spec_from_file_location('actual_outer_spatial588_v2',wp);w=importlib.util.module_from_spec(spec);sys.modules[spec.name]=w;spec.loader.exec_module(w);ctx=w.verify(prepared,project=P);assert ctx['original_plan']==science and ctx['effective_plan']==plan
 import torch
 assert not torch.cuda.is_initialized() and h(sp)==before
 out={'schema':'formal_main_v2','status':'root_and_independent_metadata_ready_actual_P_outer_verified_not_submitted','authorization':ref(R/X/'submission_authorization_v2.json'),'readiness':ref(R/X/'runtime_readiness.json'),'prepared_invocation':ref(R/X/'prepared_invocation.json'),'independent_review':ref(R/X/'plan_independent_review.json'),'root_review':ref(R/X/'plan_root_review.json'),'gateway_independent_review':ref(R/X/'gateway_independent_full_review_v2.json'),'actual_P_outer_verified':True,'actual_new_invocation_published':False,'new_GPU_submissions':0,'legacy12_compatible_trials':12,'remaining_trials':588,'all_prior_GPU_seconds_retained':395,'state_sha256_unchanged':before,'runtime_preflight':live,'final_release':False,'profiling_authorized':False,'failed_authorization_preserved':oldref,'bounded_correction':'Only add independently verified original gateway8f247f source coverage to the authorization review; preserve full guard, old failed authorization and readiness/prepared/science bytes. No submission existed.'}
 o=save(R/B/'Spatial_submission_readiness.json',out);print(json.dumps({'receipt':o,'authorization':out['authorization'],'actual_P_outer_verified':True,'new_GPU_submissions':0}))

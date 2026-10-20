from pathlib import Path
from types import SimpleNamespace
import json,hashlib,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1832';T='results/formal_main_v2/execution/nonLong_action_v1_1032'
GROUPS=[('libero_spatial',23,'libero_spatial_k128_seed23_development.json',['A128_seed23','B128_seed23']),('libero_object',23,'libero_object_k128_seed23_development.json',['A128_seed23','B128_seed23']),('libero_goal',17,'libero_goal_k128_seed17_references_development.json',['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17'])]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(rel,pin,name):
 p=R/rel;assert h(p)==pin
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def put(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw
 else:
  with p.open('xb') as stream:stream.write(raw)
c=module('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','nonlongdepsctl')
g=module('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','nonlongdepsgw')
planner=module('scripts/ops/formal_downstream_supervisor.py','f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571','nonlongdepsplanner')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/g.STATE);s=json.loads((R/g.STATE).read_bytes());assert s['pending_submission'] is None
 plans=[];files={}
 for suite,seed,name,methods in GROUPS:
  args=dict(stage='development',source_inventory=g.INVENTORY,execution_manifest=T+'/'+name,output_relative=None,freeze_directory=None,profile_panel=None,prior_review=None,collection_review=None,repair_record=None,resume=False,stop_after=None)
  plan=planner.plan(SimpleNamespace(**args),copy.deepcopy(s),project=R)
  assert plan['invocation']['suite']==suite and plan['invocation']['method_ids']==methods and not plan['invocation']['resume'] and plan['invocation']['prior_job_ids']==[]
  for rel,pin in plan['publish_files'].items():
   g.relative(rel);source=g.no_links(R/rel);target=g.no_links(P/rel)
   assert source.is_file() and h(source)==pin and source.stat().st_size<100*(1<<20)
   assert source.suffix not in ['.pt','.pth','.safetensors','.bin','.ckpt','.npz','.npy','.pkl','.pickle','.h5','.hdf5']
   if target.exists():assert target.is_file() and h(target)==pin
   if rel in files:assert files[rel]['sha256']==pin
   else:files[rel]=dict(sha256=pin,bytes=source.stat().st_size,already_present=target.exists())
  plans.append(dict(suite=suite,methods=methods,plan_sha256=plan['plan_sha256'],publish_files=plan['publish_files']))
 for rel,row in files.items():put(P/rel,(R/rel).read_bytes());assert h(P/rel)==row['sha256']
 assert h(R/g.STATE)==before
 receipt=dict(status='original_pure_planner_static_dependencies_published_exactly',plans=plans,files=files,state_unchanged=True,GPU_submissions=[],new_trials=0,scientific_changes=False,final_release=False)
 rel=B+'/nonLong_existing_runtime_dependencies_publication.json';put(R/rel,(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
 put(R/B/'root_operations/publish_nonlong_existing_dependencies_1032.py',Path(__file__).read_bytes())
 print(json.dumps(dict(receipt=dict(path=rel,sha256=h(R/rel)),files=len(files),new_files=sum(not r['already_present'] for r in files.values()),new_jobs=0)))

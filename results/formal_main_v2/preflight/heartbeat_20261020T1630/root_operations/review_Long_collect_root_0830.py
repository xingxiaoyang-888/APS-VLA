from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,copy,os
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
B='results/formal_main_v2/preflight/heartbeat_20261020T1630';O='results/formal_main_v2/execution/long_collect_action_v1_0830'
sys.dont_write_bytecode=True;sys.path.insert(0,str(S/'src'))
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def checked(rel,pin):
 assert h(R/rel)==pin,rel
 return json.loads((R/rel).read_bytes())
def mod(p,pin,name):
 assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('root readiness is CPU only')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(path));p=p if p.is_absolute() else Path.cwd()/p
   if any('sealed' in x.lower() or x.lower() in ['weights','checkpoints'] for x in p.parts) or p.suffix.lower() in ['.pt','.pth','.safetensors','.pkl','.pickle','.ckpt','.bin','.pruned_init','.init']:raise RuntimeError('No payload read in root readiness')
   writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
   if writing and not p.is_relative_to(R/B) and p!=R/'results/experiment_supervisor/.writer.lock':raise RuntimeError('Root readiness writes only its proof')
sys.addaudithook(guard)
science=checked(O+'/scientific_plan.json','1c50e85dfea3042cb7cee74cf5482e2325e4036e0bc7a74187d0061983790ee0')
effective=checked(O+'/effective_plan.json','1ce34d9ecf18e36d2c0043e2fdfd42ca327344d286fb35704fdfe70e8b5ed8ac')
action=checked(O+'/execution_contract.json','06ca8c538a323e14ad8197a80e9cc5c39d303976adbd8959630e535b11b1acc0')
assert science['invocation']['stage']=='collect' and science['invocation']['method_ids']==['dense']
assert not science['invocation']['resume'] and science['invocation']['prior_job_ids']==[]
assert not any(n=='cti_vla' or n.startswith('cti_vla.') for n in sys.modules)
wrapper=mod(P/'scripts/server/run_formal_downstream.py','f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24','root_actual_science_wrapper')
args=wrapper.verify(science['invocation']);assert args.mode=='collect' and args.global_freeze is None and args.panel is None
args.prepare_only=True
pin='b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd'
adapter=mod(P/'scripts/ops/formal_evaluation_adapter.py',pin,'root_actual_science_adapter')
prep=adapter.run(args,mode='collect',source_root=S,source_inventory=P/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',adapter_sha256=pin,resume=False)
origins={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.items() if (n=='cti_vla' or n.startswith('cti_vla.')) and getattr(m,'__file__',None)}
assert origins and all((S/'src') in Path(p).parents for p in origins.values())
assert prep['status']=='prepared_only' and prep['gpu_calls']==0 and prep['observations']==30 and prep['test_opened'] is False and prep['weights_validated'] is False
selection=json.loads((R/'.local/long_collection_prepare_0830/collection_selection_registration.json').read_bytes())
assert prep['fixed_state_ids']==[x['trial_id'] for x in selection['selected_states']]
contract=mod(P/'scripts/ops/formal_action_deployment_v1/contract.py','efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19','root_collect_contract')
assert contract.validate_effective(science,effective,scientific_plan_ref=ref(O+'/scientific_plan.json'),execution_contract_ref=ref(O+'/execution_contract.json'),execution_contract=action)
runtime=mod(P/'scripts/ops/formal_action_deployment_v1/runtime_scope.py','6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53','root_collect_runtime')
runtime.validate_contract(action['runtime_contract'],project_root=P,source_root=S)
for name,pin in effective['publish_files'].items():assert h(R/name)==h(P/name)==pin,name
for name,pin in effective['invocation']['watched_files'].items():assert h(Path(name))==pin,name
for name,pin in effective['invocation']['root_evidence_sha256'].items():assert h(R/name)==pin,name
inventory=checked('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
assert len(inventory['files'])==173
for name,pin in inventory['files'].items():assert h(R/name)==h(S/name)==pin,name
draft=checked('.local/long_collection_prepare_0830/a2/runtime_readiness_draft.json','2f9d55368a95bbc3e742886f3c90bf55164caf18456ade70a8d65c00e518abae')
for role,q in draft['component_reviews'].items():
 x=checked(q['path'],q['sha256']);assert x['status']=='passed_CPU_review' and not x.get('blockers') and x['component']==role
c=mod(R/'scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','root_collect_ctrl')
planner=mod(R/'scripts/ops/formal_downstream_supervisor.py','f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571','root_collect_planner')
a=checked('.local/long_collection_prepare_0830/a2/plan_arguments.json','ae21751e8133945ccb57b26e8d2611e10ebfe5fd044a95eae0650a364ad98daa')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);state=json.loads(sp.read_bytes())
 assert state['pending_submission'] is None
 rebuilt=planner.plan(SimpleNamespace(**a),copy.deepcopy(state),project=R)
 assert rebuilt==science,'Original pure planner reconstruction differs'
 assert not (P/science['output_relative']).exists()
 assert not (R/science['invocation_relative']).exists() and not (P/science['invocation_relative']).exists()
 proof=dict(schema='formal_main_v2',kind='formal_action_runtime_plan_review',status='passed',review_role='root',reviewed_by='root',execution_version=contract.VERSION,runtime_sources=action['files'],production_chain_complete=True,meaning_of_production_chain_complete='Exact genuine inputs and unchanged accepted production CPU chain checked; no collection GPU completion is inferred.',CPU_only=True,actual_collect_GPU_completed=False,scientific_plan=ref(O+'/scientific_plan.json'),effective_plan=ref(O+'/effective_plan.json'),plan_sha256=effective['plan_sha256'],action_execution_contract=ref(O+'/execution_contract.json'),support_files=effective['invocation']['support_files'],component_reviews=draft['component_reviews'],source=ref('.local/review_Long_collect_root_0830.py'),original_planner_rebuilt_exactly=True,actual_P_original_wrapper_passed=True,actual_P_original_collector_prepare_only_passed=True,prepare_only=prep,frozen_import_origins=origins,protected_source_files=173,scope='collect10 fixed Dense trajectories for30 common development observations only',selected_state_indices=[0,4,7,3,6,2,3,6,8,2],failed_or_short_trajectory_replacement=False,final_values_read=False,full_components_authorized=False,final_release=False,old600_reuse_or_rerun_authorized=False,scientific_success_trials_added=0,new_GPU_calls=0,utc=datetime.now(timezone.utc).isoformat())
 assert h(sp)==before
 q=R/B/'Long_collect_root_runtime_review.json'
 with q.open('x') as f:json.dump(proof,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(dict(status='passed_CPU_root_readiness',root_review=ref(q.relative_to(R).as_posix()),observations=30,GPU_calls=0)))

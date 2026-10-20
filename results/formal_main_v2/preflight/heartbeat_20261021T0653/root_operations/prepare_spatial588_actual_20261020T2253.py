from pathlib import Path
import hashlib,json,fcntl,os,sys,importlib.util,copy
from types import SimpleNamespace
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';B='results/formal_main_v2/preflight/heartbeat_20261021T0653';X='results/formal_main_v2/execution/spatial588_pre_dispatch_v1'
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
c=load('scripts/ops/formal_spatial588_predispatch_v1/control.py','e2e7c3fe7f6dcf4f63b4550c3f5bc8ec50a05aaf462b38ed961ce356cc414683','spatial588plan_control')
ct=load('scripts/ops/formal_action_deployment_v1/contract.py','efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19','spatial588plan_contract');rt=load('scripts/ops/formal_action_deployment_v1/runtime_scope.py','6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53','spatial588plan_runtime')
with (R/'results/experiment_supervisor/.writer.lock').open('a+b') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=rd(sp);assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0
 science=rd(R/X/'scientific_plan.json');assert h(R/X/'scientific_plan.json')=='b9d7404387a6896c3d7bb9ae0c55d3e132f16d6036e3c49f34ce489522bd37c2';i=science['invocation'];c.scope_invocation(i)
 trsrc=R/'.local/spatial_gateway_independent_20261020T2253/runtime_transition_review.json';assert h(trsrc)=='a35e93c1b468e99d8f0861f3e17f53a5202488cfa1ce04f8bf66e9cbcc636888';tr=rd(trsrc);assert tr['status']=='passed' and tr['review_role']=='independent'
 put(R/X/'transition_independent_review.json',trsrc.read_bytes())
 trans={'schema':'formal_main_v2','kind':'formal_action_runtime_transition','status':'root_reviewed','from_version':'formal-downstream-root-v1','to_version':ct.VERSION,'stage_key':i['stage_key'],'run_root':i['run_root'],'execution_manifest_sha256':i['execution_manifest_sha256'],'prior_job_ids':i['prior_job_ids'],'prior_review':i['prior_review'],'terminal_trials_repeated':False,'prior_outcomes_replaced':False,'new_trial_ids_only':True,'files':tr['files'],'independent_review':ref(R/X/'transition_independent_review.json'),'legacy12_compatibility':c.compatibility_module().descriptor(),'new_trials_expected':588,'old_prefix_trials':12,'allocation_history':['3022743','3042529'],'actual_executed_prefix_history':['3022743'],'old_failure_invocation_fabricated':False}
 tref=save(R/X/'runtime_transition.json',trans)
 runtime=rt.make_contract(project_root=R,source_root=S,suite='libero_spatial',stage='development')
 files={p:h(R/p) for p in ct.EXPECTED_NEW_FILES};files[ct.ACTION_ADAPTER]=ct.ACTION_SHA
 action={'schema':ct.SCHEMA,'kind':'formal_action_execution_contract','version':ct.VERSION,'status':'candidate_pending_root_readiness','scientific_settings_changed':False,'final_evaluation_enabled':False,'files':files,'runtime_contract':runtime,'GPU_acceptance':ct.GPU_REFS,'source_inventory':{'path':ct.INVENTORY,'sha256':ct.INVENTORY_SHA},'transition':tref}
 aref=save(R/X/'execution_contract.json',action);ct.validate_transition(trans,science,root=R,execution_contract=action)
 plan=ct.effective_plan(science,scientific_plan_ref=ref(R/X/'scientific_plan.json'),execution_contract_ref=aref,execution_contract=action);pref=save(R/X/'effective_plan.json',plan)
 args={'stage':'development','source_inventory':ct.INVENTORY,'execution_manifest':c.policy()['manifest']['path'],'output_relative':None,'freeze_directory':None,'profile_panel':None,'prior_review':i['prior_review'],'collection_review':None,'repair_record':c.REPAIR,'resume':True,'stop_after':None};save(R/X/'plan_arguments.json',args)
 factory,planner=c.control_modules();rebuilt=planner.plan(SimpleNamespace(**args),s,project=R,helper=factory);assert rebuilt==science
 pubs={**plan['publish_files'],**c.closure(),X+'/transition_independent_review.json':h(R/X/'transition_independent_review.json'),X+'/effective_plan.json':pref['sha256']}
 for rel,pin in pubs.items():
  ct.relative(rel);assert h(R/rel)==pin;put(P/rel,(R/rel).read_bytes());assert h(P/rel)==pin
 oldpath=P/'scripts/server/run_formal_downstream.py';assert h(oldpath)=='f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24'
 spl=importlib.util.spec_from_file_location('spatial588actual_original_wrapper',oldpath);old=importlib.util.module_from_spec(spl);sys.modules[spl.name]=old;spl.loader.exec_module(old)
 original_args=old.verify(i);watched=rt.validate_contract(runtime,project_root=P,source_root=S)
 for n,pin in plan['invocation']['watched_files'].items():assert h(Path(n))==pin,n
 for n,pin in ct.resume_prefix_inputs(i).items():assert h(Path(n))==pin,n
 assert not (P/plan['invocation_relative']).exists() and not (R/plan['invocation_relative']).exists()
 import torch
 assert not torch.cuda.is_initialized();assert h(sp)==before
 proof={'schema':'formal_main_v2','kind':'formal_spatial588_actual_P_scientific_metadata_root_review','status':'passed_metadata_verification_pending_outer_readiness','reviewed_by':'root','execution_version':ct.VERSION,'effective_plan':pref,'scientific_plan':ref(R/X/'scientific_plan.json'),'action_execution_contract':aref,'runtime_sources':action['files'],'explicit_source_control':c.descriptor(),'legacy12_compatibility':c.compatibility_module().descriptor(),'actual_P_original_scientific_wrapper_verified':True,'actual_P_runtime_contract_verified':True,'actual_P_new_outer_wrapper_verified':False,'actual_P_watched_files':len(plan['invocation']['watched_files']),'exact_P_publications':pubs,'remaining_trials':588,'legacy_prefix_trials':12,'legacy_prefix_origin_retained':True,'allocation_history_GPU_seconds':395,'new_GPU_jobs':0,'state_sha256_unchanged':before,'production_readiness_admitted':False,'final_release':False,'profiling_authorized':False}
 out=save(R/B/'Spatial_actual_P_metadata.json',proof);print(json.dumps({'receipt':out,'effective_plan':pref,'new_GPU_jobs':0,'actual_P_original_verified':True,'new_outer_readiness_pending':True}))

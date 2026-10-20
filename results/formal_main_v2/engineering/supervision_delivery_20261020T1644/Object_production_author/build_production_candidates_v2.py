from pathlib import Path
import hashlib,json,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent;A=D/'attempt04_canonical';O=D/'production_candidates01';C='results/formal_main_v2/execution/object256seed23_source_control_v1_20261020T1644'
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def raw(x):return (json.dumps(x,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2)+chr(10)).encode()
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':h(p)}
def read(p):return json.loads(p.read_bytes())
def module(p,pin):
 assert h(p)==pin;s=importlib.util.spec_from_file_location('_Object23_static_'+p.stem,p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m
control=module(R/'scripts/ops/formal_object256s23_source_bridge_v1/control.py','09ae3486565e17bd2c41b09adbfaa7a6d99f38754d3e77071f77851c9ac54f6f')
ct=module(R/'scripts/ops/formal_action_deployment_v1/contract.py','efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19')
report=read(A/'cpu_report.json');assert report['status']=='passed_canonical_CPU_source_chain_only' and report['checks']==765 and report['source_control']==control.descriptor() and report['root_and_independent_runtime_readiness'] is False
science=read(A/'scientific_plan.json');control.scope_invocation(science['invocation']);action=read(A/'execution_contract.json');args=read(A/'plan_arguments.json')
O.mkdir(exist_ok=False);files=[]
def make(name,obj):
 data=raw(obj);p=O/name
 with p.open('xb') as f:f.write(data)
 rr={'path':C+'/'+name,'sha256':hashlib.sha256(data).hexdigest()};files.append({'source':p.relative_to(R).as_posix(),'destination':rr['path'],'sha256':rr['sha256'],'bytes':len(data)});return rr
sr=make('scientific_plan.json',science);ar=make('execution_contract.json',action);pr=make('plan_arguments.json',args)
effective=ct.effective_plan(science,scientific_plan_ref=sr,execution_contract_ref=ar,execution_contract=action);control.scope_invocation(effective['invocation']);er=make('effective_plan.json',effective)
ct.validate_effective(science,effective,scientific_plan_ref=sr,execution_contract_ref=ar,execution_contract=action)
assert not any((R/x['destination']).exists() for x in files),'canonical static target already exists; root must reconcile'
bundle={'schema':'formal_main_v2','kind':'object256s23_canonical_static_plan_candidates','status':'canonical_control_CPU_checked_static_plans_unpublished','suite':'libero_object','budget':256,'seed':23,'method_ids':control.METHODS,'stage':'development','expected_trials':200,'unique_development_initial_states':100,'canonical_directory':C,'canonical_files':files,'scientific_plan':sr,'execution_contract':ar,'plan_arguments':pr,'effective_plan':er,'plan_sha256':effective['plan_sha256'],'manifest':{'path':control.MANIFEST,'sha256':control.MANIFEST_SHA},'explicit_source_control':control.descriptor(),'gateway_files':control.closure(),'author_canonical_report':ref(A/'cpu_report.json'),'root_snapshot':read(D/'canonical_state_reference.json'),'actual_P_original_metadata_verify':True,'actual_P_outer_wrapper_positive_verify':False,'runtime_readiness':None,'prepared_invocation':None,'root_authorization':None,'GPU_runs':0,'Slurm_calls':0,'state_mutated':False,'private_plan_paths_not_used_in_effective_references':True,'all_pair_GPU_seconds':58917,'failed_GPU_seconds_retained':84,'component_reviews_must_remain_original':True}
p=O/'plan_bundle.json'
with p.open('xb') as f:f.write(raw(bundle))
print(json.dumps({'bundle':ref(p),'files':files,'plan_sha256':effective['plan_sha256']},indent=2))

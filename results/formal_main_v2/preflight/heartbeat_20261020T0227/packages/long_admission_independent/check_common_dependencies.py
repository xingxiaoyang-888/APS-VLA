from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=R/'.local/long_action_admission_audit_1827'
refs={};checks=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def watch(p,expected=None):
 p=Path(p);p=p if p.is_absolute() else R/p
 assert p.is_relative_to(R) or p.is_relative_to(P)
 assert not (set(p.suffixes)&{'.pt','.pth','.bin','.safetensors','.init','.pruned_init'}) and not any('sealed' in x.lower() for x in p.parts)
 v=h(p);assert expected is None or v==expected,(str(p),v,expected);refs[str(p)]={'sha256':v,'bytes':p.stat().st_size};return p

def read(p,expected=None):return json.loads(watch(p,expected).read_text())
def ck(n,v):
 checks.append({'check':n,'passed':bool(v)});assert v,n

def save(name,obj):
 with (D/name).open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
filemap={
'runtime_scope.py':'6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53',
'contract.py':'efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19',
'entry.py':'2cdb69923146cbffcaaec555b970d03efbce0c9b9f74e3b743a2ce67a21aae19',
'wrapper.py':'d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33',
'gateway.py':'8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a',
'reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd',
'consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'}
files={'scripts/ops/formal_action_deployment_v1/'+n:v for n,v in filemap.items()}
for n,v in files.items():watch(R/n,v);watch(P/n,v)
oldready=read('results/formal_main_v2/execution/action_spatial_resume_0943/runtime_readiness.json','3e192788730bdfd97115713c332640c3b2de1f380e046ec7d045d274b9e07bb4')
oldauth=read('results/formal_main_v2/execution/action_spatial_resume_0943/submission_authorization.json','55f6c06a83847f8f60850309cdade6991cc70ba3e83451f086632c3d76504cd6')
component_refs={**oldready['component_reviews'],'gateway':oldauth['independent_review']};covered={};component_results=[]
for role,ref in component_refs.items():
 doc=read(ref['path'],ref['sha256'])
 ck(role+'_typed_component',doc['status']=='passed_CPU_review' and not doc.get('blockers') and (doc['kind']=='formal_downstream_server_gateway_independent_CPU_review' if role=='gateway' else doc['kind']=='formal_downstream_action_component_independent_CPU_review' and doc['component']==role))
 for n,v in doc['files'].items():
  ck(role+'_same_published_source_'+n,files.get(n)==v);watch(R/n,v);watch(P/n,v);covered[n]=v
 original=doc.get('original_independent_review')
 if original:read(original['path'],original['sha256'])
 component_results.append({'role':role,'reference':ref,'source_files':doc['files'],'inherited_CPU_evidence_only':True,'new_tests_run':0,'per_plan_admission_inherited':False})
ck('seven_files_covered_by_original_components',covered==files)
p=R/'scripts/ops/formal_action_deployment_v1/runtime_scope.py';sp=importlib.util.spec_from_file_location('actual_runtime_contract_closure_only',p);runtime=importlib.util.module_from_spec(sp);exec(compile(p.read_bytes(),str(p),'exec'),runtime.__dict__)
contract=runtime.make_contract(project_root=P,source_root=S,suite='libero_10',stage='development')
actual=runtime.validate_contract(contract,project_root=P,source_root=S)
for p,v in actual.items():watch(p,v)
common_publications={**files,**contract['dependencies'],**{r['path']:r['sha256'] for r in contract['engineering_acceptance'].values()},contract['source_inventory']['path']:contract['source_inventory']['sha256']}
for n,v in common_publications.items():watch(R/n,v);watch(P/n,v)
repair=read('results/formal_main_v2/preflight/heartbeat_20261019T2318/Spatial_dependency_repair.json','cb01f132002151d83eef8e5ba4c3f4228110eb8fc9a911546fb7946a82122569')
ck('Spatial_prior_review_failure_boundary_retained',repair['failed_job_id']=='3042529' and repair['child_started'] is False and repair['models_loaded'] is False and repair['new_trials']==0 and repair['missing_dependency']['sha256']=='9e14b86a1e556c53ef1cbd8c7bdc1733c3d5eb744f62ffee8df9395645816650')
source_ext=[]
for rel,ranges in [('scripts/ops/formal_action_deployment_v1/gateway.py',[(81,160),(252,290),(324,344)]),('scripts/ops/formal_action_deployment_v1/wrapper.py',[(46,92)]),('scripts/ops/formal_action_deployment_v1/contract.py',[(98,198),(201,229)])]:
 a=(R/rel).read_text().splitlines();source_ext.append({'path':rel,'sha256':h(R/rel),'ranges':[{'start':x,'end':y,'text':'\n'.join(f'{i+1}: {a[i]}' for i in range(x-1,y))} for x,y in ranges]})
save('actual_common_closure.json',{'schema':'formal_main_v2','kind':'Long_action_common_dependency_inheritance_audit','status':'passed_common_metadata_closure_only','utc':datetime.now(timezone.utc).isoformat(),'runtime_sources':files,'inherited_component_refs':component_results,'runtime_contract':contract,'actual_runtime_validate_contract_checked_count':len(actual),'common_runtime_publications':common_publications,'checks':checks,'evidence_refs':refs,'scientific_GPU_execution_proven':False,'new_plan_readiness_proven':False,'legacy_Spatial_readiness_or_authorization_reused':False,'source_guard_evidence':source_ext,'limitations':['This is actual server R/P/S metadata hashing and original runtime.validate_contract only; no runtime scope is entered and no model is loaded.','Prior component CPU tests are inherited at exact bytes, not rerun or counted as new GPU evidence.','Each of the eight plans still needs its own exact science/effective/contract/prepared invocation, per-plan root and independent admission, readiness, publication closure, and one-shot authorization/reservation.','production_chain_complete means exact pre-execution control/source closure; actual_GPU_runtime_chain_verified must remain false until an actual new action runtime chain completes and is raw-reviewed.','Gateway/wrapper do not themselves cross-check the nested root/independent plan refs beyond source/version/complete. This audit must require exact per-plan bindings, not accept old Spatial plan reviews merely because the same source bytes match.'],'state_P_Git_or_canonical_written':False,'GPU_or_Slurm_calls':0,'sealed_or_weight_values_read':False})
print(json.dumps({'status':'passed_common_metadata_closure_only','checks':len(checks),'actual_runtime_inputs':len(actual),'refs':len(refs),'common_publications':len(common_publications)},ensure_ascii=False))

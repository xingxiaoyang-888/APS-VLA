from pathlib import Path
import ast,copy,datetime,difflib,hashlib,importlib.util,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');S=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_run_564be0995e');C=R/'.local/action_runtime_lifecycle_v4_1940';O=R/'.local/action_runtime_lifecycle_v4_audit_1940';V3=R/'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,obj):
 p=O/name
 with p.open('x') as f:f.write(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 return {'path':str(p),'sha256':sha(p)}
expected={'probe.py':'91e12f29ad39591c29cfd63912394949d1cad932bb80c8a871ed852cea32cadc','test_lifecycle.py':'75b10e4fd075d584206e95f1811c73b64cc179d2743ef707ffc56cf12126ad1b','candidate_manifest.json':'25d6e0e831d7e7770150bd2008e49991ec10bddbd815a3400f7a60b539404d26'}
for n,h in expected.items():assert sha(C/n)==h
spec=importlib.util.spec_from_file_location('_independent_seal_v4',C/'probe.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
prepared=m.prepare(R,S,'.local/action_runtime_lifecycle_v4_1940/candidate_manifest.json',expected['candidate_manifest.json'])
readset=prepared['evidence'].seen
assert len(readset)==278
readref=write('actual_R_S_metadata_readset.json',{'paths_sha256':readset,'count':len(readset),'source_root':str(S),'project_root':str(R),'no_GPU_or_weight_load':True})
inv=prepared['inventory'];both={}
for root in [R,S]:
 for rel,h in inv['files'].items():
  p=root/rel;assert sha(p)==h;both[str(p)]=h
assert len(both)==346
sourceref=write('source173_R_S_recheck.json',{'source_inventory_sha256':sha(R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'),'path_sha256':both,'unchanged':True})
old=ast.parse((V3/'probe.py').read_text());new=ast.parse((C/'probe.py').read_text())
oldbody={n.name:ast.dump(n,include_attributes=False) for n in old.body if isinstance(n,(ast.ClassDef,ast.FunctionDef))};newbody={n.name:ast.dump(n,include_attributes=False) for n in new.body if isinstance(n,(ast.ClassDef,ast.FunctionDef))}
assert set(newbody)-set(oldbody)=={'PrismaticProcessLifecycle'}
assert [k for k in oldbody if oldbody[k]!=newbody[k]]==['gpu_body']
class UndoLifecycle(ast.NodeTransformer):
 def visit_ClassDef(self,n):return None if n.name=='PrismaticProcessLifecycle' else self.generic_visit(n)
 def visit_ImportFrom(self,n):return None if any(a.asname=='frozen_runtime' for a in n.names) else n
 def visit_Assign(self,n):
  if len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
   key=n.targets[0].id
   if key in ['runtime_rel','lifecycle']:return None
   if key in ['VERSION','GPU_VERSION']:
    return copy.deepcopy(next(x for x in old.body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id==key))
  return self.generic_visit(n)
 def visit_Expr(self,n):
  if isinstance(n.value,ast.Call):
   c=n.value
   if isinstance(c.func,ast.Attribute) and isinstance(c.func.value,ast.Name):
    if c.func.value.id=='lifecycle' and c.func.attr=='finish':return None
    if c.func.value.id=='journal' and c.func.attr=='emit' and c.args and isinstance(c.args[0],ast.Constant) and c.args[0].value=='runtime_compat_lifecycle_verified':return None
  return self.generic_visit(n)
 def visit_Call(self,n):
  if isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='lifecycle' and n.func.attr=='load':
   assert isinstance(n.args[0],ast.Name) and n.args[0].id=='load_openvla_oft_components'
   n.func=n.args.pop(0);n.keywords.append(ast.keyword(arg='use_minimal_prismatic_compat',value=ast.Constant(value=True)))
  return self.generic_visit(n)
normalized=UndoLifecycle().visit(copy.deepcopy(new))
assert ast.dump(old,include_attributes=False)==ast.dump(normalized,include_attributes=False)
a=json.loads((V3/'candidate_manifest.json').read_text());b=json.loads((C/'candidate_manifest.json').read_text())
changed=[k for k in set(a)|set(b) if a.get(k)!=b.get(k)];assert set(changed)=={'version','pending'}
oldfiles={n:sha(V3/n) for n in ['probe.py','launcher.py','submit.py','action_adapter.py','constructor_independent_cpu.json','candidate_manifest.json','probe.slurm','node_exclusion.py']}
expectedold={'probe.py':'ba7363695b9a67324b3717632d7571e5ceccd5e91683673ff65c0801e1e4a004','launcher.py':'13c9a2e60e0b0a9eeeb1460ff5121c1c7305c8106420a6dc21dca6634fc712c5','submit.py':'f5a4efc24f9b77b54ca73bbf0a8626e9ebde9c416ac1305cf4e88cd55ad8b8dc','action_adapter.py':'b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185','constructor_independent_cpu.json':'171b93b145431bdffb9138eea48673e9185dcadbef226e468d0ab140a7a470f1','candidate_manifest.json':'832cdad374e1dfd5cef04870a14f440ec37a1194dea9130b95c7ddd9c7be782e','probe.slurm':'69277a63fcbcb24f94a6d333bb70e490f702df9edade25e042b49fdaafe37dc0','node_exclusion.py':'0886ce865ca3edc01bf1ba4d875d139bdf8267a2b6992d1630f1a84c4efcc506'}
assert oldfiles==expectedold
D=C/'dispatch_candidate';der=json.loads((D/'mechanical_derivation.json').read_text());derived={}
for name in ['launcher.py','submit.py','node_exclusion.py','probe.slurm']:
 assert sha(V3/name)==der[name]['parent_sha256'] and sha(D/name)==der[name]['candidate_sha256']
 oldtext=(V3/name).read_text();newtext=(D/name).read_text()
 if name=='launcher.py':
  for x,y in [('formal_main_v2_action_execution_compat_gpu_v4','formal_main_v2_action_execution_compat_gpu_v3'),('action-execution-gpu-candidate-1940-v4-runtime-lifecycle','action-execution-gpu-candidate-0840-v3-constructor'),('root-action-execution-engineering-dispatch-v4-runtime-lifecycle','root-action-execution-engineering-dispatch-v3-stdin-constructor')]:newtext=newtext.replace(x,y)
 elif name=='node_exclusion.py':
  newtext=newtext.replace('v4','v3').replace('e87beacdb0ff23f293c7f6009f090a614c2903a37d6ff8e4732714236e0425c0','69277a63fcbcb24f94a6d333bb70e490f702df9edade25e042b49fdaafe37dc0')
 elif name=='probe.slurm':newtext=newtext.replace('formal_main_v2_action_execution_compat_gpu_v4','formal_main_v2_action_execution_compat_gpu_v3')
 assert newtext==oldtext
 derived[name]={'sha256':sha(D/name),'mechanical_exact_text_after_enumerated_reversal':True}
staticref=write('static_scope_review.json',{'probe_normalized_AST_equals_v3':True,'probe_ast_changes':['VERSION','GPU_VERSION','PrismaticProcessLifecycle class','gpu_body runtime guard initialization, lifecycle load, lifecycle event, finish'],'manifest_changed_keys':sorted(changed),'old_v3_files_unchanged':oldfiles,'derived_dispatch':derived,'dispatch_complete_or_authorized':False,'action_adapter_original_v3_path_and_bytes_reused':True,'runtime_object_binding':'gpu_body imports canonical cti_vla runtime from pinned S and passes source/runtime_rel + sources[runtime_rel]; each module export matched to pre-load trusted runtime','asset_compatibility':'formal_asset_metadata_adapter only patches checkpoint_manifest.load_checkpoint_manifest; unchanged main component loader supports False branch','goal_compatibility':'formal_goal_component_adapter patches _load_component_state only and checks unchanged load_openvla_oft_components; lifecycle changes bool argument through existing API'})
for name in ['independent_a2','author_rerun_a2','metadata_actual_S_a2']:
 rec=json.loads((O/(name+'.execution.json')).read_text());assert rec['returncode']==0
 assert sha(O/(name+'.stdout'))==rec['stdout_sha256'] and sha(O/(name+'.stderr'))==rec['stderr_sha256']
refs=dict(readset);refs.update(both)
for folder in [O,C]:
 for p in folder.rglob('*'):
  if p.is_file() and p.suffix not in ['.pyc'] and '__pycache__' not in p.parts:refs[str(p)]=sha(p)
for p in [R/'scripts/ops/formal_asset_metadata_adapter.py',R/'scripts/ops/formal_goal_component_adapter.py',R/'.local/action_v3_actual_GPU_audit_1940/final_a2/report.json',R/'.local/action_v3_actual_GPU_audit_1940/final_a2/references.json']+[V3/n for n in oldfiles]:refs[str(p)]=sha(p)
for p,h in refs.items():assert sha(p)==h
prepared['evidence'].unchanged()
refref=write('references.json',{'path_sha256':refs,'count':len(refs),'scope':'Metadata and CPU source/test/audit artifacts only; no model weights, checkpoint payloads or sealed state files loaded.'})
report={'schema':'formal_main_v2','kind':'action_runtime_lifecycle_v4_independent_CPU_review','status':'passed_CPU_review_pending_new_registered_16_cell_GPU_acceptance','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_files':{str(C/n):h for n,h in expected.items()},'tests':{'independent_real_frozen_S_runtime':{'passed':7,'failed':0,'four_previously_reproduced_counterexamples_now_rejected':True},'author_tests_independently_rerun':{'passed':28,'failed':0},'actual_R_control_S_source_metadata':{'inputs':278,'cells':16,'passed':True}},'scientific_source173_R_S_unchanged':True,'old_v3_eight_source_files_unchanged':True,'probe_AST_scope_verified':True,'manifest_panels_methods_budgets_unchanged':True,'runtime_guard':{'one_true_then_three_false':True,'trusted_runtime_path_SHA_and_module_globals_before_first_loader':True,'first_export_match_to_trusted_preload_objects':True,'subsequent_module_identity_and_mask_primitive_verified':True,'failure_poisoned_no_retries':True,'no_production_sysmodules_deletion':True},'compatibility_review':{'official_loader_existing_False_branch_validates_constants':True,'asset_and_goal_adapters_preserve_full_loader_and_bool_parameter':True,'full_model_loading_validation_requires_new_GPU_attempt':True},'control_derivation':{'mechanical_derivation_allowed':True,'existing_candidate_enumerated_text_reversal_matches_v3':True,'fully_registered_or_submit_ready':False,'conditions':['new versioned complete exact SHA closure and typed registration','new root reservation and one-shot invocation; consumed v3 reservation cannot be reused','reviewed autonomous coexistence facade bound to new identities','root-only fresh no-duplicate and capacity checks before dispatch']},'actual_v3_GPU_status':{'job_id':3034675,'failed':True,'completed_cells':4,'required_cells':16,'GPU_seconds':303,'scientific_rollouts_may_resume':False,'actual_report_ref':{'path':str(R/'.local/action_v3_actual_GPU_audit_1940/final_a2/report.json'),'sha256':sha(R/'.local/action_v3_actual_GPU_audit_1940/final_a2/report.json')}},'first_candidate_failure_preserved':{'path':str(O/'initial_findings.json'),'sha256':sha(O/'initial_findings.json'),'counterexample_raw':{'path':str(O/'first_capture_boundary_a1.json'),'sha256':sha(O/'first_capture_boundary_a1.json')}},'evidence':[readref,sourceref,staticref,refref],'remaining_blockers':[],'limitations':['CPU-only independent review; no new model load or GPU attempt.','Does not constitute controller-action GPU acceptance, closed-loop success/latency evidence, final-state release, or submission authority.','Original v3 remains failed with only Long 4/16 cells; all original failures and GPU cost retained.'],'actions':{'GPU_calls':0,'Slurm_submissions':0,'production_state_writes':0,'scientific_source_edits':0,'model_weight_loads':0,'sealed_state_reads':0,'local_Windows_project_writes':0,'writes_only_audit_directory':str(O)}}
rr=write('independent_review.json',report)
print(json.dumps({'review':rr,'references':refref,'tests':report['tests'],'status':report['status']},ensure_ascii=False))

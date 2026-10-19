from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,sys,traceback
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=R/'.local/long_action_admission_audit_1827'
refs={};checks=[];rows=[]
def watch(p,expected=None):
 p=Path(p);p=p if p.is_absolute() else R/p
 assert p.is_relative_to(R) or p.is_relative_to(P)
 assert not any('sealed' in x.lower() for x in p.parts) and not set(p.suffixes)&{'.pt','.pth','.bin','.safetensors','.ckpt','.init','.pruned_init'}
 a=p.stat();raw=p.read_bytes();b=p.stat();assert (a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(b.st_ino,b.st_size,b.st_mtime_ns,b.st_ctime_ns)
 h=hashlib.sha256(raw).hexdigest();assert expected is None or h==expected,(str(p),h,expected)
 refs[str(p)]={'sha256':h,'bytes':len(raw)};return raw
def read(p,h=None):return json.loads(watch(p,h))
def ck(name,value):
 checks.append({'check':name,'passed':bool(value)});assert value,name

def load(rel,pin,name):
 p=R/rel;raw=watch(p,pin);spec=importlib.util.spec_from_file_location(name,p);mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;exec(compile(raw,str(p),'exec'),mod.__dict__);return mod

def save(name,obj):
 with (D/name).open('x') as f:json.dump(obj,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
try:
 common=read(D/'actual_common_closure.json','7011f6d5549ba4925646024dbdaff157f34b3635c1933d2355afc76e0c1fde23')
 index=read('.local/long_action_outer_1827/outer_index.json','e4c18587396f3f8cee3330bd01104a8db7ca3be38f6b28361e6f11cd425c5f22')
 pubmap=read('.local/long_action_outer_1827/publication_map.json','6fd6543dcb538335122ee369609e3ed68a2faaf9c1bdf33cca207890e9241f7f')
 publication=read('results/formal_main_v2/preflight/heartbeat_20261020T0227/Long_outer_candidate_publication.json','c919f5be4d4574f09f6e1f7884d4a05bdf43c0d9f3a41b8c30afd7e1900e67f1')
 author=read('.local/long_action_outer_1827/candidate_review.json','4a92de2908b1c4365d2ab7a8b4053936a69d68169029ef24eb5d9badea36b435')
 files=common['runtime_sources'];g=load('scripts/ops/formal_action_deployment_v1/gateway.py',files['scripts/ops/formal_action_deployment_v1/gateway.py'],'actual1827gateway_readonly')
 c=load('scripts/ops/formal_action_deployment_v1/contract.py',files['scripts/ops/formal_action_deployment_v1/contract.py'],'actual1827contract_readonly')
 old=load('scripts/server/run_formal_downstream.py','f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24','actual1827legacy_wrapper_readonly')
 publication_rows={x['path']:x for x in publication['files']};pubmap_rows={x['canonical_path']:x for x in pubmap['files']}
 ck('exact_24_publication_sets',len(publication_rows)==24 and set(publication_rows)==set(pubmap_rows))
 expected_pairs={'k128_seed23','k128_seed41','k256_seed17','k256_seed23','k256_seed41','k64_seed17','k64_seed23','k64_seed41'}
 ck('exact_eight_pairs',len(index['shards'])==8 and {s['pair'] for s in index['shards']}==expected_pairs)
 manifests=[];all_methods=[];stagekeys=[];runroots=[];panel=None
 for sh in index['shards']:
  pair=sh['pair'];docs={}
  for role in ('scientific_plan','action_execution_contract','effective_plan'):
   ref=sh[role];docs[role]=read(ref['path'],ref['sha256']);watch(P/ref['path'],ref['sha256'])
   ck(pair+'_'+role+'_root_and_author_publications_match',publication_rows[ref['path']]['sha256']==ref['sha256']==pubmap_rows[ref['path']]['sha256'])
  scientific=docs['scientific_plan'];action=docs['action_execution_contract'];effective=docs['effective_plan'];inner=scientific['invocation'];inv=effective['invocation']
  ck(pair+'_actual_validate_effective',c.validate_effective(scientific,effective,scientific_plan_ref=sh['scientific_plan'],execution_contract_ref=sh['action_execution_contract'],execution_contract=action) is True)
  ck(pair+'_content_signatures',scientific['plan_sha256']==sh['scientific_plan_sha256'] and effective['plan_sha256']==sh['plan_sha256'])
  ck(pair+'_fresh_development_no_legacy_prefix',inner['stage']=='development' and inner['suite']=='libero_10' and inner['resume'] is False and inner['prior_review'] is None and inner['prior_job_ids']==[] and inner['repair_record'] is None and inner['stop_after'] is None and action['transition'] is None)
  ck(pair+'_same_fixed_resources',effective['resources']==g.RESOURCES)
  ck(pair+'_runtime_source_and_contract',action['files']=={**files,**{k:v for k,v in common['runtime_contract']['dependencies'].items() if k.endswith('/action_adapter.py')}} and action['runtime_contract']==common['runtime_contract'])
  prefix=c.resume_prefix_inputs(inner);ck(pair+'_actual_resume_prefix_empty',prefix=={})
  for n,h in inv['root_evidence_sha256'].items():watch(R/n,h)
  for n,h in effective['publish_files'].items():watch(R/n,h);watch(P/n,h)
  base=Path(sh['effective_plan']['path']).parent
  metadata_presence={role:{'path':str(base/name),'R_exists':(R/base/name).exists(),'P_exists':(P/base/name).exists()} for role,name in [('root_review','root_review.json'),('independent_review','independent_review.json'),('runtime_readiness','runtime_readiness.json'),('prepared_invocation','prepared_invocation.json'),('submission_authorization','submission_authorization.json'),('root_reservation','root_reservation.json')]}
  # This invokes real metadata-only code. It does not call Gateway.run, publish,
  # FrozenPlan.prepare, authorizations, Slurm, or any model/runtime action scope.
  io=g.NativeIO(R).preflight({'plan':effective,'invocation':inv,'prefix':prefix,'readiness_files':{}})
  ck(pair+'_actual_NativeIO_all_current_inputs_present',io['missing_publications']==[] and io['output_exists'] is False)
  for n,row in io['checked_files'].items():watch(n,row['sha256'])
  args=old.verify(inner)
  ck(pair+'_actual_original_wrapper_verify_P',args.mode=='evaluate' and args.project_root==P and args.development_panel is not None and args.output==Path(inv['run_root']))
  manifest=read(inner['execution_manifest'],inner['execution_manifest_sha256']);manifestref={'path':str(Path(inner['execution_manifest']).relative_to(P)),'sha256':inner['execution_manifest_sha256']}
  ck(pair+'_manifest_method_order',manifest['suite']=='libero_10' and manifest['split']=='development' and [m['identity']['method_id'] for m in manifest['methods']]==sh['method_ids']==inv['method_ids'])
  ck(pair+'_frozen_environment',manifest['environment']=={'environment_seed':0,'runtime_seed':17,'wait_steps':10,'action_chunk':8,'max_steps':520})
  panelref={'path':manifest['development_panel'],'sha256':manifest['development_panel_sha256']};watch(P/panelref['path'],panelref['sha256']);watch(R/panelref['path'],panelref['sha256'])
  if panel is None:panel=panelref
  ck(pair+'_same_development_panel',panelref==panel)
  ck(pair+'_two_complete_trained_selectors',len(manifest['methods'])==2 and all(m['identity']['training_complete'] is True and m['identity']['future_head_deployed'] is False for m in manifest['methods']))
  ready_base={**effective['publish_files'],sh['effective_plan']['path']:sh['effective_plan']['sha256']}
  rows.append({'pair':pair,'scientific_plan':sh['scientific_plan'],'action_execution_contract':sh['action_execution_contract'],'effective_plan':sh['effective_plan'],'plan_sha256':sh['plan_sha256'],'method_ids':sh['method_ids'],'stage_key':inv['stage_key'],'run_root':inv['run_root'],'invocation_relative':effective['invocation_relative'],'fixed_resources':effective['resources'],'fresh_no_prior_or_transition':True,'execution_manifest':manifestref,'development_panel':panelref,'actual_NativeIO_preflight':io,'actual_original_wrapper_verify_P':True,'runtime_publication_required_known_exact':ready_base,'per_plan_root_signing_roles_still_required':metadata_presence,'component_audit_refs_inherited':{x['role']:x['reference'] for x in common['inherited_component_refs']},'expected_new_trials':200,'new_scientific_trials_completed':0,'full_new_wrapper_verify_performed':False,'FrozenPlan_prepare_or_validate_authorization_performed':False})
  all_methods.extend(sh['method_ids']);stagekeys.append(inv['stage_key']);runroots.append(inv['run_root']);manifests.append(manifestref)
 ck('sixteen_unique_methods_exact',len(all_methods)==16 and len(set(all_methods))==16 and sorted(all_methods)==index['methods'])
 ck('eight_nonoverlapping_fresh_stage_output_roots',len(set(stagekeys))==len(set(runroots))==8)
 ck('no_old_full_references_or_A128_seed17_repeated',all(x not in all_methods for x in ['Dense','A128_seed17','B128_seed17']) and all(x.startswith(('A','B')) for x in all_methods))
 for n,v in common['runtime_sources'].items():watch(R/n,v);watch(P/n,v)
 for p,row in list(refs.items()):watch(p,row['sha256'])
 report={'schema':'formal_main_v2','kind':'Long16_fresh_action_actual_dependency_admission_audit','status':'passed_pre_readiness_actual_dependency_closure','utc':datetime.now(timezone.utc).isoformat(),'execution_version':'formal-downstream-action-v1','runtime_sources':files,'common_closure':{'path':str((D/'actual_common_closure.json').relative_to(R)),'sha256':'7011f6d5549ba4925646024dbdaff157f34b3635c1933d2355afc76e0c1fde23'},'outer_index':{'path':'.local/long_action_outer_1827/outer_index.json','sha256':'e4c18587396f3f8cee3330bd01104a8db7ca3be38f6b28361e6f11cd425c5f22'},'publication':{'path':'results/formal_main_v2/preflight/heartbeat_20261020T0227/Long_outer_candidate_publication.json','sha256':'c919f5be4d4574f09f6e1f7884d4a05bdf43c0d9f3a41b8c30afd7e1900e67f1'},'plans':rows,'checks':checks,'evidence_refs':refs,'unique_P_S_NativeIO_inputs':len({n for row in rows for n in row['actual_NativeIO_preflight']['checked_files']}),'submission_authorized':False,'actual_GPU_runtime_chain_verified':False,'scientific_trials_completed_by_new_runtime':0,'full_new_wrapper_verify_passed':False,'production_chain_complete':False,'production_chain_complete_meaning':'This report is pre-readiness dependency closure only. Final production_chain_complete may mean exact pre-execution control/source closure after genuine per-plan reviews/readiness/prepared invocation and actual P wrapper verification; it must never mean actual GPU execution.','remaining_conditions':['Root must sign and publish each exact per-plan root review, independent review, readiness, prepared invocation, single-use authorization and its owned reservation. Original source/component receipts can be inherited but old Spatial plan-specific approval cannot.','Readiness runtime_publication_files must include the effective plan file and both nested root/independent reviews in addition to the 22 effective-plan publications. The readiness file itself is added by the gateway; publish component review files explicitly if the chosen consumer directly reads them.','Nested root/independent reviews must bind exact scientific/effective/action-contract file references and content plan SHA, method IDs, suite and stage. Current gateway/wrapper checks nested version/sources/completion but not all these plan refs.','Before submission execute actual validate_authorization, full-registry FrozenPlan.prepare, fresh NativeIO with complete readiness files, and full new wrapper.verify(P). No current source-check result substitutes for them.','This fresh chain has no prior_review, prior_job_ids, repair_record or transition, preventing the former Spatial missing-prior startup dependency. Never infer whole-ancestry equivalence or old performance reuse from these fresh metadata checks.','Actual final success requires real GPU/raw journal verification. O2A, whole-ancestry consumption and global/final release remain separate gates.'],'writes_limited_to_audit_and_required_transport_journal':True,'state_P_Git_or_canonical_written':False,'model_or_checkpoint_loaded':False,'sealed_values_read':False,'GPU_or_Slurm_calls':0}
 save('eight_plan_actual_closure.json',report)
 print(json.dumps({'status':report['status'],'plans':len(rows),'checks':len(checks),'refs':len(refs),'unique_P_S_inputs':report['unique_P_S_NativeIO_inputs'],'missing_current_runtime_inputs':sum(len(x['actual_NativeIO_preflight']['missing_publications']) for x in rows),'new_GPU_seconds':0,'full_new_wrapper_pending':True},ensure_ascii=False))
except BaseException as exc:
 save('eight_plan_failure_a1.json',{'exception':repr(exc),'traceback':traceback.format_exc(),'checks':checks,'completed_plans':rows,'evidence_refs':refs})
 raise

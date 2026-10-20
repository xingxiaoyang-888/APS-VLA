from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,copy,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D='results/formal_main_v2/execution/nonLong_action_v1_20261020T1530';B='results/formal_main_v2/preflight/heartbeat_20261020T2330'
AUTHOR_REF={'path': 'results/formal_main_v2/engineering/supervision_delivery_20261020T1530/plan_author/attempt01/candidate_review.json', 'sha256': '6623e8c6c9a828fcd74701405486440fd476d4895bc4c526efbdd543b0f87054'}
INDEX_REF={'path': '.local/nonLong64_development_independent_20261020T1530/independent_index.json', 'sha256': '393e453ca855828c3b12cd560b7c650ade0e9055da6495ef9ae8b352e48d126c'}
GROUPS={'libero_spatial_k64_seed17': ['libero_spatial', 64, 17, ['A64_seed17', 'B64_seed17'], 220], 'libero_spatial_k64_seed41': ['libero_spatial', 64, 41, ['A64_seed41', 'B64_seed41'], 220], 'libero_object_k64_seed17': ['libero_object', 64, 17, ['A64_seed17', 'B64_seed17'], 280], 'libero_object_k64_seed41': ['libero_object', 64, 41, ['A64_seed41', 'B64_seed41'], 280]}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel):return json.loads((R/rel).read_bytes())
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def checkref(rr):
 assert h(R/rr['path'])==rr['sha256'];return read(rr['path'])
def write(rel,obj):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 raw=(json.dumps(obj,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode()
 with p.open('xb') as f:f.write(raw)
 return ref(rel)
def cp(src,dst,pin,base=R):
 p=R/src;out=base/dst;assert h(p)==pin and not p.is_symlink();out.parent.mkdir(parents=True,exist_ok=True)
 assert not any(z.is_symlink() for z in [out,*out.parents])
 if out.exists():assert h(out)==pin
 else:
  with out.open('xb') as f:f.write(p.read_bytes())
 return dict(path=dst,sha256=pin)
author=checkref(AUTHOR_REF);index=checkref(INDEX_REF);shards=index.get('shards',index.get('plans'));assert len(shards)==4
authors={row['group_key']:row for row in author['plans']};assert set(authors)==set(GROUPS) and author['total_planned_trials']==800
oldD='results/formal_main_v2/execution/long_remaining16_action_v1_1827/k64_seed41'
oldready=read(oldD+'/runtime_readiness.json');oldauth=read(oldD+'/submission_authorization.json')
gp=R/'scripts/ops/formal_action_deployment_v1/gateway.py';assert h(gp)=='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a'
spec=importlib.util.spec_from_file_location('signnonlong20261020T1530gateway',gp);g=importlib.util.module_from_spec(spec);sys.modules[spec.name]=g;spec.loader.exec_module(g)
c=g.load(R/g.CONTROLLER,g.CONTROLLER_SHA,'signnonlong20261020T1530controller')
wrapper=g.load(P/'scripts/ops/formal_action_deployment_v1/wrapper.py','d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33','signnonlong20261020T1530_actual_P_wrapper')
checks=[];began=time.perf_counter()
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state_sha=h(R/g.STATE);state=read(g.STATE)
 assert state['pending_submission'] is None and state['autonomous_training_v1']['reserved_GPU_slots']==0 and state['autonomous_training_v1']['root_submission_hold'] is None
 for sh in shards:
  sub=sh['group_key'];suite,budget,seed,methods,horizon=GROUPS[sub];assert sh['suite']==suite;dd=D+'/'+sub
  iv=checkref(sh['candidate']);arow=authors[sub]
  sciref=arow['scientific_plan'];effref=arow['effective_plan'];actionref=arow['execution_contract']
  science=checkref(sciref);eff=checkref(effref);action=checkref(actionref)
  assert iv['status']=='passed' and iv['production_chain_complete'] is True and not iv['actual_GPU_runtime_chain_verified']
  for key,value in [('scientific_plan',sciref),('effective_plan',effref),('action_execution_contract',actionref),('plan_sha256',eff['plan_sha256']),('method_ids',methods)]:
   assert iv[key]==value,(suite,key)
  assert iv['runtime_sources']==action['files']
  assert iv['suite']==suite and iv['allowed_stages']==['development'] and not iv['resume'] and iv['prior_job_ids']==[]
  assert science['invocation']['method_ids']==methods and eff['invocation']['method_ids']==methods
  assert not (R/science['invocation_relative']).exists() and not (P/science['invocation_relative']).exists() and not Path(science['invocation']['run_root']).exists()
  for n,pin in {**iv['runtime_sources'],**dict(action['GPU_acceptance'])}.items():assert h(R/n)==pin
  for rr in oldready['component_reviews'].values():
   rv=checkref(rr);assert rv['status']=='passed_CPU_review' and not rv['blockers']
  canonical=dd+'/plan_independent_review.json';assert sh['canonical_path']==canonical
  indref=cp(sh['candidate']['path'],canonical,sh['candidate']['sha256'])
  now=datetime.now(timezone.utc).isoformat()
  fields=dict(execution_version=g.OUTER_VERSION,production_chain_complete=True,production_chain_complete_meaning='Exact development pre-execution metadata/source/consumer closure only; not a newly executed GPU chain.',actual_GPU_runtime_chain_verified=False,scientific_trials_completed_by_new_runtime=0,runtime_sources=action['files'],scientific_plan=sciref,effective_plan=effref,action_execution_contract=actionref,plan_sha256=eff['plan_sha256'],method_ids=methods,allowed_stages=['development'],allowed_suite=suite,scientific_settings_changed=False,O2A_enabled=False,global_freeze_enabled=False,final_evaluation_enabled=False,expected_trials=100*len(methods),unique_development_initial_states=100,prior_job_ids=[],historical_results_preserved=True,historical_trials_rerun=False,horizon=horizon)
  rootref=write(dd+'/plan_root_review.json',dict(schema='formal_main_v2',kind='formal_action_development_plan_root_review',status='passed',reviewed_by='root',utc=now,independent_review=indref,author_review=AUTHOR_REF,root_explicit_all_plan_fields_and_methodIDs_checked=True,inherited_GPU_engineering=action['GPU_acceptance'],positive_full_outer_wrapper_verification_required=True,**fields))
  pubs={**{rr['path']:rr['sha256'] for rr in oldready['component_reviews'].values()},rootref['path']:rootref['sha256'],indref['path']:indref['sha256'],effref['path']:effref['sha256'],sciref['path']:sciref['sha256'],actionref['path']:actionref['sha256']}
  ready=dict(schema='formal_main_v2',kind='formal_action_runtime_readiness',status='passed',reviewed_by='root',utc=now,active=False,activation_meaning='Prepared and reviewed only; no slot reservation activated and no invocation registered.',raw_consumer_ready=True,root_review=rootref,independent_review=indref,component_reviews=oldready['component_reviews'],support_files=eff['invocation']['support_files'],runtime_publication_files=pubs,forbidden_stages=['collect','full','components','global_freeze','final'],**fields)
  rr=write(dd+'/runtime_readiness.json',ready)
  prepared={**eff['invocation'],'registered_utc':now,'plan_sha256':eff['plan_sha256'],'runtime_readiness':rr};pr=write(dd+'/prepared_invocation.json',prepared)
  args=dict(stage='development',source_inventory=g.INVENTORY,execution_manifest=arow['manifest']['path'],output_relative=None,freeze_directory=None,profile_panel=None,prior_review=None,collection_review=None,repair_record=None,resume=False,stop_after=None)
  auth=copy.deepcopy(oldauth);auth.update(plan=effref,scientific_plan=sciref,prepared_invocation=pr,runtime_readiness=rr,approved_utc=now,plan_arguments=args);auth.pop('root_reservation')
  reservation=dict(schema='formal_main_v2',kind='root_downstream_GPU_slot_reservation',status='approved_for_exact_downstream_request',reviewed_by='root',approved_utc=now,controller_job_id='3034538',reserved_slots=1,capacity_limit_all_GPU_modes=8,automatic_retry=False,stage_key=eff['invocation']['stage_key'],plan=effref,authorization_path=dd+'/submission_authorization.json',authorization_intent_sha256=g.intent_sha(auth),scope='Only this exact previously unrun nonLong development group; inactive until shared state explicitly binds it.')
  rv=write(dd+'/reservation_root_record.json',reservation);auth['root_reservation']=rv;authref=write(dd+'/submission_authorization.json',auth)
  a,e,plan,inner,inv=g.validate_authorization(R,authref);bundle=g.FrozenPlan(R,a,e,plan,inner,inv).prepare(state);bundle['readiness_files']={**pubs,rr['path']:rr['sha256']}
  io=g.NativeIO(R);io.preflight(bundle);_,publish=io._watch(bundle)
  published=[]
  for n,pin in publish.items():
   if not (P/n).exists():published.append(n)
   cp(n,n,pin,base=P)
  actual=io._inputs(bundle,False);assert actual['missing_publications']==[]
  verified=wrapper.verify(inv,project=P)
  assert verified['effective_plan']==eff and verified['original_plan']==science and verified['execution_contract']==action
  e.unchanged();assert h(R/g.STATE)==state_sha
  check=write(dd+'/root_pre_execution_check.json',dict(schema='formal_main_v2',kind='root_actual_P_wrapper_readonly_verification',status='passed_actual_unchanged_P_wrapper_verify_and_NativeIO',utc=datetime.now(timezone.utc).isoformat(),suite=suite,authorization=authref,readiness=rr,reservation=rv,prepared_invocation=pr,root_review=rootref,independent_review=indref,scientific_plan=sciref,effective_plan=effref,action_execution_contract=actionref,plan_sha256=eff['plan_sha256'],method_ids=methods,runtime_files_checked=len(actual['checked_files']),published_metadata_files=published,full_P_wrapper_verify=True,real_full_registry_scientific_reconstruction=True,state_sha256=state_sha,state_unchanged=True,live_capacity_not_queried=True,reservation_not_activated=True,actual_GPU_runtime_chain_verified=False,model_not_loaded=True,new_trials=0,new_GPU_submissions=[]))
  checks.append(dict(group_key=sub,suite=suite,budget=budget,seed=seed,methods=methods,authorization=authref,readiness=rr,reservation=rv,prepared_invocation=pr,root_check=check,independent_review=indref,expected_trials=100*len(methods)))
 assert h(R/g.STATE)==state_sha
 receipt=write(B+'/nonLong_runtime_readiness_root_index.json',dict(schema='formal_main_v2',status='passed_4_exact_development_pre_execution_checks_pending_live_capacity',utc=datetime.now(timezone.utc).isoformat(),shards=checks,actual_full_P_wrapper_verifications=4,all_original_scientific_plans_rebuilt_from_full_registry=True,state_sha256=state_sha,state_unchanged=True,new_GPU_submissions=[],new_trials=0,actual_GPU_runtime_chain_verified=False,final_release=False,elapsed_seconds=time.perf_counter()-began))
 with (R/B/'root_operations/sign_nonlong_readiness_20261020T1530.py').open('xb') as f:f.write(Path(__file__).read_bytes())
 print(json.dumps(dict(receipt=receipt,readiness=4,actual_P_wrapper_pass=4,new_GPU=0,state_unchanged=True)),flush=True)

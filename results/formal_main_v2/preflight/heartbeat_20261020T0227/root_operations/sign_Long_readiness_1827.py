
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,copy,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D='results/formal_main_v2/execution/long_remaining16_action_v1_1827';B='results/formal_main_v2/preflight/heartbeat_20261020T0227'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel):return json.loads((R/rel).read_text())
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def checkref(rr):
 assert h(R/rr['path'])==rr['sha256'];return read(rr['path'])
def write(rel,obj):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True);raw=(json.dumps(obj,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode()
 with p.open('xb') as f:f.write(raw)
 return ref(rel)
def cp(src,dst,pin,base=R):
 p=R/src;out=base/dst;assert h(p)==pin and not p.is_symlink();out.parent.mkdir(parents=True,exist_ok=True)
 if out.exists():assert h(out)==pin
 else:
  with out.open('xb') as f:f.write(p.read_bytes())
 assert h(out)==pin
 return dict(path=dst,sha256=pin)
ixrel='.local/long_action_outer_audit_1827/independent_index.json';assert h(R/ixrel)=='795839d52918b19d26f13928fb1dce5f7459e30cc8404585b767730b5cf59fd2';ix=read(ixrel);assert len(ix['shards'])==8
ar=B+'/packages/long_outer_author/candidate_review.json';assert h(R/ar)=='4a92de2908b1c4365d2ab7a8b4053936a69d68169029ef24eb5d9badea36b435';author=read(ar);assert author['tests']['passed']==42
oldD='results/formal_main_v2/execution/action_spatial_resume_0943';oldready=read(oldD+'/runtime_readiness.json');oldauth=read(oldD+'/submission_authorization.json')
args_index=read('.local/long_development_1722/plan_index.json');assert h(R/'.local/long_development_1722/plan_index.json')=='e27f3c8973e778bd98b31327cbfe9b02c91faee4ad73af14e8c6cb8aa0132890'
byargs={f"k{x['visual_tokens']}_seed{x['seed']}":x for x in args_index['plans']}
gp=R/'scripts/ops/formal_action_deployment_v1/gateway.py';assert h(gp)=='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a'
sp=importlib.util.spec_from_file_location('sign1827_gateway',gp);g=importlib.util.module_from_spec(sp);sys.modules[sp.name]=g;sp.loader.exec_module(g)
c=g.load(R/g.CONTROLLER,g.CONTROLLER_SHA,'sign1827_controller')
wrapper=g.load(P/'scripts/ops/formal_action_deployment_v1/wrapper.py','d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33','sign1827_actual_P_wrapper')
checks=[];began=time.perf_counter()
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state_sha=h(R/g.STATE);state=read(g.STATE);assert state['pending_submission'] is None
 assert state['autonomous_training_v1']['reserved_GPU_slots']==1 and state['autonomous_training_v1']['reservation_root_record']['sha256']=='0aabce41556248f83877ce47a102ebb32817624eac4ad04a431862b098289c9d'
 for sh in ix['shards']:
  pair=sh['pair'];dd=D+'/'+pair;iv=checkref(sh['candidate']);science=checkref(sh['scientific_plan']);eff=checkref(sh['effective_plan']);action=checkref(sh['action_execution_contract'])
  assert iv['status']=='passed' and iv['production_chain_complete'] is True and iv['actual_GPU_runtime_chain_verified'] is False and iv['positive_full_outer_wrapper_verification_pending_root_readiness'] is True
  for k in ['scientific_plan','effective_plan','action_execution_contract','plan_sha256','method_ids']:
   assert iv[k]==sh[k],(pair,k)
  assert iv['runtime_sources']==action['files']==author['runtime_sources']
  assert iv['allowed_stages']==['development'] and iv['suite']=='libero_10' and iv['prior_job_ids']==[] and iv['transition'] is None and not iv['resume']
  assert not (R/iv['invocation_relative']).exists() and not (P/iv['invocation_relative']).exists() and not Path(iv['run_root']).exists()
  for rr in [iv['independent_checks'],iv['independent_reconstruction'],iv['author_source'],iv['root_publication']]:assert h(R/rr['path'])==rr['sha256']
  for n,pin in {**iv['runtime_sources'],**iv['inherited_engineering_GPU_evidence']}.items():assert h(R/n)==pin
  for rr in oldready['component_reviews'].values():rv=checkref(rr);assert rv['status']=='passed_CPU_review' and not rv['blockers']
  indref=cp(sh['candidate']['path'],sh['canonical_path'],sh['candidate']['sha256'])
  now=datetime.now(timezone.utc).isoformat()
  fields=dict(execution_version=g.OUTER_VERSION,production_chain_complete=True,production_chain_complete_meaning='Exact development pre-execution control/source and consumer closure only; actual new GPU execution is not claimed.',actual_GPU_runtime_chain_verified=False,scientific_trials_completed_by_new_runtime=0,runtime_sources=action['files'],scientific_plan=sh['scientific_plan'],effective_plan=sh['effective_plan'],action_execution_contract=sh['action_execution_contract'],plan_sha256=sh['plan_sha256'],method_ids=sh['method_ids'],allowed_stages=['development'],allowed_suite='libero_10',scientific_settings_changed=False,O2A_enabled=False,global_freeze_enabled=False,final_evaluation_enabled=False,expected_trials=200,unique_development_initial_states=100,prior_job_ids=[],old_Long600_preserved=True,old_Long_GPU_seconds_retained_once=10531)
  rootref=write(dd+'/plan_root_review.json',dict(schema='formal_main_v2',kind='formal_action_development_plan_root_review',status='passed',reviewed_by='root',utc=now,independent_review=indref,author_review=ref(ar),root_explicit_all_plan_fields_and_methodIDs_checked=True,inherited_GPU_engineering=iv['inherited_engineering_GPU_evidence'],positive_full_outer_wrapper_verification_required=True,**fields))
  pubs={**{rr['path']:rr['sha256'] for rr in oldready['component_reviews'].values()},rootref['path']:rootref['sha256'],indref['path']:indref['sha256'],sh['effective_plan']['path']:sh['effective_plan']['sha256'],sh['scientific_plan']['path']:sh['scientific_plan']['sha256'],sh['action_execution_contract']['path']:sh['action_execution_contract']['sha256']}
  ready=dict(schema='formal_main_v2',kind='formal_action_runtime_readiness',status='passed',reviewed_by='root',utc=now,active=False,activation_meaning='Prepared and reviewed only; no slot reservation activated and no invocation registered.',raw_consumer_ready=True,root_review=rootref,independent_review=indref,component_reviews=oldready['component_reviews'],support_files=eff['invocation']['support_files'],runtime_publication_files=pubs,forbidden_stages=['collect','full','components','global_freeze','final'],**fields)
  rr=write(dd+'/runtime_readiness.json',ready)
  prepared={**eff['invocation'],'registered_utc':now,'plan_sha256':eff['plan_sha256'],'runtime_readiness':rr}
  pr=write(dd+'/prepared_invocation.json',prepared)
  auth=copy.deepcopy(oldauth)
  auth.update(plan=sh['effective_plan'],scientific_plan=sh['scientific_plan'],prepared_invocation=pr,runtime_readiness=rr,approved_utc=now,plan_arguments=checkref(byargs[pair]['plan_arguments']))
  auth.pop('root_reservation')
  reservation=dict(schema='formal_main_v2',kind='root_downstream_GPU_slot_reservation',status='approved_for_exact_downstream_request',reviewed_by='root',approved_utc=now,controller_job_id='3034538',reserved_slots=1,capacity_limit_all_GPU_modes=8,automatic_retry=False,stage_key=eff['invocation']['stage_key'],plan=sh['effective_plan'],authorization_path=dd+'/submission_authorization.json',authorization_intent_sha256=g.intent_sha(auth),scope='Only this fresh Long A/B development shard. Not active until root explicitly binds this record in shared supervisor state.',old_CUDA_reservation_must_not_be_reused=True)
  rv=write(dd+'/reservation_root_record.json',reservation);auth['root_reservation']=rv
  authref=write(dd+'/submission_authorization.json',auth)
  a,e,plan,inner,inv=g.validate_authorization(R,authref)
  # Explicit pair identity binding is stronger than the minimal nested receipt schema.
  for gate in [checkref(ready['root_review']),checkref(ready['independent_review'])]:
   for k in ['scientific_plan','effective_plan','action_execution_contract','plan_sha256','method_ids']:assert gate[k]==sh[k]
  bundle=g.FrozenPlan(R,a,e,plan,inner,inv).prepare(state)
  bundle['readiness_files']={**pubs,rr['path']:rr['sha256']}
  io=g.NativeIO(R);pre=io.preflight(bundle);_,publish=io._watch(bundle)
  published=[]
  for n,pin in publish.items():
   if not (P/n).exists():published.append(n)
   cp(n,n,pin,base=P)
  actual=io._inputs(bundle,False);assert actual['missing_publications']==[]
  checked=wrapper.verify(inv,project=P)
  assert checked['effective_plan']==eff and checked['original_plan']==science and checked['execution_contract']==action
  e.unchanged();assert h(R/g.STATE)==state_sha
  check=write(dd+'/root_pre_execution_check.json',dict(schema='formal_main_v2',kind='root_actual_P_wrapper_readonly_verification',status='passed_actual_unchanged_P_wrapper_verify_and_NativeIO',utc=datetime.now(timezone.utc).isoformat(),pair=pair,authorization=authref,readiness=rr,reservation=rv,prepared_invocation=pr,root_review=rootref,independent_review=indref,scientific_plan=sh['scientific_plan'],effective_plan=sh['effective_plan'],action_execution_contract=sh['action_execution_contract'],plan_sha256=sh['plan_sha256'],method_ids=sh['method_ids'],runtime_files_checked=len(actual['checked_files']),published_metadata_files=published,full_P_wrapper_verify=True,real_full_registry_scientific_reconstruction=True,state_sha256=state_sha,state_unchanged=True,live_capacity_not_queried=True,reservation_not_activated=True,actual_GPU_runtime_chain_verified=False,model_not_loaded=True,new_trials=0,new_GPU_submissions=[]))
  checks.append(dict(pair=pair,authorization=authref,readiness=rr,reservation=rv,prepared_invocation=pr,root_check=check,independent_review=indref,methods=sh['method_ids']))
 assert h(R/g.STATE)==state_sha
 receipt=write(B+'/Long_runtime_readiness_root_index.json',dict(schema='formal_main_v2',status='passed_8_exact_development_pre_execution_checks_pending_live_capacity',utc=datetime.now(timezone.utc).isoformat(),shards=checks,author_CPU_checks=42,independent_checks=39,actual_full_P_wrapper_verifications=8,all_8_original_scientific_plans_rebuilt_from_full_registry=True,state_sha256=state_sha,state_unchanged=True,reservation_unchanged=True,Spatial_CUDA_reservation_preserved=True,new_GPU_submissions=[],new_trials=0,actual_GPU_runtime_chain_verified=False,final_release=False,elapsed_seconds=time.perf_counter()-began))
 print(json.dumps(dict(receipt=receipt,readiness=8,actual_P_wrapper_pass=8,new_GPU=0,state_unchanged=True)),flush=True)

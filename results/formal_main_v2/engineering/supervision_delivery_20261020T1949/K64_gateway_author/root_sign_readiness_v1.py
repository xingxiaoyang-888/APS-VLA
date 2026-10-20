"""ROOT-ONLY DRAFT: exact per-pair metadata/readiness, no submission or state write.
Source creation/CPU compilation is not root approval or real runtime readiness.
"""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import argparse,copy,hashlib,importlib.util,json,re,sys,time
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261021T0349'
G='scripts/ops/formal_action_deployment_posttraining_k64s23_v1/gateway.py';GPIN='873d0145f8d3ed51e916f39e1e36cb0251d10777a6f98429621f526d37a2c7bb'
MAP={'path':'.local/k64_seed23_bridges_20261020T1949/static_plan_publication_candidate.json','sha256':'d447aebff71f88bea0f568def97a5106936a7c107062062e7386758f8d6a30ca'}
OLD_READY={'path':'results/formal_main_v2/execution/object256seed23_source_control_v1_20261020T1644/runtime_readiness.json','sha256':'cb9c34495e0170d17cb37858ce45b7302e1a1abfa27ea30abc927a02af22cb1c'}
WRAPPER='scripts/ops/formal_action_deployment_v1/wrapper.py';WRAPPER_SHA='d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33'
METHODS=['A64_seed23','B64_seed23']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p,pin,name):
 if sha(p)!=pin:raise ValueError('pinned source changed '+str(p))
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def main(argv=None):
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--suite',choices=['Spatial','Object'],required=True)
 for key in ('plan-independent-review','gateway-cpu-review'):
  ap.add_argument('--'+key,required=True);ap.add_argument('--'+key+'-sha256',required=True)
 ap.add_argument('--root-reviewed-source-sha256',required=True);ap.add_argument('--execute-root-readiness',action='store_true',required=True)
 a=ap.parse_args(argv)
 if not (a.execute_root_readiness and sha(Path(__file__))==a.root_reviewed_source_sha256 and Path.cwd().resolve()==R):raise ValueError('exact root-reviewed execution required')
 g=load(R/G,GPIN,'root_k64s23_completed_gateway');require=g.require;ev=g.Evidence(R)
 suite='libero_'+a.suite.lower();allowed=g.SCOPED_DEVELOPMENT_PLANS[suite];C=str(Path(allowed['path']).parent)
 def rr(key):return {'path':getattr(a,key),'sha256':getattr(a,key+'_sha256')}
 def ref(path):return {'path':path,'sha256':g.stable(g.no_links(R/g.relative(path)))['sha256']}
 allowed_write={C+'/'+name for name in ['plan_root_review.json','plan_independent_review.json','gateway_independent_CPU_review.json','runtime_readiness.json','prepared_invocation.json','reservation_root_record.json','submission_authorization.json','root_pre_execution_check.json']}
 rootreceipt=B+'/'+a.suite+'64s23_runtime_readiness_root.json';allowed_write.add(rootreceipt)
 def write(path,value):
  require(path in allowed_write,'bounded root metadata output only');g.record(R/g.relative(path),value);return ref(path)
 def exact_copy(reference,dst,base=R):
  g.relative(dst);g.relative(reference['path']);require(type(reference)is dict and set(reference)=={'path','sha256'} and re.fullmatch('[0-9a-f]{64}',str(reference['sha256'])),'copy needs exact ref')
  source=g.no_links(R/reference['path']);data=source.read_bytes();require(g.sha(data)==reference['sha256'],'copy source changed')
  target=g.no_links(base/dst)
  if base==R:require(dst in allowed_write,'R copy outside bounded outputs')
  else:require(base==P and dst.startswith(('scripts/','configs/','results/formal_main_v2/')) and not dst.startswith('results/formal_main_v2/invocations/'),'P metadata copy only')
  if target.exists():require(g.stable(target)['sha256']==reference['sha256'],'refuse changed destination')
  else:g.immutable(target,data)
  return {'path':dst,'sha256':reference['sha256']}
 mapping=ev.ref(MAP);pairs=[x for x in mapping['pairs'] if x['suite']==suite];require(len(pairs)==1 and mapping['kind']=='k64_seed23_exact_two_development_plans_CPU_candidate','two-pair static map required');pair=pairs[0]
 require(pair['methods']==METHODS and pair['effective_plan']=={k:allowed[k] for k in ('path','sha256')} and pair['scientific_plan']==allowed['scientific_plan'] and pair['plan_sha256']==allowed['plan_sha256'],'static map exact plan differs')
 expected={C+'/'+x for x in ['scientific_plan.json','effective_plan.json','execution_contract.json','plan_arguments.json','source_provenance.json']}
 require({x['path'] for x in pair['files']}==expected and len(pair['files'])==5,'exact five canonical static files')
 for row in pair['files']:ev.watch(row['path'],row['sha256'])
 control=load(R/allowed['control']['path'],allowed['control']['sha256'],'root_k64s23_pair_control');descriptor=control.descriptor();gateway_files=g.source_files(R)
 require(pair['source_control']==descriptor and descriptor['scope']=={'suite':suite,'tokens':64,'seed':23,'method_ids':METHODS,'stage':'development','trials':200},'exact source bridge scope')
 science=ev.ref(pair['scientific_plan']);effective=ev.ref(pair['effective_plan']);action_ref=effective['invocation']['action_execution_contract'];action=ev.ref(action_ref)
 args=ev.ref(next({'path':x['path'],'sha256':x['sha256']} for x in pair['files'] if x['path'].endswith('/plan_arguments.json')))
 control.scope_args(SimpleNamespace(**args));control.scope_invocation(science['invocation']);control.scope_invocation(effective['invocation'])
 indref=rr('plan_independent_review');ind=ev.ref(indref);cpuref=rr('gateway_cpu_review');cpu=ev.ref(cpuref)
 require(cpu.get('schema')=='formal_main_v2' and cpu.get('kind')=='formal_downstream_server_gateway_independent_CPU_review' and cpu.get('status')=='passed_CPU_review' and not cpu.get('blockers'),'typed independent gateway CPU receipt missing')
 require(all(cpu.get('files',{}).get(k)==v for k,v in gateway_files.items()),'new canonical gateway full merged source closure not independently covered')
 require(ind.get('schema')=='formal_main_v2' and ind.get('status')=='passed' and ind.get('execution_version')==g.OUTER_VERSION and ind.get('production_chain_complete') is True and ind.get('actual_GPU_runtime_chain_verified') is False and not ind.get('blockers'),'independent metadata/source plan proof absent')
 for key,value in [('scientific_plan',pair['scientific_plan']),('effective_plan',pair['effective_plan']),('action_execution_contract',action_ref),('plan_sha256',effective['plan_sha256']),('method_ids',METHODS),('runtime_sources',action['files']),('suite',suite),('allowed_stages',['development']),('prior_job_ids',[]),('resume',False),('explicit_source_control',descriptor)]:require(ind.get(key)==value,'independent exact plan differs: '+key)
 old=ev.ref(OLD_READY);require(set(old['component_reviews'])=={'runtime','wrapper','raw_consumer'},'inherited original component gates required')
 for r in old['component_reviews'].values():
  cv=ev.ref(r);require(cv.get('status')=='passed_CPU_review' and not cv.get('blockers'),'inherited component failed')
 c=g.load(R/g.CONTROLLER,g.CONTROLLER_SHA,'root_k64s23_controller');wrapper=g.load(P/WRAPPER,WRAPPER_SHA,'root_k64s23_actual_P_wrapper');started=time.monotonic()
 with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
  state_sha=sha(R/g.STATE);state=c.read_json(R/g.STATE);before=copy.deepcopy(state);require(sha(R/g.STATE)==state_sha,'state read drift')
  ctl=state['autonomous_training_v1'];require(state['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None,'pending reservation or hold requires root reconciliation')
  require(ctl['controller_job_id']=='3034538','exact original completed controller required')
  for path in allowed_write:require(not (R/path).exists(),'existing readiness output: reconcile; never re-enter '+path)
  require(not (R/effective['invocation_relative']).exists() and not (P/effective['invocation_relative']).exists() and not (P/effective['output_relative']).exists(),'existing invocation/output; no retry')
  for job in state['registered_jobs']:require(not(job.get('experiment')==g.ROUND and job.get('suite')==suite and job.get('mode')=='development' and set(job.get('method_ids',[]))&set(METHODS)),'existing overlapping attempt')
  canonical_ind=exact_copy(indref,C+'/plan_independent_review.json');canonical_cpu=exact_copy(cpuref,C+'/gateway_independent_CPU_review.json');now=datetime.now(timezone.utc).isoformat()
  fields=dict(execution_version=g.OUTER_VERSION,production_chain_complete=True,production_chain_complete_meaning='Exact metadata/source/consumer closure only, not a newly executed GPU chain',actual_GPU_runtime_chain_verified=False,scientific_trials_completed_by_new_runtime=0,runtime_sources=action['files'],scientific_plan=pair['scientific_plan'],effective_plan=pair['effective_plan'],action_execution_contract=action_ref,plan_sha256=effective['plan_sha256'],method_ids=METHODS,allowed_stages=['development'],allowed_suite=suite,scientific_settings_changed=False,O2A_enabled=False,global_freeze_enabled=False,final_evaluation_enabled=False,expected_trials=200,unique_development_initial_states=100,prior_job_ids=[],resume=False,historical_results_preserved=True,historical_trials_rerun=False,horizon=220 if suite=='libero_spatial' else 280,explicit_source_control=descriptor,all_pair_GPU_seconds=descriptor['all_pair_GPU_seconds'],retained_failed_GPU_seconds=descriptor['retained_failed_GPU_seconds'])
  rootref=write(C+'/plan_root_review.json',dict(schema=g.ROUND,kind='formal_action_development_plan_root_review',status='passed',reviewed_by='root',utc=now,independent_review=canonical_ind,root_explicit_all_plan_fields_and_methodIDs_checked=True,inherited_GPU_engineering=action['GPU_acceptance'],positive_full_outer_wrapper_verification_required=True,**fields))
  pubs={**{x['path']:x['sha256'] for x in old['component_reviews'].values()},rootref['path']:rootref['sha256'],canonical_ind['path']:canonical_ind['sha256'],pair['effective_plan']['path']:pair['effective_plan']['sha256'],pair['scientific_plan']['path']:pair['scientific_plan']['sha256'],action_ref['path']:action_ref['sha256']}
  ready=write(C+'/runtime_readiness.json',dict(schema=g.ROUND,kind='formal_action_runtime_readiness',status='passed',reviewed_by='root',utc=now,active=False,activation_meaning='Metadata reviewed only; no slot reserved or invocation registered',raw_consumer_ready=True,root_review=rootref,independent_review=canonical_ind,component_reviews=old['component_reviews'],support_files=effective['invocation']['support_files'],runtime_publication_files=pubs,forbidden_stages=['collect','full','components','global_freeze','final'],**fields))
  prepared={**effective['invocation'],'registered_utc':now,'plan_sha256':effective['plan_sha256'],'runtime_readiness':ready};preparedref=write(C+'/prepared_invocation.json',prepared)
  auth=dict(schema=g.ROUND,kind='formal_downstream_single_submission_authorization',version=g.VERSION,status='approved_for_exactly_one_registered_downstream_submission',reviewed_by='root',approved_utc=now,automatic_retry=False,maximum_attempts=1,excluded_nodes=['gpu4020'],control_root=str(R),runtime_root=str(P),controller={'path':g.CONTROLLER,'sha256':g.CONTROLLER_SHA},controller_activation=g.ACTIVATION,controller_job_id='3034538',planner={'path':g.PLANNER,'sha256':g.PLANNER_SHA},gap_review=g.GAP,final_release_authorized_by_gateway=False,plan=pair['effective_plan'],scientific_plan=pair['scientific_plan'],prepared_invocation=preparedref,runtime_readiness=ready,plan_arguments=args,gateway_files=gateway_files,independent_review=canonical_cpu,explicit_source_control=descriptor)
  reservation=write(C+'/reservation_root_record.json',dict(schema=g.ROUND,kind='root_downstream_GPU_slot_reservation',status='approved_for_exact_downstream_request',reviewed_by='root',approved_utc=now,controller_job_id='3034538',reserved_slots=1,capacity_limit_all_GPU_modes=8,automatic_retry=False,stage_key=effective['invocation']['stage_key'],plan=pair['effective_plan'],authorization_path=C+'/submission_authorization.json',authorization_intent_sha256=g.intent_sha(auth),scope='Only this exact first complete 200-trial development request; inactive until separately bound in shared state'))
  auth['root_reservation']=reservation;authref=write(C+'/submission_authorization.json',auth)
  aa,ee,plan,inner,inv=g.validate_authorization(R,authref);bundle=g.FrozenPlan(R,aa,ee,plan,inner,inv).prepare(state);bundle['readiness_files']={**pubs,ready['path']:ready['sha256']}
  io=g.NativeIO(R);io.preflight(bundle);_,publications=io._watch(bundle);new=[]
  for name,pin in publications.items():
   if not (P/name).exists():new.append(name)
   exact_copy({'path':name,'sha256':pin},name,base=P)
  actual=io._inputs(bundle,False);require(actual['missing_publications']==[],'actual P metadata incomplete')
  verified=wrapper.verify(inv,project=P);require(verified['effective_plan']==effective and verified['original_plan']==science and verified['execution_contract']==action,'actual original P wrapper differs')
  ee.unchanged();ev.unchanged();require(state==before and sha(R/g.STATE)==state_sha,'readiness changed live state')
  check=write(C+'/root_pre_execution_check.json',dict(schema=g.ROUND,kind='root_actual_P_wrapper_readonly_verification',status='passed_actual_unchanged_P_wrapper_verify_and_NativeIO',utc=datetime.now(timezone.utc).isoformat(),suite=suite,authorization=authref,readiness=ready,reservation=reservation,prepared_invocation=preparedref,root_review=rootref,independent_review=canonical_ind,scientific_plan=pair['scientific_plan'],effective_plan=pair['effective_plan'],action_execution_contract=action_ref,plan_sha256=effective['plan_sha256'],method_ids=METHODS,explicit_source_control=descriptor,runtime_files_checked=len(actual['checked_files']),published_metadata_files=new,full_P_wrapper_verify=True,real_full_registry_scientific_reconstruction=True,state_sha256=state_sha,state_unchanged=True,live_capacity_not_queried=True,reservation_not_activated=True,actual_GPU_runtime_chain_verified=False,model_not_loaded=True,new_trials=0,new_GPU_submissions=[]))
  receipt=write(rootreceipt,dict(schema=g.ROUND,kind='exact_k64s23_runtime_readiness_root',status='passed_exact_pre_execution_checks_pending_live_capacity',utc=datetime.now(timezone.utc).isoformat(),suite=suite,static_map=MAP,source_control=descriptor,independent_review=canonical_ind,gateway_CPU_review=canonical_cpu,root_check=check,authorization=authref,readiness=ready,reservation=reservation,prepared_invocation=preparedref,actual_full_P_wrapper_verifications=1,state_sha256=state_sha,state_unchanged=True,new_GPU_submissions=[],new_trials=0,actual_GPU_runtime_chain_verified=False,final_release=False,elapsed_seconds=time.monotonic()-started,root_script_sha256=sha(Path(__file__))))
  require(sha(R/g.STATE)==state_sha,'state changed at final receipt');print(json.dumps({'receipt':receipt,'actual_P_wrapper_pass':1,'new_GPU':0,'state_unchanged':True}))
if __name__=='__main__':main()

# Draft for ROOT only. Creation/compilation is not execution or readiness approval.
# No Slurm, state mutation, invocation publication, GPU loading, or automatic retry.
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,importlib.util,json,sys,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
C='results/formal_main_v2/execution/object256seed23_source_control_v1_20261020T1644'
B='results/formal_main_v2/preflight/heartbeat_20261021T0044'
CONTROL='scripts/ops/formal_object256s23_source_bridge_v1/control.py';CONTROL_SHA='09ae3486565e17bd2c41b09adbfaa7a6d99f38754d3e77071f77851c9ac54f6f'
BUNDLE_SHA='52368d3b96e72ec4deb601949a7133579327818a6a7e963ca4657892bb36dfad'
OLD='results/formal_main_v2/execution/long_remaining16_action_v1_1827/k64_seed41'
METHODS=['A256_seed23','B256_seed23'];sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
def require(ok,msg):
 if not ok:raise ValueError('Object23 root readiness draft: '+msg)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def path(rel,base=R):
 require(type(rel) is str and not Path(rel).is_absolute() and '..' not in Path(rel).parts and Path(rel).as_posix()==rel,'canonical relative path required')
 p=base/rel;require(not any(x.is_symlink() for x in (p,*p.parents)),'no symlinks');return p
WATCH={}
def read_ref(rr):
 require(type(rr) is dict and set(rr)=={'path','sha256'} and type(rr['sha256']) is str and len(rr['sha256'])==64,'exact reference shape')
 p=path(rr['path']);require(h(p)==rr['sha256'],'source changed '+rr['path']);WATCH[rr['path']]=rr['sha256'];return json.loads(p.read_bytes())
def ref(rel):return {'path':rel,'sha256':h(path(rel))}
def unchanged():
 for rel,pin in WATCH.items():require(h(path(rel))==pin,'watched evidence changed: '+rel)
def write(rel,obj):
 require(rel.startswith(C+'/') or rel==B+'/Object_runtime_readiness_root.json','bounded output only')
 p=path(rel);p.parent.mkdir(parents=True,exist_ok=True);data=(json.dumps(obj,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+chr(10)).encode()
 with p.open('xb') as f:f.write(data)
 return ref(rel)
def cp(rr,dst,base=R):
 data=path(rr['path']).read_bytes();require(hashlib.sha256(data).hexdigest()==rr['sha256'],'copy source changed')
 out=path(dst,base);out.parent.mkdir(parents=True,exist_ok=True)
 if out.exists():require(h(out)==rr['sha256'],'refuse changed existing destination')
 else:
  with out.open('xb') as f:f.write(data)
 return {'path':dst,'sha256':rr['sha256']}
def load(rel,pin):
 p=path(rel);require(h(p)==pin,'pinned code changed');spec=importlib.util.spec_from_file_location('_Object23_root_'+p.stem,p);mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod

def main(argv=None):
 ap=argparse.ArgumentParser(description=__doc__)
 for key in ['bundle','independent-plan-review','gateway-cpu-review','author-canonical-review']:
  ap.add_argument('--'+key,required=True);ap.add_argument('--'+key+'-sha256',required=True)
 ap.add_argument('--root-reviewed-source-sha256',required=True);ap.add_argument('--execute-root-readiness',action='store_true',required=True)
 a=ap.parse_args(argv);require(a.execute_root_readiness and h(Path(__file__))==a.root_reviewed_source_sha256,'explicit root source approval required')
 require(Path.cwd().resolve()==R,'must execute in server control R')
 rr=lambda key:{'path':getattr(a,key),'sha256':getattr(a,key+'_sha256')}
 bundle_ref=rr('bundle');require(bundle_ref['sha256']==BUNDLE_SHA,'unexpected static bundle')
 bundle=read_ref(bundle_ref);control=load(CONTROL,CONTROL_SHA);descriptor=control.descriptor();closure=control.closure()
 require(bundle['kind']=='object256s23_canonical_static_plan_candidates' and bundle['canonical_directory']==C and bundle['explicit_source_control']==descriptor and bundle['gateway_files']==closure,'bundle scope or canonical source differs')
 require(bundle['suite']=='libero_object' and bundle['budget']==256 and bundle['seed']==23 and bundle['method_ids']==METHODS and bundle['stage']=='development' and bundle['expected_trials']==200,'exact Object256s23 full development required')
 require(bundle['all_pair_GPU_seconds']==58917 and bundle['failed_GPU_seconds_retained']==84,'full failure cost required')
 require(len(bundle['canonical_files'])==4 and {x['destination'] for x in bundle['canonical_files']}=={C+'/'+x for x in ['scientific_plan.json','execution_contract.json','plan_arguments.json','effective_plan.json']},'exact static publication list')
 for row in bundle['canonical_files']:
  require(h(path(row['destination']))==row['sha256'],'canonical plan not yet published exactly');WATCH[row['destination']]=row['sha256']
 science=read_ref(bundle['scientific_plan']);effective=read_ref(bundle['effective_plan']);action=read_ref(bundle['execution_contract']);args=read_ref(bundle['plan_arguments'])
 control.scope_args(__import__('types').SimpleNamespace(**args));control.scope_invocation(science['invocation']);control.scope_invocation(effective['invocation'])
 require(effective['plan_sha256']==bundle['plan_sha256'],'effective plan identity differs')
 author_ref=rr('author_canonical_review');require(author_ref['sha256']==bundle['author_canonical_report']['sha256'],'author canonical report identity differs');author=read_ref(author_ref)
 require(author['status']=='passed_canonical_CPU_source_chain_only' and author['production_path_published'] is True and author['source_control']==descriptor and author['actual_FrozenPlan_rebuild'] is True and author['actual_terminal_science_context_rebuild'] is True and author['GPU_runs']==0,'canonical author source proof absent')
 ind_candidate=rr('independent_plan_review');iv=read_ref(ind_candidate);cpu_candidate=rr('gateway_cpu_review');cpu=read_ref(cpu_candidate)
 require(cpu.get('schema')=='formal_main_v2' and cpu.get('kind')=='formal_downstream_server_gateway_independent_CPU_review' and cpu.get('status')=='passed_CPU_review' and not cpu.get('blockers'),'typed independent gateway CPU receipt required')
 require(all(cpu.get('files',{}).get(n)==pin for n,pin in closure.items()),'CPU independent source closure differs')
 require(cpu.get('explicit_source_control')==descriptor,'gateway CPU proof not canonical explicit bridge')
 require(iv.get('schema')=='formal_main_v2' and iv.get('status')=='passed' and iv.get('execution_version')=='formal-downstream-action-v1' and iv.get('production_chain_complete') is True and iv.get('actual_GPU_runtime_chain_verified') is False,'independent metadata/source closure required, not GPU claims')
 for key,value in [('scientific_plan',bundle['scientific_plan']),('effective_plan',bundle['effective_plan']),('action_execution_contract',bundle['execution_contract']),('plan_sha256',effective['plan_sha256']),('method_ids',METHODS),('runtime_sources',action['files']),('suite','libero_object'),('allowed_stages',['development']),('prior_job_ids',[]),('resume',False),('explicit_source_control',descriptor)]:require(iv.get(key)==value,'independent plan differs: '+key)
 g=control.gateway_module();controller=g.load(R/g.CONTROLLER,g.CONTROLLER_SHA,'_Object23_root_original_controller')
 wrapper=g.load(P/'scripts/ops/formal_action_deployment_v1/wrapper.py','d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33','_Object23_actual_P_wrapper')
 oldready=read_ref(ref(OLD+'/runtime_readiness.json'));oldauth=read_ref(ref(OLD+'/submission_authorization.json'))
 require(set(oldready['component_reviews'])=={'runtime','wrapper','raw_consumer'},'original component gates required')
 for rr0 in oldready['component_reviews'].values():
  cv=read_ref(rr0);require(cv.get('status')=='passed_CPU_review' and not cv.get('blockers'),'inherited component failure')
 started=time.perf_counter()
 with controller.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
  state_sha=h(R/g.STATE);state=controller.read_json(R/g.STATE);before=copy.deepcopy(state);require(h(R/g.STATE)==state_sha,'state drift during read')
  require(state['pending_submission'] is None and state['autonomous_training_v1']['reserved_GPU_slots']==0 and state['autonomous_training_v1']['root_submission_hold'] is None,'unresolved root submission/reservation')
  require(state['autonomous_training_v1']['controller_job_id']==oldauth['controller_job_id'],'controller identity changed; root reassessment required')
  for name in ['plan_root_review.json','plan_independent_review.json','gateway_independent_CPU_review.json','runtime_readiness.json','prepared_invocation.json','reservation_root_record.json','submission_authorization.json','root_pre_execution_check.json']:
   require(not path(C+'/'+name).exists(),'existing root readiness artifact; reconcile, do not re-enter')
  require(not path(B+'/Object_runtime_readiness_root.json').exists(),'root receipt already exists')
  require(not (R/science['invocation_relative']).exists() and not (P/science['invocation_relative']).exists() and not Path(science['invocation']['run_root']).exists(),'already invoked/output exists; no retry')
  for job in state['registered_jobs']:
   require(not (job.get('experiment')=='formal_main_v2' and job.get('suite')=='libero_object' and job.get('mode')=='development' and bool(set(job.get('method_ids',[]))&set(METHODS))),'existing overlapping development attempt')
  indref=cp(ind_candidate,C+'/plan_independent_review.json');cpuref=cp(cpu_candidate,C+'/gateway_independent_CPU_review.json');now=datetime.now(timezone.utc).isoformat()
  fields=dict(execution_version=g.OUTER_VERSION,production_chain_complete=True,production_chain_complete_meaning='Exact pre-execution metadata/source/consumer closure only; not a newly executed GPU chain.',actual_GPU_runtime_chain_verified=False,scientific_trials_completed_by_new_runtime=0,runtime_sources=action['files'],scientific_plan=bundle['scientific_plan'],effective_plan=bundle['effective_plan'],action_execution_contract=bundle['execution_contract'],plan_sha256=effective['plan_sha256'],method_ids=METHODS,allowed_stages=['development'],allowed_suite='libero_object',scientific_settings_changed=False,O2A_enabled=False,global_freeze_enabled=False,final_evaluation_enabled=False,expected_trials=200,unique_development_initial_states=100,prior_job_ids=[],resume=False,historical_results_preserved=True,historical_trials_rerun=False,horizon=280,explicit_source_control=descriptor,all_pair_GPU_seconds=58917,retained_failed_GPU_seconds=84)
  rootref=write(C+'/plan_root_review.json',dict(schema='formal_main_v2',kind='formal_action_development_plan_root_review',status='passed',reviewed_by='root',utc=now,independent_review=indref,author_review=author_ref,root_explicit_all_plan_fields_and_methodIDs_checked=True,inherited_GPU_engineering=action['GPU_acceptance'],positive_full_outer_wrapper_verification_required=True,**fields))
  pubs={**{v['path']:v['sha256'] for v in oldready['component_reviews'].values()},rootref['path']:rootref['sha256'],indref['path']:indref['sha256'],bundle['effective_plan']['path']:bundle['effective_plan']['sha256'],bundle['scientific_plan']['path']:bundle['scientific_plan']['sha256'],bundle['execution_contract']['path']:bundle['execution_contract']['sha256']}
  ready=dict(schema='formal_main_v2',kind='formal_action_runtime_readiness',status='passed',reviewed_by='root',utc=now,active=False,activation_meaning='Metadata reviewed only; no slot reserved and no invocation registered.',raw_consumer_ready=True,root_review=rootref,independent_review=indref,component_reviews=oldready['component_reviews'],support_files=effective['invocation']['support_files'],runtime_publication_files=pubs,forbidden_stages=['collect','full','components','global_freeze','final'],**fields)
  readyref=write(C+'/runtime_readiness.json',ready);prepared={**effective['invocation'],'registered_utc':now,'plan_sha256':effective['plan_sha256'],'runtime_readiness':readyref};preparedref=write(C+'/prepared_invocation.json',prepared)
  auth=copy.deepcopy(oldauth);auth.update(plan=bundle['effective_plan'],scientific_plan=bundle['scientific_plan'],prepared_invocation=preparedref,runtime_readiness=readyref,approved_utc=now,plan_arguments=args,gateway_files=closure,independent_review=cpuref,explicit_source_control=descriptor);auth.pop('root_reservation')
  reservation=dict(schema='formal_main_v2',kind='root_downstream_GPU_slot_reservation',status='approved_for_exact_downstream_request',reviewed_by='root',approved_utc=now,controller_job_id=auth['controller_job_id'],reserved_slots=1,capacity_limit_all_GPU_modes=8,automatic_retry=False,stage_key=effective['invocation']['stage_key'],plan=bundle['effective_plan'],authorization_path=C+'/submission_authorization.json',authorization_intent_sha256=g.intent_sha(auth),scope='Only exact unrun Object256s23 A/B200 development. Inactive until root separately binds shared state.')
  reservationref=write(C+'/reservation_root_record.json',reservation);auth['root_reservation']=reservationref;authref=write(C+'/submission_authorization.json',auth)
  aa,ee,plan,inner,inv=g.validate_authorization(R,authref);runtime_bundle=g.FrozenPlan(R,aa,ee,plan,inner,inv).prepare(state);runtime_bundle['readiness_files']={**pubs,readyref['path']:readyref['sha256']}
  io=g.NativeIO(R);io.preflight(runtime_bundle);_,publications=io._watch(runtime_bundle);new_publications=[]
  for name,pin in publications.items():
   if not (P/name).exists():new_publications.append(name)
   cp({'path':name,'sha256':pin},name,base=P)
  actual=io._inputs(runtime_bundle,False);require(actual['missing_publications']==[],'P metadata incomplete')
  verified=wrapper.verify(inv,project=P);require(verified['effective_plan']==effective and verified['original_plan']==science and verified['execution_contract']==action,'actual original P wrapper disagreement')
  ee.unchanged();unchanged();require(state==before and h(R/g.STATE)==state_sha,'root state changed during readonly readiness')
  check=write(C+'/root_pre_execution_check.json',dict(schema='formal_main_v2',kind='root_actual_P_wrapper_readonly_verification',status='passed_actual_unchanged_P_wrapper_verify_and_NativeIO',utc=datetime.now(timezone.utc).isoformat(),suite='libero_object',authorization=authref,readiness=readyref,reservation=reservationref,prepared_invocation=preparedref,root_review=rootref,independent_review=indref,scientific_plan=bundle['scientific_plan'],effective_plan=bundle['effective_plan'],action_execution_contract=bundle['execution_contract'],plan_sha256=effective['plan_sha256'],method_ids=METHODS,explicit_source_control=descriptor,runtime_files_checked=len(actual['checked_files']),published_metadata_files=new_publications,full_P_wrapper_verify=True,real_full_registry_scientific_reconstruction=True,state_sha256=state_sha,state_unchanged=True,live_capacity_not_queried=True,reservation_not_activated=True,actual_GPU_runtime_chain_verified=False,model_not_loaded=True,new_trials=0,new_GPU_submissions=[]))
  receipt=write(B+'/Object_runtime_readiness_root.json',dict(schema='formal_main_v2',status='passed_exact_Object256s23_pre_execution_checks_pending_live_capacity',utc=datetime.now(timezone.utc).isoformat(),bundle=bundle_ref,source_control=descriptor,author_review=author_ref,independent_review=indref,gateway_CPU_review=cpuref,root_check=check,authorization=authref,readiness=readyref,reservation=reservationref,prepared_invocation=preparedref,actual_full_P_wrapper_verifications=1,state_sha256=state_sha,state_unchanged=True,new_GPU_submissions=[],new_trials=0,actual_GPU_runtime_chain_verified=False,final_release=False,elapsed_seconds=time.perf_counter()-started,root_script_sha256=h(Path(__file__))))
  require(h(R/g.STATE)==state_sha,'state changed at receipt');print(json.dumps({'receipt':receipt,'readiness':1,'actual_P_wrapper_pass':1,'new_GPU':0,'state_unchanged':True}),flush=True)
if __name__=='__main__':main()

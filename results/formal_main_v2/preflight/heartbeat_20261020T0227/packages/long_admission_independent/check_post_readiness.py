from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,importlib.util,traceback
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=R/'.local/long_action_admission_audit_1827'
refs={};checks=[];rows=[]
def watch(p,pin=None):
 p=Path(p);p=p if p.is_absolute() else R/p
 assert p.is_relative_to(R) or p.is_relative_to(P)
 assert not any('sealed' in q.lower() for q in p.parts) and not set(p.suffixes)&{'.pt','.pth','.bin','.safetensors','.ckpt','.init','.pruned_init'}
 a=p.stat();b=p.read_bytes();z=p.stat();assert (a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
 h=hashlib.sha256(b).hexdigest();assert pin is None or h==pin,(str(p),h,pin);refs[str(p)]={'sha256':h,'bytes':len(b)};return b

def read(p,pin=None):return json.loads(watch(p,pin))
def exact(ref,base=R):return read(base/ref['path'],ref['sha256'])
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n

def load(p,pin,name):
 p=Path(p);b=watch(p,pin);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;exec(compile(b,str(p),'exec'),m.__dict__);return m

def save(name,value):
 with (D/name).open('x') as f:json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
try:
 first=read(D/'eight_plan_actual_closure.json','55224ff043f7420793ec32982d389cfbbd20ac76ab9d454dd91122b2af5bad64')
 indexref={'path':'results/formal_main_v2/preflight/heartbeat_20261020T0227/Long_runtime_readiness_root_index.json','sha256':'aa3319a5d3f2cf5f1c34d0ed272feae84cbaf7cfda4a6cb7d3cc88cb97c34c53'}
 ix=exact(indexref);byplan={x['pair']:x for x in first['plans']}
 watch('.local/sign_Long_readiness_1827.py','45e0eb8b400918eb1eda899429674c558521777892ad55f13ba8f466fae9618b')
 files=first['runtime_sources'];g=load(R/'scripts/ops/formal_action_deployment_v1/gateway.py',files['scripts/ops/formal_action_deployment_v1/gateway.py'],'actual1827post_gateway')
 w=load(P/'scripts/ops/formal_action_deployment_v1/wrapper.py',files['scripts/ops/formal_action_deployment_v1/wrapper.py'],'actual1827post_P_wrapper')
 ck('eight_exact_root_checks',len(ix['shards'])==8 and {x['pair'] for x in ix['shards']}==set(byplan))
 ck('root_evidence_boundary',ix['actual_full_P_wrapper_verifications']==8 and ix['all_8_original_scientific_plans_rebuilt_from_full_registry'] is True and ix['state_unchanged'] is True and ix['reservation_unchanged'] is True and ix['Spatial_CUDA_reservation_preserved'] is True and ix['actual_GPU_runtime_chain_verified'] is False and ix['new_GPU_submissions']==[] and ix['new_trials']==0 and ix['final_release'] is False)
 for sh in ix['shards']:
  pair=sh['pair'];base=byplan[pair];rc=exact(sh['root_check']);ready=exact(sh['readiness']);exact(sh['readiness'],P)
  rootref=ready['root_review'];indref=ready['independent_review'];root=exact(rootref);ind=exact(indref);exact(rootref,P);exact(indref,P)
  ck(pair+'_distinct_root_and_independent',rootref!=indref and sh['independent_review']==indref)
  for role,doc in [('root',root),('independent',ind),('readiness',ready),('root_execution_check',rc)]:
   for key in ['scientific_plan','effective_plan','action_execution_contract','plan_sha256','method_ids']:ck(pair+'_'+role+'_'+key,doc[key]==base[key])
  science=exact(base['scientific_plan']);eff=exact(base['effective_plan']);action=exact(base['action_execution_contract'])
  ck(pair+'_reviewed_exact_runtime_and_CPU_boundary',all(d['runtime_sources']==action['files'] and d['execution_version']=='formal-downstream-action-v1' and d['production_chain_complete'] is True and d['actual_GPU_runtime_chain_verified'] is False for d in [root,ind,ready]))
  ck(pair+'_readiness_not_activated_development_only',ready['active'] is False and ready['allowed_stages']==['development'] and ready['O2A_enabled'] is False and ready['global_freeze_enabled'] is False and ready['final_evaluation_enabled'] is False and ready['scientific_settings_changed'] is False)
  ck(pair+'_root_actual_execution_claims_only_preflight',rc['full_P_wrapper_verify'] is True and rc['real_full_registry_scientific_reconstruction'] is True and rc['state_unchanged'] is True and rc['live_capacity_not_queried'] is True and rc['reservation_not_activated'] is True and rc['actual_GPU_runtime_chain_verified'] is False and rc['model_not_loaded'] is True and rc['new_trials']==0 and rc['new_GPU_submissions']==[])
  # Actual production pure admission validation, with genuine root metadata.
  a,e,plan,inner,inv=g.validate_authorization(R,sh['authorization'])
  ck(pair+'_actual_validate_authorization_same_bound_inputs',plan==eff and inner==science and inv==exact(sh['prepared_invocation']) and a['prepared_invocation']==sh['prepared_invocation'] and a['runtime_readiness']==sh['readiness'] and a['root_reservation']==sh['reservation'])
  for n,h in e.hashes.items():watch(R/n,h)
  ck(pair+'_fresh_prepared_invocation',inv['resume'] is False and inv['prior_review'] is None and inv['prior_job_ids']==[] and inv['repair_record'] is None and action['transition'] is None)
  for n,h in ready['runtime_publication_files'].items():watch(R/n,h);watch(P/n,h)
  must={base['effective_plan']['path']:base['effective_plan']['sha256'],base['scientific_plan']['path']:base['scientific_plan']['sha256'],base['action_execution_contract']['path']:base['action_execution_contract']['sha256'],rootref['path']:rootref['sha256'],indref['path']:indref['sha256']}
  ck(pair+'_explicit_all_wrapper_read_ref_publications',all(ready['runtime_publication_files'].get(n)==h for n,h in must.items()))
  bundle={'plan':plan,'invocation':inv,'prefix':{},'readiness_files':{**ready['runtime_publication_files'],sh['readiness']['path']:sh['readiness']['sha256']}}
  actual=g.NativeIO(R).preflight(bundle)
  ck(pair+'_independent_actual_NativeIO_full_readiness',actual['missing_publications']==[] and actual['output_exists'] is False)
  for p,row in actual['checked_files'].items():watch(p,row['sha256'])
  result=w.verify(inv,project=P)
  ck(pair+'_independent_actual_new_P_wrapper_verify',result['effective_plan']==eff and result['original_plan']==science and result['execution_contract']==action)
  ck(pair+'_canonical_invocation_absent_R_P',not (R/plan['invocation_relative']).exists() and not (P/plan['invocation_relative']).exists())
  e.unchanged()
  rows.append({'pair':pair,'root_check':sh['root_check'],'root_review':rootref,'independent_review':indref,'readiness':sh['readiness'],'authorization':sh['authorization'],'reservation':sh['reservation'],'prepared_invocation':sh['prepared_invocation'],'scientific_plan':base['scientific_plan'],'effective_plan':base['effective_plan'],'action_execution_contract':base['action_execution_contract'],'plan_sha256':base['plan_sha256'],'method_ids':base['method_ids'],'stage_key':base['stage_key'],'invocation_relative':base['invocation_relative'],'actual_validate_authorization_passed':True,'actual_full_P_wrapper_verify_passed':True,'actual_NativeIO_preflight':actual,'runtime_publication_files':ready['runtime_publication_files'],'actual_GPU_runtime_chain_verified':False,'scientific_trials_completed_by_new_runtime':0})
 # One read-only observation, not a scheduler or capacity assessment.
 statepath=R/'results/experiment_supervisor/state.json';raw=statepath.read_bytes();state=json.loads(raw);auto=state['autonomous_training_v1'];reservation={'path':'results/formal_main_v2/preflight/cuda_single_recovery_3028522_slot_reservation_1940.json','sha256':'0aabce41556248f83877ce47a102ebb32817624eac4ad04a431862b098289c9d'}
 ck('observed_Spatial_CUDA_priority_reservation_unchanged',auto['reserved_GPU_slots']==1 and auto['reservation_root_record']==reservation)
 keys={x['stage_key'] for x in rows};invocations={x['invocation_relative'] for x in rows}
 matches=[j for j in state['registered_jobs'] if j.get('stage_key') in keys or j.get('invocation') in invocations]
 ck('eight_new_stages_not_registered',matches==[])
 ck('no_new_plan_pending_submission',state['pending_submission'] is None or state['pending_submission'].get('stage_key') not in keys)
 stateobs={'utc':datetime.now(timezone.utc).isoformat(),'state_sha256':hashlib.sha256(raw).hexdigest(),'registered_job_count':len(state['registered_jobs']),'new_stage_matches':matches,'pending_submission':state['pending_submission'],'controller_job_id':auto['controller_job_id'],'reserved_GPU_slots':auto['reserved_GPU_slots'],'reservation_root_record':auto['reservation_root_record'],'live_scheduler_queried':False}
 for p,row in list(refs.items()):watch(p,row['sha256'])
 report={'schema':'formal_main_v2','kind':'Long16_action_per_plan_post_readiness_independent_admission_audit','status':'passed_exact_pre_execution_control_and_source_closure_only','utc':datetime.now(timezone.utc).isoformat(),'root_readiness_index':indexref,'pre_readiness_audit':{'path':str((D/'eight_plan_actual_closure.json').relative_to(R)),'sha256':'55224ff043f7420793ec32982d389cfbbd20ac76ab9d454dd91122b2af5bad64'},'runtime_sources':files,'plans':rows,'checks':checks,'evidence_refs':refs,'state_observation':stateobs,'actual_new_P_wrapper_verifications':8,'actual_validate_authorization_checks':8,'actual_full_NativeIO_checks':8,'new_original_planner_reconstructions_by_this_post_audit':0,'root_original_planner_reconstructions_verified_from_exact_receipts':8,'production_chain_complete':True,'production_chain_complete_meaning':'Exact eight-development-plan pre-execution control/source/publication closure verified. This field does not claim completed actual GPU runtime, actual action results, success rate, latency, equivalence or scientific release.','actual_GPU_runtime_chain_verified':False,'scientific_trials_completed_by_new_runtime':0,'submission_performed':False,'GPU_or_Slurm_calls':0,'state_P_Git_or_canonical_written':False,'models_or_weight_values_read':False,'sealed_values_read':False,'O2A_or_global_freeze_or_final_release':False,'remaining_conditions':['Actual submission must refresh all registered Slurm evidence/capacity and acquire an exact plan-specific owned reservation under the shared writer lock; existing Spatial CUDA reservation remains first.','No invocation has been registered or published, no reservation activated and no new stage submitted by this audit. Genuine unconsumed root authorizations are metadata preparation only.','A successful new scientific GPU run still needs raw runtime/source/action/trial/cost review; inherited 16-cell v4 engineering evidence cannot stand in for its performance.','Old Long/Spatial/Object legacy action data remain historical; these fresh plans do not establish old/new semantic equivalence. Whole-ancestry consumer, O2A and global/final release gates remain closed.']}
 save('post_readiness_independent_review.json',report)
 print(json.dumps({'status':report['status'],'plans':len(rows),'checks':len(checks),'refs':len(refs),'actual_new_wrapper_P_passes':8,'GPU':0,'pending_new_trials':1600,'Spatial_CUDA_reservation_preserved':True},ensure_ascii=False))
except BaseException as exc:
 save('post_readiness_failure_a1.json',{'exception':repr(exc),'traceback':traceback.format_exc(),'checks':checks,'plans':rows,'evidence_refs':refs});raise

"""Read-only independent actual canonical Spatial588 integration verification.
Writes are confined to this private audit directory; no scheduler, state,
canonical or P mutation, and no production authorization is created.
"""
from pathlib import Path
from types import ModuleType,SimpleNamespace
from datetime import datetime,timezone
import copy,hashlib,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/spatial_gateway_independent_20261020T2253'
checks=[];read={}
def h(b):return hashlib.sha256(b).hexdigest()
def data(rel,pin=None):
 p=R/rel;assert p.resolve()==p and not p.is_symlink()
 raw=p.read_bytes();digest=h(raw);assert pin is None or digest==pin
 read[rel]={'sha256':digest,'bytes':len(raw)}
 return raw
def j(rel,pin=None):return json.loads(data(rel,pin))
def ok(name,v):
 assert v,name
 checks.append({'name':name,'passed':True})
def mod(rel,pin,name):
 raw=data(rel,pin);m=ModuleType(name);m.__file__=str(R/rel);m.__package__='';sys.modules[name]=m
 exec(compile(raw,str(R/rel),'exec',dont_inherit=True),m.__dict__);return m
def save(name,obj):
 p=D/name;assert D in p.parents and p.resolve()==p
 with p.open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
 return {'path':p.relative_to(R).as_posix(),'sha256':h(p.read_bytes())}
try:
 receipt_ref={'path':'results/formal_main_v2/preflight/heartbeat_20261021T0653/Spatial_canonical_install.json','sha256':'f5e269bcf3c5d8375ee8c1b482b13b703dd6f70da7a4a26508e167c307a2d90d'}
 root=j(**{'rel':receipt_ref['path'],'pin':receipt_ref['sha256']})
 mapping=j('.local/spatial588_integration_20261020T2156/phase2_v2/install_files.json','60fb788f3f8f13ee9b1f24b5312c435f48d22fa2668ac736649f24f202defb85')
 indref=root['independent_history']
 hist=j(indref['path'],'db89d100fdc77f3ea7185ca8ffb1d20cbce333a88b627f8d477618f1924f6cc9')
 own=j('.local/spatial_gateway_independent_20261020T2253/independent_review.json','e488430128bfbecc1e3ca846764dd6620ebea405d90ffb06063b1d09bdce69b2')
 ok('prior CPU review is independent and not production',own['status']=='passed_CPU_review' and own['production_admission'] is False and own['check_count']==242)
 ok('exact 13 canonical source mapping',len(mapping['files'])==13 and len(root['canonical_files'])==13)
 for row in mapping['files']:
  src=data(row['source'],row['sha256']);dst=data(row['destination'],row['sha256'])
  ok('actual R source byte identity '+row['destination'],src==dst and len(dst)==row['bytes'])
 c=mod('scripts/ops/formal_spatial588_predispatch_v1/control.py','e2e7c3fe7f6dcf4f63b4550c3f5bc8ec50a05aaf462b38ed961ce356cc414683','spatial588_actual_canonical_independent')
 g=mod('.local/spatial588_integration_20261020T2156/phase3_gateway/gateway.py','aba5868a8dc4e480262177785b2e62123d014046624f37924248721a9575c99c','spatial588_gateway_actual_canonical_reader')
 bridge=c.compatibility_module();factory,planner=c.control_modules()
 actual_sources=c.closure()
 ok('actual canonical closure equals independently reviewed projection',actual_sources==hist['history_control_sources']==root['source_closure'])
 ok('actual typed history descriptor equals independent and root',c.descriptor()==hist['typed_predispatch_history']==root['typed_history'])
 ok('actual legacy descriptor equals original source scope',bridge.descriptor()==root['legacy12'])
 for rel,pin in actual_sources.items():data(rel,pin)
 statepath=R/'results/experiment_supervisor/state.json'
 state_raw=statepath.read_bytes();state=json.loads(state_raw)
 ok('no ambiguous pending at read snapshot',state['pending_submission'] is None)
 ev=factory.Evidence(R)
 real_history=c.verify_history(ev,planner.formal_jobs(state))
 real_prefix=bridge.audit_prefix(ev)
 ok('full real original consumer history reconstructed',real_history==c.descriptor() and real_prefix==bridge.descriptor())
 ok('12 legacy122chunks917actions preserved',bridge.proof()['counts']=={'trials':12,'chunks':122,'executed_actions':917})
 ok('393 executed plus2 no-child allocation retained exactly once',real_history['prior_GPU_seconds']==395 and real_history['predispatch_failure_GPU_seconds']==2 and real_history['all_prior_job_ids']==['3022743','3042529'] and real_history['executed_prior_job_ids']==['3022743'] and real_history['predispatch_failed_job_ids']==['3042529'])
 ar=root['root_adoption'];rr=root['root_repair'];pr=root['scientific_plan']
 adoption=j(ar['path'],'0fb9fb3dcddaa14c242593239f2638cc0030d73e7bee1792d1e3f0517f9478b3')
 repair=j(rr['path'],'b513730309129a576da70747861507e7a6dcd5b821e0dc617df69bceed7617e0')
 scientific=j(pr['path'],'b9d7404387a6896c3d7bb9ae0c55d3e132f16d6036e3c49f34ce489522bd37c2')
 ok('genuine root adoption separated from private proposal',adoption['status']=='root_adopted' and adoption['reviewed_by']=='root' and ar['path']==bridge.ADOPTION and adoption['independent_review']['sha256']=='3cb7efa91ebbdb42c8ae91afef2f34ade5b237ee169a369a721353b0840bbf50')
 ok('genuine root repair separated from independent history',repair['status']=='reviewed' and repair['reviewed_by']=='root' and repair['root_authorized'] is True and rr['path']==c.REPAIR and repair['independent_history_review']==indref)
 ok('canonical repair full guard actually passes',c.check_repair(ev,c.REPAIR,planner.formal_jobs(state))==real_history)
 ok('canonical adoption full guard actually passes',bridge.check_adoption(ev)==real_prefix)
 args=SimpleNamespace(stage='development',source_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',execution_manifest=c.policy()['manifest']['path'],output_relative=None,freeze_directory=None,profile_panel=None,prior_review=c.policy()['prefix_review']['path'],collection_review=None,repair_record=c.REPAIR,resume=True,stop_after=None)
 rebuilt=planner.plan(args,state,project=R,helper=factory)
 ok('full original-derived planner exactly rebuilds actual scientific plan',rebuilt==scientific)
 c.scope_invocation(scientific['invocation'])
 ok('scientific exact one attempt03 same original output prefix',scientific['invocation_relative']=='results/formal_main_v2/invocations/libero_spatial_development_8c843c1d4ee8383c_attempt03.json' and scientific['output_must_exist'] is True and scientific['output_relative']=='results/formal_main_v2/libero_spatial/downstream/development/8c843c1d4ee8383c/attempt01')
 allowed=g.SCOPED_DEVELOPMENT_PLANS['libero_spatial']
 projected_auth={'plan':{'path':allowed['path'],'sha256':'0'*64},'scientific_plan':pr,'prepared_invocation':{'path':allowed['prepared_path'],'sha256':'0'*64},'plan_arguments':vars(args)}
 ok('actual scientific reference compatible with gateway scope only',g._exact_development_authorization(projected_auth)==allowed)
 ok('exact source control loads actual canonical package',g._exact_development_control(R,scientific['invocation']).closure()==actual_sources)
  P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
 prior_ref={'path':scientific['invocation']['prior_review'],'sha256':scientific['invocation']['root_evidence_sha256'][scientific['invocation']['prior_review']]}
 prior=j(prior_ref['path'],prior_ref['sha256'])
 output=Path(scientific['invocation']['run_root']).relative_to(P).as_posix()
 four={output+'/'+n:prior['files'][output+'/'+n] for n in ('trials.jsonl','closed_loop_report.json','config.json','panel.json')}
 runtime_files={}
 for rel,pin in four.items():
  raw=data(rel,pin);p=P/rel
  ok('actual R/P original prefix identity '+rel,p.resolve()==p and not p.is_symlink() and p.is_file() and p.read_bytes()==raw and h(p.read_bytes())==pin)
  runtime_files[str(p)]={'sha256':pin,'bytes':len(raw)}
 legacy_ind=adoption['independent_review'];legacy_proof=j(legacy_ind['path'],legacy_ind['sha256'])
 ok('legacy independent proof retained explicit historical capture limitation',legacy_proof['production_admission'] is False)
 historical=j('scripts/ops/formal_spatial588_predispatch_v1/historical_identity.json','9980917fedc08fc39bb2b5eed1b2d522ef956eadf8e4e8ee8c55297332a4c9aa')
 ok('source-derived historical controller rule not invented capture',historical['actual_historical_controller_instance_capture'] is False and historical['RNG']['old_full_snapshot_recorded'] is False and historical['RNG']['no_new_rng_calls_or_action_changes'] is True)
 transition_ref=save('runtime_transition_review.json',{'schema':'formal_main_v2','kind':'formal_action_runtime_transition_review','status':'passed','review_role':'independent','reviewed_by':'independent','stage_key':scientific['invocation']['stage_key'],'from_version':'formal-downstream-root-v1','to_version':'formal-downstream-action-v1','prior_review':prior_ref['path'],'files':four,'actual_R_P_original_bytes_verified':True,'runtime_files':runtime_files,'legacy12_root_adoption':ar,'legacy12_independent_review':legacy_ind,'history_root_repair':rr,'typed_predispatch_history':real_history,'history_control_sources':actual_sources,'legacy12_compatibility':real_prefix,'retained_legacy_trials':12,'remaining_current_trials':588,'full_original_planner_reconstructed':True,'new_trial_ids_only':True,'terminal_trials_repeated':False,'prior_outcomes_replaced':False,'source_derived_historical_controller_identity':True,'historical_controller_instance_capture':False,'historical_full_RNG_snapshot_recorded':False,'new_current_runtime_actual_P_verify_passed':False,'no_new_scientific_result_admitted':True,'production_submission_authorized':False,'new_GPU_seconds':0,'new_scientific_trials':0,'final_release':False})
 ev.unchanged()
 for rel,row in read.items():assert h((R/rel).read_bytes())==row['sha256'],rel
 # A changing real registry is not written or polled here; evidence reports both
 # endpoint hashes, without using an independent reader to hold the writer lock.
 endpoint=h(statepath.read_bytes())
 gateway_rel='scripts/ops/formal_action_deployment_posttraining_spatial588_v1/gateway.py'
 gateway_installed=(R/gateway_rel).is_file()
 if gateway_installed:ok('actual canonical gateway bytes exact',h((R/gateway_rel).read_bytes())=='aba5868a8dc4e480262177785b2e62123d014046624f37924248721a9575c99c')
 evidence=save('canonical_evidence.json',{'files_read':read,'full_planner_reconstructed':True,'raw_history_reconstructed':True,'canonical_gateway_present_at_end':gateway_installed,'registry_snapshot_sha256':h(state_raw),'registry_end_sha256':endpoint,'no_real_registry_writes':True,'new_GPU_seconds':0})
 report={'schema':'formal_main_v2','kind':'Spatial588_actual_R_canonical_independent_verification','status':'passed','reviewed_by':'independent','blockers':[],'check_count':len(checks),'checks':checks,'root_install_receipt':receipt_ref,'gateway_CPU_review':{'path':'.local/spatial_gateway_independent_20261020T2253/independent_review.json','sha256':'e488430128bfbecc1e3ca846764dd6620ebea405d90ffb06063b1d09bdce69b2'},'evidence':evidence,'history_control_sources':actual_sources,'typed_predispatch_history':real_history,'legacy12_compatibility':real_prefix,'scientific_plan':pr,'runtime_transition_independent_review':transition_ref,'root_adoption':ar,'root_repair':rr,'legacy_counts':{'trials':12,'chunks':122,'executed_actions':917},'prior_GPU_seconds':395,'new_GPU_seconds':0,'new_scientific_trials':0,'new_real_submissions':0,'canonical_files_written_by_independent':False,'state_mutated':False,'P_mutated':False,'Git_mutated':False,'sealed_values_read':False,'actual_P_verified':False,'runtime_readiness_proven':False,'production_admission':False,'final_release':False,'remaining_gates':['Actual effective plan/transition/new runtime action contract and prepared invocation','Separate root and independent runtime/component readiness','Actual new P wrapper --verify and byte-identity preflight','Exact root one-attempt authorization; fresh all-mode capacity/owner/lease/pending checks under writer lock','Terminal original full consumer and independent 12legacy+588current review'],'utc':datetime.now(timezone.utc).isoformat()}
 ref=save('canonical_integration_review.json',report)
 allfiles=sorted(p for p in D.rglob('*') if p.is_file() and not p.is_symlink())
 manifest=save('delivery_manifest_v2.json',{'schema':'formal_main_v2','kind':'Spatial588_gateway_CPU_and_actual_R_canonical_delivery','status':'passed_scoped_review','production_admission':False,'review':ref,'previous_manifest':{'path':'.local/spatial_gateway_independent_20261020T2253/delivery_manifest.json','sha256':'9b633e11cfd85a9341d5f60e2f107a6d473970e2930d8402c3edd53ba5f6dd90'},'file_count':len(allfiles),'files':[{'path':p.relative_to(R).as_posix(),'sha256':h(p.read_bytes()),'bytes':p.stat().st_size} for p in allfiles],'new_GPU_seconds':0,'new_scientific_trials':0})
 print(json.dumps({'checks':len(checks),'review':ref,'transition_review':transition_ref,'manifest':manifest,'file_count':len(allfiles)}))
except BaseException as exc:
 save('canonical_failure_a1.json',{'error':repr(exc),'traceback':traceback.format_exc(),'checks':checks,'new_GPU_seconds':0,'production_admission':False})
 raise

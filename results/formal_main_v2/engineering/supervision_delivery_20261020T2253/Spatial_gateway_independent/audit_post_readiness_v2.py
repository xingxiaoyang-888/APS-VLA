"""Final read-only independent Spatial588 exact authorization/outer preflight.
This runs original validators without Gateway.run, capacity reservations,
scheduler calls, publication, model loading or environment steps.
"""
from pathlib import Path
from types import ModuleType
from datetime import datetime,timezone
import hashlib,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/spatial_gateway_independent_20261020T2253'
X='results/formal_main_v2/execution/spatial588_pre_dispatch_v1'
checks=[];reads={}
def h(b):return hashlib.sha256(b).hexdigest()
def read(p,pin):
 assert p.resolve()==p and not any(q.is_symlink() for q in (p,*p.parents))
 b=p.read_bytes();assert h(b)==pin,(str(p),pin,h(b));reads[str(p)]={'sha256':pin,'bytes':len(b)};return b
def mod(p,pin,name):
 m=ModuleType(name);m.__file__=str(p);m.__package__='';sys.modules[name]=m
 exec(compile(read(p,pin),str(p),'exec',dont_inherit=True),m.__dict__);return m
def ok(name,value=True):
 assert value,name
 checks.append({'name':name,'passed':True})
def save(name,x):
 p=D/name
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
 return {'path':p.relative_to(R).as_posix(),'sha256':h(p.read_bytes())}
try:
 authref={'path':X+'/submission_authorization_v2.json','sha256':'d0143bc88b855ad9f4d6b6008e8373272d55c953d36bba88fbd8840a1090f7d5'}
 postref={'path':'results/formal_main_v2/preflight/heartbeat_20261021T0653/Spatial_submission_readiness.json','sha256':'781295f45ece3572a2966748e44cf7c286c1868cade244cb35c09834f68c2b9c'}
 post=json.loads(read(R/postref['path'],postref['sha256']))
 ok('root post-readiness exact authorization',post['authorization']==authref and post['actual_P_outer_verified'] is True and post['actual_new_invocation_published'] is False)
 g=mod(R/'scripts/ops/formal_action_deployment_posttraining_spatial588_v1/gateway.py','aba5868a8dc4e480262177785b2e62123d014046624f37924248721a9575c99c','spatial588_final_outer_gateway')
 auth,e,plan,scientific,prepared=g.validate_authorization(R,authref)
 ok('full untouched original authorization validator passes actual v2',auth['automatic_retry'] is False and auth['maximum_attempts']==1 and auth['independent_review']['sha256']=='ca51fe9dc7a201d1791ab0569ca372fd5a87cfc8875d9a1313ae7b16ef6f5749')
 oldref=post['failed_authorization_preserved']
 read(R/oldref['path'],'5f9f641ab807850b173f51c6ef43d9622654d40a149bb223bf52895d6a25e1f7')
 try:g.validate_authorization(R,oldref)
 except ValueError as ex:
  ok('retained v1 authorization still fails exact original missing support guard',str(ex)=='component reviews omit support implementation')
 else:raise AssertionError('old rejected authorization unexpectedly accepted')
 statep=R/g.STATE;rawstate=statep.read_bytes();state=json.loads(rawstate)
 ok('state has no pending and no reservation set by this review',state['pending_submission'] is None and state['autonomous_training_v1']['reserved_GPU_slots']==0)
 ok('root post-readiness state snapshot still current',h(rawstate)==post['state_sha256_unchanged'])
 rebuilt=g.FrozenPlan(R,auth,e,plan,scientific,prepared).prepare(state)
 ok('full FrozenPlan original scientific reconstruction and prepared fields exact',rebuilt['plan']==plan and rebuilt['invocation']==prepared)
 ready=e.ref(auth['runtime_readiness'])
 ready_files=dict(ready['runtime_publication_files'])
 ok('readiness has no self-reference',auth['runtime_readiness']['path'] not in ready_files)
 for name,pin in ready_files.items():e.watch(name,pin);read(P/name,pin)
 ready_files[auth['runtime_readiness']['path']]=auth['runtime_readiness']['sha256'];rebuilt['readiness_files']=ready_files
 read(P/auth['runtime_readiness']['path'],auth['runtime_readiness']['sha256'])
 actual=g.NativeIO(R).preflight(rebuilt)
 ok('actual NativeIO no missing inputs and original output retained',actual['missing_publications']==[] and actual['output_exists'] is True)
 ok('independent actual NativeIO exactly matches root receipt',actual==post['runtime_preflight'])
 outer=mod(P/'scripts/ops/formal_action_deployment_v1/wrapper.py','d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33','spatial588_final_actual_outer')
 verified=outer.verify(prepared,project=P)
 ok('actual unchanged P outer independently verifies complete readiness',verified['original_plan']==scientific and verified['effective_plan']==plan and verified['readiness']==ready)
 ok('actual outer exact original checkpoint/run_root',str(verified['args'].checkpoint)==verified['execution_contract']['runtime_contract']['checkpoint'] and str(verified['args'].output)==prepared['run_root'])
 ok('typed history12legacy588current preserved',prepared['pre_dispatch_history']['all_prior_job_ids']==['3022743','3042529'] and prepared['pre_dispatch_history']['prior_GPU_seconds']==395 and prepared['legacy12_compatibility']['scope']['legacy_trials']==12 and prepared['legacy12_compatibility']['scope']['remaining_trials']==588)
 invrel=plan['invocation_relative']
 ok('no actual invocation registered or published',not (R/invrel).exists() and not (P/invrel).exists() and not any(j.get('invocation')==invrel for j in state['registered_jobs']))
 ok('neither old nor new request has a submitted audit',not (R/f'results/formal_main_v2/downstream_gateway/{authref["sha256"]}').exists() and not (R/f'results/formal_main_v2/downstream_gateway/{oldref["sha256"]}').exists())
 e.unchanged()
 ok('real state unchanged throughout independent review',h(statep.read_bytes())==h(rawstate))
 for name,row in reads.items():assert h(Path(name).read_bytes())==row['sha256'],name
 evidence=save('post_readiness_evidence.json',{'checks':checks,'actual_runtime_preflight':actual,'gateway_evidence_sha256':e.hashes,'direct_read_files':reads,'state_sha256':h(rawstate),'actual_outer_arguments':{'checkpoint':str(verified['args'].checkpoint),'run_root':str(verified['args'].output)},'new_GPU_seconds':0})
 report={'schema':'formal_main_v2','kind':'formal_downstream_actual_P_outer_independent_readiness_review','status':'passed','review_role':'independent','reviewed_by':'independent','blockers':[],'authorization':authref,'post_readiness':postref,'gateway_independent_review':auth['independent_review'],'prepared_invocation':auth['prepared_invocation'],'runtime_readiness':auth['runtime_readiness'],'effective_plan':auth['plan'],'scientific_plan':auth['scientific_plan'],'root_reservation_metadata':auth['root_reservation'],'execution_version':'formal-downstream-action-v1','runtime_sources':verified['execution_contract']['files'],'explicit_source_control':auth['explicit_source_control'],'legacy12_compatibility':auth['legacy12_compatibility'],'full_validate_authorization_passed':True,'full_FrozenPlan_prepare_passed':True,'actual_NativeIO_preflight_passed':True,'actual_P_new_outer_wrapper_verified':True,'actual_P_outer_verified':True,'actual_GPU_runtime_chain_verified':False,'production_chain_complete':True,'production_chain_complete_meaning':'Actual metadata/source/consumer/outer validation only. No new GPU trial occurred. This evidence does not reserve or submit.','read_only_state_sha256':h(rawstate),'registered_jobs_at_readiness':len(state['registered_jobs']),'reserved_GPU_slots':0,'pending_submission':None,'slot_mutated':False,'capacity_and_scheduler_fresh_observation_performed':False,'required_before_submission':'Root must reserve one exact owned slot with shared writer lock/CAS and run fresh actual all-mode capacity/controller owner/lease/pending checks inside the unmodified exact single-use gateway. Any uncertain outcome stops and preserves original ACK/token.','legacy_compatible_trials':12,'remaining_current_trials':588,'all_prior_GPU_seconds_retained':395,'new_GPU_seconds':0,'new_real_submissions':0,'new_GPU_submissions':0,'new_scientific_trials':0,'failed_prior_authorization_still_rejected':oldref,'scientific_settings_changed':False,'state_mutated':False,'P_mutated':False,'canonical_mutated':False,'Git_mutated':False,'sealed_values_read':False,'model_loaded':False,'simulator_started':False,'profiling_authorized':False,'final_release':False,'evidence':evidence,'check_count':len(checks),'utc':datetime.now(timezone.utc).isoformat()}
 ref=save('post_readiness_independent_review.json',report)
 files=sorted(p for p in D.rglob('*') if p.is_file() and not p.is_symlink())
 manifest=save('delivery_manifest_final.json',{'schema':'formal_main_v2','kind':'Spatial588_exact_gateway_actual_outer_complete_independent_delivery','status':'passed_scoped_review','review':ref,'file_count':len(files),'files':[{'path':p.relative_to(R).as_posix(),'sha256':h(p.read_bytes()),'bytes':p.stat().st_size} for p in files],'new_GPU_seconds':0,'new_scientific_trials':0,'automatic_submission_authority':False})
 print(json.dumps({'review':ref,'manifest':manifest,'check_count':len(checks),'file_count':len(files)}))
except BaseException as exc:
 save('post_readiness_failure_a1.json',{'error':repr(exc),'traceback':traceback.format_exc(),'checks':checks,'new_GPU_seconds':0,'state_or_submission_mutated':False})
 raise

"""Spatial588 independent real-P metadata/source/typed-consumer check.
Only this private audit directory may be written. No Slurm, model loading,
simulation, outer execution, or production authority is created.
"""
from pathlib import Path
from types import ModuleType,SimpleNamespace
from datetime import datetime,timezone
import ast,hashlib,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/spatial_gateway_independent_20261020T2253'
X='results/formal_main_v2/execution/spatial588_pre_dispatch_v1'
checks=[];reads={};runtime_reads={}
def sha(b):return hashlib.sha256(b).hexdigest()
def take(path,pin):
 assert path.resolve()==path and not any(p.is_symlink() for p in (path,*path.parents))
 b=path.read_bytes();assert sha(b)==pin,(str(path),pin,sha(b))
 (reads if R in path.parents else runtime_reads)[str(path)]={'sha256':pin,'bytes':len(b)}
 return b
def jr(rel,pin):return json.loads(take(R/rel,pin))
def ok(name,v=True):
 assert v,name
 checks.append({'name':name,'passed':True})
def mod(p,pin,name):
 b=take(p,pin);m=ModuleType(name);m.__file__=str(p);m.__package__='';sys.modules[name]=m
 exec(compile(b,str(p),'exec',dont_inherit=True),m.__dict__);return m
def save(name,x):
 p=D/name;assert p.resolve()==p and D in p.parents
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes())}
try:
 root_ref={'path':'results/formal_main_v2/preflight/heartbeat_20261021T0653/Spatial_actual_P_metadata.json','sha256':'b047c66138dcf77ab2d54ebd57e0512de10169e71ab0f60f930ac75ca172052e'}
 root=jr(root_ref['path'],root_ref['sha256'])
 can=jr('.local/spatial_gateway_independent_20261020T2253/canonical_integration_review.json','acfc4abd6ee375a0ebdfe7aebbd485d94ae1a8497c7d10acbbf9897fa5e4c6b0')
 er=root['effective_plan'];sr=root['scientific_plan'];cr=root['action_execution_contract']
 ok('exact effective/scientific/contract references',er=={'path':X+'/effective_plan.json','sha256':'17bfd4d6f5b69ae6dc18fe9cc36256baeb60f0aa4586fbb4c6de5391c93123b5'} and sr==can['scientific_plan'] and cr=={'path':X+'/execution_contract.json','sha256':'0ab1cc0063809c81a9cbb17bbd6503644e1c20d646cf4111f32472c08bbda0d5'})
 effective=jr(er['path'],er['sha256']);scientific=jr(sr['path'],sr['sha256']);contract=jr(cr['path'],cr['sha256'])
 for ref in [er,sr,cr]:
  ok('actual R/P plan bytes '+ref['path'],take(R/ref['path'],ref['sha256'])==take(P/ref['path'],ref['sha256']))
 for rel,pin in root['exact_P_publications'].items():
  ok('exact root-published P metadata '+rel,take(R/rel,pin)==take(P/rel,pin))
 inner=scientific['invocation'];inv=effective['invocation']
 for name,pin in inv['watched_files'].items():
  p=Path(name);ok('actual P watched path in P '+name,P in p.parents)
  take(p,pin)
 ok('all actual watched files checked',len(inv['watched_files'])==root['actual_P_watched_files']==219)
 c=mod(R/'scripts/ops/formal_spatial588_predispatch_v1/control.py','e2e7c3fe7f6dcf4f63b4550c3f5bc8ec50a05aaf462b38ed961ce356cc414683','spatial588_P_meta_control')
 bridge=c.compatibility_module();factory,planner=c.control_modules()
 ok('actual canonical source closure unchanged since independent',c.closure()==can['history_control_sources'])
 for rel,pin in c.closure().items():ok('actual R/P exact control closure '+rel,take(R/rel,pin)==take(P/rel,pin))
 ok('typed and legacy descriptors still independently bound',c.descriptor()==root['explicit_source_control']==can['typed_predispatch_history'] and bridge.descriptor()==root['legacy12_compatibility']==can['legacy12_compatibility'])
 ctr=mod(P/'scripts/ops/formal_action_deployment_v1/contract.py','efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19','spatial588_actual_P_contract')
 ctr.validate_execution_contract(contract,inner)
 ctr.validate_effective(scientific,effective,scientific_plan_ref=sr,execution_contract_ref=cr,execution_contract=contract)
 ok('actual P original contract validates exact new effective plan')
 trans=jr(contract['transition']['path'],contract['transition']['sha256'])
 take(P/contract['transition']['path'],contract['transition']['sha256'])
 ok('actual P original transition validates real independent four-file proof',ctr.validate_transition(trans,scientific,root=P,execution_contract=contract) is True)
 t_ref=trans['independent_review'];ok('unchanged independent transition is used',t_ref['sha256']=='a35e93c1b468e99d8f0861f3e17f53a5202488cfa1ce04f8bf66e9cbcc636888')
 take(P/t_ref['path'],t_ref['sha256']);take(R/t_ref['path'],t_ref['sha256'])
 old=mod(P/'scripts/server/run_formal_downstream.py','f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24','spatial588_actual_P_original_scientific_verify')
 args=old.verify(inner)
 ok('actual P original scientific verify uses exact frozen checkpoint and output',str(args.checkpoint)==contract['runtime_contract']['checkpoint'] and str(args.output)==inner['run_root'] and args.resume is True)
 runtime=mod(P/'scripts/ops/formal_action_deployment_v1/runtime_scope.py','6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53','spatial588_actual_P_runtime_validate')
 runtime_watches=runtime.validate_contract(contract['runtime_contract'],project_root=P,source_root=Path(inv['source_root']))
 ok('actual P original runtime contract/source and bounded engineering identities verified',bool(runtime_watches) and contract['runtime_contract']['suite']=='libero_spatial' and contract['runtime_contract']['stage']=='development')
 for name,pin in runtime_watches.items():take(Path(name),pin)
 ok('runtime source maps exact across all layers',root['runtime_sources']==contract['files'])
 for rel,pin in contract['files'].items():ok('actual R/P runtime consumer source '+rel,take(R/rel,pin)==take(P/rel,pin))
 for rel,pin in inv['support_files'].items():ok('actual R/P support '+rel,take(R/rel,pin)==take(P/rel,pin))
 state_bytes=(R/'results/experiment_supervisor/state.json').read_bytes();state=json.loads(state_bytes)
 ok('no ambiguous submission at actual metadata review',state['pending_submission'] is None)
 ev=factory.Evidence(R)
 ok('new contract same exact action semantics as proven twelve',bridge.check_adoption(ev,invocation=inv)==bridge.descriptor())
 ok('real two-allocation original consumer history reverified',c.check_repair(ev,c.REPAIR,planner.formal_jobs(state))==c.descriptor())
 exactargs=SimpleNamespace(stage='development',source_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',execution_manifest=c.policy()['manifest']['path'],output_relative=None,freeze_directory=None,profile_panel=None,prior_review=c.policy()['prefix_review']['path'],collection_review=None,repair_record=c.REPAIR,resume=True,stop_after=None)
 ok('full original scientific plan unchanged after P install',planner.plan(exactargs,state,project=R,helper=factory)==scientific)
 # Load the real typed reviewer/consumer from pinned sources; do not fabricate
 # a current terminal report because no new 588 execution exists.
 rv=c.reviewer_module();consumer=c.consumer_module()
 ok('real typed reviewer/consumer load without altered source',callable(rv.review) and callable(consumer.review_downstream_output))
 source=(R/'scripts/ops/formal_spatial588_predispatch_v1/control.py').read_text()
 ok('terminal consumer requires all600 and preserves12legacy/588current',all(x in source for x in ["result['completed_trials']==result['expected_trials']==600","'original_legacy_prefix_trials':12","'new_action_trials':588","'eligible_for_current_action_global_freeze':False","'legacy_compatible_trials':12","'current_wrapper_trials':588"]))
 ok('consumer rejects non-Spatial development and requires root typed evidence',"expected_stage=='development' and suite=='libero_spatial'" in source and "saved.get('operational_predispatch_history')==descriptor()" in source)
 c.scope_invocation(inv)
 ok('new attempt invocation absent R and P',not (R/effective['invocation_relative']).exists() and not (P/effective['invocation_relative']).exists())
 ev.unchanged()
 for name,row in {**reads,**runtime_reads}.items():assert sha(Path(name).read_bytes())==row['sha256'],name
 evidence=save('actual_P_evidence.json',{'source_files':reads,'actual_P_files':runtime_reads,'runtime_watched_files':runtime_watches,'check_count':len(checks),'checks':checks,'registry_snapshot_sha256':sha(state_bytes),'new_GPU_seconds':0})
 report={'schema':'formal_main_v2','kind':'formal_action_plan_independent_CPU_review','status':'passed','review_role':'independent','reviewed_by':'independent','blockers':[],'execution_version':'formal-downstream-action-v1','production_chain_complete':True,'production_chain_complete_meaning':'Exact real R/P metadata, original scientific validator, source/runtime contract and typed original-consumer closure; not a newly executed GPU or simulator chain. Outer invocation verification remains a subsequent explicit gate.','actual_GPU_runtime_chain_verified':False,'actual_P_original_scientific_wrapper_verified':True,'actual_P_runtime_contract_verified':True,'actual_P_new_outer_wrapper_verified':False,'scientific_plan':sr,'effective_plan':er,'action_execution_contract':cr,'plan_sha256':effective['plan_sha256'],'runtime_sources':contract['files'],'support_files':inv['support_files'],'explicit_source_control':c.descriptor(),'legacy12_compatibility':bridge.descriptor(),'root_actual_P_metadata':root_ref,'evidence':evidence,'check_count':len(checks),'source_control_scope':'Only original Spatial600 attempt03: exact12 individually compatible legacy rows retained, remaining588 under current action wrapper','original_runtime_transition':contract['transition'],'raw_consumer_ready':True,'raw_consumer_readiness_meaning':'Pinned original full reconstruction and narrowly scoped typed history/legacy proof audited; actual new terminal rows must still pass root and independent consumer.','retained_legacy_trials':12,'remaining_trials':588,'allocation_history_GPU_seconds':395,'prior_failed_GPU_seconds':2,'new_GPU_seconds':0,'new_GPU_jobs':0,'new_scientific_trials':0,'model_loaded':False,'simulator_started':False,'scientific_settings_changed':False,'state_mutated':False,'P_mutated':False,'canonical_mutated':False,'Git_mutated':False,'sealed_values_read':False,'production_submission_authorized':False,'profiling_authorized':False,'final_release':False,'remaining_gates':['Root runtime readiness and prepared invocation with exact distinct root/independent evidence','Actual new outer wrapper.verify plus NativeIO/FrozenPlan preflight','Fresh all-mode eight-slot capacity and one-attempt root authorization under writer lock/CAS','After execution: all600 original reconstruction with12legacy+588current and all393+2+new GPU seconds retained'],'utc':datetime.now(timezone.utc).isoformat()}
 ref=save('actual_P_independent_review.json',report)
 files=sorted(p for p in D.rglob('*') if p.is_file() and not p.is_symlink())
 manifest=save('delivery_manifest_v3.json',{'schema':'formal_main_v2','kind':'Spatial588_gateway_and_actual_P_metadata_independent_delivery','status':'passed_scoped_review','production_submission_authorized':False,'review':ref,'file_count':len(files),'files':[{'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in files],'new_GPU_seconds':0})
 print(json.dumps({'review':ref,'manifest':manifest,'file_count':len(files),'checks':len(checks)}))
except BaseException as exc:
 save('actual_P_failure_a1.json',{'error':repr(exc),'traceback':traceback.format_exc(),'checks':checks,'new_GPU_seconds':0,'production_submission_authorized':False})
 raise

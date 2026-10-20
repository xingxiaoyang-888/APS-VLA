"""Exact existing Long collect production plan, unapproved drafts, CPU-only evidence."""
from __future__ import annotations
from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
import copy,hashlib,importlib.util,json,os,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e';INPUT=R/'.local/long_collection_prepare_0830';D=INPUT/'a2'
DEST='results/formal_main_v2/execution/long_collect_action_v1_0830';PREF='scripts/ops/formal_action_deployment_v1/'
MANIFEST=DEST+'/dense_development.json';MANIFEST_SHA='703980515d5b063c31276b0e610ffd6cdf68adae5e1f43cfb65ecd61d92923f1'
INVENTORY='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
PIN={
'scripts/formal_execution_manifests.py':'614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89',
'scripts/ops/formal_downstream_supervisor.py':'f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571',
'scripts/server/run_formal_downstream.py':'f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24',
'scripts/ops/formal_evaluation_adapter.py':'b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd',
'scripts/profile_formal.py':'4b8a7ac0b8be904f8f6b66d9fe7f6c3f7425056e013db903ac6b480191e2ebf6',
'src/cti_vla/evaluation/formal_profiling.py':'56f9fec509a67b5687393e4d020f26722ee16f237df27261bbf38c1437278a80',
PREF+'contract.py':'efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19',
PREF+'entry.py':'2cdb69923146cbffcaaec555b970d03efbce0c9b9f74e3b743a2ce67a21aae19',
PREF+'wrapper.py':'d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33',
PREF+'gateway.py':'8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a',
PREF+'runtime_scope.py':'6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53',
PREF+'reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd',
PREF+'consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'}
READS={};WRITTEN={};TESTS=[]
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No process/network/Slurm in candidate preparation')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(path));p=p if p.is_absolute() else Path.cwd()/p
   if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) or p.suffix.lower() in {'.pt','.pth','.safetensors','.pkl','.pickle','.ckpt','.bin','.pruned_init','.init'}:raise RuntimeError('No sealed/weight payload access: '+str(p))
   writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
   if writing and D not in p.parents:raise RuntimeError('No writes outside unique private directory: '+str(p))
sys.addaudithook(guard)
def require(v,m):
 if not v:raise ValueError(m)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(value,pin=None):
 p=Path(value);p=p if p.is_absolute() else R/p
 require(p.resolve()==p and (R in p.parents or P in p.parents),'canonical R/P file required')
 raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();require(pin is None or pin==h,'pin changed: '+str(p))
 require(str(p) not in READS or READS[str(p)]==h,'evidence drift');READS[str(p)]=h;return raw
def js(value,pin=None):return json.loads(read(value,pin))
def write(name,value):
 p=D/name;require(D in p.parents,'private output only');raw=value if isinstance(value,bytes) else (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(raw)
 row=dict(path=p.relative_to(R).as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw));WRITTEN[name]=row;return row
def cref(name):return dict(path=DEST+'/'+name,sha256=WRITTEN[name]['sha256'])
def load(rel):
 raw=read(rel,PIN[rel]);p=R/rel;name='collect0830_'+p.stem
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;exec(compile(raw,str(p),'exec'),m.__dict__);return m
def reject(name,fn,fragment):
 try:fn()
 except (ValueError,RuntimeError) as exc:
  require(fragment in str(exc),'wrong negative-test rejection '+name+': '+str(exc));TESTS.append(dict(name=name,status='rejected_as_required',error_type=type(exc).__name__,error=str(exc),synthetic_fault_input=True,actual_receipt_created=False));return
 raise ValueError('Unsafe accepted candidate fault: '+name)
def check_sources():
 inventory=js(INVENTORY,'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 require(len(inventory['files'])==173,'frozen inventory count')
 for root in (R,S,R/'snapshots/formal_main_v2_run_564be0995e'):
  for rel,h in inventory['files'].items():read(root/rel,h)
 for rel,h in PIN.items():
  read(rel,h)
  if rel.startswith(PREF):read(P/rel,h)
 return inventory

def main():
 started=datetime.now(timezone.utc).isoformat();inventory=check_sources()
 input_evidence=js(INPUT/'dense_input_evidence.json');read(MANIFEST,MANIFEST_SHA);read(P/MANIFEST,MANIFEST_SHA)
 publication=js('results/formal_main_v2/preflight/heartbeat_20261020T1630/Long_collect_dense_input_publication.json','cd5845df1efd1f37a7df73b635e53c65a9975816a38a96fac3d8cf597f3d81bc')
 h=load('scripts/formal_execution_manifests.py');planner=load('scripts/ops/formal_downstream_supervisor.py')
 c=load(PREF+'contract.py');runtime=load(PREF+'runtime_scope.py');gw=load(PREF+'gateway.py')
 original_wrapper=load('scripts/server/run_formal_downstream.py');outer_wrapper=load(PREF+'wrapper.py');legacy=load('scripts/ops/formal_evaluation_adapter.py')
 state_raw=(R/'results/experiment_supervisor/state.json').read_bytes();state=json.loads(state_raw);write('state_at_planning.json',state_raw)
 state_before=copy.deepcopy(state)
 require(state.get('pending_submission') is None,'pending submission must resolve before plan')
 registered=[j for j in state['registered_jobs'] if j.get('suite')=='libero_10' and (j.get('mode') in ('collect','full','components') or j.get('stage') in ('collect','full','components'))]
 require(not registered,'registered formal collect/profile already exists; no duplicate')
 arguments=dict(stage='collect',source_inventory=INVENTORY,execution_manifest=MANIFEST,output_relative=None,freeze_directory=None,profile_panel=None,prior_review=None,collection_review=None,repair_record=None,resume=False,stop_after=None)
 write('plan_arguments.json',arguments)
 science=planner.plan(SimpleNamespace(**arguments),copy.deepcopy(state),project=R,helper=h)
 require(state==state_before,'read-only actual registry mutated')
 inv=science['invocation'];require(inv['stage']=='collect' and inv['method_ids']==['dense'] and inv['resume'] is False and inv['prior_job_ids']==[],'unexpected scope/history')
 require(science['resources']==gw.RESOURCES,'original one-L40 allocation changed')
 require(not(R/science['output_relative']).exists() and not(P/science['output_relative']).exists(),'existing collect output')
 require(not(R/science['invocation_relative']).exists() and not(P/science['invocation_relative']).exists(),'existing invocation')
 require('--global-freeze' not in inv['argv'] and '--sealed-final' not in inv['argv'] and '--uncontended-gpu' in inv['argv'],'collect/final/timing flags differ')
 write('scientific_plan.json',science);science_ref=cref('scientific_plan.json')
 args=original_wrapper.verify(inv);require(args.mode=='collect' and args.global_freeze is None and args.panel is None,'actual original P wrapper collect paths')
 fresh=js(INPUT/'fresh_collector_prepare_only.json','e1e848cedbc131b8ff2f7e55d329b2b29f338cd60d72b5fe125b75976dfd99e3')
 require(fresh['scientific_plan']['sha256']==WRITTEN['scientific_plan.json']['sha256'] and fresh['source_import_guard_preserved'] is True and fresh['actual_output_created'] is False,'fresh original preparation does not bind this actual plan')
 prep=fresh['result']
 selected=js(INPUT/'collection_selection_registration.json')
 require(prep['status']=='prepared_only' and prep['command']=='collect' and prep['methods']==['dense'] and prep['observations']==30 and prep['gpu_calls']==0 and prep['weights_validated'] is False and prep['test_opened'] is False,'original collector prepare-only result differs')
 require(prep['fixed_state_ids']==[r['trial_id'] for r in selected['selected_states']],'original collector changed task/state selection')
 write('original_collector_prepare_only.json',prep)
 scope=runtime.make_contract(project_root=R,source_root=S,suite='libero_10',stage='collect')
 require(scope==runtime.make_contract(project_root=P,source_root=S,suite='libero_10',stage='collect'),'R/P runtime contract mismatch')
 runtime_watches={}
 for root in (R,P):runtime_watches.update(runtime.validate_contract(scope,project_root=root,source_root=S))
 for path,hsh in runtime_watches.items():read(path,hsh)
 write('runtime_contract.json',scope)
 files={rel:PIN[rel] for rel in c.EXPECTED_NEW_FILES};files[c.ACTION_ADAPTER]=c.ACTION_SHA
 action=dict(schema=c.SCHEMA,kind='formal_action_execution_contract',version=c.VERSION,status='candidate_pending_root_readiness',scientific_settings_changed=False,final_evaluation_enabled=False,files=files,runtime_contract=scope,GPU_acceptance=c.GPU_REFS,source_inventory=dict(path=c.INVENTORY,sha256=c.INVENTORY_SHA),transition=None)
 write('execution_contract.json',action);action_ref=cref('execution_contract.json')
 effective=c.effective_plan(science,scientific_plan_ref=science_ref,execution_contract_ref=action_ref,execution_contract=action)
 require(c.validate_effective(science,effective,scientific_plan_ref=science_ref,execution_contract_ref=action_ref,execution_contract=action),'effective envelope validation')
 write('effective_plan.json',effective);effective_ref=cref('effective_plan.json')
 component_base='results/formal_main_v2/engineering/action_deployment_candidates_0809/'
 components={
 'runtime':dict(path=component_base+'action_deployment_chain_independent_0809/runtime_component_independent_projection.json',sha256='927cb53f1b06d01c0d49ea86449d0aeb62aa6ec6285045e6d9d6d3c4ea77abc4'),
 'wrapper':dict(path=component_base+'action_deployment_chain_independent_0809/wrapper_component_independent_projection.json',sha256='14bfa92531e1e895ffe0da595b508810e1454333d74db5fbcc12acb1cf1ae146'),
 'raw_consumer':dict(path=component_base+'action_gateway_consumers_independent_0809/raw_consumer_independent_review.json',sha256='3f815f3a48755e16e01219eb7f24c2b3fcb84e65d769d1e0a1d141a84d769479')}
 gateway_ind=dict(path=component_base+'action_gateway_consumers_independent_0809/gateway_independent_review.json',sha256='c232149639a1e6335189610aebba19830e1a3c8bfe9b932d1398566f10cd2b4f')
 for role,ref in components.items():
  rv=js(ref['path'],ref['sha256']);require(rv['component']==role and rv['status']=='passed_CPU_review' and not rv.get('blockers'),'prior component review not accepted')
 js(gateway_ind['path'],gateway_ind['sha256']);read(gw.CONTROLLER,gw.CONTROLLER_SHA);js(gw.ACTIVATION['path'],gw.ACTIVATION['sha256']);js(gw.GAP['path'],gw.GAP['sha256'])
 ready=dict(schema=c.SCHEMA,kind='formal_action_runtime_readiness',status='draft_pending_plan_independent_and_root_readiness',reviewed_by=None,execution_version=c.VERSION,scientific_settings_changed=False,final_evaluation_enabled=False,raw_consumer_ready=False,effective_plan=effective_ref,scientific_plan=science_ref,plan_sha256=effective['plan_sha256'],runtime_sources=files,root_review=None,independent_review=None,production_chain_complete=False,allowed_stages=['collect'],allowed_suite='libero_10',forbidden_stages=['development','full','components','global_freeze','final'],support_files=effective['invocation']['support_files'],action_execution_contract=action_ref,component_reviews=components,runtime_publication_files={effective_ref['path']:effective_ref['sha256'],**{r['path']:r['sha256'] for r in components.values()}},pending_runtime_publication_roles=['root_review','independent_plan_review'],selected_development_states=10,source_development_states=100,expected_observations=30,expected_scientific_success_trials=0,full_O2A_enabled=False,global_freeze_enabled=False,actual_GPU_collect_verified=False,active=False)
 write('runtime_readiness_draft.json',ready)
 auth=dict(schema=c.SCHEMA,kind='formal_downstream_single_submission_authorization',version=gw.VERSION,status='draft_not_approved',control_root=str(R),runtime_root=str(P),controller_activation=gw.ACTIVATION,maximum_attempts=1,automatic_retry=False,excluded_nodes=['gpu4020'],gateway_files=gw.source_files(R),planner=dict(path=gw.PLANNER,sha256=gw.PLANNER_SHA),controller=dict(path=gw.CONTROLLER,sha256=gw.CONTROLLER_SHA),gap_review=gw.GAP,final_release_authorized_by_gateway=False,independent_review=gateway_ind,plan=effective_ref,scientific_plan=science_ref,prepared_invocation=None,plan_arguments=arguments,runtime_readiness=None,controller_job_id=state['autonomous_training_v1']['controller_job_id'],root_reservation=None)
 auth_private=write('submission_authorization_draft.json',auth)
 write('reservation_root_record_draft.json',dict(schema=c.SCHEMA,kind='root_downstream_GPU_slot_reservation',status='draft_not_approved',controller_job_id=auth['controller_job_id'],reserved_slots=1,capacity_limit_all_GPU_modes=8,automatic_retry=False,stage_key=inv['stage_key'],plan=effective_ref,authorization_path=DEST+'/submission_authorization.json',authorization_intent_sha256=None,scope='Exactly this Long fixed30 Dense collection; no scientific success trial repetition or timing pass',old_reservation_must_not_be_reused=True))
 write('prepared_invocation_template.json',{**effective['invocation'],'registered_utc':None,'plan_sha256':effective['plan_sha256'],'runtime_readiness':None})
 proposed={cref(n)['path']:WRITTEN[n] for n in ('scientific_plan.json','execution_contract.json','effective_plan.json')}
 publications=[];runtime_files={}
 for rel,hsh in {**effective['publish_files'],**ready['runtime_publication_files']}.items():
  source=R/proposed[rel]['path'] if rel in proposed else R/rel;raw=read(source,hsh)
  for root in (R,P):
   dest=root/rel
   require(not dest.exists() or (dest.is_file() and digest(dest)==hsh),'publication conflict: '+str(dest))
  publications.append(dict(canonical_path=rel,candidate_path=source.relative_to(R).as_posix(),sha256=hsh,bytes=len(raw),R_present_exact=(R/rel).is_file(),P_present_exact=(P/rel).is_file()))
  runtime_files[str(P/rel)]=hsh
 runtime_files.update(effective['invocation']['watched_files'])
 for rel,hsh in effective['invocation']['support_files'].items():runtime_files[str(P/rel)]=hsh
 runtime_status=[]
 for path,hsh in sorted(runtime_files.items()):
  p=Path(path)
  require(P in p.parents and p.resolve()==p,'invalid P dependency')
  if p.is_file():read(p,hsh);status='present_exact'
  else:
   rel=p.relative_to(P).as_posix();require(rel in proposed and proposed[rel]['sha256']==hsh,'missing unplanned runtime input: '+path);status='missing_candidate_pending_root_publication'
  runtime_status.append(dict(path=path,sha256=hsh,status=status))
 for rel,hsh in inv['root_evidence_sha256'].items():read(rel,hsh)
 # These negative fixtures are only in memory. No fixture is a root receipt.
 reject('unsigned_outer_readiness',lambda:outer_wrapper.verify(effective['invocation'],project=P),'Exact path/SHA reference required')
 reject('draft_authorization',lambda:gw.validate_authorization(R,dict(path=auth_private['path'],sha256=auth_private['sha256'])),'typed root authorization absent')
 reject('runtime_final_scope',lambda:runtime.make_contract(project_root=R,source_root=S,suite='libero_10',stage='final'),'only registered')
 from cti_vla.evaluation import formal_profiling as fp
 registration=js('configs/experiments/formal_main_v2.json');manifest=js(MANIFEST,MANIFEST_SHA)
 bad=copy.deepcopy(manifest);bad['methods']=js('results/formal_main_v2/execution/libero_10_development_references_v1.json')['methods']
 reject('collect_not_dense_only',lambda:fp.validate_profile_manifest(bad,registration,collect=True),'fixed dense-only')
 reject('trajectory_has_fewer_than_three_observations',lambda:fp.selected_control_steps(2),'never pad or substitute')
 require(fp.selected_control_steps(3)==[0,1,2] and fp.selected_control_steps(520)==[0,259,519],'fixed temporal selection')
 for name,change,message in [('collect_unrelated_global_freeze',dict(freeze_directory=DEST),'unrelated global freeze'),('collect_substituted_panel',dict(profile_panel=DEST+'/panel.json'),'cannot substitute'),('collect_partial_stop_after',dict(stop_after=1),'Only rollouts'),('collect_resume_without_history',dict(resume=True),'No registered prior'),('full_before_global_freeze',dict(stage='full'),'complete global freeze')]:
  a={**arguments,**change};reject(name,lambda a=a:planner.plan(SimpleNamespace(**a),copy.deepcopy(state),project=R,helper=h),message)
 tampered=copy.deepcopy(effective);tampered['invocation']['argv'].append('--prepare-only')
 reject('outer_changed_scientific_argv',lambda:c.validate_effective(science,tampered,scientific_plan_ref=science_ref,execution_contract_ref=action_ref,execution_contract=action),'Scientific invocation changed')
 require(state==state_before,'tests changed immutable in-memory actual registry')
 rebuilt=planner.plan(SimpleNamespace(**arguments),copy.deepcopy(state),project=R,helper=h);require(rebuilt==science,'original scientific plan reconstruction changed')
 runtime.unchanged(runtime_watches);check_sources()
 for path,hsh in list(READS.items()):require(digest(path)==hsh,'evidence changed after build: '+path)
 write('CPU_negative_checks.json',dict(schema=c.SCHEMA,kind='Long_collect_candidate_CPU_negative_checks',tests=TESTS,all_rejected=True,actual_original_prepare_only=prep,registered_state_unfiltered=True,synthetic_receipts_published=False,new_GPU_calls=0))
 write('publication_map.json',dict(schema=c.SCHEMA,kind='Long_collect_candidate_publication_map',status='candidate_pending_root_publication',canonical_prefix=DEST,files=publications,publication_authorized_by_this_file=False))
 write('runtime_dependency_closure.json',dict(schema=c.SCHEMA,kind='Long_collect_runtime_dependency_closure',status='existing_actual_R_P_dependencies_passed_candidate_publication_pending',runtime_inputs=runtime_status,runtime_sources=files,root_science_evidence=inv['root_evidence_sha256'],P_immutable_watch=effective['invocation']['watched_files'],pending_root_and_independent_reviews=True,actual_GPU_collect_verified=False))
 write('read_evidence_sha256.json',READS)
 report=dict(schema=c.SCHEMA,kind='Long_fixed30_collect_author_CPU_preparation',status='passed_original_CPU_plan_pending_independent_root_readiness',created_utc=started,review_role='author_candidate_not_independent',method_ids=['dense'],suite='libero_10',stage='collect',scientific_plan=science_ref,effective_plan=effective_ref,action_execution_contract=action_ref,scientific_plan_content_sha256=science['plan_sha256'],effective_plan_content_sha256=effective['plan_sha256'],plan_arguments=arguments,stage_key=inv['stage_key'],run_root=inv['run_root'],invocation_relative=science['invocation_relative'],resources=science['resources'],manifest_publication=dict(path='results/formal_main_v2/preflight/heartbeat_20261020T1630/Long_collect_dense_input_publication.json',sha256='cd5845df1efd1f37a7df73b635e53c65a9975816a38a96fac3d8cf597f3d81bc'),original_planner_unmodified=True,original_P_wrapper_verified=True,original_profile_prepare_only_verified=True,corrected_profile_registry_observation=dict(field='mode or stage',registered_profiles=registered,initial_input_note='input candidate observation used stage only; actual planner and this preparation check authoritative mode as well'),current_registry_count=len(state['registered_jobs']),state_at_planning_sha256=hashlib.sha256(state_raw).hexdigest(),fixed_development_state_ids=prep['fixed_state_ids'],collection_trajectories=10,expected_observations=30,scientific_success_trials_added=0,global_freeze_required_for_collect=False,full_components_still_require_global_freeze=True,old600_reuse_authorized=False,old600_rerun_authorized=False,fixed_source_hashes_count_each=173,fixed_source_locations=[str(R),str(S),str(R/'snapshots/formal_main_v2_run_564be0995e')],deployed_action_values='unchanged accepted v4 runtime semantics',production_code_changes=0,weights_deserialized=False,final_values_read=False,new_GPU_seconds=0,submission_authorized=False,root_readiness_created=False,independent_review_created=False,live_capacity_approval=False,CPU_negative_checks=len(TESTS),pending=['Root and independent per-plan review','Canonical science/contract/effective inputs publication in R/P','Genuine root runtime_readiness and prepared_invocation','Fresh root one-slot reservation under shared writer lock','Original gateway live scheduler preflight and exactly-one submission','After real collect: whole-chain original+action raw consumer and independent reconstruction, all scheduler cost'],outputs=copy.deepcopy(WRITTEN))
 write('candidate_review.json',report)
 print(json.dumps(dict(status=report['status'],scientific_plan=science_ref,effective_plan=effective_ref,execution_contract=action_ref,run_root=inv['run_root'],observations=30,negative_checks=len(TESTS),files=WRITTEN),ensure_ascii=False))
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  write('plan_preparation_failure_a2.json',dict(error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc(),partial_outputs=WRITTEN));raise

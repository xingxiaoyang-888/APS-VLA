"""Freeze an actual development-only outer plan; drafts never self-authorize."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys
from datetime import datetime,timezone
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=R/'.local/action_actual_plan_0943'
DEST='results/formal_main_v2/execution/action_spatial_resume_0943'
PIN={'contract.py':'efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19','entry.py':'2cdb69923146cbffcaaec555b970d03efbce0c9b9f74e3b743a2ce67a21aae19','wrapper.py':'d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33','gateway.py':'8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','runtime_scope.py':'6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53','reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'}
readmap={};written={}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(rel,pin=None):
 p=Path(rel);p=p if p.is_absolute() else R/p
 assert p.resolve()==p and '..' not in p.parts and (R in p.parents or P in p.parents)
 assert not any('sealed' in x.lower() or x.lower() in ('test','weights','checkpoints') for x in p.parts)
 assert not set(p.suffixes)&{'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.pruned_init','.init'}
 raw=p.read_bytes();h=sha(raw);assert pin is None or h==pin,(str(p),pin,h)
 assert str(p) not in readmap or readmap[str(p)]==h;readmap[str(p)]=h;return raw
def js(rel,pin=None):return json.loads(read(rel,pin))
def write(name,obj):
 raw=(json.dumps(obj,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 with (D/name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 written[name]={'path':str((D/name).relative_to(R)),'sha256':sha(raw),'bytes':len(raw)}
 return {'path':DEST+'/'+name,'sha256':sha(raw)}
def load(n):
 p=R/'scripts/ops/formal_action_deployment_v1'/n;raw=read(p,PIN[n])
 spec=importlib.util.spec_from_file_location('actual_outer_'+n[:-3],p);m=importlib.util.module_from_spec(spec);exec(compile(raw,str(p),'exec'),m.__dict__);return m
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No subprocess/network while freezing draft')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(path));p=p if p.is_absolute() else Path.cwd()/p
   assert not any('sealed' in x.lower() for x in p.parts)
   assert not set(p.suffixes)&{'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.pruned_init','.init'}
   writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
   if writing:assert D in p.parents,str(p)
sys.addaudithook(guard)
read(__file__)
ct=load('contract.py');gw=load('gateway.py')
plan=js(D/'scientific_plan.json','43a521e2b1c5b7f8ceff442ce655dde5cae73dfde0f9f7598f65fa57446b4a94')
runtime=js(D/'runtime_contract.json','127b7f81407731126738a028c439a0d722474001ac945d1545da56f4f0678708')
transition_ref={'path':DEST+'/transition.json','sha256':'95da28cbfd0968d38e5e92b9468c331b377cccf88ec3bfcdb342b4ce2f1a43a1'}
transition=js(transition_ref['path'],transition_ref['sha256'])
assert transition['allowed_stages']==['development'] and transition['old_new_outcome_equivalence_established'] is False
ind=js(transition['independent_review']['path'],transition['independent_review']['sha256'])
for n,h in transition['files'].items():read(n,h)
ct.validate_transition(transition,plan,root=R)
files={}
for n,h in PIN.items():rel='scripts/ops/formal_action_deployment_v1/'+n;read(rel,h);files[rel]=h
files[ct.ACTION_ADAPTER]=ct.ACTION_SHA;read(ct.ACTION_ADAPTER,ct.ACTION_SHA)
for n,h in {**runtime['dependencies'],**ct.GPU_REFS}.items():read(n,h)
action=dict(schema='formal_main_v2',kind='formal_action_execution_contract',version=ct.VERSION,status='candidate_pending_root_readiness',scientific_settings_changed=False,final_evaluation_enabled=False,files=files,runtime_contract=runtime,GPU_acceptance=ct.GPU_REFS,source_inventory={'path':ct.INVENTORY,'sha256':ct.INVENTORY_SHA},transition=transition_ref)
scientific_ref={'path':DEST+'/scientific_plan.json','sha256':'43a521e2b1c5b7f8ceff442ce655dde5cae73dfde0f9f7598f65fa57446b4a94'}
action_ref=write('execution_contract.json',action)
effective=ct.effective_plan(plan,scientific_plan_ref=scientific_ref,execution_contract_ref=action_ref,execution_contract=action)
ct.validate_effective(plan,effective,scientific_plan_ref=scientific_ref,execution_contract_ref=action_ref,execution_contract=action)
effective_ref=write('effective_plan.json',effective)
prefix=ct.resume_prefix_inputs(plan['invocation']);assert len(prefix)==2
assert set(plan['invocation']['watched_files'])-set(effective['invocation']['watched_files'])==set(prefix)
component_base='results/formal_main_v2/engineering/action_deployment_candidates_0809/'
components={
 'runtime':{'path':component_base+'action_deployment_chain_independent_0809/runtime_component_independent_projection.json','sha256':'927cb53f1b06d01c0d49ea86449d0aeb62aa6ec6285045e6d9d6d3c4ea77abc4'},
 'wrapper':{'path':component_base+'action_deployment_chain_independent_0809/wrapper_component_independent_projection.json','sha256':'14bfa92531e1e895ffe0da595b508810e1454333d74db5fbcc12acb1cf1ae146'},
 'raw_consumer':{'path':component_base+'action_gateway_consumers_independent_0809/raw_consumer_independent_review.json','sha256':'3f815f3a48755e16e01219eb7f24c2b3fcb84e65d769d1e0a1d141a84d769479'}}
for role,ref in components.items():
 rv=js(ref['path'],ref['sha256'])
 assert rv['component']==role and rv['status']=='passed_CPU_review' and not rv.get('blockers')
gateway_ind={'path':component_base+'action_gateway_consumers_independent_0809/gateway_independent_review.json','sha256':'c232149639a1e6335189610aebba19830e1a3c8bfe9b932d1398566f10cd2b4f'}
js(gateway_ind['path'],gateway_ind['sha256'])
ready=dict(schema='formal_main_v2',kind='formal_action_runtime_readiness',status='draft_pending_plan_independent_and_root_readiness',reviewed_by=None,execution_version=ct.VERSION,scientific_settings_changed=False,final_evaluation_enabled=False,raw_consumer_ready=False,effective_plan=effective_ref,scientific_plan=scientific_ref,plan_sha256=effective['plan_sha256'],runtime_sources=files,root_review=None,independent_review=None,production_chain_complete=False,allowed_stages=['development'],allowed_suite='libero_spatial',forbidden_stages=['collect','full','components','global_freeze','final'],support_files=effective['invocation']['support_files'],action_execution_contract=action_ref,component_reviews=components,runtime_publication_files={effective_ref['path']:effective_ref['sha256'],**{r['path']:r['sha256'] for r in components.values()},transition['independent_review']['path']:transition['independent_review']['sha256']},pending_runtime_publication_roles=['root_review','independent_plan_review'],original_terminal_trials_preserved=12,maximum_new_trial_ids=588,old_new_outcome_equivalence_established=False,O2A_enabled=False,global_freeze_enabled=False,active=False)
ready_ref=write('runtime_readiness_draft.json',ready)
state=js(D/'state_at_planning.json')
auth_path=DEST+'/submission_authorization.json'
auth=dict(schema='formal_main_v2',kind='formal_downstream_single_submission_authorization',version=gw.VERSION,status='draft_not_approved',control_root=str(R),runtime_root=str(P),controller_activation=gw.ACTIVATION,maximum_attempts=1,automatic_retry=False,excluded_nodes=['gpu4020'],gateway_files=gw.source_files(R),planner={'path':gw.PLANNER,'sha256':gw.PLANNER_SHA},controller={'path':gw.CONTROLLER,'sha256':gw.CONTROLLER_SHA},gap_review=gw.GAP,final_release_authorized_by_gateway=False,independent_review=gateway_ind,plan=effective_ref,scientific_plan=scientific_ref,prepared_invocation=None,plan_arguments=js(D/'plan_arguments.json'),runtime_readiness=None,controller_job_id=state['autonomous_training_v1']['controller_job_id'],root_reservation=None)
auth_ref=write('submission_authorization_draft.json',auth)
reservation=dict(schema='formal_main_v2',kind='root_downstream_GPU_slot_reservation',status='draft_not_approved',controller_job_id=auth['controller_job_id'],reserved_slots=1,capacity_limit_all_GPU_modes=8,automatic_retry=False,stage_key=effective['invocation']['stage_key'],plan=effective_ref,authorization_path=auth_path,authorization_intent_sha256=None,scope='Only this Spatial development continuation; not a CUDA recovery reservation',old_CUDA_reservation_must_not_be_reused=True)
write('reservation_root_record_draft.json',reservation)
prepared={**effective['invocation'],'registered_utc':None,'plan_sha256':effective['plan_sha256'],'runtime_readiness':None}
write('prepared_invocation_template.json',prepared)
new_outputs={scientific_ref['path']:{'source':str((D/'scientific_plan.json').relative_to(R)),'sha256':scientific_ref['sha256']},action_ref['path']:{'source':str((D/'execution_contract.json').relative_to(R)),'sha256':action_ref['sha256']},effective_ref['path']:{'source':str((D/'effective_plan.json').relative_to(R)),'sha256':effective_ref['sha256']}}
publications={}
for rel,h in {**effective['publish_files'],**ready['runtime_publication_files']}.items():
 src=R/new_outputs[rel]['source'] if rel in new_outputs else R/rel
 raw=read(src,h);dest=P/rel
 exists=dest.exists();p_sha=sha(read(dest)) if exists else None
 assert p_sha in (None,h),(rel,p_sha,h)
 publications[rel]=dict(source_relative=src.relative_to(R).as_posix(),sha256=h,bytes=len(raw),P_status='already_exact' if exists else 'missing_pending_root_publication')
for n,h in effective['invocation']['root_evidence_sha256'].items():
 read(R/new_outputs[n]['source'] if n in new_outputs else R/n,h)
watch_results={}
pubmap={n:r['sha256'] for n,r in publications.items()}
for absolute,h in {**effective['invocation']['watched_files'],**prefix}.items():
 path=Path(absolute)
 if path.exists():read(path,h);watch_results[absolute]='already_exact'
 else:
  rel=path.relative_to(P).as_posix();assert pubmap.get(rel)==h,('not publishable',absolute)
  watch_results[absolute]='missing_expected_publication'
assert not (R/effective['invocation_relative']).exists() and not (P/effective['invocation_relative']).exists()
write('dependency_closure.json',dict(schema='formal_main_v2',kind='actual_development_plan_dependency_closure',status='all_existing_bytes_verified_pending_root_publication_readiness',effective_plan=effective_ref,scientific_plan=scientific_ref,execution_contract=action_ref,transition=transition_ref,readiness_draft=ready_ref,R_scientific_evidence=plan['invocation']['root_evidence_sha256'],P_immutable_watch=effective['invocation']['watched_files'],P_pre_run_prefix=prefix,P_runtime_status=watch_results,runtime_publications=publications,explicitly_pending=['Root/independent plan readiness receipt bytes','Readiness final signed bytes','Prepared invocation with actual registration time','Root authorization/reservation ownership and current all-job Slurm capacity'],no_weight_publication=True,no_sealed_input=True,not_a_live_capacity_approval=True))
for p,h in list(readmap.items()):assert sha(Path(p).read_bytes())==h,('input changed',p)
summary=dict(schema='formal_main_v2',kind='actual_development_action_plan_preparation',status='plan_validated_readiness_pending',created_utc=datetime.now(timezone.utc).isoformat(),scientific_inputs_synthetic=False,scientific_plan=scientific_ref,effective_plan=effective_ref,effective_plan_content_sha256=effective['plan_sha256'],execution_contract=action_ref,transition=transition_ref,source_files=files,prior_completed_trials=12,remaining_trial_ids=588,method_ids=effective['invocation']['method_ids'],prior_GPU_seconds=393,resources=effective['resources'],resume=True,stop_after=None,allowed_stages=['development'],forbidden_stages=['collect','full','components','global_freeze','final'],old_new_outcome_equivalence_established=False,passed_checks=['real unmocked original pure planner','exact allowlist converter and same scientific argv/resources/provenance','root signed and independent reviewed exact prefix','two files only pre-run partition','real runtime contract and inherited v4 16-cell proof','P existing input SHA/no conflict and explicit missing publications','unallocated next attempt absent in R and P'],new_GPU_jobs=0,production_state_modified=False,P_publication=False,root_readiness_issued=False,outputs=written,read_evidence_sha256=readmap)
write('plan_preparation_review.json',summary)
print(json.dumps({'effective_plan':effective_ref,'content_sha256':effective['plan_sha256'],'execution_contract':action_ref,'files':written,'read_evidence_count':len(readmap)},ensure_ascii=False,sort_keys=True))

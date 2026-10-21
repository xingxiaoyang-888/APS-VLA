from pathlib import Path
import ast,copy,hashlib,json,sys,io,contextlib,traceback,math
from datetime import datetime,timezone
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
A=R/'.local/goal_bounded_diagnostic_20261020T2358';D=R/'.local/goal_bounded_diagnostic_independent_20261020T2358'
H=lambda b:hashlib.sha256(b).hexdigest()
def jb(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
checks=[];inputs={}
def ck(b,name):
 if not b:raise AssertionError(name)
 checks.append({'check':name,'passed':True})
def rd(p,want=None):
 p=Path(p);ck(p.is_file() and p.resolve()==p,'regular:'+str(p))
 st=p.stat();b=p.read_bytes();en=p.stat();ck((st.st_size,st.st_mtime_ns,st.st_ino)==(en.st_size,en.st_mtime_ns,en.st_ino),'stable:'+str(p))
 if want:ck(H(b)==want,'SHA:'+str(p))
 inputs[str(p)]={'bytes':len(b),'sha256':H(b)}
 return b
def js(p,want=None):return json.loads(rd(p,want))
def out(name,value):
 p=D/name;ck(p.parent==D and not p.exists(),'new_private:'+name)
 b=(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':H(b),'bytes':len(b)}
def io_guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect','socket.bind'):raise RuntimeError('No subprocess/network')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes)) and ((mode and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags & (1|2|64|512|1024))):
   if not Path(path).resolve().is_relative_to(D):raise RuntimeError('Write outside private independent directory')
 if event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.symlink','os.link','os.chmod'):
  for p in args[:2 if event in ('os.rename','os.link') else 1]:
   if isinstance(p,(str,bytes)) and not Path(p).resolve().is_relative_to(D):raise RuntimeError('Mutation outside private independent directory')
sys.addaudithook(io_guard)
try:
 manifest=js(A/'delivery_manifest_v2.json','84a3b3c3695f437b63898ed3be9e07857910940be82b8db51437376c2771ee29')
 ck(manifest['file_count']==len(manifest['files'])==23,'frozen23file_manifest_v2')
 for name,m in manifest['files'].items():
  ck(Path(name).name==name,'flat_manifest_name:'+name);b=rd(A/name,m['sha256']);ck(len(b)==m['bytes'],'manifest_size:'+name)
 oldmanifest=js(A/'delivery_manifest.json','d5e0391fd7b10a1fac8ecdf0198c1abcaab5375894b80dee37c86638273477bf')
 ck(len(oldmanifest['files'])==20 and all(manifest['files'][k]==v for k,v in oldmanifest['files'].items()),'original20_unchanged')
 inventory=js(A/'source_inventory.json','fb164db456cbbe2455d9803ccfa13bf2d64061d768b80cf84f3fb8987dccab7e')
 ck(inventory['file_count']==len(inventory['files'])==100 and inventory['raw_blob_count']==len(inventory['selected_raw_blobs'])==72,'actual100sources72blobs')
 for p,m in inventory['files'].items():
  path=Path(p);ck(path.is_relative_to(R) or path.is_relative_to(P),'server_source_path')
  ck('/test/' not in p and path.suffix not in ('.pt','.pth','.safetensors','.ckpt'),'no_weight_or_sealed_final_input')
  b=rd(path,m['sha256']);ck(len(b)==m['bytes'],'inventory_size:'+p)
 for p,m in inventory['selected_raw_blobs'].items():ck(inventory['files'][p]==m,'72_blob_subset:'+p)
 # Reproduce pinned analyzer verbatim, intercept only output publication to independent memory.
 source=rd(A/'analyze.py','1b6d006846e58d9e8e513e4430b198f3f78ad4b2740c3783e2b580cbc17b299f')
 ana={'__name__':'independent_goal_author_reproduction','__file__':str(A/'analyze.py')}
 exec(compile(source,str(A/'analyze.py'),'exec'),ana)
 captured={}
 allowed={'source_timing_and_hash_contract.json','recorded_environment_identity.json','fixed_neighbor_hypothesis_tests.json','selected_archive_member_verification.json','classifier_CPU_tests.json','missing_evidence_and_propositions.json','boundary_evidence.json','source_inventory.json','execution_report.json'}
 def capture(name,value):
  ana['need'](name in allowed and name not in captured,'new private output '+name)
  captured[name]=json.loads(json.dumps(value,allow_nan=False))
 ana['out']=capture
 stdout=io.StringIO()
 with contextlib.redirect_stdout(stdout):ana['main']()
 ck(set(captured)==allowed,'all9_analyzer_outputs_captured_no_source_write')
 for name,value in captured.items():
  original=js(A/name);actual=copy.deepcopy(value)
  if name=='execution_report.json':
   actual.pop('CPU_wall_seconds');original.pop('CPU_wall_seconds')
  ck(actual==original,'author_analyzer_exact_reproduction:'+name)
 ck(captured['execution_report.json']['check_count']==1234 and len(captured['execution_report.json']['checks'])==1235 and all(x['passed'] for x in captured['execution_report.json']['checks']),'metadata1234_actual1235_preserved_and_reproduced')
 ck(captured['classifier_CPU_tests.json']['test_count']==14,'original14_classifier_cases')
 repro=out('author_analyzer_reproduction.json',{'source_sha256':H(source),'original_output_root':str(A),'publication_interception_only':True,'reproduced_outputs':sorted(captured),'all_outputs_equal_except_wall_seconds':True,'declared_check_count':1234,'actual_check_array_count':1235,'classifier_cases':14,'no_new_GPU_or_environment_execution':True,'stdout':stdout.getvalue(),'count_erratum':js(A/'count_metadata_clarification.json')})
 # Builder has top-level execution: compile exact AST split immediately before first input panel, no source edits.
 build=rd(A/'build_prospective_specification.py','75379ac29257a706729262873bb9e9d875dd66edabeea882c1f3ab5cd8b48e63')
 bt=ast.parse(build);idx=next(i for i,n in enumerate(bt.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='panel' for t in n.targets))
 ck(all(not isinstance(n,ast.Assign) or not any(isinstance(t,ast.Name) and t.id in ('panel','protocol') for t in n.targets) for n in bt.body[:idx]),'builder_split_before_input_only')
 scope={'__name__':'independent_goal_spec_reproduction','__file__':str(A/'build_prospective_specification.py')}
 exec(compile(ast.Module(body=bt.body[:idx],type_ignores=[]),str(A/'build_prospective_specification.py'),'exec'),scope)
 spec_outputs={}
 def write_spec(name,value):
  scope['check'](name not in spec_outputs and Path(name).name==name,'private nonoverwrite '+name)
  spec_outputs[name]=json.loads(json.dumps(value,allow_nan=False))
 scope['write']=write_spec;bs=io.StringIO()
 with contextlib.redirect_stdout(bs):exec(compile(ast.Module(body=bt.body[idx:],type_ignores=[]),str(A/'build_prospective_specification.py'),'exec'),scope)
 ck(set(spec_outputs)=={'prospective_full200_specification.json','prospective_specification_CPU_tests.json','command_serialization_check.json'},'all_builder_outputs_memory_only')
 for name,value in spec_outputs.items():ck(value==js(A/name),'author_spec_exact_reproduction:'+name)
 spec=scope['protocol'];ck(spec_outputs['prospective_specification_CPU_tests.json']['positive_tests']==1 and spec_outputs['prospective_specification_CPU_tests.json']['rejection_tests']==20,'one_positive20_negative_replayed')
 out('author_spec_v1_reproduction.json',{'source_sha256':H(build),'exact_AST_prefix_and_suffix_with_output_capture_only':True,'outputs':list(spec_outputs),'positive_tests':1,'negative_tests':20,'all_outputs_equal':True,'stdout':bs.getvalue(),'production_ready':False})
 # Independent raw ledger and source timing reconstruction.
 O=ana['O'];N=ana['N'];KEYS=ana['KEYS']
 old=[x for x in map(json.loads,rd(O/'original_run/trials.jsonl',ana['PINS'][str(O/'original_run/trials.jsonl')]).splitlines()) if x.get('event')=='result']
 new=[x for x in map(json.loads,rd(N/'original_run/trials.jsonl',ana['PINS'][str(N/'original_run/trials.jsonl')]).splitlines()) if x.get('event')=='result']
 ck(len(old)==len(new)==58 and [x['trial_id'] for x in old]==[x['trial_id'] for x in new],'independent58_orderedidentities')
 f=('control_step','observation_sha256','normalized_actions','environment_actions','metadata')
 trace=lambda r:({'chunks':[{k:x[k] for k in f} for x in r['chunks']],'executed_actions':r['executed_actions']})
 changed=[i+1 for i in range(58) if trace(old[i])!=trace(new[i])]
 ck(changed==[30],'independent_only_ordinal30_trace_difference')
 a,b=old[29],new[29]
 ck(a['trial_id']==b['trial_id']==ana['IDENTITY'] and a['task_id']==b['task_id']==1 and a['source_state_index']==b['source_state_index']==12,'independent_fixed_identity')
 hash_difference=[i for i,(x,y) in enumerate(zip(a['chunks'],b['chunks'])) if x['observation_sha256']!=y['observation_sha256']]
 action_difference=[i for i,(x,y) in enumerate(zip(a['executed_actions'],b['executed_actions'])) if jb(x)!=jb(y)]
 ck(hash_difference[0]==9 and action_difference[0]==72 and jb(a['executed_actions'][:72])==jb(b['executed_actions'][:72]),'independent_q9_step72_signed_zero_command_boundary')
 rt=rd(R/'src/cti_vla/evaluation/libero_runtime.py','2fc1bacbd1268a36f2e31451c70a650be4f8d0c8f6803e7c8b2a3d45f701c781').decode();tree=ast.parse(rt)
 run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_episode')
 predict=next(n for n in ast.walk(run) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='predict_chunk')
 hashcall=next(n for n in ast.walk(run) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_observation_hash')
 ck(predict.lineno==329 and hashcall.lineno==337 and predict.lineno<hashcall.lineno,'source_post_policy_hash_position')
 hashfn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_observation_hash')
 hn={'hashlib':hashlib,'np':np,'Mapping':dict,'Any':object};exec(compile(ast.Module(body=[hashfn],type_ignores=[]),'<pinned_original_hash_only>','exec'),hn)
 old_events=[x for x in map(json.loads,rd(O/'observer/events.jsonl',ana['PINS'][str(O/'observer/events.jsonl')]).splitlines()) if x.get('ordinal')==30]
 new_events=[x for x in map(json.loads,rd(N/'observer/events.jsonl',ana['PINS'][str(N/'observer/events.jsonl')]).splitlines()) if x.get('ordinal')==30]
 ck(not any(x.get('control_step',0) not in (None,0) for x in old_events),'no_old_nonzero_pre_post_raw_arrays')
 def arrays(event,base):
  ans={}
  ck(set(event['observation_arrays'])==set(KEYS),'five_components')
  for key in KEYS:
   m=event['observation_arrays'][key];ref=m['blob'];p=base/'observer'/ref['path']
   ck(str(p) in inventory['files'] and ref['path'].startswith('blobs/') and '..' not in Path(ref['path']).parts,'exact_pinned_blob_path')
   raw=rd(p,ref['sha256']);dt=np.dtype(m['dtype']);ck(not dt.hasobject and len(raw)==ref['bytes']==m['bytes']==math.prod(m['shape'])*dt.itemsize and H(raw)==m['sha256'],'blob_dtype_shape_bytes')
   ans[key]=np.frombuffer(raw,dtype=dt).reshape(m['shape'])
  return ans
 values={}
 for q in range(11):
  before=[e for e in new_events if e.get('control_step')==8*q and e.get('phase') in ('t0_query_before','query_before')]
  after=[e for e in new_events if e.get('control_step')==8*q and e.get('phase') in ('t0_query_after','query_after')]
  ck(len(before)==len(after)==1,'one_pre_post_for_query:'+str(q))
  bef,aft=arrays(before[0],N),arrays(after[0],N)
  ck(all(bef[k].dtype==aft[k].dtype and bef[k].shape==aft[k].shape and bef[k].tobytes()==aft[k].tobytes() for k in KEYS),'actual_new_prepost_bytes:'+str(q))
  digest=hn['_observation_hash'](bef);ck(digest==b['chunks'][q]['observation_sha256']==before[0]['observation_sha256']==after[0]['observation_sha256'],'pinned_original_hash_recomputed:'+str(q));values[q]=bef
 preold=next(x for x in old_events if x.get('phase')=='t0_query_before');vold=arrays(preold,O)
 ck(all(vold[k].dtype==values[0][k].dtype and vold[k].shape==values[0][k].shape and vold[k].tobytes()==values[0][k].tobytes() for k in KEYS),'old_new_t0_five_raw_bytes')
 target=a['chunks'][9]['observation_sha256'];candidates=[]
 for q in (8,9,10):candidates.append({'kind':'whole_query','query_index':q,'step':8*q,'sha256':hn['_observation_hash'](values[q]),'matches_old_q9_post':hn['_observation_hash'](values[q])==target})
 for q in (8,10):
  for key in KEYS:
   combined=dict(values[9]);combined[key]=values[q][key];hashed=hn['_observation_hash'](combined)
   candidates.append({'kind':'single_component_substitution','base_query':9,'substituted_key':key,'from_query':q,'sha256':hashed,'matches_old_q9_post':hashed==target})
 ck(candidates==captured['fixed_neighbor_hypothesis_tests.json']['candidates'] and len(candidates)==13 and not any(x['matches_old_q9_post'] for x in candidates),'13_fixed_candidates_independent_reconstruction_zero_matches')
 # Hash excludes instruction by construction; changing unknown instruction cannot locate the old difference.
 v=values[9];ck(hn['_observation_hash']({**v,'instruction':'one'})==hn['_observation_hash']({**v,'instruction':'different'}),'raw_five_hash_excludes_instruction')
 altered={k:np.copy(x) for k,x in v.items()};altered[KEYS[0]].reshape(-1)[0]^=1
 ck(hn['_observation_hash'](altered)!=hn['_observation_hash'](v),'independent_image_bit_negative')
 altered={k:np.copy(x) for k,x in v.items()};altered[KEYS[2]]=altered[KEYS[2]].astype(np.float32)
 ck(hn['_observation_hash'](altered)!=hn['_observation_hash'](v),'independent_dtype_negative')
 # Independently derive complete future whitelist from original panel, without looking at outcomes.
 panel=scope['panel'];methods=[m['identity'] for m in scope['config']['manifest']['methods']];frozen=[]
 for s in panel['states']:
  for m in methods:
   frozen.append({'ordinal':len(frozen)+1,'trial_id':s['trial_id']+':'+m['method_id'],'state_trial_id':s['trial_id'],'task_id':s['task_id'],'task_name':s['task_name'],'source_state_index':s['source_state_index'],'initial_state_sha256':s['initial_state_sha256'],'method':m['method_id']})
 ck(frozen==spec['rows'] and len(frozen)==200 and len({x['state_trial_id'] for x in frozen})==100,'independent_full200_frozen_whitelist')
 ck(H(jb(frozen))==spec['rows_signature_sha256'],'row_signature_actual')
 ck(spec['maximum_control_steps']==60000 and spec['maximum_policy_queries']==7600 and spec['stop_after_trial_count']==200 and spec['maximum_new_attempts']==1,'actual_spec_fixed60000_7600_bounds')
 ck(spec['scientific_environment']==scope['registration']['suites']['libero_goal']['environment'] and spec['policy_watchdog_seconds']==scope['config']['policy_watchdog_seconds'],'actual_spec_environment_watchdog')
 historical=P/'results/formal_main_v2/libero_goal/downstream/development/5185766bb353c8e6/attempt01/trials.jsonl'
 hist=[x for x in map(json.loads,rd(historical,'41494deb99b5b498343a21b4e187599743aaa2383301c7337c57f7dbda591e57').splitlines()) if x.get('event')=='result']
 ck(len(hist)==200 and [x['trial_id'] for x in hist]==[x['trial_id'] for x in frozen],'real_old200_same_full_identities')
 mismatches=[]
 for i in range(0,200,2):
  x,y=hist[i:i+2];ck(x['state_trial_id']==y['state_trial_id'],'old200_pair_identity:'+str(i//2))
  if x['chunks'][0]['observation_sha256']!=y['chunks'][0]['observation_sha256']:mismatches.append({'state_trial_id':x['state_trial_id'],'task_id':x['task_id'],'source_state_index':x['source_state_index'],'A_ordinal':i+1,'B_ordinal':i+2,'A_t0_posthash':x['chunks'][0]['observation_sha256'],'B_t0_posthash':y['chunks'][0]['observation_sha256']})
 ck(len(mismatches)>0,'old200_still_has_actual_t0_posthash_mismatch')
 facts=out('independent_actual_evidence.json',{'source_timing':{'predict_line':predict.lineno,'hash_line':hashcall.lineno,'sampling':'post_policy','old_nonzero_pre_observations_saved':False},'fixed_identity':ana['IDENTITY'],'all58_changed_ordinals':changed,'first_different_hash_query':9,'first_different_control_action':72,'previous_equal_hash_query':8,'new_selected11_prepost_bytes_verified':True,'selected_archive_five_members_reconstructed_by_original_pinned_analyzer':True,'entire_archive10741_reaudit':False,'fixed13_candidates':candidates,'only_exact13_candidates_excluded':True,'old200_actual_t0_posthash_mismatches':mismatches,'prospective_full200_original_whitelist_verified':True,'old200_HOLD':True,'new_Goal_science_HOLD':True,'cause_identified':False,'old_failure_repaired':False,'new_GPU_jobs':0,'scientific_trials_added':0,'final_release':False})
 # Supplementary finite contract boundary cases. Accepted weaknesses are explicitly retained.
 boundary=[]
 changes=[('max_control_steps_not_bound',lambda p:p.update(maximum_control_steps=60001)),('max_policy_queries_not_bound',lambda p:p.update(maximum_policy_queries=7601)),('stop_after_not_bound',lambda p:p.update(stop_after_trial_count=58)),('watchdog_not_bound',lambda p:p.update(policy_watchdog_seconds=1)),('rows_signature_not_bound',lambda p:p.update(rows_signature_sha256='0'*64)),('panel_sha_not_bound',lambda p:p.update(panel_sha256='0'*64)),('pass_criteria_not_bound',lambda p:p.update(pass_criteria=[])),('fail_criteria_not_bound',lambda p:p.update(fail_criteria=[])),('retro_no_auto_transition_not_bound',lambda p:p['retrospective_branch'].update(no_automatic_transition=False))]
 for name,mutate in changes:
  bad=copy.deepcopy(spec);mutate(bad)
  try:answer=scope['validate_design'](bad,frozen,methods,scope['environment'])
  except (ValueError,KeyError,TypeError) as e:boundary.append({'case':name,'accepted':False,'reason':str(e)})
  else:boundary.append({'case':name,'accepted':bool(answer),'production_ready':bad['production_ready'],'required_fix':'Bind this field to exact canonical specification or derived authoritative value before using the predicate as a complete design contract.'})
 ck(all(x['accepted'] for x in boundary),'nine_v1_contract_gaps_measured')
 out('v1_design_contract_counterexamples.json',{'source_sha256':H(build),'tests':boundary,'immutable_original_spec_fields_correct':True,'not_actual_permission':True,'future_source_must_be_separately_reviewed':True})
 # Distinct hypothetical causes project to identical actual available logs; neither is attribution.
 classify=ana['classify'];evidence=dict(integrity=True,identity_same=True,schema_same=True,old_sampling='post_policy',new_sampling='pre_and_post_policy',old_pre_available=False,old_pre=None,old_post=target,new_pre=b['chunks'][9]['observation_sha256'],new_post=b['chunks'][9]['observation_sha256'],actions_before_same=True)
 wa={**evidence,'old_pre_available':True,'old_pre':target};wb={**evidence,'old_pre_available':True,'old_pre':evidence['new_pre']}
 ca,cb=classify(wa),classify(wb)
 ck(ca['decision']!=cb['decision'] and all(c[k] is False for c in (ca,cb) for k in ('root_cause_identified','scientific_release','old200_adopted')),'two_synthetic_worlds_cannot_attribute_actual_missing_data')
 for name,mutate in [('missing_integrity',lambda x:x.pop('integrity')),('false_schema',lambda x:x.update(schema_same=False)),('new_mutation',lambda x:x.update(new_post='f'*64)),('unsupported_old_pre',lambda x:x.update(old_pre='0'*64))]:
  bad=copy.deepcopy(evidence);mutate(bad)
  try:classify(bad)
  except (ValueError,KeyError,TypeError):ck(True,'supplementary_classifier_reject:'+name)
  else:raise AssertionError('classifier expected reject '+name)
 ck('torch' not in sys.modules and 'mujoco' not in sys.modules,'no_model_simulator_import')
 for p,m in inputs.items():ck(H(Path(p).read_bytes())==m['sha256'],'final_source_stability:'+p)
 report={'schema':'formal_main_v2','kind':'Goal_bounded_CPU_diagnostic_independent_review_v1','status':'passed_evidence_analysis_with_v1_design_contract_gaps','reviewed_by':'independent_goal_cpu_gate_2054','author_manifest':{'path':str((A/'delivery_manifest_v2.json').relative_to(R)),'sha256':'84a3b3c3695f437b63898ed3be9e07857910940be82b8db51437376c2771ee29'},'utc':datetime.now(timezone.utc).isoformat(),'checks_passed':len(checks),'checks':checks,'source_inventory_files':100,'selected_blob_files':72,'author_checks_replayed_actual':1235,'author_declared_check_count_erratum':1234,'classifier14_tests_replayed':True,'original_design_tests':{'positive':1,'negative':20},'additional_design_counterexamples':len(boundary),'all_original_outputs_reproduced_except_wallclock':True,'source_publication_interception_only':True,'independent_actual_evidence':facts,'old_hash_post_policy_verified':True,'no_old_nonzero_pre_capture_invented':True,'13_exact_candidates_excluded_no_mechanism_attribution':True,'future200_and_old200_HOLD_separate':True,'old200_HOLD':True,'new_Goal_science_HOLD':True,'cause_identified':False,'old_failure_repaired':False,'new_GPU_jobs':0,'new_GPU_seconds':0,'new_scientific_trials':0,'Slurm_queries':0,'production_ready':False,'final_release':False,'no_state_Git_canonical_P_writes':True,'blockers':['Frozen v1 design validator accepts nine independently mutated bound/receipt/criteria fields; separately versioned stronger CPU contract required before calling predicate complete.','Full200 runtime implementation, exact AST/source/model/data closure, actual-P readiness, storage bound, native lock/CAS/ACK/duplicate protection remain unimplemented and require root review/authorization.','Current evidence cannot determine old query9 pre-policy arrays or intermediate hidden state; old200 remains HOLD.'],'inputs':inputs}
 out('independent_review_v1.json',report)
 print(json.dumps({'status':report['status'],'checks':len(checks),'author_checks':1235,'design_counterexamples':len(boundary),'real_old200_t0_mismatch_pairs':len(mismatches),'production_ready':False}))
except BaseException as e:
 out('audit_v1_failure.json',{'error':str(e),'traceback':traceback.format_exc(),'checks':checks,'new_GPU_jobs':0,'new_scientific_trials':0});raise

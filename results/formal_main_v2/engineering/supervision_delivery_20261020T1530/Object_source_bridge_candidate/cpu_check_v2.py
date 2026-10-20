import sys,json,hashlib,importlib.util,io,contextlib,traceback,copy
from pathlib import Path
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=Path(__file__).parent
sys.path.insert(0,str(R/'src'))
def module(path):
 spec=importlib.util.spec_from_file_location('check_'+path.stem,path);m=importlib.util.module_from_spec(spec);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
assert hashlib.sha256((D/'bridge_v2.py').read_bytes()).hexdigest()=='8785b42fe62dd513f796871875547c894de972516ac9762ad60a89d3df9a7c8e'
bridge=module(D/'bridge_v2.py');p=bridge.policy();factory=module(R/p['references']['original_factory']['path'])
OUT=D/'attempt02';OUT.mkdir(exist_ok=False)
checks=[]
def record(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail));return bool(ok)
def invoke(f,label):
 log=io.StringIO();rc=None
 with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
  try:rc=f()
  except BaseException:traceback.print_exc();rc=99
 (OUT/(label+'.log')).write_text(log.getvalue());return rc,log.getvalue()
def args(name):return ['--project-root',str(R),'development','--suite','libero_object','--methods','A256_seed23','B256_seed23','--source-inventory','results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','--output',(OUT/name).relative_to(R).as_posix()]
rc,log=invoke(lambda:factory.main(args('original_rejected.json')),'original_factory')
record('original_consumer_failure_preserved',rc==2 and 'metadata history does not cover every allocation' in log,dict(returncode=rc))
ev=factory.Evidence(R);facade=bridge.auditor(ev)
(OUT/'bounded_source.diff').write_text(facade.source_diff)
factory.source_review_module=lambda evidence:bridge.auditor(evidence)
rc,log=invoke(lambda:factory.main(args('development.json')),'bridge_factory')
record('real_R_factory_all_original_scientific_gates',rc==0,dict(returncode=rc))
refs=p['references'];read=lambda k:json.loads((R/refs[k]['path']).read_text())
docs={'saved':read('final_root'),'independent':read('final_independent'),'recovery_root':read('recovery_root'),'recovery_independent':read('recovery_independent'),'failure':read('failure'),'recovery_authorization':read('recovery_authorization'),'continuous_authorization':read('continuous_authorization')}
def reject(name,fn):
 try:fn()
 except (ValueError,KeyError,TypeError) as e:return record(name,True,type(e).__name__+': '+str(e))
 except BaseException as e:return record(name,False,'wrong exception '+repr(e))
 return record(name,False,'unexpected admission')
try:record('document_positive_real_source_chain',bridge.validate_documents(p,**copy.deepcopy(docs))==set(p['successful_job_ids']))
except BaseException as e:record('document_positive_real_source_chain',False,repr(e))
mutations=[
 ('reject_added_normal_metadata_for_failed',lambda x:x['saved']['runtime_compatibility_history'].update({'3028460':x['saved']['runtime_compatibility_history']['3039258']})),
 ('reject_missing_successful_metadata',lambda x:x['saved']['runtime_compatibility_history'].pop('3039258')),
 ('reject_missing_failure_history',lambda x:x['saved']['startup_failure_history'].clear()),
 ('reject_unknown_failed_job',lambda x:x['saved']['startup_failure_history'].update({'3028468':x['failure']})),
 ('reject_failed_GPU_cost_dropped',lambda x:x['saved'].update(pair_allocated_gpu_seconds=58833)),
 ('reject_incorrect_independent_status',lambda x:x['independent'].update(status='passed')),
 ('reject_unbound_independent_root',lambda x:x['independent']['root_review'].update(sha256='0'*64)),
 ('reject_missing_independent_failure_reconstruction',lambda x:x['independent'].update(historical_failure_preserved_and_rebuilt=False)),
 ('reject_changed_frozen173',lambda x:x['independent'].update(all173_R_S_and_mirror_match=False)),
 ('reject_AB_initialization_order_mismatch',lambda x:x['independent'].update(same_AB_initialization_and_full40000_order=False)),
 ('reject_independent_failed_bill_dropped',lambda x:x['independent']['cost'].update(retained_failed_GPU_seconds=0)),
 ('reject_missing_allocation_in_bill',lambda x:x['independent']['cost']['allocations'].pop(0)),
 ('reject_changed_recovery_boundary',lambda x:x['recovery_root'].update(completed_by_arm={'A':500,'B':0})),
 ('reject_missing_recovery_independent',lambda x:x['recovery_independent'].update(status='pending')),
 ('reject_failure_claiming_trained_sample',lambda x:x['failure'].update(completed_by_arm={'A':1,'B':0})),
 ('reject_other_failure_authorization',lambda x:x['recovery_authorization'].update(failed_job_id='3028468')),
 ('reject_unbound_continuous_recovery',lambda x:x['continuous_authorization'].update(recovery_job_id='3039999')),
 ('reject_other_continuous_pair',lambda x:x['continuous_authorization'].update(pair_key='libero_object_k256_seed41')),
 ('reject_selected_checkpoint_substitution',lambda x:x['independent']['actual_checkpoint_hashes'][0]['best'].update(sha256='0'*64)),
 ('reject_selected_update_substitution',lambda x:x['independent']['actual_checkpoint_hashes'][0].update(selected_update=4500)),
 ('reject_missing_selected_arm',lambda x:x['independent']['actual_checkpoint_hashes'].pop())]
for name,mut in mutations:
 x=copy.deepcopy(docs);mut(x);reject(name,lambda x=x:bridge.validate_documents(p,**x))
if (OUT/'development.json').exists():
 manifest=json.loads((OUT/'development.json').read_text());rows=manifest['methods'];jobs=docs['saved']['registered_pair_jobs_at_review'];kw=dict(suite='libero_object',pair=p['pair'],method_rows=rows,relevant=jobs)
 bridge.scope_guard(p,**kw);record('scope_positive_exact_three_allocations',True)
 for name,mut in [
  ('reject_wrong_suite',lambda x:x.update(suite='libero_goal')),
  ('reject_changed_pair',lambda x:x['pair'].update(seed=41)),
  ('reject_A_only',lambda x:x['method_rows'].pop()),
  ('reject_drop_failed_allocation',lambda x:x['relevant'].pop(0)),
  ('reject_duplicate_allocation',lambda x:x['relevant'].append(copy.deepcopy(x['relevant'][0]))),
  ('reject_failed_as_completed',lambda x:x['relevant'][0].update(status='COMPLETED',exit_code='0:0')),
  ('reject_changed_failure_bill',lambda x:x['relevant'][0].update(elapsed_seconds=0)),
  ('reject_selected_identity_sha',lambda x:x['method_rows'][0]['identity'].update(checkpoint_sha256='0'*64))]:
  x=copy.deepcopy(kw);mut(x);reject(name,lambda x=x:bridge.scope_guard(p,**x))
 proof=json.loads((OUT/'development.json.evidence.json').read_text())['source_provenance']
 factory2,planner2=bridge.control_modules(factory.Evidence(R))
 record('explicit_factory_planner_binding_no_original_mutation',factory2.source_review_module is bridge.auditor and planner2.provenance_helper is bridge.auditor)
 evidence2=factory.Evidence(R);aa=bridge.auditor(evidence2)
 rebuilt=aa.derived.review_source_provenance(evidence2,registration=json.loads((R/'configs/experiments/formal_main_v2.json').read_text()),suite='libero_object',inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text()),method_rows=manifest['methods'],jobs=proof['registered_source_jobs'])
 record('terminal_consumer_rebuilds_identical_versioned_source_proof',rebuilt==proof)
 reject('final_invocation_not_enabled',lambda:aa.review_invocation(evidence2,job={'suite':'libero_object','mode':'final'},invocation={'method_ids':p['method_ids']}))
 record('proof_explicit_new_version' ,proof['version']==bridge.VERSION and proof['startup_failure_source_bridge']['normal_metadata_fabricated'] is False)
 record('proof_keeps_failed_allocation',set(proof['method_bindings']['A256_seed23']['registered_training_job_ids'])==set(p['all_job_ids']))
 record('proof_CPU_only_no_final',proof['startup_failure_source_bridge']['new_GPU_runs']==0 and proof['startup_failure_source_bridge']['test_opened'] is False)
record('original_consumer_bytes_unchanged',hashlib.sha256((R/refs['original_consumer']['path']).read_bytes()).hexdigest()==refs['original_consumer']['sha256'])
record('factory_bytes_unchanged',hashlib.sha256((R/refs['original_factory']['path']).read_bytes()).hexdigest()==refs['original_factory']['sha256'])
summary=dict(status='passed' if all(x['passed'] for x in checks) else 'failed',CPU_checks=len(checks),passed=sum(x['passed'] for x in checks),checks=checks,GPU_runs=0,Slurm_submissions=0,state_writes=False,canonical_writes=False,scientific_result_claimed=False,root_admission=False)
(OUT/'cpu_checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:summary[k] for k in ('status','CPU_checks','passed','GPU_runs','Slurm_submissions','root_admission')}))
if not all(x['passed'] for x in checks):print(json.dumps([x for x in checks if not x['passed']],ensure_ascii=False))
raise SystemExit(0 if summary['status']=='passed' else 2)

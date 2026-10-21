from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,importlib.util,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/object_terminal_independent_20261021T0334';B='results/formal_main_v2/preflight/heartbeat_20261021T1134'
BRIDGE='.local/object_terminal_pull_bridge_20261021T0334/bridge.py';BRIDGE_SHA='191745c8b7bcd82a165849ce8680a990da4f5de53d3204f9cdbb51f598cc7e49'
ROOT_REVIEW=B+'/Object_terminal_review.json';ROOT_SHA='07b9c955b5e625dd4cd48fdf0ab8224b0e8d0e8d035190d4cd9d250ae25543d1'
STATE_SHA='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa'
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'scripts/ops/formal_object_single_error_v1'),str(S/'src')]
checks=[];negative=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(name,ok):
 if not ok:raise AssertionError(name)
 checks.append(dict(name=name,passed=True))
def exact(n,pin):
 p=R/n;ck('pin:'+n,p.resolve()==p and h(p)==pin);return p.read_bytes()
def save(n,v):(D/n).open('x',encoding='utf-8').write(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n')
def ref(p):return {'path':str(p.relative_to(R)),'sha256':h(p),'bytes':p.stat().st_size}
try:
 source=exact(BRIDGE,BRIDGE_SHA);root_saved=json.loads(exact(ROOT_REVIEW,ROOT_SHA))
 spec=importlib.util.spec_from_file_location('_object_exact_terminal_bridge_independent',R/BRIDGE);bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
 from cti_vla.evaluation import formal_trials as M
 ck('preloaded_exact_scientific_S_module',Path(M.__file__).resolve()==S/'src/cti_vla/evaluation/formal_trials.py')
 import reviewer as Q
 import constants as C
 import fixed as F
 ck('canonical_original_reviewer_unmodified',h(Path(Q.__file__))=='c0aa1fc3d7c1607032897d7eede009bb989753daf58911d2b3351b4df7a030a2')
 raw_state=exact('results/experiment_supervisor/state.json',STATE_SHA);state=json.loads(raw_state)
 observation=json.loads(exact(B+'/initial_observation.json','0c0520630396e633c5b417a401da18bd100974e79d5f962308cf892bd945ac41'))
 basis=json.loads(exact(B+'/terminal_analysis_projection_basis.json','41d5019d4f47cfe180dc57ffbb5ab698e05ad2c845657064295862f05a7a2ac5'))
 projected=json.loads(exact(bridge.ANALYSIS,bridge.ANALYSIS_SHA));reconstructed=copy.deepcopy(state);expected_changes=[]
 for j in reconstructed['registered_jobs']:
  if j['job_id'] not in ('3054409','3054717'):continue
  a=observation['projection']['observation']['rows'][j['job_id']];patch={k:a[k] for k in ('status','exit_code','elapsed_seconds','gpus','node','allocation')};patch['raw_status']=a['status']
  expected_changes.append(dict(job_id=j['job_id'],before={k:j.get(k) for k in patch},after=patch));j.update(patch)
 ck('analysis_projection_exact_saved_accounting_only',projected==reconstructed and expected_changes==basis['changes'] and basis['persisted_state_unchanged'] is True and basis['original_state_sha256']==STATE_SHA)
 pull=json.loads(exact(bridge.PULL,bridge.PULL_SHA));base=str(Path(bridge.PULL).parent);before=json.loads((R/base/'inventory_before.json').read_bytes());after=json.loads((R/base/'inventory_after.json').read_bytes())
 required=json.loads(exact('.local/object_terminal_independent_20261021T0334/pull_required_files.json','4a96ff490da5aae69722c1b057f35dcf90ca2e43d9e8a842bc2fa8de24c33a4d'))
 ck('whole_exact13_pull_equals_independent_P_inventory',{r['relative']:(r['sha256'],r['bytes']) for r in pull['files']}=={r['path']:(r['sha256'],r['bytes']) for r in required['files']} and len(pull['files'])==13 and before==after)
 for row in required['files']:
  n=row['path'];a=R/n;b=P/n;ck('actual_R_P_terminal_bytes:'+n,a.resolve()==a and b.resolve()==b and a.read_bytes()==b.read_bytes() and h(a)==row['sha256'] and a.stat().st_size==row['bytes'])
 old,helper,evidence,_,_,_,_=Q.validators(project=R);scheduler=C.load(R,C.SCHEDULER,C.SCHEDULER_SHA)
 registered=[j for j in projected['registered_jobs'] if j['job_id']=='3054409'];ck('unique_registered_current_attempt',len(registered)==1)
 job=dict(registered[0],mode='development',suite='libero_object',method_ids=list(F.METHODS),source_sha256=scheduler.FROZEN_SHA256,adapter_sha256=C.LEGACY_SHA,execution_manifest_sha256=F.PINS[F.MANIFEST])
 jobs=[dict(j,mode='development') if j['job_id']=='3054409' else j for j in scheduler.formal_jobs(projected)]
 original_result=old.pulled_candidate(helper.Evidence(R),scheduler,job,bridge.PULL,jobs)
 positive=bridge.extend_verified(old.pulled_candidate,helper.Evidence(R),scheduler,job,bridge.PULL,jobs)
 ck('actual_positive_calls_original9_then_exact4',len(original_result['files'])==9 and len(positive['files'])==13 and set(positive['files'])==set(original_result['files'])|set(bridge.FOUR))
 ck('original_candidate_fields_untouched',all(positive[k]==v for k,v in original_result.items() if k!='files') and all(positive['files'][k]==v for k,v in original_result['files'].items()))
 # In-memory predicate counterexamples only. Metadata read views are deliberately
 # mutated while watch() retains the actual immutable-file digest, to exercise
 # deeper semantic guards rather than merely the outer exact receipt SHA.
 # These fixtures are never persisted as production pull/ledger evidence.
 class View:
  def __init__(self,documents):self.documents=documents;self.delegate=helper.Evidence(R)
  def read(self,n):return copy.deepcopy(self.documents[n]) if n in self.documents else self.delegate.read(n)
  def watch(self,n):return self.delegate.watch(n)
  def path(self,n):return self.delegate.path(n)
 def run_negative(name,mutate=None,job_patch=None,pull_path=None,candidate_patch=None,original_error=False):
  docs={bridge.PULL:copy.deepcopy(pull),base+'/inventory_before.json':copy.deepcopy(before),base+'/inventory_after.json':copy.deepcopy(after)};candidate=copy.deepcopy(original_result);j=copy.deepcopy(job);calls=[]
  if mutate:mutate(docs)
  if job_patch:j.update(job_patch)
  if candidate_patch:candidate_patch(candidate)
  def original(*args):
   calls.append('original_guard_called')
   if original_error:raise ValueError('independent original guard sentinel')
   return candidate
  try:bridge.extend_verified(original,View(docs),scheduler,j,pull_path or bridge.PULL,jobs)
  except ValueError as e:
   negative.append(dict(name=name,passed=True,error=str(e),original_guard_calls=len(calls),synthetic_metadata_view_only=True));return
  raise AssertionError('negative was not rejected: '+name)
 journal=sorted(bridge.FOUR)[0]
 def selected(docs,which,rel=journal):return next(r for r in docs[which]['files'] if r['relative']==rel)
 run_negative('different_job',job_patch={'job_id':'3054410'})
 run_negative('different_pull_path',pull_path=bridge.PULL.replace('0334','0335'))
 run_negative('original_guard_failure_propagates_before_supplement',original_error=True)
 run_negative('missing_journal',lambda d:d[bridge.PULL]['files'].remove(selected(d,bridge.PULL)))
 run_negative('extra_journal',lambda d:d[bridge.PULL]['files'].append(dict(selected(d,bridge.PULL),relative=journal+'.extra')))
 run_negative('duplicate_journal',lambda d:d[bridge.PULL]['files'].append(copy.deepcopy(selected(d,bridge.PULL))))
 run_negative('duplicate_conflicting_journal',lambda d:d[bridge.PULL]['files'].append(dict(selected(d,bridge.PULL),sha256='0'*64)))
 run_negative('missing_inventory_journal',lambda d:[d[n]['files'].remove(selected(d,n)) for n in (base+'/inventory_before.json',base+'/inventory_after.json')])
 run_negative('extra_inventory_journal',lambda d:[d[n]['files'].append(dict(selected(d,n),relative=journal+'.extra')) for n in (base+'/inventory_before.json',base+'/inventory_after.json')])
 run_negative('before_after_inventory_changed',lambda d:d[base+'/inventory_after.json']['files'].pop())
 run_negative('inventory_digest_mismatch',lambda d:d[bridge.PULL].update(inventory_sha256='0'*64))
 run_negative('original_projection_only8',candidate_patch=lambda c:c['files'].pop(next(iter(c['files']))))
 run_negative('original_projection_overlaps_typed_journal',candidate_patch=lambda c:(c['files'].pop(next(iter(c['files']))),c['files'].update({journal:bridge.FOUR[journal][0]})))
 run_negative('original_projection_unknown_ninth_file',candidate_patch=lambda c:(c['files'].pop(next(iter(c['files']))),c['files'].update({'results/formal_main_v2/unknown.json':'0'*64})))
 for rel in sorted(bridge.FOUR):
  for field,value in [('job_ids',['3054410']),('job_ids',['3054409','3054409']),('path',str(P/rel)+'.other'),('bytes',bridge.FOUR[rel][1]+1),('sha256','0'*64)]:
   def mutate(d,rel=rel,field=field,value=value):
    for n in (bridge.PULL,base+'/inventory_before.json',base+'/inventory_after.json'):selected(d,n,rel)[field]=value
   run_negative(Path(rel).name+':'+field+':'+repr(value),mutate)
  run_negative(Path(rel).name+':unverified_action',lambda d,rel=rel:selected(d,bridge.PULL,rel).update(action='copied_unverified'))
 for when in ['accounting_before','accounting_after']:
  for field,value in [('status','RUNNING'),('exit_code','1:0'),('elapsed_seconds',327),('gpus',2)]:
   run_negative(when+':'+field,lambda d,when=when,field=field,value=value:d[bridge.PULL][when]['jobs']['3054409'].update({field:value}))
 suite=dict(schema='formal_main_v2',kind='Object3054409_exact_four_journal_bridge_independent_tests',status='passed',bridge_sha256=BRIDGE_SHA,actual_positive_original9_plus4=True,positive_checks=2,negative_count=len(negative),negative_tests=negative,fixtures_scope='In-memory semantic guard isolation only, no production ledger/pull modifications or synthetic evidence acceptance.',canonical_changes=False,actual_runtime_interpretation_unchanged=True)
 save('bridge_guard_tests.json',suite)
 # Complete real source/config/checkpoint/full600/report/raw/typed lifecycle
 # original reconstruction; no input substitution, boolean consumer stub, or
 # synthetic ledger is used in these two calls.
 actual_review=bridge.review();ck('full_original_review_exact_root_receipt',actual_review==root_saved)
 consumed=bridge.consume(dict(path=ROOT_REVIEW,sha256=ROOT_SHA));ck('full_original_consume_reconstruction_exact',consumed==actual_review==root_saved)
 orig=consumed['original_review']
 ck('eligible_new_completed_attempt_and_same_cell',orig['status']=='passed_raw_reconstruction' and orig['actual_status']=='completed' and orig['actual_success'] is True and orig['logical_trial_id']==F.CELL)
 ck('all601_attempts_preserved_599legacy_plus1current',orig['legacy_equivalent_trials']==599 and orig['actual_current_trials']==1 and orig['original_historical_trials']==600 and orig['all_attempts_retained']==601 and orig['logical_success_count']==521)
 ck('original_full600_summary_stays_partial1',orig['original_full_summary']['expected_trials']==600 and orig['original_full_summary']['completed_trials']==1 and orig['original_full_summary']['status']=='incomplete' and orig['scientific_complete_inferred_from_original_partial_report'] is False)
 ck('GPU_cost6713_plus326_once',orig['legacy_GPU_seconds']==6713 and orig['new_allocation_GPU_seconds']==326 and orig['unique_total_GPU_seconds']==7039 and orig['cost']['all_attempt_gpu_seconds']==326 and len(orig['cost']['allocations'])==1 and orig['cost']['allocations'][0]['job_id']=='3054409')
 ck('immutable_runtime_controller_consumer_claims_no_synthetic',orig['runtime_structure']['runtime']['synthetic_input'] is False)
 ck('all13_used_raw_evidence_bound',all(orig['evidence_sha256'].get(r['path'])==r['sha256'] for r in required['files']))
 ck('no_new_final_release',orig['final_allowed'] is False and consumed['final_release'] is False)
 ck('state_unchanged_during_all_private_checks',(R/'results/experiment_supervisor/state.json').read_bytes()==raw_state)
 ck('bridge_and_canonical_sources_unchanged',h(R/BRIDGE)==BRIDGE_SHA and h(Path(Q.__file__))==bridge.REVIEW_SHA and h(R/'scripts/review_formal_downstream.py')==bridge.OLD_SHA)
 ck('legacy_pulled_candidate_binding_restored',old.pulled_candidate.__name__=='pulled_candidate' and old.pulled_candidate.__code__.co_filename==str(R/'scripts/review_formal_downstream.py'))
 save('original_consumer_reconstructed.json',consumed)
 diag=json.loads((D/'logical_view_diagnostics_v2.json').read_bytes())
 history=[json.loads(x) for x in (R/F.RUN/'trials.jsonl').read_bytes().splitlines()];results={r['trial_id']:r for r in history if r['event']=='result'}
 paired=collections=None
 ab={'both_success':0,'A_only':0,'B_only':0,'both_failure':0}
 for state_row in json.loads((R/F.RUN/'panel.json').read_bytes())['states']:
  a=results[state_row['trial_id']+':A128_seed17']['success'];b=results[state_row['trial_id']+':B128_seed17']['success'];key='both_success' if a and b else 'A_only' if a else 'B_only' if b else 'both_failure';ab[key]+=1
 ck('all100_AB_paired_initial_states_retained',sum(ab.values())==100 and ab['both_success']+ab['A_only']==98 and ab['both_success']+ab['B_only']==96)
 report=dict(schema='formal_main_v2',kind='Object3054409_terminal_independent_review',status='passed',reviewed_by='independent',job_id='3054409',blockers=[],source173_verified_by_original_full_input_reconstruction=True,canonical_reviewer_sha256=bridge.REVIEW_SHA,original_pull_guard_sha256=bridge.OLD_SHA,bridge_source=ref(R/BRIDGE),scope='Original unchanged reviewer and consumer fully reconstructed with exact frozen S import context and independently checked four-journal metadata projection supplement. Unassisted canonical review failures retained; no production/runtime source changed.',full_original_review_reconstructed=True,full_original_consumer_reconstructed=True,strict_four_journal_supplement_required=True,raw_P_R_all13_equal=True,root_review=ref(R/ROOT_REVIEW),pull_receipt=ref(R/bridge.PULL),analysis_projection=ref(R/bridge.ANALYSIS),projection_basis=ref(R/B/'terminal_analysis_projection_basis.json'),original_consumer_reconstruction=ref(D/'original_consumer_reconstructed.json'),raw_precheck=ref(D/'raw_precheck.json'),typed_P_reconstruction=ref(D/'typed_P_reconstruction.json'),original_failures=[ref(R/B/'Object_original_terminal_review_failure.json'),ref(D/'canonical_review_S_attempt.json')],source_origin_diagnosis=ref(D/'source_origin_diagnosis.json'),amplitude_diagnostic_correction=ref(D/'logical_view_diagnostics_v2.json'),bridge_guard_tests=ref(D/'bridge_guard_tests.json'),trials=dict(legacy_equivalent=599,current=1,logical_complete_view=600,historical_attempts=601,original_policy_error_preserved=1,unique_initial_states=100,tasks=10,original_whole600_not_retroactively_admitted=True),successes=dict(legacy=520,current=1,logical=521,logical_negative_outcomes=79),current_raw=dict(status='completed',success=True,chunks=19,executed_actions=145,policy_calls=19,raw_sha256=orig['raw_sha256']),per_method=diag['methods'],per_task=diag['per_task'],paired_AB=dict(initial_states=100,counts=ab,B_minus_A_percentage_points=-2.0),cost=dict(legacy_allocation_ids=list(F.JOBS),legacy_GPU_seconds_once=6713,new_job_id='3054409',new_GPU_seconds_once=326,total_GPU_seconds_once=7039,scope='Four actual allocations counted once; new elapsed time is not added again to existing global accounting.'),old_unrecorded_eighth_query_payload_unknown=True,original_error_not_erased=True,current_attempt_no_retry=True,root_admission_pending=True,final_allowed=False,final_release=False,source_or_config_changes=False,new_GPU_submissions=0,new_Slurm_queries=0,state_writes=False,Git_writes=False,CPU_guard_negative_tests=len(negative),check_count=len(checks),checks=checks,utc=datetime.now(timezone.utc).isoformat())
 save('independent_review.json',report)
 print(json.dumps(dict(status='passed',checks=len(checks),guard_negative_tests=len(negative),independent_review_sha256=h(D/'independent_review.json'),consumer_reconstruction_sha256=h(D/'original_consumer_reconstructed.json'))))
except BaseException as error:
 save('full_consumer_audit_failure.json',dict(status='failed',error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc(),checks=checks,negative_tests=negative,scientific_acceptance=False,new_GPU_submissions=0,new_Slurm_queries=0));raise

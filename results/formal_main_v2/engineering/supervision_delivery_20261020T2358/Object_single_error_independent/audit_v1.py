"""Independent CPU-only audit of the frozen Object single-error candidate."""
from pathlib import Path
import ast,collections,copy,hashlib,importlib.util,io,json,os,sys,traceback,types,contextlib
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/object_single_error_candidate_20261020T2253'
O=R/'.local/object_single_error_independent_20261020T2358'
ARCH=R/'results/formal_main_v2/engineering/supervision_delivery_20261020T2253/Object_single_error_candidate'
MP='fd5af505956b76add76fbd2e2ad3d8fff4f5910ae6e8cdf9e95d662d20b2dec7'
checks=[];extra=[];limits=[];watched={}
def h(b):return hashlib.sha256(b).hexdigest()
def verify(p,pin=None):
 p=Path(p);b=p.read_bytes()
 if pin is not None:assert h(b)==pin,str(p)
 watched[str(p)]={'sha256':h(b),'bytes':len(b)}
 return b
def check(label,value):
 if not value:raise AssertionError(label)
 checks.append(label)
def publish(name,row):
 data=(json.dumps(row,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
 p=O/name
 with p.open('xb') as f:f.write(data)
 return {'path':p.relative_to(R).as_posix(),'sha256':h(data),'bytes':len(data)}
def audit_io(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','socket.bind'):
  raise AssertionError('Independent CPU audit prohibits external execution/network: '+event)
 if event=='open':
  path,mode,flags=args
  write=isinstance(mode,str) and any(x in mode for x in 'wax+')
  write=write or isinstance(flags,int) and bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if write and not isinstance(path,int):assert Path(path).absolute().is_relative_to(O),'write outside private audit: '+str(path)
 if event in ('os.remove','os.rmdir','os.rename','os.mkdir'):
  for path in args[:2] if event=='os.rename' else args[:1]:
   if isinstance(path,(str,bytes)):assert Path(path).absolute().is_relative_to(O),'mutation outside private audit'
sys.addaudithook(audit_io)
def main():
 manifest=json.loads(verify(D/'delivery_manifest.json',MP))
 check('18 exact manifest entries',manifest['file_count']==len(manifest['files'])==18)
 check('explicit CPU and production HOLD',not manifest['production_admitted'] and not manifest['actual_P_verified'] and not manifest['production_write_performed'])
 for row in manifest['files']:
  b=verify(R/row['path'],row['sha256']);check('candidate size:'+row['path'],len(b)==row['bytes'])
  check('archive exact bytes:'+row['path'],verify(ARCH/Path(row['path']).name)==b)
 check('archive original manifest exact',verify(ARCH/'delivery_manifest_original.json')==verify(D/'delivery_manifest.json'))
 # Read and execute the exact original author tests with output redirected into memory.
 sys.path.insert(0,str(D));sys.path.insert(0,str(R/'src'))
 import fixed as F, iterator as I,gate as G,terminal as T
 from cti_vla.evaluation import formal_trials as M,libero_runtime as L
 import numpy as np
 module=types.ModuleType('_independent_object_author_tests');module.__file__=str(D/'test_cpu.py')
 exec(compile(verify(D/'test_cpu.py','b370dbc10a78caf746e801394489913a8041aaef367b7db8dc5a1add4f1f3ec2'),str(D/'test_cpu.py'),'exec'),module.__dict__)
 captured={};module.publish=lambda name,row:captured.__setitem__(name,copy.deepcopy(row))
 stdout=io.StringIO()
 with contextlib.redirect_stdout(stdout):module.main()
 saved_tests=json.loads((D/'cpu_tests.json').read_bytes())
 check('author 24 positive and 74 negative reproduced exactly',captured['cpu_tests.json']==saved_tests and saved_tests['positive_checks']==24 and saved_tests['negative_checks']==74)
 oldfixture=json.loads((D/'cpu_gate_fixtures.json').read_bytes());fixture=copy.deepcopy(captured['cpu_gate_fixtures.json'])
 oldfixture['all_modes_snapshot'].pop('captured_utc');fixture['all_modes_snapshot'].pop('captured_utc')
 check('all author fixtures exact except UTC',oldfixture==fixture)
 publish('author_cpu_reproduction.json',{'status':'passed','positive':24,'negative':74,'checks':captured['cpu_tests.json'],'synthetic_fixture_only':True,'stdout':stdout.getvalue(),'production_admitted':False,'GPU_calls':0,'new_scientific_trials':0})
 inputs=F.load_inputs(M);scope=inputs['scope']
 check('scope regenerated from actual sources',F.sig(scope)==F.SCOPE_SHA==h(verify(D/'scope.json')))
 # Separate reconstruction of all raw identities and proof references.
 raw=verify(R/F.RUN/'trials.jsonl',F.PINS[F.RUN+'/trials.jsonl'])
 check('actual P old raw600 matches exact R',verify(P/F.RUN/'trials.jsonl')==raw)
 for n in ('config.json','panel.json'):
  check('actual P original '+n,verify(P/F.RUN/n)==verify(R/F.RUN/n,F.PINS[F.RUN+'/'+n]))
 lines=raw.splitlines(keepends=True);rows=[json.loads(x) for x in lines]
 panel=inputs['panel'];methods=('dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17')
 expected={state['trial_id']+':'+mid:(state,mid) for state in panel['states'] for mid in methods}
 starts={};results={};owner={};job=None;invocations=[];offsets=[];offset=0
 for line,row in zip(lines,rows):
  offsets.append(offset);offset+=len(line)
  if row['event']=='invocation':job=row['slurm_job_id'];invocations.append(job);continue
  check('no unmodeled historical event at '+str(len(offsets)),row['event'] in ('start','result'))
  tid=row['trial_id'];state,mid=expected[tid]
  want={'state_trial_id':state['trial_id'],'method':mid,'task_id':state['task_id'],'task_name':state['task_name'],'source_state_index':state['source_state_index'],'initial_state_sha256':state['initial_state_sha256'],'suite':'libero_object','split':'development','runtime_seed':17,'environment_seed':0,'action_chunk':8,'configured_wait_steps':10}
  check('old full trial identity at '+str(len(offsets)),all(row[k]==v for k,v in want.items()))
  if row['event']=='start':
   check('unique old start '+tid,tid not in starts);starts[tid]=row
  else:
   check('unique matched old result '+tid,tid in starts and tid not in results);results[tid]=row;owner[tid]=job
 check('all 600 identities and 3 original jobs independently reconstructed',set(starts)==set(results)==set(expected) and invocations==['3021394','3021603','3021844'])
 failed=[r for r in results.values() if r['status']!='completed']
 check('one exact policy error; raw query8 absent',len(failed)==1 and failed[0]['trial_id']==F.CELL and failed[0]['status']=='policy_error' and failed[0]['success'] is False and failed[0]['policy_calls']==8 and len(failed[0]['chunks'])==7 and len(failed[0]['executed_actions'])==56)
 normal={k:v for k,v in results.items() if v['status']=='completed'}
 per=[json.loads(x) for x in verify(R/F.OLD_PROOF/'per_trial_independent_599.jsonl',F.PINS[F.OLD_PROOF+'/per_trial_independent_599.jsonl']).splitlines()]
 check('599 independent proof exact coverage',len(per)==599 and {x['trial_id'] for x in per}==set(normal))
 for row in per:
  for event in ('start','result'):
   r=row[event];i=r['line']-1
   check('599 byte/line/index binding '+event+':'+row['trial_id'],offsets[i]==r['byte_offset'] and len(lines[i])==r['bytes'] and h(lines[i])==r['sha256'] and rows[i]['trial_id']==row['trial_id'] and rows[i]['event']==event)
  check('599 outcome/owner binding '+row['trial_id'],row['success']==normal[row['trial_id']]['success'] and row['source_job_id']==owner[row['trial_id']])
 check('599 old action/chunk counts independently counted',sum(len(x['executed_actions']) for x in normal.values())==91945 and sum(len(x['chunks']) for x in normal.values())==11720)
 proof599=json.loads(verify(R/F.PROOF_ARCHIVE,F.PINS[F.PROOF_ARCHIVE]))
 check('599 review explicitly not whole600 admission',proof599['status']=='passed' and proof599['production_reuse_authorized'] is False and proof599['whole600_compatibility_admitted'] is False)
 for key in ('original_consumer','source_history','single_failure_design','single_failure_scope_guard_addendum'):
  if key in proof599:
   ref=proof599[key];p=R/F.OLD_PROOF/Path(ref['path']).name
   if p.exists():verify(p,ref['sha256'])
 # Independently validate the sole syntactic difference and unchanged validation order.
 source=verify(R/F.LOOP,F.LOOP_SHA);orig_ast=next(x for x in ast.parse(source).body if isinstance(x,ast.FunctionDef) and x.name=='evaluate_formal_trials')
 independent=copy.deepcopy(orig_ast);outer=next(x for x in independent.body if isinstance(x,ast.For));inner=outer.body[0]
 check('fixed insertion anchor',isinstance(inner,ast.For) and ast.dump(inner.body[0],include_attributes=False)==ast.dump(ast.parse('identity = _identity(panel, state, identifier)').body[0],include_attributes=False))
 condition=ast.parse('if identity["trial_id"] != '+repr(F.CELL)+':\n    continue').body[0];inner.body.insert(1,condition);ast.fix_missing_locations(independent)
 original,derived,derivation=I.derive_loop(M,source)
 check('independent full AST equals candidate derived AST',F.sig(ast.dump(independent,include_attributes=False))==derivation['derived_ast_sha256'])
 inner.body.pop(1)
 check('remove only condition restores every original AST node',ast.dump(independent,include_attributes=False)==ast.dump(orig_ast,include_attributes=False))
 check('full panel validator precedes any filtering',isinstance(orig_ast.body[1],ast.Expr) and ast.unparse(orig_ast.body[1].value.func)=='validate_trial_identities')
 check('derived distinct from frozen original code',derivation['original_code_sha256']!=derivation['derived_code_sha256'] and M.evaluate_formal_trials is original)
 publish('source_and_raw_identity_review.json',{'status':'passed_CPU_source_identity_only','candidate_manifest_sha256':MP,'checks':checks,'all600_raw_sha256':h(raw),'legacy599_count':599,'legacy599_actions':91945,'legacy599_chunks':11720,'old_error':{'trial_id':F.CELL,'source_job_id':owner[F.CELL],'recorded_chunks':7,'policy_calls':8,'executed_actions':56,'rejected_chunk8_unknown':True},'original_allocations':scope['legacy_allocations'],'legacy_gpu_seconds':6713,'independent_AST_derivation':derivation,'full599_runtime_replay_inherited_not_repeated':True,'new_simulator_or_GPU_execution':False})
 # Supplementary boundary tests. All receipts/job identities here are explicitly synthetic.
 data=captured['cpu_gate_fixtures.json'];plan=data['plan'];base=copy.deepcopy(data['all_modes_snapshot']);now=datetime.fromisoformat(base['captured_utc']);base['captured_utc']=now.isoformat()
 def observe_case(name,call,wanted='reject',impact=None):
  try:value=call();accepted=True;reason=None
  except (ValueError,KeyError,TypeError,AssertionError) as e:value=None;accepted=False;reason=type(e).__name__+': '+str(e)
  row={'case':name,'accepted_structurally':accepted,'wanted':wanted,'error':reason,'output':value,'synthetic_only':True}
  extra.append(row)
  if wanted=='reject':check('supplementary reject:'+name,not accepted)
  elif wanted=='CPU_only_accept':check('supplementary CPU boundary:'+name,accepted)
  if impact is not None:limits.append({'case':name,'required_production_fix':impact,'structural_acceptance_observed':accepted})
  return value
 def snapshot_with(row,actual):
  s=copy.deepcopy(base);s['registered_jobs']=[row];s['slurm_rows']=[actual];return s
 reg={'job_id':'9910001','project':'CTI-VLA','mode':'linked_policy_error_correction','pair_id':F.PAIR,'logical_trial_id':F.CELL}
 actual={'job_id':'9910001','state':'FAILED','gpus':1}
 observe_case('terminal_same_cell_without_link_fields',lambda:G.check_snapshot(snapshot_with(reg,actual),plan,now),'CPU_only_accept','Native gateway must reject terminal prior correction bound by mode plus exact logical cell even when linked_result/token/output metadata is missing. Incomplete registration is HOLD, not permission for another token.')
 rg={'job_id':'9910002','project':'CTI-VLA','mode':'engineering','pair_id':'unrelated','comment':'expected-project-token'}
 ac={'job_id':'9910002','state':'RUNNING','gpus':1,'comment':'different-project-token','name':'foreign-name'}
 observe_case('Slurm_comment_name_conflict',lambda:G.check_snapshot(snapshot_with(rg,ac),plan,now),'CPU_only_accept','Real scheduler adapter must corroborate registered name/account/partition/requested GPU/output/comment and original ACK; CPU predicate currently reads only ID/state/GPU.')
 for state in ['UNKNOWN','REQUEUED','SPECIAL_UNKNOWN']:
  a=copy.deepcopy(ac);a['state']=state;observe_case('unknown_state_'+state,lambda a=a:G.check_snapshot(snapshot_with(rg,a),plan,now))
 rg2=copy.deepcopy(reg);rg2['linked_original_result_sha256']=F.RESULT['sha256'];observe_case('terminal_explicit_link_is_blocked',lambda:G.check_snapshot(snapshot_with(rg2,actual),plan,now))
 for change in [('captured_utc',(now.replace(year=now.year-1)).isoformat()),('reserved_gpu_slots',8),('pending',[{'job_id':'unknown'}]),('output_exists',True),('unknown_registered_activity',True)]:
  sn=copy.deepcopy(base);sn[change[0]]=change[1];observe_case('snapshot_'+change[0],lambda sn=sn:G.check_snapshot(sn,plan,now))
 class Empty:
  def __init__(self):self.events=[dict(event='invocation',created_utc='SYNTHETIC',slurm_job_id='9910010',run_signature=F.sig(inputs['config']))]
  def completed(self):return set()
 args=dict(panel=panel,manifest=inputs['manifest'],config=inputs['config'],policies={m:object() for m in methods},ledger=Empty(),job_id='9910010',run_signature=F.sig(inputs['config']),stop_after=None,policy_watchdog_seconds=60.,scope=scope,loop_proof=derivation)
 value=observe_case('opaque_policy_objects_structural_only',lambda:I.check_runtime_call(M,**args),'CPU_only_accept','Actual entry must verify all six exact model/checkpoint/adapter policy identities. Matching dictionary keys alone is not actual model acceptance.')
 check('opaque policy precheck never authorizes production',value['production_authorized'] is False)
 original_episode=M.run_episode
 try:
  M.run_episode=lambda *a,**kw:None
  value=observe_case('replaced_run_episode_global_structural_only',lambda:I.check_runtime_call(M,**args),'CPU_only_accept','Typed runtime must pin current action run_episode and all execution globals, and separately record original versus derived trial-loop code. The original source file hash does not prove live global binding.')
  check('altered global precheck never authorizes production',value['production_authorized'] is False)
 finally:M.run_episode=original_episode
 # Terminal parser/typed receipt inputs are not a substitute for the real consumer.
 config=copy.deepcopy(inputs['config']);sig=F.sig(config);identifier=scope['identity']
 bogus_result={**copy.deepcopy(results[F.CELL]),'status':'completed','success':True,'chunks':[],'executed_actions':[],'event':'result','run_signature':sig}
 fake_rows=[{'event':'invocation','created_utc':'SYNTHETIC','slurm_job_id':'9910010','run_signature':sig},{**identifier,'event':'start','created_utc':'SYNTHETIC','run_signature':sig},bogus_result]
 fake_raw=b''.join(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n' for x in fake_rows)
 alloc=[{'job_id':'9910010','gpus':1,'elapsed_seconds':1,'status':'COMPLETED','raw_status':'COMPLETED','exit_code':'0:0'}]
 receipts={role:{'kind':'Object_single_error_full_terminal_consumer','reviewed_by':role,'status':'passed','blockers':[],'job_id':'9910010','new_raw_sha256':F.sha(fake_raw),'original_raw_sha256':h(raw),'original_config_manifest_model_checkpoint_source_environment_guards':True,'current_action_runtime_and_adapter_provenance_verified':True,'all_chunks_trajectory_hashes_statistics_rebuilt':True,'full100_initial_state_and6_method_identity_verified':True,'old599_compatibility_root_adopted':True,'final_allowed':False,'synthetic_fixture':True} for role in ['root','independent']}
 # Do not store the fabricated 600-cell view; store only its admission flags.
 def malformed_terminal():
  result=T.assemble_candidate(inputs,fake_raw,config,alloc,formal=M,receipts=receipts)
  return {k:result[k] for k in ['status','production_admitted','root_global_release','logical_cells','legacy_equivalent_cells','current_attempt_cells','original_ledger_rewritten']}
 value=observe_case('empty_action_success_with_synthetic_receipt_flags',malformed_terminal,'CPU_only_accept','Production consumer must independently recompute every action/chunk/statistic and pin actual canonical root/independent receipt bytes. Current terminal candidate only checks supplied object flags; intentionally malformed fixture can produce a CPU view.')
 check('malformed CPU view still refuses production',value['production_admitted'] is False and value['root_global_release'] is False)
 observe_case('duplicate_new_allocation_rejected',lambda:T.account_allocations(scope['legacy_allocations'],alloc*2))
 observe_case('old_job_cannot_be_new',lambda:T.account_allocations(scope['legacy_allocations'],[{**alloc[0],'job_id':'3021844'}]))
 check('all mutable globals restored',M.run_episode is original_episode and M.evaluate_formal_trials is original)
 for row in manifest['files']:verify(R/row['path'],row['sha256'])
 verify(R/F.RUN/'trials.jsonl',F.PINS[F.RUN+'/trials.jsonl']);verify(P/F.RUN/'trials.jsonl',F.PINS[F.RUN+'/trials.jsonl'])
 publish('supplementary_CPU_boundary_tests.json',{'status':'passed_declared_CPU_scope_with_explicit_production_gaps','cases':extra,'production_limitations':limits,'all_fixtures_synthetic':True,'no_raw_ledger_fabricated_or_written':True,'new_GPU_seconds':0,'Slurm_queries':0,'production_admitted':False})
 blockers=[
  {'id':'B1_native_transaction','detail':'Exact parent/child wrapper, one-shot native writer-lock/CAS pending/ACK gateway, full all-mode capacity and original-token reconciliation remain unimplemented in this frozen package; terminal same-cell and actual scheduler provenance counterexamples must be closed.'},
  {'id':'B2_full_execution_closure','detail':'Five-file CPU core closure excludes actual entry/wrapper/gateway/reviewer/consumer. No canonical/P installation or source/model/checkpoint verify occurred. Derive-loop source proof alone does not pin live run_episode/global or policy objects.'},
  {'id':'B3_distinct_derived_provenance','detail':'Actual adapter must preserve original frozen loop code identity and separately bind one-node derived loop code; cannot store derived code under frozen_trial_loop_code_sha256.'},
  {'id':'B4_actual_terminal_consumer','detail':'True original-scientific and action-runtime consumers plus root/independent canonical typed receipts are required. Synthetic true flags can pass current CPU assembly, as explicitly demonstrated; no main-result admission is possible here.'},
  {'id':'B5_root_adoption_single_authorization','detail':'Root must explicitly adopt only599 as legacy-equivalent, retain original600/one policy_error/6713seconds, then authorize exactly one whole-from-initial-state linked trial independent of outcome; not ordinary resume and no query8 invention.'}
 ]
 report={'schema':'formal_main_v2','kind':'Object_single_error_CPU_candidate_independent_review','status':'passed_CPU_candidate_only_with_production_blockers','reviewed_by':'independent_goal_cpu_gate_2054','candidate_manifest':{'path':(D/'delivery_manifest.json').relative_to(R).as_posix(),'sha256':MP},'author_positive_checks_replayed':24,'author_negative_checks_replayed':74,'supplementary_case_count':len(extra),'independent_checks_passed':len(checks),'checks':checks,'production_blockers':blockers,'discovered_structural_boundaries':limits,'all_blockers_required_before_production':True,'production_admitted':False,'actual_P_runtime_verified':False,'new_GPU_submissions':0,'new_GPU_seconds':0,'Slurm_queries':0,'new_scientific_trials':0,'state_canonical_P_Git_writes':0,'old599_reuse_authorized':False,'whole600_adopted':False,'old_query8_known':False,'original600_raw_sha256':h(raw),'legacy_allocation_GPU_seconds':6713,'original173_R_Psnapshot_Rmirror_checked_by_reproduced_load_inputs':True,'full599_runtime_replay_inherited_not_repeated':True,'one_node_AST_filter_independently_reconstructed':True,'scope':'Audit of CPU candidate/source contracts only. Actual future production code requires a separate complete audit; synthetic boundary outputs are evidence of missing enforcement, never scientific outcomes.','utc':datetime.now(timezone.utc).isoformat()}
 publish('watched_inputs.json',watched)
 rp=publish('independent_review.json',report)
 print(json.dumps({'status':report['status'],'review':rp,'checks':len(checks),'author_replay':[24,74],'supplementary_cases':len(extra),'production_admitted':False},ensure_ascii=False))
try:main()
except BaseException as e:
 publish('audit_v1_failure.json',{'error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'checks_passed':len(checks),'checks':checks,'supplementary_cases':extra,'no_GPU_Slurm_state_P_Git_changes':True})
 raise

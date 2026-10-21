from pathlib import Path
import ast,copy,hashlib,json,sys,io,contextlib,traceback
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');A=R/'.local/goal_bounded_diagnostic_20261020T2358';D=R/'.local/goal_bounded_diagnostic_independent_20261020T2358'
H=lambda b:hashlib.sha256(b).hexdigest()
checks=[];inputs={}
def ck(b,label):
 if not b:raise AssertionError(label)
 checks.append({'check':label,'passed':True})
def rd(p,pin=None):
 p=Path(p);ck(p.resolve()==p and p.is_file(),'regular:'+str(p));b=p.read_bytes()
 if pin:ck(H(b)==pin,'SHA:'+str(p))
 inputs[str(p)]={'sha256':H(b),'bytes':len(b)};return b
def js(p,pin=None):return json.loads(rd(p,pin))
def out(n,x):
 p=D/n;ck(p.parent==D and not p.exists(),'new_private:'+n)
 b=(json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'bytes':len(b),'sha256':H(b)}
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect','socket.bind'):raise RuntimeError('No subprocess or network')
 if event=='open':
  p,mode,flags=args
  if isinstance(p,(str,bytes)) and ((mode and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(1|2|64|512|1024))):
   if not Path(p).resolve().is_relative_to(D):raise RuntimeError('Write outside private output')
 if event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.symlink','os.link','os.chmod'):
  for p in args[:2 if event in ('os.rename','os.link') else 1]:
   if isinstance(p,(str,bytes)) and not Path(p).resolve().is_relative_to(D):raise RuntimeError('Mutation outside private output')
sys.addaudithook(guard)
try:
 prev=js(D/'independent_review_v1.json','935c24b0eb2e5ea19dc3524e045310d3a67a91e0adb2b3e8670f17d0b4331262')
 ck(prev['checks_passed']==1751 and prev['old_hash_post_policy_verified'] and prev['old200_HOLD'] and not prev['production_ready'],'previous_actual_evidence_review_scope')
 m=js(A/'delivery_manifest_v3.json','25ca8079785f3409d35be85e7a62044ec20e6674b1c36ffbefcc66056a66ed18')
 ck(m['file_count']==len(m['files'])==31,'31file_v3_manifest')
 for n,v in m['files'].items():
  ck(Path(n).name==n,'flat_name:'+n);b=rd(A/n,v['sha256']);ck(len(b)==v['bytes'],'size:'+n)
 old=js(A/'delivery_manifest_v2.json','84a3b3c3695f437b63898ed3be9e07857910940be82b8db51437376c2771ee29')
 ck(all(m['files'][k]==v for k,v in old['files'].items()),'all_v2_files_unchanged_in_v3')
 src=rd(A/'build_prospective_specification_v2.py','c8f64e3ee1f4c6d07aa12e7afd2ecd75847c391987fddecdf1d14e25be96e8bf')
 oldsrc=rd(A/'build_prospective_specification.py','75379ac29257a706729262873bb9e9d875dd66edabeea882c1f3ab5cd8b48e63')
 tree=ast.parse(src);oldtree=ast.parse(oldsrc)
 def assigned(t,name):return next(n.value for n in t.body if isinstance(n,ast.Assign) and any(isinstance(q,ast.Name) and q.id==name for q in n.targets))
 def dump(n):return ast.dump(n,include_attributes=False)
 ck(dump(assigned(tree,'protocol'))==dump(assigned(oldtree,'protocol')),'entire_protocol_AST_identical')
 ck(dump(assigned(tree,'REQUIRED'))==dump(assigned(oldtree,'REQUIRED')),'all_required_gates_AST_identical')
 for f in [n.name for n in oldtree.body if isinstance(n,ast.FunctionDef) and n.name!='validate_design']:
  x=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==f);y=next(n for n in oldtree.body if isinstance(n,ast.FunctionDef) and n.name==f)
  ck(dump(x)==dump(y),'non_validator_function_unchanged:'+f)
 idx=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='panel' for t in n.targets))
 ns={'__name__':'independent_goal_spec_v2_reproduction','__file__':str(A/'build_prospective_specification_v2.py')}
 exec(compile(ast.Module(body=tree.body[:idx],type_ignores=[]),str(A/'build_prospective_specification_v2.py'),'exec'),ns)
 captures={}
 def write(n,v):
  ns['check'](n not in captures and Path(n).name==n,'private nonoverwrite '+n)
  captures[n]=json.loads(json.dumps(v,allow_nan=False))
 ns['write']=write;sout=io.StringIO()
 with contextlib.redirect_stdout(sout):exec(compile(ast.Module(body=tree.body[idx:],type_ignores=[]),str(A/'build_prospective_specification_v2.py'),'exec'),ns)
 ck(len(captures)==3,'three_v2_outputs_captured_only')
 for n,v in captures.items():ck(v==js(A/n),'exact_reproduced_v2_output:'+n)
 tests=captures['prospective_specification_CPU_tests_v2.json'];ck(tests['positive_tests']==1 and tests['rejection_tests']==30 and all(t['rejected'] for t in tests['negative_tests']),'one_positive30_rejections_reproduced')
 ck(rd(A/'prospective_full200_specification_v2.json')==rd(A/'prospective_full200_specification.json') and H(rd(A/'prospective_full200_specification.json'))=='ed0b59bd1acbdab34658f5599f4969aa745e596348bf25d230a38c978aa652ad','actual_spec_bytes_unchanged')
 spec=ns['protocol'];assert ns['validate_design'](spec,ns['rows'],ns['methods'],ns['environment'])
 mutations=[
 ('old_gap_max_control_steps',lambda p:p.update(maximum_control_steps=60001)),
 ('old_gap_max_policy_queries',lambda p:p.update(maximum_policy_queries=7601)),
 ('old_gap_stop_after',lambda p:p.update(stop_after_trial_count=58)),
 ('old_gap_watchdog',lambda p:p.update(policy_watchdog_seconds=1)),
 ('old_gap_rows_signature',lambda p:p.update(rows_signature_sha256='0'*64)),
 ('old_gap_panel_sha',lambda p:p.update(panel_sha256='0'*64)),
 ('old_gap_pass_criteria',lambda p:p.update(pass_criteria=[])),
 ('old_gap_fail_criteria',lambda p:p.update(fail_criteria=[])),
 ('old_gap_retrospective_no_auto',lambda p:p['retrospective_branch'].update(no_automatic_transition=False)),
 ('fractional_query_bound',lambda p:p.update(maximum_policy_queries=7600.0)),
 ('float_trial_stop',lambda p:p.update(stop_after_trial_count=200.0)),
 ('gate_order_changed',lambda p:p['required_future_gates'].reverse()),
 ('duplicate_gate',lambda p:p['required_future_gates'].append(p['required_future_gates'][0])),
 ('missing_panel_hash',lambda p:p.pop('panel_sha256')),
 ('unregistered_extra_field',lambda p:p.update(auto_expand=True)),
 ('old200_auto_adopt',lambda p:p['retrospective_branch'].update(adoption_rule='adopt old after new success')),
 ('trial_initial_state_sha_changed',lambda p:p['rows'][0].update(initial_state_sha256='0'*64)),
 ('method_seed_changed',lambda p:p['method_identities'][0].update(seed=23)),
 ('max_new_attempts2',lambda p:p.update(maximum_new_attempts=2)),
 ('release_after_CPU_only',lambda p:p.update(production_ready=True))
 ]
 extra=[]
 for name,mutate in mutations:
  bad=copy.deepcopy(spec);mutate(bad)
  try:ns['validate_design'](bad,ns['rows'],ns['methods'],ns['environment'])
  except (ValueError,KeyError,TypeError) as e:extra.append({'case':name,'rejected':True,'reason':str(e)})
  else:raise AssertionError('v2 accepted independent mutation '+name)
 ck(len(extra)==20,'all20_independent_contract_mutations_rejected')
 bound={'row_count':spec['row_count'],'unique_states':spec['unique_development_states'],'stop_after_trials':spec['stop_after_trial_count'],'attempts':spec['maximum_new_attempts'],'control_steps':spec['maximum_control_steps'],'policy_queries':spec['maximum_policy_queries'],'rows_sha256':spec['rows_signature_sha256'],'panel_sha256':spec['panel_sha256'],'watchdog_seconds':spec['policy_watchdog_seconds']}
 ck(bound['row_count']==bound['stop_after_trials']==200 and bound['unique_states']==100 and bound['attempts']==1 and bound['control_steps']==60000 and bound['policy_queries']==7600 and bound['watchdog_seconds']==60.,'authoritative_frozen_prospective_limits')
 for p,v in prev['inputs'].items():ck(H(Path(p).read_bytes())==v['sha256'],'previous_actual_evidence_still_exact:'+p)
 for p,v in inputs.items():ck(H(Path(p).read_bytes())==v['sha256'],'v3_input_stability:'+p)
 testref=out('v2_contract_independent_tests.json',{'source_sha256':H(src),'actual_specification_sha256':'ed0b59bd1acbdab34658f5599f4969aa745e596348bf25d230a38c978aa652ad','author_positives_reproduced':1,'author_rejections_reproduced':30,'independent_rejections':extra,'old_nine_counterexamples_now_rejected':True,'all_scientific_specification_values_unchanged':True,'bounds':bound,'stdout':sout.getvalue(),'production_contract':False})
 remaining=[
 {'id':'G1_root_prospective_policy_choice','detail':'Root must explicitly choose a fresh entire fixed200 prospective attempt; this CPU design itself is not submission authority or evidence that old200 can be adopted.'},
 {'id':'G2_full200_runtime','detail':'Implement/version the full200 passive gate, original-loop AST preservation, correct BaseException fail-closed partial evidence handling, full model/checkpoint/data/source identity, and reject CPU fixtures in real mode.'},
 {'id':'G3_actualP_native_gateway','detail':'Independently audit actual-P exact closure and all-mode<=8 capacity, writer lock/CAS, one output/token/ACK, pending reconciliation, no prior Goal activity, no automatic retry; reserve evidence storage with full query bound.'},
 {'id':'G4_terminal_scientific_acceptance','detail':'Require actual200 ordered raw trials,100 paired initial receipts,7600-max queries with all full inputs/actions, original consumer plus distinct independent terminal review and root acceptance; preserve failed outcomes and all prior cost exactly once.'},
 {'id':'G5_retrospective_and_final_HOLD','detail':'Old200 and additional Goal science remain HOLD now. A future valid prospective200 cannot identify the old cause, adopt old200, expand remaining Goal development, or open final sealed values.'}]
 report={'schema':'formal_main_v2','kind':'Goal_bounded_CPU_diagnostic_and_prospective_design_independent_review','status':'passed','audit_scope':'CPU real-evidence diagnosis and frozen prospective200 design only; no production/runtime/GPU admission','reviewed_by':'independent_goal_cpu_gate_2054','utc':datetime.now(timezone.utc).isoformat(),'author_manifest':{'path':str((A/'delivery_manifest_v3.json').relative_to(R)),'sha256':'25ca8079785f3409d35be85e7a62044ec20e6674b1c36ffbefcc66056a66ed18','files':31},'actual_evidence_review_v1':{'path':str((D/'independent_review_v1.json').relative_to(R)),'sha256':'935c24b0eb2e5ea19dc3524e045310d3a67a91e0adb2b3e8670f17d0b4331262'},'checks_passed_this_revision':len(checks),'checks_passed_total':1751+len(checks),'checks':checks,'blockers':[],'remaining_production_gates':remaining,'actual_evidence_passed':True,'old_hash_post_policy_verified':True,'old_query9_pre_policy_values_unavailable':True,'fixed13_neighbors_excluded_only':True,'cause_identified':False,'old_failure_repaired':False,'same_t0_does_not_prove_intermediate_hidden_state':True,'old200_t0_mismatch_pair_count':1,'old200_mismatch_ordinals':[57,58],'two_engineering_trace_difference_ordinal':30,'prospective_scope_and_history_separate':True,'frozen_bounds':bound,'author_actual_evidence_checks_replayed':1235,'author_declared1234_count_erratum_retained':True,'classifier_cases_replayed':14,'original_design20_rejections_and_9_gaps_retained':True,'current_design_author_positive':1,'current_design_author_rejections':30,'independent_current_design_rejections':20,'all_old_nine_contract_gaps_closed':True,'current_contract_test_review':testref,'old200_HOLD':True,'new_Goal_science_HOLD':True,'prospective_full200_GPU_authorized':False,'production_ready':False,'new_GPU_jobs':0,'new_GPU_seconds':0,'new_scientific_trials':0,'Slurm_queries':0,'no_state_Git_P_canonical_writes':True,'final_release':False,'inputs':inputs}
 ref=out('independent_review.json',report)
 print(json.dumps({'status':report['status'],'scope':report['audit_scope'],'checks_total':report['checks_passed_total'],'report':ref,'production_ready':False,'remaining_production_gate_count':len(remaining)}))
except BaseException as e:
 out('audit_v2_failure.json',{'error':str(e),'traceback':traceback.format_exc(),'checks':checks,'production_ready':False});raise

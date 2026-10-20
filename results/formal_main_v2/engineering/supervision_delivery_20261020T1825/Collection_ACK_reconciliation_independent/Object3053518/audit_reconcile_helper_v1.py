from pathlib import Path
from contextlib import contextmanager
from datetime import datetime,timezone
import ast,copy,fcntl,hashlib,json,os,sys
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/spatial_collect_reconcile_independent_20261020T1825/Object3053518'
SOURCE=R/'.local/reconcile_collect_3053518_20261020T1825.py';PIN='09f019371cb5cf5b76d67e330ec412767e892e0263a7b48c792aa73616c3f722'
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes())}
def save(name,v):
 p=D/name
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
checks=[]
def check(name,v):
 assert v,name;checks.append(name)
raw=SOURCE.read_bytes();check('helper_source_pin',sha(raw)==PIN);tree=ast.parse(raw)
check('no_submit_or_run_calls',not any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr in ('submit','run','publish') for x in ast.walk(tree)))
blocks=[x for x in tree.body if isinstance(x,ast.With)];check('one_writer_transaction',len(blocks)==1)
block=blocks[0];check('original_shared_writer_lock',ast.unparse(block.items[0].context_expr)=="c.exclusive_lock(R / 'results/experiment_supervisor/.writer.lock')")
mutation_index=next(i for i,n in enumerate(block.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='c.atomic_json')
record_indices=[i for i,n in enumerate(block.body[:mutation_index]) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='g.record']
check('exact_two_immutable_precommit_record_intents',len(record_indices)==2)
check('one_state_CAS',sum(isinstance(x,ast.Call) and ast.unparse(x.func)=='c.atomic_json' for x in ast.walk(tree))==1)
check('CAS_explicit_expected_before','expected_sha=before' in ast.unparse(block.body[mutation_index]))
check('single_known_job_no_arguments',"JID = '3053518'" in ast.unparse(tree) and 'argparse' not in ast.unparse(tree))
@contextmanager
def readonly_shared_lock(path):
 check('actual_lock_exists',path.is_file() and not path.is_symlink())
 with path.open('rb') as f:
  fcntl.flock(f,fcntl.LOCK_SH)
  try:yield
  finally:fcntl.flock(f,fcntl.LOCK_UN)
write_intents=[]
def record_spy(path,value):
 assert str(path).startswith(str(R/'results/formal_main_v2'))
 write_intents.append({'path':Path(path).relative_to(R).as_posix(),'value':copy.deepcopy(value)})
def forbid(*a,**k):raise AssertionError('forbidden mutation')
queries=[]
def guard(event,args):
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes)):
   p=Path(os.fsdecode(path)).absolute()
   if p.suffix.lower() in {'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init'}:raise RuntimeError('payload forbidden')
   if isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND) and not p.is_relative_to(D):raise RuntimeError('production write forbidden')
 if event=='subprocess.Popen':
  argv=args[1];assert argv[0] in {'sacct','squeue','scontrol'},argv
  state=json.loads((R/'results/experiment_supervisor/state.json').read_bytes());ids={str(j['job_id']) for j in state['registered_jobs']}|{'3053518'}
  if argv[0] in {'sacct','squeue'}:assert set(argv[argv.index('-j')+1].split(','))<=ids
  else:assert argv==['scontrol','show','job','-o','3053518']
  queries.append(argv)
 if event.startswith('socket.') or event in {'os.system','os.remove','os.rename','os.rmdir','os.unlink'}:raise RuntimeError('forbidden side effect')
sys.addaudithook(guard)
# Execute only the exact reviewed pre-CAS logic. Replace lock with read-only SH lock,
# immutable writes with memory spies, and terminate before the state mutation.
prefix=copy.deepcopy(tree);b=next(n for n in prefix.body if isinstance(n,ast.With));b.items[0].context_expr=ast.Call(func=ast.Name(id='readonly_shared_lock',ctx=ast.Load()),args=[copy.deepcopy(block.items[0].context_expr.args[0])],keywords=[])
b.body=b.body[:mutation_index]
b.body.insert(0,ast.parse('g.record = record_spy\nc.atomic_json = forbid\nc.Slurm.submit = forbid').body[0])
b.body.insert(1,ast.parse('c.atomic_json = forbid').body[0]);b.body.insert(2,ast.parse('c.Slurm.submit = forbid').body[0])
ast.fix_missing_locations(prefix)
ns=dict(__name__='independent_readonly_prefix',__file__=str(SOURCE),readonly_shared_lock=readonly_shared_lock,record_spy=record_spy,forbid=forbid)
exec(compile(prefix,str(SOURCE)+'::readonly_pre_CAS','exec'),ns)
baseline=ns['baseline'];candidate=ns['s'];observed=ns['observed'];job=ns['job'];caps=ns['caps'];auth=ns['auth'];before=ns['before'];token=ns['token'];J='3053518';H=ns['AUTH']
check('full_registered_plus_known_job_observation',set(observed['rows'])=={str(j['job_id']) for j in baseline['registered_jobs']}|{J})
check('unique_known_job_append',candidate['registered_jobs']==baseline['registered_jobs']+[job] and sum(str(j['job_id'])==J for j in candidate['registered_jobs'])==1)
check('exact_original_gateway_job',job==json.loads((D/'original_gateway_rebuilt_job.json').read_bytes()))
check('matching_pending_cleared_only_in_memory',baseline['pending_submission']['known_job_id']==J and candidate['pending_submission'] is None)
check('reservation_consumed_once_in_memory',candidate['autonomous_training_v1']['reserved_GPU_slots']==0 and candidate['autonomous_training_v1']['downstream_reservations_consumed'][H]=={'job_id':J,'reservation':auth['root_reservation'],'request_token':token})
check('zero_submission_prefix',all(q[0]!='sbatch' for q in queries))
check('known_allocation_exact_one_GPU',observed['rows'][J]['status'] in ns['c'].TERMINAL|ns['c'].KNOWN_LIVE and observed['rows'][J]['gpus']==1 and (caps['occupied'].count(J)==1)==(observed['rows'][J]['status'] not in ns['c'].TERMINAL))
check('full_cost_recomputed_not_added',candidate['current_round_cost']['allocated_gpu_seconds']==sum(observed['rows'][str(j['job_id'])]['elapsed_seconds']*observed['rows'][str(j['job_id'])]['gpus'] for j in candidate['registered_jobs'] if j.get('experiment')=='formal_main_v2'))
allowed_top={'registered_jobs','pending_submission','autonomous_training_v1','current_round_cost','formal_main_progress'}
check('all_unrelated_top_state_unchanged',all(baseline.get(k)==candidate.get(k) for k in set(baseline)|set(candidate) if k not in allowed_top))
for field,allowed in [('autonomous_training_v1',{'reserved_GPU_slots','downstream_reservations_consumed'}),('current_round_cost',{'registered_jobs','allocated_gpu_seconds','allocated_gpu_hours','final'}),('formal_main_progress',{'parallel_execution'})]:
 old=baseline[field];new=candidate[field];check('unchanged:'+field,all(old.get(k)==new.get(k) for k in set(old)|set(new) if k not in allowed))
old=baseline['formal_main_progress']['parallel_execution'];new=candidate['formal_main_progress']['parallel_execution'];check('parallel_only_active_count_changed',all(old.get(k)==new.get(k) for k in set(old)|set(new) if k!='registered_requested_active_GPU_jobs'))
check('root72_and_final_seal_unchanged',candidate['formal_main_progress']['root_and_independent_completed_arms']==72 and candidate['formal_main_progress']['completed_final_trials']==0 and candidate['formal_main_progress']['global_release_created'] is False)
check('actual_state_still_original_pending',sha((R/'results/experiment_supervisor/state.json').read_bytes())==before)
save('helper_readonly_prefix_full_observation.json',{'observation':observed,'corroboration':ns['corroboration'],'capacity':caps,'query_argv':queries})
save('helper_proposed_state.json',candidate)
save('helper_record_intents_CPU_ONLY.json',write_intents)
report=save('helper_source_independent_review.json',dict(schema='formal_main_v2',kind='Object3053518_exact_pending_reconciliation_independent_CPU_review',status='passed_for_exact_helper_and_pending_only',created_utc=datetime.now(timezone.utc).isoformat(),source=ref(SOURCE),expected_state_sha256=before,job_id=J,authorization_sha256=H,checks=checks,checks_passed=len(checks),actual_readonly_prefix_reconstructed=True,actual_readonly_prefix_lock='rb LOCK_SH replaces production EX lock only for independent dry-run',all_registered_plus_exact_known_job_observed=True,original_source_AST_statement_prefix_retained=True,production_write_intents_intercepted_in_memory=True,production_state_writes=0,submission_calls=0,GPU_results_read=False,real_apply_performed=False,required_root_apply='Execute only reviewed helper SHA with original writer EX lock and expected SHA. Original failure/pending evidence retained. Any changed pending/state or unknown/inconsistent allocation identity fails closed and requires fresh bounded review; a true terminal status only records cost and does not accept scientific results; never resend.',proofs=[ref(D/x) for x in ('submission_evidence_independent_review.json','helper_readonly_prefix_full_observation.json','helper_proposed_state.json','helper_record_intents_CPU_ONLY.json')]))
print(json.dumps(report))

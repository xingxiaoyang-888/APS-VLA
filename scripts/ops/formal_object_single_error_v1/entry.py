"""Actual-P typed entry. --verify is read-only; --run requires a separately released atomic gateway."""
import argparse,fcntl,hashlib,json,os,re,sys,time,traceback
from contextlib import ExitStack
from datetime import datetime,timezone
from pathlib import Path
# Verify all candidate modules before importing executable project code.
def bootstrap(argv):
 base=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
 package='scripts/ops/formal_object_single_error_v1'
 if os.name!='posix' or Path(__file__).resolve()!=base/package/'entry.py':
  raise RuntimeError('actual-P canonical entry required before module import')
 p=argparse.ArgumentParser();mode=p.add_mutually_exclusive_group(required=True)
 mode.add_argument('--verify',action='store_true');mode.add_argument('--run',action='store_true')
 p.add_argument('--plan',type=Path);p.add_argument('--plan-sha256')
 p.add_argument('--invocation',type=Path);p.add_argument('--invocation-sha256')
 a=p.parse_args(argv)
 if a.verify:
  expected=base/'results/formal_main_v2/execution/object_single_error_v1/plan.json'
  if a.plan!=expected or a.invocation is not None or a.invocation_sha256 is not None:raise ValueError('exact static plan required')
  path=a.plan;checksum=a.plan_sha256
 else:
  expected=base/'results/formal_main_v2/invocations/object_single_error_task08_state0049_dense_attempt01.json'
  if a.invocation!=expected or a.plan is not None or a.plan_sha256 is not None:raise ValueError('exact immutable invocation required')
  path=a.invocation;checksum=a.invocation_sha256
 raw=path.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=checksum:raise ValueError('entry input SHA differs before module import')
 value=json.loads(raw);source=value.get('production_sources')
 names=('fixed.py','iterator.py','constants.py','adoption.py','execution.py','wrapper.py','entry.py','reviewer.py','gateway_contract.py','scope.json')
 if type(source) is not dict or set(source)!={package+'/'+n for n in names}:raise ValueError('complete new source closure required before module import')
 for name in names:
  rel=package+'/'+name
  if hashlib.sha256((base/rel).read_bytes()).hexdigest()!=source[rel]:raise ValueError('entry source differs before module import: '+rel)
if __name__=='__main__':bootstrap(sys.argv[1:])
import fixed as F
import constants as C
import execution as E
import wrapper as W
import gateway_contract as G

def exclusive_json(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x',encoding='utf8',newline='\n') as out:
  json.dump(value,out,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);out.write('\n');out.flush();os.fsync(out.fileno())
def actual_registration(inv,job,inv_sha):
 # Short read transaction only; hold no supervisor lock during GPU execution.
 with (F.R/'results/experiment_supervisor/.writer.lock').open('r') as h:
  fcntl.flock(h,fcntl.LOCK_SH)
  try:state=json.loads((F.R/'results/experiment_supervisor/state.json').read_text())
  finally:fcntl.flock(h,fcntl.LOCK_UN)
 record=G.bound_registration(inv,state,job_id=job,invocation_sha256=inv_sha)
 F.require(os.environ.get('SLURM_JOB_NAME')==record['job_name']
  and os.environ.get('SLURM_JOB_ACCOUNT')==record['account']
  and os.environ.get('SLURM_JOB_PARTITION')==record['partition'],'actual scheduler environment differs')
 return record

def run(inv,inv_sha,job):
 context=W.verify_invocation(inv,expected_job_id=job)
 actual_registration(inv,job,inv_sha)
 old=context['original_wrapper'];legacy=context['legacy'];runtime=context['runtime'];args=context['args']
 directory=F.P/C.JOURNAL_ROOT/job
 directory.mkdir(parents=True,exist_ok=False)
 identity_path=directory/'identity.json';runtime_path=directory/'action_events.jsonl'
 iterator_path=directory/'iterator_events.jsonl';completion_path=directory/'completion.json'
 shared=dict(schema='formal_main_v2',version=C.VERSION,job_id=job,invocation_sha256=inv_sha,
  plan_sha256=inv['plan_sha256'],scope_sha256=F.SCOPE_SHA,logical_trial_id=F.CELL,run_root=str(F.P/F.OUT),
  production_sources=inv['production_sources'])
 event_lists={'action':[],'iterator':[]};event_paths={'action':runtime_path,'iterator':iterator_path}
 def emit(kind,event,**fields):
  rows=event_lists[kind]
  F.require(not set(fields)&{'seq','utc','event','kind'},'typed event metadata overwrite')
  row=dict(kind='Object_single_error_'+kind+'_event',seq=len(rows),utc=datetime.now(timezone.utc).isoformat(),
   event=event,**fields)
  with event_paths[kind].open('a',encoding='utf8',newline='\n') as f:
   f.write(json.dumps(row,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
  rows.append(row)
 action_emit=lambda event,**fields:emit('action',event,**fields)
 iterator_emit=lambda event,**fields:emit('iterator',event,**fields)
 identity=dict(**shared,kind='Object_single_error_actual_identity',
  actual_entrypoint=C.BASE+'/entry.py',actual_scientific_adapter=C.LEGACY,
  actual_scientific_adapter_sha256=C.LEGACY_SHA,original_scientific_wrapper_executed=False,
  original_reference_invocation=C.REFERENCE,original_reference_sha256=C.REFERENCE_SHA,
  original_argument_values={k:str(v) if isinstance(v,Path) else v for k,v in vars(context['original_args']).items()},
  actual_argument_values={k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()},
  original_arguments_to_actual=context['args_diff'],runtime_contract=context['runtime_contract'],
  full_scientific_trials=600,legacy_rows_inserted=0,actually_allowed_trials=[F.CELL],
  final_allowed=False,ordinary_resume=False,loop_execution_recorded_in_separate_iterator_journal=True)
 exclusive_json(identity_path,identity)
 receipt=dict(schema='formal_main_v2',kind='formal_downstream_job_receipt',job_id=job,stage='development',
  stage_key=C.STAGE_KEY,run_root=str(F.P/F.OUT),invocation_sha256=inv_sha,
  source_sha256=context['reference']['source_sha256'],adapter_sha256=C.LEGACY_SHA,
  wrapper_sha256=inv['production_sources'][C.BASE+'/entry.py'],stage_completed_claimed=False,
  typed_identity_sha256=C.digest(identity_path),typed_version=C.VERSION,
  original_scientific_wrapper_executed=False,cost_scope='One complete actual Slurm allocation; no duplicate nested charge')
 started=time.perf_counter();exit_code=1;errors=[];result=None;runtime_verified=False
 try:
  with ExitStack() as stack:
   locks=F.P/'results/formal_main_v2/stage_locks';locks.mkdir(parents=True,exist_ok=True)
   names=[C.STAGE_KEY,*['libero_object_development_'+mid for mid in F.METHODS]]
   for name in sorted(names):
    stream=stack.enter_context((locks/(name+'.lock')).open('a'));fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
   # This marker is never cleared. A failed preflight is still an attempted allocation.
   exclusive_json(F.P/C.JOURNAL_ROOT/(C.STAGE_KEY+'.once_claim.json'),
    dict(**shared,kind='Object_single_error_permanent_execution_claim',negative_or_failure_never_auto_retry=True))
   F.require(not (F.P/F.OUT).exists(),'linked output already exists; no ordinary resume')
   F.require(not list((F.P/'results/formal_main_v2/adapter_invocations').glob(job+'_*')),'existing actual adapter attempt blocks duplicate')
   with legacy.source_imports(F.S):
    assets=runtime.expected_asset_identities(project_root=F.P,source_root=F.S,
     contract=context['runtime_contract'],asset_contract=context['reference']['downstream_asset_compatibility'])
    def scientific_runner():
     with E.install(legacy,context=context,job_id=job,emit=iterator_emit):
      return legacy.run(args,mode=args.mode,source_root=args.source_root,source_inventory=args.source_inventory,
       adapter_sha256=C.LEGACY_SHA,resume=False)
    result=runtime.run_with_asset_contexts(scientific_runner,project_root=F.P,source_root=F.S,
     contract=context['runtime_contract'],asset_contract=context['reference']['downstream_asset_compatibility'],emit=action_emit)
   runtime_proof=runtime.verify_runtime_events(event_lists['action'],context['runtime_contract'],expected_asset_identities=assets)
   F.require(runtime_proof.get('synthetic_input') is False,'synthetic runtime not permitted for actual execution')
   raw_path=F.P/F.OUT/'trials.jsonl';raw=[json.loads(x) for x in raw_path.read_bytes().splitlines()]
   E.verify_events(event_lists['iterator'],job_id=job,raw_sha256=C.digest(raw_path),
    raw_status=raw[-1]['status'],raw_success=raw[-1]['success'])
   C.verify_closure(F.P,inv['production_sources'])
   runtime_verified=True;exit_code=0
 except BaseException as e:
  errors.append(dict(type=type(e).__name__,message=str(e)))
  traceback.print_exception(type(e),e,e.__traceback__)
 finally:
  try:
   artifacts,receipts=old.archive_adapter_evidence(root=F.P,output=F.P/F.OUT,job_id=job,
    invocation=dict(run_root=str(F.P/F.OUT)))
   receipt.update(adapter_artifacts=artifacts,adapter_receipts=receipts)
   if exit_code==0:F.require(len(receipts)==1 and receipts[0]['status']=='returned','successful typed entry lacks genuine original adapter')
  except BaseException as e:exit_code=1;errors.append(dict(type=type(e).__name__,message=str(e),phase='archive'))
  finished=dict(**shared,kind='Object_single_error_actual_completion',
   status='returned' if exit_code==0 else 'failed',exit_code=exit_code,errors=errors,
   runtime_and_iterator_structures_verified=runtime_verified,scientific_acceptance_inferred=False,
   identity_sha256=C.digest(identity_path),
   action_events_sha256=C.digest(runtime_path) if runtime_path.exists() else None,
   iterator_events_sha256=C.digest(iterator_path) if iterator_path.exists() else None,
   wall_seconds=time.perf_counter()-started,finished_utc=datetime.now(timezone.utc).isoformat())
  exclusive_json(completion_path,finished)
  receipt.update(status=finished['status'],exit_code=exit_code,errors=errors,wall_seconds=finished['wall_seconds'],
   finished_utc=finished['finished_utc'],typed_completion_sha256=C.digest(completion_path))
  exclusive_json(F.P/'results/formal_main_v2/job_receipts'/f'{job}.json',receipt)
 return exit_code

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__)
 mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument('--verify',action='store_true');mode.add_argument('--run',action='store_true')
 parser.add_argument('--plan',type=Path);parser.add_argument('--plan-sha256')
 parser.add_argument('--invocation',type=Path);parser.add_argument('--invocation-sha256')
 args=parser.parse_args(argv)
 F.require(os.name=='posix' and Path(__file__).resolve()==F.P/C.BASE/'entry.py','canonical actual-P entry required')
 if args.verify:
  F.require(args.plan==F.P/C.PLAN and args.invocation is None and args.invocation_sha256 is None,'one exact static plan only')
  raw=F.read(F.P,C.PLAN,args.plan_sha256)
  print(json.dumps(W.verify_plan(json.loads(raw))['static_verification'],ensure_ascii=False,sort_keys=True));return 0
 F.require(args.plan is None and args.plan_sha256 is None and args.invocation==F.P/C.INVOCATION,'one exact registered linked invocation only')
 job=os.environ.get('SLURM_JOB_ID','');F.require(re.fullmatch('[0-9]+',job),'registered actual Slurm required')
 raw=F.read(F.P,C.INVOCATION,args.invocation_sha256)
 return run(json.loads(raw),args.invocation_sha256,job)
if __name__=='__main__':raise SystemExit(main())

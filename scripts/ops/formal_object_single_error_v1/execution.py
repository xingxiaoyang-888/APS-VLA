"""One verified full-panel iterator scope inside the unchanged adapter and execute."""
from contextlib import contextmanager
import __future__, ast, copy, inspect, json, marshal, sys, threading, types
from pathlib import Path
import fixed as F
import constants as C
import iterator as I

_LOCK=threading.Lock()

def code(fn):return I.codesig(fn.__code__)
def compiled_function(raw,filename,name):
 return I.nested(compile(raw,str(filename),'exec',dont_inherit=True),name)
def assert_function(fn,expected,module,name):
 F.require(type(fn) is types.FunctionType and fn.__globals__ is module.__dict__
  and fn.__name__==name and I.codesig(fn.__code__)==I.codesig(expected),'live function code/globals differs: '+name)
def class_codes(raw,filename,name):
 return {x.co_name:x for x in I.nested(compile(raw,str(filename),'exec',dont_inherit=True),name).co_consts
         if isinstance(x,types.CodeType)}
def module_origin(module,name,relative,*,source=F.S):
 F.require(sys.modules.get(name) is module and module.__name__==name
  and Path(module.__file__).resolve()==source/relative,'exact loaded snapshot module required')
def current_episode(formal,runtime,*,source=F.S):
 module_origin(formal,'cti_vla.evaluation.formal_trials',F.LOOP,source=source)
 module_origin(runtime,'cti_vla.evaluation.libero_runtime',F.RUNTIME,source=source)
 raw=F.read(source,F.RUNTIME,F.RUNTIME_SHA);compiled=compile(raw,str(source/F.RUNTIME),'exec',dont_inherit=True)
 # Independently reconstruct the already GPU-accepted one-range-check removal.
 action=C.load(F.R,C.ACTION,C.ACTION_SHA)
 before=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='run_episode')
 after=copy.deepcopy(before);matches=[]
 def walk(node):
  for _,value in ast.iter_fields(node):
   if isinstance(value,list):
    for i,n in enumerate(value):
     if isinstance(n,ast.AST):
      if ast.dump(n,include_attributes=False)==ast.dump(action._BRANCH,include_attributes=False):matches.append((value,i))
      else:walk(n)
   elif isinstance(value,ast.AST):walk(value)
 walk(after);F.require(len(matches)==1,'one registered action range branch required')
 seq,index=matches[0];removed=seq.pop(index)
 restored=copy.deepcopy(after);seq.insert(index,removed)
 F.require(ast.dump(after,include_attributes=False)==ast.dump(before,include_attributes=False),'action AST edits exceed registered branch')
 seq.pop(index);expected={}
 exec(compile(ast.Module(body=[after],type_ignores=[]),str(source/F.RUNTIME),'exec',
  flags=__future__.annotations.compiler_flag,dont_inherit=True),runtime.__dict__,expected)
 actual=runtime.run_episode
 assert_function(actual,expected['run_episode'].__code__,runtime,'run_episode')
 F.require(formal.run_episode is actual and actual.__defaults__ is None
  and actual.__kwdefaults__==dict(wait_steps=10,max_steps=220,policy_watchdog_seconds=60.),'current action alias/defaults differ')
 assert_function(runtime._observation_hash,I.nested(compiled,'_observation_hash'),runtime,'_observation_hash')
 action._check_chunk_construction(runtime,raw)
 assert_function(runtime.PolicyChunk.__post_init__,class_codes(raw,source/F.RUNTIME,'PolicyChunk')['__post_init__'],runtime,'__post_init__')
 F.require(tuple(runtime.DUMMY_ACTION)==(0.,0.,0.,0.,0.,0.,-1.),'dummy action changed')
 return dict(original_run_episode_code_sha256=I.codesig(I.nested(compiled,'run_episode')),
  current_run_episode_code_sha256=code(actual),current_action_ast_sha256=F.sig(ast.dump(after,include_attributes=False)),
  original_source_sha256=F.RUNTIME_SHA,action_adapter_sha256=C.ACTION_SHA,
  observation_code_sha256=code(runtime._observation_hash),policy_chunk_post_init_code_sha256=code(runtime.PolicyChunk.__post_init__),
  action_values_changed=False,formal_alias_is_current_runtime=True)

def token_policy_codes(*,source=F.S):
 from cti_vla.models import openvla_oft_policy as M
 relative='src/cti_vla/models/openvla_oft_policy.py'
 module_origin(M,'cti_vla.models.openvla_oft_policy',relative,source=source)
 inventory=json.loads(F.read(F.R,F.INVENTORY,F.INVENTORY_SHA))['files']
 expected=class_codes(F.read(source,relative,inventory[relative]),source/relative,'OpenVLAOFTTokenPolicy')
 cls=M.OpenVLAOFTTokenPolicy;signatures={}
 decorated={'forward_from_tokens':M.torch.no_grad,'forward_from_full_tokens':M.torch.no_grad,
  'predict_rollout_from_tokens':M.torch.inference_mode}
 for name,co in expected.items():
  if name=='<lambda>':continue
  item=cls.__dict__.get(name)
  fn=item.fget if isinstance(item,property) else item.__func__ if isinstance(item,staticmethod) else item
  if name in decorated:
   underlying=getattr(fn,'__wrapped__',None);assert_function(underlying,co,M,name)
   F.require(code(fn)==code(decorated[name]()(underlying)),'token policy decorator code differs')
   free=dict(zip(fn.__code__.co_freevars,(c.cell_contents for c in fn.__closure__ or ())))
   context=free.get('ctx_factory')
   F.require(free.get('func') is underlying and (context is decorated[name]
    or getattr(context,'__self__',None).__class__ is decorated[name]),'token policy decorator closure differs')
  else:assert_function(fn,co,M,name)
  signatures[name]=I.codesig(co)
 return signatures,inventory[relative]

def policy_closure(policies,manifest,*,source=F.S):
 from cti_vla.evaluation import formal_runtime as M
 module_origin(M,'cti_vla.evaluation.formal_runtime','src/cti_vla/evaluation/formal_runtime.py',source=source)
 inventory=json.loads(F.read(F.R,F.INVENTORY,F.INVENTORY_SHA))['files']
 relative='src/cti_vla/evaluation/formal_runtime.py';raw=F.read(source,relative,inventory[relative])
 expected=class_codes(raw,source/relative,'FormalRolloutPolicy');cls=M.FormalRolloutPolicy
 signatures={}
 for name,co in expected.items():
  if name=='<lambda>':continue
  fn=cls.__dict__.get(name)
  if name=='__call__':
   underlying=getattr(fn,'__wrapped__',None)
   assert_function(underlying,co,M,name)
   regenerated=M.torch.no_grad()(underlying)
   F.require(code(fn)==code(regenerated),'policy no_grad wrapper code changed')
   free=dict(zip(fn.__code__.co_freevars,(c.cell_contents for c in fn.__closure__ or ())))
   F.require(free.get('func') is underlying and 'ctx_factory' in free,'policy decorator closure changed')
   context=free['ctx_factory']
   F.require(type(context)==type(M.torch.no_grad) and context is M.torch.no_grad
    or getattr(context,'__self__',None).__class__ is M.torch.no_grad,'policy decorator is not no_grad context')
  else:assert_function(fn,co,M,name)
  signatures[name]=I.codesig(co)
 F.require(tuple(policies)==F.METHODS,'exact six verified policy instances required')
 token_signatures,token_source=token_policy_codes(source=source)
 components=None;processor=None;rows=[]
 for method,spec in zip(F.METHODS,manifest['methods']):
  p=policies[method];ident=spec['identity']
  F.require(type(p) is cls and not set(expected)&set(p.__dict__),'opaque/overridden policy instance rejected')
  F.require((p.suite,p.method,p.total_tokens)==('libero_object',ident['method'],ident['visual_tokens'])
   and p.record_selection is True and p.component_timing is False,'policy identity or profiling scope differs')
  if components is None:components=p.components;processor=p.processor
  F.require(p.components is components and p.processor is processor,'one shared official base/processor required')
  if ident['method'] in ('A','B'):
   F.require(p.selector is not None,'selected instance identity missing')
   # The original execute separately checks every selector checkpoint and pair before construction.
   from cti_vla.evaluation.formal_trials import selector_instance_identity
   F.require(selector_instance_identity(p.selector.provenance)==ident,'live selector provenance differs')
  else:F.require(p.selector is None,'baseline cannot hold selector')
  from cti_vla.models.openvla_oft_policy import OpenVLAOFTTokenPolicy
  token=p.token_policy
  F.require(type(token) is OpenVLAOFTTokenPolicy and not set(token_signatures)&set(token.__dict__),'opaque token policy rejected')
  rows.append(dict(method_id=method,identity=ident,class_name=cls.__module__+'.'+cls.__name__))
 return dict(methods=rows,policy_methods_code_sha256=signatures,source_sha256=inventory[relative],
  token_policy_methods_code_sha256=token_signatures,token_policy_source_sha256=token_source,
  original_execute_responsible_for_model_checkpoint_F00_F01_F03=True,opaque_callbacks_allowed=False)

def original_execute_callbacks(evaluate,factory,reseed,on_result):
 raw=F.read(F.S,'scripts/eval_formal_selector_libero.py','de5a2b0a20f8121b57da8a1f766e4f5b48f3c86e214eae7aa3d08d642753f887')
 expected=compiled_function(raw,F.S/'scripts/eval_formal_selector_libero.py','execute')
 assert_function(evaluate.execute,expected,evaluate,'execute')
 for name,fn in [('factory',factory),('reseed',reseed),('on_result',on_result)]:
  assert_function(fn,I.nested(expected,name),evaluate,name)
 return {name:code(fn) for name,fn in [('factory',factory),('reseed',reseed),('on_result',on_result)]}

@contextmanager
def install(adapter,*,context,job_id,emit):
 F.require(_LOCK.acquire(False),'duplicate/nested linked iterator scope')
 original_bindings=adapter.recorded_bindings;original_run=adapter.run;run_code=code(original_run)
 calls=0;installed=False;returned=False
 F.require(C.digest(adapter.__file__)==C.LEGACY_SHA,'original scientific adapter source differs')
 try:
  @contextmanager
  def bindings(evaluate,legacy,profiler_helpers,source,legacy_emit):
   nonlocal installed,calls,returned
   F.require(source==F.S and not installed,'one exact evaluation binding scope')
   from cti_vla.evaluation import formal_trials as M,libero_runtime as L
   module_origin(M,'cti_vla.evaluation.formal_trials',F.LOOP)
   original,derived,proof=I.derive_loop(M,F.read(F.S,F.LOOP,F.LOOP_SHA))
   current=current_episode(M,L)
   execute_code=code(evaluate.execute)
   installed=True
   # Original adapter sees the frozen loop before entering this scope and keeps
   # its own two binding events unchanged; this separate journal identifies execution.
   with original_bindings(evaluate,legacy,profiler_helpers,source,legacy_emit) as old_bindings:
    def guarded(panel,policies,ledger,env_factory,*,reseed,policy_watchdog_seconds=60.,stop_after=None,on_result=None):
     nonlocal calls,returned
     F.require(calls==0,'one linked attempt only; every second call is forbidden')
     calls+=1
     F.require(type(ledger) is L.TrialLedger and ledger.path==F.P/F.OUT/'trials.jsonl','genuine fresh TrialLedger exact new path required')
     config=json.loads((F.P/F.OUT/'config.json').read_text())
     F.validate_panel_manifest(panel,context['manifest'],config,M)
     F.require(stop_after is None and policy_watchdog_seconds==60.,'ordinary stop/resume forbidden')
     F.require(len(ledger.events)==1 and not ledger.completed() and ledger.recovered_tail is None,'fresh independent ledger required; no old or synthesized completions')
     inv=ledger.events[0]
     F.require(set(inv)=={'event','created_utc','slurm_job_id','run_signature'} and inv['event']=='invocation'
      and inv['slurm_job_id']==job_id and inv['run_signature']==ledger.run_signature==F.sig(config),'actual fresh invocation mismatch')
     F.require(current_episode(M,L)==current,'live action code changed after scoped install')
     callbacks=original_execute_callbacks(evaluate,env_factory,reseed,on_result)
     policies_proof=policy_closure(policies,context['manifest'])
     emit('linked_call_checked',actual_job_id=job_id,run_signature=ledger.run_signature,
      initial_ledger_sha256=C.digest(ledger.path),fresh_invocations=1,fresh_completed=0,
      full_scientific_states=100,full_scientific_methods=list(F.METHODS),allowed_trial_id=F.CELL,
      current_action=current,policy_closure=policies_proof,original_execute_callbacks=callbacks,
      original_loop_code_sha256=code(original),actual_derived_loop_code_sha256=code(derived))
     result=derived(panel,policies,ledger,env_factory,reseed=reseed,policy_watchdog_seconds=policy_watchdog_seconds,
      stop_after=stop_after,on_result=on_result)
     F.require(result==1 and len(ledger.events)==3 and [r['event'] for r in ledger.events]==['invocation','start','result']
      and all(r['trial_id']==F.CELL for r in ledger.events[1:]),'linked iterator did not produce exactly one fresh attempt')
     F.require(current_episode(M,L)==current and policy_closure(policies,context['manifest'])==policies_proof,'live policy/action changed during derived execution')
     returned=True
     emit('linked_loop_returned',attempts=1,ledger_sha256=C.digest(ledger.path),
      result_status=ledger.events[-1]['status'],success=ledger.events[-1]['success'],success_not_required=True)
     return result
    emit('linked_iterator_installed',derivation=proof,current_action=current,
     original_execute_code_sha256=execute_code,original_adapter_run_code_sha256=run_code,
     guard_code_sha256=code(guarded),ordinary_resume=False,legacy_completion_rows_inserted=0)
    M.evaluate_formal_trials=guarded
    try:yield old_bindings
    finally:
     intact=M.evaluate_formal_trials is guarded and code(evaluate.execute)==execute_code
     M.evaluate_formal_trials=original
     emit('linked_iterator_restored',binding_intact=intact,original_loop_restored=M.evaluate_formal_trials is original,
      call_count=calls,returned=returned,original_loop_code_sha256=code(original))
     F.require(intact,'linked iterator/frozen execute changed during scope')
  adapter.recorded_bindings=bindings
  try:yield
  finally:
   intact=adapter.recorded_bindings is bindings and adapter.run is original_run and code(original_run)==run_code
   adapter.recorded_bindings=original_bindings
   F.require(intact and installed and calls==1,'adapter run or exact once-only scope changed/incomplete')
 finally:_LOCK.release()

def verify_events(events,*,job_id,raw_sha256,raw_status,raw_success):
 F.require([e.get('event') for e in events]==['linked_iterator_installed','linked_call_checked','linked_loop_returned','linked_iterator_restored'],
  'complete exact typed iterator lifecycle required')
 a,b,c,d=events
 F.require(b.get('actual_job_id')==job_id and b.get('allowed_trial_id')==F.CELL and b.get('fresh_invocations')==1
  and b.get('fresh_completed')==0 and b.get('full_scientific_states')==100
  and b.get('full_scientific_methods')==list(F.METHODS),'typed full-science/fresh-ledger identity differs')
 F.require(a.get('ordinary_resume') is False and a.get('legacy_completion_rows_inserted')==0
  and a['derivation']['source_sha256']==F.LOOP_SHA and a['derivation']['allowlist']==[F.CELL]
  and a['derivation']['inserted_node_count']==1,'unregistered iterator derivation')
 F.require(a['derivation']['original_code_sha256']==b.get('original_loop_code_sha256')==d.get('original_loop_code_sha256')
  and a['derivation']['derived_code_sha256']==b.get('actual_derived_loop_code_sha256')
  and a.get('current_action')==b.get('current_action'),'original/derived/current code identities mixed')
 F.require(c.get('attempts')==1 and c.get('ledger_sha256')==raw_sha256
  and c.get('result_status')==raw_status and c.get('success')==raw_success and c.get('success_not_required') is True,
  'iterator return differs from actual raw result')
 F.require(d.get('binding_intact') is True and d.get('original_loop_restored') is True
  and d.get('call_count')==1 and d.get('returned') is True,'iterator restoration did not complete')
 return dict(kind='Object_single_error_iterator_actual_structure',status='passed_structure',
  raw_sha256=raw_sha256,events_sha256=F.sig(events),event_count=4,legacy_rows_inserted=0,actual_attempts=1)

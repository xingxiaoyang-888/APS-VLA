"""Candidate AST insertion on the accepted action runtime, never writes original code."""
import ast,copy,hashlib,importlib.util,sys
from pathlib import Path
R=Path(__file__).resolve().parent
BASE='ast_observer_v2.py'
BASE_SHA='e88222ea96c290019b2ec838ff68fe25a9f94d115ae996d92735e18e4cf0800e'
def sha(b):return hashlib.sha256(b).hexdigest()
raw=(R/BASE).read_bytes()
if sha(raw)!=BASE_SHA:raise ValueError('pinned observer AST engine changed')
# Reuse its source/code identity, restoration and original call/timer invariants.
from types import ModuleType
base=ModuleType('_goal_pair_gate_ast_engine');base.__file__=str(R/BASE)
exec(compile(raw,str(R/BASE),'exec'),base.__dict__)

def derive_run(raw):
 original,accepted=base.accepted_run_node(raw);derived=copy.deepcopy(accepted)
 base.replace_statement(derived,'env.reset()',[
  base.parse_stmt(base.NAME+'.capture("reset_before", env)'),
  base.parse_stmt(base.TEMP+' = env.reset()'),
  base.parse_stmt(base.NAME+'.capture("reset_after", env, '+base.TEMP+')'),
  base.parse_stmt(base.NAME+'.capture("set_init_before", env, '+base.TEMP+')'),base.parse_stmt('del '+base.TEMP)])
 base.surround(derived,'observation = env.set_init_state(np.asarray(initial_state, dtype=np.float64))',after=[base.NAME+'.capture("set_init_after", env, observation)'])
 base.surround(derived,'observation, _, _, _ = env.step(list(DUMMY_ACTION))',before=[base.NAME+'.capture("wait_before", env, observation, wait_steps=result["wait_steps"])'])
 base.surround(derived,'result["wait_steps"] += 1',after=[base.NAME+'.capture("wait_after", env, observation, wait_steps=result["wait_steps"])'])
 base.surround(derived,'query_started = time.perf_counter()',before=[base.NAME+'.capture("t0_query_before" if control_step == 0 else "query_before", env, observation, control_step=control_step, instruction=instruction)'])
 base.surround(derived,'elapsed = time.perf_counter() - query_started',after=[base.NAME+'.capture("t0_query_after" if control_step == 0 else "query_after", env, observation, control_step=control_step, chunk=chunk, instruction=instruction)'])
 base.surround(derived,'observation, _, done, _ = env.step(action.tolist())',before=[base.NAME+'.step_before(action, control_step, result["control_steps"], result["policy_calls"])'])
 base.surround(derived,'result["control_steps"] += 1',after=[base.NAME+'.step_after(action, control_step, result["control_steps"], result["policy_calls"])'])
 ast.fix_missing_locations(derived);proof=base.assert_projection(accepted,derived)
 proof.update(frozen_original_ast_sha256=sha(base.text(original).encode()),accepted_action_amplitude_branch_sha256=sha(base.text(base.parse_stmt(base.RANGE_BRANCH)).encode()),accepted_action_branch_deletions=1)
 return accepted,derived,proof

LEDGER_TEMP='_cti_prefix_ledger_event'
def derive_trials(raw):
 base.require(sha(raw)==base.TRIALS_SHA,'unregistered formal trial source')
 original=base.function_node(raw,'evaluate_formal_trials');derived=copy.deepcopy(original)
 for expr in ('{**identity, "event": "start", "created_utc": datetime.now(timezone.utc).isoformat()}','{**identity, "event": "cleanup_error", "error": str(exc)}'):
  target='ledger.append('+expr+')'
  base.replace_statement(derived,target,[base.parse_stmt(LEDGER_TEMP+' = '+expr),base.parse_stmt(base.NAME+'.guard_ledger_event('+LEDGER_TEMP+', ledger)'),base.parse_stmt('ledger.append('+LEDGER_TEMP+')'),base.parse_stmt('del '+LEDGER_TEMP)])
 base.surround(derived,'ledger.append(row)',before=[base.NAME+'.guard_ledger_event(row, ledger)'])
 # Start hook remains after the exact original append, not before reseeding.
 base.surround(derived,'del '+LEDGER_TEMP,after=[]) if False else None
 # There are two delete-temp sites; select the original start block structurally.
 found=[]
 for node in ast.walk(derived):
  for _,items in ast.iter_fields(node):
   if isinstance(items,list):
    for i,item in enumerate(items):
     if isinstance(item,ast.Assign) and len(item.targets)==1 and isinstance(item.targets[0],ast.Name) and item.targets[0].id==LEDGER_TEMP and 'created_utc' in base.text(item.value):
      found.append((items,i))
 base.require(len(found)==1,'unique start guard')
 items,i=found[0];items.insert(i+4,base.parse_stmt(base.NAME+'.trial_begin(identity, state)'))
 base.surround(derived,'reseed()',after=[base.NAME+'.capture("reseed_after")'])
 base.surround(derived,'env, instruction = environment_factory(state)',before=[base.NAME+'.capture("factory_before")'],after=[base.NAME+'.capture("factory_after", env)'])
 base.surround(derived,'if result["status"] == "infrastructure_error":\n    raise RuntimeError("formal infrastructure attempt retained; repair and resume same trial")',before=[base.NAME+'.trial_end(row, ledger)'])
 ast.fix_missing_locations(derived);return original,derived,base.assert_projection(original,derived)
def restore_ledger_blocks(node):
 # Every erased expression is additionally protected by the complete layout SHA.
 for parent in ast.walk(node):
  for field,items in ast.iter_fields(parent):
   if not isinstance(items,list):continue
   i=0
   while i<len(items):
    x=items[i]
    if isinstance(x,ast.Assign) and len(x.targets)==1 and isinstance(x.targets[0],ast.Name) and x.targets[0].id==LEDGER_TEMP:
     base.require(i+3<len(items),'guarded row block truncated')
     expr=x.value
     base.require(base.text(items[i+1])==base.text(base.parse_stmt(base.NAME+'.guard_ledger_event('+LEDGER_TEMP+', ledger)')) and base.text(items[i+2])==base.text(base.parse_stmt('ledger.append('+LEDGER_TEMP+')')) and base.text(items[i+3])==base.text(base.parse_stmt('del '+LEDGER_TEMP)),'prewrite block differs')
     old=base.parse_stmt('ledger.append(None)');old.value.args=[copy.deepcopy(expr)]
     items[i:i+4]=[old]
    i+=1
 return node

class StripGate(base.StripObserver):
 def visit_FunctionDef(self,node):
  return self.generic_visit(restore_ledger_blocks(node))
 def visit_Expr(self,node):
  call=node.value
  if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and isinstance(call.func.value,ast.Name) and call.func.value.id==base.NAME and call.func.attr in ('step_after','step_before','guard_ledger_event'):return None
  return super().visit_Expr(node)
# These hashes are set from a source-only generation once, then frozen before tests.
LAYOUT={'run_episode':('7dcc7b9948a0090b06f70d642568f5240de9e2f0d890d2d49276feba15896f58','7fe318b78a7e766c9ca902605292188716dc5021d97cc419c4eaf9dc8be7d325'),
 'evaluate_formal_trials':('d48d153550ba6c1df559d08d20cc629dd7063bf0156ebfdfa0f89964a6855e46','fc19fee909b7e52598627e01339378f173ec13701c5c4157fa5640434a217f70')}
base.StripObserver=StripGate;base.OBSERVER_LAYOUT_V2=LAYOUT;base.derive_run=derive_run;base.derive_trials=derive_trials
observer_scope=base.observer_scope

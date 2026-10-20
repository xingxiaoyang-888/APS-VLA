"""Candidate AST insertion on the accepted action runtime, never writes original code."""
import ast,copy,hashlib,importlib.util,sys
from pathlib import Path
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
BASE='scripts/ops/formal_goal_prefix58_observer_v2/ast_observer_v2.py'
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
 base.surround(derived,'result["control_steps"] += 1',after=[base.NAME+'.step_after(action, control_step, result["control_steps"], result["policy_calls"])'])
 ast.fix_missing_locations(derived);proof=base.assert_projection(accepted,derived)
 proof.update(frozen_original_ast_sha256=sha(base.text(original).encode()),accepted_action_amplitude_branch_sha256=sha(base.text(base.parse_stmt(base.RANGE_BRANCH)).encode()),accepted_action_branch_deletions=1)
 return accepted,derived,proof
class StripGate(base.StripObserver):
 def visit_Expr(self,node):
  call=node.value
  if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and isinstance(call.func.value,ast.Name) and call.func.value.id==base.NAME and call.func.attr=='step_after':return None
  return super().visit_Expr(node)
# These hashes are set from a source-only generation once, then frozen before tests.
LAYOUT={'run_episode':('7dcc7b9948a0090b06f70d642568f5240de9e2f0d890d2d49276feba15896f58','2dc5763fb80b6eaa00ba24c8f0b529a046f6c0d2ef8a880059a5edcb8c1e6725'),
 'evaluate_formal_trials':('d48d153550ba6c1df559d08d20cc629dd7063bf0156ebfdfa0f89964a6855e46','25361b2db2ff14d26db2222cf9bba430f6207dec5f1caff22478224da7589849')}
base.StripObserver=StripGate;base.OBSERVER_LAYOUT_V2=LAYOUT;base.derive_run=derive_run
observer_scope=base.observer_scope

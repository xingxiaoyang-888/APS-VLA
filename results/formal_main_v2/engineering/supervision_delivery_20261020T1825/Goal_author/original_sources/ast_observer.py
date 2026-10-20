"""Reversible observer-only AST insertion around exact accepted action_v1 loops.

The accepted one-branch amplitude-check deletion is reproduced exactly first.
The original closed-loop calls, expressions, ordering, and timers remain intact.
This private context restores action_v1's active replacement before it exits.
"""
from __future__ import annotations
import __future__
import ast
import copy
from contextlib import contextmanager
import hashlib
import marshal
from pathlib import Path
import types

RUNTIME_SHA='2fc1bacbd1268a36f2e31451c70a650be4f8d0c8f6803e7c8b2a3d45f701c781'
TRIALS_SHA='93a0971dbc8bbf4cb462490b0b00a337d92f015af83b798bb635163a9cb864f6'
NAME='_cti_prefix_observer'
TEMP='_cti_prefix_reset_return'
RANGE_BRANCH='''if bool((np.abs(chunk.environment_actions) > 1.00001).any()):
    raise ValueError("environment action outside normalized controller [-1, 1] range")'''

def require(ok,message):
    if not ok: raise ValueError(message)

def text(node): return ast.dump(node,include_attributes=False)
def sha(value): return hashlib.sha256(value).hexdigest()
def code_sha(fn): return sha(marshal.dumps(fn.__code__,2))
def parse_stmt(value): return ast.parse(value).body[0]

def function_node(raw,name):
    tree=ast.parse(raw)
    matches=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name]
    require(len(matches)==1 and not matches[0].decorator_list,'unexpected frozen function')
    require(not any(isinstance(n,ast.Name) and n.id.startswith('_cti_prefix') for n in ast.walk(matches[0])),
            'observer symbol collides with original source')
    return matches[0]

def replace_statement(tree,target,replacement):
    signature=text(parse_stmt(target)); found=[]
    for parent in ast.walk(tree):
        for field,items in ast.iter_fields(parent):
            if isinstance(items,list):
                for i,item in enumerate(items):
                    if isinstance(item,ast.stmt) and text(item)==signature:
                        found.append((items,i,item))
    require(len(found)==1,'target statement is not unique: '+target)
    items,i,old=found[0]
    new=[ast.copy_location(copy.deepcopy(x),old) for x in replacement]
    items[i:i+1]=new


def surround(tree,target,before=(),after=()):
    replacement=[parse_stmt(s) for s in before]+[parse_stmt(target)]+[parse_stmt(s) for s in after]
    # Preserve original positions on the original statement for unchanged timing proof.
    original=next(n for n in ast.walk(tree) if isinstance(n,ast.stmt) and text(n)==text(parse_stmt(target)))
    replacement[len(before)]=copy.deepcopy(original)
    replace_statement(tree,target,replacement)


def accepted_run_node(raw):
    require(sha(raw)==RUNTIME_SHA,'unregistered run_episode source')
    original=function_node(raw,'run_episode'); accepted=copy.deepcopy(original)
    replace_statement(accepted,RANGE_BRANCH,[])
    return original,accepted

class StripObserver(ast.NodeTransformer):
    def visit_Expr(self,node):
        call=node.value
        if (isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute)
                and isinstance(call.func.value,ast.Name) and call.func.value.id==NAME):
            require(call.func.attr in ('capture','trial_begin','trial_end'),'unknown observer call')
            return None
        return self.generic_visit(node)
    def visit_Assign(self,node):
        if len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id==TEMP:
            require(text(node.value)==text(ast.parse('env.reset()',mode='eval').body),'reset return expression changed')
            return ast.copy_location(ast.Expr(value=copy.deepcopy(node.value)),node)
        return self.generic_visit(node)
    def visit_Delete(self,node):
        if len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id==TEMP:
            return None
        return self.generic_visit(node)

def assert_projection(original,derived):
    restored=StripObserver().visit(copy.deepcopy(derived))
    require(text(restored)==text(original),'AST changes exceed observer hooks/reset-return retention')
    # Every existing call (including original perf_counter placement) is identical after projection.
    return dict(original_ast_sha256=sha(text(original).encode()),
                observer_ast_sha256=sha(text(derived).encode()),
                stripped_ast_sha256=sha(text(restored).encode()),
                original_calls=[text(n) for n in ast.walk(original) if isinstance(n,ast.Call)],
                projected_calls=[text(n) for n in ast.walk(restored) if isinstance(n,ast.Call)],
                original_function_unchanged_after_projection=True,
                reset_result_retained_only_for_passive_copy=True,
                original_policy_timer_statements_unchanged=True)

def derive_run(raw):
    original,accepted=accepted_run_node(raw); derived=copy.deepcopy(accepted)
    replace_statement(derived,'env.reset()',[
        parse_stmt(NAME+'.capture("reset_before", env)'),
        parse_stmt(TEMP+' = env.reset()'),
        parse_stmt(NAME+'.capture("reset_after", env, '+TEMP+')'),
        parse_stmt(NAME+'.capture("set_init_before", env, '+TEMP+')'),
        parse_stmt('del '+TEMP)])
    surround(derived,'observation = env.set_init_state(np.asarray(initial_state, dtype=np.float64))',
             after=[NAME+'.capture("set_init_after", env, observation)'])
    surround(derived,'observation, _, _, _ = env.step(list(DUMMY_ACTION))',
             before=[NAME+'.capture("wait_before", env, observation, wait_steps=result["wait_steps"])'])
    surround(derived,'result["wait_steps"] += 1',
             after=[NAME+'.capture("wait_after", env, observation, wait_steps=result["wait_steps"])'])
    surround(derived,'query_started = time.perf_counter()',
             before=[NAME+'.capture("t0_query_before", env, observation, control_step=control_step)'])
    surround(derived,'elapsed = time.perf_counter() - query_started',
             after=[NAME+'.capture("t0_query_after", env, observation, control_step=control_step, chunk=chunk)'])
    ast.fix_missing_locations(derived)
    proof=assert_projection(accepted,derived)
    proof.update(frozen_original_ast_sha256=sha(text(original).encode()),
                 accepted_action_amplitude_branch_sha256=sha(text(parse_stmt(RANGE_BRANCH)).encode()),
                 accepted_action_branch_deletions=1)
    return accepted,derived,proof

def derive_trials(raw):
    require(sha(raw)==TRIALS_SHA,'unregistered formal trial source')
    original=function_node(raw,'evaluate_formal_trials'); derived=copy.deepcopy(original)
    surround(derived,'ledger.append({**identity, "event": "start", "created_utc": datetime.now(timezone.utc).isoformat()})',
             after=[NAME+'.trial_begin(identity, state)'])
    surround(derived,'reseed()',after=[NAME+'.capture("reseed_after")'])
    surround(derived,'env, instruction = environment_factory(state)',
             before=[NAME+'.capture("factory_before")'],
             after=[NAME+'.capture("factory_after", env)'])
    target='''if result["status"] == "infrastructure_error":
    raise RuntimeError("formal infrastructure attempt retained; repair and resume same trial")'''
    surround(derived,target,before=[NAME+'.trial_end(row, ledger)'])
    ast.fix_missing_locations(derived)
    return original,derived,assert_projection(original,derived)

def _compile(node,module):
    namespace={}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(module.__file__),'exec',
                 flags=__future__.annotations.compiler_flag,dont_inherit=True),module.__dict__,namespace)
    return namespace[node.name]

def _original_code(raw,name,filename):
    codes=[x for x in compile(raw,filename,'exec',dont_inherit=True).co_consts
           if isinstance(x,types.CodeType) and x.co_name==name]
    require(len(codes)==1,'original code symbol not unique')
    return sha(marshal.dumps(codes[0],2))

@contextmanager
def observer_scope(runtime,trials,observer,*,emit):
    raw=Path(runtime.__file__).read_bytes(); t_raw=Path(trials.__file__).read_bytes()
    accepted,run_node,run_proof=derive_run(raw)
    original_trial,trial_node,trial_proof=derive_trials(t_raw)
    active=runtime.run_episode; original_evaluate=trials.evaluate_formal_trials
    require(trials.run_episode is active,'accepted action_v1 aliases differ')
    require(active.__globals__ is runtime.__dict__ and original_evaluate.__globals__ is trials.__dict__,
            'loop globals differ')
    expected_active=_compile(accepted,runtime)
    require(code_sha(active)==code_sha(expected_active),'active loop is not the exact accepted action_v1 derivation')
    require(code_sha(original_evaluate)==_original_code(t_raw,'evaluate_formal_trials',str(trials.__file__)),
            'original formal trial function was replaced')
    require(NAME not in runtime.__dict__ and NAME not in trials.__dict__,'observer already installed')
    replacement=_compile(run_node,runtime); trial_replacement=_compile(trial_node,trials)
    for old,new in ((active,replacement),(original_evaluate,trial_replacement)):
        require(old.__defaults__==new.__defaults__ and old.__kwdefaults__==new.__kwdefaults__
                and old.__annotations__==new.__annotations__,'observer calling contract differs')
    saved=(active.__code__,original_evaluate.__code__,runtime.PolicyChunk,runtime._observation_hash,
           runtime.DUMMY_ACTION,code_sha(replacement),code_sha(trial_replacement))
    proof=dict(version='goal-prefix58-observer-ast-v1',run_episode=run_proof,trial_loop=trial_proof,
               active_run_code_sha256=code_sha(active),original_trial_code_sha256=code_sha(original_evaluate),
               observer_run_code_sha256=code_sha(replacement),observer_trial_code_sha256=code_sha(trial_replacement),
               accepted_action_context_required=True,scientific_settings_changed=False,
               original_execute_and_loading_untouched=True,observer_writes_outside_policy_timer=True)
    emit('prefix_observer_scope_enter',proof=proof)
    runtime.__dict__[NAME]=trials.__dict__[NAME]=observer
    runtime.run_episode=trials.run_episode=replacement
    trials.evaluate_formal_trials=trial_replacement
    raised=False
    try:
        yield proof
    except BaseException:
        raised=True
        raise
    finally:
        intact=(runtime.run_episode is replacement and trials.run_episode is replacement
                and trials.evaluate_formal_trials is trial_replacement
                and runtime.__dict__.get(NAME) is observer and trials.__dict__.get(NAME) is observer
                and active.__code__ is saved[0] and original_evaluate.__code__ is saved[1]
                and runtime.PolicyChunk is saved[2] and runtime._observation_hash is saved[3]
                and runtime.DUMMY_ACTION is saved[4]
                and code_sha(replacement)==saved[5] and code_sha(trial_replacement)==saved[6])
        runtime.run_episode=trials.run_episode=active
        trials.evaluate_formal_trials=original_evaluate
        runtime.__dict__.pop(NAME,None);trials.__dict__.pop(NAME,None)
        emit('prefix_observer_scope_exit',bindings_intact=intact,bindings_restored=True,
             runner_raised=raised,scientific_trials_added=0)
        require(intact,'observer binding integrity failure; accepted action context restored')

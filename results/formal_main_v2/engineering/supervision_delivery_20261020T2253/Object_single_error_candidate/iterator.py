"""One AST insertion into the frozen full-panel iterator; no submit or GPU CLI."""
from __future__ import annotations
import __future__
import ast
import copy
import hashlib
import marshal
import types
import fixed as F

NAME='evaluate_formal_trials'
ANCHOR=ast.parse('identity = _identity(panel, state, identifier)').body[0]
FILTER=ast.parse('if identity["trial_id"] != '+repr(F.CELL)+':\n    continue').body[0]


def astsig(node):return F.sig(ast.dump(node,include_attributes=False))
def codesig(code):return hashlib.sha256(marshal.dumps(code,2)).hexdigest()


def nested(code,name):
 found=[x for x in code.co_consts if isinstance(x,types.CodeType) and x.co_name==name]
 F.require(len(found)==1,'unique compiled original function required')
 return found[0]


def original_function(module,name,compiled):
 fn=getattr(module,name)
 F.require(type(fn) is types.FunctionType and fn.__globals__ is module.__dict__ and fn.__name__==name
  and codesig(fn.__code__)==codesig(nested(compiled,name)),'frozen function/globals modified: '+name)
 return fn


def derive_loop(module,source_bytes):
 F.require(F.sha(source_bytes)==F.LOOP_SHA,'exact original full-panel iterator source required')
 original=getattr(module,NAME);compiled=compile(source_bytes,original.__code__.co_filename,'exec',dont_inherit=True)
 original_function(module,NAME,compiled)
 for name in ('_identity','validate_trial_identities','expected_method_ids'):
  original_function(module,name,compiled)
 F.require(original.__defaults__ is None and original.__kwdefaults__=={'policy_watchdog_seconds':60.,'stop_after':None,'on_result':None},
  'original loop calling defaults differ')
 before=next(x for x in ast.parse(source_bytes).body if isinstance(x,ast.FunctionDef) and x.name==NAME)
 F.require(not before.decorator_list,'unexpected original decorator')
 after=copy.deepcopy(before);matches=[]
 def visit(node,path=()):
  for field,value in ast.iter_fields(node):
   if isinstance(value,list):
    for index,child in enumerate(value):
     if isinstance(child,ast.AST):
      if ast.dump(child,include_attributes=False)==ast.dump(ANCHOR,include_attributes=False):matches.append((value,index,path+((field,index),)))
      else:visit(child,path+((field,index),))
   elif isinstance(value,ast.AST):visit(value,path+((field,None),))
 visit(after)
 F.require(len(matches)==1,'exact unique identity-construction anchor required')
 sequence,index,path=matches[0];inserted=copy.deepcopy(FILTER);sequence.insert(index+1,inserted)
 ast.fix_missing_locations(after)
 derived_ast=astsig(after)
 sequence.pop(index+1);F.require(astsig(after)==astsig(before),'edit exceeds exact one allowlist insertion')
 sequence.insert(index+1,inserted)
 namespace={}
 exec(compile(ast.Module(body=[after],type_ignores=[]),original.__code__.co_filename,'exec',
  flags=__future__.annotations.compiler_flag,dont_inherit=True),module.__dict__,namespace)
 replacement=namespace[NAME]
 F.require(replacement.__globals__ is original.__globals__ and replacement.__defaults__==original.__defaults__
  and replacement.__kwdefaults__==original.__kwdefaults__ and replacement.__annotations__==original.__annotations__,'derived loop calling contract differs')
 proof=dict(kind='Object_single_error_iterator_derivation',source_sha256=F.LOOP_SHA,original_ast_sha256=astsig(before),
  derived_ast_sha256=derived_ast,inserted_node_ast_sha256=astsig(inserted),inserted_node_count=1,
  insertion_after_path=[list(x) for x in path],original_code_sha256=codesig(original.__code__),
  derived_code_sha256=codesig(replacement.__code__),code_marshal_version=2,full100_state_and6method_guards_unchanged=True,
  original_identity_reset_reseed_run_episode_action_success_error_logic_unchanged=True,allowlist=[F.CELL],
  fake_legacy_completions_written=False,run_episode_implementation_not_changed=True,
  production_or_GPU_authority=False)
 return original,replacement,proof


def check_runtime_call(module,*,panel,manifest,config,policies,ledger,job_id,run_signature,stop_after,
                       policy_watchdog_seconds,scope,loop_proof):
 # Must be called by a separately accepted exact child entry after actual model verification,
 # immediately before the derived loop. This function is not an execution authorization.
 F.check_scope(scope)
 F.require(scope['allowlist']==[F.CELL] and scope['ordinary_resume'] is False and scope['fresh_reset'] is True,'no ordinary resume')
 identity=F.validate_panel_manifest(panel,manifest,config,module)
 F.require(identity==scope['identity'] and scope['action_semantics_sha256']==F.ACTION,'scope identity differs')
 F.require(tuple(policies)==F.METHODS,'all six verified original policies required even though only dense executes')
 F.require(stop_after is None and type(policy_watchdog_seconds) in (float,int) and policy_watchdog_seconds==60.,'stop_after forbidden; watchdog unchanged')
 F.require(type(job_id) is str and job_id.isdigit() and job_id not in F.JOBS,'distinct actual new Slurm job required')
 F.require(type(run_signature) is str and len(run_signature)==64 and all(x in '0123456789abcdef' for x in run_signature),'new config signature required')
 F.require(len(ledger.events)==1,'fresh independent ledger must have exactly one actual invocation')
 invocation=ledger.events[0]
 F.require(set(invocation)=={'event','created_utc','slurm_job_id','run_signature'} and invocation['event']=='invocation'
  and invocation['slurm_job_id']==job_id and invocation['run_signature']==run_signature and bool(invocation['created_utc']),'actual new invocation fields differ')
 F.require(ledger.completed()==set(),'no fabricated prior completions')
 F.require(loop_proof==derive_loop(module,F.read(F.R,F.LOOP,F.LOOP_SHA))[2],'complete exact AST/code derivation proof differs')
 F.require(loop_proof['kind']=='Object_single_error_iterator_derivation' and loop_proof['source_sha256']==F.LOOP_SHA
  and loop_proof['allowlist']==[F.CELL] and loop_proof['inserted_node_count']==1,'exact derivation proof required')
 return dict(kind='Object_single_error_call_precheck',status='CPU_structural_precheck_only',
  scientific_expected_trials=600,actually_authorized_cell_count=1,original_method_count=6,
  actual_new_job_id=job_id,full_reset_required=True,ordinary_resume=False,production_authorized=False)

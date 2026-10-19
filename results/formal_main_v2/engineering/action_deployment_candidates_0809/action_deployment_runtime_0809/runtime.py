"""Bounded operational candidate; external root activation/Slurm/panel gates required.

No submit or execution CLI. Frozen scientific files are never written.
"""
from __future__ import annotations
import argparse
import ast
import copy
from contextlib import contextmanager, ExitStack
import hashlib
import importlib
import importlib.util
import json
import marshal
from pathlib import Path
import sys
import threading
import types
import uuid

VERSION = 'formal-action-deployment-runtime-v1'
P = Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
R = Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
S = P/'snapshots/formal_main_v2_run_564be0995e'
INVENTORY = 'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
INVENTORY_SHA = '5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
SOURCE_SHA = 'dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e'
REG = 'configs/experiments/formal_main_v2.json'
ACTION = 'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py'
ACTION_SHA = 'b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185'
ACTION_REG = 'configs/experiments/formal_main_v2_action_execution_compat_v1.json'
ACTION_REG_SHA = '0917bff60e632a5be3c2db50b16daa0b904e4754a3ba31334802060f75d3eefe'
PROBE = 'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v4/source/probe.py'
PROBE_SHA = '91e12f29ad39591c29cfd63912394949d1cad932bb80c8a871ed852cea32cadc'
ROOT_GPU = 'results/formal_main_v2/preflight/heartbeat_20261019T1347/v4_GPU_root_acceptance.json'
ROOT_GPU_SHA = '3ee503429d703bb9d8da5970a9e183d371defbaf86884b24ae164d6cbc7bc1e9'
IND_GPU = 'results/formal_main_v2/engineering/action_v4_actual_independent_0547/terminal_review.json'
IND_GPU_SHA = '613489f84224eaafac36523244ac98e3b81d50624d9da7102b3d5cd1062edbbe'
LEGACY = 'scripts/ops/formal_evaluation_adapter.py'
LEGACY_SHA = 'b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd'
ASSET = 'scripts/ops/formal_asset_evaluation_adapter.py'
ASSET_SHA = '5762e163a00845c3404dbee87b724289bd6cef40cbb644cbec668bc4f7dbd688'
META = 'scripts/ops/formal_asset_metadata_adapter.py'
META_SHA = 'd1ca08465ffcf2682569b1224e2018f17fdba61feac1896f864cc981759397d0'
GOAL = 'scripts/ops/formal_goal_component_adapter.py'
GOAL_SHA = '60db92e78f62e3dc54c7a791debee9085a2651cfbcd99d4ce725c68428f1c6ea'
TIMING = 'src/cti_vla/evaluation/profiling.py'
TIMING_SHA = '648cf11400b0d70f2e4ee99fd8d4c26f917b38957b546ad5bfc578915d1d0404'
FORMAL_TIMING = 'src/cti_vla/evaluation/formal_profiling.py'
FORMAL_TIMING_SHA = '56f9fec509a67b5687393e4d020f26722ee16f237df27261bbf38c1437278a80'
ANALYZER = 'scripts/analyze_formal.py'
ANALYZER_SHA = '7f9573877f8a3662bd06dae9362823fd478283ed14cc86a6c3763f6fb4f682f1'
LOADER = 'src/cti_vla/models/openvla_oft_loader.py'
RUNTIME = 'src/cti_vla/models/openvla_oft_runtime_compat.py'
STAGES = ('development','collect','full','components')
SUITES = ('libero_spatial','libero_object','libero_goal','libero_10')
_LOCK = threading.Lock()
_PROCESS_USED = False


def require(ok, message):
    if not ok: raise ValueError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()


def sig(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def code_sha(code):
    return hashlib.sha256(marshal.dumps(code,2)).hexdigest()


def direct(value):
    p=Path(value).absolute()
    require(p.resolve()==p,'direct server path required')
    return p


def read_pinned(project, relative, expected, watched):
    raw=Path(relative)
    require(not raw.is_absolute() and '..' not in raw.parts and not any('sealed' in x.lower() for x in raw.parts),'unsafe metadata path')
    path=direct(project/raw)
    require(project in path.parents and sha(path)==expected,'pinned metadata changed: '+relative)
    watched[str(path)]=expected
    return path.read_bytes()


def load(path, expected):
    path=direct(path);require(sha(path)==expected,'module source differs')
    name='_action_deployment_'+uuid.uuid4().hex
    module=types.ModuleType(name);module.__file__=str(path)
    # No .pyc writer and no import side effects beyond this exact source.
    exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__)
    return module


def make_contract(*, project_root, source_root, suite, stage):
    require(suite in SUITES and stage in STAGES,'only registered development/collect/full/components suite stages')
    project=direct(project_root);source=direct(source_root)
    require(project in (P,R) and source==S,'canonical server project and frozen snapshot required')
    watched={};inventory=json.loads(read_pinned(project,INVENTORY,INVENTORY_SHA,watched))
    require(len(inventory['files'])==173 and inventory['source_sha256']==SOURCE_SHA,'source inventory differs')
    registration=json.loads(read_pinned(source,REG,inventory['files'][REG],watched))
    spec=registration['suites'][suite]
    return dict(schema='formal_main_v2',kind='formal_action_deployment_runtime_contract',version=VERSION,
        suite=suite,stage=stage,source_root=str(source),source_sha256=SOURCE_SHA,
        source_inventory=dict(path=INVENTORY,sha256=INVENTORY_SHA),
        registration=dict(path=REG,sha256=inventory['files'][REG]),checkpoint=spec['model_root_server'],
        implementation_sha256=sha(__file__),
        dependencies={ACTION:ACTION_SHA,ACTION_REG:ACTION_REG_SHA,PROBE:PROBE_SHA,LEGACY:LEGACY_SHA,ASSET:ASSET_SHA,META:META_SHA,GOAL:GOAL_SHA},
        engineering_acceptance=dict(root=dict(path=ROOT_GPU,sha256=ROOT_GPU_SHA),independent=dict(path=IND_GPU,sha256=IND_GPU_SHA)),
        policy=dict(expected_base_loads=1,first_minimal_install=True,repeat_load='reject',
            action_values='unchanged',action_scope='same dense/uniform/A/B',
            timing_validator='remove_amplitude_disjunct_only_preserve_shape_finite',
            timing_aliases=['cti_vla.evaluation.profiling._validate_chunk','cti_vla.evaluation.formal_profiling._validate_chunk'],
            asset_scope_order=['metadata_if_object_or_goal','component_if_goal','deployment_runtime','original_runner'],
            no_timed_policy_instrumentation=True,scientific_settings_changed=False,final_allowed=False))


def validate_contract(contract, *, project_root, source_root):
    require(type(contract) is dict,'typed contract required')
    # Stage is rejected before metadata paths or user-provided references are followed.
    expected=make_contract(project_root=project_root,source_root=source_root,suite=contract.get('suite'),stage=contract.get('stage'))
    require(sig(contract)==sig(expected),'runtime contract fields/source/implementation differ')
    project=direct(project_root);source=direct(source_root);watched={}
    inventory=json.loads(read_pinned(project,INVENTORY,INVENTORY_SHA,watched))
    for relative,digest in inventory['files'].items():read_pinned(source,relative,digest,watched)
    for relative,digest in contract['dependencies'].items():read_pinned(project,relative,digest,watched)
    root=json.loads(read_pinned(project,ROOT_GPU,ROOT_GPU_SHA,watched))
    ind=json.loads(read_pinned(project,IND_GPU,IND_GPU_SHA,watched))
    require(root['kind']=='root_action_execution_v4_GPU_acceptance' and root['status']=='passed_bounded_GPU_engineering_only'
        and root['independent_review']==dict(path=IND_GPU,sha256=IND_GPU_SHA)
        and ind['kind']=='action_execution_v4_actual_GPU_independent_review'
        and ind['status']=='passed_bounded_actual_GPU_engineering_acceptance_pending_root_integration'
        and root['job_id']==ind['job_id']=='3039197' and root['scientific_trials_added']==ind['scientific_trials_added']==0,
        'bounded engineering acceptance types differ')
    watched[str(direct(__file__))]=contract['implementation_sha256']
    return watched


def unchanged(watched):
    for p,h in watched.items():require(sha(p)==h,'watched bytes changed: '+p)


def _nested_code(code, name):
    matches=[c for c in code.co_consts if isinstance(c,types.CodeType) and c.co_name==name]
    require(len(matches)==1,'exact source code symbol required: '+name)
    return matches[0]


def _check_function(fn, module, source_bytes, name):
    require(type(fn) is types.FunctionType and fn.__globals__ is module.__dict__ and fn.__name__==name,
        'original function/global binding differs')
    ref=_nested_code(compile(source_bytes,str(module.__file__),'exec',dont_inherit=True),name)
    require(code_sha(fn.__code__)==code_sha(ref),'original function code differs: '+name)
    return ref


def _function_snapshot(fn):
    return (fn.__code__,fn.__defaults__,fn.__kwdefaults__,copy.deepcopy(fn.__kwdefaults__),fn.__annotations__,copy.deepcopy(fn.__annotations__))


def _function_same(fn,s):
    return (fn.__code__ is s[0] and fn.__defaults__ is s[1] and fn.__kwdefaults__ is s[2]
        and fn.__kwdefaults__==s[3] and fn.__annotations__ is s[4] and fn.__annotations__==s[5])


def _restore_function(fn,s):
    fn.__code__,fn.__defaults__,fn.__kwdefaults__,fn.__annotations__=s[0],s[1],s[2],s[4]
    if s[2] is not None:s[2].clear();s[2].update(s[3])
    s[4].clear();s[4].update(s[5])


def derive_validator(module, *, kind):
    """Pure function derivation; no module binding changed by this API."""
    require(kind in ('timing','analyzer_chunk'),'unregistered validator kind')
    relative,digest,name=(TIMING,TIMING_SHA,'_validate_chunk') if kind=='timing' else (ANALYZER,ANALYZER_SHA,'validate_chunk')
    source_bytes=Path(module.__file__).read_bytes()
    require(hashlib.sha256(source_bytes).hexdigest()==digest,'validator source differs')
    original=getattr(module,name);_check_function(original,module,source_bytes,name)
    require(original.__defaults__ is None and original.__kwdefaults__ is None,'validator defaults changed')
    tree=ast.parse(source_bytes);before=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
    after=copy.deepcopy(before)
    if kind=='timing':
        branches=[x for x in ast.walk(after) if isinstance(x,ast.If)]
        require(len(branches)==1 and isinstance(branches[0].test,ast.BoolOp) and isinstance(branches[0].test.op,ast.Or)
            and len(branches[0].test.values)==3,'timing validator AST differs')
        removed=branches[0].test.values.pop()
        target=ast.parse('(np.abs(actions) > 1.00001).any()',mode='eval').body
        require(ast.dump(removed,include_attributes=False)==ast.dump(target,include_attributes=False),'unexpected timing clause')
        branches[0].test.values.append(removed)
        require(ast.dump(after,include_attributes=False)==ast.dump(before,include_attributes=False),'timing edit exceeded one clause')
        branches[0].test.values.pop()
    else:
        expected=ast.parse('if key == "environment_actions" and np.any(np.abs(actions) > 1.00001):\n    raise ValueError("final executable action outside normalized controller bounds")').body[0]
        matches=[]
        for parent in ast.walk(after):
            for field,value in ast.iter_fields(parent):
                if isinstance(value,list):
                    for index,node in enumerate(value):
                        if isinstance(node,ast.AST) and ast.dump(node,include_attributes=False)==ast.dump(expected,include_attributes=False):matches.append((value,index))
        require(len(matches)==1,'analyzer amplitude branch differs')
        seq,index=matches[0];removed=seq.pop(index);seq.insert(index,removed)
        require(ast.dump(after,include_attributes=False)==ast.dump(before,include_attributes=False),'analyzer edit exceeded one branch')
        seq.pop(index)
    namespace={}
    exec(compile(ast.Module(body=[after],type_ignores=[]),str(module.__file__),'exec',dont_inherit=True),module.__dict__,namespace)
    replacement=namespace[name]
    # Preserve original callable annotations/default semantics (future annotations vary across callers).
    replacement.__annotations__=dict(original.__annotations__)
    require(replacement.__defaults__==original.__defaults__ and replacement.__kwdefaults__==original.__kwdefaults__,'replacement signature differs')
    proof=dict(kind=kind,source_sha256=digest,original_code_sha256=code_sha(original.__code__),
        replacement_code_sha256=code_sha(replacement.__code__),original_ast_sha256=sig(ast.dump(before,include_attributes=False)),
        replacement_ast_sha256=sig(ast.dump(after,include_attributes=False)),removed_ast_sha256=sig(ast.dump(removed,include_attributes=False)),
        changes='one amplitude disjunct' if kind=='timing' else 'one environment amplitude branch',
        action_values_modified=False,shape_and_finite_checks_preserved=True)
    return original,replacement,proof


@contextmanager
def validator_scope(module, *, kind, alias_module=None, emit):
    require(callable(emit),'durable event callback required')
    name='_validate_chunk' if kind=='timing' else 'validate_chunk'
    original,replacement,proof=derive_validator(module,kind=kind)
    if kind=='timing':
        require(alias_module is not None and Path(alias_module.__file__).read_bytes() and sha(alias_module.__file__)==FORMAL_TIMING_SHA,
            'exact formal timing alias module required')
        require(alias_module._validate_chunk is original,'formal timing alias is already changed')
    else:require(alias_module is None,'analyzer adapter only binds its own exact validator')
    old_snapshot,new_snapshot=_function_snapshot(original),_function_snapshot(replacement)
    raised=False
    aliases=['cti_vla.evaluation.profiling._validate_chunk','cti_vla.evaluation.formal_profiling._validate_chunk'] if kind=='timing' else ['scripts/analyze_formal.py:validate_chunk']
    emit('deployment_validator_enter',proof=proof,validator_kind=kind,aliases=aliases)
    setattr(module,name,replacement)
    if alias_module is not None:setattr(alias_module,name,replacement)
    try:yield proof
    except BaseException:
        raised=True;raise
    finally:
        intact=(getattr(module,name) is replacement and (alias_module is None or getattr(alias_module,name) is replacement)
            and _function_same(original,old_snapshot) and _function_same(replacement,new_snapshot))
        _restore_function(original,old_snapshot);_restore_function(replacement,new_snapshot)
        setattr(module,name,original)
        if alias_module is not None:setattr(alias_module,name,original)
        emit('deployment_validator_exit',validator_kind=kind,aliases=aliases,bindings_intact=intact,bindings_restored=True,runner_raised=raised)
        require(intact,'validator scope/bindings changed')


def derive_one_base_lifecycle(probe):
    """Reuse v4 trusted checks; alter only four literal cardinalities 4 -> 1."""
    raw=Path(probe.__file__).read_bytes();require(hashlib.sha256(raw).hexdigest()==PROBE_SHA,'v4 probe differs')
    tree=ast.parse(raw);before=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='PrismaticProcessLifecycle')
    after=copy.deepcopy(before);counts={}
    for fn in after.body:
        if isinstance(fn,ast.FunctionDef):
            nodes=[x for x in ast.walk(fn) if isinstance(x,ast.Constant) and type(x.value) is int and x.value==4]
            if nodes:counts[fn.name]=len(nodes)
            for node in nodes:node.value=1
    require(counts=={'__init__':2,'load':1,'finish':1},'unexpected lifecycle cardinalities')
    restore=copy.deepcopy(after)
    for fn in restore.body:
        if isinstance(fn,ast.FunctionDef) and fn.name in counts:
            # Reverse by exact original AST path rather than modifying all literal ones.
            oldfn=next(x for x in before.body if isinstance(x,ast.FunctionDef) and x.name==fn.name)
            for left,right in zip(ast.walk(oldfn),ast.walk(fn)):
                if isinstance(left,ast.Constant) and type(left.value) is int and left.value==4:right.value=4
    require(ast.dump(restore,include_attributes=False)==ast.dump(before,include_attributes=False),'lifecycle edit exceeds cardinality')
    namespace={};exec(compile(ast.Module(body=[after],type_ignores=[]),str(probe.__file__),'exec',dont_inherit=True),probe.__dict__,namespace)
    proof=dict(source_sha256=PROBE_SHA,cardinality_edits=counts,expected_base_loads=1,
        original_ast_sha256=sig(ast.dump(before,include_attributes=False)),derived_ast_sha256=sig(ast.dump(after,include_attributes=False)),
        trusted_globals_exports_module_identity_checks_unchanged=True)
    return namespace['PrismaticProcessLifecycle'],proof


@contextmanager
def _one_base_loader_scope(module, lifecycle, *, checkpoint, emit):
    original=module.load_openvla_oft_components;saved=_function_snapshot(original)
    owner=threading.get_ident();calls=0;completed=0;failed=False;active=True
    def once(requested, *, device, use_minimal_prismatic_compat):
        nonlocal calls,completed,failed
        try:
            require(active and not failed and threading.get_ident()==owner,'inactive/failed/foreign-thread loader scope')
            require(calls==0 and str(requested)==str(checkpoint) and use_minimal_prismatic_compat is True,'one registered first-load request required')
            require(module.load_openvla_oft_components is once and _function_same(original,saved),'loader binding/code changed')
            calls+=1;emit('deployment_base_load_start',checkpoint=str(requested),calls=calls)
            # Goal's existing intact() sees the actual unchanged original during its component calls.
            module.load_openvla_oft_components=original
            try:
                value=lifecycle.load(original,requested,device=device)
                require(module.load_openvla_oft_components is original and _function_same(original,saved),'original loader changed during loading')
            finally:
                if module.load_openvla_oft_components is not original:failed=True
                module.load_openvla_oft_components=once
            completed+=1;emit('deployment_base_load_complete',checkpoint=str(requested),completed=completed)
            return value
        except BaseException as error:
            failed=True;emit('deployment_base_load_failed',error_type=type(error).__name__,error=str(error),calls=calls,completed=completed)
            raise
    wrapper_code=once.__code__;raised=False
    emit('deployment_base_scope_enter',expected_base_loads=1,original_code_sha256=code_sha(original.__code__))
    module.load_openvla_oft_components=once
    try:yield
    except BaseException:
        raised=True;failed=True;raise
    finally:
        active=False
        intact=module.load_openvla_oft_components is once and once.__code__ is wrapper_code and _function_same(original,saved)
        finish_error=None
        if not failed:
            try:lifecycle.finish()
            except BaseException as error:finish_error=error;failed=True
        _restore_function(original,saved);module.load_openvla_oft_components=original
        emit('deployment_base_scope_exit',calls=calls,completed=completed,failed=failed,runner_raised=raised,
            original_binding_restored=module.load_openvla_oft_components is original,original_intact=intact)
        require(intact,'loader scope or original function changed')
        if finish_error is not None:raise finish_error
        if not raised:require(not failed and calls==completed==1,'single base load did not finish cleanly')


@contextmanager
def _source_imports(source):
    for name,module in list(sys.modules.items()):
        if name=='cti_vla' or name.startswith(('cti_vla.','cti_vla_baselines')):
            origin=getattr(module,'__file__',None)
            require(not origin or source/'src' in Path(origin).resolve().parents,'fresh canonical source process required')
    previous=list(sys.path);sys.path.insert(0,str(source/'src'))
    try:yield
    finally:sys.path[:]=previous


@contextmanager
def runtime_scope(*, project_root, source_root, contract, emit):
    global _PROCESS_USED
    require(callable(emit),'durable event callback required')
    if not _LOCK.acquire(blocking=False):raise RuntimeError('duplicate/nested deployment runtime scope')
    watched=None;raised=False;success=False
    try:
        require(not _PROCESS_USED,'fresh process required after a prior runtime attempt')
        watched=validate_contract(contract,project_root=project_root,source_root=source_root)
        _PROCESS_USED=True
        project,source=direct(project_root),direct(source_root)
        emit('deployment_runtime_enter',runtime_version=VERSION,contract_sha256=sig(contract),contract=copy.deepcopy(contract),
            activation_external_required=True,scientific_completion_inferred=False)
        with _source_imports(source),ExitStack() as scopes:
            runtime=importlib.import_module('cti_vla.evaluation.libero_runtime')
            trials=importlib.import_module('cti_vla.evaluation.formal_trials')
            loader=importlib.import_module('cti_vla.models.openvla_oft_loader')
            compat=importlib.import_module('cti_vla.models.openvla_oft_runtime_compat')
            require(direct(loader.__file__)==source/LOADER,'noncanonical loader module path')
            _check_function(loader.load_openvla_oft_components,loader,(source/LOADER).read_bytes(),'load_openvla_oft_components')
            require(loader.load_openvla_oft_components.__defaults__ is None and loader.load_openvla_oft_components.__kwdefaults__==dict(device='cuda:0',dtype=loader.torch.bfloat16,num_images_in_input=2,local_files_only=True,use_minimal_prismatic_compat=False),'original loader defaults changed')
            probe=load(project/PROBE,PROBE_SHA);cls,proof=derive_one_base_lifecycle(probe)
            life=cls([contract['checkpoint']],compat,runtime_path=source/RUNTIME,runtime_sha256=sha(source/RUNTIME))
            require(not life.current(),'one-suite execution requires fresh Prismatic namespace')
            emit('deployment_lifecycle_derivation',proof=proof)
            adapter=load(project/ACTION,ACTION_SHA)
            scopes.enter_context(adapter.install_action_execution_compat(project_root=project,source_root=source,
                runtime_module=runtime,formal_trials_module=trials,expected_adapter_sha256=ACTION_SHA,emit=emit))
            if contract['stage'] in ('full','components'):
                timing=importlib.import_module('cti_vla.evaluation.profiling')
                formal=importlib.import_module('cti_vla.evaluation.formal_profiling')
                scopes.enter_context(validator_scope(timing,kind='timing',alias_module=formal,emit=emit))
            scopes.enter_context(_one_base_loader_scope(loader,life,checkpoint=contract['checkpoint'],emit=emit))
            yield
        success=True
    except BaseException:
        raised=True;raise
    finally:
        try:
            if watched is not None:
                unchanged(watched)
                emit('deployment_runtime_exit',runtime_version=VERSION,contract_sha256=sig(contract),runner_raised=raised,
                    returned=success,source_inputs_unchanged=True,scientific_completion_inferred=False)
        finally:_LOCK.release()



def expected_asset_identities(*, project_root, source_root, contract, asset_contract):
    """Read-only original metadata validators, never target tensors or GPU.

    The caller must pass the checked contract, not identities copied from a raw
    journal. Production identities describe P/S exactly; no path normalization
    of a previously emitted identity is permitted.
    """
    validate_contract(contract,project_root=project_root,source_root=source_root)
    suite=contract['suite'];project,source=direct(project_root),direct(source_root)
    if suite not in ('libero_object','libero_goal'):
        require(asset_contract is None,'legacy suite has no asset contract')
        return None
    asset=load(project/ASSET,ASSET_SHA);asset.validate_contract(asset_contract,suite,project)
    metadata=load(project/META,META_SHA)
    result={'metadata':metadata.validate_asset_metadata_compat(project_root=project,source_root=source,
        registration_path=project/asset.META_REG,expected_adapter_sha256=META_SHA)}
    if suite=='libero_goal':
        goal=load(project/GOAL,GOAL_SHA)
        result['component']=goal.validate_goal_component_compat(project_root=project,source_root=source,
            contract=asset_contract['component_implementation'])
    return result

def run_with_asset_contexts(runner, *, project_root, source_root, contract, asset_contract, emit):
    """runner is a zero-argument closure over the unchanged legacy.run and args.

    Caller owns its typed invocation, source/panel/checkpoint gates, journal, locks,
    root activation and final receipt. This helper never executes a stage wrapper.
    """
    require(callable(runner) and callable(emit),'runner closure and durable event callback required')
    validate_contract(contract,project_root=project_root,source_root=source_root)
    suite=contract['suite'];project,source=direct(project_root),direct(source_root)
    with ExitStack() as scopes:
        if suite in ('libero_object','libero_goal'):
            asset=load(project/ASSET,ASSET_SHA)
            asset.validate_contract(asset_contract,suite,project)
            metadata=load(project/META,META_SHA)
            scopes.enter_context(metadata.install_asset_metadata_compat(project_root=project,source_root=source,
                registration_path=project/asset.META_REG,expected_adapter_sha256=META_SHA,emit=emit))
            if suite=='libero_goal':
                goal=load(project/GOAL,GOAL_SHA)
                scopes.enter_context(goal.install_goal_component_compat(project_root=project,source_root=source,
                    contract=asset_contract['component_implementation'],emit=emit))
        else:require(asset_contract is None,'legacy suite cannot silently request asset compatibility')
        scopes.enter_context(runtime_scope(project_root=project,source_root=source,contract=contract,emit=emit))
        return runner()


# Exact accepted GPU action identity; its source raw SHA is d9196329c94a816933c57c22e09c9adacf2fe7a773635802024c06dc41a53e4e.
EXPECTED_ACTION_IDENTITY = {'action_transformation': 'none; existing finite PolicyChunk passed unchanged', 'adapter_sha256': 'b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185', 'alias_module': 'src/cti_vla/evaluation/formal_trials.py', 'alias_module_sha256': '93a0971dbc8bbf4cb462490b0b00a337d92f015af83b798bb635163a9cb864f6', 'ast_proof': {'code_marshal_version': 2, 'exact_removed_node_path': [['body', 5], ['body', 5], ['body', 0], ['body', 7]], 'original_code_sha256': 'a1c042be2f0e37890cb003ab3840bc22598d7887140c230cd77a8d0ef5217a60', 'original_function_ast_sha256': '43034be729b1b5441a1a775e019da55001cc1695911862c6119949cda2652193', 'other_AST_nodes_unchanged': True, 'removed_branch_ast_sha256': '402453319b026104e894baa4cf32add9433030e4f8759117d918f10ad12deac3', 'removed_if_count': 1, 'replacement_code_sha256': '59bf996c15054234aeff8ff34916234781fc2b89026faad1dc68aa3cd8bbae37', 'replacement_function_ast_sha256': '49be9e13ff5be39f74bd1ed9265ef0b5a3277c6f306e1cf77279567676ed150a'}, 'candidate_only': True, 'controller_verified': False, 'deployment_authorized': False, 'frozen_source_files': 173, 'frozen_source_sha256': 'dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e', 'kind': 'candidate_action_execution_identity', 'methods': 'uniform scope for dense/uniform/A/B; no method argument or branch', 'policy_chunk_construction': {'base': 'builtins.object', 'code_marshal_version': 2, 'construction_function_code_sha256': {'__delattr__': '2db98554470e4d985d927730f5f43255e316d9d087105c476414226e8c33fa1b', '__init__': '1468b2bfd177626f0f6daaede9189e8883877f9691c1c23f92dfd86c9ca0a10b', '__post_init__': 'e984eaebdf4783b7af63c1ccca00cbe6462bc00cf405d62d5275888813856028', '__setattr__': '141e7e42e5c862578fbeb3e8274eb997b2fd1fa1f14f76d115dc15f52f3f55d3'}, 'exact_frozen_class_AST_sha256': '7c3743b5517af3ee339e21229790250f37bf1586329aa0e0e815a39fe420fb69', 'generated_code_reference': 'same_runtime_frozen_class_dataclass', 'metaclass': 'builtins.type', 'same_runtime_reference': True, 'source_defined_code_reference': 'full_frozen_module_compile_without_execution'}, 'real_environment_acceptance_pending': True, 'registration_sha256': '0917bff60e632a5be3c2db50b16daa0b904e4754a3ba31334802060f75d3eefe', 'runtime_python': '3.11.7 (main, Dec 15 2023, 18:12:31) [GCC 11.2.0]', 'schema': 'formal_main_v2', 'source_inventory_sha256': '5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926', 'source_root': '/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_run_564be0995e', 'target_module': 'src/cti_vla/evaluation/libero_runtime.py', 'target_module_sha256': '2fc1bacbd1268a36f2e31451c70a650be4f8d0c8f6803e7c8b2a3d45f701c781', 'version': 'formal-main-v2-controller-exec-cpu-candidate-v3-full-module-constructor-identity'}
EXPECTED_TIMING_PROOF = {'kind': 'timing', 'source_sha256': '648cf11400b0d70f2e4ee99fd8d4c26f917b38957b546ad5bfc578915d1d0404', 'original_code_sha256': 'b5d16b8ed702ee7acc8ea96ae010b2adb3e76a0e927d4ad9abaad266b4033964', 'replacement_code_sha256': '6ece22bd645ea19f56ca8bb91cf1c51151f418d7de0e9555b70b7c3c4ee61f12', 'original_ast_sha256': 'd6384e8cd8c68eec9889d72388cbd8bb7bac034859d377e292a8c14b680b5d6a', 'replacement_ast_sha256': 'f25ad064b13ae015b7e85afe09ff1942daf3e5d58c4d8b2fccc4839dca2893b7', 'removed_ast_sha256': '2209262fe785f12612581f1255404a842d226f66ae75a8e4fb15a53c63a5593c', 'changes': 'one amplitude disjunct', 'action_values_modified': False, 'shape_and_finite_checks_preserved': True}
EXPECTED_BASE_CODE_SHA = 'e34e8ab02d662a8785fc959cdae78707e2ced447294a74bf11c799413de34b36'


def verify_runtime_events(events, contract, *, expected_asset_identities=None):
    """Pure structural verification; no IO, GPU inference, root approval or scientific pass.

    Only a clean returned journal can satisfy this function. Failed/partial
    journals are retained by the caller and raise here rather than receiving a
    success-shaped receipt. Outer job/scheduler/runner gates remain mandatory.
    """
    require(type(events) is list and events and all(type(x) is dict for x in events),'nonempty raw event list required')
    require(contract.get('schema')=='formal_main_v2' and contract.get('kind')=='formal_action_deployment_runtime_contract'
        and contract.get('version')==VERSION and contract.get('stage') in STAGES and contract.get('suite') in SUITES,
        'unregistered runtime event contract')
    suite,stage=contract['suite'],contract['stage']
    assets=suite in ('libero_object','libero_goal');goal=suite=='libero_goal';timing=stage in ('full','components')
    if assets:
        expected_keys={'metadata','component'} if goal else {'metadata'}
        require(type(expected_asset_identities) is dict and set(expected_asset_identities)==expected_keys,'prevalidated exact asset identities required')
    else:require(expected_asset_identities is None,'legacy suite cannot accept asset identity evidence')
    prefixes=('deployment_','action_execution_candidate_','asset_metadata_compat_','goal_component_')
    selected=[r for r in events if isinstance(r.get('event'),str) and r['event'].startswith(prefixes)]
    expected=[]
    if assets:expected+=['asset_metadata_compat_enter']
    if goal:expected+=['goal_component_compat_enter']
    expected+=['deployment_runtime_enter','deployment_lifecycle_derivation','action_execution_candidate_enter']
    if timing:expected+=['deployment_validator_enter']
    expected+=['deployment_base_scope_enter']
    if assets:expected+=['asset_metadata_compat_load_start','asset_metadata_compat_load_complete']
    expected+=['deployment_base_load_start']
    if goal:expected+=['goal_component_load_start','goal_component_load_complete']*2
    expected+=['deployment_base_load_complete','deployment_base_scope_exit']
    if timing:expected+=['deployment_validator_exit']
    expected+=['action_execution_candidate_exit','deployment_runtime_exit']
    if goal:expected+=['goal_component_compat_exit']
    if assets:expected+=['asset_metadata_compat_exit']
    require([r['event'] for r in selected]==expected,'runtime scope event sequence is incomplete, duplicated, failed or reordered')
    def row(name):return next(r for r in selected if r['event']==name)
    entered=row('deployment_runtime_enter');exited=row('deployment_runtime_exit')
    require(entered.get('contract')==contract and entered.get('contract_sha256')==sig(contract)
        and entered.get('runtime_version')==exited.get('runtime_version')==VERSION
        and exited.get('contract_sha256')==sig(contract)
        and entered.get('activation_external_required') is True
        and entered.get('scientific_completion_inferred') is False
        and exited.get('scientific_completion_inferred') is False
        and exited.get('runner_raised') is False and exited.get('returned') is True
        and exited.get('source_inputs_unchanged') is True,'runtime returned/contract identity differs')
    proof=row('deployment_lifecycle_derivation').get('proof',{})
    require(proof==dict(source_sha256=PROBE_SHA,cardinality_edits={'__init__':2,'load':1,'finish':1},expected_base_loads=1,
        original_ast_sha256='50d9865e833bacd05cacc4af0856910bfa645a7fb67e3f091bae60446b14132a',
        derived_ast_sha256='8aaeb549969bd7656e7e7067eaba7c70ef17f91f5434f42ce9b3951c30517105',
        trusted_globals_exports_module_identity_checks_unchanged=True),'one-load derivation differs')
    ident=row('action_execution_candidate_enter').get('identity',{})
    require(sig({k:v for k,v in ident.items() if k not in ('watched_files','identity_sha256')})==sig(EXPECTED_ACTION_IDENTITY),
        'actual unchanged action adapter identity/code/constructor differs')
    require(ident.get('identity_sha256')==sig({k:v for k,v in ident.items() if k!='identity_sha256'}),'action identity signature differs')
    watched=ident.get('watched_files',{})
    require(type(watched) is dict,'action watched evidence missing')
    frozen={k[len(str(S)) + 1:]:v for k,v in watched.items() if k.startswith(str(S)+'/')}
    require(len(frozen)==173 and hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()==SOURCE_SHA,
        'action identity frozen173 map differs')
    require(len(watched)==176,'action identity watched closure count differs')
    nonfrozen={k:v for k,v in watched.items() if not k.startswith(str(S)+'/')}
    require(any(nonfrozen=={str(root/ACTION):ACTION_SHA,str(root/INVENTORY):INVENTORY_SHA,
        str(root/'configs/experiments/formal_main_v2_action_execution_compat_v1.json'):'0917bff60e632a5be3c2db50b16daa0b904e4754a3ba31334802060f75d3eefe'} for root in (P,R)),
        'action identity non-source closure differs')
    last=row('action_execution_candidate_exit')
    require(last.get('identity_sha256')==ident['identity_sha256'] and last.get('runner_raised') is False
        and last.get('fresh_runtime_required') is False and last.get('changed_inputs')==[]
        and last.get('candidate_only') is True and last.get('deployment_authorized') is False
        and all(last.get(k) is True for k in ('original_bindings_restored','scope_binding_and_code_intact',
            'finite_shape_and_observation_helpers_intact','source_inputs_unchanged','policy_chunk_construction_intact','policy_chunk_construction_restored')),
        'action scope is not intact/restored; original candidate status must not be rewritten')
    base=row('deployment_base_scope_enter');beg=row('deployment_base_load_start');done=row('deployment_base_load_complete');end=row('deployment_base_scope_exit')
    require(base.get('expected_base_loads')==1 and base.get('original_code_sha256')==EXPECTED_BASE_CODE_SHA
        and beg.get('checkpoint')==done.get('checkpoint')==contract['checkpoint'] and beg.get('calls')==done.get('completed')==1
        and end.get('calls')==end.get('completed')==1 and end.get('failed') is False and end.get('runner_raised') is False
        and end.get('original_binding_restored') is True and end.get('original_intact') is True,'one original base load did not complete and restore')
    if timing:
        v=row('deployment_validator_enter');ve=row('deployment_validator_exit');pr=v.get('proof',{})
        require(v.get('validator_kind')==ve.get('validator_kind')=='timing' and pr.get('kind')=='timing'
            and sig(pr)==sig(EXPECTED_TIMING_PROOF) and v.get('aliases')==ve.get('aliases')==contract['policy']['timing_aliases']
            and pr.get('action_values_modified') is False and pr.get('shape_and_finite_checks_preserved') is True
            and ve.get('bindings_intact') is True and ve.get('bindings_restored') is True and ve.get('runner_raised') is False,
            'both timing validator bindings must be intact and restored')
    if assets:
        meta=row('asset_metadata_compat_exit');mi=row('asset_metadata_compat_enter').get('identity',{})
        require(sig(mi)==sig(expected_asset_identities['metadata']),'metadata identity differs from independently validated source/model identity')
        require(all(meta.get(k) is True for k in ('original_loader_restored','directory_verifier_unchanged','binding_intact',
            'original_loader_code_unchanged','directory_verifier_code_unchanged','frozen_source_and_inputs_unchanged'))
            and meta.get('runner_raised') is False and [meta.get(k) for k in ('adapted_calls_attempted','adapted_calls_completed','passthrough_calls')]==[1,1,0]
            and row('asset_metadata_compat_load_start').get('view')==mi.get('views',{}).get(suite)
            and row('asset_metadata_compat_load_complete').get('suite')==suite,'metadata context sequence/identity/restore differs')
    if goal:
        ge=row('goal_component_compat_exit');gi=row('goal_component_compat_enter').get('identity',{})
        require(sig(gi)==sig(expected_asset_identities['component']),'Goal identity differs from independently validated component contract')
        require(all(ge.get(k) is True for k in ('original_loader_restored','original_function_codes_unchanged','binding_intact',
            'torch_load_unchanged','source_inputs_unchanged','component_files_unchanged')) and ge.get('runner_raised') is False
            and [ge.get(k) for k in ('component_calls_attempted','component_calls_completed','rejected_calls')]==[2,2,0],'Goal context failed/restoration differs')
        for event in ('goal_component_load_start','goal_component_load_complete'):
            items=[r for r in selected if r['event']==event]
            require([r.get('call_id') for r in items]==[0,1] and [r.get('mapping') for r in items]==gi.get('mappings'),
                'Goal original two component mappings/order differ')
    return dict(schema='formal_main_v2',kind='action_deployment_runtime_structure',status='complete_runtime_structure_only',
        contract_sha256=sig(contract),event_count=len(selected),all_source_and_binding_contexts_restored=True,
        original_base_loads=1,synthetic_input=any(r.get('synthetic') is True or r.get('synthetic_fixture') is True for r in events),
        scientific_completion_inferred=False,GPU_acceptance_inferred=False,root_activation_inferred=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['inspect'])
    parser.add_argument('--project-root',type=Path,default=R)
    parser.add_argument('--source-root',type=Path,default=S)
    parser.add_argument('--suite',choices=SUITES,required=True)
    parser.add_argument('--stage',choices=STAGES,required=True)
    args=parser.parse_args()
    contract=make_contract(project_root=args.project_root,source_root=args.source_root,suite=args.suite,stage=args.stage)
    watched=validate_contract(contract,project_root=args.project_root,source_root=args.source_root)
    print(json.dumps(dict(kind='action_deployment_runtime_inspection',status='metadata_verified_only',contract=contract,
        contract_sha256=sig(contract),watched_files=watched,GPU_calls=0,Slurm_submissions=0,root_activation=False),ensure_ascii=False,indent=2))

if __name__=='__main__':main()

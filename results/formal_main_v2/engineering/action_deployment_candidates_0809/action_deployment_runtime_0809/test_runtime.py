"""CPU only: real frozen validator/installer bytecode; fake model loading explicitly synthetic."""
from pathlib import Path
import copy,importlib,importlib.util,json,sys,types
import numpy as np
import pytest
D=Path(__file__).parent
spec=importlib.util.spec_from_file_location('deployment_candidate_test',D/'runtime.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
sys.path.insert(0,str(c.S/'src'))
from cti_vla.evaluation import profiling,formal_profiling
from cti_vla.models import openvla_oft_runtime_compat as compat


def events():
    rows=[]
    return rows,lambda event,**fields:rows.append(dict(event=event,**fields))


def contract(suite='libero_10',stage='development'):
    return c.make_contract(project_root=c.R,source_root=c.S,suite=suite,stage=stage)


@pytest.mark.parametrize('suite',c.SUITES)
@pytest.mark.parametrize('stage',c.STAGES)
def test_exact_contract_all_suites_and_allowed_stages(suite,stage):
    value=contract(suite,stage)
    assert value['suite']==suite and value['stage']==stage
    assert value['policy']['expected_base_loads']==1
    assert value['policy']['final_allowed'] is False
    assert value['engineering_acceptance']['root']['sha256']==c.ROOT_GPU_SHA
    assert value['engineering_acceptance']['independent']['sha256']==c.IND_GPU_SHA
    assert 'gpu_submission_authorized' not in value and 'candidate_only' not in value


@pytest.mark.parametrize('key,value',[('stage','final'),('suite','other'),('implementation_sha256','0'*64),
 ('checkpoint','/bad'),('source_root','/bad'),('candidate_only',False),('root_activation',True)])
def test_changed_contract_rejected(key,value):
    v=contract();v[key]=value
    with pytest.raises(ValueError):c.validate_contract(v,project_root=c.R,source_root=c.S)


def test_final_rejected_before_metadata_read(monkeypatch):
    monkeypatch.setattr(c,'read_pinned',lambda *a:pytest.fail('must reject before reads'))
    with pytest.raises(ValueError):c.make_contract(project_root='/sealed',source_root='/sealed',suite='libero_10',stage='final')


def test_real_read_only_metadata_closure():
    refs=c.validate_contract(contract(),project_root=c.R,source_root=c.S)
    assert len(refs)==184 and refs[str(c.R/c.ROOT_GPU)]==c.ROOT_GPU_SHA


def test_pure_validator_derivation_retains_original():
    old=profiling._validate_chunk
    original,replacement,proof=c.derive_validator(profiling,kind='timing')
    assert original is old and profiling._validate_chunk is old
    x=np.full((8,7),2.5);chunk=types.SimpleNamespace(environment_actions=x)
    with pytest.raises(ValueError):old(chunk)
    assert replacement(chunk) is None and np.all(x==2.5)
    assert proof['shape_and_finite_checks_preserved'] and not proof['action_values_modified']


@pytest.mark.parametrize('actions',[np.zeros((7,7)),np.zeros((8,6)),np.full((8,7),np.nan),np.full((8,7),np.inf),np.full((8,7),-np.inf)])
def test_invalid_timed_chunk_still_refused(actions):
    rows,emit=events();old=profiling._validate_chunk
    with c.validator_scope(profiling,kind='timing',alias_module=formal_profiling,emit=emit):
        assert formal_profiling._validate_chunk is profiling._validate_chunk
        with pytest.raises(ValueError):profiling._validate_chunk(types.SimpleNamespace(environment_actions=actions))
    assert formal_profiling._validate_chunk is profiling._validate_chunk is old
    assert rows[-1]['bindings_restored']


def test_full_timing_cpu_endpoint_metadata_unchanged():
    rows,emit=events();actions=np.full((8,7),7.5);before=actions.tobytes()
    identity={'suite':'libero_10','method':'dense','visual_tokens':512}
    meta=dict(schema='formal_main_v2',**identity,policy_calls=1,vision_calls=1,packing_calls=1,
        scorer_calls=0,future_head_calls=0,language_cache='disabled',diagnostic_indices_recorded=False)
    chunk=types.SimpleNamespace(environment_actions=actions,metadata=meta)
    with c.validator_scope(profiling,kind='timing',alias_module=formal_profiling,emit=emit):
        assert len(formal_profiling._validate_timed_chunk(chunk,identity))==64
        chunk.environment_actions=actions.tolist()
        with pytest.raises(ValueError,match='CPU NumPy'):formal_profiling._validate_timed_chunk(chunk,identity)
        chunk.environment_actions=actions
        meta['future_head_calls']=1
        with pytest.raises(ValueError,match='deployed identity'):formal_profiling._validate_timed_chunk(chunk,identity)
    assert actions.tobytes()==before


def test_validator_runner_exception_restores():
    old=profiling._validate_chunk;rows,emit=events()
    with pytest.raises(RuntimeError,match='runner failed'):
        with c.validator_scope(profiling,kind='timing',alias_module=formal_profiling,emit=emit):raise RuntimeError('runner failed')
    assert profiling._validate_chunk is formal_profiling._validate_chunk is old
    assert rows[-1]['runner_raised']


@pytest.mark.parametrize('mutation',['alias','original_code','replacement_code','annotations'])
def test_validator_drift_detected_and_restored(mutation):
    old=profiling._validate_chunk;snapshot=c._function_snapshot(old);rows,emit=events()
    with pytest.raises(ValueError,match='scope/bindings'):
        with c.validator_scope(profiling,kind='timing',alias_module=formal_profiling,emit=emit):
            if mutation=='alias':formal_profiling._validate_chunk=lambda x:None
            if mutation=='original_code':old.__code__=(lambda x:None).__code__
            if mutation=='replacement_code':profiling._validate_chunk.__code__=(lambda x:None).__code__
            if mutation=='annotations':old.__annotations__['tampered']=1
    assert profiling._validate_chunk is formal_profiling._validate_chunk is old and c._function_same(old,snapshot)


def test_wrong_alias_rejected_before_binding(monkeypatch):
    old=profiling._validate_chunk;rows,emit=events()
    monkeypatch.setattr(formal_profiling,'_validate_chunk',lambda x:None)
    with pytest.raises(ValueError,match='alias is already'):
        with c.validator_scope(profiling,kind='timing',alias_module=formal_profiling,emit=emit):pass
    assert profiling._validate_chunk is old


def test_analyzer_chunk_same_values_and_all_other_checks():
    module=c.load(c.R/c.ANALYZER,c.ANALYZER_SHA)
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    from cti_vla.evaluation.libero_runtime import INPUTS_VERSION
    from cti_vla.evaluation.libero_runtime import ACTION_VERSION
    identity=dict(suite='libero_10',method='dense',visual_tokens=512)
    meta=dict(schema='formal_main_v2',**identity,per_camera_budgets=[256,256],policy_calls=1,vision_calls=1,
        packing_calls=1,scorer_calls=0,future_head_calls=0,language_cache='disabled',inputs_version=INPUTS_VERSION,
        action_version=ACTION_VERSION,packing_version=PACKING_VERSION,retained_indices=list(range(512)))
    chunk=dict(metadata=meta,normalized_actions=np.zeros((8,7)).tolist(),environment_actions=np.full((8,7),3.5).tolist())
    before=json.dumps(chunk,sort_keys=True);rows,emit=events();old=module.validate_chunk
    with pytest.raises(ValueError,match='outside normalized'):old(chunk,identity)
    with c.validator_scope(module,kind='analyzer_chunk',emit=emit):
        assert module.validate_chunk(chunk,identity) is None
        wrong=copy.deepcopy(chunk);wrong['metadata']['retained_indices']=list(range(511))
        with pytest.raises(ValueError,match='hard token'):module.validate_chunk(wrong,identity)
        wrong=copy.deepcopy(chunk);wrong['environment_actions'][0][0]=float('nan')
        with pytest.raises(ValueError,match='actions are invalid'):module.validate_chunk(wrong,identity)
    assert module.validate_chunk is old and json.dumps(chunk,sort_keys=True)==before


@pytest.fixture
def life():
    # Explicit isolated CPU interpreter fixture; no production module removal.
    assert not [n for n in sys.modules if n=='prismatic' or n.startswith('prismatic.')]
    probe=c.load(c.R/c.PROBE,c.PROBE_SHA);cls,proof=c.derive_one_base_lifecycle(probe)
    value=cls(['/synthetic-model'],compat,runtime_path=c.S/c.RUNTIME,runtime_sha256=c.sha(c.S/c.RUNTIME))
    try:yield value
    finally:
        for n in list(sys.modules):
            if n=='prismatic' or n.startswith('prismatic.'):del sys.modules[n]


def fake_loader_module(life,*,fail=False):
    module=types.SimpleNamespace();count=[]
    def frozen_loader(checkpoint,*,device,use_minimal_prismatic_compat):
        assert module.load_openvla_oft_components is frozen_loader
        count.append((checkpoint,device,use_minimal_prismatic_compat))
        compat.install_prismatic_runtime_compat(use_minimal_compat=use_minimal_prismatic_compat)
        if fail:raise RuntimeError('synthetic loader failure')
        return 'synthetic-model'
    module.load_openvla_oft_components=frozen_loader
    return module,frozen_loader,count


def test_one_load_real_frozen_installer_and_restoration(life):
    module,old,count=fake_loader_module(life);rows,emit=events()
    with c._one_base_loader_scope(module,life,checkpoint='/synthetic-model',emit=emit):
        assert module.load_openvla_oft_components('/synthetic-model',device='synthetic-cpu',use_minimal_prismatic_compat=True)=='synthetic-model'
    assert module.load_openvla_oft_components is old and count==[('/synthetic-model','synthetic-cpu',True)]
    assert rows[-1]['completed']==1 and rows[-1]['original_binding_restored']


@pytest.mark.parametrize('case',['second','wrong_checkpoint','false_flag','zero','loader_error','caught_error','runtime_constant','runtime_helper','module_path'])
def test_single_loader_fail_closed(life,case):
    module,old,count=fake_loader_module(life,fail=case in ('loader_error','caught_error'));rows,emit=events()
    with pytest.raises((ValueError,RuntimeError)):
        with c._one_base_loader_scope(module,life,checkpoint='/synthetic-model',emit=emit):
            if case=='zero':pass
            elif case=='caught_error':
                try:module.load_openvla_oft_components('/synthetic-model',device='cpu',use_minimal_prismatic_compat=True)
                except RuntimeError:pass
            else:
                module.load_openvla_oft_components('/bad' if case=='wrong_checkpoint' else '/synthetic-model',
                    device='cpu',use_minimal_prismatic_compat=case!='false_flag')
                if case=='second':module.load_openvla_oft_components('/synthetic-model',device='cpu',use_minimal_prismatic_compat=True)
                if case=='runtime_constant':sys.modules['prismatic.vla.constants'].NUM_ACTIONS_CHUNK=4
                if case=='runtime_helper':sys.modules['prismatic.training.train_utils'].get_current_action_mask=lambda x:x
                if case=='module_path':sys.modules['prismatic'].__path__.append('/bad')
    assert module.load_openvla_oft_components is old and rows[-1]['original_binding_restored']


def test_one_load_goal_original_intact_context_composition(life,monkeypatch):
    # Original Goal implementation is exercised; tensors/checkpoint IO are synthetic.
    goal=c.load(c.R/c.GOAL,c.GOAL_SHA);module=types.SimpleNamespace();trace=[];rows,emit=events()
    import torch
    module.torch=torch
    def tensor_loader(path):trace.append(str(path));return {'weight':object()}
    def remove_prefix(value):return value
    def base_loader(checkpoint,*,device,use_minimal_prismatic_compat):
        assert module.load_openvla_oft_components is base_loader
        compat.install_prismatic_runtime_compat(use_minimal_compat=use_minimal_prismatic_compat)
        module._load_component_state('/fake/action150.pt');module._load_component_state('/fake/proprio150.pt')
        return 'synthetic-goal-model'
    module._load_component_state=tensor_loader;module.remove_uniform_ddp_prefix=remove_prefix;module.load_openvla_oft_components=base_loader
    identity=dict(original_function_code_sha256={name:goal.code_sha(getattr(module,name)) for name in goal.SYMBOLS},
        mappings=[dict(requested_path='/fake/action150.pt',target_path='/fake/action50.pt'),dict(requested_path='/fake/proprio150.pt',target_path='/fake/proprio50.pt')])
    monkeypatch.setattr(goal,'_verify_target',lambda row:Path(row['target_path']))
    monkeypatch.setattr(goal,'_unchanged',lambda identity:None)
    with goal._scoped_component_loader(module,identity,emit):
        with c._one_base_loader_scope(module,life,checkpoint='/synthetic-model',emit=emit):
            assert module.load_openvla_oft_components('/synthetic-model',device='cpu',use_minimal_prismatic_compat=True)=='synthetic-goal-model'
    assert trace==['/fake/action50.pt','/fake/proprio50.pt']
    assert module.load_openvla_oft_components is base_loader and module._load_component_state is tensor_loader
    assert next(r for r in rows if r['event']=='goal_component_compat_exit')['original_loader_restored']


@pytest.mark.parametrize('suite,order',[('libero_spatial',['runtime+','runner','runtime-']),
 ('libero_object',['metadata+','runtime+','runner','runtime-','metadata-']),
 ('libero_goal',['metadata+','goal+','runtime+','runner','runtime-','goal-','metadata-'])])
def test_composition_uses_original_runner_and_order(monkeypatch,suite,order):
    from contextlib import contextmanager
    trace=[];value=contract(suite)
    @contextmanager
    def scope(name):
        trace.append(name+'+')
        try:yield
        finally:trace.append(name+'-')
    asset=types.SimpleNamespace(validate_contract=lambda *args:None,META_REG='x')
    metadata=types.SimpleNamespace(install_asset_metadata_compat=lambda **kwargs:scope('metadata'))
    goal=types.SimpleNamespace(install_goal_component_compat=lambda **kwargs:scope('goal'))
    monkeypatch.setattr(c,'validate_contract',lambda *args,**kwargs:{})
    monkeypatch.setattr(c,'load',lambda path,digest:{c.ASSET_SHA:asset,c.META_SHA:metadata,c.GOAL_SHA:goal}[digest])
    monkeypatch.setattr(c,'runtime_scope',lambda **kwargs:scope('runtime'))
    def runner():trace.append('runner');return object_result
    object_result=object()
    assert c.run_with_asset_contexts(runner,project_root=c.R,source_root=c.S,contract=value,
        asset_contract=None if suite=='libero_spatial' else {'component_implementation':{}},emit=lambda *a,**k:None) is object_result
    assert trace==order


def test_cli_has_no_run_submit_final():
    import subprocess
    for args in [['run'],['submit'],['inspect','--suite','libero_10','--stage','final']]:
        result=subprocess.run([sys.executable,'-B',str(D/'runtime.py'),*args],capture_output=True,text=True)
        assert result.returncode!=0


def test_full_runtime_original_cpu_rejection_restores_and_poison(monkeypatch):
    # Actual canonical loader is reached, but rejects CPU before any CUDA API or weights.
    from cti_vla.models import openvla_oft_loader as loader
    from cti_vla.evaluation import libero_runtime,formal_trials
    monkeypatch.setattr(c,'_PROCESS_USED',False)
    value=contract(stage='full');rows,emit=events()
    original=loader.load_openvla_oft_components;episode=libero_runtime.run_episode;validator=profiling._validate_chunk
    with pytest.raises(ValueError,match='explicit CUDA'):
        with c.runtime_scope(project_root=c.R,source_root=c.S,contract=value,emit=emit):
            loader.load_openvla_oft_components(value['checkpoint'],device='cpu',use_minimal_prismatic_compat=True)
    assert loader.load_openvla_oft_components is original
    assert libero_runtime.run_episode is formal_trials.run_episode is episode
    assert profiling._validate_chunk is formal_profiling._validate_chunk is validator
    assert rows[-1]['returned'] is False and rows[-1]['runner_raised']
    with pytest.raises(ValueError,match='fresh process'):
        with c.runtime_scope(project_root=c.R,source_root=c.S,contract=value,emit=emit):pass
    with pytest.raises(ValueError):c.verify_runtime_events(rows,value)


def synthetic_runtime_journal(suite='libero_10',stage='development'):
    """Declared synthetic structural evidence; never a real execution/GPU receipt."""
    v=contract(suite,stage);rows=[]
    def add(event,**kw):rows.append(dict(event=event,synthetic_fixture=True,**kw))
    asset=suite in ('libero_object','libero_goal');goal=suite=='libero_goal';timing=stage in ('full','components')
    view={'synthetic':True,'suite':suite}
    mappings=[dict(requested_path='/synthetic/action150',target_path='/synthetic/action50'),
        dict(requested_path='/synthetic/proprio150',target_path='/synthetic/proprio50')]
    if asset:add('asset_metadata_compat_enter',identity={'views':{suite:view}})
    if goal:add('goal_component_compat_enter',identity={'mappings':mappings})
    add('deployment_runtime_enter',runtime_version=c.VERSION,contract=v,contract_sha256=c.sig(v),activation_external_required=True,scientific_completion_inferred=False)
    probe=c.load(c.R/c.PROBE,c.PROBE_SHA);_,proof=c.derive_one_base_lifecycle(probe)
    add('deployment_lifecycle_derivation',proof=proof)
    ident=json.loads((c.R/'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v4/3039197/action_execution_identity.json').read_text())
    add('action_execution_candidate_enter',identity=ident)
    if timing:add('deployment_validator_enter',validator_kind='timing',proof=copy.deepcopy(c.EXPECTED_TIMING_PROOF),aliases=v['policy']['timing_aliases'])
    add('deployment_base_scope_enter',expected_base_loads=1,original_code_sha256=c.EXPECTED_BASE_CODE_SHA)
    if asset:
        add('asset_metadata_compat_load_start',view=view)
        add('asset_metadata_compat_load_complete',suite=suite)
    add('deployment_base_load_start',checkpoint=v['checkpoint'],calls=1)
    if goal:
        for i,mapping in enumerate(mappings):
            add('goal_component_load_start',call_id=i,mapping=mapping)
            add('goal_component_load_complete',call_id=i,mapping=mapping)
    add('deployment_base_load_complete',checkpoint=v['checkpoint'],completed=1)
    add('deployment_base_scope_exit',calls=1,completed=1,failed=False,runner_raised=False,original_binding_restored=True,original_intact=True)
    if timing:add('deployment_validator_exit',validator_kind='timing',aliases=v['policy']['timing_aliases'],bindings_intact=True,bindings_restored=True,runner_raised=False)
    add('action_execution_candidate_exit',identity_sha256=ident['identity_sha256'],runner_raised=False,fresh_runtime_required=False,
        changed_inputs=[],candidate_only=True,deployment_authorized=False,original_bindings_restored=True,scope_binding_and_code_intact=True,
        finite_shape_and_observation_helpers_intact=True,source_inputs_unchanged=True,policy_chunk_construction_intact=True,policy_chunk_construction_restored=True)
    add('deployment_runtime_exit',runtime_version=c.VERSION,contract_sha256=c.sig(v),runner_raised=False,returned=True,
        source_inputs_unchanged=True,scientific_completion_inferred=False)
    if goal:add('goal_component_compat_exit',original_loader_restored=True,original_function_codes_unchanged=True,binding_intact=True,
        torch_load_unchanged=True,source_inputs_unchanged=True,component_files_unchanged=True,runner_raised=False,
        component_calls_attempted=2,component_calls_completed=2,rejected_calls=0)
    if asset:add('asset_metadata_compat_exit',original_loader_restored=True,directory_verifier_unchanged=True,binding_intact=True,
        original_loader_code_unchanged=True,directory_verifier_code_unchanged=True,frozen_source_and_inputs_unchanged=True,
        runner_raised=False,adapted_calls_attempted=1,adapted_calls_completed=1,passthrough_calls=0)
    return rows,v


def synthetic_expected_assets(rows):
    result={}
    for row in rows:
        if row['event']=='asset_metadata_compat_enter':result['metadata']=copy.deepcopy(row['identity'])
        if row['event']=='goal_component_compat_enter':result['component']=copy.deepcopy(row['identity'])
    return result or None


@pytest.mark.parametrize('suite',c.SUITES)
@pytest.mark.parametrize('stage',c.STAGES)
def test_pure_event_verifier_only_structural_never_scientific(suite,stage):
    rows,value=synthetic_runtime_journal(suite,stage)
    result=c.verify_runtime_events(rows,value,expected_asset_identities=synthetic_expected_assets(rows))
    assert result['status']=='complete_runtime_structure_only' and result['synthetic_input'] is True
    assert all(result[k] is False for k in ('scientific_completion_inferred','GPU_acceptance_inferred','root_activation_inferred'))


@pytest.mark.parametrize('mutation',['missing','duplicate','reorder','candidate_flag','false_root_claim','action_hash',
    'wrong_base','two_loads','failed_poison','timing_alias','timing_proof','metadata','goal','source_map','unknown_event'])
def test_pure_event_verifier_failure_cases(mutation):
    rows,value=synthetic_runtime_journal('libero_goal','full')
    trusted=synthetic_expected_assets(rows)
    def row(name):return next(r for r in rows if r['event']==name)
    if mutation=='missing':rows.pop()
    if mutation=='duplicate':rows.append(rows[-1])
    if mutation=='reorder':rows[0],rows[1]=rows[1],rows[0]
    if mutation=='candidate_flag':row('action_execution_candidate_enter')['identity']['candidate_only']=False
    if mutation=='false_root_claim':row('deployment_runtime_exit')['scientific_completion_inferred']=True
    if mutation=='action_hash':row('action_execution_candidate_enter')['identity']['ast_proof']['replacement_code_sha256']='0'*64
    if mutation=='wrong_base':row('deployment_base_load_start')['checkpoint']='/wrong'
    if mutation=='two_loads':row('deployment_base_scope_exit')['calls']=2
    if mutation=='failed_poison':row('deployment_base_scope_exit')['failed']=True
    if mutation=='timing_alias':row('deployment_validator_exit')['bindings_restored']=False
    if mutation=='timing_proof':row('deployment_validator_enter')['proof']['replacement_code_sha256']='0'*64
    if mutation=='metadata':row('asset_metadata_compat_exit')['adapted_calls_completed']=0
    if mutation=='goal':row('goal_component_compat_exit')['binding_intact']=False
    if mutation=='source_map':row('action_execution_candidate_enter')['identity']['watched_files'][str(c.S/'AGENTS.md')]='0'*64
    if mutation=='unknown_event':rows.insert(4,dict(event='deployment_unregistered_event'))
    with pytest.raises(ValueError):c.verify_runtime_events(rows,value,expected_asset_identities=trusted)



@pytest.mark.parametrize('mutation',['missing_expected','wrong_metadata_source','wrong_goal_mapping','self_consistent_forgery'])
def test_asset_enter_identity_requires_prevalidated_expectation(mutation):
    rows,value=synthetic_runtime_journal('libero_goal','full');trusted=synthetic_expected_assets(rows)
    meta=next(r for r in rows if r['event']=='asset_metadata_compat_enter')
    goal=next(r for r in rows if r['event']=='goal_component_compat_enter')
    if mutation=='missing_expected':trusted=None
    if mutation=='wrong_metadata_source':meta['identity']['source_sha256']='0'*64
    if mutation=='wrong_goal_mapping':goal['identity']['mappings'][0]['target_path']='/bad'
    if mutation=='self_consistent_forgery':
        goal['identity']['mappings'][0]['target_path']='/self-consistent-bad'
        for r in rows:
            if r['event'] in ('goal_component_load_start','goal_component_load_complete') and r['call_id']==0:
                r['mapping']=goal['identity']['mappings'][0]
    with pytest.raises(ValueError):c.verify_runtime_events(rows,value,expected_asset_identities=trusted)

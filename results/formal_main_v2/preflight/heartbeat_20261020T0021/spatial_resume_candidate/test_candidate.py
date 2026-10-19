"""Focused exact-case tests; no scheduler, simulator, model, or state writes."""
import copy, importlib.util, json
from pathlib import Path
from unittest.mock import patch
import pytest
D=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('spatial_resume1621_candidate',D/'prepare.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
@pytest.fixture
def facts():
 return json.loads((D/'actual_facts.json').read_text())
def test_actual_evidence_and_plan_are_not_authority(facts):
 assert m.validate_facts(facts) is True
 result=json.loads((D/'actual_evidence_check.json').read_text())
 plan=json.loads((D/'attempt03_candidate.json').read_text())
 assert result['actual_wrapper_verify_P'] is True
 assert result['old_planner_rejection']['status']=='rejected_original_unchanged_planner'
 assert result['old_planner_rejection']['full_registry_supplied'] is True
 assert plan['status']=='prepared_only_not_executable'
 assert plan['kind']!='formal_downstream_plan'
 assert plan['prior_job_ids']==['3022743','3042529']
 assert plan['actual_ledger_contributors']==['3022743']
 assert plan['prior_allocation_GPU_seconds']==395
 assert plan['submission_authorized'] is False and plan['production_readiness'] is False
 assert plan['invocation_relative_proposed'].endswith('_attempt03.json')
 assert 'invocation' not in plan and 'prepared_invocation' not in plan
 assert len(plan['unresolved_integration'])==5
@pytest.mark.parametrize('field,value',[
 ('allocation_job_ids',['3022743']),('allocation_job_ids',['3022743','3042529','3042529']),
 ('ledger_contributors',['3022743','3042529']),('all_prior_GPU_seconds',393),
 ('prefix_bytes',592888),('prefix_sha256','0'*64),('terminal_trials',13),
 ('journal_rows',26),('unique_initial_states',3),('maximum_new_trial_ids',600),
 ('planned_trials',612),('resume',False),('mode','final'),('suite','libero_object'),
 ('child_started',True),('new_terminal_trials',1),('action_artifact_count',1),
 ('adapter_artifact_count',1),('actual_P_wrapper_verify_passed',False),
 ('dependency_present_R_P',False),('frozen173_unchanged',False),
 ('invocation03_absent_R_P',False),('authorization_reusable',True),('submission_enabled',True)
])
def test_reject_changed_fact(facts,field,value):
 facts[field]=value
 with pytest.raises(ValueError):m.validate_facts(facts)
@pytest.mark.parametrize('kind',['status','exit_code','elapsed_seconds','gpus'])
def test_failure_allocation_cannot_be_erased(facts,kind):
 facts['allocation_rows'][1][kind]={'status':'COMPLETED','exit_code':'0:0','elapsed_seconds':0,'gpus':0}[kind]
 with pytest.raises(ValueError):m.validate_facts(facts)
@pytest.mark.parametrize('path',[
 'configs/manifests/formal_main_v2/libero_spatial/initial_states/sealed_final.json',
 'results/x/test/data.json','results/x/initial_states/current.json',
 'results/formal_main_v2/libero_spatial/downstream/final/x/trials.jsonl',
 'models/a.pt','results/a.ckpt','../state.json','/tmp/a.json','results\\x.json'
])
def test_lexical_guard_precedes_io(path):
 with patch.object(m,'stable',side_effect=AssertionError('I/O should not occur')) as reader:
  with pytest.raises(ValueError):m.Evidence().read(path)
  reader.assert_not_called()
def test_canonical_development_metadata_allowed():
 assert str(m.relative('configs/manifests/formal_main_v2/libero_spatial/initial_states/development.json')).endswith('development.json')
def test_existing_publication_closure_includes_indirect_prior():
 c=json.loads((D/'publication_closure.json').read_text())
 assert c['includes_prior_review_indirect_read'] is True
 assert c['files'][m.PRIOR]['sha256']==m.PINS[m.PRIOR]
 assert all(v['present_P'] for v in c['files'].values())
 assert c['future_publication_status']=='pending_exact_root_source_and_SHA_registration'
def test_no_fresh_invocation_or_consumed_authorization_reuse():
 p=json.loads((D/'attempt03_candidate.json').read_text())
 assert p['resume'] is True and p['output_relative']==m.RUN
 assert p['consumed_authorization']['reusable'] is False
 assert p['required_new_authorization']['not_created'] is True
 assert p['required_new_authorization']['maximum_attempts']==1
 assert p['required_new_authorization']['automatic_retry'] is False

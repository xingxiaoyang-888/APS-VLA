"""Independent consumer boundaries; synthetic data never establish GPU admission."""
from pathlib import Path
from types import SimpleNamespace
import copy, hashlib, importlib.util, json, sys
import pytest
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
H=R/'.local/action_downstream_consumers_0809'
FIXED={'reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034','test_consumers.py':'7b2b04f83f72cb3431112d1a77e5a3c4ba8c87c74a9f9225244c2b5c4dcaadea'}
for n,h in FIXED.items():assert hashlib.sha256((H/n).read_bytes()).hexdigest()==h
spec=importlib.util.spec_from_file_location('ind_consumer_fixture_0809',H/'test_consumers.py')
f=importlib.util.module_from_spec(spec);sys.modules[spec.name]=f;spec.loader.exec_module(f)
g,c=f.g,f.c

def test_real_helper_missing_Evidence_APIs_closed_with_original_code(monkeypatch):
 # Read only the original Long acceptance root and verify its required filenames.
 # Stop before parsing acceptance/data; this is API compatibility, not a GPU gate.
 e=g.Evidence(R);helper=g.load(e,g.OLD_HELPER,g.PINNED[g.OLD_HELPER])
 registration=e.read('configs/experiments/formal_main_v2.json')
 original=e.require;calls=[]
 class BoundaryReached(Exception):pass
 def stop_after_require(paths):
  original(paths);calls.extend(e.relative(x) for x in paths);raise BoundaryReached()
 monkeypatch.setattr(e,'require',stop_after_require)
 with pytest.raises(BoundaryReached):helper.load_suite_acceptance(e,registration,'libero_10',{})
 assert len(calls)==9 and any(x.endswith('/f03_calls.jsonl') for x in calls)
 # Invoke the original store operation with an explicitly synthetic upstream auditor.
 proof={'synthetic_upstream_proof_for_API_only':True}
 adapter=SimpleNamespace(review_source_provenance=lambda *args,**kwargs:proof)
 original_function=g.clone(helper.source_provenance_for_rows,source_review_module=lambda ev:adapter)
 assert original_function(e,registration,'libero_10',[],inventory={},jobs=[]) is proof
 assert e.source_provenance['libero_10'] is proof
 e.unchanged()

@pytest.mark.parametrize('suffix',['final_registry.json.bak','Final_registry.json','development.json/x','sealed_final.json','../../initial_state/value.json'])
def test_metadata_exception_does_not_expand_paths(suffix,monkeypatch):
 monkeypatch.setattr(Path,'open',lambda *args,**kwargs:pytest.fail('forbidden path attempted read'))
 with pytest.raises(ValueError):g.relative('configs/manifests/formal_main_v2/libero_10/initial_states/'+suffix)

def test_Evidence_require_symlink_cannot_read_target(tmp_path):
 target=tmp_path/'target.json';target.write_text('{}');link=tmp_path/'metadata.json';link.symlink_to(target)
 e=g.Evidence(tmp_path)
 with pytest.raises(ValueError,match='Symlink'):e.require(['metadata.json'])

def test_partial_engineering_success_flag_cannot_be_promoted(tmp_path,monkeypatch):
 ng,nc,p,a,invref,contract_ref,_,writer=f.layered_writer_fixture(tmp_path,monkeypatch)
 pullref={'path':a.pull_relative,'sha256':g.digest(tmp_path/a.pull_relative)}
 out=ng.review(tmp_path,job=a.job,invocation_ref=invref,pull_ref=pullref,registered_jobs=p.state['registered_jobs'],expected_contract_ref=contract_ref)
 assert out['scientific_complete'] is False
 altered=copy.deepcopy(out);altered['scientific_complete']=True
 ref=f.save(tmp_path,a.review_relative,altered)
 with pytest.raises(ValueError,match='does not exactly rebuild'):nc.review_downstream_output(ng.Evidence(tmp_path),ref,expected_stage='development',suite='libero_10')

@pytest.mark.parametrize('terminal',['completed','policy_error'])
def test_repeating_prior_terminal_trial_never_replaces_old_outcome(tmp_path,monkeypatch,terminal):
 ng,nc,p,a,invref,contract_ref,_,writer=f.layered_writer_fixture(tmp_path,monkeypatch)
 path=tmp_path/a.output/'trials.jsonl';rows=[json.loads(x) for x in path.read_bytes().splitlines()]
 result=next(x for x in rows if x.get('event')=='result');start=next(x for x in rows if x.get('event')=='start')
 if terminal=='policy_error':
  result.update(status='policy_error',success=False,control_steps=0,chunks=[],executed_actions=[],policy_calls=1,termination='policy_error')
 rows.append(copy.deepcopy(start));path.write_bytes(b''.join(json.dumps(x,sort_keys=True).encode()+b'\n' for x in rows))
 writer.pull(p,a)
 with pytest.raises(ValueError,match='Terminal trial was repeated'):
  ng.review(tmp_path,job=a.job,invocation_ref=invref,pull_ref={'path':a.pull_relative,'sha256':g.digest(tmp_path/a.pull_relative)},registered_jobs=p.state['registered_jobs'],expected_contract_ref=contract_ref)

@pytest.mark.parametrize('fault',['synthetic','not_restored','two_bases','raises'])
def test_failed_runtime_proof_never_becomes_scientific_pass(tmp_path,monkeypatch,fault):
 ng,nc,p,a,invref,contract_ref,parentpath,writer=f.layered_writer_fixture(tmp_path,monkeypatch)
 contract=json.loads((tmp_path/contract_ref['path']).read_bytes());folder=a.output+'/action_execution/'+a.job['job_id']+'/'
 files={folder+n:g.digest(tmp_path/(folder+n)) for n in ('identity.json','events.jsonl','completion.json')}
 answer=dict(all_source_and_binding_contexts_restored=True,original_base_loads=1,synthetic_input=False)
 if fault=='synthetic':answer['synthetic_input']=True
 elif fault=='not_restored':answer['all_source_and_binding_contexts_restored']=False
 elif fault=='two_bases':answer['original_base_loads']=2
 def verify(*args,**kwargs):
  if fault=='raises':raise ValueError('independent structural verifier failure')
  return answer
 with pytest.raises(ValueError):ng.actual_runtime(ng.Evidence(tmp_path),a.job,a.inv,files,contract,SimpleNamespace(verify_runtime_events=verify),a.adapter)

@pytest.mark.parametrize('field',['root_review','runtime_sources','final_evaluation_enabled'])
def test_rehashed_readiness_cannot_weaken_exact_envelope(tmp_path,field):
 ng,job,inv,contractref,ready=f.envelope_fixture(tmp_path)
 if field=='root_review':ready['independent_review']=ready['root_review']
 elif field=='runtime_sources':ready['runtime_sources']=dict(ready['runtime_sources'],**{g.CONSUMER:'e'*64})
 else:ready[field]=True
 ref=f.save(tmp_path,inv['runtime_readiness']['path'],ready);inv['runtime_readiness']=ref;job['runtime_readiness']=ref
 with pytest.raises(ValueError):ng.validate_envelope(ng.Evidence(tmp_path),job,inv,contractref)

def test_consumer_cycle_rejected_without_recursive_proof(tmp_path,monkeypatch):
 ng,nc,p,a,invref,contract_ref,_,writer=f.layered_writer_fixture(tmp_path,monkeypatch)
 out=ng.review(tmp_path,job=a.job,invocation_ref=invref,pull_ref={'path':a.pull_relative,'sha256':g.digest(tmp_path/a.pull_relative)},registered_jobs=p.state['registered_jobs'],expected_contract_ref=contract_ref)
 ref=f.save(tmp_path,a.review_relative,out)
 def recurse(*args,**kwargs):return nc.review_downstream_output(ng.Evidence(tmp_path),ref,expected_stage='development',suite='libero_10',require_complete=False)
 monkeypatch.setattr(ng,'review',recurse)
 with pytest.raises(ValueError,match='Cyclic'):nc.review_downstream_output(ng.Evidence(tmp_path),ref,expected_stage='development',suite='libero_10',require_complete=False)

from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest

Q=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('candidate_contract',Q/'contract.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


def base():
 inv=dict(schema=c.SCHEMA,kind='formal_downstream_invocation',version='formal-downstream-root-v1',stage='development',
  stage_key='libero_10_development_abcdef',suite='libero_10',method_ids=['A128_seed17','B128_seed17'],source_root=str(c.SOURCE),source_sha256=c.SOURCE_SHA,
  source_inventory=str(c.P/c.INVENTORY),source_inventory_sha256=c.INVENTORY_SHA,entrypoint='scripts/ops/formal_evaluation_adapter.py',adapter_sha256='b'*64,
  wrapper='scripts/server/run_formal_downstream.py',wrapper_sha256='c'*64,support_files={'scripts/server/run_formal_downstream.py':'c'*64},
  argv=['evaluate','--source-root',str(c.SOURCE),'--output',str(c.P/'results/formal_main_v2/libero_10/downstream/development/abcdef/attempt01')],
  run_root=str(c.P/'results/formal_main_v2/libero_10/downstream/development/abcdef/attempt01'),resume=False,
  execution_manifest=str(c.P/'results/formal_main_v2/manifests/development/libero_10.json'),execution_manifest_sha256='d'*64,
  registration_sha256='e'*64,watched_files={str(c.P/'configs/experiments/formal_main_v2.json'):'e'*64},root_evidence_sha256={'configs/experiments/formal_main_v2.json':'e'*64},
  prior_job_ids=[],prior_review=None,prior_allocation_cost=[],repair_record=None,stop_after=None,source_provenance={'suite':'libero_10','proof':'original'},scientific_settings_changed=False,final_values_read_locally=False)
 plan=dict(schema=c.SCHEMA,kind='formal_downstream_plan',invocation_relative='results/formal_main_v2/invocations/libero_10_development_abcdef_attempt01.json',invocation=inv,
  publish_files={'scripts/server/run_formal_downstream.py':'c'*64},output_relative=str(Path(inv['run_root']).relative_to(c.P)),output_must_exist=False,
  resources=dict(gres='gpu:l40:1',cpus_per_task=7,time='04:00:00'))
 plan['plan_sha256']=c.signature(plan)
 contract=dict(schema=c.SCHEMA,kind='formal_action_execution_contract',version=c.VERSION,status='candidate_pending_root_readiness',scientific_settings_changed=False,
  final_evaluation_enabled=False,files={**{name:hashlib.sha256(name.encode()).hexdigest() for name in c.EXPECTED_NEW_FILES},c.ACTION_ADAPTER:c.ACTION_SHA},
  runtime_contract={'version':'unittest-fixture-not-production',**{k:inv[k] for k in ('suite','stage','source_root','source_sha256')}},GPU_acceptance=copy.deepcopy(c.GPU_REFS),source_inventory={'path':c.INVENTORY,'sha256':c.INVENTORY_SHA},transition=None)
 refs={'scientific_plan_ref':{'path':'results/formal_main_v2/plans/old.json','sha256':'f'*64},'execution_contract_ref':{'path':'configs/experiments/candidate.json','sha256':'1'*64},'execution_contract':contract}
 return plan,refs


class ContractTests(unittest.TestCase):
 def test_explicit_identity_preserves_original(self):
  old,refs=base();untouched=copy.deepcopy(old);new=c.effective_plan(old,**refs)
  self.assertEqual(old,untouched);self.assertNotEqual(new['invocation']['version'],old['invocation']['version'])
  self.assertEqual(new['invocation']['argv'],old['invocation']['argv'])
  self.assertEqual(new['invocation']['source_provenance'],old['invocation']['source_provenance'])
  self.assertEqual(new['invocation']['scientific_plan'],refs['scientific_plan_ref'])
  self.assertTrue(c.validate_effective(old,new,**refs))
 def test_scientific_mutations_fail_even_resigned(self):
  changes={'argv':['evaluate','--loss-weight','0.2'],'method_ids':['B64_seed17'],'suite':'libero_goal','resume':True,'run_root':str(c.P/'results/other'),
   'source_root':str(c.P/'snapshot2'),'source_sha256':'2'*64,'execution_manifest_sha256':'2'*64,'registration_sha256':'2'*64,'stop_after':1,
   'source_provenance':{},'prior_review':'results/different.json','prior_job_ids':['99'],'prior_allocation_cost':[], 'adapter_sha256':'3'*64}
  for key,value in changes.items():
   with self.subTest(key=key):
    old,refs=base()
    if key=='prior_allocation_cost':old['invocation'][key]=[{'job_id':'1','elapsed_seconds':100}];old['plan_sha256']=c.signature({k:v for k,v in old.items() if k!='plan_sha256'})
    new=c.effective_plan(old,**refs);new['invocation'][key]=value;new['plan_sha256']=c.signature({k:v for k,v in new.items() if k!='plan_sha256'})
    with self.assertRaises(ValueError):c.validate_effective(old,new,**refs)
 def test_resources_and_output_cannot_change(self):
  for key,val in [('resources',{'gres':'gpu:l40:8'}),('output_relative','results/other'),('output_must_exist',True),('invocation_relative','results/other.json')]:
   with self.subTest(key=key):
    old,refs=base();new=c.effective_plan(old,**refs);new[key]=val;new['plan_sha256']=c.signature({k:v for k,v in new.items() if k!='plan_sha256'})
    with self.assertRaises(ValueError):c.validate_effective(old,new,**refs)
 def test_extra_scientific_hidden_field_fails(self):
  old,refs=base();new=c.effective_plan(old,**refs);new['invocation']['future_observation_path']='secret'
  with self.assertRaises(ValueError):c.validate_effective(old,new,**refs)
 def test_proof_and_support_mutations_fail(self):
  for key in ['support_files','watched_files','root_evidence_sha256']:
   old,refs=base();new=c.effective_plan(old,**refs);new['invocation'][key].pop(next(iter(new['invocation'][key])))
   with self.assertRaises(ValueError):c.validate_effective(old,new,**refs)
 def test_no_final_or_sealed_flags(self):
  for kind in ('stage','flag'):
   old,refs=base()
   if kind=='stage':old['invocation']['stage']='final'
   else:old['invocation']['argv']+=['--sealed-final',str(c.P/'sealed.json')]
   old['plan_sha256']=c.signature({k:v for k,v in old.items() if k!='plan_sha256'})
   with self.assertRaises(ValueError):c.effective_plan(old,**refs)
 def test_candidate_cannot_self_authorize(self):
  for key,val in [('status','passed'),('final_evaluation_enabled',True),('scientific_settings_changed',True)]:
   old,refs=base();refs['execution_contract'][key]=val
   with self.assertRaises(ValueError):c.effective_plan(old,**refs)
 def test_consumer_and_wrapper_exact_set_mandatory(self):
  for name in c.EXPECTED_NEW_FILES:
   old,refs=base();refs['execution_contract']['files'].pop(name)
   with self.assertRaises(ValueError):c.effective_plan(old,**refs)
 def test_action_original_bytes_and_gpu_receipts_pinned(self):
  for key in ('action','gpu','inventory'):
   old,refs=base();x=refs['execution_contract']
   if key=='action':x['files'][c.ACTION_ADAPTER]='0'*64
   elif key=='gpu':x['GPU_acceptance'][next(iter(c.GPU_REFS))]='0'*64
   else:x['source_inventory']['sha256']='0'*64
   with self.assertRaises(ValueError):c.effective_plan(old,**refs)
 def test_resume_needs_explicit_transition(self):
  old,refs=base();old['invocation']['resume']=True;old['plan_sha256']=c.signature({k:v for k,v in old.items() if k!='plan_sha256'})
  with self.assertRaises(ValueError):c.effective_plan(old,**refs)
  refs['execution_contract']['transition']={'path':'results/formal_main_v2/transitions/foo.json','sha256':'9'*64}
  inv=old['invocation'];inv.update(prior_job_ids=['123'],prior_review='results/formal_main_v2/prior.json')
  output=old['output_relative']
  for name in ('trials.jsonl','closed_loop_report.json'):inv['root_evidence_sha256'][output+'/'+name]='8'*64
  old['plan_sha256']=c.signature({k:v for k,v in old.items() if k!='plan_sha256'})
  new=c.effective_plan(old,**refs);self.assertIn('results/formal_main_v2/transitions/foo.json',new['publish_files'])
 def test_all_suites_partition_only_exact_resume_ledgers(self):
  for suite in ('libero_10','libero_spatial','libero_object','libero_goal'):
   with self.subTest(suite=suite):
    old,refs=base();inv=old['invocation'];inv.update(suite=suite,resume=True,prior_job_ids=['123'],prior_review='results/formal_main_v2/prior.json')
    inv['argv']+=['--resume'];old['output_must_exist']=True
    refs['execution_contract']['runtime_contract']['suite']=suite
    refs['execution_contract']['transition']={'path':'results/formal_main_v2/transitions/foo.json','sha256':'9'*64}
    prefix={str(c.P/old['output_relative']/name):'8'*64 for name in ('trials.jsonl','closed_loop_report.json')}
    for remote,checksum in prefix.items():
     inv['root_evidence_sha256'][str(Path(remote).relative_to(c.P))]=checksum
     if suite in ('libero_10','libero_spatial'):inv['watched_files'][remote]=checksum
    inv['watched_files'][inv['run_root']+'/config.json']='7'*64
    old['plan_sha256']=c.signature({k:v for k,v in old.items() if k!='plan_sha256'});prior=copy.deepcopy(old)
    new=c.effective_plan(old,**refs)
    self.assertEqual(old,prior);self.assertEqual(c.resume_prefix_inputs(inv),prefix)
    for name in prefix:self.assertNotIn(name,new['invocation']['watched_files'])
    self.assertIn(inv['run_root']+'/config.json',new['invocation']['watched_files'])
    self.assertTrue(all(new['invocation']['root_evidence_sha256'][str(Path(name).relative_to(c.P))]==value for name,value in prefix.items()))
    bad=copy.deepcopy(new);bad['invocation']['watched_files'].pop(inv['run_root']+'/config.json')
    with self.assertRaises(ValueError):c.validate_effective(old,bad,**refs)
    bad=copy.deepcopy(new);bad['invocation']['watched_files'].update(prefix)
    with self.assertRaises(ValueError):c.validate_effective(old,bad,**refs)
 def test_resume_prefix_missing_foreign_or_conflicting_proof_rejected(self):
  old,_=base();inv=old['invocation'];inv.update(resume=True,prior_job_ids=['123'],prior_review='results/formal_main_v2/prior.json')
  output=old['output_relative']
  with self.assertRaises(ValueError):c.resume_prefix_inputs(inv)
  for name in ('trials.jsonl','closed_loop_report.json'):inv['root_evidence_sha256'][output+'/'+name]='8'*64
  inv['root_evidence_sha256'][output+'/other.json']='9'*64
  self.assertEqual(len(c.resume_prefix_inputs(inv)),2)
  inv['watched_files'][inv['run_root']+'/trials.jsonl']='7'*64
  with self.assertRaises(ValueError):c.resume_prefix_inputs(inv)
  inv['watched_files'].pop(inv['run_root']+'/trials.jsonl');inv['stage']='final'
  with self.assertRaises(ValueError):c.resume_prefix_inputs(inv)
  inv['stage']='development';inv['prior_job_ids']=[]
  with self.assertRaises(ValueError):c.resume_prefix_inputs(inv)
 def test_fresh_execution_has_no_mutable_prefix(self):
  old,_=base();self.assertEqual(c.resume_prefix_inputs(old['invocation']),{})
  self.assertEqual(c.immutable_watches(old['invocation']),old['invocation']['watched_files'])
 def test_runtime_scope_cannot_swap_suite_or_stage(self):
  for key,value in [('suite','libero_goal'),('stage','components'),('source_root','/other'),('source_sha256','0'*64)]:
   old,refs=base();refs['execution_contract']['runtime_contract'][key]=value
   with self.assertRaises(ValueError):c.effective_plan(old,**refs)
 def test_transition_binds_prior_version_and_raw_prefix(self):
  with tempfile.TemporaryDirectory(dir=Q) as temporary:
   root=Path(temporary);old,refs=base();inv=old['invocation'];inv.update(resume=True,prior_job_ids=['123'],prior_review='results/formal_main_v2/downstream_reviews/old.json')
   output=str(Path(inv['run_root']).relative_to(c.P));files={}
   for name in ('trials.jsonl','closed_loop_report.json','config.json','panel.json'):
    path=root/output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('{}\n');files[output+'/'+name]=c.digest(path)
   def put(rel,obj):
    p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj));return {'path':rel,'sha256':c.digest(p)}
   prior={'files':files,'execution_version':c.VERSION}
   old_contract=refs['execution_contract'];prior['action_execution_contract']=put('results/formal_main_v2/contracts/previous.json',old_contract)
   pref=put(inv['prior_review'],prior);inv['root_evidence_sha256'][pref['path']]=pref['sha256']
   old['plan_sha256']=c.signature({k:v for k,v in old.items() if k!='plan_sha256'})
   ind=dict(kind='formal_action_runtime_transition_review',status='passed',review_role='independent',stage_key=inv['stage_key'],files=files,prior_review=inv['prior_review'],from_version=c.VERSION,to_version=c.VERSION)
   tr=dict(schema=c.SCHEMA,kind='formal_action_runtime_transition',status='root_reviewed',from_version=c.VERSION,to_version=c.VERSION,
    stage_key=inv['stage_key'],run_root=inv['run_root'],execution_manifest_sha256=inv['execution_manifest_sha256'],prior_job_ids=inv['prior_job_ids'],prior_review=inv['prior_review'],
    terminal_trials_repeated=False,prior_outcomes_replaced=False,new_trial_ids_only=True,files=files,independent_review=put('results/formal_main_v2/transitions/independent.json',ind))
   self.assertTrue(c.validate_transition(tr,old,root=root,execution_contract=old_contract))
   bad=copy.deepcopy(tr);bad['from_version']='formal-downstream-root-v1'
   with self.assertRaises(ValueError):c.validate_transition(bad,old,root=root,execution_contract=old_contract)
   changed=copy.deepcopy(old_contract);changed['runtime_contract']['checkpoint']='another'
   with self.assertRaises(ValueError):c.validate_transition(tr,old,root=root,execution_contract=changed)
   with self.assertRaises(ValueError):c.validate_transition(tr,old,root=root)
   bad=copy.deepcopy(tr);bad['prior_outcomes_replaced']=True
   with self.assertRaises(ValueError):c.validate_transition(bad,old,root=root,execution_contract=old_contract)
   (root/output/'trials.jsonl').write_text('changed\n')
   with self.assertRaises(ValueError):c.validate_transition(tr,old,root=root,execution_contract=old_contract)
 def test_exact_reference_and_nonpayload(self):
  for path in ('../outside.json','/absolute.json','C:/local.json','x\\y.json','results/sealed_final.json','checkpoints/best.pt','foo.pkl','initial_states/final_registry.json'):
   with self.subTest(path=path),self.assertRaises(ValueError):c.ref({'path':path,'sha256':'0'*64})
  with self.assertRaises(ValueError):c.ref({'path':'foo.json','sha256':'0'*64,'optional':True})
 def test_read_hash_and_symlink_guard(self):
  with tempfile.TemporaryDirectory(dir=Q) as temporary:
   root=Path(temporary);p=root/'proof.json';p.write_text('{}');r={'path':'proof.json','sha256':c.digest(p)}
   self.assertEqual(c.read_ref(root,r),{})
   p.write_text('{"tampered": true}')
   with self.assertRaises(ValueError):c.read_ref(root,r)
   link=root/'alias.json';link.symlink_to(p)
   with self.assertRaises(ValueError):c.read_ref(root,{'path':'alias.json','sha256':c.digest(p)})
 def test_nan_signature_fails(self):
  with self.assertRaises(ValueError):c.signature({'x':float('nan')})
 def test_plan_forgery_without_signature_fails(self):
  old,refs=base();old['invocation']['argv']+=['--changed']
  with self.assertRaises(ValueError):c.effective_plan(old,**refs)


if __name__=='__main__':unittest.main(verbosity=2)

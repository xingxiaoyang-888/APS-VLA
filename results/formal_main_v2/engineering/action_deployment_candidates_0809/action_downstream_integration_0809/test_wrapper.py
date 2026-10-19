from pathlib import Path
import copy,hashlib,importlib.util,json,tempfile,unittest
from unittest.mock import patch
from types import SimpleNamespace
Q=Path(__file__).resolve().parent

def module(name,file):
 spec=importlib.util.spec_from_file_location(name,Q/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=module('test_parent_contract','contract.py');w=module('test_candidate_wrapper','wrapper.py');fixtures=module('test_parent_fixture','test_contract.py')

def write(root,path,value):
 p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');return {'path':path,'sha256':c.digest(p)}

class ParentBoundary(unittest.TestCase):
 def setUp(self):
  self.temporary=tempfile.TemporaryDirectory(dir=Q);self.root=Path(self.temporary.name)
  old,refs=fixtures.base();self.old=old;self.refs=refs
  for n in c.EXPECTED_NEW_FILES:
   p=self.root/n;p.parent.mkdir(parents=True,exist_ok=True)
   p.write_bytes((Q/Path(n).name).read_bytes() if Path(n).name in ('contract.py','wrapper.py','entry.py') else b'# CPU boundary fixture only\n')
  action=self.root/c.ACTION_ADAPTER;action.parent.mkdir(parents=True,exist_ok=True);action.write_bytes((Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')/c.ACTION_ADAPTER).read_bytes())
  self.refs['execution_contract']['files']={n:c.digest(self.root/n) for n in {*c.EXPECTED_NEW_FILES,c.ACTION_ADAPTER}}
  original=self.root/w.OLD;original.parent.mkdir(parents=True,exist_ok=True);original.write_bytes((Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')/w.OLD).read_bytes())
  self.old['invocation']['support_files']={w.OLD:w.OLD_SHA};self.old['invocation']['wrapper_sha256']=w.OLD_SHA
  # Watches are empty only at this scientific-validator boundary fixture.
  self.old['invocation']['watched_files']={};self.old['invocation']['root_evidence_sha256']={};self.old['publish_files']={w.OLD:w.OLD_SHA}
  self.old['plan_sha256']=c.signature({k:v for k,v in self.old.items() if k!='plan_sha256'})
  self.refs['scientific_plan_ref']=write(self.root,self.refs['scientific_plan_ref']['path'],self.old)
  self.refs['execution_contract_ref']=write(self.root,self.refs['execution_contract_ref']['path'],self.refs['execution_contract'])
  self.effective=c.effective_plan(self.old,**self.refs)
  effective_ref=write(self.root,'results/formal_main_v2/plans/effective.json',self.effective)
  self.ready=dict(schema=c.SCHEMA,kind='formal_action_runtime_readiness',status='passed',reviewed_by='root',execution_version=c.VERSION,
   scientific_settings_changed=False,final_evaluation_enabled=False,raw_consumer_ready=True,effective_plan=effective_ref,
   plan_sha256=self.effective['plan_sha256'],runtime_sources=self.refs['execution_contract']['files'])
  for role in ('root_review','independent_review'):
   self.ready[role]=write(self.root,'results/formal_main_v2/preflight/'+role+'.json',dict(status='passed',execution_version=c.VERSION,
    runtime_sources=self.refs['execution_contract']['files'],production_chain_complete=True,fixture_role=role))
  self.inv={**copy.deepcopy(self.effective['invocation']),'registered_utc':'2026-10-19T00:00:00Z','plan_sha256':self.effective['plan_sha256'],
   'runtime_readiness':write(self.root,'results/formal_main_v2/preflight/readiness.json',self.ready)}
  self.loads=[]
 def tearDown(self):self.temporary.cleanup()
 def run_verify(self):
  actual_load=w.load
  def load(path,name):
   self.loads.append(name)
   if name=='original_plan_validator_not_execution':return SimpleNamespace(verify=lambda inv: SimpleNamespace(original_plan_validator_received=copy.deepcopy(inv)))
   if name=='action_deployment_runtime':return SimpleNamespace(validate_contract=lambda **kw: None)
   return actual_load(path,name)
  # P path checks and runtime watches are evaluated separately by actual frozen
  # scientific validator/GPU entry. This fixture never models a complete plan.
  with patch.object(w,'load',load), patch.object(c,'P',self.root):
   with patch.object(w,'sha',side_effect=self.sha_boundary):return w.verify(self.inv,project=self.root)
 def sha_boundary(self,path):
  path=Path(path)
  if str(path) in self.inv['watched_files']:return self.inv['watched_files'][str(path)]
  return c.digest(path)
 def test_changed_parent_rejected_before_contract_import(self):
  (self.root/w.WRAPPER_REL).write_text('# tamper\n')
  with self.assertRaisesRegex(ValueError,'parent source'):self.run_verify()
  self.assertEqual(self.loads,[])
 def test_changed_contract_rejected_before_import(self):
  (self.root/w.CONTRACT_REL).write_text('# tamper\n')
  with self.assertRaisesRegex(ValueError,'Contract source'):self.run_verify()
  self.assertEqual(self.loads,[])
 def test_missing_readiness_blocks_original_science(self):
  self.inv.pop('runtime_readiness')
  with self.assertRaises(ValueError):self.run_verify()
  self.assertNotIn('original_plan_validator_not_execution',self.loads)
 def test_incomplete_chain_not_authorized(self):
  self.ready['raw_consumer_ready']=False;self.inv['runtime_readiness']=write(self.root,self.inv['runtime_readiness']['path'],self.ready)
  with self.assertRaisesRegex(ValueError,'readiness'):self.run_verify()
  self.assertNotIn('original_plan_validator_not_execution',self.loads)
 def test_candidate_production_flag_cannot_be_forged(self):
  ref=self.ready['independent_review'];v=json.loads((self.root/ref['path']).read_text());v['production_chain_complete']=False
  self.ready['independent_review']=write(self.root,ref['path'],v);self.inv['runtime_readiness']=write(self.root,self.inv['runtime_readiness']['path'],self.ready)
  with self.assertRaisesRegex(ValueError,'Partial candidate'):self.run_verify()
  self.assertNotIn('original_plan_validator_not_execution',self.loads)
 def test_original_review_cannot_serve_as_independent(self):
  self.ready['independent_review']=self.ready['root_review'];self.inv['runtime_readiness']=write(self.root,self.inv['runtime_readiness']['path'],self.ready)
  with self.assertRaisesRegex(ValueError,'not independent'):self.run_verify()
 def test_prepared_extra_field_fails(self):
  self.inv['unreviewed_extra']='silent behavior'
  with self.assertRaisesRegex(ValueError,'extra/missing'):self.run_verify()
 def test_prepared_science_changed_fails(self):
  self.inv['argv']+=['--future-loss','0.5']
  with self.assertRaisesRegex(ValueError,'changed effective'):self.run_verify()
 def test_ready_source_list_omission_fails(self):
  self.ready['runtime_sources']=dict(self.ready['runtime_sources']);self.ready['runtime_sources'].pop(c.CONSUMER)
  self.inv['runtime_readiness']=write(self.root,self.inv['runtime_readiness']['path'],self.ready)
  with self.assertRaisesRegex(ValueError,'Ready sources'):self.run_verify()

if __name__=='__main__':unittest.main(verbosity=2)

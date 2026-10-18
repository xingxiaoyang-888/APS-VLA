"""Independent corrected guard tests with actual canonical S runtime; no model load."""
from pathlib import Path
import hashlib,importlib.util,json,sys,unittest
import torch
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');S=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_run_564be0995e')
C=R/'.local/action_runtime_lifecycle_v4_1940'
assert hashlib.sha256((C/'probe.py').read_bytes()).hexdigest()=='91e12f29ad39591c29cfd63912394949d1cad932bb80c8a871ed852cea32cadc'
spec=importlib.util.spec_from_file_location('_independent_v4_corrected',C/'probe.py');candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
sys.path.insert(0,str(S/'src'))
from cti_vla.models import openvla_oft_runtime_compat as compat
SOURCE=S/'src/cti_vla/models/openvla_oft_runtime_compat.py'
EXPECTED=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_bytes())['files']['src/cti_vla/models/openvla_oft_runtime_compat.py']
assert Path(compat.__file__).resolve()==SOURCE and hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
class IndependentTests(unittest.TestCase):
 def setUp(self):
  self.assertFalse(candidate.PrismaticProcessLifecycle.current())
  self.paths=[str(p) for p in (Path('/registered')/x for x in ['long','spatial','object','goal'])]
  self.codes=[compat.get_current_action_mask.__code__,compat.get_next_actions_mask.__code__]
  self.ignore=compat.IGNORE_INDEX;self.guard=candidate.PrismaticProcessLifecycle(self.paths,compat,runtime_path=SOURCE,runtime_sha256=EXPECTED);self.calls=[]
 def tearDown(self):
  # This cleanup is test-process-only; production guard never deletes modules.
  for name in tuple(candidate.PrismaticProcessLifecycle.current()):sys.modules.pop(name)
  compat.get_current_action_mask.__code__,compat.get_next_actions_mask.__code__=self.codes
  compat.IGNORE_INDEX=self.ignore
 def loader(self,path,*,device,use_minimal_prismatic_compat):
  self.calls.append((path,device,use_minimal_prismatic_compat))
  compat.install_prismatic_runtime_compat(use_minimal_compat=use_minimal_prismatic_compat);return object()
 def assert_poisoned(self):
  before=len(self.calls)
  with self.assertRaises(ValueError):self.guard.load(self.loader,self.paths[self.guard.completed],device='CPU')
  self.assertEqual(len(self.calls),before);self.assertTrue(self.guard.failed)
 def test_first_constant_drift_rejected(self):
  def bad(*a,**kw):
   x=self.loader(*a,**kw);sys.modules['prismatic.vla.constants'].ACTION_DIM=8;return x
  with self.assertRaises(ValueError):self.guard.load(bad,self.paths[0],device='CPU')
  self.assertEqual(self.guard.completed,0);self.assert_poisoned()
 def test_first_helper_replacement_rejected(self):
  def bad(*a,**kw):
   x=self.loader(*a,**kw);sys.modules['prismatic.training.train_utils'].get_current_action_mask=lambda x:x;return x
  with self.assertRaises(ValueError):self.guard.load(bad,self.paths[0],device='CPU')
  self.assertEqual(self.guard.completed,0);self.assert_poisoned()
 def test_first_helper_code_drift_rejected(self):
  def bad(*a,**kw):
   x=self.loader(*a,**kw);compat.get_current_action_mask.__code__=(lambda x:x).__code__;return x
  with self.assertRaises(ValueError):self.guard.load(bad,self.paths[0],device='CPU')
  self.assertEqual(self.guard.completed,0);self.assert_poisoned()
 def test_helper_global_drift_rejected(self):
  self.guard.load(self.loader,self.paths[0],device='CPU');compat.IGNORE_INDEX=9
  with self.assertRaises(ValueError):self.guard.load(self.loader,self.paths[1],device='CPU')
  self.assertEqual(len(self.calls),1);self.assert_poisoned()
 def test_actual_S_runtime_four_loads_keep_semantics_and_ownership(self):
  tokens=torch.tensor([[-100]*2+[32001]*56+[0]*3])
  reference=[compat.get_current_action_mask(tokens),compat.get_next_actions_mask(tokens)]
  objects=[]
  for p in self.paths:
   objects.append(self.guard.load(self.loader,p,device='CPU'))
   helpers=sys.modules['prismatic.training.train_utils']
   self.assertIs(helpers.get_current_action_mask,compat.get_current_action_mask)
   self.assertIs(helpers.get_next_actions_mask,compat.get_next_actions_mask)
   self.assertTrue(torch.equal(helpers.get_current_action_mask(tokens),reference[0]))
   self.assertTrue(torch.equal(helpers.get_next_actions_mask(tokens),reference[1]))
  self.guard.finish();self.assertEqual([x[2] for x in self.calls],[True,False,False,False]);self.assertEqual(self.guard.completed,4)
  self.assertEqual(len({id(x) for x in objects}),4)
 def test_runtime_R_alias_rejected_when_S_is_required(self):
  with self.assertRaises(ValueError):candidate.PrismaticProcessLifecycle(self.paths,compat,runtime_path=R/'src/cti_vla/models/openvla_oft_runtime_compat.py',runtime_sha256=EXPECTED)
 def test_wrong_registered_SHA_rejected(self):
  with self.assertRaises(ValueError):candidate.PrismaticProcessLifecycle(self.paths,compat,runtime_path=SOURCE,runtime_sha256='0'*64)
if __name__=='__main__':unittest.main()

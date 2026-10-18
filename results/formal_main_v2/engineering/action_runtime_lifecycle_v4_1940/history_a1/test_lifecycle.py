import importlib.util
from pathlib import Path
import sys
import types
import unittest
import ast
import hashlib
import torch

R = Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D = Path(__file__).parent

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

candidate = load(D / 'probe.py', 'runtime_lifecycle_candidate')
compat = load(R / 'src/cti_vla/models/openvla_oft_runtime_compat.py', 'frozen_real_runtime')

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.assertFalse(candidate.PrismaticProcessLifecycle.current())
        self.paths = tuple('/registered/checkpoint_' + str(i) for i in range(4))
        self.guard = candidate.PrismaticProcessLifecycle(self.paths)
        self.calls = []
        self.original_codes = [compat.get_current_action_mask.__code__, compat.get_next_actions_mask.__code__]

    def tearDown(self):
        # Test process only: production lifecycle never removes modules.
        for name in tuple(candidate.PrismaticProcessLifecycle.current()):
            sys.modules.pop(name)
        compat.get_current_action_mask.__code__, compat.get_next_actions_mask.__code__ = self.original_codes

    def loader(self, path, *, device, use_minimal_prismatic_compat):
        self.calls.append((path, device, use_minimal_prismatic_compat))
        compat.install_prismatic_runtime_compat(use_minimal_compat=use_minimal_prismatic_compat)
        return path

    def one(self):
        return self.guard.load(self.loader, self.paths[0], device='CPU-test-no-model')

    def second(self):
        return self.guard.load(self.loader, self.paths[1], device='CPU-test-no-model')

    def test_real_installer_true_then_three_false_preserves_mask_results(self):
        tokens = torch.tensor([[32001] * 56 + [-100] * 4])
        self.one()
        expected = (compat.get_current_action_mask(tokens), compat.get_next_actions_mask(tokens))
        for path in self.paths[1:]:
            self.guard.load(self.loader, path, device='CPU-test-no-model')
            helpers = sys.modules['prismatic.training.train_utils']
            self.assertTrue(torch.equal(helpers.get_current_action_mask(tokens), expected[0]))
            self.assertTrue(torch.equal(helpers.get_next_actions_mask(tokens), expected[1]))
        self.guard.finish()
        self.assertEqual([r[2] for r in self.calls], [True, False, False, False])

    def test_original_v3_reinstall_failure_reproduced(self):
        self.one()
        with self.assertRaisesRegex(RuntimeError, 'before any prismatic import'):
            compat.install_prismatic_runtime_compat(use_minimal_compat=True)

    def test_preexisting_runtime_rejected(self):
        compat.install_prismatic_runtime_compat(use_minimal_compat=True)
        with self.assertRaisesRegex(ValueError, 'fresh process'):
            self.one()
        self.assertEqual(self.calls, [])

    def test_unknown_module_added(self):
        self.one();sys.modules['prismatic.unknown'] = types.ModuleType('prismatic.unknown')
        with self.assertRaises(ValueError): self.second()

    def test_known_module_replaced(self):
        self.one();sys.modules['prismatic.vla.constants'] = types.ModuleType('prismatic.vla.constants')
        with self.assertRaises(ValueError): self.second()

    def test_module_removed(self):
        self.one();sys.modules.pop('prismatic.vla.constants')
        with self.assertRaises(ValueError): self.second()

    def test_constant_mutated(self):
        self.one();sys.modules['prismatic.vla.constants'].NUM_ACTIONS_CHUNK = 9
        with self.assertRaises(ValueError): self.second()

    def test_helper_replaced(self):
        self.one();sys.modules['prismatic.training.train_utils'].get_current_action_mask = lambda x: x
        with self.assertRaises(ValueError): self.second()

    def test_helper_code_mutated(self):
        self.one();compat.get_current_action_mask.__code__ = (lambda x:x).__code__
        with self.assertRaises(ValueError): self.second()

    def test_module_extra_attribute(self):
        self.one();sys.modules['prismatic'].extra = True
        with self.assertRaises(ValueError): self.second()

    def test_package_path_mutated_in_place(self):
        self.one();sys.modules['prismatic'].__path__.append('/unknown')
        with self.assertRaises(ValueError): self.second()

    def test_spec_mutated_in_place(self):
        self.one();sys.modules['prismatic'].__spec__.loader = object()
        with self.assertRaises(ValueError): self.second()

    def test_wrong_checkpoint_order_before_loading(self):
        with self.assertRaises(ValueError): self.second()
        self.assertEqual(self.calls, [])

    def test_first_load_failure_is_terminal(self):
        def fail(*a, **kw):
            self.loader(*a, **kw)
            raise RuntimeError('registered simulated loader failure')
        with self.assertRaises(RuntimeError): self.guard.load(fail, self.paths[0], device='CPU')
        self.assertEqual(self.guard.completed, 0)
        with self.assertRaises(ValueError): self.one()

    def test_later_load_failure_is_terminal(self):
        self.one()
        def fail(*a, **kw):
            self.loader(*a, **kw)
            raise RuntimeError('registered simulated loader failure')
        with self.assertRaises(RuntimeError): self.guard.load(fail, self.paths[1], device='CPU')
        with self.assertRaises(ValueError): self.second()

    def test_load_time_drift_rejected(self):
        self.one()
        def mutate(*a, **kw):
            value = self.loader(*a, **kw)
            sys.modules['prismatic.vla.constants'].ACTION_DIM = 8
            return value
        with self.assertRaises(ValueError): self.guard.load(mutate, self.paths[1], device='CPU')
        self.assertEqual(self.guard.completed, 1)

    def test_missing_first_install_rejected(self):
        with self.assertRaises(ValueError): self.guard.load(lambda *a, **k: None, self.paths[0], device='CPU')
        self.assertEqual(self.guard.completed, 0)

    def test_fifth_load_rejected(self):
        for path in self.paths:self.guard.load(self.loader, path, device='CPU')
        with self.assertRaises(ValueError): self.guard.load(self.loader, self.paths[0], device='CPU')
        self.assertEqual(len(self.calls), 4)

    def test_finish_rejects_incomplete(self):
        self.one()
        with self.assertRaises(ValueError):self.guard.finish()
        with self.assertRaises(ValueError):self.second()

    def test_finish_rejects_late_mutation(self):
        for path in self.paths:self.guard.load(self.loader, path, device='CPU')
        sys.modules['prismatic.vla.constants'].PROPRIO_DIM = 9
        with self.assertRaises(ValueError): self.guard.finish()

    def test_four_distinct_checkpoints_required(self):
        with self.assertRaises(ValueError):candidate.PrismaticProcessLifecycle(self.paths[:3])
        with self.assertRaises(ValueError):candidate.PrismaticProcessLifecycle([self.paths[0]]*4)

    def test_only_lifecycle_and_version_changed(self):
        old = (R/'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/probe.py').read_text()
        new = (D/'probe.py').read_text()
        oldtree,newtree=ast.parse(old),ast.parse(new)
        oldnodes={n.name:ast.dump(n,include_attributes=False) for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        newnodes={n.name:ast.dump(n,include_attributes=False) for n in newtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        self.assertEqual(set(newnodes)-set(oldnodes), {'PrismaticProcessLifecycle'})
        self.assertEqual([k for k in oldnodes if oldnodes[k]!=newnodes[k]], ['gpu_body'])
        self.assertEqual(candidate.LIMITS['cells'],16)
        self.assertEqual(candidate.LIMITS['max_control_steps'],8)

if __name__ == '__main__':unittest.main()

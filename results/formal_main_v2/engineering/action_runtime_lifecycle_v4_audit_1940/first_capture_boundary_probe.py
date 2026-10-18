"""Independent first-capture drift probes: actual frozen CPU installer, no model."""
import importlib.util,json,sys
from pathlib import Path
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');S=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_run_564be0995e')
def load(p,name):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
candidate=load(R/'.local/action_runtime_lifecycle_v4_1940/probe.py','candidate_v4')
compat=load(S/'src/cti_vla/models/openvla_oft_runtime_compat.py','independent_actual_frozen_compat')
paths=['/registered/checkpoint_'+str(i) for i in range(4)]
results=[]
for case in ['first_constant_drift','first_helper_replacement','first_helper_code_drift','helper_global_drift_after_first']:
 assert not candidate.PrismaticProcessLifecycle.current()
 guard=candidate.PrismaticProcessLifecycle(paths);original_code=compat.get_current_action_mask.__code__;old_ignore=compat.IGNORE_INDEX
 def loader(path,*,device,use_minimal_prismatic_compat):
  compat.install_prismatic_runtime_compat(use_minimal_compat=use_minimal_prismatic_compat)
  if use_minimal_prismatic_compat:
   if case=='first_constant_drift':sys.modules['prismatic.vla.constants'].ACTION_DIM=8
   elif case=='first_helper_replacement':sys.modules['prismatic.training.train_utils'].get_current_action_mask=lambda x:x
   elif case=='first_helper_code_drift':compat.get_current_action_mask.__code__=(lambda x:x).__code__
  return path
 try:
  guard.load(loader,paths[0],device='CPU-no-model')
  if case=='helper_global_drift_after_first':
   compat.IGNORE_INDEX=9;guard.load(loader,paths[1],device='CPU-no-model')
  results.append(dict(case=case,rejected=False,completed=guard.completed,failed=guard.failed))
 except Exception as exc:results.append(dict(case=case,rejected=True,type=type(exc).__name__,message=str(exc),completed=guard.completed,failed=guard.failed))
 finally:
  # Isolated CPU test cleanup only. Production candidate must never remove modules.
  for name in tuple(candidate.PrismaticProcessLifecycle.current()):sys.modules.pop(name)
  compat.get_current_action_mask.__code__=original_code;compat.IGNORE_INDEX=old_ignore
print(json.dumps(results,indent=2))

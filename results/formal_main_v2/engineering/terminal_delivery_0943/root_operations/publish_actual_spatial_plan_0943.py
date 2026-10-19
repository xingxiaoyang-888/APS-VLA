from pathlib import Path
import json,hashlib,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('root_publish_c',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
pins={'scientific_plan.json':'43a521e2b1c5b7f8ceff442ce655dde5cae73dfde0f9f7598f65fa57446b4a94','execution_contract.json':'b63689d9f3fb3dece0c2fee8c219ad94cd8e1e694962afdb2cd66a40bf551bc0','effective_plan.json':'a56ff9e12b6ddad13e3e6ee4b78f5181ffa3ead3f8df8c620370e00c95d2eb3b'}
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 for name,pin in pins.items():
  src=R/'.local/action_actual_plan_0943'/name;assert h(src)==pin
  dst=R/'results/formal_main_v2/execution/action_spatial_resume_0943'/name
  if dst.exists():assert h(dst)==pin
  else:
   with dst.open('xb') as f:f.write(src.read_bytes())
 print(json.dumps({'published_exact_R':pins,'state_unchanged':True,'submitted':False}))

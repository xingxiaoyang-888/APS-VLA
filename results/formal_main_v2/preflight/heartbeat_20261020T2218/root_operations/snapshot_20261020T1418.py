from pathlib import Path
import hashlib,importlib.util,sys,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B=R/'results/formal_main_v2/preflight/heartbeat_20261020T2218'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('snapshot20261020T1418',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 p=R/'results/experiment_supervisor/state.json';before=h(p);raw=p.read_bytes();assert h(p)==before
 out=B/'state_before.json'
 with out.open('xb') as f:f.write(raw)
 assert h(out)==before
 print(json.dumps(dict(path=out.relative_to(R).as_posix(),sha256=before,state_unchanged=True)))

from pathlib import Path
import json,hashlib,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1832'
D=R/'.local/nonLong_development_plans_1032';T='results/formal_main_v2/execution/nonLong_action_v1_1032'
rows=[
('libero_spatial_k128_seed23_development.json',4413,'e7af973a3375e4c27c98a3b6a90cac920577241b2676fdabd2c3e9001286c667'),
('libero_object_k128_seed23_development.json',4399,'13fa7f0330208b9f5cca78602cc759c032698ec229e7cfa07b0c4e6bd900f3ad'),
('libero_goal_k128_seed17_references_development.json',7462,'8cdd32e2d85b4f030dcadb7a05338a124ae6b395aed546c6c7a7ed1d9019bbaa')]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('publish1032ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
def put(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw
 else:
  with p.open('xb') as f:f.write(raw)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=h(state)
 out=[]
 for name,size,pin in rows:
  src=D/name;assert src.is_file() and not src.is_symlink() and src.stat().st_size==size and h(src)==pin
  raw=src.read_bytes();doc=json.loads(raw)
  put(R/T/name,raw);put(P/T/name,raw)
  out.append(dict(path=T+'/'+name,sha256=pin,bytes=size,runtime_sha256=h(P/T/name)))
 assert h(state)==before
 receipt=dict(status='exact_execution_manifests_published',source_root=str(D),files=out,state_unchanged=True,new_jobs=0,final_release=False)
 put(R/B/'nonLong_execution_manifest_publication.json',(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode())
 put(R/B/'root_operations/publish_nonlong_manifests_1032.py',Path(__file__).read_bytes())
 print(json.dumps(receipt,ensure_ascii=False))

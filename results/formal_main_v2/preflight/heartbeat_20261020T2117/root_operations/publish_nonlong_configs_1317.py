from pathlib import Path
import json,hashlib,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T2117'
D=R;T='configs/experiments/formal_main_v2'
rows=[["libero_goal_k128_seed41.json","1ce4cb1a4865e21d672c048800414c6634d0ca8b4ea717e1e288d4b35ba2713c"],["libero_spatial_k256_seed17.json","9a740cbe61bbd0cfd3312b756ce49d06344a5007a7b1df8d980ebeeac6413242"],["libero_object_k256_seed17.json","c12d177b3b48845462093d5417bbc759b6065ebecb26f51ac59d9d2e2d05a4a7"],["libero_goal_k256_seed17.json","559997769adaac37fe5f638f64308f6a5757e4e4e0dccc821b0d1f604439b2cf"]]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('publish1317ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
def put(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw
 else:
  with p.open('xb') as f:f.write(raw)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=h(state)
 out=[]
 for name,pin in rows:
  src=R/T/name;assert src.is_file() and not src.is_symlink() and h(src)==pin
  raw=src.read_bytes();size=len(raw)
  dest=P/T/name;assert not dest.exists(),'expected missing config'
  put(dest,raw)
  out.append(dict(path=T+'/'+name,sha256=pin,bytes=size,runtime_sha256=h(dest)))
 assert h(state)==before
 receipt=dict(status='exact_existing_training_configs_copied',source_root=str(D),files=out,state_unchanged=True,new_jobs=0,final_release=False)
 put(R/B/'nonLong_training_config_publication.json',(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode())
 put(R/B/'root_operations/publish_nonlong_configs_1317.py',Path(__file__).read_bytes())
 print(json.dumps(receipt,ensure_ascii=False))

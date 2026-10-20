from pathlib import Path
import json,hashlib,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T2218'
D=R;T='configs/experiments/formal_main_v2'
rows=[['libero_spatial_k256_seed23.json', '22632c2a5d02d05d2b38d21c584c394ee7c4a207caed0ecbb3ebad8c75aaeef6'], ['libero_spatial_k256_seed41.json', '99ce2b9675ecb586cef19ab0616977119041e30daaa28d2e3e4a14d936ea9dd4'], ['libero_object_k256_seed41.json', '0e31c40ea1c9f71ccc7b4d74b62df1958c158ce47a0b1f8d2749d6061b25d5d4']]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('publish20261020T1418ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
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
 put(R/B/'root_operations/publish_nonlong_configs_20261020T1418.py',Path(__file__).read_bytes())
 print(json.dumps(receipt,ensure_ascii=False))

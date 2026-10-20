from pathlib import Path
import json,hashlib,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T2218'
D=R/'.local/nonLong_development_plans_20261020T1418/revision02';T='results/formal_main_v2/execution/nonLong_action_v1_20261020T1418'
rows=[['libero_spatial_k256_seed23_development.json', 4413, 'af318258b35ac8af110663deb9838a7a723a36378a7dce93e9635513fb140be0', 256, 23, 'libero_spatial'], ['libero_spatial_k256_seed41_development.json', 4413, '4bfdc63f4a3adf8661a0d25b5ab81a8262921bb1bbf8395140c0286afb80c3c9', 256, 41, 'libero_spatial'], ['libero_object_k256_seed41_development.json', 4399, '544502f003520760b3203ba67fe135da84b1d5c63b4351ac4ed34e705d3780a5', 256, 41, 'libero_object']]
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
 for name,size,pin,budget,seed,suite in rows:
  src=D/name;assert src.is_file() and not src.is_symlink() and src.stat().st_size==size and h(src)==pin
  raw=src.read_bytes();doc=json.loads(raw)
  assert doc['split']=='development' and len(doc['methods'])==2 and doc['suite']==suite
  assert doc['environment']==dict(environment_seed=0,runtime_seed=17,wait_steps=10,action_chunk=8,max_steps={'libero_spatial':220,'libero_object':280,'libero_goal':300}[doc['suite']])
  assert [m['identity']['method'] for m in doc['methods']]==['A','B'] and all(m['identity']['visual_tokens']==budget and m['identity']['training_seed']==seed and m['identity']['training_complete'] and not m['identity']['future_head_deployed'] for m in doc['methods'])
  put(R/T/name,raw);put(P/T/name,raw)
  out.append(dict(path=T+'/'+name,sha256=pin,bytes=size,runtime_sha256=h(P/T/name)))
 assert h(state)==before
 receipt=dict(status='exact_execution_manifests_published',source_root=str(D),files=out,state_unchanged=True,new_jobs=0,final_release=False)
 put(R/B/'nonLong_execution_manifest_publication.json',(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode())
 put(R/B/'root_operations/publish_nonlong_manifests_20261020T1418.py',Path(__file__).read_bytes())
 print(json.dumps(receipt,ensure_ascii=False))

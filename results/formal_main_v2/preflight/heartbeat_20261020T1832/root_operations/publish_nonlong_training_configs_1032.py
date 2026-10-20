from pathlib import Path
import hashlib,json,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1832'
pins={'configs/experiments/formal_main_v2/libero_spatial_k128_seed23.json':('1486acf0aeaadd5b95a43388190e110138ba3e005708bd267539740292c19700',3346),'configs/experiments/formal_main_v2/libero_object_k128_seed23.json':('d44113bc34a6823e2403cc41cbf799de655855ed28c4ebd7fa3f6d3524b416ed',3341)}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('nonlongconfigpubctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
preview=R/'.local/nonLong_development_plans_1032/dependency_preview_v1/required_P_copies.json';assert h(preview)=='9e5a9d8628260db8788a949bf51a060ee13914f08f57d1eb3e923acc54d52b4e'
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=h(state);rows=[]
 for rel,(pin,size) in pins.items():
  src=R/rel;dst=P/rel
  assert src.is_file() and not src.is_symlink() and h(src)==pin and src.stat().st_size==size
  assert not any(x.is_symlink() for x in [dst,*dst.parents])
  raw=src.read_bytes();json.loads(raw);present=dst.exists()
  if present:assert dst.read_bytes()==raw
  else:
   dst.parent.mkdir(parents=True,exist_ok=True)
   with dst.open('xb') as f:f.write(raw)
  assert h(dst)==pin;rows.append(dict(path=rel,sha256=pin,bytes=size,already_present=present))
 assert h(state)==before
 obj=dict(status='two_original_watched_training_configurations_copied_R_to_P',files=rows,new_GPU_jobs=0,state_unchanged=True,scientific_changes=False)
 rel=B+'/nonLong_training_config_runtime_publication.json'
 with (R/rel).open('x') as f:json.dump(obj,f,sort_keys=True,indent=2);f.write('\n')
 with (R/B/'root_operations/publish_nonlong_training_configs_1032.py').open('xb') as f:f.write(Path(__file__).read_bytes())
 print(json.dumps(dict(receipt=dict(path=rel,sha256=h(R/rel)),**obj)))

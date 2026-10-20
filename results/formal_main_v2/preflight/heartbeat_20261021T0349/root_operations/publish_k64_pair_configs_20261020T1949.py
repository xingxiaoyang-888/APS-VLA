from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';sp=importlib.util.spec_from_file_location('pairconfig1949ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
files={'configs/experiments/formal_main_v2/libero_spatial_k64_seed23.json':'d21812392d4193c35ddb53fa02c91abcece0ac261d98141a97ab247090472645','configs/experiments/formal_main_v2/libero_object_k64_seed23.json':'ee134516837433a66b40907d18c3867b80137159b2c768945e810adbe8ad993d'}
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=h(state);inv=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_bytes());e=[]
 for n,pin in files.items():
  src=R/n;dst=P/n;assert h(src)==h(S/n)==pin and inv['files'][n]==pin
  assert not any(q.is_symlink() for q in [src,dst,*src.parents,*dst.parents]);raw=src.read_bytes()
  if dst.exists():assert dst.read_bytes()==raw
  else:dst.parent.mkdir(parents=True,exist_ok=True);dst.open('xb').write(raw)
  assert h(dst)==pin;e.append({'path':n,'sha256':pin,'bytes':len(raw),'R_S_P_exact':True})
 assert h(state)==before;out=R/'results/formal_main_v2/preflight/heartbeat_20261021T0349/k64_pair_config_dependency_publication.json'
 with out.open('x') as f:json.dump({'status':'exact_original_two_pair_configs_published_for_P_verify','files':e,'state_unchanged':True,'new_scientific_authority':False,'new_GPU_jobs':0},f,indent=2);f.write('\n')
 print(json.dumps({'status':'two_original_pair_configs_R_S_P_identical','receipt_sha256':h(out)}))

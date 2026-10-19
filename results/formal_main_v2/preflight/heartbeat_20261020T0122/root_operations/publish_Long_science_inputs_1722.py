from pathlib import Path
import hashlib,json,os,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B=R/'results/formal_main_v2/preflight/heartbeat_20261020T0122'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
proj=R/'.local/long_development_1722/runtime_science_input_projection.json';assert h(proj)=='0b50a5b152f83a0488c17cc19e3d13c9674949e4939700df1b8cc11a1e40f62e'
rows=json.loads(proj.read_text())['files'];assert len(rows)==222
idx=json.loads((R/'.local/long_development_1722/manifest_index.json').read_text())
expected=set()
for x in idx['shards']:
 expected.add(x['canonical_path'])
 expected.add('configs/experiments/formal_main_v2/libero_10_k'+str(x['visual_tokens'])+'_seed'+str(x['seed'])+'.json')
assert len(expected)==16
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('sciencepublish1722ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statep=R/'results/experiment_supervisor/state.json';before=h(statep);s=json.loads(statep.read_text());assert s['pending_submission'] is None
 missing=[]
 for x in rows:
  src=R/x['local_path'];dst=Path(x['server_path'])
  assert R in src.parents and P in dst.parents and '..' not in src.parts and '..' not in dst.parts
  assert not any(p.is_symlink() for p in [src,*src.parents,dst,*dst.parents]) and src.is_file() and h(src)==x['sha256'] and src.stat().st_size==x['bytes']
  if dst.exists():assert h(dst)==x['sha256']
  else:
   assert dst.relative_to(P).as_posix() in expected and src.relative_to(R).as_posix()==dst.relative_to(P).as_posix()
   assert src.suffix=='.json' and src.stat().st_size<100000
   missing.append(x)
 assert {Path(x['server_path']).relative_to(P).as_posix() for x in missing}==expected
 for x in missing:
  src=R/x['local_path'];dst=Path(x['server_path']);dst.parent.mkdir(parents=True,exist_ok=True)
  with dst.open('xb') as f:f.write(src.read_bytes());f.flush();os.fsync(f.fileno())
  assert h(dst)==x['sha256']
 for x in rows:assert h(Path(x['server_path']))==x['sha256']
 assert h(statep)==before
 out=B/'Long_runtime_science_publication.json'
 with out.open('x') as f:json.dump(dict(schema='formal_main_v2',kind='root_exact_runtime_scientific_input_publication',status='all222_scientific_inputs_present_exact',projection=dict(path=proj.relative_to(R).as_posix(),sha256=h(proj)),new_files=missing,existing_files_unchanged=206,source_files_unchanged=True,outer_runtime_readiness=False,submission_authorized=False,no_GPU_submission=True,state_unchanged=True),f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(dict(path=out.relative_to(R).as_posix(),sha256=h(out),published_files=len(missing),all_inputs=222,production_ready=False)))

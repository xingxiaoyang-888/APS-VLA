"""Publish exact reviewed Goal candidate to new R/P paths; no GPU authority."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,os,shutil,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
SRC=R/'.local/goal_gate_integration_20261020T2156/package';PKG='scripts/ops/formal_goal_paired_input_gate_v1';B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0556'
MSHA='7e7da3f5b514102f08d105677e1dff504989aaf6c647f320405526d1fd2982ec'
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(p):
 p=Path(p);assert p.is_absolute() and p.resolve()==p and not any(x.is_symlink() for x in (p,*p.parents));return p
def load(p,pin,name):
 assert h(safe(p))==pin;spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def write(p,raw):
 safe(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def main():
 assert Path.cwd()==R and sys.dont_write_bytecode
 c=load(R/'scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','goalpubctl')
 with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
  sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=json.loads(sp.read_bytes())
  assert s['pending_submission'] is None and s['formal_main_progress']['root_and_independent_completed_arms']==72 and not s['formal_main_progress']['test_opened']
  assert h(SRC/'package_manifest.json')==MSHA
  mf=json.loads((SRC/'package_manifest.json').read_bytes())
  names=['entry.py','observer_v3.py','ast_observer_v2.py','paired_input_gate_v1.py','ast_gate_v2.py','config.json','prefix58.json','run.slurm']
  assert set(mf['files'])=={PKG+'/'+n for n in names}
  closure=R/'.local/goal_gate_integration_20261020T2156/CPU_production_preflight01/source_closure.json'
  assert h(closure)=='0c21661833a02a5a7e870c2280d137c8f2d9d3fa8eeb48fe02ab95b384d22639'
  files=json.loads(closure.read_bytes())['files']
  for p,v in files.items():assert h(safe(p))==v['sha256'],p
  assert shutil.disk_usage(P).free>=4363621114
  names+=['package_manifest.json']
  assert not (B/'Goal_paired_publication.json').exists()
  for n in names:
   assert h(safe(SRC/n))==(MSHA if n=='package_manifest.json' else mf['files'][PKG+'/'+n])
   for root in [R,P]:assert not safe(root/PKG/n).exists(),'publication destination exists'
  for n in names:
   raw=(SRC/n).read_bytes()
   for root in [R,P]:write(root/PKG/n,raw)
  entry=load(P/PKG/'entry.py',mf['files'][PKG+'/entry.py'],'goalpubentry')
  entry.validate_config(json.loads((P/PKG/'config.json').read_bytes()))
  inv,wrapper,ctx,legacy=entry.prepare_original()
  pp=entry.validate_prefix(inv,legacy,json.loads((P/PKG/'prefix58.json').read_bytes())['rows'])
  import torch
  assert not torch.cuda.is_initialized() and not entry.OUTPUT.exists() and not entry.AUTH.exists()
  for n in names:
   assert h(R/PKG/n)==h(P/PKG/n)==h(SRC/n)
  for p,v in files.items():assert h(safe(p))==v['sha256'],p
  assert h(sp)==before
  out=dict(schema='formal_main_v2',status='published_exact_eight_files_actual_P_CPU_verified_no_GPU_authority',utc=datetime.now(timezone.utc).isoformat(),package_manifest_sha256=MSHA,files=mf['files'],source_closure_sha256=h(closure),source_closure_paths=len(files),prefix_proof=pp,original_selected_checkpoint_bytes_verified=True,CPU_fixture_disabled_by_production_entry=True,state_sha256=before,scientific_trials_added=0,GPU_jobs_submitted=0,root_authorization_created=False,Goal_old200_and_new_science_HOLD=True,final_values_read=False)
  write(B/'Goal_paired_publication.json',(json.dumps(out,indent=2,sort_keys=True)+'\n').encode())
  print(json.dumps({k:v for k,v in out.items() if k!='files'}))
if __name__=='__main__':main()

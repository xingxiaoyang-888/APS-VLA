from pathlib import Path
import hashlib,json,sys,importlib.util,subprocess
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261020T2330'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,b):
 assert p.is_relative_to(R) or p.is_relative_to(P)
 for x in (p,*p.parents):assert not x.is_symlink()
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b
 else:
  with p.open('xb') as f:f.write(b)
 return dict(path=str(p),sha256=h(p))
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('prep641530c',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
ip=R/'.local/nonLong64_development_plans_20261020T1530/execution_manifest_candidates.json';assert h(ip)=='ed844da98872f2c7e684cb5157e585e6ddfb5a759c2f69ad478961f58259e346'
helper=R/'.local/devterminal_independent_20261020T1530/recompute_spatial256.py';assert h(helper)=='e4d2747b673c2ee076078430dc5a40f6b0be81303618d08dc4d62119ddd0fc52'
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=h(state);rows=[]
 idx=json.loads(ip.read_bytes());assert len(idx['plans'])==4 and idx['total_trials']==800 and idx['final_enabled'] is False
 for v in idx['plans']:
  assert v['suite'] in ['libero_spatial','libero_object'] and v['seed'] in [17,41] and v['budget']==64 and v['expected_trials']==200
  src=R/v['candidate']['path'];assert h(src)==v['candidate']['sha256'];dest=v['canonical_path'];assert dest.startswith('results/formal_main_v2/execution/nonLong_action_v1_20261020T1530/')
  for base in (R,P):rows.append(put(base/dest,src.read_bytes()))
 result=subprocess.run([sys.executable,'-B',str(helper),'--statistics-ref','.local/devterminal_independent_20261020T1530/development_statistics.json','--statistics-sha','3ea06d35c1f8f92a30a46449212080c3d952f08e2d1a8f633b568e75d760648a','--output',B+'/Spatial256_root_bootstrap_recomputation.json'],capture_output=True,text=True,timeout=45)
 assert result.returncode==0,result.stderr
 assert json.loads(result.stdout)['status']=='passed' and h(state)==before
 receipt=dict(status='four_exact_manifest_copies_and_root_statistics_recomputation',files=rows,state_unchanged=True,new_jobs=0,final_opened=False,statistics=dict(path=B+'/Spatial256_root_bootstrap_recomputation.json',sha256=h(R/B/'Spatial256_root_bootstrap_recomputation.json')))
 put(R/B/'next64_manifest_publication.json',(json.dumps(receipt,sort_keys=True,indent=2)+'\n').encode());print(json.dumps(receipt))

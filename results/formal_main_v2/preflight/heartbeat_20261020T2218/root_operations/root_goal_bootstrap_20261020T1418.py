from pathlib import Path
import hashlib,sys,importlib.util,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
m=load('.local/integration_candidate_20261020T1418/recompute_goal_bootstrap_v1.py','17d4d6f3d48c2e83421c784eb3352e9550838251d6b89a136df6d87be8179118','rootgoal1418bootstrap')
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','rootgoal1418ctl')
result=m.recompute()
assert result['status']=='passed' and result['new_GPU_jobs']==0 and result['unique_initial_states']==100
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json')
 out=R/'results/formal_main_v2/preflight/heartbeat_20261020T2218/Goal128_root_bootstrap_recomputation.json'
 with out.open('x') as f:json.dump(result,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
 assert h(R/'results/experiment_supervisor/state.json')==before
 print(json.dumps(dict(path=out.relative_to(R).as_posix(),sha256=h(out),means=result['means_percent'],CI=result['bootstrap_interval95_pp'],SD=result['seed_sample_SD_pp'])))

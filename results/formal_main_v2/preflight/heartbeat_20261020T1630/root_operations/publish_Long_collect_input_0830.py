from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1630'
D='.local/long_collection_prepare_0830';out='results/formal_main_v2/execution/long_collect_action_v1_0830/dense_development.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=h(p),bytes=p.stat().st_size)
def load(rel):return json.loads((R/rel).read_bytes())
p=R/D/'dense_development.json';assert h(p)=='703980515d5b063c31276b0e610ffd6cdf68adae5e1f43cfb65ecd61d92923f1'
ep=R/D/'dense_input_evidence.json';assert h(ep)=='766756f88add0d010dadf408fd3da9c90593c5ad2e03acaa3d6e1ff68a40499f'
x=json.loads(p.read_bytes());e=json.loads(ep.read_bytes())
assert x['suite']=='libero_10' and x['split']=='development' and len(x['methods'])==1
assert x['methods'][0]['identity']['method']=='dense' and x['methods'][0]['identity']['visual_tokens']==512
assert x['methods'][0]['identity']['future_head_deployed'] is False
assert x['environment']==dict(action_chunk=8,environment_seed=0,max_steps=520,runtime_seed=17,wait_steps=10)
assert h(R/x['development_panel'])==x['development_panel_sha256']=='46a06087483151e36198167e7d4e5313c50b63172e09128d65a3650112f0a268'
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('publishcollect0830',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=h(state);s=json.loads(state.read_bytes())
 assert s['pending_submission'] is None
 assert not any(j.get('mode')=='collect' and j.get('suite')=='libero_10' for j in s['registered_jobs'])
 inv=load('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json')
 assert len(inv['files'])==173 and out not in inv['files']
 for name,pin in inv['files'].items():assert h(R/name)==h(P/'snapshots/formal_main_v2_run_564be0995e'/name)==pin
 for target in (R/out,P/out):assert not target.exists()
 for target in (R/out,P/out):
  target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as f:f.write(p.read_bytes())
 assert h(R/out)==h(P/out)==h(p) and h(state)==before
 report=dict(schema='formal_main_v2',kind='root_publish_original_Dense_only_collection_input',utc=datetime.now(timezone.utc).isoformat(),status='published_input_only_no_submission_authorization',source=ref(p),input_evidence=ref(ep),canonical=ref(R/out),runtime_copy=str(P/out),runtime_sha256=h(P/out),protected_files_verified=173,state_unchanged=True,final_state_values_read=False,new_GPU_submissions=0,future_head_deployed=False)
 q=R/B/'Long_collect_dense_input_publication.json'
 with q.open('x') as f:json.dump(report,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(dict(status=report['status'],canonical=ref(R/out),receipt=ref(q))))

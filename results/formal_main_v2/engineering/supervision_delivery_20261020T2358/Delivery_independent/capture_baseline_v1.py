from pathlib import Path
import hashlib,json,sys
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=R/'.local/delivery_independent_20261020T2358';S=P/'snapshots/formal_main_v2_run_564be0995e';M=R/'snapshots/formal_main_v2_run_564be0995e'
def h(b):return hashlib.sha256(b).hexdigest()
def ref(p):b=p.read_bytes();return {'path':str(p.relative_to(R)) if p.is_relative_to(R) else str(p),'sha256':h(b),'bytes':len(b)}
def save(name,b):
 p=D/name;assert not p.exists()
 with p.open('xb') as f:f.write(b)
 return ref(p)
def jout(x):return (json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect','socket.bind'):raise RuntimeError('No execution/network in baseline auditor')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes)) and ((mode and any(v in mode for v in 'wax+')) or (isinstance(flags,int) and flags&(1|2|64|512|1024))):
   if not Path(path).resolve().is_relative_to(D):raise RuntimeError('write outside private audit dir')
sys.addaudithook(guard)
sp=R/'results/experiment_supervisor/state.json';b=sp.read_bytes();assert h(b)=='a0d4d98f112adc082a04789c764d8c6006a2133cb61834f4b0e2097f5b64fb10'
s=json.loads(b);base=save('baseline_state.json',b)
invp=R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';ib=invp.read_bytes();assert h(ib)=='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
inv=json.loads(ib);assert len(inv['files'])==173
rows=[]
for rel,want in inv['files'].items():
 row={'relative':rel,'sha256':want,'roots':{}}
 for label,root in [('canonical_R',R),('frozen_S',S),('source_mirror_R',M)]:
  p=root/rel;assert p.is_file() and p.resolve()==p and all(not q.is_symlink() for q in [p,*p.parents])
  rb=p.read_bytes();assert h(rb)==want;row['roots'][label]={'bytes':len(rb),'sha256':h(rb)}
 rows.append(row)
docnames=['正式主实验规划','完整实验计划','实验进度','正式主实验阶段结论','正式自动连续训练执行登记','研究方案','论文方法与实验设置草稿']
docs={name:ref(R/('docs/'+name+'.md')) for name in docnames}
prev=R/'results/formal_main_v2/preflight/heartbeat_20261021T0653/final_summary.json';assert ref(prev)['sha256']=='f4d17e968396671b9e8072de1503133652b437e1dd9eee040f74c5d37a56b12d'
obs=R/'results/formal_main_v2/preflight/heartbeat_20261021T0758/live_observation.json';assert ref(obs)['sha256']=='36b9bfbc9d09e5aeca5fedb1b82abb021dcc41633d6676ab18d68aeef4f4c102'
f=s['formal_main_progress'];assert (f['root_and_independent_completed_arms'],f['root_and_independent_reviewed_arm_updates'],f['current_action_development_trial_count'],f['completed_development_trials'],f['completed_final_trials'])==(72,360000,5800,7012,0)
assert len(s['autonomous_training_v1']['completed_pairs'])==36 and not f['global_release_created'] and not f['test_opened'] and s['pending_submission'] is None
assert sp.read_bytes()==b
report={'schema':'formal_main_v2','kind':'independent_pre_snapshot_baseline_capture','status':'passed_baseline_only','utc':datetime.now(timezone.utc).isoformat(),'baseline_state':base,'original_state_path':'results/experiment_supervisor/state.json','prior_summary':ref(prev),'existing_single_live_observation':ref(obs),'source173_inventory':ref(invp),'frozen_source_checks':rows,'source173_three_roots_verified':True,'documents_before':docs,'new_state_Git_P_canonical_Slurm_writes':0,'additional_Slurm_queries':0,'future_snapshot_verified':False}
out=save('baseline_capture.json',jout(report));print(json.dumps({'report':out,'source173_three_roots':True,'state_sha256':h(b)}))

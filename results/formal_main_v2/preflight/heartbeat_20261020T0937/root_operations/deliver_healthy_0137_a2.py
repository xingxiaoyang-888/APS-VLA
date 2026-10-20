from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T0937'
HEAD='148b37535e2bcf1b64a4096a05a3f9e27f8c7cff'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.run(['git','-c','core.quotepath=false',*a],cwd=R,capture_output=True,check=True)
def rd(rel):return json.loads((R/rel).read_bytes())
def save(rel,x):
 p=R/rel
 with p.open('x') as f:json.dump(x,f,sort_keys=True,indent=2);f.write('\n')
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('git0137ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 state=rd('results/experiment_supervisor/state.json');f=state['formal_main_progress']
 assert state['pending_submission'] is None and f['root_and_independent_completed_arms']==54 and f['trained_arms']==54 and f['root_and_independent_reviewed_arm_updates']==277000
 assert f['completed_development_trials']==1412 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert state['autonomous_training_v1']['reserved_GPU_slots']==0
 source=B+'/root_operations/deliver_healthy_0137_a2.py'
 with (R/source).open('xb') as stream:stream.write(Path(__file__).read_bytes())
 exact={'results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl'}
 allowed_excluded={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/slurm/cti-formal_3044017.out','results/slurm/cti-formal_3044017.err','results/formal_main_v2/control_transport/heartbeat_0137_delivery_a2.jsonl'}
 selected=[];excluded=[]
 for row in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split('\0'):
  if not row:continue
  status,name=row[:2],row[3:];assert status in (' M','??'),row
  accept=name in exact or name.startswith(B+'/')
  if name.startswith('results/formal_main_v2/control_transport/'):
   lines=(R/name).read_text().splitlines();accept=bool(lines) and json.loads(lines[-1]).get('event')=='control_end'
  if accept:
   p=R/name;assert p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20)
   assert p.suffix in {'.json','.jsonl','.txt','.py'}
   selected.append(name)
  else:excluded.append(name)
 assert set(excluded)<=allowed_excluded,excluded
 for i in range(0,len(selected),50):git('add','--',*selected[i:i+50])
 for name in selected:assert git('show',':'+name).stdout==(R/name).read_bytes()
 inv=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json');assert len(inv['files'])==173
 for name,pin in inv['files'].items():assert h(R/name)==hashlib.sha256(git('show',':'+name).stdout).hexdigest()==pin
 git('diff','--cached','--check')
 save(B+'/git_delivery.json',dict(schema='formal_main_v2',status='checked_healthy_snapshot_ready_for_nonforce_push',retained_attempts='First writer-lock contention and second strict live-audit filename mismatch retained; no index/GPU/state mutation by either failed delivery attempt',utc=datetime.now(timezone.utc).isoformat(),baseline=HEAD,frozen_index_and_worktree_files=173,files=[dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size) for n in sorted(selected)],excluded_live_files=excluded,raw_tail_diagnostics_not_final_results=True,full_original_logs_remain_on_server=True,new_GPU_submissions=[],completed_training_groups=54,completed_final_trials=0,final_sealed=True,normal_jobs_not_polled_again=True,no_independent_or_new_scientific_result_claim=True))
 git('add','--',B+'/git_delivery.json');assert git('show',':'+B+'/git_delivery.json').stdout==(R/B/'git_delivery.json').read_bytes()
 git('diff','--cached','--check')
 out=git('commit','-m','Record healthy eight-GPU supervision without duplicate submissions')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_0137.json',dict(commit=commit,baseline=HEAD,files=len(selected)+1,complete=54,no_new_terminal=True))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=commit,files=len(selected)+1,summary=out.stdout.decode().splitlines()[:2])))

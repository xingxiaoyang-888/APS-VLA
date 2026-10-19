from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T0530'
HEAD='7d2c6c2173fd36bd8e9139493abb042818d516a6'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
def save(rel,value):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(value,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('finalize2130ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD
 guard=R/B/'git_index_guard.stdout.json';g=json.loads(guard.read_text())
 assert g['status']=='verified_index_archive_delivery' and g['frozen_files_verified_in_worktree_and_index']==173
 assert len(g['raw_paths_restored_exactly'])==1 and g['raw_paths_restored_exactly'][0]['bytes']==132813168
 required=json.loads((R/B/'git_required_files.json').read_bytes())
 staged=set(git('diff','--cached','--name-only').stdout.decode().splitlines())
 assert staged=={x['path'] for x in required['files']}|{B+'/git_required_files.json'}
 for row in required['files']:
  raw=git('show',':'+row['path']).stdout;assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
  if row['path'] not in ['results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl']:assert h(R/row['path'])==row['sha256']
 assert git('show',':'+B+'/git_required_files.json').stdout==(R/B/'git_required_files.json').read_bytes()
 inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_bytes())
 for name,pin in inventory['files'].items():assert h(R/name)==hashlib.sha256(git('show',':'+name).stdout).hexdigest()==pin
 note=json.loads((R/B/'git_index_delivery.json').read_bytes());exceptions=note['raw_whitespace_exceptions']
 for row in exceptions:assert h(R/row['path'])==row['sha256']
 git('diff','--cached','--check','--','.',*[':(exclude)'+x['path'] for x in exceptions])
 live=json.loads((R/'results/experiment_supervisor/state.json').read_bytes());snap=json.loads(git('show',':results/experiment_supervisor/state.json').stdout)
 assert live['pending_submission'] is None and live['formal_main_progress']['root_and_independent_completed_arms']==48
 assert live['formal_main_progress']['completed_training_pairs']==snap['formal_main_progress']['completed_training_pairs']
 assert {j['job_id'] for j in live['registered_jobs']}=={j['job_id'] for j in snap['registered_jobs']}
 assert live['autonomous_training_v1']['owner_id']==snap['autonomous_training_v1']['owner_id'] and live['autonomous_training_v1']['reserved_GPU_slots']==snap['autonomous_training_v1']['reserved_GPU_slots']==0
 assert live['formal_main_progress']['completed_final_trials']==0 and not live['formal_main_progress']['global_release_created']
 source=B+'/root_operations/finalize_delivery_2130.py'
 with (R/source).open('xb') as f:f.write(Path(__file__).read_bytes())
 audit='results/formal_main_v2/control_transport/heartbeat_2130_stage_delivery_a2.jsonl';lines=(R/audit).read_text().splitlines();assert json.loads(lines[-1])['event']=='control_end'
 alias_audit='results/formal_main_v2/control_transport/heartbeat_2130_canonical_alias_delivery.jsonl';assert json.loads((R/alias_audit).read_text().splitlines()[-1])['event']=='control_end'
 additions=[source,audit,alias_audit,B+'/git_index_guard.stdout.json',B+'/git_index_guard.stderr.txt',B+'/git_whitespace_diagnostic.json',B+'/git_index_delivery.json']
 for rel in additions:
  p=R/rel;assert p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20)
  git('add','--',rel);assert git('show',':'+rel).stdout==p.read_bytes()
 save(B+'/git_delivery.json',dict(schema='formal_main_v2',utc=datetime.now(timezone.utc).isoformat(),status='checked_server_index_ready_for_nonforce_push',baseline=HEAD,required_files=B+'/git_required_files.json',incremental_archive_guard=dict(path=B+'/git_index_guard.stdout.json',sha256=h(guard)),new_raw_restored=1,new_raw_bytes=132813168,previous_union29_unchanged=True,frozen_files=173,weights_added=False,root_independent_complete=48,machine_complete=50,root_accepted_updates=248000,exact_Long_GPU_job='3043709',duplicate_submissions=0,Spatial_original1500_recovered_and_single_continuous5000_admitted=True,Spatial_new_continuous_job_not_submitted=True,final_sealed=True,preserved_raw_whitespace_exceptions=exceptions,additions=[dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size) for n in additions],live_controller_ticks_after_snapshot_deferred=True,normal_live_GPU_not_polled_for_git=True))
 git('add','--',B+'/git_delivery.json');assert git('show',':'+B+'/git_delivery.json').stdout==(R/B/'git_delivery.json').read_bytes()
 git('diff','--cached','--check','--','.',*[':(exclude)'+x['path'] for x in exceptions])
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines())
 answer=git('commit','-m','Verify Spatial recovery and start paired Long development without duplicate jobs')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_2130.json',dict(commit=commit,baseline=HEAD,files=count,index_guard='passed',root_complete=48,machine_complete=50))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=commit,files=count,summary=answer.stdout.decode().splitlines()[:2])))

from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T0833';E='results/formal_main_v2/engineering/supervision_delivery_0033'
HEAD='532ec5c0696c7613f45a52a9389c0d1a25a6cd60'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
def read(rel):return json.loads((R/rel).read_bytes())
def save(rel,value):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as stream:json.dump(value,stream,sort_keys=True,ensure_ascii=False,indent=2);stream.write('\n')
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('finalize0033ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD
 guard=R/B/'git_index_guard.stdout.json';g=json.loads(guard.read_text());assert g['status']=='verified_index_archive_delivery' and g['frozen_files_verified_in_worktree_and_index']==173
 assert len(g['raw_paths_restored_exactly'])==3 and sum(x['bytes'] for x in g['raw_paths_restored_exactly'])==178950489
 required=read(B+'/git_required_files.json');staged=set(git('diff','--cached','--name-only').stdout.decode().splitlines())
 assert staged=={x['path'] for x in required['files']}|{B+'/git_required_files.json'}
 for row in required['files']:
  raw=git('show',':'+row['path']).stdout;assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
  if row['path'] not in ['results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl']:assert h(R/row['path'])==row['sha256']
 assert git('show',':'+B+'/git_required_files.json').stdout==(R/B/'git_required_files.json').read_bytes()
 inventory=read('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json')
 for name,pin in inventory['files'].items():assert h(R/name)==hashlib.sha256(git('show',':'+name).stdout).hexdigest()==pin
 note=read(B+'/git_index_delivery.json');exceptions=note['raw_whitespace_exceptions']
 for row in exceptions:assert h(R/row['path'])==row['sha256']
 git('diff','--cached','--check','--','.',*[':(exclude)'+x['path'] for x in exceptions])
 live=read('results/experiment_supervisor/state.json');snap=json.loads(git('show',':results/experiment_supervisor/state.json').stdout)
 assert live['pending_submission'] is None and live['formal_main_progress']['root_and_independent_completed_arms']==54
 assert live['formal_main_progress']['completed_training_pairs']==snap['formal_main_progress']['completed_training_pairs']
 assert {j['job_id'] for j in live['registered_jobs']}=={j['job_id'] for j in snap['registered_jobs']}
 assert live['autonomous_training_v1']['owner_id']==snap['autonomous_training_v1']['owner_id']
 assert live['autonomous_training_v1']['reserved_GPU_slots']==snap['autonomous_training_v1']['reserved_GPU_slots']==0
 assert live['formal_main_progress']['completed_development_trials']==1412 and live['formal_main_progress']['completed_final_trials']==0 and not live['formal_main_progress']['global_release_created']
 source=B+'/root_operations/finalize_delivery_0033.py'
 with (R/source).open('xb') as stream:stream.write(Path(__file__).read_bytes())
 audit='results/formal_main_v2/control_transport/heartbeat_0033_stage_delivery.jsonl';assert json.loads((R/audit).read_text().splitlines()[-1])['event']=='control_end'
 additions=[source,audit,B+'/git_index_guard.stdout.json',B+'/git_index_guard.stderr.txt',B+'/git_whitespace_diagnostic.json',B+'/git_index_delivery.json']
 for rel in additions:
  p=R/rel;assert p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20)
  assert p.suffix in {'.py','.md','.json','.jsonl','.txt'} and not any(t in rel.lower() for t in ['sealed','initial_state','final_state','checkpoint'])
  git('add','--',rel);assert git('show',':'+rel).stdout==p.read_bytes()
 save(B+'/git_delivery.json',dict(schema='formal_main_v2',utc=datetime.now(timezone.utc).isoformat(),status='checked_server_index_ready_for_nonforce_push',baseline=HEAD,required_files=B+'/git_required_files.json',incremental_archive_guard=dict(path=B+'/git_index_guard.stdout.json',sha256=h(guard)),new_raw_restored=3,new_raw_bytes=178950489,previous_archives_unchanged=True,frozen_files=173,weights_added=False,root_independent_complete=54,root_accepted_updates=277000,new_development_trials=0,new_GPU_submissions=['3044017'],duplicate_submissions=0,final_sealed=True,preserved_raw_whitespace_exceptions=exceptions,additions=[dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size) for n in additions],live_controller_ticks_after_snapshot_deferred=True,normal_live_GPU_not_polled_for_git=True))
 git('add','--',B+'/git_delivery.json');assert git('show',':'+B+'/git_delivery.json').stdout==(R/B/'git_delivery.json').read_bytes()
 git('diff','--cached','--check','--','.',*[':(exclude)'+x['path'] for x in exceptions])
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines())
 answer=git('commit','-m','Accept Goal256 seed23 training and audit bounded recovery admission')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_0033.json',dict(commit=commit,baseline=HEAD,files=count,index_guard='passed',root_complete=54,new_development_trials=0))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=commit,files=count,summary=answer.stdout.decode().splitlines()[:2])),flush=True)

from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0332'
HEAD='218e99cd2cec7eed0bf7c4cf1984e2b152bc9121'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
def save(rel,v):
 with (R/rel).open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('finish1932ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD
 guard=R/B/'git_index_guard.stdout.json';assert h(guard)=='861cd832d178ab97e91eef94b5631a38c8398c55bfe1c67593650283be7cd885'
 check=json.loads(guard.read_text());assert check['status']=='verified_index_archive_delivery' and check['frozen_files_verified_in_worktree_and_index']==173 and len(check['raw_paths_restored_exactly'])==29
 required=json.loads((R/B/'git_required_files.json').read_text())
 staged=set(git('diff','--cached','--name-only').stdout.decode().splitlines())
 assert staged=={x['path'] for x in required['files']}|{B+'/git_required_files.json'}
 for row in required['files']:
  raw=git('show',':'+row['path']).stdout;assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
  if row['path'] not in ['results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl']:assert h(R/row['path'])==row['sha256']
 assert git('show',':'+B+'/git_required_files.json').stdout==(R/B/'git_required_files.json').read_bytes()
 assert not git('diff','--cached','--name-only','--','configs','src','scripts','AGENTS.md').stdout
 inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text())
 for name,pin in inventory['files'].items():assert h(R/name)==hashlib.sha256(git('show',':'+name).stdout).hexdigest()==pin
 rawdiff='results/formal_main_v2/engineering/terminal_delivery_1932/independent/audit.diff'
 assert h(R/rawdiff)=='98c1e009f27056d403a5d555ff38f55ab295c11e8d82fd5dce3b90351233a927'
 diagnostic=git('diff','--cached','--check',check=False)
 assert diagnostic.returncode==2 and diagnostic.stdout.decode()==rawdiff+':43: trailing whitespace.\n+ \n' and not diagnostic.stderr
 git('diff','--cached','--check','--','.',':(exclude)'+rawdiff)
 status=json.loads((R/'results/experiment_supervisor/state.json').read_text())
 assert status['pending_submission'] is None and status['formal_main_progress']['root_and_independent_completed_arms']==48
 staged_state=json.loads(git('show',':results/experiment_supervisor/state.json').stdout)
 assert status['formal_main_progress']['completed_training_pairs']==staged_state['formal_main_progress']['completed_training_pairs']
 assert {j['job_id'] for j in status['registered_jobs']}=={j['job_id'] for j in staged_state['registered_jobs']}
 assert status['autonomous_training_v1']['reservation_root_record']==staged_state['autonomous_training_v1']['reservation_root_record']
 source=B+'/root_operations/finalize_commit_1932_v2.py'
 with (R/source).open('xb') as f:f.write(Path(__file__).read_bytes())
 compile((R/source).read_bytes(),source,'exec')
 audit='results/formal_main_v2/control_transport/heartbeat_1932_commit.jsonl';lines=(R/audit).read_text().splitlines();assert json.loads(lines[-1])['event']=='control_end'
 note=B+'/git_raw_diff_preservation.json'
 save(note,dict(schema='formal_main_v2',status='exact_raw_audit_diff_preserved',utc=datetime.now(timezone.utc).isoformat(),initial_commit_not_created=True,initial_full_archive_index_guard_passed=True,reason='The prior commit gate allowed raw log/text whitespace but did not include the preserved unified-diff audit artifact. Only this exact SHA-bound raw diff line is excepted; source/docs are still checked without exceptions.',raw_path=rawdiff,raw_sha256=h(R/rawdiff),diagnostic=diagnostic.stdout.decode(),scientific_sources_changed=False,original_failed_commit_script_retained=B+'/root_operations/commit_1932.py'))
 additions=[source,audit,note,B+'/git_index_guard.stdout.json',B+'/git_index_guard.stderr.txt']
 for rel in additions:
  p=R/rel;assert p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20)
  git('add','--',rel);assert git('show',':'+rel).stdout==p.read_bytes()
 delivery=B+'/git_delivery.json'
 save(delivery,dict(schema='formal_main_v2',status='full_archive_index_verified_final_metadata_verified',baseline=HEAD,initial_required_files=B+'/git_required_files.json',full_index_guard=dict(path=B+'/git_index_guard.stdout.json',sha256=h(guard)),raw_restored_exactly=29,raw_bytes=1126966804,frozen_index_and_worktree_files=173,weights_added=False,scientific_sources_and_config_changed=False,raw_whitespace_exception=dict(path=rawdiff,sha256=h(R/rawdiff)),bounded_operational_metadata_additions=[dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size) for n in additions],excluded_live_files=['results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/slurm/cti-formal_3043399.out','results/slurm/cti-formal_3043399.err'],normal_training_not_polled_for_git=True,supervisor_snapshot_is_exact_as_of_initial_index_guard=True,live_controller_ticks_after_snapshot_deferred_to_next_heartbeat=True))
 git('add','--',delivery);assert git('show',':'+delivery).stdout==(R/delivery).read_bytes()
 git('diff','--cached','--check','--','.',':(exclude)'+rawdiff)
 result=git('commit','-m','Verify 48 training groups and resume the registered Spatial recovery')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_1932.json',dict(commit=commit,baseline=HEAD,index_guard='passed',raw_diff_byte_preservation='passed',files=len(staged)+len(additions)+1))
 print(json.dumps(dict(status='committed',commit=commit,files=len(staged)+len(additions)+1,pushed=False,summary=result.stdout.decode().splitlines()[:2])))

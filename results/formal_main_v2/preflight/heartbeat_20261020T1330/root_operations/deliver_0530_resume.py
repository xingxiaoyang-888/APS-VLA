from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1330';E='results/formal_main_v2/engineering/supervision_delivery_0530'
HEAD='07535f5ff2989b0b6b9319d9f604a4ceceb71258'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel):return json.loads((R/rel).read_bytes())
def ref(rel):return dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('delivery0530resume',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD
 req=B+'/git_required_files.json';assert h(R/req)=='014c794d06f7f4148d7efda17e60d82019de482734b2379c311542d3656fdc6e'
 guard=B+'/git_index_guard.stdout.json';assert h(R/guard)=='9f4cbf7fdba670f6891c3f651a052efee4de9a1da5a08f56222c1bbc0b06c6ae'
 diag=B+'/git_whitespace_diagnostic.json';assert h(R/diag)=='77e9b48c3057d4de372e3375eac195ce812ca7e1400c5fecdec35177f56bdf28'
 source=B+'/root_operations/deliver_0530.py';assert h(R/source)=='f81e9d7598cc6ec4d52440182d2580eb5cb1051c6d18aa31ce4469aab4aa7e11'
 expected={r['path'] for r in rd(req)['files']}|{req}
 actual=set(git('diff','--cached','--name-only').stdout.decode().splitlines());assert expected==actual
 for row in rd(req)['files']+[ref(req)]:
  raw=git('show',':'+row['path']).stdout;assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],row['path']
 guard_obj=rd(guard);assert guard_obj['status']=='verified_index_archive_delivery' and guard_obj['frozen_files_verified_in_worktree_and_index']==173
 assert len(guard_obj['raw_paths_restored_exactly'])==3 and sum(x['bytes'] for x in guard_obj['raw_paths_restored_exactly'])==169428644
 inventory=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json')
 assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():
  assert h(R/rel)==pin and hashlib.sha256(git('show',':'+rel).stdout).hexdigest()==pin,rel
 state=json.loads(git('show',':results/experiment_supervisor/state.json').stdout);f=state['formal_main_progress']
 assert f['root_and_independent_completed_arms']==60 and f['root_and_independent_reviewed_arm_updates']==305000 and f['completed_development_trials']==1612
 assert state['pending_submission'] is None and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 for rel,pin in rd('results/formal_main_v2/downstream_reviews/3045322.json')['files'].items():
  assert hashlib.sha256(git('show',':'+rel).stdout).hexdigest()==pin
 failure='results/formal_main_v2/control_transport/heartbeat_0530_delivery.jsonl'
 audit=[json.loads(v) for v in (R/failure).read_text().splitlines()];assert audit[-1]['event']=='control_end' and audit[-1]['returncode']==1
 diag_now=git('diff','--cached','--check',check=False)
 assert diag_now.returncode==2 and diag_now.stdout.decode()==rd(diag)['stdout'] and not diag_now.stderr
 exceptions=[E+'/Goal128seed41_independent/adaptation.diff',source]
 assert rd(diag)['stdout']==exceptions[0]+':43: trailing whitespace.\n+ \n'+exceptions[1]+':105: new blank line at EOF.\n'
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 resume=B+'/root_operations/deliver_0530_resume.py'
 with (R/resume).open('xb') as stream:stream.write(Path(__file__).read_bytes())
 fix=B+'/git_delivery_bounded_correction.json'
 save(fix,dict(status='exact_original_staged_evidence_reverified',utc=datetime.now(timezone.utc).isoformat(),original_failed_operation=ref(source),failure_transport=ref(failure),original_archive_guard=ref(guard),original_required_files=ref(req),first_failure='Own archived execution source contained one extra newline at EOF; scientific and archive checks already passed.',correction='Retain the executed source bytes and original patch bytes unchanged as provenance; allow only their two pinned whitespace diagnostics. The recovery source itself has no added whitespace diagnostics.',whitespace_exceptions=[ref(x) for x in exceptions],scientific_changes=False,state_changes=False,Slurm_changes=False,original_index_exactly_unchanged=True,weights_added=False))
 additions=[guard,B+'/git_index_guard.stderr.txt',diag,resume,fix,failure]
 delivery=B+'/git_delivery.json'
 save(delivery,dict(schema='formal_main_v2',utc=datetime.now(timezone.utc).isoformat(),status='all_required_index_and_exact_archive_verified',baseline=HEAD,required_files=req,index_guard=ref(guard),guard_inherited_after_exact_unchanged_index_verification=True,frozen_index_and_worktree_files=173,new_raw_restored=3,new_raw_bytes=169428644,previous_archives_unchanged=True,weights_added=False,excluded_live_files=['results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_0530_delivery_resume.jsonl'],raw_whitespace_exceptions=[ref(n) for n in exceptions],root_independent_complete=60,root_accepted_updates=305000,new_root_GPU_submissions=['3046779','3046798'],exact_pending_reconciled_without_resubmission=True,Long128seed41_development_terminal_accepted=True,Long256seed17_seed23_development_submitted=True,exact_downstream_reservation_consumed=True,new_development_trials=200,all_development_trials=1612,current_action_trials=400,unique_initial_states_across_seed23_and41=100,final_sealed=True,no_normal_GPU_realtime_polling=True,bounded_delivery_correction=ref(fix),additions=[ref(n) for n in additions]))
 for n in additions+[delivery]:
  git('add','--',n);assert git('show',':'+n).stdout==(R/n).read_bytes()
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 assert set(git('diff','--cached','--name-only').stdout.decode().splitlines())==expected|set(additions)|{delivery}
 answer=git('commit','-m','Accept Goal128 seed41 and Long development; fill two GPU slots')
 commit=git('rev-parse','HEAD').stdout.decode().strip();count=len(expected|set(additions)|{delivery})
 save('.local/git_commit_0530.json',dict(commit=commit,baseline=HEAD,files=count,index_guard='passed_original_plus_exact_index_reverification',root_complete=60,new_development_trials=200))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=commit,files=count,archive_bytes=169428644,raw_whitespace_exceptions=2,summary=answer.stdout.decode().splitlines()[:2])),flush=True)

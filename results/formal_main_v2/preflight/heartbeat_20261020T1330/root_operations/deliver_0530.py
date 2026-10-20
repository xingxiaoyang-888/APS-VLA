from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,importlib.util,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1330'
E='results/formal_main_v2/engineering/supervision_delivery_0530'
HEAD='07535f5ff2989b0b6b9319d9f604a4ceceb71258'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/Goal128seed41_20261020_0530.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel):return json.loads((R/rel).read_bytes())
def ref(rel):return dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as stream:json.dump(x,stream,sort_keys=True,ensure_ascii=False,indent=2);stream.write('\n')
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('delivery0530ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 state=rd('results/experiment_supervisor/state.json');f=state['formal_main_progress']
 assert state['pending_submission'] is None and f['root_and_independent_completed_arms']==60 and f['root_and_independent_reviewed_arm_updates']==305000
 assert f['completed_development_trials']==1612 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert len([x for x in f['Long_remaining16_development_submissions'] if x['job_id']=='3045322' and x['completed_trials_accepted']==200])==1
 assert {x['job_id'] for x in f['Long_remaining16_development_submissions']}=={'3045322','3046779','3046798'}
 assert f['current_action_development_trial_count']==400 and f['current_action_development_unique_initial_states']==100
 assert state['autonomous_training_v1']['reserved_GPU_slots']==0
 assert h(R/SNAP)=='623fadb557bf0231a1c1c83adeaad007cf19f10f51c6cbd6a914173f3f17e79a'
 assert h(R/B/'Goal3039988_archive_inputs.json')=='3354529c3f99c3837f96dec9c1fe29ba11b848bcc3fe0882eb54b8eda3326065'
 raws=rd(B+'/Goal3039988_archive_inputs.json')['raw'];raw_names={x['path'] for x in raws}
 assert len(raws)==3 and sum(x['bytes'] for x in raws)==169428644
 for row in raws:assert ref(row['path'])==row
 ignore=R/'.gitignore';prior=ignore.read_text();adds=[]
 for p in sorted((R/E).rglob('*.log')):
  assert p.is_file() and not p.is_symlink();line='!/'+p.relative_to(R).as_posix()
  if line not in prior.splitlines():adds.append(line)
 for name in sorted(raw_names):
  if '/'+name not in prior.splitlines():adds.append('/'+name)
 if adds:ignore.write_text(prior+'\n# Exact lossless Goal128 seed41 terminal raw and audited logs,20261020T1330.\n'+'\n'.join(adds)+'\n')
 source=B+'/root_operations/deliver_0530.py'
 with (R/source).open('xb') as stream:stream.write(Path(__file__).read_bytes())
 exact={'.gitignore','results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl',
 'results/formal_main_v2/invocations/libero_10_development_5185766bb353c8e6_attempt01.json',
 'results/formal_main_v2/invocations/libero_10_development_b0a59115666b5afa_attempt01.json',
 'results/formal_main_v2/downstream_reviews/3045322.json','results/formal_main_v2/downstream_reviews/3045322_independent.json',
 'results/formal_main_v2/job_receipts/3039988.json','results/formal_main_v2/submissions/3046779.json','results/formal_main_v2/submissions/3046798.json','results/slurm/cti-formal_3039988.out','results/slurm/cti-formal_3039988.err'}
 exact.update('docs/'+n+'.md' for n in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式Long其余16选择器开发登记','正式Long128种子41开发结果'])
 raw_long=rd('results/formal_main_v2/downstream_reviews/3045322.json')['files']
 for name,pin in raw_long.items():assert h(R/name)==pin
 exact.update(raw_long)
 prefixes=[B+'/',E+'/','results/formal_main_v2/libero_goal/k128/seed41/training/','results/formal_main_v2/pulls/20261020T052651Z_c8bc72a2008d/','results/formal_main_v2/pulls/20261020T053844Z_7c37a0aebf20/',
 'results/formal_main_v2/nonweight_archives/v1/','results/formal_main_v2/autonomous_training/run_v1/reviews/libero_goal_k128_seed41_58ebbd39960c4d4ea47d0b290a545149/',
 'results/formal_main_v2/downstream_gateway/035d49cc3acd52f713f4bcead2d01e5055a76a31776223d8fb6c878d25a901f8/',
 'results/formal_main_v2/downstream_gateway/e436e498db113a851dfdab2e9a23ef3313d599d02278705261926413ddebe909/']
 selected=[];excluded=[]
 for row in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split('\0'):
  if not row:continue
  status,name=row[:2],row[3:];assert status in (' M','??'),row
  accept=name in exact or any(name.startswith(p) for p in prefixes)
  if name.startswith('results/formal_main_v2/control_transport/'):
   lines=(R/name).read_text().splitlines();accept=bool(lines) and json.loads(lines[-1]).get('event')=='control_end'
  if accept:
   p=R/name;assert name not in raw_names and p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20),name
   assert p.suffix not in ('.pt','.pth','.ckpt','.bin','.safetensors','.pyc','.init','.npz','.npy','.h5','.hdf5'),name
   selected.append(name)
  else:excluded.append(name)
 assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_0530_delivery.jsonl'},excluded
 assert all(p.relative_to(R).as_posix() in selected for p in (R/E).rglob('*') if p.is_file()),'archive evidence ignored or unlisted'
 for i in range(0,len(selected),60):git('add','--',*selected[i:i+60])
 required=dict(schema='cti_nonweight_archive_stage_v1',kind='required_files',files=[ref(n) for n in sorted(selected)])
 save(B+'/git_required_files.json',required);git('add','--',B+'/git_required_files.json')
 checker=R/'scripts/ops/check_nonweight_archive_stage.py';assert h(checker)=='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6'
 argv=[sys.executable,'-B',str(checker),'--project-root',str(R),'--snapshot',SNAP,'--snapshot-sha256',h(R/SNAP),'--required-files',B+'/git_required_files.json']
 for n in sorted(raw_names):argv.extend(['--raw-path',n])
 result=subprocess.run(argv,cwd=R,capture_output=True)
 for n,raw in [('git_index_guard.stdout.json',result.stdout),('git_index_guard.stderr.txt',result.stderr)]:
  with (R/B/n).open('xb') as stream:stream.write(raw)
 assert result.returncode==0,result.stderr.decode()
 guard=json.loads(result.stdout);assert guard['status']=='verified_index_archive_delivery' and guard['frozen_files_verified_in_worktree_and_index']==173
 assert {x['path'] for x in guard['raw_paths_restored_exactly']}==raw_names and sum(x['bytes'] for x in guard['raw_paths_restored_exactly'])==169428644
 diag=git('diff','--cached','--check',check=False)
 save(B+'/git_whitespace_diagnostic.json',dict(returncode=diag.returncode,stdout=diag.stdout.decode(),stderr=diag.stderr.decode()))
 exceptions=[]
 if diag.returncode:
  headers=[line for line in diag.stdout.decode().splitlines() if re.match(r'^.*?:[0-9]+: ',line)]
  assert headers and not diag.stderr
  for header in headers:
   m=re.fullmatch(r'(.*?):[0-9]+: (trailing whitespace|new blank line at EOF)\.',header);assert m,header
   name=m.group(1);assert name.startswith(E+'/') and name.endswith(('.patch','.diff','.log','.txt','.stdout','.stderr')) or name in ['results/slurm/cti-formal_3039988.out','results/slurm/cti-formal_3039988.err','results/slurm/cti-formal-downstream_3045322.out','results/slurm/cti-formal-downstream_3045322.err'],name
   exceptions.append(name)
  exceptions=sorted(set(exceptions))
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 for row in required['files']:
  raw=git('show',':'+row['path']).stdout;assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
 for name,pin in raw_long.items():assert hashlib.sha256(git('show',':'+name).stdout).hexdigest()==pin
 additions=[B+'/git_index_guard.stdout.json',B+'/git_index_guard.stderr.txt',B+'/git_whitespace_diagnostic.json']
 save(B+'/git_delivery.json',dict(schema='formal_main_v2',utc=datetime.now(timezone.utc).isoformat(),status='all_required_index_and_exact_archive_verified',baseline=HEAD,required_files=B+'/git_required_files.json',index_guard=ref(B+'/git_index_guard.stdout.json'),frozen_index_and_worktree_files=173,new_raw_restored=3,new_raw_bytes=169428644,previous_archives_unchanged=True,weights_added=False,excluded_live_files=excluded,raw_whitespace_exceptions=[ref(n) for n in exceptions],root_independent_complete=60,root_accepted_updates=305000,new_root_GPU_submissions=['3046779','3046798'],exact_pending_reconciled_without_resubmission=True,Long128seed41_development_terminal_accepted=True,Long256seed17_seed23_development_submitted=True,exact_downstream_reservation_consumed=True,new_development_trials=200,all_development_trials=1612,current_action_trials=400,unique_initial_states_across_seed23_and41=100,final_sealed=True,no_normal_GPU_realtime_polling=True,additions=[ref(n) for n in additions]))
 for n in additions+[B+'/git_delivery.json']:
  git('add','--',n);assert git('show',':'+n).stdout==(R/n).read_bytes()
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines())
 answer=git('commit','-m','Accept Goal128 seed41 and Long development; fill two GPU slots')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_0530.json',dict(commit=commit,baseline=HEAD,files=count,index_guard='passed',root_complete=60,new_development_trials=200))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=commit,files=count,archive_bytes=169428644,raw_whitespace_exceptions=len(exceptions),summary=answer.stdout.decode().splitlines()[:2])),flush=True)


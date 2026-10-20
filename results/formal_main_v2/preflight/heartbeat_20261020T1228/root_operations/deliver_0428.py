from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,importlib.util,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1228'
E='results/formal_main_v2/engineering/supervision_delivery_0428'
HEAD='27b0811dbad4179e49d65f816abed94ebc7e8945'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/Goal128seed23_20261020_0428.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel):return json.loads((R/rel).read_bytes())
def ref(rel):return dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as stream:json.dump(x,stream,sort_keys=True,ensure_ascii=False,indent=2);stream.write('\n')
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('delivery0428ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 state=rd('results/experiment_supervisor/state.json');f=state['formal_main_progress']
 assert state['pending_submission'] is None and f['root_and_independent_completed_arms']==58 and f['root_and_independent_reviewed_arm_updates']==296000
 assert f['completed_development_trials']==1412 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert len([x for x in f['Long_remaining16_development_submissions'] if x['job_id']=='3045322'])==1
 assert state['autonomous_training_v1']['reserved_GPU_slots']==0
 assert h(R/SNAP)=='73d1d12fb98124ae2f20e71374b381a3fb96f8a5f02f4a7a55cba138b6fea355'
 assert h(R/B/'Goal3039981_archive_inputs.json')=='c4db57dadd2dffc406d099623d8777ef00942198376333772738b97372e97e4a'
 raws=rd(B+'/Goal3039981_archive_inputs.json')['raw'];raw_names={x['path'] for x in raws}
 assert len(raws)==3 and sum(x['bytes'] for x in raws)==149270140
 for row in raws:assert ref(row['path'])==row
 ignore=R/'.gitignore';prior=ignore.read_text();adds=[]
 for p in sorted((R/E).rglob('*.log')):
  assert p.is_file() and not p.is_symlink();line='!/'+p.relative_to(R).as_posix()
  if line not in prior.splitlines():adds.append(line)
 for name in sorted(raw_names):
  if '/'+name not in prior.splitlines():adds.append('/'+name)
 if adds:ignore.write_text(prior+'\n# Exact lossless Goal128 seed23 terminal raw and audited logs,20261020T1228.\n'+'\n'.join(adds)+'\n')
 source=B+'/root_operations/deliver_0428.py'
 with (R/source).open('xb') as stream:stream.write(Path(__file__).read_bytes())
 exact={'.gitignore','results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl',
 'results/formal_main_v2/invocations/libero_10_development_428eafaeb10a5ce3_attempt01.json',
 'results/formal_main_v2/job_receipts/3039981.json','results/formal_main_v2/submissions/3045322.json','results/slurm/cti-formal_3039981.out','results/slurm/cti-formal_3039981.err'}
 exact.update('docs/'+n+'.md' for n in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式Long其余16选择器开发登记'])
 prefixes=[B+'/',E+'/','results/formal_main_v2/libero_goal/k128/seed23/training/','results/formal_main_v2/pulls/20261020T035302Z_fd2d333ba251/',
 'results/formal_main_v2/nonweight_archives/v1/','results/formal_main_v2/autonomous_training/run_v1/reviews/libero_goal_k128_seed23_bc4cc1378dbe411f9c87fa166be78ef6/',
 'results/formal_main_v2/downstream_gateway/a2104c3cb1d96dd0d8ddd5bf9c0a9b2a19dc04d5cbf8e6fae8d69d9dea6b0730/']
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
 assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_0428_delivery.jsonl'},excluded
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
 assert {x['path'] for x in guard['raw_paths_restored_exactly']}==raw_names and sum(x['bytes'] for x in guard['raw_paths_restored_exactly'])==149270140
 diag=git('diff','--cached','--check',check=False)
 save(B+'/git_whitespace_diagnostic.json',dict(returncode=diag.returncode,stdout=diag.stdout.decode(),stderr=diag.stderr.decode()))
 exceptions=[]
 if diag.returncode:
  headers=[line for line in diag.stdout.decode().splitlines() if re.match(r'^.*?:[0-9]+: ',line)]
  assert headers and not diag.stderr
  for header in headers:
   m=re.fullmatch(r'(.*?):[0-9]+: (trailing whitespace|new blank line at EOF)\.',header);assert m,header
   name=m.group(1);assert name.startswith(E+'/') and name.endswith(('.patch','.diff','.log','.txt','.stdout','.stderr')) or name in ['results/slurm/cti-formal_3039981.out','results/slurm/cti-formal_3039981.err'],name
   exceptions.append(name)
  exceptions=sorted(set(exceptions))
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 for row in required['files']:
  raw=git('show',':'+row['path']).stdout;assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
 additions=[B+'/git_index_guard.stdout.json',B+'/git_index_guard.stderr.txt',B+'/git_whitespace_diagnostic.json']
 save(B+'/git_delivery.json',dict(schema='formal_main_v2',utc=datetime.now(timezone.utc).isoformat(),status='all_required_index_and_exact_archive_verified',baseline=HEAD,required_files=B+'/git_required_files.json',index_guard=ref(B+'/git_index_guard.stdout.json'),frozen_index_and_worktree_files=173,new_raw_restored=3,new_raw_bytes=149270140,previous_archives_unchanged=True,weights_added=False,excluded_live_files=excluded,raw_whitespace_exceptions=[ref(n) for n in exceptions],root_independent_complete=58,root_accepted_updates=296000,new_root_GPU_submissions=['3045322'],exact_pending_reconciled_without_resubmission=True,Long128seed41_development_submitted=True,exact_downstream_reservation_consumed=True,new_development_trials=0,final_sealed=True,no_normal_GPU_realtime_polling=True,additions=[ref(n) for n in additions]))
 for n in additions+[B+'/git_delivery.json']:
  git('add','--',n);assert git('show',':'+n).stdout==(R/n).read_bytes()
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines())
 answer=git('commit','-m','Accept Goal128 seed23 and start Long128 seed41 development')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_0428.json',dict(commit=commit,baseline=HEAD,files=count,index_guard='passed',root_complete=58,new_development_trials=0))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=commit,files=count,archive_bytes=149270140,raw_whitespace_exceptions=len(exceptions),summary=answer.stdout.decode().splitlines()[:2])),flush=True)

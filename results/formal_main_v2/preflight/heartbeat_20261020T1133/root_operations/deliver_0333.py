from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,importlib.util,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1133'
E='results/formal_main_v2/engineering/supervision_delivery_0333'
HEAD='adae7ccc6ed7f7faece36f1a0c742cd1946f91cd'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/Goal256seed41_20261020_0333.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel):return json.loads((R/rel).read_bytes())
def ref(rel):return dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as stream:json.dump(x,stream,sort_keys=True,ensure_ascii=False,indent=2);stream.write('\n')
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('delivery0333ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 state=rd('results/experiment_supervisor/state.json');f=state['formal_main_progress']
 assert state['pending_submission'] is None and f['root_and_independent_completed_arms']==56 and f['root_and_independent_reviewed_arm_updates']==288000
 assert f['completed_development_trials']==1412 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert f['spatial64seed23_continuous_v2_ready']['job_id']=='3044479' and f['spatial64seed23_continuous_v2_ready']['GPU_submitted'] is True
 assert f['object64seed23_continuous_ready']['GPU_submitted'] is True and f['object64seed23_continuous_ready']['job_id']=='3044844'
 assert h(R/SNAP)=='cc31b32b83a186989f291c672f09a64467b2f0448020b4a9ea57e8ca9ee524da'
 assert h(R/B/'Goal3038735_archive_inputs.json')=='4bfab506b25b49184336eab27f1ae40a44434235e1f58c51c27cb66fc9584a2d'
 raws=rd(B+'/Goal3038735_archive_inputs.json')['raw'];raw_names={x['path'] for x in raws}
 assert len(raws)==3 and sum(x['bytes'] for x in raws)==182651083
 for row in raws:assert ref(row['path'])==row
 ignore=R/'.gitignore';prior=ignore.read_text();adds=[]
 for p in sorted((R/E).rglob('*.log')):
  assert p.is_file() and not p.is_symlink();line='!/'+p.relative_to(R).as_posix()
  if line not in prior.splitlines():adds.append(line)
 for name in sorted(raw_names):
  if '/'+name not in prior.splitlines():adds.append('/'+name)
 if adds:ignore.write_text(prior+'\n# Exact lossless Goal256 seed41 terminal raw and audited logs,20261020T1133.\n'+'\n'.join(adds)+'\n')
 source=B+'/root_operations/deliver_0333.py'
 with (R/source).open('xb') as stream:stream.write(Path(__file__).read_bytes())
 exact={'.gitignore','results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl',
 'results/formal_main_v2/invocations/libero_object_train_k64_seed23_attempt03.json',
 'results/formal_main_v2/job_receipts/3038735.json','results/formal_main_v2/submissions/3044844.json','results/slurm/cti-formal_3038735.out','results/slurm/cti-formal_3038735.err'}
 exact.update('docs/'+n+'.md' for n in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记'])
 prefixes=[B+'/',E+'/','results/formal_main_v2/libero_goal/k256/seed41/training/','results/formal_main_v2/pulls/20261020T033606Z_926f09617fd7/',
 'results/formal_main_v2/nonweight_archives/v1/','results/formal_main_v2/autonomous_training/run_v1/reviews/libero_goal_k256_seed41_7716da45646f4c7dacb6d6a69f8ab3d2/',
 'results/formal_main_v2/continuous_admissions/3044017/6619bd4e9a8e75b76200bca401a861bc5c6c1180a54c37cf739da18f55ea019c/']
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
 assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_0333_delivery.jsonl'},excluded
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
 assert {x['path'] for x in guard['raw_paths_restored_exactly']}==raw_names and sum(x['bytes'] for x in guard['raw_paths_restored_exactly'])==182651083
 diag=git('diff','--cached','--check',check=False)
 save(B+'/git_whitespace_diagnostic.json',dict(returncode=diag.returncode,stdout=diag.stdout.decode(),stderr=diag.stderr.decode()))
 exceptions=[]
 if diag.returncode:
  headers=[line for line in diag.stdout.decode().splitlines() if re.match(r'^.*?:[0-9]+: ',line)]
  assert headers and not diag.stderr
  for header in headers:
   m=re.fullmatch(r'(.*?):[0-9]+: (trailing whitespace|new blank line at EOF)\.',header);assert m,header
   name=m.group(1);assert name.startswith(E+'/') and name.endswith(('.patch','.diff','.log','.txt','.stdout','.stderr')) or name in ['results/slurm/cti-formal_3038735.out','results/slurm/cti-formal_3038735.err'],name
   exceptions.append(name)
  exceptions=sorted(set(exceptions))
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 for row in required['files']:
  raw=git('show',':'+row['path']).stdout;assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
 additions=[B+'/git_index_guard.stdout.json',B+'/git_index_guard.stderr.txt',B+'/git_whitespace_diagnostic.json']
 save(B+'/git_delivery.json',dict(schema='formal_main_v2',utc=datetime.now(timezone.utc).isoformat(),status='all_required_index_and_exact_archive_verified',baseline=HEAD,required_files=B+'/git_required_files.json',index_guard=ref(B+'/git_index_guard.stdout.json'),frozen_index_and_worktree_files=173,new_raw_restored=3,new_raw_bytes=182651083,previous_archives_unchanged=True,weights_added=False,excluded_live_files=excluded,raw_whitespace_exceptions=[ref(n) for n in exceptions],root_independent_complete=56,root_accepted_updates=288000,new_root_GPU_submissions=['3044844'],exact_pending_reconciled_without_resubmission=True,Object64_prior_original500_accepted=True,Object64_continuous_submitted=True,new_development_trials=0,final_sealed=True,no_normal_GPU_realtime_polling=True,additions=[ref(n) for n in additions]))
 for n in additions+[B+'/git_delivery.json']:
  git('add','--',n);assert git('show',':'+n).stdout==(R/n).read_bytes()
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines())
 answer=git('commit','-m','Accept Goal256 seed41 and refill Object64 continuation')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_0333.json',dict(commit=commit,baseline=HEAD,files=count,index_guard='passed',root_complete=56,new_development_trials=0))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=commit,files=count,archive_bytes=182651083,raw_whitespace_exceptions=len(exceptions),summary=answer.stdout.decode().splitlines()[:2])),flush=True)

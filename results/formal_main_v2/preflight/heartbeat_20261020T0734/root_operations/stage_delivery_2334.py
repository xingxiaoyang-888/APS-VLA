from pathlib import Path
import hashlib,json,subprocess,sys,importlib.util,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T0734';E='results/formal_main_v2/engineering/supervision_delivery_2334'
HEAD='e032fbde99a84d9b947142b3f6839bba661d3db1'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/Goal256seed17_20261020_2334.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel):return json.loads((R/rel).read_bytes())
def save(rel,value):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(value,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('git2334ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 state=read('results/experiment_supervisor/state.json');f=state['formal_main_progress']
 assert state['pending_submission'] is None and f['root_and_independent_completed_arms']==52
 assert f['root_and_independent_reviewed_arm_updates']==267000 and f['completed_development_trials']==1412
 assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert h(R/SNAP)=='9bfaa25a6c1a1a51463da544089596e386ef31f86f568d96d3a3ac6577e97cce'
 assert h(R/B/'Goal3037543_archive_inputs.json')=='5c7ad3cc73b259e6d813540960ee2a1daec42313ff9ea4bd30c92d44023ccfa8'
 raws=read(B+'/Goal3037543_archive_inputs.json')['raw'];assert len(raws)==3 and sum(x['bytes'] for x in raws)==181404060
 for row in raws:assert h(R/row['path'])==row['sha256'] and (R/row['path']).stat().st_size==row['bytes']
 raw_names={x['path'] for x in raws}
 ignore=R/'.gitignore';prior=ignore.read_text();additions=[]
 for p in sorted((R/E).rglob('*.log')):
  assert p.is_file() and not p.is_symlink();line='!/'+p.relative_to(R).as_posix()
  if line not in prior.splitlines():additions.append(line)
 for name in sorted(raw_names):
  if '/'+name not in prior.splitlines():additions.append('/'+name)
 if additions:ignore.write_text(prior+'\n# Exact lossless Goal256 seed17 raw archive,20261020T0734.\n'+'\n'.join(additions)+'\n')
 op=R/B/'root_operations/stage_delivery_2334.py'
 with op.open('xb') as stream:stream.write(Path(__file__).read_bytes())
 exact={'.gitignore','results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl',
 'results/formal_main_v2/invocations/libero_goal_train_k64_seed41_attempt01.json','results/formal_main_v2/job_receipts/3037543.json',
 'results/slurm/cti-formal_3037543.out','results/slurm/cti-formal_3037543.err'}
 exact.update('docs/'+n+'.md' for n in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记'])
 prefixes=[B+'/',E+'/','results/formal_main_v2/libero_goal/k256/seed17/training/',
 'results/formal_main_v2/pulls/20261019T230639Z_3d90310410f1/',
 'results/formal_main_v2/autonomous_training/run_v1/reviews/libero_goal_k256_seed17_cf4a56b91c1f4dacb898ff24fc7c29b9/',
 'results/formal_main_v2/autonomous_training/run_v1/reviews/libero_goal_k64_seed41_bc31ce4403814aa4a044dc228051cbe2/',
 'results/formal_main_v2/nonweight_archives/v1/']
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
 assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_2334_stage_delivery.jsonl'},excluded
 for i in range(0,len(selected),60):git('add','--',*selected[i:i+60])
 required=dict(schema='cti_nonweight_archive_stage_v1',kind='required_files',files=[dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size) for n in sorted(selected)])
 save(B+'/git_required_files.json',required);git('add','--',B+'/git_required_files.json')
 checker=R/'scripts/ops/check_nonweight_archive_stage.py';assert h(checker)=='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6'
 argv=[sys.executable,'-B',str(checker),'--project-root',str(R),'--snapshot',SNAP,'--snapshot-sha256',h(R/SNAP),'--required-files',B+'/git_required_files.json']
 for name in sorted(raw_names):argv.extend(['--raw-path',name])
 result=subprocess.run(argv,cwd=R,capture_output=True)
 for name,raw in [('git_index_guard.stdout.json',result.stdout),('git_index_guard.stderr.txt',result.stderr)]:
  with (R/B/name).open('xb') as stream:stream.write(raw)
 assert result.returncode==0,result.stderr.decode()
 v=json.loads(result.stdout);assert v['status']=='verified_index_archive_delivery' and v['frozen_files_verified_in_worktree_and_index']==173
 assert {x['path'] for x in v['raw_paths_restored_exactly']}==raw_names
 diag=git('diff','--cached','--check',check=False);save(B+'/git_whitespace_diagnostic.json',dict(returncode=diag.returncode,stdout=diag.stdout.decode(),stderr=diag.stderr.decode()))
 exceptions=[]
 if diag.returncode:
  headers=[line for line in diag.stdout.decode().splitlines() if re.match(r'^.*?:[0-9]+: ',line)]
  assert headers and not diag.stderr
  for header in headers:
   match=re.fullmatch(r'(.*?):[0-9]+: (trailing whitespace|new blank line at EOF)\.',header);assert match,header
   name=match.group(1)
   assert name.startswith(E+'/') and name.endswith(('.diff','.log','.txt')) or name.startswith('results/slurm/'),name
   exceptions.append(name)
  exceptions=sorted(set(exceptions))
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 save(B+'/git_index_delivery.json',dict(schema='formal_main_v2',status='all_required_index_and_incremental_archive_verified',baseline=HEAD,required_files=B+'/git_required_files.json',index_guard=dict(path=B+'/git_index_guard.stdout.json',sha256=h(R/B/'git_index_guard.stdout.json')),frozen_index_and_worktree_files=173,new_raw_restored=3,new_raw_bytes=181404060,previous_archives_unchanged=True,weights_added=False,excluded_live_files=excluded,raw_whitespace_exceptions=[dict(path=n,sha256=h(R/n)) for n in exceptions],root_independent_complete=52,new_GPU_submissions_by_root=[],new_development_trials=0))
 print(json.dumps(dict(status='staged_and_index_checked',files=len(selected)+1,raw_restored_bytes=181404060,whitespace_exception_count=len(exceptions),ready_for_final_commit=True)),flush=True)

from pathlib import Path
import hashlib,json,subprocess,sys,importlib.util,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T0833';E='results/formal_main_v2/engineering/supervision_delivery_0033'
HEAD='532ec5c0696c7613f45a52a9389c0d1a25a6cd60'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/Goal256seed23_20261020_0033.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel):return json.loads((R/rel).read_bytes())
def save(rel,value):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(value,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('git0033ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 state=read('results/experiment_supervisor/state.json');f=state['formal_main_progress']
 assert state['pending_submission'] is None and f['root_and_independent_completed_arms']==54
 assert f['root_and_independent_reviewed_arm_updates']==277000 and f['completed_development_trials']==1412
 assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert h(R/SNAP)=='0c9c27f3a7a3d5fdcc8c098e97c8ab195b397899faca775f0556116f696b8d9a'
 assert h(R/B/'Goal3037821_archive_inputs.json')=='00fa1f9e5a0314f4d97dc9788a639bff51c4640e35742f02f472ba8948031349'
 raws=read(B+'/Goal3037821_archive_inputs.json')['raw'];assert len(raws)==3 and sum(x['bytes'] for x in raws)==178950489
 for row in raws:assert h(R/row['path'])==row['sha256'] and (R/row['path']).stat().st_size==row['bytes']
 raw_names={x['path'] for x in raws}
 ignore=R/'.gitignore';prior=ignore.read_text();additions=[]
 for p in sorted((R/E).rglob('*.log')):
  assert p.is_file() and not p.is_symlink();line='!/'+p.relative_to(R).as_posix()
  if line not in prior.splitlines():additions.append(line)
 for name in sorted(raw_names):
  if '/'+name not in prior.splitlines():additions.append('/'+name)
 if additions:ignore.write_text(prior+'\n# Exact lossless Goal256 seed23 raw archive,20261020T0833.\n'+'\n'.join(additions)+'\n')
 op=R/B/'root_operations/stage_delivery_0033.py'
 with op.open('xb') as stream:stream.write(Path(__file__).read_bytes())
 exact={'.gitignore','results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl',
 'results/formal_main_v2/invocations/libero_object_train_k64_seed23_attempt02.json','results/formal_main_v2/submissions/3044017.json','configs/experiments/formal_main_v2_spatial_cuda_continuous_3043399_v2.json','results/formal_main_v2/job_receipts/3037821.json',
 'results/slurm/cti-formal_3037821.out','results/slurm/cti-formal_3037821.err'}
 exact.update('docs/'+n+'.md' for n in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记'])
 prefixes=[B+'/',E+'/','results/formal_main_v2/libero_goal/k256/seed23/training/',
 'results/formal_main_v2/pulls/20261020T001210Z_d196b774c9dc/',
 'results/formal_main_v2/autonomous_training/run_v1/reviews/libero_goal_k256_seed23_9c597763f9244029af737cdec62ad9c5/',
 'results/formal_main_v2/nonweight_archives/v1/','scripts/ops/formal_spatial_cuda_continuous_admission_v2/','results/formal_main_v2/engineering/spatial_continuous_doc_binding_v2/','results/formal_main_v2/startup_recoveries/3028468/0f8c1eab2e196c544bbf1302d440085abf052bc0bbc32a6dc3d9377bcdb0aec0/']
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
 assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_0033_stage_delivery.jsonl','results/slurm/cti-formal_3044017.out','results/slurm/cti-formal_3044017.err'},excluded
 for i in range(0,len(selected),60):git('add','--',*selected[i:i+60])
 assert all(p.relative_to(R).as_posix() in selected for p in (R/E).rglob('*') if p.is_file()),'unlisted delivery evidence'
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
 save(B+'/git_index_delivery.json',dict(schema='formal_main_v2',status='all_required_index_and_incremental_archive_verified',baseline=HEAD,required_files=B+'/git_required_files.json',index_guard=dict(path=B+'/git_index_guard.stdout.json',sha256=h(R/B/'git_index_guard.stdout.json')),frozen_index_and_worktree_files=173,new_raw_restored=3,new_raw_bytes=178950489,previous_archives_unchanged=True,weights_added=False,excluded_live_files=excluded,raw_whitespace_exceptions=[dict(path=n,sha256=h(R/n)) for n in exceptions],root_independent_complete=54,new_GPU_submissions_by_root=['3044017'],new_development_trials=0))
 print(json.dumps(dict(status='staged_and_index_checked',files=len(selected)+1,raw_restored_bytes=178950489,whitespace_exception_count=len(exceptions),ready_for_final_commit=True)),flush=True)

from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,importlib.util,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T0530';E='results/formal_main_v2/engineering/supervision_delivery_2130'
HEAD='7d2c6c2173fd36bd8e9139493abb042818d516a6'
RAW='results/formal_main_v2/libero_object/k64/seed41/training/cache_events/3037535_ff11e398c517.jsonl'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/machine_training_object64seed41_20261020_2130.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel):return json.loads((R/rel).read_bytes())
def save(rel,value):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(value,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('git2130ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 state=read('results/experiment_supervisor/state.json');assert state['pending_submission'] is None and state['formal_main_progress']['root_and_independent_completed_arms']==48
 assert state['formal_main_progress']['root_and_independent_reviewed_arm_updates']==248000 and state['formal_main_progress']['completed_final_trials']==0 and not state['formal_main_progress']['test_opened']
 assert read(B+'/Spatial_continuous_root_admission.json')['status']=='approved_for_one_future_capacity_checked_submission'
 assert h(R/SNAP)=='3e42e2d5fc7f133cbbdf6c5c7bc1d2b5d7c0af3cf4d17f33ad4892171ece3ac7'
 assert h(R/RAW)=='accac0f01a63667ccf28bd6dec7909d28aa4d3c6c9643719f2e1f0fb5be8b9b8'
 ignore=R/'.gitignore';prior=ignore.read_text();additions=[]
 for p in sorted((R/E).rglob('*.log')):
  assert p.is_file() and not p.is_symlink();line='!/'+p.relative_to(R).as_posix()
  if line not in prior.splitlines():additions.append(line)
 if '/'+RAW not in prior.splitlines():additions.append('/'+RAW)
 if additions:ignore.write_text(prior+'\n# Exact server-only supervision archive paths, 20261020T0530.\n'+'\n'.join(additions)+'\n')
 op=R/B/'root_operations/stage_delivery_2130.py'
 with op.open('xb') as f:f.write(Path(__file__).read_bytes())
 exact={'.gitignore','results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl',
 'configs/experiments/formal_main_v2_spatial_cuda_continuous_3043399_v1.json','scripts/ops/formal_action_deployment_v1/README.md',
 'results/formal_main_v2/invocations/libero_10_development_ea4e52de3babd049_attempt01.json',
 'results/formal_main_v2/invocations/libero_goal_train_k64_seed17_attempt01.json',
 'results/formal_main_v2/job_receipts/3037535.json','results/formal_main_v2/job_receipts/3043399.json','results/formal_main_v2/submissions/3043709.json',
 'results/slurm/cti-formal_3037535.out','results/slurm/cti-formal_3037535.err','results/slurm/cti-formal_3043399.out','results/slurm/cti-formal_3043399.err'}
 exact.update('docs/'+n+'.md' for n in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式CUDA启动失败恢复登记','正式Long其余16选择器开发登记'])
 prefixes=[B+'/',E+'/', 'scripts/ops/formal_spatial_cuda_continuous_admission_v1/',
 'results/formal_main_v2/libero_spatial/k64/seed23/training/',
 'results/formal_main_v2/libero_object/k64/seed41/training/',
 'results/formal_main_v2/pulls/20261019T213629Z_4f95d3193797/',
 'results/formal_main_v2/pulls/20261019T215443Z_58826646465f/',
 'results/formal_main_v2/downstream_gateway/6e574361d66aaba7869b536082d9c605106bdaf2ec428f3ccb46ea986c8ef37a/',
 'results/formal_main_v2/autonomous_training/run_v1/reviews/libero_object_k64_seed41_64064d625c3c474eb751c78807b6946c/',
 'results/formal_main_v2/nonweight_archives/v1/']
 selected=[];excluded=[]
 for row in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split('\0'):
  if not row:continue
  status,name=row[:2],row[3:];assert status in (' M','??'),row
  accept=name in exact or any(name.startswith(p) for p in prefixes)
  if name.startswith('results/formal_main_v2/control_transport/'):
   lines=(R/name).read_text().splitlines();accept=bool(lines) and json.loads(lines[-1]).get('event')=='control_end'
  if accept:
   p=R/name;assert name!=RAW and p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20),name
   assert p.suffix not in ('.pt','.pth','.ckpt','.bin','.safetensors','.pyc','.init','.npz','.npy','.h5','.hdf5'),name
   selected.append(name)
  else:excluded.append(name)
 assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_2130_stage_delivery.jsonl'},excluded
 assert not git('diff','--','results/formal_main_v2/nonweight_archives/v1/snapshots/completed_training_20261020_1932_union29.json').stdout
 for i in range(0,len(selected),60):git('add','--',*selected[i:i+60])
 required=dict(schema='cti_nonweight_archive_stage_v1',kind='required_files',files=[dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size) for n in sorted(selected)])
 save(B+'/git_required_files.json',required);git('add','--',B+'/git_required_files.json')
 checker=R/'scripts/ops/check_nonweight_archive_stage.py';assert h(checker)=='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6'
 argv=[sys.executable,'-B',str(checker),'--project-root',str(R),'--snapshot',SNAP,'--snapshot-sha256',h(R/SNAP),'--raw-path',RAW,'--required-files',B+'/git_required_files.json']
 result=subprocess.run(argv,cwd=R,capture_output=True)
 for n,raw in [('git_index_guard.stdout.json',result.stdout),('git_index_guard.stderr.txt',result.stderr)]:
  with (R/B/n).open('xb') as f:f.write(raw)
 assert result.returncode==0,result.stderr.decode()
 v=json.loads(result.stdout);assert v['status']=='verified_index_archive_delivery' and v['frozen_files_verified_in_worktree_and_index']==173 and len(v['raw_paths_restored_exactly'])==1 and v['raw_paths_restored_exactly'][0]['path']==RAW
 diag=git('diff','--cached','--check',check=False);save(B+'/git_whitespace_diagnostic.json',dict(returncode=diag.returncode,stdout=diag.stdout.decode(),stderr=diag.stderr.decode()))
 exceptions=sorted(set(re.findall(r'^(.*?):[0-9]+: (?:trailing whitespace|new blank line at EOF)\.',diag.stdout.decode(),re.M)))
 # Preserve original raw bytes only, never excuse active code or documentation.
 if diag.returncode:
  headers=[line for line in diag.stdout.decode().splitlines() if re.match(r'^.*?:[0-9]+: ',line)]
  assert headers and not diag.stderr
  exceptions=[]
  for header in headers:
   match=re.fullmatch(r'(.*?):[0-9]+: (trailing whitespace|new blank line at EOF)\.',header);assert match,header
   name=match.group(1)
   assert name.startswith(E+'/') or name.startswith('results/slurm/') or name.startswith(B+'/') and (name.endswith(('.txt','.out','.err','.log','.diff'))),name
   exceptions.append(name)
  exceptions=sorted(set(exceptions))
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 save(B+'/git_index_delivery.json',dict(schema='formal_main_v2',status='all_required_index_and_incremental_archive_verified',baseline=HEAD,required_files=B+'/git_required_files.json',index_guard=dict(path=B+'/git_index_guard.stdout.json',sha256=h(R/B/'git_index_guard.stdout.json')),frozen_index_and_worktree_files=173,new_raw_restored=1,new_raw_bytes=132813168,previous_union29_unchanged=True,weights_added=False,excluded_live_files=excluded,raw_whitespace_exceptions=[dict(path=n,sha256=h(R/n)) for n in exceptions],machine_complete=50,root_independent_complete=48,pending_Object64seed41_root_independent_review=True,new_GPU_submissions_by_root=['3043709'],normal_controller_refill='3043762'))
 print(json.dumps(dict(status='staged_and_index_checked',files=len(selected)+1,raw_restored_bytes=132813168,whitespace_exception_count=len(exceptions),ready_for_final_commit=True)))

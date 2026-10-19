from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,importlib.util,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T0632';E='results/formal_main_v2/engineering/supervision_delivery_2232'
HEAD='c5caf2601e17c2cacd67d92166b8757e9301e078'
RAW='results/formal_main_v2/libero_10/downstream/development/ea4e52de3babd049/attempt01/trials.jsonl'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/Long_development3043709_20261020_2232.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel):return json.loads((R/rel).read_bytes())
def save(rel,value):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(value,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('git2232ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 state=read('results/experiment_supervisor/state.json');assert state['pending_submission'] is None and state['formal_main_progress']['root_and_independent_completed_arms']==50
 assert state['formal_main_progress']['root_and_independent_reviewed_arm_updates']==257000 and state['formal_main_progress']['completed_development_trials']==1412 and state['formal_main_progress']['completed_final_trials']==0 and not state['formal_main_progress']['test_opened']
 assert h(R/SNAP)=='f80012c6dbd3e7efa6f13ad3567255c5e1a05ef7081112a97cab26836a4cf98a'
 assert h(R/RAW)=='1c38e72abf36136fb0917788887df0096be9a4743144f0a3501c54bb2dbeffb2' and (R/RAW).stat().st_size==31699657
 mirrors=read(B+'/3043709_source_snapshot_mirror.json')['files'];assert len(mirrors)==173
 for row in mirrors:assert h(R/row['canonical_source'])==h(R/row['destination'])==row['sha256']
 save(B+'/source_snapshot_canonical_Git_delivery.json',dict(schema='formal_main_v2',status='same173_source_bytes_delivered_at_canonical_paths_with_exact_alias_reconstruction',original_actual_server_transport=dict(path=B+'/3043709_source_snapshot_mirror.json',sha256=h(R/B/'3043709_source_snapshot_mirror.json')),alias_files=mirrors,restorer=dict(path='scripts/ops/restore_formal_source_mirror_v1.py',sha256=h(R/'scripts/ops/restore_formal_source_mirror_v1.py')),reason='Existing index guard only admits state-handling/model Python at canonical top-level source paths. Preserve guard and deliver identical source bytes once, plus explicit alias map and reconstruction.',no_unique_source_bytes_omitted=True,all_original_mirrors_retained_on_server=True,guard_unchanged=True))
 ignore=R/'.gitignore';prior=ignore.read_text();additions=[]
 for p in sorted((R/E).rglob('*.log')):
  assert p.is_file() and not p.is_symlink();line='!/'+p.relative_to(R).as_posix()
  if line not in prior.splitlines():additions.append(line)
 for name in [RAW]+[row['destination'] for row in mirrors]:
  if '/'+name not in prior.splitlines():additions.append('/'+name)
 if additions:ignore.write_text(prior+'\n# Exact raw archive and byte-identical source aliases,20261020T0632.\n'+'\n'.join(additions)+'\n')
 doc=R/'docs/服务器工作区与GitHub同步.md';first,tail=doc.read_text().split('\n',1)
 doc.write_text(first+'\n\n2026-10-20：首次新动作开发终态复核补齐R/snapshots/formal_main_v2_run_564be0995e的173份精确源镜像；原S、canonical R与镜像SHA一致。Git保留canonical源的全部原字节、[精确路径映射](../'+B+'/source_snapshot_canonical_Git_delivery.json)和重建器，不重复提交同源目录。服务器Git克隆后，如需审核这些路径别名，可运行 python -B scripts/ops/restore_formal_source_mirror_v1.py --project-root <服务器仓库绝对路径>；它只重建已登记同SHA源码，已有不同内容即拒绝，无权重/封存值/Slurm/state访问。该重建不冒称新的原S核验，原实测传输证明保留。\n\n'+tail.lstrip('\n'))
 op=R/B/'root_operations/stage_delivery_2232.py'
 with op.open('xb') as f:f.write(Path(__file__).read_bytes())
 exact={'.gitignore','results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl','scripts/ops/formal_action_deployment_v1/README.md','scripts/ops/restore_formal_source_mirror_v1.py',
 'results/formal_main_v2/invocations/libero_goal_train_k64_seed23_attempt01.json','results/formal_main_v2/job_receipts/3043709.json',
 'results/formal_main_v2/downstream_reviews/3043709.json','results/formal_main_v2/downstream_reviews/3043709_independent.json',
 'results/formal_main_v2/libero_object/k64/seed41/training/segment_reviews/3037535.json','results/formal_main_v2/libero_object/k64/seed41/training/segment_reviews/3037535_independent.json',
 'results/slurm/cti-formal-downstream_3043709.out','results/slurm/cti-formal-downstream_3043709.err'}
 exact.update('docs/'+n+'.md' for n in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式Long其余16选择器开发登记','正式Long128种子23开发结果','服务器工作区与GitHub同步'])
 prefixes=[B+'/',E+'/', 'results/formal_main_v2/libero_10/downstream/development/ea4e52de3babd049/attempt01/',
 'results/formal_main_v2/pulls/20261019T223821Z_c4b67281fa45/',
 'results/formal_main_v2/autonomous_training/run_v1/reviews/libero_goal_k64_seed23_7952284951a848739419977df261253f/',
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
 assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_2232_stage_delivery.jsonl'},excluded
 for i in range(0,len(selected),60):git('add','--',*selected[i:i+60])
 required=dict(schema='cti_nonweight_archive_stage_v1',kind='required_files',files=[dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size) for n in sorted(selected)])
 save(B+'/git_required_files.json',required);git('add','--',B+'/git_required_files.json')
 checker=R/'scripts/ops/check_nonweight_archive_stage.py';assert h(checker)=='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6'
 argv=[sys.executable,'-B',str(checker),'--project-root',str(R),'--snapshot',SNAP,'--snapshot-sha256',h(R/SNAP),'--raw-path',RAW,'--required-files',B+'/git_required_files.json']
 result=subprocess.run(argv,cwd=R,capture_output=True)
 for name,raw in [('git_index_guard.stdout.json',result.stdout),('git_index_guard.stderr.txt',result.stderr)]:
  with (R/B/name).open('xb') as f:f.write(raw)
 assert result.returncode==0,result.stderr.decode()
 v=json.loads(result.stdout);assert v['status']=='verified_index_archive_delivery' and v['frozen_files_verified_in_worktree_and_index']==173 and len(v['raw_paths_restored_exactly'])==1 and v['raw_paths_restored_exactly'][0]['path']==RAW
 for row in mirrors:assert hashlib.sha256(git('show',':'+row['canonical_source']).stdout).hexdigest()==row['sha256']
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
 save(B+'/git_index_delivery.json',dict(schema='formal_main_v2',status='all_required_index_and_incremental_archive_verified',baseline=HEAD,required_files=B+'/git_required_files.json',index_guard=dict(path=B+'/git_index_guard.stdout.json',sha256=h(R/B/'git_index_guard.stdout.json')),frozen_index_and_worktree_files=173,source_aliases_reconstructible_from_exact_index_bytes=173,new_raw_restored=1,new_raw_bytes=31699657,previous_archives_unchanged=True,weights_added=False,excluded_live_files=excluded,raw_whitespace_exceptions=[dict(path=n,sha256=h(R/n)) for n in exceptions],root_independent_complete=50,new_GPU_submissions_by_root=[],new_development_trials=200))
 print(json.dumps(dict(status='staged_and_index_checked',files=len(selected)+1,raw_restored_bytes=31699657,whitespace_exception_count=len(exceptions),ready_for_final_commit=True)),flush=True)

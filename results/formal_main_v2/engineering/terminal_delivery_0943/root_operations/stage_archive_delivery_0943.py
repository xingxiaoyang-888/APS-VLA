from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261019T1743'
S='results/formal_main_v2/nonweight_archives/v1/snapshots/completed_training_20261019_0943_union23.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True);f.write('\n')
def git(*a):return subprocess.run(['git','-c','core.quotepath=false',*a],cwd=R,capture_output=True,check=True)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('stage0943controller',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()=='40aa74cf49662e2b375e3592a4af09d85a7be7b1'
 assert not git('diff','--cached','--name-only').stdout,'preexisting index edits'
 snap=json.loads((R/S).read_text());assert h(R/S)=='4af1f5375d8e79bf567aeb5e68e1b4ed28b52bce5dd77e6a65623e17be70abb2'
 raw={f['path'] for f in snap['files']}
 ignore=R/'.gitignore';text=ignore.read_text()
 additions=['/'+n for n in sorted(raw) if '/'+n not in text.splitlines()]
 log_scopes=['results/formal_main_v2/engineering/action_actual_plan_delivery_0943','results/formal_main_v2/engineering/terminal_delivery_0943',
  'results/formal_main_v2/autonomous_training/run_v1/reviews/libero_object_k256_seed41_50e454793c864814b422e8464af9dc1d']
 for prefix in log_scopes:
  for p in (R/prefix).rglob('*.log'):
   row='!/'+p.relative_to(R).as_posix()
   if row not in text.splitlines():additions.append(row)
 assert len([x for x in additions if not x.startswith('!')])==6
 ignore.write_text(text+'\n# Exact retained terminal raw and CPU audit logs for 20261019T0943 delivery.\n'+'\n'.join(additions)+'\n')
 source=R/'.local/stage_archive_delivery_0943.py';target=R/'results/formal_main_v2/engineering/terminal_delivery_0943/root_operations/stage_archive_delivery_0943.py'
 with target.open('xb') as f:f.write(source.read_bytes())
 write(B+'/integration_corrections.json',dict(schema='formal_main_v2',scientific_artifacts_changed=False,state_not_written_by_failed_attempts=True,
  retained_attempts=[
   dict(script='.local/integrate_terminal_and_spatial_0943.py',reason='Incorrect assumed candidate SHA equals finalized deployment SHA; frozen core writes training_complete metadata before best.pt serialization. Actual server best SHA, deployment metadata and independently recomputed min validation bind the selection.'),
   dict(script='.local/integrate_terminal_and_spatial_0943_v2.py',reason='Direct-only legacy root/independent fields omit7 already independently reviewed pairs stored in terminal_root_and_independent_review. v3 checks both SHA-bound receipt forms.')],
  successful_integration=dict(path='.local/integrate_terminal_and_spatial_0943_v3.py',sha256=h(R/'.local/integrate_terminal_and_spatial_0943_v3.py')),
  count_correction=dict(path=B+'/initial_observation_count_correction_v2.json',sha256=h(R/B/'initial_observation_count_correction_v2.json'))))
 logpath=R/'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out'
 n=logpath.stat().st_size
 with logpath.open('rb') as f:rawlog=f.read(n)
 assert len(rawlog)==n and n<10_000_000
 p=R/B/'controller_live_log_prefix.txt'
 with p.open('xb') as f:f.write(rawlog)
 write(B+'/controller_live_log_prefix_receipt.json',dict(source=str(logpath),captured_prefix_bytes=n,sha256=h(p),utc=datetime.now(timezone.utc).isoformat(),complete_at_initial_size_only=True,source_may_continue_appending=True))
 z=git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split('\0')
 rows=[(x[:2],x[3:]) for x in z if x]
 prefix_allow=[
 'results/formal_main_v2/engineering/action_actual_plan_delivery_0943/',
 'results/formal_main_v2/engineering/terminal_delivery_0943/',
 'results/formal_main_v2/execution/action_spatial_resume_0943/',B+'/',
 'results/formal_main_v2/nonweight_archives/v1/',
 'results/formal_main_v2/libero_object/k256/seed23/training/',
 'results/formal_main_v2/libero_object/k256/seed41/training/',
 'results/formal_main_v2/pulls/20261019T093213Z_d5c5ed4c402d/',
 'results/formal_main_v2/pulls/20261019T094848Z_786471d56a08/',
 'results/formal_main_v2/pulls/20261019T095542Z_e5d54e39d3ae/',
 'results/formal_main_v2/autonomous_training/run_v1/reviews/libero_object_k256_seed41_50e454793c864814b422e8464af9dc1d/']
 exact={'.gitignore','results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl'}
 exact|={'docs/'+n+'.md' for n in ['完整实验计划','实验进度','正式CUDA启动失败恢复登记','正式主实验规划','正式主实验阶段结论','正式动作执行入口接入记录','正式自动连续训练执行登记']}
 exact|={f'results/formal_main_v2/job_receipts/{j}.json' for j in ['3034570','3039258']}
 exact|={f'results/slurm/cti-formal_{j}.{ext}' for j in ['3034570','3039258'] for ext in ['out','err']}
 exact|={'results/formal_main_v2/invocations/libero_goal_train_k128_seed23_attempt03.json','results/formal_main_v2/invocations/libero_goal_train_k128_seed41_attempt02.json'}
 allowed=[];excluded=[]
 for status,name in rows:
  assert status in [' M','??'],'unexpected index or deletion status'
  accept=name in exact or any(name.startswith(p) for p in prefix_allow)
  if name.startswith('results/formal_main_v2/control_transport/'):
   events=(R/name).read_text().splitlines()
   accept=bool(events) and json.loads(events[-1]).get('event')=='control_end'
  if accept:
   assert name not in raw and (R/name).is_file() and not (R/name).is_symlink()
   assert (R/name).stat().st_size<100*(1<<20)
   allowed.append(name)
  else:excluded.append(name)
 required={'schema':'cti_nonweight_archive_stage_v1','kind':'required_files','files':[dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size) for n in sorted(allowed)]}
 write(B+'/git_required_files.json',required)
 allowed.append(B+'/git_required_files.json')
 for i in range(0,len(allowed),70):git('add','--',*allowed[i:i+70])
 checker=R/'scripts/ops/check_nonweight_archive_stage.py';assert h(checker)=='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6'
 argv=[sys.executable,'-B',str(checker),'--project-root',str(R),'--snapshot',S,'--snapshot-sha256',h(R/S),'--required-files',B+'/git_required_files.json']
 for n in sorted(raw):argv+=['--raw-path',n]
 print(json.dumps(dict(staged_files=len(allowed),excluded=excluded,guard_started=True)),flush=True)
 out=subprocess.run(argv,cwd=R,capture_output=True,text=True,timeout=300)
 for name,value in [('git_index_guard.stdout.json',out.stdout),('git_index_guard.stderr.txt',out.stderr)]:
  with (R/B/name).open('x') as f:f.write(value)
 assert out.returncode==0,out.stderr
 review=json.loads(out.stdout);assert review['status']=='verified_index_archive_delivery' and review['frozen_files_verified_in_worktree_and_index']==173
 write(B+'/git_stage_closed_receipt.json',dict(status='passed_index_guard_ready_to_commit',guard_stdout_sha256=h(R/B/'git_index_guard.stdout.json'),
  index_sha256=review['index_sha256'],staged_changes_sha256=review['staged_changes_sha256'],head=review['head'],
  required_files=B+'/git_required_files.json',excluded_live_or_current_transport=excluded,raw_files=23,raw_bytes=859375546))
 print(json.dumps(dict(status=review['status'],staged_files=len(allowed),raw_restored=len(review['raw_paths_restored_exactly']),index_files=review['index_files_checked_for_size_and_mode'])))

from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0332';HEAD='218e99cd2cec7eed0bf7c4cf1984e2b152bc9121'
S='results/formal_main_v2/nonweight_archives/v1/snapshots/completed_training_20261020_1932_union29.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
def git(*a,check=True):return subprocess.run(['git','-c','core.quotepath=false',*a],cwd=R,capture_output=True,check=check)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('commit1932ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 state=json.loads((R/'results/experiment_supervisor/state.json').read_text());assert state['pending_submission'] is None and state['formal_main_progress']['root_and_independent_completed_arms']==48
 assert state['autonomous_training_v1']['reserved_GPU_slots']==1
 assert state['autonomous_training_v1']['reservation_root_record']['sha256']=='2233de819653db5c84512902a61972aace9fa4adee787d860bbb8dbd47c865ee'
 oldstate=json.loads(git('show',HEAD+':results/experiment_supervisor/state.json').stdout);oldids={str(j['job_id']) for j in oldstate['registered_jobs']};newjobs=[j for j in state['registered_jobs'] if str(j['job_id']) not in oldids]
 assert [j['job_id'] for j in newjobs]==['3043399']
 snap=json.loads((R/S).read_text());assert len(snap['files'])==29;raw={x['path'] for x in snap['files']}
 ignore=R/'.gitignore';text=ignore.read_text();additions=['/'+n for n in sorted(raw) if '/'+n not in text.splitlines()];assert len(additions)==3
 scopes=[B,'results/formal_main_v2/engineering/terminal_delivery_1932','results/formal_main_v2/autonomous_training/run_v1/reviews/libero_object_k64_seed17_d4abd059ff114163a3be1e4c0e85868f']
 for prefix in scopes:
  for p in (R/prefix).rglob('*.log'):
   row='!/'+p.relative_to(R).as_posix()
   if row not in text.splitlines():additions.append(row)
 ignore.write_text(text+'\n# Exact terminal raw archives and retained audit logs for 20261020T0332.\n'+'\n'.join(additions)+'\n')
 with (R/B/'root_operations/commit_1932.py').open('xb') as f:f.write(Path(__file__).read_bytes())
 log=R/'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out';n=log.stat().st_size
 with log.open('rb') as f:data=f.read(n)
 assert len(data)==n and n<10000000
 with (R/B/'controller_log_prefix.txt').open('xb') as f:f.write(data)
 save(B+'/controller_log_prefix.json',dict(source=str(log),bytes=n,sha256=hashlib.sha256(data).hexdigest(),utc=datetime.now(timezone.utc).isoformat(),live_prefix_only=True))
 exact={'.gitignore','results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl'}
 exact|={'docs/'+name+'.md' for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式CUDA启动失败恢复登记','正式Long其余16选择器开发登记']}
 exact|={'results/formal_main_v2/job_receipts/3037054.json','results/slurm/cti-formal_3037054.out','results/slurm/cti-formal_3037054.err','results/formal_main_v2/submissions/3043399.json',newjobs[0]['invocation']}
 prefixes=[B+'/', 'results/formal_main_v2/engineering/terminal_delivery_1932/','results/formal_main_v2/nonweight_archives/v1/',
 'results/formal_main_v2/libero_object/k64/seed17/training/', 'results/formal_main_v2/pulls/20261019T190051Z_b73e8f8d7a36/',
 'results/formal_main_v2/autonomous_training/run_v1/reviews/libero_object_k64_seed17_d4abd059ff114163a3be1e4c0e85868f/',
 'results/formal_main_v2/startup_recoveries/3028522/7411a2e5e0d7e2123eea8bfea4c2bbaccb037d54b09697180340a597e3cfb18a/']
 allowed=[];excluded=[]
 for row in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split('\0'):
  if not row:continue
  status,name=row[:2],row[3:];assert status in (' M','??'),row
  accept=name in exact or any(name.startswith(x) for x in prefixes)
  if name.startswith('results/formal_main_v2/control_transport/'):
   events=(R/name).read_text().splitlines();accept=bool(events) and json.loads(events[-1]).get('event')=='control_end'
  if accept:
   p=R/name;assert name not in raw and p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20)
   assert p.suffix not in ('.pt','.pth','.ckpt','.safetensors','.pyc') and '__pycache__' not in p.parts
   if name.endswith('.py'):compile(p.read_bytes(),name,'exec')
   allowed.append(name)
  else:excluded.append(name)
 assert set(excluded)<= {'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_1932_commit.jsonl','results/slurm/cti-formal_3043399.out','results/slurm/cti-formal_3043399.err'},excluded
 required=dict(schema='cti_nonweight_archive_stage_v1',kind='required_files',files=[dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size) for n in sorted(allowed)])
 save(B+'/git_required_files.json',required);allowed.append(B+'/git_required_files.json')
 for i in range(0,len(allowed),60):git('add','--',*allowed[i:i+60])
 assert not git('diff','--cached','--name-only','--','configs','src','scripts','AGENTS.md').stdout
 checker=R/'scripts/ops/check_nonweight_archive_stage.py';assert h(checker)=='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6'
 argv=[sys.executable,'-B',str(checker),'--project-root',str(R),'--snapshot',S,'--snapshot-sha256',h(R/S),'--required-files',B+'/git_required_files.json']
 for n in sorted(raw):argv+=['--raw-path',n]
 print(json.dumps(dict(staged_files=len(allowed),new_registered_jobs=[j['job_id'] for j in newjobs],guard_started=True)),flush=True)
 out=subprocess.run(argv,cwd=R,capture_output=True,text=True,timeout=300)
 for name,value in [('git_index_guard.stdout.json',out.stdout),('git_index_guard.stderr.txt',out.stderr)]:
  with (R/B/name).open('x') as f:f.write(value)
 assert out.returncode==0,out.stderr
 check=json.loads(out.stdout);assert check['status']=='verified_index_archive_delivery' and check['frozen_files_verified_in_worktree_and_index']==173
 diagnostic=git('diff','--cached','--check',check=False);exceptions=[]
 if diagnostic.returncode:
  assert diagnostic.returncode==2 and not diagnostic.stderr
  for line in diagnostic.stdout.decode().splitlines():
   if line.endswith('trailing whitespace.') or line.endswith('new blank line at EOF.'):
    name=line.split(':',1)[0];assert name.endswith(('.log','.txt','.xml','.out','.err')) and any(name.startswith(x) for x in [B+'/', 'results/formal_main_v2/engineering/terminal_delivery_1932/', 'results/slurm/']),line;exceptions.append(name)
  assert exceptions
  git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in sorted(set(exceptions))])
 else:assert not diagnostic.stdout
 save(B+'/git_delivery.json',dict(schema='formal_main_v2',status='full_index_archive_verified_ready_to_commit',baseline=HEAD,required_files=B+'/git_required_files.json',index_guard=dict(path=B+'/git_index_guard.stdout.json',sha256=h(R/B/'git_index_guard.stdout.json')),frozen_index_and_worktree_files=173,raw_restored=len(check['raw_paths_restored_exactly']),raw_files=29,raw_bytes=sum(x['bytes'] for x in snap['files']),weights_added=False,excluded_live_files=excluded,preserved_raw_whitespace_files=sorted(set(exceptions)),raw_whitespace_check_stdout=diagnostic.stdout.decode(),normal_live_GPU_jobs_not_polled_for_commit=True))
 for n in [B+'/git_index_guard.stdout.json',B+'/git_index_guard.stderr.txt',B+'/git_delivery.json']:
  assert (R/n).stat().st_size<100*(1<<20);git('add','--',n);assert git('show',':'+n).stdout==(R/n).read_bytes()
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in sorted(set(exceptions))])
 result=git('commit','-m','Verify 48 training groups and resume the registered Spatial recovery')
 commit=git('rev-parse','HEAD').stdout.decode().strip();save('.local/git_commit_1932.json',dict(commit=commit,baseline=HEAD,files=len(allowed)+3,index_guard='passed'))
 print(json.dumps(dict(status='committed',commit=commit,files=len(allowed)+3,raw_restored=len(check['raw_paths_restored_exactly']),pushed=False,commit_summary=result.stdout.decode().splitlines()[:2])))

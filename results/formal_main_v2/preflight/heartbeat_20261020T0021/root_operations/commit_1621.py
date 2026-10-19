from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0021';HEAD='816a96bbcd8a4a7ee4daffa0da8062af727c10dd'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
def save(rel,v):
 with (R/rel).open('x') as f:json.dump(v,f,sort_keys=True,indent=2,ensure_ascii=False);f.write('\n')
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';spec=importlib.util.spec_from_file_location('commit1621ctl',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 s=json.loads((R/'results/experiment_supervisor/state.json').read_text());assert s['pending_submission'] is None and s['formal_main_progress']['root_and_independent_completed_arms']==46
 assert s['autonomous_training_v1']['reserved_GPU_slots']==1
 inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text())
 for name,pin in inventory['files'].items():assert h(R/name)==pin
 with (R/B/'root_operations/commit_1621.py').open('xb') as f:f.write(Path(__file__).read_bytes())
 log=R/'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out';size=log.stat().st_size
 with log.open('rb') as f:data=f.read(size)
 assert len(data)==size and size<10000000
 with (R/B/'controller_log_prefix.txt').open('xb') as f:f.write(data)
 save(B+'/controller_log_prefix.json',dict(source=str(log),bytes=size,sha256=hashlib.sha256(data).hexdigest(),utc=datetime.now(timezone.utc).isoformat(),live_prefix_only=True))
 ignore=R/'.gitignore';original=ignore.read_text();add=[]
 for p in (R/B).rglob('*.log'):
  line='!/'+p.relative_to(R).as_posix()
  if line not in original.splitlines():add.append(line)
 if add:ignore.write_text(original+'\n# Exact retained private CPU audit logs,20261020T0021.\n'+'\n'.join(sorted(add))+'\n')
 exact={'.gitignore','results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl','scripts/ops/formal_action_deployment_v1/README.md'}
 exact|={'docs/'+n+'.md' for n in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式CUDA启动失败恢复登记','正式动作执行入口接入记录']}
 allowed=[];excluded=[]
 failed_source=B+'/spatial_resume_independent/audit.py';failed_sha='13deeceb241c80fcd259cb8d6e2b73c5210042004b4ed89e11cbfa9037dabc9c';syntax_record=None
 for row in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split('\0'):
  if not row:continue
  status,name=row[:2],row[3:];assert status in (' M','??'),row
  accept=name.startswith(B+'/') or name in exact
  if name.startswith('results/formal_main_v2/control_transport/'):
   lines=(R/name).read_text().splitlines();accept=bool(lines) and json.loads(lines[-1]).get('event')=='control_end'
  if not accept:excluded.append(name);continue
  p=R/name;assert p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20)
  if name.endswith('.py'):
   if name==failed_source:
    assert h(p)==failed_sha
    try:compile(p.read_bytes(),name,'exec')
    except SyntaxError as error:syntax_record=dict(path=name,sha256=failed_sha,expected_retained_error=str(error),not_executable_production_source=True)
    else:raise ValueError('Expected original failed harness no longer matches failure')
   else:compile(p.read_bytes(),name,'exec')
  allowed.append(name)
 assert syntax_record is not None
 assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_1621_commit.jsonl'},excluded
 for i in range(0,len(allowed),50):git('add','--',*allowed[i:i+50])
 required=[]
 for name in sorted(allowed):
  raw=git('show',':'+name).stdout;assert hashlib.sha256(raw).hexdigest()==h(R/name);required.append(dict(path=name,sha256=h(R/name),bytes=len(raw)))
 for name,pin in inventory['files'].items():assert hashlib.sha256(git('show',':'+name).stdout).hexdigest()==pin
 scientific=git('diff','--cached','--name-only','--','configs','src','scripts','results/formal_main_v2/nonweight_archives/v1').stdout.decode().splitlines();assert scientific==['scripts/ops/formal_action_deployment_v1/README.md'],scientific
 diagnostic=git('diff','--cached','--check',check=False);exceptions=[]
 if diagnostic.returncode:
  assert diagnostic.returncode==2 and not diagnostic.stderr
  for line in diagnostic.stdout.decode().splitlines():
   if line.endswith('trailing whitespace.') or line.endswith('new blank line at EOF.'):
    name=line.split(':',1)[0];assert name.startswith(B+'/') and name.endswith(('.log','.txt','.xml','.out','.err'));exceptions.append(name)
  assert exceptions
  git('diff','--cached','--check','--','.',*[':(exclude)'+x for x in sorted(set(exceptions))])
 else:assert not diagnostic.stdout
 save(B+'/git_delivery.json',dict(schema='formal_main_v2',status='passed_incremental_index_review',baseline=HEAD,files=required,frozen_index_and_worktree_files=173,scientific_sources_and_configs_changed=False,raw_archives_unchanged=True,weights_added=False,retained_failed_harness=syntax_record,excluded_live_files=excluded,preserved_raw_whitespace_files=sorted(set(exceptions)),raw_whitespace_check_stdout=diagnostic.stdout.decode()))
 git('add','--',B+'/git_delivery.json')
 git('diff','--cached','--check','--','.',*[':(exclude)'+x for x in sorted(set(exceptions))])
 answer=git('commit','-m','Reserve audited Spatial recovery and retain bounded development resume preparation')
 commit=git('rev-parse','HEAD').stdout.decode().strip();save('.local/git_commit_1621.json',dict(commit=commit,baseline=HEAD,files=len(allowed)+1))
 print(json.dumps(dict(commit=commit,files=len(allowed)+1,pushed=False,summary=answer.stdout.decode().splitlines()[:2])))

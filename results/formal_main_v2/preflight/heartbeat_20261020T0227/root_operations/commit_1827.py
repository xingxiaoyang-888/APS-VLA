
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0227';HEAD='1ab222e5b26453bc648b7fff810cba801ea7cd2f'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
def save(rel,v):
 with (R/rel).open('x') as f:json.dump(v,f,sort_keys=True,indent=2,ensure_ascii=False);f.write('\n')
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('commit1827ctl',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 s=json.loads((R/'results/experiment_supervisor/state.json').read_text());assert s['pending_submission'] is None and s['formal_main_progress']['root_and_independent_completed_arms']==46 and s['autonomous_training_v1']['reserved_GPU_slots']==1
 inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text())
 for name,pin in inventory['files'].items():assert h(R/name)==pin
 with (R/B/'root_operations/commit_1827.py').open('xb') as f:f.write(Path(__file__).read_bytes())
 log=R/'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out';size=log.stat().st_size
 with log.open('rb') as f:data=f.read(size)
 assert len(data)==size and size<10000000
 with (R/B/'controller_log_prefix.txt').open('xb') as f:f.write(data)
 save(B+'/controller_log_prefix.json',dict(source=str(log),bytes=size,sha256=hashlib.sha256(data).hexdigest(),utc=datetime.now(timezone.utc).isoformat(),live_prefix_only=True))
 ignore=R/'.gitignore';original=ignore.read_text();add=[]
 for p in (R/B).rglob('*.log'):
  line='!/'+p.relative_to(R).as_posix()
  if line not in original.splitlines():add.append(line)
 if add:ignore.write_text(original+'\n# Exact retained CPU audit logs,20261020T0227.\n'+'\n'.join(sorted(add))+'\n')
 exact={'.gitignore','results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl','docs/正式Long其余16选择器开发登记.md'}
 exact|={'docs/'+n+'.md' for n in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式动作执行入口接入记录']}
 canonical=list((R/'results/formal_main_v2/execution/long_remaining16_action_v1_1827').rglob('*.json'));assert len(canonical)==80
 exact|={p.relative_to(R).as_posix() for p in canonical}
 exact.add('scripts/ops/formal_action_deployment_v1/README.md')
 allowed=[];excluded=[]
 for row in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split('\0'):
  if not row:continue
  status,name=row[:2],row[3:];assert status in (' M','??'),row
  accept=name.startswith(B+'/') or name in exact
  if name.startswith('results/formal_main_v2/control_transport/'):
   lines=(R/name).read_text().splitlines();accept=bool(lines) and json.loads(lines[-1]).get('event')=='control_end'
  if not accept:excluded.append(name);continue
  p=R/name;assert p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20)
  assert p.suffix not in ('.pt','.pth','.ckpt','.safetensors','.pyc') and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts
  if name.endswith('.py'):compile(p.read_bytes(),name,'exec')
  allowed.append(name)
 assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_1827_commit.jsonl'},excluded
 assert all(p.relative_to(R).as_posix() in allowed for p in (R/B).rglob('*') if p.is_file())
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
 save(B+'/git_delivery.json',dict(schema='formal_main_v2',status='passed_incremental_index_review',baseline=HEAD,files=required,frozen_index_and_worktree_files=173,scientific_sources_and_configs_changed=False,raw_archives_unchanged=True,weights_added=False,all_archived_python_compiles=True,CPU_failed_attempts_retained=True,excluded_live_files=excluded,preserved_raw_whitespace_files=sorted(set(exceptions)),raw_whitespace_check_stdout=diagnostic.stdout.decode()))
 git('add','--',B+'/git_delivery.json')
 git('diff','--cached','--check','--','.',*[':(exclude)'+x for x in sorted(set(exceptions))])
 answer=git('commit','-m','Admit eight Long development shards with exact runtime readiness')
 commit=git('rev-parse','HEAD').stdout.decode().strip();save('.local/git_commit_1827.json',dict(commit=commit,baseline=HEAD,files=len(allowed)+1))
 print(json.dumps(dict(commit=commit,files=len(allowed)+1,pushed=False,summary=answer.stdout.decode().splitlines()[:2])))

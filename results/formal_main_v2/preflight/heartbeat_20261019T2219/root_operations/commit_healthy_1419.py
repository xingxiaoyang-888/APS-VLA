from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261019T2219';HEAD='2485b118eabf6cf99ce5987d02e402a12231e8ca'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.run(['git','-c','core.quotepath=false',*a],cwd=R,capture_output=True,check=True)
def save(rel,v):
 with (R/rel).open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('commit1419',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD
 assert not git('diff','--cached','--name-only').stdout
 state=json.loads((R/'results/experiment_supervisor/state.json').read_text());assert state['pending_submission'] is None
 inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text())
 for rel,pin in inventory['files'].items():assert h(R/rel)==pin
 with (R/B/'root_operations/commit_healthy_1419.py').open('xb') as f:f.write(Path(__file__).read_bytes())
 log=R/'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out';size=log.stat().st_size
 with log.open('rb') as f:raw=f.read(size)
 assert len(raw)==size and size<10_000_000
 with (R/B/'controller_log_prefix.txt').open('xb') as f:f.write(raw)
 save(B+'/controller_log_prefix.json',dict(source=str(log),bytes=size,sha256=hashlib.sha256(raw).hexdigest(),utc=datetime.now(timezone.utc).isoformat(),live_prefix_only=True))
 exact={'results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl'}
 allowed=[];excluded=[]
 for row in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split('\0'):
  if not row:continue
  status,name=row[:2],row[3:];assert status in (' M','??'),row
  accept=name.startswith(B+'/') or name in exact
  if name.startswith('results/formal_main_v2/control_transport/'):
   lines=(R/name).read_text().splitlines();accept=bool(lines) and json.loads(lines[-1]).get('event')=='control_end'
  if accept:
   p=R/name;assert p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20);allowed.append(name)
  else:excluded.append(name)
 assert set(excluded)<= {'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/commit_healthy_1419.jsonl'},excluded
 for n in allowed:git('add','--',n)
 required=[]
 for n in sorted(allowed):
  raw=git('show',':'+n).stdout;assert hashlib.sha256(raw).hexdigest()==h(R/n);required.append(dict(path=n,sha256=h(R/n),bytes=len(raw)))
  if n.endswith('.py'):compile(raw,n,'exec')
 for rel,pin in inventory['files'].items():assert hashlib.sha256(git('show',':'+rel).stdout).hexdigest()==pin
 assert not git('diff','--cached','--name-only','--','results/formal_main_v2/nonweight_archives/v1','configs','src','scripts').stdout
 git('diff','--cached','--check')
 save(B+'/git_delivery.json',dict(schema='formal_main_v2',status='passed_incremental_index_review',baseline=HEAD,files=required,frozen_index_and_worktree_files=173,scientific_sources_and_configs_changed=False,raw_archives_unchanged=True,weights_added=False,excluded_live_files=excluded))
 git('add','--',B+'/git_delivery.json');git('diff','--cached','--check')
 r=git('commit','-m','Record healthy eight-GPU training supervision at 1419 UTC')
 commit=git('rev-parse','HEAD').stdout.decode().strip();save('.local/git_commit_1419.json',dict(commit=commit,baseline=HEAD,files=len(allowed)+1))
 print(json.dumps(dict(commit=commit,files=len(allowed)+1,pushed=False,summary=r.stdout.decode().splitlines()[:2])))

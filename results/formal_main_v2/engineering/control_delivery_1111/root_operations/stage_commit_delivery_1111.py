from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261019T1911';O='results/formal_main_v2/engineering/control_delivery_1111'
HEAD='df090c0df286e9c0efe2dbe2f3e8c431e1135bcc'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def h(p):return sha(p.read_bytes())
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('commit1111_ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD
 assert not git('diff','--cached','--name-only').stdout,'preexisting staged changes'
 s=json.loads((R/'results/experiment_supervisor/state.json').read_text());assert s['pending_submission'] is None
 inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text());assert len(inventory['files'])==173
 ignore=R/'.gitignore';old=ignore.read_text();lines=[]
 for p in sorted((R/O).rglob('*.log')):
  line='!/'+p.relative_to(R).as_posix()
  if line not in old.splitlines():lines.append(line)
 if lines:ignore.write_text(old+'\n# Exact archived CPU evidence logs, heartbeat20261019T1111.\n'+'\n'.join(lines)+'\n')
 source=R/'.local/stage_commit_delivery_1111.py';dst=R/O/'root_operations'/source.name
 with dst.open('xb') as f:f.write(source.read_bytes())
 log=R/'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out';size=log.stat().st_size
 with log.open('rb') as f:raw=f.read(size)
 assert len(raw)==size and size<10_000_000
 with (R/B/'controller_live_log_prefix.txt').open('xb') as f:f.write(raw)
 save(B+'/controller_live_log_prefix_receipt.json',dict(source=str(log),bytes=size,sha256=sha(raw),utc=datetime.now(timezone.utc).isoformat(),captured_prefix_only=True,live_source_kept_server=True))
 prefixes=[O+'/',B+'/','scripts/formal_cuda_terminal_review_v1/','scripts/ops/formal_action_consumption_guard_v1/','scripts/ops/formal_cuda_continuous_admission_v1/']
 exact={'.gitignore','configs/experiments/formal_main_v2_cuda_continuous_3039258_v1.json','results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl'}
 exact|={'docs/'+x+'.md' for x in ['完整实验计划','实验进度','正式CUDA启动失败恢复登记','正式主实验规划','正式主实验阶段结论','正式动作执行入口接入记录','正式自动连续训练执行登记']}
 allowed=[];excluded=[]
 for row in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split('\0'):
  if not row:continue
  status,name=row[:2],row[3:];assert status in (' M','??'),(status,name)
  accept=name in exact or any(name.startswith(p) for p in prefixes)
  if name.startswith('results/formal_main_v2/control_transport/'):
   records=(R/name).read_text().splitlines();accept=bool(records) and json.loads(records[-1]).get('event')=='control_end'
  if accept:
   p=R/name;assert p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20)
   assert not any(x.lower() in ('.pt','.pth','.bin','.safetensors','.ckpt','.pkl','.pickle','.init') for x in p.suffixes)
   allowed.append(name)
  else:excluded.append(name)
 assert set(excluded)<= {'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/stage_commit_delivery_1111.jsonl'},excluded
 required=[{'path':n,'sha256':h(R/n),'bytes':(R/n).stat().st_size} for n in sorted(allowed)]
 save(B+'/git_required_files.json',dict(schema='formal_main_v2',files=required))
 allowed.append(B+'/git_required_files.json')
 for i in range(0,len(allowed),60):git('add','--',*allowed[i:i+60])
 names=git('diff','--cached','--name-only','-z').stdout.decode().split('\0');names=[n for n in names if n]
 assert set(names)==set(allowed)
 frozen=[]
 for rel,pin in inventory['files'].items():
  assert h(R/rel)==pin==sha(git('show',':'+rel).stdout);frozen.append(rel)
 assert not git('diff','--cached','--name-only','--','results/formal_main_v2/nonweight_archives/v1','scripts/ops/nonweight_archive_v1','scripts/ops/check_nonweight_archive_stage.py').stdout
 snapshot='results/formal_main_v2/nonweight_archives/v1/snapshots/completed_training_20261019_0943_union23.json'
 assert sha(git('show',':'+snapshot).stdout)=='4af1f5375d8e79bf567aeb5e68e1b4ed28b52bce5dd77e6a65623e17be70abb2'
 for row in required:assert sha(git('show',':'+row['path']).stdout)==row['sha256']
 index=git('ls-files','--stage','-z').stdout;index_rows=[x for x in index.split(b'\0') if x];new_sources=[]
 for n in names:
  raw=git('show',':'+n).stdout
  assert len(raw)<100*(1<<20)
  if n.endswith('.py'):compile(raw,n,'exec');new_sources.append(n)
 staged_modes={row.split(b'\t',1)[1].decode():row.split(b' ',1)[0].decode() for row in index_rows}
 assert all(staged_modes[n] in ('100644','100755') for n in names)
 diagnostic=git('diff','--cached','--check',check=False);exceptions=[]
 if diagnostic.returncode:
  assert diagnostic.returncode==2 and not diagnostic.stderr
  for line in diagnostic.stdout.decode().splitlines():
   if line.endswith('trailing whitespace.') or line.endswith('new blank line at EOF.'):
    name=line.split(':',1)[0];assert name.startswith(O+'/') and Path(name).suffix in ('.log','.xml'),line;exceptions.append(name)
  assert exceptions,diagnostic.stdout.decode()
  exceptions=sorted(set(exceptions));git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 receipt=dict(schema='formal_main_v2',kind='incremental_verified_Git_index_delivery',status='passed',utc=datetime.now(timezone.utc).isoformat(),baseline_HEAD=HEAD,index_sha256_before_receipt=sha(index),files=required,frozen_worktree_and_index_verified=173,compiled_Python_sources=len(new_sources),new_blobs_checked_size_mode_and_SHA=len(names),archive_reused_without_new_raw_changes=dict(snapshot=snapshot,sha256='4af1f5375d8e79bf567aeb5e68e1b4ed28b52bce5dd77e6a65623e17be70abb2',prior_full_index_guard='results/formal_main_v2/preflight/heartbeat_20261019T1743/git_index_guard.stdout.json',decoded_raw_files_previous_guard=23,decoded_raw_bytes_previous_guard=859375546),unmodified_raw_log_whitespace_exceptions=exceptions,raw_whitespace_stdout=diagnostic.stdout.decode(),excluded_live_or_current_audit=excluded,checkpoint_or_weight_added=False)
 save(B+'/git_index_delivery.json',receipt);git('add','--',B+'/git_index_delivery.json')
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD
 result=git('commit','-m','Register reviewed CUDA continuation and strict execution ancestry guards')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_1111.json',dict(commit=commit,baseline=HEAD,files=len(names)+1,index_receipt=B+'/git_index_delivery.json',index_receipt_sha256=h(R/B/'git_index_delivery.json'),pushed=False))
 print(json.dumps(dict(commit=commit,files=len(names)+1,compiled_sources=len(new_sources),frozen_verified=173,raw_whitespace_exceptions=exceptions,summary=result.stdout.decode().splitlines()[:3],pushed=False)))

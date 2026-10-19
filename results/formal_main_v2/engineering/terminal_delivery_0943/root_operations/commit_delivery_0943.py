from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261019T1743'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.run(['git','-c','core.quotepath=false',*a],cwd=R,capture_output=True,check=True)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('commit0943c',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 review=json.loads((R/B/'git_index_guard.stdout.json').read_text())
 assert review['status']=='verified_index_archive_delivery'
 assert hashlib.sha256(git('ls-files','--stage','-z').stdout).hexdigest()==review['index_sha256']
 assert hashlib.sha256(git('diff','--cached','--name-status','--no-renames','--no-ext-diff','--no-textconv','-z').stdout).hexdigest()==review['staged_changes_sha256']
 assert git('rev-parse','HEAD').stdout.decode().strip()==review['head']
 audit='results/formal_main_v2/control_transport/stage_archive_delivery_0943.jsonl'
 assert json.loads((R/audit).read_text().splitlines()[-1])['event']=='control_end'
 additions=[B+'/git_index_guard.stdout.json',B+'/git_index_guard.stderr.txt',B+'/git_stage_closed_receipt.json',audit]
 source=R/'.local/commit_delivery_0943.py';dst=R/'results/formal_main_v2/engineering/terminal_delivery_0943/root_operations/commit_delivery_0943.py'
 with dst.open('xb') as f:f.write(source.read_bytes())
 additions.append(dst.relative_to(R).as_posix())
 rows=[]
 for name in additions:
  p=R/name;assert p.is_file() and not p.is_symlink() and p.stat().st_size<1_000_000
  rows.append(dict(path=name,bytes=p.stat().st_size,sha256=h(p)))
 receipt=R/B/'git_guard_completion_delivery.json'
 with receipt.open('x') as f:
  json.dump(dict(status='full_index_guard_passed_plus_exact_small_delivery_receipts',utc=datetime.now(timezone.utc).isoformat(),
   previous_verified_index=review['index_sha256'],previous_verified_staged_changes=review['staged_changes_sha256'],
   additions=rows,source173_unchanged=True,scientific_results_inferred=False,
   raw_originals_retained=23,raw_bytes_restored_exactly=859375546,weight_payloads_added=False),f,sort_keys=True);f.write('\n')
 additions.append(receipt.relative_to(R).as_posix())
 git('add','--',*additions)
 for row in rows:assert hashlib.sha256(git('show',':'+row['path']).stdout).hexdigest()==row['sha256']
 git('diff','--cached','--check')
 out=git('commit','-m','Record 44 verified selectors, CUDA recovery and Spatial development readiness')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 with (R/'.local/git_commit_0943.json').open('x') as f:json.dump(dict(commit=commit,guard=review['status'],files=git('diff-tree','--no-commit-id','--name-only','-r','HEAD').stdout.decode().splitlines()),f)
 print(json.dumps(dict(commit=commit,commit_output=out.stdout.decode(),index_guard=review['status'],pushed=False)))

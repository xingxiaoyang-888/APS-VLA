from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261019T1743'
def sha(x):return hashlib.sha256(x).hexdigest()
def h(p):return sha(p.read_bytes())
def git(*a,check=True):return subprocess.run(['git','-c','core.quotepath=false',*a],cwd=R,capture_output=True,check=check)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('commit0943v2c',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 review=json.loads((R/B/'git_index_guard.stdout.json').read_text());receipt=json.loads((R/B/'git_guard_completion_delivery.json').read_text())
 added={x['path'] for x in receipt['additions']}|{B+'/git_guard_completion_delivery.json'}
 for row in receipt['additions']:assert sha(git('show',':'+row['path']).stdout)==row['sha256']==h(R/row['path'])
 index=git('ls-files','--stage','-z').stdout;kept=b''.join(row+b'\0' for row in index.split(b'\0') if row and row.split(b'\t',1)[1].decode() not in added)
 assert sha(kept)==review['index_sha256']
 changes=git('diff','--cached','--name-status','--no-renames','--no-ext-diff','--no-textconv','-z').stdout.split(b'\0')
 kept_changes=b''.join(changes[i]+b'\0'+changes[i+1]+b'\0' for i in range(0,len(changes)-1,2) if changes[i+1].decode() not in added)
 assert sha(kept_changes)==review['staged_changes_sha256']
 assert git('rev-parse','HEAD').stdout.decode().strip()==review['head']
 exceptions=['results/formal_main_v2/engineering/terminal_delivery_0943/independent/partition_tests.log','results/formal_main_v2/engineering/terminal_delivery_0943/independent/partition_tests.xml']
 diagnostic=git('diff','--cached','--check',check=False)
 assert diagnostic.returncode==2 and not diagnostic.stderr
 notes=[line for line in diagnostic.stdout.decode().splitlines() if line.endswith('trailing whitespace.')]
 assert len(notes)==6 and all(any(line.startswith(p+':') for p in exceptions) for line in notes)
 git('diff','--cached','--check','--','.',*[':(exclude)'+p for p in exceptions])
 dest=R/B/'git_preserved_raw_whitespace_review.json'
 with dest.open('x') as f:json.dump(dict(status='all_nonraw_changes_pass_whitespace_check',exact_preserved_raw_exceptions=exceptions,
  reason='Original failed pytest diagnostic bytes include trailing spaces. Preserve immutable audited log/XML SHA; do not normalize raw evidence.',
  original_check_stdout=diagnostic.stdout.decode(),actual_index_guard_still_matches=True,utc=datetime.now(timezone.utc).isoformat()),f,sort_keys=True);f.write('\n')
 src=R/'.local/commit_delivery_0943_v2.py';dst=R/'results/formal_main_v2/engineering/terminal_delivery_0943/root_operations/commit_delivery_0943_v2.py'
 with dst.open('xb') as f:f.write(src.read_bytes())
 completed_audit='results/formal_main_v2/control_transport/commit_delivery_0943.jsonl'
 assert json.loads((R/completed_audit).read_text().splitlines()[-1])['event']=='control_end'
 small=[dest.relative_to(R).as_posix(),dst.relative_to(R).as_posix(),completed_audit]
 for p in small:assert (R/p).stat().st_size<1_000_000
 git('add','--',*small)
 git('diff','--cached','--check','--','.',*[':(exclude)'+p for p in exceptions])
 result=git('commit','-m','Record 44 verified selectors, CUDA recovery and Spatial development readiness')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 files=git('diff-tree','--no-commit-id','--name-only','-r','HEAD').stdout.decode().splitlines()
 with (R/'.local/git_commit_0943.json').open('x') as f:json.dump(dict(commit=commit,index_guard=review['status'],files=files),f)
 print(json.dumps(dict(commit=commit,files_changed=len(files),commit_summary=result.stdout.decode().splitlines()[:2],pushed=False)))

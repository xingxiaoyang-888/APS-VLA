from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,fcntl,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B=R/'results/formal_main_v2/preflight/heartbeat_20261019T2318'
G=R/'scripts/ops/formal_action_deployment_v1/gateway.py';PIN='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a'
A='results/formal_main_v2/execution/action_spatial_resume_0943/submission_authorization.json';AP='55f6c06a83847f8f60850309cdade6991cc70ba3e83451f086632c3d76504cd6'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,v):
 with (B/name).open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
assert h(G)==PIN and h(R/A)==AP
ownerpath=R/'results/formal_main_v2/autonomous_training/run_v1/owner.json';before=h(ownerpath);owner=json.loads(ownerpath.read_text());s=json.loads((R/'results/experiment_supervisor/state.json').read_text())
assert owner['owner_id']==s['autonomous_training_v1']['owner_id'] and owner['coordinator_job_id']=='3034538'
assert owner['activation_sha256']=='7391c3bb17c36f8b0dbce540e28714ac6f721662118ddb7338d7c0288aa0bcef'
lease=R/'results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock';assert Path(owner['lock'])==lease and lease.is_file()
with lease.open('rb') as f:
 held=False
 try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
 except BlockingIOError:held=True
assert held and h(ownerpath)==before
assert not (R/'results/formal_main_v2/downstream_gateway'/AP).exists()
args=[sys.executable,'-B',str(G),'--authorization',A,'--authorization-sha256',AP,'--gateway-sha256',PIN,'--submit','--root-reviewed-submit']
save('Spatial_dispatch_intent.json',dict(utc=datetime.now(timezone.utc).isoformat(),argv=args,root_reuses_exact_prior_authorization=True,owner=owner,lease_held=True,expected_new_trials=588,previous_trials_preserved=12,maximum_requests=1,final_release=False))
r=subprocess.run(args,cwd=R,capture_output=True,text=True)
for name,text in [('Spatial_dispatch_stdout.json',r.stdout),('Spatial_dispatch_stderr.txt',r.stderr)]:
 with (B/name).open('x') as f:f.write(text)
save('Spatial_dispatch_process.json',dict(returncode=r.returncode,stdout_sha256=h(B/'Spatial_dispatch_stdout.json'),stderr_sha256=h(B/'Spatial_dispatch_stderr.txt'),automatic_retry=False))
if r.returncode:
 print(json.dumps(dict(status='stopped_inspect_gateway_pending_no_retry',returncode=r.returncode,stderr=r.stderr[-5000:])));raise SystemExit(r.returncode)
v=json.loads(r.stdout);assert v['status']=='submitted_once'
print(json.dumps(dict(status=v['status'],job_id=v['job']['job_id'],mode=v['job']['mode'],suite=v['job']['suite'],receipt=B.relative_to(R).as_posix()+'/Spatial_dispatch_stdout.json')))

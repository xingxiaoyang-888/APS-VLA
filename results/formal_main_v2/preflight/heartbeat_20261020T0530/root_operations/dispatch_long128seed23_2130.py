from pathlib import Path
import hashlib,sys,subprocess,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B=R/'results/formal_main_v2/preflight/heartbeat_20261020T0530'
G=R/'scripts/ops/formal_action_deployment_v1/gateway.py'
PIN='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a'
assert hashlib.sha256(G.read_bytes()).hexdigest()==PIN
argv=[sys.executable,'-B',str(G),'--authorization','results/formal_main_v2/execution/long_remaining16_action_v1_1827/k128_seed23/submission_authorization.json','--authorization-sha256','6e574361d66aaba7869b536082d9c605106bdaf2ec428f3ccb46ea986c8ef37a','--gateway-sha256',PIN]
check=subprocess.run(argv,cwd=R,capture_output=True,timeout=180)
with (B/'Long128seed23_preflight_stdout.json').open('xb') as f:f.write(check.stdout)
with (B/'Long128seed23_preflight_stderr.txt').open('xb') as f:f.write(check.stderr)
assert check.returncode==0,check.stderr.decode()[-4000:]
v=json.loads(check.stdout);assert v['status']=='read_only_checks_passed_not_submitted' and len(v['capacity']['occupied'])<8
print(json.dumps({'preflight':'passed','occupied':len(v['capacity']['occupied']),'scope':'Long128 seed23 A/B development200'}),flush=True)
dispatch=subprocess.run(argv+['--submit','--root-reviewed-submit'],cwd=R,capture_output=True,timeout=180)
with (B/'Long128seed23_submit_stdout.json').open('xb') as f:f.write(dispatch.stdout)
with (B/'Long128seed23_submit_stderr.txt').open('xb') as f:f.write(dispatch.stderr)
assert dispatch.returncode==0,dispatch.stderr.decode()[-4000:]
result=json.loads(dispatch.stdout);assert result['status']=='submitted_once'
print(json.dumps({'status':result['status'],'job_id':result['job']['job_id'],'stage_key':result['job']['stage_key'],'state_sha256':result['state_sha256']}))

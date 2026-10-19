from pathlib import Path
import hashlib,sys,subprocess,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B=R/'results/formal_main_v2/preflight/heartbeat_20261020T0332'
G=R/'.local/cuda_recovery_autonomous_1940/gateway.py'
PIN='c97b66100a0a21a722b17e32129b7a220fac7b2b2cb8b9cc9678b88f605476c3'
assert hashlib.sha256(G.read_bytes()).hexdigest()==PIN
argv=[sys.executable,'-B',str(G),'--authorization','configs/experiments/formal_main_v2_cuda_single_recovery_3028522_v1.json','--authorization-sha256','7411a2e5e0d7e2123eea8bfea4c2bbaccb037d54b09697180340a597e3cfb18a','--gateway-sha256',PIN]
check=subprocess.run(argv,cwd=R,capture_output=True,timeout=180)
with (B/'CUDA3028522_preflight_stdout.json').open('xb') as f:f.write(check.stdout)
with (B/'CUDA3028522_preflight_stderr.txt').open('xb') as f:f.write(check.stderr)
assert check.returncode==0,check.stderr.decode()[-4000:]
v=json.loads(check.stdout);assert v['status']=='read_only_checks_passed_not_submitted' and v['original_target']==1500 and len(v['capacity']['occupied'])<8
print(json.dumps({'preflight':'passed','occupied':len(v['capacity']['occupied']),'target':1500}),flush=True)
dispatch=subprocess.run(argv+['--submit','--root-reviewed-submit'],cwd=R,capture_output=True,timeout=180)
with (B/'CUDA3028522_submit_stdout.json').open('xb') as f:f.write(dispatch.stdout)
with (B/'CUDA3028522_submit_stderr.txt').open('xb') as f:f.write(dispatch.stderr)
assert dispatch.returncode==0,dispatch.stderr.decode()[-4000:]
result=json.loads(dispatch.stdout);assert result['status']=='submitted_once'
print(json.dumps({'status':result['status'],'job_id':result['job']['job_id'],'stage_key':result['job']['stage_key'],'state_sha256':result['state_sha256']}))

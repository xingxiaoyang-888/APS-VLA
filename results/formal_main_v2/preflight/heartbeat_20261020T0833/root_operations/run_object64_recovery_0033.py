from pathlib import Path
import hashlib,subprocess,sys,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B=R/'results/formal_main_v2/preflight/heartbeat_20261020T0833'
G='.local/cuda_recovery_autonomous_1940/gateway.py'
A='configs/experiments/formal_main_v2_cuda_single_recovery_3028468_v1.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert h(R/G)=='c97b66100a0a21a722b17e32129b7a220fac7b2b2cb8b9cc9678b88f605476c3'
assert h(R/A)=='0f8c1eab2e196c544bbf1302d440085abf052bc0bbc32a6dc3d9377bcdb0aec0'
assert sys.argv[1:] in ([],['--submit'])
submit=bool(sys.argv[1:]);suffix='submit' if submit else 'check'
target=B/('Object64_original_target_'+suffix);target.mkdir(exist_ok=False)
argv=[sys.executable,'-B',str(R/G),'--authorization',A,'--authorization-sha256',h(R/A),'--gateway-sha256',h(R/G)]
if submit:argv+=['--submit','--root-reviewed-submit']
r=subprocess.run(argv,cwd=R,capture_output=True)
for name,raw in [('stdout.json',r.stdout),('stderr.txt',r.stderr)]:
 with (target/name).open('xb') as f:f.write(raw)
record=dict(argv=argv,returncode=r.returncode,stdout_sha256=h(target/'stdout.json'),stderr_sha256=h(target/'stderr.txt'))
with (target/'execution.json').open('x') as f:json.dump(record,f,sort_keys=True,indent=2);f.write('\n')
if r.returncode:
 print(json.dumps(dict(status='stopped_preserved_original_gateway_failure',returncode=r.returncode,stderr_tail=r.stderr.decode()[-3500:],receipt=str(target))))
 sys.exit(r.returncode)
x=json.loads(r.stdout)
assert x['status']==('submitted_once' if submit else 'read_only_checks_passed_not_submitted')
print(json.dumps(dict(status=x['status'],job_id=x.get('job',{}).get('job_id'),receipt=target.relative_to(R).as_posix(),stdout_sha256=h(target/'stdout.json'))))

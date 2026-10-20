from pathlib import Path
import hashlib,subprocess,sys,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B=R/'results/formal_main_v2/preflight/heartbeat_20261020T0833'
G='scripts/ops/formal_spatial_cuda_continuous_admission_v1/gateway.py'
A='configs/experiments/formal_main_v2_spatial_cuda_continuous_3043399_v1.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert h(R/G)=='71af9cf0bce935d00934db8c8198f7f9624fd7194f570e36efd95f77da0634c6'
assert h(R/A)=='206bb080b2c870b112a8976d9eb27c383859ddea308ea5094ead316e569403bd'
assert sys.argv[1:] in ([],['--submit'])
submit=bool(sys.argv[1:]);suffix='submit' if submit else 'check'
target=B/('Spatial_continuous_'+suffix);target.mkdir(exist_ok=False)
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
assert x['status']==('submitted_once' if submit else 'read_only_verified_not_submitted')
print(json.dumps(dict(status=x['status'],job_id=x.get('job',{}).get('job_id'),receipt=target.relative_to(R).as_posix(),stdout_sha256=h(target/'stdout.json'))))

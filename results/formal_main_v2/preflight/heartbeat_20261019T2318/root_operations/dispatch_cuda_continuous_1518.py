from pathlib import Path
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B=R/'results/formal_main_v2/preflight/heartbeat_20261019T2318'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'scripts/ops/formal_cuda_continuous_admission_v1/gateway.py';assert h(p)=='a0f81f18ccdb6f9b0cd5f5f3f871b3f6ab451809a1c6386e347ea3602abd9792'
rel='configs/experiments/formal_main_v2_cuda_continuous_3039258_v1.json';pin='5f86034d43017d3f89b0d3a73cd90dd8bd22b0b8a54461d0b0a51e5f8df6220e';assert h(R/rel)==pin
assert not (R/'results/formal_main_v2/continuous_admissions/3039258'/pin).exists()
args=[sys.executable,'-B',str(p),'--authorization',rel,'--authorization-sha256',pin,'--gateway-sha256',h(p),'--submit','--root-reviewed-submit']
with (B/'CUDA_continuous_dispatch_intent.json').open('x') as f:json.dump(dict(utc=datetime.now(timezone.utc).isoformat(),argv=args,single_request=True,automatic_retry=False),f,sort_keys=True)
run=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=300)
for n,t in [('CUDA_continuous_dispatch.stdout.json',run.stdout),('CUDA_continuous_dispatch.stderr.txt',run.stderr)]:
 with (B/n).open('x') as f:f.write(t)
with (B/'CUDA_continuous_dispatch_process.json').open('x') as f:json.dump(dict(exit_code=run.returncode,stdout_sha256=h(B/'CUDA_continuous_dispatch.stdout.json'),stderr_sha256=h(B/'CUDA_continuous_dispatch.stderr.txt')),f)
if run.returncode:print(run.stderr[-3500:]);raise SystemExit(run.returncode)
r=json.loads(run.stdout);print(json.dumps(dict(status=r['status'],job_id=r['job']['job_id'],target=r['job']['segment_end'],pair=r['job']['stage_key'])))

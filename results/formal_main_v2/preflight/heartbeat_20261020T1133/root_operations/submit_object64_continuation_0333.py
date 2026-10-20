from pathlib import Path
import hashlib,json,subprocess,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
PY='/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python'
B=R/'results/formal_main_v2/preflight/heartbeat_20261020T1133'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
gateway='scripts/ops/formal_object64_cuda_continuous_admission_v1/gateway.py'
gh='2aaed25efd1d8783ace9ace93a5212f67b52f1d1a6fde1072349d8d8a830f54a'
auth='configs/experiments/formal_main_v2_object64_cuda_continuous_3044017_v1.json'
ah='6619bd4e9a8e75b76200bca401a861bc5c6c1180a54c37cf739da18f55ea019c'
assert sha(R/gateway)==gh and sha(R/auth)==ah
assert sha(B/'initial_observation.json')=='637984b0f114b9aecffc3312f5d3933c346406da351616e99d9fed1581940c8d'
out=B/'Object64_continuation_gateway_result.json'
assert not out.exists()
argv=[PY,'-B',str(R/gateway),'--authorization',auth,'--authorization-sha256',ah,'--gateway-sha256',gh,'--submit','--root-reviewed-submit']
p=subprocess.run(argv,cwd=R,text=True,capture_output=True)
record={'argv':argv,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'new_scientific_configuration':False,'root_reviewed_existing_authorization':True}
with out.open('x') as f:json.dump(record,f,sort_keys=True,indent=2)
if p.returncode:
 print(json.dumps({'status':'stopped_no_retry','receipt':str(out.relative_to(R)),'sha256':sha(out),'stderr_tail':p.stderr[-3500:]}));sys.exit(p.returncode)
v=json.loads(p.stdout)
print(json.dumps({'status':v['status'],'job':v['job'],'receipt':str(out.relative_to(R)),'sha256':sha(out)}))

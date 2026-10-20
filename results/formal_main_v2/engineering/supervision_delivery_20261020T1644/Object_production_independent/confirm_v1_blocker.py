from pathlib import Path
import sys,json,hashlib,types
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent;sys.dont_write_bytecode=True
p=R/'.local/object_bridge_production_20261020T1644/package/control.py';raw=p.read_bytes();pin='02be432e8c1dbf237dc08ec9d4e9e833ec2b2461228e5f3a3bede04f6930b642'
assert hashlib.sha256(raw).hexdigest()==pin
m=types.ModuleType('independent_original_candidate');m.__file__=str(p);exec(compile(raw,str(p),'exec'),m.__dict__)
try:m.gateway_module()
except ValueError as e:
 assert str(e).endswith('private derivation target not unique')
 report={'status':'confirmed_candidate_v1_constructive_blocker','entrypoint_sha256':pin,'error':str(e),'actual_original_line':(R/m.GATEWAY).read_text().splitlines()[143],'original_source_sha256':hashlib.sha256((R/m.GATEWAY).read_bytes()).hexdigest(),'GPU_runs':0,'Slurm_calls':0,'canonical_state_writes':False,'description':'Candidate replacement has three leading spaces; pinned original line has two. Private module refuses before any gateway execution. New immutable revision required.'}
else:raise AssertionError('Expected exact-replacement failure absent')
out=D/'attempt01';out.mkdir(exist_ok=False)
for name,data in [('original_candidate_control.py',raw),('independent_rejection.json',(json.dumps(report,sort_keys=True,indent=2)+'\n').encode())]:
 with (out/name).open('xb') as f:f.write(data)
print(json.dumps(report,sort_keys=True))

from pathlib import Path
import types,json,hashlib,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent;sys.dont_write_bytecode=True
p=R/'.local/object_bridge_production_20261020T1644/revision02/package/control.py';raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='f869c673992cc881f849e4d86c56925e2b609028397efbeefe6524f0b684157b'
c=types.ModuleType('v2_order');c.__file__=str(p);exec(compile(raw,str(p),'exec'),c.__dict__)
class E:
 root=project=R
 def __init__(self):self.reads=[]
 def path(self,p):return R/p
 def watch(self,p):return hashlib.sha256((R/p).read_bytes()).hexdigest()
 def read(self,p):self.reads.append(p);return {}
 def unchanged(self):pass
e=E();consumer=c.consumer_module(e)
try:consumer.review_downstream_output(e,{'path':'results/CPU_INVALID_TARGET_NO_FILE.json','sha256':'bad'},expected_stage='development',suite='libero_object')
except ValueError as error:message=str(error)
else:raise AssertionError('Expected missing explicit binding denial')
assert e.reads==['results/CPU_INVALID_TARGET_NO_FILE.json']
report={'status':'confirmed_v2_invalid_target_read_order','candidate_sha256':hashlib.sha256(raw).hexdigest(),'synthetic_read_calls':e.reads,'actual_invalid_target_read':False,'later_error':message,'fix_required':'Original ref, downstream root prefix and SHA validation must precede target read. Revision03 provided.','GPU_runs':0,'Slurm_calls':0}
out=D/'v2_order_blocker';out.mkdir(exist_ok=False)
for name,data in [('reviewed_control.py',raw),('independent_rejection.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())]:
 with (out/name).open('xb') as f:f.write(data)
print(json.dumps(report,sort_keys=True))

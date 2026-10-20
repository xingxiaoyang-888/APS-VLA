from pathlib import Path
import hashlib,json,fcntl,os,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0653';X='results/formal_main_v2/execution/spatial588_pre_dispatch_v1'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b
 else:p.open('xb').write(b)
def save(p,d):put(p,(json.dumps(d,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode())
src=R/'.local/spatial588_integration_20261020T2156/phase3_gateway/gateway.py';rel='scripts/ops/formal_action_deployment_posttraining_spatial588_v1/gateway.py';dst=R/rel
review=R/'.local/spatial_gateway_independent_20261020T2253/independent_review.json'
assert h(src)=='aba5868a8dc4e480262177785b2e62123d014046624f37924248721a9575c99c'
assert h(review)=='e488430128bfbecc1e3ca846764dd6620ebea405d90ffb06063b1d09bdce69b2'
rv=json.loads(review.read_bytes());assert rv['status']=='passed_CPU_review' and not rv['blockers'] and rv['files'][rel]==h(src)
with (R/'results/experiment_supervisor/.writer.lock').open('a+b') as f:
 fcntl.flock(f,fcntl.LOCK_EX)
 before=h(R/'results/experiment_supervisor/state.json')
 put(dst,src.read_bytes());put(R/X/'gateway_independent_review.json',review.read_bytes())
 sp=importlib.util.spec_from_file_location('spatial588gatewaypub',dst);g=importlib.util.module_from_spec(sp);sys.modules[sp.name]=g;exec(compile(dst.read_bytes(),str(dst),'exec'),g.__dict__)
 closure=g.source_files(R);assert all(rv['files'][p]==pin for p,pin in closure.items())
 assert h(R/'results/experiment_supervisor/state.json')==before
 save(R/B/'Spatial_gateway_publication.json',{'status':'exact_independently_reviewed_source_published','files':closure,'independent_review':{'path':X+'/gateway_independent_review.json','sha256':h(R/X/'gateway_independent_review.json')},'state_unchanged':True,'actual_P_verified':False,'new_jobs':0})
 print(json.dumps({'receipt':B+'/Spatial_gateway_publication.json','sha256':h(R/B/'Spatial_gateway_publication.json'),'files':len(closure),'new_jobs':0}))

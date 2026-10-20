from pathlib import Path
import json,hashlib,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T2330';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1530'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'.local/nonLong64_development_independent_20261020T1530/post_readiness/post_readiness_independent_review.json'
pin='abc083c9d0fb7503299f80b1ee914e420160346399b1d563eba3cd00d7777bca'
assert h(source)==pin
post=json.loads(source.read_bytes());assert post['status']=='passed' and post['actual_full_P_wrapper_verifications']==4
rel=E+'/plan_independent/post_readiness/post_readiness_independent_review.json'
dst=R/rel;dst.parent.mkdir(parents=True,exist_ok=True)
assert not dst.is_symlink()
if dst.exists():assert h(dst)==pin
else:
 with dst.open('xb') as f:f.write(source.read_bytes())
idx=R/B/'nonLong_runtime_readiness_root_index.json';assert h(idx)=='622340f7feecc42fc4d29aaa56bc22dd44e66af33dffbf525474107caae78a0b'
items=json.loads(idx.read_bytes())['shards'];assert len(items)==4
base=(R/'.local/reserve_libero_spatial_k256_seed23_20261020T1418.py').read_text()
output=[]
for row in items:
 src=base.replace('20261020T1418','20261020T1530').replace('heartbeat_20261020T2218','heartbeat_20261020T2330').replace("post['actual_full_P_wrapper_verifications']==3","post['actual_full_P_wrapper_verifications']==4")
 for name,value in [('AUTHORIZATION',row['authorization']),('ROOT_ACCEPTANCE',row['root_check']),('POST_READINESS_INDEPENDENT',dict(path=rel,sha256=pin)),('BATCH',row['group_key'])]:
  old=next(x for x in src.splitlines() if x.startswith(name+'='));src=src.replace(old,name+'='+repr(value),1)
 out=R/'.local'/('reserve_'+row['group_key']+'_20261020T1530.py');compile(src,str(out),'exec')
 with out.open('x') as f:f.write(src)
 output.append(dict(group=row['group_key'],entrypoint=out.relative_to(R).as_posix(),sha256=h(out),authorization=row['authorization']))
print(json.dumps(output),flush=True)

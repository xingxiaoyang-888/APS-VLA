from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/object_bridge_production_independent_20261020T1644'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
logs=[('Object_source_independent_post_readiness_20261020T1644.jsonl','506a42bd8675eca1b8cf9ea0b9d6b36f85a7b4dfc1e04fb0504d2abaaee2d7f8',1),('Object_source_independent_post_readiness_v3_20261020T1644.jsonl','ff5226dfb734d2013a35be187fa0d64377f6262003c0893b5f0e5e3f20394d0f',0)]
for name,pin,rc in logs:
 src=R/'results/formal_main_v2/control_transport'/name;raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()==pin;rows=[json.loads(x) for x in raw.splitlines()];assert rows[-1]['event']=='control_end' and rows[-1]['returncode']==rc and rows[-1]['source173_and_entrypoint_unchanged'] is True
 dst=D/'transport'/name
 with dst.open('xb') as f:f.write(raw)
report=D/'post02/independent_review.json';assert h(report)=='6ba5ef2dd4294848ed61a23431925a785ebaec7612f9390e50c055b20adbd635';v=json.loads(report.read_bytes());assert v['status']=='passed' and v['selected_checkpoint_bytes_verified'] is True and v['actual_GPU_runtime_chain_verified'] is False
files=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  assert not p.is_symlink();before=p.stat();digest=h(p);after=p.stat();assert (before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino)
  files.append({'path':p.relative_to(D).as_posix(),'sha256':digest,'bytes':after.st_size})
assert any(x['path']=='canonical_delivery_manifest.json' and x['sha256']=='1359423228a74d3e53a58711c6ce2989a4267c0f35713431ff2fc4f51cfd222b' for x in files)
manifest={'schema':'formal_main_v2','kind':'object256s23_source_control_complete_independent_delivery','status':'passed_pre_execution_source_metadata_checkpoint_bytes_only','utc':datetime.now(timezone.utc).isoformat(),'root':D.relative_to(R).as_posix(),'files':files,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'post_actual_readiness_review':{'path':report.relative_to(R).as_posix(),'sha256':h(report)},'canonical_gateway_CPU_review':{'path':(D/'canonical/gateway_independent_CPU_review.json').relative_to(R).as_posix(),'sha256':h(D/'canonical/gateway_independent_CPU_review.json')},'canonical_plan_review':{'path':(D/'plan/independent_plan_review.json').relative_to(R).as_posix(),'sha256':h(D/'plan/independent_plan_review.json')},'preservation':'All prior prepublication/canonical manifests, source versions, expected candidate failures, harness errors and diffs, CPU fixture files, reports and closed transports are retained byte-for-byte. Weight/checkpoint contents were streamed only and are absent from this delivery.','actual_GPU_runtime_chain_verified':False,'new_GPU_submissions':[],'new_trials':0,'final_release':False,'canonical_or_state_or_Git_or_Slurm_writes':False}
p=D/'delivery_manifest.json'
with p.open('x',encoding='utf-8') as f:json.dump(manifest,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'path':p.relative_to(R).as_posix(),'sha256':h(p),'files':len(files),'bytes':manifest['total_bytes']}))

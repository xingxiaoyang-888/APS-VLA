from pathlib import Path
import hashlib,json,sys,importlib.util,traceback,os
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T1134'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R)
role=sys.argv[1];assert role in ('Object','Goal')
if role=='Object':
 rel='.local/object_terminal_pull_bridge_20261021T0334/bridge.py';pin='191745c8b7bcd82a165849ce8680a990da4f5de53d3204f9cdbb51f598cc7e49'
else:
 rel='scripts/ops/formal_goal_full200_gate_v1/consumer.py';pin='c12a6a5b99c4e34ff19f535a4725fecd9fcabc70ba1f37dc2c6c32c979ad3c4b'
 sys.path.insert(0,'/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_run_564be0995e/src')
 assert h(R/B/'Goal_terminal_manifest.json')=='aceeb30cd6285ebe0680aabb1015ce420a9b671831b9ed172d3b5a6c6f1de1ab'
p=R/rel;assert h(p)==pin
spec=importlib.util.spec_from_file_location('actual_root_terminal_'+role,p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
try:
 out=m.review() if role=='Object' else m.review_terminal(R,dict(path=B+'/Goal_terminal_manifest.json',sha256='aceeb30cd6285ebe0680aabb1015ce420a9b671831b9ed172d3b5a6c6f1de1ab'))
 name=role+'_terminal_review.json'
except BaseException as e:
 out=dict(kind='terminal_reviewer_failure_preserved',entry_sha256=pin,error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),scientific_acceptance=False,state_modified=False)
 name=role+'_terminal_review_failure.json'
p=R/B/name
with p.open('x') as f:json.dump(out,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
print(json.dumps(dict(path=str(p.relative_to(R)),sha256=h(p),status=out.get('status'),error=out.get('error'))))

from pathlib import Path
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent;state=R/'results/experiment_supervisor/state.json';before=state.read_bytes();pin='b37d2469bd25d54fed2a61cfdc22fe7b882f52e85f929412977f4c8b8dd4e81c';assert hashlib.sha256(before).hexdigest()==pin
root=R/'results/formal_main_v2/execution/object_single_error_v1/gateway_attempt01';target=D/'gateway_attempt01';target.mkdir();files=[]
for src in sorted(root.iterdir()):
 assert src.is_file() and not src.is_symlink();data=src.read_bytes();dst=target/src.name
 with dst.open('xb') as f:f.write(data)
 assert src.read_bytes()==data
 files.append({'source':str(src.relative_to(R)),'private':str(dst.relative_to(R)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
assert state.read_bytes()==before
with (D/'state_at_committed.json').open('xb') as f:f.write(before)
with (D/'original_transaction_capture.json').open('x') as f:json.dump({'state_sha256':pin,'files':files,'Slurm_queries':0,'new_GPU_jobs':[],'capture_only_not_review':True},f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'captured_transaction_files':len(files),'state_sha256':pin,'capture_only_not_review':True}))

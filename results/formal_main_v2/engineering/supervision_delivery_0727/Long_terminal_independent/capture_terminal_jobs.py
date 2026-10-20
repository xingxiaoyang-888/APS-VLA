from pathlib import Path
import fcntl,hashlib,json
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent
lock=R/'results/experiment_supervisor/.writer.lock'
assert lock.is_file() and not lock.is_symlink()
with lock.open('rb') as f:
 fcntl.flock(f,fcntl.LOCK_SH|fcntl.LOCK_NB)
 try:
  raw=(R/'results/experiment_supervisor/state.json').read_bytes();state=json.loads(raw)
  jobs=[j for j in state['registered_jobs'] if j['job_id'] in {'3047152','3047156','3047163'}]
 finally:fcntl.flock(f,fcntl.LOCK_UN)
assert len(jobs)==3
expected={'3047152':3130,'3047156':3025,'3047163':3038}
for j in jobs:assert (j['status'],j['exit_code'],j['elapsed_seconds'],j['gpus'])==('COMPLETED','0:0',expected[j['job_id']],1)
v={'kind':'independent_0727_current_terminal_jobs_snapshot','utc':datetime.now(timezone.utc).isoformat(),'read_lock':'LOCK_SH|LOCK_NB on existing writer lock, released before consumer','source_state_sha256':hashlib.sha256(raw).hexdigest(),'registered_jobs':jobs,'state_changed':False,'Slurm_submitted':False}
b=json.dumps(v,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2).encode()+b'\n';p=D/'current_state_job_snapshot.json'
with p.open('xb') as f:f.write(b)
print(json.dumps({'path':str(p.relative_to(R)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'jobs':[j['job_id'] for j in jobs],'writer_read_lock_released':True}))

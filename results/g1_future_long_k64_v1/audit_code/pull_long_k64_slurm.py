"""Archive non-weight logs only for completed registered supplement jobs."""
from pathlib import Path
import hashlib, json, shlex, subprocess

root=Path('F:/CTI-VLA')
state=json.loads((root/'results/experiment_supervisor/state.json').read_text(encoding='utf-8'))
jobs=[j for j in state['registered_jobs'] if j.get('experiment')=='g1_future_long_k64_v1']
jobs=[j for j in jobs if j['status'] in ('COMPLETED','FAILED','TIMEOUT','CANCELLED','OUT_OF_MEMORY','NODE_FAIL')]
assert jobs
names=[f"{j['name']}_{j['job_id']}.{suffix}" for j in jobs for suffix in ('out','err')]
remote='/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/results/slurm'
code="from pathlib import Path\nimport hashlib,json\nr=Path("+repr(remote)+")\nnames="+repr(names)+"\nprint(json.dumps([{'path':n,'bytes':(r/n).stat().st_size,'sha256':hashlib.sha256((r/n).read_bytes()).hexdigest()} for n in names]))"
rows=json.loads(subprocess.check_output(['ssh','-o','BatchMode=yes','tongji-cvpr',
    '/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -c '+shlex.quote(code)],text=True))
target=root/'results/g1_future_long_k64_v1/slurm'
target.mkdir(exist_ok=True)
subprocess.run(['scp','-q','-o','BatchMode=yes']+['tongji-cvpr:'+remote+'/'+n for n in names]+[str(target)],check=True)
for row in rows:
    p=target/row['path']
    assert p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
(target/'download_receipt.json').write_text(json.dumps({'registered_job_ids':[j['job_id'] for j in jobs],'files':rows},indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'completed_jobs':len(jobs),'logs':len(rows),'all_SHA_match':True}))

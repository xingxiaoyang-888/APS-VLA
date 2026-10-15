"""Read only already registered Long64 output paths; never submit or retry."""
from pathlib import Path
import json,shlex,subprocess
r=Path('F:/CTI-VLA');s=json.loads((r/'results/experiment_supervisor/state.json').read_text(encoding='utf-8'))
jobs=[j for j in s['registered_jobs'] if j.get('experiment')=='g1_future_long_k64_v1']
code='''from pathlib import Path
import json
jobs=REGISTERED_JOBS
def read(p):
 try:return json.loads(p.read_text())
 except (FileNotFoundError,json.JSONDecodeError):return None
result=[]
for job in jobs:
 p=Path(job['run_root']);mode=job['mode'];row={'job_id':job['job_id'],'mode':mode,'seed':job.get('training_seed')}
 if mode=='train':
  row['arms']={}
  for arm in ('A','B'):
   q=p/'training'/arm/'cost_events.jsonl';events=[]
   if q.exists():
    for line in q.read_text().splitlines():
     try:events.append(json.loads(line))
     except json.JSONDecodeError:pass
   ends=[e for e in events if e.get('event')=='update_end']
   row['arms'][arm]={'completed_updates':len(ends),'latest_update':ends[-1]['update'] if ends else 0,'report_completed':bool(read(p/'training'/arm/'training_report.json'))}
 elif mode=='closed_loop':
  q=p/'closed_loop/trials.jsonl';events=[]
  if q.exists():
   for line in q.read_text().splitlines():
    try:events.append(json.loads(line))
    except json.JSONDecodeError:pass
  ends=[e for e in events if e.get('event')=='result'];row['completed_attempts']=len(ends)
  row['methods']={m:{'trials':sum(e['method']==m for e in ends),'successes':sum(e['method']==m and e['success'] for e in ends)} for m in ('future_A','future_B')}
 elif mode=='acceptance':
  value=read(p/'acceptance/f01_acceptance.json');row['report_status']=value.get('status') if value else None
 elif mode=='collect':
  value=read(p/'profile_panel/collection_report.json');row['report_status']=value.get('status') if value else None
  row['observations']=value.get('observations') if value else None
 else:
  value=read(p/'profiling/summary.json');row['report_status']=value.get('status') if value else None
 result.append(row)
print(json.dumps(result))
'''.replace('REGISTERED_JOBS',repr(jobs))
print(subprocess.check_output(['ssh','-o','BatchMode=yes','tongji-cvpr',
 '/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -c '+shlex.quote(code)],text=True))

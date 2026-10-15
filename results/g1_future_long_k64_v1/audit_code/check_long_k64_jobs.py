from pathlib import Path
import csv, datetime, io, json, subprocess

r = Path('F:/CTI-VLA')
p = r / 'results/experiment_supervisor/state.json'
s = json.loads(p.read_text(encoding='utf-8'))
jobs = [j for j in s['registered_jobs'] if j.get('experiment') == 'g1_future_long_k64_v1']
assert jobs, 'No registered supplement jobs'
raw = subprocess.check_output(['ssh','-o','BatchMode=yes','tongji-cvpr',
    'sacct -X -P -j ' + ','.join(j['job_id'] for j in jobs) + ' --format=JobIDRaw,JobName,State,ExitCode,ElapsedRaw,AllocTRES,NodeList,Start,End'],text=True)
rows = list(csv.DictReader(io.StringIO(raw), delimiter='|'))
byid = {j['job_id']:j for j in jobs}; out = []
for row in rows:
    if row['JobIDRaw'] not in byid:
        raise ValueError('Unexpected accounting row')
    old = byid[row['JobIDRaw']]
    tres = dict(x.split('=',1) for x in row['AllocTRES'].split(',') if '=' in x)
    value = {'job_id':row['JobIDRaw'], 'state':row['State'], 'exit_code':row['ExitCode'],
        'elapsed_seconds':int(row['ElapsedRaw']), 'allocated_gpus':int(tres.get('gres/gpu',0)),
        'node':row['NodeList'], 'start':row['Start'], 'end':row['End'],
        'scope':old['mode'], 'training_seed':old.get('training_seed')}
    out.append(value)
    old.update(status=value['state'], exit_code=value['exit_code'], elapsed_seconds=value['elapsed_seconds'], node=value['node'])
assert {v['job_id'] for v in out} == set(byid)
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
s['last_supervision_utc'] = now
gpu_seconds = sum(x['elapsed_seconds']*x['allocated_gpus'] for x in out)
s['current_round_cost'].update(allocated_gpu_seconds=gpu_seconds,allocated_gpu_hours=gpu_seconds/3600,
    final=all(x['state'] in {'COMPLETED','FAILED','TIMEOUT','CANCELLED','OUT_OF_MEMORY','NODE_FAIL'} for x in out))
p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
output = r/'results/g1_future_long_k64_v1'
(output/'slurm_accounting.txt').write_text(raw,encoding='utf-8',newline='\n')
(output/'slurm_accounting.json').write_text(json.dumps({'jobs':out,'source':'sacct -X -P; registered multiseed allocations only',
    'queried_utc':now,'parent_jobs_excluded':True},indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(out))

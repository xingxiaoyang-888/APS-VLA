"""Root-only, one pre-inference infrastructure retry of registered Long timing."""
from pathlib import Path
import datetime
import hashlib
import json
import shlex
import subprocess

r = Path('F:/CTI-VLA')
round_id = 'g1_future_long_k64_v1'
out = r / 'results' / round_id
state_path = r / 'results/experiment_supervisor/state.json'
state = json.loads(state_path.read_text(encoding='utf-8'))
assert state.get('pending_submission') is None
prior = [j for j in state['registered_jobs'] if j.get('experiment') == round_id]
profiles = [j for j in prior if j['mode'] == 'profile']
assert len(profiles) == 1 and profiles[0]['job_id'] == '3001742'
failed = profiles[0]
record = out / 'submission_profile_retry1.json'
registration_path = out / 'profile_retry1_registration.json'
assert not record.exists() and not registration_path.exists()
P = '/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA'
S = P + '/snapshots/' + round_id
R = P + '/results/' + round_id
ssh = ['ssh', '-o', 'BatchMode=yes', 'tongji-cvpr']
raw = subprocess.check_output(ssh + [
    'sacct -n -X -P -j ' + ','.join(j['job_id'] for j in prior)
    + ' --format=JobIDRaw,State,ExitCode,ElapsedRaw'], text=True)
rows = {x.split('|')[0]: x.split('|')[1:4] for x in raw.splitlines() if x.strip()}
assert set(rows) == {j['job_id'] for j in prior}
assert rows['3001742'] == ['FAILED', '1:0', '55']
for mode in ('acceptance', 'collect', 'train'):
    assert all(rows[j['job_id']][:2] == ['COMPLETED', '0:0'] for j in prior if j['mode'] == mode)
snapshot = json.loads((out / f'source_{round_id}.json').read_text(encoding='utf-8'))
reg_rel = f'configs/experiments/{round_id}.json'
reg_sha = hashlib.sha256((r / reg_rel).read_bytes()).hexdigest()
assert reg_sha == snapshot['files'][reg_rel] == failed['registration_sha256']
methods_sha = hashlib.sha256((out / 'profile_methods.json').read_bytes()).hexdigest()
assert methods_sha == '5b0b98f59c0aa8eb33500c43f14a76db99e6c97c38aa14c76344f2f82a74db2b'
remote_code = f'''from pathlib import Path
import hashlib,json
r=Path({R!r}); s=Path({S!r})
assert not (r/'profiling').exists()
assert json.loads((r/'job_3001742.json').read_text())['exit_code']==1
assert hashlib.sha256((s/{reg_rel!r}).read_bytes()).hexdigest()=={reg_sha!r}
assert hashlib.sha256((r/'profile_methods.json').read_bytes()).hexdigest()=={methods_sha!r}
p=Path({P!r})/'results/slurm/cti-long-o2a_3001742.err'
error=p.read_text()
assert 'RuntimeError: No CUDA GPUs are available' in error
assert 'line 183, in run' in error
assert 'torch.cuda.get_device_name(0)' in error
print(json.dumps({{'profiling_directory_absent':True,'failed_stderr_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}}))
'''
evidence = json.loads(subprocess.check_output(ssh + [
    '/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -c ' + shlex.quote(remote_code)], text=True))
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
registration = {
    'experiment': round_id, 'registered_utc': now, 'retry_of': '3001742', 'retry_index': 1,
    'reason': 'First CUDA context initialization failed before base loading or any warmup/measured policy inference; exact driver/allocation cause unconfirmed.',
    'independent_read_only_audit': 'CPU checkpoint loading and legacy source imports do not alter CUDA visibility or initialize CUDA; device_count may enumerate NVML without a usable CUDA context.',
    'failed_attempt_gpu_seconds': 55, 'failed_attempt_policy_calls': 0, **evidence,
    'unchanged_source_sha256': snapshot['source_sha256'], 'unchanged_registration_sha256': reg_sha,
    'unchanged_methods_sha256': methods_sha, 'excluded_node': 'gpu4020',
    'same_L40_required': True, 'protocol_and_runtime_identity_checks_unchanged': True,
    'maximum_policy_calls_across_both_attempts': 2600,
    'retain_failed_logs_and_full_allocation_cost': True,
    'no_measurement_based_rerun_or_parameter_change': True,
    'automatic_further_retries': False, 'test_opened': False,
}
registration_path.write_text(json.dumps(registration, indent=2) + '\n', encoding='utf-8', newline='\n')
subprocess.run(['scp','-q','-o','BatchMode=yes',str(registration_path),'tongji-cvpr:'+R+'/'+registration_path.name], check=True)
command = ('cd ' + shlex.quote(P) + ' && test ! -e ' + shlex.quote(R + '/profiling')
    + ' && sbatch --parsable --exclude=gpu4020 --export=' + shlex.quote('ALL,SOURCE_ROOT='+S+',RUN_ROOT='+R+',MODE=profile')
    + ' ' + shlex.quote(S + '/scripts/server/g1_future_long_profile.slurm'))
state['pending_submission'] = {'experiment':round_id, 'mode':'profile', 'retry_of':'3001742', 'retry_index':1, 'utc':now}
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
answer = subprocess.run(ssh + [command], capture_output=True, text=True)
job_id = answer.stdout.strip().split(';')[0]
if answer.returncode or not job_id.isdigit():
    raise SystemExit('Unresolved submission retained; inspect before any retry: '+answer.stdout+answer.stderr)
job = {**failed, 'job_id':job_id, 'status':'SUBMITTED', 'submitted_utc':now,
    'retry_of':'3001742', 'retry_index':1, 'retry_registration':str(registration_path.relative_to(r)).replace('\\','/'),
    'excluded_node':'gpu4020', 'purpose':'Sole same-protocol infrastructure retry before any Long O2A inference; preserve failed55 GPU seconds'}
for key in ('exit_code','elapsed_seconds','node'):
    job.pop(key, None)
state['registered_jobs'].append(job)
state['pending_submission'] = None
state['stage'] = 'G1_F_Long_k64_closed_loop_and_Long_full_latency'
state['last_supervision_utc'] = now
state['current_round_cost']['registered_jobs'] = len(prior)+1
state['current_round_cost']['final'] = False
state['last_observed_G1_F_Long_k64_progress'].update(gpu_jobs=len(prior)+1, profile_job=job_id,
    failed_profile_job='3001742', failed_profile_gpu_seconds=55)
state['next_allowed_action'] = 'Complete registered180 rollouts and sole profile retry, then analyze all retained results; no C or test'
state['current_work'] = 'All6 fresh64 training arms audited;180 development trials running; sole unchanged timing retry after pre-inference CUDA initialization failure'
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
record.write_text(json.dumps(job, indent=2)+'\n', encoding='utf-8', newline='\n')
print(json.dumps(job))

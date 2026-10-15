"""Root-only submission of one immutable, audited Long64 stage."""
from pathlib import Path
import argparse, datetime, hashlib, json, shlex, subprocess

r=Path('F:/CTI-VLA'); round_id='g1_future_long_k64_v1'
p=argparse.ArgumentParser()
p.add_argument('mode', choices=['acceptance','train','closed_loop','collect','profile'])
p.add_argument('--seed',type=int,choices=[17,23,41],default=17)
a=p.parse_args()
state_path=r/'results/experiment_supervisor/state.json'
s=json.loads(state_path.read_text(encoding='utf-8'))
assert s.get('pending_submission') is None, 'Unresolved submission must be inspected, not retried'
reg_path=r/f'configs/experiments/{round_id}.json'
reg=json.loads(reg_path.read_text(encoding='utf-8'))
out=r/f'results/{round_id}'
source_meta=json.loads((out/f'source_{round_id}.json').read_text(encoding='utf-8'))
assert hashlib.sha256(reg_path.read_bytes()).hexdigest()==source_meta['files'][reg_path.relative_to(r).as_posix()]
cfg=reg['new_configs'][str(a.seed)]
assert hashlib.sha256((r/cfg['path']).read_bytes()).hexdigest()==cfg['sha256']
local_run=out/f'seed{a.seed}' if a.mode in ('train','closed_loop') else out
record=local_run/f'submission_{a.mode}.json'
assert not record.exists(), 'Already submitted; retain history and inspect'
prior=[j for j in s['registered_jobs'] if j.get('experiment')==round_id]
assert not any(j['mode']==a.mode and (a.mode not in ('train','closed_loop') or j.get('training_seed')==a.seed) for j in prior)
P='/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA'; S=P+'/snapshots/'+round_id
R=P+'/results/'+round_id; run=R+('/seed'+str(a.seed) if a.mode in ('train','closed_loop') else '')
ssh=['ssh','-o','BatchMode=yes','tongji-cvpr']
if prior:
    raw=subprocess.check_output(ssh+['sacct -n -X -P -j '+','.join(j['job_id'] for j in prior)+' --format=JobIDRaw,State,ExitCode'],text=True)
    rows={x.split('|')[0]:x.split('|')[1:3] for x in raw.splitlines() if x.strip()}
    assert set(rows)=={j['job_id'] for j in prior},rows
else: rows={}
def completed(mode,seed=None):
    jobs=[j for j in prior if j['mode']==mode and (seed is None or j.get('training_seed')==seed)]
    return len(jobs)==1 and rows[jobs[0]['job_id']]==['COMPLETED','0:0']
def read(path): return json.loads(path.read_text(encoding='utf-8'))
if a.mode in ('acceptance','train','closed_loop'):
    reuse=out/f'seed{a.seed}/budget_reuse_registration.json'
    assert reuse.is_file()
if a.mode in ('train','closed_loop'):
    assert completed('acceptance'), 'New64 F01 must complete first'
    gate=read(out/'acceptance/root_review.json'); assert gate['status']=='passed'
if a.mode=='closed_loop':
    assert completed('train',a.seed)
    assert read(local_run/'training/train_finalization.json')['status']=='verified'
    assert read(local_run/'training/independent_review.json')['status']=='passed'
if a.mode=='profile':
    assert completed('collect')
    assert all(completed('train',seed) for seed in (17,23,41))
    assert read(out/'profile_panel/root_review.json')['status']=='passed'
    assert (out/'profile_methods.json').is_file()
stage={'acceptance':'acceptance','train':'training','closed_loop':'closed_loop','collect':'profile_panel','profile':'profiling'}[a.mode]
checks=['test ! -e '+shlex.quote(run+'/'+stage)]
if a.mode=='train':
    checks.append('test ! -e '+shlex.quote(cfg['checkpoint_root_server']))
script='g1_future_long_k64.slurm' if a.mode in ('acceptance','train','closed_loop') else 'g1_future_long_profile.slurm'
command='cd '+shlex.quote(P)+' && '+' && '.join(checks)+' && sbatch --parsable --export='+shlex.quote('ALL,SOURCE_ROOT='+S+',RUN_ROOT='+run+',TRAIN_SEED='+str(a.seed)+',MODE='+a.mode)+' '+shlex.quote(S+'/scripts/server/'+script)
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
s['pending_submission']={'experiment':round_id,'mode':a.mode,'training_seed':a.seed,'run_root':run,'utc':now}
state_path.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
answer=subprocess.run(ssh+[command],capture_output=True,text=True)
job_id=answer.stdout.strip().split(';')[0]
if answer.returncode or not job_id.isdigit():
    raise SystemExit('Unresolved submission preserved; inspect before retry: '+answer.stdout+answer.stderr)
job={'job_id':job_id,'name':'cti-long-k64' if script=='g1_future_long_k64.slurm' else 'cti-long-o2a',
     'experiment':round_id,'mode':a.mode,'training_seed':a.seed if a.mode in ('acceptance','train','closed_loop') else None,
     'status':'SUBMITTED','source_root':S,'run_root':run,'source_sha256':source_meta['source_sha256'],
     'registration_sha256':hashlib.sha256(reg_path.read_bytes()).hexdigest(),'submitted_utc':now,
     'purpose':'Bounded Long64 pruning/O2A experiment; only predeclared development data; no test'}
s['registered_jobs'].append(job);s['pending_submission']=None;s['stage']='G1_F_Long_k64_'+a.mode
s['last_supervision_utc']=now;s['current_round_cost']['registered_jobs']+=1
s['last_observed_G1_F_Long_k64_progress']['gpu_jobs']=len(prior)+1
state_path.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
local_run.mkdir(parents=True,exist_ok=True)
record.write_text(json.dumps(job,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(job))

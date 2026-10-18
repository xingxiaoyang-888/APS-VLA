"""Root-only status/submission for the registered formal experiment.

This tool never selects hyperparameters or opens final states. It checks only
job IDs in this project's supervisor state and refuses unresolved or duplicate
submissions. Scientific gates remain enforced again by the server entrypoints.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

ROOT=Path(__file__).resolve().parents[1]
P='/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA'
H='/share/home/u15016/XXY_CVPR/CTI-VLA'
ROUND='formal_main_v2'
SSH=['ssh','-o','BatchMode=yes','tongji-cvpr']
STATE=ROOT/'results/experiment_supervisor/state.json'
ACTIVE={'PENDING','RUNNING','CONFIGURING','COMPLETING','SUSPENDED','REQUEUED','RESIZING'}

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.partial')
    with temporary.open('w',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n');f.flush();os.fsync(f.fileno())
    temporary.replace(path)
def remote(command):return subprocess.check_output(SSH+[command],text=True,encoding='utf-8')

def verify_remote_training_progress(outrel, prior):
    """Require fresh non-weight evidence before any resumed allocation."""
    names=['registered_config.json','training_summary.json','training_progress.json']
    names += [f'{arm}/{name}' for arm in ('A','B') for name in ('training_report.json','progress_report.json')]
    script=("from pathlib import Path; import hashlib,json; "
        +"root=Path("+repr(P+'/'+outrel)+"); names="+repr(names)+"; "
        +"print(json.dumps({name:hashlib.sha256((root/name).read_bytes()).hexdigest() "
        +"for name in names if (root/name).is_file()}))")
    found=json.loads(remote(shlex.quote(H+'/venv/bin/python')+' -c '+shlex.quote(script)))
    if not isinstance(found,dict) or any(name not in names for name in found):
        raise ValueError('Invalid remote training inventory')
    if any(j['status']=='COMPLETED' for j in prior) and 'registered_config.json' not in found:
        raise ValueError('Completed training job lacks remote registration; inspect before resubmitting')
    for name in names:
        local=ROOT/outrel/name
        if (local.is_file() != (name in found)) or (name in found and sha(local)!=found[name]):
            raise ValueError('Pull and verify latest remote non-weight training evidence before resume: '+name)
    return found

@contextmanager
def supervisor_lock():
    path=STATE.parent/'.writer.lock';path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a+b') as handle:
        if os.name=='nt':
            import msvcrt
            handle.seek(0,os.SEEK_END)
            if handle.tell()==0:handle.write(b'0');handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
            try:yield
            finally:
                handle.seek(0);msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
        else:
            import fcntl
            fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            try:yield
            finally:fcntl.flock(handle,fcntl.LOCK_UN)

def refresh(state):
    jobs=[j for j in state['registered_jobs'] if j.get('experiment')==ROUND]
    ids=[str(j['job_id']) for j in jobs]
    if not ids:return jobs
    if not all(x.isdigit() for x in ids):raise ValueError('Invalid registered Slurm ID')
    raw=remote('sacct -n -X -P -j '+','.join(ids)+' --format=JobIDRaw,State,ExitCode,ElapsedRaw,AllocTRES,NodeList')
    rows={r.split('|')[0]:r.split('|') for r in raw.splitlines() if r.strip()}
    if set(rows)!=set(ids):raise ValueError('Accounting incomplete; do not infer completion or resubmit')
    gpu_seconds=0
    for j in jobs:
        row=rows[j['job_id']]
        j.update(status=row[1],exit_code=row[2],elapsed_seconds=int(row[3]),allocation=row[4],node=row[5])
        resources=dict(x.split('=',1) for x in row[4].split(',') if '=' in x)
        gpus=int(resources.get('gres/gpu',0));j['gpus']=gpus
        gpu_seconds+=gpus*int(row[3])
    state['current_round_cost'].update(registered_jobs=len(jobs),allocated_gpu_seconds=gpu_seconds,
        allocated_gpu_hours=gpu_seconds/3600,final=False,historical_jobs_excluded=True)
    state['last_supervision_utc']=datetime.now(timezone.utc).isoformat()
    write(ROOT/f'results/{ROUND}/slurm_accounting.json',{'utc':state['last_supervision_utc'],'raw':raw,'jobs':jobs,
        'allocated_gpu_seconds':gpu_seconds,'allocated_gpu_hours':gpu_seconds/3600,'includes_running_elapsed':True})
    write(STATE,state)
    return jobs

def submit(args,state,jobs):
    if state.get('pending_submission') is not None:raise ValueError('Unresolved submission: inspect it before retry')
    reg=read(ROOT/f'configs/experiments/{ROUND}.json');suite=reg['suites'][args.suite]
    source_info=read(args.source_inventory);source=source_info['source_root_server']
    if not source.startswith(P+'/snapshots/formal_main_v2_'):raise ValueError('Unregistered formal source root')
    for rel,digest in source_info['files'].items():
        if sha(ROOT/rel)!=digest:raise ValueError('Local source differs from frozen source: '+rel)
    pair=next(p for p in reg['pairs'] if (p['suite'],p['visual_tokens'],p['seed'])==(args.suite,args.budget,args.seed))
    stage_key=f'{args.suite}_{args.stage}'+(f'_k{args.budget}_seed{args.seed}' if args.stage=='train' else '')
    prior=[j for j in jobs if j.get('stage_key')==stage_key]
    if any(j['status'] in ACTIVE for j in prior):raise ValueError('This registered stage already has an active job')
    failed=[j for j in prior if j['status'] not in ACTIVE|{'COMPLETED'}]
    if failed and not args.repair_record:
        raise ValueError('Failed prior stage requires a retained root repair record; never blind retry')
    if args.repair_record:
        repair=read(args.repair_record)
        expected={'status':'reviewed','stage_key':stage_key,'target_source_sha256':source_info['source_sha256'],
                  'segment_end':args.segment if args.stage=='train' else None}
        if (not failed or any(repair.get(k)!=v for k,v in expected.items())
                or set(repair.get('failed_job_ids',[]))!={j['job_id'] for j in failed}):
            raise ValueError('Repair must bind this stage, its failed jobs, target source and segment')
    watched={}
    def watch(local,server=None):
        path=Path(local);path=ROOT/path if not path.is_absolute() else path
        if ROOT not in path.resolve().parents:raise ValueError('Local evidence must belong to CTI-VLA')
        rel=path.relative_to(ROOT).as_posix();watched[server or P+'/'+rel]=sha(path)
    common=['--protocol',P+'/'+suite['protocol'],'--windows',P+'/'+suite['windows'],
        '--checkpoint',suite['model_root_server'],'--asset-manifest',source+'/'+suite['model_manifest'],
        '--data-directory',suite['data_root_server'],'--cache-directory',P+'/.local/formal-hf-'+args.suite,
        '--feature-cache',suite['cache_root_server']]
    for path in (suite['protocol'],suite['windows']):watch(path)
    watch(suite['model_manifest'],source+'/'+suite['model_manifest'])
    attempts=len(prior)+1
    if args.stage=='acceptance':
        if any(j['status']=='COMPLETED' for j in prior):raise ValueError('Accepted stage already completed; inspect outputs')
        output=P+f'/results/{ROUND}/{args.suite}/acceptance/attempt{attempts:02d}'
        configs=[f'configs/experiments/{ROUND}/{args.suite}_k{k}_seed17.json' for k in (128,256,64)]
        for path in configs:watch(path,source+'/'+path)
        argv=['--suite',args.suite,'--configs',*[source+'/'+x for x in configs],*common,
              '--oft-source',P+'/external/openvla-oft','--project-root',P,'--output',output]
        entry='scripts/verify_formal_acceptance.py'
        preflight='test ! -e '+shlex.quote(output)
    else:
        if args.segment not in range(500,5001,500):raise ValueError('Segment ends only at a registered500-update boundary')
        gates=read(ROOT/f'results/{ROUND}/{args.suite}/acceptance/root_review.json')
        if gates.get('status')!='passed':raise ValueError('Root must review real suite acceptance before training')
        accepted=next((j for j in jobs if j['job_id']==str(gates['job_id'])),None)
        if not accepted or accepted['status']!='COMPLETED' or accepted['exit_code']!='0:0':raise ValueError('Accepted engineering job not completed')
        gate_base=gates['output_relative']
        for filename in ('input_acceptance.json',f'f01_k{args.budget}.json',
                         'resume_acceptance.json','f03_calls.jsonl','acceptance_complete.json'):
            path=gate_base+'/'+filename;watch(path)
            if sha(ROOT/path)!=gates['files'][filename]:raise ValueError('Engineering receipt changed after root review')
        outrel=f'results/{ROUND}/{args.suite}/k{args.budget}/seed{args.seed}/training'
        output=P+'/'+outrel
        if prior:verify_remote_training_progress(outrel,prior)
        if (ROOT/outrel/'training_summary.json').exists():raise ValueError('This pair is already complete')
        completed_by_arm=[]
        for arm in ('A','B'):
            complete=ROOT/outrel/arm/'training_report.json'
            report=complete if complete.exists() else ROOT/outrel/arm/'progress_report.json'
            completed_by_arm.append(read(report)['training_updates_completed'] if report.exists() else 0)
        if all(value>=args.segment for value in completed_by_arm):
            raise ValueError('Requested segment already completed by both arms; choose next boundary')
        if max(completed_by_arm)>args.segment:
            raise ValueError('Segment would move a partially trained arm backwards')
        if prior and not args.resume:raise ValueError('Existing pair must resume, never reinitialize')
        watch(pair['path'],source+'/'+pair['path'])
        argv=['--config',source+'/'+pair['path'],*common,'--training-checkpoints',pair['checkpoint_root_server'],
            '--input-acceptance-report',P+'/'+gate_base+'/input_acceptance.json',
            '--acceptance-report',P+'/'+gate_base+f'/f01_k{args.budget}.json','--output',output,
            '--arm','both','--stop-after-updates',str(args.segment),'--max-wall-seconds',str(args.wall_seconds)]
        if args.resume:argv.append('--resume')
        entry='scripts/run_formal_future.py'
        preflight='test ! -e '+shlex.quote(output+'/training_summary.json')
        if not prior:preflight+=' && test ! -e '+shlex.quote(pair['checkpoint_root_server'])
    now=datetime.now(timezone.utc).isoformat()
    invocation={'schema':ROUND,'stage':args.stage,'stage_key':stage_key,'suite':args.suite,
        'source_root':source,'source_sha256':source_info['source_sha256'],'entrypoint':entry,'argv':argv,
        'watched_files':watched,'registered_utc':now,'registration_sha256':sha(ROOT/f'configs/experiments/{ROUND}.json'),
        'segment_end':args.segment if args.stage=='train' else None,'repair_record':str(args.repair_record) if args.repair_record else None}
    invrel=f'results/{ROUND}/invocations/{stage_key}_attempt{attempts:02d}.json';invpath=ROOT/invrel
    if invpath.exists():raise ValueError('Invocation already registered; inspect unknown outcome')
    write(invpath,invocation)
    remote('mkdir -p '+shlex.quote(P+f'/results/{ROUND}/invocations')+' && '+preflight)
    subprocess.run(['scp','-q',str(invpath),'tongji-cvpr:'+P+'/'+invrel],check=True)
    state['pending_submission']={'stage_key':stage_key,'invocation':invrel,'utc':now};write(STATE,state)
    command='cd '+shlex.quote(P)+' && sbatch --parsable --export='+shlex.quote('ALL,SOURCE_ROOT='+source+',INVOCATION='+P+'/'+invrel)+' '+shlex.quote(source+'/scripts/server/formal_main.slurm')
    answer=subprocess.run(SSH+[command],capture_output=True,text=True);jobid=answer.stdout.strip().split(';')[0]
    if answer.returncode or not jobid.isdigit():raise RuntimeError('Submission outcome unresolved; retain pending receipt: '+answer.stdout+answer.stderr)
    job={'job_id':jobid,'name':'cti-formal','experiment':ROUND,'mode':args.stage,'stage_key':stage_key,'suite':args.suite,
        'visual_tokens':args.budget if args.stage=='train' else None,'training_seed':args.seed if args.stage=='train' else None,
        'segment_end':invocation['segment_end'],'status':'SUBMITTED','gpus':1,'source_root':source,'source_sha256':source_info['source_sha256'],
        'run_root':output,'invocation':invrel,'invocation_sha256':sha(invpath),'submitted_utc':now,
        'purpose':'Registered formal-main stage; no final states or scientific settings expansion'}
    state['registered_jobs'].append(job);state['pending_submission']=None;state['stage']='formal_main_v2_'+args.stage
    state['current_round_cost']['registered_jobs']+=1;write(STATE,state)
    write(ROOT/f'results/{ROUND}/submissions/{jobid}.json',job)
    print(json.dumps(job,ensure_ascii=False))

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('status');q=sub.add_parser('submit')
    q.add_argument('--stage',choices=('acceptance','train'),required=True)
    q.add_argument('--suite',choices=('libero_10','libero_spatial','libero_object','libero_goal'),required=True)
    q.add_argument('--source-inventory',type=Path,required=True)
    q.add_argument('--budget',type=int,choices=(256,128,64),default=128);q.add_argument('--seed',type=int,choices=(17,23,41),default=17)
    q.add_argument('--segment',type=int,default=500);q.add_argument('--wall-seconds',type=int,default=12600)
    q.add_argument('--resume',action='store_true');q.add_argument('--repair-record',type=Path)
    args=p.parse_args()
    with supervisor_lock():
        state=read(STATE);jobs=refresh(state)
        if args.command=='status':print(json.dumps({'jobs':[{k:j.get(k) for k in ('job_id','mode','suite','status','elapsed_seconds','gpus')} for j in jobs],'cost':state['current_round_cost']},ensure_ascii=False))
        else:submit(args,state,jobs)

if __name__=='__main__':main()

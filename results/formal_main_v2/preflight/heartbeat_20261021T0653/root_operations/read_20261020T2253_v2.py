from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,sys,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261021T0653'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','read2253c')
g=load('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','read2253g')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);state=json.loads(sp.read_bytes());assert before=='63c74e7e591283409a792a7597fdb9bf99d1936ff1311e123bd687a83237a51f'
 cli=c.Slurm(timeout=60);jobs=state['registered_jobs'];ids=[str(j['job_id']) for j in jobs];assert len(set(ids))==len(ids) and all(x.isdigit() for x in ids)
 fmt='JobIDRaw,State,ExitCode,ElapsedRaw,AllocTRES,NodeList,JobName%128,Comment%128'
 acct=cli.run(['sacct','-n','-X','-P','-j',','.join(ids),'--format='+fmt]);assert acct.returncode==0,acct.stderr
 rows=c.parse_sacct(acct.stdout,set(ids));assert set(rows)==set(ids)
 idsq=[str(j['job_id']) for j in jobs if str(j['job_id']) not in rows or rows[str(j['job_id'])]['status'] not in c.TERMINAL or c.state_name(j.get('status','UNKNOWN')) not in c.TERMINAL]
 queue={};rawq='';absence=None
 if idsq:
  q=cli.run(['squeue','-h','-j',','.join(idsq),'-o','%i|%T|%k'])
  if q.returncode:
   # One exact completed engineering allocation can leave a stale RUNNING
   # registry row after Slurm purges it from its live queue. Never generalize.
   assert idsq==['3054127'] and q.returncode==1 and not q.stdout.strip() and q.stderr.strip()=='slurm_load_jobs error: Invalid job id specified'
   assert rows['3054127']['status'] in c.TERMINAL
   own=cli.run(['squeue','-h','-u','u15016','-o','%i|%T|%k']);assert own.returncode==0,own.stderr
   lines=[x.split('|') for x in own.stdout.splitlines() if x.strip()];assert all(len(x)==3 for x in lines)
   matched=[x for x in lines if x[0] in idsq];assert matched==[]
   again=cli.run(['sacct','-n','-X','-P','-j',','.join(idsq),'--format='+fmt]);assert again.returncode==0,again.stderr
   repeated=c.parse_sacct(again.stdout,set(idsq));assert repeated=={x:rows[x] for x in idsq}
   absence=dict(status='exact_terminal_ID_absent_from_successful_user_queue',requested_ids=idsq,original_returncode=q.returncode,original_stderr=q.stderr,original_stdout=q.stdout,user_queue_returncode=own.returncode,user_queue_matched_rows=matched,other_user_jobs_not_retained=True,second_terminal_sacct=again.stdout,only_job3054127=True,no_legacy_source_changed=True)
  else:
   rawq=q.stdout
   for line in rawq.splitlines():
    if not line.strip():continue
    cols=line.split('|');assert len(cols)==3 and cols[0] in idsq and cols[0] not in queue
    queue[cols[0]]=dict(status=c.state_name(cols[1]),comment=cols[2])
 obs=dict(rows=rows,queue=queue,raw_sacct=acct.stdout,raw_squeue=rawq,terminal_queue_absence_evidence=absence);cap=c.capacity(jobs,obs,'3034538')
 assert cap['unknown']==[] and cap['findings']==[] and len(cap['occupied'])<=8
 for j in state['registered_jobs']:g.check_observed_identity(j,obs['rows'][str(j['job_id'])],obs['queue'].get(str(j['job_id'])),c.TERMINAL)
 formal=[j for j in state['registered_jobs'] if j.get('experiment')=='formal_main_v2'];assert len(formal)==len({str(j['job_id']) for j in formal})
 secs=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in formal)
 with (R/'results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock').open('rb') as q:fcntl.flock(q,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(q,fcntl.LOCK_UN)
 out=dict(utc=datetime.now(timezone.utc).isoformat(),state_sha256=before,observation=obs,capacity=cap,formal_allocations=len(formal),allocated_GPU_seconds=secs,allocated_GPU_hours=secs/3600,controller_lease_released=True,pending=state['pending_submission'],Goal_job=next(j for j in formal if str(j['job_id'])=='3054127'))
 d=R/B;d.mkdir(parents=True,exist_ok=True);f=d/'live_observation.json';f.open('x').write(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n');assert h(sp)==before
 print(json.dumps({k:out[k] for k in ['utc','formal_allocations','allocated_GPU_seconds','allocated_GPU_hours','controller_lease_released','pending']}))
 print(json.dumps({'capacity':cap,'Goal_job':out['Goal_job'],'Goal_sacct':obs['rows']['3054127'],'controller':obs['rows']['3034538'],'observation_sha256':h(f)},ensure_ascii=False))
root=P/'results/formal_main_v2/engineering/goal_paired_input_gate_20261020T2156/attempt01';assert root.resolve()==root and not root.is_symlink()
rows=[]
if root.exists():
 for p in sorted(root.iterdir()):
  if p.is_file():
   row=dict(name=p.name,bytes=p.stat().st_size,sha256=h(p));rows.append(row)
   if p.suffix=='.json' and p.stat().st_size<100000:print(json.dumps({'artifact':row,'content':json.loads(p.read_bytes())},ensure_ascii=False))
  elif p.is_dir():rows.append(dict(directory=p.name,count=sum(1 for x in p.iterdir() if x.is_file())))
print(json.dumps({'artifact_root':str(root),'root_entries':rows},ensure_ascii=False))

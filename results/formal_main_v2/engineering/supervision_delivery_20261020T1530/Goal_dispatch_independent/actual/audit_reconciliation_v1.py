"""Private fake-only audit of exact-ACK reconciliation. Real Slurm/process operations forbidden."""
from pathlib import Path
import copy,contextlib,fcntl,hashlib,importlib.util,io,json,os,sys,types,traceback
R0=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P0=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=Path(__file__).resolve().parent
ENTRY=R0/'.local/reconcile_goal_probe_3050711_20261020T1530.py';PIN='b48af39a9c37056ae76da40295c64cff131733c815a11007cf90cd03698e4e3b';BASE='results/formal_main_v2/preflight/heartbeat_20261020T2330/Goal_t0_dispatch'
checks=[];records=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
def ref(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def check(v,label):
 if not v:raise AssertionError(label)
 checks.append(label)
def guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect'):raise RuntimeError('real subprocess/Slurm/network forbidden')
 if event=='open':
  p,mode,flags=args
  if isinstance(p,int):return
  p=Path(os.fsdecode(p)).absolute();w=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_APPEND|os.O_CREAT|os.O_TRUNC))
  if w:assert D in p.parents,'outside private write forbidden '+str(p)
  else:assert p.suffix not in ('.pt','.safetensors','.pth')
 if event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.symlink','os.link'):
  for v in args[:2] if event in ('os.rename','os.symlink','os.link') else args[:1]:
   p=Path(os.fsdecode(v)).absolute();assert p==D or D in p.parents,'outside private mutation'
sys.addaudithook(guard)
try:
 check(sha(ENTRY)==PIN,'exact reconciliation source')
 spec=importlib.util.spec_from_file_location('goal_reconcile_independent',ENTRY);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 (D/'reconciliation_reviewed_copy.py').write_bytes(ENTRY.read_bytes())
 # Direct real site-format regression exercises colon and slash keys without fake substitutions.
 raw=read(R0/BASE/'held_identity.json')['stdout'];token=read(R0/BASE/'pending.json')['request_token']
 check(sha(R0/BASE/'held_identity.json')=='b11ab37ac3a9f5b7df4ee7a45e123751731696bebf61b508fd214533f65da7db','exact actual held scontrol fixture')
 parsed=m.fields(raw);m.verify(parsed,token,True)
 check(parsed['Partition']=='L40' and parsed['AllocNode:Sid']=='logina04:3160037' and parsed['CPUs/Task']=='7' and parsed['TresPerNode']=='gres:gpu:l40:1','real site colon/slash keys and GPU TRES now verified')
 try:m.fields(raw+' JobId=3050711')
 except AssertionError:checks.append('duplicate job field rejected')
 else:raise AssertionError('duplicate field accepted')
 for key,value in [('JobId','3050712'),('Comment','foreign'),('JobState','RUNNING'),('Reason','Resources'),('Requeue','1'),('Restarts','1'),('TresPerNode','gres:gpu:l40:2'),('ExcNodeList','(null)'),('Partition','A800'),('TimeLimit','00:40:00'),('Command','/bin/false'),('WorkDir','/tmp')]:
  try:m.verify({**parsed,key:value},token,True)
  except AssertionError:checks.append('real fixture rejection '+key)
  else:raise AssertionError('bad held identity accepted '+key)
 c=m.c;g=m.g;baseatomic=c.atomic_json
 actualauth=(R0/m.old.AUTH).read_bytes();sources={name:(P0/m.old.BASE/'source'/name).read_bytes() for name in m.old.SOURCES};pend=read(R0/BASE/'pending.json');reservation=(R0/BASE/'reservation.json').read_bytes();ack=(R0/BASE/'submission_result.json').read_bytes()
 def rr(rc=0,text='',err=''):return types.SimpleNamespace(returncode=rc,stdout=text,stderr=err)
 class FakeSlurm:
  def __init__(self,root,runtime,mode,trace):self.root=root;self.runtime=runtime;self.mode=mode;self.trace=trace;self.commands=[];self.releases=0;self.shows=0
  def submit(self,*a):raise AssertionError('reconciliation must never submit')
  def run(self,argv):
   self.commands.append(argv);check(argv[0]=='scontrol' and argv[-1]=='3050711','only exact existing job scontrol '+self.mode)
   if argv[:3]==['scontrol','show','job']:
    self.shows+=1;self.trace.append('show'+str(self.shows))
    if (self.mode=='held_unknown' and self.shows==1) or (self.mode=='released_unknown' and self.shows==2):return rr(1,'','unavailable synthetic')
    text=raw.replace(str(P0),str(self.runtime))
    if self.shows==2:text=text.replace('JobState=PENDING','JobState=RUNNING').replace('Reason=JobHeldUser','Reason=None')
    if self.mode=='bad_held_token' and self.shows==1:text=text.replace(token,'foreign')
    if self.mode=='bad_released_token' and self.shows==2:text=text.replace(token,'foreign')
    return rr(0,text)
   if argv[:2]==['scontrol','release']:
    self.releases+=1;self.trace.append('release');s=read(self.root/m.old.STATE)
    check(self.releases==1 and len([j for j in s['registered_jobs'] if j['job_id']=='3050711'])==1,'registered exactly one original ACK before release '+self.mode)
    check(s['pending_submission']['status']=='registered_held_pending_release' and s['autonomous_training_v1']['reserved_GPU_slots']==0,'durable registry/pending/reservation transfer before release '+self.mode)
    if self.mode=='release_nonzero':return rr(1,'','synthetic release error')
    return rr()
   raise AssertionError('unauthorized Slurm command '+repr(argv))
  def observe(self,jobs):
   rows={};queue={}
   for j in jobs:
    jid=j['job_id'];cp=jid=='3034538';held=jid=='3050711';t=token if held else ('controller' if cp else 'fake:'+jid)
    rows[jid]=dict(job_id=jid,status='PENDING' if held else 'RUNNING',exit_code='0:0',gpus=0 if cp or held else 1,elapsed_seconds=0,allocation='cpu=1' if cp else 'gres/gpu=1',node='synthetic',scheduler_name=j['name'],scheduler_comment=t)
    queue[jid]={'status':rows[jid]['status'],'comment':t}
   if self.mode=='capacity_unknown':rows.pop('3100000')
   if self.mode=='queue_token_conflict':queue['3050711']['comment']='foreign'
   return dict(rows=rows,queue=queue,raw_sacct='synthetic',raw_squeue='synthetic')
 def case(name,mode='success',occupied=3,wrong_pending=None,wrong_reservation=False,owner_wrong=False,heldlease=True,duplicate=False,cas_fail=None):
  root=D/'fixtures'/name/'control';runtime=D/'fixtures'/name/'runtime';root.mkdir(parents=True);runtime.mkdir();m.R=m.old.R=root;m.P=m.old.P=runtime;m.old.S=runtime/'snapshots/formal_main_v2_run_564be0995e'
  for n,b in sources.items():p=runtime/m.old.BASE/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  for p in [root/m.old.AUTH,runtime/m.old.AUTH]:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(actualauth)
  for n,b in [('pending.json',json.dumps(pend,sort_keys=True,indent=2).encode()+b'\n'),('reservation.json',reservation),('submission_result.json',ack)]:p=root/m.B/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  review=root/'.local/goal_t0_dispatch_independent_20261020T1530/review_fake.json';put(review,dict(status='passed',entrypoint_sha256=PIN,blockers=[],synthetic=True,not_production_evidence=True))
  p=copy.deepcopy(pend);p.update(job_id='3050711',status='acknowledged_held_job_not_released')
  if wrong_pending:p.update(wrong_pending)
  jobs=[dict(job_id='3034538',name='controller',mode='controller',experiment='formal_main_v2',gpus=0,status='RUNNING')]
  for i in range(occupied):
   jid=str(3100000+i);jobs.append(dict(job_id=jid,name='fake-'+jid,mode='development',experiment='formal_main_v2',gpus=1,status='RUNNING',downstream_gateway=dict(request_token='fake:'+jid,actual_sbatch_argv=['sbatch','--comment=fake:'+jid])))
  if duplicate:jobs[-1]['stage_key']=m.old.STAGE
  lease=root/'results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock';lease.parent.mkdir(parents=True);lease.touch()
  owner={'owner_id':'synthetic-owner','coordinator_job_id':'3034538','lock':str(lease)};put(lease.parent/'owner.json',owner)
  state=dict(registered_jobs=jobs,pending_submission=p,autonomous_training_v1=dict(owner_id='bad' if owner_wrong else owner['owner_id'],controller_job_id='3034538',reserved_GPU_slots=0 if wrong_reservation else 1,reservation_root_record=pend['reservation'],root_submission_hold=None,blocked_pairs={},occupied_job_ids=[]),formal_main_progress={'trained_arms':64},current_round_cost={'allocated_gpu_seconds':100})
  put(root/m.old.STATE,state);before=copy.deepcopy(state);trace=[];cas=[0];sl=FakeSlurm(root,runtime,mode,trace)
  def atomic(path,value,expected):
   cas[0]+=1;trace.append('cas'+str(cas[0]))
   if cas[0]==cas_fail:raise RuntimeError('synthetic CAS failure')
   baseatomic(path,value,expected)
  m.c=types.SimpleNamespace(exclusive_lock=c.exclusive_lock,atomic_json=atomic,capacity=c.capacity,TERMINAL=c.TERMINAL,Slurm=lambda timeout:sl)
  lf=lease.open('rb')
  if heldlease:fcntl.flock(lf,fcntl.LOCK_EX|fcntl.LOCK_NB)
  oldargv=sys.argv;sys.argv=[str(ENTRY),'--review',review.relative_to(root).as_posix(),'--review-sha256',sha(review),'--root-reviewed-release'];error=None;output=io.StringIO()
  try:
   try:
    with contextlib.redirect_stdout(output):m.main()
   except (AssertionError,RuntimeError,ValueError,KeyError) as e:error=dict(type=type(e).__name__,message=str(e))
  finally:sys.argv=oldargv;fcntl.flock(lf,fcntl.LOCK_UN);lf.close()
  after=read(root/m.old.STATE);record=dict(name=name,synthetic=True,error=error,state_before=before,state_after=after,commands=sl.commands,releases=sl.releases,trace=trace,stdout=output.getvalue())
  put(root.parent/'case_record.json',record);records.append(record);return record
 a=case('success');check(a['error'] is None and a['releases']==1 and a['state_after']['pending_submission'] is None,'only exact confirmed existing job release clears pending')
 check(a['trace']==['show1','cas1','release','show2','cas2'],'held validation then registry CAS then release then confirmation CAS')
 check(a['state_after']['formal_main_progress']==a['state_before']['formal_main_progress'] and a['state_after']['current_round_cost']==a['state_before']['current_round_cost'],'science and costs remain unchanged until controller actual accounting')
 check(a['state_after']['registered_jobs'][-1]['job_id']=='3050711' and c.job_pair(a['state_after']['registered_jobs'][-1]) is None,'existing ACK registered engineering only, not training pair')
 for name,kw in [('wrong_job',{'wrong_pending':{'job_id':'3050712'}}),('wrong_status',{'wrong_pending':{'status':'intent_persisted_before_sbatch'}}),('wrong_token',{'wrong_pending':{'request_token':'foreign'}}),('wrong_reservation',{'wrong_reservation':True}),('wrong_owner',{'owner_wrong':True}),('no_lease',{'heldlease':False}),('duplicate_stage',{'duplicate':True}),('held_unknown',{'mode':'held_unknown'}),('bad_held_token',{'mode':'bad_held_token'}),('capacity8_plusheld',{'occupied':8}),('capacity_unknown',{'mode':'capacity_unknown'}),('queue_token_conflict',{'mode':'queue_token_conflict'})]:
  a=case(name,**kw);check(a['error'] is not None and a['releases']==0,'blocked before release '+name);check(a['state_after']==a['state_before'],'pending/reservation retained '+name)
 a=case('capacity7_plusheld',occupied=7);check(a['error'] is None and a['releases']==1,'existing7 plus heldACK reaches cap8 without double reservation')
 for mode in ['release_nonzero','released_unknown','bad_released_token']:
  a=case(mode,mode=mode);check(a['error'] is not None and a['releases']==1,'one exact release only '+mode);check(a['state_after']['pending_submission']['job_id']=='3050711' and a['state_after']['pending_submission']['status']=='registered_held_pending_release','uncertain release remains pending '+mode)
 for n in [1,2]:
  a=case('cas_failure_'+str(n),cas_fail=n);check(a['error'] is not None and a['releases']==n-1 and a['state_after']['pending_submission'] is not None,'CAS failure retains pending without automatic release retry '+str(n))
 check(all(all(cmd[0]=='scontrol' for cmd in a['commands']) for a in records),'no fake sbatch/cancel/foreign scheduler action in any scenario')
 check(sha(ENTRY)==PIN,'reconciliation source unchanged')
 report=dict(schema='formal_main_v2',kind='independent_exact_ACK_reconciliation_CPU_review',status='passed',entrypoint_sha256=PIN,blockers=[],checks=checks,check_count=len(checks),cases=len(records),job_id='3050711',submission_scope='No new job; only root one release of exact originally ACKed held job after registry CAS',actual_GPU_evidence=False,real_Slurm_operations=0,canonical_mutations=0,state_mutations=0,original_parser_error_retained=True,real_format_fixture=ref(R0/BASE/'held_identity.json'),source=ref(ENTRY),limitations=['Fake scheduler tests are CPU evidence only; root must preserve actual held/accounting/ACK/release confirmation.','Any unknown or failed release stays pending. No second submission, automatic retry or original trial replacement.'])
 put(D/'reconciliation_review.json',report);print(json.dumps(dict(review=ref(D/'reconciliation_review.json'),checks=len(checks),cases=len(records))))
except BaseException as exc:
 put(D/'reconciliation_audit_failure.json',dict(status='failed',error=str(exc),type=type(exc).__name__,traceback=traceback.format_exc(),checks=checks,cases_completed=len(records)));raise

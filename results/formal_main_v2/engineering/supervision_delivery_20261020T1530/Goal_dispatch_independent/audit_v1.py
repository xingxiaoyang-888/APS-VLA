"""Independent dispatch CPU audit. Uses only private fixtures and fake Slurm; no real submit."""
from pathlib import Path
from contextlib import contextmanager
import ast,copy,fcntl,hashlib,importlib.util,json,os,sys,traceback,types
R0=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P0=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=Path(__file__).resolve().parent
ENTRY=R0/'.local/goal_t0_dispatch_20261020T1530.py';PIN='45dc2e6483578c8f332820d03386ca0cc20f3b7736ec74ad50d2e46b4d538b5d'
checks=[];cases=[];writes=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def put(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,sort_keys=True,indent=2);f.write('\n')
def check(ok,label):
 if not ok:raise AssertionError(label)
 checks.append(label)
def ref(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def load(p,name):
 spec=importlib.util.spec_from_file_location(name,p);v=importlib.util.module_from_spec(spec);sys.modules[name]=v;spec.loader.exec_module(v);return v
def io_guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect'):raise RuntimeError('NO REAL PROCESS/NETWORK/SLURM allowed in independent audit')
 if event=='open':
  name,mode,flags=args
  if isinstance(name,int):return
  p=Path(os.fsdecode(name)).absolute();iswrite=(isinstance(mode,str) and any(t in mode for t in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if iswrite:
   assert D in p.parents,'outside-private write forbidden '+str(p);writes.append(str(p))
  else:assert p.suffix not in ('.pt','.pth','.safetensors'),'weight read forbidden'
 if event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.symlink','os.link'):
  for s in args[:2] if event in ('os.rename','os.symlink','os.link') else args[:1]:
   p=Path(os.fsdecode(s)).absolute();assert p==D or D in p.parents,'outside-private mutation forbidden'
sys.addaudithook(io_guard)
try:
 check(sha(ENTRY)==PIN,'candidate exact source SHA')
 src=ENTRY.read_bytes();(D/'dispatch_reviewed_copy.py').write_bytes(src)
 module=load(ENTRY,'independent_goal_dispatch')
 cpath=R0/'scripts/ops/formal_autonomous_training_v1/controller.py';gpath=R0/'scripts/ops/formal_action_deployment_v1/gateway.py'
 check(sha(cpath)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','exact controller source pin')
 check(sha(gpath)=='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','exact gateway identity checker source pin')
 c=load(cpath,'goal_dispatch_independent_real_controller');g=load(gpath,'goal_dispatch_independent_real_gateway')
 for name,h in module.SOURCES.items():check(sha(P0/module.BASE/'source'/name)==h,'actual published source '+name)
 actualauth=read(R0/module.AUTH)
 check(sha(R0/module.AUTH)==sha(P0/module.AUTH)=='016ddbdc5d638e6271debb124d305dfdd7ccd3ef3d5f9816ac9fe13f4c3a3dda','actual root authorization identical R/P')
 check(actualauth['best_effort_application_timeout_not_hard_bound'] and actualauth['does_not_replay_original_200_trial_history'] and actualauth['automatic_retry'] is False,'actual auth records limitations and no retry')
 for role in ('root_review','independent_review'):
  rr=actualauth[role];check(sha(rr['path'])==rr['sha256'],'actual '+role+' bytes')
  rv=read(rr['path']);check(rv['status']=='passed' and rv['entrypoint_sha256']==module.ENTRY_SHA and rv['config_sha256']==module.CONFIG_SHA,'actual '+role+' identities')
 # Pure parser/resource validation. Real scontrol is never invoked.
 good=dict(JobId='99001',JobName=module.NAME,Comment='test-token',Requeue='0',TimeLimit='00:30:00',Partition='L40',Account='p_p15016',TresPerNode='gres/gpu:l40:1',ExcNodeList='gpu4020',JobState='PENDING',Reason='JobHeldUser')
 text=' '.join(k+'='+v for k,v in good.items());check(module.job_fields(text)==good,'scontrol parser exact ordinary fields')
 module.verify_held_or_released(good,'99001','test-token',True);checks.append('held identity accepted only exact job/token/resources')
 for key,val in [('JobId','99002'),('JobName','foreign'),('Comment','other'),('Requeue','1'),('TimeLimit','01:00:00'),('Partition','A800'),('Account','other'),('TresPerNode','gres/gpu:l40:2'),('ExcNodeList','(null)'),('JobState','RUNNING'),('Reason','Resources')]:
  bad={**good,key:val}
  try:module.verify_held_or_released(bad,'99001','test-token',True)
  except RuntimeError:checks.append('held reject '+key)
  else:raise AssertionError('held mismatch accepted '+key)
 for status,reason in [('RUNNING','None'),('PENDING','Priority'),('CONFIGURING','None')]:module.verify_held_or_released({**good,'JobState':status,'Reason':reason},'99001','test-token',False)
 checks.append('released identity exact live statuses accepted')
 for status,reason in [('PENDING','JobHeldUser'),('UNKNOWN','None'),('COMPLETED','None')]:
  try:module.verify_held_or_released({**good,'JobState':status,'Reason':reason},'99001','test-token',False)
  except RuntimeError:checks.append('unconfirmed release retained '+status+' '+reason)
  else:raise AssertionError('unconfirmed release accepted')
 def outcome(rc=0,out='',err=''):return types.SimpleNamespace(returncode=rc,stdout=out,stderr=err)
 class FakeSlurm:
  def __init__(self,root,state,mode,trace):self.root=root;self.state=state;self.mode=mode;self.trace=trace;self.submits=0;self.releases=0;self.shows=0;self.commands=[];self.token=None
  def observe(self,jobs):
   rows={};queue={}
   for j in jobs:
    jid=j['job_id'];status=j['status'];cp=jid=='3034538';token='ctl' if cp else 'existing:'+jid
    rows[jid]=dict(job_id=jid,status=status,exit_code='0:0',gpus=0 if cp or status=='PENDING' else 1,elapsed_seconds=20,allocation='cpu=1' if cp else 'gres/gpu=1',node='cpu001' if cp else 'gpu4001',scheduler_name=j['name'],scheduler_comment=token)
    queue[jid]=dict(status=status,comment=token)
   if self.mode=='missing_row':rows.pop('3100000')
   if self.mode=='unknown_status':rows['3100000']['status']='UNKNOWN'
   if self.mode=='queue_conflict':queue['3100000']['comment']='foreign'
   if self.mode=='name_conflict':rows['3100000']['scheduler_name']='foreign'
   if self.mode=='controller_not_running':rows['3034538']['status']='PENDING';queue['3034538']['status']='PENDING'
   if self.mode=='controller_has_gpu':rows['3034538']['gpus']=1
   return dict(rows=rows,queue=queue,raw_sacct='SYNTHETIC',raw_squeue='SYNTHETIC')
  def submit(self,argv):
   self.submits+=1;self.commands.append(argv);self.trace.append('fake_sbatch')
   check(self.submits==1,'no second sbatch in '+self.mode)
   state=read(self.root/module.STATE);pending=state['pending_submission'];self.token=pending['request_token']
   check(pending['actual_sbatch_argv']==argv and state['autonomous_training_v1']['reserved_GPU_slots']==1,'durable exact pending+reservation before sbatch '+self.mode)
   check(read(self.root/module.OUT/'pending.json')['request_token']==self.token,'immutable pending exists before sbatch '+self.mode)
   check('--hold' in argv and '--no-requeue' in argv and '--exclude=gpu4020' in argv and '--time=00:30:00' in argv and '--gres=gpu:l40:1' in argv,'submitted fixed held 1GPU30min/no-requeue/exclusion '+self.mode)
   if self.mode=='submit_raise':raise TimeoutError('synthetic sbatch network uncertainty')
   if self.mode=='submit_nonzero':return outcome(1,'','synthetic sbatch failure')
   if self.mode=='submit_ambiguous':return outcome(0,'Submitted batch job 99001\n')
   if self.mode=='duplicate_ack':return outcome(0,'3100000\n')
   return outcome(0,'99001;synthetic-cluster\n')
  def run(self,argv):
   self.commands.append(argv)
   if argv[0]==sys.executable:
    check(self.submits==0,'metadata prepare before submit '+self.mode)
    if self.mode=='preflight_failure':return outcome(1,'','synthetic metadata failure')
    return outcome(0,json.dumps({'status':'cpu_prepared_not_GPU_run'}))
   if argv[:3]==['scontrol','show','job']:
    self.shows+=1;self.trace.append('show'+str(self.shows));check(argv[-1]=='99001','show exact ACK job only '+self.mode)
    if self.mode=='held_unknown' and self.shows==1:return outcome(1,'','synthetic unavailable')
    if self.mode=='release_show_unknown' and self.shows==2:return outcome(1,'','synthetic unavailable')
    fields={**good,'Comment':self.token,'JobState':'PENDING' if self.shows==1 else 'RUNNING','Reason':'JobHeldUser' if self.shows==1 else 'None'}
    if self.mode=='held_wrong_token' and self.shows==1:fields['Comment']='foreign'
    if self.mode=='released_wrong_token' and self.shows==2:fields['Comment']='foreign'
    return outcome(0,' '.join(k+'='+v for k,v in fields.items()))
   if argv[:2]==['scontrol','release']:
    self.releases+=1;self.trace.append('release');check(argv[-1]=='99001','release exact ACK job only '+self.mode)
    state=read(self.root/module.STATE);job=next(x for x in state['registered_jobs'] if x['job_id']=='99001')
    check(state['pending_submission']['status']=='registered_held_pending_release' and state['autonomous_training_v1']['reserved_GPU_slots']==0 and job['downstream_gateway']['request_token']==self.token,'ACK job durably registered before release '+self.mode)
    if self.mode=='release_nonzero':return outcome(1,'','synthetic release failure')
    return outcome()
   raise AssertionError('unauthorized command '+repr(argv))
 def case(label,mode='success',occupied=3,pending=False,reserved=0,hold=None,owner_mismatch=False,leaseheld=True,duplicate=False,cas_fail=None):
  base=D/'fixtures'/label;root=base/'control';runtime=base/'runtime';root.mkdir(parents=True);runtime.mkdir()
  module.R=root;module.P=runtime;module.S=runtime/'snapshots/formal_main_v2_run_564be0995e'
  # All source copies are exact and private; fake auth has clearly fabricated fields.
  for name in module.SOURCES:
   dst=runtime/module.BASE/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((P0/module.BASE/'source'/name).read_bytes())
  auth=copy.deepcopy(actualauth);auth['synthetic']=True;auth['not_production_evidence']=True
  for role in ('root_review','independent_review'):
   pp=runtime/module.BASE/(role+'.json');put(pp,dict(status='passed',config_sha256=module.CONFIG_SHA,entrypoint_sha256=module.ENTRY_SHA,synthetic=True,role=role));auth[role]=ref(pp)
  put(root/module.AUTH,auth);put(runtime/module.AUTH,auth);ah=sha(root/module.AUTH)
  review=root/'.local/goal_t0_dispatch_independent_20261020T1530/review_fake.json';put(review,dict(status='passed',entrypoint_sha256=PIN,blockers=[],synthetic=True,not_production_evidence=True));rr=dict(path=review.relative_to(root).as_posix(),sha256=sha(review))
  lease=root/'results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock';lease.parent.mkdir(parents=True,exist_ok=True);lease.touch();owner=dict(owner_id='synthetic-owner',coordinator_job_id='3034538',lock=str(lease),activation_sha256='synthetic')
  put(lease.parent/'owner.json',owner)
  jobs=[dict(job_id='3034538',name='cpu-controller',mode='controller',gpus=0,experiment='formal_main_v2',status='RUNNING')]
  for i in range(occupied):
   jid=str(3100000+i);modej=['train','development','engineering'][i%3]
   j=dict(job_id=jid,name='existing-'+jid,experiment='formal_main_v2',mode=modej,gpus=1,status='PENDING' if i%2 else 'RUNNING',downstream_gateway={'request_token':'existing:'+jid,'actual_sbatch_argv':['sbatch','--comment=existing:'+jid]})
   if modej=='train':j.update(suite='libero_spatial',visual_tokens=256,training_seed=[17,23,41][i//3],segment_end=5000)
   jobs.append(j)
  if duplicate:jobs[-1]['stage_key']=module.STAGE
  state=dict(registered_jobs=jobs,pending_submission={'synthetic_prior':True} if pending else None,autonomous_training_v1=dict(owner_id='wrong' if owner_mismatch else owner['owner_id'],controller_job_id='3034538',root_submission_hold=hold,reserved_GPU_slots=reserved,blocked_pairs={},occupied_job_ids=[],completed_pairs={},verified_pairs={}),formal_main_progress=dict(trained_arms=64,expected_arms=72),current_round_cost={'allocated_gpu_seconds':100})
  put(root/module.STATE,state);before=copy.deepcopy(state);trace=[];sl=FakeSlurm(root,state,mode,trace);cas=[0]
  def atomic(path,value,expected):
   cas[0]+=1;trace.append('cas'+str(cas[0]))
   if cas_fail==cas[0]:raise RuntimeError('synthetic CAS state drift')
   c.atomic_json(path,value,expected)
  cc=types.SimpleNamespace(exclusive_lock=c.exclusive_lock,capacity=c.capacity,TERMINAL=c.TERMINAL,atomic_json=atomic)
  h=lease.open('rb')
  if leaseheld:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB)
  cwd=Path.cwd();os.chdir(root);err=None;ret=None
  try:
   try:ret=module.submit_once(cc,g,sl,ah,rr)
   except (RuntimeError,TimeoutError,KeyError) as e:err={'type':type(e).__name__,'message':str(e)}
  finally:os.chdir(cwd);fcntl.flock(h,fcntl.LOCK_UN);h.close()
  after=read(root/module.STATE)
  rec=dict(label=label,mode=mode,synthetic=True,error=err,result=ret,submissions=sl.submits,releases=sl.releases,trace=trace,commands=sl.commands,state_before=before,state_after=after)
  put(base/'case_record.json',rec);cases.append(rec);return rec
 success=case('success')
 check(success['error'] is None and success['submissions']==success['releases']==1,'one successful fake submit/release')
 check(success['state_after']['pending_submission'] is None and success['state_after']['autonomous_training_v1']['reserved_GPU_slots']==0,'only exact confirmed release clears pending and consumes reservation')
 job=success['state_after']['registered_jobs'][-1]
 check(job['mode']=='engineering' and c.job_pair(job) is None and job['scientific_trials']==0 and not job['final_states_opened'],'engineering job excluded from scientific/training counts')
 check(g.registered_comment(job)==job['downstream_gateway']['request_token'],'new registry interoperates with original gateway comment identity')
 check(success['state_before']['formal_main_progress']==success['state_after']['formal_main_progress'] and success['state_before']['current_round_cost']==success['state_after']['current_round_cost'],'dispatch does not change science counts or GPU accounting prematurely')
 check(success['trace']==['cas1','fake_sbatch','cas2','show1','cas3','release','show2','cas4'],'exact pending ACK held-registry release confirmed transaction order')
 # Re-enter the very same successful fixture: duplicate registry/immutable markers must refuse.
 oldroot=module.R;module.R=D/'fixtures/success/control';module.P=D/'fixtures/success/runtime';module.S=module.P/'snapshots/formal_main_v2_run_564be0995e'
 root=module.R;review=root/'.local/goal_t0_dispatch_independent_20261020T1530/review_fake.json';rr={'path':review.relative_to(root).as_posix(),'sha256':sha(review)};sl=FakeSlurm(root,read(root/module.STATE),'success',[]);cwd=Path.cwd();os.chdir(root)
 try:
  try:module.submit_once(c,g,sl,sha(root/module.AUTH),rr)
  except RuntimeError as e:check('already registered' in str(e) and sl.submits==0,'repeat after success rejected before another sbatch')
  else:raise AssertionError('duplicate attempt allowed')
 finally:os.chdir(cwd)
 # Capacity uses every mode including pending requested GPUs, with confirmed CPU exemption.
 for label,kwargs in [('capacity8',dict(occupied=8)),('existing_pending',dict(pending=True)),('reservation_present',dict(reserved=1)),('hold_present',dict(hold={'enabled':True})),('owner_mismatch',dict(owner_mismatch=True)),('lease_not_held',dict(leaseheld=False)),('duplicate_stage',dict(duplicate=True)),('missing_row',dict(mode='missing_row')),('unknown_status',dict(mode='unknown_status')),('queue_conflict',dict(mode='queue_conflict')),('name_conflict',dict(mode='name_conflict')),('controller_not_running',dict(mode='controller_not_running')),('controller_has_gpu',dict(mode='controller_has_gpu')),('preflight_failure',dict(mode='preflight_failure'))]:
  row=case(label,**kwargs);check(row['error'] is not None and row['submissions']==row['releases']==0,'pre-submit fail closed '+label)
  check(row['state_after']==row['state_before'],'no canonical-style state mutation before rejection '+label)
 edge=case('capacity7',occupied=7);check(edge['error'] is None and edge['result']['maximum_gpu_occupancy']==8,'all-mode seven existing including pending +one exactly reaches cap8')
 for mode in ['submit_raise','submit_nonzero','submit_ambiguous','duplicate_ack','held_unknown','held_wrong_token','release_nonzero','release_show_unknown','released_wrong_token']:
  row=case(mode,mode=mode);check(row['error'] is not None and row['submissions']==1,'single uncertain/failed submit attempt retained '+mode)
  check(row['state_after']['pending_submission'] is not None,'durable pending never cleared on failure '+mode)
  check(row['releases']==(1 if mode.startswith('release') else 0),'release never issued before exact held ACK checks '+mode)
 for n in [1,2,3,4]:
  row=case('cas_fail_'+str(n),cas_fail=n)
  check(row['error'] is not None and row['submissions']==(0 if n==1 else 1),'CAS failure cannot cause resubmit '+str(n))
  if n>1:check(row['state_after']['pending_submission'] is not None,'post-submit CAS failure retains prior durable pending '+str(n))
 # Controller counts new engineering allocation once and does not treat it as train pair.
 row=success['state_after'];j=row['registered_jobs'][-1];sl=FakeSlurm(D,row,'success',[]);snap=sl.observe(row['registered_jobs']);snap['rows'][j['job_id']]['scheduler_comment']=g.registered_comment(j);snap['queue'][j['job_id']]['comment']=g.registered_comment(j)
 cap=c.capacity(row['registered_jobs'],snap,'3034538');check(len(cap['occupied'])==4 and not cap['findings'] and not cap['unknown'],'original capacity counts new engineering once')
 check(sum(r['gpus']*r['elapsed_seconds'] for r in snap['rows'].values())==60,'original allocation accounting uses actual GPU allocations including engineering once')
 # Exactly original behavior keeps suspended accounting pending jobs reserved as requests but zero allocation cost.
 check(sha(ENTRY)==PIN,'reviewed dispatch source unchanged after CPU tests')
 realstate=R0/'results/experiment_supervisor/state.json'
 report=dict(schema='formal_main_v2',kind='independent_root_engineering_dispatch_CPU_review',status='passed',entrypoint_sha256=PIN,blockers=[],reviewed_by='independent_agent_devplans_audit_20261020_1418',checks=checks,check_count=len(checks),cases=len(cases),real_slurm_submissions=0,real_slurm_operations=0,real_GPU_evidence=False,canonical_mutations=0,state_mutations=0,source=ref(ENTRY),controller=ref(cpath),gateway=ref(gpath),limitations=['CPU fake-Slurm tests do not establish current production slot capacity, actual scontrol field values or successful submission. Root must execute once and retain actual ACK/held/release evidence.','Any uncertain or post-submit failure retains durable pending for root reconciliation; no retry/cancel is authorized.','Global writer lock is held through metadata prepare and Slurm calls; healthy GPU jobs continue but controller state writes wait briefly.'])
 put(D/'independent_review.json',report);put(D/'CPU_cases_index.json',dict(synthetic=True,case_records=[ref(D/'fixtures'/x['label']/'case_record.json') for x in cases]))
 print(json.dumps(dict(status='passed',review=ref(D/'independent_review.json'),checks=len(checks),cases=len(cases)),ensure_ascii=False))
except BaseException as e:
 put(D/'audit_v1_failure.json',dict(status='failed',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),checks=checks,cases_done=len(cases)));print(traceback.format_exc());raise

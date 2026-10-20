"""Independent fake-only audit. All candidate main paths use private copies and no process/network API."""
from pathlib import Path
import ast,contextlib,copy,difflib,fcntl,hashlib,importlib.util,io,json,os,sys,time,traceback,types
R0=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P0=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=R0/'.local/goal_prefix58_independent_20261020T1825';O=D/'dispatch_v3_attempt02'
EP=R0/'.local/goal_prefix58_dispatch_20261020T1825_v3.py';PIN='97276272c91bddc53bfa63b74410af3823d0098359e29cec7a04e65809877b01';OUTER=R0/'.local/goal_prefix58_repair_20261020T1825/outer_revision03';OPIN='da3e094a98104d08735d6da6a180b326f79ae077e710880aa9117b39b911e31f'
checks=[];cases=[];started=time.process_time()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def put(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,sort_keys=True,indent=2);f.write(chr(10))
def ref(p):return dict(path=Path(p).relative_to(R0).as_posix(),sha256=sha(p),bytes=Path(p).stat().st_size)
def ck(v,label):
 if not v:raise AssertionError(label)
 checks.append(label)
def load(p,n):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect'):raise RuntimeError('real process/Slurm/network forbidden')
 if event=='open':
  p,mode,flags=args
  if isinstance(p,int):return
  p=Path(os.fsdecode(p)).absolute();w=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_APPEND|os.O_CREAT|os.O_TRUNC))
  if w:assert D in p.parents,'outside private write '+str(p)
  else:assert p.suffix not in ('.pt','.safetensors','.pth'),'weight I/O forbidden in fake dispatcher audit'
 if event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.symlink','os.link'):
  for value in args[:2] if event in ('os.rename','os.symlink','os.link') else args[:1]:
   p=Path(os.fsdecode(value)).absolute();assert p==D or D in p.parents,'outside private mutation'
sys.addaudithook(guard)
try:
 O.mkdir(exist_ok=False);ck(sha(EP)==PIN and sha(OUTER/'entry.py')==OPIN,'exact dispatcher v3 and accepted outer v3')
 m=load(EP,'private_prefix58_dispatch_v3');e=load(OUTER/'entry.py','private_prefix58_outer_for_dispatch')
 (O/'dispatcher_reviewed_copy.py').write_bytes(EP.read_bytes())
 for version in ['','_v2']:
  p=R0/('.local/goal_prefix58_dispatch_20261020T1825'+version+'.py');(O/('dispatcher'+(version or '_v1')+'.py')).write_bytes(p.read_bytes())
 (O/'v2_to_v3.diff').write_text(''.join(difflib.unified_diff((O/'dispatcher_v2.py').read_text().splitlines(True),EP.read_text().splitlines(True))))
 fp=R0/'results/formal_main_v2/preflight/heartbeat_20261020T2330/Goal_t0_dispatch/held_identity.json';ck(sha(fp)=='b11ab37ac3a9f5b7df4ee7a45e123751731696bebf61b508fd214533f65da7db','actual prior L40 held fixture identity')
 raw=read(fp)['stdout'];(O/'actual_site_format_fixture.json').write_bytes(fp.read_bytes());parsed=m.fields(raw)
 ck(parsed['Partition']=='L40' and parsed['AllocNode:Sid']=='logina04:3160037' and parsed['CPUs/Task']=='7' and parsed['TresPerNode']=='gres:gpu:l40:1','site colon/slash fields decoded without contamination')
 try:m.fields(raw+' JobId=3050711')
 except RuntimeError:ck(True,'duplicate Slurm key rejected')
 else:raise AssertionError('duplicate key accepted')
 fields={**parsed,'JobName':m.NAME,'Comment':'synthetic-token','Command':str(P0/m.PKG/'run.slurm'),'WorkDir':str(m.S)};m.actual_identity(fields,'3050711','synthetic-token',True)
 for key,value in [('JobId','000'),('JobName','foreign'),('Comment','foreign'),('Requeue','1'),('Restarts','1'),('TimeLimit','00:31:00'),('Partition','A800'),('Account','foreign'),('QOS','foreign'),('ExcNodeList','(null)'),('NumCPUs','8'),('MinMemoryNode','128G'),('TresPerNode','gres:gpu:l40:2'),('Command','/bin/false'),('WorkDir','/tmp'),('JobState','RUNNING'),('Reason','Resources')]:
  try:m.actual_identity({**fields,key:value},'3050711','synthetic-token',True)
  except RuntimeError:ck(True,'held identity rejects '+key)
  else:raise AssertionError('bad actual identity accepted '+key)
 ct=R0/'scripts/ops/formal_autonomous_training_v1/controller.py';gw=R0/'scripts/ops/formal_action_deployment_v1/gateway.py'
 ck(sha(ct)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363' and sha(gw)=='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','original controller and gateway pinned')
 c=load(ct,'private_dispatch_original_controller');g=load(gw,'private_dispatch_original_gateway');atomic0=c.atomic_json
 failure=R0/'results/formal_main_v2/preflight/heartbeat_20261020T2218/3049679_root_review_failure_20261020T1418.json'
 ck(sha(failure)=='49b226c91f99cd9fd3584ab645992244794f4d720e0128d9ab693e82bcca6793','original failed scientific review retained')
 ss=read(R0/m.STATE);jj=next(x for x in ss['registered_jobs'] if str(x['job_id'])=='3049679');gs=[x for x in ss['formal_main_progress']['nonLong_development_submissions_1317'] if str(x.get('job_id'))=='3049679'];ck(jj['status']=='COMPLETED' and jj['exit_code']=='0:0' and jj['elapsed_seconds']==2034 and len(gs)==1 and gs[0]['terminal_review_status']=='HOLD_initial_observation_mismatch' and gs[0]['completed_trials_accepted']==0 and gs[0]['retained_unaccepted_trials']==200,'real original job is Slurm completed while200 scientific trials remain HOLD')
 put(O/'original_facts.json',{'job':jj,'scientific_disposition':gs[0],'root_failure':ref(failure)})
 package0=read(OUTER/'package_manifest.json');config0=read(OUTER/'config.json');blobs={n:(OUTER/Path(n).name).read_bytes() for n in package0['files']}
 def response(rc=0,text='',err=''):return types.SimpleNamespace(returncode=rc,stdout=text,stderr=err)
 def case(name,mode='success',occupied=2,cas_fail=None):
  box=O/'fixtures'/name;root=box/'control';runtime=box/'runtime';root.mkdir(parents=True);runtime.mkdir();m.R=root;m.P=runtime;m.S=runtime/'snapshots/formal_main_v2_run_564be0995e'
  for attr in ['P','S','R']:setattr(e,attr,{'P':runtime,'S':m.S,'R':root}[attr])
  e.BASE=runtime/m.BASE;e.OUTPUT=e.BASE/'attempt01';e.AUTH=e.BASE/'root_authorization.json';e.DISPATCH=e.BASE/'held_dispatch_record.json';e.RESERVATION=e.BASE/'reservation.json';e.ORIGINAL=runtime/'results/formal_main_v2/invocations/libero_goal_development_5185766bb353c8e6_attempt01.json';put(e.ORIGINAL,{'synthetic':True})
  config=json.loads(json.dumps(config0).replace(str(P0),str(runtime)));config['schema_note']='Synthetic fake dispatcher fixture; not production evidence'
  for base in [root,runtime]:
   for rel,b in blobs.items():
    p=base/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
   (base/m.PKG/'config.json').write_text(json.dumps(config,sort_keys=True))
  package=copy.deepcopy(package0);package['files'][m.PKG+'/config.json']=sha(runtime/m.PKG/'config.json')
  for base in [root,runtime]:put(base/m.PKG/'package_manifest.json',package)
  mh=sha(runtime/m.PKG/'package_manifest.json');ch=sha(runtime/m.PKG/'config.json');refs={}
  for role in ['root','independent']:
   rp=runtime/m.BASE/(role+'_readiness.json');put(rp,dict(schema='formal_main_v2',kind='goal_prefix58_single_attempt_CPU_readiness',status='passed',reviewed_by=role,version=e.VERSION,package_manifest_sha256=mh,config_sha256=ch,original_chain_preserved=True,observer_gaps_fixed=True,real_GPU_acceptance=False,scientific_release=False,synthetic=True));refs[role]=dict(path=str(rp),sha256=sha(rp))
  auth=dict(schema='formal_main_v2',kind='root_goal_prefix58_single_attempt_authorization',version=e.VERSION,status='approved',reviewed_by='root',stage_key=e.STAGE,config_sha256=ch,package_manifest_sha256=mh,entrypoint_sha256=OPIN,maximum_gpu_jobs=1,maximum_attempts=1,maximum_wall_seconds=1800,counts_against_8_GPU_slots=True,automatic_retry=False,scientific_release=False,original_goal200_HOLD=True,new_Goal_science_HOLD=True,maximum_trials=58,resources=e.RESOURCES,dispatch_record_path=str(e.DISPATCH),reservation_path=str(e.RESERVATION),root_review=refs['root'],independent_review=refs['independent'])
  for base in [root,runtime]:put(base/m.AUTH,auth)
  ah=sha(root/m.AUTH);token='cti-goal-prefix58-v2:'+ah
  if mode=='source_changed':(runtime/m.PKG/'observer_v3.py').write_bytes(b'synthetic changed source')
  if mode=='auth_changed':(runtime/m.AUTH).write_text('{}')
  if mode=='readiness_changed':(runtime/m.BASE/'independent_readiness.json').write_text('{}')
  if mode=='existing_attempt':(runtime/m.BASE/'attempt01').mkdir()
  review=root/'.local/goal_prefix58_independent_20261020T1825/synthetic_review.json';put(review,dict(status='passed',entrypoint_sha256=PIN,blockers=[],synthetic=True))
  fp2=root/failure.relative_to(R0);fp2.parent.mkdir(parents=True);fp2.write_bytes(failure.read_bytes())
  jobs=[dict(job_id='3034538',name='controller',experiment='formal_main_v2',mode='controller',gpus=0,status='COMPLETED',exit_code='0:0'),dict(job_id='3049679',name='cti-formal-downstream',experiment='formal_main_v2',mode='development',gpus=1,status='COMPLETED',exit_code='0:0')]
  for i in range(occupied):
   jid=str(3100000+i);jobs.append(dict(job_id=jid,name='fake-'+jid,experiment='formal_main_v2',mode=['train','development','collect','engineering'][i%4],gpus=1,status='RUNNING',suite='libero_spatial',visual_tokens=256,training_seed=[17,23,41][(i//4)%3],downstream_gateway=dict(request_token='fake:'+jid)))
  lease=root/'results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock';lease.parent.mkdir(parents=True);lease.touch();owner=dict(owner_id='synthetic-owner',coordinator_job_id='3034538',lock=str(lease));put(lease.parent/'owner.json',owner)
  state=dict(registered_jobs=jobs,pending_submission=None,autonomous_training_v1=dict(owner_id=owner['owner_id'],controller_job_id='3034538',reserved_GPU_slots=0,root_submission_hold=None,completed_pairs={str(i):{'synthetic':True} for i in range(36)},blocked_pairs={},occupied_job_ids=[]),formal_main_progress=dict(root_and_independent_completed_arms=72,test_opened=False,global_release_created=False,completed_final_trials=0,nonLong_development_submissions_1317=[copy.deepcopy(gs[0])],new_action_development_verified_by_job={}),current_round_cost=dict(allocated_gpu_seconds=12345))
  if mode=='pending':state['pending_submission']={'unknown':True}
  if mode=='reservation':state['autonomous_training_v1']['reserved_GPU_slots']=1
  if mode=='root_hold':state['autonomous_training_v1']['root_submission_hold']={'hold':True}
  if mode=='training_incomplete':state['formal_main_progress']['root_and_independent_completed_arms']=70
  if mode=='blocked_pairs':state['autonomous_training_v1']['blocked_pairs']={'pair':'failed'}
  if mode=='final_open':state['formal_main_progress']['test_opened']=True
  if mode=='duplicate_stage':jobs[-1]['stage_key']=m.STAGE
  if mode=='owner_changed':state['autonomous_training_v1']['owner_id']='foreign'
  if mode=='original_wrongly_accepted':state['formal_main_progress']['new_action_development_verified_by_job']={'3049679':{}}
  if mode=='original_hold_lost':state['formal_main_progress']['nonLong_development_submissions_1317'][0]['terminal_review_status']='passed'
  put(root/m.STATE,state);before=copy.deepcopy(state);trace=[];counts={'submit':0,'release':0,'show':0,'cas':0}
  class FakeSlurm:
   def observe(self,registered):
    trace.append('observe');rows={};queue={}
    for job in registered:
     jid=job['job_id'];status=job['status'];row=dict(status=status,exit_code='0:0',gpus=job['gpus'],scheduler_name=job['name'],scheduler_comment='fake:'+jid,elapsed_seconds=0);rows[jid]=row
     if status=='RUNNING':queue[jid]={'status':'RUNNING','comment':'fake:'+jid}
    if mode=='controller_running':rows['3034538']['status']='RUNNING'
    if mode=='original_failed':rows['3049679']['status']='FAILED'
    if mode=='capacity_unknown':rows.pop(registered[-1]['job_id'])
    if mode=='queue_conflict':queue[registered[-1]['job_id']]['comment']='foreign'
    return dict(rows=rows,queue=queue)
   def submit(self,argv):
    counts['submit']+=1;trace.append('submit');st=read(root/m.STATE)
    ck(counts['submit']==1 and st['pending_submission']['status']=='intent_persisted_before_sbatch' and st['autonomous_training_v1']['reserved_GPU_slots']==1 and (root/m.OUT/'pending.json').exists(),'pending/reservation durable before exactly one fake sbatch '+name)
    ck(argv[:4]==['sbatch','--hold','--parsable','--no-requeue'] and '--exclude=gpu4020' in argv and '--time=00:30:00' in argv and '--gres=gpu:l40:1' in argv and argv[-1]==str(runtime/m.PKG/'run.slurm'),'exact one L40 30min held no-requeue command '+name)
    if mode=='submit_raise':raise RuntimeError('synthetic lost submit response')
    if mode=='submit_unknown':return response(0,'unknown response')
    if mode=='duplicate_ack':return response(0,'3049679\n')
    return response(0,'3999999\n')
   def run(self,argv):
    ck(argv[0]=='scontrol' and argv[-1]=='3999999','only exact fake ACK can be managed '+name)
    if argv[:2]==['scontrol','release']:
     counts['release']+=1;trace.append('release');st=read(root/m.STATE)
     ck(counts['release']==1 and st['pending_submission']['status']=='registered_held_pending_release' and sum(j['job_id']=='3999999' for j in st['registered_jobs'])==1 and e.DISPATCH.exists() and st['autonomous_training_v1']['reserved_GPU_slots']==0,'registry CAS and exact P held record precede one release '+name)
     if mode=='release_unknown':return response(1,'','synthetic release uncertainty')
     return response()
    assert argv[:3]==['scontrol','show','job'];counts['show']+=1;trace.append('show'+str(counts['show']))
    if mode=='held_unknown' and counts['show']==1:return response(1)
    if mode=='released_unknown' and counts['show']==2:return response(1)
    f={**parsed,'JobId':'3999999','JobName':m.NAME,'Comment':token,'Command':str(runtime/m.PKG/'run.slurm'),'WorkDir':str(m.S)}
    if counts['show']==2:f.update(JobState='RUNNING',Reason='None')
    if mode=='held_token_changed' and counts['show']==1:f['Comment']='foreign'
    if mode=='released_token_changed' and counts['show']==2:f['Comment']='foreign'
    return response(0,' '.join(k+'='+v for k,v in f.items()))
  sl=FakeSlurm()
  def atomic(path,value,expected):
   counts['cas']+=1;trace.append('cas'+str(counts['cas']))
   if counts['cas']==cas_fail:raise RuntimeError('synthetic CAS failure')
   atomic0(path,value,expected)
  cfake=types.SimpleNamespace(Slurm=lambda timeout:sl,exclusive_lock=c.exclusive_lock,atomic_json=atomic,capacity=c.capacity,TERMINAL=c.TERMINAL)
  def fake_module(n,pin,module_name):
   if n=='scripts/ops/formal_autonomous_training_v1/controller.py':return cfake
   if n=='scripts/ops/formal_action_deployment_v1/gateway.py':return g
   if n==m.PKG+'/entry.py':ck(pin==OPIN,'exact outer module requested '+name);return e
   raise AssertionError('unexpected import')
  m.module=fake_module;e.prepare_original=lambda: ({},None,{},None)
  argv0=sys.argv;cwd=Path.cwd();sys.argv=[str(EP),'--authorization-sha256',ah,'--dispatch-review',review.relative_to(root).as_posix(),'--dispatch-review-sha256',sha(review),'--submit'];os.chdir(root);err=None;stdout=io.StringIO();lf=lease.open('rb')
  if mode=='lease_held':fcntl.flock(lf,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   try:
    with contextlib.redirect_stdout(stdout):m.main()
   except (RuntimeError,ValueError,AssertionError,KeyError,TypeError) as ex:err={'type':type(ex).__name__,'message':str(ex)}
  finally:sys.argv=argv0;os.chdir(cwd);fcntl.flock(lf,fcntl.LOCK_UN);lf.close()
  after=read(root/m.STATE);result=dict(name=name,synthetic=True,not_production_evidence=True,error=err,counts=counts,trace=trace,state_before=before,state_after=after,stdout=stdout.getvalue());put(box/'case_record.json',result);cases.append(result)
  ck(after['formal_main_progress']==before['formal_main_progress'] and after['current_round_cost']==before['current_round_cost'] and after['autonomous_training_v1']['completed_pairs']==before['autonomous_training_v1']['completed_pairs'],'science/cost/completions not changed '+name)
  return result
 a=case('success');ck(a['error'] is None and a['counts']['submit']==a['counts']['release']==1 and a['state_after']['pending_submission'] is None,'successful exact fake lifecycle completes once')
 ck(a['trace']==['observe','cas1','submit','cas2','show1','cas3','release','show2','cas4'],'durable pending/ACK/register/held/release/CAS ordering')
 a=case('capacity7',occupied=7);ck(a['error'] is None and a['counts']['submit']==1,'mixed all-mode seven occupied plus one reaches8')
 pre=['pending','reservation','root_hold','training_incomplete','blocked_pairs','final_open','duplicate_stage','owner_changed','lease_held','capacity_unknown','queue_conflict','controller_running','original_failed','original_wrongly_accepted','original_hold_lost','source_changed','auth_changed','readiness_changed','existing_attempt']
 for mode in pre:
  a=case(mode,mode);ck(a['error'] is not None and a['counts']['submit']==a['counts']['release']==0 and a['state_after']==a['state_before'],'fail closed before submit '+mode)
 a=case('capacity8',occupied=8);ck(a['error'] is not None and a['counts']['submit']==0,'all-mode capacity8 forbids ninth')
 for mode in ['submit_raise','submit_unknown','duplicate_ack','held_unknown','held_token_changed','release_unknown','released_unknown','released_token_changed']:
  a=case(mode,mode);ck(a['error'] is not None and a['counts']['submit']==1 and a['state_after']['pending_submission'] is not None,'ambiguous submit/ACK/held/release preserves pending without resend '+mode)
  ck(a['counts']['release']==(1 if mode.startswith('release') else 0),'no release before registered held identity '+mode)
 for n in [1,2,3,4]:
  a=case('CAS_failure_'+str(n),cas_fail=n);ck(a['error'] is not None and a['counts']['submit']==(0 if n==1 else 1) and a['counts']['release']==(1 if n==4 else 0),'CAS failure stops next side effect '+str(n));ck(n==1 or a['state_after']['pending_submission'] is not None,'CAS failure retains intent/ACK '+str(n))
 ck(sha(EP)==PIN and sha(OUTER/'entry.py')==OPIN,'candidate sources unchanged')
 report=dict(schema='formal_main_v2',kind='independent_Goal_prefix58_dispatch_CPU_review',status='passed',entrypoint_sha256=PIN,blockers=[],source=ref(EP),outer_source=ref(OUTER/'entry.py'),checks=checks,check_count=len(checks),cases=len(cases),negative_cases=sum(x['error'] is not None for x in cases),CPU_seconds=time.process_time()-started,real_Slurm_operations=0,real_GPU_execution=False,canonical_state_changes=0,actual_site_fixture=ref(fp),original_scientific_failure=ref(failure),source_closure_checked=True,capacity_limit_all_GPU_modes=8,maximum_GPU_jobs=1,maximum_wall_seconds=1800,automatic_retry=False,Goal200_HOLD=True,limitations=['Fake scheduler lifecycle tests are CPU evidence only. Root must archive actual unique ACK, held identity, registration, release and final scheduler evidence.','Inherited reset may swallow application exceptions; Slurm 30min is authoritative. Any ambiguous submission or release remains pending for exact reconciliation; no automatic resend.','Original science, weights, final values and real GPU runtime were not executed by this dispatcher audit.'])
 put(O/'independent_review.json',report);print(json.dumps({'review':ref(O/'independent_review.json'),'checks':len(checks),'cases':len(cases),'CPU_seconds':report['CPU_seconds']}))
except BaseException as ex:
 if O.exists():put(O/'audit_failure.json',{'status':'failed','error':str(ex),'type':type(ex).__name__,'traceback':traceback.format_exc(),'checks_completed':len(checks),'cases_completed':len(cases)})
 raise

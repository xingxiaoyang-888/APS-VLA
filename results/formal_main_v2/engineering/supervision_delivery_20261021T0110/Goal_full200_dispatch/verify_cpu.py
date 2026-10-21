from pathlib import Path
from contextlib import contextmanager
import argparse,copy,hashlib,importlib.util,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_full200_dispatch_20261021T0110'
p=D/'dispatch.py';sp=importlib.util.spec_from_file_location('_goal_full200_private_dispatch_CPU',p)
g=importlib.util.module_from_spec(sp);sys.modules[sp.name]=g;exec(compile(p.read_bytes(),str(p),'exec'),g.__dict__)
positive=[];negative=[]
def ok(v,label):
 if not v:raise AssertionError(label)
 positive.append(label)

def no(fn,label):
 try:fn()
 except BaseException as e:
  if isinstance(e,SystemExit):raise
  negative.append(dict(check=label,error_type=type(e).__name__,error=str(e)));return e
 raise AssertionError('incorrectly accepted '+label)

class Interruption(BaseException):pass
def bundle():
 ah='a'*64;inv=dict(CPU_fixture=True)
 raw=g.canonical(inv)+b'\n'
 ah=g.sha(raw)
 return dict(authorization=inv,authorization_sha256=ah,invocation_bytes=raw,authorization_ref=dict(path=g.AUTH,bytes=len(raw),sha256=ah),
  token='cti-goal-full200-v1:'+ah,comment='cti-goal-full200-v1:'+ah,sources={'CPU_fixture':True},
  runtime_package={'files':{g.PROD+'/config.json':'b'*64,g.PROD+'/entry.py':'c'*64}},
  admission={'prepared_utc':'2026-10-21T01:10:00+00:00'},admission_ref=dict(path=g.ADMISSION,bytes=1,sha256='d'*64))
class Fake:
 def __init__(self,fail=None):
  self.state={'pending_submission':None,'autonomous_training_v1':{'reserved_GPU_slots':0},
    'registered_jobs':[{'job_id':'3053440','original':'retained'}]}
  self.facts={};self.calls=[];self.fail=fail;self.triggered=False;self.sbatch_calls=0;self.release_calls=0
  self.held=True;self.published=False;self.cases=0;self.B=bundle()
 def at(self,label):
  self.calls.append(label)
  if self.fail==label and not self.triggered:self.triggered=True;raise Interruption(label)
 @contextmanager
 def lock(self):self.at('lock');yield
 def read_state(self):return copy.deepcopy(self.state),g.sha(g.canonical(self.state))
 def cas(self,state,expected):
  self.at('cas_before_'+str(self.cases));self.cases+=1
  if g.sha(g.canonical(self.state))!=expected:raise ValueError('CAS changed')
  self.state=copy.deepcopy(state);return g.sha(g.canonical(self.state))
 def fact(self,name,value):
  self.at('fact_'+name)
  if name in self.facts:raise ValueError('immutable fact already exists')
  self.facts[name]=copy.deepcopy(value)
 def fact_read(self,name):return copy.deepcopy(self.facts[name])
 def fact_exists(self,name):return name in self.facts
 def observe(self,state,allow_job=None):
  self.at('observe_'+('new' if allow_job else 'old'))
  return dict(observation={'rows':{}},derived={'occupied':[allow_job] if allow_job else [],'allocated_formal_GPU_seconds':6713})
 def absent(self):
  self.at('absent')
  if self.facts or self.published:raise ValueError('prior audit or invocation')
 def revalidate(self):self.at('revalidate')
 def publish_reservation(self):
  self.at('publish')
  if self.published:raise ValueError('prior invocation')
  self.published=True
 def submit(self,argv):
  self.sbatch_calls+=1;self.at('submit')
  return dict(returncode=0,stdout='9900001\n',stderr='',actual_sbatch_argv=argv)
 def actual(self,jid,held):
  self.at('actual_held' if held else 'actual_released')
  if held!=self.held:raise ValueError('held/released state incompatible; no resend')
  return dict(fields={'JobId':jid,'JobState':'PENDING' if held else 'RUNNING'},CPU_fixture=True)
 def release(self,jid):
  self.release_calls+=1;self.at('release_before_effect');self.held=False;self.at('release_after_effect')
  return dict(returncode=0,stdout='',stderr='',argv=['scontrol','release',jid])
 def dispatch_proof(self,jid,state,version):
  self.at('dispatch_proof')
  if self.state['registered_jobs'][-1]['job_id']!=jid:raise ValueError('dispatch before unique registration')
  return {'CPU_fixture':True}
 def committed(self,jid,state,version,obs):
  self.at('committed');state['pending_submission']=None
  return self.cas(state,version)
def transaction_checks():
 b=bundle();f=Fake();result=g.Transaction(f,b).run(submit=True)
 ok(result['status']=='submitted_once_registered_then_released' and f.sbatch_calls==f.release_calls==1,'one held submission and one release')
 ok(f.state['registered_jobs'][0]=={'job_id':'3053440','original':'retained'} and f.state['pending_submission'] is None,'historical row preserved and pending only cleared after release evidence')
 order=f.calls
 ok(order.index('fact_pending.json')<order.index('publish')<order.index('submit')<order.index('fact_sbatch_result.json')<order.index('fact_registered_held.json')<order.index('release_before_effect'),'durable pending before submit and registration before release')
 ok(f.state['registered_jobs'][1]['downstream_gateway']['request_token']==b['comment']
  and f.state['registered_jobs'][1]['name']==f.state['registered_jobs'][1]['job_name']==g.NAME,'common supervisor original comment/name preserved')
 no(lambda:g.Transaction(f,b).run(submit=True),'repeat existing output/audit rejected')
 ok(f.sbatch_calls==1,'repeat did not resubmit')
 for phase in ['publish','submit','fact_sbatch_result.json','actual_held','observe_new','fact_registered_held.json',
  'fact_release_attempt.json','release_before_effect','release_after_effect','fact_release_result.json',
  'actual_released','dispatch_proof','committed','cas_before_1','cas_before_2','cas_before_3']:
  f=Fake(phase);no(lambda f=f:g.Transaction(f,b).run(submit=True),'BaseException stops '+phase)
  ok(f.state['pending_submission'] is not None,'durable pending retained '+phase)
  calls=f.sbatch_calls
  no(lambda f=f:g.Transaction(f,b).run(submit=True),'no new submit after '+phase)
  ok(f.sbatch_calls==calls,'no repeat sbatch '+phase)
 f=Fake('submit');no(lambda:g.Transaction(f,b).run(submit=True),'lost original ACK setup')
 no(lambda:g.Transaction(f,b).run(reconcile=True),'cannot invent missing original ACK')
 ok(f.sbatch_calls==1 and f.release_calls==0,'unknown ACK never resubmitted/released')
 f=Fake('actual_held');no(lambda:g.Transaction(f,b).run(submit=True),'saved ACK unresolved held setup')
 r=g.Transaction(f,b).run(reconcile=True)
 ok(r['status']=='submitted_once_registered_then_released' and f.sbatch_calls==1 and f.release_calls==1,'unique saved original ACK can register held and release once')
 f=Fake('fact_registered_held.json');no(lambda:g.Transaction(f,b).run(submit=True),'registered held crash setup')
 r=g.Transaction(f,b).run(reconcile=True)
 ok(f.sbatch_calls==1 and f.release_calls==1,'registered-before-release crash reconciles without resubmission')
 f=Fake('release_before_effect');no(lambda:g.Transaction(f,b).run(submit=True),'release uncertainty before effect setup')
 no(lambda:g.Transaction(f,b).run(reconcile=True),'unknown release stillheld not resent')
 ok(f.release_calls==1 and f.state['pending_submission'] is not None,'release not resent when actual state held')
 f=Fake('release_after_effect');no(lambda:g.Transaction(f,b).run(submit=True),'release lost response setup')
 r=g.Transaction(f,b).run(reconcile=True)
 ok(r['status']=='original_ACK_reconciled_no_resubmission' and f.release_calls==1 and f.sbatch_calls==1,'lost release response reconciles actual live state without resend')
 f=Fake('actual_held');no(lambda:g.Transaction(f,b).run(submit=True),'ACK tampering fixture')
 f.facts['sbatch_result.json']['actual_sbatch_argv'][3]='--requeue'
 no(lambda:g.Transaction(f,b).run(reconcile=True),'saved original argv mismatch')
 f=Fake('fact_registered_held.json');no(lambda:g.Transaction(f,b).run(submit=True),'registered identity tamper fixture')
 f.state['registered_jobs'][1]['source_sha256']='0'*64
 no(lambda:g.Transaction(f,b).run(reconcile=True),'registered source drift cannot be reconciled by ACK alone')
 f=Fake();t=g.Transaction(f,b);r=t.run(submit=False)
 ok(r['status']=='read_only_ready_not_submitted' and not f.published and f.sbatch_calls==f.release_calls==0 and not f.facts,'read-only transaction no state/file/Slurm mutation')
 no(lambda:t.run(submit=True),'transaction instance single use')
 for answer in [dict(returncode=1,stdout='9900001\n'),dict(returncode=0,stdout=''),dict(returncode=0,stdout='9900001\n9900002\n'),dict(returncode=0,stdout='Submitted batch job 9900001'),dict(returncode=0,stdout='3053440\n')]:
  no(lambda answer=answer:g.parse_ack(answer,{'3053440'}),'ambiguous/nonzero/old ACK rejected '+repr(answer))
 for key,value in [('mode',g.MODE),('logical_trial_id',g.CELL),('stage_key',g.STAGE),('invocation',g.INV),('run_root',str(g.P/g.OUT)),('name',g.NAME),('slurm_comment','cti-goal-full200-v1:unknown')]:
  ok(g.duplicate({key:value,'status':'FAILED'}),'incomplete prior row blocks '+key)
 f=Fake();f.state['autonomous_training_v1']['pending_submission']={'unknown_ACK':True}
 no(lambda:g.Transaction(f,b).run(submit=True),'nested autonomous unknown ACK refuses before submission')
 ok(f.sbatch_calls==0 and f.release_calls==0,'nested pending creates no allocation')
 args=g.sbatch_argv(b)
 ok('--hold' in args and '--no-requeue' in args and '--exclude=gpu4020' in args and args[-1]==str(g.P/g.PROD/'run.slurm'),'exact held/requeue/resources/entry argv')
def actual_observation_checks():
 from types import SimpleNamespace
 c=g.controller()
 def raw(status='COMPLETED',seconds=7,name='test',comment='',gpu=1):
  return f'9900101|{status}|0:0|{seconds}|cpu=7,gres/gpu={gpu}|gpu4013|{name}|{comment}\n'
 class Scheduler:
  def __init__(self,answers):self.answers=list(answers);self.argv=[]
  def run(self,argv):
   self.argv.append(argv)
   answer=self.answers.pop(0)
   return SimpleNamespace(returncode=answer[0],stdout=answer[1],stderr=answer[2])
 jobs=[dict(job_id='9900101',status='RUNNING',gpus=1)]
 a=Scheduler([(0,raw(),''),(0,raw(),'')]);got=g.actual_observation(c,a,jobs)
 ok(len(a.argv)==2 and all(v[0]=='sacct' for v in a.argv) and got['queue']=={} and jobs[0]['status']=='RUNNING','stale registry terminal requires two full actual rows without rewriting original registry')
 for second,label in [(raw(seconds=8),'cost'),(raw(status='RUNNING'),'status'),(raw(name='foreign'),'name'),(raw(comment='other'),'token'),(raw(gpu=0),'GPU'),('','missing')]:
  a=Scheduler([(0,raw(),''),(0,second,'')])
  no(lambda a=a:g.actual_observation(c,a,jobs),'second complete terminal confirmation rejects '+label)
 a=Scheduler([(0,raw(status='UNKNOWN'),'')]);no(lambda:g.actual_observation(c,a,jobs),'unknown actual state refuses live projection')
 a=Scheduler([(0,'','')]);no(lambda:g.actual_observation(c,a,jobs),'missing original accounting refuses projection')
 a=Scheduler([(0,raw(status='RUNNING'),''),(1,'','Invalid job id specified')]);no(lambda:g.actual_observation(c,a,jobs),'squeue error never treated as empty queue')
 a=Scheduler([(0,raw(status='RUNNING'),''),(0,'','')]);no(lambda:g.actual_observation(c,a,jobs),'active queue disappearance stops projection')
 a=Scheduler([(0,raw(status='RUNNING'),''),(0,'9900102|RUNNING|\n','')]);no(lambda:g.actual_observation(c,a,jobs),'foreign active queue ID refuses projection')
 a=Scheduler([(0,raw(status='RUNNING'),''),(0,'9900101|RUNNING|\n','')]);got=g.actual_observation(c,a,jobs)
 ok(got['queue']['9900101']['status']=='RUNNING' and a.argv[-1][3]=='9900101','actual live IDs alone feed live queue query')
def projection_checks(live):
 c=g.controller();state=live['state_for_projection'];result=live['result']
 obs=result['observation'];details=result['details'];derived=g.normalized_projection(c,state,obs,details)
 ok({k:v for k,v in derived.items() if k!='original_GPU_seconds'}=={k:v for k,v in result['derived'].items() if k!='original_GPU_seconds'},'real all-mode projection rebuilt from saved registered identities and actual Slurm rows')
 ok(result['lease']['lease_available_measured'] and result['lease']['owner_sha256']==g.OWNER_SHA,'real released lease measured without changing owner/inode')
 # Actual raw sacct is re-parsed; typed JSON alone is not scheduler evidence.
 parsed=c.parse_sacct(obs['raw_sacct'],set(obs['rows']))
 ok(parsed==obs['rows'],'all registered raw sacct rows independently reparsed')
 initial=c.parse_sacct(obs['initial_raw_sacct'],set(obs['rows']))
 confirmation=obs['terminal_confirmation']
 if confirmation:
  confirm=c.parse_sacct(confirmation['raw_sacct'],set(obs['rows']))
  terminals={v for v in initial if initial[v]['status'] in c.TERMINAL}
  ok(set(confirmation['all_initial_terminal_rows_confirmed'])==terminals and all(initial[v]==confirm[v] for v in terminals),'actual full terminal rows stable across two saved queries')
 for key,value in [('pending_submission',{'unknown_ACK':True}),('root_submission_hold',{'reason':'HOLD'}),('reserved_GPU_slots',8),('blocked_pairs',{'x':'failure'}),('controller_job_id','999')]:
  bad=copy.deepcopy(state);bad['autonomous_training_v1'][key]=value
  no(lambda bad=bad:g.normalized_projection(c,bad,obs,details),'actual state controller/reservation '+key)
 bad=copy.deepcopy(state);bad['pending_submission']={'unknown_ACK':True}
 no(lambda:g.normalized_projection(c,bad,obs,details),'foreign root pending blocks projection')
 for key,value in [('test_opened',True),('completed_final_trials',1),('global_release_created',True),('root_and_independent_completed_arms',71)]:
  bad=copy.deepcopy(state);bad['formal_main_progress'][key]=value
  no(lambda bad=bad:g.normalized_projection(c,bad,obs,details),'science matrix/sealed gate '+key)
 bad=copy.deepcopy(obs);bad['rows'].pop(g.OLD_IDS[0])
 no(lambda:g.normalized_projection(c,state,bad,details),'missing accounting cannot normalize')
 for field,value in [('status','FAILED'),('exit_code','1:0'),('elapsed_seconds',839),('gpus',0)]:
  bad=copy.deepcopy(obs);bad['rows']['3054127'][field]=value
  no(lambda bad=bad:g.normalized_projection(c,state,bad,details),'old cost/failure identity '+field)
 bad=copy.deepcopy(state);bad['registered_jobs'].append(copy.deepcopy(bad['registered_jobs'][0]))
 no(lambda:g.normalized_projection(c,bad,obs,details),'duplicate actual register ID')
 for j in state['registered_jobs']:
  if str(j['job_id']) in details:
   jid=str(j['job_id'])
   for field in ['Comment','JobName','Account','Partition','StdOut','TresPerNode','JobState']:
    bad=copy.deepcopy(details);bad[jid][field]='wrong'
    no(lambda bad=bad:g.normalized_projection(c,state,obs,bad),'real active identity '+field)
   bad=copy.deepcopy(state)
   target=next(j for j in bad['registered_jobs'] if str(j['job_id'])==jid);target['pair_id']=g.PAIR
   no(lambda:g.normalized_projection(c,bad,obs,details),'same pair occupied across modes')
   bad=copy.deepcopy(state);next(j for j in bad['registered_jobs'] if str(j['job_id'])==jid)['suite']='libero_goal'
   no(lambda:g.normalized_projection(c,bad,obs,details),'other Goal allocation occupied across modes')
   break
 # Independent held-job fields validate exact stdout, resources and original argv.
 b=bundle();job=g.job_record('9900001',b,g.sbatch_argv(b));f=g.expected_live(job)
 f.update(Requeue='0',TimeLimit='02:00:00',ExcNodeList='gpu4020',NumCPUs='7',MinMemoryNode='64G',
  Command=str(g.P/g.PROD/'run.slurm'),WorkDir=str(g.S),Restarts='0',QOS=g.RESOURCES['qos'],
  TresPerNode='gres:gpu:l40:1',JobState='PENDING',Reason='JobHeldUser')
 g.validate_new_identity(job,b,f,True);ok(True,'exact held original ACK identity valid')
 for key in f:
  bad=dict(f);bad[key]='wrong'
  no(lambda bad=bad:g.validate_new_identity(job,b,bad,True),'held identity mutation '+key)
 for flag in ('RUNNING','COMPLETED'):
  bad=dict(f);bad['JobState']=flag
  no(lambda bad=bad:g.validate_new_identity(job,b,bad,True),'cannot register already-running unexpected initial submission '+flag)
 no(lambda:g.fields('JobId=1 JobId=2'),'duplicate scontrol key')
 no(lambda:g.fields('JobId=1\nJobId=2\n'),'multiple scontrol jobs')
 no(lambda:g.relative('../sealed/states.json'),'path traversal and sealed')
 no(lambda:g.relative('results/sealed/panel.json'),'sealed payload')
 return derived
def extra_scope_checks(live):
 from types import SimpleNamespace
 c=g.controller();state=copy.deepcopy(live['state_for_projection']);obs=copy.deepcopy(live['result']['observation']);details=copy.deepcopy(live['result']['details'])
 assert not details
 b=bundle();base=g.sbatch_argv(b)
 for i in range(9):
  jid=str(9910000+i);name='cti-fixture-other-'+str(i);argv=[('--job-name='+name if x.startswith('--job-name=') else '--comment=cti-other-token-'+str(i) if x.startswith('--comment=') else x) for x in base]
  j=dict(job_id=jid,name=name,job_name=name,status='PENDING',exit_code='0:0',gpus=1,experiment='formal_main_v2',mode='CPU_capacity_fixture',downstream_gateway=dict(actual_sbatch_argv=argv))
  state['registered_jobs'].append(j)
  obs['rows'][jid]=dict(job_id=jid,status='PENDING',exit_code='0:0',elapsed_seconds=0,allocation='cpu=7',node='None',gpus=0,scheduler_name=name,scheduler_comment='cti-other-token-'+str(i))
  obs['queue'][jid]=dict(status='PENDING',comment='cti-other-token-'+str(i))
  d=g.expected_live(j);d.update(JobState='PENDING',TresPerNode='gres:gpu:l40:1');details[jid]=d
  if i==6:
   x=g.normalized_projection(c,state,obs,details);ok(len(x['occupied'])==7,'seven pending0GPU requested allocations leave exactly eighth slot')
   for field,value in [('pair_id',g.PAIR),('suite','libero_goal'),('run_root',str(g.P/g.OUT))]:
    modified=copy.deepcopy(state);modified['registered_jobs'][-1][field]=value
    no(lambda modified=modified:g.normalized_projection(c,modified,obs,details),'Goal occupied exclusion '+field)
  if i>=7:no(lambda:g.normalized_projection(c,state,obs,details),'no ninth slot with allmode pending requested GPUs '+str(i+1))
 # Exact own pending is only allowed with its registered original ID.
 ownstate=copy.deepcopy(live['state_for_projection']);ownobs=copy.deepcopy(live['result']['observation']);owndetails={}
 j=g.job_record('9920001',b,g.sbatch_argv(b));ownstate['registered_jobs'].append(j)
 ownstate['pending_submission']=dict(kind='Goal_full200_durable_pending',stage_key=g.STAGE,logical_trial_id=g.CELL,known_job_id='9920001')
 ownobs['rows']['9920001']=dict(job_id='9920001',status='PENDING',exit_code='0:0',elapsed_seconds=0,allocation='cpu=7',node='None',gpus=0,scheduler_name=g.NAME,scheduler_comment=b['comment'])
 ownobs['queue']['9920001']=dict(status='PENDING',comment=b['comment'])
 d=g.expected_live(j);d.update(JobState='PENDING',TresPerNode='gres:gpu:l40:1');owndetails['9920001']=d
 ok(g.normalized_projection(c,ownstate,ownobs,owndetails,allow_job='9920001')['occupied']==['9920001'],'only exact held own pending can reconcile before release')
 for field in ['kind','stage_key','logical_trial_id','known_job_id']:
  modified=copy.deepcopy(ownstate);modified['pending_submission'][field]='wrong'
  no(lambda modified=modified:g.normalized_projection(c,modified,ownobs,owndetails,allow_job='9920001'),'own pending identity mutation '+field)
 source=R/'.local/goal_full200_author_20261021T0110_v2/package'
 pp=source/'entry.py';spec=importlib.util.spec_from_file_location('_goal_entry_schema_CPU',pp)
 e=importlib.util.module_from_spec(spec);sys.modules[spec.name]=e;exec(compile(pp.read_bytes(),str(pp),'exec'),e.__dict__)
 config=json.loads((source/'config.json').read_bytes());e.validate_config(config);ok(True,'actual prospective entry full200 config guard called')
 for field,value in [('maximum_trials',58),('maximum_trials',1000),('unique_development_states',40),('maximum_total_control_steps',60001),('maximum_total_policy_queries',7601),('method_ids',['A256_seed17']),('final_evaluation_enabled',True),('automatic_retry',True)]:
  v=copy.deepcopy(config);v[field]=value
  no(lambda v=v:e.validate_config(v),'actual full200 runtime scope rejects '+field+str(value))
 res=g.reservation(b)
 held=dict(schema=g.EXPERIMENT,kind='root_goal_full200_held_dispatch',status='held_registered_before_release',
  stage_key=g.STAGE,job_id='9920001',authorization=dict(path=str(g.P/g.AUTH),sha256=b['authorization_sha256']),
  request_token=b['token'],capacity_limit_all_GPU_modes=8,reserved_slots=1,maximum_attempts=1,
  new_submissions=1,no_requeue=True,scientific_release=False,resources=g.RUNTIME_RESOURCES,
  occupied_job_ids=['9920001'],state_after_sha256='b'*64,reservation=dict(path=str(g.P/g.RESERVATION),sha256=g.sha(g.canonical(res)+b'\n')))
 e.validate_dispatch(held,res,b['authorization'],b['authorization_sha256'],'9920001',held['reservation']['sha256'])
 ok(True,'new held dispatch/reservation directly accepted by actual entry metadata validator')
 for key in held:
  v=copy.deepcopy(held);v[key]='wrong'
  no(lambda v=v:e.validate_dispatch(v,res,b['authorization'],b['authorization_sha256'],'9920001',held['reservation']['sha256']),'actual held dispatch consumer rejects '+key)
 for key in res:
  v=copy.deepcopy(res);v[key]='wrong'
  no(lambda v=v:e.validate_dispatch(held,v,b['authorization'],b['authorization_sha256'],'9920001',held['reservation']['sha256']),'actual reservation consumer rejects '+key)

def admission_checks():
 a=g.admission_fixed();a['prepared_utc']='2026-10-21T01:10:00+00:00'
 ok(g.check_admission_fields(a)==a,'exact root bounded admission field validator')
 for key in a:
  v=copy.deepcopy(a);v[key]='wrong'
  no(lambda v=v:g.check_admission_fields(v),'root exact scope mutation '+key)
 for value in ('2026-10-21T01:10:00','not-a-date',None):
  v=copy.deepcopy(a);v['prepared_utc']=value
  no(lambda v=v:g.check_admission_fields(v),'root preparation requires explicit timezone '+str(value))
 # Import/compile only: builder has no write or submission side effect on import.
 source=(D/'prepare_admission.py').read_bytes()
 compile(source,str(D/'prepare_admission.py'),'exec')
 ok(b"sys.stdout.buffer.write" in source and b"open('w')" not in source,'root admission builder compiles and emits JSON only')

def reconcile_metadata_checks():
 for mutate in (False,True):
  io=Fake();b=bundle();b['reconcile_existing']=True
  no(lambda:g.Transaction(io,b).run(submit=mutate),'existing ACK metadata cannot authorize new path '+str(mutate))
  ok(io.sbatch_calls==io.release_calls==0,'existing-ACK new-path refusal has no scheduler mutation '+str(mutate))
 class Metadata:
  __file__=str(g.P/g.PROD/'entry.py');CONFIG=g.P/g.PROD/'config.json';R=g.R
  STORAGE_DECISION={'path':'CPU/storage','sha256':'b'*64}
  ROOT_DECISION_REL='CPU/root';ROOT_DECISION_SHA='c'*64
  def __init__(self):self.calls=[];self.decision={'status':'fixed_design_adopted_runtime_and_GPU_HOLD','GPU_execution_authorized':False};self.identity={'original_fixed200_identity_order':True,'unique_development_states':100}
  def read(self,path,pin=None):
   self.calls.append(('read',str(path),pin))
   if str(path).endswith('CPU/root'):return self.decision
   if str(path).endswith('specification.json'):return {'rows':['CPU-original-200-order']}
   return {'CPU_fixture':True}
  def validate_config(self,value):assert value=={'CPU_fixture':True};self.calls.append(('validate_config',))
  def prepare_original(self):self.calls.append(('prepare_original',));return 'inv','wrapper','ctx','legacy'
  def validate_prefix(self,inv,legacy,rows):
   assert (inv,legacy,rows)==('inv','legacy',['CPU-original-200-order'])
   self.calls.append(('validate_prefix',));return self.identity
 e=Metadata();p={'files':{g.PROD+'/specification.json':'a'*64}}
 result=g.reconcile_runtime_metadata(e,p)
 ok(result==dict(status='passed_existing_ACK_metadata_source_only',identity=e.identity,new_storage_reservation_checked=False,new_GPU_submission_allowed=False),'CPU-only original-helper call structure uses truthful existing ACK source-only status')
 ok([v[0] for v in e.calls]==['read','validate_config','read','read','prepare_original','read','validate_prefix'],'existing ACK original config/design/complete-prefix helper order retained')
 for field,value in [('original_fixed200_identity_order',False),('unique_development_states',99)]:
  f=Metadata();f.identity[field]=value
  no(lambda f=f:g.reconcile_runtime_metadata(f,p),'existing ACK metadata rejects changed full200 identity '+field)
 for field,value in [('status','unknown'),('GPU_execution_authorized',True)]:
  f=Metadata();f.decision[field]=value
  no(lambda f=f:g.reconcile_runtime_metadata(f,p),'existing ACK metadata rejects changed original design '+field)
 f=Metadata();f.__file__='/tmp/other.py'
 no(lambda:g.reconcile_runtime_metadata(f,p),'existing ACK metadata refuses noncanonical entry')

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--verify-saved',action='store_true');a=parser.parse_args()
 transaction_checks();actual_observation_checks();admission_checks();reconcile_metadata_checks()
 lp=D/'saved_real_observation.json'
 live=json.loads(lp.read_bytes());derived=projection_checks(live);extra_scope_checks(live)
 ok(derived['original_GPU_seconds']==1643,'old two Goal engineering allocations803+840 retained once')
 source=R/'.local/goal_full200_author_20261021T0110_v2/package'
 package=json.loads((source/'package_manifest.json').read_bytes())
 ok(hashlib.sha256((source/'package_manifest.json').read_bytes()).hexdigest()==g.RUNTIME_MANIFEST_SHA,'exact final runtime v2 manifest is the dispatcher literal pin')
 scope=json.loads((D/'scope.json').read_bytes())
 ok(hashlib.sha256((D/'scope.json').read_bytes()).hexdigest()==g.SCOPE_SHA and scope['runtime_files']==package['files'],'exact full10 final runtime closure in frozen scope')
 ok(scope['maximum_trials']==200 and scope['unique_development_states']==100 and scope['maximum_attempts']==1
  and scope['maximum_total_control_steps']==60000 and scope['maximum_total_policy_queries']==7600
  and not scope['automatic_retry'] and scope['old_Goal200_HOLD'] and scope['other_Goal1000_HOLD'] and not scope['final_allowed'],'scope preserves one fixed200/100 and all other HOLDs')
 for rel,h in package['files'].items():
  ok(hashlib.sha256((source/Path(rel).name).read_bytes()).hexdigest()==h,'real candidate runtime file SHA '+rel)
 config=json.loads((source/'config.json').read_bytes())
 ok(config['maximum_trials']==200 and config['unique_development_states']==100 and config['method_ids']==['A256_seed17','B256_seed17']
  and config['maximum_total_control_steps']==60000 and config['maximum_total_policy_queries']==7600 and not config['automatic_retry'],'real full200 source scientific bound')
 result=dict(schema='formal_main_v2',kind='Goal_full200_atomic_dispatch_CPU',status='passed_CPU_dispatch_candidate',
  positive_count=len(positive),negative_count=len(negative),positive=positive,negative=negative,
  dispatch_sha256=hashlib.sha256((D/'dispatch.py').read_bytes()).hexdigest(),
  runtime_package_manifest_sha256=hashlib.sha256((source/'package_manifest.json').read_bytes()).hexdigest(),
  original_saved_projection=dict(path=str(lp.relative_to(R)),sha256=hashlib.sha256(lp.read_bytes()).hexdigest(),state_sha256=live['state_sha256'],utc=live['result']['utc']),
  source173_not_written_by_dispatch_tests=True,old_Object_package_not_written_by_dispatch_tests=True,new_Slurm_queries=0,new_Slurm_submissions=0,
  new_GPU_seconds=0,new_scientific_trials=0,actual_P_new_package_verified=False,production_admitted=False)
 if a.verify_saved:
  assert result==json.loads((D/'CPU_report.json').read_bytes());print(json.dumps(dict(status='read_only_rebuild_passed',positive=len(positive),negative=len(negative))))
 else:
  with (D/'CPU_report.json').open('x') as f:json.dump(result,f,ensure_ascii=False,sort_keys=True,indent=2)
  print(json.dumps(dict(status=result['status'],positive=len(positive),negative=len(negative))))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  p=D/('failure_'+g.utc().replace(':','').replace('+','_')+'.json')
  with p.open('x') as f:json.dump(dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),positive=positive,negative=negative,Slurm_submitted=False),f,ensure_ascii=False,indent=2)
  raise

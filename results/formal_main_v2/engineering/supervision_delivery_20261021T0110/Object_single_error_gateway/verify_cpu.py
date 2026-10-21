"""CPU transaction/error tests plus one real read-only scheduler projection."""
from pathlib import Path
from contextlib import contextmanager
import argparse,copy,hashlib,importlib.util,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/object_single_error_gateway_20261021T0110'
def load(name):
 p=D/(name+'.py');s=importlib.util.spec_from_file_location('_object_gateway_test_'+name,p)
 m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
g=load('gateway');build=load('build')
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
 inv=dict(job_name=g.NAME,slurm_comment='cti-object-single-error:'+'a'*64,slurm_output=str(g.P/'results/slurm'/(g.NAME+'_%j.out')),
  plan_sha256='b'*64,runtime_readiness=dict(path=g.X+'/runtime_readiness.json',sha256='c'*64,bytes=1),
  registered_utc='2026-10-21T01:10:00+00:00')
 return dict(invocation=inv,invocation_bytes=g.canonical(inv)+b'\n',authorization_ref=dict(path=g.AUTH,bytes=1,sha256='d'*64),
  token='a'*64,comment=inv['slurm_comment'],sources={'CPU_fixture':True})
class Fake:
 def __init__(self,fail=None):
  self.state={'pending_submission':None,'autonomous_training_v1':{'reserved_GPU_slots':0},
    'registered_jobs':[{'job_id':'3021394','original':'retained'}]}
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
 def publish_invocation(self):
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
 def committed(self,jid,state,version,obs):
  self.at('committed');state['pending_submission']=None
  return self.cas(state,version)

def transaction_checks():
 b=bundle();f=Fake();result=g.Transaction(f,b).run(submit=True)
 ok(result['status']=='submitted_once_registered_then_released' and f.sbatch_calls==f.release_calls==1,'one held submission and one release')
 ok(f.state['registered_jobs'][0]=={'job_id':'3021394','original':'retained'} and f.state['pending_submission'] is None,'historical row preserved and pending only cleared after release evidence')
 order=f.calls
 ok(order.index('fact_pending.json')<order.index('publish')<order.index('submit')<order.index('fact_sbatch_result.json')<order.index('fact_registered_held.json')<order.index('release_before_effect'),'durable pending before submit and registration before release')
 ok(f.state['registered_jobs'][1]['downstream_gateway']['request_token']==b['comment']
  and f.state['registered_jobs'][1]['name']==f.state['registered_jobs'][1]['job_name']==g.NAME,'common supervisor original comment/name preserved')
 no(lambda:g.Transaction(f,b).run(submit=True),'repeat existing output/audit rejected')
 ok(f.sbatch_calls==1,'repeat did not resubmit')
 for phase in ['publish','submit','fact_sbatch_result.json','actual_held','observe_new','fact_registered_held.json',
  'fact_release_attempt.json','release_before_effect','release_after_effect','fact_release_result.json',
  'actual_released','committed','cas_before_1','cas_before_2','cas_before_3']:
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
 for answer in [dict(returncode=1,stdout='9900001\n'),dict(returncode=0,stdout=''),dict(returncode=0,stdout='9900001\n9900002\n'),dict(returncode=0,stdout='Submitted batch job 9900001'),dict(returncode=0,stdout='3021394\n')]:
  no(lambda answer=answer:g.parse_ack(answer,{'3021394'}),'ambiguous/nonzero/old ACK rejected '+repr(answer))
 for key,value in [('mode',g.MODE),('logical_trial_id',g.CELL),('stage_key',g.STAGE),('invocation',g.INV),('run_root',str(g.P/g.OUT)),('linked_failure_sha256',g.FAILURE_SHA),('name',g.NAME),('slurm_comment','cti-object-single-error:unknown')]:
  ok(g.duplicate({key:value,'status':'FAILED'}),'incomplete prior row blocks '+key)
 f=Fake();f.state['autonomous_training_v1']['pending_submission']={'unknown_ACK':True}
 no(lambda:g.Transaction(f,b).run(submit=True),'nested autonomous unknown ACK refuses before submission')
 ok(f.sbatch_calls==0 and f.release_calls==0,'nested pending creates no allocation')
 args=g.sbatch_argv(b)
 ok('--hold' in args and '--no-requeue' in args and '--exclude=gpu4020' in args and args[-2]==str(g.P/g.BASE/'run.slurm'),'exact held/requeue/resources/entry argv')

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

def state_for_projection(s):
 a=s['autonomous_training_v1'];p=s['formal_main_progress']
 return {'pending_submission':s.get('pending_submission'),'registered_jobs':copy.deepcopy(s['registered_jobs']),
  'autonomous_training_v1':{k:copy.deepcopy(a.get(k)) for k in ['owner_id','controller_job_id','blocked_pairs','last_result','root_submission_hold','reserved_GPU_slots','pending_submission']}|
   {'completed_pairs':{k:{n:v.get(n) for n in ['decision','completed_by_arm','selected_checkpoints_verified']} for k,v in a['completed_pairs'].items()}},
  'formal_main_progress':{k:copy.deepcopy(p.get(k)) for k in ['root_and_independent_completed_arms','root_and_independent_reviewed_arm_updates',
    'trained_arms','expected_arms','test_opened','global_release_created','completed_final_trials']}|
   {'completed_training_pairs':{k:True for k in p['completed_training_pairs']}}}
def capture_live():
 c=g.controller()
 with g.shared_writer_lock():
  before=g.raw(R/g.STATE);state=json.loads(before)
  n=g.Native.__new__(g.Native);n.c=c;n.scheduler=c.Slurm(timeout=30)
  result=n.observe(state)
  g.require(g.raw(R/g.STATE)==before,'actual state changed in read-only probe')
 return dict(schema=g.EXPERIMENT,kind='actual_readonly_gateway_inputs',state_sha256=g.sha(before),state_for_projection=state_for_projection(state),
  result=result,source_gateway_sha256=g.sha((D/'gateway.py').read_bytes()),Slurm_submitted=False,new_scientific_trials=0,new_GPU_seconds=0)

def projection_checks(live):
 c=g.controller();state=live['state_for_projection'];result=live['result']
 obs=result['observation'];details=result['details'];derived=g.normalized_projection(c,state,obs,details)
 ok(derived==result['derived'],'real all-mode projection rebuilt from saved registered identities and actual Slurm rows')
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
 for field,value in [('status','FAILED'),('exit_code','1:0'),('elapsed_seconds',4925),('gpus',0)]:
  bad=copy.deepcopy(obs);bad['rows']['3021844'][field]=value
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
   bad=copy.deepcopy(state);next(j for j in bad['registered_jobs'] if str(j['job_id'])==jid)['suite']='libero_object'
   no(lambda:g.normalized_projection(c,bad,obs,details),'other Object allocation occupied across modes')
   break
 # Independent held-job fields validate exact stdout, resources and original argv.
 b=bundle();job=g.job_record('9900001',b,g.sbatch_argv(b));f=g.expected_live(job)
 f.update(Requeue='0',TimeLimit='00:30:00',ExcNodeList='gpu4020',NumCPUs='7',MinMemoryNode='64G',
  Command=str(g.P/g.BASE/'run.slurm'),WorkDir=str(g.S),Restarts='0',QOS=g.RESOURCES['qos'],
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

def main():
 p=argparse.ArgumentParser();p.add_argument('--capture-live',action='store_true');p.add_argument('--verify-saved',action='store_true');a=p.parse_args()
 for n in ['gateway.py','build.py']:compile((D/n).read_bytes(),str(D/n),'exec')
 sources={n:g.sha((D/n).read_bytes()) for n in g.NAMES}
 transaction_checks()
 actual_observation_checks()
 if a.capture_live:
  live=capture_live()
  with (D/'live_inputs.json').open('x') as f:json.dump(live,f,ensure_ascii=False,sort_keys=True,indent=2)
 else:live=json.loads((D/'live_inputs.json').read_text())
 derived=projection_checks(live)
 # Rebuild complete real legacy adoption and original scientific inputs. Do not
 # create root repair, plan, invocation, readiness or any synthetic approvals.
 F,C,A,W,G=g.production_modules()
 context=W.reference_context(project=R)
 ok(context['adoption']['legacy_equivalent_trials']==599,'real599 adoption reconstructed with all original identities/costs')
 proposals=build.stage_plan(g)
 ok(set(proposals)=={g.X+'/root_repair.json',g.X+'/production_independent.json',g.PLAN}
  and proposals[g.PLAN]['method_ids']==g.METHODS and proposals[g.PLAN]['ordinary_resume'] is False,'actual staged metadata objects rebuild full original100/six scientific guard without publishing')
 for root in (R,g.P):
  ok(not (root/g.INV).exists(),'no actual invocation published by CPU tests '+str(root))
 ok(sources=={n:g.sha((D/n).read_bytes()) for n in g.NAMES},'source immutable during tests')
 result=dict(schema=g.EXPERIMENT,kind='Object_single_error_native_gateway_CPU_report',status='passed_CPU_gateway_candidate',
  positive_count=len(positive),negative_count=len(negative),positive=positive,negative=negative,source_files=sources,
  old_production_sources=g.production_map(),installed_old10_sources_verified=True,
  actual_live_projection_sha256=g.sha((D/'live_inputs.json').read_bytes()),actual_live_state_sha256=live['state_sha256'],
  actual_old599_reconstruction_sha256=F.sig(context['adoption']),actual_registered_jobs=len(live['state_for_projection']['registered_jobs']),
  actual_occupied_GPU_jobs=derived['occupied'],original_GPU_seconds=6713,new_GPU_seconds=0,new_scientific_trials=0,
  source173_verified=True,actual_new_P_entry_verified=False,canonical_gateway_installed=False,Slurm_submitted=False,
  production_admitted=False,final_values_read=False,ordinary_resume=False,retained_failures_and_negative_outcomes=True)
 if a.verify_saved:
  saved=json.loads((D/'CPU_report.json').read_text())
  if result!=saved:raise AssertionError('read-only CPU rebuild differs')
  print(json.dumps(dict(status='read_only_rebuild_passed',positive=result['positive_count'],negative=result['negative_count'])))
 else:
  with (D/'CPU_report.json').open('x') as f:json.dump(result,f,ensure_ascii=False,sort_keys=True,indent=2)
  print(json.dumps(dict(status=result['status'],positive=result['positive_count'],negative=result['negative_count'])))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  if '--capture-live' in sys.argv:
   p=D/('failure_'+g.utc().replace(':','').replace('+','_')+'.json')
   with p.open('x') as f:json.dump(dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),
    positive=positive,negative=negative,new_GPU_seconds=0,Slurm_submitted=False),f,ensure_ascii=False,indent=2)
  raise

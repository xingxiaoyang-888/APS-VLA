from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import contextmanager
import importlib.util,copy,json,hashlib,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_remaining5_dispatch_20261021T0449'
p=D/'gateway_v3.py';spec=importlib.util.spec_from_file_location('_remaining5_dispatch_CPU',p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m
exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
positive=[];negative=[]
def ok(x,name):
 if not x:raise AssertionError(name)
 positive.append(name)
def no(fn,name):
 try:fn()
 except BaseException as e:
  if isinstance(e,(KeyboardInterrupt,SystemExit)):raise
  negative.append(dict(check=name,error_type=type(e).__name__,error=str(e)));return
 raise AssertionError('accepted negative: '+name)
runtime_files={m.PROD+'/entry.py':'1'*64,**{m.PROD+'/pairs/'+key+'/config.json':'2'*64 for key in m.PAIRS}}
scope=dict(schema=m.EXPERIMENT,kind='five_exact_Goal_pairs_dispatch_scope',version=m.VERSION,design={'path':m.DESIGN,'sha256':m.DESIGN_SHA},pairs={k:list(v) for k,v in m.PAIRS.items()},runtime_manifest_sha256='3'*64,runtime_files=runtime_files)
rawscope=m.canonical(scope)+b'\n';scopepin=m.sha(rawscope)
read0=m.read;raw0=m.raw
def read_cpu(path,pin=None):
 if str(path) in [str(root/m.BASE/'scope.json') for root in (m.R,m.P)]:
  if pin not in (None,scopepin):raise ValueError('CPU scope SHA mismatch')
  return copy.deepcopy(scope)
 return read0(path,pin)
def raw_cpu(path,pin=None):
 if str(path) in [str(root/m.BASE/'scope.json') for root in (m.R,m.P)]:
  if pin not in (None,scopepin):raise ValueError('CPU scope SHA mismatch')
  return rawscope
 return raw0(path,pin)
with patch.object(m,'read',read_cpu),patch.object(m,'raw',raw_cpu):
 dispatchers={key:m.make_dispatcher(key,scopepin) for key in m.PAIRS}
 no(lambda:m.make_dispatcher('libero_goal_k128_seed17',scopepin),'unlisted trained pair refused')
 no(lambda:m.make_dispatcher('libero_goal_k256_seed17',scopepin),'already completed Goal pair refused')
 no(lambda:m.make_dispatcher(next(iter(m.PAIRS)),'9'*64),'wrong five scope SHA refused')
class Interrupt(BaseException):pass
def bundle(d):
 inv={'fixture':'CPU_SYNTHETIC_NOT_ACTUAL'};ib=m.canonical(inv)+b'\n';ah=m.sha(ib)
 return dict(authorization=inv,authorization_sha256=ah,invocation_bytes=ib,authorization_ref=dict(path=d.authorization,bytes=len(ib),sha256=ah),
  token='cti-goal-remaining5-v1:'+d.pair_key+':'+ah,comment='cti-goal-remaining5-v1:'+d.pair_key+':'+ah,
  sources={'CPU_FIXTURE_NOT_ACTUAL':True},runtime_package={'files':runtime_files},
  admission={'prepared_utc':'2026-10-21T04:49:00+00:00'},admission_ref={'path':str(Path(d.authorization).parent/'dispatch_admission.json'),'bytes':1,'sha256':'4'*64})
class Fake:
 def __init__(self,d,fail=None):
  self.d=d;self.fail=fail;self.triggered=False;self.state={'pending_submission':None,'autonomous_training_v1':{'reserved_GPU_slots':0},'registered_jobs':[{'job_id':'3053440','original':'retained'}]}
  self.facts={};self.calls=[];self.sbatch_calls=self.release_calls=self.cases=0;self.held=True;self.published=False
 def at(self,label):
  self.calls.append(label)
  if self.fail==label and not self.triggered:self.triggered=True;raise Interrupt(label)
 @contextmanager
 def lock(self):self.at('lock');yield
 def read_state(self):return copy.deepcopy(self.state),m.sha(m.canonical(self.state))
 def cas(self,state,expected):
  self.at('cas_before_'+str(self.cases));self.cases+=1
  if m.sha(m.canonical(self.state))!=expected:raise ValueError('CAS drift')
  self.state=copy.deepcopy(state);return m.sha(m.canonical(self.state))
 def fact(self,name,value):
  self.at('fact_'+name)
  if name in self.facts:raise ValueError('immutable fact exists')
  self.facts[name]=copy.deepcopy(value)
 def fact_read(self,name):return copy.deepcopy(self.facts[name])
 def fact_exists(self,name):return name in self.facts
 def observe(self,state,allow_job=None):
  self.at('observe_'+('new' if allow_job else 'old'));return {'observation':{'rows':{}},'derived':{'occupied':[allow_job] if allow_job else [],'allocated_formal_GPU_seconds':1994468}}
 def absent(self):
  self.at('absent')
  if self.facts or self.published:raise ValueError('prior attempt evidence')
 def revalidate(self):self.at('revalidate')
 def publish_reservation(self):self.at('publish');self.published=True
 def submit(self,argv):
  self.sbatch_calls+=1;self.at('submit');return dict(returncode=0,stdout='9900001\n',stderr='',actual_sbatch_argv=argv)
 def actual(self,jid,held):
  self.at('actual_held' if held else 'actual_released')
  if held!=self.held:raise ValueError('held state incompatible; no resend')
  return {'CPU_FIXTURE_NOT_ACTUAL':True,'fields':{'JobId':jid}}
 def release(self,jid):
  self.release_calls+=1;self.at('release_before_effect');self.held=False;self.at('release_after_effect');return dict(returncode=0,stdout='',stderr='',argv=['scontrol','release',jid])
 def dispatch_proof(self,jid,state,version):
  self.at('dispatch_proof')
  if self.state['registered_jobs'][-1]['job_id']!=jid:raise ValueError('registration must precede release')
 def committed(self,jid,state,version,obs):self.at('committed');state['pending_submission']=None;return self.cas(state,version)
for key,d in dispatchers.items():
 b=bundle(d);f=Fake(d);r=d.Transaction(f,b).run(submit=True)
 ok(r['status']=='submitted_once_registered_then_released' and f.sbatch_calls==f.release_calls==1,key+' one ACK/release')
 ok(f.state['pending_submission'] is None and f.state['registered_jobs'][0]=={'job_id':'3053440','original':'retained'},key+' old registration preserved')
 ok(f.calls.index('fact_pending.json')<f.calls.index('submit')<f.calls.index('fact_sbatch_result.json')<f.calls.index('fact_registered_held.json')<f.calls.index('release_before_effect'),key+' durable operation order')
 no(lambda:d.Transaction(f,b).run(submit=True),key+' repeat forbidden')
 for phase in ['publish','submit','fact_sbatch_result.json','actual_held','observe_new','fact_registered_held.json','fact_release_attempt.json','release_before_effect','release_after_effect','fact_release_result.json','actual_released','dispatch_proof','committed','cas_before_1','cas_before_2','cas_before_3']:
  f=Fake(d,phase);no(lambda:d.Transaction(f,b).run(submit=True),key+' BaseException '+phase)
  ok(f.state['pending_submission'] is not None,key+' preserves pending '+phase)
  calls=f.sbatch_calls;no(lambda:d.Transaction(f,b).run(submit=True),key+' no repeat after '+phase)
  ok(f.sbatch_calls==calls,key+' no additional allocation '+phase)
 for phase,success in [('submit',False),('actual_held',True),('fact_registered_held.json',True),('release_before_effect',False),('release_after_effect',True)]:
  f=Fake(d,phase);no(lambda:d.Transaction(f,b).run(submit=True),key+' reconcile setup '+phase)
  if success:
   d.Transaction(f,b).run(reconcile=True);ok(f.sbatch_calls==1 and f.release_calls==1,key+' reconcile original '+phase)
  else:no(lambda:d.Transaction(f,b).run(reconcile=True),key+' uncertainty stays HOLD '+phase)
 f=Fake(d);f.state['autonomous_training_v1']['pending_submission']={'unresolved':True};no(lambda:d.Transaction(f,b).run(submit=True),key+' nested pending blocks')
 ok(f.sbatch_calls==0,key+' nested pending no allocation')
 f=Fake(d);t=d.Transaction(f,b);t.run();ok(f.sbatch_calls==f.release_calls==0 and not f.facts,key+' readonly no effects');no(lambda:t.run(submit=True),key+' transaction instance singleuse')
 j=d.job_record('9910001',b,d.sbatch_argv(b))
 for other_key,other in dispatchers.items():
  ok(other.duplicate(j)==(key==other_key),key+' duplicate isolation '+other_key)
  ok(other.goal_overlap(j)==(key==other_key),key+' concurrent pair isolation '+other_key)
 ok(j['training_seed']==m.PAIRS[key][2] and j['runtime_seed']==17 and j['environment_seed']==0,key+' runtime and train seeds distinguished')
 ok(j['method_ids']==[f'{arm}{j["visual_tokens"]}_seed{j["training_seed"]}' for arm in ('A','B')],key+' exact registered method set')
 ok(m.option(argv if False else d.sbatch_argv(b),'output').startswith(str(R/'results/slurm')),key+' new scheduler log on R')
 argv=d.sbatch_argv(b)
 ok('--hold' in argv and '--no-requeue' in argv and m.option(argv,'export').split(',')[1]=='CTI_GOAL_REMAINING5_PAIR_KEY='+key,key+' exact immutable key argv')
 flds=m.expected_live(j);flds.update(Requeue='0',TimeLimit='02:00:00',Partition='L40',Account='p_p15016',ExcNodeList='gpu4020',NumCPUs='7',MinMemoryNode='64G',Command=str(m.P/m.PROD/'run.slurm'),WorkDir=str(m.S),Restarts='0',QOS=d.resources['qos'],TresPerNode='gres:gpu:l40:1',JobState='PENDING',Reason='JobHeldUser')
 d.validate_new_identity(j,b,flds,True);ok(True,key+' exact new held identity')
 for field in flds:
  bad=dict(flds);bad[field]='wrong';no(lambda bad=bad:d.validate_new_identity(j,b,bad,True),key+' reject held '+field)
 for answer in [dict(returncode=1,stdout='9910001\n'),dict(returncode=0,stdout=''),dict(returncode=0,stdout='9910001\n9910002\n'),dict(returncode=0,stdout='Submitted batch job 9910001'),dict(returncode=0,stdout='3053440\n')]:
  no(lambda answer=answer:m.parse_ack(answer,{'3053440'}),key+' ambiguous ACK')
# Reparse saved actual accounting; no new Slurm or mutation.
state_bytes=(R/'results/formal_main_v2/preflight/heartbeat_20261021T1249/method_ids_supervisor_snapshot_before.json').read_bytes();assert m.sha(state_bytes)=='54ee7389fe300b4ec553998d91b9bf727ca3231c2066e35a86716559a3c1406d'
state=json.loads(state_bytes);receipt=read0(R/'results/formal_main_v2/preflight/heartbeat_20261021T1249/initial_observation.json','069c3efbb2cdd386b3072d120925c312d09e173130783f1035e7aa3475a4bedf')
obs=receipt['projection']['observation'];ctl=m.controller();parsed=ctl.parse_sacct(obs['raw_sacct'],set(obs['rows']))
ok(parsed==obs['rows'],'all 303 saved registered allocation rows reparsed; 273 formal allocations')
for key,d in dispatchers.items():
 value=d.normalized_projection(ctl,state,obs,{})
 ok(value['occupied']==[] and value['allocated_formal_GPU_seconds']==1994468,key+' real no active job/cost projection')
 for field,val in [('root_submission_hold',{'reason':'HOLD'}),('reserved_GPU_slots',8),('pending_submission',{'unknown':True}),('blocked_pairs',{'x':'failed'}),('controller_job_id','0')]:
  bad=copy.deepcopy(state);bad['autonomous_training_v1'][field]=val;no(lambda bad=bad:d.normalized_projection(ctl,bad,obs,{}),key+' reject '+field)
 for field,val in [('test_opened',True),('global_release_created',True),('completed_final_trials',1),('root_and_independent_completed_arms',71)]:
  bad=copy.deepcopy(state);bad['formal_main_progress'][field]=val;no(lambda bad=bad:d.normalized_projection(ctl,bad,obs,{}),key+' retain scientific guard '+field)
 bad=copy.deepcopy(state);bad['pending_submission']={'unknown':True};no(lambda:d.normalized_projection(ctl,bad,obs,{}),key+' root unknown pending')
 # Compose all five registered synthetic live scopes, exclude current one before prospective admission.
 synthetic=copy.deepcopy(state);o=copy.deepcopy(obs);details={}
 for i,(other_key,other) in enumerate(dispatchers.items()):
  if other_key==key:continue
  b=bundle(other);jid=str(9920000+i);j=other.job_record(jid,b,other.sbatch_argv(b));synthetic['registered_jobs'].append(j)
  o['rows'][jid]=dict(job_id=jid,status='PENDING',exit_code='0:0',elapsed_seconds=0,allocation='',node='',gpus=0,scheduler_name=j['name'],scheduler_comment=b['comment'])
  o['queue'][jid]=dict(status='PENDING',comment=b['comment']);f=m.expected_live(j);f.update(JobState='PENDING',TresPerNode='gres:gpu:l40:1');details[jid]=f
 value=d.normalized_projection(ctl,synthetic,o,details);ok(len(value['occupied'])==4,key+' four different Goal pairs permit fifth')
 for extra in range(4):
  jid=str(9930000+extra);j=copy.deepcopy(synthetic['registered_jobs'][-1]);j.update(job_id=jid,pair_id='f'*64,stage_key='CPU_other',logical_trial_id='CPU_other'+jid,invocation='CPU_other'+jid,run_root='CPU_other'+jid,name='cti-other-'+jid,job_name='cti-other-'+jid,suite='libero_spatial')
  av=j['downstream_gateway']['actual_sbatch_argv'];av=[('--job-name='+j['name'] if a.startswith('--job-name=') else '--comment=cti-fixture-'+jid if a.startswith('--comment=') else a) for a in av]
  j['downstream_gateway']['actual_sbatch_argv']=av;j['goal_remaining5_gateway']['actual_sbatch_argv']=av;j['slurm_comment']='cti-fixture-'+jid
  synthetic['registered_jobs'].append(j);o['rows'][jid]=dict(job_id=jid,status='PENDING',exit_code='0:0',elapsed_seconds=0,allocation='',node='',gpus=0,scheduler_name=j['name'],scheduler_comment=j['slurm_comment']);o['queue'][jid]=dict(status='PENDING',comment=j['slurm_comment']);f=m.expected_live(j);f.update(JobState='PENDING',TresPerNode='gres:gpu:l40:1');details[jid]=f
  if extra<3:ok(len(d.normalized_projection(ctl,synthetic,o,details)['occupied'])==5+extra,key+' allmode capacity '+str(5+extra))
  else:no(lambda:d.normalized_projection(ctl,synthetic,o,details),key+' ninth slot refused allmode')
ok(m.sha((R/'results/formal_main_v2/preflight/heartbeat_20261021T1249/method_ids_supervisor_snapshot_before.json').read_bytes())==m.sha(state_bytes),'saved actual registry snapshot unchanged')
report=dict(schema='formal_main_v2',kind='Goal_remaining5_atomic_dispatch_author_CPU',status='passed',source_sha256=m.sha(p.read_bytes()),scope_fixture=True,scope_fixture_not_production=True,positive_count=len(positive),negative_count=len(negative),positive=positive,negative=negative,actual_observation_receipt='results/formal_main_v2/preflight/heartbeat_20261021T1249/initial_observation.json',actual_scheduler_queries=0,real_GPU_submissions=0,state_changed=False,production_ready=False)
out=D/'CPU_report_v3.json'
with out.open('x') as f:json.dump(report,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'report':str(out),'sha256':m.sha(out.read_bytes()),'positive':len(positive),'negative':len(negative)}))

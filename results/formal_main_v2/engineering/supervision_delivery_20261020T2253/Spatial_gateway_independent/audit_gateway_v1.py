"""Independent Spatial588 exact gateway review.
All writes are under this .local audit directory. Slurm and real P publication
are forbidden; submission tests use deterministic in-memory scheduler replies.
"""
from pathlib import Path
from types import ModuleType,SimpleNamespace
import ast,copy,hashlib,json,os,sys,traceback
from datetime import datetime,timezone

R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/spatial_gateway_independent_20261020T2253'
B=R/'.local/spatial588_integration_20261020T2156/phase3_gateway'
C=R/'.local/spatial588_integration_20261020T2156/phase2_v2'
MREF={'path':'.local/spatial588_integration_20261020T2156/phase3_gateway_manifest.json','sha256':'4c1ccca16c81a2dec94109cac3a5c4e6743841920d975d0737ea90bd8657cde9'}
GPIN='aba5868a8dc4e480262177785b2e62123d014046624f37924248721a9575c99c'
CPIN='e2e7c3fe7f6dcf4f63b4550c3f5bc8ec50a05aaf462b38ed961ce356cc414683'
HPIN='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
PHASE2={'path':'.local/spatial_phase2_independent_20261020T2156/independent_history_review.json','sha256':'db89d100fdc77f3ea7185ca8ffb1d20cbce333a88b627f8d477618f1924f6cc9'}
assert D.exists() and D.resolve()==D and not D.is_symlink()
checks=[];reads={};cases=[];partial={}

def sha(b):return hashlib.sha256(b).hexdigest()
def rawjson(x):return (json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
def sig(x):return sha(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode())
def get(rel,pin=None):
 p=R/rel;assert p.resolve()==p and not p.is_symlink() and R in p.parents
 b=p.read_bytes();h=sha(b);assert pin is None or pin==h,(rel,pin,h);reads[rel]={'sha256':h,'bytes':len(b)};return b
def write(p,x):
 assert D in p.parents and p.resolve()==p and not p.is_symlink()
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(rawjson(x))
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes())}
def okay(name,value=True,detail=None):
 assert value,name
 out={'name':name,'passed':True}
 if detail is not None:out['detail']=detail
 checks.append(out)
def reject(name,fn,types=(ValueError,KeyError,AssertionError,FileNotFoundError,TypeError)):
 try:fn()
 except types as exc:checks.append({'name':name,'passed':True,'expected_rejection':str(exc)[:1200]});return
 raise AssertionError('Unexpected acceptance: '+name)
def module(name,path,pin):
 b=get(path.relative_to(R).as_posix(),pin);m=ModuleType(name);m.__file__=str(path);m.__package__=''
 sys.modules[name]=m;exec(compile(b,str(path),'exec',dont_inherit=True),m.__dict__);return m

try:
 manifest=json.loads(get(MREF['path'],MREF['sha256']))
 for f in manifest['files']:okay('manifest '+f['path'],len(get(f['path'],f['sha256']))==f['bytes'])
 okay('six frozen artifacts',manifest['file_count']==len(manifest['files'])==6 and manifest['production_admission'] is False)
 g=module('_ind_gateway',B/'gateway.py',GPIN)
 c=module('_ind_phase2',C/'control.py',CPIN)
 ctl=module('_ind_controller',R/g.CONTROLLER,HPIN)
 prior_review=json.loads(get(PHASE2['path'],PHASE2['sha256']))
 okay('specific Spatial phase2 independently passed',prior_review['status']=='passed_CPU_review' and prior_review['production_admission'] is False and prior_review['checks']==431)
 files={g.COMPLETED_COLLECT_BASE['path']:g.COMPLETED_COLLECT_BASE['sha256'],**prior_review['history_control_sources'],
        'scripts/ops/formal_action_deployment_posttraining_spatial588_v1/gateway.py':GPIN}
 base=get(g.COMPLETED_COLLECT_BASE['path'],g.COMPLETED_COLLECT_BASE['sha256']).decode()
 source=(B/'gateway.py').read_text()
 def top(src):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(src).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 oldtop=top(base);newtop=top(source)
 changed=[n for n in oldtop if oldtop[n]!=newtop[n]]
 okay('exact seven scoped definitions changed',changed==['validate_authorization','completed_training_development_gate','capacity_gate','Gateway','_exact_development_authorization','_exact_development_control','_exact_development_plan'])
 okay('no added or removed top-level routines',set(oldtop)==set(newtop))
 for n in oldtop:
  if n not in changed:okay('unchanged source AST '+n,oldtop[n]==newtop[n])
 def members(src,cls):
  return {n.name:ast.dump(n,include_attributes=False) for n in next(n for n in ast.parse(src).body if isinstance(n,ast.ClassDef) and n.name==cls).body if isinstance(n,ast.FunctionDef)}
 oldmethods=members(base,'Gateway');newmethods=members(source,'Gateway')
 okay('transaction and CAS identical; only typed job metadata added',[k for k in oldmethods if oldmethods[k]!=newmethods[k]]==['_job'])
 def remainder(src):
  out=[]
  for n in ast.parse(src).body:
   if isinstance(n,(ast.FunctionDef,ast.ClassDef)):continue
   if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'VERSION','SCOPED_DEVELOPMENT_PLANS','COMPLETED_COLLECT_BASE'} for t in n.targets):continue
   out.append(ast.dump(n,include_attributes=False))
  return out
 okay('all other imports globals and main guard unchanged',remainder(base)==remainder(source))
 okay('one suite only',set(g.SCOPED_DEVELOPMENT_PLANS)=={'libero_spatial'})
 allowed=g.SCOPED_DEVELOPMENT_PLANS['libero_spatial']
 okay('exact phase2 source pin',allowed['control']=={'path':'scripts/ops/formal_spatial588_predispatch_v1/control.py','sha256':CPIN})
 okay('exact methods retain Dense uniform and128seed17',allowed['method_ids']==['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17'])

 # Private scoped source substitution is restricted to this single known module.
 # No canonical module or metadata is created by these CPU fixtures.
 real_load=g.load
 def fixture_load(path,pin,name):
  if Path(path)==R/allowed['control']['path']:
   assert pin==CPIN;return c
  return real_load(path,pin,name)
 g.load=fixture_load
 scientific=json.loads(get((C/'SYNTHETIC_planner_fixture.json').relative_to(R).as_posix()))['synthetic_plan_NOT_FOR_SUBMISSION']
 effective=copy.deepcopy(scientific)
 args=dict(stage='development',source_inventory=g.INVENTORY,execution_manifest=c.policy()['manifest']['path'],output_relative=None,freeze_directory=None,profile_panel=None,prior_review=c.policy()['prefix_review']['path'],collection_review=None,repair_record=c.REPAIR,resume=True,stop_after=None)
 auth={'plan':{'path':allowed['path'],'sha256':sha(rawjson(effective))},'scientific_plan':{'path':allowed['scientific_path'],'sha256':sha(rawjson(scientific))},'prepared_invocation':{'path':allowed['prepared_path'],'sha256':'3'*64},'plan_arguments':args,'explicit_source_control':c.descriptor(),'legacy12_compatibility':c.compatibility_module().descriptor(),'controller_job_id':g.COMPLETED_CONTROLLER_ID,'controller_activation':g.ACTIVATION}
 okay('exact scope accepts explicit in-memory CPU plan',g._exact_development_plan(R,auth,effective,scientific) is c)
 for field in ('plan','scientific_plan','prepared_invocation'):
  for path in ['results/formal_main_v2/foreign.json','.local/foreign.json','results/formal_main_v2/final/sealed.json']:
   bad=copy.deepcopy(auth);bad[field]['path']=path;reject('scope ref '+field+'/'+path,lambda bad=bad:g._exact_development_authorization(bad))
  for h in ['','x'*64,'1'*63]:
   bad=copy.deepcopy(auth);bad[field]['sha256']=h;reject('scope malformed SHA '+field+'/'+str(len(h)),lambda bad=bad:g._exact_development_authorization(bad))
 for k,v in [('stage','final'),('stage','collect'),('stage','full'),('stage','components'),('resume',False),('stop_after',12),('prior_review','results/formal_main_v2/downstream_reviews/3042529.json'),('repair_record',None),('freeze_directory','foreign'),('execution_manifest','foreign')]:
  bad=copy.deepcopy(auth);bad['plan_arguments'][k]=v;reject('argument '+k+'/'+str(v),lambda bad=bad:g._exact_development_authorization(bad))
 for k,v in [('suite','libero_object'),('suite','libero_goal'),('method_ids',['A64_seed23','B64_seed23']),('prior_job_ids',['3022743']),('prior_job_ids',['3042529','3022743']),('prior_job_ids',['3022743','3042529','999']),('pre_dispatch_history',{}),('legacy12_compatibility',{}),('resume',False),('stop_after',8)]:
  inv=copy.deepcopy(effective['invocation']);inv[k]=v;reject('actual scope '+k,lambda inv=inv:g._exact_development_control(R,inv))
 for k,v in [('invocation_relative','results/formal_main_v2/invocations/libero_spatial_development_8c843c1d4ee8383c_attempt04.json'),('output_must_exist',False),('output_relative','foreign')]:
  plan=copy.deepcopy(effective);plan[k]=v;plan['plan_sha256']=sig({k:v for k,v in plan.items() if k!='plan_sha256'})
  reject('exact plan '+k,lambda plan=plan:g._exact_development_plan(R,auth,plan,scientific))
 for field in ('explicit_source_control','legacy12_compatibility'):
  bad=copy.deepcopy(auth);bad[field]={};reject('authorization descriptor '+field,lambda bad=bad:g._exact_development_plan(R,bad,effective,scientific))
 for target in ('scientific','effective'):
  a,b=copy.deepcopy(effective),copy.deepcopy(scientific)
  (a if target=='effective' else b)['plan_sha256']='0'*64
  reject('signed content '+target,lambda a=a,b=b:g._exact_development_plan(R,auth,a,b))

 # Actual immutable training completion/owner/lease evidence; a CPU-only plan is
 # overlaid because a production Spatial588 plan does not exist yet.
 state_bytes=(R/g.STATE).read_bytes();real_state=json.loads(state_bytes)
 observation=json.loads(get(g.COMPLETED_EXIT_OBSERVATION['path'],g.COMPLETED_EXIT_OBSERVATION['sha256']))
 get(g.COMPLETED_ROOT_INTEGRATION['path'],g.COMPLETED_ROOT_INTEGRATION['sha256'])
 complete_snap=copy.deepcopy(observation['observation'])
 RealEvidence=g.Evidence
 class TrainingEvidence(RealEvidence):
  def ref(self,ref):
   if ref==auth['plan']:
    self.hashes[ref['path']]=ref['sha256'];return copy.deepcopy(effective)
   return super().ref(ref)
  def unchanged(self):
   for rel,h in self.hashes.items():
    if rel==auth['plan']['path']:assert h==auth['plan']['sha256']
    else:self.watch(rel,h)
 g.Evidence=TrainingEvidence
 owner=g.COMPLETED_WORK/'owner.json';lease=g.COMPLETED_WORK/'controller.lease.lock'
 owner_before=g.stable(owner);lease_before=lease.stat()
 training=g.completed_training_development_gate(ctl,real_state,complete_snap,auth,effective,[g.COMPLETED_CONTROLLER_ID])
 okay('actual normal controller owner and released lease verified under CPU plan overlay',training['controller_status']=='COMPLETED' and training['root_arms']==72 and training['root_reviewed_updates']==360000 and training['controller_restarted'] is False)
 okay('lease inode and owner unchanged',g.stable(owner)==owner_before and (lease.stat().st_dev,lease.stat().st_ino)==(lease_before.st_dev,lease_before.st_ino))
 partial['actual_training_metadata_gate']={'result':training,'scheduler_observation_is_immutable_historical_root_evidence':True,'new_live_Slurm_query':False,'plan_overlaid_only_in_memory':True}
 for key,val in [('status','RUNNING'),('status','FAILED'),('status','TIMEOUT'),('status','UNKNOWN'),('exit_code','1:0'),('gpus',1)]:
  snap=copy.deepcopy(complete_snap);snap['rows'][g.COMPLETED_CONTROLLER_ID][key]=val
  reject('controller reject '+key+'/'+str(val),lambda snap=snap:g.completed_training_development_gate(ctl,real_state,snap,auth,effective,[g.COMPLETED_CONTROLLER_ID]))
 for key,val in [('blocked_pairs',{'x':'failed'}),('owner_id','foreign'),('last_result',{}),('root_confirmed_normal_training_exit',{})]:
  state=copy.deepcopy(real_state);state['autonomous_training_v1'][key]=val
  reject('controller source state '+key,lambda state=state:g.completed_training_development_gate(ctl,state,complete_snap,auth,effective,[g.COMPLETED_CONTROLLER_ID]))
 state=copy.deepcopy(real_state);state['formal_main_progress']['root_and_independent_completed_arms']=71
 reject('training71 cannot reopen development',lambda:g.completed_training_development_gate(ctl,state,complete_snap,auth,effective,[g.COMPLETED_CONTROLLER_ID]))
 state=copy.deepcopy(real_state);state['formal_main_progress']['test_opened']=True
 reject('final opened refuses bounded development bridge',lambda:g.completed_training_development_gate(ctl,state,complete_snap,auth,effective,[g.COMPLETED_CONTROLLER_ID]))
 g.Evidence=RealEvidence

 # Keep real all-mode capacity, ACK, comments, reconciliation, atomic writes and
 # Gateway.run. Only completed-metadata dependency is replaced below, after its
 # own actual read-only test. All files/locks/registries are private CPU fixtures.
 original_completed=g.completed_training_development_gate
 def fixture_completed(controller,state,snap,a,plan,cpus):
  r=snap['rows'][a['controller_job_id']]
  assert r['status']=='COMPLETED' and r['exit_code']=='0:0' and r['gpus']==0 and a['controller_job_id'] in cpus
  return {'CPU_fixture_dependency_only':True,'controller_restarted':False}
 g.completed_training_development_gate=fixture_completed
 priorjobs=copy.deepcopy(c.policy()['prior_jobs'])
 controller_job=copy.deepcopy(next(j for j in real_state['registered_jobs'] if j['job_id']==g.COMPLETED_CONTROLLER_ID))
 base_jobs=[controller_job,*priorjobs]
 reservation={'path':'results/formal_main_v2/CPU_fixture_reservation_NOT_PRODUCTION.json','sha256':'9'*64}
 case_auth=copy.deepcopy(auth);case_auth.update(root_reservation=reservation,runtime_readiness={'path':'results/formal_main_v2/CPU_fixture_readiness_NOT_PRODUCTION.json','sha256':'8'*64})
 def newstate():
  return {'CPU_fixture_NOT_PRODUCTION':True,'registered_jobs':copy.deepcopy(base_jobs),'pending_submission':None,'autonomous_training_v1':{'activation':g.ACTIVATION,'activation_sha256':g.ACTIVATION['sha256'],'controller_job_id':g.COMPLETED_CONTROLLER_ID,'root_submission_hold':None,'reserved_GPU_slots':1,'reservation_root_record':reservation},'formal_main_progress':{'parallel_execution':{}}}
 def snapshot(jobs,new_id=None,new_status='PENDING',wrong_token=False):
  rows={};queue={}
  for j in jobs:
   jid=str(j['job_id']);new=jid==new_id
   status=new_status if new else j['status']
   token=g.registered_comment(j) or ''
   if wrong_token and new:token='wrong-token'
   gpu=(1 if new_status=='COMPLETED' else 0) if new else j['gpus']
   rows[jid]={'status':status,'exit_code':'0:0' if new else j.get('exit_code','0:0'),'elapsed_seconds':2 if new else j.get('elapsed_seconds',0),'allocation':'CPU fixture allocation','node':'CPU fixture node','gpus':gpu,'scheduler_name':j['name'],'scheduler_comment':token}
   if status in ctl.KNOWN_LIVE:queue[jid]={'status':status,'comment':token}
  return {'rows':rows,'queue':queue,'raw_sacct':'CPU fixture only','raw_squeue':'CPU fixture only'}
 base_snap=snapshot(base_jobs)
 capplan=copy.deepcopy(effective)
 caps,cpus,projection=g.capacity_gate(ctl,newstate(),base_snap,case_auth,capplan)
 okay('all-mode capacity positive with genuine prior identities',caps['occupied']==[] and g.COMPLETED_CONTROLLER_ID in cpus)
 for n in (7,8,9):
  state=newstate()
  modes=['train','development','collect','full','components','engineering','other']
  for i in range(n):
   state['registered_jobs'].append({'job_id':str(899990000+i),'name':'CPU_fixture_'+str(i),'experiment':'formal_main_v2','mode':modes[i%7],'suite':'CPU_fixture_other_suite','status':'RUNNING','exit_code':'0:0','gpus':1,'elapsed_seconds':0})
  snap=snapshot(state['registered_jobs'])
  if n==7:
   got=g.capacity_gate(ctl,state,snap,case_auth,capplan)[0];okay('seven occupied all-mode slots permit exactly one reserved slot',len(got['occupied'])==7)
  else:reject(str(n)+' occupied all-mode slots block',lambda state=state,snap=snap:g.capacity_gate(ctl,state,snap,case_auth,capplan))
 state=newstate();state['pending_submission']={'known_job_id':None}
 reject('unknown pending blocks before submit',lambda:g.capacity_gate(ctl,state,base_snap,case_auth,capplan))
 state=newstate();state['registered_jobs'].append(copy.deepcopy(priorjobs[0]))
 reject('duplicate registered allocation blocks',lambda:g.capacity_gate(ctl,state,base_snap,case_auth,capplan))
 for reserved in (0,2,8):
  state=newstate();state['autonomous_training_v1']['reserved_GPU_slots']=reserved
  reject('dedicated reservation '+str(reserved),lambda state=state:g.capacity_gate(ctl,state,base_snap,case_auth,capplan))
 snap=copy.deepcopy(base_snap);snap['rows']['3042529']['status']='UNKNOWN'
 reject('unknown observed allocation blocks',lambda:g.capacity_gate(ctl,newstate(),snap,case_auth,capplan))
 snap=copy.deepcopy(base_snap);snap['rows']['3042529']['exit_code']='0:0'
 reject('historical terminal status drift blocks',lambda:g.capacity_gate(ctl,newstate(),snap,case_auth,capplan))
 state=newstate();state['registered_jobs']=state['registered_jobs'][:-1]
 reject('no omission of no-child failed allocation',lambda:g.capacity_gate(ctl,state,snapshot(state['registered_jobs']),case_auth,capplan))
 new_overlap=copy.deepcopy(priorjobs[-1]);new_overlap.update(job_id='899999999',status='RUNNING',exit_code='0:0')
 state=newstate();state['registered_jobs'].append(new_overlap)
 reject('active same-stage cannot submit',lambda:g.capacity_gate(ctl,state,snapshot(state['registered_jobs']),case_auth,capplan))
 for out in ('','399999999\n399999998\n','3042529\n','399999999 garbage\n','0399999999\n'):
  reject('ACK ambiguous or duplicate '+repr(out),lambda out=out:g.parse_ack(SimpleNamespace(returncode=0,stdout=out),{'3042529'}))
 okay('ACK exact and cluster suffix accepted',g.parse_ack(SimpleNamespace(returncode=0,stdout='399999999;cluster\n'),set())=='399999999')
 reject('nonzero ACK remains uncertain',lambda:g.parse_ack(SimpleNamespace(returncode=1,stdout='399999999\n'),set()))

 # Synthetic complete state-machine scenarios, never NativeIO or real Slurm.
 original_inv=json.loads(get(priorjobs[-1]['invocation'],priorjobs[-1]['invocation_sha256']))
 bundleplan=copy.deepcopy(effective)
 outer=copy.deepcopy(original_inv);outer.update(pre_dispatch_history=c.descriptor(),legacy12_compatibility=c.compatibility_module().descriptor(),prior_job_ids=['3022743','3042529'],repair_record=c.REPAIR)
 for key in ('registered_utc','plan_sha256','runtime_readiness'):outer.pop(key,None)
 bundleplan['invocation']=outer;bundleplan['plan_sha256']=sig({k:v for k,v in bundleplan.items() if k!='plan_sha256'})
 prepared={**outer,'registered_utc':'2099-01-01T00:00:00+00:00','plan_sha256':bundleplan['plan_sha256'],'runtime_readiness':case_auth['runtime_readiness']}
 bundle={'plan':bundleplan,'invocation':prepared,'invocation_bytes':rawjson(prepared),'prefix':{},'inventory':{}}
 class MockScience:
  def __init__(self):self.plan=copy.deepcopy(bundleplan);self.calls=0
  def prepare(self,state):self.calls+=1;return copy.deepcopy(bundle)
 class MockEvidence:
  def __init__(self):self.hashes={};self.calls=0
  def ref(self,ref):assert ref==case_auth['runtime_readiness'];return {'runtime_publication_files':{}}
  def watch(self,n,h=None):self.hashes[n]=h or '0'*64;return self.hashes[n]
  def unchanged(self):self.calls+=1
 class MockIO:
  def __init__(self,mode):self.mode=mode;self.preflight_calls=0;self.publish_calls=0
  def preflight(self,b):
   self.preflight_calls+=1
   if self.mode=='preflight_failure':raise ValueError('CPU fixture preflight failure')
   return {'CPU_fixture_no_P_access':True}
  def publish(self,b):
   self.publish_calls+=1
   if self.mode=='publish_failure':raise ValueError('CPU fixture publication failure before scheduler')
 class MockController:
  TERMINAL=ctl.TERMINAL
  def __init__(self,mode):self.mode=mode;self.atomic_calls=0;self.cas_expected=[]
  def capacity(self,*args):return ctl.capacity(*args)
  def file_sha(self,p):assert D in Path(p).parents;return ctl.file_sha(p)
  def read_json(self,p):assert D in Path(p).parents;return ctl.read_json(p)
  def exclusive_lock(self,p):assert D in Path(p).parents;return ctl.exclusive_lock(p)
  def atomic_json(self,p,v,expected):
   assert D in Path(p).parents;self.atomic_calls+=1;self.cas_expected.append(expected)
   if (self.mode=='CAS_after_ACK' and self.atomic_calls==2) or (self.mode=='CAS_final' and self.atomic_calls==3):raise ValueError('CPU fixture CAS state drift; not overwritten')
   return ctl.atomic_json(p,v,expected)
 class MockScheduler:
  def __init__(self,mode):self.mode=mode;self.observations=0;self.submits=[];self.scontrol_calls=[];self.newid='399999999'
  def observe(self,jobs):
   self.observations+=1
   snap=snapshot(jobs,self.newid if self.submits else None,new_status='COMPLETED' if self.mode in ('scontrol_success','scontrol_wrong_token') else 'PENDING',wrong_token=self.mode=='wrong_token')
   if self.mode=='missing_accounting' and self.submits:snap['rows'].pop(self.newid,None)
   return snap
  def submit(self,argv):
   assert argv[0]=='sbatch';self.submits.append(copy.deepcopy(argv))
   if self.mode=='submit_timeout':
    e=TimeoutError('CPU fixture timeout after uncertain submission');e.stdout='399999999\n';e.stderr='CPU timeout';raise e
   if self.mode=='ambiguous_ACK':return SimpleNamespace(returncode=0,stdout='399999999\n399999998\n',stderr='')
   if self.mode=='nonzero_ACK':return SimpleNamespace(returncode=1,stdout='399999999\n',stderr='CPU fixture uncertainty')
   if self.mode=='duplicate_ACK':return SimpleNamespace(returncode=0,stdout='3042529\n',stderr='')
   return SimpleNamespace(returncode=0,stdout=self.newid+'\n',stderr='')
  def run(self,argv):
   assert argv==['scontrol','show','job','-o',self.newid];self.scontrol_calls.append(argv)
   token=next(x.split('=',1)[1] for x in self.submits[0] if x.startswith('--comment='))
   if self.mode=='scontrol_wrong_token':token='wrong-token'
   return SimpleNamespace(returncode=0,stdout='JobId='+self.newid+' JobName=cti-formal-downstream JobState=COMPLETED Comment='+token+'\n',stderr='')
 modes=['dry_run','healthy','scontrol_success','preflight_failure','publish_failure','submit_timeout','ambiguous_ACK','nonzero_ACK','duplicate_ACK','missing_accounting','wrong_token','scontrol_wrong_token','CAS_after_ACK','CAS_final']
 for mode in modes:
  root=D/'SYNTHETIC_transaction_cases_NOT_PRODUCTION'/mode/'root'
  statepath=root/g.STATE;statepath.parent.mkdir(parents=True,exist_ok=True)
  initial=newstate();statepath.write_bytes(rawjson(initial));(statepath.parent/'.writer.lock').write_bytes(b'CPU fixture existing writer lock\n')
  mockctl=MockController(mode);sched=MockScheduler(mode);io=MockIO(mode);science=MockScience();evidence=MockEvidence()
  aref={'path':'results/formal_main_v2/CPU_fixture_authorization_NOT_PRODUCTION.json','sha256':'a'*64}
  runner=g.Gateway(root,mockctl,sched,science,io,case_auth,aref,evidence)
  before=sha(statepath.read_bytes());caught=None;result=None
  try:result=runner.run(submit=mode!='dry_run')
  except BaseException as err:caught={'type':type(err).__name__,'message':str(err)}
  actual=json.loads(statepath.read_bytes())
  success=mode in ('healthy','scontrol_success')
  if mode=='dry_run':
   okay('transaction dry run never writes or submits',caught is None and result['status']=='read_only_checks_passed_not_submitted' and sha(statepath.read_bytes())==before and not runner.audit.exists() and not sched.submits and not io.publish_calls and not mockctl.atomic_calls)
  elif success:
   okay('transaction success '+mode,caught is None and result['status']=='submitted_once' and len(sched.submits)==1 and actual['pending_submission'] is None and len(actual['registered_jobs'])==len(base_jobs)+1 and actual['autonomous_training_v1']['reserved_GPU_slots']==0)
   job=actual['registered_jobs'][-1]
   okay('retained predecessor registry '+mode,actual['registered_jobs'][:-1]==initial['registered_jobs'])
   okay('job retains explicit typed and legacy origin '+mode,job['typed_predispatch_history']==c.descriptor() and job['legacy12_compatibility']==c.compatibility_module().descriptor() and job['prior_job_ids']==['3022743','3042529'])
   okay('full immutable exact ACK/corroboration evidence '+mode,(runner.audit/'sbatch_result.json').is_file() and (runner.audit/'submitted_job_observation.json').is_file() and (runner.audit/'committed.json').is_file())
   okay('cost actual fixture includes393plus2once '+mode,actual['current_round_cost']['allocated_gpu_seconds']==395+(2 if mode=='scontrol_success' else 0))
   again=g.Gateway(root,MockController(mode),sched,MockScience(),MockIO(mode),case_auth,aref,MockEvidence())
   reject('new instance cannot repeat submitted request '+mode,lambda again=again:again.run(submit=True))
   okay('only one scheduler request after duplicate try '+mode,len(sched.submits)==1)
  else:
   okay('transaction stops on '+mode,caught is not None and result is None and len(actual['registered_jobs'])==len(base_jobs) and not (runner.audit/'committed.json').exists())
   if mode=='preflight_failure':
    okay('preflight failure no pending/publication/submit',actual==initial and not runner.audit.exists() and not io.publish_calls and not sched.submits)
   else:
    pending=actual['pending_submission']
    okay('uncertainty keeps original pending '+mode,isinstance(pending,dict) and pending['request_token']=='cti-downstream-gateway-v1:'+aref['sha256'] and pending['automatic_retry'] is False and (runner.audit/'failed_transaction.json').is_file())
    okay('one or zero actual scheduler call '+mode,len(sched.submits)==(0 if mode=='publish_failure' else 1))
    if mode in ('missing_accounting','wrong_token','scontrol_wrong_token','CAS_final'):okay('known ACK preserved '+mode,pending.get('known_job_id')==sched.newid)
    if mode=='CAS_after_ACK':okay('original ACK survives CAS conflict',(runner.audit/'sbatch_result.json').is_file() and pending['status']=='prepared_before_invocation_publication')
    if mode=='CAS_final':okay('submission receipt retained before final CAS',(root/'results/formal_main_v2/submissions'/str(sched.newid+'.json')).is_file())
    again=g.Gateway(root,MockController(mode),sched,MockScience(),MockIO(mode),case_auth,aref,MockEvidence())
    reject('uncertain request cannot auto-retry '+mode,lambda again=again:again.run(submit=True))
   okay('unrelated controller fields unchanged '+mode,{k:v for k,v in actual['autonomous_training_v1'].items() if k not in ('reserved_GPU_slots','downstream_reservations_consumed')}=={k:v for k,v in initial['autonomous_training_v1'].items() if k not in ('reserved_GPU_slots','downstream_reservations_consumed')})
  reject('same gateway instance single use '+mode,lambda runner=runner:runner.run(submit=True))
  cases.append({'name':mode,'result':result,'error':caught,'scheduler_submit_calls':len(sched.submits),'scheduler_observe_calls':sched.observations,'scontrol_calls':sched.scontrol_calls,'CAS_calls':mockctl.atomic_calls,'IO_calls':{'preflight':io.preflight_calls,'publish':io.publish_calls},'state_before_sha256':before,'state_after_sha256':sha(statepath.read_bytes()),'scope':'CPU fixtures; not real jobs, costs, authorization or deployment'})
 g.completed_training_development_gate=original_completed
 g.load=real_load

 # Exercise unmodified NativeIO against explicit private filesystem roots.
 nio=module('_ind_nativeIO_private',B/'gateway.py',GPIN)
 sandbox=D/'SYNTHETIC_NativeIO_NOT_PRODUCTION';sr=sandbox/'R';sp=sandbox/'P';ss=sp/'snapshots/source'
 sr.mkdir(parents=True);sp.mkdir();ss.mkdir(parents=True)
 nio.P=sp;nio.S=ss
 sourcefile=sr/'scripts/CPU_fixture.py';sourcefile.parent.mkdir();sourcefile.write_bytes(b'CPU fixture metadata, not executable production code\n')
 h=sha(sourcefile.read_bytes());outrel='results/formal_main_v2/CPU_fixture_output'
 (sp/outrel).mkdir(parents=True)
 invrel='results/formal_main_v2/invocations/CPU_fixture_NOT_PRODUCTION.json'
 nb={'plan':{'publish_files':{'scripts/CPU_fixture.py':h},'output_relative':outrel,'output_must_exist':True,'invocation_relative':invrel},'invocation':{'watched_files':{}},'prefix':{},'readiness_files':{},'invocation_bytes':b'{"CPU_fixture_NOT_PRODUCTION":true}\n'}
 native=nio.NativeIO(sr)
 initial=native.preflight(nb)
 okay('NativeIO exact missing metadata permitted only before publication',initial['missing_publications']==['scripts/CPU_fixture.py'])
 bad=copy.deepcopy(nb);bad['invocation']['watched_files'][str(sp/'results/formal_main_v2/missing_input.json')]='0'*64
 reject('NativeIO missing non-publication input',lambda:native.preflight(bad))
 bad=copy.deepcopy(nb);bad['plan']['publish_files']={'results/checkpoints/model.pt':'0'*64}
 reject('NativeIO weights forbidden',lambda:native.preflight(bad))
 bad=copy.deepcopy(nb);bad['plan']['publish_files']={'results/formal_main_v2/invocations/foreign.json':'0'*64}
 reject('NativeIO unrelated invocation publication forbidden',lambda:native.preflight(bad))
 bad=copy.deepcopy(nb);bad['invocation']['watched_files'][str(sandbox/'outside.json')]='0'*64
 reject('NativeIO outside P source forbidden',lambda:native.preflight(bad))
 symlink=sp/'scripts';symlink.mkdir();(symlink/'link.py').symlink_to(sourcefile)
 bad=copy.deepcopy(nb);bad['invocation']['watched_files'][str(symlink/'link.py')]=h
 reject('NativeIO source symlink forbidden',lambda:native.preflight(bad))
 (symlink/'link.py').unlink()
 okay('owned private symlink fixture removed after rejection',not (symlink/'link.py').is_symlink())
 native.publish(nb)
 okay('NativeIO private publication exact bytes',sha((sp/'scripts/CPU_fixture.py').read_bytes())==h and (sp/invrel).read_bytes()==nb['invocation_bytes'])
 reject('NativeIO repeated invocation publication refused',lambda:native.publish(nb),(FileExistsError,ValueError))
 reject('NativeIO existing invocation prevents retry',lambda:native.preflight(nb))
 (sp/'scripts/CPU_fixture.py').write_bytes(b'CPU fixture conflicting existing bytes\n')
 reject('NativeIO does not overwrite conflicting metadata',lambda:native.publish(nb))
 okay('conflicting private bytes preserved',(sp/'scripts/CPU_fixture.py').read_bytes()==b'CPU fixture conflicting existing bytes\n')

 # Original consumer semantics remain an explicit bounded12+588 lineage.
 control_raw=(C/'control.py').read_bytes()
 tree=ast.parse(control_raw)
 reviewer_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='reviewer_module')
 text=ast.get_source_segment(control_raw.decode(),reviewer_node)
 okay('consumer keeps twelve legacy and588 current explicitly',all(x in text for x in ["'original_legacy_prefix_trials':12","'new_action_trials':588","'eligible_for_current_action_global_freeze':False","'legacy_compatible_trials':12","'current_wrapper_trials':588","'profiling_authorized':False"]))
 from_script=get('scripts/ops/formal_action_deployment_v1/consumer.py','16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034').decode()
 okay('original consumer still rebuilds and compares whole saved report','rebuilt = mod.review' in from_script and 'New root review does not exactly rebuild' in from_script)
 canonical_seen={}
 for rel,pin in files.items():
  p=R/rel
  if p.exists():
   okay('concurrent root canonical installed bytes exact '+rel,sha(p.read_bytes())==pin)
   canonical_seen[rel]={'exists':True,'sha256':pin}
  else:canonical_seen[rel]={'exists':False}
 partial['canonical_sources_at_independent_review']=canonical_seen
 okay('audit write locations remain explicitly private',D.parent==R/'.local' and not any(p.is_symlink() for p in D.rglob('*')))
 for rel,row in reads.items():assert sha((R/rel).read_bytes())==row['sha256'],rel
 write(D/'CPU_transaction_cases.json',{'kind':'isolated_CPU_state_machine_cases_NOT_PRODUCTION','cases':cases,'new_GPU_seconds':0,'new_real_submissions':0,'actual_P_writes':False})
 detail=write(D/'independent_CPU_checks.json',{'schema':'formal_main_v2','kind':'Spatial588_gateway_independent_CPU_checks','status':'passed_CPU_review','check_count':len(checks),'checks':checks,'partial_real_metadata_evidence':partial,'actual_state_snapshot_sha256':sha(state_bytes),'state_snapshot_not_polled':True,'new_real_submissions':0})
 evidence=write(D/'evidence.json',{'files_read':reads,'canonical_source_closure_projection':files,'source_projection_not_actual_install':True,'original_AST_changed_definitions':changed,'new_GPU_seconds':0})
 report={
  'schema':'formal_main_v2','kind':'formal_downstream_server_gateway_independent_CPU_review','status':'passed_CPU_review','review_role':'independent','reviewed_by':'independent','review_agent':'/root/goal_cpu_gate_2054','blockers':[],
  'production_blockers':[
   {'id':'SP588_CANONICAL_INSTALL','reason':'Exact canonical gateway and phase2_v2 installation must match this independently reviewed source map; concurrent root installations are reported separately and do not establish actual P readiness.'},
   {'id':'SP588_REAL_PLAN_AND_ROOT_ADOPTION','reason':'Only CPU plan fixtures were exercised; publish genuine explicit root legacy12 adoption/history repair, original scientific/effective plans and original transition with exact prior3022743/3042529.'},
   {'id':'SP588_RUNTIME_READINESS_AND_P_VERIFY','reason':'No actual new runtime root/independent/component readiness, prepared invocation, or new P wrapper --verify receipt has been produced by this audit.'},
   {'id':'SP588_EXACT_AUTH_AND_CAPACITY','reason':'Root must freeze one actual authorization SHA, reserve one slot under shared lock, then run fresh complete metadata/Slurm capacity/preflight checks before one submission.'},
   {'id':'SP588_TERMINAL_CONSUMER','reason':'No new588 trials exist from this audit. Actual600 terminal original consumer and independent audit must preserve legacy12 origin and current588 labels before acceptance.'}],
  'files':files,'canonical_source_scope_is_install_projection':True,'actual_new_canonical_P_verified':False,'production_admission':False,
  'candidate_manifest':MREF,'phase2_independent':PHASE2,'check_count':len(checks),'checks_ref':detail,'evidence_ref':evidence,
  'isolated_Gateway_run_state_machine_cases':len(cases),'NativeIO_test_scope':'Private synthetic filesystem roots only; original NativeIO AST and Gateway.run AST remain unchanged.',
  'actual_normal_controller_metadata_and_released_lease_checked':True,'new_live_Slurm_observation_performed':False,
  'scope':{'suite':'libero_spatial','stage':'development','methods':allowed['method_ids'],'attempt':3,'retained_legacy_trials':12,'new_current_wrapper_trials':588,'total_registered_trials':600,'real_historical_GPU_seconds':395,'failed_predispatch_GPU_seconds':2,'no_fake_failed_ledger_invocation':True},
  'source_control_separate_from_science':True,'frozen173_mutated':False,'state_mutated':False,'Git_mutated':False,'P_mutated':False,'new_real_submissions':0,'new_GPU_seconds':0,'new_scientific_trials':0,'sealed_values_read':False,'weights_read':False,
  'scientific_completion_claimed':False,'global_release':False,'profiling_authorized':False,
  'root_integration_requirements':['Install only pinned canonical source maps; regenerate descriptors and explicitly adopt separate root/independent records, never copy private CPU approvals.','Build genuine original-derived scientific/effective plans, transition, contract, separate root/independent runtime readiness and original-consumer evidence; bind typed history plus legacy12 descriptor.','Publish exact metadata on server and complete original actual P wrapper --verify for this new invocation before a separately pinned single-use authorization.','Under writer lock/CAS check all registered modes against capacity8, reserve one slot, ensure original3034538 COMPLETED0:0 and lease free; no controller restart.','After any ambiguous submit, keep pending and original ACK/comment/token and reconcile; never clear or retry.','Root and independent terminal review must reconstruct all raw600, accepted12 compatibility, current588 runtime and393+2+new cost exactly once; retain all failures.'],
  'limitations':['Mock scheduler replies, mock approvals, fixture registry files, P-like paths and fixture GPU seconds are explicitly CPU synthetic and cannot authorize or count as experiments.','The entire production authorization/FrozenPlan/NativeIO transaction remains unexecuted by this audit; genuine canonical adoption, full runtime readiness and actual P inputs must be checked independently.','This exact gateway does not support other pairs, suites, budgets, engineering retries, collection, timing or final release.'],
  'utc':datetime.now(timezone.utc).isoformat()}
 review=write(D/'independent_review.json',report)
 allfiles=[p for p in D.rglob('*') if p.is_file()]
 delivery={'schema':'formal_main_v2','kind':'Spatial588_gateway_independent_delivery','status':'passed_CPU_review','production_admission':False,'review':review,'file_count':len(allfiles),'files':[{'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(allfiles)],'new_GPU_seconds':0,'new_scientific_trials':0}
 ref=write(D/'delivery_manifest.json',delivery)
 print(json.dumps({'status':'passed_CPU_review','checks':len(checks),'transaction_cases':len(cases),'review':review,'manifest':ref,'file_count':len(allfiles)}))
except BaseException as exc:
 if not (D/'failure_a1.json').exists():write(D/'failure_a1.json',{'error':repr(exc),'traceback':traceback.format_exc(),'checks':checks,'cases':cases,'partial':partial,'new_GPU_seconds':0,'production_admission':False})
 raise

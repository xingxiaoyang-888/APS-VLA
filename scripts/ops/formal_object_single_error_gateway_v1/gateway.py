"""One exact Object policy-error attempt. Native held submission; no generic dispatch."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
from contextlib import contextmanager
import argparse,copy,fcntl,hashlib,importlib.util,json,os,re,shlex,stat,subprocess,sys,time
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
H=Path('/share/home/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
BASE='scripts/ops/formal_object_single_error_gateway_v1'
PROD='scripts/ops/formal_object_single_error_v1'
X='results/formal_main_v2/execution/object_single_error_v1'
STATE='results/experiment_supervisor/state.json'
EXPERIMENT='formal_main_v2';VERSION='object-single-error-atomic-gateway-v1'
NAMES=('gateway.py','build.py','run.slurm')
PLAN=X+'/plan.json';PREPARED=X+'/prepared_invocation.json';AUTH=X+'/submission_authorization.json'
INV='results/formal_main_v2/invocations/object_single_error_task08_state0049_dense_attempt01.json'
OUT='results/formal_main_v2/libero_object/downstream/linked_policy_error_correction/task08_state0049_dense/attempt01'
STAGE='object_single_error_task08_state0049_dense_attempt01';NAME='cti_object_linked_t8s49d1'
MODE='object_single_error_linked';PAIR='c39b5da58df0b9e0e0e3e5de896906460bc4db2ec7d02b89f9254f04f1a2fb1a'
CELL='libero_object:pick_up_the_chocolate_pudding_and_place_it_in_the_basket:state-0049:env-0:dense'
SCOPE='2d63670412abc28d3217242151ebf82f309ea93c1bb0e90478d817cf58d4a7b4'
SOURCE='dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e'
METHODS=['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17']
OLD_IDS=['3021394','3021603','3021844'];OLD_SECONDS=[386,1401,4926]
FAILURE_SHA='d7f134683c6e01c8667731c6ca6807290d91d7816d28197f48232de9bc271eb0'
OWNER='results/formal_main_v2/autonomous_training/run_v1/owner.json'
OWNER_SHA='2ba2100d6f20e8a00f7853e193d1546b3d7c4195f174c75d54605ec504e33bc2'
LEASE='results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock'
CONTROLLER='scripts/ops/formal_autonomous_training_v1/controller.py'
CONTROLLER_SHA='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
ARCHIVE='results/formal_main_v2/engineering/supervision_delivery_20261020T2358'
PUB=ARCHIVE+'/Object_single_error_production/publication_map.json'
PUB_SHA='030d0b13560ca1580c258440b8b6e2f1aeaaaf478066f8cb259a3b407897de08'
PROD_REVIEW=ARCHIVE+'/Object_single_error_production_independent/independent_review.json'
PROD_REVIEW_SHA='bdf8af2bdfe21954047a6b6209f0a4f3beac73ecb260df4bff33b69b5fa58baa'
ADOPTION=X+'/root_legacy_adoption.json';ADOPTION_SHA='c431646cbac00f461177e95361fb8d31d66c78bcfbbfc2b5c766edb8eabd6d24'
ROWS=X+'/legacy599_adoption_rows.jsonl';ROWS_SHA='ac792e8d88f251f097f3f0e110e6c32aa45dbacd103404c0189b3bebf56ccb5e'
RESOURCES=dict(job_name=NAME,account='p_p15016',qos='cpu-500_core-l40-8_card-a800-8_card',partition='L40',nodes=1,ntasks=1,cpus_per_task=7,gres='gpu:l40:1',mem='64G',time='00:30:00')
def require(v,m):
 if not v:raise ValueError(m)
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def safe(p):
 p=Path(p);require(p.is_absolute() and '..' not in p.parts and not any(x.is_symlink() for x in (p,*p.parents)),'absolute nonlink path required');return p
def relative(p):
 require(type(p)is str and p==str(PurePosixPath(p)) and not p.startswith('/') and '..' not in PurePosixPath(p).parts and '\\' not in p and ':' not in p,'unsafe relative path')
 require(not any(x in p.lower() for x in ('sealed','/checkpoints/','/weights/')),'restricted path')
 return p
def raw(p,pin=None):
 p=safe(p);a=p.stat();b=p.read_bytes();z=p.stat()
 require(stat.S_ISREG(z.st_mode) and (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns),'file changed during read')
 require(pin is None or sha(b)==pin,'source/evidence SHA differs: '+str(p));return b
def read(p,pin=None):return json.loads(raw(p,pin),parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def ref(root,rel):
 b=raw(root/relative(rel));return dict(path=rel,bytes=len(b),sha256=sha(b))
def read_ref(root,r,path=None):
 require(type(r)is dict and set(r)=={'path','bytes','sha256'} and (path is None or r['path']==path),'exact typed reference required')
 b=raw(root/relative(r['path']),r['sha256']);require(len(b)==r['bytes'],'reference size differs');return json.loads(b)
def immutable(p,b,allow_identical=False):
 p=safe(p)
 if p.exists():
  require(allow_identical and raw(p)==b,'preexisting immutable artifact; never overwrite');return
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
def record(p,v,allow_identical=False):immutable(p,canonical(v)+b'\n',allow_identical)
def load(p,pin,name):
 b=raw(p,pin);m=importlib.util.module_from_spec(importlib.util.spec_from_file_location(name,p));sys.modules[name]=m
 exec(compile(b,str(p),'exec',dont_inherit=True),m.__dict__);return m
def controller():return load(R/CONTROLLER,CONTROLLER_SHA,'_object_single_exact_controller')
def source_map(root=R):
 return {BASE+'/'+n:sha(raw(root/BASE/n)) for n in NAMES}
def production_map():
 j=read(R/PUB,PUB_SHA);m={r['destination']:r['sha256'] for r in j['files']}
 require(len(m)==10 and all(n.startswith(PROD+'/') for n in m),'original ten-file scope')
 return m
def production_modules():
 m=production_map()
 for root in (R,P):
  for n,h in m.items():raw(root/n,h)
 for name in ('fixed','constants','adoption','iterator','execution','wrapper','gateway_contract'):
  rel=PROD+'/'+name+'.py'
  if name in sys.modules:require(Path(sys.modules[name].__file__)==R/rel,'module name collision')
  else:
   sys.path.insert(0,str(R/PROD))
   try:load(R/rel,m[rel],name)
   finally:sys.path.pop(0)
 return tuple(sys.modules[n] for n in ('fixed','constants','adoption','wrapper','gateway_contract'))
def authorization(pin):
 a=read(R/AUTH,pin);require(raw(P/AUTH,pin)==raw(R/AUTH,pin),'root/runtime authorization differ')
 expected=dict(schema=EXPERIMENT,kind='Object_single_error_exact_submission_authorization',version=VERSION,
  status='approved_for_exactly_one_held_submission',reviewed_by='root',stage_key=STAGE,logical_trial_id=CELL,
  pair_id=PAIR,scope_sha256=SCOPE,maximum_attempts=1,automatic_retry=False,ordinary_resume=False,
  original_GPU_seconds=6713,original_job_ids=OLD_IDS,full_manifest_trials=600,actual_trial_allowlist=[CELL],
  final_allowed=False,resources=RESOURCES,control_root=str(R),runtime_root=str(P))
 require(all(a.get(k)==v for k,v in expected.items()),'exact root authorization differs')
 require(a.get('gateway_files')==source_map() and a.get('production_sources')==production_map(),'authorized source closure differs')
 F,C,A,W,G=production_modules()
 plan=read_ref(R,a['plan'],PLAN);require(raw(P/PLAN)==raw(R/PLAN),'actual plan bytes differ')
 ready=read_ref(R,a['runtime_readiness'],X+'/runtime_readiness.json')
 require(raw(P/a['runtime_readiness']['path'])==raw(R/a['runtime_readiness']['path']),'actual readiness bytes differ')
 inv=read_ref(R,a['prepared_invocation'],PREPARED)
 expected_inv=dict(schema=EXPERIMENT,kind='Object_single_error_bound_invocation',version=C.VERSION,plan=ref(R,PLAN),
  plan_sha256=F.sig(plan),production_sources=production_map(),runtime_readiness=ref(R,X+'/runtime_readiness.json'),
  submission_token=G.token(plan),slurm_comment='cti-object-single-error:'+G.token(plan),
  job_name=NAME,account=RESOURCES['account'],partition=RESOURCES['partition'],
  slurm_output=str(P/'results/slurm'/('cti_object_linked_t8s49d1_%j.out')),registered_utc=inv.get('registered_utc'))
 require(inv==expected_inv and datetime.fromisoformat(inv['registered_utc']).tzinfo is not None,'exact immutable invocation changed')
 context=W.verify_invocation(inv,project=P)
 ind=read_ref(P,ready['gateway_independent'],X+'/gateway_independent.json')
 require(ind.get('gateway_files')==source_map() and ind.get('production_sources')==production_map()
  and ind.get('review_scope')=='source_and_CPU_only' and ind.get('GPU_execution_authorized') is False
  and ind.get('blockers')==[],'actual gateway source/CPU review missing')
 for n,h in source_map().items():raw(P/n,h)
 require(a['actual_P_verification']==ref(R,X+'/actual_P_verification.json'),'actual-P verification source differs')
 verification=read_ref(R,a['actual_P_verification'])
 require(verification.get('returncode')==0 and verification.get('actual_P_output')==context['static_verification']
  and verification.get('production_sources')==production_map(),'new actual-P entry not verified')
 read(R/ADOPTION,ADOPTION_SHA);raw(R/ROWS,ROWS_SHA)
 return dict(authorization=a,authorization_ref=ref(R,AUTH),plan=plan,invocation=inv,
  invocation_bytes=raw(R/PREPARED),context=context,token=inv['submission_token'],
  comment=inv['slurm_comment'],sources={**source_map(),**production_map()})

def sbatch_argv(bundle):
 inv=bundle['invocation'];h=sha(bundle['invocation_bytes'])
 require(inv['job_name']==NAME and inv['slurm_comment']==bundle['comment'],'invocation job identity differs')
 return ['sbatch','--hold','--parsable','--no-requeue','--exclude=gpu4020','--comment='+bundle['comment'],
  *['--'+k.replace('_','-')+'='+str(v) for k,v in RESOURCES.items()],
  '--chdir='+str(S),'--output='+inv['slurm_output'],'--error='+str(P/'results/slurm'/(NAME+'_%j.err')),
  '--export=ALL',str(P/BASE/'run.slurm'),h]
def parse_ack(answer,known):
 require(answer.get('returncode')==0,'sbatch uncertain nonzero result')
 m=re.fullmatch(r'([1-9][0-9]*)(?:;[A-Za-z0-9_.-]+)?\n?',answer.get('stdout',''))
 require(m is not None and m[1] not in known,'missing/ambiguous/old original ACK')
 return m[1]
def fields(text):
 rows=[x for x in text.splitlines() if x.strip()];require(len(rows)==1,'single actual scontrol row required')
 entries=[x.split('=',1) for x in rows[0].split() if '=' in x]
 require(len(entries)==len({k for k,v in entries}),'duplicate scontrol field')
 return dict(entries)
def argv_of(job):
 values=[]
 for obj in (job,job.get('downstream_gateway',{}),job.get('autonomous_control',{}),job.get('startup_recovery',{}),job.get('object_single_error_gateway',{})):
  if obj.get('actual_sbatch_argv'):values.append(obj['actual_sbatch_argv'])
 require(values and all(v==values[0] for v in values),'actual active sbatch argv absent/conflicting')
 return values[0]
def option(argv,key):
 found=[x.split('=',1)[1] for x in argv if x.startswith('--'+key+'=')]
 require(len(found)==1 and found[0],'unique actual argv option required: '+key);return found[0]
def expected_live(job):
 argv=argv_of(job);jid=str(job['job_id']);name=option(argv,'job-name')
 output=option(argv,'output').replace('%x',name).replace('%j',jid)
 return dict(JobId=jid,JobName=name,Comment=option(argv,'comment'),Account=option(argv,'account'),
  Partition=option(argv,'partition'),StdOut=output)
def validate_live_identity(job,f,queue=None):
 expected=expected_live(job)
 for k,v in expected.items():require(f.get(k)==v,'actual active Slurm identity differs '+k)
 require(job.get('name',job.get('job_name'))==expected['JobName'],'registered name differs')
 if job.get('job_name'):require(job['job_name']==expected['JobName'],'registered dual name differs')
 for k,slurm in [('slurm_comment','Comment'),('account','Account'),('partition','Partition')]:
  if job.get(k):require(job[k]==f[slurm],'registered '+k+' differs')
 require(f.get('TresPerNode')=='gres:gpu:l40:1' and job.get('gpus')==1,'one registered requested GPU required')
 if queue:require(f['JobState']==queue['status'] and f['Comment']==queue['comment'],'queue/scontrol differs')
 return expected
def validate_new_identity(job,bundle,f,held):
 validate_live_identity(job,f)
 expected=dict(Requeue='0',TimeLimit='00:30:00',Partition='L40',Account='p_p15016',ExcNodeList='gpu4020',
  NumCPUs='7',MinMemoryNode='64G',Command=str(P/BASE/'run.slurm'),WorkDir=str(S),Restarts='0',
  QOS=RESOURCES['qos'],TresPerNode='gres:gpu:l40:1')
 for k,v in expected.items():require(f.get(k)==v,'actual held/new Slurm resource differs '+k)
 require(f.get('Comment')==bundle['comment'],'new token/comment differs')
 if held:require(f.get('JobState')=='PENDING' and f.get('Reason')=='JobHeldUser','must remain held before registration/release')
 else:require(f.get('JobState') in {'RUNNING','PENDING','CONFIGURING','COMPLETING','COMPLETED'}
  and f.get('Reason')!='JobHeldUser','release unknown/failed; never resend')
 return f
def duplicate(j):
 return (j.get('mode')==MODE or j.get('stage_key')==STAGE or j.get('logical_trial_id')==CELL
  or j.get('invocation')==INV or j.get('run_root') in (OUT,str(P/OUT))
  or j.get('linked_failure_sha256')==FAILURE_SHA or j.get('name',j.get('job_name'))==NAME
  or str(j.get('slurm_comment','')).startswith('cti-object-single-error:'))
def object_overlap(j):
 text=' '.join(str(j.get(k,'')) for k in ('suite','stage_key','run_root','name','job_name')).lower()
 return j.get('pair_id')==PAIR or 'object' in text
def normalized_projection(c,state,observation,details,*,allow_job=None):
 jobs=state['registered_jobs'];ids=[str(j['job_id']) for j in jobs]
 require(len(ids)==len(set(ids)) and all(re.fullmatch('[1-9][0-9]*',j) for j in ids),'duplicate/invalid registry ID')
 require(set(observation['rows'])==set(ids) and set(observation['queue'])<=set(ids),'all registered accounting required')
 caps=c.capacity(jobs,observation,'3034538')
 require(not caps['unknown'] and not caps['findings'],'unknown/stale allocation blocks')
 require(set(details)==set(caps['occupied']),'all and only occupied GPU details required')
 for j in jobs:
  jid=str(j['job_id']);row=observation['rows'][jid]
  require(not j.get('name') or row['scheduler_name']==j['name'],'accounting registered name differs')
  if jid in details:
   validate_live_identity(j,details[jid],observation['queue'].get(jid))
   require(details[jid]['JobState']==row['status'],'sacct/scontrol disagree')
   require(not object_overlap(j) or jid==allow_job,'same pair or Object allocation occupied')
  require(not duplicate(j) or jid==allow_job,'any previous/incomplete/terminal correction forbids repeat')
 for jid,seconds in zip(OLD_IDS,OLD_SECONDS):
  row=observation['rows'][jid]
  require(row['status']=='COMPLETED' and row['exit_code']=='0:0' and row['elapsed_seconds']==seconds and row['gpus']==1,'original allocation/cost changed')
 ctl=state['autonomous_training_v1'];progress=state['formal_main_progress'];r=observation['rows']['3034538']
 require(ctl.get('pending_submission') is None,'unresolved autonomous pending blocks exact correction')
 pending=state.get('pending_submission')
 require(pending is None or (allow_job is not None and type(pending)is dict and pending.get('kind')=='Object_single_error_durable_pending' and pending.get('stage_key')==STAGE and pending.get('logical_trial_id')==CELL and pending.get('known_job_id')==allow_job),'unresolved/foreign root pending blocks projection')
 require(r['status']=='COMPLETED' and r['exit_code']=='0:0' and r['gpus']==0 and '3034538' not in observation['queue'],'controller not normally complete')
 require(ctl.get('controller_job_id')=='3034538' and ctl.get('blocked_pairs')=={}
  and ctl.get('last_result')=={'status':'training_matrix_complete','completed_pairs':36,'completed_selectors':72},'controller completion differs')
 require(progress.get('root_and_independent_completed_arms')==72 and progress.get('root_and_independent_reviewed_arm_updates')==360000
  and progress.get('trained_arms')==progress.get('expected_arms')==72,'root72 completion absent')
 expected={f'{s}_k{k}_seed{n}' for s in ('libero_10','libero_spatial','libero_object','libero_goal') for k in (256,128,64) for n in (17,23,41)}
 pairs=ctl.get('completed_pairs',{})
 require(set(pairs)==set(progress.get('completed_training_pairs',{}))==expected
  and all(x.get('decision')=='complete' and x.get('completed_by_arm')=={'A':5000,'B':5000} and x.get('selected_checkpoints_verified') is True for x in pairs.values()),'all original36 pairs required')
 require(progress.get('test_opened') is False and progress.get('global_release_created') is False and progress.get('completed_final_trials')==0,'final must remain sealed')
 require(ctl.get('root_submission_hold') is None,'root submission hold')
 reserved=ctl.get('reserved_GPU_slots');require(type(reserved)is int and reserved>=0,'bad reservation')
 require(len(caps['occupied'])+reserved+(0 if allow_job else 1)<=8,'all modes/reservations exceed8')
 projection=[dict(job_id=str(j['job_id']),status=observation['rows'][str(j['job_id'])]['status'],
  gpus=observation['rows'][str(j['job_id'])]['gpus'],elapsed_seconds=observation['rows'][str(j['job_id'])]['elapsed_seconds'],
  registration_sha256=sha(canonical(j)),identity=details.get(str(j['job_id']))) for j in jobs]
 return dict(occupied=caps['occupied'],reserved_GPU_slots=reserved,registered_projection=projection,
  original_GPU_seconds=6713,allocated_formal_GPU_seconds=sum(observation['rows'][str(j['job_id'])]['elapsed_seconds']*
    observation['rows'][str(j['job_id'])]['gpus'] for j in jobs if j.get('experiment')==EXPERIMENT))
@contextmanager
def shared_writer_lock():
 path=safe(R/'results/experiment_supervisor/.writer.lock');require(path.is_file(),'existing shared writer lock required')
 with path.open('r+b') as f:
  inode=(os.fstat(f.fileno()).st_dev,os.fstat(f.fileno()).st_ino);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   st=path.stat();require(inode==(st.st_dev,st.st_ino),'writer lock inode changed');yield
  finally:fcntl.flock(f,fcntl.LOCK_UN)
def probe_lease(state,controller_row):
 owner=read(R/OWNER,OWNER_SHA);p=safe(R/LEASE);before=p.stat()
 require(owner.get('lock')==str(p) and owner.get('owner_id')==state['autonomous_training_v1'].get('owner_id')
  and owner.get('coordinator_job_id')=='3034538' and owner.get('hostname')==controller_row.get('node'),'original owner identity differs')
 with p.open('rb') as f:
  fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   st=os.fstat(f.fileno());after=p.stat()
   require((before.st_dev,before.st_ino)==(st.st_dev,st.st_ino)==(after.st_dev,after.st_ino),'lease inode changed')
   raw(R/OWNER,OWNER_SHA)
  finally:fcntl.flock(f,fcntl.LOCK_UN)
 return dict(owner_sha256=OWNER_SHA,lease_available_measured=True,lease_path=LEASE,lease_inode=before.st_ino,lease_device=before.st_dev)
def actual_observation(c,scheduler,jobs):
 # Historical registry statuses are never overwritten: sacct is authoritative
 # for deciding which registered IDs still exist in the live queue.
 ids=[str(j['job_id']) for j in jobs]
 require(len(ids)==len(set(ids)) and all(re.fullmatch('[1-9][0-9]*',v) for v in ids),'invalid registered IDs')
 argv=['sacct','-n','-X','-P','-j',','.join(ids),'--format=JobIDRaw,State,ExitCode,ElapsedRaw,AllocTRES,NodeList,JobName%128,Comment%128']
 answer=scheduler.run(argv);require(answer.returncode==0,'sacct failed: '+answer.stderr)
 rows=c.parse_sacct(answer.stdout,set(ids));require(set(rows)==set(ids),'missing registered allocation')
 queries=[dict(argv=argv,returncode=answer.returncode,stdout=answer.stdout,stderr=answer.stderr)]
 initial_raw=answer.stdout;confirmation=None
 stale=[str(j['job_id']) for j in jobs if c.state_name(j.get('status','UNKNOWN')) not in c.TERMINAL and rows[str(j['job_id'])]['status'] in c.TERMINAL]
 if stale:
  confirm=scheduler.run(argv);require(confirm.returncode==0,'terminal confirmation sacct failed: '+confirm.stderr)
  again=c.parse_sacct(confirm.stdout,set(ids));require(set(again)==set(ids),'terminal confirmation missing allocation')
  terminal=[v for v in ids if rows[v]['status'] in c.TERMINAL]
  require(all(rows[v]==again[v] for v in terminal),'terminal changed between complete accounting observations')
  queries.append(dict(argv=argv,returncode=confirm.returncode,stdout=confirm.stdout,stderr=confirm.stderr))
  confirmation=dict(stale_registry_terminal_ids=stale,all_initial_terminal_rows_confirmed=terminal,raw_sacct=confirm.stdout)
  rows=again;answer=confirm
 live=[v for v in ids if rows[v]['status'] not in c.TERMINAL]
 require(all(rows[v]['status'] in c.KNOWN_LIVE for v in live),'unknown actual scheduler state')
 queue={};rawq=''
 if live:
  argv=['squeue','-h','-j',','.join(live),'-o','%i|%T|%k'];q=scheduler.run(argv)
  require(q.returncode==0,'squeue failed: '+q.stderr);rawq=q.stdout
  queries.append(dict(argv=argv,returncode=q.returncode,stdout=q.stdout,stderr=q.stderr))
  for line in rawq.splitlines():
   if not line.strip():continue
   row=line.split('|');require(len(row)==3 and row[0] in live and row[0] not in queue,'unexpected queue row')
   queue[row[0]]=dict(status=c.state_name(row[1]),comment=row[2])
  require(set(queue)==set(live),'active accounting/queue race or missing live job; retry read-only only')
 return dict(rows=rows,queue=queue,raw_sacct=answer.stdout,raw_squeue=rawq,queries=queries,initial_raw_sacct=initial_raw,terminal_confirmation=confirmation)
class Native:
 def __init__(self,bundle):
  self.bundle=bundle;self.c=controller();self.scheduler=self.c.Slurm(timeout=30)
  self.audit=R/X/'gateway_attempt01';self.path=R/STATE
 def lock(self):return shared_writer_lock()
 def read_state(self):
  b=raw(self.path);return json.loads(b),sha(b)
 def cas(self,state,expected):self.c.atomic_json(self.path,state,expected);return sha(raw(self.path))
 def fact(self,name,value):record(self.audit/name,value)
 def fact_read(self,name):return read(self.audit/name)
 def fact_exists(self,name):return (self.audit/name).exists()
 def observe(self,state,allow_job=None):
  obs=actual_observation(self.c,self.scheduler,state['registered_jobs']);details={};queries=[]
  caps=self.c.capacity(state['registered_jobs'],obs,'3034538')
  require(not caps['unknown'] and not caps['findings'],'incomplete real accounting')
  for jid in caps['occupied']:
   answer=self.scheduler.run(['scontrol','show','job','-o',jid]);require(answer.returncode==0,'active scontrol unavailable')
   details[jid]=fields(answer.stdout);queries.append(dict(argv=['scontrol','show','job','-o',jid],returncode=answer.returncode,stdout=answer.stdout,stderr=answer.stderr))
  derived=normalized_projection(self.c,state,obs,details,allow_job=allow_job)
  lease=probe_lease(state,obs['rows']['3034538'])
  return dict(utc=utc(),observation=obs,details=details,scontrol_queries=queries,derived=derived,lease=lease)
 def absent(self):
  require(not self.audit.exists(),'prior audit/pending/failed attempt exists; reconcile only')
  for root in (R,P):require(not (root/INV).exists(),'immutable invocation already exists')
  require(not (P/OUT).exists() and not (P/'results/formal_main_v2/object_single_error_invocations'/(STAGE+'.once_claim.json')).exists(),'runtime attempt already exists')
 def revalidate(self):
  checked=authorization(self.bundle['authorization_ref']['sha256'])
  require(checked['invocation_bytes']==self.bundle['invocation_bytes'] and checked['sources']==self.bundle['sources'],'source/readiness changed')
 def publish_invocation(self):
  for root in (R,P):immutable(root/INV,self.bundle['invocation_bytes'])
 def submit(self,argv):
  require(argv==sbatch_argv(self.bundle),'only exact held argv')
  answer=self.scheduler.submit(argv)
  return dict(returncode=answer.returncode,stdout=answer.stdout,stderr=answer.stderr,actual_sbatch_argv=argv)
 def actual(self,jid,held):
  a=self.scheduler.run(['scontrol','show','job','-o',jid]);require(a.returncode==0,'exact new scontrol unavailable')
  j=job_record(jid,self.bundle,sbatch_argv(self.bundle))
  f=fields(a.stdout);validate_new_identity(j,self.bundle,f,held)
  return dict(fields=f,returncode=a.returncode,stdout=a.stdout,stderr=a.stderr,argv=['scontrol','show','job','-o',jid])
 def release(self,jid):
  a=self.scheduler.run(['scontrol','release',jid])
  return dict(argv=['scontrol','release',jid],returncode=a.returncode,stdout=a.stdout,stderr=a.stderr)
 def committed(self,jid,state,expected,obs):
  rows=[j for j in state['registered_jobs'] if str(j['job_id'])==jid];require(len(rows)==1,'new registered ID lost')
  row=obs['observation']['rows'][jid];require(row['status'] not in {'FAILED','TIMEOUT','PREEMPTED','CANCELLED','NODE_FAIL','OUT_OF_MEMORY','BOOT_FAIL'},'failed new allocation requires root diagnosis')
  for k in ('status','exit_code','elapsed_seconds','allocation','node'):rows[0][k]=row[k]
  state['pending_submission']=None
  state.setdefault('current_round_cost',{})['registered_jobs']=sum(j.get('experiment')==EXPERIMENT for j in state['registered_jobs'])
  state['current_round_cost']['allocated_gpu_seconds']=obs['derived']['allocated_formal_GPU_seconds']
  state['current_round_cost']['allocated_gpu_hours']=obs['derived']['allocated_formal_GPU_seconds']/3600
  state['formal_main_progress'].setdefault('parallel_execution',{})['registered_requested_active_GPU_jobs']=len(obs['derived']['occupied'])
  new=self.cas(state,expected);return new
def job_record(jid,bundle,argv):
 inv=bundle['invocation'];return dict(job_id=jid,name=NAME,job_name=NAME,experiment=EXPERIMENT,mode=MODE,stage_key=STAGE,suite='libero_object',
  pair_id=PAIR,logical_trial_id=CELL,method_ids=METHODS,gpus=1,status='PENDING',source_root=str(S),source_sha256=SOURCE,
  adapter_sha256='b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd',run_root=str(P/OUT),
  invocation=INV,invocation_sha256=sha(bundle['invocation_bytes']),submission_token=bundle['token'],slurm_comment=bundle['comment'],
  account=RESOURCES['account'],partition=RESOURCES['partition'],slurm_output=inv['slurm_output'],submitted_utc=inv['registered_utc'],
  linked_failure_sha256=FAILURE_SHA,original_sbatch_ACK=jid+'\n',ACK_reconciled_by_token_comment=True,
  ordinary_resume=False,maximum_attempts=1,automatic_retry=False,original_job_ids=OLD_IDS,original_GPU_seconds=6713,
  execution_manifest_sha256='34062573869c7b947fbd3c37b09da476bec673e8e16fc4ea49c6ce8c5932db5a',
  execution_version='object-single-error-linked-v1',wrapper=PROD+'/entry.py',wrapper_sha256=production_map()[PROD+'/entry.py'],
  plan_sha256=inv['plan_sha256'],runtime_readiness=inv['runtime_readiness'],final_states_opened=False,
  downstream_gateway=dict(version=VERSION,authorization=bundle['authorization_ref'],actual_sbatch_argv=argv,request_token=bundle['comment'],automatic_retry=False),
  object_single_error_gateway=dict(version=VERSION,authorization=bundle['authorization_ref'],actual_sbatch_argv=argv,
   request_token=bundle['token'],original_ACK_fact=X+'/gateway_attempt01/sbatch_result.json',automatic_retry=False))
class Transaction:
 def __init__(self,io,bundle):self.io=io;self.b=bundle;self.used=False
 def run(self,submit=False,reconcile=False):
  require(not self.used,'single-use transaction');self.used=True
  require(not (submit and reconcile),'cannot submit and reconcile together')
  io=self.io;b=self.b
  with io.lock():
   state,version=io.read_state();baseline=copy.deepcopy(state)
   try:
    require(state['autonomous_training_v1'].get('pending_submission') is None,'unresolved autonomous pending blocks transaction')
    if reconcile:return self.reconcile(state,version)
    require(state.get('pending_submission') is None,'unresolved pending; never clear/retry')
    require(state['autonomous_training_v1'].get('reserved_GPU_slots')==0,'other reserved work blocks this exact attempt')
    io.absent();observation=io.observe(state);io.revalidate()
    require(io.read_state()[1]==version,'CAS drift before intent')
    argv=sbatch_argv(b)
    if not submit:return dict(status='read_only_ready_not_submitted',observation=observation,state_sha256=version,actual_sbatch_argv=argv)
    io.fact('preflight.json',dict(state_sha256=version,observation=observation,authorization=b['authorization_ref'],
     sources=b['sources'],invocation_sha256=sha(b['invocation_bytes']),actual_sbatch_argv=argv))
    pending=dict(schema=EXPERIMENT,kind='Object_single_error_durable_pending',version=VERSION,status='before_sbatch',
     stage_key=STAGE,logical_trial_id=CELL,submission_token=b['token'],slurm_comment=b['comment'],
     invocation=INV,invocation_sha256=sha(b['invocation_bytes']),actual_sbatch_argv=argv,authorization=b['authorization_ref'],
     automatic_retry=False,requested_gpus=1,created_utc=utc(),audit_path=X+'/gateway_attempt01')
    io.fact('pending.json',pending);state['pending_submission']=copy.deepcopy(pending)
    state['autonomous_training_v1']['reserved_GPU_slots']=1
    version=io.cas(state,version);io.publish_invocation()
    require(io.read_state()[1]==version,'CAS drift before one sbatch')
    answer=io.submit(argv);io.fact('sbatch_result.json',answer)
    jid=parse_ack(answer,{str(j['job_id']) for j in state['registered_jobs']})
    state['pending_submission'].update(status='original_ACK_saved',known_job_id=jid)
    version=io.cas(state,version)
    actual=io.actual(jid,True);io.fact('held_identity.json',actual)
    return self.register_release(state,version,jid,argv,baseline)
   except BaseException as exc:
    if submit or reconcile:
     try:
      if not io.fact_exists('failed_transaction.json'):io.fact('failed_transaction.json',dict(status='HOLD_reconcile_original_ACK_only',error_type=type(exc).__name__,error=str(exc),automatic_retry=False,utc=utc()))
     except BaseException:pass
    raise
 def register_release(self,state,version,jid,argv,baseline):
  io=self.io;b=self.b
  require(not any(duplicate(j) for j in state['registered_jobs']),'duplicate linked record before registration')
  job=job_record(jid,b,argv);state['registered_jobs'].append(job)
  # The held allocation is now included in a fresh all-mode preview before
  # either registration or release; its reserved slot is not double-counted.
  preview=copy.deepcopy(state);preview['autonomous_training_v1']['reserved_GPU_slots']=0
  measured=io.observe(preview,allow_job=jid)
  if not io.fact_exists('held_capacity_before_registration.json'):io.fact('held_capacity_before_registration.json',measured)
  state['pending_submission'].update(status='registered_held_release_not_issued',known_job_id=jid)
  state['autonomous_training_v1']['reserved_GPU_slots']=0
  require(state['registered_jobs'][:-1]==baseline['registered_jobs'],'historical registration mutated')
  version=io.cas(state,version);io.fact('registered_held.json',dict(job=job,state_sha256=version))
  return self.release_once(state,version,jid)
 def release_once(self,state,version,jid):
  io=self.io
  require(not io.fact_exists('release_attempt.json'),'release already attempted; do not resend')
  io.actual(jid,True)
  attempt=dict(job_id=jid,argv=['scontrol','release',jid],state_sha256=version,submission_token=self.b['token'],utc=utc())
  io.fact('release_attempt.json',attempt)
  state['pending_submission']['status']='release_attempt_persisted';version=io.cas(state,version)
  answer=io.release(jid);io.fact('release_result.json',answer)
  require(answer['returncode']==0,'uncertain release result; never resend')
  actual=io.actual(jid,False);io.fact('released_identity.json',actual)
  observation=io.observe(state,allow_job=jid)
  io.fact('post_release_observation.json',observation)
  version=io.committed(jid,state,version,observation)
  io.fact('committed.json',dict(status='submitted_once_registered_then_released',job_id=jid,state_sha256=version,automatic_retry=False))
  return dict(status='submitted_once_registered_then_released',job_id=jid,state_sha256=version)
 def reconcile(self,state,version):
  io=self.io;b=self.b;p=state.get('pending_submission')
  require(type(p)is dict and p.get('kind')=='Object_single_error_durable_pending' and p.get('stage_key')==STAGE
   and p.get('submission_token')==b['token'] and p.get('invocation_sha256')==sha(b['invocation_bytes'])
   and p.get('authorization')==b['authorization_ref'] and p.get('actual_sbatch_argv')==sbatch_argv(b),'exact original pending required')
  require(io.fact_exists('sbatch_result.json'),'original ACK absent; unknown outcome remains HOLD, never resubmit')
  answer=io.fact_read('sbatch_result.json');require(answer.get('actual_sbatch_argv')==sbatch_argv(b),'original ACK argv differs')
  existing=[j for j in state['registered_jobs'] if duplicate(j)]
  known={str(j['job_id']) for j in state['registered_jobs'] if j not in existing}
  jid=parse_ack(answer,known);require(p.get('known_job_id') in (None,jid),'pending ACK ID differs')
  io.revalidate()
  if not existing:
   require(not io.fact_exists('release_attempt.json'),'unregistered release anomaly')
   actual=io.actual(jid,True)
   if not io.fact_exists('held_identity.json'):io.fact('held_identity.json',actual)
   baseline=copy.deepcopy(state);state['pending_submission'].update(status='original_ACK_saved',known_job_id=jid)
   version=io.cas(state,version)
   return self.register_release(state,version,jid,sbatch_argv(b),baseline)
  require(len(existing)==1 and str(existing[0]['job_id'])==jid and existing[0]['invocation_sha256']==sha(b['invocation_bytes'])
   and existing[0]['original_sbatch_ACK']==jid+'\n','unique previously registered original ACK required')
  expected=job_record(jid,b,sbatch_argv(b));expected.pop('status')
  require(all(existing[0].get(k)==v for k,v in expected.items()),'registered original identity/argv/source drift')
  io.observe(state,allow_job=jid)
  if not io.fact_exists('release_attempt.json'):return self.release_once(state,version,jid)
  # Once release might have happened, never call release again. Actual live or
  # terminal success plus complete accounting may reconcile the original job.
  actual=io.actual(jid,False);observation=io.observe(state,allow_job=jid)
  if not io.fact_exists('reconciled_release.json'):io.fact('reconciled_release.json',dict(actual=actual,observation=observation,original_release_attempt=io.fact_read('release_attempt.json')))
  version=io.committed(jid,state,version,observation)
  if not io.fact_exists('committed.json'):io.fact('committed.json',dict(status='original_ACK_reconciled_no_resubmission',job_id=jid,state_sha256=version,automatic_retry=False))
  return dict(status='original_ACK_reconciled_no_resubmission',job_id=jid,state_sha256=version)

def observe_only():
 c=controller()
 with shared_writer_lock():
  before=raw(R/STATE);s=json.loads(before);n=Native.__new__(Native);n.c=c;n.scheduler=c.Slurm(timeout=30)
  out=n.observe(s);require(raw(R/STATE)==before,'read-only state changed')
  return dict(schema=EXPERIMENT,kind='Object_single_error_actual_readonly_projection',state_sha256=sha(before),
   projection=out,production_authorized=False,Slurm_submitted=False,new_trials=0,new_GPU_seconds=0)
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--gateway-sha256',required=True)
 mode=p.add_mutually_exclusive_group();mode.add_argument('--submit',action='store_true');mode.add_argument('--reconcile',action='store_true');mode.add_argument('--observe-only',action='store_true')
 p.add_argument('--authorization-sha256');p.add_argument('--root-reviewed',action='store_true');a=p.parse_args(argv)
 require(sha(raw(Path(__file__)))==a.gateway_sha256,'gateway entry source changed')
 if a.observe_only:
  require(not a.root_reviewed and a.authorization_sha256 is None,'read-only projection takes no execution authority')
  print(json.dumps(observe_only(),sort_keys=True,ensure_ascii=False));return
 require(Path(__file__).resolve()==R/BASE/'gateway.py' and Path.cwd().resolve()==R,'canonical root gateway only')
 require(a.authorization_sha256 is not None and (not (a.submit or a.reconcile) or a.root_reviewed),'root exact authorization required')
 b=authorization(a.authorization_sha256)
 print(json.dumps(Transaction(Native(b),b).run(submit=a.submit,reconcile=a.reconcile),sort_keys=True,ensure_ascii=False))
if __name__=='__main__':main()

"""Root dispatcher for the five explicitly enumerated remaining Goal pairs.
Control transaction adapted from frozen full200 dispatcher; all pair bindings are
new immutable per-instance closures. The old exclusive module is never mutated.
"""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
from contextlib import contextmanager
from types import SimpleNamespace
import argparse,copy,fcntl,hashlib,importlib.util,json,os,re,stat,subprocess,sys
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
H=R.parent
S=P/'snapshots/formal_main_v2_run_564be0995e'
BASE='scripts/ops/formal_goal_remaining5_dispatch_v1'
PROD='scripts/ops/formal_goal_remaining5_gate_v1'
STATE='results/experiment_supervisor/state.json'
EXPERIMENT='formal_main_v2'
VERSION='goal-remaining5-held-atomic-dispatch-v1'
SOURCE='dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e'
OWNER='results/formal_main_v2/autonomous_training/run_v1/owner.json'
OWNER_SHA='2ba2100d6f20e8a00f7853e193d1546b3d7c4195f174c75d54605ec504e33bc2'
LEASE='results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock'
CONTROLLER='scripts/ops/formal_autonomous_training_v1/controller.py'
CONTROLLER_SHA='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
DESIGN='results/formal_main_v2/engineering/supervision_delivery_20261021T0334/Goal_remaining5_design/design.json'
DESIGN_SHA='5c813e3a6e9429cc46ed9ab52a5543d0cf6302c5e5c1819efd11a501a2fb4e8e'
OLD_IDS=['3053440','3054127'];OLD_SECONDS=[803,840]
PAIRS={
 'libero_goal_k256_seed23':('9ad90de70f1e3fa7581efde098ef8953427ccbfd034c6eaf686cd791f4689032',256,23),
 'libero_goal_k256_seed41':('bc06dd35931c05b180758f46e9f39cec50b632b20a33b4ebfc0d2f2cc7614954',256,41),
 'libero_goal_k64_seed17':('ad5f40d8b25cba3280e85d8c05712fd6aa749f26277e015b7eaec3b405e6b8bd',64,17),
 'libero_goal_k64_seed23':('7a6254a2e2de33e4f09a072654ea08121b51c3a4e84bfb837fee13ebb3586ce9',64,23),
 'libero_goal_k64_seed41':('8336a896242eeabff2afbd37462b83a0321f016974a27a70d83ac47949f0243d',64,41)}

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

def controller():return load(R/CONTROLLER,CONTROLLER_SHA,'_goal_remaining5_exact_controller')

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
 for obj in (job,job.get('downstream_gateway',{}),job.get('autonomous_control',{}),job.get('startup_recovery',{}),job.get('goal_full200_gateway',{})):
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

def source_map(root=R):
 return {BASE+'/'+n:sha(raw(root/BASE/n)) for n in ('gateway.py','scope.json')}
def make_dispatcher(pair_key,scope_sha256):
 require(pair_key in PAIRS,'only five exact remaining Goal pairs')
 scope=read(R/BASE/'scope.json',scope_sha256)
 require(raw(P/BASE/'scope.json',scope_sha256)==raw(R/BASE/'scope.json',scope_sha256),'scope R/P differs')
 require(set(scope)=={'schema','kind','version','design','pairs','runtime_manifest_sha256','runtime_files'},'unexpected dispatch scope fields')
 require(scope['schema']==EXPERIMENT and scope['kind']=='five_exact_Goal_pairs_dispatch_scope' and scope['version']==VERSION,'wrong scope kind')
 require(scope['design']=={'path':DESIGN,'sha256':DESIGN_SHA},'root frozen design binding differs')
 design=read(R/DESIGN,DESIGN_SHA)
 actual={r['pair_key']:(r['pair_id'],r['budget'],r['seed']) for r in design['remaining_pairs']}
 require(actual==PAIRS and scope['pairs']=={k:list(v) for k,v in PAIRS.items()},'five exact pair identity differs')
 PAIR,TOKENS,TRAIN_SEED=PAIRS[pair_key]
 KEY=pair_key;STAGE='goal_remaining5_v1/'+KEY
 X='results/formal_main_v2/execution/'+STAGE
 AUTH=X+'/root_authorization.json';INV=AUTH
 ADMISSION=X+'/dispatch_admission.json';OUT=X+'/attempt01'
 RAW='results/formal_main_v2/raw_runtime/'+STAGE+'/attempt01'
 RESERVATION=X+'/reservation.json';DISPATCH=X+'/held_dispatch_record.json'
 CELL='Goal_remaining5_'+KEY
 NAME='cti-goal-r5-k'+str(TOKENS)+'s'+str(TRAIN_SEED)
 MODE='goal_remaining5_prospective'
 METHODS=[f'{a}{TOKENS}_seed{TRAIN_SEED}' for a in ('A','B')]
 RUNTIME_MANIFEST_SHA=scope['runtime_manifest_sha256'];SCOPE_SHA=scope_sha256
 require(re.fullmatch('[0-9a-f]{64}',RUNTIME_MANIFEST_SHA) is not None,'runtime manifest must be frozen; HOLD')
 RESOURCES=dict(job_name=NAME,account='p_p15016',qos='cpu-500_core-l40-8_card-a800-8_card',partition='L40',nodes=1,ntasks=1,cpus_per_task=7,gres='gpu:l40:1',mem='64G',time='02:00:00')
 RUNTIME_RESOURCES=dict(partition='L40',gres='gpu:l40:1',cpus_per_task=7,mem='64G',wall_seconds=7200,no_requeue=True,excluded_nodes=['gpu4020'])
 CONFIG_REL=PROD+'/pairs/'+KEY+'/config.json'

 def runtime_package(root=P):
  p=read(root/PROD/'package_manifest.json',RUNTIME_MANIFEST_SHA)
  require(p.get('schema')==EXPERIMENT and p.get('version')=='goal-remaining5-prospective-single-attempt-v1'
   and p.get('files')==scope['runtime_files'] and PROD+'/entry.py' in p['files'] and CONFIG_REL in p['files'],'exact five-pair runtime closure required')
  for path,pin in p['files'].items():raw(root/relative(path),pin)
  return p

 def archive_ref(x):
  require(type(x)is dict and set(x)=={'path','bytes','sha256'} and x['path'].startswith('results/formal_main_v2/engineering/'),'archived source proof required')
  return read_ref(R,x)

 def runtime_output(value,package):
  require(value.get('status')=='passed_metadata_source_capacity_only' and value.get('stage_key')==STAGE
   and value.get('package_manifest_sha256')==RUNTIME_MANIFEST_SHA and value.get('config_sha256')==package['files'][CONFIG_REL]
   and value.get('new_GPU_submissions')==0 and value.get('actual_GPU_runtime_verified') is False
   and value.get('GPU_execution_authorized') is False and value.get('original200_HOLD') is True
   and value.get('final_release') is False,'actual P verification is source/identity/capacity only')
  require(value.get('identity',{}).get('original_fixed200_identity_order') is True
   and value.get('identity',{}).get('unique_development_states')==100,'complete original 200 identity missing')
  require(value.get('storage',{}).get('aggregate_pair_keys')==list(PAIRS)
   and value['storage'].get('no_dedup_credit') is True,'all-five conservative storage proof required')
  return value

 def admission_fixed():
  return dict(schema=EXPERIMENT,kind='root_goal_remaining5_exact_dispatch_admission',status='approved_exactly_once',
   reviewed_by='root',version=VERSION,stage_key=STAGE,pair_key=KEY,pair_id=PAIR,method_ids=METHODS,
   training_seed=TRAIN_SEED,runtime_seed=17,environment_seed=0,
   maximum_trials=200,unique_development_states=100,maximum_control_steps=60000,maximum_policy_queries=7600,
   maximum_attempts=1,automatic_retry=False,original200_HOLD=True,final_allowed=False,
   package_manifest_sha256=RUNTIME_MANIFEST_SHA,scope_sha256=SCOPE_SHA,resources=RESOURCES)

 def check_admission_fields(a):
  fixed=admission_fixed()
  require(all(a.get(k)==v for k,v in fixed.items()),'exact root dispatch scope absent')
  require(type(a.get('prepared_utc')) is str and datetime.fromisoformat(a['prepared_utc']).tzinfo is not None,'explicit UTC root preparation timestamp required')
  return a

 def reconcile_runtime_metadata(e,package):
  require(Path(e.__file__).resolve()==P/PROD/'entry.py','exact published P entry required')
  value=e.verify_existing_metadata(KEY,RUNTIME_MANIFEST_SHA)
  require(value.get('status')=='passed_existing_ACK_metadata_source_only' and value.get('new_GPU_submission_allowed') is False,'reconcile metadata may not submit/claim')
  require(value.get('identity',{}).get('original_fixed200_identity_order') is True and value['identity'].get('unique_development_states')==100,'ACK scientific identity missing')
  return value

 def admission(pin,*,reconcile_existing=False):
  require(type(reconcile_existing)is bool,'explicit original-ACK mode')
  a=read(R/ADMISSION,pin);require(raw(P/ADMISSION,pin)==raw(R/ADMISSION,pin),'admission R/P differs')
  check_admission_fields(a)
  package=runtime_package(P);require(runtime_package(R)==package,'runtime R/P differs')
  require(a.get('dispatch_files')==source_map() and a.get('runtime_files')==package['files'],'root source closures differ')
  for rel,pin in source_map().items():raw(P/rel,pin)
  auth=read_ref(R,a['authorization'],AUTH);require(raw(P/AUTH)==raw(R/AUTH),'authorization R/P differs')
  ah=sha(raw(R/AUTH));e=load(P/PROD/'entry.py',package['files'][PROD+'/entry.py'],'_goal_remaining5_'+KEY)
  ctx=e.context(KEY)
  e.validate_authorization(ctx,auth,package['files'][CONFIG_REL],RUNTIME_MANIFEST_SHA,package['files'][PROD+'/entry.py'])
  for role in ('root','independent'):
   rr=auth[role+'_review'];rel=relative(str(Path(rr['path']).relative_to(P)))
   require(raw(P/rel,rr['sha256'])==raw(R/rel,rr['sha256']),'root/runtime readiness differs')
   e.check_review(ctx,read(P/rel),role,RUNTIME_MANIFEST_SHA,package['files'][CONFIG_REL])
  ri=archive_ref(a['runtime_independent_review'])
  require(str(ri.get('status','')).startswith('passed') and ri.get('package_manifest_sha256')==RUNTIME_MANIFEST_SHA
   and ri.get('package_files')==package['files'] and ri.get('blockers')==[]
   and ri.get('reviewed_by') not in (None,'root'),'independent runtime source review missing')
  di=archive_ref(a['dispatch_independent_review'])
  require(di.get('kind')=='Goal_remaining5_atomic_dispatch_independent_review' and di.get('status')=='passed'
   and di.get('dispatch_files')==source_map() and di.get('package_manifest_sha256')==RUNTIME_MANIFEST_SHA
   and di.get('runtime_files')==package['files'] and di.get('blockers')==[]
   and di.get('review_scope')=='source_and_CPU_only' and di.get('GPU_execution_authorized') is False,'new dispatcher independent proof missing')
  capture=read_ref(R,a['actual_P_verification'])
  argv=[str(H/'venv/bin/python'),'-B',str(P/PROD/'entry.py'),'--pair-key',KEY,'--verify','--package-manifest-sha256',RUNTIME_MANIFEST_SHA]
  require(capture.get('kind')=='Goal_remaining5_actual_P_verification_capture' and capture.get('argv')==argv
   and capture.get('returncode')==0 and capture.get('runtime_files')==package['files'],'exact actual P process absent')
  prior=runtime_output(json.loads(capture['stdout']),package)
  current=reconcile_runtime_metadata(e,package) if reconcile_existing else runtime_output(e.verify_published(KEY,RUNTIME_MANIFEST_SHA,must_be_fresh=True),package)
  require(current['identity']==prior['identity'],'actual P original scientific identity differs')
  return dict(admission=a,authorization=auth,authorization_ref=ref(R,AUTH),authorization_sha256=ah,
   admission_ref=ref(R,ADMISSION),token='cti-goal-remaining5-v1:'+KEY+':'+ah,comment='cti-goal-remaining5-v1:'+KEY+':'+ah,
   invocation_bytes=raw(R/AUTH),runtime_package=package,scope=scope,sources={**source_map(),**package['files']},actual_P_current=current,reconcile_existing=reconcile_existing)

 def sbatch_argv(bundle):
  return ['sbatch','--hold','--parsable','--no-requeue','--exclude=gpu4020','--comment='+bundle['comment'],
   *['--'+k.replace('_','-')+'='+str(v) for k,v in RESOURCES.items()],
   '--chdir='+str(S),'--output='+str(P/'results/slurm'/(NAME+'_%j.out')),
   '--error='+str(P/'results/slurm'/(NAME+'_%j.err')),
   '--export=ALL,CTI_GOAL_REMAINING5_PAIR_KEY='+KEY+',CTI_GOAL_REMAINING5_AUTH_SHA256='+bundle['authorization_sha256'],str(P/PROD/'run.slurm')]

 def duplicate(j):
  return (j.get('stage_key')==STAGE or j.get('logical_trial_id')==CELL or j.get('invocation')==AUTH
   or j.get('run_root') in (str(P/OUT),str(P/OUT/'original_run'),OUT)
   or j.get('name',j.get('job_name'))==NAME
   or str(j.get('slurm_comment','')).startswith('cti-goal-remaining5-v1:'+KEY+':')
   or (j.get('pair_id')==PAIR and j.get('mode')=='development'))

 def goal_overlap(j):
  if j.get('pair_id')==PAIR:return True
  text=' '.join(str(j.get(k,'')) for k in ('suite','stage_key','run_root','name','job_name')).lower()
  # Unknown pair identity on another Goal job is not safe to infer.
  return 'goal' in text and not re.fullmatch('[0-9a-f]{64}',str(j.get('pair_id','')))

 def validate_new_identity(job,bundle,f,held):
  validate_live_identity(job,f)
  expected=dict(Requeue='0',TimeLimit='02:00:00',Partition='L40',Account='p_p15016',ExcNodeList='gpu4020',
   NumCPUs='7',MinMemoryNode='64G',Command=str(P/PROD/'run.slurm'),WorkDir=str(S),Restarts='0',
   QOS=RESOURCES['qos'],TresPerNode='gres:gpu:l40:1')
  for k,v in expected.items():require(f.get(k)==v,'actual new Goal held identity differs '+k)
  require(f.get('Comment')==bundle['comment'],'new Goal exact token/comment differs')
  if held:require(f.get('JobState')=='PENDING' and f.get('Reason')=='JobHeldUser','must remain held before root registration')
  else:require(f.get('JobState') in {'RUNNING','PENDING','CONFIGURING','COMPLETING','COMPLETED'} and f.get('Reason')!='JobHeldUser','uncertain release; never repeat')
  return f

 def job_record(jid,bundle,argv):
  p=bundle['runtime_package'];return dict(job_id=jid,name=NAME,job_name=NAME,experiment=EXPERIMENT,mode='development',goal_dispatch_mode=MODE,
   stage_key=STAGE,logical_trial_id=CELL,suite='libero_goal',pair_id=PAIR,status='PENDING',gpus=1,
   run_root=str(P/OUT/'original_run'),attempt_root=str(P/OUT),invocation=AUTH,invocation_sha256=bundle['authorization_sha256'],source_root=str(S),source_sha256=SOURCE,
   config_sha256=p['files'][CONFIG_REL],package_manifest_sha256=RUNTIME_MANIFEST_SHA,
   wrapper=str(P/PROD/'entry.py'),wrapper_sha256=p['files'][PROD+'/entry.py'],submission_token=bundle['token'],slurm_comment=bundle['comment'],
   account=RESOURCES['account'],partition=RESOURCES['partition'],slurm_output=str(P/'results/slurm'/(NAME+'_%j.out')),
   root_dispatch_prepared_utc=bundle['admission']['prepared_utc'],original_sbatch_ACK=jid+'\n',ACK_reconciled_by_token_comment=True,
   maximum_attempts=1,automatic_retry=False,visual_tokens=TOKENS,training_seed=TRAIN_SEED,runtime_seed=17,environment_seed=0,maximum_trials=200,
   maximum_control_steps=60000,maximum_policy_queries=7600,scientific_trials=0,final_states_opened=False,
   purpose='One original fixed Goal pair from exact remaining-five scope; all results pending original raw consumer and independent terminal acceptance',
   root_reservation=dict(path=RESERVATION,sha256=sha(canonical(reservation(bundle))+b'\n')),
   downstream_gateway=dict(version=VERSION,actual_sbatch_argv=argv,request_token=bundle['token'],automatic_retry=False),
   goal_remaining5_gateway=dict(admission=bundle['admission_ref'],actual_sbatch_argv=argv,request_token=bundle['token'],automatic_retry=False))

 def reservation(b):
  return dict(schema=EXPERIMENT,kind='root_goal_remaining5_GPU_slot_reservation',status='approved_for_exact_remaining5_pair',
   stage_key=STAGE,authorization=dict(path=str(P/AUTH),sha256=b['authorization_sha256']),reserved_slots=1,
   capacity_limit_all_GPU_modes=8,maximum_wall_seconds=7200,automatic_retry=False,scientific_release=False)

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
    require(not goal_overlap(j) or jid==allow_job,'same pair or unknown Goal identity occupied')
   require(not duplicate(j) or jid==allow_job,'any previous/incomplete/terminal correction forbids repeat')
  for jid,seconds in zip(OLD_IDS,OLD_SECONDS):
   row=observation['rows'][jid]
   require(row['status']=='COMPLETED' and row['exit_code']=='0:0' and row['elapsed_seconds']==seconds and row['gpus']==1,'original allocation/cost changed')
  ctl=state['autonomous_training_v1'];progress=state['formal_main_progress'];r=observation['rows']['3034538']
  require(ctl.get('pending_submission') is None,'unresolved autonomous pending blocks exact correction')
  pending=state.get('pending_submission')
  require(pending is None or (allow_job is not None and type(pending)is dict and pending.get('kind')=='Goal_remaining5_durable_pending' and pending.get('stage_key')==STAGE and pending.get('logical_trial_id')==CELL and pending.get('known_job_id')==allow_job),'unresolved/foreign root pending blocks projection')
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
   original_GPU_seconds=1643,allocated_formal_GPU_seconds=sum(observation['rows'][str(j['job_id'])]['elapsed_seconds']*
     observation['rows'][str(j['job_id'])]['gpus'] for j in jobs if j.get('experiment')==EXPERIMENT))

 class Native:
  def __init__(self,bundle):
   self.bundle=bundle;self.c=controller();self.scheduler=self.c.Slurm(timeout=30)
   self.audit=R/X/'dispatch_attempt01';self.path=R/STATE
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
   require(not self.audit.exists(),'prior dispatch audit or failed intent forbids retry')
   require(not (P/OUT).exists() and not (R/RAW).exists(),'prior attempt/raw claim forbids repeat')
   for root in (R,P):
    require(not (root/DISPATCH).exists() and not (root/RESERVATION).exists(),'old dispatch/reservation forbids repeat')
  def revalidate(self):
   checked=admission(self.bundle['admission_ref']['sha256'],reconcile_existing=self.bundle.get('reconcile_existing',False))
   require(checked['invocation_bytes']==self.bundle['invocation_bytes'] and checked['sources']==self.bundle['sources'],'source/readiness changed')
  def publish_reservation(self):
   value=reservation(self.bundle)
   for root in (R,P):record(root/RESERVATION,value)
  def dispatch_proof(self,jid,state,version):
   require(self.read_state()[1]==version,'CAS drift before held dispatch proof')
   measured=self.observe(state,allow_job=jid)
   reserved=reservation(self.bundle);rb=canonical(reserved)+b'\n'
   for root in (R,P):require(raw(root/RESERVATION)==rb,'root slot reservation changed')
   d=dict(schema=EXPERIMENT,kind='root_goal_remaining5_held_dispatch',status='held_registered_before_release',
    stage_key=STAGE,job_id=jid,authorization=dict(path=str(P/AUTH),sha256=self.bundle['authorization_sha256']),
    request_token=self.bundle['token'],capacity_limit_all_GPU_modes=8,reserved_slots=1,maximum_attempts=1,
    new_submissions=1,no_requeue=True,scientific_release=False,resources=RUNTIME_RESOURCES,
    occupied_job_ids=measured['derived']['occupied'],state_after_sha256=version,
    reservation=dict(path=str(P/RESERVATION),sha256=sha(rb)),actual_sbatch_argv=sbatch_argv(self.bundle),
    original_sbatch_ACK_fact=X+'/dispatch_attempt01/sbatch_result.json',source_files=self.bundle['sources'])
   if (R/DISPATCH).exists():
    old=read(R/DISPATCH)
    for k in d:
     if k not in ('state_after_sha256','occupied_job_ids'):require(old.get(k)==d[k],'existing dispatch identity differs')
    require(jid in old['occupied_job_ids'] and len(old['occupied_job_ids'])<=8,'original dispatch capacity invalid')
    d=old
   e=load(P/PROD/'entry.py',self.bundle['runtime_package']['files'][PROD+'/entry.py'],'_goal_dispatch_held_validate')
   e.validate_dispatch(e.context(KEY),d,reserved,self.bundle['authorization'],self.bundle['authorization_sha256'],jid,sha(rb))
   for root in (R,P):record(root/DISPATCH,d,allow_identical=True)
   return measured
  def submit(self,argv):
   require(argv==sbatch_argv(self.bundle),'only exact held argv')
   began=utc();answer=self.scheduler.submit(argv)
   return dict(returncode=answer.returncode,stdout=answer.stdout,stderr=answer.stderr,actual_sbatch_argv=argv,started_utc=began,returned_utc=utc())
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
   state['autonomous_training_v1']['occupied_job_ids']=list(obs['derived']['occupied'])
   new=self.cas(state,expected);return new

 class Transaction:
  def __init__(self,io,bundle):self.io=io;self.b=bundle;self.used=False
  def run(self,submit=False,reconcile=False):
   require(not self.used,'single-use transaction');self.used=True
   require(not (submit and reconcile),'cannot submit and reconcile together')
   io=self.io;b=self.b
   require(not b.get('reconcile_existing',False) or reconcile,'existing ACK metadata may only reconcile, never submit or prepare new work')
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
     pending=dict(schema=EXPERIMENT,kind='Goal_remaining5_durable_pending',version=VERSION,status='before_sbatch',
      stage_key=STAGE,logical_trial_id=CELL,submission_token=b['token'],slurm_comment=b['comment'],
      invocation=INV,invocation_sha256=sha(b['invocation_bytes']),actual_sbatch_argv=argv,authorization=b['authorization_ref'],
      automatic_retry=False,requested_gpus=1,created_utc=utc(),audit_path=X+'/dispatch_attempt01')
     io.fact('pending.json',pending);state['pending_submission']=copy.deepcopy(pending)
     state['autonomous_training_v1']['reserved_GPU_slots']=1
     version=io.cas(state,version);io.publish_reservation()
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
   io.dispatch_proof(jid,state,version)
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
   require(type(p)is dict and p.get('kind')=='Goal_remaining5_durable_pending' and p.get('stage_key')==STAGE
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

 return SimpleNamespace(pair_key=KEY,pair_id=PAIR,stage=STAGE,authorization=AUTH,output=OUT,raw=RAW,
  admission=admission,admission_fixed=admission_fixed,normalized_projection=normalized_projection,
  duplicate=duplicate,goal_overlap=goal_overlap,job_record=job_record,sbatch_argv=sbatch_argv,
  parse_ack=parse_ack,Transaction=Transaction,Native=Native,runtime_output=runtime_output,
  scope=scope,source_map=source_map,resources=RESOURCES,runtime_package=runtime_package,
  reservation=reservation,validate_new_identity=validate_new_identity)

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--pair-key',choices=tuple(PAIRS),required=True)
 p.add_argument('--dispatch-sha256',required=True);p.add_argument('--scope-sha256',required=True);p.add_argument('--admission-sha256',required=True)
 m=p.add_mutually_exclusive_group();m.add_argument('--submit',action='store_true');m.add_argument('--reconcile',action='store_true')
 p.add_argument('--root-reviewed',action='store_true');a=p.parse_args(argv)
 require(Path(__file__).resolve()==R/BASE/'gateway.py' and Path.cwd().resolve()==R,'canonical root dispatcher only')
 require(sha(raw(Path(__file__)))==a.dispatch_sha256,'exact new source pin')
 require(not(a.submit or a.reconcile) or a.root_reviewed,'root reviewed exact action required')
 d=make_dispatcher(a.pair_key,a.scope_sha256)
 b=d.admission(a.admission_sha256,reconcile_existing=a.reconcile)
 print(json.dumps(d.Transaction(d.Native(b),b).run(submit=a.submit,reconcile=a.reconcile),sort_keys=True,ensure_ascii=False))
if __name__=='__main__':main()

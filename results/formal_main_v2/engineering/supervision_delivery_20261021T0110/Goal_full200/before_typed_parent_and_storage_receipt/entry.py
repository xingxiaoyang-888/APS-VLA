"""One explicitly authorized Goal paired-input58 engineering attempt; no submission API.

Root must first publish/review this package, reserve one of eight slots under the
shared writer lock/CAS, submit held, reconcile the exact ACK/token and record the
job before release. This entry consumes only that NEW authorization/dispatch.
It never claims scientific completion or retries. The unchanged inherited reset
may swallow exceptions; the required Slurm7200-second bound is authoritative.
"""
from __future__ import annotations
import argparse,copy,fcntl,hashlib,importlib.util,json,os,re,sys,time,traceback
from contextlib import ExitStack
from datetime import datetime,timezone
from pathlib import Path
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');S=P/'snapshots/formal_main_v2_run_564be0995e'
PKG='scripts/ops/formal_goal_full200_gate_v1';STAGE='goal_full200_20261021T0110';BASE=P/'results/formal_main_v2/engineering'/STAGE;OUTPUT=BASE/'attempt01';ENTRY=P/PKG/'entry.py';CONFIG=P/PKG/'config.json';MANIFEST=P/PKG/'package_manifest.json';AUTH=BASE/'root_authorization.json';DISPATCH=BASE/'held_dispatch_record.json';RESERVATION=BASE/'reservation.json'
ROOT_DECISION_REL='results/formal_main_v2/preflight/heartbeat_20261021T0758/Goal_prospective_root_decision.json';ROOT_DECISION_SHA='06911f2ba90ffa9e7df233e0793c0989e0d15edf260b18a2fa2fb963ef0912d7'
RAW=R/'results/formal_main_v2/raw_runtime'/STAGE/'attempt01';STORAGE_SHA='61ffc7702ca9ce2c9f12419017416b3bf8fea852049844310d5b10f4a9c7ea37'
VERSION='goal-full200-prospective-single-attempt-v1';WRAPPER=P/'scripts/ops/formal_action_deployment_v1/wrapper.py';WSHA='d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33';LEGACY=P/'scripts/ops/formal_evaluation_adapter.py';LSHA='b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd'
ORIGINAL=P/'results/formal_main_v2/invocations/libero_goal_development_5185766bb353c8e6_attempt01.json';ISHA='c07489c5e56cc3255b60f5eb6df34146e37e4b60fa7151cc97f8008f402b8803';PREFIX_SHA='ed0b59bd1acbdab34658f5599f4969aa745e596348bf25d230a38c978aa652ad'
THREADS={'OMP_NUM_THREADS':'7','OPENBLAS_NUM_THREADS':'7','MKL_NUM_THREADS':'7','TF_NUM_INTRAOP_THREADS':'7','TF_NUM_INTEROP_THREADS':'1','TOKENIZERS_PARALLELISM':'false','MUJOCO_GL':'egl','LIBERO_CONFIG_PATH':str(P/'configs/libero_runtime'),'PYTHONPATH':str(S/'src'),'PYTHONDONTWRITEBYTECODE':'1'}
RESOURCES={'partition':'L40','gres':'gpu:l40:1','cpus_per_task':7,'mem':'64G','wall_seconds':7200,'no_requeue':True,'excluded_nodes':['gpu4020']}
PACKAGE_FILES={PKG+'/'+x for x in ('entry.py','observer_v3.py','ast_observer_v2.py','paired_input_gate_v1.py','ast_gate_v2.py','config.json','specification.json','run.slurm','storage.py','consumer.py')}
def require(ok,msg):
 if not ok:raise ValueError(msg)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for raw in iter(lambda:f.read(8<<20),b''):h.update(raw)
 return h.hexdigest()
def require_path(p,expected):
 p=Path(p);require(p==expected and p.is_absolute() and p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]),'exact non-link registered path required');return p
def read(p,pin=None):
 if pin is not None:require(re.fullmatch('[0-9a-f]{64}',str(pin)) and sha(p)==pin,'file SHA differs: '+str(p))
 return json.loads(Path(p).read_bytes())
def load(p,name,pin):
 require(sha(p)==pin,'module SHA differs before import');spec=importlib.util.spec_from_file_location(name,p);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
def ref(p):return dict(path=str(p),sha256=sha(p))
def validate_config(c):
 expected={'schema':'formal_main_v2','kind':'goal_full200_single_attempt_configuration','version':VERSION,'stage_key':STAGE,'suite':'libero_goal','seed':17,'tokens':256,'method_ids':['A256_seed17','B256_seed17'],'maximum_trials':200,'unique_development_states':100,'wait_steps':10,'action_chunk':8,'max_control_steps':300,'maximum_attempts':1,'automatic_retry':False,'scientific_trials_added':0,'original200_HOLD':True,'new_Goal_science_HOLD':True,'historical_actions_forced':False,'resources':RESOURCES,'original_invocation':{'path':str(ORIGINAL),'sha256':ISHA},'prefix':{'path':str(P/PKG/'specification.json'),'sha256':PREFIX_SHA},'output':str(OUTPUT),'final_evaluation_enabled':False,'maximum_total_control_steps':60000,'maximum_total_policy_queries':7600,'policy_watchdog_seconds':60.0,'raw_observation_root':str(RAW),'root_fixed_design':{'path':ROOT_DECISION_REL,'sha256':ROOT_DECISION_SHA}}
 require(all(c.get(k)==v for k,v in expected.items()),'exact original58 diagnostic scope/resource configuration required')
 require(set(c)==set(expected)|{'schema_note'},'unexpected configuration fields')
def validate_authorization(a,config_sha,manifest_sha,entry_sha):
 fixed={'schema':'formal_main_v2','kind':'root_goal_full200_single_attempt_authorization','version':VERSION,'status':'approved','reviewed_by':'root','stage_key':STAGE,'config_sha256':config_sha,'package_manifest_sha256':manifest_sha,'entrypoint_sha256':entry_sha,'maximum_gpu_jobs':1,'maximum_attempts':1,'maximum_wall_seconds':7200,'counts_against_8_GPU_slots':True,'automatic_retry':False,'scientific_release':False,'original_goal200_HOLD':True,'new_Goal_science_HOLD':True,'maximum_trials':200,'maximum_total_control_steps':60000,'maximum_total_policy_queries':7600,'policy_watchdog_seconds':60.0,'raw_observation_root':str(RAW),'root_fixed_design':{'path':ROOT_DECISION_REL,'sha256':ROOT_DECISION_SHA},'resources':RESOURCES,'dispatch_record_path':str(DISPATCH),'reservation_path':str(RESERVATION)}
 require(all(a.get(k)==v for k,v in fixed.items()),'new exact Goal full200 root authorization required')
 require(set(a)==set(fixed)|{'root_review','independent_review'},'unexpected authorization fields')
 require(a['root_review']!=a['independent_review'],'root and independent review must differ')
 for role in ('root','independent'):validate_review_ref(a[role+'_review'],role)
def validate_review_ref(value,role):
 require(role in ('root','independent') and isinstance(value,dict) and set(value)=={'path','sha256'},'readiness reference must contain exactly path and SHA')
 require(value['path']==str(BASE/(role+'_readiness.json')) and isinstance(value['sha256'],str) and re.fullmatch('[0-9a-f]{64}',value['sha256']),'exact new readiness path and 64-hex SHA required before target I/O')
 return value
def check_review(value,role,manifest_sha,config_sha):
 fixed={'schema':'formal_main_v2','kind':'goal_full200_single_attempt_CPU_readiness','status':'passed','reviewed_by':role,'version':VERSION,'package_manifest_sha256':manifest_sha,'config_sha256':config_sha,'original_chain_preserved':True,'observer_gaps_fixed':True,'paired_input_gate_CPU_passed':True,'pre_policy_pair_equality_gate':True,'all_query_input_integrity_gate':True,'original_policy_error_retained_then_halt':True,'full200_bound_tests_passed':True,'original_typed_raw_consumer_ready':True,'two_root_storage_contract_verified':True,'real_GPU_acceptance':False,'scientific_release':False}
 require(all(value.get(k)==v for k,v in fixed.items()),'complete matching CPU-only readiness required')
def validate_dispatch(d,res,a,auth_sha,job,reservation_sha):
 fixed={'schema':'formal_main_v2','kind':'root_goal_full200_held_dispatch','status':'held_registered_before_release','stage_key':STAGE,'job_id':job,'authorization':{'path':str(AUTH),'sha256':auth_sha},'request_token':'cti-goal-full200-v1:'+auth_sha,'capacity_limit_all_GPU_modes':8,'reserved_slots':1,'maximum_attempts':1,'new_submissions':1,'no_requeue':True,'scientific_release':False,'resources':RESOURCES}
 require(all(d.get(k)==v for k,v in fixed.items()),'exact held ACK registration must precede release')
 require(isinstance(d.get('occupied_job_ids'),list) and len(set(d['occupied_job_ids']))==len(d['occupied_job_ids'])<=8 and job in d['occupied_job_ids'],'one registered slot within all-GPU eight limit required')
 require(re.fullmatch('[0-9a-f]{64}',str(d.get('state_after_sha256'))),'root writer-lock/CAS snapshot identity missing')
 require(d.get('reservation')=={'path':str(RESERVATION),'sha256':reservation_sha},'exact root reservation pin missing')
 rf={'schema':'formal_main_v2','kind':'root_goal_full200_GPU_slot_reservation','status':'approved_for_exact_full200','stage_key':STAGE,'authorization':fixed['authorization'],'reserved_slots':1,'capacity_limit_all_GPU_modes':8,'maximum_wall_seconds':7200,'automatic_retry':False,'scientific_release':False}
 require(all(res.get(k)==v for k,v in rf.items()),'new full200 reservation required; old probe reservation forbidden')
def prepare_original():
 inv=read(ORIGINAL,ISHA);wrapper=load(WRAPPER,'g200_original_wrapper',WSHA);ctx=wrapper.verify(inv,project=P);legacy=load(LEGACY,'g200_original_legacy_adapter',LSHA)
 a=ctx['args'];require(a.policy_watchdog_seconds==60.0,'original watchdog60 required');require(a.mode=='evaluate' and not a.resume and not a.prepare_only and Path(a.output)==Path(inv['run_root']),'original args/mode changed')
 require(inv['suite']=='libero_goal' and inv['stage']=='development' and inv['method_ids']==['A256_seed17','B256_seed17'],'original development A/B pair only')
 require(not any(getattr(a,k,None) is not None for k in ('final_registry','sealed_final','release','release_sha256')),'sealed/final arguments forbidden')
 manifest=read(Path(inv['execution_manifest']),inv['execution_manifest_sha256']);expected={'A256_seed17':'756e7033ed467d50c748ff2a6290a3c9f84928c4a5a30c3304669c9e5f28d928','B256_seed17':'48cadc7b53914b87f4a7e8ef232bdcfe87bf94a1e28d8758e2db44d31e4ab2c3'}
 require([x['identity']['method_id'] for x in manifest['methods']]==list(expected),'original model loading order changed')
 for m in manifest['methods']:
  name=m['identity']['method_id'];path=Path(m['checkpoint']);require(path==Path('/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_goal/k256/seed17')/name[0]/'best.pt','exact original checkpoint path required');st=path.stat();require(sha(path)==m['identity']['checkpoint_sha256']==expected[name] and st==path.stat(),'original selected checkpoint bytes changed')
 return inv,wrapper,ctx,legacy

def validate_prefix(inv,legacy,prefix):
 panelpath=Path(inv['run_root'])/'panel.json';panel=read(panelpath,'ce8e3d31ab8f7616c87dd4d4031af41825713907ac184c6ea5b01d9040985aa9')
 require(panel['suite']=='libero_goal' and panel['split']=='development','original development panel only')
 keys=('trial_id','state_trial_id','task_id','task_name','source_state_index','initial_state_sha256','method')
 with legacy.source_imports(S):
  from cti_vla.evaluation import formal_trials
  actual=[{k:v for k,v in formal_trials._identity(panel,state,mid).items() if k in keys} for state in panel['states'] for mid in ['A256_seed17','B256_seed17']]
 require(len(prefix)==200 and actual==[{k:row[k] for k in keys} for row in prefix],'exact original full200 identity/order required before observer creation')
 require(len({x['state_trial_id'] for x in actual})==100 and all(x['task_id']==9 and x['source_state_index']==43 for x in actual[-2:]),'fixed full200 endpoint differs')
 return dict(original_panel=ref(panelpath),original_fixed58_identity_order=True,unique_development_states=29)

def execute(config,auth,job,package,gate):
 # Everything this entry owns is a fresh engineering subtree. The unchanged
 # legacy adapter separately retains its ordinary adapter provenance journal.
 require(not OUTPUT.exists(),'one attempt already exists; retry forbidden')
 storage=load(P/PKG/'storage.py','goal200_storage',STORAGE_SHA);storage.verify_storage();raw_claim=storage.claim_raw()
 OUTPUT.mkdir(parents=True,exist_ok=False);outer=OUTPUT/'outer';outer.mkdir();eventpath=outer/'events.jsonl';events=[];observer=None;result=None;errors=[];restored=False;started=time.perf_counter();code=1
 def emit(event,**fields):
  fixed=dict(seq=len(events),event=event,utc=datetime.now(timezone.utc).isoformat(),job_id=job,scientific_trials_added=0)
  require(all(k not in fixed or fixed[k]==v for k,v in fields.items()),'event field collides with outer identity')
  row=dict(fields);row.update(fixed)
  with eventpath.open('a',encoding='utf-8') as f:json.dump(row,f,sort_keys=True,ensure_ascii=False,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
  events.append(row)
 inv=wrapper=ctx=legacy=None;original_run=original_code=None
 try:
  inv,wrapper,ctx,legacy=prepare_original();require(not list((P/'results/formal_main_v2/adapter_invocations').glob(job+'_*')),'prior adapter invocation for this job forbids retry')
  original_run=legacy.run;original_code=original_run.__code__;runtime=ctx['runtime'];contract=ctx['execution_contract'];original=ctx['original_plan'];prefix=read(P/PKG/'specification.json',PREFIX_SHA)['rows'];prefix_proof=validate_prefix(inv,legacy,prefix);ob=load(P/PKG/'paired_input_gate_v1.py','g200_paired_input_gate',package['files'][PKG+'/paired_input_gate_v1.py']);ad=load(P/PKG/'ast_gate_v2.py','g200_paired_input_ast',package['files'][PKG+'/ast_gate_v2.py']);observer=ob.PairedInputGate(OUTPUT/'observer',allow_cpu_fixture=False,raw_observation_root=RAW);require(observer.allow_cpu_fixture is False and observer.sink is None,'production observer cannot use CPU fixtures or injected sinks')
  a=copy.deepcopy(ctx['args']);before_args=copy.deepcopy(vars(a));a.output=OUTPUT/'original_run';a.stop_after=200;require({k for k in vars(a) if vars(a)[k]!=before_args[k]}=={'output','stop_after'},'only prospective output and explicit full200 stop may change')
  emit('engineering_start',raw_observation_claim=raw_claim,version=VERSION,authorization_sha256=gate['auth_sha'],package_manifest_sha256=gate['manifest_sha'],original_invocation=ref(ORIGINAL),environment={k:os.environ.get(k) for k in list(THREADS)+['CUDA_VISIBLE_DEVICES','SLURM_JOB_ID','SLURMD_NODENAME']},original_argument_changes={'output':str(a.output),'stop_after':200},prefix_identity_proof=prefix_proof,original_adapter_run_code_sha256=legacy.code_sha(original_run),original_actions_forced=False)
  def runtime_emit(event,**fields):
   emit(event,**fields)
   if event in ('asset_metadata_compat_load_start','asset_metadata_compat_load_complete','deployment_base_load_start','deployment_base_load_complete','goal_component_load_start','goal_component_load_complete'):
    observer.capture('existing_loader_event:'+event)
  def scientific_runner():
   from cti_vla.evaluation import libero_runtime,formal_trials
   with ad.observer_scope(libero_runtime,formal_trials,observer,emit=emit):
    return legacy.run(a,mode='evaluate',source_root=S,source_inventory=Path(inv['source_inventory']),adapter_sha256=LSHA,resume=False)
  with legacy.source_imports(S):
   expected_assets=runtime.expected_asset_identities(project_root=P,source_root=S,contract=contract['runtime_contract'],asset_contract=original['invocation'].get('downstream_asset_compatibility'))
   result=runtime.run_with_asset_contexts(scientific_runner,project_root=P,source_root=S,contract=contract['runtime_contract'],asset_contract=original['invocation'].get('downstream_asset_compatibility'),emit=runtime_emit)
  proof=runtime.verify_runtime_events(events,contract['runtime_contract'],expected_asset_identities=expected_assets);require(proof['all_source_and_binding_contexts_restored'],'original action/component/loading context not restored');restored=True
  finish=observer.finish();require(finish['original_prefix_trials']==200 and finish['scientific_trials_added']==0 and finish['exact_paired_t0_checks']==100 and finish['runtime_context']=='real_environment_engineering','incomplete engineering prefix')
  emit('engineering_prefix_returned',runtime_proof=proof,observer_finish=finish);code=0
 except BaseException as error:
  errors.append(dict(error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc()));traceback.print_exception(type(error),error,error.__traceback__)
 finally:
  if legacy is not None and (legacy.run is not original_run or original_run.__code__ is not original_code):code=1;errors.append(dict(error_type='BindingIntegrity',error='original legacy run changed'))
  if inv is not None:
   try:
    require(sha(ORIGINAL)==ISHA and sha(WRAPPER)==WSHA and sha(LEGACY)==LSHA,'original entry source changed')
    for path,pin in inv['watched_files'].items():require(sha(Path(path))==pin,'watched original input changed')
    for path,pin in package['files'].items():require(sha(P/path)==pin,'published observer package changed')
   except BaseException as error:code=1;errors.append(dict(error_type=type(error).__name__,error=str(error)))
  archived_adapter=[]
  try:
   adir=OUTPUT/'original_run/adapter_invocations';adir.mkdir(parents=True,exist_ok=True)
   for src in sorted((P/'results/formal_main_v2/adapter_invocations').glob(job+'_*')):
    require(src.is_file() and src.suffix in ('.json','.jsonl') and not src.is_symlink(),'unexpected adapter artifact')
    b=src.read_bytes();dst=adir/src.name
    with dst.open('xb') as f:f.write(b)
    require(sha(src)==sha(dst),'adapter changed during exact archive');archived_adapter.append(dict(source=str(src),path=str(dst),sha256=sha(dst),bytes=len(b)))
   if code==0:require(len(archived_adapter)==2,'exact one original adapter pair required')
  except BaseException as error:code=1;errors.append(dict(error_type=type(error).__name__,error=str(error)))
  complete=dict(schema='formal_main_v2',kind='goal_full200_engineering_attempt',version=VERSION,status='returned_200_prospective_pending_terminal_review' if code==0 else 'failed_no_retry',job_id=job,exit_code=code,authorization_sha256=gate['auth_sha'],package_manifest_sha256=gate['manifest_sha'],adapter_artifacts=archived_adapter,original_runtime_restored=restored,raw_observation_root=str(RAW),raw_observation_claim=raw_claim,errors=errors,observer_failed=getattr(observer,'dead',None),runtime_context='real_environment_engineering',last_paired_input_abort=getattr(observer,'last_gate_abort',None),accepted_queries_retained=sum(getattr(observer,'query_counts',{}).values()),executed_policy_steps_retained=getattr(observer,'executed_policy_steps',0),paired_t0_checks_retained=len(getattr(observer,'paired_keys',set())),last_observer_abort=getattr(observer,'last_abort',None),observer_begun=getattr(observer,'begun',0),observer_finished=getattr(observer,'finished',0),maximum_attempts=1,automatic_retry=False,original_actions_forced=False,scientific_trials_added=0,original_goal200_HOLD=True,new_Goal_science_HOLD=True,final_release=False,wall_seconds=time.perf_counter()-started,raw_event_sha256=sha(eventpath) if eventpath.exists() else None,cost_scope='Charge complete Slurm allocation once, including loading, observer I/O and failures; never scientific timing.')
  with (outer/'completion.json').open('x',encoding='utf-8') as f:json.dump(complete,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 return code

def verify_published(expected_manifest_sha):
 require(Path(__file__).resolve()==ENTRY,'verification only at exact published P entry')
 package=read(MANIFEST,expected_manifest_sha);require(package.get('version')==VERSION and set(package.get('files',{}))==PACKAGE_FILES,'exact complete package closure')
 for path,pin in package['files'].items():require_path(P/path,P/path);require(sha(P/path)==pin,'published package changed')
 validate_config(read(CONFIG));decision=read(R/ROOT_DECISION_REL,ROOT_DECISION_SHA)
 require(decision['status']=='fixed_design_adopted_runtime_and_GPU_HOLD' and not decision['GPU_execution_authorized'],'design only cannot self-authorize GPU')
 inv,wrapper,ctx,legacy=prepare_original();identity=validate_prefix(inv,legacy,read(P/PKG/'specification.json',PREFIX_SHA)['rows'])
 storage=load(P/PKG/'storage.py','goal200_verify_storage',STORAGE_SHA);capacity=storage.verify_storage()
 return {'status':'passed_metadata_source_capacity_only','stage_key':STAGE,'package_manifest_sha256':expected_manifest_sha,'config_sha256':sha(CONFIG),'identity':identity,'storage':capacity,'new_GPU_submissions':0,'actual_GPU_runtime_verified':False,'GPU_execution_authorized':False,'original200_HOLD':True,'final_release':False}

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--authorization',type=Path);parser.add_argument('--authorization-sha256');parser.add_argument('--verify',action='store_true');parser.add_argument('--package-manifest-sha256');args=parser.parse_args(argv)
 if args.verify:
  require(args.authorization is None and args.authorization_sha256 is None and re.fullmatch('[0-9a-f]{64}',str(args.package_manifest_sha256)),'verify requires only exact package pin')
  print(json.dumps(verify_published(args.package_manifest_sha256),sort_keys=True));return 0
 require(args.authorization is not None and args.authorization_sha256 is not None and args.package_manifest_sha256 is None,'execute requires exact root authorization')
 require(os.name=='posix' and Path(__file__).resolve()==ENTRY,'only exact published engineering entry may execute');job=os.environ.get('SLURM_JOB_ID','');require(re.fullmatch('[1-9][0-9]*',job),'one registered Slurm GPU job required');require_path(args.authorization,AUTH);require(os.environ.get('SLURM_RESTART_COUNT','0')=='0','requeue/restart forbidden')
 require(all(os.environ.get(k)==v for k,v in THREADS.items()),'original runtime environment/thread settings required');require(os.environ.get('SLURM_CPUS_PER_TASK')=='7' and os.environ.get('SLURMD_NODENAME')!='gpu4020','registered resources/node restriction required')
 require_path(CONFIG,CONFIG);config=read(CONFIG);validate_config(config);require_path(MANIFEST,MANIFEST);manifest_sha=sha(MANIFEST);package=read(MANIFEST);require(package.get('schema')=='formal_main_v2' and package.get('version')==VERSION and set(package.get('files',{}))==PACKAGE_FILES,'exact reviewed package closure required')
 for path,pin in package['files'].items():require_path(P/path,P/path);require(sha(P/path)==pin,'package bytes changed before GPU')
 auth=read(AUTH,args.authorization_sha256);validate_authorization(auth,sha(CONFIG),manifest_sha,sha(ENTRY))
 for role in ('root','independent'):
  review=validate_review_ref(auth[role+'_review'],role);path=BASE/(role+'_readiness.json');require_path(path,path);check_review(read(path,review['sha256']),role,manifest_sha,sha(CONFIG))
 require_path(DISPATCH,DISPATCH);require_path(RESERVATION,RESERVATION);dispatch=read(DISPATCH);reservation=read(RESERVATION);validate_dispatch(dispatch,reservation,auth,args.authorization_sha256,job,sha(RESERVATION))
 # Original method/stage locks are shared with the scientific wrapper, while
 # the new output directory is an independent one-shot claim for this attempt.
 inv=read(ORIGINAL,ISHA)
 with ExitStack() as stack:
  names=[inv['stage_key'],*[f"{inv['suite']}_{inv['stage']}_{mid}" for mid in inv['method_ids']]]
  require(len(names)==len(set(names)),'duplicate original stage/method locks')
  for name in sorted(names):
   require(re.fullmatch('[A-Za-z0-9_-]+',name),'unsafe original stage key');p=P/'results/formal_main_v2/stage_locks'/(name+'.lock');f=stack.enter_context(p.open('a'));fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  return execute(config,auth,job,package,dict(auth_sha=args.authorization_sha256,manifest_sha=manifest_sha))
if __name__=='__main__':raise SystemExit(main())

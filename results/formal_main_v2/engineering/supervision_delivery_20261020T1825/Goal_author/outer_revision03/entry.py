"""One explicitly authorized Goal prefix58 engineering attempt; no submission API.

Root must first publish/review this package, reserve one of eight slots under the
shared writer lock/CAS, submit held, reconcile the exact ACK/token and record the
job before release. This entry consumes only that NEW authorization/dispatch.
It never claims scientific completion or retries. The unchanged inherited reset
may swallow exceptions; the required Slurm1800-second bound is authoritative.
"""
from __future__ import annotations
import argparse,copy,fcntl,hashlib,importlib.util,json,os,re,sys,time,traceback
from contextlib import ExitStack
from datetime import datetime,timezone
from pathlib import Path
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');S=P/'snapshots/formal_main_v2_run_564be0995e'
PKG='scripts/ops/formal_goal_prefix58_observer_v2';STAGE='goal_prefix58_20261020T1825';BASE=P/'results/formal_main_v2/engineering'/STAGE;OUTPUT=BASE/'attempt01';ENTRY=P/PKG/'entry.py';CONFIG=P/PKG/'config.json';MANIFEST=P/PKG/'package_manifest.json';AUTH=BASE/'root_authorization.json';DISPATCH=BASE/'held_dispatch_record.json';RESERVATION=BASE/'reservation.json'
VERSION='goal-prefix58-single-attempt-v2';WRAPPER=P/'scripts/ops/formal_action_deployment_v1/wrapper.py';WSHA='d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33';LEGACY=P/'scripts/ops/formal_evaluation_adapter.py';LSHA='b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd'
ORIGINAL=P/'results/formal_main_v2/invocations/libero_goal_development_5185766bb353c8e6_attempt01.json';ISHA='c07489c5e56cc3255b60f5eb6df34146e37e4b60fa7151cc97f8008f402b8803';PREFIX_SHA='1e786af6b4aafb52dba32bce1494c5e4dd4ef05c41f10cb3b9a77342c2cbcb28'
THREADS={'OMP_NUM_THREADS':'7','OPENBLAS_NUM_THREADS':'7','MKL_NUM_THREADS':'7','TF_NUM_INTRAOP_THREADS':'7','TF_NUM_INTEROP_THREADS':'1','TOKENIZERS_PARALLELISM':'false','MUJOCO_GL':'egl','LIBERO_CONFIG_PATH':str(P/'configs/libero_runtime'),'PYTHONPATH':str(S/'src'),'PYTHONDONTWRITEBYTECODE':'1'}
RESOURCES={'partition':'L40','gres':'gpu:l40:1','cpus_per_task':7,'mem':'64G','wall_seconds':1800,'no_requeue':True,'excluded_nodes':['gpu4020']}
PACKAGE_FILES={PKG+'/'+x for x in ('entry.py','observer_v3.py','ast_observer_v2.py','config.json','prefix58.json','run.slurm')}
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
 expected={'schema':'formal_main_v2','kind':'goal_prefix58_single_attempt_configuration','version':VERSION,'stage_key':STAGE,'suite':'libero_goal','seed':17,'tokens':256,'method_ids':['A256_seed17','B256_seed17'],'maximum_trials':58,'unique_development_states':29,'wait_steps':10,'action_chunk':8,'max_control_steps':300,'maximum_attempts':1,'automatic_retry':False,'scientific_trials_added':0,'original200_HOLD':True,'new_Goal_science_HOLD':True,'historical_actions_forced':False,'resources':RESOURCES,'original_invocation':{'path':str(ORIGINAL),'sha256':ISHA},'prefix':{'path':str(P/PKG/'prefix58.json'),'sha256':PREFIX_SHA},'output':str(OUTPUT),'final_evaluation_enabled':False}
 require(all(c.get(k)==v for k,v in expected.items()),'exact original58 diagnostic scope/resource configuration required')
 require(set(c)==set(expected)|{'schema_note'},'unexpected configuration fields')
def validate_authorization(a,config_sha,manifest_sha,entry_sha):
 fixed={'schema':'formal_main_v2','kind':'root_goal_prefix58_single_attempt_authorization','version':VERSION,'status':'approved','reviewed_by':'root','stage_key':STAGE,'config_sha256':config_sha,'package_manifest_sha256':manifest_sha,'entrypoint_sha256':entry_sha,'maximum_gpu_jobs':1,'maximum_attempts':1,'maximum_wall_seconds':1800,'counts_against_8_GPU_slots':True,'automatic_retry':False,'scientific_release':False,'original_goal200_HOLD':True,'new_Goal_science_HOLD':True,'maximum_trials':58,'resources':RESOURCES,'dispatch_record_path':str(DISPATCH),'reservation_path':str(RESERVATION)}
 require(all(a.get(k)==v for k,v in fixed.items()),'new exact Goal prefix58 root authorization required')
 require(set(a)==set(fixed)|{'root_review','independent_review'},'unexpected authorization fields')
 require(a['root_review']!=a['independent_review'],'root and independent review must differ')
 for role in ('root','independent'):validate_review_ref(a[role+'_review'],role)
def validate_review_ref(value,role):
 require(role in ('root','independent') and isinstance(value,dict) and set(value)=={'path','sha256'},'readiness reference must contain exactly path and SHA')
 require(value['path']==str(BASE/(role+'_readiness.json')) and isinstance(value['sha256'],str) and re.fullmatch('[0-9a-f]{64}',value['sha256']),'exact new readiness path and 64-hex SHA required before target I/O')
 return value
def check_review(value,role,manifest_sha,config_sha):
 fixed={'schema':'formal_main_v2','kind':'goal_prefix58_single_attempt_CPU_readiness','status':'passed','reviewed_by':role,'version':VERSION,'package_manifest_sha256':manifest_sha,'config_sha256':config_sha,'original_chain_preserved':True,'observer_gaps_fixed':True,'real_GPU_acceptance':False,'scientific_release':False}
 require(all(value.get(k)==v for k,v in fixed.items()),'complete matching CPU-only readiness required')
def validate_dispatch(d,res,a,auth_sha,job,reservation_sha):
 fixed={'schema':'formal_main_v2','kind':'root_goal_prefix58_held_dispatch','status':'held_registered_before_release','stage_key':STAGE,'job_id':job,'authorization':{'path':str(AUTH),'sha256':auth_sha},'request_token':'cti-goal-prefix58-v2:'+auth_sha,'capacity_limit_all_GPU_modes':8,'reserved_slots':1,'maximum_attempts':1,'new_submissions':1,'no_requeue':True,'scientific_release':False,'resources':RESOURCES}
 require(all(d.get(k)==v for k,v in fixed.items()),'exact held ACK registration must precede release')
 require(isinstance(d.get('occupied_job_ids'),list) and len(set(d['occupied_job_ids']))==len(d['occupied_job_ids'])<=8 and job in d['occupied_job_ids'],'one registered slot within all-GPU eight limit required')
 require(re.fullmatch('[0-9a-f]{64}',str(d.get('state_after_sha256'))),'root writer-lock/CAS snapshot identity missing')
 require(d.get('reservation')=={'path':str(RESERVATION),'sha256':reservation_sha},'exact root reservation pin missing')
 rf={'schema':'formal_main_v2','kind':'root_goal_prefix58_GPU_slot_reservation','status':'approved_for_exact_prefix58','stage_key':STAGE,'authorization':fixed['authorization'],'reserved_slots':1,'capacity_limit_all_GPU_modes':8,'maximum_wall_seconds':1800,'automatic_retry':False,'scientific_release':False}
 require(all(res.get(k)==v for k,v in rf.items()),'new prefix58 reservation required; old probe reservation forbidden')
def prepare_original():
 inv=read(ORIGINAL,ISHA);wrapper=load(WRAPPER,'g58_original_wrapper',WSHA);ctx=wrapper.verify(inv,project=P);legacy=load(LEGACY,'g58_original_legacy_adapter',LSHA)
 a=ctx['args'];require(a.mode=='evaluate' and not a.resume and not a.prepare_only and Path(a.output)==Path(inv['run_root']),'original args/mode changed')
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
 keys=('trial_id','state_trial_id','task_id','task_name','source_state_index','initial_state_sha256','method','environment_seed','runtime_seed')
 with legacy.source_imports(S):
  from cti_vla.evaluation import formal_trials
  actual=[{k:v for k,v in formal_trials._identity(panel,state,mid).items() if k in keys} for state in panel['states'] for mid in ['A256_seed17','B256_seed17']][:58]
 require(len(prefix)==58 and actual==[{k:row[k] for k in keys} for row in prefix],'exact first58 original identity/order required before observer creation')
 require(len({x['state_trial_id'] for x in actual})==29 and all(x['task_id']==2 and x['source_state_index']==42 for x in actual[-2:]),'fixed prefix endpoint differs')
 return dict(original_panel=ref(panelpath),original_fixed58_identity_order=True,unique_development_states=29)

def execute(config,auth,job,package,gate):
 # Everything this entry owns is a fresh engineering subtree. The unchanged
 # legacy adapter separately retains its ordinary adapter provenance journal.
 require(not OUTPUT.exists(),'one attempt already exists; retry forbidden')
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
  original_run=legacy.run;original_code=original_run.__code__;runtime=ctx['runtime'];contract=ctx['execution_contract'];original=ctx['original_plan'];prefix=read(P/PKG/'prefix58.json',PREFIX_SHA)['rows'];prefix_proof=validate_prefix(inv,legacy,prefix);ob=load(P/PKG/'observer_v3.py','g58_passive_observer',package['files'][PKG+'/observer_v3.py']);ad=load(P/PKG/'ast_observer_v2.py','g58_ast_observer',package['files'][PKG+'/ast_observer_v2.py']);observer=ob.PassiveObserver(OUTPUT/'observer',prefix)
  a=copy.deepcopy(ctx['args']);before_args=copy.deepcopy(vars(a));a.output=OUTPUT/'original_run';a.stop_after=58;require({k for k in vars(a) if vars(a)[k]!=before_args[k]}=={'output','stop_after'},'only engineering output and stop58 may change')
  emit('engineering_start',version=VERSION,authorization_sha256=gate['auth_sha'],package_manifest_sha256=gate['manifest_sha'],original_invocation=ref(ORIGINAL),environment={k:os.environ.get(k) for k in list(THREADS)+['CUDA_VISIBLE_DEVICES','SLURM_JOB_ID','SLURMD_NODENAME']},original_argument_changes={'output':str(a.output),'stop_after':58},prefix_identity_proof=prefix_proof,original_adapter_run_code_sha256=legacy.code_sha(original_run),original_actions_forced=False)
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
  finish=observer.finish();require(finish['original_prefix_trials']==58 and finish['scientific_trials_added']==0,'incomplete engineering prefix')
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
  complete=dict(schema='formal_main_v2',kind='goal_prefix58_engineering_attempt',version=VERSION,status='returned_58_engineering_only' if code==0 else 'failed_no_retry',job_id=job,exit_code=code,authorization_sha256=gate['auth_sha'],package_manifest_sha256=gate['manifest_sha'],original_runtime_restored=restored,errors=errors,observer_failed=getattr(observer,'dead',None),last_observer_abort=getattr(observer,'last_abort',None),observer_begun=getattr(observer,'begun',0),observer_finished=getattr(observer,'finished',0),maximum_attempts=1,automatic_retry=False,original_actions_forced=False,scientific_trials_added=0,original_goal200_HOLD=True,new_Goal_science_HOLD=True,final_release=False,wall_seconds=time.perf_counter()-started,raw_event_sha256=sha(eventpath) if eventpath.exists() else None,cost_scope='Charge complete Slurm allocation once, including loading, observer I/O and failures; never scientific timing.')
  with (outer/'completion.json').open('x',encoding='utf-8') as f:json.dump(complete,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 return code

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--authorization',required=True,type=Path);parser.add_argument('--authorization-sha256',required=True);args=parser.parse_args(argv)
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

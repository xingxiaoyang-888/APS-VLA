"""Four exact nonLong development candidates using unchanged published pure APIs."""
import copy,hashlib,importlib.util,json,os,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';DI=R/'.local/nonLong_development_plans_1317';D=DI/'attempt01';DEST='results/formal_main_v2/execution/nonLong_action_v1_1317';PRE='scripts/ops/formal_action_deployment_v1/';INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
PIN={'scripts/formal_execution_manifests.py':'614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89','scripts/ops/formal_downstream_supervisor.py':'f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571','scripts/server/run_formal_downstream.py':'f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24',PRE+'contract.py':'efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19',PRE+'entry.py':'2cdb69923146cbffcaaec555b970d03efbce0c9b9f74e3b743a2ce67a21aae19',PRE+'wrapper.py':'d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33',PRE+'gateway.py':'8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a',PRE+'runtime_scope.py':'6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53',PRE+'reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd',PRE+'consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'}
GROUPS=[('libero_goal', 128, 41, 'libero_goal_k128_seed41_development.json', 'b4a970f504a487b62d655b9eecdece8359c986fe3cdc394c33115e832cd604bf', ['A128_seed41', 'B128_seed41']), ('libero_spatial', 256, 17, 'libero_spatial_k256_seed17_development.json', 'db7cfa807c060c51a7aef714a6625ef4b12fcaa7f01dde385a874fe2cf2a1d36', ['A256_seed17', 'B256_seed17']), ('libero_object', 256, 17, 'libero_object_k256_seed17_development.json', '1aae788e4337db9325234f7da5b1dcb7e7b99187b5388b74811431fa0355ac33', ['A256_seed17', 'B256_seed17']), ('libero_goal', 256, 17, 'libero_goal_k256_seed17_development.json', '3b33f2d0e0c924ac919920a2a12b1c0e8cb9e059c58d58a639fd33f4651036c2', ['A256_seed17', 'B256_seed17'])]
READS={};TESTS=[];OUTPUTS={};sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No child/network/Slurm in private CPU preparation')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(path));p=p if p.is_absolute() else Path.cwd()/p
   assert not any('sealed' in x.lower() or x.lower() in ['weights','checkpoints'] for x in p.parts),'weight or sealed target forbidden'
   assert p.suffix.lower() not in ['.pt','.pth','.bin','.safetensors','.pkl','.pickle','.ckpt','.init','.pruned_init'],'weight suffix forbidden'
   writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC)))
   if writing:assert D in p.parents,'private writes only: '+str(p)
sys.addaudithook(guard)
def require(v,m):
 if not v:raise ValueError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(path,pin=None):
 p=Path(path);p=p if p.is_absolute() else R/p;require(p.resolve()==p and (R in p.parents or P in p.parents),'R/P canonical read required')
 raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();require(pin is None or pin==h,'SHA changed: '+str(p));require(str(p) not in READS or READS[str(p)]==h,'evidence drift');READS[str(p)]=h;return raw
def js(p,h=None):return json.loads(read(p,h))
def write(rel,obj):
 p=D/rel;require(D in p.parents,'private output only');p.parent.mkdir(parents=True,exist_ok=True);raw=obj if isinstance(obj,bytes) else (json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(raw)
 r={'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)};OUTPUTS[rel]=r;return r
def load(rel,root=R):
 p=root/rel;raw=read(p,PIN[rel]);name='nonlong1317_'+p.stem+'_'+str(len(sys.modules));sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;exec(compile(raw,str(p),'exec'),m.__dict__);return m
def reject(name,fn,part):
 try:fn()
 except (ValueError,RuntimeError) as e:require(part in str(e),'wrong rejection: '+str(e));TESTS.append({'name':name,'status':'expected_rejection','error':str(e),'synthetic_input_only':True});return
 raise ValueError('Unsafe acceptance: '+name)
def main():
 t0=time.perf_counter();c0=time.process_time();inventory=js(INV,'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');require(len(inventory['files'])==173,'source count')
 for root in (R,S):
  for rel,h in inventory['files'].items():read(root/rel,h)
 for rel,h in PIN.items():
  read(rel,h)
  if rel.startswith(PRE) or rel=='scripts/server/run_formal_downstream.py':read(P/rel,h)
 h=load('scripts/formal_execution_manifests.py');planner=load('scripts/ops/formal_downstream_supervisor.py');c=load(PRE+'contract.py');runtime=load(PRE+'runtime_scope.py');gw=load(PRE+'gateway.py');ow=load('scripts/server/run_formal_downstream.py',P);wrapper=load(PRE+'wrapper.py',P)
 state_raw=read(DI/'state_at_planning.json','54f7e30dc48af1d0c4dbf9af605633ff4a337d61aee4b98c715dffa5d1a6831f');state=json.loads(state_raw);write('state_at_planning.json',state_raw);baseline=copy.deepcopy(state);require(state.get('pending_submission') is None,'pending must reconcile beforeplanning')
 components={'runtime':{'path':'results/formal_main_v2/engineering/action_deployment_candidates_0809/action_deployment_chain_independent_0809/runtime_component_independent_projection.json','sha256':'927cb53f1b06d01c0d49ea86449d0aeb62aa6ec6285045e6d9d6d3c4ea77abc4'},'wrapper':{'path':'results/formal_main_v2/engineering/action_deployment_candidates_0809/action_deployment_chain_independent_0809/wrapper_component_independent_projection.json','sha256':'14bfa92531e1e895ffe0da595b508810e1454333d74db5fbcc12acb1cf1ae146'},'raw_consumer':{'path':'results/formal_main_v2/engineering/action_deployment_candidates_0809/action_gateway_consumers_independent_0809/raw_consumer_independent_review.json','sha256':'3f815f3a48755e16e01219eb7f24c2b3fcb84e65d769d1e0a1d141a84d769479'}}
 gi={'path':'results/formal_main_v2/engineering/action_deployment_candidates_0809/action_gateway_consumers_independent_0809/gateway_independent_review.json','sha256':'c232149639a1e6335189610aebba19830e1a3c8bfe9b932d1398566f10cd2b4f'}
 for role,r in components.items():v=js(r['path'],r['sha256']);require(v['component']==role and v['status']=='passed_CPU_review' and not v.get('blockers'),'originalcomponentreview')
 js(gi['path'],gi['sha256']);read(gw.CONTROLLER,gw.CONTROLLER_SHA);js(gw.ACTIVATION['path'],gw.ACTIVATION['sha256']);js(gw.GAP['path'],gw.GAP['sha256'])
 allplans=[];pub=[]
 for suite,budget,seed,name,msha,methods in GROUPS:
  sub=f'{suite}_k{budget}_seed{seed}';dest=DEST+'/'+sub;manifest=DEST+'/'+name
  read(DI/name,msha);read(manifest,msha);read(P/manifest,msha)
  args=dict(stage='development',source_inventory=INV,execution_manifest=manifest,output_relative=None,freeze_directory=None,profile_panel=None,prior_review=None,collection_review=None,repair_record=None,resume=False,stop_after=None)
  write(sub+'/plan_arguments.json',args);science=planner.plan(SimpleNamespace(**args),copy.deepcopy(state),project=R,helper=h);inv=science['invocation']
  require(inv['suite']==suite and inv['stage']=='development' and inv['method_ids']==methods and not inv['resume'] and inv['prior_job_ids']==[],'scope orduplicatehistory')
  require(science['resources']==gw.RESOURCES,'originalresources changed')
  for rel in [science['output_relative'],science['invocation_relative']]:require(not(R/rel).exists() and not(P/rel).exists(),'alreadyexisting runtime output')
  require('--global-freeze' not in inv['argv'] and '--sealed-final' not in inv['argv'],'forbiddenstageflags')
  def emit(name,value):
   row=write(sub+'/'+name,value);return {'path':dest+'/'+name,'sha256':row['sha256']}
  sr=emit('scientific_plan.json',science);old_verified=ow.verify(inv);require(old_verified.mode=='evaluate','wrongoriginalstage')
  scope=runtime.make_contract(project_root=R,source_root=S,suite=suite,stage='development');require(scope==runtime.make_contract(project_root=P,source_root=S,suite=suite,stage='development'),'R/P runtimecontract')
  runtimefiles={}
  for root in (R,P):runtimefiles.update(runtime.validate_contract(scope,project_root=root,source_root=S))
  for p,pin in runtimefiles.items():read(p,pin)
  assets=runtime.expected_asset_identities(project_root=P,source_root=S,contract=scope,asset_contract=inv.get('downstream_asset_compatibility'))
  emit('runtime_asset_metadata_identities.json',assets);emit('runtime_contract.json',scope)
  files={rel:PIN[rel] for rel in c.EXPECTED_NEW_FILES};files[c.ACTION_ADAPTER]=c.ACTION_SHA
  action=dict(schema=c.SCHEMA,kind='formal_action_execution_contract',version=c.VERSION,status='candidate_pending_root_readiness',scientific_settings_changed=False,final_evaluation_enabled=False,files=files,runtime_contract=scope,GPU_acceptance=c.GPU_REFS,source_inventory={'path':c.INVENTORY,'sha256':c.INVENTORY_SHA},transition=None)
  ar=emit('execution_contract.json',action);effective=c.effective_plan(science,scientific_plan_ref=sr,execution_contract_ref=ar,execution_contract=action);er=emit('effective_plan.json',effective)
  ready=dict(schema=c.SCHEMA,kind='formal_action_runtime_readiness',status='draft_pending_actual_plan_reviews',reviewed_by=None,execution_version=c.VERSION,scientific_settings_changed=False,final_evaluation_enabled=False,raw_consumer_ready=False,effective_plan=er,scientific_plan=sr,plan_sha256=effective['plan_sha256'],runtime_sources=files,root_review=None,independent_review=None,production_chain_complete=False,allowed_stages=['development'],allowed_suite=suite,forbidden_stages=['collect','full','components','global_freeze','final'],method_ids=methods,expected_trials=100*len(methods),support_files=effective['invocation']['support_files'],action_execution_contract=ar,component_reviews=components,runtime_publication_files={er['path']:er['sha256'],**{r['path']:r['sha256'] for r in components.values()}},unique_development_initial_states=100,active=False,O2A_enabled=False,global_freeze_enabled=False,actual_GPU_runtime_chain_verified=False)
  emit('runtime_readiness_draft.json',ready)
  auth=dict(schema=c.SCHEMA,kind='formal_downstream_single_submission_authorization',version=gw.VERSION,status='draft_not_approved',control_root=str(R),runtime_root=str(P),controller_activation=gw.ACTIVATION,maximum_attempts=1,automatic_retry=False,excluded_nodes=['gpu4020'],gateway_files=gw.source_files(R),planner={'path':gw.PLANNER,'sha256':gw.PLANNER_SHA},controller={'path':gw.CONTROLLER,'sha256':gw.CONTROLLER_SHA},gap_review=gw.GAP,final_release_authorized_by_gateway=False,independent_review=gi,plan=er,scientific_plan=sr,prepared_invocation=None,plan_arguments=args,runtime_readiness=None,controller_job_id=state['autonomous_training_v1']['controller_job_id'],root_reservation=None)
  dr=emit('submission_authorization_draft.json',auth);emit('reservation_root_record_draft.json',dict(schema=c.SCHEMA,kind='root_downstream_GPU_slot_reservation',status='draft_not_approved',controller_job_id=auth['controller_job_id'],reserved_slots=1,capacity_limit_all_GPU_modes=8,automatic_retry=False,stage_key=inv['stage_key'],plan=er,authorization_path=dest+'/submission_authorization.json',authorization_intent_sha256=None))
  emit('prepared_invocation_template.json',{**effective['invocation'],'registered_utc':None,'plan_sha256':effective['plan_sha256'],'runtime_readiness':None})
  proposed={r['path']:OUTPUTS[sub+'/'+n] for n,r in [('scientific_plan.json',sr),('execution_contract.json',ar),('effective_plan.json',er)]}
  runtime_need={**effective['invocation']['watched_files'],**{str(P/n):v for n,v in effective['invocation']['support_files'].items()},**{str(P/n):v for n,v in ready['runtime_publication_files'].items()}}
  closure=[]
  for path,pin in sorted(runtime_need.items()):
   p=Path(path);require(P in p.parents and p.resolve()==p,'noncanonicalPdependency');rel=p.relative_to(P).as_posix()
   if rel in proposed:
    source=R/proposed[rel]['path'];read(source,pin);status='newcandidate_pending_rootpublication'
   else:
    source=R/rel if rel in effective['publish_files'] or not p.is_file() else p
    read(source,pin);status='present_exact' if p.is_file() else 'existing_R_pending_P_copy'
   if p.is_file():read(p,pin)
   if status!='present_exact':pub.append({'canonical_path':rel,'candidate_path':source.relative_to(R).as_posix(),'sha256':pin,'bytes':source.stat().st_size,'suite':suite,'budget':budget,'seed':seed,'group_key':sub})
   closure.append({'path':path,'sha256':pin,'status':status})
  emit('runtime_dependency_closure.json',closure)
  for p,pin in inv['root_evidence_sha256'].items():read(p,pin)
  reject(sub+'_missing_root_readiness',lambda:wrapper.verify(effective['invocation'],project=P),'Exact path/SHA reference required')
  reject(sub+'_draft_authorization',lambda:gw.validate_authorization(R,{'path':OUTPUTS[sub+'/submission_authorization_draft.json']['path'],'sha256':dr['sha256']}),'typed root authorization absent')
  require(planner.plan(SimpleNamespace(**args),copy.deepcopy(state),project=R,helper=h)==science,'pureplanner no longerreconstructs')
  allplans.append({'group_key':sub,'suite':suite,'budget':budget,'seed':seed,'methods':methods,'trials':100*len(methods),'manifest':{'path':manifest,'sha256':msha},'scientific_plan':sr,'execution_contract':ar,'effective_plan':er,'original_P_scientific_wrapper_verify_passed':True,'new_P_wrapper_verify_passed':False,'runtime_metadata_identity_verified':True,'exact_runtime_readiness_created':False,'actual_GPU_calls':0,'stage_key':inv['stage_key'],'run_root':inv['run_root'],'invocation_relative':science['invocation_relative'],'resources':science['resources']})
 require(state==baseline,'actualsnapshot mutated')
 for p,pin in READS.items():require(sha(p)==pin,'source/evidence drift')
 write('publication_map.json',{'schema':'formal_main_v2','status':'pending_root_publication_not_permitted_by_this_file','files':pub})
 write('read_evidence_sha256.json',READS);write('CPU_checks.json',{'tests':TESTS,'private_only':True,'synthetic_receipts_published':False,'new_GPU_calls':0})
 write('candidate_review.json',{'schema':'formal_main_v2','kind':'nonLong_exact_development_author_CPU_candidates','status':'original_science_CPU_prepared_new_runtime_readiness_pending','created_utc':datetime.now(timezone.utc).isoformat(),'plans':allplans,'state_at_planning_sha256':hashlib.sha256(state_raw).hexdigest(),'source173_unchanged':True,'source_files':PIN,'total_planned_trials':800,'unique_initial_states_per_suite':100,'reuse_or_rerun_historical':False,'weights_or_sealed_values_read':False,'new_GPU_seconds':0,'production_files_changed':False,'state_Git_modified':False,'root_readiness_or_submission_authorization_created':False,'CPU_wall_seconds':time.perf_counter()-t0,'CPU_process_seconds':time.process_time()-c0,'remaining':['Independent exactplan/source/input audit','Root publication of static science/contract/effective dependencyclosures','Root and independent trueperplan readiness incl actualnewP wrapper.verify onexactpreparedinvocation','Exact one-use rootauthorization/reservation and current8slot/owner/pending preflight throughunchangedgateway','Rootonlysingle submission; completedrawresults requireoriginalconsumer plusindependentterminal review'],'final_release':False})
 files=[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(D.rglob('*')) if p.is_file() and p.name!='manifest.json']
 write('manifest.json',{'schema':'formal_main_v2','kind':'nonLong_development_private_candidate_delivery','files':files,'production_activation':False})
 print(json.dumps({'status':'prepared_not_admitted','manifest_sha256':sha(D/'manifest.json'),'report_sha256':sha(D/'candidate_review.json'),'plans':allplans,'CPU_seconds':time.process_time()-c0}))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  write('preparation_failure_v1.json',{'error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'partial_outputs':OUTPUTS,'GPU_calls':0,'production_changed':False});raise

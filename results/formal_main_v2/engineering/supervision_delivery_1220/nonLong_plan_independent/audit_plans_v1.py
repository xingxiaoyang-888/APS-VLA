"""Independent bounded audit of three exact non-Long development candidates.
Metadata/source gates only; no live state, Slurm, GPU, weights or final values.
"""
import copy,hashlib,importlib.util,json,os,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
from collections import Counter
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/nonLong_development_plans_independent_1220'
BASE=R/'.local/nonLong_development_plans_1220'
A=BASE/'attempt01'
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
PREFIX='scripts/ops/formal_action_deployment_v1/'
REVIEWER='/root/goal256_s41_terminal_0333'
READS={};CHECKS=[];OUTPUTS=[]
sys.dont_write_bytecode=True
sys.path[:0]=[str(R/'src'),str(R/'scripts')]
os.chdir(R)
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('Audit forbids process/network/Slurm')
 if event=='open':
  name,mode,flags=args
  if isinstance(name,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(name));p=p if p.is_absolute() else Path.cwd()/p
   if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) or p.suffix.lower() in ('.pt','.pth','.bin','.safetensors','.ckpt','.pkl','.pickle','.init','.pruned_init') or p.name.lower()=='init_states_test.json' or (p.name=='panel.json' and 'final' in p.parts):raise RuntimeError('Forbidden weight/final value path')
   writing=isinstance(mode,str) and any(c in mode for c in 'wax+') or isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC))
   if writing and D not in p.parents:raise RuntimeError('Private audit writes only: '+str(p))
sys.addaudithook(guard)
def need(v,msg):
 if not v:raise ValueError(msg)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(path,pin=None):
 p=Path(path);p=p if p.is_absolute() else R/p
 need(p.resolve()==p and (R in p.parents or P in p.parents),'Noncanonical evidence path')
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest();need(pin is None or h==pin,'SHA mismatch '+str(p))
 need(str(p) not in READS or READS[str(p)]==h,'Evidence drift '+str(p));READS[str(p)]=h
 return b
def js(path,pin=None):return json.loads(read(path,pin))
def ref(path):
 p=Path(path);p=p if p.is_absolute() else R/p
 return {'path':p.relative_to(R).as_posix(),'sha256':digest(p)}
def dump(name,value):
 p=D/name;p.parent.mkdir(parents=True,exist_ok=True)
 b=(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 row={'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};OUTPUTS.append(row);return row
def load(path,pin,root=R):
 p=root/path;b=read(p,pin);name='indnonlong1220_'+p.stem+'_'+str(len(sys.modules));spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;exec(compile(b,str(p),'exec'),m.__dict__);return m
def check(name,value):need(value,name);CHECKS.append({'name':name,'status':'passed'})
def main():
 start=time.perf_counter();cpu=time.process_time();mpin,dpin=sys.argv[1:3]
 need(len(mpin)==64 and all(c in '0123456789abcdef' for c in mpin),'Exact candidate manifest SHA required')
 delivery=js(BASE/'delivery_manifest.json',dpin)
 for item in delivery['files']:
  q=R/item['path'];need(BASE in q.parents,'author archive path');data=read(q,item['sha256']);need(len(data)==item['bytes'],'author archive bytes')
 manifest=js(A/'manifest.json',mpin)
 entries={r['path']:r for r in manifest['files']};need(len(entries)==len(manifest['files']),'duplicate archive entries')
 for path,row in entries.items():
  p=R/path;need(A in p.parents,'candidate manifest escapes private source');b=read(p,row['sha256']);need(len(b)==row['bytes'],'candidate size')
 author=js(A/'candidate_review.json');pin=author['source_files'];snapshot=js(A/'state_at_planning.json',author['state_at_planning_sha256']);snapshot_before=copy.deepcopy(snapshot)
 initial=js(D/'input_training_precheck.json','801d98d2fa8ffd1ebd8264f5cb151b726b7e3680e55fb4ed67c48635a3877a9d')
 read(D/'audit_inputs_v2.py','11217c8712c0ce87bbf57127b1607e7a7ab998af4790ed52aebeeb276c470e47')
 check('same_fixed_root_state_prechecked',initial['state_snapshot']['sha256']==author['state_at_planning_sha256']=='a32924884da6a900f98aea682642c70047c2b48df51d4d5524a7b4318f5e89b8')
 for rr in initial['read_evidence']:read(rr['path'],rr['sha256'])
 source_inventory=js(INV,'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 check('exact173scientific_sources',len(source_inventory['files'])==173)
 for root in (R,S):
  for path,sha in source_inventory['files'].items():read(root/path,sha)
 for path,sha in pin.items():
  read(path,sha)
  if path.startswith(PREFIX) or path=='scripts/server/run_formal_downstream.py':read(P/path,sha)
 h=load('scripts/formal_execution_manifests.py',pin['scripts/formal_execution_manifests.py'])
 planner=load('scripts/ops/formal_downstream_supervisor.py',pin['scripts/ops/formal_downstream_supervisor.py'])
 c=load(PREFIX+'contract.py',pin[PREFIX+'contract.py'])
 runtime=load(PREFIX+'runtime_scope.py',pin[PREFIX+'runtime_scope.py'])
 old=load('scripts/server/run_formal_downstream.py',pin['scripts/server/run_formal_downstream.py'],P)
 wrapper=load(PREFIX+'wrapper.py',pin[PREFIX+'wrapper.py'],P)
 gateway=load(PREFIX+'gateway.py',pin[PREFIX+'gateway.py'])
 e=h.Evidence(R);registration=h.registration_contract(e,planner.REGISTRATION);sources=h.source_contract(e,INV)
 expected=[('libero_spatial',41,['A128_seed41','B128_seed41'],200),('libero_object',41,['A128_seed41','B128_seed41'],200),('libero_goal',23,['A128_seed23','B128_seed23'],200)]
 check('exact_three_plans',[(x['suite'],x['seed'],x['methods'],x['trials']) for x in author['plans']]==expected)
 plans=[]
 for (suite,seed,methods,trials),row in zip(expected,author['plans']):
  sub=f'{suite}_k128_seed{seed}';prep=next(x for x in initial['plans'] if x['suite']==suite)
  spec=registration['suites'][suite];args=js(A/sub/'plan_arguments.json');science=js(A/sub/'scientific_plan.json',row['scientific_plan']['sha256']);action=js(A/sub/'execution_contract.json',row['execution_contract']['sha256']);effective=js(A/sub/'effective_plan.json',row['effective_plan']['sha256']);inv=science['invocation']
  check(sub+'_pure_scientific_reconstruction',planner.plan(SimpleNamespace(**args),copy.deepcopy(snapshot),project=R,helper=h)==science)
  check(sub+'_effective_reconstruction',c.effective_plan(science,scientific_plan_ref=row['scientific_plan'],execution_contract_ref=row['execution_contract'],execution_contract=action)==effective)
  c.validate_effective(science,effective,scientific_plan_ref=row['scientific_plan'],execution_contract_ref=row['execution_contract'],execution_contract=action)
  published=js(row['manifest']['path'],row['manifest']['sha256']);read(P/row['manifest']['path'],row['manifest']['sha256'])
  methodrows=h.suite_rows(e,registration,suite,sources,methods);made=h.make_execution(registration,suite,methodrows)
  panelpath=registration['suites'][suite]['initial_states_root']+'/development.json';panel=js(panelpath,published['development_panel_sha256'])
  made.update(development_panel=panelpath,development_panel_sha256=digest(R/panelpath))
  check(sub+'_original_manifest_reconstruction',made==published)
  check(sub+'_training_vs_runtime_seed',all(x['identity']['training_seed']==seed for x in methodrows) and spec['environment']['runtime_seed']==17 and spec['environment']['env_seed']==0 and '--seed' not in inv['argv'] and '--runtime-seed' not in inv['argv'])
  check(sub+'_exact_environment',published['environment']=={**h.ENVIRONMENT,'max_steps':spec['environment']['max_control_steps']} and spec['environment']['action_chunk']==8 and spec['environment']['wait_steps']==10)
  check(sub+'_common100devstates',panel['suite']==suite and panel['split']=='development' and len(panel['states'])==100 and Counter(x['task_id'] for x in panel['states'])==Counter({i:10 for i in range(10)}) and len({x['trial_id'] for x in panel['states']})==100)
  check(sub+'_fresh_scope',args['stage']=='development' and not args['resume'] and not args['prior_review'] and not args['freeze_directory'] and not inv['prior_job_ids'] and inv['method_ids']==methods and len(methods)==len(set(methods)) and not inv['prior_allocation_cost'])
  check(sub+'_no_old_method_overlap',all(not(set(j.get('method_ids',[]))&set(methods)) for j in planner.formal_jobs(snapshot) if j.get('suite')==suite and j.get('mode')=='development'))
  for relative in [science['output_relative'],science['invocation_relative']]:check(sub+'_fresh_'+relative.split('/')[-1],not(R/relative).exists() and not(P/relative).exists())
  check(sub+'_original_singleGPU_resources',science['resources']==gateway.RESOURCES)
  check(sub+'_no_future_or_final_input',not any(x in inv['argv'] for x in ('--sealed-final','--global-freeze','--release','--future-actions','--future-head','--teacher-cache')))
  selected=[]
  for method in methodrows:
   ident=method['identity']
   check(sub+'_'+ident['method_id']+'_own_official_base',ident['model_revision']==spec['model_revision'] and ident['frozen_model_sha256']==js(next(x for x in prep['selected'] if x['method_id']==ident['method_id'])['deployment_receipt']['path'])['metadata']['frozen_model_sha256'])
   if ident['method'] in ('A','B'):
    arm=ident['method'];r=js(method['receipt'],next(x for x in prep['selected'] if x['method_id']==ident['method_id'])['deployment_receipt']['sha256']);meta=r['metadata'];evaluations=r['evaluations'];best=min(evaluations,key=lambda x:(x['validation_metric'],x['update']))
    check(sub+'_'+arm+'_selected_from_complete5000',r['completed_updates']==5000 and [x['update'] for x in evaluations]==list(range(0,5001,500)) and meta['update']==best['update'] and meta['validation_metric']==best['validation_metric'] and r['checkpoint_sha256']==ident['checkpoint_sha256'] and meta['training_complete'] and r['base_frozen'] and r['checkpoint_unchanged'] and ident['future_head_deployed'] is False and meta['per_camera_budgets']==[64,64])
    selected.append({'method_id':ident['method_id'],'selected_update':meta['update'],'checkpoint':method['checkpoint'],'checkpoint_sha256':r['checkpoint_sha256'],'receipt':ref(method['receipt']),'original_identity':ident})
  for role in ('root_review','independent_review'):
   rr=prep['training_reviews'][role];review=js(rr['path'],rr['sha256']);check(sub+'_'+role,review.get('status')=='passed' or str(review.get('status','')).startswith('passed_'))
  oldargs=old.verify(inv);check(sub+'_actual_original_P_wrapper',oldargs.mode=='evaluate' and str(oldargs.checkpoint)==spec['model_root_server'])
  scope=runtime.make_contract(project_root=R,source_root=S,suite=suite,stage='development');check(sub+'_runtime_contract',scope==action['runtime_contract']==runtime.make_contract(project_root=P,source_root=S,suite=suite,stage='development'))
  for root in (R,P):
   for path,sha in runtime.validate_contract(scope,project_root=root,source_root=S).items():read(path,sha)
  assets=runtime.expected_asset_identities(project_root=P,source_root=S,contract=scope,asset_contract=inv.get('downstream_asset_compatibility'))
  check(sub+'_runtime_asset_metadata',assets==js(A/sub/'runtime_asset_metadata_identities.json'))
  closure=js(A/sub/'runtime_dependency_closure.json');pubmap=js(A/'publication_map.json')['files'];pending=[]
  for item in closure:
   path=Path(item['path']);sha=item['sha256']
   if path.is_file():read(path,sha)
   else:
    rel=path.relative_to(P).as_posix();match=[m for m in pubmap if m['canonical_path']==rel and m['sha256']==sha];need(match,'unaccounted runtime input '+rel);read(match[0]['candidate_path'],sha);pending.append(rel)
  ready=js(A/sub/'runtime_readiness_draft.json');check(sub+'_draft_not_authorized',ready['status']=='draft_pending_actual_plan_reviews' and ready['root_review'] is None and ready['independent_review'] is None and ready['active'] is False)
  for role,rr in ready['component_reviews'].items():component=js(rr['path'],rr['sha256']);check(sub+'_'+role+'_existing_component',component['status']=='passed_CPU_review' and component['component']==role and not component.get('blockers'))
  try:wrapper.verify(effective['invocation'],project=P)
  except ValueError as err:check(sub+'_missing_readiness_rejected','Exact path/SHA reference required' in str(err))
  else:raise ValueError('unready outer invocation accepted')
  canonical='results/formal_main_v2/execution/nonLong_action_v1_1220/'+sub+'/plan_independent_review.json'
  pr={'schema':'formal_main_v2','kind':'formal_action_development_plan_independent_review','status':'passed','review_role':'independent','reviewed_by':REVIEWER,'suite':suite,'seed':seed,'stage':'development','execution_version':c.VERSION,'scientific_plan':row['scientific_plan'],'effective_plan':row['effective_plan'],'action_execution_contract':row['execution_contract'],'plan_sha256':effective['plan_sha256'],'scientific_plan_sha256':science['plan_sha256'],'method_ids':methods,'expected_trials':trials,'unique_development_initial_states':100,'checkpoint_identities':selected,'runtime_sources':action['files'],'canonical_review_path':canonical,'source173_R_S_unchanged':True,'inherited_engineering_GPU_evidence':action['GPU_acceptance'],'actual_GPU_runtime_chain_verified':False,'actual_inner_wrapper_P_verified':True,'actual_outer_source_and_plan_P_closure_verified':not pending,'runtime_publication_pending':pending,'positive_full_outer_wrapper_verification_pending_root_readiness':True,'new_P_wrapper_verify_passed':False,'production_chain_complete':True,'production_chain_complete_meaning':'Exact pre-execution metadata/source/scientific/consumer chain is audited. This does not attest a new GPU run or full outer wrapper.verify; root publication, genuine readiness, both actual P verifies and fresh single-use gateway admission remain mandatory.','allowed_stages':['development'],'scientific_settings_changed':False,'final_evaluation_enabled':False,'global_freeze_enabled':False,'O2A_enabled':False,'submission_authorized':False,'new_GPU_seconds':0,'scientific_trials_completed_by_new_runtime':0,'old_success_failure_results_relabelled':False,'historical_results_retained':prep['existing_other_development_jobs'],'prior_job_ids':[],'prior_allocation_cost':[],'resume':False,'transition':None,'state_snapshot':ref(A/'state_at_planning.json'),'author_manifest':ref(A/'manifest.json'),'author_full_delivery':ref(BASE/'delivery_manifest.json'),'reviewer_source':ref(Path(__file__)),'required_before_submission':['Root publish exact static dependency closure and genuine root/independent readiness to R and P.','Root and independent each call exact new P wrapper.verify on the genuine prepared invocation.','Root unchanged gateway rechecks current registry/pending/controller owner/lease, <=8 GPU capacity and exact one-use reservation; no blind retry.'],'blockers':[]}
  proof=dump(sub+'/plan_independent_review.json',pr)
  plans.append({'suite':suite,'seed':seed,'methods':methods,'expected_trials':trials,'scientific_plan':row['scientific_plan'],'effective_plan':row['effective_plan'],'action_execution_contract':row['execution_contract'],'plan_sha256':effective['plan_sha256'],'canonical_path':canonical,'candidate':{'path':proof['path'],'sha256':proof['sha256']}})
 check('immutable_snapshot_not_modified',snapshot==snapshot_before);e.unchanged()
 for path,sha in e.files.items():read(path,sha)
 for path,sha in READS.items():need(digest(path)==sha,'Audit evidence drift '+path)
 dump('checks.json',{'checks':CHECKS,'count':len(CHECKS),'source':ref(Path(__file__))})
 dump('read_evidence_sha256.json',READS)
 dump('independent_index.json',{'schema':'formal_main_v2','kind':'nonLong_development_exact_plan_independent_index','status':'passed_exact_pre_execution_plan_review','reviewer':REVIEWER,'plans':plans,'planned_trials':600,'unique_states_per_suite':100,'new_GPU_seconds':0,'new_trials':0,'new_P_wrapper_verify_passed':False,'submission_authorized':False,'final_release':False,'CPU_wall_seconds':time.perf_counter()-start,'CPU_process_seconds':time.process_time()-cpu,'blockers':[]})
 rows=[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(D.rglob('*')) if p.is_file() and p.name!='manifest.json']
 dump('manifest.json',{'schema':'formal_main_v2','kind':'independent_nonLong_plan_audit_delivery','reviewer':REVIEWER,'files':rows,'state_Git_Slurm_modified':False})
 print(json.dumps({'status':'passed_exact_plans_pending_root_runtime','checks':len(CHECKS),'index':ref(D/'independent_index.json'),'manifest':ref(D/'manifest.json'),'plans':plans}))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  dump('failure_plans_a1.json',{'error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'checks':CHECKS,'new_GPU_seconds':0,'production_modified':False});raise

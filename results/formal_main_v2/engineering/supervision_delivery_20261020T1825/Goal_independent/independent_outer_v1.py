from pathlib import Path
import ast,copy,hashlib,importlib.util,json,re,sys,time,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=Path(__file__).parent;A=R/'.local/goal_prefix58_repair_20261020T1825';C=A/'outer_revision03';O=D/'outer_attempt01';checks=[];neg=[];start=time.process_time()
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(Path(p)),sha256=h(p),bytes=Path(p).stat().st_size)
def write(n,v):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2,ensure_ascii=False);print(file=f)
 return ref(p)
def ck(n,v):
 checks.append(dict(name=n,passed=bool(v)))
 if not v:raise AssertionError(n)
def load(p,name,pin):
 ck('source '+name,h(p)==pin);sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def reject(n,fn):
 try:fn()
 except ValueError as x:neg.append(dict(name=n,error=str(x),error_type=type(x).__name__));ck(n,True);return
 raise AssertionError('accepted negative '+n)
def changed(v):
 if type(v) is bool:return not v
 if type(v) is int:return v+1
 if type(v) is list:return []
 if type(v) is dict:return {**v,'extra':1}
 return 'wrong'
def main():
 O.mkdir(exist_ok=False);e=load(C/'entry.py','g58_ind_outer','da3e094a98104d08735d6da6a180b326f79ae077e710880aa9117b39b911e31f');old=load(A/'outer_revision02/entry.py','g58_ind_old_outer','facf8a46c1efcb4eaef14b4b5b4c70d1d3f4beabf57829696f5b7e99cd02de34')
 package=json.loads((C/'package_manifest.json').read_text());c=json.loads((C/'config.json').read_text());args=(h(C/'config.json'),h(C/'package_manifest.json'),h(C/'entry.py'))
 ck('manifest pin',args[1]=='28b3a3f5a61dd666722915cec86a7d9c4c8d86aaf5b5c35b04f4808aa43ab5d0');ck('config pin',args[0]=='224ca0a8bce551c9d7becf3e13b8e879b5716ffbbf172eb73801dacef8a05265');ck('six exact package members',set(package['files'])==e.PACKAGE_FILES)
 for n,pin in package['files'].items():ck('closure '+n,h(C/Path(n).name)==pin)
 e.validate_config(c)
 for k in c:
  if k=='schema_note':continue
  v=copy.deepcopy(c);v[k]=changed(v[k]);reject('config '+k,lambda v=v:e.validate_config(v))
 auth=dict(schema='formal_main_v2',kind='root_goal_prefix58_single_attempt_authorization',version=e.VERSION,status='approved',reviewed_by='root',stage_key=e.STAGE,config_sha256=args[0],package_manifest_sha256=args[1],entrypoint_sha256=args[2],maximum_gpu_jobs=1,maximum_attempts=1,maximum_wall_seconds=1800,counts_against_8_GPU_slots=True,automatic_retry=False,scientific_release=False,original_goal200_HOLD=True,new_Goal_science_HOLD=True,maximum_trials=58,resources=e.RESOURCES,dispatch_record_path=str(e.DISPATCH),reservation_path=str(e.RESERVATION),root_review={'path':str(e.BASE/'root_readiness.json'),'sha256':'a'*64},independent_review={'path':str(e.BASE/'independent_readiness.json'),'sha256':'b'*64})
 e.validate_authorization(auth,*args)
 for k in auth:
  v=copy.deepcopy(auth);v[k]=changed(v[k]);reject('auth '+k,lambda v=v:e.validate_authorization(v,*args))
 old_bad=copy.deepcopy(auth);old_bad['root_review'].pop('sha256');old.validate_authorization(old_bad,*args);ck('old missing SHA acceptance reproduced',True)
 for role in ('root','independent'):
  for name,val in [('missing',{'path':str(e.BASE/(role+'_readiness.json'))}),('null',{'path':str(e.BASE/(role+'_readiness.json')),'sha256':None}),('badhex',{'path':str(e.BASE/(role+'_readiness.json')),'sha256':'A'*64}),('sealed',{'path':str(e.BASE/'sealed_final.json'),'sha256':'a'*64}),('extra',{**auth[role+'_review'],'extra':1})]:
   v=copy.deepcopy(auth);v[role+'_review']=val;original=Path.open
   def forbidden_io(*a,**kw):raise AssertionError('invalid ref reached target I/O')
   Path.open=forbidden_io
   try:reject('ref zero I/O '+role+' '+name,lambda v=v:e.validate_authorization(v,*args))
   finally:Path.open=original
  review=dict(schema='formal_main_v2',kind='goal_prefix58_single_attempt_CPU_readiness',status='passed',reviewed_by=role,version=e.VERSION,package_manifest_sha256=args[1],config_sha256=args[0],original_chain_preserved=True,observer_gaps_fixed=True,real_GPU_acceptance=False,scientific_release=False);e.check_review(review,role,args[1],args[0])
  for k in review:
   v=copy.deepcopy(review);v[k]=changed(v[k]);reject('readiness '+role+' '+k,lambda v=v,role=role:e.check_review(v,role,args[1],args[0]))
 auth_sha='c'*64;job='7777777';rsha='d'*64;d=dict(schema='formal_main_v2',kind='root_goal_prefix58_held_dispatch',status='held_registered_before_release',stage_key=e.STAGE,job_id=job,authorization={'path':str(e.AUTH),'sha256':auth_sha},request_token='cti-goal-prefix58-v2:'+auth_sha,capacity_limit_all_GPU_modes=8,reserved_slots=1,maximum_attempts=1,new_submissions=1,no_requeue=True,scientific_release=False,resources=e.RESOURCES,occupied_job_ids=[job],state_after_sha256='e'*64,reservation={'path':str(e.RESERVATION),'sha256':rsha})
 res=dict(schema='formal_main_v2',kind='root_goal_prefix58_GPU_slot_reservation',status='approved_for_exact_prefix58',stage_key=e.STAGE,authorization=d['authorization'],reserved_slots=1,capacity_limit_all_GPU_modes=8,maximum_wall_seconds=1800,automatic_retry=False,scientific_release=False);e.validate_dispatch(d,res,auth,auth_sha,job,rsha)
 for k in d:
  v=copy.deepcopy(d);v[k]=changed(v[k]);reject('dispatch '+k,lambda v=v:e.validate_dispatch(v,res,auth,auth_sha,job,rsha))
 for k in res:
  v=copy.deepcopy(res);v[k]=changed(v[k]);reject('reservation '+k,lambda v=v:e.validate_dispatch(d,v,auth,auth_sha,job,rsha))
 for name,ids in [('over8',[job,*map(str,range(8))]),('duplicate',[job,job]),('missing_job',['9'])]:
  v=copy.deepcopy(d);v['occupied_job_ids']=ids;reject('occupied '+name,lambda v=v:e.validate_dispatch(v,res,auth,auth_sha,job,rsha))
 inv,wrapper,ctx,legacy=e.prepare_original();ck('original P invocation exact',h(e.ORIGINAL)==e.ISHA);prefix=json.loads((C/'prefix58.json').read_text())['rows'];proof=e.validate_prefix(inv,legacy,prefix);ck('actual P prefix58/29 verified',proof['original_fixed58_identity_order'] and proof['unique_development_states']==29)
 for name,x in [('swapped',copy.deepcopy(prefix)),('state',copy.deepcopy(prefix))]:
  if name=='swapped':x[0],x[1]=x[1],x[0]
  else:x[-1]['initial_state_sha256']='f'*64
  reject('fixed prefix '+name,lambda x=x:e.validate_prefix(inv,legacy,x))
 a=copy.deepcopy(ctx['args']);ck('future output absent',not e.OUTPUT.exists());a.output=e.OUTPUT/'original_run';a.stop_after=58;a.prepare_only=True
 prepared=legacy.run(a,mode='evaluate',source_root=e.S,source_inventory=Path(inv['source_inventory']),adapter_sha256=e.LSHA,resume=False);ck('unchanged legacy prepare only no GPU/output',prepared['status']=='prepared_only' and prepared['gpu_calls']==0 and prepared['expected_trials']==200 and not e.OUTPUT.exists());write('actual_P_prepare.json',dict(prepared=prepared,prefix=proof,selected_checkpoint_bytes_verified=True,no_execution=True))
 original_output=e.OUTPUT;original_prepare=e.prepare_original;e.OUTPUT=O/'fatal_cpu_fixture'
 try:
  calls=[]
  def no_gpu_prepare():calls.append(1);raise RuntimeError('injected independent pre-inference failure')
  e.prepare_original=no_gpu_prepare;ck('execution harness output private',e.OUTPUT.is_relative_to(D));code=e.execute(c,auth,job,package,dict(auth_sha=auth_sha,manifest_sha=args[1]));complete=json.loads((e.OUTPUT/'outer/completion.json').read_text());ck('fatal error retained/no retry',code==1 and complete['status']=='failed_no_retry' and complete['automatic_retry'] is False and len(calls)==1 and 'injected independent' in complete['errors'][0]['traceback']);reject('one-shot output refuses second run',lambda:e.execute(c,auth,job,package,dict(auth_sha=auth_sha,manifest_sha=args[1])));ck('second attempt did not enter prepare',len(calls)==1)
 finally:e.OUTPUT=original_output;e.prepare_original=original_prepare
 tree=ast.parse((C/'entry.py').read_text());fns={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)};et=ast.unparse(fns['execute']);mt=ast.unparse(fns['main']);nested=next(x for x in ast.walk(fns['execute']) if isinstance(x,ast.FunctionDef) and x.name=='scientific_runner');ck('observer surrounds unchanged run',isinstance(nested.body[-1],ast.With) and 'ad.observer_scope' in ast.unparse(nested.body[-1].items[0].context_expr) and 'return legacy.run' in ast.unparse(nested.body[-1].body[0]));ck('original asset contexts retained','runtime.run_with_asset_contexts(scientific_runner' in et);ck('one-shot output exclusive creation','OUTPUT.mkdir(parents=True, exist_ok=False)' in et);ck('original stage/method nonblocking locks',all(v in mt for v in ["inv['stage_key']","inv['method_ids']",'fcntl.LOCK_EX | fcntl.LOCK_NB','sorted(names)']));ck('no Slurm submission calls',not any(isinstance(x,ast.Call) and any(z in ast.unparse(x.func) for z in ('subprocess','system','popen','sbatch','scontrol','scancel')) for x in ast.walk(tree)));ck('restarts rejected','SLURM_RESTART_COUNT' in mt and 'requeue/restart forbidden' in mt)
 slurm=(C/'run.slurm').read_text();directives=dict(line.removeprefix('#SBATCH --').split('=',1) if '=' in line else (line.removeprefix('#SBATCH --'),True) for line in slurm.splitlines() if line.startswith('#SBATCH --'));ck('exact Slurm hard cap',all(directives.get(k)==v for k,v in {'gres':'gpu:l40:1','time':'00:30:00','no-requeue':True,'exclude':'gpu4020','nodes':'1','ntasks':'1','cpus-per-task':'7','partition':'L40','mem':'64G'}.items()));ck('no arrays/requeue/loop',not any(k.startswith('array') or k=='requeue' for k in directives) and not re.search(r'(?m)^\s*(for|while|until)\s',slurm))
 sources=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text());ck('173 frozen R/S',len(sources['files'])==173 and all(h(base/n)==pin for base in (R,S) for n,pin in sources['files'].items()));cuda=sys.modules.get('torch.cuda');ck('no CUDA initialized',cuda is None or not cuda.__dict__.get('_initialized',False))
 report=dict(schema='formal_main_v2',kind='independent_goal_prefix58_outer_CPU_review',status='passed_CPU_candidate_requires_root_publication_and_dispatch',entrypoint=ref(C/'entry.py'),package_manifest=ref(C/'package_manifest.json'),config=ref(C/'config.json'),checks=checks,passed=len(checks),negative_cases=neg,negative_count=len(neg),original_chain_preserved=True,observer_gaps_fixed=True,review_ref_SHA_gap_closed=True,actual_P_original_metadata_selected_bytes_verified=True,real_GPU_acceptance=False,scientific_release=False,original_Goal200_and_new_science_HOLD=True,production_files_state_Git_Slurm_untouched=True,CPU_seconds=time.process_time()-start,blockers=[],limitations=['Private CPU candidate only; exact package must be published and independently checked before dispatch.','Actual reservation/8-slot accounting/pending-before-sbatch/held-ACK-register-release remains a separately reviewed root submission responsibility.','Inherited reset may swallow application exceptions; actual Slurm <=1800s no-requeue hard limit is authoritative.','Synthetic CPU and passive metadata do not establish native MuJoCo/CUDA passivity or reproduce the anomaly.','Catastrophic I/O or SIGKILL can prevent completion.json; original Slurm stderr and terminal allocation accounting must remain evidence.'])
 rr=write('independent_review.json',report);ready=dict(schema='formal_main_v2',kind='goal_prefix58_single_attempt_CPU_readiness',status='passed',reviewed_by='independent',version=e.VERSION,package_manifest_sha256=args[1],config_sha256=args[0],original_chain_preserved=True,observer_gaps_fixed=True,real_GPU_acceptance=False,scientific_release=False,source_repair_review=ref(D/'attempt02/independent_review.json'),detailed_outer_review=rr,blockers=[]);e.check_review(ready,'independent',args[1],args[0]);print(json.dumps(dict(review=rr,readiness=write('independent_readiness.json',ready),passed=len(checks),negative_count=len(neg),CPU_seconds=report['CPU_seconds'])))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  if not O.exists():O.mkdir()
  write('failure.json',dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),checks=checks,negative_cases=neg,CPU_seconds=time.process_time()-start));raise

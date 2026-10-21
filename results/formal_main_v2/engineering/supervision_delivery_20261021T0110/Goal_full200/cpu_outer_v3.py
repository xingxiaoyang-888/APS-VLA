"""Exact candidate outer tests + actual original metadata reconstruction. No GPU."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys,traceback,types
D=Path(__file__).parent;R=D.parents[1];K=D/'package';P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
O=D/'CPU_outer_v3';O.mkdir(exist_ok=False);checks=[];negative=0;positive=0
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def ck(name,value,detail=None):
 checks.append({'name':name,'passed':bool(value),'detail':detail})
 if not value:raise AssertionError(name)
def fail(name,call):
 global negative
 try:call()
 except (ValueError,KeyError,TypeError,AssertionError):negative+=1;ck(name,True)
 else:ck(name,False)
def load(p,name):
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def expression(fn,variable,kw):
 n=ast.parse((K/'entry.py').read_text());f=next(x for x in n.body if isinstance(x,ast.FunctionDef) and x.name==fn)
 a=next(x for x in f.body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id==variable)
 return eval(compile(ast.Expression(a.value),'<explicit CPU authorization fixture>','eval'),{**entry.__dict__,**kw})
def mutations(name,value,checker,skip=()):
 for key in value:
  if key in skip:continue
  bad=copy.deepcopy(value);bad.pop(key);fail(name+'_missing_'+key,lambda bad=bad:checker(bad))
  bad=copy.deepcopy(value);bad[key]={'CPU_wrong_type':True};fail(name+'_changed_'+key,lambda bad=bad:checker(bad))
def main():
 global entry,positive
 entry=load(K/'entry.py','g200_outer_test');consumer=load(K/'consumer.py','g200_consumer_test');storage=load(K/'storage.py','g200_storage_test')
 cfg=json.loads((K/'config.json').read_bytes());entry.validate_config(cfg);positive+=1
 mutations('config',cfg,entry.validate_config,skip=('schema_note',))
 for key,val in [('scientific_trials_added',False),('maximum_attempts',True)]:
  bad=copy.deepcopy(cfg);bad[key]=val;fail('config_bool_not_int_'+key,lambda:entry.validate_config(bad))
 manifest=json.loads((K/'package_manifest.json').read_bytes());msha=sha(K/'package_manifest.json');csha=sha(K/'config.json');esha=sha(K/'entry.py')
 ck('package_closure_complete',manifest['version']==entry.VERSION and set(manifest['files'])==entry.PACKAGE_FILES and all(sha(K/Path(p).name)==h for p,h in manifest['files'].items()))
 auth=expression('validate_authorization','fixed',dict(config_sha=csha,manifest_sha=msha,entry_sha=esha))
 auth.update(root_review={'path':str(entry.BASE/'root_readiness.json'),'sha256':'a'*64},independent_review={'path':str(entry.BASE/'independent_readiness.json'),'sha256':'b'*64})
 validate=lambda x:entry.validate_authorization(x,csha,msha,esha)
 validate(auth);positive+=1;mutations('authorization',auth,validate)
 for role in ('root','independent'):
  v=expression('check_review','fixed',dict(role=role,manifest_sha=msha,config_sha=csha));entry.check_review(v,role,msha,csha);positive+=1
  mutations(role+'_readiness',v,lambda x,role=role:entry.check_review(x,role,msha,csha))
 authsha='c'*64;job='999999991';rsha='d'*64
 dispatch=expression('validate_dispatch','fixed',dict(a=auth,auth_sha=authsha,job=job,reservation_sha=rsha))
 dispatch.update(occupied_job_ids=[job],state_after_sha256='e'*64,reservation={'path':str(entry.RESERVATION),'sha256':rsha})
 reservation=expression('validate_dispatch','rf',dict(fixed=dispatch))
 vf=lambda x:entry.validate_dispatch(x,reservation,auth,authsha,job,rsha)
 vf(dispatch);positive+=1;mutations('dispatch',dispatch,vf)
 vr=lambda x:entry.validate_dispatch(dispatch,x,auth,authsha,job,rsha);mutations('reservation',reservation,vr)
 for ids in [[job,job],[str(1000+i) for i in range(8)]+[job],[],['999999992']]:
  bad=copy.deepcopy(dispatch);bad['occupied_job_ids']=ids;fail('capacity_ack_'+str(ids),lambda bad=bad:vf(bad))
 jobvalue={'job_id':job,'status':'COMPLETED','exit_code':'0:0','gpus':1,'elapsed_seconds':1,'stage_key':entry.STAGE,'run_root':str(P/consumer.RUN),'suite':'libero_goal','mode':'development'}
 consumer.validate_job(jobvalue,dispatch);positive+=1
 mutations('terminal_job',jobvalue,lambda x:consumer.validate_job(x,dispatch))
 # Existing CPU/full200 and old58 are not actual new full200 terminal evidence.
 fail('private_consumer_cannot_claim_terminal',lambda:consumer.review_terminal(R,{'path':'x.json','sha256':'0'*64}))
 fail('private_entry_cannot_execute',lambda:entry.main(['--authorization',str(entry.AUTH),'--authorization-sha256','0'*64]))
 fail('private_entry_cannot_verify_published',lambda:entry.verify_published(msha))
 fail('duplicate_json_rejected',lambda:consumer.strict(b'{"k":1,"k":2}'))
 fail('nonfinite_json_rejected',lambda:consumer.strict(b'{"k":NaN}'))
 # Only live read is immutable original wrapper/source/checkpoint metadata; no Slurm.
 inv,wrapper,ctx,legacy=entry.prepare_original();proof=entry.validate_prefix(inv,legacy,json.loads((K/'specification.json').read_bytes())['rows'])
 ck('actual_original_full200_panel_rebuilt',proof['unique_development_states']==100 and proof['original_fixed200_identity_order'])
 ck('actual_original_watchdog60',ctx['args'].policy_watchdog_seconds==60.0 and ctx['args'].stop_after is None)
 cap=storage.verify_storage();write(O/'actual_login_storage.json',cap);positive+=1
 ck('storage_distinct_roots_actual',cap['raw']['path']==str(entry.RAW) and cap['local']['path']==str(entry.OUTPUT) and not entry.RAW.exists() and not entry.OUTPUT.exists())
 ck('capture_worstcase_hard_ceiling',storage.MAX_CAPTURE_EVENTS>=200*(1+4+20+2*38)+32)
 ck('gate_worstcase_hard_ceiling',storage.MAX_GATE_EVENTS>=200+7600+60000+32)
 ck('raw_no_dedup_upper',storage.RAW_UPPER_BYTES==storage.MAX_CAPTURE_EVENTS*(2*256*256*3+(3+4+2)*8))
 ck('capacity_margins',storage.MARGIN_BYTES==1<<30 and storage.LOCAL_REQUIRED_BYTES==storage.LOCAL_UPPER_BYTES+(1<<30))
 write(O/'actual_original_preflight.json',{'invocation':entry.ref(entry.ORIGINAL),'wrapper':entry.ref(entry.WRAPPER),'legacy':entry.ref(entry.LEGACY),'identity':proof,'args':{k:(str(v) if isinstance(v,Path) else v) for k,v in vars(ctx['args']).items()},'watchdog_seconds':60.0,'query_bound_derivation':'ceil(300/8)=38, 200 trials -> 7600. warmup does not call policy and is not policy control_steps.','maximum_policy_steps':60000,'maximum_warmup_steps':2000,'actual_GPU_runtime_verified':False})
 # Storage injection is in-memory CPU only, preserves original source file.
 orig=storage.os.statvfs
 try:
  storage.os.statvfs=lambda p:types.SimpleNamespace(f_bavail=1,f_frsize=1)
  fail('capacity_insufficient_refused',lambda:storage.verify_storage())
 finally:storage.os.statvfs=orig
 fail('storage_relative_path_refused',lambda:storage.ancestor(Path('relative')))
 # Complete watched source closure, before and after test; never weights/final payload.
 inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_bytes())['files'];source={}
 for base,label in [(R,'R'),(R/'snapshots/formal_main_v2_run_564be0995e','R_mirror'),(S,'S')]:
  for n,h in inventory.items():
   ck('source173_'+label+'/'+n,sha(base/n)==h);source[label+'/'+n]=h
 for n,h in inv['support_files'].items():
  ck('original_support_R_'+n,sha(R/n)==h);ck('original_support_P_'+n,sha(P/n)==h);source['support/'+n]=h
 contract=json.loads((P/inv['action_execution_contract']['path']).read_bytes())
 for n,h in contract['files'].items():
  ck('contract_closure_R_'+n,sha(R/n)==h);ck('contract_closure_P_'+n,sha(P/n)==h);source['action_contract/'+n]=h
 for n,h in consumer.PINS.items():ck('original_consumer_source_'+n,sha(R/n)==h)
 write(O/'source_closure.json',source)
 ck('no_CUDA_initialization',not getattr(sys.modules.get('torch.cuda'),'_initialized',False))
 return {'status':'passed_CPU_outer_contract_and_actual_original_metadata','checks':checks,'negative_cases':negative,'positive_cases':positive,'source_closure_sha256':sha(O/'source_closure.json'),'package_manifest_sha256':msha,'actual_new_P_published':False,'actual_new_GPU_runtime_verified':False,'native_root_dispatch_not_in_candidate':True,'old200_HOLD':True,'GPU_submissions':0,'Slurm_queries':0,'scientific_trials_added':0,'final_release':False}
try:r=main()
except BaseException as e:
 r={'status':'failed','error':str(e),'type':type(e).__name__,'traceback':traceback.format_exc(),'checks':checks,'negative_cases':negative,'positive_cases':positive};write(O/'report.json',r);print(json.dumps({'status':r['status'],'error':str(e)}));raise
write(O/'report.json',r);print(json.dumps({'status':r['status'],'checks':len(checks),'negative':negative,'positive':positive}))

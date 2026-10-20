from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,sys,time,traceback
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_prefix58_repair_20261020T1825';V=D/'outer_revision02';O=D/'outer_CPU_attempt01';O.mkdir(exist_ok=False);start=time.process_time();checks=[];neg=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,x):
 p=O/n;p.write_text(json.dumps(x,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n');return dict(path=str(p.relative_to(R)),sha256=h(p))
def ck(n,ok):
 if not ok:raise AssertionError(n)
 checks.append(n)
def rejects(n,fn,contains=None):
 try:fn()
 except (ValueError,KeyError,TypeError) as e:
  if contains and contains not in str(e):raise AssertionError((n,str(e)))
  neg.append(dict(name=n,error_type=type(e).__name__,message=str(e)));return
 raise AssertionError('accepted '+n)
def main():
 pin='facf8a46c1efcb4eaef14b4b5b4c70d1d3f4beabf57829696f5b7e99cd02de34';ck('entry pin',h(V/'entry.py')==pin);spec=importlib.util.spec_from_file_location('outer_cpu_candidate',V/'entry.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);ck('import alone does not initialize GPU',not sys.modules.get('torch.cuda') or not getattr(sys.modules['torch.cuda'],'_initialized',False))
 package=json.loads((V/'package_manifest.json').read_text());ck('exact six-file package',set(package['files'])==m.PACKAGE_FILES and all(h(V/Path(k).name)==v for k,v in package['files'].items()));config=json.loads((V/'config.json').read_text());m.validate_config(config);checks.append('exact config accepted');manifest_sha=h(V/'package_manifest.json');config_sha=h(V/'config.json')
 for key,bad in [('maximum_trials',59),('tokens',128),('method_ids',['A256_seed17']),('automatic_retry',True),('scientific_trials_added',58),('historical_actions_forced',True),('final_evaluation_enabled',True),('original200_HOLD',False)]:
  c=copy.deepcopy(config);c[key]=bad;rejects('scope '+key,lambda c=c:m.validate_config(c))
 fixed={'schema':'formal_main_v2','kind':'root_goal_prefix58_single_attempt_authorization','version':m.VERSION,'status':'approved','reviewed_by':'root','stage_key':m.STAGE,'config_sha256':config_sha,'package_manifest_sha256':manifest_sha,'entrypoint_sha256':pin,'maximum_gpu_jobs':1,'maximum_attempts':1,'maximum_wall_seconds':1800,'counts_against_8_GPU_slots':True,'automatic_retry':False,'scientific_release':False,'original_goal200_HOLD':True,'new_Goal_science_HOLD':True,'maximum_trials':58,'resources':m.RESOURCES,'dispatch_record_path':str(m.DISPATCH),'reservation_path':str(m.RESERVATION),'root_review':{'path':str(m.BASE/'root_readiness.json'),'sha256':'1'*64},'independent_review':{'path':str(m.BASE/'independent_readiness.json'),'sha256':'2'*64}}
 m.validate_authorization(fixed,config_sha,manifest_sha,pin);checks.append('synthetic in-memory authorization positive')
 for key,bad in [('stage_key','goal_t0_probe_20261020T1418'),('maximum_attempts',2),('maximum_wall_seconds',1801),('counts_against_8_GPU_slots',False),('package_manifest_sha256','0'*64),('entrypoint_sha256','0'*64),('scientific_release',True),('automatic_retry',True),('new_Goal_science_HOLD',False)]:
  a=copy.deepcopy(fixed);a[key]=bad;rejects('auth '+key,lambda a=a:m.validate_authorization(a,config_sha,manifest_sha,pin))
 a=copy.deepcopy(fixed);a['independent_review']=a['root_review'];rejects('root-independent distinction',lambda:m.validate_authorization(a,config_sha,manifest_sha,pin))
 auth_sha='3'*64;reservation_sha='4'*64;job='99999999';ar={'path':str(m.AUTH),'sha256':auth_sha}
 res={'schema':'formal_main_v2','kind':'root_goal_prefix58_GPU_slot_reservation','status':'approved_for_exact_prefix58','stage_key':m.STAGE,'authorization':ar,'reserved_slots':1,'capacity_limit_all_GPU_modes':8,'maximum_wall_seconds':1800,'automatic_retry':False,'scientific_release':False}
 dispatch={'schema':'formal_main_v2','kind':'root_goal_prefix58_held_dispatch','status':'held_registered_before_release','stage_key':m.STAGE,'job_id':job,'authorization':ar,'request_token':'cti-goal-prefix58-v2:'+auth_sha,'capacity_limit_all_GPU_modes':8,'reserved_slots':1,'maximum_attempts':1,'new_submissions':1,'no_requeue':True,'scientific_release':False,'resources':m.RESOURCES,'occupied_job_ids':[job],'state_after_sha256':'5'*64,'reservation':{'path':str(m.RESERVATION),'sha256':reservation_sha}}
 m.validate_dispatch(dispatch,res,fixed,auth_sha,job,reservation_sha);checks.append('synthetic in-memory held dispatch positive')
 for key,bad in [('request_token','old-token'),('job_id','88888888'),('new_submissions',2),('occupied_job_ids',[job,job]),('occupied_job_ids',[job]+[str(i) for i in range(8)]),('state_after_sha256',None),('no_requeue',False),('status','submitted_unknown')]:
  q=copy.deepcopy(dispatch);q[key]=bad;rejects('dispatch '+key,lambda q=q:m.validate_dispatch(q,res,fixed,auth_sha,job,reservation_sha))
 q=copy.deepcopy(res);q['stage_key']='goal_t0_probe_20261020T1418';rejects('old reservation',lambda:m.validate_dispatch(dispatch,q,fixed,auth_sha,job,reservation_sha))
 review={'schema':'formal_main_v2','kind':'goal_prefix58_single_attempt_CPU_readiness','status':'passed','reviewed_by':'root','version':m.VERSION,'package_manifest_sha256':manifest_sha,'config_sha256':config_sha,'original_chain_preserved':True,'observer_gaps_fixed':True,'real_GPU_acceptance':False,'scientific_release':False};m.check_review(review,'root',manifest_sha,config_sha);checks.append('typed CPU-only review accepted')
 for key,bad in [('real_GPU_acceptance',True),('observer_gaps_fixed',False),('reviewed_by','independent'),('scientific_release',True),('status','pending')]:
  q=copy.deepcopy(review);q[key]=bad;rejects('readiness '+key,lambda q=q:m.check_review(q,'root',manifest_sha,config_sha))
 rejects('private execute rejected before I/O',lambda:m.main(['--authorization',str(m.AUTH),'--authorization-sha256','0'*64]),'only exact published')
 # Extract the identical nested journal function into a CPU-only private namespace.
 tree=ast.parse((V/'entry.py').read_text());node=next(x for x in ast.walk(tree) if isinstance(x,ast.FunctionDef) and x.name=='emit');ns=dict(events=[],eventpath=O/'synthetic_outer_events.jsonl',job=job,json=json,datetime=datetime,timezone=timezone,os=os,require=m.require);exec(compile(ast.Module(body=[node],type_ignores=[]),'<exact_outer_emit_CPU>','exec'),ns)
 ns['emit']('prefix_observer_scope_exit',bindings_intact=True,bindings_restored=True,runner_raised=False,scientific_trials_added=0);ck('existing identical zero field journal works',len(ns['events'])==1 and ns['events'][0]['scientific_trials_added']==0);rejects('conflicting science field rejected',lambda:ns['emit']('bad',scientific_trials_added=58),'collides');ck('rejected event not written',len((O/'synthetic_outer_events.jsonl').read_text().splitlines())==1)
 # Real P wrapper/source/checkpoint verification is metadata only; no main/execute.
 inv,wrapper,ctx,legacy=m.prepare_original();checks.append('real P original wrapper and checkpoint bytes passed');prefix=json.loads((V/'prefix58.json').read_text())['rows'];proof=m.validate_prefix(inv,legacy,prefix);ck('real fixed58 identity',proof['original_fixed58_identity_order']);bad=copy.deepcopy(prefix);bad[0],bad[1]=bad[1],bad[0];rejects('changed prefix order',lambda:m.validate_prefix(inv,legacy,bad),'identity/order')
 a=copy.deepcopy(ctx['args']);original=copy.deepcopy(vars(a));a.output=O/'never_created_original_output';a.stop_after=58;a.prepare_only=True
 result=legacy.run(a,mode='evaluate',source_root=m.S,source_inventory=Path(inv['source_inventory']),adapter_sha256=m.LSHA,resume=False);ck('actual legacy CPU prepare creates no output',not a.output.exists());write('real_P_original_prepare_result.json',result);ck('live original namespace preserved',vars(ctx['args'])==original)
 ck('no CUDA initialized after actual P prepare',not sys.modules.get('torch.cuda') or not getattr(sys.modules['torch.cuda'],'_initialized',False));ck('no engineering production output created',not m.OUTPUT.exists())
 # No policy/inference is called in this test. Fixed original functions are used.
 calls=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)];ck('original run chain retained',all(x in calls for x in ['verify','run','source_imports','expected_asset_identities','run_with_asset_contexts','verify_runtime_events','observer_scope','finish']));ck('no submit or scheduler functions',not any(isinstance(n,ast.Name) and n.id in ('subprocess','sbatch','scancel') for n in ast.walk(tree)))
 pins=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text())['files'];ck('173 frozen control and snapshot unchanged',len(pins)==173 and all(h(base/path)==pin for base in (R,m.S) for path,pin in pins.items()));write('real_P_identity_proof.json',proof)
 report=dict(schema='formal_main_v2',kind='goal_prefix58_outer_author_CPU',status='passed_CPU_metadata_only',checks=checks,negative_cases=neg,passed=len(checks),negative_count=len(neg),entrypoint_sha256=pin,package_manifest_sha256=manifest_sha,config_sha256=config_sha,GPU_calls=0,Slurm_submissions=0,production_state_written=False,production_output_created=False,real_GPU_readiness=False,original200_HOLD=True,new_Goal_science_HOLD=True,CPU_seconds=time.process_time()-start,limits='Actual P original wrapper and legacy prepare_only plus in-memory authorization negatives; not a native simulator/GPU run, not root or independent authorization.')
 print(json.dumps(dict(report=write('CPU_review.json',report),passed=len(checks),negative_count=len(neg),CPU_seconds=report['CPU_seconds'])))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  print(json.dumps(write('failure.json',dict(error=str(e),error_type=type(e).__name__,traceback=traceback.format_exc(),checks=checks,negative_cases=neg,CPU_seconds=time.process_time()-start,GPU_calls=0))));raise

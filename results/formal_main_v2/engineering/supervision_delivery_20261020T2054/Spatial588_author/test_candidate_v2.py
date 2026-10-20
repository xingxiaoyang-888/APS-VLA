from pathlib import Path
from types import SimpleNamespace,ModuleType
from datetime import datetime,timezone
import ast,copy,hashlib,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent
CONTROL='ab25204394179aef1affcf0d61a88d1d7856f6a22c418aff99d9687840d2c2ae'
raw=(D/'control.py').read_bytes();assert hashlib.sha256(raw).hexdigest()==CONTROL
c=ModuleType('_spatial588_author_tests');c.__file__=str(D/'control.py');exec(compile(raw,str(D/'control.py'),'exec'),c.__dict__)
sys.path.insert(0,str(R/'src'));helper=c._original(c.HELPER);state=json.loads((R/'results/experiment_supervisor/state.json').read_text());before=hashlib.sha256((R/'results/experiment_supervisor/state.json').read_bytes()).hexdigest()
checks=[]
def ok(name,fn):
 fn();checks.append({'name':name,'passed':True})
def reject(name,fn):
 try:fn()
 except (ValueError,AssertionError,FileNotFoundError,KeyError):checks.append({'name':name,'passed':True,'expected_rejection':True});return
 raise AssertionError('unexpected acceptance: '+name)
def put(n,v):
 p=D/n
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,sort_keys=True);f.write('\n')
 return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
try:
 proof=c.verify_history(helper.Evidence(R),state['registered_jobs']);ok('actual_history_whole_chain_prefix12_and_failed2_seconds',lambda:None)
 put('history_proof.json',proof);put('repair_record_proposal.json',c.repair_proposal())
 for jid in ['3022743','3042529']:
  for key,value in [('status','RUNNING'),('exit_code','0:0' if jid=='3042529' else '1:0'),('elapsed_seconds',0),('gpus',2),('source_sha256','0'*64),('invocation_sha256','0'*64),('execution_manifest_sha256','0'*64),('method_ids',['dense']),('run_root','/tmp/foreign'),('resume',not (jid=='3042529'))]:
   jobs=copy.deepcopy(state['registered_jobs']);next(j for j in jobs if j['job_id']==jid)[key]=value
   reject('prior_'+jid+'_'+key,lambda jobs=jobs:c.verify_history(helper.Evidence(R),jobs))
  jobs=[j for j in state['registered_jobs'] if j['job_id']!=jid]
  reject('missing_prior_'+jid,lambda jobs=jobs:c.verify_history(helper.Evidence(R),jobs))
  jobs=copy.deepcopy(state['registered_jobs']);jobs.append(copy.deepcopy(next(j for j in jobs if j['job_id']==jid)))
  reject('duplicate_prior_'+jid,lambda jobs=jobs:c.verify_history(helper.Evidence(R),jobs))
 jobs=copy.deepcopy(state['registered_jobs']);extra=copy.deepcopy(next(j for j in jobs if j['job_id']=='3042529'));extra['job_id']='999999998';extra['status']='UNKNOWN';jobs.append(extra)
 reject('unknown_overlapping_third_attempt',lambda:c.verify_history(helper.Evidence(R),jobs))
 p=c.policy();args=SimpleNamespace(stage='development',source_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',execution_manifest=p['manifest']['path'],output_relative=None,freeze_directory=None,profile_panel=None,prior_review=p['prefix_review']['path'],collection_review=None,repair_record=c.REPAIR,resume=True,stop_after=None)
 ok('exact_argument_scope',lambda:c.scope_args(args))
 for k,v in [('stage','final'),('stage','collect'),('stage','full'),('stage','components'),('resume',False),('stop_after',12),('execution_manifest','foreign.json'),('prior_review','results/formal_main_v2/downstream_reviews/3042529.json'),('repair_record',None),('output_relative','other'),('profile_panel','sealed_final.json')]:
  a=copy.deepcopy(args);setattr(a,k,v);reject('scope_'+k+'_'+str(v),lambda a=a:c.scope_args(a))
 _,planner=c.control_modules();reject('real_planner_missing_separately_root_reviewed_repair',lambda:planner.plan(args,state,project=R))
 planned=copy.deepcopy(state);planned['pending_submission']={'job_id':'uncertain'};reject('unresolved_pending_plan',lambda:planner.plan(args,planned,project=R))
 reject('no_explicit_helper_substitution',lambda:planner.plan(args,state,project=R,helper=helper))
 reject('no_nonserver_root',lambda:planner.plan(args,state,project=Path('/tmp')))
 # AST derivations must change only the intended original functions. No
 # trajectory, action, environment, checkpoint or validation settings change.
 original=(R/c.PLANNER).read_text();changed=original.replace('if review["job_id"] != prior[-1]["job_id"]:','if review["job_id"] != "3022743":',1).replace('or set(ledger["invocation_job_ids"]) != {j["job_id"] for j in prior}','or set(ledger["invocation_job_ids"]) != {"3022743"}',1)
 a={n.name:ast.dump(n) for n in ast.parse(original).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};b={n.name:ast.dump(n) for n in ast.parse(changed).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 assert set(a)==set(b) and [k for k in a if a[k]!=b[k]]==['prior_contract'];checks.append({'name':'planner_AST_only_prior_contract','passed':True})
 for n,h in p['original_sources'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h
 inv=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text());assert len(inv['files'])==173
 for n,h in inv['files'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h
 checks.append({'name':'all173_frozen_sources_unchanged','passed':True})
 after=hashlib.sha256((R/'results/experiment_supervisor/state.json').read_bytes()).hexdigest();assert before==after
 checks.append({'name':'supervisor_state_unchanged','passed':True})
 report={'schema':'formal_main_v2','kind':'formal_predispatch_history_author_CPU_test','status':'passed_author_CPU_tests_not_production_admission','control_sha256':CONTROL,'utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'history_control_sources':c.closure(),'typed_predispatch_history':proof,'state_before':before,'state_after':after,'new_GPU_submissions':0,'new_scientific_trials':0,'production_chain_complete':False,'pending_root_integration_and_independent_review':True,'full_runtime_P_verify_done':False,'weights_read':False,'sealed_values_read':False}
 print(json.dumps(put('author_CPU_tests.json',report)))
except BaseException as exc:
 put('author_CPU_failure_v1.json',{'error':repr(exc),'traceback':traceback.format_exc(),'checks':checks});raise

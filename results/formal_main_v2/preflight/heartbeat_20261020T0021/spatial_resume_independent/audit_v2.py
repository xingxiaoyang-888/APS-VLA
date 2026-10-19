from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,importlib.util,json,os,sys,time,traceback
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/spatial_resume_audit_1621';C=R/'.local/spatial_resume_1621'
PIN='39136af1b5d3086ffb304f4c156909726b6a0dd57d5420de655c15a638aadf49'
before=(C/'prepare.py').read_bytes();assert hashlib.sha256(before).hexdigest()==PIN
sp=importlib.util.spec_from_file_location('ind_spatial1621',C/'prepare.py');m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m
exec(compile(before,str(C/'prepare.py'),'exec'),m.__dict__)
extra={};checks=[]
def read(path,pin=None):
 raw=path.read_bytes();h=hashlib.sha256(raw).hexdigest()
 if pin is not None:assert h==pin,str(path)
 extra[str(path)]=h;return raw
def check(name,ok):
 assert ok,name
 checks.append({'case':name,'passed':True})
def jsonread(p,pin=None):return json.loads(read(p,pin))
def reject(name,fun):
 try:fun()
 except ValueError:checks.append({'case':name,'passed':True,'outcome':'rejected'})
 else:raise AssertionError(name+' unexpectedly accepted')
start=time.monotonic();out={'schema':'formal_main_v2','kind':'independent_spatial_before_child_readonly_and_CPU_check','source_sha256':PIN,'checks':checks,'started_utc':datetime.now(timezone.utc).isoformat(),'Slurm_queries':0,'GPU_runs':0,'production_writes':False}
try:
 e,facts,context=m.inspect_actual()
 out['actual_facts']=facts
 old=m.probe_old_planner(context);out['original_planner_rejection']=old
 check('actual original planner latest-allocation rejection with full registry',old['status']=='rejected_original_unchanged_planner' and old['full_registry_supplied'] is True and old['error']=='Only the newest terminal attempt can authorize continuation')
 candidate=m.make_candidate(facts,context);out['candidate']=candidate
 expected=jsonread(C/'attempt03_candidate.json','b4d75649fd6bb29e065b22840a729a8eae416fff3b99d4f36f0ec25661ed344d')
 check('candidate exact equality to frozen author proposal',candidate==expected)
 check('allocation history exactly both jobs and395GPU seconds',candidate['prior_job_ids']==['3022743','3042529'] and candidate['prior_allocation_GPU_seconds']==395 and candidate['actual_ledger_contributors']==['3022743'] and candidate['failed_allocations_without_ledger']==['3042529'])
 check('non-executable without new authorization or readiness',candidate['status']=='prepared_only_not_executable' and candidate['submission_authorized'] is False and candidate['production_readiness'] is False and candidate['consumed_authorization']['reusable'] is False and candidate['required_new_authorization']['not_created'] is True)
 check('exact attempt03 same persistent output, fixed methods argv resources',candidate['invocation_relative_proposed']==m.INV3 and candidate['output_relative']==m.RUN and candidate['resume'] is True and candidate['methods']==m.METHODS and candidate['original_scientific_argv']==context['inv']['argv'] and candidate['resources']==context['science']['resources'])
 raw=read(R/m.RUN/'trials.jsonl',m.PREFIX_SHA);praw=read(P/m.RUN/'trials.jsonl',m.PREFIX_SHA)
 rows=[json.loads(x) for x in raw.splitlines()];terms=[x for x in rows if x['event']=='result']
 check('actual raw prefix R/P equal25 rows12terminal one contributor',raw==praw and len(raw)==592887 and len(rows)==25 and len(terms)==12 and len({x['trial_id'] for x in terms})==12 and all(x['status']=='completed' for x in terms) and [x['slurm_job_id'] for x in rows if x['event']=='invocation']==['3022743'])
 receipt=jsonread(R/'results/formal_main_v2/job_receipts/3042529.json',m.PINS['results/formal_main_v2/job_receipts/3042529.json'])
 diag=jsonread(R/m.DIAG/'independent_diagnosis.json',m.PINS[m.DIAG+'independent_diagnosis.json'])
 reproduction=jsonread(R/diag['actual_reproduction']['path'],diag['actual_reproduction']['sha256'])
 wrapper=read(R/m.WRAPPER,m.PINS[m.WRAPPER]).decode()
 tree=ast.parse(wrapper);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 vc=[n.lineno for n in ast.walk(main) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='verify']
 child=[n.lineno for n in ast.walk(main) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='subprocess' and n.func.attr=='run']
 check('actual parent verify precedes new child invocation',len(vc)==len(child)==1 and vc[0]<child[0])
 check('specific before-child compound evidence',receipt['error_type']=='ValueError' and receipt['error']=='Noncanonical or missing evidence' and receipt['adapter_artifacts']==[] and receipt['adapter_receipts']==[] and receipt['action_execution_artifacts']==[] and diag['child_started'] is False and diag['failed_read_reference']=={'path':m.PRIOR,'sha256':m.PINS[m.PRIOR]} and not (P/'results/formal_main_v2/action_execution_invocations/3042529').exists())
 out['before_child_basis']={'parent_verify_line':vc[0],'new_child_call_line':child[0],'error':receipt['error'],'actual_diagnostic_reproduction':diag['actual_reproduction'],'action_and_adapter_artifacts_empty':True,'action_directory_absent':True,'original_prefix_unchanged':True,'original_scientific_wrapper_executed_field_is_not_a_child_start_flag':True}
 out['actual_prior_diagnostic_reproduction']=reproduction
 check('exact prior review indirect read in230-item closure',len(context['publication'])==230 and m.PRIOR in context['publication'] and context['publication'][m.PRIOR]['source_relative']==m.PRIOR)
 out['publication_closure']=context['publication']
 for name,key,value in [
 ('omitted_failed_allocation','allocation_job_ids',['3022743']),
 ('omitted_failed_cost','all_prior_GPU_seconds',393),
 ('fake_failed_ledger_contributor','ledger_contributors',['3022743','3042529']),
 ('child_started','child_started',True),
 ('new_action_artifact','action_artifact_count',1),
 ('changed_prefix','prefix_sha256','0'*64),
 ('new_method_or_order','methods',list(reversed(m.METHODS))),
 ('executable_claim','submission_enabled',True),
 ('attempt03_already_present','invocation03_absent_R_P',False)]:
  changed=copy.deepcopy(facts);changed[key]=value
  reject(name,lambda changed=changed:m.validate_facts(changed))
 real_stable=m.stable
 def forbidden_io(*args,**kw):raise AssertionError('forbidden path reached filesystem')
 m.stable=forbidden_io
 try:
  for path in ['../state.json','results/sealed_final.json','configs/manifests/formal_main_v2/libero_spatial/initial_states/sealed_final.json','results/x/checkpoint.pt']:
   reject('lexical reject beforeIO '+path,lambda path=path:m.Evidence().read(path))
 finally:m.stable=real_stable
 # Full unchanged() covers both R/S frozen173 and original runtime closure.
 e.unchanged();check('candidate source unchanged after actual checks',read(C/'prepare.py',PIN)==before)
 out.update(status='passed_independent_checks_submission_remains_blocked',duration_seconds=time.monotonic()-start,actual_wrapper_verify_P=True,original_planner_unmodified=True,registry_filtered=False,forged_legacy_review=False,ledger_rows_added=0,source_R_S_173_rehashed=True,frozen_runtime7_unchanged=True,attempt03_created=False,submission_ready=False)
 out['read_evidence_sha256']={**{p:v['sha256'] for p,v in e.files.items()},**extra}
except BaseException as exc:
 out.update(status='failed_independent_check',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc(),duration_seconds=time.monotonic()-start,read_evidence_sha256=extra)
raw=(json.dumps(out,sort_keys=True,indent=2)+chr(10)).encode();target=D/'checks.json'
with target.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
print(json.dumps({'status':out['status'],'checks':len(checks),'duration':out['duration_seconds'],'sha256':hashlib.sha256(raw).hexdigest(),'path':str(target),'error':out.get('error')}))
if out['status'].startswith('failed'):sys.exit(1)

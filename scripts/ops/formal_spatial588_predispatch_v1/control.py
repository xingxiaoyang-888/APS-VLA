"""Exact Spatial600 history extension: one real12-trial prefix plus one no-child failure.

Control/audit only. No scheduler, model, simulator, state mutation or GPU entry.
Original scientific runtime and 173 frozen files are untouched. The failed
allocation remains a failed allocation and never receives a ledger invocation.
"""
from pathlib import Path
from types import ModuleType, SimpleNamespace
import ast,copy,hashlib,json,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
PRIVATE='.local/spatial588_integration_20261020T2156/phase2_v2'
CANONICAL='scripts/ops/formal_spatial588_predispatch_v1'
BASE=Path(__file__).resolve().parent
POLICY_SHA='7341ba48d9c1a70557f8a883af40ac13b34caabe407fac2b9947fefc08fc9e87'
REPAIR='results/formal_main_v2/execution/spatial588_pre_dispatch_v1/repair_record.json'
HISTORY_REVIEW='results/formal_main_v2/engineering/supervision_delivery_20261020T2156/Spatial_phase2_independent/independent_history_review.json'
PLANNER='scripts/ops/formal_downstream_supervisor.py'
OLD_REVIEW='scripts/review_formal_downstream.py'
HELPER='scripts/formal_execution_manifests.py'
REVIEWER='scripts/ops/formal_action_deployment_v1/reviewer.py'
CONSUMER='scripts/ops/formal_action_deployment_v1/consumer.py'
VERSION='formal-spatial588-predispatch-history-v1'

def require(v,m):
 if not v:raise ValueError(VERSION+': '+m)
def sha(b):return hashlib.sha256(b).hexdigest()
def sig(d):return sha(json.dumps(d,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode())
def safe(rel):
 p=R/rel;require(isinstance(rel,str) and not Path(rel).is_absolute() and '..' not in Path(rel).parts and p.relative_to(R).as_posix()==rel,'canonical R path required')
 require(not any(x.is_symlink() for x in (p,*p.parents)),'symlink forbidden');return p

def policy():
 require(BASE.relative_to(R).as_posix() in (PRIVATE,CANONICAL),'exact candidate/control location')
 raw=(BASE/'policy.json').read_bytes();require(sha(raw)==POLICY_SHA,'policy bytes differ')
 p=json.loads(raw);require(p['version']==VERSION and p['all_prior_job_ids']==['3022743','3042529'] and p['executed_prior_job_ids']==['3022743'] and p['predispatch_failed_job_ids']==['3042529'],'fixed typed attempt split')
 p['anchors']={(BASE/k[len('@bundle/'):]).relative_to(R).as_posix() if k.startswith('@bundle/') else k:v for k,v in p['anchors'].items()}
 p['raw_failure_snapshot']['path']=(BASE/'raw_failure_snapshot.json').relative_to(R).as_posix()
 return p

def closure():
 p=policy();files=dict(p['original_sources'])
 files[(BASE/'policy.json').relative_to(R).as_posix()]=POLICY_SHA
 files[Path(__file__).resolve().relative_to(R).as_posix()]=sha(Path(__file__).read_bytes())
 files[(BASE/'compatibility.py').relative_to(R).as_posix()]=sha((BASE/'compatibility.py').read_bytes())
 for n,h in p['compatibility_bundle_files'].items():files[(BASE/n).relative_to(R).as_posix()]=h
 for n,h in files.items():require(sha(safe(n).read_bytes())==h,'source closure differs: '+n)
 return files

class Evidence:
 def __init__(self,original):
  self.original=original;self.project=Path(getattr(original,'project',getattr(original,'root',''))).resolve();require(self.project==R,'exact server control evidence')
 def path(self,n):return safe(n)
 def watch(self,n):
  n=Path(n).relative_to(R).as_posix() if Path(n).is_absolute() else n
  return self.original.watch(n)
 def read(self,n):self.watch(n);return self.original.read(n)
 def unchanged(self):return self.original.unchanged()

def _watch(e,n,h):require(e.watch(n)==h,'evidence SHA differs: '+n)
def _normalized_job(j):
 x=copy.deepcopy(j);raw=x.pop('raw_status',None);require(raw in (None,x.get('status')),'raw/normalized status conflict');return x

def descriptor():
 p=policy()
 return {'schema':'formal_main_v2','kind':'typed_predispatch_attempt_history','version':VERSION,'scope':{'suite':p['suite'],'stage':'development','stage_key':p['stage_key'],'method_ids':p['method_ids'],'expected_trials':600,'retained_prefix_trials':12,'remaining_trials':588},'all_prior_job_ids':['3022743','3042529'],'executed_prior_job_ids':['3022743'],'predispatch_failed_job_ids':['3042529'],'prefix_review':p['prefix_review'],'prefix_ledger':p['prefix_ledger'],'raw_failure_snapshot':p['raw_failure_snapshot'],'prior_GPU_seconds':395,'predispatch_failure_GPU_seconds':2,'ordinary_failure_review_fabricated':False,'failed_ledger_invocation_fabricated':False,'scientific_settings_changed':False,'control_sources':closure()}

def _ledger_prefix(e,p,*,postrun):
 rel=p['prefix_ledger']['path'];e.watch(rel);path=e.path(rel);count=p['prefix_ledger']['bytes'];size=path.stat().st_size
 require(size>=count and (postrun or size==count),'original ledger prefix size differs')
 with path.open('rb') as f:raw=f.read(count)
 require(len(raw)==count and sha(raw)==p['prefix_ledger']['sha256'] and raw.endswith(b'\n'),'exact original prefix bytes differ')
 rows=[json.loads(x) for x in raw.splitlines()]
 require(len(rows)==25 and [str(x.get('slurm_job_id')) for x in rows if x.get('event')=='invocation']==['3022743'],'only actual prefix invocation exists')
 require(sum(x.get('event')=='start' for x in rows)==12 and sum(x.get('event')=='result' and x.get('status')=='completed' for x in rows)==12,'complete12 prefix rows required')
 require(all(x.get('event') in ('invocation','start','result') for x in rows),'unknown original prefix event')
 return rows

def verify_history(evidence,jobs,*,postrun=False,current_job=None):
 e=Evidence(evidence);p=policy();require(type(jobs)is list,'job list required')
 for n,h in closure().items():_watch(e,n,h)
 for n,h in p['anchors'].items():_watch(e,n,h)
 ids=[j.get('job_id') for j in jobs];require(len(ids)==len(set(ids)),'duplicate registered allocation')
 prior=[]
 for expected in p['prior_jobs']:
  got=[j for j in jobs if j.get('job_id')==expected['job_id']];require(len(got)==1 and _normalized_job(got[0])==expected,'real prior allocation identity/cost differs')
  prior.append(got[0])
 overlaps=[j for j in jobs if j.get('suite')=='libero_spatial' and j.get('mode')=='development' and (not j.get('method_ids') or set(j['method_ids']) & set(p['method_ids']))]
 want=['3022743','3042529']
 if postrun:
  require(type(current_job)is dict and current_job.get('job_id') not in want,'actual new terminal allocation required')
  require(current_job in jobs and current_job.get('status')=='COMPLETED' and current_job.get('exit_code')=='0:0','new allocation must complete before terminal proof')
  want.append(current_job['job_id'])
 else:require(current_job is None,'planning cannot name new allocation')
 require(sorted([j['job_id'] for j in overlaps],key=int)==sorted(want,key=int),'new/unknown/overlapping attempt blocks exact once-only recovery')
 require(all(j.get('stage_key')==p['stage_key'] and j.get('method_ids')==p['method_ids'] and j.get('run_root')==p['run_root'] for j in overlaps),'stage/method/output overlap differs')
 inv0=e.read(prior[0]['invocation']);inv1=e.read(prior[1]['invocation'])
 require(inv0['prior_job_ids']==[] and inv1['prior_job_ids']==['3022743'] and inv1['prior_review']==p['prefix_review']['path'],'historical invocation chain differs')
 for j,inv in zip(prior,[inv0,inv1]):
  require(inv['source_sha256']==p['source_sha256'] and inv['execution_manifest_sha256']==p['manifest']['sha256'] and inv['method_ids']==p['method_ids'] and inv['run_root']==p['run_root'],'historical scientific identity differs')
  require(e.watch(j['invocation'])==j['invocation_sha256'],'prior invocation SHA differs')
 receipt=e.read('results/formal_main_v2/job_receipts/3042529.json')
 expected={'job_id':'3042529','status':'failed','exit_code':1,'error':'Noncanonical or missing evidence','error_type':'ValueError','original_scientific_wrapper_executed':False,'stage_completed_claimed':False,'adapter_artifacts':[],'adapter_receipts':[],'action_execution_artifacts':[],'invocation_sha256':prior[1]['invocation_sha256'],'run_root':p['run_root'],'stage_key':p['stage_key'],'source_sha256':p['source_sha256'],'adapter_sha256':p['adapter_sha256']}
 require(all(receipt.get(k)==v for k,v in expected.items()),'not the exact no-child pre-dispatch failure')
 require(type(receipt.get('wall_seconds')) in (int,float) and 0<=receipt['wall_seconds']<=3,'failure wall exceeds registered allocation')
 ack_path='results/formal_main_v2/downstream_gateway/55f6c06a83847f8f60850309cdade6991cc70ba3e83451f086632c3d76504cd6/sbatch_result.json'
 ack=e.read(ack_path);gateway=prior[1]['downstream_gateway']
 require(ack['returncode']==0 and ack['stdout']=='3042529\n' and ack['stderr']=='' and ack['actual_sbatch_argv']==gateway['actual_sbatch_argv'],'original single ACK differs')
 require(gateway['request_token']=='cti-downstream-gateway-v1:'+gateway['authorization']['sha256'] and '--comment='+gateway['request_token'] in ack['actual_sbatch_argv'],'exact request token/comment differs')
 snap=e.read(p['raw_failure_snapshot']['path']);require(snap['version']==VERSION and snap['status']=='author_verified_snapshot_not_root_acceptance' and snap['jobs']==p['prior_jobs'],'raw forensic snapshot identity differs')
 for jid,values in snap['accounting'].items():
  j=next(x for x in prior if x['job_id']==jid);require(all(j[k]==v for k,v in values.items()),'raw Slurm terminal/cost mismatch')
 for rel,row in snap['raw_files'].items():
  _watch(e,rel,row['sha256']);require(e.path(rel).stat().st_size==row['bytes'],'raw failure size differs')
  target=P/rel;require(target.resolve()==target and target.is_file() and target.stat().st_size==row['bytes'] and sha(target.read_bytes())==row['sha256'],'runtime raw failure and archived bytes differ')
 for absence in snap['absence']:
  target=Path(absence['directory']);require(target==target.resolve() and P in target.parents and absence['matching_files']==[] and not list(target.glob(absence['pattern'])),'failed allocation gained child artifacts')
 repair=e.read('results/formal_main_v2/preflight/heartbeat_20261019T2318/Spatial_dependency_repair.json')
 require(repair['failed_job_id']=='3042529' and repair['failed_GPU_seconds_retained']==2 and repair['child_started'] is False and repair['models_loaded'] is False and repair['actual_P_wrapper_verify_passed'] is True,'prior bounded dependency repair differs')
 require(repair['missing_dependency']['sha256']==p['prefix_review']['sha256'] and sha((P/p['prefix_review']['path']).read_bytes())==p['prefix_review']['sha256'],'missing genuine prior review remains unresolved')
 _ledger_prefix(e,p,postrun=postrun)
 if not postrun:
  _watch(e,p['prefix_report']['path'],p['prefix_report']['sha256'])
  scheduler=_original(PLANNER)
  original=scheduler.require_root_review(evidence,p['prefix_review']['path'],scheduler.formal_jobs({'registered_jobs':jobs}),expected_stage='development')
  require(original['job_id']=='3022743' and original['completed_trials']==12 and original['expected_trials']==600 and original['scientific_complete'] is False,'original whole-chain prefix review differs')
 e.unchanged();return descriptor()

def check_repair(evidence,path,jobs,*,postrun=False,current_job=None):
 require(path==REPAIR,'only exact separately root-reviewed repair path')
 e=Evidence(evidence);d=e.read(path);proof=verify_history(evidence,jobs,postrun=postrun,current_job=current_job);p=policy()
 expected={'schema':'formal_main_v2','kind':'downstream_repair','status':'reviewed','reviewed_by':'root','stage_key':p['stage_key'],'target_source_sha256':p['source_sha256'],'adapter_sha256':p['adapter_sha256'],'execution_manifest_sha256':p['manifest']['sha256'],'prior_review_sha256':p['prefix_review']['sha256'],'failed_job_ids':['3042529'],'typed_predispatch_history':proof}
 require(all(d.get(k)==v for k,v in expected.items()),'root repair does not bind exact typed history')
 require(isinstance(d.get('diagnosis'),str) and d['diagnosis'].strip() and isinstance(d.get('bounded_fix'),str) and d['bounded_fix'].strip(),'concrete bounded repair required')
 ref=d.get('independent_history_review');require(type(ref)is dict and set(ref)=={'path','sha256'} and ref.get('path')==HISTORY_REVIEW,'exact separately archived independent typed history review required');_watch(e,ref['path'],ref['sha256']);ind=e.read(ref['path'])
 require(ind.get('kind')=='formal_predispatch_history_independent_CPU_review' and ind.get('status')=='passed_CPU_review' and ind.get('review_role')=='independent' and ind.get('blockers')==[] and ind.get('history_control_sources')==closure() and ind.get('typed_predispatch_history')==proof,'independent exact history proof missing')
 return proof

def _original(rel,changes=(),injections=None):
 p=policy();raw=safe(rel).read_bytes();require(sha(raw)==p['original_sources'][rel],'original source drift: '+rel);source=raw.decode()
 for before,after in changes:
  require(source.count(before)==1,'derivation target not unique: '+rel);source=source.replace(before,after,1)
 m=ModuleType('_spatial588_'+Path(rel).stem+'_'+sha(source.encode())[:16]);m.__file__=str(safe(rel));m.__package__='';exec(compile(source,str(safe(rel))+'::<explicit_spatial588_control>','exec'),m.__dict__)
 m.__dict__.update(injections or {});m._spatial588_derivation={'original':{'path':rel,'sha256':p['original_sources'][rel]},'derived_source_sha256':sha(source.encode()),'replacements':len(changes),'original_file_modified':False};return m

def scope_args(args):
 p=policy();expected={'stage':'development','source_inventory':'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','execution_manifest':p['manifest']['path'],'output_relative':None,'freeze_directory':None,'profile_panel':None,'prior_review':p['prefix_review']['path'],'collection_review':None,'repair_record':REPAIR,'resume':True,'stop_after':None}
 require(vars(args)==expected,'only exact full588 Spatial continuation arguments')

def scope_invocation(inv):
 p=policy();expected={'stage':'development','stage_key':p['stage_key'],'suite':'libero_spatial','method_ids':p['method_ids'],'resume':True,'prior_job_ids':['3022743','3042529'],'prior_review':p['prefix_review']['path'],'repair_record':REPAIR,'stop_after':None,'run_root':p['run_root'],'execution_manifest':str(P/p['manifest']['path']),'execution_manifest_sha256':p['manifest']['sha256'],'source_sha256':p['source_sha256'],'pre_dispatch_history':descriptor(),'legacy12_compatibility':compatibility_module().descriptor()}
 require(all(inv.get(k)==v for k,v in expected.items()),'actual continuation scope/typed history differs')
 require('--resume' in inv.get('argv',[]) and not any(x in inv.get('argv',[]) for x in ['--sealed-final','--release','--stop-after']),'final/partial scope forbidden')

def control_modules(evidence=None):
 # Two semantic corrections, each gated before the original function runs.
 changes=[('if review["job_id"] != prior[-1]["job_id"]:', 'if review["job_id"] != "3022743":'),('or set(ledger["invocation_job_ids"]) != {j["job_id"] for j in prior}', 'or set(ledger["invocation_job_ids"]) != {"3022743"}')]
 planner=_original(PLANNER,changes);factory=_original(HELPER);original_prior=planner.prior_contract
 def prior(args,state,validated,project):
  scope_args(args);require(Path(project).resolve()==R,'exact control root')
  check_repair(validated['evidence'],args.repair_record,planner.formal_jobs(state))
  compatibility_module().check_adoption(validated['evidence'],postrun=False)
  return original_prior(args,state,validated,project)
 planner.prior_contract=prior;original_plan=planner.plan
 def plan(args,state,*,project=R,helper=None):
  scope_args(args);require(Path(project).resolve()==R and helper in (None,factory),'exact root/original private helper only')
  result=original_plan(args,copy.deepcopy(state),project=R,helper=factory)
  result['invocation']['pre_dispatch_history']=descriptor();result['invocation']['legacy12_compatibility']=compatibility_module().descriptor();result['plan_sha256']=planner.signature({k:v for k,v in result.items() if k!='plan_sha256'})
  scope_invocation(result['invocation']);require(result['invocation_relative'].endswith('_attempt03.json'),'only one subsequent real allocation')
  return result
 planner.plan=plan
 return factory,planner

def terminal_old(evidence,jobs,job,invocation):
 scope_invocation(invocation);check_repair(evidence,invocation['repair_record'],jobs,postrun=True,current_job=job)
 # All original allocation rows, ordering, sources, raw pulls and repair checks
 # remain. Only this proven no-child allocation has no ordinary review/ledger.
 changes=[
 ('set(observed) == (set(ids) if job["mode"] in ("development", "final") else {job["job_id"]})','set(observed) == set(ids) - {"3042529"}'),
 ('    for index, jid in enumerate(ids[:-1]):\n        # Walk every adjacent continuation, not just the most recent review:', '    for index, jid in enumerate(ids[:-1]):\n        if jid == "3042529":\n            _spatial588_failed_edge(evidence, scheduler, jobs, job, invocation, observed)\n            continue\n        # Walk every adjacent continuation, not just the most recent review:'),
 ('prior.get("job_id") == ids[-2]', 'prior.get("job_id") == "3022743"')]
 def failure_edge(ev,scheduler,js,j,inv,observed):
  scope_invocation(inv);check_repair(ev,inv['repair_record'],js,postrun=True,current_job=j)
  require(observed==['3022743',j['job_id']],'only actual prefix/new invocation sequence allowed')
 old=_original(OLD_REVIEW,changes,{'_spatial588_failed_edge':failure_edge});base_cost=old.allocation_cost
 def allocation(ev,scheduler,js,j,inv,observed):
  scope_invocation(inv);check_repair(ev,inv['repair_record'],js,postrun=True,current_job=j)
  require(inv['prior_job_ids']==['3022743','3042529'] and observed==['3022743',j['job_id']],'no silent omitted/fabricated allocation or raw invocation')
  result=base_cost(ev,scheduler,js,j,inv,observed)
  require(result['all_attempt_gpu_seconds']==395+j['elapsed_seconds'],'failure allocation cost lost')
  return {**result,'typed_predispatch_history':descriptor()}
 old.allocation_cost=allocation;return old

def reviewer_module(evidence=None):
 changes=[('    old = load(evidence, OLD_REVIEW, PINNED[OLD_REVIEW])','    old = _spatial588_old(evidence, registered_jobs, job, evidence.read_ref(invocation_ref))')]
 mod=_original(REVIEWER,changes,{'_spatial588_old':terminal_old});base=mod.review
 def review(project,**kw):
  require(Path(project).resolve()==R,'exact terminal root');ev=mod.Evidence(project);inv=ev.read_ref(kw['invocation_ref']);scope_invocation(inv)
  require(kw['job'].get('invocation','').endswith('_attempt03.json'),'one new allocation only')
  proof=check_repair(ev,inv['repair_record'],kw['registered_jobs'],postrun=True,current_job=kw['job'])
  adopted=compatibility_module().check_adoption(ev,invocation=inv,postrun=True)
  result=base(project,**kw);require(result['scientific_complete'] is True and result['completed_trials']==result['expected_trials']==600,'only full original600 scientific completion may be accepted')
  result['operational_predispatch_history']=proof
  result['execution_lineage']={'original_legacy_prefix_job_id':'3022743','original_legacy_prefix_trials':12,'new_action_job_id':kw['job']['job_id'],'new_action_trials':588,'original_prefix_preserved':True,'old_new_outcome_equivalence_established':True,'eligible_for_current_action_global_freeze':False,'legacy12_compatibility':adopted}
  result['acceptance_limitation']='Exactly12 legacy trials are individually compatible by root-adopted independent byte/identity proof and retain legacy origin;588 new trials are reviewed under the current wrapper. This bounded development consumer alone cannot perform profiling or global final release.'
  result['bounded_development_admission']={'scope':'exact_original_Spatial600_development_only','legacy_compatible_trials':12,'current_wrapper_trials':588,'original_legacy_origin_preserved':True,'global_release':False,'profiling_authorized':False}
  result['audit_source_sha256'].update(closure());result['evidence_sha256'].update(closure());result['evidence_sha256'].update(ev.files)
  ev.unchanged();return result
 mod.review=review;return mod

def consumer_module(evidence=None):
 mod=_original(CONSUMER);mod._reviewer=reviewer_module;base=mod.review_downstream_output
 def consume(ev,reference,*,expected_stage,suite,run_root=None,require_complete=True):
  require(expected_stage=='development' and suite=='libero_spatial' and type(require_complete)is bool,'exact original Spatial development only')
  saved=ev.read(reference['path']);require(saved.get('operational_predispatch_history')==descriptor(),'saved review omitted typed failure history')
  compatibility_module().check_adoption(ev,invocation=ev.read(saved['invocation_ref']['path']),postrun=True)
  return base(ev,reference,expected_stage=expected_stage,suite=suite,run_root=run_root,require_complete=require_complete)
 mod.review_downstream_output=consume;return mod

def repair_proposal():
 p=policy()
 return {'schema':'formal_main_v2','kind':'downstream_repair','status':'candidate_requires_root_review','reviewed_by':None,'stage_key':p['stage_key'],'target_source_sha256':p['source_sha256'],'adapter_sha256':p['adapter_sha256'],'execution_manifest_sha256':p['manifest']['sha256'],'prior_review_sha256':p['prefix_review']['sha256'],'failed_job_ids':['3042529'],'diagnosis':'3042529 failed before child/adapter startup because the genuine3022743 root prefix review was missing from P; source identity and all12 prefix results remain unchanged. Original ACK registration latency is a separate retained transaction issue.','bounded_fix':'Retain both Slurm allocations395GPU seconds, validate exact no-child raw failure and already completed dependency publication, then accept only one full588 resume using the original3022743 prefix review and explicit executed/allocation histories. No scientific setting or checkpoint change.','typed_predispatch_history':descriptor(),'independent_history_review':None,'root_authorized':False,'new_GPU_submissions':0}


def compatibility_module():
 raw=(BASE/'compatibility.py').read_bytes();m=ModuleType('_spatial12_explicit_compatibility_'+sha(raw)[:16]);m.__file__=str(BASE/'compatibility.py');m.__package__='';exec(compile(raw,str(BASE/'compatibility.py'),'exec'),m.__dict__);m.bind_control(__import__('sys').modules.get(__name__) or SimpleNamespace(**globals()));return m

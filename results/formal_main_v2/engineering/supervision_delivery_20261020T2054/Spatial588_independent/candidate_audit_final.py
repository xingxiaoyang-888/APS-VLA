from pathlib import Path
from types import ModuleType,SimpleNamespace
import json,hashlib,copy,ast,datetime,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent
CANDIDATE='.local/spatial588_recovery_20261020T2054/control.py';CANDIDATE_SHA='e3994a213c54b8824febe95bed2e0ca8f76b2782ddd21b5f7c5a1496f4ac3df8'
checks=[];negatives=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(ok,label):
 if not ok:raise AssertionError(label)
 checks.append(label)
def fail(label,fn):
 try:fn()
 except (ValueError,AssertionError,FileNotFoundError,KeyError) as exc:negatives.append({'case':label,'exception':type(exc).__name__,'message':str(exc)});return
 raise AssertionError('negative accepted: '+label)
def load(rel,pin):
 ck(h(R/rel)==pin,'source pin '+rel);m=ModuleType('_independent_'+Path(rel).stem);m.__file__=str(R/rel);exec(compile((R/rel).read_bytes(),str(R/rel),'exec'),m.__dict__);return m
before=h(R/'results/experiment_supervisor/state.json');state=json.loads((R/'results/experiment_supervisor/state.json').read_text());jobs=copy.deepcopy(state['registered_jobs'])
c=load(CANDIDATE,CANDIDATE_SHA);p=c.policy();f=c._original(c.HELPER);ev=f.Evidence(R)
proof=c.verify_history(ev,jobs);ck(proof==c.descriptor(),'actual prefix/full raw failed history accepted')
ck(proof['all_prior_job_ids']==['3022743','3042529'] and proof['executed_prior_job_ids']==['3022743'],'allocation and execution remain distinct')
ck(proof['prior_GPU_seconds']==395 and proof['predispatch_failure_GPU_seconds']==2,'retained full raw allocation cost')
for label,mutation in [
 ('missing failure',lambda a:a.pop(next(i for i,j in enumerate(a) if j['job_id']=='3042529'))),
 ('missing executed prefix',lambda a:a.pop(next(i for i,j in enumerate(a) if j['job_id']=='3022743'))),
 ('duplicate allocation',lambda a:a.append(copy.deepcopy(next(j for j in a if j['job_id']=='3042529')))),
 ('failure falsely completed',lambda a:next(j for j in a if j['job_id']=='3042529').update(status='COMPLETED',exit_code='0:0')),
 ('failure cost omitted',lambda a:next(j for j in a if j['job_id']=='3042529').update(elapsed_seconds=0)),
 ('prefix cost differs',lambda a:next(j for j in a if j['job_id']=='3022743').update(elapsed_seconds=392)),
 ('wrong source',lambda a:next(j for j in a if j['job_id']=='3042529').update(source_sha256='0'*64)),
 ('wrong run root',lambda a:next(j for j in a if j['job_id']=='3042529').update(run_root='/tmp/wrong')),
 ('forged failed prior ID',lambda a:next(j for j in a if j['job_id']=='3042529').update(prior_job_ids=[])),
 ('active overlapping new attempt',lambda a:a.append({**copy.deepcopy(next(j for j in a if j['job_id']=='3042529')),'job_id':'9999000','status':'RUNNING','exit_code':'0:0'})),
 ('terminal duplicate attempt',lambda a:a.append({**copy.deepcopy(next(j for j in a if j['job_id']=='3042529')),'job_id':'9999001','status':'COMPLETED','exit_code':'0:0'})),
 ('new wrong methods overlap',lambda a:a.append({'job_id':'9999002','suite':'libero_spatial','mode':'development','method_ids':['dense'],'status':'RUNNING'}))]:
 js=copy.deepcopy(jobs);mutation(js);fail(label,lambda js=js:c.verify_history(f.Evidence(R),js))
class HashFault:
 def __init__(self,target):self.base=f.Evidence(R);self.project=R;self.target=target
 def path(self,n):return self.base.path(n)
 def watch(self,n):return '0'*64 if str(n)==self.target else self.base.watch(n)
 def read(self,n):return self.base.read(n)
 def unchanged(self):return self.base.unchanged()
for rel in [p['prefix_review']['path'],p['raw_failure_snapshot']['path'],'results/formal_main_v2/job_receipts/3042529.json','results/formal_main_v2/invocations/libero_spatial_development_8c843c1d4ee8383c_attempt02.json','results/formal_main_v2/execution/libero_spatial_development_first_pair_v1.json']:
 fail('changed evidence SHA '+rel,lambda rel=rel:c.verify_history(HashFault(rel),jobs))
class ReadFault:
 def __init__(self,target,change):self.base=f.Evidence(R);self.project=R;self.target=target;self.change=change
 def path(self,n):return self.base.path(n)
 def watch(self,n):return self.base.watch(n)
 def read(self,n):
  o=self.base.read(n)
  if str(n)==self.target:o=copy.deepcopy(o);self.change(o)
  return o
 def unchanged(self):return self.base.unchanged()
receipt='results/formal_main_v2/job_receipts/3042529.json'
for label,change in [('falsely executed child',lambda d:d.update(original_scientific_wrapper_executed=True)),('forged adapter',lambda d:d.update(adapter_artifacts=[{}])),('forged action receipt',lambda d:d.update(action_execution_artifacts=[{}])),('different failure reason',lambda d:d.update(error='CUDA out of memory'))]:
 fail(label,lambda change=change:c.verify_history(ReadFault(receipt,change),jobs))
args={'stage':'development','source_inventory':'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','execution_manifest':p['manifest']['path'],'output_relative':None,'freeze_directory':None,'profile_panel':None,'prior_review':p['prefix_review']['path'],'collection_review':None,'repair_record':c.REPAIR,'resume':True,'stop_after':None}
c.scope_args(SimpleNamespace(**args));checks.append('exact scope arguments accepted without execution')
for key,val in [('stage','final'),('stage','full'),('stage','collect'),('resume',False),('stop_after',12),('execution_manifest','results/formal_main_v2/execution/other.json'),('prior_review','results/formal_main_v2/downstream_reviews/3042529.json'),('repair_record',None),('freeze_directory','results/formal_main_v2/freeze'),('profile_panel','results/formal_main_v2/panel.json'),('output_relative',p['output_relative']+'/new')]:
 d=dict(args);d[key]=val;fail('scope '+key+'='+str(val),lambda d=d:c.scope_args(SimpleNamespace(**d)))
factory,planner=c.control_modules();fail('missing root repair remains closed',lambda:planner.plan(SimpleNamespace(**args),state,project=R,helper=factory))
pending=copy.deepcopy(state);pending['pending_submission']={'request_token':'unknown'}
fail('pending submission',lambda:planner.plan(SimpleNamespace(**args),pending,project=R,helper=factory))
fail('unbound helper',lambda:planner.plan(SimpleNamespace(**args),state,project=R,helper=SimpleNamespace()))
fail('unbound repair path',lambda:c.check_repair(f.Evidence(R),'.local/fake_repair.json',jobs))
# Verify the exact AST change surface independently, before execution authority.
tree=ast.parse((R/CANDIDATE).read_text());defs={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
changes_by_fn={}
for fn,rel,expectednames in [('control_modules',c.PLANNER,{'prior_contract'}),('terminal_old',c.OLD_REVIEW,{'allocation_cost'})]:
 node=next(n for n in defs[fn].body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='changes' for x in n.targets));changes=ast.literal_eval(node.value);raw=(R/rel).read_text();derived=raw
 for old,new in changes:ck(derived.count(old)==1,'unique AST substitution '+fn);derived=derived.replace(old,new,1)
 a=ast.parse(raw);b=ast.parse(derived);an={n.name:ast.dump(n,include_attributes=False) for n in a.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};bn={n.name:ast.dump(n,include_attributes=False) for n in b.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 changed={name for name in an if an[name]!=bn[name]};ck(changed==expectednames,'AST only '+','.join(expectednames));ck(set(an)==set(bn),'no function/class additions in original '+fn);changes_by_fn[fn]={'replacement_count':len(changes),'changed_original_functions':sorted(changed),'derived_source_sha256':hashlib.sha256(derived.encode()).hexdigest()}
ck(len(changes_by_fn)==2,'planner2 and cost3 exact isolated semantic corrections')
for rel in ['scripts/ops/formal_action_deployment_v1/contract.py','scripts/ops/formal_action_deployment_v1/wrapper.py','scripts/server/run_formal_downstream.py']:
 ck(h(R/rel)==p['original_sources'][rel],'original runtime contract/wrappers unchanged '+rel)
# Additional independent final-candidate checks: legacy/current lineage must not release freeze.
class NoRead:
 def read(self,*args):raise AssertionError('must reject full admission before report I/O')
fail('default complete consumer cannot promote legacy12',lambda:c.consumer_module().review_downstream_output(NoRead(),{},expected_stage='development',suite='libero_spatial'))
fail('explicit complete consumer cannot promote legacy12',lambda:c.consumer_module().review_downstream_output(NoRead(),{},expected_stage='development',suite='libero_spatial',require_complete=True))
source_text=(R/CANDIDATE).read_text();ck("'eligible_for_current_action_global_freeze':False" in source_text and "'old_new_outcome_equivalence_established':False" in source_text,'explicit mixed execution lineage and no current-action equivalence claim')
# The author serialized only synthetic future metadata in an explicitly labelled
# fixture. Independently execute the real candidate cost function with that sparse
# in-memory overlay; neither production evidence nor a current ledger is created.
fixture_rel='.local/spatial588_recovery_20261020T2054/SYNTHETIC_cost_fixtures.json';ck(h(R/fixture_rel)=='a9248391fdaf0a9d04871ac280cf59fa3f47f9d8cdecbfd2d256a5cad3bd0529','synthetic unit fixture identity')
fixture=json.loads((R/fixture_rel).read_text());ck(fixture['kind']=='synthetic_CPU_fixture_only' and fixture['not_production_authorization'] is True,'fixture explicitly non-authoritative')
def hashj(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
class SyntheticEvidence:
 def __init__(self,overlay):self.project=R;self.base=f.Evidence(R);self.overlay=copy.deepcopy(overlay);self.files={}
 def path(self,n):return self.base.path(n)
 def watch(self,n):
  n=Path(n).relative_to(R).as_posix() if Path(n).is_absolute() else n
  value=hashj(self.overlay[n]) if n in self.overlay else self.base.watch(n);self.files[n]=value;return value
 def read(self,n):
  self.watch(n);return copy.deepcopy(self.overlay[n]) if n in self.overlay else self.base.read(n)
 def unchanged(self):
  self.base.unchanged()
  for n,v in self.files.items():
   if (hashj(self.overlay[n]) if n in self.overlay else self.base.watch(n))!=v:raise AssertionError('synthetic evidence changed '+n)
overlay=fixture['mock_files'];current=fixture['mock_current_job'];inv=overlay[current['invocation']];jobs_normal=c._original(c.PLANNER).formal_jobs(state);synthetic_jobs=jobs_normal+[current];scheduler=c._original(c.PLANNER)
ck(current.get('synthetic_fixture_not_a_job') is True and current['job_id']=='999999997','future CPU current allocation explicitly synthetic')
ck(not (R/current['invocation']).exists() and not (R/c.REPAIR).exists(),'no real new invocation or root repair written')
old=c.terminal_old(SyntheticEvidence(overlay),synthetic_jobs,current,inv)
cost=old.allocation_cost(SyntheticEvidence(overlay),scheduler,synthetic_jobs,current,inv,['3022743','999999997'])
ck(cost['all_attempt_gpu_seconds']==495 and cost['current_gpu_seconds']==100 and [r['job_id'] for r in cost['allocations']]==['3022743','3042529','999999997'],'simulated100 plus real395 preserves failed2; not actual cost')
for label,mut in [('wrong GPU allocation',{'gpus':2}),('wrong current manifest',{'execution_manifest_sha256':'0'*64}),('failed current status',{'status':'FAILED','exit_code':'1:0'}),('noninteger current cost',{'elapsed_seconds':100.5})]:
 j=copy.deepcopy(current);j.update(mut);js=jobs_normal+[j]
 fail('synthetic cost '+label,lambda j=j,js=js:c.terminal_old(SyntheticEvidence(overlay),js,j,inv).allocation_cost(SyntheticEvidence(overlay),scheduler,js,j,inv,['3022743','999999997']))
for observed in [['3022743','3042529','999999997'],['999999997'],['999999997','3022743'],['3022743','999999997','999999997']]:
 fail('synthetic raw execution coverage '+str(observed),lambda observed=observed:old.allocation_cost(SyntheticEvidence(overlay),scheduler,synthetic_jobs,current,inv,observed))
ck(not (R/current['invocation']).exists() and not (R/c.REPAIR).exists(),'synthetic evidence never written to production paths')

ck(h(R/'results/experiment_supervisor/state.json')==before,'no production state mutation')
ck(h(R/CANDIDATE)==CANDIDATE_SHA,'candidate did not change during independent audit')
result={'schema':'formal_main_v2','kind':'independent_spatial588_candidate_CPU_review','status':'passed_bounded_CPU_pending_canonical_and_runtime_closure','review_role':'independent','candidate':{'path':CANDIDATE,'sha256':CANDIDATE_SHA},'checks':checks,'negative_cases':negatives,'check_count':len(checks),'negative_count':len(negatives),'typed_predispatch_history':proof,'original_AST_derivation':changes_by_fn,'production_authorized':False,'new_GPU_jobs':0,'new_scientific_trials':0,'state_unchanged':True,'final_release':False,'legacy12_current_action_compatibility_proven':False,'complete_current_action_consumer_blocked':True,'simulated_cost_only':{'real_prior_GPU_seconds':395,'mock_current_GPU_seconds':100,'mock_sum_NOT_ACTUAL_COST':495},'actual_full_terminal_review_executed':False,'remaining_required':['Separate exact legacy12 current-action compatibility proof before full development/global freeze admission','Root must publish canonical control/forensic snapshot and independently bound root repair; private descriptor is not production proof','Exact new action transition/effective invocation/runtime_readiness and actual P wrapper --verify','Root post-training gateway scope/capacity/duplicate/unknown pending and independent approval','Genuine600 terminal reviewer/consumer after real588 resume; no synthetic report acceptance'],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
q=D/'candidate_audit_final.json';q.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(q),'sha256':h(q),'status':result['status'],'checks':len(checks),'negative_cases':len(negatives)}))

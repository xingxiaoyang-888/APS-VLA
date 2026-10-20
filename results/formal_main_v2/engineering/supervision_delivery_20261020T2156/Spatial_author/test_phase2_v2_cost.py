"""CPU-only simulated future invocation/cost inputs. NOT a job or root approval.
The sparse in-memory overlay never writes a production path or Slurm record.
"""
from pathlib import Path
from types import ModuleType
from datetime import datetime,timezone
import copy,hashlib,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent/'phase2_v2'
PIN='e2e7c3fe7f6dcf4f63b4550c3f5bc8ec50a05aaf462b38ed961ce356cc414683'
raw=(D/'control.py').read_bytes();assert hashlib.sha256(raw).hexdigest()==PIN
c=ModuleType('_spatial588_cost_fixture');c.__file__=str(D/'control.py');exec(compile(raw,str(D/'control.py'),'exec'),c.__dict__);sys.path.insert(0,str(R/'src'))
helper=c._original(c.HELPER);planner=c._original(c.PLANNER);state=json.loads((R/'results/experiment_supervisor/state.json').read_text());jobs=planner.formal_jobs(state);p=c.policy();proof=c.descriptor();checks=[]
def hashj(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def put(name,d):
 path=D/name
 with path.open('x',encoding='utf-8') as f:json.dump(d,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return {'path':path.relative_to(R).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
class SyntheticEvidence:
 def __init__(self,overlay):self.project=R;self.real=helper.Evidence(R);self.overlay=overlay;self.files={}
 def path(self,n):return self.real.path(n)
 def watch(self,n):
  n=Path(n).relative_to(R).as_posix() if Path(n).is_absolute() else n
  h=hashj(self.overlay[n]) if n in self.overlay else self.real.watch(n);self.files[n]=h;return h
 def read(self,n):
  self.watch(n);return copy.deepcopy(self.overlay[n]) if n in self.overlay else self.real.read(n)
 def unchanged(self):
  self.real.unchanged()
  for n,h in self.files.items():assert h==(hashj(self.overlay[n]) if n in self.overlay else self.real.watch(n))
def reject(name,fn):
 try:fn()
 except (ValueError,KeyError,FileNotFoundError,AssertionError) as exc:checks.append({'name':name,'passed':True,'expected_rejection':str(exc)});return
 raise AssertionError('unexpected acceptance: '+name)
try:
 failure=next(j for j in jobs if j['job_id']=='3042529');current=copy.deepcopy(failure)
 current.update(job_id='999999997',status='COMPLETED',raw_status='COMPLETED',exit_code='0:0',elapsed_seconds=100,submitted_utc='2099-01-01T00:00:00+00:00',prior_job_ids=['3022743','3042529'],invocation='results/formal_main_v2/invocations/libero_spatial_development_8c843c1d4ee8383c_attempt03.json',synthetic_fixture_not_a_job=True)
 inv=json.loads((R/failure['invocation']).read_text());inv.update(prior_job_ids=['3022743','3042529'],repair_record=c.REPAIR,pre_dispatch_history=proof,legacy12_compatibility=c.compatibility_module().descriptor(),prior_allocation_cost=[{k:j.get(k) for k in ('job_id','status','raw_status','exit_code','elapsed_seconds','gpus')} for j in jobs if j['job_id'] in ['3022743','3042529']],synthetic_fixture_not_a_production_invocation=True)
 indpath=c.HISTORY_REVIEW;ind={'kind':'formal_predispatch_history_independent_CPU_review','status':'passed_CPU_review','review_role':'independent','blockers':[],'history_control_sources':c.closure(),'typed_predispatch_history':proof,'synthetic_fixture_only':True}
 repair=c.repair_proposal();repair.update(status='reviewed',reviewed_by='root',independent_history_review={'path':indpath,'sha256':hashj(ind)},synthetic_fixture_only=True)
 inv['root_evidence_sha256'].update({c.REPAIR:hashj(repair),indpath:hashj(ind)})
 current['invocation_sha256']=hashj(inv);full=jobs+[current];overlay={current['invocation']:inv,c.REPAIR:repair,indpath:ind};ev=SyntheticEvidence(overlay)
 old=c.terminal_old(ev,full,current,inv)
 result=old.allocation_cost(ev,planner,full,current,inv,['3022743',current['job_id']]);assert [x['job_id'] for x in result['allocations']]==['3022743','3042529','999999997'];assert result['all_attempt_gpu_seconds']==495 and result['current_gpu_seconds']==100
 checks.append({'name':'synthetic_terminal_cost_retains_all3_allocations_and_failure2_seconds','passed':True})
 for observed in [[],['999999997'],['3022743','3042529','999999997'],['999999997','3022743'],['3022743','999999997','999999997']]:
  reject('observed_'+','.join(observed),lambda observed=observed:old.allocation_cost(SyntheticEvidence(overlay),planner,full,current,inv,observed))
 for key,value in [('prior_job_ids',['3022743']),('prior_review','results/formal_main_v2/downstream_reviews/3042529.json'),('repair_record',None),('method_ids',['dense']),('suite','libero_goal'),('stage','final')]:
  bad=copy.deepcopy(inv);bad[key]=value;reject('invocation_'+key,lambda bad=bad:c.terminal_old(SyntheticEvidence(overlay),full,current,bad))
 bad_overlay=copy.deepcopy(overlay);bad_overlay[c.REPAIR]['typed_predispatch_history']['predispatch_failure_GPU_seconds']=0
 reject('forged_repair_failure_cost',lambda:c.terminal_old(SyntheticEvidence(bad_overlay),full,current,inv))
 bad_overlay=copy.deepcopy(overlay);bad_overlay[indpath]['history_control_sources']={}
 reject('independent_review_omits_actual_control',lambda:c.terminal_old(SyntheticEvidence(bad_overlay),full,current,inv))
 bad=copy.deepcopy(inv);bad['prior_allocation_cost'][1]['elapsed_seconds']=0;bad_overlay=copy.deepcopy(overlay);bad_overlay[current['invocation']]=bad;badjob=copy.deepcopy(current);badjob['invocation_sha256']=hashj(bad);badjobs=jobs+[badjob]
 reject('original_cost_guard_still_rejects_omitted_failure_seconds',lambda:c.terminal_old(SyntheticEvidence(bad_overlay),badjobs,badjob,bad).allocation_cost(SyntheticEvidence(bad_overlay),planner,badjobs,badjob,bad,['3022743','999999997']))
 reject('current_action_complete_consumer_blocks_missing_real_terminal_and_adoption',lambda:c.consumer_module().review_downstream_output(helper.Evidence(R),{},expected_stage='development',suite='libero_spatial',require_complete=True))
 fixtures=put('SYNTHETIC_cost_fixtures.json',{'kind':'synthetic_CPU_fixture_only','not_production_authorization':True,'never_written_to_production_paths':True,'mock_current_job':current,'mock_files':overlay,'raw_current_ledger_not_fabricated':True})
 report={'schema':'formal_main_v2','kind':'formal_predispatch_terminal_cost_author_CPU_test','status':'passed_synthetic_terminal_cost_unit_test_only','utc':datetime.now(timezone.utc).isoformat(),'control_sha256':PIN,'checks':checks,'check_count':len(checks),'synthetic_fixture':fixtures,'result':result,'mock_GPU_seconds_NOT_ACTUAL_COST':495,'real_retained_prior_GPU_seconds':395,'new_GPU_submissions':0,'new_scientific_trials':0,'actual_current_job_exists':False,'new_ledger_invocation_fabricated':False,'production_chain_complete':False,'actual_full_terminal_consumer_executed':False,'current_action_legacy12_compatibility_proven':True,'new_terminal_review_still_required':True}
 print(json.dumps(put('synthetic_terminal_cost_tests.json',report)))
except BaseException as exc:put('synthetic_terminal_cost_failure.json',{'error':repr(exc),'traceback':traceback.format_exc(),'checks':checks});raise

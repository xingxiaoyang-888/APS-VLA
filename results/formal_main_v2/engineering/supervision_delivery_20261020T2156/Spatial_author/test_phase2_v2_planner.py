"""Full original planner with explicit CPU-only in-memory approval fixtures.
No synthetic receipt is written at its named production path; no P/Slurm/state.
"""
from pathlib import Path
from types import ModuleType,SimpleNamespace
import hashlib,json,copy,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent;B=D/'phase2_v2'
control_raw=(B/'control.py').read_bytes();assert hashlib.sha256(control_raw).hexdigest()=='e2e7c3fe7f6dcf4f63b4550c3f5bc8ec50a05aaf462b38ed961ce356cc414683'
c=ModuleType('_phase2_planner_fixture');c.__file__=str(B/'control.py');exec(compile(control_raw,c.__file__,'exec'),c.__dict__)
factory,planner=c.control_modules();OriginalEvidence=factory.Evidence;state=json.loads((R/'results/experiment_supervisor/state.json').read_text());before=hashlib.sha256((R/'results/experiment_supervisor/state.json').read_bytes()).hexdigest();checks=[]
def hashj(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def save(name,obj):
 p=B/name;p.write_text(json.dumps(obj,sort_keys=True,ensure_ascii=False,indent=2)+'\n');return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
indpath=c.HISTORY_REVIEW
ind={'kind':'formal_predispatch_history_independent_CPU_review','status':'passed_CPU_review','review_role':'independent','blockers':[],'history_control_sources':c.closure(),'typed_predispatch_history':c.descriptor(),'synthetic_fixture_only':True}
repair=c.repair_proposal();repair.update(status='reviewed',reviewed_by='root',independent_history_review={'path':indpath,'sha256':hashj(ind)},synthetic_fixture_only=True)
bridge=c.compatibility_module();ipath=bridge.INDEPENDENT_REVIEW;actual_ind=json.loads((R/'.local/spatial12_independent_20261020T2156/independent_review.json').read_text());adopt=bridge.adoption_proposal();adopt.update(status='root_adopted',reviewed_by='root',independent_review={'path':ipath,'sha256':bridge.INDEPENDENT_SHA},synthetic_fixture_only=True)
overlay={indpath:ind,c.REPAIR:repair,bridge.ADOPTION:adopt}
class SyntheticEvidence:
 def __init__(self,project):
  assert Path(project).resolve()==R;self.project=R;self.real=OriginalEvidence(R);self.files={}
 def __getattr__(self,n):return getattr(self.real,n)
 def require(self,paths):return self.real.require([p for p in paths if (Path(p).relative_to(R).as_posix() if Path(p).is_absolute() else p) not in overlay])
 def path(self,n):return self.real.path(n)
 def watch(self,n):
  n=Path(n).relative_to(R).as_posix() if Path(n).is_absolute() else n
  value=hashj(overlay[n]) if n in overlay else self.real.watch(n);self.files[n]=value;return value
 def read(self,n):
  self.watch(n);return copy.deepcopy(overlay[n]) if n in overlay else self.real.read(n)
 def unchanged(self):
  self.real.unchanged()
  for n,h in self.files.items():assert h==(hashj(overlay[n]) if n in overlay else self.real.watch(n))
factory.Evidence=SyntheticEvidence
args=SimpleNamespace(stage='development',source_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',execution_manifest=c.policy()['manifest']['path'],output_relative=None,freeze_directory=None,profile_panel=None,prior_review=c.policy()['prefix_review']['path'],collection_review=None,repair_record=c.REPAIR,resume=True,stop_after=None)
def reject(name,fn):
 try:fn()
 except (ValueError,KeyError,FileNotFoundError,AssertionError) as e:checks.append({'name':name,'expected_rejection':str(e)});return
 raise AssertionError('unexpected acceptance '+name)
try:
 planned=planner.plan(args,state,project=R,helper=factory);c.scope_invocation(planned['invocation']);assert planned['invocation']['prior_job_ids']==['3022743','3042529'];assert planned['invocation_relative'].endswith('_attempt03.json')
 checks.append({'name':'full_original_planner_with_only_CPU_in_memory_approval_overlay','passed':True})
 assert planned['invocation']['legacy12_compatibility']==bridge.descriptor() and planned['invocation']['pre_dispatch_history']==c.descriptor();checks.append({'name':'separate_allocation_and_executed_history_plus_legacy12_descriptor','passed':True})
 reject('wrong_factory',lambda:planner.plan(args,state,project=R,helper=c._original(c.HELPER)))
 bad=copy.deepcopy(state);bad['pending_submission']={'unknown':'not_cleared'};reject('pending_duplicate_submission',lambda:planner.plan(args,bad,project=R,helper=factory))
 for key,wrong in [('resume',False),('stage','final'),('stage','full'),('stage','components'),('stage','collect'),('execution_manifest','foreign.json'),('prior_review','results/formal_main_v2/downstream_reviews/3042529.json'),('stop_after',12)]:
  a=copy.deepcopy(args);setattr(a,key,wrong);reject('scope_'+key+'_'+str(wrong),lambda a=a:planner.plan(a,state,project=R,helper=factory))
 saved=copy.deepcopy(overlay[bridge.ADOPTION]);overlay[bridge.ADOPTION]['status']='candidate';reject('root_adoption_not_complete',lambda:planner.plan(args,state,project=R,helper=factory));overlay[bridge.ADOPTION]=saved
 saved=copy.deepcopy(overlay[indpath]);overlay[indpath]['typed_predispatch_history']['predispatch_failure_GPU_seconds']=0;reject('failure_cost_omission',lambda:planner.plan(args,state,project=R,helper=factory));overlay[indpath]=saved
 new=copy.deepcopy(next(j for j in state['registered_jobs'] if j['job_id']=='3042529'));new.update(job_id='999999996',status='UNKNOWN');bad=copy.deepcopy(state);bad['registered_jobs'].append(new);reject('unknown_overlapping_job',lambda:planner.plan(args,bad,project=R,helper=factory))
 req={k:v for k,v in planned.items() if k!='plan_sha256'};assert planner.signature(req)==planned['plan_sha256'];assert before==hashlib.sha256((R/'results/experiment_supervisor/state.json').read_bytes()).hexdigest()
 # Projection only: no canonical files created, no acceptance implied. All
 # package source bytes remain identical after root-controlled installation.
 private=B.relative_to(R).as_posix();canonical=c.CANONICAL
 projection=lambda value:json.loads(json.dumps(value,ensure_ascii=False).replace(private,canonical))
 projected={'source_closure':projection(c.closure()),'typed_history_descriptor':projection(c.descriptor()),'compatibility_descriptor':projection(bridge.descriptor()),'root_adoption_proposal':projection(bridge.adoption_proposal()),'repair_proposal':projection(c.repair_proposal()),'actual_canonical_publication_done':False}
 assert private not in json.dumps(projected);checks.append({'name':'canonical_projection_changes_only_bundle_root_paths_not_file_bytes_or_legacy_provenance','passed':True})
 fixture=save('SYNTHETIC_planner_fixture.json',{'kind':'CPU_in_memory_fixture_NOT_PRODUCTION','synthetic_plan_NOT_FOR_SUBMISSION':planned,'mocked_approval_file_paths':sorted(overlay),'production_paths_never_written':True,'new_GPU_seconds':0,'new_trials':0})
 save('canonical_projection.json',projected)
 save('phase2_planner_tests.json',{'status':'passed_CPU_planner_candidate_only','checks':checks,'check_count':len(checks),'fixture':fixture,'source_closure':c.closure(),'new_GPU_seconds':0,'new_trials':0,'actual_new_P_verify':False,'canonical_root_adoption_published':False,'state_unchanged':True})
 print(json.dumps({'status':'passed_CPU_planner_candidate_only','checks':len(checks),'fixture':fixture}))
except BaseException as e:
 save('phase2_planner_failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'checks':checks,'new_GPU_seconds':0});raise

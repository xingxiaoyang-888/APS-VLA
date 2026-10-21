"""Root-only exact metadata construction. No Slurm calls or scientific execution."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
BASE='scripts/ops/formal_object_single_error_gateway_v1'
def module(pin):
 p=R/BASE/'gateway.py';b=p.read_bytes()
 if hashlib.sha256(b).hexdigest()!=pin:raise ValueError('exact installed gateway SHA required')
 s=importlib.util.spec_from_file_location('_object_exact_builder_gateway',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m
 exec(compile(b,str(p),'exec',dont_inherit=True),m.__dict__);return m
def stage_plan(g):
 F,C,A,W,G=g.production_modules()
 old=g.read(g.R/g.PROD_REVIEW,g.PROD_REVIEW_SHA)
 sources=g.production_map()
 g.require(old.get('kind')=='Object_single_error_production_candidate_independent_review'
  and old.get('status')=='passed_CPU_candidate_with_production_HOLD' and old.get('blockers')==[]
  and old.get('production_source_closure')==sources and old.get('replayed_author_positive')==14
  and old.get('replayed_author_negative')==69 and old.get('production_admitted') is False,
  'actual independent CPU source proof absent')
 context=W.reference_context(project=g.R)
 A.require_independent(g.R,C.ref(g.R,C.ADOPTION_INDEPENDENT),context['adoption'])
 root_adoption=g.read(g.R/g.ADOPTION,g.ADOPTION_SHA);g.raw(g.R/g.ROWS,g.ROWS_SHA)
 # This is a transparent schema projection of an existing actual independent
 # CPU source review, not an invented independent run or GPU readiness proof.
 source_review=dict(schema=g.EXPERIMENT,kind='Object_single_error_production_source_independent_review',
  status='passed',reviewed_by='independent',schema_projection_by='root',
  original_independent_review=g.ref(g.R,g.PROD_REVIEW),original_reviewed_by=old['reviewed_by'],
  original_review_status=old['status'],blockers=[],production_sources=sources,
  scope_sha256=g.SCOPE,legacy_adoption_sha256=g.ADOPTION_SHA,
  real_raw_consumer_reconstruction_required=True,review_scope='source_and_CPU_only',
  original_production_blockers=old['production_blockers'],actual_new_terminal_review_passed=False,
  actual_GPU_execution_authorized=False)
 repair=dict(schema=g.EXPERIMENT,kind='Object_single_policy_error_linked_repair',status='reviewed',
  reviewed_by='root',scope_sha256=g.SCOPE,version=C.VERSION,logical_trial_id=g.CELL,
  old_failure_start=F.START,old_failure_result=F.RESULT,legacy_root_adoption_sha256=g.ADOPTION_SHA,
  legacy_adoption_rows_sha256=g.ROWS_SHA,original_raw_sha256=F.PINS[F.RUN+'/trials.jsonl'],
  original_job_ids=g.OLD_IDS,original_GPU_seconds=6713,rejected_query8_unknown=True,new_attempt_count=1,
  ordinary_resume=False,full_reset_from_original_initial_state=True,unchanged_full_panel_states=100,
  unchanged_full_scientific_trials=600,unchanged_method_ids=g.METHODS,new_output=g.OUT,
  negative_result_terminal_no_retry=True,scientific_settings_changed=False,final_allowed=False,
  production_sources=sources,original_error_preserved=True,old599_current_count_added=0,
  diagnosis='Original task8/source49/dense stopped with policy_error at query8; only 7 chunks/56 actions saved. The rejected chunk is unknown; no exact old replay or recovered query8 is claimed.',
  bounded_correction='One new linked attempt from the original initial-state reset with the already accepted current action execution semantics; unchanged original action values, 100-state/six-method scientific validation, checkpoint selection, and no result-conditioned retry.',
  root_reconstruction_sha256=F.sig(context['adoption']),source_CPU_review=g.ref(g.R,g.PROD_REVIEW),
  legacy_reference_trials=599,legacy_reference_successes=520,legacy_reference_negative_outcomes=79)
 def future_ref(rel,value):
  b=g.canonical(value)+b'\n';return dict(path=rel,bytes=len(b),sha256=g.sha(b))
 plan=dict(schema=g.EXPERIMENT,kind='Object_single_error_typed_scientific_plan',version=C.VERSION,
  suite='libero_object',stage='development',stage_key=g.STAGE,scope_sha256=g.SCOPE,logical_trial_id=g.CELL,
  reference_invocation=C.ref(g.R,C.REFERENCE),legacy_root_adoption=C.ref(g.R,C.ADOPTION),
  legacy_root_adoption_independent=C.ref(g.R,C.ADOPTION_INDEPENDENT),repair=future_ref(C.REPAIR,repair),
  production_independent=future_ref(g.X+'/production_independent.json',source_review),production_sources=sources,
  dependencies=C.DEPENDENCIES,full_manifest=C.ref(g.R,F.MANIFEST),new_output=g.OUT,method_ids=g.METHODS,
  ordinary_resume=False,stop_after=None,action_semantics_sha256=F.ACTION,source_inventory=C.ref(g.R,F.INVENTORY),
  source_root=str(g.S),final_allowed=False)
 W.validate_repair(repair,plan)
 return {C.REPAIR:repair,g.X+'/production_independent.json':source_review,g.PLAN:plan}

def stage_verify(g):
 F,C,A,W,G=g.production_modules();plan=g.read(g.R/g.PLAN)
 g.require(g.raw(g.P/g.PLAN)==g.raw(g.R/g.PLAN),'plan not installed identically')
 pin=g.sha(g.raw(g.P/g.PLAN))
 argv=[str(g.H/'venv/bin/python'),'-B',str(g.P/g.PROD/'entry.py'),'--verify','--plan',str(g.P/g.PLAN),'--plan-sha256',pin]
 before={**g.production_map(),**g.source_map()}
 answer=subprocess.run(argv,capture_output=True,text=True,timeout=300)
 if answer.returncode!=0:
  raise RuntimeError('actual-P verification failed; preserve stdout/stderr: '+json.dumps(dict(argv=argv,returncode=answer.returncode,stdout=answer.stdout,stderr=answer.stderr)))
 result=json.loads(answer.stdout)
 direct=W.verify_plan(plan,project=g.P)['static_verification']
 g.require(result==direct,'actual-P stdout differs from independent root reconstruction')
 g.require(before=={**g.production_map(),**g.source_map()},'source changed during actual-P verification')
 return {g.X+'/actual_P_verification.json':dict(schema=g.EXPERIMENT,kind='Object_single_error_actual_P_entry_verification_capture',
  status='passed_static_only',reviewed_by='root',argv=argv,returncode=answer.returncode,stdout=answer.stdout,stderr=answer.stderr,
  actual_P_output=result,plan=g.ref(g.R,g.PLAN),production_sources=g.production_map(),gateway_files=g.source_map(),
  source173_verified=True,new_GPU_seconds=0,new_scientific_trials=0,Slurm_submitted=False,final_allowed=False)}

def stage_prepare(g,independent_path,independent_sha):
 g.require(independent_path.startswith('results/formal_main_v2/engineering/'),'use archived independent proof')
 independent=g.read(g.R/g.relative(independent_path),independent_sha)
 sources=g.production_map();files=g.source_map()
 g.require(independent.get('schema')==g.EXPERIMENT and independent.get('kind')=='Object_single_error_gateway_independent_review'
  and independent.get('status')=='passed' and independent.get('scope_sha256')==g.SCOPE
  and independent.get('gateway_files')==files and independent.get('production_sources')==sources
  and independent.get('blockers')==[] and independent.get('review_scope')=='source_and_CPU_only'
  and independent.get('GPU_execution_authorized') is False
  and independent.get('gateway_source')==g.ref(g.R,g.BASE+'/gateway.py'),'exact actual gateway source audit absent')
 F,C,A,W,G=g.production_modules();plan=g.read(g.R/g.PLAN)
 direct=W.verify_plan(plan,project=g.P)['static_verification']
 verification=g.read(g.R/g.X/'actual_P_verification.json')
 g.require(verification.get('returncode')==0 and verification.get('actual_P_output')==direct
  and verification.get('gateway_files')==files and verification.get('production_sources')==sources,'actual-P static proof stale')
 # Retain the independent original bytes unchanged at the exact schema role.
 original=g.raw(g.R/independent_path,independent_sha)
 gateway_ref=dict(path=g.X+'/gateway_independent.json',bytes=len(original),sha256=g.sha(original))
 readiness=dict(schema=g.EXPERIMENT,kind='Object_single_error_root_runtime_readiness',status='passed',reviewed_by='root',
  plan_sha256=F.sig(plan),production_sources=sources,actual_P_verification=direct,
  actual_P_capture=g.ref(g.R,g.X+'/actual_P_verification.json'),gateway_status='independently_reviewed_exact_atomic_submission',
  gateway_independent=gateway_ref,gateway_original_independent=g.ref(g.R,independent_path),
  gateway_files=files,final_allowed=False,new_actual_terminal_review_passed=False,negative_result_terminal_no_retry=True)
 def future_ref(rel,value):
  b=g.canonical(value)+b'\n';return dict(path=rel,bytes=len(b),sha256=g.sha(b))
 stamp=g.utc()
 if (g.R/g.PREPARED).exists():stamp=g.read(g.R/g.PREPARED)['registered_utc']
 inv=dict(schema=g.EXPERIMENT,kind='Object_single_error_bound_invocation',version=C.VERSION,plan=g.ref(g.R,g.PLAN),
  plan_sha256=F.sig(plan),production_sources=sources,runtime_readiness=future_ref(g.X+'/runtime_readiness.json',readiness),
  submission_token=G.token(plan),slurm_comment='cti-object-single-error:'+G.token(plan),job_name=g.NAME,
  account=g.RESOURCES['account'],partition=g.RESOURCES['partition'],
  slurm_output=str(g.P/'results/slurm'/(g.NAME+'_%j.out')),registered_utc=stamp)
 authorization=dict(schema=g.EXPERIMENT,kind='Object_single_error_exact_submission_authorization',version=g.VERSION,
  status='approved_for_exactly_one_held_submission',reviewed_by='root',stage_key=g.STAGE,logical_trial_id=g.CELL,
  pair_id=g.PAIR,scope_sha256=g.SCOPE,maximum_attempts=1,automatic_retry=False,ordinary_resume=False,
  original_GPU_seconds=6713,original_job_ids=g.OLD_IDS,full_manifest_trials=600,actual_trial_allowlist=[g.CELL],
  final_allowed=False,resources=g.RESOURCES,control_root=str(g.R),runtime_root=str(g.P),gateway_files=files,
  production_sources=sources,plan=g.ref(g.R,g.PLAN),runtime_readiness=inv['runtime_readiness'],
  prepared_invocation=future_ref(g.PREPARED,inv),actual_P_verification=g.ref(g.R,g.X+'/actual_P_verification.json'))
 return {g.X+'/gateway_independent.json':original,g.X+'/runtime_readiness.json':readiness,g.PREPARED:inv,g.AUTH:authorization}

def publish(g,objects):
 allowed={g.X+'/'+n for n in ('root_repair.json','production_independent.json','plan.json','actual_P_verification.json',
  'gateway_independent.json','runtime_readiness.json','prepared_invocation.json','submission_authorization.json')}
 g.require(set(objects)<=allowed,'exact metadata roles only')
 data={rel:value if type(value)is bytes else g.canonical(value)+b'\n' for rel,value in objects.items()}
 with g.shared_writer_lock():
  before=g.raw(g.R/g.STATE);state=json.loads(before)
  g.require(state.get('pending_submission') is None and not any(g.duplicate(j) for j in state['registered_jobs']),'existing correction/pending blocks metadata build')
  g.require(not (g.P/g.OUT).exists() and not (g.P/g.INV).exists() and not (g.R/g.INV).exists(),'attempt exists')
  for rel,b in data.items():
   for root in (g.R,g.P):
    if (root/rel).exists():g.require(g.raw(root/rel)==b,'refuse changed existing metadata: '+rel)
  for rel,b in data.items():
   for root in (g.R,g.P):g.immutable(root/rel,b,allow_identical=True)
  g.require(g.raw(g.R/g.STATE)==before,'builder must not change state')
 return {rel:g.ref(g.R,rel) for rel in objects}

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',choices=['plan','verify','prepare'],required=True)
 p.add_argument('--gateway-sha256',required=True);p.add_argument('--builder-sha256',required=True)
 p.add_argument('--root-reviewed',action='store_true');p.add_argument('--publish',action='store_true')
 p.add_argument('--gateway-independent');p.add_argument('--gateway-independent-sha256');a=p.parse_args(argv)
 if Path(__file__).resolve()!=R/BASE/'build.py' or hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=a.builder_sha256:raise ValueError('exact canonical builder required')
 g=module(a.gateway_sha256)
 g.require(a.root_reviewed,'explicit root review required; no metadata approvals inferred')
 if a.phase=='plan':objects=stage_plan(g)
 elif a.phase=='verify':objects=stage_verify(g)
 else:
  g.require(a.gateway_independent is not None and a.gateway_independent_sha256 is not None,'actual archived gateway independent report required')
  objects=stage_prepare(g,a.gateway_independent,a.gateway_independent_sha256)
 if a.publish:
  refs=publish(g,objects);print(json.dumps(dict(status='root_metadata_published_no_Slurm',phase=a.phase,files=refs,new_trials=0,new_GPU_seconds=0),sort_keys=True))
 else:
  print(json.dumps(dict(status='root_review_objects_not_published',phase=a.phase,objects={k:(json.loads(v) if type(v)is bytes else v) for k,v in objects.items()},new_trials=0,new_GPU_seconds=0),sort_keys=True))
if __name__=='__main__':main()

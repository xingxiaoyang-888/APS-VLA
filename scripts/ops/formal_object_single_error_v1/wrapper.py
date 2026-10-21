"""Exact typed static preparation. This is not a Slurm dispatcher."""
import copy,json
from pathlib import Path
import fixed as F
import constants as C
import adoption as A

def reference_context(*,project=F.R):
 F.require(Path(project) in (F.R,F.P),'exact server metadata root required')
 # Run the genuine original reference validator, not a fabricated old invocation.
 reference=json.loads(F.read(project,C.REFERENCE,C.REFERENCE_SHA))
 old=C.load(F.P,C.OLD_WRAPPER,C.OLD_WRAPPER_SHA)
 original_args=old.verify(reference)
 F.require(reference['resume'] is False and reference['stop_after']==12 and reference['prior_job_ids']==[]
  and reference['suite']=='libero_object' and reference['stage']=='development','genuine original first invocation changed')
 args=copy.deepcopy(original_args)
 args.output=F.P/F.OUT;args.stop_after=None;args.resume=False
 before={k:str(v) if isinstance(v,Path) else v for k,v in vars(original_args).items()}
 after={k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()}
 diff={k:{'original':before[k],'actual':after[k]} for k in before if before[k]!=after[k]}
 F.require(diff=={'output':{'original':str(F.P/F.RUN),'actual':str(F.P/F.OUT)},
  'stop_after':{'original':12,'actual':None}},'only output and explicit cell selection replace stop_after12')
 manifest=json.loads(F.read(project,F.MANIFEST,F.PINS[F.MANIFEST]))
 registration=json.loads(args.registration.read_text())
 legacy=C.load(F.P,C.LEGACY,C.LEGACY_SHA)
 legacy.check_paths(args,args.mode,registration,manifest,F.S)
 from cti_vla.evaluation import formal_trials as M
 inputs=F.load_inputs(M)
 adoption=A.rebuild(inputs,project=project)
 runtime=C.load(project,C.RUNTIME,C.RUNTIME_SHA)
 runtime_contract=runtime.make_contract(project_root=project,source_root=F.S,suite='libero_object',stage='development')
 runtime.validate_contract(runtime_contract,project_root=project,source_root=F.S)
 return dict(reference=reference,args=args,original_args=original_args,args_diff=diff,manifest=manifest,
  original_wrapper=old,legacy=legacy,runtime=runtime,runtime_contract=runtime_contract,
  inputs=inputs,adoption=adoption)

def validate_repair(value,plan):
 expected=dict(schema='formal_main_v2',kind='Object_single_policy_error_linked_repair',status='reviewed',
  reviewed_by='root',scope_sha256=F.SCOPE_SHA,version=C.VERSION,logical_trial_id=F.CELL,
  old_failure_start=F.START,old_failure_result=F.RESULT,legacy_root_adoption_sha256=C.ADOPTION_SHA,
  legacy_adoption_rows_sha256=C.ROWS_SHA,original_raw_sha256=F.PINS[F.RUN+'/trials.jsonl'],
  original_job_ids=list(F.JOBS),original_GPU_seconds=6713,rejected_query8_unknown=True,
  new_attempt_count=1,ordinary_resume=False,full_reset_from_original_initial_state=True,
  unchanged_full_panel_states=100,unchanged_full_scientific_trials=600,unchanged_method_ids=list(F.METHODS),
  new_output=F.OUT,negative_result_terminal_no_retry=True,scientific_settings_changed=False,
  final_allowed=False)
 F.require(all(value.get(k)==v for k,v in expected.items()),'exact linked-error root repair required')
 F.require(value.get('production_sources')==plan['production_sources']
  and value.get('diagnosis') and value.get('bounded_correction'),'root repair must bind full new source closure and bounded diagnosis')
 F.require(value.get('original_error_preserved') is True and value.get('old599_current_count_added')==0,'old failure/count changes forbidden')
 return value

def verify_plan(plan,*,project=F.P):
 F.require(Path(project)==F.P,'actual-P static verification requires actual P installation')
 required={'schema','kind','version','suite','stage','stage_key','scope_sha256','logical_trial_id','reference_invocation',
  'legacy_root_adoption','legacy_root_adoption_independent','repair','production_independent','production_sources',
  'dependencies','full_manifest','new_output','method_ids','ordinary_resume','stop_after','action_semantics_sha256',
  'source_inventory','source_root','final_allowed'}
 F.require(set(plan)==required,'unknown or missing typed scientific plan fields')
 expected=dict(schema='formal_main_v2',kind='Object_single_error_typed_scientific_plan',version=C.VERSION,
  suite='libero_object',stage='development',stage_key=C.STAGE_KEY,scope_sha256=F.SCOPE_SHA,logical_trial_id=F.CELL,
  new_output=F.OUT,method_ids=list(F.METHODS),ordinary_resume=False,stop_after=None,
  action_semantics_sha256=F.ACTION,source_root=str(F.S),final_allowed=False)
 F.require(all(plan.get(k)==v for k,v in expected.items()),'scope/mode/output outside exact one linked attempt')
 C.verify_closure(project,plan['production_sources'])
 F.require(plan['dependencies']==C.DEPENDENCIES,'full control dependencies differ')
 F.require(plan['reference_invocation']==C.ref(project,C.REFERENCE) and plan['reference_invocation']['sha256']==C.REFERENCE_SHA,
  'only genuine exact original reference invocation')
 F.require(plan['legacy_root_adoption']==C.ref(project,C.ADOPTION) and plan['legacy_root_adoption']['sha256']==C.ADOPTION_SHA,'actual root599 adoption required')
 F.require(plan['full_manifest']==C.ref(project,F.MANIFEST) and plan['full_manifest']['sha256']==F.PINS[F.MANIFEST],
  'complete original six-method manifest required')
 F.require(plan['source_inventory']==C.ref(project,F.INVENTORY) and plan['source_inventory']['sha256']==F.INVENTORY_SHA,'source173 identity differs')
 context=reference_context(project=project)
 A.require_independent(project,plan['legacy_root_adoption_independent'],context['adoption'])
 repair=validate_repair(C.read_ref(project,plan['repair'],path=C.REPAIR),plan)
 independent=C.read_ref(project,plan['production_independent'],path=F.EX+'/production_independent.json')
 F.require(independent.get('schema')=='formal_main_v2'
  and independent.get('kind')=='Object_single_error_production_source_independent_review'
  and independent.get('status')=='passed' and independent.get('reviewed_by')=='independent'
  and independent.get('blockers')==[] and independent.get('production_sources')==plan['production_sources']
  and independent.get('scope_sha256')==F.SCOPE_SHA and independent.get('legacy_adoption_sha256')==C.ADOPTION_SHA
  and independent.get('real_raw_consumer_reconstruction_required') is True,'complete independently reviewed new source closure required')
 receipt=dict(schema='formal_main_v2',kind='Object_single_error_actual_P_static_verification',status='passed_static_only',
  version=C.VERSION,plan_sha256=F.sig(plan),actual_project=str(F.P),source_root=str(F.S),
  source173_verified=True,production_sources=plan['production_sources'],dependencies=C.DEPENDENCIES,
  original_reference_sha256=C.REFERENCE_SHA,actual_arguments_diff=context['args_diff'],
  legacy_adoption_reconstruction_sha256=F.sig(context['adoption']),ordinary_resume=False,
  original_scientific_wrapper_executed=False,original_manifest_trials=600,actual_allowlist=[F.CELL],
  model_inference_performed=False,GPU_execution_performed=False,GPU_submission_authorized=False,
  final_allowed=False,original_source_unchanged=True)
 return dict(**context,plan=plan,static_verification=receipt,repair=repair)

def verify_invocation(invocation,*,project=F.P,expected_job_id=None):
 required={'schema','kind','version','plan','plan_sha256','production_sources','runtime_readiness',
  'submission_token','slurm_comment','job_name','account','partition','slurm_output','registered_utc'}
 F.require(set(invocation)==required and invocation['kind']=='Object_single_error_bound_invocation'
  and invocation['schema']=='formal_main_v2' and invocation['version']==C.VERSION,'typed actual invocation required')
 plan=C.read_ref(project,invocation['plan'],path=C.PLAN)
 F.require(F.sig(plan)==invocation['plan_sha256'] and invocation['production_sources']==plan['production_sources'],'invocation plan/source differs')
 context=verify_plan(plan,project=project)
 # The immutable pre-submit invocation cannot contain a yet-unknown Slurm ID.
 # Actual ID is supplied by the environment and bound to the unique original ACK
 # in root registration, without rewriting the invocation after sbatch.
 if expected_job_id is not None:
  F.require(type(expected_job_id) is str and expected_job_id.isdigit() and expected_job_id not in F.JOBS,'distinct actual Slurm ID required')
 readiness=C.read_ref(project,invocation['runtime_readiness'],path=F.EX+'/runtime_readiness.json')
 F.require(readiness.get('schema')=='formal_main_v2' and readiness.get('kind')=='Object_single_error_root_runtime_readiness'
  and readiness.get('status')=='passed' and readiness.get('reviewed_by')=='root'
  and readiness.get('plan_sha256')==F.sig(plan) and readiness.get('production_sources')==plan['production_sources']
  and readiness.get('actual_P_verification')==context['static_verification']
  and readiness.get('gateway_status')=='independently_reviewed_exact_atomic_submission'
  and readiness.get('final_allowed') is False,'actual-P and exact atomic gateway release required')
 # No submit implementation is provided by this package: this dependency must
 # be supplied and independently reviewed by root before any invocation can run.
 gateway=C.read_ref(project,readiness.get('gateway_independent'),path=F.EX+'/gateway_independent.json')
 F.require(gateway.get('kind')=='Object_single_error_gateway_independent_review' and gateway.get('status')=='passed'
  and gateway.get('blockers')==[] and gateway.get('scope_sha256')==F.SCOPE_SHA
  and gateway.get('production_sources')==plan['production_sources'],'actual atomic gateway is not admitted')
 source=gateway.get('gateway_source')
 C.read_ref(project,source) if source and source.get('path','').endswith('.json') else None
 F.require(source and source['path']=='scripts/ops/formal_object_single_error_gateway_v1/gateway.py'
  and len(F.read(project,source['path'],source['sha256']))==source['bytes'],'gateway code must be exact independently reviewed actual source')
 context.update(invocation=invocation,readiness=readiness)
 return context

"""Real raw reconstruction; no successful flags can replace source/trajectory/adapter checks."""
import copy,json,types
from pathlib import Path
import numpy as np
import fixed as F
import constants as C
import adoption as A
import execution as E
import wrapper as W
import gateway_contract as G

def validators(*,project=F.R):
 helper=C.load(project,C.HELPER,C.HELPER_SHA);evidence=helper.Evidence(project)
 old=C.load(project,C.OLD_REVIEW,C.OLD_REVIEW_SHA)
 current=C.load(project,C.ACTION_REVIEW,C.ACTION_REVIEW_SHA)
 analyzer=current.load(evidence,'scripts/analyze_formal.py')
 runtime=C.load(project,C.RUNTIME,C.RUNTIME_SHA)
 trajectory,proof=current.trajectory_validator(old,analyzer,runtime)
 return old,helper,evidence,current,runtime,trajectory,proof

def parse_raw(raw,*,config,panel,manifest,job_id,inputs,project=F.R):
 F.require(type(raw) is bytes and raw.endswith(b'\n'),'complete raw linked ledger required')
 rows=[json.loads(line) for line in raw.splitlines()]
 F.require(len(rows)==3 and [r.get('event') for r in rows]==['invocation','start','result'],'one independent actual invocation/start/result only')
 F.require(str(job_id).isdigit() and job_id not in F.JOBS,'distinct actual new job required')
 from cti_vla.evaluation import formal_trials as M
 identity=F.validate_panel_manifest(panel,manifest,config,M)
 F.require(config['source_files']==inputs['config']['source_files']
  and config['registration_sha256']==inputs['config']['registration_sha256']
  and config['watched_files']==inputs['config']['watched_files']
  and config['source_verification']==inputs['config']['source_verification']
  and config['policy_watchdog_seconds']==60.,'new scientific source/model/checkpoint/data/runtime watch identity differs')
 signature=F.sig(config)
 F.require(all(r.get('run_signature')==signature for r in rows),'mixed actual run signature')
 F.require(set(rows[0])=={'event','created_utc','slurm_job_id','run_signature'}
  and rows[0]['slurm_job_id']==job_id and isinstance(rows[0]['created_utc'],str) and rows[0]['created_utc'],'genuine new invocation row required')
 for row in rows[1:]:
  F.require(all(row.get(k)==v for k,v in identity.items()),'different task/source/method/environment/runtime identity')
  F.require(row['trial_id']==F.CELL,'only one exact previously failed logical cell')
 _,_,_,_,_,trajectory,proof=validators(project=project)
 trajectory(rows[-1],manifest['methods'][0]['identity'])
 F.require(type(rows[-1].get('attempt_wall_seconds')) in (int,float) and np.isfinite(rows[-1]['attempt_wall_seconds'])
  and rows[-1]['attempt_wall_seconds']>=0,'actual attempt wall time missing')
 result=rows[-1]
 if result['chunks']:
  old=inputs['results'][F.CELL]
  F.require(result['chunks'][0]['observation_sha256']==old['chunks'][0]['observation_sha256'],
   'full-reset initial observation differs from original exact failed state')
 # No boolean consumer receipts are accepted anywhere in this parser.
 return dict(rows=rows,result=result,run_signature=signature,current_action_validation=proof,
  raw_sha256=F.sha(raw),status='actual_raw_trajectory_reconstructed')

def reference_value(evidence,scheduler,helper,state):
 reference=evidence.read(C.REFERENCE)
 F.require(evidence.watch(C.REFERENCE)==C.REFERENCE_SHA,'genuine original invocation required')
 oldjob=[j for j in scheduler.formal_jobs(state) if j['job_id']=='3021394']
 F.require(len(oldjob)==1,'original registered first allocation missing')
 old=C.load(F.R,C.OLD_REVIEW,C.OLD_REVIEW_SHA)
 value=old.validate_invocation(evidence,scheduler,helper,state,oldjob[0],reference)
 # Explicit analysis projection: this is not a fabricated historical invocation.
 projected=copy.deepcopy(reference)
 projected.update(run_root=str(F.P/F.OUT),stage_key=C.STAGE_KEY,stop_after=None,resume=False,
  wrapper=C.BASE+'/entry.py',wrapper_sha256=None,prior_job_ids=[],prior_review=None,
  prior_allocation_cost=[],repair_record=None)
 argv=list(projected['argv']);i=argv.index('--output');argv[i+1]=str(F.P/F.OUT)
 i=argv.index('--stop-after');del argv[i:i+2]
 projected['argv']=argv
 value=dict(value);value.update(invocation=projected,output=F.OUT,opt={**value['opt'],'--output':str(F.P/F.OUT)})
 value['opt'].pop('--stop-after')
 return value

def reject_synthetic(runtime_proof,action,iterator):
 F.require(runtime_proof.get('synthetic_input') is False and not any(
  r.get('synthetic') is True or r.get('synthetic_fixture') is True for r in action+iterator),
  'synthetic runtime evidence cannot establish actual completion')

def validate_code_claims(iterator,expected):
 # Expected values are recomputed from pinned bytes and actual canonical paths
 # by typed_runtime. This function never accepts caller receipt success flags.
 first=iterator[0];second=iterator[1]
 for name in ('original_execute_code_sha256','original_adapter_run_code_sha256','guard_code_sha256'):
  F.require(first.get(name)==expected[name],'actual compiled code differs: '+name)
 F.require(second.get('original_execute_callbacks')==expected['original_execute_callbacks'],'actual original execute callbacks differ')
 policy=second.get('policy_closure',{})
 for name in ('policy_methods_code_sha256','source_sha256','token_policy_methods_code_sha256','token_policy_source_sha256'):
  F.require(policy.get(name)==expected[name],'actual policy closure differs: '+name)
 F.require(policy.get('opaque_callbacks_allowed') is False,'opaque policy callback claim forbidden')

def typed_runtime(evidence,*,job,invocation,context,raw):
 base=C.JOURNAL_ROOT+'/'+job['job_id'];identity=evidence.read(base+'/identity.json')
 action=list(map(json.loads,evidence.path(base+'/action_events.jsonl').read_bytes().splitlines()))
 iterator=list(map(json.loads,evidence.path(base+'/iterator_events.jsonl').read_bytes().splitlines()))
 completed=evidence.read(base+'/completion.json')
 for name in ('action_events.jsonl','iterator_events.jsonl'):evidence.watch(base+'/'+name)
 shared=dict(schema='formal_main_v2',version=C.VERSION,job_id=job['job_id'],invocation_sha256=job['invocation_sha256'],
  plan_sha256=invocation['plan_sha256'],scope_sha256=F.SCOPE_SHA,logical_trial_id=F.CELL,
  run_root=str(F.P/F.OUT),production_sources=invocation['production_sources'])
 F.require(all(identity.get(k)==v and completed.get(k)==v for k,v in shared.items()),'actual typed entry/plan/source identity differs')
 F.require(identity.get('actual_entrypoint')==C.BASE+'/entry.py'
  and identity.get('actual_scientific_adapter')==C.LEGACY and identity.get('actual_scientific_adapter_sha256')==C.LEGACY_SHA
  and identity.get('original_scientific_wrapper_executed') is False and identity.get('legacy_rows_inserted')==0
  and identity.get('ordinary_resume') is False and identity.get('full_scientific_trials')==600
  and identity.get('actually_allowed_trials')==[F.CELL] and identity.get('final_allowed') is False,'typed entry scope differs')
 expected_original={k:str(v) if isinstance(v,Path) else v for k,v in vars(context['original_args']).items()}
 expected_actual={k:str(v) if isinstance(v,Path) else v for k,v in vars(context['args']).items()}
 F.require(identity.get('original_argument_values')==expected_original and identity.get('actual_argument_values')==expected_actual
  and identity.get('original_arguments_to_actual')==context['args_diff'],'actual entry argument derivation differs')
 for rows,kind in [(action,'action'),(iterator,'iterator')]:
  F.require(rows and all(r.get('seq')==i and r.get('kind')=='Object_single_error_'+kind+'_event'
    and isinstance(r.get('utc'),str) for i,r in enumerate(rows)),'typed raw journal malformed/reordered')
 F.require(completed.get('status')=='returned' and completed.get('exit_code')==0 and completed.get('errors')==[]
  and completed.get('identity_sha256')==evidence.watch(base+'/identity.json')
  and completed.get('action_events_sha256')==evidence.watch(base+'/action_events.jsonl')
  and completed.get('iterator_events_sha256')==evidence.watch(base+'/iterator_events.jsonl')
  and completed.get('scientific_acceptance_inferred') is False,'typed completion does not bind actual raw runtime journals')
 runtime=context['runtime']
 F.require(identity.get('runtime_contract')==context['runtime_contract'],'actual runtime contract differs')
 assets=runtime.expected_asset_identities(project_root=F.P,source_root=F.S,contract=context['runtime_contract'],
  asset_contract=context['reference']['downstream_asset_compatibility'])
 runtime_proof=runtime.verify_runtime_events(action,context['runtime_contract'],expected_asset_identities=assets)
 reject_synthetic(runtime_proof,action,iterator)
 iterator_proof=E.verify_events(iterator,job_id=job['job_id'],raw_sha256=raw['raw_sha256'],
  raw_status=raw['result']['status'],raw_success=raw['result']['success'])
 # Bind actual loop evidence to the separately frozen exact derivation, not
 # merely to agreement of several attacker-controlled journal fields.
 derivation=iterator[0]['derivation']
 from cti_vla.evaluation import formal_trials as M
 import iterator as I
 _,_,expected=I.derive_loop(M,F.read(F.S,F.LOOP,F.LOOP_SHA))
 F.require(derivation==expected,'actual derived loop differs from reviewed source')
 sources=context['inputs']['config']['source_files']
 path='scripts/eval_formal_selector_libero.py'
 execute=E.compiled_function(F.read(F.S,path,sources[path]),F.S/path,'execute')
 adapter_run=E.compiled_function(F.read(F.P,C.LEGACY,C.LEGACY_SHA),F.P/C.LEGACY,'run')
 claims=dict(original_execute_code_sha256=I.codesig(execute),original_adapter_run_code_sha256=I.codesig(adapter_run))
 callbacks={name:I.codesig(I.nested(execute,name)) for name in ('factory','reseed','on_result')}
 claims['original_execute_callbacks']=callbacks
 path='src/cti_vla/evaluation/formal_runtime.py'
 methods={name:I.codesig(co) for name,co in E.class_codes(F.read(F.S,path,sources[path]),F.S/path,'FormalRolloutPolicy').items() if name!='<lambda>'}
 claims.update(policy_methods_code_sha256=methods,source_sha256=sources[path])
 token_path='src/cti_vla/models/openvla_oft_policy.py'
 claims['token_policy_methods_code_sha256']={name:I.codesig(co) for name,co in E.class_codes(
  F.read(F.S,token_path,sources[token_path]),F.S/token_path,'OpenVLAOFTTokenPolicy').items() if name!='<lambda>'}
 claims['token_policy_source_sha256']=sources[token_path]
 own=F.read(F.P,C.BASE+'/execution.py',invocation['production_sources'][C.BASE+'/execution.py'])
 install=E.compiled_function(own,F.P/C.BASE/'execution.py','install')
 guarded=I.nested(I.nested(install,'bindings'),'guarded')
 claims['guard_code_sha256']=I.codesig(guarded)
 validate_code_claims(iterator,claims)
 from cti_vla.evaluation import libero_runtime as L
 original,current,_=C.load(F.R,C.ACTION,C.ACTION_SHA).derive_function(L,F.read(F.S,F.RUNTIME,F.RUNTIME_SHA))
 saved=M.run_episode
 try:
  L.run_episode=M.run_episode=current
  current_proof=E.current_episode(M,L)
 finally:L.run_episode=original;M.run_episode=saved
 F.require(iterator[0].get('current_action')==iterator[1].get('current_action')==current_proof,'actual current action code/observation/constructor proof differs from frozen derivation')
 F.require(iterator[1]['policy_closure']['methods']==[
  dict(method_id=r['identity']['method_id'],identity=r['identity'],
   class_name='cti_vla.evaluation.formal_runtime.FormalRolloutPolicy') for r in context['manifest']['methods']],
  'actual policy closure differs from full original six methods')
 return dict(runtime=runtime_proof,iterator=iterator_proof)

def review(job_id,pull_receipt,*,project=F.R,state=None):
 F.require(Path(project)==F.R,'root raw review uses server R only')
 old,helper,evidence,actionreview,runtime,trajectory,trajectory_proof=validators(project=project)
 scheduler=C.load(project,C.SCHEDULER,C.SCHEDULER_SHA)
 state=json.loads((project/scheduler.STATE).read_text()) if state is None else state
 matches=[j for j in state['registered_jobs'] if str(j.get('job_id'))==str(job_id)]
 F.require(len(matches)==1,'uniquely registered new allocation required');registered=matches[0]
 F.require(registered.get('mode')==G.MODE and registered.get('logical_trial_id')==F.CELL
  and registered.get('stage_key')==C.STAGE_KEY and registered.get('pair_id')==F.PAIR
  and registered.get('run_root')==str(F.P/F.OUT),'wrong typed registered mode/cell/pair/output')
 F.require(registered.get('status')=='COMPLETED' and registered.get('exit_code')=='0:0'
  and registered.get('gpus')==1 and type(registered.get('elapsed_seconds')) is int and registered['elapsed_seconds']>0,
  'complete actual Slurm allocation required; anomalies retain cost and HOLD')
 F.require(not any(G.duplicate(j) for j in state['registered_jobs'] if str(j.get('job_id'))!=str(job_id)),
  'another linked attempt is registered')
 inv=evidence.read(C.INVOCATION)
 F.require(evidence.watch(C.INVOCATION)==registered['invocation_sha256'],'exact bound invocation differs')
 F.require(all(registered.get(k)==inv.get(k) and inv.get(k) for k in G.FIELDS),'terminal registered Slurm identity differs from exact invocation')
 context=W.verify_invocation(inv,expected_job_id=str(job_id))
 F.require(context['plan']['production_sources']==C.closure(Path(__file__).parent),'actual reviewer differs from registered source closure')
 # Original input/receipt/source/selection/checkpoint validation runs in full on
 # the genuine reference before the explicitly documented new-output projection.
 value=reference_value(evidence,scheduler,helper,state)
 value['invocation']['wrapper_sha256']=inv['production_sources'][C.BASE+'/entry.py']
 job=dict(registered,mode='development',suite='libero_object',method_ids=list(F.METHODS),
  source_sha256=scheduler.FROZEN_SHA256,adapter_sha256=C.LEGACY_SHA,
  execution_manifest_sha256=F.PINS[F.MANIFEST])
 jobs=[dict(j,mode='development') if str(j.get('job_id'))==str(job_id) else j for j in scheduler.formal_jobs(state)]
 candidate=old.pulled_candidate(evidence,scheduler,job,pull_receipt,jobs)
 config=evidence.read(F.OUT+'/config.json')
 value['checkpoint']=old.runtime_inputs(evidence,scheduler,value,config)
 adapter=old.adapters(evidence,scheduler,value,job,config,candidate['files'])
 # Exactly the already registered current-action offline amplitude derivation;
 # all original source/config/checkpoint/queue/cadence/report checks are unchanged.
 rollout=actionreview.clone(old.rollout,trajectory=trajectory)
 result=rollout(evidence,scheduler,value,job,config,adapter)
 inputs=context['inputs']
 parsed=parse_raw(evidence.path(F.OUT+'/trials.jsonl').read_bytes(),config=config,panel=context['inputs']['panel'],
  manifest=context['manifest'],job_id=str(job_id),inputs=inputs,project=project)
 F.require(result['expected_trials']==600 and result['completed_trials']==1 and result['scientific_complete'] is False
  and result['raw_invocation_job_ids']==[str(job_id)] and result['unfinished_attempts_unknown_cost']==0,
  'original full600 summary must remain partial1/600 with exactly one actual allocation')
 typed=typed_runtime(evidence,job=job,invocation=inv,context=context,raw=parsed)
 iterator_first=json.loads(evidence.path(C.JOURNAL_ROOT+'/'+str(job_id)+'/iterator_events.jsonl').read_bytes().splitlines()[0])
 F.require(adapter.get('frozen_trial_loop_code_sha256')==iterator_first['derivation']['original_code_sha256'] and adapter.get('frozen_execute_code_sha256')==iterator_first['original_execute_code_sha256'],'adapter original fields cannot impersonate derived loop execution')
 costs=old.allocation_cost(evidence,scheduler,[job],job,value['invocation'],result['raw_invocation_job_ids'])
 F.require(costs['all_attempt_gpu_seconds']==registered['elapsed_seconds'],'new allocation charged more than once')
 adoption=A.rebuild(inputs,project=project)
 A.require_independent(project,context['plan']['legacy_root_adoption_independent'],adoption)
 status=parsed['result']['status'];eligible=status=='completed'
 view=dict(schema='formal_main_v2',kind=C.RAW_KIND,status='passed_raw_reconstruction' if eligible else 'HOLD_new_policy_error',
  job_id=str(job_id),scope_sha256=F.SCOPE_SHA,logical_trial_id=F.CELL,legacy_equivalent_trials=599,
  actual_current_trials=1,original_historical_trials=600,all_attempts_retained=601,
  original_failure_retained=F.RESULT,root_legacy_adoption_sha256=C.ADOPTION_SHA,
  raw_sha256=parsed['raw_sha256'],source_closure=inv['production_sources'],
  original_full_summary=result['reconstructed_summary'],actual_status=status,actual_success=parsed['result']['success'],
  logical_reference_view_complete=eligible,logical_success_count=520+int(parsed['result']['success']) if eligible else None,
  scientific_complete_inferred_from_original_partial_report=False,
  legacy_GPU_seconds=6713,new_allocation_GPU_seconds=registered['elapsed_seconds'],
  unique_total_GPU_seconds=6713+registered['elapsed_seconds'],cost=costs,
  runtime_structure=typed,current_trajectory_derivation=trajectory_proof,
  production_admitted=False,independent_terminal_review_required=True,final_allowed=False,new_attempt_must_not_repeat=True)
 for path,h in evidence.files.items():
  if path.startswith(F.OUT+'/') or path.startswith(C.JOURNAL_ROOT+'/'+str(job_id)+'/'):
   F.require(candidate['files'].get(path)==h,'consumed actual runtime/raw file absent from complete terminal pull')
 evidence.unchanged()
 view['evidence_sha256']=dict(sorted(evidence.files.items()))
 return view

def consume(receipt,*,job_id,pull_receipt,project=F.R,state=None):
 # Re-execute actual source, raw, trajectory and runtime validation. Caller
 # booleans or another alleged consumer result never substitute for this run.
 rebuilt=review(job_id,pull_receipt,project=project,state=state)
 F.require(receipt==rebuilt,'claimed terminal receipt differs from real raw reconstruction')
 return rebuilt

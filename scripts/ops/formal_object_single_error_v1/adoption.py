"""Rebuild the actual root adoption from preserved bytes, never from status flags alone."""
import json
import numpy as np
import fixed as F
import constants as C

def rebuild(inputs,*,project=F.R):
 root=json.loads(F.read(project,C.ADOPTION,C.ADOPTION_SHA))
 table_raw=F.read(project,C.ROWS,C.ROWS_SHA)
 F.require(table_raw.endswith(b'\n'),'adoption rows require complete newline')
 table=[json.loads(x) for x in table_raw.splitlines()]
 expected=[]
 raw=inputs['raw']
 # Every reference identifies unchanged original bytes and the independently
 # reproduced finite action stream; source inference is not old instance capture.
 for p in inputs['per_trial']:
  a=p['old_runtime_replay']['executed_f64le_sha256'];b=p['current_runtime_replay']['executed_f64le_sha256']
  F.require(a==b,'legacy/current executed action proof differs')
  record=inputs['normal'][p['trial_id']]
  actions=np.asarray(record['executed_actions'],dtype='<f8')
  F.require(np.isfinite(actions).all() and F.sha(actions.tobytes())==a,'adoption action bytes differ from original raw')
  for k in ('start','result'):
   rr=p[k];part=raw[rr['byte_offset']:rr['byte_offset']+rr['bytes']]
   F.require(F.sha(part)==rr['sha256'] and json.loads(part)['trial_id']==p['trial_id'],'adoption byte reference differs')
  expected.append(dict(trial_id=p['trial_id'],method=p['method'],initial_state_sha256=p['initial_state_sha256'],
   source_job_id=p['source_job_id'],status='completed',success=p['success'],start=p['start'],result=p['result'],
   old_executed_f64le_sha256=a,current_executed_f64le_sha256=b,
   target_action_semantics_sha256=F.ACTION,origin='legacy_equivalent'))
 F.require(table==expected and len(table)==599 and len({x['trial_id'] for x in table})==599,'599 actual adoption rows differ')
 strict=dict(schema='formal_main_v2',kind='Object599_legacy_compatibility_root_adoption',
  status='passed_legacy599_only',reviewed_by='root',scope_sha256=F.SCOPE_SHA,
  counts={'actions':91945,'chunks':11720,'trials':599},legacy_equivalent_trials=599,current_wrapper_generated_trials=0,
  legacy_gpu_seconds=6713,raw_historical_trials=600,retained_policy_errors=1,retained_raw600=True,
  rejected_query8_unknown=True,negative_outcomes_retained=True,new_GPU_seconds=0,new_scientific_trials=0,
  whole600_admitted=False,typed_whole600_consumer_pending=True,target_action_semantics_sha256=F.ACTION,
  GPU_execution_authorized=False,final_allowed=False,final_release=False,actual_old_controller_instance_capture=False)
 F.require(all(root.get(k)==v for k,v in strict.items()),'root599 typed scope differs')
 r=C.ref(project,C.ROWS)
 F.require(root['rows']==root['legacy599_adoption_rows']==dict(**r,count=599),'root row binding differs')
 F.require(root['legacy_allocations']==inputs['scope']['legacy_allocations'],'legacy allocations changed')
 F.require(root['legacy_raw']==C.ref(project,F.RUN+'/trials.jsonl'),'root full old raw pin differs')
 F.require(root['legacy_independent_review']==C.ref(project,F.PROOF_ARCHIVE),'root independent proof differs')
 F.require(root['original_failed_trial']['trial_id']==F.CELL,'root retained failed cell differs')
 F.require(root['original_failed_trial']['start']==F.START and root['original_failed_trial']['result']==F.RESULT,'failed bytes must remain')
 F.require(root['root_rechecked_success_count']==sum(x['success'] for x in expected)==520,'root599 success count differs')
 return dict(schema='formal_main_v2',kind='Object599_adoption_raw_reconstruction',status='passed',
  root_adoption=C.ref(project,C.ADOPTION),rows=C.ref(project,C.ROWS),scope_sha256=F.SCOPE_SHA,
  legacy_equivalent_trials=599,current_generated_trials=0,successes=520,
  original_failed_trial_retained=True,original_GPU_seconds=6713,read_raw_bytes=len(raw),
  source_basis='Independent source/runtime replay equivalence; not a historical instance capture',
  complete600_admitted=False,GPU_authorized=False,new_scientific_trials=0,final_allowed=False)

def require_independent(project,reference,reconstruction):
 F.require(reference==C.ref(project,C.ADOPTION_INDEPENDENT) and reference['sha256']==C.ADOPTION_INDEPENDENT_SHA,'exact separately archived independent adoption review required')
 r=json.loads(F.read(project,C.ADOPTION_INDEPENDENT,C.ADOPTION_INDEPENDENT_SHA))
 F.require(r.get('schema')=='formal_main_v2' and r.get('kind')=='Object599_canonical_root_adoption_independent_review'
  and r.get('status')=='passed_legacy599_only' and r.get('reviewed_by')=='independent_goal_cpu_gate_2054'
  and r.get('root_adoption')==C.ref(project,C.ADOPTION) and r.get('adoption_rows')==C.ref(project,C.ROWS)
  and r.get('all599_exact_raw_start_result_and_executed_byte_links_verified') is True
  and r.get('successes')==520 and r.get('negative_outcomes')==79 and r.get('original_GPU_seconds_once')==6713
  and r.get('whole600_admitted') is False and r.get('production_admitted') is False
  and r.get('new_scientific_trials')==0 and r.get('unknown_query8_not_invented') is True,
  'actual separately reconstructed root599 review scope differs')
 return r

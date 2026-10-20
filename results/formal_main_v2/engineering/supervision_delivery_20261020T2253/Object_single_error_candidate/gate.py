"""Fail-closed CPU predicates for one explicit linked attempt; never submits."""
from __future__ import annotations
from datetime import datetime,timezone
import re
import json
import fixed as F

VERSION='formal-object-single-error-candidate-v1'
ACTIVE={'PENDING','RUNNING','CONFIGURING','COMPLETING','SUSPENDED','RESIZING'}
TERMINAL={'COMPLETED','FAILED','TIMEOUT','PREEMPTED','CANCELLED','OUT_OF_MEMORY','NODE_FAIL','BOOT_FAIL','DEADLINE'}
RECEIPT_NAMES=('root_legacy_adoption','root_repair','independent_runtime_review','runtime_readiness','root_submission_review')
BLOCKERS=[
 'Exact new parent/child adapter provenance integration has not been published or independently reviewed.',
 'No actual P canonical source installation or --verify has occurred.',
 'No exact native writer-lock/CAS pending/ACK gateway has been activated.',
 'No real one-cell execution or typed original-scientific terminal consumer has been accepted.',
 'The original599 proof has not been adopted by this CPU candidate.'
]


def sha_text(value):
 F.require(type(value) is str and re.fullmatch('[0-9a-f]{64}',value),'SHA256 required')
 return value


def canonical_ref(value,path=None):
 F.require(type(value) is dict and set(value)=={'path','sha256'},'exact canonical reference required')
 p=value['path'];F.require(type(p) is str and p.startswith('results/formal_main_v2/') and '..' not in p.split('/')
  and not any(x in p.lower() for x in ('sealed','/.local/')),'canonical nonsealed result reference required')
 if path is not None:F.require(p==path,'exact receipt path required')
 sha_text(value['sha256']);return value


def proposal(scope,bundle_sha256,token):
 F.check_scope(scope)
 sha_text(bundle_sha256)
 F.require(type(token) is str and re.fullmatch('[0-9a-f]{48}',token),'fresh48hex submission token required')
 return dict(schema='formal_main_v2',kind='Object_single_policy_error_correction_proposal',version=VERSION,
  suite='libero_object',stage='development',mode='linked_policy_error_correction',
  pair_id=F.PAIR,logical_trial_id=F.CELL,attempt_number=1,allowlist=[F.CELL],original_method_ids=list(F.METHODS),
  original_manifest=scope['original_manifest'],scope_sha256=F.sig(scope),bundle_sha256=bundle_sha256,
  action_semantics_sha256=F.ACTION,legacy_raw=scope['legacy_raw'],legacy_start=F.START,legacy_result=F.RESULT,
  all_prior_job_ids=list(F.JOBS),legacy_gpu_seconds=6713,output=str(F.P/F.OUT),
  submission_token=token,comment='cti-object-single-error-v1:'+token,
  ordinary_resume=False,fresh_reset=True,max_new_trials=1,max_submissions=1,auto_retry=False,
  stop_after=None,policy_watchdog_seconds=60.,runtime_seed=17,environment_seed=0,
  final_allowed=False,profile_allowed=False,scientific_settings_changed=False,
  source_root=str(F.S),new_ledger_expected_before_start='absent',new_initial_states=0)


def validate_proposal(value,scope):
 expected=proposal(scope,value.get('bundle_sha256'),value.get('submission_token'))
 F.require(value==expected,'proposal widened/changed original scientific identity or exact one-cell attempt')
 return value


def validate_receipts(objects,refs,plan,scope):
 F.require(set(objects)==set(refs)==set(RECEIPT_NAMES),'complete root/independent/runtime receipt set required')
 for key in RECEIPT_NAMES:
  raw=objects[key]
  F.require(type(raw) is bytes,'exact receipt file bytes required')
  row=json.loads(raw)
  canonical_ref(refs[key],F.EX+'/'+key+'.json')
  F.require(F.sha(raw)==refs[key]['sha256'],'receipt canonical object signature differs')
  F.require(row.get('schema')=='formal_main_v2' and row.get('status')=='passed' and row.get('blockers')==[]
   and row.get('proposal_sha256')==F.sig(plan) and row.get('scope_sha256')==F.sig(scope)
   and row.get('bundle_sha256')==plan['bundle_sha256'] and row.get('final_allowed') is False,'receipt incomplete or foreign')
  F.require(row.get('kind')==key and row.get('reviewed_by')==('independent' if key=='independent_runtime_review' else 'root'),'typed audit role mismatch')
 decoded={k:json.loads(v) for k,v in objects.items()}
 legacy=decoded['root_legacy_adoption']
 F.require(legacy.get('legacy_independent_review_sha256')==F.PINS[F.OLD_PROOF+'/independent_review.json']
  and legacy.get('legacy_equivalent_trials')==599 and legacy.get('current_wrapper_generated_legacy_trials')==0
  and legacy.get('raw_historical_trials')==600 and legacy.get('retained_policy_errors')==1
  and legacy.get('legacy_gpu_seconds')==6713,'root legacy adoption scope differs')
 canonical_ref(legacy.get('legacy_independent_review'),F.PROOF_ARCHIVE)
 F.require(legacy['legacy_independent_review']['sha256']==legacy['legacy_independent_review_sha256'],'legacy archived receipt differs')
 repair=decoded['root_repair']
 F.require(repair.get('original_failed_result')==F.RESULT and repair.get('all_prior_job_ids')==list(F.JOBS)
  and repair.get('ordinary_resume') is False and repair.get('new_attempt_limit')==1
  and repair.get('rejected_query8_unknown') is True and repair.get('old_ledger_modified') is False,'repair changed/erased original failed history')
 ind=decoded['independent_runtime_review']
 F.require(ind.get('typed_iterator_reviewed') is True and ind.get('typed_gateway_reviewed') is True
  and ind.get('typed_parent_child_provenance_reviewed') is True and ind.get('typed_terminal_consumer_reviewed') is True
  and ind.get('all_mode_capacity_and_pending_ACK_reviewed') is True,'incomplete production chain independent audit')
 ready=decoded['runtime_readiness']
 F.require(ready.get('actual_P_verified') is True and ready.get('production_chain_complete') is True
  and ready.get('original173_unchanged') is True and ready.get('actual_sources')==ready.get('expected_sources')
  and type(ready.get('actual_sources')) is dict and len(ready['actual_sources'])>=5
  and ready.get('same_registered_Object_base_and_all6_methods_verified') is True
  and ready.get('new_ledger_absent') is True,'actual P/all-method/source readiness missing')
 F.require(set(ready['expected_sources'])=={F.BASE+'/'+n for n in ('fixed.py','iterator.py','gate.py','terminal.py','scope.json')}
  and F.sig(ready['expected_sources'])==plan['bundle_sha256'],'actual runtime source closure must equal exact bundle')
 for checksum in ready['expected_sources'].values():sha_text(checksum)
 F.require(ready.get('actual_project_root')==str(F.P) and ready.get('source_root')==str(F.S),'actual P/source root identity required')
 F.require(decoded['root_submission_review'].get('exact_once_registered') is True,'root exact attempt review required')
 return dict(status='structural_receipts_valid_only',production_authorized=False)


def check_snapshot(snapshot,plan,now):
 F.require(type(now) is datetime and now.tzinfo is not None,'timezone-aware live check time required')
 keys={'kind','project','captured_utc','state_sha256','controller','registered_jobs','slurm_rows','pending',
       'reserved_gpu_slots','output_exists','ledger_exists','unknown_registered_activity'}
 F.require(set(snapshot)==keys and snapshot['kind']=='all_modes_registered_live_snapshot' and snapshot['project']=='CTI-VLA','complete all-mode snapshot required')
 stamp=datetime.fromisoformat(snapshot['captured_utc'].replace('Z','+00:00'))
 F.require(stamp.tzinfo is not None and 0<=(now-stamp).total_seconds()<=60,'fresh live snapshot required before locked transaction')
 sha_text(snapshot['state_sha256'])
 F.require(snapshot['controller']=={'job_id':'3034538','status':'COMPLETED','exit_code':'0:0','lifetime_lease_held':False},'completed training owner/lease must remain terminal')
 F.require(snapshot['pending']==[] and snapshot['unknown_registered_activity'] is False,'unreconciled pending/unknown activity HOLD; never clear/resubmit')
 F.require(snapshot['output_exists'] is False and snapshot['ledger_exists'] is False,'fresh exact output/ledger required')
 reg=snapshot['registered_jobs'];live=snapshot['slurm_rows']
 F.require(type(reg) is list and type(live) is list,'all-mode records required')
 F.require(len({j['job_id'] for j in reg})==len(reg) and len({j['job_id'] for j in live})==len(live),'duplicate registered/accounted allocation')
 lookup={j['job_id']:j for j in live}
 F.require(set(lookup)=={j['job_id'] for j in reg},'missing/unknown registered Slurm allocation')
 active=0
 for row in reg:
  F.require(row.get('project')=='CTI-VLA','only this project registered jobs may be managed')
  F.require(row.get('mode') in ('training','development','collect','engineering','full','components','linked_policy_error_correction'),'unknown registered mode HOLD')
  actual=lookup[row['job_id']]
  F.require(actual.get('state') in ACTIVE|TERMINAL and type(actual.get('gpus')) is int and actual['gpus']>=0,'unknown Slurm state/GPU accounting HOLD')
  # Any existing attempt tied to the old error blocks all future submit attempts, regardless of outcome.
  F.require(row.get('linked_original_result_sha256')!=F.RESULT['sha256']
   and row.get('output')!=plan['output'] and row.get('submission_token')!=plan['submission_token']
   and row.get('comment')!=plan['comment'],'existing exact correction/ACK/token/output forbids duplicate attempt')
  if actual['state'] in ACTIVE:
   F.require(actual['gpus']==1,'independent one-GPU capacity accounting required')
   F.require(row.get('pair_id')!=F.PAIR and row.get('logical_trial_id')!=F.CELL,'same pair/cell active job')
   active+=actual['gpus']
 reserve=snapshot['reserved_gpu_slots']
 F.require(type(reserve) is int and reserve>=0 and active+reserve<8,'all modes + reservation + new1 exceed8GPU slots')
 return dict(registered_active_gpu_slots=active,reserved_gpu_slots=reserve,slots_after_submit=active+reserve+1)


def prepare_pending_intent(plan,scope,snapshot,objects,refs,*,now,writer_lock_held,actual_state_sha256,invocation_sha256):
 validate_proposal(plan,scope);validate_receipts(objects,refs,plan,scope)
 capacity=check_snapshot(snapshot,plan,now)
 F.require(writer_lock_held is True and actual_state_sha256==snapshot['state_sha256'],'shared writer lock and exact CAS required')
 sha_text(invocation_sha256)
 # Pure intent, deliberately no state update or subprocess/sbatch operation.
 return dict(kind='Object_single_error_pending_intent',proposal_sha256=F.sig(plan),cell=F.CELL,
  token=plan['submission_token'],comment=plan['comment'],invocation_sha256=invocation_sha256,
  output=plan['output'],capacity=capacity,before_state_sha256=actual_state_sha256,
  mutation_performed=False,submit_performed=False,production_authorized=False,
  handoff_requirement='separately accepted native gateway persists pending with CAS before single sbatch; unknown ACK HOLD')


def inspect_candidate(plan,scope):
 validate_proposal(plan,scope)
 return dict(schema='formal_main_v2',kind='Object_single_error_candidate_readiness',status='HOLD_CPU_candidate_only',
  blockers=list(BLOCKERS),production_authorized=False,GPU_submissions=0,new_scientific_trials=0,final_allowed=False)

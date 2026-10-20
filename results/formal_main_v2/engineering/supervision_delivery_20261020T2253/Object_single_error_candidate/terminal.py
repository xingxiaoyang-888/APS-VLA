"""Read-only typed assembly candidate. Existing raw600 and new attempt remain distinct."""
from __future__ import annotations
import json
from types import SimpleNamespace
import fixed as F


def account_allocations(old,new):
 expected=[{'job_id':j,'gpus':1,'elapsed_seconds':s,'status':'COMPLETED','raw_status':'COMPLETED','exit_code':'0:0'} for j,s in zip(F.JOBS,F.ELAPSED)]
 F.require(old==expected,'all3 original allocations and6713seconds required exactly once')
 F.require(type(new) is list and len(new)==1,'exactly one new registered allocation required')
 row=new[0]
 F.require(set(row)==set(expected[0]) and type(row['job_id']) is str and row['job_id'].isdigit() and row['job_id'] not in F.JOBS
  and row['gpus']==1 and type(row['elapsed_seconds']) is int and row['elapsed_seconds']>=0,'new allocation identity/cost missing or duplicated')
 F.require(row['status'] in ('COMPLETED','FAILED','TIMEOUT','PREEMPTED','CANCELLED','OUT_OF_MEMORY','NODE_FAIL','BOOT_FAIL','DEADLINE')
  and row['raw_status'].split()[0].rstrip('+')==row['status'] and type(row['exit_code']) is str
  and ':' in row['exit_code'],'unknown/inconsistent allocation state')
 return dict(allocations=old+new,all_attempt_gpu_seconds=6713+row['elapsed_seconds'],legacy_gpu_seconds=6713,
  new_gpu_seconds=row['elapsed_seconds'],cost_at_allocation_level_not_per_trajectory=True)


def parse_new(raw,*,formal,panel,scope,job_id,run_signature):
 F.require(type(raw) is bytes and raw.endswith(b'\n'),'new append-only raw ledger must have complete LF tail')
 lines=raw.splitlines(keepends=True)
 F.require(len(lines)==3,'exact one actual invocation/start/result; no injected599 or ordinary resume')
 rows=[json.loads(x) for x in lines]
 F.require([r.get('event') for r in rows]==['invocation','start','result'],'new attempt event order differs')
 F.require(all(r.get('run_signature')==run_signature for r in rows),'foreign run signature')
 F.require(rows[0].get('slurm_job_id')==job_id and job_id not in F.JOBS
  and set(rows[0])=={'event','created_utc','slurm_job_id','run_signature'},'actual new invocation required')
 formal.validate_trial_identities(panel,F.METHODS,SimpleNamespace(events=rows))
 for row in rows[1:]:
  F.require(all(row.get(k)==v for k,v in scope['identity'].items()),'different logical cell/initial/reset identity')
 result=rows[2]
 F.require(type(result.get('success')) is bool and result.get('status') in ('completed','policy_error','infrastructure_error'),'unrecognized new result')
 F.require(result['status']=='completed' or result['success'] is False,'failure cannot be success')
 F.require(type(result.get('chunks')) is list and type(result.get('executed_actions')) is list,'raw new action/error evidence required')
 F.require(result.get('configured_wait_steps')==10 and result.get('action_chunk')==8 and result.get('runtime_seed')==17
  and result.get('environment_seed')==0,'new reset/RNG contract differs')
 return dict(rows=rows,raw_sha256=F.sha(raw),result=result,result_line_sha256=F.sha(lines[2]),
  result_line_bytes=len(lines[2]),result_line_offset=len(lines[0])+len(lines[1]))


def assemble_candidate(inputs,raw,new_config,new_allocations,*,formal,receipts):
 scope=F.check_scope(inputs['scope']);oldalloc=scope['legacy_allocations'];cost=account_allocations(oldalloc,new_allocations)
 F.require(F.sha(inputs['raw'])==scope['legacy_raw']['sha256'],'old600 ledger mutated before assembly')
 F.require(new_config['manifest']==inputs['manifest'] and new_config['registration_sha256']==inputs['config']['registration_sha256']
  and new_config['panel_signature']==inputs['config']['panel_signature'] and new_config['source_files']==inputs['config']['source_files']
  and new_config['policy_watchdog_seconds']==60.,'new config changed scientific source/manifest/panel/watchdog')
 parsed=parse_new(raw,formal=formal,panel=inputs['panel'],scope=scope,job_id=new_allocations[0]['job_id'],run_signature=F.sig(new_config))
 job=new_allocations[0];result=parsed['result']
 if job['status']!='COMPLETED' or job['exit_code']!='0:0' or result['status']=='infrastructure_error':
  return dict(status='HOLD_new_attempt_failed_or_incomplete',new_attempt_retained=True,cost=cost,auto_retry=False,
   legacy_policy_error_retained=True,original_ledger_unchanged=True,production_admitted=False,corrected_view=None)
 F.require(set(receipts)=={'root','independent'},'both complete original-scientific terminal reviews required')
 for role,row in receipts.items():
  F.require(row.get('kind')=='Object_single_error_full_terminal_consumer' and row.get('reviewed_by')==role
   and row.get('status')=='passed' and row.get('blockers')==[] and row.get('job_id')==job['job_id']
   and row.get('new_raw_sha256')==parsed['raw_sha256'] and row.get('original_raw_sha256')==scope['legacy_raw']['sha256']
   and row.get('original_config_manifest_model_checkpoint_source_environment_guards') is True
   and row.get('current_action_runtime_and_adapter_provenance_verified') is True
   and row.get('all_chunks_trajectory_hashes_statistics_rebuilt') is True
   and row.get('full100_initial_state_and6_method_identity_verified') is True
   and row.get('old599_compatibility_root_adopted') is True and row.get('final_allowed') is False,'incomplete typed terminal consumer evidence')
 F.require(receipts['root']!=receipts['independent'],'root cannot impersonate independent review')
 expected={formal._identity(inputs['panel'],s,m)['trial_id'] for s in inputs['panel']['states'] for m in F.METHODS}
 normal=inputs['normal']
 F.require(len(normal)==599 and set(normal)==expected-{F.CELL} and inputs['results'][F.CELL]['status']=='policy_error','599+exact1 mapping differs')
 # This is a view of references, never a new fabricated scientific ledger.
 refs={r['trial_id']:dict(origin='legacy_equivalent',raw=scope['legacy_raw'],result=r['result']) for r in inputs['per_trial']}
 refs[F.CELL]=dict(origin='one_linked_current_attempt',raw_sha256=parsed['raw_sha256'],
  result=dict(byte_offset=parsed['result_line_offset'],bytes=parsed['result_line_bytes'],sha256=parsed['result_line_sha256']))
 counts={m:dict(trials=0,success=0) for m in F.METHODS}
 for row in [*normal.values(),result]:
  counts[row['method']]['trials']+=1;counts[row['method']]['success']+=int(row['success'])
 F.require(set(refs)==expected and all(c['trials']==100 for c in counts.values()),'six-method100cell coverage must remain fixed')
 return dict(schema='formal_main_v2',kind='Object_single_error_linked_view_candidate',status='CPU_reconstructed_candidate_only',
  logical_cells=600,legacy_equivalent_cells=599,current_attempt_cells=1,raw_historical_attempts=600,new_attempts=1,
  unchanged_unique_initial_states=100,additional_independent_initial_states=0,
  retained_old_failure=dict(raw=scope['legacy_raw'],result=F.RESULT,status='policy_error',success=False,rejected_query8_unknown=True),
  references=refs,method_counts=counts,cost=cost,new_failure_is_retained_without_automatic_retry=True,
  production_admitted=False,root_global_release=False,original_ledger_rewritten=False)

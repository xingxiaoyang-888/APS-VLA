#!/usr/bin/env python3
"""CPU-only generation and falsification of a prospective protocol specification."""
from pathlib import Path
import copy,hashlib,json,math
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/goal_bounded_diagnostic_20261020T2358'
N=P/'results/formal_main_v2/engineering/goal_paired_input_gate_20261020T2156/attempt01'
O=P/'results/formal_main_v2/engineering/goal_prefix58_20261020T1825/attempt01'
sources={};checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def jb(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def check(x,label):
 checks.append({'check':label,'passed':bool(x)})
 if not x:raise ValueError(label)
def read(p,pin):
 b=p.read_bytes();check(sha(b)==pin,'source pin '+str(p));sources[str(p)]={'sha256':pin,'bytes':len(b)};return json.loads(b)
def write(name,v):
 p=D/name;check(p.parent==D and not p.exists(),'private nonoverwrite '+name)
 p.write_bytes(json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False).encode()+b'\n')
def validate_design(p,expected_rows,expected_methods,expected_environment):
 if p['status']!='CPU_specification_pending_root_and_independent_review':raise ValueError('not only a design')
 if p['row_count']!=200 or p['unique_development_states']!=100 or p['rows']!=expected_rows:raise ValueError('fixed complete200 identities/order changed')
 if p['method_identities']!=expected_methods or p['scientific_environment']!=expected_environment:raise ValueError('frozen science changed')
 if p['maximum_new_attempts']!=1 or p['normal_resume_old_terminal_ledger'] is not False or p['automatic_retry'] is not False:raise ValueError('duplicate or blind replay path')
 if type(p['maximum_control_steps']) is not int or p['maximum_control_steps']!=200*expected_environment['max_control_steps']:raise ValueError('control step bound changed')
 if type(p['maximum_policy_queries']) is not int or p['maximum_policy_queries']!=200*math.ceil(expected_environment['max_control_steps']/8):raise ValueError('query bound changed')
 if type(p['stop_after_trial_count']) is not int or p['stop_after_trial_count']!=200:raise ValueError('trial stop bound changed')
 if p['policy_watchdog_seconds']!=60.0:raise ValueError('original watchdog changed')
 if p['rows_signature_sha256']!=sha(jb(expected_rows)):raise ValueError('ordered identity signature changed')
 if p['panel_sha256']!='ce8e3d31ab8f7616c87dd4d4031af41825713907ac184c6ea5b01d9040985aa9':raise ValueError('original panel SHA changed')
 if p['old200_policy']!='retain_all200_as_historical_HOLD_nonadopted' or p['old200_selection_by_success'] is not False:raise ValueError('historical selective adoption')
 if p['paired_t0_before_B'] is not True or p['all_queries_pre_post_exact'] is not True or p['failure_before_next_environment_action'] is not True:raise ValueError('input guard weakened')
 if p['success_rate_threshold'] is not None or p['forced_old_actions'] is not False or p['raw_input_redaction'] is not False:raise ValueError('outcome tuning or lost evidence')
 if p['scientific_trials_added_now']!=0 or p['new_GPU_jobs_now']!=0 or p['production_ready'] is not False or p['final_release'] is not False:raise ValueError('CPU artifact used as permission')
 if p['required_future_gates']!=REQUIRED:raise ValueError('missing/duplicate/reordered root/capacity/identity/terminal gate')
 if p!=EXPECTED_PROTOCOL:raise ValueError('any remaining frozen prospective protocol field changed')
 return True
REQUIRED=[
 'independent_review_of_CPU_design_and_root_choice_of_full_replacement_policy',
 'new_versioned_full200_gate_source_and_exact_runtime_AST_projection_review',
 'actual_P_source_config_data_model_and_selected_checkpoint_revalidation',
 'original_scientific_consumer_extended_only_by_explicit_attempt_lineage',
 'root_bound_authorization_one_new_output_path_one_token_one_ACK_no_existing_pending_or_Goal_activity',
 'all_modes_max8_slots_writer_lock_CAS_and_full_duplicate_submission_protection',
 'full_raw_observation_action_runtime_storage_bound_reserved_before_dispatch',
 'original_consumer_plus_distinct_independent_terminal_review_before_counting_exact200_once',
 'all_prior_and_new_unique_Slurm_allocations_preserved_and_charged_once',
 'final_values_remain_sealed_no_global_release_inferred']
EXPECTED_PROTOCOL=read(D/'prospective_full200_specification.json','ed0b59bd1acbdab34658f5599f4969aa745e596348bf25d230a38c978aa652ad')
panel=read(N/'original_run/panel.json','ce8e3d31ab8f7616c87dd4d4031af41825713907ac184c6ea5b01d9040985aa9')
config=read(N/'original_run/config.json','07bbc7066a8c739622f175087e7af098735dd4bb1baeb98ff6d7634e2dc9ad07')
registration=read(R/'configs/experiments/formal_main_v2.json','a3f35d8e96d701c1a9ebadc2ad02259372cf6c91da6c9cb8d57c231892cf6ff9')
check(panel['split']=='development' and panel['suite']=='libero_goal' and len(panel['states'])==100,'only fixed development100')
methods=[m['identity'] for m in config['manifest']['methods']]
check([m['method_id'] for m in methods]==['A256_seed17','B256_seed17'],'exact original pair')
rows=[]
for s in panel['states']:
 for method in methods:
  rows.append({'ordinal':len(rows)+1,'trial_id':s['trial_id']+':'+method['method_id'],'state_trial_id':s['trial_id'],
    'task_id':s['task_id'],'task_name':s['task_name'],'source_state_index':s['source_state_index'],
    'initial_state_sha256':s['initial_state_sha256'],'method':method['method_id']})
historical=P/'results/formal_main_v2/libero_goal/downstream/development/5185766bb353c8e6/attempt01/trials.jsonl'
hb=historical.read_bytes();hp='41494deb99b5b498343a21b4e187599743aaa2383301c7337c57f7dbda591e57'
check(sha(hb)==hp,'old200 source pin');sources[str(historical)]={'sha256':hp,'bytes':len(hb)}
old=[json.loads(x) for x in hb.splitlines()];old=[x for x in old if x.get('event')=='result']
check(len(old)==200 and [x['trial_id'] for x in old]==[x['trial_id'] for x in rows],'replacement scope exactly all old200 ordered trialIDs')
# No success/outcome is read to select rows or configure the proposed protocol.
environment=registration['suites']['libero_goal']['environment']
check(environment['action_chunk']==8 and environment['wait_steps']==10 and environment['env_seed']==0 and environment['runtime_seed']==17,'unchanged environment')
protocol={
 'schema':'formal_main_v2','status':'CPU_specification_pending_root_and_independent_review','production_ready':False,
 'purpose':'Separate prospective input-integrity qualification from unavailable retrospective old-path causality; no automatic GPU request',
 'row_count':200,'unique_development_states':100,'rows':rows,'rows_signature_sha256':sha(jb(rows)),
 'panel_sha256':'ce8e3d31ab8f7616c87dd4d4031af41825713907ac184c6ea5b01d9040985aa9',
 'method_identities':methods,'scientific_environment':environment,'policy_watchdog_seconds':config['policy_watchdog_seconds'],
 'maximum_new_attempts':1,'maximum_control_steps':200*environment['max_control_steps'],
 'maximum_policy_queries':200*math.ceil(environment['max_control_steps']/8),
 'stop_after_trial_count':200,'future_output_path':'must be new unique root-authorized path; no path allocated by this CPU package',
 'old200_policy':'retain_all200_as_historical_HOLD_nonadopted','old200_selection_by_success':False,
 'normal_resume_old_terminal_ledger':False,'automatic_retry':False,'forced_old_actions':False,'raw_input_redaction':False,
 'paired_t0_before_B':True,'all_queries_pre_post_exact':True,'failure_before_next_environment_action':True,
 'success_rate_threshold':None,'new_GPU_jobs_now':0,'scientific_trials_added_now':0,'final_release':False,
 'required_future_gates':REQUIRED,
 'pass_criteria':[
 'All fixed200 identities execute exactly once with original ordered A/B, both frozen selected checkpoints and unchanged scientific settings.',
 'Every one of100 A/B initial pairs has identical five raw components and instruction bytes before B policy query; no altered seeds or forced observations.',
 'Every returned policy query preserves its input object/array identities, shapes, dtypes, bytes and instruction; all accepted returned chunks and executed actions are retained.',
 'Original environment/controller/action-slice and policy calls remain unchanged under a separately versioned passive full200 gate; CPU fixture is impossible in a real attempt.',
 'All200 trials and100 pair receipts have complete source/runtime/action/raw input evidence; ordinary valid task failures remain in denominator regardless of success.',
 'Clean complete Slurm terminal, original consumer, independent review, explicit root acceptance and exact unique allocation accounting all pass before current count increases by200 once.',
 'Passing means prospective protocol integrity only: does not prove old3053440 cause, old200 compatibility, bitwise replay of older trajectories, or final release.'],
 'fail_criteria':[
 'Any initial pair mismatch stops before B inference; any pre/post mutation stops before another environment action; preserve all prior rows/blobs/cost.',
 'Missing identity, mismatched source/config/checkpoint, missing raw event/blob, invalid chunk, unknown ACK, Slurm abnormal/unknown state or unexpected exception causes HOLD and no automatic retry.',
 'A partial attempt is not promoted to a whole200 dataset, and completed old terminal entries are not silently skipped as a repair.',
 'If full200 integrity cannot pass under the unchanged scientific protocol, Goal remains blocked; never alter hyperparameters, observations, seeds, checkpoints or delete failing trials to achieve acceptance.'],
 'retrospective_branch':{
 'available_now':'post-policy hash divergence only; old nonzero-query pre/post arrays and state are absent',
 'adoption_rule':'Existing old200 remains all-or-nothing HOLD; without separately sufficient historical proof it is not counted as current input-integrity-verified evidence.',
 'if_old_path_cannot_be_recovered':'Do not require an impossible reconstruction to certify a distinct prospective dataset. Root may instead predeclare a full200 replacement attempt, with original200 retained and excluded from current count as a whole.',
 'not_a_cause_claim':'A new full200 pass cannot retroactively identify or repair the old failure.',
 'no_automatic_transition':True}
}
check(validate_design(protocol,rows,methods,environment),'valid full fixed200 CPU specification')
tests=[]
for name,mutation in [
 ('max_control_steps_changed',lambda p:p.update(maximum_control_steps=59999)),
 ('max_queries_changed',lambda p:p.update(maximum_policy_queries=7601)),
 ('stop_after_changed',lambda p:p.update(stop_after_trial_count=58)),
 ('watchdog_changed',lambda p:p.update(policy_watchdog_seconds=61)),
 ('rows_signature_changed',lambda p:p.update(rows_signature_sha256='0'*64)),
 ('panel_SHA_changed',lambda p:p.update(panel_sha256='0'*64)),
 ('hidden_extra_gate_duplicate',lambda p:p['required_future_gates'].append(p['required_future_gates'][0])),
 ('retrospective_rule_changed',lambda p:p['retrospective_branch'].update(no_automatic_transition=False)),
 ('pass_condition_removed',lambda p:p['pass_criteria'].pop()),
 ('fractional_step_bound',lambda p:p.update(maximum_control_steps=60000.0)),
 ('drop_one_trial',lambda p:p['rows'].pop()),('change_order',lambda p:p['rows'].reverse()),
 ('change_checkpoint',lambda p:p['method_identities'][0].update(checkpoint_sha256='0'*64)),
 ('change_horizon',lambda p:p['scientific_environment'].update(max_control_steps=1)),
 ('more_attempts',lambda p:p.update(maximum_new_attempts=2)),
 ('resume_terminal_old',lambda p:p.update(normal_resume_old_terminal_ledger=True)),
 ('auto_retry',lambda p:p.update(automatic_retry=True)),
 ('select_old_successes',lambda p:p.update(old200_selection_by_success=True)),
 ('claim_old_adoption',lambda p:p.update(old200_policy='adopt_after_fresh_pass')),
 ('weaken_t0',lambda p:p.update(paired_t0_before_B=False)),
 ('weaken_all_query',lambda p:p.update(all_queries_pre_post_exact=False)),
 ('late_fail_after_action',lambda p:p.update(failure_before_next_environment_action=False)),
 ('success_threshold',lambda p:p.update(success_rate_threshold=0.5)),
 ('force_old_actions',lambda p:p.update(forced_old_actions=True)),
 ('drop_raw_inputs',lambda p:p.update(raw_input_redaction=True)),
 ('count_now',lambda p:p.update(scientific_trials_added_now=200)),
 ('authorize_GPU_now',lambda p:p.update(new_GPU_jobs_now=1)),
 ('premature_production_ready',lambda p:p.update(production_ready=True)),
 ('final_release',lambda p:p.update(final_release=True)),
 ('remove_capacity_gate',lambda p:p['required_future_gates'].remove('all_modes_max8_slots_writer_lock_CAS_and_full_duplicate_submission_protection'))]:
 v=copy.deepcopy(protocol);mutation(v)
 try:validate_design(v,rows,methods,environment)
 except ValueError as e:tests.append({'case':name,'rejected':True,'reason':str(e)})
 else:raise ValueError('negative protocol case was accepted '+name)
# Signed zero / serialization detail: compare logged command values by canonical JSON as well as numeric equality.
def result30(path,pin):
 raw=path.read_bytes();check(sha(raw)==pin,'signed command ledger pin');return [x for x in map(json.loads,raw.splitlines()) if x.get('event')=='result'][29]
a=result30(O/'original_run/trials.jsonl','984fdcf8a311d483f31c117aeeb34552a1971fa0b06f4db167e02b67ef8d039e')
b=result30(N/'original_run/trials.jsonl','60cceb3556ca25e190178b047d58e700cd55403d333a54cecac05116deaf1906')
check(jb(a['executed_actions'][:72])==jb(b['executed_actions'][:72]),'prior72 canonical JSON commands exactly equal including signed zero representation')
write('prospective_full200_specification_v2.json',protocol)
write('prospective_specification_CPU_tests_v2.json',{'kind':'synthetic protocol rejection tests, not a runtime/gateway implementation','positive_tests':1,'rejection_tests':len(tests),'negative_tests':tests,'checks':checks,'source_files':sources,'new_GPU_jobs':0,'scientific_trials_added':0,'independent_review_pending':True})
write('command_serialization_check_v2.json',{'prior72_canonical_JSON_identical':True,'sha256':sha(jb(a['executed_actions'][:72])),'count':72,
 'scope':'Same serialized numeric commands provided to env.step under common source. Old raw float buffer/dtype was not directly recorded, so no broader old-buffer claim is made.'})
print(json.dumps({'status':'CPU_design_only','row_count':200,'states':100,'max_control_steps':protocol['maximum_control_steps'],'max_queries':protocol['maximum_policy_queries'],'negative_tests':len(tests),'rows_signature':protocol['rows_signature_sha256']}))

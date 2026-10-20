"""Independent reconstruction of Object raw-diagnostic claims; no adoption."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,hashlib,json,math,time
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=Path(__file__).parent
checks=[];WATCH={}
def ck(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise ValueError(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(rel,pin):
 b=(R/rel).read_bytes();ck('pin_'+rel,sha(b)==pin);WATCH[rel]=pin;return b
def nodup(pairs):
 out={}
 for k,v in pairs:
  if k in out:raise ValueError('duplicate JSON field')
  out[k]=v
 return out
def decode(b):return json.loads(b,object_pairs_hook=nodup,parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))
def save(n,v):
 p=D/n
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 return {'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
def main():
 t=time.monotonic()
 original_script=read('.local/object599_diagnostic_20261020T2054/diagnose.py','07ce2a20883b56e9e5c61bbd5f0fc1bb92f3a49a66af92fec2742f9e89fb098a')
 original=decode(read('.local/object599_diagnostic_20261020T2054/diagnostic.json','9ff4f7adee16f01f390c31a0bb417acf7a85edd1668eb8806831a222fd352ac6'))
 details=decode(read(original['per_trial']['path'],original['per_trial']['sha256']))
 rel='results/formal_main_v2/libero_object/downstream/development/8c843c1d4ee8383c/attempt01/trials.jsonl';pin='d93ad5a4eb4ae3edb7a9b20e640a72fe4971ca0e4eeb62eea71acc4d71a257d1'
 raw=read(rel,pin);ck('P_raw_ledger_equal',sha((P/rel).read_bytes())==pin)
 runtime=read('src/cti_vla/evaluation/libero_runtime.py','2fc1bacbd1268a36f2e31451c70a650be4f8d0c8f6803e7c8b2a3d45f701c781')
 trials=read('src/cti_vla/evaluation/formal_trials.py','93a0971dbc8bbf4cb462490b0b00a337d92f015af83b798bb635163a9cb864f6')
 adapter=read('results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py','b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185')
 rr=decode(read('results/formal_main_v2/downstream_reviews/3021844.json','004a810edd7f097bbeec755315beed11bbfa86640a78ffd75ef0ff78a769ee37'))
 costs=rr['cost']['allocations'];ck('original_root_completed',rr['status']=='passed' and rr['scientific_complete'] is True)
 ck('exact_three_legacy_allocations',[(r['job_id'],r['elapsed_seconds'],r['gpus']) for r in costs]==[('3021394',386,1),('3021603',1401,1),('3021844',4926,1)])
 ck('6713GPU_seconds_retained_once',sum(r['elapsed_seconds']*r['gpus'] for r in costs)==original['all_original_allocation_GPU_seconds']==6713)
 # Structural proof: call counter and predict precede the range rejection,
 # while append(chunks) follows it. Thus missing query8 bytes cannot be recovered.
 tree=ast.parse(runtime);ep=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='run_episode')
 branch=next(x for x in ast.walk(ep) if isinstance(x,ast.If) and ast.unparse(x.test)=='not queue')
 items=[ast.unparse(x) for x in branch.body]
 call_index=next(i for i,x in enumerate(items) if x.startswith("result['policy_calls'] += 1"))
 predict_index=next(i for i,x in enumerate(items) if x.startswith('chunk = predict_chunk('))
 reject_index=next(i for i,x in enumerate(items) if x.startswith('if bool((np.abs(chunk.environment_actions) > 1.00001).any()):'))
 append_index=next(i for i,x in enumerate(items) if x.startswith("result['chunks'].append("))
 ck('query_counter_before_predict_before_guard_before_append',call_index<predict_index<reject_index<append_index)
 completed=next(x for x in ast.walk(tree) if isinstance(x,ast.FunctionDef) and x.name=='completed')
 ck('legacy_completed_includes_policy_error',"('completed', 'policy_error')" in ast.unparse(completed))
 ft=next(x for x in ast.parse(trials).body if isinstance(x,ast.FunctionDef) and x.name=='evaluate_formal_trials')
 ck('ordinary_resume_skips_legacy_terminal_trial',any(isinstance(x,ast.If) and "identity['trial_id'] in ledger.completed()"==ast.unparse(x.test) and any(isinstance(y,ast.Continue) for y in x.body) for x in ast.walk(ft)))
 methods=['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17'];pending=None;job=None;offset=0;invocations=[];events=Counter();completed_rows=[];error_rows=[];state_rows=defaultdict(list);seen=set();totals=Counter();per_method=defaultdict(Counter);newrecords=[]
 source_records={x['trial_id']:x for x in details['records_completed_candidates']+details['invalid_attempts_preserved']}
 for line,chunk in enumerate(raw.splitlines(keepends=True),1):
  if not chunk.endswith(b'\n'):raise ValueError('truncated record')
  row=decode(chunk);event=row['event'];events[event]+=1
  ref={'line':line,'byte_offset':offset,'bytes':len(chunk),'sha256':sha(chunk)};offset+=len(chunk)
  if event=='invocation':
   if pending is not None:raise ValueError('invocation split incomplete attempt')
   job=row['slurm_job_id'];invocations.append(job);continue
  if row['suite']!='libero_object' or row['split']!='development' or row['method'] not in methods or (row['runtime_seed'],row['environment_seed'],row['configured_wait_steps'],row['action_chunk'])!=(17,0,10,8):raise ValueError('legacy identity drift')
  if event=='start':
   if pending is not None:raise ValueError('nested start')
   pending=(row,ref);continue
  if event!='result' or pending is None or pending[0]['trial_id']!=row['trial_id']:raise ValueError('invalid terminal event')
  if row['trial_id'] in seen:raise ValueError('duplicate result')
  seen.add(row['trial_id']);start=pending[1];pending=None
  actions=np.array(row['executed_actions'],dtype='<f8');parts=[]
  for index,c in enumerate(row['chunks']):
   a=np.array(c['environment_actions'],dtype='<f8');b=np.array(c['normalized_actions'],dtype='<f8')
   if a.shape!=(8,7) or b.shape!=(8,7) or not np.isfinite(a).all() or not np.isfinite(b).all() or (np.abs(a)>1.00001).any() or c['control_step']!=8*index:raise ValueError('invalid retained chunk')
   if np.clip(a,-1.,1.).tobytes()!=a.tobytes():raise ValueError('retained action clip changes bytes')
   parts.append(a)
  stack=np.concatenate(parts,axis=0)
  if actions.shape!=(row['control_steps'],7) or stack[:len(actions)].tobytes()!=actions.tobytes() or row['wait_steps']!=10:raise ValueError('executed sequence differs')
  got=source_records[row['trial_id']]
  if got['start']!=start or got['result']!=ref or got['original_job_id']!=job or got['executed_float64le_sha256']!=sha(actions.tobytes()) or got['retained_chunks_float64le_sha256']!=sha(stack.tobytes()) or got['retained_chunks_max_abs']!=float(np.abs(stack).max()):raise ValueError('root per-row diagnosis differs')
  if got['adopted'] is not False or got['candidate_only'] is not True:raise ValueError('adoption leakage')
  state_rows[row['state_trial_id']].append((row['method'],row['initial_state_sha256'],row['chunks'][0]['observation_sha256'],row['task_id']))
  totals.update(chunks=len(parts),actions=len(actions))
  if row['status']=='completed':
   if row['policy_calls']!=len(parts) or row['termination'] not in ('environment_success','task_horizon'):raise ValueError('unexpected completion')
   completed_rows.append(row['trial_id']);per_method[row['method']].update(completed=1,chunks=len(parts),actions=len(actions),successes=int(row['success']))
  else:
   if row['status']!='policy_error' or row['success'] is not False or row.get('error')!='environment action outside normalized controller [-1, 1] range' or row.get('error_phase')!='policy':raise ValueError('unexpected invalid attempt')
   if (line,row['task_id'],row['source_state_index'],row['method'],row['control_steps'],row['policy_calls'],len(parts))!=(1073,8,49,'dense',56,8,7):raise ValueError('error locator differs')
   error_rows.append({'trial_id':row['trial_id'],'line':line,'recorded_actions':len(actions),'policy_calls':row['policy_calls'],'retained_chunks':len(parts),'missing_rejected_chunk_bytes':True})
  newrecords.append({'trial_id':row['trial_id'],'status':row['status'],'original_job':job,'result':ref,'returned_actions_SHA':sha(stack.tobytes()),'executed_actions_SHA':sha(actions.tobytes()),'adopted':False})
 ck('all_1203_events_complete',events=={'invocation':3,'start':600,'result':600} and pending is None and offset==len(raw))
 ck('same_invocation_history',invocations==['3021394','3021603','3021844'])
 ck('599_completed_plus1_retained_error',len(completed_rows)==599 and len(error_rows)==1)
 ck('600_trials_no_duplicates',len(seen)==600 and len(source_records)==600)
 ck('100_unique_states',len(state_rows)==100)
 ck('100_recorded_t0_pairs_across6_methods',all(len(rows)==6 and {r[0] for r in rows}==set(methods) and len({r[1] for r in rows})==len({r[2] for r in rows})==1 for rows in state_rows.values()))
 ck('10states_per_task',Counter(rows[0][3] for rows in state_rows.values())==Counter({i:10 for i in range(10)}))
 ck('counts_match_root',dict(per_method)==original['per_method_completed_only'] and totals=={'chunks':11727,'actions':92001} and original['retained_chunks']==11727 and original['retained_actions']==92001)
 ck('no_scientific_or_GPU_admission',original['accepted_scientific_trials_added']==0 and original['new_GPU_seconds']==0 and original['GPU_submission_authorized'] is False and original['production_reuse_authorized'] is False and original['final_release'] is False)
 rows_ref=save('independent_per_trial.json',{'rows':newrecords,'exception':error_rows,'ledger_sha256':pin,'diagnostic_only':True,'accepted_trials':0})
 for rel,pin in WATCH.items():ck('unchanged_'+rel,sha((R/rel).read_bytes())==pin)
 report={'schema':'formal_main_v2','kind':'Object_legacy600_raw_diagnostic_independent_audit','status':'passed_diagnostic_claims_only_not_compatibility_acceptance','reviewer':'/root/goal_cpu_gate_2054','independent_of_root_implementation':True,'root_diagnostic_sha256':'9ff4f7adee16f01f390c31a0bb417acf7a85edd1668eb8806831a222fd352ac6','check_count':len(checks),'checks':checks,'evidence_sha256':WATCH,'independent_rows':rows_ref,'legacy_results':600,'completed_candidates':599,'retained_policy_error':error_rows[0],'unique_development_states':100,'recorded_t0_mismatches':0,'retained_chunks':11727,'retained_actions':92001,'all_legacy_GPU_seconds_retained_once':6713,'new_GPU_seconds':0,'new_Slurm_queries':0,'new_scientific_trials':0,'accepted_scientific_trials':0,'production_reuse_authorized':False,'final_release':False,'limitations':['Recorded t0 hashes are post-query and are not proof of historical before-query arrays.','The rejected eighth chunk was not stored; its axis, amplitude and result under current semantics are unknown.','Numeric inactivity of clipping on stored chunks does not establish full model/controller/environment equivalence.','Exactly599 complete rows were checked regardless of success; all600 including policy_error remain immutable and none is admitted.','The existing ledger regards policy_error as terminal, so ordinary resume skips the failed ID; any replacement needs explicit typed lineage and fresh engineering/runtime admission.','The Long compatibility conclusion was not imported or generalized.'],'CPU_wall_seconds':time.monotonic()-t}
 out=save('independent_diagnostic.json',report);print(json.dumps({'report':out,'checks':len(checks),'accepted_trials':0,'new_GPU_jobs':0}))
if __name__=='__main__':main()

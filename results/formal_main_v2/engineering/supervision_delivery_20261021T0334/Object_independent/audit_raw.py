from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,collections,math
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/object_terminal_independent_20261021T0334'
B='results/formal_main_v2/preflight/heartbeat_20261021T1134'
N='results/formal_main_v2/libero_object/downstream/linked_policy_error_correction/task08_state0049_dense/attempt01'
O='results/formal_main_v2/libero_object/downstream/development/8c843c1d4ee8383c/attempt01'
J='results/formal_main_v2/object_single_error_invocations/3054409';EX='results/formal_main_v2/execution/object_single_error_v1'
CELL='libero_object:pick_up_the_chocolate_pudding_and_place_it_in_the_basket:state-0049:env-0:dense'
METHODS=['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17']
checks=[];evidence={}
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(n,b):
 if not b:raise AssertionError(n)
 checks.append(dict(name=n,passed=True))
def rb(root,n,pin=None):
 p=root/n;before=p.stat();b=p.read_bytes();after=p.stat()
 ck('stable_nonlinked:'+str(root)+':'+n,p.resolve()==p and (before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino))
 if pin:ck('exact_pin:'+n,sha(b)==pin)
 evidence[str(root)+'/'+n]={'sha256':sha(b),'bytes':len(b)};return b
obs=json.loads(rb(R,B+'/initial_observation.json','0c0520630396e633c5b417a401da18bd100974e79d5f962308cf892bd945ac41'))
sacct=obs['projection']['observation']['raw_sacct'];alloc={}
for line in sacct.splitlines():
 row=line.split('|')
 if row[0] in ['3021394','3021603','3021844','3054409']:
  ck('saved_allocation_unique:'+row[0],row[0] not in alloc);alloc[row[0]]={'status':row[1],'exit_code':row[2],'seconds':int(row[3]),'allocation':row[4],'node':row[5],'job_name':row[6]}
ck('all_four_terminal_unique_allocations',len(alloc)==4 and all(r['status']=='COMPLETED' and r['exit_code']=='0:0' and 'gres/gpu=1' in r['allocation'] for r in alloc.values()))
ck('old6713_new326_once',{j:r['seconds'] for j,r in alloc.items()}=={'3021394':386,'3021603':1401,'3021844':4926,'3054409':326})
raw=rb(P,N+'/trials.jsonl','ec9feefaa0bcdc2ea7514e9f5bea2bb01f828a1a2003ac7f20422f46cd663ece');ck('new_complete_three_lines',raw.endswith(b'\n') and len(raw.splitlines())==3)
rows=[json.loads(x) for x in raw.splitlines()];ck('one_new_real_invocation_start_result',[r['event'] for r in rows]==['invocation','start','result'] and rows[0]['slurm_job_id']=='3054409')
start,new=rows[1:];ck('same_failed_logical_cell',start['trial_id']==new['trial_id']==CELL and new['task_id']==8 and new['source_state_index']==49 and new['method']=='dense')
ck('new_actual_status_not_synthetic_success_inference',new['status']=='completed' and new['success'] is True and new['termination']=='environment_success')
oldraw=rb(R,O+'/trials.jsonl','d93ad5a4eb4ae3edb7a9b20e640a72fe4971ca0e4eeb62eea71acc4d71a257d1');ck('old_P_and_R_raw_identical',rb(P,O+'/trials.jsonl')==oldraw)
old={};starts={};oldjobs=[];locations={};offset=0;activejob=None
for lineno,line in enumerate(oldraw.splitlines(keepends=True),1):
 r=json.loads(line)
 if r['event']=='invocation':activejob=r['slurm_job_id'];oldjobs.append(activejob)
 elif r['event'] in ('start','result'):
  tid=r['trial_id'];target=starts if r['event']=='start' else old
  ck('old_no_duplicate_'+r['event']+':'+tid,tid not in target);target[tid]=r
  locations[(tid,r['event'])]={'byte_offset':offset,'bytes':len(line),'line':lineno,'sha256':sha(line)}
  if r['event']=='result':locations[(tid,'source_job_id')]=activejob
 offset+=len(line)
ck('old600_and_three_original_attempt_allocations',len(old)==len(starts)==600 and oldjobs==['3021394','3021603','3021844'])
failed=old[CELL];normal={k:v for k,v in old.items() if v['status']=='completed'}
ck('old_one_policy_error_preserved',len(normal)==599 and set(old)-set(normal)=={CELL} and failed['status']=='policy_error' and failed['success'] is False and failed['policy_calls']==8 and len(failed['chunks'])==7 and len(failed['executed_actions'])==56)
ck('old_failed_start_exact',locations[(CELL,'start')]=={'byte_offset':50238056,'bytes':738,'line':1072,'sha256':'6533a08978eb006c39304bcf97829e3cfd0eef2145be3418c8d8bb02adf49c51'})
ck('old_failed_result_exact',locations[(CELL,'result')]=={'byte_offset':50238794,'bytes':44183,'line':1073,'sha256':'d7f134683c6e01c8667731c6ca6807290d91d7816d28197f48232de9bc271eb0'})
for name,pin in [('config.json','ccbb680ade2c6cab783568ea34f2fd3d3ae9abb69a62e7088f53d7150dad27a5'),('panel.json','6b7e6dd9fb5b6351ee47c7bb30eab911e7c144d700cd88f7e5162641738b2d6a')]:
 ck('new_'+name+'_same_full_original',rb(P,N+'/'+name,pin)==rb(R,O+'/'+name,pin))
panel=json.loads((P/N/'panel.json').read_bytes());cfg=json.loads((P/N/'config.json').read_bytes());manifest=json.loads(rb(R,'results/formal_main_v2/execution/libero_object_development_first_pair_v1.json','34062573869c7b947fbd3c37b09da476bec673e8e16fc4ea49c6ce8c5932db5a'))
ck('full_fixed100states_10tasks',len(panel['states'])==100 and collections.Counter(s['task_id'] for s in panel['states'])=={i:10 for i in range(10)} and len({s['initial_state_sha256'] for s in panel['states']})==100)
ck('full_original_six_methods_preserved',[r['identity']['method_id'] for r in manifest['methods']]==METHODS and cfg['manifest']==manifest)
expected=[s['trial_id']+':'+m for s in panel['states'] for m in METHODS];ck('all600_expected_ids_old_complete',len(set(expected))==600 and set(expected)==set(old))
ck('full_environment_frozen',manifest['environment']=={'environment_seed':0,'runtime_seed':17,'wait_steps':10,'action_chunk':8,'max_steps':280})
identity_keys=['trial_id','state_trial_id','suite','split','task_id','task_name','source_state_index','initial_state_sha256','environment_seed','runtime_seed','action_chunk','configured_wait_steps','method']
ck('new_start_result_old_cell_identity_exact',all(start[k]==new[k]==failed[k]==starts[CELL][k] for k in identity_keys))
ck('new_full_reset_t0_matches_original_record',new['chunks'][0]['observation_sha256']==failed['chunks'][0]['observation_sha256']=='d6d8750d30da448f94f24f8f8a569de30cc1e825a60167807f54fb90b27677f3')
ck('same_state_all_six_old_t0_hashes',len({old[start['state_trial_id']+':'+m]['chunks'][0]['observation_sha256'] for m in METHODS})==1)
ck('new_19queries_145control_10warmup',len(new['chunks'])==new['policy_calls']==19 and len(new['executed_actions'])==new['control_steps']==145 and new['wait_steps']==new['configured_wait_steps']==10)
chunks=[];large=[]
for i,c in enumerate(new['chunks']):
 e=np.asarray(c['environment_actions'],dtype='<f8');a=np.asarray(c['normalized_actions'],dtype='<f8');chunks.append(e)
 ck('chunk_shape_finite_cadence:'+str(i),e.shape==(8,7) and a.shape==(8,7) and np.isfinite(e).all() and np.isfinite(a).all() and c['control_step']==8*i)
 z=c['metadata'];ck('dense_full512_original_order_no_future:'+str(i),z['method']=='dense' and z['suite']=='libero_object' and z['visual_tokens']==512 and z['per_camera_budgets']==[256,256] and z['retained_indices']==list(range(512)) and z['scorer_calls']==0 and z['future_head_calls']==0 and z['policy_calls']==z['packing_calls']==z['vision_calls']==1)
 if np.any(np.abs(e)>1.05):large.append({'query_index':i,'control_step':c['control_step'],'max_abs':float(np.max(np.abs(e))),'elements':int((np.abs(e)>1.05).sum())})
executed=np.asarray(new['executed_actions'],dtype='<f8');queued=np.concatenate(chunks)[:len(executed)]
ck('all145_executed_actions_exact_queue_bytes',executed.shape==(145,7) and np.isfinite(executed).all() and executed.tobytes()==queued.tobytes())
retained=[]
for i,c in enumerate(failed['chunks']):
 retained.append({'query_index':i,'old_observation_sha256':c['observation_sha256'],'new_observation_sha256':new['chunks'][i]['observation_sha256'],'observation_hash_equal':c['observation_sha256']==new['chunks'][i]['observation_sha256'],'environment_actions_equal':np.asarray(c['environment_actions'],dtype='<f8').tobytes()==chunks[i].tobytes()})
adoption_raw=rb(R,EX+'/legacy599_adoption_rows.jsonl','ac792e8d88f251f097f3f0e110e6c32aa45dbacd103404c0189b3bebf56ccb5e');adoption=[json.loads(x) for x in adoption_raw.splitlines()]
ck('adoption599_coverage_excludes_original_error',len(adoption)==599 and len({r['trial_id'] for r in adoption})==599 and {r['trial_id'] for r in adoption}==set(normal) and CELL not in {r['trial_id'] for r in adoption})
for row in adoption:
 tid=row['trial_id'];r=normal[tid];actions=np.asarray(r['executed_actions'],dtype='<f8')
 ck('adoption_exact_original_bytes_and_actions:'+tid,row['start']==locations[(tid,'start')] and row['result']==locations[(tid,'result')] and row['source_job_id']==locations[(tid,'source_job_id')] and row['old_executed_f64le_sha256']==row['current_executed_f64le_sha256']==sha(actions.tobytes()) and row['success']==r['success'] and row['status']=='completed' and np.isfinite(actions).all() and row['origin']=='legacy_equivalent')
ck('legacy599_all_79_negative_outcomes_retained',sum(r['success'] for r in adoption)==520 and sum(not r['success'] for r in adoption)==79)
logical={k:dict(v,origin='legacy_equivalent') for k,v in normal.items()};logical[CELL]=dict(new,origin='current_linked_correction')
ck('logical600_new1_old599_history601_distinct_attempts',len(logical)==600 and len(old)+1==601 and sum(r['success'] for r in logical.values())==521)
per_method={m:dict(trials=sum(r['method']==m for r in logical.values()),successes=sum(r['method']==m and r['success'] for r in logical.values()),legacy=sum(r['method']==m and r['origin']=='legacy_equivalent' for r in logical.values()),current=sum(r['method']==m and r['origin']=='current_linked_correction' for r in logical.values())) for m in METHODS}
per_task={str(t):{m:dict(trials=sum(r['task_id']==t and r['method']==m for r in logical.values()),successes=sum(r['task_id']==t and r['method']==m and r['success'] for r in logical.values())) for m in METHODS} for t in range(10)}
report=json.loads(rb(P,N+'/closed_loop_report.json','f9df08f6cc4dd9ccf6676931d5c7c3a5c3aefd4805140f689c30da70044d09a1'))
ck('original600_guard_report_remains_partial1_no_spoofed_completions',report['status']=='incomplete' and report['expected_trials']==600 and report['completed_trials']==1 and report['unique_initial_states']==100 and report['test_opened'] is False and report['trials_jsonl_sha256']==sha(raw))
identity=json.loads(rb(P,J+'/identity.json','a14952078ee5f92ae24d2b23721e0d03e6e39216e80408365b2a7202fb4c336d'));complete=json.loads(rb(P,J+'/completion.json','3fd481e5d668493e632cd6d13b6d61e89be0fc13935ceaa0c59e4ba52b2ef0ec'))
actionraw=rb(P,J+'/action_events.jsonl','8d40ed3c6498afb6ccd1977f2e6c47ad99705d6b7da310a54db825082ae69ac6');iteratorraw=rb(P,J+'/iterator_events.jsonl','c9427297ac267597f3a8445ea2c40f04d436d664e091b932d8d41e129230e86d')
ck('typed_completion_raw_hash_bindings',complete['identity_sha256']==sha((P/J/'identity.json').read_bytes()) and complete['action_events_sha256']==sha(actionraw) and complete['iterator_events_sha256']==sha(iteratorraw) and complete['status']=='returned' and complete['exit_code']==0 and complete['errors']==[] and complete['scientific_acceptance_inferred'] is False)
ck('typed_full600_selection_only_one_real_cell',identity['full_scientific_trials']==600 and identity['actually_allowed_trials']==[CELL] and identity['legacy_rows_inserted']==0 and identity['ordinary_resume'] is False and identity['original_scientific_wrapper_executed'] is False and identity['final_allowed'] is False)
for path,pin in identity['production_sources'].items():ck('actual_source_R_P:'+path,rb(R,path,pin)==rb(P,path,pin))
ck('exact_review_consumer_source',identity['production_sources']['scripts/ops/formal_object_single_error_v1/reviewer.py']=='c0aa1fc3d7c1607032897d7eede009bb989753daf58911d2b3351b4df7a030a2')
iterator=[json.loads(x) for x in iteratorraw.splitlines()];ck('typed_iterator_exact_lifecycle',[r['event'] for r in iterator]==['linked_iterator_installed','linked_call_checked','linked_loop_returned','linked_iterator_restored'] and iterator[2]['ledger_sha256']==sha(raw) and iterator[2]['attempts']==1 and iterator[3]['call_count']==1 and iterator[3]['returned'] is True)
paths=[]
for parent in [P/N,P/J]:
 for path in sorted(parent.rglob('*')):
  if path.is_file() and path.name not in ['.evaluation.lock']:
   n=path.relative_to(P).as_posix();b=rb(P,n);paths.append({'path':n,'sha256':sha(b),'bytes':len(b)})
for n in ['results/formal_main_v2/job_receipts/3054409.json','results/slurm/cti_object_linked_t8s49d1_3054409.out','results/slurm/cti_object_linked_t8s49d1_3054409.err']:
 b=rb(P,n);paths.append({'path':n,'sha256':sha(b),'bytes':len(b)})
ck('complete_exact13_nonweight_pull_members',len(paths)==13 and len({r['path'] for r in paths})==13)
for absolute,row in evidence.items():
 p=Path(absolute);ck('all_evidence_unchanged:'+absolute,p.stat().st_size==row['bytes'] and sha(p.read_bytes())==row['sha256'])
def out(name,v):
 p=D/name;p.open('x',encoding='utf-8').write(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
out('pull_required_files.json',dict(schema='formal_main_v2',kind='Object3054409_independent_exact_terminal_pull_requirements',files=paths,file_count=len(paths),not_pulled_by_this_auditor=True))
out('logical_view_diagnostics.json',dict(methods=per_method,per_task=per_task,logical_trials=600,legacy_trials=599,current_trials=1,successes=521,negative_outcomes=79,raw_attempts=601,old_failed_attempt_retained=True,original_query8_unknown=True,retained_first7_comparison=retained,new_current_amplitude_over_old_threshold=large,interpretation='New successful full-reset attempt, not reconstruction of the originally unrecorded eighth query. Logical view is provisional until complete original reviewer+consumer and root admission.'))
result=dict(schema='formal_main_v2',kind='Object3054409_independent_P_raw_precheck',status='passed_raw_precheck_full_consumer_pending',reviewed_by='independent',job_id='3054409',new_status=new['status'],new_success=new['success'],new_chunks=19,new_executed_actions=145,logical_trials=600,raw_attempts_retained=601,legacy599_successes=520,legacy599_negative_outcomes=79,logical_successes=521,per_method=per_method,allocated_GPU_seconds=dict(legacy=6713,new=326,total_once=7039),allocations=alloc,original_query8_unknown=True,old_raw_unchanged=True,original_full600_guard_preserved=True,original_review_and_consume_pending=True,production_admitted=False,final_allowed=False,new_GPU_submissions=0,new_Slurm_queries=0,state_writes=False,evidence=evidence,check_count=len(checks),checks=checks,utc=datetime.now(timezone.utc).isoformat())
out('raw_precheck.json',result)
print(json.dumps(dict(status=result['status'],checks=len(checks),files=len(paths),methods=per_method,raw_precheck_sha256=sha((D/'raw_precheck.json').read_bytes()),pull_required_sha256=sha((D/'pull_required_files.json').read_bytes())),ensure_ascii=False))

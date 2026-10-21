from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,importlib.util
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
B='results/formal_main_v2/preflight/heartbeat_20261021T0758';X='results/formal_main_v2/execution/object_single_error_v1';E='results/formal_main_v2/engineering/supervision_delivery_20261020T2253/Object599_independent';A='results/formal_main_v2/engineering/supervision_delivery_20261020T2156/Object_author';RUN='results/formal_main_v2/libero_object/downstream/development/8c843c1d4ee8383c/attempt01'
CELL='libero_object:pick_up_the_chocolate_pudding_and_place_it_in_the_basket:state-0049:env-0:dense';ACTION='9a5f5935100bb04bf8fb91f6405b94efc93de236b3a75896d0f08cdb2aa1ee02';SCOPE='2d63670412abc28d3217242151ebf82f309ea93c1bb0e90478d817cf58d4a7b4'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rawsha(b):return hashlib.sha256(b).hexdigest()
def ref(rel):p=R/rel;return dict(path=rel,sha256=h(p),bytes=p.stat().st_size)
def pin(rel,want):
 p=R/rel;assert p.resolve()==p and h(p)==want,rel
 return json.loads(p.read_bytes())
def pack(x):return (json.dumps(x,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode()
def write(rel,raw):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw)
def verify_archive(prefix,filename,want):
 m=pin(prefix+'/'+filename,want);paths=[]
 for row in m['files']:
  source_root=m['root'] if prefix==E else '.local/object_legacy_integration_20261020T2156'
  rel=Path(row['path']).relative_to(source_root).as_posix();p=R/prefix/rel
  assert p.resolve()==p and p.stat().st_size==row['bytes'] and h(p)==row['sha256'],str(p)
  paths.append(rel)
 assert len(paths)==len(set(paths))==m.get('file_count',len(paths));return m
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('adopt2358c',p);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';state_before=h(sp);assert state_before=='a0d4d98f112adc082a04789c764d8c6006a2133cb61834f4b0e2097f5b64fb10'
 state=json.loads(sp.read_bytes());assert state['pending_submission'] is None and len(state['autonomous_training_v1']['completed_pairs'])==36 and state['formal_main_progress']['completed_final_trials']==0
 am=verify_archive(A,'stage1_delivery_manifest_original.json','9020eb66c1746924379106baf19cd5d50318bf4283370b900785acba596c1992')
 im=verify_archive(E,'delivery_manifest_original.json','08dd6ededfa12ba7827784cb0809db0c57128ffc880df831a977e558bded10f3')
 ind=pin(E+'/independent_review.json','62c0a39784953b14f061ae7d161813f5e4bbfa5c8db39297e7047327b28463f7')
 assert ind['status']=='passed' and ind['blockers']==[] and ind['source_model_checkpoint_initial_state_controller_RNG_verified'] is True and ind['counts']=={'trials':599,'chunks':11720,'actions':91945}
 author=pin(A+'/Object599_candidate.json','6fe1247dcb1fc211fc226f6de8d225e8757a97efd774b244431b37329b074bb2')
 old=pin('results/formal_main_v2/downstream_reviews/3021844.json','004a810edd7f097bbeec755315beed11bbfa86640a78ffd75ef0ff78a769ee37')
 alloc=old['cost']['allocations'];assert [(x['job_id'],x['elapsed_seconds'],x['gpus'],x['status'],x['exit_code']) for x in alloc]==[('3021394',386,1,'COMPLETED','0:0'),('3021603',1401,1,'COMPLETED','0:0'),('3021844',4926,1,'COMPLETED','0:0')]
 assert old['cost']['all_attempt_gpu_seconds']==6713 and ind['all_original_GPU_seconds']==6713
 inv=pin('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');assert len(inv['files'])==173
 for rel,want in inv['files'].items():
  for base in (R,S,R/'snapshots/formal_main_v2_run_564be0995e'):assert h(base/rel)==want
 config=pin(RUN+'/config.json','ccbb680ade2c6cab783568ea34f2fd3d3ae9abb69a62e7088f53d7150dad27a5');panel=pin(RUN+'/panel.json','6b7e6dd9fb5b6351ee47c7bb30eab911e7c144d700cd88f7e5162641738b2d6a')
 manifest=pin('results/formal_main_v2/execution/libero_object_development_first_pair_v1.json','34062573869c7b947fbd3c37b09da476bec673e8e16fc4ea49c6ce8c5932db5a');assert config['manifest']==manifest
 methods=['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17'];assert [x['identity']['method_id'] for x in manifest['methods']]==methods and len(panel['states'])==100
 expected={q['trial_id']+':'+m:(q,m) for q in panel['states'] for m in methods};assert len(expected)==600
 raw=(R/RUN/'trials.jsonl').read_bytes();oldrawsha='d93ad5a4eb4ae3edb7a9b20e640a72fe4971ca0e4eeb62eea71acc4d71a257d1';assert rawsha(raw)==h(P/RUN/'trials.jsonl')==oldrawsha
 lines=raw.splitlines(keepends=True);offsets=[];pos=0;events=[];jobs=[];starts={};results={};sourcejobs={}
 for i,line in enumerate(lines):
  offsets.append(pos);pos+=len(line);row=json.loads(line);events.append(row)
  if row['event']=='invocation':jobs.append(row['slurm_job_id']);current=row['slurm_job_id']
  elif row['event']=='start':assert row['trial_id'] not in starts;starts[row['trial_id']]=row
  elif row['event']=='result':assert row['trial_id'] not in results and row['trial_id'] in starts;results[row['trial_id']]=row;sourcejobs[row['trial_id']]=current
  else:raise AssertionError('unknown raw event')
 assert jobs==['3021394','3021603','3021844'] and set(starts)==set(results)==set(expected)
 failed=pin(E+'/failed_trial_independent.json','4fdfbc8b6acd4dae54d49e8af4f8ed06224424c3a66dd7b75845da1af2ed1b80')
 proof_path=R/E/'per_trial_independent_599.jsonl';assert h(proof_path)=='ddba2cf9b392fd49e445d8a264605bc0832de5196c0c39d3a7c950160d186155';proofs=[json.loads(x) for x in proof_path.read_bytes().splitlines()]
 assert len(proofs)==599 and {x['trial_id'] for x in proofs}==set(expected)-{CELL}
 def exactrow(d,event):
  i=d['line']-1;assert offsets[i]==d['byte_offset'] and len(lines[i])==d['bytes'] and rawsha(lines[i])==d['sha256']
  row=events[i];assert row['event']==event;return row
 table=[];chunks=steps=successes=0
 for proof in proofs:
  tid=proof['trial_id'];start=exactrow(proof['start'],'start');result=exactrow(proof['result'],'result');state_row,method=expected[tid]
  assert start['trial_id']==result['trial_id']==tid and result==results[tid] and sourcejobs[tid]==proof['source_job_id']
  assert result['status']==proof['status']=='completed' and result['success']==proof['success'] and type(result['success']) is bool
  assert result['initial_state_sha256']==proof['initial_state_sha256']==state_row['initial_state_sha256'] and result['method']==method==proof['method']
  assert result['task_id']==state_row['task_id']==proof['task_id'] and result['source_state_index']==state_row['source_state_index']==proof['source_state_index']
  assert result['runtime_seed']==17 and result['environment_seed']==0 and result['wait_steps']==result['configured_wait_steps']==10 and result['action_chunk']==8
  values=np.asarray(result['executed_actions'],dtype='<f8');assert values.shape==(result['control_steps'],7) and np.isfinite(values).all()
  checksum=rawsha(values.tobytes());oldproof=proof['old_runtime_replay'];newproof=proof['current_runtime_replay']
  assert checksum==oldproof['executed_f64le_sha256']==newproof['executed_f64le_sha256'] and oldproof['all_wait_and_control_actions_f64le_sha256']==newproof['all_wait_and_control_actions_f64le_sha256']
  assert oldproof['new_GPU_or_simulator_execution'] is False and newproof['new_GPU_or_simulator_execution'] is False and oldproof['python_numpy_RNG_unchanged'] is True and newproof['python_numpy_RNG_unchanged'] is True
  assert len(result['chunks'])==proof['full_chunks']==result['policy_calls'] and result['control_steps']==proof['control_steps']
  steps+=len(values);chunks+=len(result['chunks']);successes+=int(result['success'])
  table.append(dict(trial_id=tid,start=proof['start'],result=proof['result'],source_job_id=proof['source_job_id'],initial_state_sha256=proof['initial_state_sha256'],old_executed_f64le_sha256=checksum,current_executed_f64le_sha256=checksum,target_action_semantics_sha256=ACTION,origin='legacy_equivalent',method=method,success=result['success'],status='completed'))
 assert (len(table),chunks,steps)==(599,11720,91945)
 bad=exactrow(failed['result'],'result');bs=exactrow(failed['start'],'start');assert bad['trial_id']==bs['trial_id']==CELL and bad['status']=='policy_error' and bad['success'] is False and bad['policy_calls']==8 and len(bad['chunks'])==7 and len(bad['executed_actions'])==56
 assert sum(x['status']=='policy_error' for x in results.values())==1 and failed['rejected_query8_chunk_unknown'] is True
 assert h(sp)==state_before and h(P/RUN/'trials.jsonl')==h(R/RUN/'trials.jsonl')==oldrawsha
 table_raw=b''.join(pack(x) for x in table)
 row_ref=dict(path=X+'/legacy599_adoption_rows.jsonl',sha256=rawsha(table_raw),bytes=len(table_raw),count=599)
 receipt=dict(schema='formal_main_v2',kind='Object599_legacy_compatibility_root_adoption',status='passed_legacy599_only',reviewed_by='root',utc=datetime.now(timezone.utc).isoformat(),scope_sha256=SCOPE,
  legacy_independent_review=ref(E+'/independent_review.json'),legacy_independent_review_sha256=h(R/E/'independent_review.json'),legacy_independent_per_trial=ref(E+'/per_trial_independent_599.jsonl'),author_compatibility_proof=ref(A+'/Object599_candidate.json'),legacy_raw=ref(RUN+'/trials.jsonl'),original_root_review=ref('results/formal_main_v2/downstream_reviews/3021844.json'),
  original_manifest=ref('results/formal_main_v2/execution/libero_object_development_first_pair_v1.json'),original_panel=ref(RUN+'/panel.json'),original_config=ref(RUN+'/config.json'),legacy_allocations=alloc,legacy_gpu_seconds=6713,legacy_equivalent_trials=599,current_wrapper_generated_trials=0,raw_historical_trials=600,retained_policy_errors=1,rows=row_ref,legacy599_adoption_rows=row_ref,
  original_failed_trial={k:failed[k] for k in ('trial_id','task_id','source_state_index','method','initial_state_sha256','start','result','policy_calls','recorded_actions','recorded_chunks')},rejected_query8_unknown=True,retained_raw600=True,whole600_admitted=False,
  target_action_semantics_sha256=ACTION,new_scientific_trials=0,new_GPU_seconds=0,final_release=False,final_allowed=False,GPU_execution_authorized=False,typed_whole600_consumer_pending=True,
  historical_environment_basis=ind['historical_environment_basis'],actual_old_controller_instance_capture=False,counts={'trials':599,'chunks':11720,'actions':91945},negative_outcomes_retained=True,root_rechecked_success_count=successes,
  future_reference_view_requirement='599 legacy rows plus one explicitly linked new actual trial only after separate audited production chain, actual P verification, unique root submission and terminal root+independent review. This receipt adds no current-action or complete-batch scientific counts.',
  state_sha256_before=state_before,source173_verified_in_R_S_and_alias=True,source_archives_verified={'author_files':len(am['files']),'independent_files':len(im['files'])})
 assert not (R/X/'root_legacy_adoption.json').exists() and not (R/X/'legacy599_adoption_rows.jsonl').exists()
 write(row_ref['path'],table_raw);write(X+'/root_legacy_adoption.json',pack(receipt))
 write(B+'/Object599_root_evidence_review.json',pack(dict(status='root_legacy599_adoption_only',adoption=ref(X+'/root_legacy_adoption.json'),rows=row_ref,state_sha256_unchanged=state_before,all_original_GPU_seconds=6713,old_error_retained=True,new_scientific_trials=0,new_GPU_seconds=0,whole600_admitted=False,final_release=False)))
 assert h(sp)==state_before
 print(json.dumps({'status':receipt['status'],'adoption':ref(X+'/root_legacy_adoption.json'),'rows':row_ref,'counts':receipt['counts'],'new_scientific_trials':0,'state_unchanged':state_before}))
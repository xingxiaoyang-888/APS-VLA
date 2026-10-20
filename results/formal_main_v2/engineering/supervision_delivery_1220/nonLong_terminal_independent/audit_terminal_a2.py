"""Independent terminal reconstruction of two registered action-v1 development jobs."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,sys,time,traceback,types
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/nonLong_terminal_independent_1220'
REVIEWER='scripts/ops/formal_action_deployment_v1/reviewer.py'
CONSUMER='scripts/ops/formal_action_deployment_v1/consumer.py'
RPIN='9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd'
CPIN='16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
IPIN='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
PINNED_INPUTS={
 'results/formal_main_v2/pulls/20261020T122634Z_f16248744f18/receipt.json':'6deff3b3ba9facde8add9e038ed466b2efd2f96f645296cea57b30e3537423c0',
 'results/formal_main_v2/preflight/heartbeat_20261020T2020/terminal_jobs_snapshot.json':'c5c2ff31118b2b519666fb74547369a986a1b0875ac89a846ad6a8bd708ed3b2',
 'results/formal_main_v2/preflight/heartbeat_20261020T2020/terminal_pull.json':'81dde02267ddd1beac45d0f8978ecc353c4a3d19a6042abd723bb2e3d2619b86'}
JOB_INPUTS={
 '3048572':{'suite':'libero_spatial','max_steps':220,'allocated':2365,
  'auth_sha':'4a47032c83c03e81ac1297aa4c3f4ff31fc780a700990e7cb335c89cf65dbab4',
  'failure_sha':'a6d1d97c5fa91328409555ae63d0f9422ea7ce591a54e9d4bbbfb9adc153f1cd',
  'ACK_sha':'be68ec88e204cab305c9ecb8c96e1ca69543787bacd13fe3a05624bddf881c6b'},
 '3048581':{'suite':'libero_object','max_steps':280,'allocated':2186,
  'auth_sha':'9ee17e773f283ff81ca70e25ed0ab8afac7abf5ce5de73ef81625db768b0509b',
  'failure_sha':'fc3066c3de9279d808aab8dee9916521cfd37b61e353b253db19385a415ca484',
  'ACK_sha':'49865693b6d0c05be6d491f50ffeba51aef109c4e4847398c7adfcc7ead7be73'}}
inputs={}
def sha(b):return hashlib.sha256(b).hexdigest()
def read(path,pin=None):
 path=Path(path);assert path.is_file() and not path.is_symlink()
 assert path.suffix not in {'.pt','.pth','.bin','.safetensors','.ckpt','.pkl','.pickle','.pruned_init','.init'}
 assert not any(x in path.parts for x in ['test','final','weights','checkpoints'])
 b=path.read_bytes();h=sha(b)
 assert pin is None or h==pin,(str(path),h,pin)
 if str(path) in inputs:assert inputs[str(path)]['sha256']==h
 inputs[str(path)]={'sha256':h,'bytes':len(b)}
 return b
def jread(path,pin=None):return json.loads(read(path,pin))
def put(name,value):
 p=D/name;assert not p.exists(),str(p)
 b=(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
 p.write_bytes(b);return {'path':str(p.relative_to(R)),'sha256':sha(b),'bytes':len(b)}
def module(rel,pin,name):
 code=read(R/rel,pin);m=types.ModuleType(name);m.__file__=str(R/rel);m.__package__=''
 sys.modules[name]=m;exec(compile(code,m.__file__,'exec'),m.__dict__);return m
def ref(rel):return {'path':rel,'sha256':inputs[str(R/rel)]['sha256']}
def require_finite(x):
 a=np.asarray(x,dtype=np.float64);assert np.isfinite(a).all();return a
started=time.monotonic();cpu=time.process_time()
try:
 bindings=jread(D/'root_bindings.json','03ca8766082edeb4cf6b3254053d96ec0161802b45c1192e623eb0a4d36e5646')
 assert set(bindings)=={'3048572','3048581'}
 for path,pin in PINNED_INPUTS.items():read(R/path,pin)
 pull=jread(R/next(iter(PINNED_INPUTS)))
 snap=jread(R/list(PINNED_INPUTS)[1])
 assert set(pull['requested_job_ids'])==set(JOB_INPUTS)
 assert pull['weights_copied'] is False and pull['sealed_initial_states_copied'] is False
 assert len(pull['files'])==24 and pull['status']=='verified_nonweight_snapshot'
 for row in pull['files']:
  assert row['local_path']==str(R/row['relative']) and row['path']==str(P/row['relative'])
  a=read(R/row['relative'],row['sha256']);b=read(P/row['relative'],row['sha256'])
  assert a==b and len(a)==row['bytes']
 inv=jread(R/INV,IPIN);assert len(inv['files'])==173
 for rel,pin in inv['files'].items():
  read(R/rel,pin);read(S/rel,pin)
 rv=module(REVIEWER,RPIN,'_independent_nonLong_reviewer_1220')
 evidence=rv.Evidence(R);consumer=rv.load(evidence,CONSUMER,CPIN)
 combined={};paired_table=[];full_counts={'trials':0,'chunks':0,'executed_actions':0,'allocated_gpu_seconds':0}
 all_trial_ids=set()
 for jid,expected in JOB_INPUTS.items():
  suite=expected['suite'];matches=[j for j in snap['registered_jobs'] if j['job_id']==jid]
  assert len(matches)==1;job=matches[0]
  assert job['suite']==suite and job['status']=='COMPLETED' and job['exit_code']=='0:0'
  assert job['gpus']==1 and job['elapsed_seconds']==expected['allocated']
  rootref=bindings[jid];root=jread(R/rootref['path'],rootref['sha256'])
  assert root['pull_ref']['path']==next(iter(PINNED_INPUTS))
  rebuilt=consumer.review_downstream_output(evidence,rootref,expected_stage='development',
     suite=suite,run_root=job['run_root'],require_complete=True)
  assert rebuilt['scientific_complete'] and rebuilt['completed_trials']==rebuilt['expected_trials']==200
  assert rebuilt['execution_version']=='formal-downstream-action-v1'
  assert rebuilt['final_release'] is False and rebuilt['final_state_values_read'] is False and rebuilt['weights_read'] is False
  assert rebuilt['cost']['current_gpu_seconds']==rebuilt['cost']['all_attempt_gpu_seconds']==expected['allocated']
  assert len(rebuilt['cost']['allocations'])==1 and rebuilt['cost']['allocations'][0]['job_id']==jid
  for rel,h in rebuilt['evidence_sha256'].items():read(R/rel,h)
  output=Path(job['run_root']).relative_to(P)
  cfg=jread(R/output/'config.json');panel=jread(R/output/'panel.json');report=jread(R/output/'closed_loop_report.json')
  manifest=cfg['manifest'];environment={'action_chunk':8,'environment_seed':0,'max_steps':expected['max_steps'],'runtime_seed':17,'wait_steps':10}
  assert manifest['environment']==environment and manifest['suite']==suite and manifest['split']=='development'
  assert jread(R/manifest['development_panel'],manifest['development_panel_sha256'])==panel
  assert panel['suite']==suite and panel['split']=='development' and panel['environment_seed']==0
  states={r['trial_id']:r for r in panel['states']}
  assert len(states)==100 and len(panel['task_catalog'])==10
  assert Counter(s['task_id'] for s in states.values())=={t:10 for t in range(10)}
  identities={m['identity']['method_id']:m['identity'] for m in manifest['methods']}
  assert set(identities)=={'A128_seed23','B128_seed23'}
  validation_diagnostics={};token_pairs=[]
  for method in manifest['methods']:
   identity=method['identity']
   assert identity['suite']==suite and identity['training_seed']==23 and identity['visual_tokens']==128
   assert identity['future_head_deployed'] is False and identity['training_complete'] is True
   assert cfg['watched_files'][method['checkpoint']]==identity['checkpoint_sha256']
   receipt=jread(R/method['receipt'])
   assert rv.signature(receipt)==identity['deployment_receipt_sha256']
   assert receipt['checkpoint_sha256']==identity['checkpoint_sha256']
   selection=min(receipt['evaluations'],key=lambda r:(r['validation_metric'],r['update']))
   assert selection['update']==receipt['metadata']['update']
   validation_relative=str(Path(selection['artifact_path']).relative_to(P))
   validation=jread(R/validation_relative,selection['artifact_sha256'])
   assert validation['metric']=='task_macro_hard_validation_teacher_l1'
   assert validation['update']==selection['update'] and validation['arm']==identity['method']
   assert validation['validation_metric']==selection['validation_metric']==receipt['metadata']['validation_metric']
   teacher=sum(r['teacher_l1'] for r in validation['per_task'].values())/len(validation['per_task'])
   demo=sum(r['demonstration_l1'] for r in validation['per_task'].values())/len(validation['per_task'])
   assert teacher==validation['validation_metric'] and demo==validation['demonstration_l1']
   validation_diagnostics[identity['method']]={'selected_update':selection['update'],
      'hard_validation_teacher_L1_task_equal':teacher,'hard_validation_demonstration_L1_task_equal':demo,
      'validation_windows':validation['windows'],'validation_tasks':validation['tasks'],
      'validation_ref':{'path':validation_relative,'sha256':selection['artifact_sha256']},
      'deployment_receipt_raw_sha256':inputs[str(R/method['receipt'])]['sha256'],
      'deployment_receipt_canonical_JSON_sha256':identity['deployment_receipt_sha256'],
      'checkpoint_sha256':identity['checkpoint_sha256'],
      'scope':'Selected-checkpoint offline hard-pruning validation diagnostic; not closed-loop action error.'}
  raw=read(R/output/'trials.jsonl')
  assert raw.endswith(b'\n') and sha(raw)==report['trials_jsonl_sha256']
  rows=[rv.json_bytes(x) for x in raw.splitlines()]
  assert Counter(r['event'] for r in rows)=={'invocation':1,'start':200,'result':200}
  assert rows[0]['event']=='invocation' and rows[0]['slurm_job_id']==jid
  rsig=rv.signature(cfg);assert all(r['run_signature']==rsig for r in rows)
  active={};finished={};first_obs={};chunks=0;steps=0;last_time=None
  for row in rows:
   t=datetime.fromisoformat(row['created_utc']);assert t.tzinfo is not None
   assert last_time is None or t>=last_time;last_time=t
   if row['event']=='invocation':continue
   tid=row['trial_id'];sid=row['state_trial_id'];method=row['method']
   assert sid in states and method in identities and tid==sid+':'+method
   s=states[sid]
   for k in ['task_id','task_name','source_state_index','initial_state_sha256']:assert row[k]==s[k]
   assert row['suite']==suite and row['split']=='development'
   assert row['environment_seed']==0 and row['runtime_seed']==17 and row['action_chunk']==8 and row['configured_wait_steps']==10
   if row['event']=='start':
    assert tid not in active and tid not in finished;active[tid]=row;continue
   assert tid in active and tid not in finished;active.pop(tid)
   assert row['status']=='completed' and type(row['success']) is bool and row['wait_steps']==10
   controls=row['control_steps'];assert type(controls) is int and 0<controls<=expected['max_steps']
   assert row['termination']==('environment_success' if row['success'] else 'task_horizon')
   if not row['success']:assert controls==expected['max_steps']
   assert [c['control_step'] for c in row['chunks']]==list(range(0,controls,8))
   assert row['policy_calls']==len(row['chunks'])
   env_chunks=[];identity=identities[method]
   for chunk in row['chunks']:
    a=require_finite(chunk['environment_actions']);n=require_finite(chunk['normalized_actions'])
    assert a.shape==n.shape==(8,7)
    m=chunk['metadata'];assert m['suite']==suite and m['method']==identity['method']
    assert m['training_seed']==23 and m['selector_checkpoint_sha256']==identity['checkpoint_sha256']
    assert m['pair_id']==identity['pair_id'] and m['visual_tokens']==128 and m['per_camera_budgets']==[64,64]
    assert m['future_head_calls']==0 and m['language_cache']=='disabled'
    assert m['vision_calls']==m['scorer_calls']==m['packing_calls']==m['policy_calls']==1
    assert m['packing_version']=='oft-original-positions-v1'
    assert m['action_version']=='libero-oft-boundsq99-gripper-sign-invert-chunk8-v1'
    indices=m['retained_indices']
    assert indices==sorted(set(indices)) and len(indices)==128 and all(type(x) is int and 0<=x<512 for x in indices)
    assert sum(x<256 for x in indices)==64
    assert isinstance(chunk['observation_sha256'],str) and len(chunk['observation_sha256'])==64
    env_chunks.append(a)
   executed=require_finite(row['executed_actions'])
   assert executed.shape==(controls,7) and np.array_equal(executed,np.concatenate(env_chunks)[:controls])
   assert first_obs.setdefault(sid,row['chunks'][0]['observation_sha256'])==row['chunks'][0]['observation_sha256']
   assert require_finite([row['wall_seconds'],row['attempt_wall_seconds']]).min()>=0
   finished[tid]=row;chunks+=len(row['chunks']);steps+=controls
  assert not active and len(finished)==200 and len(first_obs)==100
  assert not (all_trial_ids & set(finished));all_trial_ids.update(finished)
  per_task=[];discord=Counter();method_totals=Counter()
  for task in range(10):
   selected=sorted((s for s in states.values() if s['task_id']==task),key=lambda s:s['source_state_index'])
   local=Counter();tot=Counter()
   for state in selected:
    sid=state['trial_id'];a=finished[sid+':A128_seed23']['success'];b=finished[sid+':B128_seed23']['success']
    achunk=finished[sid+':A128_seed23']['chunks'][0];bchunk=finished[sid+':B128_seed23']['chunks'][0]
    assert achunk['control_step']==bchunk['control_step']==0
    assert achunk['observation_sha256']==bchunk['observation_sha256']
    aset=set(achunk['metadata']['retained_indices']);bset=set(bchunk['metadata']['retained_indices'])
    inter=len(aset&bset);union=len(aset|bset);assert len(aset)==len(bset)==128
    token_pairs.append({'task_id':task,'state_trial_id':sid,'observation_sha256':achunk['observation_sha256'],
      'intersection_tokens':inter,'union_tokens':union,'intersection_over_128':inter/128,'Jaccard':inter/union})
    label='both_success' if a and b else 'A_only' if a else 'B_only' if b else 'both_failure'
    discord[label]+=1;local[label]+=1;method_totals['A']+=int(a);method_totals['B']+=int(b)
    tot['A']+=int(a);tot['B']+=int(b)
    paired_table.append({'suite':suite,'task_id':task,'task_name':state['task_name'],'source_state_index':state['source_state_index'],'state_trial_id':sid,
      'initial_state_sha256':state['initial_state_sha256'],'training_seed':23,'A_success':a,'B_success':b})
   per_task.append({'task_id':task,'task_name':selected[0]['task_name'],'unique_initial_states':10,
      'A_success':tot['A'],'B_success':tot['B'],'B_minus_A_pp':(tot['B']-tot['A'])*10,
      'discordance':{k:local[k] for k in ['both_success','A_only','B_only','both_failure']}})
  for row in per_task:
   tp=[x for x in token_pairs if x['task_id']==row['task_id']]
   assert len(tp)==10
   row['t0_intersection_over_128_mean']=sum(x['intersection_over_128'] for x in tp)/10
   row['t0_Jaccard_mean']=sum(x['Jaccard'] for x in tp)/10
  assert len(token_pairs)==100
  for method,identity in identities.items():
   assert sum(r['success'] for r in finished.values() if r['method']==method)==method_totals[identity['method']]
  assert report['completed_trials']==report['expected_trials']==200 and report['unique_initial_states']==100
  assert report['checkpoint_unchanged'] is True and report['test_opened'] is False
  journal_prefix=R/output/'action_execution'/jid
  outer=[rv.json_bytes(x) for x in read(journal_prefix/'events.jsonl').splitlines()]
  assert [x['seq'] for x in outer]==list(range(len(outer)))
  assert outer[0]['event']=='action_execution_start' and outer[-1]['event']=='action_execution_end'
  assert all(x['job_id']==jid and x['version']=='formal-downstream-action-v1' for x in outer)
  completion=jread(journal_prefix/'completion.json')
  assert completion['events_sha256']==inputs[str(journal_prefix/'events.jsonl')]['sha256']
  assert completion['immutable_inputs_unchanged'] and completion['runtime_restored'] and completion['errors']==[]
  authrel='results/formal_main_v2/execution/nonLong_action_v1_1032/'+suite+'_k128_seed23/submission_authorization.json'
  auth=jread(R/authrel,expected['auth_sha']);gateway=R/'results/formal_main_v2/downstream_gateway'/expected['auth_sha']
  fail=jread(gateway/'failed_transaction.json',expected['failure_sha']);ack=jread(gateway/'sbatch_result.json',expected['ACK_sha'])
  assert fail['error']=='post-submit accounting incomplete' and fail['automatic_retry'] is False
  assert ack['returncode']==0 and ack['stdout'].strip()==jid and auth['maximum_attempts']==1
  combined[suite]={'status':'passed','job_id':jid,'root_receipt':rootref,
   'source_version':'formal-downstream-action-v1','training_seed':23,'visual_tokens':128,
   'methods':identities,'trials':200,'unique_initial_states':100,'tasks':10,'per_task':per_task,
   'A_success':method_totals['A'],'B_success':method_totals['B'],'B_minus_A_pp':method_totals['B']-method_totals['A'],
   'discordance':{k:discord[k] for k in ['both_success','A_only','B_only','both_failure']},
   'full_action_chunks':chunks,'executed_control_actions':steps,'environment':environment,
   'raw_ledger':{'path':str(output/'trials.jsonl'),'sha256':sha(raw),'bytes':len(raw)},
   'allocated_GPU_seconds':expected['allocated'],'all_attempt_cost':rebuilt['cost'],
   'full_original_consumer_reconstruction_passed':True,
   't0_token_diagnostics':{'paired_observations':100,'all_t0_observation_hashes_equal':True,
    'mean_intersection_over_128':sum(x['intersection_over_128'] for x in token_pairs)/100,
    'mean_Jaccard':sum(x['Jaccard'] for x in token_pairs)/100,'rows':token_pairs,
    'scope':'Only identical pre-action t0 observation pairs; no comparison after trajectories diverge.'},
   'offline_validation_diagnostics':validation_diagnostics,'raw_start_result_pairs_exact':True,
   'checkpoint_hash_scope':'Recorded actual runtime watches/chunk metadata equal frozen selected deployment receipts; no checkpoint bytes independently opened.',
   'original_ACK_accounting_delay_preserved':True,'submission_failure_added_new_GPU_allocation':False,
   'new_GPU_seconds_by_this_audit':0,'scientific_final_release':False}
  full_counts['trials']+=200;full_counts['chunks']+=chunks;full_counts['executed_actions']+=steps;full_counts['allocated_gpu_seconds']+=expected['allocated']
 evidence.unchanged()
 assert full_counts['trials']==400 and full_counts['allocated_gpu_seconds']==4551 and len(all_trial_ids)==400
 for rel,h in evidence.files.items():read(R/rel,h)
 paired=put('paired_development_states.json',{'schema':'formal_main_v2','scope':'two_suite_seed23_development_only','states':paired_table})
 report=put('independent_review.json',{'schema':'formal_main_v2','kind':'independent_action_v1_development_terminal_review','status':'passed',
  'reviewed_utc':datetime.now(timezone.utc).isoformat(),'review_role':'independent','synthetic':False,
  'jobs':combined,'totals':full_counts,'unique_initial_states':200,'unique_initial_states_per_suite':100,
  'scope':'One training seed per suite; paired descriptive development results only. Not a three-seed estimate, final success rate, equivalence proof, or O2A speed claim.',
  'source173_R_and_S_unchanged':True,'verified_pull_files_R_P_equal':24,'paired_states':paired,
  'all_inputs':dict(sorted(inputs.items())),'checkpoint_bytes_read':False,'sealed_final_values_read':False,
  'Goal3048609_intermediate_results_read':False,'live_scheduler_queries':0,'new_GPU_jobs':0,
  'audit_correction':'a1 treated canonical deployment receipt signature as raw-file hash. a2 retains both SHA types and verifies the original JSON-signature contract; all original a1 evidence retained.',
  'state_registry_Git_Slurm_mutations':False,'CPU_process_seconds':time.process_time()-cpu,'CPU_wall_seconds':time.monotonic()-started})
 manifest=[]
 for p in sorted(D.iterdir()):
  if p.is_file() and p.name!='manifest.json':
   b=p.read_bytes();manifest.append({'path':str(p.relative_to(R)),'sha256':sha(b),'bytes':len(b)})
 mref=put('manifest.json',{'schema':'formal_main_v2','kind':'independent_review_manifest','status':'passed','files':manifest})
 print(json.dumps({'status':'passed','report':report,'manifest':mref,'totals':full_counts,
  'success':{s:[v['A_success'],v['B_success']] for s,v in combined.items()}}))
except Exception as exc:
 fail=put('failure_a2.json',{'status':'failed','error_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'inputs_read':inputs})
 print(json.dumps({'status':'failed','failure':fail}));raise

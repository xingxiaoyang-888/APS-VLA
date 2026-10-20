"""Independent CPU-only terminal audit of Goal development jobs 3048609/3049191."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,sys,time,traceback,types
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/Goal_terminal_independent_1317'
B='results/formal_main_v2/preflight/heartbeat_20261020T2117'
REVIEWER='scripts/ops/formal_action_deployment_v1/reviewer.py'
CONSUMER='scripts/ops/formal_action_deployment_v1/consumer.py'
RPIN='9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd'
CPIN='16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
IPIN='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
PULL='results/formal_main_v2/pulls/20261020T132113Z_317ce98aa8f5/receipt.json'
PINNED={
 PULL:'c5c3cf85a1a6738b78cc4f76714873cc82ee0987719912bb61f07ecef8acfc4a',
 B+'/initial_observation.json':'80eef098e54260c58876a422fe098ad6d2d7081bb530604b51e657d2bbc908ed',
 B+'/terminal_jobs_snapshot.json':'52452454dc6fcd6bd1959f752a10f1b0240a96b69c9dbe18f1a7514e77e958c8',
 B+'/3048609_root_terminal.json':'87f275fad7d770d557aebee59dc1633ac5eb08d2c1114ebded3cfebbe2051bd0',
 B+'/3049191_root_terminal.json':'175fa1fb8ac7febc6aa641f5dff10c523641be042c2f414f97b346edf0b0dcd4',
}
JOBS={
 '3048609':{'seed':17,'trials':600,'allocated':5780,
  'methods':{'dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17'},
  'root_sha':'7e3fc5858ed27baacfb878cec8adea70e8e43df736e9f2f785eb1a189c5f31a8',
  'auth':'results/formal_main_v2/execution/nonLong_action_v1_1032/libero_goal_k128_seed17/submission_authorization.json',
  'auth_sha':'a686142e3af91491d83444270b51b2fbac1f95e7a0f95fd7a0f64f4fa374e89f',
  'failure_sha':'73db53014c4f95dcd2808b8ba8cdc78d20e694240ffe4117a5d72fe34d0b31b1',
  'ack_sha':'c692fbdef5ce12749d0c6ad9663955ffa2ffc428bcb8a7a87d93ed34f6927982'},
 '3049191':{'seed':23,'trials':200,'allocated':2019,
  'methods':{'A128_seed23','B128_seed23'},
  'root_sha':'56a9bf2d1145ec5adc3efdc3a1ac145ac8d59a49a00325924068e7c49f7b7feb',
  'auth':'results/formal_main_v2/execution/nonLong_action_v1_1220/libero_goal_k128_seed23/submission_authorization.json',
  'auth_sha':'efcfa42b97d4d780999f344f8024ff369d5f466825b25d7119ad0c118cbfa117',
  'failure_sha':'2f043eca8ad6ffd8cb67466f18300801b0d180a0a0a27638c9716994a692993c',
  'ack_sha':'c9efca1b653f123564a6ed237cc9ed2fcb09ecea5123bdeb4b7fbb7ef510c3fc'},
}
inputs={}
def sha(b):return hashlib.sha256(b).hexdigest()
def read(path,pin=None):
 path=Path(path);assert path.is_file() and not path.is_symlink()
 assert path.suffix not in {'.pt','.pth','.bin','.safetensors','.ckpt','.pkl','.pickle','.pruned_init','.init'}
 assert not any(x in path.parts for x in ['test','final','weights','checkpoints'])
 b=path.read_bytes();hh=sha(b);assert pin is None or hh==pin,(str(path),hh,pin)
 if str(path) in inputs:assert inputs[str(path)]['sha256']==hh
 inputs[str(path)]={'sha256':hh,'bytes':len(b)}
 return b
def jread(path,pin=None):return json.loads(read(path,pin))
def put(name,value):
 p=D/name;assert not p.exists(),str(p)
 b=(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
 with p.open('xb') as out:out.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)}
def module(rel,pin,name):
 code=read(R/rel,pin);m=types.ModuleType(name);m.__file__=str(R/rel);m.__package__=''
 sys.modules[name]=m;exec(compile(code,m.__file__,'exec'),m.__dict__);return m
def finite(x):
 a=np.asarray(x,dtype=np.float64);assert np.isfinite(a).all();return a
def uniform(total):
 rs,cs={64:(4,2),128:(2,2),256:(2,1)}[total]
 local=[r*16+c for r in range(0,16,rs) for c in range(0,16,cs)]
 return local+[x+256 for x in local]
started=time.monotonic();cpu=time.process_time()
try:
 for rel,pin in PINNED.items():read(R/rel,pin)
 pull=jread(R/PULL);snap=jread(R/B/'terminal_jobs_snapshot.json')
 assert set(pull['requested_job_ids'])==set(JOBS)
 assert pull['weights_copied'] is False and pull['sealed_initial_states_copied'] is False
 assert pull['status']=='verified_nonweight_snapshot' and len(pull['files'])==24
 for row in pull['files']:
  assert row['local_path']==str(R/row['relative']) and row['path']==str(P/row['relative'])
  a=read(R/row['relative'],row['sha256']);b=read(P/row['relative'],row['sha256'])
  assert a==b and len(a)==row['bytes']
 inv=jread(R/INV,IPIN);assert len(inv['files'])==173
 for rel,pin in inv['files'].items():read(R/rel,pin);read(S/rel,pin)
 rv=module(REVIEWER,RPIN,'_Goal_terminal_independent_1317')
 evidence=rv.Evidence(R);consumer=rv.load(evidence,CONSUMER,CPIN)
 combined={};paired_table=[];method_results={};common_states=None;common_panel_bytes=None;common_t0={};global_ids=set()
 totals={'trials':0,'chunks':0,'executed_actions':0,'allocated_gpu_seconds':0}
 for jid,exp in JOBS.items():
  seed=exp['seed'];count=exp['trials'];methods=exp['methods'];matches=[j for j in snap['registered_jobs'] if str(j['job_id'])==jid]
  assert len(matches)==1;job=matches[0]
  assert job['suite']=='libero_goal' and job['status']=='COMPLETED' and job['exit_code']=='0:0'
  assert job['gpus']==1 and job['elapsed_seconds']==exp['allocated'] and set(job['method_ids'])==methods
  rootref={'path':'results/formal_main_v2/downstream_reviews/'+jid+'.json','sha256':exp['root_sha']}
  root=jread(R/rootref['path'],rootref['sha256']);assert root['pull_ref']['path']==PULL
  rebuilt=consumer.review_downstream_output(evidence,rootref,expected_stage='development',suite='libero_goal',run_root=job['run_root'],require_complete=True)
  assert rebuilt['scientific_complete'] and rebuilt['completed_trials']==rebuilt['expected_trials']==count
  assert rebuilt['execution_version']=='formal-downstream-action-v1' and rebuilt['final_release'] is False and rebuilt['final_state_values_read'] is False and rebuilt['weights_read'] is False
  assert rebuilt['cost']['current_gpu_seconds']==rebuilt['cost']['all_attempt_gpu_seconds']==exp['allocated']
  assert len(rebuilt['cost']['allocations'])==1 and rebuilt['cost']['allocations'][0]['job_id']==jid
  for rel,hh in rebuilt['evidence_sha256'].items():read(R/rel,hh)
  output=Path(job['run_root']).relative_to(P)
  cfg=jread(R/output/'config.json');panelbytes=read(R/output/'panel.json');panel=json.loads(panelbytes);report=jread(R/output/'closed_loop_report.json')
  manifest=cfg['manifest'];env={'action_chunk':8,'environment_seed':0,'max_steps':300,'runtime_seed':17,'wait_steps':10}
  assert manifest['suite']=='libero_goal' and manifest['split']=='development' and manifest['environment']==env
  assert jread(R/manifest['development_panel'],manifest['development_panel_sha256'])==panel
  assert panel['suite']=='libero_goal' and panel['split']=='development' and panel['environment_seed']==0
  states={x['trial_id']:x for x in panel['states']}
  assert len(states)==100 and len(panel['task_catalog'])==10 and Counter(s['task_id'] for s in states.values())=={i:10 for i in range(10)}
  if common_states is None:common_states=states;common_panel_bytes=panelbytes
  else:assert states==common_states and panelbytes==common_panel_bytes
  identities={x['identity']['method_id']:x['identity'] for x in manifest['methods']};assert set(identities)==methods
  diagnostics={}
  for method in manifest['methods']:
   ident=method['identity'];learned=ident['method'] in ('A','B')
   assert ident['suite']=='libero_goal' and ident['future_head_deployed'] is False
   assert ident['frozen_model_sha256']=='85703124930f24771cd4d04a4e88309710fcfc230e4891a1e6578d7ec14a45a2'
   assert ident['stats_key']=='libero_goal_no_noops' and ident['model_revision']=='c2d0f9fbbd82674683b397ff923168a12f6a307b'
   if not learned:
    assert ident['training_seed'] is None and 'checkpoint' not in method and 'receipt' not in method
    assert ident['visual_tokens']==(512 if ident['method']=='dense' else int(ident['method_id'][7:]))
    continue
   assert ident['training_seed']==seed and ident['visual_tokens']==128 and ident['training_complete'] is True
   assert cfg['watched_files'][method['checkpoint']]==ident['checkpoint_sha256']
   receipt=jread(R/method['receipt']);assert rv.signature(receipt)==ident['deployment_receipt_sha256']
   assert receipt['checkpoint_sha256']==ident['checkpoint_sha256']
   selection=min(receipt['evaluations'],key=lambda r:(r['validation_metric'],r['update']))
   assert selection['update']==receipt['metadata']['update']
   vrel=Path(selection['artifact_path']).relative_to(P).as_posix()
   val=jread(R/vrel,selection['artifact_sha256'])
   assert val['metric']=='task_macro_hard_validation_teacher_l1' and val['update']==selection['update'] and val['arm']==ident['method']
   assert val['validation_metric']==selection['validation_metric']==receipt['metadata']['validation_metric']
   teacher=sum(x['teacher_l1'] for x in val['per_task'].values())/len(val['per_task'])
   demo=sum(x['demonstration_l1'] for x in val['per_task'].values())/len(val['per_task'])
   assert teacher==val['validation_metric'] and demo==val['demonstration_l1']
   diagnostics[ident['method']]={'selected_update':selection['update'],'hard_validation_teacher_L1_task_equal':teacher,
    'hard_validation_demonstration_L1_task_equal':demo,'validation_windows':val['windows'],'validation_tasks':val['tasks'],
    'validation_ref':{'path':vrel,'sha256':selection['artifact_sha256']},
    'deployment_receipt_raw_sha256':inputs[str(R/method['receipt'])]['sha256'],
    'deployment_receipt_canonical_JSON_sha256':ident['deployment_receipt_sha256'],'checkpoint_sha256':ident['checkpoint_sha256'],
    'scope':'Selected checkpoint offline hard-pruning validation diagnostic, not closed-loop action error.'}
  raw=read(R/output/'trials.jsonl');assert raw.endswith(b'\n') and sha(raw)==report['trials_jsonl_sha256']
  rows=[rv.json_bytes(line) for line in raw.splitlines()]
  assert Counter(x['event'] for x in rows)=={'invocation':1,'start':count,'result':count}
  assert rows[0]['event']=='invocation' and rows[0]['slurm_job_id']==jid
  signature=rv.signature(cfg);assert all(x['run_signature']==signature for x in rows)
  active={};finished={};chunks=0;steps=0;last_time=None
  for row in rows:
   t=datetime.fromisoformat(row['created_utc']);assert t.tzinfo is not None and (last_time is None or t>=last_time);last_time=t
   if row['event']=='invocation':continue
   tid=row['trial_id'];sid=row['state_trial_id'];method=row['method'];assert sid in states and method in methods and tid==sid+':'+method
   st=states[sid]
   for key in ['task_id','task_name','source_state_index','initial_state_sha256']:assert row[key]==st[key]
   assert row['suite']=='libero_goal' and row['split']=='development' and row['environment_seed']==0 and row['runtime_seed']==17 and row['action_chunk']==8 and row['configured_wait_steps']==10
   if row['event']=='start':
    assert tid not in active and tid not in finished;active[tid]=row;continue
   assert tid in active and tid not in finished;active.pop(tid)
   assert row['status']=='completed' and type(row['success']) is bool and row['wait_steps']==10
   controls=row['control_steps'];assert type(controls) is int and 0<controls<=300
   assert row['termination']==('environment_success' if row['success'] else 'task_horizon')
   if not row['success']:assert controls==300
   assert [ch['control_step'] for ch in row['chunks']]==list(range(0,controls,8)) and row['policy_calls']==len(row['chunks'])
   ident=identities[method];learned=ident['method'] in ('A','B');tokens=ident['visual_tokens'];env_actions=[]
   for ch in row['chunks']:
    ea=finite(ch['environment_actions']);na=finite(ch['normalized_actions']);assert ea.shape==na.shape==(8,7)
    m=ch['metadata'];assert m['suite']=='libero_goal' and m['method']==ident['method']
    assert m['visual_tokens']==tokens and m['per_camera_budgets']==[tokens//2,tokens//2]
    assert m['future_head_calls']==0 and m['language_cache']=='disabled' and m['vision_calls']==m['packing_calls']==m['policy_calls']==1
    assert m['scorer_calls']==int(learned) and m['packing_version']=='oft-original-positions-v1'
    assert m['action_version']=='libero-oft-boundsq99-gripper-sign-invert-chunk8-v1'
    assert m['inputs_version']=='libero-oft-eval-rotate180-jpeg-lanczos3-crop09-boundsq99-v1'
    if learned:
     assert m['training_seed']==seed and m['selector_checkpoint_sha256']==ident['checkpoint_sha256'] and m['pair_id']==ident['pair_id']
    else:assert 'selector_checkpoint_sha256' not in m and 'training_seed' not in m and 'pair_id' not in m
    indices=m['retained_indices'];assert indices==sorted(set(indices)) and len(indices)==tokens
    assert all(type(x) is int and 0<=x<512 for x in indices) and sum(x<256 for x in indices)==tokens//2
    if ident['method']=='dense':assert indices==list(range(512))
    elif ident['method']=='uniform':assert indices==uniform(tokens)
    assert isinstance(ch['observation_sha256'],str) and len(ch['observation_sha256'])==64
    env_actions.append(ea)
   executed=finite(row['executed_actions']);assert executed.shape==(controls,7) and np.array_equal(executed,np.concatenate(env_actions)[:controls])
   assert common_t0.setdefault(sid,row['chunks'][0]['observation_sha256'])==row['chunks'][0]['observation_sha256']
   assert finite([row['wall_seconds'],row['attempt_wall_seconds']]).min()>=0
   finished[tid]=row;chunks+=len(row['chunks']);steps+=controls
  assert not active and len(finished)==count and len(common_t0)==100
  assert not(global_ids & set(finished));global_ids.update(finished)
  totals_by_method={method:sum(row['success'] for row in finished.values() if row['method']==method) for method in sorted(methods)}
  assert all(sum(row['method']==method for row in finished.values())==100 for method in methods)
  assert {method:data['successes'] for method,data in report['methods'].items()}==totals_by_method
  method_results.update(totals_by_method)
  tokenpairs=[];pertask=[];discord=Counter();A='A128_seed'+str(seed);Bm='B128_seed'+str(seed)
  for task in range(10):
   selected=sorted((st for st in states.values() if st['task_id']==task),key=lambda st:st['source_state_index']);local=Counter()
   for st in selected:
    sid=st['trial_id'];ar=finished[sid+':'+A];br=finished[sid+':'+Bm];a=ar['success'];b=br['success']
    ac=ar['chunks'][0];bc=br['chunks'][0];assert ac['control_step']==bc['control_step']==0 and ac['observation_sha256']==bc['observation_sha256']
    aa=set(ac['metadata']['retained_indices']);bb=set(bc['metadata']['retained_indices'])
    intersection=len(aa&bb);union=len(aa|bb);assert len(aa)==len(bb)==128
    tokenpairs.append({'task_id':task,'state_trial_id':sid,'observation_sha256':ac['observation_sha256'],'intersection_tokens':intersection,
      'union_tokens':union,'intersection_over_128':intersection/128,'Jaccard':intersection/union})
    label='both_success' if a and b else 'A_only' if a else 'B_only' if b else 'both_failure';discord[label]+=1;local[label]+=1
    paired_table.append({'suite':'libero_goal','task_id':task,'task_name':st['task_name'],'source_state_index':st['source_state_index'],'state_trial_id':sid,
      'initial_state_sha256':st['initial_state_sha256'],'training_seed':seed,'A_success':a,'B_success':b,
      'observation_sha256':ac['observation_sha256']})
   success={method:sum(finished[st['trial_id']+':'+method]['success'] for st in selected) for method in sorted(methods)}
   tp=[x for x in tokenpairs if x['task_id']==task];assert len(tp)==10
   pertask.append({'task_id':task,'task_name':selected[0]['task_name'],'unique_initial_states':10,'successes':success,
      'A_success':success[A],'B_success':success[Bm],'B_minus_A_pp':(success[Bm]-success[A])*10,
      'discordance':{k:local[k] for k in ['both_success','A_only','B_only','both_failure']},
      't0_intersection_over_128_mean':sum(x['intersection_over_128'] for x in tp)/10,'t0_Jaccard_mean':sum(x['Jaccard'] for x in tp)/10})
  assert len(tokenpairs)==100
  originalpair=report['paired_AB']['k128_seed'+str(seed)]
  assert originalpair['completed_pairs']==100 and abs(originalpair['B_minus_A_success_rate']*100-(totals_by_method[Bm]-totals_by_method[A]))<1e-10
  assert report['completed_trials']==report['expected_trials']==count and report['unique_initial_states']==100 and report['checkpoint_unchanged'] is True and report['test_opened'] is False
  jp=R/output/'action_execution'/jid
  outer=[rv.json_bytes(line) for line in read(jp/'events.jsonl').splitlines()]
  assert [x['seq'] for x in outer]==list(range(len(outer))) and outer[0]['event']=='action_execution_start' and outer[-1]['event']=='action_execution_end'
  assert all(x['job_id']==jid and x['version']=='formal-downstream-action-v1' for x in outer)
  completion=jread(jp/'completion.json');assert completion['events_sha256']==inputs[str(jp/'events.jsonl')]['sha256']
  assert completion['immutable_inputs_unchanged'] and completion['runtime_restored'] and completion['errors']==[]
  auth=jread(R/exp['auth'],exp['auth_sha']);gateway=R/'results/formal_main_v2/downstream_gateway'/exp['auth_sha']
  failure=jread(gateway/'failed_transaction.json',exp['failure_sha']);ack=jread(gateway/'sbatch_result.json',exp['ack_sha'])
  assert failure['error']=='post-submit accounting incomplete' and failure['automatic_retry'] is False
  assert ack['returncode']==0 and ack['stdout'].strip()==jid and auth['maximum_attempts']==1
  combined[jid]={'status':'passed','job_id':jid,'suite':'libero_goal','root_receipt':rootref,'source_version':'formal-downstream-action-v1',
   'training_seed':seed,'seed':seed,'A_B_visual_tokens':128,'methods':identities,'trials':count,'reference_trials':400 if jid=='3048609' else 0,'AB_trials':200,'unique_initial_states':100,'tasks':10,'per_task':pertask,
   'successes':totals_by_method,'A_success':totals_by_method[A],'B_success':totals_by_method[Bm],'B_minus_A_pp':totals_by_method[Bm]-totals_by_method[A],
   'discordance':{k:discord[k] for k in ['both_success','A_only','B_only','both_failure']},'full_action_chunks':chunks,'executed_control_actions':steps,
   'environment':env,'raw_ledger':{'path':(output/'trials.jsonl').as_posix(),'sha256':sha(raw),'bytes':len(raw)},
   'allocated_GPU_seconds':exp['allocated'],'all_attempt_cost':rebuilt['cost'],'full_original_consumer_reconstruction_passed':True,
   't0_token_diagnostics':{'paired_observations':100,'all_t0_observation_hashes_equal':True,'mean_intersection_over_128':sum(x['intersection_over_128'] for x in tokenpairs)/100,
     'mean_Jaccard':sum(x['Jaccard'] for x in tokenpairs)/100,'rows':tokenpairs,'scope':'AB within seed on identical pre-action t0 only; later divergent trajectories not compared.'},
   'offline_validation_diagnostics':diagnostics,'raw_start_result_pairs_exact':True,
   'checkpoint_hash_scope':'Actual runtime watches/chunk metadata match frozen selected receipts. No checkpoint bytes independently read.',
   'original_ACK_accounting_delay_preserved':True,'submission_failure_added_new_GPU_allocation':False,'new_GPU_seconds_by_this_audit':0,'scientific_final_release':False}
  totals['trials']+=count;totals['chunks']+=chunks;totals['executed_actions']+=steps;totals['allocated_gpu_seconds']+=exp['allocated']
  if jid=='3048609':
   references={m:{'successes':totals_by_method[m],'trials':100,'training_seed':None,
    'per_task':[{'task_id':x['task_id'],'successes':x['successes'][m],'trials':10} for x in pertask]} for m in ('dense','uniform256','uniform128','uniform64')}
   combined[jid]['references']=references
  del rows,finished,raw
 evidence.unchanged()
 assert totals['trials']==800 and totals['allocated_gpu_seconds']==7799 and len(global_ids)==800
 assert len(common_states)==len(common_t0)==100 and len(paired_table)==200
 assert len({x['state_trial_id'] for x in paired_table})==100 and set(x['training_seed'] for x in paired_table)=={17,23}
 for rel,hh in evidence.files.items():read(R/rel,hh)
 paired=put('paired_development_states.json',{'schema':'formal_main_v2','scope':'Goal two_seed17_23_development_only,100unique states reused across2seeds','states':paired_table})
 meanA=(combined['3048609']['A_success']+combined['3049191']['A_success'])/2
 meanB=(combined['3048609']['B_success']+combined['3049191']['B_success'])/2
 reportref=put('independent_review.json',{'schema':'formal_main_v2','kind':'independent_Goal_action_v1_development_terminal_review','status':'passed',
   'review_role':'independent','synthetic':False,'reviewed_utc':datetime.now(timezone.utc).isoformat(),
   'jobs':combined,'totals':totals,'unique_initial_states':100,'available_training_seeds':[17,23],'missing_training_seed':41,
   'method_successes_out_of100':method_results,'shared_reference_results':references,
   'available_two_seed_mean_percent':{'A128':meanA,'B128':meanB,'B_minus_A_pp':meanB-meanA},
   'shared_initial_panel_sha256':sha(common_panel_bytes),'all_eight_methods_same_t0_observation_for_each_state':True,
   'scope':'Two training seeds only; descriptive paired development results. 800 method-state trials are100unique initial-state clusters. Dense/uniform each evaluated once, not replicated per seed. No bootstrap CI, final evaluation, equivalence or O2A speed claim.',
   'bootstrap_computed':False,'CI_claimed':False,'source_preexecution_revision':'a1 was an unexecuted authoring draft; a2 adds explicit per-job reference/AB trial counts, seed alias and reference per-task results without changing scientific checks.','source173_R_and_S_unchanged':True,'verified_pull_files_R_P_equal':24,'paired_states':paired,
   'all_inputs':dict(sorted(inputs.items())),'checkpoint_bytes_read':False,'sealed_final_values_read':False,'live_scheduler_queries':0,'new_GPU_jobs':0,
   'state_registry_Git_Slurm_mutations':False,'CPU_process_seconds':time.process_time()-cpu,'CPU_wall_seconds':time.monotonic()-started})
 files=[]
 for p in sorted(D.iterdir()):
  if p.is_file() and p.name!='manifest.json':
   b=p.read_bytes();files.append({'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)})
 manifestref=put('manifest.json',{'schema':'formal_main_v2','kind':'independent_review_manifest','status':'passed','files':files})
 print(json.dumps({'status':'passed','report':reportref,'manifest':manifestref,'totals':totals,'successes':method_results,
  'seed_AB':{str(v['training_seed']):[v['A_success'],v['B_success']] for v in combined.values()}}))
except Exception as exc:
 failure=put('failure_a2.json',{'status':'failed','error_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'inputs_read':inputs})
 print(json.dumps({'status':'failed','failure':failure}));raise

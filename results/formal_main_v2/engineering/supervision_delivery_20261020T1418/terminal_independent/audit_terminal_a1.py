"""Independent CPU-only terminal audit of five completed development jobs; sixth Goal256 held separately."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,sys,time,traceback,types
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/devterminal_independent_20261020T1418'
B='results/formal_main_v2/preflight/heartbeat_20261020T2218'
REVIEWER='scripts/ops/formal_action_deployment_v1/reviewer.py'
CONSUMER='scripts/ops/formal_action_deployment_v1/consumer.py'
RPIN='9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd'
CPIN='16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
IPIN='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
PULL='results/formal_main_v2/pulls/20261020T142621Z_02800e667ffb/receipt.json'
PINNED={'results/formal_main_v2/pulls/20261020T142621Z_02800e667ffb/receipt.json': '20139adbe331ea4d217e7011f22b4e3d6e008f6c59e87ff1d00a0735ef290493', 'results/formal_main_v2/preflight/heartbeat_20261020T2218/initial_observation.json': 'cf139e4279216a82e81eddeafe7430c2794a94f1643bb3466b64ec5c8d285f76', 'results/formal_main_v2/preflight/heartbeat_20261020T2218/terminal_jobs_snapshot.json': '4417ed6bc2d89611d6507d1ad2cabc544c89faa8b1eb0340cca563706322ba1a'}
JOBS={'3049132': {'suite': 'libero_spatial', 'seed': 41, 'budget': 128, 'trials': 200, 'allocated': 2315, 'methods': {'B128_seed41', 'A128_seed41'}, 'root_sha': 'd705c821e83b0bc9121102c62fc6aeb4917b490b1a8b22a647f7851f03b75910'}, '3049172': {'suite': 'libero_object', 'seed': 41, 'budget': 128, 'trials': 200, 'allocated': 2213, 'methods': {'B128_seed41', 'A128_seed41'}, 'root_sha': '2aba593e2014ee9996083a35dc3185376e81af49e4896141fd78e1fe068bf138'}, '3049622': {'suite': 'libero_goal', 'seed': 41, 'budget': 128, 'trials': 200, 'allocated': 2039, 'methods': {'B128_seed41', 'A128_seed41'}, 'root_sha': 'ffc074a3cc374a7d348488bdac0ac28c5575865630dd551ba97858a841671c23'}, '3049632': {'suite': 'libero_spatial', 'seed': 17, 'budget': 256, 'trials': 200, 'allocated': 2351, 'methods': {'A256_seed17', 'B256_seed17'}, 'root_sha': 'a07278ca96d6c6c461283b590ba09e1c9acd9427bac40a7380a8f244a64ee56b'}, '3049657': {'suite': 'libero_object', 'seed': 17, 'budget': 256, 'trials': 200, 'allocated': 2198, 'methods': {'A256_seed17', 'B256_seed17'}, 'root_sha': '3c063f479ae499d57aa38ae6682141abfbcc3f3c5a66291a0c450fd42e66fbec'}}
MODEL_PINS={'libero_spatial': ('6a34ed9b4790fa889eb36406a1182d3d89ee539f7a65cb2f72d67e8326d557e7', '6d0231af0e48c5985f1ff86908f4674b84bc049b'), 'libero_object': ('33285a7643de7073e41bd2062cbbc80b4df8fddff915c0a86a13d0bbae48edce', '4c89574e1c538b6c102f43f0526d60a9d3650148'), 'libero_goal': ('85703124930f24771cd4d04a4e88309710fcfc230e4891a1e6578d7ec14a45a2', 'c2d0f9fbbd82674683b397ff923168a12f6a307b')}
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
 assert set(pull['requested_job_ids'])==set(JOBS)|{'3049679'}
 assert pull['weights_copied'] is False and pull['sealed_initial_states_copied'] is False
 assert pull['status']=='verified_nonweight_snapshot' and len(pull['files'])==72
 for row in pull['files']:
  assert row['local_path']==str(R/row['relative']) and row['path']==str(P/row['relative'])
  a=read(R/row['relative'],row['sha256']);b=read(P/row['relative'],row['sha256'])
  assert a==b and len(a)==row['bytes']
 inv=jread(R/INV,IPIN);assert len(inv['files'])==173
 for rel,pin in inv['files'].items():read(R/rel,pin);read(S/rel,pin)
 rv=module(REVIEWER,RPIN,'_Goal_terminal_independent_1317')
 evidence=rv.Evidence(R);consumer=rv.load(evidence,CONSUMER,CPIN)
 combined={};paired_table=[];method_results={};common_states_by_suite={};common_panels={};common_t0_by_suite={};global_ids=set()
 totals={'trials':0,'chunks':0,'executed_actions':0,'allocated_gpu_seconds':0}
 for jid,exp in JOBS.items():
  suite=exp['suite'];budget=exp['budget'];max_steps={'libero_spatial':220,'libero_object':280,'libero_goal':300}[suite];common_states=common_states_by_suite.get(suite);common_panel_bytes=common_panels.get(suite);common_t0=common_t0_by_suite.setdefault(suite,{});seed=exp['seed'];count=exp['trials'];methods=exp['methods'];matches=[j for j in snap['registered_jobs'] if str(j['job_id'])==jid]
  assert len(matches)==1;job=matches[0]
  assert job['suite']==suite and job['status']=='COMPLETED' and job['exit_code']=='0:0'
  assert job['gpus']==1 and job['elapsed_seconds']==exp['allocated'] and set(job['method_ids'])==methods
  rootref={'path':'results/formal_main_v2/downstream_reviews/'+jid+'.json','sha256':exp['root_sha']}
  root=jread(R/rootref['path'],rootref['sha256']);assert root['pull_ref']['path']==PULL
  rebuilt=consumer.review_downstream_output(evidence,rootref,expected_stage='development',suite=suite,run_root=job['run_root'],require_complete=True)
  assert rebuilt['scientific_complete'] and rebuilt['completed_trials']==rebuilt['expected_trials']==count
  assert rebuilt['execution_version']=='formal-downstream-action-v1' and rebuilt['final_release'] is False and rebuilt['final_state_values_read'] is False and rebuilt['weights_read'] is False
  assert rebuilt['cost']['current_gpu_seconds']==rebuilt['cost']['all_attempt_gpu_seconds']==exp['allocated']
  assert len(rebuilt['cost']['allocations'])==1 and rebuilt['cost']['allocations'][0]['job_id']==jid
  for rel,hh in rebuilt['evidence_sha256'].items():read(R/rel,hh)
  output=Path(job['run_root']).relative_to(P)
  cfg=jread(R/output/'config.json');panelbytes=read(R/output/'panel.json');panel=json.loads(panelbytes);report=jread(R/output/'closed_loop_report.json')
  manifest=cfg['manifest'];env={'action_chunk':8,'environment_seed':0,'max_steps':max_steps,'runtime_seed':17,'wait_steps':10}
  assert manifest['suite']==suite and manifest['split']=='development' and manifest['environment']==env
  assert jread(R/manifest['development_panel'],manifest['development_panel_sha256'])==panel
  assert panel['suite']==suite and panel['split']=='development' and panel['environment_seed']==0
  states={x['trial_id']:x for x in panel['states']}
  assert len(states)==100 and len(panel['task_catalog'])==10 and Counter(s['task_id'] for s in states.values())=={i:10 for i in range(10)}
  if common_states is None:common_states=states;common_panel_bytes=panelbytes
  else:assert states==common_states and panelbytes==common_panel_bytes
  common_states_by_suite[suite]=states;common_panels[suite]=panelbytes
  identities={x['identity']['method_id']:x['identity'] for x in manifest['methods']};assert set(identities)==methods
  diagnostics={}
  for method in manifest['methods']:
   ident=method['identity'];learned=ident['method'] in ('A','B')
   assert ident['suite']==suite and ident['future_head_deployed'] is False
   assert ident['frozen_model_sha256']==MODEL_PINS[suite][0]
   assert ident['stats_key']==suite+'_no_noops' and ident['model_revision']==MODEL_PINS[suite][1]
   if not learned:
    assert ident['training_seed'] is None and 'checkpoint' not in method and 'receipt' not in method
    assert ident['visual_tokens']==(512 if ident['method']=='dense' else int(ident['method_id'][7:]))
    continue
   assert ident['training_seed']==seed and ident['visual_tokens']==budget and ident['training_complete'] is True
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
   assert row['suite']==suite and row['split']=='development' and row['environment_seed']==0 and row['runtime_seed']==17 and row['action_chunk']==8 and row['configured_wait_steps']==10
   if row['event']=='start':
    assert tid not in active and tid not in finished;active[tid]=row;continue
   assert tid in active and tid not in finished;active.pop(tid)
   assert row['status']=='completed' and type(row['success']) is bool and row['wait_steps']==10
   controls=row['control_steps'];assert type(controls) is int and 0<controls<=max_steps
   assert row['termination']==('environment_success' if row['success'] else 'task_horizon')
   if not row['success']:assert controls==max_steps
   assert [ch['control_step'] for ch in row['chunks']]==list(range(0,controls,8)) and row['policy_calls']==len(row['chunks'])
   ident=identities[method];learned=ident['method'] in ('A','B');tokens=ident['visual_tokens'];env_actions=[]
   for ch in row['chunks']:
    ea=finite(ch['environment_actions']);na=finite(ch['normalized_actions']);assert ea.shape==na.shape==(8,7)
    m=ch['metadata'];assert m['suite']==suite and m['method']==ident['method']
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
  method_results[jid]=totals_by_method
  tokenpairs=[];pertask=[];discord=Counter();A='A'+str(budget)+'_seed'+str(seed);Bm='B'+str(budget)+'_seed'+str(seed)
  for task in range(10):
   selected=sorted((st for st in states.values() if st['task_id']==task),key=lambda st:st['source_state_index']);local=Counter()
   for st in selected:
    sid=st['trial_id'];ar=finished[sid+':'+A];br=finished[sid+':'+Bm];a=ar['success'];b=br['success']
    ac=ar['chunks'][0];bc=br['chunks'][0];assert ac['control_step']==bc['control_step']==0 and ac['observation_sha256']==bc['observation_sha256']
    aa=set(ac['metadata']['retained_indices']);bb=set(bc['metadata']['retained_indices'])
    intersection=len(aa&bb);union=len(aa|bb);assert len(aa)==len(bb)==budget
    tokenpairs.append({'task_id':task,'state_trial_id':sid,'observation_sha256':ac['observation_sha256'],'intersection_tokens':intersection,
      'union_tokens':union,'intersection_over_budget':intersection/budget,'Jaccard':intersection/union})
    label='both_success' if a and b else 'A_only' if a else 'B_only' if b else 'both_failure';discord[label]+=1;local[label]+=1
    paired_table.append({'suite':suite,'task_id':task,'task_name':st['task_name'],'source_state_index':st['source_state_index'],'state_trial_id':sid,
      'initial_state_sha256':st['initial_state_sha256'],'training_seed':seed,'visual_tokens':budget,'A_success':a,'B_success':b,
      'observation_sha256':ac['observation_sha256']})
   success={method:sum(finished[st['trial_id']+':'+method]['success'] for st in selected) for method in sorted(methods)}
   tp=[x for x in tokenpairs if x['task_id']==task];assert len(tp)==10
   pertask.append({'task_id':task,'task_name':selected[0]['task_name'],'unique_initial_states':10,'successes':success,
      'A_success':success[A],'B_success':success[Bm],'B_minus_A_pp':(success[Bm]-success[A])*10,
      'discordance':{k:local[k] for k in ['both_success','A_only','B_only','both_failure']},
      't0_intersection_over_budget_mean':sum(x['intersection_over_budget'] for x in tp)/10,'t0_Jaccard_mean':sum(x['Jaccard'] for x in tp)/10})
  assert len(tokenpairs)==100
  originalpair=report['paired_AB']['k'+str(budget)+'_seed'+str(seed)]
  assert originalpair['completed_pairs']==100 and abs(originalpair['B_minus_A_success_rate']*100-(totals_by_method[Bm]-totals_by_method[A]))<1e-10
  assert report['completed_trials']==report['expected_trials']==count and report['unique_initial_states']==100 and report['checkpoint_unchanged'] is True and report['test_opened'] is False
  jp=R/output/'action_execution'/jid
  outer=[rv.json_bytes(line) for line in read(jp/'events.jsonl').splitlines()]
  assert [x['seq'] for x in outer]==list(range(len(outer))) and outer[0]['event']=='action_execution_start' and outer[-1]['event']=='action_execution_end'
  assert all(x['job_id']==jid and x['version']=='formal-downstream-action-v1' for x in outer)
  completion=jread(jp/'completion.json');assert completion['events_sha256']==inputs[str(jp/'events.jsonl')]['sha256']
  assert completion['immutable_inputs_unchanged'] and completion['runtime_restored'] and completion['errors']==[]
  aref=job['downstream_gateway']['authorization'];auth=jread(R/aref['path'],aref['sha256']);gateway=R/'results/formal_main_v2/downstream_gateway'/aref['sha256']
  failure=jread(gateway/'failed_transaction.json');ack=jread(gateway/'sbatch_result.json')
  assert failure['error']=='post-submit accounting incomplete' and failure['automatic_retry'] is False
  assert ack['returncode']==0 and ack['stdout'].strip()==jid and auth['maximum_attempts']==1
  combined[jid]={'status':'passed','job_id':jid,'suite':suite,'root_receipt':rootref,'source_version':'formal-downstream-action-v1',
   'training_seed':seed,'seed':seed,'A_B_visual_tokens':budget,'methods':identities,'trials':count,'reference_trials':0,'AB_trials':200,'unique_initial_states':100,'tasks':10,'per_task':pertask,
   'successes':totals_by_method,'A_success':totals_by_method[A],'B_success':totals_by_method[Bm],'B_minus_A_pp':totals_by_method[Bm]-totals_by_method[A],
   'discordance':{k:discord[k] for k in ['both_success','A_only','B_only','both_failure']},'full_action_chunks':chunks,'executed_control_actions':steps,
   'environment':env,'raw_ledger':{'path':(output/'trials.jsonl').as_posix(),'sha256':sha(raw),'bytes':len(raw)},
   'allocated_GPU_seconds':exp['allocated'],'all_attempt_cost':rebuilt['cost'],'full_original_consumer_reconstruction_passed':True,
   't0_token_diagnostics':{'paired_observations':100,'all_t0_observation_hashes_equal':True,'mean_intersection_over_budget':sum(x['intersection_over_budget'] for x in tokenpairs)/100,
     'mean_Jaccard':sum(x['Jaccard'] for x in tokenpairs)/100,'rows':tokenpairs,'scope':'AB within seed on identical pre-action t0 only; later divergent trajectories not compared.'},
   'offline_validation_diagnostics':diagnostics,'raw_start_result_pairs_exact':True,
   'checkpoint_hash_scope':'Actual runtime watches/chunk metadata match frozen selected receipts. No checkpoint bytes independently read.',
   'original_ACK_accounting_delay_preserved':True,'submission_failure_added_new_GPU_allocation':False,'new_GPU_seconds_by_this_audit':0,'scientific_final_release':False}
  totals['trials']+=count;totals['chunks']+=chunks;totals['executed_actions']+=steps;totals['allocated_gpu_seconds']+=exp['allocated']
  del rows,finished,raw
 evidence.unchanged()
 assert totals['trials']==1000 and totals['allocated_gpu_seconds']==11116 and len(global_ids)==1000
 assert sum(len(x) for x in common_states_by_suite.values())==300 and len(paired_table)==500
 for rel,hh in evidence.files.items():read(R/rel,hh)
 paired=put('paired_development_states.json',{'schema':'formal_main_v2','scope':'Five jobs, 500 paired records,300unique states in3suites; no final results.','states':paired_table})
 reportref=put('independent_review.json',{'schema':'formal_main_v2','kind':'independent_nonLong_action_v1_development_terminal_review','status':'passed','review_role':'independent','synthetic':False,'reviewed_utc':datetime.now(timezone.utc).isoformat(),'jobs':combined,'totals':totals,'unique_initial_states':300,'unique_initial_states_per_suite':{k:len(v) for k,v in common_states_by_suite.items()},'method_successes_out_of100':method_results,'shared_initial_panels_sha256':{k:sha(v) for k,v in common_panels.items()},'scope':'Five separately reviewed development jobs. Goal256s17 job3049679 excluded and held for mismatched initial observation; its artifacts were copied and retained but not accepted. No final evaluation, equivalence or O2A speed claim.','held_job_ids':['3049679'],'source173_R_and_S_unchanged':True,'verified_pull_files_R_P_equal':72,'paired_states':paired,'all_inputs':dict(sorted(inputs.items())),'checkpoint_bytes_read':False,'sealed_final_values_read':False,'live_scheduler_queries':0,'new_GPU_jobs':0,'state_registry_Git_Slurm_mutations':False,'CPU_process_seconds':time.process_time()-cpu,'CPU_wall_seconds':time.monotonic()-started})
 files=[]
 for p in sorted(D.iterdir()):
  if p.is_file() and p.name!='terminal_manifest.json':
   b=p.read_bytes();files.append({'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)})
 manifestref=put('terminal_manifest.json',{'schema':'formal_main_v2','kind':'independent_review_manifest','status':'passed','files':files})
 print(json.dumps({'status':'passed','report':reportref,'manifest':manifestref,'totals':totals,'successes':method_results}))
except Exception as exc:
 failure=put('failure_a1.json',{'status':'failed','error_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'inputs_read':inputs})
 print(json.dumps({'status':'failed','failure':failure}));raise

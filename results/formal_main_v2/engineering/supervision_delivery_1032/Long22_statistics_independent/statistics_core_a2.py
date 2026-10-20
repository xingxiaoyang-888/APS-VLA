"""Independent Long22 development statistics; no simulator, GPU or release.
Functions are not executed on import. Actual entrypoint must bind real proof
and root statistics after their publication. Outcomes come only from raw ledgers.
"""
from pathlib import Path
from collections import Counter
import hashlib,json
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/Long22_statistics_independent_1032'
JOBS={
'3019954':'cde7e784bced622a6a30169af1f3c34ece8b710da8a6d65ab804454457c5d9ba',
'3043709':'3868af9c4d8c5a1c2a896047f3b9d170b7fa2f1eaeb10fcc51689686a8589325',
'3045322':'d27e9bbf12e435ba3fd1341757b451e666b77528cd5fede6cb07ab19eb790699',
'3046779':'968b0e8b09577ce93320a02c1c69f5b37f6bc0256004962aaaa8a62e55789919',
'3046798':'251788eb33c35f2cd17e613d4bb4842cb1aa6ba6eb14937578fb1675a3d139de',
'3047152':'07c46b463db75271d7bdc6ecc43b43f9a20e4c88a351a88d16a735daf39ad03b',
'3047156':'9bd3713f5260d9b6da1397c6507330503ce429c59a4ea4a15986ac9a5d50e190',
'3047163':'5a1cc6e631a421f0891da6f6810fb0824717a37cd6d18fa26800e930acdac0bc',
'3047443':'20f91c0060f086bcf402cc0b9b4e9863397c27876f4809dd9bef211aa0c87c25'}
BUDGETS=[256,128,64];SEEDS=[17,23,41]
METHODS=['dense','uniform256','uniform128','uniform64']+[f'{m}{k}_seed{s}' for k in BUDGETS for s in SEEDS for m in ('A','B')]
SEM='4ef98a5beb21bfa790a8a0f484334d6d9020a481a517d8f89534562524025d7d'
PANEL={'path':'configs/manifests/formal_main_v2/libero_10/initial_states/development.json','sha256':'46a06087483151e36198167e7d4e5313c50b63172e09128d65a3650112f0a268'}
REG={'path':'configs/experiments/formal_main_v2.json','sha256':'a3f35d8e96d701c1a9ebadc2ad02259372cf6c91da6c9cb8d57c231892cf6ff9'}
PRIOR={
256:{'path':'results/formal_main_v2/engineering/supervision_delivery_0727/Long_terminal_independent/Long256_three_seed_statistics.json','sha256':'3ad37e5a918b92d7c9e8d5d0ea538584fe548a24bd0c9a03fd97c6ce28f69abb'},
64:{'path':'results/formal_main_v2/engineering/supervision_delivery_0830/Long64_terminal_independent/Long64_three_seed_statistics.json','sha256':'510cfc9c907b0d721df0ce39b6d528adddaf7b04575e848ec21e5622ba6f98d4'}}
evidence={}
def sha(b):return hashlib.sha256(b).hexdigest()
def load(ref):
 p=R/ref['path'];assert p.resolve()==p and R in p.parents and '..' not in p.parts
 b=p.read_bytes();assert sha(b)==ref['sha256'],ref['path']
 evidence[ref['path']]={'path':ref['path'],'sha256':ref['sha256'],'bytes':len(b)}
 return json.loads(b)
def assertnear(a,b,name):
 assert np.allclose(a,b,rtol=0,atol=1e-12),name
def interval(x):return np.percentile(x,[2.5,97.5],method='linear').tolist()
def compute(proof_ref):
 proof=load(proof_ref)
 assert proof['kind']=='explicit_legacy_development_compatibility_envelope'
 assert proof['status']=='real_bound_adoptions_and_legacy_evidence_verified'
 assert proof['legacy_execution_version']=='formal-downstream-root-v1' and proof['legacy_equivalent_trials']==600
 assert proof['target_action_semantics_sha256']==SEM and proof['all600_included'] is True
 assert proof['additional_independent_initial_states']==0 and proof['final_release'] is False
 assert proof['actual_new_wrapper_trials_added']==0 and proof['old_latency_reused'] is False
 st=load(REG)['statistics'];panel=load(PANEL)
 assert st['bootstrap_seed']==20261016 and st['bootstrap_repeats']==10000 and st['seed_sd_ddof']==1
 assert st['cluster']=='initial state carrying all3 training seeds' and st['task_weight']==st['suite_weight']=='equal'
 assert st['practical_dense_loss_margin']==.02
 assert panel['split']=='development' and len(panel['states'])==100
 states={x['trial_id']:{k:x[k] for k in ('task_id','task_name','source_state_index','initial_state_sha256')} for x in panel['states']}
 assert len(states)==100 and Counter(x['task_id'] for x in states.values())=={t:10 for t in range(10)}
 ordered=[sorted([sid for sid,x in states.items() if x['task_id']==t],key=lambda sid:(states[sid]['source_state_index'],sid)) for t in range(10)]
 compact={};roots={};allocations={}
 for jid,pin in JOBS.items():
  root=load({'path':f'results/formal_main_v2/downstream_reviews/{jid}.json','sha256':pin});roots[jid]=root
  summary=root['reconstructed_summary'];manifest=summary['provenance']['manifest']
  expected=600 if jid=='3019954' else 200
  assert root['status']=='passed' and root['scientific_complete'] is True
  assert root['completed_trials']==summary['completed_trials']==expected and summary['unique_initial_states']==100
  assert root['stage']=='development' and summary['suite']=='libero_10' and summary['split']=='development'
  assert summary['test_opened'] is False and root['final_state_values_read'] is False
  assert manifest['development_panel_sha256']==PANEL['sha256']
  assert manifest['environment']=={'environment_seed':0,'runtime_seed':17,'wait_steps':10,'action_chunk':8,'max_steps':520}
  ids=[x['identity']['method_id'] for x in manifest['methods']]
  if jid=='3019954':
   assert ids==['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17']
   assert root['raw_invocation_job_ids']==['3016981','3017161','3017959','3018505','3019176','3019954']
  else:
   assert root['execution_version']=='formal-downstream-action-v1' and root['historical_transition'] is None
   assert root['action_semantics_sha256']==SEM and root['raw_invocation_job_ids']==[jid]
  rel=Path(root['run_root']).relative_to(P).as_posix()+'/trials.jsonl'
  p=R/rel;b=p.read_bytes();h=sha(b)
  assert h==root['files'][rel]==summary['trials_jsonl_sha256']
  evidence[rel]={'path':rel,'sha256':h,'bytes':len(b)}
  seen=Counter();starts=set();results=set();rawjobs=[]
  for line in b.splitlines():
   row=json.loads(line);seen[row['event']]+=1
   if row['event']=='invocation':rawjobs.append(row['slurm_job_id']);continue
   sid=row['state_trial_id'];m=row['method'];key=(sid,m)
   assert sid in states and m in ids and row['split']=='development'
   for k,v in states[sid].items():assert row[k]==v,(jid,k)
   if row['event']=='start':
    assert key not in starts;starts.add(key);continue
   assert row['event']=='result' and key in starts and key not in results and key not in compact
   assert row['status']=='completed' and type(row['success']) is bool
   assert row['environment_seed']==0 and row['runtime_seed']==17 and row['wait_steps']==10 and row['action_chunk']==8
   assert 0<row['control_steps']<=520 and len(row['chunks'])==row['policy_calls']
   ch=row['chunks'][0];md=ch['metadata'];indices=md['retained_indices']
   assert len(set(indices))==len(indices)==md['visual_tokens']
   compact[key]={'success':int(row['success']),'job':jid,'trial_id':row['trial_id'],'initial_observation_sha256':ch['observation_sha256'],'initial_token_set':indices,'steps':row['control_steps'],'task_id':row['task_id']}
   results.add(key)
  assert seen['result']==seen['start']==expected and starts==results
  assert rawjobs==root['raw_invocation_job_ids']
  for a in root['cost']['allocations']:
   assert a['job_id'] not in allocations and a['status']=='COMPLETED' and a['exit_code']=='0:0' and a['gpus']==1
   allocations[a['job_id']]=a
  for pair in summary['paired_AB'].values():
   assert pair['completed_pairs']==pair['expected_pairs']==100
   # No outcome inference from paired summary: raw rows are the sole data source.
 assert len(compact)==2200
 assert set(m for sid,m in compact)==set(METHODS)
 assert all({m for s,m in compact if s==sid}==set(METHODS) for sid in states)
 arr=np.array([[[compact[sid,m]['success'] for m in METHODS] for sid in ids] for ids in ordered],dtype=np.int8)
 assert arr.shape==(10,10,22)
 # Same within-task cluster draws for all methods and all registered seeds.
 rng=np.random.default_rng(20261016);boot=np.zeros((10000,22),dtype=float);drawhash=hashlib.sha256();draws=[]
 for t in range(10):
  idx=rng.integers(0,10,size=(10000,10));draws.append(idx);drawhash.update(idx.astype('<i8').tobytes())
  boot+=arr[t][idx].mean(axis=1)/10
 method_results={}
 for j,m in enumerate(METHODS):
  method_results[m]={'successes':int(arr[:,:,j].sum()),'trials':100,'success_rate':float(arr[:,:,j].mean()),'per_task_successes':arr[:,:,j].sum(axis=1).tolist(),'CI95':interval(boot[:,j])}
 budgets={}
 for k in BUDGETS:
  positions=[METHODS.index(f'{m}{k}_seed{s}') for s in SEEDS for m in ('A','B')]
  x=arr[:,:,positions].reshape(10,10,3,2);br=boot[:,positions].reshape(10000,3,2).mean(axis=1)
  seed_rates=x.mean(axis=(0,1));seed_diff=seed_rates[:,1]-seed_rates[:,0]
  delta=br[:,1]-br[:,0];dense=boot[:,METHODS.index('dense')]
  # Alternate direct cluster-contrast calculation ensures no per-seed resampling.
  direct=np.zeros(10000)
  for t,idx in enumerate(draws):direct+=(x[t,:,:,1]-x[t,:,:,0]).mean(axis=1)[idx].mean(axis=1)/10
  assertnear(direct,delta,f'cluster proof{k}')
  perseed={}
  for si,s in enumerate(SEEDS):
   A=f'A{k}_seed{s}';B=f'B{k}_seed{s}';overlap=[]
   pairs=Counter()
   for ids in ordered:
    for sid in ids:
     a,b=compact[sid,A],compact[sid,B];assert a['initial_observation_sha256']==b['initial_observation_sha256']
     sa,sb=set(a['initial_token_set']),set(b['initial_token_set']);assert len(sa)==len(sb)==k
     overlap.append(len(sa&sb)/k);pairs[(a['success'],b['success'])]+=1
   perseed[str(s)]={'A_successes':int(x[:,:,si,0].sum()),'B_successes':int(x[:,:,si,1].sum()),'A_rate':float(seed_rates[si,0]),'B_rate':float(seed_rates[si,1]),'B_minus_A':float(seed_diff[si]),'per_task_A_successes':x[:,:,si,0].sum(axis=1).tolist(),'per_task_B_successes':x[:,:,si,1].sum(axis=1).tolist(),'paired_outcomes':{str(key):v for key,v in sorted(pairs.items())},'initial_token_overlap_mean':float(np.mean(overlap))}
  budgets[str(k)]={'per_seed':perseed,'A_mean':float(seed_rates[:,0].mean()),'B_mean':float(seed_rates[:,1].mean()),'B_minus_A':float(seed_diff.mean()),'A_seed_sd':float(seed_rates[:,0].std(ddof=1)),'B_seed_sd':float(seed_rates[:,1].std(ddof=1)),'B_minus_A_seed_sd':float(seed_diff.std(ddof=1)),'CI95_A':interval(br[:,0]),'CI95_B':interval(br[:,1]),'CI95_B_minus_A':interval(delta),'A_minus_Dense':float(seed_rates[:,0].mean()-method_results['dense']['success_rate']),'B_minus_Dense':float(seed_rates[:,1].mean()-method_results['dense']['success_rate']),'CI95_A_minus_Dense':interval(br[:,0]-dense),'CI95_B_minus_Dense':interval(br[:,1]-dense),'A_practical_lower_bound_gt_minus2pp':bool(interval(br[:,0]-dense)[0]>-.02+1e-12),'B_practical_lower_bound_gt_minus2pp':bool(interval(br[:,1]-dense)[0]>-.02+1e-12)}
  if k in PRIOR:
   prior=load(PRIOR[k]);mean=prior['mean_over_seeds'];std=prior['seed_std_ddof1'];pb=prior['paired_bootstrap'];v=budgets[str(k)]
   for a,z in [('A','A_success_rate'),('B','B_success_rate'),('B_minus_A','B_minus_A_success_rate')]:
    assertnear(v[a+'_mean' if a in ('A','B') else a],mean[z],f'prior{k} mean{a}')
    assertnear(v[a+'_seed_sd'],std[z],f'prior{k} sd{a}')
    assertnear(v['CI95_'+a],pb['CI95_'+a],f'prior{k} CI{a}')
   for s in SEEDS:
    for field in ('A_successes','B_successes','A_rate','B_rate','B_minus_A'):
     assertnear(perseed[str(s)][field],prior['per_seed'][str(s)][field],f'prior{k}/{s}/{field}')
    assertnear(perseed[str(s)]['initial_token_overlap_mean'],prior['per_seed'][str(s)]['token_overlap_initial_observation_mean'],f'prior{k}/{s}/overlap')
 gpu=sum(v['elapsed_seconds']*v['gpus'] for v in allocations.values());assert gpu==35408
 assert sum(v['elapsed_seconds'] for jid,v in allocations.items() if jid in JOBS and jid!='3019954')==24877
 assert len(allocations)==14
 uniform={}
 for k in BUDGETS:
  j=METHODS.index(f'uniform{k}');di=METHODS.index('dense')
  uniform[str(k)]={'rate_minus_Dense':float(arr[:,:,j].mean()-arr[:,:,di].mean()),'CI95_minus_Dense':interval(boot[:,j]-boot[:,di]),'practical_lower_bound_gt_minus2pp':bool(interval(boot[:,j]-boot[:,di])[0]>-.02+1e-12)}
 clusters=[{'state_trial_id':sid,**states[sid],'successes':{m:compact[sid,m]['success'] for m in METHODS}} for ids in ordered for sid in ids]
 return {'schema':'formal_main_v2','kind':'independent_Long22_development_statistics','status':'computed_from_raw','legacy_proof_ref':proof_ref,'trials':2200,'methods':22,'unique_initial_states':100,'tasks':10,'seeds':SEEDS,'budgets':budgets,'per_method':method_results,'uniform_against_Dense':uniform,'bootstrap':{'seed':20261016,'repeats':10000,'within_task_initial_state_cluster':True,'complete_three_seed_carry':True,'same_draws_all_methods':True,'draw_indices_little_endian_int64_sha256':drawhash.hexdigest(),'state_order':'source_state_index then state_trial_id','quantile_method':'linear','seed_sd_ddof':1},'cost':{'legacy600_GPU_seconds':10531,'new_wrapper1600_GPU_seconds':24877,'total_development_GPU_seconds':gpu,'new_GPU_seconds_this_review':0,'allocations':list(allocations.values())},'clusters':clusters,'evidence':list(evidence.values()),'old_execution_not_relabelled':True,'legacy_equivalent_trials':600,'actual_new_wrapper_trials':1600,'additional_independent_initial_states':0,'final_release':False,'test_opened':False,'O2A_latency_verified':False,'science_speed_frontier_claimed':False}

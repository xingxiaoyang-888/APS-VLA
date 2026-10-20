from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,types,traceback,time,os
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/Long22_statistics_independent_1032'
B='results/formal_main_v2/preflight/heartbeat_20261020T1832/'
PROOF={'path':B+'Long_legacy600_development_compatibility_proof.json','sha256':'8468cf4fe4f9cf80741cff7d6d659ab733472ef8d4c5e825e59c0cd8e02a002a'}
EXEC={'path':B+'Long_legacy600_root_proof_execution.json','sha256':'237aa5a79d612f66bf780af38bf0bcba843461be99e5f110f722479b69406bea'}
ROOT={'path':B+'Long22_development_statistics.json','sha256':'35557e76c338ec0cb12f5dbb5b1871dc04d0ad3a8a807134b1ef320728c3abf1'}
CORE_SHA='ee455c2e39bffce37372aa79de1a4517b39ae5e111c4be26eb077795ce6aee92'
def sha(b):return hashlib.sha256(b).hexdigest()
def guard(ev,args):
 if ev in ('subprocess.Popen','os.system','socket.connect','socket.bind'):raise RuntimeError('no processes/network')
 if ev=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes)):
   p=Path(os.fsdecode(path)).absolute()
   write=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
   if write and D not in p.parents:raise RuntimeError('write outside independent directory: '+str(p))
   if p.suffix in ('.pt','.pth','.ckpt','.safetensors','.pruned_init','.init') or 'sealed' in p.parts:raise RuntimeError('weight or sealed-value read')
sys.addaudithook(guard)
def put(name,obj):
 p=D/name;b=(json.dumps(obj,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)}
start=time.monotonic()
try:
 raw=(D/'statistics_core_a2.py').read_bytes();assert sha(raw)==CORE_SHA
 mod=types.ModuleType('independent_long22_core');mod.__file__=str(D/'statistics_core_a2.py')
 exec(compile(raw,mod.__file__,'exec',dont_inherit=True),mod.__dict__)
 execution=mod.load(EXEC);assert execution['status']=='real_adoption_and_explicit_proof_verified'
 assert execution['proof']==PROOF and execution['new_GPU_seconds']==execution['new_scientific_trials']==0
 assert execution['state_or_registry_changed'] is False and execution['production_general_consumer_modified'] is False
 root=mod.load(ROOT)
 assert root['status']=='computed_pending_independent_statistics_review'
 assert root['legacy_compatibility_proof']==PROOF and root['total_development_trials']==2200
 assert root['total_method_instances']==22 and root['unique_initial_state_clusters']==100
 assert root['legacy_equivalent_trials']==600 and root['current_wrapper_actual_trials']==1600
 assert root['final_release'] is False and root['final_state_values_read'] is False
 assert root['latency_executed'] is False and root['latency_reused'] is False
 independent=mod.compute(PROOF)
 assert root['configuration']==mod.load(mod.REG)['statistics']
 for artifact in root['artifacts']:
  if artifact['path'].endswith('_independent.json'):
   v=mod.load(artifact);assert v['status']=='passed' and v['scientific_complete'] is True and v['completed_trials']==200
   assert v['root_review']['sha256']==mod.JOBS[v['job_id']]
 # Every method/task statistic and its percentile interval from actual raw data.
 checks=0
 for method,v in independent['per_method'].items():
  r=root['per_method'][method]
  for field in ('successes','trials','success_rate','per_task_successes'):
   mod.assertnear(v[field],r[field],method+'/'+field);checks+=1
  mod.assertnear(v['CI95'],r['CI95_success_rate'],method+'/CI95');checks+=1
  islegacy=method in ('dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17')
  assert r['execution_evidence']['execution_version']==('formal-downstream-root-v1' if islegacy else 'formal-downstream-action-v1')
  assert r['execution_evidence']['trials']==100
 # Independently recompute root bootstrap vectors using integer cluster sums.
 pairs=mod.load(root['paired_states']);draw=mod.load(root['bootstrap_draws'])
 assert pairs['unique_initial_state_clusters']==100 and pairs['new_independent_states']==0
 order=draw['method_order'];assert len(order)==22 and set(order)==set(mod.METHODS) and pairs['method_order']==order
 ours={x['state_trial_id']:x for x in independent['clusters']}
 assert len(pairs['states'])==100
 for r in pairs['states']:
  i=ours[r['trial_id']]
  for f in ('task_id','task_name','source_state_index','initial_state_sha256'):assert i[f]==r[f]
  assert r['success_vector']==[i['successes'][m] for m in order]
 taskids=[sorted([sid for sid,v in ours.items() if v['task_id']==t],key=lambda sid:(ours[sid]['source_state_index'],sid)) for t in range(10)]
 a=np.asarray([[[ours[sid]['successes'][m] for m in order] for sid in sids] for sids in taskids],dtype=np.int16)
 rng=np.random.default_rng(20261016);sums=np.zeros((10000,22),dtype=np.int16);h=hashlib.sha256()
 for t in range(10):
  idx=rng.integers(0,10,size=(10000,10));h.update(idx.astype('<i8').tobytes())
  sums+=np.take(a[t],idx,axis=0).sum(axis=1,dtype=np.int16)
 draws=sums.astype(np.float64)/100
 assert draw['bootstrap_seed']==20261016 and draw['repeats']==10000
 assert h.hexdigest()==draw['draw_indices_little_endian_int64_sha256']==independent['bootstrap']['draw_indices_little_endian_int64_sha256']
 mod.assertnear(draws,draw['method_rate_draws'],'all220000 root method-rate draws');checks+=220000
 for k,v in independent['budgets'].items():
  r=root['budgets'][k]
  assert r['trial_count']==600 and r['unique_initial_state_clusters']==100 and r['all_seeds_carried_per_cluster'] is True
  for mine,theirs in [('A_mean','mean_A'),('B_mean','mean_B'),('B_minus_A','mean_B_minus_A'),('A_seed_sd','seed_sd_ddof1_A'),('B_seed_sd','seed_sd_ddof1_B'),('B_minus_A_seed_sd','seed_sd_ddof1_B_minus_A'),('CI95_A','CI95_A'),('CI95_B','CI95_B'),('CI95_B_minus_A','CI95_B_minus_A')]:
   mod.assertnear(v[mine],r[theirs],k+'/'+mine);checks+=1
  for seed,s in v['per_seed'].items():
   rs=r['per_seed'][seed]
   for f in ('A_rate','B_rate','B_minus_A','per_task_A_successes','per_task_B_successes'):mod.assertnear(s[f],rs[f],k+'/'+seed+'/'+f);checks+=1
   assert s['paired_outcomes'].get('(1, 0)',0)==rs['paired_A_only_success']
   assert s['paired_outcomes'].get('(0, 1)',0)==rs['paired_B_only_success']
   mod.assertnear(np.asarray(s['per_task_B_successes'])/10-np.asarray(s['per_task_A_successes'])/10,rs['per_task_B_minus_A'],k+'/'+seed+'/task_delta')
  for method in ('A','B'):
   cols=[order.index(f'{method}{k}_seed{s}') for s in mod.SEEDS];sample=draws[:,cols].mean(axis=1)
   for reference in ('dense','uniform'):
    rid='dense' if reference=='dense' else f'uniform{k}'
    sample_diff=sample-draws[:,order.index(rid)];rv=r['paired_comparisons'][method+'_minus_'+reference]
    mod.assertnear(mod.interval(sample_diff),rv['CI95'],k+'/'+method+'/'+reference+'/CI')
    mod.assertnear(sample_diff.mean(),rv['bootstrap_mean'],k+'/'+method+'/'+reference+'/bootmean')
    point=v[method+'_mean']-independent['per_method'][rid]['success_rate']
    mod.assertnear(point,rv['point_difference'],k+'/'+method+'/'+reference+'/point')
    if reference=='dense':
     # Equality to -0.02 is not a strictly-greater practical pass.
     accepted=bool(mod.interval(sample_diff)[0]>-.02+1e-12)
     assert accepted==rv['practical_lower_CI_strictly_above_minus002']
     assert accepted==v[method+'_practical_lower_bound_gt_minus2pp']
 assert {x['job_id']:x for x in root['historical_development_allocations']}=={x['job_id']:x for x in independent['cost']['allocations']}
 assert independent['cost']['total_development_GPU_seconds']==35408 and root['historical_cost_not_added_again'] is True
 assert root['all_original_results_preserved'] is True
 # Freeze evidence again without expanding into model/source/environment audits.
 for rel,desc in mod.evidence.items():
  b=(R/rel).read_bytes();assert sha(b)==desc['sha256'] and len(b)==desc['bytes'],rel
 independent['status']='passed_independent_raw_statistics_recomputation'
 independent['root_statistics_ref']=ROOT
 statistics_ref=put('independent_statistics.json',independent)
 review={'schema':'formal_main_v2','kind':'independent_Long22_development_statistics_review','status':'passed','review_role':'independent','root_statistics_ref':ROOT,'real_legacy_proof_ref':PROOF,'root_proof_execution_ref':EXEC,'independent_statistics_ref':statistics_ref,'counts':{'trials':2200,'methods':22,'unique_initial_state_clusters':100,'legacy_compatible_trials':600,'actual_new_wrapper_trials':1600,'all_seeds':mod.SEEDS,'all_tasks':10},'bootstrap':independent['bootstrap'],'root_comparison_checks':checks,'all_method_rate_draws_independently_recomputed':220000,'prior256_and64_statistics_consistent':True,'primary128':{key:independent['budgets']['128'][key] for key in ('A_mean','B_mean','B_minus_A','CI95_B_minus_A','A_seed_sd','B_seed_sd','B_minus_A_seed_sd')},'conclusion':'On the fixed Long development panel, B128 is worse than A128 in all three seeds; the task-stratified initial-state-cluster interval for B-A is entirely below zero. Supplemental256/64 improvements have intervals crossing zero; they are not proof of equivalence or a success-latency frontier.','same_initial_states_across_seeds_remain_one_cluster':True,'shared_Dense_and_uniform_references_not_replicated_as_training_seeds':True,'development_GPU_seconds_counted_once':35408,'new_GPU_seconds':0,'new_scientific_trials':0,'no_repeated_package_or_CPU_action_audit':True,'state_Git_or_production_changed':False,'final_release':False,'sealed_values_read':False,'latency_claim':False,'CPU_wall_seconds':time.monotonic()-start,'utc':datetime.now(timezone.utc).isoformat()}
 report_ref=put('independent_review.json',review)
 files=[]
 for p in sorted(D.iterdir()):
  if p.is_file() and p.name!='manifest.json':
   b=p.read_bytes();files.append({'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)})
 manifest_ref=put('manifest.json',{'schema':'formal_main_v2','kind':'independent_Long22_statistics_package','files':files,'report':report_ref,'statistics':statistics_ref,'scope':'existing fixed Long development22 methods; no GPU or scientific setting change'})
 print(json.dumps({'status':'passed','report':report_ref,'manifest':manifest_ref,'statistics':statistics_ref,'primary128':review['primary128'],'new_GPU_seconds':0,'CPU_wall_seconds':time.monotonic()-start}))
except BaseException as exc:
 put('failure_a1.json',{'status':'failed','type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'CPU_wall_seconds':time.monotonic()-start,'new_GPU_seconds':0,'state_Git_or_production_changed':False})
 raise

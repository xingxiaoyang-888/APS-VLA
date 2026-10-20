from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,time
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1832'
PROOF_REF={"path":"results/formal_main_v2/preflight/heartbeat_20261020T1832/Long_legacy600_development_compatibility_proof.json","sha256":"8468cf4fe4f9cf80741cff7d6d659ab733472ef8d4c5e825e59c0cd8e02a002a"}
PINS={"3043709":{"root_review":{"path":"results/formal_main_v2/downstream_reviews/3043709.json","sha256":"3868af9c4d8c5a1c2a896047f3b9d170b7fa2f1eaeb10fcc51689686a8589325"},"independent_review":{"path":"results/formal_main_v2/downstream_reviews/3043709_independent.json","sha256":"bc7e6d2abc1a73529d1b57d8a7f6e03ac4c301f8eb98c3565cd18ef03217535a"}},"3045322":{"root_review":{"path":"results/formal_main_v2/downstream_reviews/3045322.json","sha256":"d27e9bbf12e435ba3fd1341757b451e666b77528cd5fede6cb07ab19eb790699"},"independent_review":{"path":"results/formal_main_v2/downstream_reviews/3045322_independent.json","sha256":"a1824a68cc0120b485df2271701c56c188b18793903e378273fff12cb33759e6"}},"3046779":{"root_review":{"path":"results/formal_main_v2/downstream_reviews/3046779.json","sha256":"968b0e8b09577ce93320a02c1c69f5b37f6bc0256004962aaaa8a62e55789919"},"independent_review":{"path":"results/formal_main_v2/downstream_reviews/3046779_independent.json","sha256":"8beeb55a298179d25221ff01f0249c569a2fd9abd58659ef7272c8f2265bce4a"}},"3046798":{"root_review":{"path":"results/formal_main_v2/downstream_reviews/3046798.json","sha256":"251788eb33c35f2cd17e613d4bb4842cb1aa6ba6eb14937578fb1675a3d139de"},"independent_review":{"path":"results/formal_main_v2/downstream_reviews/3046798_independent.json","sha256":"2386c425fa645e5a00daaa019d1a055d3e9f222612ebcd6aa8dda82998888bec"}},"3047152":{"root_review":{"path":"results/formal_main_v2/downstream_reviews/3047152.json","sha256":"07c46b463db75271d7bdc6ecc43b43f9a20e4c88a351a88d16a735daf39ad03b"},"independent_review":{"path":"results/formal_main_v2/downstream_reviews/3047152_independent.json","sha256":"57ba312dbf5931bbe644dff9492cea7f12ec844cb28050f69012d33c27e80ec7"}},"3047156":{"root_review":{"path":"results/formal_main_v2/downstream_reviews/3047156.json","sha256":"9bd3713f5260d9b6da1397c6507330503ce429c59a4ea4a15986ac9a5d50e190"},"independent_review":{"path":"results/formal_main_v2/downstream_reviews/3047156_independent.json","sha256":"9cb561881876e7a40cc850bae9f38e12d1612960b16c6c5b27f0ec34ba2cb3d5"}},"3047163":{"root_review":{"path":"results/formal_main_v2/downstream_reviews/3047163.json","sha256":"5a1cc6e631a421f0891da6f6810fb0824717a37cd6d18fa26800e930acdac0bc"},"independent_review":{"path":"results/formal_main_v2/downstream_reviews/3047163_independent.json","sha256":"f507905b5a1ff214674ed39e2847fcda67224f62ec183915b2d5b5cd57dd9d57"}},"3047443":{"root_review":{"path":"results/formal_main_v2/downstream_reviews/3047443.json","sha256":"20f91c0060f086bcf402cc0b9b4e9863397c27876f4809dd9bef211aa0c87c25"},"independent_review":{"path":"results/formal_main_v2/downstream_reviews/3047443_independent.json","sha256":"0a04480cfae7c48beb8b4a81b99c5611d2273bd6f7c685a522beb096a7fd71d1"}}}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
refs=[]
def rd(rel,pin=None):
 p=R/rel
 if pin:assert h(p)==pin,rel
 refs.append(dict(path=rel,sha256=h(p)))
 return json.loads(p.read_bytes())
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
 return ref(rel)
start=time.monotonic();cpu=time.process_time()
proof=rd(PROOF_REF['path'],PROOF_REF['sha256'])
assert proof['kind']=='explicit_legacy_development_compatibility_envelope' and proof['status']=='real_bound_adoptions_and_legacy_evidence_verified'
assert proof['legacy_equivalent_trials']==600 and proof['actual_new_wrapper_trials_added']==0 and not proof['final_release']
assert not proof['original_invocations_ran_new_wrapper'] and proof['historical_GPU_seconds']==10531
for item in proof['adoptions'].values():rd(item['path'],item['sha256'])
reg=rd('configs/experiments/formal_main_v2.json','a3f35d8e96d701c1a9ebadc2ad02259372cf6c91da6c9cb8d57c231892cf6ff9')
stat=reg['statistics'];assert stat['bootstrap_repeats']==10000 and stat['bootstrap_seed']==20261016 and stat['seed_sd_ddof']==1
panel=rd('configs/manifests/formal_main_v2/libero_10/initial_states/development.json','46a06087483151e36198167e7d4e5313c50b63172e09128d65a3650112f0a268')
assert panel['split']=='development' and panel['suite']=='libero_10'
states=sorted([{k:v[k] for k in ('trial_id','task_id','task_name','source_state_index','initial_state_sha256')} for v in panel['states']],key=lambda v:(v['task_id'],v['source_state_index'],v['trial_id']))
assert len(states)==100 and len({x['trial_id'] for x in states})==100
known={x['trial_id']:x for x in states}
roots=[proof['original_root_review']]
for job,entry in PINS.items():
 root=rd(entry['root_review']['path'],entry['root_review']['sha256'])
 ind=rd(entry['independent_review']['path'],entry['independent_review']['sha256'])
 assert root['status']==ind['status']=='passed' and root['scientific_complete'] and root['completed_trials']==200
 assert root['job_id']==job and root['execution_version']=='formal-downstream-action-v1'
 assert root['action_semantics_sha256']==proof['target_action_semantics_sha256']
 assert not root['final_release'] and not root['final_state_values_read']
 roots.append(root)
data={};costs={};identities={};sources=[];method_meta={}
for root in roots:
 for allocation in root['cost']['allocations']:
  job=str(allocation['job_id'])
  if job in costs:assert costs[job]==allocation
  else:costs[job]=allocation
 paths=[x for x in root['files'] if x.endswith('/trials.jsonl')];assert len(paths)==1
 rel=paths[0];assert h(R/rel)==root['files'][rel];raw_ref=ref(rel);refs.append(raw_ref);sources.append(raw_ref)
 n=0
 with (R/rel).open() as stream:
  for line in stream:
   q=json.loads(line)
   if q['event']!='result':continue
   assert q['suite']=='libero_10' and q['split']=='development' and q['status']=='completed'
   assert type(q['success']) is bool and q['environment_seed']==0 and q['runtime_seed']==17
   assert q['action_chunk']==8 and q['configured_wait_steps']==q['wait_steps']==10
   st=known[q['state_trial_id']]
   for field in ('task_id','task_name','source_state_index','initial_state_sha256'):assert q[field]==st[field]
   key=(q['state_trial_id'],q['method']);assert key not in data;data[key]=q['success'];n+=1
   m=method_meta.setdefault(q['method'],dict(execution_version=root.get('execution_version','formal-downstream-root-v1'),source=raw_ref,trials=0))
   assert m['source']==raw_ref and m['execution_version']==root.get('execution_version','formal-downstream-root-v1');m['trials']+=1
 assert n==root['completed_trials']
methods=['dense','uniform256','uniform128','uniform64']+[f'{arm}{budget}_seed{seed}' for budget in [256,128,64] for seed in [17,23,41] for arm in ['A','B']]
assert set(m for _,m in data)==set(methods) and len(data)==2200 and all(x['trials']==100 for x in method_meta.values())
assert sum(m['trials'] for m in method_meta.values() if m['execution_version']=='formal-downstream-root-v1')==600
v=np.array([[int(data[st['trial_id'],m]) for m in methods] for st in states],dtype=np.int64).reshape(10,10,22)
assert all(sum(st['task_id']==t for st in states)==10 for t in range(10))
paired=save(B+'/Long22_paired_development_states.json',dict(schema='formal_main_v2',method_order=methods,states=[{**s,'success_vector':[int(data[s['trial_id'],m]) for m in methods]} for s in states],unique_initial_state_clusters=100,new_independent_states=0))
rng=np.random.default_rng(20261016);counts=np.zeros((10000,22),dtype=np.int64);dh=hashlib.sha256()
for task in range(10):
 idx=rng.integers(0,10,size=(10000,10));dh.update(idx.astype('<i8').tobytes(order='C'));counts+=v[task][idx].sum(axis=1)
draw=counts/100.;q95=lambda a:np.quantile(a,[.025,.975],method='linear').tolist()
draws=save(B+'/Long22_bootstrap_draws.json',dict(schema='formal_main_v2',method_order=methods,bootstrap_seed=20261016,repeats=10000,draw_indices_little_endian_int64_sha256=dh.hexdigest(),method_rate_draws=draw.tolist()))
def column(name):return methods.index(name)
per_method={}
for m in methods:
 i=column(m);per_method[m]=dict(successes=int(v[:,:,i].sum()),trials=100,success_rate=float(v[:,:,i].mean()),per_task_successes=v[:,:,i].sum(axis=1).tolist(),CI95_success_rate=q95(draw[:,i]),execution_evidence=method_meta[m])
budgets={}
for budget in [256,128,64]:
 ai=[column(f'A{budget}_seed{s}') for s in [17,23,41]];bi=[column(f'B{budget}_seed{s}') for s in [17,23,41]]
 ar=v[:,:,ai].mean(axis=(0,1));br=v[:,:,bi].mean(axis=(0,1));ad=draw[:,ai].mean(axis=1);bd=draw[:,bi].mean(axis=1)
 di=column('dense');ui=column(f'uniform{budget}');perseed={}
 for n,seed in enumerate([17,23,41]):
  aa=v[:,:,ai[n]];bb=v[:,:,bi[n]];perseed[str(seed)]=dict(A_rate=float(ar[n]),B_rate=float(br[n]),B_minus_A=float(br[n]-ar[n]),
   paired_A_only_success=int(np.sum((aa==1)&(bb==0))),paired_B_only_success=int(np.sum((aa==0)&(bb==1))),
   per_task_A_successes=aa.sum(axis=1).tolist(),per_task_B_successes=bb.sum(axis=1).tolist(),per_task_B_minus_A=(bb.mean(axis=1)-aa.mean(axis=1)).tolist(),
   A_minus_dense=float(ar[n]-v[:,:,di].mean()),B_minus_dense=float(br[n]-v[:,:,di].mean()))
 comparisons={}
 for name,dd in [('A_minus_dense',ad-draw[:,di]),('B_minus_dense',bd-draw[:,di]),('A_minus_uniform',ad-draw[:,ui]),('B_minus_uniform',bd-draw[:,ui])]:
  ci=q95(dd);comparisons[name]=dict(bootstrap_mean=float(dd.mean()),point_difference=float((ar.mean() if name.startswith('A_') else br.mean())-v[:,:,(di if 'dense' in name else ui)].mean()),CI95=ci)
  if 'dense' in name:comparisons[name]['practical_lower_CI_strictly_above_minus002']=bool(ci[0]>-.02)
 budgets[str(budget)]=dict(per_seed=perseed,mean_A=float(ar.mean()),mean_B=float(br.mean()),mean_B_minus_A=float((br-ar).mean()),
  seed_sd_ddof1_A=float(ar.std(ddof=1)),seed_sd_ddof1_B=float(br.std(ddof=1)),seed_sd_ddof1_B_minus_A=float((br-ar).std(ddof=1)),
  CI95_A=q95(ad),CI95_B=q95(bd),CI95_B_minus_A=q95(bd-ad),paired_comparisons=comparisons,
  unique_initial_state_clusters=100,trial_count=600,training_seeds=[17,23,41],all_seeds_carried_per_cluster=True)
# Existing256/64 summaries are a consistency check, not inputs to the estimates.
for budget,rel,pin in [(256,'results/formal_main_v2/engineering/supervision_delivery_0727/Long_terminal_independent/Long256_three_seed_statistics.json','3ad37e5a918b92d7c9e8d5d0ea538584fe548a24bd0c9a03fd97c6ce28f69abb'),(64,'results/formal_main_v2/engineering/supervision_delivery_0830/Long64_terminal_independent/Long64_three_seed_statistics.json','510cfc9c907b0d721df0ce39b6d528adddaf7b04575e848ec21e5622ba6f98d4')]:
 prev=rd(rel,pin);assert np.allclose(prev['paired_bootstrap']['CI95_B_minus_A'],budgets[str(budget)]['CI95_B_minus_A'],atol=1e-14,rtol=0)
 assert np.isclose(prev['mean_over_seeds']['B_minus_A_success_rate'],budgets[str(budget)]['mean_B_minus_A'],atol=1e-14,rtol=0)
for item in refs:assert h(R/item['path'])==item['sha256']
out=dict(schema='formal_main_v2',kind='root_Long22_development_statistics',status='computed_pending_independent_statistics_review',utc=datetime.now(timezone.utc).isoformat(),
 source=ref('.local/long22_stats_1032.py'),legacy_compatibility_proof=PROOF_REF,configuration=stat,paired_states=paired,bootstrap_draws=draws,
 total_method_instances=22,total_development_trials=2200,current_wrapper_actual_trials=1600,legacy_equivalent_trials=600,unique_initial_state_clusters=100,
 all_original_results_preserved=True,new_scientific_trials=0,new_GPU_seconds=0,per_method=per_method,budgets=budgets,
 historical_development_allocations=list(costs.values()),historical_cost_not_added_again=True,
 artifacts=refs,CPU_wall_seconds=time.monotonic()-start,CPU_process_seconds=time.process_time()-cpu,
 latency_executed=False,latency_reused=False,final_release=False,final_state_values_read=False,
 limitations=['Development only; no final main-table claim.','100 unique initial states; training-seed repeats remain in the same cluster.','Legacy600 classified by explicit source/action equivalence, never relabelled as new-wrapper execution.','All budgets and negative outcomes retained; no hyperparameter or checkpoint changes.','No O2A or speed frontier conclusion; no equivalence claim from a CI crossing zero.'])
output=save(B+'/Long22_development_statistics.json',out)
print(json.dumps(dict(status=out['status'],summary=output,means={k:{a:b[a] for a in ['mean_A','mean_B','mean_B_minus_A','CI95_B_minus_A']} for k,b in budgets.items()}),ensure_ascii=False),flush=True)

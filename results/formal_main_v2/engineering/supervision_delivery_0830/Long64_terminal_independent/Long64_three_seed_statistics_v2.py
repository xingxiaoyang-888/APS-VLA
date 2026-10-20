from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib,sys
import numpy as np
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=Path(__file__).resolve().parent
JOBS=[('3047156', 17, '9bd3713f5260d9b6da1397c6507330503ce429c59a4ea4a15986ac9a5d50e190', '.local/independent_long_development_0727/job3047156/independent_review.json', '9cb561881876e7a40cc850bae9f38e12d1612960b16c6c5b27f0ec34ba2cb3d5'), ('3047163', 23, '5a1cc6e631a421f0891da6f6810fb0824717a37cd6d18fa26800e930acdac0bc', '.local/independent_long_development_0727/job3047163/independent_review.json', 'f507905b5a1ff214674ed39e2847fcda67224f62ec183915b2d5b5cd57dd9d57'), ('3047443', 41, '20f91c0060f086bcf402cc0b9b4e9863397c27876f4809dd9bef211aa0c87c25', '.local/independent_long64_development_0830/job3047443/independent_review.json', '0a04480cfae7c48beb8b4a81b99c5611d2273bd6f7c685a522beb096a7fd71d1')]
evidence={}
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {'path':str(p.relative_to(R)),'sha256':sha(b),'bytes':len(b)}
def load(rel,pin):
 p=R/rel;q=ref(p);assert q['sha256']==pin,rel;evidence[rel]=q;return json.loads(p.read_bytes())
def save(name,v):
 p=D/name;b=json.dumps(v,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2).encode()+b'\n'
 with p.open('xb') as f:f.write(b)
 return ref(p)
reg=load('configs/experiments/formal_main_v2.json','a3f35d8e96d701c1a9ebadc2ad02259372cf6c91da6c9cb8d57c231892cf6ff9')
st=reg['statistics'];assert st['bootstrap_repeats']==10000 and st['bootstrap_seed']==20261016 and st['seed_sd_ddof']==1
assert st['cluster']=='initial state carrying all3 training seeds' and st['interval']=='95% percentile'
assert st['task_weight']=='equal' and st['suite_weight']=='equal'
roots={};reviews={};rawmaps={};panelsha=None;semantics=None;environment=None;states=None
for jid,seed,rpin,irel,ipin in JOBS:
 root=load('results/formal_main_v2/downstream_reviews/'+jid+'.json',rpin);ind=load(irel,ipin)
 assert root['status']==ind['status']=='passed' and root['scientific_complete'] and ind['scientific_complete']
 assert root['stage']==ind['stage']=='development' and root['suite']==ind['suite']=='libero_10'
 assert root['completed_trials']==ind['completed_trials']==200 and ind['unique_initial_states']==100
 assert ind['root_review']=={'path':'results/formal_main_v2/downstream_reviews/'+jid+'.json','sha256':rpin}
 assert ind['method_ids']==[f'A64_seed{seed}',f'B64_seed{seed}']
 assert root['raw_invocation_job_ids']==[jid] and root['historical_transition'] is None
 assert root['final_release'] is False and root['final_state_values_read'] is False
 m=root['reconstructed_summary']['provenance']['manifest'];sp=m['development_panel_sha256']
 if panelsha is None:
  panelsha=sp;semantics=root['action_semantics_sha256'];environment=m['environment'];panel=load(m['development_panel'],sp)
  assert panel['split']=='development' and len(panel['states'])==100
  states={x['trial_id']:{k:x[k] for k in ['task_id','task_name','source_state_index','initial_state_sha256']} for x in panel['states']}
  assert len(states)==100 and Counter(x['task_id'] for x in states.values())=={i:10 for i in range(10)}
 else:assert sp==panelsha and semantics==root['action_semantics_sha256'] and environment==m['environment']
 rel=Path(root['run_root']).relative_to(P).as_posix()+'/trials.jsonl';p=R/rel;q=ref(p)
 assert root['files'][rel]==q['sha256']==root['reconstructed_summary']['trials_jsonl_sha256'];evidence[rel]=q
 rows=[json.loads(x) for x in p.read_text().splitlines()];assert Counter(x['event'] for x in rows)=={'invocation':1,'start':200,'result':200}
 assert rows[0]['slurm_job_id']==jid
 results={};starts=set()
 for x in rows:
  if x['event']=='invocation':continue
  sid=x['state_trial_id'];mid=x['method'];a='A' if mid==f'A64_seed{seed}' else 'B' if mid==f'B64_seed{seed}' else None
  assert a and sid in states and x['split']=='development' and x['task_id']==states[sid]['task_id'] and x['initial_state_sha256']==states[sid]['initial_state_sha256']
  key=(sid,a)
  if x['event']=='start':assert key not in starts;starts.add(key);continue
  assert key in starts and key not in results and x['status']=='completed' and type(x['success']) is bool
  results[key]=int(x['success'])
 assert len(results)==200
 for a in ['A','B']:assert sum(results[sid,a] for sid in states)==ind['successes'][f'{a}64_seed{seed}']
 pairs={x['state_trial_id']:x for x in root['reconstructed_summary']['paired_AB'][f'k64_seed{seed}']['results']};assert set(pairs)==set(states)
 for sid in states:assert [int(pairs[sid]['A_success']),int(pairs[sid]['B_success']),pairs[sid]['B_minus_A']]==[results[sid,'A'],results[sid,'B'],results[sid,'B']-results[sid,'A']]
 roots[seed]=root;reviews[seed]=ind;rawmaps[seed]=results
ordered=[sorted([sid for sid,x in states.items() if x['task_id']==t],key=lambda sid:(states[sid]['source_state_index'],sid)) for t in range(10)]
seeds=[17,23,41];array=np.array([[[[rawmaps[s][sid,a] for a in ['A','B']] for s in seeds] for sid in ids] for ids in ordered],dtype=np.int8)
assert array.shape==(10,10,3,2)
seed_rates=array.mean(axis=(0,1));seed_diffs=seed_rates[:,1]-seed_rates[:,0]
perseed={};pertask={}
for k,seed in enumerate(seeds):
 ind=reviews[seed];a=seed_rates[k,0];b=seed_rates[k,1]
 perseed[str(seed)]={'A_successes':int(array[:,:,k,0].sum()),'B_successes':int(array[:,:,k,1].sum()),'A_rate':float(a),'B_rate':float(b),'B_minus_A':float(b-a),'paired_outcomes':ind['paired_outcomes'],'per_task':ind['per_task'],'token_overlap_initial_observation_mean':ind['initial_observation_token_overlap_mean'],'development_GPU_seconds':ind['cost']['current_GPU_seconds'],'job_id':ind['job_id']}
for t in range(10):
 tr=array[t].mean(axis=0);diff=tr[:,1]-tr[:,0]
 pertask[str(t)]={'task_name':states[ordered[t][0]]['task_name'],'unique_initial_states':10,'seed_A_rates':tr[:,0].tolist(),'seed_B_rates':tr[:,1].tolist(),'seed_B_minus_A':diff.tolist(),'A_mean':float(tr[:,0].mean()),'B_mean':float(tr[:,1].mean()),'B_minus_A_mean':float(diff.mean()),'A_seed_sd':float(tr[:,0].std(ddof=1)),'B_seed_sd':float(tr[:,1].std(ddof=1)),'B_minus_A_seed_sd':float(diff.std(ddof=1))}
# Each sampled initial-state index selects all3 seeds and both methods as one cluster.
rng=np.random.default_rng(st['bootstrap_seed']);boot=np.zeros((st['bootstrap_repeats'],2),dtype=float);drawhash=hashlib.sha256()
for t in range(10):
 idx=rng.integers(0,10,size=(st['bootstrap_repeats'],10));drawhash.update(idx.astype('<i8').tobytes(order='C'))
 boot+=array[t][idx,:,:].mean(axis=(1,2))/10
bootdiff=boot[:,1]-boot[:,0];ci=np.percentile(bootdiff,[2.5,97.5],method='linear')
# Equivalent resampling of the per-state average3-seed contrast is checked with the same draws.
rng2=np.random.default_rng(st['bootstrap_seed']);check=np.zeros(st['bootstrap_repeats'])
for t in range(10):
 idx=rng2.integers(0,10,size=(st['bootstrap_repeats'],10));contrasts=(array[t,:,:,1]-array[t,:,:,0]).mean(axis=1);check+=contrasts[idx].mean(axis=1)/10
assert np.allclose(check,bootdiff,atol=1e-12,rtol=0)
assert seed_rates.tolist()==[[.87,.88],[.85,.89],[.90,.94]]
paired=[{'state_trial_id':sid,**states[sid],'seed_order':seeds,'A_success_vector':[rawmaps[s][sid,'A'] for s in seeds],'B_success_vector':[rawmaps[s][sid,'B'] for s in seeds]} for ids in ordered for sid in ids]
pairedref=save('Long64_three_seed_paired_states.json',{'kind':'development_cluster_outcomes','unique_initial_states':100,'trials':600,'budget':64,'states':paired,'contains_initial_state_values':False})
bootref=save('Long64_three_seed_bootstrap_draws.json',{'seed':20261016,'repeats':10000,'rng':'numpy.default_rng PCG64','numpy_version':np.__version__,'task_order':list(range(10)),'state_order':'source_state_index ascending, then state_trial_id','draw_indices_little_endian_int64_sha256':drawhash.hexdigest(),'A_rate_draws':boot[:,0].tolist(),'B_rate_draws':boot[:,1].tolist(),'B_minus_A_draws':bootdiff.tolist()})
summary={'schema':'formal_main_v2','kind':'independent_Long64_three_seed_development_statistics','status':'passed','utc':datetime.now(timezone.utc).isoformat(),'suite':'libero_10','budget':64,'seeds':seeds,'total_trials':600,'unique_initial_states':100,'tasks':10,'initial_states_per_task':10,'per_seed':perseed,'per_task':pertask,'mean_over_seeds':{'A_success_rate':float(seed_rates[:,0].mean()),'B_success_rate':float(seed_rates[:,1].mean()),'B_minus_A_success_rate':float(seed_diffs.mean())},'seed_std_ddof1':{'A_success_rate':float(seed_rates[:,0].std(ddof=1)),'B_success_rate':float(seed_rates[:,1].std(ddof=1)),'B_minus_A_success_rate':float(seed_diffs.std(ddof=1))},'paired_bootstrap':{'configuration':st,'CI95_B_minus_A':ci.tolist(),'CI95_A':np.percentile(boot[:,0],[2.5,97.5],method='linear').tolist(),'CI95_B':np.percentile(boot[:,1],[2.5,97.5],method='linear').tolist(),'quantile_method':'linear','cluster_has_all3_seeds_and_both_methods':True,'resample_within_each_task':True,'equivalent_state_mean_resampling_check':True,'conditional_on_registered_tasks_and_three_seeds':True,'p_value_reported':False},'cost':{'actual_development_GPU_seconds':sum(v['cost']['current_GPU_seconds'] for v in reviews.values()),'actual_new_job_GPU_seconds':3039,'training_or_timing_cost_included':False,'nested_phases_added':False},'same_development_panel_sha256':panelsha,'same_action_semantics_sha256':semantics,'same_environment':environment,'paired_states':pairedref,'bootstrap_draws':bootref,'evidence':list(evidence.values()),'final_release':False,'test_opened':False,'O2A_latency_verified':False,'dense_reference_included':False,'practical_dense_margin_evaluated':False,'cross_budget_aggregate':False,'other_budget_statistics_recomputed':False,'limitations':['Only Long64 development results; not the final main table.','All600 trials reuse100 unique initial states; three training seeds do not increase the initial-state sample size.','No O2A timing or dense comparison is included; no success-speed frontier conclusion.','128-token negative outcomes and all256-token results remain separately preserved; no cross-budget pooling.','The interval conditions on these tasks and registered training seeds; final sealed results remain unopened.']}
sref=save('Long64_three_seed_statistics.json',summary)
lines=['# Long64 三种子开发统计','', '仅开发面板，3 seed 共600条试验、100个唯一初态；未开放最终初态。','', '|seed|A成功/100|B成功/100|B−A百分点|初观测token重合率|GPU秒|','|---|---:|---:|---:|---:|---:|']
for seed in seeds:
 v=perseed[str(seed)];lines.append(f"|{seed}|{v['A_successes']}|{v['B_successes']}|{100*v['B_minus_A']:.2f}|{v['token_overlap_initial_observation_mean']:.6f}|{v['development_GPU_seconds']}|")
lines+=['',f"A均值 {100*seed_rates[:,0].mean():.3f}%（种子间SD {100*seed_rates[:,0].std(ddof=1):.3f}pp）；B均值 {100*seed_rates[:,1].mean():.3f}%（SD {100*seed_rates[:,1].std(ddof=1):.3f}pp）。",f"B−A均值 {100*seed_diffs.mean():+.3f}pp，种子间SD {100*seed_diffs.std(ddof=1):.3f}pp；任务内初态簇携完整三seed配对bootstrap（seed20261016，10000次），95%百分位区间 [{100*ci[0]:+.3f}, {100*ci[1]:+.3f}]pp。",'', '开发闭环成本为3次真实单GPU分配之和9102秒，其中本轮新增3039秒；不含训练或测速成本。','本统计不是最终主表；没有完整O2A、Dense参照或性能—速度折中结论。128预算负结果与256预算全部结果均单独保留，不混预算。','']
p=D/'Long64_three_seed_statistics.md'
with p.open('x') as f:f.write('\n'.join(lines))
print(json.dumps({'statistics':sref,'mean':summary['mean_over_seeds'],'seed_sd':summary['seed_std_ddof1'],'CI95_B_minus_A':ci.tolist(),'new_GPU_seconds':3039,'all64_development_GPU_seconds':9102}))

from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D='.local/independent_long64_development_0830'
B='results/formal_main_v2/preflight/heartbeat_20261020T1630'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def checked(rel,pin):
 assert h(R/rel)==pin,rel
 return json.loads((R/rel).read_bytes())
st=checked(D+'/Long64_three_seed_statistics.json','510cfc9c907b0d721df0ce39b6d528adddaf7b04575e848ec21e5622ba6f98d4')
paired=checked(st['paired_states']['path'],st['paired_states']['sha256'])
draws=checked(st['bootstrap_draws']['path'],st['bootstrap_draws']['sha256'])
reg=checked('configs/experiments/formal_main_v2.json','a3f35d8e96d701c1a9ebadc2ad02259372cf6c91da6c9cb8d57c231892cf6ff9')
assert st['paired_bootstrap']['configuration']==reg['statistics']
seeds=[17,23,41];states=paired['states'];assert len(states)==100
assert len(set(x['state_trial_id'] for x in states))==100
raw={}
for job,seed,pin in [('3047156',17,'9bd3713f5260d9b6da1397c6507330503ce429c59a4ea4a15986ac9a5d50e190'),('3047163',23,'5a1cc6e631a421f0891da6f6810fb0824717a37cd6d18fa26800e930acdac0bc'),('3047443',41,'20f91c0060f086bcf402cc0b9b4e9863397c27876f4809dd9bef211aa0c87c25')]:
 rr=checked('results/formal_main_v2/downstream_reviews/'+job+'.json',pin)
 paths=[p for p in rr['files'] if p.endswith('/trials.jsonl')];assert len(paths)==1
 p=paths[0];assert h(R/p)==rr['files'][p]
 result={}
 with (R/p).open() as stream:
  for line in stream:
   q=json.loads(line)
   if q['event']!='result':continue
   key=(q['state_trial_id'],q['method'])
   assert q['split']=='development' and q['status']=='completed' and type(q['success']) is bool and key not in result
   result[key]=q
 assert len(result)==200
 raw[seed]=result
for q in states:
 assert q['seed_order']==seeds
 for i,seed in enumerate(seeds):
  for arm in ['A','B']:
   x=raw[seed][q['state_trial_id'],f'{arm}64_seed{seed}']
   assert x['task_id']==q['task_id'] and x['initial_state_sha256']==q['initial_state_sha256']
   assert int(x['success'])==q[arm+'_success_vector'][i]
ordered=sorted(states,key=lambda x:(x['task_id'],x['source_state_index'],x['state_trial_id']))
assert states==ordered
# Independent root recomputation uses integer success counts for each state cluster.
v=np.array([[q['A_success_vector'],q['B_success_vector']] for q in states],dtype=np.int64).reshape(10,10,2,3)
counts=v.sum(axis=3);seedrates=v.mean(axis=(0,1)).T
assert seedrates.tolist()==[[.87,.88],[.85,.89],[.90,.94]]
rng=np.random.default_rng(20261016)
total=np.zeros((10000,2),dtype=np.int64);dh=hashlib.sha256()
for t in range(10):
 assert sum(q['task_id']==t for q in states)==10
 idx=rng.integers(0,10,size=(10000,10))
 dh.update(idx.astype('<i8').tobytes(order='C'))
 total+=counts[t][idx].sum(axis=1)
calc=total/300.;contrast=(total[:,1]-total[:,0])/300.
assert dh.hexdigest()==draws['draw_indices_little_endian_int64_sha256']
for k,x in [('A_rate_draws',calc[:,0]),('B_rate_draws',calc[:,1]),('B_minus_A_draws',contrast)]:
 assert np.allclose(x,draws[k],atol=1e-14,rtol=0),k
ci=np.percentile(contrast,[2.5,97.5],method='linear')
assert np.allclose(ci,st['paired_bootstrap']['CI95_B_minus_A'],atol=1e-14,rtol=0)
for name,x in [('A_success_rate',seedrates[:,0]),('B_success_rate',seedrates[:,1]),('B_minus_A_success_rate',seedrates[:,1]-seedrates[:,0])]:
 assert np.isclose(x.mean(),st['mean_over_seeds'][name],atol=1e-14,rtol=0)
 assert np.isclose(x.std(ddof=1),st['seed_std_ddof1'][name],atol=1e-14,rtol=0)
for t in range(10):
 rates=v[t].mean(axis=0).T;q=st['per_task'][str(t)]
 assert np.array_equal(rates[:,0],q['seed_A_rates']) and np.array_equal(rates[:,1],q['seed_B_rates'])
assert sum(x['development_GPU_seconds'] for x in st['per_seed'].values())==9102
report=dict(schema='formal_main_v2',status='passed',kind='root_independent_integer_cluster_recomputation',utc=datetime.now(timezone.utc).isoformat(),source=dict(path='.local/verify_long64_stats_0830.py',sha256=h(Path(__file__))),independent_statistics=dict(path=D+'/Long64_three_seed_statistics.json',sha256=h(R/D/'Long64_three_seed_statistics.json')),raw_trial_outcomes_verified=600,unique_initial_state_clusters=100,all3_seeds_carried_per_cluster=True,registered_bootstrap_repeats=10000,registered_bootstrap_seed=20261016,task_equal_weight=True,seed_sd_ddof=1,integer_sampling_SHA=dh.hexdigest(),all30000_reported_draw_values_verified=True,CI95_B_minus_A=ci.tolist(),point_difference=float((seedrates[:,1]-seedrates[:,0]).mean()),development_GPU_seconds=9102,new_GPU_jobs=0,final_state_values_read=False,final_release=False,latency_claim=False,equivalence_claim=False,maximum_float_tolerance=1e-14)
p=R/B/'Long64_root_statistics_verification.json'
with p.open('x') as f:json.dump(report,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(report=dict(path=p.relative_to(R).as_posix(),sha256=h(p)),CI95_B_minus_A=ci.tolist(),status='passed')))

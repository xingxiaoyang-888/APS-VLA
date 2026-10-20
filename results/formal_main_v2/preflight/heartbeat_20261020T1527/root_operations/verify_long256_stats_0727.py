from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D='.local/independent_long_development_0727'
B='results/formal_main_v2/preflight/heartbeat_20261020T1527'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def checked(rel,pin):
 assert h(R/rel)==pin,rel
 return json.loads((R/rel).read_bytes())
st=checked(D+'/Long256_three_seed_statistics.json','3ad37e5a918b92d7c9e8d5d0ea538584fe548a24bd0c9a03fd97c6ce28f69abb')
paired=checked(st['paired_states']['path'],st['paired_states']['sha256'])
draws=checked(st['bootstrap_draws']['path'],st['bootstrap_draws']['sha256'])
reg=checked('configs/experiments/formal_main_v2.json','a3f35d8e96d701c1a9ebadc2ad02259372cf6c91da6c9cb8d57c231892cf6ff9')
assert st['paired_bootstrap']['configuration']==reg['statistics']
seeds=[17,23,41];states=paired['states'];assert len(states)==100
assert len(set(x['state_trial_id'] for x in states))==100
raw={}
for job,seed,pin in [('3046779',17,'968b0e8b09577ce93320a02c1c69f5b37f6bc0256004962aaaa8a62e55789919'),('3046798',23,'251788eb33c35f2cd17e613d4bb4842cb1aa6ba6eb14937578fb1675a3d139de'),('3047152',41,'07c46b463db75271d7bdc6ecc43b43f9a20e4c88a351a88d16a735daf39ad03b')]:
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
   x=raw[seed][q['state_trial_id'],f'{arm}256_seed{seed}']
   assert x['task_id']==q['task_id'] and x['initial_state_sha256']==q['initial_state_sha256']
   assert int(x['success'])==q[arm+'_success_vector'][i]
ordered=sorted(states,key=lambda x:(x['task_id'],x['source_state_index'],x['state_trial_id']))
assert states==ordered
# Independent root recomputation uses integer success counts for each state cluster.
v=np.array([[q['A_success_vector'],q['B_success_vector']] for q in states],dtype=np.int64).reshape(10,10,2,3)
counts=v.sum(axis=3);seedrates=v.mean(axis=(0,1)).T
assert seedrates.tolist()==[[.92,.95],[.94,.96],[.92,.94]]
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
assert sum(x['development_GPU_seconds'] for x in st['per_seed'].values())==9226
report=dict(schema='formal_main_v2',status='passed',kind='root_independent_integer_cluster_recomputation',utc=datetime.now(timezone.utc).isoformat(),source=dict(path='.local/verify_long256_stats_0727.py',sha256=h(Path(__file__))),independent_statistics=dict(path=D+'/Long256_three_seed_statistics.json',sha256=h(R/D/'Long256_three_seed_statistics.json')),raw_trial_outcomes_verified=600,unique_initial_state_clusters=100,all3_seeds_carried_per_cluster=True,registered_bootstrap_repeats=10000,registered_bootstrap_seed=20261016,task_equal_weight=True,seed_sd_ddof=1,integer_sampling_SHA=dh.hexdigest(),all30000_reported_draw_values_verified=True,CI95_B_minus_A=ci.tolist(),point_difference=float((seedrates[:,1]-seedrates[:,0]).mean()),development_GPU_seconds=9226,new_GPU_jobs=0,final_state_values_read=False,final_release=False,latency_claim=False,equivalence_claim=False,maximum_float_tolerance=1e-14)
p=R/B/'Long256_root_statistics_verification.json'
with p.open('x') as f:json.dump(report,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(report=dict(path=p.relative_to(R).as_posix(),sha256=h(p)),CI95_B_minus_A=ci.tolist(),status='passed')))

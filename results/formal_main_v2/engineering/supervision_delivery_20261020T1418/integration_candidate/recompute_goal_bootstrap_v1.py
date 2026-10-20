"""Independent root recomputation from original accepted paired outcomes; read-only."""
from pathlib import Path
import hashlib,json
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
E='results/formal_main_v2/engineering/supervision_delivery_20261020T1418/terminal_independent'
MATRIX=(E+'/Goal128_paired_matrix.json','35104178cba959a5650b0e5fb7a5b06d6cdf27704e7a0602d3d649b8bfecf362')
STATS=(E+'/development_statistics.json','26db7c37f100857e7e789dc7fbea74e0c2c2728e864a8b35f8fdde7ddc97c1cd')
ROOTS=[('3048609',17,'7e3fc5858ed27baacfb878cec8adea70e8e43df736e9f2f785eb1a189c5f31a8'),('3049191',23,'56a9bf2d1145ec5adc3efdc3a1ac145ac8d59a49a00325924068e7c49f7b7feb'),('3049622',41,'ffc074a3cc374a7d348488bdac0ac28c5575865630dd551ba97858a841671c23')]
def read(rel,pin):
 raw=(R/rel).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=pin:raise ValueError('Exact input SHA mismatch: '+rel)
 return json.loads(raw)
def ref(rel,pin):return dict(path=rel,sha256=pin)
def recompute():
 matrix=read(*MATRIX);expected=read(*STATS)['suites']['libero_goal']
 assert matrix['seeds']==[17,23,41] and matrix['budget']==128 and matrix['suite']=='libero_goal'
 assert matrix['unique_initial_states']==100 and matrix['method_trials']==600 and expected['available_seeds']==[17,23,41]
 coords=matrix['state_coordinates'];assert len(coords)==len({x['state_trial_id'] for x in coords})==100
 assert [x['task_id'] for x in coords]==[t for t in range(10) for _ in range(10)]
 A=np.empty((10,10,3),dtype=np.int64);B=np.empty_like(A);roots=[]
 for si,(jid,seed,pin) in enumerate(ROOTS):
  rel='results/formal_main_v2/downstream_reviews/'+jid+'.json';root=read(rel,pin)
  assert root['status']=='passed' and root['scientific_complete'] and root['suite']=='libero_goal'
  pair=root['reconstructed_summary']['paired_AB']['k128_seed'+str(seed)];assert pair['completed_pairs']==100
  rows={x['state_trial_id']:x for x in pair['results']};assert set(rows)=={x['state_trial_id'] for x in coords}
  for i,c in enumerate(coords):
   row=rows[c['state_trial_id']]
   # Original paired results encode success booleans (A_success/B_success).
   A[i//10,i%10,si]=int(row['A_success']);B[i//10,i%10,si]=int(row['B_success'])
  roots.append(ref(rel,pin))
 assert np.array_equal(A,np.asarray(matrix['A_success'])) and np.array_equal(B,np.asarray(matrix['B_success']))
 assert np.isin(A,[0,1]).all() and np.isin(B,[0,1]).all()
 # Each draw independently resamples ten initials inside every fixed task.
 # The same selected cluster carries both methods and all three training seeds.
 draws=np.random.default_rng(20261016).integers(0,10,size=(10000,10,10),dtype=np.int64)
 a_draw=np.zeros(10000);b_draw=np.zeros(10000)
 for task in range(10):
  a_draw+=A[task][draws[:,task,:]].sum(axis=(1,2))/300
  b_draw+=B[task][draws[:,task,:]].sum(axis=(1,2))/300
 # Compute the paired difference directly, avoiding quantile drift from subtracting rounded means.
 d_draw=np.zeros(10000)
 for task in range(10):d_draw+=(B[task]-A[task])[draws[:,task,:]].sum(axis=(1,2))/300
 means=dict(A=float(A.mean()*100),B=float(B.mean()*100),B_minus_A_pp=float((B-A).mean()*100))
 cis={k:[float(v*100) for v in np.quantile(a,[.025,.975])] for k,a in [('A',a_draw),('B',b_draw),('B_minus_A',d_draw)]}
 seedA=A.mean(axis=(0,1))*100;seedB=B.mean(axis=(0,1))*100
 sd=dict(A=float(seedA.std(ddof=1)),B=float(seedB.std(ddof=1)),B_minus_A=float((seedB-seedA).std(ddof=1)))
 for k,v in means.items():assert np.isclose(v,expected['means_percent'][k],atol=1e-10)
 for k,v in cis.items():assert np.allclose(v,expected['bootstrap_interval95_pp'][k],atol=1e-10)
 for k,v in sd.items():assert np.isclose(v,expected['seed_sample_SD_pp'][k],atol=1e-10)
 return dict(schema='formal_main_v2',kind='independent_root_original_pair_bootstrap_recomputation',status='passed',
  input_matrix=ref(*MATRIX),statistics_comparison=ref(*STATS),original_root_receipts=roots,
  source=dict(path=str(Path(__file__).relative_to(R)),sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
  bootstrap_seed=20261016,bootstrap_repeats=10000,interval='95% percentile; linear np.quantile',
  algorithm='Fixed ten equally weighted tasks. Within each task resample ten initial-state clusters with replacement, carrying A/B and all three seeds. NumPy default_rng(20261016).integers(0,10,size=(10000,10,10),dtype=int64).',
  unique_initial_states=100,method_trials=600,means_percent=means,bootstrap_interval95_pp=cis,seed_sample_SD_pp=sd,
  exact_paired_matrix_reconstructed_from_original_root_receipts=True,development_only=True,
  final_results=False,measured_latency=False,new_GPU_jobs=0,canonical_writes=False)
if __name__=='__main__':print(json.dumps(recompute(),ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False))

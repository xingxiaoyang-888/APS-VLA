from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,time,traceback,sys,os
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/integration_independent_20261020T1418'
E='results/formal_main_v2/engineering/supervision_delivery_20261020T1418/terminal_independent'
ROOTS=[('3048609',17,'7e3fc5858ed27baacfb878cec8adea70e8e43df736e9f2f785eb1a189c5f31a8'),('3049191',23,'56a9bf2d1145ec5adc3efdc3a1ac145ac8d59a49a00325924068e7c49f7b7feb'),('3049622',41,'ffc074a3cc374a7d348488bdac0ac28c5575865630dd551ba97858a841671c23')]
checks=[];refs=[];t=time.perf_counter()
def guard(event,args):
 if event.startswith(('socket.','subprocess.')) or event in ['os.system','os.fork','os.posix_spawn']:raise PermissionError(event)
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(args[0]);mode=args[1];flags=args[2]
  if (isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)):
   assert p.resolve().is_relative_to(D.resolve()),str(p)
  assert p.suffix not in ['.pt','.pth','.safetensors','.bin'],'weight read'
  assert 'initial_states/final' not in str(p),'sealed values'
sys.addaudithook(guard)
def rd(rel,pin,base=R):
 p=base/rel;b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==pin,rel
 refs.append(dict(path=str(p),sha256=pin,bytes=len(b)));return json.loads(b)
def chk(name,v):assert v,name;checks.append(name)
def out(name,v):
 p=D/name;assert not p.exists();p.write_text(json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
 return dict(path=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
def main():
 m=rd(E+'/Goal128_paired_matrix.json','35104178cba959a5650b0e5fb7a5b06d6cdf27704e7a0602d3d649b8bfecf362')
 st=rd(E+'/development_statistics.json','26db7c37f100857e7e789dc7fbea74e0c2c2728e864a8b35f8fdde7ddc97c1cd')['suites']['libero_goal']
 coords=m['state_coordinates'];chk('fixed_three_seed100initial_scope',m['axes']==['task','within_task_state','seed'] and m['seeds']==[17,23,41] and m['unique_initial_states']==100 and m['method_trials']==600 and m['budget']==128 and m['suite']=='libero_goal')
 chk('ten_tasks_ten_unique_initials',len(coords)==len({c['state_trial_id'] for c in coords})==100 and [c['task_id'] for c in coords]==[i for i in range(10) for _ in range(10)])
 A=np.zeros((10,10,3),dtype=np.int64);B=np.zeros_like(A);dense=np.zeros((10,10),dtype=np.int64)
 for si,(jid,seed,pin) in enumerate(ROOTS):
  rr=rd('results/formal_main_v2/downstream_reviews/'+jid+'.json',pin)
  chk(jid+'_accepted_original_root',rr['status']=='passed' and rr['scientific_complete'] and rr['stage']=='development' and not rr['final_release'] and not rr['final_state_values_read'])
  pair=rr['reconstructed_summary']['paired_AB']['k128_seed'+str(seed)];pairs={x['state_trial_id']:x for x in pair['results']}
  chk(jid+'_same100coordinates',pair['completed_pairs']==100 and set(pairs)=={c['state_trial_id'] for c in coords})
  for i,c in enumerate(coords):
   x=pairs[c['state_trial_id']];chk(jid+'_bool_'+str(i),type(x['A_success'])==bool and type(x['B_success'])==bool)
   A[i//10,i%10,si]=int(x['A_success']);B[i//10,i%10,si]=int(x['B_success'])
  if si==0:
   rel=next(k for k in rr['files'] if k.endswith('/trials.jsonl'));pin=rr['files'][rel]
   raw=(R/rel).read_bytes();chk('dense_original_R_P_exact',hashlib.sha256(raw).hexdigest()==pin==hashlib.sha256((P/rel).read_bytes()).hexdigest());refs.append(dict(path=rel,sha256=pin,bytes=len(raw)))
   rows=[json.loads(x) for x in raw.splitlines() if x.strip()]
   starts=[x for x in rows if x['event']=='start' and x.get('method')=='dense'];results=[x for x in rows if x['event']=='result' and x.get('method')=='dense']
   chk('single_shared_dense100_no_seed_replication',len(starts)==len(results)==100 and len({x['state_trial_id'] for x in results})==100)
   byid={x['state_trial_id']:x for x in results};bs={x['state_trial_id']:x for x in starts}
   for i,c in enumerate(coords):
    x=byid[c['state_trial_id']];start=bs[c['state_trial_id']]
    chk('dense_pair_'+str(i),x['initial_state_sha256']==start['initial_state_sha256']==c['initial_state_sha256'] and x['task_id']==c['task_id'] and x['source_state_index']==c['source_state_index'] and x['runtime_seed']==17 and x['environment_seed']==0 and x['configured_wait_steps']==x['wait_steps']==10 and x['action_chunk']==8 and x['split']=='development' and x['status']=='completed' and type(x['success'])==bool)
    dense[i//10,i%10]=int(x['success'])
 chk('matrix_matches_all_original_pairs',np.array_equal(A,m['A_success']) and np.array_equal(B,m['B_success']) and int(dense.sum())==97)
 ix=np.random.default_rng(20261016).integers(0,10,size=(10000,10,10),dtype=np.int64)
 # Sum integer success counts across resampled task-state clusters first. Each dense cluster is paired to all three seeds.
 ac=np.zeros(10000,dtype=np.int64);bc=np.zeros_like(ac);dc=np.zeros_like(ac)
 for task in range(10):
  ac+=A[task][ix[:,task,:]].sum(axis=(1,2));bc+=B[task][ix[:,task,:]].sum(axis=(1,2));dc+=dense[task][ix[:,task,:]].sum(axis=1)*3
 ci={k:np.quantile(v/3,[.025,.975]).tolist() for k,v in [('A',ac),('B',bc),('B_minus_A',bc-ac),('A_minus_dense',ac-dc),('B_minus_dense',bc-dc)]}
 for k in ['A','B','B_minus_A']:chk('paired_CI_'+k,np.allclose(ci[k],st['bootstrap_interval95_pp'][k],atol=1e-10,rtol=0))
 for k in ['A','B']:chk('paired_dense_CI_'+k,np.allclose(ci[k+'_minus_dense'],st['shared_dense'][k+'_minus_dense_CI95_pp'],atol=1e-10,rtol=0))
 means=dict(A=float(A.sum()/3),B=float(B.sum()/3),B_minus_A_pp=float((B-A).sum()/3),dense=float(dense.sum()),A_minus_dense_pp=float(A.sum()/3-dense.sum()),B_minus_dense_pp=float(B.sum()/3-dense.sum()))
 for k in ['A','B','B_minus_A_pp']:chk('mean_'+k,abs(means[k]-st['means_percent'][k])<1e-10)
 for k in ['A','B']:chk('dense_mean_'+k,abs(means[k+'_minus_dense_pp']-st['shared_dense'][k+'_minus_dense_pp'])<1e-10 and st['shared_dense'][k+'_meets_development_margin']==(ci[k+'_minus_dense'][0]>-2))
 sa=A.sum(axis=(0,1));sb=B.sum(axis=(0,1));sd=dict(A=float(sa.std(ddof=1)),B=float(sb.std(ddof=1)),B_minus_A=float((sb-sa).std(ddof=1)))
 for k in sd:chk('seed_sample_SD_'+k,abs(sd[k]-st['seed_sample_SD_pp'][k])<1e-10)
 chk('no_equivalence_or_latency_final_claim',st['development_only'] and st['no_equivalence_or_O2A_tradeoff_claim'] and not st['shared_dense']['A_meets_development_margin'] and not st['shared_dense']['B_meets_development_margin'])
 evidence=out('Goal_dense_statistical_check_evidence.json',dict(status='passed',checks=checks,inputs=refs,algorithm='Integer pooled counts in 10000 stratified task-state cluster draws, shared dense count multiplied by3 to pair each selected cluster with all three train seeds; divide by3 for percentage units. No independent-initial inflation.',bootstrap_seed=20261016,bootstrap_repeats=10000))
 result=out('Goal_dense_statistics_independent_review.json',dict(schema='formal_main_v2',kind='independent_Goal_AB_and_shared_dense_paired_statistics_recomputation',status='passed',reviewer='/root/devplans_audit_20261020_1418',utc=datetime.now(timezone.utc).isoformat(),source=dict(path=str(Path(__file__).relative_to(R)),sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),checks_passed=len(checks),check_evidence=evidence,means_percent=means,bootstrap_interval95_pp=ci,seed_sample_SD_pp=sd,unique_initials=100,training_seeds=[17,23,41],AB_method_trials=600,shared_dense_trials=100,bootstrap_repeats=10000,bootstrap_seed=20261016,development_only=True,equivalence_supported=False,O2A_measured=False,final_release=False,sealed_final_values_read=False,new_GPU_jobs=0,new_GPU_seconds=0,new_scheduler_queries=0,state_Git_Slurm_modified=False,CPU_wall_seconds=time.perf_counter()-t))
 print(json.dumps(dict(status='passed',report=result,checks=len(checks),dense_CI={k:v for k,v in ci.items() if 'dense' in k})))
if __name__=='__main__':
 try:main()
 except Exception as ex:out('Goal_dense_failure_v1.json',dict(status='failed',error=repr(ex),traceback=traceback.format_exc(),checks_passed=len(checks)));raise

"""Rebuild Spatial256 three-seed cluster bootstrap directly from original development ledgers.
No model, simulator, scheduler, state, or Git activity. Optional output is caller-chosen R path.
"""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--statistics-ref',required=True);ap.add_argument('--statistics-sha',required=True);ap.add_argument('--output');a=ap.parse_args();seen={}
 def get(rel,pin):
  p=R/rel;assert p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(R)
  assert p.suffix in {'.json','.jsonl'} and not any(c in p.parts for c in ['final','test','weights','checkpoints'])
  b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==pin
  seen[rel]=pin;return json.loads(b)
 stat=get(a.statistics_ref,a.statistics_sha);st=stat['suites']['libero_spatial'];assert st['available_seeds']==[17,23,41] and st['visual_tokens']==256
 mr=st['paired_matrix'];matrix=get(mr['path'],mr['sha256']);assert matrix['axes']==['task','within_task_state','seed'] and matrix['seeds']==[17,23,41]
 entries={};all_t0={};ledgers=matrix['raw_ledger_refs'];assert len(ledgers)==3
 for ref in ledgers:
  p=R/ref['path'];b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==ref['sha256'] and b.endswith(b'\n');seen[ref['path']]=ref['sha256']
  rows=[json.loads(l) for l in b.splitlines()];rs=[r for r in rows if r['event']=='result'];assert len(rs)==200
  for r in rs:
   assert r['split']=='development' and r['suite']=='libero_spatial' and r['status']=='completed' and type(r['success']) is bool
   assert r['environment_seed']==0 and r['runtime_seed']==17 and r['wait_steps']==10 and r['action_chunk']==8
   arm=r['method'][0];seed=int(r['method'].split('_seed')[1]);assert r['method']==f'{arm}256_seed{seed}' and arm in ['A','B'] and seed in [17,23,41]
   stid=(r['task_id'],r['source_state_index'],r['state_trial_id'],r['initial_state_sha256']);key=(stid,seed,arm)
   assert key not in entries;entries[key]=int(r['success']);ch=r['chunks'][0];assert ch['control_step']==0
   assert all_t0.setdefault(stid,ch['observation_sha256'])==ch['observation_sha256']
 states=sorted({k[0] for k in entries});assert len(states)==100 and len(entries)==600 and len(all_t0)==100
 coords=[{'task_id':s[0],'source_state_index':s[1],'state_trial_id':s[2],'initial_state_sha256':s[3]} for s in states];assert coords==matrix['state_coordinates']
 A=np.array([[[entries[(s,z,'A')] for z in [17,23,41]] for s in states if s[0]==t] for t in range(10)],dtype=np.int64)
 B=np.array([[[entries[(s,z,'B')] for z in [17,23,41]] for s in states if s[0]==t] for t in range(10)],dtype=np.int64)
 assert A.shape==B.shape==(10,10,3) and A.tolist()==matrix['A_success'] and B.tolist()==matrix['B_success']
 seedA=A.mean((0,1))*100;seedB=B.mean((0,1))*100;seedD=(B-A).mean((0,1))*100
 assert [r['A_successes'] for r in st['per_seed']]==A.sum((0,1)).tolist() and [r['B_successes'] for r in st['per_seed']]==B.sum((0,1)).tolist()
 means={'A':float(A.mean()*100),'B':float(B.mean()*100),'B_minus_A_pp':float((B-A).mean()*100)};sd={'A':float(seedA.std(ddof=1)),'B':float(seedB.std(ddof=1)),'B_minus_A':float(seedD.std(ddof=1))}
 for k in means:assert np.isclose(means[k],st['means_percent'][k],rtol=0,atol=1e-12)
 for k in sd:assert np.isclose(sd[k],st['seed_sample_SD_pp'][k],rtol=0,atol=1e-12)
 gen=np.random.default_rng(20261016);draws=gen.integers(0,10,size=(10000,10,10),dtype=np.int64)
 boot={};ci={}
 # Average within each state first, then resample those state clusters; all three seeds travel together.
 for label,values in [('A',A),('B',B),('B_minus_A',B-A)]:
  clusters=values.mean(2);summed=np.zeros(10000,dtype=float)
  for t in range(10):summed+=clusters[t][draws[:,t,:]].mean(1)/10
  boot[label]=summed;ci[label]=(np.quantile(summed,[.025,.975],method='linear')*100).tolist()
  assert np.allclose(ci[label],st['bootstrap_interval95_pp'][label],rtol=0,atol=1e-12)
 per_seed_ci=[]
 for z in range(3):
  summed=np.zeros(10000,dtype=float)
  for t in range(10):summed+=(B[t,:,z]-A[t,:,z])[draws[:,t,:]].mean(1)/10
  interval=(np.quantile(summed,[.025,.975],method='linear')*100).tolist();per_seed_ci.append(interval)
  assert np.allclose(interval,st['per_seed'][z]['B_minus_A_bootstrap_CI95_pp'],rtol=0,atol=1e-12)
 for rel,h in seen.items():assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==h
 out={'kind':'raw_ledger_Spatial256_bootstrap_recomputation','status':'passed','statistics_ref':{'path':a.statistics_ref,'sha256':a.statistics_sha},'paired_matrix':mr,'unique_initial_states':100,'method_trials':600,'seeds':[17,23,41],'means_percent':means,'seed_sample_SD_pp':sd,'bootstrap_repeats':10000,'bootstrap_seed':20261016,'RNG':'numpy.default_rng PCG64, int64 draws [10000,10,10]','bootstrap_interval95_pp':ci,'per_seed_B_minus_A_CI95_pp':per_seed_ci,'algorithm':'Average all3seed outcomes within each initial-state cluster, resample10clusters within each fixedtask, mean across10tasks, paired A/B; quantile method linear.','all_inputs':seen,'sealed_final_values_read':False,'new_GPU_jobs':0,'root_signoff_claimed':False}
 if a.output:
  p=R/a.output;assert p.resolve().is_relative_to(R) and p.suffix=='.json' and not p.exists()
  with p.open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()

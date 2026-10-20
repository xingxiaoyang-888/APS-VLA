"""Independent raw-ledger k64 statistics, CPU only. Never executes root analysis code."""
from pathlib import Path
import hashlib,json,math,os,statistics,sys,time,traceback
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=R/'.local/k64_stats_independent_20261020T2156'
TARGET='results/formal_main_v2/preflight/heartbeat_20261021T0556/Spatial_Object64_three_seed_development_statistics.json';TSHA='d327e603eb76790d1dd30f4f6cdd9b5364121343eb01cd65298cf31c1959926d'
CONFIG='configs/experiments/formal_main_v2.json';CSHA='a3f35d8e96d701c1a9ebadc2ad02259372cf6c91da6c9cb8d57c231892cf6ff9'
ROOTCODE='.local/k64_stats_20261020T2156.py';RCSHA='f969e0b98b80c6b5da3037ad1cf18344a91d3c5f7fceb9875fba0dca66e0b0bc'
TABLE={
 'libero_spatial':[(17,'3050870','421cbed0b5a0fa49','7ec911f486b420ce2aa0aea0488756da310400fb3d9b2c917bbdf121383e228d','23927594362df4b4b3b4448a5059e338a40dfb58dd36a445275879f61252785f'),(23,'3053875','2eea5a76505a0f3c','93bf032cfdaa62491b8098d793bfd55067b0889d935634ced960420ace7cfab5','ee00999e50f845b88f22c45f8d5164d232fd1b53ae1f9cf588bdb0aa8ea4da43'),(41,'3050890','b426228fe9d2fd0a','ea6b56ca023f9ba72023e965915f15959595bd9d0aceb7e43b65bf1bb2ebe1b5','425e22b9a6ee0ed39acca3151ca5666f3efdfdd7b6cda7a4c090d0b00464dbb6')],
 'libero_object':[(17,'3050901','421cbed0b5a0fa49','c622348228cb00dbfdcd905e0209c750538fffa5f0bc1ae5ebde2b6ab4247306','c42aef780e8fb366041f0ca62e3704d7cdc782aeb53b6bd1018aa13ac0bbe9be'),(23,'3053894','2eea5a76505a0f3c','9dfe225277c8a7b75f5b8c722c551c6d507dada6c2eda14d6a76b76d3b03e2b6','afedb854ad6e2559b876ba86bf805309ff948e9f086da10232699fa5bfe91d0f'),(41,'3050916','b426228fe9d2fd0a','f1cd6bbfe83e1b7be1ebfddc69d00776292d8d6c849f344cd4f78818d26a0627','b1f3a6f4d28e2dd1ad33800cd8c27edde1d06548a59c467e92257e6a2151ec30')]}
PANELSHAS={'libero_spatial':'07718b648bfb767472506c48b0ef1837a5e6af992c2460e7567c275064809c91','libero_object':'6b7e6dd9fb5b6351ee47c7bb30eab911e7c144d700cd88f7e5162641738b2d6a'}
INDS={17:('results/formal_main_v2/downstream_reviews/four64_20261020T1644_independent.json','d3170418334cc545bd760472463a7e165a44b233393b81dff76f5eea72c397ce'),23:('results/formal_main_v2/downstream_reviews/3053875_3053894_independent.json','4f95cad2dac8f8e6a69806445658824b42ebf1104e4849cec0a5c12028f20c7b')}
INDS[41]=INDS[17]
refs={};checks=[];began=time.perf_counter();cput=time.process_time()
def ck(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
def h(p):
 d=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):d.update(b)
 return d.hexdigest()
def watch(p,pin=None):
 digest=h(p)
 if pin is not None:ck('sha:'+str(p),digest==pin)
 if str(p) in refs:ck('stable_read:'+str(p),refs[str(p)]['sha256']==digest)
 refs[str(p)]={'path':str(p),'sha256':digest,'bytes':p.stat().st_size};return refs[str(p)]
def rd(p,pin=None):watch(p,pin);return json.loads(p.read_bytes())
def save(name,value):
 p=D/name
 with p.open('x') as f:json.dump(value,f,ensure_ascii=False,allow_nan=False,sort_keys=True,indent=2);f.write('\n')
 return {'path':str(p.relative_to(R)),'sha256':h(p)}
def guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','socket.bind'):raise RuntimeError('No subprocess or network in statistics audit')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  if any('sealed' in s.lower() for s in p.parts) or ('final' in p.parts and p.name=='panel.json'):raise RuntimeError('Sealed values forbidden')
  mode,flags=args[1:3];w=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if w and not p.is_relative_to(D):raise RuntimeError('Only independent private writes')
def close(a,b):return math.isclose(float(a),float(b),rel_tol=0,abs_tol=1e-14)
def insert_result(out,row,panel,suite,methods):
 assert row['status']=='completed' and type(row['success']) is bool
 assert row['suite']==suite and row['split']=='development' and row['method'] in methods
 key=(row['state_trial_id'],row['method']);assert key not in out
 state=panel[row['state_trial_id']]
 for name in ['task_id','task_name','source_state_index','initial_state_sha256']:assert row[name]==state[name]
 assert row['trial_id']==row['state_trial_id']+':'+row['method']
 assert row['environment_seed']==0 and row['runtime_seed']==17 and row['action_chunk']==8 and row['configured_wait_steps']==10 and row['wait_steps']==10
 assert row['termination'] in ['environment_success','max_steps','environment_done']
 out[key]=int(row['success'])
def percentile_sorted(xs,p):
 at=p*(len(xs)-1);lo=math.floor(at);hi=math.ceil(at);return float(xs[lo]+(xs[hi]-xs[lo])*(at-lo))
def main():
 sys.dont_write_bytecode=True;os.environ['CUDA_VISIBLE_DEVICES']='';sys.addaudithook(guard)
 config=rd(R/CONFIG,CSHA);stat=config['statistics'];ck('frozen_statistics',stat['bootstrap_repeats']==10000 and stat['bootstrap_seed']==20261016 and stat['seed_sd_ddof']==1 and stat['task_weight']=='equal' and stat['cluster']=='initial state carrying all3 training seeds')
 watch(R/ROOTCODE,RCSHA)
 suite_results={};private_data={};allocated=set();negatives=[]
 for suite,table in TABLE.items():
  panel=rd(R/f'configs/manifests/formal_main_v2/{suite}/initial_states/development.json',PANELSHAS[suite]);ck('development_panel_'+suite,panel['suite']==suite and panel['split']=='development' and panel['environment_seed']==0)
  states=sorted(panel['states'],key=lambda x:(x['task_id'],x['source_state_index'],x['trial_id']));lookup={x['trial_id']:x for x in states};ck('100_unique_10_per_task_'+suite,len(states)==len(lookup)==100 and all(sum(s['task_id']==t for s in states)==10 for t in range(10)))
  methods=[f'{arm}64_seed{seed}' for seed in [17,23,41] for arm in ['A','B']];success={};cost=[];per_seed={};rawlines=[]
  for seed,jid,run,rawsha,rrsha in table:
   rr=rd(R/f'results/formal_main_v2/downstream_reviews/{jid}.json',rrsha);ck('original_root_terminal_'+jid,rr['status']=='passed' and rr['scientific_complete'] and rr['completed_trials']==200 and rr['execution_version']=='formal-downstream-action-v1' and rr['job_id']==jid and rr['suite']==suite and not rr['final_release'] and not rr['final_state_values_read'])
   indrel,indsha=INDS[seed];ind=rd(R/indrel,indsha);ck('original_independent_terminal_'+jid,ind['status']=='passed' and jid in ind['jobs'])
   jobs=[x for x in rr['registered_jobs_at_review'] if str(x['job_id'])==jid];ck('one_original_allocation_'+jid,len(jobs)==1)
   job=jobs[0];ck('complete_GPU_identity_'+jid,job['status']=='COMPLETED' and job['exit_code']=='0:0' and job['gpus']==1 and job['suite']==suite and job['method_ids']==[f'A64_seed{seed}',f'B64_seed{seed}'] and not job['prior_job_ids'] and jid not in allocated);allocated.add(jid)
   seconds=job['elapsed_seconds'];ck('original_allocation_cost_'+jid,rr['cost']['all_attempt_gpu_seconds']==seconds and len(rr['cost']['allocations'])==1);cost.append({'job_id':jid,'GPU_seconds':seconds})
   rel=f'results/formal_main_v2/{suite}/downstream/development/{run}/attempt01/trials.jsonl';watch(R/rel,rawsha);watch(P/rel,rawsha);ck('root_links_actual_raw_'+jid,rr['reconstructed_summary']['trials_jsonl_sha256']==rawsha)
   outcomes={};start=[];rowcount=0;last=None
   with (R/rel).open('rb') as f:
    for num,line in enumerate(f,1):
     row=json.loads(line)
     if row.get('event')=='start':start.append(row['trial_id'])
     if row.get('event')!='result':continue
     insert_result(outcomes,row,lookup,suite,[f'A64_seed{seed}',f'B64_seed{seed}']);last=row;rowcount+=1
     for chunk in row['chunks']:
      meta=chunk['metadata'];assert meta['training_seed']==seed and meta['suite']==suite and meta['visual_tokens']==64 and meta['per_camera_budgets']==[32,32] and meta['future_head_calls']==0
     rawlines.append({'job_id':jid,'line':num,'line_sha256':hashlib.sha256(line).hexdigest(),'state_trial_id':row['state_trial_id'],'method':row['method'],'success':row['success'],'task_id':row['task_id'],'initial_state_sha256':row['initial_state_sha256']})
   ck('200_exact_results_and_starts_'+jid,rowcount==len(outcomes)==len(start)==len(set(start))==200 and set(start)=={k[0]+':'+k[1] for k in outcomes})
   ck('complete_cartesian_panel_'+jid,set(outcomes)=={(x['trial_id'],m) for x in states for m in [f'A64_seed{seed}',f'B64_seed{seed}']})
   # meaningful rejection checks against the same raw validator, never alter ledger.
   for name,mut in [('duplicate',{}),('wrong_state_hash',{'initial_state_sha256':'0'*64}),('wrong_suite',{'suite':'libero_goal'}),('wrong_budget',{'method':f'A128_seed{seed}'}),('nonboolean_success',{'success':1})]:
    q=dict(last);q.update(mut);tableout=dict(outcomes) if name=='duplicate' else {}
    try:insert_result(tableout,q,lookup,suite,[f'A64_seed{seed}',f'B64_seed{seed}'])
    except (AssertionError,KeyError):negatives.append(jid+':'+name)
    else:raise AssertionError('invalid result accepted:'+name)
   success.update(outcomes)
   av=[outcomes[x['trial_id'],f'A64_seed{seed}'] for x in states];bv=[outcomes[x['trial_id'],f'B64_seed{seed}'] for x in states]
   per_seed[str(seed)]={'job_id':jid,'A_successes':sum(av),'B_successes':sum(bv),'A_rate':sum(av)/100,'B_rate':sum(bv)/100,'B_minus_A':sum(b-a for a,b in zip(av,bv))/100,'A_only':sum(a==1 and b==0 for a,b in zip(av,bv)),'B_only':sum(a==0 and b==1 for a,b in zip(av,bv)),'per_task_A_successes':[sum(av[t*10:t*10+10]) for t in range(10)],'per_task_B_successes':[sum(bv[t*10:t*10+10]) for t in range(10)],'per_task_B_minus_A':[sum(b-a for a,b in zip(av[t*10:t*10+10],bv[t*10:t*10+10]))/10 for t in range(10)]}
  rows=[{'state_trial_id':x['trial_id'],'task_id':x['task_id'],'source_state_index':x['source_state_index'],'success_vector':[success[x['trial_id'],m] for m in methods]} for x in states]
  # Entire RNG tensor, then multiplicity-weighted aggregation. Distinct implementation
  # from root's task-by-task indexed summation; all six outputs share each drawn state.
  draw_indices=np.random.default_rng(20261016).integers(0,10,size=(10,10000,10))
  draw_counts=np.zeros((10000,6),dtype=np.int64)
  for t in range(10):
   multiplicities=np.zeros((10000,10),dtype=np.int64)
   np.add.at(multiplicities,(np.repeat(np.arange(10000),10),draw_indices[t].ravel()),1)
   ck('10_clusters_per_draw_'+suite+'_'+str(t),np.all(multiplicities.sum(axis=1)==10))
   task_outcomes=np.array([q['success_vector'] for q in rows if q['task_id']==t],dtype=np.int64)
   draw_counts+=multiplicities @ task_outcomes
  differences=sorted((int(sum(row[1::2]))-int(sum(row[::2])))/300 for row in draw_counts)
  A=[per_seed[str(s)]['A_rate'] for s in [17,23,41]];B=[per_seed[str(s)]['B_rate'] for s in [17,23,41]];diff=[b-a for a,b in zip(A,B)]
  result={'per_seed':per_seed,'mean_A':statistics.mean(A),'mean_B':statistics.mean(B),'mean_B_minus_A':statistics.mean(diff),'seed_sd_ddof1_A':statistics.stdev(A),'seed_sd_ddof1_B':statistics.stdev(B),'seed_sd_ddof1_B_minus_A':statistics.stdev(diff),'CI95_B_minus_A':[percentile_sorted(differences,p) for p in [.025,.975]],'trials':len(success),'unique_state_clusters':len(states),'allocations':cost,'allocation_GPU_seconds':sum(q['GPU_seconds'] for q in cost)}
  ck('600_trials_100_clusters_'+suite,len(success)==600 and len(states)==100)
  rawref=save(suite+'_raw_result_index.json',{'rows':rawlines,'all_successes_and_failures_preserved':True,'normal_policy_outcomes_only_already_admitted_by_original_reviews':True})
  matrix={'method_order':methods,'states':rows,'unique_state_clusters':100};draw={'method_order':methods,'bootstrap_seed':20261016,'repeats':10000,'draw_indices_little_endian_int64_sha256':hashlib.sha256(draw_indices.astype('<i8').tobytes()).hexdigest(),'success_count_draws':draw_counts.tolist()}
  private_data[suite]={'matrix':matrix,'draws':draw};result['independent_raw_index']=rawref;result['independent_matrix']=save(suite+'_paired_states.json',matrix);result['independent_draws']=save(suite+'_bootstrap_draws.json',draw);suite_results[suite]=result
 # Compare only after both suites are computed completely from actual raw records.
 target=rd(R/TARGET,TSHA);ck('target_registration_scope',target['development_only'] and not target['final_release'] and not target['final_state_values_read'] and target['bootstrap_seed']==20261016 and target['task_stratified_bootstrap_repeats']==10000 and target['seed_order']==[17,23,41])
 for suite,actual in suite_results.items():
  reported=target['suite_results'][suite]
  for field in ['mean_A','mean_B','mean_B_minus_A','seed_sd_ddof1_A','seed_sd_ddof1_B','seed_sd_ddof1_B_minus_A']:ck('reported_float_'+suite+'_'+field,close(actual[field],reported[field]))
  for field in ['trials','unique_state_clusters','allocations','allocation_GPU_seconds','CI95_B_minus_A']:ck('reported_exact_'+suite+'_'+field,actual[field]==reported[field])
  for seed,values in actual['per_seed'].items():
   for name,value in values.items():ck('reported_per_seed_'+suite+'_'+seed+'_'+name,value==reported['per_seed'][seed][name])
  for field,ours in [('paired_states','matrix'),('bootstrap_draws','draws')]:
   ref=reported[field];value=rd(R/ref['path'],ref['sha256']);ck('complete_raw_reconstruction_comparison_'+suite+'_'+field,value==private_data[suite][ours])
 ck('30_distinct_raw_guard_negatives',len(negatives)==30)
 for path,ref in refs.items():ck('final_input_unchanged:'+path,h(Path(path))==ref['sha256'])
 out={'schema':'formal_main_v2','kind':'independent_raw_Spatial_Object64_three_seed_statistics_review','status':'passed','blockers':[],'root_statistics_sha256':TSHA,'root_statistics_path':TARGET,'reviewed_by':'independent','review_agent':'/root/spatial588_recovery_audit_2054','suite_results':suite_results,'checks':checks,'check_count':len(checks),'input_refs':list(refs.values()),'negative_case_names':negatives,'root_analysis_code_executed':False,'root_intermediate_pairs_used_for_reconstruction':False,'independent_aggregation':'One 10x10000x10 index tensor; per-task multiplicity matrices multiplied by raw six-column state outcomes. Explicit sorted linear percentile calculation. Python statistics sample standard deviations.','cluster_unit':'initial state within task carrying A/B for all 3 training seeds','bootstrap_repeats':10000,'bootstrap_seed':20261016,'independent_initial_states_per_suite':100,'success_trials_per_suite':600,'development_only':True,'is_final_success_rate':False,'scientific_release':False,'final_state_values_read':False,'O2A_executed':False,'new_trials':0,'new_GPU_seconds':0,'historical_allocations_counted_once_in_comparison_not_added_to_state':True,'no_equivalence_claim':True,'state_registry_Git_Slurm_mutations':0,'CPU_seconds':time.process_time()-cput,'wall_seconds':time.perf_counter()-began}
 rr=save('independent_statistics_review.json',out);print(json.dumps({'review':rr,'checks':len(checks),'suites':{k:{n:v[n] for n in ['mean_A','mean_B','mean_B_minus_A','CI95_B_minus_A']} for k,v in suite_results.items()}}),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as e:save('failure_'+str(time.time_ns())+'.json',{'error':str(e),'traceback':traceback.format_exc(),'checks':checks});raise

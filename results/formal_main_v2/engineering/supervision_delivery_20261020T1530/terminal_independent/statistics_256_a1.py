"""Fixed-protocol development statistics and bounded diagnosis; never changes execution."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter,defaultdict
import json,hashlib,gzip,sys,types,time,traceback
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/devterminal_independent_20261020T1530';B='results/formal_main_v2/preflight/heartbeat_20261020T2330'
inputs={};started=time.monotonic()
def sha(b):return hashlib.sha256(b).hexdigest()
def read(rel,pin=None):
 p=R/rel;assert p.is_file() and not p.is_symlink()
 assert p.suffix not in {'.pt','.pth','.bin','.safetensors','.ckpt','.pkl','.pickle','.pruned_init','.init'}
 assert not any(x in p.parts for x in ['test','final','weights','checkpoints'])
 b=p.read_bytes();h=sha(b);assert pin is None or h==pin,(rel,h,pin)
 if rel in inputs:assert inputs[rel]['sha256']==h
 inputs[rel]={'sha256':h,'bytes':len(b)};return b
def jr(rel,pin=None):return json.loads(read(rel,pin))
def ref(rel):b=read(rel);return {'path':rel,'sha256':sha(b),'bytes':len(b)}
def put(name,value):
 b=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode();p=D/name
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)}
def mod(rel,pin,name):
 src=read(rel,pin);m=types.ModuleType(name);m.__file__=str(R/rel);sys.modules[name]=m;exec(compile(src,m.__file__,'exec'),m.__dict__);return m

try:
 newref={'path':'.local/devterminal_independent_20261020T1530/independent_review.json','sha256':'bc6ec59ace7431daa18056a2f64352be3f909d902644c5b0a0c546249bf879d8'}
 oldref={'path':'results/formal_main_v2/engineering/supervision_delivery_20261020T1418/terminal_independent/independent_review.json','sha256':'ad8c588b38df5d774f7da678ff75b2931743156de8b1e4d373f1f5358c22fead'}
 new=jr(newref['path'],newref['sha256']);old=jr(oldref['path'],oldref['sha256'])
 assert all(x['status']=='passed' and x['review_role']=='independent' for x in [new,old])
 selected={'3049632','3049657','3050192','3050205','3050224'}
 pairs=[];metadata={};rawrefs=[];rootrefs=[];initialpanels={}
 for report in [old,new]:
  pr=report['paired_states'];data=jr(pr['path'],pr['sha256'])
  for jid,job in report['jobs'].items():
   if jid not in selected:continue
   suite=job['suite'];seed=job['training_seed'];budget=job['A_B_visual_tokens'];assert budget==256
   key=(suite,budget,seed);assert key not in metadata;metadata[key]=job
   rootref=job['root_receipt'];root=jr(rootref['path'],rootref['sha256']);assert root['job_id']==jid
   rootrefs.append(rootref)
   if suite in initialpanels:assert initialpanels[suite]==report['shared_initial_panels_sha256'][suite]
   initialpanels[suite]=report['shared_initial_panels_sha256'][suite]
   ledger=job['raw_ledger'];rows=[json.loads(x) for x in read(ledger['path'],ledger['sha256']).splitlines()];results=[x for x in rows if x['event']=='result'];rawrefs.append(ledger)
   assert len(results)==200 and {r['method'] for r in results}=={f'A256_seed{seed}',f'B256_seed{seed}'}
   pool=[dict(r) for r in data['states'] if r['suite']==suite and r['training_seed']==seed and r['visual_tokens']==256];assert len(pool)==100
   for row in pool:
    ar=next(x for x in results if x['state_trial_id']==row['state_trial_id'] and x['method']==f'A256_seed{seed}')
    br=next(x for x in results if x['state_trial_id']==row['state_trial_id'] and x['method']==f'B256_seed{seed}')
    assert (ar['success'],br['success'])==(row['A_success'],row['B_success'])
    for f in ['initial_state_sha256','source_state_index','task_id','task_name']:
     assert ar[f]==br[f]==row[f]
    assert ar['chunks'][0]['control_step']==br['chunks'][0]['control_step']==0
    assert ar['chunks'][0]['observation_sha256']==br['chunks'][0]['observation_sha256']==row['observation_sha256']
    pairs.append(row)
   del rows,results
 assert len(metadata)==5 and len(pairs)==len({(r['suite'],r['training_seed'],r['state_trial_id']) for r in pairs})==500
 config=jr('configs/experiments/formal_main_v2.json','a3f35d8e96d701c1a9ebadc2ad02259372cf6c91da6c9cb8d57c231892cf6ff9')['statistics']
 assert config['bootstrap_repeats']==10000 and config['bootstrap_seed']==20261016 and config['seed_sd_ddof']==1
 gen=np.random.default_rng(20261016);draws=gen.integers(0,10,size=(10000,10,10),dtype=np.int64)
 raw=(json.dumps({'kind':'paired_within_task_initial_state_cluster_draws','seed':20261016,'shape':list(draws.shape),'draws':draws.tolist()},separators=(',',':'))+'\n').encode()
 compressed=gzip.compress(raw,mtime=0)
 with (D/'bootstrap_draws.json.gz').open('xb') as f:f.write(compressed)
 drawref={'path':str((D/'bootstrap_draws.json.gz').relative_to(R)),'sha256':sha(compressed),'uncompressed_sha256':sha(raw),'bytes':len(compressed),'uncompressed_bytes':len(raw)}
 out={}
 for suite,seeds in [('libero_spatial',[17,23,41]),('libero_object',[17,41])]:
  rows=[r for r in pairs if r['suite']==suite];assert len(rows)==len(seeds)*100
  states=sorted({(r['task_id'],r['source_state_index'],r['state_trial_id'],r['initial_state_sha256']) for r in rows})
  assert len(states)==100 and Counter(r[0] for r in states)=={t:10 for t in range(10)}
  arrA=np.empty((10,10,len(seeds)),dtype=np.int64);arrB=np.empty_like(arrA);task_rows=[];seed_rows=[]
  for task in range(10):
   ss=[r for r in states if r[0]==task]
   for si,st in enumerate(ss):
    group=[r for r in rows if r['state_trial_id']==st[2]];assert len(group)==len(seeds)
    assert len({r['observation_sha256'] for r in group})==len({r['initial_state_sha256'] for r in group})==1
    assert {r['training_seed'] for r in group}==set(seeds)
    for zi,seed in enumerate(seeds):
     row=next(r for r in group if r['training_seed']==seed);arrA[task,si,zi]=int(row['A_success']);arrB[task,si,zi]=int(row['B_success'])
  for zi,seed in enumerate(seeds):
   job=metadata[(suite,256,seed)];a=arrA[:,:,zi];b=arrB[:,:,zi];token=job['t0_token_diagnostics']
   assert token['paired_observations']==100 and token['all_t0_observation_hashes_equal'] is True
   assert int(a.sum())==job['A_success'] and int(b.sum())==job['B_success']
   seed_rows.append({'seed':seed,'A_successes':int(a.sum()),'B_successes':int(b.sum()),'trials_per_method':100,'A_percent':float(a.mean()*100),'B_percent':float(b.mean()*100),'B_minus_A_pp':float((b-a).mean()*100),'paired_discordance':{'both_success':int(((a==1)&(b==1)).sum()),'A_only':int(((a==1)&(b==0)).sum()),'B_only':int(((a==0)&(b==1)).sum()),'both_failure':int(((a==0)&(b==0)).sum())},'t0_token_intersection_over_budget':token['mean_intersection_over_budget'],'t0_token_Jaccard':token['mean_Jaccard'],'offline_validation_diagnostics':job['offline_validation_diagnostics'],'source_job_id':job['job_id'],'allocated_GPU_seconds':job['allocated_GPU_seconds']})
   for task in range(10):
    jt=next(t for t in job['per_task'] if t['task_id']==task)
    task_rows.append({'task_id':task,'task_name':next(r['task_name'] for r in rows if r['task_id']==task),'seed':seed,'A_successes':int(a[task].sum()),'B_successes':int(b[task].sum()),'initial_states':10,'A_percent':float(a[task].mean()*100),'B_percent':float(b[task].mean()*100),'B_minus_A_pp':float((b[task]-a[task]).mean()*100),'t0_intersection_over_budget':jt['t0_intersection_over_budget_mean'],'t0_Jaccard':jt['t0_Jaccard_mean']})
  am=arrA.mean((0,1));bm=arrB.mean((0,1));dm=bm-am
  result={'suite':suite,'visual_tokens':256,'available_seeds':seeds,'missing_seeds':sorted({17,23,41}-set(seeds)),'development_only':True,'unique_initial_states':100,'trial_count':200*len(seeds),'per_seed':seed_rows,'per_task':task_rows,'means_percent':{'A':float(am.mean()*100),'B':float(bm.mean()*100),'B_minus_A_pp':float(dm.mean()*100)},'seed_sample_SD_pp':{'A':float(am.std(ddof=1)*100),'B':float(bm.std(ddof=1)*100),'B_minus_A':float(dm.std(ddof=1)*100)},'bootstrap_computed':False,'all_cross_seed_t0_hashes_match':True,'no_equivalence_or_O2A_tradeoff_claim':True,'diagnostic_scope':'Token overlap uses identical pre-action t0 only. Action L1 is offline selected-checkpoint validation, not closed-loop error.','raw_paired_matrix_reconstruction_checked':True}
  if seeds==[17,23,41]:
   matrixref=put('Spatial256_paired_matrix.json',{'schema':'formal_main_v2','suite':suite,'budget':256,'axes':['task','within_task_state','seed'],'seeds':seeds,'state_order':'task_id, source_state_index, state_trial_id, initial_state_sha256','state_coordinates':[{'task_id':st[0],'source_state_index':st[1],'state_trial_id':st[2],'initial_state_sha256':st[3]} for st in states],'A_success':arrA.tolist(),'B_success':arrB.tolist(),'unique_initial_states':100,'method_trials':600,'source_refs':[oldref,newref],'raw_ledger_refs':[metadata[(suite,256,s)]['raw_ledger'] for s in seeds]})
   result['paired_matrix']=matrixref
   sampledA=np.stack([arrA[t][draws[:,t,:]] for t in range(10)],axis=1);sampledB=np.stack([arrB[t][draws[:,t,:]] for t in range(10)],axis=1)
   da=sampledA.mean((1,2,3));db=sampledB.mean((1,2,3));dd=(sampledB-sampledA).mean((1,2,3))
   for i in range(17):
    manual=sum(float(arrB[t,idx,z]-arrA[t,idx,z]) for t in range(10) for idx in draws[i,t] for z in range(3))/300
    assert abs(manual-dd[i])<1e-15
   quant=lambda a:(np.quantile(a,[.025,.975],method='linear')*100).tolist()
   result.update(bootstrap_computed=True,bootstrap_repeats=10000,bootstrap_seed=20261016,bootstrap_interval95_pp={'A':quant(da),'B':quant(db),'B_minus_A':quant(dd)},bootstrap_cluster='Within each task, resample 10 initial-state clusters carrying all 3 seeds and both methods; tasks fixed and equally weighted.',bootstrap_draws=drawref,bootstrap_quantile='numpy.quantile method=linear, 0.025 and 0.975')
   for zi,seed in enumerate(seeds):result['per_seed'][zi]['B_minus_A_bootstrap_CI95_pp']=quant((sampledB[:,:,:,zi]-sampledA[:,:,:,zi]).mean((1,2)))
   result['shared_dense']='Not re-aggregated in this supplemental A/B-only receipt; no Dense margin or final acceptance claimed.'
  else:
   result['limitation']='Object256 seed23 is absent because the unchanged original deployment consumer rejects its receipt history. Available seeds17/41 are descriptive only; no fabricated third seed or complete-matrix CI.'
  out[suite]=result
 pairedref=put('combined_paired_development_states.json',{'schema':'formal_main_v2','scope':'Spatial256 seeds17/23/41; Object256 seeds17/41. 500 paired records, 200 unique initial states; no final trial results.','states':pairs})
 statsref=put('development_statistics.json',{'schema':'formal_main_v2','kind':'independent_256_budget_development_statistics','status':'passed_Spatial_three_seeds_Object_explicit_missing23','configuration':config,'suites':out,'all_seeds_and_negative_results_preserved':True,'final_release':False,'sealed_final_values_read':False,'latency_executed':False,'new_GPU_jobs':0,'new_GPU_seconds':0,'all_source_refs':[oldref,newref],'raw_ledger_refs':rawrefs,'original_root_refs':rootrefs,'bootstrap_draws':drawref,'paired_states':pairedref,'statistics_source':ref('.local/devterminal_independent_20261020T1530/statistics_256_a1.py'),'all_inputs':inputs})
 compact=put('compact_summary.json',{'schema':'formal_main_v2','accepted_jobs':{jid:{'suite':j['suite'],'seed':j['training_seed'],'budget':j['A_B_visual_tokens'],'A_success':j['A_success'],'B_success':j['B_success'],'B_minus_A_pp':j['B_minus_A_pp'],'trials':j['trials'],'GPU_seconds':j['allocated_GPU_seconds'],'t0_token_overlap':j['t0_token_diagnostics']['mean_intersection_over_budget'],'t0_Jaccard':j['t0_token_diagnostics']['mean_Jaccard']} for jid,j in new['jobs'].items()},'new_accepted_trials':600,'new_accepted_jobs_GPU_seconds':6678,'GPU_cost_already_in_global_ledger_do_not_add':True,'all_5_jobs_descriptive_GPU_seconds':sum(j['allocated_GPU_seconds'] for j in metadata.values()),'statistics':statsref,'Spatial_paired_matrix':out['libero_spatial']['paired_matrix'],'bootstrap_draws':drawref,'means_percent':{k:v['means_percent'] for k,v in out.items()},'Spatial_CI95_pp':out['libero_spatial']['bootstrap_interval95_pp'],'Object_missing_seed':23,'existing_Goal256_hold_unchanged':True,'existing_Object256seed23_consumer_block_unchanged':True,'sealed_final_unchanged':True})
 for rel,e in list(inputs.items()):assert sha((R/rel).read_bytes())==e['sha256'],rel
 files=[]
 for p in sorted(D.iterdir()):
  if p.is_file() and p.name!='manifest.json':files.append({'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size})
 mr=put('manifest.json',{'schema':'formal_main_v2','kind':'independent_terminal_and_256_statistics_delivery','status':'passed_3terminals_Spatial3seeds_Object2seeds','files':files,'terminal_review':newref,'statistics':statsref,'paired_states':pairedref,'compact_summary':compact,'CPU_wall_seconds':time.monotonic()-started})
 print(json.dumps({'manifest':mr,'statistics':statsref,'means':{k:v['means_percent'] for k,v in out.items()},'Spatial_CI':out['libero_spatial']['bootstrap_interval95_pp'],'seed_SD_pp':{k:v['seed_sample_SD_pp'] for k,v in out.items()}}))
except Exception as exc:
 fr=put('statistics_failure_a1.json',{'status':'failed','exception_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'inputs':inputs});print(json.dumps({'failure':fr}));raise

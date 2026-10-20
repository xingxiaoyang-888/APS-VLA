"""Fixed-protocol development statistics and bounded diagnosis; never changes execution."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter,defaultdict
import json,hashlib,gzip,sys,types,time,traceback
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/devterminal_independent_20261020T1418';B='results/formal_main_v2/preflight/heartbeat_20261020T2218'
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
 newref={'path':'.local/devterminal_independent_20261020T1418/independent_review.json','sha256':'ad8c588b38df5d774f7da678ff75b2931743156de8b1e4d373f1f5358c22fead'}
 goalref={'path':'results/formal_main_v2/downstream_reviews/Goal_seed17_23_1317_independent.json','sha256':'7cda4fb3d421242efcc9255c732a08952d4e0288d3866f0088220cd6c3e3cea9'}
 nonref={'path':'results/formal_main_v2/downstream_reviews/nonLong_seed23_1220_independent.json','sha256':'67c2e32b61a1aa2ec02202d03ff2e28112e971f3968c2f8a88e3ad5100e1f120'}
 new=jr(**{ 'rel':newref['path'],'pin':newref['sha256']});goal=jr(goalref['path'],goalref['sha256']);non=jr(nonref['path'],nonref['sha256'])
 assert all(x['status']=='passed' and x['review_role']=='independent' for x in [new,goal,non])
 pairs=[];metadata={};rawrefs=[]
 for report in [goal,non,new]:
  pr=report['paired_states'];data=jr(pr['path'],pr['sha256'])
  for row in data['states']:
   row=dict(row);row.setdefault('visual_tokens',128);pairs.append(row)
  for job in report['jobs'].values():
   suite=job['suite'] if 'suite' in job else next(x['suite'] for x in job['methods'].values())
   seed=job['training_seed'];budget=job.get('A_B_visual_tokens',job.get('visual_tokens',128));key=(suite,budget,seed)
   assert key not in metadata;metadata[key]=job
   ledger=job['raw_ledger'];rows=[json.loads(x) for x in read(ledger['path'],ledger['sha256']).splitlines()];results=[x for x in rows if x['event']=='result']
   rawrefs.append(ledger)
   for row in data['states']:
    if row['suite']!=suite or row['training_seed']!=seed or row.get('visual_tokens',128)!=budget:continue
    ar=next(x for x in results if x['state_trial_id']==row['state_trial_id'] and x['method']==f'A{budget}_seed{seed}')
    br=next(x for x in results if x['state_trial_id']==row['state_trial_id'] and x['method']==f'B{budget}_seed{seed}')
    assert (ar['success'],br['success'])==(row['A_success'],row['B_success'])
    assert ar['chunks'][0]['observation_sha256']==br['chunks'][0]['observation_sha256']
    target=next(p for p in pairs if (p['suite'],p['visual_tokens'],p['training_seed'],p['state_trial_id'])==(suite,budget,seed,row['state_trial_id']))
    target['observation_sha256']=ar['chunks'][0]['observation_sha256']
   del rows,results
 ids=[(r['suite'],r['visual_tokens'],r['training_seed'],r['state_trial_id']) for r in pairs];assert len(ids)==len(set(ids))==900
 config=jr('configs/experiments/formal_main_v2.json','a3f35d8e96d701c1a9ebadc2ad02259372cf6c91da6c9cb8d57c231892cf6ff9')['statistics']
 assert config['bootstrap_repeats']==10000 and config['bootstrap_seed']==20261016 and config['seed_sd_ddof']==1
 gen=np.random.default_rng(config['bootstrap_seed']);draws=gen.integers(0,10,size=(10000,10,10),dtype=np.int64)
 raw=(json.dumps({'kind':'paired_within_task_initial_state_cluster_draws','seed':20261016,'shape':list(draws.shape),'draws':draws.tolist()},separators=(',',':'))+'\n').encode()
 compressed=gzip.compress(raw,mtime=0)
 with (D/'bootstrap_draws.json.gz').open('xb') as f:f.write(compressed)
 drawref={'path':(D/'bootstrap_draws.json.gz').relative_to(R).as_posix(),'sha256':sha(compressed),'uncompressed_sha256':sha(raw),'bytes':len(compressed),'uncompressed_bytes':len(raw)}
 out={}
 for suite,seeds in [('libero_goal',[17,23,41]),('libero_spatial',[23,41]),('libero_object',[23,41])]:
  rows=[r for r in pairs if r['suite']==suite and r['visual_tokens']==128];assert len(rows)==100*len(seeds)
  states=sorted({(r['task_id'],r['source_state_index'],r['state_trial_id'],r['initial_state_sha256']) for r in rows})
  assert len(states)==100 and Counter(r[0] for r in states)=={t:10 for t in range(10)}
  arrA=np.empty((10,10,len(seeds)));arrB=np.empty_like(arrA);task_rows=[];seed_rows=[]
  for task in range(10):
   ss=[r for r in states if r[0]==task]
   for si,st in enumerate(ss):
    group=[r for r in rows if r['state_trial_id']==st[2]];assert len(group)==len(seeds)
    assert len({r['observation_sha256'] for r in group})==1 and len({r['initial_state_sha256'] for r in group})==1
    for zi,seed in enumerate(seeds):
     row=next(r for r in group if r['training_seed']==seed);arrA[task,si,zi]=int(row['A_success']);arrB[task,si,zi]=int(row['B_success'])
  for zi,seed in enumerate(seeds):
   job=metadata[(suite,128,seed)];a=arrA[:,:,zi];b=arrB[:,:,zi]
   token=job['t0_token_diagnostics'];assert token['all_t0_observation_hashes_equal'] is True
   seed_rows.append({'seed':seed,'A_successes':int(a.sum()),'B_successes':int(b.sum()),'trials_per_method':100,'A_percent':float(a.mean()*100),'B_percent':float(b.mean()*100),'B_minus_A_pp':float((b-a).mean()*100),'paired_discordance':{'both_success':int(((a==1)&(b==1)).sum()),'A_only':int(((a==1)&(b==0)).sum()),'B_only':int(((a==0)&(b==1)).sum()),'both_failure':int(((a==0)&(b==0)).sum())},'token_intersection_over_128':token.get('mean_intersection_over_128',token.get('mean_intersection_over_budget')),'token_Jaccard':token['mean_Jaccard'],'offline_validation_diagnostics':job['offline_validation_diagnostics'],'source_job_id':job['job_id']})
   for task in range(10):
    task_rows.append({'task_id':task,'task_name':next(r['task_name'] for r in rows if r['task_id']==task),'seed':seed,'A_successes':int(a[task].sum()),'B_successes':int(b[task].sum()),'initial_states':10,'A_percent':float(a[task].mean()*100),'B_percent':float(b[task].mean()*100),'B_minus_A_pp':float((b[task]-a[task]).mean()*100)})
  am=arrA.mean((0,1));bm=arrB.mean((0,1));dm=bm-am
  result={'suite':suite,'visual_tokens':128,'available_seeds':seeds,'missing_seeds':sorted({17,23,41}-set(seeds)),'development_only':True,'unique_initial_states':100,'trial_count':200*len(seeds),'per_seed':seed_rows,'per_task':task_rows,'means_percent':{'A':float(am.mean()*100),'B':float(bm.mean()*100),'B_minus_A_pp':float(dm.mean()*100)},'seed_sample_SD_pp':{'A':float(am.std(ddof=1)*100),'B':float(bm.std(ddof=1)*100),'B_minus_A':float(dm.std(ddof=1)*100)},'bootstrap_computed':False,'all_cross_seed_t0_hashes_match':True,'no_equivalence_or_O2A_tradeoff_claim':True}
  if seeds==[17,23,41]:
   sampledA=np.stack([arrA[t][draws[:,t,:]] for t in range(10)],axis=1);sampledB=np.stack([arrB[t][draws[:,t,:]] for t in range(10)],axis=1)
   da=sampledA.mean((1,2,3));db=sampledB.mean((1,2,3));dd=(sampledB-sampledA).mean((1,2,3))
   for i in range(17):
    manual=sum(float((arrB[t,idx,z]-arrA[t,idx,z])) for t in range(10) for idx in draws[i,t] for z in range(3))/300
    assert abs(manual-dd[i])<1e-15
   quant=lambda a:(np.quantile(a,[.025,.975])*100).tolist()
   result.update(bootstrap_computed=True,bootstrap_repeats=10000,bootstrap_seed=20261016,bootstrap_interval95_pp={'A':quant(da),'B':quant(db),'B_minus_A':quant(dd)},bootstrap_cluster='Within each task, resample10initial-state clusters carrying all3seeds and both methods; tasks fixed and equally weighted.',bootstrap_draws=drawref)
   for zi,seed in enumerate(seeds):result['per_seed'][zi]['B_minus_A_bootstrap_CI95_pp']=quant((sampledB[:,:,:,zi]-sampledA[:,:,:,zi]).mean((1,2)))
   # Shared Dense reference stays one100-trial reference, not multiplied by seeds.
   g=goal['jobs']['3048609'];ledger=g['raw_ledger'];rr=[json.loads(x) for x in read(ledger['path'],ledger['sha256']).splitlines()];dense=[r for r in rr if r['event']=='result' and r['method']=='dense'];assert len(dense)==100
   de=np.array([[int(next(r for r in dense if r['state_trial_id']==st[2])['success']) for st in states if st[0]==t] for t in range(10)],dtype=float)
   ds=np.stack([de[t][draws[:,t,:]] for t in range(10)],axis=1).mean((1,2))
   result['shared_dense']={'successes':int(de.sum()),'trials':100,'A_minus_dense_pp':float((am.mean()-de.mean())*100),'B_minus_dense_pp':float((bm.mean()-de.mean())*100),'A_minus_dense_CI95_pp':quant(da-ds),'B_minus_dense_CI95_pp':quant(db-ds),'practical_margin_pp':-2,'rule':'CI lower bound strictly greater than -2pp; development diagnostic only, not final acceptance','A_meets_development_margin':bool(np.quantile(da-ds,.025)>-.02),'B_meets_development_margin':bool(np.quantile(db-ds,.025)>-.02)}
  else:result['limitation']='seed17 historical action semantics not admitted; report available2seeds descriptively only. No fabricated3seed mean/CI, no equivalence claim.'
  out[suite]=result
 statsref=put('development_statistics.json',{'schema':'formal_main_v2','kind':'independent_nonLong_primary_budget_development_statistics','status':'passed_with_explicit_missing_seed17_scope','configuration':config,'suites':out,'all_seeds_and_negative_results_preserved':True,'final_release':False,'sealed_final_values_read':False,'latency_executed':False,'new_GPU_jobs':0,'new_GPU_seconds':0,'all_source_refs':[newref,goalref,nonref],'raw_ledger_refs':rawrefs,'bootstrap_draws':drawref,'all_inputs':inputs,'statistics_source':ref('.local/devterminal_independent_20261020T1418/statistics_and_diagnosis_a1.py')})
 pairedref=put('combined_paired_development_states.json',{'schema':'formal_main_v2','scope':'Goal1283seeds; Spatial/Object1282seeds; Spatial/Object256seed17 only. 900paired records,300unique initialstates.','states':pairs})
 # Independently reproduce the original rejection, without rewriting its guard or accepting failed results.
 snapref={'path':B+'/terminal_jobs_snapshot.json','sha256':'4417ed6bc2d89611d6507d1ad2cabc544c89faa8b1eb0340cca563706322ba1a'}
 snap=jr(snapref['path'],snapref['sha256']);jobs=snap['registered_jobs'];job=next(j for j in jobs if str(j['job_id'])=='3049679');assert job['elapsed_seconds']==2034 and job['status']=='COMPLETED'
 rv=mod('scripts/ops/formal_action_deployment_v1/reviewer.py','9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','independent_failure1418')
 invref={'path':job['invocation'],'sha256':job['invocation_sha256']};inv=jr(invref['path'],invref['sha256']);pullref={'path':'results/formal_main_v2/pulls/20261020T142621Z_02800e667ffb/receipt.json','sha256':'20139adbe331ea4d217e7011f22b4e3d6e008f6c59e87ff1d00a0735ef290493'}
 caught=None
 try:rv.review(R,job=job,invocation_ref=invref,pull_ref=pullref,registered_jobs=jobs,expected_contract_ref=inv['action_execution_contract'])
 except Exception as exc:caught={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
 assert caught and 'Paired initial observation differs across methods/attempts' in caught['message']
 base=Path(job['run_root']).relative_to(P).as_posix();ledger=base+'/trials.jsonl';rr=[json.loads(x) for x in read(ledger).splitlines()];rs=[x for x in rr if x['event']=='result'];assert len(rs)==200
 grouped=defaultdict(dict)
 for row in rs:grouped[row['state_trial_id']][row['method']]=row
 mismatches=[]
 for sid,mm in grouped.items():
  a=mm['A256_seed17'];b=mm['B256_seed17'];ah=a['chunks'][0]['observation_sha256'];bh=b['chunks'][0]['observation_sha256']
  assert a['initial_state_sha256']==b['initial_state_sha256'] and a['environment_seed']==b['environment_seed']==0 and a['runtime_seed']==b['runtime_seed']==17 and a['wait_steps']==b['wait_steps']==10
  if ah!=bh:mismatches.append({'state_trial_id':sid,'task_id':a['task_id'],'task_name':a['task_name'],'source_state_index':a['source_state_index'],'initial_state_sha256':a['initial_state_sha256'],'A_t0_observation_sha256':ah,'B_t0_observation_sha256':bh,'initial_state_identity_equal':True,'environment_seed':0,'runtime_seed':17,'wait_steps':10,'success_outcomes_not_used_for_acceptance':True})
 assert len(grouped)==100 and len(mismatches)==1 and mismatches[0]['task_id']==2 and mismatches[0]['source_state_index']==42
 bad=mismatches[0];gs=[r for r in pairs if r['suite']=='libero_goal' and r['state_trial_id']==bad['state_trial_id'] and r['visual_tokens']==128]
 assert len(gs)==3 and {r['observation_sha256'] for r in gs}=={bad['B_t0_observation_sha256']}
 rootfail=jr(B+'/3049679_root_review_failure_20261020T1418.json','49b226c91f99cd9fd3584ab645992244794f4d720e0128d9ab693e82bcca6793')
 runtime=read('src/cti_vla/evaluation/libero_runtime.py');assert b'chunk = predict_chunk(observation, instruction)' in runtime and b'_observation_hash(observation)' in runtime
 diagref=put('Goal256_seed17_failure_diagnosis.json',{'schema':'formal_main_v2','kind':'independent_bounded_Goal256_t0_mismatch_diagnosis','status':'confirmed_blocker_no_scientific_acceptance','job_id':'3049679','original_guard_reproduced':caught,'root_failure_ref':ref(B+'/3049679_root_review_failure_20261020T1418.json'),'raw_ledger':ref(ledger),'retained_trials':200,'accepted_trials':0,'all_pair_states':100,'mismatching_states':mismatches,'matching_states':99,'actual_GPU_seconds':2034,'GPU_cost_scope':'Already allocated actual job included in global bill; no additionalGPU by audit. Do not discard failedcost or add twice.','Goal128_three_seed_t0_compatible':True,'observation_hash_fields':['agentview_image','robot0_eye_in_hand_image','robot0_eef_pos','robot0_eef_quat','robot0_gripper_qpos'],'existing_raw_arrays_available':False,'cause_status':'Undetermined: whole-observation hash alone cannot distinguish camera/render differences, proprio/state divergence or input mutation. Original code hashes observation after predict_chunk returns.','next_bounded_engineering_proposal':{'status':'proposed_not_run_not_scientific_trial','only_development_state':{k:bad[k] for k in ['state_trial_id','task_id','task_name','source_state_index','initial_state_sha256']},'root_preregistration_required':True,'maximum_GPU_jobs':1,'maximum_GPU_wall_minutes':30,'maximum_resets':12,'matrix':'3fixed repetitions of A->B and B->A reset/query order (12reset t0 queries total), same selected256seed17 checkpoints and pinned environment. No policy action executes beyond the10unchangedwait actions.','record':['Five raw observation arrays and each shape/dtype/SHA plus aggregate at reset, after each of10wait steps, immediately before predict and immediately after predict','Exact init checksum and full development init vector; task/BDDL/camera/simulator/controller/library/GPU/node identities','Python/NumPy/TorchCPU/CUDA RNG states at reset/preload/postload/prequery/postquery; environment seed and runtime seed','Model load/reset/query order and timing; actual retainedindices/checkpoint SHA; pre/post array equality and maximum absolute differences','State qpos/qvel and available simulator state snapshots before/after waiting to separate physics from rendering'], 'stop_rule':'Any mismatch or evidence gap remainsHOLD. Do not relax hash equality, alter losses/tasks/initialstates, selectsuccessfuloutcomes, or replace original200. Reproduction or diagnosis alone does notauthorize science retry; root boundedrepair+independent acceptance mustfollow.'},'no_existing_checkpoints_or_source_changed':True,'no_state_Git_Slurm_mutations':True,'new_GPU_jobs':0,'new_GPU_seconds':0,'sealed_final_values_read':False,'all_inputs':inputs})
 files=[]
 for p in sorted(D.iterdir()):
  if p.is_file() and p.name!='manifest.json':files.append({'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size})
 mr=put('manifest.json',{'schema':'formal_main_v2','kind':'independent_terminal_statistics_and_diagnostic_delivery','status':'passed_5terminals_with_1explicit_blocker','files':files,'terminal_review':newref,'statistics':statsref,'paired_states':pairedref,'diagnosis':diagref,'CPU_wall_seconds':time.monotonic()-started})
 print(json.dumps({'manifest':mr,'statistics':statsref,'diagnosis':diagref,'means':{k:v['means_percent'] for k,v in out.items()},'Goal_CI':out['libero_goal']['bootstrap_interval95_pp'],'held_job':'3049679'}))
except Exception as exc:
 fr=put('statistics_diagnosis_failure_a1.json',{'status':'failed','exception_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'inputs':inputs});print(json.dumps({'failure':fr}));raise

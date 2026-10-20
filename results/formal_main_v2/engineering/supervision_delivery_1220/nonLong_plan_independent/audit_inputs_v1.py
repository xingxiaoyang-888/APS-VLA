from pathlib import Path
import json,hashlib,math,time
from collections import Counter,defaultdict
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=R/'.local/nonLong_development_plans_independent_1220'
READS={};CHECKS=[]
t0=time.perf_counter();cpu=time.process_time()
def read(rel,pin=None):
 p=Path(rel);p=p if p.is_absolute() else R/p
 assert R in p.parents and not any(x in p.parts for x in ('checkpoints','weights')) and p.suffix not in ('.pt','.bin','.init','.pkl')
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest();assert pin is None or h==pin,(str(p),h)
 READS[p.relative_to(R).as_posix()]=dict(path=p.relative_to(R).as_posix(),sha256=h,bytes=len(b));return json.loads(b)
def check(value,name):
 assert value,name;CHECKS.append(name)
def close(a,b):return math.isclose(a,b,rel_tol=0,abs_tol=1e-12)
def ref(rel):return READS[rel]
statepath='results/formal_main_v2/preflight/heartbeat_20261020T2020/state_before.json'
s=read(statepath,'a32924884da6a900f98aea682642c70047c2b48df51d4d5524a7b4318f5e89b8')
reg=read('configs/experiments/formal_main_v2.json','a3f35d8e96d701c1a9ebadc2ad02259372cf6c91da6c9cb8d57c231892cf6ff9')
rows=[]
for suite,seed,nwin,steps in [('libero_spatial',41,189,220),('libero_object',41,204,280),('libero_goal',23,186,300)]:
 key=f'{suite}_k128_seed{seed}';pair=s['formal_main_progress']['completed_training_pairs'][key];sp=reg['suites'][suite]
 check(pair['suite']==suite and pair['seed']==seed and pair['visual_tokens']==128 and pair['trained_arms']==2 and pair['allowed_next_segment_end'] is None,key+'_completed_registered')
 evidence={}
 for role in ('root_review','independent_review','selected_server_review'):
  rr=read(pair[role],pair[role+'_sha256']);evidence[role]=ref(pair[role]);check(str(rr['status']).startswith(('passed','root_and_independent')),key+'_'+role)
  if role=='root_review':check(rr['completed_by_arm']=={'A':5000,'B':5000},key+'_root5000')
 methods=[f'A128_seed{seed}',f'B128_seed{seed}'];development_jobs=[j for j in s['registered_jobs'] if j.get('suite')==suite and j.get('mode')=='development']
 check(all(not(set(j.get('method_ids',[]))&set(methods)) for j in development_jobs),key+'_no_registered_active_or_finished_duplicate')
 env=sp['environment'];check(env==dict(max_control_steps=steps,action_chunk=8,wait_steps=10,env_seed=0,runtime_seed=17),key+'_official_environment')
 wp=sp['windows'];w=read(wp);allowed=w['validation_window_ids'];check(len(allowed)==len(set(allowed))==nwin and not set(allowed)&set(w['train_window_ids']),key+'_fixed_disjoint_validation')
 dp=sp['initial_states_root']+'/development.json';panel=read(dp);states=panel['states'];check(panel['suite']==suite and panel['split']=='development' and len(states)==100 and len({x['trial_id'] for x in states})==100 and Counter(x['task_id'] for x in states)==Counter({i:10 for i in range(10)}),key+'_100_unique_development')
 selected=[]
 for arm in 'AB':
  path=f'results/formal_main_v2/{suite}/k128/seed{seed}/training/{arm}/deployment_receipt.json';d=read(path);m=d['metadata'];ev=d['evaluations']
  check(d['completed_updates']==d['planned_updates']==5000 and d['training_complete'] and d['base_frozen'] and d['checkpoint_unchanged'] and [x['update'] for x in ev]==list(range(0,5001,500)),key+'_'+arm+'_5000_11nodes')
  check(m['suite']==suite and m['seed']==seed and m['arm']==arm and m['visual_tokens']==128 and m['per_camera_budgets']==[64,64] and m['model_revision']==sp['model_revision'] and m['selection_metric']=='task_macro_hard_validation_teacher_l1' and m['training_complete'],key+'_'+arm+'_metadata')
  validation=[]
  for e in ev:
   ap=Path(e['artifact_path']);check(P in ap.parents,key+'_'+arm+'_server_validation_path')
   rel=ap.relative_to(P).as_posix();v=read(rel,e['artifact_sha256']);obs=v['observations'];ids=[x['window_id'] for x in obs]
   check(len(obs)==nwin and len(set(ids))==nwin and set(ids)==set(allowed) and v['arm']==arm and v['update']==e['update'] and v['windows']==nwin and v['tasks']==10,key+'_'+arm+f'_validation_{e["update"]}_panel')
   by=defaultdict(list)
   for x in obs:
    by[x['task_id']].append(x['teacher_l1']);idx=x['retained_indices'];act=x['normalized_actions']
    assert math.isfinite(x['teacher_l1']) and len(idx)==128 and idx==sorted(set(idx)) and sum(i<256 for i in idx)==64 and all(0<=i<512 for i in idx)
    assert len(act)==8 and all(len(a)==7 and all(math.isfinite(z) for z in a) for a in act)
   assert set(by)==set(range(10))
   means={str(t):sum(vals)/len(vals) for t,vals in by.items()};macro=sum(means.values())/10
   check(all(close(v['per_task'][t]['teacher_l1'],val) and v['per_task'][t]['windows']==len(by[int(t)]) for t,val in means.items()) and close(macro,e['validation_metric']) and close(macro,v['validation_metric']) and v['metric']==m['selection_metric'],key+'_'+arm+f'_validation_{e["update"]}_macro')
   validation.append(dict(update=e['update'],task_macro_teacher_l1=macro,artifact=ref(rel)))
  best=min(ev,key=lambda x:(x['validation_metric'],x['update']));sel=next(x for x in pair['selected_checkpoints'] if x['arm']==arm)
  check(m['update']==best['update']==sel['selected_update'] and m['validation_metric']==best['validation_metric']==sel['validation_metric'] and d['checkpoint_sha256']==sel['expected_sha256'],key+'_'+arm+'_earliest_minimum_checkpoint')
  selected.append(dict(method_id=arm+'128_seed'+str(seed),deployment_receipt=ref(path),checkpoint=sel['path'],checkpoint_sha256=d['checkpoint_sha256'],selected_update=m['update'],validation_metric=m['validation_metric'],training_seed=seed,runtime_seed=17,env_seed=0,validation=validation))
 rows.append(dict(suite=suite,training_seed=seed,method_ids=methods,planned_trials=200,unique_development_states=100,environment=env,development_panel=ref(dp),windows=ref(wp),training_reviews=evidence,selected=selected,existing_other_development_jobs=[{k:j.get(k) for k in ('job_id','status','method_ids')} for j in development_jobs]))
for rel,rr in READS.items():assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==rr['sha256']
out=dict(schema='formal_main_v2',kind='independent_next_development_training_panel_precheck',status='passed_inputs_only',reviewer='/root/goal256_s41_terminal_0333',state_snapshot=ref(statepath),registration=ref('configs/experiments/formal_main_v2.json'),plans=rows,total_planned_trials=600,checks=len(CHECKS),check_names=CHECKS,read_evidence=list(READS.values()),no_active_or_finished_target_duplicates_in_snapshot=True,current_queue_submission_authority=False,new_development_completed_trials=0,new_GPU_seconds=0,weights_or_final_values_read=False,optimizer_RNG_audit_repeated=False,CPU_wall_seconds=time.perf_counter()-t0,CPU_process_seconds=time.process_time()-cpu,production_state_Git_Slurm_modified=False,final_release=False)
p=D/'input_training_precheck.json'
with p.open('x') as f:json.dump(out,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(report=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size,checks=len(CHECKS),CPU_wall_seconds=out['CPU_wall_seconds'])))

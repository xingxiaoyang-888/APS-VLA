from pathlib import Path
import hashlib,json,sys,importlib.util
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B=R/'results/formal_main_v2/preflight/heartbeat_20261020T0122'
H=Path('/share/home/u15016/XXY_CVPR/CTI-VLA')
def h(p):
 d=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(8<<20),b''):d.update(block)
 return d.hexdigest()
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('longroot1722ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';statehash=h(statepath);s=json.loads(statepath.read_text())
 pairs=s['formal_main_progress']['completed_training_pairs']
 selected={}
 for k,v in pairs.items():
  if not k.startswith('libero_10_'):continue
  assert v['allowed_next_segment_end'] is None
  for role in ['root_review','independent_review']:
   assert h(R/v[role])==v[role+'_sha256']
  budget=int(k.split('_k')[1].split('_')[0]);seed=int(k.split('_seed')[1])
  assert budget in [256,128,64] and seed in [17,23,41]
  for x in v['selected_checkpoints']:
   mid=x['arm']+str(budget)+'_seed'+str(seed);assert mid not in selected
   p=Path(x['path']);assert p==H/'checkpoints/formal_main_v2/libero_10'/('k'+str(budget))/('seed'+str(seed))/x['arm']/'best.pt'
   assert p.is_file() and not p.is_symlink() and h(p)==x['expected_sha256']
   selected[mid]=dict(arm=x['arm'],visual_tokens=budget,seed=seed,selected_update=x['selected_update'],checkpoint_path=str(p),checkpoint_sha256=x['expected_sha256'],bytes=p.stat().st_size,root_review=dict(path=v['root_review'],sha256=v['root_review_sha256']),independent_review=dict(path=v['independent_review'],sha256=v['independent_review_sha256']),original_job_id=v['job_id'],checkpoint_reselected=False)
 assert len(selected)==18
 expected={a+str(b)+'_seed'+str(t) for b in [256,128,64] for t in [17,23,41] for a in ['A','B']}
 assert set(selected)==expected
 prior=s['registered_jobs'];old=[j for j in prior if j.get('experiment')=='formal_main_v2' and j.get('suite')=='libero_10' and j.get('mode')=='development']
 assert len(old)==6 and all(j['status']=='COMPLETED' for j in old)
 old_methods={m for j in old for m in j['method_ids']}
 assert old_methods=={'dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17'}
 targets=expected-old_methods;assert len(targets)==16
 plans=[]
 for b in [128,256,64]:
  for seed in [17,23,41]:
   if b==128 and seed==17:continue
   methods=[a+str(b)+'_seed'+str(seed) for a in ['A','B']]
   assert set(methods)<=targets
   plans.append(dict(visual_tokens=b,seed=seed,method_ids=methods,development_trials=200,unique_development_initials=100))
 assert len(plans)==8
 seconds=sum(j['elapsed_seconds']*j['gpus'] for j in old);assert seconds==10531
 assert h(statepath)==statehash
 result=dict(schema='formal_main_v2',kind='root_Long_selected_identity_and_fresh_development_scope',utc=datetime.now(timezone.utc).isoformat(),status='identity_verified_preparation_only',state_at_review_sha256=statehash,all18_selected=selected,fresh_target_method_ids=sorted(targets),engineering_shards=plans,planned_fresh_development_trials=1600,unique_initials_per_method=100,original_development_job_ids=[j['job_id'] for j in old],original_development_GPU_seconds=seconds,original_methods=sorted(old_methods),original_records_retained=True,all_selected_checkpoint_bytes_checked_on_server=True,checkpoint_tensor_loaded=False,model_weights_copied=False,scientific_settings_changed=False,method_selection_by_overlap_only_not_outcomes=True,new_execution_requires_existing_passed_action_runtime=True,old_six_action_identity_migration_pending=True,submission_authorized=False,final_release=False)
 p=B/'Long_selected_identity_root_check.json'
 with p.open('x') as f:json.dump(result,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(dict(path=p.relative_to(R).as_posix(),sha256=h(p),selected_checkpoint_identities=18,fresh_methods=16,shards=8,new_GPU_submissions=0)))

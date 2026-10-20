from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261021T0349';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1949'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return dict(path=n,sha256=h(R/n))
def save(n,v):
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def cp(n,d):
 p=R/n;q=R/d;assert p.is_file() and p.resolve()==p and not p.is_symlink();raw=p.read_bytes();q.parent.mkdir(parents=True,exist_ok=True)
 if q.exists():assert q.read_bytes()==raw
 else:q.open('xb').write(raw)
def package(n,pin,destination):
 assert h(R/n)==pin;m=rd(n);base=m['source_root'];assert base.startswith('.local/') and len(m['files'])==m['file_count'];names=set()
 for row in m['files']:
  rel=row['path'];assert not Path(rel).is_absolute() and '..' not in Path(rel).parts and rel not in names;names.add(rel)
  src=base+'/'+rel;assert row['source']==src and h(R/src)==row['sha256'] and (R/src).stat().st_size==row['bytes'];cp(src,destination+'/'+rel)
 cp(n,destination+'/delivery_manifest_original.json');return dict(original=ref(n),copy=ref(destination+'/delivery_manifest_original.json'),files=len(names))
ap=argparse.ArgumentParser();ap.add_argument('--independent-manifest',required=True);ap.add_argument('--independent-manifest-sha256',required=True);a=ap.parse_args()
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';sp=importlib.util.spec_from_file_location('collect1949_controller',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=h(state);s=rd('results/experiment_supervisor/state.json');baseline=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert f['root_and_independent_completed_arms']==72 and f['root_and_independent_reviewed_arm_updates']==360000 and f['current_action_development_trial_count']==5400 and f['completed_development_trials']==6612 and f['completed_final_trials']==0 and f['test_opened'] is False and f['global_release_created'] is False
 assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['blocked_pairs']=={} and ctl['last_result']['status']=='training_matrix_complete'
 completion=B+'/collect_terminal/completion.json';assert h(R/completion)=='fd468a87dc1c7c90090d8cc3264e3b42110c39c154c5d19dfb5975be4fa8cbf5';done=rd(completion);assert done['status']=='passed_original_review_and_consumer' and done['job_ids']==['3053503','3053518'] and done['state_unchanged'] is True and done['cost_increment_gpu_seconds']==0
 author=package('.local/collect_terminal_20261020T1949/collect_delivery_manifest.json','897889f47bc402209b73bda69b09401f4174210cf8dedeb0ec929ae16df8e91a',E+'/Collect_author')
 independent=package(a.independent_manifest,a.independent_manifest_sha256,E+'/Collect_independent')
 index=E+'/Collect_independent/terminal_independent_index.json';assert h(R/index)=='aa8f153c1662e49339a2c1f495a6ff898aa5d36e4052d9c5146bf093ea6746a2';d=rd(index);assert d['status']=='passed' and d['checks_passed']==1454 and d['scientific_success_trials_added']==d['latency_samples_added']==0 and d['gpu_seconds']==723 and d['original_reviewer_and_consumer_both_executed'] is True
 accepted={}
 for name,jid,pin in [('Spatial','3053503','9c3d20ce606a9b40a0e1217cb3a38488ee1a925ba7499a899251b8748ccc52a1'),('Object','3053518','509467ea2c3a8f0ae82468bf89808c55f08a6faa68b87ae7fae40d045a1af909')]:
  path=E+'/Collect_independent/'+jid+'_independent_review.json';assert h(R/path)==pin;v=rd(path);j=next(x for x in s['registered_jobs'] if x['job_id']==jid);previous=f['fixed_observation_collections_20261020T1825'][name];assert previous['accepted_observations']==0
  assert v['status']=='passed' and v['stage']=='collect' and v['job_id']==jid and v['suite']==j['suite'] and v['observations']==30 and v['collection_trajectories']==10 and v['new_success_trials']==v['latency_samples_added']==0 and v['final_release'] is False
  assert v['root_review']==ref('results/formal_main_v2/downstream_reviews/'+jid+'.json') and v['invocation']=={'path':j['invocation'],'sha256':j['invocation_sha256']} and v['cost']['current_gpu_seconds']==v['cost']['all_attempt_gpu_seconds']==j['elapsed_seconds']
  assert j['status']=='COMPLETED' and j['exit_code']=='0:0' and j['gpus']==1 and v['panel']==ref(v['panel']['path']);assert h(P/v['panel']['path'])==v['panel']['sha256']
  dst='results/formal_main_v2/downstream_reviews/'+jid+'_independent.json';cp(path,dst)
  accepted[name]={**previous,'status':'completed_root_and_independent_accepted','accepted_observations':30,'completed_collection_trajectories':10,'root_terminal_review':v['root_review'],'independent_terminal_review':ref(dst),'independent_package':ref(index),'observation_panel':v['panel'],'source_state_indices':[x['source_state_index'] for x in v['tasks']],'actual_control_steps':v['collection_control_steps'],'actual_policy_calls':v['collection_policy_calls'],'all_attempt_GPU_seconds':v['cost']['all_attempt_gpu_seconds'],'additional_GPU_seconds_this_supervision':0,'raw_observation_bytes':30*394644,'full_latency_executed':False,'components_executed':False,'collection_cost_is_not_O2A_latency':True,'exact_NPZ_delivery_allowlist':done['npz_allowlist'],'previous_submission_stage_record':copy.deepcopy(previous)}
 assert s['current_round_cost']['allocated_gpu_seconds']==1980004
 record={'schema':'formal_main_v2','kind':'root_fixed_collection_acceptance','status':'Spatial_Object_fixed30_each_root_and_independent_accepted','utc':datetime.now(timezone.utc).isoformat(),'source_state_sha256':before,'root_completion':ref(completion),'independent_index':ref(index),'author_package':author,'independent_package':independent,'collections':accepted,'newly_accepted_observations':60,'accepted_observations_including_Long':90,'new_scientific_trials':0,'new_GPU_jobs':0,'additional_GPU_seconds_this_supervision':0,'allocation_cost_already_accounted_once':723,'total_GPU_seconds_unchanged':1980004,'current_action_development_trials':5400,'compatible_development_trials':6000,'all_historical_development_trials':6612,'final_release':False,'final_trials':0}
 save(B+'/collection_root_acceptance.json',record)
 f['fixed_observation_collections_20261020T1825']=accepted;f['fixed_observation_collection_acceptance_20261020T1949']=ref(B+'/collection_root_acceptance.json');s['updated_utc']=record['utc']
 assert s['registered_jobs']==baseline['registered_jobs'] and s['autonomous_training_v1']==baseline['autonomous_training_v1'] and s['current_round_cost']==baseline['current_round_cost']
 c.atomic_json(state,s,expected_sha=before);save(B+'/collection_state_update.json',{'before':before,'after':h(state),'acceptance':ref(B+'/collection_root_acceptance.json'),'immutable_training_and_job_registry':True,'cost_increment':0,'scientific_trials_increment':0})
 print(json.dumps({'status':record['status'],'observations':90,'science_trials':6000,'GPU_hours':1980004/3600,'acceptance':ref(B+'/collection_root_acceptance.json')}))

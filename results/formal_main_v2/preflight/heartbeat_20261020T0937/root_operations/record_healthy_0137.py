from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,importlib.util,copy,subprocess
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T0937'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def rd(rel):return json.loads((R/rel).read_bytes())
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 return ref(rel)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('heartbeat0137ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 path=R/'results/experiment_supervisor/state.json';before=h(path);state=rd('results/experiment_supervisor/state.json');old=copy.deepcopy(state);f=state['formal_main_progress'];ctl=state['autonomous_training_v1']
 obs=rd(B+'/initial_observation.json');assert h(R/B/'initial_observation.json')=='1ae8409d6a9fe2b90e26aea56ee0bffffd293575bb280ac1882cca2f9023743c'
 assert state['pending_submission'] is None and ctl['owner_id']==obs['controller_owner']['owner_id'] and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 assert f['root_and_independent_completed_arms']==f['trained_arms']==obs['root_independent_complete']==54
 assert f['root_and_independent_reviewed_arm_updates']==277000 and f['completed_development_trials']==1412 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert {str(j['job_id']) for j in state['registered_jobs']}==set(obs['observation']['rows'])
 now=datetime.now(timezone.utc);health=[]
 for row in obs['active_jobs']:
  job=next(j for j in state['registered_jobs'] if str(j['job_id'])==row['job_id'])
  root=Path(job['run_root']);assert root.is_relative_to(P/'results/formal_main_v2') and not root.is_symlink()
  candidates=list(root.glob('*/attempts/*/cost_events.jsonl'));assert candidates
  p=max(candidates,key=lambda x:x.stat().st_mtime_ns);assert not p.is_symlink()
  with p.open('rb') as stream:
   stream.seek(0,2);size=stream.tell();start=max(0,size-65536);stream.seek(start);raw=stream.read(size-start)
  assert raw
  rows=raw.splitlines()
  if start:rows=rows[1:]
  events=[]
  for line in rows:
   try:e=json.loads(line)
   except ValueError:continue
   if e.get('job_id')==str(job['job_id']):events.append(e)
  assert events
  last=events[-1];age=(now-datetime.fromisoformat(last['utc'])).total_seconds();assert -60<=age<=1800,(job['job_id'],age,last)
  target=B+'/live_nonweight_tails/'+str(job['job_id'])+'.txt';q=R/target;q.parent.mkdir(exist_ok=True)
  with q.open('xb') as stream:stream.write(raw)
  updates=[e for e in events if e.get('event')=='update_end']
  health.append(dict(job_id=str(job['job_id']),suite=job['suite'],budget=job['visual_tokens'],seed=job['training_seed'],arm=p.relative_to(root).parts[0],source=str(p),source_bytes_at_read=size,offset=start,captured_bytes=len(raw),tail=ref(target),latest_event=last,latest_committed_update_seen=updates[-1]['update'] if updates else None,event_age_seconds=age,partial_tail_only_not_terminal_review=True))
 assert len(health)==8
 inv=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json');assert len(inv['files'])==173
 for rel,pin in inv['files'].items():assert h(R/rel)==pin
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='healthy_scheduled_no_terminal_change',utc=now.isoformat(),root_independent_complete=54,total_arms=72,root_independent_updates=277000,machine_complete=54,all_development_trials=1412,completed_final_trials=0,final_sealed=True,active_GPU_jobs=8,reserved_GPU_slots=0,controller_lease_confirmed=obs['lifecycle_lease_held'],initial_observation=ref(B+'/initial_observation.json'),live_training_evidence=health,new_GPU_submissions=[],new_completed_training_groups=0,new_development_trials=0,allocated_GPU_hours_at_initial_snapshot=obs['allocated_GPU_hours'],cost_is_final=False,followup='No spare slot; preserve admitted Spatial v2 for next scheduled heartbeat. Object3044017 remains original-target500 A/B recovery. Normal jobs left to controller without continuous polling.',scientific_files_unchanged=173,user_notification_required=False))
 state['current_round_cost'].update(allocated_gpu_seconds=obs['allocated_GPU_seconds'],allocated_gpu_hours=obs['allocated_GPU_hours'])
 state['last_root_supervision_snapshot']=summary;state['last_supervision_utc']=now.isoformat();state['updated_utc']=now.isoformat();state['updated_date']='2026-10-20'
 state['last_healthy_supervision']=summary
 assert state['registered_jobs']==old['registered_jobs'] and state['autonomous_training_v1']==old['autonomous_training_v1'] and state['formal_main_progress']==old['formal_main_progress']
 c.atomic_json(path,state,before)
 for name in ['observe_formal_0137.py','record_healthy_0137.py']:
  q=R/B/'root_operations'/name;q.parent.mkdir(exist_ok=True)
  with q.open('xb') as stream:stream.write((R/'.local'/name).read_bytes())
 q=R/B/'previous_Git_push_verified.json'
 with q.open('xb') as stream:stream.write((R/'.local/github_push_0033_verified.json').read_bytes())
 save(B+'/root_state_update.json',dict(state_before_sha256=before,state_after_sha256=h(path),summary=summary,controller_and_registry_and_progress_unchanged=True,new_GPU_submission=False,normal_training_not_polled_again=True))
 print(json.dumps(dict(status='healthy_no_terminal_change',complete=54,active=8,GPU_hours=obs['allocated_GPU_hours'],summary=summary,live=[dict(job_id=x['job_id'],arm=x['arm'],last_update=x['latest_committed_update_seen'],last_event=x['latest_event']['event'],age=round(x['event_age_seconds'],1)) for x in health])),flush=True)

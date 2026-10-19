from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0432';HEAD='398e9d446275307d597b86a0a7bc3de264d59bbf'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel):return json.loads((R/rel).read_text())
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(rel)
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('healthy2032ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
obrel=B+'/initial_observation.json';assert h(R/obrel)=='b619148235fa3345afd5a9e2536d252281bb54d4ca9e549b427e7d1bfcd67430'
ob=read(obrel);assert ob['root_independent_complete']==ob['machine_and_prior_complete']==48 and len(ob['capacity']['occupied'])==8 and ob['pending'] is None
assert all(j['status']=='RUNNING' for j in ob['active_jobs'])
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 statepath=R/'results/experiment_supervisor/state.json';before=h(statepath);s=read('results/experiment_supervisor/state.json');old=copy.deepcopy(s)
 assert s['pending_submission'] is None and s['formal_main_progress']['root_and_independent_completed_arms']==48 and len(s['formal_main_progress']['completed_training_pairs'])==24
 assert {str(j['job_id']) for j in s['registered_jobs']}==set(ob['observation']['rows'])
 assert s['autonomous_training_v1']['owner_id']==ob['controller_owner']['owner_id'] and s['autonomous_training_v1']['reserved_GPU_slots']==1
 assert s['autonomous_training_v1']['reservation_root_record']==ob['reservation_root_record']
 f=s['formal_main_progress'];assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 now=datetime.now(timezone.utc).isoformat()
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='bounded_scheduled_health_check',utc=now,observation=ref(obrel),status='healthy_no_new_completed_groups_or_actionable_change',root_independent_complete=48,total_arms=72,root_independent_updates=247000,active_GPU_jobs=8,allocated_GPU_seconds=ob['allocated_GPU_seconds'],allocated_GPU_hours=ob['allocated_GPU_hours'],cost_is_final=False,controller_owner_matches_and_lease_held=True,pending=None,new_GPU_submissions=[],new_training_completions=0,new_development_trials=0,completed_final_trials=0,final_sealed=True,exact_next_slot_reservation=ob['reservation_root_record'],next_action='At next scheduled supervision verify the registered Spatial recovery or use a genuine free reserved slot for the exact Long128seed23 development authorization;do not poll healthy GPU jobs in this turn.',normal_training_left_to_controller=True,scientific_configuration_unchanged=True,user_notification_needed=False,all_artifacts_server_only=True))
 s['last_root_health_check']=summary;s['last_supervision_utc']=now;s['updated_utc']=now
 assert s['formal_main_progress']==old['formal_main_progress'] and s['registered_jobs']==old['registered_jobs'] and s['autonomous_training_v1']==old['autonomous_training_v1'] and s['current_round_cost']==old['current_round_cost']
 c.atomic_json(statepath,s,before)
 op=R/B/'root_operations';op.mkdir(exist_ok=True)
 for name in ['observe_formal_2032.py','checkpoint_health_2032.py']:
  p=R/'.local'/name;compile(p.read_bytes(),name,'exec')
  with (op/name).open('xb') as stream:stream.write(p.read_bytes())
 with (R/B/'previous_Git_push_verified.json').open('xb') as stream:stream.write((R/'.local/github_push_1932_verified.json').read_bytes())
 inv=read('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json');assert len(inv['files'])==173
 for rel,pin in inv['files'].items():assert h(R/rel)==pin
 exact={'results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl'}
 selected=[];excluded=[]
 for row in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split('\0'):
  if not row:continue
  status,name=row[:2],row[3:];assert status in (' M','??'),row
  accept=name in exact or name.startswith(B+'/')
  if name.startswith('results/formal_main_v2/control_transport/'):
   lines=(R/name).read_text().splitlines();accept=bool(lines) and json.loads(lines[-1]).get('event')=='control_end'
  if accept:
   p=R/name;assert p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20)
   assert p.suffix not in ('.pt','.pth','.safetensors','.ckpt','.pyc')
   selected.append(name)
  else:excluded.append(name)
 assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/slurm/cti-formal_3043399.out','results/slurm/cti-formal_3043399.err','results/formal_main_v2/control_transport/heartbeat_2032_checkpoint.jsonl'},excluded
 for i in range(0,len(selected),50):git('add','--',*selected[i:i+50])
 index=[]
 for rel in selected:
  raw=git('show',':'+rel).stdout;assert hashlib.sha256(raw).hexdigest()==h(R/rel);index.append(dict(path=rel,sha256=h(R/rel),bytes=len(raw)))
 for rel,pin in inv['files'].items():assert hashlib.sha256(git('show',':'+rel).stdout).hexdigest()==pin
 assert not git('diff','--cached','--name-only','--','configs','src','scripts','AGENTS.md','docs','results/formal_main_v2/nonweight_archives/v1').stdout
 git('diff','--cached','--check')
 delivery=save(B+'/git_delivery.json',dict(schema='formal_main_v2',status='health_snapshot_index_verified',baseline=HEAD,files=index,frozen_index_and_worktree_files=173,scientific_or_plan_changes=False,raw_archives_unchanged=True,weights_added=False,excluded_live_files=excluded,current_round_cost_not_overwritten_from_observation=True))
 git('add','--',delivery['path']);git('diff','--cached','--check')
 answer=git('commit','-m','Record healthy eight-GPU supervision snapshot without new submissions')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_2032.json',dict(commit=commit,baseline=HEAD,files=len(selected)+1))
 print(json.dumps(dict(status='healthy_snapshot_committed',commit=commit,files=len(selected)+1,root_complete=48,GPU_hours=ob['allocated_GPU_hours'],occupied=8,new_GPU_submissions=[],user_notification_needed=False)))

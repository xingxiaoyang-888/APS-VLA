from pathlib import Path
from datetime import datetime,timezone
import argparse,json,hashlib,sys,importlib.util,subprocess,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T2218'
E='results/formal_main_v2/engineering/supervision_delivery_20261020T1418'
RAW_PATHS=['results/formal_main_v2/libero_goal/k64/seed17/training/A/attempts/20261019T215903_a4d9d3b13b80/cost_events.jsonl','results/formal_main_v2/libero_goal/k64/seed17/training/B/attempts/20261020T072534_e83e769526f0/cost_events.jsonl','results/formal_main_v2/libero_goal/k64/seed17/training/cache_events/3043762_74bdc10cc722.jsonl']
SNAPSHOT='results/formal_main_v2/nonweight_archives/v1/snapshots/Goal64seed17_20261020T1418.json'
SNAPSHOT_SHA='275092a703d21e6019056cbbd11f3739696d903d8e840af13db2dc1650ce0da6'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel):return json.loads((R/rel).read_bytes())
def ref(rel):return dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
def checked(rr):
 assert h(R/rr['path'])==rr['sha256'];return rd(rr['path'])
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
def module(name,rel,pin):
 p=R/rel;assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m
ap=argparse.ArgumentParser();ap.add_argument('--inputs',required=True);ap.add_argument('--inputs-sha256',required=True);args=ap.parse_args()
I=checked(dict(path=args.inputs,sha256=args.inputs_sha256))
assert I['baseline']=='e79204d66ecc25b3d9927499d01e2f4dd34a0fbb' and I['new_job_ids']==['3050192','3050205','3050224']
c=module('delivery20261020T1418ctl','scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==I['baseline'] and not git('diff','--cached','--name-only').stdout
 state=rd('results/experiment_supervisor/state.json');f=state['formal_main_progress']
 assert state['pending_submission'] is None and state['autonomous_training_v1']['reserved_GPU_slots']==0
 assert f['root_and_independent_completed_arms']==64 and f['completed_development_trials']==5012 and f['current_action_development_trial_count']==3800
 assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 summary=checked(I['summary']);ind=checked(I['independent_final_review'])
 assert ind['status']=='passed' and state['last_root_supervision_snapshot']==I['summary']
 assert I['root_integrity_status_path'] in f and f[I['root_integrity_status_path']]['status']=='passed'
 assert f[I['root_integrity_status_path']]['independent_review']==I['independent_final_review']
 root_sources={}
 for name,pin in I['transport_pins'].items():
  assert h(R/name)==pin
  lines=[json.loads(x) for x in (R/name).read_bytes().splitlines()]
  assert lines[0]['event']=='control_start' and lines[-1]['event']=='control_end'
  entry=lines[0].get('entrypoint','');parts=Path(entry).parts
  if len(parts)==2 and parts[0]=='.local':
   orig=R/entry;expected=lines[0]['entrypoint_sha256'];assert h(orig)==expected
   dst=R/B/'root_operations'/orig.name
   if dst.exists():assert h(dst)==expected
   else:dst.write_bytes(orig.read_bytes())
   root_sources[dst.relative_to(R).as_posix()]=dict(original=entry,sha256=expected)
 for row in I.get('additional_root_sources',[]):
  orig=R/row['path'];assert h(orig)==row['sha256']
  dst=R/B/'root_operations'/orig.name
  if dst.exists():assert h(dst)==row['sha256']
  else:dst.write_bytes(orig.read_bytes())
  root_sources[dst.relative_to(R).as_posix()]=dict(original=row['path'],sha256=row['sha256'],not_yet_executed=row.get('not_yet_executed',False))
 own=R/B/'root_operations'/Path(__file__).name
 if own.exists():assert h(own)==h(Path(__file__))
 else:own.write_bytes(Path(__file__).read_bytes())
 save(B+'/root_operation_sources_v2.json',dict(status='exact_sources_preserved',sources=root_sources))
 # Restore original immutable audit log visibility without changing their bytes.
 ignore=R/'.gitignore';prior=ignore.read_text();adds=[]
 for p in sorted((R/E).rglob('*.log')):
  line='!/'+p.relative_to(R).as_posix()
  if line not in prior.splitlines():adds.append(line)
 for name in RAW_PATHS:
  line='/'+name
  if line not in prior.splitlines():adds.append(line)
 if adds:ignore.write_text(prior+'\n# Exact immutable audit logs, 20261020T1418.\n'+'\n'.join(adds)+'\n')
 exact={'.gitignore','results/experiment_supervisor/state.json',args.inputs}|set(I['extra_exact'])
 event_dir='results/formal_main_v2/autonomous_training/run_v1/events';idx=rd(event_dir+'/index.json')
 assert idx['version']==1
 previous_sequence=None;previous_hash=None
 for sealed in idx['sealed']:
  assert h(R/event_dir/sealed['path'])==sealed['sha256'] and (R/event_dir/sealed['path']).stat().st_size==sealed['bytes']
  previous_sequence=sealed['last_sequence'];previous_hash=sealed['last_event_sha256']
  exact.add(event_dir+'/'+sealed['path'])
 if previous_sequence is not None:
  with (R/event_dir/idx['active']).open() as f0:first=json.loads(next(f0))
  assert first['sequence']==previous_sequence+1 and first['previous_event_sha256']==previous_hash
 exact.update([event_dir+'/index.json',event_dir+'/'+idx['active']])
 archived={}
 for p in sorted((R/B).glob('*delivery*.json')):
  pack=rd(p.relative_to(R).as_posix())
  for row in pack.get('copies',[]):
   name=row['archive']['path'];assert h(R/name)==row['archive']['sha256']==row['source']['sha256']
   assert (R/name).stat().st_size==row['source']['bytes'];archived[name]=ref(name)
 pull=checked(I['pull'])
 pull_files={x['relative']:dict(path=x['relative'],sha256=x['sha256'],bytes=x['bytes']) for x in pull['files']}
 for rr in I.get('additional_pulls',[]):
  extra_pull=checked(rr);assert extra_pull['status']=='verified_nonweight_snapshot'
  for x in extra_pull['files']:
   row=dict(path=x['relative'],sha256=x['sha256'],bytes=x['bytes'])
   if x['relative'] in pull_files:assert pull_files[x['relative']]==row
   pull_files[x['relative']]=row
 selected=[];excluded=[]
 for row in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split('\0'):
  if not row:continue
  status,name=row[:2],row[3:];assert status in (' M','??'),row
  accept=name in exact or name.startswith(B+'/') or name.startswith(E+'/') or any(name.startswith(prefix) for prefix in I['extra_prefixes'])
  if name.startswith('results/formal_main_v2/control_transport/'):accept=name in I['transport_pins']
  assert name not in RAW_PATHS,'Explicit previously archived raw must remain ignored'
  if accept:
   p=R/name;assert p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20)
   assert p.suffix not in ('.pt','.pth','.ckpt','.bin','.safetensors','.pyc','.init','.npz','.npy','.h5','.hdf5')
   selected.append(name)
  else:excluded.append(name)
 assert set(excluded)<=set(I['allowed_live_exclusions']),excluded
 assert set(archived)<=set(selected)
 assert all(p.relative_to(R).as_posix() in selected for p in (R/E).rglob('*') if p.is_file()),'Immutable archive ignored or missing'
 for i in range(0,len(selected),60):git('add','--',*selected[i:i+60])
 required=dict(schema='cti_nonweight_archive_stage_v1',kind='required_files',files=[ref(n) for n in sorted(selected)])
 save(B+'/git_required_files.json',required);git('add','--',B+'/git_required_files.json')
 actual=set(git('diff','--cached','--name-only').stdout.decode().splitlines())
 assert actual==set(selected)|{B+'/git_required_files.json'}
 g=module('delivery20261020T1418index','scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6')
 result=g.check(R,SNAPSHOT,SNAPSHOT_SHA,RAW_PATHS,B+'/git_required_files.json')
 assert result['status']=='verified_index_archive_delivery' and result['frozen_files_verified_in_worktree_and_index']==173
 save(B+'/git_index_guard.json',result)
 diag=git('diff','--cached','--check',check=False)
 save(B+'/git_whitespace_diagnostic.json',dict(returncode=diag.returncode,stdout=diag.stdout.decode(),stderr=diag.stderr.decode()))
 exceptions=[]
 if diag.returncode:
  headers=[l for l in diag.stdout.decode().splitlines() if re.match(r'^.*?:[0-9]+: ',l)]
  assert headers and not diag.stderr
  for header in headers:
   m=re.fullmatch(r'(.*?):[0-9]+: (trailing whitespace|new blank line at EOF)\.',header);assert m,header
   name=m.group(1);assert name in archived or name in pull_files,name
   if name in pull_files:assert ref(name)==pull_files[name]
   exceptions.append(name)
  exceptions=sorted(set(exceptions))
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 save(B+'/git_delivery.json',dict(schema='formal_main_v2',utc=datetime.now(timezone.utc).isoformat(),status='exact_ordinary_index_and_173frozen_verified',
  baseline=I['baseline'],required_files=ref(B+'/git_required_files.json'),index_guard=ref(B+'/git_index_guard.json'),
  independent_integration_review=I['independent_final_review'],immutable_archive_files=len(archived),
  weights_added=False,sealed_final_values_added=False,excluded_live_files=excluded,
  raw_original_whitespace_preserved=[ref(n) for n in exceptions],root_independent_complete=64,
  new_root_GPU_submissions=I['new_job_ids'],new_development_trials_accepted=1000,current_wrapper_actual_trials=3800,
  legacy_equivalent_trials=600,compatible_development_trials=4400,unique_initial_states=400,
  Goal256_seed17_unaccepted_trials=200,held_trials_not_in_success_denominator=True,
  additional_training_archived_without_root_acceptance=['3043762'],
  old_GPU_cost_not_added_again=True,all_historical_results_preserved=True,final_sealed=True,no_normal_GPU_realtime_polling=True))
 for n in [B+'/git_index_guard.json',B+'/git_whitespace_diagnostic.json',B+'/git_delivery.json']:
  git('add','--',n);assert git('show',':'+n).stdout==(R/n).read_bytes()
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines())
 out=git('commit','-m','Record Goal three-seed development results and isolate paired-observation failure')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 # Fully dated receipt prevents collisions with prior daily heartbeat names.
 save('.local/git_commit_20261020T1418.json',dict(commit=commit,baseline=I['baseline'],files=count,index_guard='passed',
  root_complete=64,new_accepted_development_trials=1000,current_action_development_trials=3800,held_Goal_trials=200))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=commit,files=count,summary=out.stdout.decode().splitlines()[:2])),flush=True)

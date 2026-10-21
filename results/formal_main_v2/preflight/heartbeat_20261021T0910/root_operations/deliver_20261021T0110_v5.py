from pathlib import Path
from datetime import datetime,timezone
import argparse,ast,hashlib,importlib.util,json,re,subprocess,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0910';E='results/formal_main_v2/engineering/supervision_delivery_20261021T0110';PREV='results/formal_main_v2/preflight/heartbeat_20261021T0225';BASE='98817e8d996e8db750191cccb8b01a7ba81da169'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/last_training_20261020T1644.json';SSHA='1ec87a42055015a0d0ea5e059d913d3d1de0d7be0870b023a81f7ee774976509'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size)
def save(n,v):
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def cp(src,dst):
 p=R/src;q=R/dst;assert p.resolve()==p and q.resolve()==q and not any(x.is_symlink() for x in [p,*p.parents,q,*q.parents]);q.parent.mkdir(parents=True,exist_ok=True)
 if q.exists():assert q.read_bytes()==p.read_bytes()
 else:q.open('xb').write(p.read_bytes())
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
def changed():return {x[3:]:x[:2] for x in git('status','--porcelain=v1','--untracked-files=all','-z','--','.',':(exclude)results/formal_main_v2/raw_runtime/goal_full200_20261021T0110/attempt01').stdout.decode().split(chr(0)) if x}
def module(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
ap=argparse.ArgumentParser();ap.add_argument('--final-audit',required=True);ap.add_argument('--final-audit-sha256',required=True);a=ap.parse_args();assert h(R/a.final_audit)==a.final_audit_sha256
c=module('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','deliver2054ctl');guard=module('scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6','deliver2054guard')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==BASE and git('diff','--cached','--name-only').stdout==b''
 s=rd('results/experiment_supervisor/state.json');f=s['formal_main_progress'];ctl=s['autonomous_training_v1'];assert (f['root_and_independent_completed_arms'],f['root_and_independent_reviewed_arm_updates'],f['current_action_development_trial_count'],f['completed_development_trials'],f['completed_final_trials'])==(72,360000,6388,7600,0)
 assert not f['test_opened'] and not f['global_release_created'] and s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 last=s['last_root_supervision_snapshot'];assert last['path']==B+'/final_summary.json' and h(R/last['path'])==last['sha256'];summary=rd(last['path']);assert summary['compatible_development_trials']==7000 and summary['new_development_accepted']==588 and '3054409' in summary['new_GPU_jobs'] and summary['allocated_GPU_seconds']>=1992004 and summary['Object599']['legacy599_root_adopted'] is True and summary['Goal_paired_input_engineering']['status']=='root_and_independent_engineering_only_accepted'
 audit=rd(a.final_audit);assert audit['status']=='passed_final_delivery_review' and audit['blockers']==[] and audit['source173_verified'] is True and audit['final_sealed'] is True and audit['state_sha256']==h(R/'results/experiment_supervisor/state.json')
 old={}
 for name in ['git_CPU_fixture_archive.json','git_operational_metadata_archive.json']:
  name=PREV+'/'+name;value=rd(name);assert git('show','HEAD:'+name).stdout==(R/name).read_bytes()
  for row in value['files']:old[row['path']]=row
 assert len(old)==61
 for n,v in old.items():assert ref(n)=={k:v[k] for k in ['path','sha256','bytes']}
 known={'results/experiment_supervisor/state.json'}|{'docs/'+n+'.md' for n in ['实验进度','完整实验计划','正式主实验规划','正式主实验阶段结论','正式自动连续训练执行登记','研究方案','论文方法与实验设置草稿','正式下游阻塞登记_20261021T0110']}
 prefixes=[B+'/',E+'/','results/formal_main_v2/execution/object_single_error_v1/','scripts/ops/formal_object_single_error_v1/','scripts/ops/formal_object_single_error_gateway_v1/','scripts/ops/formal_goal_full200_gate_v1/','scripts/ops/formal_goal_full200_dispatch_v1/','results/formal_main_v2/libero_spatial/downstream/development/8c843c1d4ee8383c/attempt01/','results/formal_main_v2/pulls/20261021T013702Z_1056842ddda1/','results/formal_main_v2/engineering/goal_full200_20261021T0110/']
 known.update(['results/formal_main_v2/downstream_reviews/3054201.json','results/formal_main_v2/invocations/object_single_error_task08_state0049_dense_attempt01.json'])
 pknown='results/formal_main_v2/pulls/20261021T013702Z_1056842ddda1/receipt.json'
 assert h(R/pknown)=='ca9d4e64b02abde022ecb6ac83c4653be0c0882485bd0f73478f69570f3e8a60'
 known_pull=rd(pknown);assert known_pull['final_evidence'] and not known_pull['weights_copied'] and not known_pull['sealed_initial_states_copied'] and not known_pull['missing']
 for row in known_pull['files']:
  assert ref(row['relative'])==dict(path=row['relative'],sha256=row['sha256'],bytes=row['bytes'])
  known.add(row['relative'])
 save(B+'/git_initial_allowlist_failure.json',dict(status='prior_guard_stop_before_staging_preserved',prior_entrypoint='.local/deliver_20261021T0110_v4.py',prior_entrypoint_sha256='4c5380c823ecbcfd4b4e9fd0e3080fceecf7d4c9e22e99deb9555c6c02885e45',unknown_paths=['results/formal_main_v2/job_receipts/3054201.json','results/slurm/cti-formal-downstream_3054201.err','results/slurm/cti-formal-downstream_3054201.out'],reason='Initial changed-path guard ran before adding the already independently verified exact Spatial14-file pull allowlist; moved the same pinned list before the guard.',index_empty_verified=True,state_unchanged=True,new_GPU_submissions=0,scientific_changes=False,original_pull_receipt=ref(pknown)))

 opened=[];closed=[];sources=[]
 for n in changed():
  if n in old or not n.startswith('results/formal_main_v2/control_transport/'):continue
  lines=[json.loads(x) for x in (R/n).read_bytes().splitlines()];assert lines[0]['event']=='control_start'
  if lines[-1]['event']!='control_end':opened.append(n);continue
  closed.append(n);known.add(n);rel=lines[0].get('entrypoint','')
  if len(Path(rel).parts)==2 and Path(rel).parts[0]=='.local':
   assert h(R/rel)==lines[0]['entrypoint_sha256'];dst=B+'/root_operations/'+Path(rel).name;guard.lexical(dst);cp(rel,dst);sources.append({'source':rel,'archive':ref(dst)})
 for rel in ['.local/deliver_20261021T0110_v1.py','.local/deliver_20261021T0110_v2.py','.local/deliver_20261021T0110_v3.py','.local/deliver_20261021T0110_v4.py','.local/deliver_20261021T0110_v5.py','.local/github_push_20261021T0110.py']:
  dst=B+'/root_operations/'+Path(rel).name;cp(rel,dst);sources.append({'source':rel,'archive':ref(dst)})
 for rel in ['.local/github_push_20261020T2358_verified.json','.local/git_commit_20261020T2358.json']:
  dst=B+'/prior_Git_proofs/'+Path(rel).name;cp(rel,dst)
 save(B+'/root_operation_sources_v2.json',{'status':'exact_nonweight_sources_preserved','sources':sources,'closed_transports':[ref(n) for n in closed],'open_transports_excluded':opened,'all_project_writes_server_only':True})
 selected=[];unknown=[]
 for n,status in changed().items():
  if n in old or n in opened:continue
  if n in known or n.startswith(tuple(prefixes)):selected.append(n)
  else:unknown.append(n)
 assert not unknown,unknown
 # Git ignores archives/logs, so force-add ONLY the exact independently reviewed
 # allowlists for the current CPU delivery packages; previous Goal15 blob volumes are already committed.
 force_refs={}
 archive_source=(R/'.local/archive_packages_20261021T0110_v6.py').read_text()
 assert h(R/'.local/archive_packages_20261021T0110_v6.py')=='04f38c99941b109b71530ec30ae5ea30db6db16b5cad965fc7e7ffd893e1a67d'
 archive_roots=ast.literal_eval(next(x for x in archive_source.splitlines() if x.startswith('ALLOWED=')).split('=',1)[1])
 for receipt_path in sorted((R/B).glob('*_archive.json')):
  receipt=rd(receipt_path.relative_to(R).as_posix())
  if receipt.get('status')!='immutable_nonweight_package_archived':continue
  destination=receipt['destination'];assert destination.startswith(E+'/')
  original=receipt['manifest'];parent=next(k for k,v in archive_roots.items() if destination==E+'/'+v);assert original['path'].startswith(parent+'/');manifest_name=Path(original['path']).stem+'_original.json';mrel=destination+'/'+manifest_name;assert h(R/mrel)==original['sha256'];m=rd(mrel);files=m['files']
  if isinstance(files,dict):files=[dict(v,path=k) for k,v in files.items()]
  assert len(files)==receipt['file_count']
  declared=m.get('source_root',str((R/original['path']).parent))
  if declared is not None:
   declared=Path(declared);assert '..' not in declared.parts
   declared=declared if declared.is_absolute() else R/declared;assert declared.resolve()==declared and declared.is_relative_to(R/parent)
   declared_prefix=declared.relative_to(R/parent)
  for row in files:
   n=row.get('source',row.get('path'))
   if n.startswith(parent+'/'):n=n[len(parent)+1:]
   elif declared is not None:n=(declared_prefix/n).as_posix()
   assert n and not Path(n).is_absolute() and '..' not in Path(n).parts
   rel=destination+'/'+n;force_refs[rel]={'path':rel,'sha256':row['sha256'],'bytes':row['bytes']}
  if 'copied_files' in receipt:
   assert sorted((x['path'],x['sha256'],x['bytes']) for x in receipt['copied_files'])==sorted((destination+'/'+((row.get('source',row.get('path')))[len(parent)+1:] if row.get('source',row.get('path')).startswith(parent+'/') else (declared_prefix/row.get('source',row.get('path'))).as_posix() if declared is not None else row.get('source',row.get('path'))),row['sha256'],row['bytes']) for row in files)
  force_refs[mrel]=ref(mrel)
 pullrel='results/formal_main_v2/pulls/20261021T013702Z_1056842ddda1/receipt.json';assert h(R/pullrel)=='ca9d4e64b02abde022ecb6ac83c4653be0c0882485bd0f73478f69570f3e8a60'
 pull=rd(pullrel);assert pull['final_evidence'] and not pull['weights_copied'] and not pull['sealed_initial_states_copied'] and not pull['missing']
 for row in pull['files']:
  n=row['relative'];force_refs[n]={'path':n,'sha256':row['sha256'],'bytes':row['bytes']}
 for n,v in force_refs.items():assert ref(n)==v
 selected=sorted(set(selected)|set(force_refs));assert len(selected)>30
 save(B+'/git_ignored_allowlist_v1.json',{'status':'exact_reviewed_archive_allowlists_forced','new_GPU_blobs':0,'package_files':[force_refs[n] for n in sorted(force_refs)],'no_glob_add_of_ignored_outputs':True})
 selected.append(B+'/git_ignored_allowlist_v1.json')
 for n in selected:
  guard.lexical(n);p=R/n;assert p.is_file() and p.resolve()==p and p.stat().st_size<100*(1<<20) and not any(x.is_symlink() for x in [p,*p.parents])
  assert p.suffix.lower() not in ['.pt','.pth','.ckpt','.safetensors','.bin','.h5','.hdf5','.pkl','.pickle','.npy','.npz']
 for i in range(0,len(selected),60):git('add','-f','--',*selected[i:i+60])
 required=B+'/git_required_files_v1.json';save(required,{'schema':'cti_nonweight_archive_stage_v1','kind':'required_files','files':[ref(n) for n in selected]});git('add','--',required)
 RAW=[v['path'] for v in rd(SNAP)['files']];assert len(RAW)==9
 checked=guard.check(R,SNAP,SSHA,RAW,required);assert checked['status']=='verified_index_archive_delivery' and checked['frozen_files_verified_in_worktree_and_index']==173
 save(B+'/git_index_guard_v1.json',checked)
 diag=git('diff','--cached','--check',check=False);assert not diag.stderr;exceptions=[]
 if diag.returncode:
  for line in diag.stdout.decode().splitlines():
   if not re.match(r'^.*?:[0-9]+: ',line):continue
   m=re.fullmatch(r'(.*?):[0-9]+: (trailing whitespace|new blank line at EOF)\.',line);assert m,line;n=m.group(1);assert n.startswith((E+'/',B+'/root_operations/')),n;exceptions.append(n)
  assert exceptions
 exceptions=sorted(set(exceptions));save(B+'/git_whitespace_diagnostic_v1.json',{'returncode':diag.returncode,'stdout':diag.stdout.decode(),'exact_archived_source_whitespace_preserved':exceptions});git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 save(B+'/git_delivery_v1.json',{'schema':'formal_main_v2','status':'exact_index_and173_frozen_verified','baseline':BASE,'source_frozen_files':173,'root_complete':72,'compatible_development_trials':7000,'new_development_accepted':588,'new_GPU_jobs':summary['new_GPU_jobs'],'accepted_fixed_observations':90,'independent_delivery_audit':ref(a.final_audit),'final_sealed':True,'weights_added':False,'all_project_writes_server_only':True,'open_transports_excluded':opened,'prospective_Goal_raw_runtime_scope_deferred_to_exact_terminal_archive':'results/formal_main_v2/raw_runtime/goal_full200_20261021T0110/attempt01','previously_archived_raw_paths_excluded':len(old),'index_guard':ref(B+'/git_index_guard_v1.json'),'summary':last,'required_files':ref(required),'utc':datetime.now(timezone.utc).isoformat()})
 for name in ['git_index_guard_v1.json','git_whitespace_diagnostic_v1.json','git_delivery_v1.json']:git('add','--',B+'/'+name);assert git('show',':'+B+'/'+name).stdout==(R/B/name).read_bytes()
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines());res=git('commit','-m','Accept Spatial588 and dispatch exact Object correction with audited Goal gates');head=git('rev-parse','HEAD').stdout.decode().strip();save('.local/git_commit_20261021T0110.json',{'commit':head,'baseline':BASE,'files':count,'root_complete':72,'index_guard':'passed','final_sealed':True});print(json.dumps({'status':'committed_not_yet_pushed','commit':head,'files':count,'summary':res.stdout.decode().splitlines()[:2]}))

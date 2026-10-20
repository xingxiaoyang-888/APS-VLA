from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,importlib.util,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1527'
E='results/formal_main_v2/engineering/supervision_delivery_0727'
HEAD='4b5e393247baa850a2fe74cd432cfe5a7651e58e'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel):return json.loads((R/rel).read_bytes())
def ref(rel):return dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as stream:json.dump(x,stream,sort_keys=True,ensure_ascii=False,indent=2);stream.write('\n')
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
def module(name,rel,pin):
 p=R/rel;assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m
c=module('delivery0727ctl','scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 state=rd('results/experiment_supervisor/state.json');f=state['formal_main_progress']
 assert state['pending_submission'] is None and f['root_and_independent_completed_arms']==62 and f['root_and_independent_reviewed_arm_updates']==314000
 assert f['completed_development_trials']==2612 and f['current_action_development_trial_count']==1400 and f['current_action_development_unique_initial_states']==100
 assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created'] and state['autonomous_training_v1']['reserved_GPU_slots']==0
 for job in ['3047152','3047156','3047163']:assert len([x for x in f['Long_remaining16_development_submissions'] if x['job_id']==job and x['completed_trials_accepted']==200])==1
 assert len([x for x in f['Long_remaining16_development_submissions'] if x['job_id']=='3047443' and x['completed_trials_accepted']==0])==1
 assert h(R/B/'summary.json')=='8a781eec1b076e12f82e39ede1df04d19839027ac5a75afb9f450146abd21143'
 ignore=R/'.gitignore';prior=ignore.read_text();adds=[]
 for p in sorted((R/E).rglob('*.log')):
  assert p.is_file() and not p.is_symlink();line='!/'+p.relative_to(R).as_posix()
  if line not in prior.splitlines():adds.append(line)
 if adds:ignore.write_text(prior+'\n# Exact immutable audit logs,20261020T1527.\n'+'\n'.join(adds)+'\n')
 source=B+'/root_operations/deliver_0727.py'
 with (R/source).open('xb') as stream:stream.write(Path(__file__).read_bytes())
 exact={'.gitignore','results/experiment_supervisor/state.json'}
 event_dir='results/formal_main_v2/autonomous_training/run_v1/events';idx=rd(event_dir+'/index.json')
 assert idx['version']==1 and idx['active']=='events.000001.jsonl' and len(idx['sealed'])==1
 sealed=idx['sealed'][0];assert sealed['path']=='events.000000.jsonl' and sealed['first_sequence']==1 and sealed['last_sequence']==4213
 assert h(R/event_dir/sealed['path'])==sealed['sha256'] and (R/event_dir/sealed['path']).stat().st_size==sealed['bytes']
 with (R/event_dir/idx['active']).open() as stream:first=json.loads(next(stream))
 assert first['sequence']==sealed['last_sequence']+1 and first['previous_event_sha256']==sealed['last_event_sha256']
 exact.update([event_dir+'/index.json',event_dir+'/'+idx['active'],event_dir+'/'+sealed['path']])
 exact.update('docs/'+n+'.md' for n in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式Long其余16选择器开发登记','正式Long256三种子与64预算开发进展'])
 exact.add('results/formal_main_v2/invocations/libero_10_development_b426228fe9d2fd0a_attempt01.json');exact.add('results/formal_main_v2/submissions/3047443.json')
 raw_long={}
 for job in ['3047152','3047156','3047163']:
  exact.update(['results/formal_main_v2/job_receipts/'+job+'.json','results/formal_main_v2/downstream_reviews/'+job+'.json','results/formal_main_v2/downstream_reviews/'+job+'_independent.json'])
  exact.update('results/slurm/cti-formal-downstream_'+job+suffix for suffix in ['.out','.err'])
  files=rd('results/formal_main_v2/downstream_reviews/'+job+'.json')['files']
  for name,pin in files.items():
   assert h(R/name)==pin,name
   if name in raw_long:assert raw_long[name]==pin
   raw_long[name]=pin
 exact.update(raw_long)
 prefixes=[B+'/',E+'/','results/formal_main_v2/pulls/20261020T072944Z_a9f44da5ac69/','results/formal_main_v2/downstream_gateway/a45db8af1bee86142cf80df416c5bf27b734f493448eb5ee429c92947b48c244/']
 archived={}
 for name in ['Long_terminal_independent_delivery.json','Long64s41_submission_independent_delivery.json','Long_legacy6_CPU_candidate_delivery.json']:
  for row in rd(B+'/'+name)['copies']:
   path=row['archive']['path'];assert h(R/path)==row['archive']['sha256']==row['source']['sha256'];assert (R/path).stat().st_size==row['source']['bytes'];archived[path]=ref(path)
 selected=[];excluded=[]
 for row in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split('\0'):
  if not row:continue
  status,name=row[:2],row[3:];assert status in (' M','??'),row
  accept=name in exact or any(name.startswith(p) for p in prefixes)
  if name.startswith('results/formal_main_v2/control_transport/'):
   lines=(R/name).read_text().splitlines();accept=bool(lines) and json.loads(lines[-1]).get('event')=='control_end'
  if accept:
   p=R/name;assert p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20),name
   assert p.suffix not in ('.pt','.pth','.ckpt','.bin','.safetensors','.pyc','.init','.npz','.npy','.h5','.hdf5'),name
   selected.append(name)
  else:excluded.append(name)
 assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_0727_delivery.jsonl'},excluded
 assert set(archived)<=set(selected) and all(p.relative_to(R).as_posix() in selected for p in (R/E).rglob('*') if p.is_file()),'exact audit files ignored or unlisted'
 assert set(raw_long)<=set(selected)
 for i in range(0,len(selected),60):git('add','--',*selected[i:i+60])
 required=dict(schema='cti_nonweight_archive_stage_v1',kind='required_files',files=[ref(n) for n in sorted(selected)])
 save(B+'/git_required_files.json',required);git('add','--',B+'/git_required_files.json')
 # New raw files fit ordinary Git limits. Reuse the pinned read-only index verifier,
 # without invoking unrelated prior lossless archive restoration or fabricating a snapshot.
 g=module('ordinary_delivery0727','scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6')
 codec=g.load_codec();required_rows=g.required_value(required,codec)
 with g.index_reader(R) as index:
  inv_data,iv=g.same_local_index(index,g.INVENTORY,codec);assert iv['sha256']==g.INVENTORY_SHA256
  inventory=json.loads(inv_data);assert len(inventory['files'])==173
  for name,pin in inventory['files'].items():
   assert name not in index.changed
   _,q=g.same_local_index(index,name,codec);assert q['sha256']==pin
  assert set(index.changed)==set(selected)|{B+'/git_required_files.json'}
  assert all(v in ['A','M'] for v in index.changed.values())
  for row in required_rows:g.same_local_index(index,row['path'],codec,expected=row)
  g.same_local_index(index,B+'/git_required_files.json',codec,expected=ref(B+'/git_required_files.json'))
  for name,pin in raw_long.items():
   _,q=g.same_local_index(index,name,codec);assert q['sha256']==pin
  for name,row in archived.items():g.same_local_index(index,name,codec,expected=row)
  index.unchanged()
 guard=dict(status='verified_ordinary_nonweight_Git_index',verifier_source_sha256=h(R/'scripts/ops/check_nonweight_archive_stage.py'),verifier_apis=['required_value','index_reader','same_local_index','Index.unchanged'],required_files_verified=len(required_rows),new_raw_files_verified=len(raw_long),all_index_objects_within_100MiB=True,frozen_files_verified_in_worktree_and_index=173,prior_archives_modified=False,new_archive_snapshot_claimed=False,weights_or_binary_state_payloads_added=False,exact_independent_archive_files=len(archived))
 save(B+'/git_index_guard.json',guard)
 diag=git('diff','--cached','--check',check=False)
 save(B+'/git_whitespace_diagnostic.json',dict(returncode=diag.returncode,stdout=diag.stdout.decode(),stderr=diag.stderr.decode()))
 exceptions=[]
 if diag.returncode:
  headers=[line for line in diag.stdout.decode().splitlines() if re.match(r'^.*?:[0-9]+: ',line)]
  assert headers and not diag.stderr
  for header in headers:
   m=re.fullmatch(r'(.*?):[0-9]+: (trailing whitespace|new blank line at EOF)\.',header);assert m,header
   name=m.group(1)
   assert name in archived or name in raw_long and name.endswith(('.out','.err','.log')),name
   exceptions.append(name)
  exceptions=sorted(set(exceptions))
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 additions=[B+'/git_index_guard.json',B+'/git_whitespace_diagnostic.json']
 save(B+'/git_delivery.json',dict(schema='formal_main_v2',utc=datetime.now(timezone.utc).isoformat(),status='exact_ordinary_index_and_173frozen_verified',baseline=HEAD,required_files=ref(B+'/git_required_files.json'),index_guard=ref(B+'/git_index_guard.json'),new_raw_files=len(raw_long),immutable_audit_files=len(archived),weights_added=False,sealed_final_values_added=False,excluded_live_files=excluded,raw_original_whitespace_preserved=[ref(n) for n in exceptions],root_independent_complete=62,root_accepted_updates=314000,new_root_GPU_submissions=['3047443'],exact_pending_reconciled_without_resubmission=True,new_development_trials=600,all_development_trials=2612,current_action_trials=1400,unique_initial_states_across_seven_pairs=100,Long256_paired_mean_difference_pp=2.3333333333333,Long256_development_CI95_pp=[-1,6],legacy600_not_reused=True,final_sealed=True,no_normal_GPU_realtime_polling=True,additions=[ref(n) for n in additions]))
 for n in additions+[B+'/git_delivery.json']:
  git('add','--',n);assert git('show',':'+n).stdout==(R/n).read_bytes()
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines())
 answer=git('commit','-m','Accept 600 Long development trials and three-seed statistics')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_0727.json',dict(commit=commit,baseline=HEAD,files=count,index_guard='passed',root_complete=62,new_development_trials=600))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=commit,files=count,raw_whitespace_exceptions=len(exceptions),summary=answer.stdout.decode().splitlines()[:2])),flush=True)

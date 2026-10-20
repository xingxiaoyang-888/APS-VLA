from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,importlib.util,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1727'
E='results/formal_main_v2/engineering/supervision_delivery_0927'
HEAD='7aa8ae7c2167b671bdfcb09f57fc77712d570f45'
TRANSPORT_PINS={"results/formal_main_v2/control_transport/heartbeat_0830_delivery.jsonl":"e4e223564829a8ed9c1f46ac082e62af1455988ca446689ae1fa86e36cc63c43","results/formal_main_v2/control_transport/heartbeat_0927_Long_collect_root_review.jsonl":"db20f4f5f01e9335978edfbcbaf6558a8ffb7eb0e38b727cc72f9e2ba76cab37","results/formal_main_v2/control_transport/heartbeat_0927_Long_npz_delivery.jsonl":"f038743abe30e4f80cfcc21af74c31de8fde8f70a531a4c5016ddff68df6922b","results/formal_main_v2/control_transport/heartbeat_0927_initial_observation.jsonl":"7aec1111862ab64e21bdca962302f5726b2587608d24cf4f09eb63c6f4c6b7ac","results/formal_main_v2/control_transport/heartbeat_0927_integration.jsonl":"a88a66ca5f749bb417905e41254f2db94370a70a7c88d82b7a46d212f87a579e","results/formal_main_v2/control_transport/heartbeat_0927_terminal_pull.jsonl":"8e00f970fa0b4e38565a982ad9e9426885bac3e521bc5b10994ea71c59a67dee","results/formal_main_v2/control_transport/independent_Long_collect_terminal_0927_a1.jsonl":"b5932fd8fee1fdd42e6ad55f7152bf534bdddae021be42a3d780bc104e26098e","results/formal_main_v2/control_transport/independent_Long_collect_terminal_0927_a2.jsonl":"307cd13a683a8baa5ba73924d5099ce3138eec107225395b739ed255cd760648","results/formal_main_v2/control_transport/independent_Long_observation_delivery_0927_a1.jsonl":"2a8693fb89445c8267bd3f80bdaae5879bf3556b7b19df739f473d9813ae4737","results/formal_main_v2/control_transport/legacy6_typed_bridge_0927_build_map_v1.jsonl":"e61b2e20e92e2893a87c4c46694e359f7fb580ee6602c5d6d0a463a7e365e956","results/formal_main_v2/control_transport/legacy6_typed_bridge_0927_root_recheck_v1.jsonl":"98a3badecb2ef892c839f4dce30b9e6779b0a9c21c8a9d1779b57540ebd2fd59","results/formal_main_v2/control_transport/legacy6_typed_bridge_0927_seal_v1.jsonl":"bd516e1ab2206d4b9098ea1aae74e8ba9a673bd72ad81b2b3201f17197c87296"}
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
c=module('delivery0927ctl','scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 state=rd('results/experiment_supervisor/state.json');f=state['formal_main_progress']
 assert state['pending_submission'] is None and f['root_and_independent_completed_arms']==62 and f['root_and_independent_reviewed_arm_updates']==314000
 assert f['completed_development_trials']==2812 and f['current_action_development_trial_count']==1600 and f['current_action_development_unique_initial_states']==100
 assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created'] and state['autonomous_training_v1']['reserved_GPU_slots']==0
 assert len([x for x in f['Long_remaining16_development_submissions'] if x['job_id']=='3047443' and x['completed_trials_accepted']==200])==1
 assert f['Long_fixed_observation_collection']['job_id']=='3047982' and f['Long_fixed_observation_collection']['accepted_observations']==30
 assert h(R/B/'summary.json')=='5e05c9eb667af2444f4e331a0e52bb304b364ce1d4bb593fee0037695ad6b6eb'
 ignore=R/'.gitignore';prior=ignore.read_text();adds=[]
 allowref=ref(B+'/observation_npz_delivery_allowlist.json');assert allowref['sha256']=='b23a11f750ded441b0dfd1f3c066eb032c783b186e567975b34a14f0856880e1'
 allow=rd(allowref['path']);npzs={v['path']:v for v in allow['files']};assert len(npzs)==30
 npz_audit_path=E+'/Long_observation_delivery_independent/typed_allowlist_review.json'
 assert h(R/npz_audit_path)=='17f0aa6d6e34f0b73e04fc9dd30b7a65f9221393cb63427158f102f493a609f2'
 npz_audit=rd(npz_audit_path);assert npz_audit['status']=='passed' and not npz_audit['blockers'] and npz_audit['allowlist']['sha256']==allowref['sha256']
 assert npz_audit['observations']==30 and npz_audit['total_bytes']==11839320
 for name,row in npzs.items():assert ref(name)=={k:row[k] for k in ['path','sha256','bytes']}
 for p in sorted(list((R/E).rglob('*.log'))+[R/name for name in npzs]):
  assert p.is_file() and not p.is_symlink();line='!/'+p.relative_to(R).as_posix()
  if line not in prior.splitlines():adds.append(line)
 if adds:ignore.write_text(prior+'\n# Exact immutable audit logs and30 typed development observations,20261020T1727.\n'+'\n'.join(adds)+'\n')
 source=B+'/root_operations/deliver_0927.py'
 with (R/source).open('xb') as stream:stream.write(Path(__file__).read_bytes())
 review_path='.local/git_delivery_review_0927/final_review.json'
 review=rd(review_path)
 assert review['status']=='passed' and review['script']==dict(path='.local/deliver_0927.py',sha256=h(Path(__file__)))
 assert review['transport_pins']==TRANSPORT_PINS and review['summary']==dict(path=B+'/summary.json',sha256=h(R/B/'summary.json'))
 assert review['reviewer']=='/root/long128s41_terminal_0530' and not review['blockers']
 with (R/B/'independent_Git_delivery_review.json').open('xb') as stream:stream.write((R/review_path).read_bytes())
 audit_base='.local/git_delivery_review_0927';audit_manifest=rd(audit_base+'/final_manifest.json')
 assert audit_manifest['reviewed_script']==review['script']
 audit_rows=list(audit_manifest['files'])+[ref(audit_base+'/final_manifest.json')];audit_copies=[]
 for row in audit_rows:
  n=Path(row['path']);assert not n.is_absolute() and n.is_relative_to(audit_base) and '..' not in n.parts
  p=R/n;assert p.is_file() and not p.is_symlink() and ref(n.as_posix())=={k:row[k] for k in ['path','sha256','bytes']}
  assert p.suffix in ['.py','.json','.diff','.md'] and p.stat().st_size<100*(1<<20)
  dest=E+'/Git_delivery_independent/'+n.relative_to(audit_base).as_posix();(R/dest).parent.mkdir(parents=True,exist_ok=True)
  with (R/dest).open('xb') as stream:stream.write(p.read_bytes())
  audit_copies.append(dict(source=row,archive=ref(dest)))
 save(B+'/Git_delivery_independent_delivery.json',dict(copies=audit_copies,source_manifest=ref(audit_base+'/final_manifest.json'),reviewed_script=review['script']))
 for path,pin in TRANSPORT_PINS.items():
  assert h(R/path)==pin and json.loads((R/path).read_bytes().splitlines()[-1])['event']=='control_end'
 exact={'.gitignore','results/experiment_supervisor/state.json'}
 event_dir='results/formal_main_v2/autonomous_training/run_v1/events';idx=rd(event_dir+'/index.json')
 assert idx['version']==1 and idx['active']=='events.000001.jsonl' and len(idx['sealed'])==1
 sealed=idx['sealed'][0];assert sealed['path']=='events.000000.jsonl' and sealed['first_sequence']==1 and sealed['last_sequence']==4213
 assert h(R/event_dir/sealed['path'])==sealed['sha256'] and (R/event_dir/sealed['path']).stat().st_size==sealed['bytes']
 with (R/event_dir/idx['active']).open() as stream:first=json.loads(next(stream))
 assert first['sequence']==sealed['last_sequence']+1 and first['previous_event_sha256']==sealed['last_event_sha256']
 exact.update([event_dir+'/index.json',event_dir+'/'+idx['active'],event_dir+'/'+sealed['path']])
 exact.update('docs/'+n+'.md' for n in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式Long其余16选择器开发登记','正式Long256三种子与64预算开发进展','正式Long64三种子开发结论','正式Long固定测速观测采集登记'])
 exact.add('docs/正式Long测速观测验收.md')
 raw_long={}
 for job in ['3047982']:
  exact.update(['results/formal_main_v2/job_receipts/'+job+'.json','results/formal_main_v2/downstream_reviews/'+job+'.json','results/formal_main_v2/downstream_reviews/'+job+'_independent.json'])
  exact.update('results/slurm/cti-formal-downstream_'+job+suffix for suffix in ['.out','.err'])
  files=rd('results/formal_main_v2/downstream_reviews/'+job+'.json')['files']
  for name,pin in files.items():
   assert h(R/name)==pin,name
   if name in raw_long:assert raw_long[name]==pin
   raw_long[name]=pin
 exact.update(raw_long)
 prefixes=[B+'/',E+'/','results/formal_main_v2/pulls/20261020T092912Z_f00b82b82873/']
 archived={}
 for name in ['Long_collect_terminal_independent_delivery.json','Long_observation_delivery_independent_delivery.json','Long_legacy6_typed_bridge_delivery.json','previous_Git_delivery_independent_delivery.json','Git_delivery_independent_delivery.json']:
  for row in rd(B+'/'+name)['copies']:
   path=row['archive']['path'];assert h(R/path)==row['archive']['sha256']==row['source']['sha256'];assert (R/path).stat().st_size==row['source']['bytes'];archived[path]=ref(path)
 selected=[];excluded=[]
 for row in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split('\0'):
  if not row:continue
  status,name=row[:2],row[3:];assert status in (' M','??'),row
  accept=name in exact or any(name.startswith(p) for p in prefixes)
  if name.startswith('results/formal_main_v2/control_transport/'):
   accept=name in TRANSPORT_PINS
   if accept:assert h(R/name)==TRANSPORT_PINS[name]
  if accept:
   p=R/name;assert p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20),name
   assert p.suffix not in ('.pt','.pth','.ckpt','.bin','.safetensors','.pyc','.init','.npy','.h5','.hdf5'),name
   if p.suffix=='.npz':assert name in npzs and ref(name)=={k:npzs[name][k] for k in ['path','sha256','bytes']},name
   selected.append(name)
  else:excluded.append(name)
 assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_0927_delivery.jsonl'},excluded
 assert set(archived)<=set(selected) and all(p.relative_to(R).as_posix() in selected for p in (R/E).rglob('*') if p.is_file()),'exact audit files ignored or unlisted'
 assert set(raw_long)<=set(selected) and set(npzs)<=set(selected) and len([n for n in selected if Path(n).suffix=='.npz'])==30
 for i in range(0,len(selected),60):git('add','--',*selected[i:i+60])
 required=dict(schema='cti_nonweight_archive_stage_v1',kind='required_files',files=[ref(n) for n in sorted(selected)])
 save(B+'/git_required_files.json',required);git('add','--',B+'/git_required_files.json')
 # New raw files fit ordinary Git limits. Reuse the pinned read-only index verifier,
 # without invoking unrelated prior lossless archive restoration or fabricating a snapshot.
 g=module('ordinary_delivery0927','scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6')
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
 guard=dict(status='verified_ordinary_nonweight_Git_index',verifier_source_sha256=h(R/'scripts/ops/check_nonweight_archive_stage.py'),verifier_apis=['required_value','index_reader','same_local_index','Index.unchanged'],required_files_verified=len(required_rows),new_raw_files_verified=len(raw_long),all_index_objects_within_100MiB=True,frozen_files_verified_in_worktree_and_index=173,prior_archives_modified=False,new_archive_snapshot_claimed=False,weights_or_sealed_simulator_state_payloads_added=False,exact_development_observation_npz_files=30,exact_development_observation_npz_bytes=11839320,NPZ_allowlist=allowref,NPZ_engineering_review=ref(npz_audit_path),exact_independent_archive_files=len(archived))
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
 save(B+'/git_delivery.json',dict(schema='formal_main_v2',utc=datetime.now(timezone.utc).isoformat(),status='exact_ordinary_index_and_173frozen_verified',baseline=HEAD,required_files=ref(B+'/git_required_files.json'),index_guard=ref(B+'/git_index_guard.json'),new_raw_files=len(raw_long),immutable_audit_files=len(archived),weights_added=False,sealed_final_values_added=False,excluded_live_files=excluded,raw_original_whitespace_preserved=[ref(n) for n in exceptions],root_independent_complete=62,root_accepted_updates=314000,new_root_GPU_submissions=[],new_development_trials=0,all_development_trials=2812,current_action_trials=1600,unique_initial_states_across_eight_pairs=100,Long64_paired_mean_difference_pp=3,Long64_development_CI95_pp=[-1/3,19/3],fixed_collect_job='3047982',accepted_collect_observations=30,collection_trajectories=10,collection_GPU_seconds=472,collection_cost_not_double_counted=True,full_latency_not_inferred=True,legacy600_not_reused=True,final_sealed=True,no_normal_GPU_realtime_polling=True,additions=[ref(n) for n in additions]))
 for n in additions+[B+'/git_delivery.json']:
  git('add','--',n);assert git('show',':'+n).stdout==(R/n).read_bytes()
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines())
 answer=git('commit','-m','Accept and archive Long fixed development observations')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_0927.json',dict(commit=commit,baseline=HEAD,files=count,index_guard='passed',root_complete=62,new_development_trials=0,new_observations=30))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=commit,files=count,raw_whitespace_exceptions=len(exceptions),summary=answer.stdout.decode().splitlines()[:2])),flush=True)

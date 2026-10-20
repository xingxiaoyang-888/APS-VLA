from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,importlib.util,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1630'
E='results/formal_main_v2/engineering/supervision_delivery_0830'
HEAD='c26f739eedf80e00fb3bd36694f98140390be207'
TRANSPORT_PINS={"results/formal_main_v2/control_transport/heartbeat_0727_delivery_v2.jsonl":"aded71ae634a19b0d193a7d76aaad42196670e40fd132ef8bf4634e402b820ac","results/formal_main_v2/control_transport/heartbeat_0830_Long64_acceptance.jsonl":"02b783cd77da4fe20f1e3264b8f4ff57760dea7215610401d9b8438176b34cfc","results/formal_main_v2/control_transport/heartbeat_0830_Long64_acceptance_attempt02.jsonl":"0c8b71be77b2b9cacd7256c06897eb852dcc1edf6e518e3fa865f5375bf1965f","results/formal_main_v2/control_transport/heartbeat_0830_Long_collect_root_review.jsonl":"6258bb21ba1ad71e852bef44c647b337906e671bbed9778dbeb8746fc7d2bfe6","results/formal_main_v2/control_transport/heartbeat_0830_archive_diagnostics_collection.jsonl":"8858b687bd1d2e974876ff1685c31fc331050d31b70c5e772c4d8bc324fea8c2","results/formal_main_v2/control_transport/heartbeat_0830_archive_diagnostics_collection_attempt02.jsonl":"4d518a90ed36b675744477adfcdfca2080be772bac559581902f797efe95cf5c","results/formal_main_v2/control_transport/heartbeat_0830_authorize_Long_collect.jsonl":"d735ea23dfa36a1ae546c1168b7641df8b3b8ecdf34ddbba2a30236cf2959f79","results/formal_main_v2/control_transport/heartbeat_0830_dispatch_Long_collect.jsonl":"e3bdd8fd6dca14e58b40ebc197479f5becd281859776280ccbcdb22d271a7830","results/formal_main_v2/control_transport/heartbeat_0830_initial_observation.jsonl":"2fb7dffe94882cd87c2dda968d3a971d1fb5c94428893508c61db8accdf399ba","results/formal_main_v2/control_transport/heartbeat_0830_integration.jsonl":"ca79fdb31dd77f796f8b20d661cb232e631ca90f2c7cf1b21ddee53ff58979de","results/formal_main_v2/control_transport/heartbeat_0830_long64_root_statistics.jsonl":"56e368328eedc2e4680b6d69bc02affc927217afca0d4be59a6ba6342951e8c1","results/formal_main_v2/control_transport/heartbeat_0830_long64s41_root_review.jsonl":"3a9d456845cc01f949842d50a4993d93f5b15f9f0bd2f27730e3ed3b4144b7b7","results/formal_main_v2/control_transport/heartbeat_0830_publish_Long_collect_input.jsonl":"8f357b8a20ef9343cbdf3c1af0dd71869b8f7c3d04fa30829898f1b9f7148a87","results/formal_main_v2/control_transport/heartbeat_0830_publish_Long_collect_plans.jsonl":"439ac6fd4f4f65f3aaf09e42cd95ec6595ceb92563664a44c73eb75a39c50795","results/formal_main_v2/control_transport/heartbeat_0830_reconcile_Long_collect.jsonl":"075bf5305cbdb7e6cc95d3bd0b41493c2b5784b25f84d31b6f70604de157ccb8","results/formal_main_v2/control_transport/heartbeat_0830_terminal_pull.jsonl":"ae104463c78427c7cc291d19b92986ba599a44f8c3b6d07f3a807353a894c657","results/formal_main_v2/control_transport/independent_Long_collect_readiness_0830_fresh.jsonl":"8387527b65cae6bc293d55ffb10109dd025d058f3fca13925f7e0b4e315d8235","results/formal_main_v2/control_transport/independent_Long_collect_readiness_0830_input.jsonl":"415414fec0a7a61247da04af70c05f5c0c0a4750a90287947e4d726339313666","results/formal_main_v2/control_transport/independent_Long_collect_readiness_0830_plan.jsonl":"e94a69e375e5441bbf9f0406abf91e36735ccea245bd3cc48682b3cfbe0b92e6","results/formal_main_v2/control_transport/independent_Long_collect_readiness_0830_submission.jsonl":"fe85f78110f8be2f5858a7434faaa46f5cfe06351b05a18562eb204ae29a99a0","results/formal_main_v2/control_transport/independent_Long_collect_readiness_0830_submission_a2.jsonl":"ae4c270e25e54bd8d082323d197ff95880850eee227e5b0137ad3406b007ee46","results/formal_main_v2/control_transport/independent_Long_collect_readiness_0830_submission_a3.jsonl":"cb0c44d508d629e76e593ecae3bab0abbe8f9bc1afb356bbf28639c35497dc08","results/formal_main_v2/control_transport/independent_long64_development_0830_Long64_statistics.jsonl":"c54a0e22da356cf35653ddcddc69c06a1a04cbb49c38afe0d87ce184ec087bd8","results/formal_main_v2/control_transport/independent_long64_development_0830_Long64_statistics_attempt02.jsonl":"80838c3f2b7fbbdcca8c8e94d0be40baa417b5569b11fec89e0ef2d8663d9f8e","results/formal_main_v2/control_transport/independent_long64_development_0830_close_manifest.jsonl":"fd296bb266dd3cb4cf9c24749f3673f371e74b6dd0f1bfb4a490470a3e7fa465","results/formal_main_v2/control_transport/independent_long64_development_0830_job3047443_direct.jsonl":"c7d972e6c78d2ae4ba134f39397c7ac7760dd1be522eb2787ecc92a5a6011e4a","results/formal_main_v2/control_transport/independent_long64_development_0830_job3047443_terminal.jsonl":"f4e2f7a39dda5df6393af520735270c2447dba68acfd16108ebe25cb0660074a","results/formal_main_v2/control_transport/independent_long64_selected_diagnostics_0830_extract_a1.jsonl":"814ba7461a8992b2a98485aee83691eeaaaf99dc948b90fcc556e37d2296e0bf","results/formal_main_v2/control_transport/independent_long64_selected_diagnostics_0830_seal_a1.jsonl":"84f82ea05cbf715fca3e346cf4eddbda22b9ee8f5002044c611f0c3cbcac825f","results/formal_main_v2/control_transport/legacy6_independent_readiness_0830.jsonl":"f9057bcc55fbdaa20dbc27476de6561bf288cb1c232ce991b90cddba065a8735","results/formal_main_v2/control_transport/long_collection_prepare_0830_freeze_a1.jsonl":"546ce39bc969a4df67cb6b83aae69f6e1186011dad42a588c5b94fc2771b3e5d","results/formal_main_v2/control_transport/long_collection_prepare_0830_fresh_collect_a1.jsonl":"bfc22d377fc9d37e3f8332a4ec2cdb924b5ea910c51b337c4d0f3a7e35908bc7","results/formal_main_v2/control_transport/long_collection_prepare_0830_input_a2.jsonl":"37e8214ee3ffb6b8ddf6bb08faeb7ca4f2b18cece7f2064dd0d28dbc7c2a5023","results/formal_main_v2/control_transport/long_collection_prepare_0830_plan_a1.jsonl":"f3e0ec6f8b9ad603ca4d8ee6b9ff23ec16113685ebdc616d02ace0ccac27f16a","results/formal_main_v2/control_transport/long_collection_prepare_0830_plan_a2.jsonl":"a1e5e45d423f2b3dcabcaaaeeef14ad21bb08c43fd711a1e494ba46e72958703"}
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
c=module('delivery0830ctl','scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 state=rd('results/experiment_supervisor/state.json');f=state['formal_main_progress']
 assert state['pending_submission'] is None and f['root_and_independent_completed_arms']==62 and f['root_and_independent_reviewed_arm_updates']==314000
 assert f['completed_development_trials']==2812 and f['current_action_development_trial_count']==1600 and f['current_action_development_unique_initial_states']==100
 assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created'] and state['autonomous_training_v1']['reserved_GPU_slots']==0
 assert len([x for x in f['Long_remaining16_development_submissions'] if x['job_id']=='3047443' and x['completed_trials_accepted']==200])==1
 assert f['Long_fixed_observation_collection']['job_id']=='3047982' and f['Long_fixed_observation_collection']['accepted_observations']==0
 assert h(R/B/'summary.json')=='1d713c34ce3489056b6b36fa651d7a5d19e773b7e990822b67140ef86cb59676'
 ignore=R/'.gitignore';prior=ignore.read_text();adds=[]
 for p in sorted((R/E).rglob('*.log')):
  assert p.is_file() and not p.is_symlink();line='!/'+p.relative_to(R).as_posix()
  if line not in prior.splitlines():adds.append(line)
 if adds:ignore.write_text(prior+'\n# Exact immutable audit logs,20261020T1630.\n'+'\n'.join(adds)+'\n')
 source=B+'/root_operations/deliver_0830.py'
 with (R/source).open('xb') as stream:stream.write(Path(__file__).read_bytes())
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
 exact.add('results/formal_main_v2/invocations/libero_10_collect_648ce4233e78353e_attempt01.json');exact.add('results/formal_main_v2/submissions/3047982.json')
 raw_long={}
 for job in ['3047443']:
  exact.update(['results/formal_main_v2/job_receipts/'+job+'.json','results/formal_main_v2/downstream_reviews/'+job+'.json','results/formal_main_v2/downstream_reviews/'+job+'_independent.json'])
  exact.update('results/slurm/cti-formal-downstream_'+job+suffix for suffix in ['.out','.err'])
  files=rd('results/formal_main_v2/downstream_reviews/'+job+'.json')['files']
  for name,pin in files.items():
   assert h(R/name)==pin,name
   if name in raw_long:assert raw_long[name]==pin
   raw_long[name]=pin
 exact.update(raw_long)
 prefixes=[B+'/',E+'/','results/formal_main_v2/pulls/20261020T083316Z_3d6dba477e42/','results/formal_main_v2/downstream_gateway/e00503d5d79d397a8fc8016cb674c7d9f728c05e8229c3b3fe5e101f36e3f67b/','results/formal_main_v2/execution/long_collect_action_v1_0830/']
 archived={}
 for name in ['Long64_terminal_independent_delivery.json','Long64_selected_diagnostics_delivery.json','Long_collect_author_candidate_delivery.json','Long_collect_independent_delivery.json','Long_legacy6_provenance_independent_delivery.json','Long_collect_submission_independent_delivery.json']:
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
   assert p.suffix not in ('.pt','.pth','.ckpt','.bin','.safetensors','.pyc','.init','.npz','.npy','.h5','.hdf5'),name
   selected.append(name)
  else:excluded.append(name)
 assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_0830_delivery.jsonl'},excluded
 assert set(archived)<=set(selected) and all(p.relative_to(R).as_posix() in selected for p in (R/E).rglob('*') if p.is_file()),'exact audit files ignored or unlisted'
 assert set(raw_long)<=set(selected)
 for i in range(0,len(selected),60):git('add','--',*selected[i:i+60])
 required=dict(schema='cti_nonweight_archive_stage_v1',kind='required_files',files=[ref(n) for n in sorted(selected)])
 save(B+'/git_required_files.json',required);git('add','--',B+'/git_required_files.json')
 # New raw files fit ordinary Git limits. Reuse the pinned read-only index verifier,
 # without invoking unrelated prior lossless archive restoration or fabricating a snapshot.
 g=module('ordinary_delivery0830','scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6')
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
 save(B+'/git_delivery.json',dict(schema='formal_main_v2',utc=datetime.now(timezone.utc).isoformat(),status='exact_ordinary_index_and_173frozen_verified',baseline=HEAD,required_files=ref(B+'/git_required_files.json'),index_guard=ref(B+'/git_index_guard.json'),new_raw_files=len(raw_long),immutable_audit_files=len(archived),weights_added=False,sealed_final_values_added=False,excluded_live_files=excluded,raw_original_whitespace_preserved=[ref(n) for n in exceptions],root_independent_complete=62,root_accepted_updates=314000,new_root_GPU_submissions=['3047982'],exact_pending_reconciled_without_resubmission=True,new_development_trials=200,all_development_trials=2812,current_action_trials=1600,unique_initial_states_across_eight_pairs=100,Long64_paired_mean_difference_pp=3,Long64_development_CI95_pp=[-1/3,19/3],fixed_collect_job='3047982',accepted_collect_observations=0,legacy600_not_reused=True,final_sealed=True,no_normal_GPU_realtime_polling=True,additions=[ref(n) for n in additions]))
 for n in additions+[B+'/git_delivery.json']:
  git('add','--',n);assert git('show',':'+n).stdout==(R/n).read_bytes()
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines())
 answer=git('commit','-m','Accept Long64 three-seed development and preregister fixed observations')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_0830.json',dict(commit=commit,baseline=HEAD,files=count,index_guard='passed',root_complete=62,new_development_trials=200))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=commit,files=count,raw_whitespace_exceptions=len(exceptions),summary=answer.stdout.decode().splitlines()[:2])),flush=True)

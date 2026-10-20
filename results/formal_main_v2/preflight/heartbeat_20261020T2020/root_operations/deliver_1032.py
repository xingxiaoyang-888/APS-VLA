from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,importlib.util,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1832';E='results/formal_main_v2/engineering/supervision_delivery_1032'
HEAD='908ecc34488bc02d112d60490ff7f6d5770bd584'
TRANSPORT_PINS={"results/formal_main_v2/control_transport/Long_legacy6_consumer_1032_CPU_v2.jsonl":"34a99614f35694c5bc8d3ce3d9b26be59bd3e4485bb2515e09d53b8a1535ea94","results/formal_main_v2/control_transport/Long_legacy6_consumer_1032_CPU_v3.jsonl":"9e089447e3045e78658493f979c9744d6b047dd89359fbabf7f9711428f4c144","results/formal_main_v2/control_transport/Long_legacy6_consumer_1032_seal_v1.jsonl":"c0c1d917e414bc25afaf19c5d6c301776b42ef3e43351c3a9e36b62758a3f7e8","results/formal_main_v2/control_transport/Spatial64seed23_terminal_1032_a1.jsonl":"b042a8d1a9422a7cad2d4f325c7ab9aafc3dddca8582dc4515c6abeab64cc2bc","results/formal_main_v2/control_transport/Spatial64seed23_terminal_1032_archive_a1.jsonl":"986bdfedf8eaf43dc9b321d6d3d945e24248a4c0cca3d4b62d1e0869169dca61","results/formal_main_v2/control_transport/Spatial64seed23_terminal_1032_seal_v2.jsonl":"80a2983138ba081876f170e7763991ba3c3e80d19b0b2b9a507074e9edf5da93","results/formal_main_v2/control_transport/heartbeat_1032_Long22_statistics.jsonl":"27745ba2cda8058033d077eb9cd10a6a3537153a179cb89b0faa77fee181b98a","results/formal_main_v2/control_transport/heartbeat_1032_archive_Spatial3044479.jsonl":"384a280361ab7d1a2aeb6771260c9de836b07ece852b547813a1575a13f7a17d","results/formal_main_v2/control_transport/heartbeat_1032_archive_evidence.jsonl":"6bcdb1e62eaac1f82777c534409a55ed4dfed6e34a17605582e6597a191dcdbc","results/formal_main_v2/control_transport/heartbeat_1032_gateway_check_Spatial128seed23.jsonl":"4fb2d665758db3778ce326d394c0258af146f28d37d54f7c2e3e6827814d7d76","results/formal_main_v2/control_transport/heartbeat_1032_gateway_submit_Goal128seed17refs.jsonl":"81890b15bd1f61a3f08f91cece617b3f46e9e121b0a2e421839368a209f4cf90","results/formal_main_v2/control_transport/heartbeat_1032_gateway_submit_Object128seed23.jsonl":"5dd99a15367477441b56d3d460fad3a6bbefddc39d897f8328a3ae4f161803a9","results/formal_main_v2/control_transport/heartbeat_1032_gateway_submit_Spatial128seed23.jsonl":"4b6ad9b49be54c3ffbe60d312fd93fa10d542bd9c84a6853db8c92faabce7cb2","results/formal_main_v2/control_transport/heartbeat_1032_initial_observation.jsonl":"5c1e982a47ed632a67cd51e53c3e82f028e0cff92010286c9b342dbcfbbf36c5","results/formal_main_v2/control_transport/heartbeat_1032_integration.jsonl":"c8d04d52ffcde6eca612a5f5281d17ec3c3301fe3a22a1cf533871fb253a032e","results/formal_main_v2/control_transport/heartbeat_1032_legacy600_adoption.jsonl":"3e93232c57a886a866483426e0b32a74476b4c9a3ed9f2e64df9fdf3b4167284","results/formal_main_v2/control_transport/heartbeat_1032_nonLong_audit_archives.jsonl":"b292f8c1e35a9e8faec7dc8a1edcf82a4ad2fc1e76b41adbcf1c8907973c0c1a","results/formal_main_v2/control_transport/heartbeat_1032_nonLong_existing_runtime_dependencies.jsonl":"a8f06547fbc61715b520896e9b51b7e08386b2b74f7f86f35f647b4a4626fa54","results/formal_main_v2/control_transport/heartbeat_1032_nonLong_manifest_publication.jsonl":"c3e297ff418064d4c48ff3a1eeda4132995ab4884472221e3a7052148ecbc71e","results/formal_main_v2/control_transport/heartbeat_1032_nonLong_root_readiness.jsonl":"9fea2a84dd9659749a579ad48d03b1814334eaca0a605039756156c2b8ff722a","results/formal_main_v2/control_transport/heartbeat_1032_nonLong_static_plans.jsonl":"6c31458b480004ac5334386788f3b797ed447cc59454eb92b0dacd4d7b3cc46e","results/formal_main_v2/control_transport/heartbeat_1032_nonLong_training_configs.jsonl":"68b6dd2c902c34324667311a31f2f324b885d000a2e099ecb85df87a41f833d3","results/formal_main_v2/control_transport/heartbeat_1032_post_dispatch.jsonl":"fe80030223c09b1bb4619ba4c21f661a66d9576b227d45dfccc071025716a300","results/formal_main_v2/control_transport/heartbeat_1032_pull_Spatial3044479.jsonl":"11aa25297ebd68ff8b50936de6eed786d08dddab06c5f22fa6d7813b6d86d382","results/formal_main_v2/control_transport/heartbeat_1032_reconcile_Goal3048609.jsonl":"7e2923f1ba8ac2b5e0faafd54eb17f809fa1b6f0bb012206d66780cf865b11bf","results/formal_main_v2/control_transport/heartbeat_1032_reconcile_Object3048581.jsonl":"05c4a5e5ff1f5a2d17a7725711811c31cd9bea2ed721c09736c4d2bea4d28603","results/formal_main_v2/control_transport/heartbeat_1032_reconcile_Spatial3048572.jsonl":"4a2096173137126f7bff1d4bc7d03b20fec647d289c3cf2c8a62cc6fbe240485","results/formal_main_v2/control_transport/heartbeat_1032_reserve_Goal128seed17refs.jsonl":"9b5da2ccebda39a77cf9fc3a9afdf18084c8608425432ed812a762df21829de5","results/formal_main_v2/control_transport/heartbeat_1032_reserve_Object128seed23.jsonl":"04f90076a28f7f6ebf81a7590025ce73124051bebd83fade63efd40ff4738f17","results/formal_main_v2/control_transport/heartbeat_1032_reserve_Spatial128seed23.jsonl":"82429770d2f08562e8db3aea963c2141dc58e192826f14657620425d45117840","results/formal_main_v2/control_transport/heartbeat_1032_review_Spatial3044479.jsonl":"85f4edeac01764b7a26524db07a88da4ce8702159699452eea9421165c3689ed","results/formal_main_v2/control_transport/heartbeat_1032_runtime_inode_evidence.jsonl":"44d91d81d4238733d2c802c246d27c705e98199bdd4a36150158f1c00b1d88ec","results/formal_main_v2/control_transport/independent_Long22_statistics_1032_a1.jsonl":"519c2e6101be81dfcd5b5499450b6fe7c712cee7f1e2b90a8c572b5ae52b1472","results/formal_main_v2/control_transport/independent_Long_legacy6_admission_1032_a1.jsonl":"a6d49adcc92766b16e2a4f4950e488d5861d75b793b81f683cb83db23f2262a5","results/formal_main_v2/control_transport/independent_Long_legacy6_admission_1032_typed_a1.jsonl":"6e0b2a2597f4533405b8dca72d2272f85979f88a7db874425f6f37aab0680f2f","results/formal_main_v2/control_transport/independent_Long_legacy6_consumer_1032_a1.jsonl":"ac2fe55b20256124862882ece38330e532658ee11ad8cf756782f4e1693548e4","results/formal_main_v2/control_transport/independent_nonLong_development_plans_1032_a1.jsonl":"51a2328978502fb76e5c10272de80f2509b6f9eed1820a42a36efbeea5c9f2f7","results/formal_main_v2/control_transport/independent_nonLong_development_plans_1032_post_a1.jsonl":"12dc99767996d3f44b6980110cd0c446f9ae36cdc7fc01c45c0aecf7a53a4260","results/formal_main_v2/control_transport/independent_nonLong_development_plans_1032_post_a2.jsonl":"5bdf58f24842465094c418e67c3571376c1bfd5bb11332439b1189d4241a15d0","results/formal_main_v2/control_transport/independent_nonLong_submission_1032_a1.jsonl":"3248568cc2bd747f7f4c4a95fb210063d1463eec945524d2f1e73044d99f476f","results/formal_main_v2/control_transport/nonLong_development_plans_1032_dependency_preview_v1.jsonl":"e326b3ff8cb7a7e8be9aa461c13e691589ad019112e973c6ac5fe72037c7c9ed","results/formal_main_v2/control_transport/nonLong_development_plans_1032_goal_manifest_v1.jsonl":"bd59e85bd880fd2aca90f71f0fe347fb5e03d913e93d4d4a741475988487169f","results/formal_main_v2/control_transport/nonLong_development_plans_1032_object_manifest_v1.jsonl":"21d35d0d0e3636c1553a3a4e1c9e88097ab84a1fdb302fca7a3ddbd53c80bf4f","results/formal_main_v2/control_transport/nonLong_development_plans_1032_prepare_v1.jsonl":"b42eec6471c79a603ab60ebe452a7a8791e86be7a4d1ede783994e093723a440","results/formal_main_v2/control_transport/nonLong_development_plans_1032_prepare_v2.jsonl":"542a90e208c5f6fd0962d4bfe11b0eb11af7e39edb5b942db4adce4197e1c5b3","results/formal_main_v2/control_transport/nonLong_development_plans_1032_seal_v1.jsonl":"1485ca9afa56ba3b1198369bd4e8eae394ffeead81e6029430895559d0bf62fc","results/formal_main_v2/control_transport/nonLong_development_plans_1032_spatial_manifest_v1.jsonl":"6c1a6d402dd55d8cc1bac4966f542e02258004473ae74b03102d37d311e94c95","results/formal_main_v2/control_transport/nonLong_development_readiness_1032_v2.jsonl":"c13fab24c4af21dfbcc12b224c204fec5aa5b4c78d3f4b93bb4a2f50e1657c05","results/formal_main_v2/control_transport/nonLong_development_readiness_1032_v3.jsonl":"23d0fb3f4b35a5c6674eea1f491cd132eb9f497cd6121c8f7a35199bcfde32fe","results/formal_main_v2/control_transport/heartbeat_0927_delivery.jsonl":"06a3104095f1d67d5dec624d8b254bca091d2bac2c88f32b499110cd20fe2e87"}
SUMMARY_SHA='06c3937e0a974c8a8e12bf33d7a862021d4e587c393ceab2f89342ab36393266'
EXTRA_EXACT=["results/formal_main_v2/invocations/libero_goal_development_8c843c1d4ee8383c_attempt01.json","results/formal_main_v2/invocations/libero_object_development_ea4e52de3babd049_attempt01.json","results/formal_main_v2/invocations/libero_spatial_development_ea4e52de3babd049_attempt01.json","results/formal_main_v2/submissions/3048572.json","results/formal_main_v2/submissions/3048581.json","results/formal_main_v2/submissions/3048609.json","results/formal_main_v2/job_receipts/3044479.json","results/slurm/cti-formal_3044479.err","results/slurm/cti-formal_3044479.out"]
EXTRA_PREFIXES=["results/formal_main_v2/execution/nonLong_action_v1_1032/","results/formal_main_v2/libero_spatial/k64/seed23/training/","results/formal_main_v2/pulls/20261020T113838Z_c5823055f27a/","results/formal_main_v2/nonweight_archives/v1/","results/formal_main_v2/downstream_gateway/4a47032c83c03e81ac1297aa4c3f4ff31fc780a700990e7cb335c89cf65dbab4/","results/formal_main_v2/downstream_gateway/9ee17e773f283ff81ca70e25ed0ab8afac7abf5ce5de73ef81625db768b0509b/","results/formal_main_v2/downstream_gateway/a686142e3af91491d83444270b51b2fbac1f95e7a0f95fd7a0f64f4fa374e89f/"]
RAW_PATHS=["results/formal_main_v2/libero_spatial/k64/seed23/training/A/attempts/20261020T024503_c9ee4745aae4/cost_events.jsonl","results/formal_main_v2/libero_spatial/k64/seed23/training/B/attempts/20261020T065405_8ceb2852a65d/cost_events.jsonl","results/formal_main_v2/libero_spatial/k64/seed23/training/cache_events/3044479_bb4f14dfaf38.jsonl"]
SNAPSHOT='results/formal_main_v2/nonweight_archives/v1/snapshots/Spatial64seed23_20261020_1032.json'
SNAPSHOT_SHA='46d99a0368858d1301310a890380873331a65f3f21ac4011605b00b41c06d9c4'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel):return json.loads((R/rel).read_bytes())
def ref(rel):return dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
def module(name,rel,pin):
 p=R/rel;assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m
c=module('delivery1032ctl','scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 state=rd('results/experiment_supervisor/state.json');f=state['formal_main_progress']
 assert state['pending_submission'] is None and f['root_and_independent_completed_arms']==64
 assert f['completed_development_trials']==2812 and f['current_action_development_trial_count']==1600
 assert f['Long22_development_statistics']['total_trials']==2200 and f['Long22_development_statistics']['explicit_legacy_equivalent_trials']==600
 assert f['Long_legacy6_equivalence_followup']['original600_reused'] and not f['Long_legacy6_equivalence_followup']['original600_rerun']
 assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert h(R/B/'summary_after_dispatch.json')==SUMMARY_SHA
 assert state['last_root_supervision_snapshot']==dict(path=B+'/summary_after_dispatch.json',sha256=SUMMARY_SHA)
 p=R/B/'root_operations/deliver_1032.py'
 with p.open('xb') as stream:stream.write(Path(__file__).read_bytes())
 ignore=R/'.gitignore';prior=ignore.read_text();adds=[]
 for raw_name in RAW_PATHS:
  line='/'+raw_name
  assert not git('ls-files','--',raw_name).stdout
  if line not in prior.splitlines():adds.append(line)
 for p in sorted((R/E).rglob('*.log')):
  line='!/'+p.relative_to(R).as_posix()
  if line not in prior.splitlines():adds.append(line)
 if adds:ignore.write_text(prior+'\n# Exact immutable audit logs,20261020T1832.\n'+'\n'.join(adds)+'\n')
 for name,pin in TRANSPORT_PINS.items():
  assert h(R/name)==pin and json.loads((R/name).read_bytes().splitlines()[-1])['event']=='control_end'
 exact={'.gitignore','results/experiment_supervisor/state.json'}|set(EXTRA_EXACT)
 event_dir='results/formal_main_v2/autonomous_training/run_v1/events';index=rd(event_dir+'/index.json')
 assert index['version']==1 and index['active']=='events.000001.jsonl' and len(index['sealed'])==1
 sealed=index['sealed'][0];assert sealed['path']=='events.000000.jsonl'
 assert h(R/event_dir/sealed['path'])==sealed['sha256'] and (R/event_dir/sealed['path']).stat().st_size==sealed['bytes']
 with (R/event_dir/index['active']).open() as stream:first=json.loads(next(stream))
 assert first['sequence']==sealed['last_sequence']+1 and first['previous_event_sha256']==sealed['last_event_sha256']
 exact.update([event_dir+'/index.json',event_dir+'/'+index['active'],event_dir+'/'+sealed['path']])
 exact.update('docs/'+name+'.md' for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式Long完整开发结果'])
 archived={}
 pull=rd('results/formal_main_v2/pulls/20261020T113838Z_c5823055f27a/receipt.json')
 assert h(R/'results/formal_main_v2/pulls/20261020T113838Z_c5823055f27a/receipt.json')=='a39164a76e708535cdf6cb02cd549e6c83c65ebfe76e7392012a64fa00ca9b01'
 original_pull_files={x['relative']:dict(path=x['relative'],sha256=x['sha256'],bytes=x['bytes']) for x in pull['files']}
 for p in sorted((R/B).glob('*_delivery.json')):
  package=rd(p.relative_to(R).as_posix())
  if 'copies' not in package:continue
  for row in package['copies']:
   name=row['archive']['path'];assert h(R/name)==row['archive']['sha256']==row['source']['sha256']
   assert (R/name).stat().st_size==row['source']['bytes'];archived[name]=ref(name)
 selected=[];excluded=[]
 for row in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split('\0'):
  if not row:continue
  status,name=row[:2],row[3:];assert status in (' M','??'),row
  accept=name in exact or name.startswith(B+'/') or name.startswith(E+'/') or any(name.startswith(prefix) for prefix in EXTRA_PREFIXES)
  if name.startswith('results/formal_main_v2/control_transport/'):accept=name in TRANSPORT_PINS
  if name in RAW_PATHS:raise AssertionError('explicit raw ignore did not apply: '+name)
  if accept:
   p=R/name;assert p.is_file() and not p.is_symlink() and p.stat().st_size<100*(1<<20)
   assert p.suffix not in ('.pt','.pth','.ckpt','.bin','.safetensors','.pyc','.init','.npz','.npy','.h5','.hdf5')
   selected.append(name)
  else:excluded.append(name)
 assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_1032_delivery.jsonl'},excluded
 assert set(archived)<=set(selected)
 assert all(p.relative_to(R).as_posix() in selected for p in (R/E).rglob('*') if p.is_file()),'immutable archive ignored or missing'
 for i in range(0,len(selected),60):git('add','--',*selected[i:i+60])
 required=dict(schema='cti_nonweight_archive_stage_v1',kind='required_files',files=[ref(n) for n in sorted(selected)])
 save(B+'/git_required_files.json',required);git('add','--',B+'/git_required_files.json')
 g=module('delivery1032index','scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6')
 codec=g.load_codec();required_rows=g.required_value(required,codec)
 with g.index_reader(R) as idx:
  data,iv=g.same_local_index(idx,g.INVENTORY,codec);assert iv['sha256']==g.INVENTORY_SHA256
  inventory=json.loads(data);assert len(inventory['files'])==173
  for name,pin in inventory['files'].items():
   assert name not in idx.changed
   _,q=g.same_local_index(idx,name,codec);assert q['sha256']==pin
  assert set(idx.changed)==set(selected)|{B+'/git_required_files.json'} and all(x in ['A','M'] for x in idx.changed.values())
  for row in required_rows:g.same_local_index(idx,row['path'],codec,expected=row)
  g.same_local_index(idx,B+'/git_required_files.json',codec,expected=ref(B+'/git_required_files.json'))
  for name,row in archived.items():g.same_local_index(idx,name,codec,expected=row)
  idx.unchanged()
 result=g.check(R,SNAPSHOT,SNAPSHOT_SHA,RAW_PATHS,B+'/git_required_files.json')
 assert result['status']=='verified_index_archive_delivery' and result['frozen_files_verified_in_worktree_and_index']==173
 save(B+'/git_index_guard.json',result)
 diag=git('diff','--cached','--check',check=False)
 save(B+'/git_whitespace_diagnostic.json',dict(returncode=diag.returncode,stdout=diag.stdout.decode(),stderr=diag.stderr.decode()))
 exceptions=[]
 if diag.returncode:
  headers=[line for line in diag.stdout.decode().splitlines() if re.match(r'^.*?:[0-9]+: ',line)]
  assert headers and not diag.stderr
  for header in headers:
   match=re.fullmatch(r'(.*?):[0-9]+: (trailing whitespace|new blank line at EOF)\.',header);assert match,header
   name=match.group(1);assert name in archived or name in original_pull_files,name
   if name in original_pull_files:assert ref(name)==original_pull_files[name]
   exceptions.append(name)
  exceptions=sorted(set(exceptions))
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 save(B+'/git_delivery.json',dict(schema='formal_main_v2',utc=datetime.now(timezone.utc).isoformat(),status='exact_ordinary_index_and_173frozen_verified',
  baseline=HEAD,required_files=ref(B+'/git_required_files.json'),index_guard=ref(B+'/git_index_guard.json'),immutable_archive_files=len(archived),
  weights_added=False,sealed_final_values_added=False,excluded_live_files=excluded,raw_original_whitespace_preserved=[ref(n) for n in exceptions],
  root_independent_complete=64,new_root_GPU_submissions=['3048572','3048581','3048609'],new_development_trials_accepted=0,active_runs_not_terminally_collected=True,
  Long_compatible_development_trials=2200,current_wrapper_actual_trials=1600,legacy_equivalent_trials=600,unique_initial_states=100,
  old_GPU_cost_not_added_again=True,all_historical_results_preserved=True,global_consumer_not_modified=True,final_sealed=True,no_normal_GPU_realtime_polling=True))
 for n in [B+'/git_index_guard.json',B+'/git_whitespace_diagnostic.json',B+'/git_delivery.json']:
  git('add','--',n);assert git('show',':'+n).stdout==(R/n).read_bytes()
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines())
 result=git('commit','-m','Accept Spatial training and Long development; launch three nonLong batches')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_1032.json',dict(commit=commit,baseline=HEAD,files=count,index_guard='passed',root_complete=64,Long_compatible_development_trials=2200))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=commit,files=count,raw_whitespace_exceptions=len(exceptions),summary=result.stdout.decode().splitlines()[:2])),flush=True)

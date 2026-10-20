from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,importlib.util,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T2020';E='results/formal_main_v2/engineering/supervision_delivery_1220'
HEAD='f14596305af9b875fb97d87183cd1e747d90f027'
TRANSPORT_PINS={"results/formal_main_v2/control_transport/heartbeat_1032_delivery.jsonl":"72844a97853170546d1fa66e58f84ad26713ef79ea65178938acf97def811267","results/formal_main_v2/control_transport/heartbeat_1220_existing_training_configs.jsonl":"d3002ce505800f0f2d0e56eee8e07daf9dbf9b1e19670f503fabc0cfd04e553e","results/formal_main_v2/control_transport/heartbeat_1220_final_independent_archives.jsonl":"b864fdfde8d531d35edc789e6be5276d7a012535507e5145ad62153770690857","results/formal_main_v2/control_transport/heartbeat_1220_gateway_submit_Goal128seed23.jsonl":"84c253869357c54987782cb606980145c5e8d73bcfba6a59843e3861dc7a0fc9","results/formal_main_v2/control_transport/heartbeat_1220_gateway_submit_Goal128seed23_a2.jsonl":"d52ffb4fc9861190afec618406253cb9dcb33d44c07e962c74da70e2ce83c043","results/formal_main_v2/control_transport/heartbeat_1220_gateway_submit_Object128seed41.jsonl":"0a537230912d68a7cd86c707f15090539c860319641ae9543182a24f09614074","results/formal_main_v2/control_transport/heartbeat_1220_gateway_submit_Object128seed41_a2.jsonl":"99aa6620324c9caaae65121ed697097c8250c8cc8f72061182f3a1a8993456cd","results/formal_main_v2/control_transport/heartbeat_1220_gateway_submit_Spatial128seed41.jsonl":"dba66f259e19207b9fadb4cdf43ff66ac5a66f7cbd5dd1b7ff475bc7edce26d5","results/formal_main_v2/control_transport/heartbeat_1220_initial_observation.jsonl":"4416ae8539245edce863c0a45194634286afe204b8f9199ad9ef597fd02725c5","results/formal_main_v2/control_transport/heartbeat_1220_integration_independent_archive.jsonl":"d95bc194c63b495cc51bc0c35a88ea9e3e29cbd9fe3a60ed1939a0ff29d80863","results/formal_main_v2/control_transport/heartbeat_1220_integration_v2.jsonl":"1fbcf25334f7a34ed1fd0bc0306263136348759afc5a143f57b3678da4820ea9","results/formal_main_v2/control_transport/heartbeat_1220_nonLong_manifests.jsonl":"ddd387fe07c45de1f4cbc2eca3181a3bd1bad968473570674cf671382a1d244e","results/formal_main_v2/control_transport/heartbeat_1220_plan_independent_archive.jsonl":"9ae28f18fd73e9ee609b9a370cdb17ab5df823d2ea6f0b3f2e85737d3d357162","results/formal_main_v2/control_transport/heartbeat_1220_postdispatch_state_snapshot.jsonl":"af3e29ec5ff3ec7222c0b7ddacbd88d8d8a531b675337a685b5aad09a0a94635","results/formal_main_v2/control_transport/heartbeat_1220_previous_Git_delivery.jsonl":"3e014f51c12e2a81951934560eee3bfd857853a0758a2d5761f8429b099f12fc","results/formal_main_v2/control_transport/heartbeat_1220_reconcile_Goal3049191.jsonl":"ecad37aff2bf892fce70fa532d5fe429804481204150e4358e6082467d50114e","results/formal_main_v2/control_transport/heartbeat_1220_reconcile_Object3049172.jsonl":"2aa2b71dbb6594520137bb3e7600eceef14bf800003105f3a2b1f9b152907c77","results/formal_main_v2/control_transport/heartbeat_1220_reconcile_Spatial3049132.jsonl":"b0924034038f4e3957f71c22363d53ef781300bbf5013b35aefdb1db903c4ea8","results/formal_main_v2/control_transport/heartbeat_1220_reserve_Goal128seed23.jsonl":"cb67ebe4ed9201bc0622e97fd1d7a371f93d348a0791258adb21af82e63925bd","results/formal_main_v2/control_transport/heartbeat_1220_reserve_Object128seed41.jsonl":"8a8efb4d9292894ca19661a4959d5d4dcc82112127c63b66927122ad10f3a56d","results/formal_main_v2/control_transport/heartbeat_1220_reserve_Spatial128seed41.jsonl":"fb71d55edf63b8bd8cb3071cf9f431ed03a54486ecb9cf275ff6627a7888f697","results/formal_main_v2/control_transport/heartbeat_1220_root_readiness.jsonl":"c616ed707979fc98ea1f4285c88d9c1cf09a0caf75964a0eb8aaa7d772e5fbb7","results/formal_main_v2/control_transport/heartbeat_1220_state_snapshot.jsonl":"91bf011edd4ae7c4512fbec94d96ca58a2a3689fc56b4b1c063eb819347a615e","results/formal_main_v2/control_transport/heartbeat_1220_static_plan_publication.jsonl":"9b9b3da8c21b8de72592c73bbd5c1d35ccb7860b1f40d207d6b118378b573652","results/formal_main_v2/control_transport/heartbeat_1220_terminal_independent_archive.jsonl":"af4fb4f64abd26147e668d68b5228b4bbbcec767a351e750206b8a3f70ad833b","results/formal_main_v2/control_transport/heartbeat_1220_terminal_pull.jsonl":"3cdc768f80dcf2a774bf2adcad95af339ca8a4dbfeb763cbcfacba117f748fa1","results/formal_main_v2/control_transport/heartbeat_1220_terminal_reviews.jsonl":"c73dbe6fb227a9996ef24f625ec34d18c76d99487ceb90b2f2f4e54346250560","results/formal_main_v2/control_transport/independent_final_delivery_1032_a1.jsonl":"bb9ad93aa8dd6371fe0a1417154e33a403455f265a8ab2a4cde5191eaf2e3701","results/formal_main_v2/control_transport/independent_final_delivery_1032_a2.jsonl":"ed5a6259d9083913a59ff2a6340e07be06df64dcd3544c305ef223835920fe14","results/formal_main_v2/control_transport/independent_nonLong_integration_1220.jsonl":"699ab335e5ad8635e1ba9f48f9857a5d7db4a1405b60389ea4070bccb7ba02ba","results/formal_main_v2/control_transport/independent_nonLong_submission_1220_a1.jsonl":"e8d9287f87d2413e8a851a501afbbcc337e03284792e3c7da9dba5185d165063","results/formal_main_v2/control_transport/independent_nonLong_terminal_1220_a1.jsonl":"8afeaac065490375c6b341a97a0180c0774617dff5b29447a4f8043d43ae6c20","results/formal_main_v2/control_transport/independent_nonLong_terminal_1220_a2.jsonl":"ad5fbd9eeb27e9ca8e5f79db4b7ea18edc6f5d01f5dcb88304bb621f398830b3","results/formal_main_v2/control_transport/nonLong_development_independent_1220_inputs_a1.jsonl":"1a8211caf8db6d4f1c512e9dc51de50a88a645a5118d21277bdc5500e9b7ba75","results/formal_main_v2/control_transport/nonLong_development_independent_1220_inputs_a2.jsonl":"ed13717e211bc2d4d766f74fed413543261de1d716954efbc22d61d274200a4b","results/formal_main_v2/control_transport/nonLong_development_independent_1220_plans_a1.jsonl":"cf3f1efaacb8cd7cb1ce671aff6a4d87a1c796d45382adea97cdb0f325079b22","results/formal_main_v2/control_transport/nonLong_development_independent_1220_plans_a2.jsonl":"370b23e3bc8eae3c73ac02b01f7fe06a6cdc2343ec9e9de70c2399b93584143a","results/formal_main_v2/control_transport/nonLong_development_independent_1220_post_a2.jsonl":"24a91b6ed119c2d5a75a7ba0dd277254c5d0f9feaf074e4eca60d8ab697554f7","results/formal_main_v2/control_transport/nonLong_development_independent_1220_seal_v1.jsonl":"c8217314e6470e7aa13e256dc52a54bd0df2af78a13dacc1a683a6a1e275b5a9","results/formal_main_v2/control_transport/nonLong_development_plans_1220_dependency_preview_a1.jsonl":"ab588ef648b69c8e4f7d81850eb3752f1d1a85002b1bb9500ba5a8b552b86e31","results/formal_main_v2/control_transport/nonLong_development_plans_1220_manifests_a1.jsonl":"944ef728850f0d0e7d602da4cd91b597eb53a1c4271388e2ba7342963851d59e","results/formal_main_v2/control_transport/nonLong_development_plans_1220_prepare_a1.jsonl":"8db4c8ec2a12c19bea58f916aafe6a16e2bfb24b6fdda23b32583176c8fef36b","results/formal_main_v2/control_transport/nonLong_development_plans_1220_seal_a1.jsonl":"fdb29a3ddb0127f26777095749991a50b7785a357afb0b613cd50c2c64a122bc"}
SUMMARY_SHA='b6faae7369781c6a6818f49038c31832655065c2c96c42c22f17a11f77f3d865'
EXTRA_EXACT=["results/formal_main_v2/job_receipts/3048572.json","results/formal_main_v2/job_receipts/3048581.json","results/formal_main_v2/libero_object/downstream/development/ea4e52de3babd049/attempt01/action_execution/3048581/completion.json","results/formal_main_v2/libero_object/downstream/development/ea4e52de3babd049/attempt01/action_execution/3048581/events.jsonl","results/formal_main_v2/libero_object/downstream/development/ea4e52de3babd049/attempt01/action_execution/3048581/identity.json","results/formal_main_v2/libero_object/downstream/development/ea4e52de3babd049/attempt01/adapter_invocations/3048581_0a421d14df7c4b63951167c03ae69a65.json","results/formal_main_v2/libero_object/downstream/development/ea4e52de3babd049/attempt01/adapter_invocations/3048581_0a421d14df7c4b63951167c03ae69a65.jsonl","results/formal_main_v2/libero_object/downstream/development/ea4e52de3babd049/attempt01/closed_loop_report.json","results/formal_main_v2/libero_object/downstream/development/ea4e52de3babd049/attempt01/config.json","results/formal_main_v2/libero_object/downstream/development/ea4e52de3babd049/attempt01/panel.json","results/formal_main_v2/libero_object/downstream/development/ea4e52de3babd049/attempt01/trials.jsonl","results/formal_main_v2/libero_spatial/downstream/development/ea4e52de3babd049/attempt01/action_execution/3048572/completion.json","results/formal_main_v2/libero_spatial/downstream/development/ea4e52de3babd049/attempt01/action_execution/3048572/events.jsonl","results/formal_main_v2/libero_spatial/downstream/development/ea4e52de3babd049/attempt01/action_execution/3048572/identity.json","results/formal_main_v2/libero_spatial/downstream/development/ea4e52de3babd049/attempt01/adapter_invocations/3048572_b610e84c8f1545c5b289d3e87c3d0c14.json","results/formal_main_v2/libero_spatial/downstream/development/ea4e52de3babd049/attempt01/adapter_invocations/3048572_b610e84c8f1545c5b289d3e87c3d0c14.jsonl","results/formal_main_v2/libero_spatial/downstream/development/ea4e52de3babd049/attempt01/closed_loop_report.json","results/formal_main_v2/libero_spatial/downstream/development/ea4e52de3babd049/attempt01/config.json","results/formal_main_v2/libero_spatial/downstream/development/ea4e52de3babd049/attempt01/panel.json","results/formal_main_v2/libero_spatial/downstream/development/ea4e52de3babd049/attempt01/trials.jsonl","results/slurm/cti-formal-downstream_3048572.err","results/slurm/cti-formal-downstream_3048572.out","results/slurm/cti-formal-downstream_3048581.err","results/slurm/cti-formal-downstream_3048581.out","results/formal_main_v2/downstream_reviews/3048572.json","results/formal_main_v2/downstream_reviews/3048581.json","results/formal_main_v2/downstream_reviews/nonLong_seed23_1220_independent.json","results/formal_main_v2/submissions/3049132.json","results/formal_main_v2/submissions/3049172.json","results/formal_main_v2/submissions/3049191.json","results/formal_main_v2/invocations/libero_spatial_development_428eafaeb10a5ce3_attempt01.json","results/formal_main_v2/invocations/libero_object_development_428eafaeb10a5ce3_attempt01.json","results/formal_main_v2/invocations/libero_goal_development_ea4e52de3babd049_attempt01.json"]
EXTRA_PREFIXES=["results/formal_main_v2/execution/nonLong_action_v1_1220/","results/formal_main_v2/pulls/20261020T122634Z_f16248744f18/","results/formal_main_v2/downstream_gateway/c657885d23b4b7741a3b99227f3c12dcda492c4c0fd2ae1d0d9dbfc928b2dc60/","results/formal_main_v2/downstream_gateway/3c3531e1d721dd357c5df0db7582334b5b45748ff1b0034f3685ed23ae8d7f8a/","results/formal_main_v2/downstream_gateway/efcfa42b97d4d780999f344f8024ff369d5f466825b25d7119ad0c118cbfa117/"]
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
c=module('delivery1220ctl','scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 state=rd('results/experiment_supervisor/state.json');f=state['formal_main_progress']
 assert state['pending_submission'] is None and f['root_and_independent_completed_arms']==64
 assert f['completed_development_trials']==3212 and f['current_action_development_trial_count']==2000
 assert f['Long22_development_statistics']['total_trials']==2200 and f['Long22_development_statistics']['explicit_legacy_equivalent_trials']==600
 assert f['Long_legacy6_equivalence_followup']['original600_reused'] and not f['Long_legacy6_equivalence_followup']['original600_rerun']
 assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert h(R/B/'summary_after_dispatch.json')==SUMMARY_SHA
 assert state['last_root_supervision_snapshot']==dict(path=B+'/summary_after_dispatch.json',sha256=SUMMARY_SHA)
 # Retain exact root one-off implementations bound by the transport audit.
 root_sources={}
 for name,pin in TRANSPORT_PINS.items():
  assert h(R/name)==pin
  lines=[json.loads(x) for x in (R/name).read_bytes().splitlines()]
  assert lines[0]['event']=='control_start' and lines[-1]['event']=='control_end'
  entry=lines[0].get('entrypoint','');parts=Path(entry).parts
  if len(parts)==2 and parts[0]=='.local':
   original=R/entry;expected=lines[0]['entrypoint_sha256'];assert h(original)==expected
   dst=R/B/'root_operations'/original.name
   if dst.exists():assert h(dst)==expected
   else:dst.write_bytes(original.read_bytes())
   root_sources[dst.relative_to(R).as_posix()]=dict(original=entry,sha256=expected)
 # This reviewed draft was not executed; preserve it with its precise provenance.
 original=R/'.local/integrate_1220.py';assert h(original)=='0bb111709a3ce5cc780a81e49963ea17b4445791f0315b1f49116865c4bb08c7'
 dst=R/B/'root_operations/integrate_1220_reviewed_draft.py'
 if dst.exists():assert h(dst)==h(original)
 else:dst.write_bytes(original.read_bytes())
 root_sources[dst.relative_to(R).as_posix()]=dict(original='.local/integrate_1220.py',sha256=h(original),executed=False)
 save(B+'/root_operation_sources.json',dict(status='exact_sources_preserved',sources=root_sources))

 p=R/B/'root_operations/deliver_1220.py'
 with p.open('xb') as stream:stream.write(Path(__file__).read_bytes())
 ignore=R/'.gitignore';prior=ignore.read_text();adds=[]
 for raw_name in RAW_PATHS:
  line='/'+raw_name
  assert not git('ls-files','--',raw_name).stdout
  if line not in prior.splitlines():adds.append(line)
 for p in sorted((R/E).rglob('*.log')):
  line='!/'+p.relative_to(R).as_posix()
  if line not in prior.splitlines():adds.append(line)
 if adds:ignore.write_text(prior+'\n# Exact immutable audit logs,20261020T2020.\n'+'\n'.join(adds)+'\n')
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
 exact.update('docs/'+name+'.md' for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式非Long开发结果'])
 archived={}
 pull=rd('results/formal_main_v2/pulls/20261020T122634Z_f16248744f18/receipt.json')
 assert h(R/'results/formal_main_v2/pulls/20261020T122634Z_f16248744f18/receipt.json')=='6deff3b3ba9facde8add9e038ed466b2efd2f96f645296cea57b30e3537423c0'
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
 assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_1220_delivery.jsonl'},excluded
 assert set(archived)<=set(selected)
 assert all(p.relative_to(R).as_posix() in selected for p in (R/E).rglob('*') if p.is_file()),'immutable archive ignored or missing'
 for i in range(0,len(selected),60):git('add','--',*selected[i:i+60])
 required=dict(schema='cti_nonweight_archive_stage_v1',kind='required_files',files=[ref(n) for n in sorted(selected)])
 save(B+'/git_required_files.json',required);git('add','--',B+'/git_required_files.json')
 g=module('delivery1220index','scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6')
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
  root_independent_complete=64,new_root_GPU_submissions=['3049132','3049172','3049191'],new_development_trials_accepted=400,active_runs_not_terminally_collected=True,
  Long_compatible_development_trials=2200,current_wrapper_actual_trials=2000,legacy_equivalent_trials=600,unique_initial_states=300,
  old_GPU_cost_not_added_again=True,all_historical_results_preserved=True,global_consumer_not_modified=True,final_sealed=True,no_normal_GPU_realtime_polling=True))
 for n in [B+'/git_index_guard.json',B+'/git_whitespace_diagnostic.json',B+'/git_delivery.json']:
  git('add','--',n);assert git('show',':'+n).stdout==(R/n).read_bytes()
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines())
 result=git('commit','-m','Accept 400 nonLong development trials and dispatch 600 matched trials')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_1220.json',dict(commit=commit,baseline=HEAD,files=count,index_guard='passed',root_complete=64,accepted_development_trials=400,current_action_development_trials=2000))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=commit,files=count,raw_whitespace_exceptions=len(exceptions),summary=result.stdout.decode().splitlines()[:2])),flush=True)

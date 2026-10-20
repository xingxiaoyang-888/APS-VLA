from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,importlib.util,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T2117';E='results/formal_main_v2/engineering/supervision_delivery_1317'
HEAD='26b4d9eb5ec9e5229b8e1c303e2b3a8980b065e7'
INPUTS={"transport_pins":{"results/formal_main_v2/control_transport/nonLong_development_independent_1317_post_a1.jsonl":"67010c31f6059414832bb6b40e07463b14a10da7c80505d79d1b39086c3e976d","results/formal_main_v2/control_transport/nonLong_development_plans_1317_manifests_a1.jsonl":"8251181e4e38f058f4bc3d8098650f1f9590dc32cf3fcb1e2b30a5e2cbbc80ee","results/formal_main_v2/control_transport/heartbeat_1317_gateway_submit_libero_object_k256_seed17.jsonl":"cf156f9b876a6749a776d7ac9e1d538ea2c9cd772ff096a2002f319ceaf4239a","results/formal_main_v2/control_transport/heartbeat_1317_dispatch_seal.jsonl":"e61953ba86d29caa58d4f493712aac135f41868d5883078d47a898dc7143865a","results/formal_main_v2/control_transport/heartbeat_1317_observation.jsonl":"e350e86eb853ba39378ead5b1d7ecf7b8dc07a188de89a446609c1fbb98a9e07","results/formal_main_v2/control_transport/independent_Goal_terminal_1317_a2.jsonl":"5311f53e3b4ad79593a6e3f0d636bd8f4c8b94dba00a362e015844e43b773db9","results/formal_main_v2/control_transport/nonLong_development_plans_1317_preview_a1.jsonl":"16101e6c900d5145bbdb2ddc7d7c7e89ab64ed53777685bb9dd4eaabd8df461c","results/formal_main_v2/control_transport/heartbeat_1317_integration_independent_archive.jsonl":"203ea2813e377ac76b2154d3a822fdc61320f85f19ca00241c23b6920de1b27d","results/formal_main_v2/control_transport/nonLong_development_independent_1317_plans_a1.jsonl":"d90eba46ac8158778e5372a6efb13e59ad3e91780de0e1ec7d4b3e257691869c","results/formal_main_v2/control_transport/record_healthy_1317.jsonl":"057e057589effbbb899a65ad5eac7f86143ebdfd47cadb3db3695747c22b9920","results/formal_main_v2/control_transport/heartbeat_1317_reserve_libero_goal_k128_seed41.jsonl":"705ffcdbf4277bfbac563481d57243ac4261e499b93dc0b74b8d4e9064637ec7","results/formal_main_v2/control_transport/heartbeat_1317_reserve_libero_spatial_k256_seed17.jsonl":"a8795d9734c476b33c0bf166293bb4dd235da62354f15dc9e1c8fd2847c3289a","results/formal_main_v2/control_transport/heartbeat_1317_reserve_libero_object_k256_seed17.jsonl":"206f2fc961435df68ab3bdb7265bb828b2a5956f296b234b33725083fdf453d3","results/formal_main_v2/control_transport/heartbeat_1317_static_plan_publication.jsonl":"a74b93a606426f892f97c93d57b8706327ee6ac8ec89c9029d6a6eca303366cd","results/formal_main_v2/control_transport/heartbeat_1317_reserve_libero_goal_k256_seed17.jsonl":"c28fcbf82f2d66b6e4de62ed94da8ce4aa8809d1cfba9174dd9fde7f9b4518b5","results/formal_main_v2/control_transport/heartbeat_1317_reconcile_Goal3049679.jsonl":"70cf4e336e5dc46c077a4bea1ccb202231646d6b9410644c39bf0f4477a40548","results/formal_main_v2/control_transport/heartbeat_1317_state_snapshot.jsonl":"c43f40c3b5cc45f36ec83ce13db406f9c332a569630deac0c6497f03b4e47be2","results/formal_main_v2/control_transport/heartbeat_1317_gateway_submit_libero_goal_k128_seed41.jsonl":"bbe7aef59e5eaf88dd7e3fc35cd9150107fcd0759017152edc012e88f4e93876","results/formal_main_v2/control_transport/heartbeat_1317_gateway_submit_libero_spatial_k256_seed17.jsonl":"d48808c3c5b2c8eb03ab08d1acf67ad7909cb5cc11d2d704a0d2ceee4fe662b0","results/formal_main_v2/control_transport/heartbeat_1317_record_independent_acceptance.jsonl":"d5c0575b3192cfe7a33b01c2fb5c3b8023baf5abf0f431f6629a737ce2ab5f11","results/formal_main_v2/control_transport/nonLong_development_independent_1317_inputs_a1.jsonl":"949ad23e649c2494b0127a79e9074a3dbd95bba19fd523a04ced5dcaf860a25b","results/formal_main_v2/control_transport/heartbeat_1317_reconcile_Spatial3049632.jsonl":"cf48dc8d5838830ed7ee1feec8ef378ef6ee27b8d2968d2f4db39be721ce762b","results/formal_main_v2/control_transport/commit_healthy_1317.jsonl":"10bf53e8be82340607578724dfe0c9f4e98e757bed93d4ed1d26df0ec130641f","results/formal_main_v2/control_transport/nonLong_development_plans_1317_prepare_a1.jsonl":"08c1b334049003df1823db6f319ff44edac952fa02884e2dc14a93bd6184fc18","results/formal_main_v2/control_transport/heartbeat_1317_integration.jsonl":"cbc71e5d1959087f4291d99b4096f79cd48788d28f12a2a9ff20b06b8e948e61","results/formal_main_v2/control_transport/heartbeat_1317_previous_delivery_archive.jsonl":"f394b7b03ed3c258cc359e0a4252a3f73d8339ea82e2022a82e85aa06aa0f510","results/formal_main_v2/control_transport/heartbeat_1317_Goal_terminal_archive.jsonl":"4b2b7ceca9f28abf3dc7a85eb7f58a7a3ff4ac7ccc05fb2e242054d62cb53577","results/formal_main_v2/control_transport/heartbeat_1317_root_readiness.jsonl":"e6eaba006bddca491a1700fe9268b5137eb74e228f9201d332a47cf081f57a1a","results/formal_main_v2/control_transport/heartbeat_1317_nonLong_independent_archive.jsonl":"09da325f350d92d73061c225cf241785f0ae19b0a293fcbc4faf75f7f993b5a6","results/formal_main_v2/control_transport/heartbeat_1317_reconcile_Goal3049622.jsonl":"7b55824f75fd045ac8047cc14e8ad8d1aea49bcdb07350ea942f82c053ba2e22","results/formal_main_v2/control_transport/heartbeat_1317_reconcile_Object3049657.jsonl":"ad4b5da080eef1bb4de7332e290196056115c7351720f7541514ce8a8c98361f","results/formal_main_v2/control_transport/independent_integration_1317_actual_a1.jsonl":"b0dafdefc3f26085b6c8c1d6f640d1e455f3d7823e05cd7c931ddf88ca2f94a2","results/formal_main_v2/control_transport/heartbeat_1317_gateway_submit_libero_goal_k256_seed17.jsonl":"30c55ca6ba64e3de2a1ff64afe95d18d6162ad97a92e2d4949072ac0398c5a69","results/formal_main_v2/control_transport/independent_integration_1317_actual_a2.jsonl":"064e55a83eac57671a09e97cedc7b6ec4f38f720c4aa1b367df9c7de835d3e62","results/formal_main_v2/control_transport/heartbeat_1317_terminal_root_review.jsonl":"035c02e5adc6d317cd0bbccf4104ce38c1180fa1c4568edaecc2e8d63d5a0374","results/formal_main_v2/control_transport/heartbeat_1317_nonLong_manifests.jsonl":"f0cd1ee59d78b7510f6d9330fbff23e6aaba6b500017a06c66d003491cab3842","results/formal_main_v2/control_transport/nonLong_development_plans_1317_seal_a1.jsonl":"37a89995db6523cb2dd71fa2e6fa9dbdf73fee6bf306dbb2af5df065de399688","results/formal_main_v2/control_transport/nonLong_development_independent_1317_seal_v1.jsonl":"cf99166e3598811833a567d81da0f78da8e947a3de95d35b926e0a36eab81b6d","results/formal_main_v2/control_transport/observe_formal_1317.jsonl":"478215848edce91867187e5c6a7d81101a9fc0bf23de2cba41d408ded2c0a4d0","results/formal_main_v2/control_transport/heartbeat_1317_terminal_pull.jsonl":"159756f4cfeb290fb78b121055dcefb8d3972ec6528cdac41008eb4cf1be9543","results/formal_main_v2/control_transport/heartbeat_1317_existing_training_configs.jsonl":"426a2362309fa83712bd7fe1cfaafd22a37e2fb3ef2a126f4f7e198810a34743","results/formal_main_v2/control_transport/heartbeat_1220_delivery.jsonl":"f0ef9a21eccee5db9328b4642ebc9bffc67389fd01d0c5fd8f300fc259614b3e","results/formal_main_v2/control_transport/final_delivery_independent_1220_a1.jsonl":"3e71df540fa48a70b0d9acf68141d127ef03d242ed0e08c4c4d78ce560ce00d0"},"summary":{"path":"results/formal_main_v2/preflight/heartbeat_20261020T2117/summary_after_dispatch.json","sha256":"91a102f6f2ea3edfc0cf7441b1bd72a40f1f90e7040fe064c8aaf7d6aafb6037"},"extra_exact":["results/formal_main_v2/downstream_reviews/3048609.json","results/formal_main_v2/downstream_reviews/3049191.json","results/formal_main_v2/downstream_reviews/Goal_seed17_23_1317_independent.json","results/formal_main_v2/invocations/libero_goal_development_428eafaeb10a5ce3_attempt01.json","results/formal_main_v2/invocations/libero_goal_development_5185766bb353c8e6_attempt01.json","results/formal_main_v2/invocations/libero_object_development_5185766bb353c8e6_attempt01.json","results/formal_main_v2/invocations/libero_spatial_development_5185766bb353c8e6_attempt01.json","results/formal_main_v2/job_receipts/3048609.json","results/formal_main_v2/job_receipts/3049191.json","results/formal_main_v2/libero_goal/downstream/development/8c843c1d4ee8383c/attempt01/action_execution/3048609/completion.json","results/formal_main_v2/libero_goal/downstream/development/8c843c1d4ee8383c/attempt01/action_execution/3048609/events.jsonl","results/formal_main_v2/libero_goal/downstream/development/8c843c1d4ee8383c/attempt01/action_execution/3048609/identity.json","results/formal_main_v2/libero_goal/downstream/development/8c843c1d4ee8383c/attempt01/adapter_invocations/3048609_b0acc7c5a81d461ea7ebf70e6ef1d3da.json","results/formal_main_v2/libero_goal/downstream/development/8c843c1d4ee8383c/attempt01/adapter_invocations/3048609_b0acc7c5a81d461ea7ebf70e6ef1d3da.jsonl","results/formal_main_v2/libero_goal/downstream/development/8c843c1d4ee8383c/attempt01/closed_loop_report.json","results/formal_main_v2/libero_goal/downstream/development/8c843c1d4ee8383c/attempt01/config.json","results/formal_main_v2/libero_goal/downstream/development/8c843c1d4ee8383c/attempt01/panel.json","results/formal_main_v2/libero_goal/downstream/development/8c843c1d4ee8383c/attempt01/trials.jsonl","results/formal_main_v2/libero_goal/downstream/development/ea4e52de3babd049/attempt01/action_execution/3049191/completion.json","results/formal_main_v2/libero_goal/downstream/development/ea4e52de3babd049/attempt01/action_execution/3049191/events.jsonl","results/formal_main_v2/libero_goal/downstream/development/ea4e52de3babd049/attempt01/action_execution/3049191/identity.json","results/formal_main_v2/libero_goal/downstream/development/ea4e52de3babd049/attempt01/adapter_invocations/3049191_90ed66dcddc849af8dce557d6522f179.json","results/formal_main_v2/libero_goal/downstream/development/ea4e52de3babd049/attempt01/adapter_invocations/3049191_90ed66dcddc849af8dce557d6522f179.jsonl","results/formal_main_v2/libero_goal/downstream/development/ea4e52de3babd049/attempt01/closed_loop_report.json","results/formal_main_v2/libero_goal/downstream/development/ea4e52de3babd049/attempt01/config.json","results/formal_main_v2/libero_goal/downstream/development/ea4e52de3babd049/attempt01/panel.json","results/formal_main_v2/libero_goal/downstream/development/ea4e52de3babd049/attempt01/trials.jsonl","results/formal_main_v2/submissions/3049622.json","results/formal_main_v2/submissions/3049632.json","results/formal_main_v2/submissions/3049657.json","results/formal_main_v2/submissions/3049679.json","results/slurm/cti-formal-downstream_3048609.err","results/slurm/cti-formal-downstream_3048609.out","results/slurm/cti-formal-downstream_3049191.err","results/slurm/cti-formal-downstream_3049191.out"],"extra_prefixes":["results/formal_main_v2/execution/nonLong_action_v1_1317/","results/formal_main_v2/pulls/20261020T132113Z_317ce98aa8f5/","results/formal_main_v2/downstream_gateway/7b8b860d709366770fb8f7f91015f49c06a66cdb03582a6f71bd1735e20f02f9/","results/formal_main_v2/downstream_gateway/0ae44db2e1a47ead872d864bd5982ff6e5728048f75dee5038a7c57d2f408abe/","results/formal_main_v2/downstream_gateway/aa99dd1b65fede72a4f4143b39292b06839ca4e16cc57410461bb306f639b750/","results/formal_main_v2/downstream_gateway/8ff3c887f80327c868c3cd4023a28c95363cd2754fce9e1c3b0ed104635f7786/"],"job_ids":["3049622","3049632","3049657","3049679"]}
TRANSPORT_PINS=INPUTS['transport_pins']
SUMMARY_SHA=INPUTS['summary']['sha256']
EXTRA_EXACT=INPUTS['extra_exact']
EXTRA_PREFIXES=INPUTS['extra_prefixes']
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
c=module('delivery1317ctl','scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD and not git('diff','--cached','--name-only').stdout
 state=rd('results/experiment_supervisor/state.json');f=state['formal_main_progress']
 assert state['pending_submission'] is None and f['root_and_independent_completed_arms']==64
 assert f['supervision_integrity_review_1317']['status']=='passed' and f['supervision_integrity_review_1317']['independent_review']['sha256']=='7128c96f5c3b08ff14d9c9add90e33e3f61889aeed27d887bfc68c26c575dc66'
 assert not f['supervision_integrity_review_1317']['submission_independent_integration_review_pending']
 assert f['completed_development_trials']==4012 and f['current_action_development_trial_count']==2800
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
 # Preserve the independently reviewed, unexecuted integration draft.
 original=R/'.local/integrate_1317_planned.py';assert h(original)=='7c4e61f24567f3c24c834b4d4f3f53973b2b9733c72dbf57080bc86ed1a6ae49'
 dst=R/B/'root_operations/integrate_1317_planned_unexecuted.py'
 if dst.exists():assert h(dst)==h(original)
 else:dst.write_bytes(original.read_bytes())
 root_sources[dst.relative_to(R).as_posix()]=dict(original='.local/integrate_1317_planned.py',sha256=h(original),executed=False)
 save(B+'/root_operation_sources.json',dict(status='exact_sources_preserved',sources=root_sources))

 p=R/B/'root_operations/deliver_1317.py'
 with p.open('xb') as stream:stream.write(Path(__file__).read_bytes())
 ignore=R/'.gitignore';prior=ignore.read_text();adds=[]
 for raw_name in RAW_PATHS:
  line='/'+raw_name
  assert not git('ls-files','--',raw_name).stdout
  if line not in prior.splitlines():adds.append(line)
 for p in sorted((R/E).rglob('*.log')):
  line='!/'+p.relative_to(R).as_posix()
  if line not in prior.splitlines():adds.append(line)
 if adds:ignore.write_text(prior+'\n# Exact immutable audit logs,20261020T2117.\n'+'\n'.join(adds)+'\n')
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
 exact.update('docs/'+name+'.md' for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式非Long开发结果','正式Goal主预算开发结果'])
 archived={}
 pull=rd('results/formal_main_v2/pulls/20261020T132113Z_317ce98aa8f5/receipt.json')
 assert h(R/'results/formal_main_v2/pulls/20261020T132113Z_317ce98aa8f5/receipt.json')=='c5c3cf85a1a6738b78cc4f76714873cc82ee0987719912bb61f07ecef8acfc4a'
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
 assert set(excluded)<={'results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/formal_main_v2/control_transport/heartbeat_1317_delivery.jsonl'},excluded
 assert set(archived)<=set(selected)
 assert all(p.relative_to(R).as_posix() in selected for p in (R/E).rglob('*') if p.is_file()),'immutable archive ignored or missing'
 for i in range(0,len(selected),60):git('add','--',*selected[i:i+60])
 required=dict(schema='cti_nonweight_archive_stage_v1',kind='required_files',files=[ref(n) for n in sorted(selected)])
 save(B+'/git_required_files.json',required);git('add','--',B+'/git_required_files.json')
 g=module('delivery1317index','scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6')
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
  weights_added=False,sealed_final_values_added=False,draft_syntax_check_note='An in-memory shell transport quoting check failed before any execution or file write; corrected literal quoting passed. No GPU or scientific configuration changed.',excluded_live_files=excluded,raw_original_whitespace_preserved=[ref(n) for n in exceptions],
  root_independent_complete=64,new_root_GPU_submissions=INPUTS['job_ids'],new_development_trials_accepted=800,active_runs_not_terminally_collected=True,
  Long_compatible_development_trials=2200,current_wrapper_actual_trials=2800,legacy_equivalent_trials=600,unique_initial_states=400,
  old_GPU_cost_not_added_again=True,all_historical_results_preserved=True,global_consumer_not_modified=True,final_sealed=True,no_normal_GPU_realtime_polling=True))
 for n in [B+'/git_index_guard.json',B+'/git_whitespace_diagnostic.json',B+'/git_delivery.json']:
  git('add','--',n);assert git('show',':'+n).stdout==(R/n).read_bytes()
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines())
 result=git('commit','-m','Accept Goal development evidence and fill registered development slots')
 commit=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_1317.json',dict(commit=commit,baseline=HEAD,files=count,index_guard='passed',root_complete=64,accepted_development_trials=800,current_action_development_trials=2800))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=commit,files=count,raw_whitespace_exceptions=len(exceptions),summary=result.stdout.decode().splitlines()[:2])),flush=True)

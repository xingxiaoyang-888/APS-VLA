from pathlib import Path
import json,hashlib,sys,importlib.util,os
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B=R/'results/formal_main_v2/preflight/heartbeat_20261020T0122'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'.local/long_development_1722/manifest_index.json';assert h(p)=='03e2dcc45625f2b02ef5f4e99eede5b9e9c3971ef2267281c35b796b4ac4362b'
idx=json.loads(p.read_text());rp=B/'Long_selected_identity_root_check.json';assert h(rp)=='e3b08dff62a583e910aecd04179841017e10f1216f6a19f431036fe056ff5757';root=json.loads(rp.read_text())
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('publishLong1722ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';before=h(statepath);s=json.loads(statepath.read_text());assert s['pending_submission'] is None
 existing=[j for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2' and j.get('suite')=='libero_10' and j.get('mode')=='development']
 mids={m for j in existing for m in j['method_ids']};assert mids==set(root['original_methods'])
 items=[];seen=set()
 for shard in idx['shards']:
  src=R/shard['candidate']['path'];dst=R/shard['canonical_path']
  assert src.parent==R/'.local/long_development_1722/manifests' and dst.parent==R/'results/formal_main_v2/execution/long_remaining16_action_v1_1722'
  assert not src.is_symlink() and not dst.exists() and not dst.is_symlink()
  raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()==shard['candidate']['sha256'] and len(raw)==shard['candidate']['bytes']
  v=json.loads(raw);assert v['schema']=='formal_main_v2' and v['kind']=='evaluation_execution' and v['split']=='development' and v['suite']=='libero_10'
  assert v['environment']==dict(environment_seed=0,runtime_seed=17,wait_steps=10,action_chunk=8,max_steps=520)
  assert v['development_panel']=='configs/manifests/formal_main_v2/libero_10/initial_states/development.json'
  assert h(R/v['development_panel'])==v['development_panel_sha256']=='46a06087483151e36198167e7d4e5313c50b63172e09128d65a3650112f0a268'
  actual=[m['identity']['method_id'] for m in v['methods']];assert actual==shard['method_ids'] and len(actual)==2
  assert not set(actual)&(seen|mids);seen.update(actual)
  for m in v['methods']:
   identity=m['identity'];prior=root['all18_selected'][identity['method_id']]
   assert m['checkpoint']==prior['checkpoint_path'] and identity['checkpoint_sha256']==prior['checkpoint_sha256']
   assert identity['visual_tokens']==shard['visual_tokens']==prior['visual_tokens'] and identity['training_seed']==shard['seed']==prior['seed']
   assert identity['future_head_deployed'] is False and identity['training_complete'] is True
   assert h(R/m['receipt'])==identity['deployment_receipt_sha256'] and h(R/m['f01_report'])==identity['f01_report_sha256']
  items.append((src,dst,raw,shard))
 assert len(items)==8 and seen==set(root['fresh_target_method_ids'])
 for src,dst,raw,shard in items:
  dst.parent.mkdir(parents=True,exist_ok=True)
  with dst.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  assert h(dst)==shard['candidate']['sha256']
 assert h(statepath)==before
 out=B/'Long_manifest_publication.json';record=dict(schema='formal_main_v2',kind='root_development_manifest_publication',status='published_original_manifest_bytes_only',source_index=dict(path=p.relative_to(R).as_posix(),sha256=h(p)),root_selected_identity=dict(path=rp.relative_to(R).as_posix(),sha256=h(rp)),files=[dict(path=dst.relative_to(R).as_posix(),sha256=h(dst),bytes=len(raw),source=src.relative_to(R).as_posix()) for src,dst,raw,shard in items],methods=sorted(seen),planned_trials=1600,unique_development_initials=100,state_unchanged=True,submitted=False,readiness_granted=False,final_release=False)
 with out.open('x') as f:json.dump(record,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(dict(path=out.relative_to(R).as_posix(),sha256=h(out),canonical_manifests=8,planned_trials=1600,submission=False)))

from pathlib import Path
import hashlib,importlib.util,json,os,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';B='results/formal_main_v2/preflight/heartbeat_20261020T0632'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert sha(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('root_mirror2232_ctl',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';ss=sha(sp)
 ip=R/'results/formal_main_v2/invocations/libero_10_development_ea4e52de3babd049_attempt01.json';assert sha(ip)=='2bf41d87718038e41f35d52b90506a3e973a7270869278157fb953d8238a7f84';inv=json.loads(ip.read_text())
 vp=R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';assert sha(vp)=='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926';inventory=json.loads(vp.read_text())
 frozen=inventory['files'];assert len(frozen)==173
 selected={str(S/k):v for k,v in frozen.items()};assert all(inv['watched_files'].get(k)==v for k,v in selected.items())
 pending=[];existing=[]
 for remote,expected in inv['watched_files'].items():
  source=Path(remote);name=source.relative_to(P);dest=R/name
  if dest.exists():
   assert sha(dest)==expected;existing.append(str(name));continue
  assert str(source) in selected
  canonical=source.relative_to(S).as_posix();assert sha(R/canonical)==expected
  assert source.is_file() and not source.is_symlink() and source.resolve()==source
  assert dest.resolve()==dest and all(not q.is_symlink() for q in dest.parents if q==R or R in q.parents)
  st=source.stat();data=source.read_bytes();assert source.stat()==st and hashlib.sha256(data).hexdigest()==expected
  pending.append((source,dest,st,data,canonical,expected))
 assert len(pending)==173
 rows=[]
 for source,dest,st,data,canonical,expected in pending:
  dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  assert sha(dest)==expected and source.stat()==st and sha(source)==expected and sha(R/canonical)==expected
  rows.append({'source':str(source),'destination':dest.relative_to(R).as_posix(),'canonical_source':canonical,'sha256':expected,'bytes':len(data),'raw_bytes_changed':False})
 receipt={'schema':'formal_main_v2','kind':'exact_frozen_source_mirror_transport','status':'verified','reason':'First action-version terminal review requires exact P-relative source snapshot mirror, absent in R. No review/code change.','invocation':{'path':ip.relative_to(R).as_posix(),'sha256':sha(ip)},'source_inventory':{'path':vp.relative_to(R).as_posix(),'sha256':sha(vp)},'files':rows,'existing_watched_files_verified':len(existing),'new_files':len(rows),'windows_files_written':False,'weights_copied':False,'sealed_values_read':False,'state_unchanged':sha(sp)==ss}
 rp=R/B/'3043709_source_snapshot_mirror.json'
 with rp.open('x') as f:json.dump(receipt,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 assert sha(sp)==ss
 print(json.dumps({'receipt':{'path':rp.relative_to(R).as_posix(),'sha256':sha(rp)},'files':len(rows),'bytes':sum(x['bytes'] for x in rows)}),flush=True)

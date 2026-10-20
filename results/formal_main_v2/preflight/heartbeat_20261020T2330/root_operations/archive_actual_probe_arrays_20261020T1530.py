from pathlib import Path
import json,hashlib,sys,importlib.util,tarfile,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261020T2330';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1530'
D=R/'.local/goal_probe_terminal_20261020T1530/arrays_delivery';BASE='results/formal_main_v2/engineering/goal_t0_probe_20261020T1418/attempt01';DEST=R/BASE/'arrays_archive'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=h(p),bytes=p.stat().st_size)
def cp(src,dst,pin):
 assert src.is_relative_to(D) and (dst.is_relative_to(DEST) or dst.is_relative_to(R/E/'Goal_probe_arrays')) and h(src)==pin
 assert not any(p.is_symlink() for p in [src,*src.parents,dst,*dst.parents])
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():assert h(dst)==pin
 else:
  with dst.open('xb') as f:f.write(src.read_bytes())
 return dict(source=ref(src),archive=ref(dst))
started=time.monotonic();cpu=time.process_time();mf=D/'delivery_manifest.json';assert h(mf)=='a9f5d72a49cb4aaecfe3503a5030d62ee2c68ac1306603e33ec5a8894f90c270';man=json.loads(mf.read_bytes())
assert man['file_count']==len(man['files'])==7 and man['nonweight_only'] and not man['scientific_release']
for r in man['files']:
 p=R/r['path'];assert p==D/r['relative_path'] and p.stat().st_size==r['bytes'] and h(p)==r['sha256']
mm=json.loads((D/'member_manifest.json').read_bytes());orig=json.loads((D/'source_npz_manifest.json').read_bytes())
assert h(D/'source_npz_manifest.json')=='ab0deed3e6a564302aa1bd08c0615b78b1f762ce96821cc07b6938f7e61b0161'
rows={r['name']:r for r in mm['files']};sources={r['source']:r for r in orig['files']};assert len(rows)==len(sources)==288
archive=D/'goal_t0_probe_3050711_development_arrays.tar.gz';assert h(archive)=='97a41e3248b708ec0906b46bd8417ba023935482b8274910fdff6954efb8174b' and archive.stat().st_size==42988390<100*(1<<20)
seen=set();total=0
with tarfile.open(archive,'r|gz') as tf:
 for member in tf:
  assert member.isfile() and member.name in rows and member.name not in seen
  row=rows[member.name];src=Path(row['source']);assert src.is_relative_to(P/BASE/'arrays') and member.name=='arrays/'+src.name and src.suffix=='.npz'
  assert row['sha256']==sources[str(src)]['sha256'] and row['bytes']==sources[str(src)]['bytes']==member.size
  assert src.stat().st_size==member.size and h(src)==row['sha256']
  digest=hashlib.sha256();n=0
  with tf.extractfile(member) as inp:
   while True:
    chunk=inp.read(1<<20)
    if not chunk:break
    n+=len(chunk);digest.update(chunk)
  assert n==member.size and digest.hexdigest()==row['sha256'];seen.add(member.name);total+=n
assert seen==set(rows) and total==orig['total_bytes']==43327608
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('arraysdelivery1530ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json');copies=[]
 for row in man['files']:
  src=R/row['path'];dst=DEST/src.name if src==archive else R/E/'Goal_probe_arrays'/src.name;copies.append(cp(src,dst,row['sha256']))
 copies.append(cp(mf,R/E/'Goal_probe_arrays'/mf.name,h(mf)))
 assert before==h(R/'results/experiment_supervisor/state.json')
 proof=dict(status='passed_lossless_nonweight_development_array_delivery',copies=copies,archive=ref(DEST/archive.name),member_manifest=ref(R/E/'Goal_probe_arrays/member_manifest.json'),source_manifest=ref(R/E/'Goal_probe_arrays/source_npz_manifest.json'),root_verified_members=len(seen),root_verified_original_and_restored_SHA=True,uncompressed_bytes=total,no_weights=True,no_final_states=True,originals_retained_in_P=True,scientific_release=False,original_hold_unchanged=True,new_GPU_jobs=0,CPU_process_seconds=time.process_time()-cpu,CPU_wall_seconds=time.monotonic()-started,source_manifest_previous_copy_to_R_false_is_historical_plan=True)
 out=R/B/'Goal_probe_arrays_delivery.json'
 with out.open('x') as fp:json.dump(proof,fp,ensure_ascii=False,sort_keys=True,indent=2);fp.write(chr(10))
 print(json.dumps(dict(receipt=ref(out),archive=proof['archive'],root_verified_members=288)),flush=True)

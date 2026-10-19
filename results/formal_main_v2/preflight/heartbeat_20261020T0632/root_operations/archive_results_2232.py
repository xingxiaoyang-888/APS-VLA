from pathlib import Path
import importlib.util,sys,json,hashlib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0632';E='results/formal_main_v2/engineering/supervision_delivery_2232'
RAW='results/formal_main_v2/libero_10/downstream/development/ea4e52de3babd049/attempt01/trials.jsonl'
PULL='results/formal_main_v2/pulls/20261019T223821Z_c4b67281fa45/receipt.json'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/Long_development3043709_20261020_2232.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):p=R/rel;return dict(path=rel,sha256=h(p),bytes=p.stat().st_size)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,sort_keys=True,indent=2);f.write('\n')
 return ref(rel)
def mod(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','archive2232_ctl')
m=mod('scripts/ops/nonweight_archive.py','f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2','archive2232_codec')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 ss=h(R/'results/experiment_supervisor/state.json')
 assert h(R/PULL)=='ed05968d82ceb14d333990099496d32aa0fdaf40f7217525636d10ec113f132e'
 pull=json.loads((R/PULL).read_text());assert pull['status']=='verified_nonweight_snapshot'
 row=next(x for x in pull['files'] if x['relative']==RAW)
 assert ref(RAW)==dict(path=RAW,sha256=row['sha256'],bytes=31699657)
 req=save(B+'/Long3043709_archive_request.json',dict(schema=m.SCHEMA,kind='archive_request',files=[ref(RAW)],provenance=[ref(PULL),ref('results/formal_main_v2/job_receipts/3043709.json'),ref('results/formal_main_v2/downstream_reviews/3043709.json')]))
 result=m.pack(R,req['path'],SNAP);assert result['status']=='packed_verified' and result['original_bytes']==31699657
 save(B+'/Long3043709_archive_pack.json',dict(**result,independent_acceptance_pending=True,source_job='3043709',original_retained=True))
 save(B+'/Long3043709_archive_inputs.json',dict(raw=ref(RAW),snapshot=ref(SNAP),pull=ref(PULL),source_tool=ref('scripts/ops/nonweight_archive.py')))
 manifest=R/'.local/object64seed41_independent_2232/delivery_files.json';assert h(manifest)=='cf49e289d7cb68e2eaaa5cfe13ac86991b9734a1c75906cdc888c117330c1e5e'
 data=json.loads(manifest.read_text());rows=data['files']+[ref(manifest.relative_to(R).as_posix())];copied=[]
 for row in rows:
  source=R/row['path'];assert source.parent==manifest.parent and h(source)==row['sha256'] and source.stat().st_size==row['bytes']
  dest=R/E/'Object64seed41_independent'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(source.read_bytes())
  assert h(dest)==row['sha256'];copied.append({'source':row,'archived':ref(dest.relative_to(R).as_posix())})
 review=manifest.parent/'3037535_independent_review.json';canonical=R/'results/formal_main_v2/libero_object/k64/seed41/training/segment_reviews/3037535_independent.json'
 with canonical.open('xb') as f:f.write(review.read_bytes())
 assert h(canonical)=='a1643466dd8bbe032261c195c8ebef6ef214c373d82ab4ede6829450a1623301'
 save(B+'/Object64seed41_independent_delivery.json',dict(copied=copied,canonical=ref(canonical.relative_to(R).as_posix()),source_manifest=ref(manifest.relative_to(R).as_posix()),state_unchanged=h(R/'results/experiment_supervisor/state.json')==ss))
 assert h(R/'results/experiment_supervisor/state.json')==ss
 print(json.dumps({'archive':result,'Object_independent':ref(canonical.relative_to(R).as_posix()),'delivery_files':len(copied)}),flush=True)

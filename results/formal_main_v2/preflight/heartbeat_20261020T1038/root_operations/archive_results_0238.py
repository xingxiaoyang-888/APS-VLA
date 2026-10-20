from pathlib import Path
import importlib.util,sys,json,hashlib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1038'
PULL='results/formal_main_v2/pulls/20261020T024610Z_89cee566247b/receipt.json'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/Object64seed23_20261020_0238.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):p=R/rel;return dict(path=rel,sha256=h(p),bytes=p.stat().st_size)
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
 return ref(rel)
def mod(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','archive0238ctl')
m=mod('scripts/ops/nonweight_archive.py','f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2','archive0238codec')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 ss=h(R/'results/experiment_supervisor/state.json')
 assert h(R/PULL)=='aa509e9edbe2bb52ae1832501b7a4785c43fa579215e67a17f47d80e284ec53b'
 pull=json.loads((R/PULL).read_text());assert pull['status']=='verified_nonweight_snapshot'
 base='results/formal_main_v2/libero_object/k64/seed23/training/'
 rows=[x for x in pull['files'] if x['relative'].startswith(base) and (x['relative'].endswith('/cost_events.jsonl') or x['relative']==base+'cache_events/3044017_40524db5877a.jsonl')]
 assert len(rows)==3
 raw=[]
 for row in rows:
  name=row['relative']
  f=ref(name);assert f==dict(path=name,sha256=row['sha256'],bytes=row['bytes']);raw.append(f)
 assert sum(x['bytes'] for x in raw)==18358140
 req=save(B+'/Object3044017_archive_request.json',dict(schema=m.SCHEMA,kind='archive_request',files=raw,provenance=[ref(PULL),ref('results/formal_main_v2/job_receipts/3044017.json'),ref(base+'segment_reviews/3044017.json')]))
 result=m.pack(R,req['path'],SNAP);assert result['status']=='packed_verified' and result['original_bytes']==18358140
 save(B+'/Object3044017_archive_pack.json',dict(**result,source_job='3044017',original_retained=True))
 out=save(B+'/Object3044017_archive_inputs.json',dict(raw=raw,snapshot=ref(SNAP),pull=ref(PULL),source_tool=ref('scripts/ops/nonweight_archive.py')))
 op=R/B/'root_operations/archive_results_0238.py'
 with op.open('xb') as stream:stream.write(Path(__file__).read_bytes())
 assert h(R/'results/experiment_supervisor/state.json')==ss
 print(json.dumps({'archive':result,'inputs':out}),flush=True)

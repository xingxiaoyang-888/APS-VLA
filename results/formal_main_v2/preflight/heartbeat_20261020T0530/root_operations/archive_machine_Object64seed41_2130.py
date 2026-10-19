from pathlib import Path
import importlib.util,sys,json,hashlib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0530'
RAW='results/formal_main_v2/libero_object/k64/seed41/training/cache_events/3037535_ff11e398c517.jsonl'
PULL='results/formal_main_v2/pulls/20261019T215443Z_58826646465f/receipt.json'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/machine_training_object64seed41_20261020_2130.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):p=R/rel;return dict(path=rel,sha256=h(p),bytes=p.stat().st_size)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,sort_keys=True,indent=2);f.write('\n')
 return ref(rel)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archive_auto2130_ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
codec=R/'scripts/ops/nonweight_archive.py';assert h(codec)=='f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2'
sp=importlib.util.spec_from_file_location('archive_auto2130_codec',codec);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert h(R/PULL)=='1518b74a2ef0331fcd2dc09619df6289fb37a9418fafa3035a641f8c90183c7c'
 pull=json.loads((R/PULL).read_text());assert pull['status']=='verified_nonweight_snapshot'
 row=next(x for x in pull['files'] if x['relative']==RAW)
 assert ref(RAW)==dict(path=RAW,sha256='accac0f01a63667ccf28bd6dec7909d28aa4d3c6c9643719f2e1f0fb5be8b9b8',bytes=132813168)
 assert row['sha256']==ref(RAW)['sha256'] and row['bytes']==132813168
 req=save(B+'/machine_only_Object64seed41_archive_request.json',dict(schema=m.SCHEMA,kind='archive_request',files=[ref(RAW)],provenance=[ref(PULL),ref('results/formal_main_v2/job_receipts/3037535.json')]))
 result=m.pack(R,req['path'],SNAP);assert result['status']=='packed_verified' and result['original_bytes']==132813168
 save(B+'/machine_only_Object64seed41_archive_pack.json',dict(**result,root_independent_accepted=False,source_job='3037535',machine_only_training_complete=True,scientific_acceptance_pending=True))
 save(B+'/machine_only_Object64seed41_archive_inputs.json',dict(raw=ref(RAW),snapshot=ref(SNAP),pull=ref(PULL),source_tool=ref('scripts/ops/nonweight_archive.py'),old_union29_archive_unchanged=True))
 op=R/B/'root_operations';op.mkdir(exist_ok=True)
 with (op/'archive_machine_Object64seed41_2130.py').open('xb') as f:f.write(Path(__file__).read_bytes())
 print(json.dumps(result))

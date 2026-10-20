from pathlib import Path
import importlib.util,sys,json,hashlib,subprocess
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T2218'
PULL='results/formal_main_v2/pulls/20261020T144744Z_f346c6655778/receipt.json'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/Goal64seed17_20261020T1418.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):p=R/rel;return dict(path=rel,sha256=h(p),bytes=p.stat().st_size)
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
 return ref(rel)
def mod(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','archiveGoal1418ctl')
m=mod('scripts/ops/nonweight_archive.py','f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2','archiveGoal1418codec')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 ss=h(R/'results/experiment_supervisor/state.json')
 assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R)
 assert h(R/PULL)=='86a9e731a2a9b4d7f9dbc3a7e507f808edba55cd2db42bf09d7f92e7daa88239'
 pull=json.loads((R/PULL).read_text());assert pull['status']=='verified_nonweight_snapshot'
 assert [str(j['job_id']) for j in pull['selected_jobs']]==['3043762']
 rows=[x for x in pull['files'] if x['relative'].startswith('results/formal_main_v2/libero_goal/k64/seed17/training/') and x['bytes']>20*(1<<20)]
 assert len(rows)==3
 raw=[]
 for row in rows:
  name=row['relative'];assert row['action']=='downloaded_verified' and name.endswith('.jsonl')
  f=ref(name);assert f==dict(path=name,sha256=row['sha256'],bytes=row['bytes']);raw.append(f)
 total=sum(x['bytes'] for x in raw);assert total==180480556
 req=save(B+'/Goal3043762_archive_request.json',dict(schema=m.SCHEMA,kind='archive_request',files=raw,provenance=[ref(PULL),ref('results/formal_main_v2/job_receipts/3043762.json')]))
 result=m.pack(R,req['path'],SNAP);assert result['status']=='packed_verified' and result['original_bytes']==total
 save(B+'/Goal3043762_archive_pack.json',dict(**result,source_job='3043762',original_retained=True,root_independent_training_acceptance=False,archival_only=True))
 out=save(B+'/Goal3043762_archive_inputs.json',dict(raw=raw,snapshot=ref(SNAP),pull=ref(PULL),source_tool=ref('scripts/ops/nonweight_archive.py'),scientific_completion_inferred=False))
 assert h(R/'results/experiment_supervisor/state.json')==ss
 op=R/B/'root_operations/archive_Goal3043762_20261020T1418.py'
 with op.open('xb') as stream:stream.write(Path(__file__).read_bytes())
 print(json.dumps({'archive':result,'inputs':out}),flush=True)

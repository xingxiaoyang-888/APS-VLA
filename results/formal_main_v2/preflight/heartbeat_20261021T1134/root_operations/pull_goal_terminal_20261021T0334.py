from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,shutil,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261021T1134';G='results/formal_main_v2/engineering/goal_full200_20261021T0110';OUT=G+'/attempt01'
PULL='results/formal_main_v2/pulls/terminal_goal_20261021T0334'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def dump(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
 return dict(path=rel,sha256=sha(p))
def load(rel,pin,name):
 p=R/rel;assert sha(p)==pin
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def utc():return datetime.now(timezone.utc).isoformat()
assert os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R)
source=R/'.local/goal_terminal_archive_20261021T0334/inventory.json'
assert sha(source)=='db4d8a05cd7f21af5aac0687d2190297cd571eb1a6ffc83eb74d235d53eb7ac1'
inventory=json.loads(source.read_text())
exclude={OUT+'/.original_run.adapter.lock',OUT+'/original_run/.evaluation.lock'}
expected=[]
for m in inventory['members']:
 if m['restore_root']!='P':continue
 rel=m['restore_relative'];assert m['source']==str(P/rel) and rel.startswith(OUT+'/')
 if rel in exclude:assert m['bytes']==0;continue
 assert m['namespace'] in ('P_passive','P_attempt_metadata')
 expected.append(dict(relative=rel,path=m['source'],sha256=m['sha256'],bytes=m['bytes'],job_ids=['3054717']))
assert len(expected)==15533
for ext in ['out','err']:
 rel='results/slurm/cti-goal-full200_3054717.'+ext;p=P/rel
 expected.append(dict(relative=rel,path=str(p),sha256=sha(p),bytes=p.stat().st_size,job_ids=['3054717']))
def build():
 rows=[]
 for e in expected:
  p=Path(e['path']);assert p==p.resolve() and p.is_file() and not p.is_symlink()
  assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'];rows.append(e)
 assert {str(p.relative_to(P)) for p in (P/OUT).rglob('*') if p.is_file()}=={r['relative'] for r in rows if r['relative'].startswith(OUT+'/')}|exclude
 for rel in exclude:assert (P/rel).stat().st_size==0
 return dict(files=sorted(rows,key=lambda x:x['relative']),missing=[],excluded=[dict(path=str(P/x),reason='zero_byte_runtime_lock_not_evidence',job_id='3054717') for x in sorted(exclude)])
g=load('scripts/ops/formal_object_single_error_gateway_v1/gateway.py','8471bba1419a9e0ca31f84e7e55ff232cd6fb0fcb4bcb89320140ea76292d727','goalterminalpullg');c=g.controller()
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statebytes=(R/'results/experiment_supervisor/state.json').read_bytes()
 assert hashlib.sha256(statebytes).hexdigest()=='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa'
 s=json.loads(statebytes);job=next(x for x in s['registered_jobs'] if x['job_id']=='3054717')
 a=g.actual_observation(c,c.Slurm(timeout=30),[job]);row=a['rows']['3054717']
 assert row['status']=='COMPLETED' and row['exit_code']=='0:0' and row['elapsed_seconds']==2205 and row['gpus']==1 and row['scheduler_name']==job['name'] and not a['queue']
 before=build();dump(PULL+'/inventory_before.json',before);records=[]
 for e in before['files']:
  p=R/e['relative'];p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists():
   assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'];action='same_sha_skipped'
  else:
   with Path(e['path']).open('rb') as src,p.open('xb') as dst:shutil.copyfileobj(src,dst,1024*1024)
   assert sha(p)==e['sha256'];action='downloaded_verified'
  records.append(dict(e,action=action,local_path=str(p)))
 after=build();assert before==after;dump(PULL+'/inventory_after.json',after)
 z=g.actual_observation(c,c.Slurm(timeout=30),[job]);assert z['rows']==a['rows'] and not z['queue']
 assert (R/'results/experiment_supervisor/state.json').read_bytes()==statebytes
 pull=dict(schema='formal_main_v2',kind='goal_full200_exact_nonweight_pull',status='verified_nonweight_snapshot',final_evidence=True,weights_copied=False,sealed_initial_states_copied=False,
 scientific_completion_inferred=False,root_utc=utc(),source_allowlist_sha256=sha(source),files=records,missing=[],excluded=before['excluded'],
 accounting_before=dict(jobs=a['rows'],real_observation=a),accounting_after=dict(jobs=z['rows'],real_observation=z),inventory_sha256=sha(R/PULL/'inventory_before.json'))
 pref=dump(PULL+'/receipt.json',pull)
 projected=R/B/'terminal_analysis_supervisor_projection.json';assert sha(projected)=='28972a53a01b3bf21e7c2194fe8b7fd31106fd49ed47290beb1a4f871d363513'
 job=next(x for x in json.loads(projected.read_text())['registered_jobs'] if x['job_id']=='3054717')
 refs={}
 for k,n in [('authorization','root_authorization.json'),('dispatch','held_dispatch_record.json'),('reservation','reservation.json')]:
  p=R/G/n;assert p.read_bytes()==(P/G/n).read_bytes();refs[k]=dict(path=G+'/'+n,sha256=sha(p))
 terminal=dict(kind='goal_full200_typed_terminal_manifest',execution_version='goal-full200-prospective-single-attempt-v1',status='complete_nonweight_pull',weights_copied=False,sealed_values_read=False,
 package_manifest_sha256='2767f20cdd3b862138f590d65563e1bad844cfe14e6fe41aecf2854fc4f0baec',job=job,
 artifacts=[dict(path=e['relative'],sha256=e['sha256'],bytes=e['bytes']) for e in records if e['relative'].startswith(OUT+'/')],**refs)
 tref=dump(B+'/Goal_terminal_manifest.json',terminal)
print(json.dumps(dict(pull=pref,terminal_manifest=tref,files=len(records),artifacts=len(terminal['artifacts']),state_unchanged=True)))

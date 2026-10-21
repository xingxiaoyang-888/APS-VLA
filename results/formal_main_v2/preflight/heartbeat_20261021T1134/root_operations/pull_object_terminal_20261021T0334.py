from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,shutil,sys,importlib.util,copy,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261021T1134';STATE='results/experiment_supervisor/state.json'
STATE_SHA='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa'
OUT='results/formal_main_v2/libero_object/downstream/linked_policy_error_correction/task08_state0049_dense/attempt01'
PULL='results/formal_main_v2/pulls/terminal_object_20261021T0334'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
 return dict(path=rel,sha256=sha(p))
def load(rel,pin,name):
 p=R/rel;assert sha(p)==pin
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def utc():return datetime.now(timezone.utc).isoformat()
assert os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R)
g=load('scripts/ops/formal_object_single_error_gateway_v1/gateway.py','8471bba1419a9e0ca31f84e7e55ff232cd6fb0fcb4bcb89320140ea76292d727','terminalpullg')
c=g.controller()
required=R/'.local/object_terminal_independent_20261021T0334/pull_required_files.json'
assert sha(required)=='4a96ff490da5aae69722c1b057f35dcf90ca2e43d9e8a842bc2fa8de24c33a4d'
expected=json.loads(required.read_text())['files']
assert len(expected)==13 and len({x['path'] for x in expected})==13
def inventory():
 rows=[]
 for e in expected:
  rel=e['path'];p=P/rel;assert p.resolve()==p and p.is_file() and not p.is_symlink()
  assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256']
  rows.append(dict(path=str(p),relative=rel,bytes=e['bytes'],sha256=e['sha256'],job_ids=['3054409']))
 assert {str(p.relative_to(P)) for p in (P/OUT).rglob('*') if p.is_file()}=={r['relative'] for r in rows if r['relative'].startswith(OUT+'/')}|{OUT+'/.evaluation.lock'}
 assert (P/OUT/'.evaluation.lock').stat().st_size==0
 assert {p.name for p in (P/'results/formal_main_v2/object_single_error_invocations/3054409').iterdir()}=={'identity.json','completion.json','action_events.jsonl','iterator_events.jsonl'}
 return dict(files=sorted(rows,key=lambda x:x['relative']),missing=[],excluded=[dict(job_id='3054409',path=str(P/OUT/'.evaluation.lock'),reason='unregistered_nonweight_extension')])
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statebytes=(R/STATE).read_bytes();assert hashlib.sha256(statebytes).hexdigest()==STATE_SHA
 state=json.loads(statebytes);j=next(j for j in state['registered_jobs'] if str(j['job_id'])=='3054409')
 a=g.actual_observation(c,c.Slurm(timeout=30),[j]);row=a['rows']['3054409']
 assert row['status']=='COMPLETED' and row['exit_code']=='0:0' and row['elapsed_seconds']==326 and row['gpus']==1 and row['scheduler_name']==j['name'] and not a['queue']
 before=inventory();dump(PULL+'/inventory_before.json',before)
 files=[]
 for item in before['files']:
  target=R/item['relative'];target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():
   assert target.stat().st_size==item['bytes'] and sha(target)==item['sha256'];action='same_sha_skipped'
  else:
   with (P/item['relative']).open('rb') as src,target.open('xb') as dst:shutil.copyfileobj(src,dst,1024*1024)
   assert sha(target)==item['sha256'];action='downloaded_verified'
  files.append(dict(item,local_path=str(target),action=action))
 after=inventory();assert before==after;dump(PULL+'/inventory_after.json',after)
 z=g.actual_observation(c,c.Slurm(timeout=30),[j]);assert z['rows']==a['rows'] and not z['queue']
 assert (R/STATE).read_bytes()==statebytes
 receipt=dict(schema='formal_main_v2',kind='nonweight_pull',status='verified_nonweight_snapshot',final_evidence=True,weights_copied=False,sealed_initial_states_copied=False,
 scientific_completion_inferred=False,started_utc=utc(),completed_utc=utc(),supervisor_state_sha256=STATE_SHA,registered_jobs=[j],requested_job_ids=['3054409'],
 selected_jobs=[dict(j,include_run_root=True,active_overlapping_job_ids=[])],skipped=[],files=files,missing=[],excluded=before['excluded'],
 accounting_before=dict(jobs=a['rows'],real_observation=a),accounting_after=dict(jobs=z['rows'],real_observation=z),inventory_sha256=sha(R/PULL/'inventory_before.json'))
 ref=dump(PULL+'/receipt.json',receipt)
 # Explicit accounting-only analysis projection. No persisted registry mutation.
 obs=json.loads((R/B/'initial_observation.json').read_text());assert sha(R/B/'initial_observation.json')=='0c0520630396e633c5b417a401da18bd100974e79d5f962308cf892bd945ac41'
 projected=copy.deepcopy(state);changes=[]
 for job in projected['registered_jobs']:
  jid=str(job['job_id'])
  if jid not in ('3054409','3054717'):continue
  actual=obs['projection']['observation']['rows'][jid]
  patch={k:actual[k] for k in ('status','exit_code','elapsed_seconds','gpus','node','allocation')};patch['raw_status']=actual['status']
  changes.append(dict(job_id=jid,before={k:job.get(k) for k in patch},after=patch));job.update(patch)
 state_ref=dump(B+'/terminal_analysis_supervisor_projection.json',projected)
 basis=dump(B+'/terminal_analysis_projection_basis.json',dict(kind='accounting_only_in_memory_analysis_projection',persisted_state_unchanged=True,original_state_sha256=STATE_SHA,observation_sha256=sha(R/B/'initial_observation.json'),changes=changes,analysis_projection=state_ref))
print(json.dumps(dict(pull=ref,state_projection=state_ref,basis=basis,files=len(files))))

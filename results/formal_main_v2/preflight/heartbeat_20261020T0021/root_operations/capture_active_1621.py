from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261020T0021'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin;spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return {'path':rel,'sha256':h(p)}
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','snapshot1419v2_ctl')
d=load('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','snapshot1419v2_identity')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=json.loads(sp.read_text());prior=copy.deepcopy(s)
 op=R/B/'initial_observation.json';assert h(op)=='6b2a7865d8269f0030a61aa1a5d60bdee92aa3056c449153ddb9a6059bbda21e';o=json.loads(op.read_text())
 assert s['pending_submission'] is None and set(o['observation']['rows'])=={str(j['job_id']) for j in s['registered_jobs']}
 assert o['root_independent_complete']==o['machine_and_prior_complete']==46
 assert set(s['autonomous_training_v1']['occupied_job_ids'])==set(o['capacity']['occupied'])
 active=[]
 for job in s['registered_jobs']:
  jid=str(job['job_id']);d.check_observed_identity(job,o['observation']['rows'][jid],o['observation']['queue'].get(jid),c.TERMINAL)
  if jid not in o['capacity']['occupied']:continue
  inv=R/job['invocation'];assert h(inv)==job['invocation_sha256']
  runtime_inv=P/job['invocation'];assert h(runtime_inv)==job['invocation_sha256']
  p=P/'results/slurm'/('cti-formal_'+jid+'.out');assert p.is_file() and not p.is_symlink()
  st=p.stat();offset=max(0,st.st_size-16384)
  with p.open('rb') as f:f.seek(offset);raw=f.read(st.st_size-offset)
  assert len(raw)==st.st_size-offset
  rel=B+'/active_log_tails/'+jid+'.txt';dest=R/rel;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(raw)
  updates=[]
  for line in raw.decode(errors='replace').splitlines():
   try:v=json.loads(line)
   except ValueError:continue
   if isinstance(v,dict) and isinstance(v.get('update'),int) and v.get('arm') in ('A','B'):updates.append(v)
  last=updates[-1] if updates else None
  active.append(dict(job_id=jid,suite=job['suite'],budget=job['visual_tokens'],seed=job['training_seed'],invocation=job['invocation'],invocation_sha256=job['invocation_sha256'],source=str(p),tail_offset=offset,tail_end=st.st_size,source_mtime_ns=st.st_mtime_ns,tail={'path':rel,'sha256':h(dest)},last_printed_update=last,source_is_live=True,not_a_checkpoint_or_terminal_review=True))
 now=datetime.now(timezone.utc).isoformat()
 receipt=save(B+'/active_evidence.json',dict(schema='formal_main_v2',utc=now,registered_scheduler_identities_checked=len(s['registered_jobs']),active=active,old_results_not_recomputed=True,scientific_settings_changed=False,initial_observation_sha256=h(op)))
 assert h(sp)==before
 print(json.dumps(dict(receipt=receipt,active=[dict(job_id=x['job_id'],arm=x['last_printed_update'].get('arm') if x['last_printed_update'] else None,update=x['last_printed_update'].get('update') if x['last_printed_update'] else None) for x in active],new_submissions=0,state_unchanged=True)))

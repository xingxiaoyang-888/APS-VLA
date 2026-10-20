from pathlib import Path
import hashlib,json,fcntl,os
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0225';D=R/'.local/spatial_object_collect_20261020T1825'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def safe(p):assert p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]);return p
def put(p,raw):
 safe(p);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw;return
 with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
with (R/'results/experiment_supervisor/.writer.lock').open('a+b') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read(sp);assert s['pending_submission'] is None
 rows=[]
 for suite,msha in [('Spatial','46bcb8468da5a8c5b51ef7fc0f3e99c9d1623e6a206a0115b2314672e7556ef9'),('Object','727205f6ddfae3506f7260e57fde5ca68a8dbc2798549654672cbe2307c0abe5')]:
  mp=D/suite/'plan_v1/publication_map.json';assert h(mp)==msha;v=read(mp);plan=read(D/suite/'plan_v1/effective_plan.json');inv=plan['invocation']
  assert inv['stage']=='collect' and inv['suite']=='libero_'+suite.lower() and inv['method_ids']==['dense'] and inv['resume'] is False and inv['final_values_read_locally'] is False and not inv['prior_job_ids']
  dest='results/formal_main_v2/execution/'+suite.lower()+'_collect_action_v1_20261020T1825/'
  new=[x for x in v['files'] if not x['R_present_exact']]
  assert {x['canonical_path'] for x in new}=={dest+n for n in ['scientific_plan.json','execution_contract.json','effective_plan.json']}
  for row in v['files']:
   source=safe(R/row['candidate_path']);assert h(source)==row['sha256'] and source.stat().st_size==row['bytes']
   for root in [R,P]:
    target=safe(root/row['canonical_path'])
    if row in new:put(target,source.read_bytes())
    assert h(target)==row['sha256']
   rows.append(row)
 assert h(sp)==before
 receipt={'schema':'formal_main_v2','status':'static_source_only_published','maps':[{'path':str(D/suite/'plan_v1/publication_map.json'),'sha256':h(D/suite/'plan_v1/publication_map.json')} for suite in ['Spatial','Object']],'files':rows,'new_files_each_root':6,'final_values_read':False,'production_state_unchanged':True,'state_sha256':before,'new_GPU_jobs':0,'runtime_readiness_authorized':False,'submission_authorized':False,'utc':datetime.now(timezone.utc).isoformat()}
 out=B/'Spatial_Object_collect_plan_publication.json';put(out,(json.dumps(receipt,sort_keys=True,indent=2)+'\n').encode());print(json.dumps({'path':str(out.relative_to(R)),'sha256':h(out)}))

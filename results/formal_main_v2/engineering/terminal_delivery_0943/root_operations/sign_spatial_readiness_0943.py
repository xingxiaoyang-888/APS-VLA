from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D='results/formal_main_v2/execution/action_spatial_resume_0943'
B='results/formal_main_v2/preflight/heartbeat_20261019T1743'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def read(rel):return json.loads((R/rel).read_bytes())
def write(rel,obj):
 raw=(json.dumps(obj,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode()
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw
 else:
  with p.open('xb') as f:f.write(raw)
 return ref(rel)
def cp(src,dst,pin):
 a=R/src;b=R/dst;assert h(a)==pin
 b.parent.mkdir(parents=True,exist_ok=True)
 if b.exists():assert h(b)==pin
 else:
  with b.open('xb') as f:f.write(a.read_bytes())
 return ref(dst)
gp='scripts/ops/formal_action_deployment_v1/gateway.py'
assert h(R/gp)=='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a'
sp=importlib.util.spec_from_file_location('spatial0943_gateway',R/gp);g=importlib.util.module_from_spec(sp);sys.modules[sp.name]=g;sp.loader.exec_module(g)
c=g.load(R/g.CONTROLLER,g.CONTROLLER_SHA,'spatial0943_controller')
with c.exclusive_lock(R/g.STATE.parent if False else R/'results/experiment_supervisor/.writer.lock'):
 origins=[]
 for folder,pin in [('action_actual_plan_0943','f50e95e7391877d772e8b84f24b0c0e02f65238e71b3ef15e8f43453a8a5d921'),('action_actual_plan_independent_0943','c256299213b8e73de226e7ef3bc14e9759cd54a85b91845d1f4da328612e6295')]:
  src='.local/'+folder;man=read(src+'/archive_closure.json');assert h(R/src/'archive_closure.json')==pin
  files=man['files']
  if isinstance(files,dict):files=[dict(path=k,**v) for k,v in files.items()]
  files=files+[dict(path='archive_closure.json',sha256=pin,bytes=(R/src/'archive_closure.json').stat().st_size)]
  for f in files:
   assert '/' not in f['path'] and '\\' not in f['path']
   s=src+'/'+f['path'];dst='results/formal_main_v2/engineering/action_actual_plan_delivery_0943/'+folder+'/'+f['path']
   assert (R/s).stat().st_size==f['bytes']
   x=cp(s,dst,f['sha256']);origins.append(dict(source=s,archive=x,bytes=f['bytes']))
 write(B+'/action_plan_archive_origin_map.json',dict(schema='formal_main_v2',files=origins,originals_retained=True))
 ind=cp('.local/action_actual_plan_independent_0943/actual_plan_independent_review.json',D+'/plan_independent_review.json','37a9a8afec7975a49461de1d5855779488bfa40f2368939f1e6e2bb9d1baaabc')
 iv=read(ind['path'])
 assert iv['status']=='passed' and iv['actual_GPU_runtime_chain_verified'] is False and iv['allowed_stages']==['development']
 for n,pin in iv['files'].items():assert h(R/n)==pin,n
 for n,pin in iv['inherited_engineering_GPU_evidence'].items():assert h(R/n)==pin,n
 ready=read('.local/action_actual_plan_0943/runtime_readiness_draft.json')
 assert h(R/'.local/action_actual_plan_0943/runtime_readiness_draft.json')=='3dbf2a4eac17d1f33766a2d8cbc5b89280bf223de8ec52293214e44afd805738'
 for k in ['effective_plan','scientific_plan','action_execution_contract']:
  assert ref(ready[k]['path'])==ready[k]
 action=read(ready['action_execution_contract']['path']);assert action['files']==ready['runtime_sources']==iv['runtime_sources']
 for n,pin in ready['runtime_sources'].items():assert h(R/n)==pin
 now=datetime.now(timezone.utc).isoformat()
 root=write(D+'/plan_root_review.json',dict(schema='formal_main_v2',kind='formal_action_development_plan_root_review',status='passed',reviewed_by='root',utc=now,
  execution_version='formal-downstream-action-v1',production_chain_complete=True,
  production_chain_complete_meaning='Exact development plan pre-execution control and source closure validated; not a completed actual GPU runtime chain.',
  actual_GPU_runtime_chain_verified=False,scientific_trials_completed_by_new_runtime=0,
  runtime_sources=ready['runtime_sources'],effective_plan=ready['effective_plan'],scientific_plan=ready['scientific_plan'],action_execution_contract=ready['action_execution_contract'],
  independent_review=ind,allowed_stages=['development'],forbidden_stages=ready['forbidden_stages'],old_new_outcome_equivalence_established=False,
  O2A_enabled=False,global_freeze_enabled=False,final_evaluation_enabled=False,scientific_settings_changed=False,
  original_terminal_trials_preserved=12,maximum_new_trial_ids=588,transition=action['transition'],
  root_hash_verified=list(iv['files']),inherited_GPU_engineering=iv['inherited_engineering_GPU_evidence'],
  limitation='Mixed old-prefix O2A/freeze join remains blocked until an explicit separately reviewed guard/equivalence treatment.'))
 ready.update(status='passed',active=True,reviewed_by='root',root_review=root,independent_review=ind,production_chain_complete=True,raw_consumer_ready=True,
  actual_GPU_runtime_chain_verified=False,scientific_trials_completed_by_new_runtime=0,production_chain_complete_meaning=read(root['path'])['production_chain_complete_meaning'],utc=now,
  pending_runtime_publication_roles=[])
 ready['runtime_publication_files'].update({root['path']:root['sha256'],ind['path']:ind['sha256']})
 rr=write(D+'/runtime_readiness.json',ready)
 prepared=read('.local/action_actual_plan_0943/prepared_invocation_template.json')
 prepared.update(registered_utc=now,runtime_readiness=rr)
 pr=write(D+'/prepared_invocation.json',prepared)
 auth=read('.local/action_actual_plan_0943/submission_authorization_draft.json')
 auth.update(status='approved_for_exactly_one_registered_downstream_submission',runtime_readiness=rr,prepared_invocation=pr,approved_utc=now,reviewed_by='root')
 reserve=read('.local/action_actual_plan_0943/reservation_root_record_draft.json')
 reserve.update(status='approved_for_exact_downstream_request',authorization_intent_sha256=g.intent_sha(auth),approved_utc=now,reviewed_by='root')
 rv=write(D+'/reservation_root_record.json',reserve)
 auth['root_reservation']=rv
 ar=write(D+'/submission_authorization.json',auth)
 a,e,plan,science,prepared=g.validate_authorization(R,ar)
 state_sha=c.file_sha(R/g.STATE);state=c.read_json(R/g.STATE)
 bundle=g.FrozenPlan(R,a,e,plan,science,prepared).prepare(state)
 pubs=dict(ready['runtime_publication_files']);pubs[rr['path']]=rr['sha256'];bundle['readiness_files']=pubs
 io=g.NativeIO(R).preflight(bundle);e.unchanged();assert state_sha==c.file_sha(R/g.STATE)
 review=write(B+'/spatial_root_pre_execution_check.json',dict(status='passed_metadata_IO_only_not_reserved_or_submitted',authorization=ar,
  reservation=rv,state_sha256=state_sha,checked_runtime_files=len(io['checked_files']),missing_publications=io['missing_publications'],
  actual_GPU_runtime_chain_verified=False,scientific_trials_completed_by_new_runtime=0,allowed_stages=['development'],
  scientific_settings_changed=False,legacy_refresh_called=False))
 print(json.dumps(dict(authorization=ar,reservation=rv,readiness=rr,root_preflight=review,missing_publications=len(io['missing_publications']),submitted=False)))

from pathlib import Path
import json,hashlib,importlib.util,sys
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B=R/'results/formal_main_v2/preflight/heartbeat_20261020T0122'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
index=R/'.local/canonical_review_alias_1722/request_index.json';assert h(index)=='edf039c611e0b29a6bc2570ccd0c47778b5df3ecd9f734ab2b7059f61cf6e7e4'
requests=json.loads(index.read_text())['requests'];assert [x['job_id'] for x in requests]==['3034580','3034584','3034597','3034604','3034611','3034616','3034689']
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','canon1722ctl')
reviewer=load('scripts/review_formal_segment.py','566408f7f72bd3d878204175573a9c08b01db67be69358ed4a8ac2d0e0603790','canon1722original')
results=[]
for req in requests:
 with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
  statep=R/'results/experiment_supervisor/state.json';before=h(statep);s=json.loads(statep.read_text());assert s['pending_submission'] is None
  for key in ['existing_terminal_root','existing_independent_review','source_inventory_ref','pull_receipt_ref','original_reviewer']:
   ref=req[key];assert h(R/ref['path'])==ref['sha256']
  for ref in req['small_terminal_products_rehashed']:assert h(R/ref['path'])==ref['sha256']
  call=req['original_review_call'];assert call['root']==str(R) and call['verify_server_resume'] is True and call['job_id']==req['job_id']
  assert not (R/req['canonical_target']).exists()
  value=reviewer.review(call['job_id'],source_inventory=call['source_inventory'],pull_receipt=call['pull_receipt'],verify_server_resume=True,root=R)
  assert value['status']=='passed' and value['kind']=='root_segment_review' and value['job_id']==req['job_id']
  assert value['completed_by_arm']==dict(A=5000,B=5000) and value['allowed_next_segment_end'] is None and value['optimizer_rng_deserialized'] is False
  assert json.loads((R/req['canonical_target']).read_text())==value and h(statep)==before
  results.append(dict(pair_key=req['pair_key'],job_id=req['job_id'],canonical_review=dict(path=req['canonical_target'],sha256=h(R/req['canonical_target'])),existing_independent_review=req['existing_independent_review'],completed_by_arm=value['completed_by_arm'],registered_pair_GPU_seconds=value['pair_allocated_gpu_seconds'],server_resume_checks=value['server_resume_checks'],state_unchanged=True))
  target=B/('canonical_reconstruction_'+req['job_id']+'.json')
  with target.open('x') as f:json.dump(results[-1],f,sort_keys=True,indent=2);f.write('\n')
  print(json.dumps(dict(job_id=req['job_id'],status='original_review_passed',canonical=req['canonical_target'])),flush=True)
out=B/'canonical_reconstruction_summary.json'
with out.open('x') as f:json.dump(dict(schema='formal_main_v2',kind='root_original_review_canonical_reconstruction',utc=datetime.now(timezone.utc).isoformat(),status='passed',requests=dict(path=index.relative_to(R).as_posix(),sha256=h(index)),results=results,new_completed_training_groups=0,existing_root_independent_groups_unchanged=True,independent_evidence_mode='Existing per-pair independent raw reviews retained; this is a new root original-review reconstruction, not a new independent audit.',GPU_submissions=0,source_changed=False,weights_copied=False),f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps(dict(receipt=out.relative_to(R).as_posix(),sha256=h(out),canonical_count=len(results))))

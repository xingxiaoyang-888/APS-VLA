from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/spatial_collect_reconcile_independent_20261020T1825'
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
def save(name,v):
 p=D/name
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
sp=ref(D/'post_reconciliation_independent_review.json');ob=ref(D/'Object3053518/post_reconciliation_independent_review.json')
assert sp['sha256']=='441182c132b6d399f54fce44baca3ab4646149762e981474527690a9ce4cc76a'
assert ob['sha256']=='05ad607d1827ff554b62d96604a2e8434e68447d07430305e21786084e721abe'
transports=[]
for n in ['Spatial3053503_independent_known_submission1825_v1','Spatial3053503_independent_helper1825_v1','Spatial3053503_independent_helper1825_v2','Spatial3053503_independent_helper1825_v3','Spatial3053503_independent_post1825_v1','Object3053518_independent_known_submission1825_v1','Object3053518_independent_helper1825_v1','Object3053518_independent_post1825_v1']:
 transports.append(ref(R/'results/formal_main_v2/control_transport'/(n+'.jsonl')))
compact=save('compact_handoff.json',dict(schema='formal_main_v2',status='two_exact_known_collect_submissions_reconciled_and_independently_post_checked',created_utc=datetime.now(timezone.utc).isoformat(),jobs={'3053503':dict(suite='libero_spatial',post_review=sp,helper_review=ref(D/'helper_source_independent_review.json'),original_ACK_count=1,root_reconcile_new_submission_calls=0,allocation_seconds_observed=363),'3053518':dict(suite='libero_object',post_review=ob,helper_review=ref(D/'Object3053518/helper_source_independent_review.json'),original_ACK_count=1,root_reconcile_new_submission_calls=0)},retained_guard_failures=['Spatial helper v1 original pending guard rejection','Spatial helper v2 original existing invocation guard rejection'],accepted_bounded_resolution='Verify pinned original preflight, original exact prepared invocation/argv and all frozen/runtime inputs; reconcile known ACK identity through original gateway; do not call new planning or submit again.',runtime_state_change='Each root CAS appends exactly one known job, consumes matching reservation/pending, recomputes all allocated cost; all historical registry and scientific fields unchanged.',no_double_count_cost=True,collect_success_or_outputs_accepted_here=False,weights_or_final_values_read=False,independent_GPU_seconds=0,independent_Slurm_submissions=0,independent_production_state_writes=0,full_state_hash_reconstruction_matches_each_root_committed_receipt=True,later_root_transactions_not_overwritten=True,external_transport_refs=transports))
files=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  assert p.suffix not in {'.pt','.pth','.ckpt','.safetensors','.bin','.pkl','.pickle'}
  files.append(ref(p))
manifest=save('delivery_manifest.json',dict(schema='formal_main_v2',kind='Spatial_Object_collect_known_ACK_reconciliation_independent_delivery',created_utc=datetime.now(timezone.utc).isoformat(),files=files,file_count=len(files),total_bytes=sum(x['bytes'] for x in files),external_transport_refs=transports,compact_handoff=compact,all_rejected_helpers_and_audits_retained=True,new_GPU_seconds=0,production_state_writes=0,Slurm_submissions=0))
print(json.dumps({'manifest':manifest,'handoff':compact,'Spatial_post':sp,'Object_post':ob,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files)},ensure_ascii=False))

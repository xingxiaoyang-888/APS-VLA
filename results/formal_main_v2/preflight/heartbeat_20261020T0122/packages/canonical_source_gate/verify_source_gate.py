from pathlib import Path
from datetime import datetime,timezone
import importlib.util,hashlib,json,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/canonical_source_gate_1722'
REF='results/formal_main_v2/preflight/heartbeat_20261020T0122/canonical_reconstruction_summary.json'
REF_SHA='ec6cf8153c0eda0d8b14a02c6d99d0fa038648443a5a2ead9a9ffa51cd66e0ac'
HELPER='scripts/formal_execution_manifests.py';HELPER_SHA='614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(R/HELPER)==HELPER_SHA and sha(R/REF)==REF_SHA
spec=importlib.util.spec_from_file_location('actual_frozen_formal_execution_manifests',R/HELPER);helper=importlib.util.module_from_spec(spec);exec(compile((R/HELPER).read_bytes(),str(R/HELPER),'exec'),helper.__dict__)
e=helper.Evidence(R);e.watch(HELPER);root=e.read(REF);assert root['status']=='passed' and len(root['results'])==7
source='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';sources=helper.source_contract(e,source);reg=helper.registration_contract(e,'configs/experiments/formal_main_v2.json')
methods={};canonical=[]
for row in root['results']:
 r=row['canonical_review'];assert e.watch(r['path'])==r['sha256'];doc=e.read(r['path']);ind=row['existing_independent_review'];assert e.watch(ind['path'])==ind['sha256']
 assert doc['kind']=='root_segment_review' and doc['status']=='passed' and doc['job_id']==row['job_id'] and doc['completed_by_arm']=={'A':5000,'B':5000}
 for arm in ['A','B']:methods.setdefault(doc['suite'],[]).append(f"{arm}{doc['visual_tokens']}_seed{doc['seed']}")
 canonical.append({'pair_key':row['pair_key'],'canonical_review':r,'existing_independent_review':ind,'source_review_rebuilt_by_root':True,'new_independent_full_training_audit_claimed':False})
outputs=[]
try:
 for suite,ids in methods.items():
  print('BEGIN',suite,len(ids),flush=True)
  rows=helper.suite_rows(e,reg,suite,sources,ids)
  assert {r['identity']['method_id'] for r in rows}==set(ids)
  provenance=e.source_provenance[suite]
  assert provenance['status']=='verified'
  p=D/(suite+'_validated_rows.json')
  with p.open('x') as f:json.dump({'suite':suite,'methods':rows,'source_provenance':provenance,'not_an_execution_authorization':True},f,ensure_ascii=False,indent=2);f.write('\n')
  outputs.append({'suite':suite,'method_ids':[r['identity']['method_id'] for r in rows],'row_count':len(rows),'result_file':p.relative_to(R).as_posix(),'sha256':sha(p),'actual_API':'formal_execution_manifests.suite_rows -> source_provenance_for_rows -> formal_asset_downstream_review._pair_source','status':'passed_actual_original_source_gate'})
  print('PASSED',suite,len(rows),flush=True)
 e.unchanged()
 result={'schema':'formal_main_v2','kind':'post_canonical_publication_source_gate_review','status':'passed_actual_original_suite_rows','utc':datetime.now(timezone.utc).isoformat(),'root_reconstruction':{'path':REF,'sha256':REF_SHA},'helper':{'path':HELPER,'sha256':HELPER_SHA},'pair_count':len(canonical),'method_count':sum(o['row_count'] for o in outputs),'canonical_root_and_retained_independent_refs':canonical,'outputs':outputs,'source_gate_blocker_resolved':True,'new_completed_training_groups':0,'new_independent_full_training_audit_claimed':False,'claims_scope':'Post-publication consumption of newly reconstructed root reviews through original source/acceptance/selected-pair/provenance gates; the earlier independent full training review remains at its original identity.','limits':{'GPU_runs':0,'Slurm_calls':0,'checkpoint_bytes_read_or_deserialized':False,'sealed_state_values_read':False,'state_P_Git_or_canonical_written':False,'readiness_or_release_created':False},'evidence_sha256':dict(e.files)}
 with (D/'source_gate_review.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'status':result['status'],'pairs':len(canonical),'methods':result['method_count'],'evidence_refs':len(e.files)},ensure_ascii=False),flush=True)
except Exception as err:
 with (D/'source_gate_failure.json').open('x') as f:json.dump({'status':'failed','exception':type(err).__name__,'message':str(err),'traceback':traceback.format_exc(),'completed_outputs':outputs,'evidence_sha256':dict(e.files)},f,ensure_ascii=False,indent=2)
 raise

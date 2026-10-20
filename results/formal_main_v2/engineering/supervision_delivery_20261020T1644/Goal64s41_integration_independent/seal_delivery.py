from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/Goal64s41_integration_independent_20261020T1644';V=R/'.local/Goal64s41_integration_preview_20261020T1644'
def pin(p,expected=None):
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest();assert expected is None or h==expected
 return dict(path=p.relative_to(R).as_posix(),sha256=h,bytes=len(b))
def put(p,data):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(data)
def js(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
pre=pin(D/'preview_independent_review.json','dc5588333a9a7862aa4cfcd60ab21c54b011aebc0f169e0604671e51804977f6');post=pin(D/'post_independent_review.json','03f63092f2a23906a3b256b0cae64a8e524ede59d1ff178d466806c3b5c4f292')
a=json.loads((R/pre['path']).read_bytes());b=json.loads((R/post['path']).read_bytes());assert a['status']==b['status']=='passed'
# Preserve all private preview inputs required to reproduce the audits in this delivery.
original_preview_files=[]
for path in sorted(V.rglob('*')):
 if not path.is_file():continue
 reference=pin(path);assert a['read_evidence_sha256'][reference['path']]==reference['sha256']
 dest=D/'preview_inputs'/path.relative_to(V);put(dest,path.read_bytes());original_preview_files.append({'original':reference,'delivered':pin(dest)})
summary={'schema':'formal_main_v2','status':'pre_and_post_independent_passed','scope':'Goal64seed41 completed training root state/document integration only','preview':pre,'post':post,'preview_checks':a['check_count'],'post_checks':b['check_count'],'actual_summary':b['actual_summary'],'actual_completion':b['actual_completion'],'actual_intent':b['actual_intent'],'result':b['result'],'controller_only_observed_subsequent_tick':b['later_controller_tick_differences'],'Goal_new_scientific_development_scope_hold_unchanged':True,'Object_bridge_scientific_admission':False,'final_release':False,'new_GPU_jobs':0,'canonical_state_docs_Git_Slurm_writes_by_auditor':False,'root_may_integrate_bound_post_status':True,'private_preview_inputs_preserved':original_preview_files}
put(D/'handoff_summary.json',js(summary))
logs=[pin(R/'results/formal_main_v2/control_transport'/f) for f in ['Goal64s41_integration_preview_independent_20261020T1644.jsonl','Goal64s41_integration_post_independent_20261020T1644.jsonl']]
files=[pin(p) for p in sorted(D.rglob('*')) if p.is_file()]
manifest={'schema':'formal_main_v2','kind':'independent_integration_delivery_manifest','status':'sealed','utc':datetime.now(timezone.utc).isoformat(),'scope':summary['scope'],'files':files,'external_execution_audits':logs,'pre_review':pre,'post_review':post,'weights_copied':False,'final_values_read':False,'no_canonical_mutation':True}
put(D/'delivery_manifest.json',js(manifest))
print(json.dumps({'manifest':pin(D/'delivery_manifest.json'),'summary':pin(D/'handoff_summary.json'),'files':len(files),'bytes':sum(f['bytes'] for f in files)}))

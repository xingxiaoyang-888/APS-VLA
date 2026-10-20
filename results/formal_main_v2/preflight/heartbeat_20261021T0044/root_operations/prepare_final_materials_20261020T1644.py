from pathlib import Path
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0044';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1644'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(n):return dict(path=n,sha256=h(R/n))
state=json.loads((R/'results/experiment_supervisor/state.json').read_bytes());assert state['formal_main_progress']['last_terminals_integrity_review_20261020T1644']['status']=='passed'
receipts=['evidence_delivery_initial.json','root_post_integration_acceptance.json','Object_author_delivery.json','Goal_prefix58_candidate_delivery.json','Object_and_Goal_independent_delivery.json','last_training_and_development_independent_delivery.json','final_delivery_scope_package_delivery.json','last_terminal_integration_independent_delivery.json','last_training_lossless_archive.json']
archive=[ref(B+'/'+n) for n in receipts]
roots=[ref(p.relative_to(R).as_posix()) for p in sorted((R/'.local').glob('*1644*.py')) if p.is_file()]
for name in ['archive_author_inputs_20261020T1644.json','archive_last_terminal_inputs_20261020T1644.json','archive_scope_package_20261020T1644_inputs.json','archive_post_package_20261020T1644_inputs.json']:
 roots.append(ref('.local/'+name))
x=dict(status='root_reviewed_delivery_materials',archive_receipts=archive,additional_root_files=roots,Goal_independent_review=dict(path=E+'/Goal_prefix58_independent/attempt02/independent_review.json',sha256='24398f0dfb160bb2ee1aa3ef5cfada40427798eb867dd56f9d7479e51a8bb604'),delivery_scope=dict(path='.local/root_delivery_scope_20261020T1644.json',sha256='0401ab1f1a6b06716730fa70f8363a3e189c3737f8720309fa81cc861eba9a3c'))
for z in [x['Goal_independent_review'],x['delivery_scope']]:assert h(R/z['path'])==z['sha256']
p=R/'.local/final_delivery_materials_20261020T1644.json';assert not p.exists();p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+chr(10))
print(json.dumps(dict(materials=ref(p.relative_to(R).as_posix()),archive_receipts=len(archive),root_files=len(roots))))

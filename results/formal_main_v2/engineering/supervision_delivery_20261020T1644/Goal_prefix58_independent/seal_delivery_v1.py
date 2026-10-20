"""Seal independent evidence inventory; does not modify any source under review."""
from pathlib import Path
import hashlib,json,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent;A=R/'.local/goal_prefix58_candidate_20261020T1644'
def h(p):
 digest=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):digest.update(block)
 return digest.hexdigest()
assert not (D/'delivery_manifest.json').exists()
assert h(A/'delivery_manifest.json')=='9a2f425a7d6e715c6a108a400bd1a92fe713e2b368bdc3a2ab2e0e3a4da76595'
author=json.loads((A/'delivery_manifest.json').read_text());assert all(h(A/r['path'])==r['sha256'] for r in author['files'])
assert h(D/'handoff_summary.json')=='6f4ec0425e1950a403a6ac4d0537d519a077b25fbe9a5443d9b0b04b53468217'
name='goal_prefix58_independent_package_v1_20261020T1644.jsonl';source=R/'results/formal_main_v2/control_transport'/name;dest=D/'transport'/name
with dest.open('xb') as f:f.write(source.read_bytes())
assert h(source)==h(dest)
files=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  assert p.resolve().is_relative_to(D) and not p.is_symlink()
  files.append({'source':str(p.relative_to(R)),'path':str(p.relative_to(D)),'sha256':h(p),'bytes':p.stat().st_size})
manifest={'schema':'formal_main_v2','kind':'independent_goal_prefix58_complete_delivery_manifest','status':'completed_with_findings_not_GPU_ready','source_root':str(D),'files':files,'file_count':len(files),'total_bytes':sum(r['bytes'] for r in files),'scope':'All private auditor scripts, both test attempts, intentional counterexamples, raw synthetic fixtures, own harness/bootstrap failures, exact prior transport audit copies, metadata bindings and lossless optional tiny-blob archive. Manifest excludes itself.','weights_included':False,'sealed_state_values_read':False,'new_GPU_jobs':0,'scientific_trials_added':0,'HOLD_unchanged':True,'unqualified_safety_pass':False,'tiny_blob_delivery_option':{'archive':'synthetic_blobs_lossless.tar.gz','member_manifest':'synthetic_blobs_member_manifest.json','members':460,'originals_retained':True,'root_may_copy_lossless_archive_in_place_of_individual_blobs':True},'final_sealing_transport_audit_external':'results/formal_main_v2/control_transport/goal_prefix58_independent_seal_v1_20261020T1644.jsonl','final_sealing_transport_note':'Transport completes after this manifest is written; final sealing audit remains outside the sealed private directory. Root can archive its completed original separately.'}
p=D/'delivery_manifest.json'
with p.open('x') as f:json.dump(manifest,f,sort_keys=True,indent=2,ensure_ascii=False);f.write('\n')
assert all((D/r['path']).stat().st_size==r['bytes'] and h(D/r['path'])==r['sha256'] for r in files)
print(json.dumps({'manifest':str(p.relative_to(R)),'sha256':h(p),'files':len(files),'bytes':manifest['total_bytes'],'status':manifest['status']}))

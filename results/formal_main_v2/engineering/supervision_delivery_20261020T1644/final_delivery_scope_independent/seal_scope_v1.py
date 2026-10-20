from pathlib import Path
import json, hashlib, datetime
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/final_delivery_scope_20261020T1644'
def ref(p):
 b=p.read_bytes(); return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(p,o):
 assert not p.exists(),str(p)
 p.write_text(json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
candidate=ref(D/'additional_exact_candidate_v2.json')
assert candidate['sha256']=='f5257769fc3f6dde3c2694e456b41730472cecdb92d3785cf3cdf3adff20187d'
o=json.loads((D/'additional_exact_candidate_v2.json').read_text())
assert o['checks']==6431 and o['candidate_files']==236
assert not o['unbound_changes_requiring_separate_root_scope']
assert not o['Git_index_commit_push_mutated'] and not o['canonical_state_Slurm_mutated']
assert not o['weights_or_sealed_values_read'] and o['source173_unchanged']
transports=[]
for name,sha,rc in [('final_delivery_scope_20261020T1644_v1.jsonl','81d83453a7edc9c2bffce692142b45458c92ed317f21f3453e3e4d9622f65a74',1),('final_delivery_scope_20261020T1644_v2.jsonl','63ab0705408faa6fce4a1122e4c5180f86a0fb046253465063a22e8fa0e0958a',0)]:
 p=R/'results/formal_main_v2/control_transport'/name
 r=ref(p); assert r['sha256']==sha
 rows=[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
 assert rows[-1]['event']=='control_end' and rows[-1]['returncode']==rc and rows[-1]['source173_and_entrypoint_unchanged'] is True
 q=D/'closed_transport'/name; q.parent.mkdir(exist_ok=True); assert not q.exists(); q.write_bytes(p.read_bytes())
 assert ref(q)['sha256']==sha
 transports.append({'original':r,'private_copy':ref(q),'returncode':rc})
sealing_transport='results/formal_main_v2/control_transport/final_delivery_scope_seal_20261020T1644_v1.jsonl'
handoff={'schema':'cti_final_delivery_scope_independent_handoff_v1','status':'private_candidate_scope_ready_for_root_review_not_Git_authorization','candidate':candidate,'checks':6431,'files':236,'bytes':o['candidate_bytes'],'category_summary':o['category_summary'],'baseline':o['baseline'],'pending_canonical_independent_publications':o['pending_exact_root_publications'],'exact_gitignore_exceptions':o['exact_gitignore_exceptions'],'raw_exclude_all9':o['raw_exclude_all9'],'root_archive_guard_snapshot':o['root_archive_guard_snapshot'],'root_must_replace_old_Goal41_only_SNAPSHOT_and_RAW_guards_in_its_existing_delivery_helper':True,'root_must_append_later_canonical_independent_and_postintegration_refs_exactly':True,'failed_attempt_preserved':{'source':ref(D/'build_scope_v1.py'),'failure':ref(D/'scope_failure_v1.json'),'reason':'The independent harness incorrectly expected root_reconciliation boolean true. The real committed receipt binds an exact path/sha256 reference. v2 verifies that exact reference, preserving the original failed test and source diff.'},'passing_attempt':{'source':ref(D/'build_scope_v2.py'),'diff':ref(D/'v1_to_v2.diff')},'closed_transport':transports,'root_handles_B_E_recursively_and_closed_global_transports':True,'sealing_transport_outside_manifest_because_it_closes_after_this_entrypoint':sealing_transport,'Git_mutations':False,'canonical_state_or_Slurm_mutations':False,'weights_or_sealed_values_read':False,'scope_not_scientific_acceptance':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
write(D/'handoff.json',handoff)
files=[ref(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json']
manifest={'schema':'cti_private_delivery_manifest_v1','status':'sealed_private_candidate','root':D.relative_to(R).as_posix(),'files':files,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'candidate':candidate,'handoff':ref(D/'handoff.json'),'sealing_transport_external':sealing_transport,'no_canonical_state_Git_Slurm_mutations':True}
write(D/'delivery_manifest.json',manifest)
print(json.dumps({'manifest':ref(D/'delivery_manifest.json'),'handoff':ref(D/'handoff.json'),'files':len(files),'bytes':manifest['total_bytes']},ensure_ascii=False))

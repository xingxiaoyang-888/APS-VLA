"""Exact known supervisor metadata filename mapping review, never environment-state access."""
from pathlib import Path
import ast,difflib,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent
B='results/formal_main_v2/preflight/heartbeat_20261021T0910';checks=[];refs={}
def ck(n,v):
 checks.append(dict(name=n,passed=bool(v)));assert v,n
def raw(n,h):
 b=(R/n).read_bytes();ck('sha/'+n,hashlib.sha256(b).hexdigest()==h);refs[n]=dict(sha256=h,bytes=len(b));return b
v5=raw('.local/deliver_20261021T0110_v5.py','a46e639d89543aa2c943d6d404e60b7dfcd4cf064da8c1ac0ac792a20313335f').decode()
v6=raw('.local/deliver_20261021T0110_v6.py','be079cffcfcc70dba489400f77947f881d3191d409a514f06be3594612fec3fa').decode();ast.parse(v6)
oldsave=" with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\\n')"
newsave=" b=(json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\\n').encode()\n if p.exists():assert p.read_bytes()==b,n\n else:p.open('xb').write(b)"
ck('only_exact_identical_existing_receipts_reused',v6.count(newsave)==1)
start=v6.index(" alias_original=B+'/final_state_before.json';alias_target=B+'/supervisor_snapshot_before.json'")
stop=v6.index(' selected=[];unknown=[]',start);block=v6[start:stop]
normal=v6[:start]+v6[stop:]
normal=normal.replace(newsave,oldsave).replace("'.local/deliver_20261021T0110_v6.py',",'').replace('root_operation_sources_v3.json','root_operation_sources_v2.json').replace('if n in old or n in opened or n==alias_original:continue','if n in old or n in opened:continue').replace("'operational_snapshot_mapping':ref(B+'/operational_snapshot_filename_mapping.json'),",'')
ck('entire_remaining_v6_exactly_v5',normal==v5)
ck('unique_original_pin_and_typed_input_ref',all(t in block for t in ["'2e53569c6435abd3fc9d1d9898d33938205c4ddef916938ac4b6af632202f104'","rd(B+'/final_snapshot_inputs.json')['state_before']['path']==alias_original","rd(alias_original)['formal_main_progress']['completed_final_trials']==0","rd(alias_original)['formal_main_progress']['test_opened'] is False"]))
ck('guard_still_applied_to_repository_target',"guard.lexical(alias_target);cp(alias_original,alias_target)" in block)
ck('original_not_deleted_or_rewritten',"n==alias_original:continue" in v6 and not any(x in block for x in ['unlink(','.rename(','.replace(','write_bytes','write_text']))
ck('copy_no_links_and_identical_only',all(t in v6 for t in ["p.resolve()==p and q.resolve()==q","not any(x.is_symlink()","if q.exists():assert q.read_bytes()==p.read_bytes()","q.open('xb').write(p.read_bytes())"]))
ck('mapping_preserves_original_and_target_refs',all(t in block for t in ['original_server_reference=ref(alias_original)','repository_copy=ref(alias_target)','sealed_initial_state_values_read=False','scientific_state_unchanged=True']))
guard=raw('scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6').decode()
ck('lexical_state_boundary_unmodified',all(t in guard for t in ['"init_state", "initial_state", "final_state", "test_state"','"State-value metadata forbidden"']))
before_raw=raw(B+'/final_state_before.json','2e53569c6435abd3fc9d1d9898d33938205c4ddef916938ac4b6af632202f104');before=json.loads(before_raw)
state=json.loads(raw('results/experiment_supervisor/state.json','bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa'))
inputs=json.loads(raw(B+'/final_snapshot_inputs.json','d6d25449de538af16bbc562ae26bf8e3d36456f6da0fb147f9e341fae724ad1a'))
summary=json.loads(raw(B+'/final_summary.json','6b7da6a87eada2d6c63ec0b0c357156953edd5132c7407d809755556719388a2'))
prior=json.loads(raw('.local/delivery_independent_20261021T0110/actual_review_v2.json','69434136678f7ce1549de4e5b10c37d5272276263ab75e9ba06effb3debe7d8a'))
raw('.local/delivery_independent_20261021T0110/delivery_manifest.json','78b8538489ffa542b5e0f8d36ab3764d563f6f2e11744d129a9b57d6dd04a890')
raw('.local/delivery_allowlist_independent_20261021T0110/delivery_manifest.json','52bd771077f5c4bfdf2b7829476bacd153565291e2986f5ce8093e935d6f62ab')
ck('known_before_snapshot_bound_to_prior_final_audit',prior['status']=='passed_final_delivery_review' and prior['blockers']==[] and prior['evidence'][B+'/final_state_before.json']['sha256']=='2e53569c6435abd3fc9d1d9898d33938205c4ddef916938ac4b6af632202f104' and inputs['state_before']['path']==B+'/final_state_before.json' and inputs['state_before']['sha256']==inputs['state_before_sha256']=='2e53569c6435abd3fc9d1d9898d33938205c4ddef916938ac4b6af632202f104')
ck('supervisor_metadata_schema_not_environment_panel',before['schema_version']==1 and isinstance(before['registered_jobs'],list) and isinstance(before['formal_main_progress'],dict) and isinstance(before['autonomous_training_v1'],dict) and set(before)==set(state))
ck('registration_metadata_exactly_retained',before['registered_jobs']==state['registered_jobs'] and len(before['registered_jobs'])==303)
ck('original_state_canonical_serialization',before_raw==(json.dumps(before,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode())
ck('scientific_final_state_remains_sealed',before['formal_main_progress']['completed_final_trials']==state['formal_main_progress']['completed_final_trials']==0 and before['formal_main_progress']['trained_arms']==72 and before['formal_main_progress']['test_opened'] is False and before['formal_main_progress']['global_release_created'] is False and summary['final_sealed'] is True)
report=dict(schema='formal_main_v2',kind='bounded_supervisor_snapshot_filename_mapping_review',status='passed_bounded_operational_snapshot_mapping_review',reviewed_by='independent',blockers=[],scope='Exact known supervisor bookkeeping snapshot only; this is not approval to rename environment initial/final-state payloads. No sealed environment-state file was opened. Prior complete delivery and allowlist reviews remain unchanged and are inherited.',checks=list(checks),state_sha256=prior['state_sha256'],summary_sha256='6b7da6a87eada2d6c63ec0b0c357156953edd5132c7407d809755556719388a2',metadata_classification='registered experiment-supervisor state snapshot before final bookkeeping update',exact_original=dict(path=B+'/final_state_before.json',sha256='2e53569c6435abd3fc9d1d9898d33938205c4ddef916938ac4b6af632202f104',bytes=len(before_raw)),exact_repository_copy_target=B+'/supervisor_snapshot_before.json',allowed_copy_requires_identical_bytes=True,original_remains_on_server=True,lexical_guard_changed=False,source173_verification_inherited=True,final_sealed=True,actual_copy_or_commit_executed_here=False,Git_operations=0,new_live_Slurm_queries=0,new_GPU_submissions=0,state_writes=0,P_writes=0,sealed_state_values_read=False,source_diff=''.join(difflib.unified_diff(v5.splitlines(True),v6.splitlines(True))),refs=refs)
out=D/'independent_review.json'
with out.open('x') as f:json.dump(report,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
files=[dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in sorted(D.iterdir()) if p.is_file()]
manifest=dict(schema='formal_main_v2',kind='bounded_metadata_mapping_independent_manifest',status='frozen',source_root=str(D),files=files,file_count=len(files),review=dict(path=out.relative_to(R).as_posix(),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),bytes=out.stat().st_size),prior_packages_unchanged=True)
m=D/'delivery_manifest.json'
with m.open('x') as f:json.dump(manifest,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(status=report['status'],checks=len(checks),review_sha256=manifest['review']['sha256'],manifest_sha256=hashlib.sha256(m.read_bytes()).hexdigest(),file_count=len(files))))

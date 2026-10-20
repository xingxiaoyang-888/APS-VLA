from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/completed_training_gateway_independent_20261020T1825'
def ref(p):
 p=Path(p);return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def write(name,v):
 p=D/name
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
review=ref(D/'attempt02/code_review.json');assert review['sha256']=='0cfcb9d8da5712c4e4561243043d5cd251a635091dbb7e35a63ea29482d3a1e3'
external=[ref(R/'results/formal_main_v2/control_transport'/x) for x in ('completed_gateway_independent1825_v1.jsonl','completed_gateway_independent1825_v2.jsonl')]
handoff=write('compact_handoff.json',dict(schema='formal_main_v2',status='passed_independent_CPU_gateway_review_only',review=review,checks=59,negative_checks=31,actual_registered_jobs=295,actual_GPU_occupied=['3053440'],controller_original_3034538_completed=True,existing_owner_and_lease_measured=True,original_RUNNING_branch_ast_and_fixture_unchanged=True,mixed_mode_shared_capacity8_preserved=True,second_collect_while_first_active_fixture_passed=True,old_runtime_gateway_and_new_target_both_bound=True,initial_test_failure_retained='The first duplicate fixture selected a non-formal historical job; corrected only the test to select a formal record. Original gateway scopes duplication to formal_main_v2; revision02 source never changed.',external_transport_refs=external,production_writes=0,Slurm_submissions=0,GPU_seconds=0,independent_scope_excludes_own_collect_plans=True,remaining=['Different agent must independently approve exact collect plans.','Root must publish exact gateway, construct genuine runtime readiness and authorization, reserve one actual slot, then run full gateway preflight with fresh actual scheduler facts.','No collection output, full O2A, freeze, final trial, or Goal scientific release is established here.']))
files=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  assert p.suffix not in ('.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle')
  files.append(ref(p))
manifest=write('delivery_manifest.json',dict(schema='formal_main_v2',kind='independent_posttraining_gateway_CPU_delivery',created_utc=datetime.now(timezone.utc).isoformat(),files=files,file_count=len(files),total_bytes=sum(x['bytes'] for x in files),external_transport_refs=external,compact_handoff=handoff,accepted_code_review=review,all_partial_attempts_retained=True,new_GPU_seconds=0))
print(json.dumps({'manifest':manifest,'handoff':handoff,'review':review,'file_count':len(files),'external':external},ensure_ascii=False))

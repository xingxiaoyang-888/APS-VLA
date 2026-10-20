"""Seal server-only author candidates; never grant runtime or scientific approval."""
from pathlib import Path
import json,hashlib,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/nonLong_development_plans_1220';A=D/'attempt01';B='results/formal_main_v2/preflight/heartbeat_20261020T2020';sys.dont_write_bytecode=True

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):
 p=Path(p);return dict(path=p.relative_to(R).as_posix(),sha256=sha(p),bytes=p.stat().st_size)
def out(name,value):
 p=D/name;b=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return ref(p)
report=json.loads((A/'candidate_review.json').read_text());assert report['status']=='original_science_CPU_prepared_new_runtime_readiness_pending' and report['total_planned_trials']==600 and report['new_GPU_seconds']==0
assert len(report['plans'])==3 and all(x['trials']==200 and x['original_P_scientific_wrapper_verify_passed'] and not x['new_P_wrapper_verify_passed'] for x in report['plans'])
assert sha(A/'state_at_planning.json')==sha(D/'state_at_planning.json')=='a32924884da6a900f98aea682642c70047c2b48df51d4d5524a7b4318f5e89b8'
assert sha(R/B/'nonLong_execution_manifest_publication.json')=='11937cea87abd869c8a9d1c0c6e83185fccfc85fe3e33586bec50c8630d4de30'
logs=[]
for n in ['manifests_a1','dependency_preview_a1','prepare_a1']:
 p=R/('results/formal_main_v2/control_transport/nonLong_development_plans_1220_'+n+'.jsonl');rows=[json.loads(x) for x in p.read_text().splitlines()]
 assert rows[-1]['event']=='control_end' and rows[-1]['returncode']==0 and rows[-1]['source173_and_entrypoint_unchanged'] is True
 logs.append({**ref(p),'wall_seconds':(rows[-1]['time_ns']-rows[0]['time_ns'])/1e9,'returncode':0})
inputs=[]
for p in report['plans']:
 sub=A/(p['suite']+'_k128_seed'+str(p['seed']))
 inputs.append({**p,'plan_arguments':ref(sub/'plan_arguments.json'),'candidate_scientific_plan':ref(sub/'scientific_plan.json'),'candidate_effective_plan':ref(sub/'effective_plan.json'),'candidate_action_execution_contract':ref(sub/'execution_contract.json'),'draft_readiness':ref(sub/'runtime_readiness_draft.json'),'draft_authorization':ref(sub/'submission_authorization_draft.json'),'prepared_template':ref(sub/'prepared_invocation_template.json'),'dependency_closure':ref(sub/'runtime_dependency_closure.json')})
out('read_only_discovery_note.json',dict(kind='read_only_path_discovery_error_retained',attempted_path='results/formal_main_v2/libero_spatial/k128/seed41/training_summary.json',error_type='FileNotFoundError',correct_path='results/formal_main_v2/libero_spatial/k128/seed41/training/training_summary.json',resolution='Original helper pair_directory explicitly includes training; corrected metadata read before factory. No GPU or production action.',scientific_gate_failed=False))
handoff=out('handoff.json',dict(schema='formal_main_v2',kind='nonLong_three_development_author_CPU_handoff',status='exact_author_plans_ready_for_root_publication_and_independent_review_not_submission',candidate_review=ref(A/'candidate_review.json'),publication_map=ref(A/'publication_map.json'),immutable_state_snapshot=ref(A/'state_at_planning.json'),state_origin=ref(R/B/'state_before.json'),input_publication=ref(R/B/'nonLong_execution_manifest_publication.json'),training_and_duplicate_checks=ref(D/'training_and_duplicate_checks.json'),missing_original_P_dependencies=ref(A/'dependency_preview_v1/required_P_copies.json'),per_plan_inputs=inputs,exact_original_entrypoints=report['source_files'],planned_future_trials=600,unique_initial_states_per_suite=100,scientific_trials_added=0,all_draft_gate_values_unapproved=True,actual_new_P_wrapper_verify_done=False,actual_GPU_runtime_chain_verified=False,weights_or_sealed_values_read=False,production_files_modified_by_author=False,state_Git_Slurm_modified=False,original_failure_attempts_retained=True,minimum_root_work=['Publish exact nine static scientific/effective/action-contract candidates to R/P under root writer discipline.','Independent actual plan/source/consumer audit; author drafts do not grant readiness.','Root genuine reviews and readiness; then actual full P wrapper/NativeIO verification on exact prepared invocation, followed by independent post-readiness review.','Root only one-use authorization, current controller/lease/pending/capacity reconciliation and single gateway submission.','Development raw terminal whole-chain consumer and independent acceptance; global final/O2A gates unchanged.'],boundaries=['No additional reference methods; exactly A/B for each requested suite/seed.','No complete18/suite requirement added; only original per-pair/suite gates.','No action semantics, trained source, fixed panel, horizons, method or hyperparameter changes.','No API draft or inherited component receipt substitutes for genuine new per-plan root/independent review.'],CPU_cost=dict(new_GPU_seconds=0,preparation_CPU_seconds=report['CPU_process_seconds'],transport_wall_seconds=sum(x['wall_seconds'] for x in logs),transport_calls=logs,other_CPU_seconds='Not independently measured; not GPU allocation.')))
files=[ref(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json']
m=out('delivery_manifest.json',dict(schema='formal_main_v2',kind='nonLong_three_development_author_CPU_delivery',files=files,publication_allowed=False,author_candidate_only=True,GPU_calls=0))
print(json.dumps(dict(manifest=m,handoff=handoff,review=ref(A/'candidate_review.json'),publication=ref(A/'publication_map.json'),state=ref(A/'state_at_planning.json'),transport_pins=logs)))

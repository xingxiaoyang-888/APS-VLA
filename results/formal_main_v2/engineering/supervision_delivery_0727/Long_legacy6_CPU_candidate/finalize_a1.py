"""Finalize private CPU candidate delivery; no production state/Git writes."""
from pathlib import Path
import hashlib,json
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=R/'.local/long_legacy6_followup_0727'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(rel,h):
 p=R/rel
 if sha(p)!=h:raise ValueError('SHA '+rel)
 return dict(path=rel,sha256=h)
pins={
'scripts/ops/formal_downstream_supervisor.py':'f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571',
'scripts/formal_execution_manifests.py':'614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89',
'scripts/profile_formal.py':'4b8a7ac0b8be904f8f6b66d9fe7f6c3f7425056e013db903ac6b480191e2ebf6',
'src/cti_vla/evaluation/formal_profiling.py':'56f9fec509a67b5687393e4d020f26722ee16f237df27261bbf38c1437278a80',
'src/cti_vla/evaluation/libero_runtime.py':'2fc1bacbd1268a36f2e31451c70a650be4f8d0c8f6803e7c8b2a3d45f701c781',
'scripts/ops/formal_action_deployment_v1/consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034',
'scripts/ops/formal_action_deployment_v1/reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd',
'scripts/ops/formal_action_deployment_v1/runtime_scope.py':'6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53',
'scripts/ops/formal_action_deployment_v1/contract.py':'efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19',
'scripts/ops/formal_action_deployment_v1/gateway.py':'8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a',
'scripts/ops/formal_action_consumption_guard_v1/consumer.py':'b3f754557646c8e5fa6172fd8a1bcded7e246bbfb4c490502bdc1e3f73e21b31',
'scripts/ops/formal_action_consumption_guard_v1/reviewer.py':'843f0336fd4161eb23d512b34935c7fca7d75032aceefe86084a16a7939a642c',
}
for p,h in pins.items():pin(p,h)
for n,h in {'report.json':'22a47a847ed81d7a18360354dd6a53b8e1153c716df78a87264bcbca25c49f18','per_trial.jsonl':'2ea56052bf56432858cfb0930707e158054da84c6a68d822b369b4b0cb4e1fbc','per_chunk.jsonl':'ccd1d56775752ac9c8d0d1381b2caf932c7327bfd4670bcca1cdc90b14a6dbc0','run_a2.log':'1509f9a1c5b9cda739c74480a4ebe6b7d2fa7123e3e55b3b54fb1c7a45c1d2fc'}.items():
 if sha(D/n)!=h:raise ValueError('candidate output changed '+n)
plan={
'schema':'formal_main_v2','kind':'Long_legacy6_minimal_followup_proposal','created_utc':datetime.now(timezone.utc).isoformat(),
'implementation_status':'proposal_only_no_production_consumer_or_scheduler_change',
'cpu_candidate':{'report':pin('.local/long_legacy6_followup_0727/report.json','22a47a847ed81d7a18360354dd6a53b8e1153c716df78a87264bcbca25c49f18'),'trials':600,'all_chunks':23179,'actual_old_actions':183676,'conditional_action_trace_pass':True,'unconditional_reuse_authorized':False,'new_GPU_seconds':0,'limitation':'Old600 controller instance/source provenance missing in the inspected run receipts; all records retained as historical old execution. Recorded-source branch-equivalence and CPU replay do not fabricate missing historical controller or RNG captures.'},
'minimum_equivalence_consumer_interface_if_all_registered_conditions_are_met':{
'proposal_name':'formal_action_legacy_equivalence_consumer_v2 (new additive module; not implemented)',
'api':'require_matching_o2a(evidence, development_refs, full_ref, components_ref, *, suite, legacy_equivalence_refs)',
'proof_api':'review_legacy_equivalence(evidence, legacy_root_ref, equivalence_ref, *, suite, target_action_semantics_sha256)',
'inputs':['Exact original root/independent review and full600 raw ledger SHA/prefix ancestry, not copied success counts.','Versioned root-approved and independently reviewed per-trial equivalence bundle; all600 trial IDs/state hashes, checkpoint identities, complete8x7 chunks including unexecuted suffix, executed prefix digests, original frozen AST proof, environment/controller identity and RNG noninterference evidence.','Exact target accepted action runtime/source and action_semantics SHA; this CPU candidate cannot substitute the missing identity condition.'],
'behavior':['Call unchanged legacy consumer to rebuild the original old receipt first. Never relabel or mutate old execution_version, original root reviews or raw ledgers.','Validate explicit bridge map for exactly the legacy reference and full trial coverage, reject missing/extra/duplicate/mixed-suite/mixed-checkpoint entries and unsupported equivalence fields.','Return a separate typed verification envelope retaining old reference, target semantic identity, per-trial bridge provenance, no new success denominator and old10531GPUseconds once.','Use unchanged action-v1 raw parser for all genuine new development/full/components outputs, compare exact checkpoints/semantics/method coverage; keep strict guard reject-by-default when no accepted bridge exists.','A separately audited global-freeze wrapper must consume this explicit proof for legacy leaves; neither guard_v1 nor current72/88 freeze rules are modified in place.','No automatic retry, development replay, caller state filtering or dedup override.'],
'blocked_until':['Recover or establish admissible historical controller/environment identity evidence; current v4 four-first-chunk match alone is insufficient for whole600 environment identity.','Independent review and root integration of the complete candidate and explicit bridge schema.','Concrete caller integration and adversarial CPU tests reject wrong SHA/semantics/ancestry/coverage while original88identity and fullO2A counts remain enforced.']},
'original_planner_dedup':{'path':'scripts/ops/formal_downstream_supervisor.py','function':'prior_contract','lines':'438-532','rules':['Same suite/stage method intersection is a conflict unless exact method list/stage key.','Registered active/unresolved jobs prevent new work.','Newest prior root review scientific_complete=True rejects new submission, including the existing600 Long methods.','Run output cannot overlap any registered output; no alternate directory or action-wrapper version bypass.'],'action':'Do not submit old600 again. Preserve600 as old receipts pending explicit reuse gate.'},
'Long_fixed30_observation_collection':{
'observed_at':datetime.now(timezone.utc).isoformat(),
'R_and_P_downstream_subdirectories':{str(base):sorted(p.name for p in (base/'results/formal_main_v2/libero_10/downstream').iterdir()) for base in [R,P]},
'observed_registered_Long_collect_full_components_jobs':'none at read-only state inspection during this heartbeat; root must repeat exact registry/product check before any submission',
'compatible_formal_panel_found':False,'earlier_small_experiment_profiles_reusable_as_formal':False,
'collector_entry':'scripts/profile_formal.py:collect (171-238), via unchanged original planner stage=collect then accepted action_deployment_v1 gateway/runtime',
'manifest':'development split, exactly dense512 identity; use official Long base, common100-state panel SHA46a06087483151e36198167e7d4e5313c50b63172e09128d65a3650112f0a268',
'needs_global_freeze':False,
'fixed_selection':'For each task0..9 choose minimum source_state_index in registered development panel; run one dense trajectory, capture every pre-action control observation, select indices0,floor((N-1)/2),N-1. Require N>=3; do not pad or change state after a failure.',
'collection_count':{'dense_trajectories':10,'observations':30,'new_scientific_success_trials':0},
'minimal_preregistration':['Root retains complete current registered-job state and checks no overlapping collect job/panel artifact.','Build immutable dense-only scientific plan using original planner and exact suite acceptance; freeze plan+runtime contract+effective invocation.','Bind accepted action runtime, all173source hashes, fixed development panel, dense base identity, one-L40/8-slot reservation and uncontended GPU checks.','Independent/root CPU readiness review and exact SHA token submission by root only; no global freeze argument for collect.'],
'acceptance':['Normal completion and unchanged base/source;10 task receipts,full trajectories/observation hashes,30NPZ content hashes and panel signature.','Reconstruct dense chunk8 cadence and first/middle/last rule from actual pre-action trajectory; environment0/runtime17/wait10/horizon520.','Root and independent nonweight review of raw journal plus full Slurm allocation cost; no success numerator reuse from collection.','Retain failures, no automatic substitute/retry.']},
'formal_full_O2A_and_components':{
'global_gate':'Original planner validate_inputs lines286-290 requires the complete global_freeze; helper.release_global(release=False) validates88identities plus four-suite complete development evidence without opening sealed values or writing root_release.',
'full_or_components_entry':'scripts/profile_formal.py:measure (241+); src/cti_vla/evaluation/formal_profiling.py:profile_formal_methods (300+)',
'per_suite_instances':22,'checkpoint_rule':'Same frozen identities used for closed-loop evaluation; all18 trained selectors plus dense and3 uniform.',
'fixed_panel_observations':30,'warmups_per_instance':50,'rounds':20,'calls_per_pass':14300,'scored_latency_samples_per_pass':13200,
'order':'Original balanced_schedule seed20261016,rotate shuffled22-method order by round; fixed30observation order; keep allspikes.',
'boundary':'Raw obs+instruction ready to CPU-executable8-action chunk ready; preprocessing,vision,DIE,packing,VLA,postprocess included; disk/model load/simulator excluded.',
'component_pass':'Independent same panel/warmups/rounds; cannot substitute full latency.',
'cost':'Charge collection,load,all warmups,main/components passes,failures and allocated GPU time; historical600 cost retained once.'},
'source_pins':[dict(path=p,sha256=h) for p,h in pins.items()],
'no_GPU_submission':True,'no_state_or_Git_mutation':True,'no_final_sealed_values_read':True}
with (D/'minimum_followup_plan.json').open('x',encoding='utf-8') as f:json.dump(plan,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
correction={'kind':'delivery_manifest_finalization','reason':'Initialdelivery manifest was emitted before run_a2 stdout flushed; its run_a2.log entry is superseded by final stable bytes. All initial files/manifest retained; no experiment or report bytes changed.','initial_manifest_sha256':sha(D/'delivery_files.json'),'final_run_a2_log_sha256':sha(D/'run_a2.log')}
with (D/'delivery_manifest_correction.json').open('x',encoding='utf-8') as f:json.dump(correction,f,sort_keys=True,indent=2);f.write('\n')
files=[dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(D.iterdir()) if p.is_file()]
final={'schema':'formal_main_v2','kind':'candidate_delivery_manifest','status':'complete_private_candidate_only','files':files,'reuse_authorized':False,'production_activated':False}
with (D/'delivery_final.json').open('x',encoding='utf-8') as f:json.dump(final,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'plan_sha256':sha(D/'minimum_followup_plan.json'),'delivery_final_sha256':sha(D/'delivery_final.json'),'files':len(files)}))

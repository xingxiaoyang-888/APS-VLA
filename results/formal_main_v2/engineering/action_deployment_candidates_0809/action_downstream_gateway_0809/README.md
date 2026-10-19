# Formal downstream server gateway candidate

CPU-only preparation under \`R/.local/action_downstream_gateway_0809\`. No production state, reservation, Slurm submission, checkpoint or sealed-value access was performed by this candidate's tests. The gateway does not grant a release or scientific completion.

## API and execution identity

- \`validate_authorization(root, ref)\`: rehash typed root authorization, independent CPU review, frozen effective/scientific plan, prepared invocation, exact new-runtime readiness and reservation.
- \`FrozenPlan.prepare(state)\`: first checks bound evidence and all 173 original source bytes, calls only the existing pure planner with an explicit server project root, then the real new converter. Every scientific field stays exactly equal to the original plan; prepared metadata is exactly \`registered_utc\`, \`plan_sha256\`, \`runtime_readiness\`.
- \`Gateway(...).run(submit=False)\`: default read-only check under the pre-existing shared writer lock. It uses the pinned controller's all-registry observations/capacity, never the legacy refresh/submit CLI.
- \`NativeIO\`: only exact SHA-bound project metadata in scripts, configs and formal results can be published. Existing runtime bytes must match. Snapshot/weight/state destinations are rejected.
- Explicit submit CLI after root separately installs and approves:
  \`python -B scripts/ops/formal_action_deployment_v1/gateway.py --authorization REL --authorization-sha256 SHA --gateway-sha256 SHA --submit --root-reviewed-submit\`.
  Default without the last two flags never publishes or changes state.

The output job retains \`execution_version=formal-downstream-action-v1\`, wrapper/entrypoint/SHA, action execution contract, scientific plan, readiness, effective plan SHA and original source-provenance SHA. It does not relabel a new execution as legacy v1.

## Root readiness and acyclic references

The root must issue a new typed \`formal_action_runtime_readiness\` with \`status=passed\`, \`reviewed_by=root\`, \`execution_version=formal-downstream-action-v1\`, unchanged science, final disabled and raw consumer ready. It binds \`effective_plan\`, \`plan_sha256\`, \`scientific_plan\`, \`runtime_sources==contract.files\`, full effective support files and action contract. Distinct root and independent production-chain receipts must bind those direct sources and declare \`production_chain_complete=true\`.

The extra \`component_reviews\` map has exactly runtime/wrapper/raw_consumer; each typed independent CPU receipt binds its source files. Together with this gateway's independent review they cover all seven new implementation files. The ready artifact may publish a minimal explicit \`runtime_publication_files\` map. It must not include its own SHA; the gateway adds the readiness file automatically.

The prepared invocation references readiness; readiness references the effective plan, not that prepared invocation. The root authorization references a reservation whose intent SHA is the canonical authorization without its \`root_reservation\` field. This avoids self hashes.

Templates are intentionally unsigned and rejected. No readiness currently exists for this candidate. CPU tests are not root authorization.

## Submission transaction

Exact original 1 L40 / 7 CPU / 64 GiB / 4 h resources and scientific argv remain. The operational command adds \`--no-requeue\`, \`--exclude=gpu4020\` and an exact authorization-derived comment. New wrapper invocation is still \`--invocation --invocation-sha256\`.

Before publication, a durable pending record is committed by CAS under the common writer lock. Only then are the unique R/P invocation and permitted missing support files published, followed by one sbatch. All registered jobs are observed twice before submission; unknown/missing accounting, 8 occupied GPUs, duplicate pair/stage, another pending request, hold or foreign reservation block submission. Confirmed registered/actual CPU0 does not occupy a GPU slot.

Activity identity uses real squeue comments; nonempty sacct comments may not conflict. For a just-acknowledged ID absent from squeue, one exact scontrol query must corroborate ID/name/state/comment; its original output is preserved. No request token is substituted for observed data. Historical terminal empty comments do not authenticate a new request.

Only a full unambiguous positive acknowledgement plus fresh accounting/token corroboration permits the new registry row. Uncertain acknowledgement, query failures, CAS drift and partial publication preserve pending/audit evidence and stop. There is no automatic retry or cleanup. A known ID remains in pending if final reconciliation fails. Existing registry rows and autonomous/controller fields are preserved; only this submission's reservation is consumed.

## Limits and test boundaries

Allowed stages: development, collect, full, components. Final is always rejected. New-to-new rollout continuation remains pending if the unchanged legacy pure planner cannot consume a new-version prior audit; the gateway never fabricates an old invocation/review. Root must separately finish the new-version consumers before issuing readiness.

CPU tests use the real controller capacity/CAS/file-lock code, real converter and actual R/S 173 source SHA checks. Scheduler calls, model/environment execution and the old scientific planner in the FrozenPlan integration case are explicit stand-ins. That case copies original source metadata into an isolated test root; it does not establish new training provenance or a real scientific plan. NativeIO tests use isolated temporary P/R directories. No network transport or scheduler invocation occurs inside these tests.

The a2 typed fixture omitted runtime suite/stage/source context and failed 20 cases while 53 transaction cases passed. The original test/source/XML/log are retained; a3 fixes only fixture metadata and passes those 20. Later import-order hardening checks pinned evidence before invoking the pure planner, with final CPU evidence recorded separately.

All-suite resume amendment: pre-run hashes now come from the exact new contract.resume_prefix_inputs(original invocation), covering only trials.jsonl and closed_loop_report.json for each development-resume suite. Original plan/root evidence/pull bytes stay unchanged; no generic mutable-file list exists.

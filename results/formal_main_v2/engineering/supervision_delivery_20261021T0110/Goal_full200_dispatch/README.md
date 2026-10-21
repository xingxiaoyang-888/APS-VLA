# Goal full200 exact held dispatcher — CPU candidate

This package is a new, single-purpose root dispatcher for one fixed Goal development attempt. It does not reuse Object submission authority. The copied low-level transaction/parser/capacity routines are attributed in derivation.json; the old Object package is frozen unchanged.

Scope is exactly the original 100 development states in their original 200-entry A256_seed17/B256_seed17 order, pair 5b1bc1ab99e1bfa1545ef8270ca3fbe8364349ab462f8a64fb4858eb15576e1e. Bounds remain 60,000 total control steps, 7,600 policy queries, 2 hours, one L40, one attempt, no requeue/retry. The original Goal200, other Goal1000, and final evaluation stay HOLD. This is not a replay of the 58-trial engineering jobs. Those original allocations remain separately retained once: 3053440 = 803 GPU seconds and 3054127 = 840 GPU seconds.

## Publication and prerequisites

Root alone publishes publication_map.json to R/P, preserves all 173 frozen files, and adopts the independent runtime/dispatcher source reviews. No publication, state edit, Slurm call, or new trial was performed by these CPU tests.

The runtime package and its package_manifest are installed separately using its own exact final publication map. The dispatcher scope binds its full 10-file map, including consumer.py. A previous runtime v1 consumer gap was discovered independently; its CPU records remain historical and cannot authorize the final v2.

Production remains HOLD until the final runtime and this dispatcher have independent source/CPU reviews, root adoption, canonical R/P byte checks, an actual P --verify capture, root and independent runtime readiness, and exact root authorization. source_and_CPU_only reviews are not evidence of a GPU run.

1. Root installs the final runtime's 11 files and this dispatcher's 2 files exactly. Root reads the runtime README and builds root_readiness.json and independent_readiness.json from the real audited evidence, followed by root_authorization.json; R and P copies must have identical bytes. No synthetic flags or old58 authorization may substitute.
2. At the published P entry, run the exact command below. Preserve the actual subprocess argv, returncode, full stdout and stderr in a server JSON whose kind is Goal_full200_actual_P_verification_capture and runtime_files equals scope.json runtime_files:
   
   PY -B P/scripts/ops/formal_goal_full200_gate_v1/entry.py --verify --package-manifest-sha256 FINAL_RUNTIME_MANIFEST_SHA
   
   The return value must be passed_metadata_source_capacity_only. This rebuilds full original scientific inputs/checkpoints and checks R/P capacity. It is not a GPU trial.
3. Archive both independent reviews under results/formal_main_v2/engineering/. Runtime review must carry package_manifest_sha256, package_files (all 10), blockers=[], and a non-root reviewed_by. Dispatcher review must have kind Goal_full200_atomic_dispatch_independent_review, status passed, dispatch_files (all 2 canonical paths), package_manifest_sha256, runtime_files (all 10), blockers=[], review_scope source_and_CPU_only, GPU_execution_authorized=false.
4. Under root supervision, run prepare_admission.py through the audited transport with its exact SHA. It prints only the exact root admission JSON; it never writes files or calls Slurm. Arguments are:
   
   --dispatch-sha256 FINAL_DISPATCH_SHA --runtime-review ARCHIVED_RUNTIME_REVIEW --dispatch-review ARCHIVED_DISPATCH_REVIEW --actual-P-verification ACTUAL_P_CAPTURE --root-reviewed
   
   All three input paths are R-relative. Root must preserve stdout bytes and publish identical bytes as R/P/results/formal_main_v2/engineering/goal_full200_20261021T0110/dispatch_admission.json under the shared writer lock. It validates real runtime/source/readiness and rechecks actual P scientific identity and current storage before constructing the proposal. Root remains responsible for the substantive approval, not just running a builder.
5. From R, run the canonical dispatcher with --dispatch-sha256 and --admission-sha256, without mutation flags for its read-only readiness. This checks the current full registry/accounting, both pending fields, original controller owner/lease/completion, all-mode eight-slot capacity, and Goal/pair exclusion.
6. Root alone invokes that same exact command once with --submit --root-reviewed. Production command details and pins are in publication_map.json / scope.json and the final manifest.

Absolute prefixes: R=/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo, P=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA, PY=/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python. The shared state lock is R/results/experiment_supervisor/.writer.lock.

## Atomic transaction and failure behavior

Pending intent plus reserved slot is durable before exactly one sbatch --hold --parsable --no-requeue. Original ACK and actual held token/comment/name/account/output/command/resources are preserved. The original ACK alone identifies the job; unknown submit outcomes are never cleared or resubmitted. The held job is included in a fresh full-mode capacity preview and then CAS-registered. The real runtime validate_dispatch consumes the actual held registration and exact reservation before the R/P held_dispatch_record is published. Only then is one release attempt durably recorded and sent.

Any BaseException preserves HOLD and original evidence. If the ACK exists, --reconcile --root-reviewed may only reconcile that exact original pending/ACK/job. It never submits another job. The existing-ACK metadata path reconstructs original config/design and the complete fixed200 scientific identity through the original helpers. It does not claim that an already-running RAW/output is fresh, and cannot be used with --submit or the new-work readiness path. The original source/authorization/ACK/registration and current all-mode capacity still must match. If release might already have been sent, it never sends release again. An actual failed/preempted/timed-out allocation remains for root diagnosis and its GPU cost is retained. The second call cannot turn a previous/partial/terminal same-scope registration into a new attempt.

The ordinary supervisor compatibility fields are preserved: name/job_name, experiment, requested gpus, source/config/wrapper identity, downstream_gateway.actual_sbatch_argv and exact full request_token/comment. root_dispatch_prepared_utc is deliberately not labeled actual submission time; the sbatch fact records real call start/return UTC.

The fresh observer queries all registered Slurm allocations. A stale nonterminal registry status with actual terminal accounting needs a second successful full sacct confirmation of every original terminal row. Live IDs must agree exactly between accounting, squeue, and scontrol; missing/unknown rows or conflicting identities fail closed. Historical registry values are not overwritten merely to fit a projection.

## Verification and limits

verify_cpu.py uses in-memory scheduler/state fixtures and the saved real 301-allocation observation from the frozen Object gateway. No additional scheduler query is made. It independently derives the Goal capacity/old803+840 projection and exercises the exact final runtime config and held_dispatch consumers. Positive and rejection lists are in CPU_report.json; raw failure histories remain alongside prior CPU reports.

Read-only replay is verify_cpu.py --verify-saved through the audited transport. It rehashes the final runtime map and compares the rebuilt report; it does not execute runtime main, start a simulation, or submit GPU work.

The final runtime/dispatch audit and root actual P preparation are required before use. No new Goal GPU raw data or terminal result exists in this package. Runtime main must still enforce its exclusive RAW claim, five-component input integrity, paired t0 gate, full bound ledger, and truthful policy-error halt. Only its real terminal consumer plus independent terminal review can support new200 acceptance. No old200, other1000, or sealed final result is admitted here.

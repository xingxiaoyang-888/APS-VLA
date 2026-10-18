# Continuous formal training: execution-only candidate

Candidate root: R/.local/autonomous_training_v1/train. This library reads only.
It does not submit Slurm, modify state, activate a controller, load a checkpoint,
or write a scientific result. Windows was used only for memory SSH transport.

## Scope

Keep the original 173 frozen files, three existing Slurm wrappers, model
loaders, DIE/head, losses, initialization, 40000-sample sequence, AdamW/RNG
restore, hard validation and selection exactly unchanged.

The new invocation changes only:
- --stop-after-updates to 5000 (the existing planned training horizon);
- --max-wall-seconds to 169200 for the entire sequential A/B invocation.

Submission uses the original registered wrapper, with explicit
sbatch --time=48:00:00 overriding its historical four-hour directive.
The controller records both the original wrapper SHA and actual submit argv.
It must also enforce the original one L40 / 7 CPU / 64 GiB / no-requeue
allocation, exclude gpu4020 under the separately approved scheduler contract,
and count every unresolved request in its eight-GPU limit.

No scientific watched_files are added or removed. The explicit top-level
autonomous_execution contract binds the authorizing amendment, this library,
the original base invocation, original wrapper, predecessor review, original
acceptance review and starting A/B recovery identities. Copy this exact
contract to the registered job; allocation_time and soft_wall_seconds are
also explicit job fields. The controller owns durable pending-before-sbatch.

## APIs (controller holds the project writer lock)

pair_key is a registered string such as libero_10_k128_seed17.

1. Rebuild own-suite original acceptance with the unchanged reviewer.
   For a fresh pair:
   admission = {decision: ready, pair_key, mode: fresh,
     acceptance_review_ref: {path, sha256},
     rebuilt_acceptance: ORIGINAL_COMPLETE_ACCEPTANCE_REVIEW_RESULT}.
   The library rechecks its source173 and exact accepted files/contracts.
   This object is not permission to skip the original raw scientific gate.

2. For an existing clean pair, first stable-pull every registered historical
   allocation and run the original review_formal_segment.review. Retain all
   costs and raw attempts. Hash the exact registered two resume.pt paths on
   the server; never download or deserialize these files in the controller.

   Machine review is explicitly an envelope:
     schema: formal_main_v2
     kind: automatic_machine_training_review
     version: autonomous-training-machine-review-v1
     status: passed_machine_reconstruction
     original_review: complete original verify_server_resume=False summary
       (status remains local_passed_remote_required)
     reviewer: {path: scripts/review_formal_segment.py, sha256: pinned SHA}
     server_resume_checks: fresh exact A/B path/existence/bytes/SHA responses
     root_signature_claimed: false
     independent_review: false

   It does not impersonate a human root or an independent reviewer.
   Existing genuine passed root reviews remain valid migration inputs.
   Call classify_terminal(root, pair_key=..., job=..., review_ref=...,
     rebuilt_review=ORIGINAL_REVIEW_RESULT, actual_resume_checks=...).

   The function requires the same original raw reconstruction, all retained
   current file SHA, complete historical GPU billing, commit endpoint and
   exact resume identities. It additionally reads current raw attempt endings.
   It returns decision complete / ready / blocked, an immutable evidence map,
   and the actual completed_by_arm. It never rounds a cursor to a multiple of500.

3. build_base_invocation(root, pair_key=..., source_inventory={path,sha256},
   jobs=REFRESHED_REGISTERED_JOBS, admission=..., registered_utc=UTC_STRING).
   This is a pure assembler; it never calls/intercepts old submit().
   Existing pairs must retain the exact prior scientific argv/gate/runtime
   identities and explicit --resume. Fresh output/checkpoint absence is a
   required server preflight returned to the controller. Only the controller
   performs the fresh preflight, current resume rehash and actual submission.

4. build_execution(root, base_plan, adapter_ref={path,sha256}).
   Returns invocation, invocation_relative, wrapper/SHA, source/config,
   execution_contract, preflight, server_resume_checks and
   sbatch_options=["--time=48:00:00"].
   Invocation path must not already exist. Root activation remains required.
   The controller must publish it atomically, keep one pending transaction,
   and stop on an uncertain sbatch outcome instead of retrying.

## Clean completion and recovery

- Legacy reviewed500-boundary jobs may proceed directly toward5000.
- target5000 + A5000/B735 is not complete. The original runner validates A's
  final receipt and skips its training; B resumes cursor5880 and its full
  optimizer/RNG/evaluation history. No validation is repeated or inserted.
- A clean soft wall can commit any complete update, not only50/500 boundaries.
  The original reviewer must first verify that commit and all raw work.
- If A completes at the allowance and the original outer runner does not enter
  B, the checked allocation wall receipt and actual A completion identify that
  specific branch. It is not an arbitrary missing-arm allowance.
- Both arms5000 require both original final deployment receipts and all11
  registered validations. There is no5500 extension.
- FAILED, TIMEOUT, PREEMPTED, missing/truncated evidence, changed checkpoints,
  unknown states or ambiguous submission hold the pair. No signal handler or
  recovery mathematics was introduced. A killed in-flight update remains an
  exception; the frozen complete last checkpoint is preserved but not
  automatically retried.

The three known startup-failed pairs remain blocked even after unrelated jobs
finish. A later separately audited repair-admission extension must rebuild the
typed startup failure, repair registration and successful recovery chain,
including the original226 GPU seconds. This version does not filter failures
from history or silently reinitialize a begun arm.

## Evidence and acceptance boundary

pytest_a1:46 new contract tests. Their upstream scientific reviewer summaries
and tiny source inventory are explicit synthetic fixtures; they do not claim
a full real scientific run or actual Slurm submission.

pytest_core_a1:8 selected existing CPU tests run the unchanged training core:
complete optimizer/head/scorer/RNG/cursor resume equality, continuous/segmented
equality, non50 clean wall checkpoint, atomic-save failure, altered ledger
prefix rejection, matched A/B behavior/order, and all registered5000 configs.
Tiny providers and CPU tensors are used; no official model was loaded.

real_source_readiness: actual R/S173, all four own-suite GPU acceptance files,
Object metadata6 and Goal metadata6+component4 are rehashed. Root's inherited
real GPU evidence binds four-suite F00/F01/F03 and28 already completed arms.
These inherited checks apply only while the execution/science bytes remain
exact. No repeat GPU training is required solely to change target/time metadata.
Root independently reviews the new controller and its CPU/scheduler probes.
The first new production invocation is then checked for the exact registered
wrapper, target5000, recovery identity and unchanged source. This candidate
itself has not activated that invocation.

Root scheduler evidence: job3034099 completed on cpui134, 3 CPU seconds/0 GPU seconds; result and root review are bound in candidate_review.json. Its 48h sbatch test-only result proves scheduler admission only, not GPU training execution.

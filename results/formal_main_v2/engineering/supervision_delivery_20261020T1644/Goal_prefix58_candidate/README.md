# Goal fixed-prefix observer: CPU candidate only

This package is a passive observer and reversible AST candidate, not a GPU or scientific release. It preserves the original Goal 256-token seed17 A/B checkpoint identities and the original state-major first 58 trial identities (29 existing development states). The original 200-trial job remains HOLD; all new Goal scientific development remains HOLD. No final state values were read.

## Completed evidence

- `cpu_report_v1.json`: 204/204 CPU checks against real frozen `run_episode` and `evaluate_formal_trials` code under the original accepted action adapter.
- `cpu_additional_v1.json`: 8/8 additional CPU sentinels. The initialized CUDA-generator branch uses a fake generator fixture, not a GPU.
- `prepare_v1.json`: the original unchanged wrapper and legacy adapter passed read-only CPU preparation; all 100 registered development states retain their identity and the first 58 match the original forensic prefix exactly. No model inference or GPU initialization occurred.
- Original action calls, action values, reset/step/policy call counts and their order match the baseline in CPU fixtures. The original accepted amplitude-check deletion is retained; there is no clipping or historical action replay.
- AST inverse projection restores the complete accepted function bodies, including original policy timer statements. Mutations adding a step, render, RNG draw, changed timer, changed query arguments, or changed reset expression are rejected.
- Before/after copying guards compare original observation and chunk object identity/bytes, global RNG, and readable simulator/environment RNG state. Negative Python/NumPy/CPU-generator/CUDA-generator-fixture mutations, input replacement/mutation and simulator mutations abort. A policy exception leaves one failure and stops; it does not run B or retry.
- The 173 frozen files and original wrappers are unchanged. No new Slurm job or GPU cost was added.

## Observer and limits

The observer copies five original observation arrays, their exact original aggregate hash, separate hashes, dtype, shape, strides and raw C-order byte blobs. It records reset before/after, set_init before/after, every original dummy wait before/after and t0 query before/after. It reads direct existing MuJoCo arrays through `env.env.sim.data._data` when the native type is recognized, and records missing data otherwise. No simulator getter/update/forward/render, extra policy call, seeding, RNG draw, CUDA initialization or explicit synchronization is added. Only already-existing generator get_state APIs are read. Native MuJoCo/CUDA passive reads still require real engineering verification.

The original unused reset return is retained briefly only to copy its five arrays, then deleted before set_init_state. This changes that temporary object's lifetime. Copying, hashing and file writes also perturb wall-clock timing. Observation hooks are outside the original policy perf_counter interval; original total episode/attempt time includes the added work. Therefore this candidate is never a latency benchmark or evidence of exact deterministic replay. Unsupported opaque values receive identity-only guards or explicit missing annotations; arbitrary observation-cache/simulator hidden state is not reconstructed.

The original reset contains an internal retry loop whose `finally: continue` can swallow application exceptions. This candidate does not modify it. A future single attempt must have an actual Slurm hard limit of at most 30 minutes, one GPU included in the shared eight-slot limit, no automatic retry, no original-action forcing, and the exact original first58 order/checkpoints/model loading. The previous 12-query probe and this CPU package do not establish a cause or clear any Goal HOLD.

## Remaining before any GPU

1. Root and another agent independently review this exact observer/AST source and CPU evidence.
2. Implement and audit a dedicated single-attempt outer runner which enters the unchanged asset/component/action_v1 contexts, installs this observer inside the accepted action context, calls the original `legacy.run` / `execute` with only a fresh engineering output and `stop_after=58`, and restores all bindings before the outer action context exits. The original execute/model-loading function must remain byte/code-identical. Record readable RNG at existing loader events without adding model calls. This outer runner is **not implemented in this package**.
3. Bind source/checkpoint/panel identities, root authorization, reserved slot and exact submission token; independently review the admission, exception and timeout handling. Do not reuse the original output or resubmit automatically.
4. Only then run at most one bounded real engineering attempt and review its raw passive captures. Success/failure outcomes must not decide engineering admission. A non-reproduction does not prove a cause.

`prepare_candidate_v1.py --execute` always rejects before reading inputs or creating outputs. No Slurm script or generic real-execution path is supplied. CPU fixtures and their successful outcomes are synthetic and excluded from all scientific denominators. CPU scripts are one-shot in this private package: preserve the existing receipts; reruns need a new private test directory.

## Rebuilding and storage

All source, tests, synthetic arrays, raw fixture journals, intentional failures, exact input copies and version history are retained in this server-only package. `delivery_manifest.json` enumerates every private file other than itself. No model/checkpoint tensors are included. Exact transport entry hashes are recorded in `transport_audits.json`; no local Windows project files were written.

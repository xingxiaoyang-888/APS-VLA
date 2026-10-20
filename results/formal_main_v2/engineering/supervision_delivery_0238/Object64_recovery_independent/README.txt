Object64 seed23 / 3044017 independent original-target recovery audit

Status: passed_original_target_recovery_only.
The failed 3028468 allocation remains FAILED with 69 GPU seconds. The successful
3044017 allocation contributes 5141 GPU seconds; total 5210. Both arms reached
500 updates from a fresh initialized run, each with 4000 actual uses / 4000 unique
windows / cursor 4000. resumed_from_existing_checkpoint is false: the old CUDA
startup failure produced no checkpoint or arm initialization.

The checker independently rebuilt full fixed 40000 sample order, same A/B
initialization, update and microbatch records, original 5000-step schedule,
validation at 0 and 500 over all 204 windows, task-equal teacher metrics,
hard64 (32 tokens per view), candidate selection, commit and cache journals,
all 25 pull files, source173 in R/S, Object-only metadata compatibility and its
own GPU acceptance provenance. Actual server hashes cover both resume files,
four partial candidates, and official Object150000 components. No checkpoint
tensor was deserialized; the optimizer/RNG payload itself was not loaded.

This is not completion of the 5000-step pair, not a new training or GPU test,
and not authorization for continuous5000, a new submission, or final evaluation.
The original next ordinary boundary is 1000. A separately audited root admission
may authorize a different execution target without changing these historical facts.

execution_a1.json contains the exact pinned server transport invocation.
The checker completed once with exit0 in about9.2 seconds. preparation_a1_failure
preserves the earlier generator insertion-needle assertion, before any checker
execution; prepare_a2.py changed only that generator's exact whitespace match.
No shared state/Git/production files or scientific source were modified.

existing_evidence_refs.json is the complete read closure. Historical private paths
are mapped to already-existing exact canonical bytes or validated members in the
existing CUDA failure archive; none are silently rewritten in the original review.
The server model/checkpoint hashes are references only. delivery_files.json lists
all new private files and itself is delivered separately by its external SHA.

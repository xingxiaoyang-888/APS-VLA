# Goal256 seed17 /3037543 independent terminal audit

Status: passed_complete_training_only. Server CPU audit of existing real training only; no new GPU run, next5500, or final release.

One fresh allocation ran both arms0→5000 without a cross-job resume. Each arm has40000 committed sample uses,33859 actual unique windows, and6141 legal repeat uses from the next seeded full-pool epoch. Every update/microbatch and11 validation nodes ×186 windows were reconstructed. Hard256 retains128 tokens per view. Equal-task teacher L1 with earlier-update tie-break selects A@4000 (0.007607010809061604) and B@5000 (0.007694445978813168).

The own Goal F00/F01-k256/F03/source identities were verified. Original metadata and Goal-component review helpers reconstructed both acceptance3012579 and training3037543 with complete raw receipts/events. The two official50000 component files and both arms' best/resume checkpoint files were SHA256-hashed in place. Nothing was deserialized, copied or altered. There was no actual cross-job optimizer/RNG restore to claim for this fresh pair; its qualification is inherited from the exact same-source Goal F03, while every real50-update commit and final resume hash was verified.

Entire pair cost is64274 GPU seconds, counted once. Shared prior acceptance cost is marked separately and not re-added. Relative to zero prior reviewed updates this completion adds10000 arm updates. No state/Git/Slurm mutation or queue polling occurred.

The archived A/B cost journals plus cache journal total181404060 bytes. All compressed chunks were checked by the pinned audited codec; a read-only comparison sink reconstructed every byte and compared it directly with the retained original. No restoration output was written.

execution_a1.json records the exact audited transport command, scriptSHA, returncode0, duration9.58760281931609s and original stdout/stderr. Two earlier in-memory generator checks incorrectly matched a legitimate template path/numeric prefix; preparation_a1_failure.json and preparation_a2_failure.json preserve them. Neither published a checker, ran a scientific audit nor consumed GPU time.

Archive every new file in delivery_files.json, including that manifest itself. existing_evidence_refs.json lists canonical dependencies instead of duplicating raw data/source aliases. All tensor files remain server-only hash references.

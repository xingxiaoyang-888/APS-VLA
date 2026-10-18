# Action GPU v3 server control-entry migration candidate

This is an uninstalled CPU candidate. It does not publish configuration, create a root approval,
run a model, start Slurm or open sealed states during its validation mode.

Control root is explicitly /share/home/u15016/XXY_CVPR/CTI-VLA/control_repo (R).
The runtime P, source snapshot S, 173 frozen files, eight reviewed GPU source payloads,
constructor adapter, original author/independent proofs and scientific gates remain unchanged.
The previous entry is preserved byte-for-byte as legacy_entry.before.py.txt; migration.diff
contains the complete limited change.

Changes:
- Replace the obsolete implicit local root with the fixed server control root R.
- Bind SERVER_WORKSPACE.md, docs/服务器工作区与GitHub同步.md and the exact old entry SHA.
- Require the caller to supply the reviewed current entry SHA.
- Add mutually exclusive --validate-only versus --root-approve-cpu-registration.
- Actual publication is permitted only from the exact installed path
  R/.local/action_execution_gpu_v3_root_integration_server_v1.py.
  The candidate entry.py can validate but cannot publish.
- Record this control-workspace migration in the root proof. Preserve the old source archive;
  use new server-entry archive/check-only-result names. All original eight payload identities,
  absence/exclusive-write checks, typed independent proof, unique CPU-only synthetic-state
  exception, full P/S closure and single-attempt root-registration gates are retained.

Read-only command (root may run after independent review):
    /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -B \
      /share/home/u15016/XXY_CVPR/CTI-VLA/storage_migration_candidates/action_gpu_v3_server_entry_v1/entry.py \
      --entry-sha256 <reviewed entry.py SHA> \
      --independent-review .local/action_execution_gpu_v3_independent_0840/independent_review.json \
      --independent-sha256 82167dfb3b61b1267ba537c45bc49d51b63e3ce5a437bc51bb0cf864638fc935 \
      --validate-only

The returned status is validated_server_candidate_no_publication_root_decision_pending.
It checks real restored evidence, prepares the proposed bytes/closure only in memory, checks
all publication paths remain absent, prints a diagnostic and returns before any file mutation
or subprocess. Proposed root declarations in memory are never saved or treated as approval.
The exact one synthetic state reference remains CPU evidence and is never deployed.

After independent migration review, root must first explicitly accept this entry and install
the same bytes at the exact R path. Root may then replace --validate-only with
--root-approve-cpu-registration. That flag records a real caller decision; it is not automatic
approval and this candidate has not exercised it. The original eight-file publication and
original submit.py --check-only run only on that future authorized branch. No --submit,
SSH/upload, model or Slurm call is added. The final root registration still needs separate
submission/capacity/identity gates and real GPU acceptance.

14 focused CPU tests passed. The real --validate-only flow ran under a Python audit hook
rejecting file writes, child processes, shell execution and socket connections. Both R and S
173-file identities were rechecked. No copied repository or synthetic registration was needed.
Tests also cover wrong root, off-root publication, entry SHA, policy/baseline drift, missing or
conflicting approval mode, sealed-path lexical rejection, unique synthetic-state authority,
original gate AST identity and fixture-free/self-cycle-free deployment closure.

All test logs, XML, stdout/stderr and receipts live in this server candidate directory.
No local files, real R publication/configuration/state, Git index or job were written.
If a pinned workspace-policy file changes before use, this candidate intentionally fails;
root must review and version a new migration rather than bypass the pin.

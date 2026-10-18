# Server control transport candidate v1

Status: CPU candidate only. No Slurm submission or live supervisor/state operation was performed.

Fixed roots:
- Control repository R: /share/home/u15016/XXY_CVPR/CTI-VLA/control_repo
- Runtime P: /ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
- Candidate: /share/home/u15016/XXY_CVPR/CTI-VLA/storage_migration_candidates/server_transport_v1

Root must independently accept this candidate before integration. Invoke an already reviewed
control script by its exact R-relative path and SHA; the wrapper does not choose or submit work.

    /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -B \
      /share/home/u15016/XXY_CVPR/CTI-VLA/storage_migration_candidates/server_transport_v1/run_server_control.py \
      --bundle-manifest-sha256 <bundle_manifest.json SHA> \
      --entrypoint scripts/<reviewed_control_script>.py \
      --entrypoint-sha256 <exact script SHA> \
      --audit-relative results/formal_main_v2/control_transport/<new-invocation>.jsonl \
      -- <original arguments>

Only this child and descendants receive the candidate bin directory in PATH, plus no-bytecode
settings and R/src + R/scripts in PYTHONPATH. The wrapper hashes all 173 frozen files in both
R and the original P snapshot before and after execution. It never edits f.SSH. Existing node
exclusion therefore still sees ['ssh','-o','BatchMode=yes','tongji-cvpr'].

Accepted SSH shape is exactly:
    ssh -o BatchMode=yes tongji-cvpr '<single shell command>'
It invokes local bash -lc, passes the original command as one argument, restores the scoped PATH
and cwd R, and preserves stdin, stdout, stderr and exit status. This is a transport replacement,
not a sandbox for the already authorized command. Original supervisor/review/scientific gates
remain responsible for command authorization. No shell profile or global PATH is changed.

Accepted SCP shape is exactly:
    scp -q <one file> tongji-cvpr:<absolute destination>
or the reverse, with exactly one remote endpoint. Relative local paths resolve beneath cwd R.
Only R/P/H descendants are eligible. Weight/checkpoint/state/sealed/test paths, aliases and
symlinks are rejected; runtime snapshot destinations are rejected. Parent directories must
already exist. New files publish atomically and exclusively; identical existing bytes are a
no-op, differing bytes are never overwritten. Failed partial transfer bytes are retained.
Unsupported host/options/recursive/multiple-file operations fail closed.

The audit JSONL is a new file directly under R/results/formal_main_v2/control_transport.
It records original and actual SSH argv, copy paths/bytes/SHA, child return codes and final
source verification. Failures remain nonzero. No audit overwrite or automatic retry occurs.

CPU test boundary:
- Real R and original snapshot: read-only exact inventory and 173-file SHA checks.
- Transport integration: a small synthetic server directory inside this candidate; copies only
  the 173 registered source files (about 3.33 MB total for two trees). It re-roots the inventory
  and three module constants for that fixture only, without changing production functions.
- Actual frozen formal_supervisor.remote/f.SSH, runner, PATH ssh/scp shims, local bash and
  nested subprocesses are exercised; no refresh, Slurm, network transport, real state,
  model, environment, weight or sealed-state operation is performed.
- A result is not approval to start a job or to remove local data.

This candidate does not migrate historical F:/ absolute paths embedded in older ad-hoc tools,
provide Git transport, bypass asset compatibility or modify raw-result archive rules. Such
entrypoints must be checked separately before their exact SHA is authorized. Git operations
must not run within this restricted tongji-cvpr transport scope. Existing raw/snapshot identity
and GitHub reconstruction verification remain unchanged.

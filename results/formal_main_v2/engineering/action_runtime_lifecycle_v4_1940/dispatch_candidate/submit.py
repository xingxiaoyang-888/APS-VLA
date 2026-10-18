"""Root-only one-shot dispatcher candidate. Import/check-only performs no I/O mutations.

Submission requires explicit --submit, three external SHA references, exact
typed CPU acceptance, the existing supervisor lock, a fresh registered-job
query, and a durable pending transaction. There is no retry/resume option.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys


def load_sibling():
    path = Path(__file__).resolve().parent / 'launcher.py'
    spec = importlib.util.spec_from_file_location('_action_execution_dispatch_contract', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


c = load_sibling()
TERMINAL = frozenset({'COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY',
    'NODE_FAIL', 'PREEMPTED', 'BOOT_FAIL', 'DEADLINE', 'REVOKED'})


def reserves_slot(job):
    words = str(job.get('status', '')).split()
    return not words or words[0].rstrip('+') not in TERMINAL


def submission_gate(state, jobs):
    c.require('pending_submission' in state and state['pending_submission'] is None,
        'unresolved pending submission; inspect without retry')
    c.require(all(j.get('experiment') == 'formal_main_v2' for j in jobs), 'foreign job supplied to capacity gate')
    c.require(len({j['job_id'] for j in jobs}) == len(jobs), 'duplicate registered job ID')
    c.require(not any(j.get('stage_key') == c.STAGE for j in jobs), 'this single-attempt stage already exists')
    active = [j for j in jobs if reserves_slot(j)]
    c.require(len({j.get('stage_key') for j in active}) == len(active), 'duplicate active stage; root inspection required')
    return active, len(active) < 8


def remote_hashes(f, names):
    # Source/metadata paths were checked locally. Repeat canonical/symlink checks
    # on the server before any hash, and reject missing keys in the response.
    script = '''from pathlib import Path
import hashlib,json
names=NAMES
out={}
for name in names:
 p=Path(name)
 if p.resolve()!=p.absolute() or any(x.is_symlink() for x in (p,*p.parents)):
  raise ValueError('server metadata alias: '+name)
 out[name]=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
print(json.dumps(out))
'''.replace('NAMES', repr(list(names)))
    # Send the potentially large source/path payload through stdin, not Windows argv.
    command = shlex.quote(c.H + '/venv/bin/python') + ' -B -'
    value = json.loads(subprocess.check_output(f.SSH + [command], input=script,
        text=True, encoding='utf-8'))
    c.require(type(value) is dict and set(value) == set(names)
        and all(v is None or (type(v) is str and re.fullmatch('[0-9a-f]{64}', v)) for v in value.values()),
        'invalid remote metadata hash response')
    return value


def remote_attempt_absent(f):
    script = '''from pathlib import Path
import json
root=Path(OUT)
inv=Path(INV)
if any(x.is_symlink() for x in (root,*root.parents,inv,*inv.parents)):
 raise ValueError('stage path alias')
print(json.dumps(dict(invocation_exists=inv.exists(),
 unexpected_entries=sorted(x.name for x in root.iterdir() if x.name!='source') if root.exists() else [])))
'''.replace('OUT', repr(c.P + '/' + c.OUT)).replace('INV', repr(c.P + '/' + c.INVOCATION))
    value = json.loads(f.remote(shlex.quote(c.H + '/venv/bin/python') + ' -c ' + shlex.quote(script)))
    c.require(value == {'invocation_exists': False, 'unexpected_entries': []}, 'existing remote attempt/invocation; never retry')


def publish_missing(f, local, server, expected):
    """Publish missing immutable bytes with an exclusive hard-link commit."""
    c.valid_sha(expected)
    partial = server + '.upload-' + expected + '.partial'
    preflight = '''from pathlib import Path
p=Path(SERVER);tmp=Path(TMP)
if p.exists() or tmp.exists() or any(x.is_symlink() for x in (p,*p.parents,tmp,*tmp.parents)):
 raise ValueError('existing destination or partial upload; inspect before retry')
p.parent.mkdir(parents=True,exist_ok=True)
'''.replace('SERVER', repr(server)).replace('TMP', repr(partial))
    f.remote(shlex.quote(c.H + '/venv/bin/python') + ' -c ' + shlex.quote(preflight))
    subprocess.run(['scp', '-q', str(local), 'tongji-cvpr:' + partial], check=True)
    commit = '''from pathlib import Path
import hashlib,os
p=Path(SERVER);tmp=Path(TMP)
if p.exists() or tmp.is_symlink() or any(x.is_symlink() for x in p.parents):
 raise ValueError('destination changed during upload')
if hashlib.sha256(tmp.read_bytes()).hexdigest()!=EXPECTED:raise ValueError('uploaded SHA differs')
os.link(tmp,p)
tmp.unlink()
'''.replace('SERVER', repr(server)).replace('TMP', repr(partial)).replace('EXPECTED', repr(expected))
    f.remote(shlex.quote(c.H + '/venv/bin/python') + ' -c ' + shlex.quote(commit))


def publish_local(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def execute_submit(project, checked, refs, f):
    """Only root calls this function after local review. No automatic retries."""
    project = Path(project).resolve()
    c.require(f.ROOT.resolve() == project and f.P == c.P and f.H == c.H, 'supervisor project differs')
    watched = checked['watched_files']; mapping = checked['deployment_files']
    c.require(c.sha(Path(__file__).resolve()) == watched[c.P + '/' + c.SUBMITTER]
        and c.sha(Path(__file__).resolve().parent / 'launcher.py') == watched[c.P + '/' + c.LAUNCHER], 'executed dispatcher source differs')
    with f.supervisor_lock():
        state = f.read(f.STATE)
        c.require(state.get('pending_submission') is None and 'pending_submission' in state, 'unresolved pending submission')
        jobs = f.refresh(state)
        active, available = submission_gate(state, jobs)
        if not available:
            return dict(submitted=False, reason='all8slotsoccupied', active_request_job_ids=[j['job_id'] for j in active])
        inv_path = c.safe_local(project, c.INVOCATION)
        c.require(not inv_path.exists(), 'prior local invocation exists; inspect, never retry')
        remote_attempt_absent(f)
        observed = remote_hashes(f, watched)
        c.require(all(v is None or v == watched[k] for k, v in observed.items()), 'remote immutable evidence differs; no overwrite')
        for row in mapping:
            if observed[row['server']] is None:
                publish_missing(f, c.safe_local(project, row['path']), row['server'], row['sha256'])
        c.require(remote_hashes(f, watched) == watched, 'remote deployment closure differs after upload')
        # Do not silently use an earlier local read if evidence changed during upload.
        rechecked = c.check_contract(project, root_ref=refs['root_review'], manifest_ref=refs['manifest'], registration_ref=refs['gpu_registration'])
        c.require(rechecked['watched_files'] == watched, 'local contract changed before publication')
        remote_attempt_absent(f)
        now = datetime.now(timezone.utc).isoformat()
        invocation = dict(schema='formal_main_v2', kind='bounded_action_execution_engineering_invocation',
            stage='engineering', stage_key=c.STAGE, source_root=c.S, source_sha256=c.SOURCE_SHA,
            entrypoint_server=c.P + '/' + c.ENTRY, entrypoint_sha256=watched[c.P + '/' + c.ENTRY],
            launcher_sha256=watched[c.P + '/' + c.LAUNCHER], wrapper_sha256=watched[c.P + '/' + c.WRAPPER],
            submitter_sha256=watched[c.P + '/' + c.SUBMITTER], watched_files=watched,
            root_review=refs['root_review'], manifest=refs['manifest'], gpu_registration=refs['gpu_registration'],
            output_root=c.P + '/' + c.OUT, dispatch_contract=c.DISPATCH,
            registered_utc=now, active_request_job_ids_before=[j['job_id'] for j in active],
            suites=list(c.SUITES), methods=list(c.METHODS))
        encoded = (json.dumps(invocation, ensure_ascii=False, indent=2) + '\n').encode()
        import hashlib
        inv_sha = hashlib.sha256(encoded).hexdigest()
        # Any failure from this point remains a durable unresolved transaction,
        # including copy failure or an ambiguous sbatch reply. No retry path exists.
        state['pending_submission'] = dict(stage_key=c.STAGE, invocation=c.INVOCATION,
            invocation_sha256=inv_sha, status='prepared_before_invocation_publication', utc=now)
        f.write(f.STATE, state)
        publish_local(inv_path, encoded)
        publish_missing(f, inv_path, c.P + '/' + c.INVOCATION, inv_sha)
        c.require(remote_hashes(f, [c.P + '/' + c.INVOCATION]) == {c.P + '/' + c.INVOCATION: inv_sha}, 'remote invocation differs')
        export = 'ALL,INVOCATION=' + c.P + '/' + c.INVOCATION + ',INVOCATION_SHA256=' + inv_sha + ',WRAPPER_SHA256=' + invocation['wrapper_sha256']
        command = 'cd ' + shlex.quote(c.P) + ' && sbatch --parsable --export=' + shlex.quote(export) + ' ' + shlex.quote(c.P + '/' + c.WRAPPER)
        answer = subprocess.run(f.SSH + [command], capture_output=True, text=True)
        reply = answer.stdout.strip()
        if answer.returncode or not re.fullmatch(r'[0-9]+(?:;[A-Za-z0-9_.-]+)?', reply):
            raise RuntimeError('Unknown sbatch outcome; pending preserved, no retry: ' + answer.stdout + answer.stderr)
        jid = reply.split(';')[0]
        c.require(jid not in {str(j['job_id']) for j in state['registered_jobs']}, 'submitted ID already registered')
        state['pending_submission'].update(status='submitted_identifier_observed', known_job_id=jid)
        f.write(f.STATE, state)
        job = dict(job_id=jid, name='cti-action-exec16', experiment='formal_main_v2', mode='engineering',
            stage_key=c.STAGE, suite=None, suites=list(c.SUITES), visual_tokens=None, training_seed=17, segment_end=None,
            status='SUBMITTED', gpus=1, source_root=c.S, source_sha256=c.SOURCE_SHA,
            run_root=c.P + '/' + c.OUT + '/' + jid, invocation=c.INVOCATION, invocation_sha256=inv_sha,
            submitted_utc=now, maximum_attempts=1, automatic_retry=False, wall_limit_seconds=3600,
            expected_engineering_cells=16, scientific_trials=0, final_states_opened=False,
            purpose='Fixed four-suite sixteen-cell action-execution engineering acceptance; no success-rate result or automatic failed-Object-trial replay')
        f.write(project / (c.BASE + 'submissions/' + jid + '.json'), job)
        state['registered_jobs'].append(job); state['pending_submission'] = None
        state['current_round_cost']['registered_jobs'] = len(jobs) + 1
        state['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs'] = len(active) + 1
        state['updated_utc'] = now
        f.write(f.STATE, state)
        return dict(submitted=True, job=job)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', type=Path, required=True)
    for name in ('root-review', 'manifest', 'gpu-registration'):
        parser.add_argument('--' + name, required=True)
        parser.add_argument('--' + name + '-sha256', required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check-only', action='store_true')
    mode.add_argument('--submit', action='store_true')
    args = parser.parse_args()
    project = args.project_root.resolve()
    refs = {name: dict(path=getattr(args, name), sha256=getattr(args, name + '_sha256'))
            for name in ('root_review', 'manifest', 'gpu_registration')}
    checked = c.check_contract(project, root_ref=refs['root_review'], manifest_ref=refs['manifest'], registration_ref=refs['gpu_registration'])
    c.require(c.sha(Path(__file__).resolve()) == checked['watched_files'][c.P + '/' + c.SUBMITTER]
        and c.sha(Path(__file__).resolve().parent / 'launcher.py') == checked['watched_files'][c.P + '/' + c.LAUNCHER],
        'executed dispatcher source differs')
    if args.check_only:
        print(json.dumps(dict(status='local_dispatch_contract_verified_no_submission', stage_key=c.STAGE,
            watched_files=len(checked['watched_files']), engineering_cells=16, scientific_trials=0,
            source_files=173, remote_checked=False, GPU_submitted=False)))
        return
    supervisor = c.safe_local(project, c.SUPERVISOR)
    c.require(c.sha(supervisor) == c.SUPERVISOR_SHA, 'frozen root supervisor differs')
    spec = importlib.util.spec_from_file_location('_formal_supervisor_action_execution_dispatch', supervisor)
    f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
    print(json.dumps(execute_submit(project, checked, refs, f)), flush=True)


if __name__ == '__main__':
    main()

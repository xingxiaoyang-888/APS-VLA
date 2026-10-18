"""Unsubmitted root-pinned launcher for exactly sixteen engineering cells.

Pure validation functions are shared with the local submitter. This module does
not import torch, a model, a simulator or the probe. The Linux execution path is
entered only by main() with an exact registered Slurm invocation.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import time

P = '/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA'
H = '/share/home/u15016/XXY_CVPR/CTI-VLA'
SOURCE_NAME = 'formal_main_v2_run_564be0995e'
S = P + '/snapshots/' + SOURCE_NAME
STAGE = 'formal_main_v2_action_execution_compat_gpu_v4'
VERSION = 'action-execution-gpu-candidate-1940-v4-runtime-lifecycle'
DISPATCH_VERSION = 'root-action-execution-engineering-dispatch-v4-runtime-lifecycle'
BASE = 'results/formal_main_v2/'
OUT = BASE + 'engineering/' + STAGE
ENTRY = OUT + '/source/probe.py'
LAUNCHER = OUT + '/source/launcher.py'
WRAPPER = OUT + '/source/probe.slurm'
SUBMITTER = OUT + '/source/submit.py'
INVOCATION = BASE + 'invocations/' + STAGE + '_attempt01.json'
INVENTORY = BASE + 'source/' + SOURCE_NAME + '.json'
INVENTORY_SHA = '5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
SOURCE_SHA = 'dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e'
SUPERVISOR = 'scripts/formal_supervisor.py'
SUPERVISOR_SHA = '3e0786da690552356bbe2f56458fe19e88c90b4de079211dc652d655fe3c2e95'
ADAPTER = 'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py'
ADAPTER_SHA = 'b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185'
ADAPTER_INDEPENDENT_SHA = '171b93b145431bdffb9138eea48673e9185dcadbef226e468d0ab140a7a470f1'
ADAPTER_INDEPENDENT_STATUS = 'passed_CPU_review_GPU_acceptance_pending'
SUITES = ('libero_10', 'libero_spatial', 'libero_object', 'libero_goal')
METHODS = ('dense', 'uniform128', 'A128_seed17', 'B128_seed17')
PANELS = frozenset(f'configs/manifests/formal_main_v2/{s}/initial_states/development.json' for s in SUITES)
LIMITS = dict(env_seed=0, runtime_seed=17, wait_steps=10, max_control_steps=8,
    action_chunk=8, cells=16, max_vla_calls=16, max_vision_calls=16,
    policy_watchdog_seconds=60, wall_seconds=3600)
DISPATCH = dict(version=DISPATCH_VERSION, stage_key=STAGE, source_root=S,
    source_sha256=SOURCE_SHA, output_root=P + '/' + OUT, max_active_requests=8,
    GPU_count=1, wall_limit_seconds=3600, maximum_attempts=1, automatic_retry=False,
    engineering_cells=16, scientific_trials=0, final_states_opened=False,
    failed_Object_trial_automatically_replayed=False)
FORBIDDEN_SUFFIXES = {'.pt', '.pth', '.bin', '.ckpt', '.safetensors', '.npz', '.npy',
    '.pkl', '.pickle', '.init', '.pruned_init'}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda: stream.read(8 << 20), b''):
            digest.update(part)
    return digest.hexdigest()


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def valid_sha(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'invalid SHA256')
    return value


def lexical_relative(value):
    """Reject forbidden aliases before resolve/stat/hash, including state payloads."""
    require(type(value) is str and value and '\\' not in value and ':' not in value,
        'invalid relative metadata path')
    p = PurePosixPath(value)
    require(not p.is_absolute() and p.as_posix() == value and '..' not in p.parts,
        'noncanonical metadata path')
    low = value.lower(); parts = low.split('/')
    source = p.suffix == '.py' and p.parts[0] in {'src', 'scripts', 'tests'}
    states = any(stem in part for part in parts for stem in ('init_state', 'initial_state', 'final_state', 'test_state'))
    require(not any('sealed' in part or part in {'weights', 'checkpoints', 'test', 'final'} for part in parts)
        and 'final_registry' not in low and p.suffix.lower() not in FORBIDDEN_SUFFIXES
        and p.suffix.lower() in {'.py', '.json', '.jsonl', '.slurm', '.sh', '.toml', '.txt', '.md', '.log', '.xml', '.out', '.err'}
        and p.name.lower() not in {'panel.json', 'state.json'}
        and (not states or source or value in PANELS), 'forbidden metadata/weight/state path')
    return value


def safe_local(root, relative):
    relative = lexical_relative(relative)
    root = Path(root).absolute(); target = root / relative
    require(root.resolve() in target.resolve().parents and target.resolve() == target.absolute(),
        'metadata path escape or alias')
    for part in (target, *target.parents):
        if part == root:
            break
        require(not part.is_symlink(), 'metadata symlink')
    return target


def read_ref(project, ref):
    require(type(ref) is dict and set(ref) == {'path', 'sha256'}, 'expected exact path/SHA reference')
    p = safe_local(project, ref['path']); expected = valid_sha(ref['sha256'])
    require(sha(p) == expected, 'metadata SHA differs: ' + ref['path'])
    return json.loads(p.read_bytes())


def registration_intent(reg):
    """Root receipt signs all registration fields except its own reference."""
    value = copy.deepcopy(reg)
    require(type(value.get('cpu_reviews')) is dict and 'root_acceptance' in value['cpu_reviews'], 'CPU gate missing')
    del value['cpu_reviews']['root_acceptance']
    return signature(value)


def check_cpu_review(project, ref, name, identity):
    require(type(ref) is dict and set(ref) == {'path', 'sha256', 'accepted_status'}, 'CPU reference fields differ')
    receipt = read_ref(project, {k: ref[k] for k in ('path', 'sha256')})
    if name == 'action_adapter_independent':
        require(ref['sha256'] == ADAPTER_INDEPENDENT_SHA and ref['accepted_status'] == receipt.get('status') == ADAPTER_INDEPENDENT_STATUS
            and receipt.get('schema') == 'formal_main_v2'
            and receipt.get('kind') == 'action_constructor_identity_independent_CPU_review'
            and receipt.get('candidate_sha256') == ADAPTER_SHA, 'adapter independent CPU gate differs')
        return receipt
    role = {'candidate_independent': 'independent', 'root_acceptance': 'root'}[name]
    status = 'passed_CPU_' + role + '_review_pending_registered_GPU'
    require(receipt.get('schema') == 'formal_main_v2' and receipt.get('version') == VERSION
        and receipt.get('kind') == 'bounded_action_execution_GPU_candidate_' + role + '_CPU_review'
        and receipt.get('status') == ref['accepted_status'] == status
        and receipt.get('candidate_identity') == identity, 'typed candidate CPU gate differs')
    files = receipt.get('candidate_files')
    require(type(files) is dict and set(files) == {'probe', 'manifest', 'action_adapter'}, 'CPU candidate files differ')
    for key, expected in [('probe', identity['probe_sha256']), ('manifest', identity['manifest_sha256']), ('action_adapter', ADAPTER_SHA)]:
        row = files[key]
        require(type(row) is dict and set(row) == {'path', 'sha256'} and row['sha256'] == expected
            and receipt.get('evidence_sha256', {}).get(row['path']) == expected, 'CPU candidate evidence binding differs')
        require(sha(safe_local(project, row['path'])) == expected, 'CPU candidate source bytes differ')
    require(files['action_adapter']['path'] == ADAPTER, 'published adapter path differs')
    return receipt


def check_contract(project, *, root_ref, manifest_ref, registration_ref, on_server=False):
    """Validate complete local inputs and exact deployment closure; no side effects."""
    root_review = read_ref(project, root_ref)
    reg = read_ref(project, registration_ref)
    manifest = read_ref(project, manifest_ref)
    require(type(reg.get('limits')) is dict and reg['limits'] == LIMITS
        and all(type(reg['limits'][k]) is int for k in LIMITS), 'fixed limits differ')
    require(reg.get('schema') == 'formal_main_v2' and reg.get('version') == STAGE
        and reg.get('status') == 'registered_single_attempt' and reg.get('gpu_submission_authorized') is True
        and reg.get('candidate_manifest') == manifest_ref and reg.get('output_root') == P + '/' + OUT and 'output' not in reg
        and reg.get('suite_order') == list(SUITES) and reg.get('method_order') == list(METHODS)
        and type(reg.get('gpus')) is int and reg['gpus'] == 1
        and type(reg.get('attempt')) is int and reg['attempt'] == 1 and reg.get('automatic_retry') is False,
        'root GPU contract differs')
    entry = reg.get('entrypoint')
    require(type(entry) is dict and set(entry) == {'path', 'sha256'} and entry['path'] == P + '/' + ENTRY,
        'unregistered GPU entrypoint')
    valid_sha(entry['sha256'])
    require(set(reg.get('cpu_reviews', {})) == {'action_adapter_independent', 'candidate_independent', 'root_acceptance'}, 'CPU gates incomplete')
    require({k: reg['cpu_reviews']['root_acceptance'][k] for k in ('path', 'sha256')} == root_ref,
        'CPU root reference is not supplied root receipt')
    identity = dict(probe_sha256=entry['sha256'], manifest_sha256=manifest_ref['sha256'], action_adapter_sha256=ADAPTER_SHA)
    cpu = {name: check_cpu_review(project, ref, name, identity) for name, ref in reg['cpu_reviews'].items()}
    require(cpu['root_acceptance'] == root_review and root_review.get('candidate_independent_review') ==
        {k: reg['cpu_reviews']['candidate_independent'][k] for k in ('path', 'sha256')}, 'root did not bind exact independent review')
    require(root_review.get('dispatch_contract') == DISPATCH and root_review.get('gpu_registration_path') == registration_ref['path']
        and root_review.get('gpu_registration_intent_sha256') == registration_intent(reg), 'root dispatch/registration intent differs')
    require(manifest.get('schema') == 'formal_main_v2' and manifest.get('version') == VERSION
        and manifest.get('candidate_only') is True and manifest.get('gpu_submission_authorized') is False
        and manifest.get('limits') == LIMITS and manifest.get('suite_order') == list(SUITES)
        and manifest.get('method_order') == list(METHODS) and set(manifest.get('suites', {})) == set(SUITES)
        and manifest.get('action_adapter', {}).get('path') == ADAPTER and manifest['action_adapter'].get('sha256') == ADAPTER_SHA,
        'candidate manifest identity differs')
    inventory = read_ref(project, dict(path=INVENTORY, sha256=INVENTORY_SHA))
    frozen = inventory.get('files')
    require(type(frozen) is dict and len(frozen) == 173 and inventory.get('source_root_server') == S
        and inventory.get('source_sha256') == SOURCE_SHA
        and hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest() == SOURCE_SHA, 'frozen inventory differs')
    required = {}
    def need(relative, digest, server=None):
        relative = lexical_relative(relative); valid_sha(digest)
        server = server or P + '/' + relative
        require(server not in required or required[server] == (relative, digest), 'contradictory deployment identity')
        required[server] = (relative, digest)
    for relative, digest in frozen.items():
        need(relative, digest, S + '/' + relative)
    for relative, digest in manifest.get('read_evidence_sha256', {}).items():
        need(relative, digest)
    for relative, digest in root_review.get('evidence_sha256', {}).items():
        require(relative not in {root_ref['path'], registration_ref['path']}, 'root receipt hash cycle')
        need(relative, digest)
    for receipt in cpu.values():
        for ref in receipt.get('candidate_files', {}).values():
            need(ref['path'], ref['sha256'])
    for ref in reg['cpu_reviews'].values():
        if ref['path'] != root_ref['path']:
            need(ref['path'], ref['sha256'])
    need(INVENTORY, INVENTORY_SHA)
    need(manifest_ref['path'], manifest_ref['sha256'])
    need(ENTRY, entry['sha256'])
    need(ADAPTER, ADAPTER_SHA)
    # Published tooling must be in the root's immutable evidence map.
    for relative in (LAUNCHER, WRAPPER, SUBMITTER):
        require(relative in root_review.get('evidence_sha256', {}), 'unbound dispatch source')
        need(relative, root_review['evidence_sha256'][relative])
    need(SUPERVISOR, SUPERVISOR_SHA)
    # Every declared metadata reference used by prepare() must be covered. The
    # two absolute actual-controller source references are server-only evidence,
    # not downloadable local files; the probe verifies them on the GPU node.
    def refs(value):
        if isinstance(value, dict):
            if 'path' in value and 'sha256' in value and not str(value['path']).startswith('/'):
                need(value['path'], value['sha256'])
            for child in value.values(): refs(child)
        elif isinstance(value, list):
            for child in value: refs(child)
    refs(manifest)
    for suite in SUITES:
        row = manifest['suites'][suite]
        require(row['panel']['path'] in PANELS and row['panel']['path'].split('/')[3] == suite, 'cross-suite development panel')
        for contract in row.get('compatibility', {}).values():
            for relative, digest in contract['files'].items(): need(relative, digest)
            need(contract['adapter'], contract['files'][contract['adapter']])
    rows = root_review.get('deployment_files')
    require(type(rows) is list and rows, 'missing root deployment mapping')
    mapping = {}
    for row in rows:
        require(type(row) is dict and set(row) == {'path', 'server', 'sha256', 'bytes'}, 'deployment row fields differ')
        relative = lexical_relative(row['path']); digest = valid_sha(row['sha256']); server = row['server']
        require(relative not in {root_ref['path'], registration_ref['path']}, 'cyclic deployment mapping')
        allowed = {P + '/' + relative}
        if frozen.get(relative) == digest: allowed.add(S + '/' + relative)
        require(server in allowed and server not in mapping, 'duplicate/aliased deployment destination')
        require(type(row['bytes']) is int and row['bytes'] >= 0, 'invalid byte count')
        path = safe_server(server) if on_server else safe_local(project, relative)
        require(path.stat().st_size == row['bytes'] and sha(path) == digest, 'local deployment bytes differ: ' + relative)
        mapping[server] = dict(row)
    require(set(mapping) == set(required), 'deployment closure mismatch: missing=' + repr(sorted(set(required)-set(mapping)))
        + ';extra=' + repr(sorted(set(mapping)-set(required))))
    for server, (relative, digest) in required.items():
        require(mapping[server]['path'] == relative and mapping[server]['sha256'] == digest, 'deployment closure SHA differs')
    for ref in (root_ref, registration_ref):
        path = safe_local(project, ref['path']); server = P + '/' + ref['path']
        require(server not in mapping, 'root/registration destination collision')
        mapping[server] = dict(path=ref['path'], server=server, sha256=ref['sha256'], bytes=path.stat().st_size)
    return dict(root_review=root_review, registration=reg, manifest=manifest, inventory=inventory,
        deployment_files=list(mapping.values()), watched_files={s: r['sha256'] for s, r in mapping.items()})


def safe_server(name):
    require(type(name) is str, 'server path must be string')
    prefix = S + '/' if name.startswith(S + '/') else P + '/'
    require(name.startswith(prefix), 'server path outside project')
    relative = lexical_relative(name[len(prefix):])
    return safe_local(prefix[:-1], relative)


def validate_invocation(inv, job, invocation_sha):
    require(re.fullmatch('[0-9]+', job or '') and valid_sha(invocation_sha), 'invalid Slurm identity')
    require(inv.get('schema') == 'formal_main_v2' and inv.get('kind') == 'bounded_action_execution_engineering_invocation'
        and inv.get('stage') == 'engineering' and inv.get('stage_key') == STAGE
        and inv.get('dispatch_contract') == DISPATCH and inv.get('source_root') == S and inv.get('source_sha256') == SOURCE_SHA
        and inv.get('entrypoint_server') == P + '/' + ENTRY and inv.get('output_root') == P + '/' + OUT,
        'invocation stage/source/bounds differ')
    watched = inv.get('watched_files')
    require(type(watched) is dict and watched and watched.get(P + '/' + ENTRY) == inv.get('entrypoint_sha256')
        and watched.get(P + '/' + WRAPPER) == inv.get('wrapper_sha256')
        and watched.get(P + '/' + LAUNCHER) == inv.get('launcher_sha256'), 'invocation tools unbound')
    for name, digest in watched.items():
        safe_server(name); valid_sha(digest)
    for key in ('root_review', 'manifest', 'gpu_registration'):
        ref = inv.get(key)
        require(type(ref) is dict and set(ref) == {'path', 'sha256'}, 'invocation reference differs')
        lexical_relative(ref['path']); valid_sha(ref['sha256'])
        require(watched.get(P + '/' + ref['path']) == ref['sha256'], 'invocation metadata not watched')
    return watched


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--invocation', required=True)
    parser.add_argument('--invocation-sha256', required=True)
    args = parser.parse_args()
    require(args.invocation == P + '/' + INVOCATION, 'unregistered invocation path')
    path = safe_server(args.invocation)
    require(sha(path) == valid_sha(args.invocation_sha256), 'invocation SHA differs')
    inv = json.loads(path.read_bytes()); job = os.environ.get('SLURM_JOB_ID', '')
    watched = validate_invocation(inv, job, args.invocation_sha256)
    require(Path(__file__).resolve() == Path(P + '/' + LAUNCHER)
        and sha(__file__) == inv['launcher_sha256'], 'launcher origin/SHA differs')
    import fcntl
    locks = Path(P) / BASE / 'stage_locks'; locks.mkdir(parents=True, exist_ok=True)
    receipts = Path(P) / BASE / 'job_receipts'; receipts.mkdir(parents=True, exist_ok=True)
    output_root = Path(P) / OUT; receipt = receipts / (job + '.json')
    started = time.monotonic(); start_utc = datetime.now(timezone.utc).isoformat()
    with (locks / (STAGE + '.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not receipt.exists(), 'existing job receipt; never repeat')
        require(not any(x.name.isdigit() for x in output_root.iterdir()), 'existing stage attempt; never repeat')
        marker = output_root / 'attempt01.launcher_started.json'
        # Durable one-shot marker survives child failures, node restart or requeue.
        with marker.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(dict(job_id=job, invocation_sha256=args.invocation_sha256, started_utc=start_utc), stream)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        code, error, before, after, command = 1, None, False, False, None
        try:
            for name, digest in watched.items(): require(sha(safe_server(name)) == digest, 'changed deployment: ' + name)
            checked = check_contract(P, root_ref=inv['root_review'], manifest_ref=inv['manifest'], registration_ref=inv['gpu_registration'], on_server=True)
            require(checked['watched_files'] == watched, 'invocation deployment closure differs')
            before = True
            command = [sys.executable, '-B', P + '/' + ENTRY, '--project-root', P, '--source-root', S,
                '--manifest', inv['manifest']['path'], '--manifest-sha256', inv['manifest']['sha256'],
                '--gpu-registration', inv['gpu_registration']['path'], '--gpu-registration-sha256', inv['gpu_registration']['sha256'],
                '--job-id', job, '--script-sha256', inv['entrypoint_sha256'], '--execute-gpu']
            remaining = 3540 - (time.monotonic() - started)
            require(remaining > 0, 'launcher verification exhausted bounded walltime')
            child = subprocess.run(command, cwd=S, timeout=remaining)
            code = child.returncode
        except BaseException as exc:
            code = 1; error = dict(type=type(exc).__name__, message=str(exc))
        finally:
            try:
                for name, digest in watched.items(): require(sha(safe_server(name)) == digest, 'changed deployment after child: ' + name)
                after = True
            except BaseException as exc:
                code = 1; error = dict(type=type(exc).__name__, message=str(exc), prior_error=error)
            value = dict(schema='formal_main_v2', kind='bounded_engineering_launcher_receipt',
                version=DISPATCH_VERSION, job_id=job, stage='engineering', stage_key=STAGE,
                invocation_sha256=args.invocation_sha256, source_sha256=SOURCE_SHA,
                entrypoint_sha256=inv['entrypoint_sha256'], manifest=inv['manifest'], gpu_registration=inv['gpu_registration'],
                root_review=inv['root_review'], watched_inputs_verified_before=before, watched_inputs_verified_after=after,
                started_utc=start_utc, finished_utc=datetime.now(timezone.utc).isoformat(),
                wall_seconds=time.monotonic()-started, exit_code=code, error=error, command=command,
                output=str(output_root / job), expected_engineering_cells=16, scientific_trials=0,
                final_states_opened=False, scientific_completion_inferred=False,
                allocation_cost_must_be_accounted_by_root=True,
                status='process_finished_pending_root_review' if code == 0 else 'failed')
            with receipt.open('x', encoding='utf-8', newline='\n') as stream:
                json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    return code


if __name__ == '__main__':
    raise SystemExit(main())

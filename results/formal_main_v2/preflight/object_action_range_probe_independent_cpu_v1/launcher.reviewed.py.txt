"""Root-pinned one-shot engineering launcher; never edits frozen runtime."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time

P = Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S = P / 'snapshots/formal_main_v2_run_564be0995e'
R = P / 'results/formal_main_v2'
STAGE = 'libero_object_action_range_probe_v1'
OUTPUT = R / 'engineering/object_action_range_probe_v1'
SOURCE_SHA = 'dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e'
REG_SHA = 'c87c76f8a3175bd760551c530f65990d08a88ab6a41d2771b44120e9cea25a3d'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def safe_input(name):
    """Only metadata/source plus the single already public development panel."""
    p = Path(name)
    low = name.lower()
    parts = low.split('/')
    allowed_panel = str(P / 'configs/manifests/formal_main_v2/libero_object/initial_states/development.json')
    source_code = p.suffix == '.py' and any(x in parts for x in ('src', 'scripts', 'tests'))
    state_named = any(stem in part for part in parts for stem in ('init_state', 'initial_state', 'final_state', 'test_state'))
    if (not p.is_absolute() or P not in p.parents or '..' in p.parts
            or any(x in parts for x in ('weights', 'checkpoints', 'final', 'test'))
            or any('sealed' in x for x in parts) or 'final_registry' in low
            or p.suffix.lower() in ('.pt', '.pth', '.bin', '.ckpt', '.safetensors', '.pkl', '.pickle', '.init', '.pruned_init')
            or (state_named and name != allowed_panel and not source_code)):
        raise ValueError('Unapproved engineering input: ' + name)
    if p.is_symlink() or p.resolve() != p:
        raise ValueError('Aliased engineering input: ' + name)
    return p


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--invocation', type=Path, required=True)
    parser.add_argument('--invocation-sha256', required=True)
    args = parser.parse_args()
    job = os.environ.get('SLURM_JOB_ID', '')
    path = args.invocation
    if (not re.fullmatch(r'[0-9]+', job) or path.parent != R / 'invocations'
            or sha(safe_input(str(path))) != args.invocation_sha256):
        raise ValueError('Registered Slurm invocation identity missing')
    inv = json.loads(path.read_bytes())
    if (inv.get('schema') != 'formal_main_v2' or inv.get('stage') != 'engineering'
            or inv.get('stage_key') != STAGE or inv.get('source_root') != str(S)
            or inv.get('source_sha256') != SOURCE_SHA or inv.get('registration_sha256') != REG_SHA
            or inv.get('wall_limit_seconds') != 900 or inv.get('maximum_attempts') != 1
            or inv.get('automatic_retry') is not False or inv.get('GPU_count') != 1):
        raise ValueError('Unknown engineering identity or bounds')
    entry = safe_input(inv['entrypoint_server'])
    if entry.parent != OUTPUT / 'source' or entry.name != 'probe.py':
        raise ValueError('Unregistered external diagnostic entrypoint')
    watched = inv['watched_files']
    wrapper = str(OUTPUT / 'source/probe.slurm')
    registration = str(P / 'configs/experiments/formal_main_v2_object_action_range_probe_v1.json')
    if (not isinstance(watched, dict) or watched.get(str(entry)) != inv['entrypoint_sha256']
            or watched.get(str(Path(__file__).resolve())) != sha(__file__)
            or watched.get(wrapper) != inv.get('wrapper_sha256') or wrapper not in watched
            or watched.get(registration) != REG_SHA):
        raise ValueError('Launcher/entry missing from immutable evidence')
    output = OUTPUT / job
    if output.exists():
        raise ValueError('Existing diagnostic result; no retry')
    locks = R / 'stage_locks'
    locks.mkdir(parents=True, exist_ok=True)
    receipts = R / 'job_receipts'
    receipts.mkdir(parents=True, exist_ok=True)
    receipt = receipts / (job + '.json')
    if receipt.exists():
        raise ValueError('Existing engineering job receipt')
    started = time.monotonic()
    code, error, verified_before, verified_after = 1, None, False, False
    with (locks / (STAGE + '.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            for name, digest in watched.items():
                if sha(safe_input(name)) != digest:
                    raise ValueError('Engineering dependency changed: ' + name)
            verified_before = True
            command = [sys.executable, '-B', str(entry), '--project-root', str(P),
                '--source-root', str(S), '--job-id', job, '--script-sha256', inv['entrypoint_sha256'], '--execute-gpu']
            remaining = max(1, 890 - (time.monotonic() - started))
            code = subprocess.run(command, cwd=S, timeout=remaining).returncode
            for name, digest in watched.items():
                if sha(safe_input(name)) != digest:
                    raise ValueError('Engineering input changed during execution: ' + name)
            verified_after = True
        except BaseException as exc:
            code = 1
            error = dict(type=type(exc).__name__, message=str(exc))
        value = dict(schema='formal_main_v2', kind='bounded_engineering_launcher_receipt',
            job_id=job, stage='engineering', stage_key=STAGE, invocation_sha256=args.invocation_sha256,
            source_sha256=SOURCE_SHA, entrypoint_sha256=inv['entrypoint_sha256'],
            watched_inputs_verified_before=verified_before, watched_inputs_verified_after=verified_after,
            finished_utc=datetime.now(timezone.utc).isoformat(), wall_seconds=time.monotonic()-started,
            exit_code=code, error=error, output=str(output), new_trials=0, final_states_opened=False,
            status='process_finished_pending_root_review' if code == 0 else 'failed')
        with receipt.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    return code


if __name__ == '__main__':
    raise SystemExit(main())

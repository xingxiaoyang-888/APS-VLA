"""Root-only Object/Goal submission with the registered metadata adapter.

This does not replace the frozen training or acceptance entrypoints. Only the
explicitly registered external wrapper is new. Plans and submissions retain
the original scientific argv, source, manifests, pair output, and stage lock.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import formal_supervisor as f

ROUND = f.ROUND
ACTIVE = f.ACTIVE | {'SUBMITTED'}
SUITES = ('libero_object', 'libero_goal')
SOURCE_INVENTORY = 'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
SOURCE_INVENTORY_SHA = '5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
PARALLEL = 'configs/experiments/formal_main_v2_parallel_execution_v1.json'
PARALLEL_SHA = 'e1378e74d1ad89af2d38d2f8eb8ce33695a346331c2e89db6313a5608faf4907'
RUNTIME_KEYS = {
    'schema': ROUND, 'kind': 'asset_metadata_compatibility',
    'version': 'formal-asset-metadata-compat-v1',
    'wrapper': 'scripts/server/run_formal_asset_stage.py',
    'slurm': 'scripts/server/formal_asset_main.slurm',
    'adapter': 'scripts/ops/formal_asset_metadata_adapter.py',
    'registration': 'configs/experiments/formal_main_v2_asset_metadata_compat_v1.json',
}
PINNED_FILES = {
    RUNTIME_KEYS['adapter']: 'd1ca08465ffcf2682569b1224e2018f17fdba61feac1896f864cc981759397d0',
    RUNTIME_KEYS['registration']: '25c90cbfe2db6fdb130a16e6b98ab7ccfc8373a2853578bf73ef0d38283cfb44',
    'configs/assets/formal_main_v2_strict/libero_object.json': 'd8f1f9a5c1c8c040aa499fd9df35ebe4a039fd6c756b565cf6055046be0cf8b3',
    'configs/assets/formal_main_v2_strict/libero_goal.json': 'e55eac83f28854318524ba87fc6554c7a9708b328700232c055deb66a72e0d6c',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def local_path(root, value):
    path = Path(value)
    path = path if path.is_absolute() else root / path
    path = path.resolve()
    require(root.resolve() in path.parents, 'Evidence must belong to CTI-VLA')
    return path


def runtime_contract(root, registration_path):
    """An already saved root registration, not a newly computed implicit opt-in."""
    registration = f.read(local_path(root, registration_path))
    require(registration.get('schema') == ROUND and
            registration.get('kind') == 'asset_execution_registration' and
            registration.get('status') == 'reviewed', 'Execution registration must be reviewed')
    runtime = registration['runtime_compatibility']
    require(set(runtime) == set(RUNTIME_KEYS) | {'files'}, 'Unexpected runtime contract keys')
    require(all(runtime.get(k) == v for k, v in RUNTIME_KEYS.items()), 'Runtime contract differs')
    expected_files = set(PINNED_FILES) | {RUNTIME_KEYS['wrapper'], RUNTIME_KEYS['slurm']}
    require(set(runtime['files']) == expected_files, 'Runtime requires exactly six registered files')
    require(all(runtime['files'].get(k) == v for k, v in PINNED_FILES.items()), 'Audited adapter inputs changed')
    for rel, digest in runtime['files'].items():
        require(f.sha(local_path(root, rel)) == digest, 'Runtime file changed: ' + rel)
    require(registration.get('source_inventory_sha256') == SOURCE_INVENTORY_SHA,
            'Execution registration must bind the frozen source inventory')
    for rel, digest in registration.get('review_inputs', {}).items():
        require(f.sha(local_path(root, rel)) == digest, 'Execution review changed: ' + rel)
    require(registration.get('review_inputs'), 'Execution review inputs required')
    return runtime


def capacity(state, jobs):
    require(state.get('pending_submission') is None, 'Unresolved submission: inspect before retry')
    require(f.sha(ROOT / PARALLEL) == PARALLEL_SHA, 'Parallel registration changed')
    parallel = f.read(ROOT / PARALLEL)
    require(parallel['max_concurrent_project_GPU_jobs'] == 8 and parallel['GPU_per_job'] == 1,
            'Unregistered concurrency limit')
    # PENDING jobs can report AllocTRES=0; count their requested GPU stage.
    active = [j for j in jobs if j['status'] in ACTIVE and
              (j.get('gpus', 0) > 0 or j.get('mode') in {'acceptance', 'train', 'development', 'final', 'profile'})]
    require(len(active) < 8, 'All eight registered GPU slots are occupied')
    return active


def validate_pair_resume(root, pair, outrel, latest, review, runtime, target):
    """Bind the reviewed boundary to both actual server recovery files."""
    require(review.get('status') == 'passed' and review.get('job_id') == latest['job_id'] and
            review.get('runtime_compatibility') == runtime, 'Latest pair/runtime root review required')
    prior_target = latest['segment_end']
    completed = review.get('completed_by_arm', {})
    require(set(completed) == {'A', 'B'} and all(type(x) is int and 0 <= x <= prior_target for x in completed.values()),
            'Invalid reviewed A/B completed boundary')
    require(review.get('requested_segment_end') == prior_target and prior_target in range(500, 5001, 500),
            'Root review must match latest allocation boundary')
    expected_target = prior_target + 500 if all(x == prior_target for x in completed.values()) else prior_target
    require(target == expected_target <= 5000 and review.get('allowed_next_segment_end') == target,
            'Only the reviewed next500 boundary or original partial boundary is allowed')
    checks = review.get('server_resume_checks', [])
    specs = review.get('server_resume_checklist', [])
    for rows in (checks, specs):
        require(isinstance(rows, list) and len(rows) == 2 and {r.get('arm') for r in rows} == {'A', 'B'},
                'Resume evidence must contain unique A and B')
    bound = []
    for arm in ('A', 'B'):
        actual = next(r for r in checks if r['arm'] == arm)
        wanted = next(r for r in specs if r['arm'] == arm)
        path = pair['checkpoint_root_server'] + '/' + arm + '/resume.pt'
        require(actual.get('path') == wanted.get('path') == path, 'Resume path differs from registered arm')
        complete_rel = outrel + '/' + arm + '/training_report.json'
        report_rel = complete_rel if (root / complete_rel).exists() else outrel + '/' + arm + '/progress_report.json'
        report_path = root / report_rel
        if not report_path.exists():
            require(completed[arm] == 0 and wanted.get('must_exist') is False and wanted.get('sha256') is None and
                    actual.get('exists') is False and not any((root / outrel / arm / 'attempts').glob('*/cost_events.jsonl')),
                    'Missing started-arm recovery cannot be treated as a fresh initialization')
            bound.append(dict(arm=arm, path=path, exists=False))
            continue
        report = f.read(report_path)
        require(review.get('evidence_sha256', {}).get(report_rel) == f.sha(report_path), 'Unreviewed pair progress')
        digest = report.get('resume_sha256')
        if report_rel == complete_rel:
            require(completed[arm] == 5000, 'Final arm report before5000')
            # The frozen final report intentionally records deployment/best
            # weights, not recovery weights. Bind recovery to its reviewed
            # last committed update instead of inventing report fields.
            commits = []
            for event_file in (root / outrel / arm / 'attempts').glob('*/cost_events.jsonl'):
                event_rel = event_file.relative_to(root).as_posix()
                require(review.get('evidence_sha256', {}).get(event_rel) == f.sha(event_file),
                        'Unreviewed final-arm checkpoint events')
                commits.extend(row for row in (json.loads(line) for line in event_file.read_text(encoding='utf-8').splitlines() if line)
                               if row.get('event') == 'checkpoint_commit' and row.get('completed_update') == 5000)
            require(commits and {row.get('resume_sha256') for row in commits} == {wanted.get('sha256')},
                    'Final-arm recovery must match reviewed update5000 checkpoint commits')
            digest = wanted['sha256']
        require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest) and
                report.get('arm') == arm and report.get('training_updates_completed') == completed[arm] and
                report.get('next_sample_cursor') == completed[arm] * 8 and
                (report_rel == complete_rel or report.get('resume_checkpoint') == path),
                'Progress arm/boundary/cursor/resume identity differs')
        require(wanted.get('must_exist') is True and actual.get('exists') is True and
                actual.get('sha256') == wanted.get('sha256') == digest and
                type(actual.get('bytes')) is int and actual['bytes'] > 0,
                'Server resume identity or existence differs from reviewed progress')
        bound.append(dict(arm=arm, path=path, exists=True, sha256=digest, bytes=actual['bytes']))
    return bound


def verify_remote_resumes(checks):
    """Read hashes on the server only; never download recovery weights."""
    program = ('from pathlib import Path; import hashlib,json; checks=' + repr(checks) + '; '
               'print(json.dumps([dict(arm=x["arm"],path=x["path"],exists=Path(x["path"]).is_file(),'
               '**(dict(sha256=hashlib.sha256(Path(x["path"]).read_bytes()).hexdigest(),bytes=Path(x["path"]).stat().st_size) '
               'if Path(x["path"]).is_file() else {})) for x in checks]))')
    actual = json.loads(f.remote(shlex.quote(f.H + '/venv/bin/python') + ' -B -c ' + shlex.quote(program)))
    require(actual == checks, 'Server resume bytes changed after root review; do not submit')


def build_plan(args, state, jobs, *, root=ROOT):
    require(args.suite in SUITES and args.stage in ('acceptance', 'train'), 'Only Object/Goal acceptance/train')
    require(args.budget in (256, 128, 64) and args.seed in (17, 23, 41), 'Unregistered pair')
    require(args.wall_seconds == 12600, 'Keep the registered engineering wall limit')
    require(state.get('pending_submission') is None, 'Unresolved submission')
    runtime = runtime_contract(root, args.runtime_registration)
    inventory_path = local_path(root, args.source_inventory)
    require(inventory_path == (root / SOURCE_INVENTORY).resolve() and f.sha(inventory_path) == SOURCE_INVENTORY_SHA,
            'Only the original frozen source inventory is allowed')
    inventory = f.read(inventory_path)
    require(len(inventory['files']) == 173, 'Frozen source file count differs')
    for rel, digest in inventory['files'].items():
        require(f.sha(root / rel) == digest, 'Frozen source changed: ' + rel)
    source = inventory['source_root_server']
    require(source == f.P + '/snapshots/formal_main_v2_run_564be0995e', 'Unexpected source root')
    reg = f.read(root / f'configs/experiments/{ROUND}.json')
    suite = reg['suites'][args.suite]
    pair = next(p for p in reg['pairs'] if (p['suite'], p['visual_tokens'], p['seed']) ==
                (args.suite, args.budget, args.seed))
    key = f'{args.suite}_{args.stage}' + (f'_k{args.budget}_seed{args.seed}' if args.stage == 'train' else '')
    prior = [j for j in jobs if j.get('stage_key') == key]
    require(not any(j['status'] in ACTIVE for j in prior), 'This pair/stage already has an active job')
    failed = [j for j in prior if j['status'] != 'COMPLETED' or j.get('exit_code') != '0:0']
    require(not failed or args.repair_record, 'Failed stage requires a retained root repair record')
    if args.repair_record:
        repair = f.read(local_path(root, args.repair_record))
        expected = dict(status='reviewed', stage_key=key, target_source_sha256=inventory['source_sha256'],
                        segment_end=args.segment if args.stage == 'train' else None,
                        runtime_compatibility=runtime)
        require(failed and all(repair.get(k) == v for k, v in expected.items()) and
                set(repair.get('failed_job_ids', [])) == {j['job_id'] for j in failed},
                'Repair must bind all failed jobs, stage, source, segment, and runtime')
    watched = {}

    def watch(rel, server=None):
        path = local_path(root, rel)
        watched[server or f.P + '/' + path.relative_to(root).as_posix()] = f.sha(path)

    common = ['--protocol', f.P + '/' + suite['protocol'], '--windows', f.P + '/' + suite['windows'],
              '--checkpoint', suite['model_root_server'], '--asset-manifest', source + '/' + suite['model_manifest'],
              '--data-directory', suite['data_root_server'], '--cache-directory', f.P + '/.local/formal-hf-' + args.suite,
              '--feature-cache', suite['cache_root_server']]
    for path in (suite['protocol'], suite['windows']):
        watch(path)
    watch(suite['model_manifest'], source + '/' + suite['model_manifest'])
    resume_checks = []
    if args.stage == 'acceptance':
        require(not args.resume, 'Acceptance cannot resume training')
        require(not any(j['status'] == 'COMPLETED' and j.get('exit_code') == '0:0' for j in prior),
                'Acceptance already completed; inspect instead of duplicating')
        output = f.P + f'/results/{ROUND}/{args.suite}/acceptance/attempt{len(prior)+1:02d}'
        configs = [f'configs/experiments/{ROUND}/{args.suite}_k{k}_seed17.json' for k in (128, 256, 64)]
        for path in configs:
            watch(path, source + '/' + path)
        argv = ['--suite', args.suite, '--configs', *[source + '/' + x for x in configs], *common,
                '--oft-source', f.P + '/external/openvla-oft', '--project-root', f.P, '--output', output]
        entry = 'scripts/verify_formal_acceptance.py'
        preflight = 'test ! -e ' + shlex.quote(output)
    else:
        require(args.segment in range(500, 5001, 500), 'Only next registered500-update boundary')
        gates_rel = f'results/{ROUND}/{args.suite}/acceptance/root_review.json'
        gates = f.read(root / gates_rel)
        require(gates.get('status') == 'passed', 'Own suite GPU acceptance must pass root review')
        require(gates.get('runtime_compatibility') == runtime, 'Acceptance runtime differs or missing')
        runtime_review = gates.get('runtime_compatibility_review', {})
        require(runtime_review.get('status') == 'verified' and
                runtime_review.get('runtime_compatibility') == runtime and
                runtime_review.get('loader_restored') is True and runtime_review.get('source_inputs_unchanged') is True,
                'Own suite adapter runtime evidence has not been root-verified')
        accepted = next((j for j in jobs if j['job_id'] == str(gates['job_id'])), None)
        require(accepted and accepted['status'] == 'COMPLETED' and accepted.get('exit_code') == '0:0'
                and accepted.get('runtime_compatibility') == runtime, 'Acceptance job not verified')
        gate_base = gates['output_relative']
        for filename in ('input_acceptance.json', f'f01_k{args.budget}.json', 'resume_acceptance.json',
                         'f03_calls.jsonl', 'acceptance_complete.json'):
            rel = gate_base + '/' + filename
            watch(rel)
            require(f.sha(root / rel) == gates['files'][filename], 'Acceptance evidence changed')
        outrel = f'results/{ROUND}/{args.suite}/k{args.budget}/seed{args.seed}/training'
        output = f.P + '/' + outrel
        require(not (root / outrel / 'training_summary.json').exists(), 'Pair already complete')
        if prior:
            require(args.resume, 'Started pair must fully resume')
            latest = max(prior, key=lambda j: j['submitted_utc'])
            review = f.read(root / outrel / 'segment_reviews' / (latest['job_id'] + '.json'))
            resume_checks = validate_pair_resume(root, pair, outrel, latest, review, runtime, args.segment)
        else:
            require(not args.resume and args.segment == 500, 'Fresh pair starts at0 and stops first at500')
            require(not (root / outrel).exists(), 'Unregistered output exists; inspect first')
        watch(pair['path'], source + '/' + pair['path'])
        argv = ['--config', source + '/' + pair['path'], *common, '--training-checkpoints', pair['checkpoint_root_server'],
                '--input-acceptance-report', f.P + '/' + gate_base + '/input_acceptance.json',
                '--acceptance-report', f.P + '/' + gate_base + f'/f01_k{args.budget}.json', '--output', output,
                '--arm', 'both', '--stop-after-updates', str(args.segment), '--max-wall-seconds', str(args.wall_seconds)]
        if args.resume:
            argv.append('--resume')
        entry = 'scripts/run_formal_future.py'
        preflight = 'test ! -e ' + shlex.quote(output + '/training_summary.json')
        if not prior:
            preflight += ' && test ! -e ' + shlex.quote(pair['checkpoint_root_server']) + ' && test ! -e ' + shlex.quote(output)
    invocation = dict(schema=ROUND, stage=args.stage, stage_key=key, suite=args.suite,
                      source_root=source, source_sha256=inventory['source_sha256'], entrypoint=entry, argv=argv,
                      watched_files=watched, registered_utc=datetime.now(timezone.utc).isoformat(),
                      registration_sha256=f.sha(root / f'configs/experiments/{ROUND}.json'),
                      segment_end=args.segment if args.stage == 'train' else None,
                      repair_record=str(args.repair_record) if args.repair_record else None,
                      runtime_compatibility=runtime)
    invrel = f'results/{ROUND}/invocations/{key}_attempt{len(prior)+1:02d}.json'
    require(not (root / invrel).exists(), 'Invocation already exists; investigate unknown outcome')
    return dict(invocation=invocation, invocation_relative=invrel, output=output,
                remote_preflight=preflight, prior_job_ids=[j['job_id'] for j in prior],
                server_resume_checks=resume_checks)


def verify_remote_inputs(invocation):
    expected = dict(invocation['watched_files'])
    expected.update({f.P + '/' + rel: digest for rel, digest in invocation['runtime_compatibility']['files'].items()})
    expected[f.P + '/' + SOURCE_INVENTORY] = SOURCE_INVENTORY_SHA
    program = ('from pathlib import Path; import hashlib,json; expected=' + repr(expected) + '; '
               'print(json.dumps({p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in expected}))')
    actual = json.loads(f.remote(shlex.quote(f.H + '/venv/bin/python') + ' -B -c ' + shlex.quote(program)))
    require(actual == expected, 'Remote source/evidence/runtime bytes differ; sync and verify before submission')


def submit(args, state, jobs):
    capacity(state, jobs)
    plan = build_plan(args, state, jobs)
    invocation = plan['invocation']
    verify_remote_inputs(invocation)
    if args.stage == 'train' and plan['prior_job_ids']:
        f.verify_remote_training_progress(plan['output'][len(f.P)+1:],
                                         [j for j in jobs if j['job_id'] in plan['prior_job_ids']])
        verify_remote_resumes(plan['server_resume_checks'])
    f.remote('mkdir -p ' + shlex.quote(f.P + f'/results/{ROUND}/invocations') + ' && ' + plan['remote_preflight'])
    invpath = ROOT / plan['invocation_relative']
    f.write(invpath, invocation)
    subprocess.run(['scp', '-q', str(invpath), 'tongji-cvpr:' + f.P + '/' + plan['invocation_relative']], check=True)
    invsha = f.sha(invpath)
    now = invocation['registered_utc']
    state['pending_submission'] = dict(stage_key=invocation['stage_key'], invocation=plan['invocation_relative'],
                                      invocation_sha256=invsha, utc=now)
    f.write(f.STATE, state)
    export = 'ALL,SOURCE_ROOT=' + invocation['source_root'] + ',INVOCATION=' + f.P + '/' + plan['invocation_relative'] + ',INVOCATION_SHA256=' + invsha
    command = 'cd ' + shlex.quote(f.P) + ' && sbatch --parsable --export=' + shlex.quote(export) + ' ' + shlex.quote(f.P + '/' + invocation['runtime_compatibility']['slurm'])
    result = subprocess.run(f.SSH + [command], capture_output=True, text=True)
    jobid = result.stdout.strip().split(';')[0]
    require(result.returncode == 0 and jobid.isdigit(), 'Submission outcome unresolved; retain pending receipt: ' + result.stdout + result.stderr)
    job = dict(job_id=jobid, name='cti-formal', experiment=ROUND, mode=args.stage,
               stage_key=invocation['stage_key'], suite=args.suite, visual_tokens=args.budget if args.stage == 'train' else None,
               training_seed=args.seed if args.stage == 'train' else None, segment_end=invocation['segment_end'],
               status='SUBMITTED', gpus=1, source_root=invocation['source_root'], source_sha256=invocation['source_sha256'],
               run_root=plan['output'], invocation=plan['invocation_relative'], invocation_sha256=invsha,
               runtime_compatibility=invocation['runtime_compatibility'], submitted_utc=now,
               purpose='Registered Object/Goal original acceptance/train with audited metadata projection; final states sealed')
    state['registered_jobs'].append(job)
    state['pending_submission'] = None
    state['stage'] = ROUND + '_' + args.stage
    state['current_round_cost']['registered_jobs'] += 1
    f.write(f.STATE, state)
    f.write(ROOT / f'results/{ROUND}/submissions/{jobid}.json', job)
    print(json.dumps(job, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('plan', 'submit'))
    p.add_argument('--stage', choices=('acceptance', 'train'), required=True)
    p.add_argument('--suite', choices=SUITES, required=True)
    p.add_argument('--source-inventory', type=Path, default=Path(SOURCE_INVENTORY))
    p.add_argument('--runtime-registration', type=Path, required=True)
    p.add_argument('--budget', type=int, default=128)
    p.add_argument('--seed', type=int, default=17)
    p.add_argument('--segment', type=int, default=500)
    p.add_argument('--wall-seconds', type=int, default=12600)
    p.add_argument('--resume', action='store_true')
    p.add_argument('--repair-record', type=Path)
    args = p.parse_args()
    with f.supervisor_lock():
        state = f.read(f.STATE)
        if args.command == 'plan':
            jobs = [j for j in state['registered_jobs'] if j.get('experiment') == ROUND]
            print(json.dumps(build_plan(args, state, jobs), ensure_ascii=False, indent=2))
        else:
            jobs = f.refresh(state)
            submit(args, state, jobs)


if __name__ == '__main__':
    main()

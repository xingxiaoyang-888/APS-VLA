"""Root-only Goal submission with separately registered component-path evidence.

The existing metadata runtime and frozen scientific argv remain intact. This
outer dispatcher adds the Goal official50000 component mapping to the job
identity and selects its explicit wrapper. It never edits the model directory.
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
sys.path.insert(0, str(ROOT / 'scripts' / 'ops'))
import formal_asset_supervisor as base

f, require = base.f, base.require
ROUND = base.ROUND
BASE_REG = 'configs/experiments/formal_main_v2_asset_execution_v1.json'
BASE_REG_SHA = '4356a807b4a1e2084b8de13c939f6588721be05e21b370932d388561188bc1d6'
BASE_TOOL = 'scripts/ops/formal_asset_supervisor.py'
BASE_TOOL_SHA = '442b6e42f4b80979541b0526dd4ae53546567cb9c0884a37dc8356bad094d26a'
TOOL = 'scripts/ops/formal_goal_asset_supervisor.py'
COMPONENT_KEYS = dict(schema=ROUND, kind='goal_component_filename_compatibility',
    version='formal-goal-components-v1', suite='libero_goal',
    wrapper='scripts/server/run_formal_goal_asset_stage.py',
    adapter='scripts/ops/formal_goal_component_adapter.py',
    slurm='scripts/server/formal_goal_asset_main.slurm',
    registration='configs/experiments/formal_main_v2_goal_component_compat_v1.json')
REVIEW_HELPER = 'scripts/ops/formal_goal_component_review.py'


def component_contract(root, args):
    path = base.local_path(root, args.component_execution_registration)
    registration = f.read(path)
    require(registration.get('schema') == ROUND and
            registration.get('kind') == 'goal_component_execution_registration' and
            registration.get('status') == 'reviewed', 'Goal execution registration must be reviewed')
    require(base.local_path(root, args.runtime_registration) == (root / BASE_REG).resolve()
            and f.sha(root / BASE_REG) == BASE_REG_SHA
            and f.sha(root / BASE_TOOL) == BASE_TOOL_SHA,
            'Existing metadata execution registration/tool changed')
    require(registration.get('metadata_execution_registration') == BASE_REG and
            registration.get('metadata_execution_registration_sha256') == BASE_REG_SHA and
            registration.get('source_inventory_sha256') == base.SOURCE_INVENTORY_SHA,
            'Goal execution registration must bind original metadata/source identities')
    contract = registration.get('component_compatibility', {})
    require(set(contract) == set(COMPONENT_KEYS) | {'files'} and
            all(contract.get(k) == v for k, v in COMPONENT_KEYS.items()),
            'Unexpected Goal component contract')
    files = contract['files']
    require(isinstance(files, dict) and set(files) == {
        COMPONENT_KEYS[k] for k in ('wrapper', 'adapter', 'slurm', 'registration')},
        'Goal component runtime requires exactly four registered files')
    for rel, digest in files.items():
        require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest)
                and f.sha(base.local_path(root, rel)) == digest, 'Goal runtime file changed: ' + rel)
    require(registration.get('root_submission_tool') == TOOL and
            registration.get('root_submission_tool_sha256') == f.sha(root / TOOL),
            'Goal submitter identity differs from its registration')
    reviews = registration.get('review_inputs', {})
    require(isinstance(reviews, dict) and reviews, 'Goal CPU/root review inputs required')
    for rel, digest in reviews.items():
        require(f.sha(base.local_path(root, rel)) == digest, 'Goal review input changed: ' + rel)
    return contract


def verify_component_review(root, review, job, contract):
    require(job.get('component_compatibility') == contract and
            review.get('component_compatibility') == contract,
            'Own Goal job/root review lacks matching component identity')
    evidence = review.get('component_compatibility_review', {})
    require(evidence.get('status') == 'verified' and
            evidence.get('component_compatibility') == contract and
            evidence.get('job_id') == job['job_id'] and
            evidence.get('helper_sha256') == f.sha(root / REVIEW_HELPER),
            'Own Goal component evidence has not been root-verified')
    hashes = evidence.get('evidence_sha256', {})
    require(isinstance(hashes, dict) and hashes, 'Goal component evidence SHA map missing')
    for rel, digest in hashes.items():
        require(f.sha(base.local_path(root, rel)) == digest, 'Goal component evidence changed: ' + rel)


def build_plan(args, state, jobs, *, root=ROOT):
    require(args.suite == 'libero_goal', 'Component mapping is registered for Goal only')
    contract = component_contract(root, args)
    # The old builder enforces own-suite GPU acceptance, unchanged frozen173,
    # exact scientific argv, all failed attempts, and next500/resume identities.
    plan = base.build_plan(args, state, jobs, root=root)
    if args.repair_record:
        repair = f.read(base.local_path(root, args.repair_record))
        require(repair.get('component_compatibility') == contract,
                'Repair record must bind the explicit Goal component runtime')
        require(repair.get('component_execution_registration_sha256') ==
                f.sha(base.local_path(root, args.component_execution_registration)),
                'Repair record does not bind reviewed component execution registration')
    if args.stage == 'train':
        review = f.read(root / f'results/{ROUND}/libero_goal/acceptance/root_review.json')
        accepted = next(j for j in jobs if j['job_id'] == str(review['job_id']))
        verify_component_review(root, review, accepted, contract)
        if plan['prior_job_ids']:
            prior = [j for j in jobs if j['job_id'] in plan['prior_job_ids']]
            latest = max(prior, key=lambda j: j['submitted_utc'])
            outrel = plan['output'][len(f.P) + 1:]
            pair_review = f.read(root / outrel / 'segment_reviews' / (latest['job_id'] + '.json'))
            verify_component_review(root, pair_review, latest, contract)
    plan['invocation']['component_compatibility'] = contract
    return plan


def verify_remote_components(invocation):
    expected = {f.P + '/' + rel: digest for rel, digest in
                invocation['component_compatibility']['files'].items()}
    program = ('from pathlib import Path; import hashlib,json; expected=' + repr(expected) + '; '
               'print(json.dumps({p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in expected}))')
    actual = json.loads(f.remote(shlex.quote(f.H + '/venv/bin/python') + ' -B -c ' + shlex.quote(program)))
    require(actual == expected, 'Remote Goal runtime differs; sync exact bytes before submission')


def submit(args, state, jobs):
    base.capacity(state, jobs)
    plan = build_plan(args, state, jobs)
    invocation = plan['invocation']
    base.verify_remote_inputs(invocation)
    verify_remote_components(invocation)
    if args.stage == 'train' and plan['prior_job_ids']:
        f.verify_remote_training_progress(plan['output'][len(f.P) + 1:],
                                         [j for j in jobs if j['job_id'] in plan['prior_job_ids']])
        base.verify_remote_resumes(plan['server_resume_checks'])
    f.remote('mkdir -p ' + shlex.quote(f.P + f'/results/{ROUND}/invocations') + ' && ' + plan['remote_preflight'])
    invpath = ROOT / plan['invocation_relative']
    f.write(invpath, invocation)
    subprocess.run(['scp', '-q', str(invpath), 'tongji-cvpr:' + f.P + '/' + plan['invocation_relative']], check=True)
    invsha = f.sha(invpath)
    now = invocation['registered_utc']
    state['pending_submission'] = dict(stage_key=invocation['stage_key'], invocation=plan['invocation_relative'],
                                      invocation_sha256=invsha, utc=now)
    f.write(f.STATE, state)
    export = ('ALL,SOURCE_ROOT=' + invocation['source_root'] + ',INVOCATION=' + f.P + '/' +
              plan['invocation_relative'] + ',INVOCATION_SHA256=' + invsha)
    command = ('cd ' + shlex.quote(f.P) + ' && sbatch --parsable --export=' + shlex.quote(export) +
               ' ' + shlex.quote(f.P + '/' + invocation['component_compatibility']['slurm']))
    result = subprocess.run(f.SSH + [command], capture_output=True, text=True)
    jobid = result.stdout.strip().split(';')[0]
    require(result.returncode == 0 and jobid.isdigit(),
            'Submission outcome unresolved; retain pending receipt: ' + result.stdout + result.stderr)
    job = dict(job_id=jobid, name='cti-formal', experiment=ROUND, mode=args.stage,
        stage_key=invocation['stage_key'], suite=args.suite, visual_tokens=args.budget if args.stage == 'train' else None,
        training_seed=args.seed if args.stage == 'train' else None, segment_end=invocation['segment_end'],
        status='SUBMITTED', gpus=1, source_root=invocation['source_root'], source_sha256=invocation['source_sha256'],
        run_root=plan['output'], invocation=plan['invocation_relative'], invocation_sha256=invsha,
        runtime_compatibility=invocation['runtime_compatibility'],
        component_compatibility=invocation['component_compatibility'], submitted_utc=now,
        purpose='Registered Goal stage with official50000 component paths and metadata evidence; final states sealed')
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
    p.add_argument('--suite', choices=('libero_goal',), default='libero_goal')
    p.add_argument('--source-inventory', type=Path, default=Path(base.SOURCE_INVENTORY))
    p.add_argument('--runtime-registration', type=Path, default=Path(BASE_REG))
    p.add_argument('--component-execution-registration', type=Path, required=True)
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

"""Explicit, bounded evidence for three CUDA failures before train_formal_arm.

This candidate never reads state, weights or final states and never submits.
The failed allocation remains FAILED. Its immutable byte bundle can be checked
after a later successful allocation has advanced mutable progress files.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[2]
P = '/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA'
H = '/share/home/u15016/XXY_CVPR/CTI-VLA'
S = P + '/snapshots/formal_main_v2_run_564be0995e'
SCHEMA = 'formal_main_v2'
VERSION = 'cuda-startup-failure-0840-v1'
SOURCE = 'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
SOURCE_PIN = '5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
SOURCE_SHA = 'dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e'
SERVER = 'results/formal_main_v2/preflight/cuda_startup_server_paths_0840.json'
SERVER_PIN = '5e5afef2f7bc9e52db23df3f7cd5c7e3e7923c0b5bcd839eaddd84964f6617a4'
ERROR = 'requested CUDA device is unavailable: cuda:0'
OBJECT_PULL = 'results/formal_main_v2/pulls/20261018T124922Z_99c13ac6c07f/receipt.json'
SPATIAL_PULL = 'results/formal_main_v2/pulls/20261018T125523Z_f18157f47643/receipt.json'
CASES = {
    '3028460': dict(suite='libero_object', budget=256, seed=23, target=500, completed=0, seconds=84,
        invocation='results/formal_main_v2/invocations/libero_object_train_k256_seed23_attempt01.json',
        invocation_sha256='4c68f05d52ffc0573efd491a1af9ccab72b2607adb1da30e65e4021cffc983c8',
        pull=OBJECT_PULL, pull_sha256='27527b98900c438cfbe16a606588b2e2f0fa5df2e5fb1c4f966a804985f0c173'),
    '3028468': dict(suite='libero_object', budget=64, seed=23, target=500, completed=0, seconds=69,
        invocation='results/formal_main_v2/invocations/libero_object_train_k64_seed23_attempt01.json',
        invocation_sha256='4336178af16be4c04b1eb91f0f7309ed8dc1e18c11920fba7163c376ca454637',
        pull=OBJECT_PULL, pull_sha256='27527b98900c438cfbe16a606588b2e2f0fa5df2e5fb1c4f966a804985f0c173'),
    '3028522': dict(suite='libero_spatial', budget=64, seed=23, target=1500, completed=1000, seconds=73,
        invocation='results/formal_main_v2/invocations/libero_spatial_train_k64_seed23_attempt03.json',
        invocation_sha256='669ba5bc67ca38ea4030b4496dc7a82a388c33c572bcb12c18591d143f263c3a',
        pull=SPATIAL_PULL, pull_sha256='8b6eead4c767b66f3fefbf0763c92e86855528cfa1aa16945cf5d8b7af3fc6d1'),
}
PREVIOUS = 'results/formal_main_v2/libero_spatial/k64/seed23/training/segment_reviews/3025205.json'
PREVIOUS_PIN = '2416c7802db8ab947971ddaaedbb771c8ab9c2edacc8fd52e2f778ba66802876'
PREVIOUS_PULL = 'results/formal_main_v2/pulls/20261018T124450Z_c90f04fa06aa/receipt.json'
PREVIOUS_PULL_PIN = '9ad5cf6849d06ff75fcfae0c85d0be1acf99b17b031fd1cb04c47aa5faafc5c5'
FORBIDDEN = {'.pt', '.pth', '.bin', '.safetensors', '.ckpt', '.pkl', '.pickle', '.init', '.pruned_init'}


def require(value, message):
    if not value:
        raise ValueError('Startup failure evidence: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_relative(value):
    require(isinstance(value, str) and '\\' not in value and ':' not in value, 'nonrelative path')
    p = PurePosixPath(value)
    require(not p.is_absolute() and p.as_posix() == value and '..' not in p.parts, 'path traversal')
    require(not {x.lower() for x in p.suffixes} & FORBIDDEN, 'weights forbidden')
    require(not any(x.lower() in {'weights', 'checkpoints', 'test', 'sealed'} or 'sealed' in x.lower() for x in p.parts), 'forbidden directory')
    if p.suffix not in {'.py', '.pyc', '.pyo'}:
        require(not any(t in value.lower() for t in ('init_state', 'initial_state', 'final_state', 'test_state')), 'state values forbidden')
    require(value != 'results/experiment_supervisor/state.json', 'mutable state is not an audit input')
    return value


def local_server(path):
    base = S if str(path).startswith(S + '/') else P
    require(str(path).startswith(base + '/'), 'foreign server evidence path')
    return safe_relative(str(path)[len(base) + 1:])


def proof_relative(job):
    c = CASES.get(str(job['job_id']))
    require(c is not None, 'unknown failure requires a separate explicit review')
    return f"results/{SCHEMA}/{c['suite']}/k{c['budget']}/seed{c['seed']}/training/startup_failure_reviews/{job['job_id']}.json"


class Reader:
    def __init__(self, root, bundle=None):
        self.root, self.bundle, self.raws = Path(root).resolve(), bundle, {}

    def raw(self, name, expected=None):
        name = safe_relative(name)
        rel = name if self.bundle is None else self.bundle[name]['path']
        path = self.root / safe_relative(rel)
        require(path.resolve() == path.absolute() and self.root in path.parents, 'symlink or foreign path')
        data = path.read_bytes()
        if self.bundle is not None:
            row = self.bundle[name]
            require(set(row) == {'path', 'sha256', 'bytes'} and len(data) == row['bytes'] and sha(data) == row['sha256'], 'archived evidence changed')
        require(expected is None or sha(data) == expected, 'SHA mismatch: ' + name)
        require(name not in self.raws or self.raws[name] == data, 'evidence changed during review')
        self.raws[name] = data
        return data

    def read(self, name, expected=None):
        return json.loads(self.raw(name, expected))


def check_pull(reader, relative, pin):
    pull = reader.read(relative, pin)
    require(pull['schema'] == SCHEMA and pull['status'] == 'verified_nonweight_snapshot' and pull['final_evidence'] is True, 'incomplete pull')
    require(not pull['missing'] and not pull['skipped'] and pull['weights_copied'] is False and pull['sealed_initial_states_copied'] is False, 'unsafe/incomplete pull')
    folder = str(PurePosixPath(relative).parent)
    before = reader.raw(folder + '/inventory_before.json', pull['inventory_sha256'])
    require(before == reader.raw(folder + '/inventory_after.json'), 'pull inventory was unstable')
    inventory = json.loads(before)
    require(inventory['missing'] == pull['missing'] and inventory['excluded'] == pull['excluded'], 'inventory exclusions differ')
    require(len({x['relative'] for x in pull['files']}) == len(pull['files']), 'duplicate pull file')
    originals = {x['relative']: x for x in inventory['files']}
    require(set(originals) == {x['relative'] for x in pull['files']}, 'pull files omitted')
    for row in pull['files']:
        rel = row['relative']; old = originals[rel]
        require(all(row[k] == v for k, v in old.items()) and row['path'] == P + '/' + rel, 'pull row differs')
        require(row['action'] in {'downloaded_verified', 'same_sha_skipped'}, 'unfinished pull action')
        require(len(reader.raw(rel, row['sha256'])) == row['bytes'], 'pull file length differs')
    for item in pull['selected_jobs']:
        require(item['include_run_root'] is True and not item['active_overlapping_job_ids'], 'active/incomplete pair pull')
    for x in pull['excluded']:
        job = next(j for j in pull['selected_jobs'] if j['job_id'] == x['job_id'])
        require(x['path'] == job['run_root'] + '/.training.lock' and x['reason'] == 'unregistered_nonweight_extension', 'unexpected excluded evidence')
    return pull


def reconstruct(reader, job_id):
    job_id = str(job_id); require(job_id in CASES, 'unregistered failure')
    c = CASES[job_id]
    source = reader.read(SOURCE, SOURCE_PIN)
    require(source['source_root_server'] == S and source['source_sha256'] == SOURCE_SHA and len(source['files']) == 173, 'frozen inventory differs')
    for rel, checksum in source['files'].items():
        reader.raw(rel, checksum)
    registration = reader.read('configs/experiments/formal_main_v2.json')
    pair = next(x for x in registration['pairs'] if (x['suite'], x['visual_tokens'], x['seed']) == (c['suite'], c['budget'], c['seed']))
    runrel = f"results/{SCHEMA}/{c['suite']}/k{c['budget']}/seed{c['seed']}/training"
    checkpoint = H + f"/checkpoints/{SCHEMA}/{c['suite']}/k{c['budget']}/seed{c['seed']}"
    require(pair['checkpoint_root_server'] == checkpoint and pair['run_root_server'] + '/training' == P + '/' + runrel, 'pair paths differ')
    config = reader.read(pair['path'], pair['sha256'])
    require((config['schema'], config['suite'], config['seed'], config['tokens_per_camera']) == (SCHEMA, c['suite'], c['seed'], c['budget'] // 2), 'pair configuration differs')
    invocation = reader.read(c['invocation'], c['invocation_sha256'])
    require(invocation['source_root'] == S and invocation['source_sha256'] == SOURCE_SHA and invocation['entrypoint'] == 'scripts/run_formal_future.py', 'invocation source differs')
    require(invocation['segment_end'] == c['target'] and invocation['stage'] == 'train' and invocation['suite'] == c['suite'], 'invocation target differs')
    argv = invocation['argv']; resumed = argv[-1] == '--resume'
    values = argv[:-1] if resumed else argv
    require(len(values) % 2 == 0 and len(set(values[::2])) == len(values[::2]), 'malformed arguments')
    args = dict(zip(values[::2], values[1::2]))
    require(resumed == (c['completed'] > 0) and args['--stop-after-updates'] == str(c['target']) and args['--arm'] == 'both' and args['--max-wall-seconds'] == '12600', 'registered invocation was changed')
    require(args['--training-checkpoints'] == checkpoint and args['--output'] == P + '/' + runrel and args['--config'] == S + '/' + pair['path'], 'cross-pair invocation')
    require(invocation['registration_sha256'] == sha(reader.raw('configs/experiments/formal_main_v2.json')), 'registration SHA changed')
    for path, checksum in invocation['watched_files'].items():
        reader.raw(local_server(path), checksum)
    pull = check_pull(reader, c['pull'], c['pull_sha256'])
    selected = next(x for x in pull['selected_jobs'] if x['job_id'] == job_id)
    require(selected['stage_key'] == invocation['stage_key'] and selected['run_root'] == P + '/' + runrel, 'selected pair differs')
    account = pull['accounting_after']['jobs'][job_id]
    require(account == pull['accounting_before']['jobs'][job_id] and account['status'] == 'FAILED' and account['exit_code'] == '1:0' and account['node'] == 'gpu4020' and account['elapsed_seconds'] == c['seconds'], 'failed accounting differs')
    require(dict(x.split('=', 1) for x in account['allocation'].split(','))['gres/gpu'] == '1', 'GPU allocation changed')
    receipt_rel = f'results/{SCHEMA}/job_receipts/{job_id}.json'
    receipt = reader.read(receipt_rel)
    require(receipt['job_id'] == job_id and receipt['exit_code'] == 1 and receipt['invocation_sha256'] == c['invocation_sha256'] and receipt['source_sha256'] == SOURCE_SHA and receipt['stage_key'] == invocation['stage_key'], 'receipt identity/exit differs')
    require(0 < receipt['wall_seconds'] <= c['seconds'], 'allocation omitted wall cost')
    rows = [x for x in pull['files'] if x['relative'].startswith(runrel + '/')]
    failures = [x for x in rows if x['relative'].startswith(runrel + '/failures/' + job_id + '_')]
    require(len(failures) == 1, 'exactly one retained failure required')
    failure = reader.read(failures[0]['relative'])
    require(failure['status'] == 'failed' and failure['error_type'] == 'RuntimeError' and failure['error'] == ERROR and 0 < failure['seconds'] <= receipt['wall_seconds'], 'different failure cannot reuse this repair')
    stderr = reader.raw(f'results/slurm/cti-formal_{job_id}.err').decode('utf-8')
    require('openvla_oft_loader.py", line 191, in load_openvla_oft_components' in stderr and 'run_formal_future.py", line 132, in run' in stderr and stderr.count('RuntimeError: ' + ERROR) == 1 and f'srun: error: gpu4020: task 0: Exited with exit code 1' in stderr, 'failure traceback differs')
    require(reader.raw(f'results/slurm/cti-formal_{job_id}.out') == b'', 'unexpected training stdout')
    runtime = invocation.get('runtime_compatibility')
    runtime_result = None
    if c['suite'] == 'libero_object':
        require(runtime and len(runtime['files']) == 6 and receipt['runtime_compatibility'] == runtime, 'missing Object runtime identity')
        for rel, checksum in runtime['files'].items(): reader.raw(rel, checksum)
        identity_rel = runrel + '/compatibility/' + job_id + '/identity.json'
        events_rel = runrel + '/compatibility/' + job_id + '/compatibility_events.jsonl'
        identity = reader.read(identity_rel); raw = reader.raw(events_rel)
        require(raw.endswith(b'\n'), 'unclosed compatibility journal')
        events = [json.loads(line) for line in raw.splitlines()]
        names = ['stage_start', 'asset_metadata_compat_enter', 'stage_runner_start', 'asset_metadata_compat_load_start', 'asset_metadata_compat_load_complete', 'stage_runner_exception', 'asset_metadata_compat_exit', 'stage_end']
        require([x['event'] for x in events] == names and [x['seq'] for x in events] == list(range(8)), 'incomplete failed compatibility sequence')
        for item in [identity, *events]:
            for key, value in dict(job_id=job_id, suite=c['suite'], stage='train', stage_key=invocation['stage_key'], source_root=S, source_sha256=SOURCE_SHA, invocation_sha256=c['invocation_sha256']).items():
                require(item.get(key) == value, 'compatibility envelope differs')
        require(events[0]['argv'] == events[2]['argv'] == argv and events[2]['identity_sha256'] == sha(reader.raw(identity_rel)), 'runner identity differs')
        require(identity['runtime_compatibility'] == runtime and identity['identity']['verified_frozen_file_count'] == 173, 'wrong implementation identity')
        for path, checksum in identity['identity']['watched_files'].items(): reader.raw(local_server(path), checksum)
        require(events[1]['identity'] == identity['identity'], 'entered another metadata scope')
        require(events[3]['call_id'] == events[4]['call_id'] == 0 and events[3]['view'] == identity['identity']['views']['libero_object'], 'wrong metadata load')
        require(events[5]['error'] == ERROR and events[5]['error_type'] == 'RuntimeError' and events[5]['runner_exit_code'] == 1 and events[5]['runner_termination'] == 'exception', 'exception erased')
        exit_row = events[6]
        for key in ('binding_intact', 'directory_verifier_code_unchanged', 'directory_verifier_unchanged', 'frozen_source_and_inputs_unchanged', 'original_loader_code_unchanged', 'original_loader_restored', 'runner_raised'):
            require(exit_row.get(key) is True, 'failed scope not restored: ' + key)
        require((exit_row['adapted_calls_attempted'], exit_row['adapted_calls_completed'], exit_row['passthrough_calls']) == (1, 1, 0), 'unexpected metadata call count')
        for obj in (receipt, events[-1]):
            require(obj['status'] == 'failed' and obj['exit_code'] == obj['runner_exit_code'] == 1 and obj['runner_termination'] == 'exception' and obj['loader_restored'] is True and obj['source_inputs_unchanged'] is True, 'failure/restoration flags differ')
        artifacts = receipt['compatibility_artifacts']
        require(len(artifacts) == 2, 'missing compatibility copies')
        for artifact, rel in zip(sorted(artifacts, key=lambda x: x['path']), sorted([identity_rel, events_rel])):
            require(artifact['path'] == P + '/' + rel and artifact['sha256'] == sha(reader.raw(rel)) and artifact['bytes'] == len(reader.raw(rel)), 'artifact copy SHA differs')
            require(artifact['source'] == P + f'/results/{SCHEMA}/compatibility_invocations/{job_id}/' + PurePosixPath(rel).name, 'global artifact source differs')
        require({x['relative'] for x in rows} == {identity_rel, events_rel, failures[0]['relative']}, 'Object already has training evidence')
        runtime_result = dict(runtime_compatibility=runtime, failed_journal_events=8, metadata_manifest_loads=1, model_load_completed=False, loader_restored=True, source_inputs_unchanged=True)
    else:
        require(runtime is None and 'runtime_compatibility' not in receipt, 'Spatial cannot inherit Object adapter')
    server = reader.read(SERVER, SERVER_PIN)
    require(server['exit_code'] == 0 and server['stderr'] == '' and json.loads(server['stdout']) == server['result'], 'server proof failed')
    require(server['helper']['sha256'] == sha(reader.raw(server['helper']['path'])), 'server probe source changed')
    actual = next(x for x in server['result']['pairs'] if x['job_id'] == job_id)
    require(actual['checkpoint_root'] == checkpoint and actual['run_root'] == P + '/' + runrel and actual['run_root_exists'] is True, 'server pair differs')
    expected_files = {PurePosixPath(x['relative']).relative_to(runrel).as_posix(): x['bytes'] for x in rows}
    expected_files['.training.lock'] = 0
    require({x['relative']: x['bytes'] for x in actual['run_root_files']} == expected_files, 'server output differs from stable pull')
    checks, previous = [], None
    if c['completed'] == 0:
        require(actual['zero_start'] is True and actual['checkpoint_root_exists'] is False and actual['checkpoint_root_files'] == [], 'zero-start repair found checkpoint evidence')
        checks = [dict(arm=a, path=checkpoint + '/' + a + '/resume.pt', exists=False) for a in ('A', 'B')]
        pair_cost = c['seconds']
    else:
        previous = reader.read(PREVIOUS, PREVIOUS_PIN)
        old_pull = check_pull(reader, PREVIOUS_PULL, PREVIOUS_PULL_PIN)
        require(previous['status'] == 'passed' and previous['completed_by_arm'] == {'A': 1000, 'B': 1000} and previous['allowed_next_segment_end'] == 1500, 'previous real boundary differs')
        old_files = {x['relative']: (x['sha256'], x['bytes']) for x in old_pull['files']}
        new_files = {x['relative']: (x['sha256'], x['bytes']) for x in pull['files']}
        require(all(new_files.get(k) == v for k, v in old_files.items()), 'startup failure changed existing training bytes')
        require(set(new_files) - set(old_files) == {failures[0]['relative'], receipt_rel, f'results/slurm/cti-formal_{job_id}.out', f'results/slurm/cti-formal_{job_id}.err'}, 'new arm/cache/validation evidence after startup failure')
        require(actual['zero_start'] is False and actual['checkpoint_root_exists'] is True, 'existing-resume pair vanished')
        for old in previous['server_resume_checks']:
            found = next(x for x in server['result']['resume_checks'] if x['path'] == old['path'])
            require(found['sha256'] == old['sha256'] and found['bytes'] == old['bytes'] and found['stable_during_hash'] is True, 'actual resume changed after failure')
            checks.append(dict(arm=old['arm'], path=old['path'], exists=True, sha256=found['sha256'], bytes=found['bytes']))
        for arm in ('A', 'B'):
            progress = reader.read(runrel + '/' + arm + '/progress_report.json')
            require(progress['training_updates_completed'] == 1000 and progress['next_sample_cursor'] == 8000 and progress['resume_sha256'] == next(x['sha256'] for x in checks if x['arm'] == arm), 'existing progress is not the committed1000 boundary')
        pair_cost = sum(pull['accounting_after']['jobs'][x]['elapsed_seconds'] for x in ('3024716', '3025205', job_id))
        require(pair_cost == previous['pair_allocated_gpu_seconds'] + c['seconds'] == 8557, 'failed allocation cost omitted')
    static = [x['relative'] for x in pull['files'] if x['kind'] in ('job_receipt', 'slurm_log') and x['job_ids'] == [job_id]]
    static += [failures[0]['relative']]
    if runtime_result: static += [identity_rel, events_rel]
    return dict(schema=SCHEMA, kind='startup_failure_review', version=VERSION, status='verified_startup_failure',
        job_id=job_id, suite=c['suite'], visual_tokens=c['budget'], seed=c['seed'], stage_key=invocation['stage_key'],
        source_sha256=SOURCE_SHA, invocation_sha256=c['invocation_sha256'], failed_status='FAILED', failed_exit_code='1:0',
        output_relative=runrel, failure=ERROR, failure_phase='before_VLA_from_pretrained_and_train_formal_arm',
        completed_by_arm={a:c['completed'] for a in ('A','B')}, next_sample_cursor={a:c['completed']*8 for a in ('A','B')},
        requested_segment_end=c['target'], allowed_next_segment_end=c['target'], explicit_resume_required=True,
        current_allocation_new_updates=0, current_allocation_arm_initializations=0,
        server_resume_checks=checks, previous_boundary_review=None if previous is None else dict(path=PREVIOUS, sha256=PREVIOUS_PIN),
        pair_allocated_gpu_seconds=pair_cost, failed_allocation_gpu_seconds=c['seconds'],
        retained_failure_files=sorted(static), runtime_failure_evidence=runtime_result,
        node='gpu4020', node_hardware_failure_proven=False, ordinary_segment_completed=False,
        scientific_settings_changed=False, weights_opened=False, final_states_opened=False)


def create_candidate(root, job_id, bundle_root):
    """Copy explicit nonweight inputs to a new immutable candidate bundle."""
    root = Path(root).resolve(); bundle_root = safe_relative(bundle_root)
    out = root / bundle_root
    require(not out.exists(), 'bundle must be new; never overwrite evidence')
    reader = Reader(root)
    facts = reconstruct(reader, job_id)
    self_rel = Path(__file__).resolve().relative_to(root).as_posix()
    reader.raw(self_rel)
    require(all((root / rel).read_bytes() == raw for rel, raw in reader.raws.items()), 'evidence changed before archive')
    out.mkdir(parents=True)
    mapping = {}
    for rel, raw in reader.raws.items():
        copied = bundle_root + '/inputs/' + rel
        target = root / copied; target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle: handle.write(raw)
        mapping[rel] = dict(path=copied, sha256=sha(raw), bytes=len(raw))
    proof = dict(**facts, evidence_bundle=dict(sorted(mapping.items())),
        reviewer=dict(path=self_rel, sha256=sha(reader.raws[self_rel])),
        root_recovery_authorization='pending_separate_root_registration_and_CPU_review')
    path = out / 'review.json'
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        handle.write(json.dumps(proof, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    return proof, path


def require_saved(evidence, *, job, saved=None):
    """Rebuild a failure proof without treating mutable later progress as old."""
    root = Path(getattr(evidence, 'root', getattr(evidence, 'project', ROOT))).resolve()
    ref = proof_relative(job)
    canonical = evidence.read(ref)
    require(saved is None or saved == canonical, 'saved failure history differs from canonical immutable review')
    saved = canonical
    require(saved.get('status') == 'verified_startup_failure' and saved.get('kind') == 'startup_failure_review' and saved.get('version') == VERSION, 'ordinary or missing failure proof')
    require(saved['reviewer']['sha256'] == sha(Path(__file__).read_bytes()), 'failure verifier changed')
    for row in saved['evidence_bundle'].values():
        require(evidence.watch(row['path']) == row['sha256'], 'failure bundle no longer immutable')
    reader = Reader(root, saved['evidence_bundle'])
    facts = reconstruct(reader, job['job_id'])
    require(all(saved.get(k) == v for k, v in facts.items()), 'failure proof conclusions cannot be changed')
    require(set(saved['evidence_bundle']) == set(reader.raws) | {saved['reviewer']['path']}, 'unexpected or missing archived input')
    c = CASES[str(job['job_id'])]
    for key, expected in dict(experiment=SCHEMA, mode='train', suite=c['suite'], training_seed=c['seed'], visual_tokens=c['budget'],
        stage_key=f"{c['suite']}_train_k{c['budget']}_seed{c['seed']}", source_root=S, source_sha256=SOURCE_SHA,
        invocation=c['invocation'], invocation_sha256=c['invocation_sha256'], status='FAILED', exit_code='1:0',
        segment_end=c['target'], gpus=1, elapsed_seconds=c['seconds'], run_root=P+'/'+facts['output_relative']).items():
        require(job.get(key) == expected, 'registered failed job differs: ' + key)
    if facts['runtime_failure_evidence'] is not None:
        require(job.get('runtime_compatibility') == facts['runtime_failure_evidence']['runtime_compatibility'], 'registered failed runtime differs')
    else:
        require('runtime_compatibility' not in job and 'component_compatibility' not in job, 'legacy failed job acquired compatibility fields')
    for rel in facts['retained_failure_files']:
        require(evidence.watch(rel) == saved['evidence_bundle'][rel]['sha256'], 'original failed artifact changed')
    return saved


def successful_and_failed_ids(jobs, failure_history):
    failures = {k for k, j in jobs.items() if j.get('status') != 'COMPLETED' or j.get('exit_code') != '0:0'}
    require(set(failure_history) == failures, 'failed history omitted or invented')
    return set(jobs) - failures, failures

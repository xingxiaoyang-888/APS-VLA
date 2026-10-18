"""Synthetic CPU only: no remote command/process, no real state read or write."""
import importlib.util
import json
from pathlib import Path
import shlex
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('node_exclusion_candidate', HERE / 'adapter.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def save(root, rel, value):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return m.sha(p.read_bytes())


def make(tmp_path, profile='formal'):
    root = tmp_path / 'synthetic_project'
    for rel in ['scripts/formal_supervisor.py', *[v[0] for v in m.WRAPPERS.values()]]:
        out = root / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes((PROJECT / rel).read_bytes())
    f = SimpleNamespace(ROOT=root, P=m.P, H=m.H, SSH=list(m.SSH),
                        __file__=str(root / 'scripts/formal_supervisor.py'),
                        STATE=root / 'results/experiment_supervisor/state.json')
    failure = 'results/formal_main_v2/preflight/synthetic_failure.json'
    failuresha = save(root, failure, {'synthetic': True, 'kind': 'CPU_fixture_not_real_failure_receipt'})
    reg = dict(schema='formal_main_v2', kind='scheduler_node_exclusion_registration', version=m.VERSION,
               status='reviewed_for_future_explicit_requests', server_project=m.P, source_root=m.S,
               source_sha256=m.SOURCE_SHA, excluded_nodes=['gpu4020'], automatic_retry=False,
               existing_jobs_untouched=True, scope='future_explicit_training_and_action_gpu_v2_only',
               adapter_sha256=m.sha((HERE / 'adapter.py').read_bytes()),
               registered_wrapper_sha256={v[0]: v[1] for v in m.WRAPPERS.values()},
               failure_evidence_sha256={failure: failuresha}, synthetic=True)
    regpath = 'results/formal_main_v2/preflight/synthetic_registration.json'
    regref = dict(path=regpath, sha256=save(root, regpath, reg))
    wrapper_rel, wrappersha = m.WRAPPERS[profile]
    if profile == 'gpu_v2':
        request = {'kind': 'action_execution_gpu_v2'}
        stage = m.GPU_STAGE
        invrel = f'results/formal_main_v2/invocations/{stage}_attempt01.json'
        inv = dict(schema='formal_main_v2', kind='bounded_action_execution_engineering_invocation',
                   stage='engineering', stage_key=stage, source_root=m.S, source_sha256=m.SOURCE_SHA,
                   output_root=m.P + '/' + m.GPU_BASE, wrapper_sha256=wrappersha)
        invsha = save(root, invrel, inv)
        export = 'ALL,INVOCATION=' + m.P + '/' + invrel + ',INVOCATION_SHA256=' + invsha + ',WRAPPER_SHA256=' + wrappersha
        pending = dict(stage_key=stage, invocation=invrel, invocation_sha256=invsha,
                       status='prepared_before_invocation_publication')
    else:
        suite = {'formal': 'libero_spatial', 'object': 'libero_object', 'goal': 'libero_goal'}[profile]
        request = dict(kind='training', suite=suite, budget=64, seed=17, segment_end=1500, resume=True)
        stage = f'{suite}_train_k64_seed17'
        invrel = f'results/formal_main_v2/invocations/{stage}_attempt03.json'
        inv = dict(schema='formal_main_v2', stage='train', stage_key=stage, suite=suite,
                   source_root=m.S, source_sha256=m.SOURCE_SHA, entrypoint='scripts/run_formal_future.py',
                   registration_sha256=m.REGISTRATION_SHA, registered_utc='synthetic_utc', segment_end=1500,
                   argv=['--config', m.S + f'/configs/experiments/formal_main_v2/{suite}_k64_seed17.json',
                         '--arm', 'both', '--stop-after-updates', '1500', '--resume'])
        if profile != 'formal':
            inv['component_compatibility' if profile == 'goal' else 'runtime_compatibility'] = dict(slurm=wrapper_rel, files={wrapper_rel: wrappersha})
        invsha = save(root, invrel, inv)
        export = 'ALL,SOURCE_ROOT=' + m.S + ',INVOCATION=' + m.P + '/' + invrel
        pending = dict(stage_key=stage, invocation=invrel, utc='synthetic_utc')
        if profile != 'formal':
            export += ',INVOCATION_SHA256=' + invsha
            pending['invocation_sha256'] = invsha
    state = dict(pending_submission=pending, registered_jobs=[])
    save(root, 'results/experiment_supervisor/state.json', state)
    command = 'cd ' + shlex.quote(m.P) + ' && sbatch --parsable --export=' + shlex.quote(export) + ' ' + shlex.quote((m.S if profile == 'formal' else m.P) + '/' + wrapper_rel)
    return SimpleNamespace(root=root, f=f, request=request, reg=reg, ref=regref, inv=inv,
                           invrel=invrel, pending=pending, command=command, profile=profile,
                           audit='.local/fixture/prepared_argv.json')


def scope(x):
    return m.exclude_future_sbatch(x.f, request=x.request, registration_ref=x.ref, audit_relative=x.audit)


@pytest.mark.parametrize('profile', ['formal', 'object', 'goal', 'gpu_v2'])
def test_actual_command_shape_and_original_bindings_restored(tmp_path, profile):
    x = make(tmp_path, profile)
    before = x.f.STATE.read_bytes()
    original = x.f.SSH
    with scope(x):
        for query in ['sacct -n -X -P -j 1 --format=JobIDRaw,State',
                      "test ! -e '/project/path' && printf 'absent\\n'",
                      m.H + '/venv/bin/python -B -']:
            assert x.f.SSH + [query] == original + [query]
        actual = x.f.SSH + [x.command]
        assert actual == original + [x.command.replace('sbatch --parsable ', 'sbatch --parsable --exclude=gpu4020 ', 1)]
        event = json.loads((x.root / x.audit).read_bytes())
        assert event['original_ssh_argv'] == original + [x.command]
        assert event['actual_ssh_argv'] == actual
        assert event['status'] == 'argv_prepared_not_submission_result'
        assert not event['subprocess_executed_by_adapter']
        assert 'results/experiment_supervisor/state.json' not in event['metadata_evidence_sha256']
        with pytest.raises(ValueError, match='one sbatch'):
            x.f.SSH + [x.command]
    assert x.f.SSH is original and x.f.STATE.read_bytes() == before


@pytest.mark.parametrize('mutation', [
    lambda c: c.replace(m.P, '/share/foreign-project', 1),
    lambda c: c + ' && echo extra',
    lambda c: c + '; echo extra',
    lambda c: 'true && ' + c,
    lambda c: c.replace('sbatch ', 'sbatch --exclude=gpu4020 '),
    lambda c: c.replace('sbatch ', 'sbatch --exclude=gpu4021 '),
    lambda c: c.replace('sbatch ', '/usr/bin/sbatch '),
    lambda c: c.replace('sbatch ', "sba''tch "),
    lambda c: c.replace('sbatch ', 'sba\\tch '),
    lambda c: c.replace(' --export=', ' --partition=A800 --export='),
    lambda c: c.replace('ALL,', 'ALL,CUDA_VISIBLE_DEVICES=0,'),
    lambda c: c.replace(' --export=', '\n --export='),
    lambda c: c.replace('formal_main.slurm', 'foreign.slurm'),
])
def test_noncanonical_or_foreign_submission_is_not_returned(tmp_path, mutation):
    x = make(tmp_path)
    with scope(x):
        with pytest.raises(ValueError):
            x.f.SSH + [mutation(x.command)]
    assert not (x.root / x.audit).exists()


@pytest.mark.parametrize('damage', ['pending_path', 'pending_stage', 'source', 'segment', 'seed', 'resume', 'wrapper'])
def test_prepared_identity_damage(tmp_path, damage):
    x = make(tmp_path)
    if damage.startswith('pending'):
        x.pending['invocation' if damage == 'pending_path' else 'stage_key'] = 'foreign'
        save(x.root, 'results/experiment_supervisor/state.json', {'pending_submission': x.pending})
    elif damage == 'wrapper':
        (x.root / m.WRAPPERS['formal'][0]).write_bytes(b'changed wrapper')
    else:
        if damage == 'source': x.inv['source_sha256'] = 'f' * 64
        elif damage == 'segment': x.inv['segment_end'] = 2000
        elif damage == 'seed': x.inv['argv'][1] = x.inv['argv'][1].replace('seed17', 'seed23')
        elif damage == 'resume': x.inv['argv'].remove('--resume')
        save(x.root, x.invrel, x.inv)
    with scope(x):
        with pytest.raises(ValueError):
            x.f.SSH + [x.command]
    assert not (x.root / x.audit).exists()


def test_pending_sha_export_and_draft_registration(tmp_path):
    x = make(tmp_path, 'gpu_v2')
    x.pending['invocation_sha256'] = 'f' * 64
    save(x.root, 'results/experiment_supervisor/state.json', {'pending_submission': x.pending})
    with scope(x):
        with pytest.raises(ValueError, match='pending invocation SHA'):
            x.f.SSH + [x.command]
    x.reg['status'] = 'draft_pending_root_review'
    x.ref['sha256'] = save(x.root, x.ref['path'], x.reg)
    with pytest.raises(ValueError, match='not root-registered'):
        with scope(x):
            raise AssertionError('draft entered')


def test_scope_preserves_exception_and_rejects_nested_use(tmp_path):
    x = make(tmp_path)
    original = x.f.SSH
    with pytest.raises(RuntimeError, match='synthetic subprocess error'):
        with scope(x):
            with pytest.raises(ValueError, match='nested scope'):
                with scope(x): pass
            x.f.SSH + [x.command]
            raise RuntimeError('synthetic subprocess error')
    assert x.f.SSH is original
    with pytest.raises(ValueError, match='audit already exists'):
        with scope(x): pass


def test_no_submit_when_caller_returns_for_full_capacity(tmp_path):
    x = make(tmp_path)
    original = x.f.SSH
    with scope(x):
        assert x.f.SSH + ['sacct -n -j 1'] == original + ['sacct -n -j 1']
    assert x.f.SSH is original and not (x.root / x.audit).exists()


@pytest.mark.parametrize('path', ['../other.json', 'results/sealed/value.json', 'results/test/a.json',
                                  'results/initial_states_test.json', '/foreign.json'])
def test_forbidden_metadata_path_before_read(tmp_path, path):
    with pytest.raises(ValueError):
        m.metadata_path(tmp_path.resolve(), path)

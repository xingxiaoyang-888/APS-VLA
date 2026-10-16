"""Root planning must not weaken duplicate, resource, or frozen-input gates."""
from argparse import Namespace
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('asset_supervisor_test', ROOT / 'scripts/ops/formal_asset_supervisor.py')
ops = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ops)


def args(**changes):
    result = dict(stage='acceptance', suite='libero_object', budget=128, seed=17,
                  wall_seconds=12600, segment=500, resume=False, repair_record=None,
                  runtime_registration='unused_by_isolated_builder', source_inventory=Path(ops.SOURCE_INVENTORY))
    result.update(changes)
    return Namespace(**result)


def gpu_job(index, status='RUNNING', gpus=1):
    return dict(job_id=str(index), mode='train', status=status, gpus=gpus,
                stage_key=f'other_{index}', exit_code='0:0')


def test_pending_gpu_slots_are_counted():
    jobs = [gpu_job(i, 'PENDING', 0) for i in range(8)]
    with pytest.raises(ValueError, match='eight'):
        ops.capacity({'pending_submission': None}, jobs)


def test_submitted_gpu_slots_are_counted():
    with pytest.raises(ValueError, match='eight'):
        ops.capacity({}, [gpu_job(i, 'SUBMITTED') for i in range(8)])


def test_completed_and_cpu_jobs_do_not_block_free_slot():
    jobs = [gpu_job(i) for i in range(7)] + [gpu_job(8, 'COMPLETED')]
    jobs.append(dict(job_id='9', mode='shared_fs_probe', status='RUNNING', gpus=0))
    assert len(ops.capacity({}, jobs)) == 7


def test_unknown_submission_is_never_retried():
    with pytest.raises(ValueError, match='Unresolved'):
        ops.capacity({'pending_submission': {'invocation': 'some.json'}}, [])


@pytest.fixture
def isolated_builder(monkeypatch):
    runtime = dict(ops.RUNTIME_KEYS, files=dict(ops.PINNED_FILES))
    # This fixture isolates the immutable argv and operational gate builder;
    # runtime_contract itself is tested separately below, without this mock.
    monkeypatch.setattr(ops, 'runtime_contract', lambda root, path: runtime)
    real_exists = Path.exists
    invocation_dir = ROOT / 'results/formal_main_v2/invocations'
    # These plans do not write anything; mask only existing invocation names
    # to test the earlier guards independently of this checkout's job history.
    monkeypatch.setattr(Path, 'exists', lambda path: False if path.parent == invocation_dir and
                        path.name.startswith('libero_object_acceptance_attempt') else real_exists(path))
    return runtime


def test_original_manifest_and_original_entry_argv_are_retained(isolated_builder):
    plan = ops.build_plan(args(), {}, [])
    invocation = plan['invocation']
    assert invocation['entrypoint'] == 'scripts/verify_formal_acceptance.py'
    assert invocation['argv'][invocation['argv'].index('--asset-manifest') + 1] == (
        ops.f.P + '/snapshots/formal_main_v2_run_564be0995e/configs/assets/openvla_oft_libero_object.json')
    assert invocation['runtime_compatibility'] == isolated_builder
    assert len(invocation['watched_files']) == 6
    assert 'final' not in invocation['argv']


@pytest.mark.parametrize('status', ['RUNNING', 'PENDING', 'SUBMITTED', 'COMPLETING'])
def test_duplicate_stage_refused(isolated_builder, status):
    job = dict(gpu_job(1, status), stage_key='libero_object_acceptance')
    with pytest.raises(ValueError, match='already has an active'):
        ops.build_plan(args(), {}, [job])


def test_accepted_suite_is_not_repeated(isolated_builder):
    job = dict(gpu_job(1, 'COMPLETED'), stage_key='libero_object_acceptance')
    with pytest.raises(ValueError, match='already completed'):
        ops.build_plan(args(), {}, [job])


def test_failed_stage_requires_exact_repair(isolated_builder, tmp_path):
    job = dict(gpu_job(1, 'FAILED'), stage_key='libero_object_acceptance', exit_code='1:0')
    with pytest.raises(ValueError, match='repair record'):
        ops.build_plan(args(), {}, [job])
    repair = tmp_path / 'repair.json'
    data = dict(status='reviewed', stage_key=job['stage_key'],
                target_source_sha256=ops.f.read(ROOT / ops.SOURCE_INVENTORY)['source_sha256'],
                segment_end=None, runtime_compatibility=isolated_builder, failed_job_ids=['wrong'])
    repair.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError, match='all failed jobs'):
        ops.build_plan(args(repair_record=repair), {}, [job])
    data['failed_job_ids'] = ['1']
    repair.write_text(json.dumps(data), encoding='utf-8')
    plan = ops.build_plan(args(repair_record=repair), {}, [job])
    assert plan['invocation_relative'].endswith('attempt02.json')
    assert plan['output'].endswith('acceptance/attempt02')


@pytest.mark.parametrize('changes', [dict(stage='final'), dict(suite='libero_10'),
                                      dict(budget=32), dict(seed=99), dict(wall_seconds=1)])
def test_scope_cannot_expand(isolated_builder, changes):
    with pytest.raises(ValueError):
        ops.build_plan(args(**changes), {}, [])


def test_runtime_contract_requires_preregistered_exact_six_files(tmp_path):
    runtime = dict(ops.RUNTIME_KEYS, files=dict(ops.PINNED_FILES))
    reg = dict(schema=ops.ROUND, kind='asset_execution_registration', status='reviewed',
               runtime_compatibility=runtime, source_inventory_sha256=ops.SOURCE_INVENTORY_SHA)
    p = tmp_path / 'registration.json'
    p.write_text(json.dumps(reg), encoding='utf-8')
    with pytest.raises(ValueError, match='exactly six'):
        ops.runtime_contract(ROOT, p)


def test_runtime_contract_does_not_allow_adapter_replacement(tmp_path):
    runtime = dict(ops.RUNTIME_KEYS, files=dict(ops.PINNED_FILES))
    runtime['files'][ops.RUNTIME_KEYS['wrapper']] = '0' * 64
    runtime['files'][ops.RUNTIME_KEYS['slurm']] = '0' * 64
    runtime['files'][ops.RUNTIME_KEYS['adapter']] = '0' * 64
    reg = dict(schema=ops.ROUND, kind='asset_execution_registration', status='reviewed',
               runtime_compatibility=runtime, source_inventory_sha256=ops.SOURCE_INVENTORY_SHA)
    p = tmp_path / 'registration.json'
    p.write_text(json.dumps(reg), encoding='utf-8')
    with pytest.raises(ValueError, match='Audited adapter'):
        ops.runtime_contract(ROOT, p)


def test_remote_verification_binds_all_runtime_files(monkeypatch):
    runtime = dict(ops.RUNTIME_KEYS, files=dict(ops.PINNED_FILES))
    invocation = dict(watched_files={'/immutable/input': 'a' * 64}, runtime_compatibility=runtime)
    captured = []
    monkeypatch.setattr(ops.f, 'remote', lambda command: captured.append(command) or '{}')
    with pytest.raises(ValueError, match='Remote source/evidence/runtime'):
        ops.verify_remote_inputs(invocation)
    for path in runtime['files']:
        assert path in captured[0]
    assert ops.SOURCE_INVENTORY in captured[0]

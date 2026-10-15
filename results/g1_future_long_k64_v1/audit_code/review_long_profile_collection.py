"""Independent non-GPU read audit of actual Long raw timing panel artifacts."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'src'))
from cti_vla.evaluation.teacher_diagnostics import json_signature
from cti_vla.data.long_initial_states import load_long_development_panel
from cti_vla.data.identity import file_sha256

directory = root / 'results/g1_future_long_k64_v1/profile_panel'
registration_path = root / 'configs/experiments/g1_future_long_k64_v1.json'
read = lambda path: json.loads(Path(path).read_text(encoding='utf-8'))
registration = read(registration_path)
config = read(directory / 'config.json')
panel = read(directory / 'panel.json')
report = read(directory / 'collection_report.json')
source_inventory = read(root / 'results/g1_future_long_k64_v1/source_g1_future_long_k64_v1.json')
official_path = root / registration['evaluation']['panel']
official = load_long_development_panel(official_path)
old_path = root / 'results/g1_future_long_v1/closed_loop/trials.jsonl'
assert file_sha256(old_path) == registration['frozen_evidence_sha256'][old_path.relative_to(root).as_posix()]
old_events = [json.loads(line) for line in old_path.read_text(encoding='utf8').splitlines()]
old_dense = {e['state_trial_id']: e for e in old_events if e['event']=='result' and e['method']=='dense'}
assert len(old_dense)==30
events = [json.loads(line) for line in (directory / 'collection_trials.jsonl').read_text(encoding='utf8').splitlines()]
assert Counter(e['event'] for e in events)=={'start':3, 'result':3}
assert all(e['run_signature']==json_signature(config) for e in events)
assert panel['split']=='development' and panel['test_opened'] is False
assert panel['arrays_preprocessed'] is False and panel['source_kind']=='simulator_raw'
assert panel['content_signature']==json_signature({k:v for k,v in panel.items() if k!='content_signature'})
assert panel['registration_signature']==json_signature(registration)
assert config['registration_sha256']==file_sha256(registration_path)
assert config['registration_signature']==json_signature(registration)
assert config['test_opened'] is False and config['new_success_trials'] is False
assert config['collector_sha256']==source_inventory['files']['scripts/collect_long_future_profile_panel.py']
assert all(source_inventory['files'][k]==v for k,v in config['source_files'].items())
assert panel['provenance']=={**config,'checkpoint_unchanged':True}
assert (directory / panel['development_panel']['path']).read_bytes()==official_path.read_bytes()
assert file_sha256(directory / panel['development_panel']['path'])==panel['development_panel']['sha256']
assert config['model_revision']=='95220f9a3421a7ff12d4218e73d09ade830fa9a3'
assert (config['seed'],config['environment_seed'],config['max_steps'],config['wait_steps'],config['action_chunk'])==(17,0,520,10,8)
states = [min((s for s in official['states'] if s['task_id']==task),key=lambda s:s['source_state_index']) for task in (0,3,5)]
assert [s['source_state_index'] for s in states]==[0,3,2]
assert [e['state_trial_id'] for e in panel['episodes']]==[s['trial_id'] for s in states]
keys=('agentview_image','robot0_eye_in_hand_image','robot0_eef_pos','robot0_eef_quat','robot0_gripper_qpos')
array_checks, trajectory_checks = [], []
active=set()
completed={}
for event in events:
    tid=event['trial_id']
    if event['event']=='start':
        assert tid not in active and tid not in completed
        active.add(tid)
    else:
        assert tid in active and event['status']=='completed'
        active.remove(tid)
        completed[tid]=event
assert not active
assert set(completed)=={s['trial_id'] for s in states}
for state,row in zip(states,panel['episodes']):
    tid=state['trial_id']
    path=directory / row['receipt']['path']
    assert file_sha256(path)==row['receipt']['sha256']
    receipt=read(path)
    result=completed[tid]
    assert all(receipt.get(k)==v for k,v in result.items() if k not in ('event','trial_id','run_signature'))
    assert receipt['state_trial_id']==tid
    assert all(receipt[k]==state[k] for k in ('task_id','task_name','initial_state_sha256','source_state_index'))
    assert receipt['provenance']==panel['provenance']
    original=old_dense[tid]
    requested=[int((original['control_steps']-1)*fraction//8)*8 for fraction in (0,.5,.9)]
    assert requested==registration['profiling']['task_control_steps'][str(state['task_id'])]==receipt['requested_control_steps']
    assert [c['control_step'] for c in receipt['chunks']]==list(range(0,receipt['control_steps'],8))
    assert receipt['policy_calls']==len(receipt['chunks'])
    assert receipt['chunks'][0]['observation_sha256']==original['chunks'][0]['observation_sha256']
    assert receipt['missing']==[]
    assert [r['control_step'] for r in receipt['observations']]==requested
    original_chunks={c['control_step']:c for c in original['chunks']}
    collected_chunks={c['control_step']:c for c in receipt['chunks']}
    common=sorted(set(original_chunks)&set(collected_chunks))
    trajectory_checks.append({'task_id':state['task_id'],'state_trial_id':tid,
        'source_state_index':state['source_state_index'],'requested_steps':requested,
        'original_control_steps':original['control_steps'],'collected_control_steps':receipt['control_steps'],
        'original_success':original['success'],'collected_success_not_added_to_success_denominator':receipt['success'],
        'comparable_policy_queries':len(common),
        'matching_observation_hashes':sum(original_chunks[s]['observation_sha256']==collected_chunks[s]['observation_sha256'] for s in common),
        'matching_normalized_action_chunks':sum(original_chunks[s]['normalized_actions']==collected_chunks[s]['normalized_actions'] for s in common),
        'matching_environment_action_chunks':sum(original_chunks[s]['environment_actions']==collected_chunks[s]['environment_actions'] for s in common)})
    for observation in receipt['observations']:
        array_path=path.parent / observation['arrays']['path']
        assert array_path.resolve().is_relative_to(directory.resolve())
        assert file_sha256(array_path)==observation['arrays']['sha256']
        with np.load(array_path,allow_pickle=False) as archive:
            assert set(archive.files)==set(keys)
            arrays={key:archive[key] for key in keys}
        digest=hashlib.sha256()
        for key in keys:
            value=np.ascontiguousarray(arrays[key])
            assert np.isfinite(value).all()
            if key.endswith('image'):
                assert value.shape==(256,256,3) and value.dtype==np.uint8
            digest.update(key.encode()+str(value.dtype).encode()+str(value.shape).encode()+value.tobytes())
        step=observation['control_step']
        assert step==8*observation['query_index']
        assert digest.hexdigest()==observation['raw_observation_sha256']==collected_chunks[step]['observation_sha256']
        assert observation['observation_id']==f'{tid}:control_step_{step}'
        array_checks.append({'task_id':state['task_id'],'control_step':step,
            'path':array_path.relative_to(root).as_posix(),'npz_sha256':file_sha256(array_path),
            'raw_observation_sha256':digest.hexdigest(),
            'matches_original_dense_same_step':digest.hexdigest()==original_chunks[step]['observation_sha256']})
assert len(array_checks)==9 and len({r['npz_sha256'] for r in array_checks})==9
assert report['status']=='completed' and report['checkpoint_unchanged'] is True
assert report['test_opened'] is False and report['observations']==9 and report['panel']['missing']==[]
assert report['policy_calls']==sum(r['policy_calls'] for r in completed.values())==95
assert report['cost_scope']=='Three dense trajectory replays for raw observations; excluded from success counts and per-call timing, charged in GPU cost'
accounting=read(root / 'results/g1_future_long_k64_v1/slurm_accounting.json')
job=[j for j in accounting['jobs'] if str(j['job_id'])=='3001540']
assert len(job)==1
job=job[0]
assert job['state']=='COMPLETED' and job['exit_code']=='0:0' and job['allocated_gpus']==1 and job['scope']=='collect'
assert job['elapsed_seconds']==359
assert report['execution_wall_seconds_including_model_loading']<=job['elapsed_seconds']
output={'status':'passed','reviewed_utc':datetime.now(timezone.utc).isoformat(),
    'reviewer':'profile_long independent raw collection audit','review_script_sha256':file_sha256(__file__),
    'gpu_calls_for_this_review':0,'weights_loaded_for_this_review':False,
    'source_snapshot_commit':'192daa57','registration_sha256':file_sha256(registration_path),
    'panel_sha256':file_sha256(directory / 'panel.json'),
    'collection_journal_sha256':file_sha256(directory / 'collection_trials.jsonl'),
    'collection_report_sha256':file_sha256(directory / 'collection_report.json'),
    'original_dense_journal_sha256':file_sha256(old_path),
    'raw_observations':9,'registered_initial_states':3,'unique_arrays':9,
    'all_array_file_and_raw_hashes_verified':True,'all_first_observations_match_original_dense':True,
    'fixed_original_reference_step_selection':True,'replaced_or_padded_observations':0,'missing_observations':[],
    'test_opened':False,'collection_replays_added_to_success_count':0,
    'collection_policy_calls':95,'collection_cost':{'job':job,'GPU_seconds':359,'L40_GPU_hours':359/3600},
    'trajectory_comparisons':trajectory_checks,'arrays':array_checks,
    'interpretation':'Three original development trajectories replayed only to capture registered raw observations. Collection runtime is charged cost, never the O2A benchmark or extra independent success evidence.'}
target=directory / 'independent_review.json'
target.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':output['status'],'raw_observations':9,'policy_calls':95,
    'step_hash_matches':sum(r['matches_original_dense_same_step'] for r in array_checks),
    'trajectory_queries_matched':[r['matching_observation_hashes'] for r in trajectory_checks],
    'output':str(target)},ensure_ascii=False))

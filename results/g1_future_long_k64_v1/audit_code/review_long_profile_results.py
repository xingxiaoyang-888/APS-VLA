"""Independent read-only audit of actual Long O2A outputs; never starts a job.

Writes a review only after all timing and paired-loop artifacts are present.
Statistics are recomputed from the durable journal, not the saved summary.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / 'results/g1_future_long_k64_v1'
DIRECTORY = ROUND / 'profiling'
sys.path.insert(0, str(ROOT / 'src'))
from cti_vla.evaluation.teacher_diagnostics import json_signature


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def local_reference(remote):
    text = remote.replace('\\', '/')
    prefix = '/CTI-VLA/'
    if prefix not in text:
        raise AssertionError('reference is outside project: ' + text)
    relative = text.split(prefix, 1)[1]
    candidate = (ROOT / relative).resolve()
    assert ROOT.resolve() in candidate.parents
    if candidate.is_file():
        return candidate
    aliases = {
        'snapshots/g1_future_long_k64_v1/source_manifest.json':
            'results/g1_future_long_k64_v1/source_g1_future_long_k64_v1.json',
        'results/g1_future_long_k64_v1/references/parent_source_inventory.json':
            'results/g1_future_long/source_g1_future_long_v1.json',
        'results/g1_future_long_k64_v1/references/multiseed_source_inventory.json':
            'results/g1_future_long_multiseed_v1/source_g1_future_long_multiseed_v1.json'}
    if relative in aliases:
        return ROOT / aliases[relative]
    raise FileNotFoundError(candidate)


def percentile(values, probability):
    values = sorted(values)
    rank = (len(values) - 1) * probability
    lower, upper = math.floor(rank), math.ceil(rank)
    return values[lower] + (rank - lower) * (values[upper] - values[lower])


def stats(values):
    return {'count':len(values), 'mean':math.fsum(values)/len(values),
        'median':statistics.median(values), 'p95':percentile(values,.95)}


def matches(actual, expected):
    for key, value in expected.items():
        if isinstance(value,float):
            assert math.isclose(actual[key],value,rel_tol=1e-12,abs_tol=1e-9), (key,actual[key],value)
        else:
            assert actual[key]==value, (key,actual[key],value)


def audit():
    required = [DIRECTORY / f for f in ('config.json','measurements.json','summary.json','calls.jsonl')]
    required += [ROUND / f'seed{s}/closed_loop/config.json' for s in (17,23,41)]
    required += [ROUND / f'seed{s}/closed_loop/closed_loop_report.json' for s in (17,23,41)]
    missing=[str(p.relative_to(ROOT)) for p in required if not p.is_file()]
    if missing:
        print(json.dumps({'status':'pending','missing':missing,'review_written':False}))
        return
    registration_path=ROOT / 'configs/experiments/g1_future_long_k64_v1.json'
    registration=read(registration_path)
    methods=read(ROUND / 'profile_methods.json')
    retry=read(ROUND / 'profile_retry1_registration.json')
    inventory_path=ROUND / 'source_g1_future_long_k64_v1.json'
    inventory=read(inventory_path)
    config, measurement, summary=[read(DIRECTORY / name) for name in ('config.json','measurements.json','summary.json')]
    events=[json.loads(line) for line in (DIRECTORY / 'calls.jsonl').read_text(encoding='utf8').splitlines()]
    panel=read(ROUND / 'profile_panel/panel.json')
    panel_review=read(ROUND / 'profile_panel/independent_review.json')
    assert panel_review['status']=='passed' and panel_review['raw_observations']==9
    assert panel_review['panel_sha256']==sha(ROUND / 'profile_panel/panel.json')
    assert config['panel']['panel_sha256']==panel_review['panel_sha256']
    assert config['panel']['observations']==9 and config['panel']['missing']==[]
    assert config['panel']['provenance']==panel['provenance']
    assert config['registration_sha256']==methods['registration_sha256']==sha(registration_path)
    assert config['registration_signature']==json_signature(registration)
    assert config['methods_manifest_sha256']==sha(ROUND / 'profile_methods.json')
    assert retry['unchanged_methods_sha256']==config['methods_manifest_sha256']
    assert retry['unchanged_registration_sha256']==config['registration_sha256']
    assert config['config']==registration['profiling']==measurement['config']
    assert measurement['provenance']==config
    assert config['test_opened'] is False and measurement['synthetic'] is False
    assert measurement['checkpoint_unchanged'] is True
    assert config['all_instances_share_one_loaded_base'] is True
    assert config['uncontended_gpu_attested_and_checked'] is True
    assert config['cache_scope']==measurement['cache_scope']=='none'
    assert config['future_head_deployed'] is measurement['future_head_deployed'] is False
    assert measurement['component_passes']==0
    assert measurement['outlier_filter']=='none; retain all measured calls and failures'
    assert measurement['boundary']=='Raw simulator arrays + instruction ready -> executable CPU action chunk8 ready; batch1, CUDA sync before and after.'
    assert measurement['included']=='camera/proprio/prompt preprocessing, visual encoding, DIE when present, packing, one VLA forward, action D2H/unnormalization/gripper postprocessing'
    for key,digest in config['source_files'].items():
        assert digest==inventory['files'][key]==sha(ROOT / key)
    for key,name in (('config_sha256','config.json'),('measurements_sha256','measurements.json'),('journal_sha256','calls.jsonl')):
        assert summary[key]==sha(DIRECTORY / name)
    expected_names=['dense']+[f'{arm}{budget}_seed{seed}' for budget in (128,64) for seed in (17,23,41) for arm in ('A','B')]
    assert [r['name'] for r in methods['methods']]==registration['profiling']['method_names']==expected_names
    assert set(measurement['methods'])==set(expected_names)
    assert len(config['method_identities'])==12
    assert events[0]['event']=='identity' and events[0]['identity']==config
    assert events[0]['identity_sha256']==json_signature(config)
    assert Counter(e['event'] for e in events)=={'identity':1,'start':2600,'complete':2600}
    calls=[]
    for index in range(2600):
        started,complete=events[1+index*2:3+index*2]
        assert started['event']=='start' and complete['event']=='complete'
        assert started['call_id']==complete['call_id']==index
        assert all(complete[key]==value for key,value in started.items() if key!='event')
        assert complete['instruction_mode']=='uncached' and complete['kind'] in ('warmup','main')
        assert math.isfinite(complete['elapsed_ms']) and complete['elapsed_ms']>0
        assert 'components' not in complete
        calls.append({key:value for key,value in complete.items() if key!='event'})
    assert Counter(c['kind'] for c in calls)=={'warmup':260,'main':2340}
    main=[r for r in calls if r['kind']=='main']
    assert main==measurement['rows'] and measurement['sample_policy_forwards']==2600
    assert measurement['cost']==summary['cost']
    cost=measurement['cost']
    assert cost['sample_policy_forwards_attempted']==cost['api_calls_attempted']==cost['completed']==2600
    assert cost['failed']==cost['unknown_completion']==0
    assert cost['attempts_by_pass']=={'warmup':260,'main':2340,'components':0}
    observation_ids=[]
    episodes={}
    for episode in panel['episodes']:
        receipt=read(ROUND / 'profile_panel' / episode['receipt']['path'])
        for obs in receipt['observations']:
            observation_ids.append(obs['observation_id'])
            episodes[obs['observation_id']]=episode['state_trial_id']
    assert len(observation_ids)==9 and len(set(episodes.values()))==3
    assert measurement['observation_ids']==observation_ids
    assert measurement['observation_episodes']==episodes
    assert measurement['observations']==9 and measurement['episodes']==3
    rng=random.Random(1017)
    base=list(expected_names)
    rng.shuffle(base)
    expected_schedule=[]
    expected_calls=[]
    warmed=set()
    for repeat in range(20):
        offset=repeat % 13
        order=base[offset:]+base[:offset]
        obs=list(observation_ids)
        rng.shuffle(obs)
        expected_schedule.append({'round':repeat,'method_order':order,'observation_order':obs})
        for name in order:
            if name not in warmed:
                expected_calls.extend((name,'warmup',-1,observation_ids[i%9]) for i in range(20))
                warmed.add(name)
            expected_calls.extend((name,'main',repeat,oid) for oid in obs)
    assert measurement['schedule']==expected_schedule
    assert [(r['method'],r['kind'],r['round'],r['observation_id']) for r in calls]==expected_calls
    assert all(r['episode_id']==episodes[r['observation_id']] for r in calls)
    for name in expected_names:
        positions=[sum(b['method_order'][i]==name for b in expected_schedule) for i in range(13)]
        assert max(positions)-min(positions)==1
    allocation=config['allocation']
    assert allocation['other_compute_processes']==0 and len(measurement['blocks'])==260
    telemetry_count=0
    for block,planned in zip(measurement['blocks'],[{'round':b['round'],'method':m,'position':i,
            'method_order':b['method_order'],'observation_order':b['observation_order']}
            for b in expected_schedule for i,m in enumerate(b['method_order'])]):
        assert all(block[key]==value for key,value in planned.items())
        for side in ('telemetry_before','telemetry_after'):
            telemetry=block[side]
            assert telemetry['uncontended_device']==allocation
            assert telemetry['slurm']['SLURM_JOB_ID']=='3001817'
            telemetry_count+=1
    assert measurement['hardware_after']['uncontended_device']==allocation
    assert config['runtime']['gpu']=='NVIDIA L40'
    assert config['hardware']['slurm']['SLURM_JOB_ID']=='3001817'
    assert config['runtime']['slurm_job_id']=='3001817'
    identities=[]
    for spec in methods['methods'][1:]:
        name=spec['name']
        seed,budget,arm=spec['seed'],spec['total_tokens'],name[0]
        identity=config['method_identities'][name]
        selector=identity['selector']
        if budget==128:
            result_root=ROOT / ('results/g1_future_long_v1' if seed==17 else f'results/g1_future_long_multiseed_v1/seed{seed}')
        else:
            result_root=ROUND / f'seed{seed}'
        receipt_path=result_root / f'training/{arm}/deployment_receipt.json'
        receipt=read(receipt_path)
        closed_config=read(result_root / 'closed_loop/config.json')
        closed_report=read(result_root / 'closed_loop/closed_loop_report.json')
        assert closed_report['checkpoint_unchanged'] is True and closed_report['test_opened'] is False
        assert closed_config['selectors'][arm]==selector
        assert selector['selector_checkpoint_sha256']==receipt['checkpoint_sha256']==spec['checkpoint']['sha256']
        assert selector['deployment_receipt_sha256']==json_signature(receipt)
        assert spec['receipt']['sha256']==sha(receipt_path)
        assert receipt['metadata']['seed']==seed and receipt['metadata']['arm']==arm
        assert receipt['pair_config'].get('tokens_per_camera',64)*2==budget
        assert identity['checkpoint_ref']==spec['checkpoint'] and identity['receipt_ref']==spec['receipt']
        assert identity['total_tokens']==budget and identity['training_seed']==seed and identity['arm']==arm
        assert selector['future_head_deployed'] is False
        assert measurement['methods'][name]['provenance']==identity
        for key in ('f01_report','input_acceptance','source_inventory'):
            assert sha(local_reference(spec[key]['path']))==spec[key]['sha256']
        source=identity['snapshot']
        original_inventory=read(local_reference(spec['source_inventory']['path']))
        assert source['source_inventory_sha256']==spec['source_inventory']['sha256']
        assert source['runtime_sha256']==original_inventory['files']['src/cti_vla/evaluation/future_runtime.py']
        assert source['auxiliary_module_sha256']==original_inventory['files']['src/cti_vla/training/future_auxiliary.py']
        for path,digest in source['shared_source_files'].items():
            assert digest==original_inventory['files'][path]==inventory['files'][path]
        for path,digest in source['deployment_source_files'].items():
            assert digest==original_inventory['files'][path]==selector['training_source_files'][path]
        identities.append({'instance':name,'checkpoint_sha256':spec['checkpoint']['sha256'],
            'receipt_sha256':spec['receipt']['sha256'],'closed_loop_config_sha256':sha(result_root / 'closed_loop/config.json'),
            'matches_success_evaluation_selector':True})
    for name,description in measurement['methods'].items():
        assert description['cache_scope']=='none' and description['instruction_cache_enabled'] is False
        assert description['future_head_deployed'] is False and description['batch_size']==1
    primary,per_obs=[],[]
    for name in expected_names:
        values=[r['elapsed_ms'] for r in main if r['method']==name]
        assert len(values)==180
        primary.append({'method':name,**stats(values),'min':min(values),'max':max(values),
            'p99':percentile(values,.99),'largest_three_retained_ms':sorted(values)[-3:]})
        for oid in observation_ids:
            values=[r['elapsed_ms'] for r in main if r['method']==name and r['observation_id']==oid]
            assert len(values)==20
            per_obs.append({'method':name,'observation_id':oid,'episode_id':episodes[oid],**stats(values)})
    saved_primary={r['method']:r for r in summary['primary']}
    assert len(saved_primary)==len(summary['primary'])==13
    for row in primary:
        matches(saved_primary[row['method']],{k:row[k] for k in ('count','mean','median','p95')})
    saved_obs={(r['method'],r['observation_id']):r for r in summary['per_observation']}
    assert len(saved_obs)==len(summary['per_observation'])==117
    for row in per_obs:
        matches(saved_obs[(row['method'],row['observation_id'])],row)
    equal_weight,pooled=[],[]
    for family in ('A128','B128','A64','B64'):
        selected=[r for r in primary if r['method'].startswith(family+'_')]
        row={'method_family':family,'training_seeds':[17,23,41],
            'mean_of_seed_medians_ms':math.fsum(r['median'] for r in selected)/3,
            'mean_of_seed_p95_ms':math.fsum(r['p95'] for r in selected)/3,
            'seed_median_range_ms':[min(r['median'] for r in selected),max(r['median'] for r in selected)]}
        matches(next(r for r in summary['seed_equal_weight_summaries'] if r['method_family']==family),row)
        equal_weight.append(row)
        row={'method_family':family,'training_seeds':[17,23,41],**stats([r['elapsed_ms'] for r in main if r['method'].startswith(family+'_')])}
        matches(next(r for r in summary['pooled_summaries'] if r['method_family']==family),row)
        pooled.append(row)
    timings={(r['method'],r['round'],r['observation_id']):r['elapsed_ms'] for r in main}
    expected_pairs=[(m,'dense') for m in expected_names if m!='dense']
    expected_pairs += [(f'B{b}_seed{s}',f'A{b}_seed{s}') for b in (128,64) for s in (17,23,41)]
    expected_pairs += [(f'B64_seed{s}',f'A128_seed{s}') for s in (17,23,41)]
    saved_pairs={(r['treatment'],r['reference']):r for r in summary['paired_comparisons']}
    assert set(saved_pairs)==set(expected_pairs) and len(summary['paired_comparisons'])==21
    for treatment,reference in expected_pairs:
        x=[timings[(reference,r,o)] for r in range(20) for o in observation_ids]
        y=[timings[(treatment,r,o)] for r in range(20) for o in observation_ids]
        matches(saved_pairs[(treatment,reference)],{'paired_calls':180,
            'speedup_ratio_of_means':math.fsum(x)/math.fsum(y),
            'ratio_of_medians':statistics.median(x)/statistics.median(y),
            'mean_paired_difference_ms':math.fsum(b-a for a,b in zip(x,y))/180})
    accounting=read(ROUND / 'slurm_accounting.json')
    jobs={str(j['job_id']):j for j in accounting['jobs']}
    failed,finished=jobs['3001742'],jobs['3001817']
    assert failed['state']=='FAILED' and failed['exit_code']=='1:0' and failed['elapsed_seconds']==55
    assert finished['state']=='COMPLETED' and finished['exit_code']=='0:0' and finished['allocated_gpus']==1
    assert finished['node']=='gpu4022' and failed['node']=='gpu4020'
    assert measurement['execution_wall_seconds_including_model_loading']<=finished['elapsed_seconds']
    assert retry['failed_attempt_policy_calls']==0 and retry['maximum_policy_calls_across_both_attempts']==2600
    assert summary['retained_all_calls'] is True and summary['test_opened'] is False
    # Detect the known JSON mapping-order sensitivity without editing evidence.
    original_order=[(r['method'],r['observation_id']) for r in summary['per_observation']]
    sorted_mapping_order=[(m,o) for m in expected_names for o in measurement['observation_episodes']]
    review={'status':'passed','reviewed_utc':datetime.now(timezone.utc).isoformat(),
        'reviewer':'profile_long independent actual O2A audit','review_script_sha256':sha(__file__),
        'gpu_calls_for_review':0,'weights_read_for_review':False,'production_source_modified':False,
        'config_sha256':sha(DIRECTORY / 'config.json'),'measurements_sha256':sha(DIRECTORY / 'measurements.json'),
        'journal_sha256':sha(DIRECTORY / 'calls.jsonl'),'summary_sha256':sha(DIRECTORY / 'summary.json'),
        'registration_sha256':sha(registration_path),'method_manifest_sha256':sha(ROUND / 'profile_methods.json'),
        'deployments':13,'raw_observations':9,'warmup_calls':260,'measured_calls':2340,'total_policy_calls':2600,
        'failed_or_unknown_policy_calls':0,'component_calls':0,'dropped_calls':0,
        'schedule_exact_and_position_balanced':True,'raw_observations_shared_across_methods':True,
        'GPU_uuid':allocation['gpu_uuid'],'compute_pid':allocation['own_pid'],
        'uncontended_telemetry_checks':telemetry_count+2,'all_same_GPU_and_no_other_compute_process':True,
        'complete_raw_to_CPU_action_boundary_verified_against_frozen_source':True,
        'cache_scope':'none','future_head_deployed':False,'test_opened':False,
        'all12_checkpoint_identities_equal_closed_loop':True,'checkpoint_identity_checks':identities,
        'independent_primary_statistics':primary,'independent_per_observation_statistics':per_obs,
        'independent_seed_equal_weight_statistics':equal_weight,'independent_pooled_statistics':pooled,
        'all_saved_statistics_match_independent_recalculation':True,
        'json_mapping_order_requires_identity_based_summary_comparison':original_order!=sorted_mapping_order,
        'statistics_comparison_tolerance':{'relative':1e-12,'absolute_ms':1e-9},
        'timing_GPU_cost':{'successful_job':finished,'failed_pre_inference_job':failed,
            'successful_GPU_seconds':finished['elapsed_seconds'],'failed_GPU_seconds':55,
            'both_attempts_GPU_seconds':finished['elapsed_seconds']+55,
            'collection_and_training_costs_reported_separately_not_omitted':True},
        'interpretation':'Nine fixed observations from three development trajectories;20 repeated timings and3training seeds are not independent observations. All spikes retained. This audit validates latency evidence, not success-rate benefit.'}
    target=DIRECTORY / 'independent_review.json'
    target.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':'passed','deployments':13,'observations':9,'total_calls':2600,
        'same_GPU_uncontended':True,'all_checkpoint_identities_match':True,
        'JSON_list_order_only':review['json_mapping_order_requires_identity_based_summary_comparison'],
        'equal_weight_statistics':equal_weight,'cost_GPU_seconds':review['timing_GPU_cost']['both_attempts_GPU_seconds'],
        'output':str(target)},ensure_ascii=False))


if __name__=='__main__':
    audit()

from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, subprocess

root=Path('F:/CTI-VLA')
sha=lambda p:hashlib.sha256((root/p).read_bytes()).hexdigest()
read=lambda p:json.loads((root/p).read_text(encoding='utf-8'))
write=lambda p,v:(root/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
folder=root/'results/g1_future_long_k64_v1'; folder.mkdir(exist_ok=False)
parent=read('configs/experiments/g1_future_long_v1.json'); configs={}
for seed in (17,23,41):
    cfg=copy.deepcopy(parent);cfg.update(seed=seed,run_id=f'g1_future_long_k64_seed{seed}_v1',tokens_per_camera=32)
    path=f'configs/experiments/g1_future_long_k64_seed{seed}_v1.json'
    assert not (root/path).exists();write(path,cfg)
    configs[str(seed)]={'path':path,'sha256':sha(path),'result_root':f'results/g1_future_long_k64_v1/seed{seed}',
        'checkpoint_root_server':f'/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/g1_future_long_k64_v1/seed{seed}'}
parent_paths=['configs/experiments/g1_future_long_v1.json','configs/manifests/long_future_v1/protocol.json',
    'configs/manifests/long_future_v1/windows.json','configs/manifests/long_initial_states_v1/development_panel_30.json',
    'configs/assets/openvla_oft_libero_long.json','results/g1_future_long/source_g1_future_long_v1.json',
    'results/g1_future_long_v1/inputs/input_acceptance.json','results/g1_future_long_v1/inputs/calls.jsonl',
    'results/g1_future_long_v1/training/cache_index.json','results/g1_future_long_v1/closed_loop/config.json',
    'results/g1_future_long_v1/closed_loop/closed_loop_report.json','results/g1_future_long_v1/closed_loop/trials.jsonl',
    'results/g1_future_long_multiseed_v1/scientific_review.json','results/g1_future_long_multiseed_v1/analysis/summary.json',
    'results/g1_future_long_multiseed_v1/analysis/independent_closed_loop_review.json']
for seed,run in ((17,'results/g1_future_long_v1'),(23,'results/g1_future_long_multiseed_v1/seed23'),(41,'results/g1_future_long_multiseed_v1/seed41')):
    for arm in ('A','B'):parent_paths += [f'{run}/training/{arm}/deployment_receipt.json',f'{run}/training/{arm}/training_report.json']
    if seed!=17:parent_paths += [f'{run}/closed_loop/{f}' for f in ('config.json','closed_loop_report.json','trials.jsonl')]
panel=read('configs/manifests/long_initial_states_v1/development_panel_30.json')
events=[json.loads(x) for x in (root/'results/g1_future_long_v1/closed_loop/trials.jsonl').read_text().splitlines()]
states=[]
for task in (0,3,5):
    st=min((s for s in panel['states'] if s['task_id']==task),key=lambda s:s['source_state_index'])
    e=next(e for e in events if e.get('event')=='result' and e['state_trial_id']==st['trial_id'] and e['method']=='dense')
    steps=[int((e['control_steps']-1)*fraction)//8*8 for fraction in (0,.5,.9)]
    states.append({'state_trial_id':st['trial_id'],'task_id':task,'source_state_index':st['source_state_index'],
        'parent_dense_control_steps':e['control_steps'],'capture_steps':steps,'first_observation_sha256':e['chunks'][0]['observation_sha256']})
instances=[{'id':'dense','budget':512,'training_seed':None,'arm':None}]
for budget in (128,64):
    for seed in (17,23,41):
        for arm in ('A','B'):instances.append({'id':f'{arm}{budget}_seed{seed}','budget':budget,'training_seed':seed,'arm':arm})
registration={'schema':'g1_future_long_k64_v1','registered_utc':datetime.now(timezone.utc).isoformat(),
    'registered_after_observing_parent128_results':True,'scope':'VLA visual token pruning success-versus-measured-full-inference latency; no standalone future prediction or image generation',
    'suite':'libero_10','parent_config':'configs/experiments/g1_future_long_v1.json',
    'training_seeds':[17,23,41],'new_configs':configs,'allowed_parent_config_changes':['seed','run_id','tokens_per_camera'],
    'frozen_evidence_sha256':{p:sha(p) for p in parent_paths},
    'training':{'tokens_per_camera':32,'total_tokens':64,'fresh_initialization':True,'warm_start_128_forbidden':True,'updates':100,'effective_batch':8,
        'train_windows':90,'validation_windows':60,'horizon_executed_actions':8,'future_weight':.1,'within_seed_AB_matching':'initial DIE, sample order, optimizer, alpha schedule, checkpoint selection',
        'selection':'minimum hard validation teacher L1 at0/25/50/75/100; earliest tie; no future-loss or rollout selection','hyperparameter_search':False},
    'engineering':{'new_budget64_F01_required_before_training':True,'acceptance_training_seed':17,
        'inherit_old_F00_and_detached_cache_only':True,'parent128_F01_is_not_budget64_acceptance':True,
        'parent_cache_directory_server':'/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/data/g1_future_long_v1_features',
        'cache_producer_identity_retained':True,'all_cache_file_SHA_checked':True,'same_budget64_F01_explicitly_shared_across_seeds':True},
    'evaluation':{'panel':'configs/manifests/long_initial_states_v1/development_panel_30.json','tasks':[0,3,5],'states_per_task':10,
        'environment_seed':0,'runtime_seed':17,'max_steps':520,'wait_steps':10,'action_chunk':8,'new_trials_per_seed':60,'total_new_AB_trials':180,
        'new_methods':['A64','B64'],'reuse_dense_reference':'results/g1_future_long_v1/closed_loop',
        'reuse128_roots':{'17':'results/g1_future_long_v1','23':'results/g1_future_long_multiseed_v1/seed23','41':'results/g1_future_long_multiseed_v1/seed41'},
        'require_unchanged_dense_identity':True,'test_opened':False},
    'profiling':{'suite':'libero_10','observation_source':'Replay original dense policy on the minimum registered development source_state_index of each fixed task',
        'capture_rule':'floor((original dense control_steps-1)*fraction/8)*8, fractions0,.5,.9; chosen from original dense records before any64 or Long latency result',
        'states':states,'maximum_observations':9,'missing_rule':'Preserve missing steps; no last-frame padding or replacement observation. Stop timing and report if all3tasks are not represented.',
        'deployment_instances':instances,'warmup_calls_per_instance':20,'main_rounds':20,'order_seed':1017,
        'schedule':'Each round evaluates all instances in a precomputed balanced cyclic permutation; all methods use the same registered observations. No method-dependent sample removal.',
        'maximum_pipeline_calls':2600,'component_rounds':0,'boundary':'raw simulator observation and instruction to CPU physical8x7 action chunk; includes preprocessing,vision,DIE,packing,VLA,action postprocessing',
        'cuda_synchronize_before_after':True,'hooks_in_main_pass':False,'teacher_cache':False,'future_head_deployed':False,'language_visual_selection_action_cache':False,
        'single_L40_all_instances':True,'uncontended_device_check':True,'raw_loading_and_model_startup_excluded_from_per_call_but_charged_in_GPU_cost':True,
        'report':['all raw calls','per instance and observation median/p95','per seed and method median/p95','method pooled and seed mean summaries','all spikes/failures','allocation GPU cost'],
        'automatic_timing_repeats':False},
    'analysis':{'all_seeds_retained':True,'unique_initial_states':30,'cluster_unit':'state_trial_id, carrying all3seed vectors across budgets/arms',
        'bootstrap_repeats':2000,'bootstrap_seed':1517,'stratified_by':'task_id','primary_comparisons':['B64-A64','B128-A128','B64-A128'],
        'secondary_comparisons':['A64-A128','B64-B128','each method-dense'],'interval_interpretation':'descriptive conditional on fixed30states,3tasks and3training seeds; not broad population significance',
        'no_equivalence_from_nonsignificance':True,'latency_ratios':'same registered observations/hardware; raw call repeats are not independent tasks',
        'support_same_budget':'positive paired success mean with lower conditional95% bound>0; jointly inspect actual latency, no acceleration claim from token counts',
        'support_strict_B64_over_A128_tradeoff':'paired success mean>0 and lower conditional95% bound>0, measured B64 median and p95 both lower than A128; describe inconclusive cases without equivalence claims',
        'continue_C_candidate_only_if':'at least one budget has success-versus-measured-latency improvement supported by these diagnostics; C remains unexecuted without new user authorization'},
    'cost':{'all_new_allocations_counted_once':True,'include_acceptance_training_validation_collection_closed_loop_profiling_failures_retries':True,
        'parent128_cost_gpu_seconds':6557,'parent_cost_excluded_from_increment':True},
    'stop':{'complete_parts_1_and_2_then_report':True,'C_execution_authorized':False,'no_automatic_more_tasks_seeds_scale_ablations_budgets':True,'test_sealed':True}}
path='configs/experiments/g1_future_long_k64_v1.json';assert not (root/path).exists();write(path,registration)
state=read('results/experiment_supervisor/state.json')
assert state['status']=='completed' and state['pending_submission'] is None
state.setdefault('previous_round_costs',[]).append(dict(state['current_round_cost']))
state.update(status='active',stage='G1_F_Long_k64_preregistered',current_method=path,
    current_authorization='User explicitly authorized new3seed64-token A/B training,180paired development trials and Long end-to-end latency. C proposal only, no execution.',
    current_work=['Implement and validate budget64 gates and deployment, then freeze source','Run new64 acceptance then6fresh training arms and180paired trials','Measure Long full O2A across13instances, compare budgets, propose but do not run C'],
    next_allowed_action='Finish CPU audits and immutable preregistered source; submit64 acceptance before any training',
    supervision_status='active_for_new_explicit_request',last_supervision_utc=datetime.now(timezone.utc).isoformat())
state['current_round_cost']={'registered_jobs':0,'allocated_gpu_seconds':0,'allocated_gpu_hours':0,'final':False,'historical_jobs_excluded':True,
    'accounting':'results/g1_future_long_k64_v1/slurm_accounting.json'}
state['last_observed_G1_F_Long_k64_progress']={'training_seeds':[17,23,41],'trained_arms':0,'expected_arms':6,'closed_loop_trials':0,'expected_trials':180,'test_opened':False,'C_run':False}
write('results/experiment_supervisor/state.json',state)
write('results/g1_future_long_k64_v1/registration_receipt.json',{'registration':path,'sha256':sha(path),'new_GPU_jobs':0,'parent_job_check':'all8LongregisteredjobsCOMPLETEDexit0','source_commit_before_new_work':'1f07bc4'})
print(json.dumps({'registered':path,'new_configs':len(configs),'profile_states':states,'new_GPU_jobs':0}))

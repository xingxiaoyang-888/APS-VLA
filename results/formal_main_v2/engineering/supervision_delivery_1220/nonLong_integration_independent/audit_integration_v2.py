from pathlib import Path
from datetime import datetime, timezone
import ast, difflib, hashlib, json, time, traceback

R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/nonLong_integration_independent_1220'
B='results/formal_main_v2/preflight/heartbeat_20261020T2020'
E='results/formal_main_v2/engineering/supervision_delivery_1220'
INPUTS={}
def raw(rel,pin=None):
    p=R/rel;b=p.read_bytes();sha=hashlib.sha256(b).hexdigest()
    if pin is not None: assert sha==pin,(rel,sha,pin)
    INPUTS[rel]={'path':rel,'sha256':sha,'bytes':len(b)}
    return b
def rd(rel,pin=None):return json.loads(raw(rel,pin))
def ref(rel):return {k:INPUTS[rel][k] for k in ('path','sha256')}
def write(name,value):
    b=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    with (D/name).open('xb') as out:out.write(b)
def file_ref(p):
    b=p.read_bytes();return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
start=time.monotonic()
try:
    v1=raw('.local/integrate_1220.py','0bb111709a3ce5cc780a81e49963ea17b4445791f0315b1f49116865c4bb08c7').decode()
    v2=raw('.local/integrate_1220_v2.py','121369a85cd93d4ffeede2ff1d7f91f5b325167347aadcb04b76721d927af83c').decode()
    archival_assert=" assert h(R/E/'nonLong_terminal_independent/paired_development_states.json')==joint['paired_states']['sha256']=='8b767f80a3154778c8b0d3e31119f095eabaaf542b80e0b091564150e3a44346'\n"
    expected=v1.replace(" assert joint['source173_R_and_S_unchanged']",archival_assert+" assert joint['source173_R_and_S_unchanged']",1)
    expected=expected.replace("per_task_and_full_paired_trials=joint['paired_states']","per_task_and_full_paired_trials=ref(E+'/nonLong_terminal_independent/paired_development_states.json')",1)
    expected=expected.replace("put(B+'/root_operations/integrate_1220.py'","put(B+'/root_operations/integrate_1220_v2.py'",1)
    assert v2==expected,'v2 contains unreviewed additional difference'
    ast.parse(v2)
    archived=raw(B+'/root_operations/integrate_1220_v2.py','121369a85cd93d4ffeede2ff1d7f91f5b325167347aadcb04b76721d927af83c')
    assert archived.decode()==v2
    tree=ast.parse(v2)
    assert sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='observe' for n in ast.walk(tree))==1
    assert "with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):" in v2
    assert "c.atomic_json(sp,s,before)" in v2
    assert "assert ctl==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']" in v2
    assert "assert f['completed_training_pairs']==old['formal_main_progress']['completed_training_pairs'] and f['automatic_machine_verified_pairs']==old['formal_main_progress']['automatic_machine_verified_pairs']" in v2
    assert "seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus']" in v2
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('submit','sbatch','scancel') for n in ast.walk(tree))
    rootlog='results/formal_main_v2/control_transport/heartbeat_1220_integration_v2.jsonl'
    log=[json.loads(x) for x in raw(rootlog,'1fbcf25334f7a34ed1fd0bc0306263136348759afc5a143f57b3678da4820ea9').splitlines()]
    assert len(log)==2 and log[0]['entrypoint_sha256']==INPUTS['.local/integrate_1220_v2.py']['sha256']
    assert log[0]['frozen_files']==173 and log[1]['returncode']==0 and log[1]['source173_and_entrypoint_unchanged'] is True
    summary=rd(B+'/summary_after_dispatch.json','b6faae7369781c6a6818f49038c31832655065c2c96c42c22f17a11f77f3d865')
    stats=rd(summary['diagnostics']['path'],summary['diagnostics']['sha256'])
    joint=rd(E+'/nonLong_terminal_independent/independent_review.json','67c2e32b61a1aa2ec02202d03ff2e28112e971f3968c2f8a88e3ad5100e1f120')
    published=raw('results/formal_main_v2/downstream_reviews/nonLong_seed23_1220_independent.json','67c2e32b61a1aa2ec02202d03ff2e28112e971f3968c2f8a88e3ad5100e1f120')
    assert published==raw(E+'/nonLong_terminal_independent/independent_review.json')
    sub=rd(E+'/nonLong_submission_independent/independent_review.json','7e272e3787d4027c9593544e98f82affcdb55c1ff9e99daca2d38c4cefd016fe')
    assert joint['status']==sub['status']=='passed'
    assert joint['source173_R_and_S_unchanged'] and joint['totals']['trials']==400 and joint['totals']['allocated_gpu_seconds']==4551
    assert not joint['checkpoint_bytes_read'] and not joint['sealed_final_values_read'] and joint['new_GPU_jobs']==0
    paired=stats['per_task_and_full_paired_trials']
    assert paired['path']==E+'/nonLong_terminal_independent/paired_development_states.json'
    assert paired['sha256']==joint['paired_states']['sha256']=='8b767f80a3154778c8b0d3e31119f095eabaaf542b80e0b091564150e3a44346'
    rd(paired['path'],paired['sha256'])
    assert stats['jobs']==summary['accepted_jobs']
    assert stats['total_trials']==400 and stats['unique_initial_states']==200 and stats['all_job_GPU_seconds']==4551 and stats['GPU_cost_already_in_Slurm_total']
    assert not stats['bootstrap_three_seed_claimed'] and not stats['O2A_measured'] and not stats['final_results']
    state_bytes=raw('results/experiment_supervisor/state.json');state=json.loads(state_bytes);f=state['formal_main_progress'];ctl=state['autonomous_training_v1']
    assert f['root_and_independent_completed_arms']==summary['root_independent_complete']==64
    assert f['root_and_independent_reviewed_arm_updates']==summary['root_independent_updates']==321000
    assert f['completed_development_trials']==summary['raw_historical_and_current_development_trials']==3212
    assert f['current_action_development_trial_count']==summary['current_action_development_trials']==2000
    assert f['current_action_development_unique_initial_states']==summary['current_action_unique_initial_states']==300
    assert f['historical_other_action_semantics_development_trials']==1212 and f['Long22_development_statistics']['explicit_legacy_equivalent_trials']==600
    assert summary['compatible_current_and_explicit_legacy_trials']==2600 and summary['explicit_legacy_equivalent_Long_trials']==600
    assert summary['completed_by_suite']=={'libero_10':18,'libero_spatial':18,'libero_object':16,'libero_goal':12}
    assert f['completed_final_trials']==summary['final_completed']==summary['new_final_trials']==0
    assert not f['test_opened'] and not f['global_release_created'] and summary['final_release'] is False and not summary['scientific_settings_changed']
    jmap={j['job_id']:j for j in joint['jobs'].values()}
    for entry in summary['accepted_jobs']:
        jid=entry['job_id'];j=jmap[jid]
        assert entry==f['new_action_development_verified_by_job'][jid]
        assert entry['suite'] in ('libero_spatial','libero_object') and entry['seed']==23 and entry['visual_tokens']==128
        assert entry['completed_trials']==j['trials']==200 and entry['unique_initial_states']==j['unique_initial_states']==100
        assert entry['per_task']==j['per_task'] and entry['paired_outcomes']==j['discordance']
        assert entry['successes']=={'A128_seed23':j['A_success'],'B128_seed23':j['B_success']}
        assert entry['initial_observation_token_overlap_mean']==j['t0_token_diagnostics']['mean_intersection_over_128']
        assert entry['initial_observation_token_Jaccard_mean']==j['t0_token_diagnostics']['mean_Jaccard']
        assert entry['offline_validation_diagnostics']==j['offline_validation_diagnostics']
        assert entry['independent_review']==ref('results/formal_main_v2/downstream_reviews/nonLong_seed23_1220_independent.json')
        assert entry['GPU_seconds']==j['allocated_GPU_seconds'] and entry['no_legacy_semantics_equivalence_claimed']
        assert entry['O2A_complete'] is False and entry['whole_suite_development_complete'] is False
        rr=entry['root_review'];root=rd(rr['path'],rr['sha256'])
        assert root['status']=='passed' and root['completed_trials']==200 and root['scientific_complete']
        assert {m:v['successes'] for m,v in root['reconstructed_summary']['methods'].items()}==entry['successes']
        submission=next(x for x in f['nonLong_development_submissions_1032'] if x['job_id']==jid)
        assert submission['completed_trials_accepted']==200 and not submission['scientific_terminal_acceptance_pending']
    current=f['new_action_development_verified_by_job'];assert sum(x['completed_trials'] for x in current.values())==2000
    bysuite={}
    for entry in current.values():
        rr=entry['root_review'];root=rd(rr['path'],rr['sha256']);states=bysuite.setdefault(root['suite'],set())
        for pair in root['reconstructed_summary']['paired_AB'].values():states.update(x['state_trial_id'] for x in pair['results'])
    counts={k:len(v) for k,v in bysuite.items()}
    assert counts==summary['unique_current_initial_states_by_suite']==f['current_action_development_unique_initial_states_by_suite']=={'libero_10':100,'libero_spatial':100,'libero_object':100}
    assert summary['new_submissions']==f['nonLong_development_submissions_1220']
    assert {x['job_id'] for x in summary['new_submissions']}=={x['job_id'] for x in sub['jobs']}=={'3049132','3049172','3049191'}
    smap={x['job_id']:x for x in sub['jobs']}
    for entry in summary['new_submissions']:
        original=smap[entry['job_id']]
        assert entry['authorization']==original['authorization'] and entry['original_ACK']==original['original_ACK']
        assert entry['root_reconciliation']==original['root_reconciliation'] and entry['original_failed_transaction']==original['retained_post_submit_accounting_lag_failure']
        assert entry['method_ids']==original['methods'] and entry['suite']==original['suite']
        assert entry['planned_trials']==200 and entry['completed_trials_accepted']==0 and entry['scientific_terminal_acceptance_pending']
        assert not entry['final_evaluation_enabled'] and entry['duplicate_submissions']==0
        for key in ['authorization','original_ACK','root_reconciliation','original_failed_transaction']:
            r=entry[key];rd(r['path'],r['sha256'])
    assert sum(x['planned_trials'] for x in summary['new_submissions'])==600
    assert sum(x['completed_trials_accepted'] for x in summary['new_submissions'])==0
    rows=summary['scheduler']['rows'];registered=state['registered_jobs']
    relevant=[x for x in registered if x.get('experiment')=='formal_main_v2']
    missing=[str(x['job_id']) for x in relevant if str(x['job_id']) not in rows]
    assert not missing,('New registry entries since snapshot; adjust saved-snapshot scope, not cost',missing)
    seconds=sum(rows[str(x['job_id'])]['elapsed_seconds']*rows[str(x['job_id'])]['gpus'] for x in relevant)
    assert seconds==summary['allocated_GPU_seconds']==1900067 and seconds/3600==summary['allocated_GPU_hours']
    assert summary['includes_all_registered_allocations'] and not summary['cost_is_final']
    assert state['current_round_cost']['allocated_gpu_seconds']>=seconds
    assert summary['active_GPU_jobs']==8 and len(summary['capacity']['occupied'])==8 and not summary['capacity']['unknown'] and not summary['capacity']['findings']
    assert summary['controller']=='3034538' and summary['controller_owner_id']==ctl['owner_id']
    assert rows['3034538']['status']=='RUNNING' and rows['3034538']['gpus']==0
    assert summary['pending'] is None and summary['reserved_GPU_slots']==0
    assert f['latest_new_action_development_verified']==summary['diagnostics']
    assert f['latest_capacity_refill']==ref(B+'/summary_after_dispatch.json')
    assert state['last_root_supervision_snapshot']==ref(B+'/summary_after_dispatch.json')
    nonlong=raw('docs/正式非Long开发结果.md','afc852285c4f667b1aed960b09e08205821fcce92580897a75c244285a79ce5d').decode()
    for entry in summary['accepted_jobs']:
        label={'libero_spatial':'Spatial','libero_object':'Object'}[entry['suite']]
        line=f"| {label} | {entry['successes']['A128_seed23']} | {entry['successes']['B128_seed23']} | {entry['B_minus_A_percentage_points']:+.0f} | {entry['initial_observation_token_overlap_mean']:.6f} | {entry['initial_observation_token_Jaccard_mean']:.6f} | {entry['GPU_seconds']} |"
        assert line in nonlong
        for arm,diag in entry['offline_validation_diagnostics'].items():
            line=f"| {entry['suite']}/{arm} | {diag['selected_update']} | {diag['hard_validation_teacher_L1_task_equal']:.8f} | {diag['hard_validation_demonstration_L1_task_equal']:.8f} | {diag['validation_windows']} |"
            assert line in nonlong
        for task in entry['per_task']:
            line=f"| {entry['suite']} | {task['task_id']} | {task['A_success']} | {task['B_success']} | {task['B_minus_A_pp']:+.0f} |"
            assert line in nonlong
    for phrase in ['单seed差异不能证明稳定收益或等效','t0仅比较相同hash的初始观测','离线硬剪枝诊断，非闭环动作误差','历史Object600和Spatial12仍单列','Long已接受的显式等价600条只复用、不重复执行或加分母']:
        assert phrase in nonlong
    docs=[]
    for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记']:
        rel='docs/'+name+'.md';text=raw(rel).decode();head=text.split('\n')[:6]
        assert '训练仍为64/72组双审完成' in '\n'.join(head)
        assert '新增400条开发验收' in '\n'.join(head) and '另3批600条已按原配置一次提交' in '\n'.join(head)
        assert '当前8GPU占槽，累计527.796GPU小时（非最终）' in '\n'.join(head)
        assert '最终0/35200继续封存' in '\n'.join(head)
        docs.append(ref(rel))
    diff=''.join(difflib.unified_diff(v1.splitlines(True),v2.splitlines(True),fromfile='.local/integrate_1220.py',tofile='.local/integrate_1220_v2.py'))
    with (D/'reviewed_v1_to_v2.diff').open('x') as out:out.write(diff)
    report={
      'schema':'formal_main_v2','kind':'independent_nonLong1220_integration_acceptance','status':'passed','synthetic':False,'review_role':'independent',
      'utc':datetime.now(timezone.utc).isoformat(),'scope':'Static integration-source review and exact actual state/summary/document reconciliation; reuses already-completed original trial and submission audits. No consumer rerun or new scheduler query.',
      'source_v1':ref('.local/integrate_1220.py'),'source_v2':ref('.local/integrate_1220_v2.py'),
      'root_execution_transport':ref(rootlog),'summary':ref(B+'/summary_after_dispatch.json'),
      'actual_readonly_state_snapshot':ref('results/experiment_supervisor/state.json'),
      'source_changes_exact':['Assert archived paired-state content SHA','Use canonical archived paired-state reference in new diagnostics','Archive v2 source under its correct filename'],
      'checks':{
        'raw_historical_and_current_count':{'before':2812,'accepted_delta':400,'after':3212},
        'current_action_count':{'before':1600,'accepted_delta':400,'after':2000},
        'unique_current_states':{'before':100,'after':300,'per_suite':counts,'dedup_key':'suite plus state_trial_id; seeds/methods are not independent states'},
        'legacy1212_unchanged':True,'Long600_explicit_compatible_no_duplicate_execution_cost_or_denominator':True,
        'current_plus_explicit_Long600':2600,'historical_Object600_and_Spatial12_not_adopted':True,
        'accepted_two_jobs_exact_joint_independent_mapping':True,'per_task_success_t0_overlap_and_offline_L1_exact':True,
        'single_seed_development_only_no_O2A_or_final_claim':True,
        'next600_planned_only_accepted0':True,
        'training64_of72_and321000_updates_preserved':True,
        'controller_registry_training_pair_objects_preserved':'Source exact equality assertions executed successfully; no claim of a newly captured pre-integration full-state snapshot.',
        'writer_lock_and_CAS_in_original_source':True,
        'frozen173_unchanged':'Reused terminal independent report plus root integration exact transport success; no repeat consumer reconstruction.',
        'root_final_single_saved_Slurm_observation':True,
        'allocated_GPU_seconds_recomputed_from_saved_rows':seconds,
        'accepted4551GPU_seconds_already_in_total_not_added_again':True,
        'capacity_at_saved_observation':8,'live_mutable_state_caveat':'Controller may continue ordinary updates after recorded observation.',
        'final_trials':0,'final_release':False,
        'canonical_paired_reference_reachable':paired,
        'scope_no_scientific_setting_change':True},
      'reused_independent_trial_audit':ref(E+'/nonLong_terminal_independent/independent_review.json'),
      'reused_independent_submission_audit':ref(E+'/nonLong_submission_independent/independent_review.json'),
      'docs':docs+[ref('docs/正式非Long开发结果.md')],
      'input_refs':list(INPUTS.values()),'blockers':[],
      'new_GPU_runs':0,'new_scheduler_queries':0,'consumer_reconstructions':0,
      'model_checkpoint_bytes_read':False,'sealed_final_values_read':False,'shared_state_Git_or_Slurm_mutations':False,
      'wall_seconds':time.monotonic()-start,
    }
    write('independent_review.json',report)
    write('manifest.json',{'schema':'formal_main_v2','kind':'private_independent_integration_review_manifest','status':'passed','files':[file_ref(p) for p in sorted(D.iterdir()) if p.is_file() and p.name!='manifest.json']})
    print(json.dumps({'status':'passed','report':file_ref(D/'independent_review.json'),'manifest':file_ref(D/'manifest.json'),'new_queries':0}))
except Exception as exc:
    write('failure.json',{'status':'failed','error':str(exc),'traceback':traceback.format_exc(),'inputs':list(INPUTS.values()),'production_mutations':False})
    raise

from pathlib import Path
import hashlib,json,math,statistics,datetime
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
O=R/'.local/long64_selected_diagnostics_0830'
S=P/'snapshots/formal_main_v2_run_564be0995e'
inputs={}
def sha(b):return hashlib.sha256(b).hexdigest()
def read(rel,pin=None):
    p=R/rel
    assert p.suffix in ('.json','.py')
    b=p.read_bytes(); h=sha(b)
    if pin is not None: assert h==pin,(rel,h,pin)
    inputs[rel]={'path':rel,'bytes':len(b),'sha256':h}
    return json.loads(b) if p.suffix=='.json' else b

def write(name,obj):
    p=O/name
    with p.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n')
    return {'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}

def close(a,b): assert math.isclose(float(a),float(b),rel_tol=0,abs_tol=1e-14),(a,b)

old_manifest=read('.local/independent_long64_development_0830/manifest.json','e14cb0e58f94254a7511b0ec10bec425b83a139ed41ac5222f6762f277d2e471')
source_rel='src/cti_vla/training/formal_future.py'
source=read(source_rel,'3f4d2f933aa276d26dccfc2ce16d145f8bf40c7c1446ffddbb7342a763bc097b')
assert sha((S/source_rel).read_bytes())==sha(source)
assert b'"demonstration_l1": sum(v["demonstration_l1"] for v in per_task.values()) / len(per_task)' in source
jobs=[
 (17,'3047156','9bd3713f5260d9b6da1397c6507330503ce429c59a4ea4a15986ac9a5d50e190','.local/independent_long_development_0727/job3047156/independent_review.json','9cb561881876e7a40cc850bae9f38e12d1612960b16c6c5b27f0ec34ba2cb3d5'),
 (23,'3047163','5a1cc6e631a421f0891da6f6810fb0824717a37cd6d18fa26800e930acdac0bc','.local/independent_long_development_0727/job3047163/independent_review.json','f507905b5a1ff214674ed39e2847fcda67224f62ec183915b2d5b5cd57dd9d57'),
 (41,'3047443','20f91c0060f086bcf402cc0b9b4e9863397c27876f4809dd9bef211aa0c87c25','.local/independent_long64_development_0830/job3047443/independent_review.json','0a04480cfae7c48beb8b4a81b99c5611d2273bd6f7c685a522beb096a7fd71d1')]
rows=[]; pairs=[]; panel=None; window_manifest=None
for seed,job,rootsha,indrel,indsha in jobs:
    rootrel=f'results/formal_main_v2/downstream_reviews/{job}.json'
    root=read(rootrel,rootsha); ind=read(indrel,indsha)
    assert root['job_id']==job or str(root['job_id'])==job
    assert ind['root_review']=={'path':rootrel,'sha256':rootsha}
    assert ind['completed_trials']==200 and ind['unique_initial_states']==100
    assert not ind['final_release'] and not ind['final_state_values_read']
    overlap=ind['initial_observation_token_overlap_mean']; assert 0<=overlap<=1
    pair={'seed':seed,'development_job_id':job,'initial_observation_token_overlap_mean':overlap,
          'metric':'mean(|A retained set intersection B retained set| / 64)',
          'paired_initial_observations':100,'scope':ind['token_overlap_scope'],
          'independent_development_review':inputs[indrel],'canonical_development_review':inputs[rootrel]}
    pairs.append(pair)
    methods=root['reconstructed_summary']['provenance']['manifest']['methods']
    assert len(methods)==2
    for arm in ['A','B']:
        matches=[m for m in methods if m['identity']['method_id']==f'{arm}64_seed{seed}']; assert len(matches)==1
        method=matches[0]; ident=method['identity']; rel=method['receipt']
        receipt=read(rel,root['evidence_sha256'][rel])
        digest=sha(json.dumps(receipt,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode())
        assert digest==ident['deployment_receipt_sha256']
        md=receipt['metadata']
        assert receipt['training_complete'] and receipt['completed_updates']==receipt['planned_updates']==5000
        assert md['arm']==arm and md['seed']==seed and md['visual_tokens']==64 and md['suite']=='libero_10'
        assert ident['future_head_deployed'] is False
        assert receipt['checkpoint_sha256']==ident['checkpoint_sha256']==ind['selected_checkpoint_SHA'][ident['method_id']]
        assert md['selection_metric']=='task_macro_hard_validation_teacher_l1'
        evals=receipt['evaluations']; assert [e['update'] for e in evals]==list(range(0,5001,500))
        selected=min(evals,key=lambda e:(e['validation_metric'],e['update']))
        assert selected['update']==md['update']; close(selected['validation_metric'],md['validation_metric'])
        assert Path(selected['artifact_path']).is_relative_to(P)
        valrel=str(Path(selected['artifact_path']).relative_to(P))
        val=read(valrel,selected['artifact_sha256'])
        assert val['arm']==arm and val['update']==md['update'] and val['metric']==md['selection_metric']
        close(val['validation_metric'],md['validation_metric'])
        assert val['windows']==165 and val['tasks']==10 and len(val['observations'])==165
        ids=sorted((x['task_id'],x['episode_id'],x['window_id']) for x in val['observations'])
        assert len(set(ids))==165
        if panel is None: panel=ids
        else: assert ids==panel
        if window_manifest is None: window_manifest=ident['window_manifest_sha256']
        else: assert window_manifest==ident['window_manifest_sha256']
        grouped={str(t):[x for x in val['observations'] if str(x['task_id'])==str(t)] for t in range(10)}
        assert set(val['per_task'])==set(grouped)
        for t,obs in grouped.items():
            assert obs and val['per_task'][t]['windows']==len(obs)
            for key in ['teacher_l1','demonstration_l1']:
                assert all(math.isfinite(x[key]) and x[key]>=0 for x in obs)
                close(sum(x[key] for x in obs)/len(obs),val['per_task'][t][key])
        close(sum(val['per_task'][str(t)]['teacher_l1'] for t in range(10))/10,val['validation_metric'])
        close(sum(val['per_task'][str(t)]['demonstration_l1'] for t in range(10))/10,val['demonstration_l1'])
        close(sum(x['teacher_l1'] for x in val['observations'])/165,val['window_weighted_teacher_l1_diagnostic'])
        rows.append({'seed':seed,'arm':arm,'method_id':ident['method_id'],'selected_update':md['update'],
                     'selected_validation_task_macro_hard_teacher_L1':val['validation_metric'],
                     'selected_validation_task_macro_hard_demonstration_L1':val['demonstration_l1'],
                     'window_weighted_teacher_L1_diagnostic':val['window_weighted_teacher_l1_diagnostic'],
                     'checkpoint_sha256':ident['checkpoint_sha256'],
                     'checkpoint_path_record_only_not_read':method['checkpoint'],
                     'selected_candidate_sha256_record_only_not_read':selected['candidate_sha256'],
                     'receipt_file':inputs[rel],'receipt_canonical_identity_sha256':digest,
                     'selected_validation_file':inputs[valrel],
                     'canonical_development_review':inputs[rootrel],
                     'validation_training_job_id':val['job_id'],'validation_windows':165,'validation_tasks':10,
                     'all11_evaluation_nodes':[{'update':e['update'],'validation_metric':e['validation_metric'],
                         'artifact_sha256':e['artifact_sha256']} for e in evals],
                     'initial_observation_AB_token_overlap_mean':overlap,
                     'token_overlap_scope':'100 identical paired development initial observations; distinct from validation windows',
                     'missing_fields':[]})
assert len(rows)==6
panel_sha=sha(json.dumps(panel,separators=(',',':'),ensure_ascii=False).encode())
report={'schema':1,'kind':'Long64_selected_checkpoint_existing_artifacts_diagnostics','status':'pass',
        'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':rows,'seed_pairs':pairs,
        'source_aggregation':{'path':source_rel,'sha256':sha(source),'lines':[395,410],
                             'teacher':'mean of 10 per-task mean hard teacher L1 values',
                             'demonstration':'mean of 10 per-task mean hard demonstration L1 values; stored demonstration_l1 field'},
        'same_fixed_validation_panel':{'windows':165,'tasks':10,'ordered_window_identity_sha256':panel_sha,
                                       'window_manifest_sha256':window_manifest,'all6_match':True},
        'selection_verified':'minimum task_macro_hard_validation_teacher_l1 over update0 and every500 through5000; ties earliest',
        'missing_fields':[],'checkpoint_bytes_read':False,'fresh_predictions':False,'GPU_seconds_added':0,
        'training_final_update_substituted_for_selected_update':False,
        'prior_directory_modified':False,'state_modified':False,'Git_modified':False,'Slurm_submitted':False,
        'sealed_values_read':False,'O2A_inference':False,'final_performance_inference':False,
        'scope':'development diagnostics only; identical initial states across seeds are not independent new states',
        'input_files':list(inputs.values())}
ref=write('selected_checkpoint_diagnostics.json',report)
lines=['# Long64 已选 checkpoint 诊断','','仅提取已验收的非权重记录，未加载 checkpoint、未新增预测或 GPU 作业。验证面板为同一组 165 个窗口、10 个任务；两项 L1 均按任务等权汇总。选择规则为 11 个验证节点中 teacher L1 最小者，平分取较早。','',
'| seed | 方法 | 选中 update | 硬 teacher L1 | 硬示范 L1 | 初观测 A/B token 重合率 | checkpoint SHA256 |',
'|---:|:---:|---:|---:|---:|---:|:---|']
for row in rows:
    lines.append(f"| {row['seed']} | {row['arm']} | {row['selected_update']} | {row['selected_validation_task_macro_hard_teacher_L1']:.9f} | {row['selected_validation_task_macro_hard_demonstration_L1']:.9f} | {row['initial_observation_AB_token_overlap_mean']:.8f} | {row['checkpoint_sha256']} |")
lines+=['','token 重合率是 100 个配对开发初观测上交集大小除以 64 的均值；不是验证窗口指标，也不比较后续分岔状态。相同 seed 的 A/B 两行展示同一个配对指标。','',
'6 组无缺项。已选 update 与训练终步分开记录；只有 seed23 B 的已选 update 恰为 5000。best checkpoint 与对应验证候选的文件 SHA 分别记录，不假定两种文件字节相同。','',
'JSON 保留完整精度、11 个选模节点、每项来源路径/字节数/SHA256。已有 128/256 预算结果未合并。本记录不支持完整推理延迟或最终性能结论。']
with (O/'selected_checkpoint_diagnostics.md').open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
write('source_manifest.json',{'schema':1,'files':list(inputs.values()),'all_sources_immutable_bound':True})
print(json.dumps({'status':'pass','report':ref,'rows':[{k:v for k,v in row.items() if k in ['seed','arm','selected_update','selected_validation_task_macro_hard_teacher_L1','selected_validation_task_macro_hard_demonstration_L1','initial_observation_AB_token_overlap_mean']} for row in rows]},sort_keys=True))

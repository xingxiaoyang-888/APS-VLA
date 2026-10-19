from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0632';E='results/formal_main_v2/engineering/supervision_delivery_2232'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return {'path':rel,'sha256':h(R/rel)}
def read(rel):return json.loads((R/rel).read_text())
def checked(rel,pin):assert h(R/rel)==pin;return read(rel)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
 return ref(rel)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('root_integrate2232',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and f['root_and_independent_completed_arms']==48 and f['root_and_independent_reviewed_arm_updates']==248000
 assert f['completed_development_trials']==1212 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 nr='results/formal_main_v2/libero_object/k64/seed41/training/segment_reviews/3037535.json';ni=nr.replace('.json','_independent.json')
 root=checked(nr,'d2836fab19c5c11cd1baba1a102ec7e677ebab781091f2b2bcb103f35825ddf8')
 ind=checked(ni,'a1643466dd8bbe032261c195c8ebef6ef214c373d82ab4ede6829450a1623301')
 assert root['status']=='passed' and ind['status']=='passed_complete_training_only' and root['completed_by_arm']==ind['completed_by_arm']=={'A':5000,'B':5000}
 assert root['pair_allocated_gpu_seconds']==ind['cost']['all_pair_allocated_GPU_seconds']==62663
 proof=ind['parallel_root_reconstruction'];assert proof['path']==nr and proof['sha256']==h(R/nr) and proof['new_reviewed_arm_updates']==9000
 for item in [proof['prior_root_review'],proof['prior_independent_review'],proof['selected_server_proof']]:assert h(R/item['path'])==item['sha256']
 prior=read(proof['prior_root_review']['path']);previous=read(proof['prior_independent_review']['path'])
 assert prior['completed_by_arm']=={'A':500,'B':500} and previous['status']=='passed'
 for path,pin in ind['read_evidence_sha256'].items():assert h(R/path)==pin
 manifest='.local/Long3043709_independent_2232/archive_closure.json'
 closure=checked(manifest,'fc05e5f4e9f787658039fa1e2e6c33036cf0c70ce6d67d5e08e1ce76c5db239e')
 rows=closure['files']+[dict(path=manifest,sha256=h(R/manifest),bytes=(R/manifest).stat().st_size)];copies=[]
 for row in rows:
  source=R/row['path'];assert source.parent==R/'.local/Long3043709_independent_2232' and source.is_file() and not source.is_symlink()
  assert h(source)==row['sha256'] and source.stat().st_size==row['bytes']
  dest=R/E/'Long3043709_independent'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as stream:stream.write(source.read_bytes())
  assert h(dest)==row['sha256'];copies.append(dict(source=row,archive=ref(dest.relative_to(R).as_posix())))
 lr='results/formal_main_v2/downstream_reviews/3043709.json';li='results/formal_main_v2/downstream_reviews/3043709_independent.json'
 with (R/li).open('xb') as stream:stream.write((R/'.local/Long3043709_independent_2232/independent_review.json').read_bytes())
 ld=checked(li,'bc7e6d2abc1a73529d1b57d8a7f6e03ac4c301f8eb98c3565cd18ef03217535a')
 rr=checked(lr,'3868af9c4d8c5a1c2a896047f3b9d170b7fa2f1eaeb10fcc51689686a8589325')
 assert ld['status']==rr['status']=='passed' and ld['root_review']==ref(lr) and ld['scientific_complete'] and rr['scientific_complete']
 assert ld['completed_trials']==rr['completed_trials']==ld['expected_trials']==rr['expected_trials']==200
 assert ld['successes']=={'A128_seed23':95,'B128_seed23':92} and ld['raw_invocation_job_ids']==['3043709'] and ld['cost']['all_attempt_GPU_seconds']==3083
 assert ld['actual_runtime_chain_verified'] and not ld['O2A_latency_verified'] and not ld['final_release']
 for path,pin in rr['evidence_sha256'].items():assert h(R/path)==pin
 delivery=save(B+'/Long3043709_independent_delivery.json',dict(copies=copies,canonical=ref(li),source_manifest=ref(manifest),new_GPU_submissions=[]))
 entry=f['completed_training_pairs']['libero_object_k64_seed41'];assert entry['verification_kind']=='machine_automatic_not_independent'
 selected=[]
 for a in ['A','B']:
  dr='results/formal_main_v2/libero_object/k64/seed41/training/'+a+'/deployment_receipt.json';d=read(dr);ar=ind['arms'][a]
  assert d['checkpoint_sha256']==ar['best_sha256'] and d['metadata']['update']==ar['earliest_selected_update'] and d['metadata']['validation_metric']==ar['selected_teacher_l1']
  selected.append(dict(arm=a,path='/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_object/k64/seed41/'+a+'/best.pt',expected_sha256=d['checkpoint_sha256'],selected_update=ar['earliest_selected_update'],validation_metric=ar['selected_teacher_l1'],metadata_source=ref(dr)))
 binding=save(B+'/3037535_selected_binding.json',dict(status='root_and_independent_selected_identity_verified',root_review=ref(nr),independent_review=ref(ni),actual_server_bytes=ref(B+'/3037535_selected_server.json'),selected_checkpoints=selected,weights_copied=False))
 entry.update(job_id='3037535',suite='libero_object',visual_tokens=64,seed=41,root_review=nr,root_review_sha256=h(R/nr),independent_review=ni,independent_review_sha256=h(R/ni),selected_checkpoints=selected,selected_server_review=binding['path'],selected_server_review_sha256=binding['sha256'],verification_kind='machine_automatic_plus_root_and_independent_raw_reconstruction')
 f['root_and_independent_completed_arms']=50;f['root_and_independent_reviewed_arm_updates']+=9000
 f['completed_engineering_segments'].append(dict(job_id='3037535',suite='libero_object',visual_tokens=64,seed=41,status='passed_root_and_independent_complete_training',updates_by_arm={'A':5000,'B':5000},allocated_gpu_seconds=60018,pair_total_gpu_seconds=62663,root_review=nr,root_review_sha256=h(R/nr),independent_review=ni,independent_review_sha256=h(R/ni),new_reviewed_arm_updates=9000))
 scope=f['downstream_action_range_issue']['Long16_pre_execution_qualified_scope'];assert scope['accepted_new_trials']==0 and scope['new_GPU_submissions']==['3043709'] and len(scope['submitted_shards'])==1
 scope['submitted_shards'][0].update(status='passed_root_and_independent_scientific_development',root_review=ref(lr),independent_review=ref(li),completed_trials=200,allocated_GPU_seconds=3083,actual_runtime_verified=True)
 scope.update(accepted_new_trials=200,actual_GPU_verified_method_ids=['A128_seed23','B128_seed23'],all16_method_GPU_verified=False,remaining_unsubmitted_shards=7,latest_actual_terminal_review=ref(lr),latest_independent_terminal_review=ref(li))
 f['completed_development_trials']+=200
 f['new_action_development_verified']=dict(job_id='3043709',root_review=ref(lr),independent_review=ref(li),completed_trials=200,unique_initial_states=100,successes=ld['successes'],paired_outcomes=ld['paired_outcomes'],B_minus_A_percentage_points=-3,action_semantics_sha256=ld['action_semantics_sha256'],no_legacy_semantics_equivalence_claimed=True,O2A_complete=False,whole_suite_development_complete=False)
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])<=8 and obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 assert obs['rows']['3043709']['status']=='COMPLETED' and obs['rows']['3043709']['elapsed_seconds']==3083
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost']['allocated_gpu_seconds'];s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 keys=[k for k,v in f['completed_training_pairs'].items() if v.get('root_review') and v.get('independent_review') or v.get('terminal_root_and_independent_review')]
 assert len(keys)==25
 suites={suite:2*sum(k.startswith(suite+'_k') for k in keys) for suite in ['libero_10','libero_spatial','libero_object','libero_goal']}
 assert suites=={'libero_10':18,'libero_spatial':16,'libero_object':14,'libero_goal':2}
 inventory=read('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json');assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():assert h(R/rel)==h(R/'snapshots/formal_main_v2_run_564be0995e'/rel)==pin
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 outcome=save(B+'/Long128seed23_development_result.json',dict(schema='formal_main_v2',status='partial_development_result_root_and_independent_verified',job_id='3043709',root_review=ref(lr),independent_review=ref(li),successes=ld['successes'],per_task=ld['per_task'],paired_outcomes=ld['paired_outcomes'],B_minus_A_percentage_points=-3,unique_initial_states=100,closed_loop_trials=200,selected_checkpoints={a:{k:read('results/formal_main_v2/libero_10/k128/seed23/training/'+a+'/deployment_receipt.json')['metadata'][k] for k in ['update','validation_metric']} for a in ['A','B']},initial_observation_token_overlap_mean=ld['initial_observation_token_overlap_mean'],token_overlap_scope=ld['token_overlap_scope'],allocated_GPU_seconds=3083,all_costs_counted_once=True,latency_not_yet_measured=True,final_evaluation=False,no_three_seed_or_significance_inference=True))
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='scheduled_supervision_training_and_actual_action_development_accepted',utc=now,root_independent_complete=50,machine_complete=f['trained_arms'],completed_by_suite=suites,total_arms=72,new_completed_training_groups=2,root_independent_updates=257000,new_reviewed_arm_updates=9000,Object64seed41_root=ref(nr),Object64seed41_independent=ref(ni),new_development_trials_accepted=200,all_historical_and_new_development_trials=1412,Long128seed23_development=outcome,Long_independent_delivery=delivery,new_GPU_submissions=[],new_duplicate_submissions=0,scheduler=obs,capacity=cap,active_GPU_jobs=len(cap['occupied']),reserved_GPU_slots=ctl['reserved_GPU_slots'],allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,cost_is_final=False,completed_final_trials=0,expected_final_trials=35200,final_sealed=True,normal_training_left_to_controller=True,server_only=True,source_mirror_only_repair=ref(B+'/3043709_source_snapshot_mirror.json'),initial_review_failure_retained=ref(B+'/3043709_root_review_failure.json'),scientific_files_unchanged=173))
 f['latest_incremental_review']=summary;f['incremental_review_history'].append(summary)
 f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied']);f['parallel_execution']['actual_running_allocated_GPUs']=sum(obs['rows'][x]['gpus'] for x in cap['occupied'] if obs['rows'][x]['status']=='RUNNING')
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']='2026-10-20'
 s['current_work']='50/72 complete training groups root+independent accepted (Long18,Spatial16,Object14,Goal2),257000 reviewed arm updates. Long128 seed23 action-version development200 passed both raw reviews: A95/B92 over100 common initial states; no benefit or final/latency claim. Normal8-GPU training continues under controller.'
 s['next_actions']=['Leave healthy auto5000 training to controller and next scheduled heartbeat; preserve11 validation nodes, complete resume and max8 GPU slots.','At next genuine spare capacity use exact already admitted Spatial64seed23 continuous1500to5000 authorization once; never duplicate its historical failure/recovery. Normal Goal64seed41 may fill first under controller.','Proceed with remaining7 already registered Long development200 shards only through exact one-time authorization/reservation and shared8-slot accounting; never rerun accepted3043709 or change checkpoint based on development outcomes.','Object64seed23 original CUDA-target recovery and Spatial failed development continuation remain separately bounded engineering work; old failures are retained.','All72 selected checkpoints+16 reference identities+4suite complete development receipts and root globalrelease remain mandatory before final35200. Complete same-checkpoint O2A and component timing with matched action semantics; no old/new equivalence assumed.']
 s['next_allowed_action']=s['next_actions'][0]
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 c.atomic_json(sp,s,before)
 detail=f'{stamp}：正式训练 **50/72组通过root与独立复核**（Long18、Spatial16、Object14、Goal2）。新增Object64 seed41 A/B各5000步：11×204硬剪枝验证、40000窗口使用和实际best/resume字节一致，分别选2000/2500步。新增9000已审臂更新，累计257000；原3028482与3037535共62663 GPU秒全部保留。\\n\\n'.replace('\\n','\n')
 detail+=f'**{len(cap["occupied"])}卡活动，累计{seconds/3600:.3f} GPU小时**（含失败和运行中分配，非最终成本）。Long128 seed23新增200条开发闭环通过双重复核：A95/100、B92/100，B−A为−3个百分点；共同100初态中双方成功91、仅A4、仅B1、均失败4。本组未观察到未来监督收益；不能推断三seed平均、显著性/等效或成功率—延迟折中。实际新版部署链、6906次8×7动作chunk及零未来头调用通过，3083 GPU秒仅计一次。\\n\\n'.replace('\\n','\n')
 detail+='首次root审核仅因R缺少173份实际S源码镜像停止，现已按精确SHA补齐并用未改审核器复算通过；无GPU重跑、无科学改动。原1212条开发记录保留，新旧合计1412；新证据只覆盖这两个方法，不宣称旧动作语义等价或Long22方法整体验收。最终0/35200封存。正常训练交控制器；下次定时监督处理空槽、余下开发与终态。[本轮收据](../'+B+'/summary.json)，[逐任务结果](正式Long128种子23开发结果.md)。\n\n'
 short=f'{stamp} 更新：50/72组训练双审通过，新增Object64 seed41两组；{len(cap["occupied"])}卡活动，累计{seconds/3600:.3f} GPU小时（非最终）。Long128 seed23新增200开发trial验收完成，A95%/B92%，配对差−3个百分点；属于100共同初态的单seed开发结果，未完成完整延迟或三seed结论。原记录和负结果保留，最终0/35200封存。[本轮收据](../{B}/summary.json)。\n\n'
 docs=[]
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式Long其余16选择器开发登记']:
  rel='docs/'+name+'.md';p=R/rel;assert rel not in inventory['files'];prior_text=p.read_text();first,tail=prior_text.split('\n',1);oldsha=h(p);p.write_text(first+'\n\n'+(detail if name=='实验进度' else short)+tail.lstrip('\n'));docs.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 lines=['# 正式Long128 seed23开发结果','',stamp+'，只记录本组固定开发面板结果。','', 'A：动作监督；B：同A增加0.1未来视觉表征MSE。两组均按已登记5000步训练与validation选模，部署128 tokens；评测10任务×10共同开发初态，chunk8、wait10、max520。未据开发结果重选checkpoint。','','| 任务ID | A成功/10 | B成功/10 | B−A百分点 |','|---|---:|---:|---:|']
 for t in range(10):
  a=ld['per_task']['A128_seed23'][str(t)]['successes'];b=ld['per_task']['B128_seed23'][str(t)]['successes'];lines.append(f'| {t} | {a} | {b} | {(b-a)*10:+d} |')
 lines+=['','合计A95/100、B92/100；B−A −3个百分点。配对：均成功91、仅A4、仅B1、均失败4。100个唯一初态，不将两方法或跨seed重复视为更多独立初态。','','同一初始观测的A/B token交集/128均值86.6328125%；后续轨迹分叉，因此不把后续异状态选择直接作配对。未来头调用0，6906次真实策略前向，54560个控制动作逐项对应chunk前缀。','','开发作业3043709完整分配3083 GPU秒（0.856389 GPU小时），包括加载与全部执行；不把内部阶段重复加到账单。完整O2A仍待同checkpoint、同执行语义测速，无加速结论。','','该seed开发组未出现B收益；不据此改变冻结方法、停止其他预登记seed或预写最终结论。旧1212条开发记录原样保留；本次新动作执行证据不证明旧结果等价。全局release和最终35200仍关闭。','','[root原始重建](../'+lr+')；[独立原始重建](../'+li+')；[机器可读逐任务/身份/成本](../'+outcome['path']+')。']
 rel='docs/正式Long128种子23开发结果.md'
 with (R/rel).open('x') as stream:stream.write('\n'.join(lines)+'\n')
 docs.append(dict(path=rel,after_sha256=h(R/rel)))
 rel='scripts/ops/formal_action_deployment_v1/README.md';p=R/rel;first,tail=p.read_text().split('\n',1);oldsha=h(p)
 p.write_text(first+'\n\nCurrent status, 2026-10-20 CST: genuine fresh Long128 seed23 development job3043709 passed root and independent raw reconstruction,200 trials over100 common initial states,A95/B92,3083 allocated GPU seconds. Exact published consumer and unchanged scientific primitives verified actual runtime, checkpoints, fixed panel and actions.173 missing control source mirrors were copied from the actual frozen snapshot at identical hashes; initial audit failure retained. This proves only these two development instances, not the remaining7 shards, old/new semantic equivalence, O2A or final release. See results/formal_main_v2/preflight/heartbeat_20261020T0632/summary.json.\n\nEarlier status paragraphs are historical snapshots.\n\n'+tail.lstrip('\n'));docs.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 op=R/B/'root_operations';op.mkdir(exist_ok=True)
 for name in ['observe_formal_2232.py','review_terminal_2232.py','pull_long_2232.py','review_long_2232.py','mirror_long_source_2232.py','review_long_2232_a2.py','archive_results_2232.py','integrate_2232.py']:
  raw=(R/'.local'/name).read_bytes();compile(raw,name,'exec')
  with (op/name).open('xb') as stream:stream.write(raw)
 with (R/B/'previous_Git_push_verified.json').open('xb') as stream:stream.write((R/'.local/github_push_2130_verified.json').read_bytes())
 save(B+'/root_integration.json',dict(status='integrated',state_before_sha256=before,state_after_sha256=h(sp),summary=summary,docs=docs,controller_and_registry_unchanged_by_integration=True,new_GPU_jobs=[],frozen_scientific_files=173,normal_gpu_realtime_polling=False))
 print(json.dumps(dict(status='integrated',root_completed=50,reviewed_updates=257000,new_development=200,all_development=1412,active_GPU_jobs=len(cap['occupied']),GPU_hours=seconds/3600,summary=summary)),flush=True)

from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1727';E='results/formal_main_v2/engineering/supervision_delivery_0927'
PACKAGES=[{"base":".local/Long_collect_terminal_independent_0927","manifest":".local/Long_collect_terminal_independent_0927/manifest.json","sha256":"419c8204df194270de3afec659673be570214de2f3d594099ffbb5ea39978245","archive":"Long_collect_terminal_independent"},{"base":".local/Git_observation_delivery_review_0927","manifest":".local/Git_observation_delivery_review_0927/manifest.json","sha256":"378abaa9a9754681b9c2ed911e3fb236ca51d06286c001ed11d0897b5375bf45","archive":"Long_observation_delivery_independent"},{"base":".local/git_delivery_review_0830","manifest":".local/git_delivery_review_0830/final_manifest.json","sha256":"096cddff1750d0f081b4100dd2d11d0127311448ae2a29c72e957d6b5759e6f6","archive":"previous_Git_delivery_independent"},{"base":".local/legacy6_typed_bridge_0927","manifest":".local/legacy6_typed_bridge_0927/manifest.json","sha256":"fb84c6cfc2f69832bb0d8ce6e0fae87e23e19645fd4a262dd9fa418fa9b9f011","archive":"Long_legacy6_typed_bridge"}]
LEGACY_REPORT={"path":".local/legacy6_typed_bridge_0927/report.json","sha256":"123d73d7a4e5622fd3048efc69058ce19b3d480c28f1ef33a874302b08ead508"}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def rd(rel,pin=None):
 p=R/rel
 if pin:assert h(p)==pin,rel
 return json.loads(p.read_bytes())
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as stream:json.dump(v,stream,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
 return ref(rel)
def clone(rel,raw):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as stream:stream.write(raw)
 return ref(rel)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('integrate0927ctl',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=rd('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 assert f['root_and_independent_completed_arms']==62 and f['root_and_independent_reviewed_arm_updates']==314000
 assert f['completed_development_trials']==2812 and f['current_action_development_trial_count']==1600 and f['current_action_development_unique_initial_states']==100
 assert f['historical_other_action_semantics_development_trials']==1212 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 rr='results/formal_main_v2/downstream_reviews/3047982.json';root=rd(rr,'45e76fbb32159d53dc7be7e5ca6b25d4d52815d44d0234063f30a69500567479')
 ir='.local/Long_collect_terminal_independent_0927/independent_review.json';ind=rd(ir,'0f324131adfc237d02c607af6728f49e58bb80f99bfd89306f0720d28527d9eb')
 assert root['status']==ind['status']=='passed' and root['scientific_complete'] and ind['scientific_complete']
 assert root['job_id']==ind['job_id']=='3047982' and root['observations']==ind['observations']==30
 assert root['completed_collection_trajectories']==ind['collection_trajectories']==10 and root['known_policy_calls']==ind['collection_policy_calls']==369
 assert ind['original_reviewer_and_consumer_both_executed'] and ind['collection_control_steps']==2917
 assert root['cost']['current_gpu_seconds']==root['cost']['all_attempt_gpu_seconds']==472
 assert not root['final_release'] and not root['final_state_values_read'] and not root['weights_read']
 allowref=ref(B+'/observation_npz_delivery_allowlist.json');allow=rd(allowref['path'],'b23a11f750ded441b0dfd1f3c066eb032c783b186e567975b34a14f0856880e1')
 npz=rd('.local/Git_observation_delivery_review_0927/typed_allowlist_review.json','17f0aa6d6e34f0b73e04fc9dd30b7a65f9221393cb63427158f102f493a609f2')
 assert npz['status']=='passed' and not npz['blockers']
 assert npz['allowlist']['sha256']==allowref['sha256'] and npz['observations']==30 and npz['total_bytes']==11839320
 assert allow['status']=='passed' and len(allow['files'])==30 and allow['total_bytes']==11839320
 for row in allow['files']:
  rel=row['path'];assert h(R/rel)==h(P/rel)==row['sha256']==root['files'][rel] and (R/rel).stat().st_size==row['bytes']==394644
 prior_collection=copy.deepcopy(f['Long_fixed_observation_collection'])
 assert prior_collection['job_id']=='3047982' and prior_collection['accepted_observations']==0
 jobs=[j for j in s['registered_jobs'] if str(j['job_id'])=='3047982'];assert len(jobs)==1
 job=jobs[0];assert h(R/job['invocation'])==h(P/job['invocation'])==job['invocation_sha256']=='4f12f98f6c7027961eb14d3de07fd27387e8f30dc4edab2490a7649b0b2109be'
 assert root['invocation_sha256']==job['invocation_sha256']
 runroot=Path(job['run_root']).relative_to(P).as_posix()
 panelref=ref(runroot+'/panel.json');assert panelref['sha256']=='d06a6d7b1c90aed765b9121ec9909fbe14c4d491c0f9d7f9c321a156bfdb1b9c'
 assert rd(panelref['path'])['content_signature']=='0287609dd3154b0aa86b9bd0325d1d702e793b7842af03a8c0cfb8c836b68392'
 deliveries=[]
 for item in PACKAGES:
  base=Path(item['base']);m=rd(item['manifest'],item['sha256']);rows=[]
  for raw in m['files']:
   row=dict(raw);p=Path(row['path'])
   if not p.is_relative_to(base):p=base/p
   assert p.is_relative_to(base) and '..' not in p.parts and not p.is_absolute()
   row['path']=p.as_posix();rows.append(row)
  rows.append(dict(path=item['manifest'],sha256=h(R/item['manifest']),bytes=(R/item['manifest']).stat().st_size))
  copies=[]
  for row in rows:
   src=R/row['path'];assert src.is_file() and not src.is_symlink() and h(src)==row['sha256'] and src.stat().st_size==row['bytes']
   assert src.suffix not in ['.pt','.pth','.bin','.safetensors','.ckpt','.pyc','.npz','.npy'] and src.stat().st_size<100*(1<<20)
   dst=E+'/'+item['archive']+'/'+Path(row['path']).relative_to(base).as_posix()
   copies.append(dict(source=row,archive=clone(dst,src.read_bytes())))
  deliveries.append(save(B+'/'+item['archive']+'_delivery.json',dict(copies=copies,source_manifest=ref(item['manifest']),no_source_transformation=True,production_modified=False,new_GPU_jobs=0)))
 canonical_ind=clone('results/formal_main_v2/downstream_reviews/3047982_independent.json',(R/ir).read_bytes())
 legacy=rd(LEGACY_REPORT['path'],LEGACY_REPORT['sha256'])
 assert legacy['status']=='author_CPU_candidate_checks_passed_not_admitted' and legacy['review_role']=='author'
 assert not legacy['reuse_authorized'] and not legacy['production_consumer_state_Git_changed'] and legacy['new_GPU_seconds']==0 and legacy['new_scientific_trials']==0
 assert legacy['coverage']['trials']==600 and legacy['coverage']['unique_initial_states']==100 and legacy['pending_original_condition']['old_instance_hash_recorded'] is False
 legacy_followup=copy.deepcopy(f['Long_legacy6_equivalence_followup'])
 legacy_followup.update(status='bounded_typed_map_author_candidate_archived_pending_root_and_independent_admission',
  author_candidate=LEGACY_REPORT,author_candidate_archive=ref(E+'/Long_legacy6_typed_bridge/'+Path(LEGACY_REPORT['path']).relative_to('.local/legacy6_typed_bridge_0927').as_posix()),
  typed_map_candidate_only=True,production_reuse_authorized=False,production_consumer_changed=False,original600_reused=False,original600_rerun=False,new_scientific_trials=0)
 assert legacy_followup['old_RNG_dump_not_registered_requirement']
 f['Long_legacy6_equivalence_followup']=legacy_followup
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])<=8
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 assert obs['rows']['3047982']['status']=='COMPLETED' and obs['rows']['3047982']['exit_code']=='0:0' and obs['rows']['3047982']['elapsed_seconds']==472
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost']['allocated_gpu_seconds']
 inventory=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():assert h(R/rel)==h(P/'snapshots/formal_main_v2_run_564be0995e'/rel)==pin
 collection=copy.deepcopy(prior_collection)
 collection.update(status='completed_root_and_independent_accepted',scheduler_status_at_snapshot='COMPLETED',accepted_observations=30,completed_collection_trajectories=10,known_policy_calls=369,actual_control_steps=2917,
  new_success_rate_trials=0,all_attempt_GPU_seconds=472,model_loading_included_in_cost=True,root_terminal_review=ref(rr),independent_terminal_review=canonical_ind,observation_panel=panelref,
  observation_panel_content_signature='0287609dd3154b0aa86b9bd0325d1d702e793b7842af03a8c0cfb8c836b68392',
  exact_NPZ_delivery_allowlist=allowref,exact_NPZ_independent_review=ref(E+'/Long_observation_delivery_independent/typed_allowlist_review.json'),
  raw_observation_bytes=11839320,collection_cost_is_not_O2A_latency=True,no_outcome_based_observation_selection=True,
  previous_submission_stage_record=prior_collection,full_latency_executed=False,components_executed=False,final_opened=False)
 acceptance=save(B+'/Long_observation_collection_acceptance.json',dict(schema='formal_main_v2',status='root_and_independent_accepted',collection=collection,
  control_steps_per_task=[380,249,242,220,260,148,200,269,429,520],first_indices=[0]*10,middle_indices=[189,124,120,109,129,73,99,134,214,259],
  last_indices=[379,248,241,219,259,147,199,268,428,519],initialization_source_indices=[0,4,7,3,6,2,3,6,8,2],
  root_and_independent_reports_distinct=True,known_review_script_key_error_retained=True,new_scientific_success_rate_trials=0,full_latency_executed=False,component_latency_executed=False,sealed_final_trials=0))
 f['Long_fixed_observation_collection']=collection
 s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 next_actions=['Leave healthy5000-step automatictraining to the registered controller; no normalGPU real-time polling. Review terminal artifacts at next scheduledheartbeat.',
 'Preserve accepted Long fixed30 rawdevelopmentobservations and original collector/action/Slurm traces via P-to-R-to-GitHub exactNPZ allowlist; collection adds no success-rate trials or latency result.',
 'Bounded root and independent admission of archived legacyLong600 typed-map author candidate against original controller/environment identity requirements. Installation/factory provenance is not a historical instance-hash measurement; no added fullRNGdump gate. No reuse or blindrerun before admission.',
 'Finish remaining10 trainingarms and other suite development under unchanged gates. Preserve Long128 negatives and every seed. Currentaction1600trials share100initialstates;historical1212separate.',
 'FullO2A/components stay behind existing88identity/foursuite developmentfreeze. Final35200 need72checkpoints+16refs+all devreceipts+rootrelease. No sealedvalues or scopeexpansion.']
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='scheduled_supervision_Long_fixed_development_observation_collection_acceptance',utc=now,
  root_independent_complete=62,total_arms=72,completed_by_suite={'libero_10':18,'libero_spatial':16,'libero_object':16,'libero_goal':12},
  new_completed_training_groups=0,root_independent_updates=314000,new_reviewed_arm_updates=0,new_development_trials_accepted=0,
  all_historical_and_new_development_trials=2812,current_action_development_trials=1600,current_action_unique_initial_states=100,historical_other_action_trials_not_pooled=1212,
  Long_collection=collection,collection_acceptance=acceptance,collection_GPU_seconds=472,collection_GPU_hours=472/3600,
  collection_cost_already_in_registered_ledger_not_added_again=True,independent_and_author_deliveries=deliveries,Long_legacy6_typed_bridge_author_candidate=legacy_followup,
  new_GPU_submissions_by_root=[],new_duplicate_submissions=0,scheduler=obs,capacity=cap,active_GPU_jobs=len(cap['occupied']),reserved_GPU_slots=0,
  allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,cost_is_final=False,completed_final_trials=0,expected_final_trials=35200,
  final_sealed=True,normal_training_left_to_controller=True,server_only=True,scientific_files_unchanged=173,next=next_actions))
 f['latest_incremental_review']=summary;f['incremental_review_history'].append(summary)
 f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied'])
 f['parallel_execution']['actual_running_allocated_GPUs']=sum(obs['rows'][x]['gpus'] for x in cap['occupied'] if obs['rows'][x]['status']=='RUNNING')
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']='2026-10-20'
 s['current_work']=f'62/72traininggroups root+independentcomplete (Long18 Spatial16 Object16 Goal12);314000reviewedupdates. Long fixed30developmentobservations from10Dense trajectories3047982 root+independentaccepted;472GPU seconds,369policycalls,2917controlsteps. No new success-rate trials or O2A. Currentaction1600trials/100uniqueinitialstates;old1212separate. Legacy600 typed-map authorcandidate archived,not productionadmitted/rerun. {len(cap["occupied"])}activeGPU,{seconds/3600:.3f}GPUh;final0/35200sealed.'
 s['next_actions']=next_actions;s['next_allowed_action']=next_actions[0]
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 assert f['completed_training_pairs']==old['formal_main_progress']['completed_training_pairs'] and f['new_action_development_verified_by_job']==old['formal_main_progress']['new_action_development_verified_by_job']
 c.atomic_json(sp,s,before)
 longtext=f'{stamp}：训练 **62/72组通过root与独立复核**（Long18、Spatial16、Object16、Goal12），314000已审臂更新；本轮无新增训练或成功率结果。当前{len(cap["occupied"])}卡运行，累计 **{seconds/3600:.3f} GPU小时**（全部登记分配，包含失败与运行中作业，非最终）。正常训练交自动控制器。\n\n'
 longtext+='Long采集3047982完成双审：原10任务各一条预登记Dense开发轨迹，按实际首、中、末保留30观测，共11,839,320字节，没有按成功率筛换。两路图像和当前机器人状态按精确路径、SHA和数组格式放行到GitHub。369次动作chunk、2917控制步，完整分配472GPU秒（0.131小时，含加载）；已计入总账，不重复累加，不是O2A延迟。\n\n'
 longtext+='采集不增加成功率分母：当前动作语义仍1600条开发试验、100唯一初态，历史1212另列。完整测速及分项计时未运行，遵守原88身份与四套件开发冻结。旧Long600复用映射仅归档作者候选，生产准入仍需root及独审；历史安装/工厂来源不冒称当时实例哈希测量，不新增旧完整RNG dump门槛。旧600未复用或重跑，最终0/35200封存，173科学文件不变。\n\n'
 longtext+=f'[本轮证据](../{B}/summary.json)，[观测验收](正式Long测速观测验收.md)。\n\n'
 short=f'{stamp}：62/72训练组双审完成，{len(cap["occupied"])}卡运行，累计{seconds/3600:.3f}GPU小时（非最终）。Long固定10条采集轨迹、30观测双审通过，472GPU秒已计总账；无新增成功率或O2A结果。旧600复用映射仅作者候选，未准入或重跑。最终0/35200封存。见[观测验收](正式Long测速观测验收.md)及[本轮证据](../{B}/summary.json)。\n\n'
 docs=[];updates={name:(longtext if name=='实验进度' else short) for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记']}
 updates['正式Long固定测速观测采集登记']=f'{stamp}验收：3047982通过root及独审，**10条开发采集轨迹、30观测全部验收**，固定来源与首中末规则不变。成本472GPU秒；不计入成功率分母或推理延迟。O2A及分项计时未运行。[验收记录](正式Long测速观测验收.md)。\n\n'
 for name,addition in updates.items():
  rel='docs/'+name+'.md';assert rel not in inventory['files'];p=R/rel;oldsha=h(p);first,tail=p.read_text().split('\n',1);p.write_text(first+'\n\n'+addition+tail.lstrip('\n'));docs.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 report='# Long 固定测速观测验收\n\n'+longtext
 report+='## 固定来源与实际轨迹覆盖\n\n每任务取原开发面板最小source_state_index。环境seed0、运行seed17、等待10步、chunk8、上限520控制步。等待后、执行动作前采集；middle=floor((N−1)/2)，无补帧或结果筛选。\n\n| task | 开发初态索引 | 实际控制步N | 首 | 中 | 末 |\n|---:|---:|---:|---:|---:|---:|\n'
 for i,(idx,n) in enumerate(zip([0,4,7,3,6,2,3,6,8,2],[380,249,242,220,260,148,200,269,429,520])):report+=f'| {i} | {idx} | {n} | 0 | {(n-1)//2} | {n-1} |\n'
 report+='\n## 内容与复查\n\n每个NPZ恰含两路256×256×3 uint8图像，float64当前位置(3)、姿态四元数(4)、夹爪状态(2)，各394,644字节；allow_pickle=False，无object数组、额外ZIP成员或封存模拟器初态。官方Long基座revision 95220f9a3421a7ff12d4218e73d09ade830fa9a3，Dense512，无未来头。panel签名0287609dd3154b0aa86b9bd0325d1d702e793b7842af03a8c0cfb8c836b68392。\n\n'
 report+=f'[原panel](../{runroot}/panel.json)、[root审核](../{rr})、[独立审核](../{canonical_ind["path"]})、[精确文件清单](../{allowref["path"]})、[NPZ内容独审](../{collection["exact_NPZ_independent_review"]["path"]})。\n\n'
 report+='472GPU秒包括整个Slurm分配，不是策略调用均值延迟。正式O2A仍需同checkpoint、每实例50次预热、面板20轮、随机平衡顺序和共同计时边界。此次不产生加速比或成功率—延迟结论。审计脚本一次元数据字段名修正及失败原件保留，采集内容不变。\n'
 newdoc='docs/正式Long测速观测验收.md';clone(newdoc,report.encode());docs.append(dict(path=newdoc,before_sha256=None,after_sha256=h(R/newdoc)))
 for name in ['observe_formal_0927.py','pull_terminal_0927.py','review_Long_collect_3047982_0927.py','verify_Long_observation_npz_delivery_0927.py','integrate_0927.py']:
  raw=(R/'.local'/name).read_bytes();compile(raw,name,'exec');clone(B+'/root_operations/'+name,raw)
 clone(B+'/previous_Git_push_verified.json',(R/'.local/github_push_0830_verified.json').read_bytes())
 save(B+'/root_integration.json',dict(status='integrated',state_before_sha256=before,state_after_sha256=h(sp),summary=summary,docs=docs,controller_and_registry_unchanged_by_integration=True,
  training_acceptances_unchanged=True,new_GPU_jobs=[],accepted_collection_observations=30,new_success_rate_trials=0,frozen_scientific_files=173,normal_GPU_realtime_polling=False))
 print(json.dumps(dict(status='integrated',root_completed=62,new_observations=30,new_success_rate_trials=0,active_GPU_jobs=len(cap['occupied']),GPU_hours=seconds/3600,summary=summary)),flush=True)

from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1832';E='results/formal_main_v2/engineering/supervision_delivery_1032'
STATS_REF={"path":"results/formal_main_v2/preflight/heartbeat_20261020T1832/Long22_development_statistics.json","sha256":"35557e76c338ec0cb12f5dbb5b1871dc04d0ad3a8a807134b1ef320728c3abf1"}
INDEPENDENT_STATS={"path":".local/Long22_statistics_independent_1032/independent_review.json","sha256":"47c5c52c0d57140f414a4af229536144c078fed0c3d924c4e97cdd037aa06f43"}
PACKAGES=[{"base":".local/Long22_statistics_independent_1032","manifest":"manifest.json","sha256":"f4d7ad999f650a4ca521d2c44cfe83213d4a1102eabed64f871080708f5f891d","archive":"Long22_statistics_independent"},{"base":".local/git_delivery_review_0927","manifest":"final_manifest.json","sha256":"7b239e0b03430e58da0584be27f37c44ddc0bd5e295c2a5658498c9192e96069","archive":"previous_Git_delivery_independent"}]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def rd(rel,pin=None):
 if pin:assert h(R/rel)==pin,rel
 return json.loads((R/rel).read_bytes())
def clone(rel,raw):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw)
 return ref(rel)
def save(rel,x):return clone(rel,(json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('integrate1032ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state_path=R/'results/experiment_supervisor/state.json';before=h(state_path);s=rd('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 assert f['root_and_independent_completed_arms']==62 and f['root_and_independent_reviewed_arm_updates']==314000
 assert f['completed_development_trials']==2812 and f['current_action_development_trial_count']==1600 and f['current_action_development_unique_initial_states']==100
 assert f['historical_other_action_semantics_development_trials']==1212 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 stat=rd(STATS_REF['path'],STATS_REF['sha256']);ind=rd(INDEPENDENT_STATS['path'],INDEPENDENT_STATS['sha256'])
 assert ind['status']=='passed' and ind['root_statistics_ref']==STATS_REF
 assert ind['counts']['trials']==2200 and ind['counts']['unique_initial_state_clusters']==100 and ind['development_GPU_seconds_counted_once']==35408
 proofref=stat['legacy_compatibility_proof'];proof=rd(proofref['path'],proofref['sha256'])
 assert stat['total_development_trials']==2200 and stat['current_wrapper_actual_trials']==1600 and stat['legacy_equivalent_trials']==600
 assert proof['status']=='real_bound_adoptions_and_legacy_evidence_verified' and proof['legacy_equivalent_trials']==600 and not proof['final_release']
 assert not proof['original_invocations_ran_new_wrapper'] and proof['new_GPU_seconds']==0 and not proof['old_latency_reused']
 deliveries=[]
 for item in PACKAGES:
  base=Path(item['base']);mp=base/item['manifest'];m=rd(mp.as_posix(),item['sha256']);rows=[]
  for raw in m['files']:
   row=dict(raw);p=Path(row['path'])
   if not p.is_relative_to(base):p=base/p
   assert p.is_relative_to(base) and '..' not in p.parts and not p.is_absolute()
   row['path']=p.as_posix();rows.append(row)
  rows.append(dict(path=mp.as_posix(),sha256=h(R/mp),bytes=(R/mp).stat().st_size));copies=[]
  for row in rows:
   src=R/row['path'];assert src.is_file() and not src.is_symlink() and h(src)==row['sha256'] and src.stat().st_size==row['bytes']
   assert src.suffix not in ['.pt','.pth','.bin','.safetensors','.ckpt','.pyc','.npz','.npy'] and src.stat().st_size<100*(1<<20)
   dst=E+'/'+item['archive']+'/'+Path(row['path']).relative_to(base).as_posix()
   copies.append(dict(source=row,archive=clone(dst,src.read_bytes())))
  deliveries.append(save(B+'/'+item['archive']+'_delivery.json',dict(source_manifest=ref(mp.as_posix()),copies=copies,no_source_transformation=True,new_GPU_jobs=0)))
 for name in ['long22_stats_1032.py','integrate_1032.py']:
  clone(B+'/root_operations/'+name,(R/'.local'/name).read_bytes())
 acceptance=save(B+'/Long22_development_root_acceptance.json',dict(schema='formal_main_v2',status='root_and_independent_statistics_accepted',
  root_statistics=STATS_REF,independent_statistics=ref(E+'/Long22_statistics_independent/independent_review.json'),legacy_compatibility_proof=proofref,methods=22,
  unique_initial_state_clusters=100,compatible_development_trials=2200,current_wrapper_actual_trials=1600,legacy_equivalent_trials=600,
  newly_executed_trials=0,new_GPU_jobs=0,old_legacy_cost_already_counted=True,old_execution_version_preserved=True,
  general_global_consumer_hook_enabled=False,full_latency_executed=False,final_release=False,final_state_values_read=False))
 prior=copy.deepcopy(f['Long_legacy6_equivalence_followup'])
 follow=copy.deepcopy(prior);follow.update(status='root_independent_accepted_and_explicit_CPU_proof_exercised',prior_candidate_stage=prior,
  root_acceptance=acceptance,real_development_compatibility_proof=proofref,production_reuse_authorized=True,
  reuse_scope='Exact600 in Long22 development statistics only; all88/foursuite/global-release consumers unchanged.',
  production_general_consumer_hook_enabled=False,production_consumer_changed=False,original600_reused=True,original600_rerun=False,
  new_scientific_trials=0,actual_new_wrapper_trials_added=0,typed_map_candidate_only=False,
  original_typed_map_bytes_preserved=True,old_RNG_dump_not_registered_requirement=True)
 f['Long_legacy6_equivalence_followup']=follow
 f['Long22_development_statistics']=dict(status='root_independent_accepted',acceptance=acceptance,statistics=STATS_REF,
  independent_statistics=ref(E+'/Long22_statistics_independent/independent_review.json'),methods=22,total_trials=2200,actual_new_wrapper_trials=1600,explicit_legacy_equivalent_trials=600,
  unique_initial_state_clusters=100,all_original_development_trials=2812,original_historical_version_trials=1212,other_historical_not_admitted=612,
  budgets={k:{field:v[field] for field in ['mean_A','mean_B','mean_B_minus_A','CI95_B_minus_A']} for k,v in stat['budgets'].items()},
  all_seeds_preserved=True,no_new_scientific_trials=True,no_full_latency_or_final_conclusion=True,final_release=False)
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])<=8
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost']['allocated_gpu_seconds']
 inventory=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():assert h(R/rel)==h(P/'snapshots/formal_main_v2_run_564be0995e'/rel)==pin
 s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 next_actions=['Leave the healthy controller and registered training jobs running to5000; no repeated normal-job polling.',
 'Use the accepted explicit Long600 compatibility proof together with actual1600 current-wrapper results only for Long development. Preserve exact archive path mapping and genuine original execution versions; global consumer hook remains separate.',
 'Prepare and audit existing registered nonLong development entrypoints and ready checkpoint identities to use available GPU slots without changing scientific gates. No implicit new job submission.',
 'Finish remaining10 training arms and all four suites development. FullO2A/components still need the original88identity/four-suite freeze; final35200 need72checkpoints+16refs+all devreceipts+rootrelease.',
 'Report Long128 negative development contrast and both other-budget intervals with all seeds; no final or measured-speed frontier inference. No search or scope expansion.']
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='scheduled_supervision_Long600_equivalence_and_Long22_development_acceptance',utc=now,
  root_independent_complete=62,total_arms=72,completed_by_suite={'libero_10':18,'libero_spatial':16,'libero_object':16,'libero_goal':12},
  root_independent_updates=314000,new_completed_training_groups=0,new_reviewed_arm_updates=0,
  new_development_trials_executed=0,all_raw_development_trials=2812,current_wrapper_actual_trials=1600,
  original_historical_version_trials=1212,Long_legacy_equivalent_trials_accepted=600,Long_compatible_development_trials=2200,
  unique_initial_state_clusters=100,Long_development_acceptance=acceptance,Long_statistics=STATS_REF,legacy_equivalence_proof=proofref,
  new_GPU_submissions_by_root=[],new_duplicate_submissions=0,scheduler=obs,capacity=cap,active_GPU_jobs=len(cap['occupied']),reserved_GPU_slots=0,
  allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,cost_is_final=False,legacy10531_GPU_seconds_not_added_again=True,
  completed_final_trials=0,expected_final_trials=35200,final_sealed=True,normal_training_left_to_controller=True,server_only=True,
  scientific_files_unchanged=173,additional_deliveries=deliveries,next=next_actions))
 f['latest_incremental_review']=summary;f['incremental_review_history'].append(summary)
 f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied'])
 f['parallel_execution']['actual_running_allocated_GPUs']=sum(obs['rows'][x]['gpus'] for x in cap['occupied'] if obs['rows'][x]['status']=='RUNNING')
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']='2026-10-20'
 s['current_work']=f'62/72 training groups root+independent complete;314000 reviewed arm updates. Long explicit legacy600 equivalence accepted with genuine old identity, no rerun; Long22 development2200 trials on100 unique states =1600 actual current-wrapper+600 legacy-equivalent. Original2812 raw trials retained. {len(cap["occupied"])} activeGPU,{seconds/3600:.3f}GPUh. Global88/four-suite timing and finalrelease gates unchanged; final0/35200sealed.'
 s['next_actions']=next_actions;s['next_allowed_action']=next_actions[0]
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 assert f['completed_training_pairs']==old['formal_main_progress']['completed_training_pairs'] and f['new_action_development_verified_by_job']==old['formal_main_progress']['new_action_development_verified_by_job']
 c.atomic_json(state_path,s,before)
 table='| 总tokens | A三seed均值 | B三seed均值 | B−A | 95%配对区间 |\n|---:|---:|---:|---:|---:|\n'
 for k in ['256','128','64']:
  v=stat['budgets'][k];ci=v['CI95_B_minus_A']
  table+=f'| {k} | {v["mean_A"]*100:.2f}% | {v["mean_B"]*100:.2f}% | {v["mean_B_minus_A"]*100:+.2f}pp | [{ci[0]*100:.2f}, {ci[1]*100:.2f}]pp |\n'
 text=f'{stamp}：训练 **62/72组双审完成**（Long18、Spatial16、Object16、Goal12），{len(cap["occupied"])}卡运行，累计 **{seconds/3600:.3f} GPU小时**（全部登记分配，非最终）。本轮没有新GPU作业。\n\n'
 text+='Long旧600通过root与独立来源/动作审查，并由新显式CPU证明入口实际验收，无需重跑。旧执行版本保留；不冒称历史实例哈希捕获，10531GPU秒早已计账。Long全部22个部署实例的开发结果现可汇总：**1600条新版实际执行＋600条旧版等价证明＝2200条，仍只有100个唯一初态**。原2812条历史与新记录全部保留，另612条历史记录未因此准入。\n\n'
 text+=table+'\n主预算128的均值为负；256与64的区间跨零，不能据此声称稳定收益或等效。Dense94%；均匀256/128/64为91%/77%/39%，均各100条共享参考，不复制为三seed。以上全部是开发结果，无O2A实测加速结论。\n\n'
 text+='正常训练交自动控制器；下一步准备其他套件已验收组的并行开发任务。全局consumer接入、88身份/四套件冻结、完整O2A与最终release仍未完成；最终0/35200封存，173科学文件不变。\n\n'
 text+=f'[本轮证据](../{B}/summary.json)，[Long完整开发汇总](正式Long完整开发结果.md)。\n\n'
 short=f'{stamp}：62/72训练组双审完成，{len(cap["occupied"])}卡运行，累计{seconds/3600:.3f}GPU小时。Long旧600显式等价证明通过，22个部署实例的2200条开发记录齐备（100唯一初态），无新增GPU试验。主预算128均值B−A为{stat["budgets"]["128"]["mean_B_minus_A"]*100:+.2f}pp，保留负结果；测速及最终结论尚未完成。见[完整开发汇总](正式Long完整开发结果.md)及[本轮证据](../{B}/summary.json)。\n\n'
 docs=[]
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记']:
  rel='docs/'+name+'.md';assert rel not in inventory['files'];p=R/rel;prior=h(p);first,tail=p.read_text().split('\n',1);p.write_text(first+'\n\n'+(text if name=='实验进度' else short)+tail.lstrip('\n'));docs.append(dict(path=rel,before_sha256=prior,after_sha256=h(p)))
 report='# Long 完整开发结果\n\n'+text+'## 逐种子结果\n\n| 总tokens | seed | A成功率 | B成功率 | B−A |\n|---:|---:|---:|---:|---:|\n'
 for k in ['256','128','64']:
  for seed,v in stat['budgets'][k]['per_seed'].items():report+=f'| {k} | {seed} | {v["A_rate"]*100:.0f}% | {v["B_rate"]*100:.0f}% | {v["B_minus_A"]*100:+.0f}pp |\n'
 report+='\n## 证据与统计范围\n\nLong开发历史分配共35,408GPU秒（9.836小时），已含在项目总账，本轮不重复加算。任务内初态为簇，每次抽样携带完整三seed；10任务等权、每任务10开发初态，bootstrap10000次，seed20261016，95%百分位区间。报告seed标准差ddof=1，未把重复seed算作新初态。逐任务成功数、A/B配对不一致计数、对Dense/均匀的差值及区间见原始统计JSON。旧600的每条映射绑定原始chunk/执行动作、checkpoint、初态、执行版本及真实Slurm成本；新API无future头、模拟器重放、GPU提交或final授权。\n\n'
 report+=f'[统计原件](../{STATS_REF["path"]})、[独立统计验收](../{E}/Long22_statistics_independent/independent_review.json)、[逐初态向量](../{stat["paired_states"]["path"]})、[全部bootstrap抽样结果](../{stat["bootstrap_draws"]["path"]})、[旧600显式证明](../{proofref["path"]})。\n\n'
 report+='此前未能证实历史源码连续性的审计保留；本轮用安装包全量字节与早于旧作业的inode ctime补足来源连续性，推断范围按普通文件系统语义明确登记。没有将来源推断写成旧运行时实例测量。新显式接口当前仅用于这600条开发证明；通用全局冻结消费者未被改写。所有结果仍须遵守最终冻结与评测规则。\n'
 clone('docs/正式Long完整开发结果.md',report.encode());docs.append(dict(path='docs/正式Long完整开发结果.md',after_sha256=h(R/'docs/正式Long完整开发结果.md')))
 save(B+'/root_integration.json',dict(status='integrated',state_before_sha256=before,state_after_sha256=h(state_path),summary=summary,docs=docs,
  controller_and_registry_unchanged_by_integration=True,new_GPU_jobs=[],new_scientific_trials=0,legacy600_proof_exercised=True,Long_development_trials=2200,unique_initial_states=100,
  frozen_scientific_files=173,global_consumer_not_modified=True,final_release=False))
 print(json.dumps(dict(status='integrated',root_completed=62,Long_development_trials=2200,active_GPU_jobs=len(cap['occupied']),GPU_hours=seconds/3600,summary=summary)),flush=True)

from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261019T1743'
D='results/formal_main_v2/execution/action_spatial_resume_0943'
ARCH='results/formal_main_v2/engineering/terminal_delivery_0943'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def read(rel):return json.loads((R/rel).read_bytes())
def write(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 raw=(json.dumps(v,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode()
 if p.exists():assert p.read_bytes()==raw
 else:
  with p.open('xb') as f:f.write(raw)
 return ref(rel)
def cp(src,dst,pin=None):
 a=R/src;b=R/dst
 actual=h(a);assert pin is None or actual==pin
 b.parent.mkdir(parents=True,exist_ok=True)
 if b.exists():assert h(b)==actual
 else:
  with b.open('xb') as f:f.write(a.read_bytes())
 return dict(source=src,archive=ref(dst),bytes=a.stat().st_size)
cpn=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert h(cpn)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('root_integrate0943c',cpn);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 old=c.file_sha(R/'results/experiment_supervisor/state.json');s=c.read_json(R/'results/experiment_supervisor/state.json');before=copy.deepcopy(s)
 assert s['pending_submission'] is None
 assert s['autonomous_training_v1']['reserved_GPU_slots']==1 and s['autonomous_training_v1']['reservation_root_record']==ref(D+'/reservation_root_record.json')
 manifest='.local/cuda_recovery_independent_0943/delivery_files.json';assert h(R/manifest)=='7862e2f4458a278511543945e96229b0a3dbaab11e535ac9f7c0b4a05bb4a996'
 files=read(manifest)['files']
 if isinstance(files,dict):files=[dict(path=k,**v) for k,v in files.items()]
 origins=[]
 for row in files:
  name=row['path'];src=name if name.startswith('.local/') else '.local/cuda_recovery_independent_0943/'+name
  assert (R/src).parent==R/'.local/cuda_recovery_independent_0943'
  assert (R/src).stat().st_size==row['bytes']
  origins.append(cp(src,ARCH+'/independent/'+Path(name).name,row['sha256']))
 origins.append(cp(manifest,ARCH+'/independent/delivery_files.json'))
 for f in sorted((R/'.local/cuda_terminal_review_0943').iterdir()):
  if f.is_file():origins.append(cp(str(f.relative_to(R)),ARCH+'/reviewer/'+f.name))
 for f in sorted((R/'.local').glob('*0943*.py')):
  if f.is_file():origins.append(cp(str(f.relative_to(R)),ARCH+'/root_operations/'+f.name))
 write(B+'/terminal_archive_origin_map_v2.json',dict(schema='formal_main_v2',files=origins,originals_retained=True,rebuildable_fixtures_excluded=True))
 pairs=s['formal_main_progress']['completed_training_pairs']
 normalroot='results/formal_main_v2/libero_object/k256/seed41/training/segment_reviews/3034570.json'
 assert h(R/normalroot)=='373c593c00752655b94cd02d51789716e292d78310149753b475532daf78c545'
 nr=read(normalroot);assert nr['completed_by_arm']=={'A':5000,'B':5000}
 normalind='results/formal_main_v2/libero_object/k256/seed41/training/segment_reviews/3034570_independent.json'
 cp('.local/cuda_recovery_independent_0943/3034570_independent_review.json',normalind,'b1e96f4b174b7b7208ac1bf90312cc0d88b04c64823784c46538187a9ff58ec5')
 ni=read(normalind);assert ni['status']=='passed_complete_training_only' and ni['root_review']==ref(normalroot)
 selected=read(B+'/3034570_selected_server.json');checks=[];selection=[]
 for row in selected['checks']:
  arm=row['arm'];dep=f'results/formal_main_v2/libero_object/k256/seed41/training/{arm}/deployment_receipt.json';dv=read(dep)
  v=min(dv['evaluations'],key=lambda x:(x['validation_metric'],x['update']))
  assert dv['checkpoint_sha256']==row['sha256']==ni['arms'][arm]['best_sha256']
  assert dv['metadata']['update']==v['update'] and dv['metadata']['validation_metric']==v['validation_metric']
  assert v['update']==ni['arms'][arm]['earliest_selected_update'] and v['validation_metric']==ni['arms'][arm]['selected_teacher_l1']
  new=dict(row);new.update(selected_update=v['update'],validation_metric=v['validation_metric'],metadata_source=ref(dep));checks.append(new)
  selection.append(dict(arm=arm,path=row['path'],expected_sha256=row['sha256'],selected_update=v['update'],validation_metric=v['validation_metric']))
 sr=write(B+'/3034570_selected_binding.json',dict(status='verified_actual_server_bytes_bound_to_validated_metadata',job_id='3034570',checks=checks,
  actual_server_probe=ref(B+'/3034570_selected_server.json'),root_review=ref(normalroot),independent_review=ref(normalind),
  no_checkpoint_tensor_deserialized=True,weights_copied=False,original_null_metadata_fields_preserved=True,candidate_and_deployment_hashes_not_assumed_equal=True))
 entry=pairs['libero_object_k256_seed41'];assert not entry.get('root_review') and 'machine_verification' in entry
 entry.update(job_id='3034570',suite='libero_object',visual_tokens=256,seed=41,trained_arms=2,
  verification_kind='machine_automatic_plus_root_and_independent_raw_reconstruction',root_review=normalroot,root_review_sha256=h(R/normalroot),
  independent_review=normalind,independent_review_sha256=h(R/normalind),selected_server_review=sr['path'],selected_server_review_sha256=sr['sha256'],selected_checkpoints=selection,allowed_next_segment_end=None)
 cr='results/formal_main_v2/libero_object/k256/seed23/training/segment_reviews/3039258.json'
 assert h(R/cr)=='57192346c2b8e7010538a9798d6215c5605468b0e2c68c2873a7d2ea92f48d71'
 ci='results/formal_main_v2/libero_object/k256/seed23/training/segment_reviews/3039258_independent.json'
 cp('.local/cuda_recovery_independent_0943/independent_review.json',ci,'d94d20c293a556836ffd8b09c7cca80627ceefb13d1a22da0f9f28ed47105f1a')
 cv=read(ci);assert cv['status']=='passed_original_target_recovery_only' and cv['root_review']==ref(cr)
 assert cv['continuous5000_admission_authorized'] is False
 p=s['formal_main_progress']
 assert p['root_and_independent_reviewed_arm_updates']==221000
 assert not any(str(x.get('job_id'))=='3039258' for x in p['completed_engineering_segments'])
 p['completed_engineering_segments'].append(dict(job_id='3039258',suite='libero_object',visual_tokens=256,seed=23,
  updates_by_arm={'A':500,'B':500},status='passed_root_and_independent_original_target_recovery',not_completed_formal_training=True,
  root_review=cr,root_review_sha256=h(R/cr),independent_review=ci,independent_review_sha256=h(R/ci),
  allocated_gpu_seconds=6512,pair_allocated_gpu_seconds_including_retained_failure=6596,automatic_continuous_admission=False))
 p['root_and_independent_reviewed_arm_updates']=231000
 p['root_and_independent_completed_arms']=sum(2 for v in pairs.values() if v.get('root_review') and v.get('independent_review'))
 assert p['root_and_independent_completed_arms']==44
 issue=p['CUDA_startup_issue'];issue['original_target_recovery_3039258']=dict(status='passed_root_and_independent_original500_only',root=ref(cr),independent=ref(ci),original_FAILED_job_id='3028460',
  original_failed_GPU_seconds=84,successful_recovery_GPU_seconds=6512,continuous5000_admission=False,original_failure_had_checkpoint=False)
 issue['next']='Versioned separately reviewed autonomous5000 admission for recovered Object256 seed23; retain controller blocked history. Other two original-target recoveries remain unsubmitted.'
 for item in issue['single_recovery_authorizations']:
  if item['failed_job_id']=='3028460':item.update(status='original_target500_root_independent_passed_continuous_admission_pending',root_terminal_review=ref(cr),independent_terminal_review=ref(ci))
 for item in p['parallel_execution'].get('awaiting_terminal_review',[]):
  if str(item.get('job_id'))=='3028460':item.update(status='FAILED_retained_recovery3039258_original500_passed_continuous5000_admission_pending')
 p['first_spatial_development'].update(status='first12_preserved_remaining588_readiness_passed_waiting_reserved_GPU_slot',
  continuation_authorization=ref(D+'/submission_authorization.json'),continuation_readiness=ref(D+'/runtime_readiness.json'),
  continuation_reservation=ref(D+'/reservation_root_record.json'),next='At next scheduled supervision reconcile exact gateway pending/registry and capacity; if free submit exact single approved development request. Preserve12; append588 only. No O2A/final release.',
  next_stop_after=None)
 p['downstream_asset_consumer_integration']['latest_exact_development_readiness']=ref(D+'/runtime_readiness.json')
 p['downstream_asset_consumer_integration']['new_actual_GPU_runtime_chain_verified']=False
 cost=read(B+'/spatial_slot_reservation_activation.json')
 snapshot='results/formal_main_v2/nonweight_archives/v1/snapshots/completed_training_20261019_0943_union23.json'
 assert h(R/snapshot)=='4af1f5375d8e79bf567aeb5e68e1b4ed28b52bce5dd77e6a65623e17be70abb2'
 now=datetime.now(timezone.utc).isoformat()
 summary=dict(schema='formal_main_v2',kind='root_heartbeat_supervision_summary',utc=now,status='healthy_training_controller_active_exception_reviews_delivered',
  root_and_independent_completed_arms=44,total_arms=72,completed_by_suite={'libero_10':18,'libero_spatial':16,'libero_object':8,'libero_goal':2},
  root_and_independent_reviewed_arm_updates=231000,new_reviewed_arm_updates=10000,newly_completed_arms=2,
  completed_pair=dict(pair='libero_object_k256_seed41',root=ref(normalroot),independent=ref(normalind),selected_binding=sr),
  cuda_original_target_recovery=issue['original_target_recovery_3039258'],
  occupied_GPU_jobs_snapshot=8,cost_snapshot_utc=cost['utc'],allocated_GPU_hours_snapshot=cost['allocated_GPU_hours_snapshot'],GPU_cost_final=False,
  spatial_remaining_development=dict(original_terminal_trials_preserved=12,maximum_new_trials=588,authorization=ref(D+'/submission_authorization.json'),
    reservation=ref(D+'/reservation_root_record.json'),actual_check_only=ref(B+'/spatial_actual_check_only.json'),new_trials_completed=0,submitted=False,actual_GPU_runtime_chain_verified=False),
  completed_development_trials_unchanged=1212,completed_final_trials=0,expected_final_trials=35200,final_sealed=True,
  mixed_old_prefix_O2A_and_global_freeze_blocked=True,nonweight_archive=ref(snapshot),raw_files=23,raw_bytes=859375546,
  count_correction=ref(B+'/initial_observation_count_correction.json'),
  normal_training_GPU_submissions_by_root=0,scientific_settings_changed=False,source173_unchanged=True,server_only=True,
  next=['Scheduled capacity recheck and exact Spatial588 request; no ongoing polling','Separately reviewed recovered-pair continuous admission and two remaining bounded recoveries','Continue normal controller auto5000 and root terminal result deliveries'])
 summaryref=write(B+'/summary.json',summary)
 p['latest_completed_pairs_independent_delivery']=summaryref
 p['latest_incremental_review']=summaryref;p['incremental_review_history'].append(summaryref)
 p['nonweight_archive_preparation_20261019_0943']=dict(snapshot=ref(snapshot),files=23,raw_bytes=859375546,server_originals_retained=True,index_guard_pending=True)
 s['last_root_supervision_snapshot']=summaryref;s['last_supervision_utc']=now
 s['updated_utc']=now;s['updated_date']='2026-10-19'
 s['current_work']='44/72 root+independently verified; controller runs8 normal GPU jobs; Spatial588 exact development request reserved awaiting slot; CUDA3039258 original500 passed, continuous admission pending.'
 s['next_actions']=summary['next']
 assert s['autonomous_training_v1']==before['autonomous_training_v1']
 assert s['registered_jobs']==before['registered_jobs']
 assert p['completed_final_trials']==0 and not p['test_opened'] and not p['global_release_created']
 c.atomic_json(R/'results/experiment_supervisor/state.json',s,old)
 general='2026-10-19 18:20 本轮验收：完整训练 **44/72组**（Long18、Spatial16、Object8、Goal2），新增Object256 seed41 A/B各5000步通过root与独立原始证据复算；累计已审231000次臂更新。3039258的Object256 seed23 A/B各完成原定500步，旧FAILED及84 GPU秒保留，恢复6512 GPU秒；只验收原目标，不计入5000完成量，控制器异常阻断暂不解除。\n\n18:12 CST真实Slurm快照仍8个正常训练GPU，控制器owner/lease一致、无pending或重复pair，累计 **333.972778 GPU小时**（含失败与运行中，非最终账单）。Spatial原开发组12条保留，只追加剩余588条的具体计划及新执行版本通过双审，专属未来1槽已登记；实际check-only因8槽全满拒绝，尚未提交，也无新trial。正常训练不取消，按下一次定时监督推进。\n\n新整链尚未实际GPU运行；旧/新动作语义的结果等价尚未证明，混合旧前缀的O2A、全局冻结及最终评测仍关闭。原1212开发记录（含Object原1条policy_error）全部保留，不重跑改分母；最终0/35200封存。23份终态非权重raw共859375546字节已无损压缩并复原，原文与所有权重留服务器，Git交付另由暂存区校验确认。[本轮凭据](../results/formal_main_v2/preflight/heartbeat_20261019T1743/summary.json)。\n\n'
 brief='2026-10-19 18:20执行更新：44/72组完整训练通过root与独立复核；正常8卡自动5000不变。CUDA3039258仅完成原500恢复，后续连续准入待单独工程审查；Spatial剩余588条development-only计划已双审并预留下一个槽，当前8满、未提交。h8/λ0.1、72组、11次验证与173冻结源不变；原1212开发记录和失败保留，最终0/35200封存。18:12 CST账单333.972778 GPU小时（非最终）。[本轮凭据](../results/formal_main_v2/preflight/heartbeat_20261019T1743/summary.json)。\n\n'
 for rel in ['docs/实验进度.md','docs/完整实验计划.md','docs/正式主实验阶段结论.md','docs/正式主实验规划.md','docs/正式自动连续训练执行登记.md']:
  path=R/rel;text=path.read_text();first,sep,rest=text.partition('\n')
  addition=general if rel in ['docs/实验进度.md','docs/正式主实验阶段结论.md'] else brief
  assert addition not in text
  path.write_text(first+'\n\n'+addition+rest.lstrip('\n'))
 action='2026-10-19具体计划接入：Spatial原6方法、100开发初态、既定checkpoint/环境/资源和同一输出目录不变，保留12条终态，仅允许追加588个未完成ID。原plan真实重建及新外层转换通过root与独审，7项负例拒绝；source/runtime/P输入已校验，readiness只限development。production_chain_complete字段仅表示该计划预执行控制闭包齐备，actual_GPU_runtime_chain_verified=false，新入口产出的trial仍为0。\n\n授权55f6c06a…、预约e11b08fd…已绑定共享writer锁/CAS；18:12 CST实际check-only因8满拒绝，尚未发布正式invocation或提交GPU。下一次监督须重查owner/lease、pending、精确token与容量后使用该单次网关，不可另造请求。混合旧前缀的O2A/freeze join仍缺显式等价门，相关阶段继续禁止；不能把原Object policy_error丢弃重跑。[具体readiness](../results/formal_main_v2/execution/action_spatial_resume_0943/runtime_readiness.json)；[根预检](../results/formal_main_v2/preflight/heartbeat_20261019T1743/spatial_root_pre_execution_check.json)。\n\n'
 cuda='2026-10-19原目标终态验收：3039258 COMPLETED 0:0，Object256 seed23 A/B均500更新、4000实际唯一窗口、0/500各204窗口硬剪枝验证通过root及独立原始复算。原失败3028460没有初始化/训练checkpoint，故此次resumed=false正确，不能称其恢复了原优化器/RNG。新resume字节SHA已核，下一次实际恢复仍由冻结训练核验证完整状态。费用84+6512=6596 GPU秒，FAILED身份保留；另外两组尚未重提。\n\n新增审核器只修旧失败三份外部证据的原作业归属，当前作业及共享run-root仍走原严格pull校验，33项CPU检查通过。保留初版schema/测试脚本错误及全部日志。3039258日志实际由原wrapper写于R，基于真实sacct WorkDir与原wrapper登记镜像到P，原始日志未改。该恢复未获自动5000例外准入，不能直接清blocked或调用旧手动500续跑。[root](../results/formal_main_v2/libero_object/k256/seed23/training/segment_reviews/3039258.json)；[独审](../results/formal_main_v2/libero_object/k256/seed23/training/segment_reviews/3039258_independent.json)。\n\n'
 for rel,addition in [('docs/正式动作执行入口接入记录.md',action),('docs/正式CUDA启动失败恢复登记.md',cuda)]:
  path=R/rel;text=path.read_text();first,sep,rest=text.partition('\n');path.write_text(first+'\n\n'+addition+rest.lstrip('\n'))
 write(B+'/state_integration_receipt.json',dict(schema='formal_main_v2',status='integrated_under_writer_lock_CAS',before_sha256=old,after_sha256=c.file_sha(R/'results/experiment_supervisor/state.json'),summary=summaryref,
  controller_fields_preserved=True,registered_jobs_unchanged=True,source173_checked_by_transport=True))
 print(json.dumps(dict(summary=summaryref,root_independent_complete=44,reviewed_updates=231000,archived_private_files=len(origins),state_after=c.file_sha(R/'results/experiment_supervisor/state.json'))))

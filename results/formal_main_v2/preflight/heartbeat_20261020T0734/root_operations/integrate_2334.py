from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T0734';E='results/formal_main_v2/engineering/supervision_delivery_2334'
NR='results/formal_main_v2/libero_goal/k256/seed17/training/segment_reviews/3037543.json';NI=NR.replace('.json','_independent.json')
MAN='.local/goal256seed17_independent_2334/delivery_files.json'
IND='.local/goal256seed17_independent_2334/3037543_independent_review.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return {'path':rel,'sha256':h(R/rel)}
def read(rel):return json.loads((R/rel).read_text())
def checked(rel,pin):
 assert h(R/rel)==pin
 return read(rel)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as stream:json.dump(x,stream,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
 return ref(rel)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('root_integrate2334',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and f['root_and_independent_completed_arms']==50 and f['root_and_independent_reviewed_arm_updates']==257000
 assert f['completed_development_trials']==1412 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 root=checked(NR,'15ba5f131999cf1ea9aa0137f5f2e4dba80c4abbb1c548a35df2c6c339c90f7f')
 ind=checked(IND,'4df4dc75041622fc582a3e6abc56de71d11fec640f086d94563e30f841c0315f')
 assert root['status']=='passed' and ind['status']=='passed_complete_training_only' and root['completed_by_arm']==ind['completed_by_arm']=={'A':5000,'B':5000}
 assert root['pair_allocated_gpu_seconds']==ind['cost']['all_pair_allocated_GPU_seconds']==64274
 assert ind['cost']['allocations']==[{'GPU_seconds':64274,'job_id':'3037543'}]
 assert ind['same_AB_initialization_and_full40000_order'] and ind['all173_R_and_S_match']
 assert not ind['scientific_closed_loop_claimed'] and not ind['final_release_authorized']
 proof=ind['parallel_root_reconstruction'];assert proof['path']==NR and proof['sha256']==h(R/NR) and proof['new_reviewed_arm_updates']==10000
 assert proof['selected_server_proof']==ref(B+'/3037543_selected_server.json')
 for path,pin in ind['read_evidence_sha256'].items():assert h(R/path)==pin
 manifest=checked(MAN,'ca1e7a07adff0a7a2ac04ac8d99fa4468accd2934c8e80af0762b0ae7455b673');copies=[]
 rows=manifest['files']+[dict(path=MAN,sha256=h(R/MAN),bytes=(R/MAN).stat().st_size)]
 for row in rows:
  source=R/row['path'];assert source.parent==R/Path(MAN).parent and source.is_file() and not source.is_symlink()
  assert h(source)==row['sha256'] and source.stat().st_size==row['bytes']
  dest=R/E/'Goal256seed17_independent'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as stream:stream.write(source.read_bytes())
  assert h(dest)==row['sha256'];copies.append(dict(source=row,archive=ref(dest.relative_to(R).as_posix())))
 with (R/NI).open('xb') as stream:stream.write((R/IND).read_bytes())
 assert h(R/NI)==h(R/IND)
 delivery=save(B+'/Goal3037543_independent_delivery.json',dict(copies=copies,canonical=ref(NI),source_manifest=ref(MAN),no_GPU_execution=True))
 inventory_rel='.local/object64_recovery_inventory_2334/inventory.json'
 obj=checked(inventory_rel,'74e7f059f775123b40363d68a2a9319233de3f130da933b92fd13d8918db0a22')
 assert obj['pair_key']=='libero_object_k64_seed23' and not obj['GPU_submitted'] and not obj['state_changed'] and not obj['source_changed'] and not obj['final_states_read']
 inventory_dest=E+'/Object64seed23_recovery_inventory.json'
 with (R/inventory_dest).open('xb') as stream:stream.write((R/inventory_rel).read_bytes())
 assert h(R/inventory_dest)==h(R/inventory_rel)
 entry=f['completed_training_pairs']['libero_goal_k256_seed17'];assert entry['verification_kind']=='machine_automatic_not_independent'
 selected=[]
 for a in ['A','B']:
  dr='results/formal_main_v2/libero_goal/k256/seed17/training/'+a+'/deployment_receipt.json';d=read(dr);ar=ind['arms'][a]
  assert ar['completed_updates']==5000 and ar['sample_uses']==40000 and ar['unique_windows']==33859 and ar['cursor']==40000
  assert d['checkpoint_sha256']==ar['best_sha256'] and d['metadata']['update']==ar['earliest_selected_update'] and d['metadata']['validation_metric']==ar['selected_teacher_l1']
  selected.append(dict(arm=a,path='/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_goal/k256/seed17/'+a+'/best.pt',expected_sha256=d['checkpoint_sha256'],selected_update=ar['earliest_selected_update'],validation_metric=ar['selected_teacher_l1'],metadata_source=ref(dr)))
 binding=save(B+'/3037543_selected_binding.json',dict(status='root_and_independent_selected_identity_verified',root_review=ref(NR),independent_review=ref(NI),actual_server_bytes=ref(B+'/3037543_selected_server.json'),selected_checkpoints=selected,weights_copied=False))
 entry.update(job_id='3037543',suite='libero_goal',visual_tokens=256,seed=17,root_review=NR,root_review_sha256=h(R/NR),independent_review=NI,independent_review_sha256=h(R/NI),selected_checkpoints=selected,selected_server_review=binding['path'],selected_server_review_sha256=binding['sha256'],verification_kind='machine_automatic_plus_root_and_independent_raw_reconstruction')
 f['root_and_independent_completed_arms']=52;f['root_and_independent_reviewed_arm_updates']+=10000
 f['completed_engineering_segments'].append(dict(job_id='3037543',suite='libero_goal',visual_tokens=256,seed=17,status='passed_root_and_independent_complete_training',updates_by_arm={'A':5000,'B':5000},allocated_gpu_seconds=64274,pair_total_gpu_seconds=64274,root_review=NR,root_review_sha256=h(R/NR),independent_review=NI,independent_review_sha256=h(R/NI),new_reviewed_arm_updates=10000))
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])<=8 and obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 assert obs['rows']['3037543']['status']=='COMPLETED' and obs['rows']['3037543']['elapsed_seconds']==64274
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost']['allocated_gpu_seconds'];s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 keys=[k for k,v in f['completed_training_pairs'].items() if v.get('root_review') and v.get('independent_review') or v.get('terminal_root_and_independent_review')]
 assert len(keys)==26
 suites={suite:2*sum(k.startswith(suite+'_k') for k in keys) for suite in ['libero_10','libero_spatial','libero_object','libero_goal']}
 assert suites=={'libero_10':18,'libero_spatial':16,'libero_object':14,'libero_goal':4}
 inventory=read('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json');assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():assert h(R/rel)==h(R/'snapshots/formal_main_v2_run_564be0995e'/rel)==pin
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='scheduled_supervision_training_accepted',utc=now,root_independent_complete=52,machine_complete=f['trained_arms'],completed_by_suite=suites,total_arms=72,new_completed_training_groups=2,root_independent_updates=267000,new_reviewed_arm_updates=10000,Goal256seed17_root=ref(NR),Goal256seed17_independent=ref(NI),selected_identity=binding,independent_delivery=delivery,Object64_original_target_read_only_inventory=ref(inventory_dest),training_sample_uses_per_arm=40000,unique_training_windows_per_arm=33859,second_traversal_uses_per_arm=6141,validation_nodes_per_arm=11,validation_windows_per_node=186,new_development_trials_accepted=0,all_historical_and_new_development_trials=1412,new_GPU_submissions_by_root=[],new_duplicate_submissions=0,scheduler=obs,capacity=cap,active_GPU_jobs=len(cap['occupied']),reserved_GPU_slots=ctl['reserved_GPU_slots'],allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,cost_is_final=False,completed_final_trials=0,expected_final_trials=35200,final_sealed=True,normal_training_left_to_controller=True,server_only=True,scientific_files_unchanged=173))
 f['latest_incremental_review']=summary;f['incremental_review_history'].append(summary)
 f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied']);f['parallel_execution']['actual_running_allocated_GPUs']=sum(obs['rows'][x]['gpus'] for x in cap['occupied'] if obs['rows'][x]['status']=='RUNNING')
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']='2026-10-20'
 s['current_work']='52/72 complete training groups root+independent accepted (Long18,Spatial16,Object14,Goal4),267000 reviewed arm updates. Newly accepted Goal256seed17 fresh A/B5000; 40000 uses/33859 unique windows,11x186 validation, A4000/B5000 selected. No new development or final inference. Healthy training continues under autonomous controller.'
 s['next_actions']=['Leave healthy auto5000 training to controller and next scheduled heartbeat; preserve11 validation nodes, complete resume and max8 GPU slots.','At next genuine spare capacity use exact already admitted Spatial64seed23 continuous1500to5000 authorization once; never duplicate historical failure/recovery or consume other reservations.','Proceed with remaining7 registered Long development200 shards only through exact one-time authorization/reservation and shared8-slot accounting; never rerun accepted3043709 or change checkpoint based on development outcomes.','Object64seed23 already has an audited unused original-target500 authorization and gateway; activate only its own reservation and pass live preflight at a genuine free slot. Preserve69 failed GPU seconds and require separate5000 admission after500 recovery. Spatial failed development continuation remains separate.','All72 selected checkpoints+16reference identities+4suite complete development receipts and root globalrelease remain mandatory before final35200. Complete same-checkpoint O2A and component timing with matched action semantics.']
 s['next_allowed_action']=s['next_actions'][0]
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 c.atomic_json(sp,s,before)
 text=f'{stamp}：正式训练 **52/72组通过root与独立复核**（Long18、Spatial16、Object14、Goal4）。新增Goal256 seed17 A/B各5000步；原始记录复核11×186硬剪枝验证、相同初始化与完整40000次采样顺序，覆盖33859个独立窗口及第二轮6141次使用。A/B分别按既定验证规则选4000/5000步，教师L1为0.00760701/0.00769445。实际best与resume SHA及Goal官方50000步组件身份一致。新增10000已审臂更新，累计267000；本pair完整64274 GPU秒计入总账，缓存/前反向/验证等内部阶段不再重复加总。\n\n'
 text+=f'**{len(cap["occupied"])}卡活动，累计{seconds/3600:.3f} GPU小时**（含失败和运行中分配，非最终成本）。控制器已自动启动Goal64 seed41；本轮root无新GPU提交。以上只确认训练与选模，不推断Goal闭环收益或延迟改善。原开发记录1412条保留，本轮无新增开发；最终0/35200继续封存。正常作业交自动控制器，下次定时监督处理终态与真实空槽。[本轮原始证据](../{B}/summary.json)。\n\n'
 short=f'{stamp} 更新：52/72组训练双审通过，新增Goal256 seed17两组；{len(cap["occupied"])}卡活动，累计{seconds/3600:.3f} GPU小时（非最终）。A/B各40000次使用、33859独立窗口，11×186验证，选4000/5000步；仅训练与身份验收，不作闭环收益判断。本轮无新GPU提交或开发结果，原始日志完整归档，最终0/35200封存。[本轮收据](../{B}/summary.json)。\n\n'
 docs=[]
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记']:
  rel='docs/'+name+'.md';p=R/rel;assert rel not in inventory['files'];first,tail=p.read_text().split('\n',1);oldsha=h(p);p.write_text(first+'\n\n'+(text if name=='实验进度' else short)+tail.lstrip('\n'));docs.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 op=R/B/'root_operations';op.mkdir(exist_ok=True)
 for name in ['observe_formal_2334.py','review_terminal_2334.py','archive_results_2334.py','integrate_2334.py']:
  raw=(R/'.local'/name).read_bytes();compile(raw,name,'exec')
  with (op/name).open('xb') as stream:stream.write(raw)
 with (R/B/'previous_Git_push_verified.json').open('xb') as stream:stream.write((R/'.local/github_push_2232_verified.json').read_bytes())
 save(B+'/root_integration.json',dict(status='integrated',state_before_sha256=before,state_after_sha256=h(sp),summary=summary,docs=docs,controller_and_registry_unchanged_by_integration=True,new_GPU_jobs=[],frozen_scientific_files=173,normal_gpu_realtime_polling=False))
 print(json.dumps(dict(status='integrated',root_completed=52,reviewed_updates=267000,new_development=0,all_development=1412,active_GPU_jobs=len(cap['occupied']),GPU_hours=seconds/3600,summary=summary)),flush=True)

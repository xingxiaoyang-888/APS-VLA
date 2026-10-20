from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T0833';E='results/formal_main_v2/engineering/supervision_delivery_0033'
NR='results/formal_main_v2/libero_goal/k256/seed23/training/segment_reviews/3037821.json';NI=NR.replace('.json','_independent.json')
MAN='.local/goal256seed23_independent_0033/delivery_files.json'
IND='.local/goal256seed23_independent_0033/3037821_independent_review.json'
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
spec=importlib.util.spec_from_file_location('root_integrate0033',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and f['root_and_independent_completed_arms']==52 and f['root_and_independent_reviewed_arm_updates']==267000
 assert f['completed_development_trials']==1412 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 root=checked(NR,'11a239df861d502bfc65befb74c1a991ade37cf5cd3f89cba786ce749aef6b46')
 ind=checked(IND,'ed9d27395bc21f697150f26fa8a70ea9bcc86fc262239c09ec49c5b91fbc79ac')
 assert root['status']=='passed' and ind['status']=='passed_complete_training_only' and root['completed_by_arm']==ind['completed_by_arm']=={'A':5000,'B':5000}
 assert root['pair_allocated_gpu_seconds']==ind['cost']['all_pair_allocated_GPU_seconds']==65386
 assert ind['cost']['allocations']==[{'GPU_seconds':65386,'job_id':'3037821'}]
 assert ind['same_AB_initialization_and_full40000_order'] and ind['all173_R_and_S_match']
 assert not ind['scientific_closed_loop_claimed'] and not ind['final_release_authorized']
 proof=ind['parallel_root_reconstruction'];assert proof['path']==NR and proof['sha256']==h(R/NR) and proof['new_reviewed_arm_updates']==10000
 assert proof['selected_server_proof']==ref(B+'/3037821_selected_server.json')
 for path,pin in ind['read_evidence_sha256'].items():assert h(R/path)==pin
 manifest=checked(MAN,'1b6d34655beae5dcef41546f2eb0ee8ec74e8776f9c9881ab49f724ba08161ed');copies=[]
 rows=manifest['files']+[dict(path=MAN,sha256=h(R/MAN),bytes=(R/MAN).stat().st_size)]
 for row in rows:
  source=R/row['path'];assert source.parent==R/Path(MAN).parent and source.is_file() and not source.is_symlink()
  assert h(source)==row['sha256'] and source.stat().st_size==row['bytes']
  dest=R/E/'Goal256seed23_independent'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as stream:stream.write(source.read_bytes())
  assert h(dest)==row['sha256'];copies.append(dict(source=row,archive=ref(dest.relative_to(R).as_posix())))
 with (R/NI).open('xb') as stream:stream.write((R/IND).read_bytes())
 assert h(R/NI)==h(R/IND)
 delivery=save(B+'/Goal3037821_independent_delivery.json',dict(copies=copies,canonical=ref(NI),source_manifest=ref(MAN),no_GPU_execution=True))
 entry=f['completed_training_pairs']['libero_goal_k256_seed23'];assert entry['verification_kind']=='machine_automatic_not_independent'
 selected=[]
 for a in ['A','B']:
  dr='results/formal_main_v2/libero_goal/k256/seed23/training/'+a+'/deployment_receipt.json';d=read(dr);ar=ind['arms'][a]
  assert ar['completed_updates']==5000 and ar['sample_uses']==40000 and ar['unique_windows']==33859 and ar['cursor']==40000
  assert d['checkpoint_sha256']==ar['best_sha256'] and d['metadata']['update']==ar['earliest_selected_update'] and d['metadata']['validation_metric']==ar['selected_teacher_l1']
  selected.append(dict(arm=a,path='/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_goal/k256/seed23/'+a+'/best.pt',expected_sha256=d['checkpoint_sha256'],selected_update=ar['earliest_selected_update'],validation_metric=ar['selected_teacher_l1'],metadata_source=ref(dr)))
 binding=save(B+'/3037821_selected_binding.json',dict(status='root_and_independent_selected_identity_verified',root_review=ref(NR),independent_review=ref(NI),actual_server_bytes=ref(B+'/3037821_selected_server.json'),selected_checkpoints=selected,weights_copied=False))
 entry.update(job_id='3037821',suite='libero_goal',visual_tokens=256,seed=23,root_review=NR,root_review_sha256=h(R/NR),independent_review=NI,independent_review_sha256=h(R/NI),selected_checkpoints=selected,selected_server_review=binding['path'],selected_server_review_sha256=binding['sha256'],verification_kind='machine_automatic_plus_root_and_independent_raw_reconstruction')
 f['root_and_independent_completed_arms']=54;f['root_and_independent_reviewed_arm_updates']+=10000
 f['completed_engineering_segments'].append(dict(job_id='3037821',suite='libero_goal',visual_tokens=256,seed=23,status='passed_root_and_independent_complete_training',updates_by_arm={'A':5000,'B':5000},allocated_gpu_seconds=65386,pair_total_gpu_seconds=65386,root_review=NR,root_review_sha256=h(R/NR),independent_review=NI,independent_review_sha256=h(R/NI),new_reviewed_arm_updates=10000))
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])<=8 and obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 assert obs['rows']['3037821']['status']=='COMPLETED' and obs['rows']['3037821']['elapsed_seconds']==65386
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost']['allocated_gpu_seconds'];s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 keys=[k for k,v in f['completed_training_pairs'].items() if v.get('root_review') and v.get('independent_review') or v.get('terminal_root_and_independent_review')]
 assert len(keys)==27
 suites={suite:2*sum(k.startswith(suite+'_k') for k in keys) for suite in ['libero_10','libero_spatial','libero_object','libero_goal']}
 assert suites=={'libero_10':18,'libero_spatial':16,'libero_object':14,'libero_goal':6}
 inventory=read('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json');assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():assert h(R/rel)==h(R/'snapshots/formal_main_v2_run_564be0995e'/rel)==pin
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='scheduled_supervision_training_accepted',utc=now,root_independent_complete=54,machine_complete=f['trained_arms'],completed_by_suite=suites,total_arms=72,new_completed_training_groups=2,root_independent_updates=277000,new_reviewed_arm_updates=10000,Goal256seed23_root=ref(NR),Goal256seed23_independent=ref(NI),selected_identity=binding,independent_delivery=delivery,training_sample_uses_per_arm=40000,unique_training_windows_per_arm=33859,second_traversal_uses_per_arm=6141,validation_nodes_per_arm=11,validation_windows_per_node=186,new_development_trials_accepted=0,all_historical_and_new_development_trials=1412,new_GPU_submissions_by_root=['3044017'],Object64_original_target_recovery=ref(B+'/Object64_3044017_submission_identity.json'),Spatial_v2_root_admission=ref(B+'/Spatial_v2_root_publication_and_prepare.json'),Spatial_v2_capacity_decision=ref(B+'/Spatial_v2_capacity_decision.json'),new_duplicate_submissions=0,scheduler=obs,capacity=cap,active_GPU_jobs=len(cap['occupied']),reserved_GPU_slots=ctl['reserved_GPU_slots'],allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,cost_is_final=False,completed_final_trials=0,expected_final_trials=35200,final_sealed=True,normal_training_left_to_controller=True,server_only=True,scientific_files_unchanged=173))
 f['spatial64seed23_continuous_v2_ready']=dict(authorization=ref('configs/experiments/formal_main_v2_spatial_cuda_continuous_3043399_v2.json'),root_preflight=ref(B+'/Spatial_v2_root_publication_and_prepare.json'),capacity=ref(B+'/Spatial_v2_capacity_decision.json'),status='CPU_and_root_raw_admission_passed_wait_for_real_spare_GPU',GPU_submitted=False)
 f['latest_incremental_review']=summary;f['incremental_review_history'].append(summary)
 f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied']);f['parallel_execution']['actual_running_allocated_GPUs']=sum(obs['rows'][x]['gpus'] for x in cap['occupied'] if obs['rows'][x]['status']=='RUNNING')
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']='2026-10-20'
 s['current_work']='54/72 complete training groups root+independent accepted (Long18,Spatial16,Object14,Goal6),277000 reviewed arm updates. Newly accepted Goal256seed23 fresh A/B5000; 40000 uses/33859 unique windows,11x186 validation, A4500/B4500 selected. No new development or final inference. Object64seed23 original-target500 recovery3044017 submitted exactly once and verified RUNNING; Spatial64seed23 continuous-v2 operational-document history binding passed author/independent/root raw checks, ready for next real spare slot. Healthy training continues under autonomous controller.'
 s['next_actions']=['Leave healthy auto5000 training to controller and next scheduled heartbeat; preserve11 validation nodes, complete resume and max8 GPU slots.','At next genuine spare capacity use configs/experiments/formal_main_v2_spatial_cuda_continuous_3043399_v2.json SHA1cdb14995f275d03557d86be1b565f615a005d911b994ce8c17a3d229e989411 and exact v2 gateway, fresh full identity/capacity gate then once only. Historical v1 doc-hash failure is retained and v2 only bridges exact old/new operational-doc bytes. No new Spatial invocation or GPU submission yet.','Proceed with remaining7 registered Long development200 shards only through exact one-time authorization/reservation and shared8-slot accounting; never rerun accepted3043709 or change checkpoint based on development outcomes.','Object64seed23 recovery3044017 is now registered once, RUNNING and identity-verified, original target500 only; its exact reservation was consumed once, remaining reserved0. Do not resubmit. At terminal use actual R/results/slurm logs with established exact R-to-P mirror/pull before review. Preserve failed69 GPU seconds; separate 5000 admission still required after successful500 root+independent recovery. Spatial failed development continuation remains separate.','All72 selected checkpoints+16reference identities+4suite complete development receipts and root globalrelease remain mandatory before final35200. Complete same-checkpoint O2A and component timing with matched action semantics.']
 s['next_allowed_action']=s['next_actions'][0]
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 c.atomic_json(sp,s,before)
 text=f'{stamp}：正式训练 **54/72组通过root与独立复核**（Long18、Spatial16、Object14、Goal6）。新增Goal256 seed23 A/B各5000步；原始记录复核11×186硬剪枝验证、相同初始化与完整40000次采样顺序，覆盖33859个独立窗口及第二轮6141次使用。A/B分别按既定验证规则选4500/4500步，教师L1为0.00786342/0.00752019。实际best与resume SHA及Goal官方50000步组件身份一致。新增10000已审臂更新，累计277000；本pair完整65386 GPU秒计入总账，缓存/前反向/验证等内部阶段不再重复加总。\n\n'
 text+=f'**{len(cap["occupied"])}卡活动，累计{seconds/3600:.3f} GPU小时**（含失败和运行中分配，非最终成本）。本轮root单次提交Object64 seed23原目标500步恢复3044017，并核对真实Slurm身份及8槽上限。Spatial64 seed23连续恢复v2已通过25项作者检查、15项独审及root原始证据重建；只绑定运维文档新旧字节，173科学文件未变。当前8槽占满，尚未提交Spatial新作业，下一次真实空槽走新授权与原提交门槛。以上只确认训练与选模，不推断Goal闭环收益或延迟改善。原开发记录1412条保留，本轮无新增开发；最终0/35200继续封存。正常作业交自动控制器，下次定时监督处理终态与真实空槽。[本轮原始证据](../{B}/summary.json)。\n\n'
 short=f'{stamp} 更新：54/72组训练双审通过，新增Goal256 seed23两组；{len(cap["occupied"])}卡活动，累计{seconds/3600:.3f} GPU小时（非最终）。A/B各40000次使用、33859独立窗口，11×186验证，选4500/4500步；仅训练与身份验收，不作闭环收益判断。本轮新增Object64 seed23原目标500步恢复3044017；Spatial64 seed23续跑文档版本绑定v2通过双审与root预检，满8槽时等待下次真实空槽。本轮无新增开发结果，原始日志完整归档，最终0/35200封存。[本轮收据](../{B}/summary.json)。\n\n'
 docs=[]
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记']:
  rel='docs/'+name+'.md';p=R/rel;assert rel not in inventory['files'];first,tail=p.read_text().split('\n',1);oldsha=h(p);p.write_text(first+'\n\n'+(text if name=='实验进度' else short)+tail.lstrip('\n'));docs.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 op=R/B/'root_operations';op.mkdir(exist_ok=True)
 for name in ['observe_formal_0033.py','review_terminal_0033.py','archive_results_0033.py','activate_object64_slot_0033.py','run_object64_recovery_0033.py','object_identity_0033.py','run_spatial_continuous_0033.py','publish_spatial_v2_0033.py','spatial_capacity_0033.py','integrate_0033.py']:
  raw=(R/'.local'/name).read_bytes();compile(raw,name,'exec')
  with (op/name).open('xb') as stream:stream.write(raw)
 with (R/B/'previous_Git_push_verified.json').open('xb') as stream:stream.write((R/'.local/github_push_2334_verified.json').read_bytes())
 save(B+'/root_integration.json',dict(status='integrated',state_before_sha256=before,state_after_sha256=h(sp),summary=summary,docs=docs,controller_and_registry_unchanged_by_integration=True,new_GPU_jobs=['3044017'],frozen_scientific_files=173,normal_gpu_realtime_polling=False))
 print(json.dumps(dict(status='integrated',root_completed=54,reviewed_updates=277000,new_development=0,all_development=1412,active_GPU_jobs=len(cap['occupied']),GPU_hours=seconds/3600,summary=summary)),flush=True)

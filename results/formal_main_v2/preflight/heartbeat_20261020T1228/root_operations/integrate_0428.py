from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1228';E='results/formal_main_v2/engineering/supervision_delivery_0428'
NR='results/formal_main_v2/libero_goal/k128/seed23/training/segment_reviews/3039981.json';NI=NR.replace('.json','_independent.json')
MAN='.local/independent_goal3039981_0428/delivery_files.json';IND='.local/independent_goal3039981_0428/3039981_independent_review.json'
LMAN='.local/independent_long128s41_0428/manifest.json';LIND='.local/independent_long128s41_0428/independent_review.json'
D='results/formal_main_v2/execution/long_remaining16_action_v1_1827/k128_seed41'
AD='results/formal_main_v2/downstream_gateway/a2104c3cb1d96dd0d8ddd5bf9c0a9b2a19dc04d5cbf8e6fae8d69d9dea6b0730'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def read(rel):return json.loads((R/rel).read_text())
def checked(rel,pin):
 assert h(R/rel)==pin,rel
 return read(rel)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as stream:json.dump(x,stream,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
 return ref(rel)
def archive_manifest(rel,pin,subdir):
 manifest=checked(rel,pin);copies=[]
 rows=manifest['files']+[dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size)]
 for row in rows:
  source=R/row['path'];assert source.parent==R/Path(rel).parent and source.is_file() and not source.is_symlink()
  assert h(source)==row['sha256'] and source.stat().st_size==row['bytes']
  assert source.suffix not in ['.pt','.pth','.bin','.safetensors','.ckpt','.pyc'] and source.stat().st_size<100*(1<<20)
  dest=R/E/subdir/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as stream:stream.write(source.read_bytes())
  copies.append(dict(source=row,archive=ref(dest.relative_to(R).as_posix())))
 return copies
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('root_integrate0428',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and f['root_and_independent_completed_arms']==56 and f['root_and_independent_reviewed_arm_updates']==288000
 assert f['completed_development_trials']==1412 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 root=checked(NR,'e742b9453c814788b3772768817a65a35da5e52bafc9ecdcc65688fb86c0273c')
 ind=checked(IND,'6126c326b153586b2ce863e0f3d134d4d27c1274c4eb3a4d6712d4f58676cf75')
 assert root['status']=='passed' and ind['status']=='passed_complete_training_only' and root['completed_by_arm']==ind['completed_by_arm']=={'A':5000,'B':5000}
 assert root['pair_allocated_gpu_seconds']==ind['cost']['all_pair_allocated_GPU_seconds']==72435
 assert ind['cost']['allocations']==[{'GPU_seconds':3214,'job_id':'3026224'},{'GPU_seconds':3125,'job_id':'3030839'},{'GPU_seconds':66096,'job_id':'3039981'}]
 assert ind['same_AB_initialization_and_full40000_order'] and ind['all173_R_and_S_match'] and ind['new_reviewed_arm_updates']==8000
 assert not ind['scientific_closed_loop_claimed'] and not ind['final_release_authorized']
 proof=ind['parallel_root_reconstruction'];assert proof['path']==NR and proof['sha256']==h(R/NR) and proof['new_reviewed_arm_updates']==8000 and not proof['fresh_pair'] and proof['prior_reviewed_updates_per_arm']==1000
 assert proof['selected_server_proof']==ref(B+'/3039981_selected_server.json')
 for path,pin in ind['read_evidence_sha256'].items():assert h(R/path)==pin,path
 copies=archive_manifest(MAN,'631233eb6043e0697036e92526f427bcab670f4986171d04b96f4619ed895961','Goal128seed23_independent')
 with (R/NI).open('xb') as stream:stream.write((R/IND).read_bytes())
 delivery=save(B+'/Goal3039981_independent_delivery.json',dict(copies=copies,canonical=ref(NI),source_manifest=ref(MAN),no_GPU_execution=True))
 lind=checked(LIND,'782483c01efe42ebc8c2fe83f4c78bdcc989c8cae7e7bddc727f4fc672c44770')
 assert lind['status']=='passed' and lind['job_id']=='3045322' and lind['blockers']==[]
 lcopies=archive_manifest(LMAN,'70b436d266469e1458b1375c2aeba4ddc523be2b2b01e0864dd5ca49af8c7242','Long128seed41_submission_independent')
 lref=ref(E+'/Long128seed41_submission_independent/'+Path(LIND).name)
 ldelivery=save(B+'/Long3045322_independent_delivery.json',dict(copies=lcopies,independent_report=lref,no_GPU_execution=True))
 rec=checked(B+'/Long3045322_pending_reconciliation.json','ac21ef6e5beb48417f595b9f0e112dd280810e55f4cf57d763cad84706ee8ea7')
 assert rec['status']=='exact_original_ACK_job_reconciled' and rec['new_submissions']==0 and rec['job']['job_id']=='3045322'
 assert read(AD+'/committed.json')['root_reconciliation']==ref(B+'/Long3045322_pending_reconciliation.json')
 jobs=[j for j in s['registered_jobs'] if str(j['job_id'])=='3045322'];assert len(jobs)==1 and jobs[0]['method_ids']==['A128_seed41','B128_seed41']
 assert jobs[0]['invocation_sha256']=='2a7e9f4fbaf9947eec17807ca21c351a2e0c12fb512e5bd3f9619502e1db0afc'
 assert ctl['reserved_GPU_slots']==0 and ctl['downstream_reservations_consumed']['a2104c3cb1d96dd0d8ddd5bf9c0a9b2a19dc04d5cbf8e6fae8d69d9dea6b0730']['job_id']=='3045322'
 entry=f['completed_training_pairs']['libero_goal_k128_seed23'];assert entry['verification_kind']=='machine_automatic_not_independent'
 selected=[]
 for a in ['A','B']:
  dr='results/formal_main_v2/libero_goal/k128/seed23/training/'+a+'/deployment_receipt.json';d=read(dr);ar=ind['arms'][a]
  assert ar['completed_updates']==5000 and ar['sample_uses']==40000 and ar['unique_windows']==33859 and ar['cursor']==40000
  assert d['checkpoint_sha256']==ar['best_sha256'] and d['metadata']['update']==ar['earliest_selected_update']==3000 and d['metadata']['validation_metric']==ar['selected_teacher_l1']
  selected.append(dict(arm=a,path='/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_goal/k128/seed23/'+a+'/best.pt',expected_sha256=d['checkpoint_sha256'],selected_update=ar['earliest_selected_update'],validation_metric=ar['selected_teacher_l1'],metadata_source=ref(dr)))
 binding=save(B+'/3039981_selected_binding.json',dict(status='root_and_independent_selected_identity_verified',root_review=ref(NR),independent_review=ref(NI),actual_server_bytes=ref(B+'/3039981_selected_server.json'),selected_checkpoints=selected,weights_copied=False))
 entry.update(job_id='3039981',suite='libero_goal',visual_tokens=128,seed=23,root_review=NR,root_review_sha256=h(R/NR),independent_review=NI,independent_review_sha256=h(R/NI),selected_checkpoints=selected,selected_server_review=binding['path'],selected_server_review_sha256=binding['sha256'],verification_kind='machine_automatic_plus_root_and_independent_raw_reconstruction')
 assert not any(x.get('job_id')=='3039981' and x.get('independent_review') for x in f['completed_engineering_segments'])
 f['root_and_independent_completed_arms']=58;f['root_and_independent_reviewed_arm_updates']+=8000
 f['completed_engineering_segments'].append(dict(job_id='3039981',suite='libero_goal',visual_tokens=128,seed=23,status='passed_root_and_independent_complete_training',updates_by_arm={'A':5000,'B':5000},allocated_gpu_seconds=66096,pair_total_gpu_seconds=72435,root_review=NR,root_review_sha256=h(R/NR),independent_review=NI,independent_review_sha256=h(R/NI),new_reviewed_arm_updates=8000,prior_root_independent_updates_per_arm=1000))
 submission=dict(job_id='3045322',suite='libero_10',visual_tokens=128,seed=41,method_ids=['A128_seed41','B128_seed41'],planned_trials=200,unique_development_initial_states=100,completed_trials_accepted=0,status='submitted_once_pending_accounting_delay_reconciled',authorization=ref(D+'/submission_authorization.json'),reconciliation=ref(B+'/Long3045322_pending_reconciliation.json'),independent_submission_review=lref,failure_retained=ref(AD+'/failed_transaction.json'),exact_reservation_consumed=True,automatic_retry=False,final_evaluation_enabled=False)
 history=f.setdefault('Long_remaining16_development_submissions',[]);assert not any(x['job_id']=='3045322' for x in history);history.append(submission)
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])<=8 and obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 assert obs['rows']['3039981']['status']=='COMPLETED' and obs['rows']['3039981']['elapsed_seconds']==66096
 assert obs['rows']['3045322']['status'] in ['RUNNING','PENDING','CONFIGURING'] and '3045322' in cap['occupied']
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost']['allocated_gpu_seconds'];s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 keys=[]
 for k,v in f['completed_training_pairs'].items():
  if v.get('root_review') and v.get('independent_review'):
   for role in ['root_review','independent_review']:assert h(R/v[role])==v[role+'_sha256']
   keys.append(k)
  elif v.get('terminal_root_and_independent_review'):
   x=v['terminal_root_and_independent_review'];assert x['completed_by_arm']=={'A':5000,'B':5000}
   for role in ['root_review','independent_review']:assert ref(x[role]['path'])==x[role]
   keys.append(k)
 assert len(keys)==29
 suites={suite:2*sum(k.startswith(suite+'_k') for k in keys) for suite in ['libero_10','libero_spatial','libero_object','libero_goal']}
 assert suites=={'libero_10':18,'libero_spatial':16,'libero_object':14,'libero_goal':10}
 inventory=read('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json');assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():assert h(R/rel)==h(P/'snapshots/formal_main_v2_run_564be0995e'/rel)==pin
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 next_actions=['Leave healthy auto5000 training to the controller; next scheduled heartbeat handles terminals and exceptions, no continuous in-turn polling.',
 'Long128 seed41 development3045322 is already registered once for200 trials; reconcile its terminal artifacts at next scheduled supervision, never rerun accepted Long3043709.',
 'After an actual free slot, continue the remaining registered development and latency work through exact authorization and shared8-slot accounting. Preserve all historical CUDA failures and recovery costs.',
 'All72 selected checkpoints+16reference identities+4suite complete development receipts and root globalrelease remain required before final35200; no final-state reading or result-based reselection.']
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='scheduled_supervision_training_accepted_and_development_slot_refilled',utc=now,root_independent_complete=58,machine_complete=f['trained_arms'],completed_by_suite=suites,total_arms=72,new_completed_training_groups=2,root_independent_updates=296000,new_reviewed_arm_updates=8000,Goal128seed23_root=ref(NR),Goal128seed23_independent=ref(NI),selected_identity=binding,independent_delivery=delivery,training_sample_uses_per_arm=40000,unique_training_windows_per_arm=33859,second_traversal_uses_per_arm=6141,validation_nodes_per_arm=11,validation_windows_per_node=186,terminal_segment_GPU_seconds=66096,all_pair_GPU_seconds=72435,new_development_trials_accepted=0,all_historical_and_new_development_trials=1412,new_GPU_submissions_by_root=['3045322'],Long128seed41_development=submission,Long_submission_independent=lref,original_ack_accounting_delay_reconciled_no_resubmit=True,new_duplicate_submissions=0,scheduler=obs,capacity=cap,active_GPU_jobs=len(cap['occupied']),reserved_GPU_slots=ctl['reserved_GPU_slots'],allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,cost_is_final=False,completed_final_trials=0,expected_final_trials=35200,final_sealed=True,normal_training_left_to_controller=True,server_only=True,scientific_files_unchanged=173,nonweight_archive=ind['archive_reconstruction']['snapshot'],new_archived_raw_bytes=149270140,independent_review_limitations=ind['limitations'],next=next_actions))
 f['latest_incremental_review']=summary;f['incremental_review_history'].append(summary)
 f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied']);f['parallel_execution']['actual_running_allocated_GPUs']=sum(obs['rows'][x]['gpus'] for x in cap['occupied'] if obs['rows'][x]['status']=='RUNNING')
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']='2026-10-20'
 s['current_work']=f'58/72 complete groups root+independent accepted (Long18,Spatial16,Object14,Goal10),296000 reviewed arm updates. New Goal128seed23 A/B1000-to5000,11x186 cumulative validations,40000 uses/33859 unique windows,A/B3000 selected. Long128seed41 development3045322 registered once after exact accounting-delay reconciliation;{len(cap["occupied"])} active GPUs. Development1412 accepted unchanged and final0/35200 sealed.'
 s['next_actions']=next_actions;s['next_allowed_action']=next_actions[0]
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 c.atomic_json(sp,s,before)
 text=f'{stamp}：正式训练 **58/72组通过root与独立复核**（Long18、Spatial16、Object14、Goal10）。新增Goal128 seed23 A/B各完成5000步；保留先前500/1000步双审，本次仅新增8000已审臂更新，累计296000。独立重建11×186硬剪枝验证、相同初始化及完整40000次样本顺序，33859个唯一窗口、第二轮6141次使用，两个跨作业恢复边界可核对。A/B均选3000步，teacher L1分别0.01835416/0.01833054；best/resume实际SHA与Goal官方组件通过，3份新增大日志共149270140字节无损重建，6份历史小日志按已提交原字节校验。优化器/RNG恢复依据原真实验收、冻结加载实现和断点哈希链，本次未独立反序列化张量。该pair历次分配3214+3125+66096=72435 GPU秒计入总账一次。\n\n'
 text+=f'本轮将真实空槽用于Long128 seed41开发评测，唯一作业3045322，原10任务×10共同开发初态、A/B共200条；沿用已验收动作运行入口，结果尚待验收。提交后即时Slurm记账缺行已按原ACK、精确token、全作业清单和scontrol核对，消费本请求专属一卡预约，无重发。当前 **{len(cap["occupied"])}卡活动，正式轮累计{seconds/3600:.3f} GPU小时**（含失败和运行中分配，非最终成本）。原开发1412条全部保留，未新增已验收成功率或加速结论，最终0/35200继续封存。正常训练交自动控制器，下次定时监督处理终态。[本轮收据](../{B}/summary.json)。\n\n'
 short=f'{stamp}：58/72组训练双审通过，新增Goal128 seed23 A/B各5000步、累计11×186验证，均按原规则选3000步；本轮只增加8000已审更新。Long128 seed41原登记200条开发评测已单次启动（3045322），记账延迟按原ACK核对无重发。{len(cap["occupied"])}卡活动，正式轮累计{seconds/3600:.3f} GPU小时（非最终）。历史开发1412条保留，新评测待验收；最终0/35200封存。173科学文件不变，非权重结果完整归档，权重仅服务器。[本轮证据](../{B}/summary.json)。\n\n'
 docs=[]
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式Long其余16选择器开发登记']:
  rel='docs/'+name+'.md';p=R/rel;assert rel not in inventory['files'];first,tail=p.read_text().split('\n',1);oldsha=h(p);p.write_text(first+'\n\n'+(text if name=='实验进度' else short)+tail.lstrip('\n'));docs.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 op=R/B/'root_operations';op.mkdir(exist_ok=True)
 for name in ['observe_formal_0428.py','reserve_Long128seed41_0428.py','dispatch_long128seed41_0428.py','reconcile_long128s41_pending_0428.py','review_terminal_0428.py','archive_results_0428.py','integrate_0428.py']:
  raw=(R/'.local'/name).read_bytes();compile(raw,name,'exec')
  with (op/name).open('xb') as stream:stream.write(raw)
 with (R/B/'previous_Git_push_verified.json').open('xb') as stream:stream.write((R/'.local/github_push_0333_verified.json').read_bytes())
 save(B+'/root_integration.json',dict(status='integrated',state_before_sha256=before,state_after_sha256=h(sp),summary=summary,docs=docs,controller_and_registry_unchanged_by_integration=True,new_GPU_jobs=['3045322'],frozen_scientific_files=173,normal_gpu_realtime_polling=False))
 print(json.dumps(dict(status='integrated',root_completed=58,reviewed_updates=296000,new_development=0,active_GPU_jobs=len(cap['occupied']),GPU_hours=seconds/3600,summary=summary)),flush=True)
